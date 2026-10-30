# Shared building blocks for the ANIMALS kit modules (kit_animals_beasts / _birds / _small /
# _items): model and part containers, the baked soft shading, eyes, ribbon lofts.
#
# Space (kit_lib): metres, Z up, the model's front (the side the game camera sees) faces -Y.
# Animals are built side-on: the head points +X, so their right flank faces the camera; the crab
# faces the camera and walks sideways. Moving parts are separate meshes whose origin is their
# pivot; their rest rotation is identity, so their local axes are the model's.
import math
import numpy as np
import kit_animals_geo as G
import kit_animals_atlas as A

UP = np.array((0.0, 0.0, 1.0))


class Part:
    """A mesh object of the model. pivot: the object's origin (model space). parent: another part's
    name, or None for the model root. motion: notes for the game (axis, range)."""
    def __init__(self, name, pivot, pieces, parent=None, motion=None):
        self.name = name
        self.pivot = np.asarray(pivot, float)
        self.pieces = [p for p in pieces if p is not None]
        self.parent = parent
        self.motion = motion


class Model:
    """kind: 'rig' (an empty root named after the model holding the parts) or 'static' (one mesh
    named after the model). colors: {part id: scene-linear base colour}."""
    def __init__(self, name, parts, colors, budget, kind='rig', extra=None, attach=None):
        """attach: {name: (model-space location, part name or None for the root)}."""
        self.name = name; self.parts = parts; self.colors = colors; self.budget = budget
        self.kind = kind; self.extra = extra or {}; self.attach = attach or {}


def scaled(model, s):
    """Scale a finished model about its origin (pieces, pivots, attach points)."""
    for part in model.parts:
        part.pivot = part.pivot * s
        for p in part.pieces:
            p.V = p.V * s
    model.attach = {k: (tuple(np.asarray(v[0], float) * s), v[1]) for k, v in model.attach.items()}
    return model


# ---------------------------------------------------------------- baked shading
def soft_shade(V, N, Aocc, z0, z1, dark=0.74, light=1.08, ao_w=0.4, nz_w=0.55):
    """Brightness factor: light backs and tops, darker bellies and undersides, darker in creases.
    z0..z1: the height range of the part's body (belly .. back)."""
    tn = G.smoothstep(-0.8, 0.85, N[:, 2])
    tz = G.smoothstep(z0, z1, V[:, 2])
    k = dark + (light - dark) * (nz_w * tn + (1 - nz_w) * tz)
    return k * ((1 - ao_w) + ao_w * Aocc)


def painter(base_lin, part, z0, z1, uv=None, **kw):
    """A region painter for Surface.pieces: base colour with soft shading."""
    def fn(V, N, Aocc):
        return G.shade_srgb(base_lin, soft_shade(V, N, Aocc, z0, z1, **kw)), part, uv
    return fn


def flat_painter(base_lin, part, k=1.0, uv=None):
    def fn(V, N, Aocc):
        kk = np.full(len(V), k) * (0.75 + 0.25 * Aocc)
        return G.shade_srgb(base_lin, kk), part, uv
    return fn


def shade_piece(p, base_lin, part, z0, z1, aofield=None, ao_scale=0.03, **kw):
    """Colour an explicit piece with the soft shading (AO from aofield when given)."""
    Aocc = G.ao(aofield, p.V, p.N, ao_scale) if aofield is not None else np.ones(len(p.V))
    p.color(G.shade_srgb(base_lin, soft_shade(p.V, p.N, Aocc, z0, z1, **kw)))
    p.part(part)
    return p


# ---------------------------------------------------------------- eyes and beads
def eye(f_head, center, toward, r, kind='eye', depth=0.55, n=10, rings=3, sink=0.2, squash=1.0):
    """A glossy eye bead on the surface of f_head where the ray from `center` toward `toward`
    leaves it; it bulges along the surface normal there."""
    center = np.asarray(center, float); toward = np.asarray(toward, float)
    d = G.unit(toward - center)
    p, nrm = G.surface_point(f_head, center + d * 0.6, -d)
    b = G.bead(p - nrm * r * sink, nrm, r, depth, n=n, rings=rings, uvreg=A.inset(kind), squash=squash)
    b.color(np.ones(3)); b.part(0)
    return b, p, nrm


# ---------------------------------------------------------------- ribbons (ears, flat tails)
def ribbon(points, widths, thick, normal_fn, n=8, sides=8, bulge=0.0):
    """A flat loft along a spline: elliptical sections, semi-axes width (across) x thick (along
    the section normal from normal_fn(t, point, tangent)). Rounded ends shrink to points.
    bulge > 0 cups the section (an ear's hollow) toward -normal."""
    P = G.catmull(points, n)
    W = G.interp(widths, n); Th = G.interp(thick, n)
    Tg = G.unit(np.gradient(P, axis=0))
    rings = []; nrms = []
    for i in range(n):
        t = Tg[i]
        nv = np.asarray(normal_fn(i / (n - 1), P[i], t), float)
        nv = G.unit(nv - t * np.dot(nv, t)); bv = np.cross(t, nv)
        ang = 2 * math.pi * np.arange(sides) / sides
        ca, sa = np.cos(ang), np.sin(ang)
        off = (ca[:, None] * bv * W[i] + sa[:, None] * nv * Th[i]
               - (bulge * W[i] * (1 - ca ** 2))[:, None] * nv)
        rings.append(P[i] + off)
        nrms.append(G.unit(ca[:, None] * bv / max(W[i], 1e-6) + sa[:, None] * nv / max(Th[i], 1e-6)))
    p = G.loft(rings, True, True)
    N = list(np.concatenate(nrms)); N.append(-Tg[0]); N.append(Tg[-1])
    p.N = G.unit(np.array(N))
    fn = np.cross(p.V[p.T[:, 1]] - p.V[p.T[:, 0]], p.V[p.T[:, 2]] - p.V[p.T[:, 0]])
    if np.einsum('ij,ij->i', fn, p.N[p.T].mean(axis=1)).sum() < 0:
        p.T = p.T[:, ::-1]
    # smooth the normals with the true surface (keeps the rim soft)
    p.N = G.unit(0.5 * p.N + 0.5 * G.vnormals(p.V, p.T))
    return p


def polyline_dist(points):
    """Field: distance to a polyline (for painted lines, used with G.band)."""
    P = np.asarray(points, float)

    def f(Q):
        d = np.full(len(Q), 1e9)
        for a, b in zip(P[:-1], P[1:]):
            ab = b - a
            t = np.clip(((Q - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
            d = np.minimum(d, np.linalg.norm(Q - (a + t[:, None] * ab), axis=1))
        return d
    return f


def neg(f):
    return lambda P: -f(P)


def both(*masks):
    """Intersection of masks (positive where all are)."""
    def f(P):
        d = masks[0](P)
        for m in masks[1:]:
            d = np.minimum(d, m(P))
        return d
    return f


def either(*masks):
    def f(P):
        d = masks[0](P)
        for m in masks[1:]:
            d = np.maximum(d, m(P))
        return d
    return f


def above(xs, zs, xmax=None, xmin=None):
    """Mask positive above a curve z(x) in the side view (through the given points), optionally
    limited to xmin < x < xmax. Side-projected masks cross the surface cleanly, so their cut
    lines come out smooth."""
    xs = np.asarray(xs, float); zs = np.asarray(zs, float)

    def f(P):
        d = P[:, 2] - np.interp(P[:, 0], xs, zs)
        if xmax is not None:
            d = np.minimum(d, xmax - P[:, 0])
        if xmin is not None:
            d = np.minimum(d, P[:, 0] - xmin)
        return d
    return f


def side_ellipse(cx, cz, rx, rz, ang=0.0, ymin=None):
    """Mask positive inside an ellipse in the side view (x, z), optionally only where |y| > ymin."""
    c, s_ = math.cos(ang), math.sin(ang)

    def f(P):
        x = P[:, 0] - cx; z = P[:, 2] - cz
        u = x * c + z * s_; v = -x * s_ + z * c
        d = (1 - np.sqrt((u / rx) ** 2 + (v / rz) ** 2)) * min(rx, rz)
        if ymin is not None:
            d = np.minimum(d, np.abs(P[:, 1]) - ymin)
        return d
    return f
