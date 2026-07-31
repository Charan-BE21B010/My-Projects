"""OCR utilities for multilingual document images."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .text_utils import clean_text


def render_text_image(text: str, out_path: Path, width: int = 1100) -> Path:
    """Render document text onto an image to simulate scanned pages."""
    lines = [ln.strip() for ln in clean_text(text).splitlines() if ln.strip()]
    font = ImageFont.load_default()
    line_h = 18
    height = max(220, 40 + line_h * (len(lines) + 2))
    img = Image.new("RGB", (width, height), color=(252, 252, 248))
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        draw.text((24, y), line, fill=(20, 20, 20), font=font)
        y += line_h
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def ocr_image(image_path: Path) -> str:
    """
    Extract text from an image.
    Uses pytesseract when available. Falls back to paired .txt sidecar
    or matching file in data/documents for offline demos.
    """
    image_path = Path(image_path)
    try:
        import pytesseract
        from PIL import Image as PILImage

        img = PILImage.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng+hin+spa")
        if text and text.strip():
            return clean_text(text)
    except Exception:
        pass

    sidecar = image_path.with_suffix(".txt")
    if sidecar.exists():
        return clean_text(sidecar.read_text(encoding="utf-8"))

    docs = image_path.parents[1] / "documents"
    candidate = docs / f"{image_path.stem}.txt"
    if candidate.exists():
        return clean_text(candidate.read_text(encoding="utf-8"))

    raise FileNotFoundError(f"Could not OCR or find text for {image_path}")


def load_document_text(path: Path) -> str:
    path = Path(path)
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        return ocr_image(path)
    return clean_text(path.read_text(encoding="utf-8"))
