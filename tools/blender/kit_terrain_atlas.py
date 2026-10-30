# The terrain kit's atlas (TerrainAtlas.png): soft painted detail that multiplies the vertex
# colours. Everything is near-white and almost neutral, so the colour comes from the vertex
# colours and a recolour of a part (UV2.x) keeps the painted detail.
#   stone     side faces of rocks: mottling, weathering streaks, speckle, a few hairline cracks
#   stonetop  up faces of rocks: mottling, lichen spots, speckle
#   strata    side faces of cliffs: wavy sedimentary bands and seams, streaks
#   grass     grass caps: short soft brush strokes
#   mountain  distant rock faces: gully streaks and faint bands (periodic in u, for tiling strips)
#   fields    rolling hills: a patchwork of fields and hedgerows (periodic in u)
#   sand      dunes and the sand pile: wind ripples and grain
#   gravel    the gravel pile: packed pebbles
#   white     plain white, around the kit_lib white corner UV (0.97, 0.03)
import math
import numpy as np

AT = 1024
REG = {
    'stone':    (0.0, 0.5, 0.5, 1.0),
    'stonetop': (0.5, 0.75, 0.75, 1.0),
    'grass':    (0.75, 0.75, 1.0, 1.0),
    'strata':   (0.5, 0.5, 1.0, 0.75),
    'mountain': (0.0, 0.25, 0.5, 0.5),
    'fields':   (0.5, 0.25, 1.0, 0.5),
    'sand':     (0.0, 0.0, 0.25, 0.25),
    'gravel':   (0.25, 0.0, 0.5, 0.25),
    'grain':    (0.75, 0.125, 0.875, 0.25),
    'white':    (0.875, 0.0, 1.0, 0.125),
}
MARGIN = 0.03     # UV inset inside each region (mip bleed)


def reg_uv(name, s, t, margin=MARGIN, clamp=True):
    u0, v0, u1, v1 = REG[name]
    if clamp:
        s = min(max(s, 0.0), 1.0); t = min(max(t, 0.0), 1.0)
    s = margin + s * (1 - 2 * margin); t = margin + t * (1 - 2 * margin)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


def _region(name):
    u0, v0, u1, v1 = REG[name]
    x0, x1 = int(round(u0 * AT)), int(round(u1 * AT)); y0, y1 = int(round((1 - v1) * AT)), int(round((1 - v0) * AT))
    w, h = x1 - x0, y1 - y0
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    # S, T: the [0, 1] coordinates the mesh UVs use inside the margin
    S = (U - MARGIN) / (1 - 2 * MARGIN); T = (V - MARGIN) / (1 - 2 * MARGIN)
    return (slice(y0, y1), slice(x0, x1)), S, T


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _noise(shape, cells, rng, periodic=False):
    """Smooth value noise of shape (h, w) with cells (cx, cy); periodic in x when asked."""
    from PIL import Image
    h, w = shape
    cx, cy = cells
    if periodic:
        small = rng.random((cy, cx)).astype(np.float32)
        tiled = np.concatenate([small, small, small], axis=1)
        im = Image.fromarray((tiled * 255).astype(np.uint8), 'L').resize((w * 3, h), Image.BICUBIC)
        a = np.asarray(im, np.float32) / 255.0
        return a[:, w:2 * w]
    small = (rng.random((cy, cx)) * 255).astype(np.uint8)
    im = Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def _per(arr, S):
    """Re-sample an array that repeats over the region's pixel width so it repeats over the mesh
    coordinate S in [0, 1] instead (the strips' x maps to S inside the margins)."""
    w = arr.shape[1]
    cols = np.clip((np.mod(S[0], 1.0) * w).astype(int), 0, w - 1)
    return arr[:, cols]


def _fbm(shape, base, rng, octaves=4, periodic=False, aspect=1.0):
    acc = np.zeros(shape, np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        c = int(base * 2 ** o)
        acc += amp * _noise(shape, (max(2, c), max(2, int(c * aspect))), rng, periodic)
        tot += amp; amp *= 0.5
    return acc / tot


def _blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def _dots(img, rng, count, rmin, rmax, col, alpha, where=None):
    h, w = img.shape[:2]
    ys = rng.integers(0, h, count); xs = rng.integers(0, w, count)
    for y, x in zip(ys, xs):
        if where is not None and rng.random() > where[y, x]: continue
        r = rng.uniform(rmin, rmax)
        y0, y1 = max(0, int(y - r - 1)), min(h, int(y + r + 2)); x0, x1 = max(0, int(x - r - 1)), min(w, int(x + r + 2))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((yy - y) ** 2 + (xx - x) ** 2)
        m = np.clip(r + 0.5 - d, 0, 1)[..., None] * alpha
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + np.array(col)[None, None] * m


def _crack(img, rng, x, y, steps, ang, col=(0.62, 0.6, 0.64), width=1.0, alpha=0.55, turn=0.2):
    h, w = img.shape[:2]
    for i in range(steps):
        ang += rng.uniform(-turn, turn)
        x += math.cos(ang) * 2.0; y += math.sin(ang) * 2.0
        if not (2 <= x < w - 2 and 2 <= y < h - 2): break
        a = alpha * (1 - i / steps * 0.7)
        y0, y1, x0, x1 = int(y) - 2, int(y) + 3, int(x) - 2, int(x) + 3
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((yy - y) ** 2 + (xx - x) ** 2)
        m = np.clip(width + 0.5 - d, 0, 1)[..., None] * a
        img[y0:y1, x0:x1] = np.minimum(img[y0:y1, x0:x1], img[y0:y1, x0:x1] * (1 - m) + np.array(col)[None, None] * m)
        # a light lip beside the crack (chipped edge)
        y2 = int(y) - 2
        if 0 <= y2 < h:
            img[y2, int(x)] = np.minimum(1.0, img[y2, int(x)] * 1.02)


def paint(path):
    rng = np.random.default_rng(11)
    img = np.ones((AT, AT, 3), np.float32)

    # ---- stone: mottled, streaked, speckled, a few cracks
    sl, S, T = _region('stone')
    sh = S.shape
    sub = np.ones(sh + (3,), np.float32)
    mott = _fbm(sh, 5, rng, 4)
    sub *= (0.86 + 0.14 * mott)[..., None]
    warm = _fbm(sh, 3, rng, 2)
    sub = _blend(sub, _ss(0.55, 0.8, warm), (1.0, 0.95, 0.90), 0.35)
    sub = _blend(sub, _ss(0.55, 0.8, 1 - warm), (0.93, 0.93, 1.0), 0.35)
    streak = _noise(sh, (46, 7), rng) * _fbm(sh, 3, rng, 2)
    sub *= (1 - 0.05 * _ss(0.35, 0.6, streak))[..., None]
    _dots(sub, rng, 2600, 0.5, 1.3, (0.70, 0.68, 0.72), 0.35)
    _dots(sub, rng, 1400, 0.5, 1.2, (1.0, 1.0, 1.0), 0.4)
    _dots(sub, rng, 160, 2.0, 5.0, (0.86, 0.84, 0.88), 0.3)
    for _ in range(7):
        _crack(sub, rng, rng.uniform(0, sh[1]), rng.uniform(0, sh[0]), int(rng.integers(8, 22)), rng.uniform(0, 2 * math.pi), alpha=0.35, turn=0.12)
    img[sl] = sub

    # ---- stone top: mottling and lichen
    sl, S, T = _region('stonetop')
    sh = S.shape
    sub = np.ones(sh + (3,), np.float32)
    sub *= (0.90 + 0.10 * _fbm(sh, 4, rng, 4))[..., None]
    lich = _fbm(sh, 6, rng, 3)
    sub = _blend(sub, _ss(0.62, 0.70, lich), (0.90, 0.94, 0.82), 0.4)
    lich2 = _fbm(sh, 7, rng, 3)
    sub = _blend(sub, _ss(0.66, 0.72, lich2), (1.0, 0.94, 0.84), 0.35)
    _dots(sub, rng, 900, 0.5, 1.2, (0.72, 0.7, 0.74), 0.35)
    _dots(sub, rng, 260, 1.0, 2.4, (0.94, 0.97, 0.86), 0.5)
    img[sl] = sub

    # ---- strata: wavy bands for cliff sides (t = height)
    sl, S, T = _region('strata')
    sh = S.shape
    wob = (_fbm(sh, 3, rng, 3, aspect=0.5) - 0.5) * 0.06 + 0.012 * np.sin(S * 2 * math.pi * 3)
    tt = T + wob
    nb = 8
    band = tt * nb
    k = np.floor(band); fr = band - k
    tone = 0.94 + 0.05 * np.sin(k * 2.7 + 0.6) * np.cos(k * 1.3)
    sub = np.ones(sh + (3,), np.float32) * tone[..., None]
    # each band lighter at its top lip, a dark seam under it
    sub *= (0.94 + 0.06 * _ss(0.55, 0.95, fr))[..., None]
    seam = _ss(0.06, 0.0, np.minimum(fr, 1 - fr))
    sub = _blend(sub, seam, (0.72, 0.70, 0.76), 0.5)
    sub *= (0.92 + 0.08 * _fbm(sh, 6, rng, 3))[..., None]
    streak = _noise(sh, (60, 7), rng) * _fbm(sh, 4, rng, 2)
    sub *= (1 - 0.05 * _ss(0.35, 0.62, streak))[..., None]
    _dots(sub, rng, 1800, 0.5, 1.2, (0.72, 0.7, 0.74), 0.35)
    for _ in range(10):
        _crack(sub, rng, rng.uniform(0, sh[1]), rng.uniform(0, sh[0]), int(rng.integers(6, 18)), math.pi / 2 + rng.uniform(-0.3, 0.3), alpha=0.4, turn=0.1)
    img[sl] = sub

    # ---- grass: short soft strokes
    sl, S, T = _region('grass')
    sh = S.shape
    sub = np.ones(sh + (3,), np.float32) * (0.86 + 0.12 * _fbm(sh, 4, rng, 3))[..., None]
    h, w = sh
    for _ in range(3200):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        L = rng.uniform(3, 9); a = -math.pi / 2 + rng.uniform(-0.5, 0.5)
        val = rng.uniform(0.70, 1.0)
        for s in np.linspace(0, 1, 6):
            px, py = int(x + math.cos(a) * L * s) % w, int(y + math.sin(a) * L * s) % h
            sub[py, px] = sub[py, px] * 0.4 + val * 0.6
    img[sl] = sub

    # ---- mountain: gullies (dark streaks running down), faint bands; periodic in S
    sl, S, T = _region('mountain')
    sh = S.shape
    g1 = _per(_noise(sh, (120, 5), rng, periodic=True), S)
    g2 = _per(_noise(sh, (40, 3), rng, periodic=True), S)
    gul = _ss(0.74, 0.92, g1) * _ss(0.35, 0.7, g2)
    sub = np.ones(sh + (3,), np.float32) * (0.93 + 0.07 * _per(_fbm(sh, 6, rng, 3, periodic=True), S))[..., None]
    sub *= (1 - 0.08 * gul)[..., None]
    ridge = _ss(0.25, 0.05, g1)
    sub = np.minimum(1.0, sub * (1 + 0.04 * ridge)[..., None])
    bands = 0.5 + 0.5 * np.sin(T * 2 * math.pi * 9 + (g2 - 0.5) * 2.0)
    sub *= (0.97 + 0.03 * bands)[..., None]
    img[sl] = sub

    # ---- fields: patchwork with hedgerows; periodic in S (x along the strip), T across it
    sl, S, T = _region('fields')
    sh = S.shape
    h, w = sh
    npts = 70
    px = rng.random(npts); py = rng.random(npts)
    aspect = 2.6        # the strip region is wider (in metres) than it is deep
    best = np.full(sh, 9.0, np.float32); second = np.full(sh, 9.0, np.float32); idx = np.zeros(sh, np.int32)
    for i in range(npts):
        for sx in (-1.0, 0.0, 1.0):
            dx = (S - px[i] - sx) * aspect; dy = (T - py[i])
            d = np.sqrt(dx * dx + dy * dy)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d))
            idx = np.where(closer, i, idx)
            best = np.where(closer, d, best)
    tones = 0.88 + 0.12 * rng.random(npts)
    tints = np.array([(1.0, 0.97, 0.88) if r < 0.3 else (0.95, 1.0, 0.97) if r < 0.55 else (1.0, 1.0, 1.0)
                      for r in rng.random(npts)], np.float32)
    sub = tints[idx] * tones[idx][..., None]
    stripe_ang = rng.uniform(0, math.pi, npts); striped = rng.random(npts) < 0.35
    ang = stripe_ang[idx]
    kx = np.round(26 * aspect * np.cos(ang))          # whole cycles along S, so stripes tile
    st = np.sin((S * kx + T * 26 * np.sin(ang)) * 2 * math.pi)
    sub *= (1 - 0.025 * (st > 0.2) * striped[idx])[..., None]
    edge = second - best
    sub = _blend(sub, _ss(0.007, 0.002, edge), (0.70, 0.72, 0.66), 0.5)
    sub *= (0.95 + 0.05 * _per(_fbm(sh, 8, rng, 3, periodic=True), S))[..., None]
    img[sl] = sub

    # ---- sand: wind ripples and grain
    sl, S, T = _region('sand')
    sh = S.shape
    warp = (_fbm(sh, 3, rng, 2) - 0.5) * 0.12
    ph = (T + 0.06 * np.sin(S * 2 * math.pi * 1.3) + warp) * 34
    fr = ph - np.floor(ph)
    rip = _ss(0.0, 0.75, fr) * _ss(1.0, 0.85, fr)        # gentle rise, sharp crest
    sub = np.ones(sh + (3,), np.float32) * (0.91 + 0.08 * rip)[..., None]
    sub *= (0.97 + 0.03 * _fbm(sh, 10, rng, 2))[..., None]
    _dots(sub, rng, 1800, 0.4, 0.9, (0.84, 0.82, 0.80), 0.4)
    _dots(sub, rng, 900, 0.4, 0.8, (1.0, 1.0, 1.0), 0.5)
    img[sl] = sub

    # ---- gravel: packed pebbles, lit from above, dark gaps
    sl, S, T = _region('gravel')
    sh = S.shape
    h, w = sh
    sub = np.ones(sh + (3,), np.float32) * 0.46
    for _ in range(1500):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        rx, ry = rng.uniform(3.0, 6.5), rng.uniform(2.5, 5.0)
        a = rng.uniform(0, math.pi)
        tone = rng.uniform(0.66, 1.0)
        tint = np.array((1.0, 0.98, 0.95)) if rng.random() < 0.5 else np.array((0.95, 0.96, 1.0))
        y0, y1 = max(0, int(cy - 8)), min(h, int(cy + 9)); x0, x1 = max(0, int(cx - 8)), min(w, int(cx + 9))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dx, dy = xx - cx, yy - cy
        u = (dx * math.cos(a) + dy * math.sin(a)) / rx; v = (-dx * math.sin(a) + dy * math.cos(a)) / ry
        d = np.sqrt(u * u + v * v)
        m = np.clip((1 - d) * 4, 0, 1)
        lit = np.clip(0.75 - 0.35 * (dy / ry) * 0.8 - 0.15 * (dx / rx), 0.35, 1.0)
        col = tone * tint[None, None, :] * (0.55 + 0.45 * lit)[..., None] * (1 - 0.25 * d)[..., None]
        sub[y0:y1, x0:x1] = sub[y0:y1, x0:x1] * (1 - m[..., None]) + col * m[..., None]
    img[sl] = np.clip(sub * 1.2 + 0.04, 0, 1)

    # ---- grain: builder's sand, damp clumps and grain, no ripples
    sl, S, T = _region('grain')
    sh = S.shape
    sub = np.ones(sh + (3,), np.float32) * (0.92 + 0.08 * _fbm(sh, 6, rng, 3))[..., None]
    _dots(sub, rng, 900, 0.4, 0.9, (0.80, 0.78, 0.76), 0.45)
    _dots(sub, rng, 500, 0.4, 0.8, (1.0, 1.0, 1.0), 0.5)
    _dots(sub, rng, 60, 1.0, 2.2, (0.86, 0.84, 0.82), 0.4)
    img[sl] = sub

    # ---- white (the kit_lib corner, UV (0.97, 0.03), and around it)
    sl, S, T = _region('white')
    img[sl] = 1.0

    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
    return path
