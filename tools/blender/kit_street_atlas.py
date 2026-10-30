# The street kit's atlas (StreetAtlas.png): layout, UV helpers and the painted weathering maps.
# Everything here multiplies the vertex colours, so painted wear survives a recolour. Values are
# sRGB. Regions marked periodic repeat seamlessly across their width (u), so a tiling model can map
# exactly one period across its length, and a cylinder its full turn.
import math
import numpy as np

AT = 2048
WHITE_UV = (0.97, 0.03)
# name: (u0, v0, u1, v1), v up
REG = {
    'conc':     (0.0, 0.90625, 0.5, 1.0),
    'paint':    (0.5, 0.90625, 1.0, 1.0),
    'plastic':  (0.0, 0.8125, 0.5, 0.90625),
    'pwood':    (0.5, 0.8125, 0.75, 0.90625),
    'wood':     (0.75, 0.8125, 1.0, 0.90625),
    'wall':     (0.0, 0.4375, 0.5, 0.8125),
    'hoard':    (0.5, 0.4375, 1.0, 0.8125),
    'vdisp1':   (0.0, 0.25, 0.09375, 0.4375),
    'vdisp2':   (0.09375, 0.25, 0.1875, 0.4375),
    'vpanel':   (0.1875, 0.3125, 0.25, 0.4375),
    'plate':    (0.1875, 0.25, 0.25, 0.3125),
    'vhead1':   (0.25, 0.40625, 0.375, 0.4375),
    'vhead2':   (0.25, 0.375, 0.375, 0.40625),
    'cloth':    (0.25, 0.25, 0.375, 0.375),
    'hazard':   (0.375, 0.3125, 0.5, 0.4375),
    'redwhite': (0.5, 0.3125, 0.75, 0.4375),
    'pcrate':   (0.75, 0.3125, 0.875, 0.4375),
    'leaf':     (0.875, 0.3125, 1.0, 0.4375),
    'manhole':  (0.375, 0.1875, 0.5, 0.3125),
    'drain':    (0.5, 0.1875, 0.625, 0.3125),
    'noentry':  (0.625, 0.1875, 0.75, 0.3125),
    'crossing': (0.75, 0.1875, 0.875, 0.3125),
    'basket':   (0.875, 0.1875, 1.0, 0.3125),
    'planks':   (0.0, 0.1875, 0.25, 0.25),
    'bark':     (0.25, 0.1875, 0.375, 0.25),
    'lens':     (0.0, 0.125, 0.0625, 0.1875),
    'lamp':     (0.0625, 0.125, 0.125, 0.1875),
    'button':   (0.125, 0.125, 0.1875, 0.1875),
    'dial':     (0.1875, 0.125, 0.25, 0.1875),
    'post':     (0.25, 0.125, 0.3125, 0.1875),
    'binplate': (0.3125, 0.125, 0.375, 0.1875),
    'fan':      (0.375, 0.0625, 0.5, 0.1875),
    'acvent':   (0.5, 0.0625, 0.625, 0.1875),
    'soil':     (0.625, 0.0625, 0.75, 0.1875),
    'chalk':    (0.75, 0.0625, 0.875, 0.1875),
    'sackmark': (0.875, 0.0625, 0.9375, 0.1875),
    'white':    (0.9375, 0.0, 1.0, 0.0625),
}
PERIODIC = {'conc', 'paint', 'plastic', 'wall', 'hoard', 'hazard', 'redwhite'}
MARGIN_U = {k: 0.07 for k in PERIODIC}
MARGIN_U['hoard'] = 0.02     # the hoarding tile maps exactly [0, 1]; a little bleed room
MARGIN_U['wall'] = 0.12      # the pillar samples up to 0.11 past either end of the period
DEFAULT_MARGIN = 0.02
# Wall-type grime maps: side faces use q in [0, SIDE_TOP] for the model's height; upward faces use
# the clean band [TOP0, TOP1].
SIDE_TOP, TOP0, TOP1 = 0.89, 0.92, 0.99


def margins(name):
    return MARGIN_U.get(name, DEFAULT_MARGIN), DEFAULT_MARGIN


def reg_uv(name, s, t, margin=None):
    u0, v0, u1, v1 = REG[name]
    mu, mv = margins(name) if margin is None else (margin, margin)
    if name not in PERIODIC: s = min(max(s, 0.0), 1.0)
    t = min(max(t, 0.0), 1.0)
    s = mu + s * (1 - 2 * mu); t = mv + t * (1 - 2 * mv)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


# ---------------------------------------------------------------- painting helpers
def region(name):
    """Pixel slice of a region and its parameter grids: P, Q in [0, 1] over the mapped area (they
    run past 0 and 1 in the margins, so periodic content fills them seamlessly)."""
    u0, v0, u1, v1 = REG[name]
    x0, x1 = int(round(u0 * AT)), int(round(u1 * AT)); y0, y1 = int(round((1 - v1) * AT)), int(round((1 - v0) * AT))
    w, h = x1 - x0, y1 - y0
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, 1 - (np.arange(h) + 0.5) / h)
    mu, mv = margins(name)
    P = (U - mu) / (1 - 2 * mu); Q = (V - mv) / (1 - 2 * mv)
    return (slice(y0, y1), slice(x0, x1)), P.astype(np.float32), Q.astype(np.float32)


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def blend(img, mask, col, alpha=1.0):
    m = (np.clip(mask, 0, 1) * alpha)[..., None]
    return img * (1 - m) + np.array(col, np.float32)[None, None, :] * m


def pnoise(P, Q, cx, cy, rng, wrap_q=False):
    """Smooth value noise, periodic in P (cx cells per unit), and in Q when wrap_q."""
    R = rng.random((cy + 1, cx)).astype(np.float32)
    if wrap_q: R[cy] = R[0]
    x = (P % 1.0) * cx
    y = ((Q % 1.0) if wrap_q else np.clip(Q, 0, 0.9999)) * cy
    x0 = np.floor(x).astype(int); fx = x - x0; x0 %= cx; x1 = (x0 + 1) % cx
    y0 = np.clip(np.floor(y).astype(int), 0, cy - 1); fy = y - y0; y1 = y0 + 1
    sx = fx * fx * (3 - 2 * fx); sy = fy * fy * (3 - 2 * fy)
    a = R[y0, x0] + (R[y0, x1] - R[y0, x0]) * sx
    b = R[y1, x0] + (R[y1, x1] - R[y1, x0]) * sx
    return a + (b - a) * sy


def fbm(P, Q, cx, cy, rng, octaves=3, wrap_q=False):
    tot = 0; amp = 1; acc = 0
    for o in range(octaves):
        acc = acc + amp * pnoise(P, Q, cx * 2 ** o, cy * 2 ** o, rng, wrap_q)
        tot += amp; amp *= 0.5
    return acc / tot


def specks(sub, weight, rng, count, rmin, rmax, col, alpha, periodic=False, period_px=None, aspect=1.0):
    """Soft round specks where weight (same shape as sub) is high. periodic: also drawn one period
    left and right, so the region wraps."""
    h, w = weight.shape
    ys = rng.integers(0, h, count); xs = rng.integers(0, w, count)
    keep = rng.random(count) < np.clip(weight[ys, xs], 0, 1) ** 1.2
    col = np.array(col, np.float32)
    for y, x in zip(ys[keep], xs[keep]):
        r = rng.uniform(rmin, rmax); rv = max(r * aspect, 0.5)
        for dx in ((0, -period_px, period_px) if periodic else (0,)):
            cx = x + dx
            x0, x1 = max(0, int(cx - r - 1)), min(w, int(cx + r + 2))
            if x1 <= x0: continue
            y0, y1 = max(0, int(y - rv - 1)), min(h, int(y + rv + 2))
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d = np.sqrt(((yy - y) * r / rv) ** 2 + (xx - cx) ** 2)
            m = (np.clip(r + 0.5 - d, 0, 1) * alpha)[..., None]
            sub[y0:y1, x0:x1] = sub[y0:y1, x0:x1] * (1 - m) + col[None, None] * m


def period_px(name, P):
    return P.shape[1] * (1 - 2 * margins(name)[0])


def blobs(sub, P, Q, rng, centres, rad, col, alpha, aspect=1.0, rim=None, lumps=5, periodic=True):
    """Irregular painted patches (rust, chips, stains): each a cluster of overlapping soft discs.
    centres: [(p, q)], rad: radius in P units (Q radius = rad * aspect)."""
    acc = np.zeros(P.shape, np.float32)
    for (pc, qc) in centres:
        for k in range(lumps):
            r = rad * rng.uniform(0.35, 1.0)
            pp = pc + rng.normal(0, rad * 0.7); qq = qc + rng.normal(0, rad * 0.7 * aspect)
            dp = P - pp
            if periodic: dp = (dp + 0.5) % 1.0 - 0.5
            d = np.sqrt(dp ** 2 + ((Q - qq) / aspect) ** 2)
            acc = np.maximum(acc, ss(r, r * 0.55, d))
    if rim is not None:
        edge = np.clip(acc * (1 - acc) * 4, 0, 1)
        sub = blend(sub, edge, rim, alpha)
    return blend(sub, acc, col, alpha), acc


# ---------------------------------------------------------------- weathering maps
GRIME = (0.70, 0.63, 0.54)
DARK_GRIME = (0.56, 0.50, 0.43)
RUST_DARK = (0.50, 0.31, 0.20)
RUST = (0.74, 0.47, 0.30)
MOSS = (0.62, 0.68, 0.46)


def _bottom(sub, P, Q, rng, strength, height=0.17, col=GRIME, name='conc'):
    edge = height * (0.75 + 0.5 * fbm(P, Q * 0 + 0.5, 9, 1, rng))
    g = ss(edge, 0.0, Q) * (Q < SIDE_TOP + 0.02)
    nz = fbm(P, Q, 30, 6, rng)
    g = g * (0.55 + 0.6 * nz)
    sub = blend(sub, g, col, strength)
    specks(sub, g * 1.2, rng, 3500, 0.6, 1.7, DARK_GRIME, 0.45, True, period_px(name, P))
    return sub


def _top_band(sub, P, Q, rng, base=0.97, var=0.03):
    top = (Q > SIDE_TOP + 0.01)
    t = base + var * fbm(P, Q, 16, 4, rng)
    sub[top] = np.repeat(t[top][:, None], 3, 1)
    return sub


def paint_conc(img, rng):
    sl, P, Q = region('conc')
    sub = np.ones(P.shape + (3,), np.float32)
    mott = fbm(P, Q, 10, 3, rng, 4)
    sub *= (0.88 + 0.12 * mott)[..., None]
    sub = blend(sub, ss(0.55, 0.8, fbm(P, Q, 6, 2, rng)), (0.95, 0.93, 0.90), 0.5)   # warm/cool patches
    # drip streaks below the top edges, uneven columns
    col = pnoise(P, P * 0, 70, 1, rng) * 0.6 + pnoise(P, P * 0, 23, 1, rng) * 0.4
    fade = ss(0.15, 0.85, Q) * (0.6 + 0.4 * fbm(P, Q, 40, 8, rng))
    sub = blend(sub, ss(0.55, 0.85, col) * fade * (Q < SIDE_TOP), (0.74, 0.72, 0.68), 0.55)
    # pits and aggregate
    specks(sub, np.ones(P.shape), rng, 5000, 0.5, 1.1, (0.60, 0.58, 0.55), 0.45, True, period_px('conc', P))
    specks(sub, np.ones(P.shape), rng, 1200, 0.6, 1.3, (1.0, 1.0, 0.98), 0.35, True, period_px('conc', P))
    # damp, grime and moss at the base
    sub = _bottom(sub, P, Q, rng, 0.6, 0.18, GRIME, 'conc')
    g = ss(0.10, 0.0, Q) * ss(0.5, 0.75, fbm(P, Q, 24, 3, rng))
    sub = blend(sub, g, MOSS, 0.55)
    specks(sub, ss(0.14, 0.0, Q), rng, 900, 0.8, 2.2, (0.52, 0.60, 0.40), 0.55, True, period_px('conc', P))
    sub = _top_band(sub, P, Q, rng, 0.95, 0.05)
    specks(sub, (Q > SIDE_TOP + 0.01).astype(np.float32), rng, 1200, 0.5, 1.2, (0.7, 0.68, 0.64), 0.4, True, period_px('conc', P))
    img[sl] = sub


def paint_paint(img, rng):
    sl, P, Q = region('paint')
    sub = np.ones(P.shape + (3,), np.float32)
    sub *= (0.93 + 0.07 * fbm(P, Q, 8, 3, rng, 3))[..., None]
    pp = period_px('paint', P)
    aspect = (P.shape[1] / P.shape[0])   # Q units are this many times larger than P units per pixel
    # rust: clusters weighted to the bottom and the top edge, with streaks running down
    cents = []
    for k in range(38):
        q = rng.random() ** 1.8 * SIDE_TOP if rng.random() < 0.7 else SIDE_TOP - rng.random() * 0.12
        cents.append((rng.random(), q))
    sub, acc = blobs(sub, P, Q, rng, cents, 0.0042, RUST, 0.85, aspect, rim=RUST_DARK, lumps=4)
    for (pc, qc) in cents[::4]:
        dp = (P - pc + 0.5) % 1.0 - 0.5
        L = rng.uniform(0.05, 0.18)
        m = ss(0.0035, 0.0, np.abs(dp)) * ss(qc - L, qc, Q) * (Q < qc)
        sub = blend(sub, m, (0.84, 0.66, 0.52), 0.3)
    # chipped paint: small darker flecks with a light edge
    cents = [(rng.random(), rng.random() * SIDE_TOP) for _ in range(70)]
    sub, _ = blobs(sub, P, Q, rng, cents, 0.0025, (0.76, 0.74, 0.72), 0.7, aspect, rim=(0.58, 0.55, 0.52), lumps=3)
    # scratches
    for k in range(25):
        p0, q0 = rng.random(), rng.random() * SIDE_TOP
        ang = rng.uniform(-0.6, 0.6); L = rng.uniform(0.008, 0.03)
        dp = (P - p0 + 0.5) % 1.0 - 0.5; dq = (Q - q0) / aspect
        along = dp * math.cos(ang) + dq * math.sin(ang); across = -dp * math.sin(ang) + dq * math.cos(ang)
        m = ss(0.0012, 0.0, np.abs(across)) * (np.abs(along) < L)
        sub = blend(sub, m, (0.82, 0.80, 0.78), 0.6)
    sub = _bottom(sub, P, Q, rng, 0.55, 0.16, GRIME, 'paint')
    specks(sub, ss(0.12, 0.0, Q), rng, 900, 0.8, 1.8, RUST, 0.5, True, pp)
    sub = _top_band(sub, P, Q, rng, 0.96, 0.04)
    specks(sub, (Q > SIDE_TOP + 0.01).astype(np.float32), rng, 500, 0.6, 1.6, RUST, 0.5, True, pp)
    img[sl] = sub


def paint_plastic(img, rng):
    sl, P, Q = region('plastic')
    sub = np.ones(P.shape + (3,), np.float32)
    sub *= (0.95 + 0.05 * fbm(P, Q, 8, 3, rng))[..., None]
    aspect = (P.shape[1] / P.shape[0])
    for k in range(120):
        p0, q0 = rng.random(), rng.random() * SIDE_TOP
        ang = rng.uniform(-PI_4, PI_4); L = rng.uniform(0.006, 0.025)
        dp = (P - p0 + 0.5) % 1.0 - 0.5; dq = (Q - q0) / aspect
        along = dp * math.cos(ang) + dq * math.sin(ang); across = -dp * math.sin(ang) + dq * math.cos(ang)
        m = ss(0.0015, 0.0, np.abs(across)) * (np.abs(along) < L)
        sub = blend(sub, m, (0.84, 0.83, 0.82), 0.5)
    sub = _bottom(sub, P, Q, rng, 0.4, 0.14, GRIME, 'plastic')
    sub = _top_band(sub, P, Q, rng, 0.97, 0.03)
    img[sl] = sub


PI_4 = math.pi / 4


def _grain(P, Q, rng, freq=22, wob=0.06):
    a = rng.uniform(0, 6)
    g = np.sin((Q * freq + wob * freq * np.sin(P * 7 + a) + 0.5 * np.sin(P * 23 + Q * 3)) * 2 * math.pi)
    g2 = fbm(P, Q, 40, 4, rng)
    return 0.5 + 0.5 * g, g2


def paint_wood(img, rng):
    """One board, grain along P: darker edges, a knot, nail heads near the ends."""
    sl, P, Q = region('wood')
    sub = np.ones(P.shape + (3,), np.float32)
    g, g2 = _grain(P, Q, rng, 9, 0.08)
    sub *= (0.86 + 0.08 * g + 0.06 * g2)[..., None]
    streak = pnoise(P * 0, Q, 1, 40, rng)
    sub *= (0.94 + 0.06 * streak)[..., None]
    for (pc, qc) in ((0.33, 0.62), (0.78, 0.3)):
        d = np.sqrt(((P - pc) * 4) ** 2 + (Q - qc) ** 2)
        sub = blend(sub, ss(0.09, 0.05, d), (0.62, 0.48, 0.36), 0.8)
        sub = blend(sub, ss(0.025, 0.0, np.abs(d - 0.11)), (0.74, 0.60, 0.46), 0.6)
    edge = np.minimum(np.minimum(Q, 1 - Q), np.minimum(P, 1 - P) * 0.4)
    sub = blend(sub, ss(0.10, 0.0, edge), (0.66, 0.54, 0.42), 0.8)
    sub = blend(sub, ss(0.025, 0.0, edge), (0.48, 0.38, 0.30), 0.8)
    # weathered grey patches
    sub = blend(sub, ss(0.6, 0.8, fbm(P, Q, 5, 2, rng)), (0.86, 0.86, 0.84), 0.45)
    for pc in (0.06, 0.94):
        for qc in (0.3, 0.7):
            d = np.sqrt(((P - pc) * 6) ** 2 + (Q - qc) ** 2)
            sub = blend(sub, ss(0.07, 0.04, d), (0.32, 0.30, 0.30), 1.0)
            sub = blend(sub, ss(0.05, 0.0, np.sqrt(((P - pc + 0.003) * 6) ** 2 + (Q - qc - 0.015) ** 2)), (0.6, 0.58, 0.56), 0.6)
    img[sl] = sub


def paint_planks(img, rng):
    """Three planks across Q (crate sides), grain along P, gaps between them."""
    sl, P, Q = region('planks')
    sub = np.ones(P.shape + (3,), np.float32)
    k = np.floor(Q * 3).clip(0, 2); kq = (Q * 3) % 1.0
    g, g2 = _grain(P, kq, rng, 6, 0.1)
    tone = np.choose(k.astype(int), [0.97, 0.90, 1.0])
    sub *= (tone * (0.86 + 0.09 * g + 0.05 * g2))[..., None]
    sub = blend(sub, ss(0.08, 0.0, np.minimum(kq, 1 - kq)), (0.52, 0.40, 0.30), 0.9)
    sub = blend(sub, ss(0.6, 0.85, fbm(P, Q, 6, 3, rng)), (0.86, 0.85, 0.82), 0.4)
    for pc in (0.05, 0.95):
        for qc in (1 / 6, 0.5, 5 / 6):
            d = np.sqrt(((P - pc) * 2) ** 2 + (Q - qc) ** 2)
            sub = blend(sub, ss(0.025, 0.015, d), (0.32, 0.30, 0.30), 1.0)
    img[sl] = sub


def paint_pwood(img, rng):
    """Painted boards (pickets): faint grain through the paint, peeled patches, grime specks."""
    sl, P, Q = region('pwood')
    sub = np.ones(P.shape + (3,), np.float32)
    g, g2 = _grain(P, Q, rng, 7, 0.05)
    sub *= (0.93 + 0.04 * g + 0.03 * g2)[..., None]
    aspect = P.shape[1] / P.shape[0]
    cents = [(rng.random(), rng.random()) for _ in range(12)]
    sub, acc = blobs(sub, P, Q, rng, cents, 0.02, (0.80, 0.66, 0.52), 0.85, aspect, rim=(0.62, 0.52, 0.44), lumps=4, periodic=False)
    edge = np.minimum(Q, 1 - Q)
    sub = blend(sub, ss(0.12, 0.0, edge) * ss(0.4, 0.7, fbm(P, Q, 30, 4, rng)), (0.80, 0.68, 0.56), 0.6)
    specks(sub, ss(0.2, 0.0, P), rng, 900, 0.6, 1.6, DARK_GRIME, 0.5)
    sub = blend(sub, ss(0.12, 0.0, P) * (0.5 + 0.5 * fbm(P, Q, 20, 4, rng)), GRIME, 0.5)
    img[sl] = sub


def paint_surfaces(img, rng):
    paint_conc(img, rng); paint_paint(img, rng); paint_plastic(img, rng)
    paint_wood(img, rng); paint_planks(img, rng); paint_pwood(img, rng)
