"""Prototype of the 'comic halftone' filter, written the way the PostFX pass would do it:
every step is a per-pixel screen-space operation (plus a 3x3 edge kernel), so the
Unity shader can do the same. Usage: comic_filter.py in.jpg out.png [crop x0,y0,x1,y1]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

W = 1920  # work at the game's reference resolution


def load(path, crop=None):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    h = round(im.height * W / im.width)
    return im.resize((W, h), Image.LANCZOS)


def lum(c):
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def sobel(L):
    p = np.pad(L, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return np.hypot(gx, gy)


def comic(im, dot_period=9.0, offset_px=7.0):
    src = np.asarray(im).astype(np.float32) / 255
    h, w, _ = src.shape

    # 1. Flat colour: smooth away texture noise, then a punchier grade.
    flat = np.asarray(im.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.ModeFilter(5))).astype(np.float32) / 255
    L = lum(flat)[..., None]
    c = L + (flat - L) * 1.45                      # saturation
    c = np.clip((c - 0.5) * 1.18 + 0.5, 0, 1)      # contrast

    # 2. Cel bands: luminance stepped into 4 tones, hue kept.
    L = lum(c)[..., None]
    bands = np.array([0.0, 0.32, 0.55, 0.78, 1.0])
    Lq = np.interp(L, bands[:-1] + 0.12, bands[1:] - 0.06)
    Lq = np.clip(np.round(Lq * 4) / 4 * 0.7 + L * 0.3, 0, 1)
    c = np.clip(c * (Lq / np.maximum(L, 1e-3)), 0, 1)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    Ls = lum(c)

    # 3. Halftone: a 45-degree Ben-Day dot screen in the mid-tones and shade; dots in a
    #    darker, more saturated version of the local colour (the printed-ink look).
    u = (xx + yy) / (dot_period * 1.4142)
    v = (xx - yy) / (dot_period * 1.4142)
    d = np.hypot(u - np.round(u), v - np.round(v))           # 0 at dot centre, ~0.7 at corner
    cover = np.clip((0.66 - Ls) / 0.5, 0, 1) * 0.6           # dot radius from darkness
    dots = np.clip((cover - d) * dot_period * 0.9 + 0.5, 0, 1)[..., None]
    ink_col = c * 0.55 * np.array([0.85, 0.8, 1.0])
    c = c * (1 - dots) + ink_col * dots

    # 4. Hatching in the deepest shadow.
    hatch = (np.sin((xx - yy) * np.pi / 4.0) > 0.35).astype(np.float32)
    deep = np.clip((0.28 - Ls) / 0.15, 0, 1)[..., None] * hatch[..., None]
    c = c * (1 - deep * 0.6)

    # 5. Ink lines from the flat image's edges (in game: depth + normal edges too).
    e = sobel(lum(flat))
    line = np.clip((e - 0.3) / 0.2, 0, 1)
    line = np.asarray(Image.fromarray((line * 255).astype(np.uint8)).filter(ImageFilter.SMOOTH)).astype(np.float32) / 255
    ink = np.array([0.06, 0.05, 0.12])
    c = c * (1 - line[..., None]) + ink * line[..., None]

    # 6. Print misregistration: red and blue plates pulled apart, none at the centre of the
    #    frame (where the kid runs), growing toward the edges.
    r = np.clip(np.hypot((xx - w * 0.5) / (w * 0.5), (yy - h * 0.55) / (h * 0.55)) - 0.35, 0, 1)
    k = (r * offset_px).astype(np.float32)
    xi = np.clip(xx + k, 0, w - 1).astype(int)
    xo = np.clip(xx - k, 0, w - 1).astype(int)
    yi = yy.astype(int)
    out = c.copy()
    out[..., 0] = c[yi, xi, 0]
    out[..., 2] = c[yi, xo, 2]

    # 7. Paper: warm-white stock and a faint grain.
    rng = np.random.default_rng(3)
    out = out * 0.96 + np.array([0.035, 0.03, 0.02])
    out += (rng.standard_normal((h, w, 1)) * 0.012)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    crop = tuple(int(v) for v in sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    im = load(sys.argv[1], crop)
    im.save(sys.argv[2].replace(".png", "_before.png"))
    comic(im).save(sys.argv[2])
