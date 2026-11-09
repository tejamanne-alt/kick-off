# The five Locker Room bags' shared atlases with their gaps filled (polish_all.py): every kid's FBX carries a fitted
# copy of each bag with the same UVs, so one kid's copies give the islands. The atlas is RGBA (its alpha marks the
# recolourable cloth for ToonCharacter's _MaskTint), and both colour and alpha are pushed out into the gaps, so no mip
# level mixes a foreign colour, or a foreign mask, into a bag's edges.
#   blenv/bin/python polish_bags.py -- <kid.fbx> <atlas dir> <out dir> KickOff RaceCar ...
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polish_lib as pl

argv = sys.argv[sys.argv.index('--') + 1:]
fbx, src, out = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X')
for bag in argv[3:]:
    o = bpy.data.objects.get('Bag_' + bag)
    if o is None:
        print('[polish_bags] no Bag_%s in %s' % (bag, fbx)); continue
    name = 'Bag%sAtlas.png' % bag
    pl.save_png(pl.fill_atlas(o, os.path.join(src, name)), os.path.join(out, name))
    print('[polish_bags] filled', name)
