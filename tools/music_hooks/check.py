"""Checks Florida's and Kamakura's written hooks (Audio/MusicGenerator.FloridaStyleOf, KamakuraStyleOf) against their chords, as the music is made, since
nobody can listen in a check: every note on a strong beat (beats 1 and 3 of a bar, or any note a beat long or more) must be a
tone of the chord under it (a major chord's 6th or 9th, and a minor one's 9th, count too), each bar is sixteen steps, each
hook four bars, each loop sixteen chords, and every note is between G3 and D6. Exits 1 on any problem (docs/LEARNINGS.md G4).

    python3 tools/music_hooks/check.py [path/to/MusicGenerator.cs]
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'Assets/_Game/Scripts/Audio/MusicGenerator.cs')
PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
QUALITY = {'': [0, 4, 7], 'm': [0, 3, 7], '7': [0, 4, 7, 10], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], '7sus4': [0, 5, 7, 10],
           'sus4': [0, 5, 7], '6': [0, 4, 7, 9], '9': [0, 4, 7, 10, 14], 'm9': [0, 3, 7, 10, 14], 'maj9': [0, 4, 7, 11, 14],
           '13': [0, 4, 10, 14, 21], 'm7b5': [0, 3, 6, 10]}


def pitch_class(name):
    return (PC[name[0]] + (1 if name[1:2] == '#' else -1 if name[1:2] == 'b' else 0)) % 12


def midi(token):
    m = re.match(r'([A-G][#b]?)(\d)$', token)
    if not m: raise ValueError('not a note: ' + token)
    return 12 * (int(m.group(2)) + 1) + pitch_class(m.group(1))


def chord(name):
    m = re.match(r'([A-G][#b]?)(.*)$', name.split('/')[0])
    return pitch_class(m.group(1)), QUALITY[m.group(2)], m.group(2)


def styles(src):
    # Florida's styles and, since v145, Kamakura's (both written hooks over their chords)
    for fn in ('FloridaStyleOf', 'KamakuraStyleOf'):
        start = src.index('static Style ' + fn)
        body = src[start:src.index('\n        static ', start + 10)]
        for item in styles_in(body, fn):
            yield item


def styles_in(body, fn):
    for block in re.split(r'case Soundscape\.|default:', body)[1:]:
        ch = re.search(r'chords = new\[\] \{(.*?)\}', block, re.S)
        if not ch: continue
        name = fn[:-7] + ' ' + (block.split(':')[0].strip() if block.split('\n')[0].strip().endswith(':') else 'Menu')
        hooks = [re.findall(r'"([^"]+)"', re.search(k + r' = new\[\]\s*\{(.*?)\}', block, re.S).group(1)) for k in ('hookA', 'hookB')]
        yield name, re.findall(r'"([^"]+)"', ch.group(1)), hooks


def check(src):
    problems = []
    count = 0
    for name, chords, (hook_a, hook_b) in styles(src):
        count += 1
        if len(chords) != 16: problems.append('%s: %d chords, not 16' % (name, len(chords)))
        for half, hook in ((0, hook_a), (8, hook_b)):
            if len(hook) != 4: problems.append('%s: a hook of %d bars, not 4' % (name, len(hook)))
            for rep in range(2):
                notes, cur = [], None
                for b, bar in enumerate(hook):
                    steps = bar.split()
                    if len(steps) != 16: problems.append('%s: "%s" has %d steps, not 16' % (name, bar, len(steps)))
                    for i, t in enumerate(steps):
                        beat = (half + rep * 4 + b) * 4 + i / 4
                        if t == '_':
                            if cur: cur[1] += 0.25
                        elif t == '.': cur = None
                        else:
                            cur = [beat, 0.25, midi(t)]
                            notes.append(cur)
                for beat, length, m in notes:
                    bar = int(beat // 4)
                    in_bar = beat - bar * 4
                    names = chords[bar % len(chords)].split()
                    c = names[min(len(names) - 1, int(in_bar // (4 / len(names))))]
                    root, tones, q = chord(c)
                    ok = set(t % 12 for t in tones)
                    if q in ('', 'maj7', '6', 'maj9'): ok |= {2, 9}
                    if q.startswith('m') and q != 'maj7': ok |= {2}
                    strong = (abs(in_bar - round(in_bar)) < 1e-6 and round(in_bar) % 2 == 0) or length >= 1
                    if strong and (m - root) % 12 not in ok:
                        problems.append('%s: bar %d beat %.2f, note %d over %s' % (name, bar + 1, in_bar + 1, m, c))
                    if not 55 <= m <= 86: problems.append('%s: note %d out of range' % (name, m))
    return count, problems


if __name__ == '__main__':
    n, problems = check(open(SRC).read())
    for p in problems: print(p)
    print('%d styles, %d problems' % (n, len(problems)))
    sys.exit(1 if problems or n != 14 else 0)
