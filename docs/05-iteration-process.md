# 05 — Iteration Process

This is how to iterate fast without re-deriving the design system on every round. It's the playbook you use when someone is giving feedback.

## The fast iteration loop

1. **Scan references VISUALLY.** Open every file in your references folder and LOOK at each one. Never pick a reference by filename. Describe references by what they show ("burning paper with a list", "split red/blue background") not their number.

2. **Scan brand pictures VISUALLY.** Open every file in `brand_pictures_dir`. Pick the one that matches the needed pose and expression (pointing, presenting, neutral, shocked).

3. **Pull the video transcript.** If you have `SUPADATA_API_KEY` set, the orchestrator does this automatically. Otherwise grab it manually. The thumbnail has to reference real claims from the video, not invented copy.

4. **Generate the background.** Use `generate_bg.py` with the appropriate style preset. Pass `--labels` if the style needs real words.

5. **Overlay the headline.** Use `overlay_text.py` with single blue banner defaults.

6. **Send it visually to your collaborator.** One-line caption. The image is the description.

## Iteration translation table

When your collaborator gives feedback, translate literally and fix ONLY that thing. Don't re-architect.

| User says | What they mean | Fix |
|---|---|---|
| "face too small" / "face too low" | subject is taking up too little of the frame | `--face-size 0.42` + regenerate |
| "mouth looks weird" | Gemini opened the mouth when source was closed | force `--mouth closed` and regenerate |
| "doesn't look like me" | Gemini's face approximation is off from the reference | try a different brand pic, refine `face_description` in profile, or add more reference headshots |
| "wrong words on the graphic" | Gemini invented gibberish labels | pass an explicit `--labels` list with real words only |
| "headline too big" / "too small" | proportion is off | adjust `--text-width-ratio` by ±0.05 |
| "don't like the two highlights" | they want a single solid banner | use default `--banner-style single` |
| "different colour" | the current banner clashes with the bg | generate 3-4 colour variants in parallel and let them pick |
| "graphic too simple" | not enough visual density | regenerate with a denser style or a longer label list |
| "doesn't pop" | banner contrast is weak | check banner vs bg contrast, darken bg area behind banner if needed |
| "not 4k quality" | output is blurry | verify LANCZOS upscale to 1920x1080 + UnsharpMask applied |
| "give me variations" | they want to see options visually | generate 3-4 real variants in parallel, never describe options in text |
| "what else" | same as above | more parallel variants |

## Hard rules for iteration

- **Change ONE thing per round.** If they say "face too small AND headline too big", change both but don't also slip in a different colour you prefer.
- **Never re-architect.** If the base concept is working and they only want a detail fixed, don't regenerate from scratch with a new style.
- **Parallel over sequential.** When they want "variations", spawn 3-4 runs in parallel. Don't generate one, ask, generate another.
- **Show, don't tell.** Skip the text descriptions of options. Render the images and send them.

## When to start over

Sometimes a thumbnail direction isn't salvageable and you need to go back to step 1. Signs:

- They reject 3+ iterations of the same base concept
- They say "I don't like this reference" (the style itself is wrong)
- They say "I want a completely different angle" (the desire loop is wrong)
- They say "this isn't it" for a reason you can't translate

When you hit any of these, go back to the desire loop (doc 03) and re-pick the style + reference. Don't try to incrementally fix a fundamentally wrong direction.

## When to stop iterating

Sometimes people iterate endlessly because the thumbnail is "fine" but they're not sure. At some point you have to call it done. Signs a thumbnail is ready to ship:

- The dominant element is immediately identifiable at 1/16th size
- The text is readable at mobile size
- The face looks like the person
- The headline complements (not repeats) the title
- The graphic element reinforces the desire loop
- The overall feel matches the video's tone

If all six are true, ship it. If you're still fiddling after 6-8 rounds, the problem is upstream — either the video angle, the title, or the desire loop — not the thumbnail.

## Documentation discipline

After each successful thumbnail, note:

- What style worked
- What brand pic worked
- What label list worked
- What the user rejected along the way and why

Feed this back into your profile or into a project-specific notes file. Over time your defaults get sharper and you need fewer iterations.
