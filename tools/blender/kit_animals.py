# The ANIMALS kit for Dribble To School: original stylized 3D animals and collectibles that
# replace the blobby procedural dog and seagull, the flat coin and sticker sprites, and add the
# little wildlife of each chapter. Read docs/ART_DIRECTION.md first.
#   blenv/bin/python kit_animals.py -- /abs/outdir [--only Dog,Coin]
# Writes into outdir: <Model>.fbx (one per model), AnimalsAtlas.png, Animals.json, Animals.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Animals.blend /abs/outdir/sheet.png [--models A,B]
#
# Look: cute but grounded, chunky readable silhouettes, soft gradients baked into the vertex
# colours (light backs, darker bellies and creases), crisp painted markings, small glossy eyes
# with a highlight (painted in the atlas).
#
# Space (kit_lib): metres, Z up, the front (the side the game camera sees) faces -Y, and every
# model has an Attach.Front empty at (0, -1, 0).
#   Animals are side-on: the head points +X (game +x once Attach.Front faces the camera), so the
#   right flank faces the camera; the game yaws them so the head leads. The crab faces the camera
#   (-Y) and walks sideways along X.
#   Origins: on the ground at the footprint centre (Dog, Cat, Pigeon, Crab, Squirrel,
#   SeagullStanding); at the waterline (Duck); at the body's centre (flying Seagull, Butterfly);
#   at the centre (Coin, Sticker, Star).
# Rigs: an animated animal is an empty root named after the model holding one mesh per part
# (Body, Head, Tail, Leg.., Wing.., Claw.., Ear..), each with its origin at its pivot and an
# identity rest rotation, so its local axes are the model's. The game rotates the parts.
# Vertex data (kit_lib contract): colour (sRGB in the FBX) x AnimalsAtlas.png; UV0 the atlas
# (eyes, noses, feathers, wing patterns, painted mouths and stripes; flat parts use the white
# corner); UV1.x the recolour part: 1 main colour (fur, feathers, wing colour, coin gold, sticker
# face), 2 secondary (collar, beak, bill, neck sheen, heart), 0 fixed. Part colours carry baked
# shading around the base colour recorded in Animals.json (sRGB), so the game's brightness-ratio
# recolour keeps it. Normals are custom (from the modelling fields), so low-poly forms shade softly.
#
# Models (parts in brackets are separate meshes, origin at the pivot; see Animals.json "rig"):
#   Dog              [Body, Head (neck), Tail, LegFL/FR/BL/BR (shoulders, hips), EarL/EarR under Head]
#                    honey-ginger mutt with cream socks, muzzle, chest and brows, a red collar and tag
#   Seagull          [Body, WingL, WingR (shoulders)] flying, wings spread flat, 0.9 m span
#   SeagullStanding  static, standing on the ground
#   Pigeon           [Body, Head (neck base)] blue-grey with a green-purple neck sheen
#   Duck             [Body, Head (neck)] a mallard drake, floating
#   Cat              [Body, Tail] a ginger tabby sitting (for a 1.6 m garden wall), blue collar, bell
#   Crab             [Body, ClawL, ClawR (shoulders)] faces the camera
#   Butterfly        [Body, WingL, WingR] apricot wings, painted pattern
#   Squirrel         [Body, Tail] a red squirrel with a bushy tail
#   Coin, Sticker, Star  static collectibles, origin at the centre, face toward -Y
# Modules: kit_animals_geo (fields, meshing, cuts, pieces), kit_animals_common (parts, shading,
# eyes), kit_animals_atlas, kit_animals_beasts (dog, cat, squirrel), kit_animals_birds (gulls,
# pigeon, duck), kit_animals_small (crab, butterfly), kit_animals_items (coin, sticker, star).
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
import kit_lib as KL
import kit_animals_geo as G
import kit_animals_atlas as A
import kit_animals_common as K
import kit_animals_beasts as BEASTS
import kit_animals_birds as BIRDS
import kit_animals_small as SMALL
import kit_animals_items as ITEMS

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS and not ARGS[0].startswith('--') else os.path.abspath('animals_out')
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None

MODELS = [
    ('Dog', BEASTS.build_dog),
    ('Seagull', BIRDS.build_seagull),
    ('SeagullStanding', BIRDS.build_seagull_standing),
    ('Pigeon', BIRDS.build_pigeon),
    ('Duck', BIRDS.build_duck),
    ('Cat', BEASTS.build_cat),
    ('Crab', SMALL.build_crab),
    ('Butterfly', SMALL.build_butterfly),
    ('Squirrel', BEASTS.build_squirrel),
    ('Coin', ITEMS.build_coin),
    ('Sticker', ITEMS.build_sticker),
    ('Star', ITEMS.build_star),
]


def build(model, mat):
    """Blender objects for a Model: the root (an empty, or the static mesh) and its parts."""
    objs = {}
    if model.kind == 'static':
        part = model.parts[0]
        root = G.to_object(model.name, G.merge(part.pieces), part.pivot)
        objs[model.name] = root
    else:
        root = bpy.data.objects.new(model.name, None)
        bpy.context.scene.collection.objects.link(root)
        root.empty_display_size = 0.2
        objs[model.name] = root
        for part in model.parts:
            o = G.to_object(part.name, G.merge(part.pieces), part.pivot)
            objs[part.name] = o
        for part in model.parts:
            o = objs[part.name]
            parent = objs[part.parent] if part.parent else root
            o.parent = parent
            ppiv = next(p.pivot for p in model.parts if p.name == part.parent) if part.parent else np.zeros(3)
            o.location = tuple(map(float, part.pivot - ppiv))
    bpy.context.view_layer.update()
    KL.attach(root, 'Front', (0, -1, 0))
    for k, (loc, on) in model.attach.items():
        # an attach point on a moving part follows it (its location is relative to the part's pivot)
        if on and model.kind != 'static':
            piv = next(p.pivot for p in model.parts if p.name == on)
            KL.attach(objs[on], k, tuple(map(float, np.asarray(loc, float) - piv)))
        else:
            KL.attach(root, k, tuple(map(float, loc)))
    KL.assign(root, mat)
    bpy.context.view_layer.update()
    return root


def rig_info(model):
    out = {}
    for part in model.parts:
        if model.kind == 'static':
            continue
        e = {'pivot': [round(float(c), 4) for c in part.pivot], 'parent': part.parent or model.name,
             'tris': int(sum(p.tris() for p in part.pieces))}
        if part.motion:
            e['motion'] = part.motion
        out[part.name] = e
    return out


def main():
    t0 = time.time()
    KL.reset()
    os.makedirs(OUT, exist_ok=True)
    atlas = os.path.join(OUT, 'AnimalsAtlas.png')
    A.paint_atlas(atlas)
    mat = KL.material('Animals', atlas)
    man = KL.Manifest('Animals', 'AnimalsAtlas.png')
    man.data['notes'] = {
        'front': '-Y (Attach.Front at (0, -1, 0)). Animals are side-on with the head toward +X; the crab faces -Y.',
        'axes': 'model space: X head direction, Y depth (away from the camera), Z up. Parts have identity rest rotations.',
        'parts': '0 fixed, 1 main colour (fur, feathers, wings, gold, sticker face), 2 secondary (collar, beak, sheen, heart)',
    }
    report = []
    for name, fn in MODELS:
        if ONLY and name not in ONLY:
            continue
        t = time.time()
        model = fn()
        root = build(model, mat)
        parts = {k: tuple(float(x) for x in v) for k, v in sorted(model.colors.items())}
        extra = dict(model.extra)
        if model.kind != 'static':
            extra['rig'] = rig_info(model)
        extra['attach'] = {'Front': {'at': [0, -1, 0], 'parent': name}}
        for k, (loc, on) in model.attach.items():
            extra['attach'][k] = {'at': [round(float(c), 4) for c in loc], 'parent': on or name}
        man.add(root, parts=parts, **extra)
        bad = [o.name for o in [root] + list(root.children_recursive) if '.0' in o.name[-4:]]
        if bad:
            raise RuntimeError('suffixed names in %s: %s' % (name, bad))
        KL.export_model(root, os.path.join(OUT, name + '.fbx'))
        tris = KL.tree_tris(root)
        # free the part names (Body, Head, WingL, Attach.Front...) for the next model: Blender
        # suffixes clashing names, and the game matches the exported names exactly
        for o in root.children_recursive:
            o.name = name + ':' + o.name
        for part in model.parts:
            print('   part %-10s %5d tris %s' % (part.name, sum(p.tris() for p in part.pieces), [p.tris() for p in part.pieces]))
        report.append((name, tris, model.budget, man.data['models'][name]['size'], time.time() - t))
    man.save(os.path.join(OUT, 'Animals.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Animals.blend'))
    for name, tris, lim, size, dt in report:
        print('ANIMAL %-16s %5d / %4d tris %s  size %s  (%.1fs)' % (name, tris, lim, 'OK  ' if tris <= lim else 'OVER', size, dt))
    print('done in %.1fs' % (time.time() - t0))


main()
