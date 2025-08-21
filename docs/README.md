# US & CA Government Opportunity Aggregator

![Tests](https://github.com/icarolk/gov-opportunity-aggregator/actions/workflows/tests.yml/badge.svg)

End‑to‑end procurement pipeline that **scrapes Cal eProcure & SAM.gov**, **normalizes + enriches + classifies + scores**, **maps capacity** against your internal hours, and **surfaces a prioritized view with actionable Slack alerts** — all designed to run locally with **one `docker compose up`** and light reviewer setup.

> **Assessment goals covered (per brief):** scraping, normalization, enrichment & classification, scoring & capacity mapping, prioritized view + Slack alert with Decision link, tests (≥70% coverage) and CI badge, README + Loom, and demo URL.

---

## Contents

* [Architecture](#architecture)
* [Quickstart](#quickstart)
* [Workflow import](#workflow-import)
* [Credentials to add in n8n](#credentials-to-add-in-n8n)
* [Airtable base & interface links](#airtable-base--interface-links)
* [Data model & capacity mapping](#data-model--capacity-mapping)
* [Repository layout](#repository-layout)
* [Tests & coverage (≥70%)](#tests--coverage-70)
* [What the reviewer will do](#what-the-reviewer-will-do)
* [Troubleshooting](#troubleshooting)
* [Loom & Demo](#loom--demo)
* [License](#license)

---

## Architecture

**Orchestration:** n8n (Docker)
**Scrapers:** Playwright Python (Cal eProcure + LACo Bids helper) and SAM.gov JSON mapping
**Normalizer:** `scrapers/formatter.py` emits a unified schema for all sources
**Analyzer:** Enrichment + classification (rule‑first with LLM fallback), scoring, and capacity fit
**Storage/UI:** Airtable base + public Interface for a prioritized view
**Alerts:** Slack message with **Accept / Ignore** decision links that call a local n8n webhook

```
Cal eProcure / LACo   SAM.gov
      \                 /
       \   Ingest (01) /
        \             /
        Normalize (02)  →  Enrich+Classify (03) → Score+Capacity (04) → Notify (05)
                                  |                          |               |
                                  |                          |               +--> Slack alert (buttons = links)
                                  |                          +--> Airtable (status, decision)
                                  +--> Token cost log
```

---

## Quickstart

1. **Prereqs**: Docker + Docker Compose.
2. **Copy env file** (edit as needed):

```bash
cp .env.example .env
# set N8N auth, port, WEBHOOK_URL, and scraper limits
```

3. **Boot n8n** (auth via envs if enabled):

```bash
docker compose up -d
```

4. Open **n8n UI** at `http://localhost:${N8N_PORT:-5678}`.
5. **Import the workflows** from the `workflows/` folder (see next section).
6. In **n8n → Credentials**, add **OpenAI**, **Airtable**, and **Slack** (instructions below).
7. In **n8n**, run the **01→05** workflows (or trigger ingest first, then follow the chain).
8. Open the **Airtable Interface** (link below) to see the prioritized view.

> **Note**: By design, workflows are **not auto‑imported** on container start; import once and save.

---

## Configuration (`.env`)

Use `.env.example` as a baseline and copy to `.env` before starting. Key variables:

**n8n**

```
N8N_PORT=5678              # UI + webhook port (keep consistent with WEBHOOK_URL)
GENERIC_TIMEZONE=America/Sao_Paulo
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change-me
N8N_SECURE_COOKIE=false     # local dev
N8N_ENCRYPTION_KEY=please-change-this-32+chars
WEBHOOK_URL=http://localhost:5678/   # base URL used in decision links/webhooks
```

**Scrapers**

```
HEADLESS=true
SCRAPE_CAL_QTY=20
SCRAPE_LACO_QTY=20
SCRAPE_SAM_QTY=20          # if applicable to your SAM.gov ingest
```

> For your local `.env`, you can pick a different port (e.g., `5897`); just ensure `WEBHOOK_URL` uses the same port (e.g., `http://localhost:5897/`). This keeps Slack **Decision** links working against your local n8n.

## Workflow import

**UI import (recommended):**

1. In n8n, go to **Workflows → Import from File**.
2. Select each JSON in `/workflows` (e.g., `01_ingest.json` … `05_notify.json`).
3. Save. Ensure any environment expressions resolve (see credentials section).

**CLI (optional):**

```bash
# Copy workflows into the running container, then import
docker cp workflows gov-n8n:/workflows
docker exec -it gov-n8n n8n import:workflow --input=/workflows/*.json
```

---

## Credentials to add in n8n

> Keep secrets in **n8n Credentials** (no secrets in git). Use env vars in nodes for Base IDs, table names, and channels.

### 1) OpenAI

* **n8n → Credentials → New → OpenAI**
* **API Key**: your key
* Save as: `OpenAI (Classifier)` (or any name — pick the same name in the node)
* Model is selected per node (document the one you used if parameterized).

### 2) Airtable

* **n8n → Credentials → New → Airtable**
* **Personal Access Token (PAT)** scopes (minimum):

  * `data.records:read`, `data.records:write`
  * `schema.bases:read` (if you browse bases)
* Save as: `Airtable (Prod)`
* In nodes, keep IDs as expressions reading envs, e.g.:

  * `{{$env.AIRTABLE_BASE_ID}}`
  * `{{$env.AIRTABLE_TABLE_OPPORTUNITIES}}`

### 3) Slack

**Bot Token (recommended)**

* Create a Slack app with `chat:write` (and any additional scopes you need).
* Install to workspace; copy **Bot User OAuth Token** (`xoxb-…`).
* **n8n → Credentials → New → Slack** → paste token.
* Save as: `Slack (Alerts)`. In the Slack node, select this credential and a channel (env‑friendly: `{{$env.SLACK_CHANNEL}}`).

> **Decision Links**: The alert includes **Accept/Ignore** links that point to your local n8n webhook, e.g.
> `http://localhost:5678/webhook/decision?checksum=...&decision=Go`
> Clicking from Slack opens the reviewer’s browser and hits the local webhook — no public tunnel required.

---

## Airtable base & interface links

* **Public Interface (demo):** See `demo_url.txt` or open directly:
  [https://airtable.com/appWUC1bwghJqFCxS/shr5Mxeep7Gw2K8Gx](https://airtable.com/appWUC1bwghJqFCxS/shr5Mxeep7Gw2K8Gx)
* **Duplicate this Base** (create your own copy in one click):
  [https://airtable.com/appWUC1bwghJqFCxS/shrh4jjeE0pMPMooh](https://airtable.com/appWUC1bwghJqFCxS/shrh4jjeE0pMPMooh)

> The workflows read/write to your **own** duplicated base (IDs/Tables are parameterized).

---

## Data model & capacity mapping

Unified schema (excerpt) written by the normalizers in `scrapers/formatter.py`:

```
{
  "opportunity_id": str,
  "title": str,
  "solicitation_number": str|null,
  "agency": str|null,
  "posted_date": ISO|null,
  "deadline": ISO|string|null,
  "naics_code": str|null,
  "classification_code": str|null,
  "service_line": "Janitorial|Construction|IT|Logistics|Safety/Fire|Medical|Education|Aviation|Other"|null,
  "estimated_value": number|null,
  "effort_hours": number|null,
  "effort_bucket": "Low|Medium|High"|null,
  "type": str|null,
  "active": boolean|null,
  "decision": "Go|Review|No Go"|null,
  "score": number|null,
  "created_at": ISO|null,
  "checksum": str,
  "token_cost": number|null
}
```

**Capacity reference** lives in `data/resource_capacity.csv`:

```
service_line,hours_available
Janitorial,200
Construction,120
IT,80
Logistics,60
Safety/Fire,40
Medical,50
Education,70
Aviation,30
Other,40
```

**Rule:** compare `effort_hours` vs `hours_available` per `service_line` → flag `decision`:

* ✅ **Go** (have capacity)
* ⚠️ **Review** (near the limit)
* ❌ **No Go** (insufficient capacity)

The **scoring** step aggregates fit signals (deadline proximity, category fit, etc.) into `score` to drive the prioritized view. Token usage/cost from the LLM nodes is logged at the end of the run.

---

## Repository layout

```
.
├─ .env.example                 # copy to .env and adjust
├─ data/
│  └─ resource_capacity.csv
├─ docs/
│  ├─ LICENSE
│  └─ README.md
├─ scrapers/
│  ├─ cal_eprocure_scraper.py     # Playwright headless scrape
│  ├─ lacobids_scraper.py         # LA County helper scraper
│  ├─ formatter.py                # Normalizers → unified schema + checksum
│  ├─ Dockerfile                  # Playwright runtime image
│  └─ requirements.txt
├─ workflows/                     # Exported n8n JSON (01…05)
├─ tests/
│  ├─ test_formatter_cal.py
│  ├─ test_formatter_laco.py
│  ├─ test_formatter_sam.py
│  └─ test_hash_and_idempotency.py
├─ docker-compose.yml             # n8n service (basic auth via envs)
├─ n8n.Dockerfile                 # Adds docker-cli (keeps default entrypoint)
├─ requirements.txt               # pytest, pytest-cov, pytest-asyncio
├─ demo_url.txt                   # public interface link
├─ loom_link.txt                  # 8-min walkthrough link
└─ pytest.ini                     # pytest config
````
---

## Tests & Coverage (≥70%)

You can run the test suite in two ways: **locally with Python** or **inside Docker**.  
Both methods will produce coverage reports (minimum 70% required).

---

### Option 1: Local (Python environment)
From the repository root, create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Run tests with coverage:

```bash
pytest -q --cov=scrapers --cov-report=term-missing
```
Option 2: Inside Docker
If you are already running the project via docker compose up, you can execute tests inside the scraper container without setting up Python locally:

```bash
docker exec gov-scrapers python -m pytest -q \
  --cov=scrapers \
  --cov-config=/workspace/.coveragerc \
  --cov-report=term-missing \
  /workspace/tests
```

Output shows per‑file coverage; the suite exercises normalizers and checksum idempotency.

**CI badge:** Add a GitHub Actions workflow (`.github/workflows/tests.yml`) that runs the above.
Update the badge at the top of this README to point to your repo:

```
![Tests](https://github.com/user/repository/actions/workflows/tests.yml/badge.svg)
```

---

## What the reviewer will do

1. **Clone** the repo.
2. `docker compose up -d` → boots **n8n**.
3. Open `http://localhost:5678` → **Import** workflows from `/workflows`.
4. **Add credentials** in n8n: OpenAI, Airtable, Slack (as above).
5. **Run** the 01→05 chain, verify **Airtable Interface** shows prioritized data.
6. Confirm **Slack alert** posts with **Accept/Ignore** links; clicking **updates status** in Airtable and records **Decision Made**.
7. Run tests: `pytest -q --cov=scrapers --cov-report=term-missing` (or via CI).

> Minimum pass: ≥40 opportunities (≤72h old), duplicate‑run idempotency, token cost logged, Go/Review/No Go, CI badge, README + Loom.

---

## Troubleshooting

* **n8n auth:** set `N8N_BASIC_AUTH_ACTIVE=true` and provide `N8N_BASIC_AUTH_USER` & `N8N_BASIC_AUTH_PASSWORD` via environment or `.env` consumed by Docker Compose.
* **Playwright headless:** scrapers default to `HEADLESS=true`. Override with envs if needed.
* **Row counts:** `SCRAPE_CAL_QTY` / `SCRAPE_LACO_QTY` control how many rows are fetched during demo runs.
* **Webhook links from Slack:** links target `http://localhost:${N8N_PORT}/...` and should match `WEBHOOK_URL`. If you change `N8N_PORT`, update `WEBHOOK_URL` accordingly so Decision links resolve locally...\`. Keep the port/path consistent with your local n8n.
* **Airtable types:** date fields expect ISO (e.g., `YYYY-MM-DD`). If Airtable rejects a value, enable **Typecast** in the node or pre‑normalize the field.

---

## Loom & Demo

* **Public Interface:** see `demo_url.txt` or open [Interface Airtable](https://airtable.com/appWUC1bwghJqFCxS/shr5Mxeep7Gw2K8Gx)
* **Loom walkthrough:** see `loom_link.txt` or open [Loom video](https://www.loom.com/share/b8cba89954d74ee0a7232015a56b0703?sid=1bcbcf61-2de7-4c95-9779-42489e993843)

---

## License

See [`docs/LICENSE`](./docs/LICENSE).


