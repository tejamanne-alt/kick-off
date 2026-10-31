# Renders a review sheet of a built teen with the game's look (ToonCharacter: two flat cel bands
# from the sun, the shade tinted cool by the sky, a rim of light, an ink outline):
#   blenv/bin/python review_teen.py -- /abs/Girl.blend /abs/girl_sheet.png [--bg a.png,b.png,...]
# Top row: face close-ups (front, three-quarter, profile). Middle: full body standing
# three-quarter, running, kicking, side, back. Bottom: the character at in-game size (about
# 215 px tall, with the in-game outline width) standing and running in front of game
# screenshots (--bg; each is scaled to 920 px tall, a phone's screen height), or in front of a
# busy stand-in when none are given: the silhouette and colours must still read there.
import bpy, math, sys, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]
bgs = args[args.index('--bg') + 1].split(',') if '--bg' in args else []
OUTLINE = float(os.environ.get('REVIEW_OUTLINE', '0.0017'))   # the player's outline width in the game (fraction of screen height)
KID_PX = 215              # the kid's height on a 920 px tall screen
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene
kid = bpy.data.objects['Kid']; rig = bpy.data.objects['KidRig']

# The game's toon shading (ToonCharacter.shader with WorldLook's daylight), as shader nodes:
#   lit  = smoothstep(-0.02, 0.06, N.L)
#   col  = albedo * lerp(shade, sun, lit) + rim * 0.22 * sun
SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
mat = kid.data.materials[0]; nt = mat.node_tree
mix = [n for n in nt.nodes if n.type == 'MIX'][0]
L = nt.nodes.new('ShaderNodeCombineXYZ')
geo = nt.nodes.new('ShaderNodeNewGeometry')
dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
lit = nt.nodes.new('ShaderNodeMapRange'); lit.interpolation_type = 'SMOOTHSTEP'
lit.inputs['From Min'].default_value = -0.02; lit.inputs['From Max'].default_value = 0.06
nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
band = nt.nodes.new('ShaderNodeMix'); band.data_type = 'RGBA'
band.inputs['A'].default_value = SHADE + (1,); band.inputs['B'].default_value = SUN + (1,)
nt.links.new(lit.outputs['Result'], band.inputs['Factor'])
m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
nt.links.new(mix.outputs['Result'], m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
# rim: smoothstep(0.6, 0.76, 1 - N.V) * lerp(0.4, 1, saturate(N.L + 0.35))
ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
rim = nt.nodes.new('ShaderNodeMapRange'); rim.interpolation_type = 'SMOOTHSTEP'
rim.inputs['From Min'].default_value = 0.4; rim.inputs['From Max'].default_value = 0.24
rim.inputs['To Min'].default_value = 0.0; rim.inputs['To Max'].default_value = 1.0
nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
side = nt.nodes.new('ShaderNodeMapRange'); side.inputs['From Min'].default_value = -0.35; side.inputs['From Max'].default_value = 0.65
side.inputs['To Min'].default_value = 0.4; side.inputs['To Max'].default_value = 1.0
nt.links.new(dot.outputs['Value'], side.inputs['Value'])
rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'
nt.links.new(rim.outputs['Result'], rk.inputs[0]); nt.links.new(side.outputs['Result'], rk.inputs[1])
RIM = float(os.environ.get('REVIEW_RIM', '0.22'))
rk2 = nt.nodes.new('ShaderNodeMath'); rk2.operation = 'MULTIPLY'; rk2.inputs[1].default_value = RIM
nt.links.new(rk.outputs[0], rk2.inputs[0])
add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
add.inputs['B'].default_value = SUN + (1,)
nt.links.new(rk2.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
kid.data.materials.append(ol)
sol = kid.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = 0.005; sol.offset = 1; sol.use_flip_normals = True; sol.material_offset = 1
mat.use_backface_culling = True
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
try: S.eevee.taa_render_samples = 8
except Exception: pass
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.type = 'ORTHO'

# The game's sun, (0.45, 0.8, -0.4) in Unity (x right, y up, z away from the camera); the review
# camera looks along +Y, so in Blender's world it is (0.45, -0.4, 0.8). The normals are world
# space, so the light stays put while the character turns.
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()
L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR

# Head height for framing the close-ups.
zs = [(kid.matrix_world @ v.co).z for v in kid.data.vertices]
top = max(zs)
head_z = rig.data.bones['Head'].head_local.z
face_z = head_z + 0.12

poses = {'stand': {},
         'run': {'UpperLeg.R': -40, 'LowerLeg.R': 60, 'UpperLeg.L': 38, 'LowerLeg.L': 92, 'UpperArm.R': 34, 'LowerArm.R': -85, 'UpperArm.L': -30, 'LowerArm.L': -70, 'Bag': 10},
         'kick': {'UpperLeg.R': -80, 'LowerLeg.R': 5, 'UpperLeg.L': 10, 'LowerLeg.L': 14, 'UpperArm.R': 45, 'UpperArm.L': -60, 'LowerArm.L': -35},
         'idle': {'LowerLeg.R': 5, 'LowerLeg.L': 5, 'LowerArm.R': -14, 'LowerArm.L': -14}}

def pose(name):
    for pb in rig.pose.bones: pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
    for b, a in poses[name].items(): rig.pose.bones[b].rotation_euler = (math.radians(a), 0, 0)

shots = [  # (file, pose, yaw, ortho scale, camera z, resolution)
    ('face_front', 'stand', 0, 0.44, face_z, (560, 560)),
    ('face_34', 'stand', -35, 0.44, face_z, (560, 560)),
    ('face_side', 'stand', -90, 0.44, face_z, (560, 560)),
    ('stand', 'stand', -24, top * 1.08, top * 0.5, (420, 760)),
    ('run', 'run', -24, top * 1.08, top * 0.5, (420, 760)),
    ('kick', 'kick', -24, top * 1.08, top * 0.5, (420, 760)),
    ('side', 'stand', -90, top * 1.08, top * 0.5, (420, 760)),
    ('back', 'stand', 155, top * 1.08, top * 0.5, (420, 760)),
]
GH = 250
game_scale = top * GH / KID_PX
shots += [('game_stand', 'idle', 66, game_scale, game_scale * 0.5 - 0.02 * top, (150, GH)),
          ('game_run', 'run', 66, game_scale, game_scale * 0.5 - 0.02 * top, (150, GH))]
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_review_tmp')
os.makedirs(tmp, exist_ok=True)
files = []
for name, p, yaw, scale, z, (rx, ry) in shots:
    pose(p)
    rig.rotation_euler = (0, 0, math.radians(yaw))
    cam.data.ortho_scale = scale
    cam.location = (0, -5, z); cam.rotation_euler = (math.radians(90), 0, 0)
    S.render.resolution_x, S.render.resolution_y = rx, ry
    game = name.startswith('game')
    S.render.film_transparent = game
    # in-game: the outline is a constant fraction of the screen height
    sol.thickness = OUTLINE * 920 / KID_PX * top if game else (0.0022 if name.startswith('face') else 0.0045)
    S.render.filepath = os.path.join(tmp, name + '.png'); bpy.ops.render.render(write_still=True)
    files.append(S.render.filepath)

from PIL import Image, ImageDraw
ims = {os.path.basename(f)[:-4]: Image.open(f).convert('RGBA') for f in files}
W = 420 * 5; H = 560 + 760 + 300
sheet = Image.new('RGB', (W, H), (62, 62, 66))
x = 0
for k in ('face_front', 'face_34', 'face_side'):
    sheet.paste(ims[k].convert('RGB'), (x, 0)); x += 560
x = 0
for k in ('stand', 'run', 'kick', 'side', 'back'):
    sheet.paste(ims[k].convert('RGB'), (x, 560)); x += 420

def stand_in(w, h):
    """A busy street stand-in: shop fronts in mixed colours over pale paving."""
    im = Image.new('RGB', (w, h), (205, 200, 190)); d = ImageDraw.Draw(im)
    cols = [(178, 60, 52), (232, 196, 90), (70, 120, 80), (220, 220, 214), (60, 70, 96), (196, 150, 110)]
    for i in range(0, w, 70):
        d.rectangle([i, 0, i + 70, h - 60], fill=cols[(i // 70) % len(cols)])
        d.rectangle([i + 10, 40, i + 60, 120], fill=(40, 46, 60))
    d.rectangle([0, h - 60, w, h], fill=(214, 210, 200))
    return im

# in-game strip: each background cut to 700 x 300 (feet 30 px above its bottom)
backs = []
for b in bgs[:3]:
    try:
        im = Image.open(b).convert('RGB')
        if im.size != (700, 300):     # a whole screenshot: scale to 920 px tall, cut round its middle
            im = im.resize((int(im.width * 920 / im.height), 920), Image.LANCZOS)
            cx = im.width // 2 + 250 * (len(backs) - 1)
            im = im.crop((cx - 350, 780 - 300 + 10, cx + 350, 780 + 10))
        backs.append(im)
    except Exception as ex:
        print('background', b, ex)
while len(backs) < 3: backs.append(stand_in(700, 300))
for i, bg in enumerate(backs):
    canvas = bg.copy().convert('RGBA')
    for k, dx in (('game_stand', 210), ('game_run', 420)):
        g = ims[k]
        canvas.alpha_composite(g, (dx, 300 - 30 - GH + int(0.02 * GH)))
    sheet.paste(canvas.convert('RGB'), (i * 700, 560 + 760))
sheet.save(out)
print('sheet', out)
