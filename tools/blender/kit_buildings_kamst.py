# The KamakuraStreet kit (kit_buildings.py --kit KamakuraStreet): Kamakura's temples and shrines, its street things, the tram
# and the little vehicles, on its own 4096 x 4096 atlas. See kit_buildings_kambase.py for the look and the contract.
#
#   Temples and shrines: a vermilion torii, a small temple gate under a heavy kawara roof, a granite stone lantern, mossy
#     stone steps, a wall of cut Kamakura-ishi tuff (tiles end to end), a rack of ema, a small shrine hall (nagare-zukuri,
#     copper roof gone green).
#   Street: a convex traffic mirror, a green public phone in its booth, a bus stop's timetable pole, two vending machines,
#     tactile paving, a decorated manhole cover, a house-front stand of pots, a laundry pole stand, a corrugated shed.
#   Tram: the little two-car seaside tram (invented green-and-cream livery), a catenary pole, a level crossing's signal and
#     barrier, a segment of single track (tiles end to end).
#   Vehicles (parked and empty): a white kei truck, a kei car, a delivery moped, a jinrikisha.
#
# Axes as the kit's: metres, X along the street, -Y toward the camera, Z up. Unlike the buildings (front-centred), these
# models' origin is the centre of their footprint on the ground; the tram's is the centre of the whole tram on the rail.
# Vehicles' noses point to +X. Every name, sign, label and livery is invented (no brands, no real shrine or temple names);
# the Japanese lettering is painted into the kit's own tiles below (paint()). Materials added here are prefixed 'kt'.
from kit_buildings_kambase import *
from kit_buildings_kambase import _c
from kit_buildings_atlas import _noise, _ss, _mul, _blend
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- the kit's own materials (name: part, colour, uv, grad)
#   'keep' materials sample the kit's tiles through UVs set here: white ones show a tile's own colour, tinted ones multiply
#   a grey weathering tile (wood grain, granite, tuff) by their colour. 'piece' ones take the shared painted-wear map.
KT_MAT = {
    'kttex': (0, (1, 1, 1), 'keep', 0.0), 'kttexg': (0, (1, 1, 1), 'keep', 0.18),
    # timber through the grain tile: silvered, dark-stained, fresh cedar, black lacquer
    'ktsilv': (0, (0.66, 0.64, 0.60), 'keep', 0.18), 'ktdarkw': (0, (0.30, 0.25, 0.21), 'keep', 0.12),
    'ktcedw': (0, (0.74, 0.56, 0.40), 'keep', 0.12), 'ktbrown': (0, (0.46, 0.33, 0.24), 'keep', 0.15),
    # stone through the granite / tuff tiles
    'ktgran': (0, (0.74, 0.73, 0.69), 'keep', 0.12), 'kttuff': (0, (0.74, 0.71, 0.60), 'keep', 0.12),
    # flat colours
    'ktmoss': (0, (0.33, 0.45, 0.19), 'white', 0.35), 'ktmossl': (0, (0.46, 0.56, 0.23), 'white', 0.3),
    'ktsoffit': (0, (0.22, 0.19, 0.17), 'white', 0.0), 'ktkawad': (0, (0.30, 0.32, 0.35), 'piece', 0.0),
    'ktkawa': (0, (0.40, 0.42, 0.46), 'white', 0.1), 'ktcopper': (0, (0.40, 0.62, 0.54), 'white', 0.1),
    'ktgold': (0, (0.78, 0.62, 0.30), 'white', 0.0), 'ktrope': (0, (0.80, 0.70, 0.46), 'white', 0.15),
    'ktshide': (0, (0.97, 0.97, 0.95), 'white', 0.0), 'ktpurple': (0, (0.42, 0.22, 0.48), 'white', 0.0),
    'ktplaster': (0, (0.90, 0.88, 0.82), 'piece', 0.0), 'ktred': (0, (0.78, 0.10, 0.08), 'white', 0.0),
    'ktlamp': (0, (0.55, 0.06, 0.05), 'white', 0.0), 'ktyel': (0, (0.98, 0.78, 0.10), 'white', 0.0),
    'ktblk': (0, (0.07, 0.07, 0.075), 'white', 0.0), 'ktorange': (0, (0.94, 0.46, 0.13), 'piece', 0.0),
    'ktgalv': (0, (0.70, 0.72, 0.72), 'piece', 0.0), 'ktconc': (0, (0.70, 0.69, 0.66), 'piece', 0.0),
    'ktconcd': (0, (0.52, 0.51, 0.49), 'white', 0.2), 'ktgrey': (0, (0.58, 0.60, 0.62), 'white', 0.0),
    'ktgreyd': (0, (0.30, 0.31, 0.33), 'white', 0.0), 'ktmirror': (0, (0.80, 0.84, 0.88), 'white', 0.0),
    # the phone, the vending machines
    'ktphg': (0, (0.24, 0.56, 0.36), 'piece', 0.0), 'ktphgrey': (0, (0.66, 0.68, 0.70), 'white', 0.0),
    'ktvend1': (0, (0.10, 0.52, 0.56), 'piece', 0.0), 'ktvend2': (0, (0.60, 0.50, 0.78), 'piece', 0.0),
    'ktcream': (0, (0.95, 0.92, 0.84), 'piece', 0.0), 'ktbinb': (0, (0.20, 0.36, 0.62), 'white', 0.15),
    # the tram: green and cream (grime-projected), its roof and running gear
    'kttg': (0, (0.13, 0.36, 0.25), 'grime', 0.0), 'kttc': (0, (0.94, 0.90, 0.77), 'grime', 0.0),
    'kttroof': (0, (0.47, 0.48, 0.48), 'piece', 0.0), 'ktbogie': (0, (0.16, 0.16, 0.17), 'white', 0.2),
    'ktglassd': (0, (0.16, 0.20, 0.24), 'white', 0.0), 'ktrubber': (0, (0.10, 0.10, 0.11), 'white', 0.0),
    'ktsteel': (0, (0.50, 0.50, 0.50), 'white', 0.1), 'ktrail': (0, (0.52, 0.45, 0.40), 'white', 0.3),
    'ktchrome': (0, (0.80, 0.81, 0.82), 'white', 0.0), 'ktlight': (0, (1.0, 0.97, 0.86), 'white', 0.0),
    'ktinsul': (0, (0.58, 0.40, 0.30), 'white', 0.0),
    # vehicles
    'ktkeiw': (0, (0.92, 0.92, 0.90), 'piece', 0.0), 'ktkeic': (0, (0.74, 0.84, 0.80), 'piece', 0.0),
    'ktbumper': (0, (0.30, 0.31, 0.32), 'white', 0.0), 'ktscoot': (0, (0.86, 0.84, 0.76), 'piece', 0.0),
    'ktseatred': (0, (0.70, 0.12, 0.12), 'white', 0.1), 'ktlacq': (0, (0.10, 0.09, 0.09), 'white', 0.0),
    'kthood': (0, (0.12, 0.12, 0.13), 'white', 0.1), 'ktrustp': (0, (0.50, 0.28, 0.16), 'white', 0.0),
    # plants and pots
    'ktpotb': (0, (0.14, 0.14, 0.14), 'white', 0.2), 'ktpott': (0, (0.70, 0.38, 0.24), 'white', 0.2),
    'ktpotg': (0, (0.42, 0.40, 0.36), 'white', 0.1), 'ktbamboo': (0, (0.76, 0.68, 0.44), 'white', 0.1),
    'ktpine': (0, (0.20, 0.34, 0.20), 'white', 0.3), 'ktmg': (0, (0.36, 0.40, 0.86), 'white', 0.0),
    'ktmgp': (0, (0.78, 0.40, 0.72), 'white', 0.0), 'ktleaf': (0, (0.30, 0.50, 0.24), 'white', 0.3),
    'ktwire': (0, (0.72, 0.73, 0.74), 'white', 0.0), 'ktemaw': (0, (0.86, 0.76, 0.58), 'white', 0.0), 'ktpeg': (0, (0.30, 0.62, 0.80), 'white', 0.0),
}
for _k, _v in KT_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1


# ================================================================ helpers
def tx(bm, region, margin=0.01):
    """Box-projected UVs into a tile, normalised to the piece's own bounds (weathering tiles)."""
    uv_box(bm, bm.faces[:], region, margin)
    return bm


def tadd(B, bm, region, margin=0.01):
    return B.add(tx(bm, region, margin))


def plane_uv(bm, region, ax, ay, lo, hi, margin=0.0):
    """Planar UVs into a tile: s from coordinate ax over [lo[0], hi[0]], t from ay over [lo[1], hi[1]]."""
    lu = L(bm)[3]
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv(region, (co[ax] - lo[0]) / (hi[0] - lo[0]), (co[ay] - lo[1]) / (hi[1] - lo[1]), margin)
    return bm


def quad(B, pts, region, normal, st=((0, 0), (1, 0), (1, 1), (0, 1)), mat='kttex', shade=1.0):
    """One textured quad (corners in order) with its tile corners st."""
    mb = MB()
    m = {tuple(map(float, p)): s for p, s in zip(pts, st)}
    mb.face(pts, mat, normal, shade, lambda co: reg_uv(region, *m[min(m, key=lambda q: (Vector(q) - co).length)], 0.0))
    return B.add(mb.bm())


def yquad(B, x0, x1, z0, z1, y, region, facing=-1, mat='kttex'):
    """A textured panel in the plane y facing -Y (facing=-1) or +Y."""
    if facing < 0:
        return quad(B, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], region, (0, -1, 0), mat=mat)
    return quad(B, [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)], region, (0, 1, 0), mat=mat)


def xquad(B, y0, y1, z0, z1, x, region, facing=1, mat='kttex'):
    """A textured panel in the plane x facing +X (facing=1) or -X."""
    if facing > 0:
        return quad(B, [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], region, (1, 0, 0), mat=mat)
    return quad(B, [(x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1)], region, (-1, 0, 0), mat=mat)


def bx(lo, hi, mat):
    """A plain box without its bottom (10 triangles): small blocks, brackets, slats."""
    return box(lo, hi, mat, skip=('-z',))


def cyl(x, y, z0, z1, r, mat, n=10, sm=1, caps=(True, True)):
    prof = ([(0.0, z0)] if caps[0] else []) + [(r, z0), (r, z1)] + ([(0.0, z1)] if caps[1] else [])
    bm, _ = lathe(prof, n, mat, sm=sm)
    return xform(bm, T(x, y, 0))


def disc_y(x, y, z, r, t, mat, n=12, facing=-1, back=False):
    """A disc (wheel, lamp, tile end) with its axis along Y, front face toward facing (its back left open unless back)."""
    bm, _ = lathe(([(0.0, 0.0)] if back else []) + [(r, 0.0), (r, t), (0.0, t)], n, mat, sm=0)
    xform(bm, T(x, y, z) @ R(math.pi / 2 * (1 if facing < 0 else -1), 'X'))
    return bm


def wheel(B, x, y, z, r, w, tyre='ktrubber', hub='ktchrome', n=14, hub_r=0.55):
    """A tyre (a short drum with rounded shoulders) and its hub caps, axis along Y."""
    t, _ = lathe([(0.0, -w / 2), (r * 0.9, -w / 2), (r, -w * 0.3), (r, w * 0.3), (r * 0.9, w / 2), (0.0, w / 2)], n, tyre, sm=1)
    xform(t, T(x, y, z) @ R(math.pi / 2, 'X')); B.add(t)
    for s in (-1, 1):
        h, _ = lathe([(0.0, 0.0), (r * hub_r, 0.0), (r * hub_r * 0.8, 0.012), (0.0, 0.016)], 8, hub)
        xform(h, T(x, y + s * (w / 2 + 0.001), z) @ R(-s * math.pi / 2, 'X')); B.add(h)


def moss(B, x, y, z, rx, ry, rz=0.03, seed=0, mat='ktmoss'):
    B.add(blob((x, y, z), (rx, ry, rz), mat, 6, 2, seed, 0.25))


def ttris(B):
    return sum(sum(len(f.verts) - 2 for f in p.faces) for p in B.pieces)


# ---------------------------------------------------------------- roofs
def slope_prof(y0, z0, y1, z1, n=5, curve=0.35, up=0.0):
    """A roof slope's profile from the ridge (y0, z0) to the eave (y1, z1), concave (steeper at the ridge, the Japanese
    'sori'), its last stretch lifted by up (the eave's upturn)."""
    pts = []
    for i in range(n + 1):
        s = i / n
        f = s + curve * s * (1 - s)
        pts.append((y0 + (y1 - y0) * s, z0 + (z1 - z0) * f + up * max(0.0, s - 0.7) ** 2 / 0.09))
    return pts


def roof_slope(B, x0, x1, prof, t, region, mat='kttex', under='ktsoffit', edge='ktkawad', ends='ktdarkw'):
    """A roof slab over x0..x1 following prof (ridge first, eave last) in the Y-Z plane, t thick: its top textured with a
    tile (s along X, t up the slope), the underside, the eave's edge and the two ends."""
    mb = MB()
    n = len(prof)
    sgn = 1 if prof[-1][0] > prof[0][0] else -1
    acc = [0.0]
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]): acc.append(acc[-1] + math.hypot(yb - ya, zb - za))
    tot = acc[-1]
    for i in range(n - 1):
        (ya, za), (yb, zb) = prof[i], prof[i + 1]
        ta, tb = 1 - acc[i] / tot, 1 - acc[i + 1] / tot
        pts = [(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)]
        st = [(0, ta), (1, ta), (1, tb), (0, tb)]
        mm = {p: s for p, s in zip(pts, st)}
        mb.face(pts, mat, (0, sgn * 0.3, 1), 1.0,
                lambda co, mm=mm: reg_uv(region, *mm[min(mm, key=lambda q: (Vector(q) - co).length)], 0.0))
        mb.face([(x0, ya, za - t), (x1, ya, za - t), (x1, yb, zb - t), (x0, yb, zb - t)], under, (0, 0, -1), 0.8)
        for x, e in ((x0, -1), (x1, 1)):
            mb.face([(x, ya, za), (x, yb, zb), (x, yb, zb - t), (x, ya, za - t)], ends, (e, 0, 0), 0.9)
    ye, ze = prof[-1]
    mb.face([(x0, ye, ze), (x1, ye, ze), (x1, ye, ze - t), (x0, ye, ze - t)], edge, (0, sgn, 0), 1.0)
    return B.add(mb.bm())


def barge(B, x, prof, t, h=0.28, w=0.07, mat='ktdarkw'):
    """A bargeboard (hafu) along a slope's end at x: a board hanging h below the roof's top edge."""
    mb = MB()
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
        for xx, e in ((x - w / 2, -1), (x + w / 2, 1)):
            mb.face([(xx, ya, za + 0.02), (xx, yb, zb + 0.02), (xx, yb, zb - h), (xx, ya, za - h)], mat, (e, 0, 0), 1.0)
        mb.face([(x - w / 2, ya, za - h), (x + w / 2, ya, za - h), (x + w / 2, yb, zb - h), (x - w / 2, yb, zb - h)], mat, (0, 0, -1), 0.8)
    ye, ze = prof[-1]
    mb.face([(x - w / 2, ye, ze + 0.02), (x + w / 2, ye, ze + 0.02), (x + w / 2, ye, ze - h), (x - w / 2, ye, ze - h)], mat, None, 1.0)
    bm = mb.bm()
    return B.add(fix_normals(bm))


def tile_ends(B, x0, x1, y, z, pitch, r=0.075, facing=-1, mat='ktkawa'):
    """The round end tiles (noki-gawara) along an eave, one per row of round tiles, and the flat tiles' lip between."""
    n = max(1, int(round((x1 - x0) / pitch)))
    for k in range(n):
        x = x0 + (k + 0.5) * (x1 - x0) / n
        B.add(disc_y(x, y, z, r, 0.06, mat, 8, facing))
    B.add(cbox2((x0, y - 0.03, z - 0.09), (x1, y + 0.03, z - 0.03), 0.01, 'ktkawad'))


def ridge(B, x0, x1, y, z, h=0.5, w=0.42, onigawara=True, mat='ktkawad', cap='ktkawa'):
    """A tiled ridge (munagawara): stacked courses, a round cap tile along the top, ogre tiles at the ends."""
    B.add(cbox2((x0, y - w / 2, z - 0.1), (x1, y + w / 2, z + h * 0.45), 0.02, mat))
    B.add(cbox2((x0 + 0.05, y - w * 0.36, z + h * 0.45), (x1 - 0.05, y + w * 0.36, z + h * 0.82), 0.02, mat))
    B.add(tube([(x0 + 0.05, y, z + h * 0.82), (x1 - 0.05, y, z + h * 0.82)], w * 0.22, cap, 8))
    if onigawara:
        for x, s in ((x0, -1), (x1, 1)):
            pts = [(-w * 0.85, 0.0), (w * 0.85, 0.0), (w * 0.95, h * 1.1), (w * 0.6, h * 1.5), (0.0, h * 1.62), (-w * 0.6, h * 1.5),
                   (-w * 0.95, h * 1.1)]
            bm = extrude_poly(pts, 0.16, mat, back=True)
            xform(bm, T(x - s * 0.02, y, z - 0.05) @ R(math.pi / 2, 'Y') @ R(math.pi / 2, 'Z') @ T(0, 0, -0.08))
            B.add(fix_normals(bm))


# ================================================================ tile painters (numpy: f(U, V, w, h), V up)
def pnoise(U, V, cx, cy, seed):
    """Smooth value noise, periodic across U (cx cells), cy cells up V."""
    r = np.random.default_rng(seed).random((cy + 2, cx))
    x = U * cx; y = np.clip(V, -0.5, 1.5) * cy + 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    ya = np.clip(y0, 0, cy + 1); yb = np.clip(y0 + 1, 0, cy + 1)
    xa = x0 % cx; xb = (x0 + 1) % cx
    a = r[ya, xa] * (1 - fx) + r[ya, xb] * fx
    b = r[yb, xa] * (1 - fx) + r[yb, xb] * fx
    return (a * (1 - fy) + b * fy).astype(np.float32)


def fbm(U, V, cx, cy, seed, oct=3):
    v = np.zeros(U.shape, np.float32); a = 1.0; tot = 0
    for o in range(oct):
        v += a * pnoise(U, V, cx * 2 ** o, cy * 2 ** o, seed + o * 17); tot += a; a *= 0.5
    return v / tot


def _hash(a, b, s=0.0):
    t = np.sin(a * 12.9898 + b * 78.233 + s) * 43758.5453
    return t - np.floor(t)


def _rgb(U, c):
    return np.ones(U.shape + (3,), np.float32) * np.array(c, np.float32)


def t_grain(U, V, w, h):
    """Weathered wood, grey: grain streaks along V, fine dark lines, a few checks (drying cracks) and knots, darker toward
    the foot. A multiplier: the faces' colours make it silver-grey, dark-stained or fresh cedar."""
    n1 = pnoise(U, V, 30, 3, 71); n2 = pnoise(U, V, 90, 5, 72); n3 = fbm(U, V, 5, 5, 73)
    v = 0.84 + 0.10 * n1 + 0.06 * (n2 - 0.5) + 0.06 * (n3 - 0.5)
    g = np.sin(2 * np.pi * (U * 34 + 1.4 * n3 + 0.5 * n1))
    v *= 1 - 0.14 * _ss(0.8, 1.0, g)
    rng = np.random.default_rng(74)
    for k in range(9):
        cx = rng.uniform(0, 1); v0 = rng.uniform(0, 0.7); L = rng.uniform(0.1, 0.35)
        m = _ss(0.004, 0.0, np.abs(U - cx - 0.004 * np.sin(V * 40))) * (V > v0) * (V < v0 + L)
        v *= 1 - 0.35 * m
    for k in range(4):
        cx, cy = rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9)
        d = np.hypot((U - cx) * w, (V - cy) * h * 0.5)
        v *= 1 - 0.3 * _ss(5, 1, d)
    v *= 1 - 0.18 * _ss(0.15, 0.0, V)
    return np.stack([v * 1.0, v * 0.985, v * 0.96], -1)


def t_vermil(U, V, w, h):
    """Vermilion paint on a torii's timber: sun-faded toward orange-pink in patches, grime rising from the foot, black mould
    streaks from the top, chips down to grey wood."""
    base = _rgb(U, (0.84, 0.25, 0.13))
    n1 = fbm(U, V, 4, 8, 81); n2 = pnoise(U, V, 60, 120, 82); n3 = pnoise(U, V, 12, 30, 83)
    base = _blend(base, _ss(0.5, 0.75, n1), (0.92, 0.46, 0.32), 0.65)
    base *= (0.94 + 0.08 * n3)[..., None]
    base = _mul(base, _ss(0.3, 0.0, V) * (0.5 + 0.5 * n3), (0.55, 0.42, 0.38), 0.75)
    rng = np.random.default_rng(84)
    for k in range(14):
        cx = rng.uniform(0, 1); L = rng.uniform(0.15, 0.6); wd = rng.uniform(0.006, 0.02)
        m = _ss(wd, 0.0, np.abs(U - cx)) * _ss(1 - L, 1.0, V)
        base = _mul(base, m, (0.45, 0.32, 0.30), 0.6)
    chips = (n2 > 0.86) * (0.4 + 0.6 * n3)
    base = _blend(base, chips, (0.55, 0.50, 0.45), 0.85)
    return base


def t_lacq(U, V, w, h):
    """Black lacquer, weathered: dull grey bloom in patches, pale salt streaks from the top."""
    base = _rgb(U, (0.10, 0.095, 0.09))
    n1 = fbm(U, V, 6, 4, 91); n2 = pnoise(U, V, 40, 20, 92)
    base = _blend(base, _ss(0.55, 0.8, n1), (0.26, 0.25, 0.24), 0.6)
    base = _blend(base, (n2 > 0.8) * 0.5, (0.32, 0.30, 0.28), 0.5)
    return base


def stone_mul(tint, seed, moss_amt=1.0, layers=False):
    """Granite (or Kamakura-ishi tuff with its layers and pits) as a multiplier: grains, mottling, dark lichen, and moss
    gathered at the foot, the top and the ends of each piece."""
    def f(U, V, w, h):
        r = np.random.default_rng(seed)
        g = r.normal(0, 1, U.shape).astype(np.float32)
        n1 = fbm(U, V, 6, 6, seed + 1); n2 = pnoise(U, V, 30, 30, seed + 2); n3 = fbm(U, V, 3, 3, seed + 3)
        v = 0.86 + 0.07 * (n1 - 0.5) + 0.035 * g
        if layers:
            v *= 1 - 0.05 * (np.sin(V * 38 + n1 * 4) * 0.5 + 0.5)
            v *= 1 - 0.3 * (n2 > 0.82) * (r.random(U.shape) > 0.4)
        else:
            v = np.where(r.random(U.shape) > 0.985, v * 0.55, v)
            v = np.where(r.random(U.shape) > 0.99, np.minimum(v * 1.12, 1.0), v)
        sub = np.stack([v, v, v], -1) * np.array(tint, np.float32)
        sub = _mul(sub, _ss(0.6, 0.8, n3) * 0.8, (0.62, 0.62, 0.60), 0.7)
        edge = np.maximum.reduce([_ss(0.28, 0.0, V), _ss(0.82, 1.0, V) * 0.8, _ss(0.12, 0.0, U), _ss(0.88, 1.0, U)])
        m = _ss(0.55, 0.8, n1 * 0.55 + n2 * 0.2 + edge * 0.6) * moss_amt
        sub = _mul(sub, m, (0.50, 0.70, 0.36), 0.95)
        sub = _mul(sub, _ss(0.75, 0.95, n2) * m, (0.80, 0.95, 0.60), 0.6)
        return sub
    return f


def t_tuffwall(U, V, w, h):
    """A retaining wall of cut Kamakura-ishi (the town's soft green-grey tuff) 4.0 by 1.4 m, periodic across its length so the
    segments tile: running-bond blocks 0.8 x 0.35, eroded soft at the arrises, pitted, the joints filled with soil and moss,
    moss thick along the top and in damp blotches, dark water stains run down from the coping."""
    X = U * 4.0; Z = V * 1.4
    course = np.floor(Z / 0.35); off = (course % 2) * 0.4
    xb = X + off; idx = np.floor(xb / 0.8)
    du = xb - idx * 0.8; dz = Z - course * 0.35
    d = np.minimum(np.minimum(du, 0.8 - du), np.minimum(dz, 0.35 - dz))
    tone = _hash(idx % 5, course)
    tone2 = _hash(idx % 5 + 3.1, course + 1.7)
    base = np.array((0.66, 0.64, 0.51), np.float32)
    col = base * (0.84 + 0.26 * tone)[..., None]
    col = _blend(col, (tone2 > 0.7).astype(np.float32), (0.60, 0.62, 0.55), 0.5)
    col = _blend(col, (tone2 < 0.2).astype(np.float32), (0.70, 0.62, 0.46), 0.4)
    n1 = fbm(U, V, 16, 6, 101); n2 = pnoise(U, V, 160, 56, 102); n3 = fbm(U, V, 6, 2, 103)
    col *= (0.9 + 0.16 * n1)[..., None]
    col *= (1 - 0.25 * (n2 > 0.78))[..., None]
    col *= (1 - 0.05 * (np.sin(Z * 70 + n1 * 3) * 0.5 + 0.5))[..., None]
    arr = _ss(0.05, 0.0, d)
    col = _mul(col, arr, (0.62, 0.60, 0.52), 0.6)
    joint = _ss(0.018 + 0.01 * n1, 0.006, d)
    col = _blend(col, joint, (0.20, 0.19, 0.14), 0.95)
    mz = np.maximum(_ss(0.75, 1.0, V), _ss(0.25, 0.0, V) * 0.7)
    mm = _ss(0.5, 0.75, n1 * 0.5 + n3 * 0.35 + mz * 0.55 + _ss(0.06, 0.0, d) * 0.3)
    mcol = np.where((n2 > 0.5)[..., None], np.array((0.34, 0.46, 0.18)), np.array((0.46, 0.55, 0.22)))
    col = col * (1 - mm[..., None]) + mcol * mm[..., None] * (0.85 + 0.25 * n1)[..., None]
    rng = np.random.default_rng(104)
    for k in range(16):
        cx = rng.uniform(0, 1); L = rng.uniform(0.2, 0.75); wd = rng.uniform(0.01, 0.03)
        dx = np.minimum(np.abs(U - cx), 1 - np.abs(U - cx))
        m = _ss(wd, 0.0, dx + 0.01 * np.sin(V * 30)) * _ss(1 - L, 1.0, V) * (1 - mm)
        col = _mul(col, m, (0.55, 0.55, 0.50), 0.7)
    return col


def kawara(ncol, nrow, base=(0.36, 0.38, 0.42)):
    """Grey glazed hongawara seen down the slope: ncol rows of round tiles over the flat channel tiles, nrow courses, every
    tile its own glaze, lichen freckles, moss in the lowest channels, rain streaks."""
    def f(U, V, w, h):
        cu = (U * ncol) % 1.0; col = np.floor(U * ncol)
        rv = V * nrow; row = np.floor(rv); fv = rv - row
        d = np.abs(cu - 0.5)
        rnd = d < 0.2
        cy = np.sqrt(np.clip(1 - (d / 0.2) ** 2, 0, 1))
        lt = np.where(rnd, 0.52 + 0.55 * cy, 0.78 - 0.25 * _ss(0.32, 0.2, d))
        lt = lt * np.where(rnd, 1 - 0.3 * _ss(0.06, 0.0, fv), 1 - 0.35 * _ss(0.08, 0.0, fv))
        tone = _hash(col, row)
        lt = lt * (0.9 + 0.18 * tone)
        c = np.array(base, np.float32)[None, None] * lt[..., None]
        c = _blend(c, (tone > 0.85).astype(np.float32) * rnd, (0.42, 0.46, 0.52), 0.5)
        n1 = fbm(U, V, 8, 8, 111); n2 = pnoise(U, V, 120, 120, 112)
        c = _blend(c, (n2 > 0.9) * (n1 > 0.5) * 1.0, (0.52, 0.53, 0.47), 0.45)
        c = _blend(c, (~rnd) * _ss(0.55, 0.8, n1) * _ss(0.45, 0.0, V), (0.30, 0.40, 0.18), 0.8)
        c *= (1 - 0.12 * _ss(0.5, 0.8, pnoise(U, V, 50, 3, 113)))[..., None]
        return c
    return f


def t_copper(U, V, w, h):
    """A copper roof gone green: verdigris blotched blue-green and darker, brown where the rain doesn't wash it, the standing
    seams down the slope and the sheets' cross joints."""
    n1 = fbm(U, V, 6, 6, 121); n2 = pnoise(U, V, 40, 6, 122); n3 = pnoise(U, V, 200, 30, 123)
    c = _rgb(U, (0.42, 0.60, 0.53))
    c = _blend(c, _ss(0.5, 0.75, n1), (0.30, 0.47, 0.44), 0.7)
    c = _blend(c, _ss(0.3, 0.0, V) * pnoise(U, V, 30, 4, 124), (0.22, 0.30, 0.30), 0.5)
    c = _blend(c, _ss(0.62, 0.85, n2) * _ss(0.6, 1.0, V), (0.42, 0.36, 0.26), 0.6)
    c *= (0.94 + 0.08 * n3)[..., None]
    su = (U * 26) % 1.0
    c *= (1 - 0.35 * _ss(0.05, 0.0, np.minimum(su, 1 - su)) + 0.15 * _ss(0.09, 0.05, np.abs(su - 0.06)))[..., None]
    sv = (V * 9) % 1.0
    c *= (1 - 0.2 * _ss(0.03, 0.0, sv))[..., None]
    return np.clip(c, 0, 1)


def t_corr(U, V, w, h):
    """Corrugated galvanized sheet gone dull: the corrugations (light crest, dark trough), rust blooming up from the foot and
    bleeding down from the fixings, a few panels redder than others."""
    n1 = fbm(U, V, 6, 4, 131); n2 = pnoise(U, V, 60, 40, 132); n3 = pnoise(U, V, 4, 1, 133)
    cr = np.sin(2 * np.pi * U * 28)
    c = _rgb(U, (0.62, 0.64, 0.64)) * (0.86 + 0.14 * cr)[..., None] * (0.92 + 0.1 * n1)[..., None]
    rust = _ss(0.35, 0.0, V) * (0.4 + 0.6 * n1) + _ss(0.65, 0.85, n1 * 0.6 + n3 * 0.5) * 0.7
    c = _blend(c, np.clip(rust, 0, 1) * (0.7 + 0.3 * n2), (0.55, 0.30, 0.16), 0.85)
    rng = np.random.default_rng(134)
    for zr in (0.95, 0.52, 0.1):
        for k in range(14):
            cx = rng.uniform(0, 1); L = rng.uniform(0.05, 0.3)
            m = _ss(0.012, 0.0, np.abs(U - cx)) * _ss(zr - L, zr, V) * (V < zr + 0.01)
            c = _blend(c, m * 0.8, (0.50, 0.26, 0.14), 0.7)
    c *= (0.9 + 0.1 * (cr * 0.5 + 0.5))[..., None]
    return np.clip(c, 0, 1)


def t_ballast(U, V, w, h):
    """Ballast: angular grey stones, a few browner, rust dust between the rails."""
    S = 46.0
    x = U * S * (w / h); y = V * S
    xi = np.floor(x); yi = np.floor(y)
    best = np.full(U.shape, 9.0); second = np.full(U.shape, 9.0); idv = np.zeros(U.shape)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx = xi + dx; cy = yi + dy
            px = cx + _hash(cx, cy, 1.0); py = cy + _hash(cx, cy, 2.0)
            dd = np.maximum(np.abs(x - px), np.abs(y - py)) * 0.6 + np.hypot(x - px, y - py) * 0.4
            nb = dd < best
            second = np.where(nb, best, np.minimum(second, dd)); idv = np.where(nb, _hash(cx, cy, 3.0), idv)
            best = np.minimum(best, dd)
    edge = second - best
    v = (0.62 + 0.3 * idv) * (0.75 + 0.25 * _ss(0.0, 0.25, edge)) * (1 - 0.25 * _ss(0.6, 0.0, 1 - best))
    c = np.stack([v, v * 0.98, v * 0.95], -1)
    c = _mul(c, (idv > 0.85).astype(np.float32), (0.86, 0.78, 0.68), 0.8)
    mid = _ss(0.36, 0.2, np.abs(V - 0.5))
    c = _mul(c, mid * (0.5 + 0.5 * pnoise(U, V, 20, 6, 141)), (0.78, 0.62, 0.50), 0.6)
    c *= (1 - 0.35 * _ss(0.25, 0.0, edge))[..., None]
    return np.clip(c, 0, 1)


# ================================================================ tile painters (PIL: draw(dr, w, h, k), y down)
def _jt(dr, x, y, s, size, ink, anchor='mm', stroke=0):
    f = SG._font(SG.KANA, max(6, int(size)))
    if f is None: return
    dr.text((x, y), s, font=f, fill=_c(ink), anchor=anchor, stroke_width=int(stroke), stroke_fill=_c(ink))


def _jfit(dr, s, size, maxw):
    size = int(size)
    f = SG._font(SG.KANA, size)
    while f is not None and size > 8 and dr.textlength(s, font=f) > maxw:
        size -= 1; f = SG._font(SG.KANA, size)
    return size


SMALL_KANA = set('ぁぃぅぇぉっゃゅょァィゥェォッャュョヮ')


def _jv(dr, cx, y0, y1, s, ink, maxw, stroke=0):
    """Vertical lettering from y0 to y1, centred on cx, as Japanese is set top to bottom: the long-vowel mark ー turned
    upright, small kana set up and to the right in their cell."""
    n = len(s)
    size = min((y1 - y0) / n * 0.92, maxw)
    for i, ch in enumerate(s):
        cy = y0 + (i + 0.5) * (y1 - y0) / n
        if ch in 'ー－—':
            dr.line([(cx, cy - size * 0.36), (cx, cy + size * 0.36)], fill=_c(ink), width=max(1, int(size * 0.09)))
        elif ch in SMALL_KANA:
            _jt(dr, cx + size * 0.14, cy - size * 0.12, ch, size, ink, stroke=stroke)
        else:
            _jt(dr, cx, cy, ch, size, ink, stroke=stroke)


def p_plaque(name):
    """A shrine or temple plaque (gaku): a black board in a gilt frame, the name in gold, top to bottom."""
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c((0.42, 0.33, 0.18)))
        dr.rectangle([w * 0.06, w * 0.06, w * 0.94, h - w * 0.06], fill=_c((0.72, 0.56, 0.26)))
        dr.rectangle([w * 0.14, w * 0.14, w * 0.86, h - w * 0.14], fill=_c((0.08, 0.075, 0.07)))
        _jv(dr, w / 2, w * 0.24, h - w * 0.24, name, (0.86, 0.70, 0.36), w * 0.62, stroke=2 * k)
    return f


def p_plaqueh(name):
    """A horizontal plaque for the front beam: a black board in a gilt frame, the name in gold, read left to right."""
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c((0.42, 0.33, 0.18)))
        dr.rectangle([h * 0.07, h * 0.07, w - h * 0.07, h * 0.93], fill=_c((0.72, 0.56, 0.26)))
        dr.rectangle([h * 0.16, h * 0.16, w - h * 0.16, h * 0.84], fill=_c((0.08, 0.075, 0.07)))
        _jt(dr, w / 2, h / 2, name, _jfit(dr, name, h * 0.52, w * 0.8), (0.86, 0.70, 0.36), stroke=2 * k)
    return f


EMA_WISH = ['合格祈願', '家内安全', '無病息災', '良縁成就', '健康第一', '交通安全', '安産祈願', '商売繁盛']


def p_ema(dr, w, h, k):
    """Eight ema faces (4 x 2, each wider than tall, the plaque's peak at the top): the pale wood, a picture painted on the
    upper part (the white horse, the sun over a wave, a hydrangea, a torii, a temple roof), a wish written in ink below."""
    cw, ch = w / 4, h / 2
    rng = np.random.default_rng(5)
    for i in range(8):
        x0, y0 = (i % 4) * cw, (i // 4) * ch
        wood = (0.88 - 0.06 * rng.random(), 0.74 - 0.05 * rng.random(), 0.52)
        dr.rectangle([x0, y0, x0 + cw, y0 + ch], fill=_c(wood))
        for j in range(6):
            yy = y0 + ch * (0.12 + 0.15 * j)
            dr.line([(x0, yy), (x0 + cw, yy + ch * 0.03)], fill=_c((wood[0] - 0.07, wood[1] - 0.07, wood[2] - 0.05)), width=max(1, k))
        cx, cy = x0 + cw / 2, y0 + ch * 0.45
        s_ = ch * 0.85
        kind = i % 5
        if kind == 0:                                                   # the white horse
            wc = (0.97, 0.96, 0.93)
            dr.ellipse([cx - s_ * 0.28, cy - s_ * 0.1, cx + s_ * 0.16, cy + s_ * 0.1], fill=_c(wc))
            dr.polygon([(cx + s_ * 0.1, cy - s_ * 0.02), (cx + s_ * 0.26, cy - s_ * 0.22), (cx + s_ * 0.34, cy - s_ * 0.15),
                        (cx + s_ * 0.18, cy + s_ * 0.04)], fill=_c(wc))
            for lx in (-0.22, -0.12, 0.02, 0.11):
                dr.line([(cx + s_ * lx, cy + s_ * 0.06), (cx + s_ * lx, cy + s_ * 0.2)], fill=_c(wc), width=3 * k)
            dr.line([(cx + s_ * 0.2, cy - s_ * 0.17), (cx + s_ * 0.1, cy - s_ * 0.03)], fill=_c((0.75, 0.15, 0.12)), width=3 * k)
        elif kind == 1:                                                 # the sun over a wave
            dr.ellipse([cx - s_ * 0.1, cy - s_ * 0.24, cx + s_ * 0.1, cy - s_ * 0.04], fill=_c((0.85, 0.18, 0.12)))
            for j in range(3):
                dr.arc([cx - s_ * 0.45 + j * s_ * 0.3, cy - s_ * 0.02, cx - s_ * 0.13 + j * s_ * 0.3, cy + s_ * 0.24], 180, 360,
                       fill=_c((0.14, 0.30, 0.60)), width=4 * k)
        elif kind == 2:                                                 # a hydrangea
            for j in range(18):
                a = j * 2.4; rr = s_ * 0.17 * math.sqrt(j / 18)
                px, py = cx + math.cos(a) * rr * 1.2, cy + math.sin(a) * rr * 0.9
                dr.ellipse([px - s_ * 0.05, py - s_ * 0.05, px + s_ * 0.05, py + s_ * 0.05],
                           fill=_c((0.42 + 0.1 * (j % 3), 0.48, 0.86 - 0.1 * (j % 2))))
        elif kind == 3:                                                 # a torii
            dr.rectangle([cx - s_ * 0.32, cy - s_ * 0.22, cx + s_ * 0.32, cy - s_ * 0.17], fill=_c((0.1, 0.1, 0.1)))
            dr.rectangle([cx - s_ * 0.27, cy - s_ * 0.12, cx + s_ * 0.27, cy - s_ * 0.08], fill=_c((0.85, 0.25, 0.13)))
            for lx in (-0.18, 0.18):
                dr.rectangle([cx + s_ * lx - s_ * 0.03, cy - s_ * 0.17, cx + s_ * lx + s_ * 0.03, cy + s_ * 0.2], fill=_c((0.85, 0.25, 0.13)))
        else:                                                           # a temple roof under a red sun
            dr.polygon([(cx - s_ * 0.38, cy + s_ * 0.02), (cx, cy - s_ * 0.18), (cx + s_ * 0.38, cy + s_ * 0.02)], fill=_c((0.25, 0.27, 0.30)))
            dr.rectangle([cx - s_ * 0.24, cy + s_ * 0.02, cx + s_ * 0.24, cy + s_ * 0.2], fill=_c((0.55, 0.36, 0.22)))
            dr.ellipse([cx + s_ * 0.2, cy - s_ * 0.3, cx + s_ * 0.34, cy - s_ * 0.16], fill=_c((0.85, 0.18, 0.12)))
        s = EMA_WISH[i]
        _jt(dr, cx, y0 + ch * 0.84, s, _jfit(dr, s, ch * 0.16, cw * 0.8), (0.12, 0.10, 0.09))
        dr.ellipse([cx - 3 * k, y0 + ch * 0.05, cx + 3 * k, y0 + ch * 0.05 + 6 * k], fill=_c((0.35, 0.25, 0.15)))


def p_koshi(dr, w, h, k):
    """The shrine hall's front: six lattice doors (kōshi-do) of dark wood over the dim hall."""
    dr.rectangle([0, 0, w, h], fill=_c((0.10, 0.08, 0.07)))
    n = 6
    for i in range(n):
        x0 = i * w / n; x1 = x0 + w / n
        dr.rectangle([x0 + 3 * k, 0, x1 - 3 * k, h], outline=_c((0.40, 0.31, 0.22)), width=7 * k)
        for j in range(1, 6):
            xx = x0 + 3 * k + (w / n - 6 * k) * j / 6
            dr.line([(xx, 0), (xx, h * 0.76)], fill=_c((0.38, 0.30, 0.21)), width=3 * k)
        for j in range(1, 12):
            yy = h * 0.76 * j / 12
            dr.line([(x0 + 3 * k, yy), (x1 - 3 * k, yy)], fill=_c((0.34, 0.27, 0.19)), width=2 * k)
        dr.rectangle([x0 + 3 * k, h * 0.76, x1 - 3 * k, h], fill=_c((0.36, 0.28, 0.20)))
        dr.line([(x0 + 3 * k, h * 0.76), (x1 - 3 * k, h * 0.76)], fill=_c((0.22, 0.17, 0.12)), width=4 * k)


def p_saisen(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.30, 0.22, 0.15)))
    for j in range(5):
        dr.line([(0, h * (0.1 + 0.2 * j)), (w, h * (0.1 + 0.2 * j))], fill=_c((0.26, 0.19, 0.13)), width=2 * k)
    _jt(dr, w / 2, h / 2, '奉納', h * 0.62, (0.85, 0.70, 0.38), stroke=k)


def p_timetable(dr, w, h, k):
    """The bus stop's timetable: the operator, the stop, its direction, and the departures by hour (weekdays, Saturdays,
    Sundays and holidays)."""
    dr.rectangle([0, 0, w, h], fill=_c((0.97, 0.97, 0.95)))
    dr.rectangle([0, 0, w, h * 0.13], fill=_c((0.12, 0.30, 0.52)))
    _jt(dr, w / 2, h * 0.04, 'しおかぜバス', h * 0.03, (0.97, 0.97, 0.95))
    _jt(dr, w / 2, h * 0.095, '潮見坂', h * 0.055, (0.97, 0.97, 0.95), stroke=k)
    _jt(dr, w / 2, h * 0.165, '鎌倉駅 行', h * 0.04, (0.10, 0.10, 0.12), stroke=k)
    cols = ['時', '平日', '土曜', '休日']
    xs = [0.1, 0.36, 0.62, 0.86]
    y0 = h * 0.21
    dr.rectangle([w * 0.03, y0, w * 0.97, y0 + h * 0.035], fill=_c((0.86, 0.88, 0.92)))
    for c, x in zip(cols, xs):
        _jt(dr, w * x, y0 + h * 0.018, c, h * 0.026, (0.1, 0.1, 0.12))
    rng = np.random.default_rng(9)
    rows = list(range(6, 22))
    rh = (h * 0.96 - y0 - h * 0.04) / len(rows)
    for i, hr in enumerate(rows):
        yy = y0 + h * 0.04 + i * rh
        if i % 2: dr.rectangle([w * 0.03, yy, w * 0.97, yy + rh], fill=_c((0.92, 0.93, 0.95)))
        _jt(dr, w * xs[0], yy + rh / 2, str(hr), rh * 0.7, (0.1, 0.1, 0.12))
        for j, x in enumerate(xs[1:]):
            n = 3 if (7 <= hr <= 9 and j == 0) else 2
            mins = sorted(rng.choice(range(0, 60, 5), n, replace=False))
            _jt(dr, w * x, yy + rh / 2, ' '.join('%02d' % m for m in mins), rh * 0.62, (0.1, 0.1, 0.12))
    for x in (0.2, 0.49, 0.75):
        dr.line([(w * x, y0), (w * x, h * 0.96)], fill=_c((0.7, 0.72, 0.76)), width=k)


def p_busround(dr, w, h, k):
    """The bus stop's round sign: a white disc in a blue ring, the operator's name, a bus, the stop's name."""
    dr.rectangle([0, 0, w, h], fill=_c((0.12, 0.30, 0.52)))
    dr.ellipse([w * 0.05, h * 0.05, w * 0.95, h * 0.95], fill=_c((0.97, 0.97, 0.95)))
    _jt(dr, w / 2, h * 0.22, 'しおかぜバス', h * 0.075, (0.12, 0.30, 0.52), stroke=k)
    bx0, by0, bx1, by1 = w * 0.27, h * 0.33, w * 0.73, h * 0.58
    dr.rounded_rectangle([bx0, by0, bx1, by1], radius=w * 0.03, fill=_c((0.12, 0.30, 0.52)))
    for j in range(4):
        x = bx0 + w * 0.03 + j * (bx1 - bx0 - w * 0.06) / 4
        dr.rectangle([x + w * 0.01, by0 + h * 0.03, x + (bx1 - bx0 - w * 0.06) / 4 - w * 0.005, by0 + h * 0.11], fill=_c((0.97, 0.97, 0.95)))
    for x in (bx0 + w * 0.09, bx1 - w * 0.09):
        dr.ellipse([x - w * 0.04, by1 - h * 0.04, x + w * 0.04, by1 + h * 0.04], fill=_c((0.1, 0.1, 0.1)))
    _jt(dr, w / 2, h * 0.75, '潮見坂', h * 0.13, (0.10, 0.10, 0.12), stroke=k)


def p_phonelabel(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.22, 0.54, 0.34)))
    _jt(dr, w / 2, h / 2, '公衆電話', h * 0.62, (0.97, 0.97, 0.95), stroke=k)


def p_phone(dr, w, h, k):
    """The grey digital public phone's face: the handset in its cradle on the left, a small green display, the keypad, the
    coin and card slots."""
    dr.rectangle([0, 0, w, h], fill=_c((0.68, 0.70, 0.72)))
    dr.rounded_rectangle([w * 0.06, h * 0.08, w * 0.3, h * 0.92], radius=w * 0.08, fill=_c((0.55, 0.57, 0.60)))
    dr.rectangle([w * 0.4, h * 0.08, w * 0.92, h * 0.22], fill=_c((0.20, 0.34, 0.26)))
    _jt(dr, w * 0.66, h * 0.15, '0 円', h * 0.07, (0.62, 0.90, 0.62))
    for r in range(4):
        for c in range(3):
            x = w * (0.47 + 0.15 * c); y = h * (0.32 + 0.11 * r)
            dr.rounded_rectangle([x - w * 0.05, y - h * 0.04, x + w * 0.05, y + h * 0.04], radius=2 * k, fill=_c((0.90, 0.90, 0.88)))
    dr.rectangle([w * 0.45, h * 0.8, w * 0.62, h * 0.83], fill=_c((0.1, 0.1, 0.1)))
    dr.rectangle([w * 0.7, h * 0.78, w * 0.9, h * 0.81], fill=_c((0.1, 0.1, 0.1)))
    _jt(dr, w * 0.66, h * 0.9, '公衆電話', h * 0.055, (0.22, 0.54, 0.34))


VEND = {
    1: {'body': (0.10, 0.52, 0.56), 'band': (0.97, 0.93, 0.82), 'ink': (0.10, 0.36, 0.40), 'brand': 'しおさい', 'sub': '潮騒ドリンク',
        'drinks': [('潮風サイダー', (0.55, 0.80, 0.95)), ('ほうじ茶', (0.55, 0.35, 0.20)), ('朝つゆの水', (0.85, 0.93, 0.97)),
                   ('みかん', (0.98, 0.60, 0.15)), ('微糖珈琲', (0.30, 0.20, 0.14)), ('麦茶', (0.80, 0.62, 0.30)),
                   ('緑茶', (0.40, 0.62, 0.28)), ('ミルクティー', (0.90, 0.82, 0.68)), ('ラムネ', (0.62, 0.85, 0.92)),
                   ('白桃', (0.98, 0.78, 0.76)), ('黒豆茶', (0.22, 0.18, 0.16)), ('レモン', (0.98, 0.90, 0.30))]},
    2: {'body': (0.60, 0.50, 0.78), 'band': (0.97, 0.96, 0.98), 'ink': (0.36, 0.26, 0.52), 'brand': 'あじさい', 'sub': '紫陽花飲料',
        'drinks': [('梅ソーダ', (0.86, 0.40, 0.46)), ('玄米茶', (0.70, 0.62, 0.36)), ('天然水', (0.80, 0.90, 0.98)),
                   ('ぶどう', (0.50, 0.22, 0.50)), ('カフェオレ', (0.78, 0.62, 0.46)), ('ジャスミン茶', (0.72, 0.84, 0.50)),
                   ('甘酒', (0.97, 0.95, 0.90)), ('ココア', (0.42, 0.26, 0.18)), ('りんご', (0.92, 0.30, 0.25)),
                   ('柚子茶', (0.98, 0.84, 0.30)), ('麦茶', (0.80, 0.62, 0.30)), ('炭酸水', (0.70, 0.86, 0.90))]},
}


def p_vend(which):
    """A drink vending machine's front (invented brand): the brand band, three rows of four sample cans and bottles behind the
    glass with their names and prices, the cold (blue) and hot (red) labels, a lit button under each, the coin slot, the note
    reader and change return on the right, the take-out flap at the foot, the brand on the lower panel."""
    V_ = VEND[which]

    def f(dr, w, h, k):
        body, band, ink = V_['body'], V_['band'], V_['ink']
        dr.rectangle([0, 0, w, h], fill=_c(body))
        # the display window (top 0.06 .. 0.56 of the height, left 0.05 .. 0.78)
        x0, x1, y0, y1 = w * 0.05, w * 0.78, h * 0.05, h * 0.56
        dr.rectangle([x0, y0, x1, y1], fill=_c((0.86, 0.88, 0.90)))
        rh = (y1 - y0) / 3
        rng = np.random.default_rng(which)
        for r in range(3):
            yb = y0 + (r + 1) * rh
            dr.rectangle([x0, yb - rh * 0.3, x1, yb], fill=_c((0.95, 0.95, 0.96)))
            for c in range(4):
                i = r * 4 + c
                name, col = V_['drinks'][i]
                cx = x0 + (c + 0.5) * (x1 - x0) / 4
                cw = (x1 - x0) / 4 * (0.52 if i % 3 else 0.42)
                top = yb - rh * (0.92 if i % 3 == 0 else 0.8)
                bot = yb - rh * 0.32
                dr.rounded_rectangle([cx - cw / 2, top, cx + cw / 2, bot], radius=cw * 0.18, fill=_c(col))
                for s_ in range(6):                                         # cylindrical shading
                    xx = cx - cw / 2 + cw * s_ / 6
                    sh = 0.82 + 0.3 * math.sin(math.pi * (s_ + 0.5) / 6)
                    dr.rectangle([xx, top + cw * 0.15, xx + cw / 6, bot - cw * 0.1],
                                 fill=_c(tuple(min(1, v * sh) for v in col)))
                if i % 3 == 0:
                    dr.rectangle([cx - cw * 0.22, top - rh * 0.06, cx + cw * 0.22, top + rh * 0.02], fill=_c((0.95, 0.95, 0.95)))
                lab = (0.98, 0.98, 0.96) if sum(col) < 1.6 else (0.12, 0.12, 0.14)
                _jv(dr, cx, top + (bot - top) * 0.16, bot - (bot - top) * 0.06, name, lab, cw * 0.5)
                dr.rectangle([cx - cw * 0.45, bot + rh * 0.03, cx + cw * 0.45, bot + rh * 0.12],
                             fill=_c((0.20, 0.42, 0.86) if r < 2 or c < 2 else (0.86, 0.18, 0.16)))
                lab2 = 'つめた〜い' if (r < 2 or c < 2) else 'あったか〜い'
                _jt(dr, cx, bot + rh * 0.075, lab2, _jfit(dr, lab2, rh * 0.065, cw * 0.82), (0.98, 0.98, 0.98))
                _jt(dr, cx, bot + rh * 0.18, '¥%d' % (130 if i % 3 else 160), rh * 0.09, (0.10, 0.10, 0.12), stroke=k)
                dr.rounded_rectangle([cx - cw * 0.4, bot + rh * 0.24, cx + cw * 0.4, bot + rh * 0.3], radius=2 * k,
                                     fill=_c((0.30, 0.90, 0.50) if rng.random() > 0.15 else (0.96, 0.30, 0.25)))
        # the brand band under the window
        dr.rectangle([0, h * 0.58, w, h * 0.7], fill=_c(band))
        _jt(dr, w * 0.42, h * 0.64, V_['brand'], h * 0.06, ink, stroke=2 * k)
        _jt(dr, w * 0.42, h * 0.685, V_['sub'], h * 0.022, ink)
        # the coin column
        cx0 = w * 0.82
        dr.rectangle([cx0, h * 0.06, w * 0.96, h * 0.55], fill=_c((0.20, 0.21, 0.22)))
        dr.rectangle([cx0 + w * 0.03, h * 0.09, w * 0.93, h * 0.13], fill=_c((0.05, 0.25, 0.10)))
        _jt(dr, w * 0.89, h * 0.11, '0', h * 0.03, (0.4, 1.0, 0.5))
        dr.rectangle([cx0 + w * 0.055, h * 0.18, cx0 + w * 0.085, h * 0.25], fill=_c((0.05, 0.05, 0.05)))
        _jt(dr, w * 0.89, h * 0.27, '硬貨', h * 0.018, (0.9, 0.9, 0.9))
        dr.rectangle([cx0 + w * 0.02, h * 0.32, w * 0.94, h * 0.34], fill=_c((0.05, 0.05, 0.05)))
        _jt(dr, w * 0.89, h * 0.36, '千円札', h * 0.018, (0.9, 0.9, 0.9))
        dr.rectangle([cx0 + w * 0.03, h * 0.44, w * 0.93, h * 0.5], fill=_c((0.08, 0.08, 0.08)))
        _jt(dr, w * 0.89, h * 0.52, 'おつり', h * 0.018, (0.9, 0.9, 0.9))
        # the take-out flap
        dr.rectangle([w * 0.1, h * 0.76, w * 0.75, h * 0.9], fill=_c((0.12, 0.12, 0.13)))
        dr.rectangle([w * 0.12, h * 0.77, w * 0.73, h * 0.8], fill=_c((0.22, 0.22, 0.23)))
        _jt(dr, w * 0.425, h * 0.86, '取出口', h * 0.025, (0.85, 0.85, 0.85))
        dr.rectangle([0, h * 0.95, w, h], fill=_c(tuple(v * 0.5 for v in body)))
    return f


def p_bin(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.20, 0.36, 0.62)))
    dr.rectangle([w * 0.08, h * 0.12, w * 0.92, h * 0.55], fill=_c((0.97, 0.97, 0.95)))
    _jt(dr, w / 2, h * 0.24, '空きかん', h * 0.12, (0.20, 0.36, 0.62), stroke=k)
    _jt(dr, w / 2, h * 0.43, 'ペットボトル', h * 0.09, (0.20, 0.36, 0.62))
    _jt(dr, w / 2, h * 0.75, 'リサイクル', h * 0.09, (0.97, 0.97, 0.95))


def p_mirror(dr, w, h, k):
    """A convex mirror's face: the corner it watches, bent round: sky and a pole at the top, the lane curving across, a block
    wall, a house front, the mirror's dark rim."""
    dr.rectangle([0, 0, w, h], fill=_c((0.12, 0.12, 0.12)))
    cx, cy, r = w / 2, h / 2, w * 0.47
    im = Image.new('RGB', (int(w), int(h)), _c((0.60, 0.74, 0.90)))
    d2 = ImageDraw.Draw(im)
    for j in range(int(h * 0.45)):
        t = j / (h * 0.45)
        d2.line([(0, j), (w, j)], fill=_c((0.46 + 0.3 * t, 0.62 + 0.22 * t, 0.86 + 0.08 * t)))
    d2.ellipse([-w * 0.3, h * 0.48, w * 1.3, h * 1.6], fill=_c((0.40, 0.40, 0.42)))
    d2.ellipse([-w * 0.1, h * 0.58, w * 1.1, h * 1.5], fill=_c((0.33, 0.33, 0.35)))
    d2.arc([-w * 0.05, h * 0.62, w * 1.05, h * 1.45], 200, 340, fill=_c((0.93, 0.93, 0.9)), width=3 * k)
    d2.chord([-w * 0.4, h * 0.25, w * 0.45, h * 0.9], 120, 300, fill=_c((0.72, 0.71, 0.68)))
    d2.chord([w * 0.5, h * 0.15, w * 1.5, h * 0.85], 240, 60, fill=_c((0.86, 0.80, 0.68)))
    d2.polygon([(w * 0.62, h * 0.16), (w * 0.95, h * 0.06), (w * 1.0, h * 0.2), (w * 0.66, h * 0.26)], fill=_c((0.34, 0.36, 0.40)))
    d2.rectangle([w * 0.7, h * 0.32, w * 0.8, h * 0.5], fill=_c((0.55, 0.62, 0.66)))
    d2.line([(w * 0.42, 0), (w * 0.47, h * 0.5)], fill=_c((0.62, 0.62, 0.6)), width=5 * k)
    d2.line([(0, h * 0.18), (w, h * 0.1)], fill=_c((0.15, 0.15, 0.15)), width=k)
    d2.ellipse([w * 0.08, h * 0.3, w * 0.3, h * 0.48], fill=_c((0.30, 0.48, 0.26)))
    mask = Image.new('L', (int(w), int(h)), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    dr._image.paste(im, (0, 0), mask)
    dr.arc([cx - r * 0.85, cy - r * 0.85, cx + r * 0.6, cy + r * 0.6], 200, 250, fill=_c((0.95, 0.97, 1.0)), width=6 * k)


def p_manhole(dr, w, h, k):
    """A decorated sewer cover (an invented design for the town): a hydrangea in flower over a breaking wave, a temple roof
    and the sun, coloured in, in a ring of cast pattern with the word おすい (sewer)."""
    iron = (0.30, 0.30, 0.31); ironl = (0.42, 0.42, 0.43)
    dr.rectangle([0, 0, w, h], fill=_c(iron))
    cx, cy = w / 2, h / 2
    R_ = w * 0.49
    dr.ellipse([cx - R_, cy - R_, cx + R_, cy + R_], fill=_c(ironl))
    for j in range(36):                                     # the cast ring of little blocks
        a = 2 * math.pi * j / 36
        px, py = cx + math.cos(a) * R_ * 0.9, cy + math.sin(a) * R_ * 0.9
        dr.rectangle([px - 5 * k, py - 5 * k, px + 5 * k, py + 5 * k], fill=_c(iron))
    r2 = R_ * 0.8
    dr.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=_c((0.62, 0.78, 0.88)))
    dr.ellipse([cx + r2 * 0.25, cy - r2 * 0.75, cx + r2 * 0.6, cy - r2 * 0.4], fill=_c((0.86, 0.26, 0.16)))
    dr.polygon([(cx - r2 * 0.75, cy - r2 * 0.05), (cx - r2 * 0.25, cy - r2 * 0.4), (cx + r2 * 0.25, cy - r2 * 0.05)],
               fill=_c((0.30, 0.31, 0.35)))
    dr.rectangle([cx - r2 * 0.5, cy - r2 * 0.05, cx, cy + r2 * 0.12], fill=_c((0.62, 0.34, 0.22)))
    for j in range(4):                                       # the wave
        x0 = cx - r2 + j * r2 * 0.55
        dr.pieslice([x0, cy, x0 + r2 * 0.7, cy + r2 * 0.7], 180, 360, fill=_c((0.16, 0.36, 0.66)))
        dr.pieslice([x0 + r2 * 0.12, cy + r2 * 0.1, x0 + r2 * 0.58, cy + r2 * 0.6], 180, 360, fill=_c((0.94, 0.95, 0.96)))
    dr.rectangle([cx - r2, cy + r2 * 0.33, cx + r2, cy + r2], fill=_c((0.16, 0.36, 0.66)))
    for j in range(22):                                      # the hydrangea
        a = j * 2.4; rr = r2 * 0.32 * math.sqrt(j / 22)
        px, py = cx + r2 * 0.35 + math.cos(a) * rr, cy + r2 * 0.25 + math.sin(a) * rr
        dr.ellipse([px - r2 * 0.09, py - r2 * 0.09, px + r2 * 0.09, py + r2 * 0.09],
                   fill=_c((0.48 + 0.12 * (j % 3), 0.44, 0.84 - 0.08 * (j % 2))), outline=_c(iron), width=k)
    for a in (2.6, 3.4):
        dr.ellipse([cx + r2 * 0.35 + math.cos(a) * r2 * 0.42 - r2 * 0.12, cy + r2 * 0.35 + math.sin(a) * r2 * 0.2 - r2 * 0.06,
                    cx + r2 * 0.35 + math.cos(a) * r2 * 0.42 + r2 * 0.12, cy + r2 * 0.35 + math.sin(a) * r2 * 0.2 + r2 * 0.06],
                   fill=_c((0.28, 0.50, 0.26)))
    dr.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=_c(iron), width=5 * k)
    _jt(dr, cx, cy + r2 * 0.78, 'おすい', r2 * 0.18, (0.94, 0.95, 0.96), stroke=k)


def p_fumikiri(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.98, 0.80, 0.12)))
    dr.rectangle([4 * k, 4 * k, w - 4 * k, h - 4 * k], outline=_c((0.06, 0.06, 0.06)), width=5 * k)
    _jt(dr, w / 2, h * 0.42, '踏切', h * 0.48, (0.06, 0.06, 0.06), stroke=2 * k)
    _jt(dr, w / 2, h * 0.8, 'とまれ みよ', h * 0.17, (0.06, 0.06, 0.06), stroke=k)


def p_stripe(n, vertical=False):
    """Black-and-yellow diagonal stripes, n pairs along the tile's length."""
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c((0.98, 0.78, 0.10)))
        L = h if vertical else w
        p = L / n
        for i in range(-2, n + 3):
            a = i * p
            if vertical:
                dr.polygon([(0, a), (w, a - w * 0.8), (w, a - w * 0.8 + p / 2), (0, a + p / 2)], fill=_c((0.07, 0.07, 0.07)))
            else:
                dr.polygon([(a, h), (a + h * 0.8, 0), (a + h * 0.8 + p / 2, 0), (a + p / 2, h)], fill=_c((0.07, 0.07, 0.07)))
    return f


def p_direction(dr, w, h, k):
    """The crossing's direction indicator: two arrows that light toward the coming train."""
    dr.rectangle([0, 0, w, h], fill=_c((0.08, 0.08, 0.08)))
    for s, cx in ((-1, w * 0.27), (1, w * 0.73)):
        pts = [(cx - s * w * 0.15, h * 0.4), (cx + s * w * 0.02, h * 0.4), (cx + s * w * 0.02, h * 0.2), (cx + s * w * 0.18, h * 0.5),
               (cx + s * w * 0.02, h * 0.8), (cx + s * w * 0.02, h * 0.6), (cx - s * w * 0.15, h * 0.6)]
        dr.polygon(pts, fill=_c((0.30, 0.30, 0.28) if s < 0 else (0.98, 0.92, 0.70)))


def p_tramglass(dr, w, h, k):
    """A tram window: dark glass, the sky's pale reflection along its top, the empty car beyond (the far windows bright,
    hanging straps, the seat backs), no one aboard."""
    dr.rectangle([0, 0, w, h], fill=_c((0.20, 0.24, 0.28)))
    dr.rectangle([w * 0.08, h * 0.18, w * 0.92, h * 0.7], fill=_c((0.46, 0.56, 0.64)))
    for x in (0.2, 0.5, 0.8):
        dr.line([(w * x, h * 0.0), (w * x, h * 0.16)], fill=_c((0.75, 0.75, 0.72)), width=k)
        dr.ellipse([w * x - 4 * k, h * 0.15, w * x + 4 * k, h * 0.23], outline=_c((0.82, 0.82, 0.8)), width=k)
    dr.rectangle([0, h * 0.72, w, h], fill=_c((0.25, 0.20, 0.20)))
    dr.rectangle([0, h * 0.7, w, h * 0.76], fill=_c((0.40, 0.25, 0.22)))
    dr.polygon([(0, 0), (w, 0), (w, h * 0.12), (0, h * 0.3)], fill=_c((0.62, 0.72, 0.82)))
    dr.polygon([(w * 0.6, h), (w * 0.9, 0), (w, 0), (w * 0.72, h)], fill=_c((0.30, 0.36, 0.42)))


def p_tramdest(dr, w, h, k):
    """The tram's destination window (invented): 潮見ヶ浜 with its reading in roman letters."""
    dr.rectangle([0, 0, w, h], fill=_c((0.05, 0.05, 0.06)))
    _jt(dr, w / 2, h * 0.4, '潮見ヶ浜', h * 0.58, (0.98, 0.98, 0.96), stroke=k)
    f = SG._font(SG.LATIN_SOFT, int(h * 0.2))
    if f: dr.text((w / 2, h * 0.84), 'Shiomigahama', font=f, fill=_c((0.98, 0.98, 0.96)), anchor='mm')


def p_tramside(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.97, 0.97, 0.95)))
    dr.rectangle([2 * k, 2 * k, w - 2 * k, h - 2 * k], outline=_c((0.13, 0.36, 0.25)), width=3 * k)
    _jt(dr, w / 2, h / 2, '鎌倉 ⇔ 潮見ヶ浜', h * 0.5, (0.10, 0.10, 0.12), stroke=k)


def p_tramnum(num):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c((0.94, 0.90, 0.77)))
        fo = SG._font(SG.LATIN, int(h * 0.75))
        if fo: dr.text((w / 2, h / 2), num, font=fo, fill=_c((0.13, 0.36, 0.25)), anchor='mm')
    return f


def p_demae(dr, w, h, k):
    """The moped's delivery box: a soba shop's (invented) name and 出前 (delivery)."""
    dr.rectangle([0, 0, w, h], fill=_c((0.72, 0.14, 0.12)))
    dr.rectangle([4 * k, 4 * k, w - 4 * k, h - 4 * k], outline=_c((0.97, 0.94, 0.86)), width=3 * k)
    _jt(dr, w / 2, h * 0.38, '出前', h * 0.38, (0.97, 0.94, 0.86), stroke=k)
    _jt(dr, w / 2, h * 0.76, 'そば 潮見庵', h * 0.17, (0.97, 0.94, 0.86))


def p_plate(dr, w, h, k):
    """A licence plate with nothing readable: the kei's yellow, its raised rim, worn blank."""
    dr.rectangle([0, 0, w, h], fill=_c((0.95, 0.80, 0.22)))
    dr.rectangle([2 * k, 2 * k, w - 2 * k, h - 2 * k], outline=_c((0.70, 0.58, 0.16)), width=2 * k)
    dr.rectangle([w * 0.2, h * 0.35, w * 0.8, h * 0.7], fill=_c((0.88, 0.74, 0.22)))


def p_kanban(text, bg, ink):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c(bg))
        _jt(dr, w / 2, h / 2, text, min(h * 0.6, _jfit(dr, text, h * 0.6, w * 0.9)), ink, stroke=k)
    return f


TILES = [
    # weathering and materials (numpy painters)
    ('kt_grain', 384, 768), ('kt_vermil', 384, 768), ('kt_lacq', 192, 384), ('kt_gran', 256, 256), ('kt_granb', 256, 256),
    ('kt_tuff', 384, 384), ('kt_tuffwall', 2048, 720), ('kt_kawara', 1536, 512), ('kt_kawara2', 384, 384),
    ('kt_copper', 1024, 640), ('kt_corr', 768, 384), ('kt_ballast', 512, 426),
    # signs and painted faces (PIL)
    ('kt_plaque', 128, 300), ('kt_plaque2', 128, 300), ('kt_plaqueh', 384, 112), ('kt_ema', 960, 384), ('kt_koshi', 768, 336), ('kt_saisen', 240, 96),
    ('kt_timetable', 320, 560), ('kt_busround', 256, 256), ('kt_phonelabel', 256, 54), ('kt_phone', 128, 170),
    ('kt_vend1', 512, 936), ('kt_vend2', 512, 936), ('kt_bin', 160, 160), ('kt_mirror', 256, 256), ('kt_manhole', 512, 512),
    ('kt_fumikiri', 256, 150), ('kt_stripe', 768, 48), ('kt_stripev', 48, 512), ('kt_direction', 128, 64),
    ('kt_tramglass', 128, 128), ('kt_tramdest', 384, 108), ('kt_tramside', 384, 60), ('kt_num1', 96, 48), ('kt_num2', 96, 48),
    ('kt_demae', 192, 144), ('kt_plate', 96, 48),
]


def paint(img, put):
    """The kit's own tiles (kit_buildings_atlas.paint calls this through EXTRA)."""
    pp = SG.put_pil
    put(img, 'kt_grain', t_grain); put(img, 'kt_vermil', t_vermil); put(img, 'kt_lacq', t_lacq)
    put(img, 'kt_gran', stone_mul((1.0, 1.0, 1.0), 151)); put(img, 'kt_granb', stone_mul((1.0, 1.0, 1.0), 157, 0.45)); put(img, 'kt_tuff', stone_mul((1.0, 1.0, 1.0), 161, 1.2, True))
    put(img, 'kt_tuffwall', t_tuffwall)
    put(img, 'kt_kawara', kawara(24, 9)); put(img, 'kt_kawara2', kawara(7, 5)); put(img, 'kt_copper', t_copper)
    put(img, 'kt_corr', t_corr); put(img, 'kt_ballast', t_ballast)
    pp(img, 'kt_plaque', p_plaque('若潮神社'), (0.42, 0.33, 0.18))
    pp(img, 'kt_plaque2', p_plaque('海光山'), (0.42, 0.33, 0.18))
    pp(img, 'kt_plaqueh', p_plaqueh('若潮神社'), (0.42, 0.33, 0.18))
    pp(img, 'kt_ema', p_ema, (0.86, 0.72, 0.5))
    pp(img, 'kt_koshi', p_koshi, (0.1, 0.08, 0.07))
    pp(img, 'kt_saisen', p_saisen, (0.30, 0.22, 0.15))
    pp(img, 'kt_timetable', p_timetable, (0.97, 0.97, 0.95))
    pp(img, 'kt_busround', p_busround, (0.12, 0.30, 0.52))
    pp(img, 'kt_phonelabel', p_phonelabel, (0.22, 0.54, 0.34))
    pp(img, 'kt_phone', p_phone, (0.68, 0.70, 0.72))
    pp(img, 'kt_vend1', p_vend(1), VEND[1]['body'])
    pp(img, 'kt_vend2', p_vend(2), VEND[2]['body'])
    pp(img, 'kt_bin', p_bin, (0.20, 0.36, 0.62))
    pp(img, 'kt_mirror', p_mirror, (0.12, 0.12, 0.12))
    pp(img, 'kt_manhole', p_manhole, (0.30, 0.30, 0.31))
    pp(img, 'kt_fumikiri', p_fumikiri, (0.98, 0.80, 0.12))
    pp(img, 'kt_stripe', p_stripe(10), (0.98, 0.78, 0.10))
    pp(img, 'kt_stripev', p_stripe(12, True), (0.98, 0.78, 0.10))
    pp(img, 'kt_direction', p_direction, (0.08, 0.08, 0.08))
    pp(img, 'kt_tramglass', p_tramglass, (0.2, 0.24, 0.28))
    pp(img, 'kt_tramdest', p_tramdest, (0.05, 0.05, 0.06))
    pp(img, 'kt_tramside', p_tramside, (0.97, 0.97, 0.95))
    pp(img, 'kt_num1', p_tramnum('201'), (0.94, 0.90, 0.77))
    pp(img, 'kt_num2', p_tramnum('251'), (0.94, 0.90, 0.77))
    pp(img, 'kt_demae', p_demae, (0.72, 0.14, 0.12))
    pp(img, 'kt_plate', p_plate, (0.95, 0.80, 0.22))


# ================================================================ TEMPLES AND SHRINES
def under_at(pr, y, t):
    """The underside's height of a roof slope (profile pr, t thick) at y."""
    for (ya, za), (yb, zb) in zip(pr[:-1], pr[1:]):
        if min(ya, yb) - 1e-6 <= y <= max(ya, yb) + 1e-6:
            return za + (zb - za) * (y - ya) / (yb - ya) - t
    return pr[-1][1] - t


def torii(B):
    """A myōjin torii in vermilion: two posts leaning in a little on rounded granite footings, black-lacquered at their feet,
    the collars (daiwa) under the beams, the tie beam (nuki) running through and out past the posts with its wedges, the
    plaque with the shrine's name (invented: 若潮神社) on its strut, the vermilion shimaki and the black kasagi on top,
    curving up to its slanted ends. 4.6 m across the kasagi, 4.4 m to its tips. Paint faded and chipped, moss on the stones."""
    px, pt = 1.42, 1.34                      # post centres at the foot and at the top (they lean in)
    for s in (-1, 1):
        f, _ = lathe([(0.0, 0.0), (0.40, 0.0), (0.42, 0.1), (0.36, 0.24), (0.24, 0.32), (0.0, 0.34)], 12, 'ktgran', sm=1)
        xform(f, T(s * px, 0, 0)); tadd(B, f, 'kt_gran')
        tadd(B, tube([(s * px, 0, 0.28), (s * (px + (pt - px) * 0.12), 0, 0.78)], 0.172, 'kttex', 12), 'kt_lacq')
        tadd(B, tube([(s * px, 0, 0.28), (s * pt, 0, 3.8)], 0.158, 'kttex', 12), 'kt_vermil')
        tadd(B, tube([(s * (pt + 0.008), 0, 3.56), (s * pt, 0, 3.8)], 0.19, 'kttex', 12), 'kt_vermil')
        for k in range(3):
            a = 2.0 * k + s
            moss(B, s * px + 0.3 * math.cos(a), 0.3 * math.sin(a), 0.27, 0.13, 0.1, 0.04, seed=k + (s > 0) * 5,
                 mat='ktmoss' if k % 2 else 'ktmossl')
        # the wedge (kusabi) through the nuki outside each post
        B.add(cbox2((s * (pt + 0.17) - 0.04, -0.1, 3.12), (s * (pt + 0.17) + 0.04, 0.1, 3.34), 0.01, 'ktdarkw'))
    tadd(B, cbox2((-1.98, -0.085, 3.12), (1.98, 0.085, 3.34), 0.015, 'kttex'), 'kt_vermil')
    tadd(B, cbox2((-0.11, -0.07, 3.34), (0.11, 0.07, 3.8), 0.01, 'kttex'), 'kt_vermil')               # the strut
    tadd(B, cbox2((-2.12, -0.15, 3.8), (2.12, 0.15, 3.98), 0.02, 'kttex'), 'kt_vermil')               # the shimaki
    # the plaque (gaku) in front of the strut, over the nuki
    B.add(cbox2((-0.21, -0.17, 2.98), (0.21, -0.08, 3.9), 0.015, 'ktdarkw'))
    yquad(B, -0.19, 0.19, 3.0, 3.88, -0.172, 'kt_plaque')
    # the kasagi: a beam curving up toward its ends, the ends cut on a slant
    mb = MB()
    n = 12
    xs = [-2.3 + 4.6 * i / n for i in range(n + 1)]

    def zb(x): return 3.98 + 0.16 * (abs(x) / 2.3) ** 2.8
    def zt(x): return zb(x) + 0.23 + 0.03 * (abs(x) / 2.3) ** 2
    yw, yt = 0.19, 0.215
    for a, b in zip(xs[:-1], xs[1:]):
        mb.face([(a, -yw, zb(a)), (b, -yw, zb(b)), (b, -yt, zt(b)), (a, -yt, zt(a))], 'kttex', (0, -1, 0))
        mb.face([(b, yw, zb(b)), (a, yw, zb(a)), (a, yt, zt(a)), (b, yt, zt(b))], 'kttex', (0, 1, 0))
        mb.face([(a, -yt, zt(a)), (b, -yt, zt(b)), (b, yt, zt(b)), (a, yt, zt(a))], 'kttex', (0, 0, 1))
        mb.face([(a, yw, zb(a)), (b, yw, zb(b)), (b, -yw, zb(b)), (a, -yw, zb(a))], 'kttex', (0, 0, -1))
    for x, e in ((-2.3, -1), (2.3, 1)):
        o = e * 0.07
        mb.face([(x, -yw, zb(x)), (x, yw, zb(x)), (x + o, yt, zt(x)), (x + o, -yt, zt(x))], 'kttex', (e, 0, 0.3))
    # the slanted end: the top edge runs out past the bottom
    bm = mb.bm()
    for v in bm.verts:
        if abs(abs(v.co.x) - 2.3) < 1e-4 and v.co.z > zb(2.3) + 0.1:
            v.co.x += math.copysign(0.07, v.co.x)
    tadd(B, bm, 'kt_lacq')
    return 4.4


def temple_gate(B):
    """A small temple gate (a yakuimon with side bays): silvered timber (round main pillars and square ones), the passage
    2.5 m wide between them with its threshold and its two plank doors swung open against the pillars, board walls and a
    barred window in the side bays, tie beams, bracket blocks, the frieze, the plaque with the temple's mountain name
    (invented: 海光山); a heavy gabled roof of grey glazed kawara with deep eaves on rafters, the round end tiles along the
    eave, the verge tiles, the bargeboards, a tall tiled ridge with ogre tiles; on a granite plinth with moss."""
    tadd(B, cbox2((-2.8, -1.4, 0.0), (2.8, 1.4, 0.18), 0.03, 'ktgran'), 'kt_granb')
    for x in (-2.6, -1.2, 0.3, 1.7, 2.6):
        moss(B, x, -1.36, 0.17, 0.25, 0.06, 0.03, seed=int(x * 10) + 40, mat='ktmoss')
    zt = 3.25                                         # pillar tops
    for s in (-1, 1):
        tadd(B, cyl(s * 1.25, 0.0, 0.18, 0.28, 0.25, 'ktgran', 10), 'kt_gran')
        tadd(B, cyl(s * 1.25, 0.0, 0.28, zt, 0.17, 'ktsilv', 12), 'kt_grain')
        for x in (1.25, 2.35):
            for y in (-0.9, 0.9):
                tadd(B, cbox2((s * x - 0.2, y - 0.2, 0.18), (s * x + 0.2, y + 0.2, 0.28), 0.03, 'ktgran'), 'kt_gran')
                tadd(B, cbox2((s * x - 0.12, y - 0.12, 0.28), (s * x + 0.12, y + 0.12, zt), 0.025, 'ktsilv'), 'kt_grain')
                # the bracket blocks: a big block, an arm along the front, three small blocks
                B.add(bx((s * x - 0.18, y - 0.18, zt), (s * x + 0.18, y + 0.18, zt + 0.17), 'ktdarkw'))
                tadd(B, bx((s * x - 0.45, y - 0.08, zt + 0.17), (s * x + 0.45, y + 0.08, zt + 0.31), 'ktsilv'), 'kt_grain')
                for dx in (-0.34, 0.0, 0.34):
                    B.add(bx((s * x + dx - 0.09, y - 0.1, zt + 0.31), (s * x + dx + 0.09, y + 0.1, zt + 0.43), 'ktdarkw'))
        # tie beams across the gate's depth
        for x in (1.25, 2.35):
            tadd(B, cbox2((s * x - 0.08, -1.08, zt - 0.27), (s * x + 0.08, 1.08, zt - 0.02), 0.015, 'ktsilv'), 'kt_grain')
        # the side bay: a board wall with a barred window, a low tie beam
        x0, x1 = (1.37, 2.23) if s > 0 else (-2.23, -1.37)
        tadd(B, box((x0, -0.04, 0.18), (x1, 0.04, zt - 0.27), 'ktsilv', skip=('-z',)), 'kt_grain')
        for k in range(5):
            xx = x0 + (x1 - x0) * (k + 0.5) / 5
            B.add(bx((xx - 0.025, -0.07, 1.65), (xx + 0.025, -0.04, 2.35), 'ktdarkw'))
        B.add(box((x0 + 0.04, -0.045, 1.65), (x1 - 0.04, -0.041, 2.35), 'ktsoffit'))
        for z in (1.6, 2.35):
            B.add(cbox2((x0, -0.08, z - 0.04), (x1, -0.04, z + 0.04), 0.01, 'ktdarkw'))
        for y in (-0.9, 0.9):
            tadd(B, cbox2((x0, y - 0.07, 0.9), (x1, y + 0.07, 1.05), 0.01, 'ktsilv'), 'kt_grain')
        # the door leaf, swung open inward against the main pillar
        xd = s * 1.12
        tadd(B, cbox2((xd - 0.045, 0.1, 0.3), (xd + 0.045, 1.33, 3.0), 0.01, 'ktsilv'), 'kt_grain')
        for z in (0.7, 1.6, 2.5):
            B.add(bx((xd - 0.055, 0.12, z - 0.05), (xd + 0.055, 1.31, z + 0.05), 'ktblk'))
    # head tie beams along the front, the middle and the back, running out past the outer pillars (kibana)
    for y in (-0.9, 0.0, 0.9):
        tadd(B, cbox2((-2.6, y - 0.08, zt - 0.27), (2.6, y + 0.08, zt - 0.02), 0.015, 'ktsilv'), 'kt_grain')
    tadd(B, cbox2((-1.25, -0.07, 0.18), (1.25, 0.07, 0.36), 0.015, 'ktdarkw'), 'kt_grain')            # threshold
    # purlins on the brackets, the frieze up to the roof
    for y in (-0.9, 0.9):
        tadd(B, cbox2((-2.75, y - 0.1, zt + 0.43), (2.75, y + 0.1, zt + 0.62), 0.015, 'ktsilv'), 'kt_grain')
    # the roof: two concave slopes, ridge 5.36 at y 0, eaves 3.75 at y +-2.05
    zr, ze, ye, t = 5.36, 3.75, 2.05, 0.24
    X0, X1 = -3.25, 3.25
    profs = {}
    for s in (-1, 1):
        pr = slope_prof(0.0, zr, s * ye, ze, 6, 0.38)
        profs[s] = pr
        roof_slope(B, X0, X1, pr, t, 'kt_kawara', edge='ktkawad', ends='ktdarkw')
        for x in (X0, X1):
            barge(B, x + (0.035 if x < 0 else -0.035), pr, t, 0.3, 0.07)
            B.add(tube([(x + (0.06 if x < 0 else -0.06), y, z + 0.06) for y, z in pr], 0.085, 'ktkawa', 6))
        # the rafters under the eave, from the purlin out to the fascia
        def under(y, pr=pr):
            for (ya, za), (yb, zb_) in zip(pr[:-1], pr[1:]):
                if min(ya, yb) - 1e-6 <= y <= max(ya, yb) + 1e-6:
                    return za + (zb_ - za) * (y - ya) / (yb - ya) - t
            return pr[-1][1] - t
        for k in range(22):
            x = -3.1 + 6.2 * k / 21
            ya, yb = s * 0.85, s * (ye - 0.06)
            B.add(tube([(x, ya, under(ya) - 0.05), (x, yb, under(yb) - 0.05)], 0.05, 'ktsilv', 4, sm=0))
        B.add(cbox2((X0 + 0.05, s * ye - 0.08, under(s * ye) - 0.16), (X1 - 0.05, s * ye + 0.02, under(s * ye) + 0.01), 0.01,
                    'ktdarkw') if s < 0 else
              cbox2((X0 + 0.05, s * ye - 0.02, under(s * ye) - 0.16), (X1 - 0.05, s * ye + 0.08, under(s * ye) + 0.01), 0.01, 'ktdarkw'))
        # the frieze over the purlin, up to the roof's underside
        zf = zt + 0.62
        tadd(B, box((-2.6, s * 0.9 - 0.04, zf), (2.6, s * 0.9 + 0.04, under(s * 0.9) + 0.02), 'ktsilv'), 'kt_grain')
    tile_ends(B, X0 + 0.08, X1 - 0.08, -ye - 0.03, ze - 0.1, 0.27, r=0.085, facing=-1)
    tile_ends(B, X0 + 0.08, X1 - 0.08, ye + 0.03, ze - 0.1, 0.27, r=0.085, facing=1)
    # the gable ends: boards closing the triangle over the tie beams at the outer pillars
    for s in (-1, 1):
        x = s * 2.42
        mb = MB()
        pts = [(x, -0.9, zt + 0.62), (x, -0.9, under_at(profs[-1], -0.9, t) + 0.02)] + \
              [(x, y, z - t + 0.02) for y, z in reversed(profs[-1]) if y > -0.9] + \
              [(x, y, z - t + 0.02) for y, z in profs[1][1:] if y < 0.9] + \
              [(x, 0.9, under_at(profs[1], 0.9, t) + 0.02), (x, 0.9, zt + 0.62)]
        mb.face(pts, 'ktsilv', (s, 0, 0))
        tadd(B, mb.bm(), 'kt_grain')
    ridge(B, X0 + 0.2, X1 - 0.2, 0.0, zr, h=0.6, w=0.46)
    # the plaque under the front eave
    B.add(bx((-0.24, -1.06, 2.28), (0.24, -0.99, 3.3), 'ktdarkw'))
    yquad(B, -0.22, 0.22, 2.3, 3.28, -1.062, 'kt_plaque2')
    return 6.1


def stone_lantern(B):
    """A granite Kasuga-style stone lantern (tōrō): the hexagonal base, the pole with its knot, the platform, the fire box
    with its window (and a round one each side), the hexagonal roof with its curled corners, the jewel on top; moss on the
    roof and the base, the stone darkened by damp."""
    parts = [
        ([(0.0, 0.0), (0.40, 0.0), (0.40, 0.11), (0.33, 0.19), (0.20, 0.25), (0.0, 0.25)], 6),
        ([(0.0, 0.25), (0.12, 0.25), (0.11, 0.98), (0.0, 0.98)], 10),
        ([(0.0, 0.58), (0.135, 0.58), (0.135, 0.64), (0.0, 0.64)], 10),
        ([(0.0, 0.98), (0.16, 0.98), (0.33, 1.08), (0.33, 1.16), (0.0, 1.16)], 6),
        ([(0.0, 1.16), (0.22, 1.16), (0.22, 1.5), (0.0, 1.5)], 6),
        ([(0.0, 1.5), (0.5, 1.5), (0.52, 1.55), (0.27, 1.76), (0.12, 1.81), (0.0, 1.81)], 6),
        ([(0.0, 1.81), (0.1, 1.81), (0.11, 1.86), (0.0, 1.87)], 8),
        ([(0.0, 1.86), (0.085, 1.89), (0.1, 1.95), (0.065, 2.01), (0.0, 2.05)], 8),
    ]
    for prof, n in parts:
        bm, _ = lathe(prof, n, 'ktgran', phase=0.0 if n == 6 else 0.5, sm=0 if n == 6 else 1)
        tadd(B, bm, 'kt_gran')
    # the fire box's openings: the window front and back, a round one each side
    a = 0.22 * math.cos(math.pi / 6)
    for s in (-1, 1):
        mb = MB()
        y = s * (a + 0.004)
        pts = [(-0.11, y, 1.22), (0.11, y, 1.22), (0.11, y, 1.44), (-0.11, y, 1.44)]
        mb.face(pts if s < 0 else pts[::-1], 'ktsoffit', (0, s, 0))
        B.add(mb.bm())
    for ang in (math.pi / 6, 5 * math.pi / 6, 7 * math.pi / 6, 11 * math.pi / 6):
        d = Vector((math.cos(ang), math.sin(ang), 0)) * (a + 0.004)
        c, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.0, 0.002)], 8, 'ktsoffit')
        xform(c, T(d.x, d.y, 1.33) @ frame((0, 0, 0), (math.cos(ang), math.sin(ang), 0)))
        B.add(c)
    # the roof's curled corners (warabite)
    for k in range(6):
        ang = 2 * math.pi * k / 6
        c, s_ = math.cos(ang), math.sin(ang)
        B.add(tube([(0.5 * c, 0.5 * s_, 1.55), (0.56 * c, 0.56 * s_, 1.6), (0.55 * c, 0.55 * s_, 1.67), (0.5 * c, 0.5 * s_, 1.65)],
                   0.035, 'ktgran', 4))
    # moss on the roof and the base
    rng = np.random.default_rng(3)
    for k in range(7):
        ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.18, 0.38)
        z = 1.55 + (0.5 - r) / 0.23 * 0.2
        moss(B, r * math.cos(ang), r * math.sin(ang), z, 0.12, 0.1, 0.035, seed=k, mat='ktmoss' if k % 3 else 'ktmossl')
    for k in range(6):
        ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 0.32)
        moss(B, r * math.cos(ang), r * math.sin(ang), 0.2, 0.12, 0.09, 0.035, seed=10 + k, mat='ktmoss' if k % 2 else 'ktmossl')
    for k in range(3):
        ang = rng.uniform(0, 2 * math.pi)
        moss(B, 0.28 * math.cos(ang), 0.28 * math.sin(ang), 1.1, 0.08, 0.07, 0.025, seed=20 + k)
    return 2.05


def stone_steps(B):
    """Stone steps up from the street (+Y): six risers of cut tuff, each tread two slabs a little out of true, moss along the
    edges and in the joints, low tuff walls at the sides stepping up with them, moss on their copings. 3.0 m between the
    walls (3.6 m over them), 1.0 m up over 2.4 m."""
    rng = np.random.default_rng(11)
    n, rise, run, y0 = 6, 1.0 / 6, 0.32, -1.2
    for k in range(n):
        yf = y0 + k * run
        z0, z1 = k * rise, (k + 1) * rise
        cut = rng.uniform(-0.7, 0.7)
        for xa, xb in ((-1.5, cut - 0.008), (cut + 0.008, 1.5)):
            j = rng.uniform(-0.01, 0.012); f = rng.uniform(-0.015, 0.02)
            tadd(B, cbox2((xa, yf + f, z0), (xb, 1.2, z1 + j), 0.03, 'kttuff'), 'kt_tuff')
        for x in (-1.42, 1.42):
            moss(B, x, yf + 0.18, z1 + 0.005, 0.12, 0.17, 0.025, seed=k * 3 + (x > 0), mat='ktmoss' if k % 2 else 'ktmossl')
        moss(B, cut, yf + 0.2, z1 + 0.004, 0.05, 0.15, 0.02, seed=k * 7 + 2)
        if k % 2 == 0:
            moss(B, rng.uniform(-1.0, 1.0), yf + 0.005, z0 + rise * 0.3, 0.2, 0.025, 0.05, seed=k + 30)
    # the side walls: tuff blocks, the coping sloping up with the steps
    for s in (-1, 1):
        prof = [(-1.2, 0.0), (1.2, 0.0), (1.2, 1.45), (0.75, 1.45), (-1.2, 0.42)]
        mb = MB()
        xo, xi = s * 1.8, s * 1.5
        # outer, inner faces (the tuff wall tile, mapped by y and z), the coping, the front end
        for x, e in ((xo, s), (xi, -s)):
            pts = [(x, y, z) for y, z in prof]
            mb.face(pts, 'kttex', (e, 0, 0), 1.0, lambda co: reg_uv('kt_tuffwall', (co.y + 1.2) / 4.0 + (0.35 if s > 0 else 0.0),
                                                                     co.z / 1.4, 0.0))
        bm = mb.bm()
        B.add(bm)
        for (ya, za), (yb, zb) in ((prof[4], prof[3]), (prof[3], prof[2])):
            mb2 = MB()
            mb2.face([(xi, ya, za), (xo, ya, za), (xo, yb, zb), (xi, yb, zb)], 'kttuff', (0, 0, 1))
            tadd(B, mb2.bm(), 'kt_tuff')
        mb3 = MB()
        mb3.face([(xi, -1.2, 0.0), (xo, -1.2, 0.0), (xo, -1.2, 0.42), (xi, -1.2, 0.42)], 'kttuff', (0, -1, 0))
        mb3.face([(xo, 1.2, 0.0), (xi, 1.2, 0.0), (xi, 1.2, 1.45), (xo, 1.2, 1.45)], 'kttuff', (0, 1, 0))
        tadd(B, mb3.bm(), 'kt_tuff')
        for k in range(5):
            y = -1.0 + k * 0.45
            z = 0.42 + (y + 1.2) / 1.95 * 1.03 if y < 0.75 else 1.45
            moss(B, s * 1.65, y, min(z, 1.45) + 0.01, 0.17, 0.22, 0.04, seed=50 + k + (s > 0) * 9, mat='ktmoss' if k % 2 else 'ktmossl')
    return 1.45


def moss_wall(B):
    """A retaining wall of cut Kamakura-ishi, the town's soft green-grey tuff: 4.0 m of running-bond blocks 1.4 m high
    leaning back a little, each block's face weathered soft and proud of its joints (real relief), moss thick on the coping
    and in the joints, ferns in the cracks. Its texture repeats exactly every 4.0 m, so the segments tile end to end."""
    W, Hh, D = 4.0, 1.4, 0.6
    yf0, bat = -0.3, 0.07

    def joint_d(x, z):
        X = x + 2.0
        c = min(3, int(z / 0.35)) if z < Hh else 3
        off = (c % 2) * 0.4
        xb = X + off
        du = xb - math.floor(xb / 0.8 + 1e-9) * 0.8
        dz = z - c * 0.35
        return min(du, 0.8 - du, dz, 0.35 - dz)
    xs = [-2.0 + 0.2 * i for i in range(21)]
    zs = [0.0875 * j for j in range(17)]
    V = []; F = []
    for j, z in enumerate(zs):
        for i, x in enumerate(xs):
            d = joint_d(x, z)
            bulge = 0.025 * _ss(0.0, 0.09, d) if 0 < z < Hh else 0.0
            if abs(x) > 1.999: bulge = min(bulge, 0.004)
            V.append((x, yf0 + bat * z / Hh - bulge, z))
    nx = len(xs)
    for j in range(len(zs) - 1):
        for i in range(nx - 1):
            F.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
    bm, faces = bm_from(V, F, 'kttex', sm=1)
    for f in bm.faces:
        if f.normal.y > 0: f.normal_flip()
    plane_uv(bm, 'kt_tuffwall', 0, 2, (-2.0, 0.0), (2.0, Hh))
    B.add(bm)
    yt = yf0 + bat
    # the coping's top, the back and the ends
    tadd(B, box((-2.0, yt, Hh - 0.02), (2.0, D / 2, Hh), 'kttuff', skip=('-z', '-x', '+x')), 'kt_tuff')
    for x, e in ((-2.0, -1), (2.0, 1)):
        mb = MB()
        mb.face([(x, yf0, 0.0), (x, D / 2, 0.0), (x, D / 2, Hh), (x, yt, Hh)], 'kttuff', (e, 0, 0))
        tadd(B, mb.bm(), 'kt_tuff')
    rng = np.random.default_rng(21)
    for k in range(9):
        x = -1.75 + 3.5 * k / 8 + rng.uniform(-0.1, 0.1)
        moss(B, x, yt + 0.12, Hh + 0.01, rng.uniform(0.2, 0.32), 0.2, 0.045, seed=k, mat='ktmoss' if k % 3 else 'ktmossl')
        moss(B, x + 0.1, yt - 0.01, Hh - 0.06, rng.uniform(0.12, 0.25), 0.04, 0.09, seed=k + 20)
    # ferns sprouting from the joints
    for (x, z) in ((-1.2, 0.7), (0.4, 1.05), (1.45, 0.35), (-0.4, 0.35)):
        y = yf0 + bat * z / Hh - 0.005
        for k in range(6):
            a = -0.9 + 1.8 * k / 5
            tip = (x + 0.28 * math.sin(a), y - 0.12 - 0.05 * abs(a), z + 0.08 + 0.1 * math.cos(a))
            mid = (x + 0.15 * math.sin(a), y - 0.1, z + 0.12)
            B.add(tube([(x, y, z), mid, tip], 0.018, 'ktleaf' if k % 2 else 'leafd', 3))
    return Hh + 0.05


def ema_rack(B):
    """A rack of ema (wooden prayer plaques) under a little roof of kawara: two posts, three rails, the plaques hung on them
    by their cords, some over others, each painted with a picture and a wish."""
    for s in (-1, 1):
        tadd(B, bx((s * 0.86 - 0.05, -0.05, 0.0), (s * 0.86 + 0.05, 0.05, 1.86), 'ktsilv'), 'kt_grain')
        tadd(B, bx((s * 0.86 - 0.12, -0.12, 0.0), (s * 0.86 + 0.12, 0.12, 0.08), 'ktgran'), 'kt_gran')
    for z in (0.78, 1.12, 1.46):
        tadd(B, bx((-0.92, -0.03, z - 0.025), (0.92, 0.03, z + 0.025), 'ktsilv'), 'kt_grain')
        B.add(tube([(-0.8, -0.032, z + 0.02), (0.8, -0.032, z + 0.02)], 0.004, 'ktred', 3))
    tadd(B, bx((-0.95, -0.06, 1.78), (0.95, 0.06, 1.88), 'ktsilv'), 'kt_grain')
    for s in (-1, 1):
        pr = slope_prof(0.0, 2.12, s * 0.42, 1.86, 3, 0.25)
        roof_slope(B, -1.02, 1.02, pr, 0.06, 'kt_kawara2', edge='ktkawad', ends='ktdarkw')
        for x in (-1.0, 1.0):
            B.add(tube([(x, y, z + 0.02) for y, z in pr], 0.03, 'ktkawa', 5))
    B.add(tube([(-1.0, 0.0, 2.14), (1.0, 0.0, 2.14)], 0.05, 'ktkawad', 6))
    for s in (-1, 1):
        for k in range(7):
            x = -0.9 + 1.8 * k / 6
            B.add(disc_y(x, s * 0.44, 1.84, 0.035, 0.03, 'ktkawa', 6, -s))
    # the plaques: a pentagon (a peaked top), hung in rows and layers in front of the rails
    rng = np.random.default_rng(8)
    pent = [(-0.09, -0.06), (0.09, -0.06), (0.09, 0.03), (0.0, 0.065), (-0.09, 0.03)]
    k = 0
    for row, z in enumerate((0.78, 1.12, 1.46)):
        for layer in range(2):
            n = 8 if layer == 0 else 5
            for i in range(n):
                x = -0.8 + 1.6 * (i + 0.5 * layer + 0.2) / (n + 0.4 * layer)
                if layer == 1: x = -0.72 + 1.44 * i / (n - 1) + rng.uniform(-0.05, 0.05)
                cell = rng.integers(8)
                cu, cv = cell % 4, 1 - cell // 4
                y = -0.05 - 0.015 * layer
                zc = z - 0.1 - 0.03 * layer + rng.uniform(-0.01, 0.01)
                bm = extrude_poly(pent, 0.012, 'kttex', 'ktemaw', back=False)
                uv_fn(bm, [f for f in bm.faces], 'kt_ema',
                      lambda co, cu=cu, cv=cv: ((cu + (co.x + 0.09) / 0.18) / 4, (cv + (co.y + 0.06) / 0.125) / 2))
                bm.normal_update()
                setmat(bm, 'ktemaw', [f for f in bm.faces if abs(f.normal.z) < 0.5])
                xform(bm, T(x, y, zc) @ R(rng.uniform(-0.12, 0.12), 'Y') @ R(math.pi / 2, 'X'))
                B.add(fix_normals(bm))
                k += 1
    return 2.2


def shrine_hall(B):
    """A small shrine's worship hall (haiden) in the nagare style for the back of the grounds: a copper roof gone green
    sweeping forward over the steps on two posts, rafters under the deep eaves, the hall of weathered timber raised on a
    stone base, six lattice doors across the front under a white frieze, a veranda with its railing, wooden steps up, the
    plaque with the shrine's name (invented: 若潮神社), the offering box (奉納), the bell and its rope of red, white and purple,
    a straw rope with paper streamers across the front. 8 x 7 m."""
    tadd(B, cbox2((-3.7, -2.6, 0.0), (3.7, 2.75, 0.3), 0.03, 'ktgran'), 'kt_granb')
    zf, zb_ = 1.0, 3.65                                   # the floor, the eave beam's top
    xs = (-2.9, -0.97, 0.97, 2.9)
    for x in xs:
        for y in (-1.5, 2.3):
            tadd(B, cyl(x, y, 0.3, zb_, 0.13, 'ktbrown', 10), 'kt_grain')
    for x in (-2.9, 2.9):
        tadd(B, cyl(x, 0.4, 0.3, zb_, 0.13, 'ktbrown', 10), 'kt_grain')
    for x in (-3.35, -0.97, 0.97, 3.35):
        tadd(B, cyl(x, -2.35, 0.3, zf, 0.09, 'ktbrown', 8), 'kt_grain')
    # under the floor: the dark crawl space behind a skirt
    B.add(box((-2.85, -1.45, 0.3), (2.85, 2.25, zf - 0.05), 'ktsoffit', skip=('-z', '+z')))
    # the floor and veranda
    tadd(B, cbox2((-3.45, -2.42, zf - 0.09), (3.45, 2.38, zf), 0.01, 'ktsilv'), 'kt_grain')
    # walls: the lattice doors across the front, boards on the sides and back, the white frieze above
    yquad(B, -2.9, 2.9, zf, 2.9, -1.47, 'kt_koshi')
    for x, e in ((-2.9, -1), (2.9, 1)):
        tadd(B, box((x - 0.04, -1.5, zf), (x + 0.04, 2.3, 2.9), 'ktbrown', skip=('-z',)), 'kt_grain')
    tadd(B, box((-2.9, 2.26, zf), (2.9, 2.34, 2.9), 'ktbrown', skip=('-z',)), 'kt_grain')
    for y0, y1 in ((-1.56, -1.44), (2.24, 2.36)):
        tadd(B, cbox2((-3.0, y0, 2.9), (3.0, y1, 3.05), 0.01, 'ktbrown'), 'kt_grain')
        B.add(box((-2.9, y0 + 0.03, 3.05), (2.9, y1 - 0.03, 3.45), 'ktplaster'))
        tadd(B, cbox2((-3.1, y0 - 0.02, 3.45), (3.1, y1 + 0.02, zb_), 0.01, 'ktbrown'), 'kt_grain')
    for x in (-2.9, 2.9):
        B.add(box((x - 0.03, -1.5, 3.05), (x + 0.03, 2.3, 3.45), 'ktplaster'))
        tadd(B, cbox2((x - 0.07, -1.6, 3.45), (x + 0.07, 2.4, zb_), 0.01, 'ktbrown'), 'kt_grain')
    # the veranda's railing (front, broken for the steps, and the sides)
    for x0, x1 in ((-3.4, -1.05), (1.05, 3.4)):
        for z in (zf + 0.32, zf + 0.62):
            tadd(B, cbox2((x0, -2.42, z - 0.03), (x1, -2.36, z + 0.03), 0.01, 'ktdarkw'), 'kt_grain')
        for x in np.linspace(x0 + 0.05, x1 - 0.05, 4):
            B.add(cbox2((x - 0.04, -2.43, zf), (x + 0.04, -2.35, zf + 0.68), 0.01, 'ktdarkw'))
    for x in (-3.42, 3.42):
        for z in (zf + 0.32, zf + 0.62):
            B.add(cbox2((x - 0.03, -2.42, z - 0.03), (x + 0.03, -1.5, z + 0.03), 0.01, 'ktdarkw'))
    # the steps up to the veranda, between their stringers
    for k in range(5):
        z = 0.2 * (k + 1)
        y = -3.45 + 0.22 * k
        tadd(B, cbox2((-0.95, y, z - 0.06), (0.95, y + 0.26, z), 0.01, 'ktsilv'), 'kt_grain')
    for x in (-1.0, 1.0):
        mb = MB()
        for xx, e in ((x - 0.05, -1), (x + 0.05, 1)):
            mb.face([(xx, -3.5, 0.0), (xx, -2.42, 0.0), (xx, -2.42, zf), (xx, -3.5, 0.12)], 'ktbrown', (e, 0, 0))
        mb.face([(x - 0.05, -3.5, 0.12), (x + 0.05, -3.5, 0.12), (x + 0.05, -2.42, zf + 0.04), (x - 0.05, -2.42, zf + 0.04)], 'ktbrown', (0, -0.5, 1))
        tadd(B, mb.bm(), 'kt_grain')
    tadd(B, cbox2((-1.1, -3.62, 0.0), (1.1, -3.45, 0.12), 0.02, 'ktgran'), 'kt_gran')
    # the front posts (kōhai) carrying the roof's sweep over the steps, their beam, the curved ties back to the hall
    for x in (-1.3, 1.3):
        tadd(B, cbox2((x - 0.17, -3.27, 0.0), (x + 0.17, -2.93, 0.2), 0.02, 'ktgran'), 'kt_gran')
        tadd(B, cbox2((x - 0.1, -3.2, 0.2), (x + 0.1, -3.0, 3.15), 0.02, 'ktbrown'), 'kt_grain')
        B.add(tube([(x, -3.1, 3.0), (x, -2.4, 3.32), (x, -1.6, 3.35)], 0.08, 'ktbrown', 6))
    tadd(B, cbox2((-1.55, -3.18, 2.92), (1.55, -3.02, 3.15), 0.015, 'ktbrown'), 'kt_grain')
    tadd(B, cbox2((-1.55, -3.2, 3.15), (1.55, -3.0, 3.3), 0.015, 'ktbrown'), 'kt_grain')
    # the roof: copper, ridge 6.55 at y 0.6, the long front slope to 3.45 at -3.45, the back to 3.9 at 3.4
    t = 0.25
    zr, X0, X1 = 6.55, -4.0, 4.0
    pf = slope_prof(0.6, zr, -3.45, 3.45, 8, 0.42, up=0.08)
    pb = slope_prof(0.6, zr, 3.4, 3.9, 5, 0.35)
    for pr, s in ((pf, -1), (pb, 1)):
        roof_slope(B, X0, X1, pr, t, 'kt_copper', edge='ktcopper', ends='ktcopper')
        for x in (X0, X1):
            barge(B, x + (0.035 if x < 0 else -0.035), pr, t, 0.32, 0.07, mat='ktbrown')

        def under(y, pr=pr):
            for (ya, za), (yb, zb2) in zip(pr[:-1], pr[1:]):
                if min(ya, yb) - 1e-6 <= y <= max(ya, yb) + 1e-6:
                    return za + (zb2 - za) * (y - ya) / (yb - ya) - t
            return pr[-1][1] - t
        ya, yb = (-1.55, -3.4) if s < 0 else (2.35, 3.35)
        for k in range(25):
            x = -3.85 + 7.7 * k / 24
            path = [(x, y, under(y) - 0.05) for y in np.linspace(ya, yb, 4)]
            B.add(tube(path, 0.045, 'ktbrown', 4, sm=0))
        ye = pr[-1][0]
        B.add(cbox2((X0 + 0.05, ye - 0.06, under(ye) - 0.12), (X1 - 0.05, ye + 0.06, under(ye) + 0.02), 0.01, 'ktdarkw'))
        # the frieze board closing the space between the eave beam and the roof
        yw = -1.5 if s < 0 else 2.3
        tadd(B, box((-3.1, yw - 0.04, zb_), (3.1, yw + 0.04, under(yw) + 0.02), 'ktbrown'), 'kt_grain')
    # the gable ends of the hall
    for sx in (-1, 1):
        x = sx * 2.95
        pts = [(x, -1.5, zb_)]
        for y, z in reversed(pf):
            if -1.5 < y < 0.6: pts.append((x, y, z - t + 0.02))
        pts.append((x, 0.6, zr - t + 0.02))
        for y, z in pb:
            if 0.6 < y < 2.3: pts.append((x, y, z - t + 0.02))
        pts.append((x, 2.3, zb_))
        mb = MB(); mb.face(pts, 'ktbrown', (sx, 0, 0))
        tadd(B, mb.bm(), 'kt_grain')
    ridge(B, X0 + 0.15, X1 - 0.15, 0.6, zr, h=0.36, w=0.36, mat='ktcopper', cap='ktcopper')
    # the plaque, the offering box, the bell and its rope
    B.add(bx((-0.5, -3.25, 2.9), (0.5, -3.2, 3.24), 'ktdarkw'))
    yquad(B, -0.48, 0.48, 2.91, 3.23, -3.252, 'kt_plaqueh')
    tadd(B, cbox2((-0.62, -2.3, zf), (0.62, -1.75, zf + 0.55), 0.015, 'ktdarkw'), 'kt_grain')
    yquad(B, -0.58, 0.58, zf + 0.06, zf + 0.5, -2.305, 'kt_saisen')
    for k in range(6):
        y = -2.25 + 0.09 * k
        B.add(cbox2((-0.6, y, zf + 0.55), (0.6, y + 0.05, zf + 0.62), 0.01, 'ktbrown'))
    B.add(tube([(0.0, -2.62, 3.12), (0.0, -2.62, 2.5)], 0.012, 'ktsteel', 4))
    B.add(blob((0.0, -2.62, 2.42), (0.13, 0.13, 0.12), 'ktgold', 8, 3, 1, 0.02))
    for j, mat in enumerate(('ktred', 'ktshide', 'ktpurple')):
        pts = []
        for i in range(10):
            z = 2.32 - 1.12 * i / 9
            a = j * 2.094 + i * 1.3
            pts.append((0.03 * math.cos(a), -2.62 + 0.03 * math.sin(a), z))
        B.add(tube(pts, 0.03, mat, 5))
    # the straw rope (shimenawa) across the front posts, sagging, and its paper streamers (shide)
    rope = [(x, -3.25, 2.82 - 0.16 * (1 - (x / 1.3) ** 2)) for x in np.linspace(-1.3, 1.3, 11)]
    B.add(tube(rope, 0.075, 'ktrope', 7))
    B.add(tube([(x, y - 0.02, z + 0.04) for x, y, z in rope], 0.03, 'ktrope', 5))
    for x in (-0.75, -0.25, 0.25, 0.75):
        z0 = 2.82 - 0.16 * (1 - (x / 1.3) ** 2) - 0.06
        for i in range(4):
            dx = 0.04 if i % 2 == 0 else -0.04
            B.add(cbox2((x - 0.04 + (dx if i % 2 else 0), -3.335, z0 - 0.1 * (i + 1)), (x + 0.04 + (dx if i % 2 else 0), -3.325, z0 - 0.1 * i),
                        0.002, 'ktshide'))
    return 7.0

# ================================================================ STREET
def front_uv(bm, region, x0, x1, z0, z1):
    """Map a front piece (faces toward -Y) into a tile by world x and z over the front's bounds."""
    return plane_uv(bm, region, 0, 2, (x0, z0), (x1, z1))


def convex_mirror(B):
    """A road mirror at a blind corner: an orange steel pole on a concrete collar, the bracket, one round convex mirror in
    its orange rim, facing the street and tipped down a little, the sun hood over it; the paint faded and dusty."""
    B.add(cyl(0, 0, 0.0, 0.06, 0.12, 'ktconc', 10, sm=0))
    B.add(cyl(0, 0, 0.0, 2.95, 0.038, 'ktorange', 10))
    B.add(cyl(0, 0, 2.95, 2.97, 0.045, 'ktorange', 10))
    for z in (2.62, 2.9):
        B.add(cbox2((-0.05, -0.12, z - 0.03), (0.05, 0.0, z + 0.03), 0.01, 'ktorange'))
    c = Vector((0.0, -0.17, 2.76))
    d = Vector((0.0, -1.0, -0.14)).normalized()
    M = frame(c, d, (0, 0, 1))
    rim, _ = lathe([(0.0, -0.06), (0.30, -0.06), (0.335, -0.03), (0.335, 0.02), (0.31, 0.03), (0.31, 0.0)], 20, 'ktorange', sm=1)
    B.add(xform(rim, M))
    face, _ = lathe([(0.31, 0.0), (0.24, 0.02), (0.14, 0.035), (0.0, 0.04)], 20, 'kttex', sm=1)
    plane_uv(face, 'kt_mirror', 0, 1, (-0.31, -0.31), (0.31, 0.31))
    B.add(xform(face, M))
    # the hood: a curved visor over the top half
    mb = MB()
    n = 8
    for i in range(n):
        a0 = math.radians(20 + 140 * i / n); a1 = math.radians(20 + 140 * (i + 1) / n)
        p = lambda a, r, z: (r * math.cos(a), r * math.sin(a), z)
        mb.face([p(a0, 0.335, 0.03), p(a1, 0.335, 0.03), p(a1, 0.345, 0.13), p(a0, 0.345, 0.13)], 'ktorange', None)
    hood = mb.bm()
    for f in hood.faces:
        if f.normal.dot(f.calc_center_median() * Vector((1, 1, 0))) < 0: f.normal_flip()
    bm2 = hood.copy()
    for f in bm2.faces: f.normal_flip()
    B.add(xform(hood, M)); B.add(xform(bm2, M.copy()))
    return 3.15


def phone_booth(B):
    """A green public phone in its little glass booth: a light aluminium frame (the glass itself left open to see in), a green
    roof with 公衆電話 on all four sides, kick panels, the folding door's stiles and handle; inside on its shelf the grey
    digital public phone, its handset on the hook, the directory shelf below."""
    s = 0.45
    B.add(cbox2((-s, -s, 0.0), (s, s, 0.06), 0.01, 'ktconcd'))
    for x in (-s + 0.03, s - 0.03):
        for y in (-s + 0.03, s - 0.03):
            B.add(bx((x - 0.03, y - 0.03, 0.06), (x + 0.03, y + 0.03, 2.06), 'ktphgrey'))
    for z in (0.06, 0.4, 1.0, 2.0):
        h = 0.04 if z > 0.1 else 0.06
        for y in (-s + 0.03, s - 0.03):
            B.add(box((-s + 0.03, y - 0.02, z), (s - 0.03, y + 0.02, z + h), 'ktphgrey', skip=('-x', '+x')))
        for x in (-s + 0.03, s - 0.03):
            B.add(box((x - 0.02, -s + 0.03, z), (x + 0.02, s - 0.03, z + h), 'ktphgrey', skip=('-y', '+y')))
    # kick panels on the back and sides, the door's meeting stiles and its handle
    B.add(box((-s + 0.06, s - 0.035, 0.1), (s - 0.06, s - 0.025, 0.4), 'ktphg'))
    for x in (-s + 0.03, s - 0.03):
        B.add(box((x - 0.005, -s + 0.06, 0.1), (x + 0.005, s - 0.06, 0.4), 'ktphg'))
    B.add(box((-s + 0.06, -s + 0.025, 0.1), (s - 0.06, -s + 0.035, 0.4), 'ktphg'))
    B.add(cbox2((-0.03, -s + 0.005, 0.1), (0.03, -s + 0.05, 2.0), 0.008, 'ktphgrey'))
    B.add(cbox2((0.05, -s - 0.02, 0.95), (0.08, -s + 0.01, 1.35), 0.01, 'ktchrome'))
    # the roof and the label round it
    B.add(cbox2((-s - 0.03, -s - 0.03, 2.06), (s + 0.03, s + 0.03, 2.2), 0.015, 'ktphg'))
    B.add(cbox2((-s + 0.02, -s + 0.02, 2.2), (s - 0.02, s - 0.02, 2.23), 0.01, 'ktphg'))
    yquad(B, -0.38, 0.38, 2.08, 2.18, -s - 0.032, 'kt_phonelabel')
    yquad(B, -0.38, 0.38, 2.08, 2.18, s + 0.032, 'kt_phonelabel', facing=1)
    xquad(B, -0.38, 0.38, 2.08, 2.18, s + 0.032, 'kt_phonelabel', facing=1)
    xquad(B, -0.38, 0.38, 2.08, 2.18, -s - 0.032, 'kt_phonelabel', facing=-1)
    # the shelf, the phone, its handset and cord, the directory shelf
    B.add(cbox2((-0.36, 0.12, 0.92), (0.36, 0.42, 0.96), 0.01, 'ktphgrey'))
    B.add(cbox2((-0.15, 0.2, 0.96), (0.15, 0.4, 1.38), 0.03, 'ktphgrey'))
    yquad(B, -0.14, 0.14, 0.98, 1.36, 0.198, 'kt_phone')
    B.add(cbox2((-0.135, 0.17, 1.0), (-0.085, 0.2, 1.34), 0.02, 'ktgrey'))
    B.add(tube([(-0.11, 0.17, 1.02), (-0.16, 0.14, 0.9), (-0.12, 0.18, 0.85), (-0.1, 0.2, 0.97)], 0.006, 'ktgreyd', 3))
    B.add(cbox2((-0.36, 0.12, 0.45), (0.36, 0.42, 0.48), 0.01, 'ktphgrey'))
    for k, col in enumerate(('ktbinb', 'ktyel', 'ktphgrey')):
        B.add(cbox2((-0.3 + 0.08 * k, 0.2, 0.48), (-0.24 + 0.08 * k, 0.4, 0.74), 0.005, col))
    return 2.23


def bus_stop_pole(B):
    """A bus stop's pole: a heavy round concrete foot, the grey pole, the round sign on top (the operator しおかぜバス, a bus,
    the stop 潮見坂), the timetable in its frame under a little hood; a small wooden bench beside it."""
    x = -0.62
    f, _ = lathe([(0.0, 0.0), (0.27, 0.0), (0.27, 0.1), (0.2, 0.16), (0.06, 0.18), (0.0, 0.18)], 12, 'ktconc', sm=1)
    B.add(xform(f, T(x, 0, 0)))
    B.add(cyl(x, 0, 0.18, 2.3, 0.032, 'ktgalv', 8))
    # the round sign, both faces
    for sgn in (-1, 1):
        d, _ = lathe([(0.0, 0.0), (0.255, 0.0), (0.255, 0.012)], 20, 'kttex', sm=0)
        lo, hi = (x - 0.255, 2.2 - 0.255), (x + 0.255, 2.2 + 0.255)
        xform(d, T(x, sgn * 0.012, 2.2) @ R(math.pi / 2 * (1 if sgn < 0 else -1), 'X'))
        if sgn < 0: plane_uv(d, 'kt_busround', 0, 2, lo, hi)
        else: plane_uv(d, 'kt_busround', 0, 2, (hi[0], lo[1]), (lo[0], hi[1]))
        B.add(d)
    rim, _ = lathe([(0.255, -0.014), (0.265, -0.014), (0.265, 0.014), (0.255, 0.014)], 20, 'ktgalv')
    B.add(xform(rim, T(x, 0, 2.2) @ R(math.pi / 2, 'X')))
    # the timetable
    B.add(cbox2((x - 0.22, -0.09, 1.0), (x + 0.22, -0.04, 1.72), 0.01, 'ktgalv'))
    yquad(B, x - 0.19, x + 0.19, 1.03, 1.69, -0.092, 'kt_timetable')
    B.add(cbox2((x - 0.24, -0.16, 1.72), (x + 0.24, -0.03, 1.76), 0.01, 'ktgalv'))
    for z in (1.2, 1.6):
        B.add(cbox2((x - 0.04, -0.05, z - 0.03), (x + 0.04, 0.03, z + 0.03), 0.005, 'ktgalv'))
    # the bench
    for bx in (-0.08, 0.88):
        for by in (-0.12, 0.12):
            B.add(cbox2((bx - 0.025, by - 0.025, 0.0), (bx + 0.025, by + 0.025, 0.42), 0.005, 'ktgalv'))
    for k in range(3):
        by = -0.17 + k * 0.12
        tadd(B, cbox2((-0.15, by, 0.42), (0.95, by + 0.1, 0.45), 0.01, 'ktcedw'), 'kt_grain')
    return 2.46


def vending(B, which, bin_=False):
    """A drink vending machine (invented brand; see VEND): the cabinet in the brand's colour, the front painted as one tile
    with its display of sample cans and bottles, the lit buttons, prices, the coin column, the take-out flap, given relief:
    the display's frame standing proud, the coin column, the flap's hood, the plinth; the brand's band round the sides.
    With bin_, a blue recycling box for cans and bottles stands beside it."""
    xm = -0.25 if bin_ else 0.0
    w, d, h = 1.0, 0.75, 1.83
    x0, x1 = xm - w / 2, xm + w / 2
    body = 'ktvend1' if which == 1 else 'ktvend2'
    reg = 'kt_vend%d' % which
    B.add(cbox2((x0 + 0.02, -d / 2 + 0.03, 0.0), (x1 - 0.02, d / 2, 0.06), 0.01, 'ktblk'))
    B.add(box((x0, -d / 2, 0.06), (x1, d / 2, h - 0.04), body, skip=('-y', '-z')))
    B.add(cbox2((x0 - 0.01, -d / 2 - 0.01, h - 0.05), (x1 + 0.01, d / 2 + 0.01, h), 0.01, body))
    fr = front_uv(box((x0, -d / 2 - 0.001, 0.06), (x1, -d / 2 + 0.01, h - 0.05), 'kttex', skip=('+y', '-z', '+z', '-x', '+x')), reg,
                  x0, x1, 0.06, h - 0.05)
    B.add(fr)

    def tz(v): return 0.06 + (h - 0.11) * (1 - v)          # a tile v (from the top) to a height
    def tx_(u): return x0 + w * u
    # the display's frame, proud of the face
    for (u0, u1, v0, v1) in ((0.035, 0.795, 0.035, 0.05), (0.035, 0.795, 0.56, 0.575), (0.035, 0.05, 0.035, 0.575), (0.78, 0.795, 0.035, 0.575)):
        B.add(cbox2((tx_(u0), -d / 2 - 0.03, tz(v1)), (tx_(u1), -d / 2, tz(v0)), 0.004, 'ktgrey'))
    # the coin column standing out, its face mapped to the same tile
    cc = cbox2((tx_(0.81), -d / 2 - 0.035, tz(0.555)), (tx_(0.97), -d / 2, tz(0.055)), 0.006, 'kttex')
    B.add(front_uv(cc, reg, x0, x1, 0.06, h - 0.05))
    # the flap's hood
    B.add(cbox2((tx_(0.09), -d / 2 - 0.06, tz(0.755)), (tx_(0.76), -d / 2, tz(0.74)), 0.006, 'ktgreyd'))
    B.add(cbox2((tx_(0.09), -d / 2 - 0.02, tz(0.905)), (tx_(0.76), -d / 2, tz(0.895)), 0.004, 'ktgreyd'))
    # the brand band round the sides and back
    band = 'ktcream'
    for xx, e in ((x0 - 0.003, -1), (x1 + 0.003, 1)):
        B.add(box((min(xx, xx + e * 0.002), -d / 2 + 0.02, tz(0.7)), (max(xx, xx + e * 0.002), d / 2 - 0.02, tz(0.58)), band))
    if bin_:
        bx0, bx1 = 0.32, 0.76
        B.add(cbox2((bx0, -0.2, 0.0), (bx1, 0.22, 0.86), 0.03, 'ktbinb'))
        B.add(cbox2((bx0 - 0.01, -0.21, 0.86), (bx1 + 0.01, 0.23, 0.92), 0.02, 'ktbinb'))
        yquad(B, bx0 + 0.03, bx1 - 0.03, 0.4, 0.82, -0.201, 'kt_bin')
        for xh in (bx0 + 0.12, bx1 - 0.12):
            hole, _ = lathe([(0.0, 0.0), (0.07, 0.0), (0.0, 0.002)], 10, 'ktblk')
            B.add(xform(hole, T(xh, -0.02, 0.921)))
    return h


def vending1(B): return vending(B, 1, True)
def vending2(B): return vending(B, 2, False)


def tactile_strip(B):
    """Yellow tactile paving: four 0.3 m blocks of guidance bars (running along the street), flush, a little worn and dirty."""
    for k in range(4):
        x0 = -0.6 + 0.3 * k
        col = 'ktyel'
        B.add(box((x0 + 0.002, -0.148, 0.0), (x0 + 0.298, 0.148, 0.004), col, skip=('-z',)))
        for j in range(4):
            y = -0.105 + 0.07 * j
            B.add(fbox((x0 + 0.02, y - 0.0125, 0.004), (x0 + 0.28, y + 0.0125, 0.009), 0.003, col))
    return 0.009


def manhole(B):
    """A decorated sewer cover, flush with the road: its iron frame and the coloured cast lid (an invented design for the
    town: a hydrangea over a breaking wave, a temple roof and the sun, おすい round the foot)."""
    ring, _ = lathe([(0.325, 0.0), (0.37, 0.0), (0.37, 0.006), (0.325, 0.006)], 24, 'ktgreyd')
    B.add(ring)
    lid, _ = lathe([(0.0, 0.0), (0.325, 0.0), (0.325, 0.006), (0.0, 0.006)], 24, 'kttex')
    plane_uv(lid, 'kt_manhole', 0, 1, (-0.325, -0.325), (0.325, 0.325))
    B.add(lid)
    return 0.006


def _bonsai(B, x, y, z, seed, s=1.0):
    """A black pine bonsai in a shallow glazed pot: a leaning, twisting trunk and flat pads of needles."""
    rng = np.random.default_rng(seed)
    B.add(bx((x - 0.2 * s, y - 0.13 * s, z), (x + 0.2 * s, y + 0.13 * s, z + 0.08 * s), 'ktpotg'))
    B.add(box((x - 0.18 * s, y - 0.11 * s, z + 0.08 * s), (x + 0.18 * s, y + 0.11 * s, z + 0.081 * s), 'soil'))
    pts = [(x - 0.04 * s, y, z + 0.08 * s), (x + 0.04 * s, y, z + 0.2 * s), (x - 0.05 * s, y, z + 0.33 * s), (x + 0.06 * s, y, z + 0.45 * s)]
    B.add(tube(pts, 0.03 * s, 'woodd', 5))
    for k, (px, pz, r) in enumerate(((-0.14, 0.28, 0.11), (0.14, 0.38, 0.1), (0.04, 0.5, 0.12), (-0.08, 0.44, 0.08))):
        B.add(tube([(x, y, z + pz * s - 0.03 * s), (x + px * s, y + rng.uniform(-0.03, 0.03), z + pz * s)], 0.012 * s, 'woodd', 3))
        B.add(blob((x + px * s, y, z + pz * s + 0.02 * s), (r * s, r * 0.8 * s, 0.045 * s), 'ktpine', 6, 1, seed + k, 0.2))


def _ppot(B, x, y, z, r, h, mat, seed, leaves=True):
    """A plastic plant pot (a rolled rim) of soil, with a mound of leaves (and, now and then, a few flowers)."""
    pb, _ = lathe([(r * 0.75, 0.0), (r * 0.95, h * 0.85), (r, h), (r * 0.9, h), (0.0, h * 0.9)], 8, [mat, mat, mat, 'soil'])
    B.add(xform(pb, T(x, y, z)))
    if not leaves: return
    rng = np.random.default_rng(seed + 60)
    for k in range(3):
        a = 2.1 * k + rng.random()
        B.add(blob((x + math.cos(a) * r * 0.4, y + math.sin(a) * r * 0.4, z + h + r * 0.5 + 0.03 * k), (r * 0.8, r * 0.8, r * 0.7),
                   ('leaf', 'leafd', 'ktleaf')[k], 5, 2, seed * 5 + k))
    if seed % 2:
        for k in range(4):
            a = 1.6 * k
            B.add(blob((x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5 - 0.02, z + h + r * 1.0), (0.03, 0.03, 0.025),
                       ('fl2', 'fl4', 'fl1')[seed % 3], 4, 1, k))


def pot_shelf(B):
    """A house front's stand of pots on a two-step shelf of weathered boards: two black pine bonsai in shallow pots, black and
    terracotta plastic pots of green, a morning glory in a pot climbing its little bamboo trellis with blue and purple
    flowers, a watering can."""
    # the stand: two steps of boards on legs
    for x in (-0.72, 0.0, 0.72):
        for y, zt in ((-0.12, 0.38), (0.12, 0.72)):
            tadd(B, bx((x - 0.025, y - 0.025, 0.0), (x + 0.025, y + 0.025, zt), 'ktsilv'), 'kt_grain')
    for (y0, y1, z) in ((-0.22, 0.0, 0.38), (0.02, 0.22, 0.72)):
        for k in range(2):
            ya = y0 + (y1 - y0) * k / 2
            tadd(B, bx((-0.76, ya + 0.004, z), (0.76, ya + (y1 - y0) / 2 - 0.004, z + 0.025), 'ktsilv'), 'kt_grain')
    _bonsai(B, -0.4, 0.12, 0.745, 3)
    _bonsai(B, 0.38, 0.12, 0.745, 7, 0.85)
    # plastic pots on the lower step
    for k, (x, mat, plant) in enumerate(((-0.55, 'ktpotb', 'bush'), (-0.22, 'ktpott', 'flowers'), (0.15, 'ktpotb', 'grass'),
                                         (0.5, 'ktpott', 'bush'))):
        _ppot(B, x, -0.11, 0.405, 0.1, 0.15, mat, k)
    # the morning glory on the ground, its trellis of four canes and three rings
    mx, my = 0.0, -0.42
    _ppot(B, mx, my, 0.0, 0.13, 0.2, 'ktpotb', 9, leaves=False)
    for a in range(4):
        ang = math.pi / 4 + a * math.pi / 2
        B.add(tube([(mx + 0.08 * math.cos(ang), my + 0.08 * math.sin(ang), 0.18), (mx + 0.09 * math.cos(ang), my + 0.09 * math.sin(ang), 1.18)],
                   0.007, 'ktbamboo', 4))
    for z in (0.5, 0.8, 1.1):
        B.add(tube([(mx + 0.11 * math.cos(t_), my + 0.11 * math.sin(t_), z) for t_ in np.linspace(0, 2 * math.pi, 9)], 0.004,
                   'ktbamboo', 3, caps=False))
    rng = np.random.default_rng(56)
    vine = [(mx + 0.1 * math.cos(t_ * 1.7), my + 0.1 * math.sin(t_ * 1.7), 0.2 + 0.95 * t_ / 6.0) for t_ in np.linspace(0, 6.0, 12)]
    B.add(tube(vine, 0.005, 'ktleaf', 3, caps=False))
    for k in range(12):
        t_ = rng.uniform(0.3, 6.0)
        c = (mx + 0.12 * math.cos(t_ * 1.7 + 0.3), my + 0.12 * math.sin(t_ * 1.7 + 0.3), 0.2 + 0.95 * t_ / 6.0)
        B.add(blob(c, (0.05, 0.02, 0.045), 'ktleaf' if k % 2 else 'leaf', 4, 1, k, 0.2))
    for k in range(7):
        t_ = rng.uniform(1.5, 6.0)
        ang = t_ * 1.7 - 0.4
        c = Vector((mx + 0.14 * math.cos(ang), my + 0.14 * math.sin(ang), 0.2 + 0.95 * t_ / 6.0))
        fl, _ = lathe([(0.0, 0.0), (0.05, 0.04), (0.0, 0.035)], 6, 'ktmg' if k % 3 else 'ktmgp', sm=1)
        out = Vector((math.cos(ang), math.sin(ang) - 0.6, 0.2)).normalized()
        B.add(xform(fl, frame(c, out)))
    # a watering can by the stand
    B.add(cyl(0.6, -0.4, 0.0, 0.22, 0.09, 'ktgalv', 10))
    B.add(tube([(0.68, -0.4, 0.06), (0.82, -0.4, 0.26)], 0.012, 'ktgalv', 5))
    B.add(tube([(0.53, -0.4, 0.2), (0.6, -0.4, 0.3), (0.67, -0.4, 0.2)], 0.008, 'ktgalv', 4, caps=False))
    return 1.2


def laundry_pole(B):
    """A laundry pole stand in a back yard: two stands (a weighted base, a steel post with two Y-shaped arms), two aluminium
    poles laid across their arms, wire hangers and a round pinch hanger of pegs hooked on the front pole."""
    for x in (-1.05, 1.05):
        B.add(cbox2((x - 0.18, -0.24, 0.0), (x + 0.18, 0.24, 0.1), 0.03, 'ktconc'))
        B.add(cyl(x, 0, 0.1, 1.82, 0.022, 'ktgalv', 8))
        B.add(cyl(x, 0, 0.1, 0.25, 0.04, 'ktgalv', 8))
        # the cross bar at the top, a hook turned up at each end for a pole, a lower bar for a second height
        for z, ya in ((1.76, 0.3), (1.36, 0.26)):
            B.add(tube([(x, -ya, z), (x, ya, z)], 0.014, 'ktgalv', 5))
            for sgn in (-1, 1):
                B.add(tube([(x, sgn * (ya - 0.05), z), (x, sgn * ya, z + 0.01), (x, sgn * (ya + 0.012), z + 0.07)], 0.009, 'ktgalv', 4))
        B.add(tube([(x, -0.3, 1.76), (x, 0.0, 1.6), (x, 0.3, 1.76)], 0.008, 'ktgalv', 4, caps=False))
    poles = ((-0.27, 1.79), (0.27, 1.79))
    for y, z in poles:
        B.add(tube([(-1.3, y, z), (1.3, y, z)], 0.017, 'ktwire', 8))
    yp, zp = poles[0]
    for k, x in enumerate((-0.7, -0.55, -0.4, 0.55)):
        top = (x, yp, zp + 0.02)
        hk = [(x, yp + 0.03, zp - 0.02), (x, yp, zp + 0.035), (x, yp - 0.025, zp), (x, yp - 0.01, zp - 0.06)]
        B.add(tube(hk, 0.003, 'ktwire', 3, caps=False))
        sh = [(x, yp - 0.01, zp - 0.06), (x - 0.2, yp - 0.01, zp - 0.2), (x + 0.2, yp - 0.01, zp - 0.2), (x, yp - 0.01, zp - 0.06)]
        B.add(tube(sh, 0.004, 'ktwire' if k % 2 else 'ktpeg', 3, caps=False))
    # the round pinch hanger
    cx, cz = 0.1, zp - 0.32
    B.add(tube([(cx, yp, zp), (cx, yp, cz + 0.02)], 0.004, 'ktwire', 3, caps=False))
    B.add(tube([(cx + 0.18 * math.cos(a), yp + 0.18 * math.sin(a), cz) for a in np.linspace(0, 2 * math.pi, 13)], 0.008, 'ktpeg', 4, caps=False))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        B.add(tube([(cx, yp, cz + 0.02), (cx + 0.18 * math.cos(a), yp + 0.18 * math.sin(a), cz)], 0.003, 'ktpeg', 3, caps=False))
    for k in range(10):
        a = 2 * math.pi * k / 10
        px, py = cx + 0.18 * math.cos(a), yp + 0.18 * math.sin(a)
        B.add(cbox2((px - 0.008, py - 0.012, cz - 0.07), (px + 0.008, py + 0.012, cz - 0.005), 0.003, 'ktpeg' if k % 2 else 'ktshide'))
    return 1.9


def corrugated_shed(B):
    """A small storage shed of corrugated sheet gone to rust: a timber frame on concrete blocks, corrugated walls, two
    sliding doors in their rails with a padlocked hasp, a lean-to roof of big-wave sheet overhanging the front, sloping down
    to the back."""
    W, D = 2.4, 1.6
    x0, x1, y0, y1 = -W / 2 + 0.06, W / 2 - 0.06, -D / 2 + 0.06, D / 2 - 0.08
    zb, zf, zbk = 0.14, 1.98, 1.78
    for x in (x0 + 0.1, x1 - 0.1):
        for y in (y0 + 0.08, y1 - 0.08):
            B.add(cbox2((x - 0.2, y - 0.1, 0.0), (x + 0.2, y + 0.1, zb), 0.01, 'ktconc'))
    B.add(box((x0, y0, zb), (x1, y1, zb + 0.06), 'ktdarkw'))

    def ztop(y): return zf + (zbk - zf) * (y - y0) / (y1 - y0)
    # walls: back and sides, mapped with the corrugated tile by their own lengths
    mb = MB()
    mb.face([(x1, y1, zb), (x0, y1, zb), (x0, y1, zbk), (x1, y1, zbk)], 'kttex', (0, 1, 0), 1.0,
            lambda co: reg_uv('kt_corr', (x1 - co.x) / (x1 - x0), (co.z - zb) / (zf - zb), 0.0))
    for x, e in ((x0, -1), (x1, 1)):
        pts = [(x, y0, zb), (x, y1, zb), (x, y1, zbk), (x, y0, zf)]
        if e < 0: pts = pts[::-1]
        mb.face(pts, 'kttex', (e, 0, 0), 1.0, lambda co: reg_uv('kt_corr', (co.y - y0) / (y1 - y0) * 0.66, (co.z - zb) / (zf - zb), 0.0))
    B.add(mb.bm())
    # the front: posts, the header, two sliding doors (one a little open), the rails, the hasp and padlock
    for x in (x0, x1, 0.0):
        tadd(B, cbox2((x - 0.045, y0 - 0.04, zb), (x + 0.045, y0 + 0.04, zf), 0.005, 'ktdarkw'), 'kt_grain')
    tadd(B, cbox2((x0 - 0.04, y0 - 0.05, zf - 0.16), (x1 + 0.04, y0 + 0.04, zf), 0.005, 'ktdarkw'), 'kt_grain')
    B.add(cbox2((x0, y0 - 0.06, zb + 0.02), (x1, y0 - 0.02, zb + 0.06), 0.005, 'ktrustp'))
    B.add(cbox2((x0, y0 - 0.07, zf - 0.2), (x1, y0 - 0.03, zf - 0.16), 0.005, 'ktrustp'))
    for (a, b, yy) in ((x0 + 0.03, 0.06, y0 - 0.07), (-0.02, x1 - 0.03, y0 - 0.11)):
        q = MB()
        q.face([(a, yy, zb + 0.07), (b, yy, zb + 0.07), (b, yy, zf - 0.2), (a, yy, zf - 0.2)], 'kttex', (0, -1, 0), 1.0,
               lambda co, a=a, b=b: reg_uv('kt_corr', 0.1 + 0.4 * (co.x - a) / (b - a), (co.z - zb) / (zf - zb), 0.0))
        B.add(q.bm())
        for (u0, u1, v0, v1) in ((a, a + 0.04, zb + 0.07, zf - 0.2), (b - 0.04, b, zb + 0.07, zf - 0.2), (a, b, zb + 0.07, zb + 0.11),
                                 (a, b, zf - 0.24, zf - 0.2)):
            B.add(cbox2((u0, yy - 0.015, v0), (u1, yy + 0.005, v1), 0.004, 'ktrustp'))
    B.add(cbox2((-0.08, y0 - 0.14, 1.0), (0.04, y0 - 0.11, 1.07), 0.005, 'ktsteel'))
    B.add(cbox2((-0.03, y0 - 0.17, 0.92), (0.01, y0 - 0.13, 0.99), 0.005, 'ktgold'))
    # the roof: big-wave corrugated sheet, its waves along X, overhanging the front and sides
    rx0, rx1, ry0, ry1 = -W / 2, W / 2, -D / 2, D / 2
    n = 18
    mb = MB()
    zr0, zr1 = ztop(ry0) + 0.06, ztop(ry1) + 0.06
    for i in range(n):
        xa = rx0 + (rx1 - rx0) * i / n; xb = rx0 + (rx1 - rx0) * (i + 0.5) / n; xc = rx0 + (rx1 - rx0) * (i + 1) / n
        for (p, q, hp, hq) in ((xa, xb, 0.0, 0.025), (xb, xc, 0.025, 0.0)):
            pts = [(p, ry0, zr0 + hp), (q, ry0, zr0 + hq), (q, ry1, zr1 + hq), (p, ry1, zr1 + hp)]
            mb.face(pts, 'kttex', (0, 0.1, 1), 1.0,
                    lambda co: reg_uv('kt_corr', (co.x - rx0) / (rx1 - rx0), 0.2 + 0.8 * (co.y - ry0) / (ry1 - ry0), 0.0))
    mb.face([(rx0, ry0, zr0 - 0.005), (rx0, ry1, zr1 - 0.005), (rx1, ry1, zr1 - 0.005), (rx1, ry0, zr0 - 0.005)], 'ktrustp', (0, 0, -1))
    mb.face([(rx0, ry0, zr0 - 0.005), (rx1, ry0, zr0 - 0.005), (rx1, ry0, zr0 + 0.025), (rx0, ry0, zr0 + 0.025)], 'ktrustp', (0, -1, 0))
    B.add(mb.bm())
    tadd(B, cbox2((x0 - 0.05, y0 - 0.06, ztop(y0) - 0.02), (x1 + 0.05, y0 + 0.04, ztop(y0) + 0.06), 0.005, 'ktdarkw'), 'kt_grain')
    return zr0 + 0.03

# ================================================================ TRAM
TRAM_CAR, TRAM_GAP, TRAM_W = 12.4, 0.2, 2.5
WIRE_Z = 4.9                       # the contact wire's height over the rail (TramPoleKM's Attach.Wire, the pantograph's head)


def _livery(u0, u1):
    """The tram's livery as wall zones: deep green below the windows, cream above, a green band under the roof."""
    return [(u0, u1, 0.95, 1.62, 'kttg'), (u0, u1, 3.3, 3.45, 'kttg')]


def reveal_mb(u0, u1, v0, v1, dep, bottom=True, mat='ktsoffit'):
    """An opening's reveal in a wall's own space (u, v, w out), dep deep: its faces looking into the opening."""
    mb = MB()
    mb.face([(u0, v1, 0.0), (u1, v1, 0.0), (u1, v1, -dep), (u0, v1, -dep)], mat, (0, -1, 0), 0.6)
    mb.face([(u0, v0, 0.0), (u0, v1, 0.0), (u0, v1, -dep), (u0, v0, -dep)], mat, (1, 0, 0), 0.75)
    mb.face([(u1, v0, 0.0), (u1, v1, 0.0), (u1, v1, -dep), (u1, v0, -dep)], mat, (-1, 0, 0), 0.75)
    if bottom:
        mb.face([(u0, v0, 0.0), (u1, v0, 0.0), (u1, v0, -dep), (u0, v0, -dep)], mat, (0, 1, 0), 0.9)
    return mb


def tram_car(B, xc, s, panto=False, num='kt_num1'):
    """One car of the tram, 12.4 m, its cab toward s (-1: -X, +1: +X), centred at xc. A car-local a runs from 0 at the cab's
    face to 12.4 at the coupled end; world x = xc + s * (6.2 - a)."""
    L, Wd = TRAM_CAR, TRAM_W
    y0, y1 = -Wd / 2, Wd / 2
    zb, ze = 0.95, 3.45

    def X(a): return xc + s * (L / 2 - a)
    ch = 0.16                                                     # the cab corners' chamfer
    wins = [(0.35, 0.95)] + [(a, a + 1.12) for a in (2.25, 3.6, 4.95, 6.3)] + [(9.25, 10.37), (10.6, 11.72)]
    doors = [(0.98, 2.08), (7.6, 8.9)]
    ops_a = [(a0, a1, 1.75, 2.78) for a0, a1 in wins] + [(a0, a1, zb, 3.0) for a0, a1 in doors]
    for side in (-1, 1):
        y = side * Wd / 2
        # the wall frame runs along +X on the near side (facing -Y) and along -X on the far side
        ux = 1 if side < 0 else -1
        wf = WF((0, y, 0), (ux, 0, 0), 'front' if side < 0 else 'back')

        def U(a): return ux * X(a)
        ua, ub = sorted((U(ch), U(L)))
        ops = [tuple(sorted((U(a0), U(a1)))) + (v0, v1) for a0, a1, v0, v1 in ops_a]
        wall(B, wf, ua, ub, ze, ops, v0=zb, mat='kttc', zones=_livery(ua, ub))
        for (u0, u1, v0, v1), (a0, a1, _, _) in zip(ops, ops_a):
            door = v0 < 1.0
            dep = 0.05 if not door else 0.04
            put(B, wf, reveal_mb(u0, u1, v0, v1, dep, bottom=not door).bm())
            if not door:
                g = MB()
                g.face([(u0, v0, -dep), (u1, v0, -dep), (u1, v1, -dep), (u0, v1, -dep)], 'kttex', (0, 0, 1), 1.0,
                       lambda co, u0=u0, u1=u1, v0=v0, v1=v1: reg_uv('kt_tramglass', (co.x - u0) / (u1 - u0), (co.y - v0) / (v1 - v0), 0.0))
                put(B, wf, g.bm())
                put(B, wf, fbox((u0, 2.33, -dep), (u1, 2.37, -dep + 0.02), 0.005, 'ktchrome'))
                if side < 0: B.feat('front', 'streak', a0=min(X(a0), X(a1)), a1=max(X(a0), X(a1)), b=1.75, length=0.5, k=1.0)
            else:
                # two sliding leaves: cream, green below, a tall window each, the meeting seam
                um = (u0 + u1) / 2
                for p, q in ((u0, um - 0.005), (um + 0.005, u1)):
                    lf = MB()
                    lf.face([(p, v0 + 0.02, -dep), (q, v0 + 0.02, -dep), (q, v1 - 0.02, -dep), (p, v1 - 0.02, -dep)], 'kttc', (0, 0, 1))
                    lf.face([(p, v0 + 0.02, -dep + 0.002), (q, v0 + 0.02, -dep + 0.002), (q, 1.62, -dep + 0.002), (p, 1.62, -dep + 0.002)],
                            'kttg', (0, 0, 1))
                    lf.face([(p + 0.07, 1.8, -dep + 0.003), (q - 0.07, 1.8, -dep + 0.003), (q - 0.07, 2.8, -dep + 0.003), (p + 0.07, 2.8, -dep + 0.003)],
                            'kttex', (0, 0, 1), 1.0, lambda co, p=p, q=q: reg_uv('kt_tramglass', (co.x - p - 0.07) / (q - p - 0.14), (co.y - 1.8), 0.0))
                    put(B, wf, lf.bm())
                put(B, wf, fbox((um - 0.012, v0 + 0.02, -dep), (um + 0.012, v1 - 0.02, -dep + 0.012), 0.004, 'ktrubber'))
                put(B, wf, fbox((u0 - 0.05, zb - 0.12, -0.0), (u1 + 0.05, zb, 0.06), 0.01, 'ktsteel'))       # the step
        # the side destination plate and the car's number
        dq = MB(); a_, b_ = sorted((U(2.6), U(4.6)))
        dq.face([(a_, 2.88, 0.013), (b_, 2.88, 0.013), (b_, 3.12, 0.013), (a_, 3.12, 0.013)], 'kttex', (0, 0, 1), 1.0,
                lambda co, a_=a_, b_=b_: reg_uv('kt_tramside', (co.x - a_) / (b_ - a_), (co.y - 2.88) / 0.24, 0.0))
        put(B, wf, dq.bm())
        nq = MB(); a_, b_ = sorted((U(0.4), U(0.85)))
        nq.face([(a_, 1.2, 0.006), (b_, 1.2, 0.006), (b_, 1.42, 0.006), (a_, 1.42, 0.006)], 'kttex', (0, 0, 1), 1.0,
                lambda co, a_=a_, b_=b_: reg_uv(num, (co.x - a_) / (b_ - a_), (co.y - 1.2) / 0.22, 0.0))
        put(B, wf, nq.bm())
    # the cab end: its face and chamfered corners, the windscreen, the destination window, lamps, number, wipers, bumper
    xf = X(0.0)
    cab = WF((xf, 0, 0), (0, s, 0), 'right' if s > 0 else 'left')     # u along the face, w out of it (toward s)
    yc = Wd / 2 - ch
    wall(B, cab, -yc, yc, ze, [(-1.0, -0.06, 1.8, 2.85), (0.06, 1.0, 1.8, 2.85), (-0.48, 0.48, 2.94, 3.22)], v0=zb, mat='kttc',
         zones=_livery(-yc, yc))
    for yy in (-1, 1):
        P0 = Vector((xf, yy * yc, 0)); P1 = Vector((X(ch), yy * Wd / 2, 0))
        if (P1 - P0).cross(Vector((0, 0, 1))).dot(Vector((s, yy, 0))) < 0: P0, P1 = P1, P0
        cw = WF(P0, P1 - P0, 'front')
        ln = (P1 - P0).length
        wall(B, cw, 0.0, ln, ze, [], v0=zb, mat='kttc', zones=_livery(0.0, ln))
    for (u0, u1, v0, v1), reg in (((-1.0, -0.06, 1.8, 2.85), 'kt_tramglass'), ((0.06, 1.0, 1.8, 2.85), 'kt_tramglass'),
                                  ((-0.48, 0.48, 2.94, 3.22), 'kt_tramdest')):
        g = MB()
        g.face([(u0, v0, -0.03), (u1, v0, -0.03), (u1, v1, -0.03), (u0, v1, -0.03)], 'kttex', (0, 0, 1), 1.0,
               lambda co, u0=u0, u1=u1, v0=v0, v1=v1, reg=reg: reg_uv(reg, (co.x - u0) / (u1 - u0), (co.y - v0) / (v1 - v0), 0.0))
        put(B, cab, g.bm())
        put(B, cab, reveal_mb(u0, u1, v0, v1, 0.03, mat='ktrubber').bm())
    for u in (-0.5, 0.5):
        put(B, cab, fbox((u - 0.01, 1.85, 0.0), (u + 0.01, 2.4, 0.03), 0.004, 'ktblk'))
    for u in (-0.72, 0.72):
        lb, _ = lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.05), (0.1, 0.06)], 10, 'ktchrome')
        lmp, _ = lathe([(0.0, 0.06), (0.1, 0.06), (0.0, 0.08)], 10, 'ktlight')
        for bm in (lb, lmp):
            xform(bm, T(u, 1.32, 0.0))
            put(B, cab, bm)
        put(B, cab, fbox((u + (0.2 if u > 0 else -0.28), 1.27, 0.0), (u + (0.28 if u > 0 else -0.2), 1.37, 0.02), 0.005, 'ktred'))
    B.lamps.append({'center': tuple(cab.P(-0.72, 1.32, 0.08)), 'kind': 'head'})
    B.lamps.append({'center': tuple(cab.P(0.72, 1.32, 0.08)), 'kind': 'head'})
    nq = MB()
    nq.face([(-0.2, 1.62, 0.006), (0.2, 1.62, 0.006), (0.2, 1.8, 0.006), (-0.2, 1.8, 0.006)], 'kttex', (0, 0, 1), 1.0,
            lambda co: reg_uv(num, (co.x + 0.2) / 0.4, (co.y - 1.62) / 0.18, 0.0))
    put(B, cab, nq.bm())
    put(B, cab, fbox((-yc, 0.82, 0.0), (yc, 0.98, 0.12), 0.02, 'ktbogie'))                    # the anti-climber / bumper
    put(B, cab, fbox((-0.12, 0.7, 0.0), (0.12, 0.84, 0.28), 0.02, 'ktbogie'))                 # the coupler's head
    # the roof: an arched section from the cab's face (a little visor) to the coupled end
    sec = [(-1.27, 3.43), (-1.22, 3.58), (-0.98, 3.72), (-0.55, 3.82), (0.0, 3.86), (0.55, 3.82), (0.98, 3.72), (1.22, 3.58), (1.27, 3.43)]
    xa, xb = sorted((X(-0.06), X(L)))
    mb = MB()
    for (ya, za), (yb, zb2) in zip(sec[:-1], sec[1:]):
        mb.face([(xa, ya, za), (xa, yb, zb2), (xb, yb, zb2), (xb, ya, za)], 'kttroof', (0, ya + yb, 1))
    for x, e in ((xa, -1), (xb, 1)):
        mb.face([(x, y, z) for y, z in sec], 'kttroof', (e, 0, 0))
    mb.face([(xa, -1.27, 3.43), (xb, -1.27, 3.43), (xb, 1.27, 3.43), (xa, 1.27, 3.43)], 'ktsoffit', (0, 0, -1))
    B.add(mb.bm())
    # roof equipment: a long box, ventilators, (the pantograph on one car)
    xm = X(6.6)
    B.add(cbox2((xm - 1.6, -0.55, 3.84), (xm + 1.6, 0.55, 4.06), 0.04, 'ktgrey'))
    for a in (4.0, 9.8):
        B.add(cbox2((X(a) - 0.3, -0.3, 3.84), (X(a) + 0.3, 0.3, 3.98), 0.06, 'kttroof'))
    if panto:
        pa = 2.6
        xp = X(pa)
        for dx in (-0.35, 0.35):
            for dy in (-0.3, 0.3):
                B.add(cyl(xp + dx, dy, 3.85, 3.98, 0.045, 'ktinsul', 6))
        B.add(cbox2((xp - 0.45, -0.38, 3.98), (xp + 0.45, 0.38, 4.03), 0.01, 'ktbogie'))
        k_x = X(pa + 0.95)
        hx = X(pa + 0.15)
        B.add(tube([(xp, -0.18, 4.04), (k_x, -0.05, 4.52)], 0.03, 'ktsteel', 6))
        B.add(tube([(xp, 0.18, 4.04), (k_x, 0.05, 4.52)], 0.03, 'ktsteel', 6))
        B.add(tube([(k_x, 0.0, 4.52), (hx, 0.0, WIRE_Z - 0.06)], 0.022, 'ktsteel', 6))
        B.add(tube([(xp + s * -0.2, 0.0, 4.04), (X(pa + 0.7), 0.0, 4.25)], 0.02, 'ktsteel', 5))
        for dx in (-0.05, 0.05):
            B.add(tube([(hx + dx, -0.62, WIRE_Z - 0.12), (hx + dx, -0.5, WIRE_Z - 0.02), (hx + dx, 0.5, WIRE_Z - 0.02),
                        (hx + dx, 0.62, WIRE_Z - 0.12)], 0.018, 'ktsteel', 5))
        B.add(bx((hx - 0.06, -0.5, WIRE_Z - 0.03), (hx + 0.06, 0.5, WIRE_Z), 'ktgreyd'))
    # under the floor: the skirt, equipment boxes, the two bogies, the coupled end's gangway and coupler
    xs0, xs1 = sorted((X(0.1), X(L - 0.05)))
    B.add(box((xs0, -0.95, 0.62), (xs1, 0.95, zb), 'ktbogie', skip=('+z',)))
    for a in (2.3, 10.1):
        x = X(a)
        B.add(bx((x - 1.15, -0.72, 0.36), (x + 1.15, -0.6, 0.6), 'ktbogie'))
        B.add(bx((x - 1.15, 0.6, 0.36), (x + 1.15, 0.72, 0.6), 'ktbogie'))
        B.add(bx((x - 0.15, -0.72, 0.5), (x + 0.15, 0.72, 0.62), 'ktbogie'))
        for dx in (-0.85, 0.85):
            for yy in (-0.5, 0.5):
                tw, _ = lathe([(0.0, -0.06), (0.33, -0.06), (0.33, 0.06), (0.0, 0.06)], 10, 'ktsteel', sm=0)
                B.add(xform(tw, T(x + dx, yy, 0.33) @ R(math.pi / 2, 'X')))
            for yy in (-0.74, 0.74):
                B.add(cyl(x + dx, yy, 0.25, 0.42, 0.07, 'ktbogie', 6))
        for dx in (-0.4, 0.4):
            B.add(cyl(x + dx, -0.73, 0.42, 0.6, 0.06, 'ktsteel', 6))
    xg = X(L)
    B.add(bx((min(xg, xg - s * 0.1), -0.7, 1.0), (max(xg, xg - s * 0.1), 0.7, 3.1), 'ktrubber'))
    return 4.06


def tram(B):
    """The town's little seaside tram (an invented livery: deep green below the windows, cream above, a green band under the
    grey roof), two 12.4 m cars coupled by a short gangway, 25 m over all, 2.5 m wide: each car a cab end with its raked
    windscreen, the destination window (潮見ヶ浜), two headlamps and red tail lamps, the car's number; two pairs of sliding
    doors and the windows on each side (an empty car beyond the glass), the side destination plate (鎌倉 ⇔ 潮見ヶ浜), rain
    streaks under the windows; the bogies with their wheels and springs, the skirt; on the first car's roof a single-arm
    pantograph raised to the wire (4.9 m over the rail). The origin is the centre of the whole tram on the rail; nobody
    aboard."""
    half = (TRAM_CAR + TRAM_GAP) / 2
    B.feat('front', 'ao', a0=-TRAM_CAR - 0.2, a1=TRAM_CAR + 0.2, b=3.45, length=0.3, k=0.35)
    tram_car(B, -half, -1, panto=True, num='kt_num1')
    tram_car(B, half, 1, panto=False, num='kt_num2')
    B.add(bx((-0.2, -0.08, 0.72), (0.2, 0.08, 0.84), 'ktbogie'))
    return WIRE_Z


def tram_pole(B):
    """A catenary pole by the single track: a tapered concrete pole 7 m tall on its footing, a steel cantilever bracket
    reaching 1.8 m toward the track (-Y) at 5.6 m with its diagonal stay, porcelain insulators by the pole, a hanger down to
    the clamp that holds the contact wire (Attach.Wire, 4.9 m), a band with the pole's number plate."""
    f, _ = lathe([(0.0, 0.0), (0.24, 0.0), (0.24, 0.18), (0.18, 0.22), (0.0, 0.22)], 10, 'ktconc', sm=1)
    B.add(f)
    p, _ = lathe([(0.0, 0.0), (0.165, 0.0), (0.115, 7.0), (0.0, 7.02)], 12, 'ktconc', sm=1)
    B.add(p)
    for z in (5.6, 6.35):
        B.add(cyl(0, 0, z - 0.08, z + 0.08, 0.135, 'ktgalv', 10))
    zb = 5.6
    # bracket and stay, insulators near the pole
    B.add(tube([(0.0, -0.14, zb), (0.0, -0.45, zb)], 0.03, 'ktgalv', 6))
    for k in range(3):
        y = -0.48 - k * 0.07
        d = disc_y(0.0, y, zb, 0.07, 0.04, 'ktinsul', 8, back=True)
        B.add(d)
    B.add(tube([(0.0, -0.7, zb), (0.0, -2.0, zb)], 0.03, 'ktgalv', 6))
    B.add(tube([(0.0, -0.14, 6.35), (0.0, -0.45, 6.2)], 0.022, 'ktgalv', 5))
    for k in range(2):
        y = -0.48 - k * 0.07
        B.add(disc_y(0.0, y, 6.18 - k * 0.02, 0.06, 0.04, 'ktinsul', 8, back=True))
    B.add(tube([(0.0, -0.62, 6.15), (0.0, -1.9, zb + 0.02)], 0.018, 'ktgalv', 5))
    # the hanger and the clamp at the wire
    B.add(tube([(0.0, -1.8, zb), (0.0, -1.8, WIRE_Z + 0.05)], 0.012, 'ktgalv', 4))
    B.add(cbox2((-0.12, -1.83, WIRE_Z - 0.01), (0.12, -1.77, WIRE_Z + 0.05), 0.01, 'ktgalv'))
    B.attach.append(('Attach.Wire', (0.0, -1.8, WIRE_Z)))
    # the number plate
    B.add(box((-0.1, -0.135, 2.4), (0.1, -0.12, 2.65), 'white'))
    B.add(box((-0.07, -0.136, 2.45), (0.07, -0.135, 2.6), 'ktblk'))
    return 7.02


def _stripe_box(B, lo, hi, region, axis=1, span=1.0):
    """A box striped along `axis` (0 or 1) with the diagonal-stripe tile: the faces map s along the axis (span of the
    tile's length), t across."""
    bm = box(lo, hi, 'kttex')
    lu = L(bm)[3]
    a = axis
    for f in bm.faces:
        n = f.normal
        other = 2 if abs(n[2]) < 0.5 else (1 - a)
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv(region, span * (co[a] - lo[a]) / (hi[a] - lo[a]), (co[other] - lo[other]) / (hi[other] - lo[other]), 0.0)
    return B.add(bm)


def crossing_signal(B):
    """A level crossing's warning signal: a post striped black and yellow up to the 踏切 sign, the direction indicator (its
    arrows), two round red lamps side by side under their hoods on a black board facing the road (Attach.LampL, LampR; the
    same pair on the back), the crossbuck of striped boards, the alarm bell on top."""
    B.add(cbox2((-0.22, -0.22, 0.0), (0.22, 0.22, 0.12), 0.02, 'ktconc'))
    post = cyl(0, 0, 0.12, 1.62, 0.06, 'kttex', 8, caps=(False, False))
    lu = L(post)[3]
    for f in post.faces:
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv('kt_stripev', (math.atan2(-co.x, -co.y) / (2 * math.pi)) % 1.0, (co.z - 0.12) / 1.5, 0.0)
    B.add(post)
    B.add(cyl(0, 0, 1.62, 3.62, 0.062, 'ktgrey', 8))
    # the 踏切 sign
    B.add(bx((-0.27, -0.09, 1.66), (0.27, -0.065, 1.98), 'ktgrey'))
    yquad(B, -0.26, 0.26, 1.67, 1.97, -0.091, 'kt_fumikiri')
    # the direction indicator
    B.add(cbox2((-0.2, -0.16, 2.06), (0.2, -0.05, 2.26), 0.01, 'ktblk'))
    yquad(B, -0.18, 0.18, 2.08, 2.24, -0.161, 'kt_direction')
    # the lamps on their arm, front and back
    B.add(bx((-0.6, -0.04, 2.56), (0.6, 0.04, 2.64), 'ktgreyd'))
    for sgn, ysgn in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = sgn * 0.33
        B.add(disc_y(x, ysgn * 0.05, 2.6, 0.26, 0.03, 'ktblk', 16, ysgn, back=True))
        B.add(disc_y(x, ysgn * 0.08, 2.6, 0.12, 0.03, 'ktlamp', 12, ysgn))
        mb = MB()
        for i in range(7):
            a0 = math.pi * i / 7; a1 = math.pi * (i + 1) / 7
            p = lambda a, y: (x + 0.135 * math.cos(a), y, 2.6 + 0.135 * math.sin(a))
            mb.face([p(a0, ysgn * 0.08), p(a1, ysgn * 0.08), p(a1, ysgn * 0.3), p(a0, ysgn * 0.3)], 'ktblk', None)
        hood = mb.bm()
        back = hood.copy()
        for f in back.faces: f.normal_flip()
        B.add(hood); B.add(back)
    B.attach.append(('Attach.LampL', (-0.33, -0.11, 2.6)))
    B.attach.append(('Attach.LampR', (0.33, -0.11, 2.6)))
    # the crossbuck: two striped boards crossing in an X
    for sgn in (-1, 1):
        bm = box((-0.62, -0.03, -0.075), (0.62, 0.0, 0.075), 'kttex')
        lu = L(bm)[3]
        for f in bm.faces:
            for l in f.loops:
                co = l.vert.co
                l[lu].uv = reg_uv('kt_stripe', (co.x + 0.62) / 1.24, (co.z + 0.075) / 0.15, 0.0)
        xform(bm, T(0, -0.07 - (0.032 if sgn > 0 else 0.0), 3.2) @ R(sgn * math.radians(32), 'Y'))
        B.add(bm)
    # the bell
    bl, _ = lathe([(0.0, 3.62), (0.15, 3.62), (0.16, 3.66), (0.13, 3.76), (0.06, 3.82), (0.0, 3.83)], 12, 'ktblk', sm=1)
    B.add(bl)
    return 3.83


def crossing_bar(B):
    """The crossing's barrier: the gate machine on its concrete pad (a grey cabinet striped at the foot, the motor housing),
    and the striped arm 4.0 m long reaching out along -Y at 1.0 m (lowered), from its hinge (Attach.Pivot) beside the
    cabinet, the counterweight behind, a red reflector at its tip."""
    B.add(cbox2((-0.35, -0.3, 0.0), (0.35, 0.3, 0.08), 0.01, 'ktconc'))
    _stripe_box(B, (-0.2, -0.17, 0.08), (0.2, 0.17, 0.5), 'kt_stripe', axis=0, span=0.25)
    B.add(cbox2((-0.2, -0.17, 0.5), (0.2, 0.17, 1.2), 0.02, 'ktgrey'))
    B.add(cbox2((-0.22, -0.19, 1.2), (0.22, 0.19, 1.26), 0.01, 'ktgreyd'))
    hub, _ = lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.1), (0.0, 0.1)], 10, 'ktgreyd')
    B.add(xform(hub, T(0.2, 0.0, 1.0) @ R(math.pi / 2, 'Y')))
    px = 0.34
    B.attach.append(('Attach.Pivot', (px, 0.0, 1.0)))
    _stripe_box(B, (px - 0.04, -4.0, 0.955), (px + 0.04, 0.0, 1.045), 'kt_stripe', axis=1)
    B.add(bx((px - 0.05, 0.0, 0.94), (px + 0.05, 0.5, 1.06), 'ktgreyd'))
    B.add(cbox2((px - 0.08, 0.35, 0.86), (px + 0.08, 0.6, 1.1), 0.02, 'ktgreyd'))
    B.add(disc_y(px, -4.0, 1.0, 0.04, 0.01, 'ktred', 8, -1))
    return 1.26


def track(B):
    """A 4.0 m segment of the single track: two rails (their heads worn bright) on seven concrete sleepers with their clips,
    in a bed of ballast stained rust-brown between the rails. It tiles end to end along X; the rails' tops are at 0.32 m
    (Attach.RailTop), where the tram's origin sits."""
    Lh = 2.0
    # the ballast bed: a flat top and sloping shoulders
    prof = [(-1.75, 0.0), (-1.35, 0.14), (1.35, 0.14), (1.75, 0.0)]
    mb = MB()
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
        mb.face([(-Lh, ya, za), (-Lh, yb, zb), (Lh, yb, zb), (Lh, ya, za)], 'kttex', (0, ya + yb, 1), 1.0,
                lambda co: reg_uv('kt_ballast', (co.x + Lh) / (2 * Lh), (co.y + 1.75) / 3.5, 0.0))
    for x, e in ((-Lh, -1), (Lh, 1)):
        mb.face([(x, y, z) for y, z in prof], 'kttex', (e, 0, 0), 0.9, lambda co: reg_uv('kt_ballast', 0.5, (co.y + 1.75) / 3.5, 0.0))
    B.add(mb.bm())
    n = 7
    for k in range(n):
        x = -Lh + (k + 0.5) * 2 * Lh / n
        B.add(bx((x - 0.12, -1.0, 0.1), (x + 0.12, 1.0, 0.18), 'ktconc'))
        for y in (-0.566, 0.566):
            for d in (-0.06, 0.06):
                B.add(bx((x - 0.04, y + d - 0.02, 0.18), (x + 0.04, y + d + 0.02, 0.21), 'ktbogie'))
    # the rails: a section swept along X, the head's top bright
    sec = [(-0.065, 0.0), (0.065, 0.0), (0.065, 0.012), (0.009, 0.03), (0.009, 0.095), (0.033, 0.103), (0.033, 0.145),
           (-0.033, 0.145), (-0.033, 0.103), (-0.009, 0.095), (-0.009, 0.03), (-0.065, 0.012)]
    zr = 0.175
    for yc in (-0.566, 0.566):
        mb = MB()
        m = len(sec)
        for i in range(m):
            (ya, za), (yb, zb) = sec[i], sec[(i + 1) % m]
            mat = 'ktchrome' if (za == 0.145 and zb == 0.145) else 'ktrail'
            mb.face([(-Lh, yc + ya, zr + za), (-Lh, yc + yb, zr + zb), (Lh, yc + yb, zr + zb), (Lh, yc + ya, zr + za)], mat, None)
        B.add(mb.bm())
    B.attach.append(('Attach.RailTop', (0.0, 0.0, zr + 0.145)))
    return zr + 0.145

# ================================================================ VEHICLES
def ybody(B, outline, w, mat, arches=(), well='ktblk'):
    """A body symmetric about y = 0, w wide: the outline extruded, both sides closed."""
    pts = list(outline)
    if arches:
        bottom_z = pts[0][1]
        cut = [pts[0]]
        for (ax, az, r) in sorted(arches):
            h = max(0.0, bottom_z - az)
            a0 = math.asin(min(1.0, h / r))
            for i in range(9):
                ang = (math.pi - a0) - (math.pi - 2 * a0) * i / 8
                cut.append((ax + r * math.cos(ang), az + r * math.sin(ang)))
        pts = cut + pts[1:]
    n = len(pts)
    V = [(x, -w / 2, z) for x, z in pts] + [(x, w / 2, z) for x, z in pts]
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(reversed(range(n)))
    F = [idx, [n + i for i in reversed(idx)]]
    M = [mat, mat]
    for j in range(n):
        a, b = idx[j], idx[(j + 1) % n]
        F.append([a, n + a, n + b, b]); M.append(mat)
    bm, faces = bm_from(V, F, M)
    fix_normals(bm)
    lm = L(bm)[0]
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.y) < 0.5 and arches and any(math.hypot(c.x - ax, c.z - az) < r + 0.01 for ax, az, r in arches) and f.normal.z < 0.2:
            f[lm] = MID[well]
    return bm


def glass_side(B, pts_xz, y, facing, mat='ktglassd'):
    """A dark glass panel on a vehicle's side (a polygon in x, z) just proud of the body at y."""
    mb = MB()
    mb.face([(x, y, z) for x, z in pts_xz], mat, (0, facing, 0))
    return B.add(mb.bm())


def kei_truck(B):
    """A white kei truck parked (nose to +X): the cab-over cab with its raked windscreen, the door windows, mirrors on
    stalks, the grille and square headlamps, the grey bumper and a blank yellow plate; the flat bed with its drop sides
    and tailgate (hinges, ribs, a little rust at the edges), the guard frame behind the cab; 12-inch wheels; no one in it."""
    Wd = 1.48
    rw, ry = 0.27, Wd / 2 - 0.1
    fx, rx = 1.0, -0.95
    # the cab
    cab = [(0.5, 0.4), (1.69, 0.4), (1.7, 1.02), (1.58, 1.64), (1.46, 1.8), (0.55, 1.8)]
    B.add(ybody(B, cab, Wd, 'ktkeiw', arches=((fx, 0.27, 0.34),)))
    for sgn in (-1, 1):
        y = sgn * (Wd / 2 + 0.003)
        glass_side(B, [(0.72, 1.12), (1.45, 1.12), (1.56, 1.62), (1.44, 1.72), (0.72, 1.72)][::(1 if sgn < 0 else -1)], y, sgn)
        glass_side(B, [(0.6, 1.12), (0.68, 1.12), (0.68, 1.72), (0.6, 1.72)][::(1 if sgn < 0 else -1)], y, sgn, 'ktkeiw')
        B.add(box((0.69, y - 0.002 if sgn < 0 else y - 0.001, 0.62), (0.7, y + 0.001 if sgn < 0 else y + 0.002, 1.75), 'ktbumper'))
        B.add(bx((1.1, y - 0.01, 1.0), (1.22, y + 0.01, 1.03), 'ktbumper'))
        B.add(tube([(1.58, sgn * 0.74, 1.25), (1.62, sgn * 0.86, 1.32)], 0.012, 'ktblk', 4))
        B.add(cbox2((1.56, sgn * 0.86 - 0.05, 1.26), (1.62, sgn * 0.86 + 0.05, 1.42), 0.015, 'ktblk'))
    # the windscreen, the grille, the lamps, the bumper and plate
    mb = MB()
    mb.face([(1.706, -0.66, 1.06), (1.706, 0.66, 1.06), (1.595, 0.62, 1.6), (1.595, -0.62, 1.6)], 'ktglassd', (1, 0, 0.2))
    B.add(mb.bm())
    for yy in (-0.55, 0.55):
        B.add(bx((1.69, yy - 0.11, 0.78), (1.715, yy + 0.11, 0.92), 'ktlight'))
        B.add(bx((1.69, yy + (0.12 if yy > 0 else -0.17), 0.8), (1.712, yy + (0.17 if yy > 0 else -0.12), 0.9), 'ktorange'))
    B.add(bx((1.69, -0.38, 0.8), (1.71, 0.38, 0.9), 'ktbumper'))
    B.add(cbox2((1.62, -0.76, 0.38), (1.77, 0.76, 0.58), 0.03, 'ktbumper'))
    xquad(B, -0.17, 0.17, 0.4, 0.56, 1.772, 'kt_plate')
    # the chassis and the bed
    B.add(bx((-1.62, -0.42, 0.42), (0.6, 0.42, 0.62), 'ktblk'))
    B.add(bx((-1.7, -Wd / 2, 0.62), (0.5, Wd / 2, 0.72), 'ktkeiw'))
    for sgn in (-1, 1):
        y = sgn * Wd / 2
        B.add(box((-1.7, min(y, y - sgn * 0.035), 0.72), (0.48, max(y, y - sgn * 0.035), 1.04), 'ktkeiw'))
        for z in (0.82, 0.94):
            B.add(box((-1.68, min(y, y + sgn * 0.006), z), (0.46, max(y, y + sgn * 0.006), z + 0.025), 'ktkeiw'))
        for x in (-1.2, -0.5, 0.2):
            B.add(box((x, min(y, y + sgn * 0.012), 0.66), (x + 0.07, max(y, y + sgn * 0.012), 0.74), 'ktbumper'))
            B.add(box((x - 0.04, min(y, y + sgn * 0.008), 0.73), (x + 0.11, max(y, y + sgn * 0.008), 0.77), 'ktrustp'))
        for (xa, xb) in ((-1.7, -1.52), (-0.9, -0.78), (0.3, 0.48)):
            B.add(box((xa, min(y, y + sgn * 0.007), 1.015), (xb, max(y, y + sgn * 0.007), 1.045), 'ktrustp'))
        # the rear wheel arch: the bed's skirt stops round the wheel
        B.add(box((rx - 0.36, min(y - sgn * 0.12, y), 0.55), (rx + 0.36, max(y - sgn * 0.12, y), 0.62), 'ktblk'))
    B.add(box((-1.73, -Wd / 2, 0.66), (-1.7, Wd / 2, 1.04), 'ktkeiw'))
    for z in (0.8, 0.92):
        B.add(box((-1.736, -Wd / 2 + 0.02, z), (-1.73, Wd / 2 - 0.02, z + 0.025), 'ktkeiw'))
    xquad(B, -0.55, -0.21, 0.5, 0.66, -1.731, 'kt_plate', facing=-1)
    for yy in (-0.62, 0.62):
        B.add(bx((-1.76, yy - 0.08, 0.46), (-1.7, yy + 0.08, 0.64), 'ktred'))
    # the guard frame behind the cab
    for yy in (-0.66, 0.66):
        B.add(cbox2((0.44, yy - 0.025, 0.72), (0.49, yy + 0.025, 1.76), 0.008, 'ktkeiw'))
    B.add(cbox2((0.44, -0.69, 1.7), (0.49, 0.69, 1.76), 0.008, 'ktkeiw'))
    for k in range(5):
        yy = -0.5 + 0.25 * k
        B.add(bx((0.45, yy - 0.012, 1.04), (0.48, yy + 0.012, 1.7), 'ktkeiw'))
    for x in (fx, rx):
        for yy in (-ry, ry):
            wheel(B, x, yy, rw, rw, 0.16, hub='ktgrey', n=12, hub_r=0.48)
    return 1.8


def kei_car(B):
    """A small boxy kei car (a tall wagon) in a soft mint, parked nose to +X: the short bonnet, the tall cabin with its
    windows all round, the sliding rear door's rail, square-ish lamps, vertical tail lamps, mirrors, door handles, grey
    bumpers, blank plates, 14-inch wheels; empty."""
    Wd = 1.48
    rw = 0.29
    fx, rx = 1.12, -1.13
    out = [(-1.68, 0.3), (1.66, 0.3), (1.72, 0.55), (1.7, 0.86), (1.38, 0.98), (0.88, 1.08), (0.42, 1.62), (0.3, 1.69),
           (-1.5, 1.7), (-1.66, 1.62), (-1.7, 1.2), (-1.72, 0.55)]
    B.add(ybody(B, out, Wd, 'ktkeic', arches=((fx, rw, 0.34), (rx, rw, 0.34))))
    for sgn in (-1, 1):
        y = sgn * (Wd / 2 + 0.003)
        rev = (1 if sgn < 0 else -1)
        glass_side(B, [(0.48, 1.12), (0.82, 1.12), (0.47, 1.53), (0.47, 1.53)][:3][::rev], y, sgn)
        glass_side(B, [(-0.36, 1.1), (0.4, 1.1), (0.4, 1.56), (-0.36, 1.56)][::rev], y, sgn)
        glass_side(B, [(-1.18, 1.1), (-0.44, 1.1), (-0.44, 1.56), (-1.18, 1.56)][::rev], y, sgn)
        glass_side(B, [(-1.6, 1.1), (-1.26, 1.1), (-1.26, 1.56), (-1.56, 1.56)][::rev], y, sgn)
        y2 = sgn * (Wd / 2 + 0.005)
        for x0 in (0.42, -0.42):
            B.add(box((x0 - 0.008, min(y2, y2 - sgn * 0.003), 0.36), (x0 + 0.008, max(y2, y2 - sgn * 0.003), 1.6), 'ktbumper'))
        B.add(box((-1.2, min(y2, y2 - sgn * 0.003), 1.03), (0.4, max(y2, y2 - sgn * 0.003), 1.05), 'ktbumper'))
        for x in (0.2, -0.6):
            B.add(bx((x, y2 - 0.01, 0.98), (x + 0.12, y2 + 0.01, 1.01), 'ktchrome'))
        B.add(tube([(0.62, sgn * 0.74, 1.12), (0.68, sgn * 0.85, 1.16)], 0.012, 'ktkeic', 4))
        B.add(cbox2((0.64, sgn * 0.86 - 0.05, 1.08), (0.7, sgn * 0.86 + 0.05, 1.22), 0.015, 'ktkeic'))
        B.add(box((-1.72, min(sgn * 0.6, sgn * 0.73), 0.9), (-1.7, max(sgn * 0.6, sgn * 0.73), 1.4), 'ktred'))
    # the windscreen, the back window, lamps, grille, bumpers, plates
    mb = MB()
    mb.face([(0.9, -0.66, 1.1), (0.9, 0.66, 1.1), (0.44, 0.64, 1.62), (0.44, -0.64, 1.62)], 'ktglassd', (1, 0, 0.8))
    mb.face([(-1.705, 0.6, 1.2), (-1.705, -0.6, 1.2), (-1.665, -0.58, 1.6), (-1.665, 0.58, 1.6)], 'ktglassd', (-1, 0, 0))
    B.add(mb.bm())
    for yy in (-0.52, 0.52):
        B.add(bx((1.68, yy - 0.15, 0.68), (1.712, yy + 0.15, 0.84), 'ktlight'))
    B.add(bx((1.7, -0.3, 0.6), (1.725, 0.3, 0.72), 'ktbumper'))
    B.add(cbox2((1.62, -0.75, 0.28), (1.77, 0.75, 0.5), 0.04, 'ktbumper'))
    B.add(cbox2((-1.78, -0.75, 0.28), (-1.66, 0.75, 0.52), 0.04, 'ktbumper'))
    xquad(B, -0.17, 0.17, 0.32, 0.48, 1.772, 'kt_plate')
    xquad(B, -0.17, 0.17, 0.62, 0.78, -1.721, 'kt_plate', facing=-1)
    for x in (fx, rx):
        for yy in (-0.62, 0.62):
            wheel(B, x, yy, rw, rw, 0.17, hub='ktgrey', n=12, hub_r=0.5)
    return 1.7


def scooter_km(B):
    """A small 50cc delivery moped on its centre stand (nose to +X): the step-through frame, the cream leg shield, the
    headlamp on the handlebar, the seat, the little engine and its exhaust, the rear carrier with a red delivery box
    (an invented soba shop's: 出前, そば 潮見庵), spoked wheels; the rear wheel just off the ground."""
    rw = 0.26
    fx, rx = 0.62, -0.58
    for x, z in ((fx, rw), (rx, rw + 0.02)):
        wheel(B, x, 0.0, z, rw, 0.07, n=14, hub_r=0.3, hub='ktchrome')
        ring = tube([(x + 0.18 * math.cos(a), 0.0, z + 0.18 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)], 0.012,
                    'ktchrome', 4, caps=False)
        B.add(ring)
    # forks, frame, leg shield, fenders
    B.add(tube([(fx, 0.06, rw), (fx - 0.12, 0.06, 0.82)], 0.018, 'ktchrome', 6))
    B.add(tube([(fx, -0.06, rw), (fx - 0.12, -0.06, 0.82)], 0.018, 'ktchrome', 6))
    B.add(tube([(fx + 0.1, 0.0, rw + 0.1), (fx + 0.02, 0.0, rw + 0.3), (fx - 0.16, 0.0, rw + 0.28)], 0.045, 'ktscoot', 6))
    B.add(tube([(fx - 0.12, 0.0, 0.8), (0.25, 0.0, 0.45), (-0.05, 0.0, 0.36), (-0.35, 0.0, 0.5), (-0.5, 0.0, 0.66)], 0.05, 'ktscoot', 8))
    shield = [(-0.2, 0.3), (0.2, 0.3), (0.24, 0.6), (0.17, 0.82), (-0.17, 0.82), (-0.24, 0.6)]
    bm = extrude_poly(shield, 0.03, 'ktscoot', back=True)
    xform(bm, T(fx - 0.2, 0.0, 0.0) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1))))
    B.add(fix_normals(bm))
    B.add(tube([(rx + 0.3 * math.cos(a), 0.0, rw + 0.02 + 0.3 * math.sin(a)) for a in np.linspace(0.3, 2.4, 7)], 0.05, 'ktscoot', 6))
    # handlebar, headlamp, mirrors
    B.add(tube([(fx - 0.14, -0.3, 0.98), (fx - 0.12, 0.0, 0.95), (fx - 0.14, 0.3, 0.98)], 0.014, 'ktchrome', 5))
    for yy in (-0.32, 0.32):
        B.add(tube([(fx - 0.14, yy, 0.98), (fx - 0.14, yy + (0.07 if yy > 0 else -0.07), 0.98)], 0.02, 'ktblk', 5))
        B.add(tube([(fx - 0.14, yy * 0.8, 0.98), (fx - 0.16, yy * 0.85, 1.18)], 0.006, 'ktchrome', 3))
        B.add(blob((fx - 0.16, yy * 0.85, 1.2), (0.02, 0.05, 0.035), 'ktchrome', 6, 2, 3, 0.0))
    B.add(cbox2((fx - 0.2, -0.11, 0.86), (fx + 0.0, 0.11, 0.98), 0.03, 'ktscoot'))
    lamp = disc_y(0.0, 0.0, 0.0, 0.07, 0.02, 'ktlight', 10, -1)
    B.add(xform(lamp, T(fx + 0.01, 0.0, 0.92) @ R(math.pi / 2, 'Z')))
    # engine, exhaust, seat, carrier and box, the stand
    B.add(cbox2((-0.15, -0.12, 0.2), (0.15, 0.12, 0.42), 0.04, 'ktgreyd'))
    B.add(tube([(0.1, 0.1, 0.24), (-0.1, 0.17, 0.2), (-0.55, 0.17, 0.3), (-0.75, 0.16, 0.36)], 0.03, 'ktchrome', 6))
    B.add(cbox2((-0.48, -0.13, 0.7), (0.0, 0.13, 0.8), 0.05, 'ktblk'))
    B.add(bx((-0.95, -0.2, 0.8), (-0.45, 0.2, 0.83), 'ktchrome'))
    for xx in (-0.92, -0.48):
        B.add(tube([(xx, 0.0, 0.8), (rx + (0.05 if xx > -0.6 else -0.1), 0.0, rw + 0.05)], 0.012, 'ktchrome', 4))
    B.add(cbox2((-0.97, -0.2, 0.83), (-0.47, 0.2, 1.23), 0.02, 'ktred'))
    yquad(B, -0.95, -0.49, 0.86, 1.2, -0.201, 'kt_demae')
    yquad(B, -0.95, -0.49, 0.86, 1.2, 0.201, 'kt_demae', facing=1)
    B.add(tube([(-0.3, -0.08, 0.36), (-0.32, -0.12, 0.0)], 0.012, 'ktblk', 4))
    B.add(tube([(-0.3, 0.08, 0.36), (-0.32, 0.12, 0.0)], 0.012, 'ktblk', 4))
    return 1.23


def rickshaw(B):
    """A jinrikisha parked with its shafts resting on the ground: two tall wheels (black rims and spokes, rubber tyres), the
    black-lacquered body tipped forward on them, a red seat and red blanket, the black hood folded half up on its bows, the
    footboard, the long shafts with their cross bar; empty, waiting."""
    R_, ax = 0.55, -0.5
    for yy in (-0.6, 0.6):
        rim = tube([(ax + R_ * math.cos(a), yy, R_ + R_ * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)], 0.03, 'ktrubber', 4,
                   caps=False)
        B.add(rim)
        B.add(tube([(ax + (R_ - 0.04) * math.cos(a), yy, R_ + (R_ - 0.04) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)], 0.018,
                   'ktlacq', 3, caps=False))
        for k in range(12):
            a = 2 * math.pi * k / 12
            B.add(tube([(ax, yy, R_), (ax + (R_ - 0.05) * math.cos(a), yy, R_ + (R_ - 0.05) * math.sin(a))], 0.008, 'ktlacq', 3, caps=False))
        hub, _ = lathe([(0.0, -0.06), (0.06, -0.06), (0.07, 0.0), (0.06, 0.06), (0.0, 0.06)], 8, 'ktgold')
        B.add(xform(hub, T(ax, yy, R_) @ R(math.pi / 2, 'X')))
    B.add(tube([(ax, -0.6, R_), (ax, 0.6, R_)], 0.02, 'ktlacq', 5))
    # the body, built level about the axle, then tipped forward until the shafts' ends rest on the ground
    parts = []
    parts.append(cbox2((-0.45, -0.38, 0.62), (0.15, 0.38, 0.78), 0.03, 'ktlacq'))                  # the seat box
    parts.append(cbox2((-0.42, -0.36, 0.78), (0.12, 0.36, 0.86), 0.04, 'ktseatred'))               # the cushion
    parts.append(cbox2((-0.52, -0.38, 0.62), (-0.42, 0.38, 1.25), 0.03, 'ktlacq'))                 # the back
    parts.append(cbox2((-0.49, -0.34, 0.85), (-0.42, 0.34, 1.2), 0.03, 'ktseatred'))
    parts.append(box((0.1, -0.37, 0.5), (0.13, 0.37, 0.78), 'ktseatred'))                          # the blanket over the front
    for yy in (-0.4, 0.4):
        parts.append(cbox2((-0.5, yy - 0.025, 0.86), (0.12, yy + 0.025, 0.98), 0.01, 'ktlacq'))     # the arm rests
    parts.append(cbox2((0.15, -0.3, 0.32), (0.55, 0.3, 0.37), 0.01, 'ktlacq'))                    # the footboard
    for yy in (-0.28, 0.28):
        parts.append(tube([(0.12, yy, 0.62), (0.2, yy, 0.36)], 0.02, 'ktlacq', 4))
    for yy in (-0.36, 0.36):
        parts.append(tube([(-0.55, yy, 0.6), (0.3, yy, 0.6), (2.05, yy * 0.9, 0.6)], 0.028, 'ktlacq', 6))
    parts.append(tube([(1.98, -0.33, 0.6), (1.98, 0.33, 0.6)], 0.022, 'ktlacq', 5))
    # the hood: four bows fanned back from the seat's back, fabric between them
    piv = Vector((-0.45, 0.0, 0.95))
    angs = [math.radians(a) for a in (100, 128, 150, 168)]
    rows = []
    for a in angs:
        pts = []
        for i in range(9):
            t_ = math.pi * i / 8
            y = -0.42 * math.cos(t_)
            r = 0.55 * math.sin(t_) + 0.05
            pts.append(piv + Vector((r * math.cos(a), y, r * math.sin(a) * 0.9 + 0.0)))
        rows.append(pts)
        parts.append(tube(pts, 0.012, 'ktlacq', 4, caps=False))
    mb = MB()
    for ra, rb in zip(rows[:-1], rows[1:]):
        for i in range(8):
            q = [ra[i], ra[i + 1], rb[i + 1], rb[i]]
            mb.face(q, 'kthood', None)
            mb.face(q[::-1], 'kthood', None)
    parts.append(mb.bm())
    # tip it forward about the axle so the shafts' ends touch the ground
    tip = Vector((2.05 - ax, 0.0, 0.6 - R_))
    want = 0.04 - R_
    lo, hi = 0.0, 0.6
    for _ in range(40):
        mid = (lo + hi) / 2
        zt = tip.x * math.sin(-mid) + tip.z * math.cos(mid)
        if zt > want: lo = mid
        else: hi = mid
    pitch = (lo + hi) / 2
    M = T(ax, 0, R_) @ R(pitch, 'Y') @ T(-ax, 0, -R_)
    for p in parts:
        B.add(xform(p, M))
    return 1.5


# ================================================================ the kit's rows
def _row(name, W, H, D, fn, col, mtop, ppm):
    """A row centred on its footprint: the side maps cover -D/2 .. D/2."""
    return (name, W, H, D, 0.0, fn, col, mtop, {'ppm': ppm},
            {'right': (-D / 2 - 0.7, D / 2 + 0.7, 0.0, mtop), 'left': (-D / 2 - 0.7, D / 2 + 0.7, 0.0, mtop)})


def pal_kamst(pal):
    """The kit's SPECS rows (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps)."""
    stone = pal((0.66, 0.65, 0.61), (0.40, 0.42, 0.46), (0.36, 0.38, 0.42))
    rows = [
        _row('ToriiKM', 4.6, 4.4, 0.8, torii, pal((0.84, 0.25, 0.13), (0.10, 0.10, 0.10), (0.66, 0.65, 0.61)), 4.5, 40),
        _row('TempleGateKM', 6.5, 6.1, 4.1, temple_gate, pal((0.62, 0.60, 0.56), (0.30, 0.25, 0.21), (0.36, 0.38, 0.42)), 6.2, 40),
        _row('StoneLanternKM', 1.1, 2.05, 1.1, stone_lantern, stone, 2.1, 24),
        _row('StoneStepsKM', 3.6, 1.45, 2.4, stone_steps, stone, 1.5, 24),
        _row('MossWallKM', 4.0, 1.45, 0.6, moss_wall, stone, 1.5, 24),
        _row('EmaRackKM', 2.1, 2.2, 0.9, ema_rack, pal((0.62, 0.60, 0.56), (0.86, 0.72, 0.5), (0.36, 0.38, 0.42)), 2.3, 24),
        _row('ShrineHallKM', 8.0, 7.0, 7.0, shrine_hall, pal((0.46, 0.33, 0.24), (0.90, 0.88, 0.82), (0.40, 0.62, 0.54)), 7.1, 32),
        _row('ConvexMirrorKM', 0.8, 3.15, 0.8, convex_mirror, pal((0.94, 0.46, 0.13), (0.70, 0.69, 0.66), (0.56, 0.55, 0.54)), 3.2, 24),
        _row('PhoneBoothKM', 0.9, 2.23, 0.9, phone_booth, pal((0.24, 0.56, 0.36), (0.66, 0.68, 0.70), (0.56, 0.55, 0.54)), 2.3, 24),
        _row('BusStopPoleKM', 1.9, 2.46, 0.6, bus_stop_pole, pal((0.70, 0.72, 0.72), (0.12, 0.30, 0.52), (0.56, 0.55, 0.54)), 2.5, 24),
        _row('VendingKM', 1.5, 1.83, 0.8, vending1, pal((0.10, 0.52, 0.56), (0.95, 0.92, 0.84), (0.20, 0.36, 0.62)), 1.9, 24),
        _row('VendingKM2', 1.0, 1.83, 0.8, vending2, pal((0.60, 0.50, 0.78), (0.95, 0.92, 0.84), (0.56, 0.55, 0.54)), 1.9, 24),
        _row('TactileStripKM', 1.2, 0.01, 0.3, tactile_strip, pal((0.98, 0.78, 0.10), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 0.1, 24),
        _row('ManholeKM', 0.74, 0.006, 0.74, manhole, pal((0.30, 0.30, 0.31), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 0.1, 24),
        _row('PotShelfKM', 1.6, 1.2, 0.9, pot_shelf, pal((0.62, 0.60, 0.56), (0.20, 0.34, 0.20), (0.56, 0.55, 0.54)), 1.3, 24),
        _row('LaundryPoleKM', 2.6, 1.9, 0.6, laundry_pole, pal((0.70, 0.72, 0.72), (0.30, 0.62, 0.80), (0.56, 0.55, 0.54)), 2.0, 24),
        _row('CorrugatedShedKM', 2.4, 2.1, 1.6, corrugated_shed, pal((0.62, 0.64, 0.64), (0.50, 0.28, 0.16), (0.56, 0.55, 0.54)), 2.2, 24),
        _row('TramKM', 25.0, 4.9, 2.6, tram, pal((0.94, 0.90, 0.77), (0.13, 0.36, 0.25), (0.47, 0.48, 0.48)), 5.0, 40),
        _row('TramPoleKM', 0.6, 7.02, 4.2, tram_pole, pal((0.70, 0.69, 0.66), (0.70, 0.72, 0.72), (0.56, 0.55, 0.54)), 7.1, 24),
        _row('CrossingSignalKM', 1.3, 3.83, 0.7, crossing_signal, pal((0.98, 0.78, 0.10), (0.07, 0.07, 0.07), (0.55, 0.06, 0.05)), 3.9, 24),
        _row('CrossingBarKM', 0.8, 1.26, 8.4, crossing_bar, pal((0.98, 0.78, 0.10), (0.07, 0.07, 0.07), (0.58, 0.60, 0.62)), 1.3, 24),
        _row('TrackKM', 4.0, 0.32, 3.5, track, pal((0.52, 0.45, 0.40), (0.70, 0.69, 0.66), (0.56, 0.55, 0.54)), 0.4, 24),
        _row('KeiTruckKM', 3.5, 1.8, 1.6, kei_truck, pal((0.92, 0.92, 0.90), (0.30, 0.31, 0.32), (0.56, 0.55, 0.54)), 1.9, 24),
        _row('KeiCarKM', 3.5, 1.7, 1.6, kei_car, pal((0.74, 0.84, 0.80), (0.30, 0.31, 0.32), (0.56, 0.55, 0.54)), 1.8, 24),
        _row('ScooterKM', 1.9, 1.23, 0.7, scooter_km, pal((0.86, 0.84, 0.76), (0.72, 0.14, 0.12), (0.56, 0.55, 0.54)), 1.3, 24),
        _row('RickshawKM', 2.7, 1.5, 1.4, rickshaw, pal((0.10, 0.09, 0.09), (0.70, 0.12, 0.12), (0.12, 0.12, 0.13)), 1.6, 24),
    ]
    return rows
