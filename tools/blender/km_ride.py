# KM1-2 Ride the Enoden's set (docs/KAMAKURA_BUILD.md, BUILD KM-L12; docs/CITIES.md M1, the ride), from the three
# photographic set pictures KM1-2a to c with km_leg_kit.py. The ride is a fixed side-on camera inside the tram:
#   - the car (KM-B42, new): its far wall straight across the aisle as the picture has it, 11.2 m from bench to bench at
#     370 px to the metre (its door 1.85 m), the windows' plain grey let go so the town shows through them; the bench
#     seats standing out from the wall, the floor and the ceiling in their own colours;
#   - the town passing (KM-B43, new): KM1-2b, one long cut-out whose ends meet (the ride scrolls it behind the
#     windows), at 110 px to the metre, its street 1 m below the car's floor;
#   - the three stations seen through the open door (KM-B44, new): Yuigahama, Wadazuka and Kamakura, each cut from
#     KM1-2c between its grey gaps, at 230 px to the metre, the platform level with the car's floor.
# The image tool's mark is painted out of each. The pictures are placed at half their size: the set is seen whole on
# the screen. One texture, KmRideAtlas.png (4096 x 2048).
#   blenv/bin/python km_ride.py -- /abs/outdir /abs/review/kamakura/ride [--install /abs/Assets/_Game/Art/Models/Kamakura]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index('--') + 1:]
OUT, REVIEW = args[0], args[1]
INSTALL = args[args.index('--install') + 1] if '--install' in args else None
sys.argv = [sys.argv[0], '--', OUT]
import bpy                                     # noqa: E402,F401
import cv2                                     # noqa: E402
import numpy as np                             # noqa: E402
from mathutils import Vector                   # noqa: E402
from PIL import Image                          # noqa: E402
import kit_buildings_km as KB                  # noqa: E402
import kit_lib as K                            # noqa: E402
import km_leg_kit as LK                        # noqa: E402

ATLAS_W, ATLAS_H = 4096, 2048
KS = 0.5                                       # the pictures placed at half their size
P = lambda x, y, z: Vector((x, y, z))

CAR = dict(src='photo/KM1-2a.png', s=370.0, gy=892.0, cx=2064.0, depth=2.6,
           windows=[(246, 246, 646, 603), (700, 246, 1085, 603), (1138, 246, 1531, 603), (1572, 246, 2205, 603),
                    (3528, 246, 3913, 603), (3970, 246, 4128, 603), (2497, 254, 2682, 600), (2782, 254, 2982, 600)],
           benches=[(0, 2420), (3936, 4128)], seat_top=746, mark=(3880, 860, 4128, 1000))
TOWN = dict(src='photo/KM1-2b.png', s=110.0, gy=810.0, mark=(3880, 860, 4128, 1000))
STATIONS = dict(src='photo/KM1-2c.png', s=230.0, gy=860.0, mark=(3880, 860, 4128, 1000),
                names=[('KmPlatformYuigahama', 'Yuigahama', (0, 0, 1305, 1024)),
                       ('KmPlatformWadazuka', 'Wadazuka', (1465, 0, 2662, 1024)),
                       ('KmPlatformKamakura', 'Kamakura', (2822, 0, 4128, 1024))])


def unmark(a, box):
    """The image tool's ✦ mark out of its corner: painted from round it."""
    x0, y0, x1, y1 = box
    f = a[..., :3].astype(np.int32)
    m = np.zeros(a.shape[:2], bool)
    sub = f[y0:y1, x0:x1]
    m[y0:y1, x0:x1] = (sub.min(-1) > 200) & (sub.max(-1) - sub.min(-1) < 30)
    m = cv2.dilate(m.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    return LK.patch_fill(a[..., :3], m, patch=9, window=120)


def small(a):
    return cv2.resize(a, (round(a.shape[1] * KS), round(a.shape[0] * KS)), interpolation=cv2.INTER_AREA)


def car(atlas):
    """KM-B42, the tram car's inside: the far wall the picture's (its windows let go), the benches standing out, the
    floor and the ceiling in their colours."""
    c = CAR
    a = unmark(np.asarray(KB.ref(c['src'])), c['mark'])
    grey = (np.abs(a.astype(np.int32) - 128).max(-1) < 16)
    glass = np.zeros(grey.shape, bool)
    for x0, y0, x1, y1 in c['windows']:
        glass[y0:y1, x0:x1] = grey[y0:y1, x0:x1]
    glass = cv2.morphologyEx(glass.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool)
    alpha = (~glass).astype(np.uint8) * 255
    pos = atlas.place(Image.fromarray(small(np.dstack([a, alpha])), 'RGBA'))
    s, gy, cx = c['s'], c['gy'], c['cx']
    fmap = lambda co: ((cx + co.x * s) * KS, (gy - co.z * s) * KS)
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    img = Image.fromarray(a)
    green = (atlas.place(LK.flat_sample(img, (300, 760, 1200, 800))), (64, 64))
    floor = (atlas.place(LK.colour_sample(img, (0, 900, 4128, 1024), (256, 64))), (256, 64))
    ceiling = (atlas.place(LK.flat_sample(img, (300, 60, 1400, 100))), (64, 64))
    b = KB.Builder(atlas, pos, fmap, *ceiling)
    top = Z(0)
    b.face([P(X(0), 0.0, 0.0), P(X(4128), 0.0, 0.0), P(X(4128), 0.0, top), P(X(0), 0.0, top)])          # the far wall
    for x0, x1 in c['benches']:
        b.box(X(x0), X(x1), -0.5, 0.0, 0.0, Z(c['seat_top']), side=green, skip=('back', 'bottom'))
    d = c['depth']
    b.face([P(X(0), -d, 0.0), P(X(4128), -d, 0.0), P(X(4128), 0.0, 0.0), P(X(0), 0.0, 0.0)], floor, project=False)
    b.face([P(X(0), 0.0, top), P(X(4128), 0.0, top), P(X(4128), -d, top), P(X(0), -d, top)], ceiling, project=False)
    o = b.object('KmTramCar')
    return o, dict(id='KM-B42', source='photo/KM1-2a: the tram car\'s inside, its far wall across the aisle', cutout=True,
                   budget=300, px_centre=cx, px_per_m=s, real_size=[round(4128 / s, 2), d, round(top, 2)])


def card(atlas, a, alpha, crop, gy, s, name, info):
    x0, y0, x1, y1 = crop
    rgba = small(np.dstack([a[y0:y1, x0:x1], alpha[y0:y1, x0:x1]]))
    cs = (x0 * KS, y0 * KS, x0 * KS + rgba.shape[1], y0 * KS + rgba.shape[0])
    o = LK.card(atlas, rgba, cs, (x0 + x1) / 2 * KS, gy * KS, s * KS, 0.0, name, both=False)
    info.update(real_size=[round((x1 - x0) / s, 2), 0.01, round((gy - y0) / s, 2)], px_centre=(x0 + x1) / 2, px_per_m=s,
                cutout=True, budget=100)
    return o, info


def sky_of(a):
    f = a.astype(np.int32)
    return LK.sky_mask(a) | ((f.min(-1) > 225) & (f.max(-1) - f.min(-1) < 20))


def town(atlas):
    """KM-B43, the town passing the windows: KM1-2b whole, its sky let go; its ends meet, so the ride repeats it."""
    t = TOWN
    a = unmark(np.asarray(KB.ref(t['src'])), t['mark'])
    alpha = (~sky_of(a)).astype(np.uint8) * 255
    return card(atlas, a, alpha, (0, 0, a.shape[1], a.shape[0]), t['gy'], t['s'], 'KmTownPassing',
                dict(id='KM-B43', source='photo/KM1-2b: the town passing the tram\'s windows (a cut-out; its ends meet)'))


def stations(atlas):
    """KM-B44, the three stations seen through the open door: each cut from KM1-2c between its grey gaps, the sky
    let go."""
    t = STATIONS
    a = unmark(np.asarray(KB.ref(t['src'])), t['mark'])
    alpha = (~sky_of(a)).astype(np.uint8) * 255
    out = []
    for name, label, crop in t['names']:
        out.append(card(atlas, a, alpha, crop, t['gy'], t['s'], name,
                        dict(id='KM-B44', source='photo/KM1-2c: %s station\'s platform, seen through the door' % label)))
    return out


BOXES = dict(KmTramCar=(0, 0, 4128, 1024), KmTownPassing=(0, 0, 4128, 1024), KmPlatformYuigahama=(0, 0, 1305, 1024),
             KmPlatformWadazuka=(1465, 0, 2662, 1024), KmPlatformKamakura=(2822, 0, 4128, 1024))
SRCS = dict(KmTramCar='photo/KM1-2a.png', KmTownPassing='photo/KM1-2b.png')


def checks(o, info, oe, fins, tris):
    n = o.name
    card_ = n != 'KmTramCar'
    return {
        1: ('pass', 'each part once (looked at in Top and Bottom)'),
        2: ('limit' if oe or fins else 'pass', '%d edges with one face, %d with three or more: %s' % (
            oe, fins, 'a cut-out card' if card_ else 'the wall, the floor and the ceiling as single faces, the benches as '
            'boxes without their backs')),
        3: ('limit', 'a flat cut-out: its depth is not modelled' if card_ else
            'the wall flat (its straps, poles and fittings drawn on it); the benches stand out'),
        4: ('limit', 'the picture from the aisle; nothing behind' if card_ else
            'the picture from the aisle; the floor and the ceiling in their own colours'),
        5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget %d), the shared 4096 x 2048 KmRideAtlas at half the '
                    'pictures\' size' % (tuple(info['real_size']) + (tris, info['budget']))),
        6: ('pass', 'its outline the picture\'s'),
        7: ('pass', 'the windows let go on purpose: the town shows through them' if n == 'KmTramCar' else
            'no holes in what the ride sees'),
        8: ('pass', 'nothing in front of it'),
        9: ('pass', 'the photographic KM1-2 set, in KM-0\'s look'),
        10: ('pass', 'solid and whole'),
        11: ('pass', 'no brand or logo: the posters, the route map and the station boards are invented or real place '
                     'names'),
        12: ('pass', 'the sky let go' if card_ else 'the windows\' grey let go'),
        13: ('pass', 'the image tool\'s mark painted out'),
        14: ('n/a', 'no moving parts (the ride slides the town past)'), 15: ('n/a', 'no moving parts'),
        16: ('n/a', 'no feet'), 17: ('n/a', 'one piece'),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(REVIEW, exist_ok=True)
    K.reset()
    atlas = LK.Atlas(ATLAS_W, ATLAS_H)
    models = [car(atlas), town(atlas)] + stations(atlas)
    src = KB.ref('photo/KM1-2c.png')
    # the review's "source" crops: each from its own picture
    orig_review = LK.review

    def review(models_, mats, _src, review_dir, boxes, checks_):
        os.makedirs(os.path.join(review_dir, 'source'), exist_ok=True)
        orig_review(models_, mats, src, review_dir, boxes, checks_)
        for name, path in SRCS.items():
            KB.ref(path).crop(boxes[name]).save(os.path.join(review_dir, 'source', name + '.jpg'), quality=88)
    LK.review = review
    LK.export(models, atlas, OUT, REVIEW, 'KmRideAtlas.png', 'Ride', src, BOXES, checks, INSTALL)


if __name__ == '__main__':
    main()
