# Delivery validation — 21 October 2026

## Completed

- Python 3.12.14: 39 offline tests passed for this Korean edition.
- Real FFmpeg/FFprobe renders produced H.264/AAC output at 1080x1920.
- The caption positioning code is inherited from the Japanese edition, where
  a synthetic Latin-script frame was inspected. No Korean frame was visually
  reviewed in this build environment.
- Korean spaced and unspaced text split into bounded cues using supplied
  character timing. Tests covered preferred word boundaries, decomposed Hangul
  syllables and decimal punctuation.
- Korean caption rendering rejected a missing explicit font file.
- Keyword tests preserved missing values, separated incompatible sources and
  rejected invalid values and the wrong target market.
- User niche selection and project reinitialisation guards were exercised.
- KR/ko search parameters, snapshot scope, Korean project state, foreign-market
  rejection and Korean narration normalisation were checked.
- YouTube mocks verified pagination bounds, deduplication, duration filtering,
  absent statistics, and verified-only shortlists.
- ElevenLabs mocks exercised exact request payloads, changed-plan rejection,
  duplicate-job prevention, polling and unknown outcomes without paid retries.

## Not exercised live

- Claude Code execution: the Claude executable was not installed in this build environment.
- YouTube API authentication or live discovery: no local API key was configured.
- Keyword-provider integration: this release imports sourced CSV data; it has no
  built-in vidIQ/Google Ads traffic API adapter.
- Paid ElevenLabs generation, current voice availability, credits or billing.
- Actual Korean font glyph rendering: no Korean font was installed here.
  Configure a Korean font and inspect a real export before production.
- Korean narration pronunciation, translation quality or fluent editorial review.
- Live niche research, revenue outcomes, Shorts performance or publishing.

Synthetic media in the tests is only a technical check, not a produced Korean
Short. No API credits were consumed by these tests. GitHub Actions is configured,
but has not run remotely because this project has not yet been uploaded.
