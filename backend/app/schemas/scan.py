"""
Owned by: Shubh (detection/OCR/extraction/calibration output)
         + Aditya (compliance_results / overall_status, computed downstream)

This is THE shared contract. Do not change field names without
telling the whole team - Keshav's frontend and Aditya's rule engine
both depend on this exact shape.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class DetectionMethod(str, Enum):
    YOLO = "yolo"
    OPENCV_FALLBACK = "opencv_fallback"


class CalibrationMethod(str, Enum):
    ARUCO = "aruco"
    KNOWN_OBJECT = "known_object"
    NONE = "none"  # font-height check skipped / low confidence


class FieldStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class BoundingBox(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class Detection(BaseModel):
    method: DetectionMethod
    confidence: float = Field(..., ge=0, le=1)
    pdp_bbox: BoundingBox


class ExtractedField(BaseModel):
    field_name: str          # e.g. "mrp", "net_quantity", "manufacturer_name"
    raw_ocr_text: str        # what OCR actually saw, pre-fuzzy-match
    normalized_value: str    # after fuzzy match / cleanup
    confidence: float = Field(..., ge=0, le=1)
    bbox: BoundingBox


class FontAnalysisField(BaseModel):
    field_name: str
    measured_height_mm: float
    required_height_mm: float
    status: FieldStatus
    calibration_confidence: float = Field(..., ge=0, le=1)


class FontAnalysis(BaseModel):
    calibration_method: CalibrationMethod
    mm_per_pixel: Optional[float] = None
    fields: List[FontAnalysisField]


class PlacementCheck(BaseModel):
    field_name: str
    within_pdp: bool
    confidence: float = Field(..., ge=0, le=1)


class ComplianceResult(BaseModel):
    rule_id: str              # e.g. "RULE_6_MRP_PRESENT", "RULE_7_FONT_HEIGHT"
    field_name: str
    status: FieldStatus
    confidence: float = Field(..., ge=0, le=1)
    message: str               # human-readable explanation for the report
    rule_version: str           # e.g. "LMPC-2011-v1.0"


class ScanResult(BaseModel):
    scan_id: str
    product_name_hint: Optional[str] = None
    timestamp: datetime
    detection: Detection
    extracted_fields: List[ExtractedField]
    font_analysis: FontAnalysis
    placement_checks: List[PlacementCheck]
    compliance_results: List[ComplianceResult]
    overall_status: FieldStatus
    rule_version: str
    evidence_image_url: str    # annotated image with bboxes drawn
    original_image_url: str


class ScanRequest(BaseModel):
    """
    Sent as multipart/form-data alongside the image file - NOT as this
    JSON body directly. FastAPI route signature will be:

        async def scan(
            image: UploadFile,
            calibration_method: CalibrationMethod = Form(...),
            known_object_size_mm: Optional[float] = Form(None),
        )

    This class documents the expected form fields only.
    """
    calibration_method: CalibrationMethod
    known_object_size_mm: Optional[float] = None  # required if calibration_method == known_object
