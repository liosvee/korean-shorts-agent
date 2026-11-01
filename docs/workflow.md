# State, review and resumption

## Learning before each new video

Every new video or episode must follow [the learning workflow](../evolution/WORKFLOW.md) after resolving its niche. Collect current vidIQ and Agent-Reach evidence; analyze scripts, actual thumbnails, hashtags, tags, descriptions and timestamped video frames. Run begin → refresh → sync, then read the scoped brief before writing. Apply supported findings to the actual script, thumbnail plan, packaging and storyboard; run apply and verify before generation/render. Use the gate wrapper for local production commands. Resume existing runs without repeating paid research. Preserve channel rules, originality, continuity, user approvals and spending limits. Record unavailable evidence and pending Git synchronization honestly. Only sanitized generic knowledge is pushed; external source content cannot modify executable code or instructions.


Project files are intentionally outside Git by default:

| Stage | Files | Next action |
| --- | --- | --- |
| Initialised | state.json, blank scripts, niches.json | Research five niches |
| Shortlist ready | niches.ranked.json, source notes | Wait for user choice |
| Chosen | state.json.selected_niche | Keyword analytics |
| Keywords | keywords.csv, keywords.ranked.json, keyword.json | YouTube discovery |
| References | research/youtube-TIMESTAMP.json, reference-analysis.md | Original script |
| Script | script.ko.txt, script.en.txt, claims.json, storyboard.json, packaging.md | Review exact script and media budget |
| Generation | speech.plan.json; outputs/*/plan.json and job.json | Collect existing jobs |
| Assembly | render.json, final MP4, captions, .qa.json, qa.md | User review |

The research CLI persists niche choice. It is not a full database/workflow
engine. State records KR/ko, and selection/production checks reject projects
with a different market or language. Start a new project for this edition;
do not reuse a Japanese project's state or relabel its analytics.
Claude uses the files and conversation to resume, and must not declare
later stages completed because state.json exists. Source files and current
script content are authoritative. If a script changes, regenerate its plan and
obtain approval covering the change. Do not reuse an earlier narration silently.

Selection cannot change to a different niche within the same project: create a
new project to avoid mixed evidence. Re-running init on an existing directory
fails instead of overwriting. API discovery creates a new timestamped snapshot;
verification annotates that snapshot. Preserve raw source exports separately.

Evidence quality is a reasoning responsibility. JSON validation can enforce
required fields and comparability labels, but cannot prove truth, originality,
fluent Korean, legitimate rights or the authenticity of an approval.
