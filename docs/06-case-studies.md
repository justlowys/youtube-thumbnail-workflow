# 06 — Case Study Format

Client-win videos deserve their own format. This is Daniel Fazio's case study pattern — validated across millions of views on the Daniel Fazio / Client Ascension channel — packaged into `scripts/case_study.py`.

## Why case studies are different

Regular strategy thumbnails are hooks: they create curiosity about what's inside. Case study thumbnails are **proofs**: they deliver the headline value directly in the thumbnail. The click is for the story, not the outcome.

This flips the design:

- Regular thumbnail: face + teaser + curiosity gap
- Case study thumbnail: two faces + money number + time frame + no gap

## The Fazio formula

Look at any Daniel Fazio client interview thumbnail. They all follow the same pattern:

1. **Two real faces** side-by-side. Left half is one person (usually the creator), right half is the client. Both approximately equal scale, head + shoulders.
2. **Natural backgrounds** — whatever each person was shot on (home office, gaming chair, bookshelf). The backgrounds intentionally don't match, which is part of the authenticity.
3. **Money banner dead centre bottom** — `$XX,XXX/MO` in a bold red rectangle with white text.
4. **Time-frame sub-banner directly below** — `IN X MONTHS` or `IN X DAYS` in a white rectangle with black text.
5. **Drop shadows** on both banners (creates depth, not haloes, because the banners are opaque).
6. **SF Pro Heavy** for both banners.
7. **No clutter** — the two faces and the banner are literally the only elements.

That's it. No headline text on top. No extra graphics. No "CASE STUDY:" prefix (the format IS the case study signal).

## Why this works

- **Proof is immediate** — the money number is the headline
- **Authenticity** — real interview stills are always more credible than Gemini-generated faces
- **Fast comprehension** — 3 elements max, readable at 1/16th size on mobile
- **Trust signals** — the two faces plus real backgrounds create social proof without screaming "testimonial"
- **Competitive mimicry** — this format is now the industry standard for client wins, so viewers recognize it instantly as a case study

## How to build one

```bash
python3 scripts/case_study.py \
  --video-id VIDEO_ID \
  --amount '$17,259/MO' \
  --timeframe "IN 30 DAYS" \
  --frame-time 60 \
  --output out/case-study.png
```

The script:

1. Downloads the interview video via yt-dlp
2. Extracts a still frame at `--frame-time` seconds
3. Automatically detects and crops letterbox bars (top/bottom black bars)
4. Resizes to 1920x1080
5. Overlays the red money banner + white time-frame sub-banner
6. Applies drop shadows + unsharp mask
7. Saves

## Picking the right frame

Experiment with different `--frame-time` values until you find a moment where:

- Both faces are looking at camera (or at each other naturally)
- Both expressions are clean (no mid-blink, no weird mouth positions)
- Neither person is reaching off-frame or adjusting something
- The lighting is consistent across both sides

Common good moments:

- Right when the client says the money number
- During a laugh after the creator asks a question
- When both people are listening thoughtfully

Start with `--frame-time 60` and step through in 30-second increments.

## Format rules

- **Money format**: include `/MO` for MRR figures, `/YR` for annual, or no suffix for one-time amounts. Always use a comma in numbers over 1000. Always prefix with `$`.
- **Time frame**: be specific. "IN 30 DAYS", "IN 5 MONTHS", "IN 2 WEEKS". Not "FAST" or "QUICKLY".
- **Banner y-position**: default `--y-pos 0.72` works for most 16:9 interview stills. Move to 0.76 if the faces are cut off or 0.68 if there's too much headroom.

## What NOT to do

- **Don't generate client faces with Gemini.** You'll ship an obvious deepfake-looking thumbnail that destroys trust. Always use interview stills.
- **Don't use blue as the money banner colour.** Red is the industry standard. Changing to blue makes the thumbnail look like a generic business video, not a case study.
- **Don't add "CASE STUDY:" as a headline.** The format IS the signal.
- **Don't add extra graphics** (funnels, arrows, icons). Minimalism is part of the credibility.
- **Don't use stock photos** for missing faces. If you can't get a real interview still, skip this format entirely.

## When NOT to use this format

- **For educational / strategy videos.** Use `dense-whiteboard` or similar. The Fazio format is wasted on a framework explainer.
- **For personal lessons.** Use `cinematic-quote`.
- **For comparison videos.** Use `split-cold-warm`.
- **If you only have one face.** The two-face split is load-bearing. A solo case study should use a regular asymmetrical layout with a proof screenshot (Stripe dashboard, PayPal, bank balance).

## The two-face test

Before shipping a Fazio-style thumbnail, verify:

1. Are both faces recognizable at 1/16th size on mobile?
2. Is the money number readable without zooming?
3. Does the time frame subheader make the claim specific enough to be believable?

If yes to all three, ship it.
