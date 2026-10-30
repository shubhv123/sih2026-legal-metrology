"""
Vision services package.
Exposes detection, preprocessing, OCR, extraction, and calibration modules.
"""

# Guarded imports for preprocessing (requires cv2 which may not be available in test env)
try:
    from .preprocessing import (
        decode_image,
        resize_to_max_dimension,
        to_grayscale,
        apply_clahe,
        apply_bilateral_filter,
        apply_adaptive_threshold,
        preprocess_for_ocr,
    )
    _PREPROCESSING_AVAILABLE = True
except ImportError:
    # Provide stubs to avoid breaking __all__ and downstream imports
    decode_image = None
    resize_to_max_dimension = None
    to_grayscale = None
    apply_clahe = None
    apply_bilateral_filter = None
    apply_adaptive_threshold = None
    preprocess_for_ocr = None
    _PREPROCESSING_AVAILABLE = False

from .ocr import run_ocr, get_ocr_reader
from .extraction import extract_fields, FIELD_KEYWORDS

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
