import base64
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from elmarketing.client import APIError, Client, download
from elmarketing.captions import srt, timestamp
from elmarketing.jobs import collect, digest, review, submit, validate, write_json
from elmarketing.render import render, probe


def plan():
    return {'kind': 'video', 'request': {'model_id': 'veo-3.1-fast-generate-001', 'prompt': 'Product shot',
            'duration_secs': 8, 'aspect_ratio': '9:16', 'resolution': '1080p', 'generate_audio': False},
            'estimated_credits': 100, 'estimate_source': 'TEST FIXTURE ONLY; not a real price'}


class FakeClient:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []
    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result, {}


class JobsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.job = Path(self.temp.name)/'job'

    def test_exact_payload_and_duplicate_protection(self):
        p = plan(); c = FakeClient({'id': 'real-id', 'status': 'pending'})
        submit(c, p, digest(p), self.job)
        self.assertEqual(c.calls[0][0], ('POST', '/v1/flows/video', p['request']))
        with self.assertRaises(FileExistsError):
            submit(c, p, digest(p), self.job)
        self.assertEqual(len(c.calls), 1)

    def test_changed_plan_requires_new_review(self):
        p = plan(); token = digest(p); p['request']['prompt'] = 'changed'
        with self.assertRaises(ValueError):
            submit(FakeClient(), p, token, self.job)
        self.assertFalse(self.job.exists())

    def test_unknown_cost_blocks_submit(self):
        p = plan(); p['estimated_credits'] = None
        self.assertIsNone(review(p)['estimated_credits'])
        with self.assertRaises(ValueError):
            submit(FakeClient(), p, digest(p), self.job)

    def test_no_automatic_paid_retry(self):
        p = plan(); c = FakeClient(APIError(None, 'network uncertainty'))
        with self.assertRaises(APIError):
            submit(c, p, digest(p), self.job)
        self.assertEqual(len(c.calls), 1)
        self.assertEqual(json.loads((self.job/'job.json').read_text())['status'], 'unknown')

    def test_completed_download_has_no_signed_url_in_state(self):
        self.job.mkdir()
        write_json(self.job/'job.json', {'kind':'video','id':'abc','status':'pending'})
        c=FakeClient({'status':'completed','content_url':'https://example.com/signed','content_mime_type':'video/mp4'})
        with patch('elmarketing.jobs.download') as dl:
            result = collect(c, self.job)
            dl.assert_called_once()
        self.assertEqual(result['output'], 'media.mp4')
        self.assertNotIn('content_url', (self.job/'job.json').read_text())
        self.assertEqual(c.calls[0][0], ('GET', '/v1/flows/video/abc'))

    def test_poll_timeout_retains_id(self):
        self.job.mkdir(); write_json(self.job/'job.json', {'kind':'video','id':'abc','status':'pending'})
        now=[0]
        def sleep(t): now[0]+=t
        c=FakeClient({'status':'generating'})
        with self.assertRaises(TimeoutError):
            collect(c, self.job, timeout=5, clock=lambda: now[0], sleep=sleep)
        self.assertEqual(json.loads((self.job/'job.json').read_text())['id'],'abc')

    def test_poll_failure_is_terminal(self):
        self.job.mkdir(); write_json(self.job/'job.json', {'kind':'video','id':'abc','status':'pending'})
        c=FakeClient({'status':'failed','failure_reason':'model_error'})
        with self.assertRaises(RuntimeError): collect(c,self.job)
        self.assertEqual(len(c.calls),1)

    def test_poll_rate_limit_backoff(self):
        self.job.mkdir(); write_json(self.job/'job.json', {'kind':'video','id':'abc','status':'pending'})
        c=FakeClient(APIError(429,'rate limited'),{'status':'completed','content_url':'https://example.com/media','content_mime_type':'video/mp4'})
        waits=[]
        with patch('elmarketing.jobs.download'):
            collect(c,self.job,sleep=waits.append)
        self.assertEqual(waits,[10])

    def test_speech_audio_and_captions(self):
        p=plan(); p.update(kind='speech',voice_id='testvoice',request={'model_id':'eleven_multilingual_v2','text':'Hi.'})
        alignment={'characters':list('Hi.'),'character_start_times_seconds':[0,.1,.2],'character_end_times_seconds':[.1,.2,.3]}
        c=FakeClient({'audio_base64':base64.b64encode(b'mock mp3').decode(),'alignment':alignment})
        result=submit(c,p,digest(p),self.job)
        self.assertEqual(result['status'],'completed')
        self.assertEqual((self.job/'audio.mp3').read_bytes(),b'mock mp3')
        self.assertIn('00:00:00,300',(self.job/'captions.srt').read_text())

    def test_reference_placeholder_blocked(self):
        p=plan();p['request']['start_frame']={'type':'generation','generation_id':'REPLACE_WITH_IMAGE_GENERATION_ID'}
        with self.assertRaises(ValueError): validate(p)

    def test_v2_audio_tags_blocked(self):
        p=plan();p.update(kind='speech',voice_id='real',request={'model_id':'eleven_multilingual_v2','text':'[excited] Hello'})
        with self.assertRaises(ValueError):validate(p)

    def test_lipsync_schema_has_no_prompt(self):
        p=plan();p['request']={'model_id':'creatify-aurora','image':{'type':'asset','asset_id':'image-id'},'audio':{'type':'asset','asset_id':'audio-id'}}
        validate(p)
        p['request']['prompt']='unsupported'
        with self.assertRaises(ValueError): validate(p)


class CaptionTest(unittest.TestCase):
    def test_timestamp_rounds_with_carry(self):
        self.assertEqual(timestamp(59.9999),'00:01:00,000')
    def test_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            srt({'characters':['a'],'character_start_times_seconds':[],'character_end_times_seconds':[1]})
    def test_phrase_timing_uses_alignment(self):
        text='Hello world. A new line.'
        a={'characters':list(text),'character_start_times_seconds':[i*.2 for i in range(len(text))],
           'character_end_times_seconds':[(i+1)*.2 for i in range(len(text))]}
        value=srt(a)
        self.assertIn('Hello world.',value)
        self.assertIn('00:00:00,000 --> 00:00:02,400',value)


class SecurityTest(unittest.TestCase):
    def test_download_rejects_insecure_url(self):
        with self.assertRaises(ValueError):download('http://example.com/file','unused')
    def test_api_client_refuses_arbitrary_url(self):
        with self.assertRaises(ValueError):Client('test').request('GET','https://elsewhere.example')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
class RenderTest(unittest.TestCase):
    def test_real_render_and_duration_guard(self):
        with tempfile.TemporaryDirectory(prefix='test media ') as tmp:
            root=Path(tmp)
            def ff(*args):
                subprocess.run(['ffmpeg','-v','error','-y',*args],check=True,capture_output=True)
            ff('-f','lavfi','-i','color=c=blue:s=320x240:r=30','-t','0.5','-c:v','libx264',str(root/'clip.mp4'))
            ff('-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1','-c:a','pcm_s16le',str(root/'voice.wav'))
            ff('-f','lavfi','-i','sine=frequency=220:sample_rate=48000','-t','0.5','-c:a','pcm_s16le',str(root/'music.wav'))
            (root/'caption.srt').write_text('1\n00:00:00,000 --> 00:00:00,900\nOffline render test\n')
            m={'aspect_ratio':'9:16','narration':'voice.wav','music':'music.wav','captions':'caption.srt',
               'scenes':[{'file':'clip.mp4','seconds':1}]}
            write_json(root/'render.json',m)
            result=render(root/'render.json',root/'final.mp4')
            self.assertEqual((result['width'],result['height']),(1080,1920))
            streams=probe(root/'final.mp4')['streams']
            self.assertEqual({s['codec_type'] for s in streams},{'audio','video'})
            with self.assertRaises(FileExistsError):render(root/'render.json',root/'final.mp4')
            m['scenes'][0]['seconds']=.1;write_json(root/'render.json',m)
            with self.assertRaises(ValueError):render(root/'render.json',root/'short.mp4')
            m['scenes'][0]['seconds']=1
            (root/'caption.srt').write_text('1\n00:00:00,000 --> 00:00:00,900\n한국어 자막\n', encoding='utf-8')
            write_json(root/'render.json',m)
            with self.assertRaisesRegex(ValueError,'Korean captions require'):
                render(root/'render.json',root/'missing-font.mp4')
            (root/'caption.srt').write_text('1\n00:00:00,000 --> 00:00:00,900\nOffline render test\n')
            m['scenes'][0]['seconds']=1.2;m['target_seconds']=1.2;write_json(root/'render.json',m)
            result=render(root/'render.json',root/'exact.mp4')
            self.assertEqual(result['duration_seconds'],1.2)


if __name__=='__main__':unittest.main()

