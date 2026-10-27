"""Export this carousel with local headless Chrome, then check its PDF and PNGs.

Run build.py first. No installation, server, or network is required.
Browser profiles are temporary; exports stay beside this script.
"""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image
from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
CANDIDATES = [
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
]
BROWSER = next((path for path in CANDIDATES if path.is_file()), None)
if BROWSER is None:
    raise SystemExit("A local Chrome or Edge installation is required.")


def render(extra: list[str], source: Path) -> None:
    temp_root = Path(tempfile.gettempdir()).resolve()
    profile = Path(tempfile.mkdtemp(prefix="li009-render-")).resolve()
    if not profile.is_relative_to(temp_root) or profile == temp_root:
        raise RuntimeError("Unexpected temporary profile location.")
    command = [
        str(BROWSER), "--headless", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-background-networking", "--disable-background-mode",
        "--force-device-scale-factor=1", "--window-size=1080,1350",
        "--virtual-time-budget=1800", f"--user-data-dir={profile}",
        *extra, source.as_uri(),
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(f"Browser export failed: {result.stderr.decode(errors='replace')[-1200:]}")
    finally:
        # Only this renderer's verified temporary directory can be removed.
        if profile.is_relative_to(temp_root) and profile.name.startswith("li009-render-"):
            shutil.rmtree(profile)


def main() -> None:
    pages = sorted((HERE / "source").glob("slide-??.svg"))
    if len(pages) != 7:
        raise RuntimeError("Build the seven source pages first.")
    for source in pages:
        output = HERE / f"{source.stem}.png"
        render([f"--screenshot={output}"], source)
        with Image.open(output) as image:
            if image.size != (1080, 1350):
                raise RuntimeError(f"Unexpected dimensions: {output.name} {image.size}")
        print(f"Exported {output.name}", flush=True)
    print_source = HERE / "source/print.html"
    print_source.write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>AI tool retry decisions — Madhan Kumar</title>'
        '<style>@page{size:1080px 1350px;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0}'
        'section{width:1080px;height:1350px;break-after:page;overflow:hidden}section:last-child{break-after:auto}'
        'svg{display:block;width:1080px;height:1350px}</style>'
        + "".join(f"<section>{page.read_text(encoding='utf-8')}</section>" for page in pages)
        + "</html>", encoding="utf-8",
    )
    pdf = HERE / "LI-009-retry-decisions.pdf"
    render([f"--print-to-pdf={pdf}", "--no-pdf-header-footer"], print_source)
    reader = PdfReader(pdf)
    if len(reader.pages) != 7:
        raise RuntimeError(f"Expected seven PDF pages; found {len(reader.pages)}.")
    for index, page in enumerate(reader.pages, start=1):
        if len(page.extract_text().strip()) < 50:
            raise RuntimeError(f"Missing selectable text on PDF page {index}.")
        if abs(float(page.mediabox.width) / float(page.mediabox.height) - 0.8) > 0.002:
            raise RuntimeError(f"Unexpected PDF aspect ratio on page {index}.")
    overview = Image.new("RGB", (1456, 948), "#E6E4D9")
    for i, source in enumerate(pages):
        with Image.open(HERE / f"{source.stem}.png") as image:
            overview.paste(image.convert("RGB").resize((348, 435), Image.Resampling.LANCZOS), (16 + (i % 4) * 360, 16 + (i // 4) * 465))
    overview.save(HERE / "overview.png")
    with zipfile.ZipFile(HERE / "LI-009-instagram-carousel.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for source in pages:
            archive.write(HERE / f"{source.stem}.png", arcname=f"{source.stem}.png")
    print(json.dumps({"pdf_pages": len(reader.pages), "selectable_text": True, "png_dimensions": [1080, 1350], "pdf_bytes": pdf.stat().st_size}))


if __name__ == "__main__":
    main()
