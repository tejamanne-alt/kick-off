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
EAR_CENTER = (0.1505, 0.014, 1.418)


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
    """Read the built body's neck (teen.py builds the body before the head): the straight part
    of the neck between z 1.245 and 1.325, and its top."""
    o = bpy.data.objects.get('Body')
    if o is None or o.type != 'MESH': return
    mw = o.matrix_world
    ring = []; top = 0.0
    for v in o.data.vertices:
        p = mw @ v.co
        if abs(p.x) < 0.07 and -0.07 < p.y < 0.1 and p.z > 1.2: top = max(top, p.z)
        if 1.245 < p.z < 1.325 and abs(p.x) < 0.07 and -0.06 < p.y < 0.1: ring.append(p)
    if len(ring) < 6 or top == 0: return
    xs = [abs(p.x) for p in ring]; ys = [p.y for p in ring]
    NECK[:] = [0.5 * (max(ys) + min(ys)), max(xs), 0.5 * (max(ys) - min(ys)), top]


def _shape(girl):
    """Per-character shape parameters. Both faces are an oblong-oval: fairly straight, nearly
    parallel sides from the cheekbones down to about the mouth, then a soft round into the chin.
    width: the front outline's half-width by height (base z)."""
    if girl:   # the softer one: gentle cheeks, a rounded chin
        return dict(width=((1.46, 0.1463), (1.44, 0.1475), (1.42, 0.1425), (1.40, 0.1335), (1.38, 0.1285),
                           (1.36, 0.124), (1.34, 0.118), (1.32, 0.108), (1.30, 0.092), (1.28, 0.068), (1.26, 0.036)),
                    taper_front=0.04,
                    nape=(0.40, 1.41, 1.335), funnel=0.5,
                    fwd=(0.012, 1.38, 1.27), down=0.024,
                    floor=(1.265, 0.85, 2.0, -0.05), back=(20.0, 0.07), fk=0.025,
                    nose=((0, -0.160, 1.389), (0.010, 0.013, 0.013)), nk=0.008)
    # boy: a little longer and straighter-sided, a softly squared chin
    return dict(width=((1.46, 0.1463), (1.44, 0.1475), (1.42, 0.1435), (1.40, 0.1355), (1.38, 0.1315),
                       (1.36, 0.1255), (1.34, 0.119), (1.32, 0.1105), (1.30, 0.097), (1.28, 0.0755), (1.26, 0.048), (1.24, 0.02)),
                taper_front=0.03,
                nape=(0.40, 1.41, 1.335), funnel=0.48,
                fwd=(0.014, 1.38, 1.25), down=0.038,
                floor=(1.252, 0.85, 2.4, -0.05), back=(20.0, 0.078), fk=0.022,
                chin_flat=0.017,
                nose=((0, -0.161, 1.386), (0.011, 0.014, 0.015)), nk=0.008)


_WT = {}


def _width_taper(keys, down):
    """z -> x scale that takes the cranium ellipsoid to the half-widths `keys` [(z, w), ...]
    below z = 1.46 (a piecewise-linear outline through the keys, smoothed)."""
    key = (tuple(keys), down)
    if key in _WT: return _WT[key]
    ks = sorted(keys)
    zf = np.linspace(1.18, 1.56, 761)
    wl = np.interp(zf, [k[0] for k in ks], [k[1] for k in ks])
    g = np.exp(-0.5 * (np.arange(-60, 61) * 0.0005 / 0.009) ** 2); g /= g.sum()
    wpad = np.concatenate([np.full(60, wl[0]), wl, np.full(60, wl[-1])])
    ws = np.convolve(wpad, g, mode='valid')
    cz, rz, rx = CRANIUM_CENTER[2], CRANIUM_RADII[2], CRANIUM_RADII[0]
    zc = zf + 0.3 * down * _ss(1.41, 1.25, zf)
    we = rx * np.sqrt(np.clip(1 - ((zc - cz) / rz) ** 2, 0.0, 1.0))
    tap = np.clip(ws / np.maximum(we, 1e-4), 0.25, 1.0)
    tap = np.where(zf >= 1.46, 1.0, tap + (1.0 - tap) * _ss(1.44, 1.47, zf))
    _WT[key] = f = (lambda z: np.interp(z, zf, tap))
    return f


def head_sdf(p, girl):
    """Signed distance (approx.) to the head surface; p is (N, 3) base-space points."""
    s = _shape(girl)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    cc, cr = np.asarray(CRANIUM_CENTER), np.asarray(CRANIUM_RADII)
    # Narrow the lower head toward the jaw from the temples down to the given front outline
    # (half-widths by height, one smooth curve); the same at every depth, so the front outline
    # stays one smooth curve; taper_front narrows the chin a little more.
    tap0 = _width_taper(s['width'], s.get('down', 0.0))(z)
    k = (1.0 - tap0) * (1 + s['taper_front'] * _ss(0.0, -0.1, y))
    # ... except round the ear root, where the side of the skull stays full so the ears sit on it.
    ez, ey = EAR_CENTER[2], EAR_CENTER[1]
    g_ear = 0.9 * np.exp(-((y - ey) / 0.03) ** 2 - ((z - ez - 0.004) / 0.036) ** 4)
    k = k * (1.0 - g_ear)
    # Behind the ears the sides narrow toward the neck (never inside the neck's top) ...
    ny, nx, nyr, ntop = NECK
    cc_, cr_ = CRANIUM_CENTER, CRANIUM_RADII
    zq = np.clip((z - cc_[2]) / cr_[2], -0.999, 0.999)
    kf = s.get('funnel', 0.0) * _ss(1.43, 1.30, z) * _ss(-0.05, 0.03, y) * (1.0 - g_ear)
    we = cr_[0] * np.sqrt(np.maximum(1 - zq ** 2 - ((ny - cc_[1]) / cr_[1]) ** 2, 0.02))
    kmax = 1.0 - (nx + 0.006) / we
    kf = np.maximum(_smin(kf, kmax - k, 0.03), 0.0)
    k = k + kf
    tap = 1.0 - k
    # ... and the back of the skull tucks in toward the nape (the back is scaled toward the
    # centre below the widest point of the occiput), down to just behind the neck.
    na, n0, n1 = s['nape']
    sy = 1.0 - na * _ss(n0, n1, z)
    yb = cc_[1]
    yback = cr_[1] * np.sqrt(np.maximum(1 - zq ** 2, 0.02))
    sy = np.minimum(_smax(sy, (ny + nyr + 0.007 - yb) / yback, 0.05), 1.0)
    yw = y + _ss(-0.03, 0.05, y) * (y - yb) * (1.0 / sy - 1.0)
    # Bring the mouth and chin forward a little (and so the chin down).
    fa, f0, f1 = s['fwd']
    yw = yw + fa * _ss(f0, f1, z) * _ss(0.02, -0.1, y)
    zw = z + s.get('down', 0.0) * _ss(1.41, 1.25, z) * _ss(0.0, -0.1, y)   # a longer lower face
    pw = np.stack([x / tap, yw, zw], axis=1)
    d = _ell(pw, cc, cr) * tap * np.minimum(1.0, sy + 0.25)
    # The jaw line: below a surface rising from the chin toward the neck and the ears is cut away.
    z0, slope, curve, yc = s['floor']
    yy = _smin(y, np.full_like(y, yc), 0.025)    # rises steeply behind the chin, then levels under the neck
    cw = s.get('chin_flat', 0.0)     # a flatter, squarer chin for him
    ax = np.abs(x) - cw
    xe = 0.5 * (ax + np.sqrt(ax * ax + 0.012 ** 2)) - 0.5 * (-cw + math.sqrt(cw * cw + 0.012 ** 2))
    # Behind the jaw angle the cut climbs faster toward the ears (but stays below the ear lobes),
    # so under the ears the head narrows into the neck.
    bw = _ss(-0.035, 0.02, y)
    bc, bcap = s.get('back', (curve, 1.0))
    lift = curve * xe * xe
    xb = np.abs(x) - (nx + 0.002)               # beside the neck, not over it
    xb = 0.5 * (xb + np.sqrt(xb * xb + 0.008 ** 2))
    lift = lift + bw * (_smin(bc * xb * xb, np.full_like(x, bcap), 0.02) - lift)
    floor = z0 + slope * (yy + 0.09) + lift - 0.02 * _ss(0.0, 0.08, y)
    # let the underside down a little over the neck (more over a short neck), so the neck
    # always enters it cleanly
    plug = min(0.035, max(0.007, 1.318 - ntop))
    if plug > 0:
        floor = floor - plug * np.exp(-(x / (nx + 0.004)) ** 4 - ((y - ny) / (nyr + 0.004)) ** 4)
    d = _smax(d, floor - z, s['fk'])
    # Keep the top and back inside the cranium (a no-op where the shape is already inside).
    d = np.where(z > 1.45, np.maximum(d, _ell(p, cc, cr)), d)
    # A small soft button nose: the most forward point of the profile.
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
    w = (0.6 * _ss(1.40, 1.335, pts[:nr * nseg, 2]))[:, None]
    for _ in range(70):
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
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=8, radius=1, location=(0, 0, 0))
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
    rot = (math.radians(-12), math.radians(sx * 9), math.radians(sx * -21))
    loc = (sx * EAR_CENTER[0], EAR_CENTER[1], EAR_CENTER[2])
    e.rotation_euler = rot; e.location = loc
    if sx < 0:
        e.scale = (-1, 1, 1)
    from mathutils import Euler
    M = Matrix.Translation(loc) @ Euler(rot, 'XYZ').to_matrix().to_4x4() @ Matrix.Diagonal((1.0 if sx > 0 else -1.0, 1, 1, 1))
    EAR_INV[sx] = M.inverted()
    bake(e); _outward(e)
    return finish(e)


def flat_face_normals(o):
    """Anime face shading: the head's normals are taken from a smooth egg round the cranium,
    and over the face they lean hard toward one forward (and slightly upward) direction, so the
    cel bands sweep across the face as one clean shape (all lit, or all in shade) instead of
    tracing the nose, cheeks and jaw."""
    me = o.data
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    c = np.array([0.0, 0.0, 1.40]); r = np.array([0.15, 0.17, 0.21])
    Ne = (V - c) / r ** 2
    Ne /= np.linalg.norm(Ne, axis=1)[:, None]
    fwd = np.array([0.0, -0.96, 0.28]); fwd /= np.linalg.norm(fwd)
    # how much of the face: the front, fading out toward the ears and under the chin
    face = _ss(-0.02, -0.11, V[:, 1]) * _ss(1.24, 1.30, V[:, 2])
    N = Ne + (fwd[None] - Ne) * (0.8 * face)[:, None]
    N /= np.linalg.norm(N, axis=1)[:, None]
    me.normals_split_custom_set_from_vertices(N.tolist())
    me.update()


def build_head(girl, skin):
    """The head and both ears, all white vertex colour x the atlas (whose skin is the body's
    skin colour, see face_teen.skin_rgb), bound rigidly to the Head bone."""
    parts = []
    measure_neck()
    head = _head_mesh(girl)
    finish(head)
    flat_face_normals(head)
    parts.append(Part(head, (1, 1, 1, 1), 0, 'Head', uv=head_uv))   # white x the painted atlas
    for s in (1, -1):
        parts.append(Part(_ear(s), (1, 1, 1, 1), 0, 'Head', uv=ear_uv))   # white x the atlas' ear
    return parts
