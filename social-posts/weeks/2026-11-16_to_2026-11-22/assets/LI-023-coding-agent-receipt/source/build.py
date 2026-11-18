"""Set the FrontierCode data and generated comic on one 4:5 social card."""

import argparse
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SOURCE = Path(__file__).resolve().parent
SOCIAL_POSTS = SOURCE.parents[4]
FONT_DIR = SOCIAL_POSTS / "skills/style-ref-editorial/assets/fonts"
SCALE = 2

PAPER = "#FFFCF0"
INK = "#100F0F"
PLUM = "#7C3154"
SECONDARY = "#575653"
RULE = "#DAD8CE"
BUTTER = "#FFF1B8"
SKY = "#DFF2FF"
ROSE = "#FFE2E8"
REGULAR = "WorkSans-Regular.ttf"
BOLD = "WorkSans-Bold.ttf"
DISPLAY = "BricolageGrotesque-Bold.ttf"


@cache
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size * SCALE)


def draw_meme(output: Path) -> None:
    canvas = Image.new("RGB", (1080 * SCALE, 1350 * SCALE), PAPER)
    draw = ImageDraw.Draw(canvas)

    def label(x, y, value, size, face=REGULAR, color=INK, anchor="la"):
        draw.text((x * SCALE, y * SCALE), value, fill=color, font=font(face, size), anchor=anchor)

    def box(bounds, color):
        draw.rectangle(tuple(value * SCALE for value in bounds), fill=color)

    def rule(y):
        box((48, y, 1032, y + 1), RULE)

    label(540, 28, "GPT-6.2 Sol vs Claude Opus 5.5", 58, DISPLAY, anchor="ma")
    with Image.open(SOURCE / "budget-scene.png") as scene:
        illustration = ImageOps.fit(scene.convert("RGB"), (984 * SCALE, 532 * SCALE), Image.Resampling.LANCZOS)
        canvas.paste(illustration, (48 * SCALE, 108 * SCALE))

    label(48, 665, "FrontierCode 2.0", 48, DISPLAY)
    label(1032, 685, "132 coding tasks · max effort", 33, REGULAR, SECONDARY, anchor="ra")

    left_model = 605
    right_model = 884
    box((453, 737, 756, 836), SKY)
    box((756, 737, 1032, 836), ROSE)
    label(50, 768, "Coding agent", 36, BOLD)
    label(left_model, 747, "GPT-6.2 Sol", 37, BOLD, anchor="ma")
    label(right_model, 747, "Claude Opus 5.5", 32, BOLD, anchor="ma")
    label(left_model, 793, "Codex", 33, REGULAR, SECONDARY, anchor="ma")
    label(right_model, 793, "Claude Code", 33, REGULAR, SECONDARY, anchor="ma")

    box((48, 843, 1032, 926), BUTTER)
    label(65, 866, "Avg. API cost / attempt", 33, BOLD)
    label(left_model, 846, "$1.29", 62, DISPLAY, anchor="ma")
    label(right_model, 846, "$12.82", 62, DISPLAY, anchor="ma")

    for y, metric, sol, opus in (
        (943, "Attempts passed", "48.2%", "51.8%"),
        (1016, "Avg. output tokens", "38,100", "201,900"),
        (1100, "Standard API rates", "$2 / $10", "$4 / $20"),
    ):
        label(64, y, metric, 36, BOLD)
        label(left_model, y - 3, sol, 44, BOLD, anchor="ma")
        label(right_model, y - 3, opus, 44, BOLD, anchor="ma")
    rule(1004)
    rule(1089)
    label(64, 1146, "Input / output per 1M tokens", 29, REGULAR, SECONDARY)
    rule(1209)

    label(48, 1230, "Include retries in cost per passing task.", 39, BOLD, PLUM)
    label(48, 1290, "Cognition benchmark · Provider API list rates", 27, REGULAR, SECONDARY)
    label(1032, 1287, "madvibe.ai", 30, BOLD, anchor="ra")

    canvas.save(output, optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    draw_meme(parser.parse_args().output)
