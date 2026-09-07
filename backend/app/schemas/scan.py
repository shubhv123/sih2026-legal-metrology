"""
Shared Scan Contract
Owned by: Shubh (vision pipeline output) + Aditya (compliance results, DB persistence, reports)

Unifies vision explainability outputs (detection bbox, character font analysis, placement checks)
with database persistence and PDF/DOCX reporting fields.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CalibrationMethod, ComplianceStatus, ProductCategory


class DetectionMethod(str, Enum):
    YOLO = "yolo"
    OPENCV_FALLBACK = "opencv_fallback"


# Preserve FieldStatus as an alias / match for ComplianceStatus
FieldStatus = ComplianceStatus


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
    field_name: str
    raw_ocr_text: str = ""
    raw_text: Optional[str] = None
    normalized_value: Any = ""
    unit: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    bbox: Optional[BoundingBox] = None
    bounding_box: Optional[List[int]] = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Harmonize raw_text and raw_ocr_text
        if not self.raw_ocr_text and self.raw_text:
            self.raw_ocr_text = self.raw_text
        if not self.raw_text and self.raw_ocr_text:
            self.raw_text = self.raw_ocr_text
        # Harmonize bbox and bounding_box [ymin, xmin, ymax, xmax]
        if self.bbox and not self.bounding_box:
            self.bounding_box = [self.bbox.y_min, self.bbox.x_min, self.bbox.y_max, self.bbox.x_max]
        elif self.bounding_box and not self.bbox:
            self.bbox = BoundingBox(
                x_min=self.bounding_box[1],
                y_min=self.bounding_box[0],
                x_max=self.bounding_box[3],
                y_max=self.bounding_box[2],
            )


class FontAnalysisField(BaseModel):
    field_name: str
    measured_height_mm: float
    required_height_mm: float
    status: FieldStatus
    calibration_confidence: float = Field(..., ge=0, le=1)


class FontAnalysis(BaseModel):
    calibration_method: CalibrationMethod
    mm_per_pixel: Optional[float] = None
    fields: List[FontAnalysisField] = []


class PlacementCheck(BaseModel):
    field_name: str
    within_pdp: bool
    confidence: float = Field(..., ge=0, le=1)


class ComplianceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    rule_name: Optional[str] = None
    field_name: str
    status: FieldStatus
    confidence: float = Field(..., ge=0, le=1)
    message: str = ""
    violation_reason: Optional[str] = None
    measured_value: Optional[str] = None
    expected_value: Optional[str] = None
    rule_version: str = "LMPC-2011-v1.0"

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.message and self.violation_reason:
            self.message = self.violation_reason
        elif not self.violation_reason and self.message:
            self.violation_reason = self.message
        if not self.rule_name:
            self.rule_name = self.rule_id.replace("_", " ").title()


# Alias for backward compatibility
ComplianceResultSchema = ComplianceResult


class ScanSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    category: Optional[ProductCategory] = ProductCategory.STANDARD_RETAIL
    overall_status: ComplianceStatus
    overall_confidence: float
    rule_version: str = "LMPC-2011-v1.0"
    evidence_image_url: Optional[str] = None
    violations_count: int = 0
    created_at: datetime


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    product_id: Optional[int] = None
    product_name: Optional[str] = "Scanned Commodity Sample"
    product_name_hint: Optional[str] = None
    brand_name: Optional[str] = None
    category: Optional[ProductCategory] = ProductCategory.STANDARD_RETAIL
    overall_status: ComplianceStatus = ComplianceStatus.REVIEW_REQUIRED
    overall_confidence: float = 0.85
    calibrated_scale_factor: Optional[float] = None
    calibration_method: CalibrationMethod = CalibrationMethod.NONE
    rule_version: str = "LMPC-2011-v1.0"
    original_image_url: Optional[str] = None
    evidence_image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    timestamp: Optional[datetime] = None

    # Vision explainability artifacts (Keshav frontend & UI inspect)
    detection: Optional[Detection] = None
    extracted_fields: Union[List[ExtractedField], Dict[str, Any]] = []
    font_analysis: Optional[FontAnalysis] = None
    placement_checks: Optional[List[PlacementCheck]] = []
    compliance_results: List[ComplianceResult] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.product_name and self.product_name_hint:
            self.product_name = self.product_name_hint
        if not self.product_name_hint and self.product_name:
            self.product_name_hint = self.product_name
        if not self.created_at and self.timestamp:
            self.created_at = self.timestamp
        if not self.timestamp and self.created_at:
            self.timestamp = self.created_at


# Unified alias
ScanResult = ScanResponse


class ScanRequest(BaseModel):
    calibration_method: CalibrationMethod = CalibrationMethod.ARUCO
    known_object_size_mm: Optional[float] = None
