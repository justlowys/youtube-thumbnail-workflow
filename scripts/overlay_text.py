#!/usr/bin/env python3
"""Overlay the JustScale winning-formula headline on a generated background.

Defaults: SF Pro Heavy, single solid blue banner (0, 102, 255), white text,
78% frame width, y=0.78, LANCZOS upscale to 1920x1080 + UnsharpMask.

Usage:
    python3 overlay_text.py \\
        --bg workspace/thumbs/blueprint-bg.png \\
        --headline "\\$500K BLUEPRINT" \\
        --output workspace/thumbs/blueprint-final.png
"""
import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


SF_FONT = "/System/Library/Fonts/SFNS.ttf"
SKILL_ROOT = Path(__file__).resolve().parents[1]
PLAYFAIR_FONT = SKILL_ROOT / "assets" / "fonts" / "PlayfairDisplay.ttf"
PLAYFAIR_ITALIC_FONT = SKILL_ROOT / "assets" / "fonts" / "PlayfairDisplay-Italic.ttf"

COLORS = {
    "blue":    (0, 102, 255),
    "red":     (220, 30, 30),
    "navy":    (18, 30, 74),
    "charcoal":(22, 22, 28),
    "yellow":  (255, 215, 30),
    "white":   (255, 255, 255),
}


def make_sf(size, variation="Heavy"):
    f = ImageFont.truetype(SF_FONT, size)
    try:
        f.set_variation_by_name(variation)
    except Exception:
        pass
    return f


def make_playfair(size, italic=False, variation="Black"):
    path = PLAYFAIR_ITALIC_FONT if italic else PLAYFAIR_FONT
    if not path.exists():
        print(f"Warning: Playfair font not found at {path}, falling back to SF Pro",
              file=sys.stderr)
        return make_sf(size, "Heavy")
    f = ImageFont.truetype(str(path), size)
    try:
        if italic and "Italic" not in variation:
            variation = f"{variation} Italic"
        f.set_variation_by_name(variation)
    except Exception:
        pass
    return f


def fit_font(draw, text, max_w, font_factory, start_size=170, min_size=50):
    size = start_size
    while size > min_size:
        f = font_factory(size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 4
    return font_factory(min_size)


def render(args):
    img = Image.open(args.bg).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    text = args.headline
    max_w = int(W * args.text_width_ratio)
    color_bg = COLORS.get(args.highlight_color, COLORS["blue"])
    color_text = COLORS.get(args.text_color, COLORS["white"])

    if args.accent_word and args.banner_style == "split":
        parts = text.split(args.accent_word, 1)
        part1 = parts[0].rstrip()
        part2 = args.accent_word
        part3 = parts[1].lstrip() if len(parts) > 1 else ""

        font1 = fit_font(draw, part1, max_w // 2, lambda s: make_sf(s, "Heavy"))
        # Use same size for consistency
        size1 = font1.size
        if args.font_accent == "playfair-italic":
            font2 = make_playfair(size1, italic=True)
        elif args.font_accent == "playfair":
            font2 = make_playfair(size1, italic=False)
        else:
            font2 = make_sf(size1, "Heavy")
        font3 = make_sf(size1, "Heavy")

        w1 = draw.textbbox((0, 0), part1, font=font1)[2] if part1 else 0
        w2 = draw.textbbox((0, 0), part2, font=font2)[2]
        w3 = draw.textbbox((0, 0), part3, font=font3)[2] if part3 else 0
        asc = max(font1.getmetrics()[0], font2.getmetrics()[0], font3.getmetrics()[0])
        gap = int(size1 * 0.08)
        total_w = w1 + (gap if part1 else 0) + w2 + (gap if part3 else 0) + w3
        x = (W - total_w) // 2
        y = int(H * args.y_pos)

        pad_x = 18
        draw.rectangle(
            [x - pad_x, y - 4, x + total_w + pad_x, y + asc + 14],
            fill=color_bg,
        )
        cx = x
        if part1:
            draw.text((cx, y), part1, fill=color_text, font=font1)
            cx += w1 + gap
        draw.text((cx, y), part2, fill=COLORS["yellow"] if args.accent_highlight else color_text,
                  font=font2)
        cx += w2
        if part3:
            cx += gap
            draw.text((cx, y), part3, fill=color_text, font=font3)

    else:
        font = fit_font(draw, text, max_w, lambda s: make_sf(s, "Heavy"))
        b = draw.textbbox((0, 0), text, font=font)
        tw = b[2] - b[0]
        asc, desc = font.getmetrics()
        x = (W - tw) // 2
        y = int(H * args.y_pos)

        pad_x = 22
        draw.rectangle(
            [x - pad_x, y - 6, x + tw + pad_x, y + asc + 16],
            fill=color_bg,
        )
        draw.text((x, y), text, fill=color_text, font=font)

    img = img.resize((1920, 1080), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"Saved: {out}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--bg", required=True, help="Background image path")
    p.add_argument("--headline", required=True, help="Headline text")
    p.add_argument("--output", required=True, help="Output path")
    p.add_argument("--highlight-color", default="blue",
                   choices=list(COLORS.keys()), help="Banner background color")
    p.add_argument("--text-color", default="white",
                   choices=list(COLORS.keys()), help="Text color")
    p.add_argument("--text-width-ratio", type=float, default=0.78,
                   help="Fit headline to this fraction of frame width (default 0.78)")
    p.add_argument("--y-pos", type=float, default=0.78,
                   help="Vertical position as fraction (default 0.78)")
    p.add_argument("--banner-style", default="single",
                   choices=["single", "split"],
                   help="single = one solid banner (default), split = split parts")
    p.add_argument("--accent-word", default="",
                   help="Word to render in accent font (for split style)")
    p.add_argument("--font-accent", default="sf",
                   choices=["sf", "playfair", "playfair-italic"],
                   help="Font for the accent word")
    p.add_argument("--accent-highlight", action="store_true",
                   help="Render the accent word in yellow")
    return p.parse_args()


if __name__ == "__main__":
    render(parse_args())
