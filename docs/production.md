# Production and recovery

## Narration

1. Run `python -m elmarketing account` and `python -m elmarketing voices --search "Korean"`
   locally. Search results are not proof of natural Korean delivery; choose a
   suitable voice after inspecting its actual capabilities and authorised sample.
2. Write Korean narration and its complete English translation in the project.
3. Run `python -m ko_shorts speech-plan PROJECT --voice ACTUAL_VOICE_ID`.
   This creates a Multilingual v2 plan without a price. It strips leading/
   trailing whitespace and normalises Hangul to Unicode NFC before counting
   the exact submitted text during review. It
   binds the English translation into the plan hash. No v3 audio tags are used.
4. Look up the current estimate for the exact voice, model and text. Record
   estimated_credits and estimate_source (include date). Character count is not
   assumed to equal credits. Include every visual/music request in the total.
5. Run review and show the full plan to the user. Submit only after authorisation:

```sh
python -m elmarketing review projects/first-short/speech.plan.json
python -m elmarketing submit projects/first-short/speech.plan.json --approve HASH_FROM_REVIEW --job-dir outputs/narration
```

The returned hash is a change detector, not consent or a provider-enforced cap.
Key/account quotas must be configured at the provider if a spending cap is needed.
Any change to the reviewed plan changes the hash. Never auto-retry a paid POST.
Additional takes beyond the approved scope need approval.

Speech output includes response.json, audio.mp3 and, when supplied by the
provider, alignment.json and captions.srt. Inspect missing alignment rather
than fabricating times. Rebuild captions from saved alignment without regenerating
audio. Korean captions prefer spaces and punctuation within character/time
limits. Long unspaced tokens may split, but decomposed Hangul syllables remain
together. A single syllable longer than the time limit cannot be shortened
without inventing timing. Review phrase boundaries and provider timing manually.

## Visuals and music

Examples include image, video and music plans inherited from the companion
workspace. Check current official model parameters and plan access before use.
Edit prompts, aspect ratio, IDs and costs; obtain approval for each generation.
Image/video access may depend on plan and model. Do not assume a credit balance
implies permission for every API or model.

```sh
python -m elmarketing review projects/first-short/scene-01.plan.json
python -m elmarketing submit projects/first-short/scene-01.plan.json --approve HASH_FROM_REVIEW --job-dir outputs/scene-01
python -m elmarketing collect outputs/scene-01 --timeout 300
```

Collection only polls/downloads an existing job. Record asset origins and licences
in the storyboard. Do not copy the reference creator's footage or soundtrack.
Local supplied images/clips work without paid image/video generation.

## Korean fonts and assembly

Obtain a Korean font from its official distribution, e.g. Noto CJK, and keep
it in ignored fonts/. Use the exact font family name plus the actual local font
path in render.json; the renderer loads that file via libass fontsdir. Korean
caption renders fail early without a font file. Supplying any font file does not
prove Korean glyph support: inspect output for missing characters. Fonts are
not bundled in this repository. Preserve the font licence when redistributing.

Copy templates/render.json into projects/first-short/render.json. Relative paths
resolve from that manifest's directory. Replace scenes and durations after probing
the narration. The zero-second template is intentionally invalid, not production
timing. Optional music and music_gain (0–1) can be added. Music uses a fixed gain,
not automatic ducking. Original clip audio is discarded.

```sh
python -m elmarketing probe outputs/narration/audio.mp3
python -m elmarketing render projects/first-short/render.json --output outputs/first-short-final.mp4
```

The default target length is measured narration duration. Set target_seconds only
when needed; it must not truncate narration. Visuals must cover the full target.
Short clips hold their final frame. Images are letterboxed, not automatically
cropped. Use portrait source assets for a full-frame portrait design.

Output is H.264/AAC MP4 with faststart and a technical .qa.json probe report.
Captions are burned into the image; the original SRT remains available. Watch
and listen before delivery. Confirm font glyphs, phrasing, pronunciation, safe
placement and asset permissions. The program does not certify Korean fluency.

## Unknown outcomes

Every paid submission creates an exclusive new job directory before the request.
If the request times out or processing fails, inspect job.json and saved responses.
An unknown result may have been charged. Do not create a replacement job to
work around the guard. Reconcile the request with provider history; if an
image/video ID is confirmed, preserve that ID and collect it. If response.json
already contains speech audio/alignment, recover those files locally without a
new API call. Report local processing failure separately from generation failure.
