"""Assemble local media, narration, optional music and SRT with FFmpeg."""
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SIZES = {'9:16': (1080, 1920), '16:9': (1920, 1080), '1:1': (1080, 1080), '4:5': (1080, 1350)}


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]).stdout)


def duration(path):
    return float(probe(path)['format']['duration'])


def render(manifest_path, output):
    manifest_path = Path(manifest_path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    base = manifest_path.parent
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Output exists. Choose a new filename.')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise ValueError('Install ffmpeg and ffprobe first.')
    width, height = SIZES[manifest.get('aspect_ratio', '9:16')]
    narration = (base/manifest['narration']).resolve()
    narration_length = duration(narration)
    length = float(manifest.get('target_seconds', narration_length))
    if not math.isfinite(length) or length < narration_length:
        raise ValueError('target_seconds must be finite and at least the measured narration duration; narration is never truncated.')
    scenes = manifest['scenes']
    if not scenes or any(not math.isfinite(float(s['seconds'])) or float(s['seconds']) <= 0 for s in scenes):
        raise ValueError('Supply scenes with finite positive durations.')
    if sum(float(s['seconds']) for s in scenes) + .05 < length:
        raise ValueError('Visuals are shorter than the target duration. Extend scenes explicitly.')
    sources = [narration] + [(base/s['file']).resolve() for s in scenes]
    sources += [(base/manifest[k]).resolve() for k in ('music', 'captions') if manifest.get(k)]
    if any(not p.is_file() for p in sources):
        raise ValueError('A local media or caption file is missing.')
    font_name = manifest.get('caption_font', 'DejaVu Sans')
    if not re.fullmatch(r'[A-Za-z0-9 _-]+', font_name):
        raise ValueError('caption_font must be a simple font family name.')
    font_file = (base/manifest['caption_font_file']).resolve() if manifest.get('caption_font_file') else None
    if font_file and (not font_file.is_file() or font_file.suffix.lower() not in {'.ttf','.otf','.ttc'}):
        raise ValueError('caption_font_file must be an existing TTF, OTF or TTC file.')
    if manifest.get('captions'):
        caption_text = (base/manifest['captions']).read_text(encoding='utf-8-sig')
        if re.search(r'[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff]', caption_text) and not font_file:
            raise ValueError('Korean captions require caption_font_file and its matching caption_font family. See docs/production.md.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='el-render-', dir=output.parent) as folder:
        work = Path(folder)
        for i, scene in enumerate(scenes):
            source = (base/scene['file']).resolve()
            seconds = float(scene['seconds'])
            still = source.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}
            command = ['ffmpeg', '-v', 'error', '-y']
            command += ['-loop', '1'] if still else []
            command += ['-i', str(source), '-an', '-t', str(seconds), '-vf',
                        f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={seconds}',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', str(work/f'{i}.mp4')]
            run(command)
        (work/'concat.txt').write_text(''.join(f"file '{i}.mp4'\n" for i in range(len(scenes))))
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '1', '-i', 'concat.txt', '-c', 'copy', 'visuals.mp4'], cwd=work)
        command = ['ffmpeg', '-v', 'error', '-y', '-i', str(work/'visuals.mp4'), '-i', str(narration)]
        filters = ['[1:a]aresample=48000,apad[voice]']
        audio = '[voice]'
        if manifest.get('music'):
            gain = float(manifest.get('music_gain', .12))
            if not math.isfinite(gain) or not 0 <= gain <= 1:
                raise ValueError('music_gain must be between 0 and 1.')
            command += ['-stream_loop', '-1', '-i', str((base/manifest['music']).resolve())]
            filters += [f'[2:a]aresample=48000,volume={gain}[bed]', '[voice][bed]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[mixed]']
            audio = '[mixed]'
        video = '0:v:0'
        if manifest.get('captions'):
            # Fixed local basename avoids platform-specific subtitle filter escaping.
            shutil.copyfile(base/manifest['captions'], work/'captions.srt')
            # Give libass explicit video-sized coordinates. Default SRT styling
            # uses a small landscape canvas and can oversize Korean on portrait.
            run(['ffmpeg','-v','error','-y','-i','captions.srt','captions.ass'], cwd=work)
            ass = (work/'captions.ass').read_text(encoding='utf-8-sig')
            ass = re.sub(r'(?m)^PlayResX:.*$', f'PlayResX: {width}', ass)
            ass = re.sub(r'(?m)^PlayResY:.*$', f'PlayResY: {height}', ass)
            (work/'captions.ass').write_text(ass, encoding='utf-8')
            if font_file:
                (work/'fonts').mkdir()
                shutil.copyfile(font_file, work/'fonts'/('caption'+font_file.suffix.lower()))
            fonts_option = ':fontsdir=fonts' if font_file else ''
            font_size = round(width*.0444)
            side_margin, bottom_margin = round(width*.07), round(height*.16)
            filters += [f"[0:v]subtitles=captions.ass{fonts_option}:force_style='FontName={font_name},FontSize={font_size},Outline=3,MarginL={side_margin},MarginR={side_margin},MarginV={bottom_margin}'[captioned]"]
            video = '[captioned]'
        command += ['-filter_complex', ';'.join(filters), '-map', video, '-map', audio,
                    '-t', str(length), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(work/'final.mp4')]
        run(command, cwd=work)
        report = probe(work/'final.mp4')
        streams = report['streams']
        if not any(s['codec_type']=='audio' for s in streams) or not any(s['codec_type']=='video' for s in streams):
            raise RuntimeError('Rendered output must contain audio and video.')
        if abs(float(report['format']['duration'])-length) > .25:
            raise RuntimeError('Rendered duration differs from target by more than 0.25 seconds.')
        shutil.move(work/'final.mp4', output)
    output.with_suffix('.qa.json').write_text(json.dumps(report, indent=2)+'\n')
    return {'output': str(output), 'duration_seconds': length, 'width': width, 'height': height}

