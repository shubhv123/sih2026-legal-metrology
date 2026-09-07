"""
Tests for Dual Calibration and Statutory Rule 7 Font Height Evaluation.
Owner: SHUBH
"""

import numpy as np
import cv2
import pytest

from app.schemas.scan import (
    CalibrationMethod,
    ExtractedField,
    BoundingBox,
    FieldStatus,
)
from app.services.vision.calibration import (
    calibrate_aruco,
    calibrate_known_object,
    get_calibration,
    get_mm_per_pixel,
    get_required_font_height,
    evaluate_font_heights,
    CONFIDENCE_REVIEW_THRESHOLD,
)


def _generate_synthetic_aruco_image(
    dict_id=cv2.aruco.DICT_4X4_50,
    marker_id=1,
    marker_size_px=200,
    canvas_size=400,
) -> np.ndarray:
    """Helper to generate a clean synthetic image containing an ArUco marker."""
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)

    canvas = np.ones((canvas_size, canvas_size), dtype=np.uint8) * 255
    offset = (canvas_size - marker_size_px) // 2
    canvas[offset : offset + marker_size_px, offset : offset + marker_size_px] = marker_img
    return cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)


def test_calibrate_aruco_success():
    """Verify ArUco marker detection computes mm_per_pixel accurately."""
    # 200px marker on 400x400 canvas, real-world size 30mm -> ~0.15 mm/px
    img = _generate_synthetic_aruco_image(marker_size_px=200)
    result = calibrate_aruco(img, known_marker_size_mm=30.0)

    assert result is not None
    mm_per_px, confidence = result
    assert pytest.approx(mm_per_px, abs=0.01) == 0.15
    assert confidence >= CONFIDENCE_REVIEW_THRESHOLD
    assert confidence == 0.95


def test_calibrate_aruco_multi_dictionary():
    """Verify detection succeeds across different supported dictionaries (4x4, 5x5, 6x6)."""
    for dict_id in [cv2.aruco.DICT_4X4_50, cv2.aruco.DICT_5X5_50, cv2.aruco.DICT_6X6_50]:
        img = _generate_synthetic_aruco_image(dict_id=dict_id, marker_size_px=150)
        res = calibrate_aruco(img, known_marker_size_mm=30.0)
        assert res is not None
        mm_px, conf = res
        assert pytest.approx(mm_px, abs=0.01) == 0.20
        assert conf >= 0.85


def test_calibrate_aruco_missing_marker():
    """Verify None is returned when no ArUco marker is in the image."""
    blank_img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    res = calibrate_aruco(blank_img)
    assert res is None

    empty_img = np.array([], dtype=np.uint8)
    assert calibrate_aruco(empty_img) is None


def test_calibrate_known_object():
    """Verify user-selected known object fallback calculates scale."""
    # 25mm diameter reference (e.g. coin), bounding box height 100px -> 0.25 mm/px
    mm_px, conf = calibrate_known_object(object_bbox_px_height=100.0, known_size_mm=25.0)
    assert pytest.approx(mm_px, abs=0.001) == 0.25
    assert conf == 0.85

    # Degenerate input
    mm_px_zero, conf_zero = calibrate_known_object(object_bbox_px_height=0.0, known_size_mm=25.0)
    assert mm_px_zero == 0.0
    assert conf_zero == 0.0


def test_get_calibration_dual_path_routing():
    """Verify get_calibration routes correctly between ArUco and known-object fallback."""
    marker_img = _generate_synthetic_aruco_image(marker_size_px=200)
    blank_img = np.ones((300, 300, 3), dtype=np.uint8) * 255

    # 1. Primary: ArUco found
    mm_px, conf, method = get_calibration(marker_img, method=CalibrationMethod.ARUCO)
    assert method == CalibrationMethod.ARUCO
    assert mm_px is not None
    assert conf >= CONFIDENCE_REVIEW_THRESHOLD

    # 2. ArUco requested, but not found -> auto fallback to known_object if params provided
    mm_px, conf, method = get_calibration(
        blank_img,
        method=CalibrationMethod.ARUCO,
        known_object_size_mm=25.0,
        known_object_bbox_px_height=100.0,
    )
    assert method == CalibrationMethod.KNOWN_OBJECT
    assert pytest.approx(mm_px, abs=0.001) == 0.25
    assert conf == 0.85

    # 3. ArUco requested, not found, no fallback params -> NONE
    mm_px, conf, method = get_calibration(blank_img, method=CalibrationMethod.ARUCO)
    assert method == CalibrationMethod.NONE
    assert mm_px is None
    assert conf == 0.0

    # 4. Explicit KNOWN_OBJECT method
    mm_px, conf, method = get_calibration(
        None,
        method=CalibrationMethod.KNOWN_OBJECT,
        known_object_size_mm=30.0,
        known_object_bbox_px_height=150.0,
    )
    assert method == CalibrationMethod.KNOWN_OBJECT
    assert pytest.approx(mm_px, abs=0.001) == 0.20
    assert conf == 0.85

    # 5. Explicit NONE method
    mm_px, conf, method = get_calibration(None, method=CalibrationMethod.NONE)
    assert method == CalibrationMethod.NONE
    assert mm_px is None


def test_get_mm_per_pixel_backward_compatibility():
    """Verify legacy get_mm_per_pixel entrypoint functions."""
    marker_img = _generate_synthetic_aruco_image(marker_size_px=200)
    mm_px = get_mm_per_pixel(marker_img, method=CalibrationMethod.ARUCO)
    assert mm_px is not None
    assert pytest.approx(mm_px, abs=0.01) == 0.15


def test_table_1_net_quantity_by_weight_volume():
    """
    Statutory verification: Net quantity declared by weight/volume
    must be bracketed by quantity value per Rule 7(2)(i) Table-I.
    """
    # Bracket 1: <= 200g / ml -> 1.0mm normal, 2.0mm blown/molded
    assert get_required_font_height("net_quantity", "50 g") == 1.0
    assert get_required_font_height("net_quantity", "50 g", is_blown_or_molded=True) == 2.0
    assert get_required_font_height("net_quantity", "200 g") == 1.0
    assert get_required_font_height("net_quantity", "200 ml") == 1.0

    # Bracket 2: 200g - 500g / ml -> 2.0mm normal, 4.0mm blown/molded
    assert get_required_font_height("net_quantity", "250 g") == 2.0
    assert get_required_font_height("net_quantity", "250 g", is_blown_or_molded=True) == 4.0
    assert get_required_font_height("net_quantity", "500 ml") == 2.0
    assert get_required_font_height("net_quantity", "500 ml", is_blown_or_molded=True) == 4.0

    # Bracket 3: > 500g / ml -> 4.0mm normal, 6.0mm blown/molded
    assert get_required_font_height("net_quantity", "750 g") == 4.0
    assert get_required_font_height("net_quantity", "750 g", is_blown_or_molded=True) == 6.0
    assert get_required_font_height("net_quantity", "1 kg") == 4.0
    assert get_required_font_height("net_quantity", "1 L") == 4.0
    assert get_required_font_height("net_quantity", "5 kg", is_blown_or_molded=True) == 6.0


def test_table_2_net_quantity_by_pdp_area():
    """
    Statutory verification: Net quantity declared by count/length/area
    must be bracketed by PRINCIPAL DISPLAY PANEL AREA per Rule 7(2)(ii) Table-II.
    """
    # Bracket 1: PDP area <= 100 cm2 -> 1.0mm normal, 2.0mm blown
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=50) == 1.0
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=50, is_blown_or_molded=True) == 2.0

    # Bracket 2: PDP area 100 - 500 cm2 -> 2.0mm normal, 4.0mm blown
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=250) == 2.0
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=250, is_blown_or_molded=True) == 4.0

    # Bracket 3: PDP area 500 - 2500 cm2 -> 4.0mm normal, 6.0mm blown
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=1200) == 4.0
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=1200, is_blown_or_molded=True) == 6.0

    # Bracket 4: PDP area > 2500 cm2 -> 6.0mm normal, 6.0mm blown
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=3000) == 6.0
    assert get_required_font_height("net_quantity", "10 N", pdp_area_cm2=3000, is_blown_or_molded=True) == 6.0


def test_rule_7_3_flat_letter_specifications():
    """
    Statutory verification: MRP, manufacturing date, unit sale price,
    and consumer care are letters/numerals evaluated under Rule 7(3) (flat 1.0mm / 2.0mm).
    """
    for field_name in ["mrp", "mfg_date", "unit_sale_price", "consumer_care", "manufacturer_name", "generic_name"]:
        # Normal packaging -> 1.0mm
        assert get_required_font_height(field_name, "test_val") == 1.0
        # Blown or molded packaging -> 2.0mm
        assert get_required_font_height(field_name, "test_val", is_blown_or_molded=True) == 2.0


def test_evaluate_font_heights_pass_fail_review():
    """End-to-end test of evaluate_font_heights honoring PASS, FAIL, and REVIEW_REQUIRED."""
    fields = [
        ExtractedField(
            field_name="net_quantity",
            raw_ocr_text="Net Wt 250g",
            normalized_value="250 g",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=10, x_max=100, y_max=35),  # height = 25px
        ),
        ExtractedField(
            field_name="mrp",
            raw_ocr_text="MRP Rs. 199",
            normalized_value="199.00",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=50, x_max=100, y_max=58),  # height = 8px
        ),
    ]

    # Case 1: High confidence calibration (0.1 mm/px, confidence 0.95)
    # - net_quantity: 25px * 0.1 = 2.5mm >= 2.0mm -> PASS
    # - mrp: 8px * 0.1 = 0.8mm < 1.0mm -> FAIL
    analysis = evaluate_font_heights(
        fields,
        mm_per_pixel=0.1,
        calibration_method=CalibrationMethod.ARUCO,
        calibration_confidence=0.95,
    )
    assert analysis.calibration_method == CalibrationMethod.ARUCO
    assert analysis.mm_per_pixel == 0.1
    assert len(analysis.fields) == 2

    nq_field = next(f for f in analysis.fields if f.field_name == "net_quantity")
    assert nq_field.measured_height_mm == 2.5
    assert nq_field.required_height_mm == 2.0
    assert nq_field.status == FieldStatus.PASS

    mrp_field = next(f for f in analysis.fields if f.field_name == "mrp")
    assert mrp_field.measured_height_mm == 0.8
    assert mrp_field.required_height_mm == 1.0
    assert mrp_field.status == FieldStatus.FAIL

    # Case 2: Calibration confidence below 0.75 -> must route to REVIEW_REQUIRED
    low_conf_analysis = evaluate_font_heights(
        fields,
        mm_per_pixel=0.1,
        calibration_method=CalibrationMethod.ARUCO,
        calibration_confidence=0.65,
    )
    assert all(f.status == FieldStatus.REVIEW_REQUIRED for f in low_conf_analysis.fields)

    # Case 3: No calibration (mm_per_pixel is None) -> must route to REVIEW_REQUIRED
    none_analysis = evaluate_font_heights(
        fields,
        mm_per_pixel=None,
        calibration_method=CalibrationMethod.NONE,
        calibration_confidence=0.0,
    )
    assert all(f.status == FieldStatus.REVIEW_REQUIRED for f in none_analysis.fields)
