# Renders the app icon's two picture layers from the game's own models, in the game's toon look (ToonCharacter's two
# flat cel bands from the sun, cool shade, a rim of light and a dark ink outline), on transparent backgrounds:
#   kid.png   the teen boy running to the right (to school, as in the levels), head to thighs, 2048 x 2048
#   ball.png  the football alone, 1024 x 1024 (app_icon_compose.py draws its ink ring as a true circle)
#   blenv/bin/python app_icon.py -- $PWD/Boy.blend $PWD/icon_layers
# Then app_icon_compose.py lays them over the sky, the sun and the pitch and writes every size the stores need.
import bpy, bmesh, math, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
blend, out_dir = args[0], args[1]
os.makedirs(out_dir, exist_ok=True)

SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
SUNDIR = Vector((-0.55, -0.45, 0.7)).normalized()      # from behind his left shoulder: the morning sun is behind him


def lin(c):
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c[:3])


def fresh(size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    S = bpy.context.scene
    S.render.engine = 'BLENDER_EEVEE'
    S.view_settings.view_transform = 'Standard'
    S.render.film_transparent = True
    try:
        S.eevee.taa_render_samples = 32
    except Exception:
        pass
    S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
    S.render.resolution_x = S.render.resolution_y = size
    return S


def toon(mat, rim_strength=0.22):
    """The game's toon shading on a material, keeping its colour (the base colour's input or value)."""
    nt = mat.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    bsdf = next((n for n in nt.nodes if n.type in ('BSDF_DIFFUSE', 'BSDF_PRINCIPLED')), None)
    surface = out.inputs['Surface'].links[0].from_node if out.inputs['Surface'].is_linked else None
    color_in = None
    if bsdf is not None:
        sock = bsdf.inputs.get('Color') or bsdf.inputs.get('Base Color')
        if sock is not None and sock.is_linked:
            color_in = sock.links[0].from_socket
        elif sock is not None:
            rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = sock.default_value
            color_in = rgb.outputs[0]
    if color_in is None and surface is not None and surface.type == 'EMISSION':
        color_in = surface.inputs['Color'].links[0].from_socket if surface.inputs['Color'].is_linked else None
    if color_in is None:
        mix = next((n for n in nt.nodes if n.type == 'MIX'), None)          # the teens' atlas x vertex colour
        color_in = mix.outputs['Result'] if mix is not None else None
    if color_in is None:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (0.8, 0.8, 0.8, 1)
        color_in = rgb.outputs[0]
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
    nt.links.new(color_in, m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
    ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
    rim = nt.nodes.new('ShaderNodeMapRange'); rim.interpolation_type = 'SMOOTHSTEP'
    rim.inputs['From Min'].default_value = 0.4; rim.inputs['From Max'].default_value = 0.22
    nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
    rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'; rk.inputs[1].default_value = rim_strength
    nt.links.new(rim.outputs['Result'], rk.inputs[0])
    add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
    add.inputs['B'].default_value = (1.0, 0.86, 0.62, 1)                 # a warm rim from the sun behind him
    nt.links.new(rk.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    mat.use_backface_culling = True


def ink(obj, thickness):
    """The dark ink outline: an inverted hull (flipped, front faces culled) in the outline material."""
    ol = bpy.data.materials.get('Outline')
    if ol is None:
        ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
        on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
        on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
    n = len(obj.material_slots)
    obj.data.materials.append(ol)
    sol = obj.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = thickness; sol.offset = 1
    sol.use_flip_normals = True; sol.material_offset = n


def camera(S, loc, target, lens):
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
    cam.data.lens = lens
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return cam


# ---------------------------------------------------------------- the kid
S = fresh(2048)
with bpy.data.libraries.load(blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
for o in dst.objects:
    if o is not None and o.name not in S.collection.objects:
        S.collection.objects.link(o)
rig = bpy.data.objects['KidRig']; kid = bpy.data.objects['Kid']
# Sprinting to the right: the far fist pumped up by his chin, the near arm swinging back, the near leg striding forward,
# leaning into it, his face turned a little toward us. (Bone angles as the game's CharacterRig: X about the side axis,
# a negative upper limb swings forward; the head turns about its own Y.)
POSE = {'Spine': (10, 0, 0), 'Chest': (4, 0, 0),
        'UpperArm.R': (38, 0, -8), 'LowerArm.R': (-45, 0, 0), 'UpperArm.L': (-50, 0, 14), 'LowerArm.L': (-118, 0, 0),
        'Neck': (-2, -6, 0), 'Head': (-6, -14, 0),
        'UpperLeg.R': (-48, 0, 0), 'LowerLeg.R': (58, 0, 0), 'UpperLeg.L': (26, 0, 0), 'LowerLeg.L': (48, 0, 0)}
for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
for b, a in POSE.items():
    rig.pose.bones[b].rotation_euler = tuple(math.radians(v) for v in a)
rig.rotation_euler = (0, 0, math.radians(35))
bpy.context.view_layer.update()
toon(kid.data.materials[0])
ink(kid, 0.0085)
camera(S, (0.3, -2.25, 1.42), (0.02, 0, 1.53), 46)
S.render.filepath = os.path.join(out_dir, 'kid.png')
bpy.ops.render.render(write_still=True)
print('rendered kid')

# ---------------------------------------------------------------- the ball
S = fresh(1024)


def football(radius):
    """A truncated icosahedron (12 dark pentagons, 20 white hexagons) with grey seams round every panel, subdivided and
    blown out to a sphere so the panels keep straight, crisp edges."""
    me = bpy.data.meshes.new('Ball')
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=0, radius=1.0)
    bmesh.ops.bevel(bm, geom=list(bm.verts), offset=100.0 / 3.0, offset_type='PERCENT', segments=1, affect='VERTICES')
    for f in bm.faces:
        f.material_index = 1 if len(f.verts) == 5 else 0
    bmesh.ops.inset_individual(bm, faces=list(bm.faces), thickness=0.018, depth=0.0)
    for f in bm.faces:
        if len(f.verts) == 4:
            f.material_index = 2                                  # the inset rims are the seams
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=10, use_grid_fill=True)
    for v in bm.verts:
        v.co = v.co.normalized()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('Ball', me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    o.scale = (radius, radius, radius)
    for name, col in (('BallWhite', (0.95, 0.95, 0.94)), ('BallBlack', (0.08, 0.08, 0.1)), ('BallSeam', (0.5, 0.52, 0.58))):
        m = bpy.data.materials.new(name); m.use_nodes = True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(col) + (1,)
        me.materials.append(m)
        toon(m, 0.12)
    return o


ball = football(1.0)
ball.rotation_euler = (math.radians(30), math.radians(-12), math.radians(16))   # a pentagon facing us, a little up and left
camera(S, (0, -9.0, 0), (0, 0, 0), 100)                                          # long lens: the ball nearly fills the frame
S.render.filepath = os.path.join(out_dir, 'ball.png')
bpy.ops.render.render(write_still=True)
print('rendered ball')
