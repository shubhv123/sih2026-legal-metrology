import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.seed import seed_database
from app.db.session import init_db
from app.routers import (
    auth_router,
    dashboard_router,
    history_router,
    reports_router,
    scan_router,
    search_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed demo data
    print("Ensuring database tables exist...")
    init_db()
    print("Seeding initial demo data if needed...")
    seed_database()
    os.makedirs("static/uploads", exist_ok=True)
    yield
    # Shutdown
    print("Application shutdown clean.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Automated Legal Metrology (Packaged Commodities) Rules, 2011 Compliance Verification API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for original and annotated evidence images
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount API v1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(scan_router, prefix=api_v1_prefix)
app.include_router(history_router, prefix=api_v1_prefix)
app.include_router(search_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": api_v1_prefix,
        "rule_version": "LMPC-2011-v1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "database": "sqlite"}


@app.get("/api/v1/health")
def health_v1():
    return {"status": "ok"}


# Global safety error handler: never return raw unhandled 500 crash
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
