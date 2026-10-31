# Street kit models, part 4: the shopping street's and the home street's small life, in the
# everyday-town look: an A-frame sign board, a standing banner flag, an electrical cabinet, a row of
# bicycle hoops, a pair of wheelie bins and a doorstep group of pots.
import math
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from kit_street_geo import (PI, lathe, sweep, tube, cbox, rpiece, prism, ball, xform, T, R, S, frame, setmat,
                            faces_facing, uv_planar, uv_long, grime_cyl, lay, bm_from, fix_normals, new_bm, merge, join)
from kit_street_build import Model
from kit_street_m1 import front_plate, decal_faces
from kit_street_m2 import leaf_ball, flower


# ---------------------------------------------------------------- A-frame sign board
def sign_board_a():
    m = Model('SignBoardA', paint=(0.30, 0.26, 0.22),
              note='Folding A-frame pavement board: a chalk menu on the front face, a shop poster on the back '
                   '(turn it 180 degrees to show that); part 1 = the frame.')
    H, W, lean = 0.96, 0.58, 0.24
    a = math.atan2(lean, H)
    L = math.hypot(lean, H)
    for sg, region in ((-1, 'aboard1'), (1, 'aboard2')):
        panel = new_bm()
        # the board inside a frame of four rails, built upright then leant from the hinge at the top
        b = cbox((W - 0.08, 0.018, L - 0.1), 0.004, 'paint')
        fr = faces_facing(b, (0, sg, 0), 0.9)
        setmat(b, 'decal', fr)
        uv_planar(b, fr, region, lambda co, sg=sg: (0.5 - sg * co.x / (W - 0.08), 0.5 + co.z / (L - 0.1)))
        merge(panel, b)
        for x in (-W / 2 + 0.02, W / 2 - 0.02):
            merge(panel, cbox((0.04, 0.032, L), 0.008, 'paint', at=(x, 0, 0)))
        for z in (-L / 2 + 0.02, L / 2 - 0.03):
            merge(panel, cbox((W, 0.032, 0.04), 0.008, 'paint', at=(0, 0, z)))
        M = T(0, sg * lean / 2, H / 2) @ R(sg * a, 'X')
        m.add(xform(panel, M))
    for x in (-W / 2 + 0.02, W / 2 - 0.02):         # the hinge pins and a chain between the legs
        m.add(tube([(x, -0.01, H - 0.02), (x, 0.01, H - 0.02)], 0.012, 'steel_d', sides=5))
        m.add(tube([(x, -lean * 0.45, 0.42), (x, lean * 0.45, 0.42)], 0.005, 'steel_d', sides=4))
    m.at('Top', (0, 0, H))
    return m


# ---------------------------------------------------------------- standing banner flag
def banner_flag():
    m = Model('BannerFlag', paint=(0.84, 0.28, 0.22), paint2=(0.98, 0.82, 0.30),
              note='A tall shop banner on a pole with a weighted base; part 1 = the cloth, part 2 = its top band. '
                   'White shapes stand in for lettering (no text).')
    base, _ = lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.08), (0.17, 0.12), (0.06, 0.15), (0.03, 0.17), (0.0, 0.17)], 12,
                    ['rubber', 'rubber', 'rubber', 'rubber', 'rubber', 'rubber'])
    m.add(base)
    Hp = 2.75
    pole, _ = lathe([(0.017, 0.15), (0.017, Hp), (0.012, Hp + 0.02), (0.0, Hp + 0.02)], 8, ['white', 'white', 'white'])
    grime_cyl(pole)
    m.add(pole)
    x0, x1, z0, z1 = 0.03, 0.5, 0.9, 2.62
    m.add(tube([(0.0, 0.0, z1 + 0.04), (x1 + 0.03, 0.0, z1 + 0.04)], 0.011, 'white', sides=5))
    # the cloth: a thin slab, rippled a little, a coloured band at the top, white shapes on its face
    nz = 8
    V, F = [], []
    for k in range(nz + 1):
        z = z0 + (z1 - z0) * k / nz
        dy = 0.015 * math.sin(k * 1.3)
        for x in (x0, x1):
            V.append((x, dy - 0.004, z)); V.append((x, dy + 0.004, z))
    for k in range(nz):
        a, b = k * 4, (k + 1) * 4
        F += [[a, a + 2, b + 2, b], [a + 1, b + 1, b + 3, a + 3], [a + 2, a + 3, b + 3, b + 2], [a, b, b + 1, a + 1]]
    F += [[0, 1, 3, 2], [nz * 4, nz * 4 + 2, nz * 4 + 3, nz * 4 + 1]]
    mats = []
    for k in range(nz):
        mats += ['paint2' if k == nz - 1 else 'paint'] * 4
    mats += ['paint', 'paint2']
    cloth, _ = bm_from(V, F, mats)
    m.add(fix_normals(cloth))
    for z in np.linspace(z0 + 0.15, z1 - 0.1, 5):
        m.add(tube([(0.0, -0.02, z), (0.0, 0.02, z)], 0.022, 'white', sides=6, caps=False))

    def ripple(z):
        k = (z - z0) / (z1 - z0) * nz
        return 0.015 * math.sin(k * 1.3)
    xc = (x0 + x1) / 2
    shapes = [('disc', z1 - 0.42, 0.13), ('bar', z1 - 0.72, 0.15), ('bar', z1 - 0.95, 0.12), ('bar', z1 - 1.18, 0.15),
              ('bar', z1 - 1.41, 0.1), ('dot', z0 + 0.12, 0.03)]
    for kind, z, s in shapes:
        y = ripple(z) - 0.007
        if kind == 'disc':
            pts = [(xc + s * math.cos(2 * PI * i / 12), z + s * math.sin(2 * PI * i / 12)) for i in range(12)]
            inner = [(xc + 0.06 * math.cos(2 * PI * i / 10), z + 0.06 * math.sin(2 * PI * i / 10)) for i in range(10)]
            m.add(xform(prism(pts, 0.004, 'white'), T(0, y - 0.002, 0)))
            m.add(xform(prism(inner, 0.004, 'paint'), T(0, y - 0.005, 0)))
        elif kind == 'bar':
            pts = [(xc - s, z - 0.07), (xc + s, z - 0.07), (xc + s, z + 0.07), (xc - s, z + 0.07)]
            m.add(xform(prism(pts, 0.004, 'white'), T(0, y - 0.002, 0)))
            pts = [(xc - 0.025, z - 0.1), (xc + 0.025, z - 0.1), (xc + 0.025, z + 0.1), (xc - 0.025, z + 0.1)]
            m.add(xform(prism(pts, 0.004, 'white'), T(0, y - 0.002, 0)))
        else:
            for dx in (-0.12, 0.0, 0.12):
                pts = [(xc + dx + s * math.cos(2 * PI * i / 8), z + s * math.sin(2 * PI * i / 8)) for i in range(8)]
                m.add(xform(prism(pts, 0.004, 'white'), T(0, y - 0.002, 0)))
    m.at('Top', (0, 0, Hp))
    return m


# ---------------------------------------------------------------- electrical cabinet
def utility_box():
    m = Model('UtilityBox', paint=(0.80, 0.81, 0.77),
              note='A street electrical cabinet on a concrete plinth: two doors, a vent, a warning sticker; part 1 = paint.')
    m.add(rpiece((-0.5, -0.27, 0.0), (0.5, 0.27, 0.12), (0.02, 0.02, 0.02), 'concrete', skip=((2, -1),)))
    W, D, H = 0.9, 0.42, 1.32
    body = rpiece((-W / 2, -D / 2, 0.12), (W / 2, D / 2, 0.12 + H), (0.02, 0.02, 0.02), 'paint',
                  extra=((0.0,), (), ()), skip=((2, -1),))
    m.add(body)
    m.add(rpiece((-W / 2 - 0.03, -D / 2 - 0.035, 0.12 + H), (W / 2 + 0.03, D / 2 + 0.03, 0.12 + H + 0.05), (0.015, 0.015, 0.015), 'paint'))
    y = -D / 2 - 0.004
    m.add(cbox((0.006, 0.006, H - 0.12), 0.0, 'steel_d', at=(0, y, 0.12 + H / 2)))     # the doors' meeting line
    for sx in (-1, 1):
        m.add(cbox((0.03, 0.02, 0.16), 0.008, 'steel_d', at=(sx * 0.07, y - 0.008, 0.12 + 0.72)))
        for k in range(5):                          # vent louvres low on each door
            m.add(cbox((0.26, 0.012, 0.016), 0.004, 'steel_d', at=(sx * 0.24, y - 0.002, 0.3 + 0.045 * k)))
    m.add(front_plate((0.16, 0.006, 0.16), (-0.24, y - 0.004, 0.12 + 1.02), 'usticker', 'paint', r=0.002))
    m.add(front_plate((0.14, 0.006, 0.07), (0.24, y - 0.004, 0.12 + 1.08), 'plate', 'paint', r=0.002))
    m.at('Top', (0, 0, 0.12 + H + 0.05))
    return m


# ---------------------------------------------------------------- bicycle hoops
def bike_rack():
    m = Model('BikeRack', paint=(0.36, 0.40, 0.42),
              note='Three inverted-U bicycle hoops in a row along X, 0.9 m apart (lean a Bicycle along one); part 1 = paint.')
    for x in (-0.9, 0.0, 0.9):
        pts = []
        for k in range(9):
            a = PI * k / 8
            pts.append((x - 0.28 * math.cos(a), 0.0, 0.55 + 0.28 * math.sin(a)))
        pts = [(x - 0.28, 0.0, 0.0)] + pts + [(x + 0.28, 0.0, 0.0)]
        m.add(tube(pts, 0.024, 'paint', sides=7))
        for sx in (-1, 1):
            m.add(cbox((0.11, 0.11, 0.02), 0.005, 'steel_d', at=(x + sx * 0.28, 0, 0.01)))
        m.add(tube([(x - 0.28, 0.0, 0.32), (x + 0.28, 0.0, 0.32)], 0.016, 'paint', sides=6))
    for k, x in enumerate((-0.45, 0.45)):            # two parking-space marks on the ground
        m.add(cbox((0.05, 0.6, 0.004), 0.0, 'white', at=(x, -0.05, 0.002)))
    m.at('Slot0', (-0.9, 0, 0)); m.at('Slot1', (0, 0, 0)); m.at('Slot2', (0.9, 0, 0))
    return m


# ---------------------------------------------------------------- wheelie bins
def wheelie_bin(paint, x):
    out = []
    W, D, H = 0.58, 0.72, 0.98

    def taper(X):
        X = X.copy()
        t = np.clip(X[:, 2] / H, 0, 1)
        X[:, 0] *= 0.9 + 0.1 * t
        X[:, 1] = X[:, 1] * (0.9 + 0.1 * t) + 0.03 * (1 - t)
        return X
    out.append(rpiece((-W / 2, -D / 2, 0.06), (W / 2, D / 2, H), (0.04, 0.04, 0.03), paint,
                      extra=((), (), (0.5,)), skip=((2, 1),), deform=taper))
    lid = rpiece((-W / 2 - 0.02, -D / 2 - 0.04, H), (W / 2 + 0.02, D / 2 + 0.02, H + 0.07), (0.03, 0.03, 0.025), paint)
    out.append(lid)
    out.append(cbox((W * 0.8, 0.05, 0.05), 0.015, 'black', at=(0, D / 2 + 0.05, H - 0.02)))
    for sx in (-1, 1):
        wh, _ = lathe([(0.0, -0.035), (0.1, -0.035), (0.1, 0.035), (0.0, 0.035)], 10, 'rubber')
        out.append(xform(wh, T(sx * (W / 2 - 0.02), D / 2 - 0.08, 0.1) @ R(PI / 2, 'Y')))
    out.append(cbox((W * 0.62, 0.016, 0.05), 0.006, paint, at=(0, -D / 2 - 0.01, H - 0.12)))
    return [xform(b, T(x, 0, 0)) for b in out]


def bin_pair():
    m = Model('BinPair', paint=(0.32, 0.50, 0.40), paint2=(0.36, 0.46, 0.60),
              note='Two wheelie bins side by side, lids to the front; part 1 = the left bin, part 2 = the right one.')
    for b in wheelie_bin('paintp', -0.33) + wheelie_bin('paint2p', 0.33):
        m.add(b)
    return m


# ---------------------------------------------------------------- doorstep pots
def pot_group():
    m = Model('PotGroup', paint=(0.95, 0.56, 0.62), paint2=(0.36, 0.52, 0.66),
              note='A doorstep group: a small tree in a glazed pot, a pot of flowers, herbs in plastic pots and a '
                   'trough; part 1 = the flowers, part 2 = the glaze.')
    rng = np.random.default_rng(31)

    def pot(c, r, h, mat):
        prof = [(r * 0.72, 0.0), (r * 0.9, h * 0.85), (r, h * 0.87), (r, h), (r * 0.88, h), (0.0, h * 0.93)]
        bm, _ = lathe(prof, 9, [mat, mat, mat, mat, 'soil'])
        grime_cyl(bm)
        return xform(bm, T(c))
    # a little tree in the glazed pot
    m.add(pot((-0.32, 0.08, 0.0), 0.2, 0.36, 'paint2'))
    m.add(tube([(-0.32, 0.08, 0.32), (-0.3, 0.08, 0.95)], 0.02, 'bark', sides=5))
    for k, (dx, dz, r) in enumerate(((0.0, 1.05, 0.22), (-0.12, 0.9, 0.17), (0.12, 0.92, 0.16), (0.02, 1.25, 0.15))):
        m.add(leaf_ball(r, (-0.31 + dx, 0.08 + 0.03 * k, dz), ['leaf', 'leaf_d', 'leaf_l', 'leaf'][k], seed=k))
    # flowers in terracotta
    m.add(pot((0.12, -0.08, 0.0), 0.15, 0.24, 'terracotta'))
    for k in range(3):
        m.add(leaf_ball(0.1, (0.12 + 0.07 * math.cos(k * 2.1), -0.08 + 0.07 * math.sin(k * 2.1), 0.3), ['leaf', 'leaf_d', 'leaf'][k], seed=10 + k))
    for k in range(6):
        a = 2 * PI * k / 6 + rng.random() * 0.4
        m.add(flower((0.12 + 0.1 * math.cos(a), -0.08 + 0.1 * math.sin(a), 0.38 + 0.03 * rng.random()), 'paint', r=0.035, seed=k))
    # herbs in two small plastic pots, a trough of greens behind
    for k, (x, y) in enumerate(((0.36, -0.16), (0.46, 0.06))):
        m.add(pot((x, y, 0.0), 0.08, 0.13, 'black'))
        m.add(leaf_ball(0.08, (x, y, 0.2), ['leaf_l', 'leaf'][k], squash=0.8, seed=20 + k))
    m.add(rpiece((-0.05, 0.12, 0.0), (0.42, 0.34, 0.2), (0.015, 0.015, 0.015), 'terracotta'))
    for k in range(3):
        m.add(leaf_ball(0.1, (0.04 + 0.15 * k, 0.23, 0.24), ['leaf_d', 'leaf', 'leaf_l'][k], seed=30 + k))
    return m


MODELS = [sign_board_a, banner_flag, utility_box, bike_rack, bin_pair, pot_group]
