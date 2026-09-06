from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import Product, Scan, User
from app.db.session import get_db
from app.schemas.enums import ComplianceStatus, ProductCategory

router = APIRouter(prefix="/search", tags=["Search & Retrieval"])


@router.get("", response_model=dict[str, Any])
def universal_search(
    q: str = Query(
        ...,
        min_length=1,
        description="Search term for product name, brand, scan UUID, or manufacturer",
    ),
    status_filter: ComplianceStatus | None = Query(
        None, alias="status", description="Filter by compliance status"
    ),
    category_filter: ProductCategory | None = Query(
        None, alias="category", description="Filter by category"
    ),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Universal search across scanned products, brands, manufacturers, and scan IDs."""
    query = db.query(Scan).outerjoin(Product, Scan.product_id == Product.id)

    search_filters = or_(
        Product.product_name.ilike(f"%{q}%"),
        Product.brand_name.ilike(f"%{q}%"),
        Product.manufacturer_details.ilike(f"%{q}%"),
        Product.category.ilike(f"%{q}%"),
        Scan.id.ilike(f"%{q}%"),
    )
    query = query.filter(search_filters)

    if status_filter:
        query = query.filter(Scan.overall_status == status_filter.value)

    if category_filter:
        query = query.filter(Product.category == category_filter.value)

    scans = query.order_by(Scan.created_at.desc()).limit(limit).all()

    results: list[dict[str, Any]] = []
    for s in scans:
        p_name = s.product.product_name if s.product else "Unknown Product"
        b_name = s.product.brand_name if s.product else None
        cat = s.product.category if s.product else "standard_retail"
        results.append(
            {
                "scan_id": s.id,
                "product_name": p_name,
                "brand_name": b_name,
                "category": cat,
                "overall_status": s.overall_status,
                "overall_confidence": s.overall_confidence,
                "rule_version": s.rule_version,
                "created_at": s.created_at.isoformat(),
            }
        )

    return {"query": q, "count": len(results), "results": results}
