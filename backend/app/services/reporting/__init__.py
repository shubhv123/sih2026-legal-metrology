"""Reporting and document generation service (Owner: Aditya).

Generates:
- Formal compliance audit PDF report with embedded evidence photo (ReportLab)
- Editable audit report (python-docx)
- Structured compliance JSON payload
"""

from typing import Any

from app.schemas.scan import ScanResponse
from app.services.reporting.docx_report import generate_docx_report
from app.services.reporting.pdf_report import generate_pdf_report


def generate_json_report(scan_data: ScanResponse) -> dict[str, Any]:
    """Generates structured audit payload."""
    return scan_data.model_dump(mode="json")


__all__ = [
    "generate_pdf_report",
    "generate_docx_report",
    "generate_json_report",
]
