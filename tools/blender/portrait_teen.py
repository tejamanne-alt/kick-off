# Renders a teen's portrait for the menus (Settings > Player, the player picker) in the game's
# look: ToonCharacter's two flat cel bands from the sun, cool sky-tinted shade, a rim of light
# and a dark ink outline, on a transparent background.
#   blenv/bin/python portrait_teen.py -- /abs/Boy.blend /abs/PlayerBoy.png [--yaw 28] [--size 512] [--full /abs/BoyFull.png] [--span-heads 2.3]
# The portrait is head to waist, a little turned toward the camera (--yaw, degrees; the boy
# and the girl turn toward each other on their side-by-side cards), square and power-of-two
# sized so the game imports it as a sprite without rescaling. --full also renders the whole
# figure in a keepy-uppy pose (knee up, arms out for balance) for key art and mock-ups. --span-heads N frames N times
# the height from the Head bone's joint to the crown instead of the teens' head to waist (the primary-school kids' bigger
# heads: --span-heads 2.3 gives the same framing, a head about half the card).
# Copy the portraits to Assets/_Game/Resources/UI/ (UiArtImportSettings makes them sprites).
import bpy, math, sys, os
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]
yaw = float(args[args.index('--yaw') + 1]) if '--yaw' in args else 28.0
size = int(args[args.index('--size') + 1]) if '--size' in args else 512
full = args[args.index('--full') + 1] if '--full' in args else None
span_heads = float(args[args.index('--span-heads') + 1]) if '--span-heads' in args else None
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene
kid = bpy.data.objects['Kid']; rig = bpy.data.objects['KidRig']

# ---- the game's toon shading (as in review_teen.py) ----
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
ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
rim = nt.nodes.new('ShaderNodeMapRange'); rim.interpolation_type = 'SMOOTHSTEP'
# ToonCharacter's rim: smoothstep(0.66, 0.8, 1 - N.V), tinted by the colour under it (lerp(albedo, 1, 0.45))
rim.inputs['From Min'].default_value = 0.34; rim.inputs['From Max'].default_value = 0.2
nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
side = nt.nodes.new('ShaderNodeMapRange'); side.inputs['From Min'].default_value = -0.35; side.inputs['From Max'].default_value = 0.65
side.inputs['To Min'].default_value = 0.4; side.inputs['To Max'].default_value = 1.0
nt.links.new(dot.outputs['Value'], side.inputs['Value'])
rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'
nt.links.new(rim.outputs['Result'], rk.inputs[0]); nt.links.new(side.outputs['Result'], rk.inputs[1])
rk2 = nt.nodes.new('ShaderNodeMath'); rk2.operation = 'MULTIPLY'; rk2.inputs[1].default_value = 0.22
nt.links.new(rk.outputs[0], rk2.inputs[0])
tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.inputs['Factor'].default_value = 0.45
nt.links.new(mix.outputs['Result'], tint.inputs['A']); tint.inputs['B'].default_value = (1, 1, 1, 1)
tsun = nt.nodes.new('ShaderNodeMix'); tsun.data_type = 'RGBA'; tsun.blend_type = 'MULTIPLY'; tsun.inputs['Factor'].default_value = 1
nt.links.new(tint.outputs['Result'], tsun.inputs['A']); tsun.inputs['B'].default_value = SUN + (1,)
add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
nt.links.new(tsun.outputs['Result'], add.inputs['B'])
nt.links.new(rk2.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
kid.data.materials.append(ol)
sol = kid.modifiers.new('outline', 'SOLIDIFY'); sol.offset = 1; sol.use_flip_normals = True; sol.material_offset = 1
mat.use_backface_culling = True
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
S.render.film_transparent = True
try: S.eevee.taa_render_samples = 16
except Exception: pass
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.type = 'ORTHO'
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()
L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR

zs = [(kid.matrix_world @ v.co).z for v in kid.data.vertices]
top = max(zs)
hips_z = rig.data.bones['Hips'].head_local.z


def pose(angles):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
    for b, a in angles.items():
        if isinstance(a, tuple): rig.pose.bones[b].rotation_euler = tuple(math.radians(v) for v in a)
        else: rig.pose.bones[b].rotation_euler = (math.radians(a), 0, 0)


def shoot(path, scale, z, res, outline):
    rig.rotation_euler = (0, 0, math.radians(yaw))
    cam.data.ortho_scale = scale
    cam.location = (0, -5, z); cam.rotation_euler = (math.radians(90), 0, 0)
    S.render.resolution_x, S.render.resolution_y = res
    sol.thickness = outline
    S.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('rendered', path)


# Head to waist: relaxed arms, a soft knee.
pose({'LowerLeg.R': 5, 'LowerLeg.L': 5, 'UpperArm.R': 6, 'UpperArm.L': -6, 'LowerArm.R': -16, 'LowerArm.L': -16, 'Head': (-4, 0, 0)})
span = (top - hips_z) * 0.66          # the top of the hair down to mid-chest
if span_heads: span = span_heads * (top - rig.data.bones['Head'].head_local.z)
shoot(out, span, top + span * 0.04 - span * 0.5, (size, size), 0.0036)

if full:
    # Keepy-uppy: the near knee up under the ball, arms out for balance.
    pose({'UpperLeg.R': -62, 'LowerLeg.R': 78, 'UpperLeg.L': 4, 'LowerLeg.L': 10,
          'UpperArm.R': (34, 0, 0), 'LowerArm.R': -40, 'UpperArm.L': (-30, 0, 0), 'LowerArm.L': -30, 'Head': (-12, 0, 0)})
    yaw = 62.0 if yaw >= 0 else -62.0     # more side-on, so the raised knee reads
    shoot(full, top * 1.12, top * 0.5, (int(size * 0.62), size), 0.0045)
