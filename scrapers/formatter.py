from __future__ import annotations

import json
import sys
from datetime import datetime
import pytz
import hashlib
import base64

# --- Utility helpers ---------------------------------------------------------

def generate_hash(string):
    """
    Deterministically generate a short checksum for a given string.

    - Uses MD5 for brevity/compatibility (not for cryptographic security).
    - The checksum is used downstream as an idempotency key to detect duplicates.
    """
    return hashlib.md5(string.encode('utf-8')).hexdigest()

# --- Normalizers: one per source --------------------------------------------

def format_opportunities_cal(raw_events):
    """
    Normalize a list of CAL eProcure-like events into the unified opportunity schema.

    Input:
      raw_events: list[dict] with mixed field names coming from the CAL scraper.

    Behavior:
      - Maps multiple possible source keys to the canonical unified schema.
      - Leaves dates/amounts as provided (no parsing here) to keep this step simple.
      - Computes a stable 'checksum' based on (id|title) for idempotency.
      - Preserves unknown fields as None to be enriched later.

    Notes:
      - There is intentional minimal transformation here; enrichment is handled
        by later steps in the pipeline (e.g., n8n/LLM).
      - Some variables are initialized twice; left as-is to avoid altering logic.
    """
    out = []
    utc = pytz.utc  # timezone handle kept for potential future use
    null = None     # explicit alias to signal intentional nulls in mappings
    false = False   # explicit alias for falsy default flags

    # NOTE: This loop resets 'out' each iteration in the original code.
    # Kept untouched to comply with "do not change logic".
    for ev in raw_events:
        out = []
    utc = pytz.utc  # duplicate initialization retained intentionally

    for ev in raw_events:
        # Prefer CAL's event_id / event_name, fall back to unified keys if present
        ev_id = ev.get("event_id") or ev.get("opportunity_id") or None
        title = ev.get("event_name") or ev.get("title") or None

        # CAL feed often lacks explicit posted/created dates; set to None
        posted_date = None
        created_at = None

        # Deadline: pass through whatever the scraper provided (string/ISO/etc.)
        deadline = ev.get("end_date") or None

        # NOTE: Intentionally not parsing timezone or human-formatted dates here.
        # Date normalization/parsing happens in a dedicated step later.

        solicitation_number = ev.get("solicitation_number") or None
        agency = ev.get("agency") or ev.get("department") or None
        agency_code = ev.get("agency_code") or None
        archive_date = ev.get("archive_date") or None
        naics_code = ev.get("naics_code") or None
        classification_code = ev.get("classification_code") or None
        service_line = ev.get("service_line") or None
        estimated_value = ev.get("estimated_value") or None
        effort_hours = ev.get("effort_hours") or None
        effort_bucket = ev.get("effort_bucket") or None
        typ = ev.get("type") or None
        active = ev.get("active") if "active" in ev else None
        decision = ev.get("decision") or None
        score = ev.get("score") or None

        # Award-related fields (may be absent in CAL rows)
        award_date = ev.get("award_date") or None
        award_number = ev.get("award_number") or None
        award_amount = ev.get("award_amount") or None
        awardee_name = ev.get("awardee_name") or None
        awardee_uei = ev.get("awardee_uei") or None
        awardee_cage = ev.get("awardee_cage") or None

        # Created-at passthrough if provided by upstream
        created_at = ev.get("created_at") or None

        # Token accounting passthrough (for LLM cost logging later)
        token_cost = ev.get("token_cost") or None

        # Idempotency checksum: stable across runs while (id|title) stays the same
        chk_src = f"{ev_id or ''}|{title or ''}"
        checksum = generate_hash(chk_src)

        # Emit one normalized row
        out.append({
            "opportunity_id": ev_id,
            "title": title,
            "solicitation_number": solicitation_number,
            "agency": agency,
            "agency_code": agency_code,
            "posted_date": posted_date,
            "deadline": deadline,
            "archive_date": archive_date,
            "naics_code": naics_code,
            "classification_code": classification_code,
            "service_line": service_line,
            "estimated_value": estimated_value,
            "effort_hours": effort_hours,
            "effort_bucket": effort_bucket,
            "type": typ,
            "active": active,
            "decision": decision,
            "score": score,
            "award_date": award_date,
            "award_number": award_number,
            "award_amount": award_amount,
            "awardee_name": awardee_name,
            "awardee_uei": awardee_uei,
            "awardee_cage": awardee_cage,
            "created_at": created_at,
            "checksum": checksum,
            "token_cost": token_cost
        })
    return out

def format_opportunities_laco(raw_bids):
    """
    Normalize a list of Los Angeles County (LACO) bid objects into the unified schema.

    Key behaviors:
      - Uses 'close_date' as the deadline, except when the value is 'Continuous'
        (treated as empty string to signal “no fixed deadline”).
      - Marks type='Solicitation' and active=True by default for open listings.
      - Computes checksum from (bid_id|title) for idempotency.
      - Stamps 'created_at' with current UTC time (second precision + 'Z').

    This function intentionally performs light-touch normalization only.
    """
    out = []
    utc = pytz.utc  # retained for consistency with other normalizers
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    for bid in raw_bids:
        bid_id = bid.get("bid_id")
        title = bid.get("title")
        solicitation_number = bid.get("solicitation_number")
        agency = bid.get("department")

        # Deadline parsing rule: convert literal 'Continuous' into empty string
        close = bid.get("close_date", "").strip()
        if close == "Continuous":
            close = ""

        # Idempotency checksum based on stable identifying fields
        chk_src = f"{bid_id or ''}|{title or ''}"
        checksum = generate_hash(chk_src)

        out.append({
            "opportunity_id": bid_id,
            "title": title,
            "solicitation_number": solicitation_number,
            "agency": agency,
            "agency_code": None,
            "posted_date": None,
            "deadline": close,
            "archive_date": None,
            "naics_code": None,
            "classification_code": None,
            "service_line": bid.get('type') or None,  # passthrough of source typing
            "estimated_value": None,
            "effort_hours": None,
            "effort_bucket": None,
            "type": "Solicitation",
            "active": True,
            "decision": None,
            "score": None,
            "award_date": None,
            "award_number": None,
            "award_amount": None,
            "awardee_name": None,
            "awardee_uei": None,
            "awardee_cage": None,
            "created_at": now,
            "checksum": checksum,
            "token_cost": None
        })

    return out

def format_opportunities_sam(raw_notices):
    """
    Normalize a list of SAM.gov API notices into the unified schema.

    Highlights:
      - Direct field mappings from the official SAM.gov JSON (noticeId, title, etc.).
      - Active flag: converts "Yes"/other into boolean True/False.
      - Award sub-document (date/number/amount/awardee) is safely unpacked.
      - 'archive_date' mirrors 'responseDeadLine' as provided by the source.
      - 'created_at' is set to current UTC when transforming.

    As with other normalizers, deep parsing/validation is deferred to later stages.
    """
    out = []
    utc = pytz.utc
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    for ev in raw_notices:
        opportunity_id = ev.get("noticeId")
        title = ev.get("title")
        solicitation_number = ev.get("solicitationNumber")
        agency = ev.get("fullParentPathName")
        agency_code = ev.get("fullParentPathCode")
        posted_date = ev.get("postedDate")
        deadline = ev.get("responseDeadLine")
        archive_date = ev.get("responseDeadLine")
        naics_code = ev.get("naicsCode")
        classification_code = ev.get("classificationCode")
        service_line = ev.get("type")
        type_f = ev.get("type")

        # Map textual activity status into a strict boolean
        isActive = ev.get("active")
        if isActive == "Yes":
            active = True
        else:
            active = False

        # Award sub-object: unwrap safely with defaults
        award_info = ev.get("award") or {}
        award_date = award_info.get("date")
        award_number = award_info.get("number")
        award_amount = award_info.get("amount")
        awardee = award_info.get("awardee") or {}
        awardee_name = awardee.get("name")
        awardee_uei = awardee.get("ueiSAM")
        awardee_cage = awardee.get("cageCode")

        # Active status again (kept as in the original code, not refactored)
        active = ev.get("active") == "Yes"

        # Idempotency checksum derived from (id|title)
        chk_src = f"{opportunity_id or ''}|{title or ''}"
        checksum = generate_hash(chk_src)

        out.append({
            "opportunity_id": opportunity_id,
            "title": title,
            "solicitation_number": solicitation_number,
            "agency": agency,
            "agency_code": agency_code,
            "posted_date": posted_date,
            "deadline": deadline,
            "archive_date": archive_date,
            "naics_code": naics_code,
            "classification_code": classification_code,
            "service_line": service_line,
            "estimated_value": None,
            "effort_hours": None,
            "effort_bucket": None,
            "type": type_f,
            "active": active,
            "decision": None,
            "score": None,
            "award_date": award_date,
            "award_number": award_number,
            "award_amount": award_amount,
            "awardee_name": awardee_name,
            "awardee_uei": awardee_uei,
            "awardee_cage": awardee_cage,
            "created_at": now,
            "checksum": checksum,
            "token_cost": None
        })

    return out

# --- CLI entrypoint ----------------------------------------------------------

def _main_cli() -> None:
    """
    Command-line interface.

    Usage:
      python normalize_opportunities.py <base64_json> <cal|laco|sam>

    Parameters:
      - base64_json: a base64-encoded JSON string representing a list of raw rows
      - source: which normalizer to apply ("cal", "laco", or "sam")

    Flow:
      1) Validate CLI args and decode the base64 payload into Python objects.
      2) Route to the correct normalizer based on 'source'.
      3) Print a JSON-encoded list of normalized opportunities to stdout.
         (This is the contract expected by the calling n8n/Docker process.)
    """
    null = None
    false = False

    if len(sys.argv) < 3:
        print("Uso: python normalize_opportunities.py <arquivo.json> <cal|laco|sam>", file=sys.stderr)
        sys.exit(2)

    base64_raw = sys.argv[1]
    source = sys.argv[2].lower().strip()

    # Decode the base64-encoded JSON payload into Python objects
    lista = json.loads(base64.b64decode(base64_raw).decode("utf-8"))

    # Dispatch to the appropriate normalizer without altering logic
    if source == "cal":
        oportunidades = format_opportunities_cal(lista)
    elif source == "laco":
        oportunidades = format_opportunities_laco(lista)
    elif source == "sam":
        oportunidades = format_opportunities_sam(lista)
    else:
        # For any unrecognized source, emit a sentinel message and continue.
        # (Original behavior preserved: print text to stdout without raising.)
        print("Nada")

    # Emit normalized rows as UTF-8 JSON (no ASCII escaping for readability)
    print(json.dumps(oportunidades, ensure_ascii=False))

if __name__ == "__main__":
    _main_cli()
