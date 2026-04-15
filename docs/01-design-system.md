# 01 — The Design System

These are the hard rules. Every one was validated by a rejection. Break them at your peril.

## Typography

- **Font**: SF Pro (`/System/Library/Fonts/SFNS.ttf` on macOS)
- **Weight**: HEAVY — set via `font.set_variation_by_name("Heavy")`
  - Bold is too thin at thumbnail size
  - Black is too heavy and clogs the letterforms
  - Heavy is the sweet spot between them
- **Size**: fits to 78% of frame width, starts at 160-170pt and scales down
- **Position**: `y = H * 0.78` — not at the literal bottom edge, not at the middle
- **Optional accent**: Playfair Display Italic for a single accent word in editorial variants. Ships in `assets/fonts/`.

## Headline banner

- **ONE solid colour banner behind the whole phrase.** Not two adjacent coloured boxes unless it's the case study format.
- **Default colour**: electric blue `(0, 102, 255)` with white text. Reads clearly on any busy background.
- **Padding**: `pad_x = 22`, `pad_y_top = -6`, `pad_y_bot = 16` around the font metrics.
- **No drop shadows** on bright backgrounds — they create haloes.
- **No strokes** around the text — they look blocky and amateur.
- **Contrast is king** — if the bg is busy, darken the bottom 30% with a gradient first, THEN put the white-on-blue banner on top.

### Case study exception

For Fazio-style case study thumbnails:
- Red `(220, 30, 30)` main banner with white text for the money amount
- White sub-banner directly below with black text for the time-frame
- Drop shadows allowed on both (they're separate banners, shadows create depth not haloes)

## Face rules

When the face comes from Gemini (every style except case study):

- **Mouth closed** unless the source photo shows otherwise. Gemini will hallucinate open mouths and make you look like you're mid-sentence. Force closed lips in the prompt.
- **Face large and close**: head fills 35-40% of the vertical height, face spans y=15% to y=55%. This is tight enough to read at small thumbnail size on mobile.
- **Pose matches source**: don't tell Gemini to create a new pose. Tell it to match the source photo's pose. Gemini's pose hallucinations are worse than its face hallucinations.
- **Never let Gemini render text**. It hallucinates apostrophes, duplicates letters, and mangles spacing. Always PIL overlay.

## Labels on graphics

Any whiteboard, flowchart, funnel, or diagram in the background must use REAL CORRECTLY-SPELLED words from an explicit list. Pass `--labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,..."` to `generate_bg.py`.

If you don't pass a label list, Gemini invents gibberish like "Stredgy", "Flowher", "RevenueKPI" — and your thumbnail looks like AI slop. The word list is how you stop this.

The words should come from the video's actual transcript or a fixed list of your channel's terminology. If the word isn't something a viewer could plausibly read in context, don't include it.

## Output resolution

- **Always upscale to 1920x1080** with LANCZOS resize + UnsharpMask filter.
- Gemini Nano Banana Pro outputs 1376x768 natively. YouTube wants HD minimum. Anything smaller reads as low-production.
- `img.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))`

## File organization

- Source headshots live in `brand_pictures_dir` (from `profile.json`)
- Name each headshot by expression: `01 neutral-slight-smile.jpg`, `07 explaining-mouth-open.jpg`, `12 both-hands-raised.jpg`
- Reference thumbnails (inspiration) live wherever you want — the scripts don't require them, but you should Read them visually before picking a style

## What this system won't do

- It won't pick a style for you. You (or your collaborator) still decides whether the video is a strategy framework, a case study, a personal lesson, or a comparison.
- It won't write the headline. The headline has to come from the video's actual content.
- It won't validate the word list. If you pass nonsense labels, Gemini will draw nonsense labels.
- It won't create multi-face compositions outside the case study path.
