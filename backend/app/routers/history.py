import json
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import ComplianceResult, Product, Scan, User
from app.db.session import get_db
from app.schemas.compliance import ComplianceResultSchema, ExtractedField
from app.schemas.enums import CalibrationMethod, ComplianceStatus, ProductCategory
from app.schemas.history import PaginatedScansResponse
from app.schemas.scan import ScanResponse, ScanSummaryItem

router = APIRouter(prefix="/history", tags=["Inspection History"])


@router.get("", response_model=PaginatedScansResponse)
def list_inspection_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: ComplianceStatus | None = Query(
        None, alias="status", description="Filter by PASS, FAIL, REVIEW_REQUIRED"
    ),
    category_filter: ProductCategory | None = Query(
        None, alias="category", description="Filter by product category"
    ),
    product_name: str | None = Query(None, description="Filter by product or brand name"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List paginated inspection scan records with multi-criteria filtering."""
    query = db.query(Scan).outerjoin(Product, Scan.product_id == Product.id)

    if status_filter:
        query = query.filter(Scan.overall_status == status_filter.value)

    if category_filter:
        query = query.filter(Product.category == category_filter.value)

    if product_name:
        query = query.filter(
            (Product.product_name.ilike(f"%{product_name}%"))
            | (Product.brand_name.ilike(f"%{product_name}%"))
        )

    if from_date:
        try:
            f_dt = datetime.fromisoformat(from_date)
            query = query.filter(Scan.created_at >= f_dt)
        except ValueError:
            pass

    if to_date:
        try:
            t_dt = datetime.fromisoformat(to_date)
            query = query.filter(Scan.created_at <= t_dt)
        except ValueError:
            pass

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    scans = (
        query.order_by(Scan.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )

    items = []
    for s in scans:
        violations_count = (
            db.query(ComplianceResult)
            .filter(
                ComplianceResult.scan_id == s.id,
                ComplianceResult.status == ComplianceStatus.FAIL.value,
            )
            .count()
        )

        p_name = s.product.product_name if s.product else "Unknown Product"
        b_name = s.product.brand_name if s.product else None
        cat = (
            ProductCategory(s.product.category)
            if (s.product and s.product.category in ProductCategory._value2member_map_)
            else ProductCategory.STANDARD_RETAIL
        )

        items.append(
            ScanSummaryItem(
                scan_id=s.id,
                product_name=p_name,
                brand_name=b_name,
                category=cat,
                overall_status=ComplianceStatus(s.overall_status),
                overall_confidence=s.overall_confidence,
                rule_version=s.rule_version,
                evidence_image_url=s.evidence_image_path,
                violations_count=violations_count,
                created_at=s.created_at,
            )
        )

    return PaginatedScansResponse(
        total=total, page=page, page_size=page_size, total_pages=total_pages, items=items
    )


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_details(
    scan_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retrieve complete scan record with evidence image and compliance check breakdown."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Scan with ID {scan_id} not found"
        )

    # Parse extracted fields
    extracted_fields = {}
    if scan.extracted_fields_json:
        try:
            raw_fields = json.loads(scan.extracted_fields_json)
            for k, v in raw_fields.items():
                extracted_fields[k] = ExtractedField(**v)
        except Exception:
            extracted_fields = {}

    # Format compliance results
    compliance_results = [
        ComplianceResultSchema(
            rule_id=r.rule_id,
            rule_name=r.rule_name,
            field_name=r.field_name,
            status=ComplianceStatus(r.status),
            confidence=r.confidence,
            measured_value=r.measured_value,
            expected_value=r.expected_value,
            violation_reason=r.violation_reason,
            rule_version=r.rule_version,
        )
        for r in scan.compliance_results
    ]

    p_name = scan.product.product_name if scan.product else None
    b_name = scan.product.brand_name if scan.product else None
    cat = (
        ProductCategory(scan.product.category)
        if (scan.product and scan.product.category in ProductCategory._value2member_map_)
        else ProductCategory.STANDARD_RETAIL
    )

    return ScanResponse(
        scan_id=scan.id,
        product_id=scan.product_id,
        product_name=p_name,
        brand_name=b_name,
        category=cat,
        overall_status=ComplianceStatus(scan.overall_status),
        overall_confidence=scan.overall_confidence,
        calibrated_scale_factor=scan.calibrated_scale_factor,
        calibration_method=CalibrationMethod(scan.calibration_method)
        if scan.calibration_method in CalibrationMethod._value2member_map_
        else CalibrationMethod.NONE,
        rule_version=scan.rule_version,
        original_image_url=scan.original_image_path,
        evidence_image_url=scan.evidence_image_path,
        created_at=scan.created_at,
        extracted_fields=extracted_fields,
        compliance_results=compliance_results,
    )
