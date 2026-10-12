#!/usr/bin/env python3
"""Validate a LinkedIn weekly post Markdown file without third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "post_id",
    "status",
    "scheduled_at",
    "timezone",
    "pillar",
    "format",
    "primary_goal",
    "audience",
)

ALLOWED_STATUSES = {
    "idea",
    "research",
    "brief",
    "draft",
    "review",
    "scheduled",
    "published",
    "measured",
    "archived",
}
ALLOWED_PILLARS = {"authority", "build_proof", "narrative", "community", "product"}
ALLOWED_FORMATS = {"text", "single_image", "document", "carousel", "video", "poll"}
FINAL_STATUSES = {"review", "scheduled", "published", "measured", "archived"}
PATH_FIELDS = ("research", "course_source")

AI_TELL_PATTERNS = (
    ("generic-audience-judgment", re.compile(r"\bmost developers\b", re.IGNORECASE)),
    ("inflated-language", re.compile(r"\bgame[ -]?changer\b", re.IGNORECASE)),
    ("generic-reveal", re.compile(r"\bhere(?:'|’)?s (?:what|how)\b", re.IGNORECASE)),
    (
        "comment-gate",
        re.compile(
            r"\bcomment\s+(?:['\"]?[A-Za-z0-9_-]+['\"]?|\w+)\s+"
            r"(?:below\s+)?(?:to|and)\s+(?:get|receive|unlock|send)\b",
            re.IGNORECASE,
        ),
    ),
)

PRECISE_NUMBER_PATTERN = re.compile(
    r"(?:[$₹€£]\s*\d[\d,.]*|"
    r"\b\d+(?:\.\d+)?\s*(?:%|×|x\b|ms\b|seconds?\b|minutes?\b|hours?\b|"
    r"tokens?\b|queries?\b|trials?\b|impressions?\b|comments?\b|followers?\b))",
    re.IGNORECASE,
)


def issue(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[dict[str, str]]]:
    problems: list[dict[str, str]] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, [issue("error", "frontmatter-missing", "File must start with YAML frontmatter delimited by ---.")]

    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}, text, [issue("error", "frontmatter-unclosed", "Frontmatter has no closing --- delimiter.")]

    data: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines[1:end], start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in raw_line:
            problems.append(
                issue("error", "frontmatter-invalid-line", f"Line {line_number} is not a key: value pair.")
            )
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            problems.append(
                issue("error", "frontmatter-nested", f"Line {line_number} uses unsupported nested frontmatter.")
            )
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        data[key] = value

    body = "\n".join(lines[end + 1 :])
    return data, body, problems


def section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{2,3}}\s+{re.escape(heading)}\s*$\n?(.*?)(?=^#{{1,3}}\s+|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized in {"null", "none", "n/a", "na"} or normalized.startswith("pending")


def validate_one(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "errors": [],
        "warnings": [],
        "final_copy_characters": 0,
    }

    if not path.is_file():
        result["errors"].append(issue("error", "file-missing", "Post file does not exist."))
        return result

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        result["errors"].append(issue("error", "encoding", "Post file must be valid UTF-8."))
        return result

    metadata, body, parsing_problems = parse_frontmatter(text)
    for problem in parsing_problems:
        result["errors"].append(problem)

    for field in REQUIRED_FIELDS:
        if not metadata.get(field, "").strip():
            result["errors"].append(issue("error", "required-field", f"Missing required frontmatter field: {field}."))

    post_id = metadata.get("post_id", "")
    if post_id and not re.fullmatch(r"LI-\d{3,}", post_id):
        result["errors"].append(issue("error", "post-id", "post_id must match LI-### (three or more digits)."))

    status = metadata.get("status", "")
    if status and status not in ALLOWED_STATUSES:
        result["errors"].append(
            issue("error", "status", f"Unsupported status '{status}'. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}.")
        )

    pillar = metadata.get("pillar", "")
    if pillar and pillar not in ALLOWED_PILLARS:
        result["errors"].append(
            issue("error", "pillar", f"Unsupported pillar '{pillar}'. Allowed: {', '.join(sorted(ALLOWED_PILLARS))}.")
        )

    post_format = metadata.get("format", "")
    if post_format and post_format not in ALLOWED_FORMATS:
        result["errors"].append(
            issue("error", "format", f"Unsupported format '{post_format}'. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}.")
        )

    scheduled_at = metadata.get("scheduled_at", "")
    if scheduled_at:
        try:
            parsed = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("timezone offset missing")
        except ValueError:
            result["errors"].append(
                issue("error", "scheduled-at", "scheduled_at must be an ISO-8601 timestamp with a timezone offset.")
            )

    for field in PATH_FIELDS:
        raw_value = metadata.get(field, "").strip()
        if is_placeholder(raw_value) or re.match(r"^[a-z]+://", raw_value, re.IGNORECASE):
            continue
        target = (path.parent / raw_value).resolve()
        if not target.exists():
            result["errors"].append(
                issue("error", "linked-path", f"{field} path does not exist relative to the post: {raw_value}")
            )

    final_copy = section(body, "Final copy")
    result["final_copy_characters"] = len(final_copy)
    if status in FINAL_STATUSES and is_placeholder(final_copy):
        result["errors"].append(
            issue("error", "final-copy-required", f"Status '{status}' requires non-placeholder content under ## Final copy.")
        )
    if len(final_copy) > 3000:
        result["errors"].append(
            issue("error", "character-limit", f"Final copy is {len(final_copy)} characters; LinkedIn hard limit is 3,000.")
        )

    review_text = "\n".join(part for part in (section(body, "Working hook"), final_copy) if part)
    for code, pattern in AI_TELL_PATTERNS:
        if pattern.search(review_text):
            result["warnings"].append(
                issue("warning", code, f"Review wording matched the '{code}' pattern; keep only if specific and evidenced.")
            )

    has_numeric_claim = bool(PRECISE_NUMBER_PATTERN.search(review_text))
    research_path = metadata.get("research", "").strip()
    evidence_text = section(body, "Evidence") or section(body, "Required proof")
    if has_numeric_claim and is_placeholder(research_path) and is_placeholder(evidence_text):
        result["warnings"].append(
            issue(
                "warning",
                "numeric-evidence",
                "Precise numeric language appears without a research link or substantive Evidence/Required proof section.",
            )
        )

    result["valid"] = not result["errors"]
    return result


def print_human(results: list[dict[str, Any]]) -> None:
    for index, result in enumerate(results):
        if index:
            print()
        label = "PASS" if result.get("valid") else "FAIL"
        print(f"{label}: {result['path']}")
        for problem in result["errors"]:
            print(f"  ERROR [{problem['code']}] {problem['message']}")
        for warning in result["warnings"]:
            print(f"  WARNING [{warning['code']}] {warning['message']}")
        print(f"  Final copy characters: {result['final_copy_characters']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("post_files", nargs="+", type=Path, help="Markdown post file(s) to validate")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON results")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    results = [validate_one(path.resolve()) for path in args.post_files]
    if args.as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_human(results)

    has_errors = any(result["errors"] for result in results)
    has_warnings = any(result["warnings"] for result in results)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
