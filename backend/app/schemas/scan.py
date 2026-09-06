from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.compliance import ComplianceResultSchema, ExtractedField
from app.schemas.enums import CalibrationMethod, ComplianceStatus, ProductCategory


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    product_id: int | None = None
    product_name: str | None = None
    brand_name: str | None = None
    category: ProductCategory | None = ProductCategory.STANDARD_RETAIL
    overall_status: ComplianceStatus
    overall_confidence: float
    calibrated_scale_factor: float | None = None
    calibration_method: CalibrationMethod = CalibrationMethod.NONE
    rule_version: str = "LMPC-2011-v1.0"
    original_image_url: str | None = None
    evidence_image_url: str | None = None
    created_at: datetime
    extracted_fields: dict[str, ExtractedField] = {}
    compliance_results: list[ComplianceResultSchema] = []


class ScanSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    product_name: str | None = None
    brand_name: str | None = None
    category: ProductCategory | None = ProductCategory.STANDARD_RETAIL
    overall_status: ComplianceStatus
    overall_confidence: float
    rule_version: str = "LMPC-2011-v1.0"
    evidence_image_url: str | None = None
    violations_count: int = 0
    created_at: datetime


# Alias for backward compatibility with Shubh's initial scaffold
ScanResult = ScanResponse
