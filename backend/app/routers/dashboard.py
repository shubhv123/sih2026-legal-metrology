from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import ComplianceResult, Scan
from app.db.session import get_db
from app.schemas.dashboard import (
    CommonViolationItem,
    DashboardStatsResponse,
    RecentActivityItem,
)
from app.schemas.enums import ComplianceStatus

router = APIRouter(prefix="/dashboard", tags=["Monitoring Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """Aggregate compliance metrics, violation frequency, and recent scan logs."""
    total_scans = db.query(Scan).count()
    pass_count = db.query(Scan).filter(Scan.overall_status == ComplianceStatus.PASS.value).count()
    fail_count = db.query(Scan).filter(Scan.overall_status == ComplianceStatus.FAIL.value).count()
    review_count = (
        db.query(Scan).filter(Scan.overall_status == ComplianceStatus.REVIEW_REQUIRED.value).count()
    )

    compliance_rate = round((pass_count / total_scans * 100.0), 1) if total_scans > 0 else 0.0

    # Query most common violations
    violation_rows = (
        db.query(
            ComplianceResult.rule_id,
            ComplianceResult.rule_name,
            func.count(ComplianceResult.id).label("v_count"),
        )
        .filter(ComplianceResult.status == ComplianceStatus.FAIL.value)
        .group_by(ComplianceResult.rule_id, ComplianceResult.rule_name)
        .order_by(func.count(ComplianceResult.id).desc())
        .limit(5)
        .all()
    )

    common_violations = [
        CommonViolationItem(rule_id=r[0], label=r[1], count=r[2]) for r in violation_rows
    ]

    # Recent scans
    recent_scans = db.query(Scan).order_by(Scan.created_at.desc()).limit(5).all()

    recent_activity = [
        RecentActivityItem(
            scan_id=s.id,
            product_name=s.product.product_name if s.product else "Unknown Product",
            overall_status=ComplianceStatus(s.overall_status),
            created_at=s.created_at,
        )
        for s in recent_scans
    ]

    return DashboardStatsResponse(
        total_scans=total_scans,
        pass_count=pass_count,
        fail_count=fail_count,
        review_required_count=review_count,
        compliance_rate_pct=compliance_rate,
        most_common_violations=common_violations,
        recent_activity=recent_activity,
    )
