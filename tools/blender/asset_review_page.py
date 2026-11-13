# The asset review's page (docs/ASSET_REVIEW.md, section 4): every model's eight views, its motions, its source and its
# fifteen checks, from the review folder a kit's --review wrote (review.json, views/, motion/, source/, cuts.jpg).
#
#   python3 tools/blender/asset_review_page.py review/kamakura/animals "Kamakura animals" [notes.json]
#
# Writes <folder>/index.html, published as an Artifact with the folder's images beside it. notes.json (optional):
# {"intro": [paragraphs], "limits": [paragraphs], "pending": [paragraphs]}.
import html
import json
import os
import sys

CHECKS = [
    'Every part once', 'Closed shell', 'Depth from own width', 'Views the game sees', 'Size, triangles',
    'Outline whole', 'No holes', 'Own models before walls', 'Look target', 'Solid', 'No brands',
    'No wires or sky', 'Repairs listed', 'Rig names', 'Joints overlap',
]
GROUPS = [
    ('walk', 'Walking', 'four legs swinging in diagonal pairs, as the game\'s dog swings them'),
    ('scurry', 'Scurrying', 'drawn mid-leap: the body bounds, the tail streams'),
    ('peck', 'On the ground', 'birds that hop and peck'),
    ('fly', 'In flight', 'small birds and insects, seen from below or above as they pass'),
    ('swim', 'In the water', 'koi and a swimming turtle'),
    ('idle', 'Resting', 'sitting, lying or perched: the tail or head moves'),
    ('', 'Still', 'nothing moves'),
]


def group_of(motions):
    for key, _, _ in GROUPS:
        if key and key in motions:
            return key
    return ''


def esc(s):
    return html.escape(str(s), quote=True)


STYLE = '''
/* A review desk: a matrix of every model against every check first, then each model's sheet, motions and notes. */
:root {
  --bg: #eef0f2; --panel: #ffffff; --ink: #1d2430; --muted: #5d6675; --line: #d5dae1;
  --accent: #2f4f86; --pass: #1f7a4d; --pass-bg: #dcefe4; --limit: #946200; --limit-bg: #f6e9c8;
  --fail: #b3261e; --fail-bg: #f7d9d6; --na: #8a93a1; --na-bg: #e9ecf0;
  --display: "Zen Kaku Gothic New", "Hiragino Sans", "Segoe UI", system-ui, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #14181f; --panel: #1c222b; --ink: #e6e9ee; --muted: #9aa3b2; --line: #2e3642;
  --accent: #8fb0ea; --pass: #6fcf9a; --pass-bg: #18392a; --limit: #e8bd5a; --limit-bg: #3b3018;
  --fail: #ff8f86; --fail-bg: #45201d; --na: #8a93a1; --na-bg: #262d37; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #14181f; --panel: #1c222b; --ink: #e6e9ee; --muted: #9aa3b2; --line: #2e3642;
  --accent: #8fb0ea; --pass: #6fcf9a; --pass-bg: #18392a; --limit: #e8bd5a; --limit-bg: #3b3018;
  --fail: #ff8f86; --fail-bg: #45201d; --na: #8a93a1; --na-bg: #262d37; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font: 16px/1.55 var(--body); }
.wrap { max-width: 1180px; margin: 0 auto; padding-block: 28px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1, h2, h3 { font-family: var(--display); text-wrap: balance; margin: 0; line-height: 1.2; }
h1 { font-size: 2rem; font-weight: 700; }
h2 { font-size: 1.35rem; font-weight: 700; }
h3 { font-size: 1.1rem; font-weight: 700; }
p { margin: 0; max-width: 68ch; }
a { color: var(--accent); }
a:focus-visible, summary:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.eyebrow { font: 600 0.75rem var(--mono); letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.stack { display: flex; flex-direction: column; gap: 14px; }
header.top { display: flex; flex-direction: column; gap: 12px; margin-bottom: 28px; }
.tally { display: flex; flex-wrap: wrap; gap: 8px; }
.pill { font: 600 0.8rem var(--mono); padding: 3px 10px; border-radius: 999px; font-variant-numeric: tabular-nums; }
.pill.pass { color: var(--pass); background: var(--pass-bg); }
.pill.limit { color: var(--limit); background: var(--limit-bg); }
.pill.fail { color: var(--fail); background: var(--fail-bg); }
.pill.na { color: var(--na); background: var(--na-bg); }
.notes { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 32px; }
.note { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: flex;
  flex-direction: column; gap: 8px; min-width: 0; }
.note ul { margin: 0; padding-left: 1.1em; display: flex; flex-direction: column; gap: 6px; }
.matrix-box { overflow-x: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
  margin-bottom: 12px; }
table.matrix { border-collapse: collapse; font: 0.8rem var(--mono); font-variant-numeric: tabular-nums; }
.matrix th, .matrix td { padding: 4px 6px; border-bottom: 1px solid var(--line); text-align: center; white-space: nowrap; }
.matrix th.name, .matrix td.name { text-align: left; position: sticky; left: 0; background: var(--panel); }
.matrix thead th { color: var(--muted); font-weight: 600; vertical-align: bottom; }
.matrix tr.grp td { text-align: left; font: 700 0.8rem var(--display); color: var(--accent); padding-top: 12px;
  background: var(--panel); }
.cell { display: inline-block; width: 22px; height: 18px; border-radius: 4px; line-height: 18px; font-size: 0.7rem;
  font-weight: 700; }
.cell.pass { background: var(--pass-bg); color: var(--pass); }
.cell.limit { background: var(--limit-bg); color: var(--limit); }
.cell.fail { background: var(--fail-bg); color: var(--fail); }
.cell.na { background: var(--na-bg); color: var(--na); }
.legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 2px 16px;
  font-size: 0.85rem; color: var(--muted); margin-bottom: 36px; }
.legend b { font-family: var(--mono); color: var(--ink); margin-right: 6px; }
section.group { display: flex; flex-direction: column; gap: 20px; margin-top: 36px; }
.group-head { display: flex; flex-direction: column; gap: 4px; border-bottom: 2px solid var(--ink); padding-bottom: 8px; }
article.model { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px;
  display: flex; flex-direction: column; gap: 14px; scroll-margin-top: 16px; min-width: 0; }
.model-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; }
.facts { font: 0.82rem var(--mono); color: var(--muted); font-variant-numeric: tabular-nums; }
.views img { width: 100%; height: auto; border-radius: 6px; display: block; }
.row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 14px; align-items: start; }
@media (max-width: 720px) { .row { grid-template-columns: minmax(0, 1fr); } }
figure { margin: 0; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
figcaption { font: 0.78rem var(--mono); color: var(--muted); }
.src img { width: 100%; height: auto; border-radius: 6px; background: #777; }
.motions { display: flex; flex-wrap: wrap; gap: 12px; }
.motions figure { width: min(280px, 100%); }
.motions img { width: 100%; height: auto; border-radius: 6px; display: block; }
.still { font-size: 0.9rem; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: 4px; }
details.checks summary { cursor: pointer; font-weight: 600; }
table.checks { border-collapse: collapse; width: 100%; font-size: 0.88rem; margin-top: 8px; }
.checks td { border-top: 1px solid var(--line); padding: 6px 8px 6px 0; vertical-align: top; }
.checks td.n { font: 600 0.8rem var(--mono); color: var(--muted); width: 2em; }
.checks td.c { width: 30%; font-weight: 600; }
.checks td.r { width: 4.5em; }
.checks td.w { color: var(--muted); overflow-wrap: anywhere; }
.toc { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 0.9rem; margin-bottom: 8px; }
.cuts img { width: 100%; height: auto; border-radius: 6px; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
'''


def page(folder, title, notes):
    review = json.load(open(os.path.join(folder, 'review.json')))
    names = list(review)
    by_group = {}
    for n in names:
        by_group.setdefault(group_of(review[n]['motions']), []).append(n)
    counts = {'pass': 0, 'limit': 0, 'FAIL': 0, 'n/a': 0}
    for n in names:
        for c in review[n]['checks']:
            counts[c[2]] = counts.get(c[2], 0) + 1
    cls = {'pass': 'pass', 'limit': 'limit', 'FAIL': 'fail', 'n/a': 'na'}
    sym = {'pass': '✓', 'limit': '!', 'FAIL': '✗', 'n/a': '–'}
    out = []
    w = out.append
    w('<title>%s Review</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' % esc(title))
    w('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    w('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&'
      'family=Source+Sans+3:wght@400;600&family=Zen+Kaku+Gothic+New:wght@500;700&display=swap">\n')
    w('<style>%s</style>\n<div class="wrap">\n' % STYLE)
    fails = [(n, c) for n in names for c in review[n]['checks'] if c[2] == 'FAIL']
    w('<header class="top"><span class="eyebrow">Asset review · docs/ASSET_REVIEW.md</span>')
    w('<h1>%s</h1>' % esc(title))
    for para in notes.get('intro', []):
        w('<p>%s</p>' % para)
    w('<div class="tally"><span class="pill pass">%d models</span>' % len(names))
    for k in ('pass', 'limit', 'FAIL', 'n/a'):
        w('<span class="pill %s">%d %s</span>' % (cls[k] if counts.get(k, 0) else 'na', counts.get(k, 0), {'pass': 'checks passed', 'limit': 'known limits',
                                                                          'FAIL': 'failed', 'n/a': 'not applicable'}[k]))
    w('</div></header>\n')
    w('<div class="notes">')
    for key, head in (('fixed', 'Fixed in this pass'), ('limits', 'Known limits'), ('pending', 'Still to come')):
        if notes.get(key):
            w('<div class="note"><h3>%s</h3><ul>%s</ul></div>' % (head, ''.join('<li>%s</li>' % p for p in notes[key])))
    if fails:
        w('<div class="note"><h3>Failed checks</h3><ul>%s</ul></div>' % ''.join(
            '<li><a href="#%s">%s</a>: %s. %s</li>' % (esc(n), esc(n), esc(c[1]), esc(c[3])) for n, c in fails))
    w('</div>\n')
    # the matrix
    w('<h2 style="margin-bottom:10px">Every model against every check</h2>')
    w('<div class="matrix-box"><table class="matrix"><thead><tr><th class="name">Model</th>')
    for i in range(1, 16):
        w('<th title="%s">%d</th>' % (esc(CHECKS[i - 1]), i))
    w('<th>tris</th><th>motions</th></tr></thead><tbody>')
    for key, label, _ in GROUPS:
        if key not in by_group:
            continue
        w('<tr class="grp"><td colspan="18">%s</td></tr>' % esc(label))
        for n in by_group[key]:
            r = review[n]
            w('<tr><td class="name"><a href="#%s">%s</a></td>' % (esc(n), esc(n)))
            for c in r['checks']:
                w('<td><span class="cell %s" title="%d %s: %s">%s</span></td>' % (cls[c[2]], c[0], esc(c[1]), esc(c[2]),
                                                                              sym[c[2]]))
            w('<td>%d</td><td style="text-align:left">%s</td></tr>' % (r['tris'], esc(', '.join(r['motions']) or '–')))
    w('</tbody></table></div>')
    w('<div class="legend">%s</div>\n' % ''.join('<span><b>%d</b>%s</span>' % (i + 1, esc(c)) for i, c in enumerate(CHECKS)))
    if os.path.exists(os.path.join(folder, 'cuts.jpg')):
        w('<figure class="cuts"><h2>The cut-outs</h2><img src="cuts.jpg" loading="lazy" alt="Every model\'s outline on its '
          'sheet, its parts coloured: body grey, tail orange, head cyan, near legs bright, far legs dark, wings purple">'
          '<figcaption>Every outline on its sheet, the parts coloured: body grey, tail orange, head cyan, legs green '
          '(front) and yellow (back), near bright and far dark, wings purple. Checks 6 and 7 are read here.</figcaption>'
          '</figure>\n')
    for key, label, blurb in GROUPS:
        if key not in by_group:
            continue
        w('<section class="group"><div class="group-head"><h2>%s</h2><p class="facts">%d models · %s</p></div>' % (
            esc(label), len(by_group[key]), esc(blurb)))
        for n in by_group[key]:
            r = review[n]
            tally = {}
            for c in r['checks']:
                tally[c[2]] = tally.get(c[2], 0) + 1
            w('<article class="model" id="%s"><div class="model-head"><h3>%s</h3><span class="facts">%s · %s · %s m · '
              '%d triangles</span></div>' % (esc(n), esc(n), esc(r['id']), esc(r['sheet'].split('_')[0]),
                                            ' × '.join('%.2f' % v for v in r['size']), r['tris']))
            w('<figure class="views"><img src="views/%s.jpg" loading="lazy" alt="%s from all eight sides">'
              '<figcaption>Front, back, left, right (the game view), left 3/4, right 3/4, top, bottom</figcaption></figure>'
              % (esc(n), esc(n)))
            w('<div class="row"><figure class="src"><img src="source/%s.jpg" loading="lazy" alt="%s on its sheet">'
              '<figcaption>The source: %s</figcaption></figure>' % (esc(n), esc(n), esc(r['sheet'])))
            if r['motions']:
                w('<div class="motions">%s</div>' % ''.join(
                    '<figure><img src="motion/%s_%s.gif" loading="lazy" alt="%s: %s"><figcaption>%s</figcaption></figure>'
                    % (esc(n), esc(m), esc(n), esc(m), esc(m)) for m in r['motions']))
            else:
                w('<p class="still">No moving parts: it stays still in the game.</p>')
            w('</div>')
            summary = ', '.join('%d %s' % (tally[k], {'pass': 'passed', 'limit': 'known limit', 'FAIL': 'FAILED',
                                                       'n/a': 'n/a'}[k]) for k in ('FAIL', 'limit', 'pass', 'n/a') if k in tally)
            w('<div class="chips">%s</div>' % ''.join('<span class="cell %s" title="%s">%d</span>' % (cls[c[2]], esc(c[1]), c[0])
                                                    for c in r['checks']))
            w('<details class="checks"%s><summary>The 15 checks: %s</summary><table class="checks">' % (
                ' open' if 'FAIL' in tally or 'limit' in tally else '', esc(summary)))
            for c in r['checks']:
                w('<tr><td class="n">%d</td><td class="c">%s</td><td class="r"><span class="pill %s">%s</span></td>'
                  '<td class="w">%s</td></tr>' % (c[0], esc(c[1]), cls[c[2]], esc(c[2]), esc(c[3])))
            w('</table></details></article>\n')
        w('</section>\n')
    w('</div>\n')
    path = os.path.join(folder, 'index.html')
    open(path, 'w').write(''.join(out))
    print(path, sum(len(x) for x in out) // 1024, 'KB')


if __name__ == '__main__':
    folder, title = sys.argv[1], sys.argv[2]
    notes = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    page(folder, title, notes)
