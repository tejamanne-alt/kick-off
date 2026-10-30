# Building-site models of the WORKS kit (kit_works.py): the backdrop tower crane, the gameplay
# crane pieces (hook, trolley, slung load), the builder's hoist (mast tile, mast cap, cage), the
# rolling concrete pipe, and the site dressing (scaffold, fence, portaloo, skip, mixer,
# wheelbarrow, pipe stack, steel beams, site cabin, digger).
# Game z maps to Blender +Y, game y to Blender Z; fronts face -Y (toward the camera).
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_works_geo import *

CONCRETE = (0.76, 0.74, 0.70)
OXIDE = (0.66, 0.36, 0.26)


def _front(M):
    M.attach.append(('Front', (0.0, -1.0, 0.0)))


def wood_box(lo, hi, band=0, r=0.008, along=0, mat='tex'):
    """A timber board / bearer textured with one of the four boards of the 'wood' tile."""
    bm = cbox(lo, hi, r, mat)
    lo = Vector(lo); hi = Vector(hi)
    others = [i for i in range(3) if i != along]

    def fn(co, f):
        s = (co[along] - lo[along]) / max(hi[along] - lo[along], 1e-5)
        n = f.normal
        a2 = others[0] if abs(n[others[0]]) < abs(n[others[1]]) else others[1]
        tt = (co[a2] - lo[a2]) / max(hi[a2] - lo[a2], 1e-5)
        return (s, (band + 0.1 + 0.8 * tt) / 4.0)
    bm.normal_update()
    return settile(bm, 'wood', fn)


def section_beam(x0, x1, yc, zb, depth, bf, tf, tw, mat, end_mat=None, rot=0.0):
    """An I / H beam lying along X from x0 to x1, centred on y = yc, its bottom at zb."""
    h = depth
    pts = [(-bf / 2, 0), (bf / 2, 0), (bf / 2, tf), (tw / 2, tf), (tw / 2, h - tf), (bf / 2, h - tf), (bf / 2, h),
           (-bf / 2, h), (-bf / 2, h - tf), (-tw / 2, h - tf), (-tw / 2, tf), (-bf / 2, tf)]
    bm = extrude_poly(pts, x1 - x0, mat)
    if end_mat:
        setmat(bm, end_mat, [f for f in bm.faces if len(f.verts) > 4])
    xform(bm, T(x0, yc, zb) @ R(rot, 'Z') @ basis((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)))
    return bm


def pipe_bm(ro, ri, length, n, mat, bevel=0.03):
    """A concrete pipe along local Z, centred, with chamfered ends."""
    h = length / 2; b = bevel; b2 = bevel * 0.6
    prof = [(ro - b, -h), (ro, -h + b), (ro, h - b), (ro - b, h), (ri + b2, h), (ri, h - b2), (ri, -h + b2), (ri + b2, -h), (ro - b, -h)]
    bm, _ = lathe(prof, n, mat, phase=0.5, sm=0)
    return bm


def wheel_bm(r, w, n=14, hub='metal', tyre='rubber', rim_r=0.6):
    """A tyre and hub along local Z (the axle)."""
    hw = w / 2
    prof = [(0.0, -hw * 0.7), (r * rim_r, -hw * 0.8), (r * 0.86, -hw), (r, -hw * 0.45), (r, hw * 0.45),
            (r * 0.86, hw), (r * rim_r, hw * 0.8), (0.0, hw * 0.7)]
    mats = [hub, tyre, tyre, tyre, tyre, tyre, hub]
    bm, _ = lathe(prof, n, mats, phase=0.0, sm=0)
    return bm


# ---------------------------------------------------------------- TowerCrane (backdrop)
def tower_crane():
    """A backdrop tower crane: about 38 m to the top of its tower head, a 40 m jib along +X and
    a counter-jib with counterweights along -X; the lattice is painted on the faces between
    modelled chords. Static; origin at the centre of the mast's footing."""
    M = Model('TowerCrane', p1=SITE_YELLOW, p2=(0.95, 0.92, 0.84), ppm=7, ao_radius=1.6,
              grime=dict(rust=0.15, chips=0.1, streaks=0.4, dirt_h=1.2, streak_len=3.0, mottle=0.08))
    # footing and the mast's feet
    M.add(cbox((-2.6, -2.6, 0.0), (2.6, 2.6, 0.8), 0.06, 'conc'))
    for x in (-0.9, 0.9):
        for y in (-0.9, 0.9):
            M.add(cbox((x - 0.28, y - 0.28, 0.8), (x + 0.28, y + 0.28, 1.1), 0.03, 'p1d'))
    hm = 0.9; z0, zt = 1.0, 30.2
    for x in (-hm, hm):
        for y in (-hm, hm):
            M.add(bar((x, y, z0), (x, y, zt), 0.22, 'p1'))
    nb = 15; bh = (zt - z0) / nb
    for k in range(nb):
        za, zb_ = z0 + k * bh, z0 + (k + 1) * bh
        for (fx, fy, nx, ny) in ((0, -1, 1, 0), (1, 0, 0, 1), (0, 1, -1, 0), (-1, 0, 0, -1)):
            # a face quad on the chords' centre plane, between the chords
            c = Vector((fx * hm, fy * hm, 0)); t = Vector((nx, ny, 0)); w = hm - 0.11
            V = [c - t * w + Vector((0, 0, za)), c + t * w + Vector((0, 0, za)), c + t * w + Vector((0, 0, zb_)), c - t * w + Vector((0, 0, zb_))]
            bm, _ = bm_from(V, [(0, 1, 2, 3)], 'tex')
            fix_out = Vector((fx, fy, 0))
            bm.normal_update()
            if bm.faces[0].normal.dot(fix_out) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            bm.verts.ensure_lookup_table()
            settile(bm, 'lattice', lambda co, f, c=c, t=t, w=w, za=za: (((co - c).dot(t) + w) / (2 * w), (co.z - za) / bh))
            M.add(bm)
    # climbing collar and the slewing unit
    M.add(cbox((-1.25, -1.25, zt - 0.1), (1.25, 1.25, zt + 0.5), 0.05, 'p1d'))
    M.add(xform(cyl(1.15, 0.0, 0.45, 20, 'iron', bevel=0.05), T(0, 0, zt + 0.5)))
    zs = zt + 0.95
    M.add(cbox((-1.6, -1.1, zs), (1.6, 1.1, zs + 0.55), 0.06, 'p1'))
    zj = zs + 0.55                               # the jibs' bottom chords
    # tower head: a tapering lattice pyramid
    ht = 6.2; top = zj + ht
    hb, htp = 0.85, 0.28
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for (sx, sy) in corners:
        M.add(bar((sx * hb, sy * hb, zj), (sx * htp, sy * htp, top), 0.18, 'p1'))
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 4]
        for seg in range(2):
            f0, f1 = seg / 2, (seg + 1) / 2
            h0, h1 = hb + (htp - hb) * f0, hb + (htp - hb) * f1
            zz0, zz1 = zj + ht * f0, zj + ht * f1
            V = [(ax * h0, ay * h0, zz0), (bx * h0, by * h0, zz0), (bx * h1, by * h1, zz1), (ax * h1, ay * h1, zz1)]
            bm, _ = bm_from(V, [(0, 1, 2, 3)], 'tex')
            out = Vector(((ax + bx) / 2, (ay + by) / 2, 0))
            if bm.faces[0].normal.dot(out) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            bm.normal_update()
            uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
            lu = L(bm)[6]; lt = L(bm)[2]
            f = bm.faces[0]; f[lt] = tile_id('lattice')
            for l in f.loops:
                p = l.vert.co
                d = [Vector(v).__sub__(p).length for v in V]
                l[lu].uv = uvs[d.index(min(d))]
            M.add(bm)
    M.add(cbox((-0.45, -0.45, top - 0.05), (0.45, 0.45, top + 0.12), 0.03, 'p1d'))
    M.add(xform(cyl(0.09, 0, 0.16, 8, 'red'), T(0, 0, top + 0.12)))
    # jib: a triangular lattice, bottom chords at y = +-0.75, top chord on the centre line
    x0, x1 = 1.3, 41.0
    jh = 1.55
    tipk = 0.62

    def jy(x):
        return 0.75 * (1 - (1 - tipk) * max(0.0, (x - 30.0) / (x1 - 30.0)))

    def jz(x):
        return jh * (1 - (1 - tipk) * max(0.0, (x - 30.0) / (x1 - 30.0)))
    xs = [x0 + (x1 - x0) * i / 16 for i in range(17)]
    for sy in (-1, 1):
        M.add(tube([(x, sy * jy(x), zj) for x in (x0, 30.0, x1)], 0.09, 'p1', sides=4, sm=2))
    M.add(tube([(x, 0, zj + jz(x)) for x in (x0, 30.0, x1)], 0.08, 'p1', sides=4, sm=2))
    for i in range(16):
        xa, xb = xs[i], xs[i + 1]
        faces = [((xa, -jy(xa), zj), (xb, -jy(xb), zj), (xb, 0, zj + jz(xb)), (xa, 0, zj + jz(xa)), Vector((0, -1, 0.4))),
                 ((xb, jy(xb), zj), (xa, jy(xa), zj), (xa, 0, zj + jz(xa)), (xb, 0, zj + jz(xb)), Vector((0, 1, 0.4))),
                 ((xa, jy(xa), zj), (xb, jy(xb), zj), (xb, -jy(xb), zj), (xa, -jy(xa), zj), Vector((0, 0, -1)))]
        for k, (a, b, c, d, out) in enumerate(faces):
            bm, _ = bm_from([a, b, c, d], [(0, 1, 2, 3)], 'tex')
            if bm.faces[0].normal.dot(out) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
            bm.normal_update()
            lu = L(bm)[6]; lt = L(bm)[2]; f = bm.faces[0]; f[lt] = tile_id('latjib')
            pts = [Vector(a), Vector(b), Vector(c), Vector(d)]
            uvs = [(0, 0), (1, 0), (1, 1), (0, 1)] if k < 2 else [(0, 0), (1, 0), (1, 1), (0, 1)]
            for l in f.loops:
                dd = [(p - l.vert.co).length for p in pts]
                l[lu].uv = uvs[dd.index(min(dd))]
            M.add(bm)
    M.add(cbox((x1 - 0.1, -0.5, zj - 0.1), (x1 + 0.15, 0.5, zj + 0.9), 0.03, 'p1d'))
    M.add(xform(cyl(0.07, 0, 0.12, 8, 'red'), T(x1, 0, zj + 0.95)))
    # counter-jib: two box girders, a grating walkway with handrails, the winch and counterweights
    cx0, cx1 = -1.3, -13.5
    for sy in (-1, 1):
        M.add(cbox((cx1, sy * 0.95 - 0.14, zj), (cx0, sy * 0.95 + 0.14, zj + 0.55), 0.04, 'p1'))
    gr = box((cx1 + 0.3, -0.81, zj + 0.42), (cx0, 0.81, zj + 0.47), 'iron', skip=('-x', '+x'))
    settile(gr, 'grate', lambda co, f: ((co.x - cx1) / (cx0 - cx1), (co.y + 0.81) / 1.62), faces=faces_facing(gr, (0, 0, 1), 0.9), mat='tex')
    M.add(gr)
    for sy in (-1, 1):
        y = sy * 1.05
        for k in range(7):
            x = cx0 - 0.2 - k * 1.9
            M.add(bar((x, y, zj + 0.55), (x, y, zj + 1.6), 0.07, 'p1'))
        M.add(bar((cx0 - 0.2, y, zj + 1.6), (cx1 + 0.4, y, zj + 1.6), 0.08, 'p1'))
        M.add(bar((cx0 - 0.2, y, zj + 1.1), (cx1 + 0.4, y, zj + 1.1), 0.06, 'p1'))
    M.add(rbox((-6.4, -0.75, zj + 0.47), (-4.2, 0.75, zj + 1.55), (0.12, 0.12, 0.12), 'p1', seg=(1, 1, 1)))
    M.feat('front', 'lines', lines=[[(-5.9, zj + 0.6), (-5.9, zj + 1.45)], [(-4.7, zj + 0.6), (-4.7, zj + 1.45)]], w=0.04, col=(0.6, 0.6, 0.6))
    M.add(xform(cyl(0.38, -0.8, 0.8, 14, 'iron', bevel=0.05), T(-3.4, 0, zj + 0.85) @ R(PI / 2, 'X')))
    for k in range(4):
        xa = cx1 + 0.25 + k * 0.72
        M.add(cbox((xa, -1.0, zj - 2.2), (xa + 0.66, 1.0, zj + 0.5), 0.05, 'conc'))
    M.feat('front', 'streaks', a0=cx1 + 0.3, a1=cx1 + 3.0, top=zj + 0.4, n=40, length=(0.4, 2.0), col=(0.70, 0.62, 0.54), alpha=(0.3, 0.6), width=(0.02, 0.08))
    # tie bars from the tower head to the jib and the counter-jib
    M.add(bar((0.2, 0, top - 0.1), (24.0, 0, zj + jz(24.0)), 0.09, 'iron', sides=4))
    M.add(bar((0.2, 0, top - 0.1), (37.0, 0, zj + jz(37.0)), 0.07, 'iron', sides=4))
    for sy in (-1, 1):
        M.add(bar((-0.2, sy * 0.15, top - 0.1), (cx1 + 0.6, sy * 0.9, zj + 0.55), 0.09, 'iron', sides=4))
    # the cab, on the front (-Y) of the slewing platform, under the jib root
    cab = rbox((0.15, -2.45, zs - 1.55), (1.85, -1.15, zs + 0.5), (0.18, 0.18, 0.18), 'p2', seg=(2, 2, 2))
    M.add(cab)
    for (lo, hi, axes) in (((0.3, -2.47, zs - 0.95), (1.7, -2.44, zs + 0.3), (0, 2)),
                           ((1.84, -2.3, zs - 0.95), (1.87, -1.3, zs + 0.3), (1, 2))):
        g = box(lo, hi, 'tex')
        tile_box(g, 'glass', Vector(lo), Vector(hi), axes=axes)
        M.add(g)
    M.add(cbox((0.2, -1.2, zs - 0.4), (1.8, -1.0, zs + 0.1), 0.03, 'p1d'))
    # trolley, hoist ropes and the hook block, about a third of the way out
    xt = 26.0
    M.add(cbox((xt - 0.8, -0.85, zj - 0.55), (xt + 0.8, 0.85, zj - 0.05), 0.05, 'p1d'))
    zh = zj - 9.0
    for dx in (-0.18, 0.18):
        M.add(bar((xt + dx, 0, zj - 0.5), (xt + dx, 0, zh + 0.9), 0.05, 'dark', sides=4))
    hb_ = rbox((xt - 0.42, -0.25, zh), (xt + 0.42, 0.25, zh + 0.95), (0.1, 0.1, 0.1), 'p1', seg=(1, 1, 1))
    ff = faces_facing(hb_, (0, -1, 0), 0.9) + faces_facing(hb_, (0, 1, 0), 0.9)
    settile(hb_, 'hazard', lambda co, f: ((co.x - xt + 0.42) / 0.84, (co.z - zh) / 0.95), faces=ff, mat='tex')
    M.add(hb_)
    hk = [(xt, 0, zh), (xt, 0, zh - 0.35)]
    for i in range(1, 9):
        a = PI + PI * 1.25 * i / 8
        hk.append((xt + 0.22 + 0.22 * math.cos(a), 0, zh - 0.55 + 0.22 * math.sin(a)))
    M.add(tube(hk, 0.07, 'iron', sides=6))
    _front(M)
    M.extra = {'height': round(top + 0.28, 2), 'jibLength': x1, 'counterJib': -cx1, 'jibHeight': round(zj, 2), 'hookAt': [xt, 0.0, round(zh - 0.6, 2)]}
    return M


# ---------------------------------------------------------------- CraneHook (gameplay)
HOOK_THROAT = -0.318


def crane_hook():
    """The hook block on the game crane's cable. Origin = the cable attach point on top (the game's
    CraneRig.hookLocal); the block hangs below it and the hook's throat (where the load's master
    ring sits) is 0.318 m below the origin."""
    M = Model('CraneHook', p1=SITE_YELLOW, ppm=260, ground=False, grime=dict(ground=0.0, rust=0.15, streaks=0.4, chips=0.4))
    M.add(cyl(0.028, -0.05, 0.0, 8, 'iron', bevel=0.006))
    M.add(cyl(0.05, -0.065, -0.04, 10, 'iron', bevel=0.006))
    blk = rbox((-0.13, -0.075, -0.19), (0.13, 0.075, -0.05), (0.035, 0.03, 0.035), 'p1', seg=(2, 1, 2))
    ff = faces_facing(blk, (0, -1, 0), 0.9) + faces_facing(blk, (0, 1, 0), 0.9)
    settile(blk, 'hazard', lambda co, f: ((co.x + 0.13) / 0.26, (co.z + 0.19) / 0.14), faces=ff, mat='tex')
    M.add(blk)
    for sx in (-1, 1):
        M.add(xform(cyl(0.03, 0, 0.012, 8, 'chrome', bevel=0.004), T(sx * 0.13, 0, -0.12) @ R(sx * PI / 2, 'Y')))
    M.add(cyl(0.032, -0.225, -0.19, 10, 'iron', bevel=0.006))
    M.add(cyl(0.022, -0.255, -0.225, 8, 'metal'))
    # the hook: a shank, then a bowl curling round to the tip (opening toward +X)
    cr = 0.046; czc = -0.272
    path = [(0, 0, -0.25), (0, 0, czc)]
    for i in range(1, 10):
        a = PI + PI * 1.3 * i / 9
        path.append((cr + cr * math.cos(a), 0, czc + cr * math.sin(a)))
    sc = [1.0, 1.0] + [1.0 - 0.45 * (i / 9) ** 1.5 for i in range(1, 10)]
    sec = [(0.018 * math.cos(2 * PI * k / 8), 0.016 * math.sin(2 * PI * k / 8)) for k in range(8)]
    M.add(sweep(path, sec, 'metal', up=(0, 1, 0), scales=sc, sm=1))
    # safety latch
    M.add(bar((0.004, 0, -0.245), (cr * 2 + 0.008, 0, czc + 0.02), 0.008, 'chrome', sides=4))
    M.attach.append(('Throat', (cr, 0.0, HOOK_THROAT)))
    _front(M)
    M.extra = {'origin': 'cable attach point (top)', 'throat': [cr, 0.0, HOOK_THROAT]}
    return M


# ---------------------------------------------------------------- CraneTrolley (gameplay)
def crane_trolley():
    """The trolley that runs along the game crane's jib (local X along the jib). Origin = the
    trolley's centre, as the game positions it; Attach.Cable is where the hoist rope leaves."""
    M = Model('CraneTrolley', p1=SITE_YELLOW, ppm=160, ground=False, grime=dict(ground=0.0, rust=0.2, streaks=0.5))
    # a chassis frame with four wheels on top that run on the jib's bottom chords (y = +-0.3)
    M.add(rbox((-0.34, -0.26, -0.02), (0.34, 0.26, 0.08), (0.03, 0.03, 0.03), 'p1', seg=(1, 1, 1)))
    for sy in (-1, 1):
        M.add(cbox((-0.33, sy * 0.3 - 0.015, 0.0), (0.33, sy * 0.3 + 0.015, 0.1), 0.008, 'p1d'))
        for x in (-0.22, 0.22):
            M.add(cbox((x - 0.035, sy * 0.3 - 0.06, 0.06), (x + 0.035, sy * 0.3 + 0.06, 0.13), 0.01, 'p1d'))
            w = wheel_bm(0.055, 0.035, n=10, hub='metal', tyre='iron', rim_r=0.5)
            xform(w, T(x, sy * 0.36, 0.15) @ R(PI / 2, 'X'))
            M.add(w)
    # the rope sheaves underneath, in a little block, and a hazard band on the front
    M.add(cbox((-0.2, -0.07, -0.13), (0.2, 0.07, -0.02), 0.015, 'p1d'))
    for x in (-0.1, 0.1):
        s_ = wheel_bm(0.06, 0.03, n=10, hub='chrome', tyre='iron', rim_r=0.4)
        xform(s_, T(x, 0, -0.08) @ R(PI / 2, 'X'))
        M.add(s_)
    hz = box((-0.3, -0.265, 0.0), (0.3, -0.26, 0.06), 'iron', skip=('+y',))
    settile(hz, 'hazard', lambda co, f: ((co.x + 0.3) / 0.6, co.z / 0.06), faces=faces_facing(hz, (0, -1, 0), 0.9), mat='tex')
    M.add(hz)
    M.attach.append(('Cable', (0.0, 0.0, -0.1)))
    _front(M)
    M.extra = {'origin': 'trolley centre', 'cable': [0.0, 0.0, -0.1]}
    return M


# ---------------------------------------------------------------- CraneLoad (gameplay)
LOAD_W = 2.6


def crane_load():
    """The slung load the game's moving platform becomes on a crane: a bundle of five steel
    H-beams on timber bearers, strapped, with its lifting gear. Origin = the platform's collider
    centre: the walkable top is at z = +0.175, the bearers' feet at -0.175 (the collider is
    2.6 x 0.35). Chains rise from lugs on the back beam (y = 0.72) to a yellow spreader beam,
    slings run on to a master ring that hangs in the hook; Attach.Hook (0, 0.72, 3.86) is where
    the CraneHook's origin (the cable attach point) goes, the game's CraneRig.hookLocal."""
    M = Model('CraneLoad', p1=(0.60, 0.33, 0.26), p2=SITE_YELLOW, ppm=110, ground=False,
              grime=dict(ground=0.0, rust=0.45, streaks=0.6, chips=0.4))
    hw = LOAD_W / 2
    ztop = 0.175; zb = -0.065
    for k in range(5):
        y = -0.6 + 0.3 * k
        M.add(section_beam(-hw, hw, y, zb, ztop - zb, 0.284, 0.028, 0.018, 'p1', end_mat='yellow'))
    for x in (-0.85, 0.85):
        M.add(wood_box((x - 0.08, -0.8, -0.175), (x + 0.08, 0.8, zb), band=(1 if x < 0 else 2), r=0.012, along=1))
    # ratchet straps
    for x in (-0.5, 0.5):
        y0, y1, za, zc = -0.756, 0.756, zb - 0.004, ztop + 0.004
        rr = 0.02
        path = []
        for (cy, cz, a0) in ((y1 - rr, zc - rr, 0.0), (y0 + rr, zc - rr, PI / 2), (y0 + rr, za + rr, PI), (y1 - rr, za + rr, 1.5 * PI)):
            for i in range(3):
                a = a0 + (PI / 2) * i / 2
                path.append((x, cy + rr * math.cos(a), cz + rr * math.sin(a)))
        sec = [(-0.025, -0.003), (0.025, -0.003), (0.025, 0.003), (-0.025, 0.003)]
        M.add(sweep(path, sec, 'orangew', up=(1, 0, 0), closed=True, caps=False, sm=2))
        M.add(cbox((x - 0.04, -0.79, 0.0), (x + 0.04, -0.755, 0.11), 0.008, 'iron'))
    # lifting gear (behind the kid)
    yb = 0.72; zs = 2.95
    for sx in (-1, 1):
        x = sx * (hw - 0.15)
        M.add(cbox((x - 0.015, yb - 0.06, ztop - 0.01), (x + 0.015, yb + 0.06, ztop + 0.09), 0.006, 'iron'))
        M.add(tube([(x - 0.03, yb, ztop + 0.06), (x - 0.03, yb, ztop + 0.12), (x, yb, ztop + 0.15), (x + 0.03, yb, ztop + 0.12), (x + 0.03, yb, ztop + 0.06)], 0.009, 'metal', sides=5))
        M.add(chain_links((x, yb, ztop + 0.15), (x, yb, zs - 0.12), 0.045))
        M.add(tube([(x - 0.025, yb, zs - 0.07), (x - 0.025, yb, zs - 0.12), (x, yb, zs - 0.15), (x + 0.025, yb, zs - 0.12), (x + 0.025, yb, zs - 0.07)], 0.008, 'metal', sides=5))
    M.add(cbox((-hw + 0.1, yb - 0.07, zs - 0.07), (hw - 0.1, yb + 0.07, zs + 0.07), 0.015, 'p2'))
    for sx in (-1, 1):
        for z0_, z1_ in ((zs - 0.12, zs - 0.07), (zs + 0.07, zs + 0.13)):
            M.add(cbox((sx * (hw - 0.15) - 0.012, yb - 0.04, z0_), (sx * (hw - 0.15) + 0.012, yb + 0.04, z1_), 0.004, 'p2'))
    # master ring in the hook's throat, and two wire-rope slings down to the spreader
    zr = 3.86 + HOOK_THROAT
    ring = []
    rzc = zr + 0.011 - 0.055
    for i in range(14):
        a = 2 * PI * i / 14
        ring.append((0.0, yb + 0.045 * math.sin(a), rzc + 0.055 * math.cos(a)))
    M.add(tube(ring, 0.011, 'metal', sides=6, closed=True, caps=False))
    for sx in (-1, 1):
        x = sx * (hw - 0.15)
        M.add(tube([(x, yb, zs + 0.12), (0.0, yb + sx * 0.012, rzc - 0.05)], 0.014, 'tex', sides=6, uvtile=('rope', None)))
        M.add(xform(cyl(0.022, -0.03, 0.03, 6, 'metal'), T(x, yb, zs + 0.12) @ along((0, 0, 0), (-x, 0, zr - zs - 0.2)).to_3x3().to_4x4()))
    M.attach.append(('Hook', (0.0, yb, 3.86)))
    _front(M)
    M.extra = {'width': LOAD_W, 'depth': 1.5, 'top': ztop, 'bottom': -0.175, 'hookLocal': [0.0, yb, 3.86],
               'note': 'origin = collider centre; scale X by width / 2.6 for other platform widths'}
    return M


# ---------------------------------------------------------------- Hoist
def hoist_mast():
    """One 3 m section of the hoist's lattice mast, tileable in Z (stack sections every 3 m).
    Origin = the game's mast position (posts at y = 0); the rack runs up its front at y = -0.1."""
    M = Model('HoistMast', p1=SITE_YELLOW, ppm=110, grime=dict(rust=0.3, streaks=0.4, ground=0.2, dirt_h=0.3))
    H = 3.0; hx = 0.25; yf, yk = 0.0, 0.45
    for x in (-hx, hx):
        for y in (yf, yk):
            M.add(tube([(x, y, 0.0), (x, y, H)], 0.032, 'p1', sides=6, caps=False))
    lv = [0.0, 0.75, 1.5, 2.25]
    for z in lv:
        M.add(bar((-hx, yk, z + 0.03), (hx, yk, z + 0.03), 0.035, 'p1'))
        M.add(bar((-hx, yf, z + 0.03), (hx, yf, z + 0.03), 0.035, 'p1'))
        for x in (-hx, hx):
            M.add(bar((x, yf, z + 0.03), (x, yk, z + 0.03), 0.035, 'p1'))
    for k, z in enumerate(lv):
        z1 = z + 0.75
        s = 1 if k % 2 == 0 else -1
        M.add(bar((-hx * s, yk, z + 0.05), (hx * s, yk, z1 - 0.02), 0.028, 'p1d', sides=4))
        for x in (-hx, hx):
            M.add(bar((x, yf if s > 0 else yk, z + 0.05), (x, yk if s > 0 else yf, z1 - 0.02), 0.028, 'p1d', sides=4))
        M.add(bar((-hx * s, yf, z + 0.05), (-hx * s * 0.2, yf, z1 - 0.02), 0.028, 'p1d', sides=4))
        M.add(cbox((-0.05, -0.065, z + 0.0), (0.05, yf - 0.02, z + 0.06), 0.008, 'iron'))
    rk = box((-0.05, -0.125, 0.0), (0.05, -0.065, H), 'ironw', skip=('-z', '+z'))
    settile(rk, 'rack', lambda co, f: ((co.x + 0.05) / 0.1, co.z / H), faces=faces_facing(rk, (0, -1, 0), 0.9), mat='tex')
    M.add(rk)
    _front(M)
    M.extra = {'tile': H, 'rackFront': -0.125, 'posts': [[-hx, yf], [hx, yf], [-hx, yk], [hx, yk]]}
    return M


def hoist_mast_cap():
    """The head of the hoist mast: the posts' last stretch, a top frame with a buffer stop for
    the cage, and an amber beacon. Origin at its base, to sit on top of the last HoistMast section."""
    M = Model('HoistMastCap', p1=SITE_YELLOW, ppm=140, ground=False, grime=dict(ground=0.0, rust=0.3, streaks=0.5))
    hx = 0.25; yf, yk = 0.0, 0.45
    for x in (-hx, hx):
        for y in (yf, yk):
            M.add(tube([(x, y, 0.0), (x, y, 0.36)], 0.032, 'p1', sides=6, caps=False))
    for z in (0.03, 0.36):
        M.add(bar((-hx, yf, z), (hx, yf, z), 0.04, 'p1'))
        M.add(bar((-hx, yk, z), (hx, yk, z), 0.04, 'p1'))
        for x in (-hx, hx):
            M.add(bar((x, yf, z), (x, yk, z), 0.04, 'p1'))
    M.add(cbox((-0.3, -0.05, 0.38), (0.3, 0.5, 0.42), 0.012, 'p1d'))
    for x in (-hx, hx):
        M.add(bar((x, yf, 0.06), (-x * 0.2, yf, 0.33), 0.028, 'p1d', sides=4))
    M.add(cbox((-0.09, -0.2, 0.26), (0.09, -0.06, 0.36), 0.015, 'p1d'))
    M.add(cbox((-0.07, -0.21, 0.18), (0.07, -0.12, 0.26), 0.02, 'rubber'))
    M.add(xform(cyl(0.06, 0, 0.03, 12, 'iron', bevel=0.008), T(0.0, 0.22, 0.42)))
    M.add(xform(cyl(0.05, 0, 0.08, 12, 'amber', bevel=0.02), T(0.0, 0.22, 0.45)))
    rk = box((-0.05, -0.125, 0.0), (0.05, -0.065, 0.2), 'ironw', skip=('-z',))
    settile(rk, 'rack', lambda co, f: ((co.x + 0.05) / 0.1, co.z / 3.0), faces=faces_facing(rk, (0, -1, 0), 0.9), mat='tex')
    M.add(rk)
    M.attach.append(('Beacon', (0.0, 0.22, 0.52)))
    _front(M)
    return M


def hoist_cage():
    """The hoist's caged deck. Origin = the deck centre (the moving platform's collider centre):
    walkable top at z = +0.175, frame bottom at -0.175, 2.6 m wide (X) and 1.5 m deep (Y). The
    open front faces the street; the cage is at the back, the drive unit behind it climbs the
    mast's rack (mast front posts at y = 1.45, rack face at y = 1.325)."""
    M = Model('HoistCage', p1=SITE_YELLOW, ppm=100, ground=False, grime=dict(ground=0.0, rust=0.3, streaks=0.6, chips=0.35))
    hw = 1.3; hd = 0.75
    M.add(cbox((-hw, -hd, -0.175), (hw, hd, 0.16), 0.025, 'p1'))
    pl = box((-hw + 0.03, -hd + 0.03, 0.16), (hw - 0.03, hd - 0.03, 0.175), 'metal', skip=('-z',))
    settile(pl, 'chequer', lambda co, f: ((co.x + hw) / (2 * hw), (co.y + hd) / (2 * hd)), faces=faces_facing(pl, (0, 0, 1), 0.9), mat='tex')
    M.add(pl)
    fz = box((-hw + 0.04, -hd - 0.008, -0.15), (hw - 0.04, -hd, 0.135), 'iron', skip=('+y',))
    settile(fz, 'hazard', lambda co, f: ((co.x + hw) / (2 * hw), (co.z + 0.15) / 0.285), faces=faces_facing(fz, (0, -1, 0), 0.9), mat='tex')
    M.add(fz)
    M.add(cbox((-hw, -hd, 0.175), (hw, -hd + 0.03, 0.225), 0.008, 'p1'))
    # cage at the back: posts, rails and a welded mesh
    yc = hd - 0.03
    for x in (-hw + 0.03, 0.0, hw - 0.03):
        M.add(tube([(x, yc, 0.175), (x, yc, 1.25)], 0.03, 'p1', sides=8))
    M.add(tube([(-hw + 0.03, yc, 1.22), (hw - 0.03, yc, 1.22)], 0.03, 'p1', sides=8))
    M.add(tube([(-hw + 0.03, yc, 0.70), (hw - 0.03, yc, 0.70)], 0.024, 'p1', sides=8))
    ym = yc + 0.03
    xs = np.arange(-hw + 0.13, hw - 0.1, 0.1)
    for x in xs:
        M.add(bar((x, ym, 0.2), (x, ym, 1.2), 0.012, 'galv', sides=3, caps=False))
    for z in (0.3, 0.5, 0.9, 1.1):
        M.add(bar((-hw + 0.05, ym, z), (hw - 0.05, ym, z), 0.012, 'galv', sides=3, caps=False))
    # control box on the right post
    M.add(cbox((0.92, yc - 0.12, 0.82), (1.16, yc - 0.03, 1.12), 0.012, 'creamw'))
    cb = box((0.95, yc - 0.125, 0.85), (1.13, yc - 0.12, 1.09), 'creamw', skip=('+y',))
    settile(cb, 'ctrl', lambda co, f: ((co.x - 0.95) / 0.18, (co.z - 0.85) / 0.24), faces=faces_facing(cb, (0, -1, 0), 0.9), mat='tex')
    M.add(cb)
    # drive unit behind, climbing the mast
    M.add(cbox((-0.36, hd - 0.05, -0.12), (0.36, 0.92, 0.22), 0.02, 'p1'))
    M.add(rbox((-0.35, 0.83, 0.2), (0.35, 1.28, 0.9), (0.06, 0.06, 0.06), 'p1d', seg=(1, 1, 1)))
    M.feat('side', 'lines', lines=[[(0.88, 0.32), (1.22, 0.32)], [(0.88, 0.78), (1.22, 0.78)]], w=0.006, col=(0.55, 0.55, 0.55))
    M.add(xform(cyl(0.13, -0.2, 0.2, 14, 'iron', bevel=0.02), T(0, 1.05, 1.02) @ R(PI / 2, 'Y')))
    for sx in (-1, 1):
        M.add(xform(cyl(0.135, 0, 0.02, 14, 'p1d', bevel=0.005), T(sx * 0.2, 1.05, 1.02) @ R(sx * PI / 2, 'Y')))
    M.add(cbox((-0.12, 1.27, 0.3), (0.12, 1.31, 0.62), 0.01, 'iron'))
    for z in (0.28, 0.82):
        for sx in (-1, 1):
            M.add(cbox((sx * 0.31 - 0.025, 1.24, z - 0.03), (sx * 0.31 + 0.025, 1.43, z + 0.03), 0.008, 'iron'))
            M.add(xform(cyl(0.035, -0.022, 0.022, 10, 'metal'), T(sx * 0.31, 1.395, z) @ R(PI / 2, 'Z')))
    M.add(xform(cyl(0.06, 0, 0.03, 12, 'iron'), T(0.22, 0.95, 0.9)))
    M.add(xform(cyl(0.048, 0, 0.08, 12, 'amber', bevel=0.02), T(0.22, 0.95, 0.93)))
    M.attach.append(('Beacon', (0.22, 0.95, 1.0)))
    _front(M)
    M.extra = {'width': 2 * hw, 'depth': 2 * hd, 'top': 0.175, 'bottom': -0.175, 'mastY': 1.45,
               'note': 'origin = collider centre; scale X by width / 2.6 for other platform widths'}
    return M


# ---------------------------------------------------------------- ConcretePipe (rolling hazard)
def concrete_pipe():
    """The rolling pipe hazard's visual: radius 0.45 m, 1.5 m long along Y (game z), hollow (inner
    radius 0.324). Origin = the pipe's centre (the CircleCollider2D's centre), so it rolls about
    its own axis. A yellow spray-paint stripe on top shows it turning."""
    M = Model('ConcretePipe', p1=CONCRETE, ppm=110, ground=False, grime=dict(ground=0.0, rust=0.0, chips=0.0, streaks=0.0, mottle=0.12))
    p = pipe_bm(0.45, 0.324, 1.5, 28, 'p1', bevel=0.03)
    xform(p, R(-PI / 2, 'X'))
    M.add(p)
    st, _ = lathe([(0.4525, -0.15), (0.4525, 0.0), (0.4525, 0.15)], 3, 'yelloww', arc=(-PI / 2 - 0.14, -PI / 2 + 0.14))
    xform(st, T(0, -0.4, 0) @ R(-PI / 2, 'X'))
    M.add(st)
    sp, _ = lathe([(0.4525, -0.04), (0.4525, 0.04)], 2, 'yelloww', arc=(-0.35, -0.12))
    xform(sp, T(0, 0.35, 0) @ R(-PI / 2, 'X'))
    M.add(sp)
    for mp in ('front', 'side', 'top'):
        M.feat(mp, 'spatter', a0=-1, a1=1, b0=-1, b1=1, n=400, r=(0.004, 0.012), col=(0.80, 0.78, 0.74), alpha=0.5)
    _front(M)
    M.extra = {'radius': 0.45, 'innerRadius': 0.324, 'length': 1.5, 'axis': 'Y (game z)', 'origin': 'pipe centre'}
    return M


# ---------------------------------------------------------------- Scaffold
def scaffold():
    """One 2 m bay of tube-and-fitting scaffold, two lifts (decks at 2.1 m and 4.1 m), boards and
    toe boards, guard rails on the front; tileable along X (the end standards of neighbouring
    bays coincide)."""
    M = Model('Scaffold', p1=(0.72, 0.74, 0.75), p2=SITE_YELLOW, ppm=45, grime=dict(rust=0.25, streaks=0.5, dirt_h=0.4))
    hx = 1.0; ys = (-0.5, 0.5); ztop = 5.15
    r = 0.03
    for x in (-hx, hx):
        M.add(wood_box((x - 0.11, -0.66, 0.0), (x + 0.11, 0.66, 0.045), band=3, along=1))
        for y in ys:
            M.add(cbox((x - 0.07, y - 0.07, 0.045), (x + 0.07, y + 0.07, 0.06), 0.004, 'iron'))
            M.add(tube([(x, y, 0.06), (x, y, ztop)], r, 'p1', sides=6))
    yl = {-0.5: -0.56, 0.5: 0.56}
    for z in (0.3, 2.05, 4.05):
        for y in ys:
            M.add(tube([(-hx, yl[y], z), (hx, yl[y], z)], 0.028, 'p1', sides=6))
            for x in (-hx, hx):
                M.add(cbox((x - 0.045, y - 0.045 + (yl[y] - y) * 0.5, z - 0.04), (x + 0.045, y + 0.045 + (yl[y] - y) * 0.5, z + 0.04), 0.008, 'iron'))
    for z in (2.11, 4.11):
        for x in (-hx + 0.04, 0.0, hx - 0.04):
            M.add(tube([(x, -0.62, z), (x, 0.62, z)], 0.026, 'p1', sides=6))
        for k in range(4):
            y0 = -0.47 + k * 0.232
            dz = 0.004 * ((k * 7) % 3)
            M.add(wood_box((-hx + 0.005 * (k % 2), y0, z + 0.026 + dz), (hx - 0.005 * ((k + 1) % 2), y0 + 0.225, z + 0.066 + dz), band=k, r=0.006))
        M.add(cbox((-hx, -0.545, z + 0.03), (hx, -0.505, z + 0.2), 0.008, 'p2'))
    for z in (2.6, 3.05, 4.6, 5.05):
        M.add(tube([(-hx, -0.62, z), (hx, -0.62, z)], 0.026, 'p1', sides=6))
        for x in (-hx, hx):
            M.add(cbox((x - 0.04, -0.66, z - 0.035), (x + 0.04, -0.54, z + 0.035), 0.008, 'iron'))
    M.add(tube([(-hx + 0.06, -0.66, 0.35), (hx - 0.06, -0.66, 3.95)], 0.026, 'p1', sides=6))
    for (x, z) in ((-hx + 0.06, 0.35), (hx - 0.06, 3.95)):
        M.add(cbox((x - 0.04, -0.7, z - 0.04), (x + 0.04, -0.6, z + 0.04), 0.008, 'iron'))
    _front(M)
    M.extra = {'bay': 2.0, 'decks': [2.11, 4.11], 'tileAxis': 'X'}
    return M


# ---------------------------------------------------------------- SiteFence
def site_fence():
    """A 3.5 m temporary mesh fence panel on block feet, tileable along X (the feet at x = +-1.75
    each hold two panels' legs; neighbouring panels' feet coincide)."""
    M = Model('SiteFence', p1=(0.72, 0.74, 0.75), p2=SAFETY_ORANGE, ppm=60, grime=dict(rust=0.2, streaks=0.3, dirt_h=0.3))
    hx = 1.75; xi = 1.70; z0, z1 = 0.16, 1.98; rc = 0.07
    for x in (-hx, hx):
        M.add(rbox((x - 0.1, -0.34, 0.0), (x + 0.1, 0.34, 0.14), (0.03, 0.05, 0.03), 'p2', seg=(1, 1, 1)))
        for dx in (-0.05, 0.05):
            M.add(xform(cyl(0.03, 0, 0.012, 8, 'dark'), T(x + dx, 0, 0.14)))
    loop = []
    for (cx, cz, a0) in ((xi - rc, z1 - rc, 0.0), (-xi + rc, z1 - rc, PI / 2), (-xi + rc, z0 + rc, PI), (xi - rc, z0 + rc, 1.5 * PI)):
        for i in range(4):
            a = a0 + (PI / 2) * i / 3
            loop.append((cx + rc * math.cos(a), 0, cz + rc * math.sin(a)))
    M.add(tube(loop, 0.021, 'p1', sides=8, closed=True, caps=False))
    for x in (-xi, xi):
        M.add(tube([(x, 0, 0.06), (x, 0, z0 + rc)], 0.021, 'p1', sides=8))
    for x in np.arange(-xi + 0.15, xi - 0.1, 0.15):
        M.add(bar((x, 0.0, z0 + 0.02), (x, 0.0, z1 - 0.02), 0.012, 'p1d', sides=3, caps=False))
    for z in np.arange(z0 + 0.3, z1 - 0.1, 0.3):
        M.add(bar((-xi + 0.02, 0.006, z), (xi - 0.02, 0.006, z), 0.012, 'p1d', sides=3, caps=False))
    for x in (-hx, hx):
        for z in (0.9, 1.75):
            M.add(cbox((x - 0.085, -0.035, z - 0.04), (x + 0.085, 0.035, z + 0.04), 0.01, 'iron'))
    _front(M)
    M.extra = {'panel': 3.5, 'height': 2.0, 'tileAxis': 'X'}
    return M


# ---------------------------------------------------------------- PortaLoo
def portaloo():
    """A portable site toilet: moulded plastic body, ribbed walls, a door on the front with a
    vacant / engaged slider, a pale roof and a vent pipe."""
    M = Model('PortaLoo', p1=(0.34, 0.58, 0.64), p2=(0.93, 0.90, 0.82), ppm=70, grime=dict(rust=0.0, chips=0.15, streaks=0.6, dirt_h=0.5, ground=0.6))
    M.add(rbox((-0.6, -0.62, 0.0), (0.6, 0.62, 0.12), (0.04, 0.04, 0.03), 'p1d', seg=(1, 1, 1)))
    M.add(rbox((-0.56, -0.58, 0.1), (0.56, 0.58, 2.16), (0.07, 0.07, 0.02), 'p1', seg=(1, 1, 1), skip=((2, 1), (2, -1))))
    for sx in (-1, 1):
        for y in (-0.3, 0.0, 0.3):
            M.add(cbox((sx * 0.56 - 0.02, y - 0.04, 0.25), (sx * 0.56 + 0.02, y + 0.04, 1.75), 0.012, 'p1'))
        v = box((sx * 0.565 - 0.005, -0.25, 1.82), (sx * 0.565 + 0.005, 0.25, 2.02), 'p1k')
        settile(v, 'vent', lambda co, f: ((co.y + 0.25) / 0.5, (co.z - 1.82) / 0.2), mat='p1dk')
        M.add(v)
    for x in (-0.25, 0.25):
        M.add(cbox((x - 0.04, 0.56, 0.25), (x + 0.04, 0.6, 1.9), 0.012, 'p1'))
    # door
    M.add(rbox((-0.44, -0.62, 0.18), (0.44, -0.57, 2.02), (0.04, 0.02, 0.04), 'p1', seg=(1, 1, 1)))
    for x in (-0.18, 0.18):
        M.add(cbox((x - 0.035, -0.645, 0.35), (x + 0.035, -0.61, 1.7), 0.012, 'p1'))
    M.add(cbox((-0.42, -0.64, 0.25), (-0.36, -0.61, 1.95), 0.01, 'p1d'))
    M.add(cbox((0.30, -0.66, 1.0), (0.34, -0.62, 1.16), 0.01, 'dark'))
    M.add(cbox((0.26, -0.68, 1.06), (0.40, -0.645, 1.10), 0.012, 'dark'))
    M.add(cbox((0.27, -0.635, 1.22), (0.39, -0.62, 1.28), 0.006, 'iron'))
    M.add(cbox((0.29, -0.64, 1.23), (0.33, -0.632, 1.27), 0.003, 'green'))
    # roof: a pale dome
    def dome(X):
        X = X.copy()
        k = np.clip(1 - (X[:, 0] / 0.62) ** 2 - (X[:, 1] / 0.64) ** 2, 0, 1)
        X[:, 2] += np.where(X[:, 2] > 2.2, 0.07 * k, 0)
        return X
    M.add(rbox((-0.62, -0.64, 2.12), (0.62, 0.64, 2.26), (0.07, 0.07, 0.05), 'p2', seg=(1, 1, 1), extra=((0.0,), (0.0,), ()), deform=dome, skip=((2, -1),)))
    M.add(tube([(0.3, 0.6, 1.6), (0.3, 0.64, 1.7), (0.3, 0.64, 2.5)], 0.045, 'p1d', sides=8))
    M.add(xform(cyl(0.07, 0, 0.06, 10, 'p1d', bevel=0.015), T(0.3, 0.64, 2.5)))
    M.feat('front', 'lines', lines=[[(-0.44, 0.18), (-0.44, 2.02), (0.44, 2.02), (0.44, 0.18)]], w=0.008, col=(0.5, 0.5, 0.5))
    _front(M)
    return M


# ---------------------------------------------------------------- Skip
def skip():
    """A builder's skip with sloping ends, ribbed sides, lifting lugs and a load of rubble."""
    M = Model('Skip', p1=(0.36, 0.50, 0.62), ppm=60, grime=dict(rust=0.55, chips=0.6, streaks=0.8, dirt_h=0.5, ground=0.7))
    zb, zt = 0.14, 1.2
    t = tray((1.2, 0.80, 0.06), (1.72, 0.88, 0.08), zb, zt, 0.05, 'p1', inner_mat='p1d', nc=2, fill=0.92)
    top = [f for f in t.faces if f.normal.z > 0.9 and f.calc_center_median().z > 0.8]
    settile(t, 'rubble', lambda co, f: ((co.x + 1.7) / 3.4, (co.y + 0.86) / 1.72), faces=top, mat='tex')
    M.add(t)
    rim = [(x, y, zt + 0.01) for x, y in rrect(1.72, 0.88, 0.08, 2)]
    M.add(tube(rim, 0.04, 'p1', sides=6, closed=True, caps=False))
    for sy in (-1, 1):
        for x in (-0.9, -0.3, 0.3, 0.9):
            y_b = sy * 0.80; y_t = sy * 0.88
            M.add(bar((x, y_b + sy * 0.02, zb + 0.02), (x, y_t + sy * 0.02, zt - 0.02), 0.07, 'p1', sides=4))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Vector((sx * 1.55, sy * 0.92, 1.0))
            M.add(xform(cyl(0.07, 0, 0.1, 10, 'p1d', bevel=0.02), T(p) @ R(-sy * PI / 2, 'X')))
            M.add(xform(cyl(0.1, 0, 0.025, 10, 'p1d', bevel=0.008), T(p + Vector((0, sy * 0.1, 0))) @ R(-sy * PI / 2, 'X')))
        M.add(cbox((sx * 1.18 - 0.06, -0.15, 0.25), (sx * 1.18 + 0.06, 0.15, 0.5), 0.02, 'p1d'))
    for y in (-0.55, 0.55):
        M.add(cbox((-1.25, y - 0.07, 0.0), (1.25, y + 0.07, zb + 0.02), 0.02, 'iron'))
    # rubble sticking up out of the load
    M.add(blob((-0.6, 0.1, 0.92), (0.55, 0.45, 0.22), 'concd', n=8, rings=2, seed=3, jitter=0.25, flat_bottom=0.0))
    M.add(blob((0.5, -0.2, 0.92), (0.45, 0.35, 0.16), 'terra', n=7, rings=2, seed=5, jitter=0.3, flat_bottom=0.0))
    b = wood_box((-0.6, -0.06, 0.0), (0.6, 0.06, 0.03), band=1)
    xform(b, T(0.2, 0.3, 1.18) @ R(0.35, 'Y') @ R(0.3, 'Z')); M.add(b)
    b = wood_box((-0.5, -0.05, 0.0), (0.5, 0.05, 0.025), band=3)
    xform(b, T(-0.7, -0.35, 1.08) @ R(-0.18, 'Y') @ R(-0.5, 'Z')); M.add(b)
    for i, (x, y) in enumerate(((0.95, 0.4), (1.1, 0.25), (-1.05, -0.4))):
        M.add(xform(cbox((-0.11, -0.05, 0), (0.11, 0.05, 0.065), 0.01, 'terra'), T(x, y, 0.96 + 0.03 * i) @ R(0.4 * i, 'Z') @ R(0.2, 'X')))
    _front(M)
    return M


# ---------------------------------------------------------------- CementMixer
def cement_mixer():
    """A small site concrete mixer: a tilted drum in a yoke on a two-wheeled stand, a motor
    housing, a tilting handwheel and a tow bar."""
    M = Model('CementMixer', p1=SAFETY_ORANGE, p2=STEEL_BLUE, ppm=120, grime=dict(rust=0.25, chips=0.3, streaks=0.5, dirt_h=0.3))
    # stand
    for sy in (-1, 1):
        M.add(tube([(-0.38, sy * 0.30, 0.2), (-0.1, sy * 0.30, 0.6), (0.05, sy * 0.30, 0.78)], 0.03, 'p2', sides=6))
        M.add(tube([(0.55, sy * 0.06, 0.03), (0.35, sy * 0.2, 0.4), (0.05, sy * 0.3, 0.55)], 0.026, 'p2', sides=6))
    M.add(tube([(-0.38, -0.40, 0.2), (-0.38, 0.40, 0.2)], 0.022, 'metal', sides=6))
    for sy in (-1, 1):
        w = wheel_bm(0.2, 0.09, n=10, hub='p2', tyre='rubber')
        xform(w, T(-0.38, sy * 0.40, 0.2) @ R(PI / 2, 'X')); M.add(w)
    M.add(cbox((0.5, -0.1, 0.0), (0.62, 0.1, 0.035), 0.01, 'iron'))
    M.add(tube([(0.05, 0.0, 0.52), (0.6, 0.0, 0.5), (0.85, 0.0, 0.46)], 0.025, 'p2', sides=6))
    ring = [(0.92 + 0.06 * math.cos(2 * PI * i / 10), 0.06 * math.sin(2 * PI * i / 10), 0.46) for i in range(10)]
    M.add(tube(ring, 0.014, 'p2', sides=5, closed=True, caps=False))
    # motor housing
    M.add(rbox((-0.42, -0.2, 0.36), (0.0, 0.2, 0.66), (0.05, 0.05, 0.05), 'p2', seg=(1, 1, 1)))
    v = box((-0.36, -0.205, 0.42), (-0.08, -0.2, 0.6), 'p2', skip=('+y',))
    settile(v, 'vent', lambda co, f: ((co.x + 0.36) / 0.28, (co.z - 0.42) / 0.18), mat='p2k', faces=faces_facing(v, (0, -1, 0), 0.9))
    M.add(v)
    # yoke and drum
    piv = Vector((0.05, 0.0, 0.8))
    for sy in (-1, 1):
        M.add(cbox((piv.x - 0.05, sy * 0.3 - 0.025, piv.z - 0.32), (piv.x + 0.05, sy * 0.3 + 0.025, piv.z + 0.04), 0.012, 'p2'))
    M.add(cbox((piv.x - 0.05, -0.3, piv.z - 0.34), (piv.x + 0.05, 0.3, piv.z - 0.28), 0.012, 'p2'))
    tilt = R(0.55, 'Y')
    prof = [(0.0, -0.10), (0.20, -0.08), (0.33, 0.04), (0.37, 0.16), (0.37, 0.26), (0.30, 0.42), (0.21, 0.55), (0.19, 0.6), (0.165, 0.6), (0.17, 0.52), (0.0, 0.36)]
    mats = ['p1', 'p1', 'p1', 'p1', 'p1', 'p1', 'p1d', 'p1d', 'iron', 'dark']
    drum, _ = lathe(prof, 14, mats, phase=0.0, sm=0)
    xform(drum, T(piv + Vector((0, 0, -0.1))) @ tilt)
    M.add(drum)
    gring, _ = lathe([(0.36, 0.1), (0.40, 0.11), (0.40, 0.15), (0.36, 0.16)], 14, 'iron', phase=0.0)
    xform(gring, T(piv + Vector((0, 0, -0.1))) @ tilt); M.add(gring)
    for k in range(4):
        a = 2 * PI * k / 4 + 0.4
        rb = box((-0.012, -0.01, 0.0), (0.012, 0.01, 0.3), 'p1d')
        xform(rb, T(piv + Vector((0, 0, -0.1))) @ tilt @ R(a, 'Z') @ T(0.34, 0, 0.1) @ R(-0.25, 'Y'))
        M.add(rb)
    M.add(xform(cyl(0.035, -0.36, 0.36, 10, 'iron'), T(piv) @ R(PI / 2, 'X')))
    # tilting handwheel
    hwc = Vector((piv.x, 0.42, piv.z))
    rim = [(hwc.x + 0.15 * math.cos(2 * PI * i / 14), hwc.y, hwc.z + 0.15 * math.sin(2 * PI * i / 14)) for i in range(14)]
    M.add(tube(rim, 0.014, 'red', sides=4, closed=True, caps=False))
    for k in range(3):
        a = 2 * PI * k / 3
        M.add(bar(hwc, (hwc.x + 0.15 * math.cos(a), hwc.y, hwc.z + 0.15 * math.sin(a)), 0.016, 'red', sides=4))
    M.add(xform(cyl(0.03, 0, 0.06, 8, 'iron'), T(hwc) @ R(-PI / 2, 'X')))
    # concrete splashes on the drum and the stand
    M.feat('front', 'spatter', a0=-0.4, a1=0.6, b0=0.4, b1=1.4, n=500, r=(0.004, 0.018), col=(0.72, 0.70, 0.66), alpha=0.75)
    M.feat('side', 'spatter', a0=-0.5, a1=0.5, b0=0.4, b1=1.4, n=300, r=(0.004, 0.018), col=(0.72, 0.70, 0.66), alpha=0.75)
    M.feat('top', 'spatter', a0=-0.5, a1=0.7, b0=-0.5, b1=0.5, n=300, r=(0.004, 0.02), col=(0.72, 0.70, 0.66), alpha=0.7)
    _front(M)
    return M


# ---------------------------------------------------------------- Wheelbarrow
def wheelbarrow():
    """A builder's wheelbarrow, wheel to +X, with a little sand and a shovel in its pan."""
    M = Model('Wheelbarrow', p1=(0.38, 0.58, 0.42), ppm=140, grime=dict(rust=0.35, chips=0.5, streaks=0.4, dirt_h=0.25))
    zb, zt = 0.36, 0.66

    def ring(hx, hy, r, z, cx, off=0.0):
        return [(cx + x, y, z) for x, y in rrect(hx - off, hy - off, max(r - off, 0.02), 3)]
    tth = 0.012
    rings = [ring(0.27, 0.19, 0.08, zb, -0.02), ring(0.48, 0.32, 0.12, zt, 0.08), ring(0.48, 0.32, 0.12, zt, 0.08, tth), ring(0.36, 0.25, 0.1, 0.52, 0.03, tth)]
    t = loft(rings, ['p1', 'p1', 'p1d'], closed_bottom=True, closed_top=True)
    fix_normals(t)
    M.add(t)
    M.add(tube([(x, y, zt + 0.005) for x, y, _ in ring(0.48, 0.32, 0.12, zt, 0.08)], 0.014, 'p1', sides=6, closed=True, caps=False))
    M.add(blob((0.03, 0.0, 0.52), (0.33, 0.23, 0.1), 'sand', n=9, rings=2, seed=8, jitter=0.12, flat_bottom=0.0))
    # frame and handles
    for sy in (-1, 1):
        M.add(tube([(0.62, sy * 0.06, 0.2), (0.42, sy * 0.15, 0.31), (-0.3, sy * 0.24, 0.36), (-0.7, sy * 0.28, 0.52), (-0.98, sy * 0.30, 0.6)], 0.021, 'iron', sides=6))
        M.add(tube([(-0.84, sy * 0.292, 0.565), (-1.0, sy * 0.30, 0.605)], 0.027, 'rubber', sides=6))
        M.add(tube([(-0.22, sy * 0.235, 0.36), (-0.26, sy * 0.26, 0.03)], 0.018, 'iron', sides=6))
        M.add(cbox((-0.32, sy * 0.26 - 0.03, 0.0), (-0.2, sy * 0.26 + 0.03, 0.03), 0.008, 'iron'))
    M.add(tube([(-0.24, -0.25, 0.14), (-0.24, 0.25, 0.14)], 0.014, 'iron', sides=6))
    w = wheel_bm(0.2, 0.085, n=16, hub='redg', tyre='rubber', rim_r=0.55)
    xform(w, T(0.62, 0, 0.2) @ R(PI / 2, 'X')); M.add(w)
    M.add(tube([(0.62, -0.08, 0.2), (0.62, 0.08, 0.2)], 0.012, 'metal', sides=6))
    # a shovel resting in the pan
    a = Vector((-0.2, 0.08, 0.53)); b = Vector((-0.95, -0.1, 1.08))
    M.add(tube([a, b], 0.017, 'timberw', sides=6))
    M.add(tube([b, b + (b - a).normalized() * 0.06, b + (b - a).normalized() * 0.1 + Vector((0, 0.06, 0)), b + (b - a).normalized() * 0.1 - Vector((0, 0.06, 0))], 0.012, 'iron', sides=5))
    bl = cbox((-0.11, -0.13, -0.005), (0.11, 0.13, 0.005), 0.01, 'metal', seg=2)
    xform(bl, T(a + (a - b).normalized() * 0.13) @ R(0.55, 'Y') @ R(0.24, 'Z')); M.add(bl)
    _front(M)
    return M


# ---------------------------------------------------------------- PipeStack
def pipe_stack():
    """Three big concrete pipes stacked on timber bearers with wedges (backdrop)."""
    M = Model('PipeStack', p1=CONCRETE, ppm=60, grime=dict(rust=0.0, chips=0.0, streaks=0.6, mottle=0.12, dirt_h=0.4))
    ro, ri, Ln = 0.5, 0.39, 1.6
    for y in (-0.55, 0.55):
        M.add(wood_box((-1.25, y - 0.08, 0.0), (1.25, y + 0.08, 0.1), band=2, along=0))
    for (x, z) in ((-0.52, 0.1 + ro), (0.52, 0.1 + ro), (0.0, 0.1 + ro + 0.9)):
        p = pipe_bm(ro, ri, Ln, 22, 'p1', bevel=0.035)
        xform(p, T(x, 0, z) @ R(-PI / 2, 'X'))
        M.add(p)
    for sx in (-1, 1):
        for y in (-0.55, 0.55):
            wd = extrude_poly([(0, 0), (0.22, 0), (0, 0.16)], 0.14, 'timberw')
            xform(wd, T(sx * 1.04, y + 0.07, 0.1) @ R(PI / 2, 'X') @ (Matrix.Identity(4) if sx > 0 else S(-1, 1, 1)))
            M.add(fix_normals(wd))
    M.feat('front', 'stain', a=0.0, b=0.4, ra=0.9, rb=0.3, col=(0.74, 0.70, 0.62), alpha=0.5)
    _front(M)
    return M


# ---------------------------------------------------------------- SteelBeams
def steel_beams():
    """A pile of primed steel I-beams on timber bearers, ends spray-marked (backdrop)."""
    M = Model('SteelBeams', p1=OXIDE, ppm=70, grime=dict(rust=0.6, chips=0.4, streaks=0.6, dirt_h=0.3))
    Lh = 2.0
    for x in (-1.3, 1.3):
        M.add(wood_box((x - 0.08, -0.62, 0.0), (x + 0.08, 0.62, 0.12), band=1, along=1))
    for k in range(4):
        M.add(section_beam(-Lh + 0.03 * k, Lh + 0.03 * k, -0.42 + 0.28 * k, 0.12, 0.3, 0.16, 0.022, 0.012, 'p1', end_mat='yellow' if k % 2 == 0 else 'whiteg'))
    for x in (-1.1, 1.1):
        M.add(wood_box((x - 0.06, -0.58, 0.42), (x + 0.06, 0.58, 0.5), band=0, along=1))
    for k in range(3):
        M.add(section_beam(-Lh + 0.15 - 0.06 * k, Lh - 0.1 - 0.06 * k, -0.28 + 0.28 * k, 0.5, 0.3, 0.16, 0.022, 0.012, 'p1', end_mat='yellow', rot=0.015 * (k - 1)))
    _front(M)
    return M


# ---------------------------------------------------------------- SiteCabin
def site_cabin():
    """A portable site office, 6 m long, on block stacks: ribbed steel walls, a door with steps,
    barred windows, a roof cap with a gutter and downpipe, an air-con unit and a lamp."""
    M = Model('SiteCabin', p1=(0.90, 0.85, 0.72), p2=STEEL_BLUE, ppm=40, grime=dict(rust=0.3, chips=0.25, streaks=0.8, dirt_h=0.6, ground=0.6, streak_len=1.6))
    hx, hy = 3.0, 1.25; zb, zt = 0.3, 2.75
    for x in (-2.6, 0.0, 2.6):
        for y in (-0.9, 0.9):
            M.add(cbox((x - 0.2, y - 0.2, 0.0), (x + 0.2, y + 0.2, zb), 0.02, 'concd'))
    M.add(box((-hx + 0.06, -hy + 0.06, zb), (hx - 0.06, hy - 0.06, zt), 'p1', skip=('-z', '+z')))
    for x in (-hx, hx - 0.14):
        for y in (-hy, hy - 0.14):
            M.add(cbox((x, y, zb), (x + 0.14, y + 0.14, zt), 0.015, 'p2'))
    for (z0, z1) in ((zb, zb + 0.14), (zt - 0.14, zt)):
        for y in (-hy, hy - 0.12):
            M.add(cbox((-hx, y, z0), (hx, y + 0.12, z1), 0.015, 'p2'))
        for x in (-hx, hx - 0.12):
            M.add(cbox((x, -hy, z0), (x + 0.12, hy, z1), 0.015, 'p2'))
    M.add(cbox((-hx - 0.05, -hy - 0.05, zt), (hx + 0.05, hy + 0.05, zt + 0.1), 0.02, 'p2'))
    M.add(cbox((-hx + 0.1, -hy + 0.1, zt + 0.1), (hx - 0.1, hy - 0.1, zt + 0.13), 0.01, 'galv'))
    for mp, (a0, a1) in (('front', (-hx + 0.14, hx - 0.14)), ('side', (-hy + 0.14, hy - 0.14))):
        M.feat(mp, 'ribs', a0=a0, a1=a1, b0=zb + 0.14, b1=zt - 0.14, pitch=0.22, depth=0.13)
    # door with a small wired window, kick plate, handle
    dx0, dx1, dz0, dz1 = 1.55, 2.45, zb + 0.06, 2.4
    M.add(cbox((dx0 - 0.06, -hy - 0.03, dz0), (dx1 + 0.06, -hy + 0.02, dz1 + 0.06), 0.012, 'p2'))
    M.add(cbox((dx0, -hy - 0.05, dz0), (dx1, -hy - 0.01, dz1), 0.01, 'p2'))
    g = box((dx0 + 0.25, -hy - 0.055, 1.75), (dx1 - 0.25, -hy - 0.045, 2.2), 'tex')
    tile_box(g, 'glass', Vector((dx0 + 0.25, 0, 1.75)), Vector((dx1 - 0.25, 0, 2.2)), axes=(0, 2)); M.add(g)
    M.add(cbox((dx0 + 0.04, -hy - 0.06, dz0 + 0.04), (dx1 - 0.04, -hy - 0.045, dz0 + 0.3), 0.006, 'metal'))
    M.add(cbox((dx1 - 0.2, -hy - 0.1, 1.28), (dx1 - 0.06, -hy - 0.05, 1.32), 0.012, 'dark'))
    M.add(cbox((dx1 - 0.13, -hy - 0.07, 1.18), (dx1 - 0.08, -hy - 0.05, 1.4), 0.01, 'iron'))
    # steps up to the door
    sx0, sx1 = dx0 - 0.15, dx1 + 0.15
    for k, (y0, z) in enumerate(((-hy - 0.75, 0.12), (-hy - 0.45, 0.22))):
        st = box((sx0, y0, z - 0.03), (sx1, y0 + 0.32, z), 'metal')
        settile(st, 'grate', lambda co, f: ((co.x - sx0) / (sx1 - sx0), (co.y - y0) / 0.32), faces=faces_facing(st, (0, 0, 1), 0.9), mat='tex')
        M.add(st)
    for x in (sx0, sx1 - 0.04):
        sg = extrude_poly([(-hy - 0.8, 0.0), (-hy - 0.05, 0.0), (-hy - 0.05, 0.27), (-hy - 0.4, 0.27)], 0.04, 'galv')
        M.add(fix_normals(xform(sg, T(x, 0, 0) @ basis((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)))))
    M.add(tube([(sx1 - 0.02, -hy - 0.75, 0.12), (sx1 - 0.02, -hy - 0.75, 1.05), (sx1 - 0.02, -hy - 0.12, 1.15), (sx1 - 0.02, -hy - 0.05, 1.15)], 0.022, 'p2', sides=6))
    # windows: frame, glass, bars, sill
    for (wx0, wx1) in ((-2.35, -1.05), (-0.65, 0.65)):
        wz0, wz1 = 1.15, 2.1
        M.add(cbox((wx0 - 0.07, -hy - 0.03, wz0 - 0.07), (wx1 + 0.07, -hy + 0.02, wz1 + 0.07), 0.015, 'p2'))
        g = box((wx0, -hy - 0.035, wz0), (wx1, -hy - 0.025, wz1), 'tex')
        tile_box(g, 'glass', Vector((wx0, 0, wz0)), Vector((wx1, 0, wz1)), axes=(0, 2)); M.add(g)
        M.add(cbox((wx0 + (wx1 - wx0) / 2 - 0.02, -hy - 0.05, wz0), (wx0 + (wx1 - wx0) / 2 + 0.02, -hy - 0.03, wz1), 0.006, 'p2'))
        for k in range(1, 8):
            x = wx0 + (wx1 - wx0) * k / 8
            M.add(bar((x, -hy - 0.08, wz0 - 0.03), (x, -hy - 0.08, wz1 + 0.03), 0.018, 'iron', sides=4, caps=False))
        for z in (wz0 - 0.03, wz1 + 0.03):
            M.add(cbox((wx0 - 0.03, -hy - 0.1, z - 0.02), (wx1 + 0.03, -hy - 0.06, z + 0.02), 0.006, 'iron'))
        M.add(cbox((wx0 - 0.1, -hy - 0.12, wz0 - 0.11), (wx1 + 0.1, -hy + 0.02, wz0 - 0.07), 0.01, 'p2'))
    # air-con unit on the right end wall
    M.add(cbox((hx - 0.02, -0.5, 1.55), (hx + 0.3, 0.3, 2.1), 0.03, 'creamw'))
    fan, _ = lathe([(0.2, 0.0), (0.2, 0.012), (0.17, 0.012), (0.04, 0.005), (0.0, 0.006)], 16, ['creamw', 'creamw', 'dark', 'iron'], phase=0.0)
    xform(fan, T(hx + 0.3, -0.12, 1.82) @ R(PI / 2, 'Y')); M.add(fan)
    for k in range(5):
        z = 1.66 + k * 0.08
        M.add(bar((hx + 0.315, -0.34, z), (hx + 0.315, 0.1, z), 0.008, 'iron', sides=4, caps=False))
    for z in (1.5, 1.52):
        pass
    M.add(cbox((hx - 0.02, -0.55, 1.5), (hx + 0.3, -0.45, 1.55), 0.01, 'iron'))
    M.add(cbox((hx - 0.02, 0.2, 1.5), (hx + 0.3, 0.3, 1.55), 0.01, 'iron'))
    # bulkhead lamp over the door
    lp, _ = lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.03), (0.085, 0.05), (0.06, 0.07), (0.0, 0.075)], 14, ['iron', 'iron', 'iron', 'lamp', 'lamp'], phase=0.0)
    lx = (dx0 + dx1) / 2
    xform(lp, T(lx, -hy - 0.02, dz1 + 0.24) @ R(PI / 2, 'X')); M.add(lp)
    for k in range(3):
        M.add(bar((lx - 0.09, -hy - 0.085, dz1 + 0.18 + k * 0.06), (lx + 0.09, -hy - 0.085, dz1 + 0.18 + k * 0.06), 0.012, 'iron', sides=4, caps=False))
    M.attach.append(('Lamp', (lx, -hy - 0.1, dz1 + 0.24)))
    # gutter and downpipe on the front
    M.add(tube([(-hx - 0.05, -hy - 0.1, zt + 0.0), (hx + 0.05, -hy - 0.1, zt + 0.0)], 0.05, 'p2', sides=6))
    M.add(tube([(-hx + 0.15, -hy - 0.1, zt), (-hx + 0.15, -hy - 0.08, zt - 0.2), (-hx + 0.15, -hy - 0.06, 0.4), (-hx + 0.3, -hy - 0.08, 0.15)], 0.04, 'p2', sides=6))
    # a notice board by the door with pinned papers (no text)
    M.add(cbox((0.95, -hy - 0.04, 1.25), (1.4, -hy - 0.0, 1.75), 0.01, 'timberw'))
    for (x, z, w_, h_, mtl) in ((1.0, 1.38, 0.16, 0.22, 'white'), (1.2, 1.46, 0.15, 0.2, 'cream'), (1.06, 1.62, 0.12, 0.09, 'amber')):
        M.add(cbox((x, -hy - 0.046, z), (x + w_, -hy - 0.04, z + h_), 0.003, mtl))
    M.feat('front', 'streaks', a0=-hx, a1=hx, top=zt - 0.15, n=60, length=(0.3, 1.4), col=(0.72, 0.62, 0.52), alpha=(0.25, 0.55), width=(0.01, 0.04))
    _front(M)
    return M


# ---------------------------------------------------------------- Digger
def digger():
    """A small, chunky tracked excavator: tracks, dozer blade, a rounded upper body with a
    counterweight, an open canopy over the seat, and the boom, stick and bucket reaching to +X
    with the bucket resting on the ground. About 5 m long."""
    M = Model('Digger', p1=SITE_YELLOW, p2=(0.30, 0.30, 0.33), ppm=50, grime=dict(rust=0.2, chips=0.45, streaks=0.6, dirt_h=0.6, ground=0.8))
    # tracks
    rt = 0.27; xe = 0.92; zc = rt
    for sy in (-1, 1):
        yc = sy * 0.62
        path = []
        for i in range(8):
            a = -PI / 2 + PI * i / 7
            path.append((xe + rt * math.cos(a), yc, zc + rt * math.sin(a)))
        for i in range(1, 3):
            path.append((xe - 2 * xe * i / 3, yc, zc + rt))
        for i in range(8):
            a = PI / 2 + PI * i / 7
            path.append((-xe + rt * math.cos(a), yc, zc + rt * math.sin(a)))
        for i in range(1, 3):
            path.append((-xe + 2 * xe * i / 3, yc, zc - rt))
        sec = [(-0.18, -0.03), (0.18, -0.03), (0.18, 0.03), (-0.18, 0.03)]
        M.add(sweep(path, sec, 'tex', up=(0, 1, 0), closed=True, caps=False, sm=2, uvtile=('tread', None)))
        M.add(cbox((-xe, yc - 0.15, 0.08), (xe, yc + 0.15, 0.46), 0.04, 'p2'))
        for x in (-xe, xe):
            w, _ = lathe([(0.0, 0.0), (0.24, 0.0), (0.24, 0.05), (0.12, 0.07), (0.0, 0.07)], 10, ['p2', 'p2', 'iron', 'iron'], phase=0.0)
            xform(w, T(x, yc + sy * 0.12, zc) @ R(-sy * PI / 2, 'X')); M.add(w)
        for x in (-0.45, 0.0, 0.45):
            w, _ = lathe([(0.075, 0.0), (0.075, 0.04), (0.0, 0.04)], 8, ['iron', 'iron'], phase=0.0)
            xform(w, T(x, yc + sy * 0.12, 0.1) @ R(-sy * PI / 2, 'X')); M.add(w)
    M.add(cbox((-0.7, -0.5, 0.25), (0.7, 0.5, 0.58), 0.04, 'p2'))
    M.add(xform(cyl(0.6, 0.0, 0.1, 14, 'iron'), T(0, 0, 0.58)))
    # dozer blade at +X
    prof = [(0.0, 0.0), (0.06, 0.0), (0.03, 0.12), (0.035, 0.28), (0.09, 0.4), (0.06, 0.42), (-0.01, 0.3), (-0.025, 0.14)]
    bl = extrude_poly(prof, 1.7, 'p1')
    xform(bl, T(1.42, 0.85, 0.03) @ basis((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0)))
    M.add(fix_normals(bl))
    for sy in (-1, 1):
        M.add(cbox((0.65, sy * 0.45 - 0.06, 0.18), (1.45, sy * 0.45 + 0.06, 0.3), 0.025, 'p1'))
    # upper structure
    zu = 0.68
    M.add(rbox((-1.05, -0.78, zu), (0.75, 0.78, zu + 0.62), (0.14, 0.14, 0.1), 'p1', seg=(2, 2, 1), skip=((2, -1),)))
    M.add(rbox((-1.35, -0.8, zu + 0.02), (-0.75, 0.8, zu + 0.66), (0.24, 0.2, 0.14), 'p1d', seg=(2, 1, 2), skip=((2, -1),)))
    M.add(rbox((-1.1, 0.0, zu + 0.6), (-0.15, 0.74, zu + 0.86), (0.1, 0.1, 0.08), 'p1', seg=(1, 1, 1), skip=((2, -1),)))
    vt = box((-0.98, 0.745, zu + 0.66), (-0.4, 0.75, zu + 0.8), 'p1k', skip=('-y',))
    settile(vt, 'vent', lambda co, f: ((co.x + 0.98) / 0.58, (co.z - zu - 0.66) / 0.14), mat='p1dk')
    M.add(vt)
    vt = box((-0.98, -0.785, zu + 0.2), (-0.45, -0.78, zu + 0.45), 'p1k', skip=('+y',))
    settile(vt, 'vent', lambda co, f: ((co.x + 0.98) / 0.53, (co.z - zu - 0.2) / 0.25), mat='p1dk')
    M.add(vt)
    M.add(tube([(-0.55, 0.45, zu + 0.84), (-0.55, 0.45, zu + 1.25)], 0.045, 'iron', sides=8))
    M.add(xform(cyl(0.05, 0, 0.06, 8, 'chrome'), T(-0.55, 0.45, zu + 1.23)))
    # canopy, seat and controls on the front (-Y) side
    zf = zu + 0.62
    M.add(cbox((-0.6, -0.76, zf), (0.5, 0.05, zf + 0.06), 0.02, 'p2'))
    seat = cbox((-0.42, -0.58, zf + 0.06), (0.0, -0.18, zf + 0.2), 0.04, 'p2')
    M.add(seat)
    M.add(cbox((-0.5, -0.58, zf + 0.15), (-0.38, -0.18, zf + 0.6), 0.04, 'p2'))
    for y in (-0.62, -0.14):
        M.add(cbox((-0.05, y - 0.05, zf + 0.06), (0.25, y + 0.05, zf + 0.3), 0.02, 'iron'))
        M.add(tube([(0.12, y, zf + 0.3), (0.16, y, zf + 0.45)], 0.012, 'dark', sides=5))
        M.add(xform(cyl(0.025, 0, 0.05, 8, 'dark'), T(0.16, y, zf + 0.45)))
    zr = zf + 1.15
    for (x, y) in ((-0.58, -0.74), (0.45, -0.74), (-0.58, 0.02), (0.45, 0.02)):
        M.add(tube([(x, y, zf + 0.05), (x, y, zr)], 0.035, 'p2', sides=6))
    M.add(rbox((-0.66, -0.82, zr - 0.02), (0.55, 0.1, zr + 0.1), (0.06, 0.06, 0.04), 'p1', seg=(1, 1, 1)))
    lp, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.05), (0.045, 0.06), (0.0, 0.06)], 10, ['iron', 'iron', 'lamp', 'lamp'], phase=0.0)
    xform(lp, T(0.56, -0.5, zr + 0.03) @ R(PI / 2, 'Y')); M.add(lp)
    M.attach.append(('Light', (0.63, -0.5, zr + 0.03)))
    # boom, stick and bucket (in the plane y = 0.32)
    yb = 0.32
    foot = Vector((0.7, yb, zu + 0.35))
    boom = [foot, Vector((1.0, yb, zu + 0.95)), Vector((1.35, yb, zu + 1.55)), Vector((1.8, yb, zu + 1.95)), Vector((2.3, yb, zu + 2.05))]
    sec = [(x, y) for x, y in rrect(0.11, 0.15, 0.05, 1)]
    M.add(sweep([tuple(p) for p in boom], sec, 'p1', up=(0, 1, 0), caps=True, scales=[1.0, 1.0, 0.95, 0.85, 0.75], sm=0))
    elbow = boom[-1]
    tipp = Vector((3.0, yb, 0.62))
    sec2 = [(x, y) for x, y in rrect(0.09, 0.11, 0.04, 1)]
    M.add(sweep([tuple(elbow + Vector((-0.05, 0, 0.12))), tuple(elbow), tuple(tipp)], sec2, 'p1', up=(0, 1, 0), caps=True, scales=[1.0, 1.0, 0.8], sm=0))
    for p in (foot, elbow, tipp):
        M.add(xform(cyl(0.06, -0.14, 0.14, 8, 'iron'), T(p) @ R(PI / 2, 'X')))
    # bucket: a curled shell (an annular sector in the XZ plane) with side plates and teeth
    C = (0.12, -0.30); Ro, Ri = 0.29, 0.23
    angs = [math.radians(100 - 250 * i / 10) for i in range(11)]
    outer = [(C[0] + Ro * math.cos(a), C[1] + Ro * math.sin(a)) for a in angs]
    inner = [(C[0] + Ri * math.cos(a), C[1] + Ri * math.sin(a)) for a in reversed(angs)]
    toXZ = basis((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    bk = extrude_poly(outer + inner, 0.46, 'p1')
    xform(bk, T(tipp + Vector((0, 0.23, 0))) @ toXZ)
    M.add(fix_normals(bk))
    for sy in (-1, 1):
        sp = extrude_poly(outer, 0.02, 'p1d')
        xform(sp, T(tipp + Vector((0, sy * 0.24 + 0.01, 0))) @ toXZ)
        M.add(fix_normals(sp))
    al = angs[-1]; lr = (Ro + Ri) / 2
    lip = Vector((tipp.x + C[0] + lr * math.cos(al), 0, tipp.z + C[1] + lr * math.sin(al)))
    tang = math.atan2(-math.cos(al), math.sin(al))
    for k in range(4):
        y = yb - 0.18 + 0.12 * k
        tth = extrude_poly([(0.0, -0.028), (0.09, 0.0), (0.0, 0.028)], 0.05, 'metal')
        xform(tth, T(lip.x, y + 0.025, lip.z) @ toXZ @ R(tang, 'Z'))
        M.add(fix_normals(tth))
    # hydraulic cylinders and hoses
    def ram(a, b, rb=0.06, rr=0.035, frac=0.55):
        a = Vector(a); b = Vector(b); m = a + (b - a) * frac
        M.add(xform(cyl(rb, 0.0, (m - a).length, 8, 'iron', bevel=0.012), along(a, m)))
        M.add(xform(cyl(rr, 0.0, (b - m).length + 0.04, 6, 'chrome', caps=(False, True)), along(m - (b - m).normalized() * 0.04, b)))
    ram((0.72, yb, zu + 0.12), (1.3, yb, zu + 1.38))
    ram((1.45, yb, zu + 1.86), (2.25, yb, zu + 2.32), frac=0.6)
    ram((2.4, yb, zu + 1.95), (2.95, yb, 0.95), rb=0.05, rr=0.03, frac=0.6)
    for dy in (-0.07, 0.07):
        M.add(tube([(0.75, yb + dy, zu + 0.55), (1.1, yb + dy, zu + 1.18), (1.45, yb + dy, zu + 1.72), (1.9, yb + dy, zu + 2.05), (2.25, yb + dy, zu + 2.17)], 0.018, 'dark', sides=5))
    _front(M)
    return M


SITE_MODELS = [tower_crane, crane_hook, crane_trolley, crane_load, hoist_mast, hoist_mast_cap, hoist_cage, concrete_pipe,
               scaffold, site_fence, portaloo, skip, cement_mixer, wheelbarrow, pipe_stack, steel_beams, site_cabin, digger]
