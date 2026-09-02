"""
Owner: shared - whoever touches this, tell the others.

This file just wires routers together. Route LOGIC lives in
app/routers/*.py and app/services/*. Don't add business logic here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import scan, history, reports, dashboard, auth

app = FastAPI(
    title="Legal Metrology Compliance Checker",
    description="SIH26034 - Automated packaging compliance checking",
    version="0.1.0",
)

# Keshav's React dev server - adjust origin if you use a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves evidence/original images referenced in ScanResult URLs
app.mount("/static", StaticFiles(directory="app/data/static"), name="static")

app.include_router(scan.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(auth.router)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
