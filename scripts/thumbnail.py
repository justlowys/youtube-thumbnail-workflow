#!/usr/bin/env python3
"""End-to-end JustScale thumbnail orchestrator.

Wraps generate_bg.py and overlay_text.py into a single call. Given a video ID,
brand pic, style, and headline, produces the finished 1920x1080 thumbnail.
Optionally fetches the transcript to print the key pillars Claude should use
when picking labels / headlines.

Usage:
    python3 thumbnail.py \\
        --video-id 8KvqCneUvDI \\
        --brand-pic "16 smile-both" \\
        --style dense-whiteboard \\
        --headline "\\$500K BLUEPRINT" \\
        --labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,ATTRACT,CONVERT,DELIVER,SCALE,KPIs,REVENUE,PIPELINE,LTV,CAC,MRR" \\
        --output workspace/thumbs/blueprint.png
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


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


def fetch_transcript(video_id):
    """Try to pull the transcript via Supadata. Returns text or None."""
    env_file = Path.home() / "Documents" / "mission-control" / ".env.local"
    if not env_file.exists():
        return None
    key = None
    for line in env_file.read_text().splitlines():
        if line.startswith("SUPADATA_API_KEY="):
            key = line.split("=", 1)[1].strip()
            break
    if not key:
        return None
    try:
        import urllib.request
        url = (f"https://api.supadata.ai/v1/youtube/transcript"
               f"?videoId={video_id}&text=true")
        req = urllib.request.Request(url, headers={"x-api-key": key})
        with urllib.request.urlopen(req, timeout=15) as resp:
            import json
            data = json.loads(resp.read())
            return data.get("content", "")
    except Exception as e:
        print(f"Warning: transcript fetch failed: {e}", file=sys.stderr)
        return None


def run_script(name, args):
    cmd = ["python3", str(SCRIPTS / name)] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, file=sys.stdout)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    if result.stdout.strip():
        print(result.stdout.strip())


def parse_args():
    p = argparse.ArgumentParser(description="End-to-end JustScale thumbnail builder")
    p.add_argument("--video-id", help="YouTube video ID — used to print transcript pillars")
    p.add_argument("--brand-pic", required=True, help="Brand picture name prefix")
    p.add_argument("--style", required=True,
                   choices=["dense-whiteboard", "burning-paper", "cinematic-quote",
                            "split-cold-warm", "clean-portrait"],
                   help="Background style preset")
    p.add_argument("--headline", required=True, help="Headline text for the overlay")
    p.add_argument("--labels", default="", help="Comma-separated labels for dense-whiteboard")
    p.add_argument("--list", default="", help="Comma-separated list for burning-paper")
    p.add_argument("--pose", default="auto",
                   choices=["auto", "both-hands-up", "pointing-right", "arms-down",
                            "holding-paper"])
    p.add_argument("--mouth", default="closed", choices=["closed", "smile"])
    p.add_argument("--face-size", type=float, default=0.38)
    p.add_argument("--color", default="dark charcoal grey")
    p.add_argument("--highlight-color", default="blue")
    p.add_argument("--text-color", default="white")
    p.add_argument("--text-width-ratio", type=float, default=0.78)
    p.add_argument("--y-pos", type=float, default=0.78)
    p.add_argument("--banner-style", default="single", choices=["single", "split"])
    p.add_argument("--accent-word", default="")
    p.add_argument("--font-accent", default="sf",
                   choices=["sf", "playfair", "playfair-italic"])
    p.add_argument("--accent-highlight", action="store_true")
    p.add_argument("--output", required=True, help="Final output path")
    p.add_argument("--keep-bg", action="store_true",
                   help="Keep the intermediate bg file next to the output")
    return p.parse_args()


def main():
    args = parse_args()
    load_dotenv()

    if args.video_id:
        transcript = fetch_transcript(args.video_id)
        if transcript:
            print(f"Transcript loaded ({len(transcript)} chars). First 500 chars:")
            print(transcript[:500])
            print("---")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    bg_path = output.with_name(output.stem + "-bg.png")

    # Step 1 — generate bg
    gen_args = [
        "--brand-pic", args.brand_pic,
        "--style", args.style,
        "--pose", args.pose,
        "--mouth", args.mouth,
        "--face-size", str(args.face_size),
        "--color", args.color,
        "--output", str(bg_path),
    ]
    if args.labels:
        gen_args.extend(["--labels", args.labels])
    if args.list:
        gen_args.extend(["--list", args.list])
    print(f"[1/2] Generating background -> {bg_path}")
    run_script("generate_bg.py", gen_args)

    # Step 2 — overlay text
    ov_args = [
        "--bg", str(bg_path),
        "--headline", args.headline,
        "--output", str(output),
        "--highlight-color", args.highlight_color,
        "--text-color", args.text_color,
        "--text-width-ratio", str(args.text_width_ratio),
        "--y-pos", str(args.y_pos),
        "--banner-style", args.banner_style,
        "--font-accent", args.font_accent,
    ]
    if args.accent_word:
        ov_args.extend(["--accent-word", args.accent_word])
    if args.accent_highlight:
        ov_args.append("--accent-highlight")
    print(f"[2/2] Overlaying headline -> {output}")
    run_script("overlay_text.py", ov_args)

    if not args.keep_bg:
        try:
            bg_path.unlink()
        except Exception:
            pass

    print(f"Done: {output}")


if __name__ == "__main__":
    main()
