"""
Owner: SHUBH

EasyOCR Integration Service for SIH26034 Legal Metrology Compliance Checker.
Runs EasyOCR on preprocessed packaging label images, normalizes 4-corner polygon
coordinates into axis-aligned BoundingBox models, and extracts pixel height
for downstream font-height calibration.
"""

import logging
from typing import List, Dict, Optional
import numpy as np

from app.schemas.scan import BoundingBox
from app.services.vision.preprocessing import (
    resize_to_max_dimension,
    to_grayscale,
    apply_clahe,
)

logger = logging.getLogger(__name__)

_easyocr_reader = None  # Lazy-loaded singleton


def get_ocr_reader():
    """
    Returns a singleton EasyOCR Reader instance.
    Lazy-loads on first call to keep startup snappy.
    """
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        logger.info("Initializing EasyOCR reader (en, CPU mode)...")
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


def run_ocr(
    image: np.ndarray,
    use_clahe: bool = True,
    min_confidence: float = 0.2,
    max_dim: int = 1600,
) -> List[Dict]:
    """
    Executes text recognition on a packaging label image using EasyOCR.

    Pipeline:
      1. Validates image array.
      2. Scales to max_dim (aspect ratio preserved) to prevent CPU latency.
      3. Optionally applies CLAHE contrast equalization to enhance faint/glared ink.
         (Note: we feed CLAHE/gray, NOT hard binary, as deep-learning OCR requires stroke gradients).
      4. Converts EasyOCR 4-corner polygon bboxes to axis-aligned BoundingBox.
      5. Computes pixel height (y_max - y_min) needed by font calibration.

    Args:
        image: BGR or grayscale NumPy array.
        use_clahe: If True, applies CLAHE contrast enhancement before OCR.
        min_confidence: Threshold below which detections are ignored.
        max_dim: Maximum size on longest edge before OCR.

    Returns:
        List of dicts:
        [
            {
                "text": str,
                "confidence": float,
                "bbox": BoundingBox,
                "height_px": int,
                "polygon": List[List[int]],
            },
            ...
        ]
        Returns empty list on blank/unreadable input or internal error.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        logger.warning("run_ocr received an empty or invalid image array.")
        return []

    try:
        # Step 1: Cap resolution for predictable inference time
        processed = resize_to_max_dimension(image, max_dim=max_dim)

        # Step 2: Prepare image for OCR (CLAHE contrast-enhanced grayscale or color)
        if use_clahe:
            gray = to_grayscale(processed)
            ocr_input = apply_clahe(gray, clip_limit=2.0, tile_grid_size=(8, 8))
        else:
            ocr_input = processed

        # Step 3: Run EasyOCR
        reader = get_ocr_reader()
        raw_detections = reader.readtext(ocr_input)

        results: List[Dict] = []
        orig_h, orig_w = image.shape[:2]
        h, w = ocr_input.shape[:2]

        scale_x = orig_w / float(w)
        scale_y = orig_h / float(h)

        for bbox_coords, text, conf in raw_detections:
            confidence = float(conf)
            if confidence < min_confidence or not text.strip():
                continue

            # EasyOCR returns 4 corner points: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            x_coords = [int(p[0]) for p in bbox_coords]
            y_coords = [int(p[1]) for p in bbox_coords]

            x_min = max(0, min(orig_w - 1, int(min(x_coords) * scale_x)))
            y_min = max(0, min(orig_h - 1, int(min(y_coords) * scale_y)))
            x_max = max(x_min + 1, min(orig_w, int(max(x_coords) * scale_x)))
            y_max = max(y_min + 1, min(orig_h, int(max(y_coords) * scale_y)))

            height_px = max(1, y_max - y_min)
            scaled_poly = [[int(p[0] * scale_x), int(p[1] * scale_y)] for p in bbox_coords]

            results.append({
                "text": text.strip(),
                "confidence": round(confidence, 4),
                "bbox": BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max),
                "height_px": height_px,
                "polygon": scaled_poly,
            })

        # Step 4: For high-resolution photos (>2000px), run targeted patch OCR
        # Dot-matrix thermal inkjet stamps (MRP, MFG, EXP) lose dot continuity when downscaled by 70%+.
        # Localized patches at native/moderate resolution preserve individual dot matrix numerals.
        if max(orig_h, orig_w) > 2000:
            import cv2
            patch_boxes = []

            # A) Check if an ArUco marker is present; thermal stamps and declarations cluster nearby
            for dict_id in [cv2.aruco.DICT_4X4_50, cv2.aruco.DICT_5X5_50]:
                aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
                if hasattr(cv2.aruco, "ArucoDetector"):
                    det = cv2.aruco.ArucoDetector(aruco_dict)
                    marker_corners, marker_ids, _ = det.detectMarkers(ocr_input)
                else:
                    marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(ocr_input, aruco_dict)
                if marker_ids is not None and len(marker_corners) > 0:
                    c = marker_corners[0][0]
                    mx1 = int(min(c[:, 0]) * scale_x)
                    my1 = int(min(c[:, 1]) * scale_y)
                    mx2 = int(max(c[:, 0]) * scale_x)
                    my2 = int(max(c[:, 1]) * scale_y)
                    mw = mx2 - mx1
                    mh = my2 - my1
                    # 1. Thermal stamp region below marker (MRP, MFG, EXP)
                    patch_boxes.append((
                        max(0, mx1 - int(mw * 0.2)),
                        my2,
                        min(orig_w, mx2 + int(mw * 1.5)),
                        min(orig_h, my2 + int(mh * 1.6)),
                    ))
                    # 2. Manufacturer & declaration panel above/right of marker
                    patch_boxes.append((
                        mx2,
                        max(0, int(my1 - 2.5 * mh)),
                        min(orig_w, int(mx2 + 1.8 * mw)),
                        my1,
                    ))
                    break

            # B) Also check the lower central packaging band if no marker or as fallback
            if not patch_boxes:
                patch_boxes.append((
                    int(orig_w * 0.15),
                    int(orig_h * 0.55),
                    int(orig_w * 0.85),
                    int(orig_h * 0.95),
                ))

            for px1, py1, px2, py2 in patch_boxes:
                patch = image[py1:py2, px1:px2]
                if patch.size == 0 or patch.shape[0] < 50 or patch.shape[1] < 50:
                    continue

                for target_w in [500, 700]:
                    if patch.shape[1] < target_w * 0.4:
                        continue
                    actual_tw = min(target_w, patch.shape[1])
                    patch_scale = actual_tw / float(patch.shape[1])
                    scaled_patch = cv2.resize(patch, (actual_tw, int(patch.shape[0] * patch_scale)))
                    patch_gray = cv2.cvtColor(scaled_patch, cv2.COLOR_BGR2GRAY) if scaled_patch.ndim == 3 else scaled_patch

                    # Connect fragmented dot-matrix inkjet dots using a subtle 2x2 erosion
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                    eroded_patch = cv2.erode(patch_gray, kernel, iterations=1)

                    sc_px = patch.shape[1] / float(actual_tw)
                    sc_py = patch.shape[0] / float(scaled_patch.shape[0])

                    for p_gray in [patch_gray, eroded_patch]:
                        patch_dets = reader.readtext(p_gray)
                        for p_bbox, p_text, p_conf in patch_dets:
                            p_confidence = float(p_conf)
                            if p_confidence < 0.15 or not p_text.strip():
                                continue

                            bx_min = px1 + int(min(pt[0] for pt in p_bbox) * sc_px)
                            by_min = py1 + int(min(pt[1] for pt in p_bbox) * sc_py)
                            bx_max = px1 + int(max(pt[0] for pt in p_bbox) * sc_px)
                            by_max = py1 + int(max(pt[1] for pt in p_bbox) * sc_py)

                            results.append({
                                "text": p_text.strip(),
                                "confidence": round(p_confidence, 4),
                                "bbox": BoundingBox(x_min=bx_min, y_min=by_min, x_max=bx_max, y_max=by_max),
                                "height_px": max(1, by_max - by_min),
                                "polygon": [[px1 + int(pt[0] * sc_px), py1 + int(pt[1] * sc_py)] for pt in p_bbox],
                            })

        return results

    except Exception as exc:
        # Non-negotiable project rule: Never crash pipeline with an unhandled exception.
        # Degrade gracefully so caller can route to REVIEW_REQUIRED.
        logger.error(f"Unexpected failure during EasyOCR execution: {exc}", exc_info=True)
        return []
