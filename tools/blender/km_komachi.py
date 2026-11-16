# KM1-3 Komachi-dori's set pieces (docs/KAMAKURA_BUILD.md: KM-B08 to B12; KM-A32's stool and chalkboard and KM-V04's
# rickshaw until their own views come), projection-modelled from the photographic KM1-3 as the home was from KM1-1
# (kit_buildings_km.py). Each is built from boxes and roofs measured off the picture, and each face toward the street
# shows the picture's own pixels. The faces the picture doesn't show take KM-P3's boards and tiles in the street's
# colours, or a sample of the model's own colour.
# What stands apart from a shop front is painted out of it and becomes its own cut-out model: the stools, the
# chalkboard and the rickshaw. The goods against a shop front stand out from it as boxes of the shop. The nobori flags
# and the kite sign stay on the fronts they hang against, until their own views come (KM-A30, A31).
# All of them share one texture, KmKomachiAtlas.png (4096 x 2048); each model gets its own material in the game
# (ArtBaker), cut out where its manifest says so.
#   blenv/bin/python km_komachi.py -- /abs/outdir /abs/review/kamakura/komachi [--install /abs/Assets/_Game/Art/Models/Kamakura]
# Writes into outdir <Model>.fbx, KmKomachiAtlas.png, Komachi.json and Komachi.blend. Into the review folder it writes
# views/<Model>.jpg (the eight views), source/<Model>.jpg (its part of the picture), painted.jpg (the picture with what
# became its own model painted out) and review.json (the checks).
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index('--') + 1:]
OUT, REVIEW = args[0], args[1]
INSTALL = args[args.index('--install') + 1] if '--install' in args else None
sys.argv = [sys.argv[0], '--', OUT]            # the kit module reads its own arguments
import bpy                                     # noqa: E402
import cv2                                     # noqa: E402
import numpy as np                             # noqa: E402
from mathutils import Vector                   # noqa: E402
from PIL import Image                          # noqa: E402
import asset_review as AR                      # noqa: E402
import kit_buildings_km as KB                  # noqa: E402
import kit_lib as K                            # noqa: E402

SRC = 'photo/KM1-3_komachi_dori.png'
S, GY = 120.0, 888.0          # px to the metre at the shop fronts (a shop's 2.1 m door), the shop fronts' foot
ATLAS_W, ATLAS_H = 4096, 2048
DENS = 80.0                   # the hidden faces' boards and tiles, px to the metre (the street sees them at a slant)


class Atlas(KB.Atlas):
    """The kit's atlas, 4096 wide and 2048 tall."""
    def __init__(self, w, h):
        super().__init__(w)
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w, h), (255, 255, 255, 255))

    def place(self, im):
        if self.x + im.width + 8 > self.w:
            self.x, self.y, self.row = 8, self.y + self.row + 16, 8
        if self.y + im.height + 8 > self.h:
            raise SystemExit('km_komachi.py: the atlas is full')
        pos = (self.x, self.y)
        im = im.convert('RGBA')
        pad = im.resize((im.width + 16, im.height + 16), Image.NEAREST)
        self.img.paste(pad, (self.x - 8, self.y - 8))
        self.img.paste(im, pos)
        self.x += im.width + 16
        self.row = max(self.row, im.height)
        return pos

    def uv(self, pos, px, py):
        return ((pos[0] + px) / self.w, 1.0 - (pos[1] + py) / self.h)


# ---------------------------------------------------------------- painting out what becomes its own model
def copy_patch(a, box, dx=0, dy=0):
    """Fills box with the pixels dx, dy away (the same wall's boards beside it, the paving's rows beside it)."""
    x0, y0, x1, y1 = box
    a[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]


def inpaint(a, mask, r=4):
    return cv2.inpaint(a, mask.astype(np.uint8), r, cv2.INPAINT_TELEA)


def stool_mask(shape):
    """The soft-serve stand's first stool, drawn from its measured parts (the wall's boards show between its legs, so
    no colour model can part them): its round seat, two front legs, two back legs and the curves where they meet the seat."""
    m = np.zeros(shape[:2], np.uint8)
    cv2.ellipse(m, (1421, 829), (27, 5), 0, 0, 360, 1, -1)
    for x0, y0, x1, y1 in ((1390, 831, 1397, 899), (1425, 832, 1433, 899), (1417, 832, 1422, 894), (1446, 832, 1453, 896)):
        m[y0:y1, x0:x1] = 1
    cv2.ellipse(m, (1399, 838), (8, 6), 0, 180, 270, 1, 4)        # the front leg's curve into the seat
    cv2.ellipse(m, (1444, 838), (8, 6), 0, 270, 360, 1, 4)        # the back leg's
    return m


def chalkboard_mask(shape):
    """The croquette shop's A-frame chalkboard: its board in its frame, leaning, and its three legs (the counter and the
    paving show between them)."""
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.array([[2112, 771], [2186, 771], [2181, 877], [2107, 877]], np.int32)], 1)
    for x0, y0, x1, y1 in ((2103, 874, 2112, 907), (2172, 874, 2182, 909), (2123, 876, 2131, 898)):
        m[y0:y1, x0:x1] = 1
    return m


def rickshaw_mask(a):
    """The rickshaw and its own colours: in each of its parts' zones (the hood, the wheels, the mudguard) the pixels that
    are its own, the greys and blacks of its metal and hood (the fence's brown and the bushes' green between its spokes
    left out); its red seat whole; the shafts drawn along their measured lines. Under the hood, where the struts stand
    against the fence, the zone is kept whole and what isn't the rickshaw's own is darkened: the hood's shade."""
    f = a.astype(np.int32)
    sat = f.max(-1) - f.min(-1)
    red = (f[..., 0] > f[..., 1] + 45) & (f[..., 0] > f[..., 2] + 40)
    own = (sat < 30) | red
    zone = np.zeros(a.shape[:2], np.uint8)
    cv2.fillPoly(zone, [np.array([[3112, 668], [3150, 654], [3270, 656], [3294, 676], [3292, 708], [3115, 708]], np.int32)], 1)
    cv2.circle(zone, (3238, 854), 59, 1, -1)                       # the near wheel
    cv2.circle(zone, (3160, 875), 36, 1, -1)                       # the far wheel, behind
    cv2.ellipse(zone, (3238, 854), (64, 64), 0, 180, 360, 1, 6)    # the mudguard over it
    m = (zone.astype(bool) & own).astype(np.uint8)
    seat = np.array([[3105, 832], [3110, 820], [3125, 790], [3140, 772], [3170, 760], [3195, 755], [3220, 752],
                     [3260, 747], [3265, 770], [3240, 785], [3220, 790], [3195, 805], [3180, 835], [3170, 850],
                     [3125, 845], [3105, 840]], np.int32)
    cv2.fillPoly(m, [seat], 1)
    shade = np.zeros(a.shape[:2], np.uint8)
    cv2.fillPoly(shade, [np.array([[3122, 706], [3284, 706], [3270, 745], [3220, 752], [3170, 760], [3140, 772],
                                   [3126, 788], [3121, 760]], np.int32)], 1)    # under the hood, down to the seat
    m[shade > 0] = 1
    cv2.line(m, (3110, 842), (2982, 902), 1, 5)                     # the shafts
    cv2.line(m, (3127, 852), (3007, 914), 1, 5)
    m[917:, :] = 0                                                 # not the paving under the tyres
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    for i in range(1, n):
        if st[i, 4] < 15:
            m[lab == i] = 0
    rgb = a.copy()
    dim = (shade > 0) & ~own
    rgb[dim] = (rgb[dim] * 0.3).astype(np.uint8)
    return m, rgb


# What stands apart from the shop fronts, in the picture's pixels: the box round it and where it surely is.
STOOLS = [(1388, 822, 1455, 899), (1493, 822, 1553, 899), (1678, 822, 1742, 899)]
CHALKBOARD = (2103, 770, 2198, 910)
RICKSHAW = (2976, 652, 3304, 918)


def painted_picture():
    """The photographic KM1-3 with the stools, the chalkboard and the rickshaw painted out (each from the boards and the
    paving beside it), the tool's mark painted out of the paving and fence (bottom right, D31), and the cut-outs' masks."""
    src = KB.ref(SRC)
    a = np.asarray(src).copy()
    masks = {}
    masks['stool'] = stool_mask(a.shape)
    masks['chalkboard'] = chalkboard_mask(a.shape)
    masks['rickshaw'], rick_rgb = rickshaw_mask(a)
    # each stool: the wall's boards and its foot 70 px to the left (the first stool) or the wall just painted
    copy_patch(a, (1386, 818, 1457, 901), dx=-72)
    copy_patch(a, (1491, 818, 1555, 901), dx=-66)
    copy_patch(a, (1676, 818, 1744, 901), dx=-72)
    # the chalkboard: the counter's boards and foot, and the paving, 92 px to its left
    copy_patch(a, (2100, 766, 2200, 912), dx=-96)
    # the rickshaw: only its shafts and the seat's front edge cross a model (the souvenir shop's right post and its
    # foot, x < 3125); they are thin, so they are painted from round them. Beyond, it stands in front of the gap and the
    # fence's first boards, which no model uses (the side gate's fence and the yard start at x 3318, past the wheel).
    rm = cv2.dilate(masks['rickshaw'], np.ones((5, 5), np.uint8))
    rm[:, 3125:] = 0
    a = inpaint(a, rm, 5)
    # the image tool's mark on the paving and the fence's foot (bottom right): the fence's rails and the paving to its left
    copy_patch(a, (3960, 852, 4128, 980), dx=-170)
    masks['rickshaw_rgb'] = Image.fromarray(rick_rgb)
    return src, Image.fromarray(a), masks


# ---------------------------------------------------------------- the models
def projector(atlas, img, crop, s=S, gy=GY, cx=None):
    """The picture's crop placed in the atlas, and the map from a point in metres (x along, z up; the model's middle at
    cx) to its pixel in that crop."""
    pos = atlas.place(img.crop(crop))
    cx = (crop[0] + crop[2]) / 2 if cx is None else cx
    return pos, (lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])), cx


def colour_sample(img, box, size=(64, 64)):
    """A plain sample of a part's own colour (a post's red, a cap's black), its mean over box, a little noise kept."""
    c = img.crop(box).convert('RGB').resize(size, Image.BILINEAR)
    return c


def gateway(atlas, img):
    """KM-B08, the red torii-shaped gateway over Komachi-dori's mouth: two posts with black feet, the tie beam, the
    signboard between, the top beam with its black cap and upturned ends. It stands further back than the shops (about
    86 px to the metre: 6 m tall, as its sheet has it); a cut-out, so the sky in the curve of its top beam is not drawn."""
    s, gy = 86.0, 808.0
    crop = (515, 285, 1040, 812)
    # the gateway's own pixels (red, its black cap and feet, the sign's gold letters); the sky, sea and street behind not
    a = np.asarray(img.convert('RGB')).astype(np.int32)[crop[1]:crop[3], crop[0]:crop[2]]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    luma = 0.3 * r + 0.59 * g + 0.11 * b
    red = (r > g + 45) & (r > b + 45)
    dark = (luma < 95) & (np.abs(r - b) < 40)
    keep = (red | dark).astype(np.uint8)
    # the signboard is whole (its letters gold on red)
    keep[352 - crop[1]:414 - crop[1], 645 - crop[0]:912 - crop[0]] = 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    rgba = np.dstack([a.astype(np.uint8), keep * 255])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    cx = 777.5
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    redpos = atlas.place(colour_sample(img, (610, 520, 638, 700)))
    capos = atlas.place(colour_sample(img, (650, 315, 900, 324)))
    red_side, cap_side = (redpos, (64, 64)), (capos, (64, 64))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    b = KB.Builder(atlas, pos, fmap, redpos, (64, 64))
    # the posts: octagonal, 0.5 m across, from the ground to the top beam
    for p0, p1 in ((602, 646), (911, 953)):
        xm, rr = (X(p0) + X(p1)) / 2, (X(p1) - X(p0)) / 2
        ring = [(xm + rr * math.cos(math.pi / 8 + k * math.pi / 4), rr * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
        for k in range(8):
            (xa, ya), (xb, yb) = ring[k], ring[(k + 1) % 8]
            b.face([Vector((xb, yb, 0.0)), Vector((xa, ya, 0.0)), Vector((xa, ya, Z(352))), Vector((xb, yb, Z(352)))],
                   red_side)
    b.box(X(560), X(995), -0.17, 0.17, Z(441), Z(411), side=red_side)          # the tie beam
    b.box(X(645), X(911), -0.1, 0.1, Z(414), Z(352), side=red_side)          # the signboard
    b.box(X(545), X(1012), -0.25, 0.25, Z(352), Z(326), side=red_side)       # the top beam
    # its black cap, its top rising toward the ends as the picture's does (measured column by column: the first dark
    # pixel from the sky down), in 16 segments
    dark_col = (luma < 95)
    xs = np.linspace(523, 1033, 17)
    tops = []
    for x in xs:
        col = dark_col[:, int(x) - crop[0]]
        ys = np.nonzero(col[:326 - crop[1]])[0]
        tops.append(crop[1] + (ys.min() if len(ys) else 312 - crop[1]))
    tops = np.convolve(np.pad(tops, 1, mode='edge'), np.ones(3) / 3, 'valid')
    P = lambda x, y, z: Vector((x, y, z))
    for k in range(16):
        xa, xb, za, zb, z0 = X(xs[k]), X(xs[k + 1]), Z(tops[k]), Z(tops[k + 1]), Z(326)
        b.face([P(xa, -0.3, z0), P(xb, -0.3, z0), P(xb, -0.3, zb), P(xa, -0.3, za)], cap_side)     # front (projected)
        b.face([P(xb, 0.3, z0), P(xa, 0.3, z0), P(xa, 0.3, za), P(xb, 0.3, zb)], cap_side)         # back
        b.face([P(xa, -0.3, za), P(xb, -0.3, zb), P(xb, 0.3, zb), P(xa, 0.3, za)], cap_side)       # top
        b.face([P(xa, 0.3, z0), P(xb, 0.3, z0), P(xb, -0.3, z0), P(xa, -0.3, z0)], cap_side)       # underside
    b.face([P(X(xs[0]), 0.3, Z(326)), P(X(xs[0]), -0.3, Z(326)), P(X(xs[0]), -0.3, Z(tops[0])), P(X(xs[0]), 0.3, Z(tops[0]))], cap_side)
    b.face([P(X(xs[-1]), -0.3, Z(326)), P(X(xs[-1]), 0.3, Z(326)), P(X(xs[-1]), 0.3, Z(tops[-1])), P(X(xs[-1]), -0.3, Z(tops[-1]))], cap_side)
    o = b.object('KmKomachiGateway')
    return o, dict(id='KM-B08', source='photo/KM1-3: the red gateway over the street\'s mouth (left of the shops)',
                   real_size=[round((1033 - 523) / s, 2), 0.6, round(Z(min(tops)), 2)], cutout=True, budget=1500)


def shop_samples(atlas, img):
    """The hidden faces of every shop: KM-P3's boards in the shops' own dark timber, its tiles in their roofs' grey, and
    the soft-serve stand's rusty corrugated iron (a band of its own roof, stretched once)."""
    boards = KB.boards_texture(img.crop((1880, 290, 1960, 420)), DENS, 600, 600)
    tiles = KB.tiles_texture(img.crop((1900, 140, 2400, 220)), DENS, 640, 640)
    tin = img.crop((1150, 120, 1820, 210)).resize((512, 96), Image.LANCZOS)
    return ((atlas.place(boards), boards.size, DENS), (atlas.place(tiles), tiles.size, DENS),
            (atlas.place(tin), tin.size))


def shop(atlas, img, name, crop, cx, parts, info, side, roof):
    """A shop: its front the picture's crop; parts(b, X, Z) lays its boxes and roofs."""
    pos, fmap, cx = projector(atlas, img, crop, cx=cx)
    X = lambda px: (px - cx) / S
    Z = lambda py: (GY - py) / S
    b = KB.Builder(atlas, pos, fmap, side[0], side[1])
    parts(b, X, Z, side, roof)
    return b.object(name), info


def soft_serve(b, X, Z, side, roof, tin=None):
    # the lean-to on its left, its own little roof sloping down to the street
    b.box(X(1212), X(1312), -1.6, 1.4, 0.0, Z(600), side=side, skip=('bottom', 'top'))
    b.face([Vector((X(1205), -1.7, Z(608))), Vector((X(1312), -1.7, Z(608))), Vector((X(1312), 1.4, Z(560))),
            Vector((X(1205), 1.4, Z(560)))], roof)
    # the ground floor and its counter; the display case on its table standing out from it
    b.box(X(1312), X(1797), -2.0, 4.0, 0.0, Z(545), side=side, skip=('bottom', 'top'))
    b.box(X(1597), X(1778), -2.45, -2.0, Z(890), Z(712), side=side, skip=('back',))
    # the skirt roof round the ground floor, meeting the upper wall
    b.skirt((X(1250), X(1800), -2.5, 4.3), (X(1330), X(1797), -1.5, 3.5, Z(452), Z(452)), Z(545), side=roof)
    # the upper storey, set back, and its roof of corrugated iron: the front slope toward the street
    b.box(X(1330), X(1797), -1.5, 3.5, Z(452), Z(215), side=side, skip=('bottom',))
    b.hip_roof(X(1140), X(1838), X(1172), X(1836), -2.1, 1.0, 4.1, Z(215), Z(112), side=tin)


def build(atlas, img):
    side, roof, tin = shop_samples(atlas, img)
    models = []
    models.append(gateway(atlas, img))
    models.append(shop(atlas, img, 'KmSoftServeStand', (1130, 105, 1845, 900), 1560.0,
                       lambda b, X, Z, sd, rf: soft_serve(b, X, Z, sd, rf, tin),
                       dict(id='KM-B11', source='photo/KM1-3: the soft-serve stand (the first shop), its lean-to and '
                            'its display case', real_size=[round((1838 - 1140) / S, 2), 6.6, round(Z_(112), 2)],
                            cutout=False, budget=1500), side, roof))
    models.append(shop(atlas, img, 'KmCroquetteShop', (1795, 105, 2210, 900), 2003.0, croquette,
                       dict(id='KM-B09', source='photo/KM1-3: the croquette shop (the left half of the two-shop '
                            'building)', real_size=[round((2206 - 1800) / S, 2), 6.6, round(Z_(118), 2)],
                            cutout=False, budget=1500), side, roof))
    models.append(shop(atlas, img, 'KmSenbeiShop', (2202, 105, 2645, 900), 2424.0, senbei,
                       dict(id='KM-B10', source='photo/KM1-3: the rice-cracker shop (the right half of the two-shop '
                            'building), its grill, its jars and the pink nobori', real_size=[round((2642 - 2206) / S, 2), 6.6,
                            round(Z_(118), 2)], cutout=False, budget=1500), side, roof))
    models.append(shop(atlas, img, 'KmSouvenirShop', (2555, 50, 3175, 900), 2860.0, souvenir,
                       dict(id='KM-B11', source='photo/KM1-3: the souvenir shop (the gabled one), its racks and its '
                            'rusty tin canopy, the kite sign on its front', real_size=[round((3168 - 2562) / S, 2), 6.6,
                            round(Z_(62), 2)], cutout=False, budget=1500), side, roof))
    return models


def Z_(py):
    return (GY - py) / S


def croquette(b, X, Z, side, roof):
    # the shop's half of the two-shop building: its ground floor with the counter, the curtains and the display
    b.box(X(1820), X(2206), -2.0, 4.0, 0.0, Z(535), side=side, skip=('bottom', 'top'))
    b.box(X(1838), X(2165), -2.3, -2.0, Z(888), Z(750), side=side, skip=('back',))       # the counter's front
    b.box(X(2075), X(2195), -2.3, -2.0, Z(750), Z(665), side=side, skip=('back', 'bottom'))  # the display case on it
    b.skirt((X(1800), X(2206), -2.6, 4.3), (X(1825), X(2206), -1.5, 3.5, Z(455), Z(455)), Z(535), side=roof)
    b.box(X(1825), X(2206), -1.5, 3.5, Z(455), Z(240), side=side, skip=('bottom',))
    b.box(X(1838), X(1925), -1.8, -1.5, Z(452), Z(388), side=side, skip=('back', 'bottom'))  # its air conditioner
    b.hip_roof(X(1800), X(2206), X(1860), X(2206), -2.1, 1.0, 4.1, Z(238), Z(118), side=roof)   # hipped at its left


def senbei(b, X, Z, side, roof):
    # the other half: the open front, the grill and the jars of crackers on their stand standing out from it
    b.box(X(2206), X(2620), -2.0, 4.0, 0.0, Z(535), side=side, skip=('bottom', 'top'))
    b.box(X(2268), X(2395), -2.55, -2.0, Z(890), Z(680), side=side, skip=('back',))        # the grill
    b.box(X(2440), X(2620), -2.6, -2.0, Z(890), Z(720), side=side, skip=('back',))         # the jars on their stand
    b.skirt((X(2206), X(2642), -2.6, 4.3), (X(2206), X(2590), -1.5, 3.5, Z(455), Z(455)), Z(535), side=roof)
    b.box(X(2206), X(2590), -1.5, 3.5, Z(455), Z(240), side=side, skip=('bottom',))
    b.box(X(2500), X(2590), -1.8, -1.5, Z(452), Z(388), side=side, skip=('back', 'bottom'))  # its air conditioner
    b.hip_roof(X(2206), X(2612), X(2206), X(2532), -2.1, 1.0, 4.1, Z(238), Z(118), side=roof)   # hipped at its right


def souvenir(b, X, Z, side, roof):
    # the ground floor, open, its racks standing out from it; the rusty tin canopy over it
    b.box(X(2625), X(3120), -2.0, 4.0, 0.0, Z(550), side=side, skip=('bottom',))
    b.box(X(2650), X(2832), -2.55, -2.0, Z(888), Z(640), side=side, skip=('back',))        # the rack of fans and goods
    b.box(X(2932), X(3078), -2.45, -2.0, Z(888), Z(625), side=side, skip=('back',))        # the hanging goods
    b.face([Vector((X(2640), -2.75, Z(550))), Vector((X(3165), -2.75, Z(550))), Vector((X(3165), -2.0, Z(492))),
            Vector((X(2640), -2.0, Z(492)))], roof)                                         # the canopy
    b.box(X(2640), X(3080), -2.0, 3.5, Z(550), Z(205), side=side, skip=('bottom',))
    b.box(X(2900), X(3135), -2.1, -2.0, Z(530), Z(318), side=side, skip=('back',))         # the kite sign on its front
    b.hip_roof(X(2562), X(3110), X(2597), X(3022), -2.5, 0.75, 4.0, Z(205), Z(62), side=roof)


def side_gate(atlas, img):
    """KM-B12, the shrine's side gate at the top of the street (the leg's stop): its two posts, the head beam, the
    moss-grown tiled roof, the open door, and the board fence either side. It stands a little back from the shops (its
    foot at y 868). Through its opening, and over its fence, the shrine's yard shows (KmShrineYard)."""
    gy, cx = 868.0, 3685.0
    crop = (3310, 280, 4128, 872)
    pos = atlas.place(img.crop(crop))
    fmap = lambda co: (cx + co.x * S - crop[0], gy - co.z * S - crop[1])
    X = lambda px: (px - cx) / S
    Z = lambda py: (gy - py) / S
    wood = (atlas.place(colour_sample(img, (3505, 600, 3535, 840))), (64, 64))
    gb = KB.boards_texture(img.crop((3330, 690, 3500, 850)), DENS, 320, 200)
    boards = (atlas.place(gb), gb.size, DENS)
    moss = (atlas.place(img.crop((3500, 330, 3900, 440)).resize((256, 72), Image.LANCZOS)), (256, 72))
    b = KB.Builder(atlas, pos, fmap, wood[0], wood[1])
    for p0, p1 in ((3502, 3540), (3826, 3868)):
        b.box(X(p0), X(p1), -0.18, 0.18, 0.0, Z(478), side=wood, skip=('bottom',))
    b.box(X(3490), X(3880), -0.22, 0.22, Z(560), Z(478), side=wood)                 # the head beam
    b.box(X(3762), X(3828), 0.18, 0.26, 0.0, Z(560), side=wood, skip=('bottom',))   # the door, open
    b.hip_roof(X(3365), X(4005), X(3428), X(3905), -1.35, 0.0, 1.35, Z(472), Z(298), side=moss)
    for f0, f1 in ((3318, 3502), (3868, 4128)):                                      # the fence, 1.7 m
        b.box(X(f0), X(f1), -0.06, 0.06, 0.0, Z(665), side=boards, skip=('bottom',))
    o = b.object('KmShrineSideGate')
    return o, dict(id='KM-B12', source='photo/KM1-3 (right): the shrine\'s side gate, its door and its fence',
                   real_size=[round((4128 - 3318) / S, 2), 2.7, round(Z(298), 2)], cutout=False, budget=1500)


# The side gate's parts in the picture's pixels: its posts, head beam, door and fences (the roof is a trapezoid)
GATE_BOXES = [(3500, 470, 3542, 870), (3824, 470, 3870, 870), (3488, 478, 3882, 562), (3760, 556, 3830, 870),
              (3318, 662, 3504, 870), (3866, 662, 4128, 870)]


def sky_mask(a):
    """The pale summer sky of the photographic pictures (as unsky's pale test), and its soft fringe."""
    a = a.astype(np.int32)
    sky = (a[..., 2] - a[..., 0] > 18) & (a[..., 2] - a[..., 1] > 4) & (a[..., 2] > 170)
    return cv2.dilate(sky.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


def card(atlas, rgba, crop, cx, gy, s, y, name, both=True):
    """A cut-out standing upright at depth y: the picture exactly from the street, mirrored from behind."""
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    b = KB.Builder(atlas, None, None, None, None)
    x0, y0, x1, y1 = crop
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    for back in ((False, True) if both else (False,)):
        pts = [(X(x0), Z(y1)), (X(x1), Z(y1)), (X(x1), Z(y0)), (X(x0), Z(y0))]
        if back:
            pts = pts[::-1]
        f = b.bm.faces.new([b.bm.verts.new(Vector((px, y + (0.002 if back else 0.0), pz))) for px, pz in pts])
        for loop in f.loops:
            c = loop.vert.co
            loop[b.uv].uv = atlas.uv(pos, cx + c.x * s - x0, gy - c.z * s - y0)
    return b.object(name, outward=False)


def yard(atlas, img):
    """The shrine's yard seen over the gate's fence and through its opening: the stone lanterns and markers, the hall up
    its steps, the bushes and the trees over them; one cut-out 1.6 m behind the gate, the sky not drawn."""
    crop, cx, gy = (3318, 0, 4128, 868), 3685.0, 868.0
    full = np.asarray(img.convert('RGB')).copy()
    # the roof and the head beam: the trees behind them, taken from the foliage above (the picture's trees over the
    # gate), so turned a little the yard shows leaves where the roof was, not a smear
    top = np.zeros(full.shape[:2], np.uint8)
    roof = np.array([[3361, 478], [3424, 292], [3909, 292], [4009, 478]], np.int32)
    cv2.fillPoly(top, [roof], 1)
    top[474:566, 3484:3886] = 1
    for y in range(286, 570):                  # row by row, top down: each row from leaves 180 px above it
        xs = np.nonzero(top[y])[0]
        full[y, xs] = full[y - 180, xs]
    # the posts and the door (narrow) and the fence (the gate's own fence hides it): painted from round them
    gate = np.zeros(full.shape[:2], np.uint8)
    for x0, y0, x1, y1 in GATE_BOXES:
        if y0 >= 470 and (x1 - x0) < 120 or y0 >= 650:
            gate[y0:y1, x0:x1] = 1
    full = inpaint(full, cv2.dilate(gate, np.ones((5, 5), np.uint8)), 7)
    a = full[crop[1]:crop[3], crop[0]:crop[2]]
    sky = sky_mask(a)
    hi = a.astype(np.int32)
    cloud = (hi.min(-1) > 190) & (hi.max(-1) - hi.min(-1) < 30)
    cloud[300:] = False                       # the stone lanterns below are pale too
    keep = (~(sky | cloud)).astype(np.uint8)
    keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    o = card(atlas, np.dstack([a, keep * 255]), crop, cx, gy, S, 1.6, 'KmShrineYard', both=False)
    return o, dict(id='KM-B12', source='photo/KM1-3 (right): the shrine\'s yard behind the side gate, its lanterns, '
                   'markers, hall and trees (a cut-out)', real_size=[round((crop[2] - crop[0]) / S, 2), 0.01,
                   round(gy / S, 2)], cutout=True, budget=500)


def cutout_model(atlas, src, mask, box, name, info):
    x0, y0, x1, y1 = box
    a = np.asarray(src.convert('RGB'))[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    o = card(atlas, np.dstack([a, m * 255]), box, (x0 + x1) / 2, float(y1), S, 0.0, name)
    info.setdefault('real_size', [round((x1 - x0) / S, 2), 0.01, round((y1 - y0) / S, 2)])
    return o, info


def build_all():
    src, img, masks = painted_picture()
    # no sky on a roof's edge (a roof a few pixels off the drawn one shows tiles, not blue): the shops' and the gate's
    for box in ((1130, 100, 2650, 250), (2555, 40, 3120, 215), (3360, 285, 4010, 480)):
        img = KB.unsky(img, box, pale=True)
    os.makedirs(REVIEW, exist_ok=True)
    img.save(os.path.join(REVIEW, 'painted.jpg'), quality=88)
    atlas = Atlas(ATLAS_W, ATLAS_H)
    models = build(atlas, img)
    models.append(side_gate(atlas, img))
    models.append(yard(atlas, img))
    ys, xs = np.nonzero(masks['stool'])
    models.append(cutout_model(atlas, src, masks['stool'], (int(xs.min()), int(ys.min()), int(xs.max()) + 1, 899),
                               'KmStool', dict(id='KM-A32', source='photo/KM1-3: the soft-serve stand\'s first stool '
                                               '(a cut-out until KM-A32\'s views)', cutout=True, budget=100)))
    models.append(cutout_model(atlas, src, masks['chalkboard'], (2103, 770, 2198, 910), 'KmChalkboard',
                               dict(id='KM-A32', source='photo/KM1-3: the croquette shop\'s chalkboard menu (a cut-out '
                                    'until KM-A32\'s views)', cutout=True, budget=100)))
    models.append(cutout_model(atlas, masks['rickshaw_rgb'], masks['rickshaw'], RICKSHAW, 'KmRickshaw',
                               dict(id='KM-V04', source='photo/KM1-3: the rickshaw by the souvenir shop (a cut-out '
                                    'until KM-V04\'s views)', cutout=True, budget=100)))
    return src, img, atlas, models


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    src, img, atlas, models = build_all()
    atlas_path = os.path.join(OUT, 'KmKomachiAtlas.png')
    atlas.img.save(atlas_path)
    manifest = K.Manifest('Kamakura', None)
    review_mats = {False: KB.unlit(atlas_path), True: KB.unlit(atlas_path, cut=True)}
    game_mats = {}
    for o, info in models:
        o.location = (0, 0, 0)
        cut = bool(info.get('cutout'))
        if cut not in game_mats:
            game_mats[cut] = K.material('KmKomachi' + ('Cut' if cut else ''), atlas_path)
        K.assign(o, game_mats[cut])
        front = K.attach(o, 'Front', (0, -1, 0))
        K.export_model(o, os.path.join(OUT, o.name + '.fbx'))
        manifest.add(o, texture='KmKomachiAtlas.png', tex_px=ATLAS_W, **info)
        bpy.data.objects.remove(front)
        print('%-18s %5d triangles' % (o.name, K.tree_tris(o)))
    manifest.save(os.path.join(OUT, 'Komachi.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Komachi.blend'))
    review(models, review_mats, src)
    if INSTALL:
        installed_path = os.path.join(INSTALL, 'Kamakura.json')
        installed = json.load(open(installed_path))
        for o, info in models:
            shutil.copy(os.path.join(OUT, o.name + '.fbx'), INSTALL)
            installed['models'][o.name] = manifest.data['models'][o.name]
        shutil.copy(atlas_path, INSTALL)
        json.dump(installed, open(installed_path, 'w'), indent=1, ensure_ascii=False)
        print('installed', len(models), 'models in', INSTALL)


def shell_counts(o):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    fins = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bm.free()
    return open_edges, fins


def review(models, mats, src):
    """The strict review (docs/ASSET_REVIEW.md): each model's eight views, its part of the picture, its checks."""
    os.makedirs(os.path.join(REVIEW, 'views'), exist_ok=True)
    os.makedirs(os.path.join(REVIEW, 'source'), exist_ok=True)
    out = {}
    names = KB.AR_CHECK_NAMES
    boxes = dict(KmKomachiGateway=(515, 285, 1040, 812), KmSoftServeStand=(1130, 105, 1845, 900),
                 KmCroquetteShop=(1795, 105, 2210, 900), KmSenbeiShop=(2202, 105, 2645, 900),
                 KmSouvenirShop=(2555, 50, 3175, 900), KmShrineSideGate=(3310, 280, 4128, 872),
                 KmShrineYard=(3318, 0, 4128, 868), KmStool=STOOLS[0], KmChalkboard=CHALKBOARD, KmRickshaw=RICKSHAW)
    for o, info in models:
        cut = bool(info.get('cutout'))
        K.assign(o, mats[cut])
        AR.eight_views(o, os.path.join(REVIEW, 'views', o.name + '.jpg'), KB.render, cell_px=360,
                       title='%s: every side (Right is the street side, as the game sees it)' % o.name)
        src.crop(boxes[o.name]).save(os.path.join(REVIEW, 'source', o.name + '.jpg'), quality=88)
        oe, fins = shell_counts(o)
        tris = K.tree_tris(o)
        card_ = o.name in ('KmShrineYard', 'KmStool', 'KmChalkboard', 'KmRickshaw')
        checks = {
            1: ('pass', 'each part once (looked at in Top and Bottom)'),
            2: ('limit' if oe or fins else 'pass',
                '%d edges with one face, %d with three or more: %s' % (oe, fins, 'a cut-out card, front and back' if card_
                else 'boxes and roof faces without the faces no one sees (their bottoms)')),
            3: ('limit' if card_ else 'pass', 'a flat cut-out: its depth is not modelled' if card_ else
                'boxes and roofs measured off the picture (about 120 px to the metre; the gateway 86)'),
            4: ('limit', 'the street side is the picture itself; the sides, back and roofs away from the street take '
                         'KM-P3\'s boards and tiles in the street\'s colours, or the part\'s own colour (no view of '
                         'their own)'),
            5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget %d), the shared 4096 x 2048 KmKomachiAtlas'
                % (tuple(info['real_size']) + (tris, info.get('budget', 1500)))),
            6: ('pass', 'its outline the picture\'s'),
            7: ('pass', 'no holes in what the street sees'),
            8: ('pass' if o.name not in ('KmSouvenirShop', 'KmSoftServeStand', 'KmSenbeiShop', 'KmCroquetteShop') else
                'limit', 'the stools, the chalkboard and the rickshaw are their own models; the nobori flags and the '
                         'kite sign stay on the fronts they hang against until their views come (KM-A30, A31)'),
            9: ('pass', 'the photographic KM1-3, in KM-0\'s look'),
            10: ('pass', 'solid and whole'),
            11: ('pass', 'no brand or logo: the signs\' words are invented'),
            12: ('pass', 'no wires on it; the sky cut out round the gateway and over the yard'),
            13: ('pass', 'painted out: the stools, the chalkboard, the rickshaw, and the image tool\'s mark (D31)'),
            14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'),
            17: ('n/a', 'one piece'),
        }
        out[o.name] = dict(id=info['id'], sheet=info['source'], size=info['real_size'], tris=tris, motions=[],
                           checks=[[i, names[i - 1], checks[i][0], checks[i][1]] for i in range(1, 18)])
    json.dump(out, open(os.path.join(REVIEW, 'review.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
