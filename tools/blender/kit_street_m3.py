# Street kit models, part 3: crates, pallet, produce, sack, pots, wall-mounted items (AC unit,
# satellite dish, gas meter), the market stall and the shop awning.
import math
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from kit_street_geo import (PI, lathe, sweep, tube, cbox, rpiece, prism, ball, xform, T, R, S, frame, setmat,
                            faces_facing, uv_planar, uv_long, grime_cyl, lay, fix_normals, new_bm, merge, join)
from kit_street_atlas import reg_uv
from kit_street_build import Model
from kit_street_m1 import front_plate
from kit_street_m2 import leaf_ball, flower, inset_top


# ---------------------------------------------------------------- shared helpers
def uv_face_long(bm, faces, region):
    """Per face: s along the face's longest edge, t across it, each normalised to the face (boards)."""
    lm, lk, lu = lay(bm)
    for f in faces:
        e = max(f.edges, key=lambda e: e.calc_length())
        a = (e.verts[1].co - e.verts[0].co).normalized()
        b = f.normal.cross(a).normalized()
        ss_ = [l.vert.co.dot(a) for l in f.loops]; tt = [l.vert.co.dot(b) for l in f.loops]
        s0, s1, t0, t1 = min(ss_), max(ss_), min(tt), max(tt)
        f[lk] = 1
        for l, s, t in zip(f.loops, ss_, tt):
            l[lu].uv = reg_uv(region, (s - s0) / max(s1 - s0, 1e-4), (t - t0) / max(t1 - t0, 1e-4))


def uv_sides(bm, faces, region, lo, hi):
    """Planar per side: s horizontal (x on Y-facing faces, y on X-facing faces), t up; top faces: x, y."""
    lm, lk, lu = lay(bm)
    for f in faces:
        n = f.normal
        f[lk] = 1
        for l in f.loops:
            c = l.vert.co
            if abs(n.z) > 0.7: s, t = (c.x - lo[0]) / (hi[0] - lo[0]), (c.y - lo[1]) / (hi[1] - lo[1])
            elif abs(n.y) >= abs(n.x): s, t = (c.x - lo[0]) / (hi[0] - lo[0]), (c.z - lo[2]) / (hi[2] - lo[2])
            else: s, t = (c.y - lo[1]) / (hi[1] - lo[1]), (c.z - lo[2]) / (hi[2] - lo[2])
            l[lu].uv = reg_uv(region, s, t)


def stripe_mat(x, x0, w, a='paintw', b='canvas'):
    return a if int(math.floor((x - x0) / w + 1e-6)) % 2 == 0 else b


def valance(x0, x1, n, w, top, h, scallop, mats, d=0.012):
    """A row of scalloped flaps from x0, n of width w, hanging from z = top (local y = 0 plane)."""
    out = []
    for i in range(n):
        a = x0 + i * w; b = a + w
        pts = [(a, top), (b, top), (b, top - h)]
        for f in (0.25, 0.5, 0.75):
            pts.append((b - f * w, top - h - scallop * math.sin(PI * f)))
        pts.append((a, top - h))
        bm = prism(pts, d, mats[i % 2])
        uv_planar(bm, bm.faces, 'cloth', lambda co: ((co.x - x0) / (n * w), (co.z - top + h + scallop) / (h + scallop)))
        out.append(bm)
    return out


# ---------------------------------------------------------------- wooden crates
def crate_bm(s=0.6):
    h = s / 2
    bm = rpiece((-h, -h, -0.0065), (h, h, s), (0.022, 0.022, 0.022), 'wood', skip=((2, -1),))
    cen = [f for f in bm.faces if max(abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)) > 0.999]
    res = bmesh.ops.inset_individual(bm, faces=cen, thickness=0.075, depth=-0.016, use_even_offset=True)
    uv_face_long(bm, res['faces'], 'wood')
    lo, hi = (-h, -h, 0.0), (h, h, s)
    uv_sides(bm, cen, 'planks', lo, hi)
    setmat(bm, 'wood_d', cen)
    inner = s - 2 * 0.022 - 2 * 0.075 + 0.03
    L = inner * math.sqrt(2)
    for (axis, sign) in (('y', -1), ('y', 1), ('x', -1), ('x', 1)):
        b = cbox((L, 0.07, 0.018), 0.006, 'wood')
        uv_long(b, b.faces, 'wood')
        if axis == 'y':
            M = T(0, sign * (h - 0.012), h) @ R(sign * PI / 4, 'Y') @ R(PI / 2, 'X')
        else:
            M = T(sign * (h - 0.012), 0, h) @ R(PI / 2, 'Z') @ R(sign * PI / 4, 'Y') @ R(PI / 2, 'X')
        merge(bm, xform(b, M))
    return bm


def crate():
    m = Model('Crate', note='Wooden crate, 0.6 m cube.')
    m.add(crate_bm(0.6))
    return m


def crate_stack():
    m = Model('CrateStack', note='Three 0.6 m crates in a pyramid.')
    for (x, z, yaw) in ((-0.31, 0.0, 0.05), (0.31, 0.0, -0.035), (0.0, 0.6, 0.09)):
        m.add(xform(crate_bm(0.6), T(x, 0, z) @ R(yaw, 'Z')))
    return m


# ---------------------------------------------------------------- plastic drinks crates
def drinks_crates():
    m = Model('DrinksCrates', paint=(0.93, 0.74, 0.26),
              note='Six plastic bottle crates, 2 wide x 3 high; part 1 = the yellow crates.')
    rng = np.random.default_rng(8)
    w, d, h = 0.44, 0.34, 0.31
    cols = [['paintp', 'blue', 'paintp'], ['green', 'paintp', 'blue']]
    for ci, x in enumerate((-0.228, 0.228)):
        for k in range(3):
            z0 = k * (h + 0.004)
            dx, dy, yaw = rng.uniform(-0.012, 0.012), rng.uniform(-0.015, 0.015), rng.uniform(-0.03, 0.03)
            bm = cbox((w, d, h), 0.018, cols[ci][k])
            if k == 2:
                inset_top(bm, 0.022, 0.07, inner_mat='black', cos=0.99)
            sides = [f for f in bm.faces if abs(f.normal.z) < 0.5]
            uv_sides(bm, sides, 'pcrate', (-w / 2, -d / 2, -h / 2), (w / 2, d / 2, h / 2))
            M = T(x + dx, dy, z0 + h / 2) @ R(yaw, 'Z')
            m.add(xform(bm, M))
            if k == 2:
                for i in range(4):
                    for j in range(3):
                        bx, by = -0.165 + 0.11 * i, -0.1 + 0.1 * j
                        zb = h / 2 - 0.05
                        bt, _ = lathe([(0.027, zb), (0.027, zb + 0.045), (0.012, zb + 0.088), (0.015, zb + 0.1), (0.0, zb + 0.105)], 5,
                                      ['amber', 'amber', 'cap', 'cap'], phase=rng.random())
                        m.add(xform(bt, M @ T(bx, by, 0)))
    return m


# ---------------------------------------------------------------- pallet
def pallet():
    m = Model('Pallet', note='Wooden pallet, 1.2 x 0.8 m.')
    rng = np.random.default_rng(2)

    def board(size, at, mat='wood_g'):
        b = cbox(size, 0.006, mat); uv_long(b, b.faces, 'wood')
        return xform(b, T(at) @ R(rng.uniform(-0.01, 0.01), 'Z'))
    for y in (-0.34, -0.17, 0.0, 0.17, 0.34):
        m.add(board((1.2, 0.11 if abs(y) < 0.3 else 0.13, 0.022), (0, y, 0.133)))
    for x in (-0.55, 0.0, 0.55):
        m.add(board((0.1, 0.8, 0.022), (x, 0, 0.111)))
        for y in (-0.34, 0.0, 0.34):
            m.add(board((0.1, 0.12 if y else 0.1, 0.078), (x, y, 0.061), 'wood'))
    for y in (-0.34, 0.0, 0.34):
        m.add(board((1.2, 0.1, 0.022), (0, y, 0.011)))
    return m


# ---------------------------------------------------------------- produce crate and sack
def produce_crate():
    m = Model('ProduceCrate', paint2=(0.95, 0.59, 0.22), note='Slatted crate heaped with oranges; part 2 = the fruit.')
    rng = np.random.default_rng(6)
    W, D, H = 0.5, 0.36, 0.26

    def slat(size, at):
        b = cbox(size, 0.005, 'wood'); uv_long(b, b.faces, 'wood')
        return xform(b, T(at))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.add(slat((0.035, 0.035, H), (sx * (W / 2 - 0.0175), sy * (D / 2 - 0.0175), H / 2)))
    for (z0, z1) in ((0.015, 0.075), (0.105, 0.165), (0.195, 0.255)):
        zc = (z0 + z1) / 2
        for sy in (-1, 1):
            m.add(slat((W, 0.012, z1 - z0), (0, sy * (D / 2 - 0.004), zc)))
        for sx in (-1, 1):
            m.add(slat((0.012, D - 0.02, z1 - z0), (sx * (W / 2 - 0.004), 0, zc)))
    m.add(cbox((W - 0.04, D - 0.04, 0.17), 0.0, 'darkwood', at=(0, 0, 0.1)))
    r = 0.047
    pts = []
    for i in range(4):
        for j in range(3):
            pts.append((-0.165 + 0.11 * i + rng.uniform(-0.01, 0.01), -0.1 + 0.1 * j + rng.uniform(-0.01, 0.01), 0.215))
    for i in range(3):
        for j in range(2):
            pts.append((-0.11 + 0.11 * i, -0.05 + 0.1 * j, 0.285))
    for k, p in enumerate(pts):
        m.add(ball(r * rng.uniform(0.92, 1.06), 'paint2', n=6, rings=4, squash=0.92, seed=k, at=p))
    for k in range(3):
        lf = ball(0.04, 'leaf_d', n=5, rings=2, squash=0.25, seed=k)
        m.add(xform(lf, T(-0.1 + 0.12 * k, -0.06 + 0.05 * k, 0.33) @ R(0.4 * k, 'Z') @ S(1.6, 0.8, 1)))
    return m


def sack():
    m = Model('Sack', note='A tied burlap sack with a faded stamp (no text).')
    W, D, H = 0.46, 0.34, 0.6

    def slump(X):
        X = X.copy(); k = np.clip(X[:, 2] / H, 0, 1)
        bulge = 1.10 - 0.18 * k + 0.12 * np.sin(PI * np.clip(k * 1.2, 0, 1))
        pinch = 1.0 - 0.55 * np.clip((k - 0.78) / 0.22, 0, 1) ** 1.5
        X[:, 0] *= bulge * pinch; X[:, 1] *= bulge * pinch
        X[:, 0] += 0.015 * np.sin(X[:, 2] * 19 + X[:, 1] * 9)
        X[:, 1] += 0.012 * np.sin(X[:, 2] * 15 + X[:, 0] * 11)
        X[:, 2] -= 0.04 * np.clip(1 - np.abs(X[:, 0]) / (W / 2), 0, 1) * (k > 0.6)
        return X
    bm = rpiece((-W / 2, -D / 2, 0.0), (W / 2, D / 2, H), (0.12, 0.1, 0.1), 'burlap', extra=((-0.08, 0.08), (0.0,), (0.15, 0.3, 0.42, 0.5)),
                skip=((2, -1),), deform=slump)
    front = [f for f in bm.faces if f.normal.y < -0.45]
    rest = [f for f in bm.faces if f.normal.y >= -0.45]
    uv_planar(bm, front, 'sackmark', lambda co: (0.5 + co.x / 0.5, co.z / 0.62))
    uv_sides(bm, rest, 'cloth', (-0.3, -0.25, 0.0), (0.3, 0.25, 0.65))
    m.add(bm)
    nk, _ = lathe([(0.075, H - 0.03), (0.06, H + 0.0), (0.05, H + 0.04), (0.075, H + 0.09), (0.09, H + 0.11), (0.0, H + 0.1)], 8, 'burlap')
    uv_sides(nk, nk.faces, 'cloth', (-0.1, -0.1, H - 0.05), (0.1, 0.1, H + 0.12))
    m.add(nk)
    tb, _ = lathe([(0.0, H + 0.005), (0.058, H + 0.005), (0.058, H + 0.03), (0.0, H + 0.03)], 8, 'twine')
    m.add(tb)
    m.add(tube([(0.05, -0.03, H + 0.02), (0.09, -0.07, H - 0.02), (0.1, -0.09, H - 0.08)], 0.008, 'twine', sides=4))
    return m


# ---------------------------------------------------------------- potted plants
def pot_shell(prof, n, soil_z, soil_r, off=0.0):
    bm, _ = lathe(prof, n, 'paintc')
    grime_cyl(bm, off=off)
    sl, _ = lathe([(soil_r, soil_z), (0.0, soil_z + 0.004)], n, 'soil')
    uv_planar(sl, sl.faces, 'soil', lambda co: (0.5 + co.x / (2 * soil_r), 0.5 + co.y / (2 * soil_r)))
    return [bm, sl]


def pot_a():
    m = Model('PotA', paint=(0.80, 0.48, 0.33), paint2=(0.90, 0.36, 0.38),
              note='Small terracotta pot with a flowering bush; part 1 = pot, part 2 = flowers.')
    rng = np.random.default_rng(11)
    prof = [(0.11, 0.0), (0.118, 0.012), (0.14, 0.17), (0.148, 0.19), (0.17, 0.196), (0.176, 0.25), (0.168, 0.26),
            (0.152, 0.256), (0.149, 0.23)]
    for b in pot_shell(prof, 14, 0.228, 0.15, 0.1): m.add(b)
    for k, (x, y, r) in enumerate(((-0.06, 0.02, 0.13), (0.07, 0.03, 0.12), (0.0, -0.05, 0.12), (0.01, 0.06, 0.11))):
        m.add(leaf_ball(r, (x, y, 0.3), ['leaf', 'leaf_d', 'leaf_l', 'leaf'][k], squash=0.85, seed=20 + k, n=8, rings=5, lump=0.08))
    for k in range(9):
        a = rng.uniform(-PI, 0.4); rr = rng.uniform(0.04, 0.12)
        z = 0.3 + math.sqrt(max(0.14 ** 2 - rr ** 2, 0)) * 0.85 + 0.012
        fx, fy = rr * math.cos(a), rr * math.sin(a) - 0.02
        m.add(flower((fx, fy, z), 'paint2', rng.uniform(0.036, 0.044), seed=k, tilt=(-0.45 * fy / 0.14, 0.45 * fx / 0.14)))
    return m


def pot_b():
    m = Model('PotB', paint=(0.36, 0.52, 0.66), note='Glazed pot with a spiky leaf plant; part 1 = glaze.')
    rng = np.random.default_rng(12)
    prof = [(0.13, 0.0), (0.15, 0.02), (0.2, 0.12), (0.215, 0.22), (0.2, 0.32), (0.18, 0.35), (0.19, 0.365),
            (0.19, 0.39), (0.176, 0.396), (0.17, 0.37)]
    for b in pot_shell(prof, 16, 0.36, 0.172, 0.3): m.add(b)
    sec = [(-0.028, 0.0), (0.0, 0.007), (0.028, 0.0), (0.0, -0.007)]
    for k in range(12):
        a = 2 * PI * k / 12 + rng.uniform(-0.15, 0.15)
        tall = rng.uniform(0.75, 1.0)
        reach = rng.uniform(0.18, 0.3)
        e = Vector((math.cos(a), math.sin(a), 0))
        path = [Vector((0, 0, 0.36)) + e * 0.02, Vector((0, 0, 0.36 + 0.3 * tall)) + e * reach * 0.3,
                Vector((0, 0, 0.36 + 0.52 * tall)) + e * reach * 0.75, Vector((0, 0, 0.36 + 0.55 * tall)) + e * reach * 1.15]
        bm = sweep(path, lambda i, p, t, e=e: e.cross(Vector((0, 0, 1))), sec, 'leaf' if k % 2 else 'leaf_d', True, [1.0, 1.0, 0.75, 0.12])
        m.add(bm)
    return m


def pot_c():
    m = Model('PotC', paint=(0.86, 0.82, 0.74), paint2=(0.96, 0.84, 0.34),
              note='Large pot with a little lemon tree; part 1 = pot, part 2 = lemons.')
    rng = np.random.default_rng(13)
    prof = [(0.24, 0.0), (0.25, 0.02), (0.28, 0.42), (0.3, 0.44), (0.31, 0.5), (0.296, 0.506), (0.286, 0.48)]
    for b in pot_shell(prof, 18, 0.47, 0.287, 0.6): m.add(b)
    tr = tube([(0, 0, 0.46), (0.02, 0.0, 0.8), (-0.02, 0.01, 1.05), (0.0, 0.0, 1.2)], 0.036, 'bark', sides=6,
              scales=[1.0, 0.85, 0.75, 0.6])
    m.add(tr)
    m.add(tube([(0.01, 0, 0.95), (0.14, 0.02, 1.12)], 0.018, 'bark', sides=5))
    m.add(tube([(-0.01, 0, 1.0), (-0.15, -0.02, 1.18)], 0.018, 'bark', sides=5))
    clumps = [(0.0, 0.0, 1.38, 0.26), (0.17, 0.04, 1.2, 0.2), (-0.18, -0.03, 1.24, 0.21), (0.05, -0.12, 1.22, 0.18), (-0.04, 0.13, 1.28, 0.19)]
    for k, (x, y, z, r) in enumerate(clumps):
        m.add(leaf_ball(r, (x, y, z), ['leaf', 'leaf_d', 'leaf', 'leaf_l', 'leaf_d'][k], squash=0.82, seed=40 + k, n=8, rings=5, lump=0.14))
    for k in range(11):
        x, y, z, r = clumps[k % 5]
        a = rng.uniform(-PI, 0.3); b = rng.uniform(-0.5, 0.6)
        p = Vector((x, y, z)) + Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b) * 0.8)) * r * 0.92
        lm_ = ball(0.036, 'paint2', n=6, rings=3, squash=1.25, seed=k)
        m.add(xform(lm_, T(p)))
    return m


# ---------------------------------------------------------------- wall-mounted items (origin: back centre, wall at y = 0)
def ac_unit():
    m = Model('ACUnit', mount='wall', note='Wall-mounted AC condenser; origin at the back centre on the wall (y = 0), unit centred on z = 0.')
    m.add(rpiece((-0.4, -0.36, -0.28), (0.4, -0.08, 0.28), (0.03, 0.03, 0.03), 'ac', extra=((0.12,), (), (0.0,))))
    fp = [(0.0, 0.0), (0.232, 0.0), (0.236, 0.016), (0.226, 0.024), (0.21, 0.017), (0.0, 0.013)]
    bm, tags = lathe(fp, 20, ['ac', 'ac', 'ac', 'decal', 'decal'])
    uv_planar(bm, [f for f, s, i in tags if s >= 3], 'fan', lambda co: (0.5 + co.x / 0.44, 0.5 + co.y / 0.44))
    m.add(xform(bm, frame((-0.12, -0.36, 0.0), (0, -1, 0))))
    m.add(front_plate((0.2, 0.012, 0.44), (0.27, -0.362, 0.0), 'acvent', 'ac'))
    for sx in (-1, 1):
        x = sx * 0.3
        m.add(cbox((0.04, 0.38, 0.035), 0.008, 'galv', at=(x, -0.19, -0.3)))
        m.add(tube([(x, -0.02, -0.56), (x, -0.33, -0.32)], 0.015, 'galv', sides=4))
        m.add(cbox((0.06, 0.012, 0.32), 0.004, 'galv', at=(x, -0.006, -0.42)))
    m.add(tube([(0.38, -0.2, -0.12), (0.47, -0.2, -0.12), (0.5, -0.17, -0.12), (0.5, -0.04, -0.12), (0.5, -0.0, -0.12)], 0.022, 'insul', sides=6))
    m.add(tube([(0.38, -0.14, -0.04), (0.45, -0.14, -0.04), (0.47, -0.12, -0.04), (0.47, -0.0, -0.04)], 0.016, 'insul', sides=6))
    m.add(tube([(0.25, -0.16, -0.28), (0.26, -0.14, -0.42), (0.24, -0.1, -0.6), (0.27, -0.08, -0.74)], 0.009, 'black', sides=4))
    return m


def satellite_dish():
    m = Model('SatelliteDish', mount='wall', note='Wall-mounted dish; origin at the centre of the wall plate (y = 0).')
    m.add(cbox((0.12, 0.016, 0.2), 0.005, 'galv', at=(0, -0.008, 0)))
    for z in (-0.07, 0.07):
        m.add(ball(0.012, 'steel_d', n=6, rings=2, squash=0.5, at=(0, -0.017, z)))
    m.add(tube([(0, -0.016, 0.03), (0, -0.2, 0.03), (0.04, -0.3, 0.0)], 0.02, 'galv', sides=6))
    Dc = Vector((0.06, -0.36, 0.02)); d = Vector((0.35, -1.0, 0.5)).normalized()
    M = frame(Dc, d, (0, 0, 1))
    prof = [(0.0, 0.0), (0.12, 0.012), (0.22, 0.04), (0.3, 0.085), (0.31, 0.094), (0.302, 0.1), (0.22, 0.054), (0.12, 0.025), (0.0, 0.013)]
    sh, _ = lathe(prof, 18, 'dish')
    fix_normals(sh)
    m.add(xform(sh, M.copy()))
    m.add(xform(cbox((0.1, 0.1, 0.04), 0.01, 'galv', at=(0, 0, -0.01)), M.copy()))
    m.add(xform(tube([(0, -0.28, 0.09), (0, -0.12, 0.24), (0, -0.01, 0.31)], 0.011, 'galv', sides=5), M.copy()))
    hd, _ = lathe([(0.0, 0.28), (0.028, 0.28), (0.03, 0.34), (0.04, 0.36), (0.03, 0.37), (0.0, 0.372)], 8, 'cap')
    m.add(xform(hd, M.copy()))
    return m


def gas_meter():
    m = Model('GasMeter', mount='wall', note='Wall-mounted gas meter; origin at the back centre (y = 0), box centred on z = 0; pipes run down.')
    m.add(cbox((0.36, 0.012, 0.46), 0.005, 'galv', at=(0, -0.006, 0.0)))
    m.add(rpiece((-0.16, -0.18, -0.19), (0.16, -0.012, 0.19), (0.025, 0.025, 0.025), 'meter'))
    m.add(rpiece((-0.178, -0.205, 0.19), (0.178, -0.01, 0.215), (0.012, 0.012, 0.008), 'meter'))
    m.add(front_plate((0.22, 0.012, 0.22), (0, -0.183, 0.04), 'dial', 'meter'))
    m.add(cbox((0.05, 0.012, 0.025), 0.004, 'steel_d', at=(0.1, -0.184, -0.13)))
    for sx in (-1, 1):
        x = sx * 0.08
        m.add(tube([(x, -0.1, -0.18), (x, -0.1, -0.29), (x, -0.075, -0.34), (x, -0.06, -0.38), (x, -0.06, -0.64)], 0.017, 'gaspipe', sides=6))
        m.add(cbox((0.05, 0.05, 0.04), 0.01, 'brass', at=(x, -0.1, -0.2)))
        m.add(cbox((0.045, 0.04, 0.03), 0.006, 'galv', at=(x, -0.04, -0.52)))
    bv, _ = lathe([(0.0, -0.03), (0.028, -0.03), (0.03, 0.03), (0.0, 0.032)], 8, 'brass')
    m.add(xform(bv, T(-0.08, -0.06, -0.45)))
    m.add(cbox((0.11, 0.018, 0.022), 0.005, 'red', at=(-0.12, -0.09, -0.45)))
    return m


# ---------------------------------------------------------------- market stall
def market_stall():
    m = Model('MarketStall', paint=(0.30, 0.56, 0.54), paint2=(0.95, 0.59, 0.22),
              note='Table 2.2 m wide under a striped canopy with crates of produce. Part 1 = canopy stripes, part 2 = the oranges.')
    rng = np.random.default_rng(21)
    top = rpiece((-1.1, -0.45, 0.78), (1.1, 0.45, 0.84), (0.02, 0.02, 0.015), 'wood', extra=((-0.55, 0.0, 0.55), (), ()))
    tf = [f for f in top.faces if f.normal.z > 0.5]
    uv_planar(top, tf, 'planks', lambda co: ((co.x + 1.1) / 2.2, (co.y + 0.45) / 0.9))
    m.add(top)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lg = cbox((0.06, 0.06, 0.78), 0.01, 'wood_d', at=(sx * 1.0, sy * 0.37, 0.39)); uv_long(lg, lg.faces, 'wood'); m.add(lg)
        st = cbox((2.0, 0.04, 0.06), 0.01, 'wood_d', at=(0, sx * 0.37, 0.2)); uv_long(st, st.faces, 'wood'); m.add(st)
    # canopy on four poles, higher at the back, sagging a little between them
    for sx in (-1, 1):
        for (y, zt) in ((-0.52, 2.2), (0.44, 2.44)):
            m.add(tube([(sx * 1.08, y, 0.0), (sx * 1.08, y, zt)], 0.024, 'galv', sides=6))
            m.add(cbox((0.08, 0.08, 0.02), 0.006, 'steel_d', at=(sx * 1.08, y, 0.01)))
    X0, SW, NS = -1.2, 0.24, 10
    xl = tuple(X0 + SW * i for i in range(1, NS))
    can = rpiece((X0, 0.0, 0.0), (-X0, 1.0, 0.018), (1e-3, 1e-3, 0.006), 'canvas', seg=(0, 0, 0), extra=(xl, (0.34, 0.67), ()),
                 mats=lambda a, s, c: stripe_mat(c[0], X0, SW))

    def drape(X):
        X = X.copy(); v = X[:, 1].copy(); w = X[:, 2].copy(); x = X[:, 0]
        X[:, 1] = -0.64 + 1.16 * v
        X[:, 2] = 2.22 + 0.24 * v + w - 0.035 * np.sin(PI * v) - 0.03 * np.sin(PI * (x - X0) / (2 * -X0)) * np.sin(PI * np.clip(v * 1.2, 0, 1))
        return X
    for vtx in can.verts:
        p = drape(np.array([vtx.co[:]]))[0]; vtx.co = Vector(p)
    can.normal_update()
    fix_normals(can)
    uv_planar(can, can.faces, 'cloth', lambda co: ((co.x - X0) / (-2 * X0), (co.y + 0.64) / 1.16))
    m.add(can)
    for b in valance(X0, -X0, NS, SW, 0.0, 0.13, 0.06, ['paintw', 'canvas']):
        m.add(xform(b, T(0, -0.652, 2.235)))
    # three tilted display crates of produce
    kinds = [('paint2', 0.054, 12, 0.95), ('apple', 0.05, 12, 0.9), ('cabbage', 0.078, 6, 0.85)]
    for ci, x in enumerate((-0.7, 0.0, 0.7)):
        cw, cd, ch = 0.6, 0.44, 0.14
        bx = rpiece((-cw / 2, -cd / 2, 0.0), (cw / 2, cd / 2, ch), (0.012, 0.012, 0.012), 'wood', skip=((2, -1),))
        inset_top(bx, 0.016, ch - 0.02, inner_mat='darkwood')
        sides = [f for f in bx.faces if abs(f.normal.z) < 0.5]
        uv_sides(bx, sides, 'planks', (-cw / 2, -cd / 2, 0.0), (cw / 2, cd / 2, ch))
        M = T(x, -0.06, 0.84) @ R(0.2, 'X') @ T(0, 0, 0.0)
        m.add(xform(bx, M))
        mat, r, n, sq = kinds[ci]
        cols, rows = (4, 3) if n == 12 else (3, 2)
        k = 0
        for i in range(cols):
            for j in range(rows):
                fx = -cw / 2 + cw * (i + 0.5) / cols + rng.uniform(-0.01, 0.01)
                fy = -cd / 2 + cd * (j + 0.5) / rows + rng.uniform(-0.01, 0.01)
                fm = mat if not (mat == 'apple' and (i + j) % 3 == 0) else 'greenf'
                b = ball(r * rng.uniform(0.93, 1.05), fm, n=6, rings=3,
                         squash=sq, lump=0.08 if mat == 'cabbage' else 0.0, seed=ci * 30 + k)
                if mat == 'cabbage':
                    uv_planar(b, b.faces, 'leaf', lambda co, r=r: (0.5 + co.x / (2.4 * r), 0.5 + co.y / (2.4 * r)))
                m.add(xform(b, M @ T(fx, fy, 0.03 + r * sq)))
                k += 1
        for i in range(2 if n == 12 else 1):
            b = ball(r, mat if mat != 'apple' else 'apple', n=6, rings=3, squash=sq, seed=ci * 50 + i)
            m.add(xform(b, M @ T(-0.06 + 0.12 * i, 0.0, 0.03 + r * sq * 2.6)))
    # crates under the table and a chalkboard on the corner
    for (x, yaw) in ((-0.55, 0.05), (0.2, -0.04)):
        cb = cbox((0.5, 0.36, 0.3), 0.012, 'wood')
        uv_sides(cb, [f for f in cb.faces if abs(f.normal.z) < 0.5], 'planks', (-0.25, -0.18, -0.15), (0.25, 0.18, 0.15))
        m.add(xform(cb, T(x, 0.02, 0.15) @ R(yaw, 'Z')))
    bd = front_plate((0.34, 0.018, 0.25), (0, 0, 0), 'chalk', 'chalkframe', r=0.008)
    m.add(xform(bd, T(0.98, -0.47, 0.99) @ R(-0.25, 'X')))
    m.add(tube([(0.98, -0.43, 0.84), (0.98, -0.5, 0.99)], 0.008, 'chalkframe', sides=4))
    return m


# ---------------------------------------------------------------- shop awning (wall)
def awning():
    m = Model('Awning', paint=(0.82, 0.36, 0.30), mount='wall',
              note='Striped shop awning 2.2 m wide; origin at the wall attachment (top centre, wall plane y = 0); it slopes out to -Y and down. Part 1 = the coloured stripes.')
    W, OUT, DROP = 2.2, 1.0, 0.42
    X0, SW, NS = -W / 2, W / 10, 10
    xl = tuple(X0 + SW * i for i in range(1, NS))
    can = rpiece((X0, 0.0, 0.0), (-X0, 1.0, 0.016), (1e-3, 1e-3, 0.006), 'canvas', seg=(0, 0, 1), extra=(xl, (0.25, 0.5, 0.75), ()),
                 mats=lambda a, s, c: stripe_mat(c[0], X0, SW))
    for vtx in can.verts:
        x, v, w = vtx.co
        vtx.co = Vector((x, -0.06 - (OUT - 0.06) * v, -0.04 - DROP * v + 0.06 * math.sin(PI * v) - 0.012 * math.sin(PI * (x - X0) / W) * math.sin(PI * v) + w))
    can.normal_update(); fix_normals(can)
    uv_planar(can, can.faces, 'cloth', lambda co: ((co.x - X0) / W, (-co.y) / OUT))
    m.add(can)
    zf = -0.04 - DROP
    for b in valance(X0, -X0, NS, SW, 0.0, 0.14, 0.06, ['paintw', 'canvas']):
        m.add(xform(b, T(0, -OUT - 0.012, zf + 0.02)))
    m.add(rpiece((X0, -OUT - 0.035, zf - 0.03), (-X0, -OUT + 0.02, zf + 0.02), (0.015, 0.015, 0.015), 'galv'))
    m.add(rpiece((X0, -0.13, -0.08), (-X0, 0.0, 0.06), (0.02, 0.035, 0.035), 'galv'))
    for sx in (-1, 1):
        x = sx * 0.95
        m.add(cbox((0.08, 0.04, 0.14), 0.01, 'steel_d', at=(x, -0.02, -0.62)))
        m.add(tube([(x, -0.03, -0.62), (x, -0.5, -0.48), (x, -OUT + 0.03, zf - 0.03)], 0.016, 'galv', sides=6))
        m.add(ball(0.024, 'steel_d', n=6, rings=3, at=(x, -0.5, -0.48)))
    return m


MODELS = [crate, crate_stack, drinks_crates, pallet, produce_crate, sack, pot_a, pot_b, pot_c,
          ac_unit, satellite_dish, gas_meter, market_stall, awning]
