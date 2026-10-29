# The teens' hair (outfit part 3, follows the Head bone). Base space: see teen_lib; fitted to
# the built head (whose top and back are teen_head's declared cranium).
#
# Each style is an under-layer shell plus swept locks:
#   shell  a cap that hugs the head down to the nape, built on a polar grid round a pole (her
#          ponytail tie, his crown whorl), so its rows are rings round the pole and its columns
#          run the way the hair is combed. The hairline is a smooth curve; toward it the cap
#          thins to about a millimetre and its edge tucks into the scalp, so it ends as a clean,
#          tapered edge (no rim). The shine is a crescent bounded by two dedicated rows whose
#          places are smooth functions round the pole, narrowing to points at its ends; the clump
#          creases are thin painted lines bounded by dedicated pairs of columns that close to a
#          point at both ends (plus a very shallow dent), so neither depends on the coarse grid.
#   locks  tapered tubes swept along smooth curves, with a lens-shaped section whose edges curl
#          toward the head and a soft or rounded end: fringe, face-framing strands, ponytail, the
#          clumps of his quiff, the cowlick. Their highlights and creases are spans of the section
#          bounded by vertices that move smoothly along the lock (lens shapes with pointed ends).
# Everything sits on the built head when there is one, otherwise on the cranium ellipsoid, so
# the hair never cuts into the face or ears.
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
BASE, SHINE, GROOVE = 0, 1, 2          # face tags


def hair_colors(girl):
    """Base colour and shine colour. The base colour is the game's default hair colour."""
    if girl: return ((0.3, 0.16, 0.09, 1), (0.5, 0.3, 0.18, 1))
    # very dark brown; the shine a warm, low-contrast brown (a grey one reads as plastic)
    return ((0.13, 0.095, 0.068, 1), (0.25, 0.185, 0.145, 1))


def _groove_color(girl):
    """The clump creases: the base colour darkened toward a warm brown (not toward blue)."""
    return (0.205, 0.1, 0.055, 1) if girl else (0.082, 0.056, 0.04, 1)


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


def _bump(x, p=1.0):
    """0 outside 0..1, rising to 1 in the middle: sin(pi x)^p (p >= 1: pointed ends)."""
    x = np.asarray(x, dtype=np.float64)
    return np.where((x > 0) & (x < 1), np.abs(np.sin(np.pi * np.clip(x, 0, 1))) ** p, 0.0)


def _keys(keys, t):
    """Piecewise-smooth interpolation of [(t, value), ...] at t (array)."""
    t = np.asarray(t, dtype=np.float64); out = np.full(t.shape, float(keys[0][1]))
    for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
        out = np.where(t >= t0, v0 + (v1 - v0) * _ss(t0, t1, t), out)
    return out


def _catmull(ctrl, n=300):
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
    grid = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
    v = np.interp(grid, np.concatenate([ak - 2 * np.pi, ak, ak + 2 * np.pi]), np.concatenate([vk, vk, vk]))
    k = np.arange(-360, 361) * (2 * np.pi / 1440); w = np.exp(-0.5 * (k / sigma) ** 2); w /= w.sum()
    vv = np.concatenate([v[-360:], v, v[:360]])
    v = np.convolve(vv, w, mode='same')[360:-360]
    return np.interp(np.mod(a, 2 * np.pi), np.concatenate([grid, [2 * np.pi]]), np.concatenate([v, v[:1]]))


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
            if loc is not None and 0.45 * re[i] < dist < re[i] + 0.03: r[i] = dist
        return r

    def place(self, D, off):
        D = _unit(np.atleast_2d(D))
        return CC + D * (self.radius(D) + off)[:, None]

    def drape(self, P, lift):
        """Points moved along the ray from the cranium centre to `lift` above the head."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64))
        return self.place(P - CC, np.broadcast_to(np.asarray(lift, dtype=np.float64), (len(P),)))

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


def front_pt(x, z, y=None):
    """A point on the front of the cranium at (x, z) (only its direction from the centre is used)."""
    if y is None:
        y = CC[1] - CR[1] * math.sqrt(max(0.05, 1 - (x / CR[0]) ** 2 - ((z - CC[2]) / CR[2]) ** 2))
    return np.array([x, y, z], dtype=np.float64)


# ------------------------------------------------------------------------- mesh accumulator
def _key(p): return (round(p[0] * 2e4), round(p[1] * 2e4), round(p[2] * 2e4))


class Mesh:
    """Vertices and faces of one object, with a tag per face (BASE / SHINE / GROOVE) and a shade
    per vertex."""
    def __init__(self):
        self.V, self.F, self.T, self.S = [], [], [], []

    def add(self, V, F, T, S=None):
        b = len(self.V); self.V += [tuple(map(float, v)) for v in V]
        self.F += [tuple(b + i for i in f) for f in F]; self.T += list(T)
        self.S += list(S) if S is not None else [1.0] * len(V)

    def build(self, name):
        me = bpy.data.meshes.new(name); me.from_pydata(self.V, [], self.F); me.update()
        return finish(new_obj(name, me))


def _orient(V, F, inside):
    """Faces wound so their normals point away from `inside` (a point or fn(face centre))."""
    tot = 0.0; V = np.asarray(V)
    for f in F[:: max(1, len(F) // 60)]:
        p0, p1, p2 = V[f[0]], V[f[1]], V[f[2]]
        c = (p0 + p1 + p2) / 3; ins = inside(c) if callable(inside) else inside
        tot += np.dot(np.cross(p1 - p0, p2 - p0), c - ins)
    return F if tot >= 0 else [tuple(reversed(f)) for f in F]


# ---------------------------------------------------------------------------------- locks
def _alloc(total, sizes):
    """total split into integer parts (each >= 1) proportional to sizes."""
    sizes = np.asarray(sizes, dtype=np.float64); raw = sizes / sizes.sum() * total
    k = np.maximum(1, np.floor(raw).astype(int))
    while k.sum() < total: k[np.argmax(raw - k)] += 1
    while k.sum() > total: k[np.argmax(k - raw)] -= 1
    return k


def sweep(mesh, path, width, thick, n=12, m=18, up=None, side=None, inner=0.4, curl=0.35,
          shine=None, grooves=(), dents=(), tip=(0.6, 1.0), root=None, root_cap=True, tip_rows=1.2, shine_at=np.pi / 2):
    """A tapered lock along a smooth curve through `path`.
    width / thick: [(t, half-width)], [(t, half-thickness)] keys along the lock (t in 0..1).
    up: the lock's outward direction (default: away from the cranium centre); side: a fixed
    sideways axis instead (e.g. +X for the ponytail). inner: the thickness under the centre line
    as a fraction of the outer thickness; curl: how far the section's edges bend toward the head.
    tip = (t0, p): the end tapers from t0 as (1 - v^2)^p (p 0.5 round, 1 a soft point).
    root = (t1, p): the same taper at the root, up to t1.
    shine = (t0, t1, phi) or (fn(points) -> bools, phi): a lens-shaped highlight on the outer
    side, at most phi radians either side of shine_at (pi/2 = the top of the section), closing to
    points at t0, t1.
    grooves: [(theta, t0, t1, psi)] thin painted creases along the lock (theta: place round the
    section, pi/2 = the top), closing to points at both ends.
    dents: [(theta, depth, sigma)] shallow dents of the section along the lock."""
    D = _catmull(path)
    if shine is not None and callable(shine[0]):
        tf = np.linspace(0, 1, 401); Pf, _ = _resample(D, tf); on = np.nonzero(np.asarray(shine[0](Pf), dtype=bool))[0]
        shine = (tf[on[0]], tf[on[-1]], shine[1]) if len(on) > 2 else None
    # rows: evenly spread, with extra ones in the highlight and toward the tip
    tt = np.linspace(0, 1, 2001); dens = np.ones_like(tt)
    if shine is not None: dens += 1.4 * _ss(shine[0] - 0.04, shine[0], tt) * _ss(shine[1] + 0.04, shine[1], tt)
    dens += tip_rows * _ss(tip[0], 1.0, tt)
    if root is not None: dens += 0.6 * _ss(root[0], 0.0, tt)
    cdf = np.concatenate([[0], np.cumsum(0.5 * (dens[1:] + dens[:-1]))])
    ts = np.interp(np.linspace(0, cdf[-1], m), cdf, tt)
    P, T = _resample(D, ts)
    if side is not None:
        Bv = np.broadcast_to(np.asarray(side, dtype=np.float64), P.shape).copy()
        Bv = _unit(Bv - (Bv * T).sum(1)[:, None] * T); U = np.cross(Bv, T)
    else:
        if up is None: U = _unit(P - CC)
        elif callable(up): U = _unit(up(P))
        else: U = _unit(np.broadcast_to(np.asarray(up, dtype=np.float64), P.shape).copy())
        U = _unit(U - (U * T).sum(1)[:, None] * T); Bv = np.cross(T, U)
    W = _keys(width, ts); H = _keys(thick, ts)
    v = np.clip((ts - tip[0]) / (1 - tip[0]), 0, 1); end = (1 - v * v) ** tip[1]
    if root is not None:
        v = np.clip((root[0] - ts) / root[0], 0, 1); end = end * (0.25 + 0.75 * (1 - v * v) ** root[1])
    W = W * end; H = H * end
    # features round the section: [centre, max half-angle, faces, tag, t0, t1]
    feats = []
    if shine is not None: feats.append([np.mod(shine_at, 2 * np.pi), shine[2], 4, SHINE, shine[0], shine[1]])
    for th, g0, g1, psi in grooves: feats.append([np.mod(th, 2 * np.pi), psi, 1, GROOVE, g0, g1])
    feats.sort(key=lambda f: f[0])
    nf = sum(f[2] for f in feats)
    if feats:
        cs = [f[0] for f in feats]
        gaps = [np.mod(cs[(i + 1) % len(cs)] - cs[i], 2 * np.pi) or 2 * np.pi for i in range(len(cs))]
        galloc = _alloc(n - nf, gaps)
    rows = m - 1                      # the last row is the tip point
    V, F, TG = [], [], []
    act = np.zeros((len(feats), rows))
    for i in range(rows):
        t = ts[i]
        if feats:
            th, tg = [], []
            hws = []
            for fi, f in enumerate(feats):
                b = _bump((t - f[4]) / (f[5] - f[4]), 1.0 if f[3] == SHINE else 0.8)
                act[fi, i] = b; hws.append(f[1] * b + 0.012)
            for fi, f in enumerate(feats):
                a0, a1 = f[0] - hws[fi], f[0] + hws[fi]
                th += list(np.linspace(a0, a1, f[2] + 1)[:-1]); tg += [fi] * f[2]
                nx = feats[(fi + 1) % len(feats)]; b0 = nx[0] - hws[(fi + 1) % len(feats)]
                if b0 <= a1: b0 += 2 * np.pi
                th += list(np.linspace(a1, b0, galloc[fi] + 1)[:-1]); tg += [-1] * galloc[fi]
            th = np.array(th); ftag = tg
        else:
            th = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 2; ftag = [-1] * n
        ca, sa = np.cos(th), np.sin(th)
        prof = 0.5 * (1 + inner) * sa + 0.5 * (1 - inner) * sa * np.tanh(sa / 0.2)
        y = prof * H[i] - curl * H[i] * ca * ca
        x = ca * W[i]
        k = np.ones_like(th)
        for dth, depth, sig in dents: k = k - depth * np.exp(-(_wrap(th - dth) / sig) ** 2)
        V += list(P[i] + np.outer(x * k, Bv[i]) + np.outer(y * k, U[i]))
        if i == 0: ftag0 = ftag
    tip_v = len(V); V.append(P[-1])
    for i in range(rows - 1):
        for kk in range(n):
            a, b = i * n + kk, i * n + (kk + 1) % n
            F.append((a, b, b + n, a + n))
            fi = ftag0[kk]
            if fi >= 0 and (act[fi, i] > 0 or act[fi, i + 1] > 0): TG.append(feats[fi][3])
            else: TG.append(BASE)
    for kk in range(n):
        a, b = (rows - 1) * n + kk, (rows - 1) * n + (kk + 1) % n
        F.append((a, b, tip_v)); TG.append(BASE)
    if root_cap:
        c = len(V); V.append(P[0] - T[0] * 0.3 * min(W[0], H[0] + 1e-4))
        for kk in range(n): F.append((c, (kk + 1) % n, kk)); TG.append(BASE)
    p0, p1, p2 = (np.array(V[j]) for j in F[0][:3])         # outward winding
    if np.dot(np.cross(p1 - p0, p2 - p0), 0.5 * (p0 + p2) - P[0]) < 0: F = [tuple(reversed(f)) for f in F]
    mesh.add(V, F, TG)
    return P


# ---------------------------------------------------------------------------------- shell
def _frame(pole, e1):
    n = _unit(pole); e1 = _unit(np.asarray(e1, dtype=np.float64) - np.dot(e1, n) * n)
    return n, e1, np.cross(n, e1)


def _azimuth_fn(pole, e1=(1, 0, 0)):
    """The azimuth round `pole` of a point (as the Shell built on that pole measures it)."""
    n, e1, e2 = _frame(pole, e1)
    def az(p):
        d = _unit(np.asarray(p, dtype=np.float64) - CC)
        return float(math.atan2(d @ e2, d @ e1))
    return az


class Shell:
    """The under-layer: a cap on a polar grid round `pole` (see the file's header).
    edge_pts: points on the hairline (only their directions from the cranium centre matter).
    off_fn(D, s, se, a) -> height above the head (D unit directions, s the angle from the pole,
    se the hairline's s at azimuth a); it should thin to about a millimetre at the hairline.
    band(a) -> (centre, half-width) in s of the shine crescent per azimuth (half-width 0 where
    there is none). grooves: [(azimuth, u0, u1, half-width m, depth m)] creases along the
    columns from u0 to u1 (fractions of the way from the pole to the hairline).
    twist(u) -> radians added to every column's azimuth at u (a spiral from the pole)."""
    R = 0.155

    def __init__(self, mesh, fit, pole, e1, edge_pts, off_fn, band=None, grooves=(), na=96, dens=None,
                 rows=(7, 1, 12), s0=0.06, sigma=0.05, twist=None, ease=1.35):
        self.fit = fit; self.off_fn = off_fn; self.grooves = list(grooves)
        n, e1, e2 = self.n, self.e1, self.e2 = _frame(pole, e1)
        E = _unit(np.asarray(edge_pts, dtype=np.float64) - CC)
        ak = np.arctan2(E @ e2, E @ e1); sk = np.arccos(np.clip(E @ n, -1, 1))
        self.ag = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
        self.seg = _smooth_periodic(ak, sk, self.ag, sigma)
        self.tw = twist if twist is not None else (lambda u: 0.0 * np.asarray(u, dtype=np.float64))
        # columns: spread by dens(a) (finer where the detail is), with a pair for each crease
        if dens is None: ac = np.arange(na) * 2 * np.pi / na
        else:
            d = dens(self.ag); c = np.concatenate([[0], np.cumsum(d)])
            ac = np.interp(np.arange(na) / na * c[-1], c, np.append(self.ag, 2 * np.pi))
        cols = [(a, -1, 0) for a in ac]
        for gi, g in enumerate(self.grooves):
            if g[3] <= 0: continue
            a0 = np.mod(g[0], 2 * np.pi)
            reg = np.array([c[0] for c in cols if c[1] < 0])
            j = np.argmin(np.abs(_wrap(reg - a0)))
            sp = np.sort(np.abs(_wrap(reg - reg[j])))[1]
            if abs(_wrap(reg[j] - a0)) < 0.4 * sp: cols = [c for c in cols if not (c[1] < 0 and c[0] == reg[j])]
            cols += [(a0, gi, -1), (a0, gi, 1)]
        cols.sort(key=lambda c: (np.mod(c[0], 2 * np.pi), c[2]))
        self.cols = cols
        n1, nb, n2 = rows; nr = n1 + nb + n2; nc = len(cols)
        jj = np.arange(nr)
        f1 = np.clip((jj + 1) / n1, 0, 1); f2 = np.clip((jj - n1 + 1) / nb, 0, 1); f3 = np.clip((jj - n1 - nb + 1) / n2, 0, 1)

        def srows(a):
            se_ = self.SE(a)
            if band is not None: c, hw = band(a)
            else: c, hw = 0.5 * se_, np.zeros_like(se_)
            c = np.clip(c, 0.35 * se_, se_ - 0.2); hw = np.maximum(hw, 0.0012)
            lo = np.minimum(c - hw, se_ - 0.16); hi = np.maximum(np.minimum(c + hw, se_ - 0.11), lo + 0.0024)
            s = np.where(jj < n1, s0 + (lo - s0) * (1 - (1 - f1) ** 1.15),
                np.where(jj < n1 + nb, lo + (hi - lo) * f2, hi + (se_ - hi) * (1 - (1 - f3) ** ease)))
            return s, se_, hw

        A = np.zeros((nr, nc)); S = np.zeros((nr, nc)); HW = np.zeros(nc); WG = np.zeros((nr, nc))
        for ci, (a_c, gi, sg) in enumerate(cols):
            s1, se1, _ = srows(np.full(nr, a_c))
            ab = a_c + self.tw(s1 / se1)
            s2, se2, hw = srows(ab)
            HW[ci] = hw[n1]
            A[:, ci] = ab; S[:, ci] = s2
            if gi >= 0:
                g = self.grooves[gi]
                w = g[3] * _bump((s2 / se2 - g[1]) / (g[2] - g[1]), 0.8)
                WG[:, ci] = w
                A[:, ci] = ab + sg * (w + 0.00006) / (self.R * np.sin(np.maximum(s2, 0.05)))
        Dm = self.dirs(S, A)
        G = np.zeros((nr + 1, nc, 3)); Hm = np.zeros((nr, nc))
        for j in range(nr):
            Hm[j] = self.height(Dm[j], S[j], A[j])
            G[j] = fit.place(Dm[j], Hm[j])
        # the edge tucks into the scalp just past the hairline
        st = S[-1] + (np.maximum(Hm[-1], 0) + 0.0022) * 0.6 / self.R
        G[nr] = fit.place(self.dirs(st, A[-1]), np.full(nc, -0.0025))
        Vt = [fit.place(n[None, :], self.height(n[None, :], np.zeros(1), np.zeros(1)))[0]] + [tuple(p) for row in G for p in row]
        SH = [1.0] * (1 + nr * nc) + [0.85] * nc
        F, TG = [], []
        def vid(j, i): return 1 + j * nc + (i % nc)
        for i in range(nc): F.append((0, vid(0, i + 1), vid(0, i))); TG.append(BASE)
        for j in range(nr):
            for i in range(nc):
                F.append((vid(j, i), vid(j, i + 1), vid(j + 1, i + 1), vid(j + 1, i)))
                i2 = (i + 1) % nc; tag = BASE
                if n1 - 1 <= j < n1 - 1 + nb and (HW[i] > 0.0025 or HW[i2] > 0.0025): tag = SHINE
                c1, c2 = cols[i], cols[i2]
                if c1[1] >= 0 and c1[1] == c2[1] and c1[2] < 0 < c2[2] and j < nr - 1 and \
                        (WG[j, i] > 1.5e-4 or WG[j + 1, i] > 1.5e-4):
                    tag = GROOVE
                TG.append(tag)
        F = _orient(Vt, F, CC)
        mesh.add(Vt, F, TG, SH)

    def SE(self, a):
        return np.interp(np.mod(a, 2 * np.pi), np.append(self.ag, 2 * np.pi), np.append(self.seg, self.seg[0]))

    def dirs(self, s, a):
        s = np.asarray(s, dtype=np.float64); a = np.asarray(a, dtype=np.float64)
        return _unit(np.cos(s)[..., None] * self.n + np.sin(s)[..., None] * (np.cos(a)[..., None] * self.e1 + np.sin(a)[..., None] * self.e2))

    def polar(self, D):
        D = _unit(np.atleast_2d(D))
        return np.arctan2(D @ self.e2, D @ self.e1), np.arccos(np.clip(D @ self.n, -1, 1))

    def height(self, D, s, a):
        se_ = self.SE(a); u = s / se_
        h = self.off_fn(D, s, se_, a)
        for (a0, u0, u1, w, depth) in self.grooves:
            if depth <= 0: continue
            d = _wrap(a - (a0 + self.tw(u))) * self.R * np.sin(s)
            h = h - depth * _bump((u - u0) / (u1 - u0), 0.8) * np.exp(-(d / 0.0045) ** 2)
        return h

    def on(self, P, extra):
        """Points (directions from the cranium centre) placed `extra` above the cap's surface (past
        the hairline: above its edge)."""
        D = _unit(np.atleast_2d(np.asarray(P, dtype=np.float64)) - CC); a, s = self.polar(D)
        s = np.minimum(s, self.SE(a))
        return self.fit.place(D, self.height(D, s, a) + np.broadcast_to(np.asarray(extra, dtype=np.float64), (len(D),)))


def _ring(scr, centre, ax, Rm, rm, lobes_n=11, nt=64, nr=11):
    """A soft gathered ring (the scrunchie) round axis ax: low, smooth ruffles."""
    ax = _unit(ax); b1 = _unit(np.cross(ax, [1, 0, 0])); b2 = np.cross(ax, b1)
    V, S = [], []
    for i in range(nt):
        th = 2 * np.pi * i / nt; ruf = math.cos(lobes_n * th)
        R_ = Rm + 0.0011 * ruf; r_ = rm * (1 + 0.075 * ruf)
        rad = math.cos(th) * b1 + math.sin(th) * b2
        for k in range(nr):
            ph = 2 * np.pi * k / nr
            V.append(centre + rad * (R_ + r_ * math.cos(ph)) + ax * (r_ * 0.86 * math.sin(ph) + 0.0009 * math.sin(lobes_n * th + 1.0)))
            S.append(0.94 + 0.06 * (0.5 + 0.5 * ruf))
    F = []
    for i in range(nt):
        for k in range(nr):
            i1 = (i + 1) % nt; k1 = (k + 1) % nr
            F.append((i * nr + k, i1 * nr + k, i1 * nr + k1, i * nr + k1))
    p0, p1, p2 = (np.array(V[j]) for j in F[0][:3])
    if np.dot(np.cross(p1 - p0, p2 - p0), p0 - (centre + b1 * Rm)) < 0: F = [tuple(reversed(f)) for f in F]
    scr.add(V, F, [BASE] * len(F), S)


# ---------------------------------------------------------------------------------- girl
def _girl(fit, mesh, scr):
    el = math.radians(35)
    pole = _unit([0, math.cos(el), math.sin(el)])          # the ponytail tie, at the back of the crown
    hl = [(0, -0.153, 1.548), (0, 0.072, 1.314)]
    for sx in (1, -1):
        hl += [(sx * 0.055, -0.143, 1.546), (sx * 0.1, -0.112, 1.526), (sx * 0.125, -0.08, 1.5),
               (sx * 0.14, -0.045, 1.478), (sx * 0.147, -0.012, 1.466), (sx * 0.15, 0.015, 1.47),
               (sx * 0.143, 0.042, 1.452), (sx * 0.13, 0.052, 1.41), (sx * 0.117, 0.058, 1.378),
               (sx * 0.085, 0.064, 1.35), (sx * 0.05, 0.068, 1.335), (sx * 0.024, 0.071, 1.309),
               (sx * 0.012, 0.072, 1.318)]

    def off_fn(D, s, se, a):
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        o = 0.0052 + 0.0036 * _ss(0.1, 0.85, z) + 0.0075 * np.exp(-(s / 0.24) ** 2)   # fuller on top, gathered at the tie
        o = o + 0.0012 * _ss(0.3, -0.3, y) * _ss(0.6, 0.9, z)
        o = o - 0.0018 * _ss(0.55, 0.9, np.abs(x)) * _ss(0.25, -0.25, z)          # pulled tight at the sides
        o = o - 0.002 * _ss(0.0, -0.5, z) * _ss(0.1, 0.5, y)                       # and at the nape
        dist = (se - s) * Shell.R
        e = 0.0009
        return e + (o - e) * _ss(0.0, 0.022, dist)

    az = _azimuth_fn(pole)
    a_front = 1.5 * np.pi                     # azimuth toward the forehead (a = pi/2 runs to the nape)

    def band(a):
        al = _wrap(a - a_front)                # 0 at the front, +-pi/2 at the sides
        w = _bump((al + 2.3) / 4.6, 1.2)
        c = 1.0 - 0.3 * (al / 2.3) ** 2
        return c, 0.088 * w
    # creases: on each side from the temple and from above the ear toward the tie, two over the
    # back, a short one either side of the crown; and the parting on her right (-X)
    G = []
    for sx in (1, -1):
        G += [(az((sx * 0.125, -0.07, 1.52)), 0.3, 0.86, 0.0012, 0.0012),
              (az((sx * 0.145, 0.0, 1.49)), 0.26, 0.84, 0.0013, 0.0012),
              (az((sx * 0.13, 0.05, 1.45)), 0.32, 0.8, 0.0011, 0.001),
              (az((sx * 0.07, -0.06, 1.58)), 0.34, 0.72, 0.001, 0.0006)]
    G += [(az((0.03, 0.1, 1.37)), 0.3, 0.72, 0.001, 0.0006)]
    a_part = az((-0.05, -0.1, 1.575))
    G += [(a_part, 0.52, 0.97, 0.0016, 0.0025)]

    def dens(a):
        al = _wrap(a - a_front)
        return 1.0 + 0.5 * np.exp(-(al / 1.0) ** 2) + 0.5 * np.exp(-((np.abs(al) - np.pi / 2) / 0.35) ** 2)
    sh = Shell(mesh, fit, pole, [1, 0, 0], hl, off_fn, band, G, na=84, dens=dens, rows=(7, 1, 12), sigma=0.045)
    over = lambda pts, lifts: sh.on(np.array(pts, dtype=np.float64), np.asarray(lifts, dtype=np.float64))

    # --- the fringe: swept across the forehead from the parting on her right (-X), above the brows
    fr_shine = (lambda Pm: (Pm[:, 2] > 1.545) & (Pm[:, 2] < 1.586), 0.32)
    def flock(pts, w, h=0.0062, tipt=0.55):
        P = over([front_pt(x, z, y) for x, y, z, l in pts], [l for x, y, z, l in pts])
        sweep(mesh, P, [(0, w * 0.45), (0.25, w), (0.6, w * 0.92), (1, w * 0.7)],
              [(0, h * 0.35), (0.3, h), (0.8, h * 0.8), (1, h * 0.6)], n=12, m=15, inner=0.35, curl=0.55,
              shine=fr_shine, tip=(tipt, 0.85), root=(0.2, 1.0))
    # (x, y or None for the front surface, z, lift above the cap) from the parting to the tip
    flock([(-0.05, -0.085, 1.592, -0.002), (-0.04, None, 1.572, 0.006), (-0.022, None, 1.545, 0.007), (0.0, None, 1.522, 0.005), (0.022, None, 1.506, 0.003)], 0.024)
    flock([(-0.048, -0.07, 1.6, -0.002), (-0.018, None, 1.578, 0.009), (0.02, None, 1.55, 0.009), (0.056, None, 1.52, 0.006), (0.088, None, 1.502, 0.003)], 0.029)
    flock([(-0.046, -0.055, 1.605, -0.002), (0.01, None, 1.588, 0.011), (0.062, None, 1.556, 0.01), (0.104, None, 1.518, 0.006), (0.13, None, 1.49, 0.003)], 0.029)
    flock([(-0.044, -0.04, 1.608, -0.002), (0.04, -0.075, 1.6, 0.011), (0.1, None, 1.566, 0.009), (0.133, None, 1.52, 0.006), (0.146, None, 1.482, 0.003)], 0.025)
    flock([(-0.054, -0.08, 1.595, -0.002), (-0.072, None, 1.575, 0.007), (-0.095, None, 1.548, 0.007), (-0.115, None, 1.522, 0.005), (-0.13, None, 1.502, 0.003)], 0.025)
    flock([(-0.056, -0.095, 1.585, -0.002), (-0.058, None, 1.566, 0.006), (-0.066, None, 1.542, 0.006), (-0.079, None, 1.522, 0.004), (-0.093, None, 1.51, 0.003)], 0.019)

    # --- face-framing strands in front of the ears, down to the jaw (roots tucked under the fringe)
    for sx in (1, -1):
        pts = [(sx * 0.118, -0.083, 1.512), (sx * 0.131, -0.062, 1.485), (sx * 0.14, -0.048, 1.45),
               (sx * 0.138, -0.046, 1.41), (sx * 0.126, -0.05, 1.372), (sx * 0.108, -0.058, 1.342)]
        P = fit.drape(pts, np.array([0.004, 0.0055, 0.0062, 0.0062, 0.0062, 0.006]))
        P = fit.clear(P, 0.0058)
        fwd_up = lambda Q, sx=sx: _unit(_unit(Q - CC) * np.array([1.0, 0.4, 0.4]) + np.array([0, -0.55, 0]))
        sweep(mesh, P, [(0, 0.0075), (0.3, 0.0098), (0.7, 0.0088), (1, 0.0068)],
              [(0, 0.0032), (0.5, 0.0036), (1, 0.003)], n=10, m=17, up=fwd_up, inner=0.6, curl=0.45,
              tip=(0.6, 0.9), root=(0.15, 1.0))

    # --- the high ponytail: a full lock arcing back and down in a gentle S to a flicked-out tip
    top = sh.on(pole[None] * 0.1 + CC, 0.0)[0]        # the cap's surface at the tie
    path = [top - pole * 0.012, top + pole * 0.01, top + pole * 0.028, (0.0, 0.188, 1.553), (0.0, 0.215, 1.536),
            (0.002, 0.231, 1.502), (0.005, 0.236, 1.45), (0.008, 0.229, 1.4), (0.011, 0.221, 1.36),
            (0.014, 0.224, 1.326), (0.019, 0.239, 1.299), (0.026, 0.26, 1.284)]
    pw = [(0, 0.0145), (0.05, 0.0152), (0.11, 0.025), (0.22, 0.032), (0.45, 0.0355), (0.65, 0.0335), (0.8, 0.0275), (1, 0.019)]
    ph = [(0, 0.0138), (0.05, 0.0145), (0.11, 0.018), (0.22, 0.0198), (0.4, 0.0205), (0.62, 0.0195), (0.78, 0.017), (1, 0.012)]
    sweep(mesh, path, pw, ph, n=20, m=38, side=(1, 0, 0), inner=1.0, curl=0.0,
          shine=(0.1, 0.36, 0.5), tip=(0.74, 0.8), tip_rows=1.8,
          grooves=[(np.pi / 2 + 0.95, 0.16, 0.9, 0.035), (np.pi / 2 - 0.95, 0.18, 0.92, 0.035), (-0.15, 0.2, 0.86, 0.03)],
          dents=[(np.pi / 2 + 0.95, 0.07, 0.25), (np.pi / 2 - 0.95, 0.07, 0.25), (-0.15, 0.05, 0.25)])
    _ring(scr, top + pole * 0.008, pole, 0.0265, 0.0125)


# ----------------------------------------------------------------------------------- boy
def _boy(fit, mesh):
    pole = _unit([0.03, 0.42, 0.9])                 # the crown whorl
    # hairline: a softly squared front with the temple corners set back, short sideburns, the
    # line arcing over the ears, behind them down to the nape, which ends in two soft points
    hl = [(0, -0.135, 1.538), (0, 0.077, 1.33)]
    hl += [(0.03, -0.13, 1.541), (0.056, -0.125, 1.546), (0.08, -0.113, 1.541), (0.1, -0.099, 1.535)]
    hl += [(-0.03, -0.132, 1.538), (-0.065, -0.122, 1.537), (-0.09, -0.107, 1.534), (-0.105, -0.095, 1.527)]
    for sx in (1, -1):
        hl += [(sx * 0.116, -0.083, 1.513), (sx * 0.126, -0.065, 1.488), (sx * 0.133, -0.049, 1.458),
               (sx * 0.138, -0.032, 1.436), (sx * 0.141, -0.019, 1.444), (sx * 0.146, -0.005, 1.466),
               (sx * 0.149, 0.015, 1.474), (sx * 0.143, 0.04, 1.456), (sx * 0.13, 0.05, 1.408),
               (sx * 0.116, 0.058, 1.377), (sx * 0.085, 0.065, 1.35), (sx * 0.055, 0.07, 1.335),
               (sx * 0.026, 0.074, 1.316), (sx * 0.012, 0.076, 1.322)]
    az = _azimuth_fn(pole)
    a_front = az((0, -0.14, 1.53)); a_part = az((0.056, -0.11, 1.55))
    qc = _unit(np.array([-0.03, -0.1, 1.575]) - CC)          # where the quiff sits
    def rel(a): return _wrap(a - a_part)                      # < 0: his right of the parting
    def frontness(a): return _ss(1.45, 0.6, np.abs(_wrap(a - a_front)))

    def off_fn(D, s, se, a):
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        # short and close at the sides and back, fuller over the top
        o = 0.0032 + 0.0072 * _ss(0.35, 0.92, z) + 0.002 * _ss(0.2, -0.4, y) * _ss(0.5, 0.9, z)
        o = o + 0.022 * np.exp(-((1 - D @ qc) / 0.07) ** 2) * _ss(0.03, -0.14, rel(a))   # under the quiff
        o = o - 0.0015 * frontness(a) * _ss(0.03, 0.2, rel(a)) * _ss(0.5, 0.85, s / se)  # combed flat left of it
        o = o - 0.005 * np.exp(-(rel(a) / 0.03) ** 2) * _ss(0.45, 0.75, s / se)          # the parting
        dist = (se - s) * Shell.R
        e = 0.0009
        return e + (o - e) * _ss(0.0, 0.02, dist)
    # a few irregular creases spiralling a little from the whorl, and the parting
    G = []
    for ang, u0, u1, w in [(-0.3, 0.1, 0.6, 0.0009), (0.5, 0.06, 0.48, 0.0008), (1.25, 0.12, 0.66, 0.0009),
                           (2.15, 0.08, 0.52, 0.0008), (2.9, 0.12, 0.62, 0.0009), (-1.1, 0.14, 0.56, 0.0008)]:
        G.append((np.pi / 2 + ang, u0, u1, w, 0.0005))
    G.append((a_part, 0.42, 0.99, 0.0015, 0.0))
    for da, u0, u1 in [(0.2, 0.55, 0.92), (0.42, 0.62, 0.9)]:                         # combed down to his left
        G.append((a_part + da, u0, u1, 0.0009, 0.0005))
    twist = lambda u: 0.32 * _ss(0.0, 0.75, u)

    def dens(a):
        return 1.0 + 0.6 * frontness(a) + 0.45 * np.exp(-((np.abs(_wrap(a - a_front)) - np.pi / 2) / 0.35) ** 2)
    sh = Shell(mesh, fit, pole, [1, 0, 0], hl, off_fn, None, G, na=100, dens=dens, rows=(8, 1, 12), sigma=0.04,
               twist=twist)
    over = lambda pts, lifts: sh.on(np.array(pts, dtype=np.float64), np.asarray(lifts, dtype=np.float64))
    lens = lambda zlo, zhi, phi=0.3: (lambda Pm: (Pm[:, 2] > zlo) & (Pm[:, 2] < zhi), phi)

    # the quiff: one broad rounded roll that rises out of the parting, crests over the front of
    # the top and rolls over to his right (-X), tapering down past the corner of his forehead
    roll = [(0.068, -0.1, 1.56, -0.008), (0.046, -0.114, 1.571, 0.002), (0.014, -0.123, 1.582, 0.012),
            (-0.028, -0.12, 1.583, 0.017), (-0.066, -0.106, 1.574, 0.016), (-0.098, -0.085, 1.553, 0.013),
            (-0.121, -0.063, 1.525, 0.008), (-0.136, -0.041, 1.494, 0.005)]
    P = over([p[:3] for p in roll], [p[3] for p in roll])
    sweep(mesh, P, [(0, 0.01), (0.3, 0.027), (0.46, 0.03), (0.72, 0.025), (1, 0.017)],
          [(0, 0.005), (0.32, 0.018), (0.46, 0.021), (0.72, 0.016), (1, 0.009)], n=22, m=30, inner=0.55, curl=0.32,
          shine=(0.2, 0.62, 0.3), shine_at=np.pi / 2 + 0.75, tip=(0.62, 0.9), root=(0.16, 1.0),
          grooves=[(np.pi / 2 - 1.05, 0.2, 0.86, 0.04), (np.pi / 2 + 1.55, 0.22, 0.82, 0.035)],
          dents=[(np.pi / 2 - 1.05, 0.06, 0.2), (np.pi / 2 + 1.55, 0.05, 0.2)])
    # a flatter clump behind it, combed the same way
    def clump(pts, w, h, m=18, shine=None):
        P = over([p[:3] for p in pts], [p[3] for p in pts])
        sweep(mesh, P, [(0, w * 0.5), (0.25, w), (0.6, w * 0.92), (1, w * 0.65)],
              [(0, h * 0.4), (0.3, h), (0.75, h * 0.85), (1, h * 0.6)], n=12, m=m, inner=0.3, curl=0.5,
              shine=shine, tip=(0.58, 0.85), root=(0.15, 1.0))
    clump([(0.056, -0.06, 1.592, -0.002), (0.024, -0.066, 1.603, 0.0036), (-0.02, -0.06, 1.606, 0.004),
           (-0.065, -0.046, 1.596, 0.0038), (-0.103, -0.026, 1.572, 0.0032), (-0.13, -0.004, 1.537, 0.0026)],
          0.022, 0.0045, shine=lens(1.605, 1.616, 0.26))
    # the other side of the parting: combed flat and down to his left
    clump([(0.06, -0.112, 1.553, -0.002), (0.083, -0.106, 1.545, 0.0026), (0.104, -0.091, 1.53, 0.0026),
           (0.12, -0.071, 1.508, 0.0022)], 0.016, 0.0036, m=14)

    # the cowlick at the crown: a few small rounded points leaning back and to one side
    Wp = sh.on((pole * 0.1 + CC)[None], 0.0)[0]
    fwd = _unit(np.cross(pole, [1, 0, 0])); side = _unit(np.cross(fwd, pole))
    for (dx, dy, ln, lean, w) in [(0.0, 0.0, 0.031, 0.4, 0.0088), (0.01, 0.006, 0.025, 0.85, 0.0074),
                                  (-0.009, 0.007, 0.021, -0.15, 0.0066)]:
        b = Wp + side * dx - fwd * dy - pole * 0.005
        back = _unit(-fwd * math.cos(lean) + side * math.sin(lean))
        pts = [b, b + pole * ln * 0.5 + back * ln * 0.12, b + pole * ln * 0.85 + back * ln * 0.5,
               b + pole * ln * 0.95 + back * ln * 1.0]
        sweep(mesh, pts, [(0, w), (0.45, w * 0.85), (1, w * 0.7)], [(0, w * 0.8), (0.45, w * 0.66), (1, w * 0.5)],
              n=10, m=12, up=back, inner=0.85, curl=0.12, tip=(0.5, 0.6))


# ---------------------------------------------------------------------------------- build
def _colour_fn(o, mesh, base, shine, groove):
    """Per-corner colour: the face's tag picks base, shine or crease colour; the vertex's shade
    darkens it."""
    tags = {_key(p.center): t for p, t in zip(o.data.polygons, mesh.T) if t}
    shades = {_key(v.co): s for v, s in zip(o.data.vertices, mesh.S) if s != 1.0}
    pal = {BASE: base, SHINE: shine, GROOVE: groove}
    def col(co, cen):
        c = pal[tags.get(_key(cen), BASE)]
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
    parts = [Part(hair, _colour_fn(hair, mesh, base, shine, _groove_color(girl)), 3, 'Head')]
    if scr.F:
        so = scr.build('Scrunchie')
        parts.append(Part(so, _colour_fn(so, scr, SCRUNCHIE, SCRUNCHIE, SCRUNCHIE), 0, 'Head'))
    return parts
