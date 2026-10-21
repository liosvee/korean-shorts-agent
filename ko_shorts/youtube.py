"""Public metadata only; duration does not prove Shorts classification."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from .core import now, required
from elmarketing.client import NoRedirect


class YouTube:
    def __init__(self, key=None):
        self.key = key or os.environ.get('YOUTUBE_API_KEY')
        if not self.key:
            raise ValueError('Set YOUTUBE_API_KEY locally; enable YouTube Data API v3.')
        self.opener = urllib.request.build_opener(NoRedirect())

    def get(self, endpoint, params):
        if endpoint not in ('search', 'videos'):
            raise ValueError('Unsupported endpoint.')
        # Header avoids placing the secret in a logged query URL.
        url = 'https://www.googleapis.com/youtube/v3/' + endpoint + '?' + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={'X-Goog-Api-Key': self.key})
        try:
            with self.opener.open(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'YouTube HTTP {exc.code}. Check API enablement, key restrictions and quota.') from None
        except (urllib.error.URLError, OSError):
            raise RuntimeError('YouTube request failed. No credentials or error body logged.') from None


def seconds(iso):
    match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', iso)
    if not match or not any(match.groups()):
        return None
    h, m, s = (float(x or 0) for x in match.groups())
    return 3600*h + 60*m + s


def discover(client, query, days=90, pages=2, clock=None):
    if not 1 <= days <= 3650 or not 1 <= pages <= 5:
        raise ValueError('Use days 1–3650 and pages 1–5.')
    required(query, 'Korean query')
    instant = clock or datetime.now(timezone.utc)
    after = (instant-timedelta(days=days)).isoformat().replace('+00:00','Z')
    ids, seen = [], set()
    requests = 0
    # Two discovery orders broaden the sample, without claiming exhaustive coverage.
    for order in ('viewCount', 'date'):
        token = None
        for _ in range(pages):
            params = dict(part='snippet', type='video', q=query, regionCode='KR',
                          relevanceLanguage='ko', videoDuration='short', order=order,
                          publishedAfter=after, maxResults=50)
            if token: params['pageToken'] = token
            response = client.get('search', params); requests += 1
            for item in response.get('items', []):
                vid = item['id'].get('videoId')
                if vid and vid not in seen:
                    seen.add(vid); ids.append(vid)
            token = response.get('nextPageToken')
            if not token: break
    rows = []
    for offset in range(0, len(ids), 50):
        response = client.get('videos', {'part':'snippet,contentDetails,statistics', 'id':','.join(ids[offset:offset+50])})
        requests += 1
        for video in response.get('items', []):
            duration = seconds(video['contentDetails']['duration'])
            if duration is None or not 0 < duration <= 180: continue
            snippet, stats = video['snippet'], video.get('statistics', {})
            published = datetime.fromisoformat(snippet['publishedAt'].replace('Z','+00:00'))
            age = max((instant-published).total_seconds()/86400, 1/24)
            views = int(stats['viewCount']) if 'viewCount' in stats else None
            rows.append({'id':video['id'], 'url':'https://www.youtube.com/watch?v='+video['id'],
                         'title_ko':snippet['title'], 'title_en':None, 'channel_id':snippet['channelId'],
                         'channel_title':snippet['channelTitle'], 'published_at':snippet['publishedAt'],
                         'duration_seconds':duration, 'views':views, 'age_days':round(age,3),
                         'average_views_per_day':round(views/age,2) if views is not None else None,
                         'likes':int(stats['likeCount']) if 'likeCount' in stats else None,
                         'comments':int(stats['commentCount']) if 'commentCount' in stats else None,
                         'shorts_confirmed':False, 'korean_confirmed':False, 'verification':None})
    return {'query':query, 'requested_region':'KR', 'relevance_language':'ko',
            'retrieved_at':instant.isoformat(), 'published_after':after,
            'api_requests':requests, 'search_orders':['viewCount','date'],
            'limitations':['Sample only; not every video in the niche.',
                          'KR and ko are search hints, not proof of audience location or spoken language.',
                          'Average views/day is lifetime average, not recent velocity or retention.',
                          'Candidates require playback/language/Shorts verification. No public revenue estimate.'],
            'candidates':sorted(rows, key=lambda x:x['views'] if x['views'] is not None else -1, reverse=True)}


def verify(data, video_id, evidence, title_en):
    required(evidence, 'Playback/Shorts/language verification evidence')
    required(title_en, 'English title translation')
    for row in data['candidates']:
        if row['id'] == video_id:
            row.update(shorts_confirmed=True, korean_confirmed=True, title_en=title_en,
                       verification={'checked_at':now(), 'evidence':evidence})
            return data
    raise ValueError('Video ID not found in this research file.')


def shortlist(data):
    verified = [x for x in data['candidates'] if x.get('shorts_confirmed') is True and x.get('korean_confirmed') is True]
    return {'note':'Highest-performing verified examples in this collected sample; not the most viral on all YouTube.',
            'retrieved_at':data['retrieved_at'],
            'by_total_views':sorted(verified,key=lambda r:r['views'] if r['views'] is not None else -1, reverse=True),
            'by_lifetime_views_per_day':sorted(verified,key=lambda r:r['average_views_per_day'] if r['average_views_per_day'] is not None else -1, reverse=True)}
