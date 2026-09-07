"""
Unit tests for fuzzy-matching and regex field extraction pipeline.
Tests RapidFuzz label matching, date normalization (day-dropping and separator tolerance),
multi-box spatial association, and sample image extraction.
"""

from pathlib import Path
import pytest
import cv2

from app.services.vision.ocr import run_ocr
from app.services.vision.extraction import extract_fields, parse_date, parse_mrp, parse_net_quantity
from app.schemas.scan import BoundingBox, ExtractedField

SAMPLE_IMAGES_DIR = Path(__file__).parent / "sample_images"


@pytest.fixture(scope="module")
def compliant_label():
    img_path = SAMPLE_IMAGES_DIR / "compliant_label.jpg"
    img = cv2.imread(str(img_path))
    assert img is not None, f"Sample image not found at {img_path}"
    return img


def test_extract_fields_from_sample_image(compliant_label):
    """
    Test 1: Run EasyOCR on the compliant synthetic label and verify
    that extract_fields extracts all core mandatory declarations.
    """
    ocr_results = run_ocr(compliant_label, use_clahe=True)
    assert len(ocr_results) > 0

    extracted = extract_fields(ocr_results)
    assert len(extracted) >= 4, f"Expected at least 4 mandatory fields, got: {[e.field_name for e in extracted]}"

    fields_dict = {f.field_name: f for f in extracted}

    # Verify Net Quantity
    assert "net_quantity" in fields_dict
    assert "500" in fields_dict["net_quantity"].normalized_value
    assert "g" in fields_dict["net_quantity"].normalized_value

    # Verify MRP
    assert "mrp" in fields_dict
    assert "149" in fields_dict["mrp"].normalized_value

    # Verify Mfg Date
    assert "mfg_date" in fields_dict
    assert "08/2026" in fields_dict["mfg_date"].normalized_value

    # Verify Manufacturer Name
    assert "manufacturer_name" in fields_dict
    assert len(fields_dict["manufacturer_name"].normalized_value) > 5

    # Verify each ExtractedField conforms to schema
    for field in extracted:
        assert isinstance(field, ExtractedField)
        assert 0.0 <= field.confidence <= 1.0
        assert field.bbox.x_min < field.bbox.x_max
        assert field.bbox.y_min < field.bbox.y_max


def test_fuzzy_matching_ocr_typos():
    """
    Test 2: Verify RapidFuzz tolerates common OCR typos in field labels
    that raw regex alone would miss.
    """
    simulated_ocr = [
        {
            "text": "M8P Rs. 199.00",  # 'MRP' read as 'M8P'
            "confidence": 0.85,
            "bbox": BoundingBox(x_min=10, y_min=10, x_max=120, y_max=35),
        },
        {
            "text": "Nel Wt 250 g",  # 'Net' read as 'Nel'
            "confidence": 0.82,
            "bbox": BoundingBox(x_min=10, y_min=40, x_max=110, y_max=65),
        },
        {
            "text": "Mtg Date: 11/2025",  # 'Mfg' read as 'Mtg'
            "confidence": 0.80,
            "bbox": BoundingBox(x_min=10, y_min=70, x_max=140, y_max=95),
        },
        {
            "text": "Exp Date: 12-2027",  # Expiry date
            "confidence": 0.88,
            "bbox": BoundingBox(x_min=10, y_min=100, x_max=130, y_max=125),
        },
        {
            "text": "Mid By: Apex Organic Foods Ltd, Delhi",  # 'Mfd' read as 'Mid'
            "confidence": 0.79,
            "bbox": BoundingBox(x_min=10, y_min=130, x_max=250, y_max=155),
        },
        {
            "text": "Helpllne: 1800-222-3333",  # 'Helpline' with double 'l'
            "confidence": 0.81,
            "bbox": BoundingBox(x_min=10, y_min=160, x_max=200, y_max=185),
        },
        {
            "text": "U.S.P Rs 0.80/g",
            "confidence": 0.85,
            "bbox": BoundingBox(x_min=10, y_min=190, x_max=130, y_max=215),
        }
    ]

    extracted = extract_fields(simulated_ocr)
    fields_dict = {f.field_name: f for f in extracted}

    assert "mrp" in fields_dict
    assert fields_dict["mrp"].normalized_value == "199.00"

    assert "net_quantity" in fields_dict
    assert fields_dict["net_quantity"].normalized_value == "250 g"

    assert "mfg_date" in fields_dict
    assert fields_dict["mfg_date"].normalized_value == "11/2025"

    assert "expiry_date" in fields_dict
    assert fields_dict["expiry_date"].normalized_value == "12/2027"

    assert "manufacturer_name" in fields_dict
    assert "Apex Organic Foods" in fields_dict["manufacturer_name"].normalized_value

    assert "consumer_care" in fields_dict
    assert "1800-222-3333" in fields_dict["consumer_care"].normalized_value

    assert "unit_sale_price" in fields_dict
    assert "0.80 / g" in fields_dict["unit_sale_price"].normalized_value


def test_date_normalization_variations():
    """
    Test 3: Verify flexible date parsing:
    - Accepts both '/' and '-' and '.' separators.
    - Full DD-MM-YYYY dates are normalized to MM/YYYY per Rule 6(1)(d).
    - 2-digit years (YY) are correctly converted to 20YY.
    """
    # DD/MM/YYYY -> MM/YYYY
    res1 = parse_date("15/08/2026")
    assert res1 is not None
    assert res1[1] == "08/2026"

    # DD-MM-YY -> MM/YYYY
    res2 = parse_date("25-04-26")
    assert res2 is not None
    assert res2[1] == "04/2026"

    # MM-YYYY -> MM/YYYY
    res3 = parse_date("09-2025")
    assert res3 is not None
    assert res3[1] == "09/2025"

    # Textual month: "Aug-2026"
    res4 = parse_date("Aug-2026")
    assert res4 is not None
    assert res4[1] == "08/2026"


def test_multibox_adjacent_value_extraction():
    """
    Test 4: Multi-box spatial association:
    Box 1 contains label keyword ('MRP:'), adjacent Box 2 contains value ('Rs. 499.00').
    Verify they are merged into one ExtractedField covering the full declaration.
    """
    simulated_boxes = [
        {
            "text": "MRP:",
            "confidence": 0.90,
            "bbox": BoundingBox(x_min=20, y_min=100, x_max=80, y_max=130),
        },
        {
            "text": "Rs. 499.00",
            "confidence": 0.92,
            "bbox": BoundingBox(x_min=90, y_min=100, x_max=180, y_max=130),
        },
    ]

    extracted = extract_fields(simulated_boxes)
    assert len(extracted) == 1
    mrp_field = extracted[0]

    assert mrp_field.field_name == "mrp"
    assert mrp_field.normalized_value == "499.00"
    assert "MRP" in mrp_field.raw_ocr_text and "499.00" in mrp_field.raw_ocr_text

    # Bounding box should span from Box 1 x_min (20) to Box 2 x_max (180)
    assert mrp_field.bbox.x_min == 20
    assert mrp_field.bbox.x_max == 180


def test_empty_and_corrupt_inputs():
    """Test 5: Edge cases return empty list without throwing errors."""
    assert extract_fields([]) == []
    assert extract_fields([{"text": "xyz123 lorem ipsum", "confidence": 0.5, "bbox": BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)}]) == []


def test_mrp_comma_parsing_and_no_digit_truncation():
    """
    Priority 1 Test: Thousands comma support (₹2,999.00 -> 2999.00)
    and ensure prices legitimately starting with 2 or 7 (e.g. ₹250.00, ₹799.00)
    never have their leading digits stripped or corrupted.
    """
    from app.services.vision.extraction import parse_mrp

    # Comma-separated thousands
    res_thousands = parse_mrp("MRP: ₹2,999.00", matched_kw="mrp")
    assert res_thousands is not None
    assert res_thousands[1] == "2999.00"

    # Prices starting with 2
    res_250 = parse_mrp("MRP: ₹250.00", matched_kw="mrp")
    assert res_250 is not None
    assert res_250[1] == "250.00"

    # Prices starting with 7
    res_799 = parse_mrp("MRP: Rs. 799.00", matched_kw="mrp")
    assert res_799 is not None
    assert res_799[1] == "799.00"


def test_consumer_care_normalization_and_heuristic_discount():
    """
    Priority 3 Test: Space before TLD normalized to dot ('enquiry@zebronics com' -> 'enquiry@zebronics.com')
    with heuristic confidence discount applied.
    Also tests phone number with interior spaces (044-4000 0004).
    """
    from app.services.vision.extraction import parse_consumer_care

    # Normal clean email + landline with spaces
    cc_clean = parse_consumer_care("Contact: 044-4000 0004, support@example.com")
    assert cc_clean is not None
    assert "044-40000004" in cc_clean[1]
    assert "support@example.com" in cc_clean[1]
    assert cc_clean[2] is False  # not heuristic

    # Space-corrupted TLD email
    cc_space = parse_consumer_care("For complaints: enquiry@zebronics com")
    assert cc_space is not None
    assert "enquiry@zebronics.com" in cc_space[1]
    assert cc_space[2] is True  # heuristic recovery flagged

    # Verify discount applied in extract_fields
    simulated_boxes = [
        {
            "text": "Consumer Care: enquiry@zebronics com",
            "confidence": 0.90,
            "bbox": BoundingBox(x_min=10, y_min=10, x_max=200, y_max=30),
        }
    ]
    extracted = extract_fields(simulated_boxes)
    assert len(extracted) == 1
    assert extracted[0].normalized_value == "enquiry@zebronics.com"
    # Composite without discount: 0.35*0.90 + 0.45*1.0 + 0.20 = 0.965. With 0.85 discount: ~0.8203
    assert extracted[0].confidence < 0.85


def test_chronological_date_cluster_and_unlabeled_price():
    """
    Test:
      1. Unlabeled price parsing with currency symbol or trailing slash-dash (₹ 320/-, 320/-).
      2. Chronological date cluster resolution: earlier date = mfg_date, later date = expiry_date.
      3. Keyword aliases: 'mfd' & 'mfg' both match mfg_date, 'ubd' & 'use by' match expiry_date.
    """
    from app.services.vision.extraction import parse_mrp, match_field_label

    # 1. Unlabeled price with slash-dash
    res_slash = parse_mrp("₹ 320/-")
    assert res_slash is not None
    assert res_slash[1] == "320.00"

    res_bare_slash = parse_mrp("320/-")
    assert res_bare_slash is not None
    assert res_bare_slash[1] == "320.00"

    # 2. Keyword aliases
    mfd_match = match_field_label("MFD: 11/05/2024")
    assert any(m[0] == "mfg_date" for m in mfd_match)

    mfg_match = match_field_label("MFG: 11/05/2024")
    assert any(m[0] == "mfg_date" for m in mfg_match)

    ubd_match = match_field_label("UBD: 10/05/2025")
    assert any(m[0] == "expiry_date" for m in ubd_match)

    useby_match = match_field_label("USE BY: 10/05/2025")
    assert any(m[0] == "expiry_date" for m in useby_match)

    # 3. Chronological Date Cluster (Unlabeled dates stacked vertically)
    simulated_cluster = [
        {
            "text": "₹ 320/-",
            "confidence": 0.88,
            "bbox": BoundingBox(x_min=100, y_min=200, x_max=250, y_max=230),
        },
        {
            "text": "11/05/2024",  # Earlier date -> MFD
            "confidence": 0.85,
            "bbox": BoundingBox(x_min=100, y_min=240, x_max=250, y_max=270),
        },
        {
            "text": "10/05/2025",  # Later date -> Expiry / UBD
            "confidence": 0.85,
            "bbox": BoundingBox(x_min=100, y_min=280, x_max=250, y_max=310),
        },
    ]

    extracted = extract_fields(simulated_cluster)
    extracted_dict = {f.field_name: f for f in extracted}

    assert "mrp" in extracted_dict
    assert extracted_dict["mrp"].normalized_value == "320.00"

    assert "mfg_date" in extracted_dict
    assert extracted_dict["mfg_date"].normalized_value == "05/2024"

    assert "expiry_date" in extracted_dict
    assert extracted_dict["expiry_date"].normalized_value == "05/2025"


