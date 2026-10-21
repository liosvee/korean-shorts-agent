"""Local interactive setup; never prints keys or overwrites existing files."""
import getpass
import os
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = root/'.env'
if not env.exists():
    values = {}
    for name in ('YOUTUBE_API_KEY', 'ELEVENLABS_API_KEY'):
        value = getpass.getpass(f'{name} (hidden; Enter to skip): ').strip()
        if '\n' in value or '\r' in value:
            raise ValueError('Keys must be single-line values.')
        values[name] = value
    with env.open('x', encoding='utf-8') as handle:
        handle.write(''.join(f'{k}={v}\n' for k,v in values.items()))
    try: os.chmod(env, 0o600)
    except OSError: pass
    print('Created local .env.')
else:
    print('Existing .env preserved.')
context=root/'MASTER_CONTEXT.md'
if not context.exists():
    shutil.copyfile(root/'MASTER_CONTEXT.template.md',context)
print('Open MASTER_CONTEXT.md, then run: python -m ko_shorts doctor')
