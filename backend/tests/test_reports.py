from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.compliance import ComplianceResultSchema
from app.schemas.enums import ComplianceStatus, ProductCategory
from app.schemas.scan import ScanResponse
from app.services.reporting.pdf_report import generate_pdf_report


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def test_generate_pdf_report_direct():
    """Verify PDF report generator produces valid PDF bytes for sample scan data."""
    sample_scan = ScanResponse(
        scan_id="test-scan-uuid-12345",
        product_name="Test Packed Biscuit",
        brand_name="Test Brand",
        category=ProductCategory.FOOD_EXPIRY,
        overall_status=ComplianceStatus.PASS,
        overall_confidence=0.95,
        calibrated_scale_factor=0.082,
        rule_version="LMPC-2011-v1.0",
        created_at=datetime.now(UTC),
        compliance_results=[
            ComplianceResultSchema(
                rule_id="RULE_6_MANDATORY_DECLARATIONS",
                rule_name="Mandatory Declarations Completeness",
                field_name="all_mandatory_fields",
                status=ComplianceStatus.PASS,
                confidence=0.95,
                measured_value="6/6 fields present",
                expected_value="All Rule 6 declarations present",
                rule_version="LMPC-2011-v1.0",
            ),
            ComplianceResultSchema(
                rule_id="RULE_7_FONT_HEIGHT",
                rule_name="Minimum Character Height",
                field_name="net_quantity_numeral",
                status=ComplianceStatus.PASS,
                confidence=0.91,
                measured_value="3.0 mm",
                expected_value="Min 2.0 mm per Table-I",
                rule_version="LMPC-2011-v1.0",
            ),
        ],
    )

    pdf_bytes = generate_pdf_report(sample_scan)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_pdf_report_fail_and_review_states():
    """Verify PDF generator handles FAIL and REVIEW_REQUIRED states cleanly without error."""
    for test_status in [ComplianceStatus.FAIL, ComplianceStatus.REVIEW_REQUIRED]:
        sample_scan = ScanResponse(
            scan_id=f"test-scan-{test_status.value.lower()}",
            product_name="Test Product",
            overall_status=test_status,
            overall_confidence=0.72,
            rule_version="LMPC-2011-v1.0",
            created_at=datetime.now(UTC),
            compliance_results=[
                ComplianceResultSchema(
                    rule_id="RULE_7_FONT_HEIGHT",
                    rule_name="Minimum Character Height",
                    field_name="net_quantity_numeral",
                    status=test_status,
                    confidence=0.70,
                    violation_reason="Font size non-compliant or uncalibrated reference."
                    if test_status == ComplianceStatus.FAIL
                    else "Scale missing.",
                    rule_version="LMPC-2011-v1.0",
                )
            ],
        )
        pdf_bytes = generate_pdf_report(sample_scan)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF-")


def test_reports_pdf_endpoint(client):
    """Verify GET /api/v1/reports/{scan_id}/pdf returns 200 and application/pdf."""
    # Retrieve an existing scan ID from history
    hist_res = client.get("/api/v1/history?page=1&page_size=1")
    assert hist_res.status_code == 200
    items = hist_res.json()["items"]
    assert len(items) > 0
    scan_id = items[0]["scan_id"]

    # Request PDF
    res = client.get(f"/api/v1/reports/{scan_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "inline" in res.headers["content-disposition"]
    assert f"inspection_report_{scan_id}.pdf" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-")


def test_reports_pdf_endpoint_not_found(client):
    """Verify 404 response for non-existent scan ID."""
    res = client.get("/api/v1/reports/non-existent-uuid-99999/pdf")
    assert res.status_code == 404


def test_reports_docx_endpoint(client):
    """Verify GET /api/v1/reports/{scan_id}/docx returns 200 and document stream."""
    hist_res = client.get("/api/v1/history?page=1&page_size=1")
    assert hist_res.status_code == 200
    scan_id = hist_res.json()["items"][0]["scan_id"]

    res = client.get(f"/api/v1/reports/{scan_id}/docx")
    assert res.status_code == 200
    assert "wordprocessingml" in res.headers["content-type"]
    assert len(res.content) > 0


def test_reports_json_endpoint(client):
    """Verify GET /api/v1/reports/{scan_id}/json returns 200 and structured audit record."""
    hist_res = client.get("/api/v1/history?page=1&page_size=1")
    assert hist_res.status_code == 200
    scan_id = hist_res.json()["items"][0]["scan_id"]

    res = client.get(f"/api/v1/reports/{scan_id}/json")
    assert res.status_code == 200
    data = res.json()
    assert data["scan_id"] == scan_id
    assert "compliance_results" in data
    assert "overall_status" in data
