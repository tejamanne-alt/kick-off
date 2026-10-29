# Builds one of the two playable teens (original characters) in Blender:
#   blenv/bin/python teen.py -- /abs/path/Boy.fbx --boy
#   blenv/bin/python teen.py -- /abs/path/Girl.fbx --girl
# Writes <Name>.fbx, <Name>.blend, <Name>Atlas.png (the painted face atlas) and
# <Name>.json (the default outfit colours the game recolours from) next to the .fbx.
#
# The pieces live in modules: teen_body (joints, skin, proportions), teen_outfit (clothes,
# shoes, bag), teen_head (head and ears), teen_hair, face_teen (the face painting), with
# shared helpers in teen_lib. This file colours, rigs, joins and exports them.
import bpy, sys, os, json
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = sys.argv[sys.argv.index('--') + 1]
GIRL = '--girl' in sys.argv
NAME = 'Girl' if GIRL else 'Boy'
bpy.ops.wm.read_factory_settings(use_empty=True)

import importlib
import teen_lib, teen_body, teen_outfit, teen_head, teen_hair, face_teen
for m in (teen_lib, teen_body, teen_outfit, teen_head, teen_hair, face_teen): importlib.reload(m)
from teen_lib import C, activate, WHITE_UV

ATLAS = os.path.join(os.path.dirname(OUT), NAME + 'Atlas.png')
face_teen.paint(ATLAS, GIRL)

# ---------------- build ----------------
body = teen_body.build_body(GIRL)
pal = teen_outfit.palette(GIRL)
parts = [teen_lib.Part(body, teen_outfit.skin_color(GIRL), 0, 'body')]
parts += teen_outfit.build_outfit(GIRL, body)
parts += teen_head.build_head(GIRL, pal['skin'])
parts += teen_hair.build_hair(GIRL)

# ---------------- colours, UVs, part ids ----------------
def colorize(p):
    o = p.obj; me = o.data
    if not me.color_attributes: me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    col = me.color_attributes['Col']
    while len(me.uv_layers) < 2: me.uv_layers.new()
    uv0, uv1 = me.uv_layers[0], me.uv_layers[1]
    mw = o.matrix_world
    for poly in me.polygons:
        cen = mw @ poly.center
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            c = p.color(co, cen) if callable(p.color) else p.color
            col.data[li].color = c
            uv0.data[li].uv = p.uv(co) if p.uv else WHITE_UV
            uv1.data[li].uv = (p.part(co, cen) if callable(p.part) else p.part, 0)
for p in parts: colorize(p)

# ---------------- teen proportions ----------------
for p in parts:
    o = p.obj
    for v in o.data.vertices: v.co = teen_body.grow(o.matrix_world @ v.co, GIRL)
    o.matrix_world = Matrix()

# ---------------- armature ----------------
arm = bpy.data.armatures.new('Rig'); rig = teen_lib.new_obj('KidRig', arm); activate(rig); bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
def bone(n, h, t, parent=None):
    b = eb.new(n); b.head = teen_body.grow(Vector(h), GIRL); b.tail = teen_body.grow(Vector(t), GIRL)
    if parent: b.parent = eb[parent]
    return b
for n, h, t, parent in teen_body.bones(GIRL): bone(n, h, t, parent)
bh, bt = teen_outfit.bag_bone(GIRL)
bone('Bag', bh, bt, 'Hips')
# A marker in front of the face (no weights) so the game can tell which way the model faces.
bone('Nose', (0, -0.2, 1.42), (0, -0.26, 1.42), 'Head')
for b in eb: b.roll = 0
bpy.ops.object.mode_set(mode='OBJECT')

# Body weights from bone heat; clothes copy the body's weights; the rest follows one bone.
activate(body); rig.select_set(True); C.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
def rigid(o, bname):
    vg = o.vertex_groups.new(name=bname); vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
    o.parent = rig; m = o.modifiers.new('arm', 'ARMATURE'); m.object = rig
def transfer(o):
    m = o.modifiers.new('dt', 'DATA_TRANSFER'); m.object = body; m.use_vert_data = True; m.data_types_verts = {'VGROUP_WEIGHTS'}
    m.vert_mapping = 'POLYINTERP_NEAREST'; m.layers_vgroup_select_src = 'ALL'; m.layers_vgroup_select_dst = 'NAME'
    activate(o); bpy.ops.object.datalayout_transfer(modifier=m.name); bpy.ops.object.modifier_apply(modifier=m.name)
    o.parent = rig; a = o.modifiers.new('arm', 'ARMATURE'); a.object = rig
for p in parts[1:]:
    if p.bind == 'transfer': transfer(p.obj)
    elif callable(p.bind): p.bind(p.obj, rig)      # custom weights (e.g. a skirt that follows the legs)
    else: rigid(p.obj, p.bind)

# Join everything into one skinned mesh with the atlas material.
mat = bpy.data.materials.new('Kid'); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']; tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(ATLAS)
vc = nt.nodes.new('ShaderNodeVertexColor'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B']); nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
objs = [p.obj for p in parts]
for o in objs:
    o.data.materials.clear(); o.data.materials.append(mat)
for x in C.scene.objects: x.select_set(False)
for o in objs: o.select_set(True)
C.view_layer.objects.active = body; bpy.ops.object.join(); kid = C.object; kid.name = 'Kid'
mods = [m for m in kid.modifiers if m.type == 'ARMATURE']
for m in mods[1:]: kid.modifiers.remove(m)
mods[0].object = rig
tris = sum(len(p.vertices) - 2 for p in kid.data.polygons)
print('verts', len(kid.data.vertices), 'tris', tris)
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace('.fbx', '.blend'))
for x in C.scene.objects: x.select_set(False)
kid.select_set(True); rig.select_set(True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, apply_scale_options='FBX_SCALE_ALL', add_leaf_bones=False,
    bake_anim=False, mesh_smooth_type='FACE', use_mesh_modifiers=True, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X', path_mode='STRIP')
hair = teen_hair.hair_colors(GIRL)[0]
with open(OUT.replace('.fbx', '.json'), 'w') as f:
    json.dump({'top': pal['top'][:3], 'legwear': pal['legwear'][:3], 'hair': hair[:3], 'tris': tris}, f)
print('exported')
