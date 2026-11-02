# Builds the game's world map picture and its layout data: an aerial view of the town the kid walks through, rendered from the
# game's own kit models, and TownMapLayout.json (the routes, the level nodes, the district and street-name anchors) that the
# map screen draws on it. The layout (town_map_layout.py) is data; the picture and the JSON both come from it, so they agree.
#
#   blenv/bin/python town_map.py -- <out dir> [--scale 1.0] [--samples 32] [--ss 2] [--crop x0,y0,x1,y1] [--debug] [--no-render]
#
# writes <out dir>/TownMap.jpg (3200 x 1800), <out dir>/TownMapLayout.json, <out dir>/TownMap_ground.png (the painted ground),
# and with --debug <out dir>/TownMap_debug.png (the routes, nodes and label boxes over the picture).
#   --scale 0.5   renders at half size (the JSON is always in the full 3200 x 1800 pixels)
#   --crop        renders only that part of the full picture (picture px), for a close look
import sys, os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image

import town_map_graph as G
import town_map_layout as L
import town_map_build as B
import town_map_raster as R
import town_map_ground as GR
import town_map_place as PL
import town_map_sets as SETS
import town_map_plan as PLAN


def log(t0, msg):
    print(f'[{time.time() - t0:6.1f}s] {msg}', flush=True)


def grade(img, saturation=0.93, contrast=1.05, lift=0.012):
    """The picture's grade: a little less saturation, a touch of contrast, cool shadows, bright daylight."""
    a = np.asarray(img.convert('RGB'), np.float32) / 255.0
    lum = (a * np.array([0.299, 0.587, 0.114], np.float32)).sum(axis=2, keepdims=True)
    a = lum + (a - lum) * saturation
    a = 0.5 + (a - 0.5) * contrast
    sh = np.clip(1 - lum * 2.0, 0, 1)
    a = a + sh * np.array([-0.008, 0.002, 0.016], np.float32) + lift
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def main(argv):
    args = argv[argv.index('--') + 1:] if '--' in argv else argv[1:]
    out_dir = args[0]
    scale = float(args[args.index('--scale') + 1]) if '--scale' in args else 1.0
    samples = int(args[args.index('--samples') + 1]) if '--samples' in args else 32
    ss = int(args[args.index('--ss') + 1]) if '--ss' in args else 2
    crop = tuple(int(v) for v in args[args.index('--crop') + 1].split(',')) if '--crop' in args else None
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()

    built = B.build(L)
    log(t0, 'layout built: routes %s, %d nodes%s' % ({k: round(G.poly_length(v)) for k, v in built['routes'].items()}, len(built['nodes']),
                                                   ('; WARNING ' + built['label_error']) if built['label_error'] else ''))
    data = B.to_json(L, built)
    with open(os.path.join(out_dir, 'TownMapLayout.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
    if '--layout-only' in args:
        return

    masks = GR.Masks(L, built)
    log(t0, 'road masks')
    world, items, lots, sets = PL.generate(L, built, masks, SETS.Sets)
    log(t0, 'placed %d models (%d lots)' % (len(items), len(lots)))
    ground_png = os.path.join(out_dir, 'TownMap_ground.png')
    if '--repaint' in args or not os.path.exists(ground_png) or '--keep-ground' not in args:
        cv = R.Canvas(ss)
        GR.paint_all(cv, L, built, masks, lots, sets)
        cv.save(ground_png)
        log(t0, 'ground painted')
    if '--no-render' in args:
        return

    import town_map_scene as SC
    S = SC.reset()
    SC.ground(S, ground_png)
    SC.lights(S)
    SC.camera(S, scale)
    n = SC.add_items(S, items)
    log(t0, 'scene: %d objects' % n)
    raw = os.path.join(out_dir, 'TownMap_raw.png')
    dt = SC.render(S, raw, samples, crop)
    log(t0, 'rendered in %.0fs' % dt)
    img = grade(Image.open(raw))
    name = 'TownMap.jpg' if not crop and scale == 1.0 else ('TownMap_crop_%d_%d.jpg' % (crop[0], crop[1]) if crop else 'TownMap_preview.jpg')
    img.save(os.path.join(out_dir, name), quality=92, subsampling=0)
    log(t0, 'saved ' + name)
    if '--debug' in args and not crop:
        full = img.resize((R.IMG_W, R.IMG_H)) if img.size != (R.IMG_W, R.IMG_H) else img
        PLAN.draw_overlay(full, built).save(os.path.join(out_dir, 'TownMap_debug.png'))


if __name__ == '__main__':
    main(sys.argv)
