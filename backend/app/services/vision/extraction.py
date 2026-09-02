"""
Owner: SHUBH

Pipeline: EasyOCR raw text + bboxes -> normalize -> fuzzy match against
known field keywords -> regex validate the value -> confidence score.
This is the "item 3" fix from the review - NOT raw regex alone.
"""

from typing import List
import numpy as np

from app.schemas.scan import ExtractedField, BoundingBox

# Keywords each field is fuzzy-matched against (case-insensitive).
# TODO(parul/shubh): expand this list based on real label variations
# seen during dataset collection (e.g. "M.R.P.", "Maximum Retail Price").
FIELD_KEYWORDS = {
    "mrp": ["mrp", "maximum retail price", "m.r.p"],
    "net_quantity": ["net wt", "net weight", "net qty", "net quantity", "contents"],
    "manufacturer_name": ["mfd by", "manufactured by", "marketed by", "packed by"],
    "mfg_date": ["mfg date", "mfg", "pkd on", "packed on"],
    "consumer_care": ["consumer care", "customer care", "helpline", "contact us"],
    "country_of_origin": ["country of origin", "made in"],
}

_easyocr_reader = None


def _get_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


def run_ocr(image: np.ndarray) -> List[dict]:
    """
    Returns raw EasyOCR output: list of {text, bbox, confidence}.
    TODO(shubh): call reader.readtext(image), normalize the bbox
    format (EasyOCR returns 4 corner points, we want x_min/y_min/x_max/y_max).
    """
    reader = _get_reader()
    raw_results = reader.readtext(image)
    # TODO: convert EasyOCR's polygon bboxes to BoundingBox rectangles
    return []


def extract_fields(ocr_results: List[dict]) -> List[ExtractedField]:
    """
    TODO(shubh):
    1. For each OCR text chunk, fuzzy-match against FIELD_KEYWORDS
       (use rapidfuzz.fuzz.partial_ratio, threshold ~80).
    2. Once a field label is matched, look at nearby text (same line /
       next token) for the VALUE, then regex-validate the value format
       per field (e.g. mrp -> r'\\d+(\\.\\d{1,2})?', net_quantity ->
       r'\\d+\\s*(g|kg|ml|l)\\b').
    3. Return one ExtractedField per matched field.
    """
    return []
