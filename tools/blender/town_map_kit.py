# The kit models for the town map (town_map.py): the game's own FBX files (Assets/_Game/Art/Models/<Kit>/<Name>.fbx)
# imported into the scene, joined into one mesh each, given the kit's material (vertex colour x atlas, with the
# plants' leaf-card cut-out), tinted if asked (the game's ModelTint rule: parts 1 to 3 take a colour and keep each
# vertex's brightness relative to the part's mean) and placed as linked duplicates, so a thousand trees cost one mesh.
#
# Conventions of the kits (docs/ART_DIRECTION.md): metres, Z up, the front of a model faces -Y, the origin is on the
# ground at the middle of the front. place() turns a model so that its front faces the direction you give.
import bpy, os, math
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Art', 'Models'))

_templates = {}     # (kit, name, tint key) -> bpy.types.Mesh
_info = {}          # (kit, name) -> dict(size, min, max)
_materials = {}     # atlas path -> material
_collection = None
CUTOUT_KITS = ('Plants',)
# How the shading is built for every kit material: see shade() below.
SUN_DIR = Vector((-0.5, -0.55, 0.9)).normalized()    # towards the sun (from the south-west, about 50 degrees up): town_map.py sets the lamp from it


def lin(c):
    """sRGB (0..1) -> scene-linear."""
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c[:3])


def fbx_path(kit, name):
    if kit == 'Chars':                       # the game's characters stand loose in the models folder (Kid.fbx, KidAtlas.png)
        return os.path.join(MODELS_DIR, name + '.fbx')
    return os.path.join(MODELS_DIR, kit, name + '.fbx')


def atlas_path(kit, name):
    if kit == 'Chars':
        return os.path.join(MODELS_DIR, name + 'Atlas.png')
    if kit == 'Cars':
        return os.path.join(MODELS_DIR, 'Cars', name + 'Atlas.png')
    return os.path.join(MODELS_DIR, kit, kit + 'Atlas.png')


def has(kit, name):
    return os.path.exists(fbx_path(kit, name))


def hidden_collection():
    global _collection
    if _collection is None or _collection.name not in bpy.data.collections:
        _collection = bpy.data.collections.new('town_templates')
        bpy.context.scene.collection.children.link(_collection)
        _collection.hide_render = True
        _collection.hide_viewport = True
    return _collection


def reset():
    """Forget everything (after bpy.ops.wm.read_factory_settings)."""
    global _collection
    _templates.clear(); _info.clear(); _materials.clear()
    _collection = None


def material(kit, name):
    """Vertex colour x atlas, diffuse; the plants' leaf cards are cut out by the atlas alpha."""
    path = atlas_path(kit, name)
    if path in _materials:
        return _materials[path]
    m = bpy.data.materials.new(os.path.basename(path))
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = 'Linear'
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    nt.links.new(uvn.outputs['UV'], tex.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
    surf = shade(nt, mul.outputs['Result'])
    if kit in CUTOUT_KITS:
        tex.image.alpha_mode = 'STRAIGHT'
        # The game's leaf-card cut-out: atlas alpha against 0.5 (Toon.shader _ALPHATEST_ON), drawn from both sides.
        mask = nt.nodes.new('ShaderNodeMath'); mask.operation = 'GREATER_THAN'; mask.inputs[1].default_value = 0.5
        nt.links.new(tex.outputs['Alpha'], mask.inputs[0])
        hole = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(mask.outputs[0], mix.inputs['Fac'])
        nt.links.new(hole.outputs[0], mix.inputs[1]); nt.links.new(surf, mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        for attr, val in (('surface_render_method', 'DITHERED'), ('use_transparent_shadow', True), ('use_backface_culling', False)):
            if hasattr(m, attr):
                setattr(m, attr, val)
    else:
        nt.links.new(surf, out.inputs['Surface'])
    _materials[path] = m
    return m


def shade(nt, color_socket):
    """The surface shader that every model and the ground use: a diffuse BSDF (sun, sky and cast shadows come from
    Eevee), kept as one function so the whole picture can change its look in one place."""
    d = nt.nodes.new('ShaderNodeBsdfDiffuse')
    nt.links.new(color_socket, d.inputs['Color'])
    return d.outputs['BSDF']


def _import_joined(path):
    """Import one FBX and return (mesh, size info): every mesh object of the file joined into one mesh, in the model's
    own space (the root's transform and the children's baked in), the Attach.* empties and the objects dropped."""
    before = set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o.name not in before]
    names = [o.name for o in new]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        mw = o.matrix_world.copy()
        o.data.transform(mw)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    keep = bpy.context.view_layer.objects.active
    me = keep.data
    me.name = os.path.splitext(os.path.basename(path))[0]
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    return me


def _pts(me):
    n = len(me.vertices)
    a = np.zeros(n * 3)
    me.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def _load(kit, name):
    key = (kit, name)
    if key in _info:
        return _templates[(kit, name, None)]
    path = fbx_path(kit, name)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    me = _import_joined(path)
    pts = _pts(me)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    _info[key] = dict(size=tuple(hi - lo), min=tuple(lo), max=tuple(hi))
    me.materials.clear()
    me.materials.append(material(kit, name))
    me.name = f'{kit}.{name}'
    _templates[(kit, name, None)] = me
    return me


def info(kit, name):
    _load(kit, name)
    return _info[(kit, name)]


def _tinted(kit, name, tints):
    """A copy of the mesh with parts 1..3 recoloured (tints: three sRGB colours or None; brightness kept)."""
    base = _load(kit, name)
    tints = list(tints) + [None] * (3 - len(tints))
    key = (kit, name, tuple(tuple(round(c, 3) for c in t) if t else None for t in tints))
    if key in _templates:
        return _templates[key]
    me = base.copy()
    me.name = f'{kit}.{name}.t{len(_templates)}'
    attr = me.color_attributes[0]
    n = len(me.loops)
    part = np.zeros(n * 2); me.uv_layers[1].data.foreach_get('uv', part)
    part = np.rint(part.reshape(-1, 2)[:, 0]).astype(int) - 1
    cols = np.zeros(n * 4); attr.data.foreach_get('color', cols); cols = cols.reshape(-1, 4)
    for p in range(3):
        if tints[p] is None:
            continue
        sel = part == p
        if not sel.any():
            continue
        mean = cols[sel, :3].mean(axis=0).sum() + 1e-4
        k = cols[sel, :3].sum(axis=1) / mean
        cols[sel, :3] = np.clip(np.array(lin(tints[p]))[None, :] * k[:, None], 0, 1)
    attr.data.foreach_set('color', cols.ravel())
    me.update()
    _templates[key] = me
    return me


def place(kit, name, x, y, face=0.0, scale=1.0, z=0.0, tints=None, collection=None, tilt=None, name_hint=None):
    """A linked duplicate of a kit model with its origin at (x, y, z) metres (x east, y north), turned so that its
    front faces the compass direction `face` (degrees; 0 = north (+Y), 90 = east, 180 = south (-Y), 270 = west: the
    direction a house looks AT the street). `scale` may be a number or (sx, sy, sz). tints: [part1, part2, part3] sRGB."""
    me = _load(kit, name) if not tints else _tinted(kit, name, tints)
    o = bpy.data.objects.new(name_hint or name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    o.location = (x, y, z)
    # the model's front is -Y: rotating by a about Z sends -Y to the heading whose bearing is `face`
    o.rotation_euler = (0, 0, math.radians(180.0 - face) if tilt is None else math.radians(180.0 - face))
    if isinstance(scale, (int, float)):
        o.scale = (scale, scale, scale)
    else:
        o.scale = scale
    return o
