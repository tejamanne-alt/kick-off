# Geometry, shading and export helpers for kit_leisure.py (the LEISURE kit). Read
# docs/ART_DIRECTION.md and kit_lib.py first.
#
# A model is a Model: named groups of bmesh pieces (the root mesh is group '', children are other
# groups with their own origin), Attach.* points, a palette and the settings for its painted wear.
# Every piece carries, per face, a material id ('mat': part, colour key, uv mode, AO strength) and
# an atlas tile id ('reg'), per face corner a tile-local UV ('uv', 0..1 inside the tile), and per
# vertex an optional custom normal ('cn', zero = use the weighted normal) and own colour ('vc',
# used by colour key '@', e.g. foliage ramps).
#
# realize() turns a Model into Blender objects: triangulated, weighted normals with crisp edges
# above SHARP degrees, soft shading baked into the vertex colours (ray-cast ambient occlusion with
# the ground as an occluder, darker low down, a little lighter on top, crevices tinted lilac), atlas
# UVs (tile UVs, or the model's projected wear maps for 'grime' faces, or the white corner) and the
# recolour part in UV2.x.
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import kit_lib as K

PI = math.pi
C = bpy.context
SHARP = 62.0                     # edges sharper than this (degrees) keep a hard normal

# ---------------------------------------------------------------- palette (sRGB) and materials
DEF_PAL = {
    'paint': (0.95, 0.93, 0.88), 'accent': (0.80, 0.33, 0.27), 'third': (0.42, 0.62, 0.70),
    'wood': (0.74, 0.57, 0.40), 'woodd': (0.52, 0.38, 0.28), 'woodl': (0.86, 0.73, 0.55),
    'metal': (0.58, 0.60, 0.63), 'dark': (0.22, 0.23, 0.26), 'rope': (0.86, 0.77, 0.58),
    'stone': (0.74, 0.71, 0.74), 'white': (1.0, 1.0, 1.0), 'cream': (0.96, 0.92, 0.83),
    'red': (0.84, 0.30, 0.25), 'yellow': (0.98, 0.80, 0.33), 'sand': (0.93, 0.83, 0.64),
    'glow': (1.0, 0.93, 0.74), 'rubber': (0.24, 0.24, 0.26), 'conc': (0.80, 0.78, 0.74),
    'teal': (0.38, 0.62, 0.62), 'blue': (0.40, 0.60, 0.80), 'green': (0.45, 0.62, 0.36),
    'brass': (0.82, 0.68, 0.40), 'water': (0.40, 0.72, 0.74), 'mud': (0.56, 0.47, 0.38),
}

SHORT = {
    # name: (part, colour key, uv mode)    uv: 'grime' (projected wear maps), 'keep' (tile), 'white'
    'paint': (1, 'paint', 'grime'), 'paintc': (1, 'paint', 'white'), 'paintk': (1, 'paint', 'keep'),
    'accent': (2, 'accent', 'grime'), 'accentc': (2, 'accent', 'white'), 'accentk': (2, 'accent', 'keep'),
    'third': (3, 'third', 'grime'), 'thirdc': (3, 'third', 'white'), 'thirdk': (3, 'third', 'keep'),
    'wood': (0, 'wood', 'keep'), 'woodd': (0, 'woodd', 'keep'), 'woodl': (0, 'woodl', 'keep'),
    'metal': (0, 'metal', 'grime'), 'metalc': (0, 'metal', 'white'), 'dark': (0, 'dark', 'white'),
    'darkg': (0, 'dark', 'grime'), 'rope': (0, 'rope', 'keep'), 'stone': (0, 'stone', 'keep'),
    'stoneg': (0, 'stone', 'grime'), 'white': (0, 'white', 'white'), 'cream': (0, 'cream', 'grime'),
    'creamc': (0, 'cream', 'white'), 'red': (0, 'red', 'white'), 'yellow': (0, 'yellow', 'white'),
    'tex': (0, 'white', 'keep'), 'sand': (0, 'sand', 'keep'), 'conc': (0, 'conc', 'grime'),
    'rubber': (0, 'rubber', 'white'), 'brass': (0, 'brass', 'white'), 'teal': (0, 'teal', 'white'),
    'blue': (0, 'blue', 'white'), 'green': (0, 'green', 'white'), 'mud': (0, 'mud', 'white'),
    'own0': (0, '@', 'white'), 'own1': (1, '@', 'white'), 'own2': (2, '@', 'white'),
    'own0k': (0, '@', 'keep'), 'own1k': (1, '@', 'keep'), 'own2k': (2, '@', 'keep'),
}
MT = []          # material table: (part, key, uv, ao)
_MI = {}


def mt(m, ao=1.0):
    """A material id: a SHORT name, or a (part, key, uv[, ao]) tuple."""
    if isinstance(m, int): return m
    if isinstance(m, str):
        p, k, u = SHORT[m]; a = 0.0 if k == 'glow' else ao
    else:
        p, k, u = m[:3]; a = m[3] if len(m) > 3 else ao
    key = (p, k, u, a)
    if key not in _MI:
        _MI[key] = len(MT); MT.append(key)
    return _MI[key]


# Atlas tiles (pixel sizes; positions are packed by kit_leisure_atlas.layout).
TILES = [('grain', 256, 128), ('pgrain', 256, 128), ('bark', 192, 256), ('stone', 128, 128),
         ('canvas', 128, 128), ('rope', 64, 128), ('grate', 256, 256), ('water', 256, 256),
         ('shingle', 256, 256), ('sand', 128, 128), ('target', 192, 192), ('flag', 128, 96),
         ('mat', 256, 256), ('window', 128, 96), ('glow', 64, 128), ('lily', 96, 96), ('chain', 32, 128),
         ('bricks', 128, 128), ('terry', 128, 128), ('bucket', 128, 64), ('slats', 128, 128)]
TILE = {n: i for i, (n, w, h) in enumerate(TILES)}


def s2l(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


def smooth01(t):
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)


def sstep(e0, e1, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class Ramp:
    """Three-stop shading ramp (dark, base, light) in sRGB; s = 0.5 is the base colour."""
    def __init__(self, dark, base, light):
        self.d, self.b, self.l = (np.array(c, float) for c in (dark, base, light))
        self.base = s2l(self.b)

    def __call__(self, s):
        s = np.clip(np.asarray(s, float), 0, 1)[..., None]
        lo = self.d + (self.b - self.d) * np.clip(s / 0.5, 0, 1)
        hi = self.b + (self.l - self.b) * np.clip((s - 0.5) / 0.5, 0, 1)
        c = np.where(s < 0.5, lo, hi)
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------- bmesh pieces
def new_bm():
    bm = bmesh.new()
    bm.faces.layers.int.new('mat'); bm.faces.layers.int.new('reg')
    bm.loops.layers.uv.new('uv')
    bm.verts.layers.float_vector.new('cn'); bm.verts.layers.float_vector.new('vc')
    return bm


def lay(bm):
    f = bm.faces.layers.int; v = bm.verts.layers.float_vector
    return f['mat'], f['reg'], bm.loops.layers.uv['uv'], v['cn'], v['vc']


def bm_from(V, F, m):
    """Faces F over vertices V; m: one material (any mt() form) or one per face."""
    bm = new_bm(); lm = lay(bm)[0]
    vs = [bm.verts.new(tuple(map(float, v))) for v in V]
    out = []
    many = isinstance(m, list)
    mm = None if many else mt(m)
    for i, f in enumerate(F):
        try:
            face = bm.faces.new([vs[j] for j in f])
        except ValueError:
            out.append(None); continue
        face[lm] = mt(m[i]) if many else mm
        out.append(face)
    bm.normal_update()
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return bm, out


def merge(dst, src):
    a = lay(dst); b = lay(src)
    vmap = {}
    for v in src.verts:
        nv = dst.verts.new(v.co); nv[a[3]] = v[b[3]]; nv[a[4]] = v[b[4]]; vmap[v] = nv
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[a[0]] = f[b[0]]; nf[a[1]] = f[b[1]]
        for x, y in zip(f.loops, nf.loops): y[a[2]].uv = x[b[2]].uv
    return dst


def join(*bms):
    out = new_bm()
    for b in bms:
        if b is not None: merge(out, b)
    out.normal_update()
    out.verts.ensure_lookup_table(); out.faces.ensure_lookup_table()
    return out


def copy(bm):
    return join(bm)


def xform(bm, M):
    M = Matrix(M)
    if len(M) == 3: M = M.to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    R = M.to_3x3().inverted_safe().transposed()
    lc = lay(bm)[3]
    for v in bm.verts:
        n = Vector(v[lc])
        if n.length > 1e-6: v[lc] = (R @ n).normalized()
    if M.to_3x3().determinant() < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def setmat(bm, m, faces=None):
    lm = lay(bm)[0]; i = mt(m)
    for f in (bm.faces if faces is None else faces):
        if f is not None: f[lm] = i
    return bm


def set_vc(bm, fn):
    """Own vertex colours (linear RGB) from fn(co) (used by colour key '@')."""
    lv = lay(bm)[4]
    for v in bm.verts: v[lv] = tuple(fn(v.co))
    return bm


def flip(bm):
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.normal_update()
    bm.faces.ensure_lookup_table(); return bm


def recalc(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update()
    bm.faces.ensure_lookup_table(); return bm


def T(x, y=0.0, z=0.0):
    if not isinstance(x, (int, float)): x, y, z = x
    return Matrix.Translation((x, y, z))


def R(a, axis):
    return Matrix.Rotation(a, 4, axis)


def S(x, y=None, z=None):
    if y is None: y = z = x
    return Matrix.Diagonal((x, y, z, 1.0))


def frame(origin, z, up=(0, 0, 1)):
    """Matrix at origin whose local Z is z and local Y leans toward up."""
    z = Vector(z).normalized(); up = Vector(up)
    x = up.cross(z)
    if x.length < 1e-6: x = Vector((1, 0, 0)).cross(z)
    if x.length < 1e-6: x = Vector((0, 1, 0)).cross(z)
    x.normalize(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin)
    return M


# ---------------------------------------------------------------- primitives
def _lines(a0, a1, r, seg, extra):
    cs = {round(a0, 6), round(a1, 6)}
    for o in {0: [], 1: [1.0], 2: [1.0, 0.586], 3: [1.0, 0.732, 0.423]}[seg]:
        cs.add(round(a0 + r * o, 6)); cs.add(round(a1 - r * o, 6))
    for e in extra:
        if a0 + 1e-4 < e < a1 - 1e-4: cs.add(round(e, 6))
    return sorted(cs)


def rbox(lo, hi, r, seg=(1, 1, 1), extra=((), (), ()), skip=()):
    """A rounded box on an explicit grid (see car.py): the grid of axis lines projected onto a box
    with elliptical edges of radii r. Returns (X positions, faces, tags (axis, sign), centres)."""
    lo = np.array(lo, float); hi = np.array(hi, float)
    r = np.minimum(np.maximum(np.array(r, float) * np.ones(3), 1e-4), (hi - lo) / 2 - 1e-5)
    ax = [_lines(lo[i], hi[i], r[i], seg[i], extra[i]) for i in range(3)]
    index = {}; P = []; F = []; Tg = []

    def vid(p):
        k = tuple(round(c, 6) for c in p)
        i = index.get(k)
        if i is None: i = index[k] = len(P); P.append(k)
        return i
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        for s in (-1, 1):
            if (a, s) in skip: continue
            val = hi[a] if s > 0 else lo[a]
            B, Cc = ax[b], ax[c]
            for j in range(len(B) - 1):
                for k in range(len(Cc) - 1):
                    q = []
                    for jj, kk in ((j, k), (j + 1, k), (j + 1, k + 1), (j, k + 1)):
                        p = [0.0, 0.0, 0.0]; p[a] = val; p[b] = B[jj]; p[c] = Cc[kk]
                        q.append(vid(p))
                    if s < 0: q.reverse()
                    F.append(q); Tg.append((a, s))
    P = np.array(P)
    ctr = (lo + hi) / 2; h = (hi - lo) / 2
    Q = P - ctr; inner = np.maximum(h - r, 0)
    qq = np.clip(Q, -inner, inner)
    d = (Q - qq) / r
    n = np.linalg.norm(d, axis=1, keepdims=True); n[n < 1e-9] = 1
    X = ctr + qq + r * d / n
    Pc = np.array([P[f].mean(axis=0) for f in F])
    return X, F, Tg, Pc


def rpiece(lo, hi, r, m, seg=(1, 1, 1), extra=((), (), ()), skip=(), deform=None, mats=None):
    """A rounded box piece. mats: optional fn(axis, sign, centre) -> material per face."""
    X, F, Tg, Pc = rbox(lo, hi, r, seg, extra, skip)
    if deform is not None: X = deform(X)
    ms = [mats(a, s, c) for (a, s), c in zip(Tg, Pc)] if mats else m
    bm, _ = bm_from(X, F, ms)
    return bm


def box(lo, hi, m):
    """A plain box (12 triangles)."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return bm_from(V, F, m)[0]


def cbox(size, r, m, seg=1):
    """A chamfered box (full size) centred on the origin."""
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    r = min(r, min(size) * 0.45)
    if r > 1e-5:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    setmat(bm, m)
    return recalc(bm)


def lathe(prof, n, m, phase=0.5, close_top=True):
    """Surface of revolution about Z. prof: (radius, height[, 'S']) from bottom to top ('S' splits
    the smoothing there). m: one material or one per profile segment. Loop UVs: u around (0..1),
    v the arc length along the profile (metres). Returns (bm, [(face, segment, i)])."""
    pts = [(p[0], p[1]) for p in prof]
    split = [len(p) > 2 and p[2] == 'S' for p in prof]
    arc = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    V = []; ring_s = []; ring_e = []

    def ring(r, h):
        if r < 1e-7:
            V.append((0.0, 0.0, h)); return [len(V) - 1]
        ids = list(range(len(V), len(V) + n))
        for i in range(n):
            a = 2 * PI * (i + phase) / n
            V.append((r * math.cos(a), r * math.sin(a), h))
        return ids
    for k, (r, h) in enumerate(pts):
        rg = ring(r, h)
        ring_e.append(rg)
        ring_s.append(ring(r, h) if split[k] else rg)
    F = []; M = []; tags = []; UV = []
    many = isinstance(m, (list, tuple)) and not (len(m) in (3, 4) and isinstance(m[0], int))
    for si in range(len(pts) - 1):
        A, B = ring_s[si], ring_e[si + 1]
        if len(A) == 1 and len(B) == 1: continue
        for i in range(n):
            i2 = (i + 1) % n
            u0, u1 = i / n, (i + 1) / n
            if len(A) == 1:
                f = [A[0], B[i2], B[i]]; uv = [((u0 + u1) / 2, arc[si]), (u1, arc[si + 1]), (u0, arc[si + 1])]
            elif len(B) == 1:
                f = [A[i], A[i2], B[0]]; uv = [(u0, arc[si]), (u1, arc[si]), ((u0 + u1) / 2, arc[si + 1])]
            else:
                f = [A[i], A[i2], B[i2], B[i]]; uv = [(u0, arc[si]), (u1, arc[si]), (u1, arc[si + 1]), (u0, arc[si + 1])]
            F.append(f); M.append(m[si] if many else m); tags.append((si, i)); UV.append(uv)
    bm, faces = bm_from(V, F, M)
    lu = lay(bm)[2]
    out = []
    for f, t, uv in zip(faces, tags, UV):
        if f is None: continue
        for l, c in zip(f.loops, uv): l[lu].uv = c
        out.append((f, t[0], t[1]))
    return bm, out


def sweep(path, up, section, m, caps=True, scales=None, closed_path=False, closed_sec=True):
    """Rings of a 2D section (u along the normal, v along the binormal) along a polyline.
    up: a vector or fn(i, point, tangent). Loop UVs: u the arc length along the path (metres),
    v around the section (0..1)."""
    path = [Vector(p) for p in path]
    n = len(path); msec = len(section); V = []
    for i, p in enumerate(path):
        if closed_path:
            t = path[(i + 1) % n] - path[i - 1]
        elif i == 0: t = path[1] - p
        elif i == n - 1: t = p - path[-2]
        else: t = path[i + 1] - path[i - 1]
        t.normalize()
        u = Vector(up(i, p, t) if callable(up) else up)
        N = (u - t * u.dot(t))
        if N.length < 1e-6: N = t.orthogonal()
        N.normalize(); Bv = t.cross(N)
        sc = scales[i] if scales is not None else 1.0
        for (a, b) in section: V.append(p + N * (a * sc) + Bv * (b * sc))
    L = [0.0]
    for i in range(1, n): L.append(L[-1] + (path[i] - path[i - 1]).length)
    if closed_path: L.append(L[-1] + (path[0] - path[-1]).length)
    per = [0.0]
    for k in range(1, msec + 1):
        a, b = section[k - 1], section[k % msec]
        per.append(per[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    per = [p / max(per[-1], 1e-9) for p in per]
    F = []; UV = []
    nseg = n if closed_path else n - 1
    kmax = msec if closed_sec else msec - 1
    for i in range(nseg):
        i2 = (i + 1) % n
        for k in range(kmax):
            k2 = (k + 1) % msec
            F.append([i * msec + k, i * msec + k2, i2 * msec + k2, i2 * msec + k])
            UV.append([(L[i], per[k]), (L[i], per[k + 1]), (L[i + 1], per[k + 1]), (L[i + 1], per[k])])
    if caps and not closed_path and closed_sec:
        F.append([k for k in reversed(range(msec))])
        F.append([(n - 1) * msec + k for k in range(msec)])
        sx = max(abs(a) for a, b in section) or 1; sy = max(abs(b) for a, b in section) or 1
        UV.append([(0.5 + section[k][0] / (2 * sx) * 0.2, 0.5 + section[k][1] / (2 * sy)) for k in reversed(range(msec))])
        UV.append([(0.5 + section[k][0] / (2 * sx) * 0.2, 0.5 + section[k][1] / (2 * sy)) for k in range(msec)])
    bm, faces = bm_from(V, F, m)
    lu = lay(bm)[2]
    for f, uv in zip(faces, UV):
        if f is None: continue
        for l, c in zip(f.loops, uv): l[lu].uv = c
    # (N, B, tangent) is right-handed, so a counter-clockwise section (positive area) already
    # faces outward; a clockwise one is flipped
    area = sum(section[k][0] * section[(k + 1) % msec][1] - section[(k + 1) % msec][0] * section[k][1] for k in range(msec))
    if area < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def _up_default(i, p, t):
    return Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))


def circle(r, k, phase=0.0):
    return [(r * math.cos(2 * PI * (j + phase) / k), r * math.sin(2 * PI * (j + phase) / k)) for j in range(k)]


def tube(path, r, m, sides=6, caps=True, radii=None, up=None, closed_path=False, phase=0.5):
    sec = circle(r, sides, phase)
    sc = None if radii is None else [x / r for x in radii]
    return sweep(path, up or _up_default, sec, m, caps, sc, closed_path)


def chamfer_rect(w, h, c):
    """8-point chamfered rectangle section (w across u, h across v)."""
    a, b = w / 2, h / 2; c = min(c, a * 0.9, b * 0.9)
    return [(a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c), (-a + c, -b), (a - c, -b), (a, -b + c)]


def member(p0, p1, w, h, m, ch=0.22, up=None, caps=True, plain=False):
    """A timber or bar from p0 to p1: w wide (across, horizontal), h deep (along up); chamfered
    unless plain. Its loop UVs run along it (u metres) and around it (v)."""
    p0 = Vector(p0); p1 = Vector(p1)
    d = (p1 - p0).normalized()
    if up is None: up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    if plain:
        a, b = h / 2, w / 2
        sec = [(a, b), (-a, b), (-a, -b), (a, -b)]
    else:
        sec = [(y, x) for (x, y) in chamfer_rect(w, h, min(w, h) * ch)]
    return sweep([p0, p1], lambda i, p, t: Vector(up), sec, m, caps)


def torus(R_, r, n, k, m, phase=0.0):
    path = [(R_ * math.cos(2 * PI * i / n), R_ * math.sin(2 * PI * i / n), 0) for i in range(n)]
    sec = circle(r, k, phase)
    return sweep(path, lambda i, p, t: Vector(p).normalized(), sec, m, False, None, True)


def disc(r, n, z, m, up=True):
    V = [(r * math.cos(2 * PI * i / n), r * math.sin(2 * PI * i / n), z) for i in range(n)]
    F = [list(range(n)) if up else list(reversed(range(n)))]
    return bm_from(V, F, m)[0]


def grid(nu, nv, fn, m, fmat=None):
    """A (nu+1) x (nv+1) quad sheet: fn(s, t) -> point (s, t in 0..1). Loop UVs (s, t)."""
    V = [fn(i / nu, j / nv) for j in range(nv + 1) for i in range(nu + 1)]
    F = []; UV = []; M = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            F.append([a, a + 1, a + nu + 2, a + nu + 1])
            UV.append([(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)])
            M.append(fmat((i + 0.5) / nu, (j + 0.5) / nv) if fmat else m)
    bm, faces = bm_from(V, F, M)
    lu = lay(bm)[2]
    for f, uv in zip(faces, UV):
        if f is None: continue
        for l, c in zip(f.loops, uv): l[lu].uv = c
    return bm


def solidify(bm, t, m_edge=None):
    """Thicken a sheet by t along -normal: an underside (reversed) and edge walls."""
    out = new_bm(); merge(out, bm)
    a = lay(out)
    res = bmesh.ops.solidify(out, geom=out.faces[:], thickness=t)
    out.normal_update()
    return out


def geodesic(freq):
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


def bumps(D, rng, count, amp, size):
    r = np.ones(len(D))
    cs = math.cos(size)
    dirs = rng.normal(size=(count, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    for k in range(count):
        d = D @ dirs[k]
        g = np.clip((d - cs) / (1 - cs), 0, 1)
        r += amp * rng.uniform(0.6, 1.2) * (g * g * (3 - 2 * g))
    return r


def ellipsoid_e(Vv, center, radii, flat=1.0):
    q = (np.asarray(Vv, float) - center) / np.asarray(radii, float)
    q[:, 2] = np.where(q[:, 2] < 0, q[:, 2] / flat, q[:, 2])
    return np.linalg.norm(q, axis=1)


def pebble(center, radii, rng, m, freq=2, amp=0.12, flat=0.55, cut=None, n_b=5, planes=0.0):
    """A soft stone: a geodesic sphere with a few broad bumps, flattened underneath; faces below
    z = cut are dropped. planes > 0 quantises it toward a few broad facets."""
    D, F = geodesic(freq)
    r = bumps(D, rng, n_b, amp, 0.9)
    P = D * r[:, None]
    if planes > 0:
        ns = rng.normal(size=(7, 3)); ns /= np.linalg.norm(ns, axis=1, keepdims=True)
        ns[:, 2] = np.abs(ns[:, 2]) * 0.5 + 0.3; ns /= np.linalg.norm(ns, axis=1, keepdims=True)
        for nn in ns:
            d = P @ nn
            lim = 0.86
            over = np.maximum(d - lim, 0)
            P -= planes * over[:, None] * nn[None, :]
    P[:, 2] = np.where(P[:, 2] < 0, P[:, 2] * flat, P[:, 2])
    Vv = np.asarray(center, float) + P * np.asarray(radii, float)
    if cut is not None:
        keep = [f for f in F if max(Vv[i][2] for i in f) > cut]
        F = keep
    bm, _ = bm_from(Vv, F, m)
    return bm


# ---------------------------------------------------------------- tile UVs
def tile_natural(bm, tile, rng=None, span=1.2, faces=None, swap=False, vscale=1.0, voff=0.0):
    """Map loop UVs that hold (metres along, 0..1 around) onto a tile: along -> u (a random window
    of the tile, span metres for the full width; longer pieces stretch), around -> v."""
    lm, lr, lu, _, _ = lay(bm)
    fs = bm.faces if faces is None else [f for f in faces if f is not None]
    Lmax = max([l[lu].uv[0] for f in fs for l in f.loops] + [1e-4])
    w = min(1.0, Lmax / span)
    off = float(rng.uniform(0, 1 - w)) if rng is not None else 0.0
    tid = TILE[tile] + 1
    for f in fs:
        f[lr] = tid
        for l in f.loops:
            s, t = l[lu].uv
            u = off + w * s / Lmax; v = voff + t * vscale
            l[lu].uv = (v, u) if swap else (u, v)
    return bm


def tile_box(bm, tile, rng=None, span=1.2, faces=None, along=None, across=1.0):
    """Box-project the faces onto a tile: u along the piece's long axis (the grain), v across."""
    lm, lr, lu, _, _ = lay(bm)
    vs = [v.co for v in bm.verts]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    ext = [max(hi[i] - lo[i], 1e-4) for i in range(3)]
    ax = along if along is not None else max(range(3), key=lambda i: ext[i])
    Lx = ext[ax]
    w = min(1.0, Lx / span); off = float(rng.uniform(0, 1 - w)) if rng is not None else 0.0
    voff = float(rng.uniform(0, 1 - across)) if rng is not None else 0.0
    tid = TILE[tile] + 1
    bm.normal_update()
    for f in (bm.faces if faces is None else faces):
        f[lr] = tid
        n = f.normal
        dom = max(range(3), key=lambda i: abs(n[i]))
        if dom == ax:
            a, b = [i for i in range(3) if i != ax]
            for l in f.loops:
                co = l.vert.co
                l[lu].uv = (off + 0.04 * (co[a] - lo[a]) / ext[a], voff + across * (co[b] - lo[b]) / ext[b])
        else:
            other = [i for i in range(3) if i != ax and i != dom][0]
            for l in f.loops:
                co = l.vert.co
                l[lu].uv = (off + w * (co[ax] - lo[ax]) / Lx, voff + across * (co[other] - lo[other]) / ext[other])
    return bm


def tile_planar(bm, tile, fn, faces=None):
    """UVs from fn(co) -> (s, t) in 0..1 on a tile."""
    lm, lr, lu, _, _ = lay(bm)
    tid = TILE[tile] + 1
    for f in (bm.faces if faces is None else faces):
        if f is None: continue
        f[lr] = tid
        for l in f.loops: l[lu].uv = tuple(fn(l.vert.co))
    return bm


def tile_lathe(bm, tags, tile, segs, n, per_face=False, su=(0.0, 1.0)):
    """Lathe faces of the given profile segments onto a tile: u around (the whole way, or 0..1 on
    every face when per_face), v along the profile over those segments."""
    lr, lu = lay(bm)[1], lay(bm)[2]
    sel = [(f, s, i) for f, s, i in tags if s in segs]
    if not sel: return bm
    vs = [l[lu].uv[1] for f, _, _ in sel for l in f.loops]
    v0, v1 = min(vs), max(vs)
    tid = TILE[tile] + 1
    for f, s, i in sel:
        f[lr] = tid
        for l in f.loops:
            u, v = l[lu].uv
            uu = (u * n - i) if per_face else u
            l[lu].uv = (su[0] + (su[1] - su[0]) * uu, (v - v0) / max(v1 - v0, 1e-6))
    return bm


def tile_keep(bm, tile, faces=None):
    """The loop UVs already hold tile-local (s, t): just tag the tile."""
    lr = lay(bm)[1]; tid = TILE[tile] + 1
    for f in (bm.faces if faces is None else faces):
        if f is not None: f[lr] = tid
    return bm


# ---------------------------------------------------------------- the model
class Model:
    def __init__(self, name, pal=None, **kw):
        self.name = name
        self.pal = dict(DEF_PAL); self.pal.update(pal or {})
        self.groups = {'': []}
        self.origins = {'': (0.0, 0.0, 0.0)}
        self.attach = []              # (name, model-space location, group)
        self.lines = {}               # wear-map seams: map -> [polyline in map metres]
        self.spots = []               # extra wear marks: (map, a, b, radius, colour, alpha)
        self.parts = {}               # part id -> colour key (or a linear colour)
        self.extra = {}
        self.empty_root = False
        self.ground = 0.0             # z of the ground for occlusion (None: no ground)
        self.ao_dist = 0.45; self.ao = 0.62
        self.grad = (0.84, 1.6)       # shading gradient: brightness at the ground, height where it reaches 1
        # wear maps
        self.dirt = (0.82, 0.72, 0.56); self.dirt_h = 0.35; self.dirt_a = 0.42
        self.chips = 0.5; self.chip = (0.70, 0.56, 0.42); self.streaks = 0.4; self.fade = 0.04
        self.ppm = None
        self.maps = {}
        self.order = ''
        for k, v in kw.items(): setattr(self, k, v)

    def add(self, bm, group=''):
        self.groups.setdefault(group, []).append(bm); return bm

    def child(self, name, origin):
        self.groups.setdefault(name, []); self.origins[name] = tuple(origin)

    def at(self, name, loc, group=''):
        self.attach.append((name, tuple(loc), group))

    def line(self, mp, *pts):
        self.lines.setdefault(mp, []).append([tuple(p) for p in pts])

    def bbox(self):
        pts = [v.co for bms in self.groups.values() for b in bms for v in b.verts]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        return lo, hi

    def map_extents(self):
        lo, hi = self.bbox(); m = 0.06
        return {'front': (lo.x - m, hi.x + m, lo.z - m, hi.z + m), 'side': (lo.y - m, hi.y + m, lo.z - m, hi.z + m),
                'top': (lo.x - m, hi.x + m, lo.y - m, hi.y + m)}

    def uses_grime(self):
        for bms in self.groups.values():
            for b in bms:
                lm = lay(b)[0]
                for f in b.faces:
                    if MT[f[lm]][2] == 'grime': return True
        return False


# ---------------------------------------------------------------- shading
def _hemi(nr):
    g = PI * (3 - 5 ** 0.5); out = []
    for i in range(nr):
        u = (i + 0.5) / nr; r = math.sqrt(u); a = i * g
        out.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(max(0.0, 1 - u)))))
    return out


HEMI = _hemi(28)
LILAC = np.array((1.0, 1.03, 0.80))   # occlusion removes less blue: crevices go cool, never black


def occlusion(bvh, co, n, dist, ground):
    t = Vector((0, 0, 1)) if abs(n.z) < 0.95 else Vector((1, 0, 0))
    x = t.cross(n).normalized(); y = n.cross(x)
    o = co + n * 0.004
    occ = 0.0
    for d in HEMI:
        w = (x * d.x + y * d.y + n * d.z)
        hit = bvh.ray_cast(o, w, dist)
        h = None
        if hit[0] is not None: h = hit[3]
        if ground is not None and w.z < -1e-4:
            tg = (ground - o.z) / w.z
            if 0 < tg < dist and (h is None or tg < h): h = tg
        if h is not None:
            occ += 0.55 + 0.45 * (1 - h / dist)
    return occ / len(HEMI)


# ---------------------------------------------------------------- realize
def realize(M, layout):
    """Build the Blender objects for a Model; returns (root, objects)."""
    groups = {}
    for g, bms in M.groups.items():
        if not bms: continue
        bm = join(*bms)
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bm.normal_update(); bm.verts.index_update(); bm.faces.index_update()
        groups[g] = bm
    # one BVH over the whole model
    allV = []; allF = []
    for bm in groups.values():
        off = len(allV)
        allV += [v.co.copy() for v in bm.verts]
        allF += [[off + v.index for v in f.verts] for f in bm.faces]
    bvh = BVHTree.FromPolygons(allV, allF)
    lo, hi = M.bbox()
    H = max(hi.z - (M.ground if M.ground is not None else lo.z), 0.2)
    g0, gh = M.grad
    gh = min(gh, H)
    ext = M.map_extents()
    pal = {k: s2l(v) for k, v in M.pal.items()}
    objs = {}
    for g, bm in groups.items():
        lm, lr, lu, lc, lv = lay(bm)
        # shading per vertex
        shade = {}
        zg = M.ground if M.ground is not None else lo.z
        for v in bm.verts:
            cn = Vector(v[lc])
            n = cn if cn.length > 1e-6 else (v.normal if v.normal.length > 1e-6 else Vector((0, 0, 1)))
            occ = occlusion(bvh, v.co, n.normalized(), M.ao_dist, M.ground)
            hz = smooth01((v.co.z - zg) / gh)
            k = (g0 + (1 - g0) * hz) * (1 + 0.05 * max(n.z, 0))
            shade[v.index] = (occ, k)
        # crisp edges
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP):
                e.smooth = False
        cols = []; uvs = []; parts = []
        for f in bm.faces:
            part, key, uvm, aok = MT[f[lm]]
            nrm = f.normal
            if uvm == 'grime':
                ax, ay, az = abs(nrm.x), abs(nrm.y), abs(nrm.z)
                mp = 'top' if (az >= ax and az >= ay) else ('front' if ay >= ax else 'side')
            for l in f.loops:
                v = l.vert
                base = Vector(v[lv]) if key == '@' else Vector(pal[key])
                occ, k = shade[v.index]
                fac = (1 - M.ao * aok * occ * LILAC) * (k if aok > 0 else 1.0)
                c = [min(1.0, base[i] * fac[i]) for i in range(3)]
                cols.extend((c[0], c[1], c[2], 1.0))
                if uvm == 'keep' and f[lr] > 0:
                    uvs.extend(layout.tile_uv(TILES[f[lr] - 1][0], l[lu].uv))
                elif uvm == 'grime':
                    a0, a1, b0, b1 = ext[mp]; co = v.co
                    a, b = (co.x, co.z) if mp == 'front' else ((co.y, co.z) if mp == 'side' else (co.x, co.y))
                    uvs.extend(layout.tile_uv(M.name + '.' + mp, ((a - a0) / (a1 - a0), (b - b0) / (b1 - b0))))
                else:
                    uvs.extend(K.WHITE_UV)
                parts.extend((float(part), 0.0))
        # custom normal overrides (per vertex)
        cnv = {v.index: Vector(v[lc]) for v in bm.verts if Vector(v[lc]).length > 1e-6}
        name = M.name if g == '' else g
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        for a in ('mat', 'reg', 'cn', 'vc'):
            if a in me.attributes: me.attributes.remove(me.attributes[a])
        uv0 = me.uv_layers[0]; uv0.name = 'UVMap'
        uv0.data.foreach_set('uv', uvs)
        uv1 = me.uv_layers.new(name='Part'); uv1.data.foreach_set('uv', parts)
        col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
        col.data.foreach_set('color', cols)
        me.color_attributes.active_color = col; me.color_attributes.render_color_index = 0
        ob = K.new_obj(name, me)
        me.shade_smooth()
        # shade_smooth clears the sharp flags: mark them again from the bmesh
        sharp = [not e.smooth for e in bm.edges]
        if 'sharp_edge' not in me.attributes:
            me.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
        me.attributes['sharp_edge'].data.foreach_set('value', sharp)
        K.activate(ob)
        mod = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); mod.mode = 'FACE_AREA'; mod.weight = 50; mod.keep_sharp = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if cnv:
            nl = len(me.loops)
            arr = np.zeros(nl * 3, np.float32); me.corner_normals.foreach_get('vector', arr)
            arr = arr.reshape(-1, 3)
            lv_ = np.zeros(nl, np.int64); me.loops.foreach_get('vertex_index', lv_)
            for i in range(nl):
                c = cnv.get(int(lv_[i]))
                if c is not None: arr[i] = (c.x, c.y, c.z)
            me.normals_split_custom_set([tuple(map(float, a)) for a in arr])
        o = Vector(M.origins.get(g, (0, 0, 0)))
        if o.length > 0:
            me.transform(Matrix.Translation(-o)); ob.location = o
        objs[g] = ob
        bm.free()
    if M.empty_root:
        root = bpy.data.objects.new(M.name, None); C.scene.collection.objects.link(root)
        root.empty_display_size = 0.3
        for g, ob in objs.items():
            ob.parent = root
    else:
        root = objs['']
        for g, ob in objs.items():
            if g != '': ob.parent = root
    root['kit_name'] = M.name
    for g, ob in objs.items():
        ob['kit_name'] = M.name if g == '' else g
    K.attach(root, 'Front', (0, -1, 0))['kit_name'] = 'Attach.Front'
    for name, loc, g in M.attach:
        par = objs[g] if g else root
        o = Vector(M.origins.get(g, (0, 0, 0))) if g else Vector()
        K.attach(par, name, Vector(loc) - o)['kit_name'] = 'Attach.' + name
    return root, objs


def export_clean(root, path):
    """Export with every object under its intended name: Blender suffixes duplicates (a second
    'Attach.Front' becomes 'Attach.Front.001'), so the names are swapped in for this export."""
    for o in [root] + list(root.children_recursive):
        want = o.get('kit_name')
        if not want or o.name == want: continue
        other = bpy.data.objects.get(want)
        if other is not None and other is not o:
            other.name = want + '~'
        o.name = want
    K.export_model(root, path)
