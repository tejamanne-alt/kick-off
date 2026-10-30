# The LEISURE kit for Dribble To School: original, cozy, stylized beach, park and playground set
# pieces, modelled by script in Blender (read docs/ART_DIRECTION.md first). Some are gameplay pieces
# whose sizes match the game's colliders and pivots (see the notes on each model below).
#   blenv/bin/python kit_leisure.py -- /abs/outdir [--only A,B]
# Writes into outdir: <Model>.fbx per model, LeisureAtlas.png, Leisure.json, Leisure.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Leisure.blend /abs/outdir/sheet.png [--models A,B]
#
# Space: metres, Z up, the front faces -Y (toward the game camera), origin at the base centre on
# the ground unless a model says otherwise. Every model has Attach.Front at (0, -1, 0); other
# Attach.* empties mark points the game uses (rope ties, jets, lights, faces).
# One material: vertex colours x LeisureAtlas.png. UV0 = the atlas (tiles, the model's projected
# wear maps, or the white corner at (0.97, 0.03)); UV1.x = recolour part (0 fixed, 1 main paint,
# 2 secondary, 3 third). Vertex colours are the part's base colour times soft baked shading
# (occlusion, ground contact, a low-to-high gradient), so a brightness-ratio recolour keeps it;
# wear, grain, seams and dirt live in the atlas. Leisure.json records each part's base colour (sRGB).
#
# Modules: kit_leisure_geo.py (pieces, primitives, shading, export), kit_leisure_atlas.py (atlas),
# kit_leisure_beach.py, kit_leisure_play.py (gameplay pieces), kit_leisure_park.py (backdrop).
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector
import kit_lib as K
import kit_leisure_geo as G
import kit_leisure_atlas as ATL
import kit_leisure_beach as BEACH

try:
    import kit_leisure_play as PLAY
except ImportError:
    PLAY = None
try:
    import kit_leisure_park as PARK
except ImportError:
    PARK = None

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS and not ARGS[0].startswith('--') else os.path.abspath('leisure_out')
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None

BUILDERS = [
    ('LifeguardTower', BEACH.lifeguard), ('Parasol', BEACH.parasol), ('BeachTowel', BEACH.towel),
    ('CoolBox', BEACH.coolbox), ('SandCastle', BEACH.sandcastle), ('BucketSpade', BEACH.bucketspade),
]
if PLAY:
    BUILDERS += PLAY.BUILDERS
if PARK:
    BUILDERS += PARK.BUILDERS


def part_colour(M, v):
    if isinstance(v, str): return G.s2l(M.pal[v])
    return tuple(float(x) for x in v)


def r3(v):
    return [round(float(x), 4) for x in v]


def main():
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    models = []
    for i, (name, fn) in enumerate(BUILDERS):
        if ONLY and name not in ONLY: continue
        M = fn(np.random.default_rng(100 + i))
        assert M.name == name, (M.name, name)
        models.append(M)
    layout = ATL.Layout(models)
    print('atlas rows used', layout.used, 'of', ATL.ATH)
    built = []
    for M in models:
        root, objs = G.realize(M, layout)
        built.append((M, root, objs))
    atlas = os.path.join(OUT, 'LeisureAtlas.png')
    ATL.paint(atlas, layout)
    mat = K.material('Leisure', atlas)
    man = K.Manifest('Leisure', 'LeisureAtlas.png')
    for M, root, objs in built:
        K.assign(root, mat)
        parts = {k: part_colour(M, v) for k, v in sorted(M.parts.items())}
        att = {}
        for e in [root] + list(root.children_recursive):
            nm = e.get('kit_name', e.name)
            if e.type == 'EMPTY' and nm.startswith('Attach.'):
                att[nm[len('Attach.'):]] = r3(e.matrix_world.translation)
        kids = [o.get('kit_name', o.name) for o in root.children if not o.get('kit_name', o.name).startswith('Attach.')]
        extra = dict(M.extra)
        extra['attach'] = att
        if kids: extra['children'] = kids
        man.add(root, parts=parts, **extra)
        e = man.data['models'][root.name]
        print('%-15s tris %5d  size %s  parts %s' % (root.name, e['tris'], e['size'], e['parts']))
        G.export_clean(root, os.path.join(OUT, M.name + '.fbx'))
    man.save(os.path.join(OUT, 'Leisure.json'))
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Leisure.blend'))
    print('done', OUT)


main()
