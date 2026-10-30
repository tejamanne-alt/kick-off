# Mesh layer of the WORKS kit (kit_works.py): bmesh pieces with per-face materials, primitives
# (boxes, chamfered and rounded boxes, lathes, sweeps, tubes, extruded outlines, trays, blobs),
# the atlas layout, and the conversion of a model's pieces into one mesh object with
#   vertex colours  base colour x baked soft shading (ray-cast ambient occlusion, piece gradients)
#   UV0             the kit atlas: the model's own projected grime maps, a shared tile, or white
#   UV1.x           recolour part (0 fixed, 1 main paint, 2 secondary)
# and soft custom normals (weighted by face area, sharp only where a piece asks for it).
#
# Every piece is a bmesh with face layers
#   mat    index into MATS            sm     0 sharp above 40 degrees, 1 always smooth, 2 always sharp
#   tile   shared atlas tile id or -1 shade  brightness multiplier
#   bz0, bz1  the piece's height range (for gradients)
# and a loop UV layer 'UVMap' holding tile-local (s, t) in [0, 1] when tile >= 0.
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import kit_lib as K

import os as _os
PI = math.pi
AT = 2048
PROFILE = bool(_os.environ.get('KIT_PROFILE'))
WHITE_UV = K.WHITE_UV


def s2l(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


# ---------------------------------------------------------------- materials
# name: (part, colour, uv mode, grad)
#   colour  'p1' / 'p2' (the model's part colours), 'p1d' / 'p2d' (the same, darker) or an sRGB triple
#   uv      grime  the model's projected maps (front / side / top) - a multiplier with wear and dirt
#           keep   a shared tile set by the piece (tile layer + local UVs)
#           white  the atlas' plain corner
#   grad    how much darker the bottom of its piece is than the top (0..1)
SITE_YELLOW = (0.93, 0.72, 0.27)
SAFETY_ORANGE = (0.90, 0.47, 0.20)
STEEL_BLUE = (0.47, 0.56, 0.62)
MAT = {
    'p1': (1, 'p1', 'grime', 0.0), 'p1d': (1, 'p1d', 'grime', 0.0), 'p1w': (1, 'p1', 'white', 0.0),
    'p1k': (1, 'p1', 'keep', 0.0), 'p1dk': (1, 'p1d', 'keep', 0.0), 'p1g': (1, 'p1', 'grime', 0.25),
    'p2': (2, 'p2', 'grime', 0.0), 'p2d': (2, 'p2d', 'grime', 0.0), 'p2w': (2, 'p2', 'white', 0.0),
    'p2k': (2, 'p2', 'keep', 0.0),
    'yellow': (0, SITE_YELLOW, 'grime', 0.0), 'yelloww': (0, SITE_YELLOW, 'white', 0.0),
    'orange': (0, SAFETY_ORANGE, 'grime', 0.0), 'orangew': (0, SAFETY_ORANGE, 'white', 0.0),
    'steel': (0, STEEL_BLUE, 'grime', 0.0),
    'galv': (0, (0.73, 0.75, 0.76), 'grime', 0.0), 'galvw': (0, (0.73, 0.75, 0.76), 'white', 0.0),
    'iron': (0, (0.27, 0.27, 0.30), 'grime', 0.0), 'ironw': (0, (0.27, 0.27, 0.30), 'white', 0.0),
    'dark': (0, (0.15, 0.15, 0.17), 'white', 0.0), 'rubber': (0, (0.19, 0.19, 0.20), 'white', 0.0),
    'rubberg': (0, (0.21, 0.21, 0.22), 'grime', 0.0),
    'chrome': (0, (0.84, 0.86, 0.87), 'white', 0.0), 'metal': (0, (0.60, 0.62, 0.64), 'grime', 0.0),
    'conc': (0, (0.78, 0.76, 0.72), 'grime', 0.0), 'concd': (0, (0.62, 0.60, 0.57), 'grime', 0.0),
    'concw': (0, (0.78, 0.76, 0.72), 'white', 0.15),
    'asphalt': (0, (0.36, 0.35, 0.36), 'grime', 0.0),
    'timber': (0, (0.71, 0.53, 0.35), 'grime', 0.0), 'timberw': (0, (0.71, 0.53, 0.35), 'white', 0.15),
    'tex': (0, (1.0, 1.0, 1.0), 'keep', 0.0), 'texg': (0, (1.0, 1.0, 1.0), 'keep', 0.2),
    'red': (0, (0.83, 0.20, 0.17), 'white', 0.0), 'redg': (0, (0.83, 0.20, 0.17), 'grime', 0.0),
    'white': (0, (0.96, 0.95, 0.92), 'white', 0.0), 'whiteg': (0, (0.96, 0.95, 0.92), 'grime', 0.0),
    'cream': (0, (0.95, 0.91, 0.82), 'grime', 0.0), 'creamw': (0, (0.95, 0.91, 0.82), 'white', 0.0),
    'lamp': (0, (1.0, 0.95, 0.80), 'white', 0.0), 'amber': (0, (0.98, 0.62, 0.18), 'white', 0.0),
    'green': (0, (0.32, 0.62, 0.36), 'white', 0.0), 'lens': (0, (0.12, 0.14, 0.18), 'white', 0.0),
    'blue': (0, (0.34, 0.52, 0.72), 'white', 0.0),
    'soil': (0, (0.40, 0.31, 0.24), 'white', 0.0), 'sand': (0, (0.86, 0.76, 0.58), 'grime', 0.0),
    'leaf': (0, (0.40, 0.60, 0.32), 'white', 0.35), 'leafl': (0, (0.55, 0.72, 0.36), 'white', 0.3),
    'leafd': (0, (0.27, 0.46, 0.27), 'white', 0.35),
    'fl1': (0, (0.97, 0.56, 0.64), 'white', 0.1), 'fl2': (0, (0.99, 0.84, 0.36), 'white', 0.1),
    'fl3': (0, (0.97, 0.96, 0.91), 'white', 0.1), 'fl4': (0, (0.93, 0.40, 0.30), 'white', 0.1),
    'fl5': (0, (0.74, 0.58, 0.88), 'white', 0.1),
    'terra': (0, (0.80, 0.45, 0.32), 'grime', 0.2), 'brass': (0, (0.82, 0.66, 0.34), 'white', 0.0),
    'oxide': (0, (0.64, 0.33, 0.24), 'grime', 0.0),
}
MATS = list(MAT)
MID = {n: i for i, n in enumerate(MATS)}

TILES = []                    # shared atlas tiles by id (names), registered by the painters
TID = {}


def tile_id(name):
    if name not in TID:
        TID[name] = len(TILES); TILES.append(name)
    return TID[name]


# ---------------------------------------------------------------- bmesh pieces
def new_bm():
    bm = bmesh.new()
    fl = bm.faces.layers
    fl.int.new('mat'); fl.int.new('sm'); fl.int.new('tile')
    fl.float.new('shade'); fl.float.new('bz0'); fl.float.new('bz1')
    bm.loops.layers.uv.new('UVMap')
    return bm


def L(bm):
    fl = bm.faces.layers
    return (fl.int['mat'], fl.int['sm'], fl.int['tile'], fl.float['shade'], fl.float['bz0'], fl.float['bz1'],
            bm.loops.layers.uv['UVMap'])


def bm_from(V, F, mat, sm=0):
    """Faces F over vertices V; mat is one name or one per face."""
    bm = new_bm(); lm, ls, lt, lsh, _, _, lu = L(bm)
    vs = [bm.verts.new(tuple(map(float, v))) for v in V]
    out = []
    for k, f in enumerate(F):
        try:
            face = bm.faces.new([vs[i] for i in f])
        except ValueError:
            out.append(None); continue
        face[lm] = MID[mat if isinstance(mat, str) else mat[k]]; face[ls] = sm; face[lt] = -1; face[lsh] = 1.0
        out.append(face)
    bm.normal_update()
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return bm, out


def merge(dst, src):
    ld = L(dst); ls_ = L(src)
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        for a, b in zip(ld[:6], ls_[:6]): nf[a] = f[b]
        for a, b in zip(f.loops, nf.loops): b[ld[6]].uv = a[ls_[6]].uv
    return dst


def copy(bm):
    return bm.copy()


def xform(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if M.to_3x3().determinant() < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def setmat(bm, name, faces=None):
    lm = L(bm)[0]
    for f in (bm.faces if faces is None else faces): f[lm] = MID[name]
    return bm


def setsm(bm, v, faces=None):
    ls = L(bm)[1]
    for f in (bm.faces if faces is None else faces): f[ls] = v
    return bm


def setshade(bm, v, faces=None):
    lsh = L(bm)[3]
    for f in (bm.faces if faces is None else faces): f[lsh] = v
    return bm


def settile(bm, name, fn, faces=None, mat=None):
    """Faces sample shared tile `name` at fn(co, face) -> (s, t) in [0, 1]."""
    lm, _, lt, _, _, _, lu = L(bm)
    tid = tile_id(name)
    for f in (bm.faces if faces is None else faces):
        f[lt] = tid
        if mat: f[lm] = MID[mat]
        for l in f.loops:
            l[lu].uv = fn(l.vert.co, f)
    return bm


def tile_box(bm, name, lo, hi, faces=None, mat=None, axes=None):
    """Box-projected tile UVs normalised to (lo, hi). axes: fixed (a, b) axis pair, else by normal."""
    bm.normal_update()

    def fn(co, f):
        if axes: a, b = axes
        else:
            ax = max(range(3), key=lambda i: abs(f.normal[i]))
            a, b = [(1, 2), (0, 2), (0, 1)][ax]
        return ((co[a] - lo[a]) / max(hi[a] - lo[a], 1e-5), (co[b] - lo[b]) / max(hi[b] - lo[b], 1e-5))
    return settile(bm, name, fn, faces, mat)


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update(); return bm


def faces_facing(bm, d, cos=0.7):
    d = Vector(d).normalized(); bm.normal_update()
    return [f for f in bm.faces if f.normal.dot(d) > cos]


def delete_faces(bm, faces):
    bmesh.ops.delete(bm, geom=list(faces), context='FACES'); return bm


def tris_of(bm):
    return sum(len(f.verts) - 2 for f in bm.faces)


# ---------------------------------------------------------------- matrices
def T(x, y=None, z=None):
    if y is None: return Matrix.Translation(Vector(x))
    return Matrix.Translation(Vector((x, y, z)))


def R(angle, axis):
    return Matrix.Rotation(angle, 4, axis)


def S(sx, sy=None, sz=None):
    if sy is None: sy = sz = sx
    return Matrix.Diagonal((sx, sy, sz, 1.0))


def basis(origin, x, y, z):
    M = Matrix((Vector(x), Vector(y), Vector(z))).transposed().to_4x4(); M.translation = Vector(origin); return M


def frame(origin, z, up=(0, 0, 1)):
    """A matrix at origin whose local Z is z and whose local Y leans toward up."""
    z = Vector(z).normalized(); up = Vector(up)
    x = up.cross(z)
    if x.length < 1e-6: x = Vector((1, 0, 0)).cross(z)
    if x.length < 1e-6: x = Vector((0, 1, 0)).cross(z)
    x.normalize(); y = z.cross(x)
    return basis(origin, x, y, z)


def along(a, b):
    """A matrix mapping local Z (0..1 scaled to the length) onto the segment a -> b."""
    a = Vector(a); b = Vector(b); d = b - a
    return frame(a, d, (0, 0, 1) if abs(d.normalized().z) < 0.95 else (1, 0, 0))


# ---------------------------------------------------------------- primitives
def box(lo, hi, mat, skip=(), sm=0):
    """An axis-aligned box; skip: faces left out, as '-x', '+x', '-y', '+y', '-z', '+z'."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = {'-z': (0, 3, 2, 1), '+z': (4, 5, 6, 7), '-y': (0, 1, 5, 4), '+y': (2, 3, 7, 6), '-x': (3, 0, 4, 7), '+x': (1, 2, 6, 5)}
    faces = [f for k, f in F.items() if k not in skip]
    return bm_from(V, faces, mat, sm)[0]


def cbox(lo, hi, r, mat, seg=1, sm=0):
    """A chamfered (seg 1) or rounded (seg 2+) box from lo to hi."""
    lo = Vector(lo); hi = Vector(hi); size = hi - lo
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    r = min(r, min(size) * 0.45)
    if r > 1e-4:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    lm, ls, lt, lsh, _, _, _ = L(bm)
    for f in bm.faces:
        f[lm] = MID[mat]; f[ls] = sm; f[lt] = -1; f[lsh] = 1.0
    xform(bm, T((lo + hi) / 2))
    return fix_normals(bm)


def _lines(a0, a1, r, seg, extra):
    cs = {round(a0, 6), round(a1, 6)}
    for o in {0: [], 1: [1.0], 2: [1.0, 0.586], 3: [1.0, 0.732, 0.423]}[seg]:
        cs.add(round(a0 + r * o, 6)); cs.add(round(a1 - r * o, 6))
    for e in extra:
        if a0 + 1e-4 < e < a1 - 1e-4: cs.add(round(e, 6))
    return sorted(cs)


def rbox(lo, hi, r, mat, seg=(2, 2, 2), extra=((), (), ()), skip=(), deform=None, sm=0, matfn=None):
    """A rounded box on an explicit grid (the car kit's form): each face is a grid of the
    rounding lines and the extra lines, projected onto a box with elliptical edges of radii r.
    skip: (axis, sign) faces left out. matfn(axis, sign, centre) -> material name per face."""
    lo = np.array(lo, float); hi = np.array(hi, float); r = np.maximum(np.array(r, float) if np.ndim(r) else np.array([r] * 3, float), 1e-4)
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
    if deform is not None: X = deform(X)
    if matfn is not None:
        mats = [matfn(a, s, P[f].mean(axis=0)) for f, (a, s) in zip(F, Tg)]
    else:
        mats = mat
    bm, _ = bm_from(X, F, mats, sm)
    return bm


def lathe(prof, n, mats, phase=0.5, sm=0, arc=None):
    """A surface of revolution about local Z. prof: (radius, height) from one end to the other
    (r = 0 makes a pole); faces point outward when the profile runs bottom to top on the outside.
    mats: one per profile segment (or one name). arc: (a0, a1) for a partial revolution.
    Returns (bm, [(face, segment, i)])."""
    V = []; rings = []
    full = arc is None
    cnt = n if full else n + 1
    for (r, h) in prof:
        if r < 1e-7:
            rings.append([len(V)]); V.append((0.0, 0.0, h))
        else:
            ids = list(range(len(V), len(V) + cnt)); rings.append(ids)
            for i in range(cnt):
                a = 2 * PI * (i + phase) / n if full else arc[0] + (arc[1] - arc[0]) * i / n
                V.append((r * math.cos(a), r * math.sin(a), h))
    F = []; M = []; tags = []
    for si in range(len(prof) - 1):
        A, B = rings[si], rings[si + 1]
        if len(A) == 1 and len(B) == 1: continue
        for i in range(n):
            i2 = (i + 1) % cnt if full else i + 1
            if len(A) == 1: f = [A[0], B[i2], B[i]]
            elif len(B) == 1: f = [A[i], A[i2], B[0]]
            else: f = [A[i], A[i2], B[i2], B[i]]
            F.append(f); M.append(mats if isinstance(mats, str) else mats[si]); tags.append((si, i))
    bm, faces = bm_from(V, F, M, sm)
    return bm, [(f, s, i) for f, (s, i) in zip(faces, tags) if f is not None]


def cyl(r, z0, z1, n, mat, caps=(True, True), bevel=0.0, sm=0, phase=0.5, cap_mat=None):
    """A cylinder along local Z with optional chamfered rims."""
    cm = cap_mat or mat
    b = min(bevel, r * 0.4, (z1 - z0) * 0.4)
    prof = []
    if caps[0]:
        prof.append((0.0, z0))
        if b > 0: prof.append((r - b, z0))
    prof.append((r, z0 + (b if caps[0] else 0.0)))
    prof.append((r, z1 - (b if caps[1] else 0.0)))
    if caps[1]:
        if b > 0: prof.append((r - b, z1))
        prof.append((0.0, z1))
    mats = [cm if abs(prof[i][1] - prof[i + 1][1]) < 1e-9 else mat for i in range(len(prof) - 1)]
    bm, _ = lathe(prof, n, mats, phase=phase, sm=sm)
    return bm


def _frames(path, up0, closed=False):
    """Parallel-transport frames (tangent, normal, binormal) along a polyline."""
    n = len(path); P = [Vector(p) for p in path]
    Ts = []
    for i in range(n):
        if closed:
            t = (P[(i + 1) % n] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
        elif i == 0: t = P[1] - P[0]
        elif i == n - 1: t = P[-1] - P[-2]
        else: t = (P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
        Ts.append(t.normalized())
    u = Vector(up0)
    N = (u - Ts[0] * u.dot(Ts[0]))
    if N.length < 1e-6: N = Ts[0].orthogonal()
    N.normalize()
    out = []
    for i in range(n):
        if i > 0:
            q = Ts[i - 1].rotation_difference(Ts[i])
            N = (q @ N); N = (N - Ts[i] * N.dot(Ts[i])).normalized()
        out.append((Ts[i], N, Ts[i].cross(N)))
    return out


def sweep(path, section, mat, up=(0, 0, 1), caps=True, closed=False, scales=None, sm=0, uvtile=None):
    """Rings of a closed 2D section (a along the normal, b along the binormal) along a polyline,
    framed by parallel transport from `up`. uvtile: (tile name, metres per tile length) maps
    s around the section and t along the path."""
    n = len(path); m = len(section); V = []
    fr = _frames(path, up, closed)
    for i, p in enumerate(path):
        p = Vector(p); t, N, B = fr[i]
        sc = scales[i] if scales else 1.0
        if closed:   # mitre the ring so the tube keeps its thickness at corners
            pass
        for (a, b) in section: V.append(p + N * (a * sc) + B * (b * sc))
    F = []
    segs = n if closed else n - 1
    for i in range(segs):
        i2 = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            F.append([i * m + k, i * m + k2, i2 * m + k2, i2 * m + k])
    nside = len(F)
    if caps and not closed:
        F.append([k for k in reversed(range(m))]); F.append([(n - 1) * m + k for k in range(m)])
    bm, faces = bm_from(V, F, mat, sm)
    bm.verts.index_update()
    if uvtile:
        name, tl = uvtile
        L_ = [0.0]
        for i in range(1, n + (1 if closed else 0)):
            L_.append(L_[-1] + (Vector(path[i % n]) - Vector(path[i - 1])).length)
        if tl is None: tl = max(L_[-1], 1e-4)
        lt = L(bm)[2]; lu = L(bm)[6]; tid = tile_id(name)
        for fi, f in enumerate(faces[:nside]):
            if f is None: continue
            i, k = divmod(fi, m)
            f[lt] = tid
            for l in f.loops:
                vi = l.vert.index
                ri, kk = divmod(vi, m)
                if closed and ri == 0 and i == n - 1: ri = n
                kk2 = kk if not (kk == 0 and k == m - 1) else m
                l[lu].uv = (kk2 / m, L_[ri] / tl)
    return fix_normals(bm)


def tube(path, radius, mat, sides=6, caps=True, sm=1, up=(0, 0, 1), closed=False, uvtile=None):
    sec = [(radius * math.cos(2 * PI * (k + 0.5) / sides), radius * math.sin(2 * PI * (k + 0.5) / sides)) for k in range(sides)]
    bm = sweep(path, sec, mat, up=up, caps=caps, closed=closed, sm=sm, uvtile=uvtile)
    if caps:
        ls = L(bm)[1]
        for f in bm.faces:
            if len(f.verts) > 4: f[ls] = 0
    return bm


def bar(a, b, w, mat, sides=4, sm=None, caps=True):
    """A thin straight member from a to b (square by default)."""
    return tube([a, b], w * (0.5 / math.cos(PI / sides)), mat, sides=sides, caps=caps, sm=(1 if sides > 4 else 2) if sm is None else sm)


def extrude_poly(pts, depth, mat, side_mat=None, caps=(True, True), sm=0):
    """A 2D outline (x, y) extruded along +Z from 0 to depth."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(reversed(range(n)))
    V = [(x, y, 0.0) for x, y in pts] + [(x, y, depth) for x, y in pts]
    F = []; M = []
    if caps[1]: F.append([n + i for i in idx]); M.append(mat)
    if caps[0]: F.append(list(reversed(idx))); M.append(mat)
    for j in range(n):
        a, b = idx[j], idx[(j + 1) % n]
        F.append([a, b, n + b, n + a]); M.append(side_mat or mat)
    bm, _ = bm_from(V, F, M, sm)
    return bm


def rrect(hx, hy, r, nc=3, cx=0.0, cy=0.0):
    """A rounded rectangle outline (counter-clockwise), nc segments per corner."""
    r = min(r, hx * 0.999, hy * 0.999)
    pts = []
    for (sx, sy, a0) in ((1, 1, 0.0), (-1, 1, PI / 2), (-1, -1, PI), (1, -1, 1.5 * PI)):
        ccx, ccy = cx + sx * (hx - r), cy + sy * (hy - r)
        for i in range(nc + 1):
            a = a0 + (PI / 2) * i / nc
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


def loft(rings, mats, closed_bottom=True, closed_top=False, sm=0):
    """Faces between consecutive rings of equal point count (each ring a list of 3D points).
    mats: one per band (len(rings) - 1) or one name."""
    m = len(rings[0]); V = [p for r in rings for p in r]
    F = []; M = []
    for i in range(len(rings) - 1):
        for k in range(m):
            k2 = (k + 1) % m
            F.append([i * m + k, i * m + k2, (i + 1) * m + k2, (i + 1) * m + k])
            M.append(mats if isinstance(mats, str) else mats[i])
    if closed_bottom: F.append(list(reversed(range(m)))); M.append(mats if isinstance(mats, str) else mats[0])
    if closed_top: F.append([(len(rings) - 1) * m + k for k in range(m)]); M.append(mats if isinstance(mats, str) else mats[-1])
    bm, _ = bm_from(V, F, M, sm)
    return bm


def tray(bot, top, z0, z1, t, mat, inner_mat=None, nc=3, fill=None):
    """An open container: bot/top = (hx, hy, r) rounded rectangles at z0 / z1, wall thickness t.
    fill: height of a flat fill surface inside (or None for the inner floor)."""
    im = inner_mat or mat

    def ring(spec, z, off=0.0):
        hx, hy, r = spec
        return [(x, y, z) for x, y in rrect(hx - off, hy - off, max(r - off, 0.01), nc)]
    outer = [ring(bot, z0), ring(top, z1)]
    lip = [ring(top, z1, t)]
    zi = fill if fill is not None else z0 + t
    k = (zi - z0) / (z1 - z0)
    mid = (bot[0] + (top[0] - bot[0]) * k, bot[1] + (top[1] - bot[1]) * k, bot[2] + (top[2] - bot[2]) * k)
    inner = [ring(mid, zi, t)]
    rings = outer + lip + inner
    bm = loft(rings, [mat, mat, im], closed_bottom=True, closed_top=True)
    return fix_normals(bm)


def blob(center, radii, mat, n=7, rings=3, seed=0, jitter=0.12, flat_bottom=None, sm=1):
    """A soft lumpy ellipsoid (flowers, foliage, sand heaps)."""
    rng = np.random.default_rng(seed)
    prof = [(0.0, -1.0)]
    for k in range(1, rings + 1):
        a = -PI / 2 + PI * k / (rings + 1)
        prof.append((math.cos(a), math.sin(a)))
    prof.append((0.0, 1.0))
    bm, _ = lathe(prof, n, mat, phase=rng.random(), sm=sm)
    for v in bm.verts:
        j = 1 + jitter * (rng.random() * 2 - 1)
        z = v.co.z
        if flat_bottom is not None: z = max(z, flat_bottom)
        v.co = Vector((v.co.x * radii[0] * j, v.co.y * radii[1] * j, z * radii[2] * (1 + 0.5 * jitter * (rng.random() * 2 - 1))))
    xform(bm, T(center))
    return bm


def chain_links(a, b, w, mat='tex'):
    """A chain as a flat bar textured with links (the chain tile stretched over its length)."""
    bm = tube([a, b], w * 0.5, mat, sides=4, caps=True, sm=2, uvtile=('chain', None))
    return bm


# ---------------------------------------------------------------- the model
class Model:
    def __init__(self, name, p1=None, p2=None, ppm=60, ground=True, ao_radius=None, grime=None, ao=0.6):
        self.name = name
        self.p1 = p1; self.p2 = p2
        self.ppm = ppm                    # pixels per metre of its projected maps
        self.ground = ground              # stands on z = 0 (ground occlusion and dirt)
        self.ao_radius = ao_radius
        self.ao = ao
        self.grime = dict(mottle=0.06, ground=0.5, dirt_h=0.45, streaks=0.5, rust=0.25, chips=0.3, seed=len(name) * 7)
        if grime: self.grime.update(grime)
        self.pieces = []
        self.attach = []                  # (name, location)
        self.feats = {}                   # map name -> [(kind, kw)]
        self.extra = {}                   # manifest extras
        self.ledges = []
        self.maps = {}
        self.prof = {}

    def add(self, bm, mat=None, sm=None, shade=None, tile=None):
        if bm is None or len(bm.faces) == 0: return bm
        lm, ls, lt, lsh, lb0, lb1, lu = L(bm)
        if mat is not None:
            for f in bm.faces: f[lm] = MID[mat]
        if sm is not None:
            for f in bm.faces: f[ls] = sm
        if shade is not None:
            for f in bm.faces: f[lsh] = shade
        zs = [v.co.z for v in bm.verts]
        z0, z1 = min(zs), max(zs)
        for f in bm.faces: f[lb0] = z0; f[lb1] = z1
        self.pieces.append(bm)
        if PROFILE:
            import inspect
            fr = inspect.stack()[1]
            k = '%s:%d' % (fr.function, fr.lineno)
            self.prof[k] = self.prof.get(k, 0) + tris_of(bm)
        return bm

    def feat(self, mp, kind, **kw):
        self.feats.setdefault(mp, []).append((kind, kw))

    def pal(self, key):
        c = MAT[key][1]
        p1 = self.p1 or (1.0, 1.0, 1.0); p2 = self.p2 or (1.0, 1.0, 1.0)
        if c == 'p1': return p1
        if c == 'p2': return p2
        if c == 'p1d': return tuple(x * 0.78 for x in p1)
        if c == 'p2d': return tuple(x * 0.78 for x in p2)
        return c

    def bounds(self):
        lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
        for bm in self.pieces:
            for v in bm.verts:
                for i in range(3):
                    lo[i] = min(lo[i], v.co[i]); hi[i] = max(hi[i], v.co[i])
        return lo, hi

    def tris(self):
        return sum(tris_of(b) for b in self.pieces)

    def plan_maps(self, margin=0.04):
        lo, hi = self.bounds()
        lo = lo - Vector((margin,) * 3); hi = hi + Vector((margin,) * 3)
        self.lo, self.hi = lo, hi
        e = {'front': (lo.x, hi.x, lo.z, hi.z), 'side': (lo.y, hi.y, lo.z, hi.z), 'top': (lo.x, hi.x, lo.y, hi.y)}
        self.maps = e
        out = []
        for mp, (a0, a1, b0, b1) in e.items():
            ppm = self.ppm * (0.6 if mp == 'top' else 1.0)
            out.append((self.name + '.' + mp, max(8, int(math.ceil((a1 - a0) * ppm))), max(8, int(math.ceil((b1 - b0) * ppm)))))
        return out


# ---------------------------------------------------------------- atlas layout
REG = {}           # name -> (u0, v0, u1, v1)


def reg_px(name):
    u0, v0, u1, v1 = REG[name]
    return int(round(u0 * AT)), int(round((1 - v1) * AT)), int(round(u1 * AT)), int(round((1 - v0) * AT))


def reg_uv(name, s, t):
    u0, v0, u1, v1 = REG[name]
    s = min(max(s, 0.0), 1.0); t = min(max(t, 0.0), 1.0)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


def allocate(items, pad=4, white=64):
    """Shelf-pack [(name, w, h)] (pixels) from the top-left; the bottom `white` rows stay clear
    (the plain white corner lives at the bottom right). Returns the rows used."""
    REG.clear()
    REG['white'] = ((AT - white) / AT, 0.0, 1.0, white / AT)
    limit = AT - white - 2 * pad
    items = sorted(items, key=lambda r: (-r[2], -r[1]))
    sx = 0; sy = 0; sh = 0
    for name, w, h in items:
        W2, H2 = w + 2 * pad, h + 2 * pad
        if sx + W2 > AT:
            sx = 0; sy += sh; sh = 0
        if sy + H2 > limit:
            raise RuntimeError('atlas full at %s (%d x %d)' % (name, w, h))
        x0, y0 = sx + pad, sy + pad
        REG[name] = (x0 / AT, (AT - (y0 + h)) / AT, (x0 + w) / AT, (AT - y0) / AT)
        sx += W2; sh = max(sh, H2)
    return sy + sh


# ---------------------------------------------------------------- ambient occlusion
def _hemi(n):
    """Cosine-weighted hemisphere directions (z up), a Fibonacci spiral."""
    out = []
    ga = PI * (3 - math.sqrt(5))
    for i in range(n):
        r = math.sqrt((i + 0.5) / n)
        a = i * ga
        out.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(max(0.0, 1 - r * r)))))
    return out


def bake_ao(V, Fs, pts, nrms, radius, ground, rays=28):
    bvh = BVHTree.FromPolygons(V, Fs, all_triangles=True)
    H = _hemi(rays)
    eps = max(radius * 2e-3, 1e-3)
    out = np.ones(len(pts), np.float32)
    for k, (co, n) in enumerate(zip(pts, nrms)):
        t = n.orthogonal().normalized(); b = n.cross(t)
        occ = 0.0
        o = co + n * eps
        for d in H:
            w = t * d.x + b * d.y + n * d.z
            hit = bvh.ray_cast(o, w, radius)
            h = 0.0
            # a back-face hit means the sample sits inside another part (overlapping pieces):
            # that is not occlusion seen from outside, so it does not count
            if hit[0] is not None and hit[1].dot(w) < 0:
                q = hit[3] / radius
                h = 1.0 - q * q * (3 - 2 * q)
            if ground and w.z < -1e-4:
                tg = (co.z + 0.002) / -w.z
                if tg < radius:
                    q = tg / radius
                    h = max(h, 0.85 * (1.0 - q * q * (3 - 2 * q)))
            occ += h
        out[k] = 1.0 - occ / len(H)
    return out


# ---------------------------------------------------------------- to a mesh object
def to_object(M, sharp_deg=40.0):
    bm = new_bm()
    for p in M.pieces: merge(bm, p)
    for p in M.pieces: p.free()
    M.pieces = []
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.normal_update()
    lm, ls, lt, lsh, lb0, lb1, lu = L(bm)
    thr = math.radians(sharp_deg)
    for f in bm.faces: f.smooth = True
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) != 2:
            e.smooth = len(lf) < 2; continue
        a, b = lf[0][ls], lf[1][ls]
        if a == 2 or b == 2: e.smooth = False
        elif a == 1 and b == 1: e.smooth = True
        else: e.smooth = e.calc_face_angle(0.0) < thr
    # ledges for the grime streaks: upward faces, in model space
    led = []
    for f in bm.faces:
        if f.normal.z > 0.6 and f.calc_area() > 4e-4:
            xs = [v.co.x for v in f.verts]; ys = [v.co.y for v in f.verts]; zs = [v.co.z for v in f.verts]
            led.append((min(xs), max(xs), min(ys), max(ys), max(zs)))
    M.ledges = led
    me = bpy.data.meshes.new(M.name); bm.to_mesh(me); bm.free()
    ob = K.new_obj(M.name, me)
    K.activate(ob)
    m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.mode = 'FACE_AREA'; m.weight = 50; m.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    m = ob.modifiers.new('tri', 'TRIANGULATE'); m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'; m.keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    paint_mesh(M, me)
    return ob


def _attr(me, name, n, dtype=np.float32):
    a = np.zeros(n, dtype); me.attributes[name].data.foreach_get('value', a); return a


def paint_mesh(M, me):
    npl = len(me.polygons); nl = len(me.loops); nv = len(me.vertices)
    mats = _attr(me, 'mat', npl, np.int32); tiles = _attr(me, 'tile', npl, np.int32)
    shade = _attr(me, 'shade', npl); bz0 = _attr(me, 'bz0', npl); bz1 = _attr(me, 'bz1', npl)
    pn = np.zeros(npl * 3, np.float32); me.polygons.foreach_get('normal', pn); pn = pn.reshape(-1, 3)
    tot = np.zeros(npl, np.int32); me.polygons.foreach_get('loop_total', tot)
    lp = np.repeat(np.arange(npl), tot)
    lv = np.zeros(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
    vco = np.zeros(nv * 3, np.float32); me.vertices.foreach_get('co', vco); vco = vco.reshape(-1, 3)
    co = vco[lv]
    cn = np.zeros(nl * 3, np.float32); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    uv = np.zeros(nl * 2, np.float32); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    # ---- ambient occlusion per (vertex, corner normal)
    lo, hi = M.lo, M.hi
    diag = float(np.linalg.norm(np.array(hi) - np.array(lo)))
    radius = M.ao_radius or min(max(0.1 * diag, 0.08), 2.0)
    keys = {}
    kidx = np.zeros(nl, np.int32)
    q = np.round(cn * 8).astype(np.int32)
    for i in range(nl):
        k = (int(lv[i]), int(q[i, 0]), int(q[i, 1]), int(q[i, 2]))
        j = keys.get(k)
        if j is None: j = keys[k] = len(keys)
        kidx[i] = j
    # sample each corner a little way in toward its triangle's centre, so a big face whose corners
    # sit in crevices is not darkened all over by its corners' occlusion
    pc = np.zeros(npl * 3, np.float32); me.polygons.foreach_get('center', pc); pc = pc.reshape(-1, 3)
    pts = [None] * len(keys); nrm = [None] * len(keys)
    for i in range(nl):
        j = kidx[i]
        if pts[j] is None:
            d = pc[lp[i]] - co[i]; dl = float(np.linalg.norm(d))
            step = min(0.4 * dl, 0.25) / dl if dl > 1e-6 else 0.0
            pts[j] = Vector(co[i] + d * step); nrm[j] = Vector(cn[i]).normalized()
    Vl = [Vector(v) for v in vco]
    Fl = [tuple(p.vertices) for p in me.polygons]
    ao = bake_ao(Vl, Fl, pts, nrm, radius, M.ground)
    aol = ao[kidx]
    # ---- colours
    part_of = np.array([MAT[k][0] for k in MATS], np.float32)
    grad_of = np.array([MAT[k][3] for k in MATS], np.float32)
    base = np.array([M.pal(k) if MAT[k][1] in ('p1', 'p2', 'p1d', 'p2d') else MAT[k][1] for k in MATS], np.float32)
    mode_of = np.array([['grime', 'keep', 'white'].index(MAT[k][2]) for k in MATS])
    mt = mats[lp]
    hgt = np.maximum(bz1[lp] - bz0[lp], 1e-4)
    rel = np.clip((co[:, 2] - bz0[lp]) / hgt, 0, 1)
    g = 1.0 - grad_of[mt] * (1 - rel)
    sh = shade[lp] * g * (1.0 - M.ao * (1.0 - aol))
    col = np.clip(base[mt] * sh[:, None], 0, 1)
    cols = np.concatenate([col, np.ones((nl, 1), np.float32)], 1)
    # ---- UVs
    out = np.tile(np.array(WHITE_UV, np.float32), (nl, 1))
    mode = mode_of[mt]
    tl = tiles[lp]
    keep = (tl >= 0)
    for tid in np.unique(tl[keep]):
        sel = tl == tid
        u0, v0, u1, v1 = REG[TILES[tid]]
        s = np.clip(uv[sel, 0], 0, 1); t = np.clip(uv[sel, 1], 0, 1)
        out[sel, 0] = u0 + s * (u1 - u0); out[sel, 1] = v0 + t * (v1 - v0)
    gm = (mode == 0) & ~keep
    if gm.any():
        n = pn[lp]
        ax = np.abs(n)
        top = (ax[:, 2] >= ax[:, 0]) & (ax[:, 2] >= ax[:, 1])
        front = ~top & (ax[:, 1] >= ax[:, 0])
        side = ~top & ~front
        for mp, sel, (ia, ib) in (('top', top, (0, 1)), ('front', front, (0, 2)), ('side', side, (1, 2))):
            sel = sel & gm
            if not sel.any(): continue
            a0, a1, b0, b1 = M.maps[mp]
            u0, v0, u1, v1 = REG[M.name + '.' + mp]
            s = np.clip((co[sel, ia] - a0) / (a1 - a0), 0, 1); t = np.clip((co[sel, ib] - b0) / (b1 - b0), 0, 1)
            out[sel, 0] = u0 + s * (u1 - u0); out[sel, 1] = v0 + t * (v1 - v0)
    parts = np.zeros((nl, 2), np.float32); parts[:, 0] = part_of[mt]
    colattr = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = colattr; me.color_attributes.render_color_index = 0
    colattr.data.foreach_set('color_srgb', cols.ravel())
    me.uv_layers['UVMap'].data.foreach_set('uv', out.ravel())
    pl = me.uv_layers.new(name='Part'); pl.data.foreach_set('uv', parts.ravel())
    for a in ('mat', 'sm', 'tile', 'shade', 'bz0', 'bz1'):
        if a in me.attributes: me.attributes.remove(me.attributes[a])
