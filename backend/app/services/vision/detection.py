"""
Owner: SHUBH

Detection: try YOLOv8n first; if confidence is below threshold OR the
model isn't ready yet, fall back to OpenCV contour detection. This
function should ALWAYS return a result - never raise on a bad image,
return low confidence instead and let the caller/rule engine route it
to REVIEW_REQUIRED.
"""

from pathlib import Path
from typing import Tuple
import numpy as np

from app.schemas.scan import Detection, DetectionMethod, BoundingBox

YOLO_MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "yolov8n_pdp.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.6

_yolo_model = None  # lazy-loaded singleton


def _load_yolo_model():
    global _yolo_model
    if _yolo_model is None and YOLO_MODEL_PATH.exists():
        from ultralytics import YOLO
        _yolo_model = YOLO(str(YOLO_MODEL_PATH))
    return _yolo_model


def detect_pdp(image: np.ndarray) -> Detection:
    """
    TODO(shubh):
    1. Try YOLO if the trained weight file exists and confidence is high
       enough.
    2. Otherwise (or if YOLO isn't trained yet / underperforms per the
       day-5 decision gate) fall back to opencv_fallback_detect() below.
    """
    model = _load_yolo_model()

    if model is not None:
        # results = model(image)
        # if results and results[0].boxes and results[0].boxes.conf[0] > YOLO_CONFIDENCE_THRESHOLD:
        #     box = results[0].boxes.xyxy[0].tolist()
        #     return Detection(
        #         method=DetectionMethod.YOLO,
        #         confidence=float(results[0].boxes.conf[0]),
        #         pdp_bbox=BoundingBox(x_min=int(box[0]), y_min=int(box[1]),
        #                               x_max=int(box[2]), y_max=int(box[3])),
        #     )
        pass  # placeholder until model is trained - uncomment above

    return opencv_fallback_detect(image)


def opencv_fallback_detect(image: np.ndarray) -> Detection:
    """
    Contour-based fallback - no trained model required. Finds the
    largest roughly-rectangular contour in the image as the PDP guess.
    TODO(shubh): implement with cv2.findContours + cv2.boundingRect
    on the largest contour after edge detection.
    """
    h, w = image.shape[:2]
    # Placeholder: assume PDP is the central 80% of the image
    margin_x, margin_y = int(w * 0.1), int(h * 0.1)
    return Detection(
        method=DetectionMethod.OPENCV_FALLBACK,
        confidence=0.5,  # low-ish on purpose - this is a naive placeholder
        pdp_bbox=BoundingBox(
            x_min=margin_x, y_min=margin_y,
            x_max=w - margin_x, y_max=h - margin_y,
        ),
    )
