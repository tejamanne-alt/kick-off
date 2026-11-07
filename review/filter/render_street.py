# Renders a street from the game's own models (buildings kit, a car, the playable kids, the ball)
# from the game's camera, with the game's toon look, plus the data the comic filter reads:
#   blenv/bin/python render_street.py -- <models dir> <out dir> [width height]
# Writes colour.png (the picture), normal.png (view-space normals, 0.5 + 0.5 n), data.png
# (r, g: depth as a fraction of FAR in two 8-bit halves, b: the comic mask = ToonCharacter's _ComicWorld,
# 1 street / 0 figure).
import bpy, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
MODELS, OUT = args[0], args[1]
RW, RH = (int(args[2]), int(args[3])) if len(args) > 3 else (1920, 1080)
FAR = 300.0
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
SUN = (1.0, 0.97, 0.92)
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()   # WorldLook's sun (Unity x, z, y -> Blender x, -z... as in review_teen)


def image(path):
    return bpy.data.images.load(path, check_existing=True)


def toon_material(name, tex=None, colour=(1, 1, 1), shade=(0.62, 0.66, 0.8), mask=1.0, use_vcol=False, lighting=1.0):
    """Toon / ToonCharacter as nodes: albedo x lerp(shade, sun, smoothstep(-0.02, 0.06, N.L)).
    The comic mask is kept as a custom property (read by the data override)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    m['comicworld'] = mask
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    alb = nt.nodes.new('ShaderNodeRGB'); alb.outputs[0].default_value = tuple(colour) + (1,)
    albedo = alb.outputs[0]
    if tex is not None:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex; t.interpolation = 'Closest' if False else 'Linear'
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
        nt.links.new(t.outputs['Color'], mul.inputs['A']); nt.links.new(albedo, mul.inputs['B'])
        albedo = mul.outputs['Result']
    if use_vcol:
        vc = nt.nodes.new('ShaderNodeVertexColor')
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
        nt.links.new(albedo, mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
        albedo = mul.outputs['Result']
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    L = nt.nodes.new('ShaderNodeCombineXYZ')
    L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
    lit = nt.nodes.new('ShaderNodeMapRange'); lit.interpolation_type = 'SMOOTHSTEP'
    lit.inputs['From Min'].default_value = -0.02; lit.inputs['From Max'].default_value = 0.06
    nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
    sh = tuple(s + (1 - s) * (1 - lighting) for s in shade)
    band = nt.nodes.new('ShaderNodeMix'); band.data_type = 'RGBA'
    band.inputs['A'].default_value = sh + (1,); band.inputs['B'].default_value = SUN + (1,)
    nt.links.new(lit.outputs['Result'], band.inputs['Factor'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(albedo, mul.inputs['A']); nt.links.new(band.outputs['Result'], mul.inputs['B'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mul.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def outline(obj, width, mask):
    """ToonCharacter's ink hull: back faces pushed out (a flipped solidify)."""
    ol = bpy.data.materials.new(obj.name + 'Ink'); ol.use_nodes = True; ol.use_backface_culling = True
    ol['comicworld'] = mask
    e = ol.node_tree.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.02, 0.016, 0.03, 1)
    ol.node_tree.links.new(e.outputs[0], ol.node_tree.nodes['Material Output'].inputs['Surface'])
    obj.data.materials.append(ol)
    sol = obj.modifiers.new('ink', 'SOLIDIFY'); sol.thickness = width; sol.offset = 1
    sol.use_flip_normals = True; sol.material_offset = len(obj.data.materials) - 1


def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def place(objs, loc, yaw=0.0, height=None, front=False):
    roots = [o for o in objs if o.parent is None]
    meshes = [o for o in objs if o.type == 'MESH']
    bpy.context.view_layer.update()
    if height is not None:
        zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
        h = max(zs) - min(zs)
        for r in roots:
            r.scale = r.scale * (height / h)
    bpy.context.view_layer.update()
    for r in roots:
        r.rotation_euler.z += math.radians(yaw)
    bpy.context.view_layer.update()
    pts = [(o.matrix_world @ Vector(c)) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = Vector(((mn.x + mx.x) / 2, mn.y if front else (mn.y + mx.y) / 2, mn.z))
    for r in roots:
        r.location += Vector(loc) - centre
    bpy.context.view_layer.update()


def skin(objs, mat):
    for o in objs:
        if o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(mat)


# ---- the street ----
paving = toon_material('Paving', colour=(0.74, 0.71, 0.70))
road = toon_material('Road', colour=(0.47, 0.43, 0.45))
kerb = toon_material('Kerb', colour=(0.82, 0.8, 0.78))
wallm = toon_material('Wall', colour=(0.74, 0.69, 0.6))
capm = toon_material('Cap', colour=(0.85, 0.82, 0.77))
box('Footpath', (0, 0.0, -0.05), (60, 5.0, 0.1), paving)
box('Kerb', (0, -2.6, -0.02), (60, 0.25, 0.16), kerb)
box('Road', (0, -6.0, -0.12), (60, 6.5, 0.1), road)
shadem = toon_material('CanopyShade', colour=(0.2, 0.2, 0.3), lighting=0.0, shade=(1, 1, 1))
for i, (x, w) in enumerate([(-7.5, 4.0), (-4.2, 1.6), (7.0, 5.0)]):
    box('Shade%d' % i, (x, -2.0, 0.003), (w, 7.0, 0.004), shadem)
# a block wall with a cap and posts, in front of the houses
for i in range(-6, 7):
    x = i * 3.0
    box('WallSeg%d' % i, (x, 2.7, 0.65), (2.85, 0.2, 1.3), wallm)
    box('WallCap%d' % i, (x, 2.7, 1.33), (2.9, 0.26, 0.08), capm)
    box('Post%d' % i, (x + 1.47, 2.7, 0.75), (0.32, 0.32, 1.5), capm)

atlas = image(os.path.join(MODELS, 'Buildings', 'BuildingsAtlas.png'))
bmat = toon_material('Buildings', tex=atlas, shade=(0.6, 0.64, 0.78), use_vcol=False)
for name, x, y in [('HouseFlat', -9.5, 4.2), ('HouseGable', -0.5, 5.0), ('ShopKonbini', 9.5, 4.2)]:
    objs = import_fbx(os.path.join(MODELS, 'Buildings', name + '.fbx'))
    skin(objs, bmat)
    place(objs, (x, y, 0.0), front=True)

# a car on the road, drawn like the street by the filter (_ComicWorld 1)
car = import_fbx(os.path.join(MODELS, 'Cars', 'Hatch.fbx'))
cmat = toon_material('Car', tex=image(os.path.join(MODELS, 'Cars', 'HatchAtlas.png')), shade=(0.66, 0.68, 0.86), mask=1.0)
skin(car, cmat)
place(car, (3.6, -4.6, 0.0), yaw=90)
for o in car:
    if o.type == 'MESH':
        outline(o, 0.03, 1.0)

# the kids and the ball: figures (_ComicWorld 0), their own ink outline
POSES = {'run': {'UpperLeg.R': -40, 'LowerLeg.R': 60, 'UpperLeg.L': 38, 'LowerLeg.L': 92, 'UpperArm.R': 34,
                 'LowerArm.R': -85, 'UpperArm.L': -30, 'LowerArm.L': -70, 'Bag': 10},
         'kick': {'UpperLeg.R': -80, 'LowerLeg.R': 5, 'UpperLeg.L': 10, 'LowerLeg.L': 14, 'UpperArm.R': 45,
                  'UpperArm.L': -60, 'LowerArm.L': -35}}


def kid(model, loc, yaw, pose, height):
    objs = import_fbx(os.path.join(MODELS, model + '.fbx'))
    mat = toon_material(model, tex=image(os.path.join(MODELS, model + 'Atlas.png')), shade=(0.68, 0.66, 0.86), mask=0.0, use_vcol=True)
    skin(objs, mat)
    for o in objs:
        if o.type == 'ARMATURE':
            for pb in o.pose.bones:
                pb.rotation_mode = 'XYZ'
            for b, a in POSES[pose].items():
                if b in o.pose.bones:
                    o.pose.bones[b].rotation_euler = (math.radians(a), 0, 0)
    place(objs, loc, yaw=yaw, height=height)
    for o in objs:
        if o.type == 'MESH':
            outline(o, 0.012, 0.0)
    return objs


kid('Boy', (0.6, -0.4, 0.0), 66, 'kick', 1.62)
kid('PrimaryGirl', (-2.4, 0.6, 0.0), 66, 'run', 1.3)

# the ball: white with dark patches (as SphereShape paints it)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.17, location=(-0.35, -0.55, 0.62))
ball = bpy.context.object; ball.name = 'Ball'
bpy.ops.object.shade_smooth()
white = toon_material('BallWhite', colour=(0.95, 0.95, 0.95), shade=(0.7, 0.7, 0.86), mask=0.0)
black = toon_material('BallBlack', colour=(0.08, 0.08, 0.1), shade=(0.7, 0.7, 0.86), mask=0.0)
ball.data.materials.append(white); ball.data.materials.append(black)
import random
random.seed(3)
centres = [Vector(v) for v in [(0, 0, 1), (0.89, 0, 0.45), (0.28, 0.85, 0.45), (-0.72, 0.53, 0.45), (-0.72, -0.53, 0.45),
                               (0.28, -0.85, 0.45), (0, 0, -1), (-0.89, 0, -0.45), (0.72, 0.53, -0.45), (0.72, -0.53, -0.45),
                               (-0.28, 0.85, -0.45), (-0.28, -0.85, -0.45)]]
for f in ball.data.polygons:
    n = f.normal.normalized()
    if max(n.dot(c.normalized()) for c in centres) > 0.93:
        f.material_index = 1
outline(ball, 0.008, 0.0)

# ---- camera: the game's (34 degree FOV, about 12 m back, under 3 m up, a touch down) ----
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(34)
cam.data.clip_start = 0.3; cam.data.clip_end = FAR
cam.location = (0.0, -12.0, 2.6)
d = Vector((0.0, 0.0, 1.6)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
bg = S.world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.045, 0.15, 0.42, 1)   # deep cobalt (linear)
S.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
S.render.resolution_x, S.render.resolution_y = RW, RH
S.render.image_settings.file_format = 'PNG'
S.render.dither_intensity = 0.0   # no dither noise in the data images
try:
    S.eevee.taa_render_samples = 8
except Exception:
    pass


def render(path, view='Standard', depth16=False):
    S.view_settings.view_transform = view
    S.render.image_settings.color_depth = '16' if depth16 else '8'
    S.render.filepath = path
    bpy.ops.render.render(write_still=True)



# ---- data passes: one override material, emission = the data, no colour management ----
def data_material(kind):
    m = bpy.data.materials.new('Data' + kind); m.use_nodes = True; m.use_backface_culling = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    if kind == 'normal':
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
        nt.links.new(geo.outputs['Normal'], vt.inputs[0])
        # Blender's camera space looks down -Z; Unity's view-space normals face +z toward the camera too
        mp = nt.nodes.new('ShaderNodeVectorMath'); mp.operation = 'MULTIPLY_ADD'
        mp.inputs[1].default_value = (0.5, 0.5, 0.5); mp.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(vt.outputs[0], mp.inputs[0]); nt.links.new(mp.outputs[0], em.inputs['Color'])
    else:
        camd = nt.nodes.new('ShaderNodeCameraData')
        div = nt.nodes.new('ShaderNodeMath'); div.operation = 'DIVIDE'; div.inputs[1].default_value = FAR
        nt.links.new(camd.outputs['View Z Depth'], div.inputs[0])
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'OBJECT'; attr.attribute_name = 'comicworld'
        # depth in two 8-bit channels (as Unity's EncodeFloatRG): r = floor(d * 255) / 255, g = frac(d * 255)
        m255 = nt.nodes.new('ShaderNodeMath'); m255.operation = 'MULTIPLY'; m255.inputs[1].default_value = 255.0
        nt.links.new(div.outputs[0], m255.inputs[0])
        fl = nt.nodes.new('ShaderNodeMath'); fl.operation = 'FLOOR'; nt.links.new(m255.outputs[0], fl.inputs[0])
        hi = nt.nodes.new('ShaderNodeMath'); hi.operation = 'DIVIDE'; hi.inputs[1].default_value = 255.0; nt.links.new(fl.outputs[0], hi.inputs[0])
        lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'FRACT'; nt.links.new(m255.outputs[0], lo.inputs[0])
        comb = nt.nodes.new('ShaderNodeCombineColor')
        nt.links.new(hi.outputs[0], comb.inputs[0])
        nt.links.new(lo.outputs[0], comb.inputs[1])
        nt.links.new(attr.outputs['Fac'], comb.inputs[2])
        nt.links.new(comb.outputs[0], em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m


# the mask as an object property (the instancer attribute reads the object's custom property)
for o in bpy.data.objects:
    if o.type == 'MESH':
        mats = [m for m in o.data.materials if m is not None]
        o['comicworld'] = float(min((m.get('comicworld', 1.0) for m in mats), default=1.0))

NORMAL, DATA = data_material('normal'), data_material('data')


def render_set(suffix):
    bg = S.world.node_tree.nodes['Background'].inputs['Color']
    S.view_layers[0].material_override = None
    bg.default_value = (0.045, 0.15, 0.42, 1); S.render.filter_size = 1.5; S.eevee.taa_render_samples = 8
    render(os.path.join(OUT, 'colour%s.png' % suffix))
    bg.default_value = (0.5, 0.5, 1.0, 1)
    S.view_layers[0].material_override = NORMAL
    render(os.path.join(OUT, 'normal%s.png' % suffix), view='Raw')
    bg.default_value = (1.0, 0.0, 1.0, 1)
    S.view_layers[0].material_override = DATA
    S.render.filter_size = 0.01; S.eevee.taa_render_samples = 1
    render(os.path.join(OUT, 'data%s.png' % suffix), view='Raw')


render_set('')
# A close-up on the two kids' faces: the same camera, nearer (as the menus and a zoomed camera see them).
cam.location = (-0.9, -4.2, 1.45)
d = Vector((-0.9, 0.0, 1.25)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.angle_y = math.radians(22)
render_set('_close')
print('rendered', OUT)
