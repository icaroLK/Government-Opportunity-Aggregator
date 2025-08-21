from __future__ import annotations

import json
import sys
from datetime import datetime
import pytz
import hashlib
import base64

def generate_hash(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def format_opportunities_cal(raw_events):
    out = []
    utc = pytz.utc
    null = None
    false = False
    for ev in raw_events:
        out = []
    utc = pytz.utc
    for ev in raw_events:
        ev_id = ev.get("event_id") or ev.get("opportunity_id") or None
        title = ev.get("event_name") or ev.get("title") or None

        posted_date = None
        created_at = None
        deadline = ev.get("end_date") or None
        # parsing end_date as deadline
        end = ev.get("end_date")
        # if end:
        #     try:
        #         dt = dateutil.parser.parse(end, tzinfos={'PDT': pytz.timezone('US/Pacific')})
        #         dt_utc = dt.astimezone(utc)
        #         deadline = dt_utc.isoformat()
        #     except:
        #         pass

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

        award_date = ev.get("award_date") or None
        award_number = ev.get("award_number") or None
        award_amount = ev.get("award_amount") or None
        awardee_name = ev.get("awardee_name") or None
        awardee_uei = ev.get("awardee_uei") or None
        awardee_cage = ev.get("awardee_cage") or None

        created_at = ev.get("created_at") or None

        token_cost = ev.get("token_cost") or None


        chk_src = f"{ev_id or ''}|{title or ''}"
        checksum = generate_hash(chk_src)

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
    out = []
    utc = pytz.utc
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    for bid in raw_bids:
        bid_id = bid.get("bid_id")
        title = bid.get("title")
        solicitation_number = bid.get("solicitation_number")
        agency = bid.get("department")

        # deadline parsing
        close = bid.get("close_date", "").strip()
        if close == "Continuous":
            close = ""
        

        # checksum generation
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
            "service_line": bid.get('type') or None,
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
        isActive = ev.get("active")
        if isActive == "Yes":
          active = True
        else:
          active = False
        
        # Award fields
        award_info = ev.get("award") or {}
        award_date = award_info.get("date")
        award_number = award_info.get("number")
        award_amount = award_info.get("amount")
        awardee = award_info.get("awardee") or {}
        awardee_name = awardee.get("name")
        awardee_uei = awardee.get("ueiSAM")
        awardee_cage = awardee.get("cageCode")
        
        # Active status
        active = ev.get("active") == "Yes"
        
        # Checksum
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

def _main_cli() -> None:
#    oportunidades = []
    null = None
    false = False
    if len(sys.argv) < 3:
        print("Uso: python normalize_opportunities.py <arquivo.json> <cal|laco|sam>", file=sys.stderr)
        sys.exit(2)


    base64_raw = sys.argv[1]
    source = sys.argv[2].lower().strip()
    #print("[DEBUG] sys.argv =", sys.argv)
    #print(lista)
    #print("\n\nSOOOOOOOOOOOOURCE")
    lista = json.loads(base64.b64decode(base64_raw).decode("utf-8"))
    #print(lista)
    #print(source)
    if source == "cal":
        oportunidades = format_opportunities_cal(lista)
    elif source == "laco":
        oportunidades = format_opportunities_laco(lista)
    elif source == "sam":
        oportunidades = format_opportunities_sam(lista)
    else:
        print("Nada")
    print(json.dumps(oportunidades, ensure_ascii=False))

if __name__ == "__main__":
    _main_cli()
