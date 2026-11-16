# A Kamakura level's proposed layout, seen as the player will see it, for the user's approval before the level is built
# (docs/LEARNINGS.md A8): the kit's models placed by the layout's data (review/kamakura/levels/<id>/layout.json), the
# first-graders at their game height, a kid and ball for scale, rendered through the game camera (CameraFollow2D's
# framing, as preview_street.py: 34 degrees, 3.6 m half-height at the lane, tilted 4 degrees) every screen's width
# along the lane, and a plan of the whole level from above, labelled. The shading is Blender's, not the game's toon
# ramp: judge the places, sizes, order and gaps, not the light.
#   blenv/bin/python preview_km_level.py -- /abs/Kamakura.blend /abs/Kamakura.json /abs/layout.json /abs/Art/Models /abs/outdir
#     -> outdir/frames/<n>.png, outdir/strip.jpg (the frames side by side), outdir/plan.png
# The level as the game builds it: the installed models (the folder Art/Models/Kamakura in place of the .blend, its
# Kamakura.json), the layout the code places (km_level_from_code.py's built.json), and --game for the game camera's own
# framing (CameraFollow2D: 3.09 m half-height at the lane at 16:9, its focus 1.15 m over the kid's middle).
#   blenv/bin/python preview_km_level.py -- /abs/Art/Models/Kamakura /abs/Art/Models/Kamakura/Kamakura.json
#       /abs/review/kamakura/levels/KM1-1/built.json /abs/Art/Models /abs/outdir --game
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

argv = sys.argv[sys.argv.index('--') + 1:]
KIT_BLEND, KIT_JSON, LAYOUT, MODELS, OUT = argv[:5]
GAME = '--game' in argv
FROM_FBX = os.path.isdir(KIT_BLEND)                 # the installed models, each FBX with its own texture
os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)
lay = json.load(open(LAYOUT))
manifest = json.load(open(KIT_JSON))['models']

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
if FROM_FBX:
    roots = {}
else:
    with bpy.data.libraries.load(KIT_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    roots = {o.name: o for o in dst.objects if o is not None and o.parent is None and o.name in manifest}
    print('kit roots', len(roots), sorted(roots))


def load_fbx(model):
    """An installed model (FBX), in its own texture (its manifest's), cut out where it is a cut-out model; its Attach
    markers left out. Its root, at the origin."""
    info = manifest[model]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(KIT_BLEND, model + '.fbx'))
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith('Attach')]:
        new.remove(o)
        bpy.data.objects.remove(o)
    m = bpy.data.materials.new(model)
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(KIT_BLEND, info['texture']), check_existing=True)
    bsdf = nt.nodes['Principled BSDF']
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.9
    if info.get('cutout'):
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            m.blend_method = 'CLIP'
    for o in new:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(m)
    root = next(o for o in new if o.parent is None)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
    return root
cols = {}


def instance(model):
    """The kit model as a collection (its root at the origin), instanced once per placement."""
    if model not in cols:
        if model not in roots and FROM_FBX:
            roots[model] = load_fbx(model)
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
    if m not in roots and not (FROM_FBX and os.path.exists(os.path.join(KIT_BLEND, m + '.fbx')) and m in manifest):
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
for k in lay['markers']:          # what is still to come: half see-through, so it reads as a placeholder
    b0 = k.get('base', 0.0)
    o = box(k['what'], k['x'] - k['w'] / 2, k['x'] + k['w'] / 2, k['front'], k['front'] + k['d'], b0, b0 + k['h'], k['rgb'])
    if k.get('solid'):                # a stand-in the game builds: solid, as in the game
        continue
    m = o.data.materials[0]
    m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.55
    try: m.surface_render_method = 'BLENDED'
    except Exception: m.blend_method = 'BLEND'
    o.visible_shadow = False

# the people on the lane: the first-graders at their game height (neck 1.04 against the kid's 1.3: about 1.25 m to the
# kid's 1.57), a grown-up at the height its entry gives
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
    k = p.get('h', 1.25) / (max(zs) - min(zs))      # a grown-up sightseer at their own height (h), a first-grader at 1.25
    rig.scale = rig.scale * k
    # walking toward +x (dir 1) or toward -x (dir -1), a little toward us
    rig.rotation_euler = (rig.rotation_euler[0], rig.rotation_euler[1], math.radians(-66 * p.get('dir', 1)))
    rig.location = (p['x'], 0.0, -min(zs) * k)
    people.append(rig)

# the light: a clear May morning
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = 2.2; sun.data.color = (1, 0.97, 0.93)
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.62, 0.88, 1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
S.render.engine = 'BLENDER_EEVEE'
S.view_settings.view_transform = 'Standard'
S.render.resolution_x, S.render.resolution_y = 1280, 720

# the kid and the ball, for scale (moved with each frame)
kidm = box('kid', -0.2, 0.2, -0.15, 0.15, 0.0, 1.57, (0.9, 0.35, 0.3))
ball = box('ball', -0.17, 0.17, -0.17, 0.17, 0.0, 0.34, (0.97, 0.97, 0.95))

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(34); cam.data.clip_end = 3000
half, focus_y = (3.09, 1.75) if GAME else (3.6, 1.9)           # the game camera's framing (CameraFollow2D), or the board's
pitch = math.radians(4); dist = half / math.tan(math.radians(17))
fwd = Vector((0, math.cos(pitch), -math.sin(pitch)))
step = 2 * half * 16 / 9                  # one screen's width at the lane
xs = list(np.arange(X0 + step / 2, X1, step))
frames = []
for i, cx in enumerate(xs):
    focus = Vector((cx, 0, focus_y))
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
cam.data.type = 'ORTHO'; cam.data.sensor_fit = 'HORIZONTAL'; cam.data.ortho_scale = (X1 - X0) + 4   # (its width: the level's length)
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
import km_plan_labels                 # each place's short name, in rows taken in turn (E12)
km_plan_labels.label(lay, os.path.join(OUT, 'plan.png'), os.path.join(OUT, 'plan_labelled.jpg'))
print('done', len(frames), 'frames')
