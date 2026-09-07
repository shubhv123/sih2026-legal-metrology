"""
Vision services package.
Exposes detection, preprocessing, OCR, extraction, and calibration modules.
"""

from app.services.vision.preprocessing import (
    decode_image,
    resize_to_max_dimension,
    to_grayscale,
    apply_clahe,
    apply_bilateral_filter,
    apply_adaptive_threshold,
    preprocess_for_ocr,
)
from app.services.vision.ocr import run_ocr, get_ocr_reader
from app.services.vision.extraction import extract_fields, FIELD_KEYWORDS

__all__ = [
    "decode_image",
    "resize_to_max_dimension",
    "to_grayscale",
    "apply_clahe",
    "apply_bilateral_filter",
    "apply_adaptive_threshold",
    "preprocess_for_ocr",
    "run_ocr",
    "get_ocr_reader",
    "extract_fields",
    "FIELD_KEYWORDS",
]
