# Renders a review sheet of a built car (car.py) with the game's look: two cel bands from a sun
# with a cool lilac shadow, and an inverted-hull ink outline:
#   blenv/bin/python review_car.py -- /abs/Hatch.blend /abs/hatch_sheet.png
# Top row: three-quarter front and side. Bottom row: three-quarter rear and front. The strip
# along the bottom holds the car at roughly in-game size (about 120 px long), once at 1:1 and once
# enlarged 3x, where the silhouette and colours must still read, plus its stats (from the .json).
import bpy, math, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene
body = bpy.data.objects['Body']
wheels = [o for o in bpy.data.objects if o.name.startswith('Wheel.')]
meshes = [body] + wheels
SHADOW = (0.74, 0.72, 0.9, 1)


def toon(nt, color_out):
    """Lit / shadow bands from the sun (as in review_teen): colour x ramp(diffuse) -> emission."""
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(color_out, diff.inputs['Color'])
    s2r = nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(diff.outputs[0], s2r.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].color = SHADOW; ramp.color_ramp.elements[1].position = 0.18
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s2r.outputs[0], bw.inputs[0]); nt.links.new(bw.outputs[0], ramp.inputs[0])
    m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
    nt.links.new(color_out, m2.inputs['A']); nt.links.new(ramp.outputs['Color'], m2.inputs['B'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(m2.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])


mat = body.data.materials[0]; nt = mat.node_tree
mix = [n for n in nt.nodes if n.type == 'MIX'][0]
toon(nt, mix.outputs['Result'])
mat.use_backface_culling = True
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.13, 0.10, 0.12, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
sols = []
for o in meshes:
    o.data.materials.append(ol)
    s = o.modifiers.new('outline', 'SOLIDIFY'); s.thickness = 0.01; s.offset = 1; s.use_flip_normals = True
    s.material_offset = 1; s.use_rim = False
    sols.append(s)

# Ground that catches the car's shadow, so the wheels read as standing on something.
gm = bpy.data.meshes.new('ground'); gm.from_pydata([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new('ground', gm); S.collection.objects.link(ground)
gmat = bpy.data.materials.new('ground'); gmat.use_nodes = True
rgb = gmat.node_tree.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (0.66, 0.64, 0.60, 1)
toon(gmat.node_tree, rgb.outputs[0]); gm.materials.append(gmat)

turn = bpy.data.objects.new('turn', None); S.collection.objects.link(turn)
body.parent = turn
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(-30))
sun.data.angle = math.radians(2)
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.film_transparent = True      # the sky is composited behind the renders below
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
S.eevee.taa_render_samples = 16
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.type = 'ORTHO'

shots = [  # name, yaw, elevation, resolution, outline px
    ('f34', -35, 16, (800, 500), 2.0),
    ('side', -90, 3, (800, 500), 2.0),
    ('r34', 145, 16, (800, 500), 2.0),
    ('front', 0, 5, (800, 500), 2.0),
    ('game', -90, 8, (170, 90), 1.5),
]
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_review_tmp'); os.makedirs(tmp, exist_ok=True)
pts = np.array([list(o.matrix_world @ v.co) for o in meshes for v in o.data.vertices])
length = pts[:, 1].max() - pts[:, 1].min()
ims = {}
for name, yaw, elev, (rx, ry), opx in shots:
    turn.rotation_euler = (0, 0, math.radians(yaw)); C.view_layer.update()
    pts = np.array([list(o.matrix_world @ v.co) for o in meshes for v in o.data.vertices])
    e = math.radians(elev)
    fwd = Vector((0, math.cos(e), -math.sin(e))); right = Vector((1, 0, 0)); up = right.cross(fwd)
    X = pts @ np.array(right); Y = pts @ np.array(up)
    cx, cy = (X.max() + X.min()) / 2, (Y.max() + Y.min()) / 2
    if name == 'game':
        scale = length * rx / 120.0              # the car's length is 120 px
    else:
        scale = max(X.max() - X.min(), (Y.max() - Y.min()) * rx / ry) * 1.12
    centre = right * cx + up * cy
    cam.location = centre - fwd * 20; cam.rotation_euler = (math.radians(90) - e, 0, 0)
    cam.data.ortho_scale = scale
    S.render.resolution_x, S.render.resolution_y = rx, ry
    for s in sols: s.thickness = opx * scale / rx
    if name == 'f34':
        fp = Vector(bpy.data.objects['Front'].matrix_world.translation) - centre
        front_px = (rx / 2 + fp.dot(right) * rx / scale, ry / 2 - fp.dot(up) * rx / scale)
    S.render.filepath = os.path.join(tmp, name + '.png'); bpy.ops.render.render(write_still=True)
    from PIL import Image
    im = Image.open(S.render.filepath).convert('RGBA')
    bg = Image.new('RGBA', im.size, (158, 199, 242, 255)); bg.alpha_composite(im)
    ims[name] = bg.convert('RGB')

from PIL import Image, ImageDraw
W, H = 1600, 1000 + 300
sheet = Image.new('RGB', (W, H), (62, 62, 66))
for k, (x, y) in {'f34': (0, 0), 'side': (800, 0), 'r34': (0, 500), 'front': (800, 500)}.items():
    sheet.paste(ims[k], (x, y))
g = ims['game']
sheet.paste(g, (20, 1000 + (300 - g.height) // 2))
big = g.resize((g.width * 3, g.height * 3), Image.NEAREST)
sheet.paste(big, (210, 1000 + (300 - big.height) // 2))
# a close-up of the three-quarter view's front corner at 2x, to judge the outline and details
f = ims['f34']; cw, ch = 290, 150
cx, cy = int(front_px[0] - 70), int(front_px[1] - 110)
sheet.paste(f.crop((cx, cy, cx + cw, cy + ch)).resize((cw * 2, ch * 2), Image.LANCZOS), (W - cw * 2 - 10, 1000))
info_path = os.path.splitext(blend)[0] + '.json'
d = ImageDraw.Draw(sheet)
if os.path.exists(info_path):
    info = json.load(open(info_path))
    lines = [os.path.basename(os.path.splitext(blend)[0]),
             'tris %d   wheel r %.3f' % (info['tris'], info['wheelRadius']),
             'L %.2f  W %.2f  H %.2f' % (info['length'], info['width'], info['height']),
             'waist %.2f  roof %s' % (info['waist'], info.get('roof')),
             'paint %s' % (info['paint'],)]
    for i, t in enumerate(lines): d.text((740, 1030 + i * 22), t, fill=(235, 235, 235))
sheet.save(out)
print('sheet', out)
