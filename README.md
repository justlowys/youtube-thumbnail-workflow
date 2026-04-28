# YouTube Thumbnail Workflow

> A production-grade thumbnail pipeline. One command turns a video topic, a face photo, and a style reference into a finished 1920x1080 thumbnail. Hardened over 100+ real iterations on a published channel.

## What this is

A set of Python scripts + a documented design system that turn the hardest parts of YouTube thumbnails into defaults instead of guesses.

**What it handles for you:**

- Strict face matching via Gemini 3 Pro Image Preview (Nano Banana Pro). Mouth closed unless source shows otherwise. Head large in frame. Pose taken from the source photo, never invented.
- Real labels on whiteboards or graphic content. You pass a word list, the script tells Gemini to use only those words. No gibberish placeholders.
- Single-banner headlines rendered by PIL with SF Pro Heavy at 78% frame width, upscaled to 1920x1080. Never Gemini-rendered text (it hallucinates apostrophes, duplicates letters, mangles spacing).
- Fazio-style case study format. Pulls a still from the actual interview video, crops letterbox, renders the red money banner + white time-frame subheader.
- Configurable creator profile. Your face description, headshot folder, and default accent colour live in one `profile.json`.

**Why it exists:** most thumbnail tools either over-promise AI magic (every output looks the same) or under-deliver (every judgment call left to you). This sits in the middle. Every default in here was validated against the rejection pile.

Credit: original architecture forked from [Tyler Germain's youtube-thumbnail skill](https://fridaylabs.com) at Friday Labs. This version hardens that foundation with validated design-system rules.

---

## Before you can use this — checklist

The pipeline will not run until all 5 of these are done. Do them in order.

- [ ] **1. Install dependencies** (Python 3.10+, Pillow, google-genai, numpy)
- [ ] **2. Get a Gemini API key** and put it in `.env`
- [ ] **3. Create your `Brand Pictures` folder** with 5 to 15 headshots
- [ ] **4. Create your `Reference Thumbnails` folder** with style references you'd happily clone
- [ ] **5. Copy `profile.example.json` to `profile.json`** and fill in your face description

Each step is detailed below.

---

## Setup

### 1. Install

```bash
git clone https://github.com/<your-fork>/youtube-thumbnail-workflow.git
cd youtube-thumbnail-workflow
pip install Pillow google-genai numpy
# optional: only for case study video frame extraction
brew install yt-dlp ffmpeg
```

> **macOS only by default.** The PIL overlay script uses `/System/Library/Fonts/SFNS.ttf`. On Linux, install SF Pro or substitute another Heavy-weight sans-serif and update the font path in `scripts/overlay_text.py`.

### 2. API keys

Create `.env` in the project root:

```
GEMINI_API_KEY=your-key-here
SUPADATA_API_KEY=your-key-here   # optional, for auto-transcript fetching
```

Get a Gemini key at https://aistudio.google.com/. Supadata is optional but recommended.

### 3. Create your `Brand Pictures` folder

This is your curated face library. The Gemini script picks one photo per generation and uses it as the face reference. Quality of these photos determines quality of every thumbnail.

```bash
mkdir -p ~/Pictures/Brand\ Pictures
```

Drop **5 to 15 photos of yourself** into the folder. Rules:

- Studio or well-lit photos only. No phone selfies, no dim room shots.
- Mix of expressions across the set: neutral, slight smile, serious, shocked, explaining, pointing, both hands raised.
- Name each file with a short expression label so you can pick by intent later:

```
01 neutral-slight-smile.jpg
02 calm-neutral.jpg
03 shock-wide-eyes.jpg
06 open-hands-explain.jpg
09 pointing-finger-right.jpg
12 both-hands-raised.jpg
14 smile-neutral.jpg
```

This folder is the source of truth. If a photo is in here, the pipeline assumes it's approved. Remove anything you don't want appearing on a thumbnail.

You can use any path. Update `brand_pictures_dir` in `profile.json` if you put it somewhere other than `~/Pictures/Brand Pictures`.

### 4. Create your `Reference Thumbnails` folder

```bash
mkdir -p ~/Pictures/Reference\ Thumbnails
```

Save **10 to 50 reference thumbnails** you'd happily clone the style of. Right-click → Save Image from YouTube. Sources to mine:

- Top creators in your niche (highest view-count videos)
- Creators in adjacent niches whose style you admire
- Specific formats you want to replicate (whiteboard explainer, money banner, split before/after, burning paper, etc.)

When picking a reference for a new thumbnail, scan visually. Filenames are meaningless. Open the folder and look at the actual images. Pick the one whose composition matches the message of the new video.

### 5. Configure your profile

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
  "channel_description": "optional: 1 sentence about what your channel covers"
}
```

The `face_description` is the most important field. Bad descriptions make Gemini hallucinate features. Good descriptions make the face look like you 90% of the time. Examples that work:

- "young asian man, round youthful face, dark bowl-cut hair, round black wire-frame glasses, clean-shaven, early twenties"
- "middle-aged white man with short brown beard, short brown hair, dark brown eyes, mid-thirties"
- "black woman in her late twenties, natural curly hair pulled back, brown eyes, no glasses, full lips, warm brown skin"

`profile.json` is gitignored. Yours stays local.

---

## Generate your first thumbnail

```bash
python3 scripts/thumbnail.py \
  --brand-pic "12 both-hands-raised" \
  --style dense-whiteboard \
  --headline '$500K BLUEPRINT' \
  --labels "SALES FUNNEL,CONTENT,DM,CALL,CLOSE,ATTRACT,CONVERT,DELIVER,SCALE,KPIs,REVENUE,PIPELINE,LTV,CAC,MRR" \
  --output out/blueprint.png
```

Done. You have a 1920x1080 thumbnail.

## Scripts

| Script | Purpose |
|---|---|
| `generate_bg.py` | Generate a Gemini background with face + style constraints applied |
| `overlay_text.py` | PIL headline overlay with the winning formula defaults |
| `case_study.py` | Fazio-style case study builder (video frame + money banner) |
| `thumbnail.py` | End-to-end orchestrator (bg gen + overlay in one call) |

Each script has `--help` with full flags.

## Styles

| Style | Use for |
|---|---|
| `dense-whiteboard` | Strategy / framework / system videos |
| `burning-paper` | "Mistakes" / "what not to do" / negative list videos |
| `cinematic-quote` | Personal / authority / lesson videos with a quoted headline |
| `split-cold-warm` | Comparison / before-after / this-vs-that videos |
| `clean-portrait` | PFPs, simple hook videos, clean brand shots |

## Case studies (Fazio format)

For client-win videos ("How X made $Y in Z time"):

```bash
python3 scripts/case_study.py \
  --video-id <video-id> \
  --amount '$17,259/MO' \
  --timeframe "IN 30 DAYS" \
  --frame-time 60 \
  --output out/case-study.png
```

Downloads the video, extracts a still showing both faces from the interview, crops letterbox, renders the red/white money banner. Uses real interview stills so both faces are 100% authentic (Gemini never generates client faces). See [docs/06-case-studies.md](./docs/06-case-studies.md) for why this format converts.

## Documentation

The full SOP and design system live in this repo:

- [SOP.md](./SOP.md) — the complete step-by-step workflow
- [docs/01-design-system.md](./docs/01-design-system.md) — the hard rules (fonts, banners, face, labels, upscale)
- [docs/02-viewer-psychology.md](./docs/02-viewer-psychology.md) — the 3-step click loop + the 7 visual stun gun elements
- [docs/03-desire-loops.md](./docs/03-desire-loops.md) — how to frame what the thumbnail promises
- [docs/04-composition.md](./docs/04-composition.md) — symmetrical, rule-of-thirds, A→B split
- [docs/05-iteration-process.md](./docs/05-iteration-process.md) — how to iterate fast + the feedback translation table
- [docs/06-case-studies.md](./docs/06-case-studies.md) — the Fazio format, why it converts, when to use it

## Hard rules (the short version)

- Single solid banner headline, not two split colours (case study is the exception)
- SF Pro Heavy weight (between Bold and Black)
- Real correctly-spelled words on any whiteboard or graphic content. Never let Gemini invent labels.
- Face large: 35-40% of vertical height, y=15-55%
- Mouth closed unless the source photo shows otherwise
- Pose matches the source brand picture, don't force a new pose
- PIL overlay for all text, never Gemini-rendered headlines
- Upscale to 1920x1080 with LANCZOS + UnsharpMask
- For case studies: use interview stills, never Gemini-generated faces

## Iteration translation table

When your collaborator says X, change Y:

| User says | Fix |
|---|---|
| face too small / too low | `--face-size 0.42` |
| mouth weird | verify `--mouth closed` (default) or check source photo |
| doesn't look like me | try a different brand pic or refine `face_description` in profile |
| wrong words on the graphic | pass a real `--labels` word list |
| headline too big / small | adjust `--text-width-ratio` by 0.05 |
| two highlights | use default `--banner-style single` |
| different colour | generate 3-4 colour variants in parallel |
| graphic too simple | iterate the `--labels` list or try a different style |
| doesn't pop | check the banner colour contrasts the background |
| give me variations | spawn 3-4 parallel runs, don't describe options in text |

## Use as a Claude Code skill

This repo doubles as a Claude Code skill. To install:

```bash
cp -r . ~/.claude/skills/youtube-thumbnail/
```

Then type `/youtube-thumbnail` in Claude Code. Claude reads `SKILL.md` and walks you through the pipeline using the same scripts.

## License

MIT.
