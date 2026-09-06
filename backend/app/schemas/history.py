from pydantic import BaseModel

from app.schemas.scan import ScanSummaryItem


class PaginatedScansResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[ScanSummaryItem]
