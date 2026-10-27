"""Build editable carousel SVGs from saved result data.

Uses Pillow for font metrics. Writes only this asset's source and alt text.
"""

from __future__ import annotations

import base64
from html import escape
import json
from pathlib import Path

from PIL import ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FONTS = ROOT / "social-posts/skills/style-ref-editorial/assets/fonts"
SOURCE = HERE / "source"
PAPER, INK, BLUE = "#FFFCF0", "#100F0F", "#2246A8"
MINT, LILAC, BUTTER, ROSE, SKY = "#DDF6E9", "#ECE6FF", "#FFF1B8", "#FFE2E8", "#DFF2FF"
GRAY = "#575653"
FONT_FILES = {
    "Display": "BricolageGrotesque-Bold.ttf",
    "Body": "WorkSans-Regular.ttf",
    "Strong": "WorkSans-Bold.ttf",
    "Note": "NothingYouCouldDo-Regular.ttf",
    "Mono": "JetBrainsMono-Regular.ttf",
}
FONT_CSS = "".join(
    f"@font-face{{font-family:{name};src:url(data:font/ttf;base64,{base64.b64encode((FONTS / filename).read_bytes()).decode()})}}"
    for name, filename in FONT_FILES.items()
)


class Page:
    def __init__(self, number: int, title: str, alt: str):
        self.number, self.title, self.alt = number, title, alt
        self.parts: list[str] = []

    def text(self, x, y, words, size=38, face="Body", color=INK, width=None, anchor="start", leading=1.15):
        lines = words.split("\n")
        if width:
            longest = max(ImageFont.truetype(str(FONTS / FONT_FILES[face]), size).getlength(line) for line in lines)
            if longest > width:
                raise ValueError(f"Page {self.number}: text exceeds width {width}: {words!r} ({longest:.1f})")
        spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else size * leading}">{escape(line)}</tspan>' for i, line in enumerate(lines))
        limit = f' data-max-width="{width}"' if width else ""
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{face}" font-size="{size}" text-anchor="{anchor}"{limit}>{spans}</text>')

    def box(self, x, y, w, h, fill=PAPER, stroke=INK, radius=26, dashed=False):
        dash = ' stroke-dasharray="9 9"' if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"{dash}/>')

    def arrow(self, path, color=BLUE, dashed=False):
        dash = ' stroke-dasharray="11 10"' if dashed else ""
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"{dash}/>')

    def line(self, path, color=BLUE, width=3):
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')

    def header(self, eyebrow, title, subtitle, size=88):
        self.text(70, 78, eyebrow.upper(), 28, "Strong", BLUE, 940)
        self.text(65, 193, title, size, "Display", width=950, leading=1.05)
        self.text(70, 350, subtitle, 34, "Body", width=940)

    def footer(self):
        self.line("M70 1262 H1010", color="#DAD8CE", width=2)
        self.text(70, 1310, "RELIABLE AI / PHASE 0", 25, "Strong", GRAY)
        self.text(720, 1310, "Madhan Kumar", 28, "Strong")
        self.text(1010, 78, f"{self.number}/7", 28, "Strong", GRAY, anchor="end")

    def save(self):
        self.footer()
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350" role="img" aria-labelledby="title desc">
<title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.alt)}</desc>
<defs><style>{FONT_CSS}</style><marker id="arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M2 2 L10 6 L2 10" fill="none" stroke="{BLUE}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>
<rect width="1080" height="1350" fill="{PAPER}"/>
{''.join(self.parts)}</svg>'''
        (SOURCE / f"slide-{self.number:02}.svg").write_text(svg, encoding="utf-8")


def carousel(proof):
    cases = {case["name"]: case for case in proof["cases"]}
    pages = []
    p = Page(1, "Retrying a bad request won't fix it", "A large 400 invalid-payload card sits inside a retry loop. Replaying the same payload returns to the same failure. Diagnose before an AI tool retries.")
    p.text(70, 78, "AI TOOL RELIABILITY", 28, "Strong", BLUE)
    p.text(65, 210, "Retrying a\nbad request\nwon’t fix it.", 112, "Display", width=950, leading=1.03)
    p.text(76, 535, "Diagnose before your AI tool retries.", 40, "Note", BLUE, width=930)
    p.box(245, 660, 590, 300, ROSE)
    p.text(540, 835, "400", 156, "Display", anchor="middle")
    p.text(540, 906, "invalid payload", 42, "Strong", anchor="middle")
    p.arrow("M842 902 C1038 954 1040 593 754 595 C460 595 142 562 140 784 C139 854 165 892 220 900")
    p.text(170, 1050, "same payload, same failure", 42, "Note", BLUE, width=800)
    p.line("M170 1068 Q436 1082 762 1066", BLUE)
    p.box(70, 1135, 940, 95, BUTTER, stroke="#AD8301", radius=20)
    p.text(106, 1195, "Fix. Wait. Verify. Choose before retrying.", 35, "Strong", width=868)
    pages.append(p)

    p = Page(2, "Three failures, three decisions", "Three distinct retry paths: invalid payload means fix the request; temporary overload means wait within a budget; an unknown write result means verify replay safety.")
    p.header("Classify the failure", "Three failures.\nThree decisions.", "The response alone is only one clue.", 94)
    for y, fill, name, detail, action in [
        (440, ROSE, "Invalid payload", "Validation cannot pass unchanged", "FIX"),
        (635, BUTTER, "Temporary overload", "Capacity may recover", "WAIT"),
        (830, LILAC, "Unknown write result", "The operation may have committed", "VERIFY"),
    ]:
        p.box(70, y, 940, 160, fill)
        p.text(105, y + 61, name, 39, "Strong", width=560)
        p.text(105, y + 115, detail, 29, "Body", width=550)
        p.arrow(f"M660 {y + 80} Q700 {y + 72} 730 {y + 80}")
        p.text(870, y + 96, action, 40, "Strong", anchor="middle")
    p.text(87, 1100, "Two checks: failure type + replay safety.", 37, "Note", BLUE, width=910)
    p.text(87, 1172, "Use the provider’s documented error semantics.", 31, "Body", width=910)
    pages.append(p)

    p = Page(3, "A malformed request needs a change", "An illustrative API requires a positive limit. The unchanged payload with limit minus one produces a 400 validation error on all three attempts. Repair the input or stop.")
    p.header("Invalid payload", "A malformed request\nneeds a change.", "Waiting does not repair an invalid payload.", 83)
    p.box(70, 430, 940, 180, SKY)
    p.text(108, 504, '{"limit": -1}', 43, "Mono", width=850)
    p.text(108, 565, "API contract: limit must be positive.", 33, "Body", width=850)
    p.arrow("M540 620 Q547 657 540 687")
    for index, x in enumerate((70, 400, 730), start=1):
        p.box(x, 710, 280, 190, ROSE)
        p.text(x + 140, 803, "400", 78, "Display", anchor="middle")
        p.text(x + 140, 861, f"attempt {index}", 32, "Strong", anchor="middle")
        if index < 3:
            p.arrow(f"M{x + 285} 804 Q{x + 307} 796 {x + 322} 804")
    p.text(105, 974, "Same payload → same validation error.", 36, "Note", BLUE, width=880)
    p.box(70, 1032, 940, 113, MINT)
    p.text(109, 1107, "Repair the input or stop.", 47, "Display", width=860)
    p.text(70, 1200, "Illustrative API contract; provider errors can differ.", 28, "Body", GRAY, width=940)
    pages.append(p)

    p = Page(4, "Rate limited? Make room to recover", "A temporary 429 rate-limit response can lead to a successful retry after waiting. Honor Retry-After, add jitter, and cap attempts and elapsed time. Quota and billing errors need classification.")
    p.header("Temporary rate limit", "Rate limited?\nMake room to recover.", "Retry only a documented temporary condition.", 85)
    for x, fill, value, caption in [(70, ROSE, "429", "rate limited"), (405, BUTTER, "WAIT", "Retry-After"), (740, MINT, "200", "success")]:
        p.box(x, 460, 270, 230, fill)
        p.text(x + 135, 565, value, 70 if value != "WAIT" else 53, "Display", anchor="middle")
        p.text(x + 135, 634, caption, 29, "Strong", anchor="middle")
    p.arrow("M348 572 Q371 561 395 572")
    p.arrow("M682 572 Q707 561 731 572")
    p.text(270, 762, "give recovery some room", 42, "Note", BLUE, width=720)
    for y, text, fill in [(827, "Honor Retry-After when supplied.", SKY), (933, "Add jitter to spread retry timing.", LILAC), (1039, "Cap attempts and total elapsed time.", BUTTER)]:
        p.box(70, y, 940, 84, fill, stroke="#DAD8CE", radius=20)
        p.text(104, y + 54, text, 35, "Strong", width=865)
    p.text(70, 1200, "A quota or billing limit may need a different fix.", 28, "Body", GRAY, width=940)
    pages.append(p)

    p = Page(5, "A timeout can hide a completed write", "One possible failure path: a client requests a write, the API commits it, and the response is lost. A client timeout leaves the result unknown. Check the outcome or use API-enforced idempotency.")
    p.header("Unknown write result", "A timeout can hide\na completed write.", "The response can disappear after the commit.", 87)
    p.box(70, 437, 320, 100, SKY)
    p.text(230, 503, "AI tool", 41, "Strong", anchor="middle")
    p.box(690, 437, 320, 100, LILAC)
    p.text(850, 503, "Write API", 41, "Strong", anchor="middle")
    p.line("M230 550 V1000", "#A9AFB8", 2)
    p.line("M850 550 V1000", "#A9AFB8", 2)
    p.arrow("M240 625 H833")
    p.text(385, 604, "Create record", 35, "Body", width=440)
    p.box(680, 675, 330, 100, MINT)
    p.text(845, 740, "Committed", 37, "Strong", anchor="middle")
    p.arrow("M835 825 H570", dashed=True)
    p.line("M528 807 L560 841 M559 807 L527 841", "#AF3029", 5)
    p.text(330, 894, "response lost", 39, "Note", BLUE, width=480)
    p.box(70, 942, 330, 94, ROSE)
    p.text(235, 1002, "Timeout", 41, "Strong", anchor="middle")
    p.text(484, 1012, "result unknown", 40, "Note", BLUE, width=490)
    p.box(70, 1092, 940, 106, BUTTER)
    p.text(105, 1158, "Check outcome or use enforced idempotency.", 33, "Strong", width=870)
    p.text(70, 1230, "One possible failure path. Idempotency requires API support.", 26, "Body", GRAY, width=940)
    pages.append(p)

    p = Page(6, "Change the policy, count the attempts", "Verified offline simulation with a three-attempt cap: blanket retries make three invalid calls; classified retries stop after one; a temporary rate limit succeeds in two; an ambiguous write stops after one for verification. These are synthetic counts, not latency results.")
    p.header("Verified policy simulation", "Change the policy.\nCount the attempts.", "Offline simulation · cap: 3 total attempts", 91)
    p.text(95, 442, "SCENARIO / POLICY", 28, "Strong", BLUE)
    p.text(747, 442, "CALLS", 28, "Strong", BLUE, anchor="middle")
    p.text(934, 442, "RESULT", 28, "Strong", BLUE, anchor="middle")
    rows = [
        (ROSE, "Invalid payload", "Retry every failure", cases["invalid_blanket"]["attempts"], "FAIL"),
        (MINT, "Invalid payload", "Classify before retrying", cases["invalid_classified"]["attempts"], "STOP"),
        (SKY, "Temporary rate limit", "Wait, then retry safely", cases["temporary_rate_limit"]["attempts"], "OK"),
        (BUTTER, "Ambiguous write", "Verify before repeating", cases["ambiguous_write"]["attempts"], "CHECK"),
    ]
    for i, (fill, name, policy, count, result) in enumerate(rows):
        y = 475 + i * 145
        p.box(70, y, 940, 124, fill, stroke="#DAD8CE", radius=20)
        p.text(104, y + 48, name, 36, "Strong", width=540)
        p.text(104, y + 93, policy, 30, "Body", width=540)
        p.text(747, y + 89, str(count), 76, "Display", anchor="middle")
        p.text(934, y + 77, result, 29, "Strong", anchor="middle")
    p.text(80, 1123, "A stopped retry can be the correct result.", 39, "Note", BLUE, width=925)
    p.text(70, 1195, "Synthetic responses. No network or latency benchmark.", 28, "Body", GRAY, width=940)
    pages.append(p)

    p = Page(7, "Three questions before the next retry", "Before retrying an AI tool, ask whether the failure can clear without changing the request, whether repeating the operation is safe, and whether the retry fits the remaining time budget. If any answer is no, stop or change the action.")
    p.header("Keep this decision rule", "Before the next retry,\nask three things.", "Failure type + replay safety + remaining budget.", 85)
    for y, number, fill, lines in [(445, "1", ROSE, "Can this failure clear without\na request change?"), (645, "2", MINT, "Can this operation be\nrepeated safely?"), (845, "3", BUTTER, "Does a retry fit the\nremaining time budget?")]:
        p.box(70, y, 940, 165, fill)
        p.text(116, y + 107, number, 73, "Display")
        p.text(220, y + 67, lines, 39, "Strong", width=750, leading=1.3)
    p.text(80, 1100, "If no: stop or change the action.", 41, "Note", BLUE, width=925)
    p.line("M80 1122 Q407 1135 765 1120", BLUE)
    p.text(70, 1204, "Sources: RFC 9110 · RFC 6585 · AWS Builders’ Library", 27, "Body", GRAY, width=940)
    pages.append(p)
    for page in pages:
        page.save()
    (HERE / "alt-text.json").write_text(json.dumps([{"page": p.number, "title": p.title, "alt": p.alt} for p in pages], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")




if __name__ == "__main__":
    SOURCE.mkdir(parents=True, exist_ok=True)
    results = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    carousel(results)
    print(json.dumps({"svg_pages": 7}))
