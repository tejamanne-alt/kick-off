# The BARRIERS kit for Dribble To School: real things a kid ducks under on the way to school,
# modelled by script in Blender (read docs/ART_DIRECTION.md first). Each spans the footpath with a
# clear 0.85 m gap over the kid's line for the game's slide (TrackBuilder.SlideUnder):
#   blenv/bin/python kit_barriers.py -- /abs/outdir [--only PlankTrestles,SurfRack]
# Writes into outdir: <Model>.fbx per model, BarriersAtlas.png, Barriers.json, Barriers.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Barriers.blend /abs/outdir/sheet.png [--models A,B]
#
# Built with the WORKS kit's machinery (kit_works_geo.py: pieces, primitives, the atlas layout,
# baked soft shading; kit_works_atlas.py: grime maps and shared tiles), with this kit's own extra
# materials and tiles (bark, sawn log ends, shutter slats, debris netting) and its own atlas and
# manifest, so it stands alone in Art/Models/Barriers/. The models are in kit_barriers_models.py.
#
# The manifest's extras tell the game the solid to build a collider for: slideHalf / slideTop (a box
# from the gap up, centred on the origin along x) or slideRadius / slideCentre (a round one), and for
# the market stall its awning (canopyHalf, canopyBottom, canopyTop).
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit_lib as K
import kit_works_geo as G
import kit_works_atlas as ATL
from kit_barriers_models import BARRIER_MODELS

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else '/tmp/barriers'
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None


def main():
    t0 = time.time()
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    models = []
    for fn in BARRIER_MODELS:
        M = fn()
        if ONLY and M.name not in ONLY:
            for b in M.pieces: b.free()
            continue
        models.append(M)
    items = ATL.tile_items()
    for M in models:
        items += M.plan_maps()
    used = G.allocate(items)
    print('atlas rows used', used, 'of', G.AT)
    atlas = os.path.join(OUT, 'BarriersAtlas.png')
    ATL.paint(atlas, models)
    mat = K.material('Barriers', atlas)
    man = K.Manifest('Barriers', 'BarriersAtlas.png')
    for M in models:
        ob = G.to_object(M)
        K.assign(ob, mat)
        for nm, loc in M.attach:
            K.attach(ob, nm, loc)
        parts = {}
        used_parts = set()
        for p in ob.data.uv_layers['Part'].data:
            used_parts.add(int(round(p.uv[0])))
        if 1 in used_parts and M.p1: parts[1] = G.s2l(M.p1)
        if 2 in used_parts and M.p2: parts[2] = G.s2l(M.p2)
        extra = dict(M.extra)
        extra['attach'] = {nm: [round(v, 3) for v in loc] for nm, loc in M.attach}
        man.add(ob, parts=parts, **extra)
        print('%-18s tris %5d  parts %s' % (M.name, K.tree_tris(ob), sorted(used_parts)))
        names = sorted(c.name for c in ob.children)
        assert names == sorted('Attach.' + nm for nm, _ in M.attach), (M.name, names)
        K.export_model(ob, os.path.join(OUT, M.name + '.fbx'))
        for c in ob.children: c.name = M.name + ':' + c.name
    man.save(os.path.join(OUT, 'Barriers.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Barriers.blend'))
    print('done', OUT, '%.1fs' % (time.time() - t0))


main()
