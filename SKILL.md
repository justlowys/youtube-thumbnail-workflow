---
name: youtube-thumbnail
description: Use when the user wants to create, revise, or iterate a YouTube thumbnail. Walks through transcript fetching, reference picking, Gemini background generation with strict face matching, and PIL text overlay. Hardened defaults from 100+ real iterations.
---

# YouTube Thumbnail Skill

Production-grade YouTube thumbnail pipeline. Generates 1920x1080 thumbnails using Gemini 3 Pro Image Preview (Nano Banana Pro) for the background and PIL for the text overlay. Bakes in validated design rules so most decisions are defaults, not judgment calls.

---

## STEP 0 — RUN THE SETUP CHECK FIRST

Before generating anything, verify the user has completed setup. Run these checks in order. If any fail, stop and tell the user exactly which step to do, then refuse to continue until it's done.

```bash
SKILL_ROOT="$(dirname "$(realpath SKILL.md 2>/dev/null || echo .)")"
cd "$SKILL_ROOT" 2>/dev/null || true

# 1. Gemini API key
if ! grep -q "GEMINI_API_KEY=" .env 2>/dev/null && [ -z "$GEMINI_API_KEY" ]; then
  echo "MISSING: GEMINI_API_KEY. Get one at https://aistudio.google.com/, then add to .env"
fi

# 2. profile.json exists
if [ ! -f profile.json ]; then
  echo "MISSING: profile.json. Run: cp profile.example.json profile.json — then edit it"
fi

# 3. brand_pictures_dir exists and has at least one image
BRAND_DIR=$(python3 -c "import json,os; p=json.load(open('profile.json'));print(os.path.expanduser(p['brand_pictures_dir']))" 2>/dev/null)
if [ -z "$BRAND_DIR" ] || [ ! -d "$BRAND_DIR" ]; then
  echo "MISSING: Brand Pictures folder ($BRAND_DIR). Create it and add 5-15 headshots."
elif [ -z "$(find "$BRAND_DIR" -maxdepth 1 -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' 2>/dev/null | head -1)" ]; then
  echo "MISSING: photos in $BRAND_DIR. Add 5-15 headshots labeled by expression (e.g. '01 neutral.jpg')."
fi

# 4. Python deps
python3 -c "import PIL, google.genai, numpy" 2>/dev/null || \
  echo "MISSING: Python deps. Run: pip install Pillow google-genai numpy"
```

Any line printed = blocking issue. Tell the user to fix it, point them at the relevant section of `README.md`, and stop. Do NOT try to "work around" missing setup. The pipeline will fail without it.

If all checks pass silently, proceed.

---

## The pipeline (every thumbnail)

### Step 1 — Scan references and brand pictures VISUALLY

Never pick by filename. Always open the actual images first.

```bash
ls "$(python3 -c "import json,os;print(os.path.expanduser(json.load(open('profile.json'))['brand_pictures_dir']))")"
```

If the user has a Reference Thumbnails folder (recommended at `~/Pictures/Reference Thumbnails/`), list and Read every unseen file there too. Describe references by what they SHOW (whiteboard with boxes, burning paper, split-color background, big money number) — never by filename like "thumbnail (12).jpeg".

### Step 2 — Get the video transcript

The headline and any on-graphic labels MUST come from the actual video, not generic guesses. If the user gave a YouTube video ID and `SUPADATA_API_KEY` is set, fetch it:

```bash
KEY=$(grep SUPADATA_API_KEY .env | cut -d= -f2)
curl -s -H "x-api-key: $KEY" "https://api.supadata.ai/v1/youtube/transcript?videoId=VIDEO_ID&text=true"
```

If no key or no video ID, ask the user to paste the transcript or summarize the 2-3 main claims. Extract:
- 2-3 specific claims (numbers, terminology, frameworks)
- Sharpest line that captures the promise
- Specific labels for any whiteboard graphic

### Step 3 — Pick a style + brand picture

Match style to video MESSAGE, not vibe:

| Video type | Style | Why |
|---|---|---|
| Strategy / framework / system | `dense-whiteboard` | Hand-drawn diagrams convey complexity-made-simple |
| Mistakes / what-not-to-do | `burning-paper` | Implies destruction of bad ideas |
| Personal / authority / lesson | `cinematic-quote` | Moody portrait for quoted headline |
| Comparison / before-after | `split-cold-warm` | Vertical red/blue split signals contrast |
| PFP / simple hook | `clean-portrait` | No distractions |

Pick a brand picture whose pose and expression match the video's energy. Use the filename label as a hint but verify visually.

### Step 4 — Generate the background

```bash
python3 scripts/generate_bg.py \
  --brand-pic "12 both-hands-raised" \
  --style dense-whiteboard \
  --labels "WORD1,WORD2,WORD3,..." \
  --output workspace/thumb-bg.png
```

CRITICAL for `dense-whiteboard`: ALWAYS pass `--labels` with explicit words from the transcript. Without labels, Gemini invents misspelled gibberish.

The script automatically:
- Loads the user's face description from `profile.json`
- Picks the matching brand picture
- Forces face constraints (mouth closed unless source shows otherwise, face large 35-40% of vertical height, pose from source)
- Tells Gemini "no text" so the headline can be overlaid in PIL

### Step 5 — Overlay the headline in PIL

```bash
python3 scripts/overlay_text.py \
  --bg workspace/thumb-bg.png \
  --headline 'YOUR HEADLINE' \
  --output workspace/thumb-final.png
```

Defaults: SF Pro Heavy, single solid coloured banner (user's `default_accent_color`), white text inside, 78% frame width, y=0.78, LANCZOS upscale to 1920x1080 + UnsharpMask.

NEVER let Gemini render the headline. It hallucinates apostrophes, duplicates letters, mangles spacing. Always overlay in PIL.

### Step 6 — Or run end-to-end

```bash
python3 scripts/thumbnail.py \
  --video-id VIDEO_ID \
  --brand-pic "12 both-hands-raised" \
  --style dense-whiteboard \
  --headline 'YOUR HEADLINE' \
  --labels "WORD1,WORD2,WORD3,..." \
  --output out/thumb.png
```

One call: transcript fetch (if Supadata key set) + bg gen + overlay + upscale.

### Step 7 — Send the thumbnail. Wait for specific feedback.

Show the user the final image. Don't ship 4 variants by default — pick the right concept from context and ship one. If the user explicitly asks for variations, generate 3-4 in parallel and present visually.

---

## Case study format (Fazio-style)

For client-win videos ("How [name] made $X in Y time"):

```bash
python3 scripts/case_study.py \
  --video-id VIDEO_ID \
  --amount '$17,259/MO' \
  --timeframe "IN 30 DAYS" \
  --frame-time 60 \
  --output out/case-study.png
```

The script downloads the video, extracts a frame at `--frame-time` showing both faces, crops letterbox bars, renders red money banner + white time-frame subheader.

Hard rules:
- Two REAL faces, never silhouettes or question marks
- Red banner `(220, 30, 30)` + white text. Not blue.
- Money on top: `$XX,XXX/MO`
- Time-frame below: `IN X MONTHS` or `IN X DAYS`. Specific. Never "FAST".
- Never let Gemini generate the client's face. Always use real interview stills.

---

## Iteration translation table

When the user gives feedback, translate literally. Change ONLY the specific thing. Don't re-architect.

| User says | Fix |
|---|---|
| face too small / too low | regenerate with `--face-size 0.42` |
| mouth weird | confirm `--mouth closed` (default) or pick a source photo with mouth open |
| doesn't look like me | try a different brand pic, or refine `face_description` in `profile.json` |
| wrong words on the graphic | pass a real `--labels` word list with exact spellings |
| headline too big / too small | adjust `--text-width-ratio` by 0.05 |
| two highlights | use default `--banner-style single` |
| different colour | spawn 3-4 colour variants in parallel, present visually |
| graphic too simple | iterate the `--labels` list (more words = denser) |
| doesn't pop | check banner colour contrasts background. On bright bg, add dark gradient. |
| too dark | switch black text to navy or electric blue |
| text too low | move from bottom edge to y=0.72 |
| not 4K | confirm LANCZOS + UnsharpMask upscale ran. Output should be 1920x1080. |
| give me variations | spawn 3-4 parallel runs. Send images. Never describe options in text. |

---

## Hard rules (the design system)

- **Single solid banner headline.** Not two split colours. (Case study is the exception.)
- **SF Pro Heavy.** Bold is too thin. Black is too heavy.
- **Real correctly-spelled words on whiteboards.** Pass via `--labels`. Never let Gemini invent.
- **Face large.** 35-40% vertical height, y=15-55%.
- **Mouth closed by default.** Open only if source photo shows it open.
- **Pose matches the source brand picture.** Don't ask Gemini to invent a new pose.
- **Always upscale to 1920x1080.** LANCZOS + UnsharpMask.
- **PIL overlay for all text.** Never Gemini-rendered headlines.
- **Case studies use real interview stills only.** Never Gemini-generated client faces.
- **Headline complements the title, never repeats it.** Title = WHAT. Thumbnail = FEELING.
- **Maximum 3 distinct visual elements.** More than that = unreadable on mobile.
- **Bottom-right stays clear.** YouTube's timestamp overlay covers it.

---

## Dead ends — DO NOT REPEAT

These were tried and rejected over 100+ iterations:

- Insightface inswapper_128 face-swap — face always looks 70% them, never 100%
- Landmark-based face paste — hard edges, lighting mismatch
- PIL composite from scratch (cutout + new bg) — looks thin, generic
- Gemini-rendered text — always hallucinates
- White drop shadows on white backgrounds — creates haloes
- Dark offset shadows on white backgrounds — looks muddy
- Heavy black strokes around text — looks blocky
- SF Pro Bold (too thin) or SF Pro Black (too heavy) — Heavy only
- Phone selfies, dim shots, gaming-chair-LED shots as source photos
- Forcing smiles when the source photo doesn't smile
- Generic hook text not tied to the transcript
- Shipping 4 variants by default when the right concept is obvious from context

---

## Visual decisions are made visually

When the user asks for variations, alternatives, or "what else", DO NOT describe options in text. Generate 2-4 actual image variants in parallel, send them visually, then optionally annotate. The image IS the description.

This applies to every visual decision: colour, composition, reference style, headline placement. Render and show, don't list and ask.
