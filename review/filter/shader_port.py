"""A line-for-line numpy port of Shaders/PostFX.shader (Grade, pass 4 'comic', pass 5 'print'),
with PostFX.cs's default settings, so the filter can be previewed outside Unity on renders of the
game's own models. Inputs are what the camera has at the end of a frame:
  colour  HxWx3 linear-ish 0..1 (the picture), alpha HxW (ToonCharacter's _ComicWorld: 0 figures),
  depth01 HxW (0..1 of the far plane, 1 = sky), normal HxWx3 (view space, unit)."""
import numpy as np

LUM = np.array([0.299, 0.587, 0.114])

# PostFX.cs defaults
GRADE = dict(balance=np.array([1, 1, 1.01]), toeEnd=0.28, toeFloor=0.7, contrast=1.1, shoulder=0.84,
             whitePoint=0.972, saturation=1.0, vibrance=1.12, shadowTint=np.array([0, 0, 0.006]),
             midTint=np.array([0.006, -0.004, 0.002]), highlightTint=np.zeros(3), vignette=0.12)
COMIC = dict(comicSaturation=1.4, comicContrast=1.15, bands=4.0, bandMix=0.7, dotPeriod=8.5, dotReach=0.66,
             dotSize=0.6, dotStrength=1.0, characterDots=1.0, hatchStrength=0.55, inkWidth=1.3,
             inkStrength=0.9, inkFar=90.0, depthEdge=0.05, normalEdge=0.3,
             inkColor=np.array([0.06, 0.05, 0.12]), slip=4.0, paper=np.array([0.88, 0.75, 0.5, 0.04]), grain=0.04)


def saturate(x):
    return np.clip(x, 0, 1)


def smoothstep(e0, e1, x):
    t = saturate((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def dot3(a, b):
    return (a * b).sum(-1)


def grade(c, uv, g=GRADE):
    return vignette(grade_colour(c, uv, g), uv, g)


def vignette(c, uv, g=GRADE):
    p = uv - 0.5
    return saturate(c * (1 - g['vignette'] * smoothstep(0.25, 0.85, dot3(p, p)[..., None] * 2.2)))


def grade_colour(c, uv, g=GRADE):
    c = np.maximum(c * g['balance'], 0)
    c = c * (g['toeFloor'] + (1 - g['toeFloor']) * smoothstep(0, g['toeEnd'], c))
    c = (c - 0.5) * g['contrast'] + 0.5
    rng = max(g['whitePoint'] - g['shoulder'], 1e-3)
    rolled = g['shoulder'] + rng * (1 - np.exp(-np.maximum(c - g['shoulder'], 0) / rng))
    c = np.where(c >= g['shoulder'], rolled, c)
    l = dot3(c, LUM)[..., None]
    hi, lo = c.max(-1, keepdims=True), c.min(-1, keepdims=True)
    sat = (hi - lo) / np.maximum(hi, 1e-3)
    c = l + (c - l) * (g['vibrance'] + (g['saturation'] - g['vibrance']) * smoothstep(0, 0.6, sat))
    l = dot3(c, LUM)[..., None]
    sh = saturate(1 - l * 2) ** 2
    li = saturate(l * 2 - 1) ** 2
    mi = saturate(1 - np.abs(l - 0.45) / 0.3)
    return c + sh * g['shadowTint'] + mi * g['midTint'] + li * g['highlightTint']


def shift(a, dx, dy):
    """Sample a at (x+dx, y+dy) with clamp, like tex2D at uv + offset (dx, dy in pixels, rounded)."""
    h, w = a.shape[:2]
    ys = np.clip(np.arange(h) + int(round(dy)), 0, h - 1)
    xs = np.clip(np.arange(w) + int(round(dx)), 0, w - 1)
    return a[ys][:, xs]


def comic_pass(colour, alpha, depth01, normal, far, k=COMIC, mask_on=1.0):
    h, w, _ = colour.shape
    scale = h / 1080.0
    period = max(3.0, k['dotPeriod'] * scale)
    inkw = max(0.75, k['inkWidth'] * scale)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)

    world = (1 + (saturate(alpha) - 1) * mask_on)[..., None]
    c = saturate(grade_colour(colour, uv))
    l = dot3(c, LUM)[..., None]
    vivid = saturate(l + (c - l) * k['comicSaturation'])
    vivid = saturate((vivid - 0.5) * k['comicContrast'] + 0.5)
    c = vivid

    l = dot3(c, LUM)[..., None]
    stepped = np.floor(l * k['bands'] + 0.5) / k['bands']
    banded = l + (stepped - l) * k['bandMix'] * (1 - smoothstep(0.62, 0.74, l))
    c = saturate(c * (banded / np.maximum(l, 1e-3)))

    px = np.stack([xx, (h - 1 - yy)], -1) + 0.5
    l = dot3(c, LUM)[..., None]
    cover = saturate((k['dotReach'] - l) / 0.5) * k['dotSize'] * (k['characterDots'] + (1 - k['characterDots']) * world)
    r = np.stack([px[..., 0] + px[..., 1], px[..., 0] - px[..., 1]], -1) / (period * 1.41421356)
    d = np.linalg.norm(r - np.floor(r + 0.5), axis=-1)[..., None]
    dotm = saturate((cover - d) * period * 0.9 + 0.5) * (cover >= 0.02)
    ink_dot = c * 0.55 * np.array([0.85, 0.8, 1.0])
    c = c + (ink_dot - c) * dotm * k['dotStrength']

    hatch = (np.sin((px[..., 0] - px[..., 1]) * 3.14159 / (period * 0.48)) >= 0.35)[..., None]
    deep = saturate((0.28 - l) / 0.15) * hatch
    c = c * (1 - deep * k['hatchStrength'])

    # ink line
    ds = [depth01, shift(depth01, inkw, 0), shift(depth01, -inkw, 0), shift(depth01, 0, -inkw), shift(depth01, 0, inkw)]
    ns = [normal, shift(normal, inkw, 0), shift(normal, -inkw, 0), shift(normal, 0, -inkw), shift(normal, 0, inkw)]
    near = np.minimum.reduce(ds)
    jump = np.maximum.reduce([np.abs(x - ds[0]) for x in ds[1:]]) / np.maximum(near, 1e-4)
    depth_line = smoothstep(k['depthEdge'], k['depthEdge'] * 2.5, jump)
    turn = 1 - np.minimum.reduce([dot3(ns[0], x) for x in ns[1:]])
    crease = smoothstep(k['normalEdge'], k['normalEdge'] * 2, turn) * world[..., 0]
    fade = 1 - smoothstep(k['inkFar'] * 0.45, k['inkFar'], near * far)
    ink = (saturate(np.maximum(depth_line, crease)) * fade * k['inkStrength'])[..., None]
    c = c + (k['inkColor'] - c) * ink
    return vignette(c, uv)


def print_pass(c, alpha=None, k=COMIC, mask_on=1.0):
    h, w, _ = c.shape
    scale = h / 1080.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    u, v = (xx + 0.5) / w, 1 - (yy + 0.5) / h
    p = np.stack([(u - 0.5) / 0.5, (v - 0.55) / 0.55], -1)
    r = saturate(np.linalg.norm(p, axis=-1) - 0.35)
    world = np.ones_like(r) if alpha is None else 1 + (np.clip(alpha, 0, 1) - 1) * mask_on
    off = np.rint(k['slip'] * scale * r * (0.5 + 0.5 * world)).astype(int)
    out = c.copy()
    out[..., 0] = c[yy.astype(int), np.clip(xx.astype(int) + off, 0, w - 1), 0]
    out[..., 2] = c[yy.astype(int), np.clip(xx.astype(int) - off, 0, w - 1), 2]
    a = k['paper'][3]
    out = out * (1 - a) + k['paper'][:3] * a
    pxv = np.stack([np.floor(xx), np.floor(h - 1 - yy)], -1)
    q = np.modf(pxv * np.array([123.34, 456.21]))[0]
    q = q + dot3(q, q + 45.32)[..., None]
    hsh = np.modf(q[..., 0] * q[..., 1])[0]
    out = out + (hsh - 0.5)[..., None] * k['grain']
    return saturate(out)


def plain(colour):
    h, w, _ = colour.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)
    return grade(colour, uv)
