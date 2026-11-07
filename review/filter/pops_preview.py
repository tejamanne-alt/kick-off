"""Preview of UI/ComicPops over a filtered frame, with ComicLettering's and the lettering shader's
numbers (stroke 0.09 of the size in a ring of 12, a drop shadow 2 strokes down-right, the gradient
eased between 0.15 and 0.85 of the height, dots from 0.45 down on an 8 px 45-degree screen) and
ComicPops' burst (13 spikes, ink edge, pale heart). Positions are in a 1920x1080 frame (the HUD's
reference size), 150 above the action, kept in the middle of the screen.
   python3 pops_preview.py <frame.png> <font.ttf> <out.png> word:x:y:size:style:burst:tilt ..."""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

STYLES = {  # top, bottom, dots (ComicPops)
    'hot': ((255, 237, 84), (247, 105, 36), (214, 41, 31)),
    'cool': ((255, 252, 237), (110, 209, 230), (41, 120, 199)),
    'ouch': ((255, 247, 235), (245, 115, 153), (209, 33, 102)),
}
INK = (23, 13, 41)


def burst(size):
    """ComicPops.BurstSprite: a star polygon of 14 straight spikes (tips 0.8-1, notches 0.46-0.54), a
    yellow fill with a thin ink edge and the same star at half size as a pale heart."""
    N, n = 256, 28
    rng = random.Random(11)
    pts = []
    for i in range(n):
        a = (i + (rng.random() - 0.5) * 0.35) * 2 * math.pi / n + 0.13
        r = (0.8 + rng.random() * 0.2) if i % 2 == 0 else (0.46 + rng.random() * 0.08)
        pts.append((math.cos(a) * r, math.sin(a) * r))
    P = np.array(pts)
    yy, xx = np.mgrid[0:N, 0:N]
    px, py = (xx + 0.5 - N / 2) / (N / 2), (N / 2 - (yy + 0.5)) / (N / 2)

    def sdist(s):
        A, B = P * s, np.roll(P * s, -1, axis=0)
        best = np.full(px.shape, 1e9); inside = np.zeros(px.shape, bool)
        for (ax, ay), (bx, by) in zip(A, B):
            dx, dy = bx - ax, by - ay
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12), 0, 1)
            best = np.minimum(best, np.hypot(ax + dx * t - px, ay + dy * t - py))
            cross = ((ay > py) != (by > py)) & (px < (bx - ax) * (py - ay) / np.where(by - ay == 0, 1e-12, by - ay) + ax)
            inside ^= cross
        return np.where(inside, best, -best)

    d = sdist(1.0); heart = sdist(0.5) > 0
    edge, aa = 4 / (N / 2), 1.2 / (N / 2)
    out = np.zeros((N, N, 4), np.uint8)
    col = np.where((d < edge)[..., None], np.array(INK + (255,)), np.where(heart[..., None], np.array((255, 248, 214, 255)), np.array((255, 214, 58, 255))))
    out[...] = col
    out[..., 3] = (255 * np.clip((d + aa) / aa, 0, 1)).astype(np.uint8)
    return Image.fromarray(out).resize((size, size), Image.LANCZOS)


def word(text, size, style, font_path):
    f = ImageFont.truetype(font_path, size)
    w = size * 0.09
    l, t, r, b = f.getbbox(text)
    pad = int(w * 4 + 10)
    W, H = r - l + pad * 2, b - t + pad * 2
    o = (pad - l, pad - t)
    mask = Image.new('L', (W, H)); ImageDraw.Draw(mask).text(o, text, font=f, fill=255)
    m = np.asarray(mask).astype(float) / 255
    ink = np.zeros_like(m)

    def shifted(dx, dy):
        return np.asarray(mask.transform(mask.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy))).astype(float) / 255

    for k in range(8):
        a = k * 2 * math.pi / 8
        ink = np.maximum(ink, shifted(w * 2 + math.cos(a) * w, w * 2 - math.sin(a) * w))
    for k in range(12):
        a = k * 2 * math.pi / 12
        ink = np.maximum(ink, shifted(math.cos(a) * w, -math.sin(a) * w))
    top, bot, dotc = (np.array(c, float) for c in STYLES[style])
    ys = np.where(m.max(1) > 0.5)[0]
    y0, y1 = ys.min(), ys.max()
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    t = np.clip((yy - y0) / max(y1 - y0, 1), 0, 1)
    g = np.clip((t - 0.15) / 0.7, 0, 1); g = g * g * (3 - 2 * g)
    fill = top + (bot - top) * g[..., None]
    cov = np.clip((t - 0.45) * 1.4, 0, 1) * 0.9
    period = 8.0
    u, v = (xx + yy) / (period * 1.41421356), (xx - yy) / (period * 1.41421356)
    d = np.hypot(u - np.round(u), v - np.round(v))
    dm = np.clip((np.sqrt(cov) * 0.6 - d) * period * 0.8 + 0.5, 0, 1) * (cov > 0.02)
    fill = fill + (dotc - fill) * dm[..., None]
    rgb = np.array(INK, float) * (1 - m[..., None]) + fill * m[..., None]
    alpha = np.maximum(ink, m)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), 'RGBA')


GRAPHITE = (43, 43, 51)
PENCIL = {  # ComicPops' pencil lettering: top, bottom (the hatching is graphite)
    'phot': ((255, 251, 242), (255, 204, 133)),
    'pcool': ((255, 251, 242), (168, 219, 237)),
    'pouch': ((255, 251, 242), (250, 179, 196)),
}


def over(dst, rgb, a):
    """dst (HxWx4 float 0..1, premultiplied-free) under a layer of colour rgb and alpha a."""
    a = a[..., None]
    out_a = a + dst[..., 3:] * (1 - a)
    out_rgb = (np.asarray(rgb, float) * a + dst[..., :3] * dst[..., 3:] * (1 - a)) / np.maximum(out_a, 1e-6)
    return np.concatenate([out_rgb, out_a], -1)


def word_pencil(text, size, style, font_path):
    """ComicLettering with sketch: smudge (6 at 1.6 w, 0.22), second line (8 at 0.7 w, offset 1.2/0.8 w, 0.55),
    line (8 at w, 1.0) in graphite, stroke 0.05, shadow 1.8; fill paper to wash, hatched below 0.45 (period 6)."""
    f = ImageFont.truetype(font_path, size)
    w = size * 0.05
    l, t, r, b = f.getbbox(text)
    pad = int(w * 6 + 12)
    W, H = r - l + pad * 2, b - t + pad * 2
    o = (pad - l, pad - t)
    mask = Image.new('L', (W, H)); ImageDraw.Draw(mask).text(o, text, font=f, fill=255)
    m = np.asarray(mask).astype(float) / 255

    def shifted(dx, dy):
        return np.asarray(mask.transform(mask.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy))).astype(float) / 255

    img = np.zeros((H, W, 4))
    drop = w * 1.8
    for k in range(6):
        a = k * 2 * math.pi / 6
        img = over(img, np.array(GRAPHITE) / 255, shifted(drop + math.cos(a) * w * 1.6, drop - math.sin(a) * w * 1.6) * 0.22)
    for k in range(8):
        a = k * 2 * math.pi / 8
        img = over(img, np.array(GRAPHITE) / 255, shifted(w * 1.2 + math.cos(a) * w * 0.7, -w * 0.8 - math.sin(a) * w * 0.7) * 0.55)
    for k in range(8):
        a = k * 2 * math.pi / 8
        img = over(img, np.array(GRAPHITE) / 255, shifted(math.cos(a) * w, -math.sin(a) * w))
    top, bot = (np.array(c, float) / 255 for c in PENCIL[style])
    ys = np.where(m.max(1) > 0.5)[0]
    y0, y1 = ys.min(), ys.max()
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    tt = np.clip((yy - y0) / max(y1 - y0, 1), 0, 1)
    g = np.clip((tt - 0.15) / 0.7, 0, 1); g = g * g * (3 - 2 * g)
    fill = top + (bot - top) * g[..., None]
    cov = np.clip((tt - 0.45) * 1.4, 0, 1) * 0.9
    period = 6.0
    across = (xx + yy) / (period * 1.41421356)
    from_line = np.abs((across % 1.0) - 0.5) * period
    grain = np.modf(np.abs(np.sin(xx * 12.9898 + yy * 78.233) * 43758.5453))[0]
    hatch = np.clip(cov * period * 0.4 - from_line + 0.5, 0, 1) * (0.6 + 0.4 * grain) * (cov > 0.02)
    fill = fill + (np.array(GRAPHITE) / 255 - fill) * hatch[..., None]
    img = over(img, fill, m)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGBA')


def burst_pencil(size):
    """ComicPops.BurstSprite(true): the star in pencil: a yellow wash hatched across the spikes, a paper heart,
    a thin graphite edge and a second outline turned 0.045 rad and 3 percent bigger."""
    N, n = 256, 28
    rng = random.Random(11)
    pts = []
    for i in range(n):
        a = (i + (rng.random() - 0.5) * 0.35) * 2 * math.pi / n + 0.13
        r = (0.8 + rng.random() * 0.2) if i % 2 == 0 else (0.46 + rng.random() * 0.08)
        pts.append((math.cos(a) * r, math.sin(a) * r))
    P = np.array(pts)
    c, s_ = math.cos(0.045), math.sin(0.045)
    P2 = np.stack([P[:, 0] * c - P[:, 1] * s_, P[:, 0] * s_ + P[:, 1] * c], -1) * 1.03
    yy, xx = np.mgrid[0:N, 0:N]
    px, py = (xx + 0.5 - N / 2) / (N / 2), (N / 2 - (yy + 0.5)) / (N / 2)

    def sdist(Q, s):
        A, B = Q * s, np.roll(Q * s, -1, axis=0)
        best = np.full(px.shape, 1e9); inside = np.zeros(px.shape, bool)
        for (ax, ay), (bx, by) in zip(A, B):
            dx, dy = bx - ax, by - ay
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12), 0, 1)
            best = np.minimum(best, np.hypot(ax + dx * t - px, ay + dy * t - py))
            inside ^= ((ay > py) != (by > py)) & (px < (bx - ax) * (py - ay) / np.where(by - ay == 0, 1e-12, by - ay) + ax)
        return np.where(inside, best, -best)

    d, d2, heart = sdist(P, 1.0), sdist(P2, 1.0), sdist(P, 0.5) > 0
    rngg = np.random.default_rng(5); grain = 0.6 + 0.4 * rngg.random((N, N))
    lead = np.array(GRAPHITE, float)
    col = np.where(heart[..., None], np.array((255, 251, 238.)), np.array((255, 236, 176.)))
    alpha = np.where(heart, 240., 235.)
    hatch = (~heart) & (np.abs(((xx + (N - 1 - yy)) / 9.0) % 1.0 - 0.5) * 9 < 0.8)
    col = np.where(hatch[..., None], col + (lead - col) * (0.45 * grain)[..., None], col)
    edge = d < 2.6 / (N / 2)
    col = np.where(edge[..., None], col + (lead - col) * grain[..., None], col)
    aa = 1.2 / (N / 2)
    alpha = alpha * np.clip((d + aa) / aa, 0, 1)
    second = np.abs(d2) < 1.4 / (N / 2)
    outside = alpha <= 0
    col = np.where((second & ~outside)[..., None], col + (lead - col) * (0.55 * grain)[..., None], col)
    col = np.where((second & outside)[..., None], lead, col)
    alpha = np.where(second & outside, 150 * grain, alpha)
    out = np.dstack([col, alpha]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA').resize((size, size), Image.LANCZOS)


frame = Image.open(sys.argv[1]).convert('RGBA').resize((1920, 1080))
font = sys.argv[2]
for spec in sys.argv[4:]:
    text, x, y, size, style, has_burst, tilt = spec.split(':')
    x, y, size, tilt = float(x), float(y), int(size), float(tilt)
    layer = Image.new('RGBA', frame.size)
    if has_burst == '1':
        bs = int(size * (2.6 if len(text) > 6 else 2.1))
        b = (burst_pencil(bs) if style in PENCIL else burst(bs)).rotate(tilt * 0.6, resample=Image.BICUBIC)
        layer.alpha_composite(b, (int(x - size * 0.15 - b.width / 2), int(y + size * 0.05 - b.height / 2)))
    wimg = (word_pencil(text, size, style, font) if style in PENCIL else word(text, size, style, font)).rotate(tilt, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(wimg, (int(x - wimg.width / 2), int(y - wimg.height / 2)))
    frame = Image.alpha_composite(frame, layer)
frame.convert('RGB').save(sys.argv[3], quality=92)
