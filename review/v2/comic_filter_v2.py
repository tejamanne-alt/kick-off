"""Comic look v2, matched to the reference sheets: 1 flat colour, 2 light as dots, 3 ink line,
4 slip + paper. Each stage is a screen-space step the PostFX pass can do (the ink line in game
comes from depth and normals, not from the picture)."""
import numpy as np
from PIL import Image, ImageFilter

INDIGO = np.array([0.16, 0.10, 0.36])
INK = np.array([0.08, 0.05, 0.16])
CREAM = np.array([0.97, 0.93, 0.84])


def arr(im):
    return np.asarray(im.convert("RGB")).astype(np.float32) / 255


def img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def lum(c):
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def sobel(L):
    p = np.pad(L, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return np.hypot(gx, gy)


def screen(h, w, period, angle_deg):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.radians(angle_deg)
    u = (xx * np.cos(a) + yy * np.sin(a)) / period
    v = (-xx * np.sin(a) + yy * np.cos(a)) / period
    return np.hypot(u - np.round(u), v - np.round(v))      # 0 centre .. 0.707 corner


def dots(d, cover, period):
    rad = np.sqrt(np.clip(cover, 0, 1)) * 0.62
    return np.clip((rad - d) * period * 0.8 + 0.5, 0, 1) * (cover > 0.02)


RAMP_L = np.array([0.0, 0.28, 0.45, 0.6, 0.76, 0.9, 1.0])
RAMP_C = np.array([[0.10, 0.06, 0.26], [0.30, 0.20, 0.58], [0.62, 0.36, 0.62],
                   [0.95, 0.56, 0.44], [0.99, 0.78, 0.50], [0.99, 0.92, 0.76], [1.0, 0.97, 0.90]])


def ramp(L):
    return np.stack([np.interp(L, RAMP_L, RAMP_C[:, i]) for i in range(3)], -1)


def flat_colour(im):
    """Stage 1: texture smoothed away, then a comic palette: quiet greys mapped onto a
    purple-lavender-peach-cream ramp (shade purple, light warm), strong colours kept and
    pushed, luminance stepped into three bands with the hue kept."""
    small = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    small = small.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.ModeFilter(5))
    smooth = arr(small.resize(im.size, Image.BICUBIC))
    L = lum(smooth)
    sat = smooth.max(-1) - smooth.min(-1)
    Lg = np.clip((L - 0.5) * 1.2 + 0.56, 0, 1)
    vivid = Lg[..., None] + (smooth - L[..., None]) * 1.8
    vivid = np.clip(vivid * (Lg / np.maximum(L, 1e-3))[..., None] ** 0.5, 0, 1)
    w = (1 - sstep(0.06, 0.28, sat))[..., None] * 0.8
    c = vivid * (1 - w) + ramp(Lg) * w
    Lc = lum(c)
    # bands follow the light, not the texture: chosen from a blurred luminance
    Lb = np.asarray(Image.fromarray((Lc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    Lc = Lb * 0.75 + Lc * 0.25
    band = np.where(Lc < 0.3, 0.26, np.where(Lc < 0.62, 0.55, 0.86))[..., None]
    flat = np.clip(c * (band / np.maximum(Lc[..., None], 1e-3)), 0, 1)
    return flat, Lc, band[..., 0], smooth


def light_as_dots(flat, Lc, band, period=8.0):
    """Stage 2: the light between the bands drawn as dots: dark dots where a band falls toward
    the one below, cream dots on the brightest highlights, fine hatching in deep shade."""
    h, w, _ = flat.shape
    lo = np.where(band < 0.3, 0.0, np.where(band < 0.6, 0.3, 0.6))
    hi_ = np.where(band < 0.3, 0.3, np.where(band < 0.6, 0.6, 1.0))
    t = (Lc - lo) / (hi_ - lo)                                   # 0 bottom of band .. 1 top
    cover = np.clip(0.55 - t, 0, 1) * 0.9
    d = screen(h, w, period, 45)
    m = dots(d, cover, period)[..., None]
    dark = flat * 0.42 * np.array([0.8, 0.7, 1.15])
    out = flat * (1 - m) + np.clip(dark, 0, 1) * m
    lt = dots(screen(h, w, period * 0.8, 15), np.clip((Lc - 0.86) / 0.1, 0, 1) * 0.5, period * 0.8)[..., None]
    out = out * (1 - lt) + 1.0 * lt
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hatch = (np.sin((xx * 0.8 - yy) * np.pi / 3.2) > 0.55).astype(np.float32)
    deep = (np.clip((0.2 - Lc) / 0.12, 0, 1) * hatch)[..., None]
    return out * (1 - deep * 0.55) + INK * deep * 0.55


def ink_line(c, smooth, flat, width=3):
    """Stage 3: a thick ink line on the outlines and on the edges of the shade bands."""
    e = sobel(lum(smooth)) + 0.6 * sobel(lum(flat))
    line = np.clip((e - 0.2) / 0.16, 0, 1)
    li = Image.fromarray((line * 255).astype(np.uint8))
    if width >= 3:
        li = li.filter(ImageFilter.MaxFilter(3))
    li = li.filter(ImageFilter.GaussianBlur(0.7))
    line = np.asarray(li).astype(np.float32)[..., None] / 255
    return c * (1 - line) + INK * line


def slip_and_paper(c, base_slip=2.5, edge_slip=6.0, seed=7):
    """Stage 4: the colour plates printed a little out of register, on grainy paper."""
    h, w, _ = c.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.clip(np.hypot((xx - w * 0.5) / (w * 0.5), (yy - h * 0.55) / (h * 0.6)) - 0.3, 0, 1)
    k = base_slip + edge_slip * r
    yi = yy.astype(int)
    out = c.copy()
    out[..., 0] = c[yi, np.clip(xx + k, 0, w - 1).astype(int), 0]
    out[..., 2] = c[np.clip(yy + k * 0.4, 0, h - 1).astype(int), np.clip(xx - k, 0, w - 1).astype(int), 2]
    rng = np.random.default_rng(seed)
    blot = np.asarray(Image.fromarray((rng.random((h // 24 + 1, w // 24 + 1)) * 255).astype(np.uint8))
                      .resize((w, h), Image.BICUBIC)).astype(np.float32)[..., None] / 255
    fibre = np.asarray(Image.fromarray((rng.random((h, w // 3 + 1)) * 255).astype(np.uint8))
                       .resize((w, h), Image.BILINEAR)).astype(np.float32)[..., None] / 255
    grain = rng.standard_normal((h, w, 1)).astype(np.float32)
    out = out * (0.93 + blot * 0.06) + (fibre - 0.5) * 0.035 + grain * 0.022
    out = out * 0.95 + np.array([0.04, 0.03, 0.015])
    vig = 1 - 0.18 * np.clip(np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) - 0.6, 0, 1)[..., None]
    return np.clip(out * vig, 0, 1)


def comic(im, stages=False, period=8.0):
    flat, Lc, band, smooth = flat_colour(im)
    s2 = light_as_dots(flat, Lc, band, period)
    s3 = ink_line(s2, smooth, flat)
    s4 = slip_and_paper(s3)
    if stages:
        return [img(flat), img(s2), img(s3), img(s4)]
    return img(s4)
