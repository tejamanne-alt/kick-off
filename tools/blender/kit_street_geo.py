# Geometry pieces for kit_street.py (the street kit). Every piece is a bmesh with a face int layer
# 'mat' (an index into MATS), a face int layer 'uvk' (how its UVs are made, see below) and a loop UV
# layer. Forms are rounded boxes on explicit grids, lathes and sweeps, as in car.py.
#   uvk 0: the material decides (projected grime map or the atlas' white corner), at assembly
#   uvk 1: keep the UV set here (signs, icons, wood, stripes)
#   uvk 2: cylindrical grime: uv.x holds the unwrapped angle (0..1, periodic), uv.y is unused
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
from kit_street_atlas import reg_uv, WHITE_UV

PI = math.pi
MATS, MID = [], {}


def mid(name):
    i = MID.get(name)
    if i is None:
        i = MID[name] = len(MATS); MATS.append(name)
    return i


def new_bm():
    bm = bmesh.new()
    bm.faces.layers.int.new('mat'); bm.faces.layers.int.new('uvk')
    bm.loops.layers.uv.new('UVMap')
    return bm


def lay(bm):
    L = bm.faces.layers.int
    if 'mat' not in L: L.new('mat')
    if 'uvk' not in L: L.new('uvk')
    if 'UVMap' not in bm.loops.layers.uv: bm.loops.layers.uv.new('UVMap')
    return L['mat'], L['uvk'], bm.loops.layers.uv['UVMap']


def bm_from(V, F, mats):
    bm = new_bm(); lm, lk, lu = lay(bm)
    vs = [bm.verts.new(tuple(map(float, v))) for v in V]
    out = []
    for f, m in zip(F, mats):
        try:
            face = bm.faces.new([vs[i] for i in f])
            face[lm] = m if isinstance(m, int) else mid(m); face[lk] = 0
            for l in face.loops: l[lu].uv = WHITE_UV
            out.append(face)
        except ValueError:
            out.append(None)
    bm.normal_update()
    return bm, out


def merge(dst, src):
    lm, lk, lu = lay(dst); sm, sk, su = lay(src)
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[lm] = f[sm]; nf[lk] = f[sk]
        for a, b in zip(f.loops, nf.loops): b[lu].uv = a[su].uv
    return dst


def join(bms):
    out = new_bm()
    for b in bms: merge(out, b)
    return out


def xform(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if M.to_3x3().determinant() < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def T(x, y=0.0, z=0.0):
    if not isinstance(x, (int, float)): return Matrix.Translation(Vector(x))
    return Matrix.Translation((x, y, z))


def R(angle, axis):
    return Matrix.Rotation(angle, 4, axis)


def S(sx, sy, sz):
    return Matrix.Diagonal((sx, sy, sz, 1.0))


def setmat(bm, name, faces=None):
    lm = lay(bm)[0]; i = mid(name)
    for f in (bm.faces if faces is None else faces): f[lm] = i
    return bm


def mat_of(bm, f):
    return MATS[f[lay(bm)[0]]]


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update(); return bm


def frame(origin, z, up=(0, 0, 1)):
    """A matrix at origin whose local Z is z and whose local Y leans toward up."""
    z = Vector(z).normalized(); up = Vector(up)
    x = up.cross(z)
    if x.length < 1e-6: x = Vector((1, 0, 0)).cross(z)
    if x.length < 1e-6: x = Vector((0, 1, 0)).cross(z)
    x.normalize(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin)
    return M


def faces_facing(bm, d, cos=0.7):
    d = Vector(d).normalized(); bm.normal_update()
    return [f for f in bm.faces if f.normal.dot(d) > cos]


def delete_faces(bm, faces):
    bmesh.ops.delete(bm, geom=list(faces), context='FACES')
    return bm


# ---------------------------------------------------------------- primitives
def _lines(a0, a1, r, seg, extra):
    cs = {round(a0, 6), round(a1, 6)}
    for o in {0: [], 1: [1.0], 2: [1.0, 0.586], 3: [1.0, 0.732, 0.423]}[seg]:
        cs.add(round(a0 + r * o, 6)); cs.add(round(a1 - r * o, 6))
    for e in extra:
        if a0 + 1e-4 < e < a1 - 1e-4: cs.add(round(e, 6))
    return sorted(cs)


def rbox(lo, hi, r, seg=(1, 1, 1), extra=((), (), ()), skip=()):
    """A rounded box on an explicit grid (see car.py). Returns (P, X, faces, tags (axis, sign))."""
    lo = np.array(lo, float); hi = np.array(hi, float); r = np.maximum(np.array(r, float), 1e-5)
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
    return P, X, F, Tg


def rpiece(lo, hi, r, mat, seg=(1, 1, 1), extra=((), (), ()), skip=(), deform=None, mats=None):
    """mats: optional fn(axis, sign, face centre) -> material name."""
    P, X, F, Tg = rbox(lo, hi, r, seg, extra, skip)
    if deform is not None: X = deform(X)
    if mats:
        ml = [mats(a, s, P[f].mean(axis=0)) for f, (a, s) in zip(F, Tg)]
    else:
        ml = [mat] * len(F)
    bm, _ = bm_from(X, F, ml)
    return bm


def lathe(prof, n, mats, phase=0.5, arc=None):
    """A surface of revolution about local Z. prof: (radius, height) from one end to the other
    (r = 0 makes a pole); faces point outward when the profile starts at the -Z end.
    mats: one material name, or one per profile segment. arc: (a0, a1) radians for an open part.
    Returns (bm, [(face, segment, i)])."""
    V = []; rings = []
    closed = arc is None
    cols = n if closed else n + 1
    for (r, h) in prof:
        if r < 1e-7:
            rings.append([len(V)]); V.append((0.0, 0.0, h))
        else:
            ids = list(range(len(V), len(V) + cols)); rings.append(ids)
            for i in range(cols):
                a = 2 * PI * (i + phase) / n if closed else arc[0] + (arc[1] - arc[0]) * i / n
                V.append((r * math.cos(a), r * math.sin(a), h))
    F = []; M = []; tags = []
    for si in range(len(prof) - 1):
        A, B = rings[si], rings[si + 1]
        if len(A) == 1 and len(B) == 1: continue
        for i in range(n):
            i2 = (i + 1) % cols if closed else i + 1
            if len(A) == 1: f = [A[0], B[i2], B[i]]
            elif len(B) == 1: f = [A[i], A[i2], B[0]]
            else: f = [A[i], A[i2], B[i2], B[i]]
            F.append(f); M.append(mats[si] if isinstance(mats, (list, tuple)) else mats); tags.append((si, i))
    bm, faces = bm_from(V, F, M)
    return bm, [(f, s, i) for f, (s, i) in zip(faces, tags) if f is not None]


def sweep(path, up, section, mat, caps=True, scales=None, closed=True):
    """Rings of a 2D section (u along the normal, v along the binormal) along a polyline.
    up: a vector or fn(i, point, tangent) -> the ring's normal direction."""
    n = len(path); m = len(section); V = []
    for i, p in enumerate(path):
        p = Vector(p)
        if i == 0: t = Vector(path[1]) - p
        elif i == n - 1: t = p - Vector(path[-2])
        else: t = (Vector(path[i + 1]) - p).normalized() + (p - Vector(path[i - 1])).normalized()
        t.normalize()
        u = Vector(up(i, p, t) if callable(up) else up)
        N = (u - t * u.dot(t)).normalized(); B = t.cross(N)
        sc = scales[i] if scales else 1.0
        if isinstance(sc, (int, float)): sc = (sc, sc)
        for (a, b) in section: V.append(p + N * (a * sc[0]) + B * (b * sc[1]))
    F = []
    for i in range(n - 1):
        for k in range(m if closed else m - 1):
            k2 = (k + 1) % m
            F.append([i * m + k, i * m + k2, (i + 1) * m + k2, (i + 1) * m + k])
    if caps and closed:
        F.append([k for k in reversed(range(m))]); F.append([(n - 1) * m + k for k in range(m)])
    bm, _ = bm_from(V, F, [mat] * len(F))
    return fix_normals(bm) if closed else bm


def circle_sec(r, sides, phase=0.0, sy=1.0):
    return [(r * math.cos(2 * PI * (k + phase) / sides), sy * r * math.sin(2 * PI * (k + phase) / sides)) for k in range(sides)]


def tube(path, radius, mat, sides=6, caps=True, scales=None):
    def up(i, p, t):
        return Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    return sweep(path, up, circle_sec(radius, sides, 0.5), mat, caps, scales)


def cbox(size, r, mat, seg=1, at=None):
    """A chamfered box (size = full x, y, z), centred on the origin (or on at)."""
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    r = min(r, min(size) * 0.45)
    if r > 1e-5:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    setmat(bm, mat)
    lm, lk, lu = lay(bm)
    for f in bm.faces:
        for l in f.loops: l[lu].uv = WHITE_UV
    fix_normals(bm)
    if at is not None: xform(bm, T(at))
    return bm


def prism(pts, depth, mat, bevel=0.0):
    """A flat slab: the polygon pts (x, z) extruded along +Y by depth (front face at y = 0, facing -Y)."""
    bm = new_bm()
    vs = [bm.verts.new((x, 0.0, z)) for x, z in pts]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.y > 0: f.normal_flip()
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, depth, 0)), verts=nv)
    fix_normals(bm)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
    setmat(bm, mat)
    lm, lk, lu = lay(bm)
    for f in bm.faces:
        for l in f.loops: l[lu].uv = WHITE_UV
    return fix_normals(bm)


def ball(r, mat, n=8, rings=4, squash=1.0, lump=0.0, seed=0, at=None):
    """A low sphere (fruit, flower heads, foliage lumps). lump > 0 jitters the radius."""
    rng = np.random.default_rng(seed)
    prof = []
    for k in range(rings + 1):
        a = -PI / 2 + PI * k / rings
        prof.append((r * math.cos(a) if 0 < k < rings else 0.0, r * squash * math.sin(a)))
    bm, _ = lathe(prof, n, mat, phase=rng.random())
    if lump > 0:
        for v in bm.verts:
            v.co *= 1.0 + lump * (rng.random() - 0.5) * 2
    bm.normal_update()
    if at is not None: xform(bm, T(at))
    return bm


def boolean_diff(bm, cutter):
    """bm minus cutter (EXACT). The cut faces take the cutter's materials and uvk 0."""
    me = bpy.data.meshes.new('tmp'); bm.to_mesh(me); ob = bpy.data.objects.new('tmp', me)
    bpy.context.scene.collection.objects.link(ob)
    cm = bpy.data.meshes.new('cut'); cutter.to_mesh(cm); co = bpy.data.objects.new('cut', cm)
    bpy.context.scene.collection.objects.link(co)
    m = ob.modifiers.new('b', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.object = co
    for x in bpy.context.scene.objects: x.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    out = bmesh.new(); out.from_mesh(ob.data); lay(out)
    bpy.data.objects.remove(ob); bpy.data.objects.remove(co)
    bpy.data.meshes.remove(me); bpy.data.meshes.remove(cm)
    out.normal_update()
    return out


# ---------------------------------------------------------------- UVs
def uv_planar(bm, faces, region, fn, margin=None):
    """UVs from fn(co) -> (s, t) in [0, 1] inside an atlas region; kept at assembly."""
    lm, lk, lu = lay(bm)
    for f in faces:
        f[lk] = 1
        for l in f.loops:
            s, t = fn(l.vert.co)
            l[lu].uv = reg_uv(region, s, t, margin)
    return bm


def uv_white(bm, faces=None):
    lm, lk, lu = lay(bm)
    for f in (bm.faces if faces is None else faces):
        f[lk] = 1
        for l in f.loops: l[lu].uv = WHITE_UV
    return bm


def uv_long(bm, faces, region, margin=None, flip=False):
    """Box UVs normalised to the piece's bounds with s along its longest axis (wood grain)."""
    vs = [v.co for v in bm.verts]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    ext = [hi[i] - lo[i] for i in range(3)]
    L = max(range(3), key=lambda i: ext[i])
    bm.normal_update()
    lm, lk, lu = lay(bm)
    for f in faces:
        f[lk] = 1
        nax = max(range(3), key=lambda i: abs(f.normal[i]))
        others = [i for i in range(3) if i != nax]
        if L in others:
            a = L; b = [i for i in others if i != L][0]
        else:
            a, b = others
        for l in f.loops:
            co = l.vert.co
            s = (co[a] - lo[a]) / max(ext[a], 1e-4); t = (co[b] - lo[b]) / max(ext[b], 1e-4)
            if flip: s, t = t, s
            l[lu].uv = reg_uv(region, s, t, margin)
    return bm


def _angle01(co, ctr):
    return (math.atan2(co[1] - ctr[1], co[0] - ctr[0]) / (2 * PI)) % 1.0


def _unwrap(fc, a):
    d = a - fc
    if d > 0.5: d -= 1.0
    if d < -0.5: d += 1.0
    return fc + d


def uv_cyl(bm, faces, region, ctr=(0, 0), tfn=None, off=0.0, margin=None, reps=1.0):
    """Cylindrical UVs about a vertical axis through ctr: s = the angle (periodic, unwrapped per
    face so seams never stretch), t = tfn(co)."""
    lm, lk, lu = lay(bm)
    for f in faces:
        f[lk] = 1
        c = f.calc_center_median()
        fc = (_angle01(c, ctr) * reps + off) % 1.0
        for l in f.loops:
            a = _unwrap(fc, (_angle01(l.vert.co, ctr) * reps + off) % 1.0)
            l[lu].uv = reg_uv(region, a, tfn(l.vert.co) if tfn else 0.5, margin)
    return bm


def grime_cyl(bm, faces=None, ctr=(0, 0), off=0.0):
    """Mark faces for the cylindrical grime projection (uvk 2): the unwrapped angle goes in uv.x.
    Call it before the piece is moved (ctr is its local axis)."""
    lm, lk, lu = lay(bm)
    for f in (bm.faces if faces is None else faces):
        if abs(f.normal.z) > 0.8: continue
        f[lk] = 2
        c = f.calc_center_median()
        fc = (_angle01(c, ctr) + off) % 1.0
        for l in f.loops:
            l[lu].uv = (_unwrap(fc, (_angle01(l.vert.co, ctr) + off) % 1.0), 0.0)
    return bm
