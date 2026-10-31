# The town's shops and houses for the buildings kit (kit_buildings.py adds them to its SPECS), in a
# clean, lived-in everyday-town style: rendered and tiled walls, aluminium shopfronts, small tiled
# canopies, shutters, AC units, gutters, downpipes, meter boxes and signs with invented names.
#   Market street: ShopMart (a small supermarket), ShopCafe, ShopBooks, ShopFlorist, ShopNoodle and
#   ShopTall (a narrow three-storey tiled building with a closed shutter and a stair entrance),
#   ShopBoutique (another, in dark tiles, with a glass front) and ShopKonbini (a convenience store).
#   Home street: HouseLeanTo (two storeys with a corrugated lean-to), HouseFlat (a flat-roofed box with
#   a balcony) and HouseCarport (a sideways gable with a carport).
# Conventions as in kit_buildings.py: origin at the centre of the front wall's base, front toward -Y.
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_parts import _brick_uv
from kit_buildings_bits import *


# ---------------------------------------------------------------- helpers
def town_shell(B, ops, gaps=(), pp=0.6, ph=0.4, side=(), zones=(), cornice_z=None, courses=(), c=0.05, coping_mat='trim'):
    """Walls round a flat-roofed block with a parapet: front openings ops (ua, ub, va, vb), plinth
    gaps (x ranges), side windows on both sides (mirrored), front zones (ua, ub, va, vb, mat)."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0 = ph - 0.05
    wall(B, F, -W / 2 + c, W / 2 - c, H + pp, ops, v0, zones=zones)
    wall(B, Rt, c, D - c, H + pp, list(side), v0)
    wall(B, Lf, -D + c, -c, H + pp, [(-b, -a, z0, z1) for a, b, z0, z1 in side], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H + pp, [], v0)
    box_shell_corners(B, v0, H + pp, c)
    for path, closed in ring_path(B, gaps=gaps):
        plinth(B, path, ph, closed=closed)
    if cornice_z:
        cornice(B, u_path(B), cornice_z, steps=((0.04, 0.08), (0.09, 0.08), (0.15, 0.12)))
    for z0, z1 in courses:
        string_course(B, u_path(B), z0, z1, out=0.05)
    flat_top(B, H, pp, coping_mat=coping_mat)
    return F, Rt, Bk, Lf


def decal(B, wf, x0, x1, z0, z1, w, region, mat='tex'):
    """A flat panel facing out of the wall at depth w, mapped to an atlas tile (signs, posters)."""
    mb = MB()
    mb.face([(x0, z0, w), (x1, z0, w), (x1, z1, w), (x0, z1, w)], mat, (0, 0, 1), 1.0,
            lambda co: reg_uv(region, (co.x - x0) / (x1 - x0), (co.y - z0) / (z1 - z0), 0.0))
    put(B, wf, mb.bm())


def storefront(B, wf, x0, x1, z0, z1, cols, region, depth=0.2, fw=0.07, frame='alu', kick=0.2, transom=None,
               door_cols=(), posters=(), name='Shopfront'):
    """An aluminium shopfront in an opening: frame and kick rail, one continuous pane of shop
    interior behind the mullions, sliding doors (handles, meeting stiles) in door_cols, posters
    [(col, 'poster1')] stuck inside the glass."""
    mb = MB()
    reveal(mb, x0, x1, z0, z1, depth, bottom=False)
    zf = -depth + 0.07; zg = -depth + 0.025
    o = (x0, z0, x1, z1); i = (x0 + fw, z0 + kick, x1 - fw, z1 - fw)
    ring(mb, o, i, zf, zf, frame, 'front')
    ring(mb, i, i, zf, zg, frame, 'in', 0.85)
    mb.face([(i[0], i[1], zg), (i[2], i[1], zg), (i[2], i[3], zg), (i[0], i[3], zg)], 'glass', (0, 0, 1), 1.0, glass_uv(i, region))
    xs = [i[0] + (i[2] - i[0]) * k / cols for k in range(cols + 1)]
    for x in xs[1:-1]:
        bar(mb, x - 0.035, i[1], x + 0.035, i[3], zg, zf, frame)
    if transom:
        bar(mb, i[0], transom - 0.035, i[2], transom + 0.035, zg, zf + 0.004, frame)
    for c in door_cols:
        a, b = xs[c], xs[c + 1]; m = (a + b) / 2
        bar(mb, m - 0.03, i[1], m + 0.03, (transom or i[3]) - 0.035, zg, zf + 0.01, frame)
        for x in (m - 0.12, m + 0.12):
            bar(mb, x - 0.018, z0 + 0.85, x + 0.018, z0 + 1.25, zf + 0.01, zf + 0.04, 'alud')
    for c, reg in posters:
        a, b = xs[c], xs[c + 1]
        pw = min(0.55, (b - a) * 0.45); px = a + (b - a) * 0.3
        mb.face([(px, i[1] + 0.5, zg + 0.004), (px + pw, i[1] + 0.5, zg + 0.004), (px + pw, i[1] + 0.5 + pw * 1.42, zg + 0.004),
                 (px, i[1] + 0.5 + pw * 1.42, zg + 0.004)], 'tex', (0, 0, 1), 1.0,
                lambda co, px=px, pw=pw, reg=reg: reg_uv(reg, (co.x - px) / pw, (co.y - i[1] - 0.5) / (pw * 1.42), 0.0))
    put(B, wf, mb.bm())
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'opening', a0=min(a0, a1), a1=max(a0, a1), b0=z0, b1=z1)
    c3 = wf.P((x0 + x1) / 2, z0, 0)
    B.doors.append({'name': name, 'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(x1 - x0, 3), round(z1 - z0, 3)], 'wall': wf.mp})


def roller_shutter(B, wf, x0, x1, z0, z1, mat='accent', housing='accentp', pitch=0.1, name='Shutter'):
    """A closed roller shutter in an opening: the box over it, side rails, ribbed slats, bottom bar."""
    put(B, wf, fbox((x0 - 0.15, z1, 0.0), (x1 + 0.15, z1 + 0.38, 0.3), 0.07, housing))
    for x in (x0, x1 - 0.08):
        put(B, wf, fbox((x, z0, 0.0), (x + 0.08, z1, 0.09), 0.015, 'metald'))
    mb = MB()
    zz = z1
    a_, b_ = x0 + 0.06, x1 - 0.06
    while zz - pitch > z0 + 0.08:
        a, b = zz - pitch, zz
        mb.face([(a_, a + 0.015, 0.04), (b_, a + 0.015, 0.04), (b_, b - 0.02, 0.05), (a_, b - 0.02, 0.05)], mat, (0, 0, 1))
        mb.face([(a_, b - 0.02, 0.05), (b_, b - 0.02, 0.05), (b_, b, 0.028), (a_, b, 0.028)], mat, (0, 0.6, 1), 0.9)
        mb.face([(a_, a, 0.028), (b_, a, 0.028), (b_, a + 0.015, 0.04), (a_, a + 0.015, 0.04)], mat, (0, -1, 1), 0.6)
        zz -= pitch
    mb.face([(a_, z0 + 0.08, 0.035), (b_, z0 + 0.08, 0.035), (b_, zz, 0.035), (a_, zz, 0.035)], mat, (0, 0, 1))
    put(B, wf, mb.bm())
    put(B, wf, fbox((a_, z0, 0.02), (b_, z0 + 0.09, 0.075), 0.015, 'metald', back=True))
    put(B, wf, fbox(((x0 + x1) / 2 - 0.12, z0 + 0.12, 0.05), ((x0 + x1) / 2 + 0.12, z0 + 0.18, 0.09), 0.01, 'metal'))
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z1, length=0.3, k=0.4)
    c3 = wf.P((x0 + x1) / 2, z0, 0)
    B.doors.append({'name': name, 'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(x1 - x0, 3), round(z1 - z0, 3)], 'wall': wf.mp})


def hood(B, wf, x0, x1, z, out=0.4):
    """A small metal hood over a window (a single-slope tin canopy)."""
    p0 = wf.P(x0 - 0.14, 0, 0); p1 = wf.P(x1 + 0.14, 0, 0)
    shed(B, min(p0.x, p1.x), max(p0.x, p1.x), -out, 0.02, z + 0.12, z + 0.24, t=0.035, pitch=0.16, depth=0.02, fascia_mat='trimw', feat=False)
    B.feat(wf.mp, 'ao', a0=min(p0.x, p1.x), a1=max(p0.x, p1.x), b=z + 0.1, length=0.35, k=0.4)


def amado(B, wf, x0, x1, z1):
    """The storm-shutter box over a window and its runner (an aluminium detail of the town's houses)."""
    put(B, wf, fbox((x0 - 0.08, z1 + 0.02, 0.0), (x1 + 0.08, z1 + 0.28, 0.2), 0.03, 'alu'))
    a0, b0 = wf.ab(x0 - 0.08, z1); a1, _ = wf.ab(x1 + 0.08, z1)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z1, length=0.22, k=0.35)


def ground_ac(B, P, w=0.8, h=0.58, d=0.3, yaw=0.0):
    """An AC condenser standing on two little blocks on the ground at the world point P (grille to -Y)."""
    x, y, z = P
    body = fbox((-w / 2, 0.1, -d / 2), (w / 2, 0.1 + h, d / 2), 0.035, 'whitep', back=True)
    fr = faces_facing(body, (0, 0, 1), 0.95)
    setmat(body, 'tex', fr)
    uv_fn(body, fr, 'ac', lambda co: ((co.x + w / 2) / w, (co.y - 0.1) / h), 0.02)
    M = T(x, y, z) @ R(yaw, 'Z') @ R(PI / 2, 'X')
    B.add(xform(body, M))
    for sx in (-1, 1):
        B.add(xform(box((sx * w * 0.32 - 0.08, 0.0, -d / 2), (sx * w * 0.32 + 0.08, 0.1, d / 2), 'conc'), M))


def round_bin(B, P, r=0.27, h=0.68, mat='bluebin'):
    bb, _ = lathe([(r * 0.88, 0.0), (r, h * 0.94), (r * 1.04, h * 0.95), (r * 1.04, h), (r * 0.3, h + 0.05), (r * 0.25, h + 0.09),
                   (0.0, h + 0.1)], 10, mat)
    xform(bb, T(P)); B.add(bb)


def bucket_flowers(B, P, seed, r=0.13, h=0.28, kinds=('fl1', 'fl3')):
    """A metal bucket of cut flowers at the world point P."""
    rng = np.random.default_rng(seed)
    bk, _ = lathe([(r * 0.78, 0.0), (r, h), (r * 0.94, h), (0.0, h * 0.86)], 7, ['bucket', 'bucket', 'leafd'], phase=rng.random())
    xform(bk, T(P)); B.add(bk)
    top = Vector(P) + Vector((0, 0, h))
    B.add(blob(top + Vector((0, 0, 0.12)), (r * 1.1, r * 1.0, 0.16), ['leaf', 'leafd'][seed % 2], 6, 2, seed))
    for k in range(4):
        a = 2 * PI * k / 4 + rng.random()
        c = top + Vector((math.cos(a) * r * 0.55, math.sin(a) * r * 0.55, 0.2 + rng.random() * 0.1))
        B.add(blob(c, (0.07, 0.07, 0.055), kinds[k % len(kinds)], 5, 1, seed * 7 + k, 0.08))


def paper_lantern(B, P, h=0.5, r=0.2):
    x, y, z = P
    body, _ = lathe([(0.0, -h / 2), (r * 0.62, -h * 0.47), (r * 0.92, -h * 0.3), (r, 0.0), (r * 0.92, h * 0.3), (r * 0.62, h * 0.47), (0.0, h / 2)],
                    10, 'lantern')
    xform(body, T(x, y, z)); B.add(body)
    for zz, sg in ((-h / 2, -1), (h / 2, 1)):
        cp, _ = lathe([(r * 0.66, 0.0), (r * 0.66, 0.06 * sg), (0.0, 0.06 * sg)], 10, 'black')
        xform(cp, T(x, y, z + zz - 0.02 * sg)); B.add(cp)
    B.add(tube([(x, y, z + h / 2 + 0.04), (x, y, z + h / 2 + 0.3)], 0.012, 'black', 4))


def flat_ac(B, x, y, z):
    """A rooftop AC condenser at the world point (x, y, z) (grille toward -Y)."""
    B.add(cbox2((x - 0.45, y - 0.18, z), (x + 0.45, y + 0.18, z + 0.62), 0.03, 'whitep'))
    fr = MB()
    fr.face([(x - 0.3, y - 0.181, z + 0.06), (x + 0.4, y - 0.181, z + 0.06), (x + 0.4, y - 0.181, z + 0.58), (x - 0.3, y - 0.181, z + 0.58)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('ac', 0.3 + (co.x - x + 0.3) / 0.7 * 0.7, (co.z - z - 0.06) / 0.52))
    B.add(fr.bm())


def garden_pine(B, P, seed=0, h=2.75):
    """A cloud-pruned garden pine: a crooked trunk, branches out to flat dark pads of needles, a few
    rounded stones at its foot."""
    rng = np.random.default_rng(seed)
    x, y, z = P
    trunk = [(x, y, z), (x + 0.16, y, z + 0.7), (x - 0.06, y + 0.04, z + 1.4), (x + 0.1, y, z + 2.1), (x - 0.02, y, z + h)]
    B.add(tube(trunk, 0.11, 'woodd', 7))
    pads = [(0.02, h + 0.05, 0.62), (0.8, 2.05, 0.66), (-0.75, 1.62, 0.62), (0.66, 1.05, 0.55), (-0.5, 2.45, 0.5), (-0.85, 0.9, 0.45)]
    for k, (dx, dz, r) in enumerate(pads):
        t = min(dz / h, 1.0) * (len(trunk) - 1)
        i = min(int(t), len(trunk) - 2); f = t - i
        a, b = Vector(trunk[i]), Vector(trunk[i + 1])
        base = a.lerp(b, f)
        end = Vector((x + dx * 0.85, y + rng.uniform(-0.08, 0.08), z + dz - 0.12))
        if abs(dx) > 0.1:
            B.add(tube([base, base.lerp(end, 0.5) + Vector((0, 0, 0.12)), end], 0.035, 'woodd', 5))
        c = Vector((x + dx, end.y, z + dz))
        mat = ['leafd', 'leaf', 'leafd'][k % 3]
        B.add(blob(c, (r, r * 0.85, r * 0.42), mat, 8, 2, seed * 13 + k, 0.14, flat_bottom=0.3))
        B.add(blob(c + Vector((r * 0.38, -r * 0.12, r * 0.18)), (r * 0.62, r * 0.55, r * 0.34), 'leafd' if mat == 'leaf' else 'leaf', 7, 2, seed * 17 + k, 0.12, flat_bottom=0.3))
        B.add(blob(c + Vector((-r * 0.4, -r * 0.05, r * 0.12)), (r * 0.55, r * 0.5, r * 0.3), mat, 7, 2, seed * 19 + k, 0.12, flat_bottom=0.3))
    for k, (dx, dy, r) in enumerate(((-0.35, -0.2, 0.38), (0.3, -0.35, 0.32), (0.05, 0.25, 0.28))):
        B.add(blob((x + dx, y + dy, z + r * 0.45), (r, r * 0.85, r * 0.62), ['white', 'stone', 'white'][k], 8, 3, seed * 5 + k, 0.08, flat_bottom=0.3))


# ---------------------------------------------------------------- ShopKonbini
def shop_konbini(B):
    """A corner convenience store: one tall storey, a glass front full of shelves and magazines, a
    deep white fascia with blue and green stripes (KANATA 24), downlights, recycling bins (it stands
    back from the footpath; the street puts drinks machines and bicycles on its apron)."""
    W, H, D = B.W, B.H, B.D
    sf = (-W / 2 + 0.3, 3.2, 0.0, 2.75)
    F, Rt, Bk, Lf = town_shell(B, [sf], gaps=[(sf[0], sf[1])], pp=0.45, ph=0.3)
    storefront(B, F, *sf, cols=6, region='gl_konbini', transom=2.4, door_cols=(4,), posters=((0, 'poster2'), (2, 'poster1')))
    # the fascia: a deep box round the front, the sign on it, downlights under it
    fz0, fz1, out = 2.95, 4.0, 0.45
    B.add(fbox((-W / 2 - 0.05, -out, fz0), (W / 2 + 0.05, 0.0, fz1), 0.03, 'whitep', back=True))
    decal(B, F, -W / 2 + 0.05, W / 2 - 0.05, fz0 + 0.05, fz1 - 0.05, out + 0.003, 'sg_konbini')
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=fz0, length=0.55, k=0.55)
    for x in np.linspace(-W / 2 + 0.8, W / 2 - 0.8, 6):
        lp, _ = lathe([(0.0, -0.01), (0.09, -0.01), (0.1, 0.0), (0.0, 0.0)], 8, ['lamp', 'white', 'white'])
        xform(lp, T(x, -out * 0.5, fz0 - 0.001)); B.add(lp)
    B.lamps.append({'name': 'Lamp', 'center': [0.0, round(-out * 0.5, 3), round(fz0 - 0.05, 3)]})
    # beside the glass: a recycling cabinet with three mouths, a pole-mounted mirror's bracket, posters
    rx0, rx1 = 3.4, W / 2 - 0.15
    B.add(fbox((rx0, -0.62, 0.0), (rx1, -0.05, 1.02), 0.03, 'whitep', back=True))
    lab = MB()
    lab.face([(rx0 + 0.02, -0.621, 0.78), (rx1 - 0.02, -0.621, 0.78), (rx1 - 0.02, -0.621, 0.98), (rx0 + 0.02, -0.621, 0.98)], 'tex', (0, -1, 0), 1.0,
             lambda co: reg_uv('recycle', (co.x - rx0 - 0.02) / (rx1 - rx0 - 0.04), (co.z - 0.78) / 0.2, 0.0))
    B.add(lab.bm())
    for k in range(3):
        cx = rx0 + (rx1 - rx0) * (k + 0.5) / 3
        hole, _ = lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.004)], 10, 'dark')
        xform(hole, T(cx, -0.623, 0.58) @ R(PI / 2, 'X')); B.add(hole)
    put(B, F, fbox((3.45, 1.2, 0.0), (4.15, 2.2, 0.03), 0.01, 'whitep'))
    decal(B, F, 3.5, 4.1, 1.25, 2.15, 0.032, 'poster1')
    B.add(box((-1.0, -0.8, 0.0), (1.4, -0.06, 0.02), 'navy', skip=('-z',)))
    # the side: three condensers on the ground, a meter cabinet, a back door
    for k in range(3):
        ac_unit(B, Rt, 2.0 + k * 0.95, 0.12, 0.0, w=0.82, h=0.6, d=0.32, brackets=False, pipe=(k == 0))
    meter_box(B, Rt, 5.4, 1.0, w=0.5, h=0.6)
    vent(B, Rt, 7.2, 2.3, 0.34)
    wall_pipe(B, -W / 2 + 0.12, -0.08, H + 0.1, head=False)
    for x in (-2.5, 0.0, 2.5):
        flat_ac(B, x, D - 1.5, H)
    return H + 0.45 + 0.11


# ---------------------------------------------------------------- ShopMart
def shop_mart(B):
    """A small supermarket: an aluminium shopfront with sliding doors and posters, a tiled canopy on
    brackets, a big sign board over it (KOTORI MART), rooms above with hooded windows."""
    W, H, D = B.W, B.H, B.D
    sf = (-4.1, 4.1, 0.0, 2.7)
    up = [(-3.7, -1.5, 5.15, 6.35), (1.5, 3.7, 5.15, 6.35)]
    side = [(2.6, 3.8, 5.15, 6.35), (5.6, 6.8, 5.15, 6.35)]
    F, Rt, Bk, Lf = town_shell(B, [sf] + up, gaps=[(sf[0], sf[1])], side=side, courses=[(4.98, 5.06)])
    storefront(B, F, *sf, cols=6, region='gl_mart', transom=2.3, door_cols=(2, 3), posters=((0, 'poster1'), (5, 'poster2'), (1, 'poster2')))
    # fascia under the canopy, the canopy on brackets, its flashing
    put(B, F, fbox((-W / 2 + 0.02, 2.7, 0.0), (W / 2 - 0.02, 3.08, 0.16), 0.03, 'accentp'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=2.7, length=0.3, k=0.45)
    z0, rise = 3.12, 0.55
    pitched(B, 'x', -1.1, 1.1, -W / 2 - 0.05, W / 2 + 0.05, z0, rise, t=0.12, row=0.22, lip=0.03, mat='clay', slopes=(0,), ridge=False,
            barge=(True, True), over=0.03, barge_w=0.16, fmap='roofb', fascia_mat='accentw')
    B.add(fbox((-W / 2 - 0.1, 0.0, z0 + rise + 0.08), (W / 2 + 0.1, 0.09, z0 + rise + 0.2), 0.02, 'galvw'))
    knee_brackets(B, F, (-W / 2 + 0.3, -1.4, 1.4, W / 2 - 0.38), z0 + 0.05, 1.0, 'metald', drop=0.4, t=0.06)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=z0 + rise, length=0.45, k=0.5)
    # the sign board
    z_panel = sign_board(B, F, -W / 2 + 0.1, W / 2 - 0.1, 3.85, 4.85, out=0.2, frame='accentp', panel='creamp', bw=0.09)
    decal(B, F, -W / 2 + 0.19, W / 2 - 0.19, 3.94, 4.76, z_panel + 0.004, 'sg_mart')
    for x in (-3.0, 0.0, 3.0):
        gooseneck(B, F, x, 4.95, reach=0.42, rise=0.22)
    # rooms above
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, head=None, sill='trim', frame='alu', glass=('glass1', 'glass2')[k], seed=401 + k)
        hood(B, F, wo[0], wo[1], wo[3])
    ac_unit(B, F, 0.0, 5.45, 0.0, w=0.8, h=0.56, d=0.3)
    wall_pipe(B, W / 2 - 0.12, -0.08, H + 0.1)
    # side: two condensers, meters, a door to the stock room
    ac_unit(B, Rt, 1.5, 1.1, 0.0, w=0.8, h=0.56, d=0.3)
    ac_unit(B, Rt, 1.5, 2.0, 0.0, w=0.8, h=0.56, d=0.3, pipe=False)
    meter_box(B, Rt, 2.6, 1.0); meter_box(B, Rt, 3.05, 1.0)
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, glass='glass2', seed=411, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass0', seed=412, cheap=True, register=False)
    vent(B, Lf, -3.0, 2.2, 0.3)
    flat_ac(B, -2.2, D - 2.0, H); flat_ac(B, -1.1, D - 2.0, H)
    antenna(B, 3.2, D - 1.2, H, 1.6)
    # a doormat and a stack of shopping baskets by the door
    B.add(box((-1.2, -0.75, 0.0), (1.2, -0.06, 0.02), 'green', skip=('-z',)))
    for k in range(4):
        B.add(fbox((-4.0, -0.65, 0.02 + k * 0.07), (-3.45, -0.25, 0.09 + k * 0.07), 0.015, 'red', back=True))
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- ShopCafe
def shop_cafe(B):
    """A cafe: a dark tiled ground floor with one big pane and a glazed door, a plain blind, a name
    board, a round hanging sign, a bench and bay trees; rendered rooms above."""
    W, H, D = B.W, B.H, B.D
    gt = 3.35
    win = (-3.0, 0.75, 0.5, 2.7)
    door_o = (1.3, 2.55, 0.12, 2.6)
    up = [(-2.6, 0.6, 4.25, 5.75), (1.4, 2.6, 4.25, 5.75)]
    side = [(3.0, 4.2, 4.25, 5.75)]
    F, Rt, Bk, Lf = town_shell(B, [win, door_o] + up, gaps=[(door_o[0], door_o[1])], side=side,
                               zones=[(-W / 2, W / 2, 0.0, gt, 'tile')])
    B.feat('front', 'tilegrid', a0=-W / 2 - 0.1, a1=W / 2 + 0.1, b0=0.0, b1=gt, tw=0.24, th=0.12, bond=0.5, k=0.42, var=0.1)
    string_course(B, u_path(B), gt, gt + 0.12, out=0.07, mat='alud')
    window(B, F, *win, depth=0.14, fw=0.09, cols=1, transom=0.82, frame='woodd', glass='gl_cafe', sill='woodd', head=None, seed=421)
    door(B, F, *door_o, mat='accent', glass=0.72, panels=((1, 1),), casing=False, glass_region='gl_cafe', name='Door')
    steps(B, F, door_o[0] - 0.1, door_o[1] + 0.1, [0.12], tread=0.36)
    awning(B, F, -3.2, 2.75, 3.05, 1.1, 0.34, 1, 'accent', 'accent', valance=0.2, scallops=False, arms=True, segs=3)
    put(B, F, fbox((-2.0, 3.6, 0.0), (2.0, 4.05, 0.09), 0.02, 'black'))
    decal(B, F, -1.92, 1.92, 3.64, 4.01, 0.092, 'sg_cafe')
    B.feat('front', 'ao_rect', a0=-2.0, a1=2.0, b0=3.6, b1=4.05, k=0.3)
    # the round sign on a bracket, both faces
    sx, sz, sy = W / 2 - 0.35, 4.3, -0.62
    B.add(tube([(sx, -0.02, sz + 0.42), (sx, -0.9, sz + 0.42)], 0.02, 'metald', 5))
    B.add(fbox((sx - 0.08, -0.04, sz + 0.3), (sx + 0.08, 0.0, sz + 0.54), 0.01, 'metald'))
    for xx in (sy - 0.12, sy + 0.12):
        B.add(tube([(sx, xx, sz + 0.42), (sx, xx, sz + 0.3)], 0.008, 'metald', 4))
    rim, _ = lathe([(0.31, -0.03), (0.31, 0.03), (0.0, 0.03)], 14, 'cream', phase=0.5)
    xform(rim, T(sx, sy, sz) @ R(PI / 2, 'Y')); B.add(rim)
    for sg in (-1, 1):
        d = MB()
        pts = [(0.29 * math.cos(2 * PI * k / 14), 0.29 * math.sin(2 * PI * k / 14)) for k in range(14)]
        d.face([(sx + sg * 0.032, sy + p[0], sz + p[1]) for p in pts], 'tex', (sg, 0, 0), 1.0,
               lambda co, sg=sg: reg_uv('sg_disc', 0.5 - sg * (co.y - sy) / 0.6, 0.5 + (co.z - sz) / 0.6, 0.0))
        B.add(d.bm())
    # bench under the window, bay trees by the door
    bench(B, F, -2.7, -0.9)
    pot(B, (-3.3, -0.4, 0.0), 0.22, 0.42, 'pot2', 'tall', seed=422, scale=1.25)
    pot(B, (3.0, -0.42, 0.0), 0.2, 0.38, 'pot3', 'bush', seed=423, scale=1.2)
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=(3, 1)[k], transom=0.72, head='lintel', planter=('woodc', None)[k], glass=('glass1', 'glass2')[k], seed=424 + k)
    lantern(B, F, 0.95, 2.1, out=0.18)
    wall_pipe(B, -W / 2 + 0.12, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.2, 1.2, 0.0, w=0.78, h=0.54, d=0.3)
    meter_box(B, Rt, 3.4, 1.0)
    vent(B, Rt, 5.2, 2.4, 0.28)
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, glass='glass1', seed=426, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass0', seed=427, cheap=True, register=False)
    flat_ac(B, 1.6, D - 1.6, H)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- ShopBooks
def shop_books(B):
    """A bookshop: a painted timber shopfront (pilasters, fascia with SHIORI BOOKS, small-paned
    windows of books, a recessed door), a cart of books outside, tile-clad rooms above."""
    W, H, D = B.W, B.H, B.D
    wl = (-2.85, -0.8, 0.75, 2.55); wr = (0.8, 2.85, 0.75, 2.55)
    door_o = (-0.55, 0.55, 0.0, 2.55)
    up = [(-2.45, -0.85, 4.15, 5.7), (0.85, 2.45, 4.15, 5.7)]
    side = [(3.0, 4.2, 4.15, 5.7)]
    F, Rt, Bk, Lf = town_shell(B, [wl, wr, door_o] + up, gaps=[(door_o[0], door_o[1])], side=side,
                               zones=[(-W / 2, W / 2, 0.0, 3.5, 'accentw')])
    B.feat('front', 'tilegrid', a0=-W / 2 - 0.1, a1=W / 2 + 0.1, b0=3.5, b1=H + 0.6, tw=0.24, th=0.075, bond=0.5, k=0.3, var=0.08)
    for wo, s in ((wl, 431), (wr, 432)):
        window(B, F, *wo, depth=0.12, fw=0.07, cols=3, rows=2, frame='accentw', glass='gl_books', sill='accentw', head=None, mull=0.045, seed=s)
        put(B, F, fbox((wo[0] + 0.05, 0.12, 0.0), (wo[1] - 0.05, wo[2] - 0.12, 0.04), 0.015, 'accentp'))
    door(B, F, *door_o, depth=0.32, mat='accent', glass=0.55, panels=((1, 1),), casing=False, glass_region='gl_books', name='Door')
    put(B, F, fbox((-0.62, 0.0, -0.32), (0.62, 0.04, 0.02), 0.01, 'stone'))
    for x0, x1 in ((-W / 2 + 0.02, -2.92), (2.92, W / 2 - 0.02)):
        put(B, F, fbox((x0, 0.0, 0.0), (x1, 2.7, 0.1), 0.02, 'accentp'))
        put(B, F, fbox((x0 - 0.03, 2.62, 0.0), (x1 + 0.03, 2.72, 0.14), 0.015, 'accentp'))
    put(B, F, fbox((-W / 2 + 0.02, 2.72, 0.0), (W / 2 - 0.02, 3.36, 0.15), 0.02, 'accentp'))
    decal(B, F, -2.85, 2.85, 2.8, 3.28, 0.153, 'sg_books')
    put(B, F, fbox((-W / 2 - 0.06, 3.36, 0.0), (W / 2 + 0.06, 3.46, 0.24), 0.02, 'accentp'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=2.72, length=0.35, k=0.4)
    for x in (-2.0, 2.0):
        gooseneck(B, F, x, 3.62, reach=0.42, rise=0.22)
    # the book cart: a sloping tray of books on a little trolley
    cx, cy = 1.85, -0.75
    for x in (cx - 0.6, cx + 0.6):
        for y in (cy - 0.22, cy + 0.22):
            B.add(box((x - 0.025, y - 0.025, 0.08), (x + 0.025, y + 0.025, 0.7), 'woodd'))
            wh, _ = lathe([(0.0, -0.035), (0.075, -0.035), (0.075, 0.035), (0.0, 0.035)], 8, 'rubber')
            xform(wh, T(x, y, 0.075) @ R(PI / 2, 'Y')); B.add(wh)
    tray = fbox((-0.7, -0.3, 0.0), (0.7, 0.3, 0.12), 0.02, 'woodc', back=True)
    xform(tray, T(cx, cy, 0.66) @ R(-0.22, 'X')); B.add(tray)
    bk = MB()
    bk.face([(-0.65, -0.26, 0.125), (0.65, -0.26, 0.125), (0.65, 0.26, 0.125), (-0.65, 0.26, 0.125)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('books', (co.x + 0.65) / 1.3, (co.y + 0.26) / 0.52, 0.0))
    bkm = bk.bm(); xform(bkm, T(cx, cy, 0.66) @ R(-0.22, 'X')); B.add(bkm)
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, transom=0.7, head='lintel', planter='accent', glass=('glass1', 'glass0')[k], seed=433 + k)
    wall_pipe(B, W / 2 - 0.12, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.0, 1.2, 0.0, w=0.78, h=0.54, d=0.3)
    meter_box(B, Rt, 3.2, 1.0)
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, glass='glass2', seed=436, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass1', seed=437, cheap=True, register=False)
    flat_ac(B, -1.6, D - 1.8, H)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- ShopFlorist
def shop_florist(B):
    """A florist: an open front with buckets of cut flowers on a stepped stand, a plain canvas
    awning, a sign (mimosa flowers), pots and a climber; rooms above."""
    W, H, D = B.W, B.H, B.D
    opn = (-3.2, 1.65, 0.0, 2.8)
    door_o = (2.05, 3.05, 0.12, 2.55)
    up = [(-2.7, -1.0, 4.2, 5.6), (0.4, 2.1, 4.2, 5.6)]
    side = [(3.0, 4.2, 4.2, 5.6)]
    F, Rt, Bk, Lf = town_shell(B, [opn, door_o] + up, gaps=[(opn[0], opn[1]), (door_o[0], door_o[1])], side=side)
    room = 2.2
    shop_room(B, opn[0], opn[1], 0.0, opn[3], room)
    put(B, F, fbox((opn[0] - 0.1, 2.8, 0.0), (opn[1] + 0.1, 3.0, 0.08), 0.02, 'trim'))
    # inside: a shelf of buckets and greenery at the back
    B.add(fbox((opn[0] + 0.2, room - 0.5, 0.0), (opn[1] - 0.2, room, 0.55), 0.01, 'woodc', back=True))
    kinds = [('fl1', 'fl4'), ('fl3', 'fl6'), ('fl5', 'fl4'), ('fl2', 'fl3'), ('fl4', 'fl1'), ('fl6', 'fl5')]
    for i, x in enumerate(np.linspace(opn[0] + 0.45, opn[1] - 0.45, 6)):
        bucket_flowers(B, (x, room - 0.25, 0.55), 450 + i, kinds=kinds[i % 6])
    bw = MB()      # the back wall: the shop's own interior (greenery, flowers, buckets), lit
    bw.face([(opn[0] + 0.02, room - 0.02, 0.5), (opn[1] - 0.02, room - 0.02, 0.5), (opn[1] - 0.02, room - 0.02, opn[3] - 0.05),
             (opn[0] + 0.02, room - 0.02, opn[3] - 0.05)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('gl_flower', (co.x - opn[0]) / (opn[1] - opn[0]), (co.z - 0.5) / (opn[3] - 0.55), 0.0))
    B.add(bw.bm())
    pendant(B, (opn[0] + opn[1]) / 2 - 1.0, 1.0, opn[3], 0.5)
    pendant(B, (opn[0] + opn[1]) / 2 + 1.0, 1.0, opn[3], 0.5)
    # outside: the stepped stand
    sx0, sx1 = -3.05, 1.45
    for tier in range(3):
        zt = 0.3 + 0.24 * tier
        ya = -1.05 + 0.34 * tier; yb = ya + 0.34
        B.add(box((sx0, ya, zt - 0.05), (sx1, yb, zt), 'woodc', skip=('-z',)))
        B.add(box((sx0, ya - 0.01, zt - 0.24 if tier else 0.0), (sx1, ya + 0.02, zt - 0.05), 'woodd', skip=('+z', '-z')))
        n = 6 - tier
        for i in range(n):
            x = sx0 + (sx1 - sx0) * (i + 0.5) / n
            bucket_flowers(B, (x, (ya + yb) / 2, zt), 470 + tier * 10 + i, kinds=kinds[(i + tier * 2) % 6])
    for x in (sx0 + 0.03, sx1 - 0.08):
        B.add(box((x, -1.05, 0.0), (x + 0.05, -1.0, 0.3), 'woodd'))
    awning(B, F, opn[0] - 0.1, opn[1] + 0.1, 3.08, 1.25, 0.38, 6, 'accent', 'accent', valance=0.24, scallops=True, arms=True)
    z_panel = sign_board(B, F, -W / 2 + 0.1, W / 2 - 0.1, 3.35, 4.0, out=0.16, frame='accentp', panel='creamp', bw=0.07)
    decal(B, F, -W / 2 + 0.17, W / 2 - 0.17, 3.42, 3.93, z_panel + 0.004, 'sg_flower')
    door(B, F, *door_o, mat='accent', glass=0.65, panels=((1, 1),), casing=True, glass_region='gl_flower', name='Door')
    steps(B, F, door_o[0] - 0.08, door_o[1] + 0.08, [0.12], tread=0.32)
    pot(B, (3.3, -0.45, 0.0), 0.24, 0.42, 'pot', 'tall', seed=481, scale=1.3)
    pot(B, (1.85, -0.38, 0.0), 0.16, 0.26, 'pot2', 'flowers', seed=482)
    bucket_flowers(B, (2.2, -0.42, 0.0), 483, kinds=('fl5', 'fl4'))
    climber(B, F, -W / 2 + 0.25, 3.0, 6.4, 0.5, seed=484, n=12, flowers='fl1')
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, transom=0.72, head='key', planter='pot', glass=('glass2', 'glass1')[k], seed=485 + k)
    wall_pipe(B, W / 2 - 0.12, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.2, 1.2, 0.0, w=0.78, h=0.54, d=0.3)
    hose_reel(B, Rt, 3.6, 0.9)
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, glass='glass0', seed=487, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass2', seed=488, cheap=True, register=False)
    flat_ac(B, 1.4, D - 1.6, H)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- ShopNoodle
def shop_noodle(B):
    """A noodle house: a dark timber ground floor with a lattice front and a sliding door under a
    split curtain, a red paper lantern, a tiled pent roof, a wooden name board, a kitchen flue."""
    W, H, D = B.W, B.H, B.D
    gt = 2.95
    lat = (-2.95, -0.1, 0.45, 2.55)
    door_o = (0.35, 2.75, 0.0, 2.45)
    up = [(-2.4, 0.6, 4.1, 5.2), (1.5, 2.5, 4.1, 5.2)]
    side = [(3.0, 4.1, 4.1, 5.2)]
    F, Rt, Bk, Lf = town_shell(B, [lat, door_o] + up, gaps=[(door_o[0], door_o[1])], side=side, ph=0.35,
                               zones=[(-W / 2, W / 2, 0.0, gt, 'woodd')], pp=0.5)
    # the lattice: a recessed panel with the lattice tile, a stone base under it
    mb = MB()
    reveal(mb, *lat, 0.12)
    mb.face([(lat[0], lat[2], -0.1), (lat[1], lat[2], -0.1), (lat[1], lat[3], -0.1), (lat[0], lat[3], -0.1)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('lattice', (co.x - lat[0]) / (lat[1] - lat[0]), (co.y - lat[2]) / (lat[3] - lat[2]), 0.0))
    put(B, F, mb.bm())
    put(B, F, fbox((lat[0] - 0.1, 0.0, 0.0), (lat[1] + 0.1, lat[2], 0.08), 0.02, 'stone'))
    for x0, x1 in ((-W / 2, -W / 2 + 0.2), (-0.05, 0.3), (W / 2 - 0.2, W / 2)):
        put(B, F, fbox((x0, 0.0, 0.0), (x1, gt, 0.12), 0.015, 'woodd'))
    door(B, F, *door_o, depth=0.22, mat='woodd', double=True, glass=0.78, panels=((1, 1),), casing=False, glass_region='glass3', name='Door')
    # the split curtain on its rod
    put(B, F, tube([(door_o[0] - 0.05, 2.5, 0.16), (door_o[1] + 0.05, 2.5, 0.16)], 0.018, 'woodd', 6))
    n = 4; cw = (door_o[1] - door_o[0] - 0.08) / n
    for i in range(n):
        x0 = door_o[0] + 0.04 + i * cw + 0.015; x1 = x0 + cw - 0.03
        V = []
        for yy, sh in ((2.48, 0.0), (2.15, 0.012), (1.78, 0.0)):
            V += [(x0, yy, 0.15 + sh), (x1, yy, 0.15 + sh)]
        bmn, _ = bm_from(V, [[0, 1, 3, 2], [2, 3, 5, 4]], 'tex')
        bmn.normal_update()
        for f in bmn.faces:
            if f.normal.z < 0: f.normal_flip()
        uv_fn(bmn, list(bmn.faces), 'noren2', lambda co, i=i, x0=x0, x1=x1: ((i + (co.x - x0) / (x1 - x0)) / n, (co.y - 1.78) / 0.7), 0.0)
        put(B, F, bmn)
    # the pent roof across the front, a name board over it
    pitched(B, 'x', -0.9, 0.9, -W / 2 - 0.12, W / 2 + 0.12, gt + 0.02, 0.42, t=0.12, row=0.22, lip=0.03, mat='kawara', slopes=(0,),
            ridge=False, barge=(True, True), over=0.03, barge_w=0.14, fmap='roofb', fascia_mat='woodd')
    B.add(fbox((-W / 2 - 0.12, 0.0, gt + 0.52), (W / 2 + 0.12, 0.09, gt + 0.64), 0.02, 'galvw'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=gt + 0.45, length=0.5, k=0.5)
    put(B, F, fbox((-1.35, 3.62, 0.0), (1.35, 4.12, 0.08), 0.02, 'woodd'))
    decal(B, F, -1.27, 1.27, 3.67, 4.07, 0.082, 'sg_noodle')
    paper_lantern(B, (W / 2 - 0.42, -0.42, 2.2))
    B.add(tube([(W / 2 - 0.42, -0.42, 2.75), (W / 2 - 0.42, -0.02, 2.75)], 0.015, 'metald', 4))
    bench(B, F, -2.75, -1.1)
    # upper floor: a barred window with a blind, a small one
    window(B, F, *up[0], cols=2, bars=9, frame='woodd', sill='woodd', head=None, glass='glass2', seed=491)
    window(B, F, *up[1], cols=1, frame='woodd', sill='woodd', head=None, glass='glass1', seed=492)
    wall_pipe(B, -W / 2 + 0.12, -0.08, H + 0.1)
    # the kitchen flue up the side wall, a condenser, gas bottles
    fx, fy = W / 2 + 0.2, 5.6
    B.add(tube([(W / 2, fy, 1.9), (fx, fy, 1.9), (fx, fy, H + 1.4)], 0.14, 'galvw', 8))
    for z in (2.8, 4.4, H + 0.2):
        B.add(tube([(fx, fy, z - 0.03), (fx, fy, z + 0.03)], 0.16, 'galvw', 8, caps=False))
    cp, _ = lathe([(0.0, -0.05), (0.3, 0.0), (0.0, 0.18)], 8, 'galvw')
    xform(cp, T(fx, fy, H + 1.55)); B.add(cp)
    ac_unit(B, Rt, 2.0, 1.1, 0.0, w=0.78, h=0.54, d=0.3)
    gas_bottle(B, (W / 2 + 0.3, 3.4, 0.0), 'white'); gas_bottle(B, (W / 2 + 0.3, 3.8, 0.0), 'white')
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, glass='glass2', seed=493, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass0', seed=494, cheap=True, register=False)
    return H + 0.5 + 0.11


# ---------------------------------------------------------------- ShopTall
def shop_tall(B):
    """A narrow three-storey building clad in square tiles: a closed roller shutter, a stair entrance
    with mailboxes, condensers on a ledge, a sign down the wall, hooded windows above."""
    W, H, D = B.W, B.H, B.D
    ent = (-2.5, -1.15, 0.0, 2.45)
    sh = (-0.75, 2.5, 0.0, 2.6)
    w2 = (-1.6, 2.0, 4.15, 5.55); w3 = (-1.6, 2.0, 7.15, 8.55)
    side = [(3.0, 4.2, 4.15, 5.55), (3.0, 4.2, 7.15, 8.55), (6.2, 7.4, 7.15, 8.55)]
    F, Rt, Bk, Lf = town_shell(B, [ent, sh, w2, w3], gaps=[(ent[0], ent[1]), (sh[0], sh[1])], side=side, ph=0.3,
                               courses=[(3.2, 3.3), (6.3, 6.4)])
    for mp, (a0, a1) in (('front', (-W / 2 - 0.1, W / 2 + 0.1)), ('right', (-0.1, D + 0.1)), ('left', (-0.1, D + 0.1))):
        B.feat(mp, 'tilegrid', a0=a0, a1=a1, b0=0.3, b1=H + 0.6, tw=0.3, th=0.3, bond=0.0, k=0.28, var=0.05)
    roller_shutter(B, F, *sh)
    # the stair entrance: a deep recess, a dim stairwell going up, mailboxes on its side
    dep = 1.7
    mb = MB()
    x0, x1, z1 = ent[0], ent[1], ent[3]
    mb.face([(x0, 0, 0), (x0, 0, -dep), (x0, z1, -dep), (x0, z1, 0)], 'reveal', (1, 0, 0), 0.75)
    mb.face([(x1, 0, 0), (x1, z1, 0), (x1, z1, -dep), (x1, 0, -dep)], 'reveal', (-1, 0, 0), 0.7)
    mb.face([(x0, z1, 0), (x1, z1, 0), (x1, z1, -dep), (x0, z1, -dep)], 'reveal', (0, -1, 0), 0.6)
    mb.face([(x0, 0, -dep), (x1, 0, -dep), (x1, z1, -dep), (x0, z1, -dep)], 'interior', (0, 0, 1), 0.55)
    put(B, F, mb.bm())
    B.add(box((x0, 0.0, 0.0), (x1, dep, 0.02), 'conc', skip=('-z',)))
    for k in range(7):
        y0 = 0.45 + 0.19 * k
        B.add(fbox((x0 + 0.02, y0, 0.0), (x1 - 0.02, dep, 0.17 * (k + 1)), 0.01, 'conc', back=True))
    B.add(box((x1 - 0.06, 0.4, 0.0), (x1, dep, 0.9 + 0.17 * 7), 'wallw'))
    B.add(tube([(x1 - 0.1, 0.5, 1.0), (x1 - 0.1, dep, 1.0 + 0.17 * 7)], 0.02, 'metald', 5))
    for r in range(2):
        for c in range(2):
            y = 0.15 + c * 0.32; z = 1.25 + r * 0.32
            B.add(fbox((x0, y, z), (x0 + 0.12, y + 0.29, z + 0.28), 0.01, 'alu', back=True))
            B.add(box((x0 + 0.12, y + 0.06, z + 0.17), (x0 + 0.125, y + 0.23, z + 0.2), 'black'))
    lp, _ = lathe([(0.0, -0.04), (0.14, -0.04), (0.15, 0.0), (0.0, 0.0)], 8, ['lamp', 'white', 'white'])
    xform(lp, T((x0 + x1) / 2, 0.8, z1 - 0.01)); B.add(lp)
    B.lamps.append({'name': 'Lamp', 'center': [round((x0 + x1) / 2, 3), 0.8, round(z1 - 0.05, 3)]})
    B.doors.append({'name': 'Door', 'center': [round((x0 + x1) / 2, 3), 0.0, 0.0], 'size': [round(x1 - x0, 3), z1], 'wall': 'front'})
    put(B, F, fbox((x0 - 0.12, z1, 0.0), (x1 + 0.12, z1 + 0.14, 0.4), 0.02, 'conc'))
    # condensers on a ledge under the second-floor window
    put(B, F, fbox((-2.2, 3.5, 0.0), (2.55, 3.62, 0.55), 0.02, 'conc'))
    B.feat('front', 'ao', a0=-2.2, a1=2.55, b=3.5, length=0.5, k=0.5)
    ac_unit(B, F, -0.75, 3.63, 0.05, w=0.8, h=0.56, d=0.34, brackets=False)
    ac_unit(B, F, 1.15, 3.63, 0.05, w=0.8, h=0.56, d=0.34, brackets=False)
    for k, wo in enumerate((w2, w3)):
        window(B, F, *wo, cols=2, head=None, sill='trim', frame='alu', glass=('glass1', 'glass2')[k], seed=501 + k)
        hood(B, F, wo[0], wo[1], wo[3])
    put(B, F, tube([(w3[0] - 0.1, w3[2] + 0.7, 0.3), (w3[1] + 0.1, w3[2] + 0.7, 0.3)], 0.022, 'metald', 6))
    for x in np.linspace(w3[0], w3[1], 7):
        put(B, F, tube([(x, w3[2] - 0.02, 0.3), (x, w3[2] + 0.7, 0.3)], 0.012, 'metald', 4))
    pot(B, F.P(1.4, w3[2] + 0.02, 0.0) + Vector((0, -0.12, 0)), 0.12, 0.2, 'pot', 'flowers', seed=503)
    # the sign down the wall by the entrance
    put(B, F, fbox((-2.55, 3.55, 0.0), (-1.95, 6.15, 0.1), 0.02, 'whitep'))
    decal(B, F, -2.5, -2.0, 3.6, 6.1, 0.102, 'sg_tall')
    wall_pipe(B, W / 2 - 0.1, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.0, 4.4, 0.0, w=0.78, h=0.54, d=0.3)
    meter_box(B, Rt, 1.0, 1.0); meter_box(B, Rt, 1.45, 1.0)
    for i, (a, b, z0_, z1_) in enumerate(side):
        window(B, Rt, a, b, z0_, z1_, cols=2, glass=('glass0', 'glass2', 'glass1')[i], seed=504 + i, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass1', seed=507 + i, cheap=True, register=False)
    antenna(B, 1.5, D - 1.5, H, 1.8)
    flat_ac(B, -1.2, D - 2.4, H)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- ShopBoutique
def shop_boutique(B):
    """A narrow three-storey building in small dark tiles: a boutique's glass front and door, a
    brass-lettered name board (MINAMO), a steel door to the flats, windows with sills and a rail."""
    W, H, D = B.W, B.H, B.D
    sf = (-2.3, 1.15, 0.0, 2.65)
    dr = (1.45, 2.25, 0.12, 2.3)
    up = [(-1.9, -0.15, 4.0, 5.5), (0.45, 2.0, 4.0, 5.5), (-1.9, -0.15, 7.0, 8.5), (0.45, 2.0, 7.0, 8.5)]
    side = [(3.0, 4.2, 4.0, 5.5), (3.0, 4.2, 7.0, 8.5)]
    F, Rt, Bk, Lf = town_shell(B, [sf, dr] + up, gaps=[(sf[0], sf[1]), (dr[0], dr[1])], side=side, ph=0.25,
                               courses=[(3.3, 3.4), (6.35, 6.45)], coping_mat='alud')
    for mp, (a0, a1) in (('front', (-W / 2 - 0.1, W / 2 + 0.1)), ('right', (-0.1, D + 0.1)), ('left', (-0.1, D + 0.1))):
        B.feat(mp, 'tilegrid', a0=a0, a1=a1, b0=0.25, b1=H + 0.6, tw=0.2, th=0.1, bond=0.5, k=0.3, var=0.08)
    storefront(B, F, *sf, cols=3, region='gl_boutique', frame='alud', kick=0.12, door_cols=(1,), name='Shopfront')
    door(B, F, *dr, mat='accent', glass=None, panels=((1, 1),), casing=False, name='Door')
    put(B, F, fbox((sf[0] - 0.1, 2.85, 0.0), (sf[1] + 0.1, 3.25, 0.06), 0.01, 'black'))
    decal(B, F, sf[0] - 0.05, sf[1] + 0.05, 2.87, 3.23, 0.062, 'sg_boutique')
    put(B, F, fbox((sf[0] - 0.1, sf[3], 0.0), (sf[1] + 0.1, sf[3] + 0.1, 0.35), 0.01, 'alud'))
    B.feat('front', 'ao', a0=sf[0], a1=sf[1], b=sf[3], length=0.35, k=0.45)
    for x in (sf[0] + 0.3, sf[1] - 0.3):
        lp, _ = lathe([(0.0, -0.01), (0.07, -0.01), (0.08, 0.0), (0.0, 0.0)], 8, ['lamp', 'alud', 'alud'])
        xform(lp, T(x, -0.2, sf[3] - 0.001)); B.add(lp)
    put(B, F, fbox((dr[0] - 0.05, dr[3] + 0.05, 0.0), (dr[1] + 0.05, dr[3] + 0.3, 0.05), 0.01, 'alu'))
    put(B, F, fbox((dr[1] + 0.06, 1.3, 0.0), (dr[1] + 0.18, 1.48, 0.03), 0.005, 'alu'))
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, head=None, sill='alu', frame='alu', glass=('glass1', 'glass2', 'glass0', 'glass1')[k], seed=541 + k)
    for wo in up[2:]:
        put(B, F, tube([(wo[0] - 0.05, wo[2] + 0.55, 0.22), (wo[1] + 0.05, wo[2] + 0.55, 0.22)], 0.02, 'metald', 5))
        for x in np.linspace(wo[0], wo[1], 4):
            put(B, F, tube([(x, wo[2] - 0.02, 0.22), (x, wo[2] + 0.55, 0.22)], 0.011, 'metald', 4))
    ac_unit(B, F, 1.25, 5.85, 0.0, w=0.7, h=0.5, d=0.28)
    wall_pipe(B, -W / 2 + 0.1, -0.08, H + 0.1)
    ac_unit(B, Rt, 2.0, 1.2, 0.0, w=0.78, h=0.54, d=0.3)
    meter_box(B, Rt, 1.0, 1.0)
    for i, (a, b, z0_, z1_) in enumerate(side):
        window(B, Rt, a, b, z0_, z1_, cols=2, glass=('glass2', 'glass1')[i], seed=546 + i, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, glass='glass0', seed=548 + i, cheap=True, register=False)
    flat_ac(B, 0.8, D - 2.0, H)
    pot(B, (sf[0] - 0.05, -0.32, 0.0), 0.15, 0.32, 'pot2', 'tall', seed=550, scale=1.1)
    return H + 0.6 + 0.11


# ---------------------------------------------------------------- HouseLeanTo
def house_lean_to(B):
    """A white two-storey house, its gable to the street, with a lean-to of corrugated sheeting on
    one side: small windows under tin hoods, a brick pier by the door, an AC unit, a blue bin."""
    W, H, D, RH = B.W, B.H, B.D, B.RH
    xm = -W / 2 + 2.7                      # where the main block meets the lean-to
    wm = W / 2 - xm
    xc = (xm + W / 2) / 2
    t, cap = 0.15, 0.1
    k = (RH - t - cap) / (wm / 2)
    apex = H + (wm / 2) * k
    ph = 0.35; v0 = ph - 0.05
    lz0, lz1 = 2.85, 3.35                  # the lean-to's wall top, front and back
    F = WF((0, 0, 0), (1, 0, 0), 'front')
    Rt = WF((W / 2, 0, 0), (0, 1, 0), 'right')
    Lm = WF((xm, 0, 0), (0, -1, 0), 'left')
    Ll = WF((-W / 2, 0, 0), (0, -1, 0), 'left')
    Bk = WF((0, D, 0), (-1, 0, 0), 'back')
    door_o = (xm + 0.25, xm + 1.15, 0.12, 2.15)
    wg = (xc - 0.3, xc + 1.85, 0.95, 2.05)
    wu = [(xc - 1.45, xc - 0.25, 3.55, 4.55), (xc + 0.55, xc + 1.75, 3.55, 4.55)]
    wl = (-W / 2 + 0.75, -W / 2 + 1.35, 1.0, 2.05)
    gable = [(xm, H), (xc, apex), (W / 2, H)]
    wall(B, F, xm, W / 2, gable, [door_o, wg] + wu, v0)
    wall(B, F, -W / 2, xm, lz0, [wl], v0, 'rib', rib=(0.2, 0.03))
    wall(B, Rt, 0, D, H, [(2.4, 3.4, 1.0, 2.05), (2.6, 3.6, 3.55, 4.55)], v0)
    wall(B, Lm, -D, 0, H, [(-3.6, -2.6, 3.7, 4.55)], lz0 - 0.1)
    wall(B, Ll, -D, 0, [(-D, lz1), (0, lz0)], [(-3.0, -2.2, 1.0, 1.9)], v0, 'rib', rib=(0.2, 0.03))
    wall(B, Bk, -W / 2, -xm, [(-W / 2, H), (-xc, apex), (-xm, H)], [], v0)
    wall(B, Bk, -xm, W / 2, lz1, [], v0, 'rib', rib=(0.2, 0.03))
    for x, y in ((W / 2, 0), (W / 2, D), (-W / 2, 0), (-W / 2, D)):
        corner_board(B, x, y, v0, (H if x > 0 else (lz0 if y == 0 else lz1)) - 0.02, s=0.05, mat='trimw', r=0.015)
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.05, mat='conc', closed=closed)
    e = 0.35
    a0, a1 = xm - e, W / 2 + e
    z0 = H - e * k
    top = pitched(B, 'y', a0, a1, -0.4, D + 0.4, z0, (wm / 2 + e) * k, t=t)
    gable_gutters(B, a0, a1, -0.45, D + 0.45, z0 - 0.04, pipe_y=0.3, pipe_side=1)
    attic_vent(B, F, xc, H + 0.95, 0.22)
    antenna(B, xc, D * 0.6, apex + 0.1, 1.7)
    # the lean-to's roof, sloping up to the back, its gutter
    sz0 = lz0 + 0.1
    shed(B, -W / 2 - 0.22, xm, -0.32, D + 0.22, sz0, lz1 + 0.12, t=0.08, pitch=0.22, depth=0.03, fascia_mat='trimw')
    eave_gutter(B, [(-W / 2 - 0.24, -0.34), (xm, -0.34)], sz0 - 0.12, size=0.11)
    downpipe(B, [(-W / 2 - 0.15, -0.41, sz0 - 0.2), (-W / 2 - 0.15, -0.41, sz0 - 0.32), (-W / 2 - 0.06, 0.25, sz0 - 0.6),
                 (-W / 2 - 0.06, 0.25, 0.3), (-W / 2 - 0.18, 0.25, 0.1)], brackets=[(-W / 2 - 0.06, 0.25, 1.2)])
    # the door: a brick pier beside it, a tin hood, a step
    pier = box((xm - 0.02, -0.12, 0.0), (xm + 0.22, 0.0, lz0 + 0.05), 'brick', skip=('+y',))
    B.add(_brick_uv(pier, xm + 0.1, -0.06, 0.24, 0.12, lz0))
    door(B, F, *door_o, mat='accent', glass=0.3, panels=((1, 2),), casing=False, name='Door')
    shed(B, door_o[0] - 0.25, door_o[1] + 0.25, -0.72, 0.02, 2.42, 2.56, t=0.05, pitch=0.16, depth=0.022, fascia_mat='trimw', feat=False)
    B.feat('front', 'ao', a0=door_o[0] - 0.25, a1=door_o[1] + 0.25, b=2.4, length=0.45, k=0.5)
    steps(B, F, door_o[0] - 0.3, door_o[1] + 0.3, [0.16], tread=0.55)
    bulkhead(B, F, door_o[1] + 0.25, 2.0)
    # windows under tin hoods
    window(B, F, *wg, cols=2, head=None, sill='trimw', frame='alu', glass='glass1', seed=511)
    hood(B, F, wg[0], wg[1], wg[3])
    for kk, wo in enumerate(wu):
        window(B, F, *wo, cols=2, head=None, sill='trimw', frame='alu', glass=('glass2', 'glass0')[kk], seed=512 + kk)
        hood(B, F, wo[0], wo[1], wo[3])
    window(B, F, *wl, cols=1, head=None, frame='alu', glass='glass0', seed=514, casing=(0.08, 0.05))
    window(B, Rt, 2.4, 3.4, 1.0, 2.05, cols=2, frame='alu', glass='glass0', seed=515, cheap=True)
    window(B, Rt, 2.6, 3.6, 3.55, 4.55, cols=2, frame='alu', glass='glass2', seed=516, cheap=True)
    window(B, Lm, -3.6, -2.6, 3.7, 4.55, cols=2, frame='alu', glass='glass1', seed=517, cheap=True, register=False)
    window(B, Ll, -3.0, -2.2, 1.0, 1.9, cols=1, frame='alu', glass='glass0', seed=518, cheap=True, register=False)
    # life by the walls
    meter_box(B, F, -W / 2 + 2.05, 1.15, w=0.32, h=0.44)
    ground_ac(B, (wg[0] - 0.55, -0.3, 0.0))
    pot(B, (wg[0] - 0.55, -0.3, 0.68), 0.12, 0.2, 'pot', 'grass', seed=519)
    garden_pine(B, (W / 2 - 0.35, -1.05, 0.0), seed=7)
    round_bin(B, (-W / 2 + 0.45, -0.42, 0.0))
    pot(B, (door_o[0] - 0.12, -0.75, 0.0), 0.14, 0.24, 'pot', 'grass', seed=520)
    pot(B, (door_o[1] + 0.45, -0.4, 0.0), 0.17, 0.3, 'pot3', 'bush', seed=521)
    gas_bottle(B, (W / 2 + 0.3, 4.2, 0.0), 'white')
    vent(B, Rt, 5.6, 2.2, 0.26)
    B.feat('front', 'patch', a=W / 2 - 0.9, b=1.4, w=0.26, h=0.15)
    return top + 0.11


# ---------------------------------------------------------------- HouseFlat
def house_flat(B):
    """A compact flat-roofed two-storey house: a concrete canopy over the door, a timber slat
    screen, a wide window under a fin, a balcony with a solid parapet and the washing out."""
    W, H, D = B.W, B.H, B.D
    door_o = (-3.05, -2.05, 0.12, 2.3)
    wg = (0.15, 3.25, 0.95, 2.25)
    ws = (-1.45, -0.75, 1.3, 2.25)
    slit = (-3.35, -2.8, 3.35, 5.45)
    bal = (-0.55, 3.05, 3.25, 5.4)
    side = [(2.8, 4.0, 1.0, 2.2), (2.8, 4.0, 3.6, 5.0)]
    F, Rt, Bk, Lf = town_shell(B, [door_o, wg, ws, slit, bal], gaps=[(door_o[0], door_o[1])], side=side, pp=0.45, ph=0.3,
                               coping_mat='alu')
    door(B, F, *door_o, mat='accent', glass=None, panels=((1, 3),), casing=False, name='Door')
    steps(B, F, door_o[0] - 0.3, door_o[1] + 0.35, [0.16], tread=0.6)
    put(B, F, fbox((-3.75, 2.45, 0.0), (-1.2, 2.63, 1.0), 0.03, 'conc'))
    B.feat('front', 'ao', a0=-3.75, a1=-1.2, b=2.45, length=0.6, k=0.55)
    lp, _ = lathe([(0.0, -0.03), (0.1, -0.03), (0.11, 0.0), (0.0, 0.0)], 8, ['lamp', 'white', 'white'])
    xform(lp, T(-2.55, -0.55, 2.45)); B.add(lp)
    B.lamps.append({'name': 'Lamp', 'center': [-2.55, -0.55, 2.4]})
    for x in np.linspace(-1.85, -1.55, 4):
        put(B, F, fbox((x - 0.025, 0.1, 0.06), (x + 0.025, 2.38, 0.12), 0.01, 'woodc'))
    mailbox(B, F, -1.1, 1.05, 'alud')
    window(B, F, *wg, cols=3, head=None, sill='trim', frame='alu', glass='glass1', seed=521)
    put(B, F, fbox((wg[0] - 0.2, wg[3] + 0.18, 0.0), (wg[1] + 0.2, wg[3] + 0.25, 0.5), 0.01, 'alu'))
    B.feat('front', 'ao', a0=wg[0] - 0.2, a1=wg[1] + 0.2, b=wg[3] + 0.18, length=0.3, k=0.4)
    window(B, F, *ws, cols=1, head=None, sill='trim', frame='alu', glass='glass0', seed=522, bars=3)
    window(B, F, *slit, cols=1, rows=3, head=None, sill=None, frame='alu', glass='glass2', seed=523)
    # the balcony: slab, parapet, the sliding doors behind, washing on a line
    bx0, bx1, bd = bal[0] - 0.4, bal[1] + 0.45, 0.95
    B.add(fbox((bx0, -bd, 2.98), (bx1, 0.0, 3.18), 0.03, 'conc', back=True))
    B.add(fbox((bx0, -bd, 3.18), (bx1, -bd + 0.15, 4.25), 0.02, 'wallw', back=True))
    for x0 in (bx0, bx1 - 0.15):
        B.add(fbox((x0, -bd + 0.15, 3.18), (x0 + 0.15, 0.0, 4.25), 0.02, 'wallw', back=True))
    B.add(fbox((bx0 - 0.02, -bd - 0.02, 4.25), (bx1 + 0.02, 0.0, 4.33), 0.015, 'alu', back=True))
    B.feat('front', 'ao', a0=bx0, a1=bx1, b=2.98, length=0.6, k=0.5)
    window(B, F, *bal, cols=2, head=None, sill=None, frame='alu', glass='glass1', seed=524, depth=0.12)
    for x in (bal[0] + 0.2, bal[1] - 0.2):
        put(B, F, tube([(x, 5.25, 0.0), (x, 5.25, 0.7)], 0.015, 'metal', 4))
    put(B, F, tube([(bal[0] + 0.2, 5.22, 0.68), (bal[1] - 0.2, 5.22, 0.68)], 0.018, 'metal', 5))
    laundry(B, F, bal[0] + 0.3, bal[1] - 0.3, 5.22, 0.68, seed=525, n=5)
    put(B, F, fbox((bal[0] - 0.1, bal[3], 0.0), (bal[1] + 0.1, bal[3] + 0.25, 0.22), 0.03, 'alu'))
    wall_pipe(B, W / 2 - 0.1, -0.08, H + 0.1, head=False)
    # sides and roof
    ac_unit(B, Rt, 1.4, 0.5, 0.0, w=0.76, h=0.54, d=0.3, brackets=False)
    meter_box(B, Rt, 0.6, 1.1)
    gas_bottle(B, (W / 2 + 0.3, 5.6, 0.0), 'white'); gas_bottle(B, (W / 2 + 0.3, 6.0, 0.0), 'white')
    for a, b, z0_, z1_ in side:
        window(B, Rt, a, b, z0_, z1_, cols=2, frame='alu', glass='glass0', seed=526, cheap=True)
        window(B, Lf, -b, -a, z0_, z1_, cols=2, frame='alu', glass='glass2', seed=527, cheap=True, register=False)
    flat_ac(B, 2.4, D - 1.2, H)
    dish(B, (-2.8, D - 0.6, H + 0.9), d=(0.3, -1, 0.5), r=0.32)
    B.add(tube([(-2.8, D - 0.45, H), (-2.8, D - 0.45, H + 0.9)], 0.03, 'metald', 5))
    pot(B, (-0.95, -0.35, 0.0), 0.2, 0.36, 'pot2', 'tall', seed=528, scale=1.2)
    pot(B, (-3.55, -0.4, 0.0), 0.15, 0.26, 'pot', 'flowers', seed=529)
    return H + 0.45 + 0.11


# ---------------------------------------------------------------- HouseCarport
def house_carport(B):
    """A two-storey house under a sideways gable (render below, boards above, storm-shutter boxes
    over the windows, a tiled hood over the door) with a carport of slim posts and a clear roof."""
    W, H, D, RH = B.W, B.H, B.D, B.RH
    xr = W / 2 - 3.3                       # the house's right wall; the carport beyond it
    xl = -W / 2
    hw = xr - xl
    t, cap = 0.16, 0.1
    k = (RH - t - cap) / (D / 2)
    apex = H + (D / 2) * k
    gf = 2.9
    ph = 0.35; v0 = ph - 0.05
    F = WF((0, 0, 0), (1, 0, 0), 'front')
    Rt = WF((xr, 0, 0), (0, 1, 0), 'right')
    Lf = WF((xl, 0, 0), (0, -1, 0), 'left')
    Bk = WF((0, D, 0), (-1, 0, 0), 'back')
    door_o = (xl + 0.65, xl + 1.6, 0.15, 2.3)
    wg = (xl + 2.6, xl + 5.0, 0.95, 2.2)
    wu = [(xl + 0.6, xl + 1.9, 3.35, 4.55), (xl + 3.0, xl + 5.6, 3.35, 4.55)]
    wall(B, F, xl, xr, gf, [door_o, wg], v0)
    wall(B, F, xl, xr, H, wu, gf, 'lap')
    wall(B, Rt, 0, D, gf, [(4.4, 5.4, 1.0, 2.0)], v0)
    wall(B, Rt, 0, D, [(0, H), (D / 2, apex), (D, H)], [(2.9, 4.0, 3.4, 4.5)], gf, 'lap')
    wall(B, Lf, -D, 0, gf, [(-4.2, -3.2, 1.0, 2.0)], v0)
    wall(B, Lf, -D, 0, [(-D, H), (-D / 2, apex), (0, H)], [], gf, 'lap')
    wall(B, Bk, -xr, -xl, gf, [], v0)
    wall(B, Bk, -xr, -xl, H, [], gf, 'lap')
    for x, y in ((xr, 0), (xl, 0), (xr, D), (xl, D)):
        corner_board(B, x, y, gf, H - 0.02)
    string_course(B, [(xl, D), (xl, 0.0), (xr, 0.0), (xr, D)], gf - 0.08, gf + 0.08, out=0.07)
    string_course(B, [(xr, D), (xl, D)], gf - 0.08, gf + 0.08, out=0.07)
    plinth(B, [(door_o[1], 0.0), (xr, 0.0), (xr, D), (xl, D), (xl, 0.0), (door_o[0], 0.0)], ph, mat='conc')
    e = 0.4
    a0, a1 = -e, D + e
    z0 = H - e * k
    top = pitched(B, 'x', a0, a1, xl - 0.32, xr + 0.32, z0, (D / 2 + e) * k, t=t)
    eave_gutter(B, [(xl - 0.37, a0 - 0.045), (xr + 0.37, a0 - 0.045)], z0 - 0.04)
    downpipe(B, [(xl - 0.22, a0 - 0.115, z0 - 0.15), (xl - 0.22, a0 - 0.115, z0 - 0.3), (xl - 0.075, 0.3, z0 - 0.75),
                 (xl - 0.075, 0.3, 0.32), (xl - 0.2, 0.3, 0.12)], brackets=[(xl - 0.075, 0.3, z) for z in (0.9, 2.6, 4.0)])
    antenna(B, xl + 1.5, D / 2, apex + 0.1, 1.6)
    B.feat('front', 'ao', a0=xl, a1=xr, b=H - 0.02, length=0.5, k=0.45)
    # door under a little tiled hood, windows (storm-shutter boxes above the upper ones)
    door(B, F, *door_o, mat='accent', glass=0.28, panels=((1, 2),), name='Door')
    steps(B, F, door_o[0] - 0.12, door_o[1] + 0.12, [0.3, 0.15])
    door_hood(B, F, (door_o[0] + door_o[1]) / 2, 1.6, 2.68, 0.4)
    lantern(B, F, door_o[1] + 0.35, 1.95)
    window(B, F, *wg, cols=3, transom=0.72, head='lintel', glass='glass1', frame='alu', seed=531)
    for kk, wo in enumerate(wu):
        window(B, F, *wo, cols=2, head=None, casing=True, frame='alu', glass=('glass2', 'glass0')[kk], seed=532 + kk)
        amado(B, F, wo[0], wo[1], wo[3] + 0.2)
    # a little balcony rail on the wide upper window, a futon airing over it
    rx0, rx1 = wu[1][0] - 0.1, wu[1][1] + 0.1
    put(B, F, fbox((rx0, 3.2, 0.0), (rx1, 3.28, 0.45), 0.01, 'alu'))
    put(B, F, tube([(rx0, 4.05, 0.42), (rx1, 4.05, 0.42)], 0.02, 'alu', 5))
    for x in np.linspace(rx0 + 0.02, rx1 - 0.02, 9):
        put(B, F, tube([(x, 3.28, 0.42), (x, 4.05, 0.42)], 0.011, 'alu', 4))
    fu = fbox((rx0 + 0.7, 3.45, 0.38), (rx0 + 2.0, 4.12, 0.46), 0.03, 'cloth2', back=True)
    put(B, F, fu)
    put(B, F, fbox((rx0 + 0.7, 4.06, 0.3), (rx0 + 2.0, 4.12, 0.5), 0.02, 'cloth2'))
    window(B, Rt, 4.4, 5.4, 1.0, 2.0, cols=2, frame='alu', glass='glass0', seed=534, cheap=True)
    window(B, Rt, 2.9, 4.0, 3.4, 4.5, cols=2, frame='alu', glass='glass2', seed=535, cheap=True)
    window(B, Lf, -4.2, -3.2, 1.0, 2.0, cols=2, frame='alu', glass='glass1', seed=536, cheap=True, register=False)
    # the carport: posts, beams, a clear ribbed roof, a slab, tyres and a hose in the back corner
    cx0, cx1, cy0, cy1 = xr + 0.08, W / 2, -0.75, D - 0.4
    for x in (cx1 - 0.12,):
        for y in (cy0 + 0.1, cy1 - 0.1):
            B.add(cbox2((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, 2.45), 0.01, 'alu'))
    B.add(cbox2((cx0, cy0 + 0.02, 2.38), (cx1, cy0 + 0.12, 2.52), 0.01, 'alu'))
    B.add(cbox2((cx1 - 0.16, cy0, 2.38), (cx1 - 0.06, cy1, 2.5), 0.01, 'alu'))
    shed(B, cx0 - 0.05, cx1 + 0.05, cy0 - 0.05, cy1 + 0.05, 2.62, 2.78, t=0.05, pitch=0.3, depth=0.025, mat='polyc', edge_mat='alu',
         fascia_mat='alu', soffit='polyc', flash_mat='alu', feat=False)
    B.add(box((cx0, cy0, 0.0), (cx1, cy1, 0.03), 'conc', skip=('-z',)))
    for kk in range(2):
        ty, _ = lathe([(0.2, 0.0), (0.3, 0.02), (0.31, 0.11), (0.3, 0.2), (0.2, 0.22)], 10, 'rubber')
        xform(ty, T(cx1 - 0.55, cy1 - 0.6, 0.03 + kk * 0.22)); B.add(ty)
    hose_reel(B, Rt, D - 1.4, 0.0)
    ac_unit(B, Rt, 2.2, 0.05, 0.0, w=0.76, h=0.54, d=0.3, brackets=False)
    meter_box(B, Rt, 1.0, 1.2)
    B.attach.append(('Carport', (round((cx0 + cx1) / 2, 3), 1.6, 0.0)))
    pot(B, (door_o[0] - 0.35, -0.4, 0.0), 0.18, 0.32, 'pot', 'flowers', seed=537)
    pot(B, (wg[1] + 0.35, -0.35, 0.0), 0.16, 0.3, 'pot3', 'bush', seed=538)
    gas_bottle(B, (xl - 0.3, 4.6, 0.0), 'white')
    return top + 0.11


def pal_town(pal):
    """The town's SPECS rows (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps)."""
    return [
        ('ShopKonbini', 10.0, 4.4, 10.0, 0.0, shop_konbini,
         pal((0.94, 0.94, 0.93), (0.62, 0.66, 0.70), (0.56, 0.55, 0.54)), 5.2, {}, {}),
        ('ShopMart', 9.0, 7.0, 9.0, 0.0, shop_mart,
         pal((0.93, 0.93, 0.91), (0.86, 0.30, 0.22), (0.56, 0.55, 0.54)), 7.8, {}, {'roofb': (-4.8, 4.8, -1.3, 0.2)}),
        ('ShopCafe', 7.0, 6.6, 8.0, 0.0, shop_cafe,
         pal((0.92, 0.91, 0.88), (0.24, 0.40, 0.42), (0.56, 0.55, 0.54), tile=(0.27, 0.28, 0.31)), 7.4, {'ppm': 48}, {}),
        ('ShopBooks', 6.5, 6.6, 8.0, 0.0, shop_books,
         pal((0.80, 0.62, 0.52), (0.18, 0.36, 0.30), (0.56, 0.55, 0.54)), 7.4, {'ppm': 48}, {}),
        ('ShopFlorist', 7.0, 6.4, 8.0, 0.0, shop_florist,
         pal((0.95, 0.93, 0.88), (0.36, 0.56, 0.38), (0.56, 0.55, 0.54)), 7.2, {}, {}),
        ('ShopNoodle', 6.5, 6.0, 8.0, 0.0, shop_noodle,
         pal((0.93, 0.90, 0.84), (0.30, 0.22, 0.18), (0.56, 0.55, 0.54)), 6.8, {}, {'roofb': (-3.6, 3.6, -1.2, 0.2)}),
        ('ShopTall', 5.5, 9.4, 9.0, 0.0, shop_tall,
         pal((0.84, 0.82, 0.78), (0.62, 0.64, 0.66), (0.56, 0.55, 0.54)), 10.2, {'ppm': 48}, {}),
        ('ShopBoutique', 5.0, 9.4, 9.0, 0.0, shop_boutique,
         pal((0.26, 0.28, 0.33), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 10.2, {'ppm': 48}, {}),
        ('HouseLeanTo', 8.4, 5.4, 7.0, 2.3, house_lean_to,
         pal((0.95, 0.95, 0.93), (0.46, 0.36, 0.30), (0.38, 0.40, 0.44)), 8.0, {}, {}),
        ('HouseFlat', 7.6, 6.0, 7.2, 0.0, house_flat,
         pal((0.88, 0.87, 0.84), (0.42, 0.34, 0.28), (0.56, 0.55, 0.54)), 6.7, {}, {}),
        ('HouseCarport', 10.0, 5.4, 7.0, 2.2, house_carport,
         pal((0.92, 0.90, 0.85), (0.32, 0.42, 0.52), (0.30, 0.33, 0.38)), 8.0, {}, {'roofb': (-4.9, -2.9, -1.1, 0.2)}),
    ]
