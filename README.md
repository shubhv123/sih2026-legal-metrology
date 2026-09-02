# SIH26034 — Legal Metrology Compliance Checker

Automated packaging-label compliance checking against the Legal Metrology
(Packaged Commodities) Rules, 2011.

## Repo structure

```
backend/          FastAPI app — Shubh (vision/ML) + Aditya (rules/repository/reports/auth)
frontend/         React app — Keshav
ml/               Dataset + YOLOv8 training notebook — Gauri (data), Shubh (training)
docs/             API_CONTRACT.md (read this first), ARCHITECTURE.md, RULES_REFERENCE.md
```

## Day 1 — start here

1. Read `docs/API_CONTRACT.md` — this is the contract every endpoint follows. Locked unless the whole team agrees to a change.
2. **Shubh + Aditya:** `cd backend`, follow `backend/README.md` setup, confirm `uvicorn app.main:app --reload` serves working mocks at `/docs`.
3. **Keshav:** `cd frontend`, `npm install`, `npm run dev`, point `src/api/client.js` at the running backend, confirm you can hit every mock endpoint.
4. **Gauri:** start photographing product labels today — see `ml/notebooks/train_yolov8.ipynb` for what the dataset needs to look like (Roboflow YOLOv8 export format).
5. **Parul:** fill in `backend/app/data/rules/lmpc_rules_v1.json` with verified Rule 6/7 values — this file is the single source of truth the rule engine reads from.
6. **Mahi:** set up the test-plan template and start sourcing the 5-6 real demo products.

## Milestones

| Day | Milestone |
|---|---|
| 1 | API contract locked, all mocks running, everyone unblocked to build in parallel |
| 4-5 | YOLOv8 decision gate — keep it or pivot fully to OpenCV fallback |
| 5 | Early end-to-end integration check (not the full dry run — just "does data flow through") |
| 7 | **Feature freeze** — no new features after this |
| 8 | **Full dry run** — whole team, real products, actual demo laptop |
| 9-10 | Bug fixes, rehearsal, backup video, final polish only |

See the full 10-day breakdown per person in the project plan (shared separately).

## Core vs stretch (pre-agreed cut list — see plan doc for full reasoning)

**Never cut:** upload → detect (YOLO or OpenCV fallback) → OCR → extract → Rule 6/7 check → PASS/FAIL/REVIEW → PDF report with evidence → basic history

**Cut first if behind schedule:** DOCX/JSON export, RBAC, dashboard charts (fall back to a stats line), 3rd category exception, one of the two calibration methods
