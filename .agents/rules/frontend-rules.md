---
trigger: always_on
---

# CLAUDE.md — frontend/

Applies when working inside `frontend/`. Read the root `CLAUDE.md` too.

## Stack (do not substitute without asking)

- **Framework:** React (via Vite) — NOT Streamlit, NOT Next.js. This
  project deliberately uses a real frontend/backend split (React +
  FastAPI) rather than Streamlit, because a dedicated frontend developer
  (Keshav) is on the team — don't suggest collapsing back to Streamlit.
- **Routing:** react-router-dom
- **Styling:** Tailwind CSS
- **Charts:** recharts (already in `package.json`) — don't add
  chart.js/d3/plotly on top of it, one charting library is enough for
  this scope
- **HTTP client:** axios, wrapped in `src/api/client.js`
- **State management:** local component state (`useState`) and React
  Context if truly needed for auth state. Do NOT add Redux, Zustand, or
  any other state library — this app has 5 pages, it doesn't need one.

## All API calls go through `src/api/client.js`

Never write an inline `fetch()` or a new `axios` call directly inside a
component. Every backend interaction is a function in `client.js` that
matches an endpoint in `docs/API_CONTRACT.md` exactly. If you need a new
kind of API call, add a function there first, then use it in the
component. This keeps every request in one place, matching the one file
the backend devs also treat as the contract's frontend mirror.

## Pages — these five, matching the contract

`Upload.jsx`, `Results.jsx`, `History.jsx`, `Dashboard.jsx`, `Login.jsx`.
Don't add new top-level pages without checking whether the functionality
fits inside one of these five first — the scope was deliberately kept to
this set to match the PS's named functional requirements exactly.

## Status display — the three-state rule applies here too

`overall_status` and every `compliance_results[].status` is one of
`PASS` | `FAIL` | `REVIEW_REQUIRED`. Never render this as a boolean toggle,
a single checkmark/X, or collapse `REVIEW_REQUIRED` into either PASS or
FAIL for "simpler" UI. Use a consistent color mapping everywhere it
appears:
- `PASS` → green
- `FAIL` → red
- `REVIEW_REQUIRED` → amber/orange

This three-way distinction is a core selling point of the project (see
root `CLAUDE.md`) — the UI must make it visually obvious, not just
technically present in the data.

## Evidence-first display

The Results page should show the annotated evidence image
(`evidence_image_url`) prominently — this is the pitch's central
differentiator ("evidence-backed, explainable compliance," not a
black-box verdict). Don't bury it below the text findings; it should be
one of the first things visible on that page.

## Auth

Store `access_token` and `role` in `localStorage` (already handled in
`client.js`). This is fine for a hackathon demo — don't build a more
sophisticated token-refresh or secure-storage scheme, it's out of scope
for the timeline.

## Camera capture

Live camera capture via the browser is a nice-to-have (day 7, if time
allows) — file upload must always work as the baseline path regardless.
Don't make the Upload page depend on camera access being granted; treat
it as an enhancement, not the only input method.

## Scope discipline

Don't add: multi-language i18n, dark mode, extensive mobile-responsive
polish, animations/transitions beyond basic. The demo runs on a laptop
in front of judges — prioritize the core flow working reliably over
visual polish beyond "clean and readable." If asked to add something
outside the five pages above, check the root `CLAUDE.md` cut list first.

## When the backend contract changes

If a backend dev tells you a schema field changed, update
`src/api/client.js` and every page that consumes that field in the same
session — don't leave the frontend silently reading a field that no
longer exists in the response.