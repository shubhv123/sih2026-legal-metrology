"""
Unit tests for compliance rule engine and violation-explanation templates.
Tests dynamic template loading from lmpc_rules_v1.json, confidence routing,
font-height checks, placement checks, and category exceptions.
"""

import pytest

from app.schemas.scan import (
    ExtractedField, FontAnalysis, FontAnalysisField,
    PlacementCheck, BoundingBox, FieldStatus, CalibrationMethod,
)
from app.services.compliance.rule_engine import (
    evaluate_compliance,
    determine_overall_status,
    load_rules,
    reload_rules,
)


@pytest.fixture(autouse=True)
def ensure_fresh_rules():
    reload_rules()


def test_rule_templates_loaded():
    """Verify that lmpc_rules_v1.json contains complete violation templates."""
    rules = load_rules()
    assert "violation_templates" in rules
    templates = rules["violation_templates"]

    assert "fields" in templates
    assert "mrp" in templates["fields"]
    assert "net_quantity" in templates["fields"]
    assert "mfg_date" in templates["fields"]
    assert "consumer_care" in templates["fields"]
    assert "manufacturer_name" in templates["fields"]

    mrp_tpl = templates["fields"]["mrp"]
    assert "missing" in mrp_tpl
    assert "explanation" in mrp_tpl["missing"]
    assert "Rule 6(1)(e)" in mrp_tpl["missing"]["legal_reference"]


def test_mandatory_field_missing_generates_statutory_fail():
    """Verify missing mandatory fields produce FAIL with statutory citation."""
    # Provide only MRP, omitting Net Qty, Mfg Date, Manufacturer, etc.
    extracted = [
        ExtractedField(
            field_name="mrp",
            raw_ocr_text="MRP Rs. 199.00",
            normalized_value="199.00",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=30),
        )
    ]

    results = evaluate_compliance(extracted_fields=extracted)
    results_by_field = {r.field_name: r for r in results}

    # Net quantity must fail
    assert "net_quantity" in results_by_field
    net_res = results_by_field["net_quantity"]
    assert net_res.status == FieldStatus.FAIL
    assert "net weight, measure" in net_res.message.lower()

    # Consumer care must fail
    assert "consumer_care" in results_by_field
    cc_res = results_by_field["consumer_care"]
    assert cc_res.status == FieldStatus.FAIL
    assert "consumer grievance" in cc_res.message.lower()

    # Overall status should be FAIL
    overall = determine_overall_status(results)
    assert overall == FieldStatus.FAIL


def test_low_confidence_routes_to_review_required():
    """Verify field with confidence < 0.75 routes to REVIEW_REQUIRED."""
    extracted = [
        ExtractedField(
            field_name="mrp",
            raw_ocr_text="MRP Rs. 149",
            normalized_value="149.00",
            confidence=0.55,  # Below 0.75 threshold
            bbox=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=30),
        )
    ]

    results = evaluate_compliance(extracted_fields=extracted)
    mrp_res = next(r for r in results if r.field_name == "mrp")

    assert mrp_res.status == FieldStatus.REVIEW_REQUIRED
    assert "faint" in mrp_res.message.lower() or "confidence" in mrp_res.message.lower()


def test_font_height_and_placement_checks():
    """Verify Rule 7 font-height and placement checks format template messages."""
    extracted = [
        ExtractedField(
            field_name="mrp",
            raw_ocr_text="MRP Rs. 149.00",
            normalized_value="149.00",
            confidence=0.95,
            bbox=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=30),
        )
    ]

    font_analysis = FontAnalysis(
        calibration_method=CalibrationMethod.ARUCO,
        mm_per_pixel=0.1,
        fields=[
            FontAnalysisField(
                field_name="mrp",
                measured_height_mm=1.2,
                required_height_mm=2.0,
                status=FieldStatus.FAIL,
                calibration_confidence=0.90,
            )
        ]
    )

    placement_checks = [
        PlacementCheck(
            field_name="mrp",
            within_pdp=False,  # Placed outside PDP
            confidence=0.88,
        )
    ]

    results = evaluate_compliance(
        extracted_fields=extracted,
        font_analysis=font_analysis,
        placement_checks=placement_checks,
    )

    # Check font failure
    font_res = next(r for r in results if r.rule_id == "RULE_7_FONT_HEIGHT_FAIL")
    assert font_res.status == FieldStatus.FAIL
    assert "1.2 mm" in font_res.message
    assert "2.0 mm" in font_res.message

    # Check placement failure
    placement_res = next(r for r in results if r.rule_id == "RULE_6_PLACEMENT_OUTSIDE_PDP")
    assert placement_res.status == FieldStatus.FAIL
    assert "secondary face" in placement_res.message.lower() or "principal display panel" in placement_res.message.lower()


def test_category_exceptions():
    """Verify medical_device and bulk_exempt category overrides."""
    # 1. Medical device
    med_res = evaluate_compliance(extracted_fields=[], category="medical_device")
    assert len(med_res) == 1
    assert med_res[0].status == FieldStatus.PASS
    assert "RULE_2_H_MEDICAL_DEVICE_EXEMPT" in med_res[0].rule_id
    assert "Medical Devices Rules, 2017" in med_res[0].message

    # 2. Bulk exempt
    bulk_res = evaluate_compliance(extracted_fields=[], category="bulk_exempt")
    assert len(bulk_res) == 1
    assert bulk_res[0].status == FieldStatus.PASS
    assert "RULE_3_BULK_PACKAGE_EXEMPT" in bulk_res[0].rule_id
    assert "Rule 3" in bulk_res[0].message

    # 3. Food expiry exception requires expiry_date
    food_res = evaluate_compliance(extracted_fields=[], category="food_expiry")
    food_field_names = [r.field_name for r in food_res]
    assert "expiry_date" in food_field_names
    expiry_item = next(r for r in food_res if r.field_name == "expiry_date")
    assert expiry_item.status == FieldStatus.FAIL
    assert "best before" in expiry_item.message.lower() or "expiry" in expiry_item.message.lower()


def test_template_legal_citations_and_advisory_tone():
    """Verify honest country_of_origin caveat, Rule 32(2) citation, and advisory action language."""
    rules = load_rules()
    templates = rules["violation_templates"]

    # 1. country_of_origin carries honest secondary caveat, not flat Rule 6(1)(a)
    origin_tpl = templates["fields"]["country_of_origin"]
    assert "amended" in origin_tpl["missing"]["legal_reference"].lower()
    assert "pending" in origin_tpl["missing"]["legal_reference"].lower() or "secondary" in origin_tpl["missing"]["legal_reference"].lower()

    # 2. font height citation specifies Rule 32(2) specifically, not bare Rule 32
    font_tpl = templates["font_height"]["fail_below_threshold"]
    assert "Rule 32(2)" in font_tpl["legal_reference"]
    assert "Rule 32(2)" in font_tpl["recommended_action"]

    # 3. Recommended actions use advisory tone ('Recommend...'), not directives ('Issue notice...')
    for field_name, tpl_group in templates["fields"].items():
        if "missing" in tpl_group:
            action = tpl_group["missing"]["recommended_action"]
            assert action.startswith("Recommend") or "recommend" in action.lower(), (
                f"Field {field_name} missing action should be advisory, got: {action}"
            )
        if "review_required" in tpl_group:
            action = tpl_group["review_required"]["recommended_action"]
            assert "recommend" in action.lower() or "advis" in action.lower() or "inspection" in action.lower(), (
                f"Field {field_name} review action should be advisory, got: {action}"
            )

    # 4. PASS templates provide informative, affirmative explanations
    for field_name, tpl_group in templates["fields"].items():
        pass_tpl = tpl_group["pass"]
        assert len(pass_tpl["explanation"]) > 25, f"PASS explanation too brief for {field_name}"
        assert "{normalized_value}" in pass_tpl["explanation"], f"PASS template should reference value for {field_name}"


def test_placement_confidence_symmetric_gating():
    """
    Priority 2 Test: Symmetrical confidence gating for placement checks.
    Both within_pdp=True AND within_pdp=False must route to REVIEW_REQUIRED
    when detection confidence < 0.75, ensuring low-confidence assertions
    are never stated as definitive PASS or FAIL.
    """
    # 1. within_pdp=True with confidence < 0.75 -> REVIEW_REQUIRED
    pc_true_low = [
        PlacementCheck(
            field_name="generic_name",
            within_pdp=True,
            confidence=0.55,
        )
    ]
    res_true = evaluate_compliance(extracted_fields=[], placement_checks=pc_true_low)
    p_res1 = next(r for r in res_true if r.rule_id == "RULE_6_PLACEMENT_REVIEW")
    assert p_res1.status == FieldStatus.REVIEW_REQUIRED
    assert p_res1.confidence == 0.55

    # 2. within_pdp=False with confidence < 0.75 -> REVIEW_REQUIRED (symmetric!)
    pc_false_low = [
        PlacementCheck(
            field_name="generic_name",
            within_pdp=False,
            confidence=0.55,
        )
    ]
    res_false = evaluate_compliance(extracted_fields=[], placement_checks=pc_false_low)
    p_res2 = next(r for r in res_false if r.rule_id == "RULE_6_PLACEMENT_REVIEW")
    assert p_res2.status == FieldStatus.REVIEW_REQUIRED
    assert p_res2.confidence == 0.55

    # 3. High confidence >= 0.75 produces definitive statuses
    pc_high_pass = [
        PlacementCheck(
            field_name="generic_name",
            within_pdp=True,
            confidence=0.85,
        )
    ]
    res_high_pass = evaluate_compliance(extracted_fields=[], placement_checks=pc_high_pass)
    assert any(r.rule_id == "RULE_6_PLACEMENT_PASS" and r.status == FieldStatus.PASS for r in res_high_pass)

    pc_high_fail = [
        PlacementCheck(
            field_name="generic_name",
            within_pdp=False,
            confidence=0.85,
        )
    ]
    res_high_fail = evaluate_compliance(extracted_fields=[], placement_checks=pc_high_fail)
    assert any(r.rule_id == "RULE_6_PLACEMENT_OUTSIDE_PDP" and r.status == FieldStatus.FAIL for r in res_high_fail)


