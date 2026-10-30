# Gameplay pieces for kit_leisure.py. Their sizes follow the game's colliders and pivots
# (Assets/_Game/Scripts/Editor/LevelBuildKit.cs, class TrackBuilder):
#   Trampoline      Springboard's visual: pad 1.44 m across, mat top 0.31 m above the origin (ground)
#   SwingTree       chapter-5 Swing: Attach.Rope 4.0 m up and 2.5 m in front of the trunk
#   SwingSeat       the swing seat Block (1.4 x 0.2, 0.7 deep), origin at its centre
#   SwingFrame      the A-frame Swing: beam underside 4.0 m, legs at y = +-1.1
#   Fountain        the plaza floor fountain: grate flush with the paving, jets at x = 0, -0.45, 0.45
#   Raft            the ferry raft MovingPlatform: deck top 0.25 m above the waterline origin
#   SignBoard       Sign/PlantSign: a framed board on two posts, children Board and Posts
#   CheckpointFlag  MakeCheckpoint's flag pole, the pennant a child Flag
#   Target          Target(): board radius 0.475, face 0.16..0.39, children Post, Board and Face
#   SlalomFlag      SlalomGate's pole with a flag (child Flag)
#
# Placing them (game x = Blender X, game y = Blender Z, game z = Blender Y; read attach points from
# the instanced Attach.* transforms rather than hard-coding them):
#   Trampoline   as the Springboard's Visual at local (0, -0.2, 0): origin on the ground, so the
#                squash (scale about the Visual's origin) keeps the feet planted; mat top 0.31.
#   SwingTree    uniform scale s = (pivot.y - groundTop) / 4.0, then move it so Attach.Rope = pivot.
#   SwingSeat    at the seat Block's centre, unscaled (1.4 x 0.2, 0.7 deep, like the collider).
#   SwingFrame   origin at (pivot.x, groundTop); scale up only, by (pivot.y - groundTop) / 4.0.
#   Fountain     origin at (x, groundTop, 0): Attach.Jet0/1/2 at x = 0, -0.45, +0.45 (the jets' order).
#   Raft         origin at the platform's centre - 0.075 in y (deck top = collider top), x scale
#                width / 2.0; Attach.Rope is the ferry rope's height and depth (1.1 up, 0.9 back).
#   SignBoard    root (empty) on the ground; Board.localPosition up = postHeight + boardH / 2,
#                Board scale (boardW / 1.8, boardH / 0.9); Posts scale (boardW / 1.8, (postHeight +
#                boardH / 2) / 1.45). Text goes just in front of Attach.Face.
#   CheckpointFlag  Flag (origin on the pole axis) rides from Attach.FlagLow (0.6) up to 1.93.
#   Target       Post scales up by centreHeight / 2.0; Board and Face (origins at the board centre)
#                go under the ChallengeTarget object; Face is the tinted ring.
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_leisure_geo import *
from kit_leisure_beach import wood_member, flag_sheet, lumpy

PARK_DIRT = (0.60, 0.50, 0.40)


# ---------------------------------------------------------------- Trampoline
def trampoline(rng):
    M = Model('Trampoline', pal={'paint': (0.38, 0.62, 0.84), 'metal': (0.62, 0.64, 0.68), 'dark': (0.40, 0.40, 0.45)},
              dirt=PARK_DIRT, dirt_h=0.12, chips=0.15, chip=(0.85, 0.85, 0.88), ao_dist=0.25, streaks=0.1)
    M.parts = {1: 'paint'}
    zm = 0.31
    # the padded rim: a soft cushion ring (counter-clockwise section in r-z, so it faces out)
    prof = [(0.700, 0.238), (0.719, 0.272), (0.713, 0.320), (0.670, 0.343), (0.588, 0.342), (0.541, 0.324),
            (0.534, 0.293), (0.575, 0.258), (0.700, 0.238)]
    pad, tags = lathe(prof, 24, 'paint', phase=0.0)
    M.add(pad)
    for k in range(8):
        a = 2 * PI * (k + 0.5) / 8
        M.line('top', (0.54 * math.cos(a), 0.54 * math.sin(a)), (0.72 * math.cos(a), 0.72 * math.sin(a)))
    # the jumping mat, a hair under the pad's inner edge
    mat, mtag = lathe([(0.545, zm), (0.30, zm), (0.0, zm)], 24, (0, 'dark', 'keep'), phase=0.0)
    tile_planar(mat, 'mat', lambda co: (0.5 + co.x / 1.09, 0.5 + co.y / 1.09))
    M.add(mat)
    # the steel frame ring under the pad and three U-legs
    fr = torus(0.69, 0.02, 24, 5, 'metalc'); xform(fr, T(0, 0, 0.228)); M.add(fr)
    for k in range(3):
        a = PI / 2 + 2 * PI * k / 3
        pts = []
        for (da, r, z) in ((-0.36, 0.69, 0.228), (-0.37, 0.70, 0.12), (-0.38, 0.715, 0.035), (-0.2, 0.73, 0.022),
                           (0.0, 0.735, 0.02), (0.2, 0.73, 0.022), (0.38, 0.715, 0.035), (0.37, 0.70, 0.12), (0.36, 0.69, 0.228)):
            pts.append((r * math.cos(a + da), r * math.sin(a + da), z))
        M.add(tube(pts, 0.019, 'metal', sides=5))
        for da in (-0.2, 0.2):
            ft = box((-0.035, -0.025, 0.0), (0.035, 0.025, 0.02), 'rubber')
            xform(ft, T(0.73 * math.cos(a + da), 0.73 * math.sin(a + da), 0.0) @ R(a + da, 'Z')); M.add(ft)
    M.extra = {'matTop': zm, 'padRadius': 0.72}
    return M


# ---------------------------------------------------------------- foliage crowns
def clump_spec(C0, Rc, n, rng, rf=(0.34, 0.46), zstop=-0.55):
    C0 = np.array(C0, float); Rc = np.array(Rc, float)
    spec = [(C0 + rng.normal(0, 0.05, 3), Rc * 0.62)]
    ga = PI * (3 - 5 ** 0.5); ph = rng.uniform(0, 2 * PI)
    for k in range(n):
        zf = max(1 - 1.55 * (k + 0.5) / n, zstop)
        rr = math.sqrt(max(0.0, 1 - zf * zf))
        a = ph + ga * k
        d = np.array((rr * math.cos(a), rr * math.sin(a) * 0.9, zf))
        pos = C0 + d * Rc * rng.uniform(0.6, 0.72)
        rad = Rc.mean() * rng.uniform(*rf) * (1.0 + 0.12 * zf)
        spec.append((pos, np.array((rad, rad * 0.95, rad * 0.86))))
    return spec


def crown(spec, ramp, rng, C0, Rc, m='own1', core=0.6, freq=2, crev=0.38, amp=0.13, flat=0.72, front_freq=3):
    """Lumpy foliage clumps (soft blobs), culled where hidden in each other, shaded light on top,
    dark underneath and in the creases; normals blend each clump's roundness with the crown's."""
    C0 = np.asarray(C0, float); Rc = np.asarray(Rc, float)
    cl = [{'c': np.asarray(c, float), 'r': np.asarray(r, float) * np.ones(3), 'f': flat} for c, r in spec]
    zmin = min(c['c'][2] - c['r'][2] * flat for c in cl); zmax = max(c['c'][2] + c['r'][2] * 1.1 for c in cl)
    out = []
    items = list(enumerate(cl))
    if core:
        items.append((-1, {'c': C0, 'r': Rc * core, 'f': 0.8, 'core': True}))
    for i, c in items:
        big_front = c['c'][1] < C0[1] + 0.2 and c['r'].mean() > 0.6
        D, F = geodesic(2 if c.get('core') else (front_freq if big_front else freq))
        r = bumps(D, rng, int(rng.integers(5, 9)), amp, 0.8)
        P = D * r[:, None]
        P[:, 2] = np.where(P[:, 2] < 0, P[:, 2] * c['f'], P[:, 2])
        V = c['c'] + P * c['r']
        inside = np.zeros(len(V), bool); emin = np.full(len(V), 9.0)
        for j, o in enumerate(cl):
            if j == i: continue
            e = ellipsoid_e(V, o['c'], o['r'], o['f'])
            inside |= e < 0.97; emin = np.minimum(emin, e)
        F = [f for f in F if not all(inside[list(f)])]
        if not F: continue
        Nl = (V - c['c']) / c['r']; Nl /= np.linalg.norm(Nl, axis=1, keepdims=True)
        Nc = (V - C0) / Rc; Nc /= np.maximum(np.linalg.norm(Nc, axis=1, keepdims=True), 1e-9)
        hz = (V[:, 2] - zmin) / max(zmax - zmin, 1e-3)
        if c.get('core'):
            col = ramp(0.06 + 0.12 * sstep(C0[2] - Rc[2], C0[2] + Rc[2], V[:, 2]))
            N = Nc
        else:
            cr = sstep(1.28, 1.0, emin)
            s = 0.5 + 0.22 * D[:, 2] + 0.22 * (2 * hz - 1) + 0.10 * np.sum(Nl * Nc, axis=1) - crev * cr + rng.uniform(-0.05, 0.05)
            col = ramp(s)
            hue = rng.uniform(-1, 1)                    # a few clumps redder, a few more golden
            col = col * (1 + 0.10 * hue * np.array((0.15, -0.35, -0.9)))[None, :]
            N = 0.5 * Nl + 0.38 * Nc
            N /= np.linalg.norm(N, axis=1, keepdims=True)
        bm, faces = bm_from(V, F, m)
        lc, lv = lay(bm)[3], lay(bm)[4]
        for v, n_, c_ in zip(bm.verts, N, col):
            v[lc] = tuple(map(float, n_)); v[lv] = tuple(map(float, c_))
        out.append(bm)
    return out


def bend(path, r0, r1, sides, m, n=8, rng=None):
    pts = catmull(path, n)
    radii = list(np.linspace(r0, r1, len(pts)))
    return tube(pts, max(r0, 1e-3), m, sides=sides, radii=radii)


def catmull(points, n):
    P = [Vector(p) for p in points]
    P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


# ---------------------------------------------------------------- SwingTree
AUTUMN = Ramp((0.47, 0.22, 0.13), (0.86, 0.55, 0.22), (0.98, 0.84, 0.46))
BARK = (0.50, 0.40, 0.33)
ROPE_AT = (0.9, -2.5, 4.0)


def swing_tree(rng):
    M = Model('SwingTree', pal={'bark': BARK, 'rope': (0.84, 0.74, 0.55)}, ao_dist=0.6, ao=0.55, grad=(0.78, 3.5))
    M.parts = {1: tuple(AUTUMN.base)}
    bark = (0, 'bark', 'keep')
    rx, ry, rz = ROPE_AT
    # trunk: a stout S, root flare at the foot, on as a leader into the crown
    tp = catmull([(0, 0, -0.12), (0.06, 0.04, 1.2), (-0.02, 0.06, 2.4), (-0.10, 0.14, 3.3), (-0.26, 0.42, 4.5), (-0.34, 0.62, 5.5)], 4)
    rad = [0.44 * (1 - 0.72 * (i / (len(tp) - 1)) ** 0.9) for i in range(len(tp))]
    trunk = tube(tp, 0.44, bark, sides=11, radii=rad, phase=0.0)
    ph = rng.uniform(0, 6)
    for v in trunk.verts:
        z = v.co.z
        if z < 1.0:
            a = math.atan2(v.co.y - 0.04 * z, v.co.x - 0.05 * z)
            k = sstep(0.95, 0.0, z) * (0.55 * max(0.0, math.cos(5 * (a - ph))) ** 3 + 0.14)
            v.co.x = 0.05 * z + (v.co.x - 0.05 * z) * (1 + float(k)); v.co.y = 0.04 * z + (v.co.y - 0.04 * z) * (1 + float(k))
        v.co.x += 0.025 * math.sin(v.co.z * 3.1 + 1); v.co.y += 0.02 * math.cos(v.co.z * 2.3)
    trunk.normal_update()
    tile_natural(trunk, 'bark', rng, 4.0, swap=True)
    M.add(trunk)
    # the swing bough: out over the path, dipping a little where the rope is tied, on to a twiggy tip
    rb = 0.12
    bp = [(-0.04, 0.02, 3.05), (0.22, -0.75, 3.75), (0.62, -1.75, 4.24), (rx, ry, rz + rb), (1.02, -3.0, 4.14), (1.12, -3.38, 4.32)]
    bpts = catmull(bp, 4)
    brad = []
    for p in bpts:
        d = (p - Vector(bp[0])).length / (Vector(bp[-1]) - Vector(bp[0])).length
        brad.append(0.26 * (1 - d) ** 0.85 + 0.03 if d < 0.95 else 0.04)
    # keep the bough's radius at the tie exactly rb
    ti = min(range(len(bpts)), key=lambda i: (bpts[i] - Vector((rx, ry, rz + rb))).length)
    brad[ti] = rb
    bough = tube(bpts, 0.26, bark, sides=9, radii=brad)
    tile_natural(bough, 'bark', rng, 4.0, swap=True)
    M.add(bough)
    # the rope: a few turns lashed round the bough, the end hanging to the tie point
    tng = (bpts[min(ti + 1, len(bpts) - 1)] - bpts[max(ti - 1, 0)]).normalized()
    wrap, wt = lathe([(rb + 0.006, -0.06), (rb + 0.02, -0.05), (rb + 0.024, 0.0), (rb + 0.02, 0.05), (rb + 0.006, 0.06)], 10, 'rope')
    tile_lathe(wrap, wt, 'rope', (0, 1, 2, 3), 10)
    xform(wrap, frame(Vector((rx, ry, rz + rb)), tng)); M.add(wrap)
    knot, _ = lathe([(0, -0.035), (0.028, -0.025), (0.034, 0.0), (0.026, 0.025), (0, 0.034)], 8, 'rope')
    xform(knot, T(rx, ry - 0.005, rz + 0.025)); M.add(knot)
    # limbs into the crown
    limbs = [((-0.1, 0.14, 3.3), (-0.9, 0.45, 4.3), (-1.9, 0.75, 5.1), 0.21),
             ((-0.05, 0.16, 3.6), (0.75, 0.75, 4.6), (1.7, 1.1, 5.3), 0.19),
             ((-0.3, 0.5, 4.6), (-0.7, 1.4, 5.4), (-1.0, 2.0, 5.9), 0.14),
             ((0.03, 0.08, 2.5), (-0.6, -0.3, 3.0), (-1.25, -0.55, 3.35), 0.12),
             ((0.6, -1.5, 4.2), (0.5, -1.8, 4.8), (0.45, -2.0, 5.15), 0.08)]
    for a, b, c, r0 in limbs:
        lb = bend([a, b, c], r0, r0 * 0.3, 6, bark, n=3)
        tile_natural(lb, 'bark', rng, 4.0, swap=True); M.add(lb)
    for a, b in (((1.05, -3.15, 4.2), (1.35, -3.3, 4.55)), ((1.1, -3.3, 4.28), (0.95, -3.55, 4.5))):
        M.add(tube([a, b], 0.022, bark, sides=4))
    # the canopy: a broad crown over the trunk, a lobe reaching over the bough, a small tuft at its tip
    spec = clump_spec((-0.05, 0.55, 5.75), (2.9, 2.2, 1.65), 12, rng, rf=(0.38, 0.5))
    spec += [((0.75, -1.65, 5.05), (0.95, 0.85, 0.72)), ((0.2, -1.2, 5.45), (0.9, 0.8, 0.7)),
             ((1.35, -1.1, 5.2), (0.8, 0.75, 0.65)), ((1.42, -3.3, 4.82), (0.42, 0.4, 0.34)),
             ((-1.55, -0.5, 3.75), (0.62, 0.58, 0.5)), ((-2.2, 0.6, 5.0), (0.9, 0.8, 0.72)), ((2.0, 0.9, 5.1), (0.95, 0.85, 0.75))]
    for bm in crown(spec, AUTUMN, rng, (0.0, 0.2, 5.6), (3.0, 2.6, 1.8), core=0.55):
        M.add(bm)
    M.at('Rope', ROPE_AT)
    M.extra = {'rope': list(ROPE_AT), 'trunkRadius': 0.44}
    return M


# ---------------------------------------------------------------- SwingSeat
def swing_seat(rng):
    M = Model('SwingSeat', pal={'paint': (0.72, 0.54, 0.37), 'metal': (0.40, 0.40, 0.43)}, ao_dist=0.12, grad=(0.92, 0.2))
    M.ground = None
    M.parts = {1: 'paint'}
    W, Dp = 1.4, 0.7
    # three thick top boards
    bw = (Dp - 0.04) / 3
    for k in range(3):
        y = -Dp / 2 + 0.02 + bw * (k + 0.5)
        b = rpiece((-W / 2 + 0.005 * k, y - bw / 2 + 0.006, 0.025), (W / 2 - 0.004 * k, y + bw / 2 - 0.006, 0.10), (0.02, 0.014, 0.014), 'paintk')
        tile_box(b, 'grain', rng, 1.4); M.add(b)
    # an apron round the underside: front, back and the two ends
    for y in (-Dp / 2 + 0.025, Dp / 2 - 0.025):
        b = rpiece((-W / 2 + 0.02, y - 0.025, -0.10), (W / 2 - 0.02, y + 0.025, 0.03), 0.012, 'paintk')
        tile_box(b, 'grain', rng, 1.4); M.add(b)
    for x in (-W / 2 + 0.045, W / 2 - 0.045):
        b = rpiece((x - 0.025, -Dp / 2 + 0.05, -0.10), (x + 0.025, Dp / 2 - 0.05, 0.03), 0.012, 'paintk')
        tile_box(b, 'grain', rng, 1.4); M.add(b)
    # iron corner straps
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(box((sx * (W / 2 - 0.10) - 0.06, sy * (Dp / 2 + 0.002) - 0.006, -0.09), (sx * (W / 2 - 0.10) + 0.06, sy * (Dp / 2 + 0.002) + 0.006, 0.02), 'metalc'))
            M.add(box((sx * (W / 2 + 0.002) - 0.006, sy * (Dp / 2 - 0.08) - 0.05, -0.09), (sx * (W / 2 + 0.002) + 0.006, sy * (Dp / 2 - 0.08) + 0.05, 0.02), 'metalc'))
    # rope eyes at both ends: a ring on a plate, standing up and facing the camera
    for sx in (-1, 1):
        x = sx * 0.6
        pl, _ = lathe([(0, 0.10), (0.04, 0.10), (0.036, 0.11), (0, 0.112)], 10, 'metalc'); xform(pl, T(x, 0, 0)); M.add(pl)
        ey = torus(0.038, 0.009, 12, 5, 'metalc'); xform(ey, T(x, 0, 0.152) @ R(PI / 2, 'X')); M.add(ey)
        M.at('Rope' + ('L' if sx < 0 else 'R'), (x, 0, 0.19))
    M.at('Rope', (0, 0, 0.10))
    return M


# ---------------------------------------------------------------- SwingFrame
def swing_frame(rng):
    M = Model('SwingFrame', pal={'paint': (0.66, 0.50, 0.36), 'metal': (0.30, 0.31, 0.34), 'conc': (0.80, 0.78, 0.74)},
              dirt=PARK_DIRT, dirt_h=0.3, chips=0.3, chip=(0.62, 0.48, 0.36), ao_dist=0.35)
    M.parts = {1: 'paint'}
    zu, bh = 4.0, 0.2
    beam = member((0, -1.32, zu + bh / 2), (0, 1.32, zu + bh / 2), bh, bh, 'paintk')
    tile_natural(beam, 'grain', rng, 2.6); M.add(beam)
    xf = 1.48
    for yc in (-1.1, 1.1):
        for sx in (-1, 1):
            y = yc + sx * 0.075
            foot = Vector((sx * xf, y, -0.03)); top = Vector((-sx * 0.13, y, zu + 0.24))
            lg = member(foot, top, 0.14, 0.14, 'paintk', up=(0, 1, 0))
            tile_natural(lg, 'grain', rng, 2.6); M.add(lg)
            ft = cbox((0.28, 0.24, 0.07), 0.02, 'conc'); xform(ft, T(sx * (xf - 0.01), y, 0.015)); M.add(ft)
        # the tie across each A
        zt = 1.35
        k = (zt + 0.03) / (zu + 0.27)
        xt = xf - (xf + 0.13) * k
        tie = member((-xt - 0.06, yc - 0.16 * (1 if yc < 0 else -1), zt), (xt + 0.06, yc - 0.16 * (1 if yc < 0 else -1), zt), 0.05, 0.13, 'paintk', plain=False)
        tile_natural(tie, 'grain', rng, 2.6); M.add(tie)
        # bolt plate where the legs cross under the beam
        pl = cbox((0.16, 0.02, 0.16), 0.01, 'metal')
        xform(pl, T(0, yc - 0.16 * (1 if yc < 0 else -1), zu - 0.02)); M.add(pl)
        for bx in (-0.045, 0.045):
            bt, _ = lathe([(0, 0), (0.016, 0), (0.014, 0.01), (0, 0.012)], 6, 'metalc')
            sgn = -1 if yc < 0 else 1
            xform(bt, T(bx, yc - 0.16 * sgn - 0.01 * sgn, zu - 0.02) @ R(sgn * PI / 2, 'X')); M.add(bt)
        # knee brace from the beam down to the frame
        sg = 1 if yc > 0 else -1
        kb = member((0, sg * 0.55, zu), (0, sg * 0.98, zu - 0.42), 0.09, 0.07, 'paintk')
        tile_natural(kb, 'grain', rng, 2.6); M.add(kb)
    # the swing hanger under the beam's centre: a plate, a bolt either side, an eye
    pl = cbox((0.10, 0.16, 0.02), 0.006, 'metal'); xform(pl, T(0, 0, zu - 0.008)); M.add(pl)
    ey = torus(0.03, 0.008, 10, 5, 'metalc'); xform(ey, T(0, 0, zu - 0.045) @ R(PI / 2, 'X')); M.add(ey)
    M.at('Rope', (0, 0, zu))
    M.extra = {'beamUnderside': zu, 'legsY': [-1.1, 1.1]}
    return M


# ---------------------------------------------------------------- Fountain
def fountain(rng):
    M = Model('Fountain', pal={'paint': (0.84, 0.80, 0.74), 'metal': (0.62, 0.63, 0.65), 'water': (0.30, 0.48, 0.52),
                               'brass': (0.80, 0.66, 0.40)}, ao_dist=0.1, ao=0.5, grad=(0.95, 0.05))
    M.parts = {1: 'paint'}
    rg, r0, r1 = 0.56, 0.645, 0.80
    gr, gt = lathe([(rg + 0.004, 0.0), (rg, 0.012, 'S'), (0.0, 0.014)], 24, (0, 'metal', 'keep'), phase=0.0)
    tile_planar(gr, 'grate', lambda co: (0.5 + co.x / (2 * rg), 0.5 + co.y / (2 * rg)))
    M.add(gr)
    # the gutter round the grate, a film of water in it
    gu, _ = lathe([(r0 + 0.004, 0.03), (r0, 0.0, 'S'), (r0 - 0.01, -0.012), (rg + 0.012, -0.012), (rg + 0.002, 0.004)], 28, (0, 'water', 'white'), phase=0.0)
    M.add(gu)
    # stone kerb: ten curved blocks with chamfered edges
    n = 10; gap = 0.012
    for k in range(n):
        a0 = 2 * PI * k / n + gap / 0.72; a1 = 2 * PI * (k + 1) / n - gap / 0.72
        rm = (r0 + r1) / 2
        path = [(rm * math.cos(a), rm * math.sin(a), 0.0) for a in np.linspace(a0, a1, 5)]
        sec = [(y, x) for (x, y) in chamfer_rect(r1 - r0, 0.09, 0.022)]
        sec = [(a + 0.005, b) for a, b in sec]
        st = sweep(path, (0, 0, 1), sec, 'own1k')
        tile_natural(st, 'stone', rng, 0.6)
        tone = 1.0 + rng.uniform(-0.05, 0.04)
        base = Vector(s2l(M.pal['paint']))

        def col(co, tone=tone):
            r = math.hypot(co.x, co.y)
            wet = sstep(0.70, 0.66, r) * 0.22 if co.z > -0.02 else 0.0
            return base * tone * (1 - float(wet))
        set_vc(st, col)
        M.add(st)
    # three jet nozzles: brass rosettes with a dark bore
    jets = [(0.0, 0.0), (-0.45, 0.0), (0.45, 0.0)]
    for i, (x, y) in enumerate(jets):
        nz, _ = lathe([(0.052, 0.010), (0.052, 0.020, 'S'), (0.040, 0.030), (0.020, 0.034, 'S'), (0.016, 0.026, 'S'), (0.0, 0.024)],
                      12, ['brass', 'brass', 'brass', 'dark', 'dark'])
        xform(nz, T(x, y, 0)); M.add(nz)
        M.at('Jet%d' % i, (x, y, 0.034))
    M.extra = {'jets': [[x, y, 0.034] for x, y in jets], 'top': 0.055}
    return M


# ---------------------------------------------------------------- Raft
def raft(rng):
    M = Model('Raft', pal={'paint': (0.74, 0.58, 0.41), 'accent': (0.38, 0.58, 0.66), 'woodd': (0.56, 0.42, 0.31),
                           'rope': (0.86, 0.77, 0.58), 'metal': (0.34, 0.35, 0.38)},
              dirt=(0.42, 0.50, 0.46), dirt_h=0.12, dirt_a=0.5, chips=0.8, chip=(0.68, 0.62, 0.56), ao_dist=0.3)
    M.ground = None
    M.parts = {1: 'paint', 2: 'accent'}
    top = 0.25
    # deck boards along X (they stretch cleanly with the raft)
    nb = 6; bw = 1.46 / nb
    for k in range(nb):
        y = -0.73 + bw * (k + 0.5)
        dx = rng.uniform(-0.025, 0.025)
        b = member((-1.0 + dx, y, top - 0.03 - rng.uniform(0, 0.004)), (1.0 + dx * 0.5, y, top - 0.03), bw - 0.014, 0.06, 'paintk')
        tile_natural(b, 'grain', rng, 2.0); M.add(b)
    # bumper logs along the front and back edges
    for sy in (-1, 1):
        lg = tube([(-1.03, sy * 0.80, top - 0.085), (1.03, sy * 0.80, top - 0.085)], 0.085, 'woodd', sides=8)
        tile_natural(lg, 'grain', rng, 2.0); M.add(lg)
        for x in (-1.03, 1.03):
            ec, _ = lathe([(0, 0), (0.08, 0.0), (0, 0.008)], 8, 'woodl')
            xform(ec, T(x, sy * 0.80, top - 0.085) @ R(PI / 2 * (1 if x > 0 else -1), 'Y')); M.add(ec)
        # rope lashings round the logs
        for x in (-0.6, 0.6):
            loop = [(x, sy * 0.80 + 0.105 * math.cos(a), top - 0.085 + 0.105 * math.sin(a)) for a in np.linspace(0, 2 * PI, 7)[:-1]]
            ls = tube(loop, 0.014, 'rope', sides=4, closed_path=True, up=lambda i, p, t: Vector((1, 0, 0)))
            tile_natural(ls, 'rope', None, 0.4); M.add(ls)
    # four barrels under the deck, lying along X
    hoop = 'darkg'
    prof = [(0, -0.43), (0.165, -0.43, 'S'), (0.19, -0.37, 'S'), (0.198, -0.26, 'S'), (0.202, -0.20, 'S'), (0.206, 0.0),
            (0.202, 0.20, 'S'), (0.198, 0.26, 'S'), (0.19, 0.37, 'S'), (0.165, 0.43, 'S'), (0, 0.43)]
    mats = ['accent', 'accent', 'accent', 'metal', 'accent', 'accent', 'metal', 'accent', 'accent', 'accent']
    for sx in (-1, 1):
        for sy in (-1, 1):
            bl, _ = lathe(prof, 9, mats, phase=0.5)
            xform(bl, T(sx * 0.475, sy * 0.57, -0.035) @ R(PI / 2, 'Y') @ R(rng.uniform(0, 1), 'Z')); M.add(bl)
    # the ferry rope's guide: a post at the back with a ring the rope runs through
    py, rz_ = 0.72, 1.10
    ps = tube([(0, py, top - 0.02), (0, py, rz_ + 0.12)], 0.05, 'woodd', sides=8)
    tile_natural(ps, 'grain', rng, 1.5); M.add(ps)
    cap, _ = lathe([(0, rz_ + 0.11), (0.058, rz_ + 0.11), (0.05, rz_ + 0.15), (0, rz_ + 0.16)], 8, 'woodd'); xform(cap, T(0, py, 0)); M.add(cap)
    M.add(member((0, py, rz_), (0, 0.85, rz_), 0.03, 0.03, 'metalc', plain=True))
    rg_ = torus(0.06, 0.012, 12, 5, 'metalc'); xform(rg_, T(0, 0.90, rz_) @ R(PI / 2, 'Y')); M.add(rg_)
    cl = cbox((0.04, 0.16, 0.035), 0.01, 'metalc'); xform(cl, T(0.0, py - 0.06, 0.55)); M.add(cl)
    M.at('Rope', (0, 0.90, rz_))
    M.extra = {'deckTop': top, 'length': 2.0}
    return M


# ---------------------------------------------------------------- SignBoard
def signboard(rng):
    M = Model('SignBoard', pal={'paint': (0.97, 0.91, 0.76), 'accent': (0.56, 0.41, 0.30)},
              dirt=PARK_DIRT, dirt_h=0.3, chips=0.4, chip=(0.7, 0.58, 0.45), ao_dist=0.25)
    M.empty_root = True
    M.parts = {1: 'paint', 2: 'accent'}
    W, H, zb = 1.8, 0.9, 1.0
    zc = zb + H / 2
    M.child('Board', (0, 0, zc)); M.child('Posts', (0, 0, 0))
    # the face: three painted planks, recessed in a stained frame, a capping board on top
    pw = (H - 0.10) / 3
    for k in range(3):
        z0 = zb + 0.05 + pw * k
        b = rpiece((-W / 2 + 0.05, -0.012, z0 + 0.004), (W / 2 - 0.05, 0.03, z0 + pw - 0.004), (0.008, 0.006, 0.008), 'paintk')
        tile_box(b, 'pgrain', rng, 2.0); M.add(b, 'Board')
    fr = [((-W / 2, zb + 0.035), (W / 2, zb + 0.035), 0.075), ((-W / 2, zb + H - 0.035), (W / 2, zb + H - 0.035), 0.075)]
    for (x0, z0), (x1, z1), h in fr:
        b = member((x0, -0.01, z0), (x1, -0.01, z1), 0.075, h, 'accentk', up=(0, 0, 1))
        tile_natural(b, 'grain', rng, 2.0); M.add(b, 'Board')
    for x in (-W / 2 + 0.035, W / 2 - 0.035):
        b = member((x, -0.01, zb), (x, -0.01, zb + H), 0.075, 0.07, 'accentk', up=(0, 1, 0))
        tile_natural(b, 'grain', rng, 2.0); M.add(b, 'Board')
    cap = member((-W / 2 - 0.07, 0.0, zb + H + 0.035), (W / 2 + 0.07, 0.0, zb + H + 0.035), 0.16, 0.06, 'accentk')
    tile_natural(cap, 'grain', rng, 2.0); M.add(cap, 'Board')
    for x in (-W / 2 + 0.035, W / 2 - 0.035):
        for z in (zb + 0.035, zb + H - 0.035):
            nl, _ = lathe([(0, 0), (0.012, 0), (0.01, 0.006), (0, 0.008)], 6, 'metalc')
            xform(nl, T(x, -0.048, z) @ R(-PI / 2, 'X')); M.add(nl, 'Board')
    # two posts behind the board, from the ground up to the board's middle
    for x in (-0.62, 0.62):
        p = member((x, 0.095, 0.0), (x, 0.095, zc), 0.12, 0.12, 'accentk', up=(0, 1, 0))
        tile_natural(p, 'grain', rng, 2.0); M.add(p, 'Posts')
    M.at('Face', (0, -0.012, zc), 'Board')
    M.extra = {'board': [W, H], 'boardBottom': zb, 'face': [0, -0.012, zc]}
    return M


# ---------------------------------------------------------------- CheckpointFlag
def checkpoint_flag(rng):
    M = Model('CheckpointFlag', pal={'paint': (0.97, 0.96, 0.93), 'metal': (0.68, 0.70, 0.72), 'conc': (0.80, 0.78, 0.74)},
              dirt=PARK_DIRT, dirt_h=0.15, chips=0.3, chip=(0.6, 0.45, 0.35), ao_dist=0.2)
    M.parts = {1: 'paint'}
    zh = 1.93
    M.child('Flag', (0, 0, zh))
    base, _ = lathe([(0, 0), (0.13, 0.0), (0.125, 0.05, 'S'), (0.10, 0.07), (0.04, 0.08, 'S'), (0, 0.08)], 12, 'conc'); M.add(base)
    M.add(tube([(0, 0, 0.06), (0, 0, 2.20)], 0.028, 'metal', sides=8))
    fn, _ = lathe([(0, 2.18), (0.034, 2.19), (0.05, 2.23), (0.034, 2.27), (0, 2.285)], 10, 'brass'); M.add(fn)
    # halyard and cleat
    M.add(tube([(0.03, -0.005, 1.0), (0.032, -0.005, 2.17)], 0.004, 'rope', sides=3, caps=False))
    cl = cbox((0.02, 0.025, 0.11), 0.006, 'dark'); xform(cl, T(0.035, 0, 1.0)); M.add(cl)
    # the pennant: hoisted on a sleeve, tapering to the fly, rippling
    hh = 0.36

    def shape(bm):
        for v in bm.verts:
            k = max(0.0, (v.co.x - 0.03) / 0.6)
            v.co.z = zh + (v.co.z - zh) * (1 - 0.9 * k)
        bm.normal_update(); return bm
    fl = flag_sheet(0.03, 0.63, zh - hh / 2, zh + hh / 2, 9, 0.045, lambda s, t: 'paintk', thick=0.005, droop=0.03)
    shape(fl)
    tile_planar(fl, 'flag', lambda co: ((co.x - 0.03) / 0.6, (co.z - zh + hh / 2) / hh))
    M.add(fl, 'Flag')
    sl = tube([(0.032, 0.002, zh - hh / 2), (0.032, 0.002, zh + hh / 2)], 0.012, 'paintc', sides=6)
    M.add(sl, 'Flag')
    M.at('FlagLow', (0, 0, 0.60))
    M.extra = {'flagHoist': zh, 'flagLow': 0.60, 'pole': 2.2}
    return M


# ---------------------------------------------------------------- Target
def target(rng):
    M = Model('Target', pal={'paint': (0.98, 0.97, 0.94), 'white': (0.96, 0.95, 0.92), 'red': (0.86, 0.33, 0.28),
                             'metal': (0.44, 0.50, 0.56)},
              dirt=PARK_DIRT, dirt_h=0.25, chips=0.4, chip=(0.62, 0.44, 0.32), ao_dist=0.18)
    M.empty_root = True
    M.parts = {1: 'paint'}
    H0, py = 2.0, 0.75
    M.child('Post', (0, 0, 0)); M.child('Board', (0, 0, H0)); M.child('Face', (0, 0, H0))
    ft = cbox((0.22, 0.22, 0.03), 0.008, 'metal'); xform(ft, T(0, py, 0.015)); M.add(ft, 'Post')
    M.add(tube([(0, py, 0.0), (0, py, H0 + 0.05)], 0.045, 'metal', sides=8), 'Post')
    toF = T(0, 0, H0) @ R(PI / 2, 'X')        # lathe +Z -> toward the camera (-Y)
    rim = [(0, -0.05), (0.43, -0.05), (0.466, -0.042), (0.477, -0.012), (0.474, 0.032), (0.456, 0.052), (0.418, 0.052),
           (0.394, 0.04), (0.388, 0.021)]
    bd, _ = lathe(rim, 28, 'white', phase=0.0); xform(bd, toF); M.add(bd, 'Board')
    be, _ = lathe([(0.162, 0.02), (0.16, 0.032), (0.148, 0.044), (0.10, 0.05), (0.0, 0.052)], 28, 'red', phase=0.0)
    xform(be, toF); M.add(be, 'Board')
    fc, ft_ = lathe([(0.392, 0.021), (0.28, 0.025), (0.16, 0.028)], 28, 'paintk', phase=0.0)
    tile_planar(fc, 'target', lambda co: (0.5 + co.x / 0.78, 0.5 + co.y / 0.78))
    xform(fc, toF); M.add(fc, 'Face')
    # the bracket back to the post, a clamp round it, a cap on top
    M.add(member((0, 0.04, H0), (0, py - 0.03, H0), 0.06, 0.06, 'metal'), 'Board')
    bp = cbox((0.16, 0.02, 0.16), 0.008, 'metal'); xform(bp, T(0, 0.055, H0)); M.add(bp, 'Board')
    cl, _ = lathe([(0, H0 - 0.07), (0.062, H0 - 0.07, 'S'), (0.062, H0 + 0.06, 'S'), (0.04, H0 + 0.09), (0, H0 + 0.10)], 10, 'metal')
    xform(cl, T(0, py, 0)); M.add(cl, 'Board')
    M.at('Center', (0, 0, H0))
    M.extra = {'boardRadius': 0.475, 'faceRadius': [0.16, 0.39], 'center': H0, 'postY': py}
    return M


# ---------------------------------------------------------------- SlalomFlag
def slalom_flag(rng):
    M = Model('SlalomFlag', pal={'paint': (0.98, 0.97, 0.94), 'white': (0.96, 0.95, 0.92), 'red': (0.86, 0.33, 0.28)},
              ao_dist=0.15)
    M.parts = {1: 'paint'}
    zh = 1.36
    M.child('Flag', (0, 0, zh))
    base, _ = lathe([(0, 0), (0.10, 0.0), (0.095, 0.03, 'S'), (0.06, 0.045), (0.03, 0.05, 'S'), (0, 0.05)], 12, 'rubber'); M.add(base)
    prof = [(0.022, 0.04)]; mats = []
    zs = list(np.arange(0.04, 1.58, 0.22)) + [1.58]
    for k in range(len(zs) - 1):
        prof.append((0.022, zs[k + 1], 'S')); mats.append('red' if k % 2 == 0 else 'white')
    prof.append((0.0, 1.585)); mats.append('red')
    pole, _ = lathe(prof, 8, mats); M.add(pole)
    cap, _ = lathe([(0, 1.58), (0.03, 1.585), (0.032, 1.61), (0, 1.63)], 8, 'rubber'); M.add(cap)
    fl = flag_sheet(0.025, 0.47, zh - 0.17, zh + 0.17, 7, 0.035, lambda s, t: 'paintk', thick=0.005, droop=0.02)
    tile_planar(fl, 'flag', lambda co: ((co.x - 0.025) / 0.445, (co.z - zh + 0.17) / 0.34))
    M.add(fl, 'Flag')
    M.add(tube([(0.026, 0.002, zh - 0.17), (0.026, 0.002, zh + 0.17)], 0.011, 'paintc', sides=6), 'Flag')
    M.extra = {'flagHoist': zh, 'pole': 1.6}
    return M


BUILDERS = [('Trampoline', trampoline), ('SwingTree', swing_tree), ('SwingSeat', swing_seat), ('SwingFrame', swing_frame),
            ('Fountain', fountain), ('Raft', raft), ('SignBoard', signboard), ('CheckpointFlag', checkpoint_flag),
            ('Target', target), ('SlalomFlag', slalom_flag)]
