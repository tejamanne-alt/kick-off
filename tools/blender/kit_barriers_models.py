# The models of the BARRIERS kit (kit_barriers.py): real things a kid ducks under on the way to
# school, each spanning the footpath with a clear 0.85 m gap over the kid's line, so the game's
# slide (TrackBuilder.SlideUnder) passes under and the ball rolls under too.
#
# Space as in every kit: metres, Z up, fronts face -Y (the game camera); game x is Blender X, game z
# (depth) is Blender +Y, game y (up) is Blender Z. The kid runs along y = 0. Every model's origin is
# on the ground at the middle of its solid span along x, on the kid's line, and the manifest records
# the solid the game builds a collider for: slideHalf (half its length along x), slideTop (the top of
# the solid), or slideRadius and slideCentre for a round one. Under GAP nothing stands nearer the
# kid's line than LANE (legs, posts and props stand either side of it), so a sliding kid never
# passes through anything.
#
# Families: the home street (painters' boards on trestles, a car-park barrier arm, a hedge
# trimmer's work platform, an apple tree's propped bough), the market (a stall under its awning,
# a half-raised roll shutter, a delivery roller conveyor), the beach (a surf school's board rack, a
# rowing boat upturned on trestles for painting, a boardwalk crossing, a lifeguard's rescue-board
# stand), the building site (a sheeted scaffold, steel beams on trestles, a pipe rack, a manual
# site barrier) and the park (a fallen trunk, an old oak's propped bough, a rope-net tunnel, a play
# tower).
import math
import numpy as np
from mathutils import Vector, Matrix
import kit_works_geo as G
import kit_works_atlas as ATL
from kit_works_geo import *
from kit_works_site import wood_box, section_beam, wheel_bm
import kit_plants_geo as PG
import kit_plants_leaves as LV

GAP = 0.85          # clear height over the kid's line: TrackBuilder.SlideGap in the game
LANE = 0.5          # under GAP nothing stands nearer the kid's line (|y|) than this


# ---------------------------------------------------------------- extra materials and tiles
def _mat(name, part, colour, uv, grad=0.0):
    if name in MAT: return
    MAT[name] = (part, colour, uv, grad)
    MID[name] = len(MATS)
    MATS.append(name)


for _n, _s in {
    'oakbark': (0, (0.50, 0.41, 0.34), 'keep', 0.0), 'applebark': (0, (0.60, 0.54, 0.47), 'keep', 0.0),
    'woodend': (0, (0.88, 0.75, 0.55), 'white', 0.0),
    'rock': (0, (0.66, 0.64, 0.60), 'grime', 0.3), 'rockd': (0, (0.55, 0.53, 0.50), 'grime', 0.25),
    'moss': (0, (0.47, 0.60, 0.30), 'white', 0.25), 'grass': (0, (0.50, 0.66, 0.34), 'white', 0.4),
    'apple': (0, (0.84, 0.24, 0.17), 'white', 0.15), 'orangef': (0, (0.98, 0.60, 0.16), 'white', 0.12),
    'lemon': (0, (0.98, 0.86, 0.32), 'white', 0.12), 'limef': (0, (0.52, 0.74, 0.28), 'white', 0.12),
    'tomato': (0, (0.88, 0.24, 0.16), 'white', 0.12), 'banana': (0, (0.98, 0.84, 0.36), 'white', 0.1),
    'card': (0, (0.80, 0.64, 0.44), 'grime', 0.0), 'tape': (0, (0.88, 0.80, 0.62), 'white', 0.0),
    'alu': (0, (0.80, 0.82, 0.84), 'grime', 0.0), 'aluw': (0, (0.82, 0.84, 0.86), 'white', 0.0),
    'ply': (0, (0.84, 0.72, 0.54), 'grime', 0.0), 'foam': (0, (0.24, 0.26, 0.31), 'white', 0.0),
    'coral': (0, (0.98, 0.50, 0.42), 'white', 0.0), 'teal': (0, (0.30, 0.74, 0.76), 'white', 0.0),
    'sun': (0, (0.99, 0.82, 0.30), 'white', 0.0), 'sky': (0, (0.46, 0.64, 0.94), 'white', 0.0),
    'limeg': (0, (0.62, 0.84, 0.38), 'white', 0.0), 'rescue': (0, (0.99, 0.79, 0.15), 'grime', 0.0),
    'rescuer': (0, (0.86, 0.20, 0.17), 'grime', 0.0), 'navy': (0, (0.22, 0.29, 0.46), 'grime', 0.0),
    'stucco': (0, (0.91, 0.88, 0.81), 'grime', 0.12), 'stone': (0, (0.74, 0.72, 0.68), 'grime', 0.2),
    'sheet': (0, (0.84, 0.90, 0.94), 'grime', 0.0), 'sheetd': (0, (0.70, 0.78, 0.84), 'grime', 0.0),
    'netg': (0, (0.30, 0.46, 0.38), 'grime', 0.0), 'bark': (0, (0.45, 0.36, 0.28), 'grime', 0.2),
    'barkchip': (0, (0.55, 0.40, 0.28), 'grime', 0.0), 'sandw': (0, (0.90, 0.80, 0.62), 'white', 0.1),
    'pipeo': (0, (0.92, 0.50, 0.20), 'grime', 0.0), 'pipeb': (0, (0.20, 0.21, 0.23), 'grime', 0.0),
    'pipeg': (0, (0.56, 0.58, 0.60), 'grime', 0.0), 'canvas': (0, (0.96, 0.93, 0.85), 'grime', 0.0),
    'leafap': (0, (0.42, 0.60, 0.30), 'white', 0.35), 'leafapl': (0, (0.58, 0.74, 0.36), 'white', 0.3),
    'leafoak': (0, (0.34, 0.50, 0.26), 'white', 0.35), 'leafoakl': (0, (0.48, 0.64, 0.30), 'white', 0.3),
    'ivy': (0, (0.24, 0.40, 0.24), 'white', 0.3), 'matg': (0, (0.38, 0.56, 0.42), 'grime', 0.0),
}.items():
    _mat(_n, *_s)

# Leaf-card foliage (kit_plants_leaves.py, as the Plants kit's trees): shading ramps (sRGB: deep
# shade, base, sunlit) for the boughs' crowns, built into cut-out cards once the atlas is laid out.
R_APPLE = PG.Ramp('#26452c', '#6b994d', '#cfe27a')
R_OAK = PG.Ramp('#1c3929', '#577f42', '#b8d36c')
R_IVY = PG.Ramp('#122a1e', '#3d6640', '#8fb062')


def t_bark(w, h):
    """Bark as a multiplier: long plates split by dark furrows that wander along the limb (t runs
    along it, s around), a little cross-cracking, and pale lichen flecks."""
    U, V = ATL._grid(w, h)
    n = ATL._noise(h, w, (5, 4), 31)
    s = U * 14 + 0.35 * np.sin(V * 2 * np.pi * 2 + U * 5) + 0.6 * (n - 0.5)
    k = s % 1.0
    img = np.ones((h, w, 3), np.float32) * (0.97 - 0.1 * ATL._noise(h, w, (24, 12), 32))[..., None]
    img = ATL._mul(img, ATL._ss(0.16, 0.0, np.minimum(k, 1 - k)), (0.42, 0.37, 0.33), 0.95)
    cross = (V * 9 + np.floor(s) * 0.37) % 1.0
    img = ATL._mul(img, ATL._ss(0.05, 0.0, np.minimum(cross, 1 - cross)) * ATL._ss(0.4, 0.7, n), (0.6, 0.55, 0.5), 0.8)
    lichen = ATL._ss(0.68, 0.8, ATL._noise(h, w, (14, 7), 33))
    img = ATL._blend(img, lichen, (0.86, 0.9, 0.78), 0.45)
    return np.clip(img, 0, 1)


def t_rings(w, h):
    """A sawn log end (absolute colours): growth rings, a darker heart, two radial checks, a bark rim."""
    U, V = ATL._grid(w, h)
    x, y = U * 2 - 1, V * 2 - 1
    r = np.sqrt(x * x + y * y)
    rw = r + 0.025 * (ATL._noise(h, w, (6, 6), 41) - 0.5)
    img = ATL._const(w, h, (0.88, 0.75, 0.55))
    img = ATL._mul(img, (0.5 + 0.5 * np.cos(rw * 2 * np.pi * 10)) * 0.7, (0.80, 0.64, 0.45), 1.0)
    img = ATL._blend(img, ATL._ss(0.32, 0.18, rw), (0.74, 0.56, 0.37), 0.75)
    a = np.arctan2(y, x)
    for a0, ln in ((0.6, 0.55), (2.9, 0.4)):
        da = np.abs(np.angle(np.exp(1j * (a - a0))))
        img = ATL._mul(img, ATL._ss(0.05, 0.0, da * r) * ATL._ss(ln, ln - 0.1, r) * ATL._ss(0.05, 0.12, r), (0.45, 0.35, 0.27), 1.0)
    img = ATL._blend(img, ATL._ss(0.84, 0.92, rw), (0.42, 0.34, 0.27), 1.0)
    return np.clip(img, 0, 1)


def t_slats(w, h):
    """Roll-shutter slats (multiplier): a curved lath every 1/16 of the tile, lit at the top."""
    U, V = ATL._grid(w, h)
    k = (V * 16) % 1.0
    img = np.ones((h, w, 3), np.float32) * (0.78 + 0.22 * np.clip(np.sin(k * np.pi) ** 0.6, 0, 1))[..., None]
    img = ATL._mul(img, ATL._ss(0.08, 0.0, k), (0.55, 0.55, 0.57), 1.0)
    img = ATL._mul(img, ATL._ss(0.5, 0.9, ATL._noise(h, w, (12, 30), 51)), (0.85, 0.82, 0.78), 0.4)
    return np.clip(img, 0, 1)


def t_mesh(w, h):
    """Debris netting (multiplier): a fine diamond weave with bands where the sheets overlap."""
    U, V = ATL._grid(w, h)
    a = (U * 24 + V * 24) % 1.0; b = (U * 24 - V * 24) % 1.0
    m = np.maximum(ATL._ss(0.12, 0.0, np.minimum(a, 1 - a)), ATL._ss(0.12, 0.0, np.minimum(b, 1 - b)))
    img = np.ones((h, w, 3), np.float32) * 0.94
    img = ATL._mul(img, m, (0.82, 0.85, 0.88), 0.8)
    img = ATL._mul(img, ATL._ss(0.03, 0.0, np.abs(V - 0.5)), (0.75, 0.78, 0.8), 0.8)
    return np.clip(img, 0, 1)


ATL.TILE_SPECS.update({'bark': (128, 256, t_bark), 'rings': (128, 128, t_rings), 'slats': (128, 256, t_slats),
                       'mesh': (128, 128, t_mesh)})


# ---------------------------------------------------------------- helpers
def blob(center, radii, mat, n=7, rings=3, seed=0, **kw):
    """G.blob with any seed (positions make handy seeds, and they can be negative)."""
    return G.blob(center, radii, mat, n=n, rings=rings, seed=abs(int(seed)) % (2 ** 31), **kw)


def _front(M):
    M.attach.append(('Front', (0.0, -1.0, 0.0)))


def _slide(M, half, top, **kw):
    """What the game builds its collider from (see TrackBuilder.SlideUnder)."""
    M.extra.update({'slideGap': GAP, 'slideHalf': round(half, 3), 'slideTop': round(top, 3)})
    M.extra.update(kw)


def paint_by(bm, fn):
    """Set each face's material from fn(centre, normal) -> name (or None to keep it)."""
    bm.normal_update()
    lm = L(bm)[0]
    for f in bm.faces:
        m = fn(f.calc_center_median(), f.normal)
        if m: f[lm] = MID[m]
    return bm


def limb(path, r0, r1, mat, sides=8, tile=('bark', 1.0), caps=True):
    """A tapering round limb along a polyline (trunks, boughs, props), bark tiled along it."""
    sec = [(math.cos(2 * PI * (k + 0.5) / sides), math.sin(2 * PI * (k + 0.5) / sides)) for k in range(sides)]
    n = len(path)
    scales = [r0 + (r1 - r0) * (i / (n - 1)) ** 0.8 for i in range(n)]
    return sweep(path, sec, mat, scales=scales, caps=caps, sm=1, uvtile=tile)


def curve(pts, n):
    """A smooth polyline through control points (Catmull-Rom), n points."""
    P = [Vector(p) for p in pts]
    out = []
    segs = len(P) - 1
    for i in range(n):
        u = i / (n - 1) * segs
        k = min(int(u), segs - 1); t = u - k
        p0 = P[max(k - 1, 0)]; p1 = P[k]; p2 = P[k + 1]; p3 = P[min(k + 2, segs)]
        t2, t3 = t * t, t * t * t
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return out


def ring_end(bm, axis, centre, r):
    """Map the 'rings' tile onto the faces of a log end facing along axis (unit vector)."""
    axis = Vector(axis); c = Vector(centre)
    u = axis.orthogonal().normalized(); v = axis.cross(u)
    faces = faces_facing(bm, axis, 0.9)
    return settile(bm, 'rings', lambda co, f: (0.5 + (co - c).dot(u) / (2 * r), 0.5 + (co - c).dot(v) / (2 * r)), faces=faces, mat='tex')


def trestle(M, x, ylegs, ztop, splay=0.22, barh=0.065, legw=0.045, mat='timber', steel=False, band=1):
    """A folding A-frame trestle standing across the path at x: a top bar along y whose underside is
    at ztop - bar, on two pairs of legs splayed along x at y = +-ylegs (either side of the kid's
    line), each pair with a stay low down along the path and a hinge plate at the top."""
    zb = ztop - barh
    if steel:
        M.add(cbox((x - 0.045, -ylegs - 0.09, zb), (x + 0.045, ylegs + 0.09, ztop), 0.008, mat))
    else:
        M.add(wood_box((x - 0.045, -ylegs - 0.09, zb), (x + 0.045, ylegs + 0.09, ztop), band=band, along=1))
    for y in (-ylegs, ylegs):
        for s in (-1, 1):
            M.add(bar((x + s * 0.03, y, zb + barh * 0.4), (x + s * splay, y, 0.0), legw, mat))
            M.add(cbox((x + s * splay - 0.04, y - 0.035, 0.0), (x + s * splay + 0.04, y + 0.035, 0.018), 0.005, 'rubber' if steel else 'timber'))
        M.add(bar((x - splay * 0.72, y, 0.27), (x + splay * 0.72, y, 0.27), legw * 0.6, mat))
        M.add(cbox((x - 0.06, y - 0.03, zb - 0.07), (x + 0.06, y + 0.03, zb + 0.01), 0.006, 'iron'))


def leaves(M, centre, radii, mats, count, seed, size=(0.16, 0.26), flat=0.75, fine=False):
    """A crown or a spray of soft leaf clumps scattered through an ellipsoid (the outer ones
    lighter, where the sun catches them). Returns the clumps as (centre, size)."""
    rng = np.random.default_rng(seed)
    c = Vector(centre)
    out = []
    for i in range(count):
        while True:
            p = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if p.length <= 1: break
        s = rng.uniform(*size)
        q = c + Vector((p.x * radii[0], p.y * radii[1], p.z * radii[2]))
        m = mats[i % len(mats)]
        if len(mats) > 1 and p.length > 0.75 and p.z > -0.2: m = mats[1]
        M.add(blob(q, (s * 1.1, s, s * flat), m, n=9 if fine else 7, rings=3 if fine else 2, seed=seed * 31 + i, jitter=0.2))
        out.append((q, s))
    return out


def disc_sign(M, centre, normal_y, r, face, rim='white', thick=0.02):
    """A round sign plate facing -Y (or +Y): a face disc in a white rim."""
    d = cyl(r, 0, thick, 18, rim, bevel=0.004)
    xform(d, T(centre) @ R(PI / 2 * normal_y, 'X'))
    M.add(d)
    f = cyl(r * 0.84, 0, thick + 0.004, 18, face)
    xform(f, T(centre) @ R(PI / 2 * normal_y, 'X'))
    M.add(f)


# ================================================================ HOME STREET
def plank_trestles():
    """Painters at work on a house front: three scaffold boards laid on two folding trestles that
    straddle the footpath, paint tins (one open, a brush across it), a roller in its tray and a dust
    sheet folded on the boards, hanging down behind. Solid: the boards (hop on, or slide under)."""
    M = Model('PlankTrestles', p1=(0.55, 0.72, 0.90), ppm=110, grime=dict(rust=0.05, chips=0.25, streaks=0.3, dirt_h=0.3))
    hx = 1.3
    for x in (-0.95, 0.95):
        trestle(M, x, 0.7, GAP + 0.065)
    zb = GAP + 0.065
    for k, y in enumerate((-0.235, 0.0, 0.235)):
        M.add(wood_box((-hx, y - 0.112, zb), (hx, y + 0.112, zb + 0.038), band=k, along=0))
        for ex in (-hx + 0.04, hx - 0.04):
            M.add(cbox((ex - 0.02, y - 0.115, zb - 0.004), (ex + 0.02, y + 0.115, zb + 0.042), 0.004, 'galv'))
    deck = zb + 0.038
    # paint tins: the open one shows the colour (part 1), the other's lid is on
    for i, (x, y) in enumerate(((-0.62, -0.13), (-0.36, 0.12))):
        t = cyl(0.085, 0, 0.17, 14, 'galv', bevel=0.006)
        xform(t, T(x, y, deck)); M.add(t)
        M.add(xform(cyl(0.088, 0.17, 0.182, 14, 'p1w' if i == 0 else 'galv'), T(x, y, deck)))
        M.add(xform(tube([(0.0, -0.088, 0.17), (0.0, 0.0, 0.26), (0.0, 0.088, 0.17)], 0.004, 'iron', sides=4), T(x, y, deck)))
        M.add(xform(cbox((-0.02, -0.09, 0.05), (0.02, -0.084, 0.12), 0.003, 'p1w'), T(x, y, deck)))   # a drip down the side
    M.add(bar((-0.78, -0.13, deck + 0.19), (-0.48, -0.1, deck + 0.2), 0.024, 'timber'))
    M.add(cbox((-0.48, -0.125, deck + 0.17), (-0.43, -0.075, deck + 0.215), 0.006, 'dark'))
    # roller in its tray
    tr = tray((0.16, 0.13, 0.02), (0.19, 0.16, 0.03), 0.0, 0.05, 0.006, 'dark', inner_mat='p1w', nc=2, fill=0.015)
    xform(tr, T(0.62, 0.05, deck)); M.add(tr)
    M.add(xform(cyl(0.035, -0.11, 0.11, 12, 'p1w', bevel=0.006), T(0.72, 0.05, deck + 0.075) @ R(PI / 2, 'X')))
    M.add(tube([(0.72, 0.05, deck + 0.075), (0.72, 0.15, deck + 0.075), (0.78, 0.16, deck + 0.1), (1.02, 0.16, deck + 0.17)], 0.008, 'chrome', sides=5))
    M.add(tube([(0.98, 0.16, deck + 0.16), (1.12, 0.16, deck + 0.2)], 0.018, 'red', sides=8))
    # dust sheet folded on the boards, hanging down behind the kid's line
    M.add(cbox((0.05, 0.06, deck), (0.85, 0.42, deck + 0.03), 0.012, 'canvas'))
    drop = [(0.05, 0.0), (0.85, 0.0)] + [(0.85 - 0.8 * i / 8, -0.3 - 0.04 * math.sin(i * 1.7)) for i in range(9)]
    d = extrude_poly(drop, 0.012, 'canvas')
    xform(d, T(0.0, 0.43, deck + 0.02) @ R(PI / 2, 'X'))
    M.add(fix_normals(d))
    M.feat('top', 'spatter', a0=-hx, a1=hx, b0=-0.35, b1=0.35, n=260, r=(0.003, 0.012), col=(0.93, 0.93, 0.9), alpha=0.7)
    M.feat('front', 'spatter', a0=-1.2, a1=1.2, b0=0.0, b1=1.0, n=120, r=(0.003, 0.01), col=(0.93, 0.93, 0.9), alpha=0.6)
    _front(M)
    _slide(M, hx, deck)
    return M


def boom_barrier():
    """A car-park rising-arm barrier across the footpath: a cabinet at the back of the path, the
    striped aluminium arm across the path (its underside at the gap) resting in a forked post at the
    kerb, a counterweight behind. The arm is the solid: duck under it (or hop it)."""
    M = Model('BoomBarrier', p1=(0.98, 0.78, 0.22), ppm=120, grime=dict(rust=0.08, chips=0.25, streaks=0.4, dirt_h=0.35))
    hx = 0.04
    yc = 1.15
    M.add(cbox((-0.48, yc - 0.24, 0.0), (0.04, yc + 0.24, 0.08), 0.02, 'conc'))
    M.add(rbox((-0.42, yc - 0.17, 0.08), (-0.06, yc + 0.17, 1.02), (0.03, 0.03, 0.03), 'p1', seg=(1, 1, 1)))
    M.add(rbox((-0.44, yc - 0.19, 1.0), (-0.04, yc + 0.19, 1.08), (0.03, 0.03, 0.03), 'p1d', seg=(1, 1, 1)))
    M.add(cbox((-0.36, yc - 0.176, 0.25), (-0.12, yc - 0.168, 0.8), 0.006, 'p1d'))          # door
    M.add(cbox((-0.16, yc - 0.18, 0.5), (-0.14, yc - 0.172, 0.56), 0.003, 'dark'))           # lock
    M.add(xform(cyl(0.035, 0, 0.03, 10, 'red'), T(-0.24, yc, 1.08)))                     # lamp
    M.add(xform(cyl(0.028, 0, 0.05, 10, 'lamp'), T(-0.24, yc, 1.1)))
    # hub on the cabinet's side and the arm across the path
    M.add(xform(cyl(0.075, 0, 0.06, 14, 'galv', bevel=0.01), T(-0.06, yc - 0.02, GAP + 0.05) @ R(PI / 2, 'Y')))
    y_tip, y_back = -1.62, yc + 0.35
    n = 7
    for i in range(n):
        y0 = yc - (yc - y_tip) * i / n; y1 = yc - (yc - y_tip) * (i + 1) / n
        M.add(rbox((-hx, y1, GAP), (hx, y0, GAP + 0.1), (0.012, 0.0, 0.03), 'red' if i % 2 else 'white', seg=(1, 1, 1),
                   skip=((1, -1), (1, 1)) if 0 < i < n - 1 else ((1, 1),) if i == n - 1 else ((1, -1),)))
    M.add(rbox((-hx - 0.002, y_tip - 0.03, GAP - 0.002), (hx + 0.002, y_tip + 0.01, GAP + 0.102), (0.012, 0.012, 0.03), 'rubber', seg=(1, 1, 1)))
    for y in (-1.0, 0.0, 1.0):
        M.add(cbox((-hx - 0.004, y - 0.03, GAP + 0.035), (-hx, y + 0.03, GAP + 0.065), 0.002, 'red'))      # reflectors
    # short arm and counterweight behind
    M.add(cbox((-hx, yc, GAP + 0.02), (hx, y_back, GAP + 0.08), 0.01, 'galv'))
    M.add(cbox((-0.07, y_back - 0.16, GAP - 0.05), (0.07, y_back, GAP + 0.15), 0.02, 'iron'))
    # forked rest post at the kerb
    yr = -1.45
    M.add(cbox((-0.1, yr - 0.1, 0.0), (0.1, yr + 0.1, 0.04), 0.01, 'conc'))
    M.add(cbox((-0.04, yr - 0.04, 0.04), (0.04, yr + 0.04, GAP - 0.04), 0.008, 'p1'))
    M.add(cbox((-0.075, yr - 0.03, GAP - 0.05), (0.075, yr + 0.03, GAP - 0.01), 0.006, 'p1d'))
    for s in (-1, 1):
        M.add(cbox((s * 0.052 - 0.012, yr - 0.03, GAP - 0.03), (s * 0.052 + 0.012, yr + 0.03, GAP + 0.09), 0.004, 'p1d'))
    for z in (0.2, 0.5):
        M.add(cbox((-0.042, yr - 0.042, z), (0.042, yr + 0.042, z + 0.05), 0.004, 'white'))
    _front(M)
    _slide(M, 0.06, GAP + 0.1)
    return M


def access_platform():
    """A gardener's low work platform on castors, parked across the footpath to trim the hedge
    behind: an aluminium deck at the gap with guard rails round it, hedge clippings, a trimmer and
    a trug on the boards. Its ends stay open below the deck, so a kid slides through between the
    wheels. No room to stand on the deck under the rails: the whole of it is solid."""
    M = Model('AccessPlatform', p1=(0.98, 0.62, 0.18), p2=(0.32, 0.52, 0.80), ppm=100, grime=dict(rust=0.0, chips=0.2, streaks=0.3, dirt_h=0.3))
    hx, hy = 0.9, 0.62
    top = 1.98
    for x in (-hx, hx):
        for y in (-hy, hy):
            M.add(tube([(x, y, 0.17), (x, y, top)], 0.026, 'alu', sides=8))
            M.add(cbox((x - 0.04, y - 0.04, 0.15), (x + 0.04, y + 0.04, 0.18), 0.006, 'iron'))
            w = wheel_bm(0.065, 0.04, n=12, hub='iron', tyre='rubber', rim_r=0.55)
            xform(w, T(x, y, 0.065) @ R(PI / 2, 'X')); M.add(w)
            M.add(cbox((x - 0.03, y - 0.03, 0.065), (x + 0.03, y + 0.03, 0.15), 0.005, 'iron'))
            M.add(cbox((x + 0.03, y - 0.015, 0.1), (x + 0.09, y + 0.015, 0.12), 0.004, 'red'))       # brake pedal
    # base members and braces along the long sides only (the ends stay open under the deck)
    for y in (-hy, hy):
        M.add(tube([(-hx, y, 0.22), (hx, y, 0.22)], 0.022, 'alu', sides=6))
        M.add(tube([(-hx, y, 0.24), (hx, y, GAP - 0.02)], 0.018, 'alu', sides=6))
        for z in (1.45, top - 0.02):
            M.add(tube([(-hx, y, z), (hx, y, z)], 0.024, 'p1', sides=8))
    for x in (-hx, hx):
        for z in (1.45, top - 0.02):
            M.add(tube([(x, -hy, z), (x, hy, z)], 0.024, 'p1', sides=8))
    # the deck: an aluminium frame at the gap, plywood on it, toe boards round it
    for y in (-hy, hy):
        M.add(cbox((-hx, y - 0.03, GAP), (hx, y + 0.03, GAP + 0.06), 0.006, 'alu'))
    for x in (-hx + 0.03, 0.0, hx - 0.03):
        M.add(cbox((x - 0.03, -hy, GAP), (x + 0.03, hy, GAP + 0.06), 0.006, 'alu'))
    M.add(wood_box((-hx, -hy, GAP + 0.06), (hx, hy, GAP + 0.08), band=3, along=0))
    deck = GAP + 0.08
    for k, y in enumerate((-hy + 0.015, hy - 0.015)):
        M.add(wood_box((-hx, y - 0.012, deck), (hx, y + 0.012, deck + 0.15), band=k, along=0))
    for k, x in enumerate((-hx + 0.015, hx - 0.015)):
        M.add(wood_box((x - 0.012, -hy + 0.03, deck), (x + 0.012, hy - 0.03, deck + 0.15), band=2 + k, along=1))
    # clippings, a hedge trimmer and a trug
    rng = np.random.default_rng(7)
    for i in range(9):
        M.add(blob((rng.uniform(-0.75, 0.2), rng.uniform(-0.4, 0.45), deck + 0.03), (rng.uniform(0.1, 0.18), rng.uniform(0.08, 0.14), 0.06),
                   ('leaf', 'leafd', 'leafl')[i % 3], n=7, rings=2, seed=40 + i, jitter=0.3, flat_bottom=-0.2))
    M.add(rbox((0.3, -0.25, deck), (0.6, -0.12, deck + 0.12), (0.03, 0.03, 0.03), 'p1', seg=(1, 1, 1)))
    M.add(cbox((0.6, -0.2, deck + 0.04), (1.12, -0.17, deck + 0.07), 0.005, 'metal'))
    for k in range(10):
        x = 0.62 + 0.05 * k
        M.add(cbox((x, -0.215, deck + 0.045), (x + 0.02, -0.155, deck + 0.065), 0.003, 'metal'))
    M.add(tube([(0.32, -0.19, deck + 0.12), (0.4, -0.19, deck + 0.2), (0.55, -0.19, deck + 0.2), (0.6, -0.19, deck + 0.12)], 0.014, 'dark', sides=5))
    tr = tray((0.16, 0.12, 0.04), (0.2, 0.15, 0.06), 0.0, 0.16, 0.008, 'p2', inner_mat='p2', nc=2, fill=0.12)
    xform(tr, T(0.45, 0.32, deck)); M.add(tr)
    M.add(blob((0.45, 0.32, deck + 0.14), (0.17, 0.12, 0.06), 'leafd', n=7, rings=2, seed=61, jitter=0.3))
    _front(M)
    _slide(M, hx + 0.03, top + 0.02)
    return M


def _propped_bough(name, oak):
    """A garden apple tree (oak=False) or an old park oak (oak=True) whose low bough reaches out over
    the footpath and sags to the gap over the kid's line, held up by a prop. The trunk stands well
    behind the path (clear of garden walls and park hedges, which the bough arches over); the
    bough's low run is centred on x = 0."""
    if oak:
        M = Model(name, ppm=50, grime=dict(rust=0.0, chips=0.0, streaks=0.15, mottle=0.1, dirt_h=0.3))
        bark, lv = 'oakbark', ('leafoak', 'leafoakl', 'leafoak', 'ivy')
        tx, ty, tr_ = 2.0, 3.15, 0.42
        r_low = 0.15
        h_trunk = 3.0
    else:
        M = Model(name, ppm=65, grime=dict(rust=0.0, chips=0.0, streaks=0.15, mottle=0.1, dirt_h=0.3))
        bark, lv = 'applebark', ('leafap', 'leafapl', 'leafap')
        tx, ty, tr_ = 1.5, 2.5, 0.2
        r_low = 0.1
        h_trunk = 2.0
    zc = GAP + r_low                      # the bough's centre over the kid's line
    # a leaning trunk with a flared foot, splitting into the crown's main limbs
    M.add(limb(curve([(tx, ty, -0.05), (tx + 0.05, ty + 0.03, h_trunk * 0.5), (tx - 0.08, ty + 0.02, h_trunk)], 7),
               tr_ * 1.3, tr_ * 0.75, bark, sides=12 if oak else 10, tile=('bark', 1.2)))
    limbs = ((1.1, 0.4, 1.7), (-0.9, 0.6, 1.9), (0.3, -0.5, 2.2), (-0.2, 0.2, 2.4)) if oak else ((0.8, 0.2, 1.3), (-0.6, 0.4, 1.4), (0.1, -0.4, 1.5))
    p0 = Vector((tx - 0.08, ty + 0.02, h_trunk - 0.1))
    for (dx, dy, dz) in limbs:
        M.add(limb(curve([p0, p0 + Vector((dx * 0.45, dy * 0.45, dz * 0.6)), p0 + Vector((dx, dy, dz))], 5), tr_ * 0.62, tr_ * 0.22, bark, sides=8, tile=('bark', 1.0)))
    # the low bough: out of the trunk nearly level, over the wall or hedge, sagging gently down over
    # the path, along it at the gap, and up again at its tip
    if oak:
        ctrl = [(tx - 0.15, ty - 0.35, 2.35), (1.6, 2.2, 2.15), (1.05, 1.25, 1.7), (0.5, 0.45, zc + 0.15), (0.0, 0.0, zc),
                (-0.85, -0.12, zc + 0.03), (-1.6, -0.32, zc + 0.3), (-2.3, -0.5, 1.75)]
        r0, r1 = 0.26, 0.07
    else:
        ctrl = [(tx - 0.1, ty - 0.15, 1.95), (1.2, 1.95, 1.88), (0.8, 1.05, 1.45), (0.35, 0.35, zc + 0.1), (0.0, 0.0, zc),
                (-0.65, -0.08, zc + 0.02), (-1.2, -0.25, zc + 0.22), (-1.7, -0.4, 1.4)]
        r0, r1 = 0.15, 0.04
    path = curve(ctrl, 18)
    # keep the low run's underside exactly at the gap over the lane
    for i, p in enumerate(path):
        if abs(p.y) < LANE + 0.35:
            t = i / (len(path) - 1)
            rr = r0 + (r1 - r0) * t ** 0.8
            p.z = max(p.z, GAP + rr * 1.04 + 0.004)
    M.add(limb(path, r0, r1, bark, sides=10 if oak else 8, tile=('bark', 0.9)))
    # the foliage: lobes of leaf-clump cards over dark cores (kit_barriers.py builds them once the
    # atlas is laid out): the crown spreading toward the path over the bough, side shoots along the
    # bough and a spray at its tip; nothing hangs into the clear gap over the kid's line
    rng = np.random.default_rng(31 if oak else 17)
    ramp = R_OAK if oak else R_APPLE

    def clear(corners):
        return any(abs(c[1]) < LANE + 0.1 and c[2] < GAP + 0.15 for c in corners)
    tip = path[-1]
    shoots = [LV.Mass(np.array(tip) + (-0.2, -0.1, 0.3), (0.52, 0.42, 0.34) if oak else (0.46, 0.38, 0.3))]
    for k, i in enumerate((6, 10, 13)):
        p = path[i]
        q = p + Vector((0.15 * (k - 1), -0.3 + 0.2 * k, 0.6 + 0.1 * k))
        M.add(limb([p, (p + q) / 2 + Vector((0, 0, 0.1)), q], 0.04 if oak else 0.028, 0.012, bark, sides=5, tile=('bark', 0.5)))
        r = 0.36 if oak else 0.32
        shoots.append(LV.Mass(np.array(q) + (0, 0, 0.15), (r, r * 0.82, r * 0.66), bright=rng.uniform(-0.04, 0.04)))
    cz = h_trunk + (1.75 if oak else 1.15)
    if oak:
        crown = LV.masses_from((tx - 0.3, ty - 0.5, cz), (2.9, 2.0, 1.5), 9, rng, rf=(0.36, 0.46), shell=0.62, zlo=-0.55)
    else:
        crown = LV.masses_from((tx - 0.3, ty - 0.5, cz), (1.5, 1.2, 0.95), 6, rng, rf=(0.4, 0.52), shell=0.6, zlo=-0.55)
    M.leafcards = [dict(masses=crown, ramp=ramp, size=1.15 if oak else 0.85, keep_out=clear),
                   dict(masses=shoots, ramp=ramp, size=0.62 if oak else 0.56, density=1.15, inner=0.2, core=0.5,
                        keep_out=clear)]
    if not oak:
        # apples hanging under the lobes (their lower, nearer side), a few windfalls on the ground
        for i, m in enumerate(crown + shoots):
            for k in range(3 if m in crown else 2):
                a = rng.uniform(0, 2 * PI)
                d = Vector((math.cos(a), math.sin(a) * 0.8 - 0.35, -0.75)).normalized()
                p = Vector(m.c) + Vector((d.x * m.r[0], d.y * m.r[1], d.z * m.r[2])) * 0.9
                if p.z < GAP + 0.35 and abs(p.y) < LANE + 0.2: continue
                M.add(blob(p, (0.05, 0.05, 0.053), 'apple', n=6, rings=2, seed=200 + i * 3 + k, jitter=0.05))
        for i in range(5):
            M.add(blob((tx + rng.uniform(-1.0, 0.5), ty - rng.uniform(0.3, 0.9), 0.04), (0.045, 0.045, 0.04), 'apple', n=6, rings=2, seed=400 + i, jitter=0.05))
    # the prop: forked (apple) or a squared timber post with an iron band (oak), standing in front of
    # the kid's line, leaning in under the bough beyond the low run
    xp = -0.95 if oak else -0.8
    j = min(range(len(path)), key=lambda i: abs(path[i].x - xp))
    hp = path[j]
    rr = r0 + (r1 - r0) * (j / (len(path) - 1)) ** 0.8
    # it meets the bough on its near side, clear of the kid's line
    foot = Vector((xp, -1.0, 0.0))
    top = Vector((hp.x, hp.y - rr * 0.85, hp.z - rr * 0.45))
    if oak:
        M.add(bar(foot, top - (top - foot).normalized() * 0.04, 0.13, 'timber'))
        k_ = (top - foot).normalized()
        M.add(xform(cbox((-0.08, -0.08, -0.03), (0.08, 0.08, 0.03), 0.01, 'iron'), frame(top - k_ * 0.25, k_)))
        M.add(blob(foot, (0.18, 0.18, 0.06), 'soil', n=8, rings=2, seed=5, flat_bottom=0.0))
    else:
        M.add(limb([foot, (foot * 0.4 + top * 0.6)], 0.045, 0.04, 'applebark', sides=6, tile=('bark', 0.6)))
        fork = foot * 0.4 + top * 0.6
        for sgn in (-1, 1):
            M.add(limb([fork, top + Vector((sgn * 0.09, 0, 0.03))], 0.035, 0.028, 'applebark', sides=6, tile=('bark', 0.6)))
    # roots at the trunk's foot, ivy climbing the oak
    for k in range(5 if oak else 3):
        a = 2 * PI * k / (5 if oak else 3) + 0.4
        d = Vector((math.cos(a), math.sin(a), 0))
        M.add(limb([Vector((tx, ty, 0.25)) + d * tr_ * 0.5, Vector((tx, ty, 0.02)) + d * tr_ * 2.0], tr_ * 0.45, tr_ * 0.12, bark, sides=6, tile=('bark', 0.6)))
    if oak:
        M.leafcards.append(dict(masses=[LV.Mass((tx - 0.05, ty - 0.36, 1.3), (0.34, 0.14, 0.95))], ramp=R_IVY, size=0.4,
                                density=1.3, inner=0.0, core=None))
    half = 1.05 if oak else 0.85
    _front(M)
    _slide(M, half, GAP + 2 * r_low + 0.04)
    return M


def apple_bough():
    """A garden apple tree behind the wall, its low bough heavy with apples dipping over the footpath,
    propped on a forked stick. Solid: the low run of the bough (hop it, or slide under)."""
    return _propped_bough('AppleBough', oak=False)


# ================================================================ MARKET
def stall_awning():
    """A fruit and veg stall set out on the footpath: a trestle table under a cloth with crates of
    oranges, apples, lemons, limes and tomatoes, a pan scale, bananas hung from the front rail, and a
    striped awning on four poles, sloping to the front and overhanging it. The table is too low to
    walk under, there's no room on it under the awning and the awning's too high to jump: duck under
    the table. Solids: the table and its fruit, and the awning (the game makes it bouncy)."""
    M = Model('StallAwning', p1=(0.85, 0.30, 0.28), p2=(0.32, 0.55, 0.36), ppm=90, grime=dict(rust=0.05, chips=0.15, streaks=0.25, dirt_h=0.3))
    hx, hy = 1.1, 0.52
    for x in (-hx + 0.05, hx - 0.05):
        for y in (-hy + 0.03, hy - 0.03):
            M.add(cbox((x - 0.025, y - 0.025, 0.0), (x + 0.025, y + 0.025, GAP), 0.005, 'timber'))
        M.add(cbox((x - 0.02, -hy, GAP), (x + 0.02, hy, GAP + 0.045), 0.004, 'timber'))
    for y in (-hy + 0.03, hy - 0.03):
        M.add(cbox((-hx, y - 0.02, GAP), (hx, y + 0.02, GAP + 0.045), 0.004, 'timber'))
        M.add(bar((-hx + 0.07, y, 0.25), (hx - 0.07, y, 0.25), 0.03, 'timber'))
    M.add(wood_box((-hx, -hy, GAP + 0.045), (hx, hy, GAP + 0.07), band=2, along=0))
    deck = GAP + 0.07
    # the cloth: on the top, a short drop at the front (above a sliding kid), longer at the back
    M.add(cbox((-hx - 0.02, -hy - 0.03, deck), (hx + 0.02, hy + 0.03, deck + 0.012), 0.004, 'p2'))
    M.add(cbox((-hx - 0.02, -hy - 0.042, deck - 0.075), (hx + 0.02, -hy - 0.03, deck + 0.012), 0.004, 'p2'))
    M.add(cbox((-hx - 0.02, hy + 0.03, deck - 0.3), (hx + 0.02, hy + 0.042, deck + 0.012), 0.004, 'p2d'))
    for x in np.linspace(-hx + 0.1, hx - 0.1, 8):
        M.add(cbox((x - 0.006, -hy - 0.046, deck - 0.075), (x + 0.006, -hy - 0.04, deck + 0.01), 0.002, 'white'))
    deck += 0.012
    # crates of fruit in two rows, heaped
    fruit = ('orangef', 'apple', 'lemon', 'limef', 'tomato', 'orangef', 'apple', 'limef')
    k = 0
    for row, y in enumerate((-0.23, 0.23)):
        for i in range(4):
            x = -hx + 0.08 + (2 * hx - 0.16) * (i + 0.5) / 4
            M.add(wood_box((x - 0.22, y - 0.18, deck), (x + 0.22, y + 0.18, deck + 0.17), band=(i + row) % 4, along=0))
            M.add(box((x - 0.2, y - 0.16, deck + 0.17), (x + 0.2, y + 0.16, deck + 0.171), 'soil'))
            rng = np.random.default_rng(100 + k)
            f = fruit[k % len(fruit)]
            for a in range(4):
                for b in range(3):
                    px = x - 0.15 + a * 0.1 + rng.uniform(-0.015, 0.015)
                    py = y - 0.1 + b * 0.1 + rng.uniform(-0.015, 0.015)
                    hz = 0.04 * (1 - abs(a - 1.5) / 2.5) * (1 - abs(b - 1) / 2)
                    M.add(blob((px, py, deck + 0.17 + 0.03 + hz), (0.045, 0.045, 0.042), f, n=6, rings=2, seed=k * 20 + a * 3 + b, jitter=0.06))
            k += 1
    fruit_top = deck + 0.17 + 0.03 + 0.04 + 0.045
    # a pan scale at the front corner
    M.add(cbox((0.78, -0.5, deck), (0.98, -0.36, deck + 0.09), 0.012, 'white'))
    M.add(xform(cyl(0.09, 0, 0.015, 16, 'chrome'), T(0.88, -0.43, deck + 0.1)))
    # the awning: four poles, a frame sloping from 2.45 at the back to 2.15 at the front
    zf, zbk = 2.15, 2.45
    yf, yb = -0.82, 0.78
    for x in (-hx - 0.1, hx + 0.1):
        M.add(tube([(x, yf + 0.05, 0.0), (x, yf + 0.05, zf)], 0.022, 'iron', sides=6))
        M.add(tube([(x, yb, 0.0), (x, yb, zbk)], 0.022, 'iron', sides=6))
        M.add(xform(cyl(0.05, 0, 0.03, 10, 'iron'), T(x, yf + 0.05, 0.0)))
        M.add(xform(cyl(0.05, 0, 0.03, 10, 'iron'), T(x, yb, 0.0)))
    M.add(tube([(-hx - 0.1, yf + 0.05, zf - 0.06), (hx + 0.1, yf + 0.05, zf - 0.06)], 0.018, 'iron', sides=6))
    ns = 9
    cw = 2 * hx + 0.5
    for i in range(ns):
        x0 = -cw / 2 + cw * i / ns; x1 = -cw / 2 + cw * (i + 1) / ns
        mat = 'p1' if i % 2 == 0 else 'canvas'
        pts = [(x0, yf - 0.12, zf - 0.02), (x1, yf - 0.12, zf - 0.02), (x1, yb + 0.05, zbk + 0.02), (x0, yb + 0.05, zbk + 0.02)]
        M.add(loft([[Vector(p) for p in pts], [Vector(p) + Vector((0, 0, 0.025)) for p in pts]], mat, closed_bottom=True, closed_top=True))
        # scalloped valance hanging at the front
        val = [(x0, 0.0), (x1, 0.0), (x1, -0.12)] + [((x0 + x1) / 2 + (x1 - x0) / 2 * math.cos(PI * t / 6), -0.12 - 0.05 * math.sin(PI * t / 6)) for t in range(7)] + [(x0, -0.12)]
        v = extrude_poly(val, 0.012, mat)
        xform(v, T(0, yf - 0.115, zf - 0.02) @ R(PI / 2, 'X'))
        M.add(fix_normals(v))
    # bananas and a hanging price board (blank) on the front rail
    for i, x in enumerate((-0.7, -0.55)):
        for kk in range(4):
            a = kk * 0.5 - 0.75
            p0 = Vector((x, yf + 0.05, zf - 0.12))
            M.add(tube([p0, p0 + Vector((0.08 * math.sin(a), 0.03, -0.14)), p0 + Vector((0.12 * math.sin(a), 0.06, -0.24))], 0.022, 'banana', sides=5))
        M.add(bar((x, yf + 0.05, zf - 0.06), (x, yf + 0.05, zf - 0.12), 0.01, 'dark'))
    M.add(cbox((0.35, yf + 0.03, zf - 0.42), (0.75, yf + 0.06, zf - 0.18), 0.01, 'dark'))
    M.add(cbox((0.37, yf + 0.025, zf - 0.40), (0.73, yf + 0.03, zf - 0.20), 0.004, 'p2'))
    for x in (0.42, 0.68):
        M.add(bar((x, yf + 0.045, zf - 0.18), (x, yf + 0.05, zf - 0.06), 0.006, 'iron'))
    _front(M)
    _slide(M, hx, fruit_top, canopyHalf=round(cw / 2, 3), canopyBottom=zf - 0.02, canopyTop=zbk + 0.045)
    return M


def roll_shutter():
    """A covered passage's entrance where the footpath runs under a building: a rendered pier on the
    far side, a slim steel guide post at the kerb, the shutter box and a deep fascia over the top,
    and the corrugated roll shutter half up, its bottom rail at the gap. Too tall to climb: slide
    under. Solid: the shutter and everything above it."""
    M = Model('RollShutter', p1=(0.30, 0.46, 0.40), p2=(0.92, 0.88, 0.80), ppm=60, grime=dict(rust=0.25, chips=0.2, streaks=0.6, dirt_h=0.45))
    yn, yf = -1.58, 1.58
    zbox0, zbox1, ztop = 2.32, 2.62, 3.15
    hx = 0.06
    # far pier, rendered, on a stone plinth, with a pilaster cap
    M.add(cbox((-0.36, 1.62, 0.0), (0.36, 2.05, 0.3), 0.02, 'stone'))
    M.add(cbox((-0.33, 1.64, 0.3), (0.33, 2.02, ztop), 0.02, 'p2'))
    M.add(cbox((-0.37, 1.6, ztop - 0.12), (0.37, 2.06, ztop), 0.02, 'stone'))
    M.feat('front', 'ashlar', a0=-0.33, a1=0.33, b0=0.3, b1=ztop - 0.12, course=0.28, block=0.66, col=(0.84, 0.81, 0.75), tone=0.04)
    # near guide post at the kerb
    M.add(cbox((-0.08, yn - 0.12, 0.0), (0.08, yn + 0.02, 0.06), 0.01, 'conc'))
    M.add(cbox((-0.055, yn - 0.1, 0.06), (0.055, yn, zbox1), 0.006, 'p1'))
    # guide channels down both sides
    for y0, y1 in ((yn, yn + 0.05), (yf - 0.05, yf + 0.04)):
        M.add(cbox((-hx - 0.025, y0, 0.0), (hx + 0.025, y1, zbox0), 0.004, 'galv'))
    # the shutter: corrugated slats from the box down to the gap, a bottom rail with handles
    sh = box((-0.025, yn + 0.02, GAP + 0.08), (0.025, yf - 0.02, zbox0), 'tex')
    settile(sh, 'slats', lambda co, f: ((co.y - yn) / (yf - yn), (co.z - GAP) / (zbox0 - GAP)), mat='p1k')
    M.add(sh)
    M.add(cbox((-hx, yn + 0.01, GAP), (hx, yf - 0.01, GAP + 0.08), 0.008, 'galv'))
    for y in (-0.5, 0.5):
        for s in (-1, 1):
            M.add(tube([(s * hx, y - 0.07, GAP + 0.05), (s * (hx + 0.04), y - 0.05, GAP + 0.05), (s * (hx + 0.04), y + 0.05, GAP + 0.05), (s * hx, y + 0.07, GAP + 0.05)], 0.008, 'iron', sides=5))
    M.add(cbox((-hx - 0.012, -0.06, GAP + 0.01), (-hx, 0.06, GAP + 0.07), 0.004, 'brass'))
    # the shutter box and the fascia above, running from the guide post to the pier
    M.add(rbox((-0.22, yn - 0.12, zbox0), (0.22, yf + 0.06, zbox1), (0.06, 0.02, 0.06), 'p1', seg=(2, 1, 2)))
    M.add(cbox((-0.42, yn - 0.18, zbox1), (0.42, yf + 0.44, ztop), 0.02, 'p2'))
    M.add(cbox((-0.43, yn - 0.19, zbox1 + 0.06), (0.43, yf + 0.45, zbox1 + 0.12), 0.01, 'p1'))
    M.add(cbox((-0.43, yn - 0.19, ztop - 0.06), (0.43, yf + 0.45, ztop), 0.01, 'stone'))
    # a hanging blade sign (an apple painted on it) and a lamp under the fascia at the kerb end
    M.add(bar((0.0, yn - 0.18, zbox1 - 0.02), (0.0, yn - 0.62, zbox1 - 0.02), 0.025, 'iron'))
    for y in (yn - 0.25, yn - 0.55):
        M.add(bar((0.0, y, zbox1 - 0.03), (0.0, y, zbox1 - 0.1), 0.01, 'iron'))
    M.add(cbox((-0.02, yn - 0.6, zbox1 - 0.46), (0.02, yn - 0.2, zbox1 - 0.1), 0.01, 'p1'))
    for s in (-1, 1):
        d = cyl(0.12, 0, 0.004, 16, 'apple')
        xform(d, T(s * 0.021, yn - 0.4, zbox1 - 0.28) @ R(s * PI / 2, 'Y')); M.add(d)
        lf = blob((s * 0.024, yn - 0.34, zbox1 - 0.14), (0.005, 0.04, 0.02), 'leaf', n=6, rings=2, seed=3)
        M.add(lf)
    M.add(xform(cyl(0.09, 0, 0.06, 14, 'iron', bevel=0.01), T(0.0, yn + 0.2, zbox1 - 0.06)))
    M.add(xform(cyl(0.075, 0, 0.01, 14, 'lamp'), T(0.0, yn + 0.2, zbox1 - 0.07)))
    _front(M)
    _slide(M, hx + 0.04, ztop)
    return M


def delivery_conveyor():
    """A gravity roller conveyor across the footpath from a delivery van at the kerb to a shop door:
    a level bed of rollers at the gap on two stands either side of the kid's line, cartons and a
    drinks crate on their way in. Solid: the bed (hop on, or slide under)."""
    M = Model('DeliveryConveyor', p1=(0.36, 0.52, 0.70), ppm=110, grime=dict(rust=0.2, chips=0.3, streaks=0.4, dirt_h=0.3))
    hx = 0.3
    y0, y1 = -1.9, 1.9
    zt = GAP + 0.09
    for s in (-1, 1):
        M.add(cbox((s * hx - 0.02, y0, GAP), (s * hx + 0.02, y1, zt + 0.02), 0.004, 'p1'))
        M.add(cbox((s * (hx - 0.012) - 0.01, y0, zt - 0.02), (s * (hx - 0.012) + 0.01, y1, zt + 0.025), 0.003, 'p1d'))
    for y in np.arange(y0 + 0.05, y1 - 0.02, 0.1):
        M.add(xform(cyl(0.024, -hx + 0.02, hx - 0.02, 8, 'galv'), T(0.0, y, zt - 0.03) @ R(PI / 2, 'Y')))
    for y in (y0, y1):
        M.add(cbox((-hx - 0.02, y - 0.02, GAP + 0.01), (hx + 0.02, y, zt), 0.004, 'p1d'))
    # stands either side of the kid's line
    for ys in (-1.15, 1.15):
        for s in (-1, 1):
            M.add(cbox((s * hx - 0.025, ys - 0.025, 0.04), (s * hx + 0.025, ys + 0.025, GAP), 0.005, 'p1'))
            M.add(cbox((s * hx - 0.04, ys - 0.06, 0.0), (s * hx + 0.04, ys + 0.06, 0.04), 0.005, 'rubber'))
        M.add(cbox((-hx, ys - 0.02, GAP - 0.06), (hx, ys + 0.02, GAP), 0.004, 'p1'))
        M.add(cbox((-hx, ys - 0.02, 0.18), (hx, ys + 0.02, 0.22), 0.004, 'p1'))
        M.add(bar((-hx, ys, 0.22), (hx, ys, GAP - 0.06), 0.03, 'p1d'))
    # cartons and a crate on the rollers, clear of the kid's line
    def carton(x, y, w, d, h, rot):
        b = cbox((-w / 2, -d / 2, 0), (w / 2, d / 2, h), 0.008, 'card')
        xform(b, T(x, y, zt) @ R(rot, 'Z')); M.add(b)
        tp = box((-0.035, -d / 2 - 0.002, h - 0.002), (0.035, d / 2 + 0.002, h + 0.002), 'tape')
        xform(tp, T(x, y, zt) @ R(rot, 'Z')); M.add(tp)
        for s in (-1, 1):
            tp = box((-0.035, s * (d / 2) - 0.002 + (0.002 if s > 0 else 0), h - 0.12), (0.035, s * (d / 2) + (0.002 if s > 0 else -0.0), h), 'tape')
            xform(tp, T(x, y, zt) @ R(rot, 'Z')); M.add(tp)
    carton(0.0, -0.95, 0.42, 0.36, 0.32, 0.05)
    carton(-0.02, 0.92, 0.46, 0.4, 0.28, -0.06)
    cr = tray((0.2, 0.16, 0.02), (0.21, 0.17, 0.02), 0.0, 0.26, 0.012, 'p1', inner_mat='p1d', nc=2, fill=0.2)
    xform(cr, T(0.0, -1.55, zt)); M.add(cr)
    for a in range(3):
        for b in range(2):
            p = Vector((-0.12 + a * 0.12, -1.61 + b * 0.12, zt + 0.2))
            M.add(xform(cyl(0.032, 0, 0.16, 8, 'green', bevel=0.01), T(p)))
            M.add(xform(cyl(0.014, 0.16, 0.2, 6, 'green'), T(p)))
            M.add(xform(cyl(0.016, 0.2, 0.215, 6, 'red'), T(p)))
    _front(M)
    _slide(M, hx + 0.02, zt + 0.02)
    return M


# ================================================================ BEACH
def _surfboard(L, wmax, thick, mats, stripe=None, seed=0):
    """A surfboard lying flat along X, nose to +X: lofted ellipse sections, a little nose rocker.
    stripe: (u0, u1, mat) a band of colour across it; returns the bmesh."""
    st = 12; m = 8
    rings = []
    us = [0.0, 0.03] + [0.05 + 0.92 * i / (st - 3) for i in range(st - 2)]
    for u in us:
        x = -L / 2 + L * u
        w = wmax * max(0.04, math.sin(PI * (0.14 + 0.85 * u))) ** 0.75
        if u < 0.03: w *= 0.8
        t = thick * (0.55 + 0.45 * math.sin(PI * min(u, 0.98)))
        rz = 0.08 * u ** 3
        rings.append([Vector((x, w * math.cos(2 * PI * k / m), rz + t * 0.5 * math.sin(2 * PI * k / m))) for k in range(m)])
    bands = []
    for i in range(len(us) - 1):
        uc = (us[i] + us[i + 1]) / 2
        bands.append(stripe[2] if stripe and stripe[0] <= uc <= stripe[1] else mats)
    bm = loft(rings, bands, closed_bottom=True, closed_top=True, sm=1)
    return fix_normals(bm)


def surf_rack():
    """A surf school's board rack across the beach path: two timber end frames with padded arms and
    surfboards lying across them in five tiers, the lowest just above the gap, with a beach flag
    flying from the top. The boards run the whole width; the frames stand in from the ends, their
    posts either side of the kid's line. Too tall to jump: slide under."""
    M = Model('SurfRack', p1=(0.98, 0.50, 0.42), ppm=80, grime=dict(rust=0.1, chips=0.1, streaks=0.3, dirt_h=0.4, ground=0.4))
    tiers, sp, arm, thick = 5, 0.32, 0.05, 0.07
    L = 2.6
    fx, py = L / 2 - 0.3, 0.62
    top = GAP + (tiers - 1) * sp + arm + thick + 0.12
    for x in (-fx, fx):
        for y in (-py, py):
            M.add(cbox((x - 0.045, y - 0.045, -0.3), (x + 0.045, y + 0.045, top), 0.008, 'timber'))
        for i in range(tiers):
            z = GAP + i * sp
            M.add(wood_box((x - 0.04, -py - 0.07, z), (x + 0.04, py + 0.07, z + arm), band=i % 4, along=1))
            M.add(rbox((x - 0.045, -py + 0.04, z + arm), (x + 0.045, py - 0.04, z + arm + 0.014), (0.006, 0.006, 0.006), 'foam', seg=(1, 1, 1)))
    for y in (-py, py):
        M.add(wood_box((-fx - 0.05, y - 0.035, top - 0.07), (fx + 0.05, y + 0.035, top), band=3, along=0))
    M.add(bar((-fx, py + 0.06, 0.25), (fx, py + 0.06, top - 0.12), 0.05, 'timber'))
    cols = ['coral', 'teal', 'sun', 'white', 'sky', 'limeg', 'coral', 'sun', 'teal', 'white']
    k = 0
    for i in range(tiers):
        z = GAP + i * sp + arm + 0.014 + thick * 0.5
        for j, y in enumerate((-0.28, 0.28)):
            c = cols[k % len(cols)]; band = cols[(k + 3) % len(cols)]
            bm = _surfboard(L, 0.26, thick, c, stripe=(0.55, 0.62, band) if k % 3 != 2 else (0.25, 0.3, band))
            xform(bm, T(0.0, y, z) @ (Matrix.Identity(4) if (i + j) % 2 == 0 else R(PI, 'Z')))
            M.add(bm)
            fin = extrude_poly([(0, 0), (0.11, 0), (0.02, -0.07)], 0.01, 'dark')
            sgn = 1 if (i + j) % 2 == 0 else -1
            xform(fin, T(-sgn * (L / 2 - 0.16), y - 0.005, z - thick * 0.25) @ R(PI / 2, 'X') @ (Matrix.Identity(4) if sgn > 0 else S(-1, 1, 1)))
            M.add(fix_normals(fin))
            k += 1
    # the beach flag: a teardrop on a bent pole from the far frame
    pole = [(fx, py, top), (fx, py, top + 1.3), (fx - 0.1, py, top + 1.62), (fx - 0.28, py, top + 1.7)]
    M.add(tube(pole, 0.016, 'chrome', sides=6))
    drop = [(0.0, 0.0), (-0.3, 0.05), (-0.42, -0.25), (-0.36, -0.75), (-0.2, -1.05), (-0.04, -1.1), (0.0, -1.0)]
    fl = extrude_poly(drop, 0.008, 'coral')
    xform(fl, T(fx, py - 0.004, top + 1.68) @ R(PI / 2, 'X'))
    M.add(fix_normals(fl))
    st = extrude_poly([(-0.06, -0.3), (-0.33, -0.36), (-0.3, -0.6), (-0.05, -0.55)], 0.009, 'white')
    xform(st, T(fx, py - 0.006, top + 1.68) @ R(PI / 2, 'X')); M.add(fix_normals(st))
    for y in (-py, py):
        for x in (-fx, fx):
            M.add(blob((x, y, 0.0), (0.16, 0.16, 0.05), 'sandw', n=8, rings=2, seed=int(x * 10 + y * 7) + 50, jitter=0.25, flat_bottom=0.0))
    _front(M)
    _slide(M, L / 2, top)
    return M


def boat_trestles():
    """A wooden rowing boat upturned on two trestles on the sand to be repainted: a clinker hull, blue
    below a red stripe and white topsides, half sanded back, a varnished keel strip running down into
    the stem at the bow (+X) and a square transom at the stern; oars leaning on the far trestle, a
    tin and a brush on the sand. Its gunwales rest on the trestle bars at the gap, dipping a little
    toward bow and stern. Solid: the hull (slide under, or double jump onto it)."""
    M = Model('BoatTrestles', p1=(0.26, 0.42, 0.66), ppm=80, grime=dict(rust=0.0, chips=0.5, streaks=0.3, dirt_h=0.3, ground=0.35))
    L, B, D = 3.4, 0.7, 0.55
    zg = GAP + 0.07
    for x in (-1.0, 1.0):
        trestle(M, x, 0.8, zg, splay=0.24)

    def beam(u):       # half-beam: a square-ish stern, full amidships, fining to the stem
        return max(0.03, B * (1 - max(0.0, (u - 0.5) / 0.5) ** 1.9) ** 0.7 * (0.8 + 0.2 * min(1.0, u / 0.25)))

    def depth(u):      # gunwale to keel: deepest amidships, the keel curving down into the stem
        return D * (0.86 + 0.14 * math.sin(PI * min(u, 0.9) / 0.9 * 0.5 + PI * 0.25)) * (1 - 0.5 * max(0.0, (u - 0.7) / 0.3) ** 2)

    def sheer(u):      # the gunwale, upside down: dips a little toward the ends
        return zg - 0.035 * ((2 * u - 1) ** 2)

    st = 16; m = 9; th = 0.025
    rings = []
    xs = [-L / 2 + L * i / (st - 1) for i in range(st)]
    for x in xs:
        u = (x + L / 2) / L
        bb, d, zs = beam(u), depth(u), sheer(u)
        ring = []
        for k in range(m + 1):
            phi = PI * k / m
            ring.append(Vector((x, -bb * math.cos(phi), zs + d * math.sin(phi) ** 0.7)))
        for k in range(m, -1, -1):
            phi = PI * k / m
            ring.append(Vector((x, -max(bb - th, 0.01) * math.cos(phi), zs + (d - th) * math.sin(phi) ** 0.7)))
        rings.append(ring)
    hull = loft(rings, 'p1', closed_bottom=True, closed_top=True, sm=0)
    fix_normals(hull)

    def hull_paint(c, n):
        u = (c.x + L / 2) / L
        rel = (c.z - sheer(u)) / max(depth(u), 1e-3)
        if n.z < -0.5: return 'white'
        if rel < 0.3: return 'white'
        if rel < 0.36: return 'red'
        return None
    paint_by(hull, hull_paint)
    M.add(hull)
    # clinker lands as lines along the side, a sanded-back patch, keel strip and stem, transom, gunwales
    lines = []
    for f in (0.2, 0.38, 0.56, 0.74):
        lines.append([(x, sheer((x + L / 2) / L) + depth((x + L / 2) / L) * f ** 0.85) for x in np.linspace(-L / 2 + 0.02, L / 2 - 0.05, 20)])
    M.feat('front', 'lines', lines=lines, w=0.007, col=(0.6, 0.6, 0.62), alpha=0.9)
    M.feat('front', 'stain', a=0.45, b=zg + 0.38, ra=0.55, rb=0.14, col=(1.0, 0.95, 0.85), alpha=0.6)
    keel = [Vector((x, 0.0, sheer((x + L / 2) / L) + depth((x + L / 2) / L) + 0.012)) for x in np.linspace(-L / 2, L / 2, 14)]
    keel.append(Vector((L / 2 + 0.02, 0.0, sheer(1.0) + 0.05)))
    M.add(sweep(keel, [(-0.035, -0.02), (0.035, -0.02), (0.03, 0.02), (-0.03, 0.02)], 'timber', up=(0, 1, 0)))
    tr = [Vector((0.0, -beam(0.0) * math.cos(PI * k / m), sheer(0.0) + depth(0.0) * math.sin(PI * k / m) ** 0.7)) for k in range(m + 1)]
    tb = extrude_poly([(p.y, p.z) for p in tr], 0.04, 'timber')
    xform(tb, T(-L / 2 - 0.04, 0, 0) @ basis((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)))
    M.add(fix_normals(tb))
    for side in (-1, 1):
        g = [Vector((x, side * (beam((x + L / 2) / L) + 0.012), sheer((x + L / 2) / L) + 0.02)) for x in xs]
        M.add(sweep(g, [(-0.02, -0.015), (0.02, -0.015), (0.02, 0.015), (-0.02, 0.015)], 'timber', up=(0, 0, 1)))
    # two oars leaning on the far trestle, blades down on the sand
    for k, dx in enumerate((0.0, 0.16)):
        foot = Vector((1.45 + dx, 1.0, 0.03)); hand = Vector((1.05 + dx, 0.88, 1.75))
        d = (hand - foot).normalized()
        blade = cbox((-0.075, -0.009, 0.0), (0.075, 0.009, 0.55), 0.012, 'white')
        xform(blade, frame(foot, d, (0, -1, 0)))
        M.add(blade)
        M.add(tube([foot + d * 0.5, hand], 0.022, 'timberw', sides=6))
        M.add(tube([hand - d * 0.15, hand + d * 0.02], 0.026, 'dark', sides=6))
    M.add(xform(cyl(0.08, 0, 0.14, 12, 'galv', bevel=0.006), T(-0.4, 1.05, 0.0)))
    M.add(xform(cyl(0.083, 0.14, 0.15, 12, 'p1w'), T(-0.4, 1.05, 0.0)))
    M.add(bar((-0.3, 1.05, 0.155), (-0.05, 1.1, 0.04), 0.022, 'timber'))
    for x in (-1.0, 1.0):
        for y in (-0.8, 0.8):
            for sg in (-1, 1):
                M.add(blob((x + sg * 0.24, y, 0.0), (0.1, 0.08, 0.035), 'sandw', n=7, rings=2, seed=int(x * 3 + y * 5 + sg) + 70, jitter=0.3, flat_bottom=0.0))
    _front(M)
    _slide(M, L / 2 + 0.02, zg + D + 0.06)
    return M


def boardwalk():
    """A dune boardwalk crossing the beach path: a deck of grey-weathered boards on two stringers at
    the gap, on round piles either side of the kid's line, with steps down at both ends, a timber top
    rail and a rope mid-rail along each side, sand drifted round the piles. Solid: the crossing up to
    its rails (slide under, or double jump over)."""
    M = Model('Boardwalk', ppm=70, grime=dict(rust=0.0, chips=0.0, streaks=0.4, dirt_h=0.35, ground=0.5, mottle=0.1))
    hx = 0.8
    yd = 1.2
    zt = GAP + 0.13
    rail = zt + 0.9
    for x in (-hx + 0.12, hx - 0.12):
        M.add(wood_box((x - 0.04, -yd - 0.1, GAP), (x + 0.04, yd + 0.1, GAP + 0.09), band=3, along=1))
    nb = 18
    for i in range(nb):
        y0 = -yd - 0.1 + (2 * yd + 0.2) * i / nb
        M.add(wood_box((-hx, y0 + 0.006, GAP + 0.09), (hx, y0 + (2 * yd + 0.2) / nb - 0.006, zt), band=(i * 3) % 4, along=0, r=0.006))
    for x in (-hx + 0.06, hx - 0.06):
        for y in (-yd + 0.05, 0.0, yd - 0.05):
            if y == 0.0:
                M.add(xform(cyl(0.055, zt, rail + 0.04, 10, 'timberw', bevel=0.01), T(x, y, 0.0)))
            else:
                M.add(xform(cyl(0.075, -0.3, rail + 0.04, 10, 'timberw', bevel=0.012), T(x, y, 0.0)))
        M.add(wood_box((x - 0.05, -yd - 0.05, rail - 0.02), (x + 0.05, yd + 0.05, rail + 0.06), band=0, along=1))
        M.add(tube([(x, -yd + 0.05, zt + 0.42), (x, -yd / 2, zt + 0.38), (x, 0.0, zt + 0.42), (x, yd / 2, zt + 0.38), (x, yd - 0.05, zt + 0.42)], 0.016, 'tex', sides=6, uvtile=('rope', 0.4)))
    # steps down at both ends, outside the lane
    for s in (-1, 1):
        for k in range(3):
            z1 = zt - (k + 1) * (zt / 4)
            y0 = s * (yd + 0.1 + 0.15 * k); y1 = s * (yd + 0.1 + 0.15 * (k + 1))
            M.add(wood_box((-hx + 0.05, min(y0, y1), z1 - 0.06), (hx - 0.05, max(y0, y1), z1), band=k, along=0))
            for x in (-hx + 0.1, hx - 0.1):
                M.add(cbox((x - 0.03, min(y0, y1) + 0.03, -0.1), (x + 0.03, min(y0, y1) + 0.09, z1 - 0.06), 0.005, 'timber'))
    for y in (-yd + 0.05, yd - 0.05):
        for x in (-hx + 0.06, hx - 0.06):
            M.add(blob((x, y, 0.0), (0.24, 0.2, 0.08), 'sandw', n=8, rings=2, seed=int(y * 10 + x * 7) + 90, jitter=0.3, flat_bottom=0.0))
    for k, (x, y) in enumerate(((0.95, -1.1), (-1.0, 0.95), (1.0, 1.2))):
        for j in range(4):
            a = j * 0.6
            M.add(tube([(x, y, 0.0), (x + 0.12 * math.cos(a), y + 0.08 * math.sin(a), 0.3 + 0.05 * j)], 0.012, 'grass', sides=3))
    _front(M)
    _slide(M, hx, rail + 0.06)
    return M


def rescue_board_stand():
    """A lifeguard's rescue board on its stand by the path: a long yellow board with a red nose and
    rails of black grab handles, on two padded A-frames whose legs stand either side of the kid's
    line, a red rescue tube coiled on it and a red-and-yellow flag. Solid: the board (hop on it, or
    slide under)."""
    M = Model('RescueBoardStand', p1=(0.99, 0.79, 0.15), p2=(0.86, 0.20, 0.17), ppm=100, grime=dict(rust=0.05, chips=0.2, streaks=0.3, dirt_h=0.3, ground=0.4))
    L = 3.0
    for x in (-0.95, 0.95):
        trestle(M, x, 0.58, GAP + 0.06, splay=0.26, barh=0.06, mat='aluw', steel=True)
        M.add(rbox((x - 0.06, -0.32, GAP + 0.06), (x + 0.06, 0.32, GAP + 0.095), (0.015, 0.015, 0.015), 'foam', seg=(1, 1, 1)))
    zb = GAP + 0.095
    thick = 0.11
    bm = _surfboard(L, 0.3, thick, 'p1', stripe=(0.86, 1.0, 'p2'))
    xform(bm, T(0.0, 0.0, zb + thick * 0.5))
    M.add(bm)
    for s in (-1, 1):
        for x in np.linspace(-1.1, 1.0, 6):
            u = (x + L / 2) / L
            w = 0.3 * max(0.04, math.sin(PI * (0.14 + 0.85 * u))) ** 0.75
            M.add(tube([(x - 0.07, s * (w - 0.01), zb + 0.06), (x - 0.04, s * (w + 0.03), zb + 0.08), (x + 0.04, s * (w + 0.03), zb + 0.08), (x + 0.07, s * (w - 0.01), zb + 0.06)], 0.008, 'dark', sides=4))
    # the rescue tube: a long soft float with its strap coiled beside it
    tube_pts = [(-0.9, -0.05, zb + thick + 0.05), (-0.2, -0.08, zb + thick + 0.05), (0.4, -0.02, zb + thick + 0.05)]
    M.add(tube(tube_pts, 0.055, 'p2', sides=10))
    for x in (-0.95, 0.45):
        M.add(xform(cyl(0.056, -0.015, 0.015, 10, 'white'), T(x, -0.05, zb + thick + 0.05) @ R(PI / 2, 'Y')))
    coil = [Vector((0.75 + 0.1 * math.cos(a), 0.06 + 0.07 * math.sin(a), zb + thick + 0.012 + 0.004 * a)) for a in np.linspace(0, 4 * PI, 24)]
    M.add(tube(coil, 0.008, 'p1d', sides=4))
    # the flag on the far stand
    M.add(tube([(0.95, 0.62, 0.0), (0.95, 0.62, 2.6)], 0.02, 'aluw', sides=6))
    M.add(box((0.97, 0.615, 2.325), (1.57, 0.625, 2.55), 'p2'))
    M.add(box((0.97, 0.615, 2.1), (1.57, 0.625, 2.325), 'p1'))
    for x in (-0.95, 0.95):
        for y in (-0.58, 0.58):
            for s in (-1, 1):
                M.add(blob((x + s * 0.26, y, 0.0), (0.1, 0.08, 0.035), 'sandw', n=7, rings=2, seed=int(x * 3 + y * 5 + s) + 120, jitter=0.3, flat_bottom=0.0))
    _front(M)
    _slide(M, L / 2, zb + thick + 0.01)
    return M


# ================================================================ BUILDING SITE
def scaffold_gantry():
    """Scaffold over the footpath on a building job, wrapped in debris netting from its lowest lift up:
    that lift's boards are low enough to stop a standing kid, and the scaffold rises two more lifts,
    far too tall to jump: slide under the boards between the standards. Tubes, the open bottom lift
    and toe boards show under the netting; an orange banner hangs on the front, a gin wheel on top."""
    M = Model('ScaffoldGantry', p1=(0.72, 0.74, 0.75), p2=(0.42, 0.62, 0.62), ppm=40, grime=dict(rust=0.25, streaks=0.5, dirt_h=0.4))
    hx, fy = 1.3, 0.75
    top = 4.05
    xs = (-hx + 0.04, 0.0, hx - 0.04)
    r = 0.03
    for x in xs:
        for y in (-fy, fy):
            M.add(tube([(x, y, 0.06), (x, y, top + 1.05)], 0.036, 'p1', sides=6))
            M.add(cbox((x - 0.07, y - 0.07, 0.045), (x + 0.07, y + 0.07, 0.06), 0.004, 'iron'))
        M.add(wood_box((x - 0.11, -fy - 0.12, 0.0), (x + 0.11, fy + 0.12, 0.045), band=3, along=1))
        # transoms across the path under the low boards: the lowest thing over the kid
        M.add(tube([(x, -fy - 0.08, GAP + r), (x, fy + 0.08, GAP + r)], 0.028, 'p1', sides=6))
    for y in (-fy, fy):
        for z in (GAP + 2 * r + 0.012, GAP + 1.7, top - 0.08):
            M.add(tube([(-hx, y - (0.05 if y < 0 else -0.05), z), (hx, y - (0.05 if y < 0 else -0.05), z)], 0.028, 'p1', sides=6))
        for z in (top + 0.5, top + 1.0):
            M.add(tube([(-hx, y, z), (hx, y, z)], 0.026, 'p1', sides=6))
    deck = GAP + 2 * r + 0.012 + 0.03
    for k in range(6):
        y0 = -0.66 + k * 0.225
        M.add(wood_box((-hx, y0, deck), (hx, y0 + 0.22, deck + 0.038), band=k % 4, r=0.006))
    deck += 0.038
    for y in (-fy + 0.06, fy - 0.06):
        M.add(cbox((-hx, y - 0.015, deck), (hx, y + 0.015, deck + 0.15), 0.006, 'yellow'))
    # debris netting inside both faces and the ends, from the low lift up to the top lift, so the
    # standards, ledgers and rails read in front of it
    zb0, zb1 = deck + 0.02, top + 0.45
    fi = fy - 0.06
    for y in (-fi, fi):
        sh = box((-hx + 0.05, y - 0.006, zb0), (hx - 0.05, y + 0.006, zb1), 'tex')
        settile(sh, 'mesh', lambda co, f: ((co.x + hx) / (2 * hx), (co.z - zb0) / (zb1 - zb0)), mat='p2k')
        M.add(sh)
    for x in (-hx + 0.05, hx - 0.05):
        sh = box((x - 0.006, -fi, zb0), (x + 0.006, fi, zb1), 'tex')
        settile(sh, 'mesh', lambda co, f: ((co.y + fi) / (2 * fi), (co.z - zb0) / (zb1 - zb0)), mat='p2k')
        M.add(sh)
    # brick guards along the front of the low lift
    for x0, x1 in ((-hx + 0.06, -0.04), (0.04, hx - 0.06)):
        for z in np.arange(deck + 0.2, deck + 0.9, 0.12):
            M.add(bar((x0, -fy - 0.07, z), (x1, -fy - 0.07, z), 0.012, 'yellow', sides=4))
        for x in np.linspace(x0, x1, 6):
            M.add(bar((x, -fy - 0.07, deck + 0.15), (x, -fy - 0.07, deck + 0.95), 0.012, 'yellow', sides=4))
    # orange banner with a white band, tied to the front
    M.add(cbox((-0.9, -fy - 0.1, GAP + 2.2), (0.9, -fy - 0.092, GAP + 2.7), 0.004, 'orangew'))
    M.add(cbox((-0.85, -fy - 0.104, GAP + 2.37), (0.85, -fy - 0.1, GAP + 2.53), 0.003, 'white'))
    for x in (-0.86, 0.86):
        for z in (GAP + 2.25, GAP + 2.65):
            M.add(bar((x, -fy - 0.1, z), (x, -fy - 0.04, z), 0.01, 'dark'))
    # a gin wheel on a cantilevered tube at the top, its rope hanging behind
    M.add(tube([(hx - 0.04, fy, top + 0.9), (hx - 0.04, fy + 0.7, top + 0.9)], 0.026, 'p1', sides=6))
    w = wheel_bm(0.14, 0.04, n=12, hub='iron', tyre='iron', rim_r=0.6)
    xform(w, T(hx - 0.04, fy + 0.62, top + 0.72) @ R(PI / 2, 'Y')); M.add(w)
    M.add(tube([(hx + 0.0, fy + 0.62, top + 0.6), (hx + 0.0, fy + 0.62, 0.3)], 0.008, 'tex', sides=4, uvtile=('rope', 0.4)))
    M.add(tube([(hx - 0.08, fy + 0.62, top + 0.6), (hx - 0.08, fy + 0.62, 2.2)], 0.008, 'tex', sides=4, uvtile=('rope', 0.4)))
    _front(M)
    _slide(M, hx + 0.02, top + 0.2)
    return M


def beam_trestles():
    """Two primed steel beams resting on heavy steel trestles across the footpath, waiting to go up:
    the trestles' bars cross over the kid's line at the gap, their legs either side of it; timber
    packers, ratchet straps round the beams, spray marks and a red rag on the long end. Solid: the
    beams (hop onto them, or slide under)."""
    M = Model('BeamTrestles', p1=(0.66, 0.36, 0.26), p2=(0.47, 0.56, 0.62), ppm=90, grime=dict(rust=0.6, chips=0.4, streaks=0.6, dirt_h=0.3))
    zt = GAP + 0.08
    for x in (-1.25, 1.25):
        trestle(M, x, 0.62, zt, splay=0.3, barh=0.08, legw=0.06, mat='p2', steel=True)
        M.add(wood_box((x - 0.07, -0.42, zt), (x + 0.07, 0.42, zt + 0.06), band=1, along=1))
    zb = zt + 0.06
    Lh = 2.1
    for k, y in enumerate((-0.17, 0.17)):
        M.add(section_beam(-Lh + 0.08 * k, Lh + 0.08 * k, y, zb, 0.3, 0.16, 0.022, 0.012, 'p1', end_mat='yellow' if k == 0 else 'whiteg'))
    for x in (-0.6, 0.6):
        st = [(x, -0.27, zb - 0.01), (x, -0.27, zb + 0.31), (x, 0.27, zb + 0.31), (x, 0.27, zb - 0.01)]
        M.add(sweep(st, [(-0.02, -0.003), (0.02, -0.003), (0.02, 0.003), (-0.02, 0.003)], 'yellow', up=(1, 0, 0), caps=True))
        M.add(cbox((x - 0.04, -0.3, zb + 0.12), (x + 0.04, -0.27, zb + 0.22), 0.006, 'iron'))
    # a red rag tied on the long end
    e = Lh + 0.08
    rag = extrude_poly([(0, 0), (0.05, -0.02), (0.08, -0.18), (0.02, -0.24), (-0.04, -0.15)], 0.01, 'red')
    xform(rag, T(e - 0.05, 0.17 - 0.09, zb + 0.2) @ R(PI / 2, 'X') @ R(0.2, 'Z')); M.add(fix_normals(rag))
    M.feat('front', 'rect', a0=-1.5, a1=-1.2, b0=zb + 0.05, b1=zb + 0.25, col=(1.0, 0.95, 0.9), alpha=0.5)
    M.feat('front', 'rect', a0=0.9, a1=1.05, b0=zb + 0.08, b1=zb + 0.22, col=(1.0, 0.95, 0.9), alpha=0.5)
    _front(M)
    _slide(M, Lh + 0.08, zb + 0.31)
    return M


def pipe_rack():
    """A pipe rack on the site's edge, across the footpath: two steel end frames with cantilever arms
    in three tiers, the lowest at the gap, holding orange ducting, grey steel tube and black plastic
    pipe; hazard bands on the posts, a red flag on the longest pipe. Its end frames are open under
    the lowest arms. Solid: the rack up to its top bar."""
    M = Model('PipeRack', p1=(0.30, 0.45, 0.62), ppm=70, grime=dict(rust=0.35, chips=0.3, streaks=0.5, dirt_h=0.3))
    fx, py = 1.45, 0.62
    tiers = (GAP, GAP + 0.42, GAP + 0.84)
    top = 2.04
    for x in (-fx, fx):
        for y in (-py, py):
            M.add(cbox((x - 0.04, y - 0.04, 0.03), (x + 0.04, y + 0.04, top), 0.006, 'p1'))
            M.add(cbox((x - 0.1, y - 0.1, 0.0), (x + 0.1, y + 0.1, 0.03), 0.005, 'iron'))
            hz = box((x - 0.042, y - 0.042, 0.25), (x + 0.042, y + 0.042, 0.6), 'tex')
            settile(hz, 'hazard', lambda co, f, x=x, y=y: (0.5 + (co.x - x + co.y - y) * 2.5, (co.z - 0.25) / 0.35), mat='tex')
            M.add(hz)
        for z in tiers:
            M.add(cbox((x - 0.035, -py, z), (x + 0.035, py, z + 0.07), 0.005, 'p1'))
        M.add(cbox((x - 0.04, -py - 0.04, top - 0.07), (x + 0.04, py + 0.04, top), 0.006, 'p1'))
    for y in (-py, py):
        M.add(cbox((-fx, y - 0.03, top - 0.06), (fx, y + 0.03, top), 0.005, 'p1'))
        M.add(bar((-fx, y, 0.12), (fx, y, top - 0.08), 0.045, 'p1d'))
        M.add(cbox((-fx, y - 0.03, 0.08), (fx, y + 0.03, 0.14), 0.005, 'p1'))
    L = 1.95
    # tier 1: big orange ducting
    for i, y in enumerate((-0.38, 0.0, 0.38)):
        p = pipe_like(0.13, 0.115, 2 * L - 0.1 * i, 'pipeo')
        xform(p, T(0.05 * i, y, tiers[0] + 0.07 + 0.13) @ R(PI / 2, 'Y')); M.add(p)
    # tier 2: grey steel tube
    for i, y in enumerate(np.linspace(-0.45, 0.45, 6)):
        p = pipe_like(0.055, 0.045, 2 * L - 0.15 * (i % 3), 'pipeg')
        xform(p, T(-0.06 * (i % 2), y, tiers[1] + 0.07 + 0.055) @ R(PI / 2, 'Y')); M.add(p)
    # tier 3: black plastic pipe
    for i, y in enumerate((-0.42, -0.14, 0.14, 0.42)):
        p = pipe_like(0.09, 0.078, 2 * L + 0.1 * (i % 2), 'pipeb')
        xform(p, T(0.04 * i, y, tiers[2] + 0.07 + 0.09) @ R(PI / 2, 'Y')); M.add(p)
    rag = extrude_poly([(0, 0), (0.05, -0.02), (0.08, -0.22), (0.02, -0.28), (-0.04, -0.18)], 0.01, 'red')
    xform(rag, T(L + 0.1, 0.0, tiers[2] + 0.12) @ R(PI / 2, 'X')); M.add(fix_normals(rag))
    _front(M)
    _slide(M, L + 0.1, top)
    return M


def pipe_like(ro, ri, length, mat, n=14):
    """A hollow pipe along local Z, centred."""
    h = length / 2
    prof = [(ri, -h), (ro, -h), (ro, h), (ri, h), (ri, -h)]
    bm, _ = lathe(prof, n, mat, phase=0.5, sm=0)
    return bm


def site_barrier():
    """A manual barrier at the site's gate, across the footpath: a hazard-striped arm on a pivot post
    with a counterweight box, resting in a cradle post at the kerb, both posts in orange-and-grey
    block feet, an amber beacon and a round no-entry sign on the pivot post. The arm is the solid:
    duck under it (or hop it)."""
    M = Model('SiteBarrier', p1=(0.96, 0.76, 0.22), p2=(0.90, 0.47, 0.20), ppm=110, grime=dict(rust=0.3, chips=0.4, streaks=0.5, dirt_h=0.4))
    hw = 0.045
    yp = 1.15
    # pivot post in a block foot
    M.add(rbox((-0.42, yp - 0.2, 0.0), (0.12, yp + 0.2, 0.16), (0.03, 0.05, 0.03), 'p2', seg=(1, 1, 1)))
    M.add(cbox((-0.2, yp - 0.05, 0.16), (-0.1, yp + 0.05, 1.3), 0.01, 'galv'))
    M.add(cbox((-0.24, yp - 0.07, GAP - 0.02), (-0.06, yp + 0.07, GAP + 0.14), 0.01, 'iron'))
    M.add(xform(cyl(0.05, 0, 0.12, 10, 'galv'), T(-0.06, yp, GAP + 0.06) @ R(PI / 2, 'Y')))
    M.add(xform(cyl(0.07, 0, 0.1, 12, 'amber', bevel=0.02), T(-0.15, yp, 1.3)))
    M.add(xform(cyl(0.075, 0, 0.02, 12, 'dark'), T(-0.15, yp, 1.3)))
    disc_sign(M, Vector((-0.15, yp - 0.07, 1.02)), 1, 0.17, 'red')
    M.add(cbox((-0.26, yp - 0.1, 0.995), (-0.04, yp - 0.094, 1.045), 0.003, 'white'))
    # the arm across the path, hazard striped, and its counterweight behind the pivot
    y_tip = -1.6
    arm = box((-hw, y_tip, GAP), (hw, yp + 0.05, GAP + 0.09), 'tex')
    arm_len = yp + 0.05 - y_tip
    settile(arm, 'hazard', lambda co, f: ((co.y - y_tip) / arm_len, (co.z - GAP) / 0.09 if abs(f.normal.x) > 0.5 else (co.x + hw) / (2 * hw)), mat='tex')
    M.add(arm)
    M.add(cbox((-hw - 0.004, y_tip - 0.04, GAP - 0.004), (hw + 0.004, y_tip + 0.02, GAP + 0.094), 0.008, 'rubber'))
    M.add(cbox((-0.05, yp + 0.05, GAP + 0.01), (0.05, yp + 0.4, GAP + 0.08), 0.008, 'galv'))
    M.add(cbox((-0.08, yp + 0.25, GAP - 0.1), (0.08, yp + 0.5, GAP + 0.12), 0.015, 'p1'))
    M.add(cbox((-0.082, yp + 0.3, GAP - 0.02), (0.082, yp + 0.45, GAP + 0.02), 0.004, 'dark'))
    # cradle post at the kerb
    yr = -1.42
    M.add(rbox((-0.26, yr - 0.16, 0.0), (0.26, yr + 0.16, 0.14), (0.03, 0.05, 0.03), 'p2', seg=(1, 1, 1)))
    M.add(cbox((-0.035, yr - 0.035, 0.14), (0.035, yr + 0.035, GAP - 0.03), 0.006, 'galv'))
    M.add(cbox((-0.08, yr - 0.035, GAP - 0.04), (0.08, yr + 0.035, GAP - 0.005), 0.006, 'galv'))
    for s in (-1, 1):
        M.add(cbox((s * 0.065 - 0.012, yr - 0.035, GAP - 0.02), (s * 0.065 + 0.012, yr + 0.035, GAP + 0.07), 0.004, 'galv'))
    hz = box((-0.037, yr - 0.037, 0.3), (0.037, yr + 0.037, 0.65), 'tex')
    settile(hz, 'hazard', lambda co, f: (0.5 + (co.x + co.y - yr) * 2.5, (co.z - 0.3) / 0.35), mat='tex')
    M.add(hz)
    _front(M)
    _slide(M, 0.06, GAP + 0.09)
    return M


# ================================================================ PARK
def fallen_trunk():
    """A tree come down across the park path in a storm, sawn off by the park keepers either side of
    the path: the trunk lies on two boulders at the path's edges, its sawn end (rings and checks)
    to the road, splintered at the back, mossy, with two sawn branch stubs and a living twig still in
    leaf; rounds of it stacked behind. Round, so nothing rests on top: slide under, or double jump
    over (a single jump can't clear it)."""
    M = Model('FallenTrunk', ppm=70, grime=dict(rust=0.0, chips=0.0, streaks=0.2, mottle=0.12, dirt_h=0.3))
    r = 0.35
    cz = GAP + r
    yf, yb = -1.6, 1.58
    tr = limb([(0.0, yf, cz), (0.01, 0.0, cz + 0.01), (0.0, yb, cz)], r, r * 0.94, 'oakbark', sides=16, tile=('bark', 1.0))
    ring_end(tr, (0, -1, 0), (0.0, yf, cz), r)
    M.add(tr)
    # splinters at the broken back end
    rng = np.random.default_rng(3)
    for k in range(7):
        a = 2 * PI * k / 7 + 0.3
        p0 = Vector((r * 0.6 * math.cos(a), yb - 0.02, cz + r * 0.6 * math.sin(a)))
        M.add(tube([p0, p0 + Vector((0.02 * math.cos(a), rng.uniform(0.08, 0.2), 0.02 * math.sin(a)))], 0.04, 'woodend', sides=4))
    # moss along the top, branch stubs (clear of the kid's line) and a twig in leaf
    for (y, s) in ((0.85, 0.5), (-0.95, 0.4), (0.1, 0.3)):
        M.add(blob((0.02, y, cz + r * 0.92), (r * 0.5, s, 0.05), 'moss', n=8, rings=2, seed=int(y * 10) + 5, jitter=0.25, flat_bottom=-0.6))
    for (p, q, rr) in (((0.05, 1.2, cz + r * 0.7), (0.34, 1.28, cz + r + 0.35), 0.075), ((-0.05, -0.8, cz + r * 0.65), (-0.36, -0.86, cz + r + 0.25), 0.065)):
        st = limb([p, q], rr, rr * 0.9, 'oakbark', sides=8, tile=('bark', 0.6))
        ring_end(st, (Vector(q) - Vector(p)).normalized(), q, rr)
        M.add(st)
    tw = curve([(0.0, 1.4, cz + r * 0.8), (0.12, 1.45, cz + r + 0.35), (0.25, 1.5, cz + r + 0.65)], 4)
    M.add(limb(tw, 0.035, 0.015, 'oakbark', sides=5, tile=('bark', 0.5)))
    leaves(M, (0.28, 1.5, cz + r + 0.75), (0.28, 0.2, 0.2), ('leafoak', 'leafoakl'), 7, 8, size=(0.1, 0.16))
    # the boulders it came to rest on
    for (y, sd) in ((-1.08, 1), (1.12, 2)):
        h = GAP + 0.1
        M.add(blob((0.0, y, 0.0), (0.5, 0.32, h), 'rock', n=9, rings=4, seed=sd * 13, jitter=0.12, flat_bottom=0.0))
        M.add(blob((0.3, y - 0.12, 0.0), (0.3, 0.24, h * 0.5), 'rockd', n=8, rings=3, seed=sd * 17, jitter=0.15, flat_bottom=0.0))
        for k in range(3):
            a = k * 2.1 + sd
            M.add(tube([(0.4 * math.cos(a), y + 0.3 * math.sin(a), 0.0), (0.45 * math.cos(a), y + 0.34 * math.sin(a), 0.22)], 0.012, 'grass', sides=3))
    # rounds stacked at the back of the path
    for k, (x, z) in enumerate(((1.15, 0.21), (1.6, 0.21), (1.38, 0.61))):
        lg = limb([(x, 1.08, z), (x, 1.5, z)], 0.21, 0.21, 'oakbark', sides=12, tile=('bark', 0.6))
        ring_end(lg, (0, -1, 0), (x, 1.08, z), 0.21)
        M.add(lg)
    _front(M)
    M.extra.update({'slideGap': GAP, 'slideRadius': r, 'slideCentre': round(cz, 3)})
    return M


def oak_bough():
    """An old park oak behind the path whose great low bough reaches out over it and dips to the gap
    over the kid's line, held up by a squared timber prop with an iron band; ivy on the trunk.
    Solid: the low run of the bough (hop it, or slide under)."""
    return _propped_bough('OakBough', oak=True)


def net_tunnel():
    """A playground rope-net tunnel laid along the path: five green steel hoops in concrete footings
    either side of the kid's line, rope strung along them and round between them, on a rubber
    safety mat. Kids crawl through it; a sliding kid goes straight through. Solid: its crown."""
    M = Model('NetTunnel', p1=(0.30, 0.62, 0.38), ppm=90, grime=dict(rust=0.05, chips=0.2, streaks=0.3, dirt_h=0.3))
    hy, hz = 0.72, GAP + 0.06
    xs = np.linspace(-1.0, 1.0, 5)
    na = 13

    def arch(x, rr=0.0):
        return [Vector((x, -(hy + rr) * math.cos(PI * k / (na - 1)), max(0.0, (hz + rr) * math.sin(PI * k / (na - 1))))) for k in range(na)]
    for x in xs:
        M.add(tube(arch(x), 0.032, 'p1', sides=8))
        for y in (-hy, hy):
            M.add(xform(cyl(0.07, -0.05, 0.03, 10, 'conc'), T(x, y, 0.0)))
    # ropes along the tunnel at angles round the arch, and rings of rope between the hoops
    for k in range(1, na - 1):
        a = PI * k / (na - 1)
        y = -(hy + 0.035) * math.cos(a); z = (hz + 0.035) * math.sin(a)
        M.add(tube([(xs[0], y, z), (xs[-1], y, z)], 0.012, 'tex', sides=4, uvtile=('rope', 0.3)))
    for x in (xs[:-1] + xs[1:]) / 2:
        M.add(tube(arch(x, 0.035)[1:-1], 0.012, 'tex', sides=4, uvtile=('rope', 0.3)))
    # rope knots where they cross, as small beads on the crown
    for x in np.linspace(-1.0, 1.0, 9):
        for k in (5, 6, 7):
            a = PI * k / (na - 1)
            M.add(blob((x, -(hy + 0.035) * math.cos(a), (hz + 0.035) * math.sin(a)), (0.02, 0.02, 0.02), 'dark', n=6, rings=1, seed=k))
    mat = rbox((-1.35, -1.0, 0.0), (1.35, 1.0, 0.012), (0.08, 0.08, 0.004), 'matg', seg=(2, 2, 1))
    M.add(mat)
    _front(M)
    _slide(M, 1.04, hz + 0.05)
    return M


def play_tower():
    """A small playground tower beside the path: four timber posts either side of the kid's line, a
    deck at the gap with a balustrade of coloured panels (a porthole in the front one), a pitched
    roof on top, a climbing net down the back and bark chippings round its feet. No room to stand
    on the deck under the roof and too tall to jump: slide under the deck."""
    M = Model('PlayTower', p1=(0.36, 0.62, 0.86), p2=(0.86, 0.32, 0.28), ppm=80, grime=dict(rust=0.0, chips=0.2, streaks=0.4, dirt_h=0.35))
    h = 0.6
    zr0, ridge = 2.0, 2.55
    for x in (-h, h):
        for y in (-h, h):
            M.add(cbox((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, zr0 + 0.05), 0.01, 'timber'))
    for y in (-h, h):
        M.add(wood_box((-h - 0.05, y - 0.03, GAP), (h + 0.05, y + 0.03, GAP + 0.1), band=1, along=0))
    for x in (-h, h):
        M.add(wood_box((x - 0.03, -h - 0.05, GAP), (x + 0.03, h + 0.05, GAP + 0.1), band=2, along=1))
    for k in range(9):
        y0 = -h + 2 * h * k / 9
        M.add(wood_box((-h, y0 + 0.005, GAP + 0.1), (h, y0 + 2 * h / 9 - 0.005, GAP + 0.13), band=k % 4, along=0, r=0.005))
    deck = GAP + 0.13
    # balustrade: coloured panels front and back with a porthole, rails at the ends
    for y, mat in ((-h - 0.04, 'p1'), (h + 0.04, 'p2')):
        pts = rrect(0.5, 0.33, 0.06, 3)
        hole = [(0.2 * math.cos(2 * PI * i / 16), 0.2 * math.sin(2 * PI * i / 16)) for i in range(16)]
        pnl = extrude_poly(pts, 0.025, mat)
        xform(pnl, T(0.0, y - 0.0125, deck + 0.4) @ R(PI / 2, 'X'))
        M.add(fix_normals(pnl))
        if y < 0:
            M.add(xform(tube([(0.2 * math.cos(2 * PI * i / 16), 0.0, 0.2 * math.sin(2 * PI * i / 16)) for i in range(16)], 0.025, 'p2', sides=6, closed=True, caps=False), T(0.0, y - 0.03, deck + 0.42)))
            M.add(xform(cyl(0.19, 0, 0.004, 16, 'dark'), T(0.0, y - 0.03, deck + 0.42) @ R(PI / 2, 'X')))
    for x in (-h, h):
        for z in (deck + 0.35, deck + 0.75):
            M.add(cbox((x - 0.025, -h, z - 0.025), (x + 0.025, h, z + 0.025), 0.008, 'timberw'))
    # pitched roof, ridge along X
    for s in (-1, 1):
        pts = [(-h - 0.12, s * (h + 0.15), zr0), (h + 0.12, s * (h + 0.15), zr0), (h + 0.12, 0.0, ridge), (-h - 0.12, 0.0, ridge)]
        rf = loft([[Vector(p) for p in pts], [Vector(p) + Vector((0, 0, 0.03)) for p in pts]], 'p2', closed_bottom=True, closed_top=True)
        M.add(fix_normals(rf))
    for x in (-h - 0.02, h + 0.02):
        gb = extrude_poly([(-h - 0.05, zr0), (h + 0.05, zr0), (0.0, ridge - 0.02)], 0.03, 'timber')
        xform(gb, T(x - 0.015, 0, 0) @ basis((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)))
        M.add(fix_normals(gb))
    M.add(tube([(-h - 0.12, 0.0, ridge + 0.02), (h + 0.12, 0.0, ridge + 0.02)], 0.03, 'p1', sides=6))
    # climbing net down the back, from the deck to the ground behind the path
    for i in range(6):
        x = -h + 0.1 + (2 * h - 0.2) * i / 5
        M.add(tube([(x, h + 0.05, deck), (x, h + 0.95, 0.03)], 0.012, 'tex', sides=4, uvtile=('rope', 0.3)))
    for j in range(1, 5):
        f = j / 5
        M.add(tube([(-h + 0.1, h + 0.05 + 0.9 * f, deck * (1 - f)), (h - 0.1, h + 0.05 + 0.9 * f, deck * (1 - f))], 0.012, 'tex', sides=4, uvtile=('rope', 0.3)))
    M.add(tube([(-h + 0.05, h + 0.95, 0.03), (h - 0.05, h + 0.95, 0.03)], 0.03, 'timberw', sides=6))
    M.add(rbox((-1.0, -1.0, 0.0), (1.0, 1.4, 0.015), (0.2, 0.2, 0.005), 'barkchip', seg=(2, 2, 1)))
    M.feat('top', 'spatter', a0=-1.0, a1=1.0, b0=-1.0, b1=1.4, n=500, r=(0.006, 0.02), col=(0.7, 0.55, 0.42), alpha=0.6)
    _front(M)
    _slide(M, h + 0.06, ridge + 0.05)
    return M


BARRIER_MODELS = [plank_trestles, boom_barrier, access_platform, apple_bough,
                  stall_awning, roll_shutter, delivery_conveyor,
                  surf_rack, boat_trestles, boardwalk, rescue_board_stand,
                  scaffold_gantry, beam_trestles, pipe_rack, site_barrier,
                  fallen_trunk, oak_bough, net_tunnel, play_tower]
