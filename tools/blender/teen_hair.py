# The teens' hair (outfit part 3, follows the Head bone). Base space: see teen_lib; fitted to
# teen_head's cranium.
#
# Each style is an under-layer shell plus swept locks:
#   shell  a cap that hugs the head, built on a polar grid round a pole (her ponytail tie, his
#          crown whorl), so its rows are rings round the pole and its columns run the way the
#          hair is combed. The hairline is a smooth curve with a rolled, rounded edge that tucks
#          under into the scalp; soft clump grooves run along the columns (shaped and lightly
#          painted into the vertex colours).
#   locks  tapered tubes swept along smooth curves (a lens-shaped section whose edges curl
#          toward the head) ending in a soft point: fringe, face-framing strands, ponytail,
#          the ends of his quiff, cowlick, sideburns.
# The shine is a band of whole faces, so its edges stay crisp in the toon shading: a scalloped
# crescent of shell rows, and a band of rows across each lock.
# Everything sits on the built head when there is one (its top and back are the declared
# cranium), otherwise on the cranium ellipsoid, so the hair never cuts into the face or ears.
import bpy, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from teen_lib import Part, new_obj, finish
import teen_head
from teen_head import CRANIUM_CENTER

CC = np.array(CRANIUM_CENTER, dtype=np.float64)
CR = np.array(getattr(teen_head, 'CRANIUM_RADII', (0.15, 0.153, 0.162)), dtype=np.float64)
SCRUNCHIE = (0.95, 0.75, 0.25, 1)


def hair_colors(girl):
    """Base colour and shine colour. The base colour is the game's default hair colour."""
    if girl: return ((0.3, 0.16, 0.09, 1), (0.5, 0.3, 0.18, 1))
    return ((0.13, 0.1, 0.09, 1), (0.32, 0.28, 0.29, 1))


# ------------------------------------------------------------------------------- small maths
def _ss(a, b, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def _wrap(a):
    """Angle wrapped to (-pi, pi]."""
    return np.angle(np.exp(1j * np.asarray(a, dtype=np.float64)))


def _keys(keys, t):
    """Piecewise-smooth interpolation of [(t, value), ...] at t (array)."""
    t = np.asarray(t, dtype=np.float64); out = np.full(t.shape, float(keys[0][1]))
    for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
        out = np.where(t >= t0, v0 + (v1 - v0) * _ss(t0, t1, t), out)
    return out


def _catmull(ctrl, n=240):
    """A smooth curve through the control points (centripetal Catmull-Rom), densely sampled."""
    P = np.asarray(ctrl, dtype=np.float64)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5 + 1e-9
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5 + 1e-9
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5 + 1e-9
        k = max(4, n // (len(P) - 3))
        for t in np.linspace(t1, t2, k, endpoint=(i == len(P) - 3)):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    return np.array(out)


def _resample(D, ts):
    """Points at arc-length fractions ts along the dense polyline D, and unit tangents."""
    seg = np.linalg.norm(np.diff(D, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
    P = np.stack([np.interp(ts, s, D[:, k]) for k in range(3)], axis=1)
    h = 0.004
    A = np.stack([np.interp(np.clip(ts - h, 0, 1), s, D[:, k]) for k in range(3)], axis=1)
    B = np.stack([np.interp(np.clip(ts + h, 0, 1), s, D[:, k]) for k in range(3)], axis=1)
    return P, _unit(B - A)


def _smooth_periodic(a_keys, v_keys, a, sigma):
    """A smooth periodic function through (angle, value) keys, sampled at angles a."""
    order = np.argsort(np.mod(a_keys, 2 * np.pi))
    ak = np.mod(np.asarray(a_keys)[order], 2 * np.pi); vk = np.asarray(v_keys)[order]
    grid = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    v = np.interp(grid, np.concatenate([ak - 2 * np.pi, ak, ak + 2 * np.pi]), np.concatenate([vk, vk, vk]))
    k = np.arange(-180, 181) * (2 * np.pi / 720); w = np.exp(-0.5 * (k / sigma) ** 2); w /= w.sum()
    vv = np.concatenate([v[-180:], v, v[:180]])
    v = np.convolve(vv, w, mode='same')[180:-180]
    return np.interp(np.mod(a, 2 * np.pi), np.concatenate([grid, [2 * np.pi]]), np.concatenate([v, v[:1]]))


def lobes(a, creases):
    """Clump profile round the pole: 1 on a clump's crest, 0 in the creases (sorted angles)."""
    c = np.sort(np.mod(creases, 2 * np.pi)); c2 = np.concatenate([c, [c[0] + 2 * np.pi]])
    am = np.mod(a, 2 * np.pi); am = np.where(am < c[0], am + 2 * np.pi, am)
    idx = np.clip(np.searchsorted(c2, am, side='right') - 1, 0, len(c) - 1)
    ph = (am - c2[idx]) / (c2[idx + 1] - c2[idx])
    return np.sin(np.pi * np.clip(ph, 0, 1)) ** 0.55


def _runs(idx):
    """Runs of consecutive integers in a sorted index array -> [(first, last), ...]."""
    out = []; start = prev = idx[0]
    for i in idx[1:]:
        if i != prev + 1: out.append((start, prev)); start = i
        prev = i
    out.append((start, prev)); return out


def _creases(count, jitter, seed):
    rng = np.random.RandomState(seed)
    return np.arange(count) * 2 * np.pi / count + rng.uniform(-jitter, jitter, count) * 2 * np.pi / count


# ----------------------------------------------------------------------------- the head fit
class Fit:
    """The surface the hair sits on: the built head (and ears) when there is one, otherwise the
    declared cranium ellipsoid."""
    def __init__(self):
        self.head = self._bvh('Head'); self.ears = self._bvh('Ear')

    @staticmethod
    def _bvh(name):
        vs, fs = [], []
        for o in bpy.data.objects:
            if o.type != 'MESH' or o.name.split('.')[0] != name: continue
            mw = o.matrix_world; base = len(vs)
            vs += [tuple(mw @ v.co) for v in o.data.vertices]
            fs += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
        return BVHTree.FromPolygons(vs, fs) if fs else None

    def radius(self, D):
        """Distance from the cranium centre to the head surface along unit directions D."""
        D = _unit(np.atleast_2d(D))
        re = 1.0 / np.sqrt(((D / CR) ** 2).sum(axis=1))
        if self.head is None: return re
        r = re.copy(); o = Vector(CC)
        for i, d in enumerate(D):
            loc, nrm, idx, dist = self.head.ray_cast(o, Vector(d), 0.4)
            if loc is not None and abs(dist - re[i]) < 0.045: r[i] = dist
        return r

    def place(self, D, off):
        D = _unit(np.atleast_2d(D))
        return CC + D * (self.radius(D) + off)[:, None]

    def drape(self, P, lift):
        """Points moved along the ray from the cranium centre to `lift` above the head."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64))
        return self.place(P - CC, np.broadcast_to(np.asarray(lift, dtype=np.float64), (len(P),)))

    def front(self, x, z, lift):
        """A point on the front of the head at (x, z) (y from the cranium), lifted."""
        y = CC[1] - CR[1] * math.sqrt(max(0.05, 1 - (x / CR[0]) ** 2 - ((z - CC[2]) / CR[2]) ** 2))
        return self.drape([(x, y, z)], lift)[0]

    def clear(self, P, margin):
        """Push points that are closer than margin to the head or ears (or inside) outward."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64)).copy()
        D = _unit(P - CC); r = self.radius(D); d = np.linalg.norm(P - CC, axis=1)
        m = d < r + margin
        P[m] = CC + D[m] * (r[m] + margin)[:, None]
        if self.ears is not None:
            for i, p in enumerate(P):
                loc, nrm, idx, dist = self.ears.find_nearest(Vector(p), 0.03)
                if loc is None: continue
                v = np.array(p) - np.array(loc); s = np.dot(v, np.array(nrm))
                if s < margin: P[i] = np.array(loc) + np.array(nrm) * margin
        return P


# ------------------------------------------------------------------------- mesh accumulator
def _key(p): return (round(p[0] * 2e4), round(p[1] * 2e4), round(p[2] * 2e4))


class Mesh:
    """Vertices and faces of one object, with a tag per face (1 = shine) and a shade per vertex."""
    def __init__(self):
        self.V, self.F, self.T, self.S = [], [], [], []

    def add(self, V, F, T, S=None):
        b = len(self.V); self.V += [tuple(map(float, v)) for v in V]
        self.F += [tuple(b + i for i in f) for f in F]; self.T += list(T)
        self.S += list(S) if S is not None else [1.0] * len(V)

    def build(self, name):
        me = bpy.data.meshes.new(name); me.from_pydata(self.V, [], self.F); me.update()
        return finish(new_obj(name, me))


# ---------------------------------------------------------------------------------- locks
def sweep(mesh, path, width, thick, n=10, m=18, up=None, side=None, inner=0.45, curl=0.35,
          shine=None, root_cap=True, spacing=0.85, dense=None):
    """A tapered lock along a smooth curve through `path`.
    width / thick: [(t, half-width)], [(t, half-thickness)] keys along the lock (t in 0..1).
    up: the lock's outward direction (default: away from the cranium centre); side: a fixed
    sideways axis instead (e.g. +X for the ponytail). inner: the thickness under the centre
    line as a fraction of the outer thickness; curl: how far the section's edges bend toward
    the head. shine: (t0, t1) rows of the shine on the outer side, or fn(row centres) -> bools.
    dense: (t0, t1, k) adds k extra rows between t0 and t1 (a smoother highlight there)."""
    D = _catmull(path)
    if callable(shine):
        # a highlight placed by position (e.g. a height band shared by several locks): find where
        # along this lock it falls, and give it extra rows there so its lens shape stays smooth
        tf = np.linspace(0, 1, 241); Pf, _ = _resample(D, tf); on = np.nonzero(np.asarray(shine(Pf), dtype=bool))[0]
        if len(on):
            i0, i1 = _runs(on)[0]
            shine = (tf[i0], tf[i1])
            if dense is None and i1 > i0: dense = (tf[i0], tf[i1], 5)
        else:
            shine = None
    ts = np.linspace(0, 1, m) ** spacing
    if dense:
        t0, t1, k = dense
        ts = np.concatenate([ts[(ts < t0 - 1e-3) | (ts > t1 + 1e-3)], np.linspace(t0, t1, k)])
        ts.sort(); m = len(ts)
    P, T = _resample(D, ts)
    if side is not None:
        Bv = np.broadcast_to(np.asarray(side, dtype=np.float64), P.shape).copy()
        Bv = _unit(Bv - (Bv * T).sum(1)[:, None] * T); U = np.cross(Bv, T)
    else:
        U = _unit(P - CC) if up is None else _unit(np.broadcast_to(np.asarray(up, dtype=np.float64), P.shape).copy())
        U = _unit(U - (U * T).sum(1)[:, None] * T); Bv = np.cross(T, U)
    W = _keys(width, ts); H = _keys(thick, ts)
    al = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ca, sa = np.cos(al), np.sin(al)
    tm = 0.5 * (ts[:-1] + ts[1:]); Pm = 0.5 * (P[:-1] + P[1:])
    if shine is None: lit = np.zeros(m - 1, dtype=bool)
    elif callable(shine): lit = np.asarray(shine(Pm), dtype=bool)
    else: lit = (shine[0] <= tm) & (tm <= shine[1])
    # the highlight is a lens: widest across the lock in the middle of the band, narrowing at its ends
    lens = np.zeros(m - 1)
    idx = np.nonzero(lit)[0]
    if len(idx):
        for i0, i1 in _runs(idx):
            L = i1 - i0 + 1
            for i in range(i0, i1 + 1):
                u = (i - i0 + 0.5) / L
                lens[i] = 0.95 - 0.75 * math.sin(math.pi * u) ** 0.7
    V, F, TG = [], [], []
    rows = m - 1                      # the last row is the tip point
    for i in range(rows):
        y = np.where(sa > 0, sa, sa * inner) * H[i] - curl * H[i] * ca * ca
        V += list(P[i] + np.outer(ca * W[i], Bv[i]) + np.outer(y, U[i]))
    tip = len(V); V.append(P[-1])
    for i in range(rows - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            F.append((a, b, b + n, a + n))
            TG.append(1 if (lit[i] and 0.5 * (sa[k] + sa[(k + 1) % n]) > lens[i]) else 0)
    for k in range(n):
        a, b = (rows - 1) * n + k, (rows - 1) * n + (k + 1) % n
        F.append((a, b, tip)); TG.append(0)
    if root_cap:
        c = len(V); V.append(P[0] - T[0] * 0.3 * min(W[0], H[0] + 1e-4))
        for k in range(n): F.append((c, (k + 1) % n, k)); TG.append(0)
    p0, p1, p2 = (np.array(V[j]) for j in F[0][:3])         # outward winding
    if np.dot(np.cross(p1 - p0, p2 - p0), 0.5 * (p0 + p2) - P[0]) < 0: F = [tuple(reversed(f)) for f in F]
    mesh.add(V, F, TG)
    return P


# ---------------------------------------------------------------------------------- shell
def shell(mesh, fit, pole, e1, edge_pts, off_fn, groove_fn, band, na=96, rows=(7, 2, 7), s0=0.06,
          edge_sigma=0.09, crease_shade=0.0):
    """The under-layer: a cap on a polar grid round `pole`.
    edge_pts: points on the hairline (only their directions from the cranium centre matter).
    off_fn(D, s, se, a) -> height above the head; groove_fn(a, s, se) -> (added height, clump
    profile 0..1); band(a) -> (s_lo, s_hi, on): the shine rows' place (radians from the pole)
    per column and whether they are shine. rows = (pole..band, in the band, band..hairline).
    crease_shade darkens the vertex colour in the grooves. Returns a helper that places
    points on the outside of the cap."""
    n = _unit(pole); e1 = _unit(np.asarray(e1, dtype=np.float64) - np.dot(e1, n) * n); e2 = np.cross(n, e1)
    E = _unit(np.asarray(edge_pts, dtype=np.float64) - CC)
    ak = np.arctan2(E @ e2, E @ e1); sk = np.arccos(np.clip(E @ n, -1, 1))
    a = np.linspace(0, 2 * np.pi, na, endpoint=False)
    se = _smooth_periodic(ak, sk, a, edge_sigma)
    s_lo, s_hi, on = band(a)
    s_lo = np.minimum(s_lo, se - 0.25); s_hi = np.minimum(np.maximum(s_hi, s_lo + 0.004), se - 0.18)
    n1, nb, n2 = rows
    S = []
    for j in range(n1):
        u = (j + 1) / n1; S.append(s0 + (s_lo - s0) * (1 - (1 - u) ** 1.15))
    for j in range(nb): S.append(s_lo + (s_hi - s_lo) * (j + 1) / nb)
    for j in range(n2):                      # denser toward the hairline
        u = (j + 1) / n2; S.append(s_hi + (se - s_hi) * (1 - (1 - u) ** 1.35))
    S = np.array(S)

    def dirs(s, aa=a):
        return _unit(np.cos(s)[:, None] * n + np.sin(s)[:, None] * (np.cos(aa)[:, None] * e1 + np.sin(aa)[:, None] * e2))

    def height(D, s, se_, aa):
        g, lob = groove_fn(aa, s, se_)
        return off_fn(D, s, se_, aa) + g, lob

    grid, shade = [], []
    for j in range(len(S)):
        Dj = dirs(S[j]); h, lob = height(Dj, S[j], se, a)
        grid.append(fit.place(Dj, h)); shade.append(1 - crease_shade * (1 - lob) ** 2)
    # the rolled edge: rows past the hairline curling down into the scalp
    D_e = dirs(se); off_e, lob_e = height(D_e, se, se, a)
    ext = off_e * 0.9 / fit.radius(D_e)
    for f_ext, f_off in ((0.55, 0.72), (0.9, 0.28)):
        grid.append(fit.place(dirs(se + ext * f_ext), off_e * f_off)); shade.append(np.full(na, 0.92))
    grid.append(fit.place(dirs(se + ext * 1.05), np.full(na, -0.004))); shade.append(np.full(na, 0.9))
    G = np.array(grid)
    pole_h, _ = height(n[None, :], np.zeros(1), se[:1], a[:1])
    V = [fit.place(n[None, :], pole_h)[0]] + [tuple(p) for row in G for p in row]
    SH = [1.0] + [float(v) for row in shade for v in row]
    F, TG = [], []
    def vid(j, i): return 1 + j * na + (i % na)
    for i in range(na): F.append((0, vid(0, i + 1), vid(0, i))); TG.append(0)
    for j in range(len(G) - 1):
        for i in range(na):
            F.append((vid(j, i), vid(j, i + 1), vid(j + 1, i + 1), vid(j + 1, i)))
            TG.append(1 if (n1 - 1 <= j < n1 - 1 + nb and on[i] and on[(i + 1) % na]) else 0)
    tot = 0.0                                # outward winding
    for f in F[na:na * 4]:
        p0, p1, p2 = (np.array(V[k]) for k in f[:3]); tot += np.dot(np.cross(p1 - p0, p2 - p0), p0 - CC)
    if tot < 0: F = [tuple(reversed(f)) for f in F]
    mesh.add(V, F, TG, SH)

    def on_shell(P, extra):
        """Points (directions from the cranium centre) placed `extra` above the cap's surface."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64)); D = _unit(P - CC)
        aa = np.arctan2(D @ e2, D @ e1); ss_ = np.arccos(np.clip(D @ n, -1, 1))
        sei = np.interp(np.mod(aa, 2 * np.pi), np.concatenate([a, [2 * np.pi]]), np.concatenate([se, se[:1]]))
        h, _ = height(D, np.minimum(ss_, sei), sei, aa)
        return fit.place(D, h + np.broadcast_to(np.asarray(extra, dtype=np.float64), (len(P),)))
    return on_shell


def _ring(scr, centre, ax, Rm, rm, lobes_n=9, nt=45, nr=9):
    """A puffy ruffled ring (the scrunchie) round axis ax."""
    ax = _unit(ax); b1 = _unit(np.cross(ax, [1, 0, 0])); b2 = np.cross(ax, b1)
    V = []
    for i in range(nt):
        th = 2 * np.pi * i / nt; ruf = math.cos(lobes_n * th)
        R_ = Rm + 0.0022 * ruf; r_ = rm * (1 + 0.14 * ruf)
        rad = math.cos(th) * b1 + math.sin(th) * b2
        for k in range(nr):
            ph = 2 * np.pi * k / nr
            V.append(centre + rad * (R_ + r_ * math.cos(ph)) + ax * (r_ * 0.8 * math.sin(ph) + 0.0016 * math.sin(lobes_n * th + 1.0)))
    F = []
    for i in range(nt):
        for k in range(nr):
            i1 = (i + 1) % nt; k1 = (k + 1) % nr
            F.append((i * nr + k, i1 * nr + k, i1 * nr + k1, i * nr + k1))
    p0, p1, p2 = (np.array(V[j]) for j in F[0][:3])
    if np.dot(np.cross(p1 - p0, p2 - p0), p0 - (centre + b1 * Rm)) < 0: F = [tuple(reversed(f)) for f in F]
    # the folds of the gathered fabric a little darker
    S = [0.9 + 0.1 * (0.5 + 0.5 * math.cos(lobes_n * 2 * np.pi * (j // nr) / nt)) for j in range(len(V))]
    scr.add(V, F, [0] * len(F), S)


# ---------------------------------------------------------------------------------- girl
def _girl(fit, mesh, scr):
    pole = _unit([0, math.cos(math.radians(44)), math.sin(math.radians(44))])   # the ponytail tie
    tie = fit.place(pole[None], 0.0)[0]
    hl = []
    for sx in (1, -1):
        hl += [(sx * 0.06, -0.14, 1.545), (sx * 0.105, -0.112, 1.512), (sx * 0.13, -0.075, 1.487),
               (sx * 0.148, -0.025, 1.47), (sx * 0.152, 0.015, 1.472), (sx * 0.146, 0.048, 1.458),
               (sx * 0.13, 0.085, 1.405), (sx * 0.09, 0.11, 1.35)]
    hl += [(0, -0.152, 1.548), (0, 0.12, 1.335)]
    cre = _creases(15, 0.18, 3)
    def off_fn(D, s, se, a):
        o = 0.0105 + 0.0075 * _ss(0.2, 0.9, D[:, 2]) + 0.016 * np.exp(-(s / 0.3) ** 2)
        o = o + 0.004 * _ss(0.45, 0.85, np.abs(D[:, 0])) * _ss(-0.15, 0.3, D[:, 2])     # a little fuller at the sides
        e = 0.0062
        return e + (o - e) * _ss(1.0, 0.8, s / se)
    def groove_fn(a, s, se):
        lob = lobes(a, cre); fade = _ss(0.3, 0.7, s) * (1 - 0.6 * _ss(0.9, 1.0, s / se))
        return 0.0034 * fade * (lob - 1), 1 - fade * (1 - lob)
    def band(a):
        # a scalloped crescent over the top and upper sides (a = 3pi/2 runs over the top to the front)
        w = _ss(1.35, 0.85, np.abs(_wrap(a - 1.5 * np.pi)))
        teeth = 0.045 * lobes(a, cre); c = 1.02
        return c - 0.06 * np.maximum(w, 0.04), c + (0.05 + teeth) * np.maximum(w, 0.04), w > 0.3
    shell(mesh, fit, pole, [1, 0, 0], hl, off_fn, groove_fn, band, crease_shade=0.1)

    # --- the fringe: swept across the forehead from a parting on her right (-X), above the brows
    fr_shine = lambda Pm: (Pm[:, 2] > 1.553) & (Pm[:, 2] < 1.571)
    def flock(pts, w, h=0.0072):
        path = [fit.front(x, z, l) for x, z, l in pts]
        sweep(mesh, path, [(0, w * 0.6), (0.22, w), (0.62, w * 0.82), (1, 0.0)],
              [(0, h * 0.7), (0.3, h), (0.8, h * 0.7), (1, 0.0)], n=12, m=15, inner=0.4, curl=0.5, shine=fr_shine)
    # (x, z, lift) from the parting to the tip; the tips turn toward her left (+X)
    flock([(-0.046, 1.603, 0.006), (-0.036, 1.575, 0.017), (-0.022, 1.542, 0.016), (0.0, 1.515, 0.011), (0.026, 1.502, 0.007)], 0.026)
    flock([(-0.042, 1.605, 0.006), (-0.014, 1.582, 0.019), (0.022, 1.548, 0.018), (0.058, 1.515, 0.012), (0.09, 1.497, 0.007)], 0.03)
    flock([(-0.036, 1.607, 0.006), (0.012, 1.59, 0.02), (0.062, 1.555, 0.018), (0.104, 1.516, 0.012), (0.132, 1.487, 0.007)], 0.03)
    flock([(-0.028, 1.609, 0.006), (0.04, 1.598, 0.018), (0.1, 1.567, 0.016), (0.135, 1.522, 0.011), (0.149, 1.484, 0.007)], 0.026)
    flock([(-0.05, 1.602, 0.006), (-0.07, 1.58, 0.016), (-0.094, 1.549, 0.014), (-0.116, 1.522, 0.01), (-0.132, 1.505, 0.007)], 0.026)
    flock([(-0.05, 1.6, 0.006), (-0.054, 1.575, 0.014), (-0.064, 1.545, 0.013), (-0.078, 1.522, 0.009), (-0.094, 1.51, 0.007)], 0.021)

    # --- face-framing strands in front of the ears, down to the jaw
    for sx in (1, -1):
        pts = [fit.front(sx * 0.118, 1.522, 0.008), (sx * 0.134, -0.074, 1.482), (sx * 0.143, -0.061, 1.43),
               (sx * 0.14, -0.056, 1.38), (sx * 0.132, -0.062, 1.343), (sx * 0.122, -0.078, 1.322)]
        sweep(mesh, fit.clear(pts, 0.012), [(0, 0.012), (0.25, 0.0135), (0.7, 0.0105), (1, 0.0)],
              [(0, 0.006), (0.5, 0.0062), (1, 0.0)], n=12, m=20, inner=0.55, curl=0.35, shine=(0.1, 0.2))

    # --- the high ponytail: a full lock arcing back and down in a gentle S to a flicked-out
    #     tip, two side locks splitting off toward the end, and the scrunchie round the tie
    out = tie + pole * 0.06
    path = [tie - pole * 0.012, tie + pole * 0.028, out, (0.0, 0.192, 1.588), (0.0, 0.238, 1.56),
            (0.004, 0.258, 1.5), (0.008, 0.258, 1.43), (0.011, 0.244, 1.37), (0.014, 0.25, 1.32), (0.018, 0.273, 1.284)]
    sweep(mesh, path, [(0, 0.015), (0.06, 0.018), (0.15, 0.038), (0.32, 0.046), (0.55, 0.043), (0.8, 0.027), (1, 0.0)],
          [(0, 0.015), (0.06, 0.018), (0.15, 0.031), (0.32, 0.036), (0.55, 0.033), (0.8, 0.02), (1, 0.0)],
          n=18, m=30, side=(1, 0, 0), inner=1.0, curl=0.0, shine=(0.165, 0.265), spacing=0.92, dense=(0.15, 0.28, 9))
    for sx in (1, -1):
        p = [(sx * 0.012, 0.26, 1.49), (sx * 0.03, 0.262, 1.425), (sx * 0.036, 0.25, 1.368), (sx * 0.05, 0.262, 1.318)]
        sweep(mesh, p, [(0, 0.012), (0.3, 0.02), (0.7, 0.014), (1, 0.0)], [(0, 0.012), (0.3, 0.017), (0.7, 0.011), (1, 0.0)],
              n=12, m=18, side=(1, 0, 0), inner=1.0, curl=0.0)
    _ring(scr, tie + pole * 0.028, pole, 0.03, 0.0155)


# ----------------------------------------------------------------------------------- boy
def _boy(fit, mesh):
    pole = _unit([0.03, 0.42, 0.9])                 # the crown whorl
    hl = []
    for sx in (1, -1):
        hl += [(sx * 0.137, -0.06, 1.482), (sx * 0.148, -0.025, 1.468), (sx * 0.152, 0.012, 1.471),
               (sx * 0.147, 0.045, 1.456), (sx * 0.135, 0.075, 1.405), (sx * 0.105, 0.1, 1.36), (sx * 0.05, 0.115, 1.337)]
    hl += [(0.042, -0.141, 1.553), (0.075, -0.13, 1.542), (0.1, -0.115, 1.53), (0.122, -0.095, 1.508),
           (-0.04, -0.147, 1.55), (-0.085, -0.13, 1.542), (-0.11, -0.108, 1.53), (-0.125, -0.093, 1.514)]
    hl += [(0, -0.15, 1.551), (0, 0.12, 1.332)]
    cre = _creases(17, 0.2, 7)
    a_part = 1.5 * np.pi + 0.27                     # the column of his parting (+X of the front)
    qc = _unit([-0.22, -0.56, 0.8])                 # centre of the quiff's volume
    def rel(a): return _wrap(a - a_part)            # signed angle from the parting
    def frontness(a): return _ss(1.5, 0.7, np.abs(_wrap(a - 1.5 * np.pi)))
    def off_fn(D, s, se, a):
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        o = 0.007 + 0.016 * _ss(0.05, 0.65, z) + 0.004 * _ss(0.2, 0.7, y)
        o = o + 0.005 * _ss(0.45, 0.85, np.abs(x)) * _ss(-0.1, 0.35, z)                 # a little fuller at the sides
        o = o + 0.026 * np.exp(-((1 - D @ qc) / 0.14) ** 2) * _ss(0.0, -0.12, rel(a))
        o = o - 0.007 * frontness(a) * _ss(0.05, 0.3, rel(a)) * _ss(0.4, 0.8, s / se)   # combed flat left of the part
        o = o - 0.01 * np.exp(-(rel(a) / 0.035) ** 2) * _ss(0.55, 0.8, s / se)            # the parting
        e = 0.004
        q = frontness(a) * _ss(0.05, -0.25, rel(a))          # the quiff rises steeply from the hairline
        return e + (o - e) * _ss(1.0, 0.8 + 0.12 * q, s / se)
    def groove_fn(a, s, se):
        # the clumps sweep away from the parting toward the front: to his right on the quiff,
        # to his left on the other side
        tw = 0.75 * frontness(a) * _ss(0.35, 1.0, s / se) * np.where(rel(a) < 0, 1.0, -1.0)
        lob = lobes(a + tw, cre); fade = _ss(0.12, 0.45, s) * (1 - 0.5 * _ss(0.92, 1.0, s / se))
        return 0.0034 * fade * (lob - 1), 1 - fade * (1 - lob)
    def band(a):
        w = _ss(1.9, 1.3, np.abs(_wrap(a - 1.5 * np.pi)))
        teeth = 0.045 * lobes(a, cre); c = 0.76
        return c - 0.05 * np.maximum(w, 0.04), c + (0.045 + teeth) * np.maximum(w, 0.04), w > 0.3
    on_shell = shell(mesh, fit, pole, [1, 0, 0], hl, off_fn, groove_fn, band, na=104, rows=(8, 2, 9), crease_shade=0.12)

    def on(x, y, z, lift): return fit.drape([(x, y, z)], lift)[0]
    W = fit.place(pole[None], 0.0)[0]
    fwd = _unit(np.cross(pole, [1, 0, 0])); side = np.cross(fwd, pole)
    def tuft(pts, lifts, w, h, n=10, m=12, shine=None):
        """A soft clump lying on the cap, its end lifting a little off it."""
        P = np.vstack([on_shell([p], l) for p, l in zip(pts, lifts)])
        sweep(mesh, P, [(0, w * 0.7), (0.35, w), (0.75, w * 0.75), (1, 0.0)], [(0, h * 0.7), (0.4, h), (1, 0.0)],
              n=n, m=m, inner=0.5, curl=0.45, shine=shine)
    # a few tousled-but-tidy clumps radiating from the crown, their ends lifting a little
    for ang, ln, w in [(-0.95, 0.09, 0.024), (-0.1, 0.1, 0.027), (0.8, 0.095, 0.025)]:
        dirv = -fwd * math.cos(ang) + side * math.sin(ang)
        pts = [W + dirv * (ln * t) - pole * (ln * t) ** 2 * 3.0 for t in (0.05, 0.4, 0.75, 1.0)]
        tuft(pts, [-0.002, 0.0015, 0.003, 0.005], w, 0.0045, m=14)
    # the cowlick tuft at the crown: two small curling points
    sweep(mesh, [W - pole * 0.004, W + pole * 0.03 - fwd * 0.004, W + pole * 0.05 + fwd * 0.008, W + pole * 0.056 + fwd * 0.028],
          [(0, 0.012), (0.35, 0.011), (1, 0.0)], [(0, 0.008), (0.4, 0.007), (1, 0.0)], n=10, m=14, up=-fwd, inner=0.8, curl=0.2)
    sweep(mesh, [W - pole * 0.004 + side * 0.006, W + pole * 0.024 + side * 0.014, W + pole * 0.036 + side * 0.03 - fwd * 0.006],
          [(0, 0.009), (0.35, 0.008), (1, 0.0)], [(0, 0.006), (0.4, 0.005), (1, 0.0)], n=10, m=12, up=-side, inner=0.8, curl=0.2)
    # the front of the quiff: a full, rounded swoop rising from the parting and sweeping over
    # to his right, its end coming down past the corner of the forehead to his right temple
    def swoop(xzl, w, h, m=22, shine=None, inner=0.55, curl=0.35):
        P = np.vstack([on_shell([fit.front(x, z, 0.0)], l) for x, z, l in xzl])
        sweep(mesh, P, [(0, w * 0.45), (0.22, w), (0.6, w * 0.9), (0.85, w * 0.55), (1, 0.0)],
              [(0, h * 0.5), (0.3, h), (0.7, h * 0.85), (1, 0.0)], n=12, m=m, inner=inner, curl=curl, shine=shine)
    sw_shine = lambda Pm: (Pm[:, 2] > 1.553) & (Pm[:, 2] < 1.568)
    swoop([(0.052, 1.562, 0.0), (0.022, 1.568, 0.008), (-0.02, 1.562, 0.012), (-0.06, 1.546, 0.012),
           (-0.095, 1.52, 0.009), (-0.12, 1.495, 0.006), (-0.135, 1.473, 0.004)], 0.031, 0.011, m=24, shine=sw_shine)
    swoop([(0.03, 1.588, -0.004), (-0.01, 1.59, 0.0), (-0.06, 1.58, 0.001), (-0.1, 1.558, 0.001),
           (-0.13, 1.528, 0.001), (-0.146, 1.498, 0.0)], 0.028, 0.007, shine=sw_shine)
    # the other side of the parting, combed down to end above his left ear
    swoop([(0.066, 1.558, 0.0), (0.094, 1.545, 0.005), (0.118, 1.524, 0.005), (0.136, 1.5, 0.003)], 0.02, 0.007, m=14)
    # short tapered sideburns in front of the ears
    for sx in (1, -1):
        pts = [on(sx * 0.136, -0.066, 1.492, 0.004), on(sx * 0.141, -0.054, 1.47, 0.0035), on(sx * 0.143, -0.047, 1.452, 0.003)]
        sweep(mesh, pts, [(0, 0.01), (0.4, 0.008), (1, 0.0)], [(0, 0.0035), (1, 0.0)], n=8, m=10, inner=0.4, curl=0.3)


# ---------------------------------------------------------------------------------- build
def _colour_fn(o, mesh, base, shine):
    """Per-corner colour: the face's tag picks base or shine, the vertex's shade darkens it."""
    tags = {_key(p.center): t for p, t in zip(o.data.polygons, mesh.T) if t}
    shades = {_key(v.co): s for v, s in zip(o.data.vertices, mesh.S) if s != 1.0}
    def col(co, cen):
        c = shine if tags.get(_key(cen)) == 1 else base
        k = shades.get(_key(co), 1.0)
        return (c[0] * k, c[1] * k, c[2] * k, 1)
    return col


def build_hair(girl):
    base, shine = hair_colors(girl)
    fit = Fit()
    mesh = Mesh(); scr = Mesh()
    if girl: _girl(fit, mesh, scr)
    else: _boy(fit, mesh)
    hair = mesh.build('Hair')
    parts = [Part(hair, _colour_fn(hair, mesh, base, shine), 3, 'Head')]
    if scr.F:
        so = scr.build('Scrunchie')
        parts.append(Part(so, _colour_fn(so, scr, SCRUNCHIE, SCRUNCHIE), 0, 'Head'))
    return parts
