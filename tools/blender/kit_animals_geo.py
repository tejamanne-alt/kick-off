# Geometry helpers for kit_animals.py (the stylized animals and collectibles). Read
# docs/ART_DIRECTION.md first.
#
# Organic parts are modelled as signed distance fields (SDF): ellipsoids, round cones, tubes and
# tori combined with smooth unions, so a muzzle melts into a head and a haunch into a body. A
# field is meshed with surface nets on a fine grid, decimated in Blender (quadric collapse, mirror
# symmetric where the part is) to the triangle budget, and its vertices are projected back onto
# the field. Normals come from the field's gradient, so the low-poly mesh shades like the smooth
# form it stands for.
#
# Markings (a pale muzzle, a dark wing tip, a mouth line, collar bands) are crisp: the mesh is cut
# along the zero line of each marking field, and every face then belongs to one region, coloured
# by that region's function. Vertices on a cut are split, so each side keeps its own colour and
# recolour part while the normals stay shared (no visible seam in the shading).
#
# Thin or precise parts (wings, eyes, antennae, coins) are explicit meshes: lofts, lathes, tubes.
# Everything ends up in Pieces (numpy meshes with a position, normal, scene-linear RGBA colour,
# atlas UV and recolour part per vertex) that to_object() turns into a Blender mesh carrying the
# kit_lib contract: colour attribute 'Col' (BYTE_COLOR, CORNER), UV0 the atlas, UV1.x the part,
# custom split normals.
import math
import numpy as np
import bpy

WHITE_UV = (0.97, 0.03)
PI = math.pi


# ---------------------------------------------------------------- colour and maths
def s2l(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(np.asarray(c, float), 0, None)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def hexc(h):
    """'#rrggbb' (sRGB) -> scene-linear RGB."""
    h = h.lstrip('#')
    return s2l(np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]))


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def unit(a):
    a = np.asarray(a, float)
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.maximum(n, 1e-12)


def lerp(a, b, t):
    t = np.asarray(t, float)
    if t.ndim == 1 and np.ndim(a) >= 1:
        t = t[:, None]
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def shade_srgb(base_lin, k):
    """Scale a scene-linear colour's brightness by k as seen in sRGB (k per vertex), so the baked
    shading steps look even and the game's brightness-ratio recolour reads it back as k."""
    s = l2s(base_lin)[None, :] * np.asarray(k, float)[:, None]
    return s2l(np.clip(s, 0, 1))


def frame(z, up=(0, 0, 1)):
    """Rotation matrix whose columns are local axes: z along z, y leaning toward up."""
    z = unit(np.asarray(z, float)); up = np.asarray(up, float)
    x = np.cross(up, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross((1.0, 0, 0), z)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross((0, 1.0, 0), z)
    x = unit(x); y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)


def axes(x, y=None, z=None):
    """Rotation matrix from two given local axes (the third completes a right-handed frame)."""
    if z is None:
        x = unit(x); y = unit(np.asarray(y, float) - x * np.dot(y, x)); z = np.cross(x, y)
    elif y is None:
        z = unit(z); x = unit(np.asarray(x, float) - z * np.dot(x, z)); y = np.cross(z, x)
    else:
        y = unit(y); z = unit(np.asarray(z, float) - y * np.dot(z, y)); x = np.cross(y, z)
    return np.stack([x, y, z], axis=1)


def rot(axis, ang):
    a = unit(np.asarray(axis, float)); c, s = math.cos(ang), math.sin(ang)
    x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def catmull(points, n):
    """n points along a Catmull-Rom spline through the control points."""
    P = np.asarray(points, float)
    if len(P) == 2:
        return np.array([P[0] + (P[1] - P[0]) * t for t in np.linspace(0, 1, n)])
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    seg = len(P) - 1
    out = []
    for t in np.linspace(0, seg, n):
        i = min(int(t), seg - 1); u = t - i
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return np.array(out)


def interp(vals, n):
    """Resample a list of values (one per control point) to n evenly spaced values."""
    vals = np.asarray(vals, float)
    return np.interp(np.linspace(0, len(vals) - 1, n), np.arange(len(vals)), vals)


# ---------------------------------------------------------------- signed distance fields
# A field is a callable P (N x 3) -> distance (N). Primitives are exact or close bounds; the
# smooth operators blend them. Fields need not be exact: the mesher only needs the zero set and
# a sensible gradient.
def sphere(c, r):
    c = np.asarray(c, float)
    return lambda P: np.linalg.norm(P - c, axis=1) - r


def ellipsoid(c, r, R=None):
    """Ellipsoid at c with radii r along the columns of R (world axes when R is None)."""
    c = np.asarray(c, float); r = np.asarray(r, float)

    def f(P):
        q = P - c
        if R is not None:
            q = q @ R
        k0 = np.linalg.norm(q / r, axis=1)
        k1 = np.linalg.norm(q / (r * r), axis=1)
        d = k0 * (k0 - 1) / np.maximum(k1, 1e-9)
        return np.where(k1 < 1e-9, -r.min(), d)
    return f


def round_cone(a, b, ra, rb):
    """A capsule from a (radius ra) to b (radius rb), tangent-continuous (iq's round cone)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    ba = b - a; l2 = float(ba @ ba); rr = ra - rb; a2 = l2 - rr * rr; il2 = 1.0 / l2

    def f(P):
        pa = P - a
        y = pa @ ba; z = y - l2
        x2v = pa * l2 - y[:, None] * ba
        x2 = np.einsum('ij,ij->i', x2v, x2v)
        y2 = y * y * l2; z2 = z * z * l2
        k = np.sign(rr) * rr * rr * x2
        d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - ra
        d1 = np.sqrt(x2 + z2) * il2 - rb
        d2 = np.sqrt(x2 + y2) * il2 - ra
        return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))
    return f


def tube(points, radii, n=None):
    """A smooth tapered tube through control points (radii per control point): a chain of round
    cones along a Catmull-Rom spline."""
    if n is None:
        n = max(2, 3 * (len(points) - 1) + 1)
    P = catmull(points, n) if len(points) > 2 else np.asarray(points, float)
    R = interp(radii, len(P))
    cones = [round_cone(P[i], P[i + 1], R[i], R[i + 1]) for i in range(len(P) - 1)]

    def f(Q):
        d = cones[0](Q)
        for c in cones[1:]:
            d = np.minimum(d, c(Q))
        return d
    return f


def flat_tube(points, radii, flat, normal, n=None):
    """A tube squashed to `flat` (0..1) of its radius along `normal` (a ribbon-like limb: ears,
    tail plumes). Distances are scaled, not exact."""
    normal = unit(normal)
    c = np.asarray(points, float).mean(axis=0)
    M = np.eye(3) + (1.0 / flat - 1.0) * np.outer(normal, normal)   # stretches space along normal
    base = tube([c + (p - c) for p in np.asarray(points, float)], radii, n)

    def f(P):
        Q = c + (P - c) @ M.T
        return base(Q) * flat
    return f


def torus(c, axis, R, r):
    c = np.asarray(c, float); M = frame(axis)

    def f(P):
        q = (P - c) @ M
        a = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - R
        return np.sqrt(a * a + q[:, 2] ** 2) - r
    return f


def rbox(c, half, r, R=None):
    c = np.asarray(c, float); half = np.asarray(half, float)

    def f(P):
        q = P - c
        if R is not None:
            q = q @ R
        q = np.abs(q) - half + r
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - r
    return f


def cylinder(c, axis, r, h, rr=0.0):
    """A capped cylinder (radius r, half height h along axis) with rounded edges rr."""
    c = np.asarray(c, float); M = frame(axis)

    def f(P):
        q = (P - c) @ M
        d = np.stack([np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2) - r + rr, np.abs(q[:, 2]) - h + rr], axis=1)
        return np.minimum(d.max(axis=1), 0) + np.linalg.norm(np.maximum(d, 0), axis=1) - rr
    return f


def plane(p, n):
    """Half-space: negative behind the plane through p with outward normal n."""
    p = np.asarray(p, float); n = unit(n)
    return lambda P: (P - p) @ n


def mirror_y(f):
    """Evaluate f on the +Y side only (a mirrored pair from one definition)."""
    return lambda P: f(np.column_stack([P[:, 0], np.abs(P[:, 1]), P[:, 2]]))


def mirror_x(f):
    """Evaluate f on the +X side only (for the crab, which faces -Y)."""
    return lambda P: f(np.column_stack([np.abs(P[:, 0]), P[:, 1], P[:, 2]]))


def orient_by_normals(p):
    """Flip each triangle whose winding disagrees with its vertices' normals."""
    V, T = p.V, p.T
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    bad = np.einsum('ij,ij->i', fn, p.N[T].sum(axis=1)) < 0
    p.T = np.where(bad[:, None], T[:, ::-1], T)
    return p


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def blend(base, *items):
    """base, then (field, k[, op]) items folded in: op 'add' (smooth union, default), 'sub'
    (smooth subtraction) or 'int' (smooth intersection)."""
    def f(P):
        d = base(P)
        for it in items:
            g, k = it[0], it[1]
            op = it[2] if len(it) > 2 else 'add'
            v = g(P)
            if op == 'add':
                d = smin(d, v, k)
            elif op == 'sub':
                d = smax(d, -v, k)
            else:
                d = smax(d, v, k)
        return d
    return f


def union(*fields):
    def f(P):
        d = fields[0](P)
        for g in fields[1:]:
            d = np.minimum(d, g(P))
        return d
    return f


def displaced(f, fn):
    """f plus a displacement field fn(P) (positive pushes the surface in)."""
    return lambda P: f(P) + fn(P)


def grad(f, P, eps=5e-4):
    P = np.asarray(P, float)
    G = np.zeros_like(P)
    for i in range(3):
        d = np.zeros(3); d[i] = eps
        G[:, i] = (f(P + d) - f(P - d)) / (2 * eps)
    return G


def project(f, P, iters=5, eps=5e-4):
    """Newton steps onto the zero set along the gradient."""
    P = np.array(P, float)
    for _ in range(iters):
        d = f(P)
        g = grad(f, P, eps)
        g2 = np.maximum(np.einsum('ij,ij->i', g, g), 1e-8)
        step = (d / g2)[:, None] * g
        # never jump further than a few millimetres in one step (thin parts, saddles)
        L = np.linalg.norm(step, axis=1, keepdims=True)
        step = np.where(L > 0.02, step * 0.02 / np.maximum(L, 1e-12), step)
        P -= step
    return P


def normals(f, P, eps=5e-4):
    return unit(grad(f, P, eps))


# ---------------------------------------------------------------- meshing
_CORNERS = [(dx, dy, dz) for dz in (0, 1) for dy in (0, 1) for dx in (0, 1)]
_EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]


def surface_nets(f, lo, hi, h, sym_y=False):
    """Naive surface nets: one vertex per grid cell the surface crosses (the mean of its edge
    crossings), one quad per crossed grid edge. Returns V (n x 3), quads (m x 4) facing out."""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    if sym_y:
        m = max(abs(lo[1]), abs(hi[1])); lo[1], hi[1] = -m, m
    n = np.maximum(np.ceil((hi - lo) / h).astype(int) + 1, 3)
    xs = [np.linspace(lo[i], lo[i] + h * (n[i] - 1), n[i]) for i in range(3)]
    if sym_y:
        xs[1] = xs[1] - xs[1].mean()
    X, Y, Z = np.meshgrid(*xs, indexing='ij')
    F = f(np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)).reshape(X.shape)
    border = np.concatenate([F[0].ravel(), F[-1].ravel(), F[:, 0].ravel(), F[:, -1].ravel(), F[:, :, 0].ravel(), F[:, :, -1].ravel()])
    if border.min() < 0:
        print('surface_nets: WARNING the field reaches the grid border', lo, hi)
    cn = n - 1
    vals = [F[dx:dx + cn[0], dy:dy + cn[1], dz:dz + cn[2]] for dx, dy, dz in _CORNERS]
    acc = np.zeros(tuple(cn) + (3,)); cnt = np.zeros(tuple(cn))
    for a, b in _EDGES:
        fa, fb = vals[a], vals[b]
        m = (fa < 0) != (fb < 0)
        if not m.any():
            continue
        t = np.where(m, fa / np.where(m, fa - fb, 1.0), 0.0)
        oa = np.array(_CORNERS[a], float); ob = np.array(_CORNERS[b], float)
        acc += m[..., None] * (oa + t[..., None] * (ob - oa))
        cnt += m
    active = cnt > 0
    idx = -np.ones(tuple(cn), np.int64)
    idx[active] = np.arange(active.sum())
    I = np.argwhere(active)
    org = np.array([xs[0][0], xs[1][0], xs[2][0]])
    V = org + h * (I + acc[active] / cnt[active][:, None])
    inside = F < 0
    quads = []
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        sl0 = [slice(None)] * 3; sl1 = [slice(None)] * 3
        sl0[a] = slice(0, n[a] - 1); sl1[a] = slice(1, n[a])
        for ax in (b, c):
            sl0[ax] = slice(1, n[ax] - 1); sl1[ax] = slice(1, n[ax] - 1)
        s0 = inside[tuple(sl0)]; s1 = inside[tuple(sl1)]
        m = s0 != s1
        if not m.any():
            continue
        G = np.argwhere(m)
        G[:, b] += 1; G[:, c] += 1
        out = s0[m]                      # inside at the low end: the surface faces +a
        cells = []
        for db, dc in ((-1, -1), (0, -1), (0, 0), (-1, 0)):
            K = G.copy(); K[:, b] += db; K[:, c] += dc
            cells.append(idx[K[:, 0], K[:, 1], K[:, 2]])
        Q = np.stack(cells, axis=1)
        Q = np.where(out[:, None], Q, Q[:, ::-1])
        quads.append(Q)
    Q = np.concatenate(quads) if quads else np.zeros((0, 4), np.int64)
    Q = Q[(Q >= 0).all(axis=1)]
    return V, Q


def _mesh_from(V, F, name='tmp'):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in V], [], [tuple(int(i) for i in f) for f in F])
    me.validate(clean_customdata=False)
    return me


def _read_tris(me):
    me.calc_loop_triangles()
    V = np.zeros((len(me.vertices), 3)); me.vertices.foreach_get('co', V.ravel())
    T = np.zeros((len(me.loop_triangles), 3), np.int64); me.loop_triangles.foreach_get('vertices', T.ravel())
    return V, T


def decimate(V, F, tris, sym=True, weights=None, wfactor=1.0):
    """Quadric-collapse V/F (any polygons) to about `tris` triangles in Blender. sym mirrors the
    collapse across Y = 0. weights (per vertex, 0..1) keep detail where they are high."""
    me = _mesh_from(V, F, 'dec')
    o = bpy.data.objects.new('dec', me)
    bpy.context.scene.collection.objects.link(o)
    total = sum(len(f) - 2 for f in F)
    md = o.modifiers.new('d', 'DECIMATE')
    md.decimate_type = 'COLLAPSE'
    md.ratio = min(1.0, tris / max(total, 1))
    md.use_collapse_triangulate = True
    if sym:
        md.use_symmetry = True; md.symmetry_axis = 'Y'
    if weights is not None:
        # Blender reads the group as influence: 1 collapses freely, low values hold detail.
        vg = o.vertex_groups.new(name='w')
        w = 1.0 - 0.85 * np.clip(np.asarray(weights, float), 0, 1)
        for lvl in np.unique(np.round(w, 2)):
            ids = np.nonzero(np.round(w, 2) == lvl)[0].tolist()
            vg.add(ids, float(lvl), 'REPLACE')
        md.vertex_group = 'w'; md.vertex_group_factor = wfactor
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    Vo, T = _read_tris(me2)
    bpy.data.objects.remove(o); bpy.data.meshes.remove(me); bpy.data.meshes.remove(me2)
    return Vo, T


def clean(V, T):
    """Drop unused vertices and degenerate triangles."""
    T = np.asarray(T, np.int64)
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    used = np.unique(T)
    remap = -np.ones(len(V), np.int64); remap[used] = np.arange(len(used))
    return np.asarray(V)[used], remap[T]


def mesh_field(f, lo, hi, h, tris, sym=False, weight=None, wfactor=1.0):
    """Mesh the field f inside the box lo..hi at grid step h, decimated to about `tris`
    triangles and projected back onto the surface. weight(P) -> 0..1 keeps more detail."""
    V, Q = surface_nets(f, lo, hi, h, sym_y=sym)
    V = project(f, V, iters=3)
    w = weight(V) if weight is not None else None
    V, T = decimate(V, Q, tris, sym=sym, weights=w, wfactor=wfactor)
    V, T = clean(V, T)
    V = project(f, V, iters=4)
    if sym:
        # keep the mirror plane exact (decimation is symmetric, projection may drift a hair)
        on = np.abs(V[:, 1]) < 1e-4
        V[on, 1] = 0.0
    return V, T


# ---------------------------------------------------------------- crisp regions
def cut(V, T, g, f=None, attrs=()):
    """Cut triangles along the zero set of the field g. New vertices are interpolated on the
    crossed edges (refined by a few regula-falsi steps) and projected onto the surface f (if
    given). attrs: per-vertex arrays interpolated along with the positions; returns
    (V, T) or (V, T, [attrs]) when attrs are given."""
    V = [np.asarray(v, float) for v in V]
    attrs = [list(np.asarray(a, float)) for a in attrs]
    vals = list(g(np.asarray(V)))
    made = {}
    newT = []
    fresh = []

    def cross(a, b):
        key = (a, b) if a < b else (b, a)
        if key in made:
            return made[key]
        pa, pb, ga, gb = V[a], V[b], vals[a], vals[b]
        lo_t, hi_t, glo, ghi = 0.0, 1.0, ga, gb
        t = ga / (ga - gb)
        for _ in range(4):
            gt = float(g((pa + t * (pb - pa))[None])[0])
            if (gt < 0) == (glo < 0):
                lo_t, glo = t, gt
            else:
                hi_t, ghi = t, gt
            if abs(ghi - glo) < 1e-12:
                break
            t = lo_t + (hi_t - lo_t) * glo / (glo - ghi)
        p = pa + t * (pb - pa)
        i = len(V); V.append(p); vals.append(0.0); made[key] = i; fresh.append(i)
        for at in attrs:
            at.append(at[a] * (1 - t) + at[b] * t)
        return i
    for tri in np.asarray(T):
        s = [vals[i] >= 0 for i in tri]
        if s[0] == s[1] == s[2]:
            newT.append(tuple(tri)); continue
        for r in range(3):
            a, b, c = tri[r], tri[(r + 1) % 3], tri[(r + 2) % 3]
            if s[r] != s[(r + 1) % 3] and s[(r + 1) % 3] == s[(r + 2) % 3]:
                break
        ab = cross(a, b); ac = cross(a, c)
        newT += [(a, ab, ac), (ab, b, c), (ab, c, ac)]
    V = np.array(V)
    if f is not None and fresh:
        V[fresh] = project(f, V[fresh], iters=3)
    T = np.array(newT, np.int64)
    if attrs:
        return V, T, [np.array(a) for a in attrs]
    return V, T


def refine(V, T, need, maxlen, f=None, iters=4):
    """Split the longest edge of every triangle whose centroid satisfies need(C) (bool per
    triangle) while it is longer than maxlen; neighbours split the same edges (conforming).
    New vertices are projected onto the surface f. Used before cutting thin painted lines."""
    V = [np.asarray(v, float) for v in V]
    T = [tuple(int(i) for i in t) for t in T]
    for _ in range(iters):
        Va = np.array(V); Ta = np.array(T)
        sel = np.nonzero(need(Va[Ta].mean(axis=1)))[0]
        mark = set()
        for k in sel:
            a, b, c = Ta[k]
            es = [(a, b), (b, c), (c, a)]
            L = [np.linalg.norm(Va[x] - Va[y]) for x, y in es]
            j = int(np.argmax(L))
            if L[j] > maxlen:
                x, y = es[j]; mark.add((min(x, y), max(x, y)))
        if not mark:
            break
        mid = {}
        for e in mark:
            mid[e] = len(V); V.append(0.5 * (V[e[0]] + V[e[1]]))
        fresh = list(mid.values())
        if f is not None:
            P = project(f, np.array([V[i] for i in fresh]), iters=3)
            for i, p in zip(fresh, P):
                V[i] = p
        newT = []
        for (a, b, c) in T:
            m = [mid.get((min(a, b), max(a, b))), mid.get((min(b, c), max(b, c))), mid.get((min(c, a), max(c, a)))]
            cnt = sum(x is not None for x in m)
            if cnt == 0:
                newT.append((a, b, c)); continue
            # rotate so the pattern starts at a known edge
            vs = [a, b, c]
            for r in range(3):
                mm = m[r:] + m[:r]; vv = vs[r:] + vs[:r]
                if cnt == 1 and mm[0] is not None: break
                if cnt == 2 and mm[0] is not None and mm[1] is not None: break
                if cnt == 3: break
            a_, b_, c_ = vv
            if cnt == 1:
                newT += [(a_, mm[0], c_), (mm[0], b_, c_)]
            elif cnt == 2:
                newT += [(mm[0], b_, mm[1]), (a_, mm[0], mm[1]), (a_, mm[1], c_)]
            else:
                newT += [(a_, mm[0], mm[2]), (mm[0], b_, mm[1]), (mm[2], mm[1], c_), (mm[0], mm[1], mm[2])]
        T = newT
    return np.array(V), np.array(T, np.int64)


def regions(V, T, masks):
    """Region per triangle: the index of the first mask positive at its centroid, else -1."""
    C = np.asarray(V)[np.asarray(T)].mean(axis=1)
    R = -np.ones(len(T), np.int64)
    for i in range(len(masks) - 1, -1, -1):
        R[masks[i](C) > 0] = i
    return R


def band(field, width):
    """A mask positive within width/2 of the zero set of field (lines painted on a surface)."""
    return lambda P: width * 0.5 - np.abs(field(P))


# ---------------------------------------------------------------- pieces
def vnormals(V, T):
    V = np.asarray(V, float); T = np.asarray(T, np.int64)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    return unit(N)


class Piece:
    """A triangle mesh with per-vertex position V, normal N, scene-linear RGBA colour C, atlas
    UV U and recolour part P."""
    def __init__(self, V, T, N=None):
        self.V = np.asarray(V, float).reshape(-1, 3)
        self.T = np.asarray(T, np.int64).reshape(-1, 3)
        self.N = vnormals(self.V, self.T) if N is None else unit(np.asarray(N, float))
        n = len(self.V)
        self.C = np.ones((n, 4))
        self.U = np.tile(np.array(WHITE_UV), (n, 1))
        self.P = np.zeros(n)

    def tris(self):
        return len(self.T)

    def color(self, rgb):
        rgb = np.asarray(rgb, float)
        self.C[:, :3] = np.broadcast_to(rgb, (len(self.V), 3)) if rgb.ndim == 1 else rgb
        return self

    def part(self, p):
        self.P[:] = p
        return self

    def move(self, R=None, t=(0, 0, 0)):
        if R is not None:
            R = np.asarray(R, float)
            self.V = self.V @ R.T; self.N = unit(self.N @ R.T)
            if np.linalg.det(R) < 0:
                self.T = self.T[:, ::-1]
        self.V = self.V + np.asarray(t, float)
        return self

    def copy(self):
        q = Piece(self.V.copy(), self.T.copy(), self.N.copy())
        q.C = self.C.copy(); q.U = self.U.copy(); q.P = self.P.copy()
        return q

    def mirrored_y(self):
        q = self.copy()
        q.V[:, 1] *= -1; q.N[:, 1] *= -1; q.T = q.T[:, ::-1]
        return q


def signed_volume(p):
    V = p.V; T = p.T
    return float(np.einsum('ij,ij->i', V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6.0)


def outward(p):
    """Flip a closed piece whose faces look inward (negative signed volume)."""
    if signed_volume(p) < 0:
        p.T = p.T[:, ::-1]
    return p


def merge(pieces):
    pieces = [p for p in pieces if p is not None and len(p.V)]
    out = Piece(np.zeros((0, 3)), np.zeros((0, 3), np.int64), N=np.zeros((0, 3)))
    off = 0; Ts = []
    for p in pieces:
        Ts.append(p.T + off); off += len(p.V)
    out.V = np.concatenate([p.V for p in pieces]); out.N = np.concatenate([p.N for p in pieces])
    out.C = np.concatenate([p.C for p in pieces]); out.U = np.concatenate([p.U for p in pieces])
    out.P = np.concatenate([p.P for p in pieces]); out.T = np.concatenate(Ts)
    return out


def split_by_region(V, T, N, R):
    """{region: (Piece, vertex indices into V)}; vertices on region borders are duplicated."""
    out = {}
    for r in np.unique(R):
        sel = T[R == r]
        used = np.unique(sel)
        remap = -np.ones(len(V), np.int64); remap[used] = np.arange(len(used))
        out[int(r)] = (Piece(V[used], remap[sel], N[used]), used)
    return out


def paint_piece(p, masks, paint, ao_vals=None):
    """Regions on an explicit Piece: cut along each mask (no projection; normals and UVs are
    interpolated), then colour each region with paint[name](V, N, U, ao) -> (rgb, part[, uv]).
    Returns one Piece per region."""
    V, T = p.V, p.T
    N, U = p.N, p.U
    A = np.ones(len(V)) if ao_vals is None else np.asarray(ao_vals, float)
    for m in masks:
        for g in (m[2] if len(m) > 2 else [m[1]]):
            V, T, (N, U, A) = cut(V, T, g, None, attrs=(N, U, A))
    N = unit(N)
    R = regions(V, T, [m[1] for m in masks])
    names = [m[0] for m in masks]
    out = []
    for r, (pc, idx) in split_by_region(V, T, N, R).items():
        key = names[r] if r >= 0 else 'base'
        pc.U = U[idx]
        res = paint[key](pc.V, pc.N, pc.U, A[idx])
        pc.color(res[0]); pc.part(res[1])
        if len(res) > 2 and res[2] is not None:
            pc.U = res[2]
        out.append(pc)
    return out


def ao(field, V, N, scale, steps=5, strength=1.0):
    """Ambient occlusion from the distance field (iq): 1 open, toward 0 in creases."""
    occ = np.zeros(len(V)); w = 1.0
    for i in range(1, steps + 1):
        hgt = scale * i / steps
        d = field(V + N * hgt)
        occ += w * np.clip(hgt - d, 0, None) / scale
        w *= 0.7
    return np.clip(1 - strength * occ, 0, 1)


def ground_ao(V, height, floor=0.0):
    """Darkening near the ground (contact shadow baked into feet and bellies)."""
    return 1 - 0.35 * smoothstep(height, 0.0, V[:, 2] - floor)


class Surface:
    """An SDF part meshed and split into coloured regions.
    regions: [(name, mask)] in priority order; paint: name -> fn(V, N) -> (rgb array, part) and
    optionally uv fn. Default region name is 'base'."""
    def __init__(self, f, lo, hi, h, tris, sym=False, weight=None, wfactor=1.0):
        self.f = f
        self.V, self.T = mesh_field(f, lo, hi, h, tris, sym=sym, weight=weight, wfactor=wfactor)

    def pieces(self, masks, paint, ao_field=None, ao_scale=0.03, ao_strength=1.0, refine_near=None, edge=None):
        """masks: [(name, mask)] or [(name, mask, [cut fields])]; refine_near: [(near(C) -> bool,
        max edge length)] applied before cutting (thin lines need small triangles). edge: an
        edge length; triangles on the region borders are split down to it first, so the borders
        come out as smooth curves."""
        V, T = self.V, self.T
        for near, L in (refine_near or []):
            V, T = refine(V, T, near, L, self.f)
        if edge:
            gs = [g for m in masks for g in (m[2] if len(m) > 2 else [m[1]])]
            if gs:
                near = lambda C: np.min(np.abs(np.stack([g(C) for g in gs])), axis=0) < edge * 0.75
                V, T = refine(V, T, near, edge, self.f, iters=2)
        for m in masks:
            cuts = m[2] if len(m) > 2 else [m[1]]
            for g in cuts:
                V, T = cut(V, T, g, self.f)
        N = normals(self.f, V)
        R = regions(V, T, [m[1] for m in masks])
        names = [m[0] for m in masks]
        A = ao(ao_field or self.f, V, N, ao_scale, strength=ao_strength)
        out = []
        for r, (pc, idx) in split_by_region(V, T, N, R).items():
            key = names[r] if r >= 0 else 'base'
            res = paint[key](pc.V, pc.N, A[idx])
            pc.color(res[0]); pc.part(res[1])
            if len(res) > 2 and res[2] is not None:
                pc.U = res[2](pc.V, pc.N)
            out.append(pc)
        return out


# ---------------------------------------------------------------- explicit primitives
def lathe(profile, n, R=None, t=(0, 0, 0), phase=0.0, close=True):
    """Surface of revolution about local Z. profile: [(radius, z)], radius 0 makes a pole.
    The faces look outward when the profile runs from -Z to +Z."""
    V = []; rings = []
    for (r, z) in profile:
        if r < 1e-9:
            rings.append([len(V)]); V.append((0.0, 0.0, z))
        else:
            ids = list(range(len(V), len(V) + n)); rings.append(ids)
            for i in range(n):
                a = 2 * PI * (i + phase) / n
                V.append((r * math.cos(a), r * math.sin(a), z))
    T = []
    for s in range(len(rings) - 1):
        A, B = rings[s], rings[s + 1]
        for i in range(n):
            i2 = (i + 1) % n
            if len(A) == 1 and len(B) == 1:
                continue
            if len(A) == 1:
                T.append((A[0], B[i], B[i2]))
            elif len(B) == 1:
                T.append((A[i], B[0], A[i2]))
            else:
                T += [(A[i], B[i], B[i2]), (A[i], B[i2], A[i2])]
    p = Piece(np.array(V), np.array(T)[:, ::-1])
    if R is not None or any(t):
        p.move(R, t)
    return p


def loft(rings, cap0=True, cap1=True):
    """Quads between consecutive closed rings (each m x 3, same m), capped with a centre fan.
    Ring points should run counter-clockwise seen from the end the loft heads toward."""
    rings = [np.asarray(r, float) for r in rings]
    m = len(rings[0]); V = np.concatenate(rings); T = []
    for s in range(len(rings) - 1):
        for i in range(m):
            a, b = s * m + i, s * m + (i + 1) % m
            c, d = (s + 1) * m + (i + 1) % m, (s + 1) * m + i
            T += [(a, b, c), (a, c, d)]
    V = list(V)
    if cap0:
        c0 = len(V); V.append(rings[0].mean(axis=0))
        T += [(c0, (i + 1) % m, i) for i in range(m)]
    if cap1:
        c1 = len(V); V.append(rings[-1].mean(axis=0)); o = (len(rings) - 1) * m
        T += [(c1, o + i, o + (i + 1) % m) for i in range(m)]
    return Piece(np.array(V), np.array(T))


def tube_mesh(path, radii, sides=6, cap0=True, cap1=True, up=(0, 0, 1)):
    """An explicit tapered tube along a polyline (thin limbs, antennae, stalks)."""
    path = np.asarray(path, float); n = len(path)
    radii = np.broadcast_to(np.asarray(radii, float), (n,))
    Tg = unit(np.gradient(path, axis=0))
    ref = np.asarray(up, float)
    rings = []; Ns = []
    Nprev = None
    for i in range(n):
        t = Tg[i]
        nv = (ref - t * np.dot(ref, t)) if Nprev is None else (Nprev - t * np.dot(Nprev, t))
        if np.linalg.norm(nv) < 1e-6:
            nv = np.cross(t, (1, 0, 0))
        nv = unit(nv); bv = np.cross(t, nv); Nprev = nv
        ang = 2 * PI * np.arange(sides) / sides
        d = np.cos(ang)[:, None] * nv + np.sin(ang)[:, None] * bv
        rings.append(path[i] + d * radii[i]); Ns.append(d)
    p = loft(rings, cap0, cap1)
    N = list(np.concatenate(Ns))
    if cap0: N.append(-Tg[0])
    if cap1: N.append(Tg[-1])
    p.N = unit(np.array(N))
    # loft orientation depends on the ring direction; make faces look along the normals
    fn = np.cross(p.V[p.T[:, 1]] - p.V[p.T[:, 0]], p.V[p.T[:, 2]] - p.V[p.T[:, 0]])
    if np.einsum('ij,ij->i', fn, p.N[p.T].mean(axis=1)).sum() < 0:
        p.T = p.T[:, ::-1]
    return p


def bead(center, outward, r, depth=0.6, n=10, rings=3, up=(0, 0, 1), uvreg=None, squash=1.0):
    """A domed bead (eye, nose): a half-ellipsoid of radius r bulging `depth * r` out along
    `outward` from `center`. uvreg (u0, v0, u1, v1) maps its face planar into the atlas."""
    prof = [(r * math.cos(a), r * depth * math.sin(a)) for a in np.linspace(0, PI / 2, rings + 1)]
    prof = [(r * 1.0, -r * 0.5)] + prof          # a short skirt sunk into the surface
    prof[-1] = (0.0, prof[-1][1])
    M = frame(outward, up)
    M[:, 1] *= squash
    p = lathe(prof, n)
    # analytic normals of the dome
    q = p.V.copy(); q[:, 2] /= depth
    p.N = unit(np.where(q[:, 2:3] < -1e-9, np.column_stack([q[:, 0], q[:, 1], np.zeros(len(q))]), q))
    if uvreg is not None:
        u0, v0, u1, v1 = uvreg
        p.U = np.column_stack([u0 + (u1 - u0) * (0.5 + 0.5 * p.V[:, 0] / r), v0 + (v1 - v0) * (0.5 + 0.5 * p.V[:, 1] / r)])
    p.V = p.V @ M.T + np.asarray(center, float)
    p.N = unit(p.N @ M.T)
    return p


def surface_point(f, start, direction, max_dist=1.0):
    """March from `start` along `direction` to the surface of f; returns (point, normal)."""
    d = unit(direction); p = np.asarray(start, float).copy()
    travelled = 0.0
    for _ in range(200):
        v = float(f(p[None])[0])
        if v < 1e-5:
            break
        p = p + d * v * 0.9; travelled += v * 0.9
        if travelled > max_dist:
            break
    p = project(f, p[None], iters=4)[0]
    return p, normals(f, p[None])[0]


# ---------------------------------------------------------------- Blender
def to_object(name, p, origin=(0, 0, 0)):
    """A Blender mesh object from a Piece (vertices relative to origin, object at origin)."""
    o_ = np.asarray(origin, float)
    me = bpy.data.meshes.new(name)
    V = p.V - o_
    me.from_pydata([tuple(map(float, v)) for v in V], [], [tuple(int(i) for i in t) for t in p.T])
    me.validate(clean_customdata=False)
    nl = len(me.loops)
    lv = np.zeros(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices([tuple(map(float, n)) for n in p.N])
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = 0
    col.data.foreach_set('color', np.clip(p.C[lv], 0, 1).astype(np.float32).ravel())
    uv0 = me.uv_layers.new(name='UVMap'); uv1 = me.uv_layers.new(name='Part')
    uv0.data.foreach_set('uv', p.U[lv].astype(np.float32).ravel())
    P2 = np.zeros((nl, 2), np.float32); P2[:, 0] = p.P[lv]
    uv1.data.foreach_set('uv', P2.ravel())
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = tuple(map(float, o_))
    return o
