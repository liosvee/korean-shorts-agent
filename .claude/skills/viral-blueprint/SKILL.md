---
name: viral-blueprint
description: >
  Find the most-viewed videos in the channel's niche with vidIQ, pick the top performers, and
  use their script, title, description, hashtags and tags as a BLUEPRINT for an original,
  improved next video — then hand the blueprint to the production lane. Use for "find viral
  videos in my niche and make a better version", "what's blowing up in my niche — copy the
  formula", "use the top video as a blueprint", "remake the best performer but better",
  "reverse-engineer the viral script/title/tags", or "next video based on what's working".
  Runs FIRST for every new video or episode, before any script is written. Skip only when
  revising or resuming an existing project (reuse its saved research) or when the user opts out.
  Never for re-uploading or closely paraphrasing someone else's video.
---

# viral-blueprint — learn from the niche's winners, ship something better

**This is the first stage of every new production.** Resumes and revisions reuse the project's
saved `viral/` files instead of re-running it; the user can opt out for a single video.

Eight steps: **search → select → check script → script blueprint → check title → title
blueprint → metadata blueprint → improved video**. vidIQ does the research through its MCP
server (`.mcp.json`); `scripts/blueprint.py` ranks, dissects and proves originality offline.
The production itself is the existing lane — this skill never renders on its own.

**Blueprint means structure, not words.** Keep what made the video work — hook shape, pacing,
beat order, devices, title pattern, metadata layout. Never reuse its sentences, title wording,
description text, thumbnail art or footage. `blueprint.py check` enforces this; an ERROR blocks
production. Improved means: a sharper hook, a payoff the original only teased, the channel's own
voice and verified quotes, tighter pacing, better-targeted keywords.

## Before you start

- Use the project's **selected niche**. Never replace the user's niche choice with your own; if
  none is selected yet, run `prompts/01-niches.md` first.
- This runs **inside** the learning workflow (`evolution/WORKFLOW.md`), not beside it.
  Run `learn.py begin` for the niche first; save every vidIQ response below into that run's
  evidence directory under the ignored `<project>/.evolution/` (or `<project>/viral/`), feed the
  picked videos into `refresh`, and bind the blueprint-driven script and packaging in `apply`.
  Resuming a project? Reuse its saved responses — do not repeat paid calls.
- Read `AGENTS.md`, `docs/workflow.md` and `MASTER_CONTEXT.md`: niche wording, own channel ID (to exclude), brand voice, format
  and hard rules. Missing fields? Ask once and offer to save them there.
- **Cost.** Every vidIQ call used here costs 5 credits (outliers, search, get_videos_by_ids,
  transcript, score_title); `video_watch` / `watch_shortform_content` cost more — check the tool
  description. A typical run is ~12 calls ≈ 60 credits plus one watch job per pick. Tell the user
  the estimate before collecting, and check `vidiq_balance` first. Never auto-retry a charged call.

## 1 · Search the niche for viral videos

This pack makes **Korean Shorts**. vidIQ's outlier search does not cover non-English Shorts, so
search YouTube directly in Korean and rank by views:

```
vidiq_youtube_search  query="<niche keywords in Korean>"  type=["video"]  order="viewCount"  regionCode="KR"
                      videoDuration="short"  publishedAfter=<3 months ago>  limit=25
```

Run 2–3 query variants (synonyms, the problem the viewer has, the promise). `videoDuration=short`
means under 4 minutes, so `select --format short` still drops anything over 180 s. A URL, tag or
duration does not prove a Short is in Korean: confirm with the transcript or watch analysis.
Korean **long-form** may use `vidiq_outliers language="ko" contentType="long"` as well.

Save each raw response as JSON (`viral/search-1.json`, `viral/search-2.json` …). Then refresh stats,
descriptions and tags for every candidate ID in one call (≤ 50 IDs) and save that too:

```
vidiq_get_videos_by_ids  videoIds=[...]   →  viral/refresh.json
```

## 2 · Select the ones with the most views

```bash
python3 <skill>/scripts/blueprint.py select viral/search-*.json viral/refresh.json \
  --format short --language ko --niche "<niche>" --exclude-channel <own channel ID or @handle> \
  --max-age-days 120 --top 3 -o viral/selection.json
```

Ranks by view count after dropping the wrong format (Shorts ≤ 180 s), your own channel, uploads
younger than 3 days (views not settled) and records without a view count. One pick per channel by
default (`--per-channel`) so the blueprint is a pattern, not one creator's style. Narrow
`--max-age-days` when comparing raw views — a 3-year-old video wins on age alone. The full cohort
is saved, not just the winners. Show the user the top picks and let them choose (default: #1).

## 3 · Check the script

```
vidiq_video_transcript  videoId=<pick>  language="ko"   →  viral/<id>.transcript.json
vidiq_video_watch (long) | vidiq_watch_shortform_content (Short)  →  save job ID, poll, save analysisText
```

The transcript is the spoken script, not the creator's written one; no captions → record the gap.
The watch analysis gives pacing, visuals and cuts. Then:

```bash
python3 <skill>/scripts/blueprint.py dissect viral/selection.json --video <pick> \
  --transcript viral/<id>.transcript.json -o viral/blueprint.json
```

`blueprint.md` shows runtime, words per minute, the hook window (first 3 s for a Short),
a 10-slice beat map with the devices in each slice (questions, open loops, lists, contrast turns,
CTAs), and the title and metadata anatomy.

## 4 · Use it as the blueprint for the next script

Write the next Short with `prompts/04-script.md` — `script.ko.txt`, `script.en.txt`,
`storyboard.json`, `claims.json` — using the blueprint as the structural brief:

- Same job per beat (hook in the first 3 s → promise → development → answer), your own angle,
  examples and verified facts. Pace within ±15 % of the source's characters per second.
- Improve on it: pay off the hook sooner, cut the beats the watch analysis flags as slow, answer
  what the original only teased. No withheld answer to force another watch.
- Record what was kept from the blueprint and what changed in `reference-analysis.md` — the
  originality notes `04-script.md` already asks for.
- Prove originality before approval:

```bash
python3 <skill>/scripts/blueprint.py check viral/blueprint.json --script <project>/script.ko.txt
```

## 5 · Check the title

`blueprint.md` → title anatomy: length, number, question, brackets, CAPS, "you", power words,
colon/dash split, and a slot pattern (`Why Strong Men {…}`). Pull 3–5 other picks' titles from
`selection.json` to see which patterns repeat across channels — a pattern shared by several
winners is stronger evidence than one title.

## 6 · Use it as the blueprint for the title

Draft 5+ titles that keep the winning **pattern** with new words and the channel's topic. Score
them (`vidiq_score_title type=long|short channelId=<own>`), optionally get more with
`vidiq_generate_titles`, keep the best under 70 chars, then:

```bash
python3 <skill>/scripts/blueprint.py check viral/blueprint.json --title "<chosen title>"
```

ERROR at ≥ 80 % similarity to the source title. The output lists which source patterns you kept.

## 7 · Description, hashtags and tags → improved versions

From `blueprint.md`: the above-the-fold line, links, timestamps, hashtags and tag set. Improve,
don't copy:

- Description: your own first lines with the main keyword, the channel's links. No sentences
  lifted from the source.
- Tags: keep the source's relevant descriptors, add keywords from `vidiq_keyword_research` for
  the niche and the channel's own terms; ≤ 500 characters.
- Hashtags: 3–5 relevant ones; the first three show above the title.

Write them into `packaging.md` (Korean title, English title, Korean description, tags)
as `04-script.md` asks. Then write `viral/upload.json` as `{"title": …, "description": …, "tags": […]}` (the same
text, for the checker) and run:

```bash
python3 <skill>/scripts/blueprint.py check viral/blueprint.json --script <project>/script.ko.txt \
  --upload viral/upload.json -o viral/check.json
```

## 8 · Make the improved video — hand off to the existing pipeline

With `check` at 0 errors, continue the project's normal flow: present the Korean script with
its English translation, storyboard and sources, then `prompts/05-production.md` for the exact
paid plans, cost estimate and approval before any generation. Pass `viral/blueprint.md` and the
watch analysis along as the pacing/visual reference for the storyboard. This skill never
generates or renders on its own, and a research decision is not approval to spend.

After rendering, compare the actual pacing to the blueprint (beat starts vs the 10-slice map).
Re-run `check` if the script or packaging changes after review.

## Hand-off record

Keep in `<project>/viral/`: the saved vidIQ responses, `selection.json`, `blueprint.json/.md`,
`check.json`, the chosen title's vidIQ score, and a short `NOTES.md` listing what was kept from
the blueprint and what was deliberately improved. These are media-side project files — never
commit them to this repo. Generic lessons go through the learning workflow's sanitized knowledge.

## Korean specifics

- `check` switches to characters for Korean text: a shared run of ≥ 15 characters in the script
  (≥ 25 in the description) is a copy, and overlap is measured on 8-character phrases.
- Words-per-minute is less reliable for Korean; `blueprint.json` reports characters per second
  instead — use it to keep narration pace within ±15 % of the source.
- Score titles with `vidiq_score_title type=short`; Korean titles are judged on the first
  ~20–30 characters that show on the Shorts feed, not the 70-character English rule.
- Hashtags in Korean and English both count toward the 3–5 guideline.

## Honest limits

- "Most views" is within the sampled cohort, not the whole niche. Views are not CTR, retention
  or proof of *why* a video worked.
- A transcript is not the original script; missing captions stay a recorded gap.
- The originality check is lexical. It catches copied sentences, not a too-close idea — keep the
  angle your own.

Explain to the user in English; pair every Korean title, line and tag with English.
