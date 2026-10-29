# Geometry helpers for the terrain kit (kit_terrain.py): convex rock chunks with rounded edges,
# heightfield strips (optionally periodic in x so they tile), iso-line cuts for crisp part
# boundaries (snow, meadow), lathe heaps, simple conifers, and the baked ambient occlusion.
#
# Every piece is a bmesh with a face int layer 'kind' (an index into KINDS); kit_terrain.py
# turns kinds into colours, atlas regions and recolour parts.
import bmesh, math, itertools, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

KINDS = ('rock', 'cliff', 'grass', 'snow', 'mrock', 'meadow', 'hill', 'sand', 'gravel', 'pebble',
         'conifer', 'trunk', 'soil')
KID = {k: i for i, k in enumerate(KINDS)}
PI = math.pi


def smooth01(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def sstep(e0, e1, x):
    return smooth01((x - e0) / (e1 - e0))


def lerp(a, b, t):
    return a + (b - a) * t


def mix3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def smax(a, b, k):
    """Smooth maximum (polynomial), k = blend width."""
    if k <= 0: return max(a, b)
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k * 0.25


def smin(a, b, k):
    return -smax(-a, -b, k)


def wrap(d, W):
    """Signed periodic difference."""
    return (d + W * 0.5) % W - W * 0.5


class Waves:
    """Smooth pseudo-noise from a few random plane waves (cheap, deterministic, optionally
    periodic in x with period W so tiled strips stay seamless)."""
    def __init__(self, seed, scale, octaves=3, W=None, dims=3):
        r = random.Random(seed)
        self.w = []
        for o in range(octaves):
            for k in range(3):
                f = 2 * PI * (2.0 ** o) / scale          # angular frequency
                th = r.uniform(0, 2 * PI); el = r.uniform(-0.5, 0.5) if dims == 3 else 0.0
                kx, ky, kz = f * math.cos(th) * math.cos(el), f * math.sin(th) * math.cos(el), f * math.sin(el)
                if W:                                    # snap to whole cycles per period
                    kx = round(kx * W / (2 * PI)) * 2 * PI / W
                self.w.append((kx, ky, kz, r.uniform(0, 2 * PI), 0.55 ** o))
        self.norm = sum(a for *_, a in self.w) * 0.6

    def __call__(self, x, y, z=0.0):
        s = 0.0
        for kx, ky, kz, ph, a in self.w:
            s += a * math.sin(kx * x + ky * y + kz * z + ph)
        return max(-1.0, min(1.0, s / self.norm))


# ---------------------------------------------------------------- bmesh basics
def new_bm():
    bm = bmesh.new()
    bm.faces.layers.int.new('kind')
    return bm


def klayer(bm):
    return bm.faces.layers.int.get('kind') or bm.faces.layers.int.new('kind')


def set_kind(bm, kind, faces=None):
    lk = klayer(bm)
    for f in (bm.faces if faces is None else faces):
        f[lk] = KID[kind]
    return bm


def kind_of(bm, f):
    return KINDS[f[klayer(bm)]]


def merge(dst, src):
    lk, sk = klayer(dst), klayer(src)
    vmap = {v: dst.verts.new(v.co) for v in src.verts}
    for f in src.faces:
        try:
            nf = dst.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[lk] = f[sk]
    return dst


def xform(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if M.to_3x3().determinant() < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def fix_normals(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


def tri_count(bm):
    return sum(len(f.verts) - 2 for f in bm.faces)


def dirv(az, el):
    """Unit vector from azimuth (from +X toward +Y) and elevation, degrees."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))


# ---------------------------------------------------------------- convex chunks
class Hull:
    """A convex polytope: the intersection of the half-spaces n . x <= d (n unit)."""
    def __init__(self, planes):
        self.planes = [(Vector(n).normalized(), float(d)) for n, d in planes]

    def inside(self, p, margin=0.0):
        return all(n.dot(p) <= d - margin for n, d in self.planes)

    def vertices(self):
        P = self.planes; pts = []
        for i, j, k in itertools.combinations(range(len(P)), 3):
            M = Matrix((P[i][0], P[j][0], P[k][0]))
            if abs(M.determinant()) < 1e-7: continue
            p = M.inverted() @ Vector((P[i][1], P[j][1], P[k][1]))
            if all(n.dot(p) <= d + 1e-5 for n, d in P):
                if not any((p - q).length < 1e-4 for q in pts):
                    pts.append(p)
        return pts

    def bmesh(self, kind='rock', weld=0.0):
        bm = new_bm()
        vs = [bm.verts.new(p) for p in self.vertices()]
        res = bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
        junk = list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
        if junk: bmesh.ops.delete(bm, geom=junk, context='VERTS')
        if weld > 0:
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), use_dissolve_boundaries=False,
                                 verts=bm.verts[:], edges=bm.edges[:])
        fix_normals(bm)
        set_kind(bm, kind)
        return bm


def round_edges(bm, offset, segments=2, min_angle=12.0, skip_down=True, profile=0.5):
    """Bevel the creased edges (soft, rounded), leaving the flat ground face's rim alone."""
    bm.normal_update()
    edges = []
    for e in bm.edges:
        if len(e.link_faces) != 2: continue
        if math.degrees(e.calc_face_angle(0.0)) < min_angle: continue
        if skip_down and any(f.normal.z < -0.97 for f in e.link_faces): continue
        edges.append(e)
    if edges and offset > 0 and segments > 0:
        bmesh.ops.bevel(bm, geom=edges, offset=offset, offset_type='OFFSET', segments=segments,
                        profile=profile, affect='EDGES', clamp_overlap=True, loop_slide=True)
    fix_normals(bm)
    return bm


def chunk_hull(rng, size, center=None, sink=0.04, n=11, top_tilt=12.0, cut=(0.9, 1.0), majors=3,
               major_cut=(0.76, 0.86), el=(-38.0, 64.0), block=0.25, tops=1, cut_top=(0.95, 1.0),
               top_flat=None, extra=(), floor=None, flat_tilt=0.0):
    """Plane set for one chunky rock: a flat ground face, a (tilted) top, and n planes whose
    normals are spread evenly (a jittered spiral) between the elevations el, at random depths:
    a few 'major' planes cut deep and become the broad faces, the rest trim the rims. Each plane
    sits at the support distance of an ellipsoid (block = 0) or a box (block = 1) of the given
    full size, times its cut factor."""
    a = Vector(size) * 0.5
    c = Vector(center) if center is not None else Vector((0, 0, a.z - sink))

    def rad(nn):
        e = math.sqrt((a.x * nn.x) ** 2 + (a.y * nn.y) ** 2 + (a.z * nn.z) ** 2)
        b = abs(a.x * nn.x) + abs(a.y * nn.y) + abs(a.z * nn.z)
        return e * (1 - block) + b * block

    P = [((0, 0, -1), sink if floor is None else -floor)]
    if top_flat is not None:
        nn = dirv(rng.uniform(0, 360), 90 - rng.uniform(0.0, flat_tilt))
        P.append((nn, nn.dot(Vector((c.x, c.y, top_flat)))))
    else:
        for t in range(tops):
            nn = dirv(rng.uniform(0, 360), 90 - rng.uniform(0.2, 1.0) * top_tilt * (1 + 0.8 * t))
            P.append((nn, nn.dot(c) + rng.uniform(*cut_top) * rad(nn)))
    ga = 180.0 * (3 - math.sqrt(5))
    off = rng.uniform(0, 360)
    s0, s1 = math.sin(math.radians(el[1])), math.sin(math.radians(el[0]))
    major = set(rng.sample(range(n), min(majors, n)))
    for i in range(n):
        z = s0 + (s1 - s0) * (i + rng.uniform(0.2, 0.8)) / n
        e = math.degrees(math.asin(max(-1, min(1, z)))) + rng.uniform(-6, 6)
        az = off + i * ga + rng.uniform(-14, 14)
        nn = dirv(az, e)
        f = rng.uniform(*(major_cut if i in major else cut))
        P.append((nn, nn.dot(c) + f * rad(nn)))
    for nn, d in extra:
        P.append((Vector(nn).normalized(), d))
    return Hull(P)


def chunk(rng, size, bevel=0.18, segments=2, kind='rock', loc=(0, 0, 0), rot=0.0, weld_frac=0.03, **kw):
    """A rounded convex rock chunk. bevel is a fraction of the smallest size. Returns (bm, hull)
    with the hull already moved to loc / rotated by rot (degrees about Z)."""
    h = chunk_hull(rng, size, **kw)
    bm = h.bmesh(kind, weld=min(size) * weld_frac)
    round_edges(bm, bevel * min(size), segments)
    set_kind(bm, kind)
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rot), 4, 'Z')
    xform(bm, M)
    R = M.to_3x3()
    hull = Hull([(R @ n, d + (R @ n).dot(Vector(loc))) for n, d in h.planes])
    return bm, hull


def cull_buried(bm, hulls, margin):
    """Delete faces lying wholly inside another chunk (they can never be seen)."""
    dead = []
    for f in bm.faces:
        for h in hulls:
            if all(h.inside(v.co, margin) for v in f.verts):
                dead.append(f); break
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='FACES')
    return bm


def assemble(pieces, margin):
    """pieces: [(bm, hull)]. Merge them, dropping faces buried inside the others."""
    out = new_bm()
    for i, (bm, h) in enumerate(pieces):
        others = [hh for j, (_, hh) in enumerate(pieces) if j != i and hh is not None]
        cull_buried(bm, others, margin)
        merge(out, bm)
    return out


# ---------------------------------------------------------------- heightfields
def grid_surface(xs, ys, fz, kind='hill'):
    """A surface z = fz(x, y) over the grid xs x ys. Each cell is split along the diagonal whose
    midpoint lies closest to the true surface, so ridges and valleys keep their crease lines.
    Returns (bm, V) with V[j][i] the vertex at (xs[i], ys[j])."""
    bm = new_bm()
    V = [[bm.verts.new((x, y, fz(x, y))) for x in xs] for y in ys]
    lk = klayer(bm); kid = KID[kind]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            a, b, c, d = V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]
            fc = fz((xs[i] + xs[i + 1]) * 0.5, (ys[j] + ys[j + 1]) * 0.5)
            if abs((a.co.z + c.co.z) * 0.5 - fc) <= abs((b.co.z + d.co.z) * 0.5 - fc):
                tt = ((a, b, c), (a, c, d))
            else:
                tt = ((a, b, d), (b, c, d))
            for t in tt:
                f = bm.faces.new(t); f[lk] = kid
    bm.normal_update()
    return bm, V


def end_caps(bm, V, kind='soil'):
    """Close the two x ends of a strip down to z = 0 (hidden when the strip is tiled)."""
    lk = klayer(bm)
    for col, sgn in ((0, -1), (-1, 1)):
        ring = [V[j][col] for j in range(len(V))]
        y0, y1 = ring[0].co.y, ring[-1].co.y; x = ring[0].co.x
        pts = list(ring)
        if ring[-1].co.z > 1e-3: pts.append(bm.verts.new((x, y1, 0.0)))
        if ring[0].co.z > 1e-3: pts.append(bm.verts.new((x, y0, 0.0)))
        try:
            f = bm.faces.new(pts)
        except ValueError:
            continue
        f.normal_update()
        if f.normal.x * sgn < 0: f.normal_flip()
        f[lk] = KID[kind]
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='EAR_CLIP')
    return bm


def contour_cut(bm, fields, key, t=0.5):
    """Cut bm's faces along the iso-line fields[key] = t (piecewise linear), so a part boundary
    is a crisp smooth line instead of a stair of triangles. fields: {name: {BMVert: value}};
    every field is interpolated onto the new vertices."""
    s = fields[key]
    for v in bm.verts:
        if abs(s[v] - t) < 1e-6: s[v] = t + 2e-6
    cut = [e for e in bm.edges if (s[e.verts[0]] - t) * (s[e.verts[1]] - t) < 0]
    new = set()
    for e in cut:
        v0, v1 = e.verts
        f = (t - s[v0]) / (s[v1] - s[v0])
        _, nv = bmesh.utils.edge_split(e, v0, f)
        for fd in fields.values():
            fd[nv] = fd[v0] + (fd[v1] - fd[v0]) * f
        s[nv] = t
        new.add(nv)
    for face in list(bm.faces):
        vs = [v for v in face.verts if v in new]
        if len(vs) == 2 and not any(set(e.verts) == set(vs) for e in face.edges):
            bmesh.utils.face_split(face, vs[0], vs[1])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    return bm


def face_mean(fd, f):
    return sum(fd[v] for v in f.verts) / len(f.verts)


# ---------------------------------------------------------------- lathe heaps
def heap(rings, segs, fr, kind='sand', jitter=None):
    """A heap on the ground: rings of radius fraction u in (0, 1] at angle a give the point
    fr(u, a) -> (x, y, z); a single apex vertex at u = 0."""
    bm = new_bm(); lk = klayer(bm)
    ax, ay, az = fr(0.0, 0.0)
    apex = bm.verts.new((ax, ay, az))
    R = []
    for k in range(1, rings + 1):
        u = k / rings
        R.append([bm.verts.new(fr(u, 2 * PI * (i + 0.5 * (k % 2)) / segs)) for i in range(segs)])
    for i in range(segs):
        f = bm.faces.new((apex, R[0][i], R[0][(i + 1) % segs])); f[lk] = KID[kind]
    for k in range(rings - 1):
        A, B = R[k], R[k + 1]
        for i in range(segs):
            i2 = (i + 1) % segs
            if k % 2 == 0:   # B is shifted half a step forward
                tt = ((A[i], B[i], A[i2]), (A[i2], B[i], B[i2]))
            else:
                tt = ((A[i], B[(i - 1) % segs], B[i]), (A[i], B[i], A[i2]))
            for t in tt:
                f = bm.faces.new(t); f[lk] = KID[kind]
    fix_normals(bm)
    # outward / upward
    if sum(f.normal.z * f.calc_area() for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.normal_update()
    return bm


# ---------------------------------------------------------------- conifers
def conifer(rng, base, height, radius, tiers=3, points=6, lean=(0.0, 0.0), trunk=0.35):
    """A small stylized conifer: stacked drooping tiers with a spiky star rim, a pointed tip and
    a stub of trunk. Returns a bmesh (kinds 'conifer' and 'trunk')."""
    bm = new_bm(); lk = klayer(bm)
    bx, by, bz = base
    lx, ly = lean
    def P(x, y, z):
        t = (z - bz) / height
        return Vector((bx + x + lx * t * height, by + y + ly * t * height, z))
    z0 = bz + height * trunk * rng.uniform(0.8, 1.1)
    span = (bz + height) - z0
    phase = rng.uniform(0, 2 * PI)
    for k in range(tiers):
        tk = k / tiers
        zr = z0 + span * tk * 0.86                       # rim height
        th = span * (0.48 if k < tiers - 1 else 1.0 - tk * 0.86)   # tier cone height
        za = min(zr + th, bz + height)
        rk = radius * (1.0 - 0.62 * tk) * rng.uniform(0.92, 1.06)
        n = points * 2
        ring = []
        for i in range(n):
            a = phase + k * 0.9 + 2 * PI * i / n + rng.uniform(-0.08, 0.08)
            out = (i % 2 == 0)
            r = rk * (1.0 if out else 0.66)
            dz = -th * (0.16 if out else 0.0)
            ring.append(bm.verts.new(P(r * math.cos(a), r * math.sin(a), zr + dz)))
        apex = bm.verts.new(P(0, 0, za))
        under = bm.verts.new(P(0, 0, zr + th * 0.12))
        for i in range(n):
            f = bm.faces.new((ring[i], ring[(i + 1) % n], apex)); f[lk] = KID['conifer']
            f = bm.faces.new((ring[(i + 1) % n], ring[i], under)); f[lk] = KID['conifer']
    # trunk stub: a thin square prism from below the ground to the first tier
    tw = radius * 0.13
    q = []
    for z in (bz - 0.3, z0 + span * 0.05):
        q.append([bm.verts.new(P(tw * math.cos(a), tw * math.sin(a), z)) for a in (PI / 4, 3 * PI / 4, 5 * PI / 4, 7 * PI / 4)])
    for i in range(4):
        f = bm.faces.new((q[0][i], q[0][(i + 1) % 4], q[1][(i + 1) % 4], q[1][i])); f[lk] = KID['trunk']
    bm.normal_update()
    return bm


# ---------------------------------------------------------------- shading data
def vertex_normals(me):
    """Per-vertex shading normal: the mean of its corner normals."""
    acc = [Vector((0, 0, 0)) for _ in me.vertices]
    cn = me.corner_normals
    for li, l in enumerate(me.loops):
        acc[l.vertex_index] += cn[li].vector
    out = []
    for v, a in zip(me.vertices, acc):
        out.append(a.normalized() if a.length > 1e-8 else v.normal.copy())
    return out


def _hemi(n):
    """n cosine-weighted directions on the +Z hemisphere (golden spiral)."""
    out = []
    ga = PI * (3 - math.sqrt(5))
    for i in range(n):
        r = math.sqrt((i + 0.5) / n)
        a = i * ga
        out.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(max(0.0, 1 - r * r)))))
    return out


def bake_ao(me, normals, radius, rays=40, ground=0.0, shifts=(), ground_weight=0.8):
    """Ambient occlusion per vertex (1 = open sky), by ray casts against the mesh (plus copies
    moved by `shifts`, for strips that tile) and the ground plane z = ground."""
    V = [v.co.copy() for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    allV, allF = list(V), list(F)
    for s in shifts:
        off = len(allV)
        allV += [v + Vector(s) for v in V]
        allF += [tuple(i + off for i in f) for f in F]
    bvh = BVHTree.FromPolygons(allV, allF, all_triangles=False)
    H = _hemi(rays)
    eps = radius * 1e-3
    ao = []
    for co, n in zip(V, normals):
        t = n.orthogonal().normalized(); b = n.cross(t)
        occ = 0.0
        o = co + n * eps
        for d in H:
            w = t * d.x + b * d.y + n * d.z
            hit = bvh.ray_cast(o, w, radius)
            h = 0.0
            if hit[0] is not None:
                h = 1.0 - smooth01(hit[3] / radius)
            if w.z < -1e-4 and co.z > ground - 0.05:
                tg = (co.z - ground) / -w.z
                if tg < radius:
                    h = max(h, ground_weight * (1.0 - smooth01(tg / radius)))
            occ += h
        ao.append(1.0 - occ / len(H))
    return ao
