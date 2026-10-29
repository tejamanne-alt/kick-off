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
# the origin, for the facing check), Door*, Window.N (glass centres), Lamp*, plus model extras.
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


# ---------------------------------------------------------------- shared house bits
def attic_vent(B, wf, x, y, r=0.3):
    """A round louvred vent on a gable."""
    rb, _ = lathe([(r, 0.0), (r, 0.05), (r * 0.92, 0.07), (r * 0.8, 0.07), (r * 0.78, 0.04)], 12, 'trim', phase=0.5)
    xform(rb, T(x, y, 0)); put(B, wf, rb)
    d, tags = lathe([(r * 0.79, 0.03), (0, 0.03)], 12, 'tex', phase=0.5)
    uv_fn(d, list(d.faces), 'vent', lambda co: (0.5 + co.x / (2 * r), 0.5 + co.y / (2 * r)), 0.0)
    xform(d, T(x, y, 0)); put(B, wf, d)


def door_hood(B, wf, xc, w, z_eave, rise, depth=0.85, brackets='woodc'):
    """A little tiled gable hood over a door, on two knee brackets (front wall only)."""
    p = wf.P(xc, 0, 0)
    pitched(B, 'y', p.x - w / 2, p.x + w / 2, -depth, -0.02, z_eave, rise, t=0.12, row=0.2, lip=0.03, mat='roofp',
            barge=(True, False), feat=False, over=0.03, barge_w=0.16)
    # the hood's gable infill and brackets
    mb = MB()
    tri = [(xc - w / 2 + 0.1, z_eave + 0.06), (xc, z_eave + rise - 0.02), (xc + w / 2 - 0.1, z_eave + 0.06)]
    mb.face([(x, y, depth - 0.04) for x, y in tri], 'trimw', (0, 0, 1), 0.92)
    put(B, wf, mb.bm())
    for sx in (-1, 1):
        x = xc + sx * (w / 2 - 0.16)
        prof = [(0.0, -0.55), (0.08, -0.55), (0.08, -0.16), (depth - 0.08, 0.0), (depth - 0.08, 0.06), (0.0, 0.06)]
        b = extrude_poly(prof, 0.08, brackets)
        xform(b, T(x + 0.04, z_eave, 0) @ R(-PI / 2, 'Y'))
        put(B, wf, b)
    a0, _ = wf.ab(xc - w / 2, 0); a1, _ = wf.ab(xc + w / 2, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z_eave - 0.02, length=0.55, k=0.55)


def gable_gutters(B, a0, a1, r0, r1, zg, pipe_y=0.3, pipe_side=1, pipe_to=None):
    """Gutters along both side eaves of a roof whose ridge runs along Y, and one downpipe."""
    eave_gutter(B, [(a1 + 0.045, r0), (a1 + 0.045, r1)], zg)
    eave_gutter(B, [(a0 - 0.045, r1), (a0 - 0.045, r0)], zg)
    xg = (a1 + 0.045 + 0.07) if pipe_side > 0 else (a0 - 0.045 - 0.07)
    xw = (B.W / 2 + 0.075) if pipe_side > 0 else (-B.W / 2 - 0.075)
    zt = zg - 0.1
    pts = [(xg, pipe_y, zt), (xg, pipe_y, zt - 0.15), (xw, pipe_y, zt - 0.45), (xw, pipe_y, 0.32), (xw + 0.12 * pipe_side, pipe_y, 0.12)]
    downpipe(B, pts, brackets=[(xw, pipe_y, z) for z in np.arange(0.9, zt - 0.6, 1.7)])


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
    # roof
    e = 0.38
    a0, a1 = -W / 2 - e, W / 2 + e
    z0 = H - e * k
    top = pitched(B, 'y', a0, a1, -0.42, D + 0.42, z0, (W / 2 + e) * k, t=t)
    gable_gutters(B, a0, a1, -0.47, D + 0.47, z0 - 0.04, pipe_y=0.3, pipe_side=1)
    chimney(B, 1.7, D - 1.9, H, apex + 0.55, pots=2)
    attic_vent(B, F, 0.0, H + 1.05, 0.3)
    # front door: steps, a tiled hood, a lantern, pots
    door(B, F, *door_o, glass=0.32, panels=((2, 2),), name='Door')
    steps(B, F, door_o[0] - 0.12, door_o[1] + 0.12, [0.30, 0.15])
    door_hood(B, F, (door_o[0] + door_o[1]) / 2, 1.75, 2.66, 0.44)
    lantern(B, F, -1.5, 1.95)
    pot(B, (-1.2, -0.42, 0), 0.19, 0.3, 'pot', 'flowers', seed=1)
    pot(B, (-3.22, -0.75, 0), 0.17, 0.34, 'pot3', 'tall', seed=2, scale=0.9)
    meter_box(B, F, -1.0, 0.9)
    # windows: the ground window with a flower box, upstairs with casings and shutters
    window(B, F, *win_g, cols=3, transom=0.72, planter='accent', glass='glass1', seed=3, head='key')
    for kk, wo in enumerate(win_u):
        window(B, F, *wo, cols=2, head=None, casing=True, shutters='accent', planter='pot', glass=('glass2', 'glass1')[kk], seed=4 + kk)
    window(B, Rt, 2.7, 3.9, 1.0, 2.2, cols=2, glass='glass0', seed=6, cheap=True)
    window(B, Rt, 2.9, 4.0, 3.85, 5.0, cols=2, head=None, casing=True, glass='glass2', seed=7)
    window(B, Lf, -3.9, -2.7, 1.0, 2.2, cols=2, glass='glass0', seed=8, cheap=True, register=False)
    window(B, Lf, -4.0, -2.9, 3.85, 5.0, cols=2, head=None, casing=True, glass='glass1', seed=9, register=False)
    # side: an AC unit on a pad and a vent
    B.add(cbox2((W / 2 + 0.05, 4.7, 0.0), (W / 2 + 0.5, 5.8, 0.1), 0.02, 'conc'))
    ac_unit(B, Rt, 5.25, 0.1, 0.0, w=0.9, h=0.62, d=0.36, brackets=False)
    vent(B, Rt, 1.2, 2.5, 0.26)
    B.feat('front', 'patch', a=-3.0, b=1.3, w=0.32, h=0.22)
    B.feat('front', 'patch', a=3.1, b=0.75, w=0.28, h=0.18)
    B.feat('right', 'patch', a=6.4, b=2.6, w=0.3, h=0.2)
    return top + 0.11


# ---------------------------------------------------------------- the kit
SPECS = [
    # name, W, H, D, RH, builder, palette, map top, styles
    ('HouseGable', 7.0, 6.0, 7.0, 2.6, house_gable,
     pal((0.95, 0.90, 0.80), (0.46, 0.60, 0.53), (0.75, 0.41, 0.30)), 9.4, {}),
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
    for name, W, H, D, RH, fn, p, mtop, st in specs:
        fr = 40 if W <= 11 else (30 if W <= 14 else 26)
        sd = 22
        e = {'front': (-W / 2 - 0.7, W / 2 + 0.7, 0.0, mtop), 'right': (-0.7, D + 0.7, 0.0, mtop),
             'left': (-0.7, D + 0.7, 0.0, mtop), 'roof': (-W / 2 - 0.8, W / 2 + 0.8, -1.0, D + 0.8)}
        exts[name] = e
        for mp, (a0, a1, b0, b1) in e.items():
            ppm = fr if mp == 'front' else sd
            maps.append((name + '.' + mp, int(math.ceil((a1 - a0) * ppm)), int(math.ceil((b1 - b0) * ppm))))
    used = allocate(bottom, maps)
    print('atlas rows used', used, 'of', AT - 128 - 12)
    buildings = []
    for name, W, H, D, RH, fn, p, mtop, st in specs:
        B = Bld(name, W, H, D, RH, p)
        B.maps = exts[name]; B.style = dict(st)
        B.total = fn(B)
        B.prof_done = dict(B.prof)
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
        for i, l in enumerate(B.lamps): K.attach(ob, l['name'] if l['name'] != 'Lamp' else 'Lamp.%d' % i, l['center'])
        for nm, loc in B.attach: K.attach(ob, nm, loc)
        parts = {1: s2l(B.pal['wall']), 2: s2l(B.pal['accent']), 3: s2l(B.pal['roof'])}
        man.add(ob, parts=parts, footprint={'width': B.W, 'wall': B.H, 'depth': B.D, 'roof': B.RH},
                doors=B.doors, windows=B.windows, lamps=B.lamps)
        print(B.name, 'tris', K.tree_tris(ob))
        if B.prof: print('  ', sorted(B.prof.items(), key=lambda kv: -kv[1]))
        K.export_model(ob, os.path.join(OUT, B.name + '.fbx'))
    man.save(os.path.join(OUT, 'Buildings.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Buildings.blend'))
    print('done', OUT)


main()
