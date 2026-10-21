"""Convert provider character alignments to phrase captions; no guessed timing."""
import math
import re
import unicodedata


def korean_cues(chars, starts, ends, max_chars, max_seconds):
    """Prefer spaces; split long unspaced tokens without separating Hangul jamo."""
    units = []
    for i, char in enumerate(chars):
        if units:
            previous = units[-1][0]
            combined = unicodedata.normalize('NFC', previous + char)
            if unicodedata.combining(char) or len(combined) < len(previous) + 1:
                units[-1] = (combined, units[-1][1], ends[i])
                continue
        units.append((char, starts[i], ends[i]))
    result, start = [], 0
    limit = min(max_chars, 18)
    while start < len(units):
        if units[start][0].isspace():
            start += 1
            continue
        stop, size, sentence_end = start, 0, False
        while stop < len(units):
            char, _, end = units[stop]
            if stop > start and (size + len(char) > limit or end - units[start][1] > max_seconds):
                break
            size += len(char)
            stop += 1
            if char in '.!?。！？\n':
                if char == '.' and stop > 1 and stop < len(units) and units[stop-2][0].isdigit() and units[stop][0].isdigit():
                    continue
                sentence_end = True
                break
        if not sentence_end and stop < len(units) and not units[stop][0].isspace():
            spaces = [i for i in range(start+1, stop) if units[i][0].isspace()]
            if spaces:
                stop = spaces[-1]
        visible_end = stop
        while visible_end > start and units[visible_end-1][0].isspace():
            visible_end -= 1
        text = ''.join(u[0] for u in units[start:visible_end])
        if text:
            result.append((text, units[start][1], units[visible_end-1][2]))
        start = stop
    return result


def cues(alignment, max_chars=42, max_seconds=3.0):
    if not isinstance(max_chars, int) or max_chars < 1 or not math.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError('Caption limits must be positive.')
    chars = alignment['characters']
    starts = alignment['character_start_times_seconds']
    ends = alignment['character_end_times_seconds']
    if not chars or not len(chars) == len(starts) == len(ends):
        raise ValueError('Missing or mismatched alignment arrays.')
    if any(not isinstance(c, str) or len(c) != 1 for c in chars):
        raise ValueError('Alignment must contain individual characters.')
    if any(not math.isfinite(s) or not math.isfinite(e) or s < 0 or e < s for s, e in zip(starts, ends)):
        raise ValueError('Invalid alignment timestamps.')
    if any(b < a for a, b in zip(starts, starts[1:])):
        raise ValueError('Alignment timestamps are not ordered.')
    if any(b < a for a, b in zip(ends, ends[1:])):
        raise ValueError('Alignment end timestamps are not ordered.')
    if re.search(r'[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff]', ''.join(chars)):
        return korean_cues(chars, starts, ends, max_chars, max_seconds)
    words = [(m.group(), starts[m.start()], ends[m.end()-1]) for m in re.finditer(r'\S+', ''.join(chars))]
    result, group = [], []
    for word in words:
        if group and (len(' '.join(w[0] for w in group)) + len(word[0]) + 1 > max_chars or word[2] - group[0][1] > max_seconds):
            result.append((' '.join(w[0] for w in group), group[0][1], group[-1][2]))
            group = []
        group.append(word)
        if word[0].endswith(('.', '!', '?')):
            result.append((' '.join(w[0] for w in group), group[0][1], group[-1][2]))
            group = []
    if group:
        result.append((' '.join(w[0] for w in group), group[0][1], group[-1][2]))
    return result


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f'{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}'


def srt(alignment):
    return '\n\n'.join(f'{i}\n{timestamp(start)} --> {timestamp(end)}\n{text}'
                       for i, (text, start, end) in enumerate(cues(alignment), 1)) + '\n'

