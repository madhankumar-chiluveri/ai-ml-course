"""Package the directly generated LI-018 carousel.

The built-in image tool creates the complete artwork. This script preserves
the native images, exports exact 2160x2700 PNGs, and assembles an image-based
PDF. Export scaling does not add image detail. No performance is simulated.
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject


HERE = Path(__file__).resolve().parent
OUT = HERE.parent
GPU_SOURCE = "https://docs.nvidia.com/deeplearning/performance/dl-performance-gpu-background/index.html"
LLM_SOURCE = "https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization"
GENERATION_SOURCE = "https://github.com/huggingface/transformers/blob/main/docs/source/en/llm_tutorial_optimization.md"
DESCRIPTIONS = [
    "Mad studies a cutaway GPU, with VRAM marked FITS and a path to compute. The model fits. Why is it still slow? Capacity is only one check.",
    "Weights are learned numbers. Loading places them in VRAM, the GPU's main memory. The workload also needs saved context and calculation buffers. Fitting is a capacity check, measured in GB.",
    "For one token, GPU units read weights in pieces through caches and registers, calculate next-token probabilities, then select and append a token. A token is a text chunk. Bandwidth is data moved per second, measured in GB/s.",
    "Three successive read-calculate-token rows show generation repeating. Large models exceed small on-chip stores, so required weights are read again from VRAM. For one response, movement can take longer than calculation and limit token speed.",
    "A hypothetical comparison assumes both workloads fit in 24 GB and each step reads 14 GB of weights. Ideal read times are 40 ms at 350 GB/s and 20 ms at 700 GB/s. This is illustrative arithmetic, not a benchmark; other work also affects token latency.",
]


def render(browser, source, options, scale=1):
    temp_root = Path(tempfile.gettempdir()).resolve()
    profile = Path(tempfile.mkdtemp(prefix="li018-direct-render-")).resolve()
    if not profile.is_relative_to(temp_root) or profile == temp_root:
        raise RuntimeError("Unexpected temporary browser profile")
    try:
        command = [str(browser), "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                   "--disable-extensions", "--disable-background-networking", "--disable-background-mode",
                   f"--force-device-scale-factor={scale}", "--window-size=1080,1350", "--virtual-time-budget=1500",
                   f"--user-data-dir={profile}", *options, source.as_uri()]
        result = subprocess.run(command, capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace")[-1200:])
    finally:
        if profile.is_relative_to(temp_root) and profile.name.startswith("li018-direct-render-"):
            shutil.rmtree(profile)


def source_outline(writer, title, page, url):
    """Keep source navigation without painting over generated artwork."""
    item = writer.add_outline_item(title, page)
    item.get_object()[NameObject("/A")] = DictionaryObject({
        NameObject("/S"): NameObject("/URI"),
        NameObject("/URI"): TextStringObject(url),
    })


def main():
    browser = next((p for p in (
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ) if p.is_file()), None)
    if not browser:
        raise RuntimeError("Local Chrome or Edge is required")
    slides = []
    for i in range(1, 6):
        native = HERE / f"direct-slide-{i:02d}.png"
        with Image.open(native) as im:
            if abs(im.width / im.height - .8) > .008:
                raise RuntimeError(f"Unexpected native aspect ratio on page {i}: {im.size}")
            print(f"Native page {i}: {im.width}x{im.height}", flush=True)
        data = base64.b64encode(native.read_bytes()).decode()
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350" role="img">'
        svg += f'<title>LI-018, page {i} of 5</title><desc>{escape(DESCRIPTIONS[i-1])}</desc>'
        svg += '<rect width="1080" height="1350" fill="#FFFCF0"/>'
        svg += f'<image width="1080" height="1350" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>'
        if i in (3, 4, 5):
            url = GPU_SOURCE if i == 3 else LLM_SOURCE
            svg += f'<a href="{escape(url)}"><title>Read the supporting NVIDIA guide</title><rect x="360" y="1260" width="370" height="65" fill="white" fill-opacity="0.001"/></a>'
        svg += '</svg>'
        source = HERE / f"slide-{i:02d}.svg"
        source.write_text(svg, encoding="utf-8")
        slides.append(svg)
        final = OUT / f"slide-{i:02d}.png"
        render(browser, source, [f"--screenshot={final}"], scale=2)
        with Image.open(final) as im:
            if im.size != (2160, 2700):
                raise RuntimeError(f"Unexpected PNG dimensions: {im.size}")
        print(f"Exported page {i}/5: 2160x2700", flush=True)
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The model fits. Why is it still slow? | madvibe.ai</title>'
    html += '<style>@page{size:1080px 1350px;margin:0}html,body{margin:0;padding:0;background:#FFFCF0}section{width:1080px;height:1350px;break-after:page;overflow:hidden}section:last-child{break-after:auto}svg{display:block;width:1080px;height:1350px}</style></head><body>'
    html += ''.join(f'<section aria-label="Page {i}">{svg}</section>' for i, svg in enumerate(slides, 1)) + '</body></html>'
    (HERE / "index.html").write_text(html, encoding="utf-8")
    pdf = OUT / "LI-018-vram-and-token-speed.pdf"
    render(browser, HERE / "index.html", [f"--print-to-pdf={pdf}", "--no-pdf-header-footer"])
    reader = PdfReader(pdf)
    if len(reader.pages) != 5:
        raise RuntimeError(f"Expected five PDF pages, got {len(reader.pages)}")
    if not all(abs(float(p.mediabox.width) / float(p.mediabox.height) - .8) < .001 for p in reader.pages):
        raise RuntimeError("Incorrect PDF aspect ratio")
    if not all(p["/Resources"].get("/XObject") for p in reader.pages):
        raise RuntimeError("Missing generated artwork in PDF")
    writer = PdfWriter()
    writer.append(reader, import_outline=False)
    writer.add_metadata({"/Title": "The model fits. Why is it still slow?", "/Author": "madvibe.ai", "/Subject": "Capacity, bandwidth and compute; source-led conceptual illustrations, not benchmarks"})
    source_outline(writer, "Source: NVIDIA GPU Performance Background", 2, GPU_SOURCE)
    source_outline(writer, "Source: NVIDIA Inference Optimization", 3, LLM_SOURCE)
    source_outline(writer, "Source: Hugging Face Autoregressive Generation", 2, GENERATION_SOURCE)
    temporary = OUT / "LI-018-vram-and-token-speed.packaging.pdf"
    with temporary.open("wb") as stream:
        writer.write(stream)
    temporary.replace(pdf)
    overview = Image.new("RGB", (1152, 964), "#EAE7DB")
    for i in range(5):
        with Image.open(OUT / f"slide-{i+1:02d}.png") as im:
            overview.paste(im.convert("RGB").resize((360, 450), Image.Resampling.LANCZOS), (18 + i % 3 * 378, 18 + i // 3 * 478))
    overview.save(OUT / "overview.png")
    with zipfile.ZipFile(OUT / "LI-018-instagram-carousel.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for i in range(1, 6):
            archive.write(OUT / f"slide-{i:02d}.png", arcname=f"slide-{i:02d}.png")
    print(f"Verified five image-based pages, source links, exact 4:5 PNGs. PDF: {pdf.stat().st_size:,} bytes.", flush=True)


if __name__ == "__main__":
    main()
