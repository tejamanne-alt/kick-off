# The teens' bodies: the joint layout (shared with the armature), the body mesh and the teen
# proportions. Base space: see teen_lib.
#
# The body (and most of the clothes in teen_outfit) is modelled as a signed distance field:
# tapered capsules, ellipsoids and a lofted torso blended with smooth unions, so joints,
# armpits, the crotch and the neck flow into each other like a sculpt. The field is turned
# into a mesh with "surface nets" (an all-quad polygoniser), snapped onto the exact surface and
# decimated to the mobile budget.
#
# Everything here is designed in TEEN space (the proportions the player sees) and mapped back
# to base space with ungrow(), so teen.py's grow() lands it exactly where it was designed.
import bpy, math
import numpy as np
from mathutils import Vector
from teen_lib import C, new_obj, apply_mods, smooth

# ----------------------------------------------------------------------------------------------
# Proportions. Base space below Z0 is stretched by a constant factor; above Z0 it is only lifted
# (the head and hair keep their shape). The lift sets how many heads tall the teen is: the head
# (chin ~1.27 to crown ~1.59 base, about 0.32) over the whole height.
Z0 = 1.20


def lift(girl):
    return 0.49 if girl else 0.57      # girl ~6.5 heads, boy ~6.7 heads


def grow(co, girl):
    """Base space -> teen proportions: legs and torso stretched, the head only lifted."""
    L = lift(girl); x, y, z = co
    nz = z + L if z >= Z0 else z * (Z0 + L) / Z0
    return Vector((x, y, nz))


def ungrow(co, girl):
    """Teen space -> base space (the inverse of grow)."""
    L = lift(girl); x, y, z = co
    bz = z - L if z >= Z0 + L else z * Z0 / (Z0 + L)
    return Vector((x, y, bz))


def ungrow_np(V, girl):
    L = lift(girl); V = np.array(V, dtype=np.float64)
    z = V[:, 2]
    V[:, 2] = np.where(z >= Z0 + L, z - L, z * Z0 / (Z0 + L))
    return V


def grow_np(V, girl):
    L = lift(girl); V = np.array(V, dtype=np.float64)
    z = V[:, 2]
    V[:, 2] = np.where(z >= Z0, z + L, z * (Z0 + L) / Z0)
    return V


# ----------------------------------------------------------------------------------------------
# Joints in teen space: name -> (x, y, z). L/R are mirrored (+X is the character's left).
def tj(girl):
    L = lift(girl)
    if girl:
        j = dict(pelvis=(0, 0.006, 1.10), spine=(0, 0.002, 1.27), chest=(0, 0.004, 1.47),
                 neck0=(0, 0.012, 1.70), neck1=(0, 0.01, 1.30 + L), headtop=(0, 0.01, 1.60 + L))
        side = dict(hip=(0.084, 0.0, 1.075), knee=(0.088, -0.006, 0.575), ankle=(0.092, 0.02, 0.085),
                    toe=(0.096, -0.15, 0.03), shoulder=(0.152, 0.010, 1.638), elbow=(0.211, 0.024, 1.30),
                    wrist=(0.232, 0.006, 1.03), tip=(0.237, -0.004, 0.87))
    else:
        j = dict(pelvis=(0, 0.006, 1.135), spine=(0, 0.002, 1.32), chest=(0, 0.004, 1.52),
                 neck0=(0, 0.014, 1.765), neck1=(0, 0.01, 1.30 + L), headtop=(0, 0.01, 1.60 + L))
        side = dict(hip=(0.090, 0.0, 1.115), knee=(0.093, -0.006, 0.60), ankle=(0.097, 0.02, 0.09),
                    toe=(0.1, -0.17, 0.03), shoulder=(0.172, 0.010, 1.702), elbow=(0.232, 0.026, 1.36),
                    wrist=(0.25, 0.006, 1.075), tip=(0.252, -0.004, 0.90))
    for k, (x, y, z) in side.items():
        j[k + 'L'] = (x, y, z); j[k + 'R'] = (-x, y, z)
    return {k: np.array(v, dtype=np.float64) for k, v in j.items()}


def joints(girl):
    """Joint centres in BASE space: name -> (x, y, z)."""
    return {k: tuple(ungrow(Vector(v), girl)) for k, v in tj(girl).items()}


def bones(girl):
    """The armature (base space): (name, head, tail, parent). The game needs these names."""
    j = joints(girl)
    t = tj(girl)
    def B(p): return tuple(ungrow(Vector(p), girl))
    b = [('Hips', j['pelvis'], j['spine'], None), ('Spine', j['spine'], j['chest'], 'Hips'),
         ('Chest', j['chest'], j['neck0'], 'Spine'),
         ('Neck', j['neck0'], j['neck1'], 'Chest'), ('Head', j['neck1'], j['headtop'], 'Neck')]
    for n in 'LR':
        b += [('UpperLeg.' + n, j['hip' + n], j['knee' + n], 'Hips'),
              ('LowerLeg.' + n, j['knee' + n], j['ankle' + n], 'UpperLeg.' + n),
              ('Foot.' + n, j['ankle' + n], j['toe' + n], 'LowerLeg.' + n),
              ('UpperArm.' + n, j['shoulder' + n], j['elbow' + n], 'Chest'),
              ('LowerArm.' + n, j['elbow' + n], j['wrist' + n], 'UpperArm.' + n),
              ('Hand.' + n, j['wrist' + n], B(t['wrist' + n] * 0.45 + t['tip' + n] * 0.55), 'LowerArm.' + n)]
    return b


# ----------------------------------------------------------------------------------------------
# Signed distance fields (numpy; p is an (N, 3) array, negative inside).
def _a(v): return np.asarray(v, dtype=np.float64)


def smin(a, b, k):
    if k <= 0: return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def union(fs, k):
    def f(p):
        d = fs[0](p)
        for g in fs[1:]: d = smin(d, g(p), k)
        return d
    return f


def round_cone(a, b, ra, rb):
    """A capsule from a (radius ra) to b (radius rb), exact distance (Inigo Quilez)."""
    a = _a(a); b = _a(b); ba = b - a; l2 = ba @ ba; rr = ra - rb; a2 = l2 - rr * rr; il2 = 1.0 / l2
    def f(p):
        pa = p - a; y = pa @ ba; z = y - l2
        xv = pa * l2 - y[:, None] * ba; x2 = (xv * xv).sum(1)
        y2 = y * y * l2; z2 = z * z * l2; k = np.sign(rr) * rr * rr * x2
        d1 = np.sqrt(x2 + z2) * il2 - rb
        d2 = np.sqrt(x2 + y2) * il2 - ra
        d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - ra
        return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))
    return f


def chain(pts, radii, k):
    """Tapered capsules through several points, smoothly joined."""
    return union([round_cone(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)], k)


def frame(z_axis, y_hint=(0, 1, 0)):
    """3x3 matrix whose COLUMNS are a right-handed frame with its third axis along z_axis."""
    ez = _a(z_axis); ez = ez / np.linalg.norm(ez)
    ey = _a(y_hint); ey = ey - ez * (ey @ ez); ey /= np.linalg.norm(ey)
    ex = np.cross(ey, ez)
    return np.stack([ex, ey, ez], 1)


def ellipsoid(c, r, R=None):
    c = _a(c); r = _a(r)
    def f(p):
        q = p - c
        if R is not None: q = q @ R
        k0 = np.linalg.norm(q / r, axis=1); k1 = np.maximum(np.linalg.norm(q / (r * r), axis=1), 1e-9)
        return k0 * (k0 - 1.0) / k1
    return f


def rbox(c, half, rad, R=None):
    c = _a(c); half = _a(half)
    def f(p):
        q = p - c
        if R is not None: q = q @ R
        q = np.abs(q) - half + rad
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - rad
    return f


def catmull(keys, n=200):
    """Dense samples of a Catmull-Rom curve through the rows of keys (first column is the parameter)."""
    K = _a(keys); out = []
    P = np.vstack([K[0] * 2 - K[1], K, K[-1] * 2 - K[-2]])
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, max(2, n // len(K)), endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(K[-1])
    return np.array(out)


def loft(keys, zlo, zhi, kcap=0.02):
    """A torso-like solid: at height z an (super)ellipse of half-width w, half-depth d, centred at
    y = cy, exponent n. keys: rows (z, w, d, cy, n)."""
    T = catmull(keys, 400)
    zs = T[:, 0]
    def prof(z):
        return [np.interp(z, zs, T[:, i]) for i in range(1, 5)]
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        w, d, cy, n = prof(z)
        X = np.abs(x) / w; Y = np.abs(y - cy) / d
        q = (X ** n + Y ** n) ** (1.0 / n)
        g = np.sqrt((X / w) ** 2 + (Y / d) ** 2) + 1e-9
        dist = (q - 1.0) / np.maximum(g / np.maximum(q, 1e-6), 1e-6)
        dist = smax(dist, zlo - z, kcap)
        return smax(dist, z - zhi, kcap)
    f.prof = prof
    return f


# ----------------------------------------------------------------------------------------------
# Polygonising: surface nets (one vertex per surface cell, one quad per crossed grid edge).
def _grid_eval(f, lo, n, h, chunk=400000):
    xs = lo[0] + np.arange(n[0]) * h; ys = lo[1] + np.arange(n[1]) * h; zs = lo[2] + np.arange(n[2]) * h
    F = np.empty((n[0], n[1], n[2]))
    # evaluate slab by slab along z to limit memory
    per = max(1, chunk // (n[0] * n[1]))
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    for k0 in range(0, n[2], per):
        k1 = min(n[2], k0 + per); m = k1 - k0
        P = np.empty((n[0], n[1], m, 3))
        P[..., 0] = X[:, :, None]; P[..., 1] = Y[:, :, None]; P[..., 2] = zs[None, None, k0:k1]
        F[:, :, k0:k1] = f(P.reshape(-1, 3)).reshape(n[0], n[1], m)
    return F


def surface_nets(f, lo, hi, h):
    lo = _a(lo); hi = _a(hi)
    n = (np.ceil((hi - lo) / h) + 1).astype(int)
    F = _grid_eval(f, lo, n, h)
    F[F == 0] = 1e-9
    nx, ny, nz = n
    corners = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
    cedges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    cs = [F[i:nx - 1 + i, j:ny - 1 + j, k:nz - 1 + k] for (i, j, k) in corners]
    acc = np.zeros((nx - 1, ny - 1, nz - 1, 3)); cnt = np.zeros((nx - 1, ny - 1, nz - 1))
    for a, b in cedges:
        fa, fb = cs[a], cs[b]
        m = (fa < 0) != (fb < 0)
        t = np.where(m, fa / np.where(m, fa - fb, 1.0), 0.0)
        pa = _a(corners[a]); pb = _a(corners[b])
        for ax in range(3):
            acc[..., ax] += np.where(m, pa[ax] + t * (pb[ax] - pa[ax]), 0.0)
        cnt += m
    has = cnt > 0
    vid = -np.ones(cnt.shape, dtype=np.int64)
    vid[has] = np.arange(has.sum())
    ijk = np.argwhere(has)
    V = lo + (ijk + acc[has] / cnt[has][:, None]) * h
    quads = []
    def emit(m, sl, offs):
        I = np.argwhere(m)
        if not len(I): return
        I = I + _a(sl).astype(np.int64)
        cells = [vid[I[:, 0] + o[0], I[:, 1] + o[1], I[:, 2] + o[2]] for o in offs]
        q = np.stack(cells, 1)
        inside = F[I[:, 0], I[:, 1], I[:, 2]] < 0
        q[~inside] = q[~inside][:, ::-1]
        quads.append(q)
    emit((F[:-1, 1:-1, 1:-1] < 0) != (F[1:, 1:-1, 1:-1] < 0), (0, 1, 1), [(0, -1, -1), (0, 0, -1), (0, 0, 0), (0, -1, 0)])
    emit((F[1:-1, :-1, 1:-1] < 0) != (F[1:-1, 1:, 1:-1] < 0), (1, 0, 1), [(-1, 0, -1), (-1, 0, 0), (0, 0, 0), (0, 0, -1)])
    emit((F[1:-1, 1:-1, :-1] < 0) != (F[1:-1, 1:-1, 1:] < 0), (1, 1, 0), [(-1, -1, 0), (0, -1, 0), (0, 0, 0), (-1, 0, 0)])
    quads = np.concatenate(quads) if quads else np.zeros((0, 4), np.int64)
    return V, quads


def grad(f, V, e=1e-4):
    g = np.empty_like(V)
    for ax in range(3):
        d = np.zeros(3); d[ax] = e
        g[:, ax] = (f(V + d) - f(V - d)) / (2 * e)
    return g


def project(f, V, iters=4, maxstep=0.01):
    """Snap points onto the zero surface of f (Newton steps along the gradient)."""
    V = V.copy()
    for _ in range(iters):
        d = f(V); g = grad(f, V)
        s = (d / np.maximum((g * g).sum(1), 1e-9))[:, None] * g
        L = np.linalg.norm(s, axis=1)[:, None]
        V -= s * np.minimum(1.0, maxstep / np.maximum(L, 1e-12))
    return V


def relax(V, Q, f, iters=2, lam=0.5):
    """Even out the quads (Laplacian smoothing) and snap back onto the surface."""
    nv = len(V)
    E = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    E = np.concatenate([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=nv).astype(np.float64)
    for _ in range(iters):
        S = np.zeros_like(V)
        for ax in range(3): S[:, ax] = np.bincount(E[:, 0], weights=V[E[:, 1], ax], minlength=nv)
        avg = S / np.maximum(deg, 1)[:, None]
        V = V + lam * (avg - V)
        V = project(f, V, 2)
    return V


def sdf_object(name, f, lo, hi, h, tris=None, relax_iters=2, girl=None, symmetric=True, dense=None):
    """Mesh the field f inside the box lo..hi with cell size h (teen space), decimate to about
    `tris` triangles, then map to base space (if girl is not None). The normals are made
    outward and set from the field's analytic gradient (clean cel bands, no decimation noise).
    dense = (mask_fn(V) -> bool array, tris): a region (hems, necklines) kept denser, with its
    own budget on top of `tris`."""
    V, Q = surface_nets(f, lo, hi, h)
    V = project(f, V, 4, h)
    if relax_iters: V = relax(V, Q, f, relax_iters)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], Q.tolist())
    me.validate()
    o = new_obj(name, me)
    if tris and dense is not None:
        m = np.asarray(dense[0](V), dtype=bool)
        vg = o.vertex_groups.new(name='dense'); vg.add(np.nonzero(m)[0].tolist(), 1.0, 'REPLACE')
        vo = o.vertex_groups.new(name='rest'); vo.add(np.nonzero(~m)[0].tolist(), 1.0, 'REPLACE')
        inside = int(np.sum(m[Q].all(1))) * 2; cur = 2 * len(Q)
        def dec(ratio, group):
            dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = min(1.0, ratio)
            dm.vertex_group = group; dm.vertex_group_factor = 1.0
            if symmetric: dm.use_symmetry = True; dm.symmetry_axis = 'X'
            apply_mods(o)
        dec((tris * (1 - inside / cur) + inside) / cur, 'rest')
        cur = sum(len(p.vertices) - 2 for p in o.data.polygons)
        gi = o.vertex_groups['dense'].index
        w = np.zeros(len(o.data.vertices))
        for v in o.data.vertices:
            for g in v.groups:
                if g.group == gi: w[v.index] = g.weight
        inside = sum(len(p.vertices) - 2 for p in o.data.polygons if min(w[i] for i in p.vertices) >= 0.5)
        dec((cur - inside + dense[1]) / cur, 'dense')
        for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    elif tris:
        cur = 2 * len(Q)
        if cur > tris:
            dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = tris / cur
            if symmetric: dm.use_symmetry = True; dm.symmetry_axis = 'X'
    apply_mods(o)
    make_outward(o)
    N = field_normals(o, f)
    if girl is not None: to_base(o, girl)
    smooth(o)
    set_normals(o, N, girl)
    return o


def make_outward(o):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data)
    if bm.calc_volume(signed=True) < 0:
        for fc in bm.faces: fc.normal_flip()
        bm.to_mesh(o.data); o.data.update()
    bm.free()


def field_normals(o, f):
    """Unit gradients of f at the mesh's (teen-space) vertices."""
    me = o.data
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    g = grad(f, V)
    return g / np.maximum(np.linalg.norm(g, axis=1), 1e-12)[:, None]


def set_normals(o, N, girl=None):
    """Set per-vertex custom normals N (teen space). If the mesh has been mapped to base space
    (girl given), the normals are mapped too (z scaled by the inverse of ungrow's stretch), so
    after teen.py's grow() they are the teen-space normals again."""
    me = o.data
    N = np.array(N, dtype=np.float64)
    if girl is not None:
        V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
        L = lift(girl)
        k = np.where(V[:, 2] >= Z0, 1.0, (Z0 + L) / Z0)
        N[:, 2] *= k
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    me.normals_split_custom_set_from_vertices(N.tolist())
    me.update()


def to_base(o, girl):
    me = o.data
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V)
    V = ungrow_np(V.reshape(-1, 3), girl)
    me.vertices.foreach_set('co', V.ravel()); me.update()


def mesh_object(name, verts, faces, girl=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate()
    o = new_obj(name, me)
    if girl is not None: to_base(o, girl)
    smooth(o)
    return o


# ----------------------------------------------------------------------------------------------
# The body field, in pieces the clothes reuse.
class BodyField:
    def __init__(self, girl):
        self.girl = girl
        j = self.j = tj(girl)
        if girl:
            # side profile: a gentle S (lumbar hollow at 1.27, chest a touch forward, upper back rounded)
            keys = [(1.035, 0.075, 0.060, 0.012, 2.0), (1.08, 0.132, 0.086, 0.012, 2.0),
                    (1.13, 0.138, 0.089, 0.012, 2.0), (1.20, 0.123, 0.081, 0.006, 2.0),
                    (1.27, 0.104, 0.069, -0.001, 2.1), (1.35, 0.108, 0.075, -0.004, 2.2),
                    (1.43, 0.112, 0.086, -0.011, 2.2), (1.51, 0.113, 0.0865, -0.0065, 2.2),
                    (1.58, 0.118, 0.0795, 0.0045, 2.2), (1.615, 0.134, 0.0725, 0.0075, 2.3),
                    (1.645, 0.140, 0.063, 0.009, 2.4), (1.672, 0.112, 0.055, 0.012, 2.1),
                    (1.695, 0.076, 0.049, 0.014, 2.0), (1.715, 0.052, 0.046, 0.015, 2.0)]
            self.torso_core = loft(keys, 1.03, 1.72, 0.02)
            self.r = dict(neck=(0.046, 0.041), uarm=(0.038, 0.031), farm=(0.033, 0.031, 0.022),
                          thigh=(0.071, 0.060, 0.046), shin=(0.045, 0.026), calf=(0.046, 0.044, 0.11),
                          delt=(0.042, 0.044, 0.055))
            self.hand_scale = 1.08
        else:
            keys = [(1.07, 0.075, 0.062, 0.012, 2.0), (1.12, 0.127, 0.089, 0.012, 2.0),
                    (1.18, 0.133, 0.090, 0.010, 2.0), (1.26, 0.129, 0.081, 0.000, 2.1),
                    (1.34, 0.125, 0.0795, -0.0025, 2.2), (1.43, 0.128, 0.090, -0.007, 2.2),
                    (1.52, 0.131, 0.0975, -0.0115, 2.2), (1.60, 0.138, 0.0955, -0.0045, 2.3),
                    (1.65, 0.152, 0.084, 0.005, 2.4), (1.70, 0.13, 0.069, 0.010, 2.2),
                    (1.735, 0.088, 0.058, 0.014, 2.0), (1.765, 0.064, 0.053, 0.016, 2.0), (1.78, 0.06, 0.052, 0.016, 2.0)]
            self.torso_core = loft(keys, 1.065, 1.78, 0.03)
            self.r = dict(neck=(0.053, 0.047), uarm=(0.049, 0.038), farm=(0.04, 0.037, 0.026),
                          thigh=(0.077, 0.067, 0.051), shin=(0.051, 0.029), calf=(0.053, 0.050, 0.12),
                          delt=(0.043, 0.045, 0.054))
            self.hand_scale = 1.16
        self.keys = keys
        r = self.r
        # buttocks: two soft ellipsoids behind the hip joints
        hz = j['hipL'][2]
        glutes = [ellipsoid((s * 0.052, 0.040, hz + 0.005), (0.068, 0.058, 0.075)) for s in (1, -1)]
        tc = self.torso_core
        if girl:
            self.torso = lambda p: smin(smin(tc(p), glutes[0](p), 0.03), glutes[1](p), 0.03)
        else:
            # the trapezius: one sloping line from the neck out to the shoulder (no dip before
            # the shoulder ball)
            n0 = j['neck0']
            traps = [round_cone((s * 0.045, n0[1] + 0.006, n0[2] - 0.012), (s * 0.15, n0[1], n0[2] - 0.045), 0.03, 0.03)
                     for s in (1, -1)]
            def torso(p):
                d = smin(smin(tc(p), glutes[0](p), 0.03), glutes[1](p), 0.03)
                return smin(d, np.minimum(traps[0](p), traps[1](p)), 0.035)
            self.torso = torso
        n0 = j['neck0']; n1 = j['neck1']
        self.neck = round_cone(n0 + (0, 0.003, -0.04), n1 + (0, 0.012, 0.01), r['neck'][0], r['neck'][1])
        self.hand = {}; self.foot = {}; self.uarm = {}; self.farm = {}
        self.thigh = {}; self.shin = {}
        for n, s in (('L', 1), ('R', -1)):
            sh, el, wr, tip = j['shoulder' + n], j['elbow' + n], j['wrist' + n], j['tip' + n]
            adir = (el - sh) / np.linalg.norm(el - sh)
            delt = ellipsoid(sh + adir * 0.03 + (-s * 0.006, -0.002, 0.004), r['delt'], frame(adir))
            ua = round_cone(sh, el, r['uarm'][0], r['uarm'][1])
            mid = el + (wr - el) * 0.3
            fa = chain([el, mid, wr], r['farm'], 0.0)
            self.uarm[n] = lambda p, ua=ua, delt=delt: smin(ua(p), delt(p), 0.02)
            self.farm[n] = fa
            self.hand[n] = self._hand(wr, tip, s)
            hp, kn, an = j['hip' + n], j['knee' + n], j['ankle' + n]
            midt = hp + (kn - hp) * 0.5 + (0, -0.004, 0)
            th = chain([hp, midt, kn], r['thigh'], 0.0)
            sn = round_cone(kn, an, r['shin'][0], r['shin'][1])
            # the calf sits behind the shin bone, a little to the inside; the knee keeps a
            # rounded cap so a bent knee does not pinch to a point
            calf = ellipsoid(kn + (an - kn) * 0.33 + (-s * 0.004, 0.024, 0), r['calf'])
            kcap = ellipsoid(kn + (0, -0.027, 0.012), (0.031, 0.021, 0.036) if girl else (0.035, 0.024, 0.041))
            self.thigh[n] = th
            self.shin[n] = lambda p, sn=sn, calf=calf, kcap=kcap: smin(smin(sn(p), calf(p), 0.035), kcap(p), 0.02)
            fs = 1.0 if girl else 1.08
            ft = ellipsoid((an[0] + s * 0.001, -0.03 * fs, 0.04), (0.03 * fs, 0.085 * fs, 0.026))
            heel = ellipsoid((an[0], 0.028, 0.048), (0.028, 0.034, 0.036))
            self.foot[n] = lambda p, ft=ft, heel=heel: smin(ft(p), heel(p), 0.03)

    def _hand(self, wr, tip, s):
        """A mitten with a thumb. Palm faces the thigh (-s*X), thumb forward (-Y)."""
        k = self.hand_scale
        d = (tip - wr) / np.linalg.norm(tip - wr)
        R = frame(d, (0, 1, 0))           # columns: ex (~ +X side), ey (~ +Y, back), ez (along the hand)
        ex, ey, ez = R[:, 0], R[:, 1], R[:, 2]
        palm = ellipsoid(wr + ez * 0.048 * k + ex * (-s * 0.002 * k), (0.0185 * k, 0.037 * k, 0.05 * k), R)
        R2 = frame(d + ex * (-s * 0.2), (0, 1, 0))
        fing = ellipsoid(wr + ez * 0.105 * k + ex * (-s * 0.006 * k) + ey * (0.002 * k), (0.0155 * k, 0.035 * k, 0.05 * k), R2)
        t0 = wr + ez * 0.032 * k + ex * (-s * 0.008 * k) + ey * (-0.024 * k)
        tdir = ez * 0.86 + ey * (-0.40) + ex * (-s * 0.32); tdir /= np.linalg.norm(tdir)
        thumb = round_cone(t0, t0 + tdir * 0.046 * k, 0.0150 * k, 0.0118 * k)
        return lambda p: smin(smin(palm(p), fing(p), 0.03 * k), thumb(p), 0.012 * k)

    def arm_full(self, n):
        return lambda p: smin(np.minimum(self.uarm[n](p), self.farm[n](p)), self.hand[n](p), 0.012)

    def leg_full(self, n):
        return lambda p: smin(np.minimum(self.thigh[n](p), self.shin[n](p)), self.foot[n](p), 0.03)

    def __call__(self, p):
        d = smin(self.torso(p), self.neck(p), 0.035)
        for n in 'LR':
            d = smin(d, self.arm_full(n)(p), 0.045)
            d = smin(d, self.leg_full(n)(p), 0.06)
        return d


_FIELDS = {}
BODY_TRIS = {True: (5850, 560, 780), False: (5850, 560, 200)}
NECK_TRIS = {True: 520, False: 520}


def field(girl):
    if girl not in _FIELDS: _FIELDS[girl] = BodyField(girl)
    return _FIELDS[girl]


def build_body(girl):
    """The skin: one smooth closed mesh (teen-space field, mapped to base space). Skin the
    clothes hide is tucked in a little (so it never pokes through) and thinned out hard, to
    spend the triangles where they show."""
    import teen_outfit
    f = field(girl)
    top = tj(girl)['neck1'][2] + 0.09
    V, Q = surface_nets(f, (-0.30, -0.22, -0.01), (0.30, 0.17, top), 0.0062)
    V = project(f, V, 4, 0.0062)
    V = relax(V, Q, f, 2)
    depth, semi, sockd = teen_outfit.cover(girl)(V)
    g = grad(f, V); g /= np.maximum(np.linalg.norm(g, axis=1), 1e-9)[:, None]
    V = V - g * np.clip(np.maximum(depth - 0.0035, (sockd > 0) * (sockd + 0.001)), 0, 0.007)[:, None]
    me = bpy.data.meshes.new('Body'); me.from_pydata(V.tolist(), [], Q.tolist()); me.validate()
    body = new_obj('Body', me)
    def group(name, w):
        vg = body.vertex_groups.new(name=name); w = np.round(w, 2)
        for val in np.unique(w):
            idx = np.nonzero(w == val)[0].tolist()
            if idx: vg.add(idx, float(val), 'REPLACE')
    hidden = np.clip((depth - 0.006) / 0.004, 0, 1)
    group('hidden', hidden); group('semi', semi * (hidden < 0.5) * 1.0)
    # the neck shows big in the face close-ups: it gets its own, denser budget
    jj = tj(girl); nz0, nz1 = jj['neck0'][2] - 0.035, jj['neck1'][2] + 0.03
    rr = np.hypot(V[:, 0], V[:, 1] - jj['neck0'][1])
    neck = ((V[:, 2] > nz0) & (V[:, 2] < nz1) & (rr < 0.085) & (hidden < 0.5)) * 1.0
    group('neck', neck); group('notneck', 1.0 - neck)
    # Triangle budget: a uniform pass, then the hidden skin and the covered-at-rest skin
    # (thighs in the skirt, legs in the socks) are thinned out to their own small budgets.
    stage1, hid_budget, semi_budget = BODY_TRIS[girl]
    def dec(ratio, vg=None):
        d = body.modifiers.new('dec', 'DECIMATE'); d.ratio = min(1.0, ratio); d.use_symmetry = True; d.symmetry_axis = 'X'
        if vg: d.vertex_group = vg; d.vertex_group_factor = 1.0
        apply_mods(body)
    def count(vg):
        gi = body.vertex_groups[vg].index
        w = np.zeros(len(body.data.vertices))
        for v in body.data.vertices:
            for gg in v.groups:
                if gg.group == gi: w[v.index] = gg.weight
        tot = 0; inside = 0
        for p in body.data.polygons:
            t = len(p.vertices) - 2; tot += t
            if min(w[i] for i in p.vertices) >= 0.5: inside += t
        return tot, inside
    tot, inside = count('neck')
    dec((stage1 * (1 - inside / tot) + inside) / tot, 'notneck')     # everything but the neck
    tot, inside = count('neck')
    dec((tot - inside + NECK_TRIS[girl]) / tot, 'neck')              # then the neck, to its budget
    tot, inside = count('hidden'); dec((tot - inside + hid_budget) / tot, 'hidden')
    tot, inside = count('semi'); dec((tot - inside + semi_budget) / tot, 'semi')
    for g in ('semi', 'hidden', 'neck', 'notneck'): body.vertex_groups.remove(body.vertex_groups[g])
    make_outward(body)
    N = field_normals(body, f)
    to_base(body, girl); smooth(body)
    set_normals(body, N, girl)
    return body
