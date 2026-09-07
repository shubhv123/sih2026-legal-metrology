"""
Owner: SHUBH

Dual calibration per the plan:
 - PRIMARY: ArUco marker (known physical dimensions, robust to perspective)
 - FALLBACK: user-selected known-size object (e.g. a coin) with its
   real-world size passed in via the API (known_object_size_mm)

Either path produces mm_per_pixel, which is then used to convert
every extracted field's bbox height into a real-world mm measurement.

Also evaluates font height compliance according to Legal Metrology
(Packaged Commodities) Rules, 2011, Rule 7 specifications:
 - Rule 7(2)(i) Table-I: Net quantity numeral by weight or volume
 - Rule 7(2)(ii) Table-II: Net quantity numeral by PDP area (for count/length/area)
 - Rule 7(3): All other mandatory letters/numerals (flat 1.0mm normal / 2.0mm blown/molded)
"""

import json
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import cv2

from app.schemas.scan import (
    CalibrationMethod,
    ExtractedField,
    FontAnalysis,
    FontAnalysisField,
    FieldStatus,
)
from app.services.vision.extraction import parse_net_quantity

CONFIDENCE_REVIEW_THRESHOLD = 0.75
DEFAULT_ARUCO_SIZE_MM = 30.0
RULES_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "lmpc_rules_v1.json"

_cached_rules: Optional[dict] = None

ARUCO_DICTIONARIES = [
    cv2.aruco.DICT_4X4_50,
    cv2.aruco.DICT_4X4_100,
    cv2.aruco.DICT_5X5_50,
    cv2.aruco.DICT_5X5_100,
    cv2.aruco.DICT_6X6_50,
    cv2.aruco.DICT_6X6_100,
]


def load_rules() -> dict:
    """Loads and caches lmpc_rules_v1.json."""
    global _cached_rules
    if _cached_rules is None:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            _cached_rules = json.load(f)
    return _cached_rules


def calibrate_aruco(
    image: np.ndarray,
    known_marker_size_mm: float = DEFAULT_ARUCO_SIZE_MM,
) -> Optional[Tuple[float, float]]:
    """
    Detects ArUco marker in image and calculates mm_per_pixel and confidence.

    Iterates through common ArUco dictionaries using OpenCV 4.7+ ArucoDetector
    (with fallback to cv2.aruco.detectMarkers for legacy OpenCV).

    Returns:
        (mm_per_pixel, calibration_confidence) or None if no marker detected.
    """
    if image is None or image.size == 0:
        return None

    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Determine scales to test: always test native, and if large (>1600px), also test scaled
    h, w = gray.shape[:2]
    scales = [1.0]
    if max(h, w) > 1600:
        scales.insert(0, 1600.0 / max(h, w))

    detector_params = cv2.aruco.DetectorParameters()

    for scale in scales:
        if scale != 1.0:
            detect_gray = cv2.resize(gray, (int(w * scale), int(h * scale)))
        else:
            detect_gray = gray

        for dict_id in ARUCO_DICTIONARIES:
            aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
            
            # OpenCV 4.7+ ArucoDetector support with fallback
            if hasattr(cv2.aruco, "ArucoDetector"):
                detector = cv2.aruco.ArucoDetector(aruco_dict, detector_params)
                corners, ids, _ = detector.detectMarkers(detect_gray)
            else:
                corners, ids, _ = cv2.aruco.detectMarkers(detect_gray, aruco_dict, parameters=detector_params)

            if ids is not None and len(corners) > 0:
                # Use the first detected marker and scale coordinates back to original image space
                c = corners[0][0] / scale  # shape (4, 2)
                sides = [
                    np.linalg.norm(c[0] - c[1]),
                    np.linalg.norm(c[1] - c[2]),
                    np.linalg.norm(c[2] - c[3]),
                    np.linalg.norm(c[3] - c[0]),
                ]
                mean_side_px = float(np.mean(sides))
                min_side = float(min(sides))
                max_side = float(max(sides))

                if mean_side_px < 5.0 or min_side <= 0:
                    continue  # Marker too small or degenerate

                # Perspective distortion estimate: square marker should have equal sides
                aspect_ratio = max_side / min_side

                if aspect_ratio <= 1.25:
                    confidence = 0.95
                elif aspect_ratio <= 1.50:
                    confidence = 0.85
                else:
                    # Heavy perspective tilt / distortion
                    confidence = 0.70

                mm_per_pixel = known_marker_size_mm / mean_side_px
                return round(float(mm_per_pixel), 5), float(confidence)

    return None


def calibrate_known_object(
    object_bbox_px_height: float,
    known_size_mm: float,
) -> Tuple[float, float]:
    """
    Fallback calibration: user selects/crops a reference object of known size
    (e.g. a coin with known diameter in mm).

    Returns:
        (mm_per_pixel, calibration_confidence)
    """
    if object_bbox_px_height <= 0:
        return 0.0, 0.0

    mm_per_pixel = known_size_mm / object_bbox_px_height
    # Known object fallback has manual boundary/perspective variance -> confidence 0.85
    confidence = 0.85
    return round(float(mm_per_pixel), 5), confidence


def get_calibration(
    image: Optional[np.ndarray],
    method: CalibrationMethod = CalibrationMethod.ARUCO,
    known_object_size_mm: Optional[float] = None,
    known_object_bbox_px_height: Optional[float] = None,
    aruco_marker_size_mm: float = DEFAULT_ARUCO_SIZE_MM,
) -> Tuple[Optional[float], float, CalibrationMethod]:
    """
    Unified dual-path calibration entrypoint.

    Returns:
        (mm_per_pixel, calibration_confidence, effective_method)
    """
    if method == CalibrationMethod.ARUCO:
        if image is not None:
            aruco_res = calibrate_aruco(image, known_marker_size_mm=aruco_marker_size_mm)
            if aruco_res is not None:
                return aruco_res[0], aruco_res[1], CalibrationMethod.ARUCO

        # Automatic fallback to known object if parameters were provided
        if known_object_size_mm is not None and known_object_bbox_px_height is not None:
            mm_px, conf = calibrate_known_object(known_object_bbox_px_height, known_object_size_mm)
            return mm_px, conf, CalibrationMethod.KNOWN_OBJECT

        return None, 0.0, CalibrationMethod.NONE

    if method == CalibrationMethod.KNOWN_OBJECT:
        if known_object_size_mm is not None and known_object_bbox_px_height is not None:
            mm_px, conf = calibrate_known_object(known_object_bbox_px_height, known_object_size_mm)
            return mm_px, conf, CalibrationMethod.KNOWN_OBJECT
        return None, 0.0, CalibrationMethod.NONE

    return None, 0.0, CalibrationMethod.NONE


def get_mm_per_pixel(
    image: np.ndarray,
    method: CalibrationMethod,
    known_object_size_mm: Optional[float] = None,
    known_object_bbox_px_height: Optional[float] = None,
) -> Optional[float]:
    """Legacy entrypoint preserved for simple call sites - returns mm_per_pixel or None."""
    mm_px, _, _ = get_calibration(
        image=image,
        method=method,
        known_object_size_mm=known_object_size_mm,
        known_object_bbox_px_height=known_object_bbox_px_height,
    )
    return mm_px


def get_required_font_height(
    field_name: str,
    normalized_value: Optional[str] = None,
    pdp_area_cm2: Optional[float] = None,
    is_blown_or_molded: bool = False,
    rules_data: Optional[dict] = None,
) -> float:
    """
    Determines statutory minimum font height in mm for a given field per Rule 7:
      - 'net_quantity' with weight/vol (g, kg, ml, l) -> Table-I (bracketed by qty)
      - 'net_quantity' with count/length/area (u, m, etc.) -> Table-II (bracketed by PDP area)
      - All other fields ('mrp', 'mfg_date', 'unit_sale_price', etc.) -> Rule 7(3) flat letters specification
    """
    rules = rules_data or load_rules()
    r7_spec = rules.get("rule_7_font_height_specifications", {})
    mapping = r7_spec.get("font_height_rule_mapping", {}).get(field_name, "letters_height_specification")

    if mapping == "table_1_or_2_by_declaration_type":
        norm_str = normalized_value or ""
        parsed = parse_net_quantity(norm_str)
        if parsed and len(parsed) >= 2:
            norm_str = parsed[1]

        num_matches = re.findall(r"([0-9]+(?:\.[0-9]+)?)", norm_str)
        unit_match = re.search(r"(kg|g|mg|l|ml|m|cm|mm|u|n|unit|units|piece|pieces|pcs)\b", norm_str, re.IGNORECASE)
        unit = unit_match.group(1).lower() if unit_match else ""
        raw_val = float(num_matches[-1]) if num_matches else None

        # Check if weight or volume -> Table-I
        if unit in ["g", "kg", "mg", "ml", "l"]:
            # Normalize to grams or milliliters
            if raw_val is not None:
                val = float(raw_val)
                if unit in ["kg", "l"]:
                    val *= 1000.0
                elif unit == "mg":
                    val /= 1000.0
            else:
                val = 100.0  # Safe default if value unparsed

            table_1 = r7_spec.get("table_1_numerals_by_weight_or_volume", {}).get("brackets", [])
            for bracket in table_1:
                max_val = bracket.get("net_qty_max_g_ml")
                min_val = bracket.get("net_qty_min_g_ml")

                if min_val is None and max_val is not None:
                    if val <= max_val:
                        return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]
                elif min_val is not None and max_val is not None:
                    if min_val < val <= max_val:
                        return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]
                elif min_val is not None and max_val is None:
                    if val > min_val:
                        return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]

            # Fallback for Table-I (above 500g/ml)
            return 6.0 if is_blown_or_molded else 4.0

        # Declaration by length, area or number (units, pieces, metres, etc.) -> Table-II
        table_2 = r7_spec.get("table_2_numerals_by_pdp_area", {}).get("brackets", [])
        area = pdp_area_cm2 if pdp_area_cm2 is not None else 250.0  # Default to standard packaging bracket (100 to 500 cm2)

        for bracket in table_2:
            max_area = bracket.get("pdp_area_max_cm2")
            min_area = bracket.get("pdp_area_min_cm2")

            if min_area is None and max_area is not None:
                if area <= max_area:
                    return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]
            elif min_area is not None and max_area is not None:
                if min_area < area <= max_area:
                    return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]
            elif min_area is not None and max_area is None:
                if area > min_area:
                    return bracket["min_height_mm_blown_or_molded"] if is_blown_or_molded else bracket["min_height_mm_normal"]

        return 6.0 if is_blown_or_molded else 4.0

    # Rule 7(3) Letters / flat specification
    letters_spec = r7_spec.get("letters_height_specification", {})
    return (
        letters_spec.get("min_height_mm_blown_or_molded", 2.0)
        if is_blown_or_molded
        else letters_spec.get("min_height_mm_normal", 1.0)
    )


def evaluate_font_heights(
    extracted_fields: List[ExtractedField],
    mm_per_pixel: Optional[float],
    calibration_method: CalibrationMethod = CalibrationMethod.ARUCO,
    calibration_confidence: float = 0.0,
    pdp_area_cm2: Optional[float] = None,
    is_blown_or_molded: bool = False,
    rules_data: Optional[dict] = None,
) -> FontAnalysis:
    """
    Evaluates font height compliance for all extracted mandatory declarations.

    Three-state confidence-aware determination:
      - If calibration failed or confidence < 0.75: status = REVIEW_REQUIRED
      - If measured_height >= required_height: status = PASS
      - Else: status = FAIL
    """
    rules = rules_data or load_rules()
    mapping = rules.get("rule_7_font_height_specifications", {}).get("font_height_rule_mapping", {})

    fields: List[FontAnalysisField] = []

    for field in extracted_fields:
        # Only evaluate fields that have a defined font specification
        if field.field_name not in mapping:
            continue

        req_height = get_required_font_height(
            field_name=field.field_name,
            normalized_value=field.normalized_value,
            pdp_area_cm2=pdp_area_cm2,
            is_blown_or_molded=is_blown_or_molded,
            rules_data=rules,
        )

        bbox_h_px = max(0.0, float(field.bbox.y_max - field.bbox.y_min))

        if mm_per_pixel is not None and mm_per_pixel > 0:
            measured_height = round(bbox_h_px * mm_per_pixel, 2)
        else:
            measured_height = 0.0

        # Confidence gate: if calibration confidence < 0.75, route to REVIEW_REQUIRED
        if mm_per_pixel is None or calibration_confidence < CONFIDENCE_REVIEW_THRESHOLD:
            status = FieldStatus.REVIEW_REQUIRED
        elif measured_height >= req_height:
            status = FieldStatus.PASS
        else:
            status = FieldStatus.FAIL

        fields.append(
            FontAnalysisField(
                field_name=field.field_name,
                measured_height_mm=measured_height,
                required_height_mm=req_height,
                status=status,
                calibration_confidence=calibration_confidence,
            )
        )

    return FontAnalysis(
        calibration_method=calibration_method,
        mm_per_pixel=mm_per_pixel,
        fields=fields,
    )

