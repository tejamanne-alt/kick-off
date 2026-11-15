# Builds the copy-ready character prompts page (published as an artifact, beside the city prompts page) from each city's
# build doc, section "Characters (<code>-C)": its model-sheet prompts, where each sheet goes, the Gemini notes, the
# meshy.ai steps and why the game's own kids are not used. So the page never disagrees with the docs.
#   python3 tools/prompts_page/gen_characters.py <out.html>
import html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))

CITIES = [dict(key='kamakura', name='Kamakura', country='Japan', accent='#d6453a', code='KM',
               doc='docs/KAMAKURA_BUILD.md', who='KM1-1’s first-graders, walking to school in a line')]


def inline(md):
    """Markdown's **bold**, *italic* and `code` in a line of the doc, as HTML."""
    t = html.escape(md, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*([^*]+?)\*(?![\w*])', r'<i>\1</i>', t)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', t)


def joined(lines):
    return ' '.join(l.strip() for l in lines)


def city_data(c):
    doc = open(os.path.join(REPO, c['doc'])).read()
    head = '## Characters (%s-C)' % c['code']
    if head not in doc:
        sys.exit('gen_characters.py: no "%s" in %s' % (head, c['doc']))
    sec = doc[doc.index(head):]
    sec = sec[:re.search(r'\n## ', sec[3:]).start() + 3]
    prompts = []
    for text in re.findall(r'```text\n(ASSET %s-C\d\d.*?)\n```' % c['code'], sec, re.S):
        m = re.match(r'ASSET (%s-C\d\d), ([^.]+)\.' % c['code'], text)
        if not m:
            sys.exit('gen_characters.py: a prompt without its "ASSET <id>, <what>." opening')
        what = re.sub(r', a model sheet$', '', m.group(2))
        prompts.append(dict(id=m.group(1), title=what[0].upper() + what[1:], text=joined(text.split('\n'))))   # one paragraph
    if not prompts:
        sys.exit('gen_characters.py: no prompts in ' + head)
    # where each sheet goes: the doc's path for the first, its folder name in brackets for the next
    m = re.search(r'goes in `(review/[^`]+?)/(%s-C01_[^/`]+)/1_sheet\.png`(?: \(and `(%s-C\d\d_[^`]+)`\))?'
                  % (c['code'], c['code']), sec)
    if not m:
        sys.exit('gen_characters.py: where the sheets go has moved: update the generator')
    folders = {f.split('_')[0]: f for f in (m.group(2), m.group(3)) if f}
    for p in prompts:
        if p['id'] not in folders:
            sys.exit('gen_characters.py: no folder for ' + p['id'])
        p['path'] = '%s/%s/1_sheet.png' % (m.group(1), folders[p['id']])
    # why not the game's kids: the bullets after "can't be used:"
    why = re.search(r"can't be used:\n((?:- .*\n(?:  .*\n)*)+)", sec)
    reasons = [inline(joined(b.split('\n'))) for b in re.split(r'\n(?=- )', why.group(1).strip())] if why else []
    reasons = [r[2:] if r.startswith('- ') else r for r in reasons]
    # the Gemini notes: the paragraph after the prompts
    gem = re.search(r'```\n\n(One Gemini chat.*?)\n\n', sec, re.S)
    # the meshy.ai steps: the numbered list, and what follows it
    steps = re.search(r'then in meshy\.ai:\n((?:\d\. .*\n(?:   .*\n)*)+)(Then .*?)(?:\n\n|$)', sec, re.S)
    if not steps:
        sys.exit("gen_characters.py: the meshy.ai steps have moved: update the generator")
    meshy = [inline(joined(i.split('\n'))) for i in re.split(r'\n(?=\d\. )', steps.group(1).strip())]
    meshy = [re.sub(r'^\d\. ', '', s) for s in meshy]
    # the remesh numbers, for the comparison table
    nums = re.search(r'A passer-by \(([^)]*)\): ([\d,]+)\s+quads, about ([\d,]+) triangles\. A playable kid: ([\d,]+) quads, '
                     r'about ([\d,]+) triangles\..*?cuts them to ([\d,]+) and ([\d,]+)', joined(steps.group(1).split('\n')))
    if not nums:
        sys.exit('gen_characters.py: the remesh numbers have moved: update the generator')
    table = dict(passer=dict(who=nums.group(1), quads=nums.group(2), tris=nums.group(3), game=nums.group(6)),
                 kid=dict(quads=nums.group(4), tris=nums.group(5), game=nums.group(7)))
    return dict(key=c['key'], name=c['name'], country=c['country'], accent=c['accent'], who=c['who'], prompts=prompts,
                reasons=reasons, gemini=inline(joined(gem.group(1).split('\n'))) if gem else '',
                meshy=meshy, after=inline(joined(steps.group(2).split('\n'))), table=table)


data = dict(cities=[city_data(c) for c in CITIES])
out = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdout'
tpl = open(os.path.join(HERE, 'characters.html')).read()
open(out, 'w').write(tpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
print('wrote', out, sum(len(c['prompts']) for c in data['cities']), 'prompts')
