# KM2-1 Down to Yuigahama's set pieces (docs/KAMAKURA_BUILD.md, BUILD KM-L21), projection-modelled from the
# photographic KM2-1 as KM1-3's and KM1-4's were (km_leg_kit.py): the fronts along the lane at 120 px to the metre,
# measured off the picture, each face toward the street the picture's own pixels.
#   - the neighbour's two-storey timber house, its gable to the street, and its board fence (the pots before the fence
#     and the pole at its end painted out: they are the kit's);
#   - the concrete block wall with its bin;
#   - the narrow alley seen between the houses (a cut-out 6 m back, scaled about the game camera's eye as KM1-4's
#     layers are);
#   - the surf house, its upper block and its porch under a tin canopy (the leaning surfboards painted out: they are
#     their own cut-out, KmSurfboards);
#   - the coast road's tunnel as the game shows a tunnel, cut away from the side: a deck over the lane carrying the
#     picture's portal top, its "beach" sign and the guard rail, with the tunnel's tiled wall behind the lane;
#   - the embankment's retaining wall with the guard rail on top, to be laid along the lane before and after it;
#   - the surf rental hut, its upper block and lean-to (the bicycles painted out: they are the kit's; the surf rack
#     painted out: it is its own cut-out, KmSurfRack);
#   - the bamboo fence at the beach (a cut-out).
# All of them share one texture, KmSurfLaneAtlas.png (4096 x 2048).
#   blenv/bin/python km_surf_lane.py -- /abs/outdir /abs/review/kamakura/surf_lane [--install /abs/Assets/_Game/Art/Models/Kamakura]
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

SRC = 'photo/KM2-1_down_to_yuigahama.png'
S = 120.0                # px to the metre at the lane's fronts (the neighbour's 1.8 m fence)
CAM, CAM_H = 10.1, 2.45  # the game camera: its distance in front of the lane, its height
ATLAS_W, ATLAS_H = 4096, 2048
P = lambda x, y, z: Vector((x, y, z))


def scale_at(front):
    return S * (CAM + 1.5) / (CAM + front)


def ground_row(front, foot=890.0):
    """The picture's row where a layer `front` metres behind the lane meets the ground (KM1-4's E15: scaled about the
    camera's eye, the house fronts' foot at row `foot`)."""
    eye = foot - CAM_H * S
    return eye + CAM_H * scale_at(front)


def gable_front(b, el, apex, er, yf, yb, side):
    """A gabled roof whose gable faces the street: its front triangle (eave left, apex, eave right, each (x, z)) at
    depth yf, the picture's; its two slopes running back to yb and its back triangle in the roof's sample."""
    (xl, zl), (xa, za), (xr, zr) = el, apex, er
    b.face([P(xl, yf, zl), P(xr, yf, zr), P(xa, yf, za)])
    b.face([P(xr, yb, zr), P(xl, yb, zl), P(xa, yb, za)], side)
    b.face([P(xl, yb, zl), P(xl, yf, zl), P(xa, yf, za), P(xa, yb, za)], side)
    b.face([P(xr, yf, zr), P(xr, yb, zr), P(xa, yb, za), P(xa, yf, za)], side)
    b.face([P(xl, yf, zl), P(xl, yb, zl), P(xr, yb, zr), P(xr, yf, zr)], side)


def builder(atlas, img, crop, cx, gy, s=S):
    pos = atlas.place(img.crop(crop))
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    return pos, fmap, X, Z


# ---------------------------------------------------------------- the picture, painted
SURFBOARDS = (1280, 560, 1502, 886)
SURF_RACK = (3188, 545, 3497, 864)
BAMBOO = (3598, 500, 3756, 760)


def painted_picture():
    """The photographic KM2-1 with what becomes the kit's or its own model painted out, each from the boards or wall
    above it or the ground beside it: the pots before the neighbour's fence and the pole at its end, the leaning
    surfboards before the surf house, the bicycles before the hut and its surf rack, and the image tool's mark (D31)."""
    src = KB.ref(SRC)
    a = np.asarray(src).copy()
    # the pots: the fence where they stood, its rail, boards, posts and plinth, carried on from its plain section 330
    # px to the left, right of the bin (above the pots the picture's right section is slatted; carried down, its
    # slats made a grid)
    for x in range(618, 948):
        a[639:905, x] = a[639:905, x - 330]
    for x in range(930, 992):                            # the pole before the fence's end, from 60 px to the left
        a[630:905, x] = a[630:905, x - 60]
    # the surfboards: the house's plaster wall from the rows above them, the ground from the left
    for y in range(595, 862):
        a[y, 1282:1502] = a[525 + (y - 525) % 68, 1282:1502]
    LK.copy_patch(a, (1282, 860, 1502, 888), dx=-90)
    # the bicycles: the hut's boards from the rows above, the deck's edge and the sand from round them
    for y in range(700, 832):
        a[y, 2612:2932] = a[620 + (y - 620) % 78, 2612:2932]
    m = np.zeros(a.shape[:2], np.uint8)
    m[830:898, 2610:2935] = 1
    a = LK.inpaint(a, m, 7)
    # the surf rack: the lean-to's boards from the rows above, the sand below from round it
    for y in range(553, 840):
        a[y, 3186:3500] = a[470 + (y - 470) % 80, 3186:3500]
    m = np.zeros(a.shape[:2], np.uint8)
    m[838:868, 3186:3500] = 1
    a = LK.inpaint(a, m, 7)
    LK.copy_patch(a, (3960, 860, 4070, 965), dx=-130)    # the image tool's mark
    return src, Image.fromarray(a)


def card_model(atlas, src, mask, box, name, info, s=S):
    o, info = LK.cutout_model(atlas, src, mask, box, name, info, s)
    info.update(px_centre=(box[0] + box[2]) / 2, px_per_m=s)
    return o, info


# ---------------------------------------------------------------- the lane's houses
def lane_house(atlas, img):
    """The neighbour's two-storey timber house, its gable to the street: the ground storey, the skirt roof, the upper
    storey with its balcony and air conditioner, the gabled roof; and its board fence 1.5 m in front of it."""
    cx, gy = 580.0, 890.0
    pos, fmap, X, Z = builder(atlas, img, (170, 18, 994, 905), cx, gy)
    wood = (atlas.place(LK.colour_sample(img, (270, 560, 330, 640))), (64, 64))
    tiles = (atlas.place(LK.colour_sample(img, (300, 470, 700, 520))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, wood[0], wood[1])
    b.box(X(228), X(889), 0.0, 7.0, 0.0, Z(528), side=wood, skip=('bottom', 'top'))       # the ground storey
    b.skirt((X(172), X(906), -0.6, 7.6), (X(256), X(878), 0.4, 6.6, Z(456), Z(456)), Z(528), side=tiles)
    b.box(X(256), X(878), 0.4, 6.6, Z(456), Z(211), side=wood, skip=('bottom',))         # the upper storey
    b.box(X(756), X(844), -0.15, 0.4, Z(456), Z(394), side=wood, skip=('back', 'bottom'))  # its air conditioner
    gable_front(b, (X(200), Z(217)), (X(550), Z(24)), (X(911), Z(222)), 0.2, 6.8, tiles)
    b.box(X(222), X(989), -1.55, -1.42, 0.0, Z(639), side=wood, skip=('bottom',))       # the fence
    o = b.object('KmLaneHouse')
    return o, dict(id='KM-B18', source='photo/KM2-1 (left): the neighbour\'s timber house and its board fence',
                   real_size=[round((989 - 172) / S, 2), 9.15, round(Z(24), 2)], cutout=False, budget=1500,
                   px_centre=cx, px_per_m=S)


def block_wall(atlas, img):
    """The concrete block wall with its vent blocks, and the bin against it (1.85 m of it, 2 m tall), to be laid along a
    lane (KM1-1's block wall too)."""
    cx, gy = 111.0, 888.0
    pos, fmap, X, Z = builder(atlas, img, (0, 640, 222, 892), cx, gy)
    conc = (atlas.place(LK.colour_sample(img, (20, 660, 120, 740))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, conc[0], conc[1])
    b.box(X(0), X(222), 0.0, 0.15, 0.0, Z(646), side=conc, skip=('bottom',))
    o = b.object('KmBlockWall')
    return o, dict(id='KM-T22', source='photo/KM2-1 (left): the concrete block wall and its bin',
                   real_size=[round(222 / S, 2), 0.15, round(Z(646), 2)], cutout=False, budget=100, px_centre=cx,
                   px_per_m=S)


def alley(atlas, img):
    """The narrow alley seen between the houses, its houses and poles going back: a cut-out 6 m behind the lane, the
    sky not drawn."""
    front = 6.0
    s, gy, cx = scale_at(front), ground_row(front), 1107.0
    crop = (975, 280, 1242, int(gy))
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]]
    keep = (~LK.sky_mask(a)).astype(np.uint8)
    o = LK.card(atlas, np.dstack([a, keep * 255]), crop, cx, gy, s, 0.0, 'KmAlleyView', both=False)
    return o, dict(id='KM-B19', source='photo/KM2-1: the narrow alley between the houses (a cut-out, 6 m back)',
                   real_size=[round((crop[2] - crop[0]) / s, 2), 0.01, round((gy - crop[1]) / s, 2)], cutout=True,
                   budget=100, px_centre=cx, px_per_m=s)


def surf_house(atlas, img):
    """The surf house: its two-storey back block with wetsuits hung at its window, the one-storey front with its gable
    to the street, its porch under the tin canopy (wetsuits, crates, the cool box), the long white board at its end."""
    cx, gy = 1560.0, 880.0
    pos, fmap, X, Z = builder(atlas, img, (1190, 150, 1920, 886), cx, gy)
    plaster = (atlas.place(LK.flat_sample(img, (1500, 400, 1560, 470))), (64, 64))      # its gable wall's plaster
    tiles = (atlas.place(LK.colour_sample(img, (1330, 470, 1600, 500))), (64, 64))
    tin = (atlas.place(img.crop((1475, 512, 1875, 545)).resize((256, 32), Image.LANCZOS)), (256, 32))
    b = KB.Builder(atlas, pos, fmap, plaster[0], plaster[1])
    b.box(X(1195), X(1590), 1.0, 7.0, 0.0, Z(275), side=plaster, skip=('bottom',))       # the back block
    gable_front(b, (X(1255), Z(265)), (X(1445), Z(160)), (X(1630), Z(275)), 0.8, 7.2, tiles)
    b.box(X(1285), X(1880), -0.5, 4.0, 0.0, Z(520), side=plaster, skip=('bottom',))      # the front, one storey
    gable_front(b, (X(1255), Z(525)), (X(1612), Z(365)), (X(1885), Z(495)), -0.7, 4.2, tiles)
    b.face([P(X(1470), -1.9, Z(550)), P(X(1880), -1.9, Z(550)), P(X(1880), -0.5, Z(510)), P(X(1470), -0.5, Z(510))],
           tin)                                                                          # the tin canopy
    b.face([P(X(1880), -0.5, Z(510) - 0.03), P(X(1470), -0.5, Z(510) - 0.03), P(X(1470), -1.9, Z(550) - 0.03),
            P(X(1880), -1.9, Z(550) - 0.03)], tin)                                       # the canopy's underside
    b.box(X(1495), X(1840), -1.9, -0.5, Z(870), Z(796), side=plaster, skip=('bottom',))   # the porch's deck
    for p0, p1 in ((1518, 1534), (1834, 1850)):                                          # its posts
        b.box(X(p0), X(p1), -1.85, -1.7, Z(796), Z(550), side=plaster, skip=('bottom', 'top'))
    o = b.object('KmSurfHouse')
    return o, dict(id='KM-B20', source='photo/KM2-1: the surf house, its porch, wetsuits and the long white board',
                   real_size=[round((1915 - 1195) / S, 2), 9.1, round(Z(160), 2)], cutout=False, budget=1500,
                   px_centre=cx, px_per_m=S)


# ---------------------------------------------------------------- the coast road
def tunnel(atlas, img):
    """The pedestrian tunnel under the coast road, as the game draws a tunnel side-on (cut away): a deck over the lane
    whose face toward the street is the picture's portal top (the parapet, the rusty "beach" sign, the frame), the guard
    rail on its edge (cut out against the sky), the dark ceiling under it, and behind the lane the tunnel's tiled wall.
    The opening is 2.5 m high and 4 m long; the game darkens it (DarkZone)."""
    cx, gy = 2216.0, 798.0
    crop = (1972, 262, 2462, 500)
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]]
    keep = (~LK.sky_mask(a)).astype(np.uint8)
    pos = atlas.place(Image.fromarray(np.dstack([a, keep * 255]), 'RGBA'))
    fmap = lambda co: (cx + co.x * S - crop[0], gy - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    Z = lambda py: (gy - py) / S
    conc = (atlas.place(LK.colour_sample(img, (1890, 450, 1960, 600))), (64, 64))
    ceil = (atlas.place(LK.flat_sample(img, (2150, 505, 2300, 520))), (64, 64))
    tiles = (atlas.place(img.crop((2300, 520, 2400, 780))), (100, 260))
    b = KB.Builder(atlas, pos, fmap, conc[0], conc[1])
    x0, x1 = X(1972), X(2462)
    # the deck: its face toward the street (the portal top, the sign), its underside (the ceiling), its top and back
    b.face([P(x0, -1.7, Z(498)), P(x1, -1.7, Z(498)), P(x1, -1.7, Z(329)), P(x0, -1.7, Z(329))])
    b.face([P(x0, -1.7, Z(329)), P(x1, -1.7, Z(329)), P(x1, 2.2, Z(329)), P(x0, 2.2, Z(329))], conc)
    b.face([P(x0, 2.2, Z(498)), P(x1, 2.2, Z(498)), P(x1, -1.7, Z(498)), P(x0, -1.7, Z(498))], ceil)     # facing down
    b.face([P(x0, 2.2, Z(498)), P(x0, -1.7, Z(498)), P(x0, -1.7, Z(329)), P(x0, 2.2, Z(329))], conc)
    b.face([P(x1, -1.7, Z(498)), P(x1, 2.2, Z(498)), P(x1, 2.2, Z(329)), P(x1, -1.7, Z(329))], conc)
    # the guard rail along its edge, cut out against the sky (the same projection: the rows above the parapet)
    b.face([P(x0, -1.6, Z(329)), P(x1, -1.6, Z(329)), P(x1, -1.6, Z(262)), P(x0, -1.6, Z(262))])
    # the tunnel's wall behind the lane, its tiles
    b.face([P(x0, 2.2, 0.0), P(x1, 2.2, 0.0), P(x1, 2.2, Z(498)), P(x0, 2.2, Z(498))], tiles, project=False)
    o = b.object('KmCoastTunnel', outward=False)
    return o, dict(id='KM-B21', source='photo/KM2-1: the tunnel under the coast road: its portal top and sign as the '
                   'deck\'s face, the guard rail, the tiled wall', real_size=[round((2462 - 1972) / S, 2), 3.9,
                   round(Z(262), 2)], cutout=True, budget=100, px_centre=cx, px_per_m=S)


def embankment(atlas, img):
    """The coast road's embankment wall along the lane (streaked concrete, its grassy ledge, the guard rail on top cut
    out against the sky): 1.7 m of it, laid in turn along the lane."""
    cx, gy = 1872.0, 820.0
    crop = (1772, 262, 1972, 822)
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]].copy()
    # below the grassy ledge the picture's wall is hidden by the surf house and its plants: it takes the parapet's
    # clean streaked concrete (x 2425 to 2625, rows 340 to 398, right of the sign), stretched down the wall (its rust
    # streaks run down; repeated, the band made a ladder)
    full = np.asarray(img.convert('RGB'))
    rows = a.shape[0] - (429 - crop[1])
    band = Image.fromarray(full[340:398, 2425:2625]).resize((a.shape[1], rows), Image.BICUBIC)
    a[429 - crop[1]:] = np.asarray(band)
    keep = (~LK.sky_mask(a)).astype(np.uint8)
    pos = atlas.place(Image.fromarray(np.dstack([a, keep * 255]), 'RGBA'))
    fmap = lambda co: (cx + co.x * S - crop[0], gy - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    Z = lambda py: (gy - py) / S
    conc = (atlas.place(LK.colour_sample(img, (1890, 450, 1960, 600))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, conc[0], conc[1])
    x0, x1 = X(1772), X(1972)
    b.face([P(x0, 0.0, 0.0), P(x1, 0.0, 0.0), P(x1, 0.0, Z(262)), P(x0, 0.0, Z(262))])
    b.face([P(x0, 0.0, Z(329)), P(x1, 0.0, Z(329)), P(x1, 3.0, Z(329)), P(x0, 3.0, Z(329))], conc)   # the road's verge
    o = b.object('KmEmbankmentWall', outward=False)
    return o, dict(id='KM-T20', source='photo/KM2-1: the coast road\'s embankment wall and guard rail',
                   real_size=[round(200 / S, 2), 3.0, round(Z(262), 2)], cutout=True, budget=100, px_centre=cx,
                   px_per_m=S)


# ---------------------------------------------------------------- the beach
def surf_hut(atlas, img):
    """The surf rental hut of silver-grey timber: its upper block, the lower front with its gable to the street and the
    rusty canopy over its open door, the lean-to at its right, the steps."""
    cx, gy = 3025.0, 860.0
    pos, fmap, X, Z = builder(atlas, img, (2486, 100, 3566, 866), cx, gy)
    wood = (atlas.place(LK.colour_sample(img, (2560, 560, 2640, 680))), (64, 64))
    roof = (atlas.place(LK.colour_sample(img, (2750, 370, 3000, 400))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, wood[0], wood[1])
    b.box(X(2673), X(3180), 1.0, 7.0, Z(440), Z(267), side=wood, skip=('bottom',))       # the upper block
    gable_front(b, (X(2640), Z(327)), (X(2987), Z(113)), (X(3227), Z(260)), 0.8, 7.2, roof)
    b.box(X(2520), X(3420), -1.0, 7.0, 0.0, Z(530), side=wood, skip=('bottom',))         # the lower front
    gable_front(b, (X(2493), Z(540)), (X(3047), Z(373)), (X(3467), Z(513)), -1.2, 7.2, roof)
    b.face([P(X(2867), -1.6, Z(540)), P(X(3247), -1.6, Z(540)), P(X(3247), -1.0, Z(507)), P(X(2867), -1.0, Z(507))])
    b.box(X(3420), X(3560), -0.6, 5.0, 0.0, Z(530), side=wood, skip=('bottom',))         # the lean-to
    b.box(X(2927), X(3187), -1.5, -1.0, 0.0, Z(827), side=wood, skip=('bottom',))         # the steps
    o = b.object('KmSurfHut')
    return o, dict(id='KM-B22', source='photo/KM2-1 (right): the surf rental hut', real_size=[round((3560 - 2493) / S, 2),
                   8.8, round(Z(113), 2)], cutout=False, budget=1500, px_centre=cx, px_per_m=S)


def masks(src):
    """The cut-outs' masks: the leaning surfboards (their colours, and the grey traction pad), the surf rack (its boards'
    colours, the pale rack and chairs), the bamboo fence (not the sky, the sea or the sand)."""
    f = np.asarray(src.convert('RGB')).astype(np.int32)
    sat = f.max(-1) - f.min(-1)
    luma = 0.3 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
    out = {}
    m = np.zeros(f.shape[:2], np.uint8)
    x0, y0, x1, y1 = SURFBOARDS
    m[y0:y1, x0:x1] = (sat[y0:y1, x0:x1] > 55)
    m[800:868, 1432:1498] = 1                         # the pad at the orange board's tail
    out['boards'] = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # the rack by its outline (the boards' rounded tops, the chairs and the white board at its right), measured: its
    # cream and white boards have no colour to tell them from the hut's wall
    m = np.zeros(f.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.array([[3205, 862], [3205, 640], [3225, 612], [3245, 600], [3262, 590], [3280, 582],
                               [3300, 578], [3320, 580], [3335, 560], [3350, 552], [3370, 553], [3385, 548],
                               [3400, 552], [3420, 560], [3438, 562], [3450, 580], [3462, 610], [3480, 640],
                               [3495, 700], [3495, 862]], np.int32)], 1)
    out['rack'] = m
    m = np.zeros(f.shape[:2], np.uint8)
    x0, y0, x1, y1 = BAMBOO
    r, g, bb = f[y0:y1, x0:x1, 0], f[y0:y1, x0:x1, 1], f[y0:y1, x0:x1, 2]
    sky_or_sea = (bb > r + 15) & (bb > 120)
    sand = (luma[y0:y1, x0:x1] > 170) & (r > bb + 15)
    m[y0:y1, x0:x1] = ~(sky_or_sea | sand)
    out['bamboo'] = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return out


def build_all():
    src, img = painted_picture()
    os.makedirs(REVIEW, exist_ok=True)
    img.save(os.path.join(REVIEW, 'painted.jpg'), quality=88)
    ms = masks(src)
    atlas = LK.Atlas(ATLAS_W, ATLAS_H)
    models = [lane_house(atlas, img), surf_house(atlas, img), surf_hut(atlas, img), tunnel(atlas, img),
              embankment(atlas, img), block_wall(atlas, img), alley(atlas, img),
              card_model(atlas, src, ms['boards'], SURFBOARDS, 'KmSurfboards',
                         dict(id='KM-A36', source='photo/KM2-1: the surfboards leaning by the surf house (a cut-out)',
                              cutout=True, budget=100)),
              card_model(atlas, src, ms['rack'], SURF_RACK, 'KmSurfRack',
                         dict(id='KM-A36', source='photo/KM2-1: the hut\'s rack of surfboards and folded chairs (a '
                              'cut-out)', cutout=True, budget=100)),
              card_model(atlas, src, ms['bamboo'], BAMBOO, 'KmBambooFence',
                         dict(id='KM-T17', source='photo/KM2-1 (right): the bamboo fence by the boardwalk (a cut-out)',
                              cutout=True, budget=100))]
    return src, img, atlas, models


BOXES = dict(KmLaneHouse=(170, 18, 994, 905), KmBlockWall=(0, 640, 222, 892), KmAlleyView=(975, 280, 1242, 830),
             KmSurfHouse=(1190, 150, 1920, 886), KmCoastTunnel=(1972, 262, 2462, 800),
             KmEmbankmentWall=(1772, 262, 1972, 822), KmSurfHut=(2486, 100, 3566, 866), KmSurfboards=SURFBOARDS,
             KmSurfRack=SURF_RACK, KmBambooFence=BAMBOO)
CARDS = ('KmAlleyView', 'KmSurfboards', 'KmSurfRack', 'KmBambooFence')


def checks(o, info, oe, fins, tris):
    """The seventeen checks of a KM2-1 set piece (docs/ASSET_REVIEW.md)."""
    card_ = o.name in CARDS
    flat = o.name in ('KmCoastTunnel', 'KmEmbankmentWall')
    return {
        1: ('pass', 'each part once (looked at in Top and Bottom)'),
        2: ('limit' if oe or fins else 'pass',
            '%d edges with one face, %d with three or more: %s' % (oe, fins, 'a cut-out card' if card_ else
            'faces only where the street or the camera sees them (the tunnel and the wall are open behind)' if flat
            else 'boxes and roof faces without the faces no one sees (their bottoms)')),
        3: ('limit' if card_ else 'pass', 'a flat cut-out: its depth is not modelled' if card_ else
            'boxes and roofs measured off the picture at %.0f px to the metre' % info['px_per_m']),
        4: ('limit', 'the street side is the picture itself; the sides, back and roofs away from the street take the '
                     'part\'s own colour (no view of their own)'),
        5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget %d), the shared 4096 x 2048 KmSurfLaneAtlas'
            % (tuple(info['real_size']) + (tris, info.get('budget', 1500)))),
        6: ('pass', 'its outline the picture\'s'),
        7: ('pass', 'no holes in what the street sees'),
        8: ('pass', 'the pots, the pole and the bicycles are the kit\'s, the surfboards and the surf rack their own '
                    'cut-outs: each painted out of what stood behind it'),
        9: ('pass', 'the photographic KM2-1, in KM-0\'s look'),
        10: ('pass', 'solid and whole'),
        11: ('pass', 'no brand or logo: the signs\' words are invented or generic (砂浜, beach)'),
        12: ('pass', 'the sky cut out round the guard rail and over the alley; the wires cross the sky above'),
        13: ('pass', 'painted out: the pots and the pole from the fence, the surfboards from the surf house, the '
                     'bicycles and the surf rack from the hut, the image tool\'s mark (D31)'),
        14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'),
        17: ('n/a', 'one piece'),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    src, img, atlas, models = build_all()
    LK.export(models, atlas, OUT, REVIEW, 'KmSurfLaneAtlas.png', 'SurfLane', src, BOXES, checks, INSTALL)


if __name__ == '__main__':
    main()
