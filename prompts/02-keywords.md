# Keywords after user selection

1. Record the user's exact niche using `python -m ko_shorts select PROJECT ID`.
2. Build 15–30 natural Korean seed queries and English translations. Include
   relevant Hangul spacing variants and locally used terms where appropriate. Do not mechanically
   translate English keyword lists and assume Korean demand.
3. If a real keyword analytics tool is connected in Claude Code, inspect its
   current schema and market coverage, then use it. Otherwise request a provider
   export. This repository has a CSV importer, not a vidIQ or Google Ads adapter.
   Do not invent a vidIQ endpoint or imply a ChatGPT connection transfers here.
4. Normalise the supplied data to templates/keywords.csv. Keep source URLs,
   provider, dates, market and measurement period. If a provider does not support
   South Korea, do not relabel worldwide data KR. Search volumes are estimates unless
   the provider establishes otherwise. Record missing values as empty.
5. Run `python -m ko_shorts keywords PROJECT CSV`. Show grouped rankings with
   English meanings. A relative-interest index is not monthly search volume.
6. Prefer the highest-volume relevant Korean YouTube/KR keyword in one
   comparable group, after checking suitability for a Short. Explain if a lower
   volume keyword is chosen for relevance. Select it with choose-keyword and
   its zero-based group index. Do not claim "most searched on YouTube" beyond
   the measured provider/sample. If estimates are missing, explicitly label the
   choice qualitative. Obtain user acceptance of qualitative research if that
   substitutes for the requested traffic analysis.
7. Continue to prompts/03-shorts.md without another selection gate.
