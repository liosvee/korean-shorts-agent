# Research the shortlist

1. Read the brief. Initialise `projects/first-short` unless the user supplied a
   different project. Run doctor. Use web research available in Claude Code;
   a ChatGPT connector is not automatically available in this local session.
2. Research 5 candidate niches using natural Korean queries. For each, record
   Korean name, English meaning, audience, concrete revenue routes, demand
   evidence, production effort, competition and important unknowns.
3. Prioritise official or primary sources for factual claims. Record URL,
   retrieval date, relevant period, metric units and exact supported claim.
   Advertiser prices and affiliate commission schedules support possible revenue
   routes, not expected conversions or net profit. No unsupported CPM/RPM table.
4. Fill niches.json using templates/niches.json. Assign the four 0–5 editorial
   assessments only after research. Explain every score. Equal weights are a
   review aid, not empirically validated; alter only if the user requests it.
5. Run `python -m ko_shorts niches PROJECT`. Present all five in a concise English
   table with Korean names and sources. Explain which appears most promising
   under the chosen revenue model and why. Say when evidence is insufficient.
6. Ask the user to choose one. Stop here. Do not call select yourself until the
   user chooses. Save the shortlist and decision context so the run can resume.
