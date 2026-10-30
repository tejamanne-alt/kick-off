# Park and playground backdrop for kit_leisure.py: Slide, SeeSaw, SwingSet, Sandpit, PicnicTable,
# ParkLamp, DuckPond, Gazebo. Metres, Z up, front faces -Y, origin at the base centre on the ground.
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_leisure_geo import *
from kit_leisure_beach import lumpy, flag_sheet
from kit_leisure_play import catmull, PARK_DIRT

LAV, WARM = (0.56, 0.53, 0.65), (0.86, 0.77, 0.67)


def stone(center, radii, rng, cut=-0.02, planes=0.5, freq=2, lav=LAV, warm=WARM):
    st = pebble(center, radii, rng, 'own0k', freq=freq, amp=0.10, flat=0.6, cut=cut, planes=planes)
    zs = [v.co.z for v in st.verts]; z0, z1 = min(zs), max(zs)
    jit = rng.uniform(-0.04, 0.04)

    def col(co):
        f = (co.z - z0) / max(z1 - z0, 1e-4)
        k = float(sstep(0.45, 0.95, f))
        return [(1 + jit) * (s2l(lav)[i] * (1 - k) + s2l(warm)[i] * k) for i in range(3)]
    set_vc(st, col)
    tile_box(st, 'stone', rng, 0.5)
    return st


# ---------------------------------------------------------------- Slide
def slide(rng):
    M = Model('Slide', pal={'paint': (0.30, 0.56, 0.60), 'accent': (0.97, 0.76, 0.31), 'third': (0.84, 0.36, 0.30),
                            'wood': (0.76, 0.60, 0.43), 'metal': (0.70, 0.72, 0.74)},
              dirt=PARK_DIRT, dirt_h=0.35, chips=0.6, chip=(0.70, 0.66, 0.62), ao_dist=0.35)
    M.parts = {1: 'paint', 2: 'accent', 3: 'third'}
    zp = 1.45
    xa, xb, yw = -1.12, -0.62, 0.30
    posts = [(xa, -yw), (xb, -yw), (xa, yw), (xb, yw)]
    for x, y in posts:
        M.add(member((x, y, -0.02), (x, y, 2.18), 0.08, 0.08, 'paint'))
        cp, _ = lathe([(0, 0), (0.05, 0), (0.05, 0.03), (0.03, 0.05), (0, 0.055)], 8, 'thirdc'); xform(cp, T(x, y, 2.18)); M.add(cp)
    deck = rpiece((xa - 0.05, -yw - 0.05, zp - 0.07), (xb + 0.05, yw + 0.05, zp), 0.015, 'wood')
    tile_planar(deck, 'slats', lambda co: ((co.y + 0.35) / 0.7, (co.x - xa + 0.05) / 0.6)); M.add(deck)
    # side guard panels with porthole windows, a little hip roof over the deck
    for y in (-yw, yw):
        pn = cbox((xb - xa - 0.08, 0.035, 0.52), 0.012, 'accent'); xform(pn, T((xa + xb) / 2, y, zp + 0.36)); M.add(pn)
        M.spots.append(('front', (xa + xb) / 2, zp + 0.38, 0.11, (0.22, 0.26, 0.28), 0.9))
        M.spots.append(('front', (xa + xb) / 2, zp + 0.38, 0.13, (0.62, 0.58, 0.55), 0.4))
    q = 2 ** 0.5
    rf, tags = lathe([(0, 2.16), (1.0 * q, 2.16), (1.0 * q, 2.22, 'S'), (0.1 * q, 2.62), (0, 2.64)], 4, ['thirdc', 'third', 'thirdk', 'thirdc'])
    tile_lathe(rf, tags, 'shingle', (2,), 4, per_face=True)
    xform(rf, T((xa + xb) / 2, 0, 0) @ S(0.42, 0.46, 1.0)); M.add(rf)
    fin, _ = lathe([(0, 2.6), (0.04, 2.62), (0.03, 2.7), (0.045, 2.74), (0, 2.8)], 8, 'accentc'); xform(fin, T((xa + xb) / 2, 0, 0)); M.add(fin)
    # the ladder at the back end
    xl0 = -1.62

    def lx(z): return xl0 + (xa - xl0) * z / zp
    for y in (-0.24, 0.24):
        M.add(member((lx(-0.02), y, -0.02), (lx(zp + 0.4), y, zp + 0.4), 0.06, 0.07, 'paint', up=(0, 1, 0)))
    for z in np.arange(0.3, zp - 0.05, 0.29):
        M.add(tube([(lx(z), -0.24, z), (lx(z), 0.24, z)], 0.02, 'metalc', sides=6, caps=False))
    # the chute: a U-channel sweeping down to a flat run-out
    pts = catmull([(xb - 0.02, 0, zp - 0.005), (-0.30, 0, zp - 0.10), (0.25, 0, zp - 0.48), (0.95, 0, 0.62),
                   (1.40, 0, 0.36), (1.75, 0, 0.30), (2.0, 0, 0.32)], 3)
    sec = [(-0.03, -0.27), (-0.03, 0.27), (0.12, 0.27), (0.15, 0.255), (0.15, 0.23), (0.13, 0.218), (0.0, 0.218),
           (0.0, -0.218), (0.13, -0.218), (0.15, -0.23), (0.15, -0.255), (0.12, -0.27)]

    def up(i, p, t):
        return Vector((0, 0, 1)) - t * t.z
    ch = sweep(pts, up, sec, 'accent')
    M.add(ch)
    # supports under the chute
    for (x, z, y) in ((0.70, 0.78, 0.0), (1.72, 0.27, -0.2), (1.72, 0.27, 0.2)):
        M.add(member((x, y, -0.02), (x, y, z), 0.07, 0.07, 'paint', up=(0, 1, 0)))
    for y in (-0.2, 0.2):
        fp = cbox((0.12, 0.12, 0.03), 0.01, 'metal'); xform(fp, T(1.72, y, 0.012)); M.add(fp)
    M.add(member((0.70, -0.25, 0.70), (0.70, 0.25, 0.70), 0.06, 0.06, 'paint'))
    return M


# ---------------------------------------------------------------- SeeSaw
def seesaw(rng):
    M = Model('SeeSaw', pal={'paint': (0.84, 0.38, 0.31), 'accent': (0.98, 0.79, 0.34), 'metal': (0.36, 0.42, 0.50),
                             'rubber': (0.22, 0.22, 0.24)},
              dirt=PARK_DIRT, dirt_h=0.2, chips=0.8, chip=(0.66, 0.52, 0.40), ao_dist=0.3)
    M.parts = {1: 'paint', 2: 'accent'}
    zp = 0.56
    ang = math.radians(-9)
    Mp = T(0, 0, zp) @ R(ang, 'Y')
    # the stand: two inverted Vs either side of the plank and an axle
    for y in (-0.19, 0.19):
        for sx in (-1, 1):
            M.add(member((sx * 0.36, y, -0.02), (sx * 0.02, y, zp + 0.02), 0.06, 0.06, 'metal', up=(0, 1, 0)))
        ft = cbox((0.86, 0.08, 0.04), 0.012, 'metal'); xform(ft, T(0, y, 0.02)); M.add(ft)
    M.add(tube([(0, -0.24, zp), (0, 0.24, zp)], 0.035, 'metalc', sides=8))
    hub = rpiece((-0.12, -0.15, -0.05), (0.12, 0.15, 0.0), 0.02, 'metal'); xform(hub, Mp); M.add(hub)
    # the plank, painted, its grain showing through
    pl = rpiece((-1.5, -0.14, 0.0), (1.5, 0.14, 0.065), (0.06, 0.02, 0.02), 'paintk', seg=(2, 1, 1))
    tile_box(pl, 'grain', rng, 3.0); xform(pl, Mp); M.add(pl)
    for sx in (-1, 1):
        seat = rpiece((-0.17, -0.15, 0.0), (0.17, 0.15, 0.05), (0.04, 0.03, 0.02), 'accent', seg=(2, 1, 1))
        xform(seat, Mp @ T(sx * 1.25, 0, 0.06)); M.add(seat)
        # T-handle in front of each seat
        hx = sx * 0.95
        M.add(tube([Mp @ Vector((hx, 0, 0.06)), Mp @ Vector((hx, 0, 0.36))], 0.02, 'accentc', sides=6))
        M.add(tube([Mp @ Vector((hx, -0.15, 0.36)), Mp @ Vector((hx, 0.15, 0.36))], 0.022, 'accentc', sides=6))
        for y in (-0.15, 0.15):
            gr, _ = lathe([(0, 0), (0.028, 0), (0.028, 0.06), (0, 0.065)], 6, 'rubber')
            xform(gr, Mp @ T(hx, y, 0.36) @ R(PI / 2 if y < 0 else -PI / 2, 'X')); M.add(gr)
        # an old tyre half-buried under each end as a bumper
        ty = torus(0.20, 0.075, 14, 6, 'rubber', phase=0.5)
        xform(ty, T(sx * 1.32, 0, 0.06) @ R(PI / 2, 'X')); M.add(ty)
    return M


# ---------------------------------------------------------------- SwingSet
def swingset(rng):
    M = Model('SwingSet', pal={'paint': (0.38, 0.56, 0.78), 'accent': (0.86, 0.38, 0.31), 'metal': (0.64, 0.66, 0.68),
                               'wood': (0.78, 0.62, 0.44)},
              dirt=PARK_DIRT, dirt_h=0.3, chips=0.7, chip=(0.62, 0.42, 0.30), ao_dist=0.3)
    M.parts = {1: 'paint', 2: 'accent'}
    zt, xe, yf = 2.25, 1.45, 0.78
    M.add(tube([(-xe - 0.06, 0, zt), (xe + 0.06, 0, zt)], 0.05, 'paint', sides=8))
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.add(tube([(sx * (xe + 0.08), sy * yf, -0.03), (sx * xe, sy * 0.05, zt - 0.05)], 0.042, 'paint', sides=8))
            an = cbox((0.12, 0.12, 0.03), 0.01, 'metal'); xform(an, T(sx * (xe + 0.08), sy * yf, 0.01)); M.add(an)
        # the tie across each A and the joint at its top
        M.add(tube([(sx * (xe + 0.05), -0.55, 0.62), (sx * (xe + 0.05), 0.55, 0.62)], 0.03, 'paint', sides=6))
        jn = rpiece((-0.08, -0.13, -0.10), (0.08, 0.13, 0.08), 0.03, 'paint'); xform(jn, T(sx * xe, 0, zt)); M.add(jn)
        ec, _ = lathe([(0, 0), (0.056, 0), (0.05, 0.03), (0, 0.035)], 8, 'metalc')
        xform(ec, T(sx * (xe + 0.06), 0, zt) @ R(sx * PI / 2, 'Y')); M.add(ec)
    # two swings: a rubber strap seat and a wooden board, one pushed back a little
    for k, (x, tilt) in enumerate(((-0.62, 0.0), (0.62, math.radians(14)))):
        Mt = T(x, 0, zt) @ R(tilt, 'X')
        zs = 0.48 - zt
        for xx in (-0.23, 0.23):
            hg = torus(0.03, 0.008, 8, 4, 'metalc'); xform(hg, Mt @ T(xx, 0, -0.045) @ R(PI / 2, 'X')); M.add(hg)
            ch = tube([Mt @ Vector((xx, 0, -0.07)), Mt @ Vector((xx, 0, zs + 0.04))], 0.011, (0, 'metal', 'keep'), sides=4, caps=False)
            tile_natural(ch, 'chain', None, 0.3, swap=True)
            M.add(ch)
        if k == 0:
            path = [Mt @ Vector((xx, 0, zs + 0.02 - 0.045 * (1 - (xx / 0.24) ** 2))) for xx in np.linspace(-0.25, 0.25, 7)]
            sec = [(y, x) for (x, y) in chamfer_rect(0.17, 0.022, 0.008)]
            st = sweep(path, (0, 0, 1), sec, 'accent'); M.add(st)
        else:
            sb = rpiece((-0.27, -0.09, -0.02), (0.27, 0.09, 0.025), 0.012, 'accentk')
            tile_box(sb, 'grain', rng, 0.8); xform(sb, Mt @ T(0, 0, zs)); M.add(sb)
    return M


# ---------------------------------------------------------------- Sandpit
def sandpit(rng):
    M = Model('Sandpit', pal={'paint': (0.76, 0.59, 0.42), 'sand': (0.93, 0.83, 0.64), 'yellow': (0.98, 0.78, 0.30),
                              'red': (0.86, 0.36, 0.30)},
              ao_dist=0.25, grad=(0.85, 0.4))
    M.parts = {1: 'paint'}
    hw = 1.0; th = 0.12; zt = 0.30
    # timber sides: two boards stacked per side, corner posts
    for k, (a, b) in enumerate((((-hw, -hw + th / 2), (hw, -hw + th / 2)), ((-hw, hw - th / 2), (hw, hw - th / 2)),
                                ((-hw + th / 2, -hw + th), (-hw + th / 2, hw - th)), ((hw - th / 2, -hw + th), (hw - th / 2, hw - th)))):
        for z0, z1 in ((0.0, 0.145), (0.155, zt)):
            p0 = (a[0], a[1], (z0 + z1) / 2); p1 = (b[0], b[1], (z0 + z1) / 2)
            bd = member(p0, p1, th - 0.01, z1 - z0, 'paintk')
            tile_natural(bd, 'grain', rng, 2.0); M.add(bd)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = member((sx * (hw - 0.07), sy * (hw - 0.07), -0.02), (sx * (hw - 0.07), sy * (hw - 0.07), zt + 0.06), 0.13, 0.13, 'paintk', up=(0, 1, 0))
            tile_natural(p, 'grain', rng, 2.0); M.add(p)
    # corner seats: triangular boards on two corners
    for sx, sy in ((-1, 1), (1, 1), (1, -1)):
        tri = [(sx * (hw - 0.01), sy * (hw - 0.01)), (sx * (hw - 0.45), sy * (hw - 0.01)), (sx * (hw - 0.01), sy * (hw - 0.45))]
        V = [(x, y, zt + 0.005) for x, y in tri] + [(x, y, zt + 0.045) for x, y in tri]
        F = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
        sb, _ = bm_from(V, F, 'paintk'); recalc(sb)
        tile_box(sb, 'grain', rng, 0.8); M.add(sb)
    # the sand: soft heaps and a dug hole
    n = 11; a = hw - th + 0.01
    heaps = [((-0.35, 0.3), 0.32, 0.10), ((0.4, -0.2), 0.22, 0.07), ((0.2, 0.45), 0.18, -0.07)]

    def sfn(s, t):
        x = -a + 2 * a * s; y = -a + 2 * a * t
        z = 0.20 + 0.012 * math.sin(x * 7 + 1) * math.cos(y * 6)
        for (cx, cy), r, h in heaps:
            d = math.hypot(x - cx, y - cy) / r
            z += h * max(0.0, 1 - d * d) ** 1.5
        return (x, y, z)
    sd = grid(n, n, sfn, 'sand')
    tile_planar(sd, 'sand', lambda co: ((co.x + a) / (2 * a), (co.y + a) / (2 * a))); M.add(sd)
    # toys: a bucket on its side and a little rake
    bk, tags = lathe([(0, 0.0), (0.075, 0.0), (0.09, 0.14, 'S'), (0.097, 0.15), (0.088, 0.15, 'S'), (0.075, 0.02), (0, 0.02)], 12, 'yellow')
    xform(bk, T(0.42, -0.45, 0.31) @ R(math.radians(30), 'Z') @ R(PI / 2 - 0.15, 'X')); M.add(bk)
    Mr = T(-0.45, -0.35, 0.24) @ R(math.radians(-35), 'Z')
    M.add(tube([Mr @ Vector((0, -0.05, 0.0)), Mr @ Vector((0, 0.32, 0.02))], 0.012, 'red', sides=5))
    rk = cbox((0.16, 0.03, 0.02), 0.006, 'red'); xform(rk, Mr @ T(0, -0.06, 0.0)); M.add(rk)
    for k in range(5):
        tt = cbox((0.012, 0.035, 0.012), 0.003, 'red'); xform(tt, Mr @ T(-0.06 + 0.03 * k, -0.09, -0.005)); M.add(tt)
    return M


# ---------------------------------------------------------------- PicnicTable
def picnic(rng):
    M = Model('PicnicTable', pal={'paint': (0.76, 0.59, 0.42), 'metal': (0.40, 0.40, 0.42), 'wood': (0.84, 0.68, 0.46),
                                  'cream': (0.95, 0.90, 0.80), 'red': (0.84, 0.36, 0.30)},
              ao_dist=0.3)
    M.parts = {1: 'paint'}
    L = 1.8; zt = 0.76; zb = 0.45
    for k in range(5):
        y = -0.32 + 0.16 * k
        bd = member((-L / 2, y, zt - 0.022), (L / 2, y, zt - 0.022), 0.15, 0.045, 'paintk')
        tile_natural(bd, 'grain', rng, 2.0); M.add(bd)
    for sy in (-1, 1):
        for k in range(2):
            y = sy * (0.56 + 0.13 * k)
            bd = member((-L / 2 + 0.05, y, zb - 0.02), (L / 2 - 0.05, y, zb - 0.02), 0.12, 0.04, 'paintk')
            tile_natural(bd, 'grain', rng, 2.0); M.add(bd)
    for x in (-0.62, 0.62):
        # cleat under the top, the bench bearer, two crossing legs
        for (y0, y1, z, h) in ((-0.38, 0.38, zt - 0.075, 0.07), (-0.80, 0.80, zb - 0.075, 0.07)):
            bb = member((x, y0, z), (x, y1, z), 0.06, h, 'paintk')
            tile_natural(bb, 'grain', rng, 2.0); M.add(bb)
        for sy in (-1, 1):
            lg = member((x + 0.035 * sy, sy * 0.62, -0.02), (x + 0.035 * sy, sy * 0.14, zt - 0.05), 0.07, 0.09, 'paintk', up=(1, 0, 0))
            tile_natural(lg, 'grain', rng, 2.0); M.add(lg)
        for (y, z) in ((-0.6, zb - 0.075), (0.6, zb - 0.075), (-0.25, zt - 0.075), (0.25, zt - 0.075)):
            bt, _ = lathe([(0, 0), (0.014, 0), (0.012, 0.008), (0, 0.01)], 6, 'metal')
            xform(bt, T(x - 0.032, y, z) @ R(-PI / 2, 'Y')); M.add(bt)
    for sx in (-1, 1):
        br = member((sx * 0.6, 0, zb - 0.09), (sx * 0.12, 0, zt - 0.08), 0.06, 0.05, 'paintk')
        tile_natural(br, 'grain', rng, 2.0); M.add(br)
    M.add(member((-0.62, 0, zb - 0.11), (0.62, 0, zb - 0.11), 0.07, 0.06, 'paintk'))
    # a wicker picnic basket with a checked cloth peeking out
    bx, by = 0.35, 0.05
    bs = rpiece((-0.18, -0.12, 0.0), (0.18, 0.12, 0.15), (0.05, 0.05, 0.02), (0, 'wood', 'keep'), seg=(2, 2, 1))
    tile_box(bs, 'rope', rng, 0.5); xform(bs, T(bx, by, zt) @ R(0.2, 'Z')); M.add(bs)
    ld = rpiece((-0.19, -0.13, 0.0), (0.19, 0.13, 0.03), (0.05, 0.05, 0.012), (0, 'wood', 'keep'), seg=(2, 2, 1))
    tile_box(ld, 'rope', rng, 0.5); xform(ld, T(bx, by, zt + 0.15) @ R(0.2, 'Z')); M.add(ld)
    hd = tube([(x, 0, z) for x, z in ((-0.14, 0.17), (-0.12, 0.26), (0.0, 0.29), (0.12, 0.26), (0.14, 0.17))], 0.012, 'wood', sides=5)
    xform(hd, T(bx, by, zt) @ R(0.2, 'Z')); M.add(hd)

    def cloth(s, t):
        x = -0.17 + 0.34 * s
        return (x, -0.131 - 0.03 * t, 0.13 - 0.07 * t - 0.025 * math.sin(PI * s) * t)
    cl = grid(4, 2, cloth, None, fmat=lambda s, t: 'red' if (int(s * 4) + int(t * 2)) % 2 == 0 else 'cream')
    xform(cl, T(bx, by, zt) @ R(0.2, 'Z')); M.add(cl)
    cb = copy(cl); flip(cb); xform(cb, T(0, 0.002, 0)); M.add(cb)
    return M


# ---------------------------------------------------------------- ParkLamp
def park_lamp(rng):
    M = Model('ParkLamp', pal={'paint': (0.25, 0.39, 0.34), 'brass': (0.82, 0.68, 0.40), 'glow': (1.0, 0.94, 0.78)},
              dirt=PARK_DIRT, dirt_h=0.35, chips=0.5, chip=(0.50, 0.40, 0.30), ao_dist=0.25, streaks=0.8)
    M.parts = {1: 'paint'}
    base, _ = lathe([(0, 0), (0.24, 0.0), (0.24, 0.10, 'S'), (0.2, 0.13), (0.17, 0.16, 'S'), (0.17, 0.45, 'S'), (0.14, 0.50),
                     (0.10, 0.55, 'S'), (0.08, 0.62), (0, 0.62)], 8, 'paint', phase=0.5)
    M.add(base)
    M.add(tube([(0, 0, 0.6), (0, 0, 2.95)], 0.058, 'paint', sides=8, radii=list(np.linspace(0.064, 0.045, 2))))
    for z in (0.66, 1.25, 2.86):
        cl, _ = lathe([(0, z - 0.03), (0.085, z - 0.03), (0.09, z), (0.085, z + 0.03), (0, z + 0.03)], 8, 'paint'); M.add(cl)
    # the ladder rest: a bar through the post with ball ends
    M.add(tube([(-0.30, 0, 2.62), (0.30, 0, 2.62)], 0.018, 'paint', sides=6))
    for x in (-0.31, 0.31):
        b, _ = lathe([(0, -0.035), (0.03, -0.02), (0.035, 0.0), (0.03, 0.02), (0, 0.035)], 6, 'brass'); xform(b, T(x, 0, 2.62)); M.add(b)
    # crown scrolls under the lantern
    for k in range(4):
        a = PI / 4 + k * PI / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [Vector((0, 0, 2.86)) + d * 0.04, Vector((0, 0, 2.96)) + d * 0.13, Vector((0, 0, 3.05)) + d * 0.16, Vector((0, 0, 3.04)) + d * 0.12]
        M.add(tube(pts, 0.012, 'paint', sides=4))
    # the lantern: a tapering four-sided case, glowing glass, a pyramid cap and a finial
    cone, _ = lathe([(0, 2.92), (0.07, 2.95), (0.13, 3.02, 'S'), (0.13, 3.06), (0, 3.06)], 8, 'paint'); M.add(cone)
    zg0, zg1, w0, w1 = 3.06, 3.48, 0.105, 0.155
    for k in range(4):
        a = k * PI / 2

        def gl(s, t, a=a):
            w = w0 + (w1 - w0) * t
            P = Vector((-w + 2 * w * s, -w, zg0 + (zg1 - zg0) * t))
            return tuple(R(a, 'Z') @ P)
        g = grid(1, 1, gl, 'tex'); tile_keep(g, 'glow'); setmat(g, (0, 'glow', 'keep', 0.0)); M.add(g)
    for k in range(4):
        a = PI / 4 + k * PI / 2
        q = 2 ** 0.5
        M.add(member(R(a - PI / 4, 'Z') @ Vector((w0 + 0.005, -w0 - 0.005, zg0)), R(a - PI / 4, 'Z') @ Vector((w1 + 0.005, -w1 - 0.005, zg1)),
                     0.03, 0.03, 'paint', plain=True))
    ring = lathe([(0.0, zg1), (w1 * 2 ** 0.5 + 0.03, zg1, 'S'), (w1 * 2 ** 0.5 + 0.03, zg1 + 0.04, 'S'), (0.06, zg1 + 0.26), (0, zg1 + 0.27)], 4, 'paint', phase=0.5)[0]
    M.add(ring)
    fin, _ = lathe([(0, zg1 + 0.25), (0.03, zg1 + 0.27), (0.045, zg1 + 0.31), (0.02, zg1 + 0.35), (0.008, zg1 + 0.42), (0, zg1 + 0.43)], 8, 'brass'); M.add(fin)
    bot = lathe([(0.0, zg0 - 0.002), (w0 * 2 ** 0.5 + 0.02, zg0 - 0.002, 'S'), (w0 * 2 ** 0.5 + 0.02, zg0 + 0.03, 'S'), (0, zg0 + 0.03)], 4, 'paint', phase=0.5)[0]
    M.add(bot)
    M.at('Light', (0, 0, (zg0 + zg1) / 2))
    return M


# ---------------------------------------------------------------- DuckPond
WATER_DEEP, WATER_SHALLOW, FOAM = (0.20, 0.46, 0.52), (0.44, 0.76, 0.74), (0.88, 0.96, 0.94)


def duck_pond(rng):
    M = Model('DuckPond', pal={'paint': (0.33, 0.62, 0.64), 'accent': (0.46, 0.66, 0.36), 'mud': (0.62, 0.53, 0.42),
                               'brown': (0.42, 0.30, 0.22), 'pink': (0.97, 0.72, 0.78), 'yellow': (0.98, 0.84, 0.36)},
              ao_dist=0.3, grad=(0.9, 0.3))
    M.parts = {1: 'paint', 2: 'accent'}
    ph = rng.uniform(0, 6)

    def rad(a):
        return 1 + 0.07 * math.sin(3 * a + ph) + 0.05 * math.sin(5 * a + 2 * ph) + 0.03 * math.sin(2 * a)
    RX, RY, zw = 1.85, 1.15, 0.045
    NA = 36
    fr = [0.0, 0.35, 0.62, 0.82, 0.92, 0.965, 1.0]

    def P(a, f, z):
        r = rad(a)
        return (RX * r * f * math.cos(a), RY * r * f * math.sin(a), z)
    V = [P(0, 0, zw)]; Cc = [WATER_DEEP]
    for f in fr[1:]:
        for i in range(NA):
            a = 2 * PI * i / NA
            V.append(P(a, f, zw))
            if f <= 0.82:
                c = [WATER_DEEP[k] + (WATER_SHALLOW[k] - WATER_DEEP[k]) * sstep(0.2, 0.85, f) for k in range(3)]
            elif f < 0.95: c = WATER_SHALLOW
            elif f < 0.99: c = FOAM
            else: c = WATER_SHALLOW
            Cc.append(c)
    F = []
    for i in range(NA):
        F.append([0, 1 + i, 1 + (i + 1) % NA])
    for j in range(len(fr) - 2):
        b0 = 1 + j * NA; b1 = b0 + NA
        for i in range(NA):
            i2 = (i + 1) % NA
            F.append([b0 + i, b1 + i, b1 + i2, b0 + i2])
    wt, _ = bm_from(V, F, 'own1k'); recalc(wt)
    if wt.faces[0].normal.z < 0: flip(wt)
    lv = lay(wt)[4]
    for v, c in zip(wt.verts, Cc): v[lv] = s2l(c)
    tile_planar(wt, 'water', lambda co: (0.5 + co.x / (2.4 * RX), 0.5 + co.y / (2.4 * RY)))
    M.add(wt)
    # muddy bank from the water's edge up under the stones
    Vb = []; Fb = []
    for i in range(NA):
        a = 2 * PI * i / NA
        Vb += [P(a, 0.995, zw - 0.004), P(a, 1.07, 0.075), P(a, 1.13, 0.01)]
    for i in range(NA):
        i2 = (i + 1) % NA
        for k in range(2):
            Fb.append([i * 3 + k, i2 * 3 + k, i2 * 3 + k + 1, i * 3 + k + 1])
    bk, _ = bm_from(Vb, Fb, 'mud'); recalc(bk)
    if sum(f.normal.z for f in bk.faces) < 0: flip(bk)
    M.add(bk)
    # the stone edge
    a = rng.uniform(0, 0.3)
    while a < 2 * PI - 0.12:
        r = rad(a)
        sz = rng.uniform(0.15, 0.30)
        front = math.sin(a) < 0
        h = sz * rng.uniform(0.42, 0.7) * (0.85 if front else 1.0)
        c = Vector((RX * r * 1.08 * math.cos(a), RY * r * 1.09 * math.sin(a), h * 0.2))
        st = stone(c, (sz, sz * rng.uniform(0.7, 0.95), h), rng, cut=-0.01, planes=1.1)
        xform(st, T(c) @ R(rng.uniform(0, PI), 'Z') @ T(-c))
        M.add(st)
        a += (sz * 1.75) / (math.hypot(RX * math.sin(a), RY * math.cos(a)) * r)
    # lily pads with a notch, two flowers
    pads = [(-0.7, 0.25, 0.20), (-0.45, 0.45, 0.14), (-0.95, -0.05, 0.16), (0.55, -0.35, 0.18), (0.8, -0.1, 0.13),
            (0.3, 0.5, 0.15), (0.05, -0.55, 0.12)]
    for k, (x, y, r) in enumerate(pads):
        n = 11; gap = 0.5
        Vp = [(0, 0, 0)] + [(r * math.cos(gap / 2 + (2 * PI - gap) * i / n), r * math.sin(gap / 2 + (2 * PI - gap) * i / n), 0) for i in range(n + 1)]
        Fp = [[0, i + 1, i + 2] for i in range(n)]
        pd, _ = bm_from(Vp, Fp, 'accentk')
        if pd.faces[0].normal.z < 0: flip(pd)
        tile_planar(pd, 'lily', lambda co, r=r: (0.5 + co.x / (2 * r), 0.5 + co.y / (2 * r)))
        for v in pd.verts:
            d = v.co.length / r; v.co.z = 0.006 * (1 - d) + 0.004 * d
        xform(pd, T(x, y, zw + 0.004) @ R(rng.uniform(0, 2 * PI), 'Z')); M.add(pd)
    for (x, y) in ((-0.62, 0.2), (0.58, -0.3)):
        petals = []
        for ring_, (n, rr, lift, sc) in enumerate(((8, 0.075, 0.035, 1.0), (6, 0.05, 0.05, 0.9))):
            for i in range(n):
                a = 2 * PI * (i + 0.5 * ring_) / n
                d = Vector((math.cos(a), math.sin(a), 0)); s = Vector((-math.sin(a), math.cos(a), 0))
                base = Vector((0, 0, 0.01))
                tip = d * rr + Vector((0, 0, lift))
                Vf = [base - s * 0.014, base + s * 0.014, tip + s * 0.016 - d * 0.02, tip]
                pt, _ = bm_from(Vf, [(0, 1, 2), (0, 2, 3)], (0, 'pink', 'white'))
                pt2 = copy(pt); flip(pt2)
                petals += [pt, pt2]
        ctr, _ = lathe([(0, 0.01), (0.02, 0.02), (0.016, 0.035), (0, 0.04)], 6, (0, 'yellow', 'white'))
        fl = join(*(petals + [ctr])); xform(fl, T(x, y, zw + 0.008)); M.add(fl)
    # reeds and bulrushes at the back left
    rx, ry = -1.25, 0.95
    for k in range(13):
        a = rng.uniform(0, 2 * PI); rr = rng.uniform(0, 0.22)
        bx_, by_ = rx + rr * math.cos(a), ry + rr * math.sin(a)
        L = rng.uniform(0.55, 1.0); lean = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.15), 1)).normalized()
        tip = Vector((bx_, by_, 0.02)) + lean * L + Vector((lean.x, lean.y, 0)) * L * 0.25
        mid = Vector((bx_, by_, 0.02)) + lean * L * 0.55
        bl = tube([(bx_, by_, 0.0), mid, tip], 0.014, 'accent', sides=3, radii=[0.016, 0.01, 0.002])
        M.add(bl)
    for k in range(3):
        bx_, by_ = rx + rng.uniform(-0.12, 0.12), ry + rng.uniform(-0.12, 0.12)
        top = Vector((bx_ + rng.uniform(-0.08, 0.08), by_, rng.uniform(0.95, 1.2)))
        M.add(tube([(bx_, by_, 0.0), top], 0.007, 'accent', sides=3))
        hd, _ = lathe([(0, -0.08), (0.024, -0.07), (0.026, 0.0), (0.022, 0.07), (0, 0.08)], 6, (0, 'brown', 'white'))
        xform(hd, T(top - Vector((0, 0, 0.12)))); M.add(hd)
    M.extra = {'water': zw}
    return M


# ---------------------------------------------------------------- Gazebo
def gazebo(rng):
    M = Model('Gazebo', pal={'paint': (0.96, 0.93, 0.85), 'accent': (0.40, 0.59, 0.56), 'stone': (0.84, 0.78, 0.72),
                             'wood': (0.76, 0.60, 0.44), 'brick': (0.82, 0.56, 0.45), 'glow': (1.0, 0.92, 0.72)},
              dirt=PARK_DIRT, dirt_h=0.35, chips=0.5, chip=(0.62, 0.52, 0.42), ao_dist=0.5, streaks=0.6)
    M.parts = {1: 'paint', 2: 'accent'}
    N = 8; ph = 0.5
    zf = 0.48
    Rp = 2.08
    # plinth: brick drum with a stone cap, wooden boards on top
    pl, tags = lathe([(Rp - 0.02, -0.02), (Rp, 0.40, 'S'), (Rp + 0.06, 0.41), (Rp + 0.07, zf, 'S'), (0.0, zf)], N,
                     [(0, 'brick', 'keep'), (0, 'stone', 'keep'), (0, 'stone', 'keep'), (0, 'wood', 'keep')], phase=ph)
    tile_lathe(pl, tags, 'bricks', (0,), N, per_face=True)
    tile_lathe(pl, tags, 'stone', (1, 2), N, per_face=True)
    tile_planar(pl, 'slats', lambda co: (0.5 + co.x / (2 * Rp + 0.2), 0.5 + co.y / (2 * Rp + 0.2)), faces=[f for f, s, i in tags if s == 3])
    M.add(pl)
    yfront = -(Rp + 0.07) * math.cos(PI / N)
    for k in range(3):
        h = zf - 0.16 * k
        st = rpiece((-0.72, yfront - 0.30 * (k + 1), -0.02), (0.72, yfront + 0.02, h - 0.01), 0.02, (0, 'stone', 'keep'))
        tile_box(st, 'stone', rng, 1.5); M.add(st)
    # eight turned posts at the corners
    Rc = 1.78
    angs = [2 * PI * (k + ph) / N for k in range(N)]
    zb_ = 2.88
    for a in angs:
        x, y = Rc * math.cos(a), Rc * math.sin(a)
        po, _ = lathe([(0, zf), (0.10, zf), (0.10, zf + 0.22, 'S'), (0.07, zf + 0.26), (0.055, zf + 0.32), (0.05, zb_ - 0.3),
                       (0.07, zb_ - 0.22, 'S'), (0.09, zb_ - 0.18), (0.09, zb_), (0, zb_)], 6, 'paint', phase=0.0)
        xform(po, T(x, y, 0)); M.add(po)
    # railings in every bay but the front, with turned balusters
    for k in range(N):
        a0, a1 = angs[k], angs[(k + 1) % N]
        p0 = Vector((Rc * math.cos(a0), Rc * math.sin(a0), 0)); p1 = Vector((Rc * math.cos(a1), Rc * math.sin(a1), 0))
        mid = (p0 + p1) / 2
        if mid.y < -1.5 and abs(mid.x) < 0.3: continue
        d = (p1 - p0).normalized()
        q0, q1 = p0 + d * 0.06, p1 - d * 0.06
        M.add(member(q0 + Vector((0, 0, zf + 0.92)), q1 + Vector((0, 0, zf + 0.92)), 0.09, 0.06, 'paint'))
        M.add(member(q0 + Vector((0, 0, zf + 0.12)), q1 + Vector((0, 0, zf + 0.12)), 0.07, 0.05, 'paint', plain=True))
        for t in np.linspace(0.2, 0.8, 4):
            b = q0.lerp(q1, t)
            bl, _ = lathe([(0.02, zf + 0.14), (0.034, zf + 0.42), (0.018, zf + 0.9)], 4, 'paintc', phase=0.5)
            xform(bl, T(b.x, b.y, 0)); M.add(bl)
    # the eave beam and a lacy arch in each bay
    ring = [(Rc * math.cos(a), Rc * math.sin(a), zb_ + 0.07) for a in angs]
    sec = [(y, x) for (x, y) in chamfer_rect(0.14, 0.16, 0.03)]
    M.add(sweep(ring, (0, 0, 1), sec, 'paint', caps=False, closed_path=True))
    for k in range(N):
        a0, a1 = angs[k], angs[(k + 1) % N]
        p0 = Vector((Rc * math.cos(a0), Rc * math.sin(a0), zb_)); p1 = Vector((Rc * math.cos(a1), Rc * math.sin(a1), zb_))
        d = p1 - p0
        pts = []
        for t in np.linspace(0, 1, 7):
            p = p0 + d * t
            p.z = zb_ - 0.04 - 0.30 * (1 - (2 * t - 1) ** 2) ** 0.6 * (1 if 0 < t < 1 else 0) - (0.28 if t in (0.0, 1.0) else 0)
            pts.append(p)
        pts[0] = p0 + d * 0.04 + Vector((0, 0, -0.28)); pts[-1] = p1 - d * 0.04 + Vector((0, 0, -0.28))
        out = Vector((d.y, -d.x, 0)).normalized()
        M.add(sweep(pts, lambda i, p, t, out=out: out, [(0.02, 0.03), (-0.02, 0.03), (-0.02, -0.03), (0.02, -0.03)], 'paintc'))
    # the roof: an ogee bell of shingles, a scalloped valance, a ceiling, a cupola and finial
    q = 1 / math.cos(PI / N)
    Re = 2.22
    prof = [(Re * q, zb_ + 0.08), (Re * q, zb_ + 0.20, 'S')]
    for t in np.linspace(0.08, 1.0, 6):
        r = Re * (1 - t) + 0.32 * t
        z = zb_ + 0.20 + (4.15 - zb_ - 0.20) * (t ** 1.6 * 0.6 + t * 0.4)
        prof.append((r * q, z))
    prof[-1] = (0.32 * q, 4.15, 'S')
    prof += [(0.0, 4.15)]
    rf, tags = lathe(prof, N, ['accent'] + ['accentk'] * (len(prof) - 3) + ['accentc'], phase=ph)
    tile_lathe(rf, tags, 'shingle', tuple(range(1, len(prof) - 2)), N, per_face=True)
    M.add(rf)
    ceil, _ = lathe([(Re * q, zb_ + 0.08), (1.4 * q, zb_ + 0.25), (0.0, zb_ + 0.55)], N, 'paintc', phase=ph)
    flip(ceil); M.add(ceil)
    for k in range(N):
        a0, a1 = 2 * PI * (k + ph) / N, 2 * PI * (k + 1 + ph) / N
        c0 = Vector((Re * q * math.cos(a0), Re * q * math.sin(a0), zb_ + 0.08))
        c1 = Vector((Re * q * math.cos(a1), Re * q * math.sin(a1), zb_ + 0.08))

        def vfn(s, t, c0=c0, c1=c1):
            p = c0.lerp(c1, s)
            hang = 0.06 + 0.06 * abs(math.sin(PI * s * 2))
            return (p.x, p.y, p.z - hang * (1 - t))
        va = grid(6, 1, vfn, 'paintc')
        cm = va.faces[0].calc_center_median()
        if va.faces[0].normal.dot(Vector((cm.x, cm.y, 0))) < 0: flip(va)
        vb = copy(va); flip(vb)
        for v in vb.verts:
            dd = Vector((v.co.x, v.co.y, 0)).normalized(); v.co -= dd * 0.006
        M.add(va); M.add(vb)
    cu, ctags = lathe([(0.30, 4.12), (0.30, 4.38, 'S'), (0.44, 4.38), (0.44, 4.43, 'S'), (0.05, 4.78), (0.0, 4.80)], N,
                      ['paint', 'accentc', 'accent', 'accentk', 'accentc'], phase=ph)
    tile_lathe(cu, ctags, 'shingle', (3,), N, per_face=True)
    M.add(cu)
    fn_, _ = lathe([(0, 4.76), (0.05, 4.78), (0.06, 4.84), (0.035, 4.9), (0.01, 5.05), (0, 5.07)], 8, 'brass'); M.add(fn_)
    # a lantern hanging from the ceiling
    M.add(tube([(0, 0, zb_ + 0.5), (0, 0, 2.62)], 0.008, 'dark', sides=4, caps=False))
    lt, _ = lathe([(0, 2.30), (0.07, 2.33, 'S'), (0.09, 2.47, 'S'), (0.11, 2.50), (0.04, 2.60), (0, 2.62)], 6,
                  [(0, 'dark', 'white'), (0, 'glow', 'keep', 0.0), (0, 'dark', 'white'), (0, 'dark', 'white'), (0, 'dark', 'white')])
    tile_lathe(lt, [t for t in _ if t[1] == 1], 'glow', (1,), 6, per_face=True)
    M.add(lt)
    M.at('Light', (0, 0, 2.40))
    M.extra = {'floor': zf}
    return M


BUILDERS = [('Slide', slide), ('SeeSaw', seesaw), ('SwingSet', swingset), ('Sandpit', sandpit), ('PicnicTable', picnic),
            ('ParkLamp', park_lamp), ('DuckPond', duck_pond), ('Gazebo', gazebo)]
