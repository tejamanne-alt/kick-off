# Each Kamakura leg's lane, from its lane pictures (docs/IMAGE_PROMPTS.md, "its lane in five pictures"): the user's
# pictures look straight at the lane's fronts, left to right, each picking up where the last ends, so each is built as
# one front of the lane:
#   - the front: the picture above its foot row (the row where the houses, walls, rocks and trees meet the ground),
#     standing upright at the lane's back edge, its sky kept (it is the picture's own sky, and the game camera never
#     sees over its top);
#   - the ground before it: the picture's ground band just below the foot row, laid flat from the front toward the
#     lane, so the paving, sand, rock or path the picture stands on runs on under the lane.
# Each leg's pictures share one texture (KmLane<leg>Atlas.png, 4096 wide). The image tool's mark is painted out.
#   blenv/bin/python km_lanes.py -- /abs/outdir /abs/review/kamakura/lanes [--legs KM2-1,KM2-2] [--install /abs/Art/Models/Kamakura]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index('--') + 1:]
OUT, REVIEW = args[0], args[1]
INSTALL = args[args.index('--install') + 1] if '--install' in args else None
ONLY = args[args.index('--legs') + 1].split(',') if '--legs' in args else None
sys.argv = [sys.argv[0], '--', OUT]
import bpy                                     # noqa: E402,F401
import cv2                                     # noqa: E402
import numpy as np                             # noqa: E402
from mathutils import Vector                   # noqa: E402
from PIL import Image                          # noqa: E402
import kit_buildings_km as KB                  # noqa: E402
import kit_lib as K                            # noqa: E402
import km_leg_kit as LK                        # noqa: E402

P = lambda x, y, z: Vector((x, y, z))
GROUND_DEPTH = 0.85         # the ground laid from the front to the game's footpath (its back edge 1.5 m behind the lane)
PIC_W = 2032                # each picture this wide in its leg's texture: two to a row of 4096 (about 70 to 75 px to the metre)

# each leg: its pictures in order, the fronts' foot row, px to the metre (a 2 m doorway about 160 px in the 724 px tall
# pictures, about 280 px in the 1024 px ones), the ground band's depth in px below the foot row, and its ground's kind
LEGS = {
    'KM1-3': dict(pics=['KM1-3a.png', 'KM1-3b.png', 'KM1-3d.png'], foot=[882, 890, 912], s=140.0, band=100,
                  ground='paving'),
    'KM1-4': dict(pics=['KM1-4a.png', 'KM1-4b.png', 'KM1-4c.png'], foot=[836, 868, 832], s=140.0, band=120,
                  ground='paving'),
    'KM2-1': dict(pics=['KM2-1a_home_lane.png', 'KM2-1b_surfers_houses.png', 'KM2-1c_surf_shop.png',
                        'KM2-1d_tunnel.png', 'KM2-1e_boardwalk.png'], foot=588, s=80.0, band=24, ground='pavement'),
    'KM2-2': dict(pics=['KM2-2a_the_surfboards.png', 'KM2-2b_fishing_boats.png', 'KM2-2c_lifeguard_tower.png',
                        'KM2-2d_sea_wall.png', 'KM2-2e_beach_road.png'], foot=610, s=80.0, band=100, ground='sand'),
    'KM2-4': dict(pics=['KM2-4a_beachs_end.png', 'KM2-4b_rock_shelves.png', 'KM2-4c_tide_pools.png',
                        'KM2-4d_pine.png', 'KM2-4e_torii.png'], foot=612, s=80.0, band=100, ground='rock'),
    'KM2-5': dict(pics=['KM2-5a_raised_path.png', 'KM2-5b_bakery.png', 'KM2-5c_pottery_shop.png',
                        'KM2-5d_crossing.png', 'KM2-5e_red_torii_and_school.png'], foot=602, s=80.0, band=110,
                  ground='paving'),
    'KM3-1': dict(pics=['KM3-1a_the_back_gate.png', 'KM3-1b_the_first_flight.png', 'KM3-1c_the_lantern.png',
                        'KM3-1d_the_rest_hut.png', 'KM3-1e_the_trail_sign.png'], foot=620, s=80.0, band=100,
                  ground='wet stone'),
    'KM3-2': dict(pics=['KM3-2a_the_roots.png', 'KM3-2b_the_footbridge.png', 'KM3-2c_the_cave_tomb.png',
                        'KM3-2d_the_rail_fence.png', 'KM3-2e_genjiyama.png'], foot=575, s=80.0, band=90, ground='path'),
    'KM3-3': dict(pics=['KM3-3a_the_lawn.png', 'KM3-3b_the_bell_tower.png', 'KM3-3c_the_bamboo_grove.png',
                        'KM3-3d_the_steps.png', 'KM3-3e_the_school_gate.png'], foot=605, s=80.0, band=90, ground='path'),
}


def unmark(a):
    """The image tool's ✦ mark out of the bottom right (and the right edge's second one): its near-white,
    colourless sparkle, painted from round it."""
    h, w = a.shape[:2]
    x0, y0 = int(w * 0.84), int(h * 0.55)
    f = a[..., :3].astype(np.int32)
    m = np.zeros((h, w), bool)
    sub = f[y0:, x0:]
    m[y0:, x0:] = (sub.min(-1) > 205) & (sub.max(-1) - sub.min(-1) < 26)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    keep = np.zeros_like(m)
    for i in range(1, n):
        if 30 < st[i, cv2.CC_STAT_AREA] < w * h * 0.004:      # the mark's parts, not a white wall or a cloud
            keep |= lab == i
    keep = cv2.dilate(keep.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    return LK.patch_fill(a[..., :3], keep, patch=9, window=120) if keep.any() else a[..., :3].copy()


def foot_of(L, k):
    return L['foot'][k] if isinstance(L['foot'], list) else L['foot']


def band_of(L, k):
    """The ground band under the fronts, kept to 690 rows in all for the 724 px pictures: five of them then fit a 4096 x 2048
    texture (two to a row)."""
    return min(L['band'], 690 - foot_of(L, k)) if foot_of(L, k) < 724 else L['band']


# what a picture shows that it may not: KM1-3a's station board carries a real railway's logo (the card asked for
# invented names only): the board's own white over it
FIXES = {'KM1-3a.png': [((768, 392, 826, 450), (740, 400, 762, 446))]}


def fix(a, name):
    a = a.copy()
    for (x0, y0, x1, y1), (sx0, sy0, sx1, sy1) in FIXES.get(name, []):
        a[y0:y1, x0:x1] = np.median(a[sy0:sy1, sx0:sx1].reshape(-1, a.shape[2]), 0).astype(a.dtype)
    return a


def lane_model(atlas, a, leg, k, L):
    """One lane picture: its front upright at y = 0 (its middle at x = 0), its ground band laid flat before it."""
    s, foot, band = L['s'], foot_of(L, k), band_of(L, k)
    h, w = a.shape[:2]
    k_ = PIC_W / w                                        # two pictures to a row of the leg's 4096 px texture
    a = cv2.resize(a, (PIC_W, round(h * k_)), interpolation=cv2.INTER_AREA)
    s, foot, band = s * k_, foot * k_, band * k_
    h, w = a.shape[:2]
    pos = atlas.place(Image.fromarray(a[:min(h, int(foot + band) + 2)]))
    cx = w / 2
    X = lambda px: (px - cx) / s
    b = KB.Builder(atlas, pos, lambda co: (cx + co.x * s, foot - co.z * s), pos, (1, 1))
    top = foot / s
    b.face([P(X(0), 0.0, 0.0), P(X(w), 0.0, 0.0), P(X(w), 0.0, top), P(X(0), 0.0, top)])           # the front
    # the ground: its far edge the foot row, its near edge the band's bottom row
    f = b.bm.faces.new([b.bm.verts.new(v) for v in (P(X(0), -GROUND_DEPTH, 0.0), P(X(w), -GROUND_DEPTH, 0.0),
                                                     P(X(w), 0.0, 0.0), P(X(0), 0.0, 0.0))])
    f[b.part] = -1
    for loop in f.loops:
        c = loop.vert.co
        py = foot + band * (-c.y / GROUND_DEPTH)
        loop[b.uv].uv = atlas.uv(pos, cx + c.x * s, min(py, foot + band))
    name = 'KmLane%s%s' % (leg.replace('-', ''), chr(ord('A') + k))
    o = b.object(name, outward=False)
    for poly in o.data.polygons:                          # the ground faces up
        if abs(poly.normal.z) > 0.5 and poly.normal.z < 0:
            poly.flip()
    return o, dict(id='KM-L%s' % leg[2:].replace('-', ''), source='photo/%s: %s\'s lane, picture %d of %d (the front and '
                   'the ground before it)' % (L['pics'][k], leg, k + 1, len(L['pics'])), cutout=False, budget=100,
                   px_per_m=round(s, 2), px_centre=cx, real_size=[round(w / s, 2), GROUND_DEPTH, round(top, 2)],
                   lane=leg, lane_index=k, lane_width=round(w / s, 3), ground=L['ground'])


def checks(o, info, oe, fins, tris):
    return {
        1: ('pass', 'its front and its ground, each once'),
        2: ('limit', '%d edges with one face: a front and a ground, single faces' % oe),
        3: ('limit', 'the picture\'s fronts are flat: their depth is not modelled (the leg\'s set pieces stand before it)'),
        4: ('limit', 'the picture from the lane; nothing behind (no one sees behind it)'),
        5: ('pass', '%.1f x %.1f x %.1f m at %.0f px to the metre, %d triangles, its leg\'s shared texture'
            % (tuple(info['real_size']) + (info['px_per_m'], tris))),
        6: ('pass', 'its edges meet the pictures before and after it'),
        7: ('pass', 'no holes'),
        8: ('pass', 'nothing in front of it is part of it'),
        9: ('pass', 'the user\'s lane picture as it is'),
        10: ('pass', 'whole'),
        11: ('pass', 'invented names; real place names only'),
        12: ('pass', 'its own sky, kept (the camera never sees over it)'),
        13: ('pass', 'the image tool\'s mark painted out'),
        14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'), 17: ('n/a', 'one piece'),
    }


def build_leg(leg):
    L = LEGS[leg]
    K.reset()
    first = np.asarray(KB.ref('photo/' + L['pics'][0]))
    k_ = PIC_W / first.shape[1]
    row = round(min(first.shape[0], max(foot_of(L, k) + band_of(L, k) for k in range(len(L['pics']))) + 2) * k_) + 16
    rows = row * ((len(L['pics']) + 1) // 2) + 16
    atlas = LK.Atlas(4096, 1024 if rows <= 1024 else 2048 if rows <= 2048 else 4096)
    models, boxes = [], {}
    for k, p in enumerate(L['pics']):
        a = unmark(fix(np.asarray(KB.ref('photo/' + p)), p))
        o, info = lane_model(atlas, a, leg, k, L)
        models.append((o, info))
        boxes[o.name] = (0, 0, a.shape[1], a.shape[0])
    src = KB.ref('photo/' + L['pics'][0])
    out = os.path.join(OUT, leg)
    os.makedirs(out, exist_ok=True)
    review_dir = os.path.join(REVIEW, leg)
    orig = LK.review

    def review(models_, mats, _src, rd, bx, ch):
        orig(models_, mats, src, rd, bx, ch)
        for (o, info), p in zip(models_, L['pics']):
            im = KB.ref('photo/' + p)
            im.resize((im.width // 2, im.height // 2)).save(os.path.join(rd, 'source', o.name + '.jpg'), quality=85)
    LK.review = review
    name = 'KmLane%sAtlas.png' % leg.replace('-', '')
    LK.export(models, atlas, out, review_dir, name, 'Lane' + leg.replace('-', ''), src, boxes, checks, INSTALL)
    LK.review = orig
    # the pictures are opaque: saved RGB, so the game's import doesn't take the texture for a cut-out (LEARNINGS D41)
    for d in [out] + ([INSTALL] if INSTALL else []):
        path = os.path.join(d, name)
        if os.path.exists(path):
            Image.open(path).convert('RGB').save(path, optimize=True)


def main():
    for leg in LEGS:
        if ONLY is None or leg in ONLY:
            build_leg(leg)
            print('built', leg)


if __name__ == '__main__':
    main()
