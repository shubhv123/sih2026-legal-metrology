"""Owned by: Aditya"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.scan import FieldStatus, ScanResult


class ScanSummary(BaseModel):
    """Lightweight version shown in history/search lists - NOT the full ScanResult."""
    scan_id: str
    product_name_hint: Optional[str] = None
    timestamp: datetime
    overall_status: FieldStatus
    evidence_thumbnail_url: str


class HistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[ScanSummary]


class HistoryQueryParams(BaseModel):
    """Documents expected query params for GET /api/v1/history"""
    page: int = 1
    page_size: int = 20
    status: Optional[FieldStatus] = None
    product_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ScanDetailResponse(ScanResult):
    """GET /api/v1/history/{scan_id} returns the full ScanResult as-is."""
    pass
