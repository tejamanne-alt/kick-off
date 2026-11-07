# A playable kid from a textured, single-mesh model standing alone (an AI-generated model the user supplied, exported as
# FBX: one fused mesh, one 2048 base-colour texture, no rig), in the same contract as the game's other kids (one skinned
# mesh 'Kid' under 'KidRig', one material: vertex colours times the atlas; UV2.x the outfit part; the bones the game
# poses; Nose and Bag markers; <Name>.json with the default outfit colours). Each supplied model has a profile (PROFILES)
# with its own colour rules:
#   backpack_boy  Max (BackpackBoy): an A-posed teen; ginger hair, a denim jacket over a grey hoodie, dark jeans, white
#                 sneakers and a brown backpack.
#   first_day     Leo (PrimaryBoy2): a primary-school boy standing with his arms down; short black hair, a white
#                 sweatshirt with purple sleeves, khaki cargo joggers with a red drawstring, a purple backpack, and bare
#                 feet: he is given sneakers of his own (shoes()).
#   unicorn       Zoe (PrimaryGirl2): a primary-school girl; black hair in a long braid, a pink rainbow-unicorn jacket over
#                 a white T-shirt, terracotta trousers, black shoes, a backpack in the jacket's print (found by its shape).
#   explorer      Mia (PrimaryGirl): an A-posed primary-school girl; shoulder-length black hair with a headband, a white
#                 T-shirt, red shorts, bare legs, white socks, pink sneakers, a beige backpack (found by its shape).
#   plaid         Kai (PrimaryBoy): a primary-school boy; short black hair, a red plaid flannel shirt with a white hood,
#                 light-blue cargo jeans, black-and-white sneakers, a grey backpack.
# tools/blender/README.md ("The backpack boy, Leo and Zoe") says more. It reuses meshy_boy.py's helpers.
#
#   blenv/bin/python meshy_teen.py -- /abs/source.fbx /abs/outdir [--profile backpack_boy|first_day|unicorn|explorer|plaid] [--name <Name>]
#       [--tris 30000] [--joints-only]
#     -> outdir/<Name>.fbx, <Name>.blend, <Name>.json, <Name>Atlas.png, <Name>_joints.png
#
# The steps:
#   tidy      decimated to the budget, scaled to the teen boy's height (2.14; the game scales by the neck anyway), feet
#             at z = 0, the head centred over the origin, facing -Y.
#   joints    from the mesh as it stands: each arm from its own cross-sections below the armpit (an A-pose or hanging
#             down), a straight line from the fingertips; the legs' cross-sections (the arms left out) and the crotch, the
#             soles; the neck at its narrowest, the shoulders below it inside the torso.
#   separate  the legs, if the scan joins them below the crotch, are cut apart and each side's holes closed.
#   rig       the game's armature on those joints, weights by nearness to the bones; the arms hanging as the teen boy's,
#             the legs in under the hips, baked in and made the rest pose; the backpack follows the Bag bone (the game
#             swings it as he runs), fading where it meets his back.
#   paint     outfit parts by texture colour (the profile's rules): the top 1, the legwear 2, the hair 3, the rest 0; the
#             atlas has those parts' texels divided by their colour, which the vertex colours carry instead, so the shop's
#             outfits recolour them (ModelOutfit) and the default looks as the model did.
#   shoes     (a barefoot model) sneakers grown from each foot's own surface, smoothed, set out a little and given a
#             flat sole, skinned as the foot is; coloured by vertex colour over a white patch made in the atlas.
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
PROFILE_NAME = argv[argv.index('--profile') + 1] if '--profile' in argv else 'backpack_boy'
TRIS = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 30000
os.makedirs(OUT, exist_ok=True)
DEFAULT_NAMES = {'backpack_boy': 'BackpackBoy', 'first_day': 'PrimaryBoy2', 'unicorn': 'PrimaryGirl2', 'explorer': 'PrimaryGirl', 'plaid': 'PrimaryBoy'}
NAME = argv[argv.index('--name') + 1] if '--name' in argv else DEFAULT_NAMES[PROFILE_NAME]
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
    """Weld the scan's seams (Meshy exports face -y, as the game's models do), scale it to the teen boy's height with the
    feet on z = 0, centred on the head."""
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update()
    V = verts_np(o); zmin, zmax = V[:, 2].min(), V[:, 2].max(); H = zmax - zmin
    k = HEIGHT / H
    # the head's middle is the middle across (a stance may be uneven); the hips' front part (a backpack makes the back
    # no guide) the middle front to back
    head = V[V[:, 2] > zmin + 0.9 * H]
    cx = (head[:, 0].min() + head[:, 0].max()) / 2
    hips = V[(V[:, 2] > zmin + 0.45 * H) & (V[:, 2] < zmin + 0.55 * H) & (np.abs(V[:, 0] - cx) < 0.1 * H)]
    cy = np.percentile(hips[:, 1], 30)
    o.data.transform(Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation((-cx, -cy, -zmin))); o.data.update()
    log('scaled by %.4f' % k)


# ------------------------------------------------------------------------------------------------ joints
HAND = 0.20              # fingertips to wrist along the arm (the hands hang open)


def arm_rings(V, T, sg, H):
    """One arm's cross-sections, from the armpit down to the fingertips: going down from the shoulders, the outermost
    small outline on that side at each height, beside the body (not behind it: a backpack, the hair); a run of them
    follows on from one to the next (where the arm touches the body its outline is the body's, so a short gap is passed
    over), and the longest run is the arm (a sleeve's edge by the shoulder, or a leg below the hand, are short runs of
    their own). Returned from the fingertips up."""
    runs, rings = [], []
    for z in np.arange(0.70 * H, 0.25 * H, -0.008 * H):
        best = None
        front = V[np.abs(V[:, 2] - z) < 0.005 * H][:, 1].min()
        for P in slice_loops(V, T, z, 8):
            c = P.mean(0)
            if sg * c[0] < 0.06 * H or np.ptp(P[:, 0]) > 0.09 * H or np.ptp(P[:, 1]) > 0.09 * H: continue
            if c[1] > front + 0.13 * H: continue
            if best is None or sg * c[0] > sg * best[0]: best = np.append(c, max(np.ptp(P[:, 0]), np.ptp(P[:, 1])) / 2)
        if best is None:
            if rings and rings[-1][2] - z > 0.07 * H: runs.append(rings); rings = []
            continue
        if rings and np.linalg.norm(best[:2] - rings[-1][:2]) > 0.03 * H + 0.5 * (rings[-1][2] - z - 0.008 * H):
            runs.append(rings); rings = []
        rings.append(best)
    runs.append(rings)
    return np.array(max(runs, key=len)[::-1])                    # (x, y, z, the outline's half size)


def find_joints(o):
    V = verts_np(o); T = mesh_tris(o); H = V[:, 2].max()
    J, info = {}, {}
    # the arms: a straight line through each one's cross-sections; the fingertips the lowest point near it
    lines_arm, near_arm = {}, np.zeros(len(V), bool)
    for n, sg in (('L', 1), ('R', -1)):
        R = arm_rings(V, T, sg, H)
        assert len(R) >= 6, 'no %s arm found apart from the body' % n
        info['armr' + n] = np.percentile(R[:, 3], 90); info['rings' + n] = R.copy(); R = R[:, :3]
        c = R.mean(0); d = np.linalg.svd(R - c)[2][0]; d = d if d[2] > 0 else -d
        lines_arm[n] = (c, d, R)
        dl, F = seg_dist(V, R[0] - d * 0.1 * H, R[-1])
        arm = (dl < 0.06 * H) & (V[:, 2] < R[-1][2]) & (V[:, 2] > R[0][2] - 0.05 * H) & (V[:, 0] * sg > 0.04 * H)
        near_arm |= arm
        tz = R[0][2] - 0.012 * H                                # (the fingertips: just below the lowest outline)
        J['tip' + n] = c + d * (tz - c[2]) / d[2]               # (on the line: the hand's own centre)
        info['armtop' + n] = R[-1][2]
    # the legs, with the arms left out of the cross-sections
    Tm = T[~near_arm[T].any(1)]
    def two(z):
        # two outlines of a size side by side (a jacket's hem and a backpack's bottom are one in front of the other)
        L = slice_loops(V, Tm, z, 20)
        if len(L) < 2 or len(L[1]) < 0.6 * len(L[0]): return None
        a, b = L[0].mean(0), L[1].mean(0)
        return L[:2] if abs(a[0] - b[0]) > 0.1 and abs(a[1] - b[1]) < 0.05 else None
    crotch = next((z for z in np.arange(0.53 * H, 0.30 * H, -0.005) if two(z) and two(z - 0.01)), None)   # (two levels running)
    top = crotch
    if crotch is None:
        # wide shorts or a skirt hide it: the legs show below the hems, and the crotch is put 0.10 of the height above
        # them (the cut between the legs, legs_apart, then parts the shorts down the middle)
        top = next(z for z in np.arange(0.30 * H, 0.12 * H, -0.005) if two(z) and two(z - 0.01))
        crotch = top + 0.10 * H
        log('legs: no crotch shows above %.3f; the legs part at %.3f under the clothes, the crotch put at %.3f' % (0.30 * H, top, crotch))
    info['crotch'] = crotch
    a, b = sorted(two(top - 0.01), key=lambda P: P[:, 0].mean())
    lines = {'R': [a.mean(0)], 'L': [b.mean(0)]}
    for z in np.arange(top - 0.03, 0.06 * H, -0.02):
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

    # the trunk: its centre across, and a little behind its front (a backpack makes the back no guide)
    x0 = (J['hipL'][0] + J['hipR'][0]) / 2
    def trunk(z):
        P = np.concatenate(slice_loops(V, T, z, 8)); P = P[np.abs(P[:, 0] - x0) < 0.08]
        return np.array([x0, P[:, 1].min() + 0.12, z])
    J['pelvis'] = np.array([x0, (J['hipL'][1] + J['hipR'][1]) / 2, crotch + 0.09])

    # the neck: the narrowest cross-section of the middle between the chest and the head's middle; the Head joint just
    # above it, the shoulders 0.065 of the height below it
    mid = np.abs(V[:, 0] - x0) < 0.095 * H; Tn = T[mid[T].all(1)]
    widths = []
    for z in np.arange(0.70 * H, 0.93 * H, 0.005):
        L = slice_loops(V, Tn, z, 12)
        if L: widths.append((np.ptp(L[0][:, 0]), z))
    nz = min(widths)[1]
    # (a hood round the neck or a braid behind it can make that fall on the shoulders: the chin, where the front steps
    # back by 4 cm going down the face, is a floor for it)
    fr = []
    for z in np.arange(0.93 * H, 0.70 * H, -0.01 * H):
        m = (np.abs(V[:, 2] - z) < 0.006 * H) & (np.abs(V[:, 0] - x0) < 0.05)
        fr.append((z, V[m, 1].min() if m.any() else np.nan))
    chin = next((za for (za, a), (zb_, b) in zip(fr[:-1], fr[1:]) if za < 0.9 * H and b - a > 0.04), None)
    if chin is not None and nz < chin - 0.03 * H:
        log('neck: the narrowest cross-section (%.3f) is below the chin (%.3f): the chin is taken' % (nz, chin)); nz = chin
    shoulder_z = nz - 0.065 * H
    # the spine and the chest at 0.41 and 0.68 of the way from the crotch up to the shoulders
    J['spine'] = trunk(crotch + 0.41 * (shoulder_z - crotch)); J['chest'] = trunk(crotch + 0.68 * (shoulder_z - crotch))
    # the arms' joints: the shoulder on the arm's line at the shoulders' height, kept inside the torso's outline; the
    # wrist a hand's length up from the tips, the elbow half way
    for n, sg in (('L', 1), ('R', -1)):
        c, d, R = lines_arm[n]
        top = V[(np.abs(V[:, 2] - shoulder_z) < 0.02 * H) & (V[:, 1] < J['chest'][1] + 0.05)]
        edge = (sg * (top[:, 0] - x0)).max() - 0.08                      # (the shoulder inside the torso's outline)
        if R[-1][2] - R[0][2] < 0.15 * H:
            # only the hand shows apart from the body (baggy sleeves hang against a loose shirt): its outlines say
            # little of the arm's direction, so the shoulder is taken from the torso's outline and the arm runs
            # straight from it to the hand
            S = np.array([x0 + sg * edge, J['chest'][1], shoulder_z])
            hand = R.mean(0); d = (S - hand) / np.linalg.norm(S - hand); c = hand
            J['tip' + n] = hand + d * (R[0][2] - 0.012 * H - hand[2]) / d[2]
            log('arms: only the %s hand shows apart from the body; the shoulder is taken from the torso' % n)
            info['hand_only' + n] = True
            info['armtop' + n] = shoulder_z - 0.07 * H                 # (the sleeve is split from the shirt up to the armpit)
        else:
            S = c + d * (shoulder_z - c[2]) / d[2]
            S[0] = x0 + sg * min(abs(S[0] - x0), edge)
        S[1] = J['chest'][1]
        tipc = J['tip' + n]
        W = tipc + (S - tipc) / np.linalg.norm(S - tipc) * HAND
        J['shoulder' + n], J['wrist' + n] = S, W
        ez = (S[2] + W[2]) / 2; J['elbow' + n] = c + d * (ez - c[2]) / d[2] + np.array([0, 0.02, 0])   # (on the arm)
    sz = (J['shoulderL'][2] + J['shoulderR'][2]) / 2
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


def cut_apart(o, bm, lab, band, px):
    """Cut out the faces between an arm and the body (lab: 0 body, 1/2 the arms) and close each side's holes."""
    me = o.data
    cut = [f for f in bm.faces if any(band[x.index] for x in f.verts) and len({int(lab[x.index]) for x in f.verts}) > 1]
    rim = {x for f in cut for x in f.verts}
    open0 = sum(1 for e in bm.edges if e.is_boundary)
    bmesh.ops.delete(bm, geom=cut, context='FACES')
    side = {x: int(lab[x.index]) for x in bm.verts}                      # (whose each old vertex is: 0 body, 1/2 arms)
    # each hole the cut left closed (its rim is all on one side: the cut parted the two), in the texture's colour at
    # the rim's most typical corner
    edges = [e for e in bm.edges if e.is_boundary and e.verts[0] in rim and e.verts[1] in rim]
    new = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
    new = bmesh.ops.triangulate(bm, faces=new)['faces']
    # (a fill that bridges the cut, an arm's rim and the body's in one loop, would join them again: it goes)
    bridge = [f for f in new if len({side.get(x, -1) for x in f.verts} - {-1}) > 1]
    bmesh.ops.delete(bm, geom=bridge, context='FACES_ONLY'); new = [f for f in new if f.is_valid]
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')   # (their loose edges too)
    uv = bm.loops.layers.uv.active
    for f in new:
        cand = [l[uv].uv.copy() for x in f.verts for l in x.link_loops if l.face not in new]
        if not cand: continue
        cc = mb.sample(px, np.array([tuple(u) for u in cand]))
        src = cand[int(np.argmin(np.abs(cc - np.median(cc, 0)).sum(1)))]
        for l in f.loops: l[uv].uv = src
    made = len(new)
    # what holes_fill left (a rim that is no clean loop): each connected run closed by a fan to its middle
    edges = [e for e in bm.edges if e.is_boundary and e.verts[0] in rim and e.verts[1] in rim]
    up = {e: e for e in edges}
    def find(e):
        while up[e] is not e: up[e] = up[up[e]]; e = up[e]
        return e
    at = {}
    edges = [e for e in edges if side.get(e.verts[0], -1) == side.get(e.verts[1], -2)]   # (each side on its own)
    up = {e: e for e in edges}
    for e in edges:
        for x in e.verts:
            if x in at: up[find(e)] = find(at[x])
            else: at[x] = e
    runs = {}
    for e in edges: runs.setdefault(find(e), []).append(e)
    for g in runs.values():
        if len(g) < 2: continue
        ring = {x for e in g for x in e.verts}
        c = bm.verts.new(sum((x.co for x in ring), Vector()) / len(ring))
        cand = [l[uv].uv.copy() for x in ring for l in x.link_loops]   # (the rim's most typical colour)
        cc = mb.sample(px, np.array([tuple(u) for u in cand]))
        src = cand[int(np.argmin(np.abs(cc - np.median(cc, 0)).sum(1)))]
        for e in g:
            l = e.link_loops[0]; a, b = l.vert, l.link_loop_next.vert
            try: f = bm.faces.new((c, b, a))
            except ValueError: continue
            for fl in f.loops: fl[uv].uv = src
            made += 1
    bad = [x for x in bm.verts if not x.link_faces]; bmesh.ops.delete(bm, geom=bad, context='VERTS')
    left = sum(1 for e in bm.edges if e.is_boundary) - open0
    bm.to_mesh(me); bm.free(); me.update()
    log('arms: %d faces cut where they touch the body; the holes closed with %d faces (%d open edges more than before; '
        '%d fill faces across the cut dropped)' % (len(cut), made, left, len(bridge)))


def arms_apart(o, px, J, info):
    """Where a forearm or a hand touches the body in the scan (Leo's rest on his trouser pockets), the surfaces are
    one: cut them apart. Below the armpit (and leaving out the profile's colours that are never an arm's: his trousers) each point is the arm's if it is nearer the arm's line than the body's axis,
    each distance measured in that part's own thickness (the arm's from its cross-sections, the torso's from the
    shoulders' width, a leg's from its cross-sections); the arm is the part of that joined to the fingertips. The faces
    between an arm and the rest go, and the holes are closed."""
    V = verts_np(o); me = o.data; E = edges_np(o)
    x0 = J['pelvis'][0]; rt = (abs(J['shoulderL'][0] - x0) + abs(J['shoulderR'][0] - x0)) / 2 + 0.03
    legs = [P for P in slice_loops(V, mesh_tris(o), info['crotch'] - 0.1, 20)[:2]]
    rl = np.mean([max(np.ptp(P[:, 0]), np.ptp(P[:, 1])) / 2 for P in legs])
    body = (seg_dist(V, J['pelvis'], J['neck0'])[0]) / rt
    for n in 'LR':
        body = np.minimum(body, np.min([seg_dist(V, J[a + n], J[b + n])[0] for a, b in (('hip', 'knee'), ('knee', 'ankle'))], 0) / rl)
    lab = np.zeros(len(V), dtype=np.int64); band = np.ones(len(V), bool)
    not_arm = PROFILE['not_arm'](vertex_colours(o, px)) if PROFILE.get('not_arm') else np.zeros(len(V), bool)
    for n, k in (('L', 1), ('R', 2)):
        d = np.min([seg_dist(V, J[a + n], J[b + n])[0] for a, b in (('shoulder', 'elbow'), ('elbow', 'wrist'), ('wrist', 'tip'))], 0)
        arm = (d / info['armr' + n] < body) & (V[:, 2] < info['armtop' + n] - 0.02) & ~not_arm
        if info.get('hand_only' + n):
            # (a hand in a pocket: its fingers go on below its last outline, into the pocket; they go with the hand)
            u = (J['tip' + n] - J['wrist' + n]) / np.linalg.norm(J['tip' + n] - J['wrist' + n])
            fingers = seg_dist(V, J['tip' + n], J['tip' + n] + u * 0.12)[0] < info['armr' + n] + 0.03
            arm |= fingers & ~not_arm
            # (fingertips fused to the pocket's surface are not joined to the hand in the mesh: their skin colour says
            #  whose they are)
            hh, ss, vv = hsv(vertex_colours(o, PX))
            tips = fingers & (hh > 8) & (hh < 40) & (ss > 0.2) & (ss < 0.7) & (vv > 0.2) & (vv < 0.85)
        Ea = E[arm[E[:, 0]] & arm[E[:, 1]]]; cl = components(len(V), Ea)
        tipv = np.argmin(np.where(arm, np.linalg.norm(V - J['tip' + n], axis=1), np.inf))
        lab[arm & (cl == cl[tipv])] = k
        if info.get('hand_only' + n): lab[tips & (lab == 0)] = k
        log('arms: the %s arm, %d vertices below the armpit' % (n, (lab == k).sum()))
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    if info.get('hand_onlyL') or info.get('hand_onlyR'):
        # A sleeve fused to the shirt all the way down: cutting a strip out between them would leave holes the length of
        # the arm. The mesh is split along the seam instead: each face goes with the side most of its corners are on,
        # and the edges between an arm's faces and the body's are split, so nothing is missing while he stands.
        fs = {}
        for f in bm.faces:
            ls = [int(lab[x.index]) for x in f.verts]; fs[f] = max(set(ls), key=lambda k: (ls.count(k), k))
        seam = [e for e in bm.edges if len(e.link_faces) == 2 and fs[e.link_faces[0]] != fs[e.link_faces[1]]]
        bmesh.ops.split_edges(bm, edges=seam)
        # (where the two sides touch only at a corner, the vertex is ripped into one for each fan of faces round it)
        torn = 0
        for x in list(bm.verts):
            if x.is_valid and len({fs.get(f, -1) for f in x.link_faces}) > 1:
                bmesh.utils.vert_separate(x, [e for e in x.link_edges]); torn += 1
        # each side's new opening (the shirt under the sleeve was never scanned: it would show the inside, dark, as
        # the arm swings away) closed on its own, in the rim's most typical colour; after the split no loop has both
        # sides on it
        edges = [e for e in bm.edges if e.is_boundary and len({fs.get(f, -1) for f in e.link_faces}) == 1]
        new = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
        new = bmesh.ops.triangulate(bm, faces=new)['faces']
        uv = bm.loops.layers.uv.active
        for f in new:
            cand = [l[uv].uv.copy() for x in f.verts for l in x.link_loops if l.face not in new]
            if not cand: continue
            cc = mb.sample(px, np.array([tuple(u) for u in cand]))
            src = cand[int(np.argmin(np.abs(cc - np.median(cc, 0)).sum(1)))]
            for l in f.loops: l[uv].uv = src
        bm.verts.ensure_lookup_table()
        bm.to_mesh(me); bm.free(); me.update()
        log('arms: %d corner vertices ripped; the openings closed with %d faces' % (torn, len(new)))
        log('arms: the sleeves split from the body along %d edges (no faces cut)' % len(seam))
    else:
        cut_apart(o, bm, lab, band, px)
    if info.get('hand_onlyL') or info.get('hand_onlyR'):
        # (with only the hands apart from the body, the cut leaves small scraps of cuff and fingers by them: dropped)
        V = verts_np(o); lab = components(len(V), edges_np(o)); ids, cnt = np.unique(lab, return_counts=True)
        dh = np.min([seg_dist(V, J['wrist' + n], J['tip' + n])[0] for n in 'LR'], 0)
        scrap = (np.isin(lab, ids[cnt < 100]) & (dh < 0.12)) | np.isin(lab, ids[cnt < 40])   # (and any loose crumb)
        if scrap.any(): delete_verts(o, ~scrap); log('arms: %d scrap vertices by the hands dropped' % scrap.sum())


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
    # where a baggy sleeve is fused to a loose shirt all the way down (only the hand shows apart: find_joints), a
    # point follows the arm only if it is relatively nearer the arm than the body's axis (each in its own thickness:
    # the sleeve's about 0.045 of the height, the trunk's half the shoulders' width), or near the shoulder joint; else
    # the shirt's side and the backpack would stretch out with the arm
    Hh = V[:, 2].max(); rt = (abs(B['UpperArm.L'].head_local.x - B['UpperArm.R'].head_local.x)) / 2 + 0.03
    dbody = seg_dist(V, np.array(B['Hips'].head_local), np.array(B['Neck'].head_local))[0] / rt
    for n in 'LR':
        if not info.get('hand_only' + n): continue
        segs = [(np.array(B[b + n].head_local), np.array(B[b + n].tail_local)) for b in ('UpperArm.', 'LowerArm.', 'Hand.')]
        darm = np.min([seg_dist(V, a, b)[0] for a, b in segs], 0) / (0.045 * Hh)
        near_sh = np.linalg.norm(V - segs[0][0], axis=1) < 0.08
        off = (darm >= dbody) & ~near_sh
        for b in ('UpperArm.', 'LowerArm.', 'Hand.'): allow[off, ix[b + n]] = False
        log('weights: the %s arm keeps to its sleeve (%d vertices nearer the body left off it)' % (n, off.sum()))
    # below the armpits each arm is a piece of its own (arms_apart): only it takes that arm's bones, and it takes
    # nothing but them and the chest's
    za = min(info['armtopL'], info['armtopR']) - 0.02
    low = V[:, 2] < za; Ea = E[low[E[:, 0]] & low[E[:, 1]]]; lab = components(len(V), Ea)
    low0, lab0 = low, lab
    for n in 'LR':
        low, lab = low0, lab0
        if info.get('hand_only' + n):
            # (only the hand shows apart: it is the arm's own piece from just under its own outlines' top, which the
            # two hands, hanging at different heights, need each for itself)
            low = V[:, 2] < info['armtop' + n] - 0.02; Ea = E[low[E[:, 0]] & low[E[:, 1]]]; lab = components(len(V), Ea)
        seed = np.argmin(np.where(low, np.linalg.norm(V - np.array(B['Hand.' + n].tail_local), axis=1), np.inf))
        piece = low & (lab == lab[seed])
        log('weights: the %s arm below the armpit is %d of %d vertices' % (n, piece.sum(), low.sum()))
        if piece.sum() > 0.25 * low.sum(): continue                      # (still joined to the body: leave it)
        # (and any small loose piece by its forearm or hand: a bit of the hand the cut left behind)
        fa = np.min([seg_dist(V, np.array(B[b + n].head_local), np.array(B[b + n].tail_local))[0] for b in ('LowerArm.', 'Hand.')], 0)
        ids, cnt = np.unique(lab[low], return_counts=True)
        for i, c in zip(ids, cnt):
            m = low & (lab == i)
            if c < 0.05 * low.sum() and not (m & piece).any() and np.median(fa[m]) < 0.08: piece |= m
        armb = [ix[b + n] for b in ('UpperArm.', 'LowerArm.', 'Hand.')]
        above_elbow = V[:, 2] > B['LowerArm.' + n].head_local.z
        for j in range(len(names)):
            if j in armb: allow[low & ~piece, j] = False; allow[piece, j] = True
            elif names[j] == 'Chest': allow[piece & ~above_elbow, j] = False     # (the chest's pull ends at the elbow)
            else: allow[piece, j] = False
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
    """The backpack's texels, by the profile's colour (h0..h1 degrees of hue, the least saturation, a band of value)."""
    h, s, v = hsv(Cc); h0, h1, s0, v0, v1 = PROFILE['pack'][:5]
    s1 = PROFILE['pack'][5] if len(PROFILE['pack']) > 5 else 1.01           # (an optional most saturation: a grey pack)
    return (h >= h0) & (h <= h1) & (s > s0) & (s < s1) & (v > v0) & (v < v1)


def backpack(o, rig, px):
    """The backpack: the profile's colour (or, for 'shape', anything but hair) and behind the back. It follows the Bag bone (head at its top, tail toward its bottom, on
    the Chest), fading over the few centimetres where it meets his back so the swing bends rather than tears."""
    V = verts_np(o); E = edges_np(o); B = rig.data.bones
    chest = np.array(B['Chest'].head_local); hips = np.array(B['Hips'].head_local)
    band = (V[:, 2] > hips[2]) & (V[:, 2] < np.array(B['Head'].head_local)[2]) & (np.abs(V[:, 0]) < 0.3)
    # (sleeves the pack's colour, hanging by its sides, are the arms')
    for n in 'LR':
        for bn in ('UpperArm.', 'LowerArm.', 'Hand.'):
            band &= seg_dist(V, np.array(B[bn + n].head_local), np.array(B[bn + n].tail_local))[0] > 0.09
    if PROFILE['pack'] == 'shape':
        # a pack in the jacket's own print: it is what stands behind the back line (the back's furthest point where it
        # is least, between the crotch and the chest: below the pack), but not the hair (a braid hangs down over it)
        h, s_, v = hsv(vertex_colours(o, px)); pack = band & (v >= 0.2)
        z0 = (B['UpperLeg.L'].head_local.z + B['UpperLeg.R'].head_local.z) / 2 - 0.04
        prof = []
        for z in np.arange(z0, chest[2], 0.02):
            m = (np.abs(V[:, 2] - z) < 0.01) & (np.abs(V[:, 0]) < 0.12)
            # (only slices through the whole trunk, front to back: between the legs a few stray vertices of the front)
            if m.sum() > 40 and np.ptp(V[m, 1]) > 0.15: prof.append(np.percentile(V[m, 1], 95))
        yb = np.full(len(V), min(prof) + 0.03)
        log('backpack: by its shape, behind y = %.3f' % yb[0])
    else:
        # his back at each height: the furthest-back point of what is not the pack, near the middle
        if PROFILE.get('face_colours'):
            # (a texture in many small islands: a vertex is the pack's if most of its faces are, each by its own colour)
            me = o.data; tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri)
            tri = tri.reshape(-1, 3); fp = is_pack(face_colours(o, px)).astype(float)
            acc = np.zeros(len(V)); cnt = np.zeros(len(V))
            np.add.at(acc, tri.ravel(), np.repeat(fp, 3)); np.add.at(cnt, tri.ravel(), 1)
            pack = (acc > 0.5 * np.maximum(cnt, 1)) & band
        else:
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
    w = w * np.all((V > lo) & (V < hi), 1) * pack            # (only the pack's own colour: the seat of the trousers
                                                             #  behind the back line is not the pack's)
    deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(4):
        acc = np.zeros(len(V)); np.add.at(acc, E[:, 0], w[E[:, 1]]); np.add.at(acc, E[:, 1], w[E[:, 0]])
        w = np.maximum(w * core, 0.5 * w + 0.5 * acc / np.maximum(deg, 1))
    top = np.array([P[:, 0].mean(), np.median(P[:, 1]), P[:, 2].max()])
    bot = np.array([top[0], top[1], P[:, 2].min()])
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    b = eb.new('Bag'); b.head = Vector(top); b.tail = Vector(top * 0.4 + bot * 0.6); b.roll = 0; b.parent = eb['Chest']
    bpy.ops.object.mode_set(mode='OBJECT')
    w = w * PROFILE.get('bag', 1.0)                           # (a pack fused to much of the back swings less)
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
def bone_weights(o):
    W, names = weights(o)
    return lambda *ns: sum(W[:, names.index(n)] for n in ns if n in names)


def biggest_piece(o, mask):
    """The largest connected piece of the vertices in mask."""
    E = edges_np(o); Eh = E[mask[E[:, 0]] & mask[E[:, 1]]]; lab = components(len(mask), Eh)
    ids, cnt = np.unique(lab[mask], return_counts=True)
    return mask & (lab == ids[np.argmax(cnt)])


def by_vertex_votes(o, P):
    """Each face takes the part most of its corners have."""
    me = o.data
    tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); tri = tri.reshape(-1, 3)
    assert len(tri) == len(me.polygons), 'expected triangles'
    votes = np.stack([(P[tri] == p).sum(1) for p in range(4)], 1)
    return np.argmax(votes, 1), tri


def khaki(Cc):
    """Leo's cargo joggers' colour."""
    h, s, v = hsv(Cc)
    return (h > 15) & (h < 55) & (s > 0.08) & (s < 0.45) & (v > 0.3)


def red_shorts(Cc):
    """Mia's shorts' red."""
    h, s, v = hsv(Cc)
    return ((h < 15) | (h > 335)) & (s > 0.45) & (v > 0.12)              # (its folds shade to a deep maroon)


def face_colours(o, px):
    """Each face's texture colour at its own centre (a vertex's colour averages its corners, which on a texture cut
    into many small islands mixes the neighbouring islands)."""
    me = o.data; nl = len(me.loops)
    UV = np.empty(nl * 2); me.uv_layers[0].data.foreach_get('uv', UV); UV = UV.reshape(-1, 3, 2).mean(1)
    return mb.sample(px, UV)


def parts_explorer(o, px):
    """Mia's parts, by each face's own texture colour: 1 the white T-shirt, 2 the red shorts, 3 the hair (the biggest
    dark piece above the shorts); 0 the skin, the headband, the backpack, the socks and the pink sneakers."""
    me = o.data; V = verts_np(o); bw = bone_weights(o)
    tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); tri = tri.reshape(-1, 3)
    assert len(tri) == len(me.polygons), 'expected triangles'
    fw = lambda w: w[tri].mean(1)
    foot = fw(bw('Foot.L', 'Foot.R')); hand = fw(bw('Hand.L', 'Hand.R')); bag = fw(bw('Bag')); head = fw(bw('Head'))
    Cf = face_colours(o, px); h, s, v = hsv(Cf); z = V[tri][:, :, 2].mean(1)
    hip = rig_z('UpperLeg.L'); shorts = red_shorts(Cf)
    white = (s < 0.25) & (v > 0.45)
    FP = np.zeros(len(tri), dtype=np.int64)
    FP[white & (z > hip + 0.05) & (head < 0.5)] = 1
    FP[shorts & (z < hip + 0.3)] = 2                                      # (and the waistband)
    # the hair: dark faces above the shorts, the biggest piece of them (by the vertices they share)
    dark = (v < 0.2) & (z > hip + 0.3)
    vm = np.zeros(len(V), bool); vm[tri[dark].ravel()] = True
    hair_v = biggest_piece(o, vm)
    FP[dark & hair_v[tri].all(1)] = 3
    FP[(foot > 0.6) | (hand > 0.5) | (bag > 0.5)] = 0
    return FP, tri


def light_jeans(Cc):
    """Kai's light-blue jeans."""
    h, s, v = hsv(Cc)
    return (h > 190) & (h < 230) & (s > 0.15) & (s < 0.6) & (v > 0.35)


def parts_plaid(o, px):
    """Kai's parts, by each face's own texture colour: 1 the red plaid shirt (its reds and pinks, its white and dark
    lines; the white hood with it), 2 the light-blue cargo jeans, 3 the hair (the biggest dark piece of the head);
    0 the skin, the grey backpack and the sneakers."""
    me = o.data; V = verts_np(o); bw = bone_weights(o)
    tri = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', tri); tri = tri.reshape(-1, 3)
    assert len(tri) == len(me.polygons), 'expected triangles'
    fw = lambda w: w[tri].mean(1)
    foot = fw(bw('Foot.L', 'Foot.R')); hand = fw(bw('Hand.L', 'Hand.R')); bag = fw(bw('Bag')); head = fw(bw('Head'))
    Cf = face_colours(o, px); h, s, v = hsv(Cf); z = V[tri][:, :, 2].mean(1)
    hip = rig_z('UpperLeg.L')
    red = ((h < 20) | (h > 320)) & (s > 0.2) & (v > 0.25)
    white = (s < 0.2) & (v > 0.6)
    skin = (h > 10) & (h < 40) & (s > 0.25) & (s < 0.65) & (v > 0.3) & (v < 0.8)
    FP = np.zeros(len(tri), dtype=np.int64)
    FP[(red | white) & (z > hip - 0.05) & (head < 0.5) & ~skin] = 1
    FP[light_jeans(Cf) & (z < hip + 0.15)] = 2
    dark = (v < 0.2) & (head > 0.5)
    vm = np.zeros(len(V), bool); vm[tri[dark].ravel()] = True
    FP[dark & biggest_piece(o, vm)[tri].all(1)] = 3
    FP[(foot > 0.6) | (hand > 0.5) | (bag > 0.5)] = 0
    return FP, tri


def terracotta(Cc):
    """Zoe's trousers' colour (her brown skin is darker and yellower)."""
    h, s, v = hsv(Cc)
    return ((h < 22) | (h > 345)) & (s > 0.28) & (s < 0.65) & (v > 0.5)


def parts_unicorn(o, px):
    """Zoe's parts: 1 the jacket in its rainbow-unicorn print (the shop recolours it as shades of one colour), 2 the
    terracotta trousers, 3 the hair with its braid (the biggest dark piece above the hips); 0 the skin, the backpack
    (the same print), the black shoes."""
    V = verts_np(o); bw = bone_weights(o)
    foot = bw('Foot.L', 'Foot.R'); hand = bw('Hand.L', 'Hand.R'); bag = bw('Bag')
    Cc = vertex_colours(o, px); h, s, v = hsv(Cc)
    hip = rig_z('UpperLeg.L'); trousers = terracotta(Cc)
    pinkish = ((h > 280) | (h < 15)) & (s > 0.25) & (v > 0.35)
    light = (s < 0.25) & (v > 0.6)
    P = np.zeros(len(V), dtype=np.int64)
    P[(pinkish | light) & (V[:, 2] > hip + 0.02) & ~trousers] = 1
    P[trousers & (V[:, 2] < hip + 0.15)] = 2
    P[biggest_piece(o, (v < 0.2) & (V[:, 2] > hip + 0.1))] = 3
    P[(foot > 0.6) | (hand > 0.5) | (bag > 0.5)] = 0
    return by_vertex_votes(o, P)


def parts_first_day(o, px):
    """Leo's parts: 1 the sweatshirt's white (its purple sleeves, shoulders and cuffs stay as they are), 2 the khaki
    cargo joggers, 3 the black hair (the biggest dark piece of the head); 0 the skin, the red drawstring, the backpack."""
    V = verts_np(o); bw = bone_weights(o)
    head = bw('Head'); foot = bw('Foot.L', 'Foot.R'); hand = bw('Hand.L', 'Hand.R'); bag = bw('Bag')
    h, s, v = hsv(vertex_colours(o, px))
    hip = rig_z('UpperLeg.L')
    white = (s < 0.2) & (v > 0.55)
    trousers = khaki(vertex_colours(o, px))
    P = np.zeros(len(V), dtype=np.int64)
    P[white & (V[:, 2] > hip - 0.06)] = 1
    P[trousers & (V[:, 2] < hip + 0.12) & ~white] = 2
    P[biggest_piece(o, (v < 0.2) & (head > 0.5))] = 3
    P[(foot > 0.6) | (hand > 0.5) | (bag > 0.5)] = 0
    return by_vertex_votes(o, P)


def parts_backpack_boy(o, px):
    """Max's parts (0 fixed: skin, hoodie, T-shirt, backpack, shoes; 1 the denim jacket; 2 the jeans; 3 the hair), by
    the texture colour, the bones that carry it and the height."""
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
    return by_vertex_votes(o, P)


def rig_z(bone): return RIG.data.bones[bone].head_local.z


# ------------------------------------------------------------------------------------------------ shoes
SOLE = 0.03              # the sole's thickness (the kid stands on it: everything is raised by it)
SHOE_OFF = 0.016         # how far the shoe stands off the foot
SHOE_TOP = 0.035         # the shoe's collar, above the ankle joint
# the sneakers' colours (sRGB): a white upper, a purple band above the sole and a purple heel tab (his sleeves' and his
# backpack's purple), an off-white sole with a grey tread
SHOE_UPPER, SHOE_ACCENT = (0.96, 0.96, 0.97), (0.40, 0.22, 0.66)
SHOE_SOLE, SHOE_TREAD = (0.90, 0.89, 0.86), (0.45, 0.45, 0.48)


def white_patch(o, png):
    """Paint the middle of the atlas's largest unused area white (the shoes map onto it and take their colours from
    their vertex colours). Returns its UV centre."""
    from PIL import Image, ImageDraw
    me = o.data; im = Image.open(png).convert('RGB'); Wd, Hd = im.size
    UV = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', UV); UV = UV.reshape(-1, 3, 2)
    used = Image.new('L', (Wd, Hd), 0); dr = ImageDraw.Draw(used)
    for f in UV: dr.polygon([(u * Wd, (1 - v) * Hd) for u, v in f], fill=255)
    free = np.array(used) == 0; depth = 0
    while True:                                                     # erode until one more step would leave nothing
        e = free.copy()
        for sh in ((0, 1), (0, -1), (1, 0), (-1, 0)): e &= np.roll(free, sh, axis=(0, 1))
        e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = False
        if not e.any(): break
        free = e; depth += 1
    yy, xx = np.argwhere(free)[0]; r = max(depth - 6, 2)
    A = np.array(im); A[yy - r:yy + r + 1, xx - r:xx + r + 1] = 255; Image.fromarray(A).save(png)
    log('shoes: a white patch %d texels across at (%d, %d) of the atlas' % (2 * r + 1, xx, yy))
    return ((xx + 0.5) / Wd, 1 - (yy + 0.5) / Hd)


SHOE_ST, SHOE_RING = 30, 32   # stations along a shoe, points round each


def sneaker(Vf, ankle, toe):
    """A sneaker round one foot's vertices Vf: a loft along the foot (heel to toe) of rounded-box cross-sections, each
    as wide as the foot there and as high as its top, set out by SHOE_OFF, with a flat bottom SOLE below the ground; the
    ends rounded off and closed. Returns its vertices, faces (quads and the end fans) and each vertex's place along the
    foot (0 heel, 1 toe) and height above the sole's bottom."""
    f = toe - ankle; f[2] = 0; f /= np.linalg.norm(f); sv = np.array([-f[1], f[0], 0.0])
    P = Vf - ankle; u = P @ f; v = P @ sv; z = Vf[:, 2]
    u0, u1 = u.min() - SHOE_OFF, u.max() + SHOE_OFF + 0.012
    us = np.linspace(u0, u1, SHOE_ST); step = us[1] - us[0]
    lo, hi, tp = np.zeros(SHOE_ST), np.zeros(SHOE_ST), np.zeros(SHOE_ST)
    for i, ui in enumerate(us):
        uc = np.clip(ui, u.min(), u.max()); m = np.abs(u - uc) < 0.6 * step + 0.008
        if not m.any(): m = np.abs(u - uc) <= np.sort(np.abs(u - uc))[min(5, len(u) - 1)]   # (the nearest few)
        # (the width from the foot below the ankle joint: a trouser cuff hanging round the ankle would make the shoe
        #  bulge and fold there)
        mw = m & (z < ankle[2] + 0.005)
        if not mw.any(): mw = m
        lo[i], hi[i], tp[i] = v[mw].min() - SHOE_OFF, v[mw].max() + SHOE_OFF, z[m].max() + SHOE_OFF
    for arr, keep in ((lo, np.minimum), (hi, np.maximum), (tp, np.maximum)):   # (smoothed along the foot, no toes,
        raw = arr.copy()                                                         #  but never inside the foot)
        for _ in range(3): arr[1:-1] = (arr[:-2] + 2 * arr[1:-1] + arr[2:]) / 4
        arr[:] = keep(arr, raw)
    # the top: the collar's height behind the ankle, then a tongue down to the toe box in a gentle curve (the front of
    # the ankle stands above the foot's cut and would show in a step)
    collar = tp[us <= 0].max() if (us <= 0).any() else tp.max(); toe_top = tp[-4:].max()
    a = np.clip(us / max(u1, 1e-6), 0, 1)
    tp[:] = np.maximum(tp, np.where(us <= 0, collar, toe_top + (collar - toe_top) * (1 - a ** 1.6)))
    zb = -SOLE; R = 0.045; verts, place = [], []
    t = np.linspace(0, 2 * np.pi, SHOE_RING, endpoint=False); cx, cz = np.cos(t), np.sin(t)
    ex, ez = np.sign(cx) * np.abs(cx) ** 0.6, np.sign(cz) * np.abs(cz) ** 0.6   # (a rounded box)
    secs, grow = [], np.ones(SHOE_ST)
    for i, ui in enumerate(us):
        d = min(ui - u0, u1 - ui); k = max(0.3, math.sqrt(max(0.0, 1 - ((R - min(d, R)) / R) ** 2)))
        cv, hw = (lo[i] + hi[i]) / 2, (hi[i] - lo[i]) / 2 * k
        zt = zb + (tp[i] - zb) * max(k, 0.55); zc, hz = (zb + zt) / 2, (zt - zb) / 2
        # how much it must grow for every point of the foot near it to be inside (the rounded corners would cut
        # into a big toe)
        m = np.abs(u - ui) < 0.6 * step + 0.008
        if m.any() and k > 0.99:
            g = ((np.abs(v[m] - cv) / hw) ** 3.33 + (np.abs(z[m] - zc) / hz) ** 3.33).max()
            grow[i] = max(1.0, g ** 0.3)
        secs.append((ui, cv, hw, zc, hz))
    # (the growth spread along the shoe, so neighbouring sections never fold over each other)
    grow = np.array([grow[max(0, i - 3):i + 4].max() for i in range(SHOE_ST)])
    for _ in range(3): grow[1:-1] = (grow[:-2] + 2 * grow[1:-1] + grow[2:]) / 4
    # no dips along the shoe (a foot's triangles would cut through one): the half-width and the top fill every valley,
    # rising to their highest and falling after it
    # no dips along the shoe (a foot's triangles would cut through one): each side and the top fill every valley,
    # rising to their furthest and falling back after it
    def unimodal(a):
        return np.maximum(a, np.minimum(np.maximum.accumulate(a), np.maximum.accumulate(a[::-1])[::-1]))
    right = unimodal(np.array([sc[1] + sc[2] * gi for sc, gi in zip(secs, grow)]))
    left = -unimodal(-np.array([sc[1] - sc[2] * gi for sc, gi in zip(secs, grow)]))
    tops = unimodal(np.array([sc[3] + sc[4] * gi for sc, gi in zip(secs, grow)]))
    for (ui, _, _, _, _), a, b, zt in zip(secs, left, right, tops):
        cv, hw = (a + b) / 2, (b - a) / 2; zc, hz = (zb + zt) / 2, (zt - zb) / 2
        for j in range(SHOE_RING):
            w = hw * (1.05 if ez[j] < -0.6 else 1.0)                  # (a lip: the sole a little wider)
            q = ankle + f * ui + sv * (cv + w * ex[j]); q[2] = max(zc + hz * ez[j], zb)
            verts.append(q); place.append(((ui - u0) / (u1 - u0), q[2] - zb))
    faces = []
    for i in range(SHOE_ST - 1):
        for j in range(SHOE_RING):
            a, b = i * SHOE_RING + j, i * SHOE_RING + (j + 1) % SHOE_RING
            faces.append((a, b, b + SHOE_RING, a + SHOE_RING))
    for i, sgn in ((0, -1), (SHOE_ST - 1, 1)):                      # the ends closed by a fan
        ring = np.array(verts[i * SHOE_RING:(i + 1) * SHOE_RING]); c = ring.mean(0) + f * sgn * 0.004
        verts.append(c); place.append((0.0 if i == 0 else 1.0, c[2] - zb)); ci = len(verts) - 1
        for j in range(SHOE_RING):
            a, b = i * SHOE_RING + j, i * SHOE_RING + (j + 1) % SHOE_RING
            faces.append((a, b, ci) if sgn > 0 else (b, a, ci))
    return np.array(verts), faces, place


ANKLE_BLEND = 0.05       # above the collar, the leg's skin goes over to the shin within this


def shin_share(dz):
    """How much of a point of a shoe (or the leg in it) dz above the ankle joint follows the shin: none below 1.5 cm
    over the joint, rising to half at the collar (more shears the shoe off the foot as the ankle bends), then to all of
    it ANKLE_BLEND above the collar (the bare ankle there would otherwise push through the tongue as the ankle bends)."""
    if dz <= SHOE_TOP: return 0.5 * float(np.clip((dz - 0.015) / (SHOE_TOP - 0.015), 0, 1))
    return 0.5 + 0.5 * float(np.clip((dz - SHOE_TOP) / ANKLE_BLEND, 0, 1))


def shoes(o, rig, uv):
    """Sneakers for bare feet: a sneaker shape round each foot (sneaker()), skinned to the foot (the shin's share
    rising up the collar: shin_share);
    coloured by vertex colour (the atlas under them is a white patch): a white upper, a purple band above the sole and a
    purple heel tab, an off-white sole, a grey tread; outfit part 0. Everything is then raised by the sole."""
    me = o.data; V = verts_np(o); W, names = weights(o); B = rig.data.bones
    sm = bpy.data.meshes.new('Shoes'); out = bmesh.new()
    uvl = out.loops.layers.uv.new(me.uv_layers[0].name); pl = out.loops.layers.uv.new(me.uv_layers[1].name)
    col = out.loops.layers.float_color.new('Col')
    shoe_w = []
    def rgba(c): return Vector(tuple(float(x) for x in lin(c)) + (1.0,))
    for n in 'LR':
        ankle = np.array(B['Foot.' + n].head_local); toe = np.array(B['Foot.' + n].tail_local)
        leg = (W[:, names.index('Foot.' + n)] + W[:, names.index('LowerLeg.' + n)] > 0.5)
        idx = np.where(leg & (V[:, 2] < ankle[2] + SHOE_TOP))[0]
        SV, faces, place = sneaker(V[idx], ankle, toe)
        # the foot inside bends as its shoe does (or a toe weighted to the shin would poke through), and so, less and
        # less, does the ankle above the collar
        for k in np.where(leg & (V[:, 2] < ankle[2] + SHOE_TOP + ANKLE_BLEND))[0]:
            t = shin_share(V[k, 2] - ankle[2]); W[k] = 0
            W[k, names.index('Foot.' + n)] = 1 - t; W[k, names.index('LowerLeg.' + n)] = t
        bv = []
        # skinned whole to the foot, blending to the shin only up the collar (so the shoe bends as one piece)
        for q in SV:
            bv.append(out.verts.new(q)); t = shin_share(q[2] - ankle[2])
            shoe_w.append({'Foot.' + n: 1 - t, 'LowerLeg.' + n: t})
        top = max(h for _, h in place)
        def colour(i):
            a, h = place[i]
            if h < 0.005: return SHOE_TREAD
            if h < SOLE + 0.004: return SHOE_SOLE
            if h < SOLE + 0.02: return SHOE_ACCENT
            if a < 0.14 and h > top - 0.06: return SHOE_ACCENT                      # the heel tab
            return SHOE_UPPER
        for fc in faces:
            nf = out.faces.new([bv[i] for i in fc])
            for l, i in zip(nf.loops, fc): l[uvl].uv = uv; l[pl].uv = (0.0, 0.0); l[col] = rgba(colour(i))
    bmesh.ops.recalc_face_normals(out, faces=out.faces)
    mb.set_weights(o, W, names)
    out.to_mesh(sm); out.free()
    so = bpy.data.objects.new('Shoes', sm); C.scene.collection.objects.link(so)
    for g in o.vertex_groups: so.vertex_groups.new(name=g.name)
    for i, wd in enumerate(shoe_w):
        for nm, wv in wd.items():
            if wv > 1e-4: so.vertex_groups[nm].add([i], float(wv), 'REPLACE')
    # the body's colour layer is bytes at the corners: the shoes' match it
    ca = sm.color_attributes['Col']
    if ca.data_type != 'BYTE_COLOR':
        vals = np.empty(len(sm.loops) * 4); ca.data.foreach_get('color', vals); sm.color_attributes.remove(ca)
        nb = sm.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); nb.data.foreach_set('color', vals)
    for x in C.scene.objects: x.select_set(False)
    so.select_set(True); o.select_set(True); C.view_layer.objects.active = o
    bpy.ops.object.join()
    T = Matrix.Translation((0, 0, SOLE))
    o.data.transform(T); o.data.update(); rig.data.transform(T)
    log('shoes: %d vertices, %d faces; raised by the sole, %.3f' % (len(shoe_w), len(sm.polygons) if sm.polygons else 0, SOLE))


def finish(o, rig, img, px):
    png = os.path.join(OUT, NAME + 'Atlas.png')
    mb.face_parts = PROFILE['parts']                            # (meshy_boy.paint does the rest as for the boy)
    refs = mb.paint(o, img, px, png)
    if PROFILE['shoes']: shoes(o, rig, white_patch(o, png))
    o.data.materials.clear(); o.data.materials.append(atlas_material('Kid', png))
    o.name = 'Kid'; o.data.name = 'Kid'
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    export_fbx([o, rig], os.path.join(OUT, NAME + '.fbx'))
    cols = {'top': refs.get(1, (1, 1, 1)), 'legwear': refs.get(2, (1, 1, 1)), 'hair': refs.get(3, (1, 1, 1)), 'accent': mb.ACCENT}
    with open(os.path.join(OUT, NAME + '.json'), 'w') as f:
        json.dump(dict({k: [round(float(c), 4) for c in srgb(v)] for k, v in cols.items()}, tris=tris), f)
    neck = rig.data.bones['Head'].head_local.z; top = max(v.co.z for v in o.data.vertices)
    log('%s: %d tris; the Head joint at %.3f of %.3f (%.3f of his height): at %.2f m tall, a neck height of %.3f' % (
        NAME, tris, neck, top, neck / top, PROFILE['stands'], PROFILE['stands'] * neck / top))


# Each supplied model's rules: the backpack's colour (hue from, hue to, least saturation, value from, value to, and
# optionally the most saturation, for a grey pack; or
# 'shape': no colour of its own, found by its shape), its outfit parts, whether it needs shoes, how tall the kid stands
# in the game (metres: PlayerRoster); optionally how much
# of the game's swing the backpack takes ('bag'), the colours that are never an arm's ('not_arm', for arms_apart) and
# whether the pack's colour is judged per face ('face_colours': a texture cut into many small islands).
PROFILES = {
    'backpack_boy': {'pack': (15, 45, 0.35, 0.18, 0.75), 'parts': parts_backpack_boy, 'shoes': False, 'stands': 1.75},
    'first_day': {'pack': (245, 300, 0.25, 0.12, 0.9), 'parts': parts_first_day, 'shoes': True, 'stands': 1.32,
                  'bag': 0.5, 'not_arm': khaki},
    'plaid': {'pack': (0, 360, -1, 0.28, 0.72, 0.13), 'parts': parts_plaid, 'shoes': False, 'stands': 1.30, 'bag': 0.5,
              'not_arm': light_jeans, 'face_colours': True},
    'explorer': {'pack': 'shape', 'parts': parts_explorer, 'shoes': False, 'stands': 1.27, 'bag': 0.5, 'not_arm': red_shorts},
    'unicorn': {'pack': 'shape', 'parts': parts_unicorn, 'shoes': False, 'stands': 1.29, 'bag': 0.5, 'not_arm': terracotta},
}
PROFILE = PROFILES[PROFILE_NAME]


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
    arms_apart(obj, px, J, info)
    RIG = rig = make_rig(J)
    weigh_near(obj, rig, info)
    J = repose(obj, rig, J)
    backpack(obj, rig, px)
    nose(obj, rig)
    finish(obj, rig, img, px)
