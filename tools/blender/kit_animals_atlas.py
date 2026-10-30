# The ANIMALS kit atlas (AnimalsAtlas.png, 1024 x 1024): painted detail that vertex colours can't
# carry, multiplied with them by the kit material. Regions are (u0, v0, u1, v1) in UV space.
#   eye, eye_cat, eye_bird   glossy eyes: dark bead / green-gold slit / orange ring, with highlights
#   nose                     a glossy dog or cat nose with nostrils
#   feather                  value map of a gull's upper wing (coverts, flight feathers), mapped by
#                            (chord, span): u 0 at the leading edge -> 1 at the trailing edge,
#                            v 0 at the shoulder -> 1 at the tip
#   wingB                    value map of the butterfly's wing (veins, border, spots), mapped by the
#                            wing's own planar coordinates (see wing_outline())
#   dog_face, cat_face       painted mouths and face stripes (side / head projections)
#   cat_side, rings          tabby stripes on the flanks, rings along a tail
#   pigeon_side, crab_face   the pigeon's wing bars, the crab's smile
#   white                    the plain corner at UV (0.97, 0.03) for flat-coloured parts
# Value maps are near-white greyscale so a recoloured part keeps its pattern.
import math
import numpy as np

AT = 1024
REG = {
    'eye': (0.0, 0.875, 0.125, 1.0),
    'eye_cat': (0.125, 0.875, 0.25, 1.0),
    'eye_bird': (0.25, 0.875, 0.375, 1.0),
    'nose': (0.375, 0.875, 0.5, 1.0),
    'feather': (0.0, 0.5, 0.5, 0.75),
    'wingB': (0.5, 0.5, 1.0, 1.0),
    'dog_face': (0.5, 0.25, 0.75, 0.5),
    'cat_face': (0.75, 0.25, 1.0, 0.5),
    'cat_side': (0.25, 0.25, 0.5, 0.5),
    'rings': (0.25, 0.0, 0.5, 0.0625),
    'crab_face': (0.5, 0.125, 0.625, 0.25),
    'pigeon_side': (0.625, 0.125, 0.75, 0.25),
    'white': (0.9375, 0.0, 1.0, 0.0625),
}


def inset(name, m=0.004):
    u0, v0, u1, v1 = REG[name]
    return (u0 + m, v0 + m, u1 - m, v1 - m)


def _px(name):
    u0, v0, u1, v1 = REG[name]
    x0, x1 = int(round(u0 * AT)), int(round(u1 * AT)); y0, y1 = int(round((1 - v1) * AT)), int(round((1 - v0) * AT))
    w, h = x1 - x0, y1 - y0
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    return (slice(y0, y1), slice(x0, x1)), U, V


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def put(img, mask, col, a=1.0):
    m = (np.clip(mask, 0, 1) * a)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def hx(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def noise(h, w, cells, rng):
    from PIL import Image
    small = (rng.random((cells[1], cells[0])) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC), np.float32) / 255.0


# ---------------------------------------------------------------- the butterfly wing outline
# Shared with the model: wing coordinates (s, t) with s along the body (forward +), t outward from
# the body (0 at the root). The wing is a forewing and a hindwing lobe, in metres for a 0.12 m
# half-span; wing_outline() returns a signed distance (negative inside).
WB = {'span': 0.125, 'xmin': -0.085, 'xmax': 0.075}


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _ellipse(px, py, cx, cy, rx, ry, ang):
    c, s = math.cos(ang), math.sin(ang)
    x = (px - cx) * c + (py - cy) * s; y = -(px - cx) * s + (py - cy) * c
    k0 = np.hypot(x / rx, y / ry); k1 = np.hypot(x / rx ** 2, y / ry ** 2)
    return k0 * (k0 - 1) / np.maximum(k1, 1e-9)


def _smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)


def wing_outline(s, t):
    """Signed distance (m) to the butterfly wing outline in wing coordinates."""
    fore = _ellipse(s, t, 0.022, 0.066, 0.042, 0.072, math.radians(-28))
    hind = _ellipse(s, t, -0.030, 0.048, 0.050, 0.052, math.radians(32))
    tail = _ellipse(s, t, -0.072, 0.040, 0.020, 0.011, math.radians(-20))
    d = _smin(fore, hind, 0.012)
    d = _smin(d, tail, 0.012)
    root = _ellipse(s, t, -0.004, 0.004, 0.026, 0.012, 0.0)
    return _smin(d, root, 0.01)


def wing_uv(s, t):
    u0, v0, u1, v1 = inset('wingB', 0.006)
    a = (np.asarray(s) - WB['xmin']) / (WB['xmax'] - WB['xmin'])
    b = np.asarray(t) / WB['span']
    return np.stack([u0 + (u1 - u0) * np.clip(a, 0, 1), v0 + (v1 - v0) * np.clip(b, 0, 1)], axis=-1)


def _paint_wing(img):
    sl, U, V = _px('wingB')
    s = WB['xmin'] + U * (WB['xmax'] - WB['xmin']); t = V * WB['span']
    d = wing_outline(s, t)
    fore = _ellipse(s, t, 0.022, 0.066, 0.042, 0.072, math.radians(-28))
    hind = _ellipse(s, t, -0.030, 0.048, 0.050, 0.052, math.radians(32))
    sub = np.ones(U.shape + (3,), np.float32)
    # a soft glow lighter toward the body, darker toward the edge
    sub *= (0.92 + 0.08 * ss(0.02, -0.035, d))[..., None]
    # veins: gently curving lines fanning out from the root, fading in away from it
    ang = np.arctan2(t - 0.004, s + 0.004)
    rad = np.hypot(s + 0.004, t - 0.004)
    bend = ang + 0.22 * np.sin(rad * 28.0) * (ang - math.pi / 2)
    q = (bend / math.pi * 11.0) % 1.0
    vein = ss(0.06, 0.02, np.minimum(q, 1 - q))
    sub = put(sub, vein * ss(0.022, 0.045, rad) * ss(-0.004, -0.016, d), (0.62, 0.6, 0.6), 0.5)
    # the dark border along the outer edge, scalloped on its inner side
    scal = 0.0035 * np.sin(ang * 22.0)
    border = ss(-0.019 + scal, -0.014 + scal, d)
    sub = put(sub, border, (0.16, 0.14, 0.15), 1.0)
    # a dark tip on the forewing
    tip = ss(-0.008, 0.004, -_ellipse(s, t, 0.052, 0.118, 0.034, 0.03, math.radians(-30)))
    sub = put(sub, tip * (fore < 0.002), (0.16, 0.14, 0.15), 1.0)
    # pale spots in the border and the tip
    spots = [(0.050, 0.118, 0.0058), (0.061, 0.103, 0.0052), (0.038, 0.126, 0.0050), (0.067, 0.086, 0.0045),
             (0.024, 0.130, 0.0042), (-0.012, 0.094, 0.0040), (-0.032, 0.093, 0.0040), (-0.052, 0.082, 0.0038),
             (-0.068, 0.066, 0.0036), (-0.078, 0.048, 0.0034)]
    for (cx, cy, r) in spots:
        sp = ss(r, r * 0.6, np.hypot(s - cx, t - cy))
        sub = put(sub, sp, (0.97, 0.95, 0.9), 1.0)
    # an eye spot on the hindwing
    e = np.hypot(s + 0.045, t - 0.050)
    sub = put(sub, ss(0.0105, 0.0085, e), (0.18, 0.15, 0.16), 1.0)
    sub = put(sub, ss(0.0065, 0.005, e), (0.98, 0.93, 0.80), 1.0)
    sub = put(sub, ss(0.0035, 0.0022, e), (0.25, 0.30, 0.42), 1.0)
    # a fine dark edge line
    sub = put(sub, ss(-0.0028, -0.0010, d), (0.10, 0.09, 0.10), 1.0)
    img[sl] = sub


def _paint_eye(img, name, kind):
    sl, U, V = _px(name)
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.hypot(x, y)
    if kind == 'dark':
        sub = np.ones(U.shape + (3,), np.float32) * hx('#1b1414')
        # a warm brown iris glow in the lower half, a dark pupil
        glow = ss(0.95, 0.35, np.hypot(x * 1.0, (y + 0.35) * 1.3)) * ss(-0.1, -0.7, y + 0.2)
        sub = put(sub, glow, hx('#5a3626'), 0.75)
        sub = put(sub, ss(0.42, 0.34, r), hx('#0d0909'), 0.9)
    elif kind == 'cat':
        sub = np.ones(U.shape + (3,), np.float32) * hx('#b8c24a')
        sub = put(sub, ss(0.2, 0.9, r), hx('#7f9a3a'), 0.6)
        sub = put(sub, ss(0.0, 0.8, y + 0.2) * ss(0.95, 0.4, r), hx('#e8d26a'), 0.45)
        pup = np.hypot(x / 0.28, y / 0.78)
        sub = put(sub, ss(1.05, 0.9, pup), hx('#141011'), 1.0)
        sub = put(sub, ss(0.86, 0.98, r), hx('#3b3a26'), 1.0)
    else:   # bird: orange ring, black pupil
        sub = np.ones(U.shape + (3,), np.float32) * hx('#e08a2c')
        sub = put(sub, ss(0.5, 0.95, r), hx('#b35a1c'), 0.6)
        sub = put(sub, ss(0.55, 0.47, r), hx('#141011'), 1.0)
        sub = put(sub, ss(0.86, 0.98, r), hx('#3a2a20'), 1.0)
    # highlights: a big soft one up front, a small one below
    h1 = np.hypot((x - 0.28) / 1.1, (y - 0.36))
    sub = put(sub, ss(0.27, 0.19, h1), (1, 1, 1), 1.0)
    h2 = np.hypot(x + 0.3, y + 0.38)
    sub = put(sub, ss(0.11, 0.07, h2), (1, 1, 1), 0.85)
    img[sl] = sub


def _paint_nose(img):
    sl, U, V = _px('nose')
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    sub = np.ones(U.shape + (3,), np.float32) * hx('#3a2a28')
    sub = put(sub, ss(0.2, -0.8, y), hx('#241918'), 0.6)
    # nostrils: two commas low on the front
    for sx in (-1, 1):
        d = np.hypot((x - sx * 0.33) / 1.25, (y + 0.12) / 0.8)
        sub = put(sub, ss(0.24, 0.15, d), hx('#120c0c'), 1.0)
    # a soft gloss on the top
    g = np.hypot((x + 0.05) / 1.6, (y - 0.5) / 0.7)
    sub = put(sub, ss(0.45, 0.1, g), hx('#8a7470'), 0.8)
    sub = put(sub, ss(0.16, 0.08, np.hypot(x + 0.25, y - 0.55)), (1, 1, 1), 0.7)
    img[sl] = sub


def _paint_feather(img):
    sl, U, V = _px('feather')
    c, s = U, V                 # chord (0 leading edge .. 1 trailing edge), span (0 root .. 1 tip)
    sub = np.ones(U.shape + (3,), np.float32)
    # a slightly darker trailing half, lighter coverts along the leading edge
    sub *= (1.0 - 0.07 * ss(0.35, 1.0, c))[..., None]
    # covert rows: rounded feather tips along two rows near the leading edge
    for k, c0 in enumerate((0.24, 0.40)):
        ph = (s * (22 + 5 * k)) % 1.0
        scal = 0.03 * np.sqrt(np.clip(1 - (2 * ph - 1) ** 2, 0, 1))
        sub = put(sub, ss(0.012, 0.0, np.abs(c - c0 - scal)) * ss(0.95, 0.85, s), (0.82, 0.82, 0.85), 0.4)
    # flight feather edges: lines along the chord, leaning toward the tip outboard
    lean = 0.18 * ss(0.4, 1.0, s)
    q = (s * 15.0 + c * lean * 15.0) % 1.0
    line = ss(0.06, 0.0, np.minimum(q, 1 - q)) * ss(0.48, 0.6, c)
    sub = put(sub, line, (0.74, 0.74, 0.77), 0.7)
    img[sl] = sub


# ---------------------------------------------------------------- face decals (side projections)
# A head's vertices map by their side projection (x, z) into a decal region (both flanks share
# it); the decal is white except for painted lines, so it multiplies over any fur colour.
DOG_FACE = {'x0': 0.02, 'x1': 0.42, 'z0': 0.26, 'z1': 0.66,
            'mouth': [(0.384, 0.469), (0.374, 0.4625), (0.352, 0.4555), (0.327, 0.4565), (0.309, 0.4645), (0.3015, 0.4765)]}


def side_uv(spec, region):
    u0, v0, u1, v1 = inset(region, 0.004)

    def fn(V, N):
        a = (V[:, 0] - spec['x0']) / (spec['x1'] - spec['x0']); b = (V[:, 2] - spec['z0']) / (spec['z1'] - spec['z0'])
        return np.stack([u0 + (u1 - u0) * np.clip(a, 0, 1), v0 + (v1 - v0) * np.clip(b, 0, 1)], axis=1)
    return fn


def _stroke(sub, X, Z, pts, w0, w1, col, soft=0.0012):
    """A painted line along pts (decal metres) whose width tapers from w0 (start) to w1 (end)."""
    P = np.asarray(pts, float)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]); L /= L[-1]
    best = np.full(X.shape, 1e9); wid = np.full(X.shape, w0)
    for i in range(len(P) - 1):
        (ax, az), (bx, bz) = P[i], P[i + 1]
        dx, dz = bx - ax, bz - az
        t = np.clip(((X - ax) * dx + (Z - az) * dz) / (dx * dx + dz * dz), 0, 1)
        d = np.hypot(X - (ax + t * dx), Z - (az + t * dz))
        s = L[i] + t * (L[i + 1] - L[i])
        w = w0 + (w1 - w0) * s
        m = d < best
        best = np.where(m, d, best); wid = np.where(m, w, wid)
    return put(sub, ss(wid * 0.5 + soft, wid * 0.5 - soft * 0.3, best), col, 1.0)


def head_uv(spec, region, center, R):
    """A mirrored cylindrical projection around a head's own vertical axis: u = |angle| from
    the nose (0) to the back of the head (1), v = height. R: the head's rotation (columns are its
    local axes: x toward the nose, z up)."""
    u0, v0, u1, v1 = inset(region, 0.004)
    c = np.asarray(center, float); R = np.asarray(R, float)

    def fn(V, N):
        q = (V - c) @ R
        a = np.abs(np.arctan2(q[:, 1], q[:, 0])) / math.pi
        b = (q[:, 2] - spec['z0']) / (spec['z1'] - spec['z0'])
        return np.stack([u0 + (u1 - u0) * np.clip(a, 0, 1), v0 + (v1 - v0) * np.clip(b, 0, 1)], axis=1)
    return fn


def ring_uv(t_of, region='rings'):
    """Tail rings: u from a parameter along the tail (0 base .. 1 tip), v at mid height."""
    u0, v0, u1, v1 = inset(region, 0.004)

    def fn(V, N):
        t = np.clip(t_of(V), 0, 1)
        return np.stack([u0 + (u1 - u0) * t, np.full(len(t), 0.5 * (v0 + v1))], axis=1)
    return fn


CAT_FACE = {'z0': -0.07, 'z1': 0.11}            # head-local heights covered by the decal
CAT_SIDE = {'x0': -0.17, 'x1': 0.12, 'z0': 0.0, 'z1': 0.3}
PIGEON_SIDE = {'x0': -0.2, 'x1': 0.1, 'z0': 0.05, 'z1': 0.22}
CRAB_FACE = {'x0': -0.08, 'x1': 0.08, 'z0': 0.02, 'z1': 0.12}


def front_uv(spec, region):
    """Projection along Y (the front, for the crab): u = x, v = z."""
    u0, v0, u1, v1 = inset(region, 0.004)

    def fn(V, N):
        a = (V[:, 0] - spec['x0']) / (spec['x1'] - spec['x0']); b = (V[:, 2] - spec['z0']) / (spec['z1'] - spec['z0'])
        return np.stack([u0 + (u1 - u0) * np.clip(a, 0, 1), v0 + (v1 - v0) * np.clip(b, 0, 1)], axis=1)
    return fn


def _paint_cat(img):
    # face: angle a (0 at the nose .. 1 at the back), height z (head-local metres)
    sl, U, V = _px('cat_face')
    a = U; z = CAT_FACE['z0'] + V * (CAT_FACE['z1'] - CAT_FACE['z0'])
    sub = np.ones(U.shape + (3,), np.float32)
    dark = (0.62, 0.56, 0.54)
    # forehead 'M': three short stripes running back over the crown
    for a0, w in ((0.0, 0.016), (0.075, 0.014), (0.15, 0.013)):
        m = ss(w, w * 0.5, np.abs(a - a0 - 0.12 * ss(0.03, 0.09, z))) * ss(0.025, 0.04, z) * ss(0.11, 0.09, z)
        sub = put(sub, m, dark, 1.0)
    # cheek stripes: two strokes back from the eye
    for z0, a0 in ((0.002, 0.33), (-0.018, 0.36)):
        m = ss(0.0055, 0.003, np.abs(z - z0 - 0.06 * (a - a0))) * ss(a0 - 0.01, a0 + 0.02, a) * ss(a0 + 0.17, a0 + 0.12, a)
        sub = put(sub, m, dark, 1.0)
    # the mouth: a soft 'w' under the nose (in angle the curve is mirrored about the midline)
    pts = [(0.0, -0.022), (0.0, -0.03), (0.03, -0.037), (0.065, -0.034), (0.085, -0.027)]
    X = a * 0.12          # angle -> rough arc metres so the stroke keeps its width
    sub = _stroke(sub, X, z, [(x * 0.12, zz) for x, zz in pts], 0.0036, 0.0024, (0.40, 0.26, 0.24), soft=0.0008)
    img[sl] = sub
    # flanks: tabby stripes over the back and haunch (side projection)
    sl, U, V = _px('cat_side')
    x = CAT_SIDE['x0'] + U * (CAT_SIDE['x1'] - CAT_SIDE['x0']); z = CAT_SIDE['z0'] + V * (CAT_SIDE['z1'] - CAT_SIDE['z0'])
    sub = np.ones(U.shape + (3,), np.float32)
    stripes = [(-0.13, 0.03, 0.085), (-0.10, 0.07, 0.08), (-0.065, 0.11, 0.09), (-0.035, 0.16, 0.085),
               (-0.02, 0.2, 0.06), (0.0, 0.235, 0.045)]
    for (x0, z0, L) in stripes:
        # a stroke curving down the flank from the spine, tapering
        t = np.clip((z0 + 0.03 - z) / L, 0, 1)
        cx = x0 + 0.02 * np.sin(t * 2.4)
        w = 0.011 * (1 - 0.7 * t)
        m = ss(w, w * 0.45, np.abs(x - cx)) * ss(z0 + 0.04, z0 + 0.02, z) * ss(z0 - L, z0 - L + 0.02, z)
        sub = put(sub, m, (0.66, 0.6, 0.58), 1.0)
    img[sl] = sub
    # rings: dark bands along a tail (u along the tail)
    sl, U, V = _px('rings')
    sub = np.ones(U.shape + (3,), np.float32)
    for u0 in (0.3, 0.48, 0.64, 0.78, 0.9):
        sub = put(sub, ss(0.035, 0.022, np.abs(U - u0)), (0.66, 0.6, 0.58), 1.0)
    sub = put(sub, ss(0.95, 0.97, U), (0.66, 0.6, 0.58), 1.0)
    img[sl] = sub


def _paint_pigeon(img):
    sl, U, V = _px('pigeon_side')
    sp = PIGEON_SIDE
    x = sp['x0'] + U * (sp['x1'] - sp['x0']); z = sp['z0'] + V * (sp['z1'] - sp['z0'])
    sub = np.ones(U.shape + (3,), np.float32)
    for x0 in (-0.03, -0.068):
        cx = x0 - 0.3 * (z - 0.13)
        m = ss(0.0075, 0.005, np.abs(x - cx)) * ss(0.098, 0.106, z) * ss(0.168, 0.158, z)
        sub = put(sub, m, (0.42, 0.42, 0.46), 1.0)
    img[sl] = sub


def _paint_crab(img):
    sl, U, V = _px('crab_face')
    x = CRAB_FACE['x0'] + U * (CRAB_FACE['x1'] - CRAB_FACE['x0']); z = CRAB_FACE['z0'] + V * (CRAB_FACE['z1'] - CRAB_FACE['z0'])
    sub = np.ones(U.shape + (3,), np.float32)
    pts = [(-0.017, 0.062), (-0.008, 0.0555), (0.0, 0.054), (0.008, 0.0555), (0.017, 0.062)]
    sub = _stroke(sub, x, z, pts, 0.0032, 0.0032, (0.35, 0.16, 0.12), soft=0.0007)
    # rosy cheeks
    for sx in (-1, 1):
        d = np.hypot((x - sx * 0.036) / 1.4, z - 0.062)
        sub = put(sub, ss(0.011, 0.004, d), (1.0, 0.82, 0.8), 0.5)
    img[sl] = sub


def _paint_dog_face(img):
    sl, U, V = _px('dog_face')
    sp = DOG_FACE
    X = sp['x0'] + U * (sp['x1'] - sp['x0']); Z = sp['z0'] + V * (sp['z1'] - sp['z0'])
    sub = np.ones(U.shape + (3,), np.float32)
    sub = _stroke(sub, X, Z, sp['mouth'], 0.0062, 0.0042, (0.34, 0.22, 0.19))
    img[sl] = sub


def paint_atlas(path):
    rng = np.random.default_rng(11)
    img = np.ones((AT, AT, 3), np.float32)
    _paint_eye(img, 'eye', 'dark')
    _paint_eye(img, 'eye_cat', 'cat')
    _paint_eye(img, 'eye_bird', 'bird')
    _paint_nose(img)
    _paint_feather(img)
    _paint_wing(img)
    _paint_dog_face(img)
    _paint_cat(img)
    _paint_crab(img)
    _paint_pigeon(img)
    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
