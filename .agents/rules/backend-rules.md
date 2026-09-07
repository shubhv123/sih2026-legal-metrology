---
trigger: always_on
---

# CLAUDE.md — backend/

Applies when working inside `backend/`. Read the root `CLAUDE.md` too — this
file adds backend-specific detail on top of it.

## Stack (do not substitute without asking)

- **Framework:** FastAPI (Python 3.11)
- **Validation/schemas:** Pydantic v2 — every request/response shape lives in
  `app/schemas/`
- **DB:** SQLAlchemy + SQLite (`compliance.db`). Not Postgres — that's a
  roadmap item, don't migrate to it mid-build.
- **Server:** `uvicorn app.main:app --reload`, local host only for the demo
  (no cloud deployment required)
- **Auth:** lightweight, 2 hardcoded roles (`inspector`, `admin`) is
  sufficient. Don't build full OAuth2/RBAC infrastructure.

## Layered structure — respect it

```
app/routers/      Endpoint definitions ONLY — parse request, call a
                   service function, return the response. No business
                   logic here.
app/services/      All actual logic lives here, split by domain:
  vision/          Shubh: detection, ocr, extraction, calibration
  compliance/       Aditya: rule_engine, placement, confidence
  reporting/        Aditya: pdf_report, docx_report, json_report
app/schemas/       Pydantic models — THE contract. Shared, don't touch
                   without flagging it.
app/db/            SQLAlchemy models + session setup
app/data/rules/    lmpc_rules_v1.json — legal rules as DATA, not code
```

If you're about to write compliance-checking logic inside a router
function, stop — it belongs in `services/compliance/`. Routers stay thin.

## The rule engine reads data, not hardcoded Python

`app/data/rules/lmpc_rules_v1.json` is the single source of truth for
mandatory fields, font-height thresholds, and category exceptions. When
extending rule logic, add to this JSON file and write generic code that
reads it — don't hardcode a new field name or threshold directly in
`rule_engine.py`. This is a deliberate architecture choice (regulatory
changes shouldn't require redeploying code) — preserve it.

## Category exceptions — capped at 3, do not expand

`medical_device`, `bulk_exempt`, `food_expiry` are the only three category
exceptions in scope. Don't add a fourth without the team agreeing —
this was a deliberate scope decision to avoid the full statutory
exception taxonomy eating build time.

## Specific library choices (these were decided for a reason)

- **OCR:** EasyOCR primary. Tesseract as a secondary option if needed.
  Do not integrate PaddleOCR or TrOCR unless there's spare time after
  core features are done and the team agrees.
- **Detection:** `ultralytics` YOLOv8n, fine-tuned on our own dataset.
  OpenCV (`cv2.findContours` etc.) is the mandatory fallback — the
  `/scan` endpoint must work even if the YOLO weight file doesn't exist
  yet or underperforms.
- **Fuzzy matching:** RapidFuzz (not fuzzywuzzy/thefuzz — RapidFuzz is
  faster and has a cleaner license). Used to normalize OCR text before
  regex validation — raw regex alone is NOT considered acceptable field
  extraction (it doesn't tolerate OCR typos).
- **PDF generation:** ReportLab.
- **DOCX generation:** python-docx.
- **Calibration:** `cv2.aruco` for the primary method. Fallback accepts
  a user-specified real-world size for a selected reference object —
  don't hardcode a specific object (e.g. a particular coin denomination).

## Error handling — this is non-negotiable

`/api/v1/scan` must never return a raw 500 error or unhandled exception
on a bad, blurry, or unusual image. Catch failures at each pipeline
stage and degrade to a low-confidence result routed to
`REVIEW_REQUIRED` instead. A demo that crashes on an unexpected judge's
product is a worse outcome than one that says "low confidence, please
verify manually."

## Every compliance result needs a rule version stamp

Every `ComplianceResult` object carries `rule_version` (e.g.
`"LMPC-2011-v1.0"`, read from the rules JSON's `version` field). This
isn't decorative — it's the "rule-versioning" design decision from the
project's feasibility review. Don't drop it when adding new check types.

## Testing

Given the timeline, keep tests thin but present: at minimum, a smoke
test per router (`tests/test_scan.py` etc.) confirming a 200 response
with the right top-level shape. Don't chase full coverage — prioritize
the pipeline actually working over test completeness.

## What NOT to build here

Celery, Redis, PostgreSQL, PostGIS, MinIO/S3, HashiCorp Vault, ECDSA
report signing, multi-tenant architecture. These are real
production-roadmap ideas (see root `CLAUDE.md`) but out of scope for
this codebase. If you find yourself reaching for one of these, stop and
use the SQLite/local-file equivalent instead.