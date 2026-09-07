"""
Owner: SHUBH

Image Preprocessing Service for SIH26034 Legal Metrology Compliance Checker.
Provides deterministic OpenCV transformations (decoding with EXIF orientation,
downscaling, grayscale conversion, CLAHE contrast enhancement, bilateral denoising,
and Gaussian adaptive binarization).

Important Design & Usage Notes:
- EasyOCR Input: Use 'clahe' or 'gray'. EasyOCR is a deep learning model (CRAFT + CRNN)
  trained on natural scene images. Hard binarization ('binary') discards stroke
  gradients and often harms EasyOCR accuracy.
- OpenCV Contour Input: Use 'binary'. Hard binarization provides crisp edges
  optimal for contour extraction in PDP isolation (detection.py).
"""

from typing import Tuple, Dict
import cv2
import numpy as np


def decode_image(image_bytes: bytes) -> np.ndarray:
    """
    Decodes raw image bytes into an 8-bit BGR OpenCV NumPy array.
    
    Uses cv2.IMREAD_COLOR explicitly to ensure OpenCV automatically applies
    EXIF orientation flags (e.g. from smartphone portrait photography).
    
    Raises:
        ValueError: if image_bytes is empty, corrupt, or cannot be decoded.
    """
    if not image_bytes:
        raise ValueError("Cannot decode empty image bytes.")

    np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    # cv2.IMREAD_COLOR auto-rotates according to EXIF orientation metadata
    decoded = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)

    if decoded is None or decoded.size == 0:
        raise ValueError("Failed to decode image from bytes. File may be corrupt or an unsupported format.")

    return decoded


def resize_to_max_dimension(image: np.ndarray, max_dim: int = 1600) -> np.ndarray:
    """
    Downscales the image so its longest dimension does not exceed max_dim,
    preserving the aspect ratio.
    
    Prevents 12MP+ smartphone photos from stalling the demo pipeline during
    bilateral filtering, CLAHE, and EasyOCR inference.
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image provided to resize_to_max_dimension.")

    h, w = image.shape[:2]
    longest = max(h, w)

    if longest <= max_dim:
        return image

    scale = max_dim / float(longest)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Converts a color image to single-channel 8-bit grayscale.
    Returns the array unchanged if it is already single-channel.
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image provided to to_grayscale.")

    if len(image.shape) == 2:
        return image
    elif image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise ValueError(f"Unsupported number of image channels: {image.shape[2]}")


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Contrast Limited Adaptive Histogram Equalization (CLAHE).
    Normalizes localized contrast to mitigate phone flash glare, glossy packaging
    reflections, and faint ink declarations.

    - For 1-channel (grayscale): applies CLAHE directly.
    - For 3-channel (BGR): converts to LAB color space, equalizes the L (Lightness)
      channel, and converts back to BGR to avoid color shifts.
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image provided to apply_clahe.")

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    if len(image.shape) == 2:
        return clahe.apply(image)
    elif len(image.shape) == 3 and image.shape[2] == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_equalized = clahe.apply(l_channel)
        merged_lab = cv2.merge((l_equalized, a_channel, b_channel))
        return cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)
    else:
        gray = to_grayscale(image)
        return clahe.apply(gray)


def apply_bilateral_filter(
    image: np.ndarray,
    d: int = 9,
    sigma_color: float = 50.0,
    sigma_space: float = 50.0,
) -> np.ndarray:
    """
    Applies a bilateral filter to smooth textures and reduce camera sensor noise
    while preserving sharp character edges critical for OCR and calibration.
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image provided to apply_bilateral_filter.")

    return cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)


def apply_adaptive_threshold(
    image: np.ndarray,
    block_size: int = 11,
    c: int = 2,
) -> np.ndarray:
    """
    Applies Gaussian adaptive binarization to produce a high-contrast binary mask.
    Used primarily for contour isolation in the OpenCV PDP fallback detector.
    
    (Note: Feed 'clahe' or 'gray' to EasyOCR rather than this binary output,
    as hard binarization discards stroke gradients used by neural text recognizers).
    """
    gray = to_grayscale(image)

    # Ensure block_size is odd and >= 3 for OpenCV adaptive thresholding
    if block_size % 2 == 0:
        block_size += 1
    if block_size < 3:
        block_size = 3

    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
    )


def preprocess_for_ocr(image: np.ndarray, max_dim: int = 1600) -> Dict[str, np.ndarray]:
    """
    Orchestrates the preprocessing pipeline and returns keyed transformation stages.

    Chaining order:
      1. resized: Rescales image so max(H, W) <= max_dim (guards live demo speed).
      2. gray: Converted from resized color image.
      3. clahe: Contrast-equalized from gray (RECOMMENDED INPUT for EasyOCR).
      4. denoised: Bilateral filter applied on clahe output.
      5. binary: Gaussian adaptive threshold applied on denoised output
                 (RECOMMENDED INPUT for contour-based PDP detection).
    """
    # Step 1: Cap resolution for fast CPU inference on demo day
    resized = resize_to_max_dimension(image, max_dim=max_dim)

    # Step 2: Grayscale
    gray = to_grayscale(resized)

    # Step 3: CLAHE contrast equalization (recommended for EasyOCR)
    clahe_gray = apply_clahe(gray, clip_limit=2.0, tile_grid_size=(8, 8))

    # Step 4: Bilateral denoising chained on CLAHE output
    denoised = apply_bilateral_filter(clahe_gray, d=9, sigma_color=50.0, sigma_space=50.0)

    # Step 5: Gaussian adaptive binarization chained on denoised output (for contour PDP isolation)
    binary = apply_adaptive_threshold(denoised, block_size=11, c=2)

    return {
        "original": resized,
        "gray": gray,
        "clahe": clahe_gray,
        "denoised": denoised,
        "binary": binary,
    }
