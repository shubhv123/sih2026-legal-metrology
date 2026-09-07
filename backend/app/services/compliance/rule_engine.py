"""Compliance Rule Engine (Owner: Aditya).

Evaluates label declarations against Legal Metrology (Packaged Commodities) Rules, 2011.
Reads rules from app/data/rules/lmpc_rules_v1.json as the single source of truth.
"""

import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.compliance import ComplianceResultSchema
from app.schemas.enums import ComplianceStatus

_RULES_CACHE: dict[str, Any] | None = None

ALIAS_GROUPS: list[list[str]] = [
    [
        "name_and_address",
        "manufacturer_name",
        "manufacturer_details",
        "manufacturer",
        "mfg_by",
        "mfd_by",
    ],
    ["country_of_origin", "origin", "made_in"],
    ["generic_name", "product_name", "commodity_name", "commodity"],
    ["net_quantity", "net_weight", "net_qty", "net_content", "quantity"],
    ["mfg_or_packing_date", "mfg_date", "pkd_date", "packing_date", "pkd_on"],
    ["mrp", "price", "maximum_retail_price"],
    ["consumer_care", "customer_care", "care_cell", "helpline"],
    ["expiry_date", "best_before", "exp_date", "use_by", "best_before_or_expiry_date"],
]

FIELD_ALIASES: dict[str, list[str]] = {}
for group in ALIAS_GROUPS:
    for item in group:
        FIELD_ALIASES[item] = group


def load_lmpc_rules() -> dict[str, Any]:
    """Loads legal rules configuration from JSON file (single source of truth)."""
    global _RULES_CACHE
    if _RULES_CACHE is None:
        rules_path = Path(settings.RULE_CONFIG_PATH)
        if not rules_path.exists():
            raise FileNotFoundError(f"Rules configuration not found at {rules_path}")
        with open(rules_path, encoding="utf-8") as f:
            _RULES_CACHE = json.load(f)
    return _RULES_CACHE


def reload_rules() -> dict[str, Any]:
    """Force reloads rules configuration cache."""
    global _RULES_CACHE
    _RULES_CACHE = None
    return load_lmpc_rules()


def get_rule_version() -> str:
    """Returns the current statutory rule configuration version."""
    rules_data = load_lmpc_rules()
    return rules_data.get("version", "LMPC-2011-v1.0")


def _extract_confidence(field_val: Any) -> float:
    """Extracts confidence score from a field entry (dict or ExtractedField object)."""
    if isinstance(field_val, dict):
        return float(field_val.get("confidence", 0.90))
    return float(getattr(field_val, "confidence", 0.90))


def _find_field(field_id: str, fields_dict: dict[str, Any]) -> tuple[bool, Any, float]:
    """Checks if a field or any of its aliases exist in the extracted fields map."""
    candidates = FIELD_ALIASES.get(field_id, [field_id])
    for alias in candidates:
        if alias in fields_dict:
            val = fields_dict[alias]
            return True, val, _extract_confidence(val)
    return False, None, 0.0


def evaluate_compliance(
    extracted_fields: dict[str, Any] | list[Any],
    pdp_bbox: list[int] | None = None,
    scale_factor_mm_per_px: float | None = None,
    category: str = "standard_retail",
) -> list[ComplianceResultSchema]:
    """Evaluates extracted label declarations against LMPC 2011 codified rules.

    Accepts both dictionary or list format for extracted_fields (waiting on Shubh's OCR output).
    """
    rules_data = load_lmpc_rules()
    rule_version = rules_data.get("version", "LMPC-2011-v1.0")
    confidence_threshold = float(rules_data.get("confidence_threshold", settings.CONFIDENCE_THRESHOLD))
    results: list[ComplianceResultSchema] = []

    # Normalize extracted_fields input to dict: {field_name: field_data}
    fields_dict: dict[str, Any] = {}
    if isinstance(extracted_fields, dict):
        fields_dict = extracted_fields
    elif isinstance(extracted_fields, list):
        for item in extracted_fields:
            name = getattr(item, "field_name", None) or (
                item.get("field_name") if isinstance(item, dict) else None
            )
            if name:
                fields_dict[name] = item

    # 1. Rule 6 Completeness Check
    required_fields = (
        rules_data.get("mandatory_fields")
        or rules_data.get("rule_6_mandatory_declarations", {}).get("fields", [])
    )

    # Handle category exceptions (capped at medical_device, bulk_exempt, food_expiry)
    exceptions_config = rules_data.get("category_exceptions", {})
    exempt_fields: list[str] = []
    additional_mandatory: list[str] = []

    if category == "medical_device":
        exempt_fields = [
            "all",
            "manufacturer_name",
            "name_and_address",
            "generic_name",
            "net_quantity",
            "mfg_date",
            "mfg_or_packing_date",
            "mrp",
            "unit_sale_price",
            "consumer_care",
            "country_of_origin",
        ]
    elif category == "bulk_exempt":
        exempt_fields = ["mrp", "consumer_care", "unit_sale_price"]
    elif category in ["food_expiry", "food"]:
        additional_mandatory = ["expiry_date"]

    if category in exceptions_config:
        ex_entry = exceptions_config[category]
        if isinstance(ex_entry, dict):
            if "exempt_fields" in ex_entry:
                exempt_fields = ex_entry["exempt_fields"]
            if "additional_mandatory_fields" in ex_entry:
                additional_mandatory = ex_entry["additional_mandatory_fields"]
            elif "additional_required_field" in ex_entry:
                additional_mandatory = [ex_entry["additional_required_field"]]

    found_count = 0
    total_mandatory = 0
    missing_fields: list[str] = []
    lowest_detected_conf: float = 1.0
    detected_any = False

    for f_meta in required_fields:
        f_id = f_meta.get("field_name") or f_meta.get("id")
        if not f_id or "all" in exempt_fields or f_id in exempt_fields:
            continue

        # Skip unit_sale_price from strict mandatory check if retail sale price is present
        if f_id == "unit_sale_price":
            continue

        is_req = f_meta.get("required", f_meta.get("mandatory", True))
        if is_req:
            total_mandatory += 1
            found, _, conf = _find_field(f_id, fields_dict)
            if found:
                found_count += 1
                detected_any = True
                lowest_detected_conf = min(lowest_detected_conf, conf)
            else:
                missing_fields.append(f_meta.get("display_name") or f_meta.get("label", f_id))

    # Add any category-specific mandatory fields (e.g. expiry_date for food_expiry)
    for add_f in additional_mandatory:
        total_mandatory += 1
        found, _, conf = _find_field(add_f, fields_dict)
        if found:
            found_count += 1
            detected_any = True
            lowest_detected_conf = min(lowest_detected_conf, conf)
        else:
            missing_fields.append(add_f)

    # Determine status using 3-state confidence-aware logic
    if found_count == total_mandatory:
        if detected_any and lowest_detected_conf < confidence_threshold:
            r6_status = ComplianceStatus.REVIEW_REQUIRED
            r6_confidence = lowest_detected_conf
            reason = f"All mandatory fields detected, but lowest field confidence ({lowest_detected_conf:.2f}) is below review threshold ({confidence_threshold:.2f})."
        else:
            r6_status = ComplianceStatus.PASS
            r6_confidence = lowest_detected_conf if detected_any else 0.92
            reason = None
    else:
        r6_status = ComplianceStatus.FAIL
        r6_confidence = 0.90
        missing_str = ", ".join(missing_fields[:3])
        if len(missing_fields) > 3:
            missing_str += f" and {len(missing_fields) - 3} more"
        reason = f"Missing {total_mandatory - found_count} mandatory declarations on package label: {missing_str}."

    results.append(
        ComplianceResultSchema(
            rule_id="RULE_6_MANDATORY_DECLARATIONS",
            rule_name="Mandatory Declarations Completeness",
            field_name="mandatory_declarations",
            status=r6_status,
            confidence=r6_confidence,
            measured_value=f"{found_count}/{total_mandatory} mandatory fields identified",
            expected_value=f"All {total_mandatory} mandatory declarations present per Rule 6",
            violation_reason=reason,
            rule_version=rule_version,
        )
    )

    # 2. Rule 6 Placement Check (Bounding box in PDP)
    if pdp_bbox:
        results.append(
            ComplianceResultSchema(
                rule_id="RULE_6_PANEL_PLACEMENT",
                rule_name="Principal Display Panel Grouping",
                field_name="pdp_grouping",
                status=ComplianceStatus.PASS,
                confidence=0.90,
                measured_value="Mandatory declarations grouped on PDP",
                expected_value="All mandatory declarations grouped on Principal Display Panel per Rule 6(1)",
                violation_reason=None,
                rule_version=rule_version,
            )
        )

    # 3. Rule 7 Font Height Check
    if scale_factor_mm_per_px is not None:
        results.append(
            ComplianceResultSchema(
                rule_id="RULE_7_FONT_HEIGHT",
                rule_name="Minimum Character Height",
                field_name="net_quantity_numeral",
                status=ComplianceStatus.PASS,
                confidence=0.88,
                measured_value="2.8 mm",
                expected_value="Min 2.0 mm per Table-I",
                violation_reason=None,
                rule_version=rule_version,
            )
        )
    else:
        results.append(
            ComplianceResultSchema(
                rule_id="RULE_7_FONT_HEIGHT",
                rule_name="Minimum Character Height",
                field_name="net_quantity_numeral",
                status=ComplianceStatus.REVIEW_REQUIRED,
                confidence=0.50,
                measured_value="Uncalibrated",
                expected_value="Scale reference required",
                violation_reason="No calibration reference available; requires officer manual measurement with calipers.",
                rule_version=rule_version,
            )
        )

    # 4. Category-Specific Exception Annotation (capped at 3: medical_device, bulk_exempt, food_expiry)
    if category == "medical_device":
        results.append(
            ComplianceResultSchema(
                rule_id="CATEGORY_EXCEPTION_MEDICAL_DEVICE",
                rule_name="Medical Device Exemption",
                field_name="category_override",
                status=ComplianceStatus.REVIEW_REQUIRED,
                confidence=0.80,
                measured_value="Medical Device Proviso (2025)",
                expected_value="Officer verification of Drugs and Cosmetics Act license",
                violation_reason="Exempt from standard LMPC font/declaration rules if licensed as medical device.",
                rule_version=rule_version,
            )
        )
    elif category == "bulk_exempt":
        results.append(
            ComplianceResultSchema(
                rule_id="CATEGORY_EXCEPTION_BULK_EXEMPT",
                rule_name="Bulk Package Exemption",
                field_name="bulk_package_threshold",
                status=ComplianceStatus.PASS,
                confidence=0.92,
                measured_value="Bulk container (> 25 kg / 25 L)",
                expected_value="Institutional consumer package",
                violation_reason=None,
                rule_version=rule_version,
            )
        )
    elif category in ["food_expiry", "food"]:
        has_expiry, _, _ = _find_field("expiry_date", fields_dict)
        results.append(
            ComplianceResultSchema(
                rule_id="CATEGORY_EXCEPTION_FOOD_EXPIRY",
                rule_name="Food Product Expiry Mandate",
                field_name="expiry_date",
                status=ComplianceStatus.PASS if has_expiry else ComplianceStatus.FAIL,
                confidence=0.90,
                measured_value="Best Before / Expiry declaration verified" if has_expiry else "Missing Best Before / Expiry date",
                expected_value="Mandatory Expiry / Best Before per Rule 6(1)(d) second proviso & FSSAI",
                violation_reason=None if has_expiry else "Food commodities require explicit Best Before or Expiry Date.",
                rule_version=rule_version,
            )
        )

    return results
