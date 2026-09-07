"""
Owner: SHUBH

Detection: try YOLOv8n first; if confidence is below threshold OR the
model isn't ready yet, fall back to OpenCV contour detection. This
function should ALWAYS return a result - never raise on a bad image,
return low confidence instead and let the caller/rule engine route it
to REVIEW_REQUIRED.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np
import cv2

from app.schemas.scan import Detection, DetectionMethod, BoundingBox

# Primary model path in backend/app/data/models/, secondary in ml/weights/
YOLO_MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "yolov8n_pdp.pt"
ML_WEIGHTS_PATH = Path(__file__).parent.parent.parent.parent.parent / "ml" / "weights" / "best.pt"

YOLO_CONFIDENCE_THRESHOLD = 0.5

_yolo_model = None  # lazy-loaded singleton


def _load_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        target_path = None
        if YOLO_MODEL_PATH.exists():
            target_path = YOLO_MODEL_PATH
        elif ML_WEIGHTS_PATH.exists():
            target_path = ML_WEIGHTS_PATH

        if target_path is not None:
            try:
                from ultralytics import YOLO
                _yolo_model = YOLO(str(target_path))
            except Exception:
                _yolo_model = None
    return _yolo_model


def detect_pdp(image: np.ndarray) -> Detection:
    """
    Detects Principal Display Panel (PDP) bounding box:
    1. Try YOLO if trained weights exist and top box confidence >= YOLO_CONFIDENCE_THRESHOLD (0.6).
    2. Otherwise (low confidence, model missing, or unexpected exception),
       seamlessly fall back to opencv_fallback_detect().
    Never raises an exception on bad/unusual input.
    """
    if image is None or image.size == 0:
        return opencv_fallback_detect(image)

    try:
        model = _load_yolo_model()
        if model is not None:
            results = model.predict(image, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)
            if results and len(results) > 0 and len(results[0].boxes) > 0:
                top_box = results[0].boxes[0]
                conf = float(top_box.conf[0])
                if conf >= YOLO_CONFIDENCE_THRESHOLD:
                    box = top_box.xyxy[0].tolist()
                    h, w = image.shape[:2]
                    x_min = max(0, min(w - 1, int(box[0])))
                    y_min = max(0, min(h - 1, int(box[1])))
                    x_max = max(x_min + 1, min(w, int(box[2])))
                    y_max = max(y_min + 1, min(h, int(box[3])))
                    return Detection(
                        method=DetectionMethod.YOLO,
                        confidence=round(conf, 3),
                        pdp_bbox=BoundingBox(
                            x_min=x_min,
                            y_min=y_min,
                            x_max=x_max,
                            y_max=y_max,
                        ),
                    )
    except Exception:
        # Fall through to OpenCV fallback on any model error
        pass

    return opencv_fallback_detect(image)


def opencv_fallback_detect(image: np.ndarray) -> Detection:
    """
    Contour-based fallback — no trained model required.
    Finds the statutory declaration panel or label by scoring candidate contours
    on edge/text density + rectangularity rather than pure area.
    This prevents grabbing the entire photo or background countertop.
    """
    if image is None or image.size == 0:
        return Detection(
            method=DetectionMethod.OPENCV_FALLBACK,
            confidence=0.5,
            pdp_bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
        )

    h, w = image.shape[:2]
    total_area = h * w

    try:
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 1. Otsu thresholding cleanly segments high-contrast packaging from surfaces
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 2. Text stroke gradient in X direction (horizontal character transitions)
        sobel_x = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
        _, text_mask = cv2.threshold(sobel_x, 40, 255, cv2.THRESH_BINARY)

        # 3. Find contours
        contours, _ = cv2.findContours(otsu, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            # Must be at least 5% of the frame to be a meaningful panel
            if area < total_area * 0.05:
                continue

            x, y, cw, ch = cv2.boundingRect(c)
            bbox_area = cw * ch
            area_ratio = bbox_area / total_area

            # Avoid full-frame captures (> 85% area)
            if area_ratio > 0.85:
                continue

            aspect = max(cw, ch) / max(min(cw, ch), 1)
            if aspect > 4.5:
                continue

            # Extent / rectangularity: how much contour fills its bounding box
            extent = area / max(bbox_area, 1.0)

            # Text edge density inside this candidate bounding box
            crop_text = text_mask[y : y + ch, x : x + cw]
            text_density = np.count_nonzero(crop_text) / float(bbox_area)

            # Combined score: prioritize high text density and good rectangular extent
            score = (text_density * 4.0) + (extent * 1.5)
            candidates.append((score, text_density, extent, area_ratio, (x, y, x + cw, y + ch)))

        if candidates:
            # Sort by text-density + rectangularity score (highest first)
            candidates.sort(key=lambda item: item[0], reverse=True)
            best_score, best_td, best_ext, best_ar, (bx1, by1, bx2, by2) = candidates[0]

            # Dynamic confidence based on text density and rectangular fit
            confidence = min(0.72, max(0.50, 0.40 + (best_td * 1.2) + (best_ext * 0.20)))

            return Detection(
                method=DetectionMethod.OPENCV_FALLBACK,
                confidence=round(confidence, 3),
                pdp_bbox=BoundingBox(x_min=bx1, y_min=by1, x_max=bx2, y_max=by2),
            )
    except Exception:
        pass

    # Safe default: central 80% with low confidence (0.50 -> routes to REVIEW_REQUIRED)
    margin_x, margin_y = int(w * 0.1), int(h * 0.1)
    return Detection(
        method=DetectionMethod.OPENCV_FALLBACK,
        confidence=0.50,
        pdp_bbox=BoundingBox(
            x_min=margin_x,
            y_min=margin_y,
            x_max=max(margin_x + 1, w - margin_x),
            y_max=max(margin_y + 1, h - margin_y),
        ),
    )


