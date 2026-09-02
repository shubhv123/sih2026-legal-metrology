"""Owned by: Aditya"""

from pydantic import BaseModel
from typing import List, Dict


class TrendPoint(BaseModel):
    date: str  # ISO date string, e.g. "2026-09-05"
    compliant: int
    non_compliant: int
    review_required: int


class DashboardStats(BaseModel):
    total_scans: int
    compliant_count: int
    non_compliant_count: int
    review_required_count: int
    violations_by_field: Dict[str, int]   # e.g. {"mrp": 4, "net_quantity": 2}
    compliance_trend: List[TrendPoint]
    rule_version: str
