import json
from datetime import UTC, datetime, timedelta

from app.core.security import hash_password
from app.db.base import Base
from app.db.models import ComplianceResult, Product, Scan, User
from app.db.session import SessionLocal, engine, init_db


def seed_database(force_reseed: bool = False) -> None:
    init_db()
    db = SessionLocal()
    try:
        # Check if users already seeded
        if db.query(User).count() > 0 and not force_reseed:
            print("Database already contains records. Skipping seed.")
            return

        if force_reseed:
            print("Resetting database schema for re-seed...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

        print("Seeding demo users (Inspector & Admin)...")
        inspector = User(
            username="inspector",
            hashed_password=hash_password("inspector123"),
            role="inspector",
            full_name="Field Officer Sharma",
            is_active=True,
        )
        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            role="admin",
            full_name="Enforcement Director Verma",
            is_active=True,
        )
        db.add_all([inspector, admin])
        db.commit()
        db.refresh(inspector)
        db.refresh(admin)

        print("Seeding comprehensive dummy products and scans...")

        # ----------------------------------------------------------------------
        # 1. PASS - Sunfeast Dark Fantasy (Standard Retail Food)
        # ----------------------------------------------------------------------
        p1 = Product(
            product_name="Sunfeast Dark Fantasy Choco Fills",
            brand_name="Sunfeast",
            category="food_expiry",
            net_quantity_declared="75 g",
            mrp_declared=40.0,
            country_of_origin="India",
            manufacturer_details="ITC Limited, Virginia House, 37 J.L. Nehru Road, Kolkata 700071",
            mfg_date="01/2026",
            expiry_date="07/2026",
            consumer_care="1800-425-4444 / itccares@itc.in",
        )
        db.add(p1)
        db.commit()
        db.refresh(p1)

        s1_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        s1 = Scan(
            id=s1_id,
            product_id=p1.id,
            original_image_path="/static/uploads/sample_dark_fantasy.jpg",
            evidence_image_path="/static/uploads/sample_dark_fantasy_annotated.jpg",
            overall_status="PASS",
            overall_confidence=0.94,
            calibrated_scale_factor=0.082,
            calibration_method="aruco",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {
                    "mrp": {
                        "raw_text": "MRP Rs 40.00 (incl. of all taxes)",
                        "normalized_value": 40.0,
                        "unit": "INR",
                        "confidence": 0.96,
                        "bounding_box": [120, 45, 150, 280],
                    },
                    "net_quantity": {
                        "raw_text": "Net Weight: 75 g",
                        "normalized_value": 75.0,
                        "unit": "g",
                        "confidence": 0.95,
                        "bounding_box": [160, 45, 185, 210],
                    },
                    "mfg_date": {
                        "raw_text": "Mfg: 01/26",
                        "normalized_value": "2026-01-01",
                        "confidence": 0.92,
                        "bounding_box": [190, 45, 210, 160],
                    },
                    "expiry_date": {
                        "raw_text": "Best Before 6 Months",
                        "normalized_value": "6 Months",
                        "confidence": 0.89,
                        "bounding_box": [215, 45, 235, 270],
                    },
                    "manufacturer": {
                        "raw_text": "Mfd by: ITC Limited, Virginia House, Kolkata 700071",
                        "normalized_value": "ITC Limited, Kolkata",
                        "confidence": 0.91,
                        "bounding_box": [240, 45, 280, 520],
                    },
                    "consumer_care": {
                        "raw_text": "Consumer Care: 1800-425-4444",
                        "normalized_value": "1800-425-4444",
                        "confidence": 0.93,
                        "bounding_box": [285, 45, 310, 480],
                    },
                }
            ),
            notes="Full Rule 6 and Rule 7 Table-I compliance verified.",
            created_at=datetime.now(UTC) - timedelta(hours=6),
        )
        db.add(s1)
        db.commit()

        db.add_all(
            [
                ComplianceResult(
                    scan_id=s1_id,
                    rule_id="RULE_6_MANDATORY_DECLARATIONS",
                    rule_name="Mandatory Declarations Completeness",
                    field_name="all_mandatory_fields",
                    status="PASS",
                    confidence=0.94,
                    measured_value="6/6 mandatory fields identified",
                    expected_value="All Rule 6 declarations present",
                    violation_reason=None,
                    rule_version="LMPC-2011-v1.0",
                ),
                ComplianceResult(
                    scan_id=s1_id,
                    rule_id="RULE_6_PANEL_PLACEMENT",
                    rule_name="Principal Display Panel Grouping",
                    field_name="pdp_grouping",
                    status="PASS",
                    confidence=0.91,
                    measured_value="100% fields enclosed within PDP boundary",
                    expected_value="All mandatory declarations on Principal Display Panel",
                    violation_reason=None,
                    rule_version="LMPC-2011-v1.0",
                ),
                ComplianceResult(
                    scan_id=s1_id,
                    rule_id="RULE_7_FONT_HEIGHT",
                    rule_name="Minimum Character Height",
                    field_name="net_quantity_numeral",
                    status="PASS",
                    confidence=0.88,
                    measured_value="3.2 mm",
                    expected_value="Min 2.0 mm for net weight 50g-100g (Table-I)",
                    violation_reason=None,
                    rule_version="LMPC-2011-v1.0",
                ),
            ]
        )

        # ----------------------------------------------------------------------
        # 2. FAIL - Maggi Masala Noodles (Font Height & Missing Consumer Care)
        # ----------------------------------------------------------------------
        p2 = Product(
            product_name="Maggi 2-Minute Masala Noodles",
            brand_name="Nestle",
            category="food_expiry",
            net_quantity_declared="70 g",
            mrp_declared=14.0,
            country_of_origin="India",
            manufacturer_details="Nestle India Ltd, 100/101 World Trade Centre, New Delhi",
            mfg_date="02/2026",
            expiry_date="11/2026",
            consumer_care=None,
        )
        db.add(p2)
        db.commit()
        db.refresh(p2)

        s2_id = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
        s2 = Scan(
            id=s2_id,
            product_id=p2.id,
            original_image_path="/static/uploads/sample_maggi.jpg",
            evidence_image_path="/static/uploads/sample_maggi_annotated.jpg",
            overall_status="FAIL",
            overall_confidence=0.89,
            calibrated_scale_factor=0.076,
            calibration_method="reference_object",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {
                    "mrp": {
                        "raw_text": "MRP Rs 14",
                        "normalized_value": 14.0,
                        "unit": "INR",
                        "confidence": 0.94,
                        "bounding_box": [110, 40, 130, 210],
                    },
                    "net_quantity": {
                        "raw_text": "Net Weight 70g",
                        "normalized_value": 70.0,
                        "unit": "g",
                        "confidence": 0.92,
                        "bounding_box": [140, 40, 155, 180],
                    },
                }
            ),
            notes="Violation: Numeral font height below Table-I minimum statutory requirement.",
            created_at=datetime.now(UTC) - timedelta(hours=4),
        )
        db.add(s2)
        db.commit()

        db.add_all(
            [
                ComplianceResult(
                    scan_id=s2_id,
                    rule_id="RULE_7_FONT_HEIGHT",
                    rule_name="Minimum Character Height",
                    field_name="net_quantity_numeral",
                    status="FAIL",
                    confidence=0.89,
                    measured_value="1.3 mm",
                    expected_value="Min 2.0 mm for net weight 50g-200g (Table-I)",
                    violation_reason="Numeral height (1.3 mm) is below statutory 2.0 mm threshold under Rule 7 Table-I.",
                    rule_version="LMPC-2011-v1.0",
                ),
                ComplianceResult(
                    scan_id=s2_id,
                    rule_id="RULE_6_MANDATORY_DECLARATIONS",
                    rule_name="Mandatory Declarations Completeness",
                    field_name="consumer_care",
                    status="FAIL",
                    confidence=0.86,
                    measured_value="Missing",
                    expected_value="Toll-free number or customer care email under Rule 6(1)(e)",
                    violation_reason="No consumer care telephone or email found on package label.",
                    rule_version="LMPC-2011-v1.0",
                ),
            ]
        )

        # ----------------------------------------------------------------------
        # 3. REVIEW_REQUIRED - Savlon Antiseptic (Medical Device Exemption Proviso)
        # ----------------------------------------------------------------------
        p3 = Product(
            product_name="Savlon Antiseptic Liquid 500ml",
            brand_name="Savlon",
            category="medical_device",
            net_quantity_declared="500 ml",
            mrp_declared=135.0,
            country_of_origin="India",
            manufacturer_details="ITC Ltd, Quality Care Division, Manpura, Baddi",
            mfg_date="12/2025",
            expiry_date="11/2027",
            consumer_care="1800-425-4444",
        )
        db.add(p3)
        db.commit()
        db.refresh(p3)

        s3_id = "c3d4e5f6-a7b8-9012-cdef-123456789012"
        s3 = Scan(
            id=s3_id,
            product_id=p3.id,
            original_image_path="/static/uploads/sample_savlon.jpg",
            evidence_image_path="/static/uploads/sample_savlon_annotated.jpg",
            overall_status="REVIEW_REQUIRED",
            overall_confidence=0.68,
            calibrated_scale_factor=None,
            calibration_method="none",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {"generic_name": {"raw_text": "Antiseptic Liquid", "confidence": 0.71}}
            ),
            notes="Scale reference missing; category exception 'medical_device' detected. Routed to Review Required.",
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db.add(s3)
        db.commit()

        db.add_all(
            [
                ComplianceResult(
                    scan_id=s3_id,
                    rule_id="RULE_7_FONT_HEIGHT",
                    rule_name="Minimum Character Height",
                    field_name="font_height_calibration",
                    status="REVIEW_REQUIRED",
                    confidence=0.60,
                    measured_value="Uncalibrated",
                    expected_value="Valid ArUco tag or known reference object for mm scale",
                    violation_reason="No calibration reference detected in frame; physical font size cannot be determined reliably.",
                    rule_version="LMPC-2011-v1.0",
                ),
                ComplianceResult(
                    scan_id=s3_id,
                    rule_id="CATEGORY_EXCEPTION_MEDICAL_DEVICE",
                    rule_name="Medical Device Statutory Exemption",
                    field_name="medical_device_proviso",
                    status="REVIEW_REQUIRED",
                    confidence=0.72,
                    measured_value="Medical Device Proviso (23 Oct 2025) potentially applicable",
                    expected_value="Officer verification of Drugs and Cosmetics Act license",
                    violation_reason="Product appears to be a medical antiseptic subject to Medical Devices Rules 2017 exemption.",
                    rule_version="LMPC-2011-v1.0",
                ),
            ]
        )

        # ----------------------------------------------------------------------
        # 4. PASS - Tata Salt 1kg (Standard Retail Food)
        # ----------------------------------------------------------------------
        p4 = Product(
            product_name="Tata Salt Vacuum Evaporated Iodised Salt",
            brand_name="Tata",
            category="standard_retail",
            net_quantity_declared="1 kg",
            mrp_declared=28.0,
            country_of_origin="India",
            manufacturer_details="Tata Consumer Products Ltd, Mumbai 400001",
            mfg_date="03/2026",
            expiry_date="02/2028",
            consumer_care="1800-345-1720 / customercare@tataconsumer.com",
        )
        db.add(p4)
        db.commit()
        db.refresh(p4)

        s4_id = "d4e5f6a7-b8c9-0123-defa-234567890123"
        s4 = Scan(
            id=s4_id,
            product_id=p4.id,
            original_image_path="/static/uploads/sample_tata_salt.jpg",
            evidence_image_path="/static/uploads/sample_tata_salt_annotated.jpg",
            overall_status="PASS",
            overall_confidence=0.96,
            calibrated_scale_factor=0.080,
            calibration_method="aruco",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {
                    "mrp": {
                        "raw_text": "MRP Rs 28.00 (incl. of all taxes)",
                        "normalized_value": 28.0,
                        "unit": "INR",
                        "confidence": 0.97,
                    },
                    "net_quantity": {
                        "raw_text": "Net Weight: 1 kg",
                        "normalized_value": 1.0,
                        "unit": "kg",
                        "confidence": 0.98,
                    },
                }
            ),
            notes="All mandatory declarations and Table-I font dimensions conform to standard.",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db.add(s4)
        db.commit()

        db.add(
            ComplianceResult(
                scan_id=s4_id,
                rule_id="RULE_6_MANDATORY_DECLARATIONS",
                rule_name="Mandatory Declarations Completeness",
                field_name="all_mandatory_fields",
                status="PASS",
                confidence=0.96,
                measured_value="6/6 mandatory fields identified",
                expected_value="All Rule 6 declarations present",
                violation_reason=None,
                rule_version="LMPC-2011-v1.0",
            )
        )

        # ----------------------------------------------------------------------
        # 5. PASS - UltraTech Cement 50kg (Category Exception: Bulk Exempt)
        # ----------------------------------------------------------------------
        p5 = Product(
            product_name="UltraTech Super Cement 50kg Bag",
            brand_name="UltraTech",
            category="bulk_exempt",
            net_quantity_declared="50 kg",
            mrp_declared=None,
            country_of_origin="India",
            manufacturer_details="UltraTech Cement Ltd, Ahura Centre, Mahakali Caves Road, Andheri East, Mumbai",
            mfg_date="02/2026",
            expiry_date=None,
            consumer_care=None,
        )
        db.add(p5)
        db.commit()
        db.refresh(p5)

        s5_id = "e5f6a7b8-c9d0-1234-efab-345678901234"
        s5 = Scan(
            id=s5_id,
            product_id=p5.id,
            original_image_path="/static/uploads/sample_cement.jpg",
            evidence_image_path="/static/uploads/sample_cement_annotated.jpg",
            overall_status="PASS",
            overall_confidence=0.93,
            calibrated_scale_factor=0.085,
            calibration_method="aruco",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {
                    "net_quantity": {
                        "raw_text": "Net Weight 50 kg",
                        "normalized_value": 50.0,
                        "unit": "kg",
                        "confidence": 0.95,
                    }
                }
            ),
            notes="Institutional package exceeding 25kg. Rule 3 & 26 bulk packaging exemption applies cleanly.",
            created_at=datetime.now(UTC) - timedelta(minutes=45),
        )
        db.add(s5)
        db.commit()

        db.add(
            ComplianceResult(
                scan_id=s5_id,
                rule_id="CATEGORY_EXCEPTION_BULK_EXEMPT",
                rule_name="Bulk Institutional Exemption",
                field_name="bulk_package_threshold",
                status="PASS",
                confidence=0.93,
                measured_value="Net Weight 50 kg (> 25 kg threshold)",
                expected_value="Rule 3 & 26 industrial consumer exemption criteria met",
                violation_reason=None,
                rule_version="LMPC-2011-v1.0",
            )
        )

        # ----------------------------------------------------------------------
        # 6. FAIL - Britannia Good Day (Placement Violation: MRP outside PDP)
        # ----------------------------------------------------------------------
        p6 = Product(
            product_name="Britannia Good Day Butter Cookies",
            brand_name="Britannia",
            category="food_expiry",
            net_quantity_declared="100 g",
            mrp_declared=30.0,
            country_of_origin="India",
            manufacturer_details="Britannia Industries Limited, Prestige Shantiniketan, Bengaluru",
            mfg_date="01/2026",
            expiry_date="07/2026",
            consumer_care="1800-425-4449",
        )
        db.add(p6)
        db.commit()
        db.refresh(p6)

        s6_id = "f6a7b8c9-d0e1-2345-fabc-456789012345"
        s6 = Scan(
            id=s6_id,
            product_id=p6.id,
            original_image_path="/static/uploads/sample_good_day.jpg",
            evidence_image_path="/static/uploads/sample_good_day_annotated.jpg",
            overall_status="FAIL",
            overall_confidence=0.87,
            calibrated_scale_factor=0.078,
            calibration_method="aruco",
            rule_version="LMPC-2011-v1.0",
            inspector_id=inspector.id,
            extracted_fields_json=json.dumps(
                {
                    "mrp": {
                        "raw_text": "MRP Rs 30.00",
                        "confidence": 0.91,
                        "bounding_box": [720, 50, 750, 200],
                    },
                    "net_quantity": {
                        "raw_text": "100g",
                        "confidence": 0.94,
                        "bounding_box": [150, 60, 175, 180],
                    },
                }
            ),
            notes="Placement violation: MRP printed on side fold instead of Principal Display Panel.",
            created_at=datetime.now(UTC) - timedelta(minutes=15),
        )
        db.add(s6)
        db.commit()

        db.add(
            ComplianceResult(
                scan_id=s6_id,
                rule_id="RULE_6_PANEL_PLACEMENT",
                rule_name="Principal Display Panel Grouping",
                field_name="mrp_placement",
                status="FAIL",
                confidence=0.87,
                measured_value="MRP located outside detected PDP region (offset: 220px)",
                expected_value="MRP declaration grouped on Principal Display Panel per Rule 6(1)",
                violation_reason="MRP is printed on package side fold, violating Rule 6 mandatory grouping on the Principal Display Panel.",
                rule_version="LMPC-2011-v1.0",
            )
        )

        db.commit()
        print("Successfully seeded 6 diverse products with scans and compliance results!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force_reseed=True)
