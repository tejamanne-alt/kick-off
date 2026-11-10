# The steps of polish_character.py (see its header for why each one is needed), and the UV rasteriser and atlas fill
# that face_paint.py shares.
import bpy, bmesh
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image

# Normal-smoothing radius by outfit part (UV2.x): 0 skin and fixed parts, 1 top, 2 legwear, 3 hair, 4 accent.
RADIUS = {0: 0.012, 1: 0.02, 2: 0.02, 3: 0.035, 4: 0.02}
DEFAULT_RADIUS = 0.016
HAIR_VOLUME = 0.07        # m: the neighbourhood whose centroid a hair vertex's normal points away from
HAIR_VOLUME_MIX = 0.75    # how much of a hair vertex's normal is that direction (the rest its smoothed surface normal)


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def open_edges(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    n = sum(1 for e in bm.edges if e.is_boundary)
    bm.free()
    return n


def clean(o, merge):
    """Drops loose vertices and degenerate faces, and welds open-edge vertices within `merge` of each other (the torn
    texture islands' borders). Returns how many vertices were merged."""
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    n0 = len(bm.verts)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
    n1 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.is_boundary], dist=merge)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-12], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    n2 = len(bm.verts)
    bm.to_mesh(me); bm.free(); me.update()
    return int(n1 - n2)


def seam_vertices(me):
    """Vertices on a texture island's border (their corners carry more than one UV): moving one drags the painted
    detail of every island it borders (a printed number, a plaid, a logo stretched into blocks)."""
    lv = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', lv)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    key = np.round(uv * 8192).astype(np.int64); key = key[:, 0] * 16384 + key[:, 1]
    order = np.lexsort((key, lv))
    lv_s, key_s = lv[order], key[order]
    new = np.ones(len(lv_s), bool); new[1:] = (lv_s[1:] != lv_s[:-1]) | (key_s[1:] != key_s[:-1])
    distinct = np.bincount(lv_s[new], minlength=len(me.vertices))
    return distinct > 1


def protect_group(o, bones, keep=0.3, seam_keep=0.15):
    """The vertex group the decimator cuts: 1 everywhere, down to `keep` on vertices weighted to the named bones and to
    `seam_keep` on the texture islands' borders."""
    g = o.vertex_groups.new(name='_Cut')
    names = {vg.index: vg.name for vg in o.vertex_groups}
    seam = seam_vertices(o.data)
    for v in o.data.vertices:
        w = sum(x.weight for x in v.groups if names.get(x.group) in bones)
        cut = 1.0 - (1.0 - keep) * min(1.0, w * 1.5)
        if seam[v.index]: cut = min(cut, seam_keep)
        g.add([v.index], cut, 'REPLACE')
    return g.name


def decimate(o, target, group=None, factor=3.0):
    n = tris(o)
    if n <= target: return
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = target / n; m.use_collapse_triangulate = True
    if group: m.vertex_group = group; m.vertex_group_factor = factor
    bpy.ops.object.modifier_apply(modifier=m.name)
    if group and o.vertex_groups.get(group): o.vertex_groups.remove(o.vertex_groups.get(group))


def _polys(me):
    P = len(me.polygons)
    fn = np.zeros(P * 3); me.polygons.foreach_get('normal', fn)
    ar = np.zeros(P); me.polygons.foreach_get('area', ar)
    cen = np.zeros(P * 3); me.polygons.foreach_get('center', cen)
    return fn.reshape(-1, 3), ar, cen.reshape(-1, 3)


def unflip(o, radius=0.012):
    """Turns round the triangles whose winding points into the body: those whose surroundings (the area within `radius`)
    clearly face the other way. Thin parts (an ear, a collar), whose near and far sides are both within reach, are left
    alone: there the vote is split."""
    me = o.data
    fn, ar, cen = _polys(me)
    tree = cKDTree(cen)
    flip = []
    for i, ids in enumerate(tree.query_ball_point(cen, radius)):
        if len(ids) < 4: continue
        ids = np.asarray(ids)
        d = fn[ids] @ fn[i]
        s = (d * ar[ids]).sum(); tot = (np.abs(d) * ar[ids]).sum()
        if tot > 0 and s < -0.5 * tot: flip.append(i)
    if flip:
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flip], flip_multires=False)
        bm.to_mesh(me); bm.free(); me.update()
    return len(flip)


def vertex_parts(me):
    """Each vertex's outfit part: the largest UV2.x among its corners (so a vertex on a garment's edge counts as the
    garment, never as skin)."""
    part = np.full(len(me.vertices), -1)
    if len(me.uv_layers) < 2: return np.zeros(len(me.vertices), int)
    lv = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', lv)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[1].data.foreach_get('uv', uv)
    np.maximum.at(part, lv, np.round(uv.reshape(-1, 2)[:, 0]).astype(int))
    return np.maximum(part, 0)


def fix_parts(o):
    """Every face's corners carry one outfit part (the game recolours by vertex; a face across two parts would smear)."""
    me = o.data
    if len(me.uv_layers) < 2: return 0
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[1].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    ls = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_start', ls)
    lt = np.zeros(len(me.polygons), int); me.polygons.foreach_get('loop_total', lt)
    fixed = 0
    for s, t in zip(ls, lt):
        v = np.round(uv[s:s + t, 0])
        if v.min() != v.max():
            vals, c = np.unique(v, return_counts=True); v[:] = vals[np.argmax(c)]; fixed += 1
        uv[s:s + t, 0] = v
    me.uv_layers[1].data.foreach_set('uv', uv.ravel())
    return fixed


def fix_weights(o):
    """At most four bones a vertex (Unity skins with four), normalised."""
    for v in o.data.vertices:
        gs = sorted([(g.weight, g.group) for g in v.groups], reverse=True)
        keep = gs[:4]; s = sum(w for w, _ in keep)
        for _, gi in gs[4:]: o.vertex_groups[gi].remove([v.index])
        if s > 0:
            for w, gi in keep: o.vertex_groups[gi].add([v.index], w / s, 'REPLACE')


def _vertex_weights(o, names):
    """The weights of the named bones per vertex (columns in the order given), and every group's index by name."""
    me = o.data; nv = len(me.vertices)
    gi = {g.name: g.index for g in o.vertex_groups}
    W = np.zeros((nv, len(names)))
    col = {gi[n]: k for k, n in enumerate(names) if n in gi}
    for v in me.vertices:
        for g in v.groups:
            k = col.get(g.group)
            if k is not None: W[v.index, k] = g.weight
    return W, gi


FACE_ROUND = 1.6         # the face's sphere: its centre this many face half-widths behind the face
HEAD_CUT_SLOPE = 0.9      # the cut under which the head blends into the neck dips this much per unit forward (under the chin)
HEAD_BLEND = 0.12         # the blend below the cut, as a share of the head's height above the Head joint


def rigid_head(o, rig):
    """The whole head moves with the Head bone. The scans' automatic rigs gave the face part Head, part Neck: 38% of
    Hana's face and three quarters of her jaw were mostly on the Neck, so as the head turned the face creased and folded
    (docs/LEARNINGS.md C6, C15). Every vertex of the head and neck (Head + Neck at least half its weight) above a cut
    through the Head joint, dipping forward under the chin, follows the Head alone; below the cut it blends back to its own
    weights over HEAD_BLEND of the head's height (the throat and the nape bend with the neck). Returns the vertices made
    rigid."""
    if 'Head' not in o.vertex_groups or 'Head' not in rig.data.bones or 'Nose' not in rig.data.bones: return 0
    me = o.data; nv = len(me.vertices)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    B = rig.data.bones
    J = np.array(B['Head'].head_local); nose = np.array(B['Nose'].head_local)
    fwd = nose - J; fwd[2] = 0; fwd /= np.linalg.norm(fwd)
    hh = co[:, 2].max() - J[2]
    W, gi = _vertex_weights(o, ['Head', 'Neck'])
    rel = co - J
    cut = rel[:, 2] + np.maximum(rel @ fwd, 0) * HEAD_CUT_SLOPE
    t = np.clip((cut + HEAD_BLEND * hh) / (HEAD_BLEND * hh), 0, 1)
    sel = np.flatnonzero((W.sum(1) > 0.5) & (t > 0) & (W[:, 0] < 0.999))
    head = o.vertex_groups['Head']
    for i in sel:
        v = me.vertices[int(i)]
        h0 = W[i, 0]; h1 = h0 + (1 - h0) * t[i]
        rest = 1 - h0
        pairs = [(g.group, g.weight) for g in v.groups]          # (read first: removing invalidates the elements)
        for gidx, w in pairs:
            if gidx == head.index: continue
            nw = w * (1 - h1) / rest if rest > 1e-9 else 0.0
            if nw < 1e-4: o.vertex_groups[gidx].remove([int(i)])
            else: o.vertex_groups[gidx].add([int(i)], float(nw), 'REPLACE')
        head.add([int(i)], float(h1), 'REPLACE')
    return int((t[sel] >= 1).sum())


TEAR_RADIUS = 0.012       # the neighbourhood that decides a face's garment, as a share of the figure's height (2 cm at 1.65 m)
TEAR_SHARE = 0.65         # a garment must cover this much of it (the face itself not counted)
TEAR_SATURATION = 0.3     # and the face's own texel must be greyish (a light streak or a dark crease, never skin)


def absorb_tears(o, atlas):
    """White tears: specks and streaks of no outfit part (UV2.x 0) inside a garment. The scans painted their clothes and
    hair with light streaks (folds, highlights, unpainted seams, thin stripes cut into jagged triangles by decimation);
    paint() made each dark garment a vertex colour times a near-white atlas and left the light streaks out of it (part 0:
    a white vertex colour times the texel's own light colour), so they drew as white tears in the dark jackets, trousers
    and hair, and stayed white when the shop recoloured the garment (docs/LEARNINGS.md C16). Most of them do not even share
    an edge with their garment (the scans are cut along every colour line), so the test is by surface, not by topology: a
    part-0 face joins garment p when p covers TEAR_SHARE of the surface within TEAR_RADIUS of it (the face itself not
    counted: at 32k triangles a face is about that size; on the same side: faces turned the same way) and its own texel is
    greyish (under TEAR_SATURATION, or dark), never skin. Wide features (a printed letter, the hoodie under a jacket, the
    face, the hands) keep their middles. Three rounds, so a streak a few faces wide goes too. The face's part and its corners' colour become the garment's; its light texel then shades the garment's
    colour a little. Returns the faces moved."""
    me = o.data
    if len(me.uv_layers) < 2 or 'Col' not in me.color_attributes: return 0
    col = me.color_attributes['Col']
    if col.domain != 'CORNER': return 0
    me.calc_loop_triangles()
    nv = len(me.vertices); P = len(me.polygons)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    ls = np.zeros(P, int); me.polygons.foreach_get('loop_start', ls)
    lt = np.zeros(P, int); me.polygons.foreach_get('loop_total', lt)
    lv = np.zeros(len(me.loops), int); me.loops.foreach_get('vertex_index', lv)
    u0 = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', u0); u0 = u0.reshape(-1, 2)
    u1 = np.zeros(len(me.loops) * 2); me.uv_layers[1].data.foreach_get('uv', u1); u1 = u1.reshape(-1, 2)
    cd = np.zeros(len(me.loops) * 4); col.data.foreach_get('color', cd); cd = cd.reshape(-1, 4)
    part = np.round(u1[ls, 0]).astype(int)
    # each face's centre, normal and area (polygon normals and areas from Blender)
    cen = np.zeros(P * 3); me.polygons.foreach_get('center', cen); cen = cen.reshape(-1, 3)
    nrm = np.zeros(P * 3); me.polygons.foreach_get('normal', nrm); nrm = nrm.reshape(-1, 3)
    area = np.zeros(P); me.polygons.foreach_get('area', area)
    H = co[:, 2].max() - co[:, 2].min()
    # each face's own texel colour: the mean of its corners' and its centre's texels
    Hh, Ww = atlas.shape[:2]
    def texel(uv):
        x = np.clip((uv[:, 0] % 1.0) * Ww, 0, Ww - 1).astype(int); y = np.clip((1 - uv[:, 1] % 1.0) * Hh, 0, Hh - 1).astype(int)
        return atlas[y, x, :3]
    fid = np.repeat(np.arange(P), lt)
    tsum = np.zeros((P, 3)); np.add.at(tsum, fid, texel(u0))
    ucen = np.zeros((P, 2)); np.add.at(ucen, fid, u0); ucen /= lt[:, None]
    tex = (tsum + texel(ucen)) / (lt + 1)[:, None]
    mx, mn = tex.max(1), tex.min(1)
    pale = ((mx - mn) / np.maximum(mx, 1e-4) < TEAR_SATURATION) | (mx < 0.2)
    # each garment's own vertex colour (one per part)
    colour = {}
    for q in (1, 2, 3, 4):
        m = np.repeat(part == q, lt)
        if m.any():
            vals, cnt = np.unique(np.round(cd[m], 4), axis=0, return_counts=True); colour[q] = vals[np.argmax(cnt)]
    if not colour: return 0
    tree = cKDTree(cen)
    new_part = part.copy()
    for _ in range(3):
        cand = np.flatnonzero((new_part == 0) & pale)
        changed = False
        for i, ids in zip(cand, tree.query_ball_point(cen[cand], TEAR_RADIUS * H)):
            ids = np.asarray([j for j in ids if j != i], int)
            if len(ids) == 0: continue
            w = area[ids] * (nrm[ids] @ nrm[i] > 0.3)
            tot = w.sum()
            if tot <= 0: continue
            best, bw = 0, 0.0
            for q in colour:
                s = w[new_part[ids] == q].sum()
                if s > bw: best, bw = q, s
            if best and bw >= TEAR_SHARE * tot:
                new_part[i] = best; changed = True
        if not changed: break
    moved = new_part != part
    if not moved.any(): return 0
    lm = np.repeat(moved, lt)
    lp = np.repeat(new_part, lt)
    u1[lm, 0] = lp[lm]
    cd[lm] = np.array([colour[q] for q in lp[lm]])
    me.uv_layers[1].data.foreach_set('uv', u1.ravel())
    col.data.foreach_set('color', cd.ravel())
    me.update()
    return int(moved.sum())


def face_lean(o, rig, strength):
    """The face's lean toward a smooth rounded shape: per vertex, how much (0..strength), and the direction it leans to.
    The face is the skin (part 0) of the head (on the Head bone, made rigid by rigid_head) facing forward; its middle,
    down over the mouth and the chin, leans fully, fading out toward the cheeks' edge, the hairline and under the chin.
    The direction is the normal of a sphere centred FACE_ROUND face half-widths behind the face (docs/LEARNINGS.md C15): a
    constant forward lean lit the middle as one flat plane while the jaw kept the scan's noisy normals, and the light/shade
    step ran across the mouth and chin as a jagged crease that crawled as the head turned. Leaning to a sphere, the face
    shades as one rounded shape: lit as a whole in front light, with a clean curved edge when the sun is to one side."""
    me = o.data
    nv = len(me.vertices)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    if 'Head' not in o.vertex_groups or 'Nose' not in rig.data.bones: return None
    gi = o.vertex_groups['Head'].index
    hw = np.zeros(nv)
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi: hw[v.index] = g.weight
    part = vertex_parts(me)
    B = rig.data.bones
    head = np.array(B['Head'].head_local); nose = np.array(B['Nose'].head_local)
    fwd = nose - head; fwd[2] = 0; fwd /= np.linalg.norm(fwd)
    side = np.cross(fwd, [0, 0, 1.0])
    me.calc_loop_triangles()
    T = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('vertices', T); T = T.reshape(-1, 3)
    p = co[T]; fn = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    vn = np.zeros_like(co)
    for k in range(3): np.add.at(vn, T[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-20)
    rel = co - head
    skin = (part == 0) & (hw > 0.5)
    w = skin * np.clip((vn @ fwd + 0.1) / 0.4, 0, 1) * np.clip((rel @ fwd) / 0.04, 0, 1)
    if (w > 0.3).sum() < 20: return None
    x = rel @ side; z = rel[:, 2]
    cx = np.average(x, weights=w + 1e-9); cz = np.average(z, weights=w + 1e-9)
    hx = np.sqrt(np.average((x - cx) ** 2, weights=w + 1e-9)) * 1.9
    hz = np.sqrt(np.average((z - cz) ** 2, weights=w + 1e-9)) * 1.9
    rr = np.sqrt(((x - cx) / hx) ** 2 + ((z - cz) / hz) ** 2)
    m = np.clip((1.6 - rr) / 0.5, 0, 1) * np.clip(w / 0.4, 0, 1)
    # the scan's own normals are noisy, so the mask is too: even it out over the surface (only within the skin)
    E = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
    deg = np.bincount(E.ravel(), minlength=nv).astype(float)
    for _ in range(8):
        s = np.zeros(nv); np.add.at(s, E[:, 0], m[E[:, 1]]); np.add.at(s, E[:, 1], m[E[:, 0]])
        m = np.where(skin, 0.5 * m + 0.5 * s / np.maximum(deg, 1), 0.0)
    # the sphere: centred behind the middle of the face, FACE_ROUND face half-widths back
    fc = head + side * cx + np.array([0, 0, 1.0]) * cz + fwd * np.average(rel @ fwd, weights=w + 1e-9)
    centre = fc - fwd * FACE_ROUND * hx          # (hx: about the face's half-width)
    d = co - centre; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    return np.clip(m * 1.15, 0, 1) * strength, d


def smooth_normals(o, face=None):
    """Proximity-smoothed vertex normals (see polish_character.py), set as the mesh's custom normals; with `face`, the
    inner face leaned toward the head's forward direction."""
    me = o.data; me.calc_loop_triangles()
    nv = len(me.vertices)
    co = np.zeros(nv * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    T = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('vertices', T); T = T.reshape(-1, 3)
    p = co[T]; fn = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); area = np.linalg.norm(fn, axis=1)
    fnu = fn / np.maximum(area, 1e-20)[:, None]
    cen = p.mean(1)
    vn = np.zeros((nv, 3))
    for k in range(3): np.add.at(vn, T[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-20)[:, None]
    part = vertex_parts(me) if len(me.uv_layers) > 1 else np.full(nv, -1)
    rad = np.array([RADIUS.get(int(k), DEFAULT_RADIUS) for k in part])
    tree = cKDTree(cen)
    out = vn.copy()
    for r in np.unique(rad):
        idx = np.flatnonzero(rad == r)
        for i, ids in zip(idx, tree.query_ball_point(co[idx], r)):
            if not ids: continue
            ids = np.asarray(ids)
            w = area[ids] * np.clip(fnu[ids] @ vn[i], 0, None)       # never from the far side of a thin part
            d = np.linalg.norm(cen[ids] - co[i], axis=1); w *= np.clip(1 - d / r, 0, 1) ** 2
            s = (fnu[ids] * w[:, None]).sum(0); L = np.linalg.norm(s)
            if L > 1e-12: out[i] = s / L
    # Hair: the scans model it as many thin strands facing every way, and the toon shader's rim light (added whatever
    # the hair's colour) lit them as white speckle. Each hair vertex points away from the middle of the hair mass around
    # it (the centroid of everything within HAIR_VOLUME), mostly, so the hair shades as one soft volume and the rim shows
    # only round its outline.
    hair = np.flatnonzero(part == 3)
    if len(hair):
        vtree = cKDTree(co)
        for i, ids in zip(hair, vtree.query_ball_point(co[hair], HAIR_VOLUME)):
            if len(ids) < 8: continue
            vol = co[i] - co[ids].mean(0); L = np.linalg.norm(vol)
            if L < 1e-6: continue
            vol /= L
            if vol @ out[i] < -0.2: continue          # a strand's underside, inside the mass: keep its own normal
            n = vol * HAIR_VOLUME_MIX + out[i] * (1 - HAIR_VOLUME_MIX)
            out[i] = n / max(np.linalg.norm(n), 1e-9)
    if face is not None:
        m, to = face                      # how much, and the direction (one, or one per vertex)
        lean = np.broadcast_to(to, out.shape) * 0.85 + out * 0.15
        lean /= np.linalg.norm(lean, axis=1, keepdims=True)
        out = out * (1 - m[:, None]) + lean * m[:, None]
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    me.normals_split_custom_set_from_vertices([tuple(x) for x in out])


# ------------------------------------------------------------------------------------------------ atlas
def uv_triangles(o, layer=0):
    me = o.data; me.calc_loop_triangles()
    L = np.zeros(len(me.loop_triangles) * 3, int); me.loop_triangles.foreach_get('loops', L)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[layer].data.foreach_get('uv', uv)
    return uv.reshape(-1, 2)[L.reshape(-1, 3)]


def rasterize(uv_tris, size):
    """Every texel centre covered by a UV triangle: the triangle's index (-1 none) and the barycentric weights.
    Vectorised in batches of triangles grouped by their bounding box's size."""
    N = size
    P = uv_tris.astype(np.float64).copy()
    P[..., 0] *= N
    P[..., 1] = (1.0 - P[..., 1]) * N
    tri = -np.ones((N, N), np.int32)
    bary = np.zeros((N, N, 3), np.float32)
    best = np.full((N, N), -np.inf, np.float32)
    x0 = np.floor(P[..., 0].min(1) - 0.5).astype(int); x1 = np.ceil(P[..., 0].max(1) - 0.5).astype(int)
    y0 = np.floor(P[..., 1].min(1) - 0.5).astype(int); y1 = np.ceil(P[..., 1].max(1) - 0.5).astype(int)
    ext = np.maximum(np.maximum(x1 - x0 + 1, y1 - y0 + 1), 1)
    a, b, c = P[:, 0], P[:, 1], P[:, 2]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(den) > 1e-12
    area = np.abs(den)
    for lo, hi in ((0, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128), (128, 1 << 20)):
        sel = np.flatnonzero(ok & (ext > lo) & (ext <= hi))
        if len(sel) == 0: continue
        G = hi if hi < (1 << 20) else int(ext[sel].max())
        gy, gx = np.mgrid[0:G, 0:G]; gx = gx.ravel(); gy = gy.ravel()
        batch = max(1, int(4e6 // (G * G)))
        for s in range(0, len(sel), batch):
            t = sel[s:s + batch]
            px = x0[t][:, None] + gx[None, :]; py = y0[t][:, None] + gy[None, :]
            inbox = (px <= x1[t][:, None]) & (py <= y1[t][:, None]) & (px >= 0) & (py >= 0) & (px < N) & (py < N)
            cx = px + 0.5; cy = py + 0.5
            l0 = ((b[t, 1] - c[t, 1])[:, None] * (cx - c[t, 0][:, None]) + (c[t, 0] - b[t, 0])[:, None] * (cy - c[t, 1][:, None])) / den[t][:, None]
            l1 = ((c[t, 1] - a[t, 1])[:, None] * (cx - c[t, 0][:, None]) + (a[t, 0] - c[t, 0])[:, None] * (cy - c[t, 1][:, None])) / den[t][:, None]
            l2 = 1 - l0 - l1
            m = inbox & (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            ii, jj = np.nonzero(m)
            if len(ii) == 0: continue
            X = px[ii, jj]; Y = py[ii, jj]; Tt = t[ii]; ar = area[Tt].astype(np.float32)
            order = np.argsort(ar)
            X, Y, Tt, ar = X[order], Y[order], Tt[order], ar[order]
            Lb = np.stack([l0[ii, jj][order], l1[ii, jj][order], l2[ii, jj][order]], 1).astype(np.float32)
            keep = ar >= best[Y, X]
            X, Y, Tt, ar, Lb = X[keep], Y[keep], Tt[keep], ar[keep], Lb[keep]
            tri[Y, X] = Tt; bary[Y, X] = Lb; best[Y, X] = ar
    return tri, bary


def coverage(uv_tris, size):
    """Texels bilinear sampling inside the triangles can reach: centres inside a triangle, plus the texels under each
    triangle's corners, edge midpoints and centre (so slivers thinner than a texel still count)."""
    tri, _ = rasterize(uv_tris, size)
    cov = tri >= 0
    pts = np.concatenate([uv_tris, (uv_tris + np.roll(uv_tris, 1, axis=1)) / 2, uv_tris.mean(1, keepdims=True)], 1).reshape(-1, 2)
    X = np.clip((pts[:, 0] * size).astype(int), 0, size - 1); Y = np.clip(((1 - pts[:, 1]) * size).astype(int), 0, size - 1)
    cov[Y, X] = True
    # and their 4-neighbours: bilinear filtering at an island's edge reads half a texel outside it
    from scipy import ndimage
    return ndimage.binary_dilation(cov)


def push_pull(img, mask):
    """Fills every texel outside `mask` with a smooth extension of the colours inside it (a pull down a mip chain of the
    masked colours, then a push back up), so a mip level never averages a gap's foreign colour into an island."""
    img = img.astype(np.float32); m = mask.astype(np.float32)
    pyr = []
    c = img * m[..., None]; w = m.copy()
    while min(c.shape[0], c.shape[1]) > 1:
        pyr.append((c, w))
        h2, w2 = c.shape[0] // 2, c.shape[1] // 2
        c = c[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, -1).sum((1, 3))
        w = w[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).sum((1, 3))
    filled = c / np.maximum(w, 1e-8)[..., None]
    for c, w in reversed(pyr):
        up = np.repeat(np.repeat(filled, 2, 0), 2, 1)[:c.shape[0], :c.shape[1]]
        own = c / np.maximum(w, 1e-8)[..., None]
        k = np.clip(w, 0, 1)[..., None]
        filled = own * k + up * (1 - k)
    out = img.copy()
    out[~mask] = filled[~mask]
    return out


def load_png(path):
    im = Image.open(path)
    mode = 'RGBA' if im.mode in ('RGBA', 'LA') else 'RGB'
    return np.asarray(im.convert(mode)).astype(np.float32) / 255.0


def save_png(a, path):
    a = np.clip(a, 0, 1)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def fill_atlas(o, atlas_path, layer=0):
    A = load_png(atlas_path)
    cov = coverage(uv_triangles(o, layer), A.shape[0])
    return push_pull(A, cov)


# ------------------------------------------------------------------------------------------------ texture clean-up
# The scans' textures carry photographic noise: pores and blotches on the skin, single strands of hair, the speckle of
# a printed T-shirt's cotton. Under two flat cel bands that reads as dirt. clean_atlas() smooths it on the surface itself
# (never across the atlas, whose neighbouring texels belong to unrelated islands): each texel is placed in 3D, the texels
# of the same outfit part facing the same way are averaged in a small 3D neighbourhood, and only the weak detail is
# taken away (cored): a difference from the average under the part's threshold goes, a strong one (a seam, a print, a
# logo, a stripe, a drawn eye) comes back exactly as painted.
# radius (m) and coring threshold (luminance difference of the final colour, atlas times vertex colour) by outfit part:
CLEAN = {0: (0.006, 0.05), 1: (0.004, 0.06), 2: (0.004, 0.06), 3: (0.008, 0.12), 4: (0.004, 0.06)}


def texel_surface(o, size):
    """Every covered atlas texel's 3D position, normal, outfit part and vertex colour (from the mesh `o`'s UVs)."""
    me = o.data; me.calc_loop_triangles()
    LT = len(me.loop_triangles)
    L = np.zeros(LT * 3, int); me.loop_triangles.foreach_get('loops', L); L = L.reshape(-1, 3)
    V = np.zeros(LT * 3, int); me.loop_triangles.foreach_get('vertices', V); V = V.reshape(-1, 3)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    tri, bary = rasterize(uv[L], size)
    m = tri >= 0
    T = tri[m]; B = bary[m]
    P = (co[V[T]] * B[..., None]).sum(1)
    p = co[V]; fn = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
    N = fn[T]
    if len(me.uv_layers) > 1:
        u1 = np.zeros(len(me.loops) * 2); me.uv_layers[1].data.foreach_get('uv', u1); u1 = u1.reshape(-1, 2)
        part = np.round(u1[L[T, 0], 0]).astype(int)
    else:
        part = np.zeros(len(T), int)
    vc = np.ones((len(T), 3))
    if 'Col' in me.color_attributes:
        col = me.color_attributes['Col']
        cd = np.zeros(len(col.data) * 4); col.data.foreach_get('color', cd); cd = cd.reshape(-1, 4)[:, :3]
        if col.domain == 'POINT': vc = (cd[V[T]] * B[..., None]).sum(1)
        else: vc = (cd[L[T]] * B[..., None]).sum(1)
    return m, P, N, part, vc


def _voxel_mean(P, N, part, colour, cell):
    """The mean colour of the texels around each texel: a 3x3x3 neighbourhood of `cell`-sized voxels, separately for each
    outfit part and each of the six directions a surface can face (so the two sides of a thin part never mix)."""
    face = np.argmax(np.abs(N), 1) * 2 + (N[np.arange(len(N)), np.argmax(np.abs(N), 1)] > 0)
    g = np.floor(P / cell).astype(np.int64)
    off = (1 << 20)
    def key(gx, gy, gz):
        return ((((gx + off) * (1 << 21) + (gy + off)) * (1 << 21) + (gz + off)) * 8 + face) * 8 + part
    k0 = key(g[:, 0], g[:, 1], g[:, 2])
    uk, inv = np.unique(k0, return_inverse=True)
    inv = inv.ravel()
    sums = np.zeros((len(uk), colour.shape[1])); cnt = np.zeros(len(uk))
    np.add.at(sums, inv, colour); np.add.at(cnt, inv, 1)
    acc = np.zeros_like(colour, dtype=np.float64); w = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                k = key(g[:, 0] + dx, g[:, 1] + dy, g[:, 2] + dz)
                i = np.searchsorted(uk, k); i = np.clip(i, 0, len(uk) - 1)
                hit = uk[i] == k
                wt = 1.0 / (1 + abs(dx) + abs(dy) + abs(dz))
                acc[hit] += sums[i[hit]] * wt; w[hit] += cnt[i[hit]] * wt
    return acc / np.maximum(w, 1e-9)[:, None]


def clean_atlas(o, atlas, keep=None, clean=CLEAN):
    """The atlas with its weak, noisy detail smoothed away on the surface (see above). keep: an optional boolean mask
    of texels (atlas-sized) left exactly as they are (a painted face)."""
    size = atlas.shape[0]
    m, P, N, part, vc = texel_surface(o, size)
    A = atlas.copy()
    rgb = A[..., :3][m].astype(np.float64)
    final = rgb * vc
    out = rgb.copy()
    lumw = np.array([0.299, 0.587, 0.114])
    for pid, (radius, thr) in clean.items():
        sel = part == pid
        if sel.sum() < 100: continue
        mean_final = _voxel_mean(P[sel], N[sel], part[sel], final[sel], radius)
        mean_rgb = _voxel_mean(P[sel], N[sel], part[sel], rgb[sel], radius)
        diff = np.abs((final[sel] - mean_final) @ lumw)
        t = np.clip((diff - thr * 0.5) / (thr * 0.5), 0, 1); t = t * t * (3 - 2 * t)   # 0 below thr/2, 1 above thr
        out[sel] = mean_rgb + (rgb[sel] - mean_rgb) * t[:, None]
    flat = A[..., :3].reshape(-1, 3)
    idx = np.flatnonzero(m.ravel())
    res = np.clip(out, 0, 1).astype(np.float32)
    if keep is not None:
        kk = keep.ravel()[idx]
        res[kk] = flat[idx][kk]
    flat[idx] = res
    A[..., :3] = flat.reshape(A[..., :3].shape)
    return A
