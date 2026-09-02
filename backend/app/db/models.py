"""
Owner: ADITYA

These tables back the /history, /search, /dashboard, and /reports
endpoints. scan_result_json stores the FULL ScanResult (Shubh's
schema) as JSON so we don't have to model every nested field as
separate columns for a 10-day prototype - query the JSON for detail
views, use the indexed columns (status, product_name, created_at)
for filtering/search/dashboard aggregation.
"""

from sqlalchemy import Column, String, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserRoleEnum(str, enum.Enum):
    INSPECTOR = "inspector"
    ADMIN = "admin"


class ComplianceStatusEnum(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(UserRoleEnum), nullable=False)


class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(String, primary_key=True)
    product_name_hint = Column(String, nullable=True, index=True)
    overall_status = Column(SAEnum(ComplianceStatusEnum), nullable=False, index=True)
    rule_version = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    evidence_image_url = Column(String, nullable=False)
    original_image_url = Column(String, nullable=False)

    # Full ScanResult (Shubh's pydantic schema, .dict()) stored as JSON.
    # This is what /history/{scan_id} and /reports/{scan_id}/json read from.
    scan_result_json = Column(JSON, nullable=False)
