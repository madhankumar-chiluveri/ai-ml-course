#!/usr/bin/env python3
"""Static checks for a built page. Exit code 1 if anything fails.

Usage: python check.py page.html [page2.html ...]

Checks:
  1. Tag balance (non-void HTML/SVG elements all close, in order).
  2. Every inline <script> parses (`node --check`, skipped if node is missing).
  3. Every plot/spark/dg('id') call has a matching id="..." host, and every
     sp-/ch-/dg- host in the HTML is filled by some call (no empty boxes).
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

VOID = {"meta", "link", "br", "img", "input", "hr", "path", "rect", "circle", "line",
        "polyline", "polygon", "use", "stop", "source", "col", "wbr", "ellipse"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                if i != len(self.stack) - 1:
                    self.errors.append(f"unclosed {[t for t, _ in self.stack[i + 1:]]} before </{tag}> at line {self.getpos()[0]}")
                del self.stack[i:]
                return
        self.errors.append(f"stray </{tag}> at line {self.getpos()[0]}")


def check(path):
    src = pathlib.Path(path).read_text(encoding="utf-8")
    problems = []

    b = Balance()
    b.feed(src)
    problems += b.errors
    if b.stack:
        problems.append(f"left open: {[(t, p[0]) for t, p in b.stack[:8]]}")

    scripts = re.findall(r"<script>(.*?)</script>", src, flags=re.S)
    node = shutil.which("node")
    if node:
        for i, s in enumerate(scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(s)
            r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
            pathlib.Path(f.name).unlink(missing_ok=True)
            if r.returncode:
                problems.append(f"script #{i + 1} does not parse:\n{r.stderr.strip()[:600]}")
    else:
        print("  (node not found: script syntax not checked)")

    js = "\n".join(scripts)
    called = set(re.findall(r"\b(?:plot|spark|dg)\('([\w-]+)'", js))
    hosts = set(re.findall(r'id="((?:sp|ch|dg)-[\w-]+)"', src))
    for i in sorted(called - set(re.findall(r'id="([\w-]+)"', src))):
        problems.append(f"call targets missing host id: {i}")
    # wrappers (e.g. a local helper that calls dg(id, …)) pass the id as a plain string,
    # so any quoted mention of the host id in a script counts as filling it
    for i in sorted(h for h in hosts - called if f"'{h}'" not in js and f'"{h}"' not in js):
        problems.append(f"host never filled: {i}")

    print(f"{path}: {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    for p in problems:
        print("  - " + p)
    return not problems


if __name__ == "__main__":
    ok = all([check(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
