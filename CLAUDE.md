# Korean Shorts Agent

Read AGENTS.md, MASTER_CONTEXT.md if present, and docs/workflow.md. You are the
research and creative agent; Python supplies data collection, validation and
media operations. This project does not run a separate LLM service.

When the user says "Start Korean Shorts research", follow prompts/01-niches.md.
When the user selects a niche, record that selection and continue with
prompts/02-keywords.md, then prompts/03-shorts.md and prompts/04-script.md.
When production is approved, follow prompts/05-production.md.
For "resume", inspect the project's files and state before deciding the next step.
Keep user explanations in English and Korean creative text paired with English.
Never replace the user's niche choice with your own.
