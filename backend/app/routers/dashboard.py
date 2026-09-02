"""
Owner: ADITYA

TODO(aditya):
 1. Replace mock stats with real aggregation queries over the Scan table
    (COUNT grouped by overall_status, GROUP BY date for trend, etc.)
 2. violations_by_field: count how many times each field_name appears
    with status=FAIL across all scans.
 3. Keep this endpoint FAST - it's called every time the dashboard page
    loads. If it gets slow, pre-aggregate on write (when a scan is saved)
    instead of computing on every read.
"""

from fastapi import APIRouter

from app.schemas.dashboard import DashboardStats, TrendPoint

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """MOCK - replace with real DB aggregation."""
    return DashboardStats(
        total_scans=42,
        compliant_count=28,
        non_compliant_count=9,
        review_required_count=5,
        violations_by_field={"mrp": 3, "consumer_care": 4, "net_quantity": 2},
        compliance_trend=[
            TrendPoint(date="2026-09-01", compliant=5, non_compliant=1, review_required=0),
            TrendPoint(date="2026-09-02", compliant=6, non_compliant=2, review_required=1),
        ],
        rule_version="LMPC-2011-v1.0",
    )
