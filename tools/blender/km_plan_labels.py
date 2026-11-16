# The labels on a Kamakura level's plan from above (preview_km_level.py's plan.png): each place's short name under it,
# in eight rows taken in turn along the level, so neighbours never share a row; the play beats as red lines; the metres.
#   python3 km_plan_labels.py layout.json plan.png plan_labelled.jpg
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def short(it):
    """A place's name on the plan: its label, its model, or its description up to the first bracket or colon."""
    if it.get('label'):
        return it['label']
    if it.get('model'):
        return it['model']
    return re.split(r' \(|: ', it['what'])[0]


def label(lay, plan_path, out_path, rows=8):
    X0, X1 = lay['length']
    plan = Image.open(plan_path).convert('RGB')
    W, H = plan.size
    span = (X1 - X0) + 4
    px = lambda x: (x - (X0 - 2)) / span * W
    py = lambda z: (21.0 - z) / 30.0 * H
    d = ImageDraw.Draw(plan)
    fs = ImageFont.truetype(FONT, 13) if os.path.exists(FONT) else ImageFont.load_default()
    # a place labelled '-' is one of a run already named (a wall's segments after the first, a crossing's stripes)
    items = sorted([it for it in lay['placements'] + lay['markers'] if it.get('label') != '-'], key=lambda it: it['x'])
    base = py(0.75) + 8                      # under the lane's far edge
    for n, it in enumerate(items):
        x, z = it['x'], it['front']
        yy = base + (n % rows) * 17
        d.line([(px(x), py(z)), (px(x), yy)], fill=(20, 20, 20), width=1)
        d.text((px(x) + 2, yy), short(it), font=fs, fill=(10, 10, 10), stroke_width=2, stroke_fill=(250, 250, 250))
    for it in lay['play']:
        d.line([(px(it['x']), 0), (px(it['x']), H)], fill=(200, 40, 40), width=2)
    for x in range(int(X0) // 10 * 10, int(X1) + 1, 10):
        d.text((px(x) + 2, H - 22), '%d m' % x, font=fs, fill=(250, 250, 250), stroke_width=2, stroke_fill=(20, 20, 20))
    plan.save(out_path, quality=86)


if __name__ == '__main__':
    label(json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3])
