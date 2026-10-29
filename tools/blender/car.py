# Builds one of the original stylized cars for Dribble To School in Blender:
#   blenv/bin/python car.py -- /abs/path/Hatch.fbx --type hatch
# Types: hatch and wagon (parked cars, matching the parked-car colliders), van, pickup and
# fourby (crossing traffic). Writes <Name>.fbx, <Name>.blend, <Name>Atlas.png and <Name>.json
# ({"paint": [r, g, b], "tris": n, ...}) next to the .fbx.
#
# Coordinates: metres, Z up, the car's front faces -Y, wheels resting on z = 0, centred on its
# length and width; the car's own left is +X. Exported like teen.py (FBX_SCALE_ALL, -Z forward,
# Y up), no armature:
#   Body        one mesh: vertex colours times the atlas, one material
#   Wheel.FL/FR/RL/RR   separate meshes parented to Body, origin at the hub, axle along local X
#   Front       an empty at the centre of the front bumper, parented to Body
# One material: vertex colours times the car's atlas (<Name>Atlas.png). UV channel 2 (x): 1 for
# the body paint (the game recolours it, keeping each vertex's brightness ratio to the base
# paint), 0 for everything else. Paint vertices all carry exactly the base paint colour; their
# grime, mud speckle and panel gaps live in the atlas (UV channel 1 projects them onto side,
# front, rear and top maps), so a recolour keeps the dirt. Vertex colours and the JSON's
# "paint" are sRGB, as stored in the FBX.
# Normals: one smooth normal per vertex, weighted by face area (so flat panels stay flat up to
# their soft bevels); the ink hull pushed along them never tears.
#
# Forms are rounded boxes on explicit grids (rbox), lathes and sweeps, so details can follow
# grid lines: windows are inset grid cells with a rubber frame, wheel arches are boolean-cut
# wells covered by swept flares, small parts are placed by ray casts onto the body.
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else '/tmp/Car.fbx'
TYPE = ARGS[ARGS.index('--type') + 1] if '--type' in ARGS else 'hatch'
C = bpy.context
PI = math.pi

# ---------------------------------------------------------------- materials (sRGB)
MATS = ['paint', 'paint2', 'trim', 'plastic', 'chrome', 'glass', 'frame', 'well', 'under', 'groove',
        'head', 'tail', 'amber', 'plate', 'grille', 'tyre', 'sidewall', 'wheel', 'mirror', 'wood',
        'cloth', 'cloth2', 'strap', 'metal', 'can', 'can2', 'cream', 'red', 'produce', 'produce2',
        'sack', 'rack', 'bed', 'lamp', 'canvas', 'sidewall2']
MID = {n: i for i, n in enumerate(MATS)}
BASE_COL = {
    'trim': (0.17, 0.17, 0.19), 'plastic': (0.25, 0.25, 0.27), 'chrome': (0.80, 0.82, 0.83),
    'glass': (1, 1, 1), 'frame': (0.14, 0.14, 0.16), 'well': (0.09, 0.09, 0.10),
    'under': (0.12, 0.12, 0.13), 'groove': (0.13, 0.11, 0.11), 'head': (1, 1, 1), 'tail': (1, 1, 1),
    'amber': (0.97, 0.62, 0.20), 'plate': (1, 1, 1), 'grille': (1, 1, 1), 'tyre': (0.17, 0.17, 0.18),
    'sidewall': (0.21, 0.21, 0.22), 'wheel': (1, 1, 1), 'mirror': (0.55, 0.64, 0.70),
    'wood': (1, 1, 1), 'cloth': (0.62, 0.30, 0.25), 'cloth2': (0.86, 0.52, 0.24),
    'strap': (0.20, 0.19, 0.20), 'metal': (0.30, 0.30, 0.32), 'can': (0.70, 0.22, 0.18),
    'can2': (0.42, 0.47, 0.30), 'cream': (0.95, 0.91, 0.80), 'red': (0.78, 0.20, 0.16),
    'produce': (0.93, 0.55, 0.20), 'produce2': (0.52, 0.68, 0.32), 'sack': (1, 1, 1),
    'rack': (0.16, 0.16, 0.18), 'bed': (1, 1, 1), 'lamp': (1.0, 0.96, 0.85), 'canvas': (0.88, 0.82, 0.66),
    'sidewall2': (0.27, 0.27, 0.28),
}
# UV channel 1 for each material: grime (the painted side/front maps), panel (glass streak),
# keep (set by the part itself), anything else samples the atlas' white corner.
UVMODE = {'paint': 'grime', 'paint2': 'grime', 'trim': 'grime', 'plastic': 'grime', 'glass': 'panel',
          'cream': 'grime', 'metal': 'grime', 'bed': 'keep'}
for k in ('head', 'tail', 'plate', 'grille', 'wheel', 'wood', 'cloth', 'cloth2', 'sack', 'can', 'can2'):
    UVMODE[k] = 'keep'

# ---------------------------------------------------------------- atlas layout (UV space)
# The paint, bumpers and trim sample projected maps: side (y, z) for side-facing faces, front and
# rear (x, z) for faces looking along Y, top (y, x) for upward faces. They hold the grime and the
# panel gaps, so a recolour of the paint keeps both.
AT = 1024
REG = {
    'side': (0.0, 0.70, 1.0, 1.0),
    'front': (0.0, 0.48, 0.5, 0.70),
    'rear': (0.5, 0.48, 1.0, 0.70),
    'top': (0.0, 0.25, 0.75, 0.48),
    'glass': (0.75, 0.25, 1.0, 0.48),
    'wheel': (0.0, 0.0, 0.25, 0.25),
    'head': (0.25, 0.125, 0.375, 0.25),
    'rtail': (0.25, 0.0, 0.375, 0.125),      # round tail lamp
    'tail': (0.375, 0.0, 0.4375, 0.25),      # tall combination lamp
    'grille': (0.4375, 0.125, 0.6875, 0.25),
    'plate': (0.4375, 0.0625, 0.6875, 0.125),
    'can': (0.6875, 0.0, 0.8125, 0.25),      # jerry can side
    'wood': (0.8125, 0.125, 1.0, 0.25),
    'cloth': (0.8125, 0.0, 0.9375, 0.125),
    'white': (0.9375, 0.0, 1.0, 0.0625),
}
WHITE_UV = (0.96875, 0.03125)
SIDE_HALF, FRONT_HALF, TOP_HALF, MAP_TOP = 2.4, 1.2, 1.0, 2.05


def map_st(name, co):
    """World position -> (s, t) in [0, 1] on one of the projected maps."""
    if name == 'side': return 0.5 + co[1] / (2 * SIDE_HALF), co[2] / MAP_TOP
    if name in ('front', 'rear'): return 0.5 + co[0] / (2 * FRONT_HALF), co[2] / MAP_TOP
    return 0.5 + co[1] / (2 * SIDE_HALF), 0.5 + co[0] / (2 * TOP_HALF)


def pick_map(n):
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if az >= ax and az >= ay and n[2] > 0: return 'top'
    if ay > ax and ay > az: return 'front' if n[1] < 0 else 'rear'
    return 'side'


def reg_uv(name, s, t, margin=0.02):
    u0, v0, u1, v1 = REG[name]
    s = min(max(s, 0.0), 1.0); t = min(max(t, 0.0), 1.0)
    s = margin + s * (1 - 2 * margin); t = margin + t * (1 - 2 * margin)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


class Bag(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v): self[k] = v


def smooth01(t):
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- bmesh pieces
# Every piece is a bmesh with a face int layer 'mat' (an index into MATS), a face int layer
# 'panel' (glass panel id) and a loop UV layer (UV channel 1, used by 'keep' materials).
def new_bm():
    bm = bmesh.new()
    bm.faces.layers.int.new('mat'); bm.faces.layers.int.new('panel')
    bm.loops.layers.uv.new('UVMap')
    return bm


def lay(bm):
    if 'panel' not in bm.faces.layers.int: bm.faces.layers.int.new('panel')
    if 'mat' not in bm.faces.layers.int: bm.faces.layers.int.new('mat')
    if 'UVMap' not in bm.loops.layers.uv: bm.loops.layers.uv.new('UVMap')
    return bm.faces.layers.int['mat'], bm.faces.layers.int['panel'], bm.loops.layers.uv['UVMap']


def bm_from(V, F, mats):
    bm = new_bm(); lm, lp, _ = lay(bm)
    vs = [bm.verts.new(tuple(map(float, v))) for v in V]
    out = []
    for f, m in zip(F, mats):
        try:
            face = bm.faces.new([vs[i] for i in f]); face[lm] = m; face[lp] = -1; out.append(face)
        except ValueError:
            out.append(None)
    white_uv(bm)
    bm.normal_update()
    return bm, out


def white_uv(bm):
    lu = lay(bm)[2]
    for f in bm.faces:
        for l in f.loops: l[lu].uv = WHITE_UV
    return bm


def merge(dst, src):
    lm, lp, lu = lay(dst); sm, sp, su = lay(src)
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[lm] = f[sm]; nf[lp] = f[sp]
        for a, b in zip(f.loops, nf.loops): b[lu].uv = a[su].uv
    return dst


def xform(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if M.to_3x3().determinant() < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def setmat(bm, name, faces=None):
    lm = lay(bm)[0]
    for f in (bm.faces if faces is None else faces): f[lm] = MID[name]
    return bm


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


def basis(origin, x, y, z):
    M = Matrix((Vector(x), Vector(y), Vector(z))).transposed().to_4x4(); M.translation = Vector(origin); return M


def uv_planar(bm, faces, region, fn, margin=0.02):
    """UVs for faces from fn(local co) -> (s, t) in [0, 1] inside an atlas region (before placing)."""
    lu = lay(bm)[2]
    for f in faces:
        for l in f.loops:
            s, t = fn(l.vert.co)
            l[lu].uv = reg_uv(region, s, t, margin)


def faces_facing(bm, d, cos=0.7):
    d = Vector(d).normalized(); bm.normal_update()
    return [f for f in bm.faces if f.normal.dot(d) > cos]


# ---------------------------------------------------------------- primitives
def _lines(a0, a1, r, seg, extra):
    cs = {round(a0, 6), round(a1, 6)}
    for o in {0: [], 1: [1.0], 2: [1.0, 0.586], 3: [1.0, 0.732, 0.423]}[seg]:
        cs.add(round(a0 + r * o, 6)); cs.add(round(a1 - r * o, 6))
    for e in extra:
        if a0 + 1e-4 < e < a1 - 1e-4: cs.add(round(e, 6))
    return sorted(cs)


def rbox(lo, hi, r, seg=(2, 2, 2), extra=((), (), ()), skip=()):
    """A rounded box on an explicit grid. Each face is a grid of the axis lines (the rounding
    lines, then the extra lines), and the grid is projected onto a box with elliptical edges of
    radii r. Returns (P grid coords, X positions, faces, tags (axis, sign), face param centres)."""
    lo = np.array(lo, float); hi = np.array(hi, float); r = np.maximum(np.array(r, float), 1e-4)
    ax = [_lines(lo[i], hi[i], r[i], seg[i], extra[i]) for i in range(3)]
    index = {}; P = []; F = []; T = []

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
                    F.append(q); T.append((a, s))
    P = np.array(P)
    ctr = (lo + hi) / 2; h = (hi - lo) / 2
    Q = P - ctr; inner = np.maximum(h - r, 0)
    qq = np.clip(Q, -inner, inner)
    d = (Q - qq) / r
    n = np.linalg.norm(d, axis=1, keepdims=True); n[n < 1e-9] = 1
    X = ctr + qq + r * d / n
    Pc = np.array([P[f].mean(axis=0) for f in F])
    return P, X, F, T, Pc


def rpiece(lo, hi, r, mat, seg=(2, 2, 2), extra=((), (), ()), skip=(), deform=None):
    P, X, F, T, Pc = rbox(lo, hi, r, seg, extra, skip)
    if deform is not None: X = deform(X)
    bm, _ = bm_from(X, F, [MID[mat]] * len(F))
    return bm


def lathe(prof, n, mats, phase=0.5):
    """A surface of revolution about local Z. prof: (radius, height) from one end to the other
    (r = 0 makes a pole); the faces point outward when the profile starts at the -Z end.
    mats: one material per profile segment. Returns (bm, [(face, segment, i)])."""
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
            F.append(f); M.append(MID[mats[si] if isinstance(mats, (list, tuple)) else mats]); tags.append((si, i))
    bm, faces = bm_from(V, F, M)
    return bm, [(f, s, i) for f, (s, i) in zip(faces, tags) if f is not None]


def sweep(path, up, section, mat, caps=True, scales=None):
    """Rings of a closed 2D section (u along the normal, v along the binormal) along a polyline.
    up: a vector or fn(i, point, tangent) -> vector giving each ring's normal direction."""
    n = len(path); m = len(section); V = []
    for i, p in enumerate(path):
        p = Vector(p)
        if i == 0: t = Vector(path[1]) - p
        elif i == n - 1: t = p - Vector(path[-2])
        else: t = Vector(path[i + 1]) - Vector(path[i - 1])
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
    bm, _ = bm_from(V, F, [MID[mat]] * len(F))
    return fix_normals(bm)


def tube(path, radius, mat, sides=6, caps=True):
    sec = [(radius * math.cos(2 * PI * k / sides), radius * math.sin(2 * PI * k / sides)) for k in range(sides)]

    def up(i, p, t):
        return Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    return sweep(path, up, sec, mat, caps)


def cbox(size, r, mat, seg=1):
    """A small chamfered box (size = full x, y, z) centred on the origin."""
    bm = new_bm()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    r = min(r, min(size) * 0.45)
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    setmat(bm, mat); white_uv(bm)
    return fix_normals(bm)


def new_obj(name, me):
    o = bpy.data.objects.new(name, me); C.scene.collection.objects.link(o); return o


def activate(o):
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True); C.view_layer.objects.active = o


def boolean_diff(bm, cutter):
    me = bpy.data.meshes.new('tmp'); bm.to_mesh(me); ob = new_obj('tmp', me)
    cm = bpy.data.meshes.new('cut'); cutter.to_mesh(cm); co = new_obj('cut', cm)
    m = ob.modifiers.new('b', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.object = co
    activate(ob); bpy.ops.object.modifier_apply(modifier=m.name)
    out = bmesh.new(); out.from_mesh(ob.data); lay(out)
    bpy.data.objects.remove(ob); bpy.data.objects.remove(co)
    bpy.data.meshes.remove(me); bpy.data.meshes.remove(cm)
    out.normal_update()
    return out


# ---------------------------------------------------------------- panel gaps
# Gaps are painted into the projected maps (see paint_atlas): thin dark lines given as polylines
# in map coordinates, side (y, z), front / rear (x, z), top (y, x).
def cab_y_at(c, yp, z):
    """World y of the cabin's grid line y = yp (its y at the waist) at height z (the shear)."""
    cb = c.cab; zw = c.tub.zw if cb.zw is None else cb.zw
    s = (yp - cb.yf0) / (cb.yr0 - cb.yf0)
    kf = (cb.yf1 - cb.yf0) / (cb.zt - zw); kr = (cb.yr0 - cb.yr1) / (cb.zt - zw)
    return yp + (z - zw) * (kf * (1 - s) - kr * s)


def cab_x_at(c, xp, z):
    cb = c.cab; zw = c.tub.zw if cb.zw is None else cb.zw
    return xp * (1 - (1 - cb.w1 / cb.w0) / (cb.zt - zw) * (z - zw))


def door_gaps(c, doors, zb, up_pillars=True, zw=None, up_front=False):
    """doors: ((front y at the bottom, front y at the waist), (rear y bottom, rear y waist)).
    The rear edges continue up the pillars between the side windows (and the front edges up the
    A-pillar when up_front)."""
    t = c.tub; zw = zw or t.zw
    g1 = c.cab.g1 if c.cab else zw
    for (f0, f1), (r0, r1) in doors:
        pts = [(f0, zb), (f1, zw)]
        if up_front and c.cab: pts.append((cab_y_at(c, f1, g1 - 0.004), g1 - 0.004))
        c.gap('side', *pts)
        pts = [(r0, zb), (r1, zw)]
        if up_pillars and c.cab: pts.append((cab_y_at(c, r1, g1 - 0.004), g1 - 0.004))
        c.gap('side', *pts)
        c.gap('side', (f0, zb), (r0, zb))
        for yy in (f1, r1):
            for sx in (-1, 1):
                c.gap('top', (yy, sx * ((c.cab.w0 if c.cab else t.hw) - 0.03)), (yy, sx * (t.hw + 0.02)))


def bonnet_gaps(c, yb, xb, zf):
    t = c.tub
    c.gap('top', (yb, -xb), (yb, xb))
    for sx in (-1, 1):
        c.gap('top', (yb, sx * xb), (t.y0 - 0.2, sx * xb))
        c.gap('front', (sx * xb, zf), (sx * xb, zf + 0.06))
    c.gap('front', (-xb, zf), (xb, zf))


def tailgate_gaps(c, xt, zt, ytop, up_cabin=False, ztop=None):
    t = c.tub
    for sx in (-1, 1):
        c.gap('top', (ytop, sx * xt), (t.y1 + 0.2, sx * xt))
        pts = [(sx * xt, zt), (sx * xt, t.zw)]
        if up_cabin and c.cab:
            zz = ztop or c.cab.zt - 0.06
            pts.append((sx * cab_x_at(c, xt, zz), zz))
        c.gap('rear', *pts)
    c.gap('rear', (-xt, zt), (xt, zt))


# ---------------------------------------------------------------- the car
class Car:
    def __getattr__(self, k):
        if k.startswith('__'): raise AttributeError(k)
        return None

    def __init__(self):
        self.pieces = []          # body bmesh pieces
        self.wheels = {}          # name -> bmesh (local, hub at origin)
        self.pal = dict(BASE_COL)
        self.bvh = None
        self.lines = {}            # panel gaps painted into the projected maps: map -> [polyline]

    def gap(self, mp, *pts):
        self.lines.setdefault(mp, []).append([tuple(p) for p in pts])

    def add(self, bm):
        self.pieces.append(bm); return bm

    def hit(self, o, d, bvh=None):
        loc, nrm, idx, dist = (bvh or self.bvh).ray_cast(Vector(o), Vector(d).normalized())
        return (loc, nrm) if loc is not None else (None, None)

    def wheel_pos(self):
        return {'FL': (self.track, self.yf), 'FR': (-self.track, self.yf),
                'RL': (self.track, self.yr), 'RR': (-self.track, self.yr)}


def make_bvh(bms):
    tmp = new_bm()
    for b in bms: merge(tmp, b)
    tmp.normal_update()
    t = BVHTree.FromBMesh(tmp); tmp.free(); return t


# ---------------------------------------------------------------- lower body
def deform_tub(X, t):
    x, y, z = X[:, 0].copy(), X[:, 1].copy(), X[:, 2].copy()
    hz = np.clip((z - t.z0) / (t.zw - t.z0), 0, 1)
    wf = np.clip((t.nose_start - y) / (t.nose_start - t.y0), 0, 1); wf = wf * wf * (3 - 2 * wf)
    wr = np.clip((y - t.tail_start) / (t.y1 - t.tail_start), 0, 1); wr = wr * wr * (3 - 2 * wr)
    z = z - (t.nose_drop or 0) * wf ** 1.5 * hz ** 2 - (t.tail_drop or 0) * wr ** 1.5 * hz ** 2
    y = y + (t.nose_lean or 0) * wf ** 3 * (hz - 0.35) - (t.tail_lean or 0) * wr ** 3 * (hz - 0.35)
    x = x * (1 - (t.nose_taper or 0) * wf ** 2 - (t.tail_taper or 0) * wr ** 2)
    if t.barrel: x = x * (1 + t.barrel * np.sin(PI * hz))
    return np.stack([x, y, z], 1)


def build_tub(c, cut_arches=True):
    t = c.tub
    P, X, F, T, Pc = rbox((-t.hw, t.y0, t.z0), (t.hw, t.y1, t.zw), t.r,
                          extra=(t.xlines or (), t.ylines or (), t.zlines or ()))
    X = deform_tub(X, t)
    mats = [MID['under'] if (a == 2 and s < 0) else MID['paint'] for a, s in T]
    bm, _ = bm_from(X, F, mats)
    if cut_arches:
        cutter = new_bm()
        for k, (wx, wy) in c.wheel_pos().items():
            if k[0] == 'R' and c.no_rear_arch: continue
            sgn = 1 if wx > 0 else -1
            xin = abs(wx) - c.tw / 2 - 0.045
            ra = c.Ra
            cyl, _ = lathe([(0, 0), (ra, 0), (ra, 1.2), (0, 1.2)], 20, ['well'] * 3)
            xform(cyl, Matrix.Translation((sgn * xin, wy, c.R)) @ Matrix.Rotation(sgn * PI / 2, 4, 'Y'))
            merge(cutter, cyl)
        bm = boolean_diff(bm, cutter)
    # nobody sees the underside
    lm = lay(bm)[0]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lm] == MID['under']], context='FACES')
    return bm


# ---------------------------------------------------------------- cabin / glasshouse
def deform_cab(v, cb, zw):
    x, y, z = v
    dz = z - zw
    s = (y - cb.yf0) / (cb.yr0 - cb.yf0)
    kf = (cb.yf1 - cb.yf0) / (cb.zt - zw); kr = (cb.yr0 - cb.yr1) / (cb.zt - zw)
    kx = (1 - cb.w1 / cb.w0) / (cb.zt - zw)
    return Vector((x * (1 - kx * dz), y + dz * (kf * (1 - s) - kr * s), z))


def build_cabin(c):
    cb = c.cab; zw = c.tub.zw if cb.zw is None else cb.zw
    zb = zw - 0.16
    xl = [cb.xw, -cb.xw, cb.xr, -cb.xr] + list(cb.xlines or ())
    if cb.rear_split: xl += [cb.rear_split, -cb.rear_split]
    yl = [y for pr in cb.side for y in pr] + list(cb.ylines or ())
    zl = [cb.g0, cb.g1] + list(cb.zlines or ())
    P, X, F, T, Pc = rbox((-cb.w0, cb.yf0, zb), (cb.w0, cb.yr0, cb.zt), cb.r, extra=(xl, yl, zl), skip=((2, -1),))
    panels = {}
    mats = []; pids = []
    for (a, s), (x, y, z) in zip(T, Pc):
        m, pid = 'paint', None
        if cb.g0 < z < cb.g1:
            if a == 1 and s < 0 and abs(x) < cb.xw and cb.xw > 0: pid = 'ws'
            elif a == 1 and s > 0 and abs(x) < cb.xr and cb.xr > 0: pid = 'rear'
            elif a == 0:
                for k, (y0, y1) in enumerate(cb.side):
                    if y0 < y < y1: pid = ('side', s, k)
        if pid == 'rear' and cb.rear_split:
            pid = None if abs(x) < cb.rear_split else ('rear', x > 0)
        if pid is not None:
            m = 'glass'; pid = panels.setdefault(pid, len(panels) + c.panel_base)
        elif z > cb.g1 and cb.roof: m = cb.roof
        elif cb.body: m = cb.body
        mats.append(MID[m]); pids.append(-1 if pid is None else pid)
    bm, faces = bm_from(X, F, mats)
    lm, lp, _ = lay(bm)
    for f, pid in zip(faces, pids):
        if f is not None: f[lp] = pid
    c.panel_base += len(panels) + 1
    # hidden part inside the lower body
    dead = [f for f in bm.faces if max(v.co.z for v in f.verts) < zw - 0.035]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    # windows: inset each panel, the ring is the rubber frame
    bm.normal_update()
    for pid in set(pids):
        if pid < 0: continue
        reg = [f for f in bm.faces if f[lp] == pid]
        res = bmesh.ops.inset_region(bm, faces=reg, thickness=cb.fw or 0.024, depth=-0.012, use_even_offset=True, use_boundary=True)
        for f in res['faces']: f[lm] = MID['frame']; f[lp] = -1
    for v in bm.verts: v.co = deform_cab(v.co, cb, zw)
    bm.normal_update()
    flat = [f for f in bm.faces if f.normal.z > 0.9999 and f[lp] < 0]
    if len(flat) > 1: bmesh.ops.dissolve_faces(bm, faces=flat)
    bm.normal_update()
    return bm


# ---------------------------------------------------------------- wheels
def build_wheel(c, R, W, n=20, rows=2, depth=0.016, spare=False):
    xo = W / 2; tb = R - depth
    xt = xo - 0.035
    tread = [(tb, -xt + 2 * xt * k / rows) for k in range(rows + 1)]
    prof = ([(0, -(xo - 0.03)), (0.90 * R, -xo), (0.97 * R, -(xo - 0.02))]
            + tread +
            [(0.97 * R, xo - 0.02), (0.86 * R, xo), (0.70 * R, xo - 0.006), (0.655 * R, xo - 0.016),
             (0.58 * R, xo - 0.040), (0.17 * R, xo - 0.040), (0, xo - 0.022)])
    nt = len(tread) - 1
    mats = ['under', 'sidewall', 'tyre'] + ['tyre'] * nt + ['tyre', 'sidewall', 'sidewall2', 'sidewall'] + ['wheel'] * 3
    bm, tags = lathe(prof, n, mats, phase=0.0)
    lm, lp, lu = lay(bm)
    # tread blocks: a checker of the tread cells, raised by depth
    t0 = 3
    blocks = [f for f, s, i in tags if t0 <= s < t0 + nt and (i + s) % 2 == 0]
    res = bmesh.ops.extrude_discrete_faces(bm, faces=blocks)
    for f in res['faces']:
        for v in f.verts:
            rv = Vector((v.co.x, v.co.y, 0))
            if rv.length > 1e-6: v.co += rv.normalized() * depth
    for f in bm.faces:
        if f[lm] in (MID['tyre'], MID['sidewall'], MID['sidewall2']):
            for l in f.loops: l[lu].uv = WHITE_UV
    rim = 0.66 * R
    wf = [f for f in bm.faces if f[lm] == MID['wheel']]
    uv_planar(bm, wf, 'wheel', lambda co: (0.5 + co.x / (2 * rim), 0.5 + co.y / (2 * rim)), margin=0.01)
    # local Z (the axle) -> +X: the outer face looks out of the car's left side
    xform(bm, Matrix.Rotation(PI / 2, 4, 'Y'))
    return fix_normals(bm)


# ---------------------------------------------------------------- body details
def add_flares(c, mat=None, width=None, out=None, inset=0.045, steps=10, which=('F', 'R')):
    mat = mat or c.flare_mat or 'paint'; width = width or c.flare_w or 0.08; out = out or c.flare_out or 0.035
    t = c.tub
    for k, (wx, wy) in c.wheel_pos().items():
        if k[0] not in which: continue
        sgn = 1 if wx > 0 else -1
        ra = c.Ra
        zc = c.R
        zlow = (c.flare_low if c.flare_low is not None else t.z0) + 0.005
        th0 = math.asin(max(-0.95, min(0.95, (zlow - zc) / ra)))
        th = [th0 + (PI - 2 * th0) * i / steps for i in range(steps + 1)]
        xs = c.flare_x if c.flare_x is not None else t.hw
        path = [(sgn * xs, wy + ra * math.cos(a), zc + ra * math.sin(a)) for a in th]
        sec = [(-0.005, -inset), (width * 0.95, -inset), (width, out * 0.15), (width * 0.55, out), (-0.005, out * 0.7)]
        sc = [0.25 + 0.75 * smooth01(min(i, steps - i) / 2.2) for i in range(steps + 1)]
        ctr = Vector((sgn * xs, wy, zc))

        def up(i, p, tg, ctr=ctr):
            return Vector(p) - ctr
        # binormal = tangent x radial = -X on the arc as built; flip the section for the left side
        s2 = [(a, -b * sgn) for a, b in sec]
        bm = sweep(path, up, s2, mat, caps=True, scales=sc)
        c.add(bm)


def add_lathe_light(c, loc, nrm, r, rim='chrome', lens='head', n=14, depth=0.045, up=(0, 0, 1)):
    prof = [(0, -0.05), (r * 1.14, -0.05), (r * 1.14, depth * 0.45), (r * 1.03, depth), (r * 0.86, depth * 0.85),
            (r * 0.55, depth * 1.0), (0, depth * 1.06)]
    bm, tags = lathe(prof, n, ['plastic', rim, rim, rim, lens, lens])
    lf = [f for f, s, i in tags if s >= 4]
    rr = r * 0.86
    if lens in ('head', 'tail'):
        region = 'head' if lens == 'head' else 'rtail'
        setmat(bm, 'head', lf)
        uv_planar(bm, lf, region, lambda co: (0.5 + co.x / (2 * rr), 0.5 + co.y / (2 * rr)), margin=0.0)
    xform(bm, frame(loc, nrm, up))
    return c.add(bm)


def add_box_on(c, loc, nrm, size, r, mat, up=(0, 0, 1), seg=1, front_region=None, sink=0.0, inset=None):
    """A chamfered box standing on a surface point: local Z along nrm (size[2] is its depth)."""
    bm = cbox(size, r, mat, seg)
    xform(bm, Matrix.Translation((0, 0, size[2] / 2 - sink)))
    if inset:
        fr = faces_facing(bm, (0, 0, 1), 0.9)
        res = bmesh.ops.inset_region(bm, faces=fr, thickness=inset[0], depth=inset[1], use_even_offset=True)
        setmat(bm, inset[2], res['faces'])
        if len(inset) > 3: setmat(bm, inset[3], fr)
    if front_region:
        fr = faces_facing(bm, (0, 0, 1), 0.3)
        sx, sy = size[0], size[1]
        uv_planar(bm, fr, front_region, lambda co: (0.5 + co.x / sx, 0.5 + co.y / sy), margin=0.01)
        if front_region in ('tail', 'grille', 'plate', 'head'):
            setmat(bm, {'tail': 'tail', 'grille': 'grille', 'plate': 'plate', 'head': 'head'}[front_region], fr)
    xform(bm, frame(loc, nrm, up))
    return c.add(bm)


def surf(c, x, y, z, d):
    """Hit the body from outside along direction d through (x, y, z)."""
    d = Vector(d).normalized()
    return c.hit(Vector((x, y, z)) - d * 4.0, d)


def add_bumper(c, front, mat, z0, z1, depth, overhang, wrap=0.08, rz=0.06, hw=None):
    t = c.tub
    hw = hw or (t.hw - 0.005)
    if front:
        lo = (-hw, t.y0 - overhang, z0); hi = (hw, t.y0 - overhang + depth, z1); sg = 1
    else:
        lo = (-hw, t.y1 + overhang - depth, z0); hi = (hw, t.y1 + overhang, z1); sg = -1
    ext = (0.5, -0.5)

    def bend(X):
        X = X.copy(); X[:, 1] += sg * wrap * (np.abs(X[:, 0]) / hw) ** 4; return X
    bm = rpiece(lo, hi, (0.07, min(depth / 2 - 0.005, 0.06), min((z1 - z0) / 2 - 0.005, rz)), mat,
                seg=(2, 1, 1), extra=(ext, (), ()), deform=bend)
    c.add(bm)
    return (lo[1] if front else hi[1]), (z0 + z1) / 2


def add_mirror(c, sgn, y, z, mat='paint', arm=0.06):
    loc, nrm = surf(c, 0, y, z, (-sgn, 0, 0))
    if loc is None: return
    base = add_box_on(c, loc, Vector((sgn, 0, 0)), (0.06, 0.035, arm + 0.02), 0.01, 'trim', sink=0.02)
    head_c = loc + Vector((sgn * (arm + 0.05), 0.012, 0.03))
    bm = cbox((0.13, 0.07, 0.095), 0.025, mat, seg=1)
    fr = faces_facing(bm, (0, 1, 0), 0.9)
    res = bmesh.ops.inset_region(bm, faces=fr, thickness=0.012, depth=-0.006, use_even_offset=True)
    setmat(bm, 'mirror', fr); setmat(bm, 'trim', res['faces'])
    xform(bm, Matrix.Translation(head_c) @ Matrix.Rotation(sgn * 0.12, 4, 'Z'))
    c.add(bm)


def add_wiper(c, x, z, length, ang, bvh_dir=(0, 1, 0), rear=False):
    d = Vector(bvh_dir)
    loc, nrm = surf(c, x, 0, z, d)
    if loc is None: return
    nrm = nrm.normalized()
    upv = (Vector((0, 0, 1)) - nrm * nrm.z).normalized()
    hor = upv.cross(nrm).normalized()
    along = (hor * math.cos(ang) + upv * math.sin(ang)).normalized()
    side = nrm.cross(along)
    M = basis(loc + nrm * 0.012 + along * (length / 2), along, side, nrm)
    bm = cbox((length, 0.018, 0.014), 0.005, 'trim'); xform(bm, M); c.add(bm)


# ---------------------------------------------------------------- atlas painting
def _region_px(name):
    u0, v0, u1, v1 = REG[name]
    x0, x1 = int(round(u0 * AT)), int(round(u1 * AT)); y0, y1 = int(round((1 - v1) * AT)), int(round((1 - v0) * AT))
    w, h = x1 - x0, y1 - y0
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    return (slice(y0, y1), slice(x0, x1)), U, V


def _noise(h, w, cells, rng, smooth=True):
    from PIL import Image
    small = (rng.random((cells[1], cells[0])) * 255).astype(np.uint8)
    im = Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def _blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


MUD = (0.62, 0.53, 0.44)
SPECK = (0.46, 0.39, 0.33)
RUST = (0.62, 0.36, 0.20)


def _specks(img, g, rng, count, rmin=0.6, rmax=2.0, col=SPECK, alpha=0.8, aspect=1.0):
    """Mud specks where g is high. aspect = vertical / horizontal pixels per metre, so the specks
    come out round on the car."""
    h, w = g.shape
    ys = rng.integers(0, h, count); xs = rng.integers(0, w, count)
    keep = rng.random(count) < g[ys, xs] ** 1.3
    for y, x in zip(ys[keep], xs[keep]):
        r = rng.uniform(rmin, rmax); rv = max(r * aspect, 0.5)
        y0, y1 = max(0, int(y - rv - 1)), min(h, int(y + rv + 2)); x0, x1 = max(0, int(x - r - 1)), min(w, int(x + r + 2))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt(((yy - y) * r / rv) ** 2 + (xx - x) ** 2)
        m = np.clip(r + 0.5 - d, 0, 1) * alpha
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m[..., None]) + np.array(col)[None, None] * m[..., None]


def _gaps(sub, a, b, polylines, w=0.0045, soft=0.004):
    """Panel gaps: dark anti-aliased lines along polylines given in map coordinates (metres)."""
    k = np.ones(a.shape, np.float32)
    for pl in polylines:
        for (a0, b0), (a1, b1) in zip(pl[:-1], pl[1:]):
            da, db = a1 - a0, b1 - b0
            L2 = max(da * da + db * db, 1e-9)
            tt = np.clip(((a - a0) * da + (b - b0) * db) / L2, 0, 1)
            d = np.sqrt((a - (a0 + tt * da)) ** 2 + (b - (b0 + tt * db)) ** 2)
            k = np.minimum(k, 0.22 + 0.78 * _ss(w, w + soft, d))
    sub *= k[..., None]


def paint_atlas(path, c):
    rng = np.random.default_rng(7)
    img = np.ones((AT, AT, 3), np.float32)
    t = c.tub
    z0 = c.grime_z0 if c.grime_z0 is not None else t.z0
    # ---- side map (shared by both sides): sills, wheel arches, the low ends
    sl, U, V = _region_px('side')
    y = (U - 0.5) * 2 * SIDE_HALF; z = V * MAP_TOP
    sub = np.ones(U.shape + (3,), np.float32)
    g = _ss(z0 + 0.20, z0 - 0.02, z) * 0.7
    for (wy, rr) in c.grime_arches:
        d = np.sqrt((y - wy) ** 2 + (z - c.R) ** 2) - rr
        behind = 0.55 + 0.45 * _ss(-0.25, 0.35, y - wy)
        ga = np.exp(-np.maximum(d, 0) / 0.075) * (d > -0.02) * behind * _ss(c.R + rr + 0.05, c.R - 0.1, z)
        g = np.maximum(g, ga * 0.85)
    yl0, yl1 = c.grime_ends
    g = np.maximum(g, _ss(0.50, 0.18, z) * np.maximum(_ss(yl0 + 0.4, yl0, y), _ss(yl1 - 0.4, yl1, y)) * 0.7)
    asp = (U.shape[0] / MAP_TOP) / (U.shape[1] / (2 * SIDE_HALF))
    nz = _noise(*U.shape, (48, int(20.5)), rng) * 0.6 + _noise(*U.shape, (160, 68), rng) * 0.4
    g = np.clip(g * (0.45 + 0.9 * nz), 0, 1)
    sub *= (1 - 0.07 * _ss(0.65, 0.2, z))[..., None]
    sub = _blend(sub, g, MUD, 0.38)
    _specks(sub, g, rng, 6000, 0.6, 1.8, SPECK, 0.6, asp)
    _specks(sub, g * 0.6, rng, 1200, 1.5, 3.0, MUD, 0.4, asp)
    if c.rust:
        _specks(sub, g * c.rust, rng, 1500, 0.8, 2.2, RUST, 0.55, asp)
    _gaps(sub, y, z, c.lines.get('side', []))
    img[sl] = sub
    # ---- front and rear maps: grime along the bottom
    for name in ('front', 'rear'):
        sl, U, V = _region_px(name)
        x = (U - 0.5) * 2 * FRONT_HALF; z = V * MAP_TOP
        sub = np.ones(U.shape + (3,), np.float32)
        g = _ss(z0 + 0.32, z0 - 0.1, z) * 0.6
        asp = (U.shape[0] / MAP_TOP) / (U.shape[1] / (2 * FRONT_HALF))
        nz = _noise(*U.shape, (24, 20), rng) * 0.6 + _noise(*U.shape, (80, 68), rng) * 0.4
        g = np.clip(g * (0.4 + 0.9 * nz), 0, 1)
        sub *= (1 - 0.06 * _ss(0.6, 0.2, z))[..., None]
        sub = _blend(sub, g, MUD, 0.35)
        _specks(sub, g, rng, 2500, 0.6, 1.8, SPECK, 0.6, asp)
        if c.rust:
            _specks(sub, g * c.rust, rng, 600, 0.8, 2.0, RUST, 0.5, asp)
        _gaps(sub, x, z, c.lines.get(name, []))
        img[sl] = sub
    # ---- top map: clean, a little sun-faded dust, the bonnet and tailgate gaps
    sl, U, V = _region_px('top')
    y = (U - 0.5) * 2 * SIDE_HALF; x = (V - 0.5) * 2 * TOP_HALF
    nz = _noise(*U.shape, (30, 10), rng)
    sub = np.ones(U.shape + (3,), np.float32) * (0.985 + 0.015 * nz)[..., None]
    _gaps(sub, y, x, c.lines.get('top', []))
    img[sl] = sub
    # ---- glass: a deep tint, darker at the top, with soft lighter streaks
    sl, U, V = _region_px('glass')
    top, bot = np.array((0.13, 0.17, 0.22)), np.array((0.25, 0.32, 0.37))
    sub = top[None, None] * V[..., None] + bot[None, None] * (1 - V[..., None])
    d = U * 0.85 + V
    s1 = _ss(0.11, 0.0, np.abs(d - 0.72)); s2 = _ss(0.035, 0.0, np.abs(d - 0.98))
    sub = _blend(sub, s1, (0.52, 0.62, 0.68), 0.5); sub = _blend(sub, s2, (0.62, 0.72, 0.77), 0.55)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    sub = _blend(sub, _ss(0.06, 0.0, edge), (0.10, 0.12, 0.15), 0.5)
    img[sl] = sub
    # ---- headlight lens
    sl, U, V = _region_px('head')
    r = np.sqrt((U - 0.5) ** 2 + (V - 0.5) ** 2) / 0.5
    sub = np.ones(U.shape + (3,), np.float32) * np.array((1.0, 0.97, 0.86))
    for rr, wdt in ((0.30, 0.035), (0.56, 0.03), (0.78, 0.03)):
        sub = _blend(sub, _ss(wdt, 0.0, np.abs(r - rr)), (0.86, 0.81, 0.70), 0.7)
    sub = _blend(sub, _ss(0.2, 0.14, r), (0.96, 0.90, 0.74), 1.0)
    sub = _blend(sub, _ss(0.86, 1.0, r), (0.62, 0.58, 0.52), 1.0)
    hl = np.sqrt(((U - 0.36) / 1.2) ** 2 + (V - 0.68) ** 2)
    sub = _blend(sub, _ss(0.14, 0.08, hl), (1, 1, 1), 1.0)
    img[sl] = sub
    # ---- round tail lamp
    sl, U, V = _region_px('rtail')
    r = np.sqrt((U - 0.5) ** 2 + (V - 0.5) ** 2) / 0.5
    sub = np.ones(U.shape + (3,), np.float32) * np.array((0.80, 0.17, 0.14))
    sub = _blend(sub, _ss(0.45, 0.1, r), (0.92, 0.32, 0.26), 0.8)
    for rr in (0.38, 0.7):
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - rr)), (0.6, 0.1, 0.1), 0.6)
    sub = _blend(sub, _ss(0.86, 1.0, r), (0.45, 0.08, 0.08), 1.0)
    hl = np.sqrt(((U - 0.36) / 1.2) ** 2 + (V - 0.68) ** 2)
    sub = _blend(sub, _ss(0.13, 0.07, hl), (1, 0.8, 0.75), 0.9)
    img[sl] = sub
    # ---- combination tail lamp (red / amber / clear)
    sl, U, V = _region_px('tail')
    sub = np.ones(U.shape + (3,), np.float32)
    red, amb, clr = np.array((0.80, 0.17, 0.14)), np.array((0.96, 0.60, 0.17)), np.array((0.93, 0.92, 0.88))
    sub[:] = clr
    sub[V > 0.30] = amb; sub[V > 0.56] = red
    sub = _blend(sub, (V > 0.6) * _ss(0.25, 0.0, np.abs(U - 0.32)) * _ss(0.6, 0.95, V), (0.95, 0.38, 0.32), 0.7)
    for vv in (0.30, 0.56):
        sub = _blend(sub, _ss(0.02, 0.0, np.abs(V - vv)), (0.25, 0.1, 0.1), 0.9)
    for vv in np.arange(0.62, 0.98, 0.09):
        sub = _blend(sub, _ss(0.012, 0.0, np.abs(V - vv)) * (V > 0.58), (0.62, 0.1, 0.1), 0.5)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    sub = _blend(sub, _ss(0.07, 0.0, edge), (0.22, 0.1, 0.1), 0.8)
    img[sl] = sub
    # ---- grille
    sl, U, V = _region_px('grille')
    sub = np.ones(U.shape + (3,), np.float32) * 0.11
    style = c.grille_style or 'slats'
    if style == 'slats':
        k = (V * 5.0) % 1.0
        slat = (k > 0.28)
        shade = 0.42 - 0.22 * ((k - 0.28) / 0.72)
        sub = np.where(slat[..., None], shade[..., None] * np.array((1, 1, 1.03))[None, None], sub)
    elif style == 'vertical':
        k = (U * 9.0) % 1.0
        slat = (k > 0.3)
        shade = 0.40 - 0.2 * np.abs((k - 0.65) / 0.35)
        sub = np.where(slat[..., None], shade[..., None] * np.ones(3)[None, None], sub)
    else:  # mesh
        a = ((U * 16 + V * 8) % 1.0); b = ((U * 16 - V * 8) % 1.0)
        bar = (np.minimum(a, 1 - a) < 0.14) | (np.minimum(b, 1 - b) < 0.14)
        sub = np.where(bar[..., None], 0.36, sub)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V) * 2)
    sub = _blend(sub, _ss(0.05, 0.0, edge), (0.07, 0.07, 0.08), 0.8)
    img[sl] = sub
    # ---- plate: plain, light, a dark rim and a little grime at the bottom
    sl, U, V = _region_px('plate')
    sub = np.ones(U.shape + (3,), np.float32) * np.array((0.95, 0.94, 0.88))
    ex = np.minimum(U, 1 - U) * 4; ey = np.minimum(V, 1 - V)
    edge = np.minimum(ex, ey)
    sub = _blend(sub, _ss(0.08, 0.05, edge), (0.24, 0.24, 0.26), 1.0)
    sub = _blend(sub, _ss(0.4, 0.0, V) * (edge > 0.08), (0.80, 0.76, 0.68), 0.5)
    img[sl] = sub
    # ---- wheel face
    paint_wheel(img, c.wheel_style or 'steel', c.wheel_cols or ((0.95, 0.92, 0.84), (0.82, 0.84, 0.86)))
    # ---- wood planks
    sl, U, V = _region_px('wood')
    base = np.array((0.78, 0.58, 0.37))
    plank = np.floor(V * 4); kv = (V * 4) % 1.0
    tone = 0.9 + 0.1 * np.sin(plank * 2.3 + 1)
    grain = 0.95 + 0.05 * np.sin(U * 9 + np.sin(V * 11 + plank * 1.7) * 1.5 + plank)
    sub = base[None, None] * (tone * grain)[..., None]
    sub = _blend(sub, _ss(0.09, 0.0, np.minimum(kv, 1 - kv)), (0.38, 0.25, 0.15), 0.95)
    edge = np.minimum(U, 1 - U)
    sub = _blend(sub, _ss(0.09, 0.03, edge), (0.62, 0.45, 0.28), 1.0)
    sub = _blend(sub, _ss(0.03, 0.0, edge), (0.36, 0.24, 0.14), 0.9)
    img[sl] = sub
    # ---- cloth (canvas weave + seams)
    sl, U, V = _region_px('cloth')
    wv = 0.95 + 0.03 * np.sin(U * 300) * np.sin(V * 300)
    sub = np.ones(U.shape + (3,), np.float32) * wv[..., None]
    nz = _noise(*U.shape, (8, 8), rng)
    sub *= (0.92 + 0.08 * nz)[..., None]
    sub = _blend(sub, _ss(0.012, 0.0, np.abs(V - 0.82)), (0.7, 0.7, 0.7), 0.7)
    sub = _blend(sub, _ss(0.012, 0.0, np.abs(V - 0.18)), (0.7, 0.7, 0.7), 0.7)
    img[sl] = sub
    # ---- jerry can side (embossed X)
    sl, U, V = _region_px('can')
    sub = np.ones(U.shape + (3,), np.float32)
    dx = np.minimum(np.abs((U - 0.5) - (V - 0.5) * 0.7), np.abs((U - 0.5) + (V - 0.5) * 0.7))
    inside = (np.abs(U - 0.5) < 0.38) & (np.abs(V - 0.5) < 0.40)
    sub = _blend(sub, _ss(0.05, 0.02, dx) * inside, (0.72, 0.72, 0.72), 1.0)
    sub = _blend(sub, _ss(0.02, 0.0, dx) * inside, (1.0, 1.0, 1.0), 0.5)
    img[sl] = sub
    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)


def paint_wheel(img, style, cols):
    sl, U, V = _region_px('wheel')
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y); a = np.arctan2(y, x)
    rim, hub = np.array(cols[0]), np.array(cols[1])
    sub = np.ones(U.shape + (3,), np.float32) * rim
    dark = (0.16, 0.16, 0.17)
    if style == 'steel':          # painted steel, round vent holes, a small domed cap
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.93)), rim * 0.62, 1.0)
        sub = _blend(sub, _ss(0.025, 0.0, np.abs(r - 0.62)), rim * 0.75, 1.0)
        for k in range(8):
            aa = 2 * PI * k / 8 + PI / 8
            d = np.sqrt((x - 0.77 * np.cos(aa)) ** 2 + (y - 0.77 * np.sin(aa)) ** 2)
            sub = _blend(sub, _ss(0.105, 0.085, d), dark, 1.0)
        sub = _blend(sub, _ss(0.40, 0.37, r), hub, 1.0)
        sub = _blend(sub, _ss(0.025, 0.0, np.abs(r - 0.385)), hub * 0.6, 1.0)
        sub = _blend(sub, _ss(0.16, 0.08, np.sqrt((x + 0.12) ** 2 + (y - 0.14) ** 2)), (1, 1, 1), 0.8)
    elif style == 'hubcap':       # a full flat cap with radial slots
        sub[:] = hub
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.92)), hub * 0.6, 1.0)
        slots = (np.cos(a * 12) > 0.75) & (r > 0.55) & (r < 0.86)
        sub = _blend(sub, slots.astype(np.float32), hub * 0.45, 1.0)
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.42)), hub * 0.6, 1.0)
        sub = _blend(sub, _ss(0.2, 0.17, r), rim, 1.0)
        sub = _blend(sub, _ss(0.25, 0.0, np.abs(a - 2.2)) * (r < 0.9) * (r > 0.45), (1, 1, 1), 0.35)
    elif style == 'spoke':        # off-road: six wide spokes, lug nuts
        sub[:] = rim
        win = (np.cos(a * 6) < -0.25) & (r > 0.36) & (r < 0.84)
        sub = _blend(sub, win.astype(np.float32), dark, 1.0)
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.9)), rim * 0.6, 1.0)
        for k in range(6):
            aa = 2 * PI * k / 6
            d = np.sqrt((x - 0.24 * np.cos(aa)) ** 2 + (y - 0.24 * np.sin(aa)) ** 2)
            sub = _blend(sub, _ss(0.06, 0.04, d), rim * 0.55, 1.0)
        sub = _blend(sub, _ss(0.13, 0.11, r), hub, 1.0)
    else:                         # plain steel with lug nuts
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.9)), rim * 0.62, 1.0)
        sub = _blend(sub, _ss(0.03, 0.0, np.abs(r - 0.58)), rim * 0.72, 1.0)
        for k in range(5):
            aa = 2 * PI * k / 5 + 0.3
            d = np.sqrt((x - 0.36 * np.cos(aa)) ** 2 + (y - 0.36 * np.sin(aa)) ** 2)
            sub = _blend(sub, _ss(0.07, 0.05, d), rim * 0.5, 1.0)
        sub = _blend(sub, _ss(0.2, 0.17, r), hub, 1.0)
    img[sl] = sub


# ---------------------------------------------------------------- shared dressing
def uv_world(bm, faces, region, fn, margin=0.01):
    lu = lay(bm)[2]
    for f in faces:
        for l in f.loops:
            l[lu].uv = reg_uv(region, *fn(l.vert.co), margin)


def uv_box(bm, faces, region, margin=0.02):
    """Box-projected UVs, normalised to the piece's bounds (wood, cloth, cans)."""
    vs = [v.co for v in bm.verts]
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    lu = lay(bm)[2]; bm.normal_update()
    for f in faces:
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            co = l.vert.co
            l[lu].uv = reg_uv(region, (co[a] - lo[a]) / max(hi[a] - lo[a], 1e-4), (co[b] - lo[b]) / max(hi[b] - lo[b], 1e-4), margin)


def front_lamps(c, x, z, r, rim='chrome', depth=0.03, ind=None):
    for sx in (-1, 1):
        loc, nrm = surf(c, sx * x, 0, z, (0, 1, 0))
        add_lathe_light(c, loc, (nrm + Vector((0, -0.6, 0))).normalized(), r, rim=rim, depth=depth)
        if ind:
            ix, iz, size = ind
            loc, nrm = surf(c, sx * ix, 0, iz, (0, 1, 0))
            add_box_on(c, loc, nrm, size, 0.012, 'amber', sink=0.012)


def grille(c, z, w, h, mat='chrome', x=0.0):
    loc, nrm = surf(c, x, 0, z, (0, 1, 0))
    gf = add_box_on(c, loc, nrm, (w, h, 0.03), 0.02, mat, seg=2, sink=0.015, inset=(0.016, -0.008, mat, 'grille'))
    fr = [f for f in gf.faces if f[lay(gf)[0]] == MID['grille']]
    iw, ih = w - 0.07, h - 0.07
    uv_world(gf, fr, 'grille', lambda co: (0.5 + (co.x - x) / iw, 0.5 + (co.z - z) / ih))
    return gf


def tail_lamps(c, x, z, w, h, depth=0.035):
    for sx in (-1, 1):
        loc, nrm = surf(c, sx * x, 0, z, (0, -1, 0))
        add_box_on(c, loc, nrm, (w, h, depth), 0.02, 'trim', front_region='tail', sink=0.015)


def plate(c, loc, nrm, sink=0.0):
    add_box_on(c, loc, nrm, (0.38, 0.11, 0.014), 0.008, 'plate', front_region='plate', sink=sink)


def bumpers(c, mat, front, rear, strip=True):
    """front / rear: (z0, z1, depth, overhang, wrap). A rubber strip along each, a plate on the front."""
    fy, fz = add_bumper(c, True, mat, *front[:4], wrap=front[4])
    ry, rz = add_bumper(c, False, mat, *rear[:4], wrap=rear[4])
    c.front = (0, fy, fz)
    if strip:
        for yy, zz, sg, w in ((fy, fz, -1, front), (ry, rz, 1, rear)):
            bm = cbox((2 * c.tub.hw - 0.22, 0.06, 0.045), 0.015, 'trim')
            xform(bm, Matrix.Translation((0, yy - sg * 0.016, zz - 0.25 * (w[1] - w[0])))); c.add(bm)
    plate(c, Vector((0, fy - 0.004, fz)), Vector((0, -1, 0)))
    return fy, fz, ry, rz


def mudflaps(c, which=('R',), w=None, h=0.16):
    for k, (wx, wy) in c.wheel_pos().items():
        if k[0] not in which: continue
        top = (c.flap_top or c.tub.z0 + 0.05) if (k[0] == 'F' or not c.flap_top_r) else c.flap_top_r
        hh = h
        bm = cbox((w or c.tw - 0.01, 0.014, hh), 0.006, 'trim')
        xform(bm, Matrix.Translation((wx, wy + c.Ra + 0.005, top - hh / 2))); c.add(bm)


def aerial(c, x, y, length=0.36):
    loc, nrm = surf(c, x, y, 0, (0, 0, -1))
    bm = cbox((0.010, 0.010, length), 0.003, 'trim')
    xform(bm, Matrix.Translation(loc) @ Matrix.Rotation(-0.45, 4, 'X') @ Matrix.Translation((0, 0, length / 2 - 0.01))); c.add(bm)


def fuel_cap(c, y, z):
    loc, nrm = surf(c, 0, y, z, (1, 0, 0))
    bm, _ = lathe([(0, -0.02), (0.05, -0.02), (0.05, 0.004), (0.042, 0.009), (0, 0.01)], 12, ['paint'] * 4)
    xform(bm, frame(loc, nrm)); c.add(bm)


def common_details(c, doors, mirror=None, sills=True, handle_z=None):
    t = c.tub
    for sx in (-1, 1):
        # mirrors at the base of the A-pillars
        my, mz, arm = mirror or (c.cab.yf0 + 0.22, t.zw + 0.06, 0.06)
        add_mirror(c, sx, my, mz, mat=c.mirror_mat or 'paint', arm=arm)
        # door handles near the rear top of each door
        for (y0, y1) in doors:
            loc, nrm = surf(c, 0, y1 - 0.15, handle_z or t.zw - 0.14, (-sx, 0, 0))
            if loc is not None: add_box_on(c, loc, nrm, (0.12, 0.03, 0.026), 0.01, c.handle_mat or 'chrome', up=(0, 0, 1), sink=0.008)
        if sills:
            # sill strip between the arches
            y0 = c.yf + c.Ra + 0.07; y1 = c.yr - c.Ra - 0.07
            bm = cbox((0.08, y1 - y0, 0.10), 0.03, c.sill_mat or 'plastic')
            xform(bm, Matrix.Translation((sx * (t.hw - 0.025), (y0 + y1) / 2, t.z0 + 0.06)))
            c.add(bm)
        if c.rub_z:
            # a slim rubbing strip along the doors
            y0 = c.yf + c.Ra + 0.10; y1 = c.yr - c.Ra - 0.10
            bm = cbox((0.05, y1 - y0, 0.03), 0.012, c.rub_mat or 'trim')
            xform(bm, Matrix.Translation((sx * (t.hw - 0.012), (y0 + y1) / 2, c.rub_z)))
            c.add(bm)
        # side repeater on the front wing
        loc, nrm = surf(c, 0, c.yf + 0.10, t.zw - 0.12, (-sx, 0, 0))
        if loc is not None: add_box_on(c, loc, nrm, (0.06, 0.028, 0.016), 0.008, 'amber', sink=0.006)


# ---------------------------------------------------------------- cargo and kit
def roof_rack(c, x, y0, y1, z, bars, r=0.016, mat='rack', basket=False):
    """Two rails on feet along the roof with cross bars (basket: a closed frame, the bars inside)."""
    for sx in (-1, 1):
        c.add(tube([(sx * x, y0, z), (sx * x, y1, z)], r, mat))
        for yy in (y0 + 0.06, (y0 + y1) / 2, y1 - 0.06) if basket else (y0 + 0.06, y1 - 0.06):
            loc, nrm = surf(c, sx * x, yy, 0, (0, 0, -1))
            h = z - loc.z + 0.01
            bm = cbox((0.035, 0.07, h + 0.02), 0.01, mat); xform(bm, Matrix.Translation((sx * x, yy, loc.z + h / 2 - 0.01))); c.add(bm)
    for yy in bars:
        c.add(tube([(-x - (0 if basket else 0.035), yy, z + (0 if basket else 0.012)), (x + (0 if basket else 0.035), yy, z + (0 if basket else 0.012))], r * 0.9, mat))
    if basket:
        for yy in (y0, y1):
            c.add(tube([(-x, yy, z), (x, yy, z)], r, mat))


def crate(c, ctr, size, mat='wood'):
    bm = cbox(size, 0.012, mat)
    uv_box(bm, bm.faces, 'wood')
    xform(bm, Matrix.Translation(ctr)); return c.add(bm)


def strap_band(c, ctr, size, axis='y', r=0.06):
    """A strap: a thin rounded band around a box of the given size, across the given axis."""
    sx, sy, sz = size
    if axis == 'y': lo, hi = (-sx / 2 - 0.008, -0.022, -sz / 2 - 0.008), (sx / 2 + 0.008, 0.022, sz / 2 + 0.008); rr = (r, 0.01, r)
    else: lo, hi = (-0.022, -sy / 2 - 0.008, -sz / 2 - 0.008), (0.022, sy / 2 + 0.008, sz / 2 + 0.008); rr = (0.01, r, r)
    bm = rpiece(lo, hi, rr, 'strap', seg=(1, 1, 1))
    xform(bm, Matrix.Translation(ctr)); c.add(bm)


def duffel(c, ctr, size, mat='cloth'):
    sx, sy, sz = size
    rr = min(sx, sy, sz) * 0.42

    def puff(X):
        X = X.copy(); X[:, 2] += 0.02 * np.cos(np.clip(X[:, 0] / (sx / 2), -1, 1) * PI / 2) * (X[:, 2] > 0)
        return X
    bm = rpiece((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2), (rr, rr, rr), mat, seg=(1, 1, 1), deform=puff)
    uv_box(bm, bm.faces, 'cloth')
    xform(bm, Matrix.Translation(ctr)); c.add(bm)
    for dx in (-sx * 0.25, sx * 0.25):
        strap_band(c, Vector(ctr) + Vector((dx, 0, 0)), size, axis='x', r=rr)
    # handles on top
    c.add(tube([Vector(ctr) + Vector(p) for p in ((-0.09, 0, sz / 2), (-0.06, 0, sz / 2 + 0.035), (0.06, 0, sz / 2 + 0.035), (0.09, 0, sz / 2))], 0.011, 'strap', sides=5))


def bedroll(c, ctr, r, length, mat='cloth2'):
    prof = [(0, -length / 2), (r * 0.8, -length / 2), (r, -length / 2 + 0.03), (r, length / 2 - 0.03), (r * 0.8, length / 2), (0, length / 2)]
    bm, _ = lathe(prof, 12, [mat] * 5)
    uv_box(bm, bm.faces, 'cloth')
    xform(bm, Matrix.Translation(ctr) @ Matrix.Rotation(PI / 2, 4, 'Y')); c.add(bm)
    for dx in (-length * 0.3, length * 0.3):
        bm, _ = lathe([(0, -0.02), (r + 0.008, -0.02), (r + 0.008, 0.02), (0, 0.02)], 12, ['strap'] * 3)
        xform(bm, Matrix.Translation(Vector(ctr) + Vector((dx, 0, 0))) @ Matrix.Rotation(PI / 2, 4, 'Y')); c.add(bm)


def jerry_can(c, ctr, mat='can', yaw=0.0):
    sx, sy, sz = 0.28, 0.42, 0.13          # lying flat, the handles toward +y
    bm = rpiece((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2), (0.03, 0.03, 0.03), mat, seg=(1, 1, 1))
    uv_box(bm, bm.faces, 'can')
    M = Matrix.Translation(ctr) @ Matrix.Rotation(yaw, 4, 'Z')
    xform(bm, M); c.add(bm)
    h = [Vector(p) for p in ((-0.09, sy / 2 - 0.01, 0.0), (-0.09, sy / 2 + 0.04, 0.0), (0.09, sy / 2 + 0.04, 0.0), (0.09, sy / 2 - 0.01, 0.0))]
    c.add(tube([M @ p for p in h], 0.012, mat, sides=5))
    bm = cbox((0.05, 0.05, 0.05), 0.012, 'metal'); xform(bm, M @ Matrix.Translation((sx / 2 - 0.06, sy / 2 + 0.01, 0.0))); c.add(bm)


def sack(c, ctr, size, mat='sack'):
    sx, sy, sz = size

    def slump(X):
        X = X.copy(); k = np.clip((X[:, 2] + sz / 2) / sz, 0, 1)
        X[:, 0] *= 1.12 - 0.3 * k; X[:, 1] *= 1.12 - 0.3 * k
        return X
    bm = rpiece((-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2), (sx * 0.4, sy * 0.4, sz * 0.3), mat, seg=(1, 1, 1), deform=slump)
    uv_box(bm, bm.faces, 'cloth')
    xform(bm, Matrix.Translation(ctr)); c.add(bm)
    bm, _ = lathe([(0, 0), (0.05, 0), (0.035, 0.04), (0.06, 0.08), (0, 0.09)], 8, [mat] * 4)
    uv_box(bm, bm.faces, 'cloth')
    xform(bm, Matrix.Translation(Vector(ctr) + Vector((0, 0, sz / 2 - 0.03)))); c.add(bm)
    bm, _ = lathe([(0, 0), (0.042, 0), (0.042, 0.02), (0, 0.02)], 8, ['strap'] * 3)
    xform(bm, Matrix.Translation(Vector(ctr) + Vector((0, 0, sz / 2 + 0.01)))); c.add(bm)


def ball(c, ctr, r, mat, squash=1.0, n=8):
    bm, _ = lathe([(0, -r * squash), (r * 0.72, -r * 0.7 * squash), (r, 0), (r * 0.72, r * 0.7 * squash), (0, r * squash)], n, [mat] * 4)
    xform(bm, Matrix.Translation(ctr)); return c.add(bm)


def mudguard(c, wx, wy, mat='trim', steps=8):
    """A fender plate over a wheel that sits outside the body (the pickup's rear wheels)."""
    rr = c.R + 0.045; half = c.tw / 2 + 0.035
    th = [PI * (0.08 + 0.84 * i / steps) for i in range(steps + 1)]
    path = [(wx, wy + rr * math.cos(a), c.R + rr * math.sin(a)) for a in th]
    sec = [(0, -half), (0.022, -half), (0.022, half), (0, half)]
    ctr = Vector((wx, wy, c.R))
    c.add(sweep(path, lambda i, p, tg: Vector(p) - ctr, sec, mat, caps=True))


def spare_wheel(c, loc, nrm, R, w, cover='cloth'):
    prof = [(0, -w / 2), (0.92 * R, -w / 2), (R, -w / 2 + 0.05), (R, w / 2 - 0.05), (0.94 * R, w / 2), (0.55 * R, w / 2 + 0.012), (0, w / 2 + 0.016)]
    bm, tags = lathe(prof, 18, ['tyre', 'tyre', 'tyre', 'tyre', cover, cover])
    xform(bm, frame(Vector(loc) + Vector(nrm) * (w / 2 + 0.06), nrm)); c.add(bm)
    bm = cbox((0.12, 0.12, 0.08), 0.02, 'metal'); xform(bm, frame(Vector(loc) + Vector(nrm) * 0.03, nrm)); c.add(bm)


def porthole(c, sx, y, z, r):
    loc, nrm = surf(c, 0, y, z, (-sx, 0, 0))
    prof = [(0, -0.02), (r * 1.22, -0.02), (r * 1.22, 0.012), (r * 1.12, 0.026), (r * 1.02, 0.016), (r, 0.004), (0, 0.004)]
    bm, tags = lathe(prof, 18, ['chrome', 'chrome', 'chrome', 'chrome', 'frame', 'glass'])
    lm, lp, _ = lay(bm)
    for f, s_, i in tags:
        if s_ == 5: f[lp] = c.panel_base
    c.panel_base += 1
    xform(bm, frame(loc, nrm)); c.add(bm)


def bull_bar(c, y, z0, z1, x, r=0.032, mat='rack'):
    hoop = [(-x, y, z0), (-x, y, z1 - 0.08), (-x + 0.03, y - 0.005, z1 - 0.02), (-x + 0.1, y - 0.01, z1),
            (x - 0.1, y - 0.01, z1), (x - 0.03, y - 0.005, z1 - 0.02), (x, y, z1 - 0.08), (x, y, z0)]
    c.add(tube(hoop, r, mat, sides=6))
    c.add(tube([(-x, y, (z0 + z1) / 2 - 0.03), (x, y, (z0 + z1) / 2 - 0.03)], r * 0.85, mat, sides=6))
    for sx in (-1, 1):
        c.add(tube([(sx * x, y, z0 + 0.04), (sx * x, y + 0.22, z0 + 0.04)], r * 0.9, mat, sides=6))


# ---------------------------------------------------------------- hatch: a small city hatchback (parked)
def spec_hatch():
    c = Car(); c.type = 'hatch'; c.name = 'Hatch'
    c.paint = (0.80, 0.47, 0.35)                       # faded terracotta, cream roof
    c.pal['paint'] = c.paint; c.pal['paint2'] = (0.95, 0.91, 0.80)
    c.R, c.tw, c.track, c.yf, c.yr = 0.325, 0.20, 0.67, -1.08, 1.13
    c.Ra = c.R + 0.055
    c.rub_z = 0.60; c.rub_mat = 'trim'; c.sill_mat = 'plastic'
    c.tub = Bag(y0=-1.64, y1=1.64, hw=0.79, z0=0.24, zw=0.95, r=(0.13, 0.26, 0.13),
                nose_start=-1.0, nose_drop=0.05, nose_lean=0.05, nose_taper=0.03,
                tail_start=1.25, tail_drop=0.03, tail_lean=0.04, tail_taper=0.02, ylines=(-1.2, -0.97, 1.25))
    c.cab = Bag(yf0=-0.95, yf1=-0.62, yr0=1.24, yr1=1.05, w0=0.74, w1=0.64, zt=1.55, r=(0.13, 0.13, 0.09),
                g0=0.99, g1=1.42, side=[(-0.80, 0.30), (0.44, 0.98)], xw=0.54, xr=0.49, roof='paint2')
    c.wheel_style = 'steel'; c.wheel_cols = ((0.95, 0.92, 0.84), (0.84, 0.86, 0.88))
    c.grille_style = 'slats'
    return c


def build_hatch(c):
    t = c.tub
    tub = c.add(build_tub(c))
    cab = c.add(build_cabin(c))
    # panel gaps: one door a side (its front edge leans back with the A-pillar and its rear
    # edge runs on up the B-pillar), the bonnet and the tailgate (up the C-pillars)
    yd0, yd1, zdb = -0.62, 0.38, 0.42
    door_gaps(c, [((yd0, -0.80), (yd1, yd1))], zdb)
    bonnet_gaps(c, -1.00, 0.60, 0.86)
    tailgate_gaps(c, 0.56, 0.50, c.cab.yr0 - 0.05, up_cabin=True)
    c.bvh = make_bvh([tub, cab])
    common_details(c, doors=[(yd0, yd1)])
    # front: round lamps, a slatted grille with a chrome surround, amber indicators on the corners
    front_lamps(c, 0.50, 0.71, 0.11, ind=(0.71, 0.62, (0.075, 0.05, 0.03)))
    grille(c, 0.67, 0.48, 0.15)
    bumpers(c, 'cream', (0.22, 0.42, 0.16, 0.07, 0.07), (0.24, 0.44, 0.15, 0.07, 0.04))
    # rear: tall combination lamps, plate on the tailgate, a hatch handle
    tail_lamps(c, 0.64, 0.72, 0.13, 0.24)
    loc, nrm = surf(c, 0, 0, 0.66, (0, -1, 0)); plate(c, loc, nrm, sink=0.004)
    loc, nrm = surf(c, 0, 0, 0.82, (0, -1, 0))
    add_box_on(c, loc, nrm, (0.16, 0.035, 0.03), 0.01, 'chrome', sink=0.01)
    add_wiper(c, -0.40, c.cab.g0 + 0.04, 0.42, 0.10)
    add_wiper(c, 0.06, c.cab.g0 + 0.04, 0.40, 0.12)
    add_wiper(c, -0.05, c.cab.g0 + 0.05, 0.34, 0.25, bvh_dir=(0, -1, 0))
    aerial(c, -0.45, -0.25)
    fuel_cap(c, 1.30, 0.82)
    add_flares(c)
    mudflaps(c)


# ---------------------------------------------------------------- wagon: a compact estate with a loaded roof rack (parked)
def spec_wagon():
    c = Car(); c.type = 'wagon'; c.name = 'Wagon'
    c.paint = (0.47, 0.60, 0.72)                       # dusty blue
    c.pal['paint'] = c.paint
    c.pal['cloth'] = (0.72, 0.34, 0.26)                # duffel: rust canvas
    c.pal['cloth2'] = (0.88, 0.64, 0.28)               # rolled tent: mustard
    c.R, c.tw, c.track, c.yf, c.yr = 0.32, 0.20, 0.67, -1.10, 1.15
    c.Ra = c.R + 0.055
    c.rub_z = 0.58; c.rub_mat = 'trim'
    c.tub = Bag(y0=-1.64, y1=1.64, hw=0.79, z0=0.24, zw=0.95, r=(0.12, 0.18, 0.12),
                nose_start=-1.05, nose_drop=0.06, nose_lean=0.04, nose_taper=0.03,
                tail_start=1.4, tail_lean=0.01, tail_taper=0.01, ylines=(-1.25, -1.0))
    c.cab = Bag(yf0=-0.98, yf1=-0.64, yr0=1.50, yr1=1.40, w0=0.74, w1=0.65, zt=1.55, r=(0.12, 0.12, 0.08),
                g0=0.99, g1=1.42, side=[(-0.84, 0.10), (0.24, 0.84), (0.98, 1.30)], xw=0.54, xr=0.50)
    c.wheel_style = 'hubcap'; c.wheel_cols = ((0.95, 0.92, 0.84), (0.80, 0.82, 0.84))
    c.grille_style = 'mesh'
    return c


def build_wagon(c):
    t = c.tub
    tub = c.add(build_tub(c))
    cab = c.add(build_cabin(c))
    zdb = 0.42
    door_gaps(c, [((-0.64, -0.84), (0.17, 0.17)), ((0.17, 0.17), (0.70, 0.91))], zdb)
    bonnet_gaps(c, -1.03, 0.58, 0.85)
    tailgate_gaps(c, 0.56, 0.50, c.cab.yr0 - 0.05, up_cabin=True)
    c.bvh = make_bvh([tub, cab])
    common_details(c, doors=[(-0.64, 0.17), (0.17, 0.80)])
    front_lamps(c, 0.53, 0.70, 0.10, ind=(0.53, 0.53, (0.09, 0.04, 0.03)))
    grille(c, 0.70, 0.58, 0.17)
    fy, fz, ry, rz = bumpers(c, 'chrome', (0.22, 0.40, 0.16, 0.07, 0.07), (0.24, 0.42, 0.15, 0.07, 0.04))
    tail_lamps(c, 0.65, 0.70, 0.12, 0.30)
    loc, nrm = surf(c, 0, 0, 0.62, (0, -1, 0)); plate(c, loc, nrm, sink=0.004)
    loc, nrm = surf(c, 0, 0, 0.80, (0, -1, 0))
    add_box_on(c, loc, nrm, (0.18, 0.035, 0.03), 0.01, 'chrome', sink=0.01)
    add_wiper(c, -0.40, c.cab.g0 + 0.04, 0.42, 0.10)
    add_wiper(c, 0.06, c.cab.g0 + 0.04, 0.40, 0.12)
    add_wiper(c, -0.05, c.cab.g0 + 0.05, 0.38, 0.22, bvh_dir=(0, -1, 0))
    fuel_cap(c, 1.32, 0.80)
    add_flares(c)
    mudflaps(c)
    # the roof rack and its load: a wooden crate, a strapped duffel bag and a rolled tent
    roof_rack(c, 0.52, -0.42, 1.26, c.cab.zt + 0.07, (-0.28, 0.42, 1.08))
    zb = c.cab.zt + 0.096
    crate(c, (0.05, -0.08, zb + 0.09), (0.50, 0.38, 0.18))
    duffel(c, (-0.04, 0.50, zb + 0.085), (0.62, 0.34, 0.17))
    bedroll(c, (0.0, 1.04, zb + 0.085), 0.085, 0.74)


# ---------------------------------------------------------------- van: a small two-tone delivery / camper van (traffic)
def spec_van():
    c = Car(); c.type = 'van'; c.name = 'Van'
    c.paint = (0.32, 0.58, 0.59)                       # faded teal below, cream above
    c.pal['paint'] = c.paint; c.pal['paint2'] = (0.95, 0.91, 0.80)
    c.R, c.tw, c.track, c.yf, c.yr = 0.33, 0.20, 0.70, -1.28, 1.30
    c.Ra = c.R + 0.055
    c.tub = Bag(y0=-1.86, y1=1.86, hw=0.83, z0=0.28, zw=1.00, r=(0.12, 0.18, 0.12),
                nose_start=-1.20, nose_drop=0.10, nose_lean=0.06, nose_taper=0.03, tail_start=1.7, ylines=(-1.48, -1.22))
    c.cab = Bag(yf0=-1.24, yf1=-0.80, yr0=1.84, yr1=1.82, w0=0.80, w1=0.74, zt=1.84, r=(0.13, 0.15, 0.12),
                g0=1.06, g1=1.55, side=[(-1.06, -0.32), (-0.04, 0.60)], xw=0.62, xr=0.62, rear_split=0.05, body='paint2')
    c.wheel_style = 'plain'; c.wheel_cols = ((0.95, 0.94, 0.90), (0.82, 0.84, 0.86))
    c.grille_style = 'slats'
    return c


def build_van(c):
    t = c.tub
    tub = c.add(build_tub(c))
    cab = c.add(build_cabin(c))
    zdb = 0.45
    door_gaps(c, [((-0.80, -1.10), (-0.24, -0.24)), ((-0.12, -0.12), (0.74, 0.74))], zdb, up_front=True)
    bonnet_gaps(c, -1.27, 0.62, 0.84)
    for x in (-0.72, 0.0, 0.72):
        c.gap('rear', (x, 0.48), (x, 1.70))
    c.gap('rear', (-0.72, 0.48), (0.72, 0.48))
    c.gap('rear', (-0.72, 1.70), (0.72, 1.70))
    c.gap('side', (cab_y_at(c, -1.10, 1.64), 1.64), (1.78, 1.64))      # rain gutter
    c.bvh = make_bvh([tub, cab])
    common_details(c, doors=[(-0.80, -0.24), (-0.12, 0.74)], mirror=(c.cab.yf0 + 0.20, t.zw + 0.08, 0.045))
    front_lamps(c, 0.56, 0.68, 0.115, ind=(0.75, 0.62, (0.06, 0.06, 0.03)))
    grille(c, 0.68, 0.62, 0.17)
    fy, fz, ry, rz = bumpers(c, 'chrome', (0.24, 0.44, 0.16, 0.07, 0.07), (0.26, 0.46, 0.15, 0.06, 0.04))
    tail_lamps(c, 0.70, 0.74, 0.12, 0.30)
    loc, nrm = surf(c, -0.36, 0, 0.62, (0, -1, 0)); plate(c, loc, nrm, sink=0.004)
    for sx in (-1, 1):
        loc, nrm = surf(c, sx * 0.10, 0, 1.00, (0, -1, 0))
        add_box_on(c, loc, nrm, (0.12, 0.035, 0.03), 0.01, 'chrome', sink=0.01)
        porthole(c, sx, 1.30, 1.30, 0.165)
        # sliding-door rail along the rear quarter, a chrome strip on the two-tone line
        bm = cbox((0.03, 0.86, 0.022), 0.008, 'trim'); xform(bm, Matrix.Translation((sx * 0.80, 1.16, c.cab.g0 - 0.03))); c.add(bm)
        bm = cbox((0.03, 2.90, 0.022), 0.008, 'chrome'); xform(bm, Matrix.Translation((sx * 0.818, 0.32, t.zw - 0.025))); c.add(bm)
    add_wiper(c, -0.46, c.cab.g0 + 0.05, 0.50, 0.08)
    add_wiper(c, 0.08, c.cab.g0 + 0.05, 0.48, 0.10)
    add_wiper(c, 0.34, c.cab.g0 + 0.06, 0.30, 0.3, bvh_dir=(0, -1, 0))
    # a little roof vent
    loc, nrm = surf(c, 0, 0.30, 0, (0, 0, -1))
    add_box_on(c, loc, Vector((0, 0, 1)), (0.48, 0.40, 0.08), 0.03, 'paint2', up=(0, 1, 0), sink=0.01, inset=(0.04, -0.01, 'paint2', 'trim'))
    fuel_cap(c, 0.98, 0.80)
    # a ladder up the left rear door to the roof
    lx = 0.40; ly = 1.84 + 0.035
    for dx in (-0.13, 0.13):
        c.add(tube([(lx + dx, ly - 0.035, 0.70), (lx + dx, ly, 0.74), (lx + dx, ly, 1.78), (lx + dx, ly - 0.06, 1.86)], 0.014, 'chrome', sides=6))
    for z in (0.92, 1.12, 1.32, 1.52, 1.72):
        c.add(tube([(lx - 0.13, ly, z), (lx + 0.13, ly, z)], 0.011, 'chrome', sides=5, caps=False))
    add_flares(c)
    mudflaps(c, ('F', 'R'))


# ---------------------------------------------------------------- pickup: a little cab-over kei-style truck (traffic)
def spec_pickup():
    c = Car(); c.type = 'pickup'; c.name = 'Pickup'
    c.paint = (0.87, 0.69, 0.32)                       # mustard
    c.pal['paint'] = c.paint
    c.pal['sack'] = (0.80, 0.70, 0.52)
    c.R, c.tw, c.track, c.yf, c.yr = 0.29, 0.17, 0.62, -0.98, 0.98
    c.Ra = c.R + 0.05
    c.no_rear_arch = True
    c.tub = Bag(y0=-1.70, y1=-0.44, hw=0.74, z0=0.32, zw=0.98, r=(0.11, 0.15, 0.11),
                nose_start=-1.45, nose_lean=0.03, nose_taper=0.02, tail_start=-0.6, ylines=(-1.45,))
    c.cab = Bag(yf0=-1.60, yf1=-1.45, yr0=-0.48, yr1=-0.50, w0=0.70, w1=0.64, zt=1.74, r=(0.12, 0.12, 0.10),
                g0=1.03, g1=1.55, side=[(-1.40, -0.74)], xw=0.56, xr=0.40)
    c.wheel_style = 'plain'; c.wheel_cols = ((0.95, 0.94, 0.90), (0.82, 0.84, 0.86))
    c.grille_style = 'slats'
    c.grime_ends = (-1.70, 1.66)
    return c


def build_pickup(c):
    t = c.tub
    tub = c.add(build_tub(c))
    cab = c.add(build_cabin(c))
    door_gaps(c, [((-1.40, -1.52), (-0.62, -0.62))], 0.73, up_front=True)
    c.gap('front', (-0.62, 0.86), (0.62, 0.86))       # the cab's front panel
    # the bed: sub-frame, floor, drop sides, headboard and tailgate, ribs pressed into the sides
    y0, y1, hw, zf, zt = -0.40, 1.62, 0.74, 0.62, 1.02
    bed = []
    bed.append(c.add(rpiece((-0.42, y0 - 0.06, 0.47), (0.42, y1 - 0.08, zf + 0.01), (0.03,) * 3, 'trim', seg=(1, 1, 1))))
    bed.append(c.add(cbox((2 * hw, y1 - y0, 0.10), 0.025, 'paint')))
    xform(bed[-1], Matrix.Translation((0, (y0 + y1) / 2, zf + 0.05)))
    for sx in (-1, 1):
        bm = c.add(cbox((0.05, y1 - y0, zt - zf - 0.06), 0.018, 'paint')); xform(bm, Matrix.Translation((sx * (hw - 0.025), (y0 + y1) / 2, (zf + 0.06 + zt) / 2)))
        bed.append(bm)
    for yy in (y0 + 0.025, y1 - 0.025):
        bm = c.add(cbox((2 * hw - 0.02, 0.05, zt - zf - 0.06 + (0.08 if yy < 0 else 0)), 0.018, 'paint'))
        xform(bm, Matrix.Translation((0, yy, (zf + 0.06 + zt + (0.08 if yy < 0 else 0)) / 2))); bed.append(bm)
    for z in (0.78, 0.90):
        c.gap('side', (y0 + 0.08, z), (y1 - 0.08, z))
        c.gap('rear', (-hw + 0.08, z), (hw - 0.08, z))
    c.bvh = make_bvh([tub, cab] + bed)
    common_details(c, doors=[(-1.40, -0.62)], mirror=(c.cab.yf0 + 0.18, t.zw + 0.08, 0.07), sills=False)
    front_lamps(c, 0.50, 0.64, 0.115, ind=(0.69, 0.64, (0.05, 0.07, 0.03)))
    grille(c, 0.66, 0.50, 0.15)
    loc, nrm = surf(c, 0, 0, t.zw - 0.02, (0, 1, 0))
    add_box_on(c, loc, Vector((0, -1, 0)), (1.30, 0.035, 0.02), 0.008, 'chrome', sink=0.01)
    fy, fz = add_bumper(c, True, 'trim', 0.30, 0.46, 0.16, 0.06, wrap=0.06)
    c.front = (0, fy, fz)
    plate(c, Vector((0, fy - 0.004, fz)), Vector((0, -1, 0)))
    # rear: bumper bar, lamps and plate under the tailgate
    bm = c.add(rpiece((-0.70, y1 - 0.10, 0.40), (0.70, y1 + 0.03, 0.54), (0.04, 0.04, 0.04), 'trim', seg=(1, 1, 1)))
    for sx in (-1, 1):
        add_box_on(c, Vector((sx * 0.56, y1 + 0.03, 0.47)), Vector((0, 1, 0)), (0.16, 0.09, 0.03), 0.015, 'trim', front_region='tail', sink=0.01)
    plate(c, Vector((0, y1 + 0.03, 0.47)), Vector((0, 1, 0)))
    # a guard frame behind the cab
    for sx in (-1, 1):
        c.add(tube([(sx * 0.62, -0.34, zt), (sx * 0.62, -0.34, 1.56), (sx * 0.58, -0.34, 1.60)], 0.022, 'rack'))
    c.add(tube([(-0.58, -0.34, 1.60), (0.58, -0.34, 1.60)], 0.024, 'rack'))
    c.add(tube([(-0.62, -0.34, 1.32), (0.62, -0.34, 1.32)], 0.018, 'rack'))
    add_wiper(c, -0.38, c.cab.g0 + 0.04, 0.40, 0.10)
    add_wiper(c, 0.08, c.cab.g0 + 0.04, 0.40, 0.12)
    add_flares(c, which=('F',))
    for sx in (-1, 1):
        mudguard(c, sx * c.track, c.yr)
    mudflaps(c, ('F', 'R'), h=0.14)
    # the load: a crate of pumpkins and cabbages, a burlap sack and a milk churn
    crate(c, (0.18, 0.18, zf + 0.10 + 0.13), (0.56, 0.44, 0.26))
    for (x, y, r, m) in ((0.02, 0.06, 0.11, 'produce'), (0.30, 0.10, 0.10, 'produce'), (0.10, 0.30, 0.10, 'produce2'), (0.34, 0.31, 0.09, 'produce')):
        ball(c, (x, y, zf + 0.10 + 0.26 + r * 0.45), r, m, squash=0.8)
    sack(c, (-0.36, 0.72, zf + 0.10 + 0.20), (0.34, 0.30, 0.40))
    tb = c.add(rpiece((-0.24, -0.11, 0), (0.24, 0.11, 0.17), (0.02, 0.02, 0.02), 'red', seg=(1, 1, 1)))
    xform(tb, Matrix.Translation((0.30, 1.22, zf + 0.10)) @ Matrix.Rotation(0.25, 4, 'Z'))
    c.add(tube([Matrix.Translation((0.30, 1.22, zf + 0.10)) @ Matrix.Rotation(0.25, 4, 'Z') @ Vector(p)
                for p in ((-0.10, 0, 0.17), (-0.08, 0, 0.23), (0.08, 0, 0.23), (0.10, 0, 0.17))], 0.012, 'trim', sides=5))


# ---------------------------------------------------------------- fourby: a compact boxy off-roader (traffic)
def spec_fourby():
    c = Car(); c.type = 'fourby'; c.name = 'Fourby'
    c.paint = (0.55, 0.65, 0.50)                       # sage green, cream roof
    c.pal['paint'] = c.paint; c.pal['paint2'] = (0.95, 0.91, 0.80)
    c.pal['canvas'] = (0.88, 0.82, 0.66)               # spare wheel cover
    c.rust = 0.5
    c.R, c.tw, c.track, c.yf, c.yr = 0.37, 0.26, 0.72, -1.15, 1.10
    c.Ra = c.R + 0.06
    c.tread_rows = 3; c.tread_depth = 0.024
    c.flare_mat = 'plastic'; c.flare_w = 0.11; c.flare_out = 0.07
    c.sill_mat = 'metal'
    c.tub = Bag(y0=-1.66, y1=1.58, hw=0.80, z0=0.48, zw=1.08, r=(0.09, 0.12, 0.09),
                nose_start=-1.30, nose_drop=0.03, nose_lean=0.02, tail_start=1.4, ylines=(-1.32, -0.98))
    c.cab = Bag(yf0=-0.96, yf1=-0.78, yr0=1.54, yr1=1.52, w0=0.77, w1=0.72, zt=1.62, r=(0.09, 0.10, 0.07),
                g0=1.12, g1=1.50, side=[(-0.80, 0.18), (0.32, 0.90), (1.04, 1.38)], xw=0.62, xr=0.54, roof='paint2')
    c.wheel_style = 'spoke'; c.wheel_cols = ((0.93, 0.90, 0.82), (0.36, 0.37, 0.38))
    c.flap_top_r = 0.44
    c.grille_style = 'vertical'
    return c


def build_fourby(c):
    t = c.tub
    tub = c.add(build_tub(c))
    cab = c.add(build_cabin(c))
    zdb = 0.58
    door_gaps(c, [((-0.58, -0.86), (0.25, 0.25)), ((0.25, 0.25), (0.54, 0.97))], zdb)
    bonnet_gaps(c, -1.00, 0.62, 0.98)
    tailgate_gaps(c, 0.64, 0.58, c.cab.yr0 - 0.05, up_cabin=True)
    c.bvh = make_bvh([tub, cab])
    common_details(c, doors=[(-0.58, 0.25), (0.25, 0.86)])
    front_lamps(c, 0.55, 0.86, 0.115, ind=(0.55, 0.66, (0.10, 0.045, 0.03)))
    grille(c, 0.86, 0.66, 0.26)
    fy, fz = add_bumper(c, True, 'metal', 0.42, 0.64, 0.20, 0.10, wrap=0.05)
    ry, rz = add_bumper(c, False, 'metal', 0.44, 0.64, 0.18, 0.08, wrap=0.03)
    c.front = (0, fy, fz)
    plate(c, Vector((0, fy - 0.004, fz)), Vector((0, -1, 0)))
    bull_bar(c, fy - 0.10, fz + 0.02, 1.00, 0.44)
    plate(c, Vector((0.40, ry + 0.004, rz)), Vector((0, 1, 0)))
    tail_lamps(c, 0.70, 0.86, 0.12, 0.26)
    loc, nrm = surf(c, 0, 0, 0.98, (0, -1, 0))
    spare_wheel(c, loc, nrm, 0.33, 0.22, cover='canvas')
    add_wiper(c, -0.44, c.cab.g0 + 0.04, 0.46, 0.06)
    add_wiper(c, 0.10, c.cab.g0 + 0.04, 0.44, 0.08)
    add_flares(c)
    mudflaps(c, ('F', 'R'), h=0.18)
    # roof basket with two jerry cans and a crate
    zr = c.cab.zt + 0.08
    roof_rack(c, 0.60, -0.55, 1.30, zr, (-0.15, 0.45, 0.95), r=0.018, basket=True)
    jerry_can(c, (-0.24, 0.10, zr + 0.085), 'can')
    jerry_can(c, (0.12, 0.10, zr + 0.085), 'can2')
    crate(c, (0.0, 0.88, zr + 0.11), (0.62, 0.40, 0.18))


# ---------------------------------------------------------------- assembly
def to_object(name, bms, c):
    bm = new_bm()
    for b in bms: merge(bm, b)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = new_obj(name, me)
    # Smooth normals weighted by face area, taken on the n-gons (so a big flat panel keeps its
    # own normal right up to its rounded edges), then triangulated keeping them. One normal per
    # vertex: the ink hull (pushed along the normals) never tears.
    me.shade_smooth()
    m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.mode = 'FACE_AREA'; m.weight = 50; m.keep_sharp = False
    activate(ob); bpy.ops.object.modifier_apply(modifier=m.name)
    m = ob.modifiers.new('tri', 'TRIANGULATE'); m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'; m.keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=m.name)
    n = len(me.polygons)
    mats = np.zeros(n, np.int32); me.attributes['mat'].data.foreach_get('value', mats)
    pans = np.zeros(n, np.int32); me.attributes['panel'].data.foreach_get('value', pans)
    uv = me.uv_layers['UVMap']; part = me.uv_layers.new(name='Part')
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = col; me.color_attributes.render_color_index = 0
    # glass panels: a 2D frame per panel, normalised to its bounds
    pframes = {}
    for pid in set(pans.tolist()):
        if pid < 0: continue
        polys = [p for p in me.polygons if pans[p.index] == pid]
        nrm = sum((p.normal * p.area for p in polys), Vector()).normalized()
        u = Vector((0, 0, 1)).cross(nrm)
        if u.length < 1e-4: u = Vector((1, 0, 0))
        u.normalize(); v = nrm.cross(u)
        cos = [me.vertices[i].co for p in polys for i in p.vertices]
        us = [co.dot(u) for co in cos]; vs = [co.dot(v) for co in cos]
        pframes[pid] = (u, v, min(us), max(us), min(vs), max(vs))
    cols = []; uvs = []; parts = []
    for p in me.polygons:
        mname = MATS[mats[p.index]]
        rgb = c.pal.get(mname, (1, 1, 1))
        mode = UVMODE.get(mname, 'white')
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            cols.extend((rgb[0], rgb[1], rgb[2], 1.0))
            if mode == 'grime':
                nn = p.normal
                mp = pick_map(p.normal)
                s_, t_ = map_st(mp, co)
                uvs.extend(reg_uv(mp, min(max(s_, 0.01), 0.99), min(max(t_, 0.015), 0.985), 0.0))
            elif mode == 'panel':
                pf = pframes[pans[p.index]]
                s = (co.dot(pf[0]) - pf[2]) / max(pf[3] - pf[2], 1e-4); t = (co.dot(pf[1]) - pf[4]) / max(pf[5] - pf[4], 1e-4)
                uvs.extend(reg_uv('glass', s, t, 0.01))
            elif mode == 'keep':
                uvs.extend(uv.data[li].uv)
            else:
                uvs.extend(WHITE_UV)
            parts.extend((1.0 if mname == 'paint' else 0.0, 0.0))
    col.data.foreach_set('color_srgb', cols)
    uv.data.foreach_set('uv', uvs); part.data.foreach_set('uv', parts)
    me.attributes.remove(me.attributes['mat']); me.attributes.remove(me.attributes['panel'])
    return ob


def material(atlas):
    mat = bpy.data.materials.new('Car'); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(atlas)
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(tex.outputs['Color'], mul.inputs['A']); nt.links.new(vc.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.8
    return mat


SPECS = {'hatch': (spec_hatch, build_hatch), 'wagon': (spec_wagon, build_wagon), 'van': (spec_van, build_van),
         'pickup': (spec_pickup, build_pickup), 'fourby': (spec_fourby, build_fourby)}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spec, build = SPECS[TYPE]
    c = spec()
    c.panel_base = 0
    c.grime_arches = [(c.yf, c.Ra), (c.yr, c.Ra)]
    c.grime_ends = c.grime_ends or (c.tub.y0, c.tub.y1)
    build(c)
    stem = os.path.splitext(OUT)[0]
    atlas = stem + 'Atlas.png'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    paint_atlas(atlas, c)
    mat = material(atlas)
    body = to_object('Body', c.pieces, c)
    body.data.materials.append(mat)
    objs = [body]
    tris = len(body.data.polygons)
    wb = build_wheel(c, c.R, c.tw, n=c.wheel_n or 20, rows=c.tread_rows or 2, depth=c.tread_depth or 0.016)
    for k, (wx, wy) in c.wheel_pos().items():
        w = wb.copy()
        if wx < 0: xform(w, Matrix.Scale(-1, 4, (1, 0, 0)))
        wo = to_object('Wheel.' + k, [w], c)
        wo.data.materials.append(mat)
        wo.location = (wx, wy, c.R)
        wo.parent = body; wo.matrix_parent_inverse = Matrix()
        objs.append(wo); tris += len(wo.data.polygons)
    fe = bpy.data.objects.new('Front', None); C.scene.collection.objects.link(fe)
    fe.location = c.front; fe.parent = body; fe.empty_display_size = 0.2
    objs.append(fe)
    # measurements
    vs = [body.matrix_world @ v.co for v in body.data.vertices]
    for o in objs[1:5]: vs += [o.matrix_world @ v.co for v in o.data.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    info = {'paint': [round(x, 4) for x in c.paint], 'tris': tris, 'wheelRadius': c.R,
            'length': round(max(ys) - min(ys), 3), 'width': round(max(xs) - min(xs), 3), 'height': round(max(zs), 3),
            'waist': c.tub.zw, 'roof': c.cab.zt if c.cab else None, 'atlas': os.path.basename(atlas)}
    print('CARINFO', json.dumps(info))
    C.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=stem + '.blend')
    for x in C.scene.objects: x.select_set(False)
    for o in objs: o.select_set(True)
    C.view_layer.objects.active = body
    bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, apply_scale_options='FBX_SCALE_ALL', add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE', use_mesh_modifiers=True, axis_forward='-Z', axis_up='Y',
                             path_mode='STRIP')
    with open(stem + '.json', 'w') as f:
        json.dump(info, f)
    print('exported', OUT, 'tris', tris)


main()
