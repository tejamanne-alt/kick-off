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
    N = 256
    rng = random.Random(7)
    radius = [(0.84 + rng.random() * 0.16) if i % 2 == 0 else (0.42 + rng.random() * 0.12) for i in range(26)]
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5 - N / 2) / (N / 2), (N / 2 - (yy + 0.5)) / (N / 2)
    d = np.hypot(dx, dy)
    a = (np.arctan2(dy, dx) / (2 * np.pi) + 1) % 1 * 26
    i0 = np.floor(a).astype(int) % 26
    r = (np.array(radius)[i0] + (np.array(radius)[(i0 + 1) % 26] - np.array(radius)[i0]) * (a - np.floor(a))) * 0.98
    out = np.zeros((N, N, 4), np.uint8)
    edge = 7 / (N / 2)
    out[d <= r] = (255, 214, 58, 255)
    out[(d <= r) & (d > r - edge)] = INK + (255,)
    out[d < r * 0.5] = (255, 248, 214, 255)
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


frame = Image.open(sys.argv[1]).convert('RGBA').resize((1920, 1080))
font = sys.argv[2]
for spec in sys.argv[4:]:
    text, x, y, size, style, has_burst, tilt = spec.split(':')
    x, y, size, tilt = float(x), float(y), int(size), float(tilt)
    layer = Image.new('RGBA', frame.size)
    if has_burst == '1':
        bs = int(size * (2.6 if len(text) > 6 else 2.1))
        b = burst(bs).rotate(tilt * 0.6, resample=Image.BICUBIC)
        layer.alpha_composite(b, (int(x - size * 0.15 - b.width / 2), int(y + size * 0.05 - b.height / 2)))
    wimg = word(text, size, style, font).rotate(tilt, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(wimg, (int(x - wimg.width / 2), int(y - wimg.height / 2)))
    frame = Image.alpha_composite(frame, layer)
frame.convert('RGB').save(sys.argv[3], quality=92)
