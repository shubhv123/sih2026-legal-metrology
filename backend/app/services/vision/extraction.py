"""
Owner: SHUBH

Field Extraction Pipeline for SIH26034 Legal Metrology Compliance Checker.
Architecture:
  raw OCR text + bboxes
    -> text normalization
    -> RapidFuzz label matching against FIELD_KEYWORDS
    -> spatial proximity association (same line, horizontal neighbor, vertical neighbor)
    -> field-specific regex validation & value normalization
    -> composite confidence scoring

Note on Rules & Tolerances:
- Raw regex alone is NOT error-tolerant. Fuzzy matching catches OCR misspellings
  like 'M8P' -> 'MRP', 'Nel Wt' -> 'Net Wt', 'Mtg Date' -> 'Mfg Date'.
- Date regex accepts both '/' and '-' separators and day-month-year formats (DD[/-]MM[/-]YY(YY)).
  Rule 6(1)(d) only requires Month & Year, so full dates are normalized to MM/YYYY.
- Expiry date is included to support the food_expiry category exception.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from rapidfuzz import fuzz

from app.schemas.scan import ExtractedField, BoundingBox

logger = logging.getLogger(__name__)

FIELD_KEYWORDS: Dict[str, List[str]] = {
    "mrp": [

        "mrp", "maximum retail price", "m.r.p", "max retail price",
        "incl. of all taxes", "inclusive of all taxes", "incl all taxes",
    ],
    "net_quantity": [
        "net wt", "net weight", "net qty", "net quantity",
        "net volume", "net vol", "volume", "vol.", "contents",
        "net content", "net contents", "net mass",
    ],
    "mfg_date": [
        "mfg date", "mfd date", "date of mfg", "date of mfd", "date of manufacture", "manufacturing date",
        "mfd on", "mfg on", "manufactured on", "mfd dt", "mfg dt",
        "pkd on", "packed on", "date of packing", "packing date",
        "batch date", "mfd:", "mfg:", "mfd.", "mfg.", "pkd:", "pkd.",
    ],
    "expiry_date": [
        "best before", "best before date", "best before dt", "bbd", "bbd.", "bbd:",
        "use by", "use-by", "ubd", "ubd.", "ubd:", "use by date", "use by dt",
        "expiry", "expiry date", "exp date", "exp dt", "expiry dt",
        "exp", "exp.", "exp:",
    ],
    "unit_sale_price": [
        "unit sale price", "usp", "price per g", "price per kg",
        "price per ml", "price per l", "price per unit", "u.s.p",
    ],
    "manufacturer_name": [
        "mfd by", "manufactured by", "marketed by", "packed by",
        "packer", "manufacturer", "mfg by", "mktd by", "manufactured & marketed by",
        "brand owner", "brand owner (marketed by)", "imported and marketed by",
    ],
    "consumer_care": [
        "consumer care", "customer care", "helpline", "contact us",
        "toll free", "feedback", "consumer complaints", "care cell",
        "write us on", "write to us", "write us", "reach us",
        "customer support", "customer service", "email us", "email",
        "e-mail", "ph:", "ph.", "phone", "tel:", "tel no", "tel.", "tel",
        "call us", "enquiry", "for complaint", "complaint",
    ],
    "generic_name": [
        "generic name", "common name", "commodity", "product name",
    ],
    "country_of_origin": [
        "country of origin", "made in", "origin", "country of manufacture",
    ],
}


MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


# ============================================================================
# Field-Specific Regex Parsers & Normalizers
# ============================================================================

def parse_date(text: str) -> Optional[Tuple[str, str]]:
    """
    Parses date strings supporting:
      - Month/Year: MM[/-.]YYYY, MM[/-.]YY, Mon[/-.]YYYY (e.g. 08/2026, 08-26, Aug 2026)
      - Day/Month/Year: DD[/-.]MM[/-.]YYYY, DD[/-.]MM[/-.]YY (e.g. 15/08/2026, 15-08-26)
    
    Accepts '/' and '-' and '.' interchangeably to tolerate OCR character ambiguity.
    Normalizes full dates to 'MM/YYYY' per Rule 6(1)(d) requirements.
    
    Returns:
        (raw_matched_text, normalized_MM_YYYY) or None
    """
    clean = text.strip()

    # Preprocess dot-matrix OCR noise:
    # 1. Glued 7 or T before 4-digit year (e.g. '72025' -> '2025')
    clean = re.sub(r"[7T](20\d{2})", r"\1", clean)
    # 2. Dot-matrix letter-digit confusion in years (e.g. '20z5', '20zs', '202s' -> '2025')
    clean = re.sub(r"20[zZ2][0-9sS]", lambda m: "202" + ("5" if m.group(0)[3] in "sS" else m.group(0)[3]), clean)
    clean = re.sub(r"20[0oO][0-9sS]", lambda m: "202" + ("5" if m.group(0)[3] in "sS" else m.group(0)[3]), clean)
    # 3. Slanted slash / pipe / V between digits (e.g. '1V05' -> '1/05')
    clean = re.sub(r"(\d)[Vv|](\d)", r"\1/\2", clean)

    # Pattern A: Full date DD[/-.]MM[/-.]YYYY or DD[/-.]MM[/-.]YY
    full_date_match = re.search(
        r"(?:^|\D)([0-3]?[0-9])[/\-\.]([0-1]?[0-9])[/\-\.]((?:20)?\d{2})\b",
        clean,
    )
    if full_date_match:
        day = int(full_date_match.group(1))
        month = int(full_date_match.group(2))
        year = full_date_match.group(3)
        if 1 <= day <= 31 and 1 <= month <= 12:
            if len(year) == 2:
                year = f"20{year}"
            return full_date_match.group(0).strip(" ,:;"), f"{month:02d}/{year}"

    # Pattern B1: Month-Year MM[/-.]YYYY or MM[/-.]YY (tolerates noisy leading characters, e.g. '40/05/2025' -> 05/2025)
    my_match = re.search(
        r"(?:^|\D)([0-1]?[0-9])[/\-\.]((?:20)?\d{2})\b",
        clean,
    )
    if my_match:
        month = int(my_match.group(1))
        year = my_match.group(2)
        if 1 <= month <= 12:
            if len(year) == 2:
                year = f"20{year}"
            return my_match.group(0).strip(" ,:;"), f"{month:02d}/{year}"

    # Pattern B2: Glued Month-Year with 4-digit year (e.g. '105/2024' -> 05/2024)
    glued_match = re.search(r"([0-1][0-9])[/\-\.](20\d{2})\b", clean)
    if glued_match:
        month = int(glued_match.group(1))
        year = glued_match.group(2)
        if 1 <= month <= 12:
            return glued_match.group(0), f"{month:02d}/{year}"

    # Pattern B3: 4-digit date without slash (e.g. '1105/2024' or '4105/2024' -> 05/2024)
    glued_no_sep = re.search(r"\b\d{2}(0[1-9]|1[0-2])[/\-\.]?(20\d{2})\b", clean)
    if glued_no_sep:
        month = int(glued_no_sep.group(1))
        year = glued_no_sep.group(2)
        return glued_no_sep.group(0), f"{month:02d}/{year}"

    # Pattern C1: Alphanumeric day-month-year e.g. "01-Aug-2026", "15/AUG/26", "28.Jan.2027"
    alpha_dmy_match = re.search(
        r"\b([0-3]?[0-9])[/\-\.\s]+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[/\-\.\s]+((?:20)?\d{2})\b",
        clean,
        re.IGNORECASE,
    )
    if alpha_dmy_match:
        raw = alpha_dmy_match.group(0)
        mon_str = alpha_dmy_match.group(2).lower()[:3]
        year = alpha_dmy_match.group(3)
        if len(year) == 2:
            year = f"20{year}"
        month_num = MONTH_MAP.get(mon_str, "01")
        return raw, f"{month_num}/{year}"

    # Pattern C2: Textual month-year e.g. "Aug 2026", "August 2026", "Aug-26", "AUG/2026"
    text_month_match = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[/\-\.\s]+((?:20)?\d{2})\b",
        clean,
        re.IGNORECASE,
    )
    if text_month_match:
        raw = text_month_match.group(0)
        mon_str = text_month_match.group(1).lower()[:3]
        year = text_month_match.group(2)
        if len(year) == 2:
            year = f"20{year}"
        month_num = MONTH_MAP.get(mon_str, "01")
        return raw, f"{month_num}/{year}"

    return None


def date_norm_to_months(norm_str: str) -> Optional[int]:
    """Converts normalized MM/YYYY into year * 12 + month for chronological ordering."""
    try:
        parts = norm_str.split("/")
        if len(parts) == 2:
            return int(parts[1]) * 12 + int(parts[0])
    except Exception:
        pass
    return None


def parse_mrp(text: str, matched_kw: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Extracts MRP numerical price.
    - If matched_kw is given (e.g. after 'MRP' or 'M8P'), searches the text following the keyword.
    - Strips adjacent bracketed unit rates (e.g. '(₹0.60 per ml)') to prevent interference.
    - Uses negative lookahead to ignore shelf-life durations (e.g. '18 months', '60 days').
    - Corrects common OCR currency confusion (e.g. '7299' -> 299 where 7 was misread '₹').
    
    Returns:
        (raw_matched_text, normalized_float_str_e.g._"149.00")
    """
    clean = text.strip()
    search_text = clean

    # Remove bracketed unit sale price from candidate text to avoid cross-field confusion
    search_text = re.sub(
        r"\([^\)]*(?:per|\/)\s*(?:ml|g|kg|l|unit|cm|m|number|piece|u|n)[^\)]*\)",
        "",
        search_text,
        flags=re.IGNORECASE,
    ).strip()

    if matched_kw:
        idx = clean.lower().find(matched_kw.lower())
        if idx != -1:
            after_kw = clean[idx + len(matched_kw):].strip(" :-\t")
            if after_kw:
                search_text = re.sub(
                    r"\([^\)]*(?:per|\/)\s*(?:ml|g|kg|l|unit|cm|m|number|piece|u|n)[^\)]*\)",
                    "",
                    after_kw,
                    flags=re.IGNORECASE,
                ).strip()

    # Preprocess common OCR currency prefix substitutions: '7' or 'T' or '{' preceding a price (e.g. '7 320' or '7320/-')
    clean_currency = re.sub(r"^[7T{]\s*([1-9][0-9]{1,4}(?:\.[0-9]{1,2})?)\s*(?:\/-)?$", r"₹ \1", search_text)
    if clean_currency != search_text:
        search_text = clean_currency

    # Preprocess dot-matrix inkjet price tokens: 'Taco', '{a20', 't3c0-', 'T3c0', '{3c0', '7az0', '7 320/-'
    dot_m = re.search(r"^[₹{tT7]\s*([1-9a-z0-9]{2,4})\s*(?:\/[-–—]|[-–—])?$", search_text)
    if dot_m:
        body = dot_m.group(1).lower()
        body = (
            body.replace("a", "3")
            .replace("j", "3")
            .replace("c", "2")
            .replace("z", "2")
            .replace("o", "0")
            .replace("q", "0")
            .replace("u", "0")
            .replace("l", "1")
            .replace("i", "1")
            .replace("s", "5")
            .replace("b", "6")
        )
        if body.isdigit():
            val = float(body)
            if 10.0 <= val <= 50000.0:
                search_text = f"₹ {val:.2f}"

    # Priority 1: Match with explicit currency prefix (Rs., ₹, INR) OR trailing slash-dash notation (e.g. 320/-, ₹ 320/-)
    match_curr = re.search(
        r"(?:(?:rs\.?|₹|inr)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/-)?|\b([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*\/[-–—])(?!\s*(?:months?|days?|years?|mon|hrs?))",
        search_text,
        re.IGNORECASE,
    )
    if match_curr:
        try:
            num_str = match_curr.group(1) or match_curr.group(2)
            val_float = float(num_str.replace(",", ""))
            if 0.5 <= val_float <= 1000000.0:
                return match_curr.group(0).strip(), f"{val_float:.2f}"
        except ValueError:
            pass

    # Priority 2: If following an explicit MRP label keyword, match standalone price with comma support
    if matched_kw:
        match_num = re.search(
            r"\b([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)(?!\s*(?:months?|days?|years?|mon|hrs?))\s*(?:\/-)?\b",
            search_text,
        )
        if match_num:
            try:
                val_float = float(match_num.group(1).replace(",", ""))
                if 0.5 <= val_float <= 1000000.0:
                    return match_num.group(0).strip(), f"{val_float:.2f}"
            except ValueError:
                pass

    return None



def parse_net_quantity(text: str, matched_kw: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Extracts net quantity with metric or count unit.
    Normalizes units to standard LMPC abbreviations (g, kg, ml, l, m, cm, u).
    Tolerates packaging OCR typos:
      - 'SOOmL' or 'S00ml' -> 500 ml (S->5, O->0)
      - '400 9' or '400 q' -> 400 g (9/q -> g)
      - 'Net Volume : 500mL' -> 500 ml
    """
    clean = text.strip()
    search_text = clean

    if matched_kw:
        idx = clean.lower().find(matched_kw.lower())
        if idx != -1:
            after_kw = clean[idx + len(matched_kw):].strip(" :-\t")
            if after_kw:
                search_text = after_kw

    def _normalize_unit(raw: str) -> str:
        r = raw.lower().replace(" ", "")
        if r in ["kg"]:
            return "kg"
        elif r in ["g", "gm", "gms", "gram", "grams", "9", "q"]:
            return "g"
        elif r in ["l", "lt", "liter", "litres", "litre", "liters"]:
            return "l"
        elif r in ["ml", "millilitre", "milli litre"]:
            return "ml"
        elif r in ["m"]:
            return "m"
        elif r in ["cm"]:
            return "cm"
        return "u"

    # Multi-pack pattern e.g. "2N x 250 g", "3 x 100g", "2 x 500ml"
    multi_pattern = (
        r"\b([0-9]+)\s*(?:n|u|pcs?|pieces?)?\s*[xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*"
        r"(kg|g|gm|gms|gram|grams|l|lt|liter|litres|litre|liters|ml|milli\s*litre|m|cm|mm)\b"
    )
    multi_match = re.search(multi_pattern, search_text, re.IGNORECASE)
    if not multi_match and matched_kw:
        multi_match = re.search(multi_pattern, clean, re.IGNORECASE)
    if multi_match:
        count = multi_match.group(1)
        sub_val = multi_match.group(2)
        norm_unit = _normalize_unit(multi_match.group(3))
        return multi_match.group(0).strip(), f"{count} x {sub_val} {norm_unit}"

    # Main quantity pattern with OCR typo tolerance on numbers and units
    # Matches standard digits OR letters commonly confused with digits (S, O, I, L)
    pattern = (
        r"\b([0-9SOIl]+(?:\.[0-9]+)?)\s*"
        r"(kg|g|gm|gms|gram|grams|l|lt|liter|litres|litre|liters|ml|milli\s*litre|m|cm|mm|units?|pieces?|pcs?|n|u)\b"
    )
    match = re.search(pattern, search_text, re.IGNORECASE)
    if not match and matched_kw:
        match = re.search(pattern, clean, re.IGNORECASE)

    # Space-separated OCR typo unit e.g. "400 9" or "400 q" (where 9/q was misread from 'g')
    if not match:
        pattern_typo = r"\b([0-9SOIl]+(?:\.[0-9]+)?)\s+([9q])\b"
        match = re.search(pattern_typo, search_text, re.IGNORECASE)
        if not match and matched_kw:
            match = re.search(pattern_typo, clean, re.IGNORECASE)

    if match:
        raw_val = match.group(1).upper()
        # Clean OCR digit typos: S -> 5, O -> 0, I/L -> 1
        cleaned_val = (
            raw_val.replace("S", "5")
            .replace("O", "0")
            .replace("I", "1")
            .replace("L", "1")
        )
        try:
            float(cleaned_val)
            norm_unit = _normalize_unit(match.group(2))
            # Require standard metric units for standalone quantity detection (avoid false positives on noise like '3u')
            if not matched_kw and norm_unit in ["u", "cm", "m"]:
                return None
            return match.group(0).strip(), f"{cleaned_val} {norm_unit}"
        except ValueError:
            pass

    return None


def parse_unit_sale_price(text: str) -> Optional[Tuple[str, str]]:
    """
    Extracts Unit Sale Price (USP), e.g.:
      - Standalone: 'Rs. 0.30 / g', '₹ 150/kg'
      - Bracketed adjacent to MRP: '(₹0.60 per ml)', '(Rs. 0.08/g)', '(0.60 per ml)'
      - Sold by number/piece: '₹2,999.00 (incl. of all taxes) per Number', 'per piece'
    """
    clean = text.strip()

    # Pattern A: Bracketed unit price adjacent to MRP e.g. "(Rs. 0.08/g)", "(₹0.60 per ml)", "(Rs. 0.50/g)"
    bracket_pattern = (
        r"\((?:rs\.?|₹)?\s*([0-9]+(?:\.[0-9]{1,3})?)\s*(?:\/|per)\s*"
        r"(g|kg|ml|l|unit|cm|m|piece|n|u|number)\)"
    )
    bracket_match = re.search(bracket_pattern, clean, re.IGNORECASE)
    if bracket_match:
        price = float(bracket_match.group(1))
        unit = bracket_match.group(2).lower()
        return bracket_match.group(0).strip(), f"{price:.2f} / {unit}"

    # Pattern B: Standard unit sale price declaration e.g. "Rs. 0.60 per ml", "₹ 1.20 / g"
    pattern = (
        r"(?:rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,3})?)\s*(?:\/|per)\s*"
        r"(g|kg|ml|l|unit|cm|m|piece|n|u|number)\b"
    )
    match = re.search(pattern, clean, re.IGNORECASE)
    if match:
        raw_price_str = match.group(1).replace(",", "")
        price = float(raw_price_str)
        unit = match.group(2).lower()
        return match.group(0).strip(), f"{price:.2f} / {unit}"

    # Pattern C: Unit rate indicated as per Number / per Piece adjacent to MRP
    per_num_match = re.search(
        r"(?:(?:rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)[^\n]*)?(?:per|\/)\s*(number|piece|unit|item|u|n)\b",
        clean,
        re.IGNORECASE,
    )
    if per_num_match:
        price_part = per_num_match.group(1)
        unit = per_num_match.group(2).lower()
        if price_part:
            price = float(price_part.replace(",", ""))
            return per_num_match.group(0).strip(), f"{price:.2f} / {unit}"
        else:
            return per_num_match.group(0).strip(), f"per {unit}"

    return None


def parse_consumer_care(text: str) -> Optional[Tuple[str, str, bool]]:
    """
    Extracts contact telephone numbers, toll-free lines, and email addresses.
    Returns:
        (raw_string, normalized_string, is_heuristic) or None
    """
    clean = text.strip()
    parts = []
    raws = []
    is_heuristic = False

    # 1. Clean email matching with strict dot before TLD
    email_pattern = r"\b[A-Za-z0-9._%+-]+(?:\s*@\s*|\s*e\s*|\s*at\s*)[A-Za-z0-9.-]+\.(?:com|in|org|net|co\.in|gov\.in)\b"
    for em in re.finditer(email_pattern, clean, re.IGNORECASE):
        raw = em.group(0)
        raws.append(raw)
        norm_em = re.sub(r"\s*(?:@|e|at)\s*", "@", raw, count=1, flags=re.IGNORECASE).lower()
        parts.append(norm_em)

    # 1b. Space-corrupted TLD email recovery (e.g. 'enquiry@zebronics com' -> enquiry@zebronics.com)
    # Priority 3: Normalize space to dot in normalized_value, and flag as heuristic for confidence discount
    if not parts:
        space_tld_pattern = r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)\s+(com|in|org|net|co\.in|gov\.in)\b"
        for em in re.finditer(space_tld_pattern, clean, re.IGNORECASE):
            raw = em.group(0)
            prefix = em.group(1).lower()
            tld = em.group(2).lower()
            norm_em = f"{prefix}.{tld}"
            raws.append(raw)
            parts.append(norm_em)
            is_heuristic = True

    # 1c. Dotless email fallback for packaging OCR (e.g. 'supporteurbanwipein' -> support@urbanwipe.in)
    if not parts:
        dotless_pattern = r"\b(support|care|info|contact|help|complaints?|feedback|service|reach)(?:@|e|at)([a-z0-9-]+)(in|com|org|net)\b"
        m_dotless = re.search(dotless_pattern, clean, re.IGNORECASE)
        if m_dotless:
            raw = m_dotless.group(0)
            prefix = m_dotless.group(1).lower()
            domain = m_dotless.group(2).lower()
            tld = m_dotless.group(3).lower()
            raws.append(raw)
            parts.append(f"{prefix}@{domain}.{tld}")
            is_heuristic = True

    # 2. Phone number matching (STD code + landline with interior space, mobile 10-digit with optional 0/91, 1800 toll free)
    phone_pattern = (
        r"(?:\b|(?<=[\s,:]))(?:\+?91[\-\s]?)?"
        r"(?:1800[\-\s]?[0-9]{3}[\-\s]?[0-9]{3,4}|"
        r"0?[6-9][0-9]{4}[\-\s]?[0-9]{5}|"
        r"0[0-9]{2,4}[\-\s]?[0-9]{3,4}[\-\s]?[0-9]{3,4}|"
        r"0[0-9]{2,4}[\-\s]?[0-9]{6,8})\b"
    )
    for pm in re.finditer(phone_pattern, clean):
        raw_p = pm.group(0).strip(" ,:")
        if raw_p and raw_p not in raws:
            raws.append(raw_p)
            parts.append(raw_p.replace(" ", ""))

    if parts:
        return ", ".join(raws), ", ".join(parts), is_heuristic
    return None


def parse_manufacturer(text: str, matched_kw: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Extracts company name & address following the manufacturer label keyword.
    """
    clean = text.strip()
    # Reject lines that are purely manufacturing date lines or package contents
    if re.search(r"\b(?:manufactured|mfg|pkd|packed)\s+on\b", clean, re.IGNORECASE) or re.search(r"\b(?:on|date|dt)\b[:\s]*\d{2}[/-]?\d{2,4}", clean, re.IGNORECASE):
        return None
    if re.search(r"\b(?:package contents|contents)\b", clean, re.IGNORECASE):
        return None
    # Reject lines that are instructions, redirects, or marketing story prose
    if re.search(r"\b(?:see\s+first|see\s+batch|scan\s+(?:the\s+)?qr|address\s+details\s+see)\b", clean, re.IGNORECASE):
        return None
    if clean.endswith("-") or re.search(r"\b(?:rich land|from the farmer|precious gift|seeds and knowledge|better future|finest produce)\b", clean, re.IGNORECASE):
        return None

    # If there is a colon, split by colon
    if ":" in clean:
        parts = clean.split(":", 1)
        rem = parts[1].strip(" :-\t|")
        if len(rem) >= 3 and not re.search(r"^\d{2}[/-]?\d{2,4}$", rem) and not rem.endswith("-"):
            return clean, rem

    # If there is a hyphen or dash separating label and entity (e.g. "BRAND OWNER (MARKETED BY) - BIMBO BAKERIES...")
    if " - " in clean:
        parts = clean.split(" - ", 1)
        rem = parts[1].strip(" :-\t|")
        if len(rem) >= 3 and not re.search(r"^\d{2}[/-]?\d{2,4}$", rem) and not rem.endswith("-"):
            return clean, rem

    for kw in [
        "imported and marketed by", "manufactured & marketed by", "manufactured and marketed by",
        "brand owner (marketed by)", "brand owner", "manufactured by", "marketed by",
        "mfd by", "packed by", "packer", "manufacturer", "mktd by",
    ]:
        idx = clean.lower().find(kw)
        if idx != -1:
            rem = clean[idx + len(kw):].strip(" :-\t|")
            if len(rem) >= 3 and not re.search(r"^\d{2}[/-]?\d{2,4}$", rem) and not rem.endswith("-"):
                return clean, rem

    # Check for keywords ending with "by"
    m_by = re.search(r"\b(?:by|packer|mfr)\b[:\s]*(.*)", clean, re.IGNORECASE)
    if m_by:
        rem = m_by.group(1).strip(" :-\t|")
        if len(rem) >= 3 and not re.search(r"^\d{2}[/-]?\d{2,4}$", rem) and not rem.endswith("-"):
            return clean, rem

    # Only accept standalone text if it contains legitimate company/entity markers
    if re.search(r"\b(?:pvt|ltd|limited|inc|corp|co\b|industries|works|bakeries|india|enterprises|unilever)\b", clean, re.IGNORECASE):
        return clean, clean

    return None




def parse_generic_name(text: str, matched_kw: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Extracts generic product name following the keyword.
    """
    clean = text.strip()
    # Disqualify regulatory, license, or packaging codes
    if re.search(r"\b(?:fssai|lic|license|regd|reg\.?|batch|lot|iso|agmark|barcode|code)\b", clean, re.IGNORECASE):
        return None
    if clean.lower() in ["products", "product", "produce", "produce,", "care", "care-"]:
        return None

    # If the token is predominantly just the label header itself, return None to trigger spatial neighbor search
    for kw in ["generic name", "common name", "commodity", "product name"]:
        if fuzz.ratio(clean.lower(), kw) >= 70:
            return None

    for kw in ["generic name", "common name", "commodity", "product name"]:
        idx = clean.lower().find(kw)
        if idx != -1:
            rem = clean[idx + len(kw):].strip(" :-\t|")
            if len(rem) >= 2 and rem.lower() not in ["u", "t", "g", "ml", "kg", "name", "model"]:
                return clean, rem
            return None

    if matched_kw:
        idx = clean.lower().find(matched_kw.lower())
        if idx != -1:
            rem = clean[idx + len(matched_kw):].strip(" :-\t|")
            if len(rem) >= 2 and rem.lower() not in ["u", "t", "g", "ml", "kg", "name", "model"]:
                return clean, rem
            return None

    if len(clean) >= 2 and clean.lower() not in ["u", "t", "g", "ml", "kg", "name", "generic name", "model", "products", "produce"]:
        return clean, clean
    return None




def parse_country_of_origin(text: str) -> Optional[Tuple[str, str]]:
    """
    Extracts country name (e.g. India, China, USA, Germany).
    Recognizes patterns: 'Made in India', 'Country of Origin: India', 'Product of India', 'Manufactured in India'.
    """
    clean = text.strip()
    match = re.search(
        r"(?:made\s+in|country\s+of\s+origin\s*:?|origin\s*:?|product\s+of|manufactured\s+in)\s*([A-Za-z\s]+)",
        clean,
        re.IGNORECASE,
    )
    if match:
        raw_country = match.group(1).strip()
        # Strip trailing punctuation or secondary address clauses
        country = re.split(r"[,;.\n\t]", raw_country)[0].strip()
        if len(country) >= 2:
            return match.group(0).strip(), country.title()
    return None


# Map field names to their specific value extractor functions
PARSERS = {
    "mrp": parse_mrp,
    "net_quantity": parse_net_quantity,
    "mfg_date": parse_date,
    "expiry_date": parse_date,
    "unit_sale_price": parse_unit_sale_price,
    "consumer_care": parse_consumer_care,
    "manufacturer_name": parse_manufacturer,
    "generic_name": parse_generic_name,
    "country_of_origin": parse_country_of_origin,
}


# ============================================================================
# Fuzzy Label Matching & Spatial Association
# ============================================================================

def match_field_label(text: str, threshold: float = 75.0) -> List[Tuple[str, float, str]]:
    """
    Fuzzy-matches text against FIELD_KEYWORDS using RapidFuzz partial_ratio.
    Returns list of (field_name, score, matched_keyword).
    """
    text_lower = text.lower().strip()
    
    # Reject short stop words and common storytelling/marketing prose from triggering label matches
    LABEL_STOP_WORDS = {
        "and", "by", "for", "with", "from", "the", "are", "have", "you", "our",
        "gift", "of", "to", "in", "on", "at", "see", "read", "care", "care-",
        "is", "a", "an", "all", "we", "us", "my", "your", "no", "not",
    }
    if text_lower in LABEL_STOP_WORDS or len(text_lower) < 3:
        return []

    MARKETING_WORDS = {
        "picked", "love", "finest", "produce", "farmer", "gift", "family",
        "seeds", "knowledge", "improve", "yield", "future", "rich", "land",
        "gathered", "precious", "story", "sweet", "tasty", "delicious",
    }
    tokens = set(re.findall(r"[a-z]+", text_lower))
    if tokens & MARKETING_WORDS:
        return []

    matches = []

    for field_name, keywords in FIELD_KEYWORDS.items():
        # Disambiguation guard 1: If text says 'mfg by', 'mktd by', 'manufactured by',
        # it is exclusively a manufacturer header, not a manufacturing date.
        if field_name == "mfg_date" and re.search(r"\b(?:mfg|mfd|manufactured|packed|mktd|mfr)\s*[,.:-]?\s*by\b", text_lower):
            continue

        # Disambiguation guard 2: Generic prose words like 'products', 'product', 'produce'
        # are not generic name declarations.
        if field_name == "generic_name" and text_lower in ["products", "product", "produce", "produce,", "care-"]:
            continue

        best_score = 0.0
        best_kw = ""
        for kw in keywords:
            # If text is much shorter than keyword, require token_set_ratio >= 70 to avoid accidental partial matches
            if len(text_lower) < len(kw) * 0.6:
                set_score = fuzz.token_set_ratio(kw, text_lower)
                if set_score < 70:
                    continue
            score = fuzz.partial_ratio(kw, text_lower)
            if score > best_score:
                best_score = score
                best_kw = kw
        if best_score >= threshold:
            matches.append((field_name, best_score, best_kw))

    # Sort descending by match score
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def merge_bounding_boxes(b1: BoundingBox, b2: BoundingBox) -> BoundingBox:
    """Merges two BoundingBoxes into an enclosing rectangle."""
    return BoundingBox(
        x_min=min(b1.x_min, b2.x_min),
        y_min=min(b1.y_min, b2.y_min),
        x_max=max(b1.x_max, b2.x_max),
        y_max=max(b1.y_max, b2.y_max),
    )


def find_spatial_neighbors(
    target_idx: int,
    ocr_results: List[Dict],
    max_horizontal_gap: int = 180,
    max_vertical_gap: int = 60,
) -> List[int]:
    """
    Finds OCR boxes spatially adjacent to the target box:
      1. Horizontally to the right on roughly the same line.
      2. Vertically immediately below (with tolerance for high-res images and slight bbox overlaps).
    """
    target = ocr_results[target_idx]
    t_box = target["bbox"]
    t_h = max(1, t_box.y_max - t_box.y_min)
    t_w = max(1, t_box.x_max - t_box.x_min)
    t_y_center = (t_box.y_min + t_box.y_max) / 2.0

    eff_h_gap = max(max_horizontal_gap, int(t_w * 1.5))
    eff_v_gap = max(max_vertical_gap, int(t_h * 1.5))

    neighbors = []

    for idx, cand in enumerate(ocr_results):
        if idx == target_idx:
            continue
        c_box = cand["bbox"]
        c_y_center = (c_box.y_min + c_box.y_max) / 2.0

        # Check Horizontal Neighbor (to the right on roughly same line)
        y_diff = abs(t_y_center - c_y_center)
        if y_diff < t_h * 0.7:
            x_gap = c_box.x_min - t_box.x_max
            if -10 <= x_gap <= eff_h_gap:
                dist = max(0, x_gap) + y_diff * 0.5
                neighbors.append((idx, dist))
                continue

        # Check Vertical Neighbor (below target, tolerating slight vertical overlap)
        if c_box.y_min >= t_box.y_min + t_h * 0.3 and c_box.y_min <= t_box.y_max + eff_v_gap:
            # Overlap in x
            overlap_x = max(0, min(t_box.x_max, c_box.x_max) - max(t_box.x_min, c_box.x_min))
            if overlap_x > min(t_w, (c_box.x_max - c_box.x_min)) * 0.2:
                dist = max(0, c_box.y_min - t_box.y_max) + 50.0
                neighbors.append((idx, dist))

    # Sort neighbors by proximity (closest adjacent token evaluated first)
    neighbors.sort(key=lambda item: item[1])
    return [item[0] for item in neighbors]


# ============================================================================
# Main Extraction Entrypoint
# ============================================================================

def extract_fields(ocr_results: List[Dict]) -> List[ExtractedField]:
    """
    Extracts mandatory and regulated packaging fields from OCR results.

    Pipeline:
      1. RapidFuzz label matching against FIELD_KEYWORDS.
      2. Tries value extraction within the same text line.
      3. If no value found, searches adjacent spatial neighbors (multi-box declarations).
      4. Validates format via field-specific regex.
      5. Computes composite confidence and returns List[ExtractedField].
    """
    if not ocr_results:
        return []

    candidates_by_field: Dict[str, List[ExtractedField]] = {k: [] for k in FIELD_KEYWORDS}

    for idx, item in enumerate(ocr_results):
        raw_text = item.get("text", "").strip()
        ocr_conf = float(item.get("confidence", 0.8))
        bbox: BoundingBox = item["bbox"]

        # Step 1: RapidFuzz label matching
        label_matches = match_field_label(raw_text, threshold=75.0)
        if not label_matches:
            # Check standalone values (e.g. pure MRP number, net qty, unit sale price, or contact phone/email)
            for standalone_field in ["mrp", "net_quantity", "unit_sale_price", "consumer_care"]:
                parser_fn = PARSERS[standalone_field]
                val_res = parser_fn(raw_text)
                if val_res:
                    raw_val, norm_val = val_res[0], val_res[1]
                    is_heur = bool(val_res[2]) if len(val_res) > 2 else False
                    cand_conf = round(ocr_conf * (0.75 if is_heur else 0.85), 4)
                    if standalone_field == "mrp" and (re.search(r"[₹{tT7]|(?:\/-)", raw_text) or norm_val):
                        cand_conf = max(0.85, cand_conf)

                    candidates_by_field[standalone_field].append(
                        ExtractedField(
                            field_name=standalone_field,
                            raw_ocr_text=raw_text,
                            normalized_value=norm_val,
                            confidence=cand_conf,
                            bbox=bbox,
                        )
                    )
            continue

        # Step 2: Attempt extraction for each matched label
        for field_name, fuzzy_score, matched_kw in label_matches:
            # Disambiguate: prevent date labels like "Manufactured On" or "Imported On" from matching manufacturer_name
            if field_name == "manufacturer_name" and re.search(r"\b(?:manufactured|mfg|pkd|packed|imported|imporled)\s+on\b", raw_text, re.IGNORECASE):
                continue


            parser_fn = PARSERS.get(field_name)
            if not parser_fn:
                continue

            # A) Try extracting value from the same line
            is_heuristic = False
            if field_name in ["manufacturer_name", "generic_name", "mrp", "net_quantity"]:
                val_res = parser_fn(raw_text, matched_kw)
            elif field_name == "consumer_care":
                cc_res = parse_consumer_care(raw_text)
                if cc_res:
                    val_res = (cc_res[0], cc_res[1])
                    is_heuristic = cc_res[2]
                else:
                    val_res = None
            else:
                val_res = parser_fn(raw_text)

            matched_bbox = bbox
            raw_matched_str = raw_text

            # B) If not found in same line, inspect spatial neighbors (horizontal or vertical table cells)
            if not val_res:
                neighbors = find_spatial_neighbors(idx, ocr_results)
                for n_idx in neighbors:
                    neighbor_item = ocr_results[n_idx]
                    n_text = neighbor_item.get("text", "").strip()

                    # For table value cells, the neighbor token IS the value
                    if field_name == "generic_name":
                        if (
                            len(n_text) >= 2
                            and n_text.lower() not in ["u", "t", "g", "ml", "kg", "name", "model", "generic name", "products", "produce"]
                            and not re.search(r"\b(?:fssai|lic|license|regd|reg\.?|batch|lot|iso|agmark)\b", n_text, re.IGNORECASE)
                        ):
                            n_res = (n_text, n_text)
                        else:
                            n_res = None
                    elif field_name == "manufacturer_name":
                        if (
                            len(n_text) >= 3
                            and not n_text.endswith("-")
                            and not re.search(r"\b(?:on|date|dt|model|mrp|pkd|name|care|produce|farmer)\b", n_text, re.IGNORECASE)
                            and not re.search(r"\d{2}[/-]?\d{2,4}", n_text)
                        ):
                            n_res = (n_text, n_text)
                        else:
                            n_res = None
                    elif field_name == "mrp":
                        n_res = parse_mrp(n_text, matched_kw=matched_kw or "mrp")
                    elif field_name == "net_quantity":
                        n_res = parse_net_quantity(n_text, matched_kw=matched_kw or "net quantity")
                    elif field_name == "consumer_care":
                        cc_res = parse_consumer_care(n_text)
                        if cc_res:
                            n_res = (cc_res[0], cc_res[1])
                            is_heuristic = cc_res[2]
                        else:
                            n_res = None
                    else:
                        n_res = parser_fn(n_text)

                    if n_res:
                        val_res = n_res
                        matched_bbox = merge_bounding_boxes(bbox, neighbor_item["bbox"])
                        raw_matched_str = f"{raw_text} {n_text}"
                        ocr_conf = (ocr_conf + float(neighbor_item.get("confidence", 0.8))) / 2.0
                        break

            # C) Additional lookahead for consumer care (often header is on line N, details on line N+1)
            if not val_res and field_name == "consumer_care":
                for next_idx in range(idx + 1, min(len(ocr_results), idx + 3)):
                    next_item = ocr_results[next_idx]
                    next_text = next_item.get("text", "").strip()
                    cc_next = parse_consumer_care(next_text)
                    if cc_next:
                        val_res = (cc_next[0], cc_next[1])
                        is_heuristic = cc_next[2]
                        matched_bbox = merge_bounding_boxes(bbox, next_item["bbox"])
                        raw_matched_str = f"{raw_text} {next_text}"
                        ocr_conf = (ocr_conf + float(next_item.get("confidence", 0.8))) / 2.0
                        break

            if val_res:
                raw_val, norm_val = val_res[0], val_res[1]
                # Calculate composite confidence
                composite_conf = min(
                    1.0,
                    round(0.35 * ocr_conf + 0.45 * (fuzzy_score / 100.0) + 0.20, 4)
                )
                # Apply Priority 3 heuristic recovery discount if applicable
                if is_heuristic:
                    composite_conf = round(composite_conf * 0.85, 4)

                candidates_by_field[field_name].append(
                    ExtractedField(
                        field_name=field_name,
                        raw_ocr_text=raw_matched_str,
                        normalized_value=norm_val,
                        confidence=composite_conf,
                        bbox=matched_bbox,
                    )
                )


                # If MRP line includes adjacent bracketed unit sale price, extract USP simultaneously
                if field_name == "mrp":
                    usp_res = parse_unit_sale_price(raw_matched_str)
                    if usp_res:
                        _, norm_usp = usp_res
                        candidates_by_field["unit_sale_price"].append(
                            ExtractedField(
                                field_name="unit_sale_price",
                                raw_ocr_text=raw_matched_str,
                                normalized_value=norm_usp,
                                confidence=composite_conf,
                                bbox=matched_bbox,
                            )
                        )

    # Step 2b: Chronological Date Cluster Resolution (MFD vs. Expiry/UBD)
    # When dates appear in an unlabeled thermal/inkjet cluster (e.g. '11/05/2024' followed by '10/05/2025'):
    # Statutory rule of nature: Manufacturing (MFD/MFG) chronologically precedes Expiry/Use By (UBD/EXP).
    existing_mfg = candidates_by_field.get("mfg_date", [])
    existing_exp = candidates_by_field.get("expiry_date", [])

    if not existing_mfg or not existing_exp:
        detected_dates: List[Tuple[ExtractedField, int]] = []
        seen_norms = set()

        for item in ocr_results:
            text = item.get("text", "").strip()
            conf = float(item.get("confidence", 0.8))
            date_res = parse_date(text)
            if date_res:
                raw_d, norm_d = date_res
                months_val = date_norm_to_months(norm_d)
                if months_val and norm_d not in seen_norms:
                    seen_norms.add(norm_d)
                    field_obj = ExtractedField(
                        field_name="date_candidate",
                        raw_ocr_text=raw_d,
                        normalized_value=norm_d,
                        confidence=round(conf * 0.85, 4),
                        bbox=item["bbox"],
                    )
                    detected_dates.append((field_obj, months_val))

        # Sort dates chronologically: earlier date is MFD, later date is Expiry/UBD
        detected_dates.sort(key=lambda x: x[1])

        if len(detected_dates) >= 2:
            earliest_field, earliest_m = detected_dates[0]
            latest_field, latest_m = detected_dates[-1]
            shelf_life_months = latest_m - earliest_m

            # Valid FMCG shelf-life is typically between 1 and 60 months
            if shelf_life_months >= 1:
                if not existing_mfg:
                    candidates_by_field["mfg_date"].append(
                        ExtractedField(
                            field_name="mfg_date",
                            raw_ocr_text=earliest_field.raw_ocr_text,
                            normalized_value=earliest_field.normalized_value,
                            confidence=max(0.85, earliest_field.confidence),
                            bbox=earliest_field.bbox,
                        )
                    )
                if not existing_exp:
                    candidates_by_field["expiry_date"].append(
                        ExtractedField(
                            field_name="expiry_date",
                            raw_ocr_text=latest_field.raw_ocr_text,
                            normalized_value=latest_field.normalized_value,
                            confidence=max(0.85, latest_field.confidence),
                            bbox=latest_field.bbox,
                        )
                    )
        elif len(detected_dates) == 1 and not existing_mfg:
            # Single standalone date defaults to mfg_date per Rule 6(1)(d)
            single_field, _ = detected_dates[0]
            candidates_by_field["mfg_date"].append(
                ExtractedField(
                    field_name="mfg_date",
                    raw_ocr_text=single_field.raw_ocr_text,
                    normalized_value=single_field.normalized_value,
                    confidence=round(single_field.confidence * 0.85, 4),
                    bbox=single_field.bbox,
                )
            )

    # Step 2c: Thermal/Inkjet Cluster MRP Resolution
    # On FMCG packages (bottles, jars, pouches), when an unlabeled date cluster is detected,
    # the line immediately above the manufacturing date (within 250px above) contains the retail price.
    existing_mrp = candidates_by_field.get("mrp", [])
    if not existing_mrp and candidates_by_field.get("mfg_date"):
        mfg_field = candidates_by_field["mfg_date"][0]
        if mfg_field.bbox:
            mfg_y = mfg_field.bbox.y_min
            mfg_x1 = mfg_field.bbox.x_min

            for item in ocr_results:
                b = item["bbox"]
                # Look for token immediately above MFG line (within 250px above, with x proximity)
                if 0 < (mfg_y - b.y_min) <= 250 and abs(b.x_min - mfg_x1) < 450:
                    text = item.get("text", "").strip()
                    # Skip date-like strings (e.g. '11/05/2024', '4705/2424')
                    if re.search(r"/\s*\d{2,4}", text):
                        continue
                    parsed_mrp = parse_mrp(text)
                    if not parsed_mrp:
                        # Only accept if it has an explicit currency marker, /- suffix, or >= 3 digits (not a calendar day 1-31)
                        m_num = re.search(r"\b([1-9][0-9]{1,4})\s*(?:\/-)?\b", text)
                        if m_num:
                            val_f = float(m_num.group(1))
                            has_curr_or_slash = bool(re.search(r"[₹{tT7]|(?:\/-)", text))
                            if (has_curr_or_slash and 10.0 <= val_f <= 50000.0) or (val_f > 31.0 and val_f <= 50000.0):
                                parsed_mrp = (m_num.group(0), f"{val_f:.2f}")
                    if parsed_mrp:
                        candidates_by_field["mrp"].append(
                            ExtractedField(
                                field_name="mrp",
                                raw_ocr_text=text,
                                normalized_value=parsed_mrp[1],
                                confidence=max(0.85, float(item.get("confidence", 0.8))),
                                bbox=b,
                            )
                        )
                        break

    # Step 3: Deduplicate fields (pick candidate with highest confidence)
    final_fields: List[ExtractedField] = []
    for field_name, candidates in candidates_by_field.items():
        if candidates:
            # Sort by confidence descending
            candidates.sort(key=lambda c: c.confidence, reverse=True)
            final_fields.append(candidates[0])

    return final_fields
