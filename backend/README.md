# Backend — Legal Metrology Compliance Checker (SIH26034)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs (auto-generated): http://localhost:8000/docs

## Who owns what

| Path | Owner | Notes |
|---|---|---|
| `app/routers/scan.py` | Shubh | Main pipeline endpoint — currently returns a mock response |
| `app/services/vision/*` | Shubh | Detection, OCR, extraction, calibration |
| `app/routers/history.py`, `search`, `dashboard.py`, `reports.py`, `auth.py` | Aditya | Repository, search, dashboard stats, exports, login |
| `app/services/compliance/rule_engine.py` | Aditya | Reads `app/data/rules/lmpc_rules_v1.json`, evaluates compliance |
| `app/db/models.py` | Aditya | SQLAlchemy tables |
| `app/data/rules/lmpc_rules_v1.json` | Parul (content) / Aditya (consumes it) | Structured Rule 6/7 data — do not hardcode rules in Python, edit this file |
| `app/schemas/*` | Shared contract — **do not change field names without telling the team** | See `docs/API_CONTRACT.md` |

## Day 1 priority
Every router currently returns a **mock response matching the real schema**. This means:
- Keshav can build the entire frontend against these mocks starting today, without waiting for the real pipeline.
- Shubh and Aditya can replace mock internals independently, as long as the response still matches `app/schemas/*`.

**Rule: if you need to change a schema field, ping the team first** — Keshav's frontend and the other backend dev are both depending on it staying stable.

## Running with mocks (day 1, no ML deps needed)
The scan endpoint mock doesn't require EasyOCR/YOLO to be installed to return a response — useful for Keshav to start immediately. Only install `easyocr`/`ultralytics` when you start replacing the mock with real logic.
