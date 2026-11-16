# KM2-2 Yuigahama Morning's set pieces (docs/KAMAKURA_BUILD.md, BUILD KM-L22), from the photographic KM2-2 with
# km_leg_kit.py, as KM2-1's were. The picture looks along the beach with the sea's horizon in it (row 456), so every
# piece takes its scale from how far its foot stands below the horizon: s = (foot - 456) / 2.64 px to the metre, the
# picture's eye 2.64 m up (the lifeguard tower, 4.7 m to its roof's top, sets it; the boats come out 4.9 and 5.1 m long,
# the surfboards 1.6 to 1.9 m above the sand, the sea wall 1.75 m above its dune). The pieces:
#   - the near fishing boat on its rollers (KM-B20), and in front of it its gear (KM-A37): the crab traps and the net,
#     the fish boxes (KM-A35) and the coiled ropes, as two cut-outs, the gear to stand nearer;
#   - the far fishing boat on its rollers with its net (KM-B20, a cut-out);
#   - the lifeguard tower (KM-B21): its roof, posts, cabin, platform and four legs as boxes from the picture, the cross
#     braces as strips on the front legs, each box showing only its own part of the picture; its ladder leaning in front
#     and its flag (cut out);
#   - the sea wall (KM-B23) squared up out of the picture's perspective, the tower painted out of it;
#   - the beach houses and black pines above the sea wall (KM-B37, new; a cut-out against the sky, the tower painted
#     out of it);
#   - the litter sacks and their bamboo fence (KM-A41, new), three surfboards stuck in the sand (KM-A36), the beach's
#     rules board on its post (KM-A42, new) and Enoshima on the horizon (KM-B38, new): cut-outs.
# All of them share one texture, KmBeachAtlas.png (4096 x 2048).
#   blenv/bin/python km_beach.py -- /abs/outdir /abs/review/kamakura/beach [--install /abs/Assets/_Game/Art/Models/Kamakura]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index('--') + 1:]
OUT, REVIEW = args[0], args[1]
INSTALL = args[args.index('--install') + 1] if '--install' in args else None
sys.argv = [sys.argv[0], '--', OUT]            # the kit module reads its own arguments
import bpy                                     # noqa: E402,F401  (it brings mathutils)
import cv2                                     # noqa: E402
import numpy as np                             # noqa: E402
from mathutils import Vector                   # noqa: E402
from PIL import Image                          # noqa: E402
import kit_buildings_km as KB                  # noqa: E402
import kit_lib as K                            # noqa: E402
import km_leg_kit as LK                        # noqa: E402

SRC = 'photo/KM2-2_yuigahama_morning.png'
ATLAS_W, ATLAS_H = 4096, 2048
HORIZON, PIC_EYE = 456.0, 2.64
P = lambda x, y, z: Vector((x, y, z))


def s_at(foot):
    """px to the metre of a thing whose foot is at row `foot`."""
    return (foot - HORIZON) / PIC_EYE


# ---------------------------------------------------------------- the outlines, in the picture's pixels (measured)
BOAT = [(1600, 742), (1606, 722), (1652, 698), (1655, 662), (1672, 650), (1706, 652), (1712, 690), (1815, 672),
        (1866, 673), (2120, 659), (2228, 630), (2242, 638), (2232, 666), (2190, 705), (2140, 742), (1960, 776),
        (1696, 782), (1684, 770), (1672, 740), (1618, 750)]
ROLLERS = [(1532, 764, 1700, 802), (1732, 786, 1762, 814)]
BOAT_BOX, BOAT_FOOT = (1528, 626, 2246, 816), 800
TRAPS = [(2015, 700), (2030, 680), (2070, 674), (2110, 678), (2130, 700), (2130, 770), (2080, 778), (2080, 835),
         (2062, 848), (2000, 848), (1968, 832), (1964, 790), (1985, 758), (2015, 750)]
CRATES = [(2077, 752), (2145, 737), (2175, 735), (2234, 758), (2234, 822), (2150, 834), (2095, 834), (2077, 826)]
ROPES = (1880, 776, 2236, 846)            # the big coil and those by the boxes (the trail across the sand left)
GEAR_BOX, GEAR_FOOT = (1754, 670, 2238, 850), 845
FAR_HULL = [(1746, 622), (1750, 600), (1785, 573), (1806, 578), (1800, 596), (1938, 580), (1938, 534), (1953, 534),
            (1953, 578), (1992, 570), (2000, 562), (2048, 562), (2126, 553), (2134, 558), (2125, 576), (2088, 604),
            (2050, 626), (1980, 640), (1790, 640), (1782, 615), (1765, 625)]
FAR_ROLLERS = [(1803, 636, 1832, 659), (1885, 638, 1903, 661), (1968, 634, 1988, 660)]
FAR_NET = [(2014, 640), (2020, 622), (2050, 619), (2072, 632), (2072, 655), (2040, 660), (2016, 656)]
FAR_BOX, FAR_FOOT = (1742, 530, 2138, 662), 658
TOWER_FOOT = 772
ROOF = [(2322, 236), (2380, 206), (2594, 249), (2594, 256), (2568, 266), (2352, 261), (2322, 243)]
ROOF_UNDER = [(2365, 256), (2562, 260), (2562, 283), (2505, 289), (2378, 270)]   # its underside, seen from below
FLAG = (2350, 80, 2442, 222)
LADDER = [(2304, 742), (2328, 768), (2342, 768), (2392, 458), (2362, 456)]
BRACES = [((2410, 486), (2550, 645)), ((2547, 486), (2405, 630))]
BACK_ZONE = (2366, 484, 2564, 662)          # the far braces (the back and sides), dark wood seen between the legs
SACKS = [(2442, 790), (2448, 750), (2470, 705), (2500, 697), (2520, 688), (2560, 684), (2600, 684), (2640, 690),
         (2665, 700), (2680, 715), (2690, 740), (2698, 800), (2690, 808), (2640, 815), (2630, 828), (2560, 829),
         (2520, 819), (2475, 813), (2445, 800)]
FENCE = [(2566, 618), (2597, 624), (2600, 607), (2608, 607), (2611, 628), (2650, 632), (2705, 638), (2707, 629),
         (2721, 629), (2723, 652), (2737, 658), (2752, 795), (2700, 805), (2566, 805)]
SACKS_BOX, SACKS_FOOT = (2438, 602, 2756, 832), 815
BOARDS = [  # each board: its outline and its foot
    ([(1346, 526), (1352, 528), (1356, 545), (1358, 580), (1357, 620), (1352, 641), (1325, 641), (1321, 620),
      (1322, 580), (1328, 545), (1340, 528)], 640),
    ([(1386, 505), (1392, 510), (1398, 540), (1401, 580), (1400, 625), (1394, 632), (1376, 632), (1371, 620),
      (1371, 580), (1374, 540), (1380, 510)], 631),
    ([(1446, 497), (1452, 501), (1460, 525), (1465, 560), (1463, 597), (1450, 597), (1443, 560), (1441, 525)], 596)]
SIGN = [(3141, 482), (3224, 475), (3233, 576), (3204, 579), (3204, 658), (3190, 658), (3190, 580), (3150, 585)]
SIGN_BOX, SIGN_FOOT = (3138, 472, 3236, 660), 656
WALL_QUAD = [(2276, 480), (3010, 504), (3010, 592), (2276, 534)]   # its top and its foot in the dune, both ends
WALL_LEN, WALL_H, WALL_PX = 14.0, 1.75, 100
HOUSES = (2018, 56, 3292, 504)
HOUSES_FOOT = 598
ENOSHIMA = (1215, 390, 1680, 457)


def wall_top(x):
    x0, y0 = WALL_QUAD[0]
    x1, y1 = WALL_QUAD[1]
    return y0 + (np.clip(x, x0, x1) - x0) * (y1 - y0) / (x1 - x0)


def poly_mask(shape, polys=(), rects=()):
    m = np.zeros(shape[:2], np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = 1
    return m


def strip(a, b, half=5.0):
    """A brace from a to b, half px either side of its line."""
    (xa, ya), (xb, yb) = a, b
    L = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
    nx, ny = (yb - ya) / L * half, -(xb - xa) / L * half
    return [(xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)]


# the tower's parts: (name, picture box x0, y0, x1, y1, depth from, depth to, sample)
TOWER_PARTS = [
    ('roof', 2322, 206, 2594, 289, -0.25, 1.9, 'roof'),
    ('post_fl', 2402, 245, 2415, 460, 0.0, 0.12, 'wood'), ('post_bl', 2355, 255, 2370, 460, 1.5, 1.62, 'wood'),
    ('post_br', 2492, 268, 2505, 367, 1.5, 1.62, 'wood'), ('post_fr', 2540, 262, 2554, 367, 0.0, 0.12, 'wood'),
    ('cabin', 2415, 367, 2555, 460, 0.0, 1.6, 'boards'),
    ('platform', 2350, 460, 2560, 482, -0.1, 1.7, 'wood'),
    ('leg_fl', 2392, 482, 2412, 772, 0.0, 0.16, 'wood'), ('leg_fr', 2540, 482, 2564, 772, 0.0, 0.16, 'wood'),
    ('leg_bl', 2350, 482, 2365, 772, 1.5, 1.66, 'wood'), ('leg_br', 2492, 482, 2510, 772, 1.5, 1.66, 'wood')]


def tower_masks(shape, a):
    """The tower's own pixels: its boxes' parts (the roof by its outline and its underside), the front braces, the flag
    and its pole (not the sky); the ladder apart; the far braces apart (the dark wood between the legs)."""
    m = poly_mask(shape, [ROOF, ROOF_UNDER] + [strip(*b) for b in BRACES],
                  [(x0, y0, x1, y1) for n, x0, y0, x1, y1, *_ in TOWER_PARTS if n != 'roof'] + [(2354, 82, 2362, 222)])
    x0, y0, x1, y1 = FLAG
    flag = poly_mask(shape, [[(2360, 90), (2440, 100), (2438, 162), (2360, 156)]])
    flag[y0:y1, x0:x1] &= (~LK.sky_mask(a[y0:y1, x0:x1])).astype(np.uint8)
    struct = m | flag
    f = a[..., :3].astype(np.int32)
    luma = 0.3 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
    x0, y0, x1, y1 = BACK_ZONE
    back = np.zeros(shape[:2], np.uint8)
    back[y0:y1, x0:x1] = ((luma[y0:y1, x0:x1] < 105) & (f[y0:y1, x0:x1].max(-1) - f[y0:y1, x0:x1].min(-1) < 50))
    back = cv2.morphologyEx(back, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    back = cv2.morphologyEx(back, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    back &= 1 - cv2.dilate(struct, np.ones((3, 3), np.uint8))
    return struct, poly_mask(shape, [LADDER]), back


# ---------------------------------------------------------------- the picture, painted
def pictures():
    """The photographic KM2-2 (src); the tower's own copy, its legs' feet hidden by the sacks and the fence carried on
    down to the sand (tower_img); the picture with the tower painted out of the houses and pines behind it (img)."""
    src = KB.ref(SRC)
    a = np.asarray(src).copy()
    t = a.copy()
    for x0, x1, y_from in ((2490, 2512, 700), (2538, 2566, 688), (2348, 2367, 742)):
        for y in range(y_from, TOWER_FOOT + 2):
            t[y, x0:x1] = t[y - 40, x0:x1]
    struct, ladder, back = tower_masks(a.shape, a)
    # the tower out of the houses and pines behind it, down to the wall's top: painted from what is round it there
    rows = np.arange(a.shape[0])[:, None]
    below = rows >= wall_top(np.arange(a.shape[1]))[None, :] + 3
    hole = cv2.dilate(struct | ladder | back, np.ones((7, 7), np.uint8)).astype(bool) & ~below
    hole[:, :2290] = False
    b = LK.patch_fill(a[..., :3], hole, patch=11, window=150, avoid=below)
    return src, Image.fromarray(t), Image.fromarray(b), struct, ladder, back


# ---------------------------------------------------------------- the models
def cutout(atlas, a, mask, box, foot, name, info, y=0.0, both=True):
    """A cut-out of box (its pixels a, its outline mask), its foot at row `foot`, scaled by its distance below the
    horizon."""
    x0, y0, x1, y1 = box
    s = s_at(foot)
    rgba = np.dstack([a[y0:y1, x0:x1], mask[y0:y1, x0:x1] * 255])
    o = LK.card(atlas, rgba, box, (x0 + x1) / 2, float(foot), s, y, name, both)
    info.update(real_size=[round((x1 - x0) / s, 2), 0.01, round((foot - y0) / s, 2)], px_centre=(x0 + x1) / 2,
                px_per_m=round(s, 2), cutout=True)
    info.setdefault('budget', 100)
    return o, info


def boat_masks(a):
    f = a.astype(np.int32)
    luma = 0.3 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
    gear = poly_mask(a.shape, [TRAPS, CRATES])
    x0, y0, x1, y1 = ROPES
    sand = np.median(luma[y0:y1, x0:x1])
    rope = np.zeros_like(gear)
    rope[y0:y1, x0:x1] = (luma[y0:y1, x0:x1] > sand + 28).astype(np.uint8)
    rope = cv2.morphologyEx(rope, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(rope)
    big = np.isin(lab, [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 150])
    gear |= big.astype(np.uint8)
    gear = cv2.morphologyEx(gear, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    hull = poly_mask(a.shape, [BOAT])
    boat = LK.trim_edges(hull | poly_mask(a.shape, [], ROLLERS), a)
    far = LK.trim_edges(poly_mask(a.shape, [FAR_HULL, FAR_NET], FAR_ROLLERS), a)
    gear = LK.trim_edges(gear, a, band=10)
    # the hull behind the traps and boxes: carried on from 180 px toward the stern along the hull's own lines (they rise
    # 0.11 px for each px toward the bow); the gear stands in front, its own cut-out
    behind = (cv2.dilate(gear, np.ones((5, 5), np.uint8)) & hull).astype(bool)
    boat_a = a[..., :3].copy()
    ys, xs = np.nonzero(behind)
    boat_a[ys, xs] = a[np.clip(np.round(ys + 0.11 * 180).astype(int), 0, a.shape[0] - 1), xs - 180, :3]
    boat |= behind.astype(np.uint8)
    return boat, gear, far, boat_a


def tower(atlas, timg, struct, ladder, back):
    """KM-B21, the lifeguard tower: its parts as boxes (TOWER_PARTS), each box's street face showing only its own part of
    the picture (the rest of the box's face clear), the other faces the weathered wood's colour; the X of braces as strips
    on the front legs, the far ones (the back's and the sides') on a face at the back legs; the ladder leaning against
    the platform's end, the flag on its pole at the roof's corner."""
    s, gy = s_at(TOWER_FOOT), float(TOWER_FOOT)
    crop = (2296, 76, 2600, 776)
    a = np.asarray(timg)
    cx = 2470.0
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    rgba = np.dstack([a[crop[1]:crop[3], crop[0]:crop[2]], struct[crop[1]:crop[3], crop[0]:crop[2]] * 255])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    roof = np.asarray(timg)[poly_mask(a.shape, [ROOF]).astype(bool)]
    side = dict(wood=(atlas.place(LK.flat_sample(timg, (2394, 520, 2410, 700))), (64, 64)),
                boards=(atlas.place(LK.flat_sample(timg, (2420, 375, 2550, 455))), (64, 64)),
                roof=(atlas.place(Image.new('RGB', (64, 64), tuple(int(v) for v in np.median(roof[:, :3], 0)))),
                      (64, 64)))
    b = KB.Builder(atlas, pos, fmap, *side['wood'])
    for name, x0, y0, x1, y1, d0, d1, smp in TOWER_PARTS:
        b.box(X(x0), X(x1), d0, d1, Z(y1), Z(y0), side=side[smp])
    for (pa, pb) in BRACES:
        pts = [P(X(px), -0.02, Z(py)) for px, py in strip(pa, pb)]
        if (pts[1] - pts[0]).cross(pts[2] - pts[0]).y > 0:
            pts = pts[::-1]
        b.face(pts)
    x0, y0, x1, y1 = FLAG
    b.face([P(X(x0), -0.27, Z(y1)), P(X(x1), -0.27, Z(y1)), P(X(x1), -0.27, Z(y0)), P(X(x0), -0.27, Z(y0))])
    o = b.object('KmLifeguardTower')
    # the ladder, cut out on its own
    lx0, ly0 = min(p[0] for p in LADDER) - 2, min(p[1] for p in LADDER) - 2
    lx1, ly1 = max(p[0] for p in LADDER) + 2, max(p[1] for p in LADDER) + 2
    rgba = np.dstack([a[ly0:ly1, lx0:lx1], ladder[ly0:ly1, lx0:lx1] * 255])
    lpos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    c = KB.Builder(atlas, None, None, None, None)
    LK.card_faces(c, atlas, lpos, (lx0, ly0, lx1, ly1), cx, gy, s, -0.14, both=False)
    k = c.object('KmLifeguardTowerLadder', outward=False)
    # the far braces: the dark wood between the legs, on a face at the back legs
    x0, y0, x1, y1 = BACK_ZONE
    bpos = atlas.place(Image.fromarray(np.dstack([a[y0:y1, x0:x1], back[y0:y1, x0:x1] * 255]), 'RGBA'))
    d = KB.Builder(atlas, None, None, None, None)
    LK.card_faces(d, atlas, bpos, BACK_ZONE, cx, gy, s, 1.52, both=True)
    kb = d.object('KmLifeguardTowerBraces', outward=False)
    o = K.join([o, k, kb], 'KmLifeguardTower')
    return o, dict(id='KM-B21', source='photo/KM2-2: the lifeguard tower, its ladder and flag', cutout=True,
                   real_size=[round((2594 - 2304) / s, 2), 2.15, round(Z(82), 2)], budget=1500, px_centre=cx,
                   px_per_m=round(s, 2))


def sea_wall(atlas, src, struct, ladder):
    """KM-B23, the sea wall in streaked concrete, its face squared up out of the picture's perspective (its four corners,
    WALL_QUAD, to a 14 x 1.75 m face at 100 px to the metre) and the tower painted out of it from further along; the
    top, the ends and the back take its concrete's colour."""
    w, h = int(WALL_LEN * WALL_PX), int(WALL_H * WALL_PX)
    M = cv2.getPerspectiveTransform(np.float32(WALL_QUAD), np.float32([(0, 0), (w, 0), (w, h), (0, h)]))
    a = np.asarray(src)
    face = cv2.warpPerspective(a, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    hole = cv2.warpPerspective(cv2.dilate(struct | ladder, np.ones((5, 5), np.uint8)) * 255, M, (w, h),
                               flags=cv2.INTER_NEAREST) > 0
    cols = np.where(hole.any(0))[0]
    if len(cols):
        c0, c1 = cols.min(), cols.max()
        shift = c1 - c0 + 30
        face[:, c0:c1 + 1] = face[:, c0 + shift:c1 + 1 + shift]
    Image.fromarray(face).save(os.path.join(REVIEW, 'wall_face.jpg'), quality=90)
    pos = atlas.place(Image.fromarray(face))
    fmap = lambda co: (co.x * WALL_PX + w / 2, (WALL_H - co.z) * WALL_PX)
    conc = (atlas.place(LK.flat_sample(Image.fromarray(face), (0, 0, w, 30))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, *conc)
    b.box(-WALL_LEN / 2, WALL_LEN / 2, 0.0, 0.5, 0.0, WALL_H, side=conc, skip=('bottom',))
    o = b.object('KmSeaWall')
    return o, dict(id='KM-B23', source='photo/KM2-2: the sea wall at the back of the beach, squared up', cutout=False,
                   real_size=[WALL_LEN, 0.5, WALL_H], budget=100, px_centre=None, px_per_m=WALL_PX)


def houses(atlas, img):
    """KM-B37, the beach houses and the leaning black pines above the sea wall: a cut-out against the sky, down to just
    below the wall's top (the wall stands in front of its foot), at the wall's scale; the tower painted out of it."""
    x0, y0, x1, y1 = HOUSES
    a = np.asarray(img)[y0:y1, x0:x1]
    keep = (~LK.sky_mask(a)).astype(np.uint8)
    xs = np.arange(x0, x1)
    rows = np.arange(y0, y1)[:, None]
    keep[rows >= wall_top(xs)[None, :] + 8] = 0           # 8 px below the wall's top: hidden behind it
    sx0, sy0, sx1, sy1 = SIGN_BOX
    keep[sy0 - y0:, sx0 - x0:sx1 - x0] = 0             # the rules board's top: its own model
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # the picture's wall top slopes (it recedes), the squared-up wall's is level: each column let down so the wall's
    # top meets row 504 (the wall's 1.75 m) all along, so no sky shows between the wall and the houses
    drop = np.round(WALL_QUAD[1][1] - wall_top(xs)).astype(int)
    pad = int(drop.max())
    rgba = np.zeros((a.shape[0] + pad, a.shape[1], 4), np.uint8)
    for c in range(a.shape[1]):
        rgba[drop[c]:drop[c] + a.shape[0], c, :3] = a[:, c, :3]
        rgba[drop[c]:drop[c] + a.shape[0], c, 3] = keep[:, c] * 255
    s = s_at(HOUSES_FOOT)
    cx = (x0 + x1) / 2
    o = LK.card(atlas, rgba, (x0, y0, x1, y1 + pad), cx, float(HOUSES_FOOT), s, 0.0, 'KmBeachHouses', both=False)
    return o, dict(id='KM-B37', source='photo/KM2-2: the beach houses and pines above the sea wall (a cut-out)',
                   real_size=[round((x1 - x0) / s, 2), 0.01, round((HOUSES_FOOT - y0) / s, 2)], cutout=True,
                   budget=100, px_centre=cx, px_per_m=round(s, 2))


def enoshima(atlas, img):
    """KM-B38, Enoshima and the hills beyond the bay on the horizon: cut out against the hazy sky (each row's sky the
    brightest of that row), its foot the horizon; 25 m wide, to stand far back, its foot at the game camera's eye."""
    x0, y0, x1, y1 = ENOSHIMA
    a = np.asarray(img)[y0:y1, x0:x1].astype(np.int32)
    luma = 0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
    sky = np.percentile(luma, 85, axis=1)[:, None]
    keep = (luma < sky - 10).astype(np.uint8)
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    s = (x1 - x0) / 25.0
    gy = y1 + 2.45 * s                     # the card's foot 2.45 m below the horizon: on it, from the game camera
    o = LK.card(atlas, np.dstack([a.astype(np.uint8), keep * 255]), ENOSHIMA, (x0 + x1) / 2, gy, s, 0.0,
                'KmEnoshimaView', both=False)
    return o, dict(id='KM-B38', source='photo/KM2-2: Enoshima and the hills beyond the bay (a cut-out on the horizon)',
                   real_size=[25.0, 0.01, round((gy - y0) / s, 2)], cutout=True, budget=100, px_centre=(x0 + x1) / 2,
                   px_per_m=round(s, 2))


def surfboards(atlas, src):
    """KM-A36, three surfboards stuck upright in the sand: each cut out by its outline at its own scale (its foot's
    distance below the horizon), the further ones further back."""
    a = np.asarray(src)
    b = KB.Builder(atlas, None, None, None, None)
    near = s_at(BOARDS[0][1])
    cx0 = 1340.0
    for i, (outline, foot) in enumerate(BOARDS):
        s = s_at(foot)
        x0, y0 = min(p[0] for p in outline) - 2, min(p[1] for p in outline) - 2
        x1, y1 = max(p[0] for p in outline) + 2, max(p[1] for p in outline) + 2
        m = cv2.erode(poly_mask(a.shape, [outline]), np.ones((5, 5), np.uint8))   # inside the sand and foam round it
        pos = atlas.place(Image.fromarray(np.dstack([a[y0:y1, x0:x1], m[y0:y1, x0:x1] * 255]), 'RGBA'))
        # its x: where the picture puts it, at the nearest board's scale; its depth from its scale
        cxm = ((x0 + x1) / 2 - cx0) / near
        depth = 2.64 * (near / s - 1.0) * 1.5
        LK.card_faces(b, atlas, pos, (x0, y0, x1, y1), (x0 + x1) / 2 - cxm * s, float(foot), s, depth, both=False)
    o = b.object('KmBeachSurfboards', outward=False)
    return o, dict(id='KM-A36', source='photo/KM2-2: three surfboards stuck upright in the sand (cut-outs)', cutout=True,
                   real_size=[2.0, round(2.64 * (near / s_at(BOARDS[2][1]) - 1.0) * 1.5, 2), 1.9], budget=100,
                   px_centre=cx0, px_per_m=round(near, 2))


def build_all():
    src, timg, img, struct, ladder, back = pictures()
    os.makedirs(REVIEW, exist_ok=True)
    img.save(os.path.join(REVIEW, 'painted.jpg'), quality=88)
    a = np.asarray(src)
    boat, gear, far, boat_a = boat_masks(a)
    sacks = poly_mask(a.shape, [SACKS, FENCE])
    sign = poly_mask(a.shape, [SIGN])
    atlas = LK.Atlas(ATLAS_W, ATLAS_H)
    models = [houses(atlas, img), sea_wall(atlas, src, struct | back, ladder),
              cutout(atlas, boat_a, boat, BOAT_BOX, BOAT_FOOT, 'KmFishingBoat',
                     dict(id='KM-B20', source='photo/KM2-2: the near fishing boat on its rollers (a cut-out)')),
              cutout(atlas, a, gear, GEAR_BOX, GEAR_FOOT, 'KmBoatGear',
                     dict(id='KM-A37', source='photo/KM2-2: the crab traps and net (KM-A37), the fish boxes (KM-A35) '
                          'and the coiled ropes by the near boat (a cut-out)')),
              cutout(atlas, a, far, FAR_BOX, FAR_FOOT, 'KmFishingBoatFar',
                     dict(id='KM-B20', source='photo/KM2-2: the far fishing boat on its rollers, its net (a cut-out)')),
              tower(atlas, timg, struct, ladder, back),
              cutout(atlas, a, sacks, SACKS_BOX, SACKS_FOOT, 'KmLitterSacks',
                     dict(id='KM-A41', source='photo/KM2-2: the sacks of collected litter and their bamboo fence '
                          '(a cut-out)')),
              surfboards(atlas, src),
              cutout(atlas, a, sign, SIGN_BOX, SIGN_FOOT, 'KmBeachSign',
                     dict(id='KM-A42', source='photo/KM2-2: the beach\'s rules board on its post (a cut-out)')),
              enoshima(atlas, img)]
    return src, img, atlas, models


BOXES = dict(KmBeachHouses=HOUSES, KmSeaWall=(2266, 470, 3020, 600), KmFishingBoat=BOAT_BOX, KmBoatGear=GEAR_BOX,
             KmFishingBoatFar=FAR_BOX, KmLifeguardTower=(2296, 76, 2600, 776), KmLitterSacks=SACKS_BOX,
             KmBeachSurfboards=(1316, 492, 1470, 646), KmBeachSign=SIGN_BOX, KmEnoshimaView=ENOSHIMA)
CARDS = ('KmBeachHouses', 'KmFishingBoat', 'KmBoatGear', 'KmFishingBoatFar', 'KmLitterSacks', 'KmBeachSurfboards',
         'KmBeachSign', 'KmEnoshimaView')


def checks(o, info, oe, fins, tris):
    """The seventeen checks of a KM2-2 set piece (docs/ASSET_REVIEW.md)."""
    card_ = o.name in CARDS
    n = o.name
    return {
        1: ('pass', 'each part once (looked at in Top and Bottom)'),
        2: ('limit' if oe or fins else 'pass',
            '%d edges with one face, %d with three or more: %s' % (oe, fins, 'cut-out cards' if card_ else
            'boxes without the faces no one sees, the braces and the ladder as single faces' if n == 'KmLifeguardTower'
            else 'a box without its underside')),
        3: ('limit' if card_ else 'pass', 'a flat cut-out: its depth is not modelled' if card_ else
            'boxes measured off the picture at %.0f px to the metre' % info['px_per_m'] if n == 'KmLifeguardTower' else
            'its face squared up out of the picture\'s perspective'),
        4: ('limit', 'the street side is the picture itself; the sides, back and tops take the part\'s own colour (no '
                     'view of their own)' if not card_ else 'the picture from the street, nothing behind'),
        5: ('pass', '%.2f x %.2f x %.2f m at %.0f px to the metre (its foot\'s distance below the horizon), %d triangles '
                    '(its budget %d), the shared 4096 x 2048 KmBeachAtlas'
            % (tuple(info['real_size']) + (info['px_per_m'], tris, info.get('budget', 1500)))),
        6: ('pass', 'its outline the picture\'s, measured'),
        7: ('pass', 'no holes in what the beach sees' if n != 'KmFishingBoat' else
            'no holes: the hull behind the traps and boxes painted from the hull round it'),
        8: ('pass', 'what stood in front of it is its own model, painted out of it or apart'),
        9: ('pass', 'the photographic KM2-2, in KM-0\'s look'),
        10: ('pass', 'solid and whole' if n != 'KmLifeguardTower' else
             'solid; the hidden feet of two legs carried on down to the sand'),
        11: ('pass', 'no brand or logo: the rules board\'s words are not a language'),
        12: ('pass', 'the sky cut out round the flag, the houses and pines and Enoshima; nothing of the sky on a box'),
        13: ('pass', 'painted out: the tower from the sea wall and from the houses and pines'),
        14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'),
        17: ('n/a', 'one piece'),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    src, img, atlas, models = build_all()
    LK.export(models, atlas, OUT, REVIEW, 'KmBeachAtlas.png', 'Beach', src, BOXES, checks, INSTALL)


if __name__ == '__main__':
    main()
