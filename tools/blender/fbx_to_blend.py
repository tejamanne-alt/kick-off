# A review-ready .blend (Kid + KidRig, the atlas times the vertex colours as meshy_boy makes it) from a shipped FBX and
# its atlas, for portrait_teen.py, review_teen.py and review_poses.py now that the source .blend files are not kept:
#   blenv/bin/python fbx_to_blend.py -- /abs/X.fbx /abs/XAtlas.png /abs/out.blend [--keep-bag Bag_KickOff|none]
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:]
fbx, atlas, out = argv[0], argv[1], argv[2]
keep = argv[argv.index('--keep-bag') + 1] if '--keep-bag' in argv else 'none'
models = os.path.dirname(fbx)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)


def atlas_material(name, png, alpha_packed=False):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']; tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(png)
    if alpha_packed: tex.image.alpha_mode = 'CHANNEL_PACKED'
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1
    nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
    return mat


for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    if o.name.startswith('Bag_'):
        if o.name != keep:
            bpy.data.objects.remove(o); continue
        o.data.materials.clear(); o.data.materials.append(atlas_material(o.name, os.path.join(models, 'Bag%sAtlas.png' % o.name[4:]), True))
    elif o.name == 'Kid':
        o.data.materials.clear(); o.data.materials.append(atlas_material('Kid', atlas))
for m in [m for m in bpy.data.materials if m.users == 0]: bpy.data.materials.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out, [o.name for o in bpy.data.objects])
