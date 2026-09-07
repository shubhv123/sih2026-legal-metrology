"""
Tests for PDP Detection (YOLOv8n + OpenCV Contour Fallback).
Owner: SHUBH
"""

import numpy as np
import pytest

from app.schemas.scan import DetectionMethod
from app.services.vision.detection import (
    detect_pdp,
    opencv_fallback_detect,
    YOLO_CONFIDENCE_THRESHOLD,
)


def test_yolo_confidence_threshold_is_point_five():
    """Verify threshold is set to 0.5 for YOLO model detection."""
    assert YOLO_CONFIDENCE_THRESHOLD == 0.5


def test_opencv_fallback_detect_solid_rectangle():
    """Verify real contour detection finds a high-contrast rectangular panel."""
    # Synthetic image: dark background with a bright rectangular panel
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    # Add a bright rectangular label panel in the center (100 to 500)
    img[100:500, 150:450] = 240

    detection = opencv_fallback_detect(img)
    assert detection.method == DetectionMethod.OPENCV_FALLBACK
    assert detection.confidence >= 0.60
    # Check that bounding box roughly bounds the panel [150, 100, 450, 500]
    assert abs(detection.pdp_bbox.x_min - 150) <= 15
    assert abs(detection.pdp_bbox.y_min - 100) <= 15
    assert abs(detection.pdp_bbox.x_max - 450) <= 15
    assert abs(detection.pdp_bbox.y_max - 500) <= 15


def test_opencv_fallback_detect_empty_or_bad_image():
    """Verify opencv_fallback_detect never raises on degenerate/empty inputs."""
    empty_img = np.array([], dtype=np.uint8)
    det1 = opencv_fallback_detect(empty_img)
    assert det1.method == DetectionMethod.OPENCV_FALLBACK
    assert det1.confidence <= 0.50

    none_det = opencv_fallback_detect(None)
    assert none_det.method == DetectionMethod.OPENCV_FALLBACK


def test_detect_pdp_never_raises():
    """Verify detect_pdp safely returns a valid Detection object on any image."""
    blank = np.zeros((400, 400, 3), dtype=np.uint8)
    det = detect_pdp(blank)
    assert det is not None
    assert det.pdp_bbox.x_max > det.pdp_bbox.x_min
    assert det.pdp_bbox.y_max > det.pdp_bbox.y_min
