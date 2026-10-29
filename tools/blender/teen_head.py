# The teens' heads: the head mesh (its front carries the painted face) and the ears.
# Base space: see teen_lib. The face is painted by face_teen.py into the atlas' upper-left
# quadrant through face_uv(): a straight front projection. The ears sample a small drawing of
# their folds in the upper-right quadrant (ear_uv / face_teen.EAR_UV).
#
# The head is an implicit surface: the cranium ellipsoid, narrowed smoothly toward the jaw
# (and tucked in at the nape), its mouth and chin brought forward, a jaw line cut from the chin
# up toward the ears and the neck, and a soft button nose. It is sampled along rays from the
# cranium centre on a latitude/longitude grid that is finer over the face, then the rings over
# the jaw are evened out along the surface. Above the brows and at the back the surface is the
# cranium the hair is fitted to (never outside it).
#   girl: soft oval, gently rounded chin.   boy: a little longer, a softly defined squarer jaw.
import bpy, math
import numpy as np
from mathutils import Vector, Matrix
from teen_lib import C, Part, new_obj, bake, finish

# The cranium the hair is fitted to (keep the top and back of the head inside this).
CRANIUM_CENTER = (0, -0.005, 1.425)
CRANIUM_RADII = (0.15, 0.153, 0.162)

# Ear centres (base space, +X ear; the other is mirrored) for anyone fitting hair round them.
EAR_CENTER = (0.146, 0.014, 1.418)


def face_uv(co):
    """World (base space) point -> atlas UV: u = x/0.34 + 0.5, v = (z - 1.27)/0.34, upper-left quadrant."""
    u = co.x / 0.34 + 0.5; v = (co.z - 1.27) / 0.34
    return (u * 0.5, 0.5 + v * 0.5)


def head_uv(co):
    """The head's UVs: face_uv() over the front half. Behind the ears the projection is slid
    continuously downward (below the painted chin) so the back of the head and the nape show
    plain skin instead of a mirror image of the face; what cannot be slid off lands under the
    hair at the back of the crown."""
    x, y, z = co
    w = _ss(0.0, 0.07, y)
    if w > 0 and z < 1.47:
        z = max(0.95, z - 2.6 * w * (1.47 - z))
    return face_uv(Vector((x, y, z)))


# ---------------------------------------------------------------- implicit shape helpers
def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _smax(a, b, k):
    return -_smin(-a, -b, k)


def _ell(p, c, r):
    """Approximate signed distance to an ellipsoid (centre c, radii r); p is (N, 3)."""
    q = (p - np.asarray(c)) / np.asarray(r)
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / np.asarray(r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


# The body's neck (centre y, radii x/y, top z): measured from the built body when there is one.
# The head's underside sits at about z = 1.30 over the neck; if the neck stops short of that,
# the underside is let down over it so the two always meet.
NECK = [0.02, 0.043, 0.042, 1.35]


def measure_neck():
    """Read the built body's neck (teen.py builds the body before the head)."""
    o = bpy.data.objects.get('Body')
    if o is None or o.type != 'MESH': return
    mw = o.matrix_world
    ring = []; top = 0.0
    for v in o.data.vertices:
        p = mw @ v.co
        if abs(p.x) < 0.06 and -0.07 < p.y < 0.1 and p.z > 1.2: top = max(top, p.z)
        if abs(p.z - 1.272) < 0.01 and abs(p.x) < 0.075 and -0.06 < p.y < 0.1: ring.append(p)
    if len(ring) < 6 or top == 0: return
    xs = [abs(p.x) for p in ring]; ys = [p.y for p in ring]
    NECK[:] = [0.5 * (max(ys) + min(ys)), max(xs), 0.5 * (max(ys) - min(ys)), top]


def _shape(girl):
    """Per-character shape parameters."""
    if girl:   # soft oval, gently rounded chin
        return dict(taper=(0.31, 1.43, 1.27, 1.6), taper_front=0.055, funnel=0.3,
                    fwd=(0.028, 1.38, 1.27),
                    floor=(1.276, 0.45, 5.0), fk=0.022,
                    nose=((0, -0.153, 1.392), (0.0105, 0.012, 0.015)), nk=0.012)
    # boy: a little longer, a softly defined jaw and chin
    return dict(taper=(0.26, 1.43, 1.26, 1.8), taper_front=0.06, funnel=0.28,
                fwd=(0.031, 1.38, 1.26), down=0.008,
                floor=(1.258, 0.42, 2.6), fk=0.012,
                chin_flat=0.02,
                nose=((0, -0.154, 1.39), (0.011, 0.0125, 0.016)), nk=0.012)


def head_sdf(p, girl):
    """Signed distance (approx.) to the head surface; p is (N, 3) base-space points."""
    s = _shape(girl)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    cc, cr = np.asarray(CRANIUM_CENTER), np.asarray(CRANIUM_RADII)
    # Narrow the lower head toward the jaw: the same at every depth, so the front outline
    # stays one smooth curve; taper_front narrows the chin a little more than the jaw.
    ta, t0, t1, te = s['taper']
    u = np.clip((t0 - z) / (t0 - t1), 0.0, 1.0)
    k = ta * u ** te * (1 + s['taper_front'] * _ss(0.0, -0.1, y) / max(ta, 1e-6))
    k = k + s.get('funnel', 0.0) * _ss(1.40, 1.29, z) * _ss(-0.03, 0.05, y)   # tuck the nape in
    tap = 1.0 - k
    # Bring the mouth and chin forward (and so the chin down).
    fa, f0, f1 = s['fwd']
    yw = y + fa * _ss(f0, f1, z) * _ss(0.02, -0.1, y)
    zw = z + s.get('down', 0.0) * _ss(1.40, 1.26, z) * _ss(0.0, -0.1, y)   # a longer chin
    pw = np.stack([x / tap, yw, zw], axis=1)
    d = _ell(pw, cc, cr) * tap
    # The jaw line: below a surface rising from the chin toward the neck and the ears is cut away.
    z0, slope, curve = s['floor']
    yy = _smin(y, np.full_like(y, -0.01), 0.03)
    cw = s.get('chin_flat', 0.0)     # a flatter, squarer chin for him
    ax = np.abs(x) - cw
    xe = 0.5 * (ax + np.sqrt(ax * ax + 0.012 ** 2)) - 0.5 * (-cw + math.sqrt(cw * cw + 0.012 ** 2))
    floor = z0 + slope * (yy + 0.09) + curve * xe * xe - 0.02 * _ss(0.0, 0.08, y)
    ny, nx, nyr, ntop = NECK
    plug = min(0.035, max(0.0, 1.318 - ntop))     # let the underside down over a short neck
    if plug > 0:
        floor = floor - plug * np.exp(-(x / (nx + 0.004)) ** 4 - ((y - ny) / (nyr + 0.004)) ** 4)
    d = _smax(d, floor - z, s['fk'])
    # Keep the top and back inside the cranium (a no-op where the shape is already inside).
    d = np.where(z > 1.45, np.maximum(d, _ell(p, cc, cr)), d)
    # A small soft button nose.
    nc, nr = s['nose']
    d = _smin(d, _ell(p, nc, nr), s['nk'])
    return d


def _spaced(n, lo, hi, dens):
    """n values strictly between lo and hi, spaced inversely to dens(x)."""
    xs = np.linspace(lo, hi, 2001)
    c = np.concatenate([[0], np.cumsum(0.5 * (dens(xs[1:]) + dens(xs[:-1])) * np.diff(xs))])
    return np.interp((np.arange(1, n + 1) / (n + 1)) * c[-1], c, xs)


def _grid(nseg, nring):
    """Latitude/longitude grid: finer at the front, round the face and over the jaw and neck,
    coarser on the crown (under the hair)."""
    us = np.arange(nseg) / nseg
    th = 2 * np.pi * us - np.pi                    # azimuth, 0 = front (-Y)
    th = th - 0.42 * np.sin(th)                    # finer at the front
    g = lambda x, c, w: np.exp(-((x - c) / w) ** 2)
    dens = lambda d: 1.0 + 0.7 * g(d, -5, 28) + 0.6 * g(d, -62, 16) - 0.45 * _ss(15, 70, d)
    ph = np.radians(_spaced(nring - 1, -90, 90, dens))
    return th, ph


def _project(dirs, girl):
    """Distance from the cranium centre along each unit direction to the head surface."""
    c = np.asarray(CRANIUM_CENTER)
    lo = np.full(len(dirs), 0.03); hi = np.full(len(dirs), 0.32)
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        inside = head_sdf(c + dirs * mid[:, None], girl) < 0
        lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
    return c + dirs * (0.5 * (lo + hi))[:, None]


def _reproject(p, girl, steps=4):
    """Move points onto the surface along the field's gradient."""
    e = 5e-4
    for _ in range(steps):
        d = head_sdf(p, girl)
        g = np.zeros_like(p)
        for i in range(3):
            dp = np.zeros(3); dp[i] = e
            g[:, i] = (head_sdf(p + dp, girl) - head_sdf(p - dp, girl)) / (2 * e)
        p = p - (d / np.maximum((g * g).sum(1), 1e-9))[:, None] * g
    return p


def _head_mesh(girl, nseg=46, nring=37):
    th, ph = _grid(nseg, nring)
    dirs = []
    for p in ph:
        for t in th:
            dirs.append((math.sin(t) * math.cos(p), -math.cos(t) * math.cos(p), math.sin(p)))
    dirs += [(0, 0, -1), (0, 0, 1)]
    pts = _project(np.asarray(dirs), girl)
    nr = len(ph); bot = nr * nseg; top = bot + 1
    # Even out the rings over the jaw and its underside (rays from the centre graze those
    # surfaces), sliding the points along the surface; the face keeps its rays.
    idx = np.arange(nr * nseg).reshape(nr, nseg)
    up = np.vstack([idx[1:], np.full((1, nseg), top)])
    dn = np.vstack([np.full((1, nseg), bot), idx[:-1]])
    lf = np.roll(idx, 1, axis=1); rt = np.roll(idx, -1, axis=1)
    w = (0.5 * _ss(1.37, 1.31, pts[:nr * nseg, 2]))[:, None]
    for _ in range(40):
        avg = (pts[up.ravel()] + pts[dn.ravel()] + pts[lf.ravel()] + pts[rt.ravel()]) * 0.25
        q = pts.copy()
        q[:nr * nseg] += w * (avg - pts[:nr * nseg])
        pts = _reproject(q, girl, 2)
    faces = []
    for i in range(nr - 1):
        for j in range(nseg):
            a = i * nseg + j; b = i * nseg + (j + 1) % nseg
            faces.append((a, b, b + nseg, a + nseg))
    for j in range(nseg):
        faces.append((bot, (j + 1) % nseg, j))
        a = (nr - 1) * nseg
        faces.append((a + j, a + (j + 1) % nseg, top))
    me = bpy.data.meshes.new('Head')
    me.from_pydata([tuple(p) for p in pts], [], faces)
    me.validate(); me.update()
    o = new_obj('Head', me)
    _outward(o)
    return o


def _outward(o):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data); bm.free()


EAR_INV = {}   # side -> world-to-ear-local matrix (for the ear UVs)


def ear_uv(co):
    """Ears: a side projection in the ear's own frame into the atlas' ear drawing (see
    face_teen.EAR_UV); the back of the ear slides outward onto plain skin."""
    from face_teen import EAR_UV
    sx = 1 if co.x > 0 else -1
    lx, ly, lz = EAR_INV[sx] @ co
    k = 1.0 + min(1.0, max(0.0, -lx - 0.0005) / 0.006)
    cu, cv, sc = EAR_UV
    return (cu + ly * k * sc, cv + lz * k * sc)


def _ear(sx):
    """A tidy ear: a flattened egg with a rolled rim and a shallow bowl, tilted back and
    splayed a little from the head. Its fold lines are painted (face_teen)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=22, ring_count=8, radius=1, location=(0, 0, 0))
    e = C.object; e.name = 'Ear'
    # local axes: X out of the head, Y front-back, Z up. Pole axis along X.
    e.rotation_euler = (0, math.radians(90), 0); bake(e)
    for v in e.data.vertices:
        x, y, z = v.co
        r = math.sqrt(y * y + z * z)
        # egg outline: the top is fuller, the lobe narrower
        y *= 1.0 + 0.16 * z
        if x > 0:   # the outer face: a bowl inside a rolled rim
            bowl = max(0.0, 1 - (r / 0.78) ** 2)
            x = x * (1 - 0.9 * bowl) + 0.1 * bowl
        v.co = (x * 0.0075, y * 0.0195, z * 0.033)
    rot = (math.radians(-12), 0, math.radians(sx * -14))
    loc = (sx * EAR_CENTER[0], EAR_CENTER[1], EAR_CENTER[2])
    e.rotation_euler = rot; e.location = loc
    if sx < 0:
        e.scale = (-1, 1, 1)
    from mathutils import Euler
    M = Matrix.Translation(loc) @ Euler(rot, 'XYZ').to_matrix().to_4x4() @ Matrix.Diagonal((1.0 if sx > 0 else -1.0, 1, 1, 1))
    EAR_INV[sx] = M.inverted()
    bake(e); _outward(e)
    return finish(e)


def build_head(girl, skin):
    """The head and both ears, all white vertex colour x the atlas (whose skin is the body's
    skin colour, see face_teen.skin_rgb), bound rigidly to the Head bone."""
    parts = []
    measure_neck()
    head = _head_mesh(girl)
    finish(head)
    parts.append(Part(head, (1, 1, 1, 1), 0, 'Head', uv=head_uv))   # white x the painted atlas
    for s in (1, -1):
        parts.append(Part(_ear(s), (1, 1, 1, 1), 0, 'Head', uv=ear_uv))   # white x the atlas' ear
    return parts
