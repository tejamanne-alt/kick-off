# The STREET asset kit for Dribble To School: original stylized street furniture and small props,
# modelled in Blender by script (read docs/ART_DIRECTION.md first).
#   blenv/bin/python kit_street.py -- /abs/outdir [--only A,B,C]
# Writes into outdir: one <Model>.fbx per model, StreetAtlas.png, Street.json (the manifest) and
# Street.blend (for review_kit.py). Modules:
#   kit_street_geo.py    bmesh primitives (rounded boxes, lathes, sweeps) and UV helpers
#   kit_street_atlas.py  the atlas layout and the painted weathering maps (concrete, paint, wood...)
#   kit_street_paint.py  painted details: block wall, hoarding graphics, stripes, signs, icons
#   kit_street_build.py  the palette and assembly: normals, baked shading and AO, UVs, recolour parts
#   kit_street_m1/m2/m3/m4.py  the models
# Conventions: metres, Z up, front faces -Y, origin at the base centre on the ground (wall-mounted
# items: the back centre on the wall plane y = 0; the awning: its wall attachment). One material
# (vertex colour x StreetAtlas.png). UV2.x is the recolour part: 1 main paint, 2 secondary (fruit
# or flowers), 0 fixed; the manifest records each part's base colour (sRGB). Every model has an
# Attach.Front empty at (0, -1, 0) and its own Attach.* points.
import bpy, sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_lib as K
from kit_street_paint import paint_atlas
from kit_street_build import build_object
import kit_street_m1, kit_street_m2, kit_street_m3, kit_street_m4

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else os.path.abspath('street_out')
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None
BUDGET = {'UtilityPole': 2500, 'MarketStall': 2500}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = os.path.join(OUT, 'StreetAtlas.png')
    paint_atlas(atlas)
    mat = K.material('Street', atlas)
    man = K.Manifest('Street', 'StreetAtlas.png')
    builders = kit_street_m1.MODELS + kit_street_m2.MODELS + kit_street_m3.MODELS + kit_street_m4.MODELS
    rows = []
    for fn in builders:
        m = fn()
        if ONLY and m.name not in ONLY: continue
        ob, parts = build_object(m)
        K.assign(ob, mat)
        extra = {'mount': m.mount, 'attach': dict(m.attach, Front=(0, -1, 0))}
        if m.tile: extra['tile'] = m.tile
        if m.note: extra['note'] = m.note
        extra.update(m.extra)
        if m.mount == 'wall':
            extra['blend_lift'] = 'lifted in Street.blend only, so review renders show it above the ground plane'
        man.add(ob, parts, **extra)
        K.export_model(ob, os.path.join(OUT, m.name + '.fbx'))
        e = man.data['models'][m.name]
        if m.mount == 'wall':
            ob.location.z = -e['min'][2] + 0.05        # the FBX keeps the true origin; this is for review only
        budget = BUDGET.get(m.name, 1500)
        rows.append((m.name, e['size'], e['tris'], budget, parts))
        print(f"MODEL {m.name:14s} {e['size']} tris {e['tris']}{'  OVER BUDGET' if e['tris'] > budget else ''}", flush=True)
    man.save(os.path.join(OUT, 'Street.json'))
    blend = os.path.join(OUT, 'Street.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    if os.path.exists(blend + '1'): os.remove(blend + '1')     # no backup copy in the output
    over = [r[0] for r in rows if r[2] > r[3]]
    print('models', len(rows), 'over budget:', over or 'none', f'({time.time() - t0:.0f} s)')


main()
