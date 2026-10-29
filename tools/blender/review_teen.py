# Renders a review sheet of a built teen with the game's look (two cel bands from a sun, a
# cool shadow tint, an ink outline):
#   blenv/bin/python review_teen.py -- /abs/Girl.blend /abs/girl_sheet.png
# Top row: face close-ups (front, three-quarter, profile). Middle: full body standing
# three-quarter, running, kicking, side, back. Bottom-right: the character at roughly
# in-game size (about 150 px tall), where the silhouette and colours must still read.
import bpy, math, sys, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene
kid = bpy.data.objects['Kid']; rig = bpy.data.objects['KidRig']

# Toon material: lit / shadow bands from a sun, vertex colour x atlas.
mat = kid.data.materials[0]; nt = mat.node_tree
mix = [n for n in nt.nodes if n.type == 'MIX'][0]
diff = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(mix.outputs['Result'], diff.inputs['Color'])
s2r = nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(diff.outputs[0], s2r.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
ramp.color_ramp.elements[0].color = (0.74, 0.72, 0.9, 1); ramp.color_ramp.elements[1].position = 0.18; ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s2r.outputs[0], bw.inputs[0]); nt.links.new(bw.outputs[0], ramp.inputs[0])
m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
nt.links.new(mix.outputs['Result'], m2.inputs['A']); nt.links.new(ramp.outputs['Color'], m2.inputs['B'])
em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(m2.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.12, 0.09, 0.11, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
kid.data.materials.append(ol)
sol = kid.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = 0.005; sol.offset = 1; sol.use_flip_normals = True; sol.material_offset = 1
mat.use_backface_culling = True
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(-30))
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.type = 'ORTHO'

# Head height for framing the close-ups.
zs = [(kid.matrix_world @ v.co).z for v in kid.data.vertices]
top = max(zs)
head_z = rig.data.bones['Head'].head_local.z
face_z = head_z + 0.13

poses = {'stand': {},
         'run': {'UpperLeg.R': -40, 'LowerLeg.R': 60, 'UpperLeg.L': 38, 'LowerLeg.L': 92, 'UpperArm.R': 34, 'LowerArm.R': -85, 'UpperArm.L': -30, 'LowerArm.L': -70},
         'kick': {'UpperLeg.R': -80, 'LowerLeg.R': 5, 'UpperLeg.L': 10, 'LowerLeg.L': 14, 'UpperArm.R': 45, 'UpperArm.L': -60, 'LowerArm.L': -35}}

def pose(name):
    for pb in rig.pose.bones: pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
    for b, a in poses[name].items(): rig.pose.bones[b].rotation_euler = (math.radians(a), 0, 0)

shots = [  # (file, pose, yaw, ortho scale, camera z, resolution)
    ('face_front', 'stand', 0, 0.5, face_z, (560, 560)),
    ('face_34', 'stand', -35, 0.5, face_z, (560, 560)),
    ('face_side', 'stand', -90, 0.5, face_z, (560, 560)),
    ('stand', 'stand', -24, top * 1.08, top * 0.5, (420, 760)),
    ('run', 'run', -24, top * 1.08, top * 0.5, (420, 760)),
    ('kick', 'kick', -24, top * 1.08, top * 0.5, (420, 760)),
    ('side', 'stand', -90, top * 1.08, top * 0.5, (420, 760)),
    ('back', 'stand', 155, top * 1.08, top * 0.5, (420, 760)),
    ('game', 'run', -80, top * 1.25, top * 0.5, (100, 180)),
]
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_review_tmp')
os.makedirs(tmp, exist_ok=True)
files = []
for name, p, yaw, scale, z, (rx, ry) in shots:
    pose(p)
    rig.rotation_euler = (0, 0, math.radians(yaw))
    cam.data.ortho_scale = scale
    cam.location = (0, -5, z); cam.rotation_euler = (math.radians(90), 0, 0)
    S.render.resolution_x, S.render.resolution_y = rx, ry
    sol.thickness = 0.0025 if name.startswith('face') else 0.005
    S.render.filepath = os.path.join(tmp, name + '.png'); bpy.ops.render.render(write_still=True)
    files.append(S.render.filepath)

from PIL import Image
ims = {os.path.basename(f)[:-4]: Image.open(f).convert('RGB') for f in files}
W = 420 * 5; H = 560 + 760
sheet = Image.new('RGB', (W, H), (62, 62, 66))
x = 0
for k in ('face_front', 'face_34', 'face_side'):
    sheet.paste(ims[k], (x, 0)); x += 560
g = ims['game']; sheet.paste(g, (W - g.width - 20, 560 - g.height - 20))
x = 0
for k in ('stand', 'run', 'kick', 'side', 'back'):
    sheet.paste(ims[k], (x, 560)); x += 420
sheet.save(out)
print('sheet', out)
