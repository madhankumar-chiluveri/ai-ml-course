"""Package generated pages as a LinkedIn PDF and Instagram carousel."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
slides = []
for number in range(1, 6):
    source = ROOT / "source" / f"slide-{number:02d}-native.png"
    output = ROOT / f"slide-{number:02d}.png"
    with Image.open(source) as image:
        image.convert("RGB").resize((2160, 2700), Image.Resampling.LANCZOS).save(output)
    slides.append(output)

document = pymupdf.open()
for slide in slides:
    page = document.new_page(width=432, height=540)
    page.insert_image(page.rect, filename=str(slide))
document.set_metadata({"title": "Did the MCP tool succeed?", "author": "madvibe.ai"})
document.save(ROOT / "LI-022-mcp-tool-errors.pdf", deflate=True, garbage=4)
document.close()

with ZipFile(ROOT / "LI-022-instagram-carousel.zip", "w", ZIP_DEFLATED) as archive:
    for slide in slides:
        archive.write(slide, slide.name)
print("Created 5 PNGs, a 5-page PDF, and an ordered Instagram ZIP.")
