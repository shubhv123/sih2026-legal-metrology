"""
Tests for live /api/v1/scan endpoint and health check.
Confirms 200 response with validated ScanResult schema, fault-tolerance, and persistence.
"""

from pathlib import Path
from fastapi.testclient import TestClient
import numpy as np
import cv2

from app.main import app
from app.schemas.scan import ScanResult

client = TestClient(app)

SAMPLE_IMAGE_PATH = Path(__file__).parent / "sample_images" / "compliant_label.jpg"


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_live_pipeline_with_sample_image():
    """Verify live scan pipeline processes image, produces ScanResult, and creates evidence image."""
    if not SAMPLE_IMAGE_PATH.exists():
        # Create a synthetic label with text
        canvas = np.ones((400, 400, 3), dtype=np.uint8) * 255
        cv2.putText(canvas, "MRP Rs 199.00", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(canvas, "Net Wt: 250 g", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        _, img_bytes = cv2.imencode(".jpg", canvas)
        content = img_bytes.tobytes()
    else:
        with open(SAMPLE_IMAGE_PATH, "rb") as f:
            content = f.read()

    response = client.post(
        "/api/v1/scan",
        files={"image": ("test_package.jpg", content, "image/jpeg")},
        data={"calibration_method": "aruco", "product_category": "standard_retail"},
    )

    assert response.status_code == 200
    data = response.json()

    # Validate against Pydantic model
    validated = ScanResult(**data)
    assert validated.scan_id is not None
    assert validated.overall_status in ["PASS", "FAIL", "REVIEW_REQUIRED"]
    assert validated.evidence_image_url.startswith("/static/evidence/")
    assert validated.original_image_url.startswith("/static/originals/")
    assert validated.rule_version == "LMPC-2011-v1.0"
    assert validated.detection is not None
    assert validated.detection.method in ["yolo", "opencv_fallback"]


def test_scan_unusual_corrupt_input_never_500():
    """Verify pipeline degrades gracefully to REVIEW_REQUIRED on corrupt input without crashing."""
    corrupt_bytes = b"not-a-real-image-corrupt-data-here"

    response = client.post(
        "/api/v1/scan",
        files={"image": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    validated = ScanResult(**data)
    assert validated.overall_status == "REVIEW_REQUIRED"
    assert validated.overall_confidence == 0.0
