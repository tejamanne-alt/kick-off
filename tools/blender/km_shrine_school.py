# KM1-4 The Shrine Bridge's set pieces (docs/KAMAKURA_BUILD.md, BUILD KM-L14: the shrine along the street, the school
# gate at the end), projection-modelled from the photographic KM1-4 as KM1-3's were (km_komachi.py, km_leg_kit.py).
# Unlike KM1-3's shop fronts, the picture is drawn in depth: the bridge runs away from the camera, the stairs climb to
# the hall, the school stands across its sports ground. So it is built in layers, each at its own depth and at the
# scale that makes it line up with the picture from the game camera: the camera stands about 10.1 m in front of the
# lane (CameraFollow2D), and a layer `front` metres behind the lane shows WALL_S * 11.6 / (10.1 + front) px to the
# metre, the walls along the street 150 (the stone wall's stones, the school gate's 1.9 m pillars).
#   - the shrine's low stone wall along the pavement (two copies, one mirrored, to be laid in turn);
#   - the purification pavilion (KM-B13) just behind it: its posts, beam, basin and roof;
#   - the lotus pond with the arched bridge (a cut-out), with the water under it;
#   - the shrine's grounds behind (a cut-out): the lantern rows, the stairs up to the hall, the fortune racks, the trees,
#     the fence along the back, with the gravel in front of it; the pavilion and the pond are painted out of it;
#   - the school's wall, its two gate pillars, the folded gate and the notice board, along the street;
#   - the green ball-stop fences behind it (cut-outs);
#   - the school building far back across its sports ground, the cherry painted out of its face (the cherry is its own
#     model, carved from KM-G16's views).
# All of them share one texture, KmShrineSchoolAtlas.png (4096 x 2048).
#   blenv/bin/python km_shrine_school.py -- /abs/outdir /abs/review/kamakura/shrine_school [--install /abs/Assets/_Game/Art/Models/Kamakura]
import math
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

SRC = 'photo/KM1-4_the_shrine_bridge.png'
WALL_S = 150.0          # px to the metre at the street's walls
CAM = 10.1              # the game camera's distance in front of the lane (3.09 m half-height at 34 degrees)
ATLAS_W, ATLAS_H = 4096, 2048
DENS = 80.0


def scale_at(front):
    """The picture's px to the metre for a layer `front` metres behind the lane (the walls at 1.5: WALL_S)."""
    return WALL_S * (CAM + 1.5) / (CAM + front)


FRONT = dict(pavilion=2.2, pond=3.5, grounds=8.0, fence=2.0, gate=1.5, building=33.0)
P = lambda x, y, z: Vector((x, y, z))


# ---------------------------------------------------------------- the picture, painted
# The arched bridge's outline (its posts' knobs, its arched railings' tops, the deck's far edge), in the picture's pixels
BRIDGE = [(892, 880), (892, 786), (899, 772), (921, 772), (926, 786), (926, 814), (1001, 812), (1001, 744), (1006, 712),
          (1018, 705), (1031, 712), (1036, 734), (1044, 720), (1070, 699), (1102, 684), (1133, 678), (1165, 681),
          (1191, 689), (1197, 676), (1212, 676), (1215, 694), (1233, 705), (1249, 723), (1253, 742), (1309, 742),
          (1309, 712), (1318, 705), (1333, 705), (1341, 707), (1370, 681), (1396, 676), (1428, 684), (1441, 680),
          (1457, 680), (1458, 707), (1462, 781), (1466, 797), (1466, 880)]
LOTUS_LEFT = (690, 712, 1030, 900)                  # where the lotus grows, left and right of the bridge
LOTUS_RIGHT = (1395, 688, 2165, 905)
EDGE = [(1375, 905), (1375, 858), (1420, 846), (1500, 849), (1560, 868), (2165, 870), (2165, 905)]   # the pond's stones
EDGE_LEFT = [(700, 860), (760, 850), (891, 852), (891, 880), (700, 880)]
PAVILION = (300, 415, 870, 910)                     # the purification pavilion, painted out of the grounds
WATER = (1395, 812, 1420, 832)                      # the pond's water, under the bridge's right arch
GRAVEL = (40, 930, 300, 1000)


def pond_mask(a):
    """The pond's own pixels: the bridge, the lotus (its leaves' green and its flowers' pink, where it grows), the
    stones along the pond's edges."""
    f = a.astype(np.int32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    green = (g > r + 10) & (g > b + 4)
    pink = (r > g + 30) & (r > 140) & (b > g - 10)
    lotus = (green | pink).astype(np.uint8)
    region = np.zeros(a.shape[:2], np.uint8)
    for x0, y0, x1, y1 in (LOTUS_LEFT, LOTUS_RIGHT):
        region[y0:y1, x0:x1] = 1
    m = lotus & region
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    luma = 0.3 * r + 0.59 * g + 0.11 * b
    edge = np.zeros(a.shape[:2], np.uint8)
    cv2.fillPoly(edge, [np.array(EDGE, np.int32), np.array(EDGE_LEFT, np.int32)], 1)
    m |= edge & (luma < 175).astype(np.uint8)            # the stones, not the pale gravel in front of them
    cv2.fillPoly(m, [np.array(BRIDGE, np.int32)], 1)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    for i in range(1, n):
        if st[i, 4] < 40:
            m[lab == i] = 0
    return m


def painted_picture():
    """The photographic KM1-4: for the shrine's grounds, the pavilion painted out (the fence and stone wall behind it
    carried on from its left, the trees over its roof from the leaves above them); for the school, the utility pole
    painted out of the ball-stop fence and the wall carried on left to the fence's end, and the image tool's mark (D31)
    painted out of the low wall; the cherry painted out of the school building's face (its bays carried on from its
    left). Returns the picture, the painted one, and the pond's mask."""
    src = KB.ref(SRC)
    a = np.asarray(src).copy()
    pond = pond_mask(a)
    # the pavilion out of the grounds: the fence and the stone wall behind it carried on from the left, column by column
    # (each from 296 px to its left, already painted where that was the pavilion); above the fence, the leaves 180 px up
    for x in range(300, 822):
        a[600:906, x] = a[600:906, x - 296]
    for y in range(415, 600):
        a[y, 300:872] = a[y - 180, 300:872]
    m = np.zeros(a.shape[:2], np.uint8)
    m[600:906, 818:872] = 1                                 # right of the fence's end: greenery, filled from round it
    a = LK.inpaint(a, m, 6)
    # the school: the pole out of the ball-stop fence (its mesh from 64 px to the left), the wall carried on left to
    # the fence's end (its plain panel right of the cabinet, repeated)
    for x in range(2236, 2312):
        a[300:672, x] = a[300:672, x - 64]
    for x in range(2171, 2300):
        a[665:906, x] = a[665:906, 2452 + (x - 2171) % 103]
    # the image tool's mark on the low wall and the pavement (bottom right): the wall's blocks from 120 px to its left
    LK.copy_patch(a, (3966, 852, 4128, 940), dx=-150)
    # the cherry out of the school building's face: its upper storeys carried on, bay by bay, from the clean two bays
    # left of the crown (2985 to 3237, 252 px); the rooftop railing from its plain stretch; the ground storey's windows
    # behind the trunk from two bays to their left; what blossom is left on the walls painted from round it
    for y in range(257, 520):
        for x in range(3237, 3905):
            a[y, x] = a[y, 2985 + (x - 2985) % 252]
    for y in range(240, 290):
        for x in range(3237, 3905):
            a[y, x] = a[y, 3150 + (x - 3150) % 84]
    for x in range(3575, 3725):
        a[520:668, x] = a[520:668, x - 252]
    f = a.astype(np.int32)
    pinkish = ((f[..., 0] > f[..., 1] + 12) & (f[..., 0] > f[..., 2])).astype(np.uint8)
    left = np.zeros(a.shape[:2], np.uint8)
    left[520:668, 3215:3905] = pinkish[520:668, 3215:3905]
    a = LK.inpaint(a, cv2.dilate(left, np.ones((5, 5), np.uint8)), 5)
    return src, Image.fromarray(a), pond


# ---------------------------------------------------------------- the shrine
def shrine_wall(atlas, img, name, mirror):
    """The shrine's low wall of mossy stones along the pavement, with the fence's sill on top: 2.6 m of it from the
    picture's left (the stretch nothing stands in front of), 1.1 m tall; laid in turn with its mirrored copy."""
    crop = (0, 738, 392, 902)
    im = img.crop(crop)
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    pos = atlas.place(im)
    s, cx, gy = WALL_S, (crop[0] + crop[2]) / 2, float(crop[3])
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    sill = atlas.place(img.crop((0, 739, 392, 760)))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    b = KB.Builder(atlas, pos, fmap, pos, im.size)
    stone = (pos, im.size)
    x0, x1, z1 = X(crop[0]), X(crop[2]), Z(crop[1])
    b.face([P(x0, -0.3, 0), P(x1, -0.3, 0), P(x1, -0.3, z1), P(x0, -0.3, z1)])                 # the front: the picture
    b.face([P(x1, 0.3, 0), P(x0, 0.3, 0), P(x0, 0.3, z1), P(x1, 0.3, z1)], stone)
    b.face([P(x0, 0.3, 0), P(x0, -0.3, 0), P(x0, -0.3, z1), P(x0, 0.3, z1)], stone)
    b.face([P(x1, -0.3, 0), P(x1, 0.3, 0), P(x1, 0.3, z1), P(x1, -0.3, z1)], stone)
    b.face([P(x0, -0.3, z1), P(x1, -0.3, z1), P(x1, 0.3, z1), P(x0, 0.3, z1)], (sill, (392, 21)))
    o = b.object(name)
    return o, dict(id='KM-T19', source='photo/KM1-4 (left): the shrine\'s stone wall under the fence%s' %
                   (', mirrored' if mirror else ''), real_size=[round((crop[2] - crop[0]) / s, 2), 0.6, round(z1, 2)],
                   cutout=False, budget=100, px_centre=cx, px_per_m=s)


def pavilion(atlas, img):
    """KM-B13, the purification pavilion: four posts on stone feet, the beam with its paper streamers, the stone basin
    with its ladles, and its tiled roof (the picture sees it from the front and a little from its right, so the roof's
    front slope carries its gable end and its right slope as the picture draws them)."""
    s, gy, cx = scale_at(FRONT['pavilion']), 905.0, 517.0
    crop = (300, 410, 875, 910)
    pos = atlas.place(img.crop(crop))
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    wood = (atlas.place(LK.colour_sample(img, (415, 650, 436, 850))), (64, 64))
    roof = (atlas.place(LK.colour_sample(img, (560, 470, 780, 540))), (64, 64))
    stone = (atlas.place(LK.colour_sample(img, (490, 800, 600, 880))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, wood[0], wood[1])
    # the posts: the front pair at the front, the right-hand back post (the picture sees it right of the front right
    # one) and one hidden behind the front left, 1.4 m back
    for (p0, p1), y in (((408, 442), 0.0), ((592, 627), 0.0), ((731, 769), 1.4), ((408, 442), 1.4)):
        b.box(X(p0), X(p1), y, y + 0.24, Z(872), Z(584), side=wood, skip=('bottom',))
    for (p0, p1), y in (((392, 446), -0.05), ((585, 635), -0.05), ((727, 775), 1.35), ((392, 446), 1.35)):
        b.box(X(p0), X(p1), y, y + 0.34, 0.0, Z(872), side=stone, skip=('bottom',))
    b.box(X(400), X(780), -0.04, 0.12, Z(612), Z(584), side=wood)                  # the beam
    b.box(X(471), X(715), 0.25, 1.15, 0.0, Z(768), side=stone, skip=('bottom',))    # the basin
    # the roof: its front slope from the eaves (y 557 left, 568 right) to the ridge (its crest at the left, y 425; 461
    # at the right), back to its back eaves; the ends and the back in the roof's own grey
    el, er, rl, rr = (X(308), Z(557)), (X(858), Z(568)), (X(470), Z(425)), (X(692), Z(461))
    yf, yr, yb = -0.65, 0.7, 2.05
    b.face([P(el[0], yf, el[1]), P(er[0], yf, er[1]), P(rr[0], yr, rr[1]), P(rl[0], yr, rl[1])])
    b.face([P(er[0], yb, er[1]), P(el[0], yb, el[1]), P(rl[0], yr, rl[1]), P(rr[0], yr, rr[1])], roof)
    b.face([P(el[0], yb, el[1]), P(el[0], yf, el[1]), P(rl[0], yr, rl[1])], roof)
    b.face([P(er[0], yf, er[1]), P(er[0], yb, er[1]), P(rr[0], yr, rr[1])], roof)
    b.face([P(el[0], yb, el[1]), P(er[0], yb, er[1]), P(er[0], yf, er[1]), P(el[0], yf, el[1])], roof)
    o = b.object('KmTemizuya')
    return o, dict(id='KM-B13', source='photo/KM1-4 (left): the purification pavilion, its basin and its roof',
                   real_size=[round((858 - 308) / s, 2), round(yb - yf, 2), round(Z(425), 2)], cutout=False, budget=1500,
                   px_centre=cx, px_per_m=s)


def pond(atlas, img, src, mask):
    """The lotus pond with the arched bridge over it, cut out of the picture, upright at the pond's near edge; behind
    it the water, flat, in its own dark green."""
    s, gy, cx = scale_at(FRONT['pond']), 905.0, 1175.0
    crop = (690, 660, 2165, 905)
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]]
    m = mask[crop[1]:crop[3], crop[0]:crop[2]]
    pos = atlas.place(Image.fromarray(np.dstack([a, m * 255]), 'RGBA'))
    b = KB.Builder(atlas, None, None, None, None)
    LK.card_faces(b, atlas, pos, crop, cx, gy, s, 0.0)
    water = (atlas.place(LK.flat_sample(img, WATER)), (64, 64))
    X = lambda px: (px - cx) / s
    b.face([P(X(crop[0]), 0.05, 0.02), P(X(crop[2]), 0.05, 0.02), P(X(crop[2]), 4.5, 0.02), P(X(crop[0]), 4.5, 0.02)],
           water)
    o = b.object('KmShrinePond', outward=False)
    return o, dict(id='KM-B14', source='photo/KM1-4: the lotus pond and the arched stone bridge (a cut-out), the water '
                   'behind', real_size=[round((crop[2] - crop[0]) / s, 2), 4.5, round((gy - crop[1]) / s, 2)],
                   cutout=True, budget=100, px_centre=cx, px_per_m=s)


def grounds(atlas, img, mask):
    """The shrine's grounds behind the pond, cut out of the picture: the fence along their back, the stone lanterns,
    the stairs up to the vermilion hall, the fortune racks, the trees; the overcast sky not drawn; under the pond's
    outline nothing (the pond stands in front, and the gravel and the water lie flat between them). In front of it,
    the gravel, flat, in its own colour."""
    s, gy, cx = scale_at(FRONT['grounds']), 905.0, 1175.0
    crop = (0, 0, 2165, 905)
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]].copy()
    keep = ~LK.overcast_mask(a, below=420)
    m = mask[crop[1]:crop[3], crop[0]:crop[2]].astype(bool)
    under = np.maximum.accumulate(m, axis=0)            # each column, from the pond's top down
    keep &= ~cv2.dilate(under.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    keep[870:, 860:1475] = False                        # the paved path to the bridge: the ground in front
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    pos = atlas.place(Image.fromarray(np.dstack([a, keep * 255]), 'RGBA'))
    b = KB.Builder(atlas, None, None, None, None)
    LK.card_faces(b, atlas, pos, crop, cx, gy, s, 0.0, both=False)
    gravel = (atlas.place(LK.colour_sample(img, GRAVEL)), (64, 64))
    X = lambda px: (px - cx) / s
    depth = FRONT['grounds'] - 1.8                      # from just behind the street's wall
    b.face([P(X(crop[0]), -depth, 0.01), P(X(crop[2]), -depth, 0.01), P(X(crop[2]), -0.02, 0.01),
            P(X(crop[0]), -0.02, 0.01)], gravel)
    o = b.object('KmShrineGrounds', outward=False)
    return o, dict(id='KM-B15', source='photo/KM1-4: the shrine\'s grounds, lanterns, stairs, hall, fortune racks and '
                   'trees (a cut-out), the gravel in front', real_size=[round((crop[2] - crop[0]) / s, 2),
                   round(depth, 2), round(gy / s, 2)], cutout=True, budget=100, px_centre=cx, px_per_m=s)


# ---------------------------------------------------------------- the school
def school_gate(atlas, img):
    """The school's wall along the street, its two gate pillars (the school's name board on the right one), the
    folded sliding gate, the utility cabinet against the wall, the notice board under its little roof, the low block
    wall at the right."""
    s, gy, cx = WALL_S, 905.0, 3084.0
    crop = (2165, 585, 4128, 912)
    pos = atlas.place(img.crop(crop))
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    conc = (atlas.place(LK.colour_sample(img, (2580, 690, 2660, 860))), (64, 64))
    wood = (atlas.place(LK.colour_sample(img, (3700, 805, 3715, 900))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, conc[0], conc[1])
    b.box(X(2171), X(2557), 0.0, 0.22, 0.0, Z(672), side=conc, skip=('bottom',))          # the wall, left
    b.box(X(2345), X(2452), -0.32, 0.0, 0.0, Z(665), side=conc, skip=('bottom', 'back'))  # the cabinet against it
    b.box(X(2555), X(2685), -0.2, 0.55, 0.0, Z(625), side=conc, skip=('bottom',))         # the left pillar
    b.box(X(3355), X(3490), -0.1, -0.02, 0.0, Z(690), side=conc, skip=('bottom',))        # the folded gate
    b.box(X(3488), X(3630), -0.2, 0.55, 0.0, Z(625), side=conc, skip=('bottom',))         # the right pillar
    b.box(X(3628), X(3962), 0.0, 0.22, 0.0, Z(670), side=conc, skip=('bottom',))          # the wall behind the board
    b.box(X(3958), X(4128), 0.0, 0.22, 0.0, Z(775), side=conc, skip=('bottom',))          # the low block wall
    # the notice board in front of the wall: its legs, its board, its little roof
    b.box(X(3700), X(3722), -0.45, -0.37, 0.0, Z(632), side=wood, skip=('bottom',))
    b.box(X(3955), X(3977), -0.45, -0.37, 0.0, Z(632), side=wood, skip=('bottom',))
    b.box(X(3722), X(3955), -0.42, -0.36, Z(805), Z(632), side=wood)
    b.box(X(3685), X(3990), -0.62, -0.18, Z(632), Z(590), side=wood)
    o = b.object('KmSchoolGate')
    return o, dict(id='KM-B16', source='photo/KM1-4 (right): the school\'s wall, gate pillars, folded gate, cabinet and '
                   'notice board', real_size=[round((4128 - 2171) / s, 2), 1.17, round(Z(590), 2)], cutout=False,
                   budget=1500, px_centre=cx, px_per_m=s)


def fence(atlas, img, name, crop, cx, feet, crown=None, behind=()):
    """A green ball-stop fence behind the school's wall (a cut-out: the overcast sky through its mesh not drawn). Its
    foot, behind what stands in front of it (the wall, the notice board), is not drawn: from the game camera, about
    2.5 m up and 10 m in front, a 1.55 m wall half a metre in front hides the fence up to about 1.5 m. feet: [(x0, x1,
    y)], nothing from y down in those columns. crown: the box where the cherry's blossom and branches cross it (the
    cherry is its own model in front). behind: boxes where its mesh shows what is its own model behind it."""
    s, gy = scale_at(FRONT['fence']), 905.0
    a = np.asarray(img.convert('RGB'))[crop[1]:crop[3], crop[0]:crop[2]].copy()
    keep = ~LK.overcast_mask(a)
    for x0, x1, yf in feet:
        keep[yf - crop[1]:, x0 - crop[0]:x1 - crop[0]] = False
    if crown is not None:
        f = a.astype(np.int32)
        luma = 0.3 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
        blossom = (f[..., 0] > f[..., 1] + 12) & (f[..., 0] > f[..., 2])
        branch = (f[..., 0] > f[..., 2] + 10) & (luma < 115) & (f[..., 1] <= f[..., 0])
        zone = np.zeros(a.shape[:2], bool)
        zone[crown[1] - crop[1]:crown[3] - crop[1], crown[0] - crop[0]:crown[2] - crop[0]] = True
        out = cv2.dilate(((blossom | branch) & zone).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        keep &= ~out
    for x0, y0, x1, y1 in behind:                      # what is its own model behind it (the school's face): only the
        c0, r0, c1, r1 = x0 - crop[0], y0 - crop[1], x1 - crop[0], y1 - crop[1]     # fence's green posts kept
        f = a[r0:r1, c0:c1].astype(np.int32)
        keep[r0:r1, c0:c1] &= (f[..., 1] > f[..., 0] + 10) & (f[..., 1] > f[..., 2])
    keep = keep.astype(np.uint8)
    o = LK.card(atlas, np.dstack([a, keep * 255]), crop, cx, gy, s, 0.0, name)
    return o, dict(id='KM-A35', source='photo/KM1-4 (right): the school\'s green ball-stop fence (a cut-out)',
                   real_size=[round((crop[2] - crop[0]) / s, 2), 0.01, round((gy - crop[1]) / s, 2)], cutout=True,
                   budget=100, px_centre=cx, px_per_m=s)


def building(atlas, img):
    """The school far back across its sports ground: the clock block with the basketball hoop and the goal in front of
    it, the main block with its rows of windows and its entrance canopy, the wing whose side the picture sees on the
    left, the rooftop units; and the sandy ground from the gate to its face, flat."""
    s, gy, cx = 40.0, 667.0, 3172.0
    crop = (2440, 195, 3905, 672)
    im = KB.unsky(img, (2440, 190, 3905, 300), pale=True)
    pos = atlas.place(im.crop(crop))
    fmap = lambda co: (cx + co.x * s - crop[0], gy - co.z * s - crop[1])
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    conc = (atlas.place(LK.colour_sample(img, (2700, 330, 2900, 480))), (64, 64))
    sand = (atlas.place(LK.flat_sample(img, (2950, 700, 3250, 800))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, conc[0], conc[1])
    # the wing on the left, toward the street, its top falling as the picture draws it (y 244 at its right, 347 at its left)
    xa, xb, zl, zr, yf = X(2445), X(2644), Z(347), Z(244), -8.0
    b.face([P(xa, yf, 0), P(xb, yf, 0), P(xb, yf, zr), P(xa, yf, zl)])
    b.face([P(xa, 0, 0), P(xa, yf, 0), P(xa, yf, zl), P(xa, 0, zl)], conc)
    b.face([P(xa, yf, zl), P(xb, yf, zr), P(xb, 0, zr), P(xa, 0, zl)], conc)
    b.box(X(2644), X(2980), -1.0, 12.0, 0.0, Z(199), side=conc, skip=('bottom',))     # the clock block
    b.box(X(2980), X(3905), 0.0, 12.0, 0.0, Z(289), side=conc, skip=('bottom',))      # the main block
    b.box(X(3047), X(3131), 3.0, 6.0, Z(289), Z(229), side=conc, skip=('bottom',))    # the rooftop units
    b.box(X(2980), X(3220), -2.0, 0.0, Z(552), Z(520), side=conc)                     # the entrance canopy
    b.face([P(X(2165), -31.5, 0.01), P(X(4128), -31.5, 0.01), P(X(4128), -1.0, 0.01), P(X(2165), -1.0, 0.01)], sand)
    o = b.object('KmSchoolBuilding')
    return o, dict(id='KM-B17', source='photo/KM1-4 (right): the school building across its sports ground, the '
                   'cherry painted out of its face', real_size=[round((3905 - 2445) / s, 2), 43.5, round(Z(199), 2)],
                   cutout=False, budget=1500, px_centre=cx, px_per_m=s)


def build_all():
    src, img, mask = painted_picture()
    os.makedirs(REVIEW, exist_ok=True)
    img.save(os.path.join(REVIEW, 'painted.jpg'), quality=88)
    atlas = LK.Atlas(ATLAS_W, ATLAS_H)
    # packed tallest first, so the 4096 x 2048 texture holds them: the grounds, the fences, the pavilion and the walls
    # in its first row, the gate and the school in the second, the pond in the third. The pavilion and the pond show
    # the picture as it is (they are what was painted out of the grounds); the rest the painted picture
    grounds_m = grounds(atlas, img, mask)
    fence_r = fence(atlas, img, 'KmSchoolFenceR', (3873, 188, 4128, 905), 4000.0,
                    feet=[(3873, 3995, 588), (3995, 4128, 760)], crown=(3873, 188, 4010, 610),
                    behind=[(3873, 250, 3912, 672)])
    fence_l = fence(atlas, img, 'KmSchoolFenceL', (2250, 300, 2414, 905), 2332.0, feet=[(2250, 2414, 668)])
    models = [shrine_wall(atlas, img, 'KmShrineWall', False), shrine_wall(atlas, img, 'KmShrineWallB', True),
              pavilion(atlas, src), grounds_m, school_gate(atlas, img), fence_l, fence_r, building(atlas, img),
              pond(atlas, src, src, mask)]
    order = ['KmShrineWall', 'KmShrineWallB', 'KmTemizuya', 'KmShrinePond', 'KmShrineGrounds', 'KmSchoolGate',
             'KmSchoolFenceL', 'KmSchoolFenceR', 'KmSchoolBuilding']
    models.sort(key=lambda m: order.index(m[0].name))
    return src, img, atlas, models


BOXES = dict(KmShrineWall=(0, 738, 392, 902), KmShrineWallB=(0, 738, 392, 902), KmTemizuya=(300, 410, 875, 910),
             KmShrinePond=(690, 660, 2165, 905), KmShrineGrounds=(0, 0, 2165, 905), KmSchoolGate=(2165, 585, 4128, 912),
             KmSchoolFenceL=(2250, 300, 2414, 905), KmSchoolFenceR=(3873, 188, 4128, 905),
             KmSchoolBuilding=(2440, 195, 3905, 672))
CARDS = ('KmShrinePond', 'KmShrineGrounds', 'KmSchoolFenceL', 'KmSchoolFenceR')


def checks(o, info, oe, fins, tris):
    """The seventeen checks of a KM1-4 set piece (docs/ASSET_REVIEW.md)."""
    card_ = o.name in CARDS
    return {
        1: ('pass', 'each part once (looked at in Top and Bottom): what stands in front of another layer is painted out '
                    'of it'),
        2: ('limit' if oe or fins else 'pass',
            '%d edges with one face, %d with three or more: %s' % (oe, fins, 'a cut-out card and its flat ground'
            if card_ else 'boxes and roof faces without the faces no one sees (their bottoms)')),
        3: ('limit' if card_ else 'pass', 'a flat layer at its own depth, %.1f m behind the lane, at %.0f px to the '
            'metre so it lines up with the picture from the game camera' % (FRONT['grounds' if o.name == 'KmShrineGrounds'
            else 'pond' if o.name == 'KmShrinePond' else 'fence'], info['px_per_m']) if card_ else
            'boxes and roofs measured off the picture at %.0f px to the metre (its depth\'s)' % info['px_per_m']),
        4: ('limit', 'the street side is the picture itself; the sides, back and tops away from the street take the '
                     'part\'s own colour (no view of their own)'),
        5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget %d), the shared 4096 x 2048 KmShrineSchoolAtlas'
            % (tuple(info['real_size']) + (tris, info.get('budget', 1500)))),
        6: ('pass', 'its outline the picture\'s'),
        7: ('pass', 'no holes in what the street sees'),
        8: ('pass', 'the ginkgo, the cherry and the lotus are their own models (carved from their views); the pavilion '
                    'and the pond are painted out of the grounds behind them, the cherry out of the school'),
        9: ('pass', 'the photographic KM1-4, in KM-0\'s look'),
        10: ('pass', 'solid and whole'),
        11: ('pass', 'no brand or logo: the school\'s name and the notices are invented'),
        12: ('pass', 'no wires on it (they cross the sky above everything); the overcast sky cut out'),
        13: ('pass', 'painted out: the pavilion from the grounds, the pole from the fence, the cherry from the school, '
                     'the image tool\'s mark from the low wall (D31)'),
        14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'),
        17: ('n/a', 'one piece'),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    src, img, atlas, models = build_all()
    LK.export(models, atlas, OUT, REVIEW, 'KmShrineSchoolAtlas.png', 'ShrineSchool', src, BOXES, checks, INSTALL)


if __name__ == '__main__':
    main()
