"""
Smoke test for /scan endpoint mock and health check.
Confirms 200 response with correct ScanResult shape.
"""

import io
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.scan import ScanResult

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_mock_endpoint():
    # Create a dummy JPEG image in-memory
    fake_image_bytes = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9")

    response = client.post(
        "/api/v1/scan",
        files={"image": ("test_label.jpg", fake_image_bytes, "image/jpeg")},
        data={"calibration_method": "aruco"},
    )

    assert response.status_code == 200
    data = response.json()

    # Validate against Pydantic model
    validated = ScanResult(**data)
    assert validated.overall_status in ["PASS", "FAIL", "REVIEW_REQUIRED"]
    assert len(validated.extracted_fields) > 0
    assert validated.evidence_image_url.startswith("/static/evidence/")
    assert validated.rule_version == "LMPC-2011-v1.0"
