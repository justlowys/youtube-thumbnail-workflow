# YouTube Thumbnail SOP

A complete, repeatable process for producing high-converting YouTube thumbnails using AI background generation + PIL text overlay. Hardened over 100+ real iterations on a published channel. Use this as the single source of truth for any thumbnail work.

---

## What this is

A pipeline that turns the hardest parts of YouTube thumbnails into defaults, not guesses. You bring a video topic, a face, and a rough idea. The pipeline returns a 1920x1080 PNG ready to upload.

**What it handles automatically:**

- Strict face matching via Gemini 3 Pro Image Preview (Nano Banana Pro). Mouth closed unless source shows otherwise. Head large in frame (35-40% vertical). Pose taken from the source photo, never invented.
- Real labels on whiteboards or graphic content. You pass a word list, the script tells Gemini to use only those words. No gibberish placeholders.
- Single-banner headlines rendered by PIL with SF Pro Heavy at 78% frame width, upscaled to 1920x1080. Never Gemini-rendered text (Gemini hallucinates apostrophes, duplicates letters, mangles spacing).
- Fazio-style case study format. Pulls a still from the actual interview video, crops letterbox, renders red money banner + white time-frame subheader.

**Why it exists:** most thumbnail tools either over-promise AI magic (every output looks the same) or under-deliver (every judgment call left to you). This sits in the middle. Every default in here was validated against the rejection pile.

---

## Prerequisites

### System

- macOS or Linux (the scripts use `/System/Library/Fonts/SFNS.ttf` on macOS by default. On Linux, install SF Pro or substitute another Heavy-weight sans-serif and update the font path in `scripts/overlay_text.py`).
- Python 3.10+
- `yt-dlp` and `ffmpeg` (only required for the case study workflow, optional otherwise)

### Install

```bash
git clone https://github.com/<your-fork>/youtube-thumbnail-workflow.git
cd youtube-thumbnail-workflow
pip install Pillow google-genai numpy
brew install yt-dlp ffmpeg   # optional, only for case studies
```

### API keys

Put these in `.env` at the project root (or in `~/.claude/.env` if using inside Claude Code):

```
GEMINI_API_KEY=your-key-here
SUPADATA_API_KEY=your-key-here   # optional, only for auto-transcript fetching
```

Get a Gemini key at https://aistudio.google.com/. Supadata is optional but recommended for pulling YouTube transcripts.

---

## One-time setup

### Step 1. Create your two working folders

The pipeline reads from two folders that you maintain by hand. Create them anywhere on disk:

```bash
mkdir -p ~/Pictures/Brand\ Pictures
mkdir -p ~/Pictures/Reference\ Thumbnails
```

You can use any path. The defaults in `profile.example.json` point at `~/Downloads/Brand Pictures`. Pick something stable and update your `profile.json` to match.

**Folder 1 — `Brand Pictures`** (5 to 15 photos of yourself)

This is your curated face library. The Gemini script picks one photo per generation and uses it as the face reference. Quality of these photos determines quality of every thumbnail.

Rules:
- Studio or well-lit photos only. No phone selfies, no dim room shots, no gaming-chair-with-LEDs photos.
- Mix of expressions across the set: neutral, slight smile, serious, shocked, explaining, pointing, both hands raised, arms crossed, hand on chin.
- Name each file with a short expression label so you can pick by intent later. Numbered prefix is optional but helps sorting:
  ```
  01 neutral-slight-smile.jpg
  02 calm-neutral.jpg
  03 shock-wide-eyes.jpg
  06 open-hands-explain.jpg
  09 pointing-finger-right.jpg
  12 both-hands-raised.jpg
  14 smile-neutral.jpg
  ```
- This folder is the source of truth. If a photo is in here, the pipeline assumes it's approved. Remove anything you don't want appearing on a thumbnail.

**Folder 2 — `Reference Thumbnails`** (10 to 50 reference images)

A library of thumbnails you'd happily clone the style of. Save them by right-click → Save Image from YouTube. Sources to mine:
- Top creators in your niche (highest view-count videos)
- Creators in adjacent niches whose style you admire
- Specific formats you want to replicate (whiteboard explainer, money banner, split before/after, burning paper, etc.)

When picking a reference for a new thumbnail, scan visually. Filenames are meaningless. Open the folder in Finder or use a viewer. Pick the one whose composition matches the message of the new video, not just the vibe.

### Step 2. Write your profile

```bash
cp profile.example.json profile.json
```

Edit `profile.json`:

```json
{
  "creator_name": "Your Name",
  "channel_handle": "@yourhandle",
  "face_description": "describe yourself the way you'd describe a stranger at a party. Include: age range, ethnicity, face shape, hair colour and style, glasses, facial hair, distinctive features. Specific beats generic.",
  "brand_pictures_dir": "~/Pictures/Brand Pictures",
  "default_outfit": "black t-shirt",
  "default_accent_color": "blue",
  "case_study_accent_color": "red",
  "channel_description": "optional: 1 sentence about what your channel covers, used as a hint for whiteboard content"
}
```

The `face_description` is the most important field. Bad descriptions make Gemini hallucinate features. Good descriptions make the face look like you 90% of the time.

**Examples that work:**
- "young asian man, round youthful face, dark bowl-cut hair, round black wire-frame glasses, clean-shaven, early twenties"
- "middle-aged white man, short brown beard with grey at the chin, short brown hair, dark brown eyes, square jaw, mid-thirties"
- "black woman in her late twenties, natural curly hair pulled back, brown eyes, no glasses, full lips, warm brown skin"

`profile.json` is gitignored. Yours stays local.

---

## The pipeline (every thumbnail follows these 6 steps)

### Step 1. Scan references and brand pictures visually

Before opening a script, look at what you already have.

```bash
open ~/Pictures/Reference\ Thumbnails/
open ~/Pictures/Brand\ Pictures/
```

Pick one reference style. Pick one brand picture whose pose and expression match the video's energy. Never pick by filename. Open the image, look at it, decide.

### Step 2. Pull the video transcript

The thumbnail must reference what the video actually says. Generic hooks underperform.

If you have a Supadata key:
```bash
KEY=$(grep SUPADATA_API_KEY .env | cut -d= -f2)
curl -s -H "x-api-key: $KEY" \
  "https://api.supadata.ai/v1/youtube/transcript?videoId=VIDEO_ID&text=true"
```

If you don't, copy the transcript out of YouTube Studio or use any free transcript tool. From the transcript, extract:
- 2 to 3 specific claims (numbers, terminology, frameworks the video actually uses)
- The single sharpest line that captures the video's promise
- Any specific labels you'll want on a whiteboard graphic (e.g. "DM, CALL, CLOSE, CONTRACT" for a sales video)

The thumbnail headline and any on-graphic labels come from this list. Never invent.

### Step 3. Generate the background

```bash
python3 scripts/generate_bg.py \
  --brand-pic "12 both-hands-raised" \
  --style dense-whiteboard \
  --labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,ATTRACT,CONVERT,DELIVER,SCALE,KPIs,REVENUE,PIPELINE,LTV,CAC,MRR" \
  --output workspace/thumb-bg.png
```

The script automatically:
- Loads your face description from `profile.json`
- Picks the brand picture matching the `--brand-pic` substring
- Sends the photo + your face description + style constraints to Gemini
- Forces "no text" so Gemini doesn't try to render the headline

**Available styles:**

| Style | Use for |
|---|---|
| `dense-whiteboard` | Strategy, framework, system, business-process videos. Cluttered hand-drawn marker diagrams. |
| `burning-paper` | "Mistakes" / "what not to do" / negative-list videos. Subject holds a burning notebook. |
| `cinematic-quote` | Personal / authority / lesson videos. Dark moody portrait, room for a quote-style headline. |
| `split-cold-warm` | Comparison / before-after / this-vs-that videos. Vertical red/blue split. |
| `clean-portrait` | PFPs, simple hook videos, clean brand shots. Solid colour background with vignette. |

Always pass `--labels` for `dense-whiteboard`. Without explicit labels, Gemini invents misspelled gibberish.

### Step 4. Overlay the headline

```bash
python3 scripts/overlay_text.py \
  --bg workspace/thumb-bg.png \
  --headline '$500K BLUEPRINT' \
  --output workspace/thumb-final.png
```

Defaults applied automatically:
- SF Pro Heavy weight (between Bold and Black, the validated sweet spot)
- Single solid coloured banner (your `default_accent_color`)
- White text inside the banner
- 78% frame width, positioned at y=0.78
- LANCZOS upscale to 1920x1080 + UnsharpMask for crispness

For editorial variants with an italic accent word, the script supports a split banner using Playfair Display Italic. See `scripts/overlay_text.py --help`.

### Step 5. Or run end-to-end

```bash
python3 scripts/thumbnail.py \
  --video-id VIDEO_ID \
  --brand-pic "12 both-hands-raised" \
  --style dense-whiteboard \
  --headline '$500K BLUEPRINT' \
  --labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,ATTRACT,CONVERT,DELIVER,SCALE" \
  --output out/thumb.png
```

One call: transcript fetch (if Supadata key is set), background generation, text overlay, final upscaled image.

### Step 6. Ship one. Wait for feedback. Fix the specific thing.

Do not generate 4 variants by default. Pick the right concept from context, ship one, iterate based on real feedback. The translation table below covers most feedback in one fix per round.

---

## Case study format (Fazio-style)

For client-win videos ("How [name] made $X in Y time"), the format is different. Two real faces side-by-side, money banner center-bottom. Modeled on Daniel Fazio's channel.

```bash
python3 scripts/case_study.py \
  --video-id kDxl9sGOwqU \
  --amount '$17,259/MO' \
  --timeframe "IN 30 DAYS" \
  --frame-time 60 \
  --output out/case-study.png
```

The script:
1. Downloads the video with `yt-dlp`
2. Extracts a frame at `--frame-time` seconds (pick a moment showing both faces)
3. Crops letterbox bars
4. Renders the red money banner + white time-frame subheader

**Hard rules for case studies:**
- Two real faces, not silhouettes, not question marks. If you don't have a clean photo of the client, pull a frame from the interview video itself.
- Red banner `(220, 30, 30)` with white text. Not blue. Red is the industry standard for money claims.
- Money on top in big SF Pro Heavy: `$XX,XXX/MO`
- Time-frame subheader directly below in smaller bold sans: `IN X MONTHS` or `IN X DAYS`. Be specific. Never "FAST" or "QUICKLY".
- No "CASE STUDY:" prefix. The format is the signal.
- No extra clutter. Just two faces + the banner.
- Never let Gemini generate the client's face. Always use real interview stills.

---

## Hard rules (the design system)

These are non-negotiable defaults:

- **Single solid banner headline.** Not two split colours. (Case study is the exception: red money on top, white time-frame below.)
- **SF Pro Heavy weight.** Bold is too thin. Black is too heavy. Heavy is the sweet spot.
- **Real correctly-spelled words on any whiteboard or graphic content.** Pass them via `--labels`. Never let Gemini invent.
- **Face large and close.** 35 to 40% of vertical height. Face spans roughly y=15 to y=55%.
- **Mouth closed by default.** Open only if the source photo shows it open.
- **Pose matches the source brand picture.** Don't ask Gemini to invent a new pose.
- **Always upscale to 1920x1080.** LANCZOS resize + UnsharpMask filter. YouTube wants HD minimum.
- **PIL overlay for all text.** Never let Gemini render headlines. It hallucinates.
- **Case studies use real interview stills only.** Never Gemini-generated client faces.
- **Headline text complements the title, never repeats it.** Title says the WHAT. Thumbnail says the FEELING.
- **Maximum 3 distinct visual elements per thumbnail.** More than that becomes unreadable on mobile.
- **Bottom-right corner stays clear.** YouTube's video timestamp overlay covers it.

---

## Iteration translation table

Most feedback is vague. Translate it literally and change only the specific thing. Don't re-architect on every round.

| Collaborator says | Specific fix |
|---|---|
| face too small / too low | regenerate with `--face-size 0.42` |
| mouth weird | confirm `--mouth closed` (default) or pick a source photo with the mouth open |
| doesn't look like me | try a different brand picture, or refine `face_description` in `profile.json` |
| wrong words on the graphic | pass a real `--labels` word list, exact spellings |
| headline too big / too small | adjust `--text-width-ratio` by 0.05 |
| two highlights | use default `--banner-style single` |
| different colour | spawn 3 to 4 colour variants in parallel, present visually |
| graphic too simple | iterate the `--labels` list (more words = denser) or try a different style |
| doesn't pop | check banner colour contrasts the background. On bright backgrounds, add a dark gradient under the headline before drawing text. |
| too dark | switch black text to navy or electric blue for the same darkness with better readability |
| text too low | move from bottom edge to y=0.72 |
| not 4K | confirm the LANCZOS + UnsharpMask upscale ran. Output should be 1920x1080. |
| give me variations | spawn 3 to 4 parallel runs, send images back, never describe options in text |
| use another reference | literal. Try a different reference style. |

---

## Dead ends. Do not repeat.

Tried and rejected over 100+ iterations:

- **Insightface inswapper_128 face-swap.** Face always looks 70% you, never 100%. Hard quality ceiling.
- **Landmark-based face paste from arbitrary source photo.** Hard edges, lighting mismatch.
- **PIL composite from scratch (cutout + new background).** Looks thin and generic.
- **Gemini-rendered text.** Hallucinates apostrophes, duplicates letters, mangles spacing. Always.
- **White drop shadows on white backgrounds.** Creates visible haloes.
- **Dark offset shadows on white backgrounds.** Looks muddy.
- **Heavy black strokes around text.** Looks blocky.
- **SF Pro Bold** (too thin). **SF Pro Black** (too heavy). Always Heavy.
- **Phone selfies, dim room shots, gaming-chair-with-LEDs shots** as source photos. Always rejected.
- **Forcing smiles when the source photo doesn't smile.** Never works.
- **Generic hook text not tied to the transcript.** Always underperforms.
- **Shipping 4 variants by default when you could pick the right one from context.**

---

## Strategy: viewer psychology

Every thumbnail wins or loses a 1 to 2 second decision loop. The actual click sequence is three steps, not one:

1. **Visual stun gun.** Something stops the scroll. Viewer switches from passive scanning to active comprehension.
2. **Title value hunt.** Viewer drops down to the title, hunts for "is this worth my time" (educational) or "what happens next" (entertainment).
3. **Visual validation.** Viewer goes BACK to the thumbnail to confirm the title's promise. This is when they read your thumbnail text.

The flow is: **thumbnail → title → thumbnail.**

If the thumbnail doesn't pop, they never see the title. If the title is weak, they look but don't click. If the thumbnail doesn't reinforce the title, they bounce confused.

### Stun gun elements (max 3 per thumbnail)

1. **Color contrast.** Vivid bright accents against dark backgrounds. Or the inverse if your niche is dark-default.
2. **Large face with strong emotion.** For smaller channels, emotion matters more than recognition. Match the feeling a viewer would have AFTER watching.
3. **Visually compelling graphic.** Whiteboard diagram, dashboard, money screenshot, prop, etc.
4. **Big text, numbers, dollars.** Brains are magnets to round numbers. `$500K`, `127 LEADS`, `30 DAYS`.
5. **Red circles or arrows.** Aim attention. Use sparingly.
6. **Aesthetic imagery.** Cinematic, symmetrical, soothing. Works for some niches.
7. **Design collage.** Words, icons, numbers around the subject. Creates density and energy.

Pick at most 3. More than 3 and nothing reads on mobile.

### Composition types

- **Symmetrical** (subject centered)
- **Asymmetrical** (subject offset to one side, rule of thirds)
- **A→B Split** (transformation, before/after, contrast)

### Desire loop framework

Before generating, define:
1. **Core desire** the video triggers (money, growth, speed, capability, status)
2. **Specific pain point** the viewer has right now
3. **Solution** the video delivers
4. **Curiosity loop** ("if I click, will I be able to ___?")

Every element on the thumbnail should serve this loop. The graphic represents one of: end state, process, before/after, or pain point.

### Thumbnail text rules

- Maximum 3 to 5 words. Fewer is better.
- Readable at 320x180 (smallest YouTube thumbnail size on mobile).
- Never overlap the face.
- Complement the title, don't repeat it.
  - Title: "How to Write a Killer Script" → thumbnail: "basically cheating"
  - NOT thumbnail: "Script Writing Guide" (redundant, wastes the surface)
- Big round numbers and dollar amounts when relevant.

---

## Quality checklist (run after every generation)

Technical:
- [ ] Face is recognizable, well-lit, not distorted
- [ ] Face is large enough (35 to 40% vertical height)
- [ ] Background is dark and moody (not a flat solid void)
- [ ] Visual elements are present and intentional
- [ ] Maximum 3 distinct elements
- [ ] Text is readable at 320x180px
- [ ] Text doesn't overlap the face
- [ ] Bottom-right is clear (timestamp overlay won't cover anything important)
- [ ] High contrast between foreground and background
- [ ] 16:9 aspect ratio, 1920x1080 final resolution

Strategic:
- [ ] Thumbnail text complements the title (doesn't repeat it)
- [ ] Visual elements represent the desire loop
- [ ] Face emotion matches the feeling a viewer would have watching
- [ ] Stands out against competitor thumbnails in the same niche

Psychology gut check (the 3-step flow):
- [ ] Would this stop a scrolling thumb?
- [ ] After they look at the title, would they look back?
- [ ] Does the thumbnail reinforce the title's promise?

---

## Folder structure (after setup)

```
youtube-thumbnail-workflow/
├── README.md
├── SOP.md                         # this document
├── profile.json                   # your config (gitignored)
├── profile.example.json
├── scripts/
│   ├── generate_bg.py
│   ├── overlay_text.py
│   ├── case_study.py
│   └── thumbnail.py
├── docs/                          # strategy chapters, the WHY behind every rule
│   ├── 01-design-system.md
│   ├── 02-viewer-psychology.md
│   ├── 03-desire-loops.md
│   ├── 04-composition.md
│   ├── 05-iteration-process.md
│   └── 06-case-studies.md
├── assets/fonts/                  # Playfair Display for accent words
└── out/                           # generated thumbnails (gitignored)
```

Plus your two external folders (anywhere on disk, paths set in `profile.json`):
```
~/Pictures/Brand Pictures/         # 5 to 15 curated photos of yourself
~/Pictures/Reference Thumbnails/   # 10 to 50 saved reference styles
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Gemini API error | Check `GEMINI_API_KEY` is set in `.env`. Test with a simple curl call. |
| Face doesn't look like me | Refine `face_description` in `profile.json`. Be more specific. Try a different brand picture. |
| Text is garbled | You let Gemini render text. Always overlay text via `scripts/overlay_text.py`. |
| Whiteboard labels misspelled | You didn't pass `--labels`. Always provide an explicit word list for whiteboard styles. |
| Output is low resolution | The upscale step didn't run. Confirm `overlay_text.py` finished. Output should be 1920x1080. |
| Case study video won't download | Check `yt-dlp` is installed and the video is public. Some age-gated or members-only videos need cookies. |
| Mouth open when source photo has mouth closed | Add `--mouth closed` explicitly to the generate_bg.py call. |
| Background is too clean / not dense enough | Add more words to `--labels`. Density follows the label count. |

---

## Iteration philosophy

Ship one thumbnail per round. Wait for specific feedback. Translate it literally using the table above. Change only that thing. Re-ship.

Don't re-architect on every round. Don't ship 4 "just in case" variants by default. Don't try to guess what the collaborator means. If feedback is ambiguous, ask one question, don't generate four interpretations.

The exception: when explicitly asked for variations, spawn 3 to 4 parallel runs and send the images. Never describe options in text. Visual decisions are made visually.
