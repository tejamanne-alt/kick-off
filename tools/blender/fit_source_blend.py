# A character's original FBX opened as the game's tools import it (polish_character.py's axes) and saved as a .blend,
# its objects as named in the FBX ('Kid', 'KidRig', the Bag_ meshes): what meshy_bag.py's fit takes, in polish_all.py's
# step that fits the extra bags onto each kid's original before its polish. (fbx_to_blend.py is another tool: a
# review-ready .blend with its materials, for the player cards and reviews.)
#   blenv/bin/python fit_source_blend.py -- /abs/Kid.fbx /abs/Kid.blend
import sys, bpy
fbx, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X')
bpy.ops.wm.save_as_mainfile(filepath=out)
print('[fit_source_blend]', fbx, '->', out, ', '.join(o.name for o in bpy.data.objects))
