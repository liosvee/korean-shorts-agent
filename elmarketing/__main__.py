import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from .client import Client, load_env
from .jobs import collect, review, submit
from .render import render, probe


def main():
    parser = argparse.ArgumentParser(description='ElevenLabs marketing workspace')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('voices'); p.add_argument('--search', default='')
    sub.add_parser('account')
    sub.add_parser('models')
    p = sub.add_parser('review'); p.add_argument('plan')
    p = sub.add_parser('submit'); p.add_argument('plan'); p.add_argument('--approve', required=True); p.add_argument('--job-dir', required=True)
    p = sub.add_parser('collect'); p.add_argument('job_dir'); p.add_argument('--timeout', type=float, default=900)
    p = sub.add_parser('render'); p.add_argument('manifest'); p.add_argument('--output', required=True)
    p = sub.add_parser('probe'); p.add_argument('file')
    args = parser.parse_args()
    load_env()
    if args.command == 'review':
        result = review(json.loads(Path(args.plan).read_text(encoding='utf-8')))
    elif args.command == 'render':
        result = render(args.manifest, args.output)
    elif args.command == 'probe':
        result = probe(args.file)
    else:
        client = Client()
        if args.command == 'submit':
            result = submit(client, json.loads(Path(args.plan).read_text(encoding='utf-8')), args.approve, args.job_dir)
        elif args.command == 'collect':
            result = collect(client, args.job_dir, args.timeout)
        else:
            path = {'account': '/v1/user/subscription', 'models': '/v1/models',
                    'voices': '/v2/voices?' + urlencode({'search': getattr(args, 'search', ''), 'page_size': 100})}[args.command]
            result, _ = client.request('GET', path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)

