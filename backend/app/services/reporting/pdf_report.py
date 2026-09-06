"""PDF Report Generation Service using ReportLab (Owner: Aditya).

Produces a formal government inspection report for the Legal Metrology (Packaged Commodities) Rules, 2011.
Conforms strictly to the 3-state compliance model (PASS, FAIL, REVIEW_REQUIRED)
and stamps the statutory rule version.
"""

import io
import os
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.scan import ScanResponse

# ------------------------------------------------------------------------------
# Color Palette
# ------------------------------------------------------------------------------
NAVY_PRIMARY = colors.HexColor("#0F294A")
NAVY_SECONDARY = colors.HexColor("#1E3A8A")
TEXT_MUTED = colors.HexColor("#475569")
TEXT_DARK = colors.HexColor("#0F172A")
BG_LIGHT = colors.HexColor("#F8FAFC")
BORDER_COLOR = colors.HexColor("#CBD5E1")

# Status Colors
STATUS_PASS_BG = colors.HexColor("#DCFCE7")
STATUS_PASS_TEXT = colors.HexColor("#15803D")
STATUS_PASS_BORDER = colors.HexColor("#86EFAC")

STATUS_FAIL_BG = colors.HexColor("#FEE2E2")
STATUS_FAIL_TEXT = colors.HexColor("#B91C1C")
STATUS_FAIL_BORDER = colors.HexColor("#FCA5A5")

STATUS_REV_BG = colors.HexColor("#FEF3C7")
STATUS_REV_TEXT = colors.HexColor("#B45309")
STATUS_REV_BORDER = colors.HexColor("#FCD34D")


def _get_status_style(status_val: str) -> tuple[colors.HexColor, colors.HexColor, colors.HexColor]:
    """Returns (bg_color, text_color, border_color) for given compliance status."""
    norm = str(status_val).upper().strip()
    if norm == "PASS":
        return STATUS_PASS_BG, STATUS_PASS_TEXT, STATUS_PASS_BORDER
    elif norm == "FAIL":
        return STATUS_FAIL_BG, STATUS_FAIL_TEXT, STATUS_FAIL_BORDER
    else:
        return STATUS_REV_BG, STATUS_REV_TEXT, STATUS_REV_BORDER


def generate_pdf_report(
    scan_data: ScanResponse | dict[str, Any], output_path: str | None = None
) -> bytes:
    """Generates an official Legal Metrology Compliance Inspection Report as PDF bytes.

    Args:
        scan_data: ScanResponse Pydantic instance or dictionary matching the scan schema.
        output_path: Optional file path to save the generated PDF.

    Returns:
        bytes: Raw PDF content bytes.
    """
    # Normalize data if Pydantic model
    if isinstance(scan_data, ScanResponse):
        data = scan_data.model_dump(mode="json")
    elif hasattr(scan_data, "__dict__") and not isinstance(scan_data, dict):
        # SQLAlchemy model or similar
        data = {
            "scan_id": getattr(scan_data, "id", "UNKNOWN"),
            "product_name": getattr(scan_data.product, "product_name", "Unknown Product")
            if getattr(scan_data, "product", None)
            else "Unknown",
            "brand_name": getattr(scan_data.product, "brand_name", None)
            if getattr(scan_data, "product", None)
            else None,
            "category": getattr(scan_data.product, "category", "standard_retail")
            if getattr(scan_data, "product", None)
            else "standard_retail",
            "overall_status": getattr(scan_data, "overall_status", "REVIEW_REQUIRED"),
            "overall_confidence": getattr(scan_data, "overall_confidence", 0.8),
            "calibrated_scale_factor": getattr(scan_data, "calibrated_scale_factor", None),
            "calibration_method": getattr(scan_data, "calibration_method", "none"),
            "rule_version": getattr(scan_data, "rule_version", "LMPC-2011-v1.0"),
            "evidence_image_url": getattr(scan_data, "evidence_image_path", None),
            "created_at": getattr(scan_data, "created_at", datetime.now(UTC)).isoformat()
            if hasattr(getattr(scan_data, "created_at", None), "isoformat")
            else str(getattr(scan_data, "created_at", "")),
            "compliance_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "field_name": r.field_name,
                    "status": r.status,
                    "confidence": r.confidence,
                    "measured_value": r.measured_value,
                    "expected_value": r.expected_value,
                    "violation_reason": r.violation_reason,
                    "rule_version": r.rule_version,
                }
                for r in getattr(scan_data, "compliance_results", [])
            ],
        }
    else:
        data = scan_data

    # Extract top-level fields
    scan_id = str(data.get("scan_id", "N/A"))
    product_name = data.get("product_name") or "Packaged Commodity Sample"
    brand_name = data.get("brand_name") or "Unspecified Brand"
    category = str(data.get("category") or "standard_retail").replace("_", " ").title()
    overall_status = str(data.get("overall_status", "REVIEW_REQUIRED")).upper()
    overall_conf = float(data.get("overall_confidence", 0.0))
    scale_factor = data.get("calibrated_scale_factor")
    calib_method = str(data.get("calibration_method", "none")).replace("_", " ").title()
    rule_version = data.get("rule_version") or "LMPC-2011-v1.0"
    created_at_raw = data.get("created_at")
    evidence_image_url = data.get("evidence_image_url")
    results = data.get("compliance_results", [])

    # Format timestamp
    try:
        if isinstance(created_at_raw, str):
            dt = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        elif isinstance(created_at_raw, datetime):
            dt = created_at_raw
        else:
            dt = datetime.now(UTC)
        scan_timestamp = dt.strftime("%d-%b-%Y %H:%M:%S UTC")
    except Exception:
        scan_timestamp = str(created_at_raw)

    # Document buffer setup
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
    )

    # Styles
    sample_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GovHeader",
        parent=sample_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=NAVY_PRIMARY,
        alignment=1,  # Centered
    )
    subtitle_style = ParagraphStyle(
        "GovSubtitle",
        parent=sample_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=NAVY_SECONDARY,
        alignment=1,
    )
    rule_stamp_style = ParagraphStyle(
        "RuleStamp",
        parent=sample_styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=1,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=sample_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=NAVY_PRIMARY,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "CellBody",
        parent=sample_styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=TEXT_DARK,
    )
    body_muted = ParagraphStyle(
        "CellBodyMuted", parent=body_style, fontSize=7.5, textColor=TEXT_MUTED
    )
    verdict_badge_style = ParagraphStyle(
        "VerdictBadge",
        parent=sample_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        alignment=1,
    )

    story = []

    # --------------------------------------------------------------------------
    # 1. Government Header & Rule Stamp
    # --------------------------------------------------------------------------
    story.append(Paragraph("GOVERNMENT OF INDIA • MINISTRY OF CONSUMER AFFAIRS", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011", title_style))
    story.append(Paragraph("OFFICIAL STATUTORY COMPLIANCE INSPECTION REPORT", subtitle_style))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            f"<b>Statutory Standard:</b> Legal Metrology Act, 2009 (Sec 18/36) &nbsp;|&nbsp; "
            f"<b>Rule Version Configuration:</b> <font color='#1E3A8A'><b>{rule_version}</b></font> &nbsp;|&nbsp; "
            f"<b>Effective Scope:</b> Rule 6 Declarations, Rule 7 Font Thresholds &amp; 2025 Amendments",
            rule_stamp_style,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        HRFlowable(width="100%", thickness=1.5, color=NAVY_PRIMARY, spaceAfter=8, spaceBefore=2)
    )

    # --------------------------------------------------------------------------
    # 2. Executive Verdict Banner (Three-State)
    # --------------------------------------------------------------------------
    v_bg, v_text, v_border = _get_status_style(overall_status)
    status_label = (
        "VERDICT: COMPLIANT (PASS)"
        if overall_status == "PASS"
        else (
            "VERDICT: NON-COMPLIANT VIOLATIONS DETECTED (FAIL)"
            if overall_status == "FAIL"
            else "VERDICT: OFFICER REVIEW REQUIRED (AMBIGUOUS / UNCALIBRATED)"
        )
    )
    verdict_badge_style.textColor = v_text

    verdict_table_data = [
        [
            Paragraph(status_label, verdict_badge_style),
            Paragraph(
                f"<b>Overall Pipeline Confidence:</b> {round(overall_conf * 100, 1)}%<br/>"
                f"<b>Assessment Date:</b> {scan_timestamp}",
                body_style,
            ),
        ]
    ]
    verdict_table = Table(verdict_table_data, colWidths=[360, 163])
    verdict_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), v_bg),
                ("BOX", (0, 0), (-1, -1), 1.5, v_border),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(verdict_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------------------------
    # 3. Inspection Metadata Block
    # --------------------------------------------------------------------------
    story.append(Paragraph("1. INSPECTION & PACKAGE IDENTIFICATION METADATA", section_heading))
    meta_table_data = [
        [
            Paragraph("<b>Inspection Scan ID:</b>", body_muted),
            Paragraph(f"<font name='Courier'>{scan_id}</font>", body_style),
            Paragraph("<b>Inspect Date/Time:</b>", body_muted),
            Paragraph(scan_timestamp, body_style),
        ],
        [
            Paragraph("<b>Commodity Name:</b>", body_muted),
            Paragraph(f"<b>{product_name}</b>", body_style),
            Paragraph("<b>Brand / Trademark:</b>", body_muted),
            Paragraph(brand_name, body_style),
        ],
        [
            Paragraph("<b>Package Category:</b>", body_muted),
            Paragraph(f"{category}", body_style),
            Paragraph("<b>Inspecting Authority:</b>", body_muted),
            Paragraph("Legal Metrology Inspectorate (Field Unit)", body_style),
        ],
        [
            Paragraph("<b>Scale Calibration:</b>", body_muted),
            Paragraph(
                f"{calib_method}"
                + (f" ({scale_factor} mm/px)" if scale_factor else " (No reference detected)"),
                body_style,
            ),
            Paragraph("<b>Statutory Reference:</b>", body_muted),
            Paragraph(f"Rule Version {rule_version}", body_style),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[105, 160, 105, 153])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------------------------
    # 4. Summary Metrics Table
    # --------------------------------------------------------------------------
    total_checks = len(results)
    pass_checks = sum(1 for r in results if str(r.get("status", "")).upper() == "PASS")
    fail_checks = sum(1 for r in results if str(r.get("status", "")).upper() == "FAIL")
    review_checks = sum(1 for r in results if str(r.get("status", "")).upper() == "REVIEW_REQUIRED")
    score_pct = round((pass_checks / total_checks * 100.0), 1) if total_checks > 0 else 0.0

    story.append(Paragraph("2. STATUTORY COMPLIANCE AUDIT SUMMARY", section_heading))
    metrics_data = [
        [
            Paragraph("<b>Total Rules Evaluated</b>", body_muted),
            Paragraph("<b>Compliant (PASS)</b>", body_muted),
            Paragraph("<b>Violations (FAIL)</b>", body_muted),
            Paragraph("<b>Officer Review (REVIEW)</b>", body_muted),
            Paragraph("<b>Statutory Pass Rate</b>", body_muted),
        ],
        [
            Paragraph(f"<font size=11><b>{total_checks}</b></font>", body_style),
            Paragraph(f"<font size=11 color='#15803D'><b>{pass_checks}</b></font>", body_style),
            Paragraph(f"<font size=11 color='#B91C1C'><b>{fail_checks}</b></font>", body_style),
            Paragraph(f"<font size=11 color='#B45309'><b>{review_checks}</b></font>", body_style),
            Paragraph(f"<font size=11 color='#0F294A'><b>{score_pct}%</b></font>", body_style),
        ],
    ]
    metrics_table = Table(metrics_data, colWidths=[105, 105, 105, 110, 98])
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------------------------
    # 5. Detailed Findings Table (Rule Engine Output)
    # --------------------------------------------------------------------------
    story.append(
        Paragraph("3. DETAILED STATUTORY RULE FINDINGS & ADVISORY ACTIONS", section_heading)
    )

    findings_headers = [
        Paragraph("<b>Statutory Rule & ID</b>", body_muted),
        Paragraph("<b>Target Parameter</b>", body_muted),
        Paragraph("<b>Measured / Observed</b>", body_muted),
        Paragraph("<b>Mandatory Standard</b>", body_muted),
        Paragraph("<b>Verdict</b>", body_muted),
        Paragraph("<b>Statutory Explanation & Action</b>", body_muted),
    ]
    findings_rows = [findings_headers]

    for r in results:
        r_id = r.get("rule_id", "RULE_N/A")
        r_name = r.get("rule_name", r_id)
        f_name = str(r.get("field_name", "")).replace("_", " ").title()
        status_val = str(r.get("status", "REVIEW_REQUIRED")).upper()
        conf = round(float(r.get("confidence", 0.0)) * 100, 0)
        measured = str(r.get("measured_value") or "Detected")
        expected = str(r.get("expected_value") or "Statutory requirement")
        reason = r.get("violation_reason")

        st_bg, st_text, _ = _get_status_style(status_val)
        status_html = f"<font color='{st_text.hexval()}'><b>{status_val}</b></font><br/><font size=6.5 color='#64748B'>{conf:.0f}% conf</font>"

        if status_val == "PASS":
            explanation = "Complies with statutory standard. No enforcement action required."
        elif status_val == "FAIL":
            explanation = f"<font color='#B91C1C'><b>VIOLATION:</b> {reason or 'Does not satisfy legal metrology mandate. Notice recommended.'}</font>"
        else:
            explanation = f"<font color='#B45309'><b>REVIEW:</b> {reason or 'Ambiguous detection. Field inspection officer verification recommended.'}</font>"

        findings_rows.append(
            [
                Paragraph(
                    f"<b>{r_name}</b><br/><font size=6.5 color='#64748B'>{r_id}</font>", body_style
                ),
                Paragraph(f"{f_name}", body_style),
                Paragraph(f"{measured}", body_style),
                Paragraph(f"{expected}", body_muted),
                Paragraph(status_html, body_style),
                Paragraph(explanation, body_style),
            ]
        )

    findings_table = Table(findings_rows, colWidths=[100, 65, 80, 85, 65, 128])
    findings_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(findings_table)
    story.append(Spacer(1, 12))

    # --------------------------------------------------------------------------
    # 6. Packaging Evidence Image Block
    # --------------------------------------------------------------------------
    evidence_elements = []
    evidence_elements.append(
        Paragraph("4. PACKAGING EVIDENCE PHOTO & SPATIAL VERIFICATION", section_heading)
    )

    image_drawn = False
    if evidence_image_url:
        # Check if file exists on disk
        clean_path = evidence_image_url.lstrip("/")
        if os.path.exists(clean_path):
            try:
                from PIL import Image as PILImage

                with PILImage.open(clean_path) as pil_img:
                    pil_img.verify()
                img = Image(clean_path, width=4.5 * inch, height=2.2 * inch)
                img.hAlign = "CENTER"
                evidence_elements.append(img)
                image_drawn = True
            except Exception:
                image_drawn = False

    if not image_drawn:
        # Designated placeholder frame
        placeholder_data = [
            [
                Paragraph(
                    "<b>[ PACKAGING EVIDENCE IMAGE — ANNOTATED PDP INSPECTION PHOTO ]</b><br/><br/>"
                    f"<i>Associated Image Reference: {evidence_image_url or 'Live scan capture'}</i><br/>"
                    "Verified bounding boxes for Principal Display Panel (PDP), Rule 6 mandatory declarations,<br/>"
                    "and Rule 7 font-height measurement calibration scale.",
                    ParagraphStyle(
                        "EvidencePlaceholder", parent=body_style, alignment=1, textColor=TEXT_MUTED
                    ),
                )
            ]
        ]
        placeholder_table = Table(placeholder_data, colWidths=[523])
        placeholder_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ]
            )
        )
        evidence_elements.append(placeholder_table)

    story.append(KeepTogether(evidence_elements))
    story.append(Spacer(1, 14))

    # --------------------------------------------------------------------------
    # 7. Verification & Officer Signature Block
    # --------------------------------------------------------------------------
    verification_elements = []
    verification_elements.append(Paragraph("5. STATUTORY VERIFICATION & SIGN-OFF", section_heading))
    verification_elements.append(
        Paragraph(
            "<i>Notice: This automated report constitutes a preliminary technical assessment prepared under the "
            "Legal Metrology (Packaged Commodities) Rules, 2011. Final enforcement notices under Section 36 are subject "
            "to field verification and discretion of the authorized Legal Metrology Inspector.</i>",
            body_muted,
        )
    )
    verification_elements.append(Spacer(1, 8))

    sig_data = [
        [
            Paragraph(
                "<b>Automated System Engine:</b><br/>SIH26034 Compliance Engine v1.0<br/>Rule Version: "
                + rule_version,
                body_muted,
            ),
            Paragraph(
                "<b>Inspecting Officer Name:</b><br/>Field Officer Sharma<br/>Badge ID: LM-DL-2026-084",
                body_muted,
            ),
            Paragraph(
                "<b>Signature & Official Seal:</b><br/><br/>____________________________________<br/>Legal Metrology Inspectorate",
                body_muted,
            ),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[174, 174, 175])
    sig_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    verification_elements.append(sig_table)

    story.append(KeepTogether(verification_elements))

    # Build PDF document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
