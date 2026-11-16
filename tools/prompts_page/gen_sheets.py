# Builds a copy-ready prompts page (published as an artifact) from one of the city's prompt documents: Kamakura's plants
# (docs/KAMAKURA_PLANT_PROMPTS.md) or its animals, birds and fish (docs/KAMAKURA_ANIMAL_PROMPTS.md). The document is the
# source: its intro, "How to use them", "Check each picture before saving it", the base prompts and the groups of prompts,
# each with the folder its pictures are saved in. Whether a prompt's pictures are already in the repository is read from
# that folder, so the page shows what is still to make. ChatGPT's version of a prompt has ChatGPT's frame shapes in its
# FORMAT paragraph (1:1, 2:3 and 3:2: 16:9 and 21:9 become 3:2, 9:16 becomes 2:3).
#   python3 tools/prompts_page/gen_sheets.py docs/KAMAKURA_PLANT_PROMPTS.md <out.html> --accent '#3f8a4a'
import html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

args = sys.argv[1:]
doc_path, out = args[0], args[1]
accent = args[args.index('--accent') + 1] if '--accent' in args else '#2a55c4'
doc = open(os.path.join(REPO, doc_path) if not os.path.isabs(doc_path) else doc_path).read()

FIRST = re.compile(r'(BASE|VIEWS|LEAVES|BARK|FOLIAGE|ASSET) ([A-Z]{2}-[A-Z]\d+[a-z]?),? ([^.]+?)(?: \(([^)]*)\))?\.')
BADGES = {'BASE': 'Paste first', 'VIEWS': 'Views', 'LEAVES': 'Leaves', 'BARK': 'Bark', 'FOLIAGE': 'Foliage', 'ASSET': 'Views'}


def inline(md):
    """Markdown's **bold**, *italic* and `code`, as HTML."""
    t = html.escape(md, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*([^*]+?)\*(?![\w*])', r'<i>\1</i>', t)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', t)


def joined(text):
    return ' '.join(l.strip() for l in text.strip().split('\n'))


def chatgpt(text):
    """The prompt with ChatGPT's frame shapes in its FORMAT paragraphs."""
    def fix(m):
        p = m.group(0)
        for a, b in (('16:9', '3:2'), ('21:9', '3:2'), ('9:16', '2:3'), ('4:1', '3:1')):
            p = p.replace(a, b)
        return p
    return re.sub(r'FORMAT:.*?(?=\n\n|\Z)', fix, text, flags=re.S)


def sections(text, level):
    """[(heading, body)] for the headings of this level ('## ' or '### ')."""
    parts = re.split(r'\n(?=' + level + r' )', '\n' + text)
    out = []
    for p in parts:
        if p.startswith(level + ' '):
            head, _, body = p.partition('\n')
            out.append((head[len(level) + 1:].strip(), body))
    return out


def prose(body):
    """The paragraphs of a section before its first prompt."""
    before = body.split('```text', 1)[0].strip()
    return [inline(joined(p)) for p in re.split(r'\n\s*\n', before) if p.strip()]


def items_of(body):
    """Each prompt in a section, with the folder (and files) its pictures are saved as."""
    items = []
    for m in re.finditer(r'```text\n(.*?)\n```\n?(Save: `([^`]+)`(?: \(([^)]*)\))?)?', body, re.S):
        text, folder, files = m.group(1), m.group(3), m.group(4)
        f = FIRST.match(joined(text))
        if not f:
            sys.exit('gen_sheets.py: a prompt does not start with its kind and id: ' + text[:60])
        kind, pid, title, aside = f.group(1), f.group(2), f.group(3), f.group(4)
        base = re.search(r'Use BASE (KM-S\d+)', text)
        names = re.findall(r'`([^`]+)`', files or '')
        status = None
        if folder:
            d = os.path.join(REPO, folder)
            have = [n for n in names if os.path.exists(os.path.join(d, n))] if names else (os.listdir(d) if os.path.isdir(d) else [])
            status = dict(have=len(have), of=len(names) or len(have))
        items.append(dict(kind=kind.lower(), badge=BADGES[kind], id=pid, title=title[:1].upper() + title[1:],
                          aside=aside, base=base.group(1) if base else None, folder=folder, files=names, status=status,
                          tools=dict(gemini=text, chatgpt=chatgpt(text))))
    return items


title = re.match(r'# (.+)', doc).group(1)
top = sections(doc, '##')
intro = [inline(joined(p)) for p in re.split(r'\n\s*\n', doc.split('\n## ', 1)[0].split('\n', 1)[1]) if p.strip()]
data = dict(title=title, accent=accent, intro=intro, how=[], checks=[], bases=[], groups=[], source=doc_path)
for head, body in top:
    if head.startswith('How to use'):
        steps = re.split(r'\n(?=\d+\. )', body.strip().split('\n\n')[0])
        data['how'] = [inline(joined(re.sub(r'^\d+\. ', '', s))) for s in steps if s.strip()]
        data['how_note'] = [inline(joined(p)) for p in body.strip().split('\n\n')[1:] if p.strip()]
    elif head.startswith('Check each'):
        data['checks'] = [inline(joined(b[2:])) for b in re.split(r'\n(?=- )', body.strip()) if b.startswith('- ')]
    elif head.startswith('The base prompts'):
        for sub, sbody in sections(body, '###'):
            for it in items_of(sbody):
                data['bases'].append(dict(it, group=sub, note=prose(sbody)))
    else:
        items = items_of(body)
        if items:
            data['groups'].append(dict(name=head, note=prose(body), items=items))
if not data['how'] or not data['checks'] or not data['bases'] or not data['groups']:
    sys.exit('gen_sheets.py: %s is missing its how-to, checks, bases or groups: update the document or the generator' % doc_path)
# every prompt that names its base names one this page has
known = {b['id'] for b in data['bases']}
for g in data['groups']:
    for it in g['items']:
        if it['base'] and it['base'] not in known:
            sys.exit('gen_sheets.py: %s uses %s, which is not among the base prompts' % (it['id'], it['base']))
tpl = open(os.path.join(HERE, 'sheets.html')).read()
open(out, 'w').write(tpl.replace('/*TITLE*/', html.escape(title))
                     .replace('/*DATA*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
n = sum(len(g['items']) for g in data['groups'])
made = sum(1 for g in data['groups'] for it in g['items'] if it['status'] and it['status']['have'] >= it['status']['of'] > 0)
print('wrote', out, len(data['bases']), 'bases,', n, 'prompts in', len(data['groups']), 'groups,', made, 'already in')
