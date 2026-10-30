# Landforms for the terrain kit: distant strips (mountain ranges, rolling hills, a forest band)
# that tile seamlessly along x (their heights, colours and atlas mapping are periodic with the
# strip width), sand dunes, and the sand and gravel piles. Builders return (bmesh, ctx) for
# kit_terrain.finalize.
import math, random
import bmesh
from mathutils import Vector
import kit_terrain_geo as G
from kit_terrain_geo import smooth01, sstep, smax, smin, wrap, Waves
from kit_terrain_rocks import Ctx


def columns(W, n, extra=()):
    """n + 1 x positions over [-W/2, W/2], with the extra x (peak apexes) snapped in."""
    xs = [-W / 2 + W * i / n for i in range(n + 1)]
    step = W / n
    for e in extra:
        e = wrap(e, W)
        j = min(range(len(xs)), key=lambda i: abs(xs[i] - e))
        if 0 < j < len(xs) - 1:
            if abs(xs[j] - e) < step * 0.3: xs[j] = e
            else: xs.append(e)
    return sorted(xs)


def rows_with(base, extra=(), mind=1.5):
    ys = list(base)
    for e in extra:
        j = min(range(len(ys)), key=lambda i: abs(ys[i] - e))
        if 0 < j < len(ys) - 1:
            if abs(ys[j] - e) < mind: ys[j] = e
            else: ys.append(e)
    return sorted(ys)


def vfields(bm, fns):
    return {k: {v: f(v.co) for v in bm.verts} for k, f in fns.items()}


# ---------------------------------------------------------------- mountains
class Peak:
    """A pyramidal mountain: facets [(azimuth of the downhill direction, slope)] meet in straight
    ridges at the apex (px, py, H); the faces are slightly concave (power p), flaring into the
    foothills."""
    def __init__(self, px, py, H, facets, p=1.35):
        self.px, self.py, self.H, self.p = px, py, H, p
        self.f = [(math.cos(math.radians(a)) * s, math.sin(math.radians(a)) * s) for a, s in facets]

    def __call__(self, x, y, W):
        dx = wrap(x - self.px, W); dy = y - self.py
        m = max(fx * dx + fy * dy for fx, fy in self.f)
        t = max(m, 0.0) / self.H
        return self.H * max(0.0, 1.0 - t) ** self.p if t < 1 else 0.0


def facets(rng, front=0.62, n=5, spread=(0.8, 1.25)):
    """Downhill directions around the compass with a front (-Y) facet, slopes ~ front * spread."""
    out = [(-90 + rng.uniform(-14, 14), front * rng.uniform(0.95, 1.08))]
    base = rng.uniform(0, 360)
    for i in range(1, n):
        az = -90 + 360 * i / n + rng.uniform(-18, 18)
        out.append((az, front * rng.uniform(*spread)))
    return out


def mountain_range(seed, W, peaks_spec, spurs, foot, snowline, depth=(-92.0, 56.0), ncols=78):
    """A distant range W wide that tiles along x: pyramidal peaks (peaks_spec: x, y, height,
    front slope, facets) and front spurs merged with a smooth maximum, a band of foothills (foot:
    height, y, width), snow above the snowline (more in hollows, less on steep faces), meadow
    on the gentle low ground; snow and meadow edges are cut into the mesh as crisp lines."""
    rng = random.Random(seed)
    y0, y1 = depth
    peaks = []
    for (px, py, H, front, n) in peaks_spec:
        peaks.append(Peak(px, py, H, facets(rng, front, n), p=rng.uniform(1.25, 1.5)))
    for (px, py, H, front) in spurs:
        peaks.append(Peak(px, py, H, facets(rng, front, 4, (0.9, 1.4)), p=1.2))
    fnz = Waves(seed + 1, 70.0, 2, W=W, dims=2)
    snz = Waves(seed + 2, 40.0, 2, W=W, dims=2)

    def h(x, y):
        z = 0.0
        for pk in peaks:
            z = smax(z, pk(x, y, W), 7.0)
        # foothills: low rolling band near the front
        fh = foot[0] * (0.65 + 0.35 * fnz(x, 0.0)) * math.exp(-((y - foot[1]) / foot[2]) ** 2)
        z = smax(z, fh, 6.0)
        # near the front and back edges the ground ramps down at no more than ~45 degrees, so a
        # peak too near an edge flattens into a slope instead of being cut off as a wall
        lim = min((y - y0) * 1.0, (y1 - y) * 2.4) - 0.4
        return smin(z, lim, 10.0)

    xs = columns(W, ncols, [pk.px for pk in peaks[:len(peaks_spec)]])
    base_rows = [y0, y0 + 6, y0 + 14, y0 + 23, y0 + 32, y0 + 41, y0 + 50, y0 + 58, y0 + 66, y0 + 73,
                 y0 + 80, y0 + 87, y0 + 94, y0 + 101, y0 + 108, y0 + 116, y0 + 126, y0 + 137, y1]
    ys = rows_with([y for y in base_rows if y <= y1], [pk.py for pk in peaks[:len(peaks_spec)]], 2.0)
    bm, V = G.grid_surface(xs, ys, h, 'mrock')

    def lap(x, y, d=7.0):
        return (h(x + d, y) + h(x - d, y) + h(x, y + d) + h(x, y - d) - 4 * h(x, y)) / (d * d)

    def slope(x, y, d=3.0):
        return math.hypot(h(x + d, y) - h(x - d, y), h(x, y + d) - h(x, y - d)) / (2 * d)

    def snow(co):
        x, y, z = co
        L = snowline + 4.5 * snz(x, y)
        c = max(-0.05, min(0.05, lap(x, y)))
        s = slope(x, y)
        return (z - L + 120.0 * c - 9.0 * max(0.0, s - 1.3)) / 6.0

    def meadow(co):
        x, y, z = co
        s = slope(x, y)
        return (foot[0] * 0.9 + 4.0 * snz(x * 1.3, y) - z) / 5.0 + (0.6 - s) * 2.0

    fields = vfields(bm, {'snow': snow, 'meadow': meadow})
    G.contour_cut(bm, fields, 'snow', 0.0)
    G.contour_cut(bm, fields, 'meadow', 0.0)
    lk = G.klayer(bm)
    for f in bm.faces:
        if G.face_mean(fields['snow'], f) > 0: f[lk] = G.KID['snow']
        elif G.face_mean(fields['meadow'], f) > 0: f[lk] = G.KID['meadow']
        else: f[lk] = G.KID['mrock']
    G.end_caps(bm, V, 'soil')
    hmax = max(v.co.z for v in bm.verts)
    ctx = Ctx(seed=seed, normals='smooth', ao_radius=38.0, ao_rays=28, period=W, z0=0.0, z1=hmax, noise_scale=60.0,
              category='landscape', budget=6000, depth=(y0, y1), hmax=hmax, tileWidth=W,
              notes='tiles seamlessly along x every %d m' % W)
    return bm, ctx


def mountain_range1():
    """Alpine: a twin-summit massif right of centre (90 m), a sharp secondary peak to the left,
    lower peaks and front spurs, a low saddle at the tiling seam."""
    peaks = [(38, 14, 90, 0.95, 5), (72, 22, 77, 0.95, 5), (-92, 14, 71, 0.95, 5), (-148, 20, 58, 0.85, 4),
             (128, 18, 63, 0.9, 5), (-38, 26, 56, 0.8, 4), (172, 28, 46, 0.8, 4), (-190, 26, 40, 0.75, 4)]
    spurs = [(8, -28, 40, 0.85), (-70, -26, 36, 0.9), (102, -30, 33, 0.85), (-122, -34, 28, 0.9), (150, -22, 30, 0.85),
             (58, -36, 26, 0.9)]
    return mountain_range(4401, 400.0, peaks, spurs, (17.0, -58.0, 14.0), 52.0)


def mountain_range2():
    """Sawtooth: a run of steep, narrow peaks (to 72 m) on the left, a broad snowy massif with a
    long shoulder on the right, a low pass between them."""
    peaks = [(-150, 16, 58, 1.0, 4), (-112, 10, 72, 1.05, 4), (-78, 18, 63, 1.05, 4), (-46, 12, 52, 1.0, 4),
             (48, 18, 68, 0.8, 6), (96, 24, 60, 0.8, 5), (150, 12, 50, 0.9, 4)]
    spurs = [(-128, -26, 32, 0.95), (-60, -28, 28, 0.95), (70, -30, 30, 0.85), (126, -26, 26, 0.9), (2, -18, 24, 0.8)]
    return mountain_range(4402, 400.0, peaks, spurs, (15.0, -60.0, 13.0), 44.0)


# ---------------------------------------------------------------- rolling hills
def hills_rolling():
    W = 300.0
    rng = random.Random(4501)
    bumps = []
    for (y, H, sx, sy, n) in ((18.0, (13, 25), (24, 52), 24.0, 7), (-6.0, (7, 16), (18, 38), 17.0, 8), (-28.0, (3, 8), (14, 28), 12.0, 9)):
        off = rng.uniform(0, W)
        for i in range(n):
            px = -W / 2 + off + W * (i + rng.uniform(-0.32, 0.32)) / n
            bumps.append((px, y + rng.uniform(-6, 6), rng.uniform(*H), rng.uniform(*sx), sy * rng.uniform(0.85, 1.15)))
    nz = Waves(4502, 40.0, 2, W=W, dims=2)
    y0, y1 = -48.0, 48.0

    def h(x, y):
        z = 0.0
        for px, py, H, sx, sy in bumps:
            dx = wrap(x - px, W) / sx; dy = (y - py) / sy
            r2 = dx * dx + dy * dy
            if r2 < 9: z = smax(z, H * math.exp(-r2) * (1 + 0.04 * nz(x, y)), 4.0)
        edge = sstep(y0, y0 + 14, y) * sstep(y1, y1 - 16, y)
        return z * edge - 0.3 * (1 - edge)

    xs = columns(W, 96)
    ys = [y0, -42, -37, -32.5, -28.5, -24.5, -20.5, -16.5, -12.5, -8.5, -4.5, -0.5, 3.5, 7.5, 11.5, 15.5, 19.5, 24, 29, 35, 41, y1]
    bm, V = G.grid_surface(xs, ys, h, 'hill')

    def slope(x, y, d=2.0):
        return math.hypot(h(x + d, y) - h(x - d, y), h(x, y + d) - h(x, y - d)) / (2 * d)

    onz = Waves(4503, 18.0, 2, W=W, dims=2)

    def outcrop(co):
        x, y, z = co
        return (slope(x, y) - 0.66) * 6.0 + onz(x, y) * 1.4 - 0.9

    G.end_caps(bm, V, 'soil')
    hmax = max(v.co.z for v in bm.verts)
    ctx = Ctx(seed=4501, normals='smooth', ao_radius=22.0, ao_rays=28, period=W, z0=0.0, z1=hmax, noise_scale=45.0,
              category='landscape', budget=6000, depth=(y0, y1), hmax=hmax, tileWidth=W,
              notes='tiles seamlessly along x every %d m' % W)
    return bm, ctx


# ---------------------------------------------------------------- forest band
def forest_strip():
    W = 100.0
    rng = random.Random(4601)
    nz = Waves(4602, 22.0, 2, W=W, dims=2)
    y0, y1 = -7.5, 10.0

    def mound(x, y):
        c = 1.8 + 0.55 * nz(x, 0.0)
        return c * math.exp(-((y - 0.6) / 5.5) ** 2) * sstep(y0, y0 + 3.0, y) * sstep(y1, y1 - 3.0, y) - 0.15

    xs = columns(W, 40)
    ys = [y0, -5.6, -3.6, -1.6, 0.4, 2.4, 4.4, 6.4, 8.4, y1]
    bm, V = G.grid_surface(xs, ys, mound, 'meadow')
    G.end_caps(bm, V, 'soil')
    # trees: three loose rows, tall at the back; periodic spacing so the band tiles
    trees = []
    for (yr, hr, rr, gap) in ((4.4, (7.2, 8.6), (2.2, 2.6), (3.1, 4.0)), (1.0, (5.8, 7.4), (1.9, 2.3), (3.3, 4.6)),
                              (-2.6, (4.0, 5.6), (1.5, 1.9), (4.0, 8.5))):
        x = -W / 2 + rng.uniform(0, 2)
        while x < W / 2 - 1.0:
            trees.append((x, yr + rng.uniform(-1.3, 1.3), rng.uniform(*hr), rng.uniform(*rr)))
            x += rng.uniform(*gap)
    out = G.new_bm(); G.merge(out, bm)
    for (x, y, H, R) in trees:
        z = mound(x, y)
        tiers = 3 if H > 6.0 else 2
        t = G.conifer(rng, (x, y, z), H, R, tiers=tiers, points=5, trunk_stub=(y < 0.0),
                      lean=(rng.uniform(-0.03, 0.03), rng.uniform(-0.02, 0.02)))
        G.merge(out, t)
    ctx = Ctx(seed=4601, normals='smooth', ao_radius=5.0, ao_rays=28, period=W, z0=0.0, z1=10.0, noise_scale=14.0,
              category='landscape', budget=6000, depth=(y0, y1), tileWidth=W, trees=len(trees),
              notes='tiles seamlessly along x every %d m' % W)
    return out, ctx


# ---------------------------------------------------------------- dunes
def dune(seed, half_w, H_of_u, crest_of_u, Lw, Ls, windward_front=True, nu=40):
    """A dune on a curvilinear grid: u runs along the crest (x), v across it; the crest row is
    shared by the gentle windward side and the steeper slip face, so the ridge line stays crisp
    but soft. Lw, Ls: lengths of the two sides at full height."""
    vw = [0.0, 0.07, 0.17, 0.3, 0.46, 0.64, 0.82, 1.0]
    vs = [0.06, 0.15, 0.28, 0.45, 0.66, 0.85, 1.0]
    Hmax = max(H_of_u(i / 200 * 2 - 1) for i in range(201))
    sgn = -1 if windward_front else 1      # the windward side lies toward -Y when windward_front

    def herm(v, a):
        return (2 * v ** 3 - 3 * v ** 2 + 1) - a * (v ** 3 - 2 * v ** 2 + v)

    rowsdef = [(-v, 'w') for v in reversed(vw[1:])] + [(0.0, 'c')] + [(v, 's') for v in vs]
    bm = G.new_bm(); lk = G.klayer(bm)
    V = []
    us = [-1 + 2 * (i / nu) for i in range(nu + 1)]
    us = [math.copysign(abs(u) ** 0.85, u) for u in us]
    for vv, side in rowsdef:
        row = []
        for u in us:
            H = H_of_u(u)
            k = (0.42 + 0.58 * math.sqrt(max(H, 0) / Hmax))
            yc = crest_of_u(u)
            av = abs(vv)
            if side == 's':
                y = yc - sgn * Ls * k * av
                z = H * herm(av, 1.6)
            else:
                y = yc + sgn * Lw * k * av
                z = H * herm(av, 0.75)
            x = half_w * u * (1 - 0.1 * av * av)
            row.append(bm.verts.new((x, y, z - 0.04)))
        V.append(row)
    for j in range(len(rowsdef) - 1):
        for i in range(nu):
            a, b, c, d = V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]
            for t in ((a, b, c), (a, c, d)):
                try:
                    f = bm.faces.new(t); f[lk] = G.KID['sand']
                except ValueError:
                    pass
    G.fix_normals(bm)
    if sum(f.normal.z * f.calc_area() for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.normal_update()
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    return bm


def sand_dune1():
    """10 m, 2.1 m: a long ridge with two humps and a gentle S-curved crest; the gentle windward
    side faces the camera, the slip face falls away behind."""
    def H(u):
        e = max(0.0, 1 - u * u) ** 0.9
        return 2.1 * e * (0.62 * math.exp(-((u + 0.38) / 0.32) ** 2) + 1.0 * math.exp(-((u - 0.22) / 0.42) ** 2)) / 1.02
    def crest(u):
        return 0.55 * math.sin(1.7 * u + 0.4) + 0.3
    bm = dune(4701, 5.1, H, crest, 4.6, 2.6, True)
    return bm, Ctx(seed=4701, normals='smooth', ao_radius=2.5, span=11.0, z0=0.0, z1=2.1, noise_scale=6.0,
                   category='dune', budget=1500)


def sand_dune2():
    """12 m, 2.4 m: a crescent dune whose horns curl toward the camera around a concave slip face."""
    def H(u):
        return 2.4 * max(0.0, 1 - abs(u) ** 2.2) ** 1.1 * (1 + 0.08 * math.sin(3 * u))
    def crest(u):
        return 1.6 - 2.4 * u * u
    bm = dune(4702, 6.0, H, crest, 4.8, 2.8, False)
    return bm, Ctx(seed=4702, normals='smooth', ao_radius=2.8, span=13.0, z0=0.0, z1=2.4, noise_scale=7.0,
                   category='dune', budget=1500)


# ---------------------------------------------------------------- piles
def sand_pile():
    """About 2 m across: a builder's sand heap, rounded top, a flared toe and a shovel bite."""
    rng = random.Random(4801)
    R, Hh = 1.0, 0.86
    nz = Waves(4802, 0.6, 2)
    bite_a = math.radians(-58)
    bite = Vector((math.cos(bite_a) * 0.56, math.sin(bite_a) * 0.56))

    def fr(u, a):
        r = R * (1 + 0.07 * math.sin(3 * a + 0.7) + 0.04 * math.sin(5 * a + 2.1))
        x, y = r * u * math.cos(a), r * u * math.sin(a)
        z = Hh * max(0.0, 1 - u ** 1.6) ** 1.25
        z += 0.03 * nz(x, y, 0.0) * (1 - u)
        d2 = ((x - bite.x) ** 2 + (y - bite.y) ** 2) / 0.09
        z -= 0.36 * math.exp(-d2 * 1.6) * (1 - u * 0.45)
        if u >= 1.0: z = -0.03
        return (x, y, z)

    bm = G.heap(10, 28, fr, 'sand')
    return bm, Ctx(seed=4801, normals='smooth', ao_radius=0.9, span=6.0, z0=0.0, z1=Hh, noise_scale=0.8,
                   category='pile', budget=600, sand_region='grain')


def gravel_pile():
    """About 2 m across: a lumpy heap of gravel with a few loose stones at its toe."""
    rng = random.Random(4901)
    R, Hh = 1.0, 0.72
    nz = Waves(4902, 0.45, 3)

    def fr(u, a):
        r = R * (1 + 0.08 * math.sin(2 * a + 0.3) + 0.05 * math.sin(5 * a + 1.3))
        x, y = r * u * math.cos(a), r * u * math.sin(a)
        z = Hh * max(0.0, 1 - u ** 1.35) ** 1.15
        z += 0.05 * nz(x, y, 0.0) * (1 - u * 0.8)
        if u >= 1.0: z = -0.03
        return (x, y, z)

    bm = G.heap(9, 24, fr, 'gravel')
    for i in range(9):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.85, 1.25)
        s = rng.uniform(0.08, 0.16)
        loc = (r * math.cos(a), r * math.sin(a), 0)
        if i < 3:
            u = rng.uniform(0.35, 0.7); x, y, z = fr(u, a)
            loc = (x, y, z - s * 0.25)
        pb, _ = G.chunk(rng, (s, s * 0.8, s * 0.6), bevel=0.0, segments=0, kind='pebble', loc=loc,
                        rot=rng.uniform(0, 360), n=6, majors=2, block=0.2, top_tilt=25)
        G.merge(bm, pb)
    return bm, Ctx(seed=4901, normals='smooth', ao_radius=0.8, span=2.2, z0=0.0, z1=Hh, noise_scale=0.6,
                   category='pile', budget=600)
