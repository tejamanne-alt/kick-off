# Painted details of the street atlas: the block wall, the site hoarding, stripes, signs, lamp
# lenses, the vending fronts and the small icons. No text anywhere: icons and simple shapes only.
import math
import numpy as np
from kit_street_atlas import (region, ss, blend, pnoise, fbm, specks, blobs, period_px, paint_surfaces,
                              AT, GRIME, DARK_GRIME, RUST, RUST_DARK, MOSS)

PI = math.pi


# ---------------------------------------------------------------- shape helpers (distances)
def d_seg(X, Y, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
    return np.sqrt((X - ax - t * dx) ** 2 + (Y - ay - t * dy) ** 2)


def d_box(X, Y, cx, cy, hw, hh, r=0.0):
    qx = np.abs(X - cx) - hw + r; qy = np.abs(Y - cy) - hh + r
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - r


def d_circ(X, Y, cx, cy, r):
    return np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) - r


def fill(d, aa=0.006):
    return ss(aa, -aa, d)


def sq(name):
    sl, P, Q = region(name)
    return sl, P, Q, 2 * P - 1, 2 * Q - 1


def figure(X, Y, cx, cy, s, walking=True):
    """A simple pictogram person (head, body, arms, legs) as a mask."""
    X = (X - cx) / s; Y = (Y - cy) / s
    m = fill(d_circ(X, Y, 0.06, 0.78, 0.15), 0.02)
    lw = 0.085
    if walking:
        segs = [((0.03, 0.55), (-0.04, 0.05)), ((0.0, 0.42), (0.26, 0.2)), ((0.0, 0.42), (-0.22, 0.22)),
                ((-0.04, 0.05), (0.24, -0.38)), ((-0.04, 0.05), (-0.26, -0.36)), ((-0.26, -0.36), (-0.36, -0.30))]
    else:
        segs = [((0.0, 0.55), (0.0, 0.05)), ((0.0, 0.45), (0.2, 0.08)), ((0.0, 0.45), (-0.2, 0.08)),
                ((0.0, 0.05), (0.1, -0.38)), ((0.0, 0.05), (-0.1, -0.38))]
    for a, b in segs:
        m = np.maximum(m, fill(d_seg(X, Y, a, b) - lw, 0.02))
    return m


def weather(sub, X, Y, rng, dirt=0.35, scratches=20):
    sub = blend(sub, ss(-0.4, -1.0, Y) * (0.5 + 0.5 * fbm((X + 1) / 2, (Y + 1) / 2, 6, 6, rng)), GRIME, dirt)
    for k in range(scratches):
        x0, y0 = rng.uniform(-0.8, 0.8, 2); ang = rng.uniform(0, PI); L = rng.uniform(0.04, 0.16)
        d = d_seg(X, Y, (x0, y0), (x0 + L * math.cos(ang), y0 + L * math.sin(ang)))
        sub = blend(sub, ss(0.008, 0.0, d), (0.85, 0.85, 0.84), 0.35)
    return sub


# ---------------------------------------------------------------- block wall (periodic, 2 m)
def paint_wall(img, rng):
    sl, P, Q = region('wall')
    x = -1 + 2 * P; z = 1.8 * Q
    zb, bh, bw = 0.10, 0.2, 0.4
    k = np.floor((z - zb) / bh); kz = (z - zb) / bh - k
    off = 0.2 * (np.mod(k, 2))
    jj = np.floor((x - off + 1) / bw); jx = (x - off + 1) / bw - jj
    tbl = rng.uniform(0.86, 0.99, (16, 5))
    tone = tbl[np.mod(k, 16).astype(int), np.mod(jj, 5).astype(int)]
    sub = np.ones(P.shape + (3,), np.float32) * tone[..., None]
    warm = rng.uniform(-1, 1, (16, 5))[np.mod(k, 16).astype(int), np.mod(jj, 5).astype(int)]
    sub *= (1 + 0.025 * warm[..., None] * np.array((1.0, 0.2, -1.0))[None, None])
    sub *= (0.92 + 0.08 * fbm(P, Q, 48, 20, rng, 3))[..., None]
    specks(sub, np.ones(P.shape), rng, 9000, 0.5, 1.1, (0.62, 0.60, 0.57), 0.5, True, period_px('wall', P))
    # bevelled block edges: light top lip, darker bottom, recessed mortar joints
    dz_top = (1 - kz) * bh; dz_bot = kz * bh; dx = np.minimum(jx, 1 - jx) * bw
    sub = blend(sub, ss(0.022, 0.008, dz_top) * (dx > 0.008), (1.0, 0.99, 0.97), 0.55)
    sub = blend(sub, ss(0.02, 0.006, dz_bot), (0.70, 0.68, 0.64), 0.5)
    sub = blend(sub, ss(0.016, 0.006, dx) * (jx > 0.5), (0.74, 0.72, 0.68), 0.4)
    joint = np.maximum(ss(0.007, 0.003, np.minimum(dz_top, dz_bot)), ss(0.007, 0.003, dx))
    sub = blend(sub, joint, (0.56, 0.54, 0.50), 0.95)
    # chipped block corners
    cents = [(rng.random(), (0.1 + 0.2 * rng.integers(0, 8) + 0.2 * rng.random()) / 1.8) for _ in range(26)]
    sub, _ = blobs(sub, P, Q, rng, cents, 0.004, (0.66, 0.64, 0.60), 0.8, 2.0 / 1.8, lumps=3)
    # the open blocks of the decorative course (k = 5): a lighter raised frame round each opening
    for cx in (-0.6, -0.2, 0.2, 0.6):
        d = np.sqrt((x - cx) ** 2 + (z - 1.2) ** 2)
        inb = (np.abs(x - cx) < 0.195) & (np.abs(z - 1.2) < 0.095)
        sub = blend(sub, inb * ss(0.012, 0.0, np.abs(d - 0.082)), (1.0, 0.99, 0.96), 0.6)
        sub = blend(sub, inb * ss(0.012, 0.0, np.abs(d - 0.097)), (0.70, 0.68, 0.64), 0.5)
        # a dirt streak washed down from each opening
        m = ss(0.035, 0.0, np.abs(x - cx + 0.01 * np.sin(z * 30))) * ss(0.6, 1.1, z) * (z < 1.13)
        sub = blend(sub, m * (0.5 + 0.5 * fbm(P, Q, 60, 30, rng)), (0.70, 0.67, 0.62), 0.5)
    # streaks below the cap, damp and moss at the foot, chalky efflorescence
    col = pnoise(P, P * 0, 60, 1, rng) * 0.6 + pnoise(P, P * 0, 17, 1, rng) * 0.4
    m = ss(0.55, 0.85, col) * ss(0.7, 1.5, z) * (z < 1.505)
    sub = blend(sub, m * (0.6 + 0.4 * fbm(P, Q, 50, 20, rng)), (0.70, 0.68, 0.64), 0.55)
    g = ss(0.55 + 0.15 * fbm(P, Q * 0, 12, 1, rng), 0.0, z)
    sub = blend(sub, g * (0.5 + 0.6 * fbm(P, Q, 40, 32, rng)), GRIME, 0.55)
    sub = blend(sub, ss(0.24, 0.10, z) * ss(0.45, 0.7, fbm(P, Q, 30, 24, rng)), MOSS, 0.6)
    specks(sub, ss(0.35, 0.1, z), rng, 2500, 0.7, 2.0, (0.50, 0.58, 0.40), 0.55, True, period_px('wall', P))
    sub = blend(sub, ss(0.62, 0.8, fbm(P, Q, 9, 4, rng)) * ss(0.9, 0.2, z), (1.0, 1.0, 0.98), 0.45)
    img[sl] = sub


# ---------------------------------------------------------------- site hoarding (periodic, 3 m)
def paint_hoard(img, rng):
    sl, P, Q = region('hoard')
    x = -1.5 + 3 * P; z = 2.6 * Q
    w = 2 * PI / 3.0
    sky_hi, sky_lo = np.array((0.74, 0.86, 0.90)), np.array((0.95, 0.93, 0.86))
    t = ss(0.9, 2.4, z)[..., None]
    sub = sky_lo[None, None] * (1 - t) + sky_hi[None, None] * t
    # sun with a soft halo
    d = np.sqrt((x + 0.72) ** 2 + (z - 1.82) ** 2)
    sub = blend(sub, ss(0.48, 0.3, d), (0.98, 0.90, 0.74), 0.6)
    sub = blend(sub, fill(d - 0.27, 0.008), (0.98, 0.78, 0.55), 1.0)
    # clouds
    for (cx, cz, s) in ((0.35, 2.05, 1.0), (1.15, 1.72, 0.7), (-1.25, 2.2, 0.8)):
        m = np.zeros(P.shape, np.float32)
        for (ox, oz, r) in ((-0.16, 0, 0.09), (0, 0.04, 0.13), (0.17, 0.0, 0.1), (0.05, -0.04, 0.1)):
            dx = (x - cx - ox * s + 1.5) % 3.0 - 1.5
            m = np.maximum(m, fill(np.sqrt(dx ** 2 + (z - cz - oz * s) ** 2) - r * s, 0.008))
        m = np.maximum(m, fill(d_box(((x - cx + 1.5) % 3.0 - 1.5), z, 0, cz - 0.05 * s, 0.22 * s, 0.05 * s, 0.05 * s), 0.008))
        sub = blend(sub, m, (0.99, 0.98, 0.95), 1.0)
    # a crane on the skyline (site theme): mast, jib, counter-jib, hook
    cr = (0.90, 0.60, 0.28)
    mx = 0.88
    mast = np.minimum(d_seg(x, z, (mx - 0.05, 0.9), (mx - 0.05, 2.12)), d_seg(x, z, (mx + 0.05, 0.9), (mx + 0.05, 2.12)))
    for zz in np.arange(0.95, 2.1, 0.12):
        mast = np.minimum(mast, d_seg(x, z, (mx - 0.05, zz), (mx + 0.05, zz + 0.12)))
    jib = np.minimum(d_seg(x, z, (mx - 0.45, 2.14), (mx + 0.62, 2.14)), d_seg(x, z, (mx - 0.45, 2.2), (mx + 0.25, 2.2)))
    jib = np.minimum(jib, d_seg(x, z, (mx, 2.12), (mx, 2.36)))
    jib = np.minimum(jib, np.minimum(d_seg(x, z, (mx, 2.36), (mx + 0.62, 2.15)), d_seg(x, z, (mx, 2.36), (mx - 0.45, 2.2))))
    sub = blend(sub, fill(np.minimum(mast, jib) - 0.012, 0.006), cr, 1.0)
    sub = blend(sub, fill(d_box(x, z, mx - 0.38, 2.11, 0.07, 0.05, 0.01), 0.006), (0.45, 0.45, 0.48), 1.0)
    sub = blend(sub, fill(d_seg(x, z, (mx + 0.45, 2.14), (mx + 0.45, 1.75)) - 0.005, 0.004), (0.35, 0.35, 0.38), 1.0)
    sub = blend(sub, fill(d_box(x, z, mx + 0.45, 1.72, 0.035, 0.03, 0.01), 0.005), (0.35, 0.35, 0.38), 1.0)
    # far and near hills
    hf = 1.12 + 0.16 * np.sin(w * x + 0.6) + 0.07 * np.sin(3 * w * x + 1.3)
    sub = blend(sub, fill(z - hf, 0.006), (0.62, 0.77, 0.64), 1.0)
    hn = 0.80 + 0.11 * np.sin(2 * w * x + 2.0) + 0.04 * np.sin(5 * w * x + 0.4)
    # trees on the near hill line
    for tx in (-1.22, -1.02, 0.42, 1.28):
        th = 0.80 + 0.11 * math.sin(2 * w * tx + 2.0) + 0.04 * math.sin(5 * w * tx + 0.4)
        sub = blend(sub, fill(d_box(x, z, tx, th + 0.06, 0.012, 0.08), 0.005), (0.48, 0.38, 0.30), 1.0)
        sub = blend(sub, fill(d_circ(x, z, tx, th + 0.2, 0.1), 0.006), (0.30, 0.52, 0.38), 1.0)
        sub = blend(sub, fill(d_circ(x, z, tx - 0.03, th + 0.23, 0.05), 0.006) * 0.5, (0.42, 0.64, 0.46), 1.0)
    # a little house on the hill
    hx, hz = -0.15, 0.86
    sub = blend(sub, fill(d_box(x, z, hx, hz + 0.1, 0.16, 0.11), 0.005), (0.97, 0.90, 0.78), 1.0)
    roof = np.maximum(z - (hz + 0.38 - 1.1 * np.abs(x - hx)), (hz + 0.2) - z)
    sub = blend(sub, fill(roof, 0.005), (0.82, 0.44, 0.33), 1.0)
    sub = blend(sub, fill(d_box(x, z, hx + 0.06, hz + 0.06, 0.035, 0.07), 0.004), (0.50, 0.38, 0.32), 1.0)
    sub = blend(sub, fill(d_box(x, z, hx - 0.07, hz + 0.12, 0.04, 0.035), 0.004), (0.98, 0.84, 0.50), 1.0)
    sub = blend(sub, fill(z - hn, 0.006), (0.44, 0.64, 0.48), 1.0)
    # bands: teal at the foot and the top, a cream pinstripe, hazard stripes along the kick strip
    band = (0.33, 0.56, 0.52)
    sub = blend(sub, fill(z - 0.44, 0.004), (0.95, 0.93, 0.86), 1.0)
    sub = blend(sub, fill(z - 0.40, 0.004), band, 1.0)
    sub = blend(sub, fill(2.42 - z, 0.004), (0.95, 0.93, 0.86), 1.0)
    sub = blend(sub, fill(2.46 - z, 0.004), band, 1.0)
    st = 0.5 + 0.5 * np.sin(2 * PI * (P * 12 + z / 0.25))
    hz_ = fill(z - 0.16, 0.004)
    sub = blend(sub, hz_, (0.94, 0.76, 0.24), 1.0)
    sub = blend(sub, hz_ * ss(0.45, 0.55, st), (0.16, 0.16, 0.17), 1.0)
    # joints between the sheets (x = 0 and the tile ends)
    dj = np.minimum(np.abs(x), 1.5 - np.abs(x))
    sub = blend(sub, ss(0.012, 0.0, dj), (0.55, 0.55, 0.55), 0.5)
    # weathering: rain streaks, splashes at the foot, scuffs, rust weeping from the bolts
    col = pnoise(P, P * 0, 80, 1, rng) * 0.6 + pnoise(P, P * 0, 26, 1, rng) * 0.4
    m = ss(0.58, 0.85, col) * ss(0.6, 2.4, z)
    sub = blend(sub, m * (0.5 + 0.5 * fbm(P, Q, 60, 20, rng)), (0.76, 0.74, 0.70), 0.45)
    g = ss(0.42 + 0.12 * fbm(P, Q * 0, 14, 1, rng), 0.0, z)
    sub = blend(sub, g * (0.5 + 0.6 * fbm(P, Q, 40, 10, rng)), GRIME, 0.6)
    specks(sub, ss(0.5, 0.05, z), rng, 4000, 0.7, 2.2, DARK_GRIME, 0.55, True, period_px('hoard', P))
    for bx in (-1.5, -0.75, 0.0, 0.75, 1.5):
        for bz in (0.3, 2.5):
            m = ss(0.01, 0.0, np.abs(x - bx - 0.06)) * ss(bz - 0.25, bz, z) * (z < bz)
            sub = blend(sub, m, (0.80, 0.58, 0.44), 0.5)
    img[sl] = sub


# ---------------------------------------------------------------- stripes
def paint_hazard(img, rng):
    """Yellow and black diagonal stripes for the pole's guard sleeve: 6 turns around, 45 degrees
    on a 0.19 m radius, 1.8 m tall sleeve."""
    sl, P, Q = region('hazard')
    n, a = 6, 9.0
    st = 0.5 + 0.5 * np.sin(2 * PI * (P * n + Q * a))
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.94, 0.76, 0.26))
    sub = blend(sub, ss(0.42, 0.58, st), (0.15, 0.15, 0.16), 1.0)
    sub *= (0.92 + 0.08 * fbm(P, Q, 12, 12, rng))[..., None]
    cents = [(rng.random(), rng.random()) for _ in range(40)]
    sub, _ = blobs(sub, P, Q, rng, cents, 0.008, (0.62, 0.62, 0.60), 0.8, 1.0, rim=(0.40, 0.38, 0.36), lumps=3)
    sub = blend(sub, ss(0.25, 0.0, Q) * (0.5 + 0.5 * fbm(P, Q, 20, 8, rng)), GRIME, 0.6)
    specks(sub, ss(0.3, 0.0, Q), rng, 1500, 0.6, 1.6, DARK_GRIME, 0.5, True, period_px('hazard', P))
    img[sl] = sub


def paint_redwhite(img, rng):
    """Red and white diagonal stripes for the barrier boards (5 periods along a 1.7 m board)."""
    sl, P, Q = region('redwhite')
    n, a = 5, 0.6
    st = 0.5 + 0.5 * np.sin(2 * PI * (P * n + Q * a))
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.95, 0.93, 0.88))
    sub = blend(sub, ss(0.45, 0.55, st), (0.80, 0.24, 0.20), 1.0)
    sub *= (0.93 + 0.07 * fbm(P, Q, 20, 4, rng))[..., None]
    for k in range(60):
        p0, q0 = rng.random(), rng.random(); ang = rng.uniform(-0.4, 0.4); L = rng.uniform(0.01, 0.05)
        dp = (P - p0 + 0.5) % 1.0 - 0.5; dq = (Q - q0) * 0.12
        along = dp * math.cos(ang) + dq * math.sin(ang); across = -dp * math.sin(ang) + dq * math.cos(ang)
        sub = blend(sub, ss(0.0015, 0.0, np.abs(across)) * (np.abs(along) < L), (0.72, 0.70, 0.68), 0.5)
    sub = blend(sub, ss(0.12, 0.0, np.minimum(Q, 1 - Q)), (0.62, 0.58, 0.54), 0.55)
    sub = blend(sub, ss(0.5, 0.0, Q) * (0.4 + 0.6 * fbm(P, Q, 30, 4, rng)), GRIME, 0.45)
    img[sl] = sub


# ---------------------------------------------------------------- signs and lamps
def paint_signs(img, rng):
    sl, P, Q, X, Y = sq('noentry')
    r = np.sqrt(X * X + Y * Y)
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.74, 0.74, 0.72))
    sub = blend(sub, fill(r - 0.985, 0.01), (0.95, 0.94, 0.90), 1.0)
    red = np.array((0.80, 0.19, 0.16)) * (0.94 + 0.06 * fbm(P, Q, 6, 6, rng))[..., None]
    m = fill(r - 0.90, 0.01)[..., None]
    sub = sub * (1 - m) + red * m
    sub = blend(sub, fill(d_box(X, Y, 0, 0, 0.64, 0.15, 0.04), 0.01), (0.96, 0.95, 0.92), 1.0)
    sub = weather(sub, X, Y, rng, 0.3, 14)
    specks(sub, ss(0.8, 1.0, r), rng, 120, 0.8, 2.0, RUST, 0.6)
    img[sl] = sub
    sl, P, Q, X, Y = sq('crossing')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.95, 0.94, 0.90))
    blue = np.array((0.22, 0.43, 0.70)) * (0.94 + 0.06 * fbm(P, Q, 6, 6, rng))[..., None]
    m = fill(d_box(X, Y, 0, 0, 0.92, 0.92, 0.1), 0.01)[..., None]
    sub = sub * (1 - m) + blue * m
    tri = np.maximum.reduce([-(Y + 0.62), (Y - 0.78) + 1.73 * X * 0.98, (Y - 0.78) - 1.73 * X * 0.98]) / 2
    sub = blend(sub, fill(tri, 0.006), (0.96, 0.95, 0.92), 1.0)
    for i in range(5):
        sub = blend(sub, fill(d_box(X, Y, -0.4 + 0.2 * i, -0.5, 0.06, 0.05, 0.01), 0.006), (0.14, 0.14, 0.16), 1.0)
    sub = blend(sub, figure(X, Y, 0.0, -0.08, 0.48), (0.14, 0.14, 0.16), 1.0)
    sub = weather(sub, X, Y, rng, 0.3, 14)
    img[sl] = sub
    # signal lens (unlit, the game lays its icons over it)
    sl, P, Q, X, Y = sq('lens')
    r = np.sqrt(X * X + Y * Y)
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.17, 0.18, 0.19))
    for rr in (0.25, 0.45, 0.65, 0.82):
        sub = blend(sub, ss(0.03, 0.0, np.abs(r - rr)), (0.24, 0.25, 0.26), 0.8)
    sub = blend(sub, ss(0.35, 0.05, np.sqrt((X + 0.32) ** 2 + (Y - 0.36) ** 2)), (0.42, 0.44, 0.46), 0.6)
    sub = blend(sub, ss(0.88, 1.0, r), (0.10, 0.10, 0.11), 1.0)
    img[sl] = sub
    # street lamp diffuser
    sl, P, Q, X, Y = sq('lamp')
    r = np.sqrt(X * X + Y * Y)
    sub = np.ones(P.shape + (3,), np.float32) * np.array((1.0, 0.97, 0.86))
    sub = blend(sub, ss(0.3, 1.0, r), (0.97, 0.86, 0.64), 0.8)
    a = np.arctan2(Y, X)
    sub = blend(sub, ss(0.75, 1.0, np.cos(a * 16)) * ss(0.2, 0.6, r), (0.95, 0.84, 0.66), 0.5)
    img[sl] = sub


def paint_ground(img, rng):
    # manhole cover: raised rim, a ring of studs, a wave band and a six-petal flower in the middle
    sl, P, Q, X, Y = sq('manhole')
    r = np.sqrt(X * X + Y * Y); a = np.arctan2(Y, X)
    low, high = 0.62, 1.0
    h = np.full(P.shape, low, np.float32)
    h = np.where(r > 0.86, high, h)
    h = np.where(np.abs(r - 0.83) < 0.025, 0.4, h)
    studs = np.zeros(P.shape, bool)
    for k in range(24):
        aa = 2 * PI * k / 24
        studs |= np.sqrt((X - 0.72 * np.cos(aa)) ** 2 + (Y - 0.72 * np.sin(aa)) ** 2) < 0.04
    h = np.where(studs, high, h)
    wave = (r > 0.44) & (r < 0.64) & (np.abs(np.sin(a * 12 + r * 18)) < 0.32)
    h = np.where(wave, 0.92, h)
    h = np.where(np.abs(r - 0.42) < 0.02, high, h)
    petal = r < 0.38 * (0.45 + 0.55 * np.abs(np.cos(3 * a)))
    h = np.where(petal, 0.95, h)
    h = np.where(petal & (r > 0.38 * (0.45 + 0.55 * np.abs(np.cos(3 * a))) - 0.035), 0.55, h)
    h = np.where(r < 0.09, high, h)
    sub = np.repeat(h[..., None], 3, 2)
    sub *= (0.9 + 0.1 * fbm(P, Q, 12, 12, rng))[..., None]
    sub = blend(sub, (h < 0.7) * ss(0.4, 0.8, fbm(P, Q, 16, 16, rng)), (0.76, 0.52, 0.38), 0.7)
    sub = blend(sub, ss(1.0, 1.03, r), (0.55, 0.53, 0.50), 1.0)
    specks(sub, np.ones(P.shape), rng, 1500, 0.5, 1.4, (0.40, 0.38, 0.36), 0.5)
    img[sl] = sub
    # drain grate: bars and dark slots, a cross bar, leaves caught in it
    sl, P, Q = region('drain')
    sub = np.ones(P.shape + (3,), np.float32) * 0.92
    inner = (np.abs(P - 0.5) < 0.42) & (np.abs(Q - 0.5) < 0.38)
    slot = inner & (((P - 0.08) * 11) % 1.0 < 0.55) & (np.abs(Q - 0.5) > 0.03)
    sub[slot] = (0.11, 0.10, 0.10)
    sub = blend(sub, inner & ~slot & (((P - 0.08) * 11) % 1.0 < 0.65), (0.70, 0.69, 0.67), 0.7)
    sub = blend(sub, ss(0.5, 0.75, fbm(P, Q, 10, 6, rng)) * ~slot, (0.76, 0.52, 0.38), 0.6)
    specks(sub, slot.astype(np.float32), rng, 300, 1.5, 3.5, (0.55, 0.40, 0.24), 0.9)
    specks(sub, np.ones(P.shape), rng, 800, 0.5, 1.3, (0.4, 0.38, 0.36), 0.5)
    sub = blend(sub, ss(0.05, 0.0, np.minimum(np.minimum(P, 1 - P), np.minimum(Q, 1 - Q))), (0.55, 0.53, 0.50), 0.8)
    img[sl] = sub
    # soil: dark clods, light pebbles
    sl, P, Q = region('soil')
    sub = np.ones(P.shape + (3,), np.float32) * (0.82 + 0.18 * fbm(P, Q, 16, 16, rng))[..., None]
    specks(sub, np.ones(P.shape), rng, 900, 1.0, 3.0, (0.6, 0.55, 0.5), 0.7)
    specks(sub, np.ones(P.shape), rng, 300, 1.2, 2.6, (1.0, 0.98, 0.94), 0.8)
    img[sl] = sub


def paint_cloth(img, rng):
    sl, P, Q = region('cloth')
    wv = 0.95 + 0.04 * np.sin(P * 520) * np.sin(Q * 520)
    sub = np.ones(P.shape + (3,), np.float32) * wv[..., None]
    sub *= (0.93 + 0.07 * fbm(P, Q, 8, 8, rng))[..., None]
    sub = blend(sub, ss(0.65, 0.85, fbm(P, Q, 5, 5, rng)), (0.86, 0.82, 0.76), 0.35)
    img[sl] = sub
    sl, P, Q = region('sackmark')
    wv = 0.93 + 0.06 * np.sin(P * 260) * np.sin(Q * 520)
    sub = np.ones(P.shape + (3,), np.float32) * wv[..., None]
    sub *= (0.9 + 0.1 * fbm(P, Q, 6, 8, rng))[..., None]
    X, Y = 2 * P - 1, (2 * Q - 1) * 2
    ink = (0.52, 0.42, 0.34)
    m = ss(0.06, 0.0, np.abs(np.sqrt(X * X + Y * Y) - 0.62))
    m = np.maximum(m, ss(0.05, 0.0, d_seg(X, Y, (0, -0.45), (0, 0.45))))
    for k in range(4):
        yy = -0.25 + 0.18 * k
        for sx in (-1, 1):
            d = np.sqrt(((X - sx * 0.12) / 0.6) ** 2 + ((Y - yy - 0.05) / 0.25) ** 2) * 0.25 - 0.05
            m = np.maximum(m, fill(d, 0.01))
    m *= ss(0.25, 0.55, fbm(P, Q, 20, 30, rng))
    sub = blend(sub, m, ink, 0.75)
    img[sl] = sub


def paint_leaf(img, rng):
    sl, P, Q = region('leaf')
    sub = np.ones(P.shape + (3,), np.float32) * 0.62
    h, w = P.shape
    for k in range(260):
        cx, cy = rng.random(), rng.random(); ang = rng.uniform(0, PI)
        L, W = rng.uniform(0.06, 0.12), rng.uniform(0.025, 0.045)
        dx, dy = P - cx, Q - cy
        u = dx * math.cos(ang) + dy * math.sin(ang); v = -dx * math.sin(ang) + dy * math.cos(ang)
        e = (u / L) ** 2 + (v / W) ** 2
        m = ss(1.0, 0.8, e)
        tone = rng.uniform(0.82, 1.0)
        shade = tone * (0.86 + 0.14 * ss(-L, L, u))
        col = np.stack([shade, shade, shade], -1)
        sub = sub * (1 - m[..., None]) + col * m[..., None]
        sub = blend(sub, m * ss(0.006, 0.0, np.abs(v)) * (np.abs(u) < L * 0.85), (0.75, 0.75, 0.75), 0.6)
    img[sl] = sub
    sl, P, Q = region('bark')
    sub = np.ones(P.shape + (3,), np.float32) * (0.8 + 0.2 * pnoise(P, Q * 0, 24, 1, rng))[..., None]
    sub = blend(sub, ss(0.6, 0.85, pnoise(P, Q, 30, 3, rng)), (0.55, 0.5, 0.46), 0.8)
    img[sl] = sub
    sl, P, Q = region('basket')
    a = (P * 14) % 1.0; b = (Q * 10 + 0.5 * (np.floor(P * 14) % 2)) % 1.0
    sub = np.ones(P.shape + (3,), np.float32) * 0.3
    strand = (np.abs(b - 0.5) < 0.38)
    sub = np.where(strand[..., None], (0.75 + 0.25 * np.sin(a * PI))[..., None] * np.ones(3), sub)
    sub = blend(sub, (np.abs(a - 0.5) > 0.44).astype(np.float32), (0.4, 0.4, 0.4), 0.8)
    sub = blend(sub, ss(0.08, 0.0, np.minimum(Q, 1 - Q)), (1, 1, 1), 1.0)
    img[sl] = sub


def paint_small(img, rng):
    # push-button panel: a walking figure over a dark field, an arrow down to the button
    sl, P, Q, X, Y = sq('button')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.95, 0.80, 0.30))
    sub = blend(sub, fill(d_box(X, Y, 0, 0.42, 0.7, 0.45, 0.1), 0.01), (0.16, 0.16, 0.18), 1.0)
    sub = blend(sub, figure(X, Y, 0, 0.42, 0.36), (0.96, 0.95, 0.92), 1.0)
    head = np.maximum.reduce([np.abs(X) - (Y + 0.52) * 0.9, Y + 0.28, -(Y + 0.52)])
    arrow = np.maximum(fill(d_box(X, Y, 0, -0.16, 0.06, 0.12), 0.01), fill(head, 0.01))
    sub = blend(sub, arrow, (0.16, 0.16, 0.18), 1.0)
    sub = weather(sub, X, Y, rng, 0.3, 10)
    img[sl] = sub
    # gas meter face: a gauge, counter wheels without numbers
    sl, P, Q, X, Y = sq('dial')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.93, 0.91, 0.85))
    sub = blend(sub, fill(d_circ(X, Y, 0, 0.3, 0.5), 0.01), (0.20, 0.20, 0.22), 1.0)
    sub = blend(sub, fill(d_circ(X, Y, 0, 0.3, 0.44), 0.01), (0.97, 0.96, 0.92), 1.0)
    a = np.arctan2(Y - 0.3, X); rr = np.sqrt(X ** 2 + (Y - 0.3) ** 2)
    sub = blend(sub, (np.cos(a * 24) > 0.8) * (rr > 0.33) * (rr < 0.42) * (Y > 0.15), (0.2, 0.2, 0.22), 1.0)
    sub = blend(sub, fill(d_seg(X, Y, (0, 0.3), (0.26, 0.5)) - 0.025, 0.01), (0.80, 0.22, 0.18), 1.0)
    sub = blend(sub, fill(d_circ(X, Y, 0, 0.3, 0.05), 0.01), (0.2, 0.2, 0.22), 1.0)
    for i in range(5):
        sub = blend(sub, fill(d_box(X, Y, -0.48 + 0.24 * i, -0.45, 0.09, 0.13, 0.02), 0.01), (0.16, 0.16, 0.18), 1.0)
        sub = blend(sub, fill(d_box(X, Y, -0.48 + 0.24 * i, -0.45, 0.06, 0.012), 0.008), (0.6, 0.6, 0.6), 1.0)
    sub = weather(sub, X, Y, rng, 0.25, 6)
    img[sl] = sub
    # post box plate: an envelope and a small clock (collection times) on cream
    sl, P, Q, X, Y = sq('post')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.95, 0.92, 0.84))
    sub = blend(sub, ss(0.03, 0.0, np.abs(d_box(X, Y, 0, 0, 0.86, 0.86, 0.12))), (0.25, 0.22, 0.2), 1.0)
    env = ss(0.045, 0.0, np.abs(d_box(X, Y, 0, 0.3, 0.45, 0.28, 0.03)))
    env = np.maximum(env, ss(0.04, 0.0, np.minimum(d_seg(X, Y, (-0.45, 0.58), (0, 0.25)), d_seg(X, Y, (0.45, 0.58), (0, 0.25)))) * (Y > 0.25))
    sub = blend(sub, env, (0.25, 0.22, 0.2), 1.0)
    sub = blend(sub, ss(0.04, 0.0, np.abs(d_circ(X, Y, 0, -0.42, 0.28))), (0.25, 0.22, 0.2), 1.0)
    sub = blend(sub, ss(0.035, 0.0, np.minimum(d_seg(X, Y, (0, -0.42), (0, -0.25)), d_seg(X, Y, (0, -0.42), (0.14, -0.45)))), (0.25, 0.22, 0.2), 1.0)
    sub = weather(sub, X, Y, rng, 0.3, 8)
    img[sl] = sub
    # bin plate: a leaf in a ring
    sl, P, Q, X, Y = sq('binplate')
    r = np.sqrt(X * X + Y * Y)
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.95, 0.93, 0.86))
    sub = blend(sub, ss(0.06, 0.0, np.abs(r - 0.8)), (0.25, 0.40, 0.30), 1.0)
    u = (X + Y) / 1.414; v = (Y - X) / 1.414
    leaf = ((u / 0.55) ** 2 + (v / 0.28) ** 2) < 1
    sub = blend(sub, leaf.astype(np.float32), (0.36, 0.58, 0.38), 1.0)
    sub = blend(sub, leaf * (np.abs(v) < 0.03), (0.95, 0.93, 0.86), 1.0)
    sub = weather(sub, X, Y, rng, 0.25, 6)
    img[sl] = sub
    # pole plate: cream with stripes and a diamond (no text)
    sl, P, Q, X, Y = sq('plate')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.93, 0.90, 0.80))
    sub = blend(sub, ss(0.04, 0.0, np.abs(d_box(X, Y, 0, 0, 0.84, 0.88, 0.08))), (0.30, 0.28, 0.26), 1.0)
    sub = blend(sub, fill(np.abs(X) + np.abs(Y - 0.45) - 0.25, 0.01), (0.30, 0.42, 0.62), 1.0)
    for yy in (-0.1, -0.35, -0.6):
        sub = blend(sub, fill(d_box(X, Y, 0, yy, 0.5, 0.06, 0.03), 0.01), (0.32, 0.30, 0.28), 1.0)
    sub = weather(sub, X, Y, rng, 0.4, 6)
    img[sl] = sub
    # chalkboard: dark board, an apple, a carrot and a few chalk dots and smudges
    sl, P, Q, X, Y = sq('chalk')
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.20, 0.25, 0.22))
    sub = blend(sub, ss(0.4, 0.9, fbm(P, Q, 6, 6, rng)), (0.34, 0.38, 0.35), 0.5)
    chalk = (0.90, 0.90, 0.86)
    sub = blend(sub, ss(0.035, 0.0, np.abs(d_circ(X, Y, -0.35, 0.25, 0.3))), chalk, 0.9)
    sub = blend(sub, ss(0.03, 0.0, d_seg(X, Y, (-0.35, 0.52), (-0.25, 0.7))), chalk, 0.9)
    sub = blend(sub, ss(0.03, 0.0, d_seg(X, Y, (0.25, -0.1), (0.65, 0.5))), (0.95, 0.66, 0.40), 0.9)
    sub = blend(sub, ss(0.03, 0.0, d_seg(X, Y, (0.65, 0.5), (0.72, 0.68))), (0.60, 0.85, 0.55), 0.9)
    for k in range(5):
        sub = blend(sub, fill(d_circ(X, Y, -0.6 + 0.3 * k, -0.55, 0.06), 0.01), chalk, 0.85)
    sub = blend(sub, ss(0.03, 0.0, np.abs(Y + 0.3 + 0.04 * np.sin(X * 12))) * (np.abs(X) < 0.75), chalk, 0.7)
    img[sl] = sub


def paint_machines(img, rng):
    # AC fan grille and side louvres
    sl, P, Q, X, Y = sq('fan')
    r = np.sqrt(X * X + Y * Y); a = np.arctan2(Y, X)
    sub = np.ones(P.shape + (3,), np.float32) * 0.2
    sub = blend(sub, ss(0.06, 0.0, np.abs(np.sin(a * 6 + r * 2.2))) * (r < 0.9), (0.32, 0.33, 0.34), 1.0)
    for rr in np.arange(0.15, 0.95, 0.11):
        sub = blend(sub, ss(0.025, 0.0, np.abs(r - rr)), (0.78, 0.78, 0.76), 1.0)
    sub = blend(sub, ss(0.02, 0.0, np.minimum(np.abs(X), np.abs(Y))) * (r < 0.92), (0.78, 0.78, 0.76), 1.0)
    sub = blend(sub, fill(r - 0.16, 0.01), (0.86, 0.86, 0.84), 1.0)
    sub = blend(sub, ss(0.93, 0.98, r), (1, 1, 1), 1.0)
    img[sl] = sub
    sl, P, Q = region('acvent')
    k = (Q * 12) % 1.0
    sub = np.ones(P.shape + (3,), np.float32) * (0.55 + 0.42 * ss(0.15, 0.85, k))[..., None]
    sub = blend(sub, ss(0.06, 0.0, np.minimum(np.minimum(P, 1 - P), np.minimum(Q, 1 - Q))), (0.62, 0.62, 0.6), 1.0)
    sub = blend(sub, ss(0.3, 0.0, Q) * (0.5 + 0.5 * fbm(P, Q, 10, 6, rng)), GRIME, 0.5)
    img[sl] = sub
    # plastic crate side: frame, openings showing bottles, a hand-hold slot
    sl, P, Q = region('pcrate')
    sub = np.ones(P.shape + (3,), np.float32)
    X, Y = 2 * P - 1, 2 * Q - 1
    holes = np.zeros(P.shape, np.float32)
    for i in range(4):
        for j in range(2):
            holes = np.maximum(holes, fill(d_box(X, Y, -0.66 + 0.44 * i, -0.42 + 0.56 * j, 0.17, 0.2, 0.06), 0.02))
    sub = blend(sub, holes, (0.30, 0.30, 0.31), 1.0)
    for i in range(4):
        bx = -0.66 + 0.44 * i
        m = fill(d_box(X, Y, bx, -0.3, 0.09, 0.32, 0.08), 0.02) * holes
        sub = blend(sub, m, (0.48, 0.40, 0.32), 1.0)
    sub = blend(sub, fill(d_box(X, Y, 0, 0.72, 0.3, 0.07, 0.07), 0.02), (0.22, 0.22, 0.23), 1.0)
    sub = blend(sub, ss(0.03, 0.0, np.abs(Y - 0.55)), (0.82, 0.82, 0.82), 0.6)
    sub *= (0.95 + 0.05 * fbm(P, Q, 8, 8, rng))[..., None]
    sub = blend(sub, ss(-0.5, -1.0, Y), GRIME, 0.4)
    img[sl] = sub
    # vending: two product windows, the coin panel and two lit headers
    for name, seed in (('vdisp1', 3), ('vdisp2', 5)):
        r2 = np.random.default_rng(seed)
        sl, P, Q = region(name)
        x, z = P * 0.62, Q * 1.0
        top, bot = np.array((0.92, 0.93, 0.92)), np.array((0.80, 0.82, 0.84))
        sub = bot[None, None] * (1 - Q[..., None]) + top[None, None] * Q[..., None]
        pal = [(0.86, 0.28, 0.24), (0.96, 0.72, 0.26), (0.32, 0.58, 0.82), (0.44, 0.70, 0.40), (0.95, 0.95, 0.92),
               (0.62, 0.36, 0.22), (0.88, 0.50, 0.62), (0.30, 0.32, 0.36), (0.96, 0.58, 0.24)]
        for row in range(3):
            z0 = 0.06 + row * 0.32
            sub = blend(sub, fill(d_box(x, z, 0.31, z0 - 0.02, 0.31, 0.012), 0.002), (0.45, 0.46, 0.48), 1.0)
            for c in range(6):
                cx = 0.055 + c * 0.102
                col = np.array(pal[r2.integers(0, len(pal))])
                if r2.random() < 0.5:   # bottle
                    m = np.maximum(fill(d_box(x, z, cx, z0 + 0.09, 0.03, 0.08, 0.025), 0.002),
                                   fill(d_box(x, z, cx, z0 + 0.19, 0.012, 0.03, 0.006), 0.002))
                    cap = fill(d_box(x, z, cx, z0 + 0.225, 0.014, 0.008, 0.003), 0.002)
                    lab = fill(d_box(x, z, cx, z0 + 0.08, 0.031, 0.025), 0.002)
                    sub = blend(sub, m, col * 0.85 + 0.12, 0.85)
                    sub = blend(sub, lab, col, 1.0)
                    sub = blend(sub, cap, (0.95, 0.95, 0.95), 1.0)
                else:                   # can
                    m = fill(d_box(x, z, cx, z0 + 0.08, 0.033, 0.065, 0.008), 0.002)
                    sub = blend(sub, m, col, 1.0)
                    sub = blend(sub, fill(d_box(x, z, cx, z0 + 0.08, 0.033, 0.012), 0.002) * m, (0.96, 0.96, 0.94), 0.9)
                sub = blend(sub, fill(d_box(x, z, cx - 0.012, z0 + 0.06, 0.006, 0.05), 0.002), (1, 1, 1), 0.35)
                sub = blend(sub, fill(d_box(x, z, cx, z0 - 0.045, 0.03, 0.012, 0.004), 0.002), (0.97, 0.97, 0.95), 1.0)
                sub = blend(sub, fill(d_circ(x, z, cx, z0 - 0.045, 0.007), 0.002), (0.90, 0.30, 0.25), 1.0)
        d = P * 0.7 + Q
        sub = blend(sub, ss(0.08, 0.0, np.abs(d - 0.75)), (1, 1, 1), 0.3)
        sub = blend(sub, ss(0.03, 0.0, np.abs(d - 0.92)), (1, 1, 1), 0.35)
        edge = np.minimum(np.minimum(P, 1 - P) * 0.62, np.minimum(Q, 1 - Q))
        sub = blend(sub, ss(0.04, 0.0, edge), (0.38, 0.40, 0.42), 0.7)
        img[sl] = sub
    sl, P, Q = region('vpanel')
    X, Y = (2 * P - 1) * 0.5, 2 * Q - 1
    sub = np.ones(P.shape + (3,), np.float32) * np.array((0.74, 0.75, 0.76))
    sub = blend(sub, fill(d_box(X, Y, 0, 0.72, 0.36, 0.12, 0.02), 0.005), (0.14, 0.20, 0.18), 1.0)
    sub = blend(sub, fill(d_box(X, Y, -0.1, 0.74, 0.18, 0.03), 0.005), (0.40, 0.62, 0.48), 0.7)
    sub = blend(sub, fill(d_box(X, Y, 0.18, 0.35, 0.025, 0.1, 0.02), 0.005), (0.12, 0.12, 0.13), 1.0)
    sub = blend(sub, fill(d_box(X, Y, 0.0, 0.05, 0.3, 0.035, 0.02), 0.005), (0.12, 0.12, 0.13), 1.0)
    sub = blend(sub, fill(d_circ(X, Y, -0.2, 0.36, 0.08), 0.005), (0.55, 0.56, 0.58), 1.0)
    for i in range(3):
        for j in range(3):
            sub = blend(sub, fill(d_circ(X, Y, -0.2 + 0.2 * i, -0.3 - 0.17 * j, 0.05), 0.005), (0.92, 0.92, 0.9), 1.0)
    sub = blend(sub, fill(d_box(X, Y, 0, -0.85, 0.3, 0.06, 0.02), 0.005), (0.12, 0.12, 0.13), 1.0)
    img[sl] = sub
    for name, kind in (('vhead1', 0), ('vhead2', 1)):
        sl, P, Q = region(name)
        X, Y = (2 * P - 1) * 2, 2 * Q - 1
        sub = np.ones(P.shape + (3,), np.float32) * np.array((0.98, 0.96, 0.90))
        if kind == 0:
            sub = blend(sub, fill(d_circ(X, Y, 0, -0.05, 0.6), 0.02), (0.84, 0.28, 0.24), 1.0)
            band = np.abs(Y + 0.05 - 0.12 * np.sin(X * 6)) < 0.09
            sub = blend(sub, band * fill(d_circ(X, Y, 0, -0.05, 0.6), 0.02), (0.98, 0.94, 0.88), 1.0)
            leaf = ((((X - 0.2) * 0.8 + (Y - 0.7) * 0.6) / 0.28) ** 2 + (((Y - 0.7) * 0.8 - (X - 0.2) * 0.6) / 0.12) ** 2) < 1
            sub = blend(sub, leaf.astype(np.float32), (0.42, 0.66, 0.36), 1.0)
            for sx in (-1, 1):
                for k in range(3):
                    sub = blend(sub, fill(d_circ(X, Y, sx * (0.95 + 0.3 * k), -0.05, 0.09 - 0.02 * k), 0.02), (0.84, 0.28, 0.24), 1.0)
        else:
            for (cx, cy, r) in ((-0.25, -0.2, 0.32), (0.25, 0.25, 0.22), (0.5, -0.35, 0.14), (-0.55, 0.42, 0.12)):
                sub = blend(sub, ss(0.06, 0.0, np.abs(d_circ(X, Y, cx, cy, r))), (0.28, 0.48, 0.74), 1.0)
            for sx in (-1, 1):
                sub = blend(sub, ss(0.07, 0.0, np.abs(Y + 0.1 - 0.25 * np.sin(X * 3.0))) * (np.abs(X) > 0.95) * (np.abs(X) < 1.85), (0.28, 0.48, 0.74), 0.9)
        edge = np.minimum(np.minimum(P, 1 - P) * 4, np.minimum(Q, 1 - Q))
        sub = blend(sub, ss(0.12, 0.0, edge), (0.80, 0.78, 0.72), 0.6)
        img[sl] = sub


def paint_atlas(path, seed=11):
    from PIL import Image
    rng = np.random.default_rng(seed)
    img = np.ones((AT, AT, 3), np.float32)
    paint_surfaces(img, rng)
    paint_wall(img, rng); paint_hoard(img, rng)
    paint_hazard(img, rng); paint_redwhite(img, rng)
    paint_signs(img, rng); paint_ground(img, rng)
    paint_cloth(img, rng); paint_leaf(img, rng)
    paint_small(img, rng); paint_machines(img, rng)
    img[AT - 128:, AT - 128:] = 1.0          # the plain white corner (UV 0.97, 0.03)
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(path)
