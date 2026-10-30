# Paints BuildingsAtlas.png for kit_buildings.py. Two kinds of regions:
#  - shared tiles in absolute colour for parts whose vertex colour is white (glass, wood, brick,
#    produce, the AC grille, the clock face, the shop banner) or as multipliers for tinted parts
#    (louvred shutters, the generic wear map);
#  - per-building projected maps (front, left, right: (x or y, z); roof: (x, y)), multipliers over
#    the vertex colours, so the game's recolour keeps them: soft mottling, darker bases, grime
#    streaks under sills, contact shadows under canopies and balconies, tile joints, moss, rust.
import numpy as np
from PIL import Image
from kit_buildings_geo import REG, AT, reg_px

PAD = 6
rng = np.random.default_rng(5)


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def _blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def _mul(img, mask, col, alpha=1.0):
    """Multiply toward col where mask is set."""
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m + m * np.array(col, np.float32)[None, None, :])


def _noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    cx, cy = max(2, int(cells[0])), max(2, int(cells[1]))
    small = (r.random((cy, cx)) * 255).astype(np.uint8)
    im = Image.fromarray(small, 'L').resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def grid(name, pad=PAD):
    """Pixel slice of a region including its bleed, and U, V (0..1 inside the region, beyond it
    in the bleed), V up."""
    x0, y0, x1, y1 = reg_px(name)
    w, h = x1 - x0, y1 - y0
    xs = np.arange(max(0, x0 - pad), min(AT, x1 + pad)); ys = np.arange(max(0, y0 - pad), min(AT, y1 + pad))
    U = (xs - x0 + 0.5) / w
    V = 1 - (ys - y0 + 0.5) / h
    UU, VV = np.meshgrid(U, V)
    return (slice(ys[0], ys[-1] + 1), slice(xs[0], xs[-1] + 1)), UU, VV, w, h


def put(img, name, fn, pad=PAD):
    sl, U, V, w, h = grid(name, pad)
    img[sl] = np.clip(fn(U, V, w, h), 0, 1)


# ---------------------------------------------------------------- shared tiles
def glass(variant):
    def f(U, V, w, h):
        top = np.array((0.50, 0.56, 0.68)); mid = np.array((0.16, 0.22, 0.29)); bot = np.array((0.22, 0.29, 0.35))
        t = np.clip(V, 0, 1)[..., None]
        sub = np.where(t > 0.62, mid + (top - mid) * _ss(0.62, 1.0, t), bot + (mid - bot) * _ss(0.0, 0.62, t))
        if variant == 3:     # warm lit interior
            g = np.exp(-(((U - 0.5) / 0.35) ** 2 + ((V - 0.35) / 0.3) ** 2))
            sub = _blend(sub, g, (0.74, 0.52, 0.32), 0.6)
        if variant == 1:     # curtains at the sides and a gathered valance
            cur = np.array((0.95, 0.89, 0.78))
            for side in (U, 1 - U):
                wc = 0.15 + 0.035 * (1 - V)
                m = _ss(wc + 0.012, wc - 0.012, side)
                fold = 0.84 + 0.16 * np.cos(side / np.maximum(wc, 0.05) * np.pi * 3.0) ** 2
                sub = _blend(sub, m, cur, 1.0)
                sub = sub * (1 - m * (1 - fold))[..., None]
                sub = _mul(sub, _ss(wc - 0.035, wc, side) * m, (0.86, 0.82, 0.76), 0.6)
            val = (V > 0.86 + 0.025 * np.cos(U * 2 * np.pi * 4)).astype(np.float32)
            sub = _blend(sub, val, (0.90, 0.84, 0.74), 1.0)
            sub = _mul(sub, _ss(0.0, 0.03, V - 0.86 - 0.025 * np.cos(U * 2 * np.pi * 4)) * val, (0.8, 0.76, 0.7), 0.5)
        if variant == 2:     # a blind, half down
            m = (V > 0.58)
            slat = 0.9 + 0.1 * np.cos((V - 0.58) * 2 * np.pi * 14)
            sub = np.where(m[..., None], np.array((0.93, 0.88, 0.78)) * slat[..., None], sub)
            sub = _blend(sub, _ss(0.02, 0.0, np.abs(V - 0.58)), (0.55, 0.50, 0.44), 0.9)
        d = U * 0.75 + V
        s1 = _ss(0.16, 0.0, np.abs(d - 0.95)); s2 = _ss(0.045, 0.0, np.abs(d - 1.27))
        sub = _blend(sub, s1, (0.78, 0.84, 0.90), 0.34); sub = _blend(sub, s2, (0.88, 0.92, 0.95), 0.5)
        edge = np.minimum(np.minimum(U, 1 - U) * 1.4, 1 - V)
        sub = sub * (1 - 0.45 * _ss(0.07, 0.0, edge))[..., None]
        return sub
    return f


def louvre(U, V, w, h):
    sub = np.ones(U.shape + (3,), np.float32)
    inside = (np.abs(U - 0.5) < 0.38) & (np.abs(V - 0.5) < 0.45)
    k = ((V - 0.05) * 16) % 1.0
    slat = 1.0 - 0.32 * k
    sub = np.where(inside[..., None], (slat * (k < 0.86) + 0.55 * (k >= 0.86))[..., None] * np.ones(3), sub)
    rail = np.abs(V - 0.5) < 0.025
    sub[rail] = 1.0
    edge = np.minimum(np.abs(np.abs(U - 0.5) - 0.38), np.abs(np.abs(V - 0.5) - 0.45))
    sub = sub * (1 - 0.35 * _ss(0.02, 0.0, edge) * (np.abs(U - 0.5) < 0.39) * (np.abs(V - 0.5) < 0.46))[..., None]
    sub *= (0.88 + 0.12 * _ss(0.0, 0.5, V))[..., None]
    return sub


def wood(U, V, w, h):
    base = np.array((0.76, 0.56, 0.37))
    plank = np.floor(V * 4); kv = (V * 4) % 1.0
    tone = 0.9 + 0.1 * np.sin(plank * 2.3 + 1)
    grain = 0.95 + 0.05 * np.sin(U * 20 + np.sin(V * 23 + plank * 1.7) * 1.5 + plank)
    sub = base[None, None] * (tone * grain)[..., None]
    sub = _blend(sub, _ss(0.08, 0.0, np.minimum(kv, 1 - kv)), (0.36, 0.24, 0.15), 0.95)
    return sub


def crate(U, V, w, h):
    base = np.array((0.80, 0.62, 0.42))
    sub = base[None, None] * (0.94 + 0.06 * np.sin(U * 40 + V * 3))[..., None]
    gap = (np.abs(V - 0.5) < 0.06)
    sub = np.where(gap[..., None], np.array((0.22, 0.16, 0.12)), sub)
    post = (np.minimum(U, 1 - U) < 0.1)
    sub = np.where(post[..., None], base * 0.82, sub)
    sub = _blend(sub, _ss(0.03, 0.0, np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))), (0.4, 0.28, 0.18), 0.8)
    return sub


def brick(U, V, w, h):
    # 0.8 m x 2.4 m of brick
    x = U * 0.8; z = V * 2.4
    row = np.floor(z / 0.075)
    xo = x + (row % 2) * 0.11
    col = np.floor(xo / 0.225)
    r = np.random.default_rng(3).random((64, 16))
    tone = r[(row.astype(int) % 64), (col.astype(int) % 16)]
    base = np.array((0.70, 0.36, 0.27))
    sub = base[None, None] * (0.86 + 0.24 * tone)[..., None]
    sub = np.where((tone > 0.9)[..., None], np.array((0.52, 0.27, 0.22)), sub)
    jz = np.minimum(z % 0.075, 0.075 - z % 0.075); jx = np.minimum(xo % 0.225, 0.225 - xo % 0.225)
    j = np.minimum(jz, jx)
    sub = _blend(sub, _ss(0.009, 0.004, j), (0.74, 0.70, 0.64), 1.0)
    sub = _mul(sub, _ss(1.6, 2.4, z), (0.55, 0.52, 0.5), 0.6)        # soot at the top
    return sub


def produce(kind):
    cols = {'orange': [(0.98, 0.60, 0.18), (0.95, 0.52, 0.14)], 'apple': [(0.84, 0.20, 0.17), (0.90, 0.38, 0.22), (0.76, 0.16, 0.16)],
            'lemon': [(0.99, 0.86, 0.30), (0.96, 0.80, 0.26)], 'green': [(0.58, 0.78, 0.30), (0.50, 0.72, 0.28)],
            'tomato': [(0.92, 0.28, 0.20), (0.86, 0.22, 0.18)], 'plum': [(0.48, 0.26, 0.50), (0.40, 0.22, 0.44)]}

    def f(U, V, w, h):
        r = np.random.default_rng(len(kind) * 17)
        sub = np.ones(U.shape + (3,), np.float32) * np.array((0.28, 0.21, 0.15))
        n = 46 if kind != 'tomato' else 70
        rad = 0.11 if kind != 'tomato' else 0.085
        cl = cols[kind]
        pts = sorted([(r.random(), r.random()) for _ in range(n)], key=lambda p: -p[1])
        for (cx, cy) in pts:
            rr = rad * r.uniform(0.85, 1.12)
            sx = 1.25 if kind == 'lemon' else 1.0
            d = np.sqrt(((U - cx) / sx) ** 2 + (V - cy) ** 2) / rr
            m = d < 1.0
            if not m.any(): continue
            c = np.array(cl[int(r.integers(0, len(cl)))])
            lx, ly = (U - cx + rr * 0.35) / rr, (V - cy - rr * 0.35) / rr
            shade = np.clip(1.05 - 0.45 * d ** 2, 0.5, 1.1)
            hl = np.exp(-(lx ** 2 + ly ** 2) / 0.06)
            col = c[None, None] * shade[..., None] + hl[..., None] * 0.35
            sub = np.where(m[..., None], col, sub)
            if kind == 'green':
                sub = np.where((m & (np.abs(U - cx) < 0.008) & (V > cy + rr * 0.6))[..., None], np.array((0.3, 0.22, 0.12)), sub)
        return sub
    return f


def melon(U, V, w, h):
    base = np.array((0.30, 0.50, 0.24))
    s = np.sin(U * 2 * np.pi * 7 + np.sin(V * 9) * 0.6)
    sub = base[None, None] * np.ones(U.shape)[..., None]
    sub = _blend(sub, _ss(0.2, 0.7, s), (0.56, 0.72, 0.38), 0.9)
    return sub


def ac(U, V, w, h):
    sub = np.ones(U.shape + (3,), np.float32) * np.array((0.92, 0.92, 0.90))
    x = (U - 0.64) / 0.29 * 1.46; y = (V - 0.5) / 0.42
    r = np.sqrt(x * x + y * y)
    m = r < 1.0
    rings = 0.32 + 0.16 * (np.cos(r * 2 * np.pi * 5) > 0.3)
    spokes = (np.abs(np.sin(np.arctan2(y, x) * 2)) < 0.12) & (r < 0.95)
    g = np.where(spokes, 0.45, rings)
    sub = np.where(m[..., None], g[..., None] * np.array((1, 1, 1.02)), sub)
    sub = _blend(sub, _ss(0.05, 0.0, np.abs(r - 1.0)), (0.62, 0.62, 0.62), 0.9)
    sub = _blend(sub, (r < 0.16).astype(np.float32), (0.7, 0.7, 0.7), 1.0)
    lv = (U > 0.08) & (U < 0.3) & (V > 0.15) & (V < 0.85)
    k = (V * 14) % 1.0
    sub = np.where((lv & (k < 0.45))[..., None], np.array((0.62, 0.62, 0.63)), sub)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    sub = sub * (1 - 0.2 * _ss(0.04, 0.0, edge))[..., None]
    sub = _mul(sub, _ss(0.35, 0.0, V), (0.8, 0.76, 0.7), 0.5)
    return sub


def vent(U, V, w, h):
    sub = np.ones(U.shape + (3,), np.float32) * 0.92
    inside = (np.abs(U - 0.5) < 0.38) & (np.abs(V - 0.5) < 0.38)
    k = (V * 9) % 1.0
    sub = np.where(inside[..., None], (0.35 + 0.5 * k)[..., None] * np.ones(3), sub)
    return sub


def clock(U, V, w, h):
    x, y = (U - 0.5) * 2, (V - 0.5) * 2
    r = np.sqrt(x * x + y * y); a = np.arctan2(x, y)
    sub = np.ones(U.shape + (3,), np.float32) * np.array((0.97, 0.94, 0.86))
    sub = _blend(sub, _ss(0.9, 0.86, r) * 0 + (r > 0.9), (0.20, 0.22, 0.26), 1.0)
    sub = _blend(sub, _ss(0.02, 0.0, np.abs(r - 0.84)), (0.30, 0.28, 0.26), 0.9)
    for k in range(60):
        aa = 2 * np.pi * k / 60
        big = k % 5 == 0
        L0 = 0.62 if k % 15 == 0 else (0.70 if big else 0.77)
        wd = 0.035 if k % 15 == 0 else (0.022 if big else 0.008)
        dx, dy = np.sin(aa), np.cos(aa)
        along = x * dx + y * dy; perp = np.abs(x * dy - y * dx)
        m = (along > L0) & (along < 0.82) & (perp < wd)
        sub = np.where(m[..., None], np.array((0.18, 0.18, 0.2)), sub)
    sub = _mul(sub, _ss(0.2, 0.86, r) * (y < 0), (0.92, 0.9, 0.86), 0.5)
    return sub


def banner(U, V, w, h):
    base = np.array((0.20, 0.26, 0.46))
    sub = base[None, None] * (0.92 + 0.08 * np.sin(U * 2 * np.pi * 12))[..., None] * np.ones(U.shape)[..., None]
    x, y = (U - 0.5) * 2 * (w / h), (V - 0.52) * 2
    r = np.sqrt(x * x + y * y)
    sub = _blend(sub, _ss(0.06, 0.03, np.abs(r - 0.62)), (0.96, 0.94, 0.88), 1.0)
    # three steam wisps above a bowl inside the ring
    bowl = (y < -0.05) & (y > -0.35) & (np.abs(x) < 0.38 * np.sqrt(np.clip(1 - ((y + 0.05) / 0.3) ** 2, 0, 1)) + 0.0)
    sub = np.where(bowl[..., None], np.array((0.96, 0.94, 0.88)), sub)
    for k, cx in enumerate((-0.18, 0.0, 0.18)):
        wx = cx + 0.06 * np.sin(y * 12 + k)
        m = (np.abs(x - wx) < 0.035) & (y > 0.02) & (y < 0.38)
        sub = np.where(m[..., None], np.array((0.96, 0.94, 0.88)), sub)
    sub = _blend(sub, _ss(0.025, 0.0, np.abs(V - 0.92)), (0.85, 0.82, 0.74), 0.8)
    sub *= (0.85 + 0.15 * _ss(0.0, 0.5, V))[..., None]
    return sub


def wear(U, V, w, h):
    sub = np.ones(U.shape + (3,), np.float32)
    n = _noise(U.shape[0], U.shape[1], (10, 10), 21)
    sub *= (0.97 + 0.03 * n)[..., None]
    g = _ss(0.35, 0.0, V) * (0.6 + 0.4 * n)
    sub = _mul(sub, g, (0.72, 0.68, 0.64), 0.6)
    for k in range(7):
        cx = 0.08 + 0.84 * ((k * 0.37) % 1.0); L = 0.25 + 0.4 * ((k * 0.61) % 1.0)
        m = _ss(0.03, 0.0, np.abs(U - cx)) * _ss(1 - L, 1.0, V)
        sub = _mul(sub, m, (0.80, 0.77, 0.74), 0.5)
    edge = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    sub = _mul(sub, _ss(0.05, 0.0, edge), (0.85, 0.83, 0.8), 0.6)
    return sub


def solar(U, V, w, h):
    sub = np.ones(U.shape + (3,), np.float32) * np.array((0.16, 0.22, 0.38))
    cu, cv = (U * 6) % 1.0, (V * 4) % 1.0
    line = (np.minimum(cu, 1 - cu) < 0.04) | (np.minimum(cv, 1 - cv) < 0.05)
    sub = np.where(line[..., None], np.array((0.62, 0.66, 0.72)), sub)
    d = U * 0.6 + V
    sub = _blend(sub, _ss(0.12, 0.0, np.abs(d - 0.9)), (0.5, 0.58, 0.72), 0.35)
    return sub


# ---------------------------------------------------------------- building maps
def wall_map(B, mp):
    feats = B.feats.get(mp, [])
    style = B.style.get(mp, B.style.get('wall', 'render'))
    a0, a1, b0, b1 = B.maps[mp]
    seed = (sum(map(ord, B.name)) * 7 + sum(map(ord, mp))) % 9973
    r = np.random.default_rng(seed)

    def f(U, V, w, h):
        A = a0 + U * (a1 - a0); Z = b0 + V * (b1 - b0)
        ppm = w / (a1 - a0)
        sub = np.ones(U.shape + (3,), np.float32)
        H_, W_ = U.shape
        n1 = _noise(H_, W_, ((a1 - a0) / 1.6, (b1 - b0) / 1.6), seed)
        n2 = _noise(H_, W_, ((a1 - a0) / 0.35, (b1 - b0) / 0.35), seed + 1)
        n3 = _noise(H_, W_, ((a1 - a0) / 0.12, (b1 - b0) / 0.5), seed + 2)
        sub *= (0.965 + 0.035 * n1 + 0.015 * (n2 - 0.5))[..., None]
        if style == 'brick':
            row = np.floor(Z / 0.09)
            xo = A + (row % 2) * 0.125
            col = np.floor(xo / 0.25)
            rr = np.random.default_rng(seed + 5).random((256, 256))
            tone = rr[(row.astype(int) % 256), (col.astype(int) % 256)]
            sub *= (0.93 + 0.1 * tone)[..., None]
            sub = np.where((tone > 0.93)[..., None], sub * np.array((0.82, 0.8, 0.82)), sub)
            jz = np.minimum(Z % 0.09, 0.09 - Z % 0.09); jx = np.minimum(xo % 0.25, 0.25 - xo % 0.25)
            j = np.minimum(jz, jx)
            sub = _mul(sub, _ss(1.4 / ppm, 0.4 / ppm, j), (0.80, 0.78, 0.76), 0.85)
        if style in ('metal', 'siding'):
            # fixings lines with rust bleeding down from them
            rows = B.style.get('fix_rows', [0.6, 2.2, 3.8])
            for zr in rows:
                for k in range(int((a1 - a0) / 0.9) + 1):
                    if r.random() > (0.6 if style == 'metal' else 0.3): continue
                    ax = a0 + k * 0.9 + r.uniform(0.2, 0.7)
                    L = r.uniform(0.25, 0.8)
                    m = _ss(0.035, 0.0, np.abs(A - ax)) * _ss(zr - L, zr, Z) * (Z < zr + 0.02)
                    sub = _mul(sub, m * (0.6 + 0.4 * n3), (0.78, 0.55, 0.40), 0.55 if style == 'metal' else 0.35)
            sub = _mul(sub, _ss(1.2, 0.0, Z) * (0.4 + 0.6 * n2), (0.72, 0.64, 0.56), 0.4)
        # base grime and splash
        g = _ss(0.75, 0.0, Z) * (0.55 + 0.45 * n2)
        sub = _mul(sub, g, (0.66, 0.61, 0.56), 0.55)
        sp = (n3 > 0.72) * _ss(0.45, 0.05, Z)
        sub = _mul(sub, sp, (0.7, 0.64, 0.58), 0.35)
        # rain run-off under the top edge (flat roofs and parapets)
        for kind, kw in feats:
            if kind == 'top':
                zt = kw['b']
                for k in range(int((a1 - a0) / 0.5) + 2):
                    ax = a0 + k * 0.5 + r.uniform(-0.2, 0.2); L = r.uniform(0.4, 1.6)
                    wd = r.uniform(0.05, 0.16)
                    m = _ss(wd, 0.0, np.abs(A - ax)) * _ss(zt - L, zt, Z) * (Z < zt)
                    sub = _mul(sub, m * (0.5 + 0.5 * n3), (0.78, 0.75, 0.72), 0.6 * kw.get('k', 1.0))
                sub = _mul(sub, _ss(zt - 0.35, zt, Z) * (Z < zt), (0.82, 0.8, 0.78), 0.5 * kw.get('k', 1.0))
        for kind, kw in feats:
            if kind == 'streak':
                s0, s1, zb, L, k = kw['a0'], kw['a1'], kw['b'], kw['length'], kw.get('k', 1.0)
                xs = [s0 + 0.06, s1 - 0.06] + list(r.uniform(s0 + 0.1, s1 - 0.1, max(1, int((s1 - s0) / 0.35))))
                for ax in xs:
                    LL = L * r.uniform(0.45, 1.0); wd = r.uniform(0.025, 0.07)
                    m = _ss(wd, 0.0, np.abs(A - ax)) * ((Z - (zb - LL)) / LL).clip(0, 1) ** 1.6 * (Z < zb)
                    sub = _mul(sub, m * (0.55 + 0.45 * n3), (0.68, 0.64, 0.60), 0.85 * k)
                wash = _ss(0.12, 0.0, np.maximum(s0 - A, A - s1)) * _ss(zb - L * 0.5, zb, Z) * (Z < zb)
                sub = _mul(sub, wash, (0.86, 0.84, 0.8), 0.45 * k)
            elif kind == 'ao':
                s0, s1, zb, L, k = kw['a0'], kw['a1'], kw['b'], kw['length'], kw.get('k', 0.5)
                m = _ss(0.08, -0.02, np.maximum(s0 - A, A - s1)) * _ss(zb - L, zb, Z) * (Z <= zb + 0.01)
                sub = _mul(sub, m, (0.62, 0.60, 0.66), k)
            elif kind == 'ao_rect':
                s0, s1, z0, z1, k = kw['a0'], kw['a1'], kw['b0'], kw['b1'], kw.get('k', 0.3)
                dx = np.maximum(np.maximum(s0 - A, A - s1), 0); dz = np.maximum(np.maximum(z0 - Z, Z - z1), 0)
                d = np.sqrt(dx * dx + dz * dz)
                m = np.exp(-d / 0.07) * (1 - 0.5 * (Z > z1))
                sub = _mul(sub, m, (0.66, 0.64, 0.7), k)
            elif kind == 'patch':        # render fallen away, a few chunky bricks showing
                cx, cz, rw, rh = kw['a'], kw['b'], kw['w'], kw['h']
                e = ((A - cx) / rw) ** 2 + ((Z - cz) / rh) ** 2 + (n2 - 0.5) * 0.6 + (n3 - 0.5) * 0.35
                m = (e < 1.0)
                row = np.floor(Z / 0.1); xo = A + (row % 2) * 0.14
                jz = np.minimum(Z % 0.1, 0.1 - Z % 0.1); jx = np.minimum(xo % 0.28, 0.28 - xo % 0.28)
                joint = np.minimum(jz, jx) < 1.3 / ppm
                tone = np.sin(np.floor(xo / 0.28) * 12.9 + row * 78.2) * 0.5 + 0.5
                brick = np.array((0.92, 0.66, 0.55))[None, None] * (0.92 + 0.12 * tone)[..., None]
                bc = np.where(joint[..., None], np.array((0.86, 0.83, 0.8)), brick)
                sub = np.where(m[..., None], sub * bc, sub)
                rim = (e >= 1.0) & (e < 1.0 + 3.0 / (ppm * min(rw, rh)))
                sub = np.where(rim[..., None], sub * 0.82, sub)
            elif kind == 'line':        # a painted band (e.g. a stripe), multiplier col
                s0, s1, z0, z1, col = kw['a0'], kw['a1'], kw['b0'], kw['b1'], kw['col']
                m = (A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)
                sub = np.where(m[..., None], sub * np.array(col), sub)
        return sub
    return f


def roof_map(B, mp='roof'):
    feats = B.feats.get(mp, [])
    a0, a1, b0, b1 = B.maps[mp]
    seed = sum(map(ord, B.name)) * 3 % 9973
    r = np.random.default_rng(seed)

    def f(U, V, w, h):
        X = a0 + U * (a1 - a0); Y = b0 + V * (b1 - b0)
        ppm = w / (a1 - a0)
        H_, W_ = U.shape
        sub = np.ones(U.shape + (3,), np.float32)
        n1 = _noise(H_, W_, ((a1 - a0) / 1.5, (b1 - b0) / 1.5), seed)
        n2 = _noise(H_, W_, ((a1 - a0) / 0.4, (b1 - b0) / 0.4), seed + 1)
        sub *= (0.95 + 0.05 * n1)[..., None]
        for kind, kw in feats:
            if kind == 'tiles':
                ax = kw['axis']; j = kw['joint']
                S = X if ax == 'y' else Y          # across the slope
                Rr = Y if ax == 'y' else X         # along the run
                for k, (lo, hi) in enumerate(kw['rows']):
                    t = (S - lo) / (hi - lo)
                    m = (t >= 0) & (t <= 1)
                    if not m.any(): continue
                    off = (k % 2) * j * 0.5
                    q = (Rr - kw['r0'] + off) / j
                    cell = np.floor(q); fq = q - cell
                    tone = np.sin(cell * 12.9898 + k * 78.233) * 43758.5453; tone = tone - np.floor(tone)
                    shade = 0.90 + 0.14 * tone
                    shade = shade * (1 - 0.22 * _ss(0.6, 1.0, t))     # under the next row's lip
                    shade = shade * (1 + 0.06 * _ss(0.3, 0.0, t))
                    jt = np.minimum(fq, 1 - fq) * j
                    shade = shade * (1 - 0.4 * _ss(1.3 / ppm, 0.3 / ppm, jt))
                    sub = np.where(m[..., None], sub * shade[..., None], sub)
                moss = (n2 > 0.74) * (n1 > 0.45)
                sub = _mul(sub, moss.astype(np.float32), (0.86, 0.92, 0.62), 0.5)
                sub = _mul(sub, (n2 < 0.12).astype(np.float32), (0.8, 0.78, 0.76), 0.4)
            elif kind == 'ribs':
                x0, x1, y0, y1, p = kw['x0'], kw['x1'], kw['y0'], kw['y1'], kw['pitch']
                n3 = _noise(H_, W_, ((a1 - a0) / 0.15, (b1 - b0) / 1.2), seed + 4)
                sub *= (0.94 + 0.08 * n3)[..., None]
                for k in range(int((x1 - x0) / 0.9) + 1):
                    sx = x0 + k * 0.9 + 0.45
                    sub = _mul(sub, _ss(0.04, 0.0, np.abs(X - sx)), (0.82, 0.8, 0.8), 0.6)
                for k in range(int((x1 - x0) / 0.4)):
                    if r.random() < 0.55: continue
                    sx = x0 + r.uniform(0, x1 - x0); L = r.uniform(0.6, 2.5)
                    m = _ss(0.06, 0.0, np.abs(X - sx)) * _ss(y0 + L, y0, Y)
                    sub = _mul(sub, m * (0.5 + 0.5 * n2), (0.85, 0.62, 0.45), 0.6)
                sub = _mul(sub, _ss(y0 + 0.6, y0, Y) * n2, (0.8, 0.66, 0.54), 0.5)
            elif kind == 'flat':
                sub *= (0.9 + 0.1 * n2)[..., None]
                for k in range(5):
                    cx, cy = r.uniform(a0, a1), r.uniform(b0, b1)
                    e = ((X - cx) / r.uniform(0.6, 2.0)) ** 2 + ((Y - cy) / r.uniform(0.6, 2.0)) ** 2 + (n2 - 0.5)
                    sub = _mul(sub, (e < 1.0).astype(np.float32), (0.84, 0.84, 0.86), 0.6)
                ed = np.minimum(np.minimum(X - kw['x0'], kw['x1'] - X), np.minimum(Y - kw['y0'], kw['y1'] - Y))
                sub = _mul(sub, _ss(0.5, 0.0, ed), (0.78, 0.76, 0.74), 0.6)
        return sub
    return f


def paint(path, buildings):
    img = np.ones((AT, AT, 3), np.float32)
    for k in range(4): put(img, 'glass%d' % k, glass(k))
    put(img, 'louvre', louvre); put(img, 'wood', wood); put(img, 'crate', crate); put(img, 'brick', brick)
    for kind in ('orange', 'apple', 'lemon', 'green', 'tomato', 'plum'): put(img, 'p_' + kind, produce(kind))
    put(img, 'melon', melon); put(img, 'ac', ac); put(img, 'vent', vent); put(img, 'clock', clock)
    put(img, 'banner', banner); put(img, 'wear', wear); put(img, 'solar', solar)
    for B in buildings:
        for mp in B.maps:
            name = B.name + '.' + mp
            if mp in ('roof', 'roofb'): put(img, name, roof_map(B, mp))
            else: put(img, name, wall_map(B, mp))
    x0, y0, x1, y1 = reg_px('white')
    img[y0 - PAD:, x0 - PAD:] = 1.0
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
