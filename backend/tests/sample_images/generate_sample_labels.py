"""
Helper script to generate synthetic packaging label images for unit testing OCR.
Creates compliant_label.jpg and faded_label.jpg in backend/tests/sample_images/.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_sample_labels():
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Compliant Label (White background, black text, clean layout)
    h, w = 400, 600
    img = Image.new('RGB', (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try to load a default font
    try:
        font_large = ImageFont.truetype("DejaVuSans.ttf", 24)
        font_medium = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
        font_tiny = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()

    # Outer border
    draw.rectangle([10, 10, w - 10, h - 10], outline=(0, 0, 0), width=2)
    # Header
    draw.text((30, 50), "GREENROOTS WHOLE WHEAT", font=font_large, fill=(0, 0, 0))
    draw.line([(30, 65), (w - 30, 65)], fill=(100, 100, 100), width=1)

    # Declarations
    draw.text((30, 110), "Net Weight: 500 g", font=font_medium, fill=(0, 0, 0))
    draw.text((30, 160), "MRP Rs. 149.00", font=font_medium, fill=(0, 0, 0))
    draw.text((240, 160), "(Incl. of all taxes)", font=font_small, fill=(50, 50, 50))
    draw.text((30, 210), "Mfg Date: 08/2026", font=font_medium, fill=(0, 0, 0))
    draw.text((30, 260), "Mfd By: GreenRoots Agro Ltd, Mumbai 400001", font=font_tiny, fill=(0, 0, 0))
    draw.text((30, 310), "Consumer Care: 1800-200-3000, help@greenroots.in", font=font_tiny, fill=(0, 0, 0))

    compliant_path = out_dir / "compliant_label.jpg"
    img.save(str(compliant_path), "JPEG")

    # 2. Faded Label (Lower contrast, gray text on off-white background)
    faded = Image.new('RGB', (w, h), (230, 230, 230))
    draw_faded = ImageDraw.Draw(faded)

    draw_faded.rectangle([10, 10, w - 10, h - 10], outline=(180, 180, 180), width=2)
    draw_faded.text((30, 50), "FADED BRAND FLOUR", font=font_large, fill=(140, 140, 140))
    draw_faded.text((30, 110), "Net Weight: 1 kg", font=font_medium, fill=(140, 140, 140))
    draw_faded.text((30, 160), "MRP Rs. 85.00", font=font_medium, fill=(140, 140, 140))
    draw_faded.text((30, 210), "Mfg Date: 09/2026", font=font_medium, fill=(140, 140, 140))

    faded_path = out_dir / "faded_label.jpg"
    faded.save(str(faded_path), "JPEG")

    print(f"Generated sample labels:\n - {compliant_path}\n - {faded_path}")


if __name__ == "__main__":
    create_sample_labels()
