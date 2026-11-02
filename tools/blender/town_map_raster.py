# 2D painting helpers for the town map's ground (numpy + PIL only): a canvas that holds the ground colour at SS x the
# picture's resolution, shapes drawn into small anti-aliased masks and composited into it, smooth noise for texture, and
# the binary morphology (round a mask's corners with a disc) that gives the blocks their rounded kerb corners.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

IMG_W, IMG_H = 3200, 1800
ORIGIN = (400, 225)             # the core's top-left in the picture


def srgb(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ noise
def smooth_noise(h, w, cell, seed, octaves=1):
    """Smooth value noise in [-1, 1]: random values on a grid of `cell` px, resized bicubically (summed over octaves)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2.0, cell / (2 ** o))
        gh, gw = int(h / c) + 3, int(w / c) + 3
        g = rng.random((gh, gw), dtype=np.float32) * 2 - 1
        im = Image.fromarray(g).resize((int(gw * c), int(gh * c)), Image.BICUBIC)
        a = np.asarray(im, np.float32)[:h, :w]
        out += a * amp
        tot += amp
        amp *= 0.5
    return out / tot


# ------------------------------------------------------------------ morphology on boolean masks
def _hdilate(m, hw):
    """Dilate a boolean mask horizontally by hw cells each way (via cumulative sums)."""
    if hw <= 0:
        return m
    c = np.cumsum(m, axis=1, dtype=np.int32)
    c = np.concatenate([np.zeros((m.shape[0], 1), np.int32), c], axis=1)      # c[:, k] = sum of the first k columns
    w = m.shape[1]
    hi = np.minimum(np.arange(w) + hw + 1, w)
    lo = np.maximum(np.arange(w) - hw, 0)
    return (c[:, hi] - c[:, lo]) > 0


def dilate_disc(m, r):
    """Dilate a boolean mask by a disc of radius r (cells)."""
    if r <= 0:
        return m.copy()
    out = np.zeros_like(m)
    cache = {}
    h = m.shape[0]
    for dy in range(-r, r + 1):
        hw = int(math.sqrt(r * r - dy * dy))
        if hw not in cache:
            cache[hw] = _hdilate(m, hw)
        d = cache[hw]
        if dy > 0:
            out[dy:] |= d[:h - dy]
        elif dy < 0:
            out[:h + dy] |= d[-dy:]
        else:
            out |= d
    return out


def erode_disc(m, r):
    return ~dilate_disc(~m, r)


def close_disc(m, r):
    """Morphological closing with a disc: concave corners of the mask get a fillet of radius r."""
    return erode_disc(dilate_disc(m, r), r)


def open_disc(m, r):
    return dilate_disc(erode_disc(m, r), r)


# ------------------------------------------------------------------ the canvas
class Canvas:
    """The ground's albedo, SS x the picture's size, float32 RGB in sRGB 0..1. Shapes are given in CORE coordinates."""

    def __init__(self, ss=2):
        self.ss = ss
        self.W, self.H = IMG_W * ss, IMG_H * ss
        self.px = np.zeros((self.H, self.W, 3), np.float32)
        self._noise = {}

    # coordinates
    def C(self, p):
        return ((p[0] + ORIGIN[0]) * self.ss, (p[1] + ORIGIN[1]) * self.ss)

    def noise(self, cell, seed=1, octaves=1):
        """A canvas-sized noise field (cached)."""
        k = (cell, seed, octaves)
        if k not in self._noise:
            self._noise[k] = smooth_noise(self.H, self.W, cell * self.ss, seed, octaves)
        return self._noise[k]

    # masks (anti-aliased by drawing at 2x and reducing)
    def poly_mask(self, pts, blur=0.0):
        xs = [self.C(p)[0] for p in pts]; ys = [self.C(p)[1] for p in pts]
        x0, y0 = max(0, int(min(xs)) - 3), max(0, int(min(ys)) - 3)
        x1, y1 = min(self.W, int(max(xs)) + 4), min(self.H, int(max(ys)) + 4)
        if x1 <= x0 or y1 <= y0:
            return None
        k = 2
        im = Image.new('L', ((x1 - x0) * k, (y1 - y0) * k), 0)
        ImageDraw.Draw(im).polygon([((self.C(p)[0] - x0) * k, (self.C(p)[1] - y0) * k) for p in pts], fill=255)
        im = im.reduce(k)
        if blur > 0:
            im = im.filter(ImageFilter.GaussianBlur(blur * self.ss))
        return x0, y0, np.asarray(im, np.float32) / 255.0

    def line_mask(self, pts, width, cap=True):
        """A thick polyline (width in core px) with round joints and caps."""
        cp = [self.C(p) for p in pts]
        w = width * self.ss
        xs = [p[0] for p in cp]; ys = [p[1] for p in cp]
        x0, y0 = max(0, int(min(xs) - w) - 3), max(0, int(min(ys) - w) - 3)
        x1, y1 = min(self.W, int(max(xs) + w) + 4), min(self.H, int(max(ys) + w) + 4)
        if x1 <= x0 or y1 <= y0:
            return None
        k = 2
        im = Image.new('L', ((x1 - x0) * k, (y1 - y0) * k), 0)
        d = ImageDraw.Draw(im)
        q = [((p[0] - x0) * k, (p[1] - y0) * k) for p in cp]
        d.line(q, fill=255, width=max(1, int(round(w * k))), joint='curve')
        if cap:
            r = w * k / 2
            for p in (q[0], q[-1]):
                d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
        im = im.reduce(k)
        return x0, y0, np.asarray(im, np.float32) / 255.0

    def disc_mask(self, c, r):
        return self.poly_mask([(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in [i * math.pi / 24 for i in range(48)]])

    def rect_mask(self, c, w, h, angle=0.0, r=0.0):
        """A rectangle (core px) centred on c, turned by angle degrees (counter-clockwise on screen), optional corner radius."""
        pts = rect_pts(c, w, h, angle)
        return self.poly_mask(pts)

    # compositing
    def blend(self, m, color, alpha=1.0):
        """Paint colour (3 values, or an array shaped like the mask + 3) where the mask is, with opacity alpha."""
        if m is None:
            return
        x0, y0, a = m
        h, w = a.shape
        reg = self.px[y0:y0 + h, x0:x0 + w]
        a = a[:reg.shape[0], :reg.shape[1]] * alpha
        col = np.asarray(color, np.float32)
        if col.ndim == 3:
            col = col[:reg.shape[0], :reg.shape[1]]
            reg[...] = reg * (1 - a[..., None]) + col * a[..., None]
        else:
            reg[...] = reg * (1 - a[..., None]) + col[None, None, :] * a[..., None]

    def blend_full(self, a, color, alpha=1.0):
        """Same, with a full-canvas mask array (0..1)."""
        self.blend((0, 0, a), color, alpha)

    def textured(self, m, base, amp=(0.05, 0.03, 0.02), cells=(160, 40, 9), seed=3, tint=None):
        """A colour array for a mask: the base colour modulated by noise at three scales (brightness, plus a little hue drift)."""
        x0, y0, a = m
        h, w = a.shape
        n = np.zeros((h, w), np.float32)
        for k, (am, cell) in enumerate(zip(amp, cells)):
            n += am * self.noise(cell, seed + k)[y0:y0 + h, x0:x0 + w]
        col = np.asarray(base, np.float32)[None, None, :] * (1 + n[..., None])
        if tint is not None:
            t = self.noise(cells[0] * 1.7, seed + 11)[y0:y0 + h, x0:x0 + w]
            col = col + np.asarray(tint, np.float32)[None, None, :] * t[..., None]
        return np.clip(col, 0, 1)

    def save(self, path):
        Image.fromarray((np.clip(self.px, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def rect_pts(c, w, h, angle=0.0):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        # counter-clockwise on screen (y down): rotate by -angle
        out.append((c[0] + dx * ca + dy * sa, c[1] - dx * sa + dy * ca))
    return out
