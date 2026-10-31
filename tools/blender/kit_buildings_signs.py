# Shop signs, shop interiors seen through glass, a shop curtain and posters for the buildings
# kit's atlas (kit_buildings_atlas.py calls paint()). These tiles are absolute colour (the faces
# that sample them have white vertex colours), so a building's paint scheme never changes a shop's
# identity. All names are invented; the lettering is drawn with whatever fonts the machine has
# (Inter or DejaVu for the Latin names, IPA Gothic for the kana), and left out if it has none.
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from kit_buildings_geo import REG, reg_px

# name, width, height (pixels): kit_buildings.py allocates these in the atlas
TILES = [
    ('gl_mart', 192, 256), ('gl_cafe', 192, 256), ('gl_books', 192, 256), ('gl_flower', 192, 256),
    ('sg_mart', 768, 84), ('sg_cafe', 384, 72), ('sg_disc', 128, 128), ('sg_books', 576, 72),
    ('sg_flower', 576, 64), ('sg_noodle', 256, 72), ('sg_tall', 64, 288), ('noren2', 256, 96),
    ('poster1', 96, 136), ('poster2', 96, 136), ('books', 128, 64), ('lattice', 128, 192),
    ('gl_konbini', 256, 192), ('sg_konbini', 640, 64), ('recycle', 128, 64),
    ('gl_boutique', 192, 256), ('sg_boutique', 384, 96),
]

LATIN = ['/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf', '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']
LATIN_SOFT = ['/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf', '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'] + LATIN
KANA = ['/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
        '/etc/alternatives/fonts-japanese-gothic.ttf']


def _font(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return None


def _c(rgb):
    return tuple(int(round(255 * max(0.0, min(1.0, v)))) for v in rgb)


def text(dr, xy, s, paths, size, fill, anchor='mm', spacing=0):
    """Draw s centred on xy (anchor), shrinking it until it fits; nothing without a font."""
    f = _font(paths, size)
    if f is None: return
    if spacing:
        # letter-spaced: lay the characters out one by one
        widths = [dr.textlength(ch, font=f) for ch in s]
        tot = sum(widths) + spacing * (len(s) - 1)
        x = xy[0] - tot / 2 if anchor[0] == 'm' else xy[0]
        for ch, w in zip(s, widths):
            dr.text((x, xy[1]), ch, font=f, fill=_c(fill), anchor='l' + anchor[1])
            x += w + spacing
        return
    dr.text(xy, s, font=f, fill=_c(fill), anchor=anchor)


def fit(dr, s, paths, size, maxw):
    f = _font(paths, size)
    while f is not None and size > 8 and dr.textlength(s, font=f) > maxw:
        size -= 1; f = _font(paths, size)
    return size


def put_pil(img, name, draw, bg, pad=6, ss=3):
    """Draw a tile with PIL at ss x supersampling (draw(dr, w, h, k) gets the scale k), shrink it
    into the region and repeat its edge pixels into the bleed."""
    if name not in REG: return
    x0, y0, x1, y1 = reg_px(name)
    w, h = x1 - x0, y1 - y0
    im = Image.new('RGB', (w * ss, h * ss), _c(bg))
    dr = ImageDraw.Draw(im)
    draw(dr, w * ss, h * ss, ss)
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    H, W = img.shape[:2]
    a = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    ya, xa = y0 - pad, x0 - pad
    cy0, cx0 = max(0, -ya), max(0, -xa)
    cy1 = a.shape[0] - max(0, ya + a.shape[0] - H); cx1 = a.shape[1] - max(0, xa + a.shape[1] - W)
    img[ya + cy0:ya + cy1, xa + cx0:xa + cx1] = a[cy0:cy1, cx0:cx1]


# ---------------------------------------------------------------- icons (PIL, in pixels)
def bird(dr, cx, cy, s, body, beak):
    dr.ellipse([cx - 0.5 * s, cy - 0.32 * s, cx + 0.42 * s, cy + 0.36 * s], fill=_c(body))
    dr.ellipse([cx + 0.05 * s, cy - 0.55 * s, cx + 0.5 * s, cy - 0.1 * s], fill=_c(body))
    dr.polygon([(cx + 0.48 * s, cy - 0.36 * s), (cx + 0.7 * s, cy - 0.3 * s), (cx + 0.48 * s, cy - 0.24 * s)], fill=_c(beak))
    dr.polygon([(cx - 0.45 * s, cy - 0.05 * s), (cx - 0.85 * s, cy - 0.3 * s), (cx - 0.6 * s, cy + 0.15 * s)], fill=_c(body))
    dr.ellipse([cx + 0.26 * s, cy - 0.42 * s, cx + 0.34 * s, cy - 0.34 * s], fill=_c((0.1, 0.1, 0.1)))


def cup(dr, cx, cy, s, col):
    dr.rounded_rectangle([cx - 0.42 * s, cy - 0.25 * s, cx + 0.3 * s, cy + 0.42 * s], radius=0.18 * s, fill=_c(col))
    dr.ellipse([cx + 0.16 * s, cy - 0.12 * s, cx + 0.58 * s, cy + 0.28 * s], outline=_c(col), width=max(2, int(0.1 * s)))
    dr.rounded_rectangle([cx - 0.6 * s, cy + 0.44 * s, cx + 0.5 * s, cy + 0.54 * s], radius=0.05 * s, fill=_c(col))
    for k in (-0.18, 0.06):
        dr.arc([cx + k * s - 0.1 * s, cy - 0.75 * s, cx + k * s + 0.1 * s, cy - 0.35 * s], 100, 260, fill=_c(col), width=max(2, int(0.07 * s)))


def cloud(dr, cx, cy, s, col):
    for (x, y, r) in ((-0.42, 0.1, 0.3), (-0.08, -0.12, 0.4), (0.32, 0.05, 0.32), (0.0, 0.18, 0.3)):
        dr.ellipse([cx + (x - r) * s, cy + (y - r) * s, cx + (x + r) * s, cy + (y + r) * s], fill=_c(col))
    dr.rectangle([cx - 0.42 * s, cy + 0.1 * s, cx + 0.32 * s, cy + 0.42 * s], fill=_c(col))


def flower(dr, cx, cy, s, petal, heart):
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        x, y = cx + 0.42 * s * math.cos(a), cy + 0.42 * s * math.sin(a)
        dr.ellipse([x - 0.3 * s, y - 0.3 * s, x + 0.3 * s, y + 0.3 * s], fill=_c(petal))
    dr.ellipse([cx - 0.24 * s, cy - 0.24 * s, cx + 0.24 * s, cy + 0.24 * s], fill=_c(heart))


def book(dr, cx, cy, s, col, page):
    dr.polygon([(cx - 0.9 * s, cy - 0.45 * s), (cx, cy - 0.3 * s), (cx + 0.9 * s, cy - 0.45 * s), (cx + 0.9 * s, cy + 0.45 * s),
                (cx, cy + 0.6 * s), (cx - 0.9 * s, cy + 0.45 * s)], fill=_c(col))
    dr.polygon([(cx - 0.78 * s, cy - 0.38 * s), (cx - 0.04 * s, cy - 0.24 * s), (cx - 0.04 * s, cy + 0.46 * s), (cx - 0.78 * s, cy + 0.34 * s)], fill=_c(page))
    dr.polygon([(cx + 0.78 * s, cy - 0.38 * s), (cx + 0.04 * s, cy - 0.24 * s), (cx + 0.04 * s, cy + 0.46 * s), (cx + 0.78 * s, cy + 0.34 * s)], fill=_c(page))


# ---------------------------------------------------------------- signs
def sg_mart(dr, w, h, k):
    green, cream, yel = (0.13, 0.44, 0.31), (0.98, 0.97, 0.92), (0.98, 0.80, 0.24)
    dr.rectangle([0, int(h * 0.8), w, h], fill=_c(yel))
    r = h * 0.36
    cx = h * 0.62
    dr.ellipse([cx - r, h * 0.42 - r, cx + r, h * 0.42 + r], fill=_c(cream))
    bird(dr, cx, h * 0.45, r * 0.95, yel, (0.92, 0.45, 0.2))
    s = fit(dr, 'KOTORI MART', LATIN, int(h * 0.56), w - h * 2.6)
    text(dr, (w * 0.5 + h * 0.3, h * 0.42), 'KOTORI MART', LATIN, s, cream, spacing=int(h * 0.04))
    text(dr, (w - h * 0.75, h * 0.42), 'ことり', KANA, int(h * 0.3), yel)


def sg_cafe(dr, w, h, k):
    cream = (0.97, 0.92, 0.80)
    cloud(dr, h * 0.62, h * 0.52, h * 0.36, cream)
    s = fit(dr, 'café kumo', LATIN_SOFT, int(h * 0.62), w - h * 1.6)
    text(dr, (w * 0.5 + h * 0.35, h * 0.5), 'café kumo', LATIN_SOFT, s, cream)


def sg_disc(dr, w, h, k):
    teal, cream = (0.16, 0.36, 0.38), (0.97, 0.92, 0.80)
    dr.ellipse([0, 0, w, h], fill=_c(cream))
    dr.ellipse([w * 0.07, h * 0.07, w * 0.93, h * 0.93], fill=_c(teal))
    cup(dr, w * 0.48, h * 0.56, w * 0.3, cream)


def sg_books(dr, w, h, k):
    gold, page = (0.93, 0.79, 0.44), (0.97, 0.94, 0.86)
    book(dr, h * 0.75, h * 0.5, h * 0.42, gold, page)
    s = fit(dr, 'SHIORI BOOKS', LATIN, int(h * 0.55), w - h * 2.2)
    text(dr, (w * 0.5 + h * 0.4, h * 0.52), 'SHIORI BOOKS', LATIN, s, gold, spacing=int(h * 0.05))
    dr.rectangle([0, 0, w, int(h * 0.08)], fill=_c(gold)); dr.rectangle([0, h - int(h * 0.08), w, h], fill=_c(gold))


def sg_flower(dr, w, h, k):
    green, yel, pink = (0.22, 0.45, 0.30), (0.98, 0.80, 0.26), (0.95, 0.55, 0.62)
    for x, p in ((h * 0.7, yel), (w - h * 0.7, pink)):
        flower(dr, x, h * 0.5, h * 0.42, p, (0.98, 0.95, 0.85))
    s = fit(dr, 'mimosa flowers', LATIN_SOFT, int(h * 0.62), w - h * 2.4)
    text(dr, (w * 0.5, h * 0.5), 'mimosa flowers', LATIN_SOFT, s, green)


def sg_noodle(dr, w, h, k):
    ink = (0.16, 0.12, 0.10)
    for i in range(7):       # grain
        y = h * (0.1 + 0.13 * i)
        dr.line([(0, y), (w, y + h * 0.05 * math.sin(i))], fill=_c((0.55, 0.38, 0.23)), width=max(1, k))
    dr.ellipse([h * 0.18, h * 0.16, h * 0.86, h * 0.84], fill=_c((0.96, 0.86, 0.50)))
    text(dr, (w * 0.58, h * 0.52), 'めん処 つき', KANA, int(h * 0.56), ink)


def sg_tall(dr, w, h, k):
    red, ink = (0.80, 0.24, 0.20), (0.18, 0.20, 0.30)
    dr.rectangle([0, 0, w, int(w * 0.5)], fill=_c(red))
    dr.ellipse([w * 0.3, w * 0.1, w * 0.7, w * 0.4], fill=_c((0.98, 0.97, 0.94)))
    chars = 'ひかり歯科'
    f = int(w * 0.68)
    y = w * 0.5 + (h - w * 0.5) / (len(chars) + 0.4) * 0.7
    step = (h - w * 0.5) / (len(chars) + 0.4)
    for ch in chars:
        text(dr, (w * 0.5, y), ch, KANA, f, ink)
        y += step


def sg_konbini(dr, w, h, k):
    # the convenience store's fascia: white, a sky-blue and a leaf-green stripe, a little house-and-sun
    # mark and the name
    blue, green, ink = (0.22, 0.56, 0.84), (0.46, 0.74, 0.32), (0.16, 0.30, 0.52)
    dr.rectangle([0, int(h * 0.72), w, int(h * 0.84)], fill=_c(blue))
    dr.rectangle([0, int(h * 0.86), w, h], fill=_c(green))
    cx, cy, s = h * 0.7, h * 0.4, h * 0.3
    dr.polygon([(cx - s, cy), (cx, cy - s * 0.9), (cx + s, cy), (cx + s * 0.75, cy), (cx + s * 0.75, cy + s * 0.8),
                (cx - s * 0.75, cy + s * 0.8), (cx - s * 0.75, cy)], fill=_c(blue))
    dr.ellipse([cx - s * 0.32, cy + s * 0.05, cx + s * 0.32, cy + s * 0.69], fill=_c((0.98, 0.80, 0.26)))
    sz = fit(dr, 'KANATA 24', LATIN, int(h * 0.5), w - h * 2.2)
    text(dr, (w * 0.5 + h * 0.2, h * 0.38), 'KANATA 24', LATIN, sz, ink, spacing=int(h * 0.05))
    text(dr, (w - h * 0.85, h * 0.38), 'かなた', KANA, int(h * 0.32), green)


def sg_boutique(dr, w, h, k):
    # brass letters on a dark board: the boutique's name, a thin rule, kana under it
    gold = (0.90, 0.76, 0.46)
    sz = fit(dr, 'MINAMO', LATIN_SOFT, int(h * 0.5), w * 0.8)
    text(dr, (w * 0.5, h * 0.36), 'MINAMO', LATIN_SOFT, sz, gold, spacing=int(h * 0.12))
    dr.rectangle([w * 0.3, h * 0.64, w * 0.7, h * 0.66], fill=_c(gold))
    text(dr, (w * 0.5, h * 0.81), 'みなも', KANA, int(h * 0.22), gold)


def recycle(dr, w, h, k):
    # three bin mouths' labels: coloured bands with simple pictograms (a can, a bottle, a paper)
    cols = [(0.86, 0.30, 0.24), (0.24, 0.52, 0.80), (0.36, 0.64, 0.36)]
    for i, c in enumerate(cols):
        x0, x1 = i * w / 3 + w * 0.02, (i + 1) * w / 3 - w * 0.02
        dr.rectangle([x0, 0, x1, h], fill=_c(c))
        cx = (x0 + x1) / 2
        if i == 0:
            dr.rounded_rectangle([cx - h * 0.14, h * 0.25, cx + h * 0.14, h * 0.75], radius=h * 0.04, fill=_c((0.97, 0.97, 0.95)))
        elif i == 1:
            dr.rounded_rectangle([cx - h * 0.12, h * 0.38, cx + h * 0.12, h * 0.8], radius=h * 0.05, fill=_c((0.97, 0.97, 0.95)))
            dr.rectangle([cx - h * 0.05, h * 0.18, cx + h * 0.05, h * 0.4], fill=_c((0.97, 0.97, 0.95)))
        else:
            dr.polygon([(cx - h * 0.2, h * 0.25), (cx + h * 0.12, h * 0.25), (cx + h * 0.2, h * 0.33), (cx + h * 0.2, h * 0.78),
                        (cx - h * 0.2, h * 0.78)], fill=_c((0.97, 0.97, 0.95)))


def noren2(dr, w, h, k):
    white = (0.97, 0.95, 0.90)
    n = 4
    for i, ch in enumerate('らーめん'):
        cx = (i + 0.5) * w / n
        text(dr, (cx, h * 0.5), ch, KANA, int(h * 0.5), white)
    # a band of little waves along the hem
    for x in range(0, w, max(4, int(w / 20))):
        dr.arc([x, h * 0.8, x + w / 20, h * 0.92], 180, 360, fill=_c(white), width=max(1, k))


def poster(kind):
    def f(dr, w, h, k):
        if kind == 1:
            red = (0.86, 0.24, 0.2)
            dr.ellipse([w * 0.12, h * 0.1, w * 0.88, h * 0.1 + w * 0.76], fill=_c(red))
            dr.ellipse([w * 0.34, h * 0.22, w * 0.66, h * 0.22 + w * 0.32], fill=_c((0.98, 0.95, 0.85)))
            dr.ellipse([w * 0.42, h * 0.3, w * 0.58, h * 0.3 + w * 0.16], fill=_c(red))
            for j in range(3):
                dr.rectangle([w * 0.15, h * (0.7 + j * 0.08), w * (0.85 - 0.2 * j), h * (0.73 + j * 0.08)], fill=_c((0.3, 0.3, 0.34)))
        else:
            blue = (0.25, 0.52, 0.80)
            dr.rectangle([0, 0, w, h * 0.22], fill=_c(blue))
            dr.rounded_rectangle([w * 0.36, h * 0.3, w * 0.64, h * 0.84], radius=w * 0.08, fill=_c((0.36, 0.72, 0.52)))
            dr.rectangle([w * 0.44, h * 0.26, w * 0.56, h * 0.32], fill=_c((0.94, 0.94, 0.94)))
            dr.rectangle([w * 0.36, h * 0.5, w * 0.64, h * 0.62], fill=_c((0.98, 0.98, 0.96)))
            dr.ellipse([w * 0.08, h * 0.62, w * 0.34, h * 0.62 + w * 0.26], fill=_c((0.98, 0.80, 0.25)))
    return f


def books_tile(dr, w, h, k):
    rng = np.random.default_rng(12)
    cols = [(0.78, 0.28, 0.24), (0.24, 0.42, 0.64), (0.92, 0.78, 0.38), (0.30, 0.54, 0.38), (0.94, 0.92, 0.86), (0.48, 0.32, 0.50), (0.88, 0.52, 0.30)]
    x = 0
    while x < w:
        bw = rng.uniform(0.035, 0.07) * w
        bh = rng.uniform(0.55, 0.95) * h
        c = cols[int(rng.integers(0, len(cols)))]
        dr.rectangle([x, h - bh, x + bw - k, h], fill=_c(c))
        dr.rectangle([x + bw * 0.2, h - bh + bh * 0.15, x + bw * 0.8 - k, h - bh + bh * 0.2], fill=_c((0.95, 0.9, 0.7)))
        x += bw


def lattice(dr, w, h, k):
    # a timber lattice front (kōshi) with paper behind: thin vertical bars, a few rails
    paper, wood = (0.93, 0.88, 0.76), (0.46, 0.31, 0.20)
    dr.rectangle([0, 0, w, h], fill=_c(paper))
    n = 12
    for i in range(n + 1):
        x = i * w / n
        dr.rectangle([x - w / n * 0.22, 0, x + w / n * 0.22, h], fill=_c(wood))
    for y in (0.0, 0.33, 0.66, 1.0):
        dr.rectangle([0, y * h - h * 0.025, w, y * h + h * 0.025], fill=_c(wood))


# ---------------------------------------------------------------- interiors through glass (numpy)
def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def _blend(img, mask, col, a=1.0):
    m = (np.clip(mask, 0, 1) * a)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def _box(U, V, x0, x1, y0, y1, soft=0.004):
    return _ss(-soft, soft, U - x0) * _ss(-soft, soft, x1 - U) * _ss(-soft, soft, V - y0) * _ss(-soft, soft, y1 - V)


def interior(kind):
    rng = np.random.default_rng({'mart': 3, 'cafe': 5, 'books': 7, 'flower': 9, 'konbini': 11, 'boutique': 13}[kind])

    def f(U, V, w, h):
        V2 = np.clip(V, 0, 1)
        if kind in ('mart', 'konbini'):
            sub = np.ones(U.shape + (3,), np.float32) * np.array((0.80, 0.83, 0.84) if kind == 'mart' else (0.90, 0.92, 0.92))
            sub = _blend(sub, _box(U, V, -1, 2, 0.9, 2), (0.95, 0.96, 0.95))                 # ceiling
            for y in (0.95,):
                for x in np.arange(0.05, 1.0, 0.3):
                    sub = _blend(sub, _box(U, V, x, x + 0.2, 0.93, 0.96), (1.0, 1.0, 0.96))    # strip lights
            rows = (0.06, 0.24, 0.42, 0.6) if kind == 'mart' else (0.3, 0.46, 0.62)
            for k, y in enumerate(rows):
                x = 0.0
                while x < 1.0:
                    bw = rng.uniform(0.02, 0.045); bh = rng.uniform(0.06, 0.11)
                    c = np.array([(0.88, 0.30, 0.25), (0.96, 0.78, 0.25), (0.30, 0.55, 0.80), (0.40, 0.70, 0.40), (0.95, 0.95, 0.92),
                                  (0.95, 0.55, 0.25), (0.70, 0.40, 0.70), (0.92, 0.92, 0.90)][int(rng.integers(0, 8))])
                    c = c * 0.7 + 0.3 * np.array((0.82, 0.83, 0.84))
                    sub = _blend(sub, _box(U, V, x, x + bw - 0.006, y + 0.02, y + 0.02 + bh), c)
                    x += bw
                sub = _blend(sub, _box(U, V, -1, 2, y, y + 0.02), (0.66, 0.68, 0.70))       # shelf edge
            if kind == 'konbini':       # magazines along the window, a counter and a coffee machine
                x = 0.0
                while x < 1.0:
                    bw = rng.uniform(0.05, 0.08)
                    c = [(0.92, 0.40, 0.45), (0.30, 0.55, 0.85), (0.98, 0.85, 0.30), (0.95, 0.95, 0.95), (0.40, 0.75, 0.55)][int(rng.integers(0, 5))]
                    sub = _blend(sub, _box(U, V, x, x + bw - 0.01, 0.02, 0.2 + rng.uniform(-0.02, 0.02)), c)
                    sub = _blend(sub, _box(U, V, x + 0.008, x + bw - 0.018, 0.12, 0.16), (0.2, 0.2, 0.25), 0.6)
                    x += bw
            if kind == 'mart':
                sub = _blend(sub, _box(U, V, 0.62, 0.92, 0.76, 0.86), (0.98, 0.84, 0.30))      # a hanging sale card
                sub = _blend(sub, _box(U, V, 0.68, 0.86, 0.78, 0.84), (0.86, 0.28, 0.22))
        elif kind == 'cafe':
            sub = (np.array((0.36, 0.25, 0.18)) + np.array((0.22, 0.16, 0.10)) * V2[..., None]).astype(np.float32)
            sub = _blend(sub, _box(U, V, 0.08, 0.5, 0.42, 0.7), (0.14, 0.16, 0.15))              # menu board
            for j in range(4):
                sub = _blend(sub, _box(U, V, 0.12, 0.12 + rng.uniform(0.18, 0.32), 0.62 - j * 0.05, 0.635 - j * 0.05), (0.86, 0.86, 0.80), 0.8)
            sub = _blend(sub, _box(U, V, -1, 2, 0.0, 0.3), (0.42, 0.28, 0.18))                   # counter
            sub = _blend(sub, _box(U, V, -1, 2, 0.28, 0.32), (0.70, 0.55, 0.40))
            for x in (0.25, 0.55, 0.82):
                sub = _blend(sub, _box(U, V, x - 0.004, x + 0.004, 0.78, 1.1), (0.15, 0.12, 0.1))
                d = np.sqrt(((U - x) / 0.09) ** 2 + ((V - 0.76) / 0.05) ** 2)
                sub = _blend(sub, (d < 1) * (V > 0.74), (0.98, 0.84, 0.52))
                g = np.exp(-(((U - x) / 0.16) ** 2 + ((V - 0.7) / 0.12) ** 2))
                sub = _blend(sub, g, (0.95, 0.74, 0.46), 0.35)
            for x in (0.62, 0.7, 0.78):                                                           # cups on the counter
                sub = _blend(sub, _box(U, V, x, x + 0.04, 0.32, 0.37), (0.95, 0.94, 0.9))
            sub = _blend(sub, np.sqrt(((U - 0.92) / 0.08) ** 2 + ((V - 0.48) / 0.14) ** 2) < 1, (0.30, 0.48, 0.28))   # a plant
        elif kind == 'books':
            sub = (np.array((0.30, 0.22, 0.16)) + np.array((0.16, 0.12, 0.08)) * V2[..., None]).astype(np.float32)
            for y0 in (0.04, 0.27, 0.5, 0.73):
                x = 0.02
                while x < 0.98:
                    bw = rng.uniform(0.018, 0.04); bh = rng.uniform(0.12, 0.19)
                    c = [(0.74, 0.26, 0.22), (0.24, 0.40, 0.62), (0.90, 0.76, 0.38), (0.28, 0.50, 0.36), (0.92, 0.90, 0.84),
                         (0.46, 0.30, 0.48), (0.84, 0.50, 0.28)][int(rng.integers(0, 7))]
                    if rng.random() < 0.08:
                        x += bw; continue
                    sub = _blend(sub, _box(U, V, x, x + bw - 0.004, y0 + 0.02, y0 + 0.02 + bh), c)
                    x += bw
                sub = _blend(sub, _box(U, V, -1, 2, y0, y0 + 0.022), (0.52, 0.36, 0.24))
            g = np.exp(-(((U - 0.5) / 0.4) ** 2 + ((V - 0.9) / 0.2) ** 2))
            sub = _blend(sub, g, (0.98, 0.86, 0.6), 0.25)
        elif kind == 'boutique':
            sub = (np.array((0.62, 0.56, 0.50)) + np.array((0.22, 0.20, 0.16)) * V2[..., None]).astype(np.float32)
            sub = _blend(sub, _box(U, V, -1, 2, 0.0, 0.08), (0.46, 0.36, 0.28))                  # floor
            sub = _blend(sub, _box(U, V, 0.05, 0.95, 0.74, 0.755), (0.3, 0.3, 0.32))              # the rail
            x = 0.08
            while x < 0.92:                                                                     # garments on hangers
                bw = rng.uniform(0.05, 0.09); bh = rng.uniform(0.25, 0.42)
                c = [(0.92, 0.90, 0.86), (0.30, 0.36, 0.52), (0.84, 0.56, 0.50), (0.56, 0.64, 0.50), (0.20, 0.20, 0.22),
                     (0.95, 0.82, 0.55)][int(rng.integers(0, 6))]
                sub = _blend(sub, _box(U, V, x, x + bw - 0.012, 0.74 - bh, 0.73), c)
                x += bw
            for cx in (0.22, 0.74):                                                             # two figures
                sub = _blend(sub, np.sqrt(((U - cx) / 0.04) ** 2 + ((V - 0.5) / 0.05) ** 2) < 1, (0.9, 0.88, 0.84))
                sub = _blend(sub, _box(U, V, cx - 0.07, cx + 0.07, 0.12, 0.45), [(0.84, 0.36, 0.30), (0.26, 0.32, 0.46)][int(cx > 0.5)])
            g = np.exp(-(((U - 0.5) / 0.5) ** 2 + ((V - 0.95) / 0.2) ** 2))
            sub = _blend(sub, g, (1.0, 0.94, 0.8), 0.3)
        else:   # flower
            sub = (np.array((0.42, 0.46, 0.40)) + np.array((0.20, 0.20, 0.18)) * V2[..., None]).astype(np.float32)
            for k in range(26):
                cx, cy = rng.uniform(0, 1), rng.uniform(0.05, 0.7); r = rng.uniform(0.06, 0.13)
                c = [(0.30, 0.50, 0.28), (0.40, 0.60, 0.32), (0.24, 0.42, 0.26)][k % 3]
                sub = _blend(sub, np.sqrt(((U - cx) / r) ** 2 + ((V - cy) / (r * 0.8)) ** 2) < 1, c)
            for k in range(60):
                cx, cy = rng.uniform(0, 1), rng.uniform(0.1, 0.72); r = rng.uniform(0.015, 0.03)
                c = [(0.96, 0.56, 0.64), (0.98, 0.84, 0.36), (0.97, 0.96, 0.92), (0.80, 0.35, 0.45), (0.74, 0.58, 0.88)][k % 5]
                sub = _blend(sub, np.sqrt(((U - cx) / r) ** 2 + ((V - cy) / r) ** 2) < 1, c)
            for x in np.arange(0.05, 1.0, 0.18):                                                  # buckets
                sub = _blend(sub, _box(U, V, x, x + 0.13, 0.0, 0.12), (0.66, 0.68, 0.70))
        # seen through glass: a little darker and bluer, the sky's reflection high up, two streaks
        sub = sub * 0.82 + np.array((0.02, 0.04, 0.07))
        sub = _blend(sub, _ss(0.75, 1.05, V), (0.62, 0.70, 0.80), 0.35)
        d = U * 0.75 + V
        sub = _blend(sub, _ss(0.16, 0.0, np.abs(d - 0.95)), (0.80, 0.86, 0.92), 0.30)
        sub = _blend(sub, _ss(0.045, 0.0, np.abs(d - 1.27)), (0.90, 0.93, 0.96), 0.45)
        edge = np.minimum(np.minimum(U, 1 - U) * 1.4, 1 - V)
        sub = sub * (1 - 0.35 * _ss(0.06, 0.0, edge))[..., None]
        return sub
    return f


def paint(img, put):
    """put(img, name, fn) paints a numpy tile (kit_buildings_atlas.put)."""
    for kind in ('mart', 'cafe', 'books', 'flower', 'konbini', 'boutique'):
        if 'gl_' + kind in REG: put(img, 'gl_' + kind, interior(kind))
    put_pil(img, 'sg_mart', sg_mart, (0.13, 0.44, 0.31))
    put_pil(img, 'sg_cafe', sg_cafe, (0.17, 0.25, 0.27))
    put_pil(img, 'sg_disc', sg_disc, (0.97, 0.92, 0.80))
    put_pil(img, 'sg_books', sg_books, (0.13, 0.31, 0.25))
    put_pil(img, 'sg_flower', sg_flower, (0.97, 0.95, 0.88))
    put_pil(img, 'sg_noodle', sg_noodle, (0.66, 0.48, 0.30))
    put_pil(img, 'sg_tall', sg_tall, (0.97, 0.96, 0.93))
    put_pil(img, 'noren2', noren2, (0.66, 0.20, 0.18))
    put_pil(img, 'poster1', poster(1), (0.99, 0.90, 0.40))
    put_pil(img, 'poster2', poster(2), (0.92, 0.95, 0.98))
    put_pil(img, 'books', books_tile, (0.36, 0.26, 0.18))
    put_pil(img, 'lattice', lattice, (0.93, 0.88, 0.76))
    put_pil(img, 'sg_konbini', sg_konbini, (0.98, 0.98, 0.97))
    put_pil(img, 'recycle', recycle, (0.9, 0.9, 0.9))
    put_pil(img, 'sg_boutique', sg_boutique, (0.12, 0.13, 0.15))
