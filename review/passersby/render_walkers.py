# The passers-by in the game's toon look, on the footpath: the six rigged passers-by (the jogger, Mom, the office
# worker, the courier, the shopkeeper, Grandad) beside the procedural adult, one row per level, each row dressed from
# their wardrobes the way TrackBuilder.Walker picks (top, legwear and hair, cap or hijab by the walker and the level),
# recoloured as ModelOutfit does in the game (each part's vertex colours times new / default). The wardrobes are read
# from LevelBuildKit.Passersby, so the picture follows the game's colours.
#   blenv/bin/python render_walkers.py -- <models dir> <out dir>   ->  <out dir>/walkers.png (four rows, on the sky)
import os, sys, json, math, re
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:]
sys.argv = sys.argv[:sys.argv.index('--') + 1] + [argv[0], argv[1], 'walkers']
src = open(os.path.join(HERE, '..', 'cartoon', 'render_scenes.py')).read()
exec(src[:src.index('SCENES = dict(')])
from PIL import Image

# ---- the wardrobes, from the game's code
CS = open(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Scripts', 'Editor', 'LevelBuildKit.cs')).read()
block = CS[CS.index('public static readonly Passerby[] Passersby'):CS.index('public static readonly string[] PasserbyModels')]
COL = re.compile(r'new Color\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)')
WARDROBES = []
for m in re.finditer(r'new Passerby\("(\w+)", ([\d.]+)f, ([\d.]+)f,(.*?\})\),', block, re.S):
    lists = re.findall(r'new\[\] \{(.*?)\}', m.group(4), re.S)
    pal = [[tuple(float(x) for x in c) for c in COL.findall(l)] for l in lists]
    WARDROBES.append((m.group(1), float(m.group(2)), pal))
print('wardrobes', [(w[0], [len(p) for p in w[2]]) for w in WARDROBES])

# Four levels, a walker each: the game's mix (seed * 7 + the level's salt) picks the top by mix / 3, the legwear by
# mix / 7 and the third part by mix / 11 from the passer-by's wardrobe.
LEVELS = [('the first level', 0), ('a market level', 52411), ('a beach level', 81277), ('a park level', 23069)]


def outfit(pal, mix):
    tops, legs, thirds = pal
    return tops[(mix // 3) % len(tops)], legs[(mix // 7) % len(legs)], thirds[(mix // 11) % len(thirds)]


def lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def keep_colours(objs):
    """Each mesh's own vertex colours and parts, to recolour from on every row."""
    out = []
    for o in meshes(objs):
        me = o.data
        if len(me.uv_layers) < 2 or not me.color_attributes: continue
        uv2 = me.uv_layers[1]; col = me.color_attributes[0]
        parts = {}
        for poly in me.polygons:
            for li in poly.loop_indices:
                idx = li if col.domain == 'CORNER' else me.loops[li].vertex_index
                parts[idx] = int(round(uv2.data[li].uv.x))
        out.append((col, [tuple(d.color) for d in col.data], parts))
    return out


def recolour(kept, defaults, dress):
    """ModelOutfit.Recolor: a part's vertex colours times new / default (game colours are sRGB; vertex colours linear)."""
    ratio = {}
    for p, key in ((1, 'top'), (2, 'legwear'), (3, 'hair')):
        new, old = lin(dress[p - 1]), lin(defaults[key])
        ratio[p] = [n / max(o, 1e-4) for n, o in zip(new, old)]
    for col, orig, parts in kept:
        for idx, c in enumerate(orig):
            r = ratio.get(parts.get(idx, 0))
            col.data[idx].color = c if r is None else (min(1, c[0] * r[0]), min(1, c[1] * r[1]), min(1, c[2] * r[2]), 1)


street(road=True, footpath=(0.74, 0.71, 0.70))
for i in range(-10, 10):
    kit('Street', 'PicketFence2', (i * 2.0 + 1.0, 2.7, 0.0))
kit('Buildings', 'HouseGable', (-6.0, 4.4, 0.0)); kit('Buildings', 'HouseLong', (3.5, 4.4, 0.0))
kit('Plants', 'Broadleaf', (-1.2, 3.6, 0.0))
for c in [(-30, 170, 40, 10), (20, 165, 46, 11)]:
    cloud(c[:3], c[3])
xs = [-4.8, -3.2, -1.6, 0.0, 1.6, 3.2, 4.8]
FIGS = []
for x, (name, height, pal) in zip(xs, WARDROBES):
    objs = person(name, (x, 0.4, 0.0), 66 if x < 0 else -66, 'walk', height)
    FIGS.append((keep_colours(objs), json.load(open(os.path.join(MODELS, name + '.json'))), pal))
person('Adult', (xs[len(WARDROBES)], 0.4, 0.0), -66, 'walk', 1.72)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(26)
cam.location = (0.0, -6.9, 1.25); cam.rotation_euler = (Vector((0.0, 0.0, 0.98)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = math.pi; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (-SUNDIR).to_track_quat('-Z', 'Y').to_euler()
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
S.render.engine = 'BLENDER_EEVEE'; S.render.resolution_x, S.render.resolution_y = 1920, 560
S.render.film_transparent = True; S.render.image_settings.color_mode = 'RGBA'
S.view_settings.view_transform = 'Standard'; S.eevee.taa_render_samples = 16
set_pass('colour')
rows = []
for k, (label, salt) in enumerate(LEVELS):
    for i, (kept, defaults, pal) in enumerate(FIGS):
        seed = 101 + 37 * i                                   # (a walker of its own on each)
        recolour(kept, defaults, outfit(pal, abs(seed * 7 + salt)) if k else (defaults['top'], defaults['legwear'], defaults['hair']))
    for o in bpy.data.meshes: o.update()
    p = os.path.join(OUT, '_walkers_%d.png' % k); S.render.filepath = p
    bpy.ops.render.render(write_still=True); rows.append(p)
    print('rendered', label if k else 'as they came')
# each row on the game's sky (review/pier_stairs/compose.py), labelled, one under the other
sys.path.insert(0, os.path.join(HERE, '..', 'pier_stairs'))
import compose
ims = []
for p, (label, _) in zip(rows, LEVELS):
    ims.append(compose.label(compose.with_sky(p), 'As they came' if not ims else 'Dressed for ' + label))
board = Image.new('RGB', (ims[0].size[0], sum(i.size[1] for i in ims)), (255, 255, 255)); y = 0
for i in ims:
    board.paste(i, (0, y)); y += i.size[1]
board.save(os.path.join(OUT, 'walkers.png'))
for p in rows: os.remove(p)
print('rendered walkers')
