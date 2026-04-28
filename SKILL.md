---
name: youtube-thumbnail
description: Use when the user wants to create, revise, or iterate a YouTube thumbnail. Walks through reference picking, transcript fetching, Gemini background generation with strict face matching, and headline overlay. Bakes in design defaults so most decisions don't need to be made per thumbnail.
---

# YouTube Thumbnail Skill

Generates 1920x1080 YouTube thumbnails. The pipeline uses Gemini for the background (with strict face matching from the user's photo) and a separate text overlay step for the headline (so it never gets garbled). The user's profile lives in `profile.json`.

---

## STEP 0 — RUN THE SETUP CHECK FIRST

Before generating anything, verify the user has completed setup. The skill lives at `~/.claude/skills/<this-skill-folder>/`. Run these checks. If any line is printed by the script below, that's a blocking issue — stop, tell the user which step they're missing, point them at the relevant section of `README.md`, and don't proceed until they've fixed it.

```bash
# Resolve skill root (works regardless of Claude's current working directory).
# Replace <skill-folder> below with the actual folder name where this skill is installed
# (default: youtube-thumbnail).
SKILL_ROOT=~/.claude/skills/youtube-thumbnail
[ -d "$SKILL_ROOT" ] || SKILL_ROOT="$(pwd)"
cd "$SKILL_ROOT"

# 1. Gemini API key (required)
if ! grep -q "GEMINI_API_KEY=" .env 2>/dev/null && [ -z "$GEMINI_API_KEY" ]; then
  echo "MISSING: GEMINI_API_KEY. Get one at https://aistudio.google.com/, then add it to .env in $SKILL_ROOT"
fi

# 2. profile.json (required)
if [ ! -f profile.json ]; then
  echo "MISSING: profile.json. Run: cd $SKILL_ROOT && cp profile.example.json profile.json — then edit it"
fi

# 3. Brand Pictures folder (required)
if [ -f profile.json ]; then
  BRAND_DIR=$(python3 -c "import json,os; p=json.load(open('profile.json'));print(os.path.expanduser(p['brand_pictures_dir']))" 2>/dev/null)
  if [ -z "$BRAND_DIR" ] || [ ! -d "$BRAND_DIR" ]; then
    echo "MISSING: Brand Pictures folder ($BRAND_DIR). Create it and add 5-15 headshots."
  elif [ -z "$(find "$BRAND_DIR" -maxdepth 1 -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' 2>/dev/null | head -1)" ]; then
    echo "MISSING: photos in $BRAND_DIR. Add 5-15 headshots labeled by expression (e.g. '01 neutral-slight-smile.jpg')."
  fi
fi

# 4. Python deps (required)
python3 -c "import PIL, google.genai, numpy" 2>/dev/null || \
  echo "MISSING: Python deps. Run: pip install Pillow google-genai numpy"
```

If all checks pass silently, proceed. Do NOT try to "work around" missing setup — the pipeline will fail without it.

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

### Step 5 — Overlay the headline

```bash
python3 scripts/overlay_text.py \
  --bg workspace/thumb-bg.png \
  --headline 'YOUR HEADLINE' \
  --output workspace/thumb-final.png
```

Defaults: SF Pro Heavy weight, single solid coloured banner (the user's `default_accent_color`), white text inside, 78% frame width, positioned around the lower third. Final output upscaled to 1920x1080.

NEVER let Gemini render the headline. It hallucinates apostrophes, duplicates letters, mangles spacing. Always use the overlay script.

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

## Case study format

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

- **Single solid colour banner behind the headline.** Not two split colours. (Case study is the exception.)
- **SF Pro Heavy weight on the headline.** Bold is too thin. Black is too heavy.
- **Real, correctly-spelled words on whiteboards.** Pass via `--labels`. Never let Gemini invent.
- **Face large in frame.** Roughly 35-40% of vertical height.
- **Mouth closed by default.** Open only if the source photo shows it open.
- **Pose matches the source brand picture.** Don't ask Gemini to invent a new pose.
- **Final output is always 1920x1080.** The overlay script handles the upscale.
- **All headline text added by the overlay script.** Never let Gemini render headlines.
- **Case studies use real interview stills only.** Never Gemini-generated client faces.
- **Headline complements the video title, never repeats it.** Title = WHAT. Thumbnail = FEELING.
- **Maximum 3 distinct visual elements.** More than that becomes unreadable on mobile.
- **Bottom-right stays clear.** YouTube's video timestamp overlay covers it.

---

## Dead ends — DO NOT REPEAT

These were tried and rejected. Save the user the time:

- Face-swap models (insightface inswapper_128 etc.) — the face always looks 70% them, never 100%
- Landmark-based face paste from arbitrary source photo — hard edges, lighting mismatch
- Compositing the face on top of a new background from scratch — looks thin, generic
- Gemini-rendered headline text — always hallucinates apostrophes and spacing
- White drop shadows on bright backgrounds — creates visible haloes
- Dark offset shadows on bright backgrounds — looks muddy
- Heavy black strokes around text — looks blocky
- SF Pro Bold (too thin) or SF Pro Black (too heavy) — Heavy is the only correct weight
- Phone selfies, dim room shots, photos with weird LED lighting as source photos
- Forcing a smile when the source photo doesn't smile — never works
- Generic hook text not tied to the actual video transcript
- Shipping 4 variants by default when the right concept is obvious from context

---

## Visual decisions are made visually

When the user asks for variations, alternatives, or "what else", DO NOT describe options in text. Generate 2-4 actual image variants in parallel, send them visually, then optionally annotate. The image IS the description.

This applies to every visual decision: colour, composition, reference style, headline placement. Render and show, don't list and ask.
