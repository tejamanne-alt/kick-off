# Paints WorksAtlas.png for kit_works.py. Two kinds of regions:
#  - shared tiles (lattice bays, chain links, wire rope, hazard stripes, boards, glass, bricks,
#    roof tiles, glazed tiles, voussoir joints, track shoes, the hoist rack and deck plate ...):
#    absolute colours for parts whose vertex colour is white, multipliers for tinted parts;
#  - each model's projected maps (front: x, z; side: y, z; top: x, y), multipliers over the vertex
#    colours, so the game's recolour keeps them: soft mottling, ground dirt and splash, grime and
#    rust streaks hanging under every ledge, rust spots and chips, plus the model's own features
#    (panel joints, ribs, coursing, stains).
# Everything is procedural (numpy); no photo textures.
import math
import numpy as np
from PIL import Image
import kit_works_geo as G

PAD = 4


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def _blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def _mul(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m + m * np.array(col, np.float32)[None, None, :])


def _noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    cx, cy = max(2, int(cells[0])), max(2, int(cells[1]))
    small = (r.random((cy, cx)) * 255).astype(np.uint8)
    im = Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def _grid(w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    return U, V


def _const(w, h, col):
    return np.ones((h, w, 3), np.float32) * np.array(col, np.float32)


DIRT = (0.74, 0.66, 0.56)
STREAK = (0.70, 0.66, 0.61)
RUST = (0.74, 0.47, 0.31)
RUSTD = (0.55, 0.36, 0.26)


def _specks(img, mask, rng, count, rmin, rmax, col, alpha):
    """Soft round spots (pixels) where mask is high."""
    h, w = mask.shape
    if count <= 0: return img
    ys = rng.integers(0, h, count); xs = rng.integers(0, w, count)
    keep = rng.random(count) < mask[ys, xs]
    c = np.array(col, np.float32)
    for y, x in zip(ys[keep], xs[keep]):
        r = rng.uniform(rmin, rmax)
        y0, y1 = max(0, int(y - r - 1)), min(h, int(y + r + 2)); x0, x1 = max(0, int(x - r - 1)), min(w, int(x + r + 2))
        if y1 <= y0 or x1 <= x0: continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((yy - y) ** 2 + (xx - x) ** 2)
        m = (np.clip(r + 0.5 - d, 0, 1) * alpha)[..., None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + c * m
    return img


def _streak(img, ppm_a, ppm_b, a0, b1, a, btop, length, width, col, alpha, rng):
    """A soft vertical streak from (a, btop) down `length` metres (map coords: a across, b up)."""
    h, w = img.shape[:2]
    xc = (a - a0) * ppm_a; yt = (b1 - btop) * ppm_b
    hw = max(width * ppm_a, 0.6); ln = max(length * ppm_b, 2)
    x0, x1 = max(0, int(xc - 3 * hw - 2)), min(w, int(xc + 3 * hw + 3))
    y0, y1 = max(0, int(yt - 1)), min(h, int(yt + ln + 2))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    t = np.clip((yy - yt) / ln, 0, 1)
    wob = np.sin(yy * 0.13 + xc) * hw * 0.35
    across = np.exp(-(((xx - xc - wob) / (hw * (1 + 0.6 * t))) ** 2))
    along = (1 - t) ** 1.4 * _ss(-0.02, 0.06, t)
    m = (across * along * alpha * (yy >= yt))[..., None]
    c = np.array(col, np.float32)
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m + m * c)


# ---------------------------------------------------------------- shared tiles
LAT_BAR = (0.93, 0.72, 0.27)        # site yellow, as the chords
LAT_GAP = (0.80, 0.76, 0.80)        # the hazy inside of the tower, seen through the near face
LAT_FAR = (0.84, 0.74, 0.52)        # the far face's members, in shade


def t_lattice(w, h):
    """One bay of a mast face between the modelled corner chords (absolute colours): a horizontal
    at the bottom and a diagonal, over the pale, hazy inside of the tower with the far face's
    diagonal behind."""
    U, V = _grid(w, h)
    img = _const(w, h, LAT_GAP)
    img *= (0.94 + 0.06 * V)[..., None]
    far = np.abs((1 - U) - V)
    img = _blend(img, _ss(0.05, 0.03, far), LAT_FAR, 1.0)
    img = _blend(img, _ss(0.06, 0.04, np.abs(V - 0.5)), LAT_FAR, 0.0)
    d = np.abs(U - V)
    bw = 0.06
    bar = np.maximum(_ss(bw, bw - 0.02, d), _ss(0.075, 0.055, V))
    img = _blend(img, bar, LAT_BAR, 1.0)
    img = _blend(img, _ss(bw, bw - 0.015, d) * (U > V) * _ss(bw - 0.03, bw, d), (0.70, 0.52, 0.20), 0.5)
    for (cu, cv) in ((0.0, 0.0), (1.0, 1.0), (1.0, 0.0), (0.0, 1.0)):
        g = np.sqrt((U - cu) ** 2 + (V - cv) ** 2)
        img = _blend(img, _ss(0.15, 0.11, g), LAT_BAR, 1.0)
    return img


def t_latjib(w, h):
    """One bay of a jib side between the modelled chords: a W of diagonals (absolute colours)."""
    U, V = _grid(w, h)
    img = _const(w, h, LAT_GAP)
    img *= (0.94 + 0.06 * V)[..., None]
    img = _blend(img, _ss(0.05, 0.03, np.abs((1 - V) - 2 * np.abs(U - 0.5))), LAT_FAR, 0.9)
    d1 = np.abs(V - 2 * U); d2 = np.abs(V - (2 - 2 * U))
    bw = 0.1
    bar = np.maximum(_ss(bw, bw - 0.04, d1), _ss(bw, bw - 0.04, d2))
    img = _blend(img, bar, LAT_BAR, 1.0)
    img = _blend(img, _ss(0.09, 0.06, V), LAT_BAR, 1.0)
    img = _blend(img, _ss(0.09, 0.06, 1 - V), LAT_BAR, 1.0)
    return img


def t_chain(w, h):
    """Chain links along t (30 links over the tile), repeated four times across s (one per side)."""
    U, V = _grid(w, h)
    img = _const(w, h, (0.10, 0.10, 0.11))
    s = (U * 4) % 1.0
    n = 30
    k = V * n; i = np.floor(k); f = k % 1.0
    face_on = (i % 2 == 0)
    # face-on link: an oval ring
    ex = (s - 0.5) / 0.42; ey = (f - 0.5) / 0.62
    rr = np.sqrt(ex ** 2 + ey ** 2)
    ring = _ss(0.32, 0.18, np.abs(rr - 0.72))
    # edge-on link: a bar
    edge = _ss(0.22, 0.12, np.abs(s - 0.5)) * _ss(0.0, 0.12, f) * _ss(1.0, 0.88, f)
    m = np.where(face_on, ring, edge)
    shade = 0.32 + 0.28 * np.clip(1 - np.abs(s - 0.35) * 2.2, 0, 1)
    img = _blend(img, m, (0.55, 0.55, 0.56), 1.0)
    img = img * (0.8 + 0.6 * shade * m)[..., None]
    img = _mul(img, m * _noise(h, w, (4, 40), 11), (0.72, 0.50, 0.38), 0.6)
    return np.clip(img, 0, 1)


def t_rope(w, h):
    U, V = _grid(w, h)
    k = (V * 120 + U * 4 * 1.5) % 1.0
    img = _const(w, h, (0.30, 0.30, 0.32)) * (0.75 + 0.45 * np.sin(k * np.pi))[..., None]
    return np.clip(img, 0, 1)


def t_hazard(w, h):
    U, V = _grid(w, h)
    k = ((U * w / h) * 1.0 + V) * 2.0 % 1.0
    img = np.where((k < 0.5)[..., None], np.array((0.96, 0.76, 0.22), np.float32), np.array((0.16, 0.16, 0.17), np.float32))
    nz = _noise(h, w, (24, 4), 3)
    img = _mul(img, _ss(0.55, 0.9, nz), (0.80, 0.74, 0.66), 0.5)
    img = _mul(img, _ss(0.35, 0.0, V), DIRT, 0.4)
    return img


def t_wood(w, h):
    """Four boards stacked in V (each a quarter): planks, grain, knots, darker ends."""
    U, V = _grid(w, h)
    rng = np.random.default_rng(4)
    b = np.floor(V * 4).clip(0, 3); f = (V * 4) % 1.0
    tones = np.array([(0.80, 0.62, 0.42), (0.74, 0.56, 0.36), (0.78, 0.64, 0.47), (0.66, 0.58, 0.48)], np.float32)
    img = tones[b.astype(int)]
    grain = 0.93 + 0.07 * np.sin(U * 90 + np.sin(f * 7 + b * 2.1) * 2.2 + b * 3) * np.sin(f * 30 + U * 6)
    img *= grain[..., None]
    for k in range(10):
        cu, cv = rng.random(), (rng.integers(0, 4) + 0.3 + 0.4 * rng.random()) / 4
        d = np.sqrt(((U - cu) * w / h * 4) ** 2 + ((V - cv) * 4) ** 2 * 2)
        img = _mul(img, _ss(0.09, 0.03, d), (0.55, 0.40, 0.28), 0.9)
    img = _mul(img, _ss(0.10, 0.0, np.minimum(f, 1 - f)), (0.62, 0.52, 0.44), 0.7)
    img = _mul(img, _ss(0.04, 0.0, np.minimum(U, 1 - U)), (0.55, 0.45, 0.36), 0.8)
    img = _mul(img, _ss(0.5, 0.95, _noise(h, w, (30, 8), 5)), (0.80, 0.76, 0.70), 0.5)
    return img


def t_glass(w, h):
    U, V = _grid(w, h)
    top = np.array((0.52, 0.60, 0.70)); mid = np.array((0.17, 0.23, 0.30)); bot = np.array((0.24, 0.30, 0.35))
    t = V[..., None]
    img = np.where(t > 0.6, mid + (top - mid) * _ss(0.6, 1.0, t), bot + (mid - bot) * _ss(0.0, 0.6, t))
    d = U * 0.75 + V
    img = _blend(img, _ss(0.16, 0.0, np.abs(d - 0.95)), (0.78, 0.84, 0.90), 0.32)
    img = _blend(img, _ss(0.045, 0.0, np.abs(d - 1.27)), (0.88, 0.92, 0.95), 0.5)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    img = img * (1 - 0.4 * _ss(0.06, 0.0, edge))[..., None]
    img = _mul(img, _ss(0.35, 0.0, V) * _noise(h, w, (8, 4), 9), DIRT, 0.5)
    return img


def t_grille(w, h):
    U, V = _grid(w, h)
    img = _const(w, h, (0.36, 0.37, 0.39))
    cu = (U * 9) % 1.0; cv = (V * 6) % 1.0
    hole = np.sqrt((cu - 0.5) ** 2 + (cv - 0.5) ** 2)
    img = _blend(img, _ss(0.30, 0.22, hole), (0.07, 0.07, 0.08), 1.0)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    img = _blend(img, _ss(0.05, 0.0, edge), (0.22, 0.22, 0.24), 1.0)
    return img


def t_tiles(w, h):
    """A band of glazed tiles (2 m x 0.6 m): 0.15 m squares, grout, a darker border course,
    a few odd tiles and a cracked one. A multiplier over the tile colour."""
    U, V = _grid(w, h)
    x = U * 2.0; z = V * 0.6
    rng = np.random.default_rng(12)
    tone = rng.random((8, 16))
    ix = np.floor(x / 0.1667).astype(int) % 16; iz = np.floor((z - 0.075) / 0.15).astype(int).clip(0, 7)
    img = np.ones((h, w, 3), np.float32)
    img *= (0.90 + 0.10 * tone[iz, ix])[..., None]
    border = (z < 0.075) | (z > 0.525)
    img = np.where(border[..., None], img * np.array((0.70, 0.70, 0.72)), img)
    odd = (tone[iz, ix] > 0.93) & ~border
    img = np.where(odd[..., None], img * np.array((0.86, 0.88, 0.92)), img)
    jx = np.minimum(x % 0.1667, 0.1667 - x % 0.1667)
    zz = np.where(border, z % 0.075, (z - 0.075) % 0.15)
    zp = np.where(border, 0.075, 0.15)
    jz = np.minimum(zz, zp - zz)
    j = np.minimum(np.where(border, 1.0, jx), jz)
    img = _blend(img, _ss(0.007, 0.003, j), (0.62, 0.60, 0.57), 1.0)
    # glaze highlight on each tile's upper left
    cx = (x % 0.1667) / 0.1667; cz = (((z - 0.075) % 0.15) / 0.15)
    hl = _ss(0.35, 0.0, np.abs(cx + (1 - cz) - 0.55)) * ~border
    img = np.clip(img * (1 + 0.05 * hl)[..., None], 0, 1)
    crack = np.abs((x - 1.31) * 2.2 - np.sin(z * 30) * 0.02 - (z - 0.3)) < 0.004
    img = np.where((crack & (np.abs(x - 1.35) < 0.08) & ~border)[..., None], img * 0.6, img)
    img = _mul(img, _ss(0.25, 0.0, V) * _noise(h, w, (30, 4), 13), DIRT, 0.35)
    return img


def t_rooftile(w, h):
    """Clay pantiles on a roof slope: s along the ridge (5 m), t from the eave (0) to the ridge (1);
    0.9 m of slope in six courses."""
    U, V = _grid(w, h)
    x = U * 5.0; y = V * 0.9
    rng = np.random.default_rng(21)
    row = np.floor(y / 0.15); fy = (y % 0.15) / 0.15
    xo = x + (row % 2) * 0.1
    col = np.floor(xo / 0.2); fx = (xo % 0.2) / 0.2
    tone = rng.random((8, 40))[row.astype(int).clip(0, 7), col.astype(int) % 40]
    base = np.array((0.78, 0.42, 0.29), np.float32)
    img = base * (0.86 + 0.24 * tone)[..., None]
    roll = 0.80 + 0.30 * np.sin(fx * np.pi)
    img *= roll[..., None]
    img *= (0.72 + 0.28 * _ss(0.0, 0.35, fy))[..., None]       # shadow under the course above
    img = _blend(img, _ss(0.05, 0.0, 1 - fy) * 0.0, (0, 0, 0), 0)
    moss = _ss(0.62, 0.85, _noise(h, w, (60, 6), 22)) * _ss(0.5, 0.0, V)
    img = _blend(img, moss, (0.52, 0.56, 0.32), 0.55)
    img = _mul(img, _ss(0.55, 0.9, _noise(h, w, (90, 10), 23)), (0.82, 0.80, 0.78), 0.5)
    return np.clip(img, 0, 1)


def t_brick(w, h):
    """0.6 m x 2.4 m of stretcher-bond brick with a grimy base (absolute colours)."""
    U, V = _grid(w, h)
    x = U * 0.6; z = V * 2.4
    row = np.floor(z / 0.075)
    xo = x + (row % 2) * 0.1125
    col = np.floor(xo / 0.225)
    r = np.random.default_rng(3).random((64, 16))
    tone = r[(row.astype(int) % 64), (col.astype(int) % 16)]
    base = np.array((0.72, 0.38, 0.28), np.float32)
    img = base * (0.84 + 0.26 * tone)[..., None]
    img = np.where((tone > 0.9)[..., None], np.array((0.56, 0.29, 0.23), np.float32), img)
    img = np.where((tone < 0.07)[..., None], np.array((0.80, 0.50, 0.36), np.float32), img)
    jz = np.minimum(z % 0.075, 0.075 - z % 0.075); jx = np.minimum(xo % 0.225, 0.225 - xo % 0.225)
    j = np.minimum(jz, jx)
    img = _blend(img, _ss(0.0085, 0.004, j), (0.80, 0.77, 0.71), 1.0)
    img = _mul(img, _ss(0.6, 0.0, z) * (0.5 + 0.5 * _noise(h, w, (6, 20), 31)), (0.70, 0.64, 0.56), 0.6)
    img = _mul(img, _ss(0.6, 0.95, _noise(h, w, (12, 50), 32)), (0.85, 0.82, 0.78), 0.5)
    return img


def t_voussoir(w, h):
    """An arch ring: s around the ring's section (four sides), t along the arch; 11 stones with
    joints and a little tone variation (a multiplier over the stone colour)."""
    U, V = _grid(w, h)
    n = 11
    k = V * n; i = np.floor(k).clip(0, n - 1); f = k % 1.0
    tone = np.random.default_rng(41).random(n + 1)[i.astype(int)]
    img = np.ones((h, w, 3), np.float32) * (0.90 + 0.10 * tone)[..., None]
    img = _blend(img, _ss(0.045, 0.015, np.minimum(f, 1 - f)), (0.62, 0.59, 0.55), 1.0)
    img = _mul(img, _ss(0.55, 0.9, _noise(h, w, (8, 60), 42)), (0.86, 0.84, 0.80), 0.6)
    return img


def t_tread(w, h):
    """Track shoes along t (44 over the loop), across s the section perimeter."""
    U, V = _grid(w, h)
    n = 44
    f = (V * n) % 1.0
    img = _const(w, h, (0.26, 0.26, 0.28))
    grouser = _ss(0.18, 0.08, np.abs(f - 0.5))
    img = _blend(img, grouser, (0.40, 0.40, 0.42), 1.0)
    img = _blend(img, _ss(0.06, 0.0, np.minimum(f, 1 - f)), (0.12, 0.12, 0.13), 1.0)
    mud = _ss(0.45, 0.85, _noise(h, w, (6, 120), 51))
    img = _blend(img, mud, (0.48, 0.40, 0.32), 0.55)
    return img


def t_rack(w, h):
    """The hoist mast's rack seen from the front: 60 teeth over 3 m."""
    U, V = _grid(w, h)
    f = (V * 60) % 1.0
    tooth = 0.5 + 0.5 * np.cos(f * 2 * np.pi)
    img = _const(w, h, (0.22, 0.22, 0.24)) * (0.55 + 0.9 * tooth)[..., None]
    side = np.minimum(U, 1 - U)
    img = _blend(img, _ss(0.12, 0.05, side), (0.18, 0.18, 0.19), 1.0)
    img = _blend(img, _ss(0.6, 0.9, _noise(h, w, (3, 40), 61)), (0.36, 0.30, 0.24), 0.35)
    return np.clip(img, 0, 1)


def t_chequer(w, h):
    """Galvanised chequer plate (2.6 m x 1.5 m deck) with scuffs and dirt toward the edges."""
    U, V = _grid(w, h)
    x = U * 2.6; y = V * 1.5
    img = _const(w, h, (0.66, 0.68, 0.69))
    a = ((x + y) / 0.06) % 1.0; b = ((x - y) / 0.06) % 1.0
    lug1 = _ss(0.25, 0.1, np.abs(a - 0.5)) * _ss(0.42, 0.3, np.abs(((x - y) / 0.12) % 1.0 - 0.5))
    lug2 = _ss(0.25, 0.1, np.abs(b - 0.5)) * _ss(0.42, 0.3, np.abs(((x + y) / 0.12 + 0.5) % 1.0 - 0.5))
    img = _blend(img, np.maximum(lug1, lug2), (0.80, 0.82, 0.83), 0.8)
    edge = np.minimum(np.minimum(U, 1 - U) * 2.6, np.minimum(V, 1 - V) * 1.5)
    img = _mul(img, _ss(0.25, 0.0, edge) * (0.6 + 0.4 * _noise(h, w, (20, 12), 71)), DIRT, 0.6)
    img = _mul(img, _ss(0.5, 0.85, _noise(h, w, (40, 24), 72)), (0.80, 0.78, 0.74), 0.5)
    return img


def t_vent(w, h):
    U, V = _grid(w, h)
    k = (V * 7) % 1.0
    img = np.ones((h, w, 3), np.float32) * (1.0 - 0.45 * _ss(0.5, 1.0, k))[..., None]
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    img = _blend(img, _ss(0.08, 0.03, edge), (0.85, 0.85, 0.85), 1.0)
    return img


def t_rubble(w, h):
    """Builder's rubble seen from above: broken brick, plaster, block, timber offcuts, dust."""
    rng = np.random.default_rng(81)
    U, V = _grid(w, h)
    img = _const(w, h, (0.66, 0.62, 0.56))
    img *= (0.85 + 0.2 * _noise(h, w, (10, 8), 82))[..., None]
    cols = [(0.72, 0.38, 0.28), (0.80, 0.78, 0.72), (0.60, 0.58, 0.55), (0.76, 0.58, 0.38), (0.45, 0.44, 0.44), (0.88, 0.86, 0.80)]
    for k in range(150):
        cu, cv = rng.random(), rng.random()
        sw, sh_ = rng.uniform(0.02, 0.09), rng.uniform(0.015, 0.06)
        a = rng.uniform(0, np.pi)
        du = (U - cu) * np.cos(a) + (V - cv) * np.sin(a); dv = -(U - cu) * np.sin(a) + (V - cv) * np.cos(a)
        m = _ss(sw, sw - 0.01, np.abs(du)) * _ss(sh_, sh_ - 0.01, np.abs(dv))
        c = np.array(cols[rng.integers(0, len(cols))]) * rng.uniform(0.85, 1.05)
        img = _blend(img, m * 0.35, (0.2, 0.18, 0.16), 1.0)
        img = _blend(img, _ss(sw - 0.004, sw - 0.012, np.abs(du)) * _ss(sh_ - 0.004, sh_ - 0.012, np.abs(dv)), c, 1.0)
    return np.clip(img, 0, 1)


def t_ctrl(w, h):
    """A hoist control box face: a green and a red button, a key switch, a lamp (no text)."""
    U, V = _grid(w, h)
    img = _const(w, h, (0.86, 0.84, 0.78))
    for cu, cv, r, c in ((0.5, 0.72, 0.17, (0.30, 0.62, 0.34)), (0.5, 0.40, 0.19, (0.84, 0.22, 0.18)), (0.5, 0.14, 0.09, (0.25, 0.25, 0.27)), (0.5, 0.9, 0.06, (0.98, 0.70, 0.22))):
        d = np.sqrt(((U - cu) * w / h) ** 2 + (V - cv) ** 2)
        img = _blend(img, _ss(r + 0.03, r + 0.01, d), (0.30, 0.30, 0.32), 1.0)
        img = _blend(img, _ss(r, r - 0.02, d), c, 1.0)
        img = _blend(img, _ss(r * 0.5, 0.0, np.sqrt(((U - cu + 0.05) * w / h) ** 2 + (V - cv - r * 0.3) ** 2)), (1, 1, 1), 0.35)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    img = _blend(img, _ss(0.06, 0.02, edge), (0.66, 0.64, 0.60), 1.0)
    return img


def t_lampdiff(w, h):
    U, V = _grid(w, h)
    img = _const(w, h, (1.0, 0.96, 0.84))
    rib = 0.94 + 0.06 * np.cos(U * 2 * np.pi * 24)
    img *= rib[..., None]
    img = _blend(img, _ss(0.5, 0.0, np.abs(V - 0.5)) * _ss(0.4, 0.0, np.abs(U - 0.5)), (1.0, 0.99, 0.94), 0.6)
    edge = np.minimum(np.minimum(U, 1 - U) * 4, np.minimum(V, 1 - V))
    img = _blend(img, _ss(0.12, 0.0, edge), (0.86, 0.80, 0.68), 0.7)
    return img


def t_grate(w, h):
    U, V = _grid(w, h)
    img = _const(w, h, (0.28, 0.28, 0.30))
    bars = _ss(0.3, 0.15, np.abs((U * w / 3.0) % 1.0 - 0.5))
    img = _blend(img, bars, (0.70, 0.72, 0.72), 1.0)
    return img


def t_corrug(w, h):
    """Vertical ribs (multiplier), 0.25 m pitch over a 2 m wide tile."""
    U, V = _grid(w, h)
    k = (U * 8) % 1.0
    img = np.ones((h, w, 3), np.float32) * (0.80 + 0.2 * np.clip(np.cos((k - 0.3) * 2 * np.pi) * 0.5 + 0.5, 0, 1))[..., None]
    return img


TILE_SPECS = {
    'lattice': (128, 144, t_lattice), 'latjib': (192, 128, t_latjib), 'chain': (32, 512, t_chain),
    'rope': (16, 256, t_rope), 'hazard': (256, 48, t_hazard), 'wood': (512, 128, t_wood),
    'glass': (128, 128, t_glass), 'grille': (64, 48, t_grille), 'tiles': (512, 154, t_tiles),
    'rooftile': (512, 96, t_rooftile), 'brick': (96, 384, t_brick), 'voussoir': (64, 512, t_voussoir),
    'tread': (64, 512, t_tread), 'rack': (32, 512, t_rack), 'chequer': (256, 148, t_chequer),
    'vent': (64, 64, t_vent), 'rubble': (192, 128, t_rubble), 'ctrl': (48, 64, t_ctrl),
    'lampdiff': (128, 32, t_lampdiff), 'grate': (256, 24, t_grate), 'corrug': (128, 64, t_corrug),
}


def tile_items():
    return [(n, TILE_SPECS[n][0], TILE_SPECS[n][1]) for n in G.TILES]


# ---------------------------------------------------------------- per-model maps
def model_map(M, mp, w, h):
    a0, a1, b0, b1 = M.maps[mp]
    U, V = _grid(w, h)
    A = a0 + U * (a1 - a0); B = b0 + V * (b1 - b0)
    pa = w / (a1 - a0); pb = h / (b1 - b0)
    gr = M.grime
    seed = gr['seed'] * 13 + {'front': 1, 'side': 2, 'top': 3}[mp]
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32)
    ext_a, ext_b = a1 - a0, b1 - b0
    n1 = _noise(h, w, (ext_a / 0.7 + 2, ext_b / 0.7 + 2), seed)
    n2 = _noise(h, w, (ext_a / 0.12 + 2, ext_b / 0.12 + 2), seed + 1)
    img *= (1 - gr['mottle'] * (0.6 * n1 + 0.4 * n2))[..., None]
    vertical = mp in ('front', 'side')
    if vertical:
        z = B
        img *= (1 - 0.05 * _ss(1.2, 0.0, z))[..., None]
        if M.ground and gr['ground'] > 0:
            dh = gr['dirt_h']
            g = _ss(dh, 0.0, z) * (0.45 + 0.9 * _noise(h, w, (ext_a / 0.25 + 2, ext_b / 0.25 + 2), seed + 2))
            img = _mul(img, np.clip(g, 0, 1), DIRT, gr['ground'])
            nsp = int(min(ext_a * dh * 140, w * h * 0.01) * gr['ground'])
            _specks(img, _ss(dh * 1.4, 0.0, z) * 0.9, rng, nsp, 0.5, max(1.0, 0.008 * pa), (0.62, 0.54, 0.46), 0.55)
        # grime and rust streaks under ledges
        if gr['streaks'] > 0 and M.ledges:
            led = M.ledges
            budget = int(min(700, 30 + ext_a * ext_b * 18) * gr['streaks'])
            widths = np.array([(l[1] - l[0]) if mp == 'front' else (l[3] - l[2]) for l in led]) + 0.02
            p = widths / widths.sum()
            picks = rng.choice(len(led), size=budget, p=p)
            for i in picks:
                l = led[i]
                lo_, hi_ = (l[0], l[1]) if mp == 'front' else (l[2], l[3])
                a = rng.uniform(lo_, hi_)
                ln = rng.uniform(0.08, 0.6) * gr.get('streak_len', 1.0) * min(1.0, 0.3 + l[4] * 0.5)
                rust = rng.random() < gr['rust']
                col = RUST if rust else STREAK
                _streak(img, pa, pb, a0, b1, a, l[4] - 0.005, ln, rng.uniform(0.004, 0.02), col, rng.uniform(0.25, 0.6), rng)
    # rust spots and chips: in patches, more of them low down, never more than a few per 1000 px
    if gr['rust'] > 0 or gr['chips'] > 0:
        area = ext_a * ext_b
        patch = _ss(0.42, 0.8, _noise(h, w, (ext_a / 0.5 + 2, ext_b / 0.5 + 2), seed + 5))
        if vertical:
            patch = np.clip(patch + 0.35 * _ss(0.8, 0.0, B), 0, 1)
        cap = w * h * 0.004
        nr = int(min(area * 70 * gr['rust'], cap * gr['rust']))
        _specks(img, patch, rng, nr, 0.5, max(1.0, 0.012 * pa), RUST, 0.6)
        nc = int(min(area * 70 * gr['chips'], cap * gr['chips']))
        _specks(img, patch * 0.8 + 0.1, rng, nc, 0.5, max(0.8, 0.007 * pa), RUSTD, 0.55)
    for kind, kw in M.feats.get(mp, []) + M.feats.get('all', []):
        img = FEATS[kind](img, A, B, pa, pb, rng, **kw)
    return np.clip(img, 0, 1)


def f_rect(img, A, B, pa, pb, rng, a0, a1, b0, b1, col=(0.8, 0.8, 0.8), alpha=1.0, soft=0.01):
    m = _ss(-soft, soft, A - a0) * _ss(-soft, soft, a1 - A) * _ss(-soft, soft, B - b0) * _ss(-soft, soft, b1 - B)
    return _mul(img, m, col, alpha)


def f_lines(img, A, B, pa, pb, rng, lines, w=0.006, col=(0.55, 0.55, 0.55), alpha=1.0):
    """Dark joint lines along polylines in map coordinates."""
    k = np.zeros(A.shape, np.float32)
    for pl in lines:
        for (x0, y0), (x1, y1) in zip(pl[:-1], pl[1:]):
            dx, dy = x1 - x0, y1 - y0
            L2 = max(dx * dx + dy * dy, 1e-9)
            t = np.clip(((A - x0) * dx + (B - y0) * dy) / L2, 0, 1)
            d = np.sqrt((A - (x0 + t * dx)) ** 2 + (B - (y0 + t * dy)) ** 2)
            k = np.maximum(k, _ss(w, w * 0.4, d))
    return _mul(img, k, col, alpha)


def f_ribs(img, A, B, pa, pb, rng, a0, a1, b0, b1, pitch=0.25, depth=0.2, vertical=True):
    """Corrugation / ribbing as soft shading bands."""
    inside = (A >= a0) & (A <= a1) & (B >= b0) & (B <= b1)
    c = A if vertical else B
    k = (c / pitch) % 1.0
    sh = 1.0 - depth * (0.5 + 0.5 * np.cos(k * 2 * np.pi + 0.9))
    return img * np.where(inside, sh, 1.0)[..., None]


def f_ashlar(img, A, B, pa, pb, rng, a0, a1, b0, b1, course=0.35, block=0.6, joint=0.008, col=(0.66, 0.63, 0.58), tone=0.08):
    inside = (A >= a0) & (A <= a1) & (B >= b0) & (B <= b1)
    row = np.floor((B - b0) / course)
    off = (row % 2) * block * 0.5
    ca = (A - a0 + off)
    colk = np.floor(ca / block)
    rnd = np.random.default_rng(int(a0 * 100 + b0 * 10) % 1000).random((256, 256))
    tn = rnd[row.astype(int) % 256, colk.astype(int) % 256]
    sub = img * (1 - tone * tn)[..., None]
    ja = np.minimum(ca % block, block - ca % block); jb = np.minimum((B - b0) % course, course - (B - b0) % course)
    j = np.minimum(ja, jb)
    sub = _mul(sub, _ss(joint, joint * 0.3, j), col, 1.0)
    return np.where(inside[..., None], sub, img)


def f_stain(img, A, B, pa, pb, rng, a, b, ra, rb, col=DIRT, alpha=0.5):
    d = np.sqrt(((A - a) / ra) ** 2 + ((B - b) / rb) ** 2)
    n = _noise(A.shape[0], A.shape[1], (max(2, (A.max() - A.min()) / 0.15), max(2, (B.max() - B.min()) / 0.15)), int(a * 97 + b * 31) % 1000)
    m = _ss(1.0, 0.4, d + 0.35 * (n - 0.5))
    return _mul(img, m, col, alpha)


def f_streaks(img, A, B, pa, pb, rng, a0, a1, top, n=10, length=(0.3, 1.2), col=STREAK, alpha=(0.3, 0.6), width=(0.01, 0.04)):
    h, w = img.shape[:2]
    am, bm = A[0, 0] - 0.5 / pa, B[0, 0] + 0.5 / pb
    for i in range(n):
        _streak(img, pa, pb, am, bm, rng.uniform(a0, a1), top, rng.uniform(*length), rng.uniform(*width), col, rng.uniform(*alpha), rng)
    return img


def f_spatter(img, A, B, pa, pb, rng, a0, a1, b0, b1, n=200, r=(0.004, 0.02), col=(0.80, 0.78, 0.74), alpha=0.7):
    m = ((A >= a0) & (A <= a1) & (B >= b0) & (B <= b1)).astype(np.float32)
    return _specks(img, m, rng, n, max(0.5, r[0] * pa), max(1.0, r[1] * pa), col, alpha)


def f_band(img, A, B, pa, pb, rng, b0, b1, col=(0.8, 0.8, 0.8), alpha=1.0, soft=0.01, a0=-1e9, a1=1e9):
    m = _ss(-soft, soft, B - b0) * _ss(-soft, soft, b1 - B) * (A >= a0) * (A <= a1)
    return _mul(img, m, col, alpha)


def f_disc(img, A, B, pa, pb, rng, a, b, r, col=(0.7, 0.7, 0.7), alpha=1.0, soft=0.01):
    d = np.sqrt((A - a) ** 2 + (B - b) ** 2)
    return _mul(img, _ss(r + soft, r - soft, d), col, alpha)


FEATS = {'rect': f_rect, 'lines': f_lines, 'ribs': f_ribs, 'ashlar': f_ashlar, 'stain': f_stain,
         'streaks': f_streaks, 'spatter': f_spatter, 'band': f_band, 'disc': f_disc}


# ---------------------------------------------------------------- the atlas
def place(img, name, sub):
    x0, y0, x1, y1 = G.reg_px(name)
    h, w = y1 - y0, x1 - x0
    if sub.shape[0] != h or sub.shape[1] != w:
        sub = np.asarray(Image.fromarray((np.clip(sub, 0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255.0
    padded = np.pad(sub, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='edge')
    ya, yb = y0 - PAD, y1 + PAD; xa, xb = x0 - PAD, x1 + PAD
    cy0, cx0 = max(0, ya), max(0, xa); cy1, cx1 = min(G.AT, yb), min(G.AT, xb)
    img[cy0:cy1, cx0:cx1] = padded[cy0 - ya:cy0 - ya + (cy1 - cy0), cx0 - xa:cx0 - xa + (cx1 - cx0)]


def paint(path, models):
    img = np.ones((G.AT, G.AT, 3), np.float32)
    for name in G.TILES:
        w, h, fn = TILE_SPECS[name]
        place(img, name, fn(w, h))
    for M in models:
        for mp in ('front', 'side', 'top'):
            key = M.name + '.' + mp
            x0, y0, x1, y1 = G.reg_px(key)
            place(img, key, model_map(M, mp, x1 - x0, y1 - y0))
    # the plain white corner
    x0, y0, x1, y1 = G.reg_px('white')
    img[y0:y1, x0:x1] = 1.0
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
