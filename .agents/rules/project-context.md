---
trigger: always_on
---

CLAUDE.md — SIH26034 Legal Metrology Compliance Checker
This file applies to the whole repo. Subdirectories (`backend/`, `frontend/`,
`ml/`) have their own `CLAUDE.md` with more specific rules — read those too
when working inside those folders. If a nested rule conflicts with this one,
the nested (more specific) rule wins.
What this project is
A prototype that scans a packaged-commodity label photo and checks it
against the Legal Metrology (Packaged Commodities) Rules, 2011 — SIH
problem statement SIH26034. Built for a 10-day hackathon prototype, not
production. Every decision here optimizes for "demoable and defensible in
front of judges," not "enterprise-scale."
Team & ownership (do not cross these lines without asking)
Shubh — `backend/app/services/vision/*` (detection, OCR, extraction,
calibration), `backend/app/routers/scan.py`
Aditya — `backend/app/services/compliance/*`, `backend/app/services/reporting/*`,
`backend/app/db/*`, `backend/app/routers/{history,search,reports,dashboard,auth}.py`
Keshav — everything in `frontend/`
Gauri — dataset collection/annotation (`ml/dataset/`, Roboflow project)
Parul — `backend/app/data/rules/lmpc_rules_v1.json` (legal content),
technical documentation
Mahi — QA, demo rehearsal, deck
If a task touches another owner's files, flag it — don't silently edit
someone else's module.
The contract — never break this silently
`docs/API_CONTRACT.md` and `backend/app/schemas/*.py` define the shape
every endpoint returns. Keshav's frontend, Aditya's rule engine, and
Shubh's pipeline all depend on these staying stable. Never rename or
remove a field in `app/schemas/` without saying so explicitly in your
response and flagging it for the team — treat this the same as any
other breaking API change.
The core design principle: confidence-aware, never binary
Every compliance check, everywhere in this codebase (backend logic,
frontend display, PDF/DOCX reports) uses three states:
`PASS` | `FAIL` | `REVIEW_REQUIRED` — never collapse this to a boolean
compliant/non-compliant. If confidence on any check is below 0.75, the
result is `REVIEW_REQUIRED`, not a forced PASS or FAIL. This is a
deliberate product decision (a single photo can't make a legal
determination with certainty) — don't "simplify" it away.
Fallback-first architecture — nothing is allowed to hard-fail
Every pipeline stage has a fallback and must always return something,
never raise an unhandled exception on bad/unusual input:
Detection: YOLOv8n → OpenCV contour detection fallback
Calibration: ArUco marker → user-selected known-object fallback → skip
(font checks become `REVIEW_REQUIRED`, not crash)
Field extraction enhancement: optional Vision-LLM → local OCR + fuzzy
match is always the primary, always-available path
When writing any pipeline code, ask: "what does this do on a blurry,
oddly-lit, or unexpected image?" The answer must never be a crash or a
silent wrong answer — it's a low-confidence result routed to review.
Timeline discipline
Day 5: YOLO fine-tune decision gate. If mAP isn't clearly good, the
OpenCV fallback becomes primary — don't keep sinking time into YOLO past
this point.
Day 7: feature freeze. No new features after this — only bug fixes,
integration, and polish.
Day 8: full dry run on the real demo laptop with real products.
If asked to add scope after day 7, push back and suggest it as a "roadmap"
talking point instead, not a build task.
Core vs. stretch (the pre-agreed cut list)
Never cut, this is the minimum demoable product:
upload → detect (YOLO or fallback) → OCR → extract → Rule 6/7 check →
PASS/FAIL/REVIEW → PDF report with evidence image → basic scan history.
Cut first if behind schedule (in this order): DOCX/JSON export → RBAC
(fall back to no-login demo) → dashboard charts (fall back to a single
stats line) → 2nd/3rd rule-category exception → one of the two calibration
methods.
Don't silently drop core-tier scope to make room for stretch-tier work.
Claims discipline — this matters for a legal-compliance product
Do not write code comments, docstrings, docs, or UI copy that state an
accuracy/performance number that hasn't actually been measured on this
project's own test data. No borrowed benchmark stats presented as our
results. If a number is aspirational or from external literature, label
it that way explicitly (e.g. "per published SROIE benchmarks" not "our
system achieves").
Explicitly out of scope for this build (production roadmap only)
Do not implement or suggest implementing: Celery/Redis task queues,
PostgreSQL/PostGIS, multi-tenant infrastructure, HashiCorp Vault, ECDSA
report signing, LiDAR/ToF depth sensing, TrOCR or LayoutLMv3 fine-tuning,
SAM2, React Native/ARKit/ARCore mobile clients, full OAuth2. These are
real production-direction ideas but out of scope for a 10-day prototype —
if asked to build toward them, note that they belong in the roadmap
section of the deck, not the codebase.
Key reference docs
`docs/API_CONTRACT.md` — the full endpoint contract, read this before
changing any router or schema
`backend/app/data/rules/lmpc_rules_v1.json` — the structured legal rules
the compliance engine reads from; don't hardcode rule values in Python
