# PlantsAtlas.png for kit_plants.py: grey-scale painted detail that the vertex colours tint
# (vertex colour x atlas). Every region is a near-white tile, so the hue and the baked shading
# live in the vertex colours (and survive the game's recolour); the atlas adds the crafted
# strokes: bark furrows, birch marks, cherry lenticels, palm-trunk fibre, conifer needles,
# palm leaflets and clipped-hedge leaves. Plain white corner at UV (0.97, 0.03).
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


def paint_atlas(path, seed=11):
    rng = np.random.default_rng(seed)
    img = np.ones((AT, AT), np.float32)
    for name, fn in PAINTERS.items():
        sl, U, V = _px(name)
        h, w = U.shape
        img[sl] = fn(rng, h, w, U, V)
    sl, _, _ = _px('white'); img[sl] = 1.0
    rgb = np.repeat(img[..., None], 3, axis=2)
    # a faint warm cast in the bark tiles' dark strokes (painted, not grey)
    warm = np.array([0.90, 0.96, 1.0], np.float32)
    rgb = 1 - (1 - rgb) * warm[None, None, :]
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
    return path
