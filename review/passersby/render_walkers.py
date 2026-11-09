# The passers-by in the game's toon look, on the footpath: the jogger in a few of her outfits (her jacket, leggings and
# hair recoloured as ModelOutfit does in the game: each part's vertex colours times new / default) beside the
# procedural adult.   blenv/bin/python render_walkers.py -- <models dir> <out dir>
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:]
sys.argv = sys.argv[:sys.argv.index('--') + 1] + [argv[0], argv[1], 'walkers']
src = open(os.path.join(HERE, '..', 'cartoon', 'render_scenes.py')).read()
exec(src[:src.index('SCENES = dict(')])

# (jacket, leggings, hair) from LevelBuildKit's JoggerTops, JoggerLeggings, JoggerHair
OUTFITS = [None,
           ((0.96, 0.45, 0.42), (0.14, 0.16, 0.3), (0.24, 0.15, 0.1)),
           ((0.55, 0.4, 0.82), (0.12, 0.12, 0.14), (0.13, 0.1, 0.09)),
           ((0.98, 0.76, 0.24), (0.16, 0.26, 0.22), (0.42, 0.18, 0.12))]
defaults = json.load(open(os.path.join(MODELS, 'Jogger.json')))


def lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def recolour(objs, outfit):
    """ModelOutfit.Recolor: a part's vertex colours times new / default (game colours are sRGB; vertex colours linear)."""
    if outfit is None: return
    ratio = {}
    for p, key in ((1, 'top'), (2, 'legwear'), (3, 'hair')):
        new, old = lin(outfit[p - 1]), lin(defaults[key])
        ratio[p] = [n / max(o, 1e-4) for n, o in zip(new, old)]
    for o in meshes(objs):
        me = o.data
        if len(me.uv_layers) < 2 or not me.color_attributes: continue
        uv2 = me.uv_layers[1]; col = me.color_attributes[0]
        for poly in me.polygons:
            for li in poly.loop_indices:
                p = int(round(uv2.data[li].uv.x))
                if p in ratio:
                    idx = li if col.domain == 'CORNER' else me.loops[li].vertex_index
                    c = col.data[idx].color
                    col.data[idx].color = (min(1, c[0] * ratio[p][0]), min(1, c[1] * ratio[p][1]), min(1, c[2] * ratio[p][2]), 1)


street(road=True, footpath=(0.74, 0.71, 0.70))
for i in range(-10, 10):
    kit('Street', 'PicketFence2', (i * 2.0 + 1.0, 2.7, 0.0))
kit('Buildings', 'HouseGable', (-6.0, 4.4, 0.0)); kit('Buildings', 'HouseLong', (3.5, 4.4, 0.0))
kit('Plants', 'Broadleaf', (-1.2, 3.6, 0.0))
for c in [(-30, 170, 40, 10), (20, 165, 46, 11)]:
    cloud(c[:3], c[3])
xs = [-3.3, -1.65, 0.0, 1.65]
for x, outfit in zip(xs, OUTFITS):
    objs = person('Jogger', (x, 0.4, 0.0), 66 if x < 0 else -66, 'walk', 1.66)
    recolour(objs, outfit)
person('Adult', (3.3, 0.4, 0.0), -66, 'walk', 1.72)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(30)
cam.location = (0.0, -8.0, 1.6); cam.rotation_euler = (Vector((0.0, 0.0, 1.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = math.pi; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (-SUNDIR).to_track_quat('-Z', 'Y').to_euler()
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
S.render.engine = 'BLENDER_EEVEE'; S.render.resolution_x, S.render.resolution_y = 1920, 900
S.render.film_transparent = True; S.render.image_settings.color_mode = 'RGBA'
S.view_settings.view_transform = 'Standard'; S.eevee.taa_render_samples = 16
set_pass('colour')
S.render.filepath = os.path.join(OUT, 'walkers.png'); bpy.ops.render.render(write_still=True)
print('rendered walkers')
