# Polishes a finished character FBX for the game (the six playable kids and their Locker Room bags, or a passer-by),
# keeping its skeleton, skin weights, outfit parts, vertex colours, bags and atlas layout exactly as the game expects:
#
#   blenv/bin/python polish_character.py -- <in.fbx> <in atlas.png> <out dir> [--name Name] [--tris 60000] [--bag-tris 12000]
#                                            [--merge 0.002] [--face-lean 0.85] [--no-face]
#     -> out dir/<Name>.fbx, <Name>Atlas.png (the atlas with its gaps filled), <Name>_polish.json (what was done)
#
# Why (docs/LEARNINGS.md, "The characters looked low quality"): the AI-made models came apart in ways the game's toon
# shading shows up at once.
# - Torn surface. The scans' vertices come split wherever the texture is cut (thousands of small UV islands), and they
#   were cut down to 100k triangles before being welded, so each island's border moved on its own: tens of thousands of
#   open edges with hairline gaps, every border vertex with a normal of its own side only. In the game that drew light
#   scratches along every seam (the rim light and the cel band flip on those normals) and let the ink hull show through
#   the gaps. Welded here: open-edge vertices within --merge of each other become one.
# - Shattered normals. The scanned surface is noisy at the scale of a few millimetres (hair strands, cloth creases, the
#   pores of a scanned face), so the two-band cel shading broke into shards and specks. Each vertex takes the area-weighted
#   normal of the surface within a radius around it (across any remaining gap, never from the far side of a thin part):
#   12 mm on skin, 20 mm on clothes, 35 mm on hair, so hair and clothes shade as clean toon shapes and faces keep theirs.
# - Back-to-front triangles. A few hundred triangles faced into the body (the cut folded them); culled, they were pin-
#   holes. A triangle whose surroundings clearly face the other way is turned round.
# - A head that folded. The scans' automatic rigs put the lower face part on the Neck bone, so it creased and squashed
#   into the neck as the head nodded (docs/LEARNINGS.md C15). Everything above a cut through the Head joint, dipping under
#   the chin, follows the Head alone, blending back to the neck below it.
# - The face. The face (eyes, nose, mouth, cheeks, the jaw and chin) leans its normals toward a sphere behind it
#   (--face-lean), so it is lit as one rounded shape instead of breaking into patches round a scanned nose and lips, with
#   a clean curved edge when the sun is to one side; the lean fades out toward the cheeks' edge and the hairline, whose
#   normals stay true for the ink outline's width.
# - White tears. Light streaks in a dark garment's texture (folds, highlights, unpainted seams) were left out of the
#   garment, a white vertex colour times a light texel: white specks and slivers in jackets, trousers and hair
#   (docs/LEARNINGS.md C16). A greyish face of no outfit part that its garment surrounds joins the garment.
# - Weight. 100k triangles a kid (and 30k for each bag) is about three triangles per pixel at the kid's size in a level;
#   cut to --tris (60k) and --bag-tris (12k), the head and hands held back so faces and fingers keep their detail.
# - Mipmaps. The atlas' gaps between islands held other colours, which the GPU's smaller mip levels averaged into the
#   islands' edges. Every gap is filled from its island (a push-pull fill), so no mip level draws a foreign colour.
# Nothing moves: no vertex is displaced except where open edges are welded (by at most --merge), so painted detail stays
# where it was. The bones and rest pose are kept; the weights are kept (at most four a vertex, normalised) except the
# head's, the outfit parts (UV2.x, one per face) and vertex colours except the tears'; the FBX is written with the same
# export settings as meshy_rigged.py.
import bpy, bmesh, sys, os, json, time
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import polish_lib as pl

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, ATLAS, OUT = argv[0], argv[1], argv[2]
opt = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
NAME = opt('--name', os.path.splitext(os.path.basename(SRC))[0])
KID_TRIS = opt('--tris', 60000)
BAG_TRIS = opt('--bag-tris', 12000)
MERGE = opt('--merge', 0.002)
FACE_LEAN = opt('--face-lean', 0.85)
FACE = '--no-face' not in argv
os.makedirs(OUT, exist_ok=True)
log = lambda *a: print('[polish]', *a, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, use_custom_normals=True, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y',
                         secondary_bone_axis='X')
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
ATLAS_PX = pl.load_png(ATLAS)
report = {'name': NAME, 'meshes': {}}
t0 = time.time()
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    r = {'tris_in': pl.tris(o), 'open_edges_in': pl.open_edges(o)}
    r['merged'] = pl.clean(o, MERGE)
    body = o.name == 'Kid'
    if body:
        g = pl.protect_group(o, {'Head', 'Hand.L', 'Hand.R'}, keep=0.3)
        pl.decimate(o, KID_TRIS, g)
    else:
        pl.decimate(o, BAG_TRIS, pl.protect_group(o, set(), keep=1.0))
    r['unflipped'] = pl.unflip(o)
    if body:
        r['head_made_rigid'] = pl.rigid_head(o, rig)
    face = pl.face_lean(o, rig, FACE_LEAN) if (body and FACE) else None
    r['mixed_part_faces_fixed'] = pl.fix_parts(o)
    if body:
        r['tear_faces_absorbed'] = pl.absorb_tears(o, ATLAS_PX)
    pl.fix_weights(o)
    pl.smooth_normals(o, face)
    r['tris_out'] = pl.tris(o); r['open_edges_out'] = pl.open_edges(o)
    report['meshes'][o.name] = r
    log(o.name, r)
log('meshes done in %.1f s' % (time.time() - t0))

out_fbx = os.path.join(OUT, NAME + '.fbx')
for x in bpy.context.scene.objects: x.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(filepath=out_fbx, use_selection=True, apply_scale_options='FBX_SCALE_ALL', add_leaf_bones=False,
                         bake_anim=False, mesh_smooth_type='FACE', use_mesh_modifiers=True, axis_forward='-Z', axis_up='Y',
                         primary_bone_axis='Y', secondary_bone_axis='X', path_mode='STRIP')

# the atlas: every gap filled from its island (the body's UVs; the bags have atlases of their own, shared by every kid)
kid = bpy.data.objects['Kid']
filled = pl.fill_atlas(kid, ATLAS)
pl.save_png(filled, os.path.join(OUT, NAME + 'Atlas.png'))
with open(os.path.join(OUT, NAME + '_polish.json'), 'w') as f:
    json.dump(report, f, indent=1)
log('wrote', out_fbx)
