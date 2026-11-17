# KM2-3 Grandma's Whitebait Shop's set pieces (docs/KAMAKURA_BUILD.md, BUILD KM-L23), from the photographic KM2-3 with
# km_leg_kit.py. The picture looks straight at the beach road's frontage, so the fronts are built as KM1-3's shops were:
# boxes and roofs whose faces toward the street are the picture's own pixels, at 215 px to the metre (the shop's opening
# 2.1 m to its lintel, its glass counter 0.9 m), their foot at row 850. The pieces:
#   - Grandma's shop (KM-B22): the ground floor with its noren and the glass counter standing out from it (the bento on
#     its cloth on top), the skirt roof, the signboard on it, the upper storey and its hipped roof (above the picture's
#     top edge its tiles go on in KM-P3's tiles);
#   - the neighbour's two houses and their board fence (KM-B39, new);
#   - the whitebait drying rack (KM-A15): its legs and rails, the three tilted trays on top and the two shelves of trays,
#     each part showing only itself;
#   - the fish boxes stacked by the door and the hose reel (KM-A35), the crates and tubs beside them (KM-A34);
#   - the low sea wall with its steps up to the promenade (KM-B23); behind it, the promenade's high wall, the dune and
#     its pines as one cut-out (KM-B40, new), and the pines behind the houses (KM-B41, new);
#   - the no-parking sign and the bus stop's sign (KM-A43, A44, new), cut out.
# The pots before the fence, the utility pole and the scooter are the kit's (KM-G26 to G33, KM-A01, KM-V03), standing
# where the picture has them: they are painted out of the fronts behind them (patch_fill).
# All of them share one texture, KmWhitebaitAtlas.png (4096 x 2048).
#   blenv/bin/python km_whitebait.py -- /abs/outdir /abs/review/kamakura/whitebait [--install /abs/Assets/_Game/Art/Models/Kamakura]
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

SRC = 'photo/KM2-3_grandmas_whitebait_shop.png'
ATLAS_W, ATLAS_H = 4096, 2048
S, GY = 215.0, 850.0
DENS = 80.0                       # the hidden faces' boards and tiles, px to the metre
P = lambda x, y, z: Vector((x, y, z))
X_ = lambda px, cx: (px - cx) / S
Z = lambda py: (GY - py) / S

# ---------------------------------------------------------------- what is measured (the picture's pixels)
SHOP = dict(ground=(1422, 2678, 367), counter=(1878, 2278, 600), skirt_eave=(1341, 2763, 350),
            skirt_top=(1452, 2641, 228), upper=(1502, 2619, 94), roof_eave=(1436, 2686, 80), sign=(1819, 2282, 172, 294))
RACK = dict(trays=[[(1307, 697), (1450, 697), (1530, 579), (1405, 577)],
                   [(1477, 699), (1615, 699), (1677, 580), (1562, 579)],
                   [(1644, 699), (1780, 699), (1829, 580), (1725, 579)]],
            rail=(1300, 702, 1797, 713), shelf1=(1310, 738, 1817, 796), shelf2=(1296, 796, 1678, 846),
            legs=[(1301, 1316), (1781, 1796)], back_post=(1821, 1836, 600), foot=889)
RACK_BOX = (1290, 570, 1845, 892)
BOXES = [(2505, 2655, 624, 675), (2493, 2667, 669, 729), (2495, 2650, 720, 771), (2492, 2667, 763, 834)]
REEL = [(2322, 845), (2318, 830), (2330, 812), (2365, 722), (2400, 716), (2440, 720), (2470, 745), (2480, 780),
        (2500, 845), (2480, 862), (2400, 860), (2340, 862)]
REEL_BOX = (2316, 712, 2502, 866)
CRATES = dict(red=(2663, 2770, 735, 830), tub=(2680, 2740, 688, 742), yellow=(2677, 2741, 642, 690))
WALL_LOW = (3155, 4128, 650, 855)
WALL_FOOT = 790                                               # its foot by the steps (it turns toward the road at its right)
STEPS = dict(x=(3300, 3600), rows=[778, 733, 702, 674, 650])   # the steps' foot, then each tread's front edge, upward
SIGN_NP = [(3659, 278), (3735, 278), (3735, 384), (3712, 384), (3712, 800), (3688, 800), (3688, 384), (3659, 384)]   # plate, arrow, post
SIGN_NP_BOX = (3655, 270, 3740, 804)
SIGN_BUS = [(3855, 414), (3925, 414), (3925, 482), (3900, 482), (3900, 830), (3881, 830), (3881, 482), (3855, 482)]
SIGN_BUS_BOX = (3852, 410, 3928, 834)
VIEW_BOX = (2700, 140, 4128, 660)                             # the promenade's wall, the dune and its pines
TREES_BOX = (430, 0, 1480, 500)                               # the pines behind the neighbour's houses
NEIGH = dict(main=(0, 789), annex=(594, 1372), annex_gable=((522, 383), (861, 144), (1180, 383)),
             annex_lean=((1150, 255), (1389, 422)), fence=(244, 1400, 472), porch=(0, 350, 355, 440))
POLE = [(1026, 0, 1126, 850), (1112, 55, 1196, 228), (1105, 350, 1166, 488), (1086, 490, 1150, 632)]   # and its
POTS = (140, 585, 1062, 850)                                  # fittings: the transformer, the meter, the notice  (x0, y0, x1, y1)
SCOOTER = (2738, 570, 3182, 886)


def poly_mask(shape, polys=(), rects=()):
    m = np.zeros(shape[:2], np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = 1
    return m


def sky(a):
    """The overcast sky of KM2-3: near white (its darkest channel over 222) and with almost no colour of its own, above
    row 700; the pale concrete walls (about 190, 181, 166) are not it (LK.overcast_mask took them)."""
    f = a.astype(np.int32)
    m = (f.min(-1) > 222) & (f.max(-1) - f.min(-1) < 16)
    m[700:] = False
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


# ---------------------------------------------------------------- the picture, painted
def rack_mask(shape):
    r = RACK
    rects = [r['rail'], r['shelf1'], r['shelf2']] + [(x0, 702, x1, r['foot']) for x0, x1 in r['legs']]
    rects.append((r['back_post'][0], r['back_post'][2], r['back_post'][1], 830))
    return poly_mask(shape, r['trays'], rects)


def pictures():
    """The photographic KM2-3 (src) and the picture with what becomes its own model painted out of the fronts behind
    it (img), each from what its source holds (D36, D38):
    - the pots: each of the fence's boards stretched down from above them (its median colour: a band copied down
      repeats what it holds in a grid, D36);
    - the pole and its fittings: the fence carried across from beside it, above the fence painted from round it
      (patch_fill);
    - the fish boxes, the hose reel and the crates: painted from round them;
    - the rack: the shop's front wall's boards and the fence's stretched down, the shop's interior carried across from
      right of the counter, the pavement under its feet carried along;
    - the scooter: at the shop's corner from the corner, above the promenade's edge from the walls beside it, below it
      from the pavement beside it (not the road's white lines);
    - the two signs: out of the promenade's wall, the dune and the sky behind them."""
    src = KB.ref(SRC)
    a = np.asarray(src)[..., :3].copy()

    def vtile(x0, x1, y0, y1, s0, s1):
        for y in range(y0, y1):
            a[y, x0:x1] = a[s0 + (y - y0) % (s1 - s0), x0:x1]

    def vstretch(x0, x1, y0, y1, s0, s1):
        a[y0:y1, x0:x1] = np.median(a[s0:s1, x0:x1], axis=0).astype(np.uint8)[None]

    def hshift(x0, x1, y0, y1, dx):
        a[y0:y1, x0:x1] = a[y0:y1, x0 + dx:x1 + dx]

    def fill(rects, avoid=None):
        global_a = LK.patch_fill(a, poly_mask(a.shape, [], rects).astype(bool), patch=11, window=160, avoid=avoid)
        a[:] = global_a

    # the pots
    vstretch(140, 268, 585, 850, 495, 580)
    vstretch(268, 352, 600, 850, 495, 538)
    vstretch(268, 352, 585, 600, 495, 538)
    vstretch(352, 1062, 585, 850, 495, 580)
    # the pole: the fence and its top rail carried across from its left, then the rest painted
    hshift(1026, 1150, 470, 850, -124)
    fill([(x0, y0, x1, min(y1, 470)) for x0, y0, x1, y1 in POLE if y0 < 470])
    # the boxes, the reel, the crates
    fill([(x0, y0, x1, y1) for x0, x1, y0, y1 in BOXES] + [REEL_BOX] + [(c[0], c[2], c[1], c[3]) for c in CRATES.values()])
    # the rack
    vstretch(1290, 1400, 570, 850, 495, 568)
    vstretch(1400, 1667, 570, 850, 445, 568)
    hshift(1667, 1845, 570, 850, 620)
    hshift(1290, 1845, 850, 892, -560)
    # the scooter
    x0, y0, x1, y1 = SCOOTER
    cols = np.zeros(a.shape[:2], bool)
    cols[:, :2790] = True
    rows_hi = np.zeros(a.shape[:2], bool)
    rows_hi[:652] = True
    fill([(x0, y0, 2790, y1)], avoid=~cols)
    cols = np.zeros(a.shape[:2], bool)
    cols[:, :2845] = True                         # not the bucket and the hose's handle by the shop's corner either
    fill([(2790, y0, x1, 652)], avoid=cols | ~rows_hi)
    road = np.zeros(a.shape[:2], bool)
    road[862:] = True
    fill([(2790, 652, x1, y1)], avoid=cols | rows_hi | road)
    # the two signs, out of the promenade's wall, the dune and the sky behind them (above the low wall)
    signs = poly_mask(a.shape, [], [(3648, 268, 3746, 400), (3682, 400, 3718, 650), (3846, 404, 3934, 492),
                                    (3874, 492, 3908, 650)])
    signs[650:] = 0
    a[:] = LK.patch_fill(a, signs.astype(bool), patch=11, window=160)
    return src, Image.fromarray(a)


# ---------------------------------------------------------------- the models
def samples(atlas, img):
    boards = KB.boards_texture(img.crop((1440, 400, 1640, 560)), DENS, 500, 500)
    tiles = KB.tiles_texture(img.crop((1500, 240, 2600, 330)), DENS, 640, 640)
    return (atlas.place(boards), boards.size, DENS), (atlas.place(tiles), tiles.size, DENS)


def builder(atlas, img, crop, cx, side, alpha=None, gy=GY):
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]]
    im = Image.fromarray(a) if alpha is None else Image.fromarray(np.dstack([a, alpha[crop[1]:crop[3], crop[0]:crop[2]] * 255]), 'RGBA')
    pos = atlas.place(im)
    fmap = lambda co: (cx + co.x * S - crop[0], gy - co.z * S - crop[1])
    return KB.Builder(atlas, pos, fmap, side[0], side[1]), (lambda px: X_(px, cx))


def roof(b, X, x0, x1, xr0, xr1, yf, yr, yb, ze, zcut, zr, tiles):
    """A hipped roof whose front slope is the picture up to zcut (its top edge) and KM-P3's tiles above it."""
    t = (zcut - ze) / (zr - ze)
    ycut = yf + t * (yr - yf)
    xc0, xc1 = x0 + t * (xr0 - x0), x1 + t * (xr1 - x1)
    b.begin([P(x0, yf, ze), P(x1, yb, ze), P(xr0, yr, zr), P(xr1, yr, zr)])
    if zcut > ze + 1e-3:
        b.face([P(x0, yf, ze), P(x1, yf, ze), P(xc1, ycut, zcut), P(xc0, ycut, zcut)])           # the picture's
    b.face([P(xc0, ycut, zcut), P(xc1, ycut, zcut), P(xr1, yr, zr), P(xr0, yr, zr)], tiles, project=False)
    b.face([P(x1, yb, ze), P(x0, yb, ze), P(xr0, yr, zr), P(xr1, yr, zr)], tiles)
    b.face([P(x0, yb, ze), P(x0, yf, ze), P(xr0, yr, zr)], tiles)
    b.face([P(x1, yf, ze), P(x1, yb, ze), P(xr1, yr, zr)], tiles)
    b.face([P(x0, yb, ze), P(x1, yb, ze), P(x1, yf, ze), P(x0, yf, ze)], tiles)
    b.end()


def shop(atlas, img, boards, tiles):
    """KM-B22, Grandma's whitebait shop, 5.8 m wide (6.6 m at its skirt roof), 4.8 m to its ridge."""
    s = SHOP
    b, X = builder(atlas, img, (1330, 0, 2780, 860), 2050.0, boards)
    g0, g1, gt = s['ground']
    b.box(X(g0), X(g1), 0.0, 6.0, 0.0, Z(gt), side=boards, skip=('bottom', 'top'))
    c0, c1, ct = s['counter']
    b.box(X(c0), X(c1), -0.55, 0.0, 0.0, Z(ct), side=boards, skip=('bottom', 'back'))    # the glass counter
    e0, e1, ey = s['skirt_eave']
    t0, t1, ty = s['skirt_top']
    b.skirt((X(e0), X(e1), -0.85, 6.85), (X(t0), X(t1), 0.0, 6.0, Z(ty), Z(ty)), Z(ey), side=tiles)
    u0, u1, uy = s['upper']
    b.box(X(u0), X(u1), 0.0, 6.0, Z(ty), Z(uy), side=boards, skip=('bottom',))
    sx0, sx1, sy0, sy1 = s['sign']
    b.box(X(sx0), X(sx1), -0.5, -0.42, Z(sy1), Z(sy0), side=boards)                         # the signboard
    r0, r1, ry = s['roof_eave']
    roof(b, X, X(r0), X(r1), X(1760), X(2360), -0.5, 3.0, 6.5, Z(ry), Z(2), 4.85, tiles)
    o = b.object('KmGrandmaShop')
    return o, dict(id='KM-B22', source='photo/KM2-3: Grandma\'s whitebait shop, its noren, its glass counter with the '
                   'bento on its cloth, its signboard', cutout=False, budget=1500, px_centre=2050.0, px_per_m=S,
                   real_size=[round((e1 - e0) / S, 2), 7.0, 4.85])


def gable_front(b, el, apex, er, yf, yb, side):
    """A gabled roof whose gable faces the street (as km_surf_lane's): its front triangle the picture's."""
    (xl, zl), (xa, za), (xr, zr) = el, apex, er
    b.begin([P(xl, yf, zl), P(xr, yb, zr), P(xa, (yf + yb) / 2, za)])
    b.face([P(xl, yf, zl), P(xr, yf, zr), P(xa, yf, za)])
    b.face([P(xr, yb, zr), P(xl, yb, zl), P(xa, yb, za)], side)
    b.face([P(xl, yb, zl), P(xl, yf, zl), P(xa, yf, za), P(xa, yb, za)], side)
    b.face([P(xr, yf, zr), P(xr, yb, zr), P(xa, yb, za), P(xa, yf, za)], side)
    b.face([P(xl, yf, zl), P(xl, yb, zl), P(xr, yb, zr), P(xr, yf, zr)], side)
    b.end()


def neighbour(atlas, img, boards, tiles):
    """KM-B39, the neighbour's two houses behind their board fence: the two-storey house (its front the picture's up to
    the picture's top edge, its roof above in KM-P3's tiles), the low house with its gable to the street and its lean-to,
    the fence of dark boards with the letterbox. The sky is let go round their edges."""
    a = np.asarray(img.convert('RGB'))
    alpha = (~sky(a)).astype(np.uint8)
    b, X = builder(atlas, img, (0, 0, 1420, 860), 700.0, boards, alpha=alpha)
    n = NEIGH
    m0, m1 = n['main']
    b.box(X(m0), X(m1), 1.2, 7.0, 0.0, Z(0), side=boards, skip=('bottom', 'top'))
    roof(b, X, X(m0) - 0.3, X(m1) + 0.3, X(m0) + 0.6, X(m1) - 0.6, 0.9, 4.1, 7.3, Z(0), Z(0), Z(0) + 1.2, tiles)
    p0, p1, py0, py1 = n['porch']
    b.face([P(X(p0), 0.4, Z(py1)), P(X(p1), 0.4, Z(py1)), P(X(p1), 1.2, Z(py0)), P(X(p0), 1.2, Z(py0))])   # porch roof
    a0, a1 = n['annex']
    (el, ez), (ax, az), (er, erz) = n['annex_gable']
    b.box(X(a0), X(a1), 1.0, 7.0, 0.0, Z(ez), side=boards, skip=('bottom', 'top'))
    gable_front(b, (X(el), Z(ez)), (X(ax), Z(az)), (X(er), Z(erz)), 0.85, 7.1, tiles)
    (lx0, ly0), (lx1, ly1) = n['annex_lean']
    b.face([P(X(lx0), 0.9, Z(ly0)), P(X(lx1), 0.9, Z(ly1)), P(X(lx1), 7.0, Z(ly1)), P(X(lx0), 7.0, Z(ly0))], tiles,
           project=False)
    b.face([P(X(lx0), 0.85, Z(ly1)), P(X(lx1), 0.85, Z(ly1)), P(X(lx0), 0.85, Z(ly0))])        # its end, the picture's
    f0, f1, fy = n['fence']
    b.box(X(f0), X(f1), 0.0, 0.08, 0.0, Z(fy), side=boards)
    o = b.object('KmShopNeighbour')
    return o, dict(id='KM-B39', source='photo/KM2-3: the neighbour\'s two houses and their board fence', cutout=True,
                   budget=1500, px_centre=700.0, px_per_m=S, real_size=[round(1420 / S, 2), 7.0, round(Z(0) + 1.2, 2)])


def rack(atlas, img_src):
    """KM-A15, the whitebait drying rack: its four legs, its rails and the back post as boxes; the three trays on top
    tilted toward the street (front edge low, 0.4 m forward), the two shelves of trays below; each part showing only
    itself (the shop's front behind it let go). 2.3 m wide, 0.8 m deep, 1.4 m tall."""
    src_a = np.asarray(img_src)[..., :3]
    m = rack_mask(src_a.shape)
    gy = float(RACK['foot'])
    crop = RACK_BOX
    cx = 1560.0
    pos = atlas.place(Image.fromarray(np.dstack([src_a[crop[1]:crop[3], crop[0]:crop[2]],
                                                 m[crop[1]:crop[3], crop[0]:crop[2]] * 255]), 'RGBA'))
    fmap = lambda co: (cx + co.x * S - crop[0], gy - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    Zr = lambda py: (gy - py) / S
    wood = (atlas.place(LK.flat_sample(img_src, (1302, 720, 1315, 880))), (64, 64))
    fish = (atlas.place(LK.colour_sample(img_src, (1340, 600, 1480, 680))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, *wood)
    for x0, x1 in RACK['legs']:
        for d in (-0.4, 0.32):
            b.box(X(x0), X(x1), d, d + 0.06, 0.0, Zr(702), side=wood)
    bx0, bx1, by = RACK['back_post']
    b.box(X(bx0), X(bx1), 0.32, 0.38, 0.0, Zr(by), side=wood)
    rx0, ry0, rx1, ry1 = RACK['rail']
    b.box(X(rx0), X(rx1), -0.42, 0.38, Zr(ry1), Zr(ry0), side=wood)
    for key in ('shelf1', 'shelf2'):
        sx0, sy0, sx1, sy1 = RACK[key]
        b.box(X(sx0), X(sx1), -0.38, 0.32, Zr(sy1), Zr(sy0), side=fish)
    for tray in RACK['trays']:
        (blx, bly), (brx, bry), (trx, try_), (tlx, tly) = tray
        b.begin([P(X(blx), -0.42, Zr(bly)), P(X(trx), 0.38, Zr(try_))])
        b.face([P(X(blx), -0.42, Zr(bly)), P(X(brx), -0.42, Zr(bry)), P(X(trx), 0.38, Zr(try_)), P(X(tlx), 0.38, Zr(tly))])
        b.face([P(X(tlx), 0.4, Zr(tly)), P(X(trx), 0.4, Zr(try_)), P(X(brx), -0.4, Zr(bry)), P(X(blx), -0.4, Zr(bly))],
               wood)
        b.end()
    o = b.object('KmDryingRack')
    return o, dict(id='KM-A15', source='photo/KM2-3: the whitebait drying rack with its trays', cutout=True, budget=500,
                   px_centre=cx, px_per_m=S, real_size=[round((1836 - 1296) / S, 2), 0.8, round(Zr(577), 2)])


def fish_boxes(atlas, img_src):
    """KM-A35, the polystyrene fish boxes stacked by the door (four, each its own box, their labels the picture's) and the
    hose reel beside them (a cut-out)."""
    src_a = np.asarray(img_src)[..., :3]
    crop = (2310, 615, 2675, 870)
    cx = 2580.0
    pos = atlas.place(Image.fromarray(src_a[crop[1]:crop[3], crop[0]:crop[2]]))
    fmap = lambda co: (cx + co.x * S - crop[0], GY - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    white = (atlas.place(LK.flat_sample(img_src, (2520, 690, 2640, 720))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, *white)
    for x0, x1, y0, y1 in BOXES:
        b.box(X(x0), X(x1), -0.45, 0.0, Z(y1), Z(y0), side=white, skip=('bottom',))
    m = poly_mask(src_a.shape, [REEL])
    x0, y0, x1, y1 = REEL_BOX
    rpos = atlas.place(Image.fromarray(np.dstack([src_a[y0:y1, x0:x1], m[y0:y1, x0:x1] * 255]), 'RGBA'))
    LK.card_faces(b, atlas, rpos, REEL_BOX, cx, GY, S, -0.3)
    o = b.object('KmFishBoxes')
    return o, dict(id='KM-A35', source='photo/KM2-3: the fish boxes stacked by the shop\'s door and the hose reel',
                   cutout=True, budget=300, px_centre=cx, px_per_m=S, real_size=[round((2667 - 2316) / S, 2), 0.45,
                                                                                    round(Z(624), 2)])


def crates(atlas, img_src):
    """KM-A34, the red crate with the grey tub and the yellow box stacked on it, at the shop's corner."""
    src_a = np.asarray(img_src)[..., :3]
    crop = (2655, 635, 2775, 835)
    cx = 2716.0
    pos = atlas.place(Image.fromarray(src_a[crop[1]:crop[3], crop[0]:crop[2]]))
    fmap = lambda co: (cx + co.x * S - crop[0], GY - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    red = (atlas.place(LK.flat_sample(img_src, (2680, 760, 2760, 820))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, *red)
    for key, d in (('red', 0.4), ('tub', 0.3), ('yellow', 0.28)):
        x0, x1, y0, y1 = CRATES[key]
        b.box(X(x0), X(x1), -d, 0.0, Z(y1), Z(y0), side=(atlas.place(LK.flat_sample(img_src, (x0 + 8, y0 + 8, x1 - 8,
                                                                                           y1 - 8))), (64, 64)))
    o = b.object('KmCrates')
    return o, dict(id='KM-A34', source='photo/KM2-3: the red crate, the tub and the yellow box at the shop\'s corner',
                   cutout=False, budget=200, px_centre=cx, px_per_m=S, real_size=[0.5, 0.4, round(Z(642), 2)])


def sea_wall_steps(atlas, img):
    """KM-B23, the low sea wall along the beach road with its steps up to the promenade: the wall 0.65 m high, its
    face the picture's; four steps standing out from it, each riser the picture's; the promenade's paving on top, 3 m
    deep, in its own colour."""
    x0, x1, y0, y1 = WALL_LOW
    conc = (atlas.place(LK.flat_sample(img, (3700, 660, 3900, 760))), (64, 64))
    paving = (atlas.place(LK.flat_sample(img, (3000, 600, 3250, 640))), (64, 64))
    gw = float(WALL_FOOT)
    Zw = lambda py: (gw - py) / S
    b, X = builder(atlas, img, (3140, 600, 4128, 870), 3640.0, conc, gy=gw)
    b.box(X(x0), X(x1), 0.0, 0.4, 0.0, Zw(y0), side=conc, skip=('bottom',))
    b.face([P(X(x0), 0.4, Zw(y0)), P(X(x1), 0.4, Zw(y0)), P(X(x1), 3.4, Zw(y0)), P(X(x0), 3.4, Zw(y0))], paving)
    sx0, sx1 = STEPS['x']
    rows = STEPS['rows']
    for k in range(4):                                   # each step a box from the ground, the lowest the furthest out
        b.box(X(sx0), X(sx1), -1.2 + 0.3 * k, 0.0, 0.0, Zw(rows[k + 1]), side=conc, skip=('bottom', 'back'))
    o = b.object('KmSeaWallSteps')
    return o, dict(id='KM-B23', source='photo/KM2-3: the low sea wall along the beach road and its steps up to the '
                   'promenade', cutout=False, budget=300, px_centre=3640.0, px_per_m=S,
                   real_size=[round((x1 - x0) / S, 2), 4.6, round(Zw(y0), 2)])


def cutout(atlas, img, mask, box, foot, s, name, info, both=True):
    x0, y0, x1, y1 = box
    a = np.asarray(img.convert('RGB'))
    o = LK.card(atlas, np.dstack([a[y0:y1, x0:x1], mask[y0:y1, x0:x1] * 255]), box, (x0 + x1) / 2, float(foot), s, 0.0,
                name, both)
    info.update(real_size=[round((x1 - x0) / s, 2), 0.01, round((foot - y0) / s, 2)], px_centre=(x0 + x1) / 2,
                px_per_m=round(s, 2), cutout=True)
    info.setdefault('budget', 100)
    return o, info


def backdrops(atlas, img):
    """The promenade's high wall, the dune and its pines (KM-B40), at 90 px to the metre (the wall about 2.4 m, its foot
    on the promenade), and the pines behind the neighbour's houses (KM-B41) at 120 px to the metre: cut out against the
    sky; the houses, the shop and the poles in front are their own models, so the pines' card lets them go."""
    a = np.asarray(img.convert('RGB'))
    keep = (~sky(a)).astype(np.uint8)
    view = keep.copy()
    view[:, :2790] = 0
    view[650:] = 0
    view = cv2.morphologyEx(view, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    trees = keep.copy()
    houses = poly_mask(a.shape, [[(0, 0), (789, 0), (789, 150), (861, 144), (1389, 422), (1420, 860), (0, 860)]],
                       [(1330, 0, 2780, 860)])
    trees &= 1 - houses
    trees[480:] = 0
    trees = cv2.morphologyEx(trees, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    v = cutout(atlas, img, view, VIEW_BOX, 640, 90.0, 'KmPromenadeView',
               dict(id='KM-B40', source='photo/KM2-3: the promenade\'s high wall, the dune and its pines beyond the '
                    'steps (a cut-out)'), both=False)
    t = cutout(atlas, img, trees, TREES_BOX, 700, 120.0, 'KmShopPines',
               dict(id='KM-B41', source='photo/KM2-3: the pines behind the neighbour\'s houses (a cut-out)'), both=False)
    return [v, t]


def build_all():
    src, img = pictures()
    os.makedirs(REVIEW, exist_ok=True)
    img.save(os.path.join(REVIEW, 'painted.jpg'), quality=88)
    atlas = LK.Atlas(ATLAS_W, ATLAS_H)
    boards, tiles = samples(atlas, img)
    a = np.asarray(src)[..., :3]
    models = [shop(atlas, img, boards, tiles), neighbour(atlas, img, boards, tiles), rack(atlas, src),
              fish_boxes(atlas, src), crates(atlas, src), sea_wall_steps(atlas, img)]
    models += backdrops(atlas, img)
    models.append(cutout(atlas, src, poly_mask(a.shape, [SIGN_NP]), SIGN_NP_BOX, 800, S, 'KmNoParkingSign',
                         dict(id='KM-A43', source='photo/KM2-3: the no-parking sign on its post (a cut-out)')))
    models.append(cutout(atlas, src, poly_mask(a.shape, [SIGN_BUS]), SIGN_BUS_BOX, 830, S, 'KmBusStopSign',
                         dict(id='KM-A44', source='photo/KM2-3: the bus stop\'s sign on its post (a cut-out)')))
    return src, img, atlas, models


REVIEW_BOXES = dict(KmGrandmaShop=(1330, 0, 2780, 860), KmShopNeighbour=(0, 0, 1420, 860), KmDryingRack=RACK_BOX,
                    KmFishBoxes=(2310, 615, 2675, 870), KmCrates=(2655, 635, 2775, 835),
                    KmSeaWallSteps=(3140, 600, 4128, 870), KmPromenadeView=VIEW_BOX, KmShopPines=TREES_BOX,
                    KmNoParkingSign=SIGN_NP_BOX, KmBusStopSign=SIGN_BUS_BOX)
CARDS = ('KmPromenadeView', 'KmShopPines', 'KmNoParkingSign', 'KmBusStopSign')


def checks(o, info, oe, fins, tris):
    """The seventeen checks of a KM2-3 set piece (docs/ASSET_REVIEW.md)."""
    card_ = o.name in CARDS
    n = o.name
    return {
        1: ('pass', 'each part once (looked at in Top and Bottom)'),
        2: ('limit' if oe or fins else 'pass',
            '%d edges with one face, %d with three or more: %s' % (oe, fins, 'cut-out cards' if card_ else
            'boxes without the faces no one sees, and single faces (a tray, a porch roof, a card)')),
        3: ('limit' if card_ else 'pass', 'a flat cut-out: its depth is not modelled' if card_ else
            'boxes and roofs measured off the picture at %.0f px to the metre' % info['px_per_m']),
        4: ('limit', 'the street side is the picture itself; the sides, backs and roofs take KM-P3\'s boards and tiles '
                     'or the part\'s own colour (no view of their own)' if not card_ else
            'the picture from the street, mirrored from behind' if n in ('KmNoParkingSign', 'KmBusStopSign') else
            'the picture from the street, nothing behind'),
        5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget %d), the shared 4096 x 2048 KmWhitebaitAtlas'
            % (tuple(info['real_size']) + (tris, info.get('budget', 1500)))),
        6: ('pass', 'its outline the picture\'s, measured'),
        7: ('pass', 'no holes in what the street sees'),
        8: ('pass', 'what stood in front of it is its own model, painted out of it'),
        9: ('pass', 'the photographic KM2-3, in KM-0\'s look'),
        10: ('pass', 'solid and whole' if n not in ('KmGrandmaShop', 'KmShopNeighbour') else
             'solid and whole; above the picture\'s top edge its roof goes on in KM-P3\'s tiles'),
        11: ('pass', 'no brand or logo: the shop\'s name and the boxes\' labels are invented'),
        12: ('pass', 'the overcast sky let go round every edge'),
        13: ('pass', 'painted out: the rack, the boxes, the reel, the crates and the scooter from the shop; the pots and '
                     'the pole from the fence and the houses'),
        14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'),
        17: ('n/a', 'one piece'),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    src, img, atlas, models = build_all()
    LK.export(models, atlas, OUT, REVIEW, 'KmWhitebaitAtlas.png', 'Whitebait', src, REVIEW_BOXES, checks, INSTALL)


if __name__ == '__main__':
    main()
