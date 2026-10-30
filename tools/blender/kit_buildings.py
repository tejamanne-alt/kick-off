# The BUILDINGS kit for Dribble To School: original, cozy, stylized buildings for the streets,
# modelled by script in Blender (read docs/ART_DIRECTION.md first).
#   blenv/bin/python kit_buildings.py -- /abs/outdir [--only HouseGable,School]
# Writes into outdir: <Model>.fbx per model, BuildingsAtlas.png, Buildings.json, Buildings.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Buildings.blend /abs/outdir/sheet.png
#
# Placement contract (matches the game's procedural House3D): the origin is the centre of the front
# wall's base (z = 0); the street face looks along -Y and the building extends back along +Y; width
# runs along X. "wall" is the front wall's height to the eaves or the parapet; roofs add height on
# top. Each FBX has one root mesh named after the model and Attach.* empties: Front (1 m in front of
# the origin, for the facing check), Door*, Window.N (glass centres), Lamp.N, plus model extras.
#
# One material: vertex colours x BuildingsAtlas.png. UV0 = atlas, UV1.x = recolour part:
# 0 fixed, 1 wall paint, 2 accent / trim (doors, shutters, awnings, sign frames, balcony fronts),
# 3 roof. Painted parts carry their base colour times soft baked shading in the vertex colours;
# grime, streaks, contact shadows, tile joints and rust live in the atlas, so a recolour keeps them.
# The manifest (Buildings.json) records each part's base colour (sRGB, as in the FBX).
#
# Modules: kit_buildings_geo.py (pieces, primitives, atlas layout, mesh conversion),
# kit_buildings_parts.py (walls, windows, doors, roofs, details), kit_buildings_atlas.py (painting).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector, Matrix
import kit_lib as K
from kit_buildings_geo import *
from kit_buildings_parts import *
import kit_buildings_atlas as ATL

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else '/tmp/buildings'
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None


def pal(wall, accent, roof, **kw):
    p = {'wall': wall, 'accent': accent, 'roof': roof, 'trim': (0.96, 0.94, 0.88), 'stone': (0.70, 0.67, 0.63),
         'conc': (0.80, 0.78, 0.74), 'frame': (0.96, 0.95, 0.91), 'soffit': (0.90, 0.87, 0.80), 'pipe': (0.68, 0.70, 0.72)}
    p.update(kw)
    return p


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


# ---------------------------------------------------------------- HouseGable
def house_gable(B):
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    gf = 3.2
    t, cap = 0.17, 0.11
    k = (RH - t - cap) / (W / 2)
    apex = H + (W / 2) * k
    ph = 0.45; v0 = ph - 0.06
    door_o = (-2.95, -1.85, 0.30, 2.45)
    win_g = (0.45, 2.65, 0.95, 2.30)
    win_u = [(-2.4, -0.9, 3.75, 5.1), (0.9, 2.4, 3.75, 5.1)]
    gable = [(-W / 2, H), (0.0, apex), (W / 2, H)]
    # ground floor in render with chamfered corners, upper floor and gables in lap siding
    wall(B, F, -W / 2 + c, W / 2 - c, gf, [door_o, win_g], v0)
    wall(B, Rt, c, D - c, gf, [(2.7, 3.9, 1.0, 2.2)], v0)
    wall(B, Lf, -D + c, -c, gf, [(-3.9, -2.7, 1.0, 2.2)], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, gf, [], v0)
    box_shell_corners(B, v0, gf, c)
    wall(B, F, -W / 2, W / 2, gable, win_u, gf, 'lap')
    wall(B, Rt, 0, D, H, [(2.9, 4.0, 3.85, 5.0)], gf, 'lap')
    wall(B, Lf, -D, 0, H, [(-4.0, -2.9, 3.85, 5.0)], gf, 'lap')
    wall(B, Bk, -W / 2, W / 2, gable, [], gf, 'flat')
    for x, y in ((W / 2, 0), (-W / 2, 0), (W / 2, D), (-W / 2, D)):
        corner_board(B, x, y, gf, H - 0.02)
    for path, closed in ring_path(B):
        string_course(B, path, gf - 0.08, gf + 0.1, out=0.075, closed=closed)
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, closed=closed)
    e = 0.38
    a0, a1 = -W / 2 - e, W / 2 + e
    z0 = H - e * k
    top = pitched(B, 'y', a0, a1, -0.42, D + 0.42, z0, (W / 2 + e) * k, t=t)
    gable_gutters(B, a0, a1, -0.47, D + 0.47, z0 - 0.04, pipe_y=0.3, pipe_side=1)
    chimney(B, 1.7, D - 1.9, H, apex + 0.55, pots=2)
    attic_vent(B, F, 0.0, H + 1.05, 0.3)
    door(B, F, *door_o, glass=0.32, panels=((2, 2),), name='Door')
    steps(B, F, door_o[0] - 0.12, door_o[1] + 0.12, [0.30, 0.15])
    door_hood(B, F, (door_o[0] + door_o[1]) / 2, 1.75, 2.66, 0.44)
    lantern(B, F, -1.5, 1.95)
    pot(B, (-1.2, -0.42, 0), 0.19, 0.3, 'pot', 'flowers', seed=1)
    pot(B, (-3.22, -0.75, 0), 0.17, 0.34, 'pot3', 'tall', seed=2, scale=0.9)
    meter_box(B, F, -1.0, 0.9)
    window(B, F, *win_g, cols=3, transom=0.72, planter='accent', glass='glass1', seed=3, head='key')
    for kk, wo in enumerate(win_u):
        window(B, F, *wo, cols=2, head=None, casing=True, shutters='accent', planter='pot', glass=('glass2', 'glass1')[kk], seed=4 + kk)
    window(B, Rt, 2.7, 3.9, 1.0, 2.2, cols=2, glass='glass0', seed=6, cheap=True)
    window(B, Rt, 2.9, 4.0, 3.85, 5.0, cols=2, head=None, casing=True, glass='glass2', seed=7)
    window(B, Lf, -3.9, -2.7, 1.0, 2.2, cols=2, glass='glass0', seed=8, cheap=True, register=False)
    window(B, Lf, -4.0, -2.9, 3.85, 5.0, cols=2, head=None, casing=True, glass='glass1', seed=9, register=False)
    B.add(cbox2((W / 2 + 0.05, 4.7, 0.0), (W / 2 + 0.5, 5.8, 0.1), 0.02, 'conc'))
    ac_unit(B, Rt, 5.25, 0.1, 0.0, w=0.9, h=0.62, d=0.36, brackets=False)
    vent(B, Rt, 1.2, 2.5, 0.26)
    B.feat('front', 'patch', a=3.05, b=1.55, w=0.3, h=0.18)
    B.feat('right', 'patch', a=6.3, b=2.5, w=0.24, h=0.15)
    return top + 0.11


# ---------------------------------------------------------------- HouseLong
def house_long(B):
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    gf = 3.0
    t, cap = 0.17, 0.11
    k = (RH - t - cap) / (D / 2)
    apex = H + (D / 2) * k
    ph = 0.42; v0 = ph - 0.06
    door_o = (-3.85, -2.85, 0.25, 2.42)
    bay = (0.4, 4.0)
    wins_u = [(-4.05, -2.55), (-0.75, 0.75), (2.55, 4.05)]
    wz = (3.65, 4.95)
    # ground floor render; the bay window stands in its own opening
    wall(B, F, -W / 2 + c, W / 2 - c, gf, [door_o, (bay[0], bay[1], 0.0, 2.62)], v0)
    wall(B, Rt, c, D - c, gf, [(2.6, 3.8, 0.95, 2.15)], v0)
    wall(B, Lf, -D + c, -c, gf, [], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, gf, [], v0)
    box_shell_corners(B, v0, gf, c)
    # upper floor: board and batten; the gables on the sides in lap siding
    ups = [(a, b, wz[0], wz[1]) for a, b in wins_u]
    wall(B, F, -W / 2, W / 2, H, ups, gf)
    wall(B, Rt, 0, D, [(0.0, H), (D / 2, apex), (D, H)], [(3.0, 4.0, 3.75, 4.85)], gf, 'lap')
    wall(B, Lf, -D, 0, [(-D, H), (-D / 2, apex), (0, H)], [], gf, 'lap')
    wall(B, Bk, -W / 2, W / 2, H, [], gf)
    for x, y in ((W / 2, 0), (-W / 2, 0), (W / 2, D), (-W / 2, D)):
        corner_board(B, x, y, gf, H - 0.02)
    mb = MB()
    for x in np.arange(-W / 2 + 0.3, W / 2 - 0.2, 0.42):
        segs = [(gf + 0.3, H - 0.05)]
        for a, b in wins_u:
            if a - 0.16 < x < b + 0.16:
                segs = [(gf + 0.3, wz[0] - 0.12), (wz[1] + 0.22, H - 0.05)]
        for z0_, z1_ in segs:
            if z1_ - z0_ > 0.1: bar(mb, x - 0.03, z0_, x + 0.03, z1_, 0.0, 0.03, 'wall')
    put(B, F, mb.bm())
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1]), (bay[0], bay[1])]):
        plinth(B, path, ph, closed=closed)
    # the pent roof between the floors (a lean-to across the front)
    pk = 0.55
    pitched(B, 'x', -0.82, 0.82, -W / 2 - 0.1, W / 2 + 0.1, gf - 0.12, 0.82 * pk, t=0.14, row=0.24, lip=0.032, mat='roofb',
            slopes=(0,), ridge=False, barge=(True, True), over=0.03, barge_w=0.18, fmap='roofb')
    B.add(fbox((-W / 2 - 0.12, 0.0, gf - 0.12 + 0.82 * pk + 0.1), (W / 2 + 0.12, 0.09, gf - 0.12 + 0.82 * pk + 0.24), 0.02, 'galvw'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=gf - 0.2, length=0.7, k=0.55)
    # main roof: ridge along X, the front slope faces the street
    e = 0.4
    a0, a1 = -e, D + e
    z0 = H - e * k
    top = pitched(B, 'x', a0, a1, -W / 2 - 0.32, W / 2 + 0.32, z0, (D / 2 + e) * k, t=t)
    eave_gutter(B, [(-W / 2 - 0.37, a0 - 0.045), (W / 2 + 0.37, a0 - 0.045)], z0 - 0.04)
    downpipe(B, [(W / 2 + 0.22, a0 - 0.115, z0 - 0.15), (W / 2 + 0.22, a0 - 0.115, z0 - 0.3), (W / 2 + 0.075, 0.3, z0 - 0.75),
                 (W / 2 + 0.075, 0.3, 0.32), (W / 2 + 0.2, 0.3, 0.12)], brackets=[(W / 2 + 0.075, 0.3, z) for z in (0.9, 2.6, 4.2)])
    chimney(B, -3.2, D / 2 + 0.5, H, apex + 0.75, w=0.7, d=0.6, pots=2)
    antenna(B, 2.6, D / 2, apex + 0.15, 1.5)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.5, k=0.45)
    # door under the pent roof, trellis, bay window
    door(B, F, *door_o, glass=None, panels=((2, 3),), name='Door')
    steps(B, F, door_o[0] - 0.1, door_o[1] + 0.1, [0.25, 0.12])
    lantern(B, F, -2.45, 1.95)
    mailbox(B, F, -2.45, 1.15)
    trellis(B, F, -2.0, -0.95, 0.0, 2.55, seed=3)
    by0, by1, bd = bay[0], bay[1], 0.5
    bf = WF((0, -bd, 0), (1, 0, 0), 'front')
    bl = WF((by0, 0, 0), (0, -1, 0), 'left')
    br = WF((by1, -bd, 0), (0, 1, 0), 'right')
    wall(B, bf, by0, by1, 2.6, [(by0 + 0.16, by1 - 0.16, 0.72, 2.38)], 0.0)
    wall(B, bl, 0, bd, 2.6, [(0.08, bd - 0.08, 0.72, 2.38)], 0.0)
    wall(B, br, 0, bd, 2.6, [(0.08, bd - 0.08, 0.72, 2.38)], 0.0)
    window(B, bf, by0 + 0.16, by1 - 0.16, 0.72, 2.38, depth=0.1, cols=3, transom=0.74, glass='glass1', head=None, seed=11)
    window(B, bl, 0.08, bd - 0.08, 0.72, 2.38, depth=0.06, cols=1, glass='glass0', head=None, sill=None, register=False)
    window(B, br, 0.08, bd - 0.08, 0.72, 2.38, depth=0.06, cols=1, glass='glass0', head=None, sill=None, register=False)
    B.add(fbox((by0 - 0.06, -bd - 0.07, 2.6), (by1 + 0.06, 0.0, 2.72), 0.03, 'trim', back=True))
    B.add(fbox((by0 - 0.02, -bd - 0.03, 0.0), (by1 + 0.02, 0.0, 0.5), 0.03, 'stone', back=True))
    pot(B, (by1 + 0.35, -0.45, 0), 0.2, 0.32, 'pot2', 'bush', seed=4)
    pot(B, (-4.55, -0.4, 0), 0.17, 0.3, 'pot', 'flowers', seed=5)
    for kk, (a, b) in enumerate(wins_u):
        window(B, F, a, b, *wz, cols=2, head=None, casing=True, planter=('accent', None, 'pot')[kk], glass=('glass1', 'glass2', 'glass0')[kk], seed=12 + kk)
    ac_unit(B, F, -1.65, gf + 0.55, 0.0, w=0.74, h=0.52, d=0.3)
    window(B, Rt, 2.6, 3.8, 0.95, 2.15, cols=2, glass='glass2', seed=15, cheap=True)
    window(B, Rt, 3.0, 4.0, 3.75, 4.85, cols=2, head=None, casing=True, glass='glass1', seed=16)
    meter_box(B, Rt, 5.6, 0.9)
    vent(B, Lf, -3.5, 2.0)
    B.feat('front', 'patch', a=4.6, b=1.6, w=0.22, h=0.14)
    return top + 0.11


# ---------------------------------------------------------------- Bungalow
def bungalow(B):
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    ph = 0.35; v0 = ph - 0.04
    rib = (0.25, 0.04)
    win = (-2.5, -1.4, 1.1, 2.25)
    door_o = (0.15, 1.1, 0.2, 2.3)
    t = 0.12
    y0, y1 = -0.42, D + 0.3
    depth = 0.04
    s = (H + RH - depth - (H + t)) / y1
    hb = H + s * D
    wall(B, F, -W / 2, W / 2, H, [win, door_o], v0, 'rib', rib=rib)
    wall(B, Rt, 0, D, [(0, H), (D, hb)], [(2.4, 3.3, 1.2, 2.2)], v0, 'rib', rib=rib)
    wall(B, Lf, -D, 0, [(-D, hb), (0, H)], [], v0, 'rib', rib=rib)
    wall(B, Bk, -W / 2, W / 2, hb, [], v0, 'flat')
    for x, y in ((W / 2, 0), (-W / 2, 0), (W / 2, D), (-W / 2, D)):
        corner_board(B, x, y, v0, (H if y == 0 else hb) - 0.02, s=0.07, mat='trimw')
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.06, mat='conc', closed=closed)
    top = shed(B, -W / 2 - 0.28, W / 2 + 0.28, y0, y1, H + t + s * y0, H + t + s * y1, t=t, pitch=0.26, depth=depth)
    eave_gutter(B, [(-W / 2 - 0.3, y0), (W / 2 + 0.3, y0)], H + t + s * y0 - t - 0.04)
    downpipe(B, [(-W / 2 - 0.15, y0 - 0.07, H - 0.1), (-W / 2 - 0.15, y0 - 0.07, H - 0.25), (-W / 2 - 0.075, 0.25, H - 0.6),
                 (-W / 2 - 0.075, 0.25, 0.32), (-W / 2 - 0.2, 0.25, 0.12)], brackets=[(-W / 2 - 0.075, 0.25, z) for z in (0.9, 2.3)])
    sx, sy = 2.1, 3.2
    zr = H + t + s * sy
    B.add(tube([(sx, sy, zr - 0.2), (sx, sy, zr + 1.1)], 0.075, 'galvw', 8))
    cp, _ = lathe([(0.0, 0.0), (0.2, 0.0), (0.0, 0.16)], 8, 'galvw')
    xform(cp, T(sx, sy, zr + 1.18)); B.add(cp)
    B.add(tube([(sx, sy, zr + 1.08), (sx, sy, zr + 1.2)], 0.03, 'galvw', 4))
    B.attach.append(('Chimney', (sx, sy, round(zr + 1.5, 3))))
    window(B, F, *win, cols=2, head=None, casing=(0.1, 0.06), planter='woodc', glass='glass1', seed=21)
    shed(B, win[0] - 0.22, win[1] + 0.22, -0.5, 0.02, win[3] + 0.32, win[3] + 0.45, t=0.04, pitch=0.18, depth=0.025, fascia_mat='accentw')
    knee_brackets(B, F, (win[0] - 0.12, win[1] + 0.04), win[3] + 0.3, 0.48, 'accentw', drop=0.3, t=0.06)
    door(B, F, *door_o, glass=0.3, panels=((1, 2),), casing=True, name='Door')
    steps(B, F, door_o[0] - 0.15, door_o[1] + 0.15, [0.2], tread=0.45)
    shed(B, door_o[0] - 0.35, door_o[1] + 0.35, -0.9, 0.02, 2.62, 2.8, t=0.05, pitch=0.18, depth=0.025, fascia_mat='accentw')
    knee_brackets(B, F, (door_o[0] - 0.2, door_o[1] + 0.12), 2.6, 0.88, 'accentw', drop=0.5, t=0.07)
    B.feat('front', 'ao', a0=door_o[0] - 0.35, a1=door_o[1] + 0.35, b=2.58, length=0.5, k=0.5)
    bulkhead(B, F, 1.55, 2.0)
    meter_box(B, F, -0.55, 1.25, w=0.32, h=0.44)
    hose_reel(B, F, -0.95, 0.75)
    bench(B, F, 1.85, 3.25)
    ac_unit(B, F, 2.55, 2.0, 0.0, w=0.74, h=0.5, d=0.28)
    pot(B, (1.55, -0.45, 0), 0.18, 0.3, 'pot', 'flowers', seed=22)
    pot(B, (3.15, -0.6, 0), 0.16, 0.28, 'pot2', 'grass', seed=23)
    pot(B, (-0.3, -0.35, 0), 0.15, 0.24, 'pot3', 'bush', seed=24)
    gas_bottle(B, (-3.15, -0.3, 0.0))
    window(B, Rt, 2.4, 3.3, 1.2, 2.2, cols=1, head=None, casing=(0.09, 0.05), glass='glass0', seed=25, cheap=True)
    vent(B, Lf, -2.5, 2.3, 0.24)
    B.style['fix_rows'] = [0.5, 1.6, 2.9]
    return top


# ---------------------------------------------------------------- shops
def shop_shell(B, ground_open, door_o=None, side_wins=((3.0, 4.2),)):
    """The common shell of the two shops: render walls, cornice, parapet, coping, side windows."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    pp = 0.6
    ph = 0.4; v0 = ph - 0.05
    ops = [ground_open] + ([door_o] if door_o else []) + list(B.upper)
    wall(B, F, -W / 2 + c, W / 2 - c, H + pp, ops, v0)
    sw = [(a, b, 4.9, 6.2) for a, b in side_wins]
    wall(B, Rt, c, D - c, H + pp, sw + [(5.2, 6.4, 1.0, 2.3)], v0)
    wall(B, Lf, -D + c, -c, H + pp, [(-b, -a, 4.9, 6.2) for a, b in side_wins], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H + pp, [], v0)
    box_shell_corners(B, v0, H + pp, c)
    gaps = [(ground_open[0], ground_open[1])] + ([(door_o[0], door_o[1])] if door_o else [])
    for path, closed in ring_path(B, gaps=gaps):
        plinth(B, path, ph, closed=closed)
    cornice(B, u_path(B), H - 0.42, steps=((0.05, 0.1), (0.11, 0.1), (0.2, 0.16)))
    string_course(B, u_path(B), 4.62, 4.78, out=0.06)
    flat_top(B, H, pp)
    B.add(cbox2((1.8, 5.2, H), (2.8, 6.0, H + 0.7), 0.04, 'whitep'))
    fr = MB()
    fr.face([(1.95, 5.199, H + 0.08), (2.65, 5.199, H + 0.08), (2.65, 5.199, H + 0.62), (1.95, 5.199, H + 0.62)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('ac', 0.3 + (co.x - 1.95) / 0.7 * 0.7, (co.z - H - 0.08) / 0.54))
    B.add(fr.bm())
    B.add(cbox2((-1.2, 6.2, H), (0.0, 7.2, H + 0.5), 0.05, 'galv'))
    for a, b in side_wins:
        window(B, Rt, a, b, 4.9, 6.2, cols=2, glass='glass2', seed=31, cheap=True)
        window(B, Lf, -b, -a, 4.9, 6.2, cols=2, glass='glass0', seed=32, cheap=True, register=False)
    window(B, Rt, 5.2, 6.4, 1.0, 2.3, cols=2, glass='glass0', seed=33, cheap=True, bars=3)
    return F, Rt, Bk, Lf


def shop_fruit(B):
    W, H, D = B.W, B.H, B.D
    opn = (-3.65, 2.0, 0.0, 3.0)
    door_o = (2.45, 3.6, 0.14, 2.5)
    B.upper = [(-3.3, -1.9, 4.95, 6.35), (-0.7, 0.7, 4.95, 6.35), (1.9, 3.3, 4.95, 6.35)]
    F, Rt, Bk, Lf = shop_shell(B, opn, door_o)
    room = 2.3
    shop_room(B, opn[0], opn[1], 0.0, opn[3], room)
    for x0, x1 in ((-W / 2, opn[0]), (opn[1], door_o[0]), (door_o[1], W / 2)):
        put(B, F, fbox((x0 + 0.02, 0.0, 0.0), (x1 - 0.02, 3.05, 0.07), 0.02, 'stone'))
    put(B, F, fbox((opn[0] - 0.1, 2.96, 0.0), (opn[1] + 0.1, 3.18, 0.08), 0.02, 'trim'))
    kinds = ['orange', 'apple', 'lemon', 'green', 'tomato', 'plum']
    for row in range(3):
        z = 0.55 + row * 0.62
        B.add(fbox((opn[0] + 0.2, room - 0.5, z - 0.05), (opn[1] - 0.2, room, z), 0.01, 'woodc', back=True))
        for i in range(8):
            x = opn[0] + 0.55 + i * 0.66
            if x > opn[1] - 0.4: break
            crate(B, (x, room - 0.26, z), (0.56, 0.36, 0.18), kinds[(i + row * 2) % 6], tilt=0.3)
    pendant(B, -0.8, 1.0, opn[3], 0.55)
    rng = np.random.default_rng(9)
    for sx0, sx1, off in ((-3.5, -0.95, 0), (-0.75, 1.85, 3)):
        for tier in range(3):
            zt = 0.42 + 0.26 * tier
            ya = -1.2 + 0.42 * tier; yb = ya + 0.42
            B.add(box((sx0, ya, zt - 0.05), (sx1, yb, zt), 'woodc', skip=('-z',)))
            B.add(box((sx0, ya - 0.01, zt - 0.26 if tier else 0.0), (sx1, ya + 0.02, zt - 0.05), 'woodd', skip=('+z', '-z')))
            n = int((sx1 - sx0) / 0.6)
            for i in range(n):
                x = sx0 + (sx1 - sx0) * (i + 0.5) / n
                crate(B, (x, (ya + yb) / 2, zt), (0.56, 0.38, 0.17), kinds[(i + tier * 2 + off) % 6], tilt=0.22, yaw=rng.uniform(-0.05, 0.05))
        for x in (sx0 + 0.03, sx1 - 0.08):
            B.add(box((x, -1.2, 0.0), (x + 0.05, -1.15, 0.42), 'woodd'))
    for i, (x, y) in enumerate(((-3.3, -1.55), (-2.95, -1.62), (-3.12, -1.45))):
        melon(B, (x, y, 0.15 if i < 2 else 0.4), 0.18, seed=i)
    bk, _ = lathe([(0.0, 0.0), (0.24, 0.0), (0.3, 0.26), (0.32, 0.28), (0.29, 0.28), (0.27, 0.12), (0.0, 0.12)], 10,
                  ['woodc', 'woodc', 'woodc', 'woodc', 'woodc', 'woodd'])
    xform(bk, T(1.75, -1.45, 0.0)); B.add(bk)
    crate(B, (1.75, -1.45, 0.02), (0.38, 0.38, 0.2), 'orange', mound=0.12, mat='woodc')
    awning(B, F, opn[0] - 0.12, opn[1] + 0.12, 3.25, 1.45, 0.6, 9, 'accent', 'cream', valance=0.24)
    z_panel = sign_board(B, F, -W / 2 + 0.08, W / 2 - 0.08, 3.55, 4.5)
    zc = 4.025
    icons = [(-2.8, 'apple'), (-1.4, 'pear'), (0.0, 'orange'), (1.4, 'carrot'), (2.8, 'cherry')]
    for x, kind in icons:
        if kind == 'apple':
            shape(B, F, apple_pts(0.26), x, zc - 0.02, z_panel, 0.05, 'ic1')
            shape(B, F, [(-0.012, 0), (0.012, 0), (0.02, 0.16), (-0.004, 0.16)], x, zc + 0.17, z_panel, 0.04, 'ic5')
            shape(B, F, circle_pts(0.1, 8, sx=1.0, sy=0.45), x + 0.11, zc + 0.27, z_panel, 0.045, 'ic4', rot=0.5)
            shape(B, F, circle_pts(0.06, 8, sx=0.6, sy=1.0), x - 0.1, zc + 0.06, z_panel + 0.05, 0.01, 'white', rot=-0.4)
        elif kind == 'pear':
            shape(B, F, circle_pts(0.21, 14), x, zc - 0.08, z_panel, 0.05, 'ic4')
            shape(B, F, circle_pts(0.13, 12), x + 0.02, zc + 0.12, z_panel, 0.052, 'ic4')
            shape(B, F, [(-0.012, 0), (0.012, 0), (0.03, 0.12), (0.006, 0.12)], x + 0.02, zc + 0.22, z_panel, 0.04, 'ic5')
        elif kind == 'orange':
            shape(B, F, circle_pts(0.25, 16), x, zc - 0.03, z_panel, 0.05, 'ic2')
            shape(B, F, circle_pts(0.1, 8, sx=1.0, sy=0.45), x + 0.09, zc + 0.24, z_panel, 0.045, 'ic4', rot=0.35)
            shape(B, F, circle_pts(0.05, 8), x - 0.09, zc + 0.06, z_panel + 0.05, 0.01, 'white')
        elif kind == 'carrot':
            shape(B, F, [(-0.13, 0.17), (-0.09, 0.22), (0.09, 0.22), (0.13, 0.17), (0.0, -0.32)], x, zc - 0.02, z_panel, 0.05, 'ic2', rot=0.35)
            for a in (-0.4, 0.0, 0.4):
                shape(B, F, circle_pts(0.12, 8, sx=0.35, sy=1.0), x - 0.07 + a * 0.12, zc + 0.3, z_panel, 0.04, 'ic4', rot=0.35 + a)
        else:
            for dx in (-0.1, 0.12):
                shape(B, F, circle_pts(0.11, 12), x + dx, zc - 0.13 + (0.03 if dx > 0 else 0), z_panel, 0.05, 'ic1')
            shape(B, F, [(-0.11, -0.03), (-0.09, -0.04), (0.0, 0.22), (-0.02, 0.23)], x, zc, z_panel, 0.04, 'ic5')
            shape(B, F, [(0.12, 0.0), (0.14, 0.0), (0.02, 0.23), (-0.0, 0.22)], x, zc, z_panel, 0.04, 'ic5')
            shape(B, F, circle_pts(0.1, 8, sx=1.0, sy=0.45), x + 0.09, zc + 0.25, z_panel, 0.045, 'ic4', rot=-0.3)
    door(B, F, *door_o, glass=0.62, panels=((1, 1),), glass_region='glass3', name='Door')
    B.doors.append({'name': 'Shopfront', 'center': [round((opn[0] + opn[1]) / 2, 3), 0.0, 0.0], 'size': [round(opn[1] - opn[0], 3), opn[3]], 'wall': 'front'})
    steps(B, F, door_o[0] - 0.05, door_o[1] + 0.05, [0.14], tread=0.3)
    lantern(B, F, 3.82, 2.05, name='Lamp')
    for kk, wo in enumerate(B.upper):
        window(B, F, *wo, cols=2, transom=0.72, head='key', planter=('accent' if kk != 1 else None), glass=('glass1', 'glass0', 'glass2')[kk], seed=35 + kk)
    awning(B, F, B.upper[1][0] - 0.1, B.upper[1][1] + 0.1, B.upper[1][3] + 0.28, 0.55, 0.3, 4, 'accent', 'cream', valance=0.14, arms=False)
    wall_pipe(B, 3.9, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.0, 1.2, 0.0)
    for i in range(3):
        crate(B, (W / 2 + 0.35, 1.0 + i * 0.05, 0.19 * i), (0.56, 0.38, 0.19), kinds[i + 1], mound=0.0, yaw=PI / 2 + 0.06 * i)
    return H + 0.6 + 0.11


def shop_shutter(B):
    W, H, D = B.W, B.H, B.D
    opn = (-3.6, 3.6, 0.0, 3.0)
    B.upper = [(-2.65, -1.15, 4.95, 6.45), (1.15, 2.65, 4.95, 6.45)]
    F, Rt, Bk, Lf = shop_shell(B, opn, None)
    room = 2.6
    shop_room(B, opn[0], opn[1], 0.0, opn[3], room)
    for x0, x1 in ((-W / 2, opn[0]), (opn[1], W / 2)):
        put(B, F, fbox((x0 + 0.02, 0.0, 0.0), (x1 - 0.02, 3.05, 0.07), 0.02, 'stone'))
    B.add(fbox((-2.6, 0.75, 0.0), (2.6, 1.15, 0.95), 0.02, 'woodc', back=True))
    B.add(fbox((-2.65, 0.7, 0.95), (2.65, 1.2, 1.0), 0.01, 'woodd', back=True))
    rng = np.random.default_rng(4)
    for row in range(3):
        z = 0.9 + row * 0.5
        B.add(fbox((-3.3, room - 0.45, z - 0.04), (3.3, room, z), 0.01, 'woodc', back=True))
        for i in range(9):
            x = -3.05 + i * 0.75 + rng.uniform(-0.08, 0.08)
            if row == 1 and i % 3 == 1: continue
            B.add(blob((x, room - 0.22, z + 0.08), (0.2, 0.12, 0.09), 'bread' if (i + row) % 3 else 'crust', 7, 2, row * 9 + i, 0.08, flat_bottom=0.2))
    for x in (-1.6, 1.6):
        pendant(B, x, 1.4, opn[3], 0.5)
    # the roller shutter, half raised: housing, rails, slats, bottom bar
    put(B, F, fbox((-3.78, 3.0, 0.0), (3.78, 3.42, 0.34), 0.08, 'accentp'))
    for x in (-3.6, 3.52):
        put(B, F, fbox((x, 0.0, 0.0), (x + 0.08, 3.0, 0.1), 0.015, 'metald'))
    zb = 1.78
    mb = MB()
    pitch = 0.1
    zz = 3.0
    while zz - pitch > zb - 1e-6:
        a, b = zz - pitch, zz
        mb.face([(-3.52, a + 0.015, 0.05), (3.52, a + 0.015, 0.05), (3.52, b - 0.02, 0.06), (-3.52, b - 0.02, 0.06)], 'accent', (0, 0, 1))
        mb.face([(-3.52, b - 0.02, 0.06), (3.52, b - 0.02, 0.06), (3.52, b, 0.035), (-3.52, b, 0.035)], 'accent', (0, 0.6, 1), 0.9)
        mb.face([(-3.52, a, 0.035), (3.52, a, 0.035), (3.52, a + 0.015, 0.05), (-3.52, a + 0.015, 0.05)], 'accent', (0, -1, 1), 0.6)
        zz -= pitch
    put(B, F, mb.bm())
    put(B, F, fbox((-3.54, zb - 0.09, 0.02), (3.54, zb + 0.005, 0.085), 0.015, 'metald', back=True))
    for x in (-1.2, 1.2):
        put(B, F, fbox((x - 0.08, zb - 0.16, 0.06), (x + 0.08, zb - 0.1, 0.11), 0.01, 'metal'))
    B.feat('front', 'ao', a0=-3.6, a1=3.6, b=zb - 0.08, length=0.35, k=0.35)
    B.doors.append({'name': 'Shopfront', 'center': [0.0, 0.0, 0.0], 'size': [7.2, round(zb - 0.09, 3)], 'wall': 'front'})
    # the cloth banner hanging inside, under the shutter
    put(B, F, tube([(-1.75, zb - 0.05, -0.12), (1.75, zb - 0.05, -0.12)], 0.02, 'woodd', 6))
    n = 4; bw = 3.3 / n
    for i in range(n):
        x0 = -1.65 + i * bw + 0.02; x1 = x0 + bw - 0.04
        V = []
        for yy, sh in ((zb - 0.07, 0.0), (zb - 0.45, 0.012), (zb - 0.9, 0.0)):
            V += [(x0, yy, -0.11 + sh), (x1, yy, -0.11 + sh)]
        bmb, faces = bm_from(V, [[0, 1, 3, 2], [2, 3, 5, 4]], 'tex')
        bmb.normal_update()
        for f in bmb.faces:
            if f.normal.z < 0: f.normal_flip()
        uv_fn(bmb, list(bmb.faces), 'banner', lambda co, i=i, x0=x0, x1=x1: ((i + (co.x - x0) / (x1 - x0)) / n, (co.y - (zb - 0.9)) / 0.83), 0.0)
        put(B, F, bmb)
    # sign: a bakery-cafe: a steaming cup, a wheat sprig, a loaf, a cake slice, a croissant
    z_panel = sign_board(B, F, -W / 2 + 0.08, W / 2 - 0.08, 3.55, 4.5)
    zc = 4.025
    sc = 1.3

    def icon(pts, cx, cy, dz, depth, mat, rot=0.0):
        shape(B, F, [(x * sc, y * sc) for x, y in pts], cx, cy, z_panel + dz, depth, mat, rot=rot)
    cx = -2.85
    icon([(-0.2, 0.15), (0.2, 0.15), (0.17, -0.12), (0.12, -0.18), (-0.12, -0.18), (-0.17, -0.12)], cx, zc - 0.08, 0, 0.05, 'ic6')
    icon(arc_strip(0.06, 0.11, -PI / 2, PI / 2, 6), cx + 0.19 * sc, zc - 0.05, 0, 0.045, 'ic6')
    icon([(-0.28, -0.22), (0.28, -0.22), (0.25, -0.26), (-0.25, -0.26)], cx, zc - 0.05, 0, 0.04, 'ic6')
    for k, dx in enumerate((-0.09, 0.0, 0.09)):
        icon(wave_strip(dx, 0.16, 0.36, 0.022, 0.03, 6, k), cx, zc - 0.08, 0, 0.03, 'white')
    cx = -1.45
    icon([(-0.012, -0.3), (0.012, -0.3), (0.012, 0.2), (-0.012, 0.2)], cx, zc, 0, 0.03, 'ic5')
    for k in range(4):
        for sgn in (-1, 1):
            icon(circle_pts(0.05, 8, sx=0.55, sy=1.0), cx + sgn * 0.045 * sc, zc - 0.05 + k * 0.085 * sc, 0.0, 0.04, 'ic3', rot=-sgn * 0.5)
    icon(circle_pts(0.05, 8, sx=0.55, sy=1.0), cx, zc + 0.31 * sc, 0, 0.04, 'ic3')
    icon([(0.38 * math.cos(a), 0.2 * math.sin(a)) for a in np.linspace(0, 2 * PI, 16, endpoint=False)], 0.0, zc, 0, 0.06, 'bread')
    for dx in (-0.16, 0.0, 0.16):
        icon([(-0.03, -0.1), (0.0, -0.1), (0.05, 0.1), (0.02, 0.1)], dx * sc, zc, 0.06, 0.01, 'crust')
    cx = 1.45
    icon([(-0.24, -0.18), (0.24, -0.18), (0.24, 0.02), (-0.24, 0.2)], cx, zc - 0.03, 0, 0.05, 'bread')
    icon([(-0.24, -0.04), (0.24, -0.04), (0.24, 0.0), (-0.24, 0.07)], cx, zc - 0.03, 0.05, 0.01, 'cream')
    icon([(-0.24, 0.2), (0.24, 0.02), (0.24, 0.06), (-0.24, 0.25)], cx, zc - 0.03, 0, 0.055, 'fl1')
    icon(circle_pts(0.06, 10), cx - 0.15 * sc, zc + 0.27 * sc, 0, 0.06, 'ic1')
    icon(arc_strip(0.16, 0.34, 0.25 * PI, 0.75 * PI, 8), 2.85, zc - 0.28, 0, 0.06, 'bread')
    for k in range(4):
        a = 0.3 * PI + 0.4 * PI * k / 3
        icon([(0, -0.008), (0.18, -0.008), (0.18, 0.008), (0, 0.008)], 2.85 + 0.16 * sc * math.cos(a), zc - 0.28 + 0.16 * sc * math.sin(a), 0.06, 0.008, 'crust', rot=a)
    for x in (-2.0, 2.0):
        gooseneck(B, F, x, 4.65, reach=0.5, rise=0.3)
    # upper floor: windows with Juliet rails and pots, an AC unit between
    for kk, wo in enumerate(B.upper):
        window(B, F, *wo, cols=2, transom=0.75, head='hood', glass=('glass1', 'glass2')[kk], seed=41 + kk)
        x0, x1, z0, z1 = wo
        put(B, F, tube([(x0 - 0.05, z0 + 0.62, 0.22), (x1 + 0.05, z0 + 0.62, 0.22)], 0.022, 'metald', 6))
        for xx in np.linspace(x0, x1, 6):
            put(B, F, tube([(xx, z0 - 0.02, 0.22), (xx, z0 + 0.62, 0.22)], 0.012, 'metald', 4))
        for j in range(2):
            pp = F.P(x0 + 0.35 + j * 0.75, z0 + 0.02, 0.0)
            pot(B, (pp.x, pp.y - 0.07, pp.z), 0.11, 0.18, ('pot', 'pot2')[j], ('flowers', 'bush')[(j + kk) % 2], seed=50 + kk * 2 + j, scale=0.9)
    ac_unit(B, F, 0.0, 5.0, 0.0, w=0.8, h=0.55, d=0.3)
    wall_pipe(B, -3.9, -0.08, H + 0.1)
    # the bakery's oven flue on the roof
    B.add(tube([(-2.6, 5.2, H - 0.1), (-2.6, 5.2, H + 1.9)], 0.13, 'galvw', 8))
    for z in (H + 0.6, H + 1.3):
        B.add(tube([(-2.6, 5.2, z - 0.03), (-2.6, 5.2, z + 0.03)], 0.15, 'galvw', 8))
    cp, _ = lathe([(0.0, -0.05), (0.32, 0.0), (0.0, 0.2)], 8, 'galvw')
    xform(cp, T(-2.6, 5.2, H + 2.05)); B.add(cp)
    B.add(tube([(-2.6, 5.2, H + 1.9), (-2.6, 5.2, H + 2.02)], 0.04, 'galvw', 4))
    B.attach.append(('Chimney', (-2.6, 5.2, round(H + 2.4, 3))))
    meter_box(B, Rt, 3.0, 1.0)
    meter_box(B, Rt, 3.5, 1.0)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- Apartment
def apartment(B):
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    pp = 0.6
    ph = 0.5; v0 = ph - 0.05
    fh = 2.8
    ground = [(-5.4, -3.2, 0.85, 2.25), (3.2, 5.4, 0.85, 2.25)]
    door_o = (-1.0, 1.0, 0.36, 2.55)
    bal = {}
    ops = list(ground) + [door_o]
    for k in range(1, 5):
        zk = fh * k
        for s in (-1, 1):
            xd = (-5.3, -3.4) if s < 0 else (3.4, 5.3)
            xw = (-2.75, -1.25) if s < 0 else (1.25, 2.75)
            bal[(k, s)] = (xd, xw)
            ops += [(xd[0], xd[1], zk + 0.06, zk + 2.2), (xw[0], xw[1], zk + 0.95, zk + 2.2)]
    wall(B, F, -W / 2 + c, W / 2 - c, H + pp, ops, v0)
    sops = [(4.4, 5.6, fh * k + 0.95, fh * k + 2.2) for k in range(5)]
    wall(B, Rt, c, D - c, H + pp, sops, v0)
    wall(B, Lf, -D + c, -c, H + pp, [(-b, -a, z0, z1) for a, b, z0, z1 in sops], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H + pp, [], v0)
    box_shell_corners(B, v0, H + pp, c)
    for path, closed in ring_path(B, gaps=[(door_o[0] - 0.2, door_o[1] + 0.2)]):
        plinth(B, path, ph, closed=closed)
    for k in range(1, 5):
        for sgn in (-1, 1):
            path = [(-W / 2, D), (-W / 2, 0.0)] if sgn < 0 else [(W / 2, 0.0), (W / 2, D)]
            string_course(B, path, fh * k - 0.1, fh * k + 0.06, out=0.05)
    string_course(B, u_path(B), H - 0.2, H, out=0.07)
    flat_top(B, H, pp)
    for kk, wo in enumerate(ground):
        window(B, F, *wo, cols=3, transom=0.7, bars=5, glass=('glass2', 'glass1')[kk], seed=61 + kk, cheap=True)
    door(B, F, *door_o, double=True, glass=0.78, panels=((1, 1),), glass_region='glass3', name='Door')
    steps(B, F, door_o[0] - 0.25, door_o[1] + 0.25, [0.36, 0.18], tread=0.32)
    put(B, F, fbox((-1.75, 2.8, 0.0), (1.75, 3.0, 1.35), 0.04, 'conc'))
    put(B, F, fbox((-1.77, 2.76, 1.3), (1.77, 3.03, 1.42), 0.02, 'accentp'))
    lp, _ = lathe([(0.0, -0.04), (0.16, -0.04), (0.17, 0.0), (0.0, 0.0)], 10, ['lamp', 'white', 'white'])
    xform(lp, T(0, -0.7, 2.79)); B.add(lp)
    B.lamps.append({'name': 'Lamp', 'center': [0.0, -0.7, 2.75]})
    B.feat('front', 'ao', a0=-1.75, a1=1.75, b=2.78, length=0.6, k=0.6)
    put(B, F, fbox((1.45, 0.95, 0.0), (2.35, 1.75, 0.09), 0.015, 'metal'))
    mb = MB()
    for i in range(3):
        for j in range(2):
            x0 = 1.52 + i * 0.27; y0 = 1.05 + j * 0.34
            bar(mb, x0, y0, x0 + 0.22, y0 + 0.28, 0.09, 0.1, 'galvw')
            bar(mb, x0 + 0.04, y0 + 0.2, x0 + 0.18, y0 + 0.22, 0.1, 0.105, 'black')
    put(B, F, mb.bm())
    put(B, F, cbox2((-1.45, 1.2, 0.0), (-1.25, 1.5, 0.06), 0.015, 'metald'))
    for x in (-2.15, 2.15):
        B.add(fbox((x - 0.4, -0.85, 0.0), (x + 0.4, -0.05, 0.5), 0.03, 'conc', back=True))
        for j in range(2):
            B.add(blob((x - 0.14 + 0.28 * j, -0.45, 0.64), (0.28, 0.26, 0.24), ['leaf', 'leafl'][j], 7, 2, 70 + j + int(x)))
    put(B, F, fbox((-0.15, fh - 0.18, 0.0), (0.15, H - 0.05, 1.2), 0.03, 'wall'))
    plan = {(1, -1): 'laundry', (1, 1): 'tall', (2, -1): 'planter', (2, 1): 'laundry', (3, -1): 'tall', (3, 1): 'planter',
            (4, -1): 'laundry', (4, 1): 'planter'}
    acs = {(1, 1), (2, -1), (3, 1), (4, -1)}
    for (k, s), (xd, xw) in bal.items():
        zk = fh * k
        xa, xb = (-5.75, -0.15) if s < 0 else (0.15, 5.75)
        put(B, F, fbox((xa, zk - 0.18, 0.0), (xb, zk + 0.05, 1.15), 0.03, 'conc'))
        put(B, F, fbox((xa, zk + 0.05, 1.03), (xb, zk + 1.0, 1.13), 0.025, 'accentp'))
        xe = xa if s < 0 else xb - 0.1
        put(B, F, box((xe, zk + 0.05, 0.0), (xe + 0.1, zk + 1.0, 1.03), 'accentp', skip=('-z',)))
        put(B, F, tube([(xa + 0.05, zk + 1.12, 1.08), (xb - 0.05, zk + 1.12, 1.08)], 0.026, 'metald', 5))
        for xx in (xa + 0.12, xb - 0.12):
            put(B, F, tube([(xx, zk + 1.0, 1.08), (xx, zk + 1.12, 1.08)], 0.015, 'metald', 4, caps=False))
        B.feat('front', 'ao', a0=xa, a1=xb, b=zk - 0.18, length=0.5, k=0.45)
        window(B, F, xd[0], xd[1], zk + 0.06, zk + 2.2, cols=2, sill=None, head=None, depth=0.12, glass=('glass1', 'glass0', 'glass2')[(k + s) % 3], seed=80 + k * 2 + s, cheap=True)
        window(B, F, xw[0], xw[1], zk + 0.95, zk + 2.2, cols=2, head='lintel', glass=('glass2', 'glass1')[(k + s) % 2], seed=90 + k * 2 + s, cheap=True)
        what = plan[(k, s)]
        if what == 'laundry':
            lx0, lx1 = (xa + 0.35, xa + 3.0) if s < 0 else (xb - 3.0, xb - 0.35)
            for xx in (lx0, lx1):
                put(B, F, tube([(xx, zk + 2.62, 0.75), (xx, zk + 2.05, 0.75)], 0.012, 'metal', 4))
            laundry(B, F, lx0, lx1, zk + 2.05, 0.75, seed=k * 3 + s, n=5)
        elif what == 'tall':
            px = (xa + 0.6) if s < 0 else (xb - 0.6)
            pot(B, (px, -0.55, zk + 0.05), 0.24, 0.42, 'pot', 'tall', seed=k * 5 + s, scale=1.35)
            pot(B, (px + 0.6 * -s, -0.7, zk + 0.05), 0.2, 0.36, 'pot2', 'bush', seed=k * 7 + s, scale=1.4)
        else:
            fx0, fx1 = (xa + 0.4, xa + 2.0) if s < 0 else (xb - 2.0, xb - 0.4)
            flower_box(B, F, fx0, fx1, zk + 0.93, 'pot', seed=k * 11 + s, z0=1.13, depth=0.22, h=0.2, density=0.34, nfl=1)
            for j in range(2):
                B.add(blob(F.P(fx0 + 0.45 + j * 0.7, zk + 0.68, 1.27), (0.1, 0.22, 0.06), 'leafd', 5, 2, k * 13 + j))
        if (k, s) in acs:
            ax = -0.72 if s < 0 else 0.72
            ac_unit(B, F, ax, zk + 1.35, 0.0, w=0.72, h=0.5, d=0.28)
    for i, (a, b, z0, z1) in enumerate(sops):
        window(B, Rt, a, b, z0, z1, cols=1, glass=('glass0', 'glass2', 'glass1')[i % 3], seed=140 + i, cheap=True)
        window(B, Lf, -b, -a, z0, z1, cols=1, glass=('glass2', 'glass0')[i % 2], seed=150 + i, cheap=True, register=False)
    tank(B, 3.4, 3.2, H + 0.02)
    sx0, sx1, sy0, sy1 = -4.9, -2.4, 5.6, 8.0
    B.add(cbox2((sx0, sy0, H), (sx1, sy1, H + 2.4), 0.04, 'wallw'))
    B.add(fbox((sx0 - 0.08, sy0 - 0.08, H + 2.4), (sx1 + 0.08, sy1 + 0.08, H + 2.55), 0.03, 'trim', back=True))
    sf = WF((0, sy0, H), (1, 0, 0), 'front')
    put(B, sf, fbox((-4.1, 0.0, 0.0), (-3.2, 2.05, 0.04), 0.02, 'accentp'))
    dish(B, (-2.55, sy0 + 0.6, H + 2.75), d=(0.2, -1, 0.5))
    antenna(B, -1.0, 7.4, H, 2.0)
    wall_pipe(B, W / 2 + 0.08, 0.35, H + 0.15, out=(1, 0))
    ac_unit(B, Rt, 5.3, fh * 2 + 0.6, 0.0)
    ac_unit(B, Lf, -5.0, fh * 3 + 0.6, 0.0)
    return H + pp + 0.11


# ---------------------------------------------------------------- Warehouse
def warehouse(B):
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    ph = 0.6; v0 = ph - 0.04
    rib = (0.3, 0.05)
    rd = (-4.2, -0.2, 0.0, 3.8)
    od = (1.6, 2.6, 0.15, 2.35)
    ow = (3.15, 4.65, 1.2, 2.3)
    t = 0.14
    y0, y1 = -0.45, D + 0.3
    depth = 0.05
    s = (H + RH - depth - (H + t)) / y1
    hb = H + s * D
    wall(B, F, -W / 2, W / 2, H, [rd, od, ow], v0, 'rib', rib=rib)
    wall(B, Rt, 0, D, [(0, H), (D, hb)], [(2.0, 6.0, 3.4, 4.1)], v0, 'rib', rib=rib)
    wall(B, Lf, -D, 0, [(-D, hb), (0, H)], [], v0, 'rib', rib=rib)
    wall(B, Bk, -W / 2, W / 2, hb, [], v0, 'flat')
    for x, y in ((W / 2, 0), (-W / 2, 0), (W / 2, D), (-W / 2, D)):
        corner_board(B, x, y, v0, (H if y == 0 else hb) - 0.02, s=0.08, mat='galvw')
    for path, closed in ring_path(B, gaps=[(rd[0], rd[1]), (od[0], od[1])]):
        plinth(B, path, ph, out=0.07, mat='conc', closed=closed)
    top = shed(B, -W / 2 - 0.3, W / 2 + 0.3, y0, y1, H + t + s * y0, H + t + s * y1, t=t, pitch=0.32, depth=depth)
    eave_gutter(B, [(-W / 2 - 0.32, y0), (W / 2 + 0.32, y0)], H + t + s * y0 - t - 0.04, size=0.15)
    downpipe(B, [(W / 2 + 0.15, y0 - 0.08, H - 0.1), (W / 2 + 0.15, y0 - 0.08, H - 0.25), (W / 2 + 0.08, 0.25, H - 0.6),
                 (W / 2 + 0.08, 0.25, 0.32), (W / 2 + 0.2, 0.25, 0.12)], brackets=[(W / 2 + 0.08, 0.25, z) for z in (1.0, 2.8, 4.3)])
    vx, vy = -2.5, 5.0
    zr = H + t + s * vy
    vb, _ = lathe([(0.2, -0.1), (0.2, 0.25), (0.3, 0.3), (0.34, 0.45), (0.3, 0.62), (0.15, 0.7), (0.0, 0.72)], 10, 'galvw')
    xform(vb, T(vx, vy, zr)); B.add(vb)
    # roller door: housing, rails, slats, bottom rail
    put(B, F, fbox((rd[0] - 0.2, rd[3], 0.0), (rd[1] + 0.2, rd[3] + 0.5, 0.42), 0.1, 'galv'))
    for x in (rd[0] - 0.12, rd[1]):
        put(B, F, fbox((x, 0.0, 0.0), (x + 0.12, rd[3], 0.14), 0.02, 'metald'))
    mb = MB()
    pitch = 0.12
    zz = rd[3]
    while zz - pitch > 0.02:
        a, b = zz - pitch, zz
        mb.face([(rd[0], a + 0.02, 0.06), (rd[1], a + 0.02, 0.06), (rd[1], b - 0.025, 0.075), (rd[0], b - 0.025, 0.075)], 'accent', (0, 0, 1))
        mb.face([(rd[0], b - 0.025, 0.075), (rd[1], b - 0.025, 0.075), (rd[1], b, 0.045), (rd[0], b, 0.045)], 'accent', (0, 0.6, 1), 0.9)
        mb.face([(rd[0], a, 0.045), (rd[1], a, 0.045), (rd[1], a + 0.02, 0.06), (rd[0], a + 0.02, 0.06)], 'accent', (0, -1, 1), 0.6)
        zz -= pitch
    mb.face([(rd[0], 0.0, 0.045), (rd[1], 0.0, 0.045), (rd[1], zz, 0.045), (rd[0], zz, 0.045)], 'accent', (0, 0, 1))
    put(B, F, mb.bm())
    put(B, F, fbox((rd[0], 0.0, 0.03), (rd[1], 0.12, 0.1), 0.015, 'metald', back=True))
    put(B, F, fbox((-2.35, 0.55, 0.08), (-2.05, 0.62, 0.13), 0.01, 'metal'))
    B.feat('front', 'ao', a0=rd[0] - 0.2, a1=rd[1] + 0.2, b=rd[3], length=0.4, k=0.45)
    B.doors.append({'name': 'RollerDoor', 'center': [round((rd[0] + rd[1]) / 2, 3), 0.0, 0.0], 'size': [rd[1] - rd[0], rd[3]], 'wall': 'front'})
    for x in (rd[0] - 0.42, rd[1] + 0.42):
        bollard(B, (x, -0.38, 0.0))
    gooseneck(B, F, (rd[0] + rd[1]) / 2, rd[3] + 0.7, reach=0.65, rise=0.35)
    door(B, F, *od, glass=0.3, panels=((1, 2),), casing=True, name='Door')
    steps(B, F, od[0] - 0.1, od[1] + 0.1, [0.15], tread=0.4)
    shed(B, od[0] - 0.4, od[1] + 0.4, -0.85, 0.02, 2.66, 2.82, t=0.05, pitch=0.2, depth=0.028, fascia_mat='galvw')
    knee_brackets(B, F, (od[0] - 0.25, od[1] + 0.17), 2.64, 0.83, 'metald', drop=0.45, t=0.06)
    B.feat('front', 'ao', a0=od[0] - 0.4, a1=od[1] + 0.4, b=2.62, length=0.5, k=0.5)
    bulkhead(B, F, 3.0, 2.05)
    window(B, F, *ow, cols=2, head=None, casing=(0.1, 0.07), bars=4, glass='glass2', seed=101)
    z_panel = sign_board(B, F, 1.5, 4.8, 3.1, 4.0, out=0.16, panel='creamp', bw=0.08)
    shape(B, F, [(-0.28, -0.24), (0.28, -0.24), (0.28, 0.2), (-0.28, 0.2)], 2.3, 3.53, z_panel, 0.04, 'ic5')
    shape(B, F, [(-0.06, -0.24), (0.06, -0.24), (0.06, 0.2), (-0.06, 0.2)], 2.3, 3.53, z_panel + 0.04, 0.01, 'ic3')
    shape(B, F, [(-0.32, 0.2), (0.32, 0.2), (0.24, 0.3), (-0.24, 0.3)], 2.3, 3.53, z_panel, 0.045, 'ic5')
    for k_, x in enumerate((3.25, 3.75, 4.25)):
        shape(B, F, [(-0.17, -0.06), (0.07, -0.06), (0.17, 0.0), (0.07, 0.06), (-0.17, 0.06)], x, 3.53, z_panel, 0.04, ('ic6', 'ic2', 'ic6')[k_])
    pallet(B, 3.4, -1.2, 0.0)
    pallet(B, 3.42, -1.18, 0.135)
    sack(B, (3.75, -0.8, 0.27))
    sack(B, (4.15, -0.85, 0.27), 0.9, 'woodc')
    crate(B, (5.0, -0.6, 0.0), (0.6, 0.5, 0.45), 'green', mound=0.0, mat='wood')
    put(B, F, fbox((0.55, 0.9, 0.0), (0.95, 1.55, 0.18), 0.02, 'red'))
    put(B, F, box((0.62, 1.1, 0.18), (0.88, 1.45, 0.19), 'glass', skip=('-z',)))
    hose_reel(B, F, 5.1, 1.3)
    window(B, Rt, 2.0, 6.0, 3.4, 4.1, cols=4, head=None, sill=None, casing=(0.08, 0.06), glass='glass0', seed=102, cheap=True)
    vent(B, Lf, -4.0, 4.0, 0.4)
    B.style['fix_rows'] = [0.62, 2.2, 3.9, 5.4]
    return top


# ---------------------------------------------------------------- School
def school(B):
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.06
    pp = 0.6
    ph = 0.9; v0 = ph - 0.05
    bx, bd = 3.6, 0.45
    bh = H + 1.1
    floors = [(1.1, 2.95), (4.2, 6.05), (7.3, 9.15)]
    wing_x = [5.2, 7.8, 10.4, 13.0]
    ww = 1.9

    def wins(sgn):
        return [(sgn * x - ww / 2, sgn * x + ww / 2, z0, z1) for x in wing_x for z0, z1 in floors]
    wl, wr = wins(-1), wins(1)
    wall(B, F, -W / 2 + c, -bx, H + pp, wl, v0)
    wall(B, F, bx, W / 2 - c, H + pp, wr, v0)
    bf = WF((0, -bd, 0), (1, 0, 0), 'front')
    bayw = [(-1.75 - 0.75, -1.75 + 0.75, z0, z1) for z0, z1 in floors[1:]] + [(1.75 - 0.75, 1.75 + 0.75, z0, z1) for z0, z1 in floors[1:]]
    door_o = (-1.2, 1.2, 0.75, 3.0)
    wall(B, bf, -bx + c, bx - c, bh, bayw + [door_o], v0)
    wall(B, WF((-bx, 0, 0), (0, -1, 0), 'left'), 0, bd - c, bh, [], v0)
    wall(B, WF((bx, -bd, 0), (0, 1, 0), 'right'), c, bd, bh, [], v0)
    corner(B, (-bx, -bd + c), (-bx + c, -bd), v0, bh)
    corner(B, (bx - c, -bd), (bx, -bd + c), v0, bh)
    sw = [(y - 0.8, y + 0.8, z0, z1) for y in (2.6, 6.0, 9.4) for z0, z1 in floors]
    wall(B, Rt, c, D - c, H + pp, sw, v0)
    wall(B, Lf, -D + c, -c, H + pp, [(-b, -a, z0, z1) for a, b, z0, z1 in sw], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H + pp, [], v0)
    box_shell_corners(B, v0, H + pp, c)
    outline = [(-W / 2, D), (-W / 2, 0.0), (-bx, 0.0), (-bx, -bd), (bx, -bd), (bx, 0.0), (W / 2, 0.0), (W / 2, D)]
    plinth(B, [(1.2, -bd), (bx, -bd), (bx, 0.0), (W / 2, 0.0), (W / 2, D), (-W / 2, D), (-W / 2, 0.0), (-bx, 0.0), (-bx, -bd), (-1.2, -bd)],
           ph, out=0.06, mat='stone')
    for z0, z1 in ((3.42, 3.62), (6.52, 6.72)):
        string_course(B, outline, z0, z1, out=0.07)
    cornice(B, outline, H - 0.42, steps=((0.05, 0.1), (0.11, 0.1), (0.2, 0.18)))
    main_path = [(bx, 0.0), (W / 2, 0.0), (W / 2, D), (-W / 2, D), (-W / 2, 0.0), (-bx, 0.0)]
    flat_top(B, H, pp, path=main_path, roof=False)
    B.add(box((-W / 2 + 0.22, 0.2, H - 0.1), (W / 2 - 0.22, D - 0.22, H + 0.02), 'roof', skip=('-z', '-x', '+x', '-y', '+y')))
    B.add(box((-bx + 0.22, -bd + 0.22, H - 0.1), (bx - 0.22, 0.21, H + 0.02), 'roof', skip=('-z', '-x', '+x', '-y', '+y')))
    B.feat('roof', 'flat', x0=-W / 2 + 0.22, x1=W / 2 - 0.22, y0=0.2, y1=D - 0.22)
    bay_path = [(-bx, 0.0), (-bx, -bd), (bx, -bd), (bx, 0.0)]
    B.add(band(bay_path, [(-0.22, bh), (-0.22, H)], 'wallw'), shade=0.85)
    coping(B, bay_path, bh, closed=False)
    # raised panel with an emblem over the entrance
    put(B, bf, fbox((-1.5, bh - 0.05, -0.25), (1.5, bh + 0.62, 0.04), 0.03, 'wall'))
    put(B, bf, fbox((-1.58, bh + 0.62, -0.3), (1.58, bh + 0.74, 0.09), 0.03, 'trim'))
    em, _ = lathe([(0.34, 0.0), (0.34, 0.05), (0.3, 0.07), (0.0, 0.07)], 14, ['accentw', 'accentw', 'accentw'], phase=0.5)
    xform(em, T(0, bh + 0.3, 0.04)); put(B, bf, em)
    star = []
    for i in range(10):
        r = 0.2 if i % 2 == 0 else 0.085
        a = PI / 2 + PI * i / 5
        star.append((r * math.cos(a), r * math.sin(a)))
    shape(B, bf, star, 0.0, bh + 0.3, 0.1, 0.02, 'cream')
    # clock tower
    tx, ty0, ty1, tz0, tz1 = 1.75, 1.0, 4.5, H, H + 4.2
    tf = WF((0, ty0, 0), (1, 0, 0), 'front')
    tr = WF((tx, ty0, 0), (0, 1, 0), 'right')
    tl = WF((-tx, ty1, 0), (0, -1, 0), 'left')
    tb = WF((0, ty1, 0), (-1, 0, 0), 'back')
    wall(B, tf, -tx, tx, tz1, [], tz0)
    wall(B, tr, 0, ty1 - ty0, tz1, [], tz0)
    wall(B, tl, 0, ty1 - ty0, tz1, [], tz0)
    wall(B, tb, -tx, tx, tz1, [], tz0)
    for x, y in ((tx, ty0), (-tx, ty0), (tx, ty1), (-tx, ty1)):
        corner_board(B, x, y, tz0, tz1, s=0.14, mat='trim', r=0.03)
    tring = [(-tx, ty0), (tx, ty0), (tx, ty1), (-tx, ty1)]
    cornice(B, tring, tz1 - 0.2, steps=((0.06, 0.08), (0.14, 0.08), (0.22, 0.12)), closed=True)
    string_course(B, tring, tz0 + 1.6, tz0 + 1.75, out=0.06, closed=True)
    e = 0.32
    zr = tz1 + 0.08
    ap = Vector((0, (ty0 + ty1) / 2, zr + 1.45))
    q = [Vector((-tx - e, ty0 - e, zr)), Vector((tx + e, ty0 - e, zr)), Vector((tx + e, ty1 + e, zr)), Vector((-tx - e, ty1 + e, zr))]
    mb = MB()
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        nrm = (b - a).cross(ap - a)
        mb.face([a, b, ap], 'roof', tuple(nrm))
        mb.face([a + Vector((0, 0, -0.12)), b + Vector((0, 0, -0.12)), b, a], 'roofw', tuple((b - a).cross(Vector((0, 0, 1)))), 0.75)
    mb.face([q[3] + Vector((0, 0, -0.12)), q[2] + Vector((0, 0, -0.12)), q[1] + Vector((0, 0, -0.12)), q[0] + Vector((0, 0, -0.12))], 'soffit', (0, 0, -1), 0.8)
    B.add(mb.bm())
    fn, _ = lathe([(0.12, 0.0), (0.06, 0.1), (0.05, 0.3), (0.1, 0.36), (0.0, 0.5)], 8, 'brass')
    xform(fn, T(ap)); B.add(fn)
    B.add(tube([ap + Vector((0, 0, 0.45)), ap + Vector((0, 0, 1.1))], 0.018, 'black', 4))
    arrow = [(-0.42, -0.02), (0.3, -0.02), (0.3, -0.07), (0.42, 0.0), (0.3, 0.07), (0.3, 0.02), (-0.42, 0.02), (-0.5, 0.09), (-0.5, -0.09)]
    ar = extrude_poly(arrow, 0.02, 'black', back=True)
    xform(ar, T(ap + Vector((0, 0.01, 0.95))) @ R(PI / 2, 'X') @ R(0.6, 'Y'))
    B.add(ar)
    for wf_, u in ((tf, 0.0), (tr, (ty1 - ty0) / 2)):
        cz = tz0 + 2.75
        rr = 0.92
        ring_, _ = lathe([(rr, 0.0), (rr, 0.07), (rr - 0.05, 0.11), (rr - 0.13, 0.11), (rr - 0.15, 0.06)], 16, 'trim', phase=0.5)
        xform(ring_, T(u, cz, 0)); put(B, wf_, ring_)
        face_, _ = lathe([(rr - 0.14, 0.06), (0.0, 0.06)], 16, 'tex', phase=0.5)
        uv_fn(face_, list(face_.faces), 'clock', lambda co, u=u, cz=cz: (0.5 + (co.x - u) / (2 * (rr - 0.14)), 0.5 + (co.y - cz) / (2 * (rr - 0.14))), 0.0)
        xform(face_, T(u, cz, 0)); put(B, wf_, face_)
        hand = [(-0.035, -0.08), (0.035, -0.08), (0.02, 0.42), (0.0, 0.48), (-0.02, 0.42)]
        shape(B, wf_, hand, u, cz, 0.065, 0.015, 'black', rot=0.0)
        shape(B, wf_, [(x * 1.25, y * 0.62) for x, y in hand], u, cz, 0.08, 0.015, 'black', rot=2.1)
        cap_, _ = lathe([(0.05, 0.0), (0.05, 0.02), (0.0, 0.03)], 8, 'black')
        xform(cap_, T(u, cz, 0.095)); put(B, wf_, cap_)
    B.attach.append(('Clock', tuple(round(v, 3) for v in tf.P(0, tz0 + 2.75, 0.1))))
    # entrance: steps between cheek walls, canopy on columns, double doors, lanterns, planters
    door(B, bf, *door_o, double=True, glass=0.45, panels=((1, 2),), name='Door')
    steps(B, bf, -2.45, 2.45, [0.75, 0.56, 0.37, 0.19], tread=0.32, back=0.25)
    for sg in (-1, 1):
        x0, x1 = sorted((sg * 2.55, sg * 3.0))
        put(B, bf, fbox((x0, 0.0, 0.0), (x1, 0.95, 1.45), 0.03, 'stone'))
        put(B, bf, fbox((x0 - 0.05, 0.95, 0.0), (x1 + 0.05, 1.05, 1.5), 0.02, 'trim'))
        col, _ = lathe([(0.2, 0.0), (0.2, 0.1), (0.14, 0.14), (0.13, 0.3), (0.12, 1.85), (0.15, 1.95), (0.2, 2.02), (0.2, 2.1)], 10, 'trim')
        xform(col, T(sg * 2.78, -bd - 1.25, 1.05)); B.add(col)
        pl = (sg * 3.55, -bd - 0.85)
        B.add(fbox((pl[0] - 0.35, pl[1] - 0.35, 0.0), (pl[0] + 0.35, pl[1] + 0.35, 0.55), 0.03, 'stone', back=True))
        for j in range(3):
            B.add(blob((pl[0] + 0.15 * (j - 1), pl[1] + 0.05 * j, 0.75 + 0.1 * (j == 1)), (0.26, 0.26, 0.26), ['leafd', 'leaf', 'leafl'][j], 7, 2, 120 + j + sg))
        lantern(B, bf, sg * 1.75, 2.35, out=0.22)
    put(B, bf, fbox((-3.15, 3.12, 0.0), (3.15, 3.36, 1.75), 0.04, 'conc'))
    put(B, bf, fbox((-3.17, 3.08, 1.68), (3.17, 3.4, 1.8), 0.02, 'accentp'))
    B.feat('front', 'ao', a0=-3.15, a1=3.15, b=3.1, length=0.8, k=0.6)
    for i, wo in enumerate(wl + wr):
        window(B, F, *wo, cols=2, transom=0.74, head='lintel', glass=('glass0', 'glass2', 'glass0', 'glass1')[i % 4], seed=200 + i, cheap=True)
    for i, wo in enumerate(bayw):
        window(B, bf, *wo, cols=2, transom=0.74, head='key', glass=('glass2', 'glass0')[i % 2], seed=240 + i)
    for i, (a, b, z0, z1) in enumerate(sw):
        window(B, Rt, a, b, z0, z1, cols=2, transom=0.74, glass=('glass0', 'glass2')[i % 2], seed=250 + i, cheap=True)
        window(B, Lf, -b, -a, z0, z1, cols=2, transom=0.74, glass='glass0', seed=270 + i, cheap=True, register=False)
    for x in (-bx - 0.25, bx + 0.25):
        wall_pipe(B, x, -0.08, H + 0.1)
    wall_pipe(B, W / 2 + 0.08, 0.4, H + 0.1, out=(1, 0))
    for x, y in ((-10.0, 7.0), (9.5, 8.5)):
        B.add(cbox2((x - 0.5, y - 0.4, H), (x + 0.5, y + 0.4, H + 0.75), 0.04, 'whitep'))
        fr = MB()
        fr.face([(x - 0.3, y - 0.401, H + 0.1), (x + 0.3, y - 0.401, H + 0.1), (x + 0.3, y - 0.401, H + 0.65), (x - 0.3, y - 0.401, H + 0.65)], 'tex', (0, -1, 0), 1.0,
                lambda co, x=x: reg_uv('ac', 0.3 + (co.x - x + 0.3) / 0.6 * 0.7, (co.z - H - 0.1) / 0.55))
        B.add(fr.bm())
    for i in range(4):
        x0 = 6.0 + i * 1.9
        sp = fbox((-0.85, -0.55, -0.03), (0.85, 0.55, 0.03), 0.01, 'tex', back=True)
        uv_fn(sp, faces_facing(sp, (0, 0, 1), 0.9), 'solar', lambda co: (0.5 + co.x / 1.7, 0.5 + co.y / 1.1), 0.02)
        xform(sp, T(x0, 5.0, H + 0.55) @ R(0.45, 'X')); B.add(sp)
        for sx in (-0.7, 0.7):
            B.add(box((x0 + sx - 0.03, 5.3, H), (x0 + sx + 0.03, 5.36, H + 0.62), 'metal'))
    flagpole(B, -14.6, 0.9, H + pp, 4.0)
    ac_unit(B, Rt, 11.2, 1.2, 0.0)
    return tz1 + 0.08 + 1.45 + 1.1


# ---------------------------------------------------------------- Garage
def garage(B):
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.04
    ph = 0.25; v0 = ph - 0.04
    do = (-1.3, 1.3, 0.0, 2.15)
    wall(B, F, -W / 2 + c, W / 2 - c, H, [do], v0)
    wall(B, Rt, c, D - c, H, [(2.0, 3.0, 1.2, 1.9)], v0)
    wall(B, Lf, -D + c, -c, H, [], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H, [], v0)
    box_shell_corners(B, v0, H, c)
    for path, closed in ring_path(B, gaps=[(do[0], do[1])]):
        plinth(B, path, ph, out=0.04, mat='conc', closed=closed)
    mb = MB()
    reveal(mb, *do, 0.14, bottom=False)
    put(B, F, mb.bm())
    lf = F.off(-0.1)
    wall(B, lf, do[0], do[1], do[3], [], 0.02, 'rib', mat='accent', rib=(0.17, 0.028))
    put(B, F, fbox((do[0], do[3] - 0.08, -0.1), (do[1], do[3], -0.05), 0.01, 'accentw'))
    put(B, F, fbox((-0.12, 0.85, -0.06), (0.12, 0.93, -0.02), 0.012, 'metal'))
    for x0, x1 in ((do[0] - 0.08, do[0]), (do[1], do[1] + 0.08)):
        put(B, F, fbox((x0, 0.0, 0.0), (x1, do[3], 0.04), 0.012, 'trim'))
    put(B, F, fbox((do[0] - 0.14, do[3], 0.0), (do[1] + 0.14, do[3] + 0.2, 0.06), 0.02, 'conc'))
    B.doors.append({'name': 'GarageDoor', 'center': [0.0, 0.0, 0.0], 'size': [do[1] - do[0], do[3]], 'wall': 'front'})
    rs = box((-W / 2 - 0.14, -0.16, H), (W / 2 + 0.14, D + 0.14, H + 0.26), 'roofw', skip=('-z',))
    for f in rs.faces:
        if f.normal.z > 0.9: f[L(rs)[0]] = MID['roof']
        else: f[L(rs)[2]] = 0.8
    B.add(rs)
    coping(B, [(-W / 2 - 0.14, -0.16), (W / 2 + 0.14, -0.16), (W / 2 + 0.14, D + 0.14), (-W / 2 - 0.14, D + 0.14)], H + 0.24,
           mat='trimw', inner=0.1, out=0.03, h=0.07, closed=True)
    B.feat('roof', 'flat', x0=-W / 2 - 0.14, x1=W / 2 + 0.14, y0=-0.16, y1=D + 0.14)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.01, length=0.4, k=0.5)
    eave_gutter(B, [(W / 2 + 0.16, D + 0.21), (-W / 2 - 0.16, D + 0.21)], H + 0.12, size=0.11)
    downpipe(B, [(W / 2 + 0.05, D + 0.28, H + 0.05), (W / 2 + 0.07, D - 0.3, H - 0.3), (W / 2 + 0.07, D - 0.3, 0.3), (W / 2 + 0.18, D - 0.3, 0.1)],
             brackets=[(W / 2 + 0.07, D - 0.3, 1.2)])
    lantern(B, F, 1.46, 1.9, out=0.16)
    window(B, Rt, 2.0, 3.0, 1.2, 1.9, cols=2, glass='glass0', seed=301, cheap=True)
    vent(B, Lf, -2.5, 1.6, 0.25)
    pot(B, (-1.42, -0.32, 0.0), 0.15, 0.26, 'pot', 'flowers', seed=302)
    # a climber spreading from the corner over the front pier and round onto the side
    climber(B, F, -1.42, 0.3, 2.45, 0.22, seed=31, n=10)
    climber(B, Lf, -0.45, 0.3, 2.2, 0.75, seed=37, n=12)
    return H + 0.3


# ---------------------------------------------------------------- the kit
SPECS = [
    # name, W, H (wall), D, roof, builder, palette, front-map top, styles, extra maps
    ('HouseGable', 7.0, 6.0, 7.0, 2.6, house_gable,
     pal((0.95, 0.90, 0.80), (0.46, 0.60, 0.53), (0.75, 0.41, 0.30)), 9.4, {}, {'roofb': (-3.5, -1.3, -1.0, 0.1)}),
    ('HouseLong', 10.0, 5.6, 7.0, 2.4, house_long,
     pal((0.96, 0.87, 0.66), (0.29, 0.49, 0.56), (0.42, 0.46, 0.55)), 8.9, {}, {'roofb': (-5.3, 5.3, -1.0, 0.1)}),
    ('Bungalow', 7.0, 3.4, 5.5, 1.0, bungalow,
     pal((0.62, 0.78, 0.75), (0.86, 0.48, 0.35), (0.60, 0.57, 0.54)), 6.0, {'wall': 'siding'}, {}),
    ('ShopFruit', 8.0, 7.4, 8.0, 0.0, shop_fruit,
     pal((0.95, 0.79, 0.64), (0.33, 0.56, 0.40), (0.56, 0.55, 0.54)), 8.4, {}, {}),
    ('ShopShutter', 8.0, 7.4, 8.0, 0.0, shop_shutter,
     pal((0.80, 0.85, 0.86), (0.76, 0.34, 0.28), (0.56, 0.55, 0.54)), 8.4, {}, {}),
    ('Apartment', 12.0, 14.0, 10.0, 0.0, apartment,
     pal((0.91, 0.82, 0.68), (0.80, 0.52, 0.38), (0.56, 0.55, 0.54)), 15.2, {}, {}),
    ('Warehouse', 11.0, 5.6, 8.0, 1.2, warehouse,
     pal((0.77, 0.75, 0.70), (0.89, 0.68, 0.32), (0.58, 0.61, 0.64)), 7.4, {'wall': 'metal'}, {}),
    ('School', 32.0, 10.0, 12.0, 0.0, school,
     pal((0.74, 0.42, 0.33), (0.30, 0.50, 0.58), (0.38, 0.47, 0.52), trim=(0.95, 0.91, 0.82), stone=(0.82, 0.78, 0.70)), 16.6, {'wall': 'brick'}, {}),
    ('Garage', 3.2, 2.6, 5.0, 0.0, garage,
     pal((0.86, 0.84, 0.78), (0.53, 0.64, 0.72), (0.40, 0.40, 0.42)), 3.4, {}, {}),
]


def main():
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    specs = [s for s in SPECS if not ONLY or s[0] in ONLY]
    maps = [('glass0', 128, 192), ('glass1', 128, 192), ('glass2', 128, 192), ('glass3', 128, 192),
            ('louvre', 64, 256), ('brick', 128, 384), ('banner', 256, 128), ('clock', 256, 256), ('wear', 128, 128),
            ('solar', 128, 128), ('vent', 64, 64)]
    bottom = [('wood', 256, 128), ('crate', 128, 128), ('p_orange', 128, 128), ('p_apple', 128, 128), ('p_lemon', 128, 128),
              ('p_green', 128, 128), ('p_tomato', 128, 128), ('p_plum', 128, 128), ('melon', 128, 128), ('ac', 192, 128),
              ('white', 128, 128)]
    exts = {}
    for name, W, H, D, RH, fn, p, mtop, st, extra in specs:
        fr = 44 if W <= 11 else (34 if W <= 14 else 29)
        e = {'front': (-W / 2 - 0.7, W / 2 + 0.7, 0.0, mtop), 'right': (-0.7, D + 0.7, 0.0, mtop),
             'left': (-0.7, D + 0.7, 0.0, mtop), 'roof': (-W / 2 - 0.8, W / 2 + 0.8, -1.0, D + 0.8)}
        e.update(extra)
        exts[name] = e
        for mp, (a0, a1, b0, b1) in e.items():
            ppm = {'front': fr, 'roofb': 44, 'right': 23, 'left': 15, 'roof': 25 if RH > 0 else 8}[mp]
            maps.append((name + '.' + mp, int(math.ceil((a1 - a0) * ppm)), int(math.ceil((b1 - b0) * ppm))))
    used = allocate(bottom, maps)
    print('atlas rows used', used, 'of', AT - 128 - 12)
    buildings = []
    for name, W, H, D, RH, fn, p, mtop, st, extra in specs:
        B = Bld(name, W, H, D, RH, p)
        B.maps = exts[name]; B.style = dict(st)
        B.total = fn(B)
        buildings.append(B)
    atlas = os.path.join(OUT, 'BuildingsAtlas.png')
    ATL.paint(atlas, buildings)
    mat = K.material('Buildings', atlas)
    man = K.Manifest('Buildings', 'BuildingsAtlas.png')
    for B in buildings:
        ob = to_object(B)
        K.assign(ob, mat)
        K.attach(ob, 'Front', (0, -1, 0))
        for d in B.doors: K.attach(ob, d['name'], d['center'])
        for i, w in enumerate(B.windows): K.attach(ob, 'Window.%d' % i, w['center'])
        for i, l in enumerate(B.lamps): K.attach(ob, 'Lamp.%d' % i, l['center'])
        for nm, loc in B.attach: K.attach(ob, nm, loc)
        parts = {1: s2l(B.pal['wall']), 2: s2l(B.pal['accent']), 3: s2l(B.pal['roof'])}
        co = np.array([v.co[:] for v in ob.data.vertices])
        lo, hi = co.min(0), co.max(0)
        # 'size' is the footprint the street lays out (width, depth, total height), so the game's
        # fit-to-facade scale comes out at 1; the true bounds (eaves, steps, awnings) are in
        # min / max / bounds.
        man.add(ob, parts=parts, size=[B.W, B.D, round(float(hi[2]), 3)], bounds=[round(float(x), 3) for x in hi - lo],
                footprint={'width': B.W, 'wall': B.H, 'depth': B.D, 'roof': B.RH, 'height': round(float(hi[2]), 3)},
                doors=B.doors, windows=B.windows, lamps=B.lamps)
        print(B.name, 'tris', K.tree_tris(ob))
        if B.prof: print('  ', sorted(B.prof.items(), key=lambda kv: -kv[1])[:12])
        K.export_model(ob, os.path.join(OUT, B.name + '.fbx'))
        # free the Attach.* names for the next model (one scene holds the whole kit; the FBX
        # above carries the exact names the game looks up)
        for c in ob.children: c.name = B.name + ':' + c.name
    man.save(os.path.join(OUT, 'Buildings.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Buildings.blend'))
    print('done', OUT)


main()
