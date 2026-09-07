"""
Unit tests for EasyOCR integration service (backend/app/services/vision/ocr.py).

NOTE ON SYNTHETIC TEST IMAGES:
These tests confirm pipeline plumbing, coordinate normalization, and data-flow
conformance to the project schemas. They DO NOT validate real-world label accuracy.
Real-world performance (handling glare, curved packaging, multilingual labels, and
embossed text) will be evaluated on Gauri's collected dataset on Day 2-3.
"""

from pathlib import Path
import pytest
import numpy as np
import cv2

from app.services.vision.ocr import run_ocr
from app.schemas.scan import BoundingBox

SAMPLE_IMAGES_DIR = Path(__file__).parent / "sample_images"


@pytest.fixture(scope="module")
def compliant_label():
    img_path = SAMPLE_IMAGES_DIR / "compliant_label.jpg"
    img = cv2.imread(str(img_path))
    assert img is not None, f"Sample image not found at {img_path}"
    return img


@pytest.fixture(scope="module")
def faded_label():
    img_path = SAMPLE_IMAGES_DIR / "faded_label.jpg"
    img = cv2.imread(str(img_path))
    assert img is not None, f"Sample image not found at {img_path}"
    return img


def test_ocr_text_detection_and_clahe_path(compliant_label, faded_label):
    """
    Test 1: Verify text is detected with confidence scores on sample labels,
    and confirm that the CLAHE-enhanced code path runs cleanly without crashing.
    """
    # 1. Run on compliant label
    results = run_ocr(compliant_label, use_clahe=False, min_confidence=0.2)
    assert len(results) > 0, "Expected OCR to detect text lines on compliant label"

    detected_text = " ".join([item["text"].lower() for item in results])
    # Check that core declarations are detected
    assert "mrp" in detected_text or "149" in detected_text or "rs" in detected_text
    assert "weight" in detected_text or "500" in detected_text or "net" in detected_text

    # Verify result structure conforms to expected contract
    first = results[0]
    assert isinstance(first["text"], str)
    assert isinstance(first["confidence"], float)
    assert 0.0 <= first["confidence"] <= 1.0
    assert isinstance(first["bbox"], BoundingBox)
    assert isinstance(first["height_px"], int)
    assert first["height_px"] > 0

    # 2. Run with use_clahe=True on faded label to confirm CLAHE path executes cleanly
    faded_results = run_ocr(faded_label, use_clahe=True, min_confidence=0.2)
    assert isinstance(faded_results, list)
    assert len(faded_results) > 0, "Expected OCR to return detections from faded label with CLAHE enabled"


def test_ocr_bounding_box_within_bounds(compliant_label):
    """
    Test 2: Verify all normalized BoundingBox coordinates are strictly within
    image spatial bounds, with valid positive pixel heights.
    """
    results = run_ocr(compliant_label, use_clahe=True)
    h, w = compliant_label.shape[:2]

    for item in results:
        bbox = item["bbox"]
        assert 0 <= bbox.x_min < bbox.x_max <= w, f"x bounds invalid: {bbox} for width {w}"
        assert 0 <= bbox.y_min < bbox.y_max <= h, f"y bounds invalid: {bbox} for height {h}"
        assert item["height_px"] == (bbox.y_max - bbox.y_min)
        assert item["height_px"] >= 1


def test_ocr_unusual_input_fault_tolerance():
    """
    Test 3: Verify the pipeline never raises an unhandled exception on unusual,
    blank, corrupted, or edge-case inputs (adhering to project error-handling rule).
    """
    # Sub-case A: Completely white canvas (no text)
    blank_white = np.full((300, 300, 3), 255, dtype=np.uint8)
    assert run_ocr(blank_white) == []

    # Sub-case B: Completely black canvas
    blank_black = np.zeros((300, 300, 3), dtype=np.uint8)
    assert run_ocr(blank_black) == []

    # Sub-case C: None input
    assert run_ocr(None) == []

    # Sub-case D: 0-size empty array
    empty_arr = np.array([], dtype=np.uint8)
    assert run_ocr(empty_arr) == []

    # Sub-case E: Extremely small 1x1 image
    tiny = np.zeros((1, 1, 3), dtype=np.uint8)
    assert run_ocr(tiny) == []
