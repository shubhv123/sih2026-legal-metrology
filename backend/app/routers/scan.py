"""
Owner: SHUBH

This is the highest-priority endpoint - Keshav's Upload/Results pages
and Aditya's rule engine both depend on this response shape.

TODO(shubh):
 1. Replace the mock ScanResult below with the real pipeline call:
    detection -> preprocessing -> ocr -> extraction -> calibration
 2. Call into app.services.compliance.rule_engine (Aditya's code) to
    fill compliance_results + overall_status - don't duplicate rule
    logic here, just call his function.
 3. Save annotated evidence image, return its URL.
 4. Persist the ScanResult to DB (db/models.py) before returning -
    this is what makes /history and /dashboard work.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.schemas.scan import (
    ScanResult, CalibrationMethod, Detection, DetectionMethod,
    BoundingBox, ExtractedField, FontAnalysis, FontAnalysisField,
    PlacementCheck, ComplianceResult, FieldStatus,
)

router = APIRouter(prefix="/api/v1", tags=["scan"])


@router.post("/scan", response_model=ScanResult)
async def scan_label(
    image: UploadFile = File(...),
    calibration_method: CalibrationMethod = Form(CalibrationMethod.ARUCO),
    known_object_size_mm: Optional[float] = Form(None),
):
    """
    MOCK IMPLEMENTATION - replace with real pipeline.
    This mock lets Keshav (frontend) and Aditya (rule engine wiring)
    build against a stable shape from day 1.
    """
    scan_id = str(uuid.uuid4())

    return ScanResult(
        scan_id=scan_id,
        product_name_hint="Sample Product",
        timestamp=datetime.utcnow(),
        detection=Detection(
            method=DetectionMethod.OPENCV_FALLBACK,
            confidence=0.91,
            pdp_bbox=BoundingBox(x_min=40, y_min=30, x_max=560, y_max=420),
        ),
        extracted_fields=[
            ExtractedField(
                field_name="mrp",
                raw_ocr_text="MRP Rs.199",
                normalized_value="199.00",
                confidence=0.95,
                bbox=BoundingBox(x_min=100, y_min=350, x_max=220, y_max=380),
            ),
            ExtractedField(
                field_name="net_quantity",
                raw_ocr_text="Net Wt 200g",
                normalized_value="200 g",
                confidence=0.89,
                bbox=BoundingBox(x_min=100, y_min=300, x_max=250, y_max=330),
            ),
        ],
        font_analysis=FontAnalysis(
            calibration_method=calibration_method,
            mm_per_pixel=0.12,
            fields=[
                FontAnalysisField(
                    field_name="mrp",
                    measured_height_mm=2.6,
                    required_height_mm=2.5,
                    status=FieldStatus.PASS,
                    calibration_confidence=0.88,
                ),
            ],
        ),
        placement_checks=[
            PlacementCheck(field_name="mrp", within_pdp=True, confidence=0.93),
            PlacementCheck(field_name="net_quantity", within_pdp=True, confidence=0.90),
        ],
        compliance_results=[
            ComplianceResult(
                rule_id="RULE_6_MRP_PRESENT",
                field_name="mrp",
                status=FieldStatus.PASS,
                confidence=0.95,
                message="MRP declaration detected and correctly formatted.",
                rule_version="LMPC-2011-v1.0",
            ),
            ComplianceResult(
                rule_id="RULE_6_CONSUMER_CARE_PRESENT",
                field_name="consumer_care",
                status=FieldStatus.FAIL,
                confidence=0.97,
                message="Consumer care details not found on package.",
                rule_version="LMPC-2011-v1.0",
            ),
        ],
        overall_status=FieldStatus.REVIEW_REQUIRED,
        rule_version="LMPC-2011-v1.0",
        evidence_image_url=f"/static/evidence/{scan_id}.jpg",
        original_image_url=f"/static/originals/{scan_id}.jpg",
    )
