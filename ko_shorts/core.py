import csv
import hashlib
import json
import math
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from elmarketing.jobs import write_json


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def required(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be non-empty text.')
    return value.strip()


def number(value, label, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{label} must be a finite nonnegative number.')
    if maximum is not None and value > maximum:
        raise ValueError(f'{label} must be at most {maximum}.')
    return value


def source(value):
    url = urlsplit(required(value.get('url'), 'Source URL'))
    if url.scheme != 'https' or not url.hostname:
        raise ValueError('Source URL must be HTTPS.')
    date.fromisoformat(value['accessed_on'])
    required(value.get('supports'), 'What the source supports')


CRITERIA = ('demand', 'commercial_opportunity', 'production_feasibility', 'differentiation')


def rank_niches(data):
    """Equal-weight editorial rubric, explicitly not a revenue prediction."""
    items = data.get('niches', [])
    if not items:
        raise ValueError('Research at least one niche before ranking.')
    result, seen = [], set()
    for row in items:
        for key in ('id', 'name_ko', 'name_en', 'audience_en', 'monetisation_en', 'unknowns_en'):
            required(row.get(key), key)
        if row['id'] in seen:
            raise ValueError('Niche IDs must be unique.')
        seen.add(row['id'])
        if not row.get('sources'):
            raise ValueError('Each niche needs traceable sources.')
        for ref in row['sources']:
            source(ref)
        scores = row['assessment']
        for key in CRITERIA:
            number(scores[key]['score'], key, 5)
            required(scores[key].get('rationale_en'), key + ' rationale')
        result.append(dict(row, editorial_score=sum(scores[k]['score'] for k in CRITERIA)))
    return {'method': 'Equal weights; four editorial 0–5 assessments. Not measured profit or a validated predictive model.',
            'ranked': sorted(result, key=lambda x: x['editorial_score'], reverse=True)}


def initialise(folder):
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=False)
    write_json(root/'state.json', {'version': 1, 'created_at': now(), 'target_market': 'KR',
                                 'content_language': 'ko', 'selected_niche': None})
    write_json(root/'niches.json', {'niches': []})
    (root/'script.ko.txt').write_text('', encoding='utf-8')
    (root/'script.en.txt').write_text('', encoding='utf-8')
    return {'project': str(root.resolve()), 'next': 'Claude researches niches into niches.json; see templates/niches.json.'}


def select(folder, niche_id):
    root = Path(folder)
    state = read(root/'state.json')
    check_locale(state)
    ranked = rank_niches(read(root/'niches.json'))
    chosen = next((x for x in ranked['ranked'] if x['id'] == niche_id), None)
    if chosen is None:
        raise ValueError('Choose an existing niche ID.')
    if state.get('selected_niche') and state['selected_niche']['id'] != niche_id:
        raise ValueError('This project already has a niche. Create a new project to avoid mixing research.')
    state.update(selected_niche=chosen, selected_at=now())
    write_json(root/'state.json', state)
    return state


def selected(folder):
    state = read(Path(folder)/'state.json')
    check_locale(state)
    if not state.get('selected_niche'):
        raise ValueError('Wait for the user to choose a niche, then run select.')
    return state


def check_locale(state):
    if state.get('target_market') != 'KR' or state.get('content_language') != 'ko':
        raise ValueError('This project is not configured for Korean/South Korea. Initialise a new Korean project.')


KEYWORD_COLUMNS = ('keyword_ko', 'translation_en', 'value', 'metric', 'platform', 'market',
                   'language', 'period', 'provider', 'source_url', 'accessed_on')


def keyword_report(path):
    """Never compare volumes across platforms, countries, periods or providers."""
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not set(KEYWORD_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError('Missing keyword columns; use templates/keywords.csv.')
        rows = list(reader)
    groups = {}
    for row in rows:
        for key in KEYWORD_COLUMNS:
            if key != 'value': required(row.get(key), key)
        if row['metric'] not in ('estimated_monthly_searches', 'relative_interest_index', 'unknown'):
            raise ValueError('Unknown metric type. Do not relabel provider scores as search volume.')
        raw = row['value'].strip()
        row['value'] = None if raw == '' else number(float(raw), 'Keyword value')
        if row['metric'] == 'unknown' and row['value'] is not None:
            raise ValueError('Unknown demand must not have a numeric value.')
        if row['metric'] == 'relative_interest_index' and row['value'] is not None:
            number(row['value'], 'Interest index', 100)
        source({'url': row['source_url'], 'accessed_on': row['accessed_on'], 'supports': row['metric']})
        key = tuple(row[k] for k in ('provider', 'platform', 'market', 'language', 'period', 'metric'))
        groups.setdefault(key, []).append(row)
    return {'note': 'Ranks only within comparable source groups. Missing data stays null. Search demand does not predict Shorts-feed distribution.',
            'groups': [{'dimensions': dict(zip(('provider','platform','market','language','period','metric'), key)),
                        'keywords': sorted(values, key=lambda r: (r['value'] is not None, r['value'] or 0), reverse=True)}
                       for key, values in groups.items()]}


def record_keyword(folder, report_path, group_index, keyword):
    selected(folder)
    report = read(report_path)
    group = report['groups'][group_index]
    row = next((r for r in group['keywords'] if r['keyword_ko'] == keyword), None)
    if row is None:
        raise ValueError('Keyword not in selected report group.')
    if row['platform'].casefold() != 'youtube' or row['market'] != 'KR' or row['language'] != 'ko':
        raise ValueError('Select a Korean YouTube/KR keyword; other groups are contextual evidence only.')
    write_json(Path(folder)/'keyword.json', row)
    return row


def prepare_speech(folder, voice, credits=None, estimate_source=None):
    selected(folder)
    root = Path(folder)
    text = unicodedata.normalize('NFC', (root/'script.ko.txt').read_text(encoding='utf-8').strip())
    translation = (root/'script.en.txt').read_text(encoding='utf-8').strip()
    if not text or not translation:
        raise ValueError('Write both Korean narration and English translation first.')
    if not re.search(r'[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff]', text):
        raise ValueError('Korean narration is missing.')
    plan = {'kind': 'speech', 'voice_id': voice,
            'request': {'model_id': 'eleven_multilingual_v2', 'text': text},
            'estimated_credits': credits, 'estimate_source': estimate_source,
            'english_translation': translation,
            'script_sha256': hashlib.sha256(text.encode()).hexdigest()}
    write_json(root/'speech.plan.json', plan)
    return plan
