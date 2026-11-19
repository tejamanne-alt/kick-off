# The Miami kit (kit_buildings.py --kit Miami): Florida's own routes (docs/CITIES.md, FL1 to FL3), on its own 4096 x 4096
# atlas, so every leg of the city is dressed in Miami's own buildings and things rather than another town's.
#
#   Little Havana (FL1-1, FL2-1's corner): a walk-up café with its ventanita, a two-storey cigar shop with an iron balcony,
#     a fruit shop with its crates, mural walls, the domino park's pergola, its tables, a fruit cart, roosters and hens.
#   Brickell and downtown (FL1-2, FL2-3, FL3-2): glass condo and office towers, a tower podium with its valet canopy, the
#     construction site's printed mesh fence, a coffee kiosk, rental scooters; Art Deco blocks with deep arcades and canvas
#     canopies, a Mediterranean Revival building with its loggia, a Spanish-style tower with a cupola (invented).
#   The river and the bay (FL1-3, FL2-1, FL2-2): a small river freighter, a tug, a fishing boat, the riverwalk's
#     rail and bollards, a coiled line, pelicans on their pilings, a cruise ship far off.
#   The Underline and Museum Park (FL3-1, FL3-3): the elevated railway's guideway on round piers painted with murals, outdoor
#     fitness bars, a museum under a canopy of hanging gardens (invented).
#   The trip itself: the city bus (seen on the map), a stop's route sign, the corner drugstore's front.
#
# Same contract as the rest of the buildings kit (kit_buildings.py): metres, Z up, the origin at the centre of the front's
# base, the street face looking along -Y, parts 1 wall / 2 accent / 3 roof. Every name on a sign is invented; no landmark,
# brand or logo is copied. The kit's own tiles (signs, murals, the mesh banner) are
# painted here (paint(), through kit_buildings_atlas.EXTRA), with the Florida kit's patterns where they are shared.
import math
import numpy as np
from mathutils import Vector
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import decal, flat_ac
from kit_buildings_cal import hip, column, iron_rail, arch_head, surround, glass_panel, condenser
import kit_buildings_fl as FL
from kit_buildings_fl import (eyebrow, stripes, glass_block, breeze_screen, post_sign, cafe_set, tile_cells, pipe_rail, flat_slab,
                              _label, _c, WHITE, SCRIPT, BOLD)
import kit_buildings_signs as SG

# ---------------------------------------------------------------- the kit's own colours (Florida's are already in MAT)
MIA_MAT = {
    'butter': (0, (0.98, 0.86, 0.52), 'white', 0.1), 'coral': (0, (0.95, 0.52, 0.42), 'white', 0.1),
    'flamingo': (0, (0.96, 0.62, 0.70), 'white', 0.1), 'mint': (0, (0.62, 0.86, 0.76), 'white', 0.1),
    'cuban': (0, (0.12, 0.30, 0.62), 'white', 0.1), 'havred': (0, (0.80, 0.16, 0.18), 'white', 0.1),
    'glassb': (0, (0.42, 0.62, 0.74), 'white', 0.0), 'glassg': (0, (0.50, 0.70, 0.72), 'white', 0.0),
    'glassd': (0, (0.22, 0.32, 0.40), 'white', 0.0), 'slab': (0, (0.92, 0.92, 0.90), 'white', 0.05),
    'rust': (0, (0.56, 0.30, 0.20), 'white', 0.2), 'hullb': (0, (0.14, 0.26, 0.46), 'white', 0.15),
    'hullr': (0, (0.62, 0.18, 0.16), 'white', 0.2), 'deckg': (0, (0.46, 0.50, 0.46), 'white', 0.1),
    'tire': (0, (0.12, 0.12, 0.13), 'white', 0.0), 'fender': (0, (0.20, 0.30, 0.52), 'white', 0.0),
    'scoot': (0, (0.16, 0.66, 0.60), 'white', 0.0), 'scootd': (0, (0.13, 0.14, 0.15), 'white', 0.0),
    'feather': (0, (0.62, 0.20, 0.12), 'white', 0.2), 'featherh': (0, (0.74, 0.48, 0.26), 'white', 0.2),
    'tailg': (0, (0.06, 0.22, 0.18), 'white', 0.1), 'comb': (0, (0.86, 0.12, 0.10), 'white', 0.0),
    'beak': (0, (0.98, 0.74, 0.22), 'white', 0.0), 'iguana': (0, (0.40, 0.62, 0.26), 'white', 0.25),
    'pelican': (0, (0.52, 0.46, 0.40), 'white', 0.2), 'pelicanw': (0, (0.92, 0.90, 0.84), 'white', 0.1),
    'mango': (0, (0.98, 0.62, 0.18), 'white', 0.1), 'mangog': (0, (0.54, 0.70, 0.24), 'white', 0.1),
    'domino': (0, (0.97, 0.96, 0.92), 'white', 0.0), 'felt': (0, (0.16, 0.42, 0.30), 'white', 0.0),
    'seat': (0, (0.18, 0.40, 0.72), 'white', 0.05), 'grab': (0, (0.98, 0.78, 0.18), 'white', 0.0),
    'floorb': (0, (0.36, 0.37, 0.40), 'white', 0.0), 'busw': (0, (0.95, 0.95, 0.93), 'white', 0.05),
    'led': (0, (0.98, 0.62, 0.12), 'white', 0.0),
    'terrazzo': (0, (0.90, 0.88, 0.84), 'white', 0.0), 'planterg': (0, (0.30, 0.52, 0.30), 'white', 0.35),
    'umbrella': (0, (0.96, 0.84, 0.32), 'white', 0.1), 'cream2': (0, (0.97, 0.93, 0.84), 'white', 0.05),
}
for _k, _v in MIA_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1

# ---------------------------------------------------------------- the kit's tiles
TILES = [
    # shared with the Florida kit (painted by its painters)
    ('fl_glassblock', 256, 256), ('fl_breeze', 256, 256), ('fl_chain', 128, 128), ('fl_gate', 128, 128), ('sg_bus', 160, 160),
    # Miami's own
    ('mi_ventanita', 768, 150), ('mi_cafemenu', 256, 320), ('mi_tabacos', 640, 140), ('mi_fruteria', 768, 140),
    ('mi_mural1', 1024, 640), ('mi_mural2', 512, 1024), ('mi_mural3', 640, 640), ('mi_mesh', 1024, 256),
    ('mi_kiosk', 384, 96), ('mi_pharmacy', 768, 150),
    ('mi_led', 512, 64), ('mi_route', 192, 256), ('mi_deco1', 640, 120), ('mi_deco2', 640, 120), ('mi_hotel', 256, 640),
    ('mi_museum', 768, 96), ('mi_containers', 512, 256), ('mi_tower', 256, 256), ('mi_towerb', 256, 256),
    ('mi_domino', 128, 128), ('mi_scoot', 128, 64), ('mi_shutter', 256, 256),
]


# ================================================================ shared pieces
def jalousie(B, wf, u0, u1, v0, v1, frame='trimw', slats=8):
    """A jalousie window: a frame of narrow horizontal glass louvres, half open (Miami's 1950s window)."""
    window(B, wf, u0, u1, v0, v1, depth=0.12, fw=0.05, cols=1, frame=frame, glass='glass2', sill='trim', head=None, cheap=True,
           seed=int(u0 * 13 + v0 * 7) % 97)
    for k in range(slats):
        v = v0 + 0.08 + (v1 - v0 - 0.16) * (k + 0.5) / slats
        put(B, wf, fbox((u0 + 0.06, v - 0.012, -0.05), (u1 - 0.06, v + 0.012, 0.035), 0.004, 'alu'))


def grille(B, wf, u0, u1, v0, v1, out=0.05, n=None, mat='black'):
    """An iron window grille with a sunburst top bar (Little Havana's houses and shops)."""
    n = n or max(3, int((u1 - u0) / 0.16))
    put(B, wf, tube([(u0, v1, out), (u1, v1, out)], 0.018, mat, 4))
    put(B, wf, tube([(u0, v0, out), (u1, v0, out)], 0.018, mat, 4))
    for x in np.linspace(u0, u1, n):
        put(B, wf, tube([(x, v0, out), (x, v1, out)], 0.011, mat, 4))
    cx = (u0 + u1) / 2
    for a in np.linspace(0.25, math.pi - 0.25, 5):
        put(B, wf, tube([(cx, v1 - 0.02, out), (cx + math.cos(a) * (u1 - u0) * 0.35, v1 - 0.02 - math.sin(a) * 0.22, out)], 0.009, mat, 3))


def stool(B, x, y, mat='flred', h=0.62):
    """A round stool on a chrome stem with a foot ring (the café's counter, the domino tables)."""
    t, _ = lathe([(0.0, h), (0.17, h), (0.17, h + 0.06), (0.0, h + 0.07)], 10, mat)
    xform(t, T(x, y, 0)); B.add(t)
    B.add(tube([(x, y, 0.0), (x, y, h)], 0.025, 'chrome', 5))
    B.add(tube([(x + 0.14 * math.cos(a), y + 0.14 * math.sin(a), 0.22) for a in np.linspace(0, 2 * math.pi, 9)], 0.012, 'chrome', 3, caps=False))
    B.add(cbox2((x - 0.16, y - 0.16, 0.0), (x + 0.16, y + 0.16, 0.03), 0.01, 'chrome'))


def shop_front_glass(B, wf, u0, u1, v0, v1, seed=0, cols=3):
    window(B, wf, u0, u1, v0, v1, depth=0.18, fw=0.07, cols=cols, frame='alu', glass='glass3', sill='conc', head=None, seed=seed)


def plain_walls(B, H, top=None, fronts=(), rights=(), lefts=(), backs=(), v0=0.0):
    W, D = B.W, B.D
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, top if top is not None else H, list(fronts), v0)
    wall(B, Rt, 0, D, H, list(rights), v0)
    wall(B, Lf, -D, 0, H, list(lefts), v0)
    wall(B, Bk, -W / 2, W / 2, H, list(backs), v0)
    return F, Rt, Bk, Lf


def palm_pot(B, x, y, scale=1.0):
    pot(B, (x, y, 0.0), 0.32 * scale, 0.5 * scale, 'concw', 'bush', seed=int(x * 31 + y * 17) % 997, scale=1.4 * scale)


# ================================================================ Little Havana
def ventanita(B):
    """A walk-up Cuban café on a Little Havana corner: one storey of butter-yellow stucco, a red-and-white striped awning, the
    ventanita (the walk-up window) with its steel counter ledge, the menu board beside it, a glass door, the café's name
    over the awning, a terrazzo step, and iron grilles on the side window."""
    W, H, D = B.W, B.H, B.D
    pp = 0.8
    vent = (-W / 2 + 0.9, -W / 2 + 3.1, 0.95, 2.25)
    sf = (-W / 2 + 3.6, W / 2 - 1.9, 0.0, 2.7)
    dr = (W / 2 - 1.6, W / 2 - 0.6, 0.0, 2.4)
    side = (2.0, 4.0, 1.0, 2.3)
    top = [(-W / 2, H + pp), (W / 2, H + pp)]
    F, Rt, Bk, Lf = plain_walls(B, H + pp, top, fronts=[vent, sf, dr], lefts=[(-side[1], -side[0], side[2], side[3])])
    flat_top(B, H, pp)
    # the ventanita: a sliding glass window over a stainless counter, the café inside
    shop_room(B, vent[0], vent[1], vent[2], vent[3], 1.2)
    window(B, F, *vent, depth=0.08, fw=0.05, cols=2, frame='chrome', glass='glass1', sill='chrome', head=None, seed=11)
    put(B, F, fbox((vent[0] - 0.1, vent[2] - 0.06, 0.0), (vent[1] + 0.1, vent[2], 0.38), 0.01, 'chromew'))
    for x in np.linspace(vent[0] + 0.15, vent[1] - 0.15, 3):
        put(B, F, fbox((x - 0.03, vent[2] - 0.32, 0.25), (x + 0.03, vent[2] - 0.06, 0.32), 0.005, 'chrome'))
    decal(B, F, vent[1] + 0.12, vent[1] + 0.62, 1.1, 1.75, 0.02, 'mi_cafemenu')
    shop_front_glass(B, F, *sf, seed=12)
    door(B, F, *dr, mat='alu', glass=0.85, panels=((1, 1),), name='Door')
    awning(B, F, -W / 2 + 0.6, W / 2 - 0.4, 3.0, 1.2, 0.5, int((W - 1.0) / 0.42) | 1, mat_a='havred', mat_b='cream2', valance=0.22,
           scallops=False)
    decal(B, F, -W / 2 + 0.6, W / 2 - 0.6, H + pp - 0.85, H + pp - 0.15, 0.02, 'mi_ventanita')
    stripes(B, F, -W / 2 - 0.01, W / 2 + 0.01, H + 0.18, n=1, h=0.08, gap=0.0, mat='accentw')
    jalousie(B, Lf, -side[1], -side[0], side[2], side[3])
    grille(B, Lf, -side[1] - 0.05, -side[0] + 0.05, side[2] - 0.05, side[3] + 0.05)
    # the step, the dominoes regulars' bench by the window, a newspaper box
    put(B, F, fbox((-W / 2, 0.0, 0.0), (W / 2, 0.08, 0.35), 0.01, 'terrazzo'))
    B.add(cbox2((W / 2 - 0.4, -0.75, 0.0), (W / 2 + 0.2, -0.35, 1.05), 0.03, 'cuban'))
    for x in (-1.0, 1.4):
        flat_ac(B, x, D - 2.2, H)
    ac_unit(B, Rt, 3.5, 2.1)
    wall_pipe(B, W / 2 - 0.16, -0.08, H + pp - 0.1)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=3.0, length=0.5, k=0.35)
    return H + pp + 0.3


def tabaqueria(B):
    """A two-storey Little Havana corner building: a cigar shop below (dark wooden double doors, a shop window with its iron
    grille, a hand-painted sign), an apartment above with jalousie windows behind a wrought-iron balcony on brackets, a
    flat roof behind a stepped parapet, a wall AC unit dripping."""
    W, H, D = B.W, B.H, B.D
    pp = 0.9
    sf = (-W / 2 + 0.7, -0.4, 0.5, 2.6)
    dr = (0.2, 1.8, 0.0, 2.7)
    up1 = (-W / 2 + 0.9, -0.5, 4.1, 5.7); up2 = (0.5, W / 2 - 0.9, 4.1, 5.7)
    top = [(-W / 2, H + pp), (-1.4, H + pp), (-1.4, H + pp + 0.5), (1.4, H + pp + 0.5), (1.4, H + pp), (W / 2, H + pp)]
    F, Rt, Bk, Lf = plain_walls(B, H + pp, top, fronts=[sf, dr, up1, up2])
    flat_top(B, H, pp)
    shop_front_glass(B, F, *sf, seed=21, cols=2)
    grille(B, F, sf[0] - 0.04, sf[1] + 0.04, sf[2] - 0.02, sf[3] + 0.02)
    door(B, F, *dr, mat='woodd', glass=None, panels=((2, 4),), double=True, name='Door')
    decal(B, F, -W / 2 + 0.6, W / 2 - 0.6, 3.05, 3.7, 0.02, 'mi_tabacos')
    for o in (up1, up2):
        jalousie(B, F, *o)
    iron_rail(B, F, -W / 2 + 0.6, W / 2 - 0.6, 3.95, h=1.0, out=0.75)
    for x in (-W / 2 + 0.8, W / 2 - 0.8):
        put(B, F, fbox((x - 0.05, 3.55, 0.0), (x + 0.05, 3.9, 0.6), 0.01, 'black'))
    eyebrow(B, F, -W / 2, W / 2, 5.95, out=0.35)
    ac_unit(B, F, W / 2 - 0.9, 5.0)
    pot(B, (-W / 2 + 1.2, -0.55, 3.88), 0.15, 0.28, 'pot', 'flowers', seed=22)
    pot(B, (W / 2 - 1.6, -0.55, 3.88), 0.15, 0.28, 'pot', 'flowers', seed=23)
    meter_box(B, Rt, 1.0, 1.4)
    wall_pipe(B, -W / 2 + 0.16, -0.08, H + pp - 0.1)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=3.0, length=0.5, k=0.3)
    return H + pp + 0.5


def fruteria(B):
    """A fruit and juice shop open to the sidewalk: a roll-up front with crates of mangoes, papayas, plantains and limes on
    tiered stands, a green awning, the shop's name over it, a juice counter at the back."""
    W, H, D = B.W, B.H, B.D
    pp = 0.7
    op = (-W / 2 + 0.6, W / 2 - 0.6, 0.0, 2.8)
    F, Rt, Bk, Lf = plain_walls(B, H + pp, None, fronts=[op])
    flat_top(B, H, pp)
    shop_room(B, op[0], op[1], 0.0, op[3], 3.0)
    put(B, F, fbox((op[0], op[3], -0.02), (op[1], op[3] + 0.35, 0.18), 0.01, 'accentp'))      # the rolled-up shutter's box
    awning(B, F, -W / 2 + 0.4, W / 2 - 0.4, 3.15, 1.4, 0.55, int((W - 0.8) / 0.4) | 1, mat_a='green', mat_b='cream2', valance=0.22)
    decal(B, F, -W / 2 + 0.6, W / 2 - 0.6, H + pp - 0.8, H + pp - 0.12, 0.02, 'mi_fruteria')
    kinds = ['orange', 'green', 'lemon', 'tomato', 'orange', 'green']
    for k, kind in enumerate(kinds):
        x = op[0] + 0.55 + k * (op[1] - op[0] - 1.1) / (len(kinds) - 1)
        for row, (y, z) in enumerate(((-0.55, 0.45), (-0.1, 0.8))):
            B.add(cbox2((x - 0.34, y - 0.22, 0.0), (x + 0.34, y + 0.22, z - 0.18), 0.01, 'woodc'))
            crate(B, (x, y, z - 0.18), (0.62, 0.42, 0.18), kinds[(k + row) % len(kinds)], tilt=0.12)
    for k in range(4):
        melon(B, (op[1] - 0.6 - 0.35 * k, -0.85, 0.17), 0.17, seed=40 + k)
    # bunches of plantains hanging from the awning frame
    for x in np.linspace(op[0] + 0.6, op[1] - 0.6, 4):
        B.add(blob((x, -0.9, 2.45), (0.16, 0.12, 0.26), 'mangog', 6, 3, int(x * 10) % 97, 0.15))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=3.15, length=0.5, k=0.3)
    return H + pp + 0.3


def mural_wall(B):
    """A two-storey blank side wall of a block, its whole face a painted mural (invented: tropical flowers, waves, a
    rooster, birds), the paint chipped at the bottom; a parking lot's low wall and a palm in front."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = plain_walls(B, H + 0.5)
    flat_top(B, H, 0.5)
    decal(B, F, -W / 2 + 0.15, W / 2 - 0.15, 0.25, H + 0.2, 0.012, 'mi_mural1')
    put(B, F, fbox((-W / 2 - 0.5, -1.2, 0.0), (W / 2 + 0.5, -1.0, 0.55), 0.02, 'concw'))
    for x in (-W / 2 + 1.2, W / 2 - 1.8):
        flat_ac(B, x, D - 2.0, H)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=0.0, length=0.6, k=0.25)
    return H + 0.6


def mural_wall2(B):
    """A one-storey warehouse wall painted end to end (invented: waves, a pelican, a sun over palms), a roll-up door."""
    W, H, D = B.W, B.H, B.D
    rd = (W / 2 - 3.3, W / 2 - 0.5, 0.0, 3.0)
    F, Rt, Bk, Lf = plain_walls(B, H + 0.4, None, fronts=[rd])
    flat_top(B, H, 0.4)
    decal(B, F, -W / 2 + 0.1, rd[0] - 0.15, 0.2, H + 0.25, 0.012, 'mi_mural3')
    tile_cells(B, F, rd[0], rd[1], 0.0, rd[3], -0.12, 'mi_shutter', 1.4)
    put(B, F, fbox((rd[0] - 0.1, rd[3], 0.0), (rd[1] + 0.1, rd[3] + 0.3, 0.2), 0.01, 'alu'))
    return H + 0.5


def domino_table(B):
    """A domino table from the little park on Calle Ocho: a square concrete table with a green top and a game of dominoes
    laid out on it, four stools round it (the game's own obstacle: its top is 0.75 m up)."""
    B.add(cbox2((-0.15, -0.15, 0.0), (0.15, 0.15, 0.7), 0.02, 'concw'))
    B.add(cbox2((-0.62, -0.62, 0.68), (0.62, 0.62, 0.75), 0.02, 'concw'))
    B.add(box((-0.55, -0.55, 0.75), (0.55, 0.55, 0.752), 'felt'))
    rng = np.random.default_rng(5)
    for k in range(14):
        a = rng.uniform(0, math.pi)
        x, y = rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4)
        bm = box((-0.05, -0.025, 0.0), (0.05, 0.025, 0.018), 'domino')
        xform(bm, T(x, y, 0.752) @ R(a, 'Z'))
        B.add(bm)
    for dx, dy in ((-0.95, 0.0), (0.95, 0.0), (0.0, 0.95)):
        stool(B, dx, dy, 'concw', 0.45)
    return 0.8


def domino_park(B):
    """The domino park's pergola: white columns under slatted beams, a low wall with a mosaic band, two tables with their
    players' stools, potted palms; the whole of it behind the sidewalk."""
    W, H, D = B.W, B.H, B.D
    for x in np.linspace(-W / 2 + 0.3, W / 2 - 0.3, 5):
        for y in (0.3, D - 0.3):
            column(B, x, y, 0.0, H, s=0.3, mat='white')
    B.add(cbox2((-W / 2, 0.1, H), (W / 2, 0.5, H + 0.3), 0.02, 'white'))
    B.add(cbox2((-W / 2, D - 0.5, H), (W / 2, D - 0.1, H + 0.3), 0.02, 'white'))
    for x in np.arange(-W / 2 + 0.2, W / 2, 0.45):
        B.add(cbox2((x - 0.06, 0.0, H + 0.3), (x + 0.06, D, H + 0.5), 0.01, 'white'))
    B.add(cbox2((-W / 2, D - 0.2, 0.0), (W / 2, D + 0.1, 0.7), 0.03, 'concw'))
    B.add(box((-W / 2, D - 0.21, 0.4), (W / 2, D - 0.2, 0.6), 'aqua'))
    for x in (-W / 4, W / 4):
        B.add(cbox2((x - 0.12, D / 2 - 0.12, 0.0), (x + 0.12, D / 2 + 0.12, 0.7), 0.02, 'concw'))
        B.add(cbox2((x - 0.55, D / 2 - 0.55, 0.68), (x + 0.55, D / 2 + 0.55, 0.75), 0.02, 'concw'))
        B.add(box((x - 0.48, D / 2 - 0.48, 0.75), (x + 0.48, D / 2 + 0.48, 0.752), 'felt'))
        for dx, dy in ((-0.85, 0), (0.85, 0), (0, -0.85), (0, 0.85)):
            stool(B, x + dx, D / 2 + dy, 'concw', 0.45)
    palm_pot(B, -W / 2 - 0.6, 0.6); palm_pot(B, W / 2 + 0.6, 0.6)
    return H + 0.6


def fruit_cart(B):
    """A fruit vendor's cart: a wooden cart on bicycle wheels heaped with mangoes and limes, a yellow umbrella over it."""
    B.add(cbox2((-0.8, -0.4, 0.55), (0.8, 0.4, 0.95), 0.02, 'cuban'))
    B.add(cbox2((-0.75, -0.35, 0.95), (0.75, 0.35, 1.0), 0.01, 'woodc'))
    for x in (-0.55, 0.55):
        w = tube([(x + 0.38 * math.cos(a), -0.42, 0.4 + 0.38 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 13)], 0.02, 'black', 4, caps=False)
        B.add(w)
        B.add(tube([(x, -0.44, 0.4), (x, 0.44, 0.4)], 0.015, 'metald', 4))
    rng = np.random.default_rng(9)
    for k in range(26):
        x, y = rng.uniform(-0.65, 0.65), rng.uniform(-0.28, 0.28)
        col = 'mango' if k % 3 else 'mangog'
        B.add(blob((x, y, 1.05 + rng.uniform(0, 0.08)), (0.07, 0.055, 0.06), col, 6, 2, k, 0.05))
    B.add(tube([(0.0, 0.1, 1.0), (0.0, 0.1, 2.2)], 0.02, 'metald', 5))
    um, _ = lathe([(0.0, 2.35), (0.9, 2.1), (0.95, 2.05), (0.0, 2.08)], 12, 'umbrella')
    xform(um, T(0, 0.1, 0)); B.add(um)
    B.add(tube([(-0.8, 0.0, 0.85), (-1.2, 0.0, 0.95)], 0.02, 'woodd', 4))
    return 2.4


def rooster(B, hen=False):
    """A rooster (or a hen) of Little Havana's free-roaming chickens: body, tail of sickle feathers, head, comb, wattle,
    beak, legs; low poly, its head toward +X (the game turns it)."""
    body = 'featherh' if hen else 'feather'
    B.add(blob((0.0, 0.0, 0.3), (0.17, 0.11, 0.13), body, 7, 3, 3, 0.08))
    B.add(blob((-0.05, 0.0, 0.36), (0.12, 0.12, 0.08), 'featherh' if not hen else body, 6, 2, 4, 0.1))
    B.add(blob((0.15, 0.0, 0.47), (0.065, 0.055, 0.075), body, 6, 2, 5, 0.06))
    B.add(blob((0.15, 0.0, 0.55), (0.05, 0.012, 0.035 if not hen else 0.02), 'comb', 5, 2, 6, 0.05))
    B.add(blob((0.2, 0.0, 0.43), (0.015, 0.01, 0.03), 'comb', 4, 2, 7, 0.0))
    b, _ = lathe([(0.0, 0.0), (0.02, 0.0), (0.0, 0.05)], 6, 'beak'); xform(b, T(0.2, 0, 0.48) @ R(-math.pi / 2, 'Y')); B.add(b)
    if hen:
        B.add(blob((-0.17, 0.0, 0.38), (0.05, 0.05, 0.08), body, 5, 2, 8, 0.1))
    else:
        for k, a in enumerate((0.3, 0.6, 0.9, 1.2)):
            B.add(tube([(-0.12, 0, 0.36), (-0.2 - 0.06 * math.cos(a), 0, 0.42 + 0.18 * math.sin(a)), (-0.3 - 0.1 * k * 0.3, 0, 0.3 + 0.05 * k)],
                       0.025, 'tailg', 4))
    for y in (-0.04, 0.04):
        B.add(tube([(0.0, y, 0.2), (0.01, y, 0.0)], 0.012, 'beak', 4))
        B.add(tube([(0.01, y, 0.005), (0.07, y, 0.005)], 0.008, 'beak', 3))
    return 0.6


def hen(B): return rooster(B, True)


def iguana(B):
    """A green iguana sunning itself: a long low body, the crest along its back, a long banded tail, splayed legs."""
    B.add(blob((0.0, 0.0, 0.09), (0.24, 0.07, 0.06), 'iguana', 7, 3, 11, 0.06))
    B.add(blob((0.28, 0.0, 0.11), (0.08, 0.05, 0.05), 'iguana', 6, 2, 12, 0.05))
    B.add(tube([(-0.2, 0, 0.08), (-0.45, 0.02, 0.05), (-0.7, -0.03, 0.03), (-0.9, 0.0, 0.02)], 0.03, 'iguana', 5))
    for k in range(9):
        x = 0.24 - k * 0.06
        B.add(box((x - 0.008, -0.004, 0.13), (x + 0.008, 0.004, 0.17 - k * 0.003), 'tailg'))
    for x in (0.15, -0.15):
        for y in (-1, 1):
            B.add(tube([(x, y * 0.05, 0.07), (x + 0.03, y * 0.14, 0.03), (x + 0.06, y * 0.16, 0.0)], 0.015, 'iguana', 4))
    return 0.2


def pelican_post(B):
    """A weathered wooden piling at the bay's edge with a brown pelican perched on it, bill tucked on its chest."""
    B.add(tube([(0, 0, -0.4), (0, 0, 1.9)], 0.16, 'woodg', 8))
    B.add(cbox2((-0.17, -0.17, 1.9), (0.17, 0.17, 1.95), 0.02, 'woodg'))
    B.add(blob((0.0, 0.0, 2.2), (0.26, 0.15, 0.17), 'pelican', 7, 3, 21, 0.06))
    B.add(blob((0.12, 0.0, 2.45), (0.06, 0.05, 0.12), 'pelicanw', 6, 2, 22, 0.05))
    B.add(blob((0.15, 0.0, 2.58), (0.06, 0.05, 0.05), 'pelicanw', 6, 2, 23, 0.05))
    B.add(tube([(0.18, 0, 2.58), (0.3, 0, 2.45), (0.32, 0, 2.2)], 0.03, 'beak', 5))
    B.add(tube([(-0.24, 0, 2.18), (-0.38, 0, 2.08)], 0.05, 'pelican', 5))
    return 2.7


def scooter(B, standing=False):
    """A rental e-scooter in an invented livery: a low deck with its grip tape, the stem, the handlebar with grips, a lamp,
    small solid wheels; lying on its side across the sidewalk, or stood on its kickstand."""
    parts = []
    deck = cbox2((-0.42, -0.08, 0.06), (0.42, 0.08, 0.12), 0.02, 'scoot'); parts.append(deck)
    parts.append(box((-0.36, -0.07, 0.12), (0.3, 0.07, 0.123), 'scootd'))
    for x in (-0.45, 0.47):
        w, _ = lathe([(0.0, -0.025), (0.1, -0.025), (0.11, 0.0), (0.1, 0.025), (0.0, 0.025)], 10, 'tire')
        xform(w, T(x, 0, 0.1) @ R(math.pi / 2, 'X')); parts.append(w)
    parts.append(tube([(0.45, 0, 0.1), (0.4, 0, 1.05)], 0.025, 'scootd', 6))
    parts.append(tube([(0.4, -0.24, 1.07), (0.4, 0.24, 1.07)], 0.018, 'scootd', 5))
    for y in (-0.24, 0.24):
        parts.append(tube([(0.4, y, 1.07), (0.4, y + (0.09 if y > 0 else -0.09), 1.07)], 0.025, 'black', 5))
    parts.append(cbox2((0.43, -0.04, 0.8), (0.47, 0.04, 0.86), 0.01, 'lamp'))
    parts.append(box((0.35, -0.085, 0.07), (0.25, 0.085, 0.11), 'scoot'))
    m = T(0, 0, 0)
    if not standing:
        # on its side: the deck along the sidewalk, the stem lying toward the street, a grip and the wheels' rims on the ground
        m = T(0, 0.55, 0.3) @ R(math.pi / 2, 'X') @ R(0.08, 'Y')
    for p in parts:
        xform(p, m); B.add(p)
    if standing:
        B.add(tube([(-0.1, 0.06, 0.07), (-0.2, 0.14, 0.0)], 0.01, 'scootd', 3))
    return 1.1 if standing else 0.4


def scooter_up(B): return scooter(B, True)


# ================================================================ Brickell and downtown
def curtain(B, wf, u0, u1, v0, v1, floor_h=3.2, bay=2.4, slab='slab', glass='glassb', balcony=0.0, fins=0.0):
    """A glass curtain wall from v0 to v1: one glazed band a floor (a reflection region over it), the floor slabs as white
    bands (with a balcony's glass rail when balcony > 0), the mullions every `bay`, vertical fins if asked."""
    mb = MB()
    v = v0
    while v < v1 - 0.01:
        va = min(v + floor_h, v1)
        g0, g1 = v + 0.35, va
        mb.face([(u0, g0, -0.04), (u1, g0, -0.04), (u1, g1, -0.04), (u0, g1, -0.04)], glass, (0, 0, 1), 1.0)
        v = va
    put(B, wf, mb.bm())
    v = v0
    while v < v1 - 0.01:
        put(B, wf, fbox((u0 - 0.05, v, -0.02), (u1 + 0.05, v + 0.35, 0.05 + balcony), 0.01, slab))
        if balcony > 0:
            put(B, wf, box((u0, v + 0.35, balcony - 0.02), (u1, v + 1.35, balcony), 'glassg'))
            put(B, wf, tube([(u0, v + 1.36, balcony - 0.01), (u1, v + 1.36, balcony - 0.01)], 0.02, 'alu', 4))
        v += floor_h
    put(B, wf, fbox((u0 - 0.05, v1, -0.02), (u1 + 0.05, v1 + 0.5, 0.06), 0.01, slab))
    x = u0
    while x <= u1 + 0.01:
        put(B, wf, box((x - 0.04, v0, -0.03), (x + 0.04, v1, 0.0 + (fins if fins else 0.01)), 'alu' if not fins else slab))
        x += bay


def tower(B, glass='glassb', balcony=1.2, floor_h=3.2, crown=True, fins=0.0, podium=7.0, bay=2.6):
    """A glass condo (or office) tower: a podium of lobby glass and stucco, the tower's curtain walls over it on every side,
    floor slabs as white bands (deep balconies on a condo), a crown of fins and the rooftop plant. Seen from the street far
    behind the near row, its top in the haze."""
    W, H, D = B.W, B.H, B.D
    sides = [WF((0, 0, 0), (1, 0, 0), 'front'), WF((W / 2, 0, 0), (0, 1, 0), 'right'), WF((-W / 2, 0, 0), (0, -1, 0), 'left'),
             WF((0, D, 0), (-1, 0, 0), 'back')]
    spans = [(-W / 2, W / 2), (0, D), (-D, 0), (-W / 2, W / 2)]
    for wf, (u0, u1) in zip(sides, spans):
        wall(B, wf, u0, u1, podium, [(u0 + 1.2, u1 - 1.2, 0.0, podium - 1.0)], mat='wall')
        window(B, wf, u0 + 1.2, u1 - 1.2, 0.0, podium - 1.0, depth=0.25, fw=0.08, cols=max(2, int((u1 - u0) / 3)), frame='alud',
               glass='glass3', sill='conc', head=None, cheap=True, register=False, seed=int(u0 * 7) % 91)
        curtain(B, wf, u0 + 0.2, u1 - 0.2, podium, H, floor_h=floor_h, bay=bay, glass=glass, balcony=balcony, fins=fins)
    # the corners: white concrete fins up the whole height
    for x, y in ((-W / 2, 0), (W / 2, 0), (-W / 2, D), (W / 2, D)):
        B.add(cbox2((x - 0.35, y - 0.35, podium), (x + 0.35, y + 0.35, H + 0.5), 0.05, 'slab'))
    B.add(box((-W / 2, 0, H + 0.4), (W / 2, D, H + 0.5), 'roof'))
    if crown:
        for x in np.linspace(-W / 2 + 1, W / 2 - 1, 7):
            B.add(box((x - 0.12, -0.2, H + 0.5), (x + 0.12, 0.2, H + 4.0), 'slab'))
        B.add(cbox2((-W / 4, D / 3, H + 0.5), (W / 4, 2 * D / 3, H + 3.4), 0.05, 'concw'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=podium, length=0.6, k=0.3)
    return H + (4.0 if crown else 0.5)


def condo_tower(B): return tower(B, 'glassb', balcony=1.3)
def office_tower(B): return tower(B, 'glassd', balcony=0.0, floor_h=3.8, fins=0.45, bay=1.6)
def condo_tower2(B): return tower(B, 'glassg', balcony=1.0, floor_h=3.1, crown=False)


def tower_podium(B):
    """The street front of a condo tower: a two-storey lobby of floor-to-ceiling glass behind white columns, a valet canopy
    on slim steel posts over the drive, planters with palms, the building's name in steel letters (invented)."""
    W, H, D = B.W, B.H, B.D
    lob = (-W / 2 + 1.0, W / 2 - 1.0, 0.0, H - 0.8)
    F, Rt, Bk, Lf = plain_walls(B, H + 0.6, None, fronts=[lob])
    flat_top(B, H, 0.6)
    window(B, F, *lob, depth=0.35, fw=0.06, cols=max(3, int(W / 2.2)), rows=2, frame='alud', glass='glass3', sill='conc', head=None, seed=51)
    shop_room(B, lob[0], lob[1], 0.0, lob[3], 4.0)
    for x in np.linspace(-W / 2 + 1.0, W / 2 - 1.0, 6):
        column(B, x, -0.4, 0.0, H - 0.5, s=0.45, mat='slab')
    # the valet canopy: a thin white slab out over the drive on four steel posts
    B.add(cbox2((-W / 4, -3.6, 4.0), (W / 4, -0.2, 4.25), 0.04, 'slab'))
    for x in (-W / 4 + 0.4, W / 4 - 0.4):
        B.add(tube([(x, -3.3, 0.0), (x, -3.3, 4.0)], 0.07, 'alu', 8))
    for x in (-W / 2 + 0.6, W / 2 - 0.6):
        B.add(cbox2((x - 0.7, -1.4, 0.0), (x + 0.7, -0.3, 0.7), 0.03, 'concw'))
    decal(B, F, -2.6, 2.6, H - 0.7, H - 0.2, 0.03, 'mi_tower')
    return H + 0.7


def site_fence(B):
    """A construction site's fence: steel posts and panels hung with a printed mesh banner (a picture of the tower to come,
    invented), a gate for the trucks, the site's hard-hat sign."""
    W, H = B.W, B.H
    for x in np.linspace(-W / 2, W / 2, 6):
        B.add(tube([(x, 0, 0.0), (x, 0, H)], 0.04, 'galvw', 6))
        B.add(cbox2((x - 0.25, -0.15, 0.0), (x + 0.25, 0.15, 0.12), 0.02, 'orange'))
    B.add(tube([(-W / 2, 0, H), (W / 2, 0, H)], 0.025, 'galvw', 4))
    mb = MB()
    mb.face([(-W / 2, -0.02, 0.15), (W / 2, -0.02, 0.15), (W / 2, -0.02, H - 0.05), (-W / 2, -0.02, H - 0.05)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('mi_mesh', (co.x + W / 2) / W, (co.z - 0.15) / (H - 0.2), 0.0))
    B.add(mb.bm())
    return H + 0.1


def coffee_kiosk(B):
    """A sidewalk coffee kiosk: a little stainless-and-teak box with its serving hatch propped open, the menu and name over it,
    two stools at its counter, a parasol."""
    W, H, D = B.W, B.H, B.D
    B.add(cbox2((-W / 2, 0, 0.0), (W / 2, D, H), 0.05, 'chromew'))
    B.add(cbox2((-W / 2 + 0.2, -0.02, 1.05), (W / 2 - 0.2, 0.02, 2.0), 0.02, 'interior'))
    B.add(cbox2((-W / 2 + 0.1, -0.45, 1.0), (W / 2 - 0.1, 0.0, 1.06), 0.02, 'woodc'))
    B.add(cbox2((-W / 2 + 0.1, -0.7, 2.05), (W / 2 - 0.1, 0.0, 2.12), 0.02, 'aquad'))
    mb = MB()
    mb.face([(-W / 2 + 0.1, -0.03, H - 0.45), (W / 2 - 0.1, -0.03, H - 0.45), (W / 2 - 0.1, -0.03, H - 0.05), (-W / 2 + 0.1, -0.03, H - 0.05)],
            'tex', (0, -1, 0), 1.0, lambda co: reg_uv('mi_kiosk', (co.x + W / 2 - 0.1) / (W - 0.2), (co.z - H + 0.45) / 0.4, 0.0))
    B.add(mb.bm())
    for x in (-0.5, 0.5):
        stool(B, x, -0.8, 'aquad', 0.72)
    return H + 0.1


def deco_block(B, sign, colour_band='aqua', floors=3, arcade=True, fins=True):
    """A downtown Art Deco block of three storeys: stucco with vertical fins and racing stripes, a stepped parapet with a
    central tower, steel casement windows over eyebrow ledges, and at the street a deep canvas-covered arcade over the sidewalk
    on slim columns (the downpour's shelter), shopfronts under it with their names."""
    W, H, D = B.W, B.H, B.D
    pp = 1.0
    sf = (-W / 2 + 0.6, W / 2 - 2.0, 0.0, 2.9)
    dr = (W / 2 - 1.7, W / 2 - 0.6, 0.0, 2.6)
    ups = []
    fl = 3.3
    for f in range(1, floors):
        z0 = 3.6 + (f - 1) * fl
        for k in range(3):
            u0 = -W / 2 + 0.8 + k * (W - 1.6) / 3 + 0.25
            ups.append((u0, u0 + (W - 1.6) / 3 - 0.5, z0, z0 + 1.7))
    top = [(-W / 2, H + pp), (-1.6, H + pp), (-1.6, H + pp + 0.9), (-0.8, H + pp + 0.9), (-0.8, H + pp + 1.6), (0.8, H + pp + 1.6),
           (0.8, H + pp + 0.9), (1.6, H + pp + 0.9), (1.6, H + pp), (W / 2, H + pp)]
    F, Rt, Bk, Lf = plain_walls(B, H + pp, top, fronts=[sf, dr] + ups)
    flat_top(B, H, pp)
    shop_front_glass(B, F, *sf, seed=hash(sign) % 97 if sign else 61, cols=4)
    door(B, F, *dr, mat='alu', glass=0.85, panels=((1, 1),), name='Door')
    for o in ups:
        window(B, F, *o, depth=0.16, fw=0.05, cols=3, rows=2, frame='trimw', glass='glass2', sill='trim', head=None, seed=int(o[0] * 9) % 91)
        eyebrow(B, F, o[0] - 0.15, o[1] + 0.15, o[3] + 0.08, out=0.35)
    if fins:
        for x in (-1.2, 1.2):
            B.add(cbox2((x - 0.1, -0.4, 3.4), (x + 0.1, 0.0, H + pp + 1.2), 0.03, 'trim'))
    stripes(B, F, -W / 2 - 0.01, W / 2 + 0.01, H + pp - 0.4, n=3, h=0.07, gap=0.07, mat='accentw')
    if sign:
        decal(B, F, -W / 2 + 0.7, W / 2 - 0.7, 3.24, 3.56, 0.02, sign)
    if arcade:
        # the arcade: a canvas roof from the wall out over the whole sidewalk, on columns at its front edge (behind the kid's
        # line, the game puts them at the back of the footpath: the canopy reaches over it)
        B.add(cbox2((-W / 2, -3.0, 3.05), (W / 2, 0.0, 3.2), 0.03, colour_band))
        B.add(cbox2((-W / 2, -3.05, 2.85), (W / 2, -2.95, 3.2), 0.02, 'accentw'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=3.05, length=0.6, k=0.35)
    for x in (-W / 4, W / 4):
        flat_ac(B, x, D - 2.5, H)
    return H + pp + 1.6


def deco_block_a(B): return deco_block(B, 'mi_deco1', 'aquad')
def deco_block_b(B): return deco_block(B, 'mi_deco2', 'havred', floors=2, fins=False)


def med_revival(B):
    """A Mediterranean Revival building of two storeys: cream stucco, a ground-floor loggia of round arches on columns, arched
    windows above with iron balconettes, a hipped roof of red barrel tiles, a little tiled tower at one corner."""
    W, H, D = B.W, B.H, B.D
    n = 5
    bay = (W - 0.8) / n
    arches = [(-W / 2 + 0.4 + k * bay + 0.2, -W / 2 + 0.4 + (k + 1) * bay - 0.2, 0.0, 2.6) for k in range(n)]
    ups = [(a[0] + 0.25, a[1] - 0.25, 3.8, 5.4) for a in arches]
    F, Rt, Bk, Lf = plain_walls(B, H, None, fronts=arches + ups)
    for a in arches:
        shop_room(B, a[0], a[1], 0.0, a[3] + 0.4, 2.0)
        arch_head(B, F, a[0], a[1], a[3], out=0.04, glass='glass0')
    for o in ups:
        window(B, F, *o, depth=0.2, fw=0.06, cols=2, frame='woodd', glass='glass1', sill='trim', head=None, seed=int(o[0] * 7) % 91)
        arch_head(B, F, o[0], o[1], o[3], out=0.03, glass='glass1')
        iron_rail(B, F, o[0] - 0.1, o[1] + 0.1, o[2], h=0.7, out=0.35)
    hip(B, -W / 2, W / 2, 0, D, H, 2.0, over=0.5)
    # the corner tower
    tx = W / 2 - 1.6
    B.add(cbox2((tx - 1.2, 0.3, H), (tx + 1.2, 2.7, H + 3.0), 0.02, 'wall'))
    for k in range(2):
        put(B, WF((tx - 1.2 + 0.4 + k * 1.0, 0.3, 0), (1, 0, 0), 'front'), fbox((0, H + 1.2, -0.02), (0.6, H + 2.4, 0.01), 0.01, 'dark'))
    hip(B, tx - 1.2, tx + 1.2, 0.3, 2.7, H + 3.0, 1.4, over=0.35)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=2.6, length=0.5, k=0.3)
    return H + 4.4


def spanish_tower(B):
    """A tall Mediterranean Revival tower (invented): a cream shaft in stages, arched windows up it, balustraded setbacks, a
    lantern and a domed cupola on top; it stands among the boulevard's palms and the glass towers behind."""
    W, H, D = B.W, B.H, B.D
    stages = [(0.0, 18.0, 1.0), (18.0, 32.0, 0.82), (32.0, 42.0, 0.64), (42.0, 48.0, 0.46)]
    for z0, z1, s in stages:
        w, d = W * s, D * s
        y0 = (D - d) / 2
        B.add(cbox2((-w / 2, y0, z0), (w / 2, y0 + d, z1), 0.04, 'wall'))
        for f in np.arange(z0 + 2.0, z1 - 1.5, 3.4):
            for k in range(max(1, int(w / 3))):
                x = -w / 2 + (k + 0.5) * w / max(1, int(w / 3))
                wf = WF((0, y0, 0), (1, 0, 0), 'front')
                put(B, wf, fbox((x - 0.45, f, -0.03), (x + 0.45, f + 1.7, 0.01), 0.01, 'dark'))
                arch_head(B, wf, x - 0.45, x + 0.45, f + 1.7, out=0.02, glass='glass0', n=6)
        B.add(cbox2((-w / 2 - 0.3, y0 - 0.3, z1 - 0.3), (w / 2 + 0.3, y0 + d + 0.3, z1), 0.03, 'trim'))
    dome, _ = lathe([(0.0, 0.0), (2.4, 0.0), (2.4, 1.6), (2.2, 2.4), (1.6, 3.4), (0.8, 4.0), (0.0, 4.2)], 16, 'roof')
    xform(dome, T(0, D / 2, 48.0)); B.add(dome)
    B.add(tube([(0, D / 2, 52.2), (0, D / 2, 54.0)], 0.12, 'brass', 6))
    return 54.0


# ================================================================ the river and the bay
def hull(B, L, Wd, Hh, bow=0.28, mat='hullb', top='white', sheer=0.3):
    """A ship's hull: flat-sided, its bow drawn to a point and raked, a rounded stern, a sheer line rising to the bow."""
    pts = []
    n = 10
    for k in range(n + 1):
        t = k / n
        x = -L / 2 + L * t
        half = Wd / 2 * (1.0 if t < 1 - bow else max(0.02, (1 - t) / bow))
        if t < 0.08: half = Wd / 2 * (0.75 + 0.25 * t / 0.08)
        pts.append((x, half))
    outline = [(x, -h) for x, h in pts] + [(x, h) for x, h in reversed(pts)]
    hb = extrude_poly(outline, Hh, mat)
    xform(hb, T(0, 0, 0)); B.add(hb)
    deck = extrude_poly([(x * 0.98, y * 0.94) for x, y in outline], 0.08, 'deckg')
    xform(deck, T(0, 0, Hh)); B.add(deck)
    rail = [(x, y * 0.97, Hh + 0.45) for x, y in outline] + [(outline[0][0], outline[0][1] * 0.97, Hh + 0.45)]
    B.add(tube(rail, 0.035, top, 4, caps=False))
    for x, y in outline[::2]:
        B.add(tube([(x, y * 0.97, Hh), (x, y * 0.97, Hh + 0.45)], 0.025, top, 4))


def freighter(B):
    """A small river freighter of the Miami River's working trade: a rusty dark hull with streaks, a deck stacked with
    containers and lashed cargo, the deckhouse and bridge aft, a mast and a crane forward."""
    L, Wd, Hh = B.W, B.D, 3.0
    hull(B, L, Wd, Hh, bow=0.18, mat='hullr', top='rust')
    B.add(box((-L / 2 + 0.6, -Wd / 2 + 0.01, 0.4), (L / 2 - 4.0, -Wd / 2 + 0.02, 0.8), 'black'))
    # containers (painted: rust red, blue, white, green)
    for k in range(5):
        x = -L / 2 + 7.5 + k * 3.9
        mb = MB()
        for j, (y0, y1) in enumerate(((-Wd / 2 + 0.6, -0.1), (0.1, Wd / 2 - 0.6))):
            bm = box((x - 1.8, y0, Hh + 0.1), (x + 1.8, y1, Hh + 2.7), 'tex')
            uv_box(bm, list(bm.faces), 'mi_containers', fit=None)
            B.add(bm)
    dh = cbox2((-L / 2 + 0.8, -Wd / 2 + 0.6, Hh), (-L / 2 + 5.5, Wd / 2 - 0.6, Hh + 3.0), 0.05, 'white'); B.add(dh)
    B.add(cbox2((-L / 2 + 1.4, -Wd / 2 + 0.8, Hh + 3.0), (-L / 2 + 5.0, Wd / 2 - 0.8, Hh + 5.0), 0.05, 'white'))
    put(B, WF((-L / 2 + 3.2, -Wd / 2 + 0.79, 0), (1, 0, 0), 'front'), fbox((-1.6, Hh + 3.6, -0.02), (1.6, Hh + 4.5, 0.01), 0.01, 'glassd'))
    B.add(tube([(-L / 2 + 3.0, 0, Hh + 5.0), (-L / 2 + 3.0, 0, Hh + 8.0)], 0.08, 'white', 6))
    B.add(tube([(L / 2 - 3.0, 0, Hh), (L / 2 - 3.0, 0, Hh + 7.0), (L / 2 - 8.0, 0, Hh + 4.5)], 0.14, 'flyel', 6))
    return Hh + 8.0


def tug(B):
    """A harbour tug: a stubby red-and-black hull ringed with black tyre fenders, a tall white wheelhouse, its funnel."""
    L, Wd, Hh = B.W, B.D, 1.8
    hull(B, L, Wd, Hh, bow=0.3, mat='hullr', top='black')
    for x in np.linspace(-L / 2 + 0.8, L / 2 - 1.5, 7):
        B.add(tube([(x + 0.3 * math.cos(a), -Wd / 2 - 0.05, 1.2 + 0.3 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)], 0.08, 'tire', 4, caps=False))
    B.add(cbox2((-1.6, -Wd / 2 + 0.6, Hh), (1.6, Wd / 2 - 0.6, Hh + 2.2), 0.05, 'white'))
    B.add(cbox2((-1.2, -Wd / 2 + 0.8, Hh + 2.2), (1.4, Wd / 2 - 0.8, Hh + 4.0), 0.05, 'white'))
    put(B, WF((0.1, -Wd / 2 + 0.79, 0), (1, 0, 0), 'front'), fbox((-1.2, Hh + 2.7, -0.02), (1.2, Hh + 3.6, 0.01), 0.01, 'glassd'))
    f, _ = lathe([(0.0, 0.0), (0.45, 0.0), (0.42, 1.8), (0.0, 1.8)], 10, 'black'); xform(f, T(-2.6, 0, Hh)); B.add(f)
    B.add(box((-3.1, -0.46, Hh + 1.2), (-2.1, 0.46, Hh + 1.45), 'red'))
    return Hh + 4.0


def fishing_boat(B):
    """Uncle Rey's fishing boat: a white hull with a blue stripe, a small cabin with its windscreen forward of the open deck,
    outriggers up, a cooler and crates on deck, fenders over the side, a coil of line at the bow."""
    L, Wd, Hh = B.W, B.D, 0.95
    hull(B, L, Wd, Hh, bow=0.32, mat='busw', top='white')
    B.add(box((-L / 2 + 0.2, -Wd / 2 - 0.002, 0.45), (L / 2 * 0.62, -Wd / 2 - 0.001, 0.6), 'cuban'))
    B.add(cbox2((-0.4, -0.75, Hh), (0.9, 0.75, Hh + 1.2), 0.05, 'white'))
    put(B, WF((1.0, 0, 0), (0, 1, 0), 'right'), fbox((-0.6, Hh + 0.6, -0.02), (0.6, Hh + 1.1, 0.01), 0.01, 'glassd'))
    B.add(cbox2((-0.5, -0.8, Hh + 1.2), (1.0, 0.8, Hh + 1.3), 0.02, 'cuban'))
    for y in (-1, 1):
        B.add(tube([(0.2, y * 0.6, Hh + 1.3), (0.0, y * 1.2, Hh + 3.5)], 0.03, 'chrome', 5))
    B.add(cbox2((-2.0, -0.4, Hh), (-1.3, 0.2, Hh + 0.5), 0.04, 'white'))
    for x in (-1.0, 1.2):
        B.add(blob((x, -Wd / 2 - 0.06, 0.55), (0.1, 0.1, 0.22), 'fender', 6, 2, int(x * 10) % 9, 0.0))
    coil = tube([(L / 2 * 0.55 + 0.18 * math.cos(a), 0.18 * math.sin(a), Hh + 0.04 + 0.006 * k) for k, a in enumerate(np.linspace(0, 6 * math.pi, 40))],
                0.025, 'rope', 4, caps=False)
    B.add(coil)
    return Hh + 3.5


def line_coil(B):
    """A coil of mooring line flaked down on the dock in loose rings, with its end trailing."""
    for k in range(6):
        r = 0.26 - 0.025 * k
        B.add(tube([(r * math.cos(a) + 0.02 * k, r * math.sin(a), 0.025 + 0.012 * k) for a in np.linspace(0, 2 * math.pi, 15)],
                   0.022, 'rope', 4, caps=False))
    B.add(tube([(0.26, 0, 0.025), (0.6, -0.15, 0.02), (0.95, -0.08, 0.02)], 0.022, 'rope', 4))
    return 0.12


def bollard_mia(B):
    """A cast-iron mooring bollard: a squat post with a flared cap, painted black, worn on its lip."""
    b, _ = lathe([(0.0, 0.0), (0.22, 0.0), (0.18, 0.08), (0.16, 0.38), (0.24, 0.45), (0.22, 0.52), (0.0, 0.52)], 12, 'black')
    B.add(b)
    return 0.52


def river_rail(B):
    """The riverwalk's rail: steel posts, a timber top rail and stainless cables, a lamp; 4 m long."""
    W = B.W
    for x in np.linspace(-W / 2, W / 2, 4):
        B.add(cbox2((x - 0.05, -0.05, 0.0), (x + 0.05, 0.05, 1.05), 0.01, 'galvw'))
    B.add(cbox2((-W / 2, -0.08, 1.05), (W / 2, 0.08, 1.12), 0.01, 'woodc'))
    for z in (0.3, 0.55, 0.8):
        B.add(tube([(-W / 2, 0, z), (W / 2, 0, z)], 0.006, 'chrome', 3))
    return 1.12


def bay_rail(B):
    """The bayfront promenade's balustrade: white balusters under a coping, 4 m long."""
    W = B.W
    B.add(cbox2((-W / 2, -0.12, 0.0), (W / 2, 0.12, 0.12), 0.02, 'concw'))
    B.add(cbox2((-W / 2, -0.14, 0.9), (W / 2, 0.14, 1.0), 0.02, 'concw'))
    for x in np.arange(-W / 2 + 0.12, W / 2, 0.24):
        b, _ = lathe([(0.0, 0.12), (0.06, 0.12), (0.04, 0.3), (0.07, 0.55), (0.04, 0.8), (0.06, 0.9), (0.0, 0.9)], 6, 'concw')
        xform(b, T(x, 0, 0)); B.add(b)
    return 1.0


def cruise_ship(B):
    """A cruise ship across the bay, far off in the haze: a long white hull, decks of balconies stepping up, a blue band, a
    raked funnel. Low detail: it is only ever seen in the distance."""
    L, Wd = B.W, B.D
    hull(B, L, Wd, 9.0, bow=0.12, mat='busw', top='white')
    B.add(box((-L / 2 + 2, -Wd / 2 - 0.02, 5.5), (L / 2 - 14, -Wd / 2 - 0.01, 6.5), 'cuban'))
    for k, (s, h) in enumerate(((0.9, 4.0), (0.82, 4.0), (0.72, 4.0), (0.55, 3.0))):
        z0 = 9.0 + sum(hh for _, hh in ((0.9, 4.0), (0.82, 4.0), (0.72, 4.0), (0.55, 3.0))[:k])
        B.add(cbox2((-L * s / 2 - 4, -Wd * 0.42, z0), (L * s / 2 - 8, Wd * 0.42, z0 + h), 0.1, 'white'))
        for z in np.arange(z0 + 0.8, z0 + h - 0.6, 1.2):
            B.add(box((-L * s / 2 - 3.5, -Wd * 0.42 - 0.02, z), (L * s / 2 - 8.5, -Wd * 0.42 - 0.01, z + 0.5), 'glassd'))
    f, _ = lathe([(0.0, 0.0), (3.0, 0.0), (2.4, 7.0), (0.0, 7.0)], 10, 'cuban'); xform(f, T(-L * 0.2, 0, 24.0)); B.add(f)
    return 31.0


# ================================================================ the Underline and Museum Park
def guideway(B):
    """A span of the elevated railway over the Underline: a precast concrete box girder 30 m long, 9 m up, on one round pier
    at its middle (its hammerhead cap under the girder), the pier painted with a mural (invented: flowers, waves, birds); the
    track's parapets along the top."""
    W = B.W
    z = 8.5
    B.add(cbox2((-W / 2, -1.4, z), (W / 2, 1.4, z + 1.8), 0.1, 'concw'))
    for y in (-1.55, 1.55):
        B.add(cbox2((-W / 2, y - 0.15, z + 1.8), (W / 2, y + 0.15, z + 2.6), 0.03, 'concw'))
    B.add(cbox2((-2.6, -1.6, z - 1.2), (2.6, 1.6, z), 0.1, 'concw'))
    p, _ = lathe([(0.0, 0.0), (1.05, 0.0), (1.0, z - 1.2), (0.0, z - 1.2)], 20, 'concw')
    B.add(p)
    # the mural, round the front half of the pier
    mb = MB()
    n = 10
    for k in range(n):
        a0, a1 = math.pi + math.pi * k / n, math.pi + math.pi * (k + 1) / n
        p0 = (1.035 * math.cos(a0), 1.035 * math.sin(a0)); p1 = (1.035 * math.cos(a1), 1.035 * math.sin(a1))
        mb.face([(p0[0], p0[1], 0.3), (p1[0], p1[1], 0.3), (p1[0], p1[1], z - 1.6), (p0[0], p0[1], z - 1.6)], 'tex', (0, -1, 0), 1.0,
                lambda co: reg_uv('mi_mural2', min(1.0, max(0.0, (math.atan2(co.y, co.x) % (2 * math.pi) - math.pi) / math.pi)), (co.z - 0.3) / (z - 1.9), 0.0))
    B.add(mb.bm())
    return z + 2.6


def fitness_bars(B):
    """An outdoor fitness station: a set of pull-up bars at three heights and parallel bars, in powder-coated green steel, on a
    rubber pad."""
    W = B.W
    B.add(box((-W / 2 - 0.3, -0.8, 0.0), (W / 2 + 0.3, 0.8, 0.03), 'rubber'))
    for k, h in enumerate((2.0, 2.3, 2.6)):
        x0 = -W / 2 + k * W / 3; x1 = x0 + W / 3
        for x in (x0 + 0.1, x1 - 0.1):
            B.add(tube([(x, 0.3, 0.0), (x, 0.3, h)], 0.045, 'green', 6))
        B.add(tube([(x0 + 0.1, 0.3, h), (x1 - 0.1, 0.3, h)], 0.03, 'chrome', 6))
    for y in (-0.5, -0.1):
        B.add(tube([(-0.8, y, 1.1), (0.8, y, 1.1)], 0.03, 'chrome', 6))
        for x in (-0.8, 0.8):
            B.add(tube([(x, y, 0.0), (x, y, 1.1)], 0.04, 'green', 6))
    return 2.6


def museum(B):
    """A museum by the bay (invented): a low glass hall on a raised plinth under a great flat canopy on slender white columns,
    vertical gardens hanging from the canopy's edge, wide steps up to it, its name on the plinth."""
    W, H, D = B.W, B.H, B.D
    B.add(cbox2((-W / 2, 0.0, 0.0), (W / 2, D, 1.2), 0.05, 'concw'))
    for k in range(5):
        B.add(box((-6.0, -0.4 * (k + 1), 0.0), (6.0, -0.4 * k, 1.2 - 0.24 * (k + 1) + 0.24), 'concw'))
    gl = WF((0, 3.0, 0), (1, 0, 0), 'front')
    window(B, gl, -W / 2 + 4.0, W / 2 - 4.0, 1.2, H - 0.5, depth=0.05, fw=0.06, cols=int((W - 8) / 2.4), rows=2, frame='alud', glass='glass3',
           sill='conc', head=None, cheap=True, register=False, seed=71)
    B.add(box((-W / 2 + 4.0, 3.0, 1.2), (W / 2 - 4.0, D - 2.0, H - 0.4), 'interior'))
    B.add(cbox2((-W / 2 - 3.0, -4.0, H), (W / 2 + 3.0, D + 2.0, H + 0.8), 0.1, 'slab'))
    for x in np.linspace(-W / 2 - 1.5, W / 2 + 1.5, 9):
        B.add(tube([(x, -3.0, 1.2), (x, -3.0, H)], 0.18, 'slab', 8))
    rng = np.random.default_rng(31)
    for x in np.arange(-W / 2 - 2.5, W / 2 + 2.5, 1.1):
        L = rng.uniform(2.0, 4.5)
        B.add(blob((x, -3.7, H - L / 2), (0.35, 0.3, L / 2), 'leafd' if rng.random() < 0.5 else 'leaf', 6, 3, int(x * 10) % 97, 0.3))
    mb = MB()
    mb.face([(-5.0, -0.02, 0.3), (5.0, -0.02, 0.3), (5.0, -0.02, 1.0), (-5.0, -0.02, 1.0)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('mi_museum', (co.x + 5.0) / 10.0, (co.z - 0.3) / 0.7, 0.0))
    B.add(mb.bm())
    return H + 0.8


# ================================================================ the bus, the stops, the drugstore
BUS_L, BUS_W, BUS_H = 12.0, 2.6, 3.2


def bus_shell(B):
    """The city bus (invented livery), as the map shows it: the far side with its windows, the roof and its AC pods, the front
    with its raked windscreen and destination sign, the back, the wheels and the inside. Its front is toward +X. (Its near side
    was a separate model the bus mini-game cut away; the mini-games were removed in v128.)"""
    L, Wd, H = BUS_L, BUS_W, BUS_H
    y0, y1 = -Wd / 2, Wd / 2
    zf = 0.35                                   # the floor
    win = [(x, x + 1.45, 1.2, 2.45) for x in np.arange(-L / 2 + 1.0, L / 2 - 2.6, 1.7)]
    door_m = (-0.6, 0.7, zf, 2.75)
    # the far side
    far = WF((0, y1, 0), (-1, 0, 0), 'back')
    wall(B, far, -L / 2, L / 2, H, [(-w[1], -w[0], w[2], w[3]) for w in win], v0=0.18, mat='busw')
    for w in win:
        window(B, far, -w[1], -w[0], w[2], w[3], depth=0.06, fw=0.05, cols=1, frame='black', glass='glass0', sill='black', head=None, cheap=True,
               register=False, seed=int(w[0] * 5) % 91)
    # inside: the far wall's lining, the floor, the ceiling, seats, rails, the cord, the sign, the reader
    B.add(box((-L / 2 + 0.1, y1 - 0.12, zf), (L / 2 - 0.1, y1 - 0.1, 1.15), 'busw'))
    B.add(box((-L / 2 + 0.1, y0 + 0.1, zf - 0.02), (L / 2 - 0.1, y1 - 0.1, zf), 'floorb'))
    B.add(box((-L / 2 + 0.1, y0 + 0.1, H - 0.12), (L / 2 - 0.1, y1 - 0.1, H - 0.1), 'cream2'))
    # the far wheels' housings (the floor is low: the wheels rise into the saloon under a box), no seats over them
    arches = (-L / 2 + 2.3, L / 2 - 3.4)
    for x in arches:
        B.add(cbox2((x - 0.66, y1 - 0.7, zf), (x + 0.66, y1 - 0.1, 1.12), 0.04, 'floorb'))
    for x in np.arange(-L / 2 + 1.2, L / 2 - 2.6, 0.95):
        if door_m[0] - 0.3 < x < door_m[1] + 0.2: continue
        if any(abs(x - a) < 0.85 for a in arches): continue
        B.add(cbox2((x - 0.25, y1 - 0.62, zf + 0.42), (x + 0.25, y1 - 0.14, zf + 0.5), 0.03, 'seat'))
        B.add(cbox2((x - 0.27, y1 - 0.62, zf + 0.5), (x - 0.18, y1 - 0.14, zf + 1.15), 0.03, 'seat'))
        B.add(cbox2((x - 0.08, y1 - 0.45, zf), (x + 0.08, y1 - 0.3, zf + 0.42), 0.02, 'alud'))
    B.add(tube([(-L / 2 + 0.3, y1 - 0.5, 2.25), (L / 2 - 0.3, y1 - 0.5, 2.25)], 0.022, 'grab', 6))
    B.add(tube([(-L / 2 + 0.3, y1 - 0.18, 2.35), (L / 2 - 2.6, y1 - 0.18, 2.35)], 0.006, 'black', 3))
    for x in np.arange(-L / 2 + 1.6, L / 2 - 2.6, 1.9):
        B.add(tube([(x, y1 - 0.68, zf), (x, y1 - 0.68, H - 0.12)], 0.02, 'grab', 6))
    sign = WF((L / 2 - 2.6, 0.0, 0), (0, -1, 0), 'left')
    mb = MB()
    mb.face([(-0.7, 2.62, 0.0), (0.7, 2.62, 0.0), (0.7, 2.9, 0.0), (-0.7, 2.9, 0.0)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('mi_led', (co.x + 0.7) / 1.4, (co.y - 2.62) / 0.28, 0.0))
    put(B, sign, mb.bm())
    B.add(cbox2((L / 2 - 2.55, -0.82, 2.58), (L / 2 - 2.5, 0.82, 2.94), 0.01, 'black'))
    B.add(cbox2((L / 2 - 0.9, y0 + 0.5, zf), (L / 2 - 0.82, y0 + 0.58, 1.15), 0.01, 'alud'))
    B.add(cbox2((L / 2 - 0.95, y0 + 0.44, 1.15), (L / 2 - 0.77, y0 + 0.64, 1.42), 0.02, 'black'))
    B.add(box((L / 2 - 0.94, y0 + 0.43, 1.25), (L / 2 - 0.78, y0 + 0.44, 1.38), 'neonb'))
    # the driver's seat and wheel, behind the front door
    B.add(cbox2((L / 2 - 1.0, y1 - 0.9, zf + 0.4), (L / 2 - 0.5, y1 - 0.3, zf + 1.2), 0.04, 'black'))
    B.add(tube([(L / 2 - 0.35 + 0.22 * math.cos(a), y1 - 0.6 + 0.22 * math.sin(a), 1.5) for a in np.linspace(0, 2 * math.pi, 11)], 0.02, 'black', 3, caps=False))
    # the roof, its AC pods, the front with the windscreen and the destination sign, the back, the skirt and the wheels
    B.add(cbox2((-L / 2, y0, H - 0.05), (L / 2, y1, H + 0.12), 0.08, 'busw'))
    for x in (-L / 2 + 2.0, 1.0):
        B.add(cbox2((x - 1.2, -0.9, H + 0.12), (x + 1.2, 0.9, H + 0.45), 0.1, 'busw'))
    fr = WF((L / 2, 0, 0), (0, 1, 0), 'right')
    wall(B, fr, y0, y1, H, [(y0 + 0.15, y1 - 0.15, 1.0, 2.55)], v0=0.18, mat='busw')
    put(B, fr, fbox((y0 + 0.15, 1.0, -0.15), (y1 - 0.15, 2.55, -0.12), 0.01, 'glassd'))
    mb = MB()
    mb.face([(y0 + 0.3, 2.62, 0.01), (y1 - 0.3, 2.62, 0.01), (y1 - 0.3, 2.95, 0.01), (y0 + 0.3, 2.95, 0.01)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('mi_led', (co.x - y0 - 0.3) / (Wd - 0.6), (co.y - 2.62) / 0.33, 0.0))
    put(B, fr, mb.bm())
    for y in (y0 + 0.35, y1 - 0.35):
        put(B, fr, fbox((y - 0.15, 0.55, 0.0), (y + 0.15, 0.7, 0.05), 0.02, 'lamp'))
    put(B, fr, fbox((y0, 0.18, 0.0), (y1, 0.5, 0.12), 0.03, 'black'))
    bk = WF((-L / 2, 0, 0), (0, -1, 0), 'left')
    wall(B, bk, -y1, -y0, H, [], v0=0.18, mat='busw')
    for y in (-y1 + 0.3, -y0 - 0.3):
        put(B, bk, fbox((y - 0.12, 0.7, 0.0), (y + 0.12, 1.0, 0.04), 0.02, 'red'))
    B.add(box((-L / 2, y0, 0.18), (L / 2, y1, 0.35), 'black'))
    for x in arches:
        bus_wheel(B, x, y1 - 0.15)
    return H + 0.45


def bus_wheel(B, x, y):
    w, _ = lathe([(0.0, -0.15), (0.5, -0.15), (0.52, 0.0), (0.5, 0.15), (0.0, 0.15)], 14, 'tire')
    xform(w, T(x, y, 0.52) @ R(math.pi / 2, 'X')); B.add(w)
    hub, _ = lathe([(0.0, -0.16), (0.28, -0.16), (0.28, 0.16), (0.0, 0.16)], 10, 'alu')
    xform(hub, T(x, y, 0.52) @ R(math.pi / 2, 'X')); B.add(hub)


def sweeper(B):
    """A street sweeper truck working the kerb (invented city livery): a white hopper body with a flat top 1.2 m up (the kid
    rides it), an orange band, the cab at the front with its windscreen and an amber beacon, the two gutter brooms under the
    cab and the pickup broom under the body, the spray bar, the wheels, the chevrons on the back. Its front is toward +X."""
    L, Wd = B.W, B.D
    y0, y1 = -Wd / 2, Wd / 2
    cab = L / 2 - 0.95
    B.add(box((-L / 2, y0 + 0.05, 0.3), (L / 2, y1 - 0.05, 0.45), 'scootd'))
    B.add(cbox2((-L / 2, y0, 0.45), (cab, y1, 1.2), 0.06, 'busw'))
    for y in (y0 - 0.004, y1):
        B.add(box((-L / 2 + 0.04, y, 0.74), (cab - 0.04, y + 0.004, 0.86), 'mango'))
    B.add(cbox2((cab, y0, 0.45), (L / 2, y1, 2.25), 0.08, 'busw'))
    B.add(box((L / 2 - 0.004, y0 + 0.14, 1.32), (L / 2 + 0.006, y1 - 0.14, 2.08), 'glassd'))
    for y in (y0 - 0.006, y1 - 0.002):
        B.add(box((cab + 0.1, y, 1.32), (L / 2 - 0.12, y + 0.008, 2.02), 'glassd'))
        B.add(box((cab + 0.04, y, 0.74), (L / 2 - 0.04, y + 0.008, 0.86), 'mango'))
    B.add(cbox2((L / 2 - 0.62, -0.13, 2.25), (L / 2 - 0.36, 0.13, 2.43), 0.04, 'mango'))
    B.add(box((L / 2 + 0.006, y0 + 0.25, 0.55), (L / 2 + 0.03, y1 - 0.25, 0.75), 'scootd'))
    B.add(tube([(L / 2 + 0.1, y0 + 0.1, 0.36), (L / 2 + 0.1, y1 - 0.1, 0.36)], 0.03, 'alu', 6))
    # the gutter brooms (flat discs of bristles) under the cab's corners, the pickup broom across under the body
    for y in (y0 + 0.25, y1 - 0.25):
        d, _ = lathe([(0.0, 0.0), (0.4, 0.0), (0.42, 0.05), (0.0, 0.07)], 14, 'mango')
        xform(d, T(L / 2 - 0.25, y, 0.03)); B.add(d)
        hub, _ = lathe([(0.0, 0.07), (0.1, 0.07), (0.08, 0.3), (0.0, 0.3)], 8, 'scootd')
        xform(hub, T(L / 2 - 0.25, y, 0.0)); B.add(hub)
    B.add(tube([(-0.35, y0 + 0.15, 0.22), (-0.35, y1 - 0.15, 0.22)], 0.2, 'scootd', 10))
    for x in (-L / 2 + 0.55, L / 2 - 0.55):
        for y in (y0 + 0.12, y1 - 0.12):
            w, _ = lathe([(0.0, -0.12), (0.36, -0.12), (0.38, 0.0), (0.36, 0.12), (0.0, 0.12)], 14, 'tire')
            xform(w, T(x, y, 0.38) @ R(math.pi / 2, 'X')); B.add(w)
            hub, _ = lathe([(0.0, -0.13), (0.2, -0.13), (0.2, 0.13), (0.0, 0.13)], 10, 'alu')
            xform(hub, T(x, y, 0.38) @ R(math.pi / 2, 'X')); B.add(hub)
    for k in range(4):
        B.add(box((-L / 2 - 0.006, y0 + 0.15 + k * 0.42, 0.5), (-L / 2, y0 + 0.36 + k * 0.42, 0.95), 'mango' if k % 2 == 0 else 'scootd'))
    return 2.43


def bus(B): return bus_shell(B)


def stop_sign(B):
    """A bus stop's sign: a tall post with the route plate (route number, the stop's direction), a schedule box."""
    B.add(tube([(0, 0, 0.0), (0, 0, 3.0)], 0.04, 'galvw', 6))
    mb = MB()
    mb.face([(-0.32, -0.05, 2.0), (0.32, -0.05, 2.0), (0.32, -0.05, 2.85), (-0.32, -0.05, 2.85)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('mi_route', (co.x + 0.32) / 0.64, (co.z - 2.0) / 0.85, 0.0))
    B.add(mb.bm())
    B.add(cbox2((-0.18, -0.08, 1.2), (0.18, 0.0, 1.6), 0.02, 'alu'))
    return 3.0


def pharmacy(B):
    """The corner drugstore on the route to school (invented): a white-and-teal one-storey front, a long glass shopfront with
    its posters, the name in a lit sign band, a green cross, a newspaper box and a bench outside."""
    W, H, D = B.W, B.H, B.D
    pp = 0.8
    sf = (-W / 2 + 0.6, W / 2 - 2.0, 0.3, 2.7)
    dr = (W / 2 - 1.8, W / 2 - 0.5, 0.0, 2.6)
    F, Rt, Bk, Lf = plain_walls(B, H + pp, None, fronts=[sf, dr])
    flat_top(B, H, pp)
    shop_front_glass(B, F, *sf, seed=81, cols=5)
    shop_room(B, sf[0], sf[1], sf[2], sf[3], 2.5)
    door(B, F, *dr, mat='alu', glass=0.85, panels=((1, 1),), name='Door')
    B.add(cbox2((-W / 2, -0.25, H - 0.2), (W / 2, 0.0, H + pp - 0.1), 0.02, 'aquad'))
    decal(B, F, -W / 2 + 0.5, W / 2 - 2.4, H - 0.12, H + pp - 0.18, 0.27, 'mi_pharmacy')
    gc = WF((W / 2 - 1.2, -0.3, 0), (1, 0, 0), 'front')
    put(B, gc, fbox((-0.15, H + 0.05, -0.02), (0.15, H + 0.75, 0.04), 0.01, 'green'))
    put(B, gc, fbox((-0.35, H + 0.25, -0.02), (0.35, H + 0.55, 0.04), 0.01, 'green'))
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=2.7, length=0.5, k=0.3)
    return H + pp + 0.2


# ================================================================ the kit's tiles
def _mural(dr, w, h, k, seed, kind):
    """An invented mural: big tropical flowers, a wave, palms, birds and a rooster, in strong flat colours with dark outlines,
    the paint weathered at its foot."""
    rng = np.random.default_rng(seed)
    bands = [(0.98, 0.78, 0.30), (0.96, 0.46, 0.38), (0.30, 0.70, 0.74), (0.16, 0.36, 0.66), (0.98, 0.62, 0.72)]
    for i in range(6):
        y0 = h * i / 6; dr.rectangle([0, y0, w, y0 + h / 6 + 1], fill=_c(bands[(i + seed) % len(bands)]))
    # a sun
    cx, cy, r = w * rng.uniform(0.6, 0.85), h * 0.28, min(w, h) * 0.18
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=_c((0.99, 0.86, 0.36)), outline=_c((0.2, 0.14, 0.12)), width=max(2, int(4 * k)))
    # waves
    for j in range(4):
        y = h * (0.62 + 0.08 * j)
        pts = [(x, y + h * 0.03 * math.sin(x / w * 10 + j)) for x in np.linspace(0, w, 40)]
        dr.line(pts, fill=_c((0.12, 0.40, 0.66) if j % 2 else (0.95, 0.97, 1.0)), width=max(3, int(h * 0.025)))
    # big flowers (hibiscus)
    for f in range(5 if kind != 2 else 3):
        fx, fy, fr = w * rng.uniform(0.08, 0.92), h * rng.uniform(0.15, 0.85), min(w, h) * rng.uniform(0.07, 0.13)
        col = [(0.92, 0.18, 0.30), (0.98, 0.52, 0.16), (0.96, 0.36, 0.58)][f % 3]
        for p in range(5):
            a = p * 2 * math.pi / 5
            px, py = fx + math.cos(a) * fr * 0.6, fy + math.sin(a) * fr * 0.6
            dr.ellipse([px - fr * 0.55, py - fr * 0.55, px + fr * 0.55, py + fr * 0.55], fill=_c(col), outline=_c((0.25, 0.08, 0.1)), width=max(1, int(2 * k)))
        dr.ellipse([fx - fr * 0.18, fy - fr * 0.18, fx + fr * 0.18, fy + fr * 0.18], fill=_c((0.99, 0.86, 0.3)))
    # palms
    for p in range(2):
        px = w * (0.12 + 0.7 * p) + rng.uniform(-20, 20) * k
        dr.line([(px, h), (px + w * 0.03, h * 0.35)], fill=_c((0.35, 0.24, 0.16)), width=max(4, int(w * 0.012)))
        for a in np.linspace(-2.6, -0.5, 6):
            dr.line([(px + w * 0.03, h * 0.35), (px + w * 0.03 + math.cos(a) * w * 0.09, h * 0.35 - math.sin(a) * h * 0.1 + h * 0.05)],
                    fill=_c((0.12, 0.45, 0.22)), width=max(3, int(w * 0.01)))
    if kind == 1:
        # a rooster in profile
        rx, ry, rs = w * 0.32, h * 0.5, min(w, h) * 0.16
        dr.ellipse([rx - rs, ry - rs * 0.7, rx + rs, ry + rs * 0.7], fill=_c((0.80, 0.22, 0.12)), outline=_c((0.15, 0.08, 0.06)), width=max(2, int(3 * k)))
        dr.ellipse([rx + rs * 0.6, ry - rs * 1.2, rx + rs * 1.2, ry - rs * 0.6], fill=_c((0.80, 0.22, 0.12)), outline=_c((0.15, 0.08, 0.06)), width=max(2, int(3 * k)))
        dr.polygon([(rx + rs * 0.75, ry - rs * 1.2), (rx + rs * 0.9, ry - rs * 1.55), (rx + rs * 1.05, ry - rs * 1.2)], fill=_c((0.9, 0.1, 0.1)))
        dr.polygon([(rx + rs * 1.2, ry - rs * 0.95), (rx + rs * 1.45, ry - rs * 0.85), (rx + rs * 1.2, ry - rs * 0.75)], fill=_c((0.99, 0.76, 0.2)))
        for a in (2.4, 2.7, 3.0):
            dr.line([(rx - rs * 0.8, ry - rs * 0.2), (rx - rs * 0.8 + math.cos(a) * rs * 1.3, ry - rs * 0.2 - math.sin(a) * rs * 1.6 - rs * 0.6)],
                    fill=_c((0.06, 0.3, 0.24)), width=max(4, int(rs * 0.18)))
    # birds
    for b in range(4):
        bx, by = w * rng.uniform(0.1, 0.9), h * rng.uniform(0.08, 0.3)
        s = min(w, h) * 0.03
        dr.line([(bx - s, by), (bx, by + s * 0.5), (bx + s, by)], fill=_c((0.12, 0.12, 0.16)), width=max(2, int(2 * k)))
    # weathering at the foot
    for _ in range(int(80 * k)):
        x = rng.uniform(0, w); y = h - rng.uniform(0, h * 0.12)
        s = rng.uniform(2, 8) * k
        dr.ellipse([x - s, y - s, x + s, y + s], fill=_c((0.86, 0.84, 0.80)))


def t_mural1(dr, w, h, k): _mural(dr, w, h, k, 3, 1)
def t_mural2(dr, w, h, k): _mural(dr, w, h, k, 7, 0)
def t_mural3(dr, w, h, k): _mural(dr, w, h, k, 11, 2)


def t_shopname(s, ink, bg, paths=None, frac=0.6, border=None):
    def f(dr, w, h, k):
        dr.rectangle([0, 0, w, h], fill=_c(bg))
        if border: dr.rectangle([h * 0.06, h * 0.08, w - h * 0.06, h * 0.92], outline=_c(border), width=max(2, int(h * 0.04)))
        _label(dr, w, h, s, paths or SCRIPT, frac, ink, maxw=0.9)
    return f


def t_cafemenu(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.12, 0.13, 0.12)))
    _label(dr, w, h, 'MENÚ', BOLD, 0.1, (0.98, 0.86, 0.5), cy=0.09)
    for i, (item, p) in enumerate((('Cafecito', '1.50'), ('Colada', '2.00'), ('Cortadito', '2.50'), ('Café con leche', '3.00'),
                                   ('Pastelito', '1.75'), ('Croqueta', '1.25'))):
        _label(dr, w, h, item, SG.LATIN_SOFT, 0.065, WHITE, cx=0.38, cy=0.22 + 0.13 * i, maxw=0.62)
        _label(dr, w, h, '$' + p, SG.LATIN_SOFT, 0.065, WHITE, cx=0.85, cy=0.22 + 0.13 * i, maxw=0.25)


def t_mesh(dr, w, h, k):
    """The construction fence's banner: a sky, a rendering of the tower to come (invented), the developer's tagline."""
    for y in range(int(h)):
        t = y / h
        dr.line([(0, y), (w, y)], fill=_c((0.40 + 0.4 * t, 0.62 + 0.25 * t, 0.86 + 0.08 * t)))
    for i in range(5):
        x0 = w * (0.08 + i * 0.09); hh = h * (0.5 + 0.08 * (i % 3))
        dr.rectangle([x0, h - hh, x0 + w * 0.06, h], fill=_c((0.62, 0.74, 0.82)))
    tx = w * 0.62
    dr.rectangle([tx, h * 0.05, tx + w * 0.12, h], fill=_c((0.80, 0.90, 0.95)))
    for y in np.arange(h * 0.1, h, h * 0.06):
        dr.line([(tx, y), (tx + w * 0.12, y)], fill=_c(WHITE), width=max(1, int(2 * k)))
    _label(dr, w, h, 'BAYSIDE ONE', BOLD, 0.2, (0.10, 0.20, 0.38), cx=0.32, cy=0.3, maxw=0.45, spacing=int(h * 0.02))
    _label(dr, w, h, 'Living above the bay - coming soon', SG.LATIN_SOFT, 0.1, (0.10, 0.20, 0.38), cx=0.32, cy=0.55, maxw=0.5)


def t_led(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.05, 0.05, 0.05)))
    _label(dr, w, h, '8  BRICKELL', BOLD, 0.66, (1.0, 0.62, 0.12), maxw=0.92, spacing=int(h * 0.08))


def t_route(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.10, 0.30, 0.60)))
    dr.rectangle([w * 0.06, h * 0.05, w * 0.94, h * 0.95], outline=_c(WHITE), width=max(2, int(3 * k)))
    _label(dr, w, h, 'BUS', BOLD, 0.16, WHITE, cy=0.17)
    dr.ellipse([w * 0.28, h * 0.32, w * 0.72, h * 0.32 + w * 0.44], fill=_c((0.96, 0.56, 0.20)))
    _label(dr, w, h, '8', BOLD, 0.2, WHITE, cy=0.32 + w * 0.22 / h)
    _label(dr, w, h, 'to Brickell', SG.LATIN_SOFT, 0.09, WHITE, cy=0.86)


def t_tower(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.92, 0.92, 0.90)))
    _label(dr, w, h, 'THE PALMS', BOLD, 0.3, (0.32, 0.34, 0.38), maxw=0.9, spacing=int(h * 0.04))


def t_containers(dr, w, h, k):
    cols = [(0.62, 0.20, 0.16), (0.16, 0.34, 0.62), (0.90, 0.90, 0.86), (0.24, 0.50, 0.34)]
    for i, c in enumerate(cols):
        x0 = w * i / 4
        dr.rectangle([x0, 0, x0 + w / 4, h], fill=_c(c))
        for x in np.arange(x0 + 4 * k, x0 + w / 4, 6 * k):
            dr.line([(x, 0), (x, h)], fill=_c(tuple(v * 0.8 for v in c)), width=max(1, int(1.5 * k)))
        for _ in range(6):
            sx = x0 + np.random.default_rng(i * 7).uniform(0, w / 4)
            dr.line([(sx, h * 0.1), (sx + 2 * k, h * 0.7)], fill=_c((0.45, 0.24, 0.14)), width=max(1, int(2 * k)))


def t_domino(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.97, 0.96, 0.92)))
    for x, y in ((0.3, 0.3), (0.7, 0.7), (0.5, 0.5)):
        dr.ellipse([w * x - 4 * k, h * y - 4 * k, w * x + 4 * k, h * y + 4 * k], fill=_c((0.1, 0.1, 0.1)))


def t_shutter(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.74, 0.76, 0.77)))
    for y in np.arange(0, h, 8 * k):
        dr.line([(0, y), (w, y)], fill=_c((0.56, 0.58, 0.6)), width=max(1, int(2 * k)))


def t_hotel(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.20, 0.62, 0.64)))
    for i, ch in enumerate('HOTEL'):
        _label(dr, w, h, ch, BOLD, 0.15, WHITE, cy=0.12 + 0.19 * i)


def paint(img, put):
    """The Miami kit's tiles (kit_buildings_atlas.paint calls this through EXTRA)."""
    pp = SG.put_pil
    PLAY.paint(img, pp)
    pp(img, 'fl_glassblock', FL.t_glassblock, (0.84, 0.86, 0.84))
    pp(img, 'fl_breeze', FL.t_breeze, (0.93, 0.93, 0.91))
    pp(img, 'fl_chain', FL.t_chain, (0.5, 0.54, 0.5))
    pp(img, 'fl_gate', FL.t_gate, (0.16, 0.17, 0.19))
    pp(img, 'sg_bus', FL.t_bus, WHITE)
    pp(img, 'mi_ventanita', t_shopname('Café La Esquina', (0.99, 0.96, 0.88), (0.70, 0.12, 0.14), frac=0.66, border=(0.99, 0.86, 0.5)),
       (0.70, 0.12, 0.14))
    pp(img, 'mi_cafemenu', t_cafemenu, (0.12, 0.13, 0.12))
    pp(img, 'mi_tabacos', t_shopname('Tabacos El Faro', (0.98, 0.90, 0.62), (0.36, 0.20, 0.12), frac=0.6, border=(0.98, 0.90, 0.62)),
       (0.36, 0.20, 0.12))
    pp(img, 'mi_fruteria', t_shopname('Frutería Los Primos', (0.98, 0.96, 0.88), (0.20, 0.52, 0.30), paths=BOLD, frac=0.5), (0.20, 0.52, 0.30))
    pp(img, 'mi_mural1', t_mural1, (0.98, 0.78, 0.30))
    pp(img, 'mi_mural2', t_mural2, (0.30, 0.70, 0.74))
    pp(img, 'mi_mural3', t_mural3, (0.96, 0.46, 0.38))
    pp(img, 'mi_mesh', t_mesh, (0.60, 0.75, 0.90))
    pp(img, 'mi_kiosk', t_shopname('Bay Brew Coffee', WHITE, (0.14, 0.50, 0.53), paths=BOLD, frac=0.55), (0.14, 0.50, 0.53))
    pp(img, 'mi_pharmacy', t_shopname('Corner Pharmacy', WHITE, (0.10, 0.48, 0.50), paths=BOLD, frac=0.55), (0.10, 0.48, 0.50))
    pp(img, 'mi_led', t_led, (0.05, 0.05, 0.05))
    pp(img, 'mi_route', t_route, (0.10, 0.30, 0.60))
    pp(img, 'mi_deco1', t_shopname('Flagler Shoes', (0.10, 0.34, 0.50), (0.97, 0.94, 0.86), frac=0.62), (0.97, 0.94, 0.86))
    pp(img, 'mi_deco2', t_shopname('Miami Optical', (0.70, 0.12, 0.14), (0.97, 0.94, 0.86), paths=BOLD, frac=0.52), (0.97, 0.94, 0.86))
    pp(img, 'mi_hotel', t_hotel, (0.20, 0.62, 0.64))
    pp(img, 'mi_museum', t_shopname('BAYSIDE MUSEUM OF ART', (0.20, 0.22, 0.26), (0.92, 0.92, 0.90), paths=BOLD, frac=0.5), (0.92, 0.92, 0.90))
    pp(img, 'mi_containers', t_containers, (0.62, 0.20, 0.16))
    pp(img, 'mi_tower', t_tower, (0.92, 0.92, 0.90))
    pp(img, 'mi_towerb', t_tower, (0.92, 0.92, 0.90))
    pp(img, 'mi_domino', t_domino, (0.97, 0.96, 0.92))
    pp(img, 'mi_scoot', t_shopname('ZIP', WHITE, (0.16, 0.66, 0.60), paths=BOLD, frac=0.7), (0.16, 0.66, 0.60))
    pp(img, 'mi_shutter', t_shutter, (0.74, 0.76, 0.77))


# ================================================================ the kit's rows
def pal_mia(pal):
    """The Miami rows of the kit's SPECS (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps)."""
    prop = {'ppm': 12}
    shop = {'wall': 'stucco', 'ppm': 64}
    big = {'wall': 'render', 'ppm': 24}
    tw = {'wall': 'render', 'ppm': 6}
    gl = pal
    return [
        # Little Havana
        ('VentanitaMIA', 9.0, 3.4, 9.0, 0.0, ventanita,
         gl((0.98, 0.86, 0.52), (0.80, 0.16, 0.18), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.93)), 4.8, shop, {}),
        ('TabaqueriaMIA', 8.0, 6.3, 9.0, 0.0, tabaqueria,
         gl((0.95, 0.56, 0.46), (0.36, 0.22, 0.14), (0.56, 0.55, 0.54), trim=(0.97, 0.95, 0.90)), 8.0, shop, {}),
        ('FruteriaMIA', 8.5, 3.6, 8.0, 0.0, fruteria,
         gl((0.66, 0.86, 0.80), (0.20, 0.52, 0.30), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.93)), 5.0, shop, {}),
        ('MuralWallMIA', 10.0, 6.5, 6.0, 0.0, mural_wall,
         gl((0.92, 0.88, 0.80), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 7.4, {'wall': 'render', 'ppm': 48}, {}),
        ('MuralShedMIA', 12.0, 4.2, 10.0, 0.0, mural_wall2,
         gl((0.90, 0.88, 0.84), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 5.0, {'wall': 'render', 'ppm': 40}, {}),
        ('DominoParkMIA', 8.0, 2.9, 4.0, 0.0, domino_park, gl((0.95, 0.95, 0.93), (0.42, 0.78, 0.78), (0.56, 0.55, 0.54)), 3.6, prop, {}),
        ('DominoTableMIA', 1.3, 0.8, 1.3, 0.0, domino_table, gl((0.85, 0.84, 0.80), (0.16, 0.42, 0.30), (0.56, 0.55, 0.54)), 1.0, prop, {}),
        ('FruitCartMIA', 2.0, 2.4, 1.2, 0.0, fruit_cart, gl((0.12, 0.30, 0.62), (0.96, 0.84, 0.32), (0.56, 0.55, 0.54)), 2.6, prop, {}),
        ('RoosterMIA', 0.7, 0.6, 0.3, 0.0, rooster, gl((0.62, 0.20, 0.12), (0.06, 0.22, 0.18), (0.56, 0.55, 0.54)), 0.8, prop, {}),
        ('HenMIA', 0.6, 0.5, 0.3, 0.0, hen, gl((0.74, 0.48, 0.26), (0.06, 0.22, 0.18), (0.56, 0.55, 0.54)), 0.8, prop, {}),
        ('IguanaMIA', 1.3, 0.2, 0.4, 0.0, iguana, gl((0.40, 0.62, 0.26), (0.06, 0.22, 0.18), (0.56, 0.55, 0.54)), 0.4, prop, {}),
        ('PelicanPostMIA', 0.8, 2.7, 0.5, 0.0, pelican_post, gl((0.62, 0.58, 0.52), (0.52, 0.46, 0.40), (0.56, 0.55, 0.54)), 2.8, prop, {}),
        ('ScooterMIA', 1.2, 0.4, 0.4, 0.0, scooter, gl((0.16, 0.66, 0.60), (0.13, 0.14, 0.15), (0.56, 0.55, 0.54)), 0.6, prop, {}),
        ('ScooterUpMIA', 1.2, 1.1, 0.6, 0.0, scooter_up, gl((0.16, 0.66, 0.60), (0.13, 0.14, 0.15), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        # Brickell and downtown
        ('CondoTowerMIA', 22.0, 84.0, 22.0, 0.0, condo_tower, gl((0.92, 0.92, 0.90), (0.42, 0.62, 0.74), (0.56, 0.55, 0.54)), 89.0, tw, {}),
        ('OfficeTowerMIA', 24.0, 66.0, 24.0, 0.0, office_tower, gl((0.86, 0.87, 0.88), (0.22, 0.32, 0.40), (0.56, 0.55, 0.54)), 71.0, tw, {}),
        ('CondoTower2MIA', 18.0, 52.0, 18.0, 0.0, condo_tower2, gl((0.95, 0.94, 0.90), (0.50, 0.70, 0.72), (0.56, 0.55, 0.54)), 53.0, tw, {}),
        ('TowerPodiumMIA', 24.0, 7.0, 10.0, 0.0, tower_podium, gl((0.94, 0.94, 0.92), (0.30, 0.31, 0.33), (0.56, 0.55, 0.54)), 8.0, big, {}),
        ('SiteFenceMIA', 8.0, 2.4, 0.3, 0.0, site_fence, gl((0.74, 0.76, 0.77), (0.96, 0.58, 0.20), (0.56, 0.55, 0.54)), 2.6, {'ppm': 64}, {}),
        ('CoffeeKioskMIA', 2.4, 2.6, 1.6, 0.0, coffee_kiosk, gl((0.86, 0.87, 0.89), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54)), 2.8, {'ppm': 48}, {}),
        ('DecoArcadeMIA', 12.0, 9.6, 12.0, 0.0, deco_block_a,
         gl((0.97, 0.93, 0.84), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 12.6, {'wall': 'stucco', 'ppm': 40}, {}),
        ('DecoArcade2MIA', 10.0, 6.3, 12.0, 0.0, deco_block_b,
         gl((0.97, 0.76, 0.80), (0.80, 0.16, 0.18), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 9.0, {'wall': 'stucco', 'ppm': 40}, {}),
        ('MedRevivalMIA', 14.0, 6.0, 10.0, 2.0, med_revival,
         gl((0.97, 0.92, 0.82), (0.36, 0.22, 0.14), (0.78, 0.40, 0.28), trim=(0.96, 0.93, 0.86)), 10.6, {'wall': 'stucco', 'ppm': 36}, {}),
        ('SpanishTowerMIA', 14.0, 48.0, 14.0, 0.0, spanish_tower, gl((0.96, 0.92, 0.82), (0.36, 0.22, 0.14), (0.78, 0.40, 0.28)), 54.0, tw, {}),
        # the river and the bay
        ('FreighterMIA', 30.0, 3.0, 7.0, 0.0, freighter, gl((0.62, 0.18, 0.16), (0.56, 0.30, 0.20), (0.56, 0.55, 0.54)), 11.0, {'ppm': 12}, {}),
        ('TugMIA', 10.0, 1.8, 4.0, 0.0, tug, gl((0.62, 0.18, 0.16), (0.12, 0.12, 0.13), (0.56, 0.55, 0.54)), 6.0, {'ppm': 16}, {}),
        ('FishingBoatMIA', 5.6, 0.95, 2.1, 0.0, fishing_boat, gl((0.95, 0.95, 0.93), (0.12, 0.30, 0.62), (0.56, 0.55, 0.54)), 4.5, {'ppm': 24}, {}),
        ('LineCoilMIA', 1.0, 0.3, 0.6, 0.0, line_coil, gl((0.82, 0.74, 0.58), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 0.4, prop, {}),
        ('BollardMIA', 0.5, 0.52, 0.5, 0.0, bollard_mia, gl((0.14, 0.14, 0.15), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 0.6, prop, {}),
        ('RiverRailMIA', 4.0, 1.12, 0.2, 0.0, river_rail, gl((0.74, 0.76, 0.77), (0.70, 0.50, 0.33), (0.56, 0.55, 0.54)), 1.2, prop, {}),
        ('BayRailMIA', 4.0, 1.0, 0.3, 0.0, bay_rail, gl((0.86, 0.85, 0.82), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 1.1, prop, {}),
        ('CruiseShipMIA', 120.0, 9.0, 18.0, 0.0, cruise_ship, gl((0.95, 0.95, 0.93), (0.12, 0.30, 0.62), (0.56, 0.55, 0.54)), 31.0, {'ppm': 2}, {}),
        # the Underline and Museum Park
        ('GuidewayMIA', 30.0, 9.0, 3.4, 0.0, guideway, gl((0.86, 0.85, 0.82), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 11.2, {'ppm': 10}, {}),
        ('FitnessBarsMIA', 3.0, 2.6, 1.6, 0.0, fitness_bars, gl((0.36, 0.60, 0.30), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 2.8, prop, {}),
        ('MuseumMIA', 40.0, 9.0, 18.0, 0.0, museum, gl((0.92, 0.92, 0.90), (0.6, 0.6, 0.6), (0.56, 0.55, 0.54)), 10.0, {'ppm': 12}, {}),
        # the trip: the bus, a stop's sign, the drugstore
        ('BusMIA', BUS_L, BUS_H, BUS_W, 0.0, bus, gl((0.95, 0.95, 0.93), (0.98, 0.78, 0.18), (0.56, 0.55, 0.54)), 3.8, {'ppm': 32}, {}),
        ('SweeperMIA', 3.4, 2.4, 1.9, 0.0, sweeper, gl((0.95, 0.95, 0.93), (0.98, 0.62, 0.18), (0.56, 0.55, 0.54)), 2.5, {'ppm': 24}, {}),
        ('StopSignMIA', 0.7, 3.0, 0.2, 0.0, stop_sign, gl((0.74, 0.76, 0.77), (0.10, 0.30, 0.60), (0.56, 0.55, 0.54)), 3.2, prop, {}),
        ('PharmacyMIA', 11.0, 3.6, 9.0, 0.0, pharmacy,
         gl((0.97, 0.97, 0.95), (0.14, 0.50, 0.53), (0.56, 0.55, 0.54), trim=(0.97, 0.96, 0.94)), 5.0, shop, {}),
    ] + PLAY.rows(gl, prop)


# the play pieces (kit_buildings_mia_play.py: imported last, as it builds on this module's helpers)
import kit_buildings_mia_play as PLAY
TILES += PLAY.TILES
