# Renders the app icon's picture layer, in the game's toon look (ToonCharacter's two flat cel bands from the sun, cool
# shade, a rim of light), on a transparent background. The icon has no characters: the hero is the ball.
#   ball.png  the football alone, 2048 x 2048 (app_icon_compose.py draws its ink ring as a true circle)
#   blenv/bin/python app_icon.py -- $PWD/icon_layers
# Then app_icon_compose.py lays it over the sky, the sunburst and the pitch and writes every size the stores need.
import bpy, bmesh, math, sys, os
from mathutils import Vector


SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
SUNDIR = Vector((-0.5, -0.75, 0.55)).normalized()      # the morning sun high on the left, in front: the ball lit, a crescent of shade


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


def camera(S, loc, target, lens):
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
    cam.data.lens = lens
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return cam


# ---------------------------------------------------------------- the ball


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


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    out_dir = args[-1]
    os.makedirs(out_dir, exist_ok=True)
    S = fresh(2048)
    ball = football(1.0)
    ball.rotation_euler = (math.radians(24), math.radians(-18), math.radians(22))   # a pentagon facing us, a little up and left: it spins
    camera(S, (0, -9.0, 0), (0, 0, 0), 100)                                          # long lens: the ball nearly fills the frame
    S.render.filepath = os.path.join(out_dir, 'ball.png')
    bpy.ops.render.render(write_still=True)
    print('rendered ball')
