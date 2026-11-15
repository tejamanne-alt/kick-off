# A Kamakura level's proposed layout, seen as the player will see it, for the user's approval before the level is built
# (docs/LEARNINGS.md A8): the kit's models placed by the layout's data (review/kamakura/levels/<id>/layout.json), the
# first-graders at their game height, a kid and ball for scale, rendered through the game camera (CameraFollow2D's
# framing, as preview_street.py: 34 degrees, 3.6 m half-height at the lane, tilted 4 degrees) every screen's width
# along the lane, and a plan of the whole level from above, labelled. The shading is Blender's, not the game's toon
# ramp: judge the places, sizes, order and gaps, not the light.
#   blenv/bin/python preview_km_level.py -- /abs/Kamakura.blend /abs/Kamakura.json /abs/layout.json /abs/Art/Models /abs/outdir
#     -> outdir/frames/<n>.png, outdir/strip.jpg (the frames side by side), outdir/plan.png
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
KIT_BLEND, KIT_JSON, LAYOUT, MODELS, OUT = argv[:5]
os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)
lay = json.load(open(LAYOUT))
manifest = json.load(open(KIT_JSON))['models']

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
with bpy.data.libraries.load(KIT_BLEND, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
roots = {o.name: o for o in dst.objects if o is not None and o.parent is None and o.name in manifest}
print('kit roots', len(roots), sorted(roots))
cols = {}


def instance(model):
    """The kit model as a collection (its root at the origin), instanced once per placement."""
    if model not in cols:
        root = roots[model]
        root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0)
        col = bpy.data.collections.new(model)
        for o in [root] + list(root.children_recursive):
            col.objects.link(o)
        cols[model] = col
    e = bpy.data.objects.new(model, None)
    e.instance_type = 'COLLECTION'; e.instance_collection = cols[model]
    S.collection.objects.link(e)
    return e


def box(name, x0, x1, z0, z1, h0, h1, rgb):
    """A box in game axes: x along, z away from the camera (Blender y), h up."""
    me = bpy.data.meshes.new(name)
    v = [(x, z, h) for x in (x0, x1) for z in (z0, z1) for h in (h0, h1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = tuple(rgb) + (1,)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    o.data.materials.append(m)
    return o


X0, X1 = lay['length']
for g in lay['ground']:
    box(g['what'], X0 - 40, X1 + 40, g['z'][0], g['z'][1], -0.05, 0.0, g['rgb'])

missing = []
for p in lay['placements']:
    m = p['model']
    if m not in roots:
        missing.append(m); continue
    info = manifest[m]
    size, mn = info.get('size', [1, 1, 1]), info.get('min', [0, -0.5, 0])
    e = instance(m)
    yaw = p.get('yaw', 0)
    if yaw == 90:            # its end toward the camera: along z, its nose at `front`
        e.rotation_euler = (0, 0, math.radians(90))
        e.location = (p['x'], p['front'] + size[0] / 2, 0)
    else:
        e.location = (p['x'], p['front'] - mn[1], 0)
for k in lay['markers']:
    box(k['what'], k['x'] - k['w'] / 2, k['x'] + k['w'] / 2, k['front'], k['front'] + k['d'], 0.0, k['h'], k['rgb'])

# the first-graders at their game height (neck 1.04 against the kid's 1.3: about 1.25 m to the kid's 1.57), on the lane
people = []
for p in lay.get('people', []):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(MODELS, p['model'] + '.fbx'))
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == 'ARMATURE'); kid = next(o for o in new if o.type == 'MESH')
    atlas = bpy.data.images.load(os.path.join(MODELS, p['model'] + 'Atlas.png'))
    mat = bpy.data.materials.new(p['model']); mat.use_nodes = True; nt = mat.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = atlas
    vc = nt.nodes.new('ShaderNodeVertexColor')
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    kid.data.materials.clear(); kid.data.materials.append(mat)
    bpy.context.view_layer.update()
    zs = [(kid.matrix_world @ v.co).z for v in kid.data.vertices]
    k = 1.25 / (max(zs) - min(zs))
    rig.scale = rig.scale * k
    rig.rotation_euler = (rig.rotation_euler[0], rig.rotation_euler[1], math.radians(-66))   # walking toward +x, a little toward us
    rig.location = (p['x'], 0.0, -min(zs) * k)
    people.append(rig)

# the light: a clear May morning
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1, 0.97, 0.93)
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.62, 0.88, 1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
S.render.engine = 'BLENDER_EEVEE'
S.view_settings.view_transform = 'Standard'
S.render.resolution_x, S.render.resolution_y = 1280, 720

# the kid and the ball, for scale (moved with each frame)
kidm = box('kid', -0.2, 0.2, -0.15, 0.15, 0.0, 1.57, (0.9, 0.35, 0.3))
ball = box('ball', -0.17, 0.17, -0.17, 0.17, 0.0, 0.34, (0.97, 0.97, 0.95))

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(34); cam.data.clip_end = 3000
pitch = math.radians(4); dist = 3.6 / math.tan(math.radians(17))
fwd = Vector((0, math.cos(pitch), -math.sin(pitch)))
step = 7.2 * 16 / 9                       # one screen's width at the lane
xs = list(np.arange(X0 + step / 2, X1, step))
frames = []
for i, cx in enumerate(xs):
    focus = Vector((cx, 0, 1.9))
    cam.location = focus - fwd * dist
    cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
    kidm.location = (cx - 2.2, 0, 0); ball.location = (cx - 1.6, 0, 0)
    S.render.filepath = os.path.join(OUT, 'frames', '%02d.png' % i)
    bpy.ops.render.render(write_still=True)
    frames.append((cx, S.render.filepath))
json.dump({'frames': frames, 'missing': missing}, open(os.path.join(OUT, 'frames.json'), 'w'))
print('missing models', missing)

# the plan from above, orthographic: the whole level
kidm.location = (X0 - 100, 0, 0); ball.location = (X0 - 100, 0, 0)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = (X1 - X0) + 4
cam.location = ((X0 + X1) / 2, 6.0, 60); cam.rotation_euler = (0, 0, 0)
S.render.resolution_x, S.render.resolution_y = 3200, int(3200 * 30 / ((X1 - X0) + 4))
S.render.filepath = os.path.join(OUT, 'plan.png')
bpy.ops.render.render(write_still=True)

# the strip (the frames side by side, as the player sees them pass) and the plan, each place labelled
from PIL import Image, ImageDraw, ImageFont
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f = ImageFont.truetype(font, 22) if os.path.exists(font) else ImageFont.load_default()
ims = [Image.open(p).convert('RGB').resize((640, 360)) for _, p in frames]
strip = Image.new('RGB', (640 * len(ims), 400), (30, 32, 36))
d = ImageDraw.Draw(strip)
for i, (im, (cx, _)) in enumerate(zip(ims, frames)):
    strip.paste(im, (640 * i, 40))
    d.text((640 * i + 8, 8), 'x %.0f to %.0f m' % (cx - step / 2, cx + step / 2), font=f, fill=(235, 235, 240))
strip.save(os.path.join(OUT, 'strip.jpg'), quality=86)
plan = Image.open(os.path.join(OUT, 'plan.png')).convert('RGB')
W, H = plan.size
span = (X1 - X0) + 4
px = lambda x: (x - (X0 - 2)) / span * W
py = lambda z: (21.0 - z) / 30.0 * H
d = ImageDraw.Draw(plan)
fs = ImageFont.truetype(font, 15) if os.path.exists(font) else f
for n, it in enumerate(lay['placements'] + lay['markers']):
    x, z = it['x'], it['front']
    label = it.get('model') or it['what']
    yy = py(z) + 8 + (n % 3) * 17
    d.line([(px(x), py(z)), (px(x), yy)], fill=(20, 20, 20), width=1)
    d.text((px(x) + 2, yy), label, font=fs, fill=(10, 10, 10), stroke_width=2, stroke_fill=(250, 250, 250))
for it in lay['play']:
    d.line([(px(it['x']), 0), (px(it['x']), H)], fill=(200, 40, 40), width=2)
for x in range(int(X0) // 10 * 10, int(X1) + 1, 10):
    d.text((px(x) + 2, H - 22), '%d m' % x, font=fs, fill=(250, 250, 250), stroke_width=2, stroke_fill=(20, 20, 20))
plan.save(os.path.join(OUT, 'plan_labelled.jpg'), quality=86)
print('done', len(frames), 'frames')
