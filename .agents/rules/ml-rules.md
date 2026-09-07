---
trigger: always_on
---

# CLAUDE.md — ml/ (and backend/app/services/vision/)

Applies when working on detection, OCR, extraction, or calibration —
whether that's the training notebook in `ml/` or the runtime services in
`backend/app/services/vision/`. Read the root `CLAUDE.md` too.

## Detection: YOLOv8n + mandatory OpenCV fallback

- Model: `ultralytics` YOLOv8n, fine-tuned on our own ~250-300 image
  dataset (Roboflow export, YOLOv8 format), trained on free-tier Colab
  (T4 GPU).
- **Day 5 is a hard decision gate.** Check `mAP50` from the training run.
  If it's not clearly good enough to trust in a live demo, the OpenCV
  contour-detection fallback (`opencv_fallback_detect()` in
  `detection.py`) becomes the PRIMARY method for the rest of the build —
  don't keep iterating on YOLO past this point hoping it improves.
- Whichever is primary, the other must remain a working fallback at all
  times. `detect_pdp()` must never raise — if YOLO's weight file doesn't
  exist or confidence is below `YOLO_CONFIDENCE_THRESHOLD` (0.6), fall
  through to OpenCV automatically.
- Do not attempt SAM2 or a custom multi-class detector — out of scope,
  see root `CLAUDE.md`.

## Dataset — shape diversity over category diversity

When advising on what images to collect/prioritize: package **shape**
(flat box, bottle, pouch, cylinder/can, tube) matters more for detector
generalization than product category. Don't optimize the dataset
collection guidance around "more food items" — a flat cardboard box
looks similar to a detector whether it's biscuits or soap.

Small, deliberate non-food examples (a few images each) are still needed
to exercise the three category exceptions during the demo:
`medical_device`, `bulk_exempt`, `food_expiry` — these don't need to be
part of the YOLO training set, they're test cases for the rule engine.

## OCR: EasyOCR primary

Use EasyOCR (`easyocr.Reader(["en"], gpu=False)`) as the default OCR
engine. Tesseract is an acceptable secondary/fallback option if EasyOCR
has issues in a specific environment. Do not integrate or fine-tune
TrOCR — real fine-tuning needs a dataset size and training time this
project doesn't have; if used at all, it would only be pretrained/
zero-shot, and even that is lower priority than getting EasyOCR working
well.

## Field extraction: never claim raw regex is "error-tolerant"

The correct pipeline is:
`raw OCR text → normalize → RapidFuzz fuzzy match against FIELD_KEYWORDS
→ regex-validate the matched VALUE → confidence score`

Raw regex against raw OCR output will miss common OCR errors (e.g. `MRP`
misread as `M8P`). Fuzzy matching happens on the field *label* before
regex validates the field *value*. Don't write or describe extraction
logic that skips the fuzzy-match step — this was a specific fix agreed
after review, not an optional enhancement.

Do not fine-tune or attempt LayoutLMv3 for this build. It needs a
labeled entity-tagging dataset (NER-style, not just bounding boxes) that
this project's timeline doesn't support — it stays a documented
production-roadmap direction only.

## Calibration: dual-path, general fallback

- Primary: ArUco marker detection (`cv2.aruco`) — known physical marker
  size gives reliable mm-per-pixel conversion.
- Fallback: a **user-selected object of known real-world size**, passed
  via the API (`known_object_size_mm`). Do not hardcode a specific
  object like "a ₹10 coin" in code, comments, or UI copy — the
  fallback must generalize to whatever reference object is actually
  available at demo time. Perspective correction is not attempted for
  this prototype; note that as a known limitation if asked, don't
  silently overclaim accuracy.
- If neither calibration method succeeds, font-height checks route to
  `REVIEW_REQUIRED` — never silently skip the check or fabricate a
  measurement.

## Confidence threshold

`0.75` is the standing threshold below which any individual check
result becomes `REVIEW_REQUIRED` regardless of whether the underlying
logic would otherwise say PASS or FAIL. Keep this threshold in one
place (a constant), don't duplicate the literal value across files.

## Claims discipline (see root CLAUDE.md too)

Don't write comments, docstrings, or explanatory text claiming a
specific accuracy/mAP/F1 number unless it was actually produced by
running our own training/eval on our own data. "SROIE benchmarks show
~X%" is fine as a cited external reference; "our system achieves X%"
is only fine if X was actually measured here.