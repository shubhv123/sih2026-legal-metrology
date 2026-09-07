"""
Unit tests for vision preprocessing module.
Tests image decoding (including EXIF orientation), max-dimension resizing,
grayscale conversion, CLAHE contrast equalization, bilateral denoising,
and Gaussian adaptive thresholding.
"""

import io
import pytest
import numpy as np
import cv2
from PIL import Image

from app.services.vision.preprocessing import (
    decode_image,
    resize_to_max_dimension,
    to_grayscale,
    apply_clahe,
    apply_bilateral_filter,
    apply_adaptive_threshold,
    preprocess_for_ocr,
)


def create_synthetic_image(height: int = 120, width: int = 240, channels: int = 3) -> np.ndarray:
    """Helper to generate a reproducible test image with gradient & text."""
    img = np.zeros((height, width, channels), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            val = (i + j) % 256
            if channels == 3:
                img[i, j] = [val, 255 - val, (val * 2) % 256]
            else:
                img[i, j] = val
    cv2.putText(img, "TEST", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    return img


def test_decode_image_valid():
    """Verify standard JPEG bytes decode to expected BGR array."""
    synthetic = create_synthetic_image(100, 200, 3)
    success, buffer = cv2.imencode(".jpg", synthetic)
    assert success

    decoded = decode_image(buffer.tobytes())
    assert decoded is not None
    assert decoded.shape == (100, 200, 3)
    assert decoded.dtype == np.uint8


def test_decode_image_exif_orientation():
    """
    Verify that cv2.IMREAD_COLOR auto-applies EXIF orientation flags from smartphone cameras.
    
    A 300 (W) x 150 (H) image with EXIF Orientation=6 (90-deg CW rotation)
    must decode as 150 (W) x 300 (H) portrait.
    """
    raw_img = Image.new("RGB", (300, 150), color=(128, 64, 32))
    exif = raw_img.getexif()
    exif[0x0112] = 6  # Orientation = 6
    
    buf = io.BytesIO()
    raw_img.save(buf, format="JPEG", exif=exif)
    jpeg_bytes = buf.getvalue()

    decoded = decode_image(jpeg_bytes)
    assert decoded is not None
    assert decoded.shape[0] == 300, f"Expected height=300 after EXIF auto-rotation, got {decoded.shape[0]}"
    assert decoded.shape[1] == 150, f"Expected width=150 after EXIF auto-rotation, got {decoded.shape[1]}"


def test_decode_image_empty_and_corrupt():
    """Verify ValueError is raised on empty or corrupted bytes."""
    with pytest.raises(ValueError, match="Cannot decode empty image bytes"):
        decode_image(b"")

    with pytest.raises(ValueError, match="Failed to decode image from bytes"):
        decode_image(b"NOT_A_REAL_IMAGE_DATA_CORRUPT")


def test_resize_to_max_dimension():
    """Verify large images are downscaled preserving aspect ratio, and smaller images are untouched."""
    # Image larger than max_dim (3000 x 2000 -> max 1600 on longest edge)
    large_img = np.zeros((2000, 3000, 3), dtype=np.uint8)
    resized = resize_to_max_dimension(large_img, max_dim=1600)
    assert resized.shape[1] == 1600  # width capped at 1600
    assert resized.shape[0] == int(round(2000 * (1600 / 3000)))  # height scaled proportionally ~1067
    assert resized.dtype == np.uint8

    # Image smaller than max_dim should remain unchanged
    small_img = np.zeros((400, 600, 3), dtype=np.uint8)
    untouched = resize_to_max_dimension(small_img, max_dim=1600)
    assert untouched.shape == (400, 600, 3)


def test_to_grayscale():
    """Verify color images are converted to 1-channel 8-bit grayscale."""
    bgr = create_synthetic_image(100, 150, 3)
    gray = to_grayscale(bgr)
    assert gray.shape == (100, 150)
    assert len(gray.shape) == 2
    assert gray.dtype == np.uint8

    # Passing already grayscale image should return as-is
    gray_again = to_grayscale(gray)
    assert gray_again.shape == (100, 150)


def test_apply_clahe_grayscale_and_color():
    """Verify CLAHE on both single-channel grayscale and 3-channel color."""
    bgr = create_synthetic_image(100, 150, 3)
    gray = to_grayscale(bgr)

    # Grayscale CLAHE
    clahe_gray = apply_clahe(gray, clip_limit=2.0)
    assert clahe_gray.shape == (100, 150)
    assert clahe_gray.dtype == np.uint8

    # Color CLAHE (LAB space lightness normalization)
    clahe_color = apply_clahe(bgr, clip_limit=2.0)
    assert clahe_color.shape == (100, 150, 3)
    assert clahe_color.dtype == np.uint8


def test_apply_bilateral_filter():
    """Verify bilateral filter preserves dimensions while denoising."""
    bgr = create_synthetic_image(100, 150, 3)
    denoised = apply_bilateral_filter(bgr, d=7, sigma_color=50.0, sigma_space=50.0)
    assert denoised.shape == (100, 150, 3)
    assert denoised.dtype == np.uint8


def test_apply_adaptive_threshold():
    """Verify Gaussian adaptive thresholding creates binary output with values in {0, 255}."""
    bgr = create_synthetic_image(100, 150, 3)
    thresh = apply_adaptive_threshold(bgr, block_size=11, c=2)
    assert thresh.shape == (100, 150)
    assert thresh.dtype == np.uint8
    unique_vals = set(np.unique(thresh))
    assert unique_vals.issubset({0, 255}), f"Returned non-binary values: {unique_vals}"


def test_preprocess_for_ocr():
    """Verify the orchestrator produces all 5 standard image variations with chaining."""
    bgr = create_synthetic_image(100, 200, 3)
    stages = preprocess_for_ocr(bgr, max_dim=1600)

    assert "original" in stages
    assert "gray" in stages
    assert "clahe" in stages
    assert "denoised" in stages
    assert "binary" in stages

    assert stages["original"].shape == (100, 200, 3)
    assert stages["gray"].shape == (100, 200)
    assert stages["clahe"].shape == (100, 200)
    assert stages["denoised"].shape == (100, 200)
    assert stages["binary"].shape == (100, 200)
