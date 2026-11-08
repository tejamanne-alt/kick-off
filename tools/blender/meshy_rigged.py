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
#
#   blenv/bin/python meshy_rigged.py -- /abs/rigged.fbx /abs/outdir [--profile awesome] [--name PrimaryBoy2] [--tris 100000]
#     -> outdir/<Name>.fbx, <Name>.blend, <Name>.json, <Name>Atlas.png
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv[sys.argv.index('--') + 1:]
PROFILE_NAME = _argv[_argv.index('--profile') + 1] if '--profile' in _argv else 'awesome'
if '--profile' not in sys.argv: sys.argv += ['--profile', 'first_day']     # (meshy_teen reads its own profile on import)
import meshy_teen as mt
import meshy_boy as mb
from meshy_boy import (log, activate, verts_np, edges_np, texture_pixels, vertex_colours, hsv, decimate, make_rig,
                       weights, srgb, atlas_material, export_fbx, components)

argv = _argv
SRC, OUT = argv[0], argv[1]
TRIS = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 100000
NAME = argv[argv.index('--name') + 1] if '--name' in argv else 'PrimaryBoy2'
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


def game_bone(name):
    s = short(name)
    if s in GAME_BONE: return GAME_BONE[s]
    for side, n in (('Left', 'L'), ('Right', 'R')):            # the fingers
        if s.startswith(side + 'Hand'): return 'Hand.' + n
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
        if g is None: lost += 1; continue
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


PROFILES = {'awesome': {'parts': parts_awesome, 'stands': 1.32}}
PROFILE = PROFILES[PROFILE_NAME]


def finish(o, rig, img, px):
    png = os.path.join(OUT, NAME + 'Atlas.png')
    mb.face_parts = PROFILE['parts']
    refs = mb.paint(o, img, px, png)
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
    decimate(obj, TRIS)
    tidy(obj, J0)
    rig = make_rig(J0)
    mt.RIG = rig
    merge_weights(obj)
    mt.bind(obj, rig)
    mt.repose(obj, rig, J0)
    bag_marker(obj, rig)
    mt.nose(obj, rig)
    finish(obj, rig, img, px)
