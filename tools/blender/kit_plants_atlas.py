# PlantsAtlas.png for kit_plants.py: grey-scale painted detail that the vertex colours tint
# (vertex colour x atlas). Every region is a near-white tile, so the hue and the baked shading
# live in the vertex colours (and survive the game's recolour); the atlas adds the crafted
# strokes: bark furrows, birch marks, cherry lenticels, palm-trunk fibre, conifer needles,
# palm leaflets and clipped-hedge leaves. Plain white corner at UV (0.97, 0.03).
#
# Leaf sprites (the alpha channel): 128 px cells of leaf clusters for the trees' and bushes' leaf
# cards, cut out by the game's Toon shader (_ALPHATEST_ON, _Cutoff 0.5). Each cell is a clump of
# overlapping clover-like leaves (or small birch leaves, five-petal blossoms, or the bristly needle
# tufts of a pruned pine), the ones behind
# darker than the ones in front, inside a transparent margin. Their alpha is a soft ramp across
# the outline (0.5 on it) that tops out at LEAF_ALPHA (< 1), so the shader can tell cut-out
# texels from solid ones: only texels below 0.97 shrink away on cards seen edge-on (_EdgeFade);
# every other region is fully opaque (alpha 1).
import math
import numpy as np
from PIL import Image

AT = 1024
# (u0, v0, u1, v1) in UV space (v up)
REG = {
    'bark':   (0.000, 0.0, 0.125, 1.0),    # around x up, about 1.2 m x 8 m, tiles around
    'birch':  (0.125, 0.0, 0.250, 1.0),    # around x up, about 0.9 m x 8 m
    'cherry': (0.250, 0.0, 0.375, 1.0),
    'palm':   (0.375, 0.0, 0.500, 0.25),   # one trunk ring: around x ring height
    'needle': (0.500, 0.0, 0.750, 0.5),    # one conifer frond flank: valley (u 0) to ridge (u 1), trunk (v 0) to tip (v 1)
    'hedge':  (0.500, 0.5, 0.750, 1.0),    # clipped leaves: 1 m along the hedge x the section's outline
    'frond':  (0.750, 0.5, 1.000, 1.0),    # palm frond: left edge (u 0), midrib (0.5), right edge (1); base (v 0) to tip (1)
    'white':  (0.9375, 0.0, 1.0, 0.0625),
}
MARGIN = 3.0 / AT

# Leaf-card sprite cells (u0, v0), 0.125 x 0.125 each: seven beside the needles (the white corner
# keeps its own cell) and six above the palm ring.
CELL = 0.125
_CELLS = [(0.75, 0.375), (0.875, 0.375), (0.75, 0.25), (0.875, 0.25), (0.75, 0.125), (0.875, 0.125), (0.75, 0.0),
          (0.375, 0.875), (0.375, 0.75), (0.375, 0.625), (0.375, 0.5), (0.375, 0.375), (0.375, 0.25)]
SPRITES = {'leaf': _CELLS[0:7], 'birch': _CELLS[7:9], 'blossom': _CELLS[9:11], 'pine': _CELLS[11:13]}
LEAF_ALPHA = 0.9          # the most opaque a sprite texel gets (solid regions are 1.0)


def sprite_uv(kind, index, s, t, inset=2.0 / AT):
    """(s, t) in [0, 1] across a leaf sprite cell -> atlas UV."""
    u0, v0 = SPRITES[kind][index % len(SPRITES[kind])]
    return np.stack([u0 + inset + np.asarray(s) * (CELL - 2 * inset), v0 + inset + np.asarray(t) * (CELL - 2 * inset)], axis=-1)


def region_uv(name, s, t, margin=MARGIN):
    """(s, t) in [0, 1] inside a region -> atlas UV (s and t may be arrays)."""
    u0, v0, u1, v1 = REG[name]
    s = np.clip(s, 0, 1); t = np.clip(t, 0, 1)
    return np.stack([u0 + margin + s * (u1 - u0 - 2 * margin), v0 + margin + t * (v1 - v0 - 2 * margin)], axis=-1)


def _px(name):
    u0, v0, u1, v1 = REG[name]
    x0, x1 = int(round(u0 * AT)), int(round(u1 * AT))
    y0, y1 = int(round((1 - v1) * AT)), int(round((1 - v0) * AT))
    w, h = x1 - x0, y1 - y0
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    return (slice(y0, y1), slice(x0, x1)), U, V


def pnoise(h, w, cx, cy, rng):
    """Smooth value noise, periodic in both directions (cx x cy cells)."""
    g = rng.random((cy, cx)).astype(np.float32)
    big = np.tile(g, (3, 3))
    im = Image.fromarray(big, 'F').resize((w * 3, h * 3), Image.BICUBIC)
    a = np.asarray(im, np.float32)[h:2 * h, w:2 * w]
    lo, hi = a.min(), a.max()
    return (a - lo) / max(hi - lo, 1e-6)


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _ellipse(img, cx, cy, rx, ry, val, soft=1.0, wrap=True, mode='set', alpha=1.0):
    h, w = img.shape
    for ox in ((-w, 0, w) if wrap else (0,)):
        x = cx + ox
        x0, x1 = max(0, int(x - rx - 2)), min(w, int(x + rx + 3))
        y0, y1 = max(0, int(cy - ry - 2)), min(h, int(cy + ry + 3))
        if x0 >= x1 or y0 >= y1: continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt(((xx + 0.5 - x) / max(rx, 0.5)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.5)) ** 2)
        m = np.clip((1 - d) * min(rx, ry) / soft + 0.5, 0, 1) * alpha
        sub = img[y0:y1, x0:x1]
        if mode == 'set':
            img[y0:y1, x0:x1] = sub * (1 - m) + val * m
        elif mode == 'min':
            img[y0:y1, x0:x1] = np.minimum(sub, sub * (1 - m) + val * m)


def paint_bark(rng, h, w, U, V):
    # long bark plates split by wobbling vertical furrows (six round the trunk), a few cross-cracks
    wob = pnoise(h, w, 3, 10, rng) - 0.5
    wob2 = pnoise(h, w, 5, 34, rng) - 0.5
    fc = U * 6 + 0.9 * wob + 0.25 * wob2
    d = np.abs((fc % 1.0) - 0.5) * 2                  # 0 mid-plate, 1 in the furrow
    furrow = ss(0.6, 0.92, d)
    plate = 1 - 0.10 * ss(0.0, 0.6, d)
    cracks = ss(0.84, 0.95, pnoise(h, w, 4, 120, rng)) * (1 - furrow)
    val = 0.98 * plate - 0.36 * furrow - 0.16 * cracks - 0.06 * pnoise(h, w, 16, 60, rng)
    return np.clip(val, 0, 1)


def paint_birch(rng, h, w, U, V):
    img = 1.0 - 0.05 * pnoise(h, w, 4, 30, rng)
    # dark lenticel dashes, wider than tall, wrapping around
    for _ in range(170):
        y = rng.uniform(0.07, 1.0) * h
        _ellipse(img, rng.uniform(0, w), y, rng.uniform(5, 22), rng.uniform(1.2, 2.6), rng.uniform(0.18, 0.45), mode='min')
    # a few bold black "eyes" where old branches fell: a wide band, pinched at the ends
    for _ in range(11):
        cx, cy = rng.uniform(0, w), rng.uniform(0.12, 0.97) * h
        L = rng.uniform(20, 34)
        for k in range(9):
            t = (k - 4) / 4.0
            _ellipse(img, cx + t * L, cy - abs(t) * 3.0, 6.5 * (1 - 0.55 * abs(t)), 4.2 * (1 - 0.6 * abs(t)),
                     0.12, mode='min')
    # rough, dark base (birches blacken and crack near the ground)
    base = 0.055 + 0.03 * pnoise(h, w, 9, 3, rng)
    dark = ss(base + 0.02, base - 0.03, V)
    crack = ss(0.6, 0.9, 1 - np.abs(2 * pnoise(h, w, 8, 4, rng) - 1))
    img = img * (1 - dark) + (0.30 + 0.10 * crack) * dark
    # soft grey streaks low on the trunk
    img *= 1 - 0.18 * ss(0.22, 0.05, V) * pnoise(h, w, 6, 10, rng)
    return np.clip(img, 0, 1)


def paint_cherry(rng, h, w, U, V):
    img = 0.86 - 0.08 * pnoise(h, w, 5, 20, rng)
    for _ in range(260):
        y = rng.uniform(0, h)
        _ellipse(img, rng.uniform(0, w), y, rng.uniform(6, 18), rng.uniform(0.8, 1.6), 1.0, mode='set', alpha=0.75)
    for _ in range(120):
        y = rng.uniform(0, h)
        _ellipse(img, rng.uniform(0, w), y, rng.uniform(8, 26), rng.uniform(0.8, 1.5), 0.58, mode='min')
    return np.clip(img, 0, 1)


def paint_palm(rng, h, w, U, V):
    # one ring of a palm trunk: fibrous criss-cross, a dark groove at the bottom, a pale lip on top
    p1 = (U * 7 + V * 1.6) % 1.0; p2 = (U * 7 - V * 1.6 + 0.5) % 1.0
    l1 = ss(0.12, 0.03, np.abs(p1 - 0.5)); l2 = ss(0.10, 0.03, np.abs(p2 - 0.5))
    img = 0.95 - 0.16 * np.maximum(l1, l2 * 0.7) - 0.06 * pnoise(h, w, 9, 3, rng)
    img *= 1 - 0.38 * ss(0.22, 0.0, V)
    img = np.maximum(img, 1.0 * ss(0.86, 0.97, V))
    return np.clip(img, 0, 1)


def paint_needle(rng, h, w, U, V):
    # a frond flank: herringbone needle strokes running out toward the tip from the ridge
    jit = pnoise(h, w, 5, 9, rng)
    ph = (V * 22.0 - (1 - U) * 3.0 + jit * 0.35) % 1.0
    line = ss(0.14, 0.04, np.abs(ph - 0.5))
    img = 0.90 + 0.10 * ss(0.3, 1.0, U)
    img -= 0.14 * line * ss(0.98, 0.75, U)
    img -= 0.22 * ss(0.22, 0.0, U)                    # the valley between fronds
    img = np.where(U > 0.95, 1.0, img)                # pale midrib
    img -= 0.18 * ss(0.14, 0.0, V)                    # dark near the trunk
    img -= 0.05 * pnoise(h, w, 12, 24, rng)
    return np.clip(img, 0, 1)


def paint_frond(rng, h, w, U, V):
    a = np.abs(U - 0.5) * 2                           # 0 midrib -> 1 edge
    jit = pnoise(h, w, 6, 12, rng)
    ph = (V * 24.0 - a * 1.6 + jit * 0.25) % 1.0
    line = ss(0.14, 0.04, np.abs(ph - 0.5))
    img = 0.86 + 0.14 * ss(1.0, 0.1, a)
    img -= 0.24 * line * ss(0.08, 0.16, a)
    img = np.where(a < 0.045, 1.0, img)               # pale midrib
    img -= 0.16 * ss(0.045, 0.06, a) * ss(0.11, 0.07, a)
    img -= 0.10 * ss(0.85, 1.0, a)
    return np.clip(img, 0, 1)


def paint_hedge(rng, h, w, U, V):
    # clipped privet: many small leaves, each lit on top and shaded under, wrapping across u
    img = 0.80 + 0.05 * pnoise(h, w, 8, 14, rng)
    for _ in range(2600):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        rx = rng.uniform(3.5, 6.5); ry = rx * rng.uniform(0.55, 0.8)
        _ellipse(img, cx, cy + 1.2, rx, ry, 0.74, mode='set', alpha=0.8)
        _ellipse(img, cx, cy, rx * 0.92, ry * 0.9, rng.uniform(0.86, 0.98), mode='set')
        _ellipse(img, cx - rx * 0.2, cy - ry * 0.35, rx * 0.45, ry * 0.35, 1.0, mode='set', alpha=0.35)
    return np.clip(img, 0, 1)


PAINTERS = {'bark': paint_bark, 'birch': paint_birch, 'cherry': paint_cherry, 'palm': paint_palm,
            'needle': paint_needle, 'hedge': paint_hedge, 'frond': paint_frond}


# ---------------------------------------------------------------- leaf sprites
def _discs_sdf(P, discs):
    """Signed distance (cell units) from points P (N, 2) to a union of discs (k, 3: x, y, r), or
    (roughly) to a bristly tuft ('tuft', x, y, R, rot, teeth)."""
    if discs and discs[0] == 'tuft':
        _, x, y, R, rot, k = discs
        q = P - (x, y)
        ang = np.arctan2(q[:, 1], q[:, 0]) - rot
        u = ang * k / (2 * math.pi)
        f = u % 1.0
        idx = np.floor(u) % k
        tip = 0.45 + 0.55 * ((np.sin(idx * 12.9898 + rot * 78.233) * 43758.5453) % 1.0)   # uneven needle lengths
        tooth = (1 - np.abs(2 * f - 1)) ** 1.5 * tip                                   # 1 at a long needle tip
        return np.hypot(q[:, 0], q[:, 1]) - R * (0.76 + 0.3 * tooth)
    d = np.full(len(P), 9.0)
    for x, y, r in discs:
        d = np.minimum(d, np.hypot(P[:, 0] - x, P[:, 1] - y) - r)
    return d


def tuft(x, y, R, rot, teeth=15):
    """A pine-needle tuft: a round pom-pom with a bristly edge."""
    return ('tuft', x, y, R, rot, teeth)


def _centre(sh):
    """(x, y, size) of a shape."""
    if sh[0] == 'tuft':
        return sh[1], sh[2], sh[3]
    return sh[0][0], sh[0][1], max(r for _, _, r in sh)


def clover(x, y, R, rot, lobes=4):
    """A clover-like leaf: round lobes about a filled centre, R its outer radius."""
    a, b = (0.52 * R, 0.48 * R) if lobes == 4 else (0.5 * R, 0.52 * R)
    out = [(x, y, 0.45 * R)]
    for k in range(lobes):
        t = rot + 2 * math.pi * k / lobes
        out.append((x + a * math.cos(t), y + a * math.sin(t), b))
    return out


def small_leaf(x, y, R, rot):
    """A small ovate leaf (birch): two overlapping discs along its axis."""
    c, s = math.cos(rot), math.sin(rot)
    return [(x + c * 0.38 * R, y + s * 0.38 * R, 0.7 * R), (x - c * 0.3 * R, y - s * 0.3 * R, 0.62 * R)]


def blossom(x, y, R, rot):
    """A five-petal flower."""
    out = [(x, y, 0.42 * R)]
    for k in range(5):
        t = rot + 2 * math.pi * k / 5
        out.append((x + 0.55 * R * math.cos(t), y + 0.55 * R * math.sin(t), 0.43 * R))
    return out


def _scatter(rng, n, radius, rmin, rmax, sep=1.0, squash=1.0, tries=600):
    """n shape centres (cell units, centre 0.5) inside an irregular blob, kept a little apart."""
    lobe_ph = rng.uniform(0, 2 * math.pi, 3); lobe_a = rng.uniform(0.0, 0.12, 3)
    out = []
    for _ in range(tries):
        if len(out) >= n: break
        R = rng.uniform(rmin, rmax)
        a = rng.uniform(0, 2 * math.pi)
        lim = radius * (1 - sum(la * (0.5 + 0.5 * math.cos((k + 2) * a + p)) for k, (la, p) in enumerate(zip(lobe_a, lobe_ph))))
        rr = (lim - R) * math.sqrt(rng.uniform(0, 1))
        if rr < 0: continue
        x, y = 0.5 + rr * math.cos(a), 0.5 + rr * math.sin(a) * squash
        if any(math.hypot(x - q[0], y - q[1]) < sep * max(R, q[2]) for q in out): continue
        out.append((x, y, R))
    return out


def paint_sprite(rng, kind, px=128, ss=4, ramp_px=7.0):
    """One leaf-card sprite: grey value and alpha (px x px, row 0 at the top)."""
    if kind == 'leaf':
        n = int(rng.integers(10, 14))
        pts = _scatter(rng, n, 0.45, 0.1, 0.145, sep=0.95, tries=1200)
        shapes = [clover(x, y, R, rng.uniform(0, 2 * math.pi), 4 if rng.random() < 0.8 else 3) for x, y, R in pts]
        lo, hi = 0.7, 1.0
    elif kind == 'birch':
        # an airy clump of small ovate leaves, most of them hanging
        pts = _scatter(rng, int(rng.integers(48, 58)), 0.45, 0.05, 0.068, sep=0.8, tries=1500)
        shapes = [small_leaf(x, y, R, math.pi / 2 + rng.normal(0, 0.7)) for x, y, R in pts]
        lo, hi = 0.6, 1.0
    elif kind == 'pine':
        pts = _scatter(rng, int(rng.integers(11, 15)), 0.43, 0.1, 0.14, sep=0.85, tries=1200)
        shapes = [tuft(x, y, R, rng.uniform(0, 2 * math.pi), int(rng.integers(20, 28))) for x, y, R in pts]
        lo, hi = 0.55, 1.0
    else:                                       # blossom
        pts = _scatter(rng, int(rng.integers(20, 27)), 0.45, 0.06, 0.085, sep=1.05)
        shapes = [blossom(x, y, R, rng.uniform(0, 2 * math.pi)) for x, y, R in pts]
        lo, hi = 0.7, 1.0
    order = np.argsort(rng.uniform(0, 1, len(shapes)))
    shapes = [shapes[i] for i in order]
    bright = np.sort(rng.uniform(0, 1, len(shapes)))       # back to front: dark to light
    bright = lo + (hi - lo) * bright
    N = px * ss
    g = (np.arange(N) + 0.5) / N
    X, Y = np.meshgrid(g, g)
    P = np.stack([X.ravel(), Y.ravel()], axis=1)
    val = np.zeros(len(P)); covered = np.zeros(len(P), bool)
    near = np.full(len(P), 9.0); near_val = np.full(len(P), (lo + hi) / 2)
    shadow = np.array((0.012, 0.02))                        # each leaf shades the one behind, below right
    for sh, b in zip(shapes, bright):
        d = _discs_sdf(P, sh)
        ds = _discs_sdf(P - shadow, sh)
        val = np.where(covered & (ds < 0) & (d >= 0), val * 0.8, val)
        cx, cy, R = _centre(sh)
        shade = b * (1.0 + 0.07 * np.clip((cy - P[:, 1]) / (R * 1.6), -1, 1))     # lit a little toward its top
        if kind == 'blossom':
            eye = np.hypot(P[:, 0] - cx, P[:, 1] - cy) < sh[0][2] * 0.42
            shade = np.where(eye, shade * 0.62, shade)
        elif kind == 'pine':                                 # needle strokes radiating from the heart
            ang = np.arctan2(P[:, 1] - cy, P[:, 0] - cx)
            rr = np.hypot(P[:, 0] - cx, P[:, 1] - cy) / R
            shade = shade * (1 - 0.1 * (0.5 + 0.5 * np.cos(ang * 2 * sh[5] + 1.3)) * np.clip(rr * 1.4 - 0.2, 0, 1))
        inside = d < 0
        val = np.where(inside, shade, val)
        covered |= inside
        closer = d < near
        near_val = np.where(closer, b, near_val); near = np.minimum(near, d)
    val = np.where(covered, val, near_val)                  # outside: the nearest leaf's colour, so filtering never greys the edge
    alpha = LEAF_ALPHA * np.clip(0.5 / LEAF_ALPHA - near * px / ramp_px, 0, 1)
    val = val.reshape(px, ss, px, ss).mean(axis=(1, 3))
    alpha = alpha.reshape(px, ss, px, ss).mean(axis=(1, 3))
    return np.clip(val, 0, 1).astype(np.float32), alpha.astype(np.float32)


def paint_sprites(img, alpha, rng):
    for kind, cells in SPRITES.items():
        for (u0, v0) in cells:
            x0 = int(round(u0 * AT)); y0 = int(round((1 - v0 - CELL) * AT)); n = int(round(CELL * AT))
            v, a = paint_sprite(rng, kind, n)
            img[y0:y0 + n, x0:x0 + n] = v
            alpha[y0:y0 + n, x0:x0 + n] = a


def paint_atlas(path, seed=11):
    rng = np.random.default_rng(seed)
    img = np.ones((AT, AT), np.float32)
    alpha = np.ones((AT, AT), np.float32)
    for name, fn in PAINTERS.items():
        sl, U, V = _px(name)
        h, w = U.shape
        img[sl] = fn(rng, h, w, U, V)
    paint_sprites(img, alpha, np.random.default_rng(seed + 100))
    sl, _, _ = _px('white'); img[sl] = 1.0; alpha[sl] = 1.0
    rgb = np.repeat(img[..., None], 3, axis=2)
    # a faint warm cast in the bark tiles' dark strokes (painted, not grey)
    warm = np.array([0.90, 0.96, 1.0], np.float32)
    rgb = np.where(alpha[..., None] >= 1.0, 1 - (1 - rgb) * warm[None, None, :], rgb)
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.clip(alpha, 0, 1)[..., None]], axis=2)
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), 'RGBA').save(path)
    return path
