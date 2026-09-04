"""
Helper script to generate synthetic packaging label images for unit testing OCR.
Creates compliant_label.jpg and faded_label.jpg in backend/tests/sample_images/.
"""

from pathlib import Path
import cv2
import numpy as np


def create_sample_labels():
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compliant Label (White background, black text, clean layout)
    h, w = 400, 600
    img = np.full((h, w, 3), 255, dtype=np.uint8)

    # Outer border
    cv2.rectangle(img, (10, 10), (w - 10, h - 10), (0, 0, 0), 2)
    # Header
    cv2.putText(img, "GREENROOTS WHOLE WHEAT", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.line(img, (30, 65), (w - 30, 65), (100, 100, 100), 1)

    # Declarations
    cv2.putText(img, "Net Weight: 500 g", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs. 149.00", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "(Incl. of all taxes)", (240, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(img, "Mfg Date: 08/2026", (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "Mfd By: GreenRoots Agro Ltd, Mumbai 400001", (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
    cv2.putText(img, "Consumer Care: 1800-200-3000, help@greenroots.in", (30, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

    compliant_path = out_dir / "compliant_label.jpg"
    cv2.imwrite(str(compliant_path), img)

    # 2. Faded Label (Lower contrast, gray text on off-white background)
    faded = np.full((h, w, 3), 230, dtype=np.uint8)
    cv2.rectangle(faded, (10, 10), (w - 10, h - 10), (180, 180, 180), 2)
    cv2.putText(faded, "FADED BRAND FLOUR", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (140, 140, 140), 2)
    cv2.putText(faded, "Net Weight: 1 kg", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 140, 140), 2)
    cv2.putText(faded, "MRP Rs. 85.00", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 140, 140), 2)
    cv2.putText(faded, "Mfg Date: 09/2026", (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 140, 140), 2)

    faded_path = out_dir / "faded_label.jpg"
    cv2.imwrite(str(faded_path), faded)

    print(f"Generated sample labels:\n - {compliant_path}\n - {faded_path}")


if __name__ == "__main__":
    create_sample_labels()
