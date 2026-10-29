# Shared helpers for the asset kits (kit_*.py). Read docs/ART_DIRECTION.md first.
#
# A kit script builds several models and writes, into one output directory:
#   <Model>.fbx         one per model: a single root object named <Model>, children allowed
#                       (wheels, moving parts, Attach.* empties), front facing -Y, origin on the ground
#   <Kit>Atlas.png      the kit's shared texture (plain white corner at UV (0.97, 0.03))
#   <Kit>.json          the manifest: per model its size, triangle count, recolour parts and extras
#   <Kit>.blend         everything, for review_kit.py
#
# Colours passed to colorize() are Blender's scene-linear values (what `.color` takes); the vertex
# colours stored in the FBX, and so Unity's mesh.colors, are those values sRGB-encoded. The manifest
# stores part base colours sRGB-encoded too (srgb()), so the game's recolour compares like with like.
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix

C = bpy.context
WHITE_UV = (0.97, 0.03)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_obj(name, me):
    o = bpy.data.objects.new(name, me)
    C.scene.collection.objects.link(o)
    return o


def activate(o):
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True)
    C.view_layer.objects.active = o


def finish(o, smooth_angle=40.0):
    """Curves to meshes, apply transform and modifiers, then smooth shading by angle (degrees;
    None for fully smooth, 0 for flat)."""
    activate(o)
    if o.type == 'CURVE':
        bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    if smooth_angle is None:
        bpy.ops.object.shade_smooth()
    elif smooth_angle <= 0:
        bpy.ops.object.shade_flat()
    else:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
        # The operator may add a modifier; bake it so the FBX carries the split normals.
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    return o


def srgb(rgb):
    """Scene-linear -> sRGB-encoded (what the FBX vertex colours and Unity hold)."""
    return [round(12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055, 4) for c in rgb[:3]]


def colorize(o, color, part=0, uv=None):
    """Per face-corner vertex colour, atlas UV (UV0) and recolour part id (UV2.x).
    color: an RGBA tuple, or fn(world_co, world_normal) -> RGBA (scene-linear).
    part:  an int, or fn(world_co, world_normal) -> int.
    uv:    None for the white corner, or fn(world_co, world_normal) -> (u, v)."""
    me = o.data
    if not me.color_attributes:
        me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    col = me.color_attributes[0]
    while len(me.uv_layers) < 2:
        me.uv_layers.new()
    uv0, uv1 = me.uv_layers[0], me.uv_layers[1]
    mw = o.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    for poly in me.polygons:
        n = (nmat @ poly.normal).normalized()
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            col.data[li].color = color(co, n) if callable(color) else color
            uv0.data[li].uv = uv(co, n) if uv else WHITE_UV
            uv1.data[li].uv = (part(co, n) if callable(part) else part, 0)
    return o


def join(objs, name):
    """Join meshes into one object called name (the first keeps its origin)."""
    objs = [o for o in objs if o is not None]
    for x in C.scene.objects: x.select_set(False)
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = C.view_layer.objects.active
    o.name = name
    o.data.name = name
    return o


def attach(parent, name, location):
    """An empty (Attach.<name>) parented to the model, marking a point the game uses."""
    e = bpy.data.objects.new('Attach.' + name, None)
    C.scene.collection.objects.link(e)
    e.empty_display_size = 0.1
    e.location = location
    e.parent = parent
    return e


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons) if o.type == 'MESH' else 0


def tree_tris(root):
    return tris(root) + sum(tree_tris(c) for c in root.children)


def material(name, atlas_path):
    """Vertex colour x atlas, diffuse (used by the review renders and stored in the .blend)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfDiffuse')
    vc = nt.nodes.new('ShaderNodeVertexColor')
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1
    if atlas_path and os.path.exists(atlas_path):
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(atlas_path, check_existing=True)
        nt.links.new(tex.outputs['Color'], mul.inputs['A'])
    else:
        mul.inputs['A'].default_value = (1, 1, 1, 1)
    nt.links.new(vc.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bsdf.inputs['Color'])
    nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return m


def assign(root, mat):
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)


def export_model(root, path):
    """Export root and its children as one FBX (game conventions, as for the characters and cars)."""
    for x in C.scene.objects: x.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    C.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options='FBX_SCALE_ALL',
        add_leaf_bones=False, bake_anim=False, mesh_smooth_type='FACE', use_mesh_modifiers=True,
        axis_forward='-Z', axis_up='Y', path_mode='STRIP', object_types={'MESH', 'EMPTY', 'ARMATURE'})


class Manifest:
    """<Kit>.json: {"kit": .., "atlas": .., "models": {Name: {size, tris, parts, ...}}}."""
    def __init__(self, kit, atlas_name):
        self.data = {'kit': kit, 'atlas': atlas_name, 'models': {}}

    def add(self, root, parts=None, **extra):
        """parts: {part_id: scene-linear base colour}. extra: anything the game should know."""
        pts = []
        for o in [root] + list(root.children_recursive):
            if o.type == 'MESH':
                pts += [o.matrix_world @ v.co for v in o.data.vertices]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        entry = {'size': [round(hi.x - lo.x, 3), round(hi.y - lo.y, 3), round(hi.z - lo.z, 3)],
                 'min': [round(v, 3) for v in lo], 'max': [round(v, 3) for v in hi],
                 'tris': tree_tris(root),
                 'parts': {str(k): srgb(v) for k, v in (parts or {}).items()}}
        entry.update(extra)
        self.data['models'][root.name] = entry

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=1)
