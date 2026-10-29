# Geometry helpers for kit_plants.py (the stylized vegetation kit). Read docs/ART_DIRECTION.md.
#
# Every plant is built from Pieces: plain numpy meshes that carry one value per vertex for the
# position (V), a custom normal (N), a scene-linear RGBA colour (C, alpha = wind weight), an atlas
# UV (U) and a recolour part id (P), plus free per-vertex tags (A). Pieces are merged, culled
# (faces hidden inside other volumes are dropped) and turned into one Blender mesh by to_object(),
# which writes the kit_lib contract: colour attribute 'Col' (BYTE_COLOR, CORNER), UV0 the atlas,
# UV1.x the part, custom split normals.
import math
import numpy as np
import bpy, bmesh

WHITE_UV = (0.97, 0.03)
UP = np.array((0.0, 0.0, 1.0))


# ---------------------------------------------------------------- colour
def s2l(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hexc(h):
    """'#rrggbb' (sRGB) -> scene-linear RGB numpy array."""
    h = h.lstrip('#')
    return s2l(np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]))


class Ramp:
    """A three-stop shading ramp (dark, base, light), interpolated in sRGB so the steps look even.
    s = 0 deep shade, s = mid the base colour, s = 1 sunlit top."""
    def __init__(self, dark, base, light, mid=0.5):
        self.d, self.b, self.l = (np.array([int(h.lstrip('#')[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
                                  for h in (dark, base, light))
        self.mid = mid
        self.base = s2l(self.b)

    def __call__(self, s):
        s = np.clip(np.asarray(s, float), 0, 1)[..., None]
        lo = self.d + (self.b - self.d) * np.clip(s / self.mid, 0, 1)
        hi = self.b + (self.l - self.b) * np.clip((s - self.mid) / (1 - self.mid), 0, 1)
        return s2l(np.where(s < self.mid, lo, hi))


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def unit(a):
    a = np.asarray(a, float)
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.maximum(n, 1e-12)


# ---------------------------------------------------------------- pieces
def _newell(V, F):
    out = np.zeros((len(F), 3))
    for i, f in enumerate(F):
        p = V[list(f)]; q = np.roll(p, -1, axis=0)
        out[i, 0] = np.sum((p[:, 1] - q[:, 1]) * (p[:, 2] + q[:, 2]))
        out[i, 1] = np.sum((p[:, 2] - q[:, 2]) * (p[:, 0] + q[:, 0]))
        out[i, 2] = np.sum((p[:, 0] - q[:, 0]) * (p[:, 1] + q[:, 1]))
    return out          # length = 2 x area


def vnormals(V, F):
    """Area-weighted vertex normals."""
    fn = _newell(V, F)
    N = np.zeros_like(V)
    for f, n in zip(F, fn):
        N[list(f)] += n
    return unit(N)


class Piece:
    def __init__(self, V, F, N=None):
        self.V = np.asarray(V, float).reshape(-1, 3)
        self.F = [tuple(int(i) for i in f) for f in F]
        self.N = vnormals(self.V, self.F) if N is None else unit(np.asarray(N, float))
        n = len(self.V)
        self.C = np.ones((n, 4))
        self.U = np.tile(np.array(WHITE_UV), (n, 1))
        self.P = np.zeros(n)
        self.A = {}

    def __len__(self):
        return len(self.V)

    def tag(self, key, value):
        self.A[key] = np.broadcast_to(np.asarray(value, float), (len(self.V),)).copy()
        return self

    def color(self, rgb, alpha=None):
        rgb = np.asarray(rgb, float)
        self.C[:, :3] = np.broadcast_to(rgb, (len(self.V), 3)) if rgb.ndim == 1 else rgb
        if alpha is not None:
            self.C[:, 3] = alpha
        return self

    def part(self, p):
        self.P[:] = p
        return self

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def move(self, M):
        """Apply a 4x4 (numpy or mathutils) matrix to positions and normals."""
        M = np.array(M, float)
        self.V = self.V @ M[:3, :3].T + M[:3, 3]
        self.N = unit(self.N @ np.linalg.inv(M[:3, :3]))
        if np.linalg.det(M[:3, :3]) < 0:
            self.F = [tuple(reversed(f)) for f in self.F]
        return self


def merge(pieces):
    pieces = [p for p in pieces if p is not None and len(p)]
    out = Piece(np.zeros((0, 3)), [], N=np.zeros((0, 3)))
    keys = set()
    for p in pieces: keys |= set(p.A)
    off = 0
    Vs, Ns, Cs, Us, Ps, F = [], [], [], [], [], []
    A = {k: [] for k in keys}
    for p in pieces:
        Vs.append(p.V); Ns.append(p.N); Cs.append(p.C); Us.append(p.U); Ps.append(p.P)
        F += [tuple(i + off for i in f) for f in p.F]
        for k in keys:
            A[k].append(p.A.get(k, np.full(len(p.V), np.nan)))
        off += len(p.V)
    out.V = np.concatenate(Vs); out.N = np.concatenate(Ns); out.C = np.concatenate(Cs)
    out.U = np.concatenate(Us); out.P = np.concatenate(Ps); out.F = F
    out.A = {k: np.concatenate(v) for k, v in A.items()}
    return out


def compact(p, keep_faces):
    """Keep only the listed faces and the vertices they use."""
    F = [p.F[i] for i in keep_faces]
    used = sorted({i for f in F for i in f})
    remap = {o: n for n, o in enumerate(used)}
    idx = np.array(used, int) if used else np.zeros(0, int)
    q = Piece(p.V[idx], [tuple(remap[i] for i in f) for f in F], N=p.N[idx] if len(idx) else np.zeros((0, 3)))
    q.C = p.C[idx]; q.U = p.U[idx]; q.P = p.P[idx]
    q.A = {k: v[idx] for k, v in p.A.items()}
    return q


def cull(p, inside):
    """Drop faces whose vertices are all inside (inside: bool per vertex)."""
    inside = np.asarray(inside, bool)
    keep = [i for i, f in enumerate(p.F) if not all(inside[list(f)])]
    return compact(p, keep)


def orient(p, ref):
    """Flip faces whose normal points against ref(face centre, face index) -> outward vector
    (the vertex normals are recomputed if any face flips)."""
    fn = _newell(p.V, p.F)
    F = []; flipped = 0
    for i, (f, n) in enumerate(zip(p.F, fn)):
        c = p.V[list(f)].mean(axis=0)
        if np.dot(n, ref(c, i)) < 0:
            F.append(tuple(reversed(f))); flipped += 1
        else:
            F.append(f)
    p.F = F
    if flipped:
        p.N = vnormals(p.V, p.F)
    return p


# ---------------------------------------------------------------- Blender object
def to_object(name, p):
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(map(float, v))) for v in p.V]
    bm.verts.index_update()
    for f in p.F:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.shade_smooth()
    me.normals_split_custom_set_from_vertices([tuple(map(float, n)) for n in p.N])
    nl = len(me.loops)
    lv = np.zeros(nl, np.int64); me.loops.foreach_get('vertex_index', lv)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = col
    me.color_attributes.render_color_index = 0
    C = np.clip(p.C[lv], 0, 1)
    col.data.foreach_set('color', C.astype(np.float32).ravel())
    uv0 = me.uv_layers.new(name='UVMap'); uv1 = me.uv_layers.new(name='Part')
    uv0.data.foreach_set('uv', p.U[lv].astype(np.float32).ravel())
    P = np.zeros((nl, 2), np.float32); P[:, 0] = p.P[lv]
    uv1.data.foreach_set('uv', P.ravel())
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


# ---------------------------------------------------------------- curves and frames
def catmull(points, n):
    """n points along a centripetal-ish Catmull-Rom spline through the control points."""
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


def bezier(p0, p1, p2, n, p3=None):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(x, float) for x in (p0, p1, p2))
    if p3 is None:
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
    p3 = np.asarray(p3, float)
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def tangents(path):
    T = np.gradient(np.asarray(path, float), axis=0)
    return unit(T)


def transport(path, first=None):
    """Parallel-transport frames (N, B, T) along a polyline."""
    T = tangents(path)
    n = len(path)
    N = np.zeros((n, 3)); B = np.zeros((n, 3))
    ref = np.array(first, float) if first is not None else (np.array((1.0, 0, 0)) if abs(T[0][0]) < 0.9 else np.array((0, 1.0, 0)))
    N[0] = unit(ref - T[0] * np.dot(ref, T[0]))
    for i in range(1, n):
        v = N[i - 1] - T[i] * np.dot(N[i - 1], T[i])
        N[i] = unit(v)
    B = np.cross(T, N)
    return N, B, T


def arclen(path):
    d = np.linalg.norm(np.diff(path, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(d)])


# ---------------------------------------------------------------- primitives
def tube(path, radii, sides=8, twist=0.0, lobe=None, tip=False, first=None, uv=None, seam=True):
    """A tapered tube along path. radii: one per point. twist: radians of section rotation over
    the length (the bark texture follows it). lobe(i, angles) -> radius factor per vertex
    (root flares, lobed sections). tip: close the end into a point. uv: (u0, v0, u1, v1, v_of_s)
    maps around (u) and along (v_of_s(arc length, ring index) -> 0..1) into an atlas region.
    Tags: 's' (arc length from the start), 'ring' (ring index)."""
    path = np.asarray(path, float); n = len(path)
    radii = np.broadcast_to(np.asarray(radii, float), (n,))
    Nf, Bf, Tf = transport(path, first)
    L = arclen(path)
    cols = sides + 1 if seam else sides
    V, Nn, U, S, R = [], [], [], [], []
    last = n - 1 if tip else n
    for i in range(last):
        ang = 2 * math.pi * np.arange(cols) / sides + twist * L[i] / max(L[-1], 1e-6)
        f = lobe(i, ang) if lobe else np.ones(cols)
        d = np.cos(ang)[:, None] * Nf[i] + np.sin(ang)[:, None] * Bf[i]
        V.append(path[i] + d * (radii[i] * f)[:, None])
        Nn.append(d)
        S += [L[i]] * cols; R += [i] * cols
        if uv:
            u0, v0, u1, v1, vf = uv
            us = u0 + (u1 - u0) * (np.arange(cols) / sides)
            U.append(np.stack([us, np.full(cols, v0 + (v1 - v0) * vf(L[i], i))], axis=1))
    V = np.concatenate(V); Nn = np.concatenate(Nn)
    F = []
    for i in range(last - 1):
        for k in range(sides):
            a = i * cols + k; b = i * cols + (k + 1) % cols
            c = (i + 1) * cols + (k + 1) % cols; d = (i + 1) * cols + k
            F.append((a, b, c, d))
    if tip:
        apex = len(V)
        V = np.vstack([V, path[-1]]); Nn = np.vstack([Nn, Tf[-1]])
        S.append(L[-1]); R.append(n - 1)
        if uv:
            u0, v0, u1, v1, vf = uv
            U.append(np.array([[0.5 * (u0 + u1), v0 + (v1 - v0) * vf(L[-1], n - 1)]]))
        i = last - 1
        for k in range(sides):
            F.append((i * cols + k, i * cols + (k + 1) % cols, apex))
    p = Piece(V, F, N=Nn)
    # true normals (taper and lobes), with the seam columns sharing one normal
    G = vnormals(p.V, p.F)
    if seam:
        for i in range(last):
            a, b = i * cols, i * cols + sides
            g = unit(G[a] + G[b]); G[a] = G[b] = g
    p.N = G
    if uv: p.U = np.concatenate(U)
    p.tag('s', S); p.tag('ring', R)
    p.A['len'] = np.full(len(p.V), L[-1])
    return orient(p, lambda c, i: c - path[min(int(round(p.A['ring'][p.F[i][0]])), n - 1)])


def geodesic(freq):
    """Unit geodesic sphere: 20 * freq^2 triangles."""
    t = (1 + 5 ** 0.5) / 2
    base = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t),
                     (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
             (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5),
             (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    index = {}; V = []; F = []

    def vid(p):
        p = p / np.linalg.norm(p)
        k = tuple(np.round(p, 5))
        if k not in index:
            index[k] = len(V); V.append(p)
        return index[k]
    for a, b, c in faces:
        A, B, Cc = base[a], base[b], base[c]
        ids = {}
        for i in range(freq + 1):
            for j in range(freq + 1 - i):
                ids[(i, j)] = vid(A + (B - A) * i / freq + (Cc - A) * j / freq)
        for i in range(freq):
            for j in range(freq - i):
                F.append((ids[(i, j)], ids[(i + 1, j)], ids[(i, j + 1)]))
                if i + j < freq - 1:
                    F.append((ids[(i + 1, j)], ids[(i + 1, j + 1)], ids[(i, j + 1)]))
    V = np.array(V)
    F = [f if np.dot(np.cross(V[f[1]] - V[f[0]], V[f[2]] - V[f[0]]), V[list(f)].mean(0)) > 0 else f[::-1] for f in F]
    return V, F


def bump_field(D, rng, count, amp, size):
    """Radial bumps on unit directions D: count soft domes of angular radius size (radians)."""
    r = np.ones(len(D))
    cs = math.cos(size)
    dirs = unit(rng.normal(size=(count, 3)))
    for k in range(count):
        d = D @ dirs[k]
        g = np.clip((d - cs) / (1 - cs), 0, 1)
        r += amp * rng.uniform(0.6, 1.2) * (g * g * (3 - 2 * g))
    return r


def blob(center, radii, freq, rng, bumps=6, amp=0.14, size=0.75, flat=0.72, dent=0.0):
    """A soft lumpy foliage clump: a geodesic sphere pushed out by a few broad bumps, its underside
    flattened (flat < 1) like a cumulus cloud. Tag 'lz': the vertex's height on the clump (-1..1)."""
    D, F = geodesic(freq)
    r = bump_field(D, rng, bumps, amp, size)
    if dent:
        r -= dent * smoothstep(0.2, -0.8, D[:, 2])
    P = D * r[:, None]
    P[:, 2] = np.where(P[:, 2] < 0, P[:, 2] * flat, P[:, 2])
    V = np.asarray(center, float) + P * np.asarray(radii, float)
    p = Piece(V, F)
    p.tag('lz', D[:, 2])
    return p


def ellipsoid_e(V, center, radii, flat=1.0):
    """Normalised ellipsoid radius of points (1 on the surface), with a flattened underside."""
    q = (np.asarray(V, float) - center) / np.asarray(radii, float)
    q[:, 2] = np.where(q[:, 2] < 0, q[:, 2] / flat, q[:, 2])
    return np.linalg.norm(q, axis=1)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


def translate(t):
    M = np.eye(4); M[:3, 3] = t; return M


def frame_to(origin, z, x_hint=(1, 0, 0)):
    """4x4 matrix: local Z along z, local X toward x_hint, placed at origin."""
    z = unit(np.asarray(z, float)); x = np.asarray(x_hint, float)
    x = x - z * np.dot(x, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array((0, 1.0, 0)) - z * z[1]
    x = unit(x); y = np.cross(z, x)
    M = np.eye(4); M[:3, 0] = x; M[:3, 1] = y; M[:3, 2] = z; M[:3, 3] = origin
    return M
