# Mesh layer of the buildings kit (kit_buildings.py): bmesh pieces that carry a material per face,
# primitives (boxes, chamfered boxes, lathes, sweeps, mitred bands, extruded outlines, blobs),
# the atlas layout, and the conversion of a building's pieces into one mesh object with vertex
# colours, atlas UVs (UV0), recolour part ids (UV1.x) and soft custom normals.
#
# Every piece is a bmesh with face layers
#   mat    index into MATS        sm     0 sharp above 50 degrees, 1 always smooth, 2 always sharp
#   shade  baked brightness       bx0..bz1  the piece's bounds (gradients, 'piece' UVs)
# and a loop UV layer 'UVMap' that 'keep' materials fill themselves.
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Matrix
import kit_lib as K

PI = math.pi
AT = 2048                      # atlas size (pixels)
WHITE_UV = K.WHITE_UV


def s2l(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


# ---------------------------------------------------------------- materials
# name: (part, colour, uv, grad)
#   colour  a key of the building's palette, or an sRGB triple
#   uv      grime  the building's projected wall maps by facing (front / left / right), white otherwise
#           roof   the building's top-down roof map
#           piece  the generic wear map, normalised to the piece's bounds
#           keep   set by the piece itself (glass, wood, brick, produce, signs ...)
#           white  the atlas' plain corner
#   grad    how much darker the bottom of the piece is than its top (0..1)
MAT = {
    'wall': (1, 'wall', 'grime', 0.0), 'reveal': (1, 'wall', 'white', 0.0), 'wallw': (1, 'wall', 'white', 0.0),
    'accent': (2, 'accent', 'grime', 0.0), 'accentp': (2, 'accent', 'piece', 0.0), 'accentw': (2, 'accent', 'white', 0.15), 'accentk': (2, 'accent', 'keep', 0.0),
    'roof': (3, 'roof', 'roof', 0.0), 'roofw': (3, 'roof', 'white', 0.0), 'roofp': (3, 'roof', 'piece', 0.0), 'roofb': (3, 'roof', 'roofb', 0.0),
    'trim': (0, 'trim', 'grime', 0.0), 'trimw': (0, 'trim', 'white', 0.0), 'trimp': (0, 'trim', 'piece', 0.0),
    'stone': (0, 'stone', 'grime', 0.0), 'conc': (0, 'conc', 'piece', 0.0), 'concw': (0, 'conc', 'white', 0.1),
    'frame': (0, 'frame', 'white', 0.0), 'soffit': (0, 'soffit', 'white', 0.0),
    'brick': (0, (1, 1, 1), 'keep', 0.0), 'glass': (0, (1, 1, 1), 'keep', 0.0), 'wood': (0, (1, 1, 1), 'keep', 0.1),
    'tex': (0, (1, 1, 1), 'keep', 0.0),
    'woodc': (0, (0.70, 0.50, 0.33), 'white', 0.2), 'woodd': (0, (0.46, 0.32, 0.22), 'white', 0.2),
    'metal': (0, (0.62, 0.64, 0.66), 'white', 0.0), 'metald': (0, (0.27, 0.28, 0.30), 'white', 0.0),
    'galv': (0, (0.74, 0.76, 0.77), 'piece', 0.0), 'galvw': (0, (0.74, 0.76, 0.77), 'white', 0.0),
    'pipe': (0, 'pipe', 'white', 0.0),
    'dark': (0, (0.11, 0.10, 0.11), 'white', 0.0), 'interior': (0, (0.36, 0.30, 0.27), 'white', 0.35),
    'leaf': (0, (0.38, 0.58, 0.30), 'white', 0.45), 'leafl': (0, (0.52, 0.70, 0.34), 'white', 0.4),
    'leafd': (0, (0.25, 0.44, 0.27), 'white', 0.45), 'leafy': (0, (0.70, 0.74, 0.34), 'white', 0.4),
    'fl1': (0, (0.97, 0.56, 0.64), 'white', 0.1), 'fl2': (0, (0.92, 0.33, 0.30), 'white', 0.1),
    'fl3': (0, (0.99, 0.83, 0.36), 'white', 0.1), 'fl4': (0, (0.97, 0.96, 0.91), 'white', 0.1),
    'fl5': (0, (0.74, 0.58, 0.88), 'white', 0.1), 'fl6': (0, (0.98, 0.62, 0.30), 'white', 0.1),
    'pot': (0, (0.78, 0.47, 0.34), 'white', 0.3), 'pot2': (0, (0.86, 0.84, 0.78), 'white', 0.3),
    'pot3': (0, (0.36, 0.50, 0.52), 'white', 0.3), 'soil': (0, (0.32, 0.24, 0.19), 'white', 0.0),
    'cloth1': (0, (0.90, 0.42, 0.38), 'white', 0.15), 'cloth2': (0, (0.42, 0.60, 0.80), 'white', 0.15),
    'cloth3': (0, (0.98, 0.86, 0.46), 'white', 0.15), 'cloth4': (0, (0.97, 0.96, 0.92), 'white', 0.15),
    'cloth5': (0, (0.58, 0.80, 0.70), 'white', 0.15), 'cloth6': (0, (0.95, 0.66, 0.72), 'white', 0.15),
    'cream': (0, (0.96, 0.92, 0.82), 'white', 0.0), 'creamp': (0, (0.96, 0.92, 0.82), 'piece', 0.0),
    'lamp': (0, (1.0, 0.94, 0.74), 'white', 0.0), 'brass': (0, (0.82, 0.66, 0.34), 'white', 0.0),
    'black': (0, (0.14, 0.14, 0.15), 'white', 0.0), 'rubber': (0, (0.18, 0.18, 0.19), 'white', 0.0),
    'yellow': (0, (0.96, 0.76, 0.26), 'white', 0.0), 'red': (0, (0.82, 0.24, 0.20), 'white', 0.1),
    'white': (0, (0.93, 0.93, 0.91), 'white', 0.1), 'whitep': (0, (0.93, 0.93, 0.91), 'piece', 0.0),
    'tank': (0, (0.40, 0.58, 0.72), 'piece', 0.0), 'ic1': (0, (0.86, 0.30, 0.26), 'white', 0.0),
    'ic2': (0, (0.97, 0.60, 0.22), 'white', 0.0), 'ic3': (0, (0.98, 0.84, 0.36), 'white', 0.0),
    'ic4': (0, (0.44, 0.66, 0.32), 'white', 0.0), 'ic5': (0, (0.62, 0.42, 0.28), 'white', 0.0),
    'ic6': (0, (0.30, 0.36, 0.52), 'white', 0.0), 'orange': (0, (0.96, 0.58, 0.20), 'white', 0.2),
    'green': (0, (0.36, 0.60, 0.30), 'white', 0.3), 'melon': (0, (1, 1, 1), 'keep', 0.25),
    'purple': (0, (0.50, 0.30, 0.52), 'white', 0.2), 'bread': (0, (0.88, 0.62, 0.34), 'white', 0.3),
    'crust': (0, (0.70, 0.42, 0.20), 'white', 0.2), 'tomato': (0, (0.88, 0.28, 0.22), 'white', 0.2),
}
MATS = list(MAT)
MID = {n: i for i, n in enumerate(MATS)}
import os as _os
PROFILE = bool(_os.environ.get('KIT_PROFILE'))
BOUNDS = ('bx0', 'bx1', 'by0', 'by1', 'bz0', 'bz1')


# ---------------------------------------------------------------- atlas layout
REG = {}          # name -> (u0, v0, u1, v1)


def reg_px(name):
    u0, v0, u1, v1 = REG[name]
    return int(round(u0 * AT)), int(round((1 - v1) * AT)), int(round(u1 * AT)), int(round((1 - v0) * AT))


def reg_uv(name, s, t, margin=0.0):
    u0, v0, u1, v1 = REG[name]
    s = min(max(s, 0.0), 1.0); t = min(max(t, 0.0), 1.0)
    s = margin + s * (1 - 2 * margin); t = margin + t * (1 - 2 * margin)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


def allocate(bottom, maps, pad=6):
    """bottom: [(name, w, h)] tiles packed left to right along the atlas' bottom edge (the plain
    white tile goes last, in the corner). maps: [(name, w, h)] shelf-packed above them, tallest
    first. Each region keeps `pad` pixels of bleed around it."""
    REG.clear()
    x = 0; ybot = AT
    hrow = max(h for _, _, h in bottom) + 2 * pad
    for name, w, h in bottom:
        if name == 'white':
            x0 = AT - w
        else:
            x0 = x + pad; x = x0 + w + pad
        y0 = AT - pad - h
        REG[name] = (x0 / AT, (AT - (y0 + h)) / AT, (x0 + w) / AT, (AT - y0) / AT)
    limit = AT - hrow
    items = sorted(maps, key=lambda r: -r[2])
    sx = 0; sy = 0; sh = 0
    for name, w, h in items:
        W2, H2 = w + 2 * pad, h + 2 * pad
        if sx + W2 > AT:
            sx = 0; sy += sh; sh = 0
        if sy + H2 > limit:
            raise RuntimeError('atlas full at ' + name)
        x0, y0 = sx + pad, sy + pad
        REG[name] = (x0 / AT, (AT - (y0 + h)) / AT, (x0 + w) / AT, (AT - y0) / AT)
        sx += W2; sh = max(sh, H2)
    return sy + sh


# ---------------------------------------------------------------- bmesh pieces
def new_bm():
    bm = bmesh.new()
    bm.faces.layers.int.new('mat'); bm.faces.layers.int.new('sm'); bm.faces.layers.float.new('shade')
    for k in BOUNDS: bm.faces.layers.float.new(k)
    bm.loops.layers.uv.new('UVMap')
    return bm


def L(bm):
    fl = bm.faces.layers
    return fl.int['mat'], fl.int['sm'], fl.float['shade'], bm.loops.layers.uv['UVMap']


def bm_from(V, F, mat, sm=0, shade=1.0):
    """Faces F over vertices V; mat is one name or one per face."""
    bm = new_bm(); lm, ls, lsh, lu = L(bm)
    vs = [bm.verts.new(tuple(map(float, v))) for v in V]
    out = []
    for k, f in enumerate(F):
        try:
            face = bm.faces.new([vs[i] for i in f])
        except ValueError:
            out.append(None); continue
        face[lm] = MID[mat if isinstance(mat, str) else mat[k]]; face[ls] = sm; face[lsh] = shade
        for l in face.loops: l[lu].uv = WHITE_UV
        out.append(face)
    bm.normal_update()
    return bm, out


def merge(dst, src):
    lm, ls, lsh, lu = L(dst); sm_, ss, ssh, su = L(src)
    db = [dst.faces.layers.float[k] for k in BOUNDS]; sb = [src.faces.layers.float[k] for k in BOUNDS]
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[lm] = f[sm_]; nf[ls] = f[ss]; nf[lsh] = f[ssh]
        for a, b in zip(db, sb): nf[a] = f[b]
        for a, b in zip(f.loops, nf.loops): b[lu].uv = a[su].uv
    return dst


def xform(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if M.to_3x3().determinant() < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def setmat(bm, name, faces=None):
    lm = L(bm)[0]
    for f in (bm.faces if faces is None else faces): f[lm] = MID[name]
    return bm


def setsm(bm, v):
    ls = L(bm)[1]
    for f in bm.faces: f[ls] = v
    return bm


def setshade(bm, v, faces=None):
    lsh = L(bm)[2]
    for f in (bm.faces if faces is None else faces): f[lsh] = v
    return bm


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.normal_update(); return bm


def faces_facing(bm, d, cos=0.7):
    d = Vector(d).normalized(); bm.normal_update()
    return [f for f in bm.faces if f.normal.dot(d) > cos]


def basis(origin, x, y, z):
    M = Matrix((Vector(x), Vector(y), Vector(z))).transposed().to_4x4(); M.translation = Vector(origin); return M


def frame(origin, z, up=(0, 0, 1)):
    """A matrix at origin whose local Z is z and whose local Y leans toward up."""
    z = Vector(z).normalized(); up = Vector(up)
    x = up.cross(z)
    if x.length < 1e-6: x = Vector((1, 0, 0)).cross(z)
    x.normalize(); y = z.cross(x)
    return basis(origin, x, y, z)


def T(x, y=None, z=None):
    if y is None: return Matrix.Translation(Vector(x))
    return Matrix.Translation(Vector((x, y, z)))


def R(angle, axis):
    return Matrix.Rotation(angle, 4, axis)


def S(sx, sy, sz):
    return Matrix.Diagonal((sx, sy, sz, 1.0))


def uv_fn(bm, faces, region, fn, margin=0.0):
    """UVs for faces from fn(co) -> (s, t) in [0, 1] inside an atlas region."""
    lu = L(bm)[3]
    for f in faces:
        for l in f.loops:
            l[lu].uv = reg_uv(region, *fn(l.vert.co), margin)


def uv_box(bm, faces, region, margin=0.02, fit=None):
    """Box-projected UVs normalised to the piece's bounds (or to fit = (lo, hi))."""
    if fit is None:
        vs = [v.co for v in bm.verts]
        lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    else:
        lo, hi = fit
    lu = L(bm)[3]; bm.normal_update()
    for f in faces:
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv(region, (co[a] - lo[a]) / max(hi[a] - lo[a], 1e-4), (co[b] - lo[b]) / max(hi[b] - lo[b], 1e-4), margin)


# ---------------------------------------------------------------- primitives
def box(lo, hi, mat, skip=(), sm=0):
    """An axis-aligned box; skip: faces left out, as '-x', '+x', '-y', '+y', '-z', '+z'."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    F = {'-z': (0, 3, 2, 1), '+z': (4, 5, 6, 7), '-y': (0, 1, 5, 4), '+y': (2, 3, 7, 6), '-x': (3, 0, 4, 7), '+x': (1, 2, 6, 5)}
    faces = [f for k, f in F.items() if k not in skip]
    bm, _ = bm_from(V, faces, mat, sm)
    return bm


def cbox(size, r, mat, seg=1, sm=0):
    """A chamfered box (size = full x, y, z) centred on the origin."""
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    r = min(r, min(size) * 0.45)
    if r > 1e-4:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    lm, ls, lsh, lu = L(bm)
    for f in bm.faces:
        f[lm] = MID[mat]; f[ls] = sm; f[lsh] = 1.0
        for l in f.loops: l[lu].uv = WHITE_UV
    return fix_normals(bm)


def fbox(lo, hi, r, mat, sm=0, back=False):
    """A box seen from the front (+Z): the front face's edges chamfered by r, no back face unless
    asked (18 triangles; casings, sills, lintels, planters, steps)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    r = min(r, (x1 - x0) * 0.45, (y1 - y0) * 0.45, (z1 - z0) * 0.9)
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1 - r), (x1, y0, z1 - r), (x1, y1, z1 - r), (x0, y1, z1 - r),
         (x0 + r, y0 + r, z1), (x1 - r, y0 + r, z1), (x1 - r, y1 - r, z1), (x0 + r, y1 - r, z1)]
    F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
         (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11), (8, 9, 10, 11)]
    if back: F.append((3, 2, 1, 0))
    bm, _ = bm_from(V, F, mat, sm)
    return fix_normals(bm) if back else _orient_out(bm, ((x0 + x1) / 2, (y0 + y1) / 2, z0 - (z1 - z0)))


def _orient_out(bm, c):
    c = Vector(c)
    for f in bm.faces:
        if f.normal.dot(f.calc_center_median() - c) < 0: f.normal_flip()
    bm.normal_update()
    return bm


def prism(pts, z0, z1, mat, caps=(False, True), sm=0):
    """A vertical prism: a 2D outline (x, y) from z0 to z1, sides and the chosen caps."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0: pts = list(reversed(pts))
    V = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    if caps[0]: F.append(tuple(reversed(range(n))))
    if caps[1]: F.append(tuple(range(n, 2 * n)))
    bm, _ = bm_from(V, F, mat, sm)
    return bm


def cbox2(lo, hi, r, mat, seg=1, sm=0):
    lo = Vector(lo); hi = Vector(hi)
    bm = cbox(tuple(hi - lo), r, mat, seg, sm)
    return xform(bm, T((lo + hi) / 2))


def lathe(prof, n, mats, phase=0.5, sm=0):
    """A surface of revolution about local Z. prof: (radius, height) from bottom to top (r = 0
    makes a pole). mats: one per profile segment (or one name). Returns (bm, [(face, seg, i)])."""
    V = []; rings = []
    for (r, h) in prof:
        if r < 1e-7:
            rings.append([len(V)]); V.append((0.0, 0.0, h))
        else:
            ids = list(range(len(V), len(V) + n)); rings.append(ids)
            for i in range(n):
                a = 2 * PI * (i + phase) / n
                V.append((r * math.cos(a), r * math.sin(a), h))
    F = []; M = []; tags = []
    for si in range(len(prof) - 1):
        A, B = rings[si], rings[si + 1]
        if len(A) == 1 and len(B) == 1: continue
        for i in range(n):
            i2 = (i + 1) % n
            if len(A) == 1: f = [A[0], B[i2], B[i]]
            elif len(B) == 1: f = [A[i], A[i2], B[0]]
            else: f = [A[i], A[i2], B[i2], B[i]]
            F.append(f); M.append(mats if isinstance(mats, str) else mats[si]); tags.append((si, i))
    bm, faces = bm_from(V, F, M, sm)
    return bm, [(f, s, i) for f, (s, i) in zip(faces, tags) if f is not None]


def cap_lathe(prof, n, mats, phase=0.5, sm=0):
    return lathe(prof, n, mats, phase, sm)[0]


def sweep(path, up, section, mat, caps=True, scales=None, sm=0):
    """Rings of a closed 2D section (a along the normal, b along the binormal) along a polyline.
    up: a vector or fn(i, point, tangent) giving each ring's normal direction."""
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
        for (a, b) in section: V.append(p + N * (a * sc) + B * (b * sc))
    F = []
    for i in range(n - 1):
        for k in range(m):
            k2 = (k + 1) % m
            F.append([i * m + k, i * m + k2, (i + 1) * m + k2, (i + 1) * m + k])
    if caps:
        F.append([k for k in reversed(range(m))]); F.append([(n - 1) * m + k for k in range(m)])
    bm, _ = bm_from(V, F, mat, sm)
    return fix_normals(bm)


def tube(path, radius, mat, sides=6, caps=True, sm=1):
    sec = [(radius * math.cos(2 * PI * (k + 0.5) / sides), radius * math.sin(2 * PI * (k + 0.5) / sides)) for k in range(sides)]

    def up(i, p, t):
        return Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    bm = sweep(path, up, sec, mat, caps)
    lsm = L(bm)[1]
    for f in bm.faces: f[lsm] = sm
    # caps stay sharp
    if caps:
        for f in bm.faces:
            if len(f.verts) > 4: f[lsm] = 0
    return bm


def band(path, profile, mat, closed=False, caps=True, sm=0, mats=None):
    """A mitred extrusion along a 2D polyline (x, y) on the ground plan: profile is a list of
    (out, z), out measured outward (to the right of the direction of travel, i.e. (dy, -dx)),
    from the bottom at the wall to the top at the wall. mats: one per profile segment."""
    P = [Vector((p[0], p[1], 0.0)) for p in path]
    n = len(P)
    nrm = []
    for i in range(n - 1 if not closed else n):
        a, b = P[i], P[(i + 1) % n]
        d = (b - a).normalized(); nrm.append(Vector((d.y, -d.x, 0)))
    miters = []
    for i in range(n):
        if closed:
            n0, n1 = nrm[i - 1], nrm[i % len(nrm)]
        else:
            n0 = nrm[max(i - 1, 0)]; n1 = nrm[min(i, len(nrm) - 1)]
        m = (n0 + n1); m = m / max(m.dot(n1), 1e-4) if m.length > 1e-6 else n1
        miters.append(m)
    m = len(profile)
    V = []
    for i in range(n):
        for (o, z) in profile:
            V.append(P[i] + miters[i] * o + Vector((0, 0, z)))
    F = []; FM = []
    segs = range(n) if closed else range(n - 1)
    for i in segs:
        i2 = (i + 1) % n
        for k in range(m - 1):
            # bottom-to-top profile on the right of travel: (i,k) (i2,k) (i2,k+1) (i,k+1) faces out
            F.append([i * m + k, i2 * m + k, i2 * m + k + 1, i * m + k + 1]); FM.append(mats[k] if mats else mat)
    bm, faces = bm_from(V, F, FM, sm)
    # orient by the expected outward direction
    lu = L(bm)[3]
    for f, (i, k) in zip(faces, [(i, k) for i in segs for k in range(m - 1)]):
        if f is None: continue
        (o0, z0), (o1, z1) = profile[k], profile[k + 1]
        do, dz = o1 - o0, z1 - z0
        exp = nrm[i] * dz + Vector((0, 0, -do))
        if exp.length > 1e-6 and f.normal.dot(exp) < 0: f.normal_flip()
    if caps and not closed:
        bm.verts.ensure_lookup_table()
        lm = L(bm)[0]
        for i, sgn in ((0, -1), (n - 1, 1)):
            vs = [bm.verts[i * m + k] for k in range(m)]
            try:
                f = bm.faces.new(vs)
                f[lm] = MID[mat]
                for l in f.loops: l[lu].uv = WHITE_UV
                d = (P[1] - P[0]) if i == 0 else (P[-1] - P[-2])
                f.normal_update()
                if f.normal.dot(d * sgn) < 0: f.normal_flip()
            except ValueError:
                pass
    bm.normal_update()
    return bm


def extrude_poly(pts, depth, mat, side_mat=None, back=False, sm=0):
    """A 2D outline (x, y) extruded along +Z from 0 to depth (front face at z = depth)."""
    n = len(pts)
    V = [(x, y, 0.0) for x, y in pts] + [(x, y, depth) for x, y in pts]
    # outline orientation: make it counter-clockwise
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(reversed(range(n)))
    F = [[n + i for i in idx]]; M = [mat]
    for j in range(n):
        a, b = idx[j], idx[(j + 1) % n]
        F.append([a, b, n + b, n + a]); M.append(side_mat or mat)
    if back:
        F.append(list(reversed(idx))); M.append(side_mat or mat)
    bm, _ = bm_from(V, F, M, sm)
    return bm


def circle_pts(r, n, cx=0.0, cy=0.0, a0=0.0, sx=1.0, sy=1.0):
    return [(cx + r * sx * math.cos(a0 + 2 * PI * i / n), cy + r * sy * math.sin(a0 + 2 * PI * i / n)) for i in range(n)]


def blob(center, radii, mat, n=7, rings=3, seed=0, jitter=0.12, flat_bottom=0.0):
    """A soft lumpy ellipsoid (leaves, fruit, clumps): fully smooth normals."""
    rng = np.random.default_rng(seed)
    prof = [(0.0, -1.0)]
    for k in range(1, rings + 1):
        a = -PI / 2 + PI * k / (rings + 1)
        prof.append((math.cos(a), math.sin(a)))
    prof.append((0.0, 1.0))
    bm, _ = lathe(prof, n, mat, phase=rng.random(), sm=1)
    for v in bm.verts:
        j = 1 + jitter * (rng.random() * 2 - 1)
        z = v.co.z
        if flat_bottom and z < -1 + flat_bottom * 2: z = max(z, -1 + flat_bottom * 2)
        v.co = Vector((v.co.x * radii[0] * j, v.co.y * radii[1] * j, z * radii[2] * (1 + 0.5 * jitter * (rng.random() * 2 - 1))))
    xform(bm, T(center))
    return bm


# ---------------------------------------------------------------- the building
class Bld:
    def __init__(self, name, W, H, D, RH, pal):
        self.name, self.W, self.H, self.D, self.RH = name, W, H, D, RH
        self.pal = pal
        self.pieces = []
        self.feats = {}            # map name -> [(kind, dict)]
        self.maps = {}             # 'front' / 'left' / 'right' / 'roof' -> (a0, a1, b0, b1) metres
        self.attach = []           # (name, location)
        self.doors = []; self.windows = []; self.lamps = []
        self.prof = {}
        self.rng = np.random.default_rng(sum(ord(c) * (i + 1) for i, c in enumerate(name)))

    def add(self, bm, mat=None, sm=None, shade=None):
        if bm is None or len(bm.faces) == 0: return bm
        lm, ls, lsh, lu = L(bm)
        if mat is not None:
            for f in bm.faces: f[lm] = MID[mat]
        if sm is not None:
            for f in bm.faces: f[ls] = sm
        if shade is not None:
            for f in bm.faces: f[lsh] = shade
        vs = [v.co for v in bm.verts]
        lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
        lb = [bm.faces.layers.float[k] for k in BOUNDS]
        vals = (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
        for f in bm.faces:
            for k, v in zip(lb, vals): f[k] = v
        self.pieces.append(bm)
        if PROFILE:
            import inspect
            st = [f.function for f in inspect.stack()[1:4] if f.function not in ('put', 'add')]
            key = st[0] if st else '?'
            self.prof[key] = self.prof.get(key, 0) + sum(len(f.verts) - 2 for f in bm.faces)
        return bm

    def feat(self, mp, kind, **kw):
        self.feats.setdefault(mp, []).append((kind, kw))

    def col(self, key):
        c = MAT[key][1]
        return self.pal[c] if isinstance(c, str) else c


# ---------------------------------------------------------------- to a mesh object
def to_object(B, sharp_deg=50.0):
    bm = new_bm()
    for p in B.pieces: merge(bm, p)
    for p in B.pieces: p.free()
    B.pieces = []
    bm.normal_update()
    ls = L(bm)[1]
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
    me = bpy.data.meshes.new(B.name); bm.to_mesh(me); bm.free()
    ob = K.new_obj(B.name, me)
    K.activate(ob)
    m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.mode = 'FACE_AREA'; m.weight = 50; m.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    m = ob.modifiers.new('tri', 'TRIANGULATE'); m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'; m.keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    paint_mesh(B, me)
    return ob


def _attr(me, name, n, dtype=np.float32):
    a = np.zeros(n, dtype); me.attributes[name].data.foreach_get('value', a); return a


def paint_mesh(B, me):
    npl = len(me.polygons); nl = len(me.loops); nv = len(me.vertices)
    mats = _attr(me, 'mat', npl, np.int32); shade = _attr(me, 'shade', npl)
    bnd = np.stack([_attr(me, k, npl) for k in BOUNDS], 1)
    pn = np.zeros(npl * 3, np.float32); me.polygons.foreach_get('normal', pn); pn = pn.reshape(-1, 3)
    tot = np.zeros(npl, np.int32); me.polygons.foreach_get('loop_total', tot)
    lp = np.repeat(np.arange(npl), tot)
    lv = np.zeros(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
    co = np.zeros(nv * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)[lv]
    uv = np.zeros(nl * 2, np.float32); me.uv_layers['UVMap'].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    n = pn[lp]; mt = mats[lp]
    part_of = np.array([MAT[k][0] for k in MATS], np.float32)
    mode_of = np.array([['grime', 'roof', 'piece', 'keep', 'white', 'roofb'].index(MAT[k][2]) for k in MATS])
    grad_of = np.array([MAT[k][3] for k in MATS], np.float32)
    base = np.array([B.col(k) for k in MATS], np.float32)
    mode = mode_of[mt]
    out = np.tile(np.array(WHITE_UV, np.float32), (nl, 1))
    out[mode == 3] = uv[mode == 3]

    def proj(mask, mp, a, b):
        if mp not in B.maps or not mask.any(): return
        a0, a1, b0, b1 = B.maps[mp]
        u0, v0, u1, v1 = REG[B.name + '.' + mp]
        s = np.clip((a[mask] - a0) / (a1 - a0), 0.002, 0.998); t = np.clip((b[mask] - b0) / (b1 - b0), 0.002, 0.998)
        out[mask, 0] = u0 + s * (u1 - u0); out[mask, 1] = v0 + t * (v1 - v0)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    g = mode == 0
    front = g & (n[:, 1] < -0.5); right = g & (n[:, 0] > 0.5); left = g & (n[:, 0] < -0.5)
    proj(front, 'front', x, z); proj(right, 'right', y, z); proj(left, 'left', y, z)
    proj(mode == 1, 'roof', x, y)
    proj(mode == 5, 'roofb', x, y)
    # generic wear, normalised to the piece's bounds on the plane it faces
    pm = mode == 2
    if pm.any():
        b = bnd[lp]
        fy = np.abs(n[:, 1]) >= np.abs(n[:, 0])
        s = np.where(fy, (x - b[:, 0]) / np.maximum(b[:, 1] - b[:, 0], 1e-3), (y - b[:, 2]) / np.maximum(b[:, 3] - b[:, 2], 1e-3))
        t = (z - b[:, 4]) / np.maximum(b[:, 5] - b[:, 4], 1e-3)
        up = np.abs(n[:, 2]) > 0.75
        u0, v0, u1, v1 = REG['wear']
        mm = pm & ~up
        out[mm, 0] = u0 + np.clip(s[mm], 0.01, 0.99) * (u1 - u0); out[mm, 1] = v0 + np.clip(t[mm], 0.01, 0.99) * (v1 - v0)
    # colours: base x baked shade x gradients
    f = shade[lp].astype(np.float32)
    b = bnd[lp]
    tz = np.clip((z - b[:, 4]) / np.maximum(b[:, 5] - b[:, 4], 1e-3), 0, 1)
    f *= 1 - grad_of[mt] * (1 - tz)
    wallish = np.isin(mt, [MID['wall'], MID['reveal'], MID['wallw'], MID['stone'], MID['trim']])
    hz = np.clip(z / 2.4, 0, 1); hz = hz * hz * (3 - 2 * hz)
    f = np.where(wallish, f * (0.86 + 0.14 * hz), f)
    down = (n[:, 2] < -0.6) & (mt != MID['glass'])
    f = np.where(down, f * 0.8, f)
    rgb = np.clip(base[mt] * f[:, None], 0, 1)
    cols = np.concatenate([rgb, np.ones((nl, 1), np.float32)], 1)
    me.uv_layers['UVMap'].data.foreach_set('uv', out.ravel())
    part = me.uv_layers.new(name='Part')
    pp = np.zeros((nl, 2), np.float32); pp[:, 0] = part_of[mt]
    part.data.foreach_set('uv', pp.ravel())
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    col.data.foreach_set('color_srgb', cols.ravel())
    me.color_attributes.active_color = col; me.color_attributes.render_color_index = 0
    for k in ('mat', 'sm', 'shade') + BOUNDS:
        if k in me.attributes: me.attributes.remove(me.attributes[k])
