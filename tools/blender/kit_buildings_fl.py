# Florida beach-town buildings and street things for their own kit (kit_buildings.py --kit Florida), after the
# user's chapter 3 references (review/florida/refs, F3-1 to F3-6): a Space Coast beach strip on the A1A. The beach
# front (a concrete-block restroom with beach showers under a blue standing-seam roof, a weathered snack shack, a
# painted lifeguard stand, a dune crossover), a chrome 1950s diner and its pole sign, a two-storey Miami Modern
# motel with its sign and pool, a rental shop, five Art Deco shops, the school-zone beacon, a bus shelter, the
# street's small things (signs, lamps, bins, a hydrant, a mailbox, a concrete pole with its mast-arm signal, a
# chain-link fence and a goal), and the school (Seagrove High: cream and teal, covered walkways, a marquee, the
# flags, an aluminium picket fence and gate, portable classrooms).
#
# Same contract as the rest of the kit (kit_buildings.py): metres, Z up, the origin at the centre of the front
# wall's base, the street face looking along -Y, parts 1 wall / 2 accent / 3 roof. Every name on a sign is
# invented. The signs and the glass-block, breeze-block and flag tiles are painted here (paint(), through
# kit_buildings_atlas.EXTRA) into the kit's own 4096 x 4096 atlas.
import math
import numpy as np
from mathutils import Vector
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import decal, flat_ac
from kit_buildings_cal import (hip, roof_z, column, gutter, condenser, surfboard, glass_panel, stucco_box, cal_window, arch_head,
                               surround, house_number, wall_vent)
import kit_buildings_signs as SG

# ---------------------------------------------------------------- the kit's own colours
# (appended to the shared table, so every other kit's material ids stay as they are)
FL_MAT = {
    'aqua': (0, (0.42, 0.78, 0.78), 'white', 0.1), 'aquad': (0, (0.14, 0.50, 0.53), 'white', 0.1),
    'seafoam': (0, (0.66, 0.86, 0.80), 'white', 0.1), 'flyel': (0, (0.98, 0.80, 0.20), 'white', 0.1),
    'flora': (0, (0.94, 0.42, 0.16), 'white', 0.1), 'flred': (0, (0.78, 0.18, 0.19), 'white', 0.1),
    'pink': (0, (0.96, 0.70, 0.76), 'white', 0.1), 'lav': (0, (0.77, 0.71, 0.90), 'white', 0.1),
    'blueb': (0, (0.18, 0.37, 0.62), 'white', 0.1), 'skyb': (0, (0.47, 0.70, 0.86), 'white', 0.1),
    'chrome': (0, (0.80, 0.82, 0.84), 'piece', 0.0), 'chromew': (0, (0.86, 0.87, 0.89), 'white', 0.0),
    'neonr': (0, (1.0, 0.42, 0.36), 'white', 0.0), 'neonb': (0, (0.62, 0.94, 1.0), 'white', 0.0),
    'grey': (0, (0.55, 0.56, 0.58), 'white', 0.1), 'greyd': (0, (0.30, 0.31, 0.33), 'white', 0.1),
    'woodg': (0, (0.62, 0.58, 0.52), 'white', 0.2), 'concp': (0, (0.80, 0.79, 0.76), 'piece', 0.0),
    'water': (0, (0.36, 0.74, 0.84), 'white', 0.0), 'rope': (0, (0.82, 0.74, 0.58), 'white', 0.0),
    'mulch': (0, (0.42, 0.28, 0.20), 'white', 0.0), 'solarp': (0, (0.16, 0.22, 0.34), 'white', 0.0),
}
for _k, _v in FL_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1


# ---------------------------------------------------------------- the kit's tiles (allocated by kit_buildings.py)
TILES = [
    ('fl_glassblock', 256, 256), ('fl_breeze', 256, 256), ('fl_chain', 128, 128), ('fl_gate', 128, 128),
    ('fl_screen', 128, 128), ('fl_lattice', 128, 128), ('sg_nowake', 224, 280),
    ('fl_men', 96, 128), ('fl_women', 96, 128), ('fl_flagus', 380, 200), ('fl_flagfl', 300, 200),
    ('sg_access23', 256, 320), ('sg_access', 256, 320), ('sg_turtle', 256, 320), ('sg_hurricane', 320, 256),
    ('sg_diner', 640, 300), ('sg_motel', 512, 300), ('sg_vacancy', 384, 96), ('sg_rentals', 768, 112),
    ('sg_surfshop', 640, 120), ('sg_havana', 640, 120), ('sg_bait', 640, 120), ('sg_icecream', 640, 120),
    ('sg_school', 640, 200), ('sg_schoolwall', 640, 96), ('sg_schoolzone', 256, 256), ('sg_arrow', 160, 96),
    ('sg_menu', 192, 256), ('sg_bus', 160, 160),
]


# ---------------------------------------------------------------- shared pieces
def tile_cells(B, wf, u0, u1, v0, v1, w, region, cell):
    """A panel of a repeating tile (glass block, breeze block, chain link): one quad per cell of `cell` metres,
    the last ones cut to fit, each mapped to its share of the tile."""
    mb = MB()
    u = u0
    while u < u1 - 1e-4:
        ua = min(u + cell, u1)
        v = v0
        while v < v1 - 1e-4:
            va = min(v + cell, v1)
            s0, s1, t0, t1 = 0.0, (ua - u) / cell, 0.0, (va - v) / cell
            mb.face([(u, v, w), (ua, v, w), (ua, va, w), (u, va, w)], 'tex', (0, 0, 1), 1.0,
                    lambda co, u=u, v=v: reg_uv(region, (co.x - u) / cell, (co.y - v) / cell, 0.0))
            v = va
        u = ua
    put(B, wf, mb.bm())


def glass_block(B, wf, u0, u1, v0, v1, depth=0.08, frame='trim'):
    """Glass block set into the wall: a slim reveal and the block panel (four blocks to a 0.8 m tile)."""
    tile_cells(B, wf, u0, u1, v0, v1, -depth + 0.02, 'fl_glassblock', 0.8)
    mb = MB()
    reveal(mb, u0, u1, v0, v1, depth)
    put(B, wf, mb.bm())


def breeze_screen(B, wf, u0, u1, v0, v1, out=0.06):
    """A breeze-block screen wall (the Florida motel's pierced concrete blocks): the panel, a frame round it."""
    tile_cells(B, wf, u0, u1, v0, v1, out, 'fl_breeze', 0.8)
    for a, b, c, d in ((u0 - 0.1, u0, v0, v1), (u1, u1 + 0.1, v0, v1), (u0 - 0.1, u1 + 0.1, v1, v1 + 0.1),
                       (u0 - 0.1, u1 + 0.1, v0 - 0.1, v0)):
        put(B, wf, fbox((a, c, 0.0), (b, d, out + 0.04), 0.01, 'trim'))


def eyebrow(B, wf, u0, u1, v, out=0.5, t=0.09, mat='trim'):
    """A thin concrete 'eyebrow' ledge over windows (Florida Deco and Miami Modern)."""
    put(B, wf, fbox((u0, v, 0.0), (u1, v + t, out), 0.015, mat))


def stripes(B, wf, u0, u1, v, n=3, h=0.07, gap=0.08, mat='accentw', out=0.025):
    """Racing stripes: n thin painted bands proud of the wall."""
    for k in range(n):
        z = v + k * (h + gap)
        put(B, wf, fbox((u0, z, 0.0), (u1, z + h, out), 0.005, mat))


def porthole(B, wf, u, v, r=0.36, mat='trim'):
    """A round window: a moulded ring and dark glass."""
    ring, _ = lathe([(r * 0.82, 0.0), (r, 0.0), (r * 1.08, 0.06), (r, 0.1), (r * 0.82, 0.1)], 16, mat)
    xform(ring, T(u, v, 0.0) @ R(0.0, 'X'))
    put(B, wf, ring)
    mb = MB()
    pts = circle_pts(r * 0.84, 16, u, v)
    mb.face([(x, y, 0.03) for x, y in pts], 'glass', (0, 0, 1), 1.0,
            lambda co: reg_uv('glass0', 0.5 + (co.x - u) / (2 * r) * 0.8, 0.55 + (co.y - v) / (2 * r) * 0.4))
    put(B, wf, mb.bm())


def pipe_rail(B, pts, h=1.0, posts=1.4, mat='white', r=0.025, mid=True, bars=0.0):
    """A pipe railing along a polyline of (x, y, z) floor points: a top rail h above it, a mid rail, posts every
    `posts` metres and, with bars > 0, balusters that far apart."""
    top = [(x, y, z + h) for x, y, z in pts]
    B.add(tube(top, r, mat, 5))
    if mid: B.add(tube([(x, y, z + h * 0.48) for x, y, z in pts], r * 0.8, mat, 4))
    for (ax, ay, az), (bx, by, bz) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(math.ceil(L / posts)))
        for k in range(n + 1):
            if k == n and (bx, by, bz) != pts[-1]: continue
            t = k / n
            x, y, z = ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t
            B.add(tube([(x, y, z), (x, y, z + h)], r * 1.3, mat, 5))
        if bars > 0:
            m = max(1, int(L / bars))
            for k in range(1, m):
                t = k / m
                x, y, z = ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t
                B.add(tube([(x, y, z + 0.06), (x, y, z + h)], r * 0.55, mat, 4, caps=False))


def hip_plain(B, x0, x1, y0, y1, ze, rise, over=0.4, t=0.1, mat='roofp', edge='roofw', seams=0.45, seam_mat='roofw',
              soffit='soffit'):
    """A plain hipped roof (standing-seam metal or shingles): four flat slopes, a fascia, a soffit, and with
    seams > 0 the standing seams down every slope that far apart."""
    X0, X1, Y0, Y1 = x0 - over, x1 + over, y0 - over, y1 + over
    dx, dy = X1 - X0, Y1 - Y0
    h = min(dx, dy) / 2
    zt, zr = ze + t, ze + rise + t
    if dx >= dy:
        ym = (Y0 + Y1) / 2
        R0, R1 = (X0 + h, ym, zr), (X1 - h, ym, zr)
        quads = [[(X0, Y0, zt), (X1, Y0, zt), R1, R0], [(X1, Y1, zt), (X0, Y1, zt), R0, R1]]
        tris = [[(X0, Y1, zt), (X0, Y0, zt), R0], [(X1, Y0, zt), (X1, Y1, zt), R1]]
    else:
        xm = (X0 + X1) / 2
        R0, R1 = (xm, Y0 + h, zr), (xm, Y1 - h, zr)
        quads = [[(X0, Y1, zt), (X0, Y0, zt), R0, R1], [(X1, Y0, zt), (X1, Y1, zt), R1, R0]]
        tris = [[(X0, Y0, zt), (X1, Y0, zt), R0], [(X1, Y1, zt), (X0, Y1, zt), R1]]
    mb = MB()
    for q in quads: mb.face(q, mat, None, 1.0)
    for q in tris: mb.face(q, mat, None, 1.0)
    rim = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    outs = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
    for i in range(4):
        (ax, ay), (bx, by) = rim[i], rim[(i + 1) % 4]
        mb.face([(ax, ay, ze), (bx, by, ze), (bx, by, zt), (ax, ay, zt)], edge, outs[i], 0.7)
    mb.face([(X0, Y1, ze), (X1, Y1, ze), (X1, Y0, ze), (X0, Y0, ze)], soffit, (0, 0, -1), 0.85)
    B.add(mb.bm())
    if seams > 0:
        # seams down the front and back slopes (x-runs) and the hips' ends (y-runs), each standing 3 cm proud
        k = rise / h
        def zat(x, y):
            d = min(x - X0, X1 - x, y - Y0, Y1 - y, h)
            return zt + max(0.0, d) * k + 0.03
        x = X0 + seams * 0.5
        while x < X1:
            for ya, yb in ((Y0, Y0 + min(h, min(x - X0, X1 - x))), (Y1, Y1 - min(h, min(x - X0, X1 - x)))):
                if abs(yb - ya) < 0.05: continue
                B.add(tube([(x, ya, zat(x, ya)), (x, yb, zat(x, yb))], 0.014, seam_mat, 3, caps=False))
            x += seams
        y = Y0 + seams * 0.5
        while y < Y1:
            for xa, xb in ((X0, X0 + min(h, min(y - Y0, Y1 - y))), (X1, X1 - min(h, min(y - Y0, Y1 - y)))):
                if abs(xb - xa) < 0.05: continue
                B.add(tube([(xa, y, zat(xa, y)), (xb, y, zat(xb, y))], 0.014, seam_mat, 3, caps=False))
            y += seams
        B.add(tube([R0, R1] if (Vector(R1) - Vector(R0)).length > 0.05 else [R0, (R0[0], R0[1], R0[2] + 0.04)], 0.05, edge, 5))
    return zr


def flat_slab(B, x0, x1, y0, y1, z, t=0.18, mat='trim'):
    """A thin flat roof slab that overhangs the walls (the Miami Modern roof line)."""
    B.add(cbox2((x0, y0, z), (x1, y1, z + t), 0.02, mat))


def shower(B, x, y, z0=0.0):
    """A beach shower post: a steel pipe with a head on an arm and a push valve, on a little drain pad."""
    B.add(box((x - 0.35, y - 0.35, z0), (x + 0.35, y + 0.35, z0 + 0.04), 'concw', skip=('-z',)))
    B.add(tube([(x, y, z0), (x, y, z0 + 2.15), (x, y - 0.28, z0 + 2.2)], 0.035, 'chromew', 6))
    hd, _ = lathe([(0.0, -0.04), (0.09, -0.04), (0.06, 0.03), (0.0, 0.04)], 8, 'chromew')
    xform(hd, T(x, y - 0.3, z0 + 2.14)); B.add(hd)
    B.add(cbox2((x - 0.05, y - 0.08, z0 + 1.0), (x + 0.05, y - 0.02, z0 + 1.12), 0.01, 'chromew'))


def post_sign(B, x, y, region, w, h, z_bottom=1.0, post='greyd', out=0.0, two=False):
    """A sign panel on one or two square posts (its face to the street)."""
    xs = (x - w * 0.32, x + w * 0.32) if two else (x,)
    for px in xs:
        B.add(cbox2((px - 0.04, y + 0.02, 0.0), (px + 0.04, y + 0.1, z_bottom + h - 0.05), 0.01, post))
    B.add(cbox2((x - w / 2, y - 0.02, z_bottom), (x + w / 2, y + 0.02, z_bottom + h), 0.01, 'whitep'))
    mb = MB()
    mb.face([(x - w / 2 + 0.01, y - 0.025, z_bottom + 0.01), (x + w / 2 - 0.01, y - 0.025, z_bottom + 0.01),
             (x + w / 2 - 0.01, y - 0.025, z_bottom + h - 0.01), (x - w / 2 + 0.01, y - 0.025, z_bottom + h - 0.01)],
            'tex', (0, -1, 0), 1.0, lambda co: reg_uv(region, (co.x - x + w / 2) / w, (co.z - z_bottom) / h, 0.0))
    B.add(mb.bm())


def palm_planter(B, x, y, r=0.7, mat='concw'):
    """A low round tree pit kerb with mulch, where a palm is planted on the sidewalk."""
    ring, _ = lathe([(r - 0.1, 0.0), (r, 0.0), (r, 0.12), (r - 0.1, 0.12)], 12, mat)
    xform(ring, T(x, y, 0.0)); B.add(ring)
    m, _ = lathe([(0.0, 0.06), (r - 0.1, 0.06)], 12, 'mulch')
    xform(m, T(x, y, 0.0)); B.add(m)


# ---------------------------------------------------------------- F3-1: the beach front
def restroom(B):
    """The beach's public restroom: painted concrete block, two blue doors with their signs, a louvred vent over
    them, a blue standing-seam hip roof with white gutters and downpipes, a wall lamp, and on its right a tiled
    shower wall with two beach showers on a concrete pad."""
    W, H, D = B.W, B.H, B.D
    xr = W / 2 - 2.2                      # the shower wall from here to the right end
    d1 = (-2.35, -1.35, 0.0, 2.15)
    d2 = (-0.85, 0.15, 0.0, 2.15)
    F, Rt, Lf, Bk = stucco_box(B, -W / 2, W / 2, 0.0, D, H, fronts=[d1, d2], rights=[], lefts=[(-2.6, -1.8, 1.9, 2.4)])
    # the block coursing round the doors (not over them)
    for a0, a1, b0, b1 in ((-W / 2, d1[0], 0.2, H), (d1[1], d2[0], 0.2, H), (d2[1], xr, 0.2, H), (d1[0], d2[1], d1[3], H)):
        B.feat('front', 'tilegrid', a0=a0, a1=a1, b0=b0, b1=b1, tw=0.4, th=0.2, bond=0.5, k=0.35, var=0.03)
    B.feat('right', 'tilegrid', a0=-0.7, a1=D + 0.7, b0=0.2, b1=H, tw=0.4, th=0.2, bond=0.5, k=0.35, var=0.03)
    B.feat('left', 'tilegrid', a0=-0.7, a1=D + 0.7, b0=0.2, b1=H, tw=0.4, th=0.2, bond=0.5, k=0.35, var=0.03)
    for k, (o, sign) in enumerate(((d1, 'fl_men'), (d2, 'fl_women'))):
        door(B, F, *o, mat='accent', glass=None, panels=((1, 2),), name='Door')
        decal(B, F, (o[0] + o[1]) / 2 - 0.18, (o[0] + o[1]) / 2 + 0.18, 1.45, 1.93, 0.012, sign)
    # the shower wall: tiles, two showers, the pad
    put(B, F, fbox((xr, 0.12, 0.0), (W / 2 - 0.15, 2.3, 0.05), 0.01, 'wall'))
    B.feat('front', 'tilegrid', a0=xr, a1=W / 2 - 0.15, b0=0.12, b1=2.3, tw=0.3, th=0.3, k=0.6, var=0.06)
    for x in (xr + 0.5, xr + 1.45):
        shower(B, x, -0.15)
    B.add(box((xr - 0.2, -1.4, 0.0), (W / 2 + 0.2, 0.0, 0.05), 'concw', skip=('-z',)))
    # a louvred vent over the doors, a lamp, a drinking-water fountain stub
    vv = fbox((-1.3, 2.35, -0.01), (-0.4, 2.7, 0.03), 0.004, 'tex')
    uv_fn(vv, faces_facing(vv, (0, 0, 1), 0.9), 'louvre', lambda co: ((co.x + 1.3) / 0.9, (co.y - 2.35) / 0.35), 0.02)
    put(B, F, vv)
    lantern(B, F, -2.75, 2.3, out=0.16, name='Lamp')
    roof_top = hip_plain(B, -W / 2, W / 2, 0.0, D, H, B.RH, over=0.45, seams=0.42)
    for x0, x1, y in ((-W / 2 - 0.45, W / 2 + 0.45, -0.45),):
        gutter(B, x0, x1, y, H - 0.02, pipe_x=-W / 2 + 0.12, pipe_wall_y=-0.06)
    downpipe(B, [(W / 2 - 0.12, -0.5, H - 0.1), (W / 2 - 0.12, -0.06, H - 0.4), (W / 2 - 0.12, -0.06, 0.25),
                 (W / 2 - 0.12, -0.18, 0.1)], r=0.04, mat='trim', brackets=[(W / 2 - 0.12, -0.06, 1.2)])
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.45, k=0.35)
    return roof_top + 0.06


def shack(B):
    """The weathered beach snack shack: vertical boards in a sun-faded colour, a shingle hip roof, a service
    window with its hatch propped up and a counter, a menu board, a small side window and an AC unit."""
    W, H, D = B.W, B.H, B.D
    sw = (-W / 2 + 0.7, W / 2 - 0.9, 0.95, 2.05)
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H, [sw], 0.0, mode='rib', mat='accent', rib=(0.16, 0.025))
    wall(B, Rt, 0, D, H, [(1.2, 2.2, 1.0, 1.9)], 0.0, mode='rib', mat='accent', rib=(0.16, 0.025))
    wall(B, Lf, -D, 0, H, [], 0.0, mode='rib', mat='accent', rib=(0.16, 0.025))
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0, mode='rib', mat='accent', rib=(0.16, 0.025))
    box_shell_corners(B, 0.0, H, 0.09, mat='trim')
    window(B, F, *sw, depth=0.12, fw=0.05, cols=1, frame='trimw', glass='glass3', sill=None, head=None, seed=901)
    # the hatch propped up over the window, the counter shelf on brackets under it
    put(B, F, fbox((sw[0] - 0.08, sw[3], 0.0), (sw[1] + 0.08, sw[3] + 0.06, 0.06), 0.01, 'trim'))
    hb = MB()
    a, b = sw[0] - 0.1, sw[1] + 0.1
    hb.face([(a, sw[3] + 0.02, 0.02), (b, sw[3] + 0.02, 0.02), (b, sw[3] + 0.34, 0.62), (a, sw[3] + 0.34, 0.62)], 'accentp', (0, -1, 1), 1.0)
    hb.face([(b, sw[3] + 0.0, 0.02), (a, sw[3] + 0.0, 0.02), (a, sw[3] + 0.32, 0.62), (b, sw[3] + 0.32, 0.62)], 'woodg', (0, 1, -1), 0.8)
    put(B, F, hb.bm())
    for x in (a + 0.15, b - 0.15):
        put(B, F, tube([(x, sw[3] - 0.2, 0.05), (x, sw[3] + 0.3, 0.58)], 0.015, 'metald', 4))
    put(B, F, fbox((sw[0] - 0.1, sw[2] - 0.06, 0.0), (sw[1] + 0.1, sw[2], 0.38), 0.01, 'woodg'))
    for x in (sw[0] + 0.1, sw[1] - 0.1):
        put(B, F, tube([(x, sw[2] - 0.45, 0.02), (x, sw[2] - 0.06, 0.34)], 0.018, 'metald', 4))
    decal(B, F, sw[1] + 0.12, sw[1] + 0.72, 1.0, 1.8, 0.03, 'sg_menu')
    window(B, Rt, 1.2, 2.2, 1.0, 1.9, depth=0.1, fw=0.05, cols=1, frame='trimw', glass='glass0', sill='trimw', head=None, seed=902, cheap=True)
    top = hip_plain(B, -W / 2, W / 2, 0.0, D, H, B.RH, over=0.35, mat='roofp', seams=0.0)
    ac_unit(B, Rt, 3.0, 1.9, w=0.6, h=0.4, d=0.24)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.35, k=0.35)
    return top + 0.05


def lifeguard(B):
    """A painted lifeguard stand on the sand: a hut on stilts, its walls one bright colour and its roof and trim
    another, a wide window band to the sea, a deck with rails round it and a ramp down to the sand."""
    W, H, D = B.W, B.H, B.D
    z0 = 1.7                                  # the hut's floor
    hw, hd = W / 2 - 0.25, D - 0.25           # the hut on the deck
    for x in (-W / 2 + 0.1, W / 2 - 0.1):
        for y in (0.1, D - 0.1):
            B.add(cbox2((x - 0.08, y - 0.08, 0.0), (x + 0.08, y + 0.08, z0), 0.01, 'accentw'))
    for y in (0.1, D - 0.1):
        B.add(tube([(-W / 2 + 0.1, y, 0.25), (W / 2 - 0.1, y, z0 - 0.15)], 0.04, 'accentw', 4))
        B.add(tube([(W / 2 - 0.1, y, 0.25), (-W / 2 + 0.1, y, z0 - 0.15)], 0.04, 'accentw', 4))
    B.add(cbox2((-W / 2, -0.6, z0 - 0.14), (W / 2, D, z0), 0.02, 'accentw'))                   # the deck
    hut = WF((0, 0.25, z0), (1, 0, 0), 'front')
    win = (-hw + 0.25, hw - 0.25, 0.85, 1.75)
    wall(B, hut, -hw, hw, H, [win], 0.0)
    rt = WF((hw, 0.25, z0), (0, 1, 0), 'right')
    wall(B, rt, 0.0, hd - 0.25, H, [(0.4, 1.4, 0.85, 1.75)], 0.0)
    lf = WF((-hw, 0.25, z0), (0, -1, 0), 'left')
    wall(B, lf, -(hd - 0.25), 0.0, H, [(-1.4, -0.5, 0.0, 1.95)], 0.0)
    bk = WF((0, hd, z0), (-1, 0, 0), 'front')
    wall(B, bk, -hw, hw, H, [], 0.0)
    window(B, hut, *win, depth=0.08, fw=0.05, cols=3, frame='trimw', glass='glass0', sill='accentw', head=None, seed=911, register=False)
    window(B, rt, 0.4, 1.4, 0.85, 1.75, depth=0.08, fw=0.05, cols=1, frame='trimw', glass='glass0', sill=None, head=None, seed=912,
           register=False, cheap=True)
    door(B, lf, -1.4, -0.5, 0.0, 1.95, depth=0.08, mat='accent', glass=0.45, panels=((1, 1),), register=False, name='Door')
    # a red band under the eaves, the roof (a low pyramid in the accent colour), a flag pole
    put(B, hut, fbox((-hw - 0.02, H - 0.3, 0.0), (hw + 0.02, H, 0.04), 0.01, 'accentw'))
    top = hip_plain(B, -hw, hw, 0.25, hd, z0 + H, 0.55, over=0.35, mat='roofp', seams=0.0)
    pipe_rail(B, [(-W / 2 + 0.05, -0.55, z0), (W / 2 - 0.05, -0.55, z0), (W / 2 - 0.05, D - 0.05, z0)], h=0.95, mat='accentw', bars=0.3, r=0.022)
    # the ramp down to the sand on the left
    rx = -W / 2
    ramp = MB()
    ramp.face([(rx - 3.3, -0.55, 0.06), (rx - 3.3, 0.45, 0.06), (rx, 0.45, z0 - 0.02), (rx, -0.55, z0 - 0.02)], 'woodg', (0, 0, 1), 1.0)
    ramp.face([(rx - 3.3, 0.45, 0.0), (rx - 3.3, -0.55, 0.0), (rx, -0.55, z0 - 0.14), (rx, 0.45, z0 - 0.14)], 'woodg', (0, 0, -1), 0.7)
    for y in (-0.55, 0.45):
        ramp.face([(rx - 3.3, y, 0.0), (rx, y, z0 - 0.14), (rx, y, z0 - 0.02), (rx - 3.3, y, 0.06)], 'woodg', (0, -1 if y < 0 else 1, 0), 0.8)
    B.add(ramp.bm())
    for k in range(9):
        x = rx - 3.3 + 0.37 * k + 0.18
        z = 0.06 + (z0 - 0.08) * (x - rx + 3.3) / 3.3
        B.add(box((x - 0.02, -0.55, z), (x + 0.02, 0.45, z + 0.03), 'woodd'))
    pipe_rail(B, [(rx - 3.25, -0.55, 0.06), (rx, -0.55, z0)], h=0.9, mat='accentw', r=0.02, mid=False)
    B.add(tube([(W / 2 - 0.1, D - 0.1, z0), (W / 2 - 0.1, D - 0.1, z0 + H + 1.6)], 0.025, 'white', 5))
    B.add(MB_flag(W / 2 - 0.1, D - 0.1, z0 + H + 1.1, 0.7, 0.45, 'flora', 'flyel'))
    return top + 1.7


def MB_flag(x, y, z, w, h, mat_a, mat_b):
    """A small two-colour flag hanging from a pole at (x, y), its top at z, waving gently along +x."""
    mb = MB()
    n = 5
    for k in range(n):
        xa, xb = k / n, (k + 1) / n
        ya = 0.06 * math.sin(xa * 5.0); yb = 0.06 * math.sin(xb * 5.0)
        m = mat_a if k < n // 2 + 1 else mat_b
        quad = [(x + xa * w, y + ya, z - h), (x + xb * w, y + yb, z - h), (x + xb * w, y + yb, z), (x + xa * w, y + ya, z)]
        mb.face(quad, m, (0, -1, 0), 1.0)
        mb.face(list(reversed(quad)), m, (0, 1, 0), 0.85)
    return mb.bm()


def crossover(B):
    """A dune crossover: a timber walkway rising off the street over the dune and running out toward the beach,
    on posts, with handrails each side and the boards across it."""
    W, H, D = B.W, B.H, B.D
    rise_end, z1 = 3.2, H                    # it climbs to z1 over the first 3.2 m, then runs level
    def zat(y):
        if y <= 0: return 0.08
        return 0.08 + (z1 - 0.08) * min(1.0, y / rise_end) ** 1.0
    ys = [0.0, rise_end * 0.5, rise_end, D]
    deck = MB()
    for ya, yb in zip(ys[:-1], ys[1:]):
        za, zb = zat(ya), zat(yb)
        deck.face([(-W / 2, ya, za), (W / 2, ya, za), (W / 2, yb, zb), (-W / 2, yb, zb)], 'woodg', (0, 0, 1), 1.0)
        for x in (-W / 2, W / 2):
            deck.face([(x, ya, za - 0.2), (x, yb, zb - 0.2), (x, yb, zb), (x, ya, za)], 'woodd', (1 if x > 0 else -1, 0, 0), 0.8)
    B.add(deck.bm())
    y = 0.15
    while y < D - 0.05:
        B.add(box((-W / 2, y - 0.015, zat(y) + 0.0), (W / 2, y + 0.015, zat(y) + 0.012), 'woodd'))
        y += 0.3
    for y in [0.05, 1.6, rise_end, rise_end + 2.0, rise_end + 4.0, D - 0.05]:
        if y > D: continue
        for x in (-W / 2 + 0.05, W / 2 - 0.05):
            B.add(cbox2((x - 0.06, y - 0.06, -0.4), (x + 0.06, y + 0.06, zat(y) + 1.0), 0.01, 'woodg'))
    for x in (-W / 2 + 0.05, W / 2 - 0.05):
        pts = [(x, yy, zat(yy)) for yy in ys]
        B.add(tube([(px, py, pz + 1.0) for px, py, pz in pts], 0.045, 'woodg', 4))
        B.add(tube([(px, py, pz + 0.5) for px, py, pz in pts], 0.03, 'woodg', 4))
    B.attach.append(('Top', (0.0, rise_end, z1)))
    return z1 + 1.1


# ---------------------------------------------------------------- F3-2: the diner
def open_window(B, wf, u0, u1, v0, v1, cols=3, depth=0.14, frame='chromew', sheen=True):
    """A big window with no glass drawn (the lit room behind shows): a slim frame and mullions in the reveal and a
    faint pale band along the top for the glass's reflection."""
    mb = MB()
    reveal(mb, u0, u1, v0, v1, depth)
    put(B, wf, mb.bm())
    zf = -depth + 0.06
    for a, b, c, d in ((u0, u1, v0, v0 + 0.05), (u0, u1, v1 - 0.05, v1), (u0, u0 + 0.05, v0, v1), (u1 - 0.05, u1, v0, v1)):
        put(B, wf, fbox((a, c, zf), (b, d, zf + 0.04), 0.004, frame))
    for k in range(1, cols):
        x = u0 + (u1 - u0) * k / cols
        put(B, wf, fbox((x - 0.025, v0, zf), (x + 0.025, v1, zf + 0.04), 0.004, frame))
    if sheen:
        g = MB()
        g.face([(u0 + 0.05, v1 - 0.22, zf - 0.005), (u1 - 0.05, v1 - 0.22, zf - 0.005), (u1 - 0.05, v1 - 0.05, zf - 0.005),
                (u0 + 0.05, v1 - 0.05, zf - 0.005)], 'glass', (0, 0, 1), 1.0,
               lambda co: reg_uv('glass0', 0.1 + (co.x - u0) / (u1 - u0) * 0.8, 0.86 + (co.y - (v1 - 0.22)) / 0.17 * 0.12))
        put(B, wf, g.bm())


def booth(B, x, y0, z0=0.0, mat='flred'):
    """A diner booth seen from the street: two high-backed red seats facing over a table with a lamp over it."""
    for yy, face in ((y0, 1), (y0 + 1.5, -1)):
        B.add(cbox2((x - 0.6, yy - 0.3, z0), (x + 0.6, yy + 0.3, z0 + 0.45), 0.04, mat))
        back = yy - 0.25 if face > 0 else yy + 0.25
        B.add(cbox2((x - 0.6, back - 0.1, z0 + 0.45), (x + 0.6, back + 0.1, z0 + 1.15), 0.05, mat))
    B.add(cbox2((x - 0.5, y0 + 0.4, z0 + 0.72), (x + 0.5, y0 + 1.1, z0 + 0.76), 0.01, 'whitep'))
    B.add(tube([(x, y0 + 0.75, z0), (x, y0 + 0.75, z0 + 0.72)], 0.04, 'chromew', 5))


def diner(B):
    """A 1950s roadside diner: a stainless 'railroad car' barrel roof with rounded ends, cream walls with red and
    chrome bands, a long run of windows with red booths and pendant lamps inside, a raised entrance with a stepped
    Deco head, glass block either side of the door, steps with rails and two planters."""
    W, H, D = B.W, B.H, B.D
    v0, v1 = 1.0, 2.55                    # the window band
    dx = 1.1                              # the entrance's half width
    wins = [(-W / 2 + 0.6, -dx - 0.9, v0, v1), (dx + 0.9, W / 2 - 0.6, v0, v1)]
    door_o = (-0.55, 0.55, 0.5, 2.6)
    gb = [(-dx + 0.05, -0.75, 1.0, 2.6), (0.75, dx - 0.05, 1.0, 2.6)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H, wins + [door_o] + gb, 0.0)
    wall(B, Rt, 0, D, H, [(1.0, 5.8, v0, v1)], 0.0)
    wall(B, Lf, -D, 0, H, [(-5.8, -1.0, v0, v1)], 0.0)
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0)
    for wo in wins: open_window(B, F, *wo, cols=4)
    open_window(B, Rt, 1.0, 5.8, v0, v1, cols=3)
    open_window(B, Lf, -5.8, -1.0, v0, v1, cols=3)
    shop_room(B, -W / 2 + 0.2, W / 2 - 0.2, 0.5, H - 0.05, D - 0.4, floor='white')
    for x in list(np.arange(-W / 2 + 1.1, -dx - 0.6, 1.5)) + list(np.arange(dx + 1.4, W / 2 - 0.6, 1.5)):
        booth(B, float(x), 0.5, 0.5)
        pendant(B, float(x), 1.25, H - 0.05, drop=0.55, mat='flred')
    B.add(cbox2((-W / 2 + 0.4, D - 1.6, 0.5), (W / 2 - 0.4, D - 1.0, 1.55), 0.03, 'chromew'))      # the counter at the back
    door(B, F, *door_o, depth=0.16, mat='chrome', glass=0.75, panels=((1, 1),), name='Door')
    for g in gb: glass_block(B, F, *g)
    # bands: a red stripe under the windows, chrome over them, the base in a darker cream
    for a, b in ((-W / 2 - 0.02, -dx), (dx, W / 2 + 0.02)):
        put(B, F, fbox((a, 0.86, 0.0), (b, 0.98, 0.05), 0.01, 'accentw'))
        put(B, F, fbox((a, 0.72, 0.0), (b, 0.78, 0.05), 0.01, 'accentw'))
        put(B, F, fbox((a, v1 + 0.02, 0.0), (b, v1 + 0.16, 0.08), 0.02, 'chromew'))
        put(B, F, fbox((a, H - 0.18, 0.0), (b, H - 0.04, 0.06), 0.01, 'accentw'))
    for wf, a, b in ((Rt, -0.02, D + 0.02), (Lf, -D - 0.02, 0.02)):
        put(B, wf, fbox((a, 0.86, 0.0), (b, 0.98, 0.05), 0.01, 'accentw'))
        put(B, wf, fbox((a, v1 + 0.02, 0.0), (b, v1 + 0.16, 0.08), 0.02, 'chromew'))
    for x in (-W / 2, W / 2):
        for y in (0.0, D):
            B.add(tube([(x, y, 0.0), (x, y, H)], 0.12, 'chromew', 8))
    # the barrel roof: chrome, a low arc across the depth, its ends rounded down over the end walls
    n = 8
    prof = [(float(y), H + 0.55 * max(0.0, math.sin(math.pi * y / D)) ** 0.7) for y in np.linspace(-0.3, D + 0.3, n + 1)]
    mb = MB()
    for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
        mb.face([(-W / 2 + 0.25, ya, za), (W / 2 - 0.25, ya, za), (W / 2 - 0.25, yb, zb), (-W / 2 + 0.25, yb, zb)], 'chrome', (0, 0, 1), 1.0)
    for sx in (-1, 1):
        xe, xo = sx * (W / 2 - 0.25), sx * (W / 2 + 0.25)
        for (ya, za), (yb, zb) in zip(prof[:-1], prof[1:]):
            mb.face([(xe, ya, za), (xe, yb, zb), (xo, yb, max(H, zb - 0.4)), (xo, ya, max(H, za - 0.4))], 'chrome', (sx, 0, 1), 0.92)
        mb.face([(xo, -0.3, H), (xo, D + 0.3, H), (xo, D + 0.3, H - 0.02), (xo, -0.3, H - 0.02)], 'chrome', (sx, 0, 0), 0.8)
    mb.face([(-W / 2 - 0.25, -0.3, H), (W / 2 + 0.25, -0.3, H), (W / 2 + 0.25, -0.3, H - 0.12), (-W / 2 - 0.25, -0.3, H - 0.12)], 'chrome', (0, -1, 0), 0.85)
    B.add(mb.bm())
    for x in np.arange(-W / 2 + 1.0, W / 2 - 0.5, 1.2):           # the roof's seams
        B.add(tube([(float(x), y, z + 0.015) for y, z in prof], 0.012, 'chromew', 3, caps=False))
    # the entrance: a taller box with a stepped Deco head
    eF = WF((0, -0.6, 0), (1, 0, 0), 'front')
    B.add(cbox2((-dx, -0.6, 0.0), (dx, 0.02, H + 0.9), 0.03, 'wall'))
    for k, (hw, z) in enumerate(((dx, H + 0.9), (dx - 0.3, H + 1.2), (dx - 0.6, H + 1.45))):
        B.add(cbox2((-hw, -0.65, z - 0.3 if k else z - 0.05), (hw, 0.0, z), 0.03, 'trim' if k else 'chromew'))
    B.add(tube([(-dx + 0.1, -0.66, H + 0.55), (dx - 0.1, -0.66, H + 0.55)], 0.03, 'accentw', 5))
    door_hole = (-0.55, 0.55)
    put(B, eF, fbox((-0.7, 2.6, 0.0), (0.7, 2.75, 0.12), 0.02, 'chromew'))
    steps(B, eF, -0.9, 0.9, [0.5, 0.34, 0.17], tread=0.32, back=0.0)
    for x in (-0.95, 0.95):
        pipe_rail(B, [(x, -1.6, 0.17), (x, -0.62, 0.5)], h=0.9, mat='chromew', r=0.022, mid=False)
    for x in (-dx - 1.6, dx + 1.6):
        B.add(cbox2((x - 0.75, -0.95, 0.0), (x + 0.75, -0.2, 0.55), 0.03, 'concw'))
        for k in range(4):
            B.add(blob((x - 0.5 + k * 0.33, -0.58, 0.62), (0.26, 0.24, 0.24), 'leafd' if k % 2 else 'leaf', 7, 3, 950 + k + int(x)))
    lantern(B, eF, -0.85, 2.2, out=0.12, name='Lamp')
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=v0 - 0.02, length=0.25, k=0.25)
    return H + 1.5


def diner_sign(B):
    """The diner's pole sign: a tall aqua pylon, a red boomerang board on both faces and a starburst on top."""
    H = B.H
    for x in (-0.18, 0.18):
        B.add(cbox2((x - 0.11, -0.11, 0.0), (x + 0.11, 0.11, H), 0.03, 'aqua'))
    B.add(cbox2((-0.5, -0.4, 0.0), (0.5, 0.4, 0.35), 0.04, 'concw'))
    # the board, leaning forward a little and canted
    w, h = 3.4, 1.6
    cx, cz = 0.4, H - 0.6
    for side in (-1, 1):
        mb = MB()
        y = 0.16 * side                     # side -1: the face to the street (-Y), read left to right
        pts = [(cx - w / 2, y, cz - h / 2), (cx + w / 2, y, cz - h / 2 + 0.35), (cx + w / 2, y, cz + h / 2 + 0.35), (cx - w / 2, y, cz + h / 2)]
        if side > 0: pts = list(reversed(pts))
        mb.face(pts, 'tex', (0, side, 0), 1.0,
                lambda co: reg_uv('sg_diner', (co.x - cx + w / 2) / w if side < 0 else 1 - (co.x - cx + w / 2) / w,
                                  (co.z - (cz - h / 2) - 0.35 * (co.x - cx + w / 2) / w) / h, 0.0))
        B.add(mb.bm())
    rim = [(cx - w / 2, cz - h / 2), (cx + w / 2, cz - h / 2 + 0.35), (cx + w / 2, cz + h / 2 + 0.35), (cx - w / 2, cz + h / 2), (cx - w / 2, cz - h / 2)]
    B.add(tube([(x, 0.0, z) for x, z in rim], 0.17, 'aqua', 4))
    # the starburst
    star = []
    for k in range(16):
        a = math.pi * 2 * k / 16
        r = 0.75 if k % 2 == 0 else 0.22
        star.append((math.cos(a) * r, math.sin(a) * r))
    sb = extrude_poly(star, 0.06, 'flyel', side_mat='flora', back=True)
    xform(sb, T(0.1, 0.03, H + 0.75) @ R(math.pi / 2, 'X'))
    B.add(sb)
    B.add(tube([(0.0, 0.0, H), (0.0, 0.0, H + 0.6)], 0.05, 'aqua', 5))
    return H + 1.5


# ---------------------------------------------------------------- F3-3: the motel, its sign and pool, the rental shop
def motel(B):
    """A two-storey Miami Modern motel: rooms in a row on both floors (teal doors, curtained windows, a light by
    each door), an open walkway along the upper floor on a slim slab with white railings and posts, an outside
    stair at the right, a breeze-block screen at the left end, an aqua end block with portholes, a thin
    overhanging flat roof with an aqua fascia, AC sleeves under the windows."""
    W, H, D = B.W, B.H, B.D
    fz = 3.0                               # the upper floor
    xl, xr = -W / 2 + 2.6, W / 2 - 2.8     # the rooms between the screen and the end block
    units = 5
    uw = (xr - xl) / units
    ops = []
    for f, z in ((0, 0.0), (1, fz)):
        for k in range(units):
            u = xl + k * uw
            ops.append((u + 0.35, u + 1.25, z, z + 2.15))                     # door
            ops.append((u + 1.6, u + uw - 0.3, z + 0.95, z + 2.15))           # window
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H, ops + [(-W / 2 + 0.4, -W / 2 + 2.3, 0.4, H - 0.5)], 0.0)
    wall(B, Rt, 0, D, H, [(3.0, 4.2, 1.0, 2.1), (3.0, 4.2, fz + 1.0, fz + 2.1)], 0.0)
    wall(B, Lf, -D, 0, H, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0)
    for f, z in ((0, 0.0), (1, fz)):
        for k in range(units):
            u = xl + k * uw
            door(B, F, u + 0.35, u + 1.25, z, z + 2.15, depth=0.12, mat='accent', glass=None, panels=((1, 2),), register=f == 0, name='Door')
            window(B, F, u + 1.6, u + uw - 0.3, z + 0.95, z + 2.15, depth=0.14, fw=0.05, cols=2, frame='alu', glass=('glass1', 'glass2')[(k + f) % 2],
                   sill='trim', head=None, seed=920 + k + 7 * f, cheap=f == 1, register=f == 0)
            lantern(B, F, u + 1.42, z + 1.95, out=0.12, name='Lamp')
            vv = fbox((u + 1.75, z + 0.45, -0.01), (u + 2.45, z + 0.8, 0.04), 0.004, 'tex')
            uv_fn(vv, faces_facing(vv, (0, 0, 1), 0.9), 'vent', lambda co, u=u, z=z: ((co.x - u - 1.75) / 0.7, (co.y - z - 0.45) / 0.35), 0.02)
            put(B, F, vv)
    window(B, Rt, 3.0, 4.2, 1.0, 2.1, cols=2, frame='alu', glass='glass1', seed=931, cheap=True)
    window(B, Rt, 3.0, 4.2, fz + 1.0, fz + 2.1, cols=2, frame='alu', glass='glass2', seed=932, cheap=True)
    # the breeze-block screen at the left end, set in the opening
    breeze_screen(B, F, -W / 2 + 0.4, -W / 2 + 2.3, 0.4, H - 0.5, out=-0.05)
    # the aqua end block on the right, standing a little proud, with two portholes
    B.add(cbox2((xr + 0.25, -0.25, 0.0), (W / 2 + 0.05, D * 0.6, H + 0.15), 0.03, 'accent'))
    eF = WF((0, -0.25, 0), (1, 0, 0), 'front')
    for z in (1.6, fz + 1.6):
        porthole(B, eF, (xr + 0.25 + W / 2) / 2, z, r=0.38)
    # the walkway: a slab over the ground floor's doors, its edge in white, posts, the rail
    y0 = -1.55
    B.add(cbox2((-W / 2 + 2.4, y0, fz - 0.22), (xr + 0.25, 0.0, fz), 0.02, 'trim'))
    B.add(cbox2((-W / 2 + 2.4, y0 - 0.02, fz - 0.3), (xr + 0.25, y0 + 0.1, fz + 0.02), 0.02, 'accentw'))
    for x in np.linspace(-W / 2 + 2.6, xr, 5):
        B.add(cbox2((float(x) - 0.07, y0 + 0.05, 0.0), (float(x) + 0.07, y0 + 0.19, fz - 0.22), 0.01, 'trim'))
    pipe_rail(B, [(-W / 2 + 2.45, y0 + 0.04, fz), (xr - 1.3, y0 + 0.04, fz)], h=1.0, mat='white', bars=0.2, r=0.022)
    # the stair: from the ground at the right up to the walkway's end, rails both sides
    sx0, sx1, sw = xr - 1.2, xr + 2.4, 1.05
    n = 16
    for k in range(n):
        xa = sx1 - (sx1 - sx0) * k / n; xb = sx1 - (sx1 - sx0) * (k + 1) / n
        z = fz * (k + 1) / n
        B.add(box((xb, y0 - sw, z - 0.05), (xa, y0, z), 'trim'))
    B.add(cbox2((sx0, y0 - sw - 0.03, 0.0), (sx0 + 0.08, y0 - sw + 0.05, fz), 0.01, 'trim'))     # the landing's post
    for yy in (y0 - sw, y0 - 0.02):
        stringer = MB()
        stringer.face([(sx1, yy, 0.0), (sx1, yy, 0.25), (sx0, yy, fz), (sx0, yy, fz - 0.3)], 'trim', (0, -1, 0), 0.9)
        B.add(stringer.bm())
    pipe_rail(B, [(sx1, y0 - sw, 0.05), (sx0, y0 - sw, fz)], h=0.95, mat='white', bars=0.3, r=0.022)
    pipe_rail(B, [(sx0, y0 - sw, fz), (sx0 - 1.0, y0 - sw, fz), (sx0 - 1.0, y0 + 0.04, fz)], h=0.95, mat='white', bars=0.14, r=0.022)
    # the roof: a thin slab that overhangs, an aqua fascia
    flat_slab(B, -W / 2 - 0.3, xr + 0.25, -1.75, D + 0.3, H, 0.2, 'trim')
    B.add(cbox2((-W / 2 - 0.32, -1.78, H - 0.08), (xr + 0.27, -1.68, H + 0.22), 0.01, 'accentw'))
    B.feat('roof', 'flat', x0=-W / 2, x1=W / 2, y0=0.0, y1=D)
    for x in (-3.0, 2.5):
        flat_ac(B, x, D - 2.5, H + 0.2)
    B.feat('front', 'ao', a0=-W / 2, a1=xr, b=fz - 0.25, length=0.6, k=0.4)
    B.feat('front', 'ao', a0=-W / 2, a1=xr, b=H - 0.02, length=0.5, k=0.35)
    return H + 0.6


def motel_sign(B):
    """The motel's roadside sign: an aqua board slanting off a white pylon, the name in script, a red VACANCY box
    under it and a gold star on top."""
    H = B.H
    w, h = 2.6, 1.9
    lean = 0.35
    cz = H - 1.6
    def face(y, rev, region, x0, x1, z0, z1, sl):
        mb = MB()
        pts = [(x0 + sl * 0.0, y, z0), (x1, y, z0), (x1 + sl, y, z1), (x0 + sl, y, z1)]
        if rev: pts = list(reversed(pts))
        mb.face(pts, 'tex', (0, 1 if rev else -1, 0), 1.0,
                lambda co: reg_uv(region, ((co.x - x0 - sl * (co.z - z0) / (z1 - z0)) / (x1 - x0)) if not rev else
                                  1 - ((co.x - x0 - sl * (co.z - z0) / (z1 - z0)) / (x1 - x0)), (co.z - z0) / (z1 - z0), 0.0))
        B.add(mb.bm())
    x0, x1, z0, z1 = -1.2, 1.4, cz - h / 2, cz + h / 2
    for y, rev in ((-0.2, False), (0.2, True)):
        face(y, rev, 'sg_motel', x0, x1, z0, z1, lean)
    pts = [(x0, z0), (x1, z0), (x1 + lean, z1), (x0 + lean, z1), (x0, z0)]
    B.add(tube([(x, 0.0, z) for x, z in pts], 0.21, 'aqua', 4))
    # the white pylon it hangs off, at its left edge, up past its top
    B.add(cbox2((x0 - 0.62, -0.28, 0.0), (x0 - 0.12, 0.28, z1 + 0.25), 0.04, 'whitep'))
    B.add(cbox2((x0 - 0.8, -0.42, 0.0), (x0 + 0.06, 0.42, 0.3), 0.04, 'concw'))
    for z in (z0 + 0.25, z1 - 0.25):
        B.add(box((x0 - 0.15, -0.06, z - 0.06), (x0 + 0.05, 0.06, z + 0.06), 'metald'))
    # the VACANCY box below, on its own brackets
    vb = (-0.95, 1.05, z0 - 0.75, z0 - 0.2)
    B.add(cbox2((vb[0] - 0.05, -0.16, vb[2] - 0.05), (vb[1] + 0.05, 0.16, vb[3] + 0.05), 0.02, 'black'))
    for y, rev in ((-0.17, False), (0.17, True)):
        face(y, rev, 'sg_vacancy', vb[0], vb[1], vb[2], vb[3], 0.0)
    for x in (-0.6, 0.7):
        B.add(tube([(x, 0.0, vb[3] + 0.05), (x, 0.0, z0)], 0.025, 'metald', 4))
    star = []
    for k in range(10):
        a = math.pi / 2 + math.pi * 2 * k / 10
        r = 0.55 if k % 2 == 0 else 0.22
        star.append((math.cos(a) * r, math.sin(a) * r))
    sb = extrude_poly(star, 0.08, 'flyel', side_mat='gold', back=True)
    xform(sb, T(x0 + lean + 0.3, 0.04, z1 + 0.75) @ R(math.pi / 2, 'X'))
    B.add(sb)
    B.add(tube([(x0 + lean + 0.3, 0.0, z1), (x0 + lean + 0.3, 0.0, z1 + 0.3)], 0.04, 'gold', 5))
    return H + 0.5


def motel_pool(B):
    """The motel's pool in front of it: a kidney-ish pool in a concrete deck, a white aluminium fence and gate,
    a striped umbrella and two loungers."""
    W, D = B.W, B.D
    B.add(box((-W / 2, 0.0, 0.0), (W / 2, D, 0.06), 'concw', skip=('-z',)))
    pool = [(math.cos(a) * (W / 2 - 1.2) * (1 + 0.08 * math.sin(2 * a)), D / 2 + math.sin(a) * (D / 2 - 0.8)) for a in np.linspace(0, 2 * math.pi, 22)[:-1]]
    pb = extrude_poly(pool, 0.005, 'water')
    xform(pb, T(0, 0, 0.055)); B.add(pb)
    rim = [(x, y, 0.07) for x, y in pool] + [(pool[0][0], pool[0][1], 0.07)]
    B.add(tube(rim, 0.08, 'trim', 4))
    pts = [(-W / 2 + 0.1, 0.1, 0.06), (W / 2 - 0.1, 0.1, 0.06)]
    pipe_rail(B, pts, h=1.2, mat='white', bars=0.12, r=0.024, posts=1.8)
    for x in (-W / 2 + 0.1, W / 2 - 0.1):
        pipe_rail(B, [(x, 0.1, 0.06), (x, D - 0.1, 0.06)], h=1.2, mat='white', bars=0.12, r=0.024, posts=1.8)
    # the umbrella
    ux, uy = W / 2 - 1.4, D - 0.9
    B.add(tube([(ux, uy, 0.06), (ux, uy, 2.35)], 0.03, 'white', 5))
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        mb = MB()
        mb.face([(ux, uy, 2.45), (ux + math.cos(a0) * 1.25, uy + math.sin(a0) * 1.25, 2.0), (ux + math.cos(a1) * 1.25, uy + math.sin(a1) * 1.25, 2.0)],
                'aqua' if k % 2 else 'white', (0, 0, 1), 1.0)
        mb.face([(ux, uy, 2.43), (ux + math.cos(a1) * 1.24, uy + math.sin(a1) * 1.24, 1.98), (ux + math.cos(a0) * 1.24, uy + math.sin(a0) * 1.24, 1.98)],
                'aqua' if k % 2 else 'white', (0, 0, -1), 0.7)
        B.add(mb.bm())
    for x in (-W / 2 + 1.0, -W / 2 + 2.0):
        B.add(cbox2((x - 0.3, D - 1.9, 0.3), (x + 0.3, D - 0.4, 0.38), 0.02, 'white'))
        B.add(cbox2((x - 0.3, D - 0.55, 0.36), (x + 0.3, D - 0.4, 0.9), 0.02, 'white'))
        for yy in (D - 1.8, D - 0.5):
            B.add(box((x - 0.28, yy - 0.03, 0.06), (x + 0.28, yy + 0.03, 0.3), 'metald'))
    return 2.5


def bike(B, x, y, mat='aqua', yaw=0.0):
    """A beach cruiser parked side-on to the street: two wheels, the frame, a saddle, swept bars, a basket."""
    r, wb = 0.33, 1.05
    c, s = math.cos(yaw), math.sin(yaw)
    P = lambda u, z: (x + u * c, y + u * s, z)
    for u in (-wb / 2, wb / 2):
        ring = [P(u + r * math.cos(a), r + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)]
        B.add(tube(ring, 0.03, 'rubber', 4, caps=False))
        B.add(tube([P(u, r), P(u + 0.01, r + 0.01)], 0.05, 'chromew', 4))
    frame = [P(-wb / 2, r), P(-0.05, r + 0.05), P(0.32, r + 0.42), P(-0.18, r + 0.46), P(-wb / 2, r)]
    B.add(tube(frame, 0.026, mat, 4))
    B.add(tube([P(-0.05, r + 0.05), P(-0.18, r + 0.46), P(-0.2, r + 0.62)], 0.024, mat, 4))
    B.add(tube([P(0.32, r + 0.42), P(wb / 2, r)], 0.024, mat, 4))
    B.add(tube([P(0.32, r + 0.42), P(0.36, r + 0.7), P(0.2, r + 0.78)], 0.02, 'chromew', 4))
    B.add(cbox2((x - 0.12 * c - 0.2 * c - 0.1, y - 0.2 * s - 0.08, r + 0.62), (x - 0.2 * c + 0.1, y - 0.2 * s + 0.08, r + 0.7), 0.02, 'black'))


def rentals(B):
    """The beach rental shop: flat-roofed yellow stucco, its name painted big along the parapet, a blue and white
    striped awning over a lit glass shopfront, a flat canopy on posts at its side with surfboards under it, beach
    cruisers parked in front, boogie boards and skateboards out on display."""
    W, H, D = B.W, B.H, B.D
    pp = 0.7
    sf = (-W / 2 + 0.5, W / 2 - 2.0, 0.0, 2.8)
    door_o = (W / 2 - 1.75, W / 2 - 0.75, 0.0, 2.5)
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H + pp, [sf, door_o], 0.0)
    wall(B, Rt, 0, D, H + pp, [], 0.0)
    wall(B, Lf, -D, 0, H + pp, [(-5.0, -3.6, 1.2, 2.4)], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp, [], 0.0)
    flat_top(B, H, pp)
    window(B, F, *sf, depth=0.18, fw=0.07, cols=4, frame='alu', glass='glass3', sill='conc', head=None, seed=941)
    door(B, F, *door_o, mat='alu', glass=0.85, panels=((1, 1),), name='Door')
    window(B, Lf, -5.0, -3.6, 1.2, 2.4, cols=2, frame='alu', glass='glass0', seed=942, cheap=True)
    decal(B, F, -W / 2 + 0.4, W / 2 - 0.4, H - 0.05, H + pp - 0.08, 0.012, 'sg_rentals')
    awning(B, F, sf[0] - 0.1, sf[1] + 0.1, sf[3] + 0.6, 1.1, 0.45, 10, mat_a='accent', mat_b='cream', valance=0.2, scallops=False)
    # the side canopy: a flat roof on two posts off the right wall
    cx0, cx1 = W / 2, W / 2 + 2.6
    B.add(cbox2((cx0, -0.9, 2.85), (cx1, D * 0.5, 3.0), 0.02, 'trim'))
    for y in (-0.8, D * 0.5 - 0.1):
        B.add(cbox2((cx1 - 0.14, y - 0.06, 0.0), (cx1 - 0.02, y + 0.06, 2.85), 0.01, 'trim'))
    for k, col in enumerate(('cloth2', 'aqua', 'white', 'skyb')):
        surfboard(B, cx0 + 0.45 + 0.42 * k, 0.5, col, lean=0.12, L=2.3, W_=0.5)
    # bikes, boogie boards, skateboards
    for k, col in enumerate(('aqua', 'skyb', 'aqua', 'seafoam')):
        bike(B, -W / 2 + 1.0 + 0.55 * k, -1.1 - 0.05 * (k % 2), col, yaw=math.pi / 2 + 0.06 * (k - 1.5))
    bx = door_o[1] - 0.3
    for k, col in enumerate(('flora', 'flyel', 'aqua', 'skyb', 'pink', 'flora', 'aqua')):
        B.add(cbox2((bx - 2.6 + k * 0.17, -0.55, 0.05), (bx - 2.52 + k * 0.17, -0.1, 1.05), 0.03, col))
    B.add(cbox2((bx - 2.75, -0.62, 0.0), (bx - 1.35, -0.05, 0.08), 0.01, 'metald'))
    for k, col in enumerate(('flora', 'aqua', 'flyel', 'skyb')):
        B.add(cbox2((sf[0] + 0.2 + k * 0.28, -0.18, 0.05), (sf[0] + 0.4 + k * 0.28, -0.12, 0.85), 0.03, col))
    gooseneck(B, F, -2.0, H + pp - 0.05, name='Lamp')
    gooseneck(B, F, 2.0, H + pp - 0.05, name='Lamp')
    meter_box(B, Rt, 5.6, 1.1)
    for x in (-1.6, 1.6):
        flat_ac(B, x, D - 2.5, H)
    wall_pipe(B, -W / 2 + 0.16, -0.08, H + pp - 0.1)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=sf[3] + 0.1, length=0.5, k=0.35)
    return H + pp + 0.05


# ---------------------------------------------------------------- F3-4: the Art Deco shops
def glass_tower(B, x, y, r, z0, z1, n=12):
    """A round glass-block tower at a corner (the Deco ice-cream parlour's): a drum of glass block between a
    stucco base and a stepped stucco cap."""
    mb = MB()
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = (x + r * math.cos(a0), y + r * math.sin(a0)); p1 = (x + r * math.cos(a1), y + r * math.sin(a1))
        fw = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        z = z0
        while z < z1 - 1e-4:
            za = min(z + 0.8, z1)
            s0 = (k * fw) % 0.8 / 0.8
            mb.face([(p0[0], p0[1], z), (p1[0], p1[1], z), (p1[0], p1[1], za), (p0[0], p0[1], za)], 'tex', None, 1.0,
                    lambda co, z=z, p0=p0, s0=s0, fw=fw: reg_uv('fl_glassblock', min(1.0, s0 + math.hypot(co.x - p0[0], co.y - p0[1]) / 0.8),
                                                            (co.z - z) / 0.8, 0.0))
            z = za
    B.add(mb.bm())
    for z, rr, t in ((z0 - 0.4, r + 0.05, 0.4), (z1, r + 0.08, 0.14), (z1 + 0.14, r - 0.05, 0.3), (z1 + 0.44, r - 0.2, 0.22)):
        cap, _ = lathe([(0.0, 0.0), (rr, 0.0), (rr, t), (0.0, t)], n, 'wall' if t > 0.2 else 'trim')
        xform(cap, T(x, y, z)); B.add(cap)


def cafe_set(B, x, y, chair='flred', table='whitep'):
    """A little round café table and two folding chairs on the sidewalk."""
    t, _ = lathe([(0.0, 0.72), (0.34, 0.72), (0.34, 0.76), (0.0, 0.76)], 10, table)
    B.add(t)
    xform(t, T(x, y, 0.0))
    B.add(tube([(x, y, 0.0), (x, y, 0.72)], 0.03, 'metald', 5))
    for dx in (-0.55, 0.55):
        cx = x + dx
        B.add(cbox2((cx - 0.2, y - 0.2, 0.44), (cx + 0.2, y + 0.2, 0.48), 0.01, chair))
        bx = cx + (0.18 if dx > 0 else -0.18)
        B.add(cbox2((bx - 0.03, y - 0.2, 0.48), (bx + 0.03, y + 0.2, 0.9), 0.01, chair))
        for ly in (y - 0.17, y + 0.17):
            B.add(tube([(cx - 0.17, ly, 0.0), (cx + 0.17, ly, 0.44)], 0.012, 'metald', 4))
            B.add(tube([(cx + 0.17, ly, 0.0), (cx - 0.17, ly, 0.44)], 0.012, 'metald', 4))


def deco_shop(B, sign, awn, glass_col=None, tower=False, fins=False, upper=False, shutter=False, sidewalk=None):
    """A one- (or two-) storey Art Deco shop: stucco in a pastel, a parapet with racing stripes and a stepped
    middle, an eyebrow ledge, a glass shopfront with its door, a striped awning, the shop's name over it, and
    by kind a glass-block column, a round glass-block tower, a two-storey front with louvred windows and fins,
    or a shut shopfront behind an accordion gate."""
    W, H, D = B.W, B.H, B.D
    pp = 0.75
    x0 = -W / 2 + (0.9 if glass_col or tower else 0.45)
    sf = (x0, W / 2 - 1.6, 0.0, 2.75) if not shutter else (-W / 2 + 0.5, W / 2 - 0.5, 0.0, 2.85)
    door_o = (W / 2 - 1.45, W / 2 - 0.5, 0.0, 2.5)
    ops = [sf] if shutter else [sf, door_o]
    if glass_col: ops.append((-W / 2 + 0.12, -W / 2 + 0.72, 0.3, H + pp - 0.4))
    if upper: ops.append((-W / 2 + 1.0, W / 2 - 1.2, 3.9, 5.3))
    top = [(-W / 2, H + pp), (-1.3, H + pp), (-1.3, H + pp + 0.35), (1.3, H + pp + 0.35), (1.3, H + pp), (W / 2, H + pp)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, top, ops, 0.0)
    wall(B, Rt, 0, D, H + pp, [], 0.0)
    wall(B, Lf, -D, 0, H + pp, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp, [], 0.0)
    flat_top(B, H, pp)
    if shutter:
        # the shut shop: a dark, empty room behind an accordion gate
        window(B, F, *sf, depth=0.22, fw=0.07, cols=2, frame='alu', glass='glass2', sill='conc', head=None, seed=961)
        tile_cells(B, F, sf[0] + 0.05, sf[1] - 0.05, 0.05, sf[3] - 0.05, 0.03, 'fl_gate', 0.8)
        for x in (sf[0] + 0.05, sf[1] - 0.05):
            put(B, F, fbox((x - 0.04, 0.0, 0.0), (x + 0.04, sf[3], 0.08), 0.005, 'galvw'))
        put(B, F, fbox((sf[0], sf[3] - 0.1, 0.0), (sf[1], sf[3], 0.1), 0.01, 'galvw'))
    else:
        window(B, F, *sf, depth=0.18, fw=0.07, cols=3, frame='alu', glass='glass3', sill='conc', head=None, seed=hash(sign) % 97)
        door(B, F, *door_o, mat='alu', glass=0.85, panels=((1, 1),), name='Door')
        awning(B, F, sf[0] - 0.1, door_o[1] + 0.1, 3.3, 1.05, 0.45, int((door_o[1] - sf[0]) / 0.38) | 1, mat_a=awn, mat_b='cream',
               valance=0.2, scallops=False)
    if glass_col: glass_block(B, F, -W / 2 + 0.12, -W / 2 + 0.72, 0.3, H + pp - 0.4)
    if tower: glass_tower(B, -W / 2 + 0.05, -0.15, 0.62, 0.4, H + pp + 0.5)
    if upper:
        window(B, F, -W / 2 + 1.0, W / 2 - 1.2, 3.9, 5.3, depth=0.16, fw=0.06, cols=3, rows=4, frame='trimw', glass='glass2', sill='trim',
               head=None, seed=962)
        eyebrow(B, F, -W / 2 + 0.8, W / 2 - 1.0, 5.4, out=0.42)
    if fins:
        for x in (W / 2 - 0.95, W / 2 - 0.55):
            B.add(cbox2((x - 0.08, -0.35, H - 1.5), (x + 0.08, 0.05, H + pp + 1.1), 0.03, 'trim'))
    # the sign band over the awning, the racing stripes along the parapet, the eyebrow
    # (the name between the eyebrow and the stripes, as tall as that leaves it)
    if sign:
        z1 = H + pp - 0.4
        z0 = max(3.47, z1 - 0.75 * min(1.0, (W - 1.6) / 6.5))
        decal(B, F, -W / 2 + (1.0 if glass_col or tower else 0.6), W / 2 - 0.6, z0, z1, 0.012, sign)
    stripes(B, F, -W / 2 - 0.01, W / 2 + 0.01, H + pp - 0.33, n=2, h=0.07, gap=0.08, mat='accentw')
    eyebrow(B, F, -W / 2, W / 2, 3.35, out=0.3, t=0.07)
    if sidewalk: sidewalk(B, F)
    for x in (-1.2, 1.2):
        flat_ac(B, x, D - 2.5, H)
    wall_pipe(B, W / 2 - 0.16, -0.08, H + pp - 0.1)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=3.3, length=0.5, k=0.35)
    return H + pp + (1.2 if fins else 0.4 if tower else 0.35)


def deco_surf(B):
    def out(B, F):
        for k, col in enumerate(('flyel', 'white', 'blueb')):
            surfboard(B, -B.W / 2 + 1.25 + 0.5 * k, -0.15 - 0.04 * k, col, lean=0.14, L=2.2)
        for x in (0.2, 1.6):
            pot(B, (x, -0.45, 0.0), 0.24, 0.42, 'pot3', 'bush', seed=971 + int(x * 10), scale=1.2)
    return deco_shop(B, 'sg_surfshop', 'blueb', glass_col=True, sidewalk=out)


def deco_cafe(B):
    def out(B, F):
        cafe_set(B, 0.2, -1.0)
        pot(B, (-B.W / 2 + 0.5, -0.45, 0.0), 0.24, 0.42, 'pot', 'flowers', seed=972, scale=1.1)
        decal(B, F, B.W / 2 - 1.4, B.W / 2 - 0.55, 1.0, 1.9, 0.01, 'sg_menu')
    return deco_shop(B, 'sg_havana', 'flred', upper=True, fins=True, sidewalk=out)


def deco_bait(B):
    def out(B, F):
        B.add(cbox2((0.6, -0.75, 0.0), (1.5, -0.3, 0.45), 0.04, 'flred'))
        B.add(cbox2((0.6, -0.75, 0.45), (1.5, -0.3, 0.52), 0.02, 'white'))
        for k, col in enumerate(('flred', 'flora', 'white')):
            b, _ = lathe([(0.0, 0.0), (0.11, 0.06), (0.12, 0.26), (0.06, 0.36), (0.0, 0.38)], 8, col)
            xform(b, T(B.W / 2 - 1.7 + 0.28 * k, -0.4, 2.95)); B.add(b)
            B.add(tube([(B.W / 2 - 1.7 + 0.28 * k, -0.4, 3.33), (B.W / 2 - 1.7 + 0.28 * k, -0.4, 3.5)], 0.008, 'rope', 3))
        B.add(tube([(-B.W / 2 + 1.0, -0.35, 0.0), (-B.W / 2 + 1.1, -0.3, 1.6)], 0.015, 'metald', 4))
        ring = [(-B.W / 2 + 1.1 + 0.22 * math.cos(a), -0.3, 1.82 + 0.22 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 11)]
        B.add(tube(ring, 0.015, 'flyel', 4, caps=False))
    return deco_shop(B, 'sg_bait', 'aquad', glass_col=True, sidewalk=out)


def deco_ice(B):
    def out(B, F):
        cafe_set(B, -0.4, -1.0, chair='pink', table='pink')
        B.feat('front', 'tilegrid', a0=-B.W / 2, a1=B.W / 2, b0=0.0, b1=0.6, tw=0.15, th=0.15, k=0.5, var=0.05)
        put(B, F, fbox((-B.W / 2 + 0.9, 0.0, 0.0), (B.W / 2 - 1.6, 0.6, 0.03), 0.005, 'aqua'))
    return deco_shop(B, 'sg_icecream', 'pink', tower=True, sidewalk=out)


def deco_shut(B):
    return deco_shop(B, None, 'aquad', shutter=True)


# ---------------------------------------------------------------- the street's small things
def bus_shelter(B):
    """A bus shelter: a teal steel frame, a glass back and ends, a flat roof, a bench, a BUS STOP plate."""
    W, H, D = B.W, B.H, B.D
    for x in (-W / 2, W / 2):
        for y in (0.0, D):
            B.add(cbox2((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, H), 0.01, 'aquad'))
    B.add(cbox2((-W / 2 - 0.15, -0.2, H), (W / 2 + 0.15, D + 0.1, H + 0.12), 0.02, 'aquad'))
    back = WF((0, D, 0), (-1, 0, 0), 'front')
    glass_panel(B, WF((0, D - 0.02, 0), (1, 0, 0), 'front'), -W / 2 + 0.05, W / 2 - 0.05, 0.3, H - 0.1, 0.0)
    for x in (-W / 2, W / 2):
        glass_panel(B, WF((x, 0.0, 0), (0, 1, 0), 'right'), 0.6, D - 0.05, 0.3, H - 0.1, 0.0)
    B.add(cbox2((-W / 2 + 0.3, D - 0.55, 0.44), (W / 2 - 0.3, D - 0.12, 0.5), 0.01, 'aquad'))
    B.add(cbox2((-W / 2 + 0.3, D - 0.16, 0.5), (W / 2 - 0.3, D - 0.1, 0.95), 0.01, 'aquad'))
    for x in (-W / 2 + 0.5, W / 2 - 0.5):
        B.add(box((x - 0.03, D - 0.5, 0.0), (x + 0.03, D - 0.2, 0.44), 'metald'))
    post_sign(B, W / 2 + 0.35, 0.0, 'sg_bus', 0.45, 0.45, z_bottom=2.1, post='metald')
    return H + 0.6


def school_zone(B):
    """A school-zone beacon: a pole with a solar panel, two amber flashers and the school sign with its arrow."""
    H = B.H
    B.add(tube([(0, 0, 0.0), (0, 0, H)], 0.05, 'galvw', 6))
    B.add(cbox2((-0.1, -0.1, 0.0), (0.1, 0.1, 0.3), 0.02, 'galvw'))
    sp = MB()
    sp.face([(-0.35, -0.2, H + 0.15), (0.35, -0.2, H + 0.15), (0.35, 0.25, H + 0.45), (-0.35, 0.25, H + 0.45)], 'solarp', (0, -1, 1), 1.0)
    B.add(sp.bm())
    B.add(tube([(0, 0, H), (0, 0.05, H + 0.3)], 0.02, 'galvw', 4))
    for x in (-0.28, 0.28):
        B.add(cbox2((x - 0.13, -0.08, H - 0.45), (x + 0.13, 0.1, H - 0.17), 0.02, 'black'))
        lt, _ = lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.03), (0.0, 0.05)], 10, 'flyel')
        xform(lt, T(x, -0.08, H - 0.31) @ R(math.pi / 2, 'X')); B.add(lt)
    post_sign(B, 0.0, -0.08, 'sg_schoolzone', 0.75, 0.75, z_bottom=H - 1.35, post='galvw')
    post_sign(B, 0.0, -0.08, 'sg_arrow', 0.6, 0.36, z_bottom=H - 1.8, post='galvw')
    return H + 0.5


def mailbox_fl(B):
    """A blue street collection box on four short legs, its rounded top and the pull-down slot."""
    B.add(cbox2((-0.3, -0.25, 0.3), (0.3, 0.25, 1.05), 0.04, 'blueb'))
    top, _ = lathe([(0.0, 0.0), (0.3, 0.0), (0.27, 0.12), (0.17, 0.2), (0.0, 0.22)], 12, 'blueb')
    xform(top, T(0, 0, 1.05) @ S(1.0, 0.83, 1.0)); B.add(top)
    B.add(cbox2((-0.18, -0.27, 0.88), (0.18, -0.24, 0.98), 0.01, 'chromew'))
    for x in (-0.24, 0.24):
        for y in (-0.19, 0.19):
            B.add(box((x - 0.03, y - 0.03, 0.0), (x + 0.03, y + 0.03, 0.3), 'blueb'))
    return 1.3


def hydrant_fl(B):
    """A fire hydrant painted yellow, its caps in a colour."""
    body, _ = lathe([(0.0, 0.0), (0.17, 0.0), (0.17, 0.06), (0.12, 0.08), (0.12, 0.55), (0.15, 0.58), (0.13, 0.66), (0.08, 0.74), (0.03, 0.8), (0.0, 0.8)], 10,
                    ['flyel', 'flyel', 'flyel', 'flyel', 'flyel', 'flyel', 'flyel', 'flyel', 'flyel'])
    B.add(body)
    for ang in (0.0, math.pi):
        c, s_ = math.cos(ang), math.sin(ang)
        B.add(tube([(0.1 * c, 0.1 * s_, 0.42), (0.2 * c, 0.2 * s_, 0.42)], 0.05, 'flyel', 6))
        B.add(tube([(0.2 * c, 0.2 * s_, 0.42), (0.23 * c, 0.23 * s_, 0.42)], 0.055, 'flred', 6))
    B.add(tube([(0, -0.1, 0.38), (0, -0.24, 0.38)], 0.07, 'flred', 6))
    return 0.85


def trash_fl(B):
    """A slatted steel litter bin in dark grey with a domed lid."""
    n = 14
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = 0.29 * math.cos(a), 0.29 * math.sin(a)
        B.add(cbox2((x - 0.035, y - 0.035, 0.05), (x + 0.035, y + 0.035, 0.92), 0.01, 'greyd'))
    for z in (0.05, 0.48, 0.88):
        ring = [(0.3 * math.cos(a), 0.3 * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 15)]
        B.add(tube(ring, 0.025, 'greyd', 4, caps=False))
    lid, _ = lathe([(0.0, 0.0), (0.33, 0.0), (0.33, 0.05), (0.2, 0.12), (0.0, 0.14)], 14, 'greyd')
    xform(lid, T(0, 0, 0.93)); B.add(lid)
    inner, _ = lathe([(0.0, 0.1), (0.25, 0.1), (0.25, 0.9)], 10, 'black')
    B.add(inner)
    return 1.1


def bench_fl(B):
    """A slatted park bench on cast legs."""
    W = B.W
    for k in range(3):
        B.add(cbox2((-W / 2, -0.25 + k * 0.16, 0.44), (W / 2, -0.12 + k * 0.16, 0.48), 0.01, 'woodc'))
    for k in range(3):
        B.add(cbox2((-W / 2, 0.17, 0.58 + k * 0.14), (W / 2, 0.21, 0.69 + k * 0.14), 0.01, 'woodc'))
    for x in (-W / 2 + 0.15, W / 2 - 0.15):
        B.add(cbox2((x - 0.04, -0.27, 0.0), (x + 0.04, -0.19, 0.46), 0.01, 'greyd'))
        B.add(cbox2((x - 0.04, 0.12, 0.0), (x + 0.04, 0.2, 1.0), 0.01, 'greyd'))
        B.add(cbox2((x - 0.04, -0.27, 0.42), (x + 0.04, 0.2, 0.46), 0.01, 'greyd'))
    return 1.05


def lamp_fl(B):
    """A teal street lamp: a slim post, a curved arm and a barn-style shade."""
    H = B.H
    B.add(cbox2((-0.14, -0.14, 0.0), (0.14, 0.14, 0.5), 0.03, 'aquad'))
    B.add(tube([(0, 0, 0.0), (0, 0, H)], 0.07, 'aquad', 8))
    arm = [(0.0, 0.0, H - 0.1)] + [(0.0, -0.9 * math.sin(math.pi / 2 * k / 6), H + 0.45 * math.sin(math.pi * k / 6)) for k in range(1, 7)]
    B.add(tube(arm, 0.04, 'aquad', 6))
    sh, _ = lathe([(0.0, -0.22), (0.32, -0.22), (0.3, -0.19), (0.1, -0.05), (0.06, 0.0), (0.0, 0.02)], 12, ['lamp', 'aquad', 'aquad', 'aquad', 'aquad'])
    xform(sh, T(0.0, -0.92, H - 0.02)); B.add(sh)
    B.lamps.append({'name': 'Lamp.0', 'center': [0.0, -0.92, round(H - 0.25, 3)]})
    return H + 0.5


def sign_access(B): post_sign(B, 0.0, 0.0, 'sg_access23', 0.75, 0.95, z_bottom=0.6); return 1.6
def sign_access_up(B): post_sign(B, 0.0, 0.0, 'sg_access', 0.7, 0.88, z_bottom=1.3); return 2.2
def sign_turtle(B): post_sign(B, 0.0, 0.0, 'sg_turtle', 0.7, 0.88, z_bottom=0.6); return 1.5
def sign_hurricane(B): post_sign(B, 0.0, 0.0, 'sg_hurricane', 0.8, 0.64, z_bottom=1.9, post='galvw'); return 2.6


def post_rope(B):
    """A run of timber posts with a sagging rope between them, keeping people off the dune."""
    W = B.W
    xs = np.linspace(-W / 2, W / 2, 4)
    for x in xs:
        B.add(cbox2((float(x) - 0.06, -0.06, 0.0), (float(x) + 0.06, 0.06, 0.8), 0.015, 'woodg'))
    for a, b in zip(xs[:-1], xs[1:]):
        pts = [(float(a + (b - a) * t), -0.07, 0.62 - 0.12 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 6)]
        B.add(tube(pts, 0.012, 'rope', 4, caps=False))
    return 0.85


def pole_signal(B):
    """A square concrete utility pole (as Florida's power company uses), a crossarm with insulators and line stubs,
    a galvanised mast arm out over the road with two signal heads, a pedestrian head and a push button."""
    H = B.H
    sec = []
    for z, s in ((0.0, 0.17), (H, 0.1)):
        sec.append((z, s))
    pole = MB()
    corners = lambda s: [(-s, -s), (s, -s), (s, s), (-s, s)]
    ca, cb = corners(0.17), corners(0.1)
    for i in range(4):
        (ax, ay), (bx, by) = ca[i], ca[(i + 1) % 4]
        (cx, cy), (dx, dy) = cb[i], cb[(i + 1) % 4]
        pole.face([(ax, ay, 0.0), (bx, by, 0.0), (dx, dy, H), (cx, cy, H)], 'concp', None, 1.0)
    pole.face([(x, y, H) for x, y in cb], 'concp', (0, 0, 1), 1.0)
    B.add(pole.bm())
    B.add(cbox2((-1.0, -0.06, H - 0.5), (1.0, 0.06, H - 0.38), 0.01, 'woodg'))
    for x in (-0.85, -0.3, 0.3, 0.85):
        ins, _ = lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.08), (0.04, 0.16), (0.0, 0.18)], 6, 'white')
        xform(ins, T(x, 0.0, H - 0.38)); B.add(ins)
        B.add(tube([(x, 0.0, H - 0.22), (x, -3.0, H - 0.6), (x, -6.0, H - 0.4)], 0.012, 'black', 3, caps=False))
        B.add(tube([(x, 0.0, H - 0.22), (x, 3.0, H - 0.6), (x, 6.0, H - 0.4)], 0.012, 'black', 3, caps=False))
    B.add(cbox2((-0.25, -0.25, H - 1.9), (0.25, 0.25, H - 1.2), 0.04, 'galvw'))                 # a transformer can
    # the mast arm, from the pole out to the right over the road (+x), its two heads hanging from it
    za = 5.6
    B.add(tube([(0.0, 0.0, za - 0.4), (0.2, 0.0, za), (4.6, 0.0, za + 0.25)], 0.08, 'galvw', 6))
    B.add(tube([(0.0, 0.0, za + 1.2), (2.2, 0.0, za + 0.16)], 0.03, 'galvw', 4))
    for x in (2.5, 4.3):
        B.add(tube([(x, 0.0, za + 0.18), (x, 0.0, za - 0.05)], 0.03, 'galvw', 4))
        B.add(cbox2((x - 0.18, -0.15, za - 1.15), (x + 0.18, 0.15, za - 0.05), 0.03, 'black'))
        for k, col in enumerate(('flred', 'flyel', 'green')):
            lt, _ = lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.03), (0.0, 0.04)], 10, col)
            xform(lt, T(x, -0.15, za - 0.25 - 0.33 * k) @ R(math.pi / 2, 'X')); B.add(lt)
            hood = [(x - 0.13, -0.16, za - 0.12 - 0.33 * k), (x + 0.13, -0.16, za - 0.12 - 0.33 * k), (x + 0.13, -0.32, za - 0.16 - 0.33 * k), (x - 0.13, -0.32, za - 0.16 - 0.33 * k)]
            hb = MB(); hb.face(hood, 'black', (0, 0, 1), 0.8); hb.face(list(reversed(hood)), 'black', (0, 0, -1), 0.6); B.add(hb.bm())
    B.add(cbox2((-0.18, -0.4, 2.3), (0.18, -0.17, 2.75), 0.02, 'black'))                         # the pedestrian head
    B.add(cbox2((-0.07, -0.25, 1.05), (0.07, -0.17, 1.25), 0.01, 'flyel'))                       # the push button
    return H + 0.1


def fence_chain(B):
    """A section of chain-link fence: galvanised posts, a top rail and the mesh (the field behind shows through
    the tile's diamonds only as paint)."""
    W, H = B.W, B.H
    for x in (-W / 2, W / 2):
        B.add(tube([(x, 0.0, 0.0), (x, 0.0, H + 0.05)], 0.035, 'galvw', 6))
    B.add(tube([(-W / 2, 0.0, H), (W / 2, 0.0, H)], 0.025, 'galvw', 5))
    for k in range(int(W / 0.25) + 1):                     # the mesh as thin wires each way (it must be seen through)
        x = -W / 2 + k * 0.25
        B.add(tube([(x, 0.0, 0.03), (min(W / 2, x + H), 0.0, 0.03 + min(H, W / 2 - x))], 0.006, 'galvw', 3, caps=False))
        B.add(tube([(x, 0.0, 0.03), (max(-W / 2, x - H), 0.0, 0.03 + min(H, x + W / 2))], 0.006, 'galvw', 3, caps=False))
    return H + 0.1


def soccer_goal(B):
    """A small white soccer goal with its net."""
    W, H, D = B.W, B.H, B.D
    B.add(tube([(-W / 2, 0, 0), (-W / 2, 0, H), (W / 2, 0, H), (W / 2, 0, 0)], 0.05, 'white', 6))
    B.add(tube([(-W / 2, 0, H), (-W / 2, D, 0.0), (W / 2, D, 0.0), (W / 2, 0, H)], 0.025, 'white', 5))
    for k in range(int(W / 0.25) + 1):
        x = -W / 2 + k * 0.25
        B.add(tube([(x, 0.0, H), (x, D, 0.0)], 0.006, 'white', 3, caps=False))
    for k in range(1, int(H / 0.25)):
        t = k * 0.25 / H
        B.add(tube([(-W / 2, D * (1 - t), H * t), (W / 2, D * (1 - t), H * t)], 0.006, 'white', 3, caps=False))
    return H + 0.1


def kayak_rack(B):
    """Kayaks and paddleboards on a timber rack under a sun sail, on the beach by the shack."""
    W, D = B.W, B.D
    for x in (-W / 2 + 0.2, W / 2 - 0.2):
        for y in (0.2, D - 0.2):
            B.add(cbox2((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, 1.3), 0.01, 'woodg'))
        for z in (0.35, 0.8, 1.25):
            B.add(cbox2((x - 0.05, 0.1, z - 0.05), (x + 0.05, D - 0.1, z), 0.01, 'woodg'))
    cols = ('flora', 'flora', 'flred', 'flyel', 'aqua', 'blueb')
    for k, z in enumerate((0.4, 0.85, 1.3)):
        for j in range(2):
            y = 0.35 + j * (D - 0.7)
            hull = [(-W / 2 - 0.2 + (W + 0.4) * t, 0.0) for t in np.linspace(0, 1, 9)]
            pts = [(x, y, z + 0.08 * math.sin(math.pi * (x + W / 2 + 0.2) / (W + 0.4))) for x, _ in hull]
            B.add(tube(pts, 0.17 if k < 2 else 0.05, cols[k * 2 + j], 6))
    for x, y in ((-W / 2 - 0.6, -0.4), (W / 2 + 0.8, -0.2), (W / 2 + 0.7, D + 0.4), (-W / 2 - 0.5, D + 0.3)):
        B.add(tube([(x, y, 0.0), (x, y, 2.7 if y < 0 else 2.2)], 0.04, 'woodg', 5))
    sail = MB()
    sail.face([(-W / 2 - 0.6, -0.4, 2.65), (W / 2 + 0.8, -0.2, 2.6), (W / 2 + 0.7, D + 0.4, 2.15), (-W / 2 - 0.5, D + 0.3, 2.2)], 'cream', (0, 0, 1), 1.0)
    sail.face([(-W / 2 - 0.5, D + 0.3, 2.18), (W / 2 + 0.7, D + 0.4, 2.13), (W / 2 + 0.8, -0.2, 2.58), (-W / 2 - 0.6, -0.4, 2.63)], 'cream', (0, 0, -1), 0.8)
    B.add(sail.bm())
    return 2.8


def volley_net(B):
    """A beach volleyball net between two posts."""
    W, H = B.W, B.H
    for x in (-W / 2, W / 2):
        B.add(tube([(x, 0, 0.0), (x, 0, H + 0.1)], 0.05, 'white', 6))
    B.add(cbox2((-W / 2, -0.01, H - 0.06), (W / 2, 0.01, H), 0.0, 'white'))
    B.add(cbox2((-W / 2, -0.01, H - 0.95), (W / 2, 0.01, H - 0.91), 0.0, 'white'))
    for k in range(int(W / 0.2) + 1):
        x = -W / 2 + k * 0.2
        B.add(tube([(x, 0.0, H - 0.93), (x, 0.0, H - 0.03)], 0.005, 'black', 3, caps=False))
    for k in range(1, 5):
        z = H - 0.93 + 0.18 * k
        B.add(tube([(-W / 2, 0.0, z), (W / 2, 0.0, z)], 0.005, 'black', 3, caps=False))
    return H + 0.15


# ---------------------------------------------------------------- F3-6: Seagrove High
def school_fl(B):
    """A Florida public high school: two long storeys of cream concrete block under a flat roof, ribbon windows
    with aluminium frames, a teal stair tower with a glass-block strip and the school's name on the building, a
    teal canopy over the entrance doors, AC units on the roof."""
    W, H, D = B.W, B.H, B.D
    tx0, tx1 = -3.0, 0.8                       # the stair tower
    wins = []
    for z in (1.0, 4.4):
        for a, b in ((-W / 2 + 1.0, tx0 - 1.0), (tx1 + 1.0, W / 2 - 1.0)):
            n = max(1, int((b - a) / 3.4))
            for k in range(n):
                u = a + (b - a) * k / n
                wins.append((u + 0.25, u + (b - a) / n - 0.25, z, z + 1.6))
    entry = (tx1 + 1.2, tx1 + 4.0, 0.0, 2.5)
    wins = [w for w in wins if not (w[2] < 2 and w[1] > entry[0] - 0.2 and w[0] < entry[1] + 0.2)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H, wins + [entry], 0.0)
    wall(B, Rt, 0, D, H, [(3.0, 6.0, 1.0, 2.6), (3.0, 6.0, 4.4, 6.0)], 0.0)
    wall(B, Lf, -D, 0, H, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0)
    flat_top(B, H, 0.6)
    B.feat('front', 'tilegrid', a0=-W / 2, a1=W / 2, b0=0.0, b1=H + 0.6, tw=0.4, th=0.2, bond=0.5, k=0.22, var=0.025)
    for k, w in enumerate(wins):
        window(B, F, *w, depth=0.16, fw=0.06, cols=3, frame='alu', glass=('glass0', 'glass1', 'glass2')[k % 3], sill='trim', head=None,
               seed=980 + k, cheap=k % 2 == 1)
    for z in (1.0, 4.4):
        window(B, Rt, 3.0, 6.0, z, z + 1.6, cols=3, frame='alu', glass='glass0', seed=999, cheap=True)
    window(B, F, *entry, depth=0.2, fw=0.07, cols=4, frame='alu', glass='glass3', sill=None, head=None, seed=978)
    # the stair tower: teal, standing proud and taller, a glass-block strip, the name on the cream band beside it
    B.add(cbox2((tx0, -0.5, 0.0), (tx1, 2.0, H + 1.6), 0.03, 'accent'))
    tF = WF((0, -0.5, 0), (1, 0, 0), 'front')
    tile_cells(B, tF, tx0 + 1.2, tx1 - 1.2, 0.8, H + 1.0, 0.02, 'fl_glassblock', 0.8)
    put(B, tF, fbox((tx0 + 1.1, 0.7, 0.0), (tx1 - 1.1, 0.8, 0.06), 0.01, 'trim'))
    put(B, tF, fbox((tx0 + 1.1, H + 1.0, 0.0), (tx1 - 1.1, H + 1.1, 0.06), 0.01, 'trim'))
    decal(B, F, W / 2 - 12.0, W / 2 - 3.0, H - 1.1, H - 0.3, 0.012, 'sg_schoolwall')
    # a teal band at the first floor and a canopy over the entrance
    put(B, F, fbox((-W / 2, 3.3, 0.0), (W / 2, 3.55, 0.05), 0.01, 'accentw'))
    B.add(cbox2((entry[0] - 0.6, -2.2, 2.85), (entry[1] + 0.6, 0.0, 3.05), 0.02, 'accentw'))
    for x in (entry[0] - 0.4, entry[1] + 0.4):
        B.add(cbox2((x - 0.07, -2.1, 0.0), (x + 0.07, -1.96, 2.85), 0.01, 'accentw'))
    for x in (-10.0, -4.0, 6.0, 11.0):
        flat_ac(B, x, D - 3.0, H)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.4, k=0.3)
    return H + 1.7


def walkway(B):
    """A covered walkway: a flat teal-trimmed canopy on slim teal posts, running back from the street (+Y)."""
    W, H, D = B.W, B.H, B.D
    for y in np.arange(0.2, D, 3.0):
        for x in (-W / 2 + 0.15, W / 2 - 0.15):
            B.add(cbox2((x - 0.07, float(y) - 0.07, 0.0), (x + 0.07, float(y) + 0.07, H), 0.01, 'accentw'))
    B.add(cbox2((-W / 2 - 0.2, -0.2, H), (W / 2 + 0.2, D, H + 0.14), 0.02, 'whitep'))
    B.add(cbox2((-W / 2 - 0.22, -0.22, H + 0.1), (W / 2 + 0.22, D + 0.02, H + 0.3), 0.02, 'accentw'))
    return H + 0.35


def portable(B):
    """A portable classroom: a long beige box on blocks, a door with a little ramp and rails, windows, an AC unit."""
    W, H, D = B.W, B.H, B.D
    z0 = 0.55
    for x in np.linspace(-W / 2 + 0.4, W / 2 - 0.4, 5):
        for y in (0.4, D - 0.4):
            B.add(box((float(x) - 0.2, y - 0.2, 0.0), (float(x) + 0.2, y + 0.2, z0), 'concw'))
    pf = WF((0, 0, z0), (1, 0, 0), 'front')
    ops = [(-W / 2 + 1.0, -W / 2 + 2.4, 0.9, 1.9), (-0.7, 0.7, 0.9, 1.9), (W / 2 - 2.8, W / 2 - 1.8, 0.0, 2.1)]
    wall(B, pf, -W / 2, W / 2, H, ops, 0.0, mode='rib', rib=(0.4, 0.02))
    for a, b, c, d in ops[:2]:
        window(B, pf, a, b, c, d, depth=0.06, fw=0.05, cols=2, frame='alu', glass='glass2', sill=None, head=None, seed=1001, cheap=True, register=False)
    door(B, pf, *ops[2], depth=0.06, mat='accent', glass=None, panels=((1, 1),), register=False, name='Door')
    B.add(box((-W / 2, 0.0, z0), (W / 2, D, z0 + H), 'wall', skip=('-y',)))
    B.add(cbox2((-W / 2 - 0.15, -0.15, z0 + H), (W / 2 + 0.15, D + 0.15, z0 + H + 0.15), 0.02, 'trim'))
    B.add(cbox2((W / 2 - 3.2, -1.2, z0 - 0.05), (W / 2 - 1.4, 0.0, z0), 0.01, 'galvw'))
    pipe_rail(B, [(W / 2 - 3.2, -1.2, z0), (W / 2 - 1.4, -1.2, z0)], h=0.9, mat='galvw', r=0.02)
    for k in range(3):
        B.add(box((W / 2 - 1.4 + 0.3 * k, -1.2, z0 * (2 - k) / 3 - 0.06), (W / 2 - 1.1 + 0.3 * k, -0.2, z0 * (2 - k) / 3), 'galvw'))
    ac_unit(B, WF((W / 2, 0, z0), (0, 1, 0), 'right'), 1.5, 1.2, w=0.7, h=0.6, d=0.3)
    return z0 + H + 0.2


def marquee(B):
    """The school's marquee sign: a low teal block on a planter base, the name panel and a dark message board."""
    W, H = B.W, B.H
    B.add(cbox2((-W / 2 - 0.2, -0.5, 0.0), (W / 2 + 0.2, 0.5, 0.55), 0.03, 'accent'))
    B.add(cbox2((-W / 2, -0.25, 0.55), (W / 2, 0.25, H), 0.03, 'whitep'))
    F = WF((0, -0.25, 0), (1, 0, 0), 'front')
    decal(B, F, -W / 2 + 0.12, W / 2 - 0.12, H - 0.95, H - 0.1, 0.01, 'sg_school')
    put(B, F, fbox((-W / 2 + 0.15, 0.75, 0.0), (W / 2 - 0.15, H - 1.05, 0.03), 0.01, 'black'))
    for k in range(5):
        x = -W / 2 + 0.5 + k * (W - 1.0) / 4
        B.add(blob((x, -0.42, 0.62), (0.28, 0.2, 0.2), 'leaf' if k % 2 else 'leafd', 7, 3, 1010 + k))
        if k % 2 == 0: B.add(blob((x, -0.48, 0.75), (0.1, 0.08, 0.08), 'fl2', 6, 2, 1020 + k))
    return H + 0.1


def flagpole_fl(B):
    """The school's flagpole: the US flag over Florida's."""
    H = B.H
    B.add(cbox2((-0.4, -0.4, 0.0), (0.4, 0.4, 0.25), 0.03, 'concw'))
    B.add(tube([(0, 0, 0.0), (0, 0, H)], 0.06, 'chromew', 8))
    B.add(blob((0, 0, H + 0.06), (0.09, 0.09, 0.09), 'gold', 6, 2, 1))
    for region, z, w, h in (('fl_flagus', H - 0.15, 1.9, 1.0), ('fl_flagfl', H - 1.35, 1.5, 1.0)):
        for side in (-1, 1):
            mb = MB()
            n = 6
            for k in range(n):
                a, b = k / n, (k + 1) / n
                ya, yb = 0.12 * math.sin(a * 4.0) * side * 0.0 + 0.1 * math.sin(a * 4.0), 0.1 * math.sin(b * 4.0)
                quad = [(0.06 + a * w, ya + side * 0.005, z - h), (0.06 + b * w, yb + side * 0.005, z - h), (0.06 + b * w, yb + side * 0.005, z),
                        (0.06 + a * w, ya + side * 0.005, z)]
                if side > 0: quad = list(reversed(quad))
                mb.face(quad, 'tex', (0, side, 0), 1.0 if side < 0 else 0.85,
                        lambda co, w=w, z=z, h=h, region=region: reg_uv(region, (co.x - 0.06) / w, (co.z - z + h) / h, 0.0))
            B.add(mb.bm())
    return H + 0.2


def fence_alu(B):
    """A section of white aluminium picket fence (the school's), with its posts."""
    W, H = B.W, B.H
    for x in (-W / 2, W / 2):
        B.add(cbox2((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, H + 0.08), 0.01, 'white'))
    for z in (0.12, H - 0.12):
        B.add(cbox2((-W / 2, -0.02, z - 0.03), (W / 2, 0.02, z + 0.03), 0.005, 'white'))
    for k in range(1, int(W / 0.12)):
        x = -W / 2 + k * 0.12
        B.add(box((x - 0.012, -0.012, 0.05), (x + 0.012, 0.012, H), 'white'))
    return H + 0.1


def school_gate(B):
    """The school's front gate: two stucco piers with ball caps and a pair of white aluminium gates swung open."""
    W, H = B.W, B.H
    for x in (-W / 2, W / 2):
        B.add(cbox2((x - 0.3, -0.3, 0.0), (x + 0.3, 0.3, H), 0.03, 'wall'))
        B.add(cbox2((x - 0.36, -0.36, H), (x + 0.36, 0.36, H + 0.12), 0.02, 'trim'))
        B.add(blob((x, 0.0, H + 0.32), (0.2, 0.2, 0.2), 'trim', 8, 4, 3))
    gw = W / 2 - 0.3
    for sx in (-1, 1):
        hx = sx * (W / 2 - 0.3)
        ang = sx * 1.25
        c, s_ = math.cos(ang), math.sin(ang)
        P = lambda u, z: (hx - sx * u * c, -u * abs(s_), z)        # swung open toward the street
        for z in (0.15, H - 0.45):
            B.add(tube([P(0.0, z), P(gw, z)], 0.025, 'white', 4))
        for k in range(1, int(gw / 0.12)):
            u = k * 0.12
            B.add(tube([P(u, 0.08), P(u, H - 0.35 + 0.15 * math.sin(math.pi * u / gw))], 0.011, 'white', 3))
    return H + 0.5


# ================================================================ Home Street (the user's chapter 1 references)
def screen_panels(B, wf, u0, u1, v0, v1, cols=3, out=0.0):
    """A screened porch's front: the dark screen mesh between white frame members (the room behind barely shows)."""
    tile_cells(B, wf, u0, u1, v0, v1, out - 0.02, 'fl_screen', 0.8)
    for k in range(cols + 1):
        u = u0 + (u1 - u0) * k / cols
        put(B, wf, fbox((u - 0.05, v0, out - 0.02), (u + 0.05, v1, out + 0.06), 0.008, 'trim'))
    for v in (v0, (v0 + v1) * 0.45, v1 - 0.05):
        put(B, wf, fbox((u0, v, out - 0.02), (u1, v + 0.06, out + 0.05), 0.006, 'trim'))


def ranch(B):
    """The Florida concrete-block ranch house (the kid's home, after the first reference): smooth stucco in a faded pastel
    (part 1), a low hipped roof of white concrete tile, a striped aluminium awning over the jalousie window, the front door in
    its own colour (part 2: the home's red) up two terrazzo steps, a screened porch on the right, an AC condenser on its pad,
    the meter, a coach lamp, white gutters."""
    W, H, D = B.W, B.H, B.D
    win = (-W / 2 + 0.9, -W / 2 + 3.4, 1.0, 2.2)
    door_o = (-1.7, -0.7, 0.3, 2.45)
    porch = (0.3, W / 2 - 0.5, 0.3, 2.6)
    F, Rt, Lf, Bk = stucco_box(B, -W / 2, W / 2, 0.0, D, H, fronts=[win, door_o, porch], rights=[(2.0, 3.4, 1.0, 2.2)],
                               lefts=[(-6.0, -4.6, 1.0, 2.2)])
    cal_window(B, F, *win, cols=2, rows=4, seed=1101, glass='glass2')
    awning(B, F, win[0] - 0.15, win[1] + 0.15, win[3] + 0.42, 0.75, 0.35, 9, mat_a='whitep', mat_b='skyb', valance=0.1, scallops=False)
    door(B, F, *door_o, depth=0.14, mat='accent', glass=0.32, panels=((1, 2),), name='Door')
    steps(B, F, door_o[0] - 0.35, door_o[1] + 0.35, [0.3, 0.15], tread=0.32)
    lantern(B, F, door_o[1] + 0.35, 2.05, out=0.14, name='Lamp')
    # the screened porch: its room (a chair inside), the screen and frame
    shop_room(B, porch[0], porch[1], porch[2], porch[3], 2.4, floor='concw')
    B.add(cbox2((porch[0] + 1.2, 1.2, 0.3), (porch[0] + 1.8, 1.8, 0.75), 0.05, 'white'))
    screen_panels(B, F, porch[0], porch[1], porch[2], porch[3], cols=3)
    put(B, F, fbox((porch[0] - 0.1, 0.0, -0.02), (porch[1] + 0.1, 0.3, 0.12), 0.01, 'concw'))
    cal_window(B, Rt, 2.0, 3.4, 1.0, 2.2, cols=2, rows=4, seed=1102, cheap=True)
    cal_window(B, Lf, -6.0, -4.6, 1.0, 2.2, cols=2, rows=4, seed=1103, cheap=True)
    top = hip(B, -W / 2, W / 2, 0.0, D, H, B.RH, over=0.5)
    gutter(B, -W / 2 - 0.5, W / 2 + 0.5, -0.5, H - 0.04, pipe_x=W / 2 - 0.16, pipe_wall_y=-0.07)
    condenser(B, -W / 2 + 0.75, -0.7, wall_y=-0.07, z_in=1.4)
    meter_box(B, F, -W / 2 + 3.9, 1.3)
    wall_vent(B, F, porch[0] - 0.6, 0.18)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.45, k=0.3)
    return top + 0.62


def ranch_small(B):
    """A small Florida block house (the pink and the yellow ones in the references): stucco, a white concrete-tile hip roof,
    jalousie windows (one under a striped awning, one with a louvred shutter), the door in its colour, the AC unit, the meter."""
    W, H, D = B.W, B.H, B.D
    w1 = (-W / 2 + 0.7, -W / 2 + 2.7, 1.0, 2.2)
    door_o = (-0.35, 0.6, 0.15, 2.3)
    w2 = (1.4, W / 2 - 0.8, 1.0, 2.2)
    F, Rt, Lf, Bk = stucco_box(B, -W / 2, W / 2, 0.0, D, H, fronts=[w1, door_o, w2], rights=[(2.4, 3.6, 1.0, 2.2)])
    cal_window(B, F, *w1, cols=2, rows=4, seed=1111, glass='glass1')
    awning(B, F, w1[0] - 0.15, w1[1] + 0.15, w1[3] + 0.4, 0.7, 0.32, 7, mat_a='whitep', mat_b='accentw', valance=0.1, scallops=False)
    cal_window(B, F, *w2, cols=2, rows=4, seed=1112, glass='glass2')
    # a louvred storm shutter propped beside the right window
    sh = fbox((w2[1] + 0.12, w2[2] - 0.05, 0.0), (w2[1] + 0.12 + (w2[1] - w2[0]) * 0.5, w2[3] + 0.05, 0.05), 0.01, 'tex')
    uv_fn(sh, faces_facing(sh, (0, 0, 1), 0.9), 'louvre', lambda co: ((co.x - w2[1]) / 0.8, (co.y - w2[2]) / 1.2), 0.02)
    put(B, F, sh)
    door(B, F, *door_o, depth=0.14, mat='accent', glass=None, panels=((1, 2),), name='Door')
    steps(B, F, door_o[0] - 0.3, door_o[1] + 0.3, [0.15], tread=0.34)
    cal_window(B, Rt, 2.4, 3.6, 1.0, 2.2, cols=2, rows=4, seed=1113, cheap=True)
    top = hip(B, -W / 2, W / 2, 0.0, D, H, B.RH, over=0.45)
    gutter(B, -W / 2 - 0.45, W / 2 + 0.45, -0.45, H - 0.04, pipe_x=-W / 2 + 0.16, pipe_wall_y=-0.07)
    condenser(B, W / 2 + 0.75, 1.2, wall_x=W / 2 + 0.07, z_in=1.4)
    meter_box(B, F, door_o[1] + 0.55, 1.35)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.45, k=0.3)
    return top + 0.62


def gable_metal(B, x0, x1, y0, y1, ze, rise, over=0.35, mat='roofp', seam=0.45):
    """A standing-seam metal gable roof, its gable to the street (the ridge along Y), seams down both slopes."""
    X0, X1, Y0, Y1 = x0 - over, x1 + over, y0 - over, y1 + over
    xm = (X0 + X1) / 2
    zt, zr = ze + 0.08, ze + rise + 0.08
    mb = MB()
    mb.face([(X0, Y0, zt), (xm, Y0, zr), (xm, Y1, zr), (X0, Y1, zt)], mat, (-1, 0, 1), 1.0)
    mb.face([(xm, Y0, zr), (X1, Y0, zt), (X1, Y1, zt), (xm, Y1, zr)], mat, (1, 0, 1), 1.0)
    for x in (X0, X1):
        mb.face([(x, Y0, ze), (x, Y1, ze), (x, Y1, zt), (x, Y0, zt)], 'roofw', (1 if x > xm else -1, 0, 0), 0.7)
    # the gable end over the front wall, in the walls' colour (its eaves' edge in trim)
    mb.face([(x0, y0 + 0.02, ze), (xm, y0 + 0.02, zr - 0.12), (x1, y0 + 0.02, ze)], 'wallw', (0, -1, 0), 0.95)
    mb.face([(X0, Y0, ze), (xm, Y0, zr - 0.04), (xm, Y0, zr - 0.12), (X0 + 0.2, Y0, ze)], 'trim', (0, -1, 0), 0.9)
    mb.face([(xm, Y0, zr - 0.04), (X1, Y0, ze), (X1 - 0.2, Y0, ze), (xm, Y0, zr - 0.12)], 'trim', (0, -1, 0), 0.9)
    B.add(mb.bm())
    y = Y0 + seam * 0.5
    while y < Y1:
        for xa, xb in ((X0, xm), (xm, X1)):
            za = zt + (zr - zt) * (0 if xa == X0 else 1) + 0.025; zb = zt + (zr - zt) * (1 if xa == X0 else 0) + 0.025
            B.add(tube([(xa, y, za), (xb, y, zb)], 0.012, 'roofw', 3, caps=False))
        y += seam
    B.add(tube([(xm, Y0, zr + 0.03), (xm, Y1, zr + 0.03)], 0.05, 'roofw', 5))
    return zr


def cottage(B):
    """An Old Florida frame cottage (Granny's, the second reference): lap siding in a faded pastel (part 1) raised on piers
    over a white lattice skirt, a standing-seam metal roof with its gable to the street, a deep front porch on white posts with
    a railing and a porch swing, steps up the middle, a door and windows with louvred shutters (part 2), a fern hanging."""
    W, H, D = B.W, B.H, B.D
    fl = 0.6                                       # the raised floor
    pd = 1.5                                       # the porch's depth in front of the wall
    door_o = (-0.5, 0.5, fl, fl + 2.15)
    wins = [(-W / 2 + 0.8, -W / 2 + 2.2, fl + 0.8, fl + 2.1), (W / 2 - 2.2, W / 2 - 0.8, fl + 0.8, fl + 2.1)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H, [door_o] + wins, fl, mode='lap')
    wall(B, Rt, 0, D, H, [(2.5, 3.7, fl + 0.8, fl + 2.1)], fl, mode='lap')
    wall(B, Lf, -D, 0, H, [], fl, mode='lap')
    wall(B, Bk, -W / 2, W / 2, H, [], fl, mode='lap')
    box_shell_corners(B, fl, H, 0.1, mat='trim')
    for k, w in enumerate(wins):
        window(B, F, *w, depth=0.12, fw=0.06, cols=2, rows=2, frame='trimw', glass=('glass1', 'glass0')[k], sill='trim', head=None, seed=1121 + k)
        for s in (-1, 1):
            u = w[0] - 0.42 if s < 0 else w[1] + 0.02
            sh = fbox((u, w[2] - 0.05, 0.0), (u + 0.4, w[3] + 0.05, 0.05), 0.01, 'tex')
            uv_fn(sh, faces_facing(sh, (0, 0, 1), 0.9), 'louvre', lambda co, u=u, w=w: ((co.x - u) / 0.4, (co.y - w[2]) / (w[3] - w[2])), 0.02)
            put(B, F, sh)
    window(B, Rt, 2.5, 3.7, fl + 0.8, fl + 2.1, cols=2, rows=2, frame='trimw', glass='glass0', seed=1123, cheap=True)
    door(B, F, *door_o, depth=0.1, mat='accent', glass=0.55, panels=((1, 1),), name='Door')
    # the skirt under the house: piers and lattice
    tile_cells(B, F, -W / 2, W / 2, 0.0, fl - 0.05, 0.02, 'fl_lattice', 0.8)
    # the porch: its floor, posts, railing either side of the steps, its shed roof, the swing
    B.add(cbox2((-W / 2 - 0.1, -pd, fl - 0.12), (W / 2 + 0.1, 0.0, fl), 0.02, 'woodg'))
    tile_cells(B, WF((0, -pd, 0), (1, 0, 0), 'front'), -W / 2 - 0.1, W / 2 + 0.1, 0.0, fl - 0.12, 0.0, 'fl_lattice', 0.8)
    for x in (-W / 2 + 0.05, -0.85, 0.85, W / 2 - 0.05):
        B.add(cbox2((x - 0.08, -pd + 0.05, fl), (x + 0.08, -pd + 0.21, H - 0.15), 0.01, 'trim'))
    for a, b in ((-W / 2 + 0.05, -0.85), (0.85, W / 2 - 0.05)):
        pipe_rail(B, [(a, -pd + 0.13, fl), (b, -pd + 0.13, fl)], h=0.85, mat='white', bars=0.12, r=0.02, mid=False)
    for k in range(3):
        z = fl - 0.2 * (k + 1)
        B.add(cbox2((-0.8, -pd - 0.24 * (k + 1), z), (0.8, -pd - 0.24 * k, z + 0.2), 0.01, 'woodg'))
    shed(B, -W / 2 - 0.2, W / 2 + 0.2, -pd - 0.25, 0.05, H - 0.2, H + 0.25, t=0.1, pitch=0.3, mat='roof', edge_mat='roofw', fascia_mat='trim', feat=False)
    # the swing on its chains, on the right of the porch
    sx = W / 2 - 1.6
    for dx in (-0.6, 0.6):
        B.add(tube([(sx + dx, -pd * 0.55, H - 0.25), (sx + dx, -pd * 0.55, fl + 0.55)], 0.008, 'black', 3))
    B.add(cbox2((sx - 0.65, -pd * 0.55 - 0.22, fl + 0.45), (sx + 0.65, -pd * 0.55 + 0.22, fl + 0.52), 0.01, 'white'))
    B.add(cbox2((sx - 0.65, -pd * 0.55 + 0.18, fl + 0.52), (sx + 0.65, -pd * 0.55 + 0.24, fl + 0.95), 0.01, 'white'))
    # a fern hanging at the left
    B.add(tube([(-W / 2 + 0.9, -pd * 0.6, H - 0.25), (-W / 2 + 0.9, -pd * 0.6, H - 0.7)], 0.006, 'black', 3))
    B.add(blob((-W / 2 + 0.9, -pd * 0.6, H - 0.85), (0.35, 0.35, 0.22), 'leafl', 7, 3, 1124))
    top = gable_metal(B, -W / 2, W / 2, 0.0, D, H, B.RH, over=0.35)
    vv = fbox((-0.4, H + 0.55, -0.02), (0.4, H + 1.05, 0.03), 0.004, 'tex')
    uv_fn(vv, faces_facing(vv, (0, 0, 1), 0.9), 'louvre', lambda co: ((co.x + 0.4) / 0.8, (co.y - H - 0.55) / 0.5), 0.02)
    put(B, WF((0, -0.3, 0), (1, 0, 0), 'front'), vv)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.2, length=0.6, k=0.35)
    return top + 0.1


def church_fl(B):
    """St Mary's in Florida (the second reference): a white stucco Mission church, its gable to the street under a curved
    parapet with a quatrefoil window, red barrel-tile roof, an arched timber door up brick steps, lanterns either side, a
    square bell tower at the left with an open arched belfry, its bell, a little tiled cap and a cross."""
    W, H, D = B.W, B.H, B.D
    n = 11
    curve = [(-W / 2, H)] + [(u, H + 2.4 * math.cos((u / (W / 2)) * math.pi / 2) ** 0.8 + 0.3 * (abs(u) < 1.2))
                             for u in np.linspace(-W / 2 + 0.01, W / 2 - 0.01, n)] + [(W / 2, H)]
    door_o = (-0.9, 0.9, 0.45, 3.0)
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, curve, [door_o, (-W / 2 + 1.0, -W / 2 + 1.8, 1.6, 3.6), (W / 2 - 1.8, W / 2 - 1.0, 1.6, 3.6)], 0.0)
    wall(B, Rt, 0, D, H, [(3.0, 3.8, 1.6, 3.6), (7.0, 7.8, 1.6, 3.6)], 0.0)
    wall(B, Lf, -D, 0, H, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0)
    door(B, F, *door_o, depth=0.3, mat='woodd', glass=None, panels=((2, 3),), double=True, name='Door')
    arch_head(B, F, door_o[0], door_o[1], door_o[3], band=0.22, glass='glass0', mat='trim')
    for u0 in (-W / 2 + 1.0, W / 2 - 1.8):
        window(B, F, u0, u0 + 0.8, 1.6, 3.6, depth=0.25, fw=0.05, cols=1, rows=2, frame='woodd', glass='glass3', sill='trim', head=None, seed=1131)
        arch_head(B, F, u0, u0 + 0.8, 3.6, band=0.1, glass='glass3')
        lantern(B, F, u0 + (1.3 if u0 < 0 else -0.5), 2.4, out=0.15, name='Lamp')
    for wo in ((3.0, 3.8), (7.0, 7.8)):
        window(B, Rt, wo[0], wo[1], 1.6, 3.6, cols=1, rows=2, frame='woodd', glass='glass3', seed=1132, cheap=True)
    # the quatrefoil over the door
    for dx, dy in ((0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)):
        porthole(B, F, dx, H + 0.6 + dy, r=0.3, mat='trim')
    steps(B, F, door_o[0] - 0.6, door_o[1] + 0.6, [0.45, 0.3, 0.15], tread=0.34, mat='accentw')
    pitched(B, 'y', -W / 2 - 0.3, W / 2 + 0.3, 0.2, D + 0.3, H - 0.15, 2.0, mat='roof', barge=(False, True))
    B.feat('roof', 'hip', x0=-W / 2 - 0.3, x1=W / 2 + 0.3, y0=0.2, y1=D + 0.3, row=0.32, pitch=0.25)
    # the bell tower on the left, a little forward of the nave
    tx, ty, tw, th = -W / 2 - 1.5, -0.3, 2.8, 9.5
    TF = WF((tx - tw / 2, ty, 0), (1, 0, 0), 'front')
    wall(B, TF, 0.0, tw, th, [(0.6, tw - 0.6, th - 2.6, th - 0.8)], 0.0)
    for wf, a, b in ((WF((tx + tw / 2, ty, 0), (0, 1, 0), 'right'), 0.0, tw), (WF((tx - tw / 2, ty + tw, 0), (0, -1, 0), 'left'), 0.0, tw),
                     (WF((tx + tw / 2, ty + tw, 0), (-1, 0, 0), 'front'), 0.0, tw)):
        wall(B, wf, a, b, th, [(0.6, tw - 0.6, th - 2.6, th - 0.8)], 0.0)
    arch_head(B, TF, 0.6, tw - 0.6, th - 0.8, band=0.15, glass='glass2', mat='trim')
    bell, _ = lathe([(0.0, 0.0), (0.42, 0.0), (0.38, 0.12), (0.24, 0.55), (0.12, 0.7), (0.0, 0.72)], 12, 'brass')
    xform(bell, T(tx, ty + tw / 2, th - 2.1)); B.add(bell)
    B.add(box((tx - tw / 2 - 0.1, ty - 0.1, th - 2.7), (tx + tw / 2 + 0.1, ty + tw + 0.1, th - 2.6), 'trim'))
    capz = hip(B, tx - tw / 2, tx + tw / 2, ty, ty + tw, th, 1.1, over=0.25, caps=True)
    B.add(tube([(tx, ty + tw / 2, capz), (tx, ty + tw / 2, capz + 1.0)], 0.05, 'black', 5))
    B.add(tube([(tx - 0.28, ty + tw / 2, capz + 0.72), (tx + 0.28, ty + tw / 2, capz + 0.72)], 0.05, 'black', 5))
    for x in (door_o[0] - 1.0, door_o[1] + 1.0):
        pot(B, (x, -1.3, 0.0), 0.32, 0.55, 'pot', 'flowers', seed=1133 + int(x * 10), scale=1.3)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.5, k=0.3)
    return th + 1.3


def mailbox_post(B):
    """A rural mailbox on a timber post at the kerb, its flag down."""
    B.add(cbox2((-0.05, -0.05, 0.0), (0.05, 0.05, 1.05), 0.01, 'woodg'))
    B.add(cbox2((-0.12, -0.25, 0.95), (0.12, 0.25, 1.05), 0.01, 'woodg'))
    box_, _ = lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.42), (0.0, 0.42)], 10, 'galvw')
    xform(box_, T(0, -0.21, 1.17) @ R(math.pi / 2, 'X')); B.add(box_)
    B.add(cbox2((-0.12, -0.21, 1.05), (0.12, 0.21, 1.17), 0.01, 'galvw'))
    B.add(cbox2((0.12, 0.05, 1.12), (0.14, 0.1, 1.35), 0.005, 'flred'))
    return 1.4


def golf_cart(B):
    """A groundskeeper's utility golf cart (the Home Street's ride, LevelBuildKit.GolfCart): white body, a green flat deck the
    whole length at 0.95 m (no canopy over it, so the kid rides on it), four wheels, a little amber beacon."""
    L, Wd = B.W, B.D
    B.add(cbox2((-L / 2 + 0.05, -Wd / 2, 0.32), (L / 2 - 0.05, Wd / 2, 0.82), 0.06, 'white'))
    B.add(cbox2((L / 2 - 0.55, -Wd / 2 + 0.05, 0.3), (L / 2, Wd / 2 - 0.05, 0.85), 0.12, 'white'))
    B.add(cbox2((-L / 2, -Wd / 2 - 0.03, 0.85), (L / 2, Wd / 2 + 0.03, 0.95), 0.02, 'aquad'))
    for x in np.linspace(-L / 2 + 0.2, L / 2 - 0.2, 6):
        B.add(box((float(x) - 0.02, -Wd / 2, 0.95), (float(x) + 0.02, Wd / 2, 0.965), 'greyd'))
    for x in (-L / 2 + 0.42, L / 2 - 0.42):
        for y in (-Wd / 2 - 0.02, Wd / 2 + 0.02):
            wh, _ = lathe([(0.0, -0.09), (0.22, -0.09), (0.24, 0.0), (0.22, 0.09), (0.0, 0.09)], 12, 'rubber')
            xform(wh, T(x, y, 0.24) @ R(math.pi / 2, 'X')); B.add(wh)
    B.add(tube([(-L / 2 + 0.12, Wd / 2 - 0.12, 0.95), (-L / 2 + 0.12, Wd / 2 - 0.12, 1.35)], 0.02, 'greyd', 4))
    bl, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.1), (0.0, 0.13)], 8, 'flora')
    xform(bl, T(-L / 2 + 0.12, Wd / 2 - 0.12, 1.35)); B.add(bl)
    for x in (L / 2 - 0.02,):
        for y in (-Wd / 2 + 0.2, Wd / 2 - 0.2):
            hl, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.02), (0.0, 0.03)], 8, 'lamp')
            xform(hl, T(x, y, 0.62) @ R(math.pi / 2, 'Y')); B.add(hl)
    return 1.5


def sprinkler(B):
    """A pop-up lawn sprinkler on the verge, its head up and three thin arcs of spray (the jets themselves are the game's)."""
    hd, _ = lathe([(0.0, 0.0), (0.06, 0.0), (0.05, 0.14), (0.03, 0.18), (0.0, 0.18)], 10, 'black')
    B.add(hd)
    rim, _ = lathe([(0.12, 0.0), (0.16, 0.0), (0.16, 0.02), (0.12, 0.02)], 12, 'greyd')
    B.add(rim)
    for k, a in enumerate((-0.55, 0.0, 0.55)):
        d = np.array((math.sin(a), -math.cos(a), 0.0))
        pts = [(d[0] * r, d[1] * r, 0.18 + 1.6 * (r / 2.2) - 1.3 * (r / 2.2) ** 2) for r in np.linspace(0.0, 2.2, 8)]
        B.add(tube(pts, 0.018, 'water', 4, caps=False))
    return 0.9


def draw_leaf(B):
    """One leaf of the canal's bascule drawbridge (its origin at the hinge, reaching +X 2.5 m; the game scales it to the gap):
    a steel deck across the street's footpath and verge, a yellow edge at its tip, a low kerb in front and a railing behind
    (none between the kid and the camera), the counterweight's top under the hinge."""
    L = B.W
    B.add(cbox2((0.0, -1.75, -0.3), (L, 1.75, 0.0), 0.02, 'grey'))
    for x in np.arange(0.15, L, 0.3):
        B.add(box((float(x) - 0.012, -1.7, -0.002), (float(x) + 0.012, 1.7, 0.006), 'greyd'))
    B.add(box((L - 0.12, -1.75, -0.29), (L - 0.02, 1.75, 0.01), 'flyel'))
    B.add(cbox2((0.0, -1.78, 0.0), (L, -1.66, 0.12), 0.01, 'grey'))
    pipe_rail(B, [(0.05, 1.68, 0.0), (L - 0.05, 1.68, 0.0)], h=1.05, posts=1.2, mat='skyb', bars=0.0, r=0.025)
    B.add(cbox2((-0.7, -1.7, -1.4), (0.2, 1.7, -0.3), 0.03, 'greyd'))
    return 1.1


def draw_tower(B):
    """The bridge tender's house on the bank: a little square tower of white stucco, windows on every side, a teal hipped
    metal roof, the door to the street."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Lf, Bk = stucco_box(B, -W / 2, W / 2, 0.0, D, H, fronts=[(-0.45, 0.45, 0.0, 2.1), (-0.8, 0.8, 2.9, 3.9)],
                               rights=[(0.5, D - 0.5, 2.9, 3.9)], lefts=[(-D + 0.5, -0.5, 2.9, 3.9)])
    door(B, F, -0.45, 0.45, 0.0, 2.1, depth=0.1, mat='accent', glass=0.4, panels=((1, 1),), name='Door')
    window(B, F, -0.8, 0.8, 2.9, 3.9, depth=0.12, fw=0.05, cols=3, frame='alu', glass='glass0', sill='trim', head=None, seed=1141)
    window(B, Rt, 0.5, D - 0.5, 2.9, 3.9, cols=2, frame='alu', glass='glass1', seed=1142, cheap=True)
    window(B, Lf, -D + 0.5, -0.5, 2.9, 3.9, cols=2, frame='alu', glass='glass1', seed=1143, cheap=True)
    eyebrow(B, F, -1.0, 1.0, 4.0, out=0.4)
    return hip_plain(B, -W / 2, W / 2, 0.0, D, H, 1.0, over=0.35, mat='roofp', seams=0.4) + 0.1


def gate_post(B):
    """The gate arm's post on the road: a grey cabinet on a pole, the arm's pivot at its top (the arm is GateArmFL)."""
    B.add(cbox2((-0.18, -0.18, 0.0), (0.18, 0.18, 0.9), 0.03, 'greyd'))
    B.add(cbox2((-0.14, -0.2, 0.55), (0.14, -0.18, 0.75), 0.01, 'flyel'))
    return 1.0


def gate_arm(B):
    """The drawbridge's traffic gate arm, upright at rest (its origin at the pivot; the drawbridge turns it down across the
    road): red and white bands, a lamp at its tip."""
    L = B.H
    for k in range(int(L / 0.5)):
        B.add(cbox2((-0.05, -0.05, k * 0.5), (0.05, 0.05, (k + 1) * 0.5), 0.01, 'flred' if k % 2 else 'white'))
    lp, _ = lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.06), (0.0, 0.1)], 8, 'neonr')
    xform(lp, T(0, 0, L)); B.add(lp)
    return L + 0.1


def canal_rail(B):
    """A concrete bridge balustrade (the canal bridge of the references): posts with teal inset panels and two rails, 5 m."""
    W = B.W
    for x in np.linspace(-W / 2, W / 2, 3):
        B.add(cbox2((float(x) - 0.2, -0.2, 0.0), (float(x) + 0.2, 0.2, 1.15), 0.03, 'concp'))
        B.add(cbox2((float(x) - 0.13, -0.21, 0.3), (float(x) + 0.13, -0.2, 0.9), 0.01, 'aqua'))
        B.add(cbox2((float(x) - 0.25, -0.25, 1.15), (float(x) + 0.25, 0.25, 1.25), 0.02, 'concp'))
    for z0, z1 in ((0.0, 0.25), (0.55, 0.68), (0.95, 1.08)):
        B.add(cbox2((-W / 2, -0.12, z0), (W / 2, 0.12, z1), 0.02, 'concp'))
    return 1.3


def dock(B):
    """A canal-side boat dock: a timber deck on piles, a boat lift's posts and cradle with a white boat in it under a canopy."""
    W, D = B.W, B.D
    for x in (-W / 2 + 0.1, -W / 2 + 0.9):
        for y in np.arange(0.2, D, 1.6):
            B.add(tube([(x, float(y), -1.5), (x, float(y), 0.15)], 0.09, 'woodg', 6))
    B.add(cbox2((-W / 2, 0.0, 0.0), (-W / 2 + 1.0, D, 0.1), 0.01, 'woodg'))
    bx = 0.6
    for y in (0.6, D - 0.6):
        for x in (bx - 1.1, bx + 1.1):
            B.add(tube([(x, y, -1.5), (x, y, 2.6)], 0.08, 'white', 6))
    B.add(cbox2((bx - 1.25, 0.4, 2.55), (bx + 1.25, D - 0.4, 2.65), 0.02, 'white'))
    hull = [(bx + 0.9 * math.cos(a) * (0.6 if math.sin(a) > 0.95 else 1.0), 1.0 + (D - 2.0) * (0.5 + 0.5 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 18)[:-1]]
    hb = extrude_poly(hull, 0.75, 'white', side_mat='white', back=True)
    xform(hb, T(0, 0, 0.35)); B.add(hb)
    B.add(box((bx - 0.92, 1.0, 0.75), (bx + 0.92, D - 1.0, 0.82), 'aqua'))
    B.add(cbox2((bx - 0.5, D * 0.45, 1.1), (bx + 0.5, D * 0.6, 1.5), 0.05, 'glass'))
    return 2.7


def sign_nowake(B):
    post_sign(B, 0.0, 0.0, 'sg_nowake', 0.6, 0.75, z_bottom=1.3, post='woodg')
    return 2.1


# ================================================================ the tiles (PIL; kit_buildings_atlas.EXTRA)
from PIL import Image, ImageDraw
_c = SG._c
SCRIPT = ['/usr/share/fonts/opentype/lobster/lobster.otf', '/usr/share/fonts/truetype/lobster/Lobster.ttf'] + SG.LATIN_SOFT
BOLD = SG.LATIN
NAVY, WHITE = (0.10, 0.24, 0.50), (0.97, 0.97, 0.96)


def _label(dr, w, h, s, paths, frac, ink, cx=0.5, cy=0.5, maxw=0.9, spacing=0):
    size = SG.fit(dr, s, paths, int(h * frac), w * maxw)
    SG.text(dr, (w * cx, h * cy), s, paths, size, ink, spacing=spacing)


def _waves(dr, x0, x1, y, amp, n, col, width):
    pts = [(x0 + (x1 - x0) * k / 60, y + amp * math.sin(k / 60 * n * 2 * math.pi)) for k in range(61)]
    dr.line(pts, fill=_c(col), width=width)


def t_glassblock(dr, w, h, k):
    """Four by four glass blocks, 0.2 m each: pale blue-green, a brighter ripple in each, mortar joints."""
    dr.rectangle([0, 0, w, h], fill=_c((0.84, 0.86, 0.84)))
    n = 4; c = w / n; j = c * 0.07
    for i in range(n):
        for jj in range(n):
            x0, y0 = i * c + j, jj * c + j
            x1, y1 = x0 + c - 2 * j, y0 + c - 2 * j
            dr.rectangle([x0, y0, x1, y1], fill=_c((0.62, 0.76, 0.80)))
            dr.rectangle([x0 + c * 0.1, y0 + c * 0.1, x1 - c * 0.1, y1 - c * 0.1], fill=_c((0.70, 0.83, 0.86)))
            for r in range(3):
                yy = y0 + c * (0.3 + 0.2 * r)
                _waves(dr, x0 + c * 0.15, x1 - c * 0.15, yy, c * 0.03, 2, (0.86, 0.93, 0.94), max(1, int(2 * k)))
            dr.line([(x0, y0), (x1, y0)], fill=_c((0.92, 0.95, 0.95)), width=max(1, int(2 * k)))


def t_breeze(dr, w, h, k):
    """Breeze blocks, 0.4 m each, two by two: a pierced four-petal pattern, the holes in deep shade."""
    dr.rectangle([0, 0, w, h], fill=_c((0.93, 0.93, 0.91)))
    n = 2; c = w / n
    for i in range(n):
        for jj in range(n):
            x0, y0 = i * c, jj * c
            cx, cy = x0 + c / 2, y0 + c / 2
            dr.rectangle([x0, y0, x0 + c, y0 + c], outline=_c((0.78, 0.78, 0.76)), width=max(1, int(3 * k)))
            for a in range(4):
                ang = a * math.pi / 2
                ex, ey = cx + math.cos(ang) * c * 0.22, cy + math.sin(ang) * c * 0.22
                dr.ellipse([ex - c * 0.16, ey - c * 0.16, ex + c * 0.16, ey + c * 0.16], fill=_c((0.20, 0.21, 0.24)))
            dr.ellipse([cx - c * 0.09, cy - c * 0.09, cx + c * 0.09, cy + c * 0.09], fill=_c((0.93, 0.93, 0.91)))


def t_chain(dr, w, h, k):
    """Chain link: diamond mesh of galvanised wire (the faces behind show between)."""
    dr.rectangle([0, 0, w, h], fill=_c((0.50, 0.54, 0.50)))
    n = 4; c = w / n
    for i in range(-1, n + 1):
        dr.line([(i * c, 0), (i * c + h, h)], fill=_c((0.80, 0.82, 0.83)), width=max(1, int(2 * k)))
        dr.line([(i * c + c, 0), (i * c + c - h, h)], fill=_c((0.70, 0.72, 0.74)), width=max(1, int(2 * k)))


def t_gate(dr, w, h, k):
    """An accordion security gate drawn shut: silver lattice over a dark, empty shop."""
    dr.rectangle([0, 0, w, h], fill=_c((0.16, 0.17, 0.19)))
    n = 4; c = w / n
    for i in range(n + 1):
        dr.line([(i * c, 0), (i * c, h)], fill=_c((0.78, 0.80, 0.82)), width=max(2, int(4 * k)))
    for i in range(-n, n + 1):
        dr.line([(i * c, 0), (i * c + c, h / 2), (i * c, h)], fill=_c((0.70, 0.72, 0.74)), width=max(1, int(3 * k)))
        dr.line([(i * c + c, 0), (i * c, h / 2), (i * c + c, h)], fill=_c((0.70, 0.72, 0.74)), width=max(1, int(3 * k)))


def t_screen(dr, w, h, k):
    """A porch screen: dark grey mesh with the dim room behind just showing."""
    dr.rectangle([0, 0, w, h], fill=_c((0.20, 0.21, 0.22)))
    dr.rectangle([0, h * 0.55, w, h], fill=_c((0.16, 0.16, 0.17)))
    for i in range(0, int(w), max(2, int(3 * k))):
        dr.line([(i, 0), (i, h)], fill=_c((0.27, 0.28, 0.29)), width=1)
    for j in range(0, int(h), max(2, int(3 * k))):
        dr.line([(0, j), (w, j)], fill=_c((0.27, 0.28, 0.29)), width=1)


def t_lattice(dr, w, h, k):
    """White diagonal lattice over the dark crawl space under a raised cottage."""
    dr.rectangle([0, 0, w, h], fill=_c((0.10, 0.10, 0.11)))
    n = 4; c = w / n
    for i in range(-n, 2 * n + 1):
        dr.line([(i * c, 0), (i * c + h, h)], fill=_c((0.93, 0.93, 0.91)), width=max(2, int(5 * k)))
        dr.line([(i * c, 0), (i * c - h, h)], fill=_c((0.90, 0.90, 0.88)), width=max(2, int(5 * k)))


def t_nowake(dr, w, h, k):
    red = (0.78, 0.16, 0.16)
    dr.rectangle([0, 0, w, h], fill=_c(WHITE))
    b = w * 0.05
    dr.rectangle([b, b, w - b, h - b], outline=_c((0.1, 0.1, 0.1)), width=max(1, int(3 * k)))
    cx, cy, r = w / 2, h * 0.5, w * 0.38
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=_c(red), width=int(w * 0.06))
    _label(dr, w, h, 'NO', BOLD, 0.2, (0.1, 0.1, 0.1), cy=0.42)
    _label(dr, w, h, 'WAKE', BOLD, 0.2, (0.1, 0.1, 0.1), cy=0.6, maxw=0.62)


def t_person(woman):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c(WHITE))
        ink = NAVY
        cx = w / 2
        dr.ellipse([cx - w * 0.12, h * 0.1, cx + w * 0.12, h * 0.28], fill=_c(ink))
        if woman:
            dr.polygon([(cx - w * 0.28, h * 0.66), (cx + w * 0.28, h * 0.66), (cx + w * 0.12, h * 0.32), (cx - w * 0.12, h * 0.32)], fill=_c(ink))
        else:
            dr.rectangle([cx - w * 0.17, h * 0.32, cx + w * 0.17, h * 0.62], fill=_c(ink))
        dr.rectangle([cx - w * 0.14, h * 0.6, cx - w * 0.03, h * 0.9], fill=_c(ink))
        dr.rectangle([cx + w * 0.03, h * 0.6, cx + w * 0.14, h * 0.9], fill=_c(ink))
    return f


def t_flag_us(dr, w, h, k):
    for i in range(13):
        dr.rectangle([0, h * i / 13, w, h * (i + 1) / 13], fill=_c((0.74, 0.14, 0.18) if i % 2 == 0 else WHITE))
    cw, ch = w * 0.4, h * 7 / 13
    dr.rectangle([0, 0, cw, ch], fill=_c((0.16, 0.20, 0.42)))
    for r in range(9):
        for c in range(6 if r % 2 == 0 else 5):
            x = cw * (c + (0.5 if r % 2 == 0 else 1.0)) / 6.0
            y = ch * (r + 0.5) / 9.0
            s = h * 0.012
            dr.ellipse([x - s, y - s, x + s, y + s], fill=_c(WHITE))


def t_flag_fl(dr, w, h, k):
    """Florida's flag: white with a red saltire and the seal at the crossing (simplified)."""
    dr.rectangle([0, 0, w, h], fill=_c(WHITE))
    t = h * 0.14
    dr.line([(0, 0), (w, h)], fill=_c((0.76, 0.14, 0.17)), width=int(t))
    dr.line([(0, h), (w, 0)], fill=_c((0.76, 0.14, 0.17)), width=int(t))
    r = h * 0.2
    dr.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=_c((0.38, 0.62, 0.80)), outline=_c((0.92, 0.80, 0.36)), width=max(1, int(3 * k)))
    dr.rectangle([w / 2 - r * 0.6, h / 2 + r * 0.2, w / 2 + r * 0.6, h / 2 + r * 0.6], fill=_c((0.86, 0.74, 0.46)))
    dr.line([(w / 2 + r * 0.1, h / 2 + r * 0.3), (w / 2 + r * 0.1, h / 2 - r * 0.6)], fill=_c((0.42, 0.28, 0.18)), width=max(1, int(3 * k)))


def t_access(number):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c(WHITE))
        b = w * 0.035
        dr.rectangle([b, b, w - b, h - b], outline=_c(NAVY), width=int(b))
        _label(dr, w, h, 'Beach', BOLD, 0.17, NAVY, cy=0.2)
        _label(dr, w, h, 'Access', BOLD, 0.17, NAVY, cy=0.4)
        if number:
            _label(dr, w, h, number, BOLD, 0.24, NAVY, cy=0.64)
        else:
            cx, y0, y1 = w / 2, h * 0.52, h * 0.74
            dr.line([(cx, y1), (cx, y0)], fill=_c(NAVY), width=int(w * 0.05))
            dr.polygon([(cx - w * 0.1, y0 + h * 0.05), (cx + w * 0.1, y0 + h * 0.05), (cx, y0 - h * 0.04)], fill=_c(NAVY))
        dr.rectangle([b * 2, h * 0.82, w - b * 2, h * 0.92], fill=_c((0.20, 0.52, 0.78)))
        for i in range(3):
            _waves(dr, b * 2, w - b * 2, h * (0.84 + 0.03 * i), h * 0.008, 4, WHITE, max(1, int(2 * k)))
    return f


def t_turtle(dr, w, h, k):
    green = (0.10, 0.40, 0.26)
    dr.rectangle([0, 0, w, h], fill=_c(WHITE))
    b = w * 0.03
    dr.rectangle([b, b, w - b, h - b], outline=_c(green), width=int(b))
    _label(dr, w, h, 'Sea Turtle', BOLD, 0.11, green, cy=0.13)
    _label(dr, w, h, 'Nesting Area', BOLD, 0.11, green, cy=0.27)
    cx, cy, r = w / 2, h * 0.53, w * 0.16
    dr.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=_c(green))
    dr.ellipse([cx - r * 0.3, cy - r * 1.3, cx + r * 0.3, cy - r * 0.7], fill=_c(green))
    for sx in (-1, 1):
        for sy in (-1, 1):
            fx, fy = cx + sx * r * 0.95, cy + sy * r * 0.55
            dr.ellipse([fx - r * 0.3, fy - r * 0.18, fx + r * 0.3, fy + r * 0.18], fill=_c(green))
    _label(dr, w, h, 'Please keep off the dunes', SG.LATIN_SOFT, 0.065, green, cy=0.8)
    _label(dr, w, h, 'and nesting sites', SG.LATIN_SOFT, 0.065, green, cy=0.89)


def t_hurricane(dr, w, h, k):
    blue = (0.10, 0.26, 0.62)
    dr.rectangle([0, 0, w, h], fill=_c(blue))
    b = w * 0.03
    dr.rectangle([b, b, w - b, h - b], outline=_c(WHITE), width=max(1, int(b * 0.6)))
    _label(dr, w, h, 'Hurricane', BOLD, 0.2, WHITE, cy=0.24)
    _label(dr, w, h, 'Evacuation', BOLD, 0.2, WHITE, cy=0.46)
    _label(dr, w, h, 'Route', BOLD, 0.2, WHITE, cy=0.66)
    cy, x0, x1 = h * 0.85, w * 0.32, w * 0.66
    dr.line([(x0, cy), (x1, cy)], fill=_c(WHITE), width=int(h * 0.06))
    dr.polygon([(x1 - h * 0.02, cy - h * 0.09), (x1 - h * 0.02, cy + h * 0.09), (x1 + h * 0.1, cy)], fill=_c(WHITE))


def t_diner(dr, w, h, k):
    """The diner's boomerang sign: script lettering on red, a cream border."""
    dr.rectangle([0, 0, w, h], fill=_c((0.38, 0.72, 0.72)))
    dr.rounded_rectangle([w * 0.03, h * 0.08, w * 0.97, h * 0.92], radius=h * 0.25, fill=_c((0.95, 0.90, 0.78)))
    dr.rounded_rectangle([w * 0.06, h * 0.15, w * 0.94, h * 0.85], radius=h * 0.2, fill=_c((0.76, 0.16, 0.18)))
    _label(dr, w, h, 'Coral Comet', SCRIPT, 0.32, (0.98, 0.93, 0.80), cy=0.36, maxw=0.82)
    _label(dr, w, h, 'Diner', SCRIPT, 0.32, (0.98, 0.93, 0.80), cy=0.66, maxw=0.82)


def t_motel(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.20, 0.62, 0.64)))
    dr.rounded_rectangle([w * 0.04, h * 0.06, w * 0.96, h * 0.94], radius=h * 0.12, fill=_c((0.26, 0.70, 0.70)),
                         outline=_c(WHITE), width=max(1, int(4 * k)))
    _label(dr, w, h, 'Seabreeze', SCRIPT, 0.36, WHITE, cy=0.34, maxw=0.86)
    _label(dr, w, h, 'Motel', SCRIPT, 0.36, WHITE, cy=0.68, maxw=0.86)


def t_vacancy(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.12, 0.10, 0.11)))
    _label(dr, w, h, 'VACANCY', BOLD, 0.62, (1.0, 0.36, 0.32), maxw=0.86, spacing=int(h * 0.04))


def t_name(s, ink, bg, paths=None, frac=0.6, stripe=None):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c(bg))
        _label(dr, w, h, s, paths or SCRIPT, frac, ink, maxw=0.9)
        if stripe: dr.rectangle([0, int(h * 0.9), w, h], fill=_c(stripe))
    return f


def t_school(dr, w, h, k):
    """The school's marquee: the name over a palm and a wave, on teal; the message board below is geometry."""
    teal = (0.10, 0.50, 0.54)
    dr.rectangle([0, 0, w, h], fill=_c(teal))
    b = h * 0.05
    dr.rectangle([b, b, w - b, h - b], outline=_c(WHITE), width=max(1, int(b * 0.5)))
    _label(dr, w, h, 'SEAGROVE', BOLD, 0.3, WHITE, cx=0.42, cy=0.33, maxw=0.62, spacing=int(h * 0.02))
    _label(dr, w, h, 'HIGH SCHOOL', BOLD, 0.24, WHITE, cx=0.42, cy=0.68, maxw=0.62, spacing=int(h * 0.02))
    cx, cy, r = w * 0.85, h * 0.5, h * 0.32
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_c(WHITE))
    dr.chord([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=_c((0.20, 0.52, 0.78)))
    dr.line([(cx - r * 0.1, cy + r * 0.3), (cx + r * 0.05, cy - r * 0.55)], fill=_c((0.40, 0.30, 0.20)), width=max(2, int(4 * k)))
    for a in (-2.4, -1.9, -1.2, -0.6, -0.1):
        dr.line([(cx + r * 0.05, cy - r * 0.55), (cx + r * 0.05 + math.cos(a) * r * 0.55, cy - r * 0.55 + math.sin(a) * -r * 0.3 + r * 0.15)],
                fill=_c((0.16, 0.50, 0.30)), width=max(2, int(5 * k)))


def t_schoolzone(dr, w, h, k):
    """A school-zone sign: fluorescent yellow-green pentagon, two children walking."""
    dr.rectangle([0, 0, w, h], fill=_c((0.86, 0.94, 0.20)))
    ink = (0.08, 0.08, 0.08)
    dr.polygon([(w / 2, h * 0.04), (w * 0.96, h * 0.42), (w * 0.96, h * 0.96), (w * 0.04, h * 0.96), (w * 0.04, h * 0.42)],
               outline=_c(ink), width=max(2, int(4 * k)))
    for cx, s in ((w * 0.38, 1.0), (w * 0.62, 0.92)):
        hy = h * 0.32
        dr.ellipse([cx - w * 0.05 * s, hy, cx + w * 0.05 * s, hy + w * 0.1 * s], fill=_c(ink))
        dr.polygon([(cx - w * 0.07 * s, h * 0.46), (cx + w * 0.07 * s, h * 0.46), (cx + w * 0.05 * s, h * 0.68), (cx - w * 0.05 * s, h * 0.68)], fill=_c(ink))
        dr.line([(cx - w * 0.03, h * 0.68), (cx - w * 0.08, h * 0.88)], fill=_c(ink), width=max(2, int(6 * k)))
        dr.line([(cx + w * 0.03, h * 0.68), (cx + w * 0.07, h * 0.88)], fill=_c(ink), width=max(2, int(6 * k)))


def t_arrow(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.86, 0.94, 0.20)))
    ink = (0.08, 0.08, 0.08)
    dr.line([(w * 0.25, h * 0.25), (w * 0.62, h * 0.72)], fill=_c(ink), width=int(h * 0.12))
    dr.polygon([(w * 0.72, h * 0.84), (w * 0.44, h * 0.78), (w * 0.70, h * 0.5)], fill=_c(ink))


def t_menu(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.16, 0.18, 0.17)))
    _label(dr, w, h, 'MENU', BOLD, 0.11, (0.96, 0.88, 0.5), cy=0.1)
    for i, item in enumerate(('Hot dogs', 'Fries', 'Lemonade', 'Ice cream', 'Smoothies')):
        _label(dr, w, h, item, SG.LATIN_SOFT, 0.075, WHITE, cx=0.4, cy=0.26 + 0.14 * i, maxw=0.6)
        _label(dr, w, h, '$%d' % (3 + i), SG.LATIN_SOFT, 0.075, WHITE, cx=0.84, cy=0.26 + 0.14 * i, maxw=0.2)


def t_bus(dr, w, h, k):
    blue = (0.10, 0.30, 0.60)
    dr.rectangle([0, 0, w, h], fill=_c(WHITE))
    dr.rectangle([w * 0.06, h * 0.06, w * 0.94, h * 0.94], fill=_c(blue))
    _label(dr, w, h, 'BUS', BOLD, 0.3, WHITE, cy=0.3)
    _label(dr, w, h, 'STOP', BOLD, 0.3, WHITE, cy=0.68)


def paint(img, put):
    """The Florida kit's own tiles (kit_buildings_atlas.paint calls this through EXTRA)."""
    pp = SG.put_pil
    pp(img, 'fl_glassblock', t_glassblock, (0.84, 0.86, 0.84))
    pp(img, 'fl_breeze', t_breeze, (0.93, 0.93, 0.91))
    pp(img, 'fl_chain', t_chain, (0.5, 0.54, 0.5))
    pp(img, 'fl_gate', t_gate, (0.16, 0.17, 0.19))
    pp(img, 'fl_screen', t_screen, (0.2, 0.21, 0.22))
    pp(img, 'fl_lattice', t_lattice, (0.1, 0.1, 0.11))
    pp(img, 'sg_nowake', t_nowake, WHITE)
    pp(img, 'fl_men', t_person(False), WHITE)
    pp(img, 'fl_women', t_person(True), WHITE)
    pp(img, 'fl_flagus', t_flag_us, WHITE)
    pp(img, 'fl_flagfl', t_flag_fl, WHITE)
    pp(img, 'sg_access23', t_access('23'), WHITE)
    pp(img, 'sg_access', t_access(None), WHITE)
    pp(img, 'sg_turtle', t_turtle, WHITE)
    pp(img, 'sg_hurricane', t_hurricane, (0.10, 0.26, 0.62))
    pp(img, 'sg_diner', t_diner, (0.38, 0.72, 0.72))
    pp(img, 'sg_motel', t_motel, (0.20, 0.62, 0.64))
    pp(img, 'sg_vacancy', t_vacancy, (0.12, 0.10, 0.11))
    pp(img, 'sg_rentals', t_name('Coastal Rentals', (0.10, 0.24, 0.50), (0.99, 0.90, 0.58), frac=0.66), (0.99, 0.90, 0.58))
    pp(img, 'sg_surfshop', t_name('Surf Shop', (0.10, 0.34, 0.50), (0.56, 0.82, 0.82), frac=0.7), (0.56, 0.82, 0.82))
    pp(img, 'sg_havana', t_name('Havana Café', (0.74, 0.14, 0.18), (0.98, 0.78, 0.80), frac=0.7), (0.98, 0.78, 0.80))
    pp(img, 'sg_bait', t_name('Bait & Tackle', (0.10, 0.24, 0.50), (0.98, 0.89, 0.58), paths=BOLD, frac=0.56), (0.98, 0.89, 0.58))
    pp(img, 'sg_icecream', t_name('Ocean Ice Cream', (0.14, 0.26, 0.58), (0.82, 0.76, 0.94), frac=0.66), (0.82, 0.76, 0.94))
    pp(img, 'sg_school', t_school, (0.10, 0.50, 0.54))
    pp(img, 'sg_schoolwall', t_name('SEAGROVE HIGH SCHOOL', (0.10, 0.44, 0.48), (0.92, 0.88, 0.77), paths=BOLD, frac=0.55), (0.92, 0.88, 0.77))
    pp(img, 'sg_schoolzone', t_schoolzone, (0.86, 0.94, 0.20))
    pp(img, 'sg_arrow', t_arrow, (0.86, 0.94, 0.20))
    pp(img, 'sg_menu', t_menu, (0.16, 0.18, 0.17))
    pp(img, 'sg_bus', t_bus, WHITE)


# ================================================================ the kit's rows
def pal_fl(pal):
    """The Florida rows of the kit's SPECS (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps).
    Most things keep their own colours (the street places them as they are); parts 1 to 3 can still be repainted."""
    st = {'wall': 'stucco'}
    prop = {'ppm': 12}
    deco = {'wall': 'stucco', 'ppm': 72}
    return [
        ('RestroomFL', 6.4, 2.9, 4.2, 0.9, restroom,
         pal((0.93, 0.93, 0.91), (0.19, 0.39, 0.64), (0.22, 0.44, 0.68), trim=(0.95, 0.95, 0.94), conc=(0.80, 0.79, 0.76)), 4.6,
         {'wall': 'render', 'ppm': 80}, {}),
        ('ShackFL', 4.2, 2.6, 3.6, 0.8, shack,
         pal((0.60, 0.72, 0.80), (0.58, 0.72, 0.80), (0.56, 0.56, 0.57), trim=(0.94, 0.94, 0.93)), 4.0, {'wall': 'siding', 'ppm': 80}, {}),
        ('LifeguardFL', 2.8, 2.3, 2.4, 0.0, lifeguard,
         pal((0.98, 0.80, 0.22), (0.94, 0.42, 0.17), (0.92, 0.38, 0.16)), 6.6, {'ppm': 64}, {}),
        ('CrossoverFL', 1.8, 1.5, 9.0, 0.0, crossover,
         pal((0.62, 0.58, 0.52), (0.62, 0.58, 0.52), (0.56, 0.55, 0.54)), 3.0, prop, {}),
        ('DinerFL', 13.0, 3.3, 7.0, 0.0, diner,
         pal((0.93, 0.89, 0.80), (0.76, 0.17, 0.18), (0.80, 0.82, 0.84), trim=(0.95, 0.94, 0.92), conc=(0.82, 0.80, 0.76)), 5.0,
         {'wall': 'stucco', 'ppm': 72}, {}),
        ('DinerSignFL', 1.2, 7.0, 0.8, 0.0, diner_sign,
         pal((0.40, 0.76, 0.76), (0.76, 0.17, 0.18), (0.56, 0.55, 0.54)), 9.0, prop, {}),
        ('MotelFL', 18.0, 6.2, 9.0, 0.0, motel,
         pal((0.95, 0.95, 0.93), (0.30, 0.66, 0.68), (0.56, 0.55, 0.54), trim=(0.96, 0.96, 0.95), frame=(0.96, 0.96, 0.95)), 7.0,
         {'wall': 'stucco', 'ppm': 64}, {}),
        ('MotelSignFL', 1.0, 6.2, 0.8, 0.0, motel_sign,
         pal((0.95, 0.95, 0.93), (0.30, 0.66, 0.68), (0.56, 0.55, 0.54)), 7.4, prop, {}),
        ('MotelPoolFL', 9.0, 0.1, 4.0, 0.0, motel_pool,
         pal((0.95, 0.95, 0.93), (0.30, 0.66, 0.68), (0.56, 0.55, 0.54), trim=(0.92, 0.92, 0.90), conc=(0.86, 0.85, 0.82)), 2.6, prop, {}),
        ('DecoSurfFL', 7.6, 3.95, 9.0, 0.0, deco_surf,
         pal((0.52, 0.80, 0.80), (0.18, 0.38, 0.70), (0.56, 0.55, 0.54), trim=(0.96, 0.95, 0.92)), 5.6, deco, {}),
        ('DecoCafeFL', 6.4, 5.8, 9.0, 0.0, deco_cafe,
         pal((0.97, 0.76, 0.80), (0.78, 0.18, 0.19), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 8.0, deco, {}),
        ('DecoBaitFL', 6.4, 3.8, 9.0, 0.0, deco_bait,
         pal((0.98, 0.88, 0.56), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 5.4, deco, {}),
        ('DecoIceFL', 7.4, 3.95, 9.0, 0.0, deco_ice,
         pal((0.80, 0.74, 0.92), (0.96, 0.66, 0.74), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 6.0, deco, {}),
        ('DecoShutFL', 7.0, 3.7, 9.0, 0.0, deco_shut,
         pal((0.95, 0.95, 0.93), (0.30, 0.66, 0.68), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 5.4, deco, {}),
        ('RentalsFL', 9.0, 3.6, 8.0, 0.0, rentals,
         pal((0.98, 0.88, 0.56), (0.18, 0.38, 0.72), (0.56, 0.55, 0.54), trim=(0.96, 0.95, 0.92)), 5.0, {'wall': 'stucco', 'ppm': 80}, {}),
        ('BusShelterFL', 3.4, 2.5, 1.5, 0.0, bus_shelter, pal((0.95, 0.95, 0.93), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54)), 3.2, prop, {}),
        ('SchoolZoneFL', 0.8, 3.6, 0.4, 0.0, school_zone, pal((0.95, 0.95, 0.93), (0.30, 0.66, 0.68), (0.56, 0.55, 0.54)), 4.2, prop, {}),
        ('MailboxFL', 0.7, 1.3, 0.6, 0.0, mailbox_fl, pal((0.95, 0.95, 0.93), (0.18, 0.37, 0.62), (0.56, 0.55, 0.54)), 1.4, prop, {}),
        ('HydrantFL', 0.5, 0.8, 0.5, 0.0, hydrant_fl, pal((0.95, 0.95, 0.93), (0.98, 0.80, 0.20), (0.56, 0.55, 0.54)), 1.0, prop, {}),
        ('TrashFL', 0.7, 1.1, 0.7, 0.0, trash_fl, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        ('BenchFL', 1.8, 1.0, 0.6, 0.0, bench_fl, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        ('LampFL', 0.4, 4.6, 1.0, 0.0, lamp_fl, pal((0.95, 0.95, 0.93), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54)), 5.2, prop, {}),
        ('SignAccessFL', 0.8, 1.6, 0.2, 0.0, sign_access, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 1.8, prop, {}),
        ('SignAccessUpFL', 0.8, 2.2, 0.2, 0.0, sign_access_up, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 2.4, prop, {}),
        ('SignTurtleFL', 0.8, 1.5, 0.2, 0.0, sign_turtle, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 1.8, prop, {}),
        ('SignHurricaneFL', 0.9, 2.6, 0.2, 0.0, sign_hurricane, pal((0.95, 0.95, 0.93), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 2.8, prop, {}),
        ('PostRopeFL', 4.0, 0.8, 0.2, 0.0, post_rope, pal((0.62, 0.58, 0.52), (0.62, 0.58, 0.52), (0.56, 0.55, 0.54)), 1.0, prop, {}),
        ('PoleSignalFL', 0.4, 9.5, 0.4, 0.0, pole_signal, pal((0.80, 0.79, 0.76), (0.74, 0.76, 0.77), (0.56, 0.55, 0.54)), 10.0, prop, {}),
        ('FenceChainFL', 4.0, 2.2, 0.1, 0.0, fence_chain, pal((0.74, 0.76, 0.77), (0.74, 0.76, 0.77), (0.56, 0.55, 0.54)), 2.4, prop, {}),
        ('SoccerGoalFL', 3.0, 1.8, 1.2, 0.0, soccer_goal, pal((0.95, 0.95, 0.93), (0.95, 0.95, 0.93), (0.56, 0.55, 0.54)), 2.0, prop, {}),
        ('KayakRackFL', 3.0, 1.3, 1.6, 0.0, kayak_rack, pal((0.62, 0.58, 0.52), (0.62, 0.58, 0.52), (0.56, 0.55, 0.54)), 3.0, prop, {}),
        ('VolleyNetFL', 8.0, 2.4, 0.2, 0.0, volley_net, pal((0.95, 0.95, 0.93), (0.95, 0.95, 0.93), (0.56, 0.55, 0.54)), 2.6, prop, {}),
        # Home Street (chapter 1)
        ('RanchFL', 12.0, 2.9, 9.0, 1.4, ranch,
         pal((0.70, 0.86, 0.82), (0.80, 0.22, 0.17), (0.88, 0.87, 0.84), trim=(0.96, 0.96, 0.95), frame=(0.95, 0.95, 0.94), conc=(0.82, 0.8, 0.77)), 4.8,
         {'wall': 'stucco', 'ppm': 64}, {}),
        ('RanchSmallFL', 8.5, 2.8, 7.5, 1.3, ranch_small,
         pal((0.96, 0.74, 0.70), (0.42, 0.60, 0.66), (0.88, 0.87, 0.84), trim=(0.96, 0.96, 0.95), frame=(0.95, 0.95, 0.94)), 4.6,
         {'wall': 'stucco', 'ppm': 64}, {}),
        ('CottageFL', 8.0, 3.6, 8.0, 2.0, cottage,
         pal((0.95, 0.76, 0.80), (0.70, 0.82, 0.84), (0.74, 0.76, 0.78), trim=(0.97, 0.97, 0.96)), 6.2, {'wall': 'siding', 'ppm': 64}, {}),
        ('ChurchFL', 8.0, 6.0, 12.0, 2.0, church_fl,
         pal((0.97, 0.96, 0.93), (0.66, 0.24, 0.18), (0.74, 0.36, 0.26), trim=(0.93, 0.91, 0.86)), 11.0, {'wall': 'stucco', 'ppm': 48}, {}),
        ('MailboxPostFL', 0.4, 1.4, 0.6, 0.0, mailbox_post, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.6, prop, {}),
        ('GolfCartFL', 2.3, 1.0, 1.2, 0.0, golf_cart, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.6, prop, {}),
        ('SprinklerFL', 0.5, 0.3, 0.5, 0.0, sprinkler, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        ('DrawLeafFL', 2.5, 0.3, 3.5, 0.0, draw_leaf, pal((0.6, 0.62, 0.64), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.4, prop, {}),
        ('DrawTowerFL', 2.4, 4.4, 2.4, 0.0, draw_tower,
         pal((0.95, 0.95, 0.93), (0.20, 0.55, 0.58), (0.30, 0.62, 0.64)), 5.8, {'wall': 'stucco', 'ppm': 32}, {}),
        ('GatePostFL', 0.4, 0.9, 0.4, 0.0, gate_post, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.0, prop, {}),
        ('GateArmFL', 0.2, 4.2, 0.2, 0.0, gate_arm, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 4.4, prop, {}),
        ('CanalRailFL', 5.0, 1.2, 0.4, 0.0, canal_rail, pal((0.86, 0.84, 0.80), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.4, prop, {}),
        ('DockFL', 3.0, 2.6, 7.0, 0.0, dock, pal((0.62, 0.58, 0.52), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 3.0, prop, {}),
        ('SignNoWakeFL', 0.6, 2.1, 0.2, 0.0, sign_nowake, pal((0.95, 0.95, 0.93), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 2.2, prop, {}),
        ('SchoolFL', 30.0, 7.2, 12.0, 0.0, school_fl,
         pal((0.92, 0.88, 0.77), (0.16, 0.58, 0.60), (0.56, 0.55, 0.54), trim=(0.96, 0.95, 0.92), frame=(0.82, 0.83, 0.84)), 9.4,
         {'wall': 'render', 'ppm': 48}, {}),
        ('WalkwayFL', 3.2, 2.9, 12.0, 0.0, walkway, pal((0.95, 0.95, 0.93), (0.16, 0.58, 0.60), (0.56, 0.55, 0.54)), 3.4, prop, {}),
        ('PortableFL', 9.0, 2.8, 3.6, 0.0, portable,
         pal((0.86, 0.82, 0.70), (0.16, 0.58, 0.60), (0.56, 0.55, 0.54), trim=(0.94, 0.93, 0.90)), 4.0, {'wall': 'siding', 'ppm': 32}, {}),
        ('MarqueeFL', 2.6, 2.1, 0.6, 0.0, marquee, pal((0.95, 0.95, 0.93), (0.16, 0.58, 0.60), (0.56, 0.55, 0.54)), 2.4, prop, {}),
        ('FlagpoleFL', 0.8, 9.0, 0.8, 0.0, flagpole_fl, pal((0.95, 0.95, 0.93), (0.95, 0.95, 0.93), (0.56, 0.55, 0.54)), 9.4, prop, {}),
        ('FenceAluFL', 2.4, 1.8, 0.1, 0.0, fence_alu, pal((0.95, 0.95, 0.93), (0.95, 0.95, 0.93), (0.56, 0.55, 0.54)), 2.0, prop, {}),
        ('SchoolGateFL', 5.0, 2.2, 0.6, 0.0, school_gate,
         pal((0.92, 0.88, 0.77), (0.16, 0.58, 0.60), (0.56, 0.55, 0.54), trim=(0.96, 0.95, 0.92)), 2.8, prop, {}),
    ]
