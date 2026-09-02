"""
Owner: ADITYA

TODO(aditya):
 1. /pdf -> app.services.reporting.pdf_report.generate() -> FileResponse
 2. /docx -> app.services.reporting.docx_report.generate() -> FileResponse
 3. /json -> just return the stored ScanResult as JSON (already a dict)
 All three pull the SAME stored ScanResult - don't recompute anything,
 just re-render it in a different format.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{scan_id}/pdf")
async def get_pdf_report(scan_id: str):
    raise HTTPException(status_code=501, detail="TODO(aditya): implement PDF export")


@router.get("/{scan_id}/docx")
async def get_docx_report(scan_id: str):
    raise HTTPException(status_code=501, detail="TODO(aditya): implement DOCX export")


@router.get("/{scan_id}/json")
async def get_json_report(scan_id: str):
    raise HTTPException(status_code=501, detail="TODO(aditya): return stored ScanResult as JSON")
