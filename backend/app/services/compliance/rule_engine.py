"""
Owner: ADITYA

This is called from app/routers/scan.py AFTER Shubh's extraction
pipeline produces extracted_fields + font_analysis + placement_checks.
Rule engine does NOT touch images/OCR - pure logic over structured data.

TODO(aditya):
 1. Load rules from app/data/rules/lmpc_rules_v1.json (Parul's structured
    rules) instead of hardcoding below.
 2. For each required field in the rules config, check:
    - is it present in extracted_fields? (Rule 6 completeness)
    - is its font height within threshold? (pull from font_analysis)
    - is it within the PDP? (pull from placement_checks)
 3. Map confidence -> PASS / FAIL / REVIEW_REQUIRED using a threshold
    (e.g. confidence < 0.75 -> REVIEW_REQUIRED even if the check itself
    would otherwise PASS/FAIL)
 4. Apply category exceptions (medical device / bulk / food-expiry -
    capped at these 3, per plan) before final result.
"""

import json
from pathlib import Path
from typing import List

from app.schemas.scan import (
    ExtractedField, FontAnalysis, PlacementCheck,
    ComplianceResult, FieldStatus,
)

RULES_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "lmpc_rules_v1.json"
CONFIDENCE_REVIEW_THRESHOLD = 0.75


def load_rules() -> dict:
    with open(RULES_PATH) as f:
        return json.load(f)


def evaluate_compliance(
    extracted_fields: List[ExtractedField],
    font_analysis: FontAnalysis,
    placement_checks: List[PlacementCheck],
) -> List[ComplianceResult]:
    """
    MOCK IMPLEMENTATION - returns a single hardcoded result.
    Replace with real rule evaluation against load_rules().
    """
    rules = load_rules()
    rule_version = rules.get("version", "LMPC-2011-v1.0")

    results: List[ComplianceResult] = []
    extracted_names = {f.field_name for f in extracted_fields}

    for field in rules.get("mandatory_fields", []):
        name = field["field_name"]
        present = name in extracted_names

        if not present:
            status = FieldStatus.FAIL
            message = f"{field['display_name']} not detected on package."
        else:
            status = FieldStatus.PASS
            message = f"{field['display_name']} detected and appears valid."

        results.append(ComplianceResult(
            rule_id=field["rule_id"],
            field_name=name,
            status=status,
            confidence=0.9 if present else 0.95,
            message=message,
            rule_version=rule_version,
        ))

    return results


def determine_overall_status(results: List[ComplianceResult]) -> FieldStatus:
    if any(r.status == FieldStatus.FAIL for r in results):
        return FieldStatus.FAIL
    if any(r.status == FieldStatus.REVIEW_REQUIRED for r in results):
        return FieldStatus.REVIEW_REQUIRED
    return FieldStatus.PASS
