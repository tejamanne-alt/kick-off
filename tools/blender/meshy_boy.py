# The playable teen boy from a textured, single-mesh model of a boy walking his bicycle (an AI-generated model the user
# supplied, exported as FBX: one fused mesh, one 2048 base-colour texture, no rig). Makes the game's Boy.fbx from it, in
# the same contract as teen.py (one skinned mesh 'Kid' under 'KidRig', one material: vertex colours times the atlas; UV2.x
# the outfit part; the bones the game poses; a Nose marker; Boy.json with the default outfit colours), and his bicycle as
# a prop of its own. tools/blender/README.md ("The boy") says more.
#
#   blenv/bin/python meshy_boy.py -- /abs/source.fbx /abs/outdir [--tris 30000]
#     -> outdir/Boy.fbx, Boy.blend, Boy.json, BoyAtlas.png, Bicycle.fbx, BicycleAtlas.png, debug_joints.png
#
# The steps:
#   split     every vertex is the boy's or the bike's, by its texture colour and where it is: the bike stands in its
#             own plane at his right (x < PLANE_X in the source), green and grey and black; the boy is skin, his cream
#             shirt and anything else off that plane; the handlebar's grips in his hands are dropped; then the boy is
#             the largest connected piece of his vertices, the bike everything else.
#   tidy      the boy scaled to the old boy's height, feet at z = 0, centred on his hips, facing -Y.
#   joints    the game's joints found on the mesh as it stands: the legs' cross-sections and the crotch, the heels,
#             each arm's skin and its centreline (the elbow is its corner), the shoulders, the neck.
#   separate  what touches in the scan but must move apart is cut (the thighs and shoes, a fist on the belt, the grips'
#             scraps) and each side's holes are closed on their own.
#   rig       the game's armature on those joints, bone-heat weights; then the re-pose (arms hanging, legs straight,
#             feet flat, head up: the game swings every bone from its rest pose) is baked in and made the rest pose,
#             and the weights are made again; Bag and Nose markers.
#   paint     outfit parts by texture colour, bones and height (shirt 1, trousers 2, hair 3, the rest 0); the atlas is
#             the source texture with the shirt's, trousers' and hair's texels divided by their colour, which goes into
#             the vertex colours instead, so the shop's outfits recolour them (ModelOutfit) and the default looks the same.
#   bicycle   decimated to a prop's budget, along x in the game's metres, its texture at half size.
import bpy, bmesh, sys, os, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
TRIS = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 30000
os.makedirs(OUT, exist_ok=True)

PLANE_X = -0.07          # the bike's plane: x below this in the source is the bike's (bar his skin and shirt)
HEIGHT = 2.14            # the old teen boy's standing height, hair included (the game scales by the neck anyway)
C = bpy.context


# ------------------------------------------------------------------------------------------------ helpers
def log(*a): print('[meshy_boy]', *a, flush=True)


def activate(o):
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True); C.view_layer.objects.active = o


def verts_np(o):
    me = o.data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    M = np.array(o.matrix_world); return V @ M[:3, :3].T + M[:3, 3]


def edges_np(o):
    me = o.data; E = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', E); return E.reshape(-1, 2)


def components(n, E):
    """Connected component label of each of n vertices over edges E (min-label propagation)."""
    lab = np.arange(n)
    for _ in range(5000):
        m = np.minimum(lab[E[:, 0]], lab[E[:, 1]])
        new = lab.copy(); np.minimum.at(new, E[:, 0], m); np.minimum.at(new, E[:, 1], m); new = new[new]
        if np.array_equal(new, lab): break
        lab = new
    return lab


def texture_pixels(img):
    W, H = img.size
    px = np.empty(W * H * 4, dtype=np.float32); img.pixels.foreach_get(px)
    return px.reshape(H, W, 4)


def loop_uvs(o):
    me = o.data; nl = len(me.loops)
    LV = np.empty(nl, dtype=np.int64); me.loops.foreach_get('vertex_index', LV)
    UV = np.empty(nl * 2); me.uv_layers[0].data.foreach_get('uv', UV)
    return LV, UV.reshape(-1, 2)


def sample(px, uv):
    H, W = px.shape[:2]
    xi = np.clip((uv[:, 0] % 1.0) * W, 0, W - 1).astype(int); yi = np.clip((uv[:, 1] % 1.0) * H, 0, H - 1).astype(int)
    return px[yi, xi, :3]


def vertex_colours(o, px):
    LV, UV = loop_uvs(o); n = len(o.data.vertices)
    acc = np.zeros((n, 3)); cnt = np.zeros(n)
    np.add.at(acc, LV, sample(px, UV)); np.add.at(cnt, LV, 1)
    return acc / np.maximum(cnt, 1)[:, None]


def hsv(Cc):
    r, g, b = Cc[:, 0], Cc[:, 1], Cc[:, 2]
    mx, mn = Cc.max(1), Cc.min(1); d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return h, s, mx


def delete_verts(o, keep):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(o.data); bm.free(); o.data.update()


# ------------------------------------------------------------------------------------------------ split
def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    activate(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    img = [n.image for n in o.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and
           any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links)][0]
    img.pack() if not img.packed_file else None
    return o, img


def split(o, px):
    V = verts_np(o); Cc = vertex_colours(o, px); h, s, v = hsv(Cc)
    skin = (h > 0) & (h < 40) & (s > 0.18) & (s < 0.7) & (v > 0.45)
    green = (h > 90) & (h < 190) & (s > 0.2) & (v > 0.33)   # (his black trousers have a dark teal tinge here and there)
    cream = (s < 0.3) & (v > 0.55) & (h < 60)
    plane = V[:, 0] < PLANE_X
    shirt = (h > 20) & (h < 60) & (s > 0.07) & (s < 0.35) & (v > 0.6)   # warm cream: his right sleeve crosses the plane
    boy = skin | shirt | (~plane & ~green)
    # the handlebar's grips and levers in his right hand: not skin, not his sleeve, in front of the body at hand height
    zr = V[:, 2]; ztop, zbot = zr.max(), zr.min(); H = ztop - zbot
    hand_band = (zr > zbot + 0.4 * H) & (zr < zbot + 0.62 * H) & (V[:, 1] < -0.12)
    neutral = s < 0.1                              # the bar is a neutral grey; his sleeves are a warm cream
    boy &= ~(hand_band & ~skin & (~cream | neutral))
    # a stray vertex amid his (a fleck of colour on the trousers) is his
    E = edges_np(o); deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(3):
        nb = np.zeros(len(V)); np.add.at(nb, E[:, 0], boy[E[:, 1]]); np.add.at(nb, E[:, 1], boy[E[:, 0]])
        boy |= (nb >= 0.75 * np.maximum(deg, 1)) & ~(plane & ~skin)
    # the boy is the largest connected piece of his vertices, with any smaller piece of his within his outline (a collar)
    Eb = E[boy[E[:, 0]] & boy[E[:, 1]]]
    lab = components(len(V), Eb)
    ids, cnt = np.unique(lab[boy], return_counts=True)
    main = ids[np.argmax(cnt)]
    keep_boy = boy & (lab == main)
    lo, hi = V[keep_boy].min(0), V[keep_boy].max(0)
    for i, n in zip(ids, cnt):
        if i == main or n < 12: continue
        P = V[lab == i]; c = P.mean(0)
        if np.all(c > lo) and np.all(c < hi) and c[0] > PLANE_X + 0.04 and ((skin | cream)[lab == i]).mean() > 0.6:
            keep_boy |= (lab == i)
    # the bike keeps no scrap of him: a piece of his collar left above the handlebar goes
    bk = ~keep_boy; Ek = E[bk[E[:, 0]] & bk[E[:, 1]]]; lk = components(len(V), Ek)
    drop = np.zeros(len(V), bool)
    for i in np.unique(lk[bk]):
        m = lk == i
        if V[m, 2].mean() > zbot + 0.68 * H: drop |= m
    log('split: boy %d verts (of %d), bike %d, %d dropped' % (keep_boy.sum(), len(V), (bk & ~drop).sum(), drop.sum()))
    bike = o.copy(); bike.data = o.data.copy(); bike.name = 'Bicycle'; C.scene.collection.objects.link(bike)
    delete_verts(o, keep_boy); o.name = 'Boy'
    delete_verts(bike, bk & ~drop)
    for x in (o, bike):
        bm = bmesh.new(); bm.from_mesh(x.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(x.data); bm.free()
    return o, bike


def decimate(o, tris):
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if n <= tris: return
    activate(o); m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = tris / n; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    log('decimated %s: %d -> %d tris' % (o.name, n, sum(len(p.vertices) - 2 for p in o.data.polygons)))


def tidy(boy, bike):
    """Scale and place the boy (and the bike with him) like the old boy: feet at z = 0, hips over the origin."""
    V = verts_np(boy); zmin, zmax = V[:, 2].min(), V[:, 2].max()
    k = HEIGHT / (zmax - zmin)
    hips = V[(V[:, 2] > zmin + 0.45 * (zmax - zmin)) & (V[:, 2] < zmin + 0.55 * (zmax - zmin))]
    cx, cy = np.median(hips[:, 0]), np.median(hips[:, 1])
    M = Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation((-cx, -cy, -zmin))
    for o in (boy, bike):
        o.data.transform(M); o.data.update()
    log('scaled by %.4f; hips centre was (%.3f, %.3f)' % (k, cx, cy))
    return k


# ------------------------------------------------------------------------------------------------ joints
HAND = 0.13              # wrist to fingertips along the surface (his hands are curled round the handlebar's grips)


def mesh_tris(o):
    me = o.data; me.calc_loop_triangles()
    T = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', T)
    return T.reshape(-1, 3)


def skin_of(Cc):
    h, s, v = hsv(Cc)
    return (h > 0) & (h < 40) & (s > 0.18) & (s < 0.7) & (v > 0.45)


def slice_loops(V, T, z0, minpts=12):
    """The mesh's cross-section at height z0: one point set per connected outline, the biggest first."""
    f = V[:, 2] - z0; ft = f[T]; Tc = T[(ft.min(1) < 0) & (ft.max(1) > 0)]
    if len(Tc) == 0: return []
    neg = f[Tc] < 0; N = len(V); cols = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = Tc[:, i], Tc[:, j]
        cols.append(np.where(neg[:, i] != neg[:, j], np.minimum(a, b) * N + np.maximum(a, b), -1))
    ks = np.sort(np.stack(cols, 1), 1)[:, 1:]                  # each crossing triangle crosses at two edges
    uk, inv = np.unique(ks.ravel(), return_inverse=True); inv = inv.reshape(-1, 2)
    a, b = uk // N, uk % N; u = f[a] / (f[a] - f[b]); P = V[a] + u[:, None] * (V[b] - V[a])
    lab = components(len(uk), inv); ids, cnt = np.unique(lab, return_counts=True)
    return [P[lab == i] for i, n in sorted(zip(ids, cnt), key=lambda t: -t[1]) if n >= minpts]


def geodesic(V, E, idx, seed):
    """Distance along the surface from the seed vertices (a mask over idx), over the vertices idx only."""
    loc = -np.ones(len(V), dtype=np.int64); loc[idx] = np.arange(len(idx))
    Ei = E[(loc[E[:, 0]] >= 0) & (loc[E[:, 1]] >= 0)]
    w = np.linalg.norm(V[Ei[:, 0]] - V[Ei[:, 1]], axis=1)
    adj = [[] for _ in idx]
    for i, j, ww in zip(loc[Ei[:, 0]].tolist(), loc[Ei[:, 1]].tolist(), w.tolist()):
        adj[i].append((j, ww)); adj[j].append((i, ww))
    dist = np.full(len(idx), np.inf); pq = [(0.0, k) for k in np.where(seed)[0].tolist()]
    for _, k in pq: dist[k] = 0.0
    heapq.heapify(pq)
    while pq:
        d, k = heapq.heappop(pq)
        if d > dist[k]: continue
        for j, ww in adj[k]:
            if d + ww < dist[j]: dist[j] = d + ww; heapq.heappush(pq, (d + ww, j))
    return dist


def line_at(P, z):
    """The point of a centreline (points with heights) at height z."""
    P = np.array(P); P = P[np.argsort(P[:, 2])]
    return np.array([np.interp(z, P[:, 2], P[:, 0]), np.interp(z, P[:, 2], P[:, 1]), z])


def ik_knee(hip, ankle, a, b):
    """Where a knee goes between hip and ankle for a thigh a and a shin b long: bent forward (-y) just enough."""
    hip, ankle = np.asarray(hip, float), np.asarray(ankle, float)
    d = np.linalg.norm(ankle - hip); down = (ankle - hip) / d
    fwd = np.array([0.0, -1.0, 0.0]); fwd -= down * (fwd @ down); fwd /= np.linalg.norm(fwd)
    ang = 0.0 if a + b <= d else math.acos(max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d))))
    return hip + (down * math.cos(ang) + fwd * math.sin(ang)) * a


def find_joints(o, px):
    """The joints of the body as it stands (arms bent, a stride), from its shape: the legs' cross-sections, the arms'
    skin, the shoulders' and the head's extent. Returns (J: name -> point, info: what separate() needs)."""
    V = verts_np(o); T = mesh_tris(o); E = edges_np(o)
    skin = skin_of(vertex_colours(o, px)); H = V[:, 2].max()
    J = {}

    # the legs: the crotch is the highest height at which the cross-section is two outlines of a size
    def two(z):
        L = slice_loops(V, T, z, 20); tot = sum(len(P) for P in L)
        return L[:2] if len(L) >= 2 and len(L[1]) > 0.3 * tot else None
    crotch = next(z for z in np.arange(0.53 * H, 0.35 * H, -0.005) if two(z))
    info = {'crotch': crotch}
    a, b = sorted(two(crotch - 0.01), key=lambda P: P[:, 0].mean())
    lines = {'R': [a.mean(0)], 'L': [b.mean(0)]}
    for z in np.arange(crotch - 0.03, 0.05 * H, -0.02):
        L = two(z)
        if not L: continue
        c0, c1 = L[0].mean(0), L[1].mean(0); r, l = lines['R'][-1][:2], lines['L'][-1][:2]
        if np.linalg.norm(c0[:2] - r) + np.linalg.norm(c1[:2] - l) > np.linalg.norm(c0[:2] - l) + np.linalg.norm(c1[:2] - r):
            c0, c1 = c1, c0
        if np.linalg.norm(c0[:2] - r) < 0.06 and np.linalg.norm(c1[:2] - l) < 0.06:
            lines['R'].append(c0); lines['L'].append(c1)
    info['lines'] = lines
    # the feet: their outlines just off the ground, the right one the one further to -x (the shoes touch lower down)
    soles = sorted(slice_loops(V, T, 0.03 * H, 20)[:2], key=lambda P: P[:, 0].mean())
    for n, sole in (('R', soles[0]), ('L', soles[1])):
        bot = line_at(lines[n], 0.0)
        foot = V[(V[:, 2] < 0.12 * H) & (np.hypot(V[:, 0] - bot[0], V[:, 1] - bot[1]) < 0.09)]
        heel = foot[foot[:, 1] > foot[:, 1].max() - 0.04][:, 2].min()        # lifted off the ground on the back foot
        hip = line_at(lines[n], crotch - 0.04); hip[2] = crotch + 0.06
        ankle = line_at(lines[n], heel + 0.06 * H)
        J['hip' + n], J['ankle' + n] = hip, ankle
        J['knee' + n] = line_at(lines[n], ankle[2] + 0.5 * (hip[2] - ankle[2]))
        J['toe' + n] = np.array([sole[:, 0].mean(), sole[:, 1].min() + 0.03, 0.03])
        info['heel' + n] = heel

    # the trunk, from the centres of its cross-sections
    def trunk(z):
        P = slice_loops(V, T, z, 30)[0]; return (P.min(0) + P.max(0)) / 2
    x0 = (J['hipL'][0] + J['hipR'][0]) / 2
    J['pelvis'] = np.array([x0, (J['hipL'][1] + J['hipR'][1]) / 2, crotch + 0.09])
    J['spine'] = trunk(0.61 * H); J['chest'] = trunk(0.70 * H)
    wide = slice_loops(V, T, 0.75 * H, 30)[0]                         # the chest with the sleeves on it

    # the arms: each one's skin below the sleeve, a piece of its own; its far end the fingertips
    band = skin & (V[:, 2] > 0.5 * H) & (V[:, 2] < 0.72 * H)
    Eb = E[band[E[:, 0]] & band[E[:, 1]]]; lab = components(len(V), Eb)
    ids, cnt = np.unique(lab[band], return_counts=True)
    for i in ids[np.argsort(-cnt)][:2]:
        A = np.where(lab == i)[0]; P = V[A]
        hem = P[:, 2].max(); upper = P[:, 2] > hem - 0.03
        n = 'L' if P[upper, 0].mean() > 0 else 'R'; sg = 1 if n == 'L' else -1
        d0 = geodesic(V, E, A, upper); tip = int(np.argmax(np.where(np.isfinite(d0), d0, -1)))
        dt = geodesic(V, E, A, np.arange(len(A)) == tip)
        wrist = P[np.abs(dt - HAND) < 0.012].mean(0)
        # the arm's centreline (the centres of rings of equal distance from the fingertips); the elbow is its corner,
        # the point furthest from the chord from the wrist to the skin just under the sleeve
        rings = [P[(dt >= d) & (dt < d + 0.02)] for d in np.arange(HAND, dt[np.isfinite(dt)].max(), 0.02)]
        cl = np.array([R.mean(0) for R in rings if len(R) > 3])
        U = P[upper].mean(0)
        elbow = cl[np.argmax(seg_dist(cl, wrist, U)[0])]
        side = V[(V[:, 0] * sg > 0.16) & (V[:, 2] < 0.85 * H)]
        S = np.array([sg * ((wide[:, 0] * sg).max() - 0.075), trunk(0.75 * H)[1], side[:, 2].max() - 0.07])
        J['shoulder' + n], J['elbow' + n], J['wrist' + n], J['tip' + n] = S, elbow, wrist, P[dt < 0.03].mean(0)
        info['hem' + n] = hem
    sz = (J['shoulderL'][2] + J['shoulderR'][2]) / 2
    head = V[V[:, 2] > 0.93 * H]; hc = (head.min(0) + head.max(0)) / 2
    J['neck0'] = np.array([x0, trunk(0.79 * H)[1], sz + 0.07])
    J['neck1'] = np.array([hc[0], J['neck0'][1] - 0.02, 0.85 * H])
    J['headtop'] = np.array([hc[0], hc[1], H])
    for k in sorted(J): log('joint %-10s %s' % (k, np.round(J[k], 3)))
    return J, info


def debug_points(o, px, J, path):
    """A quick look at the mesh's vertices (in their texture colours) with the joints marked: from the front, his left
    and his right."""
    from PIL import Image, ImageDraw
    V = verts_np(o); Cc = np.clip(vertex_colours(o, px), 0, 1); S, R = 600, 600 / 2.4
    ims = []
    # (axis across the picture, its sign, and the depth that is furthest from the camera first)
    for ax, sgn, depth in ((0, 1, -V[:, 1]), (1, 1, V[:, 0]), (1, -1, -V[:, 0])):
        im = Image.new('RGB', (S, S), (60, 60, 70)); dr = ImageDraw.Draw(im)
        for k in np.argsort(depth)[::2]:
            x = S / 2 + sgn * V[k, ax] * R; y = S - 20 - V[k, 2] * R
            dr.point((x, y), fill=tuple(int(255 * c) for c in Cc[k]))
        for jn, p in J.items():
            x = S / 2 + sgn * p[ax] * R; y = S - 20 - p[2] * R
            dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 40, 40)); dr.text((x + 4, y - 6), jn, fill=(255, 220, 0))
        ims.append(im)
    sheet = Image.new('RGB', (S * 3, S)); [sheet.paste(im, (i * S, 0)) for i, im in enumerate(ims)]; sheet.save(path)


# ------------------------------------------------------------------------------------------------ separate
def seg_dist(V, a, b):
    ab = b - a; t = np.clip(((V - a) @ ab) / max(ab @ ab, 1e-9), 0, 1); F = a + t[:, None] * ab
    return np.linalg.norm(V - F, axis=1), F


def separate(o, px, J, info):
    """Cut apart what touches in the scan but must move apart: the thighs (each vertex below the crotch goes with the
    nearer of the legs' bones) and a hand resting on the belt (the arm is the surface near its bones that is skin, or
    faces away from them; it is only cut free below the elbow, so the sleeve stays whole). The faces that join two sides
    go, and so do the black bits of the handlebar's grips left in his fists; each side's holes are closed on their own."""
    V = verts_np(o); me = o.data
    h, s, v = hsv(vertex_colours(o, px)); skinish = (h < 32) & (s > 0.08) & (v > 0.35)
    Nn = np.empty(len(V) * 3); me.vertex_normals.foreach_get('vector', Nn); Nn = Nn.reshape(-1, 3)
    E = edges_np(o)
    lab = np.zeros(len(V), dtype=np.int64)                  # 0 body, 1/2 the left/right leg, 3/4 the left/right arm
    below = V[:, 2] < info['crotch']
    dl = [np.min([seg_dist(V, J[a + n], J[b + n])[0] for a, b in (('hip', 'knee'), ('knee', 'ankle'), ('ankle', 'toe'))], 0)
          for n in 'LR']
    lab[below] = np.where(dl[0] < dl[1], 1, 2)[below]
    lower = np.zeros(len(V), bool)                          # nearest the forearm or the hand: where an arm may be cut free
    for n, k in (('L', 3), ('R', 4)):
        d = np.full(len(V), np.inf); F = np.zeros_like(V); seg = np.zeros(len(V), dtype=np.int64)
        for si, (a, b) in enumerate((('shoulder', 'elbow'), ('elbow', 'wrist'), ('wrist', 'tip'))):
            dd, FF = seg_dist(V, J[a + n], J[b + n]); m = dd < d; d[m] = dd[m]; F[m] = FF[m]; seg[m] = si
        out = np.einsum('ij,ij->i', Nn, V - F) > 0.3 * d
        arm = (d < 0.10) & (out | skinish) & (V[:, 2] < info['hem' + n] - 0.03)
        Ea = E[arm[E[:, 0]] & arm[E[:, 1]]]; cl = components(len(V), Ea)
        tipv = np.argmin(np.where(arm, np.linalg.norm(V - J['tip' + n], axis=1), np.inf))
        arm &= cl == cl[tipv]
        lab[arm] = k; lower |= arm & (seg > 0)
    grip = np.zeros(len(V), bool); fist = np.zeros(len(V), bool)
    for n in 'LR':
        dh = seg_dist(V, J['wrist' + n], J['tip' + n])[0]
        grip |= (dh < 0.07) & (v < 0.3) & ~skinish; fist |= dh < 0.10
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    cut, nleg = [], 0
    for f in bm.faces:
        ix = [x.index for x in f.verts]; ls = {int(lab[i]) for i in ix}
        if grip[ix].any(): cut.append(f)
        elif {1, 2} <= ls: cut.append(f); nleg += 1
        elif (3 in ls or 4 in ls) and len(ls) > 1 and any(lower[i] for i in ix if lab[i] >= 3): cut.append(f)
    rim = {x for f in cut for x in f.verts}
    log('separate: %d faces cut (legs %d, grips %d)' % (len(cut), nleg, sum(1 for f in cut if grip[[x.index for x in f.verts]].any())))
    bmesh.ops.delete(bm, geom=cut, context='FACES')                  # (their edges too: none may still join two sides)
    # each hole's rim, side by side (a rim on the legs is an open run: the other end of the hole was the other leg),
    # closed by a fan of triangles to its middle, in one colour: the texture at the rim's most typical corner
    def side(e):
        a, b = int(lab[e.verts[0].index]), int(lab[e.verts[1].index])
        return a if a == b else (max(a, b) if min(a, b) == 0 else -1)
    edges = [e for e in bm.edges if e.is_boundary and side(e) >= 0 and
             ((e.verts[0] in rim and e.verts[1] in rim) or (fist[e.verts[0].index] and fist[e.verts[1].index]))]
    up = list(range(len(edges))); at = {}
    def find(i):
        while up[i] != i: up[i] = up[up[i]]; i = up[i]
        return i
    for i, e in enumerate(edges):
        for x in e.verts:
            key = (x.index, side(e))
            if key in at: up[find(i)] = find(at[key])
            else: at[key] = i
    groups = {}
    for i in range(len(edges)): groups.setdefault(find(i), []).append(edges[i])
    uv = bm.loops.layers.uv.active; made = 0
    for g in groups.values():
        if len(g) < 3: continue
        ring = {x for e in g for x in e.verts}
        c = bm.verts.new(sum((x.co for x in ring), Vector()) / len(ring))
        cand = [l[uv].uv.copy() for x in ring for l in x.link_loops]
        cc = sample(px, np.array([tuple(u) for u in cand]))
        src = cand[int(np.argmin(np.abs(cc - np.median(cc, 0)).sum(1)))]
        for e in g:
            l = e.link_loops[0]; a, b = l.vert, l.link_loop_next.vert
            try: f = bm.faces.new((c, b, a))                 # (the winding the other way round from the face beside it)
            except ValueError: continue
            for fl in f.loops: fl[uv].uv = src
            made += 1
    bad = [x for x in bm.verts if not x.link_faces]
    bmesh.ops.delete(bm, geom=bad, context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
    log('separate: %d holes closed with %d faces' % (sum(1 for g in groups.values() if len(g) >= 3), made))
    # a scrap the cuts left between the legs (where the trousers' hems touched) would stay put when a leg lifts
    V = verts_np(o); lab = components(len(V), edges_np(o)); ids, cnt = np.unique(lab, return_counts=True)
    scrap = np.isin(lab, ids[cnt < 100]) & (V[:, 2] < info['crotch'])
    if scrap.any(): delete_verts(o, ~scrap); log('separate: %d scrap vertices between the legs gone' % scrap.sum())


# ------------------------------------------------------------------------------------------------ rig
def bone_list(J):
    """The game's bones (name, head, tail, parent), from joints."""
    b = [('Hips', J['pelvis'], J['spine'], None), ('Spine', J['spine'], J['chest'], 'Hips'),
         ('Chest', J['chest'], J['neck0'], 'Spine'), ('Neck', J['neck0'], J['neck1'], 'Chest'),
         ('Head', J['neck1'], J['headtop'], 'Neck')]
    for n in 'LR':
        b += [('UpperLeg.' + n, J['hip' + n], J['knee' + n], 'Hips'), ('LowerLeg.' + n, J['knee' + n], J['ankle' + n], 'UpperLeg.' + n),
              ('Foot.' + n, J['ankle' + n], J['toe' + n], 'LowerLeg.' + n),
              ('UpperArm.' + n, J['shoulder' + n], J['elbow' + n], 'Chest'), ('LowerArm.' + n, J['elbow' + n], J['wrist' + n], 'UpperArm.' + n),
              ('Hand.' + n, J['wrist' + n], J['wrist' + n] * 0.45 + J['tip' + n] * 0.55, 'LowerArm.' + n)]
    return b


def make_rig(J):
    arm = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('KidRig', arm); C.scene.collection.objects.link(rig)
    activate(rig); bpy.ops.object.mode_set(mode='EDIT')
    for n, h, t, par in bone_list(J):
        b = arm.edit_bones.new(n); b.head = Vector(h); b.tail = Vector(t); b.roll = 0
        if par: b.parent = arm.edit_bones[par]
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig


def rig_joints(rig):
    """The joints back from the rig's rest pose."""
    B = rig.data.bones; J = {}
    J['pelvis'], J['spine'] = np.array(B['Hips'].head_local), np.array(B['Hips'].tail_local)
    J['chest'], J['neck0'] = np.array(B['Chest'].head_local), np.array(B['Chest'].tail_local)
    J['neck1'], J['headtop'] = np.array(B['Head'].head_local), np.array(B['Head'].tail_local)
    for n in 'LR':
        J['hip' + n], J['knee' + n] = np.array(B['UpperLeg.' + n].head_local), np.array(B['LowerLeg.' + n].head_local)
        J['ankle' + n], J['toe' + n] = np.array(B['Foot.' + n].head_local), np.array(B['Foot.' + n].tail_local)
        J['shoulder' + n], J['elbow' + n] = np.array(B['UpperArm.' + n].head_local), np.array(B['LowerArm.' + n].head_local)
        J['wrist' + n], J['hand' + n] = np.array(B['Hand.' + n].head_local), np.array(B['Hand.' + n].tail_local)
    return J


def weights(o):
    """Vertex weights as a (vertices x groups) array, and the group names."""
    names = [g.name for g in o.vertex_groups]; W = np.zeros((len(o.data.vertices), len(names)))
    for v in o.data.vertices:
        for g in v.groups: W[v.index, g.group] = g.weight
    return W, names


def set_weights(o, W, names):
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    for j, n in enumerate(names):
        vg = o.vertex_groups.new(name=n); idx = np.where(W[:, j] > 1e-4)[0]
        for i in idx: vg.add([int(i)], float(W[i, j]), 'REPLACE')


def weigh(o, rig, smooth=2):
    """Bone-heat weights; a vertex the heat missed goes with its nearest bone; then smoothed over the surface a little,
    at most four bones a vertex (Unity skins with four), normalised."""
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    for m in list(o.modifiers): o.modifiers.remove(m)
    o.parent = None
    # (bone heat finds no solution at all with a sliver of a face in the mesh: re-posing makes some)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True); rig.select_set(True); C.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    names = [b.name for b in rig.data.bones if b.use_deform]
    W0, n0 = weights(o); W = np.zeros((len(W0), len(names)))
    for j, n in enumerate(n0):
        if n in names: W[:, names.index(n)] = W0[:, j]
    V = verts_np(o); E = edges_np(o)
    miss = W.sum(1) < 1e-3
    if miss.any():
        D = np.stack([seg_dist(V[miss], np.array(rig.data.bones[n].head_local), np.array(rig.data.bones[n].tail_local))[0] for n in names], 1)
        W[np.where(miss)[0], np.argmin(D, 1)] = 1.0
    log('weights: %d of %d vertices had no bone-heat weight' % (miss.sum(), len(V)))
    # below the crotch the legs are pieces apart: each takes nothing from the other leg's bones (bone heat goes by
    # nearness, and his toes stood close)
    zc = (rig.data.bones['UpperLeg.L'].head_local.z + rig.data.bones['UpperLeg.R'].head_local.z) / 2 - 0.08
    low = V[:, 2] < zc; El = E[low[E[:, 0]] & low[E[:, 1]]]; lab = components(len(V), El)
    for i in np.unique(lab[low]):
        m = lab == i; n = 'R' if V[m, 0].mean() > 0 else 'L'                 # the other leg
        for b in ('UpperLeg.', 'LowerLeg.', 'Foot.'): W[m, names.index(b + n)] = 0
    W[low & (W.sum(1) < 1e-6), names.index('Hips')] = 1
    deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(smooth):
        acc = np.zeros_like(W); np.add.at(acc, E[:, 0], W[E[:, 1]]); np.add.at(acc, E[:, 1], W[E[:, 0]])
        W = 0.5 * W + 0.5 * acc / np.maximum(deg, 1)[:, None]
    W[W < np.sort(W, 1)[:, -4][:, None]] = 0
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    set_weights(o, W, names)


def pose_bone(rig, name, direction=None, rot=None):
    """Turn a pose bone about its head, to point along `direction` (armature space) or by the rotation matrix `rot`."""
    C.view_layer.update(); pb = rig.pose.bones[name]
    h, t = pb.head.copy(), pb.tail.copy()
    R = rot if rot is not None else (t - h).rotation_difference(Vector(direction)).to_matrix().to_4x4()
    pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ pb.matrix
    C.view_layer.update()


ARM_DOWN = (0.17, 0.03, -1.0)        # the upper arm hanging, a little away from the side (x for the left arm)
FOREARM_DOWN = (0.06, -0.12, -1.0)   # the forearm, a touch forward of straight
FOOT = (0.0, -0.161, -0.102)         # ankle to toe of the flat (left) foot, pointed straight ahead
HEAD_UP = -8.0                       # degrees about x, at the neck and again at the head: he looks up from the ground


def repose(o, rig, J):
    """Arms hanging, legs straight under the hips (the knee bends forward just enough to put both ankles at the flat foot's
    height), both feet flat and ahead, the head up a little; baked into the mesh and made the rig's rest pose."""
    def pose(lift):
        for pb in rig.pose.bones: pb.matrix_basis = Matrix()
        for n, sg in (('L', 1), ('R', -1)):
            pose_bone(rig, 'UpperArm.' + n, (sg * ARM_DOWN[0], ARM_DOWN[1], ARM_DOWN[2]))
            pose_bone(rig, 'LowerArm.' + n, (sg * FOREARM_DOWN[0], FOREARM_DOWN[1], FOREARM_DOWN[2]))
            pose_bone(rig, 'Hand.' + n, (sg * FOREARM_DOWN[0], FOREARM_DOWN[1], FOREARM_DOWN[2]))
            hip = J['hip' + n]; a = np.linalg.norm(J['knee' + n] - hip); b = np.linalg.norm(J['ankle' + n] - J['knee' + n])
            A2 = np.array([hip[0] * 0.85, hip[1] + 0.01, min(J['ankleL'][2], J['ankleR'][2]) + lift[n]])
            k = max(1.0, np.linalg.norm(A2 - hip) / (a + b))      # (the back leg, bent, measures short: it stretches a little)
            for bn in ('UpperLeg.', 'LowerLeg.'): rig.pose.bones[bn + n].scale = (1, k, 1)
            pose_bone(rig, 'UpperLeg.' + n, Vector(ik_knee(hip, A2, a * k, b * k) - hip))
            pose_bone(rig, 'LowerLeg.' + n, Vector(A2) - rig.pose.bones['LowerLeg.' + n].head)
            pose_bone(rig, 'Foot.' + n, FOOT)
        pose_bone(rig, 'Neck', rot=Matrix.Rotation(math.radians(HEAD_UP), 4, 'X'))
        pose_bone(rig, 'Head', rot=Matrix.Rotation(math.radians(HEAD_UP), 4, 'X'))
    for n in 'LR':                                         # (a stretched leg leaves the shin's and the foot's size be)
        for bn in ('LowerLeg.', 'Foot.'): rig.data.bones[bn + n].inherit_scale = 'NONE'
    W, names = weights(o)
    def foot_low(n):
        dg = C.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh()
        P = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', P); ev.to_mesh_clear(); P = P.reshape(-1, 3)
        return P[W[:, names.index('Foot.' + n)] > 0.5][:, 2].min()
    lift = {'L': 0.0, 'R': 0.0}
    pose(lift)
    lift['R'] = foot_low('L') - foot_low('R'); pose(lift)          # both soles on the same ground
    log('repose: right ankle raised %.3f so both feet stand level; legs stretched %s' % (lift['R'],
        ', '.join('%s %.3f' % (n, rig.pose.bones['UpperLeg.' + n].scale[1]) for n in 'LR')))
    for n in 'LR':
        k = rig.pose.bones['UpperLeg.' + n]
        log('  knee gap %s: %.4f' % (n, (k.tail - rig.pose.bones['LowerLeg.' + n].head).length))
    activate(o); bpy.ops.object.modifier_apply(modifier=[m.name for m in o.modifiers if m.type == 'ARMATURE'][0])
    activate(rig); bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
    for b in rig.data.bones: b.inherit_scale = 'FULL'
    # stand on z = 0 again
    dz = -verts_np(o)[:, 2].min(); T = Matrix.Translation((0, 0, dz))
    o.data.transform(T); o.data.update(); rig.data.transform(T)
    log('repose: feet down %.3f' % dz)
    return rig_joints(rig)


# ------------------------------------------------------------------------------------------------ markers
def markers(o, rig):
    """Bones the game reads but that move nothing: Nose (in front of the face: which way he faces) and Bag (behind the
    hips, where a bag would hang; the pennant pole rides on Chest for the boy)."""
    V = verts_np(o); B = rig.data.bones; neck1 = np.array(B['Head'].head_local); hips = np.array(B['Hips'].head_local)
    face = V[(V[:, 2] > neck1[2] + 0.06) & (V[:, 2] < neck1[2] + 0.16)]
    ny, nz = face[:, 1].min(), neck1[2] + 0.11
    back = V[np.abs(V[:, 2] - hips[2] - 0.08) < 0.03][:, 1].max()
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    for n, h, t, par in (('Nose', (neck1[0], ny + 0.03, nz), (neck1[0], ny - 0.03, nz), 'Head'),
                         ('Bag', (-0.04, back + 0.02, hips[2] + 0.07), (-0.04, back + 0.02, hips[2] - 0.13), 'Hips')):
        b = eb.new(n); b.head = Vector(h); b.tail = Vector(t); b.roll = 0; b.parent = eb[par]; b.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')


# ------------------------------------------------------------------------------------------------ paint
def lin(c): c = np.asarray(c, dtype=np.float64); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): c = np.clip(np.asarray(c, dtype=np.float64), 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def face_parts(o, px):
    """The outfit part of each face (0 fixed: skin, face, shoes, belt; 1 shirt; 2 trousers; 3 hair), from its texture
    colour, the bones that carry it and its height (he stands as he will in the game: arms down)."""
    me = o.data; V = verts_np(o); E = edges_np(o); W, names = weights(o)
    bw = lambda *ns: sum(W[:, names.index(n)] for n in ns if n in names)
    arm = bw('LowerArm.L', 'LowerArm.R', 'Hand.L', 'Hand.R'); head = bw('Head'); foot = bw('Foot.L', 'Foot.R')
    torso = bw('Hips', 'Spine')
    Cv = vertex_colours(o, px); h, s, v = hsv(Cv)
    skin = skin_of(Cv); dark = v < 0.32; cream = (s < 0.3) & (v > 0.5)
    # the hair: the biggest dark piece of the head (the brows and the eyes' lines are pieces of their own)
    hd = dark & (head > 0.5); Eh = E[hd[E[:, 0]] & hd[E[:, 1]]]; lab = components(len(V), Eh)
    ids, cnt = np.unique(lab[hd], return_counts=True); hair = hd & (lab == ids[np.argmax(cnt)])
    # the belt: the dark band from where the shirt ends, down about its width (the front of the waist decides)
    front = (torso > 0.5) & (np.abs(V[:, 0]) < 0.15) & (V[:, 1] < np.median(V[torso > 0.5][:, 1]))
    zs = np.arange(1.15, 1.5, 0.005)
    frac = np.array([cream[front & (np.abs(V[:, 2] - z) < 0.004)].mean() if (front & (np.abs(V[:, 2] - z) < 0.004)).sum() > 3 else 0 for z in zs])
    belt_hi = zs[np.argmax(frac > 0.5)]; belt_lo = belt_hi - 0.04
    log('paint: the shirt ends at %.3f, the belt from %.3f' % (belt_hi, belt_lo))
    P = np.zeros(len(V), dtype=np.int64)
    P[(V[:, 2] >= belt_hi) & ~skin] = 1                                  # the shirt, sleeves and collar
    P[(V[:, 2] < belt_lo)] = 2                                           # the trousers
    P[(V[:, 2] >= belt_lo) & (V[:, 2] < belt_hi) & ~dark] = 1            # (the shirt's hem tucked in)
    P[(head > 0.5)] = 0; P[hair] = 3
    P[(arm > 0.5) | (foot > 0.6)] = 0                                    # forearms and hands, shoes
    P[skin & (P != 3)] = 0
    # a face takes the part most of its corners have
    nf = len(me.polygons); FV = np.empty(len(me.loops), dtype=np.int64); me.loops.foreach_get('vertex_index', FV)
    ls = np.empty(nf, dtype=np.int64); me.polygons.foreach_get('loop_start', ls)
    tri = FV.reshape(-1, 3) if len(FV) == 3 * nf else None
    assert tri is not None, 'expected triangles'
    votes = np.stack([(P[tri] == p).sum(1) for p in range(4)], 1)
    return np.argmax(votes, 1), tri


BAND = {1: (80, 92), 2: (55, 75), 3: (80, 92)}   # (the trousers' white flecks are the scan's, not the cloth's)


def paint(o, img, px, out_png):
    """Outfit parts, vertex colours and the atlas: the shirt's, the trousers' and the hair's texels are divided by their
    colour, which their vertices carry instead (the game recolours vertex colours: ModelOutfit), so the default looks
    as the scan did. Returns the default colours (linear)."""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()
    FP, tri = face_parts(o, px)
    nl = len(me.loops); UV = np.empty(nl * 2); me.uv_layers[0].data.foreach_get('uv', UV); UV = UV.reshape(-1, 3, 2)
    Hh, Ww = px.shape[:2]
    from PIL import Image, ImageDraw
    mask = Image.new('L', (Ww, Hh), 255); dr = ImageDraw.Draw(mask)
    for f in range(len(FP)):
        dr.polygon([(u * Ww, (1 - v) * Hh) for u, v in UV[f]], fill=int(FP[f]))
    M = np.array(mask)[::-1].astype(np.int64)                     # (image rows from the bottom, as Blender's pixels)
    M0 = M.copy()                                                 # (the colours come from his own texels only)
    for _ in range(6):                                            # grow each part a few texels into the unused margin
        free = M == 255
        for sh in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = np.roll(M, sh, axis=(0, 1)); take = free & (nb != 255); M[take] = nb[take]; free = M == 255
    T = lin(px[:, :, :3]); A = T.copy(); refs = {}
    for p in (1, 2, 3):
        sel = M == p
        if not (M0 == p).any(): continue
        # the part's colour: its texels a little brighter than most (the band BAND[p] of their brightness), so the
        # atlas there is about white with the shading below it; flecks brighter than that are clamped away
        X = T[M0 == p]; lum = X.mean(1); lo, hi = np.percentile(lum, BAND[p])
        refs[p] = np.clip(X[(lum >= lo) & (lum <= hi)].mean(0), 1e-3, 1); A[sel] = np.clip(T[sel] / refs[p], 0, 1)
        log('paint: part %d, %d texels, colour %s (sRGB %s)' % (p, sel.sum(), np.round(refs[p], 4), np.round(srgb(refs[p]), 3)))
    out = np.concatenate([srgb(A), np.ones(A.shape[:2] + (1,))], 2)[::-1]
    Image.fromarray((out[:, :, :3] * 255 + 0.5).astype(np.uint8)).save(out_png)
    # vertex colours (linear here; stored sRGB in the bytes) and the part ids in the second UV map
    Cl = np.ones((len(FP), 3, 4))
    for p, ref in refs.items(): Cl[FP == p, :, :3] = ref
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); col.data.foreach_set('color', Cl.ravel())
    while len(me.uv_layers) < 2: me.uv_layers.new(name='Parts')
    U2 = np.zeros((len(FP), 3, 2)); U2[:, :, 0] = FP[:, None]; me.uv_layers[1].data.foreach_set('uv', U2.ravel())
    me.uv_layers.active_index = 0
    for i, uvl in enumerate(me.uv_layers): uvl.active_render = i == 0
    log('paint: faces by part %s' % np.bincount(FP, minlength=4))
    return refs


def atlas_material(name, png):
    """One material: the atlas times the vertex colours (as teen_build makes it)."""
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']; tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(png)
    vc = nt.nodes.new('ShaderNodeVertexColor'); mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1
    nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B']); nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
    return mat


def export_fbx(objs, path):
    for x in C.scene.objects: x.select_set(False)
    for x in objs: x.select_set(True)
    C.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options='FBX_SCALE_ALL', add_leaf_bones=False,
        bake_anim=False, mesh_smooth_type='FACE', use_mesh_modifiers=True, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y',
        secondary_bone_axis='X', path_mode='STRIP')


def finish_boy(boy, rig, img, px):
    png = os.path.join(OUT, 'BoyAtlas.png')
    refs = paint(boy, img, px, png)
    boy.data.materials.clear(); boy.data.materials.append(atlas_material('Kid', png))
    boy.name = 'Kid'; boy.data.name = 'Kid'
    tris = sum(len(p.vertices) - 2 for p in boy.data.polygons)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Boy.blend'))
    export_fbx([boy, rig], os.path.join(OUT, 'Boy.fbx'))
    # (the colours are sRGB-encoded, as the byte vertex colours that the game compares them with)
    cols = {'top': refs.get(1, (1, 1, 1)), 'legwear': refs.get(2, (1, 1, 1)), 'hair': refs.get(3, (1, 1, 1)), 'accent': ACCENT}
    with open(os.path.join(OUT, 'Boy.json'), 'w') as f:
        json.dump(dict({k: [round(float(c), 4) for c in srgb(v)] for k, v in cols.items()}, tris=tris), f)
    B = rig.data.bones; neck = B['Head'].head_local.z; top = max(v.co.z for v in boy.data.vertices)
    log('boy: %d tris; the Head joint at %.3f of %.3f (%.3f of his height)' % (tris, neck, top, neck / top))


ACCENT = (0.578, 0.033, 0.047)        # no tie on him: the shop's accent colour stays the old boy's (linear)


NECK = 1.5                  # the game puts his Head joint 1.5 m up (PlayerRoster): the bicycle is made to that scale
BIKE_TRIS = 20000           # (the frame and spokes are thin shells: fewer and they fall apart)
BIKE_LEAN = 4.0             # degrees, away from the camera, as if on its kickstand


def finish_bike(bike, rig, img):
    """The bicycle as a prop of its own, in the game's metres: along x (front wheel to +x), leaning a little away from
    the camera (-y) as if on its stand, its wheels on z = 0 at the origin; white vertex colours (the shader multiplies
    by them); the source texture at half size."""
    decimate(bike, BIKE_TRIS)
    k = NECK / rig.data.bones['Head'].head_local.z
    M = Matrix.Rotation(math.radians(-BIKE_LEAN), 4, 'X') @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Diagonal((k, k, k, 1.0))
    bike.data.transform(M)
    V = verts_np(bike); c = (V.min(0) + V.max(0)) / 2
    bike.data.transform(Matrix.Translation((-c[0], -c[1], -V[:, 2].min()))); bike.data.update()
    me = bike.data
    for a in list(me.color_attributes): me.color_attributes.remove(a)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); col.data.foreach_set('color', np.ones(len(me.loops) * 4))
    from PIL import Image
    png = os.path.join(OUT, 'BicycleAtlas.png')
    Image.fromarray((np.clip(texture_pixels(img)[::-1, :, :3], 0, 1) * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(png)
    mat = atlas_material('Bicycle', png)
    me.materials.clear(); me.materials.append(mat)
    for i, uvl in enumerate(me.uv_layers): uvl.active_render = i == 0
    export_fbx([bike], os.path.join(OUT, 'Bicycle.fbx'))
    V = verts_np(bike); log('bicycle: %d tris, %.2f m long, %.2f m tall (x%.3f)' % (sum(len(p.vertices) - 2 for p in me.polygons),
                                                                                np.ptp(V[:, 0]), V[:, 2].max(), k))


if __name__ == '__main__':
    obj, img = load()
    px = texture_pixels(img)
    boy, bike = split(obj, px)
    tidy(boy, bike)
    J, info = find_joints(boy, px)
    debug_points(boy, px, J, os.path.join(OUT, 'debug_joints.png'))
    separate(boy, px, J, info)
    decimate(boy, TRIS)
    rig = make_rig(J)
    weigh(boy, rig)
    repose(boy, rig, J)
    weigh(boy, rig)
    markers(boy, rig)
    finish_bike(bike, rig, img)
    bpy.data.objects.remove(bike)
    finish_boy(boy, rig, img, px)
