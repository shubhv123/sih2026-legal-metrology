from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .history import router as history_router
from .reports import router as reports_router
from .scan import router as scan_router
from .search import router as search_router

__all__ = [
    "auth_router",
    "scan_router",
    "history_router",
    "search_router",
    "dashboard_router",
    "reports_router",
]
