# South Korean edition

| Setting | Value |
| --- | --- |
| Target market | South Korea, KR |
| Content/research language | Korean, ko |
| User explanations | English |
| Narration file | script.ko.txt |
| Translation file | script.en.txt |
| Keyword field | keyword_ko |
| Research title field | title_ko |
| Default font template | Noto Sans CJK KR |
| CLI package | ko_shorts |

The workflow still waits for the user's niche choice. It does not assume any
particular niche is profitable merely because it concerns South Korea.

Use natural South Korean wording and consistent speech style. The suggested
creative default is accessible polite Korean; adjust it to the audience and
channel brief. Review spacing, loanwords, names and number pronunciation.
Explain the meaning in English rather than relying on romanisation. Keep
Korean titles and thumbnail ideas distinct from literal English translations
when appropriate, without changing the underlying factual claims.

Keep Naver, Google and YouTube analytics labelled as separate platforms. None
of these names authorises substituting one platform's volume for another's.
The repository imports normalised CSV exports; it does not include a Naver,
Google Ads or vidIQ API adapter. If a provider lacks KR/ko coverage, report
that limitation instead of relabelling worldwide or Japanese data.

YouTube regionCode=KR is an availability filter, not evidence that viewers or
creators live in South Korea. relevanceLanguage=ko prioritises relevant results
but does not guarantee spoken Korean. Verify actual video content. Store
requested_region/relevance_language in each snapshot so filter scope is visible.

Narration uses an explicit model with documented Korean support, but model
support alone does not establish a particular voice's pronunciation quality.
Choose a real voice ID, inspect an authorised sample and review the final audio.
Fluent review remains necessary when the agent cannot reliably assess naturalness.

This edition is a separate project. Its schema is intentionally Korean-specific;
start a new project instead of importing an old Japanese workspace unchanged.
