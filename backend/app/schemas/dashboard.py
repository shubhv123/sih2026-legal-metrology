from datetime import datetime

from pydantic import BaseModel

from app.schemas.enums import ComplianceStatus


class CommonViolationItem(BaseModel):
    rule_id: str
    label: str
    count: int


class RecentActivityItem(BaseModel):
    scan_id: str
    product_name: str | None = None
    overall_status: ComplianceStatus
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_scans: int
    pass_count: int
    fail_count: int
    review_required_count: int
    compliance_rate_pct: float
    most_common_violations: list[CommonViolationItem] = []
    recent_activity: list[RecentActivityItem] = []
