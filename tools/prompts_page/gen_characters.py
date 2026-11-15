# Builds the copy-ready character prompts page (published as an artifact, beside the city prompts page) from each city's
# build doc, section "Characters (<code>-C)": each character's prompts (a front, then its back and sides), where each
# picture goes, the notes for Gemini and ChatGPT, the
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
    blocks = re.findall(r'```text\n(ASSET (%s-C\d\d), .*?)\n```' % c['code'], sec, re.S)
    if not blocks:
        sys.exit('gen_characters.py: no prompts in ' + head)
    m = re.search(r'go in `(review/[^`]+?)/(%s-C01_[^/`]+)/`(?: \(and `(%s-C\d\d_[^/`]+)/`\))?' % (c['code'], c['code']), sec)
    files = re.findall(r'`(\d_[a-z_]+\.png)`', sec[m.end():m.end() + 200]) if m else []
    if not m or len(files) != 4:
        sys.exit('gen_characters.py: where the pictures go has moved: update the generator')
    folders = {f.split('_')[0]: f for f in (m.group(2), m.group(3)) if f}
    cg = re.search(r'\n\n(In ChatGPT.*?):\n- ChatGPT: `(FORMAT: [^`]+)`', sec, re.S)
    if not cg:
        sys.exit("gen_characters.py: ChatGPT's FORMAT paragraph has moved: update the generator")
    chars = {}
    for raw, cid in blocks:
        text = joined(raw.split('\n'))
        v = re.search(r'\b(FRONT|BACK|LEFT SIDE|RIGHT SIDE) view\.', text)
        if not v:
            sys.exit('gen_characters.py: a prompt for %s names no view' % cid)
        view = v.group(1)
        f = next((f for f in files if f[2:-4] == view.lower().replace(' ', '_')), None)
        if not f or cid not in folders:
            sys.exit('gen_characters.py: no file or folder for %s %s' % (cid, view))
        ch = chars.setdefault(cid, dict(id=cid, title='', views=[]))
        if view == 'FRONT':
            what = re.match(r'ASSET [^,]+, ([^,]+(?:, [^,]+)*?), FRONT view\.', text).group(1)
            ch['title'] = what[0].upper() + what[1:]
            if ' FORMAT: ' not in text:
                sys.exit('gen_characters.py: %s FRONT has no FORMAT paragraph' % cid)
            tools = dict(gemini=text, chatgpt=text[:text.index(' FORMAT: ')] + ' ' + cg.group(2))
        else:
            tools = dict(gemini=text, chatgpt=text)
        ch['views'].append(dict(view=view.title(), file=f, path='%s/%s/%s' % (m.group(1), folders[cid], f), tools=tools))
    characters = list(chars.values())
    # why not the game's kids: the bullets after "can't be used:"
    why = re.search(r"can't be used:\n((?:- .*\n(?:  .*\n)*)+)", sec)
    reasons = [inline(joined(b.split('\n'))) for b in re.split(r'\n(?=- )', why.group(1).strip())] if why else []
    reasons = [r[2:] if r.startswith('- ') else r for r in reasons]
    # the notes for each tool: the paragraph after the prompts (Gemini's), and ChatGPT's before its FORMAT paragraph
    gem = re.search(r'```\n\n(One chat for each child.*?)\n\n', sec, re.S)
    # the meshy.ai steps: the numbered list, and what follows it
    steps = re.search(r'[Tt]hen in meshy\.ai:\n((?:\d\. .*\n(?:   .*\n)*)+)(Then .*?)(?:\n\n|$)', sec, re.S)
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
    return dict(key=c['key'], name=c['name'], country=c['country'], accent=c['accent'], who=c['who'], characters=characters,
                reasons=reasons, notes=dict(gemini=inline(joined(gem.group(1).split('\n'))) if gem else '',
                                            chatgpt=inline(joined(cg.group(1).split('\n'))) + '.'),
                meshy=meshy, after=inline(joined(steps.group(2).split('\n'))), table=table)


data = dict(cities=[city_data(c) for c in CITIES])
out = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdout'
tpl = open(os.path.join(HERE, 'characters.html')).read()
open(out, 'w').write(tpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
print('wrote', out, sum(len(ch['views']) for c in data['cities'] for ch in c['characters']), 'prompts')
