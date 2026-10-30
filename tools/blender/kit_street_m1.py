# Street kit models, part 1: poles, lamps, signals, walls, fence, hoarding, signs, road-works kit
# and the flat ground pieces. Each builder returns a kit_street_build.Model. Front faces -Y.
import math
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from kit_street_geo import (PI, lathe, sweep, tube, cbox, rpiece, prism, ball, boolean_diff, xform, T, R, S,
                            frame, setmat, faces_facing, uv_planar, uv_long, uv_cyl, uv_white, grime_cyl,
                            lay, MATS, mid, circle_sec, delete_faces, new_bm, merge)
from kit_street_build import Model


# ---------------------------------------------------------------- shared helpers
def decal_faces(bm, region, d, fn, other=None, cos=0.6):
    """Faces looking along d become 'decal' with planar UVs fn(co) -> (s, t); the rest take other."""
    fr = faces_facing(bm, d, cos)
    if other: setmat(bm, other)
    setmat(bm, 'decal', fr)
    uv_planar(bm, fr, region, fn)
    return bm


def front_plate(size, at, region, mat_other='steel', r=0.01, d=(0, -1, 0)):
    """A thin plate whose -Y face shows an atlas region (x across, z up)."""
    w, dep, h = size
    bm = cbox(size, r, mat_other)
    decal_faces(bm, region, d, lambda co: (0.5 + co.x / w, 0.5 + co.z / h))
    return xform(bm, T(at))


def pole_lathe(prof, n, mat, cyl=True, off=0.0):
    bm, tags = lathe(prof, n, mat)
    if cyl: grime_cyl(bm, off=off)
    return bm


def radius_at(prof, z):
    for (r0, z0), (r1, z1) in zip(prof[:-1], prof[1:]):
        if z0 <= z <= z1 and z1 > z0:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return prof[-1][0]


def end_caps(m, L, y0, y1, z0, z1, mat):
    """Closing quads just inside both ends of a tiling piece (separate from the body, so they never
    weld to it or change its normals; in a tiled run they sit back to back, hidden)."""
    from kit_street_geo import bm_from
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.0006)
        q = [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]
        bm, _ = bm_from(q, [[0, 1, 2, 3] if sx > 0 else [3, 2, 1, 0]], [mat])
        bm.normal_update()
        for f in bm.faces:
            if f.normal.x * sx < 0: f.normal_flip()
        m.add(bm)


def insulator(at, scale=1.0, n=8):
    s = scale
    prof = [(0.016 * s, 0), (0.016 * s, 0.03 * s), (0.056 * s, 0.036 * s), (0.058 * s, 0.05 * s), (0.034 * s, 0.06 * s),
            (0.05 * s, 0.074 * s), (0.051 * s, 0.088 * s), (0.03 * s, 0.098 * s), (0.026 * s, 0.112 * s), (0.0, 0.12 * s)]
    bm, _ = lathe(prof, n, ['steel_d'] + ['porcelain'] * 8)
    return xform(bm, T(at))


def clamp_ring(r, z0, z1, mat='steel_d', n=12):
    bm, _ = lathe([(r - 0.01, z0), (r + 0.012, z0 + 0.008), (r + 0.012, z1 - 0.008), (r - 0.01, z1)], n, mat)
    return bm


def sign_post(m, h=2.45, r=0.032):
    prof = [(0.075, 0.0), (0.075, 0.035), (0.045, 0.06), (r, 0.08), (r, h - 0.02), (r * 0.7, h), (0.0, h + 0.012)]
    bm, _ = lathe(prof, 8, ['concrete_d', 'concrete_d', 'galv', 'galv', 'galv', 'galv'])
    grime_cyl(bm)
    m.add(bm)


# ---------------------------------------------------------------- utility pole (9 m)
def utility_pole():
    m = Model('UtilityPole', note='Concrete pole; wires go from Attach.WireL/R/M to the next pole.')
    prof = [(0.176, 0.0), (0.173, 0.6), (0.166, 2.0), (0.153, 4.0), (0.140, 6.0), (0.129, 7.8),
            (0.122, 8.86), (0.112, 8.96), (0.075, 9.0), (0.0, 9.012)]
    m.add(pole_lathe(prof, 14, 'pole'))
    # yellow-black guard sleeve
    sp = [(0.174, 0.13), (0.191, 0.15), (0.193, 0.19), (0.193, 1.93), (0.191, 1.97), (0.17, 1.99)]
    bm, tags = lathe(sp, 14, ['black', 'black', 'decal', 'black', 'black'])
    uv_cyl(bm, [f for f, s, i in tags if s == 2], 'hazard', tfn=lambda co: (co.z - 0.19) / 1.74)
    m.add(bm)
    # step bolts, alternating left and right
    for i, z in enumerate(np.arange(2.45, 7.7, 0.42)):
        sx = 1 if i % 2 == 0 else -1
        r = radius_at(prof, z)
        m.add(tube([(sx * (r - 0.02), 0, z), (sx * (r + 0.17), 0, z), (sx * (r + 0.21), 0, z + 0.05)], 0.017, 'steel_d', sides=4))
    # crossarm with braces and clamps
    za = 8.35; ya = -0.175
    m.add(cbox((2.1, 0.11, 0.11), 0.018, 'steel', at=(0, ya, za)))
    for sx in (-1, 1):
        m.add(tube([(0, ya + 0.04, 7.86), (sx * 0.62, ya, za - 0.04)], 0.016, 'steel', sides=4))
    m.add(clamp_ring(radius_at(prof, za), za - 0.06, za + 0.06))
    m.add(clamp_ring(radius_at(prof, 7.86), 7.82, 7.9))
    for x in (-0.86, 0.86):
        m.add(insulator((x, ya, za + 0.055), 1.4))
    m.add(insulator((0, 0, 9.0), 1.45))
    m.at('WireL', (-0.86, ya, za + 0.055 + 0.14))
    m.at('WireR', (0.86, ya, za + 0.055 + 0.14))
    m.at('WireM', (0.0, 0.0, 9.0 + 0.145))
    # transformer can hung on the +X side, with brackets, bushings and leads
    tx = 0.47
    tp = [(0.0, 6.2), (0.24, 6.2), (0.272, 6.24), (0.28, 6.3), (0.28, 6.52), (0.29, 6.545), (0.28, 6.57),
          (0.28, 6.98), (0.296, 7.0), (0.296, 7.07), (0.26, 7.1), (0.18, 7.16), (0.0, 7.18)]
    bm = pole_lathe(tp, 14, 'trans', off=0.3)
    m.add(xform(bm, T(tx, 0, 0)))
    for z in (6.42, 6.9):
        m.add(cbox((0.34, 0.08, 0.06), 0.012, 'steel_d', at=(0.26, 0, z)))
        m.add(clamp_ring(radius_at(prof, z), z - 0.035, z + 0.035))
    for dx in (-0.08, 0.08):
        bm, _ = lathe([(0.04, 0), (0.04, 0.04), (0.056, 0.052), (0.032, 0.078), (0.048, 0.09), (0.026, 0.124), (0, 0.13)], 6, 'porcelain')
        m.add(xform(bm, T(tx + dx * 1.3, 0, 7.15)))
    m.add(tube([(tx + 0.1, 0, 7.28), (tx + 0.22, -0.05, 7.58), (0.8, -0.14, 8.0), (0.86, ya, za + 0.19)], 0.011, 'black', sides=4))
    m.add(tube([(tx - 0.1, 0, 7.28), (tx - 0.14, -0.08, 7.6), (0.12, -0.14, 8.1), (0.0, -0.06, 8.9)], 0.011, 'black', sides=4))
    # ground lead down the front of the pole, with clips
    r0 = radius_at(prof, 3.0)
    m.add(tube([(0.05, -radius_at(prof, 6.2) - 0.02, 6.2), (0.05, -r0 - 0.02, 3.0), (0.05, -0.185, 2.0)], 0.011, 'black', sides=4))
    for z in (5.4, 4.2, 3.0):
        m.add(cbox((0.05, 0.03, 0.03), 0.008, 'galv', at=(0.05, -radius_at(prof, z) - 0.018, z)))
    # a number plate (no text) strapped to the pole
    m.add(front_plate((0.17, 0.014, 0.30), (-0.0, -radius_at(prof, 2.25) - 0.01, 2.25), 'plate', 'steel'))
    return m


# ---------------------------------------------------------------- street lamp (6 m)
def street_lamp():
    m = Model('StreetLamp', note='Arm reaches +X (reads in the side view); Attach.Light at the lamp bowl.')
    m.add(rpiece((-0.22, -0.22, 0.0), (0.22, 0.22, 0.08), (0.03, 0.03, 0.025), 'concrete'))
    prof = [(0.17, 0.08), (0.17, 0.13), (0.15, 0.16), (0.13, 0.34), (0.1, 0.5), (0.106, 0.53), (0.106, 0.58),
            (0.09, 0.62), (0.08, 1.30), (0.09, 1.33), (0.09, 1.39), (0.078, 1.42), (0.066, 5.30), (0.055, 5.42)]
    m.add(pole_lathe(prof, 10, 'lampgreen'))
    m.add(front_plate((0.1, 0.012, 0.17), (0, -0.138, 0.30), 'plate', 'lampgreen', r=0.006))
    # swan-neck arm: up, a quarter turn over, out to the lamp
    path = [(0, 0, 5.15), (0, 0, 5.4)]
    for k in range(1, 7):
        a = (PI / 2) * k / 6
        path.append((0.45 - 0.45 * math.cos(a), 0, 5.4 + 0.45 * math.sin(a)))
    path += [(0.75, 0, 5.85), (1.05, 0, 5.85), (1.2, 0, 5.83)]
    sc = [1.0, 1.0] + [1.0 - 0.18 * k / 6 for k in range(1, 7)] + [0.8, 0.76, 0.74]
    m.add(sweep(path, lambda i, p, t: Vector((0, 1, 0)).cross(t), circle_sec(0.052, 8, 0.5), 'lampgreen', True, sc))
    # a scroll under the arm
    c = Vector((0.42, 0, 5.47)); pts = []
    th0, th1 = PI + 0.35, -PI - 0.4
    for k in range(25):
        f = k / 24; th = th0 + (th1 - th0) * f; rr = 0.40 - 0.31 * f
        pts.append(c + Vector((rr * math.cos(th), 0, rr * math.sin(th))))
    m.add(tube(pts, 0.013, 'lampgreen', sides=6))
    m.add(ball(0.022, 'lampgreen', n=6, rings=3, at=pts[-1]))
    # the lamp: a bell hood over a warm bowl, a finial on top
    lx = 1.25
    hp = [(0.0, 5.44), (0.11, 5.447), (0.185, 5.472), (0.215, 5.51), (0.255, 5.515), (0.275, 5.545), (0.25, 5.59),
          (0.19, 5.69), (0.11, 5.77), (0.065, 5.80), (0.045, 5.84), (0.055, 5.862), (0.0, 5.885)]
    bm, tags = lathe(hp, 14, ['lampglow'] * 3 + ['lampgreen'] * 9)
    uv_planar(bm, [f for f, s, i in tags if s < 3], 'lamp', lambda co: (0.5 + co.x / 0.44, 0.5 + co.y / 0.44))
    m.add(xform(bm, T(lx, 0, 0)))
    m.add(ball(0.03, 'lampgreen', n=8, rings=4, at=(lx, 0, 5.9)))
    m.at('Light', (lx, 0, 5.44))
    return m


# ---------------------------------------------------------------- pedestrian signal (about 3 m)
def ped_signal():
    m = Model('PedSignal', note='Lamp faces are dark: the game draws its red-man / green-man icons at Attach.Red / Attach.Green.')
    prof = [(0.12, 0.0), (0.12, 0.05), (0.09, 0.08), (0.075, 0.14), (0.06, 0.18), (0.06, 2.96), (0.04, 2.99), (0.0, 3.0)]
    m.add(pole_lathe(prof, 10, 'signalgrey'))
    # head housing on the front of the pole
    y0, y1, z0, z1 = -0.25, -0.075, 1.96, 2.94
    m.add(rpiece((-0.23, y0, z0), (0.23, y1, z1), (0.045, 0.03, 0.045), 'housing'))
    m.add(rpiece((-0.255, y0 - 0.03, z1 - 0.005), (0.255, y1 + 0.01, z1 + 0.035), (0.03, 0.02, 0.012), 'housing'))
    for z in (2.12, 2.80):
        m.add(cbox((0.12, 0.05, 0.08), 0.012, 'steel_d', at=(0, -0.07, z)))
        m.add(clamp_ring(0.06, z - 0.045, z + 0.045, 'steel_d', 10))
    for name, zc in (('Red', 2.68), ('Green', 2.22)):
        lp = [(0.0, -0.02), (0.168, -0.02), (0.168, 0.008), (0.158, 0.02), (0.146, 0.016), (0.14, 0.012), (0.0, 0.018)]
        bm, tags = lathe(lp, 18, ['housing', 'housing', 'housing', 'housing', 'decal', 'decal'])
        uv_planar(bm, [f for f, s, i in tags if s >= 4], 'lens', lambda co: (0.5 + co.x / 0.29, 0.5 + co.y / 0.29))
        m.add(xform(bm, frame((0, y0, zc), (0, -1, 0))))
        # visor: a hood over the top of the lamp, longer at the crown
        vb, _ = lathe([(0.165, 0.0), (0.177, 0.0), (0.177, 0.16), (0.165, 0.16), (0.165, 0.0)], 10, 'housing', arc=(-0.15, PI + 0.15))
        for v in vb.verts:
            a = math.atan2(v.co.y, v.co.x)
            v.co.z *= (0.25 + 0.75 * max(math.sin(a), 0.0))
        vb.normal_update()
        m.add(xform(vb, frame((0, y0 - 0.005, zc), (0, -1, 0))))
        m.at(name, (0, y0 - 0.025, zc))
    # a small crossing plate under the head (icon only)
    m.add(front_plate((0.22, 0.012, 0.22), (0, -0.075, 1.78), 'crossing', 'galv', r=0.008))
    m.add(cbox((0.05, 0.02, 0.06), 0.0, 'steel_d', at=(0, -0.062, 1.78)))
    # push-button box at hand height
    m.add(rpiece((-0.1, -0.2, 0.94), (0.1, -0.06, 1.27), (0.025, 0.02, 0.025), 'yellow'))
    m.add(front_plate((0.15, 0.012, 0.26), (0, -0.203, 1.105), 'button', 'yellow', r=0.006))
    bm, _ = lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.012), (0.034, 0.02), (0.03, 0.026), (0.0, 0.03)], 12, ['steel', 'steel', 'steel', 'black', 'black'])
    m.add(xform(bm, frame((0, -0.208, 1.0), (0, -1, 0))))
    for z in (0.98, 1.23):
        m.add(clamp_ring(0.06, z - 0.03, z + 0.03, 'steel_d', 10))
    return m


# ---------------------------------------------------------------- block wall (2 m tile) and pillar
WALL_H = 1.8      # the 'wall' atlas region spans z 0..1.8 m and x -1..1 m


def wall_uv(bm, xoff=0.0, side_axis=None):
    fr = [f for f in bm.faces if abs(f.normal.y) > 0.6]
    uv_planar(bm, fr, 'wall', lambda co: ((co.x + xoff + 1) / 2, co.z / WALL_H))
    fs = [f for f in bm.faces if abs(f.normal.x) > 0.6]
    if fs: uv_planar(bm, fs, 'wall', lambda co: ((co.y + xoff + 1) / 2, co.z / WALL_H))


def block_wall():
    L = 2.0
    m = Model('BlockWall2', paint=(0.79, 0.75, 0.68), tile=L,
              note='Tiles along X every 2.0 m (flush ends, capped). Part 1 = the blocks.')
    ends = ((0, -1), (0, 1))
    hx = (-0.6, -0.2, 0.2, 0.6)
    xl = [-0.6, -0.2, 0.2, 0.6] + [c + d for c in hx for d in (-0.09, 0.09)]
    zl = [0.3, 0.6, 0.9, 1.115, 1.2, 1.285, 1.4]
    body = rpiece((-L / 2, -0.125, 0.10), (L / 2, 0.125, 1.50), (1e-4, 0.012, 0.012), 'paintc', seg=(0, 1, 1),
                  extra=(xl, (), zl), skip=ends + ((2, -1), (2, 1)))
    wall_uv(body)
    cut = new_bm()
    for cx in hx:
        cb, _ = lathe([(0.0, -0.3), (0.074, -0.3), (0.074, 0.3), (0.0, 0.3)], 12, 'concrete', phase=0.0)
        merge(cut, xform(cb, T(cx, 0, 1.2) @ R(PI / 2, 'X')))
    body = boolean_diff(body, cut)
    m.add(body)
    xs = (-0.5, 0.0, 0.5)
    m.add(rpiece((-L / 2, -0.152, 1.50), (L / 2, 0.152, 1.60), (1e-4, 0.035, 0.03), 'concrete', seg=(0, 2, 1),
                 extra=(xs, (), ()), skip=ends + ((2, -1),)))
    m.add(rpiece((-L / 2, -0.138, 0.0), (L / 2, 0.138, 0.10), (1e-4, 0.012, 0.012), 'concrete_d', seg=(0, 1, 1),
                 extra=(xs, (), ()), skip=ends + ((2, -1),)))
    end_caps(m, L, -0.124, 0.124, 0.10, 1.50, 'concrete')
    end_caps(m, L, -0.148, 0.148, 1.505, 1.595, 'concrete')
    end_caps(m, L, -0.136, 0.136, 0.0, 0.098, 'concrete_d')
    return m


def wall_pillar():
    m = Model('WallPillar', paint=(0.79, 0.75, 0.68),
              note='Gate pillar for the ends of BlockWall2 runs; part 1 = the blocks (same base as the wall).')
    body = rpiece((-0.22, -0.197, 0.10), (0.22, 0.197, 1.70), (0.012, 0.012, 0.012), 'paintc',
                  extra=((0.0,), (0.0,), (0.3, 0.6, 0.9, 1.2, 1.5)), skip=((2, -1), (2, 1)))
    wall_uv(body, xoff=-1.0)
    m.add(body)
    m.add(rpiece((-0.235, -0.212, 0.0), (0.235, 0.212, 0.10), (0.012, 0.012, 0.012), 'concrete_d', skip=((2, -1),)))
    m.add(rpiece((-0.25, -0.225, 1.70), (0.25, 0.225, 1.81), (0.03, 0.03, 0.03), 'concrete', skip=((2, -1),)))
    bm, _ = lathe([(0.29, 1.80), (0.29, 1.83), (0.06, 1.94), (0.0, 1.95)], 4, 'concrete', phase=0.5)
    for v in bm.verts:
        v.co.x *= 0.235 / 0.205; v.co.y *= 0.212 / 0.205
    m.add(bm)
    # a blank wooden name plaque and an intercom box
    pl = cbox((0.22, 0.022, 0.11), 0.012, 'darkwood', at=(0, -0.205, 1.36))
    uv_long(pl, pl.faces, 'wood')
    m.add(pl)
    m.add(rpiece((-0.04, -0.222, 1.03), (0.04, -0.19, 1.17), (0.012, 0.01, 0.012), 'steel'))
    bm, _ = lathe([(0.0, 0.0), (0.016, 0.0), (0.016, 0.006), (0.0, 0.01)], 8, 'brass')
    m.add(xform(bm, frame((0, -0.222, 1.07), (0, -1, 0))))
    m.add(cbox((0.05, 0.008, 0.03), 0.004, 'black', at=(0, -0.223, 1.135)))
    return m


# ---------------------------------------------------------------- picket fence (2 m tile)
def picket_fence():
    L = 2.0
    m = Model('PicketFence2', paint=(0.95, 0.93, 0.86), tile=L,
              note='Tiles along X every 2.0 m (rails cut flush at the ends, a post at x = 0). Part 1 = paint.')
    rng = np.random.default_rng(4)
    ends = ((0, -1), (0, 1))
    for z in (0.26, 0.78):
        m.add(rpiece((-L / 2, 0.0, z - 0.035), (L / 2, 0.03, z + 0.035), (1e-4, 0.008, 0.01), 'paintp', seg=(0, 1, 1),
                     extra=((-0.5, 0.0, 0.5), (), ()), skip=ends))
        end_caps(m, L, 0.001, 0.029, z - 0.034, z + 0.034, 'paintp')
    post = rpiece((-0.045, 0.03, 0.0), (0.045, 0.12, 1.02), (0.01, 0.01, 0.01), 'paintp', skip=((2, -1), (2, 1)))
    m.add(post)
    bm, _ = lathe([(0.072, 1.02), (0.072, 1.035), (0.0, 1.09)], 4, 'paintp', phase=0.5)
    m.add(xform(bm, T(0, 0.075, 0)))
    for i in range(10):
        x = -0.9 + 0.2 * i
        h = 0.98 + rng.uniform(-0.015, 0.015)
        pts = [(-0.045, 0.04), (0.045, 0.04), (0.045, h - 0.06), (0.0, h), (-0.045, h - 0.06)]
        pk = prism(pts, 0.022, 'paint', bevel=0.006)
        uv_long(pk, pk.faces, 'pwood')
        m.add(xform(pk, T(x, -0.024, 0) @ R(rng.uniform(-0.02, 0.02), 'Y')))
    return m


# ---------------------------------------------------------------- site hoarding (3 m tile)
def hoarding():
    L, H = 3.0, 2.6
    m = Model('Hoarding3', tile=L, note='Tiles along X every 3.0 m: corrugated sheets with a painted landscape; a post and a weighted foot behind x = 0.')
    # corrugated front sheet: valley, rise, crest, fall (period 0.15 m)
    xs = []
    for k in range(20):
        x0 = -L / 2 + 0.15 * k
        xs += [(x0, 0.0), (x0 + 0.06, 0.0), (x0 + 0.075, -0.014), (x0 + 0.105, -0.014), (x0 + 0.12, 0.0)]
    xs.append((L / 2, 0.0))
    zs = [0.02, 0.45, 1.6, 2.56]
    V = []; F = []
    for z in zs:
        V += [(x, y, z) for x, y in xs]
    n = len(xs)
    for j in range(len(zs) - 1):
        for i in range(n - 1):
            a = j * n + i; F.append([a, a + 1, a + 1 + n, a + n])
    from kit_street_geo import bm_from
    sheet, _ = bm_from(V, F, ['decal'] * len(F))
    from kit_street_geo import fix_normals
    sheet.normal_update()
    for f in sheet.faces:
        if f.normal.y > 0: f.normal_flip()
    uv_planar(sheet, sheet.faces, 'hoard', lambda co: ((co.x + L / 2) / L, co.z / H))
    m.add(sheet)
    back, _ = bm_from([(-L / 2, 0.004, 0.02), (L / 2, 0.004, 0.02), (L / 2, 0.004, 1.3), (-L / 2, 0.004, 1.3),
                       (L / 2, 0.004, 2.56), (-L / 2, 0.004, 2.56)], [[0, 1, 2, 3], [3, 2, 4, 5]], ['galv', 'galv'])
    back.normal_update()
    for f in back.faces:
        if f.normal.y < 0: f.normal_flip()
    m.add(back)
    ends = ((0, -1), (0, 1))
    m.add(rpiece((-L / 2, -0.035, 2.54), (L / 2, 0.025, 2.60), (1e-4, 0.012, 0.012), 'galv', seg=(0, 1, 1), skip=ends,
                 extra=((-0.75, 0.0, 0.75), (), ())))
    m.add(rpiece((-L / 2, -0.03, 0.0), (L / 2, 0.02, 0.05), (1e-4, 0.01, 0.01), 'galv', seg=(0, 1, 1), skip=ends,
                 extra=((-0.75, 0.0, 0.75), (), ())))
    end_caps(m, L, -0.034, 0.024, 2.541, 2.599, 'galv')
    end_caps(m, L, -0.029, 0.019, 0.001, 0.049, 'galv')
    end_caps(m, L, -0.013, 0.004, 0.02, 2.56, 'galv')
    # cover strips over the sheet joints (halves at the tile ends make whole strips when tiled)
    for (x0, x1, sk) in ((-0.03, 0.03, ()), (-L / 2, -L / 2 + 0.03, ((0, -1),)), (L / 2 - 0.03, L / 2, ((0, 1),))):
        m.add(rpiece((x0, -0.03, 0.05), (x1, -0.012, 2.54), (0.008 if not sk else 1e-4, 0.005, 0.005), 'galv', skip=sk))
        for z in (0.3, 1.3, 2.3):
            xc = (x0 + x1) / 2 if not sk else (x1 if x0 < 0 else x0)
            if sk: continue
            bm, _ = lathe([(0.0, 0.0), (0.012, 0.0), (0.01, 0.006), (0.0, 0.008)], 6, 'steel_d')
            m.add(xform(bm, frame((xc, -0.03, z), (0, -1, 0))))
    # scaffold post, couplers, a raking brace and a concrete foot behind x = 0
    m.add(tube([(0, 0.05, 0.0), (0, 0.05, 2.5)], 0.024, 'steel', sides=8))
    for z in (0.5, 2.05):
        m.add(cbox((0.09, 0.07, 0.07), 0.012, 'steel_d', at=(0, 0.04, z)))
    m.add(tube([(0, 0.06, 1.95), (0, 0.95, 0.2)], 0.022, 'steel', sides=6))
    m.add(rpiece((-0.18, 0.75, 0.0), (0.18, 1.15, 0.22), (0.03, 0.03, 0.03), 'concrete', skip=((2, -1),)))
    m.add(tube([(0, 0.05, 0.1), (0, 0.85, 0.1)], 0.02, 'steel', sides=6))
    return m


# ---------------------------------------------------------------- signs
def sign_no_entry():
    m = Model('SignNoEntry', note='Round sign, icon only.')
    sign_post(m)
    R0 = 0.305
    sp = [(0.0, 0.0), (0.27, 0.0), (0.30, 0.004), (R0, 0.012), (0.30, 0.02), (0.288, 0.023), (0.0, 0.023)]
    bm, tags = lathe(sp, 24, ['galv', 'galv', 'decal', 'decal', 'decal', 'decal'])
    uv_planar(bm, [f for f, s, i in tags if s >= 2], 'noentry', lambda co: (0.5 + co.x / (2 * R0), 0.5 + co.y / (2 * R0)))
    m.add(xform(bm, frame((0, -0.045, 2.12), (0, -1, 0))))
    for z in (1.98, 2.26):
        m.add(cbox((0.1, 0.05, 0.035), 0.01, 'steel_d', at=(0, -0.02, z)))
        m.add(clamp_ring(0.032, z - 0.02, z + 0.02, 'steel_d', 8))
    return m


def sign_crossing():
    m = Model('SignCrossing', note='Square sign, icon only (a figure on a crossing).')
    sign_post(m)
    w = 0.6
    bm = rpiece((-w / 2, -w / 2, 0.0), (w / 2, w / 2, 0.022), (0.045, 0.045, 0.009), 'galv',
                mats=lambda a, s, c: 'decal' if (a == 2 and s > 0) else 'galv')
    fr = [f for f in bm.faces if f.normal.z > 0.3]
    setmat(bm, 'decal', fr)
    uv_planar(bm, fr, 'crossing', lambda co: (0.5 + co.x / w, 0.5 + co.y / w))
    m.add(xform(bm, frame((0, -0.045, 2.1), (0, -1, 0))))
    for z in (1.92, 2.28):
        m.add(cbox((0.1, 0.05, 0.035), 0.01, 'steel_d', at=(0, -0.02, z)))
        m.add(clamp_ring(0.032, z - 0.02, z + 0.02, 'steel_d', 8))
    return m


# ---------------------------------------------------------------- road-works and bollard
def bollard():
    m = Model('Bollard', paint=(0.38, 0.40, 0.42), note='Steel bollard; part 1 = body paint.')
    prof = [(0.125, 0.0), (0.125, 0.03), (0.105, 0.05), (0.088, 0.09), (0.085, 0.58), (0.094, 0.6), (0.094, 0.68),
            (0.085, 0.7), (0.085, 0.8), (0.078, 0.84), (0.06, 0.88), (0.03, 0.9), (0.0, 0.905)]
    mats = ['steel_d', 'steel_d', 'paint', 'paint', 'paint', 'yellow', 'paint', 'paint', 'paint', 'paint', 'paint', 'paint']
    bm, _ = lathe(prof, 14, mats)
    grime_cyl(bm, off=0.2)
    m.add(bm)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        bb, _ = lathe([(0.0, 0.0), (0.014, 0.0), (0.014, 0.012), (0.0, 0.016)], 6, 'steel_d')
        m.add(xform(bb, T(0.105 * math.cos(a), 0.105 * math.sin(a), 0.03)))
    return m


def traffic_cone():
    m = Model('TrafficCone', note='Orange cone with two reflective bands on a rubber base.')
    m.add(rpiece((-0.19, -0.19, 0.0), (0.19, 0.19, 0.035), (0.06, 0.06, 0.012), 'rubber', skip=((2, -1),)))
    prof = [(0.152, 0.03), (0.158, 0.045), (0.142, 0.06), (0.126, 0.17), (0.116, 0.235), (0.104, 0.31),
            (0.093, 0.38), (0.083, 0.45), (0.056, 0.62), (0.05, 0.655), (0.035, 0.672), (0.0, 0.676)]
    mats = ['orange', 'orange', 'orange', 'orange', 'white', 'orange', 'white', 'orange', 'orange', 'orange', 'orange']
    bm, _ = lathe(prof, 16, mats)
    grime_cyl(bm, off=0.1)
    m.add(bm)
    return m


def road_barrier():
    m = Model('RoadBarrier', note='Road-works barrier, about 1.8 m; Attach.Lamp at the amber lamp.')
    for sx in (-1, 1):
        x = sx * 0.82
        m.add(rpiece((x - 0.06, -0.3, 0.0), (x + 0.06, 0.3, 0.085), (0.025, 0.08, 0.025), 'rubber', skip=((2, -1),)))
        m.add(rpiece((x - 0.022, -0.022, 0.06), (x + 0.022, 0.022, 1.06), (0.008, 0.008, 0.008), 'white'))
        m.add(rpiece((x - 0.03, -0.03, 1.05), (x + 0.03, 0.03, 1.08), (0.01, 0.01, 0.01), 'black'))
    for (z0, z1) in ((0.40, 0.58), (0.82, 1.0)):
        bm = rpiece((-0.9, -0.055, z0), (0.9, -0.025, z1), (0.03, 0.008, 0.025), 'white', extra=((-0.45, 0.0, 0.45), (), ()))
        fr = [f for f in bm.faces if abs(f.normal.y) > 0.5]
        setmat(bm, 'decal', fr)
        uv_planar(bm, fr, 'redwhite', lambda co, z0=z0: ((co.x + 0.9) / 1.8, (co.z - z0) / (z1 - z0)))
        m.add(bm)
        for sx in (-1, 1):
            m.add(cbox((0.07, 0.03, 0.07), 0.008, 'steel_d', at=(sx * 0.82, -0.022, (z0 + z1) / 2)))
    # amber lamp on the left post
    lx = -0.82
    m.add(rpiece((lx - 0.07, -0.05, 1.08), (lx + 0.07, 0.04, 1.2), (0.02, 0.02, 0.02), 'black'))
    bm, _ = lathe([(0.0, 0.0), (0.075, 0.0), (0.075, 0.012), (0.07, 0.02), (0.06, 0.045), (0.035, 0.065), (0.0, 0.07)], 12,
                  ['black', 'black', 'amberlens', 'amberlens', 'amberlens', 'amberlens'])
    m.add(xform(bm, frame((lx, -0.05, 1.14), (0, -1, 0))))
    m.at('Lamp', (lx, -0.12, 1.14))
    return m


# ---------------------------------------------------------------- flat ground pieces
def manhole():
    m = Model('ManholeCover', note='Flat cover, 0.8 m across, 2.6 cm proud of the ground.')
    bm, tags = lathe([(0.40, 0.0), (0.40, 0.008), (0.38, 0.014), (0.37, 0.016)], 28, 'iron')
    m.add(bm)
    bm, tags = lathe([(0.366, 0.012), (0.366, 0.022), (0.355, 0.026), (0.0, 0.026)], 28, ['iron', 'iron', 'iron'])
    top = [f for f, s, i in tags if s >= 1]
    uv_planar(bm, top, 'manhole', lambda co: (0.5 + co.x / 0.73, 0.5 + co.y / 0.73))
    m.add(bm)
    return m


def drain_grate():
    m = Model('DrainGrate', note='Gutter grate, flat on the ground.')
    bm = rpiece((-0.32, -0.2, 0.0), (0.32, 0.2, 0.024), (0.012, 0.012, 0.008), 'iron', skip=((2, -1),))
    top = [f for f in bm.faces if f.normal.z > 0.5]
    uv_planar(bm, top, 'drain', lambda co: (0.5 + co.x / 0.64, 0.5 + co.y / 0.4))
    m.add(bm)
    return m


MODELS = [utility_pole, street_lamp, ped_signal, block_wall, wall_pillar, picket_fence, hoarding,
          sign_no_entry, sign_crossing, bollard, traffic_cone, road_barrier, manhole, drain_grate]
