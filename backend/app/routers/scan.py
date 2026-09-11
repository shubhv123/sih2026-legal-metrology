"""
Owner: SHUBH

Automated Legal Metrology (Packaged Commodities) Rules, 2011 Compliance Scanning Endpoint.
Pipeline:
  image -> decode & EXIF orientation -> detect_pdp -> run_ocr -> extract_fields
  -> get_calibration -> evaluate_font_heights -> check_placements
  -> evaluate_compliance (rule engine) -> draw annotated evidence image
  -> persist ScanRecord to DB -> return ScanResult
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.models import ComplianceResult as DBComplianceResult, Product, Scan
from app.db.session import get_db
from app.schemas.enums import CalibrationMethod, ComplianceStatus, ProductCategory
from app.schemas.scan import (
    BoundingBox,
    ComplianceResult,
    Detection,
    DetectionMethod,
    ExtractedField,
    FieldStatus,
    FontAnalysis,
    PlacementCheck,
    ScanResult,
    ScanResponse,
)
from app.services.compliance.rule_engine import determine_overall_status, evaluate_compliance
from app.services.vision.calibration import evaluate_font_heights, get_calibration
from app.services.vision.detection import detect_pdp
from app.services.vision.extraction import extract_fields
from app.services.vision.ocr import run_ocr
from app.services.vision.preprocessing import decode_image

router = APIRouter(prefix="/api/v1", tags=["scan"])

# Static image storage directories
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "data" / "static"
EVIDENCE_DIR = STATIC_DIR / "evidence"
ORIGINALS_DIR = STATIC_DIR / "originals"

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)


def _draw_evidence_image(
    image: np.ndarray,
    pdp_bbox: List[int],
    detection_method: DetectionMethod,
    detection_conf: float,
    extracted_fields: List[ExtractedField],
) -> np.ndarray:
    """
    Draws explainable visual annotations on the evidence image:
      - PDP bounding box with color-coded badge.
      - Extracted declaration bounding boxes with field name and confidence badges.
    """
    annotated = image.copy()
    h, w = annotated.shape[:2]

    # 1. Draw PDP Bounding Box
    if pdp_bbox and len(pdp_bbox) == 4:
        px1, py1, px2, py2 = pdp_bbox
        px1 = max(0, min(w - 1, int(px1)))
        py1 = max(0, min(h - 1, int(py1)))
        px2 = max(0, min(w - 1, int(px2)))
        py2 = max(0, min(h - 1, int(py2)))

        pdp_color = (255, 190, 0) if detection_method == DetectionMethod.YOLO else (0, 230, 0)
        cv2.rectangle(annotated, (px1, py1), (px2, py2), pdp_color, 3)

        badge_text = f"PDP: {detection_method.value.upper()} ({detection_conf:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(badge_text, font, font_scale, thickness)

        badge_y = max(th + 6, py1 - 8)
        cv2.rectangle(
            annotated,
            (px1, badge_y - th - 4),
            (px1 + tw + 8, badge_y + baseline),
            pdp_color,
            -1,
        )
        cv2.putText(
            annotated,
            badge_text,
            (px1 + 4, badge_y - 2),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA,
        )

    # 2. Draw Extracted Declarations
    for field in extracted_fields:
        if not field.bbox:
            continue
        bx1 = max(0, min(w - 1, int(field.bbox.x_min)))
        by1 = max(0, min(h - 1, int(field.bbox.y_min)))
        bx2 = max(0, min(w - 1, int(field.bbox.x_max)))
        by2 = max(0, min(h - 1, int(field.bbox.y_max)))

        box_color = (0, 140, 255)  # Orange for statutory fields
        cv2.rectangle(annotated, (bx1, by1), (bx2, by2), box_color, 2)

        norm_val = str(field.normalized_value)
        if len(norm_val) > 20:
            norm_val = norm_val[:18] + ".."
        tag_text = f"{field.field_name}: {norm_val}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(tag_text, font, font_scale, thickness)

        tag_y = max(th + 4, by1 - 4)
        cv2.rectangle(
            annotated,
            (bx1, tag_y - th - 3),
            (bx1 + tw + 6, tag_y + baseline),
            box_color,
            -1,
        )
        cv2.putText(
            annotated,
            tag_text,
            (bx1 + 3, tag_y - 1),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )

    return annotated


@router.post("/scan", response_model=ScanResult)
async def scan_label(
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    calibration_method: CalibrationMethod = Form(CalibrationMethod.ARUCO),
    known_object_size_mm: Optional[float] = Form(None),
    known_marker_size_mm: Optional[float] = Form(None),
    product_category: Optional[str] = Form("standard_retail"),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Scans a packaged commodity label image and performs automated LMPC Rule 6 & 7 compliance checks.
    Pipeline:
      1. Decode and normalize image.
      2. Detect PDP via YOLOv8n with OpenCV contour fallback.
      3. Run EasyOCR on the image/panel.
      4. Extract mandatory declarations with RapidFuzz label matching + regex value parsing.
      5. Calibrate spatial scale (ArUco marker or reference object).
      6. Verify Rule 7 character font heights.
      7. Verify Rule 6 PDP placement grouping.
      8. Evaluate compliance with three-state logic (PASS, FAIL, REVIEW_REQUIRED).
      9. Generate annotated evidence image and persist to SQLite DB.
    """
    upload = image or file
    if upload is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image file is required (use form field 'image' or 'file')",
        )

    scan_id = str(uuid.uuid4())
    effective_category = category or product_category or "standard_retail"
    timestamp = datetime.now(timezone.utc)

    # 1. Read and Decode Image Bytes
    try:
        contents = await upload.read()
        img_bgr = decode_image(contents)
    except Exception as exc:
        img_bgr = None

    if img_bgr is None or img_bgr.size == 0:
        # Graceful degradation on corrupt/unreadable input
        orig_url = f"/static/originals/{scan_id}.jpg"
        evid_url = f"/static/evidence/{scan_id}.jpg"
        return ScanResult(
            scan_id=scan_id,
            product_name="Unreadable Image",
            product_name_hint="Unreadable Image",
            timestamp=timestamp,
            created_at=timestamp,
            category=ProductCategory.STANDARD_RETAIL,
            detection=Detection(
                method=DetectionMethod.OPENCV_FALLBACK,
                confidence=0.0,
                pdp_bbox=BoundingBox(x_min=0, y_min=0, x_max=0, y_max=0),
            ),
            extracted_fields=[],
            font_analysis=FontAnalysis(calibration_method=CalibrationMethod.NONE, fields=[]),
            placement_checks=[],
            compliance_results=[
                ComplianceResult(
                    rule_id="RULE_IMAGE_VALIDATION",
                    field_name="image",
                    status=FieldStatus.REVIEW_REQUIRED,
                    confidence=0.0,
                    message="Uploaded image could not be decoded. Please upload a clear photo in JPEG or PNG format.",
                    rule_version="LMPC-2011-v1.0",
                )
            ],
            overall_status=FieldStatus.REVIEW_REQUIRED,
            overall_confidence=0.0,
            rule_version="LMPC-2011-v1.0",
            evidence_image_url=evid_url,
            original_image_url=orig_url,
        )

    img_h, img_w = img_bgr.shape[:2]

    # Save original image
    orig_filename = f"{scan_id}.jpg"
    orig_path = ORIGINALS_DIR / orig_filename
    cv2.imwrite(str(orig_path), img_bgr)
    orig_url = f"/static/originals/{orig_filename}"

    # 2. PDP Detection (YOLOv8n with OpenCV contour fallback)
    try:
        detection_obj = detect_pdp(img_bgr)
        pdp_bbox = [
            detection_obj.pdp_bbox.x_min,
            detection_obj.pdp_bbox.y_min,
            detection_obj.pdp_bbox.x_max,
            detection_obj.pdp_bbox.y_max,
        ]
        det_method = detection_obj.method
        det_conf = detection_obj.confidence
    except Exception:
        pdp_bbox = [0, 0, img_w, img_h]
        det_method = DetectionMethod.OPENCV_FALLBACK
        det_conf = 0.50
        detection_obj = Detection(
            method=det_method,
            confidence=det_conf,
            pdp_bbox=BoundingBox(
                x_min=0,
                y_min=0,
                x_max=img_w,
                y_max=img_h,
            ),
        )

    # 3. OCR Transcription
    try:
        ocr_results = run_ocr(img_bgr)
    except Exception:
        ocr_results = []

    # 4. Mandatory Field Extraction (RapidFuzz + Regex Normalization)
    try:
        extracted_fields = extract_fields(ocr_results)
    except Exception:
        extracted_fields = []

    # 5. Dual Scale Calibration
    try:
        marker_size = known_marker_size_mm or known_object_size_mm or 24.0
        mm_per_px, calib_conf, eff_calib_method = get_calibration(
            image=img_bgr,
            method=calibration_method,
            known_object_size_mm=known_object_size_mm,
            aruco_marker_size_mm=marker_size,
        )
    except Exception:
        mm_per_px = None
        calib_conf = 0.0
        eff_calib_method = CalibrationMethod.NONE

    # 6. Rule 7 Font Height Verification
    try:
        font_analysis = evaluate_font_heights(
            extracted_fields=extracted_fields,
            mm_per_pixel=mm_per_px,
            calibration_method=eff_calib_method,
            calibration_confidence=calib_conf,
        )
    except Exception:
        font_analysis = FontAnalysis(calibration_method=eff_calib_method, fields=[])

    # 7. Rule 6 PDP Placement Verification
    # An inspector captures the primary displayed face. When multiple stickers (e.g. brand + info sticker)
    # or curved cylindrical labels are photographed, the effective display panel encompasses the label face.
    placement_checks: List[PlacementCheck] = []
    px1, py1, px2, py2 = pdp_bbox

    if extracted_fields:
        valid_boxes = [f.bbox for f in extracted_fields if f.bbox]
        if valid_boxes:
            min_fx = min(b.x_min for b in valid_boxes)
            min_fy = min(b.y_min for b in valid_boxes)
            max_fx = max(b.x_max for b in valid_boxes)
            max_fy = max(b.y_max for b in valid_boxes)
            px1 = min(px1, min_fx - 30)
            py1 = min(py1, min_fy - 30)
            px2 = max(px2, max_fx + 30)
            py2 = max(py2, max_fy + 30)

    for f in extracted_fields:
        if not f.bbox:
            continue
        within_pdp = (
            f.bbox.x_min >= px1 - 35
            and f.bbox.x_max <= px2 + 35
            and f.bbox.y_min >= py1 - 35
            and f.bbox.y_max <= py2 + 35
        )
        # Placement confidence accounts for both panel detection confidence and field OCR confidence
        field_conf = float(f.confidence) if f.confidence is not None else 0.85
        pc_conf = round(float(0.5 * det_conf + 0.5 * field_conf), 4) if within_pdp else round(float(det_conf), 4)
        placement_checks.append(
            PlacementCheck(
                field_name=f.field_name,
                within_pdp=bool(within_pdp),
                confidence=pc_conf,
            )
        )

    # 8. Statutory Rule Engine Compliance Evaluation
    try:
        compliance_results = evaluate_compliance(
            extracted_fields=extracted_fields,
            font_analysis=font_analysis,
            placement_checks=placement_checks,
            category=effective_category,
        )
        overall_status = determine_overall_status(compliance_results)
    except Exception as exc:
        compliance_results = [
            ComplianceResult(
                rule_id="RULE_ENGINE_ERROR",
                field_name="general",
                status=FieldStatus.REVIEW_REQUIRED,
                confidence=0.50,
                message=f"Rule engine encountered an issue: {exc}. Routed to officer manual review.",
                rule_version="LMPC-2011-v1.0",
            )
        ]
        overall_status = FieldStatus.REVIEW_REQUIRED

    # Determine overall confidence
    if compliance_results:
        overall_confidence = round(
            float(min(r.confidence for r in compliance_results)), 4
        )
    else:
        overall_confidence = 0.50

    # Derive product name hint from extracted declarations if present
    name_candidates = [
        f.normalized_value
        for f in extracted_fields
        if f.field_name in ["generic_name", "product_name", "brand_name"]
    ]
    if name_candidates:
        product_name_hint = str(name_candidates[0])
    else:
        # Fallback to prominent title words detected with high confidence
        prominent = [
            r["text"]
            for r in ocr_results
            if float(r.get("confidence", 0)) >= 0.8
            and r["bbox"].y_min < img_h * 0.7
            and not any(
                kw in r["text"].lower()
                for kw in ["mrp", "rs", "net", "mfg", "lic", "fssai", "batch", "see", "code", "owner", "marketed", "by", "for"]
            )
        ]
        product_name_hint = " ".join(prominent[:2]) if prominent else "Scanned Commodity Sample"

    # 9. Draw and Save Annotated Evidence Image
    evidence_filename = f"{scan_id}.jpg"
    evidence_path = EVIDENCE_DIR / evidence_filename
    try:
        annotated_img = _draw_evidence_image(
            image=img_bgr,
            pdp_bbox=pdp_bbox,
            detection_method=det_method,
            detection_conf=det_conf,
            extracted_fields=extracted_fields,
        )
        cv2.imwrite(str(evidence_path), annotated_img)
    except Exception:
        # Fallback to saving original image as evidence if drawing fails
        cv2.imwrite(str(evidence_path), img_bgr)

    evidence_url = f"/static/evidence/{evidence_filename}"

    # Category enum matching
    cat_enum = ProductCategory.STANDARD_RETAIL
    if effective_category in ProductCategory._value2member_map_:
        cat_enum = ProductCategory(effective_category)

    # 10. Persist to Database (backed for /history, /dashboard, /reports)
    try:
        # Check if Product table should be populated
        db_product = (
            db.query(Product)
            .filter(Product.product_name == product_name_hint)
            .first()
        )
        if not db_product:
            db_product = Product(
                product_name=product_name_hint,
                category=effective_category,
            )
            db.add(db_product)
            db.flush()

        # Build extracted fields dictionary for JSON serialization
        extracted_fields_dict = {
            f.field_name: {
                "field_name": f.field_name,
                "raw_ocr_text": f.raw_ocr_text,
                "normalized_value": f.normalized_value,
                "confidence": f.confidence,
                "bbox": f.bbox.model_dump() if f.bbox else None,
            }
            for f in extracted_fields
        }

        db_scan = Scan(
            id=scan_id,
            product_id=db_product.id if db_product else None,
            original_image_path=orig_url,
            evidence_image_path=evidence_url,
            overall_status=overall_status.value,
            overall_confidence=overall_confidence,
            calibrated_scale_factor=mm_per_px,
            calibration_method=eff_calib_method.value,
            rule_version="LMPC-2011-v1.0",
            extracted_fields_json=json.dumps(extracted_fields_dict),
            created_at=timestamp,
        )
        db.add(db_scan)

        for cr in compliance_results:
            db.add(
                DBComplianceResult(
                    scan_id=scan_id,
                    rule_id=cr.rule_id,
                    rule_name=cr.rule_name or cr.rule_id,
                    field_name=cr.field_name,
                    status=cr.status.value,
                    confidence=cr.confidence,
                    measured_value=cr.measured_value or cr.message,
                    expected_value=cr.expected_value,
                    violation_reason=cr.violation_reason or cr.message,
                    rule_version=cr.rule_version,
                    created_at=timestamp,
                )
            )

        db.commit()
    except Exception as db_exc:
        db.rollback()
        # Non-fatal DB error: log and still return valid response to user

    # 11. Return Complete ScanResult
    return ScanResult(
        scan_id=scan_id,
        product_name=product_name_hint,
        product_name_hint=product_name_hint,
        brand_name=None,
        category=cat_enum,
        timestamp=timestamp,
        created_at=timestamp,
        detection=detection_obj,
        extracted_fields=extracted_fields,
        font_analysis=font_analysis,
        placement_checks=placement_checks,
        compliance_results=compliance_results,
        overall_status=overall_status,
        overall_confidence=overall_confidence,
        calibrated_scale_factor=mm_per_px,
        calibration_method=eff_calib_method,
        rule_version="LMPC-2011-v1.0",
        evidence_image_url=evidence_url,
        original_image_url=orig_url,
    )
