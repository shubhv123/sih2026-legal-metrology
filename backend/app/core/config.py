import os
from pathlib import Path

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    PROJECT_NAME: str = "SIH26034 Legal Metrology Compliance Checker"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'compliance.db'}")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sih2026-insecure-dev-secret-key")
    RULE_CONFIG_PATH: str = os.getenv(
        "RULE_CONFIG_PATH", str(BASE_DIR / "app" / "data" / "rules" / "lmpc_rules_v1.json")
    )
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
    STATIC_UPLOAD_DIR: str = os.getenv("STATIC_UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]


settings = Settings()
