# The WORKS kit for Dribble To School: original, cozy, stylized building-site, gate, underpass and
# school-entrance pieces, modelled by script in Blender (read docs/ART_DIRECTION.md first).
#   blenv/bin/python kit_works.py -- /abs/outdir [--only SlidingGate,TowerCrane]
# Writes into outdir: <Model>.fbx per model, WorksAtlas.png, Works.json, Works.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Works.blend /abs/outdir/sheet.png [--models A,B]
#
# Space: metres, Z up, fronts face -Y (toward the game camera); game z (depth) is Blender +Y and
# game y (up) is Blender Z. Origins sit at the base centre on the ground unless a model says
# otherwise (the gameplay pieces put theirs where the game's collider, slide or pivot needs it;
# see each builder's docstring and the manifest's extras). Every FBX has one root mesh named after
# the model and Attach.* empties (Attach.Front at (0, -1, 0) on every model, plus Button, Panel,
# Hook, Light, Face ...).
#
# One material: vertex colours x WorksAtlas.png. UV0 = atlas, UV1.x = recolour part: 0 fixed,
# 1 main paint, 2 secondary. Vertex colours carry each part's base colour times baked soft shading
# (ray-cast ambient occlusion and gentle piece gradients); grime, rust streaks, chips, dirt, joints
# and ribbing live in the atlas as multipliers, so a recolour keeps them. Works.json records each
# part's base colour (sRGB, as in the FBX).
#
# Modules: kit_works_geo.py (pieces, primitives, atlas layout, mesh conversion and baking),
# kit_works_atlas.py (painting), kit_works_gate.py (gate, underpass, school),
# kit_works_site.py (building site).
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit_lib as K
import kit_works_geo as G
import kit_works_atlas as ATL
from kit_works_gate import GATE_MODELS
try:
    from kit_works_site import SITE_MODELS
except ImportError:
    SITE_MODELS = []

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else '/tmp/works'
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None
LIFT = '--lift' in ARGS        # review builds only: stand models whose origin is off the ground on z = 0


def main():
    t0 = time.time()
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    models = []
    for fn in GATE_MODELS + SITE_MODELS:
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
    atlas = os.path.join(OUT, 'WorksAtlas.png')
    ATL.paint(atlas, models)
    mat = K.material('Works', atlas)
    man = K.Manifest('Works', 'WorksAtlas.png')
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
        print('%-16s tris %5d  parts %s' % (M.name, K.tree_tris(ob), sorted(used_parts)))
        if G.PROFILE:
            for k, v in sorted(M.prof.items(), key=lambda kv: -kv[1])[:12]:
                print('    %6d  %s' % (v, k))
        names = sorted(c.name for c in ob.children)
        assert names == sorted('Attach.' + nm for nm, _ in M.attach), (M.name, names)
        K.export_model(ob, os.path.join(OUT, M.name + '.fbx'))
        # free the Attach.* names for the next model (one scene holds the whole kit; each FBX
        # carries the exact names, the .blend keeps them prefixed with the model's name)
        for c in ob.children: c.name = M.name + ':' + c.name
        if LIFT and not M.ground:
            ob.location.z -= min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    man.save(os.path.join(OUT, 'Works.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Works.blend'))
    print('done', OUT, '%.1fs' % (time.time() - t0))


main()
