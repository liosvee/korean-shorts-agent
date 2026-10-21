"""Reviewable request files and crash-conscious generation tracking."""
import base64
import hashlib
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import quote
from .captions import srt
from .client import APIError, download

KINDS = {'image', 'video', 'speech', 'music', 'sfx'}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)


def digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def validate(plan):
    if plan.get('kind') not in KINDS or not isinstance(plan.get('request'), dict):
        raise ValueError('Plan needs kind (image/video/speech/music/sfx) and request object.')
    body = plan['request']
    if 'REPLACE_WITH_' in json.dumps(body):
        raise ValueError('Replace example reference IDs with IDs from your workspace.')
    if not body.get('model_id'):
        raise ValueError('Set an explicit documented model_id.')
    if plan['kind'] == 'speech':
        if not re.fullmatch(r'[A-Za-z0-9_-]+', plan.get('voice_id', '')) or plan['voice_id'].startswith('REPLACE'):
            raise ValueError('Select a real voice_id from the voices command.')
        if not body.get('text', '').strip():
            raise ValueError('Speech text is empty.')
        if body['model_id'] == 'eleven_multilingual_v2' and re.search(r'\[[^\]]+\]', body['text']):
            raise ValueError('Remove v3-style audio tags from Multilingual v2 text.')
    lipsync = plan['kind'] == 'video' and body['model_id'] == 'creatify-aurora'
    if lipsync and (not body.get('image') or not body.get('audio') or 'prompt' in body):
        raise ValueError('Aurora requires image and audio references and does not accept prompt.')
    if plan['kind'] in {'image', 'video', 'music'} and not lipsync and not body.get('prompt', '').strip():
        raise ValueError('A non-empty prompt is required.')
    if plan['kind'] == 'sfx' and not body.get('text', '').strip():
        raise ValueError('A sound description is required.')


def review(plan):
    validate(plan)
    estimate = plan.get('estimated_credits')
    source = plan.get('estimate_source')
    return {'approval_hash': digest(plan), 'kind': plan['kind'], 'request': plan['request'],
            'voice_id': plan.get('voice_id'),
            'narration_characters': len(plan['request'].get('text', '')) if plan['kind'] == 'speech' else None,
            'estimated_credits': estimate, 'estimate_source': source,
            'note': 'Estimate only, not a provider-enforced spending cap. Set a key quota in ElevenLabs. Missing cost = unknown.'}


def submit(client, plan, approval_hash, job_dir):
    validate(plan)
    if digest(plan) != approval_hash:
        raise ValueError('Approval hash does not match the exact plan. Review again.')
    cost = plan.get('estimated_credits')
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost <= 0 or not plan.get('estimate_source'):
        raise ValueError('Record a positive current credit estimate and its source before submitting.')
    directory = Path(job_dir)
    # Exclusive directory creation blocks double-clicks and concurrent submissions.
    directory.mkdir(parents=True, exist_ok=False)
    state = {'plan_hash': digest(plan), 'kind': plan['kind'], 'status': 'submitting',
             'estimated_credits': cost, 'created_at': time.time()}
    write_json(directory/'plan.json', plan)
    write_json(directory/'job.json', state)
    kind = plan['kind']
    path = {'image': '/v1/flows/image', 'video': '/v1/flows/video',
            'music': '/v1/music?output_format=mp3_44100_128',
            'sfx': '/v1/sound-generation?output_format=mp3_44100_128',
            'speech': '/v1/text-to-speech/' + quote(plan.get('voice_id', ''), safe='') + '/with-timestamps?output_format=mp3_44100_128'}[kind]
    try:
        data, headers = client.request('POST', path, plan['request'], binary=kind in {'music', 'sfx'})
        state['request_id'] = headers.get('request-id')
        state['reported_character_cost'] = headers.get('character-cost')
        if kind in {'image', 'video'}:
            state.update(id=data['id'], status=data['status'])
        else:
            if kind == 'speech':
                # Save the complete response before processing so caption failures need no regeneration.
                write_json(directory/'response.json', data)
                (directory/'audio.mp3').write_bytes(base64.b64decode(data['audio_base64'], validate=True))
                alignment = data.get('normalized_alignment') or data.get('alignment')
                if alignment:
                    write_json(directory/'alignment.json', alignment)
                    (directory/'captions.srt').write_text(srt(alignment), encoding='utf-8')
            else:
                (directory/'audio.mp3').write_bytes(data)
            state['status'] = 'completed'
    except Exception:
        state['status'] = 'unknown'
        write_json(directory/'job.json', state)
        raise
    write_json(directory/'job.json', state)
    return state


def collect(client, job_dir, timeout=900, clock=time.monotonic, sleep=time.sleep):
    directory = Path(job_dir)
    state = json.loads((directory/'job.json').read_text())
    if state['kind'] not in {'image', 'video'}:
        return state
    if not state.get('id'):
        raise ValueError('No confirmed generation ID. Check account history; never blindly resubmit.')
    interval = 2 if state['kind'] == 'image' else 10
    deadline = clock() + timeout
    while clock() < deadline:
        try:
            data, _ = client.request('GET', f"/v1/flows/{state['kind']}/{quote(state['id'], safe='')}")
        except APIError as exc:
            if exc.status != 429 and (exc.status is None or exc.status < 500):
                raise
        else:
            state['status'] = data['status']
            if data['status'] == 'failed':
                state['failure_reason'] = data.get('failure_reason')
                write_json(directory/'job.json', state)
                raise RuntimeError(f"Generation failed: {state['failure_reason']}. No automatic retry.")
            write_json(directory/'job.json', state)
            if data['status'] == 'completed':
                mime = data.get('content_mime_type', '')
                extension = {'video/mp4': '.mp4', 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp'}.get(mime)
                if not extension:
                    raise ValueError(f'Unexpected media type: {mime}')
                target = directory/('media'+extension)
                download(data['content_url'], target)
                state.update(output=target.name, content_mime_type=mime)
                write_json(directory/'job.json', state)
                return state
            if data['status'] not in {'pending', 'generating'}:
                raise ValueError('Unexpected provider status; saved for inspection.')
        sleep(min(interval, max(0, deadline-clock())))
        interval = min(interval*1.5, 60)
    raise TimeoutError('Polling timed out. Run collect again with the same job directory; no new charge is submitted.')

