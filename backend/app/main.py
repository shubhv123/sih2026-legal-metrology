"""
Legal Metrology Compliance Checker FastAPI Application
SIH26034 - Automated packaging compliance verification API.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.db.seed import seed_database
from app.db.session import init_db
from app.routers import auth, dashboard, history, reports, scan, search

STATIC_DIR = Path(__file__).resolve().parent / "data" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database tables exist and seed demo data
    init_db()
    seed_database()
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "evidence").mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "originals").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Legal Metrology Compliance Checker",
    description="Automated packaging compliance verification API per Legal Metrology (Packaged Commodities) Rules, 2011",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Static file serving
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "evidence").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "originals").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount API v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(scan.router)  # scan.router already defines /api/v1/scan and /scan
app.include_router(history.router, prefix=api_v1_prefix)
app.include_router(search.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(reports.router, prefix=api_v1_prefix)


@app.get("/")
def root():
    return {
        "service": "Legal Metrology Compliance Checker",
        "status": "online",
        "api_v1": api_v1_prefix,
        "rule_version": "LMPC-2011-v1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "database": "sqlite"}


@app.get("/api/v1/health")
def health_v1():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error occurred",
            "detail": str(exc),
            "fallback_recommendation": "REVIEW_REQUIRED",
        },
    )
