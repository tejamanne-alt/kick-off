# Rocks for the terrain kit: boulders, a stepping stone, a beach rock cluster, layered cliff
# chunks and the sea headland. Each builder returns (bmesh with face kinds, ctx) for
# kit_terrain.finalize. Everything is made of convex chunks with a few broad planes and rounded
# edges (kit_terrain_geo.chunk / block); chunks that interpenetrate read as cracks and seams,
# and the faces buried inside a neighbour are dropped.
import math, random
from mathutils import Vector, Matrix
import kit_terrain_geo as G
from kit_terrain_geo import Hull, dirv


class Ctx(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v): self[k] = v


# ---------------------------------------------------------------- blocks (cliff strata)
def block_hull(rng, lo, hi, tilt=3.0, lean=4.0, corner=(0.08, 0.35), top_cham=(0.10, 0.32),
               under=(0.0, 0.18), front_facets=True, yaw=0.0, top_slope=0.0, side_cham=True, front_pts=None):
    """A slab-like block: an axis-aligned box (lo, hi) whose faces are nudged into broad,
    slightly skewed planes, with chamfered vertical corners, a chamfered top rim, an optional
    undercut at the front foot, and (front_facets) a front made of two planes meeting in a
    shallow vertical ridge. top_slope tilts the top along x (dz/dx)."""
    lo, hi = Vector(lo), Vector(hi)
    c = (lo + hi) * 0.5; a = (hi - lo) * 0.5
    m = min(a.x, a.y, a.z)
    P = [((0, 0, -1), -lo.z)]
    # top: through the top centre, tilted a little (and along x by top_slope)
    tn = Vector((-top_slope, 0, 1)).normalized()
    tn = (tn + dirv(rng.uniform(0, 360), 0) * math.tan(math.radians(rng.uniform(0, tilt)))).normalized()
    P.append((tn, tn.dot(Vector((c.x, c.y, hi.z)))))
    # four sides (front -Y maybe as two facets)
    for az, face in ((0, Vector((hi.x, c.y, c.z))), (180, Vector((lo.x, c.y, c.z))), (90, Vector((c.x, hi.y, c.z)))):
        n = dirv(yaw + az + rng.uniform(-6, 6), rng.uniform(-lean, lean))
        P.append((n, n.dot(face)))
    if front_pts:
        # the front follows a polyline [(x, y)] (left to right), one leaning plane per segment
        for (x0, y0), (x1, y1) in zip(front_pts[:-1], front_pts[1:]):
            d2 = Vector((y1 - y0, -(x1 - x0), 0)).normalized()
            el = math.radians(rng.uniform(-lean, lean * 0.5))
            n = Vector((d2.x * math.cos(el), d2.y * math.cos(el), math.sin(el)))
            P.append((n, n.dot(Vector((x0, y0, c.z)))))
    elif front_facets:
        nf = rng.choice((2, 2, 3))
        for i in range(nf):
            t = (i + 0.5) / nf * 2 - 1                      # -1 .. 1 across the face
            n = dirv(yaw - 90 + t * rng.uniform(8, 22) + rng.uniform(-5, 5), rng.uniform(-lean, lean * 0.7))
            p = Vector((c.x + t * a.x * 0.6, lo.y + rng.uniform(0, 0.12) * a.y, c.z))
            P.append((n, n.dot(p)))
    else:
        n = dirv(yaw - 90 + rng.uniform(-6, 6), rng.uniform(-lean, lean))
        P.append((n, n.dot(Vector((c.x, lo.y, c.z)))))
    # vertical corner chamfers
    if side_cham:
        for az, cx, cy in ((225, lo.x, lo.y), (315, hi.x, lo.y)):
            n = dirv(yaw + az + rng.uniform(-12, 12), rng.uniform(-3, 3))
            f = rng.uniform(*corner)
            p = Vector((cx, cy, c.z)) - Vector((math.copysign(1, cx - c.x), math.copysign(1, cy - c.y), 0)) * f * min(a.x, a.y)
            P.append((n, n.dot(p)))
    # chamfered top rim (front strongest)
    for az, edge in ((-90, Vector((c.x, lo.y, hi.z))), (0, Vector((hi.x, c.y, hi.z))), (180, Vector((lo.x, c.y, hi.z)))):
        n = dirv(yaw + az + rng.uniform(-10, 10), rng.uniform(38, 55))
        f = rng.uniform(*top_cham) * (1.3 if az == -90 else 1.0)
        P.append((n, n.dot(edge) - f * m))
    # undercut at the front foot
    if under[1] > 0:
        n = dirv(yaw - 90 + rng.uniform(-15, 15), -rng.uniform(30, 50))
        P.append((n, n.dot(Vector((c.x, lo.y, lo.z))) - rng.uniform(*under) * m))
    return Hull(P)


def block(rng, lo, hi, bevel=0.1, segments=2, kind='cliff', **kw):
    h = block_hull(rng, lo, hi, **kw)
    size = Vector(hi) - Vector(lo)
    bm = h.bmesh(kind, weld=min(size) * 0.025)
    G.round_edges(bm, bevel * min(size), segments)
    G.set_kind(bm, kind)
    return bm, h


def rubble(rng, ctr, s, segments=1, kind='rock', **kw):
    """A small rounded chunk lying on the ground at ctr (x, y), about s across."""
    size = (s * rng.uniform(0.9, 1.15), s * rng.uniform(0.75, 0.95), s * rng.uniform(0.5, 0.72))
    p = dict(n=8, majors=2, block=0.3, top_tilt=18)
    p.update(kw)
    return G.chunk(rng, size, bevel=0.18, segments=segments, kind=kind, loc=(ctr[0], ctr[1], 0), rot=rng.uniform(0, 360), **p)


# ---------------------------------------------------------------- boulders
def rock_ctx(seed, ext, z1, **kw):
    c = Ctx(seed=seed, normals='weighted', ao_radius=max(ext * 0.6, 0.4), span=max(ext * 1.05, 3.0), z0=0.0, z1=z1,
            noise_scale=max(ext * 0.7, 0.6), category='boulder', budget=600, fit=ext)
    c.update(kw)
    return c


def boulder1():
    """0.6 m: a low, rounded chunk with a broad sloping top, like a big river pebble."""
    rng = random.Random(113)
    bm, h = G.chunk(rng, (0.62, 0.54, 0.46), bevel=0.22, segments=2, n=10, majors=3, block=0.15, top_tilt=16,
                    el=(-22, 64), sink=0.05)
    return bm, rock_ctx(101, 0.62, 0.46)


def boulder2():
    """1.0 m: a wedge whose broad top slopes down toward the front, a ridge along the back."""
    rng = random.Random(207)
    bm, h = G.chunk(rng, (1.0, 0.84, 0.86), bevel=0.18, segments=2, n=11, majors=3, block=0.35,
                    tops=2, top_tilt=18, extra=[(dirv(-100, 48), 0.5)])
    return bm, rock_ctx(202, 1.0, 0.86)


def boulder3():
    """1.5 m: a heavy main block with a smaller chunk fused to its right flank."""
    rng = random.Random(305)
    a = G.chunk(rng, (1.2, 1.05, 1.0), bevel=0.17, segments=2, n=10, majors=3, block=0.3, top_tilt=10,
                loc=(-0.16, 0.04, 0), rot=8, sink=0.07, el=(-28, 62))
    b = G.chunk(rng, (0.8, 0.74, 0.58), bevel=0.2, segments=2, n=9, majors=1, block=0.4, top_tilt=12,
                cut=(0.92, 1.0), loc=(0.42, -0.16, 0), rot=-25, sink=0.05, el=(-24, 60))
    bm = G.assemble([a, b], 0.03)
    return bm, rock_ctx(303, 1.5, 1.0)


def split_boulder(rng, size, gap, lean, bevel, segments=2, **kw):
    """One rounded boulder cracked in two along a near-vertical plane (normal +X); the halves
    lean apart about their outer feet."""
    h = G.chunk_hull(rng, size, **kw)
    out = []
    nrm = dirv(rng.uniform(-8, 8), rng.uniform(-4, 4))
    for sgn in (-1, 1):
        half = Hull(h.planes + [(nrm * -sgn, -gap * 0.5)])
        bm = half.bmesh('rock', weld=min(size) * 0.03)
        G.round_edges(bm, bevel * min(size), segments)
        G.set_kind(bm, 'rock')
        pivot = Vector((sgn * size[0] * 0.45, 0, 0))
        M = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(lean * sgn), 4, 'Y') @ Matrix.Translation(-pivot)
        G.xform(bm, M)
        out.append((bm, None))
    return G.assemble(out, 0.0)


def boulder4():
    """1.8 m: a tall rounded boulder split down the middle, the two halves leaning apart."""
    rng = random.Random(409)
    bm = split_boulder(rng, (1.6, 1.2, 1.55), gap=0.08, lean=6.0, bevel=0.15, n=12, majors=3, block=0.3,
                       top_tilt=10, sink=0.1, el=(-26, 62))
    return bm, rock_ctx(404, 1.8, 1.55)


def boulder_large1():
    """3.5 m: a broad domed mass with a flank chunk at its front-left foot and a small stone."""
    rng = random.Random(511)
    a = G.chunk(rng, (3.1, 2.6, 2.2), bevel=0.16, segments=2, n=12, majors=4, block=0.2, top_tilt=8,
                loc=(0.15, 0.1, 0), rot=12, sink=0.15, el=(-28, 62))
    b = G.chunk(rng, (1.5, 1.3, 1.0), bevel=0.18, segments=2, n=8, majors=2, block=0.35, top_tilt=18,
                loc=(-1.25, -0.7, 0), rot=-30)
    c = G.chunk(rng, (0.62, 0.55, 0.38), bevel=0.2, segments=1, n=6, majors=2, block=0.3,
                loc=(1.55, -0.95, 0), rot=40)
    bm = G.assemble([a, b, c], 0.04)
    return bm, rock_ctx(505, 3.6, 2.2)


def boulder_large2():
    """3.8 m: a tall leaning monolith with a slanted top, a fallen slab at its foot."""
    rng = random.Random(613)
    a = G.chunk(rng, (2.4, 2.0, 3.7), bevel=0.15, segments=2, n=11, majors=3, block=0.45, top_tilt=24,
                el=(-30, 58), loc=(-0.3, 0.1, 0), rot=-14, center=(0.22, 0.0, 1.8))
    b = G.chunk(rng, (1.7, 1.25, 0.7), bevel=0.2, segments=2, n=8, majors=1, block=0.5, top_tilt=10,
                cut=(0.93, 1.0), major_cut=(0.84, 0.9), loc=(1.05, -0.62, 0), rot=24, sink=0.06)
    bm = G.assemble([a, b], 0.04)
    return bm, rock_ctx(606, 3.8, 3.7)


def stepping_stone():
    """0.9 m across, its top a flat plane at 0.15 m, softly rounded rim."""
    rng = random.Random(707)
    bm, h = G.chunk(rng, (0.92, 0.78, 0.44), center=(0, 0, 0.0), sink=0.06, top_flat=0.15, bevel=0.12,
                    segments=2, n=10, majors=2, el=(-12, 40), cut=(0.9, 0.98), major_cut=(0.84, 0.9), block=0.1)
    return bm, rock_ctx(707, 0.92, 0.15, top_amt=0.8, notes='walkable top: flat at z = 0.15', fit=None)


def rock_cluster():
    """A beach group of four rocks nested together, about 3 m wide."""
    rng = random.Random(812)
    pieces = [
        G.chunk(rng, (1.4, 1.15, 1.2), bevel=0.17, segments=2, n=9, majors=3, block=0.3, top_tilt=14,
                loc=(-0.38, 0.18, 0), rot=15),
        G.chunk(rng, (1.05, 0.9, 0.68), bevel=0.18, segments=2, n=8, majors=2, block=0.3, top_tilt=20,
                loc=(0.5, -0.12, 0), rot=-35),
        G.chunk(rng, (0.8, 0.7, 0.3), bevel=0.22, segments=1, n=7, majors=2, block=0.2, top_tilt=6,
                loc=(1.12, -0.5, 0), rot=10),
        G.chunk(rng, (0.52, 0.46, 0.34), bevel=0.22, segments=1, n=6, majors=2, block=0.3, top_tilt=20,
                loc=(-1.02, -0.36, 0), rot=60),
    ]
    bm = G.assemble(pieces, 0.03)
    return bm, rock_ctx(808, 3.0, 1.2, wet=0.18, notes='beach group; darker wet band near the ground')


# ---------------------------------------------------------------- cliffs
def slab(rng, lo, hi, n=8, majors=3, block=0.55, bevel=0.1, segments=2, kind='cliff', tilt=2.5, el=(-30, 50)):
    """One stratum: a faceted rock slab with a flat bed and a flat (slightly tilted) top, its
    sides cut by a few broad planes at random angles, rims rounded."""
    lo, hi = Vector(lo), Vector(hi)
    size = hi - lo; c = (lo + hi) * 0.5
    h = G.chunk_hull(rng, size, center=c, floor=lo.z, top_flat=hi.z, flat_tilt=tilt, n=n, majors=majors,
                     block=block, el=el, cut=(0.9, 1.0), major_cut=(0.8, 0.9))
    bm = h.bmesh(kind, weld=min(size) * 0.025)
    G.round_edges(bm, bevel * min(size), segments)
    G.set_kind(bm, kind)
    return bm, h


def top_outline(hull, tol=0.03):
    """The polygon where a hull meets its top plane (the plane facing most nearly up)."""
    tn, td = max(hull.planes, key=lambda p: p[0].z)
    pts = [p for p in hull.vertices() if abs(tn.dot(p) - td) < tol]
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    pts.sort(key=lambda p: math.atan2(p.y - cy, p.x - cx))
    return pts, (tn, td), Vector((cx, cy, 0))


def turf_cap(rng, hull, over=0.2, tuck=0.32, drop=0.5, n=22, lump=0.3, dome=0.18):
    """A draped grass cap on a block's top: a lumpy, slightly domed top, a rim that bulges out
    over the rock with a scalloped edge, and an underside that tucks back into the block (so no
    open edge shows from below)."""
    pts, (tn, td), c = top_outline(hull)
    # resample the outline evenly
    per = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    L = sum((b - a).length for a, b in per)
    samples = []
    for k in range(n):
        t = L * k / n
        for a, b in per:
            l = (b - a).length
            if t <= l:
                samples.append(a.lerp(b, t / max(l, 1e-9))); break
            t -= l
    zt = lambda x, y: (td - tn.x * x - tn.y * y) / tn.z
    ph = rng.uniform(0, 6.3); ph2 = rng.uniform(0, 6.3)
    rings = []
    spec = [(-tuck, -drop), (over, -drop * 0.42), (over * 0.72, 0.04), (-0.45, dome * 0.75)]
    for off, dz in spec:
        ring = []
        for k, p in enumerate(samples):
            d = Vector((p.x - c.x, p.y - c.y, 0))
            dl = max(d.length, 1e-6)
            wob = 1 + lump * math.sin(k * 2.0 + ph) * math.sin(k * 0.7 + ph2) if off > 0 else 1.0
            o = off * wob
            x, y = p.x + d.x / dl * o, p.y + d.y / dl * o
            jz = rng.uniform(-0.03, 0.03) if off > 0 else 0.0
            ring.append(Vector((x, y, zt(x, y) + dz + jz)))
        rings.append(ring)
    bm = G.new_bm(); lk = G.klayer(bm)
    R = [[bm.verts.new(p) for p in ring] for ring in rings]
    top = bm.verts.new((c.x, c.y, zt(c.x, c.y) + dome))
    for j in range(len(R) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            for t in ((R[j][k], R[j][k2], R[j + 1][k2]), (R[j][k], R[j + 1][k2], R[j + 1][k])):
                f = bm.faces.new(t); f[lk] = G.KID['grass']
    for k in range(n):
        f = bm.faces.new((R[-1][k], R[-1][(k + 1) % n], top)); f[lk] = G.KID['grass']
    G.fix_normals(bm)
    if sum(f.normal.z * f.calc_area() for f in bm.faces) < 0:
        import bmesh
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.normal_update()
    return bm


def strata_stack(rng, width, depth, layers, x0=0.0, taper=0.12, setback=0.22, split=(1, 2), bevel=0.1,
                 segments=2, kind='cliff', overlap=0.08, n=8):
    """Layered slabs: layers = [(z0, z1)]; each layer split into 1..n slabs along x, each a
    little set back or proud of the face, upper layers narrower. Returns [(bm, hull)] and the
    top layer's hulls."""
    pieces = []; top = []
    nl = len(layers)
    for k, (z0, z1) in enumerate(layers):
        w = width * (1 - taper * k / max(nl - 1, 1)) * rng.uniform(0.94, 1.04)
        cx = x0 + rng.uniform(-0.05, 0.05) * width
        nb = rng.randint(*split)
        cuts = sorted(rng.uniform(0.35, 0.65) if nb == 2 else (i + rng.uniform(0.25, 0.75)) / nb for i in range(nb - 1))
        edges = [0.0] + cuts + [1.0]
        for b in range(nb):
            xa = cx - w / 2 + w * edges[b] - (0.0 if b == 0 else 0.1)
            xb = cx - w / 2 + w * edges[b + 1] + (0.0 if b == nb - 1 else 0.1)
            fy = -depth / 2 + setback * (k / max(nl - 1, 1)) * depth * 0.5 + rng.uniform(-0.1, 0.1) * depth
            lo = (xa, fy, z0 - (overlap if k else 0.06))
            hi = (xb, fy + depth * rng.uniform(0.85, 1.0), z1)
            bm, h = block(rng, lo, hi, bevel=bevel, segments=segments, kind=kind, lean=5.0,
                          corner=(0.1, 0.45), top_cham=(0.08, 0.3), under=(0.0, 0.2), yaw=rng.uniform(-4, 4))
            pieces.append((bm, h))
            if k == nl - 1: top.append(h)
    return pieces, top


def within(budget, make):
    """Build with two-segment bevels, falling back to one if over the triangle budget."""
    for seg in (2, 1):
        bm = make(seg)
        if G.tri_count(bm) * 1.0 <= budget * 0.97 or seg == 1:
            return bm


def cliff_ctx(seed, ext, h, **kw):
    c = Ctx(seed=seed, normals='weighted', ao_radius=max(ext * 0.35, 1.0), span=max(ext * 1.05, 3.0), z0=0.0, z1=h,
            noise_scale=ext * 0.5, category='cliff', budget=2000, strata_h=h)
    c.update(kw)
    return c


def cliff_chunk1():
    """6 m: four faceted strata, the upper ones set back, a draped grass cap on top."""
    def make(seg):
        rng = random.Random(931)
        layers = [(0.0, 1.75), (1.66, 3.2), (3.1, 4.6), (4.5, 5.72)]
        pieces, top = strata_stack(rng, 5.4, 3.4, layers, split=(1, 2), bevel=0.12, segments=seg)
        bm = G.assemble(pieces, 0.04)
        for h in top:
            G.merge(bm, turf_cap(rng, h, over=0.16, tuck=0.28, drop=0.34, dome=0.1))
        return bm
    return within(2000, make), cliff_ctx(911, 6.0, 6.0, fit=6.0, fit_axis='z')


def cliff_chunk2():
    """10 m: five thick strata stepping back as they rise, ledges, a draped grass cap."""
    def make(seg):
        rng = random.Random(944)
        layers = [(0.0, 2.3), (2.2, 4.25), (4.15, 6.1), (6.0, 7.95), (7.85, 9.65)]
        pieces, top = strata_stack(rng, 6.8, 4.0, layers, split=(1, 2), bevel=0.11, segments=seg, taper=0.18)
        bm = G.assemble(pieces, 0.05)
        for h in top:
            G.merge(bm, turf_cap(rng, h, over=0.2, tuck=0.3, drop=0.4, dome=0.12))
        return bm
    return within(2000, make), cliff_ctx(922, 10.0, 10.0, fit=10.0, fit_axis='z')


# ---------------------------------------------------------------- headland
SEG = [1]


def headland():
    """A sea headland, about 60 m wide and 20 m tall: a grassy top rising from the land on the
    left to a high bluff, a layered cliff face toward the sea (front and right), a sea stack and
    fallen blocks at its foot."""
    rng = random.Random(1201)
    nz = G.Waves(1201, 18.0, 2, dims=2)
    X0, X1 = -30.0, 21.0                    # the main mass; the stack stands at x ~ 26

    def top_x(x):                            # crest height along x
        t = (x - X0) / (X1 - X0)
        rise = G.smooth01((t - 0.0) / 0.62) ** 0.85
        return 0.6 + 19.4 * rise * (1 - 0.06 * G.smooth01((t - 0.75) / 0.25)) + 0.6 * nz(x, 0.0) * rise

    def front_y(x):
        return -9.0 + 1.6 * math.sin(x * 0.19 + 0.6) + 0.8 * math.sin(x * 0.47 + 2.0) - 2.0 * G.smooth01((x - 4) / 12)

    back_y = 14.0
    pieces = []
    # buttress columns of varied width and protrusion; each a stack of faceted strata, the top
    # block's face following the grass lip's front line so the lip tucks into it
    xs = [X0 + 3.5]
    while xs[-1] < X1 - 3.0:
        xs.append(min(xs[-1] + rng.uniform(4.5, 10.5), X1))
    xs[-1] = X1
    for i in range(len(xs) - 1):
        xa, xb = xs[i] - 0.3, xs[i + 1] + 0.3
        xm = (xa + xb) * 0.5
        slope = (top_x(xb) - top_x(xa)) / (xb - xa)
        ztop = top_x(xm) - 0.9
        zmin = min(top_x(xa), top_x(xb)) - 1.0
        if ztop < 1.2: continue
        nl = max(1, min(4, int(round(zmin / 4.4)) + 1)) if zmin > 3.0 else 1
        cuts = sorted(rng.uniform(0.25, 0.92) for _ in range(nl - 1))
        hs = [(zmin - 1.2) * c for c in cuts] + [ztop]
        col = rng.uniform(-1.6, 1.3)             # the whole buttress proud (-) or set back (+)
        line = [(x, front_y(x)) for x in (xa, xm, xb)]
        fm = min(y for _, y in line)
        z = 0.0
        for k, z1 in enumerate(hs):
            if k == nl - 1:
                off = rng.uniform(0.45, 0.65)
                pts = [(x, y + off) for x, y in line]
                lo = (xa + rng.uniform(-0.3, 0.3), min(y for _, y in pts), z - 0.25)
                hi = (xb + rng.uniform(-0.3, 0.3), back_y - 2.0, z1)
                bm, h = block(rng, lo, hi, bevel=0.05, segments=SEG[0], top_slope=slope * 0.9, top_cham=(0.06, 0.14),
                              corner=(0.05, 0.2), under=(0.0, 0.12), front_pts=pts)
            else:
                fy = fm + col + rng.uniform(-0.6, 0.6) + (0.7 if k == 0 else 0.0)
                lo = (xa + rng.uniform(-0.5, 0.2), fy, z - (0.3 if k == 0 else 0.25))
                hi = (xb + rng.uniform(-0.2, 0.5), back_y - 2.0, z1 + 0.05)
                bm, h = block(rng, lo, hi, bevel=0.06, segments=SEG[0], tilt=1.5, lean=5.0, corner=(0.1, 0.4),
                              top_cham=(0.08, 0.28), under=(0.0, 0.22), yaw=rng.uniform(-4, 4))
            pieces.append((bm, h))
            z = z1
    # the seaward (right) end: two big slabs stepping down from the bluff
    for k, (z0, z1, x0, x1) in enumerate(((0.0, 6.5, X1 - 2.0, X1 + 2.6), (6.3, 12.5, X1 - 2.5, X1 + 1.4))):
        lo = (x0, front_y(X1) + 0.6 + k * 0.8, z0 - 0.25)
        hi = (x1, back_y - 4.0, z1)
        bm, h = block(rng, lo, hi, bevel=0.06, segments=SEG[0], lean=5.0, corner=(0.1, 0.4), top_cham=(0.1, 0.3))
        pieces.append((bm, h))
    # the sea stack: three tapering strata and a grass cap
    sx, sy = 26.6, -6.4
    zs = [(0.0, 4.3), (4.15, 7.9), (7.75, 10.6)]
    for k, (z0, z1) in enumerate(zs):
        w = 5.4 - k * 0.7
        dx = rng.uniform(-0.4, 0.4)
        lo = (sx - w / 2 + dx, sy - 2.3 + k * 0.25, z0 - (0.25 if k == 0 else 0.1))
        hi = (sx + w / 2 + dx, sy + 2.5 - k * 0.25, z1)
        bm, h = block(rng, lo, hi, bevel=0.08, segments=SEG[0], lean=6.0, corner=(0.15, 0.5), top_cham=(0.1, 0.3),
                      yaw=rng.uniform(-10, 10))
        pieces.append((bm, h))
        if k == len(zs) - 1:
            stack_top = h
    # fallen blocks at the foot
    for (x, y, sz) in ((18.5, -11.8, 3.2), (22.8, -9.4, 2.4), (13.0, -12.4, 2.0), (29.6, -8.8, 1.8),
                       (24.2, -11.0, 1.3), (5.0, -12.0, 1.6), (-8.0, -10.8, 1.4), (31.0, -4.0, 1.5)):
        pieces.append(rubble(rng, (x, y), sz, segments=1))
    rock = G.assemble(pieces, 0.08)
    G.merge(rock, turf_cap(rng, stack_top, over=0.45, tuck=0.6, drop=0.9, n=20, dome=0.35))

    # grass cap: a sheet over the top. Front rows: a bulging lip that tucks back into the top
    # blocks (no open edge seen from below); back rows: a grassy slope down to the ground.
    rows = [('dz', 1.6, -2.0), ('dz', -0.15, -1.15), ('dz', 0.35, -0.35), ('dz', 1.3, -0.05)]
    for t in (0.0, 0.2, 0.42, 0.65, 0.85, 1.0):
        rows.append(('in', t, 0.0))
    rows += [('back', 3.5, 0.45), ('back', 7.5, 0.0)]
    cols = [(X0 - 1.0 + (X1 - 0.3 - (X0 - 1.0)) * i / 44, 0.0, 0.0) for i in range(45)]
    cols += [(X1 + 0.55, X1, -1.15), (X1 - 1.0, X1, -2.0)]
    cap = G.new_bm(); lk = G.klayer(cap)
    V = []
    for kind, a1, a2 in rows:
        row = []
        for x, xt, cdz in cols:
            xx = xt if xt else x
            T = top_x(xx); F = front_y(xx)
            if kind == 'dz':
                y, z = F + a1, T + a2 + cdz
            elif kind == 'in':
                y = (F + 2.5) + (back_y - (F + 2.5)) * a1
                dome = 0.6 * math.sin(math.pi * min(a1 / 0.7, 1.0)) * G.smooth01((T - 2) / 6)
                bump = 0.4 * nz(xx * 1.7, y * 1.7) * G.smooth01((T - 1) / 4)
                z = T + dome + bump + cdz
            else:
                y, z = back_y + a1, T * a2 + cdz
            if x == cols[0][0]: z = -0.25
            row.append(cap.verts.new((x, y, max(z, -0.3))))
        V.append(row)
    for j in range(len(rows) - 1):
        for i in range(len(cols) - 1):
            a, b, c, d = V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]
            for t in ((a, b, c), (a, c, d)):
                f = cap.faces.new(t); f[lk] = G.KID['grass']
    G.fix_normals(cap)
    import bmesh
    if sum(f.normal.z * f.calc_area() for f in cap.faces) < 0:
        bmesh.ops.reverse_faces(cap, faces=cap.faces[:])
    G.merge(rock, cap)
    ctx = Ctx(seed=1201, normals='weighted', ao_radius=7.0, span=62.0, z0=0.0, z1=20.0, noise_scale=20.0,
              category='landscape', budget=6000, wet=1.4, strata_h=20.0, grass_span=24.0)
    return rock, ctx
