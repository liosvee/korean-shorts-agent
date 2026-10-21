import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from elmarketing.client import load_env
from elmarketing.jobs import write_json
from .core import initialise, read, rank_niches, select, selected, keyword_report, record_keyword, prepare_speech
from .youtube import YouTube, discover, verify, shortlist


def main():
    parser = argparse.ArgumentParser(description='Korean Shorts research and production workspace')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('doctor')
    p=sub.add_parser('init'); p.add_argument('project')
    p=sub.add_parser('status'); p.add_argument('project')
    p=sub.add_parser('niches'); p.add_argument('project')
    p=sub.add_parser('select'); p.add_argument('project'); p.add_argument('niche_id')
    p=sub.add_parser('keywords'); p.add_argument('project'); p.add_argument('csv')
    p=sub.add_parser('choose-keyword'); p.add_argument('project'); p.add_argument('keyword'); p.add_argument('--group', type=int, required=True)
    p=sub.add_parser('discover'); p.add_argument('project'); p.add_argument('--query'); p.add_argument('--days',type=int,default=90); p.add_argument('--pages',type=int,default=2)
    p=sub.add_parser('verify'); p.add_argument('file'); p.add_argument('video_id'); p.add_argument('--evidence',required=True); p.add_argument('--title-en',required=True)
    p=sub.add_parser('shortlist'); p.add_argument('file')
    p=sub.add_parser('speech-plan'); p.add_argument('project'); p.add_argument('--voice',required=True); p.add_argument('--credits',type=float); p.add_argument('--estimate-source')
    args=parser.parse_args()
    load_env()
    if args.cmd=='doctor':
        result={'python':sys.version.split()[0], 'ffmpeg':bool(shutil.which('ffmpeg')), 'ffprobe':bool(shutil.which('ffprobe')),
                'claude':bool(shutil.which('claude')), 'youtube_key_set':bool(os.getenv('YOUTUBE_API_KEY')),
                'elevenlabs_key_set':bool(os.getenv('ELEVENLABS_API_KEY')),
                'note':'Local presence only, not account/credit/API verification. Install a Korean font for captions.'}
    elif args.cmd=='init': result=initialise(args.project)
    elif args.cmd=='status': result=read(Path(args.project)/'state.json')
    elif args.cmd=='niches':
        result=rank_niches(read(Path(args.project)/'niches.json'))
        write_json(Path(args.project)/'niches.ranked.json',result)
    elif args.cmd=='select': result=select(args.project,args.niche_id)
    elif args.cmd=='keywords':
        selected(args.project)
        result=keyword_report(args.csv)
        write_json(Path(args.project)/'keywords.ranked.json',result)
    elif args.cmd=='choose-keyword':
        if args.group<0: raise ValueError('Group index must be nonnegative.')
        result=record_keyword(args.project,Path(args.project)/'keywords.ranked.json',args.group,args.keyword)
    elif args.cmd=='discover':
        selected(args.project)
        query=args.query or read(Path(args.project)/'keyword.json')['keyword_ko']
        result=discover(YouTube(),query,args.days,args.pages)
        from .core import now
        stamp=now().replace(':','').replace('.','')
        target=Path(args.project)/'research'/f'youtube-{stamp}.json'
        write_json(target,result)
        result={'file':str(target), 'candidates':len(result['candidates']), 'api_requests':result['api_requests'], 'limitations':result['limitations']}
    elif args.cmd=='verify':
        result=verify(read(args.file),args.video_id,args.evidence,args.title_en)
        write_json(args.file,result)
    elif args.cmd=='shortlist': result=shortlist(read(args.file))
    else: result=prepare_speech(args.project,args.voice,args.credits,args.estimate_source)
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__':
    try: main()
    except (ValueError, KeyError, IndexError, OSError, RuntimeError) as exc:
        print(f'Error: {exc}',file=sys.stderr)
        sys.exit(1)
