"""
Owner: ADITYA (with Parul's structured legal violation templates)

Evaluates compliance against LMPC Rules 2011 (loaded from lmpc_rules_v1.json).
Called from app/routers/scan.py AFTER Shubh's vision pipeline produces
extracted_fields + font_analysis + placement_checks.

Core Design Principles:
1. Single source of truth: Reads rules and violation messages from data (lmpc_rules_v1.json),
   not hardcoded Python strings.
2. Three-state compliance: PASS | FAIL | REVIEW_REQUIRED. If confidence < 0.75,
   result is routed to REVIEW_REQUIRED.
3. Plain-language, evidence-first reports: Each result includes a clear explanation
   and statutory rule reference for enforcement officers.
4. Capped Category Exceptions: Handles medical_device, bulk_exempt, and food_expiry.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict

from app.schemas.scan import (
    ExtractedField, FontAnalysis, PlacementCheck,
    ComplianceResult, FieldStatus,
)

RULES_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "lmpc_rules_v1.json"
CONFIDENCE_REVIEW_THRESHOLD = 0.75

_cached_rules = None


def load_rules() -> dict:
    """Loads and caches lmpc_rules_v1.json."""
    global _cached_rules
    if _cached_rules is None:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            _cached_rules = json.load(f)
    return _cached_rules


def reload_rules() -> dict:
    """Force reload rules from disk (useful in testing)."""
    global _cached_rules
    _cached_rules = None
    return load_rules()


def evaluate_compliance(
    extracted_fields: List[ExtractedField],
    font_analysis: Optional[FontAnalysis] = None,
    placement_checks: Optional[List[PlacementCheck]] = None,
    category: Optional[str] = None,
) -> List[ComplianceResult]:
    """
    Evaluates extracted packaging declarations, font measurements, and placement
    against statutory rules in lmpc_rules_v1.json.
    """
    rules = load_rules()
    rule_version = rules.get("version", "LMPC-2011-v1.1")
    templates = rules.get("violation_templates", {})
    results: List[ComplianceResult] = []

    # -------------------------------------------------------------------------
    # 1. Check Category Exceptions First (medical_device, bulk_exempt)
    # -------------------------------------------------------------------------
    norm_cat = (category or "").strip().lower()

    if norm_cat == "medical_device":
        med_tpl = templates.get("exceptions", {}).get("medical_device", {})
        results.append(ComplianceResult(
            rule_id="RULE_2_H_MEDICAL_DEVICE_EXEMPT",
            field_name="medical_device_exemption",
            status=FieldStatus.PASS,
            confidence=1.0,
            message=med_tpl.get("explanation", "Exempt from LMPC Rules 6/7; governed under Medical Devices Rules, 2017."),
            rule_version=rule_version,
        ))
        return results

    if norm_cat == "bulk_exempt":
        bulk_tpl = templates.get("exceptions", {}).get("bulk_exempt", {})
        results.append(ComplianceResult(
            rule_id="RULE_3_BULK_PACKAGE_EXEMPT",
            field_name="bulk_package_exemption",
            status=FieldStatus.PASS,
            confidence=1.0,
            message=bulk_tpl.get("explanation", "Exempt from retail declarations under Rule 3 as bulk/institutional package."),
            rule_version=rule_version,
        ))
        return results

    # -------------------------------------------------------------------------
    # 2. Rule 6 Mandatory Field Completeness Check
    # -------------------------------------------------------------------------
    extracted_by_name: Dict[str, ExtractedField] = {f.field_name: f for f in extracted_fields}
    field_templates = templates.get("fields", {})

    mandatory_fields_list = list(rules.get("mandatory_fields", []))

    # If food category, add expiry_date requirement (food_expiry exception)
    if norm_cat in ["food", "food_expiry"]:
        mandatory_fields_list.append({
            "field_name": "expiry_date",
            "display_name": "Best Before / Expiry Date",
            "rule_id": "RULE_6_1_D_FOOD_EXPIRY",
            "required": True,
            "description": "Best before or expiry date required for food products per Rule 6(1)(d) proviso / FSSAI.",
        })

    for field in mandatory_fields_list:
        name = field["field_name"]
        rule_id = field["rule_id"]
        is_required = field.get("required", True)

        field_obj = extracted_by_name.get(name)
        field_tpl = field_templates.get(name, {})

        if field_obj is None:
            if not is_required:
                continue  # Optional field (e.g. country_of_origin for domestic goods)

            missing_tpl = field_tpl.get("missing", {})
            msg = missing_tpl.get("explanation") or f"{field['display_name']} not detected on package."
            results.append(ComplianceResult(
                rule_id=rule_id,
                field_name=name,
                status=FieldStatus.FAIL,
                confidence=0.95,
                message=msg,
                rule_version=rule_version,
            ))
        else:
            # Field is present -> evaluate confidence against REVIEW threshold (0.75)
            if field_obj.confidence < CONFIDENCE_REVIEW_THRESHOLD:
                rev_tpl = field_tpl.get("review_required", {})
                raw_msg = rev_tpl.get("explanation") or f"{field['display_name']} detected with low visual confidence."
                msg = raw_msg.replace("{confidence:.2f}", f"{field_obj.confidence:.2f}")
                results.append(ComplianceResult(
                    rule_id=rule_id,
                    field_name=name,
                    status=FieldStatus.REVIEW_REQUIRED,
                    confidence=field_obj.confidence,
                    message=msg,
                    rule_version=rule_version,
                ))
            else:
                pass_tpl = field_tpl.get("pass", {})
                raw_msg = pass_tpl.get("explanation") or f"{field['display_name']} detected ({field_obj.normalized_value})."
                msg = raw_msg.replace("{normalized_value}", str(field_obj.normalized_value))
                results.append(ComplianceResult(
                    rule_id=rule_id,
                    field_name=name,
                    status=FieldStatus.PASS,
                    confidence=field_obj.confidence,
                    message=msg,
                    rule_version=rule_version,
                ))

    # -------------------------------------------------------------------------
    # 3. Rule 7 Font Height Verification
    # -------------------------------------------------------------------------
    def _format_font_msg(tpl_str: str, field_name: str, measured: float, required: float) -> str:
        msg = tpl_str.replace("{field_name}", field_name)
        msg = msg.replace("{measured_height_mm:.1f}", f"{measured:.1f}")
        msg = msg.replace("{measured_height_mm}", f"{measured:.1f}")
        msg = msg.replace("{measured_mm}", f"{measured:.1f}")
        msg = msg.replace("{required_height_mm:.1f}", f"{required:.1f}")
        msg = msg.replace("{required_height_mm}", f"{required:.1f}")
        msg = msg.replace("{required_mm}", f"{required:.1f}")
        return msg

    font_templates = templates.get("font_height", {})
    if font_analysis and font_analysis.fields:
        for fa in font_analysis.fields:
            if fa.status == FieldStatus.FAIL:
                tpl = font_templates.get("fail_below_threshold", {})
                raw_msg = tpl.get("explanation") or "Character height is below statutory minimum."
                msg = _format_font_msg(raw_msg, fa.field_name, fa.measured_height_mm, fa.required_height_mm)
                results.append(ComplianceResult(
                    rule_id="RULE_7_FONT_HEIGHT_FAIL",
                    field_name=fa.field_name,
                    status=FieldStatus.FAIL,
                    confidence=fa.calibration_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))
            elif fa.status == FieldStatus.REVIEW_REQUIRED:
                tpl = font_templates.get("review_required_calibration", {})
                raw_msg = tpl.get("explanation") or "Scale calibration confidence below review threshold."
                msg = raw_msg.replace("{confidence:.2f}", f"{fa.calibration_confidence:.2f}")
                results.append(ComplianceResult(
                    rule_id="RULE_7_FONT_HEIGHT_REVIEW",
                    field_name=fa.field_name,
                    status=FieldStatus.REVIEW_REQUIRED,
                    confidence=fa.calibration_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))
            else:
                tpl = font_templates.get("pass", {})
                raw_msg = tpl.get("explanation") or "Font height meets statutory requirements."
                msg = _format_font_msg(raw_msg, fa.field_name, fa.measured_height_mm, fa.required_height_mm)
                results.append(ComplianceResult(
                    rule_id="RULE_7_FONT_HEIGHT_PASS",
                    field_name=fa.field_name,
                    status=FieldStatus.PASS,
                    confidence=fa.calibration_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))

    # -------------------------------------------------------------------------
    # 4. Placement / Principal Display Panel Check (Rule 6 & Rule 8)
    # -------------------------------------------------------------------------
    placement_templates = templates.get("placement", {})
    if placement_checks:
        for pc in placement_checks:
            pc_confidence = getattr(pc, "confidence", 1.0)
            if pc_confidence < 0.75:
                tpl = placement_templates.get("review_required", {})
                raw_msg = (
                    tpl.get("explanation")
                    or f"Declaration '{pc.field_name}' placement detection confidence ({pc_confidence:.2f}) is below 0.75 threshold; physical verification required."
                )
                msg = raw_msg.replace("{field_name}", pc.field_name).replace("{confidence:.2f}", f"{pc_confidence:.2f}")
                results.append(ComplianceResult(
                    rule_id="RULE_6_PLACEMENT_REVIEW",
                    field_name=pc.field_name,
                    status=FieldStatus.REVIEW_REQUIRED,
                    confidence=pc_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))
            elif not pc.within_pdp:
                tpl = placement_templates.get("fail_outside_pdp", {})
                raw_msg = tpl.get("explanation") or f"Declaration {pc.field_name} located outside Principal Display Panel."
                msg = raw_msg.replace("{field_name}", pc.field_name)
                results.append(ComplianceResult(
                    rule_id="RULE_6_PLACEMENT_OUTSIDE_PDP",
                    field_name=pc.field_name,
                    status=FieldStatus.FAIL,
                    confidence=pc_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))
            else:
                tpl = placement_templates.get("pass", {})
                raw_msg = tpl.get("explanation") or f"Declaration {pc.field_name} correctly positioned within PDP."
                msg = raw_msg.replace("{field_name}", pc.field_name)
                results.append(ComplianceResult(
                    rule_id="RULE_6_PLACEMENT_PASS",
                    field_name=pc.field_name,
                    status=FieldStatus.PASS,
                    confidence=pc_confidence,
                    message=msg,
                    rule_version=rule_version,
                ))


    return results


def determine_overall_status(results: List[ComplianceResult]) -> FieldStatus:
    """
    Computes overall package status using three-state logic:
      - If ANY check is FAIL -> FAIL
      - Else if ANY check is REVIEW_REQUIRED -> REVIEW_REQUIRED
      - Else -> PASS
    """
    if any(r.status == FieldStatus.FAIL for r in results):
        return FieldStatus.FAIL
    if any(r.status == FieldStatus.REVIEW_REQUIRED for r in results):
        return FieldStatus.REVIEW_REQUIRED
    return FieldStatus.PASS
