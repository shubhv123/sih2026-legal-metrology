"""
Owner: ADITYA

TODO(aditya):
 1. Replace mock list with real DB query (db/models.py -> Scan table)
 2. Implement filtering by status / product_name / date range
 3. /history/{scan_id} should return the FULL ScanResult exactly as
    it was saved by Shubh's /scan endpoint - same schema, no drift.
"""

from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.schemas.history import HistoryResponse, ScanSummary
from app.schemas.scan import FieldStatus

router = APIRouter(prefix="/api/v1", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = 1,
    page_size: int = 20,
    status: Optional[FieldStatus] = None,
    product_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    """MOCK - replace with real DB query."""
    mock_results = [
        ScanSummary(
            scan_id="mock-1",
            product_name_hint="Sample Product A",
            timestamp=datetime.utcnow(),
            overall_status=FieldStatus.PASS,
            evidence_thumbnail_url="/static/evidence/mock-1_thumb.jpg",
        )
    ]
    return HistoryResponse(total=1, page=page, page_size=page_size, results=mock_results)


@router.get("/history/{scan_id}")
async def get_scan_detail(scan_id: str):
    """MOCK - replace with real DB lookup. Should 404 if not found."""
    raise HTTPException(status_code=501, detail="TODO(aditya): implement DB lookup")


@router.get("/search", response_model=HistoryResponse)
async def search_scans(q: str, page: int = 1, page_size: int = 20):
    """MOCK - free-text search over product_name_hint / extracted fields."""
    return HistoryResponse(total=0, page=page, page_size=page_size, results=[])
