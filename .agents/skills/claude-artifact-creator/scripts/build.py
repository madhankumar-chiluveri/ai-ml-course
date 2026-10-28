#!/usr/bin/env python3
"""Assemble a claude-artifact-creator page from body parts + the bundled design system.

Usage:
  python build.py --title "Ch 1 · The Basics" --out chapters/chapter-01.html \
      --parts header.html body.html footer.html --script specs.js [--css extra.css] [--fragment]

Default output is a full standalone document (doctype/html/head/body): use it for files
saved next to their source in a repo, so they open correctly from disk.
--fragment omits the document skeleton, for pages published with the Artifact tool
(the tool adds its own skeleton and safe-area padding).

Inlined automatically, in order: Google Fonts links, assets/base.css (+ --css),
assets/defs.svg (arrow markers + cloud symbol), the parts, assets/engine.js, then --script.
"""
import argparse
import html
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap">\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Mono:wght@400;600;700&display=swap">\n'
)


def read(p):
    return pathlib.Path(p).read_text(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parts", nargs="+", required=True, help="HTML body fragments, in page order")
    ap.add_argument("--script", nargs="*", default=[], help="page-specific JS (chart/diagram specs); runs after engine.js")
    ap.add_argument("--css", nargs="*", default=[], help="extra CSS appended after base.css")
    ap.add_argument("--fragment", action="store_true", help="omit doctype/html/head/body (Artifact tool publish)")
    a = ap.parse_args()

    css = read(ASSETS / "base.css") + "".join("\n" + read(c) for c in a.css)
    defs = read(ASSETS / "defs.svg")
    body = "\n".join(read(p) for p in a.parts)
    js = read(ASSETS / "engine.js") + "".join("\n" + read(s) for s in a.script)
    title = html.escape(a.title)

    if a.fragment:
        out = (f"<title>{title}</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n{FONTS}"
               f"<style>\n{css}</style>\n{defs}\n{body}\n<script>\n{js}</script>\n")
    else:
        out = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
               f"<title>{title}</title>\n{FONTS}<style>\nbody{{margin:0}}\n{css}</style>\n</head>\n<body>\n"
               f"{defs}\n{body}\n<script>\n{js}</script>\n</body>\n</html>\n")

    dest = pathlib.Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out.encode('utf-8')):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
