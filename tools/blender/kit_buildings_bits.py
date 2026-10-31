# Shared bits of the buildings kit (kit_buildings.py and kit_buildings_town.py): vents, brackets,
# door hoods, gutters, pipes, flat tops, shop rooms, pendants, produce crates, sign bands, trellises,
# climbers, mailboxes, benches, gas bottles, hose reels, bollards, pallets, sacks, tanks, dishes,
# antennas and flagpoles. Coordinates as in kit_buildings_parts.py.
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_buildings_geo import *
from kit_buildings_parts import *


# ---------------------------------------------------------------- shared bits
def attic_vent(B, wf, x, y, r=0.3):
    """A round louvred vent on a gable."""
    rb, _ = lathe([(r, 0.0), (r, 0.05), (r * 0.92, 0.07), (r * 0.8, 0.07), (r * 0.78, 0.04)], 12, 'trim', phase=0.5)
    xform(rb, T(x, y, 0)); put(B, wf, rb)
    d, tags = lathe([(r * 0.79, 0.03), (0, 0.03)], 12, 'tex', phase=0.5)
    uv_fn(d, list(d.faces), 'vent', lambda co: (0.5 + co.x / (2 * r), 0.5 + co.y / (2 * r)), 0.0)
    xform(d, T(x, y, 0)); put(B, wf, d)


def knee_brackets(B, wf, xs, z_top, depth, mat='woodc', drop=0.55, t=0.08):
    for x in xs:
        prof = [(0.0, -drop), (t, -drop), (t, -0.16), (depth - 0.08, 0.0), (depth - 0.08, 0.06), (0.0, 0.06)]
        b = extrude_poly(prof, t, mat)
        xform(b, T(x + t / 2, z_top, 0) @ R(-PI / 2, 'Y'))
        put(B, wf, b)


def door_hood(B, wf, xc, w, z_eave, rise, depth=0.85, brackets='woodc'):
    """A little tiled gable hood over a door, on two knee brackets (front wall only)."""
    p = wf.P(xc, 0, 0)
    pitched(B, 'y', p.x - w / 2, p.x + w / 2, -depth, -0.02, z_eave, rise, t=0.12, row=0.2, lip=0.03, mat='roofb',
            barge=(True, False), over=0.03, barge_w=0.16, fmap='roofb')
    mb = MB()
    tri = [(xc - w / 2 + 0.1, z_eave + 0.06), (xc, z_eave + rise - 0.02), (xc + w / 2 - 0.1, z_eave + 0.06)]
    mb.face([(x, y, depth - 0.04) for x, y in tri], 'trimw', (0, 0, 1), 0.92)
    put(B, wf, mb.bm())
    knee_brackets(B, wf, (xc - w / 2 + 0.16, xc + w / 2 - 0.16), z_eave, depth, brackets)
    a0, _ = wf.ab(xc - w / 2, 0); a1, _ = wf.ab(xc + w / 2, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z_eave - 0.02, length=0.55, k=0.55)


def gable_gutters(B, a0, a1, r0, r1, zg, pipe_y=0.3, pipe_side=1):
    """Gutters along both side eaves of a roof whose ridge runs along Y, and one downpipe."""
    eave_gutter(B, [(a1 + 0.045, r0), (a1 + 0.045, r1)], zg)
    eave_gutter(B, [(a0 - 0.045, r1), (a0 - 0.045, r0)], zg)
    xg = (a1 + 0.045 + 0.07) if pipe_side > 0 else (a0 - 0.045 - 0.07)
    xw = (B.W / 2 + 0.075) if pipe_side > 0 else (-B.W / 2 - 0.075)
    zt = zg - 0.1
    pts = [(xg, pipe_y, zt), (xg, pipe_y, zt - 0.15), (xw, pipe_y, zt - 0.45), (xw, pipe_y, 0.32), (xw + 0.12 * pipe_side, pipe_y, 0.12)]
    downpipe(B, pts, brackets=[(xw, pipe_y, z) for z in np.arange(0.9, zt - 0.6, 1.7)])


def wall_pipe(B, x, y, z_top, z_bot=0.12, head=True, out=(0, -1)):
    """A downpipe from a rainwater head under a parapet down a wall to a shoe."""
    ox, oy = out
    if head:
        B.add(cbox2((x - 0.13, y - 0.11, z_top - 0.32), (x + 0.13, y + 0.11, z_top), 0.02, 'pipe'))
    pts = [(x, y, z_top - 0.3), (x, y, z_bot + 0.2), (x + ox * 0.12, y + oy * 0.12, z_bot)]
    downpipe(B, pts, brackets=[(x, y, z) for z in np.arange(1.0, z_top - 0.6, 2.3)])


def flat_top(B, zt, ph, path=None, coping_mat='trim', inner=0.22, maps=('front', 'right', 'left'), roof=True):
    """Parapet inner faces, coping, a flat roof inside, rain run-off painted under the coping."""
    W, D = B.W, B.D
    rp = path or [(-W / 2, 0), (W / 2, 0), (W / 2, D), (-W / 2, D)]
    if roof:
        B.add(box((-W / 2 + inner - 0.01, inner - 0.01, zt - 0.1), (W / 2 - inner + 0.01, D - inner + 0.01, zt + 0.02), 'roof',
                  skip=('-z', '-x', '+x', '-y', '+y')))
        B.feat('roof', 'flat', x0=-W / 2 + inner, x1=W / 2 - inner, y0=inner, y1=D - inner)
    B.add(band(rp, [(-inner, zt + ph), (-inner, zt)], 'wallw', closed=path is None), shade=0.85)
    coping(B, rp, zt + ph, mat=coping_mat, inner=inner + 0.02, closed=path is None)
    for mp in maps: B.feat(mp, 'top', b=zt + ph - 0.03, k=1.0)


def shop_room(B, x0, x1, z0, z1, depth, floor='conc'):
    """A dim room behind an open shopfront (faces looking in)."""
    mb = MB()
    mb.face([(x0, depth, z0), (x1, depth, z0), (x1, depth, z1), (x0, depth, z1)], 'interior', (0, -1, 0), 0.8)
    mb.face([(x0, 0, z0), (x0, depth, z0), (x0, depth, z1), (x0, 0, z1)], 'interior', (1, 0, 0), 0.9)
    mb.face([(x1, 0, z0), (x1, 0, z1), (x1, depth, z1), (x1, depth, z0)], 'interior', (-1, 0, 0), 0.9)
    mb.face([(x0, 0, z1), (x1, 0, z1), (x1, depth, z1), (x0, depth, z1)], 'interior', (0, 0, -1), 0.75)
    mb.face([(x0, 0, z0), (x0, depth, z0), (x1, depth, z0), (x1, 0, z0)], floor, (0, 0, 1), 0.7)
    B.add(mb.bm())


def pendant(B, x, y, z_ceiling, drop=0.6, mat='accentw'):
    B.add(tube([(x, y, z_ceiling), (x, y, z_ceiling - drop)], 0.01, 'black', 4))
    sh, _ = lathe([(0, -0.02), (0.2, -0.02), (0.19, 0.0), (0.06, 0.13), (0.03, 0.15), (0.0, 0.15)], 10, ['lamp', mat, mat, mat, mat], phase=0.5)
    xform(sh, T(x, y, z_ceiling - drop - 0.15)); B.add(sh)


def crate(B, c, size, kind, tilt=0.0, mound=0.07, yaw=0.0, mat='wood'):
    """An open slatted crate heaped with produce (the heap's fruit are painted in the atlas)."""
    w, d, h = size
    cb = box((-w / 2, -d / 2, 0), (w / 2, d / 2, h), mat, skip=('+z', '-z'))
    if mat == 'wood': uv_box(cb, list(cb.faces), 'crate', 0.0)
    nx, ny = 3, 2
    V = []; F = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -w / 2 + 0.025 + (w - 0.05) * i / nx; y = -d / 2 + 0.025 + (d - 0.05) * j / ny
            q = (1 - (2 * i / nx - 1) ** 2) * (1 - (2 * j / ny - 1) ** 2)
            V.append((x, y, h * 0.82 + mound * (0.35 + q)))
    for j in range(ny):
        for i in range(nx):
            F.append([j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i])
    mb, _ = bm_from(V, F, 'tex', sm=1)
    uv_fn(mb, list(mb.faces), 'p_' + kind, lambda co: ((co.x + w / 2) / w, (co.y + d / 2) / d), 0.02)
    merge(cb, mb)
    xform(cb, T(c) @ R(yaw, 'Z') @ R(tilt, 'X'))
    B.add(cb)


def melon(B, c, r=0.17, seed=0):
    m = blob(c, (r * 1.15, r * 0.95, r * 0.88), 'melon', 8, 3, seed, 0.04)
    cx, cy = c[0], c[1]
    uv_fn(m, list(m.faces), 'melon', lambda co: ((math.atan2(co.y - cy, co.x - cx) / (2 * PI)) % 1.0, 0.5 + (co.z - c[2]) / (2 * r)), 0.02)
    B.add(m)


def shape(B, wf, pts, cx, cy, z, depth, mat, rot=0.0, s=1.0):
    cr, sr = math.cos(rot), math.sin(rot)
    p2 = [(cx + s * (x * cr - y * sr), cy + s * (x * sr + y * cr)) for x, y in pts]
    bm = extrude_poly(p2, depth, mat)
    xform(bm, T(0, 0, z)); put(B, wf, bm)


def arc_strip(r0, r1, a0, a1, n):
    out = [(r1 * math.cos(a0 + (a1 - a0) * k / n), r1 * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
    inn = [(r0 * math.cos(a0 + (a1 - a0) * k / n), r0 * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n, -1, -1)]
    return out + inn


def wave_strip(x0, y0, y1, amp, w, n=6, ph=0.0):
    left = [(x0 - w / 2 + amp * math.sin(ph + 6 * k / n), y0 + (y1 - y0) * k / n) for k in range(n + 1)]
    right = [(x0 + w / 2 + amp * math.sin(ph + 6 * k / n), y0 + (y1 - y0) * k / n) for k in range(n, -1, -1)]
    return left + right


def apple_pts(r=0.25, n=16):
    pts = []
    for k in range(n):
        a = 2 * PI * k / n
        rr = r * (1 - 0.2 * math.exp(-(min(a, 2 * PI - a) ** 2) / 0.08) - 0.06 * math.exp(-((a - PI) ** 2) / 0.1))
        pts.append((rr * math.sin(a) * (1 + 0.06 * math.cos(a)), rr * math.cos(a) * 0.95))
    return pts


def sign_board(B, wf, x0, x1, z0, z1, out=0.2, frame='accentp', panel='creamp', bw=0.1):
    """A sign band: a proud frame round a recessed panel. Returns the panel's front (w)."""
    put(B, wf, fbox((x0, z0, 0), (x1, z0 + bw, out), 0.025, frame))
    put(B, wf, fbox((x0, z1 - bw, 0), (x1, z1, out), 0.025, frame))
    put(B, wf, fbox((x0, z0 + bw, 0), (x0 + bw, z1 - bw, out), 0.02, frame))
    put(B, wf, fbox((x1 - bw, z0 + bw, 0), (x1, z1 - bw, out), 0.02, frame))
    put(B, wf, fbox((x0 + bw, z0 + bw, 0), (x1 - bw, z1 - bw, out - 0.05), 0.01, panel))
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z0, length=0.3, k=0.45)
    B.attach.append(('Sign', tuple(round(c, 3) for c in wf.P((x0 + x1) / 2, (z0 + z1) / 2, out))))
    return out - 0.05


def bulkhead(B, wf, x, y, name='Lamp'):
    put(B, wf, cbox2((x - 0.13, y - 0.09, 0), (x + 0.13, y + 0.09, 0.09), 0.035, 'metald'))
    put(B, wf, cbox2((x - 0.1, y - 0.06, 0.07), (x + 0.1, y + 0.06, 0.12), 0.02, 'lamp'))
    p = wf.P(x, y, 0.12)
    B.lamps.append({'name': name, 'center': [round(p.x, 3), round(p.y, 3), round(p.z, 3)]})


def trellis(B, wf, x0, x1, z0, z1, seed=0):
    """A timber lattice on the wall with a climbing plant and a planter at its foot."""
    for k in range(5):
        x = x0 + (x1 - x0) * k / 4
        put(B, wf, fbox((x - 0.025, z0, 0.0), (x + 0.025, z1, 0.05), 0.01, 'woodc'))
    for k in range(5):
        z = z0 + 0.35 + (z1 - z0 - 0.45) * k / 4
        put(B, wf, fbox((x0 - 0.06, z - 0.022, 0.05), (x1 + 0.06, z + 0.022, 0.085), 0.01, 'woodc'))
    put(B, wf, fbox((x0 - 0.1, 0.0, 0.0), (x1 + 0.1, 0.42, 0.42), 0.03, 'woodc'))
    for k in range(10):
        t = k / 9
        x = x0 + (x1 - x0) * (0.5 + 0.42 * math.sin(t * 5.0 + seed))
        z = 0.5 + (z1 - 0.3) * t
        r = 0.2 - 0.06 * t
        put(B, wf, blob((x, z, 0.16), (r * 1.2, r, r * 0.7), ['leaf', 'leafd', 'leafl'][k % 3], 6, 2, seed * 11 + k))
        if k % 2 == 0:
            put(B, wf, blob((x + 0.1, z + 0.08, 0.26), (0.05, 0.05, 0.04), 'fl1' if seed % 2 else 'fl5', 4, 1, seed * 3 + k))
    for k in range(3):
        put(B, wf, blob((x0 + (x1 - x0) * (0.2 + 0.3 * k), 0.5, 0.22), (0.2, 0.15, 0.16), 'leaf', 6, 2, seed + 40 + k))


def climber(B, wf, x, z0, z1, spread, seed=0, n=14, flowers='fl4'):
    """A clinging climber: overlapping flat leaf masses, wide and dark at the foot, thinning upward."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        t = (k + rng.random() * 0.6) / n
        v = z0 + (z1 - z0) * t ** 0.85
        u = x + spread * (1 - 0.6 * t) * (rng.random() - 0.5) * 1.6
        r = 0.3 * (1 - 0.45 * t) * rng.uniform(0.85, 1.15)
        put(B, wf, blob((u, v, 0.05 + 0.02 * rng.random()), (r * 1.1, r, 0.08), ['leafd', 'leaf', 'leafl', 'leaf'][k % 4], 7, 2, seed * 17 + k, 0.22))
    for k in range(n // 3):
        t = rng.random()
        put(B, wf, blob((x + spread * 0.6 * (rng.random() - 0.5), z0 + (z1 - z0) * t, 0.13), (0.045, 0.045, 0.035), flowers, 4, 1, seed * 5 + k))


def mailbox(B, wf, x, y, mat='accentw'):
    put(B, wf, cbox2((x - 0.17, y - 0.2, 0), (x + 0.17, y + 0.2, 0.14), 0.03, mat))
    put(B, wf, box((x - 0.11, y + 0.1, 0.13), (x + 0.11, y + 0.125, 0.145), 'black'))


def bench(B, wf, x0, x1):
    for k in range(3):
        put(B, wf, fbox((x0, 0.44, 0.12 + k * 0.11), (x1, 0.48, 0.21 + k * 0.11), 0.01, 'woodc'))
    put(B, wf, fbox((x0, 0.62, 0.02), (x1, 0.74, 0.06), 0.01, 'woodc'))
    put(B, wf, fbox((x0, 0.8, 0.02), (x1, 0.9, 0.06), 0.01, 'woodc'))
    for x in (x0 + 0.1, x1 - 0.14):
        put(B, wf, box((x, 0.0, 0.14), (x + 0.05, 0.44, 0.19), 'woodd'))
        put(B, wf, box((x, 0.0, 0.32), (x + 0.05, 0.44, 0.37), 'woodd'))
        put(B, wf, box((x, 0.44, 0.0), (x + 0.05, 0.9, 0.05), 'woodd'))


def gas_bottle(B, P, mat='red'):
    gb, _ = lathe([(0.0, 0.0), (0.15, 0.0), (0.16, 0.04), (0.16, 0.5), (0.12, 0.6), (0.05, 0.62), (0.05, 0.7), (0.0, 0.7)], 10,
                  [mat, mat, mat, mat, mat, 'metal', 'metal'])
    xform(gb, T(P)); B.add(gb)


def hose_reel(B, wf, x, y):
    put(B, wf, tube([(x, y + 0.3, 0.0), (x, y + 0.3, 0.12), (x, y + 0.2, 0.14)], 0.02, 'metal', 5))
    ring = [(x + 0.2 * math.cos(2 * PI * k / 10), y + 0.2 * math.sin(2 * PI * k / 10), 0.1) for k in range(11)]
    put(B, wf, tube(ring, 0.028, 'green', 5, caps=False))
    put(B, wf, tube(ring[:6] + [(x - 0.12, y - 0.45, 0.2), (x + 0.05, 0.03, 0.4), (x + 0.45, 0.03, 0.62)], 0.022, 'green', 5))


def bollard(B, P):
    bm, _ = lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.25), (0.12, 0.45), (0.12, 0.65), (0.12, 0.85), (0.08, 0.92), (0.0, 0.94)], 10,
                  ['black', 'yellow', 'black', 'yellow', 'black', 'black', 'black'])
    xform(bm, T(P)); B.add(bm)


def pallet(B, x0, y0, z0, w=1.2, d=0.8, mat='woodc'):
    for k in range(5):
        x = x0 + (w - 0.12) * k / 4
        B.add(box((x, y0, z0 + 0.1), (x + 0.12, y0 + d, z0 + 0.13), mat, skip=('-z',)))
    for y in (y0, y0 + d / 2 - 0.05, y0 + d - 0.1):
        B.add(box((x0, y, z0), (x0 + w, y + 0.1, z0 + 0.1), 'woodd', skip=('-z',)))


def sack(B, P, s=1.0, mat='cream'):
    B.add(blob(Vector(P) + Vector((0, 0, 0.2 * s)), (0.28 * s, 0.2 * s, 0.22 * s), mat, 7, 2, 3, 0.1, flat_bottom=0.15))


def tank(B, x, y, z0, r=0.72, h=1.4, stand=1.0):
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.add(box((x + sx * r * 0.6 - 0.04, y + sy * r * 0.6 - 0.04, z0), (x + sx * r * 0.6 + 0.04, y + sy * r * 0.6 + 0.04, z0 + stand), 'metald', skip=('-z', '+z')))
    B.add(tube([(x - r * 0.6, y - r * 0.6, z0 + stand * 0.45), (x + r * 0.6, y + r * 0.6, z0 + stand * 0.05)], 0.02, 'metald', 4))
    B.add(tube([(x + r * 0.6, y - r * 0.6, z0 + stand * 0.45), (x - r * 0.6, y + r * 0.6, z0 + stand * 0.05)], 0.02, 'metald', 4))
    B.add(fbox((x - r * 0.8, y - r * 0.8, z0 + stand - 0.08), (x + r * 0.8, y + r * 0.8, z0 + stand), 0.02, 'metald', back=True))
    z = z0 + stand
    tb, _ = lathe([(r * 0.98, 0.0), (r, 0.06), (r, h * 0.45), (r * 1.04, h * 0.5), (r, h * 0.55), (r, h * 0.92), (r * 0.7, h * 1.02),
                   (r * 0.25, h * 1.07), (r * 0.25, h * 1.12), (0, h * 1.12)], 9, 'tank')
    xform(tb, T(x, y, z)); B.add(tb)
    B.add(tube([(x + r * 0.7, y, z + 0.15), (x + r + 0.2, y, z + 0.15), (x + r + 0.2, y, z0 - 0.0)], 0.035, 'metal', 6))


def dish(B, P, d=(0, -1, 0.35), r=0.38):
    dm, _ = lathe([(0.0, 0.0), (r, 0.09), (r * 0.96, 0.06), (0.0, -0.03)], 9, 'white', phase=0.5)
    M = frame(Vector(P), Vector(d))
    xform(dm, M); B.add(dm)
    tip = Vector(P) + Vector(d).normalized() * (r * 0.9)
    B.add(tube([Vector(P) + Vector((0, 0, -0.05)), tip], 0.012, 'metald', 4))
    B.add(cbox2(tip - Vector((0.04, 0.04, 0.04)), tip + Vector((0.04, 0.04, 0.04)), 0.01, 'metald'))
    B.add(tube([Vector(P) + Vector((0, 0.05, -0.05)), Vector(P) + Vector((0, 0.25, -0.5))], 0.025, 'metald', 5))


def antenna(B, x, y, z0, h=1.8):
    B.add(tube([(x, y, z0), (x, y, z0 + h)], 0.025, 'metald', 5))
    for k, w in enumerate((1.0, 0.8, 0.6)):
        z = z0 + h - 0.15 - k * 0.3
        B.add(box((x - 0.02, y - w / 2, z - 0.015), (x + 0.02, y + w / 2, z + 0.015), 'metald'))


def flagpole(B, x, y, z0, h=4.5, mat='accentw'):
    B.add(tube([(x, y, z0), (x, y, z0 + h)], 0.04, 'white', 6))
    B.add(blob((x, y, z0 + h + 0.05), (0.07, 0.07, 0.07), 'brass', 6, 2, 1, 0.0))
    pts = []
    n = 6
    for k in range(n + 1):
        t = k / n
        pts.append((t * 1.3, 0.0 + 0.08 * math.sin(t * 5)))
    poly = [(p[0], -0.0) for p in pts] + [(p[0], -0.75 + 0.18 * p[0] / 1.3) for p in reversed(pts)]
    fl = extrude_poly(poly, 0.02, mat, back=True)
    for v in fl.verts: v.co.z += 0.1 * math.sin(v.co.x * 4)
    xform(fl, T(x + 0.04, y, z0 + h - 0.1) @ R(PI / 2, 'X'))
    B.add(fl)
