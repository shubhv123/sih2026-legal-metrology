from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import ComplianceStatus


class ExtractedField(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field_name: str | None = None
    raw_text: str
    normalized_value: Any | None = None
    unit: str | None = None
    confidence: float
    bounding_box: list[int] | None = None  # [ymin, xmin, ymax, xmax]


class ComplianceResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    rule_name: str
    field_name: str
    status: ComplianceStatus
    confidence: float
    measured_value: str | None = None
    expected_value: str | None = None
    violation_reason: str | None = None
    rule_version: str = "LMPC-2011-v1.0"
