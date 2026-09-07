from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.history import get_scan_details
from app.services.reporting import generate_docx_report, generate_json_report, generate_pdf_report

router = APIRouter(prefix="/reports", tags=["Compliance Reports"])


@router.get("/{scan_id}/pdf")
def export_pdf_report(scan_id: str, db: Session = Depends(get_db)):
    """Export evidence-backed compliance inspection report as PDF."""
    scan_data = get_scan_details(scan_id=scan_id, db=db)
    pdf_bytes = generate_pdf_report(scan_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="inspection_report_{scan_id}.pdf"'},
    )


@router.get("/{scan_id}/docx")
def export_docx_report(scan_id: str, db: Session = Depends(get_db)):
    """Export inspection report in editable DOCX format."""
    scan_data = get_scan_details(scan_id=scan_id, db=db)
    docx_bytes = generate_docx_report(scan_data)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=compliance_report_{scan_id}.docx"},
    )


@router.get("/{scan_id}/json")
def export_json_report(scan_id: str, db: Session = Depends(get_db)):
    """Export structured JSON compliance audit record."""
    scan_data = get_scan_details(scan_id=scan_id, db=db)
    return generate_json_report(scan_data)
