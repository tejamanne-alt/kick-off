# The app icon's scene: the walk to school. Max, the backpack boy (with the Kick Off backpack), kicks a football along the
# footpath on his way to school, the school ahead of him up the street, a picket fence, a post box and a tree along the
# way, in the game's toon look (ToonCharacter's two flat cel bands, cool shade, a warm rim, a dark ink outline). The sky
# is left transparent: app_icon_compose.py paints the morning sky, the sun and the speed lines behind and over it.
#   blenv/bin/python app_icon_scene.py -- /abs/rigged/BackpackBoy.blend /abs/icon_layers
#     -> icon_layers/scene.png (2048 x 2048, the sky transparent), ball_front.png (the ball alone), scene.json (where the ball, his foot and
#        the horizon land in the picture, as fractions, for the composer)
import bpy, bmesh, math, sys, os, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
KID_BLEND, OUT = args[0], args[1]
os.makedirs(OUT, exist_ok=True)
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Assets', '_Game', 'Art', 'Models')
SIZE = 2048

SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
SUNDIR = Vector((-0.35, -0.7, 0.62)).normalized()      # the morning sun low behind the camera, to the left


def lin(c):
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c[:3])


def toon(mat, colour_socket, rim=0.2, cutout=None):
    """The game's toon shading on a material: two cel bands from the sun, a cool shade, a warm rim; colour_socket gives
    the surface colour. cutout: an alpha socket (leaves) cut at 0.5."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    L = nt.nodes.new('ShaderNodeCombineXYZ')
    L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR
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
    nt.links.new(colour_socket, m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
    ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.interpolation_type = 'SMOOTHSTEP'
    rr.inputs['From Min'].default_value = 0.4; rr.inputs['From Max'].default_value = 0.22
    nt.links.new(ndv.outputs['Value'], rr.inputs['Value'])
    rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'; rk.inputs[1].default_value = rim
    nt.links.new(rr.outputs['Result'], rk.inputs[0])
    add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
    add.inputs['B'].default_value = (1.0, 0.86, 0.62, 1)
    nt.links.new(rk.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
    shader = em
    if cutout is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        step = nt.nodes.new('ShaderNodeMath'); step.operation = 'GREATER_THAN'; step.inputs[1].default_value = 0.5
        nt.links.new(cutout, step.inputs[0])
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(step.outputs[0], mix.inputs['Fac']); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
        shader = mix
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass
    nt.links.new(shader.outputs[0], out.inputs['Surface'])
    mat.use_backface_culling = True


def ink(obj, thickness):
    ol = bpy.data.materials.get('Outline')
    if ol is None:
        ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
        on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
        on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
    n = len(obj.material_slots)
    obj.data.materials.append(ol)
    sol = obj.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = thickness; sol.offset = 1
    sol.use_flip_normals = True; sol.material_offset = n


def flat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    c = m.node_tree.nodes.new('ShaderNodeRGB'); c.outputs[0].default_value = lin(rgb) + (1,)
    toon(m, c.outputs[0], rim=0.0)
    return m


# ------------------------------------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.render.engine = 'BLENDER_EEVEE'
S.view_settings.view_transform = 'Standard'
S.render.film_transparent = True
try:
    S.eevee.taa_render_samples = 32
except Exception:
    pass
S.world = bpy.data.worlds.new('w')
S.render.resolution_x = S.render.resolution_y = SIZE


def kit(kit_name, model, loc, rot_z=0.0, scale=1.0):
    """A model of the game's asset kits (Art/Models/<kit>/<model>.fbx): the kit's atlas times each part's colour from
    <kit>.json, as the game paints it."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(MODELS, kit_name, model + '.fbx'))
    new = [o for o in bpy.data.objects if o not in before]
    info = json.load(open(os.path.join(MODELS, kit_name, kit_name + '.json')))
    parts = info['models'][model].get('parts', {})
    atlas = bpy.data.images.load(os.path.join(MODELS, kit_name, info['atlas']), check_existing=True)
    atlas.alpha_mode = 'STRAIGHT'
    root = [o for o in new if o.parent is None]
    for o in new:
        if o.type != 'MESH':
            continue
        me = o.data
        # each part's colour as a corner colour, from the part index in the 'Part' UV map
        col = me.color_attributes.new('PartCol', 'BYTE_COLOR', 'CORNER')
        uvp = me.uv_layers.get('Part')
        for li in range(len(me.loops)):
            p = int(round(uvp.data[li].uv[0])) if uvp else 0
            rgb = parts.get(str(p), [1, 1, 1]) if p else [1, 1, 1]
            col.data[li].color = lin(rgb) + (1,)
        m = bpy.data.materials.new(kit_name + model); m.use_nodes = True
        nt = m.node_tree
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = atlas
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = me.uv_layers[0].name
        nt.links.new(uvn.outputs[0], tex.inputs[0])
        vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'PartCol'
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
        nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
        toon(m, mul.outputs['Result'], rim=0.08, cutout=tex.outputs['Alpha'] if kit_name == 'Plants' else None)
        me.materials.clear(); me.materials.append(m)
    for o in root:
        o.location = loc; o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], math.radians(rot_z))
        o.scale = tuple(v * scale for v in o.scale)
    return [o for o in new if o.type == 'MESH']


def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    o.data.materials.append(mat)
    return o


# The street, running along x (he runs toward +x, to school): the footpath he is on, a kerb, the road in front (toward
# the camera at -y), a grass verge and the fence behind him.
box('Road', (80, 14, 0.1), (10, -9.1, -0.05), flat('Road', (0.42, 0.44, 0.5)))
box('Kerb', (80, 0.25, 0.16), (10, -2.0, 0.0), flat('Kerb', (0.86, 0.85, 0.82)))
box('Path', (80, 3.8, 0.1), (10, 0.0, 0.0), flat('Path', (0.86, 0.79, 0.68)))
for i in range(-20, 41):                                       # the paving's joints
    box('Joint%d' % i, (0.04, 3.8, 0.11), (i * 1.2, 0.0, 0.0), flat('Joint', (0.72, 0.66, 0.57)))
box('Verge', (80, 30, 0.1), (10, 16.9, -0.02), flat('Verge', (0.36, 0.7, 0.33)))
box('Line', (80, 0.14, 0.11), (10, -9.0, 0.0), flat('Line', (0.97, 0.95, 0.86)))

for x in (-9.0, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0):
    kit('Street', 'PicketFence2', (x, 2.3, 0.0))
kit('Street', 'PostBox', (-4.2, 1.5, 0.0), rot_z=-15)
kit('Plants', 'BroadleafLarge', (-6.5, 4.5, 0.0))
kit('Buildings', 'School', (13.0, 15.0, 0.0), rot_z=-24)
kit('Street', 'StreetLamp', (6.2, -1.75, 0.0))

# ------------------------------------------------------------------------------------------------ Max
with bpy.data.libraries.load(KID_BLEND, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Kid', 'KidRig', 'Bag_KickOff')]
for o in dst.objects:
    S.collection.objects.link(o)
rig = bpy.data.objects['KidRig']; kid = bpy.data.objects['Kid']; bag = bpy.data.objects['Bag_KickOff']
H = 1.75 / max(v.co.z for v in kid.data.vertices)                # (the model is 2.14 units tall; Max stands 1.75 m)
rig.scale = (H, H, H)
rig.location = (-1.2, -0.2, 0.0)
rig.rotation_euler = (0, 0, math.radians(42))                   # facing up the street (+x), turned toward us
# The kick: the near (right) leg swung through, high and nearly straight, toes up; the far leg planted, knee soft; the
# far arm up and forward for balance, the near arm back; leaning back a touch into it, eyes on the ball.
POSE = {'Hips': (0, 0, 0), 'Spine': (-4, 0, 0), 'Chest': (-4, 0, 0),
        'UpperLeg.R': (-78, 0, 0), 'LowerLeg.R': (16, 0, 0), 'Foot.R': (-20, 0, 0),
        'UpperLeg.L': (12, 0, 0), 'LowerLeg.L': (24, 0, 0), 'Foot.L': (-6, 0, 0),
        'UpperArm.L': (-62, 0, 30), 'LowerArm.L': (-40, 0, 0), 'UpperArm.R': (40, 0, -24), 'LowerArm.R': (-30, 0, 0),
        'Neck': (6, -8, 0), 'Head': (10, -10, 0)}
for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
for b, a in POSE.items():
    if b in rig.pose.bones:
        rig.pose.bones[b].rotation_euler = tuple(math.radians(v) for v in a)
bpy.context.view_layer.update()
for o in (kid, bag):
    m = o.data.materials[0]
    mix = next(n for n in m.node_tree.nodes if n.type == 'MIX')
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            n.image.alpha_mode = 'CHANNEL_PACKED'
    toon(m, mix.outputs['Result'], rim=0.22)
    ink(o, 0.006 / H)

# ------------------------------------------------------------------------------------------------ the ball
import app_icon as ai                                            # (its football: a truncated icosahedron, toon shaded)
ai.SUNDIR = SUNDIR
ball = ai.football(0.11)
toe = rig.matrix_world @ rig.pose.bones['Foot.R'].tail
ball.location = toe + Vector((0.02, -0.4, 0.82))                # off his toe, rising up the street toward us
ball.rotation_euler = (math.radians(24), math.radians(-18), math.radians(22))
ink(ball, 0.006)

# ------------------------------------------------------------------------------------------------ camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 27
cam.location = Vector((-2.1, -2.0, 0.55))                        # low, close: he towers over us, the school up behind him
target = Vector((1.3, 2.6, 1.75))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
S.render.filepath = os.path.join(OUT, 'scene.png')
bpy.ops.render.render(write_still=True)
# The ball alone, for the composer to lay over its kick trail.
for o in S.objects:
    if o.type == 'MESH' and o is not ball:
        o.hide_render = True
S.render.filepath = os.path.join(OUT, 'ball_front.png')
bpy.ops.render.render(write_still=True)


def at(p):
    v = world_to_camera_view(S, cam, Vector(p))
    return [round(v.x, 4), round(1 - v.y, 4)]


r_px = (Vector(at(ball.location)) - Vector(at(ball.location + cam.matrix_world.to_3x3() @ Vector((0.11, 0, 0))))).length
json.dump({'ball': at(ball.location), 'ball_r': round(r_px, 4), 'toe': at(toe),
           'horizon': at(cam.location + (target - cam.location).normalized() * 1000)[1]}, open(os.path.join(OUT, 'scene.json'), 'w'))
print('rendered scene', open(os.path.join(OUT, 'scene.json')).read())
