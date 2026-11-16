# The strict review (docs/ASSET_REVIEW.md) of the Kamakura home as the game has it (Art/Models/Kamakura/KmHome.fbx, installed
# by kit_buildings_km.py --install-home: the house and its fence, without the garden cut from the picture): its eight views
# and its checks, added to the props review (review/kamakura/props: views/KmHome.jpg, source/KmHome.jpg, review.json).
#   blenv/bin/python review_km_home.py -- /abs/Assets/_Game/Art/Models/Kamakura /abs/review/kamakura/props
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index('--') + 1:]
MODELS, REVIEW = args[0], args[1]
sys.argv = [sys.argv[0], '--', os.path.join(HERE, 'out', 'kamakura')]     # the kit module reads its own arguments
import bpy                                     # noqa: E402
from PIL import Image                          # noqa: E402
import asset_review as AR                      # noqa: E402
import kit_buildings_km as KB                  # noqa: E402
import kit_lib as K                            # noqa: E402

K.reset()
info = json.load(open(os.path.join(MODELS, 'Kamakura.json')))['models']['KmHome']
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=os.path.join(MODELS, 'KmHome.fbx'))
new = [o for o in bpy.data.objects if o not in before]
for o in [o for o in new if o.name.startswith('Attach')]:
    new.remove(o)
    bpy.data.objects.remove(o)
root = next(o for o in new if o.parent is None)
root.name = 'KmHome'
mat = KB.unlit(os.path.join(MODELS, info['texture']))
for o in new:
    if o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(mat)
root.location = (0, 0, 0)
bpy.context.view_layer.update()
os.makedirs(os.path.join(REVIEW, 'views'), exist_ok=True)
AR.eight_views(root, os.path.join(REVIEW, 'views', 'KmHome.jpg'), KB.render, cell_px=360,
               title='KmHome: every side (Right is the street side, as the game sees it)')
# its source: the photographic KM1-1's left, the house the model was projected from
src = Image.open(os.path.join(HERE, '..', '..', 'review', 'kamakura', 'refs', 'photo', 'KM1-1_hase_lanes.png')).convert('RGB')
src.crop(KB.HOME['crop']).save(os.path.join(REVIEW, 'source', 'KmHome.jpg'), quality=88)

import bmesh                                   # noqa: E402
open_edges = fins = 0
for o in new:
    if o.type != 'MESH':
        continue
    # counted with the FBX's seams merged: the export splits the surface along its texture seams (a clean prop came back
    # with 120 "open" edges: D32), which is no gap in the game
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_edges += sum(1 for e in bm.edges if e.is_boundary)
    fins += sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bm.free()
checks = {
    1: ('pass', 'the house, its skirt roof and gable, its upper storey and roof, its two air conditioners and its fence: each '
                'once (looked at in Top and Bottom)'),
    2: ('limit', '%d edges with one face, %d with three or more: built of boxes and roof faces without the faces no one can '
                 'see (the walls\' bottoms, the inside of the fence\'s boards), as approved; seen from the street and from '
                 'above, no gap shows' % (open_edges, fins)),
    3: ('pass', 'modelled from boxes and roof faces measured off the photographic KM1-1 (about 120 px to the metre)'),
    4: ('limit', 'the street side is the picture itself; its sides, back and roofs away from the street take KM-P3\'s '
                 'photographic boards and tiles in the house\'s colours (no view of their own)'),
    5: ('pass', '%.2f x %.2f x %.2f m, %d triangles (its budget 1,500; a house\'s 5,000), the kit\'s 4096 atlas as its '
                'texture (to be cropped: docs/PERFORMANCE.md)' % (tuple(info['real_size']) + (info['tris'],))),
    6: ('pass', 'its outline the picture\'s; the pots, plants and bicycle in front of the fence painted out of it and stood '
                'in front as their own models'),
    7: ('pass', 'no holes in what the street sees'),
    8: ('pass', 'the pots, the persimmon, the bicycle, the letterbox and the outdoor unit are their own models'),
    9: ('pass', 'the photographic KM1-1, in KM-0\'s look'),
    10: ('pass', 'solid and whole'),
    11: ('pass', 'no brand or logo'),
    12: ('pass', 'the power lines taken off its roof (dewire), no sky on its roof\'s edge (unsky)'),
    13: ('pass', 'the repairs: the garden painted out of the fence, the wires off the roof, the sky off the roof\'s edge'),
    14: ('n/a', 'no moving parts'), 15: ('n/a', 'no moving parts'), 16: ('n/a', 'no feet'), 17: ('n/a', 'one piece'),
}
path = os.path.join(REVIEW, 'review.json')
review = json.load(open(path))
names = KB.AR_CHECK_NAMES
review['KmHome'] = dict(id='KM-B01', sheet='photo/KM1-1 (left): the house, its entrance and its fence',
                        size=info['real_size'], tris=info['tris'], motions=[],
                        checks=[[i, names[i - 1], checks[i][0], checks[i][1]] for i in range(1, 18)])
json.dump(review, open(path, 'w'), indent=1, ensure_ascii=False)
print('KmHome reviewed: %d open edges, %d fins' % (open_edges, fins))
