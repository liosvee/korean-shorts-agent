# Research contracts and interpretation

## Niches

Fill templates/niches.json with real evidence. Each niche requires a unique ID,
Korean and English name, audience, monetisation route, unknowns, at least one
source and four assessments. Use several relevant sources where necessary;
passing schema validation does not verify a source's quality or truth.

The rubric uses 0–5 for demand, commercial opportunity, production feasibility
and differentiation. Each has a written rationale. The total is an editorial
comparison out of 20, with equal weights. It does not estimate earnings, profit
or probability of success. Uncertain dimensions should say so in the rationale;
do not silently convert unavailable data to evidence of low demand.

Income hypotheses should name the actual route, e.g. a verified affiliate
programme accepting the target market, rather than assigning an invented RPM.
High advertiser CPC does not establish Shorts RPM or creator profitability.
No estimate of net profit is justified without defensible costs, conversions
and revenue assumptions. Sources record accessed_on in YYYY-MM-DD format.

## Keywords

The CSV header is mandatory. Save UTF-8 (UTF-8 BOM accepted):

| Column | Meaning |
| --- | --- |
| keyword_ko | Natural Korean query |
| translation_en | Accurate English meaning |
| value | Numeric provider value, or blank when unavailable |
| metric | estimated_monthly_searches, relative_interest_index or unknown |
| platform | YouTube or the actual measured platform; never relabel Google |
| market | KR only when the provider actually supports South Korea |
| language | ko only when justified by the query/data scope |
| period | Exact measurement period such as 2026-09; don't mix periods |
| provider | Provider identity; preserve methodology distinctions |
| source_url | Source page/export report URL, without tokens or secrets |
| accessed_on | Retrieval date YYYY-MM-DD |

Provider exports require explicit mapping to this schema; the importer does not
guess column meanings. It groups by provider/platform/market/language/period/
metric and sorts descending within each group. Empty values remain null.
The list of groups uses zero-based indices for choose-keyword.

For relative-interest tools, use one shared comparison set and consistent
time window; separately normalised indices cannot be compared just because
the provider and period match. Encode the comparison-set identifier in period
or provider so unrelated sets stay separate. Provider-specific competition
scores belong in the written report, not in the search-volume column.

If the selected group lacks measured estimates, Claude must explicitly explain
that the "most searched" requirement remains unresolved. The software allows
a qualitative choice only as a labelled fallback, with user acceptance in the
conversation. Google search volume can be context, not YouTube evidence.

## YouTube candidates

The Data API short-duration filter returns videos under four minutes. This
project additionally filters to at most 180 seconds; that still does not prove
Shorts format. Language and region filters are relevance hints. Review actual
playback and record the evidence before adding a reference to the verified list.

Public counts are snapshots. Views/day is total public views divided by age,
with a one-hour age floor to avoid division by zero. It is not recent view
velocity. Missing likes/comments stay null, not zero. The candidate pool is a
bounded search sample, not the whole niche. Cross-date snapshots and metrics
should retain their collection times.

Shorts public view counting changed on 31 March 2025 to include starts/replays
without a minimum watch time. Public views are not engaged views, retention or
paid views. Avoid interpreting cross-period differences as content effects.
Creator revenue and private retention are not provided by this research client.

The current client does not fetch channel baselines. Any claims of unusual
performance relative to a channel must use separately sourced comparable data.
