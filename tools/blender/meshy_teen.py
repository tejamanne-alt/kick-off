# A playable teen from a textured, single-mesh model standing in an A-pose (an AI-generated model the user supplied,
# exported as FBX: one fused mesh, one 2048 base-colour texture, no rig), in the same contract as the other teens (one
# skinned mesh 'Kid' under 'KidRig', one material: vertex colours times the atlas; UV2.x the outfit part; the bones the
# game poses; Nose and Bag markers; <Name>.json with the default outfit colours). Made for the backpack boy (Max):
# ginger hair, a denim jacket over a grey hoodie, dark jeans, white sneakers and a brown backpack on both shoulders.
# tools/blender/README.md ("The backpack boy") says more. It reuses meshy_boy.py's helpers.
#
#   blenv/bin/python meshy_teen.py -- /abs/source.fbx /abs/outdir [--name BackpackBoy] [--tris 30000]
#     -> outdir/<Name>.fbx, <Name>.blend, <Name>.json, <Name>Atlas.png, <Name>_joints.png
#
# The steps:
#   tidy      decimated to the budget, scaled to the teen boy's height, feet at z = 0, hips over the origin, facing -Y.
#   joints    from the mesh as it stands: the legs' cross-sections (the arms left out) and the crotch, the soles; each
#             arm's straight A-pose line from its fingertips; the shoulders inside the torso, the neck at its narrowest.
#   separate  the legs, if the scan joins them below the crotch, are cut apart and each side's holes closed.
#   rig       the game's armature on those joints, bone-heat weights; the arms brought down from the A-pose to hanging
#             (the game swings every bone from its rest pose), baked in and made the rest pose, weighed again; the
#             backpack follows the Bag bone (the game swings it as he runs), fading into the straps on his back.
#   paint     outfit parts by texture colour: the jacket 1, the jeans 2, the hair 3, the rest 0 (skin, hoodie, T-shirt,
#             backpack, shoes); the atlas has those parts' texels divided by their colour, which the vertex colours carry
#             instead, so the shop's outfits recolour them (ModelOutfit) and the default looks as the model did.
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshy_boy as mb                                    # (its helpers; it reads the same two leading arguments)
from meshy_boy import (log, activate, verts_np, edges_np, components, texture_pixels, vertex_colours, hsv, delete_verts,
                       decimate, mesh_tris, slice_loops, line_at, seg_dist, make_rig, pose_bone, rig_joints,
                       weights, lin, srgb, atlas_material, export_fbx)

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
NAME = argv[argv.index('--name') + 1] if '--name' in argv else 'BackpackBoy'
TRIS = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 30000
os.makedirs(OUT, exist_ok=True)
C = bpy.context
HEIGHT = 2.14            # the teen boy's standing height in Blender units (the game scales by the neck anyway)
mb.log = lambda *a: print('[meshy_teen]', *a, flush=True)
log = mb.log


# ------------------------------------------------------------------------------------------------ load and tidy
def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    activate(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    img = [n.image for n in o.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and
           any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links)][0]
    img.pack() if not img.packed_file else None
    for x in [x for x in bpy.data.objects if x is not o]: bpy.data.objects.remove(x)
    o.name = NAME
    return o, img


def tidy(o):
    """Weld the scan's seams (Meshy exports face -y, as the game's models do), scale it to the teen boy's height with the feet on z = 0, hips over the origin."""
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
    V = verts_np(o); zmin, zmax = V[:, 2].min(), V[:, 2].max(); H = zmax - zmin
    k = HEIGHT / H
    hips = V[(V[:, 2] > zmin + 0.45 * H) & (V[:, 2] < zmin + 0.55 * H) & (np.abs(V[:, 0]) < 0.1 * H)]
    cx, cy = np.median(hips[:, 0]), np.percentile(hips[:, 1], 30)
    o.data.transform(Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation((-cx, -cy, -zmin))); o.data.update()
    log('scaled by %.4f' % k)


# ------------------------------------------------------------------------------------------------ joints
HAND = 0.20              # fingertips to wrist along the arm (the hands hang open)


def find_joints(o):
    V = verts_np(o); T = mesh_tris(o); H = V[:, 2].max()
    J, info = {}, {}
    # the legs, with the arms (hanging out to the sides in the A-pose) left out of the cross-sections
    mid = np.abs(V[:, 0]) < 0.095 * H
    Tm = T[mid[T].all(1)]
    def two(z):
        # two outlines of a size side by side (the jacket's hem and the backpack's bottom are one in front of the other)
        L = slice_loops(V, Tm, z, 20)
        if len(L) < 2 or len(L[1]) < 0.6 * len(L[0]): return None
        a, b = L[0].mean(0), L[1].mean(0)
        return L[:2] if abs(a[0] - b[0]) > 0.1 and abs(a[1] - b[1]) < 0.05 else None
    crotch = next(z for z in np.arange(0.53 * H, 0.35 * H, -0.005) if two(z))
    info['crotch'] = crotch
    a, b = sorted(two(crotch - 0.01), key=lambda P: P[:, 0].mean())
    lines = {'R': [a.mean(0)], 'L': [b.mean(0)]}
    for z in np.arange(crotch - 0.03, 0.06 * H, -0.02):
        L = two(z)
        if not L: continue
        c0, c1 = sorted([P.mean(0) for P in L], key=lambda c: c[0])
        lines['R'].append(c0); lines['L'].append(c1)
    info['lines'] = lines
    soles = sorted(slice_loops(V, T, 0.02 * H, 20)[:2], key=lambda P: P[:, 0].mean())
    for n, sole in (('R', soles[0]), ('L', soles[1])):
        hip = line_at(lines[n], crotch - 0.04); hip[2] = crotch + 0.06
        ankle = line_at(lines[n], 0.055 * H)
        J['hip' + n], J['ankle' + n] = hip, ankle
        J['knee' + n] = line_at(lines[n], ankle[2] + 0.5 * (hip[2] - ankle[2])); J['knee' + n][1] -= 0.01
        J['toe' + n] = np.array([sole[:, 0].mean(), sole[:, 1].min() + 0.04, 0.03])

    # the trunk: its centre across, and a little behind its front (the backpack makes the back no guide)
    x0 = (J['hipL'][0] + J['hipR'][0]) / 2
    def trunk(z):
        B = V[(np.abs(V[:, 2] - z) < 0.01) & (np.abs(V[:, 0] - x0) < 0.08)]
        return np.array([x0, np.percentile(B[:, 1], 2) + 0.12, z])
    J['pelvis'] = np.array([x0, (J['hipL'][1] + J['hipR'][1]) / 2, crotch + 0.09])
    J['spine'] = trunk(0.61 * H); J['chest'] = trunk(0.70 * H)

    # the arms: hanging out to the side, a straight line from the fingertips up; the shoulder where it meets the top of
    # the torso, the wrist a hand's length up from the tips, the elbow half way
    shoulder_z = 0.81 * H
    for n, sg in (('L', 1), ('R', -1)):
        arm = (V[:, 0] * sg > 0.115 * H) & (V[:, 2] > 0.4 * H) & (V[:, 2] < 0.7 * H)
        P = V[arm]; tip = P[np.argmin(P[:, 2])]
        cs = []
        for z in np.arange(tip[2] + 0.03, 0.66 * H, 0.02):
            R = P[np.abs(P[:, 2] - z) < 0.01]
            if len(R) > 8: cs.append((R.min(0) + R.max(0)) / 2)
        cs = np.array(cs); c = cs.mean(0); d = np.linalg.svd(cs - c)[2][0]; d = d if d[2] > 0 else -d
        S = c + d * (shoulder_z - c[2]) / d[2]
        top = V[(V[:, 2] > 0.76 * H) & (V[:, 2] < 0.80 * H) & (V[:, 1] < J['chest'][1] + 0.05)]
        S[0] = sg * min(abs(S[0]), (top[:, 0] * sg).max() - 0.08)
        S[1] = J['chest'][1]
        tipc = c + d * (tip[2] - c[2]) / d[2]                  # (the tip on the line: the hand's own centre)
        W = tipc + (S - tipc) / np.linalg.norm(S - tipc) * HAND
        J['shoulder' + n], J['wrist' + n], J['tip' + n] = S, W, tipc
        J['elbow' + n] = (S + W) / 2 + np.array([0, 0.02, 0])
    sz = (J['shoulderL'][2] + J['shoulderR'][2]) / 2
    # the neck: the narrowest cross-section between the shoulders and the head's middle; the Head joint just above it
    widths = []
    for z in np.arange(sz + 0.04, 0.93 * H, 0.005):
        L = slice_loops(V, Tm, z, 12)
        if L: widths.append((np.ptp(L[0][:, 0]), z))
    nz = min(widths)[1]
    head = V[V[:, 2] > 0.93 * H]; hc = (head.min(0) + head.max(0)) / 2
    J['neck0'] = np.array([x0, J['chest'][1] + 0.01, sz + 0.06])
    J['neck1'] = np.array([hc[0], hc[1] - 0.01, nz + 0.02])
    J['headtop'] = np.array([hc[0], hc[1], H])
    for k in sorted(J): log('joint %-10s %s' % (k, np.round(J[k], 3)))
    log('crotch %.3f, neck %.3f (%.3f of the height)' % (crotch, J['neck1'][2], J['neck1'][2] / H))
    return J, info


def debug_points(o, px, J, path):
    from PIL import Image, ImageDraw
    V = verts_np(o); Cc = np.clip(vertex_colours(o, px), 0, 1); S, R = 700, 700 / 2.4
    ims = []
    for ax, sgn, depth in ((0, 1, -V[:, 1]), (1, 1, V[:, 0])):
        im = Image.new('RGB', (S, S), (60, 60, 70)); dr = ImageDraw.Draw(im)
        for k in np.argsort(depth):
            x = S / 2 + sgn * V[k, ax] * R; y = S - 20 - V[k, 2] * R
            dr.point((x, y), fill=tuple(int(255 * c) for c in Cc[k]))
        for jn, p in J.items():
            x = S / 2 + sgn * p[ax] * R; y = S - 20 - p[2] * R
            dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 40, 40)); dr.text((x + 4, y - 6), jn, fill=(255, 255, 0))
        ims.append(im)
    sheet = Image.new('RGB', (S * len(ims), S)); [sheet.paste(im, (i * S, 0)) for i, im in enumerate(ims)]; sheet.save(path)


# ------------------------------------------------------------------------------------------------ separate
def legs_apart(o, info):
    """The scan may join the legs below the crotch (the jeans' inner seams touching): cut the faces that join the two
    sides and close each side's holes, as meshy_boy.separate does for the legs. Prints what it found."""
    V = verts_np(o); E = edges_np(o); z = info['crotch'] - 0.08
    low = V[:, 2] < z; El = E[low[E[:, 0]] & low[E[:, 1]]]; lab = components(len(V), El)
    ids, cnt = np.unique(lab[low], return_counts=True); big = ids[cnt > 200]
    sides = [np.sign(V[lab == i, 0].mean()) for i in big]
    log('legs: %d pieces below %.3f, sides %s' % (len(big), z, sides))
    if len(big) >= 2 and len(set(sides)) == 2: return
    J = {k: v for k, v in INFO_J.items()}
    for n in 'LR':                                              # (no arm is cut here: they hang free of the body)
        J['wrist' + n] = J['tip' + n] = np.array([0.0, 0.0, -10.0])
    mb.separate(o, PX, J, dict(info, hemL=-10.0, hemR=-10.0))


# ------------------------------------------------------------------------------------------------ weights
FALLOFF = 0.022          # metres: how fast a bone's pull fades past the nearest bone's distance


def weigh_near(o, rig, info):
    """Weights by nearness to the bones, made in the A-pose, where the arms hang clear of the body (bone heat finds no
    solution on this scan: its jacket, hood and backpack are layered, open shells). Below the crotch each leg takes only
    its own bones (and the hips'); the head takes the Head bone only above the jaw; smoothed over the surface a little,
    at most four bones a vertex."""
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    for m in list(o.modifiers): o.modifiers.remove(m)
    V = verts_np(o); E = edges_np(o); B = rig.data.bones
    names = [b.name for b in B if b.use_deform]
    D = np.stack([seg_dist(V, np.array(B[n].head_local), np.array(B[n].tail_local))[0] for n in names], 1)
    allow = np.ones_like(D, bool)
    ix = {n: i for i, n in enumerate(names)}
    # the legs: the pieces below the crotch (they are apart there), each with its own leg's bones
    zc = info['crotch'] - 0.06
    low = V[:, 2] < zc; El = E[low[E[:, 0]] & low[E[:, 1]]]; lab = components(len(V), El)
    for n, other in (('L', 'R'), ('R', 'L')):
        a = np.array(B['LowerLeg.' + n].tail_local); seed = np.argmin(np.where(low, np.linalg.norm(V - a, axis=1), np.inf))
        leg = low & (lab == lab[seed])
        for bn in names:
            if not (bn.endswith('.' + n) and bn.split('.')[0] in ('UpperLeg', 'LowerLeg', 'Foot')) and bn != 'Hips':
                allow[leg, ix[bn]] = False
    # nothing else takes a leg's bones (a hand hangs by the thigh)
    legs = low & np.isin(lab, [lab[np.argmin(np.where(low, np.linalg.norm(V - np.array(B['LowerLeg.' + n].tail_local), axis=1), np.inf))] for n in 'LR'])
    for bn in names:
        if bn.split('.')[0] in ('UpperLeg', 'LowerLeg', 'Foot'): allow[~legs & (V[:, 2] < zc), ix[bn]] = False
    allow[V[:, 2] < B['Head'].head_local.z - 0.03, ix['Head']] = False
    D = np.where(allow, D, np.inf)
    W = np.exp(-(D - D.min(1, keepdims=True)) / FALLOFF); W[~np.isfinite(D)] = 0
    deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(3):
        acc = np.zeros_like(W); np.add.at(acc, E[:, 0], W[E[:, 1]]); np.add.at(acc, E[:, 1], W[E[:, 0]])
        W = np.where(allow, 0.5 * W + 0.5 * acc / np.maximum(deg, 1)[:, None], 0)
    W[W < np.sort(W, 1)[:, -4][:, None]] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    bind(o, rig); mb.set_weights(o, W, names)
    log('weights: by nearness, %d vertices, %d bones; legs %d vertices' % (len(V), len(names), legs.sum()))


def bind(o, rig):
    """Parent to the rig with an Armature modifier (the vertex groups are set apart)."""
    for m in list(o.modifiers): o.modifiers.remove(m)
    o.parent = rig; o.matrix_parent_inverse = Matrix()
    m = o.modifiers.new('Armature', 'ARMATURE'); m.object = rig


# ------------------------------------------------------------------------------------------------ re-pose
ARM_DOWN = (0.17, 0.03, -1.0)        # as the teen boy: the upper arm hanging, a little away from the side
FOREARM_DOWN = (0.06, -0.12, -1.0)   # the forearm, a touch forward of straight
LEG_IN = 0.03                        # the ankles are put this far outside the hip joints (he stands with his feet apart)


def repose(o, rig, J):
    """The arms down from the A-pose to hanging, the legs brought in under the hips (the feet turned back flat), baked
    into the mesh and made the rig's rest pose."""
    for pb in rig.pose.bones: pb.matrix_basis = Matrix()
    for n, sg in (('L', 1), ('R', -1)):
        pose_bone(rig, 'UpperArm.' + n, (sg * ARM_DOWN[0], ARM_DOWN[1], ARM_DOWN[2]))
        pose_bone(rig, 'LowerArm.' + n, (sg * FOREARM_DOWN[0], FOREARM_DOWN[1], FOREARM_DOWN[2]))
        pose_bone(rig, 'Hand.' + n, (sg * FOREARM_DOWN[0], FOREARM_DOWN[1], FOREARM_DOWN[2]))
        hip, ankle = J['hip' + n], J['ankle' + n]
        ang = math.atan2(ankle[0] - hip[0], hip[2] - ankle[2]) - math.atan2(sg * LEG_IN, hip[2] - ankle[2])
        R = Matrix.Rotation(ang, 4, 'Y')                         # (about y: x toward z; turns the ankle in under the hip)
        pose_bone(rig, 'UpperLeg.' + n, rot=R)
        pose_bone(rig, 'Foot.' + n, rot=R.inverted())
        log('repose: %s leg turned in %.1f degrees' % (n, math.degrees(ang)))
    activate(o); bpy.ops.object.modifier_apply(modifier=[m.name for m in o.modifiers if m.type == 'ARMATURE'][0])
    activate(rig); bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
    dz = -verts_np(o)[:, 2].min(); T = Matrix.Translation((0, 0, dz))
    o.data.transform(T); o.data.update(); rig.data.transform(T)
    log('repose: feet down %.3f' % dz)
    bind(o, rig)
    return rig_joints(rig)


# ------------------------------------------------------------------------------------------------ backpack and markers
def is_pack(Cc):
    h, s, v = hsv(Cc)
    return (h > 15) & (h < 45) & (s > 0.35) & (v > 0.18) & (v < 0.75)


def backpack(o, rig, px):
    """The backpack: brown and behind his back. It follows the Bag bone (head at its top, tail toward its bottom, on
    the Chest), fading over the few centimetres where it meets his back so the swing bends rather than tears."""
    V = verts_np(o); E = edges_np(o); B = rig.data.bones
    chest = np.array(B['Chest'].head_local); hips = np.array(B['Hips'].head_local)
    band = (V[:, 2] > hips[2]) & (V[:, 2] < np.array(B['Head'].head_local)[2]) & (np.abs(V[:, 0]) < 0.3)
    # his back at each height: the furthest-back point of what is not the pack, near the middle
    pack = is_pack(vertex_colours(o, px)) & band
    back = {}
    for z in np.arange(hips[2], B['Head'].head_local.z, 0.02):
        m = band & ~pack & (np.abs(V[:, 2] - z) < 0.02) & (np.abs(V[:, 0]) < 0.12) & (V[:, 1] < 0.2)
        if m.sum() > 5: back[round(z, 2)] = np.percentile(V[m, 1], 95)
    zs = np.array(sorted(back)); bs = np.array([back[z] for z in zs])
    yb = np.interp(V[:, 2], zs, bs)
    w = np.clip((V[:, 1] - yb - 0.01) / 0.06, 0, 1) * band
    # the pack is the biggest brown piece well behind the back (the straps in front go with the chest)
    core = pack & (w > 0.5); Ec = E[core[E[:, 0]] & core[E[:, 1]]]; lab = components(len(V), Ec)
    ids, cnt = np.unique(lab[core], return_counts=True); core = core & (lab == ids[np.argmax(cnt)])
    P = V[core]; lo, hi = P.min(0) - 0.03, P.max(0) + 0.03
    w = w * np.all((V > lo) & (V < hi), 1)
    deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(4):
        acc = np.zeros(len(V)); np.add.at(acc, E[:, 0], w[E[:, 1]]); np.add.at(acc, E[:, 1], w[E[:, 0]])
        w = np.maximum(w * core, 0.5 * w + 0.5 * acc / np.maximum(deg, 1))
    top = np.array([P[:, 0].mean(), np.median(P[:, 1]), P[:, 2].max()])
    bot = np.array([top[0], top[1], P[:, 2].min()])
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    b = eb.new('Bag'); b.head = Vector(top); b.tail = Vector(top * 0.4 + bot * 0.6); b.roll = 0; b.parent = eb['Chest']
    bpy.ops.object.mode_set(mode='OBJECT')
    W, names = weights(o); names = names + ['Bag']; W = np.concatenate([W * (1 - w)[:, None], w[:, None]], 1)
    W[W < np.sort(W, 1)[:, -4][:, None]] = 0; W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    mb.set_weights(o, W, names)
    log('backpack: %d vertices follow the Bag bone (%d fully), top %s, bottom z %.3f' % ((w > 0.01).sum(), (w > 0.99).sum(),
                                                                                       np.round(top, 3), bot[2]))


def nose(o, rig):
    V = verts_np(o); neck1 = np.array(rig.data.bones['Head'].head_local)
    face = V[(V[:, 2] > neck1[2] + 0.06) & (V[:, 2] < neck1[2] + 0.16) & (np.abs(V[:, 0] - neck1[0]) < 0.06)]
    ny, nz = face[:, 1].min(), neck1[2] + 0.11
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    b = eb.new('Nose'); b.head = Vector((neck1[0], ny + 0.03, nz)); b.tail = Vector((neck1[0], ny - 0.03, nz)); b.roll = 0
    b.parent = eb['Head']; b.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------------------------------------------------------------------------ paint
def face_parts(o, px):
    """The outfit part of each face (0 fixed: skin, hoodie, T-shirt, backpack, shoes; 1 the denim jacket; 2 the jeans;
    3 the hair), by its texture colour, the bones that carry it and its height."""
    me = o.data; V = verts_np(o); E = edges_np(o); W, names = weights(o)
    bw = lambda *ns: sum(W[:, names.index(n)] for n in ns if n in names)
    head = bw('Head'); foot = bw('Foot.L', 'Foot.R'); legs = bw('UpperLeg.L', 'UpperLeg.R', 'LowerLeg.L', 'LowerLeg.R')
    hand = bw('Hand.L', 'Hand.R'); bag = bw('Bag')
    Cv = vertex_colours(o, px); h, s, v = hsv(Cv)
    blue = (h > 185) & (h < 240) & (s > 0.2)
    orange = (h > 5) & (h < 40) & (s > 0.55) & (v > 0.55)
    hip = rig_z('UpperLeg.L')
    P = np.zeros(len(V), dtype=np.int64)
    P[blue & (v > 0.42) & (V[:, 2] > hip - 0.12)] = 1                    # the jacket, its sleeves and collar
    P[(legs > 0.5) & (V[:, 2] < hip - 0.02) & (s < 0.5) & ~(blue & (v > 0.42))] = 2   # the jeans (dark navy)
    P[(V[:, 2] < hip + 0.08) & blue & (v <= 0.42) & (np.abs(V[:, 0]) < 0.2)] = 2     # (their waistband in the open jacket)
    # the hair: the biggest orange piece of the head (the brows are pieces of their own)
    hd = orange & (head > 0.5); Eh = E[hd[E[:, 0]] & hd[E[:, 1]]]; lab = components(len(V), Eh)
    ids, cnt = np.unique(lab[hd], return_counts=True); P[hd & (lab == ids[np.argmax(cnt)])] = 3
    P[(foot > 0.6) | (hand > 0.5) | (bag > 0.5)] = 0
    tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); tri = tri.reshape(-1, 3)
    assert len(tri) == len(me.polygons), 'expected triangles'
    votes = np.stack([(P[tri] == p).sum(1) for p in range(4)], 1)
    return np.argmax(votes, 1), tri


def rig_z(bone): return RIG.data.bones[bone].head_local.z


def finish(o, rig, img, px):
    png = os.path.join(OUT, NAME + 'Atlas.png')
    mb.face_parts = face_parts                                  # (meshy_boy.paint does the rest as for the boy)
    refs = mb.paint(o, img, px, png)
    o.data.materials.clear(); o.data.materials.append(atlas_material('Kid', png))
    o.name = 'Kid'; o.data.name = 'Kid'
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    export_fbx([o, rig], os.path.join(OUT, NAME + '.fbx'))
    cols = {'top': refs.get(1, (1, 1, 1)), 'legwear': refs.get(2, (1, 1, 1)), 'hair': refs.get(3, (1, 1, 1)), 'accent': mb.ACCENT}
    with open(os.path.join(OUT, NAME + '.json'), 'w') as f:
        json.dump(dict({k: [round(float(c), 4) for c in srgb(v)] for k, v in cols.items()}, tris=tris), f)
    neck = rig.data.bones['Head'].head_local.z; top = max(v.co.z for v in o.data.vertices)
    log('%s: %d tris; the Head joint at %.3f of %.3f (%.3f of his height): at 1.77 m tall, a neck height of %.3f' % (
        NAME, tris, neck, top, neck / top, 1.77 * neck / top))


if __name__ == '__main__':
    obj, img = load()
    PX = px = texture_pixels(img)
    decimate(obj, TRIS)
    tidy(obj)
    J, info = find_joints(obj)
    INFO_J = J
    debug_points(obj, px, J, os.path.join(OUT, NAME + '_joints.png'))
    if '--joints-only' in argv: sys.exit(0)
    legs_apart(obj, info)
    RIG = rig = make_rig(J)
    weigh_near(obj, rig, info)
    J = repose(obj, rig, J)
    backpack(obj, rig, px)
    nose(obj, rig)
    finish(obj, rig, img, px)
