"""Unit tests for compliance rule engine and statutory rules ingestion (Owner: Aditya).

Verifies:
1. Dynamic ingestion of Parul's rules JSON (lmpc_rules_v1.json).
2. Rule 6 completeness check with 3-state confidence routing (PASS, FAIL, REVIEW_REQUIRED).
3. Flexible input acceptance: dictionary or list format (waiting on Shubh's OCR format).
4. Category exceptions (medical_device, bulk_exempt, food_expiry).
5. Rule 7 font-height check (calibrated vs uncalibrated scale).
"""

import pytest

from app.schemas.compliance import ExtractedField
from app.schemas.enums import ComplianceStatus
from app.services.compliance.rule_engine import (
    evaluate_compliance,
    get_rule_version,
    load_lmpc_rules,
    reload_rules,
)


@pytest.fixture(autouse=True)
def fresh_rules():
    reload_rules()


def test_rule_json_ingestion():
    """Verify Parul's rules JSON is ingested dynamically with version stamp."""
    rules = load_lmpc_rules()
    assert rules is not None
    assert "version" in rules
    assert rules["version"].startswith("LMPC-2011")
    assert get_rule_version().startswith("LMPC-2011")
    assert "mandatory_fields" in rules or "rule_6_mandatory_declarations" in rules
    assert (
        "rule_7_font_height_specifications" in rules
        or "rule_7_font_height_tables" in rules
        or "rule_7_font_height_table_1" in rules
    )
    assert "category_exceptions" in rules


def test_rule_6_completeness_pass_dict():
    """Verify Rule 6 passes when all mandatory declarations are present (dict format)."""
    full_declarations = {
        "name_and_address": {"raw_text": "Mfd by ABC Foods Pvt Ltd, Mumbai", "confidence": 0.95},
        "country_of_origin": {"raw_text": "Country of Origin: India", "confidence": 0.95},
        "generic_name": {"raw_text": "Biscuits", "confidence": 0.92},
        "net_quantity": {"raw_text": "Net Wt: 200g", "confidence": 0.96},
        "mfg_or_packing_date": {"raw_text": "Pkd: 08/2026", "confidence": 0.90},
        "mrp": {"raw_text": "MRP Rs 50.00 (incl. of all taxes)", "confidence": 0.98},
        "consumer_care": {"raw_text": "Customer Care: care@abc.com 1800-111-222", "confidence": 0.94},
    }

    results = evaluate_compliance(
        extracted_fields=full_declarations,
        pdp_bbox=[50, 50, 400, 300],
        scale_factor_mm_per_px=0.08,
    )

    r6_res = next(r for r in results if r.rule_id == "RULE_6_MANDATORY_DECLARATIONS")
    assert r6_res.status == ComplianceStatus.PASS
    assert r6_res.violation_reason is None
    assert r6_res.measured_value is not None and "mandatory fields identified" in r6_res.measured_value


def test_rule_6_completeness_missing_fail():
    """Verify Rule 6 fails when mandatory fields are missing."""
    partial_declarations = {
        "mrp": {"raw_text": "MRP Rs 40.00", "confidence": 0.95},
        "net_quantity": {"raw_text": "Net Wt: 100g", "confidence": 0.95},
    }

    results = evaluate_compliance(extracted_fields=partial_declarations)
    r6_res = next(r for r in results if r.rule_id == "RULE_6_MANDATORY_DECLARATIONS")
    assert r6_res.status == ComplianceStatus.FAIL
    assert r6_res.violation_reason is not None and "Missing" in r6_res.violation_reason
    assert r6_res.measured_value is not None and "mandatory fields identified" in r6_res.measured_value


def test_rule_6_low_confidence_routes_to_review_required():
    """Verify Rule 6 routes to REVIEW_REQUIRED if any field confidence is below 0.75."""
    declarations_with_low_conf = {
        "name_and_address": {"raw_text": "Mfd by ABC Foods", "confidence": 0.95},
        "country_of_origin": {"raw_text": "Made in India", "confidence": 0.95},
        "generic_name": {"raw_text": "Biscuits", "confidence": 0.92},
        "net_quantity": {"raw_text": "Net Wt: 200g", "confidence": 0.55},  # Low confidence < 0.75
        "mfg_or_packing_date": {"raw_text": "Pkd: 08/2026", "confidence": 0.90},
        "mrp": {"raw_text": "MRP Rs 50.00", "confidence": 0.98},
        "consumer_care": {"raw_text": "Care: care@abc.com", "confidence": 0.94},
    }

    results = evaluate_compliance(extracted_fields=declarations_with_low_conf)
    r6_res = next(r for r in results if r.rule_id == "RULE_6_MANDATORY_DECLARATIONS")
    assert r6_res.status == ComplianceStatus.REVIEW_REQUIRED
    assert r6_res.violation_reason is not None and "review threshold" in r6_res.violation_reason.lower()


def test_flexible_input_list_format_shubh():
    """Verify rule engine accepts list of ExtractedField / dict objects (waiting on Shubh's OCR format)."""
    list_fields = [
        ExtractedField(field_name="mrp", raw_text="MRP Rs 50.00", normalized_value=50.0, unit="INR", confidence=0.96),
        {"field_name": "net_quantity", "raw_text": "100g", "confidence": 0.92},
        {"field_name": "generic_name", "raw_text": "Snack", "confidence": 0.91},
        {"field_name": "country_of_origin", "raw_text": "India", "confidence": 0.95},
        {"field_name": "name_and_address", "raw_text": "Mfd by XYZ", "confidence": 0.94},
        {"field_name": "mfg_or_packing_date", "raw_text": "01/2026", "confidence": 0.88},
        {"field_name": "consumer_care", "raw_text": "Call 1800-111", "confidence": 0.90},
    ]

    results = evaluate_compliance(extracted_fields=list_fields)
    r6_res = next(r for r in results if r.rule_id == "RULE_6_MANDATORY_DECLARATIONS")
    assert r6_res.status == ComplianceStatus.PASS


def test_category_exception_medical_device():
    """Verify medical_device category produces officer review annotation."""
    results = evaluate_compliance(extracted_fields={}, category="medical_device")
    med_res = next((r for r in results if r.rule_id == "CATEGORY_EXCEPTION_MEDICAL_DEVICE"), None)
    assert med_res is not None
    assert med_res.status == ComplianceStatus.REVIEW_REQUIRED
    assert med_res.expected_value is not None and "Drugs and Cosmetics Act" in med_res.expected_value


def test_category_exception_bulk_exempt():
    """Verify bulk_exempt category passes and exempts retail fields."""
    full_declarations = {
        "name_and_address": {"raw_text": "UltraTech Cement Ltd", "confidence": 0.95},
        "country_of_origin": {"raw_text": "India", "confidence": 0.95},
        "generic_name": {"raw_text": "Portland Cement", "confidence": 0.92},
        "net_quantity": {"raw_text": "50 kg", "confidence": 0.96},
        "mfg_or_packing_date": {"raw_text": "Pkd: 08/2026", "confidence": 0.90},
        # mrp and consumer_care are exempt
    }

    results = evaluate_compliance(extracted_fields=full_declarations, category="bulk_exempt")
    r6_res = next(r for r in results if r.rule_id == "RULE_6_MANDATORY_DECLARATIONS")
    assert r6_res.status == ComplianceStatus.PASS
    assert r6_res.measured_value is not None and "mandatory fields identified" in r6_res.measured_value

    bulk_res = next(r for r in results if r.rule_id == "CATEGORY_EXCEPTION_BULK_EXEMPT")
    assert bulk_res.status == ComplianceStatus.PASS


def test_category_exception_food_expiry():
    """Verify food_expiry category mandates expiry_date presence."""
    # 1. Without expiry_date -> fails food expiry check
    no_expiry = {
        "name_and_address": {"raw_text": "Food Corp", "confidence": 0.95},
        "generic_name": {"raw_text": "Bread", "confidence": 0.95},
        "net_quantity": {"raw_text": "400g", "confidence": 0.95},
    }
    res_no_exp = evaluate_compliance(extracted_fields=no_expiry, category="food_expiry")
    food_res = next(r for r in res_no_exp if r.rule_id == "CATEGORY_EXCEPTION_FOOD_EXPIRY")
    assert food_res.status == ComplianceStatus.FAIL

    # 2. With expiry_date -> passes food expiry check
    with_expiry = dict(no_expiry)
    with_expiry["expiry_date"] = {"raw_text": "Best Before 10 days from pkd", "confidence": 0.93}
    res_with_exp = evaluate_compliance(extracted_fields=with_expiry, category="food_expiry")
    food_res_pass = next(r for r in res_with_exp if r.rule_id == "CATEGORY_EXCEPTION_FOOD_EXPIRY")
    assert food_res_pass.status == ComplianceStatus.PASS


def test_rule_7_font_height_uncalibrated_review():
    """Verify lack of calibration routes font height to REVIEW_REQUIRED."""
    results = evaluate_compliance(extracted_fields={}, scale_factor_mm_per_px=None)
    f_res = next(r for r in results if r.rule_id == "RULE_7_FONT_HEIGHT")
    assert f_res.status == ComplianceStatus.REVIEW_REQUIRED
    assert f_res.confidence < 0.75
    assert f_res.violation_reason is not None and "calipers" in f_res.violation_reason
