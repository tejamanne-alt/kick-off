# Collectibles for the ANIMALS kit: the coin, the level's sticker badge and a puffy star. Each is
# one static mesh with its origin at its centre and its face toward -Y (the camera); the game
# spins the coin about the vertical axis and rocks the sticker. Built in a local frame with the
# face toward +Z, then turned so +Z looks along -Y.
import math
import numpy as np
import kit_animals_geo as G
import kit_animals_common as K

hexc = G.hexc
TO_FRONT = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])     # local +Z -> -Y, local +Y -> +Z (up)


def _band(profile, n, phase=0.0, rfun=None):
    """One smooth band of a lathe about local Z (profile: [(r, z)] from the face centre outward
    and round). Normals come from the profile, so bands meet at crisp creases. rfun(theta, r)
    may modulate the radius (scallops)."""
    prof = np.asarray(profile, float)
    tg = np.gradient(prof, axis=0)
    nrm2 = G.unit(np.column_stack([-tg[:, 1], tg[:, 0]]))       # (nr, nz): +z for a profile running outward on a top face
    V = []; N = []; rings = []
    for (r, z), (nr, nz) in zip(prof, nrm2):
        if r < 1e-9:
            rings.append([len(V)]); V.append((0, 0, z)); N.append((0, 0, 1 if nz >= 0 else -1))
            continue
        ids = []
        for i in range(n):
            a = 2 * math.pi * (i + phase) / n
            rr = rfun(a, r) if rfun else r
            ids.append(len(V)); V.append((rr * math.cos(a), rr * math.sin(a), z)); N.append((nr * math.cos(a), nr * math.sin(a), nz))
        rings.append(ids)
    T = []
    for s in range(len(rings) - 1):
        A_, B_ = rings[s], rings[s + 1]
        for i in range(n):
            i2 = (i + 1) % n
            if len(A_) == 1:
                T.append((A_[0], B_[i], B_[i2]))
            elif len(B_) == 1:
                T.append((A_[i], B_[0], A_[i2]))
            else:
                T += [(A_[i], B_[i], B_[i2]), (A_[i], B_[i2], A_[i2])]
    p = G.Piece(np.array(V, float), np.array(T), np.array(N, float))
    return G.orient_by_normals(p)


def _star_outline(Ro, Ri, tip_round, points=5, per_tip=3, rot=math.pi / 2):
    """A rounded star outline in the XY plane (a tip pointing +Y)."""
    out = []
    for k in range(points):
        a = rot + 2 * math.pi * k / points
        for j in range(per_tip):
            da = (j - (per_tip - 1) / 2) * tip_round
            rr = Ro - abs(j - (per_tip - 1) / 2) * Ro * 0.06
            out.append((rr * math.cos(a + da), rr * math.sin(a + da)))
        b = a + math.pi / points
        for da in (-0.13, 0.0, 0.13) if per_tip > 3 else (0.0,):
            out.append((Ri * math.cos(b + da) * (1.0 if da == 0 else 1.06), Ri * math.sin(b + da) * (1.0 if da == 0 else 1.06)))
    return np.array(out)


def _puff(outline, z_of, fr, base_z=None, base_grow=1.03, smooth=True):
    """A puffy fan over an outline (XY): rings at fractions fr of the outline (fr[-1] = 1),
    heights z_of(fraction); an optional skirt ring below at base_z."""
    n = len(outline)
    V = [(0.0, 0.0, z_of(0.0))]
    rings = []
    for f in fr:
        rings.append(list(range(len(V), len(V) + n)))
        V += [(x * f, y * f, z_of(f)) for x, y in outline]
    if base_z is not None:
        rings.append(list(range(len(V), len(V) + n)))
        V += [(x * base_grow, y * base_grow, base_z) for x, y in outline]
    T = [(0, rings[0][i], rings[0][(i + 1) % n]) for i in range(n)]
    for r in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            a, b, c, d = rings[r][i], rings[r][i2], rings[r + 1][i2], rings[r + 1][i]
            T += [(a, d, c), (a, c, b)]
    p = G.Piece(np.array(V, float), np.array(T))
    if np.mean(p.N[:, 2]) < 0:
        p.T = p.T[:, ::-1]; p.N = G.vnormals(p.V, p.T)
    return p


def _finish(pieces):
    for p in pieces:
        p.move(TO_FRONT)
    return pieces


# ================================================================ coin
COIN = {'gold': hexc('#f2b53a'), 'face': hexc('#e7a42c'), 'rim': hexc('#ffd25c'), 'side': hexc('#d2921f'),
        'star': hexc('#ffd965')}


def build_coin():
    R, Rin, hr, hf, n = 0.25, 0.188, 0.045, 0.029, 24
    pieces = []
    for sgn in (1, -1):
        face = _band([(0, hf), (Rin, hf)], n)
        wall = _band([(Rin, hf), (Rin + 0.008, hr)], n)
        for p in (face, wall):
            if sgn < 0:
                p.V[:, 2] *= -1; p.N[:, 2] *= -1; p.T = p.T[:, ::-1]
        pieces += [('face', face), ('wall', wall)]
        star = _puff(_star_outline(0.122, 0.056, 0.13, per_tip=3),
                     lambda f: hf + 0.004 + 0.017 * (1 - f ** 2) ** 0.6 if f < 1 else hf + 0.006, [0.55, 1.0],
                     base_z=hf - 0.004, base_grow=1.02)
        star.N = G.vnormals(star.V, star.T)
        if sgn < 0:
            star.V[:, 2] *= -1; star.N[:, 2] *= -1; star.T = star.T[:, ::-1]
            star.V[:, 0] *= -1; star.N[:, 0] *= -1; star.T = star.T[:, ::-1]
        pieces.append(('star', star))
    rim = _band([(Rin + 0.008, hr), (R - 0.012, hr), (R, hr - 0.014), (R, -hr + 0.014), (R - 0.012, -hr), (Rin + 0.008, -hr)], n)
    pieces.append(('rim', rim))
    out = []
    for kind, p in pieces:
        p.move(TO_FRONT)
        z = p.V[:, 2]
        light = 0.86 + 0.24 * G.smoothstep(-0.25, 0.25, z)            # lighter toward the top
        facing = np.clip(-p.N[:, 1], 0, 1)                              # the face toward the camera
        if kind == 'rim':
            side = 1 - np.abs(p.N[:, 1])                               # the coin's edge
            col = G.l2s(COIN['rim'])[None] * (1 - side[:, None]) + G.l2s(COIN['side'])[None] * side[:, None]
            k = light * (0.92 + 0.12 * np.clip(p.N[:, 2], 0, 1))
            p.color(G.s2l(np.clip(col * k[:, None], 0, 1)))
        elif kind == 'star':
            k = light * (0.94 + 0.12 * np.clip(p.N[:, 2], 0, 1)) * (0.96 + 0.06 * facing)
            p.color(G.shade_srgb(COIN['star'], k))
        elif kind == 'wall':
            p.color(G.shade_srgb(COIN['face'], light * (0.86 + 0.14 * np.clip(p.N[:, 2], -1, 1))))
        else:
            p.color(G.shade_srgb(COIN['face'], light * 0.98))
        p.part(1)
        out.append(p)
    return K.Model('Coin', [K.Part('Coin', (0, 0, 0), out)], {1: COIN['gold']}, 600, kind='static',
                   extra={'origin': 'centre', 'spin': 'about the vertical axis (model Z)'})


# ================================================================ sticker (a round badge with a heart)
STICKER = {'face': hexc('#f58cb8'), 'line': hexc('#d9628f'), 'border': hexc('#fbf8f2'), 'heart': hexc('#ffe07a'),
           'back': hexc('#ece6dc')}


def build_sticker():
    n = 40
    Rf = 0.27
    scal = lambda a, r: r + 0.012 * math.cos(10 * a) * min(max((r - 0.28) / 0.04, 0), 1)
    face = _band([(0, 0.02), (0.244, 0.02)], n)
    line = _band([(0.244, 0.02), (Rf, 0.02)], n)
    border = _band([(Rf, 0.02), (0.29, 0.037), (0.33, 0.026), (0.316, -0.02)], n, rfun=scal)
    back = _band([(0.316, -0.02), (0, -0.02)], n, rfun=scal)
    t = np.linspace(0, 2 * math.pi, 25)[:-1]
    hx = 16 * np.sin(t) ** 3
    hy = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    outline = np.column_stack([hx, hy + 2.0]) * 0.0098
    heart = _puff(outline, lambda f: 0.02 + 0.05 * (1 - f ** 2) ** 0.55 + (0.01 if f >= 1 else 0.0), [0.55, 1.0],
                  base_z=0.012, base_grow=1.03)
    heart.N = G.vnormals(heart.V, heart.T)
    out = []
    for kind, p in (('face', face), ('line', line), ('border', border), ('back', back), ('heart', heart)):
        p.move(TO_FRONT)
        z = p.V[:, 2]
        light = 0.88 + 0.2 * G.smoothstep(-0.32, 0.32, z)
        if kind == 'heart':
            # a soft gloss toward the upper left
            g = np.exp(-((p.V[:, 0] + 0.06) ** 2 + (p.V[:, 2] - 0.06) ** 2) / 0.004)
            k = light * (0.9 + 0.12 * np.clip(-p.N[:, 1], 0, 1)) * (1 + 0.1 * g)
            p.color(G.shade_srgb(STICKER['heart'], k)); p.part(2)
        elif kind == 'border':
            p.color(G.shade_srgb(STICKER['border'], light * (0.9 + 0.1 * np.clip(-p.N[:, 1] + p.N[:, 2], 0, 1)))); p.part(0)
        elif kind == 'back':
            p.color(G.shade_srgb(STICKER['back'], light * 0.95)); p.part(0)
        else:
            p.color(G.shade_srgb(STICKER['line'] if kind == 'line' else STICKER['face'], light * 0.98)); p.part(1)
        out.append(p)
    return K.Model('Sticker', [K.Part('Sticker', (0, 0, 0), out)], {1: STICKER['face'], 2: STICKER['heart']}, 600,
                   kind='static', extra={'origin': 'centre', 'diameter': 0.7})


# ================================================================ star (a puffy collectible)
STAR = {'gold': hexc('#ffcd40'), 'deep': hexc('#f0a826')}


def build_star():
    outline = _star_outline(0.25, 0.118, 0.11, per_tip=3)
    # a smoother outline: a point between each tip arc and valley
    pts = []
    m = len(outline)
    for i in range(m):
        a, b = outline[i], outline[(i + 1) % m]
        pts.append(a)
        if np.linalg.norm(a) > 0.2 and np.linalg.norm(b) < 0.15 or np.linalg.norm(a) < 0.15 and np.linalg.norm(b) > 0.2:
            pts.append(0.5 * (a + b) * 1.0)
    outline = np.array(pts)
    zf = lambda f: 0.072 * (1 - 0.8 * f ** 2) ** 0.5
    front = _puff(outline, zf, [0.42, 0.78, 1.0])
    # the rim: the outline ring at z = 0 joins the front and back puffs
    n = len(outline)
    Vf = front.V
    ring_idx = np.arange(len(Vf) - n, len(Vf))
    rim_ring = np.column_stack([outline * 1.035, np.zeros(n)])
    V = np.vstack([Vf, rim_ring])
    T = list(front.T)
    for i in range(n):
        i2 = (i + 1) % n
        a, b, c, d = ring_idx[i], ring_idx[i2], len(Vf) + i2, len(Vf) + i
        T += [(a, d, c), (a, c, b)]
    half = G.Piece(V, np.array(T))
    if np.mean(half.N[:, 2]) < 0:
        half.T = half.T[:, ::-1]
    back = half.copy(); back.V[:, 2] *= -1; back.T = back.T[:, ::-1]
    # weld the shared rim: build one closed piece
    off = len(half.V)
    Vall = np.vstack([half.V, back.V]); Tall = np.vstack([half.T, back.T + off])
    rim_b = np.arange(off + len(Vf), off + len(Vf) + n); rim_f = np.arange(len(Vf), len(Vf) + n)
    remap = np.arange(len(Vall)); remap[rim_b] = rim_f
    Tall = remap[Tall]
    p = G.Piece(Vall, Tall)
    G.outward(p)
    # pillow normals: the puff's own shape, softened toward the rim
    p.N = G.vnormals(p.V, p.T)
    p.move(TO_FRONT)
    z = p.V[:, 2]
    light = 0.82 + 0.28 * G.smoothstep(-0.22, 0.22, z)
    facing = np.clip(-p.N[:, 1], 0, 1)
    col = G.l2s(STAR['deep'])[None] * (1 - facing[:, None] * 0.7) + G.l2s(STAR['gold'])[None] * (facing[:, None] * 0.7)
    g = np.exp(-((p.V[:, 0] + 0.07) ** 2 + (p.V[:, 2] - 0.09) ** 2) / 0.006) * facing
    k = light * (1 + 0.12 * g)
    p.color(G.s2l(np.clip(col * k[:, None], 0, 1))).part(1)
    return K.Model('Star', [K.Part('Star', (0, 0, 0), [p])], {1: STAR['gold']}, 600, kind='static',
                   extra={'origin': 'centre'})
