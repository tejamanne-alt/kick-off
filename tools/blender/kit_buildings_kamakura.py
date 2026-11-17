# Kamakura's street things and buildings for their own kit (kit_buildings.py --kit Kamakura), in the main kit's stylized
# look (as Florida's: kit_buildings_fl.py), after the views the user made for each in the Kamakura work that was cancelled
# (docs/LEARNINGS.md E12; the views are in the branch's history, review/kamakura/sheets and props, commit f8ff5d1). This is
# the first batch, a proof of the look before more is built: a two-storey stucco house under a kawara hip roof, the Enoden
# tram, a small vermilion torii, a little shrine on its stone base, the level crossing's signal and barrier, a convex
# corner mirror, recycling bins, the station's name board and its IC ticket gate.
#
# Same contract as the rest of the kit (kit_buildings.py): metres, Z up, the origin at the centre of the front wall's base,
# the street face looking along -Y, parts 1 wall / 2 accent / 3 roof. Real place names only on the signs (Hase, its
# neighbouring stations, Kamakura); the words and the stripes are painted here (paint(), through kit_buildings_atlas.EXTRA)
# into the kit's own 4096 x 4096 atlas.
import math
import numpy as np
from mathutils import Vector
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import decal, amado
from kit_buildings_cal import hip
import kit_buildings_signs as SG

# ---------------------------------------------------------------- the kit's own colours
# (appended to the shared table, so every other kit's material ids stay as they are)
KM_MAT = {
    'kmverm': (0, (0.86, 0.27, 0.15), 'white', 0.1), 'kmvermd': (0, (0.62, 0.18, 0.12), 'white', 0.1),
    'kmgreen': (0, (0.20, 0.45, 0.31), 'white', 0.1), 'kmgreend': (0, (0.13, 0.30, 0.21), 'white', 0.1),
    'kmcream': (0, (0.95, 0.90, 0.74), 'white', 0.1), 'kmyel': (0, (0.98, 0.79, 0.12), 'white', 0.05),
    'kmorange': (0, (0.96, 0.47, 0.14), 'white', 0.1), 'kmred': (0, (0.86, 0.12, 0.10), 'white', 0.0),
    'kmwood': (0, (0.58, 0.42, 0.29), 'white', 0.2), 'kmwoodd': (0, (0.33, 0.24, 0.18), 'white', 0.2),
    'kmstone': (0, (0.66, 0.64, 0.59), 'piece', 0.15), 'kmstoned': (0, (0.50, 0.49, 0.45), 'piece', 0.15),
    'kmmoss': (0, (0.47, 0.55, 0.33), 'white', 0.2), 'kmcopper': (0, (0.42, 0.62, 0.55), 'white', 0.1),
    'kmtile': (0, (0.34, 0.36, 0.40), 'white', 0.05), 'kmbin': (0, (0.93, 0.91, 0.85), 'white', 0.1),
    'kmblue': (0, (0.19, 0.43, 0.76), 'white', 0.05), 'kmcab': (0, (0.46, 0.38, 0.33), 'white', 0.15),
    'kmgrey': (0, (0.58, 0.60, 0.62), 'white', 0.1), 'kmgreyd': (0, (0.30, 0.31, 0.33), 'white', 0.1),
    'kmpaper': (0, (0.98, 0.98, 0.96), 'white', 0.0), 'kmrope': (0, (0.86, 0.78, 0.56), 'white', 0.1),
}
for _k, _v in KM_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1


# ---------------------------------------------------------------- the kit's tiles (allocated by kit_buildings.py)
TILES = [
    ('km_stripe', 256, 256), ('km_station', 768, 320), ('km_bin_can', 160, 224), ('km_bin_pet', 160, 224),
    ('km_bin_glass', 160, 224), ('km_dest', 384, 96), ('km_ic', 128, 128), ('km_mirror', 192, 192), ('km_lattice', 192, 192),
    ('km_arrow', 160, 96),
]


# ---------------------------------------------------------------- shared pieces
def tex_face(B, pts, region, expect, fn, mat='tex', shade=1.0):
    """One flat face mapped into an atlas tile by fn(co) -> (s, t)."""
    mb = MB()
    mb.face(pts, mat, expect, shade, lambda co: reg_uv(region, *fn(co), 0.0))
    B.add(mb.bm())


def striped_box(B, lo, hi, r=0.02):
    """A box painted in the crossing's yellow and black diagonal stripes on every side."""
    bm = cbox2(lo, hi, r, 'tex')
    uv_box(bm, bm.faces, 'km_stripe', 0.0)
    B.add(bm)


def banded_pole(B, x, y, z0, z1, r, band=0.32, mats=('kmyel', 'black'), sides=8):
    """A round post in bands of two colours (a crossing's yellow and black)."""
    n = max(1, int(round((z1 - z0) / band)))
    for k in range(n):
        za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
        B.add(tube([(x, y, za), (x, y, zb)], r, mats[k % 2], sides, caps=(k in (0, n - 1))))


def disc(B, c, r, normal, mat, n=12, depth=0.02):
    """A thin round plate facing `normal` (one of the axes), e.g. a lamp's lens."""
    pr, _ = lathe([(0.0, 0.0), (r, 0.0), (r, depth), (0.0, depth)], n, mat)
    nx, ny, nz = normal
    if abs(ny) > 0.5: xform(pr, R(-math.pi / 2 * (1 if ny > 0 else -1), 'X'))
    elif abs(nx) > 0.5: xform(pr, R(math.pi / 2 * (1 if nx > 0 else -1), 'Y'))
    xform(pr, T(*c)); B.add(pr)


def lantern_stone(B, x, y, s=1.0):
    """A small stone lantern (a toro): base, post, the light box with its windows, a pyramid cap and a finial."""
    def at(z): return z * s
    B.add(cbox2((x - 0.2 * s, y - 0.2 * s, 0.0), (x + 0.2 * s, y + 0.2 * s, at(0.14)), 0.02, 'kmstone'))
    B.add(tube([(x, y, at(0.14)), (x, y, at(0.62))], 0.08 * s, 'kmstone', 8))
    B.add(cbox2((x - 0.17 * s, y - 0.17 * s, at(0.62)), (x + 0.17 * s, y + 0.17 * s, at(0.7)), 0.01, 'kmstone'))
    B.add(cbox2((x - 0.13 * s, y - 0.13 * s, at(0.7)), (x + 0.13 * s, y + 0.13 * s, at(0.92)), 0.01, 'kmstone'))
    for dx, dy in ((0, -1), (0, 1)):
        B.add(box((x - 0.06 * s, y + dy * 0.132 * s - 0.004, at(0.75)), (x + 0.06 * s, y + dy * 0.132 * s + 0.004, at(0.87)), 'black'))
    cap, _ = lathe([(0.0, 0.0), (0.27 * s, 0.0), (0.24 * s, 0.05 * s), (0.05 * s, 0.2 * s), (0.0, 0.21 * s)], 4, 'kmstoned', phase=0.5)
    xform(cap, T(x, y, at(0.92))); B.add(cap)
    fin, _ = lathe([(0.0, 0.0), (0.04 * s, 0.0), (0.05 * s, 0.05 * s), (0.0, 0.11 * s)], 6, 'kmstoned')
    xform(fin, T(x, y, at(1.12))); B.add(fin)


# ================================================================ HouseKM: a two-storey stucco house, kawara hip roof
def house_km(B):
    """A Kamakura house of the 1990s (KM-B04): two storeys in beige stucco under a dark grey kawara hip roof, aluminium
    sliding windows (the upper ones under storm-shutter boxes, the ground floor's small one barred), a balcony with a
    slatted rail and the washing out over the front door, its step and its tin canopy, the meters and an AC unit by the
    walls, gutters and a downpipe."""
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    ph = 0.42; v0 = ph - 0.05
    door_o = (1.75, 2.75, ph, 2.45)
    win_big = (-3.4, -1.2, 0.8, 2.35)
    win_wc = (-0.35, 0.45, 1.45, 2.15)
    up = [(-3.25, -1.85, 3.55, 4.85), (-0.95, 0.45, 3.55, 4.85)]
    bal_door = (1.4, 3.5, 3.0, 5.05)
    wall(B, F, -W / 2 + c, W / 2 - c, H, [door_o, win_big, win_wc] + up + [bal_door], v0)
    side_r = [(1.4, 2.6, 1.0, 2.2), (4.6, 5.6, 3.6, 4.7)]
    wall(B, Rt, c, D - c, H, side_r, v0)
    wall(B, Lf, -D + c, -c, H, [(-b, -a, z0, z1) for a, b, z0, z1 in side_r], v0)
    wall(B, Bk, -W / 2 + c, W / 2 - c, H, [(-2.5, -1.0, 3.6, 4.7)], v0)
    box_shell_corners(B, v0, H, c)
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.04, mat='conc', closed=closed)
    # a thin band where the upper floor's slab is (the stucco's one seam)
    string_course(B, u_path(B), 2.86, 2.93, out=0.03, mat='trim')
    top = hip(B, -W / 2, W / 2, 0.0, D, H, RH, over=0.6, t=0.13, mat='roof', edge='roofw')
    B.feats['roof'][-1][1]['kawara'] = True            # (even grey kawara, not the Spanish clay's blend)
    eave_gutter(B, [(-W / 2 - 0.62, -0.62), (W / 2 + 0.62, -0.62)], H + 0.02, size=0.11)
    downpipe(B, [(W / 2 + 0.5, -0.66, H - 0.05), (W / 2 + 0.5, -0.66, H - 0.25), (W / 2 + 0.07, -0.12, H - 0.6),
                 (W / 2 + 0.07, -0.12, 0.35), (W / 2 + 0.2, -0.2, 0.1)], r=0.045, brackets=[(W / 2 + 0.07, -0.12, 1.6), (W / 2 + 0.07, -0.12, 3.8)])
    # windows: aluminium sliding sashes
    window(B, F, *win_big, cols=2, head=None, sill='trimw', frame='alu', glass='glass1', seed=701)
    amado(B, F, win_big[0], win_big[1], win_big[3])
    window(B, F, *win_wc, cols=1, head=None, sill='trimw', frame='alu', glass='glass0', seed=702, bars=4)
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, head=None, sill='trimw', frame='alu', glass=('glass2', 'glass0')[k], seed=703 + k)
        amado(B, F, wo[0], wo[1], wo[3])
    window(B, F, *bal_door, cols=2, head=None, sill=None, frame='alu', glass='glass1', seed=706)
    amado(B, F, bal_door[0], bal_door[1], bal_door[3])
    for wf, ops in ((Rt, side_r), (Lf, [(-b, -a, z0, z1) for a, b, z0, z1 in side_r])):
        for k, wo in enumerate(ops):
            window(B, wf, *wo, cols=2, frame='alu', glass='glass0', seed=710 + k, cheap=True, register=False)
    window(B, Bk, -2.5, -1.0, 3.6, 4.7, cols=2, frame='alu', glass='glass0', seed=714, cheap=True, register=False)
    # the balcony over the front door: its slab, a slatted aluminium rail, the washing
    bx0, bx1, by0 = 1.2, W / 2 - 0.05, -1.0
    B.add(cbox2((bx0, by0, 2.86), (bx1, 0.0, 3.02), 0.02, 'trim'))
    B.add(cbox2((bx0, by0, 3.02), (bx0 + 0.05, by0 + 0.05, 4.0), 0.01, 'alu'))
    B.add(cbox2((bx1 - 0.05, by0, 3.02), (bx1, by0 + 0.05, 4.0), 0.01, 'alu'))
    B.add(cbox2((bx0, by0, 3.94), (bx1, by0 + 0.06, 4.02), 0.01, 'alu'))
    B.add(cbox2((bx0, by0, 3.06), (bx1, by0 + 0.05, 3.1), 0.005, 'alu'))
    for x in np.arange(bx0 + 0.12, bx1 - 0.08, 0.11):
        B.add(box((float(x) - 0.018, by0 + 0.01, 3.1), (float(x) + 0.018, by0 + 0.035, 3.94), 'alu'))
    for side_x in (bx0, bx1 - 0.05):
        B.add(cbox2((side_x, by0, 3.02), (side_x + 0.05, 0.0, 3.08), 0.005, 'alu'))
    laundry(B, F, bx0 + 0.25, bx1 - 0.25, 4.45, 0.55, seed=707, n=4)
    # the front door, its step and canopy (under the balcony, so a short tin hood)
    door(B, F, *door_o, mat='accent', glass=0.32, panels=((1, 2),), casing=False, name='Door')
    steps(B, F, door_o[0] - 0.2, door_o[1] + 0.2, [0.15, 0.3], tread=0.32)
    # the street's life by the walls
    meter_box(B, F, -0.95, 1.05, w=0.3, h=0.42)
    meter_box(B, F, -0.95, 1.55, w=0.24, h=0.3)
    ac_unit(B, F, -2.3, 0.0, z=0.0, brackets=False)
    vent(B, F, 0.9, 2.45, 0.2)
    B.feat('front', 'patch', a=-W / 2 + 0.8, b=0.9, w=0.3, h=0.2)
    return top + 0.1


# ================================================================ TramKM: the Enoden's green and cream car
def tram_km(B):
    """The Enoden's car (KM-V01): its lower body green, a cream band with the windows, a green line under the roof, the
    ends rounded off in plan with their two big windows, headlights and the destination sign; two pairs of doors a side,
    two bogies, the pantograph and the roof's equipment boxes. Seen side-on by the game: its length along x."""
    Lt, Dp = B.W, B.D
    c = 0.42
    x0, x1 = -Lt / 2, Lt / 2

    def plan(ins=0.0):
        a0, a1, b0, b1 = x0 + ins, x1 - ins, ins, Dp - ins
        return [(a0 + c, b0), (a1 - c, b0), (a1, b0 + c), (a1, b1 - c), (a1 - c, b1), (a0 + c, b1), (a0, b1 - c), (a0, b0 + c)]
    B.add(prism(plan(0.08), 0.55, 0.78, 'kmgreend', caps=(True, False)))            # the skirt, set in
    B.add(prism(plan(), 0.78, 1.86, 'kmgreen', caps=(False, False)))               # the lower body
    B.add(prism(plan(), 1.86, 2.95, 'kmcream', caps=(False, False)))               # the window band
    B.add(prism(plan(), 2.95, 3.25, 'kmgreen', caps=(False, False)))               # the line under the roof
    B.add(prism(plan(0.03), 3.25, 3.38, 'kmgrey', caps=(False, True)))             # the roof
    B.add(prism(plan(0.25), 3.38, 3.44, 'kmgrey', caps=(False, True)))             # its crown
    # the sides: windows along the band, two pairs of doors
    doors = (-2.7, 2.7)
    Fr = WF((0, 0, 0), (1, 0, 0), 'front')
    Bk = WF((0, Dp, 0), (-1, 0, 0), 'back')
    xs = [x for x in np.arange(x0 + c + 0.7, x1 - c - 0.5, 1.05)]
    for wf, sgn in ((Fr, 1), (Bk, -1)):
        for x in xs:
            if any(abs(x - d) < 0.95 for d in doors): continue
            decal(B, wf, sgn * x - 0.42, sgn * x + 0.42, 2.0, 2.78, 0.012, 'glass1', mat='glass')
        for d in doors:
            u = sgn * d
            put(B, wf, fbox((u - 0.5, 0.86, 0.0), (u + 0.5, 2.82, 0.03), 0.01, 'kmgreend'))
            decal(B, wf, u - 0.4, u - 0.03, 1.95, 2.7, 0.04, 'glass0', mat='glass')
            decal(B, wf, u + 0.03, u + 0.4, 1.95, 2.7, 0.04, 'glass0', mat='glass')
            put(B, wf, fbox((u - 0.52, 0.52, -0.02), (u + 0.52, 0.6, 0.12), 0.01, 'kmgreyd'))  # the step
    # the ends: two big windows, the destination sign over them, headlights and tail lights, a coupler
    for sx in (-1, 1):
        ex = sx * x1
        E = WF((ex, Dp if sx < 0 else 0.0, 0), (0, sx, 0), 'right' if sx > 0 else 'left')
        lo, hi = c + 0.05, Dp - c - 0.05
        mid = (lo + hi) / 2
        u = lambda y: (y if sx > 0 else Dp - y)
        for a, b in ((lo, mid - 0.04), (mid + 0.04, hi)):
            ua, ub = sorted((u(a), u(b)))
            decal(B, E, ua, ub, 1.95, 2.85, 0.01, 'glass2', mat='glass')
        tex_face(B, [(ex + sx * 0.015, mid - 0.45, 2.98), (ex + sx * 0.015, mid + 0.45, 2.98),
                     (ex + sx * 0.015, mid + 0.45, 3.2), (ex + sx * 0.015, mid - 0.45, 3.2)], 'km_dest', (sx, 0, 0),
                 lambda co, sx=sx, mid=mid: ((0.5 + sx * (co.y - mid) / 0.9) if sx > 0 else (0.5 - (co.y - mid) / 0.9), (co.z - 2.98) / 0.22))
        for y in (0.6, Dp - 0.6):
            disc(B, (ex, y, 1.3), 0.12, (sx, 0, 0), 'lamp')
            disc(B, (ex, y + (0.22 if y < 1 else -0.22), 1.3), 0.06, (sx, 0, 0), 'kmred')
        B.add(cbox2((ex - (0.0 if sx > 0 else 0.35), mid - 0.12, 0.62), (ex + (0.35 if sx > 0 else 0.0), mid + 0.12, 0.8), 0.02, 'metald'))
    # the bogies under the ends, their wheels
    for bx in (-3.9, 3.9):
        B.add(cbox2((bx - 1.15, 0.28, 0.32), (bx + 1.15, Dp - 0.28, 0.62), 0.04, 'metald'))
        for wx in (bx - 0.68, bx + 0.68):
            for y in (0.2, Dp - 0.2):
                B.add(tube([(wx, y - 0.06, 0.36), (wx, y + 0.06, 0.36)], 0.34, 'rubber', 12))
                B.add(tube([(wx, y - 0.075 if y < 1 else y + 0.075, 0.36), (wx, y - 0.065 if y < 1 else y + 0.065, 0.36)], 0.12, 'metal', 8))
        B.add(cbox2((bx - 0.25, 0.12, 0.42), (bx + 0.25, 0.3, 0.58), 0.02, 'black'))
    # on the roof: two equipment boxes, the pantograph's base, arms and pan
    B.add(cbox2((-3.0, 0.55, 3.42), (-1.5, Dp - 0.55, 3.66), 0.04, 'kmgrey'))
    B.add(cbox2((1.6, 0.6, 3.42), (2.8, Dp - 0.6, 3.62), 0.04, 'kmgrey'))
    for y in (0.75, Dp - 0.75):
        for x in (-0.75, 0.75):
            ins, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.06), (0.05, 0.12), (0.0, 0.13)], 6, 'white')
            xform(ins, T(x, y, 3.44)); B.add(ins)
        B.add(tube([(-0.75, y, 3.6), (0.0, y, 4.15), (0.75, y, 3.6)], 0.025, 'metald', 5, caps=False))
        B.add(tube([(-0.45, y, 4.75), (0.0, y, 4.15), (0.45, y, 4.75)], 0.02, 'metald', 5, caps=False))
    B.add(tube([(-0.75, 0.75, 3.6), (-0.75, Dp - 0.75, 3.6)], 0.03, 'metald', 5))
    B.add(tube([(0.75, 0.75, 3.6), (0.75, Dp - 0.75, 3.6)], 0.03, 'metald', 5))
    for x in (-0.45, 0.45):
        B.add(tube([(x, 0.75, 4.75), (x, Dp - 0.75, 4.75)], 0.02, 'metald', 5))
    B.add(tube([(0.0, 0.35, 4.82), (0.0, Dp - 0.35, 4.82)], 0.04, 'kmgreyd', 6))
    for y in (0.35, Dp - 0.35):
        B.add(tube([(0.0, y, 4.82), (0.0, y + (-0.18 if y < 1 else 0.18), 4.72)], 0.03, 'kmgreyd', 5))
    B.attach.append(('Roof', (0.0, Dp / 2, 3.44)))
    return 4.88


# ================================================================ ToriiKM: a small vermilion torii
def torii_km(B):
    """A small vermilion torii (KM-A11): two round pillars on black bases, the tie beam through them, the upper lintel
    with its black top sweeping up at both ends, and the tablet strut between them."""
    W = B.W
    y = 0.16
    px = W / 2 - 0.42
    for sx in (-1, 1):
        x = sx * px
        B.add(tube([(x, y, 0.0), (x, y, 0.32)], 0.14, 'black', 10))
        B.add(tube([(x, y, 0.3), (x, y, 2.3)], 0.11, 'kmverm', 10))
    # the tie beam (nuki), running through the pillars and a little beyond
    B.add(cbox2((-px - 0.32, y - 0.06, 1.78), (px + 0.32, y + 0.06, 1.92), 0.01, 'kmverm'))
    # the strut in the middle and the lower lintel (shimaki)
    B.add(cbox2((-0.07, y - 0.05, 1.92), (0.07, y + 0.05, 2.22), 0.01, 'kmverm'))
    B.add(cbox2((-px - 0.36, y - 0.08, 2.22), (px + 0.36, y + 0.08, 2.36), 0.01, 'kmverm'))
    # the top lintel (kasagi): its ends sweep up; its top in black
    xs = np.linspace(-W / 2, W / 2, 15)
    lift = lambda x: 0.13 * (abs(x) / (W / 2)) ** 2.4
    path = [(float(x), y, 2.44 + lift(x)) for x in xs]
    B.add(sweep(path, (0, 0, 1), [(-0.07, -0.1), (0.07, -0.1), (0.07, 0.1), (-0.07, 0.1)], 'kmverm'))
    path_top = [(float(x), y, 2.55 + lift(x) * 1.15) for x in np.linspace(-W / 2 - 0.05, W / 2 + 0.05, 15)]
    B.add(sweep(path_top, (0, 0, 1), [(-0.05, -0.12), (0.05, -0.12), (0.05, 0.12), (-0.05, 0.12)], 'black'))
    return 2.75


# ================================================================ ShrineKM: a little shrine on its stone base
def shrine_km(B):
    """A little roadside shrine (KM-B05): a stepped base of stone with steps up the middle, two stone lanterns, and on
    top the wooden shrine with its lattice doors under a copper roof (the crossed rafters at its ends, logs on its ridge),
    a twisted straw rope with its white paper streamers across the front, and an offering box."""
    W, D = B.W, B.D
    # the base: a lower tier of stone and an upper one, a stair up the middle of the front
    B.add(cbox2((-W / 2, 0.0, 0.0), (W / 2, D, 0.62), 0.03, 'kmstone'))
    B.add(cbox2((-W / 2 + 0.02, -0.02, 0.0), (W / 2 - 0.02, D + 0.02, 0.1), 0.02, 'kmstoned'))
    # courses of blocks proud of the lower tier's face, uneven
    rng = np.random.default_rng(3)
    for row, z in enumerate((0.1, 0.3, 0.46)):
        x = -W / 2 + (0.2 if row % 2 else 0.0)
        while x < W / 2 - 0.1:
            w = float(rng.uniform(0.38, 0.62))
            if abs(x + w / 2) > 0.95:
                B.add(cbox2((x + 0.02, -0.025, z + 0.01), (min(x + w, W / 2) - 0.02, 0.0, z + 0.15), 0.015, 'kmstone' if rng.random() < 0.7 else 'kmstoned'))
            x += w
    ux0, ux1, uy0, uy1 = -1.55, 1.55, 0.9, D - 0.25
    B.add(cbox2((ux0, uy0, 0.62), (ux1, uy1, 1.02), 0.03, 'kmstone'))
    B.add(cbox2((ux0 - 0.06, uy0 - 0.06, 0.62), (ux1 + 0.06, uy1 + 0.06, 0.68), 0.02, 'kmmoss'))
    # the stair: from the street to the upper tier, between low stone cheeks
    n = 6
    for k in range(n):
        y0 = -0.9 + k * (uy0 + 0.9) / n
        B.add(cbox2((-0.62, y0, 0.0), (0.62, uy0, (k + 1) * 1.02 / n), 0.015, 'kmstone' if k % 2 else 'kmstoned'))
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.62, sx * 0.78))
        B.add(cbox2((xa, -0.9, 0.0), (xb, uy0, 0.25), 0.02, 'kmstoned'))
    # the lanterns either side, on the upper tier
    for sx in (-1, 1):
        lantern_stone(B, sx * 1.22, uy0 + 0.4, s=1.35)
    # the shrine: a raised floor on posts, the body, its doors, the roof
    sx0, sx1, sy0, sy1, zf = -0.8, 0.8, uy0 + 0.6, uy0 + 1.95, 1.02
    for x in (sx0 + 0.06, sx1 - 0.06):
        for yy in (sy0 + 0.06, sy1 - 0.06):
            B.add(cbox2((x - 0.05, yy - 0.05, zf), (x + 0.05, yy + 0.05, zf + 0.3), 0.01, 'kmwoodd'))
    B.add(cbox2((sx0 - 0.12, sy0 - 0.2, zf + 0.3), (sx1 + 0.12, sy1 + 0.08, zf + 0.38), 0.01, 'kmwood'))
    zb0, zb1 = zf + 0.38, zf + 1.55
    B.add(cbox2((sx0, sy0, zb0), (sx1, sy1, zb1), 0.01, 'kmwood'))
    for x in (sx0, sx1):
        for yy in (sy0, sy1):
            B.add(cbox2((x - 0.05, yy - 0.05, zb0), (x + 0.05, yy + 0.05, zb1 + 0.04), 0.01, 'kmwoodd'))
    tex_face(B, [(sx0 + 0.08, sy0 - 0.012, zb0 + 0.08), (sx1 - 0.08, sy0 - 0.012, zb0 + 0.08),
                 (sx1 - 0.08, sy0 - 0.012, zb1 - 0.12), (sx0 + 0.08, sy0 - 0.012, zb1 - 0.12)], 'km_lattice', (0, -1, 0),
             lambda co: ((co.x - sx0 - 0.08) / (sx1 - sx0 - 0.16), (co.z - zb0 - 0.08) / (zb1 - zb0 - 0.2)))
    B.add(cbox2((sx0 - 0.04, sy0 - 0.06, zb1 - 0.12), (sx1 + 0.04, sy0, zb1 - 0.06), 0.01, 'kmwoodd'))
    # the roof: a gable along the depth, its front a deep overhang over the doors, copper green
    ov = 0.35
    rx0, rx1, ry0, ry1, ze, apex = sx0 - ov, sx1 + ov, sy0 - 0.75, sy1 + 0.3, zb1 + 0.04, zb1 + 0.62
    mb = MB()
    for side in (-1, 1):
        xe = rx0 if side < 0 else rx1
        pts = [(xe, ry0, ze), (xe, ry1, ze), (0.0, ry1, apex), (0.0, ry0, apex)]
        if side > 0: pts = [(xe, ry1, ze), (xe, ry0, ze), (0.0, ry0, apex), (0.0, ry1, apex)]
        mb.face(pts, 'kmcopper', (side, 0, 1), 1.0)
        under = [(p[0], p[1], p[2] - 0.06) for p in reversed(pts)]
        mb.face(under, 'kmwoodd', (-side, 0, -1), 0.6)
    for yy, wy, e in ((ry0, sy0 - 0.002, (0, -1, 0)), (ry1, sy1 + 0.002, (0, 1, 0))):
        mb.face([(rx0, yy, ze - 0.06), (rx0, yy, ze), (0.0, yy, apex), (0.0, yy, apex - 0.06)], 'kmcopper', e, 0.75)
        mb.face([(rx1, yy, ze - 0.06), (0.0, yy, apex - 0.06), (0.0, yy, apex), (rx1, yy, ze)], 'kmcopper', e, 0.75)
        # the gable's wooden triangle under the roof, on the shrine's own front and back walls
        mb.face([(sx0, wy, zb1), (sx1, wy, zb1), (0.0, wy, apex - 0.1)], 'kmwood', e, 0.9)
    B.add(mb.bm())
    B.add(cbox2((-0.06, ry0 - 0.02, apex - 0.02), (0.06, ry1 + 0.02, apex + 0.08), 0.01, 'kmcopper'))
    for yy in (ry0 + 0.15, (ry0 + ry1) / 2, ry1 - 0.2):
        B.add(tube([(0.0, yy - 0.05, apex + 0.12), (0.0, yy + 0.05, apex + 0.12)], 0.05, 'kmwood', 6))
    for yy in (ry0, ry1):                          # the crossed rafters (chigi) at both ends
        for sx in (-1, 1):
            B.add(tube([(sx * 0.22, yy, apex - 0.22), (-sx * 0.12, yy, apex + 0.28)], 0.03, 'kmwoodd', 4))
    # the rope across the front with its paper streamers, the offering box
    rope = [(sx0 - 0.25 + 0.0, sy0 - 0.62, zb1 - 0.1)] + [(x, sy0 - 0.62, zb1 - 0.1 - 0.1 * math.sin(math.pi * (x - sx0 + 0.25) / (sx1 - sx0 + 0.5)))
                                                          for x in np.linspace(sx0 - 0.15, sx1 + 0.15, 7)] + [(sx1 + 0.25, sy0 - 0.62, zb1 - 0.1)]
    B.add(tube(rope, 0.04, 'kmrope', 6))
    for x in (-0.45, 0.0, 0.45):                   # the paper streamers (shide): slim white zigzags
        zt = zb1 - 0.2
        zig = [(x - 0.03, zt), (x + 0.03, zt - 0.05), (x - 0.03, zt - 0.1), (x + 0.03, zt - 0.15), (x - 0.02, zt - 0.2)]
        for (ax, az), (bx_, bz) in zip(zig[:-1], zig[1:]):
            mb2 = MB(); mb2.face([(ax - 0.015, sy0 - 0.63, az), (ax + 0.015, sy0 - 0.63, az), (bx_ + 0.015, sy0 - 0.63, bz), (bx_ - 0.015, sy0 - 0.63, bz)], 'kmpaper', (0, -1, 0), 1.0)
            mb2.face([(bx_ - 0.015, sy0 - 0.62, bz), (bx_ + 0.015, sy0 - 0.62, bz), (ax + 0.015, sy0 - 0.62, az), (ax - 0.015, sy0 - 0.62, az)], 'kmpaper', (0, 1, 0), 0.8)
            B.add(mb2.bm())
    B.add(cbox2((-0.32, sy0 - 0.62, 1.02), (0.32, sy0 - 0.3, 1.32), 0.02, 'kmwoodd'))
    for k in range(5):
        B.add(box((-0.3 + 0.06 + k * 0.12 - 0.02, sy0 - 0.61, 1.321), (-0.3 + 0.06 + k * 0.12 + 0.02, sy0 - 0.31, 1.33), 'black'))
    return apex + 0.4


# ================================================================ the level crossing
def crossing_signal(B):
    """A level crossing's warning post (KM-A05): a post in yellow and black bands, the crossbuck at its top, under it the
    pair of red lamps with their hoods (both ways), the direction arrow and the bell, its cabinet at the foot."""
    y = 0.3
    striped_box(B, (-0.24, y - 0.2, 0.0), (0.24, y + 0.2, 0.62))
    banded_pole(B, 0.0, y, 0.62, 3.25, 0.06)
    # the crossbuck: two boards crossed, yellow with a black edge
    for ang in (math.pi / 4, -math.pi / 4):
        for mat, w, h, dz in (('black', 1.05, 0.2, 0.0), ('kmyel', 0.98, 0.14, 0.012)):
            bd = cbox((w, 0.03 + dz, h), 0.01, mat)
            xform(bd, R(ang, 'Y')); xform(bd, T(0.0, y - 0.07 - dz, 3.2)); B.add(bd)
    # the lamps: a bar across the post, a red lamp each end facing each way, their hoods
    B.add(cbox2((-0.5, y - 0.04, 2.48), (0.5, y + 0.04, 2.56), 0.01, 'black'))
    for sx in (-1, 1):
        cx = sx * 0.36
        B.add(cbox2((cx - 0.17, y - 0.07, 2.36), (cx + 0.17, y + 0.07, 2.7), 0.02, 'black'))
        for fy in (-1, 1):
            disc(B, (cx, y + fy * 0.07, 2.53), 0.12, (0, fy, 0), 'kmred', depth=0.03)
            hood = [(cx - 0.15, y + fy * 0.08, 2.68), (cx + 0.15, y + fy * 0.08, 2.68), (cx + 0.15, y + fy * 0.26, 2.62), (cx - 0.15, y + fy * 0.26, 2.62)]
            hb = MB(); hb.face(hood, 'black', (0, 0, 1), 0.8); hb.face(list(reversed(hood)), 'black', (0, 0, -1), 0.6); B.add(hb.bm())
    # the direction arrow and the bell
    B.add(cbox2((-0.24, y - 0.09, 1.92), (0.24, y + 0.09, 2.18), 0.02, 'black'))
    tex_face(B, [(-0.2, y - 0.095, 1.95), (0.2, y - 0.095, 1.95), (0.2, y - 0.095, 2.15), (-0.2, y - 0.095, 2.15)], 'km_arrow', (0, -1, 0),
             lambda co: ((co.x + 0.2) / 0.4, (co.z - 1.95) / 0.2))
    B.add(cbox2((-0.14, y - 0.12, 1.45), (0.14, y + 0.12, 1.72), 0.03, 'kmgrey'))
    for k in range(4):
        B.add(box((-0.1, y - 0.125, 1.5 + k * 0.05), (0.1, y - 0.12, 1.52 + k * 0.05), 'black'))
    return 3.6


def crossing_barrier(B):
    """The crossing's barrier (KM-A04): its machine in yellow and black stripes on a plinth, and the arm, striped, raised."""
    y = 0.3
    B.add(cbox2((-0.32, y - 0.26, 0.0), (0.32, y + 0.26, 0.1), 0.02, 'conc'))
    striped_box(B, (-0.22, y - 0.18, 0.1), (0.22, y + 0.18, 1.05), r=0.04)
    B.add(cbox2((-0.25, y - 0.2, 1.05), (0.25, y + 0.2, 1.12), 0.02, 'black'))
    hub = Vector((0.0, y - 0.24, 0.95))
    B.add(tube([(0.0, y - 0.18, 0.95), (0.0, y - 0.28, 0.95)], 0.08, 'black', 10))
    # the arm, raised to about 80 degrees, in yellow and black segments, its counterweight behind the hub
    ang = math.radians(80.0)
    d = Vector((math.cos(ang), 0.0, math.sin(ang)))
    L, n = 3.5, 10
    for k in range(n):
        a = hub + d * (L * k / n); b = hub + d * (L * (k + 1) / n)
        B.add(tube([tuple(a), tuple(b)], 0.04, ('kmyel', 'black')[k % 2], 6, caps=(k in (0, n - 1))))
    B.add(cbox2(tuple(hub - d * 0.45 - Vector((0.09, 0.07, 0.09))), tuple(hub - d * 0.2 + Vector((0.09, 0.07, 0.09))), 0.02, 'black'))
    B.attach.append(('Hub', tuple(hub)))
    return float((hub + d * L).z) + 0.05


# ================================================================ street things
def mirror_km(B):
    """A convex corner mirror (KM-A03): an orange post that bends toward the street at its top, the round mirror in its
    orange rim and the little hood over it."""
    y = 0.22
    B.add(cbox2((-0.08, y - 0.08, 0.0), (0.08, y + 0.08, 0.06), 0.01, 'kmorange'))
    path = [(0.0, y, 0.0), (0.0, y, 2.9)] + [(0.0, y - 0.2 * math.sin(math.pi / 2 * k / 5), 2.9 + 0.3 * math.sin(math.pi / 2 * k / 5)) for k in range(1, 6)]
    B.add(tube(path, 0.035, 'kmorange', 8))
    cy, cz = y - 0.24, 3.38
    rim, _ = lathe([(0.0, 0.0), (0.4, 0.0), (0.4, 0.06), (0.0, 0.06)], 20, 'kmorange')
    xform(rim, R(math.pi / 2, 'X')); xform(rim, T(0.0, cy + 0.03, cz)); B.add(rim)
    face, _ = lathe([(0.0, 0.07), (0.15, 0.06), (0.28, 0.03), (0.36, 0.0)], 20, 'tex')
    xform(face, R(math.pi / 2, 'X')); xform(face, T(0.0, cy - 0.0, cz))
    lu = L(face)[3]
    for f in face.faces:
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv('km_mirror', 0.5 + co.x / 0.8, 0.5 + (co.z - cz) / 0.8, 0.02)
    B.add(face)
    hood = [(-0.36, cy - 0.02, cz + 0.42), (0.36, cy - 0.02, cz + 0.42), (0.36, cy - 0.22, cz + 0.36), (-0.36, cy - 0.22, cz + 0.36)]
    hb = MB(); hb.face(hood, 'kmorange', (0, 0, 1), 0.9); hb.face(list(reversed(hood)), 'kmorange', (0, 0, -1), 0.6); B.add(hb.bm())
    return cz + 0.45


def recycle_km(B):
    """Recycling bins by the vending machines (KM-A20): three cream bins with lids in their colours, a round hole or
    two in each and the label on each front (cans, plastic bottles, glass)."""
    W = B.W
    w = W / 3
    for k, (lid, region) in enumerate((('kmorange', 'km_bin_can'), ('kmblue', 'km_bin_pet'), ('kmbin', 'km_bin_glass'))):
        x0 = -W / 2 + k * w + 0.015; x1 = x0 + w - 0.03
        B.add(cbox2((x0, 0.0, 0.0), (x1, 0.48, 0.86), 0.03, 'kmbin'))
        B.add(cbox2((x0 - 0.01, -0.01, 0.86), (x1 + 0.01, 0.49, 0.98), 0.03, lid))
        holes = ((x0 + x1) / 2,) if k == 1 else ((x0 + x1) / 2 - 0.1, (x0 + x1) / 2 + 0.1)
        for hx in holes:
            if k == 1:
                B.add(box((hx - 0.13, 0.17, 0.981), (hx + 0.13, 0.27, 0.985), 'black'))
            else:
                h_, _ = lathe([(0.0, 0.0), (0.055, 0.0), (0.0, 0.004)], 10, 'black')
                xform(h_, T(hx, 0.24, 0.981)); B.add(h_)
        tex_face(B, [(x0 + 0.03, -0.012, 0.3), (x1 - 0.03, -0.012, 0.3), (x1 - 0.03, -0.012, 0.8), (x0 + 0.03, -0.012, 0.8)], region, (0, -1, 0),
                 lambda co, x0=x0, x1=x1: ((co.x - x0 - 0.03) / (x1 - x0 - 0.06), (co.z - 0.3) / 0.5))
    return 1.0


def station_sign(B):
    """The station's name board (KM-A29): a white board on two grey posts, the station's name in kanji and its
    reading, the neighbouring stations either way on a green band (Hase: Gokurakuji and Yuigahama)."""
    W = B.W
    y = 0.08
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.08)
        B.add(tube([(x, y, 0.0), (x, y, 2.08)], 0.04, 'galvw', 8))
    B.add(tube([(-W / 2 + 0.08, y, 2.08), (W / 2 - 0.08, y, 2.08)], 0.035, 'galvw', 8))
    bx0, bx1, bz0, bz1 = -W / 2 + 0.16, W / 2 - 0.16, 1.18, 1.98
    B.add(cbox2((bx0, y - 0.03, bz0), (bx1, y + 0.03, bz1), 0.01, 'whitep'))
    for yy, e, flip in ((y - 0.032, (0, -1, 0), False), (y + 0.032, (0, 1, 0), True)):
        pts = [(bx0 + 0.02, yy, bz0 + 0.02), (bx1 - 0.02, yy, bz0 + 0.02), (bx1 - 0.02, yy, bz1 - 0.02), (bx0 + 0.02, yy, bz1 - 0.02)]
        tex_face(B, pts, 'km_station', e, lambda co, flip=flip: ((co.x - bx0) / (bx1 - bx0) if not flip else 1 - (co.x - bx0) / (bx1 - bx0), (co.z - bz0) / (bz1 - bz0)))
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.08)
        for z in (bz0 + 0.12, bz1 - 0.12):
            B.add(tube([(x, y, z), (x - sx * 0.1, y, z)], 0.02, 'galvw', 5))
    return 2.14


def ticket_gate(B):
    """An unstaffed station's IC card gate (KM-A28): a narrow cabinet, its reader on top with the card target and the
    small screen, the short flaps either side."""
    y0, y1 = 0.0, B.D
    B.add(cbox2((-0.16, y0, 0.0), (0.16, y1, 0.86), 0.03, 'kmcab'))
    B.add(cbox2((-0.17, y0 - 0.01, 0.0), (0.17, y1 + 0.01, 0.08), 0.02, 'kmgreyd'))
    B.add(cbox2((-0.15, y0 + 0.02, 0.86), (0.15, y0 + 0.32, 1.0), 0.03, 'kmgrey'))
    tex_face(B, [(-0.11, y0 + 0.06, 1.003), (0.11, y0 + 0.06, 1.003), (0.11, y0 + 0.28, 1.003), (-0.11, y0 + 0.28, 1.003)], 'km_ic', (0, 0, 1),
             lambda co: ((co.x + 0.11) / 0.22, (co.y - y0 - 0.06) / 0.22))
    B.add(cbox2((-0.1, y0 - 0.012, 0.66), (0.1, y0, 0.8), 0.01, 'black'))
    B.add(cbox2((-0.08, y0 - 0.016, 0.69), (0.08, y0 - 0.01, 0.77), 0.005, 'kmgreen'))
    for sx in (-1, 1):
        B.add(cbox2((sx * 0.16 - (0.0 if sx > 0 else 0.12), y0 + 0.28, 0.5), (sx * 0.16 + (0.12 if sx > 0 else 0.0), y0 + 0.34, 0.86), 0.015, 'kmgreyd'))
    return 1.0


# ================================================================ the kit's tiles
_c = SG._c
KANA = SG.KANA
BOLD = SG.LATIN
INK, WHITE, GREEN = (0.10, 0.10, 0.11), (0.97, 0.97, 0.96), (0.12, 0.50, 0.28)


def _label(dr, w, h, s, paths, frac, ink, cx=0.5, cy=0.5, maxw=0.9):
    size = SG.fit(dr, s, paths, int(h * frac), w * maxw)
    SG.text(dr, (w * cx, h * cy), s, paths, size, ink)


def t_stripe(dr, w, h, k):
    """Yellow and black at 45 degrees, 0.1 m each on a 0.4 m tile (the crossing's machines)."""
    dr.rectangle([0, 0, w, h], fill=_c((0.98, 0.79, 0.12)))
    n = 4
    step = (w + h) / n
    for i in range(-n, 2 * n):
        x = i * step
        dr.polygon([(x, 0), (x + step / 2, 0), (x + step / 2 - h, h), (x - h, h)], fill=_c(INK))


def t_station(dr, w, h, k):
    """Hase's name board: 長谷 large, はせ and Hase, the neighbours on a green band below (ごくらくじ / ゆいがはま)."""
    dr.rectangle([0, 0, w, h], fill=_c(WHITE))
    _label(dr, w, h * 0.56, '長　谷', KANA, 0.66, INK, cy=0.5)
    _label(dr, w, h, 'は　せ　　Hase', KANA, 0.15, INK, cy=0.635)
    band = int(h * 0.74)
    dr.rectangle([0, band, w, h], fill=_c(GREEN))
    dr.line([(w * 0.5, band + h * 0.03), (w * 0.5, h - h * 0.03)], fill=_c(WHITE), width=max(1, int(3 * k)))
    for s_, cx in (('← ごくらくじ  Gokurakuji', 0.25), ('ゆいがはま  Yuigahama →', 0.75)):
        size = SG.fit(dr, s_, KANA, int(h * 0.085), w * 0.46)
        SG.text(dr, (w * cx, h * 0.87), s_, KANA, size, WHITE)


def t_bin(word, sub, colour, icon):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c((0.95, 0.94, 0.9)))
        dr.rectangle([0, 0, w, h * 0.3], fill=_c(colour))
        _label(dr, w, h * 0.3, word, KANA, 0.6, WHITE, cy=0.5)
        _label(dr, w, h, sub, BOLD, 0.07, INK, cy=0.37)
        cx, cy, r = w / 2, h * 0.7, w * 0.22
        if icon == 'can':
            dr.rounded_rectangle([cx - r * 0.6, cy - r, cx + r * 0.6, cy + r], radius=r * 0.2, outline=_c(colour), width=max(2, int(5 * k)))
        elif icon == 'pet':
            dr.rounded_rectangle([cx - r * 0.5, cy - r * 0.6, cx + r * 0.5, cy + r], radius=r * 0.25, outline=_c(colour), width=max(2, int(5 * k)))
            dr.rectangle([cx - r * 0.2, cy - r, cx + r * 0.2, cy - r * 0.6], outline=_c(colour), width=max(2, int(4 * k)))
        else:
            dr.ellipse([cx - r * 0.55, cy - r * 0.2, cx + r * 0.55, cy + r], outline=_c(colour), width=max(2, int(5 * k)))
            dr.rectangle([cx - r * 0.2, cy - r, cx + r * 0.2, cy - r * 0.15], outline=_c(colour), width=max(2, int(4 * k)))
    return f


def t_dest(dr, w, h, k):
    """The tram's destination sign: 鎌倉 Kamakura, white on black."""
    dr.rectangle([0, 0, w, h], fill=_c((0.08, 0.08, 0.09)))
    _label(dr, w * 0.5, h, '鎌倉', KANA, 0.7, (0.98, 0.94, 0.80), cx=0.5, cy=0.5)
    size = SG.fit(dr, 'Kamakura', BOLD, int(h * 0.42), w * 0.42)
    SG.text(dr, (w * 0.74, h * 0.5), 'Kamakura', BOLD, size, (0.98, 0.94, 0.80))


def t_ic(dr, w, h, k):
    """The card reader's target: a blue pad with the IC mark."""
    dr.rectangle([0, 0, w, h], fill=_c((0.16, 0.38, 0.74)))
    dr.ellipse([w * 0.18, h * 0.18, w * 0.82, h * 0.82], outline=_c(WHITE), width=max(2, int(4 * k)))
    _label(dr, w, h, 'IC', BOLD, 0.34, WHITE)


def t_mirror(dr, w, h, k):
    """A convex mirror: sky at the top, a pale street below, a bright highlight."""
    for i in range(h):
        t = i / h
        col = tuple(a + (b - a) * t for a, b in zip((0.62, 0.76, 0.90), (0.70, 0.70, 0.68)))
        dr.line([(0, i), (w, i)], fill=_c(col))
    dr.ellipse([w * 0.18, h * 0.16, w * 0.45, h * 0.32], fill=_c((0.95, 0.97, 0.99)))


def t_lattice(dr, w, h, k):
    """A wooden lattice over paper (the shrine's doors, a tram door's frame): dark wood bars on warm white."""
    dr.rectangle([0, 0, w, h], fill=_c((0.93, 0.90, 0.80)))
    n = 6
    lw = max(2, int(6 * k))
    for i in range(n + 1):
        x = i * (w - lw) / n
        dr.rectangle([x, 0, x + lw, h], fill=_c((0.33, 0.24, 0.18)))
        y = i * (h - lw) / n
        dr.rectangle([0, y, w, y + lw], fill=_c((0.33, 0.24, 0.18)))


def t_arrow(dr, w, h, k):
    """The crossing's direction indicator: a lit arrow on black."""
    dr.rectangle([0, 0, w, h], fill=_c((0.06, 0.06, 0.07)))
    pts = [(w * 0.15, h * 0.4), (w * 0.6, h * 0.4), (w * 0.6, h * 0.2), (w * 0.88, h * 0.5), (w * 0.6, h * 0.8), (w * 0.6, h * 0.6), (w * 0.15, h * 0.6)]
    dr.polygon(pts, fill=_c((1.0, 0.86, 0.36)))


def paint(img, put):
    """The Kamakura kit's own tiles (kit_buildings_atlas.paint calls this through EXTRA)."""
    pp = SG.put_pil
    pp(img, 'km_stripe', t_stripe, (0.98, 0.79, 0.12))
    pp(img, 'km_station', t_station, WHITE)
    pp(img, 'km_bin_can', t_bin('カン', 'CANS', (0.93, 0.45, 0.14), 'can'), (0.95, 0.94, 0.9))
    pp(img, 'km_bin_pet', t_bin('ペット', 'PLASTIC BOTTLES', (0.19, 0.43, 0.76), 'pet'), (0.95, 0.94, 0.9))
    pp(img, 'km_bin_glass', t_bin('ビン', 'GLASS', (0.20, 0.55, 0.32), 'glass'), (0.95, 0.94, 0.9))
    pp(img, 'km_dest', t_dest, (0.08, 0.08, 0.09))
    pp(img, 'km_ic', t_ic, (0.16, 0.38, 0.74))
    pp(img, 'km_mirror', t_mirror, (0.66, 0.73, 0.79))
    pp(img, 'km_lattice', t_lattice, (0.93, 0.90, 0.80))
    pp(img, 'km_arrow', t_arrow, (0.06, 0.06, 0.07))


# ================================================================ the kit's rows
def pal_km(pal):
    """The Kamakura rows of the kit's SPECS (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps).
    The house's parts 1 to 3 (wall, accent, roof) can be repainted by the street for variety; the rest keep their own."""
    prop = {'ppm': 12}
    return [
        ('HouseKM', 8.2, 5.8, 7.4, 1.75, house_km,
         pal((0.91, 0.85, 0.72), (0.40, 0.30, 0.24), (0.34, 0.36, 0.40), trim=(0.88, 0.86, 0.82), conc=(0.74, 0.72, 0.68),
             frame=(0.80, 0.81, 0.82), soffit=(0.86, 0.84, 0.80)), 8.4, {'wall': 'stucco', 'ppm': 64}, {}),
        ('TramKM', 12.0, 3.4, 2.3, 0.0, tram_km,
         pal((0.20, 0.45, 0.31), (0.95, 0.90, 0.74), (0.58, 0.60, 0.62)), 5.0, {'ppm': 40}, {}),
        ('ToriiKM', 2.8, 2.4, 0.32, 0.0, torii_km, pal((0.86, 0.27, 0.15), (0.12, 0.12, 0.13), (0.12, 0.12, 0.13)), 2.9, prop, {}),
        ('ShrineKM', 5.4, 1.0, 3.9, 0.0, shrine_km,
         pal((0.66, 0.64, 0.59), (0.58, 0.42, 0.29), (0.42, 0.62, 0.55)), 3.4, {'ppm': 32}, {}),
        ('CrossingSignalKM', 1.1, 3.6, 0.6, 0.0, crossing_signal, pal((0.98, 0.79, 0.12), (0.12, 0.12, 0.13), (0.56, 0.55, 0.54)), 3.8, prop, {}),
        ('CrossingBarrierKM', 0.7, 1.1, 0.6, 0.0, crossing_barrier, pal((0.98, 0.79, 0.12), (0.12, 0.12, 0.13), (0.56, 0.55, 0.54)), 4.6, prop, {}),
        ('MirrorKM', 0.8, 3.8, 0.4, 0.0, mirror_km, pal((0.96, 0.47, 0.14), (0.96, 0.47, 0.14), (0.56, 0.55, 0.54)), 4.0, prop, {}),
        ('RecycleKM', 1.4, 1.0, 0.5, 0.0, recycle_km, pal((0.93, 0.91, 0.85), (0.19, 0.43, 0.76), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        ('StationSignKM', 1.8, 2.1, 0.16, 0.0, station_sign, pal((0.97, 0.97, 0.96), (0.12, 0.50, 0.28), (0.56, 0.55, 0.54)), 2.3, prop, {}),
        ('TicketGateKM', 0.6, 1.0, 0.64, 0.0, ticket_gate, pal((0.46, 0.38, 0.33), (0.58, 0.60, 0.62), (0.56, 0.55, 0.54)), 1.2, prop, {}),
    ]
