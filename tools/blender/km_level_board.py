# The page for a Kamakura level's proposed layout (docs/LEARNINGS.md A8: approval before building): the reference picture,
# the layout through the game camera screen by screen (preview_km_level.py's strip), the plan from above, the play beats,
# and the decisions and questions, all from the level's layout.json and notes.json.
#   python3 tools/blender/km_level_board.py review/kamakura/levels/KM1-1
# Writes <folder>/index.html, published as an Artifact with reference.jpg, strip.jpg and plan.jpg beside it.
import html, json, os, sys

folder = sys.argv[1]
lay = json.load(open(os.path.join(folder, 'layout.json')))
notes = json.load(open(os.path.join(folder, 'notes.json')))
esc = lambda s: html.escape(str(s), quote=True)

STYLE = '''
:root { --bg: #f1f2ef; --panel: #ffffff; --ink: #1f2522; --muted: #5d6762; --line: #d6dbd6; --accent: #b23a2e;
  --strip: #2a2e2c; --note-bg: #f7f1e3; --note-ink: #6b4f12;
  --display: "Zen Kaku Gothic New", "Hiragino Sans", "Segoe UI", system-ui, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif; --mono: "JetBrains Mono", ui-monospace, Menlo, monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #151816; --panel: #1d211f; --ink: #e6ebe7; --muted: #9ba8a1; --line: #2f3632; --accent: #ef8a7c;
  --strip: #0f1110; --note-bg: #322a17; --note-ink: #ecc977; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #151816; --panel: #1d211f; --ink: #e6ebe7; --muted: #9ba8a1; --line: #2f3632;
  --accent: #ef8a7c; --strip: #0f1110; --note-bg: #322a17; --note-ink: #ecc977; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font: 16px/1.55 var(--body); }
.wrap { max-width: 1180px; margin: 0 auto; padding-block: 28px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: flex; flex-direction: column; gap: 28px; }
h1, h2 { font-family: var(--display); margin: 0; line-height: 1.2; text-wrap: balance; }
h1 { font-size: 2rem; } h2 { font-size: 1.3rem; }
p { margin: 0; max-width: 70ch; }
.eyebrow { font: 600 0.75rem var(--mono); letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
section { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
figure { margin: 0; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
figcaption { font: 0.8rem var(--mono); color: var(--muted); }
.scroll { overflow-x: auto; border-radius: 8px; background: var(--strip); }
.scroll img { display: block; height: 320px; width: auto; max-width: none; }
.full img { width: 100%; height: auto; border-radius: 8px; display: block; }
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; }
td, th { border-top: 1px solid var(--line); padding: 7px 10px 7px 0; vertical-align: top; text-align: left; }
th { font: 600 0.78rem var(--mono); color: var(--muted); }
td.x { font: 0.85rem var(--mono); white-space: nowrap; font-variant-numeric: tabular-nums; width: 5em; }
.table-box { overflow-x: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 4px 14px 10px; }
ul { margin: 0; padding-left: 1.1em; display: flex; flex-direction: column; gap: 6px; max-width: 75ch; }
.ask { background: var(--note-bg); color: var(--note-ink); border-radius: 8px; padding: 14px 16px; }
.ask ul { color: var(--ink); }
'''

w = []
w.append('<title>%s layout</title>' % esc(lay['level']))
w.append('<meta name="claude:viewport-fit-sides" content="cover">')
w.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&'
         'family=Source+Sans+3:wght@400;600&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap">')
w.append('<style>%s</style><div class="wrap">' % STYLE)
w.append('<header class="stack"><div class="eyebrow">Kamakura · route 1 · leg 1 · proposed layout</div>'
         '<h1>%s %s</h1>' % (esc(lay['level']), esc(lay['name'])))
for para in notes['intro']:
    w.append('<p>%s</p>' % para)
w.append('</header>')
w.append('<section><h2>The picture it comes from</h2><figure class="full"><img src="reference.jpg" alt="KM1-1 Hase Lanes, '
         'the reference picture"><figcaption>%s</figcaption></figure></section>' % esc(notes['reference']))
w.append('<section><h2>Through the game camera</h2><p>%s</p><figure><div class="scroll"><img src="strip.jpg" alt="The layout '
         'through the game camera, screen by screen"></div><figcaption>Scroll sideways: each screen is what the camera '
         'shows as the kid walks on; the red figure is the kid (1.57 m) with the ball.</figcaption></figure></section>'
         % notes['strip'])
w.append('<section><h2>From above</h2><figure class="full"><img src="plan.jpg" alt="The level from above, each place '
         'labelled"><figcaption>The camera is below the picture; red lines mark the play beats.</figcaption></figure></section>')
w.append('<section><h2>The play</h2><div class="table-box"><table><thead><tr><th>x (m)</th><th>What happens</th></tr></thead><tbody>')
for b in lay['play']:
    w.append('<tr><td class="x">%.0f</td><td>%s</td></tr>' % (b['x'], esc(b['what'])))
w.append('</tbody></table></div></section>')
w.append('<section><h2>Where everything stands</h2><div class="table-box"><table><thead><tr><th>x (m)</th><th>Model</th>'
         '<th>Why there</th></tr></thead><tbody>')
for p in sorted(lay['placements'], key=lambda p: p['x']):
    w.append('<tr><td class="x">%.1f</td><td>%s</td><td>%s</td></tr>' % (p['x'], esc(p['model']), esc(p['note'])))
for m in sorted(lay['markers'], key=lambda p: p['x']):
    w.append('<tr><td class="x">%.1f</td><td>(to come)</td><td>%s</td></tr>' % (m['x'], esc(m['what'])))
w.append('</tbody></table></div></section>')
w.append('<section><h2>Decided for now</h2><ul>%s</ul></section>' % ''.join('<li>%s</li>' % d for d in notes['decided']))
w.append('<section class="ask"><h2>For you</h2><ul>%s</ul></section>' % ''.join('<li>%s</li>' % q for q in notes['ask']))
w.append('</div>')
open(os.path.join(folder, 'index.html'), 'w').write('\n'.join(w))
print('wrote', os.path.join(folder, 'index.html'))
