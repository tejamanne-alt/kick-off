# LeisureAtlas.png for kit_leisure.py: shared surface tiles (wood grain, bark, stone, canvas, rope,
# the fountain grate, pond water, shingles, sand, the target rings, flag cloth, the trampoline mat,
# glass, lily pads, chain, bricks, towel terry, bucket ribs, deck slats) plus, per model that has
# painted ('grime') faces, three projected wear maps (front x-z, side y-z, top x-y) holding sun-faded
# mottling, dirt rising from the ground, splashes, rain streaks, chipped paint and painted seams.
# Tiles are colour multipliers around white (the vertex colour carries the hue), so a recolour keeps
# them. The atlas is 2048 x 1024 (the kit needs no more); its plain white corner sits at UV (0.97, 0.03).
import math
import numpy as np
from PIL import Image
from kit_leisure_geo import TILES, sstep as ss

ATW, ATH = 2048, 1024
AT = ATW
PAD = 4
CORNER = 128          # white corner tile (bottom right)


def noise(h, w, cells, rng):
    cx, cy = max(2, int(cells[0])), max(2, int(cells[1]))
    small = (rng.random((cy, cx)) * 255).astype(np.uint8)
    im = Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def grey(v, tint=(1.0, 1.0, 1.0)):
    return np.asarray(v, np.float32)[..., None] * np.array(tint, np.float32)[None, None, :]


def specks(img, mask, rng, count, rmin, rmax, col, alpha=0.8, aspect=1.0, wobble=0.0):
    h, w = mask.shape
    ys = rng.integers(0, h, count); xs = rng.integers(0, w, count)
    keep = rng.random(count) < np.clip(mask[ys, xs], 0, 1) ** 1.2
    for y, x in zip(ys[keep], xs[keep]):
        r = rng.uniform(rmin, rmax); rv = max(r * aspect, 0.5)
        y0, y1 = max(0, int(y - rv - 2)), min(h, int(y + rv + 3)); x0, x1 = max(0, int(x - r - 2)), min(w, int(x + r + 3))
        if y1 <= y0 or x1 <= x0: continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt(((yy - y) * r / rv) ** 2 + (xx - x) ** 2)
        if wobble:
            ang = np.arctan2(yy - y, xx - x)
            d = d * (1 + wobble * np.sin(ang * 3 + rng.uniform(0, 6)))
        m = np.clip(r + 0.5 - d, 0, 1) * alpha
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m[..., None]) + np.array(col)[None, None] * m[..., None]


def seglines(a, b, polylines, w, soft, k0=0.55):
    k = np.ones(a.shape, np.float32)
    for pl in polylines:
        for (a0, b0), (a1, b1) in zip(pl[:-1], pl[1:]):
            da, db = a1 - a0, b1 - b0
            L2 = max(da * da + db * db, 1e-9)
            tt = np.clip(((a - a0) * da + (b - b0) * db) / L2, 0, 1)
            d = np.sqrt((a - (a0 + tt * da)) ** 2 + (b - (b0 + tt * db)) ** 2)
            k = np.minimum(k, k0 + (1 - k0) * ss(w, w + soft, d))
    return k


# ---------------------------------------------------------------- layout
class Layout:
    def __init__(self, models):
        items = [(n, w, h) for n, w, h in TILES]
        self.maps = {}
        for M in models:
            if not M.uses_grime(): continue
            ext = M.map_extents()
            big = max(max(e[1] - e[0], e[3] - e[2]) for e in ext.values())
            ppm = M.ppm or min(220.0, max(30.0, 165.0 / big))
            for k, (a0, a1, b0, b1) in ext.items():
                nm = M.name + '.' + k
                items.append((nm, int(math.ceil((a1 - a0) * ppm)) + 1, int(math.ceil((b1 - b0) * ppm)) + 1))
                self.maps[nm] = (M, k, (a0, a1, b0, b1))
        items.sort(key=lambda it: -it[2])
        self.reg = {}
        x = 0; y = 0; rowh = 0
        for name, w, h in items:
            ww, hh = w + 2 * PAD, h + 2 * PAD
            limit = ATW if y + max(rowh, hh) < ATH - CORNER - 2 * PAD else ATW - CORNER - 2 * PAD
            if x + ww > limit:
                y += rowh; x = 0; rowh = 0
                limit = ATW if y + hh < ATH - CORNER - 2 * PAD else ATW - CORNER - 2 * PAD
            if y + hh > ATH: raise RuntimeError('atlas full at ' + name)
            self.reg[name] = (x + PAD, y + PAD, w, h)
            x += ww; rowh = max(rowh, hh)
        self.used = y + rowh
        self.reg['white'] = (ATW - CORNER, ATH - CORNER, CORNER, CORNER)

    def tile_uv(self, name, st):
        x0, y0, w, h = self.reg[name]
        s = min(max(st[0], 0.0), 1.0); t = min(max(st[1], 0.0), 1.0)
        return ((x0 + 0.5 + s * (w - 1)) / ATW, 1.0 - (y0 + 0.5 + (1 - t) * (h - 1)) / ATH)


def grid_st(w, h):
    s = (np.arange(w) + 0.5) / w; t = 1 - (np.arange(h) + 0.5) / h
    return np.meshgrid(s, t)


# ---------------------------------------------------------------- tiles
def t_grain(w, h, rng):
    U, V = grid_st(w, h)
    warp = (noise(h, w, (5, 3), rng) - 0.5) * 0.35
    g = 0.5 + 0.5 * np.sin(2 * math.pi * (V * 6.5 + warp + 0.12 * np.sin(U * 9 + V * 3)))
    fine = 0.5 + 0.5 * np.sin(2 * math.pi * (V * 23 + warp * 2.5))
    val = 0.95 + 0.04 * noise(h, w, (12, 4), rng) - 0.11 * ss(0.80, 0.97, g) - 0.035 * ss(0.6, 1.0, fine)
    val -= 0.03 * noise(h, w, (60, 10), rng)
    img = grey(val, (1.0, 0.985, 0.96))
    for _ in range(2):
        cx, cy = rng.uniform(0.15, 0.85), rng.uniform(0.25, 0.75)
        d = np.sqrt(((U - cx) * w / h * 1.6) ** 2 + ((V - cy) * 2.2) ** 2)
        img = blend(img, ss(0.07, 0.03, d), (0.62, 0.55, 0.48), 0.8)
        for rr in (0.1, 0.15):
            img = blend(img, ss(0.012, 0.0, np.abs(d - rr)), (0.78, 0.72, 0.66), 0.5)
    return img


def t_pgrain(w, h, rng):
    U, V = grid_st(w, h)
    warp = (noise(h, w, (5, 3), rng) - 0.5) * 0.35
    g = 0.5 + 0.5 * np.sin(2 * math.pi * (V * 6.5 + warp))
    val = 0.985 + 0.015 * noise(h, w, (10, 4), rng) - 0.035 * ss(0.85, 0.98, g)
    img = grey(val)
    edge = np.minimum(V, 1 - V)
    m = ss(0.12, 0.0, edge) * 0.8
    specks(img, m, rng, 500, 0.8, 2.2, (0.78, 0.66, 0.52), 0.8, wobble=0.3)
    return img


def t_slats(w, h, rng):
    """Deck boards across V (8 boards), grain along U, dark seams."""
    U, V = grid_st(w, h)
    k = (V * 8) % 1.0; b = np.floor(V * 8)
    warp = (noise(h, w, (6, 8), rng) - 0.5) * 0.3
    g = 0.5 + 0.5 * np.sin(2 * math.pi * (k * 3.5 + warp + b * 0.37))
    tone = 0.93 + 0.05 * np.sin(b * 2.1 + 1.0)
    val = tone - 0.07 * ss(0.8, 0.97, g) - 0.02 * noise(h, w, (40, 12), rng)
    val = val * (0.45 + 0.55 * ss(0.0, 0.07, np.minimum(k, 1 - k)))
    img = grey(val, (1.0, 0.985, 0.96))
    # nail heads at the board ends
    for uu in (0.04, 0.96):
        d = np.sqrt(((U - uu) * w / h * 8) ** 2 + (k - 0.5) ** 2)
        img = blend(img, ss(0.09, 0.05, d), (0.45, 0.42, 0.40), 0.8)
    return img


def t_bark(w, h, rng):
    U, V = grid_st(w, h)
    warp = (noise(h, w, (4, 6), rng) - 0.5) * 0.7 + (noise(h, w, (8, 18), rng) - 0.5) * 0.25
    ridge = 0.5 + 0.5 * np.cos(2 * math.pi * (U * 7 + warp))
    plates = noise(h, w, (14, 30), rng)
    val = 0.62 + 0.36 * ss(0.15, 0.75, ridge) * (0.85 + 0.15 * plates)
    cracks = ss(0.06, 0.0, np.abs(((V * 9 + noise(h, w, (6, 6), rng) * 1.2) % 1.0) - 0.5) - 0.44) * ss(0.4, 0.8, ridge)
    val -= 0.15 * cracks
    img = grey(val, (1.0, 0.98, 0.97))
    img = blend(img, ss(0.45, 0.0, ridge), (0.55, 0.53, 0.62), 0.35)     # cool crevices
    lich = ss(0.70, 0.86, noise(h, w, (10, 14), rng)) * ss(0.4, 0.9, ridge)
    img = blend(img, lich, (0.86, 0.90, 0.72), 0.45)                      # pale lichen
    return img


def t_stone(w, h, rng):
    U, V = grid_st(w, h)
    val = 0.93 + 0.06 * noise(h, w, (5, 5), rng) + 0.02 * noise(h, w, (24, 24), rng)
    img = grey(val)
    specks(img, np.ones((h, w)), rng, 260, 0.5, 1.4, (0.72, 0.70, 0.76), 0.6)
    specks(img, np.ones((h, w)), rng, 120, 0.5, 1.1, (1.0, 0.98, 0.94), 0.6)
    img = blend(img, ss(0.72, 0.9, noise(h, w, (6, 6), rng)), (0.84, 0.86, 0.80), 0.3)
    return img


def t_canvas(w, h, rng):
    U, V = grid_st(w, h)
    wv = 0.965 + 0.022 * np.sin(U * w * 1.6) * np.sin(V * h * 1.6)
    val = wv * (0.97 + 0.03 * noise(h, w, (6, 6), rng)) * (0.985 + 0.03 * V)
    img = grey(val)
    seam = ss(0.035, 0.0, np.minimum(U, 1 - U))
    img = blend(img, seam, (0.78, 0.76, 0.78), 0.55)
    img = blend(img, ss(0.012, 0.0, np.abs(V - 0.10)) * (np.sin(U * 90) > -0.2), (0.80, 0.78, 0.80), 0.5)
    return img


def t_terry(w, h, rng):
    U, V = grid_st(w, h)
    val = 0.92 + 0.07 * noise(h, w, (64, 64), rng) + 0.02 * np.sin(V * h * 2.2)
    return grey(val)


def t_rope(w, h, rng):
    U, V = grid_st(w, h)
    k = (V * 10 + U * 1.0) % 1.0
    strand = 0.5 + 0.5 * np.cos(2 * math.pi * k)
    val = 0.70 + 0.30 * ss(0.05, 0.75, strand) + 0.04 * (noise(h, w, (20, 60), rng) - 0.5)
    return grey(val, (1.0, 0.98, 0.95))


def t_grate(w, h, rng):
    U, V = grid_st(w, h)
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y); a = np.arctan2(y, x)
    img = grey(np.full(U.shape, 0.86))
    slot = (((r * 9.0) % 1.0) > 0.42) & (r > 0.16) & (r < 0.9)
    spoke = np.abs(((a / (2 * math.pi) * 12) % 1.0) - 0.5) * 2 * math.pi / 12 * np.maximum(r, 0.05) < 0.035
    holes = slot & ~spoke
    img = blend(img, holes.astype(np.float32), (0.13, 0.14, 0.16), 1.0)
    img = blend(img, ss(0.025, 0.0, np.abs(r - 0.92)), (0.55, 0.56, 0.58), 0.9)
    img = blend(img, ss(0.02, 0.0, np.abs(r - 0.16)), (0.55, 0.56, 0.58), 0.9)
    for k in range(8):
        aa = 2 * math.pi * (k + 0.5) / 8
        d = np.sqrt((x - 0.955 * np.cos(aa)) ** 2 + (y - 0.955 * np.sin(aa)) ** 2)
        img = blend(img, ss(0.03, 0.015, d), (0.45, 0.45, 0.47), 1.0)
    wet = ss(0.55, 0.85, noise(h, w, (6, 6), rng)) * (1 - holes)
    img = blend(img, wet, (0.62, 0.66, 0.72), 0.5)
    img = blend(img, ss(0.6, 0.8, noise(h, w, (16, 16), rng)) * (r < 0.9) * (1 - holes), (0.70, 0.62, 0.50), 0.35)
    return img


def t_water(w, h, rng):
    U, V = grid_st(w, h)
    val = 0.90 + 0.05 * noise(h, w, (6, 5), rng)
    bands = ss(0.82, 0.97, 0.5 + 0.5 * np.sin(2 * math.pi * (V * 7 + 0.4 * noise(h, w, (4, 4), rng))))
    val = val + 0.08 * bands * ss(0.3, 0.9, noise(h, w, (8, 3), rng))
    img = grey(np.clip(val, 0, 1))
    for _ in range(4):
        cx, cy = rng.uniform(0.2, 0.8), rng.uniform(0.2, 0.8)
        d = np.sqrt((U - cx) ** 2 + ((V - cy) * 1.3) ** 2)
        for rr in (0.04, 0.075, 0.11):
            img = blend(img, ss(0.006, 0.0, np.abs(d - rr)) * ss(0.16, 0.02, d), (1, 1, 1), 0.35)
    return img


def t_shingle(w, h, rng):
    """Rows of round-bottomed shingles: u along the eaves, v up the slope (8 rows, 12 across)."""
    U, V = grid_st(w, h)
    rows, cols = 8, 12
    r = np.floor(V * rows); f = (V * rows) % 1.0
    cu = (U * cols + 0.5 * (r % 2)) % 1.0
    scal = 0.30 * (1 - ((cu - 0.5) * 2) ** 2)          # how far each shingle's round bottom hangs
    fb = f - (0.30 - scal)                             # distance above this shingle's bottom edge
    tone = 0.92 + 0.07 * noise(h, w, (cols * 2, rows * 2), rng)
    val = tone * (0.80 + 0.20 * ss(0.0, 0.35, fb))
    val = np.where(fb < 0, tone * 0.70, val)           # the row below shows through: in shadow
    val = val * (1 - 0.22 * ss(0.035, 0.0, np.abs(cu - 0.5) - 0.465))
    val = val * (1 - 0.18 * ss(0.05, 0.0, np.abs(fb)))
    img = grey(val)
    moss = ss(0.68, 0.85, noise(h, w, (10, 8), rng)) * ss(0.4, 0.0, fb)
    img = blend(img, moss, (0.80, 0.82, 0.66), 0.35)
    return img


def t_sand(w, h, rng):
    val = 0.95 + 0.04 * noise(h, w, (8, 8), rng)
    img = grey(val)
    specks(img, np.ones((h, w)), rng, 700, 0.4, 0.9, (0.86, 0.81, 0.74), 0.6)
    specks(img, np.ones((h, w)), rng, 500, 0.4, 0.9, (1.0, 0.99, 0.96), 0.8)
    specks(img, np.ones((h, w)), rng, 60, 0.8, 1.6, (0.86, 0.68, 0.62), 0.6)
    return img


def t_target(w, h, rng):
    U, V = grid_st(w, h)
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y)
    img = grey(np.full(U.shape, 0.99) - 0.03 * noise(h, w, (6, 6), rng))
    for rr in (0.52, 0.74, 0.95):
        img = blend(img, ss(0.016, 0.006, np.abs(r - rr)), (0.62, 0.60, 0.62), 0.9)
    for _ in range(5):
        cx, cy = rng.uniform(-0.7, 0.7, 2)
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        img = blend(img, ss(0.10, 0.02, d) * (r < 0.98), (0.80, 0.78, 0.76), 0.35)
    return img


def t_flag(w, h, rng):
    U, V = grid_st(w, h)
    fold = 0.94 + 0.06 * np.sin(2 * math.pi * (U * 3.2 - 0.2 * V))
    img = grey(fold * (0.985 + 0.015 * noise(h, w, (8, 6), rng)))
    img = blend(img, ss(0.10, 0.08, U), (0.86, 0.85, 0.86), 1.0)           # the hoist sleeve
    img = blend(img, ss(0.006, 0.0, np.abs(U - 0.085)), (0.70, 0.70, 0.72), 0.9)
    edge = np.minimum(np.minimum(V, 1 - V), 1 - U)
    stitch = ss(0.006, 0.0, np.abs(edge - 0.05)) * (np.sin(U * 160) > 0)
    img = blend(img, stitch, (0.78, 0.78, 0.80), 0.6)
    return img


def t_mat(w, h, rng):
    U, V = grid_st(w, h)
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y); a = np.arctan2(y, x)
    weave = 0.5 + 0.5 * np.sin(U * w * 0.9) * np.sin(V * h * 0.9)
    val = 0.42 + 0.08 * weave + 0.04 * noise(h, w, (10, 10), rng)
    img = grey(val, (0.98, 0.99, 1.04))
    img = blend(img, ss(0.93, 0.95, r), (0.72, 0.72, 0.76), 1.0)                       # webbing band
    dash = (np.sin(a * 64) > 0.0) * ss(0.01, 0.0, np.abs(r - 0.965))
    img = blend(img, dash, (1.0, 1.0, 1.0), 0.9)                                      # stitching
    img = blend(img, ss(0.012, 0.0, np.abs(r - 0.90)), (0.62, 0.62, 0.66), 0.8)
    scuff = ss(0.55, 0.0, r) * ss(0.5, 0.8, noise(h, w, (5, 5), rng))
    img = blend(img, scuff, (0.58, 0.56, 0.54), 0.25)
    return img


def t_window(w, h, rng):
    U, V = grid_st(w, h)
    top, bot = np.array((0.16, 0.20, 0.27)), np.array((0.32, 0.40, 0.46))
    img = top[None, None] * V[..., None] + bot[None, None] * (1 - V[..., None])
    d = U * 0.8 + V
    img = blend(img, ss(0.10, 0.0, np.abs(d - 0.75)), (0.55, 0.64, 0.70), 0.55)
    img = blend(img, ss(0.035, 0.0, np.abs(d - 1.02)), (0.66, 0.75, 0.80), 0.6)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    return blend(img, ss(0.07, 0.0, edge), (0.10, 0.12, 0.15), 0.6)


def t_glow(w, h, rng):
    U, V = grid_st(w, h)
    d = np.sqrt(((U - 0.5) * 1.6) ** 2 + (V - 0.45) ** 2)
    img = blend(grey(np.ones(U.shape), (0.98, 0.80, 0.50)), ss(0.55, 0.05, d), (1.0, 0.98, 0.90), 1.0)
    edge = np.minimum(U, 1 - U)
    return blend(img, ss(0.06, 0.0, edge), (0.85, 0.58, 0.32), 0.6)


def t_lily(w, h, rng):
    U, V = grid_st(w, h)
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y); a = np.arctan2(y, x)
    img = grey(0.93 + 0.06 * noise(h, w, (6, 6), rng), (1.0, 1.0, 0.98))
    vein = ss(0.05, 0.0, np.abs(((a / (2 * math.pi) * 11) % 1.0) - 0.5) * r * 2.2) * (r > 0.08) * (r < 0.92)
    img = blend(img, vein, (1.0, 1.0, 0.86), 0.55)
    img = blend(img, ss(0.85, 0.98, r), (0.80, 0.78, 0.66), 0.6)
    img = blend(img, ss(0.10, 0.0, r), (1.0, 1.0, 0.85), 0.5)
    return img


def t_chain(w, h, rng):
    U, V = grid_st(w, h)
    n = 14
    k = np.floor(V * n); f = (V * n) % 1.0
    x = (U - 0.5) * 2
    ring = np.abs(np.sqrt((x / 0.75) ** 2 + ((f - 0.5) / 0.62) ** 2) - 0.75)
    face = ss(0.22, 0.12, ring)
    side = ss(0.35, 0.2, np.abs(x)) * ss(0.0, 0.1, f) * ss(1.0, 0.9, f)
    m = np.where(k % 2 == 0, face, side)
    img = grey(0.35 + 0.65 * m)
    return img


def t_bricks(w, h, rng):
    U, V = grid_st(w, h)
    rows = 6
    r = np.floor(V * rows); f = (V * rows) % 1.0
    cu = (U * 3 + 0.5 * (r % 2)); c = np.floor(cu); fu = cu % 1.0
    tone = 0.90 + 0.08 * np.sin(r * 3.7 + c * 2.3) + 0.03 * noise(h, w, (16, 16), rng)
    mort = np.minimum(ss(0.0, 0.07, np.minimum(f, 1 - f)), ss(0.0, 0.03, np.minimum(fu, 1 - fu)))
    val = tone * (0.72 + 0.28 * mort)
    img = grey(val)
    return img


def t_bucket(w, h, rng):
    U, V = grid_st(w, h)
    val = 0.97 + 0.02 * noise(h, w, (8, 4), rng)
    for vv in (0.2, 0.78):
        val = val - 0.12 * ss(0.03, 0.0, np.abs(V - vv)) + 0.05 * ss(0.03, 0.0, np.abs(V - vv - 0.04))
    img = grey(val)
    # little embossed waves along the middle band (no text)
    wave = 0.5 + 0.12 * np.sin(U * 2 * math.pi * 6)
    img = blend(img, ss(0.02, 0.0, np.abs(V - wave)), (0.86, 0.86, 0.86), 0.7)
    return img


TILE_FN = {'grain': t_grain, 'pgrain': t_pgrain, 'bark': t_bark, 'stone': t_stone, 'canvas': t_canvas,
           'rope': t_rope, 'grate': t_grate, 'water': t_water, 'shingle': t_shingle, 'sand': t_sand,
           'target': t_target, 'flag': t_flag, 'mat': t_mat, 'window': t_window, 'glow': t_glow,
           'lily': t_lily, 'chain': t_chain, 'bricks': t_bricks, 'terry': t_terry, 'bucket': t_bucket,
           'slats': t_slats}


# ---------------------------------------------------------------- per-model wear maps
def wear_map(w, h, ext, kind, M, rng):
    a0, a1, b0, b1 = ext
    S_, T_ = grid_st(w, h)
    a = a0 + S_ * (a1 - a0); b = b0 + T_ * (b1 - b0)
    ppm = w / (a1 - a0)
    img = np.ones((h, w, 3), np.float32)
    mott = noise(h, w, ((a1 - a0) * 1.6, (b1 - b0) * 1.6), rng)
    img *= (1 - M.fade * (mott - 0.5) * 2)[..., None]
    img *= (0.985 + 0.015 * noise(h, w, ((a1 - a0) * 10, (b1 - b0) * 10), rng))[..., None]
    zg = M.ground if M.ground is not None else b0
    if kind != 'top':
        z = b - zg
        nz = noise(h, w, ((a1 - a0) * 9, max(2, M.dirt_h * 14)), rng)
        g = ss(M.dirt_h, 0.0, z) * (0.35 + 0.9 * nz)
        img = blend(img, np.clip(g, 0, 1), M.dirt, M.dirt_a)
        specks(img, ss(M.dirt_h * 1.6, 0.0, z), rng, int(900 * (a1 - a0) * M.dirt_h + 50),
               0.6, max(1.0, ppm * 0.006), tuple(np.array(M.dirt) * 0.85), 0.55)
        # rain streaks: faint darker lines running down
        ns = int(M.streaks * (a1 - a0) * 7)
        for _ in range(ns):
            x = rng.uniform(a0, a1); ztop = rng.uniform(b0 + (b1 - b0) * 0.3, b1); L = rng.uniform(0.15, 0.7)
            wpx = rng.uniform(0.004, 0.012)
            m = ss(wpx, 0.0, np.abs(a - x)) * ss(ztop - L, ztop - 0.05, b) * (b < ztop)
            img = blend(img, m, (0.80, 0.78, 0.80), 0.25)
    else:
        specks(img, np.ones((h, w)), rng, int(140 * (a1 - a0) * (b1 - b0) + 20), 0.5, max(1.0, ppm * 0.005), M.dirt, 0.45)
    # chipped paint
    area = (a1 - a0) * (b1 - b0)
    cnt = int(M.chips * area * 22) + 2
    bias = ss(1.4, 0.0, b - zg) * 0.6 + 0.4 if kind != 'top' else np.full((h, w), 0.7)
    specks(img, bias, rng, cnt, max(0.8, ppm * 0.006), max(1.4, ppm * 0.018), M.chip, 0.9, wobble=0.35)
    # painted seams and marks
    if M.lines.get(kind):
        img *= seglines(a, b, M.lines[kind], 0.0035, max(0.003, 1.2 / ppm))[..., None]
    for (mp, x, y, rad, col, al) in M.spots:
        if mp != kind: continue
        d = np.sqrt((a - x) ** 2 + (b - y) ** 2)
        img = blend(img, ss(rad, rad * 0.4, d), col, al)
    return img


def paint(path, layout, seed=5):
    rng = np.random.default_rng(seed)
    img = np.ones((ATH, ATW, 3), np.float32)
    for name, (x0, y0, w, h) in layout.reg.items():
        if name == 'white':
            img[y0:y0 + h, x0:x0 + w] = 1.0
            continue
        if name in TILE_FN:
            sub = TILE_FN[name](w, h, rng)
        else:
            M, kind, ext = layout.maps[name]
            sub = wear_map(w, h, ext, kind, M, rng)
        sub = np.clip(sub, 0, 1)
        sub = np.pad(sub, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='edge')
        img[y0 - PAD:y0 + h + PAD, x0 - PAD:x0 + w + PAD] = sub
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
