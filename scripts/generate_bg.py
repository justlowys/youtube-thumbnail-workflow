#!/usr/bin/env python3
"""Generate a Gemini background for a JustScale thumbnail.

Bakes in the strict face constraints (mouth closed, face large, pose from
source) and style presets so callers only specify the high-level intent.

Usage:
    python3 generate_bg.py \\
        --brand-pic "16 smile-both-hands" \\
        --style dense-whiteboard \\
        --labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,..." \\
        --output workspace/thumbs/blueprint-bg.png
"""
import argparse
import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = SKILL_ROOT / "profile.json"


def load_profile():
    """Load the creator profile from profile.json. Falls back to defaults
    if profile.json is missing (the user will then need to pass flags)."""
    defaults = {
        "creator_name": "the creator",
        "channel_handle": "",
        "face_description": "a person from the attached headshot photos",
        "brand_pictures_dir": "~/Downloads/Brand Pictures",
        "default_outfit": "",
        "default_accent_color": "blue",
        "case_study_accent_color": "red",
        "channel_description": "",
    }
    if PROFILE_PATH.exists():
        try:
            loaded = json.loads(PROFILE_PATH.read_text())
            defaults.update(loaded)
        except Exception as e:
            print(f"Warning: profile.json exists but failed to parse: {e}",
                  file=sys.stderr)
    return defaults


PROFILE = load_profile()
BRAND_PICTURES_DIR = Path(os.path.expanduser(PROFILE["brand_pictures_dir"]))

# === Style preset prompts ===
# Each template has {face_block}, {content_block} placeholders.

FACE_BLOCK = (
    "Subject: {face_desc} from attached headshot photos — match face EXACTLY. "
    "{mouth}{outfit}. FACE LARGE AND CLOSE — head fills approximately "
    "{face_frac}% of vertical height, face spans y=15% to y=55%. {pose}"
)

STYLE_TEMPLATES = {
    "dense-whiteboard": (
        "YouTube thumbnail 16:9. {face_block} "
        "BACKGROUND: extremely dense cluttered white whiteboard filling the "
        "frame with hand-drawn marker diagrams around the subject. "
        "{content_block} "
        "Black, blue, green, red markers. Authentic hand-drawn marker style. "
        "Every text label must be a REAL CORRECTLY-SPELLED ENGLISH word from "
        "my list, written in clear marker handwriting that a viewer can read. "
        "NO made-up words, NO gibberish."
    ),
    "burning-paper": (
        "YouTube thumbnail 16:9. {face_block} "
        "BACKGROUND: the subject holds a piece of white lined notebook paper "
        "in his left hand, mid-burn with bright orange flames consuming the "
        "right edge of the paper, smoke rising. Dark moody warm-lit background. "
        "The paper shows a written list: {content_block}. "
        "Marker writing style, some items circled or underlined in red marker. "
        "NO other text anywhere in the frame besides the list."
    ),
    "cinematic-quote": (
        "YouTube thumbnail 16:9. {face_block} "
        "BACKGROUND: dark cinematic documentary-style portrait with warm "
        "out-of-focus bookshelves and moody lighting behind him. Shallow depth "
        "of field. No clutter, no text, no objects besides the blurred "
        "bookshelf. Premium editorial portrait vibe."
    ),
    "split-cold-warm": (
        "YouTube thumbnail 16:9. {face_block} "
        "BACKGROUND: vertical split — left half solid vibrant red, right half "
        "solid vibrant blue. Subject centered straddling the split. "
        "No text, no labels, no other objects. Dramatic flat colour blocks."
    ),
    "clean-portrait": (
        "YouTube thumbnail 16:9. {face_block} "
        "BACKGROUND: solid {color} backdrop with a subtle radial vignette "
        "(brighter center, darker edges). Premium editorial portrait. No "
        "clutter, no text, no other objects."
    ),
}

POSE_TEMPLATES = {
    "auto": "Pose matches the source brand photo exactly.",
    "both-hands-up": "Both hands raised open-palmed at shoulder height in a "
                     "'presenting the system' gesture.",
    "pointing-right": "Right hand raised, index finger pointing to the right "
                      "side of the frame.",
    "arms-down": "Arms relaxed at his sides. NO hands, NO fingers, NO arms "
                 "visible in the frame. Only head and upper chest.",
    "holding-paper": "Left hand holds a burning piece of notebook paper at "
                     "chest height, right hand relaxed.",
}


def load_dotenv():
    candidates = [
        Path(__file__).resolve().parents[1] / ".env",
        Path.home() / ".claude" / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
            return
    return


def find_brand_pic(name_prefix):
    """Find a brand picture by partial name match."""
    if not BRAND_PICTURES_DIR.exists():
        print(f"Error: {BRAND_PICTURES_DIR} does not exist", file=sys.stderr)
        sys.exit(1)
    candidates = sorted(BRAND_PICTURES_DIR.glob("*.jpg"))
    for c in candidates:
        if name_prefix.lower() in c.stem.lower():
            return c
    print(f"Error: no brand picture matching '{name_prefix}' in {BRAND_PICTURES_DIR}",
          file=sys.stderr)
    print("Available:", file=sys.stderr)
    for c in candidates:
        print(f"  {c.name}", file=sys.stderr)
    sys.exit(1)


def build_content_block(style, labels, list_items):
    if style == "dense-whiteboard":
        if not labels:
            print("Error: --labels required for dense-whiteboard style", file=sys.stderr)
            sys.exit(1)
        label_list = ", ".join(labels.split(","))
        return (
            f"LABEL THE DIAGRAMS WITH THESE EXACT WORDS (use these specific "
            f"words, spelled correctly): {label_list}. "
            f"Draw diagrams: a SALES FUNNEL labeled with the pipeline stages, "
            f"a FLOWCHART of the ATTRACT -> CONVERT -> DELIVER -> SCALE "
            f"pipeline, a RISING LINE GRAPH labeled REVENUE with dollar signs, "
            f"a BAR CHART, KPI labels with up-arrows, scattered green dollar "
            f"signs, percentage symbols, circled numbers, a small calendar "
            f"grid, a network web of connected circles, checkmark boxes, and "
            f"connecting arrows. Use ONLY the real words I listed."
        )
    if style == "burning-paper":
        if not list_items:
            print("Error: --list required for burning-paper style", file=sys.stderr)
            sys.exit(1)
        items = list_items.split(",")
        numbered = "\n".join(f"{i+1}. {item.strip()}" for i, item in enumerate(items))
        return f"The list on the paper reads:\n{numbered}"
    return ""


def build_prompt(args):
    mouth = "MOUTH CLOSED (lips sealed, no teeth, no open mouth). " \
        if args.mouth == "closed" else "slight confident closed-mouth smile. "
    outfit = f", wearing {args.outfit}" if args.outfit else ""
    pose = POSE_TEMPLATES.get(args.pose, POSE_TEMPLATES["auto"])
    face_desc = args.face_description or PROFILE["face_description"]
    face_block = FACE_BLOCK.format(
        face_desc=face_desc,
        mouth=mouth,
        outfit=outfit,
        face_frac=int(args.face_size * 100),
        pose=pose,
    )
    content_block = build_content_block(args.style, args.labels, args.list)
    template = STYLE_TEMPLATES[args.style]
    prompt = template.format(
        face_block=face_block,
        content_block=content_block,
        color=args.color,
    )
    return prompt


def parse_args():
    p = argparse.ArgumentParser(description="Generate a JustScale thumbnail background via Gemini")
    p.add_argument("--brand-pic", required=True,
                   help="Brand picture name prefix (e.g. '16 smile-both-hands' or 'smile-both')")
    p.add_argument("--style", required=True, choices=list(STYLE_TEMPLATES.keys()),
                   help="Style preset")
    p.add_argument("--labels", default="",
                   help="Comma-separated label words for dense-whiteboard style")
    p.add_argument("--list", default="",
                   help="Comma-separated list items for burning-paper style")
    p.add_argument("--pose", default="auto",
                   choices=list(POSE_TEMPLATES.keys()),
                   help="Pose preset (auto = match source photo)")
    p.add_argument("--mouth", default="closed", choices=["closed", "smile"],
                   help="Mouth state — closed is the default winning-formula rule")
    p.add_argument("--face-size", type=float, default=0.38,
                   help="Face fills this fraction of vertical height (default 0.38)")
    p.add_argument("--color", default="dark charcoal grey",
                   help="Background color for clean-portrait style")
    p.add_argument("--face-description", default="",
                   help="Override profile.json face_description for this run")
    p.add_argument("--outfit", default=PROFILE["default_outfit"],
                   help="Clothing description (default from profile)")
    p.add_argument("--extra-headshot", nargs="*", default=[],
                   help="Additional brand picture name prefixes to pass as face references")
    p.add_argument("--output", required=True, help="Output path")
    return p.parse_args()


def main():
    args = parse_args()
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    client = genai.Client(api_key=api_key)

    headshots = [find_brand_pic(args.brand_pic)]
    for extra in args.extra_headshot:
        headshots.append(find_brand_pic(extra))

    prompt = build_prompt(args)
    contents = [prompt]
    for h in headshots:
        contents.append(Image.open(h))

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
        ),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data is not None:
            img = part.as_image()
            img.save(str(output_path))
            print(f"Saved: {output_path}")
            return
    print("Error: no image in Gemini response", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
