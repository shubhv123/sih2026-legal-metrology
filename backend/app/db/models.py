from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), default="inspector", nullable=False
    )  # "inspector" or "admin"
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="inspector")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    category: Mapped[str] = mapped_column(String(64), default="standard_retail", nullable=False)
    net_quantity_declared: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mrp_declared: Mapped[float | None] = mapped_column(Float, nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(
        String(64), default="India", nullable=True
    )
    manufacturer_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfg_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consumer_care: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="product")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID string
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True
    )
    original_image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    evidence_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    overall_status: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False
    )  # PASS, FAIL, REVIEW_REQUIRED
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_scale_factor: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # mm per pixel
    calibration_method: Mapped[str] = mapped_column(
        String(32), default="none", nullable=False
    )  # aruco, reference_object, none
    rule_version: Mapped[str] = mapped_column(String(64), default="LMPC-2011-v1.0", nullable=False)
    inspector_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    extracted_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product | None] = relationship("Product", back_populates="scans")
    inspector: Mapped[User | None] = relationship("User", back_populates="scans")
    compliance_results: Mapped[list["ComplianceResult"]] = relationship(
        "ComplianceResult", back_populates="scan", cascade="all, delete-orphan"
    )


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scans.id"), index=True, nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False
    )  # PASS, FAIL, REVIEW_REQUIRED
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    measured_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    violation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_version: Mapped[str] = mapped_column(String(64), default="LMPC-2011-v1.0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    scan: Mapped["Scan"] = relationship("Scan", back_populates="compliance_results")
