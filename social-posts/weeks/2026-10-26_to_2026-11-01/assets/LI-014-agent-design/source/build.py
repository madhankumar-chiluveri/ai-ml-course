"""Build the LI-014 graphic storyboard and its two platform exports.

Run with Python, Pillow, pypdf, and local Chrome/Edge. Fonts are bundled.
Illustrations are conceptual; this script does not simulate agent performance.
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image, ImageFont
from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
OUT = HERE.parent
FONTS = HERE / "fonts"
ROOT = next(p for p in HERE.parents if (p / "social-posts/README.md").is_file())
SHARED_FONTS = ROOT / "social-posts/skills/style-ref-editorial/assets/fonts"
GUIDE = "https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop"
INK = "#151916"
PAPER = "#F4F3EB"
LIME = "#D7FF6A"
LILAC = "#BEA6EC"
GRAY = "#B5BDB4"
W, H = 1080, 1350
PNG_SCALE = 2


for filename in ("WorkSans-Regular.ttf", "WorkSans-Bold.ttf", "WorkSans-OFL.txt"):
    if not (FONTS / filename).is_file():
        shutil.copyfile(SHARED_FONTS / filename, FONTS / filename)

FONT_FILES = {"display": "BarlowCondensed-Bold.ttf", "body": "WorkSans-Regular.ttf", "bold": "WorkSans-Bold.ttf"}
FONT_STYLE = "".join(
    f"@font-face{{font-family:{name};src:url(data:font/ttf;base64,{base64.b64encode((FONTS / file).read_bytes()).decode()}) format('truetype');font-weight:400;}}"
    for name, file in FONT_FILES.items()
)


def rect(x, y, width, height, fill, radius=0, stroke=None, sw=3):
    border = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"{border}/>'


def path(d, stroke=INK, sw=4, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def circle(x, y, r, fill, stroke=None, sw=3):
    border = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{border}/>'


def text(x, y, lines, size=40, font="body", color=INK, leading=None, anchor="start", max_width=None):
    lines = [lines] if isinstance(lines, str) else lines
    measure = ImageFont.truetype(str(FONTS / FONT_FILES[font]), size)
    widths = [measure.getlength(line) for line in lines]
    available = max_width if max_width is not None else W - x - 65 if anchor == "start" else W - 130
    if max(widths, default=0) > available + 1:
        raise ValueError(f"Text too wide ({max(widths):.0f}>{available}): {lines}")
    leading = leading or size * 1.05
    tspans = "".join(f'<tspan x="{x}" y="{y + i * leading:g}">{escape(line)}</tspan>' for i, line in enumerate(lines))
    return f'<text fill="{color}" font-family="{font}" font-size="{size}" text-anchor="{anchor}">{tspans}</text>'


def arrow(x1, y1, x2, y2, color=INK, sw=4):
    return path(f"M{x1},{y1} L{x2},{y2}", color, sw, extra=f'marker-end="url(#arrow-{color[1:]})"')


def check(x, y, scale=1, color=INK):
    return f'<g transform="translate({x} {y}) scale({scale})">{path("M0 17 L13 30 L43 0", color, 6)}</g>'


def window(x, y, width, height, label="AGENT", fill=LILAC, face=True, angle=0):
    s = rect(8, 11, width, height, INK, 26)
    s += rect(0, 0, width, height, fill, 26, INK, 4)
    top = min(58, height * .28)
    s += path(f"M0 {top} H{width}", INK, 3)
    for i in range(3):
        s += circle(22 + i * 18, top / 2, 4.5, INK)
    label_size = min(31, int(width * .14))
    s += text(width - 19, top / 2 + 9, label, label_size, "display", anchor="end", max_width=width - 100)
    if face:
        ey = height * .58
        for ex in (width * .36, width * .66):
            s += path(f"M{ex-12} {ey} q12 -18 24 0", INK, 6)
        s += path(f"M{width*.42} {height*.73} q{width*.1} {height*.13} {width*.2} 0", INK, 6)
        s += circle(width * .27, ey + 30, 11, "#DFB6D8")
        s += circle(width * .76, ey + 30, 11, "#DFB6D8")
    return f'<g transform="translate({x} {y}) rotate({angle} {width/2} {height/2})">{s}</g>'


def base(index, bg, foreground=INK):
    defs = "".join(
        f'<marker id="arrow-{c[1:]}" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M1 1 L6 4 L1 7" fill="none" stroke="{c}" stroke-width="1.4"/></marker>'
        for c in (INK, PAPER, LIME, LILAC)
    )
    s = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1350" viewBox="0 0 1080 1350" role="img" aria-labelledby="title"><title id="title">LI-014, page {index} of 7</title><defs>{defs}</defs><style>{FONT_STYLE}</style>'
    s += rect(0, 0, W, H, bg)
    s += text(70, 77, "AI UPDATE / 014", 27, "bold", foreground)
    s += text(1010, 77, "AGENT DESIGN", 27, "body", foreground, anchor="end")
    s += path("M70 1239 H1010", foreground, 1.5)
    s += text(70, 1291, "madvibe.ai", 27, "bold", foreground)
    s += text(1010, 1291, f"{index:02d} / 07", 29, "body", foreground, anchor="end")
    return s


def slide_1():
    s = base(1, INK, PAPER)
    s += text(70, 205, ["BEFORE YOU ADD", "ANOTHER AGENT,"], 112, "display", PAPER, 112)
    s += text(70, 429, ["CHECK WHAT", "IT ADDS."], 124, "display", LIME, 116)
    # A familiar illustrated assistant, drawn as vectors rather than a product screenshot.
    s += circle(827, 858, 188, "none", "#354234", 3)
    s += circle(827, 858, 158, "none", "#354234", 2)
    s += window(565, 726, 330, 236, "AGENT", PAPER, True, 8)
    s += window(300, 826, 390, 278, "AGENT", LILAC, True, -7)
    s += rect(743, 1035, 216, 78, LIME, 3)
    s += text(851, 1088, "+1?", 54, "display", INK, anchor="middle", max_width=190)
    s += text(70, 1185, 'A follow-up to “AI said Fixed.”', 36, "body", PAPER)
    return s + "</svg>"


def slide_2():
    s = base(2, PAPER)
    s += text(70, 207, ['“FIXED” IS', "A CLAIM."], 124, "display", leading=118)
    s += text(70, 417, "Checks bring evidence.", 43)
    s += window(114, 580, 422, 318, "AI", LILAC, True, -7)
    s += arrow(562, 752, 627, 752, INK, 5)
    sheet = rect(8, 12, 285, 352, INK, 5) + rect(0, 0, 285, 352, PAPER, 5, INK, 4)
    sheet += rect(68, -17, 148, 43, LIME, 8, INK, 3)
    sheet += text(33, 90, "VERIFY", 56, "display", max_width=220)
    for i in range(3):
        yy = 135 + i * 59
        sheet += rect(33, yy, 28, 28, "none", 2, INK, 3)
        sheet += path(f"M82 {yy+14} H243", INK, 3)
    sheet += check(35, 190, .65)
    s += f'<g transform="translate(673 566) rotate(6 142 176)">{sheet}</g>'
    s += text(70, 1007, "ILLUSTRATED CALLBACK", 27, "bold")
    s += rect(70, 1054, 940, 151, INK, 5)
    s += text(108, 1111, ["Adding an agent is a design choice.", "Its value still needs evidence."], 38, color=PAPER, leading=51, max_width=870)
    return s + "</svg>"


def slide_3():
    s = base(3, INK, PAPER)
    s += text(70, 207, ["EACH HANDOFF", "NEEDS CONTEXT."], 119, "display", PAPER, 119)
    s += text(70, 441, "What survives the next summary?", 42, color=LIME)
    labels = ("PLANNER", "BUILDER", "REVIEWER", "MAIN LOOP")
    for i, label in enumerate(labels):
        x = 70 + 252 * i
        s += rect(x + 6, 638, 181, 218, "#354234", 12)
        s += rect(x, 631, 181, 218, LILAC if i < 3 else LIME, 12)
        s += text(x + 90, 690, label, 33, "display", INK, anchor="middle", max_width=165)
        for j, length in enumerate((112, 92, 67)):
            s += path(f"M{x+28} {733+j*26} H{x+28+length}", INK, 4)
        if i < 3:
            s += arrow(x + 193, 742, x + 237, 742, PAPER, 4)
    s += text(70, 966, ["Details can get lost.", "Extra calls can add latency."], 43, color=PAPER, leading=65)
    s += rect(70, 1116, 940, 88, LIME, 4)
    s += text(106, 1173, "Test fewer handoffs on the same tasks.", 37, max_width=872)
    return s + "</svg>"


def slide_4():
    s = base(4, LIME)
    s += text(70, 207, ["ONE AGENT.", "SEVERAL SKILLS."], 123, "display", leading=119)
    s += rect(70, 444, 940, 636, INK, 30)
    s += text(105, 497, "SHARED CONTEXT", 28, "bold", LIME)
    # Side stacks represent descriptions/instructions loaded as needed, not separate model loops.
    s += rect(104, 599, 206, 283, PAPER, 10)
    s += text(207, 661, "SKILLS", 46, "display", anchor="middle", max_width=190)
    for j in range(3):
        s += rect(131, 700 + j * 47, 152, 29, "none", 2, INK, 2)
    s += window(366, 614, 342, 257, "AGENT", LILAC, True)
    s += rect(768, 599, 206, 283, PAPER, 10)
    s += text(871, 661, "TOOLS", 46, "display", anchor="middle", max_width=190)
    for j in range(3):
        s += circle(802, 717 + j * 47, 8, INK)
        s += path(f"M825 {717+j*47} H945", INK, 3)
    s += arrow(321, 741, 352, 741, LIME)
    s += arrow(721, 741, 754, 741, LIME)
    s += text(540, 969, "Load instructions when needed.", 37, color=PAPER, anchor="middle", max_width=850)
    s += text(540, 1025, "Call tools. Check the result.", 37, color=PAPER, anchor="middle", max_width=850)
    s += text(70, 1176, "A simpler option to evaluate.", 40)
    return s + "</svg>"


def boundary_icon(kind, x, y):
    if kind == 0:
        return arrow(x, y + 60, x + 115, y + 60) + path(f"M{x+26} {y+60} V{y+14} H{x+115}", INK, 4, extra='marker-end="url(#arrow-151916)"') + path(f"M{x+26} {y+60} V{y+108} H{x+115}", INK, 4, extra='marker-end="url(#arrow-151916)"')
    if kind == 1:
        return rect(x, y + 10, 78, 99, "none", 5, INK, 4) + rect(x + 91, y + 10, 78, 99, "none", 5, INK, 4) + path(f"M{x+91} {y+10} V{y+109}", INK, 4)
    return circle(x + 56, y + 51, 41, "none", INK, 5) + path(f"M{x+86} {y+82} L{x+126} {y+122}", INK, 9) + check(x + 33, y + 36, .9)


def slide_5():
    s = base(5, INK, PAPER)
    s += text(70, 207, ["KEEP SEPARATION", "WHEN IT HELPS."], 112, "display", PAPER, 115)
    rows = [
        (PAPER, "PARALLEL WORK", "Independent tasks can run together."),
        (LILAC, "FRESH CONTEXT", "Give a task its own working space."),
        (LIME, "INDEPENDENT CHECKING", "Define what the reviewer must verify."),
    ]
    for i, (fill, head, body) in enumerate(rows):
        yy = 453 + i * 235
        s += rect(70, yy, 940, 209, fill, 4)
        s += boundary_icon(i, 106, yy + 46)
        s += text(313, yy + 80, head, 51, "display", max_width=650)
        s += text(313, yy + 145, body, 33, max_width=650)
    s += text(70, 1200, "Keep the boundary that helps the task.", 37, color=PAPER)
    return s + "</svg>"


def slide_6():
    s = base(6, PAPER)
    s += text(70, 207, ["LET THE", "OUTCOME DECIDE."], 119, "display", leading=119)
    s += text(70, 439, "Same tasks. Same checks.", 43)
    s += text(540, 561, "COMPARISON PLAN", 28, "bold", anchor="middle", max_width=850)
    s += path("M540 591 V623 M290 623 H790 M290 623 V660 M790 623 V660", INK, 3)
    s += rect(70, 661, 440, 230, LILAC, 5, INK, 3)
    s += rect(570, 661, 440, 230, LIME, 5, INK, 3)
    s += text(290, 717, "CURRENT DESIGN", 40, "display", anchor="middle", max_width=400)
    s += text(790, 717, "ONE MERGE", 40, "display", anchor="middle", max_width=400)
    for xx in (130, 262, 394):
        s += rect(xx - 28, 767, 63, 66, PAPER, 7, INK, 3)
    s += arrow(173, 800, 220, 800)
    s += arrow(305, 800, 352, 800)
    s += rect(687, 764, 206, 70, PAPER, 8, INK, 3)
    s += text(790, 814, "SHARED LOOP", 33, "display", anchor="middle", max_width=190)
    s += rect(70, 955, 940, 252, INK, 5)
    s += text(112, 1011, "COMPARE", 28, "bold", LIME)
    s += text(112, 1072, "Quality / Time / Cost / Regressions", 39, color=PAPER, max_width=850)
    s += text(112, 1152, "Keep what holds up on your workload.", 36, color=PAPER, max_width=850)
    return s + "</svg>"


def slide_7():
    s = base(7, LILAC)
    s += text(70, 207, ["WHAT DOES", "YOUR NEXT", "AGENT ADD?"], 126, "display", leading=120)
    for i, label in enumerate(("Parallel work?", "Fresh context?", "Independent checking?")):
        yy = 611 + i * 104
        s += circle(88, yy - 16, 9, INK)
        s += text(124, yy, label, 50, "display")
    s += text(70, 981, "Which handoff would you test first?", 42)
    box = rect(70, 1041, 940, 160, INK, 5)
    box += text(108, 1097, "BASED ON ANTHROPIC’S GUIDE", 29, "bold", PAPER, max_width=865)
    box += text(108, 1160, "22 OCT 2026  /  READ THE ORIGINAL ↗", 34, "body", LIME, max_width=865)
    s += f'<a href="{GUIDE}" xlink:href="{GUIDE}">{box}</a>'
    return s + "</svg>"


def render(browser: Path, extra: list[str], source: Path, scale: int = 1):
    temp_root = Path(tempfile.gettempdir()).resolve()
    profile = Path(tempfile.mkdtemp(prefix="li014-render-")).resolve()
    if not profile.is_relative_to(temp_root) or profile == temp_root:
        raise RuntimeError("Unexpected temporary profile path")
    command = [str(browser), "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--disable-background-networking", "--disable-background-mode", f"--force-device-scale-factor={scale}",
               "--window-size=1080,1350", "--virtual-time-budget=1500", f"--user-data-dir={profile}", *extra, source.as_uri()]
    try:
        result = subprocess.run(command, capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace")[-1200:])
    finally:
        if profile.is_relative_to(temp_root) and profile.name.startswith("li014-render-"):
            shutil.rmtree(profile)


def main():
    slides = [func() for func in (slide_1, slide_2, slide_3, slide_4, slide_5, slide_6, slide_7)]
    for i, svg in enumerate(slides, 1):
        (HERE / f"slide-{i:02d}.svg").write_text(svg, encoding="utf-8")
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Before you add another agent — madvibe.ai</title>'
    html += '<meta name="viewport" content="width=device-width,initial-scale=1"><style>@page{size:1080px 1350px;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0;background:#151916}section{width:1080px;height:1350px;break-after:page;overflow:hidden}section:last-child{break-after:auto}svg{display:block;width:1080px;height:1350px}@media screen{body{display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px}section{box-shadow:0 6px 35px #0007}}</style></head><body>'
    html += "".join(f'<section aria-label="Page {i}">{svg}</section>' for i, svg in enumerate(slides, 1)) + '</body></html>'
    (HERE / "index.html").write_text(html, encoding="utf-8")
    browser = next((p for p in (Path("C:/Program Files/Google/Chrome/Application/chrome.exe"), Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")) if p.is_file()), None)
    if not browser:
        raise SystemExit("Local Chrome or Edge is required")
    for i in range(1, 8):
        render(browser, [f"--screenshot={OUT / f'slide-{i:02d}.png'}"], HERE / f"slide-{i:02d}.svg", scale=PNG_SCALE)
        with Image.open(OUT / f"slide-{i:02d}.png") as im:
            if im.size != (W * PNG_SCALE, H * PNG_SCALE):
                raise RuntimeError("Unexpected PNG dimensions")
        print(f"Exported page {i}/7", flush=True)
    pdf = OUT / "LI-014-another-agent.pdf"
    render(browser, [f"--print-to-pdf={pdf}", "--no-pdf-header-footer"], HERE / "index.html")
    reader = PdfReader(pdf)
    if len(reader.pages) != 7:
        raise RuntimeError(f"Expected seven PDF pages, got {len(reader.pages)}")
    for i, page in enumerate(reader.pages, 1):
        if len(page.extract_text().strip()) < 55:
            raise RuntimeError(f"Missing PDF text on page {i}")
        if abs(float(page.mediabox.width) / float(page.mediabox.height) - .8) > .001:
            raise RuntimeError("Unexpected PDF aspect ratio")
    overview = Image.new("RGB", (1456, 950), INK)
    for i in range(7):
        with Image.open(OUT / f"slide-{i+1:02d}.png") as im:
            overview.paste(im.convert("RGB").resize((348, 435), Image.Resampling.LANCZOS), (16 + i % 4 * 360, 16 + i // 4 * 465))
    overview.save(OUT / "overview.png")
    with zipfile.ZipFile(OUT / "LI-014-instagram-carousel.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for i in range(1, 8):
            archive.write(OUT / f"slide-{i:02d}.png", arcname=f"slide-{i:02d}.png")
    print(f"Verified seven pages, selectable text, {W * PNG_SCALE}x{H * PNG_SCALE} PNGs. PDF: {pdf.stat().st_size:,} bytes.")


if __name__ == "__main__":
    main()
