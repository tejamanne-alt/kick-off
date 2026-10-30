# Street kit models, part 2: planters, bench, bin, vending machines, post box and the bicycle.
import math
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from kit_street_geo import (PI, lathe, sweep, tube, cbox, rpiece, prism, ball, boolean_diff, xform, T, R, S,
                            frame, setmat, faces_facing, uv_planar, uv_long, uv_cyl, grime_cyl, lay, bm_from,
                            fix_normals, circle_sec, new_bm, merge, join)
from kit_street_build import Model
from kit_street_m1 import front_plate, decal_faces


# ---------------------------------------------------------------- shared helpers
def ell_sec(ru, rv, n=8):
    return [(ru * math.cos(2 * PI * (k + 0.5) / n), rv * math.sin(2 * PI * (k + 0.5) / n)) for k in range(n)]


def leaf_ball(r, at, mat='leaf', squash=0.62, seed=0, n=7, rings=4, lump=0.1):
    bm = ball(r, mat, n=n, rings=rings, squash=squash, lump=lump, seed=seed)
    uv_planar(bm, bm.faces, 'leaf', lambda co: (0.5 + co.x / (2.2 * r), 0.5 + (co.y + co.z * 0.6) / (2.2 * r)))
    return xform(bm, T(at))


def flower(at, mat, r=0.04, seed=0, tilt=(0.0, 0.0)):
    """A domed flower head with a warm centre."""
    prof = [(0.0, -0.3 * r), (0.85 * r, -0.08 * r), (r, 0.08 * r), (0.42 * r, 0.24 * r), (0.0, 0.26 * r)]
    bm, _ = lathe(prof, 5, [mat, mat, mat, 'flowerc'], phase=(seed * 0.37) % 1.0)
    return xform(bm, T(at) @ R(tilt[0], 'X') @ R(tilt[1], 'Y'))


def inset_top(bm, thickness, depth, inner_mat=None, ring_mat=None, cos=0.999):
    """Hollow the flat top: a rim ring (thickness) and a floor sunk by depth (with near-vertical walls)."""
    top = [f for f in bm.faces if f.normal.z > cos]
    r1 = bmesh.ops.inset_region(bm, faces=top, thickness=thickness, depth=0.0, use_even_offset=True)
    r2 = bmesh.ops.inset_region(bm, faces=top, thickness=0.002, depth=0.0, use_even_offset=True)
    verts = {v for f in top for v in f.verts}
    for v in verts: v.co.z -= depth
    if ring_mat: setmat(bm, ring_mat, r1['faces'])
    if inner_mat: setmat(bm, inner_mat, top + r2['faces'])
    bm.normal_update()
    return top, r2['faces']


def torus(c, R0, sec, n, mats, axis='Y'):
    """A ring of the closed section sec = [(radial u, axial v)] about centre c; mats per section edge.
    The ring lies in the XZ plane (axis Y)."""
    V = []
    m = len(sec)
    for k in range(n):
        th = 2 * PI * k / n
        e = Vector((math.cos(th), 0, math.sin(th))); ax = Vector((0, 1, 0))
        for (u, v) in sec:
            V.append(Vector(c) + e * (R0 + u) + ax * v)
    F = []; M = []
    for k in range(n):
        k2 = (k + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            F.append([k * m + j, k * m + j2, k2 * m + j2, k2 * m + j]); M.append(mats[j])
    bm, _ = bm_from(V, F, M)
    return fix_normals(bm)


# ---------------------------------------------------------------- planters
def planter(name, L, seed):
    m = Model(name, paint=(0.95, 0.56, 0.62), paint2=(0.98, 0.83, 0.40),
              note='Concrete planter with flowers: part 1 = the pink flowers, part 2 = the yellow ones.')
    rng = np.random.default_rng(seed)
    D, H = 0.6, 0.64
    xl = tuple(np.arange(-L / 2 + 0.25, L / 2 - 0.1, 0.25))

    def taper(X):
        X = X.copy(); k = 1 - 0.04 * (1 - np.clip((X[:, 2] - 0.07) / (H - 0.07), 0, 1))
        X[:, 0] *= k; X[:, 1] *= k
        return X
    body = rpiece((-L / 2, -D / 2, 0.07), (L / 2, D / 2, H), (0.05, 0.05, 0.04), 'concrete', extra=(xl, (0.0,), (0.25, 0.48)),
                  skip=((2, -1),), deform=taper)
    top, walls = inset_top(body, 0.07, 0.07, inner_mat='concrete_d')
    setmat(body, 'soil', top)
    uv_planar(body, top, 'soil', lambda co: ((co.x + L / 2) / L, (co.y + D / 2) / D))
    m.add(body)
    m.add(rpiece((-L / 2 + 0.05, -D / 2 + 0.05, -0.0045), (L / 2 - 0.05, D / 2 - 0.05, 0.08), (0.015, 0.015, 0.015), 'concrete_d', skip=((2, -1),)))
    # foliage mounds along the trough, flowers scattered over their tops
    nm = 4 if L < 1.5 else 7
    zs = H - 0.07
    greens = ['leaf', 'leaf_d', 'leaf_l']
    flowers = []
    for i in range(nm):
        x = -L / 2 + 0.16 + (L - 0.32) * i / (nm - 1)
        y = (0.06 if i % 2 else -0.07) + rng.uniform(-0.03, 0.03)
        r = rng.uniform(0.15, 0.19)
        cz = zs + 0.06
        m.add(leaf_ball(r, (x, y, cz), greens[i % 3], squash=0.62, seed=seed * 10 + i))
        for k in range(3 if L > 1.5 else 5):
            a = rng.uniform(-PI * 0.95, PI * 0.15); d = rng.uniform(0.2, 0.8) * r
            fx, fy = x + d * math.cos(a), y + d * math.sin(a)
            fz = cz + r * 0.62 * math.sqrt(max(1 - (d / r) ** 2, 0)) + 0.012
            u = rng.random()
            mat = 'paintw' if u < 0.45 else ('paint2' if u < 0.8 else 'petal_w')
            tilt = (-0.5 * (fy - y) / r, 0.5 * (fx - x) / r)
            flowers.append(flower((fx, fy, fz), mat, rng.uniform(0.042, 0.052), seed=i * 7 + k, tilt=tilt))
    for f in flowers: m.add(f)
    return m


def planter1(): return planter('Planter1', 1.0, 3)


def planter2(): return planter('Planter2', 2.0, 5)


# ---------------------------------------------------------------- bench
def bench():
    m = Model('Bench', paint=(0.72, 0.52, 0.35), note='Cast-iron ends, wooden slats; part 1 = the slats.')
    W = 1.7
    fr = 'lampgreen'
    P1 = [(-0.25, 0.0), (-0.245, 0.12), (-0.232, 0.30), (-0.222, 0.40), (-0.17, 0.425), (0.0, 0.415), (0.14, 0.405),
          (0.2, 0.44), (0.235, 0.6), (0.262, 0.75), (0.29, 0.87)]
    P2 = [(0.27, 0.0), (0.25, 0.15), (0.19, 0.33), (0.12, 0.405)]
    ARM = [(0.235, 0.6), (0.12, 0.64), (-0.08, 0.64), (-0.2, 0.62), (-0.265, 0.56), (-0.26, 0.48), (-0.228, 0.42)]
    for sx in (-1, 1):
        x = sx * 0.72
        m.add(sweep([(x, y, z) for y, z in P1], (1, 0, 0), ell_sec(0.017, 0.03, 8), fr))
        m.add(sweep([(x, y, z) for y, z in P2], (1, 0, 0), ell_sec(0.017, 0.028, 8), fr))
        m.add(sweep([(x + sx * 0.005, y, z) for y, z in ARM], (1, 0, 0), ell_sec(0.024, 0.02, 6), fr))
        for (y, z) in ((-0.25, 0.0), (0.27, 0.0)):
            m.add(cbox((0.06, 0.09, 0.022), 0.008, fr, at=(x, y, 0.011)))
    seat = [(-0.20, 0.462), (-0.09, 0.458), (0.02, 0.454), (0.12, 0.45)]
    for (y, z) in seat:
        s = cbox((W, 0.095, 0.034), 0.012, 'paint'); uv_long(s, s.faces, 'wood')
        m.add(xform(s, T(0, y, z)))
    for z in (0.56, 0.68, 0.80):
        # the back slats sit on the front of the backrest curve, tilted with it
        y = 0.2 + (z - 0.44) * (0.09 / 0.43) - 0.03
        s = cbox((W, 0.03, 0.1), 0.012, 'paint'); uv_long(s, s.faces, 'wood')
        m.add(xform(s, T(0, y, z) @ R(-0.2, 'X')))
    return m


# ---------------------------------------------------------------- litter bin
def litter_bin():
    m = Model('Bin', paint=(0.36, 0.52, 0.42), note='Round litter bin with a hooded mouth; part 1 = body paint.')
    bm, _ = lathe([(0.24, 0.0), (0.24, 0.03), (0.222, 0.048), (0.205, 0.05)], 14, 'steel_d')
    m.add(bm)
    prof = [(0.205, 0.045), (0.212, 0.06), (0.212, 0.10), (0.222, 0.11), (0.222, 0.15), (0.212, 0.16), (0.208, 0.40),
            (0.212, 0.60), (0.222, 0.61), (0.222, 0.65), (0.214, 0.66), (0.0, 0.66)]
    bm, tags = lathe(prof, 14, ['paint'] * 10 + ['black'])
    grime_cyl(bm, off=0.4)
    m.add(bm)
    outer = [(0.214, 0.655), (0.228, 0.655), (0.236, 0.67), (0.236, 0.72), (0.223, 0.76), (0.19, 0.835), (0.13, 0.895),
             (0.06, 0.93), (0.0, 0.936)]
    inner = [(0.0, 0.92), (0.055, 0.915), (0.12, 0.88), (0.177, 0.822), (0.209, 0.752), (0.221, 0.72), (0.221, 0.67), (0.214, 0.655)]
    ho, _ = lathe(outer, 14, 'paint'); hi, _ = lathe(inner, 14, 'black')
    hood = join([ho, hi])
    bmesh.ops.remove_doubles(hood, verts=hood.verts[:], dist=1e-5)
    cut = rpiece((-0.135, -0.34, 0.695), (0.135, -0.04, 0.83), (0.05, 0.04, 0.05), 'black')
    hood = boolean_diff(hood, cut)
    grime_cyl(hood, off=0.4)
    m.add(hood)
    bm, tags = lathe([(0.0, 0.0), (0.08, 0.0), (0.08, 0.008), (0.072, 0.012), (0.0, 0.012)], 14, ['paint', 'paint', 'decal', 'decal'])
    uv_planar(bm, [f for f, s, i in tags if s >= 2], 'binplate', lambda co: (0.5 + co.x / 0.15, 0.5 + co.y / 0.15))
    m.add(xform(bm, frame((0, -0.206, 0.38), (0, -1, 0))))
    return m


# ---------------------------------------------------------------- vending machines
def vending(name, paint, disp, head):
    m = Model(name, paint=paint, note='Generic drinks machine (no brand, no text); part 1 = the body paint.')
    m.add(rpiece((-0.48, -0.34, 0.0), (0.48, 0.36, 0.08), (0.02, 0.02, 0.02), 'steel_d', skip=((2, -1),)))
    m.add(rpiece((-0.5, -0.37, 0.07), (0.5, 0.37, 1.82), (0.035, 0.035, 0.035), 'paint',
                 extra=((-0.25, 0.0, 0.25), (0.0,), (0.5, 1.0, 1.5)), skip=((2, -1),)))
    m.add(rpiece((-0.52, -0.405, 1.80), (0.52, 0.385, 1.87), (0.025, 0.025, 0.02), 'paint'))
    wx, wz, ww, wh = -0.12, 1.1, 0.62, 1.0
    m.add(front_plate((ww, 0.02, wh), (wx, -0.375, wz), disp, 'galv'))
    for sx in (-1, 1):
        m.add(cbox((0.035, 0.03, wh + 0.07), 0.01, 'galv', at=(wx + sx * (ww / 2 + 0.0175), -0.383, wz)))
        m.add(cbox((ww + 0.07, 0.03, 0.035), 0.01, 'galv', at=(wx, -0.383, wz + sx * (wh / 2 + 0.0175))))
    m.add(front_plate((0.88, 0.025, 0.16), (0, -0.38, 1.71), head, 'galv'))
    m.add(front_plate((0.2, 0.04, 0.5), (0.33, -0.385, 1.1), 'vpanel', 'galv'))
    m.add(cbox((0.64, 0.03, 0.24), 0.02, 'black', at=(-0.06, -0.372, 0.33)))
    m.add(cbox((0.58, 0.025, 0.13), 0.01, 'steel_d', at=(-0.06, -0.388, 0.35)))
    m.add(cbox((0.66, 0.045, 0.03), 0.01, 'galv', at=(-0.06, -0.39, 0.215)))
    m.add(cbox((0.11, 0.04, 0.07), 0.012, 'black', at=(0.33, -0.385, 0.7)))
    m.add(cbox((0.85, 0.02, 0.05), 0.008, 'steel_d', at=(0, -0.375, 0.13)))
    return m


def vending_red(): return vending('VendingRed', (0.80, 0.27, 0.24), 'vdisp1', 'vhead1')


def vending_blue(): return vending('VendingBlue', (0.30, 0.49, 0.73), 'vdisp2', 'vhead2')


# ---------------------------------------------------------------- post box
def post_box():
    m = Model('PostBox', paint=(0.80, 0.25, 0.21), note='Round pillar box; part 1 = body paint.')
    bm, _ = lathe([(0.272, 0.0), (0.272, 0.06), (0.25, 0.082), (0.228, 0.1)], 16, 'steel_d')
    m.add(bm)
    prof = [(0.228, 0.1), (0.222, 0.13), (0.218, 0.25), (0.214, 1.04), (0.222, 1.06), (0.226, 1.08), (0.226, 1.14),
            (0.242, 1.17), (0.248, 1.21), (0.24, 1.25), (0.205, 1.32), (0.14, 1.385), (0.06, 1.42), (0.0, 1.425)]
    bm, _ = lathe(prof, 16, 'paint')
    grime_cyl(bm, off=0.15)
    m.add(bm)
    m.add(cbox((0.27, 0.06, 0.035), 0.012, 'paint', at=(0, -0.22, 1.0)))
    m.add(cbox((0.22, 0.03, 0.024), 0.006, 'black', at=(0, -0.214, 0.968)))
    m.add(front_plate((0.15, 0.012, 0.13), (0, -0.218, 0.80), 'post', 'paint', r=0.005))
    bm, _ = lathe([(0.212, 0.3), (0.225, 0.31), (0.225, 0.66), (0.212, 0.67)], 6, 'paint', arc=(-PI / 2 - 0.55, -PI / 2 + 0.55))
    m.add(bm)
    m.add(cbox((0.022, 0.014, 0.045), 0.005, 'brass', at=(0.07, -0.222, 0.5)))
    return m


# ---------------------------------------------------------------- bicycle
def bicycle():
    m = Model('Bicycle', paint=(0.52, 0.72, 0.68),
              note='Parked city bike on its kickstand, leaning 4 degrees away from the camera; part 1 = frame paint.')
    Rw = 0.33; xr, xf = -0.52, 0.53
    parts = []
    tyre_sec = [(0.0, -0.025), (0.022, -0.012), (0.022, 0.012), (0.0, 0.025), (-0.016, 0.015),
                (-0.044, 0.008), (-0.044, -0.008), (-0.016, -0.015)]
    for xc in (xr, xf):
        parts.append(torus((xc, 0, Rw), Rw - 0.025, tyre_sec, 15, ['rubber'] * 4 + ['chrome'] * 3 + ['rubber']))
        for k in range(4):
            a = PI / 4 * k + 0.2
            d = Vector((math.cos(a), 0, math.sin(a))) * (Rw - 0.06)
            c = Vector((xc, 0, Rw))
            parts.append(tube([c - d, c + d], 0.0035, 'chrome', sides=3, caps=False))
        hb, _ = lathe([(0.0, -0.05), (0.024, -0.04), (0.024, 0.04), (0.0, 0.05)], 6, 'galv')
        parts.append(xform(hb, T(xc, 0, Rw) @ R(PI / 2, 'X')))
    BB = Vector((-0.06, 0, 0.30)); HB = Vector((0.40, 0, 0.66)); HT = Vector((0.44, 0, 0.84)); ST = Vector((-0.22, 0, 0.80))
    ctrl = Vector((0.13, 0, 0.24))
    dt = [(1 - t) ** 2 * HB + 2 * (1 - t) * t * ctrl + t * t * BB for t in np.linspace(0, 1, 6)]
    parts.append(tube(dt, 0.022, 'paint', sides=6))
    parts.append(tube([BB, ST], 0.02, 'paint', sides=6))
    parts.append(tube([HB - Vector((0.01, 0, 0.03)), HT], 0.027, 'paint', sides=8))
    for sy in (-1, 1):
        parts.append(tube([BB + Vector((0, sy * 0.03, 0)), (xr, sy * 0.055, Rw)], 0.011, 'paint', sides=5))
        parts.append(tube([ST + Vector((0.02, sy * 0.025, -0.07)), (xr, sy * 0.055, Rw)], 0.010, 'paint', sides=5))
        parts.append(tube([(0.395, sy * 0.035, 0.635), (0.455, sy * 0.055, 0.48), (xf, sy * 0.055, Rw)], 0.011, 'paint', sides=5))
    parts.append(tube([HT, (0.42, 0, 0.98)], 0.016, 'chrome', sides=6))
    bar = [(0.29, -0.27, 1.0), (0.38, -0.25, 1.0), (0.43, -0.12, 0.985), (0.44, 0, 0.98), (0.43, 0.12, 0.985), (0.38, 0.25, 1.0), (0.29, 0.27, 1.0)]
    parts.append(tube(bar, 0.012, 'chrome', sides=5))
    for sy in (-1, 1):
        parts.append(tube([(0.30, sy * 0.27, 1.0), (0.19, sy * 0.28, 1.0)], 0.018, 'rubber', sides=5))
    parts.append(ball(0.022, 'chrome', n=6, rings=3, at=(0.41, -0.16, 1.01)))
    parts.append(tube([ST, (-0.25, 0, 0.93)], 0.013, 'chrome', sides=5))
    sd = cbox((0.26, 0.15, 0.06), 0.025, 'saddle')
    for v in sd.verts:
        k = min(max((v.co.x + 0.02) / 0.15, 0.0), 1.0)
        v.co.y *= 1 - 0.55 * k; v.co.z += 0.012 * k
    sd.normal_update()
    parts.append(xform(sd, T(-0.26, 0, 0.955)))
    # mudguards, a rear rack, the chain guard, chainring, cranks and pedals
    msec = [(0.0, -0.032), (0.012, -0.028), (0.012, 0.028), (0.0, 0.032)]
    for xc, a0, a1 in ((xf, 0.25, 2.7), (xr, 0.45, 3.3)):
        c = Vector((xc, 0, Rw)); rr = Rw + 0.03
        path = [c + Vector((math.cos(a), 0, math.sin(a))) * rr for a in np.linspace(a0, a1, 7)]
        parts.append(sweep(path, lambda i, p, t, c=c: Vector(p) - c, msec, 'galv'))
    for sy in (-1, 1):
        parts.append(tube([(-0.22, sy * 0.07, 0.715), (-0.86, sy * 0.07, 0.715)], 0.009, 'galv', sides=4))
        parts.append(tube([(-0.76, sy * 0.07, 0.715), (xr - 0.02, sy * 0.06, Rw + 0.02)], 0.008, 'galv', sides=4))
    for x in (-0.5, -0.74):
        parts.append(tube([(x, -0.075, 0.715), (x, 0.075, 0.715)], 0.007, 'galv', sides=4, caps=False))
    cg = prism([(0.02, 0.37), (0.075, 0.32), (0.05, 0.255), (-0.08, 0.24), (-0.47, 0.305), (-0.5, 0.345), (-0.46, 0.37)], 0.012, 'paint')
    parts.append(xform(cg, T(0, -0.085, 0)))
    cr, _ = lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.008), (0.0, 0.008)], 10, 'steel_d')
    parts.append(xform(cr, T(BB.x, -0.055, BB.z) @ R(PI / 2, 'X')))
    for sy, ang in ((-1, 0.6), (1, 0.6 + PI)):
        d = Vector((math.sin(ang), 0, -math.cos(ang))) * 0.165
        parts.append(tube([BB + Vector((0, sy * 0.075, 0)), BB + d + Vector((0, sy * 0.075, 0))], 0.012, 'steel_d', sides=4))
        parts.append(cbox((0.1, 0.075, 0.022), 0.0, 'black', at=BB + d + Vector((0, sy * 0.12, 0))))
    # front basket (hollow) on struts, a lamp on the fork crown
    bk = cbox((0.3, 0.34, 0.24), 0.02, 'galv')
    inset_top(bk, 0.012, 0.2, inner_mat='steel_d', cos=0.99)
    sides = [f for f in bk.faces if abs(f.normal.z) < 0.5]
    uv_planar(bk, sides, 'basket', lambda co: (0.5 + (co.x + co.y) / 0.62, 0.5 + co.z / 0.25))
    parts.append(xform(bk, T(0.64, 0, 0.92)))
    for sy in (-1, 1):
        parts.append(tube([(0.62, sy * 0.1, 0.80), (xf, sy * 0.055, Rw)], 0.007, 'galv', sides=4))
    lp, tags = lathe([(0.0, -0.03), (0.04, -0.03), (0.045, 0.02), (0.04, 0.03), (0.0, 0.033)], 8, ['chrome', 'chrome', 'lampglow', 'lampglow'])
    parts.append(xform(lp, frame((0.47, 0, 0.66), (1, 0, 0))))
    # kickstand on the far side; the whole bike leans onto it
    parts.append(tube([BB + Vector((-0.06, 0.05, 0.0)), (-0.2, 0.2, 0.024)], 0.011, 'galv', sides=5))
    parts.append(cbox((0.05, 0.035, 0.014), 0.004, 'galv', at=(-0.2, 0.2, 0.021)))
    lean = R(-0.07, 'X')
    for p in parts: m.add(xform(p, lean))
    return m


MODELS = [planter1, planter2, bench, litter_bin, vending_red, vending_blue, post_box, bicycle]
