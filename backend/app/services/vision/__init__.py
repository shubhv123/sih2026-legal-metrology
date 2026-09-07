"""Vision and ML services module (Owner: Shubh).

Covers:
- YOLOv8 PDP detection + OpenCV contour fallback
- EasyOCR transcription
- RapidFuzz fuzzy field extraction
- Dual scale calibration (ArUco marker + user-selected reference object)
- Pipeline stubs for end-to-end testing
"""

from typing import Any

try:
    from app.services.vision.calibration import calibrate_aruco, calibrate_known_object
except ImportError:
    calibrate_aruco = None  # type: ignore
    calibrate_known_object = None  # type: ignore

try:
    from app.services.vision.detection import detect_pdp as detect_pdp_model
    from app.services.vision.detection import opencv_fallback_detect as opencv_fallback_detect_fn
except ImportError:
    detect_pdp_model = None  # type: ignore
    opencv_fallback_detect_fn = None  # type: ignore

try:
    from app.services.vision.extraction import extract_fields, run_ocr
except ImportError:
    extract_fields = None  # type: ignore
    run_ocr = None  # type: ignore


def detect_pdp(image_path: str) -> dict[str, Any]:
    """Isolates Principal Display Panel (PDP) using YOLOv8n with OpenCV contour fallback."""
    return {"bbox": [100, 40, 500, 600], "confidence": 0.95, "method": "yolov8"}


def opencv_fallback_detect(image_path: str) -> dict[str, Any]:
    """Mandatory OpenCV contour fallback when YOLO confidence is below 0.6 or weights missing."""
    return {"bbox": [100, 40, 500, 600], "confidence": 0.70, "method": "opencv_contours"}


def calibrate_scale(
    image_path: str, known_object_size_mm: float | None = None
) -> tuple[float | None, str]:
    """Estimates mm-per-pixel scale factor using ArUco marker or reference object.

    Returns: (scale_factor_mm_per_pixel, calibration_method)
    """
    if known_object_size_mm:
        return (known_object_size_mm / 100.0, "reference_object")
    return (0.082, "aruco")


def run_ocr_and_extract(image_path: str) -> dict[str, Any]:
    """Runs EasyOCR and RapidFuzz field extraction pipeline."""
    return {
        "mrp": {
            "raw_text": "MRP Rs 40.00 (incl. of all taxes)",
            "normalized_value": 40.0,
            "unit": "INR",
            "confidence": 0.96,
            "bounding_box": [120, 45, 150, 280],
        },
        "net_quantity": {
            "raw_text": "Net Weight: 75 g",
            "normalized_value": 75.0,
            "unit": "g",
            "confidence": 0.95,
            "bounding_box": [160, 45, 185, 210],
        },
    }


__all__ = [
    "calibrate_aruco",
    "calibrate_known_object",
    "detect_pdp_model",
    "opencv_fallback_detect_fn",
    "extract_fields",
    "run_ocr",
    "detect_pdp",
    "opencv_fallback_detect",
    "calibrate_scale",
    "run_ocr_and_extract",
]
