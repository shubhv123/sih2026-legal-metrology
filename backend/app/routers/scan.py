"""Product scan router (Owner: Shubh).

Pipeline:
1. Receive image upload + optional calibration params.
2. detect_pdp() -> isolates package/PDP (YOLOv8 + OpenCV fallback).
3. calibrate_scale() -> calculates mm/px scale (ArUco + reference object fallback).
4. run_ocr_and_extract() -> extracts mandatory fields (EasyOCR + RapidFuzz + regex).
5. evaluate_compliance() -> Rule 6 completeness, placement & Rule 7 font-height check.
6. Return structured ScanResponse and save to database.
"""

import json
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models import ComplianceResult, Scan
from app.db.session import get_db
from app.schemas.compliance import ExtractedField
from app.schemas.enums import CalibrationMethod, ComplianceStatus, ProductCategory
from app.schemas.scan import ScanResponse
from app.services.compliance import evaluate_compliance
from app.services.vision import calibrate_scale, detect_pdp, run_ocr_and_extract

router = APIRouter(prefix="/scan", tags=["Product Scanning"])


@router.post("", response_model=ScanResponse)
async def upload_and_scan_label(
    file: UploadFile | None = File(None, description="Package label image"),
    image: UploadFile | None = File(None, description="Package label image (alias)"),
    known_object_size_mm: float | None = Form(
        None, description="Physical size of reference object in mm"
    ),
    calibration_method: str | None = Form(None, description="Calibration method"),
    product_category: str | None = Form(
        "standard_retail", description="Product category for exception handling"
    ),
    db: Session = Depends(get_db),
):
    """Upload product label image for automated LMPC compliance verification.

    Accepts file via either 'file' or 'image' field for client compatibility.
    """
    upload_file = file or image
    if upload_file is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Package label image is required (use form field 'file' or 'image')",
        )

    if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image (PNG, JPEG, WEBP)",
        )

    scan_id = str(uuid.uuid4())
    filename = f"{scan_id}_{upload_file.filename or 'label.jpg'}"
    upload_dir = "static/evidence"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    # Save uploaded file
    contents = await upload_file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # 1. Vision Detection (Stubbed for Shubh)
    pdp_result = detect_pdp(file_path)

    # 2. Calibration (Stubbed for Shubh)
    scale_factor, calib_method = calibrate_scale(file_path, known_object_size_mm)

    # 3. OCR & Field Extraction (Stubbed for Shubh)
    extracted_fields_raw = run_ocr_and_extract(file_path)

    # 4. Compliance Rule Engine (Aditya)
    compliance_results = evaluate_compliance(
        extracted_fields=extracted_fields_raw,
        pdp_bbox=pdp_result.get("bbox"),
        scale_factor_mm_per_px=scale_factor,
        category=product_category or "standard_retail",
    )

    # Calculate overall verdict
    has_fail = any(r.status == ComplianceStatus.FAIL for r in compliance_results)
    has_review = any(r.status == ComplianceStatus.REVIEW_REQUIRED for r in compliance_results)

    if has_fail:
        overall_status = ComplianceStatus.FAIL
    elif has_review:
        overall_status = ComplianceStatus.REVIEW_REQUIRED
    else:
        overall_status = ComplianceStatus.PASS

    overall_confidence = min((r.confidence for r in compliance_results), default=0.85)

    # Map extracted fields to schema
    extracted_fields = {k: ExtractedField(**v) for k, v in extracted_fields_raw.items()}

    # Normalize file path for URL
    image_url = "/" + file_path.replace("\\", "/")
    now_dt = datetime.now(UTC)

    # 5. Persist to database so /history, /reports, and /dashboard reflect this scan
    try:
        scan_record = Scan(
            id=scan_id,
            product_id=None,
            original_image_path=image_url,
            evidence_image_path=image_url,
            overall_status=overall_status.value,
            overall_confidence=overall_confidence,
            calibrated_scale_factor=scale_factor,
            calibration_method=calib_method or "none",
            rule_version="LMPC-2011-v1.0",
            extracted_fields_json=json.dumps(extracted_fields_raw),
            created_at=now_dt,
        )
        db.add(scan_record)

        for cr in compliance_results:
            cr_record = ComplianceResult(
                scan_id=scan_id,
                rule_id=cr.rule_id,
                rule_name=cr.rule_name,
                field_name=cr.field_name,
                status=cr.status.value,
                confidence=cr.confidence,
                measured_value=cr.measured_value,
                expected_value=cr.expected_value,
                violation_reason=cr.violation_reason,
                rule_version=cr.rule_version,
                created_at=now_dt,
            )
            db.add(cr_record)

        db.commit()
    except Exception as e:
        db.rollback()
        # Degrade gracefully - never let database error crash the scan response
        print(f"Warning: Failed to persist scan {scan_id} to DB: {e}")

    return ScanResponse(
        scan_id=scan_id,
        product_id=None,
        product_name="Scanned Commodity Sample",
        brand_name=None,
        category=(
            ProductCategory(product_category)
            if product_category in ProductCategory._value2member_map_
            else ProductCategory.STANDARD_RETAIL
        ),
        overall_status=overall_status,
        overall_confidence=overall_confidence,
        calibrated_scale_factor=scale_factor,
        calibration_method=(
            CalibrationMethod(calib_method)
            if calib_method in CalibrationMethod._value2member_map_
            else CalibrationMethod.NONE
        ),
        rule_version="LMPC-2011-v1.0",
        original_image_url=image_url,
        evidence_image_url=image_url,
        created_at=now_dt,
        extracted_fields=extracted_fields,
        compliance_results=compliance_results,
    )
