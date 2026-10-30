# Beach models for kit_leisure.py: LifeguardTower, Parasol, BeachTowel, CoolBox, SandCastle,
# BucketSpade. Metres, Z up, front faces -Y, origin at the base centre on the ground.
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_leisure_geo import *

SAND_DIRT = (0.86, 0.77, 0.62)


def wood_member(M, p0, p1, w, h, rng, m='wood', group='', plain=False, caps=True, up=None, span=1.4):
    bm = member(p0, p1, w, h, m, up=up, plain=plain, caps=caps)
    tile_natural(bm, 'grain', rng, span)
    return M.add(bm, group)


def flag_sheet(x0, x1, z0, z1, nu, wave, mfn, thick=0.004, droop=0.0):
    """A thin double-sided cloth in the x-z plane, rippling in y, hoisted at x0."""
    def fn(s, t):
        x = x0 + (x1 - x0) * s
        y = wave * math.sin(s * PI * 2.2 + 0.4) * s ** 0.8
        z = z0 + (z1 - z0) * t - droop * s * s
        return (x, y, z)
    a = grid(nu, 2, fn, None, fmat=mfn)
    b = copy(a); flip(b)
    xform(b, T(0, thick, 0))
    return join(a, b)


# ---------------------------------------------------------------- LifeguardTower
def lifeguard(rng):
    M = Model('LifeguardTower', pal={'paint': (0.95, 0.94, 0.90), 'accent': (0.83, 0.34, 0.28),
                                     'wood': (0.80, 0.66, 0.50), 'conc': (0.84, 0.80, 0.72)},
              dirt=SAND_DIRT, dirt_h=0.5, dirt_a=0.5, chips=0.5, chip=(0.72, 0.60, 0.47), streaks=0.7)
    M.parts = {1: 'paint', 2: 'accent'}
    D, DT = 2.56, 2.68           # deck underside, deck top

    def leg(sx, sy, z):
        k = 0.84 - 0.12 * z / D
        return Vector((sx * k, sy * k, z))
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(member(leg(sx, sy, -0.02), leg(sx, sy, D + 0.02), 0.15, 0.15, 'paint'))
            pad = cbox((0.30, 0.30, 0.09), 0.025, 'conc'); xform(pad, T(leg(sx, sy, 0.03))); M.add(pad)
    # braces: a ring at 1.2 m, X-braces on the sides and back
    zb = 1.2
    sides = {'front': ((-1, -1), (1, -1), (0, -1, 0)), 'back': ((-1, 1), (1, 1), (0, 1, 0)),
             'left': ((-1, -1), (-1, 1), (-1, 0, 0)), 'right': ((1, -1), (1, 1), (1, 0, 0))}
    for nm, (a, b, out) in sides.items():
        o = Vector(out) * 0.1
        M.add(member(leg(*a, zb) + o, leg(*b, zb) + o, 0.05, 0.12, 'paint', plain=True))
        if nm == 'front': continue
        o2 = Vector(out) * 0.095
        for z0, z1 in ((0.18, zb), (zb, D - 0.08)):
            M.add(member(leg(*a, z0) + o2, leg(*b, z1) + o2, 0.11, 0.04, 'paint', plain=True, up=out))
            M.add(member(leg(*b, z0) + o2, leg(*a, z1) + o2, 0.11, 0.04, 'paint', plain=True, up=out))
    # deck: boards on top, a red fascia round the edge
    deck = rpiece((-0.98, -0.98, D), (0.98, 0.98, DT), 0.02, 'wood')
    tile_planar(deck, 'slats', lambda co: ((co.x + 0.98) / 1.96, (co.y + 0.98) / 1.96))
    M.add(deck)
    zc = (D + DT) / 2
    for a, b in (((-1.03, -1.005, zc), (1.03, -1.005, zc)), ((-1.03, 1.005, zc), (1.03, 1.005, zc)),
                 ((-1.005, -1.0, zc), (-1.005, 1.0, zc)), ((1.005, -1.0, zc), (1.005, 1.0, zc))):
        M.add(member(a, b, 0.05, 0.17, 'accent'))
    # railing
    top = DT + 0.92
    posts = [(-0.95, -0.95), (0.95, -0.95), (-0.37, -0.95), (0.37, -0.95), (-0.95, 0.0), (0.95, 0.0), (-0.95, 0.95), (0.95, 0.95)]
    for x, y in posts:
        M.add(member((x, y, DT - 0.02), (x, y, top + 0.04), 0.08, 0.08, 'paintc'))
        cap = cbox((0.10, 0.10, 0.03), 0.01, 'accentc'); xform(cap, T(x, y, top + 0.055)); M.add(cap)
    runs = [((-0.95, -0.95), (-0.37, -0.95)), ((0.37, -0.95), (0.95, -0.95)), ((-0.95, -0.95), (-0.95, 0.95)),
            ((0.95, -0.95), (0.95, 0.95)), ((-0.95, 0.95), (0.95, 0.95))]
    for (x0, y0), (x1, y1) in runs:
        M.add(member((x0, y0, top - 0.03), (x1, y1, top - 0.03), 0.06, 0.07, 'paintc'))
        M.add(member((x0, y0, DT + 0.45), (x1, y1, DT + 0.45), 0.04, 0.06, 'paintc', plain=True))
    # the hut: painted boards (seams in the wear maps), a big front window with a propped shutter
    hx, hy0, hy1, hz = 0.66, -0.42, 0.80, 3.86
    M.add(rpiece((-hx, hy0, DT), (hx, hy1, hz), 0.03, 'paint'))
    wx, wz0, wz1 = 0.47, 3.13, 3.66
    for x in np.arange(-0.585, 0.66, 0.13):
        if abs(x) < wx + 0.06:
            M.line('front', (x, DT + 0.02), (x, wz0 - 0.07)); M.line('front', (x, wz1 + 0.06), (x, hz - 0.02))
        else:
            M.line('front', (x, DT + 0.02), (x, hz - 0.02))
    for y in np.arange(hy0 + 0.11, hy1, 0.13):
        M.line('side', (y, DT + 0.02), (y, hz - 0.02))
    glass = grid(1, 1, lambda s, t: (-wx + 2 * wx * s, hy0 - 0.006, wz0 + (wz1 - wz0) * t), 'tex')
    tile_keep(glass, 'window'); M.add(glass)
    fy = hy0 - 0.03
    M.add(member((-wx - 0.04, fy, wz1 + 0.035), (wx + 0.04, fy, wz1 + 0.035), 0.07, 0.07, 'paintc'))
    M.add(member((-wx - 0.07, fy - 0.02, wz0 - 0.04), (wx + 0.07, fy - 0.02, wz0 - 0.04), 0.11, 0.06, 'paintc'))
    for x in (-wx - 0.03, wx + 0.03, 0.0):
        M.add(member((x, fy, wz0 - 0.02), (x, fy, wz1 + 0.01), 0.06 if x else 0.04, 0.05, 'paintc', plain=x == 0.0))
    hinge = Vector((0, hy0 - 0.05, wz1 + 0.09))
    ang = math.radians(-112)
    sh = cbox((1.10, 0.045, 0.62), 0.015, 'accent')
    Msh = T(hinge) @ R(ang, 'X') @ T(0, -0.025, -0.31)
    xform(sh, Msh); M.add(sh)
    tip = T(hinge) @ R(ang, 'X') @ Vector((0, -0.02, -0.58))
    for x in (-0.46, 0.46):
        M.add(tube([(x, hy0 - 0.06, wz0 - 0.02), (x, tip.y + 0.02, tip.z - 0.02)], 0.014, 'woodd', sides=5))
    # side door, with a knob
    door = cbox((0.035, 0.56, 0.98), 0.012, 'accentc'); xform(door, T(hx + 0.012, 0.22, DT + 0.52)); M.add(door)
    kb, _ = lathe([(0, 0), (0.02, 0.0), (0.024, 0.02), (0, 0.03)], 8, 'brass'); xform(kb, T(hx + 0.03, 0.0, DT + 0.5) @ R(PI / 2, 'Y'))
    M.add(kb)
    # hip roof with shingles, a fascia and a white soffit
    q = 2 ** 0.5
    prof = [(0, hz - 0.02), (0.6 * q, hz + 0.01), (1.0 * q, hz + 0.01, 'S'), (1.0 * q, hz + 0.10, 'S'), (0.14 * q, 4.42), (0, 4.45)]
    cy = (hy0 + hy1) / 2
    roof, tags = lathe(prof, 4, ['paintc', 'paintc', 'accent', 'accentk', 'accentc'], phase=0.5)
    tile_lathe(roof, tags, 'shingle', (3,), 4, per_face=True)
    xform(roof, T(0, cy, 0) @ S(0.92, 0.86, 1.0)); M.add(roof)
    fin, _ = lathe([(0, 4.40), (0.07, 4.42), (0.05, 4.48), (0.075, 4.53), (0.0, 4.62)], 8, 'accentc')
    xform(fin, T(0, cy, 0)); M.add(fin)
    M.add(tube([(0, cy, 4.55), (0, cy, 5.62)], 0.022, 'paintc', sides=8))
    ball, _ = lathe([(0, 5.60), (0.035, 5.615), (0.045, 5.645), (0.035, 5.675), (0, 5.69)], 8, 'yellow')
    xform(ball, T(0, cy, 0)); M.add(ball)
    fl = flag_sheet(0.025, 0.62, 5.12, 5.48, 7, 0.05, lambda s, t: 'red' if t > 0.5 else 'yellow', droop=0.04)
    xform(fl, T(0, cy, 0)); M.add(fl)
    # the ladder up the front
    ztop = DT + 0.78

    def ly(z): return -1.52 + 0.55 * z / ztop
    for x in (-0.30, 0.30):
        M.add(member((x, ly(-0.02), -0.02), (x, ly(ztop), ztop), 0.075, 0.055, 'paintc'))
    for z in np.arange(0.34, DT - 0.1, 0.33):
        rb = tube([(-0.30, ly(z), z), (0.30, ly(z), z)], 0.024, 'wood', sides=6, caps=False)
        tile_natural(rb, 'grain', rng, 1.0); M.add(rb)
    # a ring buoy on the front rail
    tb = torus(0.19, 0.055, 16, 6, 'paintc')
    lm = lay(tb)[0]
    for f in tb.faces:
        c = f.calc_center_median(); a = math.atan2(c.y, c.x) + PI / 4
        if int(math.floor(a / (PI / 2))) % 2 == 0: f[lm] = mt('accentc')
    xform(tb, T(0.64, -1.03, DT + 0.58) @ R(PI / 2, 'X')); M.add(tb)
    hook = tube([(0.64, -0.97, top - 0.02), (0.64, -1.0, top - 0.09), (0.64, -1.03, DT + 0.75)], 0.008, 'dark', sides=4)
    M.add(hook)
    # a rescue board leaning on the right legs
    def taper(X):
        X = X.copy(); k = np.clip((X[:, 2] - 0.2) / 0.75, 0, 1)
        X[:, 0] *= 1 - 0.55 * k ** 2; X[:, 1] *= 1 - 0.3 * k
        return X
    rb = rpiece((-0.26, -0.045, -0.95), (0.26, 0.045, 0.95), (0.18, 0.03, 0.2), 'yellow', seg=(2, 1, 2),
                deform=taper, mats=lambda a, s, c: 'accentc' if abs(c[0]) < 0.05 and a == 1 else 'yellow')
    xform(rb, T(1.20, -0.30, 0.94) @ R(math.radians(-12), 'Y') @ R(math.radians(25), 'Z'))
    M.add(rb)
    M.extra = {'deck': DT}
    return M


# ---------------------------------------------------------------- Parasol
def parasol(rng):
    M = Model('Parasol', pal={'paint': (0.90, 0.42, 0.36), 'accent': (0.97, 0.93, 0.84), 'wood': (0.84, 0.70, 0.52)},
              ao_dist=0.35)
    M.parts = {1: 'paint', 2: 'accent'}
    Rr, zr, za, NP, NS = 1.05, 1.87, 2.20, 8, 4
    rings = [0.0, 0.3, 0.56, 0.8, 1.0]

    def zc(r):                                   # the canopy's crown: domed, a little steeper at the rim
        return za - (za - zr) * (r ** 1.45)

    def rib(p, r):
        a = 2 * PI * p / NP
        return Vector((Rr * r * math.cos(a), Rr * r * math.sin(a), zc(r)))

    def pt(p, i, r, dz=0.0):
        A, B = rib(p, r), rib(p + 1, r)
        P = A.lerp(B, i / NS)
        P.z -= 0.055 * math.sin(PI * i / NS) * r - dz
        return P
    top = []; bot = []
    th = 0.012
    for p in range(NP):
        m = 'paintk' if p % 2 == 0 else 'accentk'
        V = []; F = []; UV = []
        idx = {}

        def vid(i, j):
            if j == 0: i = 0
            k = (i, j)
            if k not in idx: idx[k] = len(V); V.append(pt(p, i, rings[j]))
            return idx[k]
        for j in range(len(rings) - 1):
            for i in range(NS):
                t0, t1 = 1 - rings[j], 1 - rings[j + 1]
                if j == 0:
                    F.append([vid(0, 0), vid(i, 1), vid(i + 1, 1)]); UV.append([(0.5, t0), (i / NS, t1), ((i + 1) / NS, t1)])
                else:
                    F.append([vid(i, j), vid(i, j + 1), vid(i + 1, j + 1), vid(i + 1, j)])
                    UV.append([(i / NS, t0), (i / NS, t1), ((i + 1) / NS, t1), ((i + 1) / NS, t0)])
        bm, faces = bm_from(V, F, m)
        lu = lay(bm)[2]
        for f, uv in zip(faces, UV):
            for l, c in zip(f.loops, uv): l[lu].uv = c
        tile_keep(bm, 'canvas')
        recalc(bm)
        if bm.faces[0].normal.z < 0: flip(bm)
        under = copy(bm); flip(under); xform(under, T(0, 0, -th))
        M.add(bm); M.add(under)
        # the scalloped valance under the rim edge, double-sided
        def vfn(s, t, p=p):
            P = pt(p, s * NS, 1.0)
            out = Vector((P.x, P.y, 0)).normalized() * 0.018 * (1 - t)
            hang = 0.05 + 0.07 * math.sin(PI * s)
            return (P.x + out.x, P.y + out.y, P.z - th - hang * (1 - t))
        va = grid(6, 1, vfn, m)
        lu2 = lay(va)[2]
        for f in va.faces:
            for l in f.loops:
                l[lu2].uv = (l[lu2].uv[0], 0.02 + 0.1 * l[lu2].uv[1])
        tile_keep(va, 'canvas')
        recalc(va)
        c = va.faces[0].calc_center_median()
        if va.faces[0].normal.dot(Vector((c.x, c.y, 0))) < 0: flip(va)
        vb = copy(va); flip(vb)
        for v in vb.verts:
            d = Vector((v.co.x, v.co.y, 0)).normalized(); v.co -= d * 0.004
        M.add(va); M.add(vb)
    # ribs under the canopy and stretchers to the runner
    for p in range(NP):
        path = [rib(p, r) - Vector((0, 0, th + 0.008)) for r in (0.08, 0.5, 0.97)]
        M.add(tube(path, 0.008, 'metalc', sides=4))
        a = rib(p, 0.5) - Vector((0, 0, th + 0.01))
        M.add(tube([a, (0, 0, 1.56)], 0.006, 'metalc', sides=4, caps=False))
    run, _ = lathe([(0, 1.50), (0.032, 1.50), (0.036, 1.53), (0.032, 1.60), (0, 1.60)], 10, 'metalc'); M.add(run)
    # the pole: a wooden lower half, a brass joint, a slimmer upper half, a finial on top
    lo = tube([(0, 0, -0.05), (0, 0, 1.18)], 0.027, 'wood', sides=8); tile_natural(lo, 'grain', rng, 1.5); M.add(lo)
    up = tube([(0, 0, 1.15), (0, 0, za)], 0.020, 'wood', sides=8); tile_natural(up, 'grain', rng, 1.5); M.add(up)
    jt, _ = lathe([(0, 1.10), (0.034, 1.10), (0.036, 1.14), (0.036, 1.22), (0.03, 1.25), (0, 1.25)], 10, 'brass'); M.add(jt)
    fn, _ = lathe([(0, za - 0.02), (0.05, za - 0.01), (0.05, za + 0.02), (0.03, za + 0.04), (0.035, za + 0.07), (0, za + 0.10)], 10, 'woodl')
    M.add(fn)
    mound, mt_ = lathe([(0, -0.01), (0.20, -0.01), (0.12, 0.022), (0.03, 0.04), (0, 0.04)], 12, 'sand')
    tile_planar(mound, 'sand', lambda co: (0.5 + co.x / 0.4, 0.5 + co.y / 0.4)); M.add(mound)
    M.pal['sand'] = (0.92, 0.82, 0.63)
    M.extra = {'canopyRadius': Rr, 'rimHeight': zr}
    return M


# ---------------------------------------------------------------- BeachTowel
def towel(rng):
    M = Model('BeachTowel', pal={'paint': (0.34, 0.66, 0.78), 'accent': (0.97, 0.93, 0.84)}, ao_dist=0.12, ao=0.5,
              grad=(0.95, 0.1))
    M.parts = {1: 'paint', 2: 'accent'}
    L0, x0, x1 = 1.7, -0.85, 0.85
    t, wd, rf = 0.012, 0.80, 0.032
    flap = 0.34
    # centre line in x-z: flat, a soft round fold at +x, the flap lying back on top
    stripes = [(0.10, 0.17), (0.215, 0.245)]
    total = L0 + PI * rf + flap
    marks = set()
    for a, b in stripes:
        for s in (a, b, total - a, total - b): marks.add(round(s, 4))
    ss_ = sorted(set([0.0, total] + list(np.linspace(0, L0 - 0.02, 12)) + list(marks) +
                     [L0 - 0.02 + PI * rf * k / 8 for k in range(9)] + list(np.linspace(L0 - 0.02 + PI * rf, total, 5))))

    def at(s):
        if s <= L0 - 0.02:
            return Vector((x0 + s, 0, t / 2)), Vector((1, 0, 0))
        s2 = s - (L0 - 0.02)
        if s2 <= PI * rf:
            a = -PI / 2 + s2 / rf
            c = Vector((x1 - 0.02, 0, t / 2 + rf))
            return c + Vector((rf * math.cos(a), 0, rf * math.sin(a))), Vector((-math.sin(a), 0, math.cos(a)))
        s3 = s2 - PI * rf
        z = t / 2 + 2 * rf - 0.03 * (s3 / flap) ** 1.5
        return Vector((x1 - 0.02 - s3, 0, z)), Vector((-1, 0, 0))
    path = [at(s)[0] for s in ss_]
    nrm = {}

    def up(i, p, tg):
        return Vector((-tg.z, 0, tg.x))
    n_across = 7
    sec = [(t / 2, -wd / 2 + wd * k / n_across) for k in range(n_across + 1)]
    sec += [(-t / 2, wd / 2 - wd * k / n_across) for k in range(n_across + 1)]
    bm = sweep(path, up, sec, 'paintk', caps=True)
    # stripes: part 2 bands by arc length
    lm, lr, lu = lay(bm)[:3]
    for f in bm.faces:
        s = sum(l[lu].uv[0] for l in f.loops) / len(f.loops)
        if any(a <= s <= b or total - b <= s <= total - a for a, b in stripes): f[lm] = mt('accentk')
    tile_natural(bm, 'terry', None, 2.2)
    # soft ripples where it lies on the sand
    for v in bm.verts:
        if v.co.x < x1 - 0.05 and v.co.z < 0.03:
            v.co.z += 0.004 * (math.sin(v.co.x * 9.0 + 1.0) * math.cos(v.co.y * 6.0) + 1)
        if v.co.z > 0.03:
            v.co.y *= 1.0 + 0.02 * math.sin(v.co.x * 20)
    bm.normal_update()
    M.add(bm)
    M.ground = 0.0
    return M


# ---------------------------------------------------------------- CoolBox
def coolbox(rng):
    M = Model('CoolBox', pal={'paint': (0.36, 0.58, 0.80), 'cream': (0.96, 0.95, 0.91), 'metal': (0.74, 0.76, 0.78)},
              dirt=SAND_DIRT, dirt_h=0.08, chips=0.12, chip=(0.88, 0.87, 0.86), ao_dist=0.2, streaks=0.2)
    M.parts = {1: 'paint'}
    W, Dp, zb, zl = 0.55, 0.38, 0.27, 0.36

    def taper(X):
        X = X.copy(); k = 0.965 + 0.035 * np.clip(X[:, 2] / zb, 0, 1)
        X[:, 0] *= k; X[:, 1] *= k; return X
    M.add(rpiece((-W / 2 + 0.01, -Dp / 2 + 0.01, 0.0), (W / 2 - 0.01, Dp / 2 - 0.01, zb), (0.05, 0.05, 0.03), 'paint', seg=(2, 2, 1), deform=taper))

    def dome(X):
        X = X.copy(); top = X[:, 2] > zb + 0.04
        X[top, 2] += 0.014 * (1 - (X[top, 0] / (W / 2)) ** 2) * (1 - (X[top, 1] / (Dp / 2)) ** 2)
        return X
    M.add(rpiece((-W / 2, -Dp / 2, zb - 0.004), (W / 2, Dp / 2, zl - 0.014), (0.05, 0.05, 0.03), 'cream', seg=(2, 2, 1), deform=dome))
    # swing handle from pivots on the ends, lying back over the lid
    hp = [(-W / 2 - 0.008, 0.0, 0.20), (-W / 2 - 0.018, 0.02, 0.29), (-W / 2 + 0.02, 0.07, 0.36),
          (W / 2 - 0.02, 0.07, 0.36), (W / 2 + 0.018, 0.02, 0.29), (W / 2 + 0.008, 0.0, 0.20)]
    M.add(tube(hp, 0.012, 'metalc', sides=6))
    for sx in (-1, 1):
        pv, _ = lathe([(0, 0), (0.028, 0), (0.026, 0.012), (0, 0.016)], 10, 'creamc')
        xform(pv, T(sx * (W / 2 - 0.004), 0, 0.20) @ R(sx * PI / 2, 'Y')); M.add(pv)
    # latch clip and drain plug on the front
    lc = cbox((0.08, 0.024, 0.07), 0.01, 'creamc'); xform(lc, T(0, -Dp / 2 - 0.006, zb + 0.005)); M.add(lc)
    dp, _ = lathe([(0, 0), (0.02, 0), (0.018, 0.012), (0, 0.014)], 8, 'creamc')
    xform(dp, T(0.19, -Dp / 2 + 0.004, 0.045) @ R(PI / 2, 'X')); M.add(dp)
    # feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            ft = cbox((0.06, 0.05, 0.02), 0.006, 'rubber'); xform(ft, T(sx * 0.21, sy * 0.13, 0.008)); M.add(ft)
    # a moulded panel line on the front and back
    M.line('front', (-0.21, 0.045), (0.21, 0.045), (0.21, 0.215), (-0.21, 0.215), (-0.21, 0.045))
    M.line('side', (-0.12, 0.05), (0.12, 0.05), (0.12, 0.21), (-0.12, 0.21), (-0.12, 0.05))
    return M


# ---------------------------------------------------------------- SandCastle
def lumpy(bm, amp, seed):
    for v in bm.verts:
        x, y, z = v.co
        k = math.sin(x * 61 + seed) * math.cos(y * 53 - seed * 0.7) + 0.6 * math.sin(z * 77 + x * 31 + seed * 1.3)
        v.co += Vector((math.cos(z * 41 + seed), math.sin(z * 37 - seed), 0.3)) * (amp * k)
    bm.normal_update()
    return bm


def merlons(cx, cy, z, r, n, size, m, phase=0.0):
    out = []
    for k in range(n):
        a = 2 * PI * (k + phase) / n
        b = box((-size[0] / 2, -size[1] / 2, 0), (size[0] / 2, size[1] / 2, size[2]), m)
        xform(b, T(cx + r * math.cos(a), cy + r * math.sin(a), z) @ R(a, 'Z'))
        out.append(b)
    return join(*out)


def sand_tower(cx, cy, r0, r1, z0, z1, n, m, ridges=2):
    prof = [(0, z0), (r0 + 0.012, z0, 'S')]
    for k in range(ridges + 1):
        f0 = k / (ridges + 1); f1 = (k + 1) / (ridges + 1)
        za, zb_ = z0 + (z1 - z0) * f0, z0 + (z1 - z0) * f1
        ra, rb = r0 + (r1 - r0) * f0, r0 + (r1 - r0) * f1
        prof += [(ra, za + 0.004), (rb + 0.004, zb_ - 0.006)]
    prof += [(r1, z1, 'S'), (r1 * 0.75, z1, 'S'), (r1 * 0.72, z1 - 0.012), (0, z1 - 0.012)]
    bm, tags = lathe(prof, n, m, phase=0.5)
    xform(bm, T(cx, cy, 0))
    return bm


def sandcastle(rng):
    M = Model('SandCastle', pal={'paint': (0.92, 0.80, 0.60), 'accent': (0.86, 0.32, 0.27), 'wood': (0.78, 0.64, 0.48)},
              ao_dist=0.12, grad=(0.82, 0.25))
    M.parts = {1: 'paint', 2: 'accent'}
    sand = 'paintk'
    mound, _ = lathe([(0, 0.0), (0.33, -0.005), (0.31, 0.03), (0.25, 0.065), (0.12, 0.085), (0, 0.09)], 16, sand)
    xform(mound, S(1.0, 0.78, 1.0)); lumpy(mound, 0.006, 1.0)
    pieces = [mound]
    ct = sand_tower(0.0, 0.04, 0.115, 0.088, 0.07, 0.29, 14, sand, ridges=2)
    pieces.append(ct)
    pieces.append(merlons(0.0, 0.04, 0.29 - 0.004, 0.078, 7, (0.034, 0.028, 0.038), sand))
    for sx in (-1, 1):
        st = sand_tower(sx * 0.19, 0.05, 0.078, 0.062, 0.05, 0.20, 12, sand, ridges=1)
        pieces.append(st)
        pieces.append(merlons(sx * 0.19, 0.05, 0.20 - 0.004, 0.054, 6, (0.026, 0.024, 0.03), sand, phase=0.25))
    wall = rpiece((-0.17, -0.115, 0.04), (0.17, -0.065, 0.165), 0.012, sand)
    pieces.append(wall)
    mer = []
    for k in range(7):
        x = -0.15 + k * 0.05
        mer.append(box((x - 0.014, -0.112, 0.16), (x + 0.014, -0.068, 0.192), sand))
    pieces.append(join(*mer))
    for p in pieces:
        if p is not mound: lumpy(p, 0.0025, 3.0)
        tile_box(p, 'sand', rng, span=0.4)
        M.add(p)
    tile_planar(mound, 'sand', lambda co: (0.5 + co.x / 0.66, 0.5 + co.y / 0.52))
    # a doorway: a dark arch pressed into the wall
    def arch(s, t):
        x = -0.035 + 0.07 * s
        zt = 0.05 + 0.065 + 0.03 * math.sin(PI * s)
        return (x, -0.117, 0.05 + (zt - 0.05) * t)
    door = grid(6, 1, arch, (0, 'mud', 'white')); M.pal['mud'] = (0.62, 0.50, 0.38); M.add(door)
    # windows on the central tower
    for a in (-0.35, 0.35):
        wv = grid(1, 1, lambda s, t, a=a: (0.104 * math.sin(a) + 0.02 * (s - 0.5) * math.cos(a),
                                           0.04 - 0.104 * math.cos(a) + 0.02 * (s - 0.5) * math.sin(a), 0.19 + 0.04 * t), (0, 'mud', 'white'))
        M.add(wv)
    # the flag
    M.add(tube([(0.0, 0.04, 0.27), (0.0, 0.04, 0.47)], 0.0045, 'woodl', sides=5))
    fl = flag_sheet(0.004, 0.10, 0.40, 0.465, 4, 0.012, lambda s, t: 'accentc', thick=0.002)
    for v in fl.verts:
        k = (v.co.x - 0.004) / 0.096
        mid = 0.4325
        v.co.z = mid + (v.co.z - mid) * (1 - k * 0.92)
    xform(fl, T(0, 0.04, 0))
    M.add(fl)
    # two little shells
    for (x, y, a, c) in ((0.24, -0.13, 0.4, (0.98, 0.86, 0.80)), (-0.22, -0.16, -0.6, (0.97, 0.95, 0.90))):
        sh, _ = lathe([(0, 0), (0.026, 0.0), (0.022, 0.008), (0, 0.012)], 7, 'own0')
        set_vc(sh, lambda co, c=c: s2l(c))
        xform(sh, T(x, y, 0.035) @ R(a, 'Z') @ R(0.3, 'X') @ S(1.0, 0.8, 1.0)); M.add(sh)
    M.at('Flag', (0.0, 0.04, 0.47))
    return M


# ---------------------------------------------------------------- BucketSpade
def bucketspade(rng):
    M = Model('BucketSpade', pal={'paint': (0.98, 0.78, 0.30), 'accent': (0.34, 0.66, 0.74), 'sand': (0.92, 0.82, 0.62)},
              ao_dist=0.12, grad=(0.85, 0.2))
    M.parts = {1: 'paint', 2: 'accent'}
    bx, by = -0.06, 0.03
    prof = [(0, 0.0), (0.085, 0.0), (0.092, 0.006, 'S'), (0.112, 0.175, 'S'), (0.121, 0.18), (0.121, 0.198, 'S'),
            (0.108, 0.198, 'S'), (0.101, 0.185), (0.082, 0.02), (0, 0.02)]
    bk, tags = lathe(prof, 16, ['paintk', 'paintk', 'paintk', 'paintk', 'paintk', 'paintk', 'paintk', 'paintk', 'paintk'])
    tile_lathe(bk, tags, 'bucket', (2,), 16)
    xform(bk, T(bx, by, 0)); M.add(bk)
    sd, _ = lathe([(0.0, 0.13), (0.099, 0.128), (0.07, 0.14), (0.02, 0.152), (0, 0.155)], 14, 'sand')
    tile_planar(sd, 'sand', lambda co: (0.5 + co.x / 0.2, 0.5 + co.y / 0.2)); lumpy(sd, 0.003, 2.0)
    xform(sd, T(bx, by, 0)); M.add(sd)
    # wire handle resting back over the rim
    arc = []
    for k in range(9):
        a = PI * k / 8
        arc.append(Vector((0.118 * math.cos(a), 0, 0.118 * math.sin(a))))
    Mh = T(bx, by, 0.165) @ R(math.radians(62), 'X')
    M.add(tube([Mh @ p for p in arc], 0.0055, 'metalc', sides=5))
    for sx in (-1, 1):
        lg = cbox((0.012, 0.02, 0.024), 0.004, 'paintc'); xform(lg, T(bx + sx * 0.115, by, 0.165)); M.add(lg)
    # the spade, stuck in the sand and leaning out
    Ms = T(0.17, -0.06, 0.0) @ R(math.radians(-24), 'Y') @ R(math.radians(8), 'X')

    def blade(s, t):
        w = 0.055 * (1 - 0.35 * (1 - t) ** 2)
        x = (s - 0.5) * 2 * w
        z = -0.04 + 0.13 * t - 0.012 * (1 - t) * (1 - abs(s - 0.5) * 2)
        y = 0.012 * ((s - 0.5) * 2) ** 2
        return (x, y, z)
    b1 = grid(4, 3, blade, 'accentc'); b2 = copy(b1); flip(b2); xform(b2, T(0, 0.006, 0))
    for b in (b1, b2):
        xform(b, Ms); M.add(b)
    M.add(tube([Ms @ Vector((0, 0.004, 0.08)), Ms @ Vector((0, 0.004, 0.40))], 0.011, 'accentc', sides=6))
    M.add(tube([Ms @ Vector((-0.045, 0.004, 0.41)), Ms @ Vector((0.045, 0.004, 0.41))], 0.013, 'accentc', sides=6))
    pile, _ = lathe([(0, -0.01), (0.09, -0.01), (0.05, 0.02), (0.0, 0.03)], 10, 'sand')
    tile_planar(pile, 'sand', lambda co: (0.5 + co.x / 0.2, 0.5 + co.y / 0.2))
    xform(pile, T(0.17, -0.06, 0)); M.add(pile)
    return M
