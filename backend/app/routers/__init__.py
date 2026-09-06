from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.history import router as history_router
from app.routers.reports import router as reports_router
from app.routers.scan import router as scan_router
from app.routers.search import router as search_router

__all__ = [
    "auth_router",
    "scan_router",
    "history_router",
    "search_router",
    "dashboard_router",
    "reports_router",
]
