"""
Owner: SHUBH

Dual calibration per the plan:
 - PRIMARY: ArUco marker (known physical dimensions, robust to perspective)
 - FALLBACK: user-selected known-size object (e.g. a coin) with its
   real-world size passed in via the API (known_object_size_mm)

Either path produces mm_per_pixel, which is then used to convert
every extracted field's bbox height into a real-world mm measurement.
"""

from typing import Optional
import numpy as np

from app.schemas.scan import CalibrationMethod


def calibrate_aruco(image: np.ndarray) -> Optional[float]:
    """
    TODO(shubh):
    1. cv2.aruco.detectMarkers() to find the marker in frame.
    2. Marker's real-world side length is known/fixed (print it at a
       fixed size, e.g. 30mm) - compute mm_per_pixel from detected
       marker's pixel side length.
    3. Return None if no marker detected (caller falls back to
       known-object method, or flags REVIEW_REQUIRED on font checks).
    """
    return None


def calibrate_known_object(
    image: np.ndarray,
    object_bbox_px_height: float,
    known_size_mm: float,
) -> float:
    """
    Fallback path: user selects/crops a reference object of known size
    in the image (e.g. a coin, known_size_mm=25 for a ₹10 coin's diameter).
    Simple ratio - no perspective correction attempted for the demo.
    """
    return known_size_mm / object_bbox_px_height


def get_mm_per_pixel(
    image: np.ndarray,
    method: CalibrationMethod,
    known_object_size_mm: Optional[float] = None,
    known_object_bbox_px_height: Optional[float] = None,
) -> Optional[float]:
    """Single entrypoint the scan router calls - routes to the right method."""
    if method == CalibrationMethod.ARUCO:
        result = calibrate_aruco(image)
        if result is not None:
            return result
        # ArUco not found - could auto-fallback here, or let caller decide
        return None

    if method == CalibrationMethod.KNOWN_OBJECT:
        if known_object_size_mm is None or known_object_bbox_px_height is None:
            return None
        return calibrate_known_object(
            image, known_object_bbox_px_height, known_object_size_mm
        )

    return None  # CalibrationMethod.NONE - font checks will be skipped/REVIEW_REQUIRED
