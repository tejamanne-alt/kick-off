# A playable kid from a model that comes rigged (an AI-generated model the user supplied with Meshy's own Mixamo-style
# skeleton and skin weights, exported as FBX with an animation: one fused, textured mesh skinned to 'mixamorig:' bones),
# in the same contract as the game's other kids (meshy_teen.py): one skinned mesh 'Kid' under 'KidRig', one material
# (vertex colours times the atlas; UV2.x the outfit part), the bones the game poses, the Nose and Bag markers,
# <Name>.json with the default outfit colours.
#
# Unlike meshy_teen.py nothing is guessed from the mesh: the joints are the skeleton's, and the weights are the
# model's own, merged into the game's coarser bones (the spine's three into Hips, Spine and Chest; the collar bones
# into the Chest; the fingers into the Hand; the toes into the Foot). The model has no bag of its own: the Bag marker
# sits on the middle of his upper back, where meshy_bag.py fits the Locker Room's bags.
#
#   awesome   Leo (PrimaryBoy2): a primary-school boy in an A-pose; short curly black hair, a white long-sleeved
#             "AWESOME" sweatshirt with a navy chest panel, khaki cargo joggers, white and navy sneakers.
#   rainbow   Zoe (PrimaryGirl2): a primary-school girl in an A-pose; black hair, a hot-pink rainbow-print jacket, coral
#             joggers, dark trainers (meshy_teen's colour rules for her, without its backpack: she has none).
#   explorer  Mia (PrimaryGirl): a primary-school girl in an A-pose; shoulder-length black hair with a headband, a white
#             "Kick Off" T-shirt, red shorts, white socks, pink sneakers (meshy_teen's colour rules for her).
#   varsity   Hana (Girl): a high-school girl in an A-pose; long wavy dark-brown hair, a maroon varsity jacket with cream
#             sleeves and striped cuffs over a cream hoodie, charcoal cargo jeans, cream platform sneakers.
#   jogger    Jogger (a passer-by, not a playable kid): a woman in her thirties in an A-pose; a black ponytail, a teal
#             zip-up running jacket, black leggings, white running shoes (--tris 30000: several walk by at once).
#   mom       Mom (a passer-by): a mother in an A-pose; black hair in a bun, a coral knitted jumper, dark-green wide-leg
#             trousers, white trainers (--tris 30000).
#   office    OfficeWorker (a passer-by): a bearded man in an A-pose; a navy blazer over a pale-blue shirt, grey suit
#             trousers, a brown belt and brown shoes (--tris 30000).
#   courier   Courier (a passer-by): a young man in an A-pose; a navy cap worn backwards over black curls, a red polo
#             shirt, khaki cargo shorts, white socks, grey trainers (--tris 30000).
#   shopkeeper  Shopkeeper (a passer-by): a woman in an A-pose; a blue hijab over a white underscarf, a long lilac tunic,
#             charcoal trousers, black flats (--tris 30000).
#   grandad   Grandad (a passer-by): an old man in an A-pose; a brown flat cap, grey hair and moustache, a mustard
#             cardigan over a gingham shirt, brown corduroy trousers, brown shoes (--tris 30000).
#   denim     Max (BackpackBoy): a teen in an A-pose; ginger hair, a light denim jacket over a dark grey hoodie, dark
#             jeans, white high-top sneakers (meshy_teen's colour rules for him; his old backpack is gone).
#   plaid     Kai (PrimaryBoy): a primary-school boy in an A-pose; short black hair, a red plaid flannel shirt over a
#             white hood, light-blue cargo jeans, chunky black-and-white sneakers (meshy_teen's colour rules for him).
#
#   blenv/bin/python meshy_rigged.py -- /abs/rigged.fbx /abs/outdir [--profile awesome|plaid|rainbow|explorer|varsity|denim|jogger|mom|office|courier|shopkeeper|grandad] [--name <Name>] [--tris 100000]
#     -> outdir/<Name>.fbx, <Name>.blend, <Name>.json, <Name>Atlas.png
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv[sys.argv.index('--') + 1:]
PROFILE_NAME = _argv[_argv.index('--profile') + 1] if '--profile' in _argv else 'awesome'
_args = list(sys.argv)
# (meshy_teen reads a profile of its own on import: give it one it knows, whatever this script's)
sys.argv = [a for i, a in enumerate(_args) if a != '--profile' and (i == 0 or _args[i - 1] != '--profile')] + ['--profile', 'first_day']
import meshy_teen as mt
sys.argv = _args
import meshy_boy as mb
from meshy_boy import (log, activate, verts_np, edges_np, texture_pixels, vertex_colours, hsv, decimate, make_rig,
                       weights, srgb, atlas_material, export_fbx, components)

argv = _argv
SRC, OUT = argv[0], argv[1]
TRIS = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 100000
NAME = argv[argv.index('--name') + 1] if '--name' in argv else {'awesome': 'PrimaryBoy2', 'plaid': 'PrimaryBoy', 'rainbow': 'PrimaryGirl2', 'explorer': 'PrimaryGirl', 'varsity': 'Girl', 'denim': 'BackpackBoy', 'jogger': 'Jogger', 'mom': 'Mom',
        'office': 'OfficeWorker', 'courier': 'Courier', 'shopkeeper': 'Shopkeeper', 'grandad': 'Grandad'}[PROFILE_NAME]
os.makedirs(OUT, exist_ok=True)
C = bpy.context
mb.log = lambda *a: print('[meshy_rigged]', *a, flush=True)
log = mb.log

# The model's bones -> the game's (anything else: the bone of its nearest named ancestor in this table).
GAME_BONE = {'Hips': 'Hips', 'Spine': 'Hips', 'Spine1': 'Spine', 'Spine2': 'Chest', 'Neck': 'Neck', 'Head': 'Head',
             'HeadTop_End': 'Head', 'headfront': 'Head',
             'LeftShoulder': 'Chest', 'RightShoulder': 'Chest',
             'LeftArm': 'UpperArm.L', 'LeftForeArm': 'LowerArm.L', 'LeftHand': 'Hand.L',
             'RightArm': 'UpperArm.R', 'RightForeArm': 'LowerArm.R', 'RightHand': 'Hand.R',
             'LeftUpLeg': 'UpperLeg.L', 'LeftLeg': 'LowerLeg.L', 'LeftFoot': 'Foot.L', 'LeftToeBase': 'Foot.L',
             'RightUpLeg': 'UpperLeg.R', 'RightLeg': 'LowerLeg.R', 'RightFoot': 'Foot.R', 'RightToeBase': 'Foot.R'}


def short(name): return name.split(':')[-1]


PARENT = {}               # each of the model's bones' parent (load): an extra bone goes with its nearest named ancestor


def game_bone(name):
    s = short(name)
    while s is not None:
        if s in GAME_BONE: return GAME_BONE[s]
        for side, n in (('Left', 'L'), ('Right', 'R')):        # the fingers
            if s.startswith(side + 'Hand'): return 'Hand.' + n
        s = PARENT.get(s)
    return None


def load():
    """The mesh at the skeleton's rest pose with its transforms applied (z up, facing -y), the skeleton's joints in
    the same space, and the base-colour texture."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    src = [x for x in bpy.data.objects if x.type == 'ARMATURE'][0]
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    src.animation_data_clear(); src.data.pose_position = 'REST'
    for pb in src.pose.bones: pb.matrix_basis = Matrix()
    C.view_layer.update()
    M = src.matrix_world
    bones = {short(b.name): (np.array(M @ b.head_local), np.array(M @ b.tail_local)) for b in src.data.bones}
    for b in src.data.bones:
        PARENT[short(b.name)] = short(b.parent.name) if b.parent else None
        if short(b.name) not in GAME_BONE and not short(b.name).startswith(('Left', 'Right', 'HeadTop')):
            log('bone %s (parent %s) goes with %s' % (b.name, b.parent.name if b.parent else None, game_bone(b.name)))
    img = [n.image for n in o.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and
           any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links)][0]
    img.pack() if not img.packed_file else None
    mw = o.matrix_world.copy()
    for m in list(o.modifiers): o.modifiers.remove(m)
    o.parent = None; o.matrix_world = mw
    activate(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.data.objects.remove(src)
    for x in [x for x in bpy.data.objects if x is not o]: bpy.data.objects.remove(x)
    o.name = NAME
    return o, img, bones


def weld(o):
    """Joins the scan's texture islands back into one surface. Its vertices come split wherever the texture is cut
    (every island a loose patch), so cutting its triangles down moved each patch's border on its own and left hairline
    cracks between them (the scratches across the passers-by's faces); welded, the cut keeps the surface closed and the
    texture's seams stay where they were, in the corners' own UVs."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data)
    n = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    log('welded the texture islands: %d -> %d vertices, %d open edges left' % (n, len(bm.verts), open_edges))
    bm.to_mesh(o.data); bm.free(); o.data.update()


# The cut's hold on the colour lines (decimate_keeping_edges): the decimate's vertex-group factor, and the weight of the
# vertices on a colour line in the group that is cut (the rest 1): low enough that a beard's edge keeps its small faces,
# above 0 so a patterned shirt (all colour lines) can still be cut down to the count.
KEEP_FACTOR, KEEP_HELD = 5.0, 0.3


def colour_edge_vertices(o, px, step=0.2):
    """The vertices on a line where the texture's colour changes (a beard against the cheek, a collar against the
    neck): between two faces whose own colours differ by more than `step` in any channel."""
    me = o.data; nl = len(me.loops); nf = len(me.polygons)
    UV = np.empty(nl * 2); me.uv_layers[0].data.foreach_get('uv', UV); UV = UV.reshape(-1, 2)
    starts = np.empty(nf, dtype=np.int64); me.polygons.foreach_get('loop_start', starts)
    sizes = np.empty(nf, dtype=np.int64); me.polygons.foreach_get('loop_total', sizes)
    Cf = mb.sample(px, np.add.reduceat(UV, starts) / sizes[:, None])[:, :3]
    EK = np.empty(nl, dtype=np.int64); me.loops.foreach_get('edge_index', EK)
    FL = np.repeat(np.arange(nf), sizes)
    order = np.argsort(EK, kind='stable'); ek, fl = EK[order], FL[order]
    pair = np.flatnonzero(ek[1:] == ek[:-1])
    differ = np.abs(Cf[fl[pair]] - Cf[fl[pair + 1]]).max(1) > step
    EV = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', EV); EV = EV.reshape(-1, 2)
    keep = np.zeros(len(me.vertices), bool); keep[EV[ek[pair][differ]].ravel()] = True
    return keep


def decimate_keeping_edges(o, tris, px):
    """Cuts the triangles down to `tris` as decimate does, the vertices on the texture's colour lines held back, so a
    part's edge (a beard's against the cheek, a moustache's, a hem) keeps small faces along it and a face rarely
    straddles it: the game recolours whole faces, so a straddling face put a jagged tooth of hair colour into the skin."""
    keep = colour_edge_vertices(o, px)
    g = o.vertex_groups.new(name='_KeepEdges')
    g.add(np.flatnonzero(~keep).tolist(), 1.0, 'REPLACE')                      # (the group is what is cut: all of it,
    g.add(np.flatnonzero(keep).tolist(), KEEP_HELD, 'REPLACE')                 #  the colour lines less)
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    activate(o); m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = tris / n; m.use_collapse_triangulate = True
    m.vertex_group = '_KeepEdges'; m.vertex_group_factor = KEEP_FACTOR
    bpy.ops.object.modifier_apply(modifier=m.name)
    o.vertex_groups.remove(o.vertex_groups['_KeepEdges'])
    log('decimated %s: %d -> %d tris, %d vertices on colour lines held back' % (
        o.name, n, sum(len(p.vertices) - 2 for p in o.data.polygons), keep.sum()))


def joints(bones):
    """The game's joints (meshy_boy.bone_list) from the skeleton's."""
    h = lambda n: bones[n][0].copy()
    t = lambda n: bones[n][1].copy()
    J = {'pelvis': h('Hips'), 'spine': h('Spine1'), 'chest': h('Spine2'), 'neck0': h('Neck'), 'neck1': h('Head'),
         'headtop': h('HeadTop_End')}
    J['pelvis'][0] = J['spine'][0] = J['chest'][0] = J['neck0'][0] = J['neck1'][0] = J['headtop'][0] = \
        (h('Head')[0] + h('Hips')[0]) / 2                        # (the spine straight up the middle)
    for side, n in (('Left', 'L'), ('Right', 'R')):
        J['hip' + n], J['knee' + n], J['ankle' + n] = h(side + 'UpLeg'), h(side + 'Leg'), h(side + 'Foot')
        J['toe' + n] = t(side + 'ToeBase')
        J['shoulder' + n], J['elbow' + n], J['wrist' + n] = h(side + 'Arm'), h(side + 'ForeArm'), h(side + 'Hand')
        tip = side + 'HandMiddle3'
        J['tip' + n] = t(tip) if tip in bones else h(side + 'Hand') + 2.2 * (t(side + 'Hand') - h(side + 'Hand'))
    return J


def tidy(o, J):
    """Welded, scaled to the teen boy's height (meshy_teen.HEIGHT) with the feet on z = 0, the head over the origin;
    the joints moved with it."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    V = verts_np(o); zmin, zmax = V[:, 2].min(), V[:, 2].max(); k = mt.HEIGHT / (zmax - zmin)
    cx, cy = J['neck1'][0], J['pelvis'][1]
    T = Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation((-cx, -cy, -zmin))
    o.data.transform(T); o.data.update()
    for key in J: J[key] = np.array(T @ Vector(J[key]))
    log('scaled by %.4f; height %.3f' % (k, mt.HEIGHT))


def merge_weights(o):
    """The model's weights, each group added into its game bone; at most four bones a vertex (Unity skins with four),
    normalised."""
    W0, n0 = weights(o)
    names = [n for n, *_ in mb.bone_list(J0)]
    W = np.zeros((len(W0), len(names)))
    lost = 0
    for j, n in enumerate(n0):
        g = game_bone(n)
        if g is None: lost += 1; log('weights: %s has no game bone; dropped' % n); continue
        W[:, names.index(g)] += W0[:, j]
    none = W.sum(1) < 1e-6
    if none.any():                                             # (a stray vertex the skin missed: its neighbours' bones)
        E = edges_np(o)
        for _ in range(20):
            acc = np.zeros_like(W); np.add.at(acc, E[:, 0], W[E[:, 1]]); np.add.at(acc, E[:, 1], W[E[:, 0]])
            W[none] = acc[none]; none = W.sum(1) < 1e-6
            if not none.any(): break
    W[W < np.sort(W, 1)[:, -4][:, None]] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    mb.set_weights(o, W, names)
    log('weights: %d groups merged into %d bones (%d dropped), %d vertices filled from neighbours' % (
        len(n0), len(names), lost, int((W0.sum(1) < 1e-6).sum())))


def bag_marker(o, rig):
    """The Bag marker on the Chest: its head at the middle of the upper back, on the surface, a little below the
    shoulders (where a backpack's top sits); its tail down the back. meshy_bag.py hangs the bags on it."""
    V = verts_np(o); B = rig.data.bones
    chest = np.array(B['Chest'].head_local); neck = np.array(B['Neck'].head_local); hips = np.array(B['Hips'].head_local)
    z = chest[2] + 0.15 * (neck[2] - chest[2])
    m = (np.abs(V[:, 2] - z) < 0.015) & (np.abs(V[:, 0] - chest[0]) < 0.05)
    yb = V[m, 1].max()
    head = Vector((chest[0], yb, z)); tail = Vector((chest[0], yb, z - 0.3 * (z - hips[2])))
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    b = eb.new('Bag'); b.head = head; b.tail = tail; b.roll = 0; b.parent = eb['Chest']; b.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    log('bag marker at %s' % np.round(np.array(head), 3))


def khaki(Cc):
    h, s, v = hsv(Cc)
    return (h > 18) & (h < 50) & (s > 0.15) & (s < 0.6) & (v > 0.3)


def parts_awesome(o, px):
    """Leo's parts: 1 the sweatshirt's white (its navy chest panel, collar and print stay as they are), 2 the khaki
    joggers, 3 the black hair (the biggest dark piece of the head); 0 the skin, the shoes and the rest."""
    V = verts_np(o); bw = mt.bone_weights(o)
    head = bw('Head'); foot = bw('Foot.L', 'Foot.R'); hand = bw('Hand.L', 'Hand.R')
    legs = bw('UpperLeg.L', 'UpperLeg.R', 'LowerLeg.L', 'LowerLeg.R')
    Cv = vertex_colours(o, px); h, s, v = hsv(Cv)
    hip = mt.rig_z('UpperLeg.L')
    white = (s < 0.18) & (v > 0.6)
    P = np.zeros(len(V), dtype=np.int64)
    P[white & (V[:, 2] > hip - 0.02) & (head < 0.5)] = 1
    P[khaki(Cv) & (V[:, 2] < hip + 0.1) & (legs + bw('Hips') > 0.5)] = 2
    P[mt.biggest_piece(o, (v < 0.22) & (head > 0.5))] = 3
    P[(foot > 0.5) | (hand > 0.5)] = 0
    return mt.by_vertex_votes(o, P)


def parts_varsity(o, px):
    """Hana's parts, by each face's own colour: 1 the varsity jacket's maroon body (its cream sleeves, the hoodie and the
    striped cuffs stay as they are), 2 the charcoal cargo jeans, 3 the long dark-brown hair (the biggest dark piece of the
    head and what hangs from it); 0 the skin, the hoodie, the sleeves and the sneakers."""
    me = o.data; V = verts_np(o); bw = mt.bone_weights(o)
    tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); tri = tri.reshape(-1, 3)
    fw = lambda w: w[tri].mean(1)
    foot = fw(bw('Foot.L', 'Foot.R')); hand = fw(bw('Hand.L', 'Hand.R')); head = fw(bw('Head', 'Neck'))
    legs = fw(bw('UpperLeg.L', 'UpperLeg.R', 'LowerLeg.L', 'LowerLeg.R'))
    Cf = mt.face_colours(o, px); h, s, v = hsv(Cf); z = V[tri][:, :, 2].mean(1)
    hip = mt.rig_z('UpperLeg.L')
    maroon = ((h < 15) | (h > 330)) & (s > 0.35) & (v > 0.12) & (v < 0.6)
    denim = (s < 0.35) & (v > 0.08) & (v < 0.45) & ((h > 180) | (s < 0.15))
    FP = np.zeros(len(tri), dtype=np.int64)
    FP[maroon & (z > hip - 0.05) & (head < 0.5)] = 1
    FP[denim & (z < hip + 0.05) & (legs + fw(bw('Hips')) > 0.5) & (foot < 0.3)] = 2
    dark = (v < 0.25) & (s > 0.15) & ((h < 45) | (h > 330)) & (z > hip + 0.4) & ~(maroon & (head < 0.5))
    vm = np.zeros(len(V), bool); vm[tri[dark].ravel()] = True
    FP[dark & mt.biggest_piece(o, vm)[tri].all(1)] = 3
    FP[(foot > 0.6) | (hand > 0.5)] = 0
    return FP, tri


def big_pieces(o, mask, share):
    """The connected pieces of the vertices in mask holding at least `share` of them (the hair's, not the brows')."""
    E = edges_np(o); Eh = E[mask[E[:, 0]] & mask[E[:, 1]]]; lab = components(len(mask), Eh)
    ids, cnt = np.unique(lab[mask], return_counts=True)
    keep = ids[cnt >= share * mask.sum()]
    return mask & np.isin(lab, keep)


def parts_jogger(o, px):
    """The jogger's parts (a passer-by), by each face's own colour: 1 the teal running jacket (its zip and trims stay as
    they are), 2 the black leggings, 3 the black ponytail and her hair (and brows); 0 the skin, the white running shoes
    and the watch."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top((h > 155) & (h < 205) & (s > 0.3) & (v > 0.2))                        # (the collar too, on the neck and head bones)
    black = (v < 0.24) & (s < 0.45)
    f.legwear(black, 0.08)
    f.FP[black & (f.z < f.hip + 0.25) & (f.head < 0.5) & (f.foot < 0.3) & (f.hand < 0.5) & (f.FP == 0)] = 2   # (the waistband)
    f.third((v < 0.36) & (s < 0.5) & (f.head > 0.5), 0.01, eyes_out=True)       # (the hair's sheen as well)
    return f.done('jogger', ('jacket', 'leggings', 'hair'))


class Faces:
    """What a passer-by's colour rules read, face by face: the triangles, each face's colour (h in degrees, s, v), its
    height, and its weights on the game's bones (feet, hands, head and neck, the skull alone, the legs and hips)."""
    def __init__(self, o, px):
        me = o.data; V = verts_np(o); bw = mt.bone_weights(o)
        tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); self.tri = tri = tri.reshape(-1, 3)
        fw = lambda w: w[tri].mean(1)
        self.o, self.nv = o, len(V)
        self.foot = fw(bw('Foot.L', 'Foot.R')); self.hand = fw(bw('Hand.L', 'Hand.R')); self.head = fw(bw('Head', 'Neck'))
        self.skull = fw(bw('Head'))
        self.legs = fw(bw('UpperLeg.L', 'UpperLeg.R', 'LowerLeg.L', 'LowerLeg.R', 'Hips'))
        self.h, self.s, self.v = hsv(mt.face_colours(o, px)); self.z = V[tri][:, :, 2].mean(1)
        self.hip = mt.rig_z('UpperLeg.L')
        self.FP = np.zeros(len(tri), dtype=np.int64)

    def top(self, m, skull=0.9):
        """The top: not on the head (a high collar is partly the skull's: `skull`, the most of it), the feet, nor the
        hands (the cuffs on the wrists are)."""
        self.FP[m & (self.skull < skull) & (self.foot < 0.3) & (self.hand < 0.6)] = 1

    def legwear(self, m, above=0.12, feet=0.3):
        """The legwear: on the legs and hips, below the hip joint (or a little above it), not on the feet (long trousers'
        hems reach onto the feet' bones: a higher `feet`, with a colour the shoes don't share)."""
        self.FP[m & (self.z < self.hip + above) & (self.legs + self.foot > 0.5) & (self.foot < feet) & (self.head < 0.3)
                & (self.hand < 0.5)] = 2

    def third(self, m, share=0.04, eyes_out=False):
        """The third part (hair, a cap or a scarf): the big pieces of it. eyes_out: hair, so its dark pieces ringed by
        the whites of the eyes (the irises and lashes) are left out, however big the cut keeps them."""
        m = m & (self.FP == 0)
        vm = np.zeros(self.nv, bool); vm[self.tri[m].ravel()] = True
        keep = big_pieces(self.o, vm, share)
        if eyes_out:
            whites = (self.s < 0.22) & (self.v > 0.78) & (self.skull > 0.9)
            wv = np.zeros(self.nv, bool); wv[self.tri[whites].ravel()] = True
            E = edges_np(self.o); lab = components(self.nv, E[keep[E[:, 0]] & keep[E[:, 1]]])
            for i in np.unique(lab[keep]):
                piece = keep & (lab == i)
                if (piece & wv).sum() > 0.12 * piece.sum():
                    keep &= ~piece
                    log('an eye left out of the hair: %d vertices, %d by the whites' % (piece.sum(), (piece & wv).sum()))
        self.FP[m & keep[self.tri].all(1)] = 3

    def done(self, who, names):
        FP = self.FP; FP[(self.foot > 0.6) | (self.hand > 0.5)] = 0
        log('%s parts: %s %d, %s %d, %s %d faces of %d' % (who, names[0], (FP == 1).sum(), names[1], (FP == 2).sum(),
                                                          names[2], (FP == 3).sum(), len(FP)))
        return FP, self.tri


def parts_mom(o, px):
    """Mom's parts (a passer-by), by each face's own colour: 1 the coral knitted jumper, 2 the dark-green wide-leg
    trousers, 3 the black hair in its bun (the big dark pieces of the head); 0 the skin, the lips and the white
    trainers."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top(((h < 22) | (h > 340)) & (s > 0.45) & (v > 0.45), 0.5)                 # (her lips are coral too: the skull's)
    f.legwear((h > 125) & (h < 195) & (s > 0.3) & (v < 0.4), 0.15, 0.62)       # (the wide hems, down to the trainers)
    f.third((v < 0.16) & (f.head > 0.5), 0.01, eyes_out=True)                    # (the bun, the hair and the brows)
    return f.done('mom', ('jumper', 'trousers', 'hair'))


def parts_office(o, px):
    """The office worker's parts (a passer-by): 1 the navy blazer, 2 the grey suit trousers, 3 the dark-brown hair and
    beard; 0 the skin, the pale-blue shirt, the brown belt and the brown shoes."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top((h > 200) & (h < 250) & (s > 0.35) & (v < 0.42))
    f.legwear((s < 0.16) & (v > 0.22) & (v < 0.6), feet=0.62)
    f.third((v < 0.3) & ((h < 45) | (s < 0.3)) & (f.head > 0.5), 0.01, eyes_out=True)   # (the beard, moustache, brows)
    return f.done('office', ('blazer', 'trousers', 'hair'))


def parts_courier(o, px):
    """The courier's parts (a passer-by): 1 the red polo shirt, 2 the khaki cargo shorts, 3 the navy cap worn backwards;
    0 the skin, the black curls under the cap, the white socks and the grey trainers."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top(((h > 340) | (h < 15)) & (s > 0.6) & (v > 0.3))
    f.legwear((h > 27) & (h < 50) & (s > 0.18) & (s < 0.5) & (v > 0.35) & (v < 0.82), 0.1)   # (not the skin: redder)
    f.third((h > 200) & (h < 250) & (s > 0.4) & (v < 0.45) & (f.head > 0.5), 0.1)
    return f.done('courier', ('polo', 'shorts', 'cap'))


def parts_shopkeeper(o, px):
    """The shopkeeper's parts (a passer-by): 1 the long lilac tunic, 2 the charcoal trousers, 3 the blue hijab (over the
    head, the shoulders and the chest); 0 the skin, the white underscarf and the black flats."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top((h > 265) & (h < 330) & (s > 0.12) & (s < 0.45) & (v > 0.35))
    f.legwear((s < 0.15) & (v > 0.15) & (v < 0.38), 0.0, 0.62)                  # (not the black flats)
    blue = (h > 200) & (h < 235) & (s > 0.5) & (v > 0.25) & (f.foot < 0.3) & (f.hand < 0.5)
    f.third(blue, 0.1)
    return f.done('shopkeeper', ('tunic', 'trousers', 'hijab'))


def parts_grandad(o, px):
    """Grandad's parts (a passer-by): 1 the mustard cardigan, 2 the brown corduroy trousers, 3 the brown flat cap; 0 the
    skin, the grey hair and moustache, the blue gingham shirt and the brown shoes."""
    f = Faces(o, px); h, s, v = f.h, f.s, f.v
    f.top((h > 30) & (h < 56) & (s > 0.55) & (v > 0.5))
    brown = (h > 8) & (h < 42) & (s > 0.3) & (v > 0.1) & (v < 0.55)
    f.legwear(brown, 0.1)                                                        # (the cardigan's last button too)
    f.third(brown & (f.skull > 0.9), 0.1)
    return f.done('grandad', ('cardigan', 'trousers', 'cap'))


PROFILES = {'awesome': {'parts': parts_awesome, 'stands': 1.32},
            'plaid': {'parts': lambda o, px: mt.parts_plaid(o, px), 'stands': 1.30},
            'rainbow': {'parts': lambda o, px: parts_without_pack(mt.parts_rainbow, o, px), 'stands': 1.29},
            'explorer': {'parts': lambda o, px: mt.parts_explorer(o, px), 'stands': 1.27},
            'varsity': {'parts': parts_varsity, 'stands': 1.65},
            'denim': {'parts': lambda o, px: mt.parts_backpack_boy(o, px), 'stands': 1.75},
            'jogger': {'parts': parts_jogger, 'stands': 1.66},
            'mom': {'parts': parts_mom, 'stands': 1.63},
            'office': {'parts': parts_office, 'stands': 1.80},
            'courier': {'parts': parts_courier, 'stands': 1.72},
            'shopkeeper': {'parts': parts_shopkeeper, 'stands': 1.60},
            'grandad': {'parts': parts_grandad, 'stands': 1.70}}
PROFILE = PROFILES[PROFILE_NAME]


def parts_without_pack(parts, o, px):
    """meshy_teen's parts for a model with no backpack: its search for the pack by shape would take the back."""
    find = mt.pack_faces
    mt.pack_faces = lambda o: np.zeros(len(o.data.polygons), bool)
    try:
        return parts(o, px)
    finally:
        mt.pack_faces = find


def finish(o, rig, img, px):
    png = os.path.join(OUT, NAME + 'Atlas.png')
    mb.face_parts = PROFILE['parts']
    refs = mb.paint(o, img, px, png, plain_last=True)
    o.data.materials.clear(); o.data.materials.append(atlas_material('Kid', png))
    o.name = 'Kid'; o.data.name = 'Kid'
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    export_fbx([o, rig], os.path.join(OUT, NAME + '.fbx'))
    cols = {'top': refs.get(1, (1, 1, 1)), 'legwear': refs.get(2, (1, 1, 1)), 'hair': refs.get(3, (1, 1, 1)), 'accent': mb.ACCENT}
    data = {k: [round(float(c), 4) for c in srgb(v)] for k, v in cols.items()}
    data['tris'] = tris
    with open(os.path.join(OUT, NAME + '.json'), 'w') as f: json.dump(data, f)
    neck = rig.data.bones['Head'].head_local.z; top = max(v.co.z for v in o.data.vertices)
    log('%s: %d tris; the Head joint at %.3f of %.3f (%.3f of his height): at %.2f m tall, a neck height of %.3f' % (
        NAME, tris, neck, top, neck / top, PROFILE['stands'], PROFILE['stands'] * neck / top))


if __name__ == '__main__':
    obj, img, bones = load()
    px = texture_pixels(img)
    J0 = joints(bones)
    weld(obj)
    decimate_keeping_edges(obj, TRIS, px)
    tidy(obj, J0)
    rig = make_rig(J0)
    mt.RIG = rig
    merge_weights(obj)
    mt.bind(obj, rig)
    mt.repose(obj, rig, J0)
    bag_marker(obj, rig)
    mt.nose(obj, rig)
    finish(obj, rig, img, px)
