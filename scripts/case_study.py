#!/usr/bin/env python3
"""Case study thumbnail (two-faces-plus-money-banner format).

Downloads a YouTube video, extracts a still frame with both faces, crops grey
bars, and overlays the red/white money banner + time-frame subheader.

Usage:
    python3 case_study.py \\
        --video-id kDxl9sGOwqU \\
        --amount "\\$17,259/MO" \\
        --timeframe "IN 30 DAYS" \\
        --frame-time 60 \\
        --output workspace/thumbs/case-study.png
"""
import argparse
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


SF_FONT = "/System/Library/Fonts/SFNS.ttf"


def sf(size, variation="Heavy"):
    f = ImageFont.truetype(SF_FONT, size)
    try:
        f.set_variation_by_name(variation)
    except Exception:
        pass
    return f


def download_video(video_id, out_dir):
    out_file = out_dir / f"{video_id}.mp4"
    if out_file.exists():
        return out_file
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["yt-dlp", "-f", "best[height<=720]", "-o", str(out_file),
         f"https://www.youtube.com/watch?v={video_id}"],
        check=True,
    )
    return out_file


def extract_frame(video_path, time_sec, out_path):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(time_sec), "-i", str(video_path),
         "-frames:v", "1", "-q:v", "2", str(out_path)],
        check=True, capture_output=True,
    )
    return out_path


def remove_letterbox(img):
    arr = np.array(img)
    row_stds = arr.std(axis=(1, 2))
    active = np.where(row_stds > 10)[0]
    if len(active) > 0:
        y_top = int(active[0])
        y_bot = int(active[-1])
        img = img.crop((0, y_top, img.size[0], y_bot + 1))
    return img


def render(args):
    tmp = Path("/tmp/thumbnail_case_study")
    video_path = download_video(args.video_id, tmp)
    frame_path = tmp / f"{args.video_id}_{args.frame_time}.jpg"
    extract_frame(video_path, args.frame_time, frame_path)

    img = Image.open(frame_path).convert("RGB")
    img = remove_letterbox(img)
    img = img.resize((1920, 1080), Image.LANCZOS)
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Main red banner
    main_text = args.amount
    max_w = int(W * 0.56)
    size = 170
    while size > 50:
        f = sf(size, "Heavy")
        if draw.textbbox((0, 0), main_text, font=f)[2] <= max_w:
            main_font = f; break
        size -= 4

    mb = draw.textbbox((0, 0), main_text, font=main_font)
    mw = mb[2] - mb[0]
    main_asc = main_font.getmetrics()[0]

    # Subheader
    sub_text = args.timeframe
    sub_size = int(size * 0.55)
    sub_font = sf(sub_size, "Heavy")
    sb = draw.textbbox((0, 0), sub_text, font=sub_font)
    sw = sb[2] - sb[0]
    sub_asc = sub_font.getmetrics()[0]

    stack_top = int(H * args.y_pos)
    main_pad_x = 32
    main_pad_y_top = 8
    main_pad_y_bot = 22
    main_bx0 = (W - mw) // 2 - main_pad_x
    main_bx1 = (W - mw) // 2 + mw + main_pad_x
    main_by0 = stack_top - main_pad_y_top
    main_by1 = stack_top + main_asc + main_pad_y_bot

    sub_pad_x = 24
    sub_pad_y_top = 6
    sub_pad_y_bot = 18
    sub_bx0 = (W - sw) // 2 - sub_pad_x
    sub_bx1 = (W - sw) // 2 + sw + sub_pad_x
    sub_by0 = main_by1 - 2
    sub_by1 = main_by1 + sub_asc + sub_pad_y_top + sub_pad_y_bot

    shadow_offset = 6
    # Drop shadows
    draw.rectangle(
        [main_bx0 + shadow_offset, main_by0 + shadow_offset,
         main_bx1 + shadow_offset, main_by1 + shadow_offset],
        fill=(0, 0, 0),
    )
    draw.rectangle(
        [sub_bx0 + shadow_offset, sub_by0 + shadow_offset,
         sub_bx1 + shadow_offset, sub_by1 + shadow_offset],
        fill=(0, 0, 0),
    )
    # Red main banner
    draw.rectangle([main_bx0, main_by0, main_bx1, main_by1], fill=(220, 30, 30))
    draw.text(((W - mw) // 2, stack_top), main_text, fill=(255, 255, 255), font=main_font)
    # White sub banner
    draw.rectangle([sub_bx0, sub_by0, sub_bx1, sub_by1], fill=(255, 255, 255))
    draw.text(((W - sw) // 2, main_by1 - 2 + sub_pad_y_top), sub_text,
              fill=(20, 20, 24), font=sub_font)

    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"Saved: {out}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--video-id", required=True, help="YouTube video ID")
    p.add_argument("--amount", required=True, help="Money amount, e.g. '$17,259/MO'")
    p.add_argument("--timeframe", required=True, help="Time frame, e.g. 'IN 30 DAYS'")
    p.add_argument("--frame-time", type=int, default=60,
                   help="Time in seconds to extract the frame from (default 60)")
    p.add_argument("--y-pos", type=float, default=0.72,
                   help="Banner y position as fraction of height (default 0.72)")
    p.add_argument("--output", required=True, help="Output path")
    return p.parse_args()


if __name__ == "__main__":
    render(parse_args())
