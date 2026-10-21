"""Small standard-library REST client. Paid POSTs are never retried."""
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class APIError(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def load_env(path=Path('.env')):
    """Read simple KEY=value lines; never execute shell code or overwrite env."""
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in '\"\'':
                    value = value[1:-1]
                os.environ.setdefault(key.strip(), value)


class Client:
    def __init__(self, api_key=None):
        self.key = api_key or os.environ.get('ELEVENLABS_API_KEY')
        if not self.key:
            raise ValueError('Set ELEVENLABS_API_KEY in .env or your environment.')
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, method, path, body=None, binary=False):
        if not path.startswith('/v1/') and not path.startswith('/v2/'):
            raise ValueError('Only ElevenLabs API paths are accepted.')
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            'https://api.elevenlabs.io' + path, data=data, method=method,
            headers={'xi-api-key': self.key, 'Content-Type': 'application/json'},
        )
        try:
            with self.opener.open(request, timeout=300) as response:
                raw = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            # Error bodies may echo scripts or secrets. Do not log them.
            hints = {401: 'Check the API key.', 402: 'Check plan and credits.',
                     403: 'Check key permissions and model access.',
                     422: 'Check this model\'s documented request schema.',
                     429: 'Rate limited. Resume GET polling later.'}
            raise APIError(exc.code, f'ElevenLabs HTTP {exc.code}. ' + hints.get(exc.code, 'Check account history before resubmitting.')) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise APIError(None, 'Network result unknown. Do not repeat paid POSTs; check account history.') from None
        return (raw if binary else json.loads(raw)), headers


def download(url, destination):
    """Download signed media separately, without sending the API key."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('Expected a signed HTTPS media URL.')
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.part')
    try:
        # Reject redirects so a response cannot silently change transport/host.
        with urllib.request.build_opener(NoRedirect()).open(url, timeout=300) as response, temporary.open('wb') as out:
            shutil.copyfileobj(response, out)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)

