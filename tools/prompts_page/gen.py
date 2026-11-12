# Builds the copy-ready prompts page (published as an artifact) from docs/IMAGE_PROMPTS.md and docs/CITIES.md, with each
# city's colour temperatures from Progression/Cities.cs, so the page never disagrees with the docs.
#   python3 tools/prompts_page/gen.py <out.html>
import re, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
P = open(REPO + '/docs/IMAGE_PROMPTS.md').read()
C = open(REPO + '/docs/CITIES.md').read()
CS = open(REPO + '/Assets/_Game/Scripts/Progression/Cities.cs').read()

# --- the climate numbers from the game's own code
clim = {}
for name, args in re.findall(r'public static readonly City (\w+) = new City\([^;]*?new CityClimate\(([^)]*)\)', CS):
    nums = re.findall(r'([0-9.]+)f', args)
    clim[name] = (int(float(nums[0])), int(float(nums[1])))
clim['Kamakura'] = (5400, 9000)   # CityClimate.Reference (ReferenceSunKelvin, ReferenceShadeKelvin)
for c in ('Kamakura', 'Florida', 'Madrid', 'NewYork', 'Mumbai'):
    if c not in clim:
        sys.exit('gen.py: no climate for ' + c + ' in Cities.cs')

CITIES = [
    dict(key='Kamakura', hash='kamakura', h2='Kamakura, Japan', name='Kamakura', country='Japan', accent='#d6453a',
         when='A clear May morning, 7:45', air='Soft sea haze; route 3 in June drizzle', code='KM'),
    dict(key='Florida', hash='florida', h2='Florida (Miami), USA', name='Florida', country='Miami, USA', accent='#1fa6a0',
         when='A hot late-August morning, 7:50', air='Humid: a milky horizon, then a downpour', code='FL'),
    dict(key='Madrid', hash='madrid', h2='Madrid, Spain', name='Madrid', country='Spain', accent='#d27a22',
         when='Early October, 8:30, just after sunrise', air='Very dry high-plateau air, crisp to the horizon', code='MD'),
    dict(key='NewYork', hash='new-york', h2='New York, USA', name='New York', country='USA', accent='#c99a06',
         when='A cold late-October morning, 7:50', air='Crisp; sun shafts down the cross streets, steam', code='NY'),
    dict(key='Mumbai', hash='mumbai', h2='Mumbai, India', name='Mumbai', country='India', accent='#8a4cc0',
         when='The July monsoon, 11:15', air='Overcast and wet, sea mist; route 3 in a break', code='MB'),
]

def blocks_in(text):
    return re.findall(r'```text\n(.*?)\n```', text, re.S)

def section(text, start, end_pat=r'\n## '):
    i = text.index(start)
    m = re.search(end_pat, text[i + len(start):])
    return text[i: i + len(start) + (m.start() if m else len(text))]

base_section = blocks_in(section(P, '## The base prompt'))
base = base_section[0]
# The two tools' versions: the base prompt's FORMAT line (Gemini's is the second block in that section), and each kind of
# shot's FORMAT line (the doc's "Format lines").
fmt_line = re.search(r'- FORMAT:.*?use exactly that ratio\.', base, re.S)
if not fmt_line or not base_section[1].startswith('- FORMAT:'):
    sys.exit("gen.py: the base prompt's FORMAT line or Gemini's replacement has moved: update the generator")
bases = {'chatgpt': base, 'gemini': base.replace(fmt_line.group(0), base_section[1].strip())}
FORMAT_KEYS = {'ChatGPT, a street or set shot': ('chatgpt', 'level'), 'Gemini, a street or set shot': ('gemini', 'level'),
               'Look target': ('both', 'look'), 'Sheet': ('both', 'sheet'), 'Plate': ('both', 'plate')}
formats = {'chatgpt': {}, 'gemini': {}}
for label, line in re.findall(r'^- ([^:`]+): `(FORMAT: [^`]+)`', P, re.M):
    tool, kind = FORMAT_KEYS[label]
    for t in (['chatgpt', 'gemini'] if tool == 'both' else [tool]):
        formats[t][kind] = line
for t in formats:
    if sorted(formats[t]) != ['level', 'look', 'plate', 'sheet']:
        sys.exit('gen.py: missing format lines for ' + t + ': ' + str(sorted(formats[t])))
KINDS = {'LEVEL': 'level', 'LOOK TARGET': 'look', 'SHEET': 'sheet', 'PLATE': 'plate', 'MAP': 'map'}

# --- legs from CITIES.md: id -> (title, kind)
legs = {}
for lid, title, kind in re.findall(r'\*\*([A-Z]{2}\d-\d) ([^*]+)\*\* \(([^)]*)\)', C):
    k = 'Mini-game' if kind.startswith('mini-game') else 'Twist' if kind.startswith('twist') else 'Dribble'
    legs[lid] = (title, k)
routes = {}
for rid, rname, n, trip in re.findall(r'\| \*\*([A-Z]{2}\d) ([^*]+)\*\*[^|]* \| (\d) \| ([^|]+) \|', C):
    routes[rid] = dict(name=rname.strip(), legs=int(n), trip=trip.strip().replace('->', '→').replace('*(', '(').replace(')*', ')'))

out = []
for c in CITIES:
    sec = section(P, '## ' + c['h2'])
    city_block = blocks_in(section(sec, '### The ', r'\n### '))[0]
    groups = []
    for m in re.finditer(r'\n#### ([^\n]+)\n(.*?)(?=\n#### |\Z)', sec, re.S):
        head, body = m.group(1), m.group(2)
        items = []
        for b in blocks_in(body):
            first = b.split('\n', 1)[0]
            mm = re.match(r'(LEVEL|SHEET|PLATE|LOOK TARGET|MAP) ([A-Z]{2}[0-9]?-?[A-Z]*[0-9]+),? ([^.]+)\.', first)
            kind, sid, title = mm.group(1), mm.group(2), mm.group(3)
            badge = legs.get(sid, (None, None))[1] if kind == 'LEVEL' else {'SHEET': 'Sheet', 'PLATE': 'Plate', 'MAP': 'Map'}.get(kind)
            items.append(dict(id=sid, title=title[:1].upper() + title[1:], badge=badge, kind=KINDS[kind], text=b))
        rid = head.split(' ', 1)[0]
        # A group's note: the paragraph between its heading and its first prompt (a city's map says what to attach).
        note = body.split('```text', 1)[0].strip().replace('`', '').replace('\n', ' ')
        groups.append(dict(head=head, route=routes.get(rid), note=note or None, items=items))
    look = [b for b in blocks_in(sec) if b.startswith('LOOK TARGET')][0]
    mm = re.match(r'LOOK TARGET ([A-Z]{2}-0), ([^.]+)\.', look)
    out.append(dict(c, block=city_block, look=dict(id=mm.group(1), title=mm.group(2), badge='Look target', kind='look', text=look),
                    groups=groups, sun=clim[c['key']][0], shade=clim[c['key']][1]))

data = dict(base=bases, formats=formats, cities=out)
total = sum(len(g['items']) for c in out for g in c['groups']) + len(out)
print('cities', len(out), 'shots', total, 'levels', sum(1 for c in out for g in c['groups'] for i in g['items'] if i['kind'] == 'level'),
      'maps', sum(1 for c in out for g in c['groups'] for i in g['items'] if i['kind'] == 'map'))
tpl = open(os.path.join(HERE, 'template.html')).read()
open(sys.argv[1], 'w').write(
    tpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
