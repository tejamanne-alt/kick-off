# Birds for the ANIMALS kit: the flying seagull (Body, WingL, WingR), the standing seagull
# (static), the market pigeon (Body, Head) and the pond duck (Body, Head, floating). See
# kit_animals_common.py for the conventions (head +X, right flank toward the camera at -Y).
import math
import numpy as np
import kit_animals_geo as G
import kit_animals_common as K
import kit_animals_atlas as A

hexc = G.hexc

GULL = {
    'white': hexc('#f7f5f0'),
    'grey': hexc('#a3aebc'),      # mantle and upper wing (part 1)
    'under': hexc('#e2e6ec'),     # wing underside (part 1, lighter)
    'tip': hexc('#2c2d33'),
    'beak': hexc('#f4c444'),      # part 2
    'spot': hexc('#d8483b'),
    'leg': hexc('#eaa18c'),
}


# ================================================================ seagull wing
_WING = {
    's':  [0.0, 0.12, 0.38, 0.62, 0.82, 1.0],
    'le': [0.075, 0.082, 0.092, 0.060, 0.012, -0.072],
    'te': [-0.070, -0.078, -0.082, -0.066, -0.070, -0.077],
    'th': [0.042, 0.030, 0.020, 0.014, 0.009, 0.004],
}
_C = [0.0, 0.05, 0.22, 0.55, 1.0, 0.55, 0.22, 0.05]
_TOP = [True, True, True, True, True, False, False, False]


def _wing_table(n=200):
    pts = np.array([_WING['s'], _WING['le'], _WING['te'], _WING['th']]).T
    D = G.catmull(pts, n)
    order = np.argsort(D[:, 0])
    return D[order]


def gull_wing(root_y=0.012, tip_y=0.45, z0=0.025, stations=13):
    """The left wing (+Y), spread flat, as a closed airfoil loft with (chord, span) feather UVs
    and regions: black tip, a white mirror spot, a white trailing edge. Returns (pieces, fns)."""
    D = _wing_table()
    u = np.linspace(0, 1, stations)
    S = 1 - (1 - u) ** 1.3
    le = np.interp(S, D[:, 0], D[:, 1]); te = np.interp(S, D[:, 0], D[:, 2]); th = np.interp(S, D[:, 0], D[:, 3])
    rings = []; UV = []
    f = lambda c: 2.598 * np.sqrt(c) * (1 - c)
    reg = A.inset('feather', 0.006)
    for i, s in enumerate(S):
        y = root_y + s * (tip_y - root_y)
        zc = z0 + 0.012 * math.sin(math.pi * s * 0.85) - 0.004 * s
        ring = []
        for c, top in zip(_C, _TOP):
            x = le[i] + c * (te[i] - le[i])
            z = zc + (0.75 if top else -0.25) * th[i] * f(c)
            ring.append((x, y, z))
            UV.append((reg[0] + (reg[2] - reg[0]) * c, reg[1] + (reg[3] - reg[1]) * s))
        rings.append(ring)
    p = G.loft(rings, True, True)
    UV.append((reg[0] + (reg[2] - reg[0]) * 0.4, reg[1])); UV.append((reg[0] + (reg[2] - reg[0]) * 0.4, reg[3]))
    p.U = np.array(UV)
    G.outward(p)
    p.N = G.vnormals(p.V, p.T)

    def s_of(P):
        return (np.abs(P[:, 1]) - root_y) / (tip_y - root_y)

    def c_of(P):
        s = np.clip(s_of(P), 0, 1)
        l = np.interp(s, D[:, 0], D[:, 1]); t = np.interp(s, D[:, 0], D[:, 2])
        return (l - P[:, 0]) / np.maximum(l - t, 1e-4)
    return p, s_of, c_of


def gull_wing_regions(p, s_of, c_of, root_y, tip_y):
    D = _wing_table()
    sm = 0.885
    xm = np.interp(sm, D[:, 0], D[:, 1]) + 0.42 * (np.interp(sm, D[:, 0], D[:, 2]) - np.interp(sm, D[:, 0], D[:, 1]))
    ym = root_y + sm * (tip_y - root_y)
    mirror = lambda P: 0.0115 - np.hypot(P[:, 0] - xm, np.abs(P[:, 1]) - ym)
    tip = lambda P: (s_of(P) + 0.20 * (c_of(P) - 0.5) - 0.79) * 0.4

    def upper(V, N, U, Aocc):
        t = G.smoothstep(-0.35, 0.35, N[:, 2])
        k = (0.94 + 0.08 * t) * (0.85 + 0.15 * Aocc)
        col = G.l2s(GULL['under'])[None] * (1 - t[:, None]) + G.l2s(GULL['grey'])[None] * t[:, None]
        # the white trailing edge of the arm, a soft fade into the grey
        w = (G.smoothstep(0.6, 0.98, c_of(V)) * G.smoothstep(0.82, 0.7, s_of(V)) * 0.85)[:, None]
        col = col * (1 - w) + G.l2s(GULL['white'])[None] * w
        return G.s2l(np.clip(col * k[:, None], 0, 1)), 1

    def flat(base, part, lo=0.9, hi=1.04):
        def fn(V, N, U, Aocc):
            k = lo + (hi - lo) * G.smoothstep(-0.4, 0.5, N[:, 2])
            return G.shade_srgb(base, k), part
        return fn
    return G.paint_piece(p, [('mirror', mirror), ('tip', tip)],
                         {'base': upper, 'mirror': flat(GULL['white'], 0, 0.92, 1.0),
                          'tip': flat(GULL['tip'], 0, 0.85, 1.15)})


def _gull_head_bits(head_c, toward, beak_base_x, scale=1.0):
    """Regions shared by both gulls: the beak (part 2) and its red spot."""
    beak = K.neg(G.ellipsoid((beak_base_x + 0.042 * scale, 0, head_c[2] - 0.01 * scale), (0.045 * scale, 0.03 * scale, 0.032 * scale)))
    spot = G.mirror_y(lambda P: 0.0062 * scale - np.linalg.norm(P - np.array((beak_base_x + 0.041 * scale, 0.0085 * scale, head_c[2] - 0.019 * scale)), axis=1))
    return beak, spot


# ================================================================ seagull (flying)
def build_seagull():
    HC = np.array((0.165, 0, 0.036))
    chest = G.ellipsoid((0.035, 0, -0.004), (0.115, 0.066, 0.066))
    rear = G.round_cone((-0.02, 0, 0.0), (-0.15, 0, 0.012), 0.058, 0.022)
    tail = G.ellipsoid((-0.178, 0, 0.012), (0.058, 0.05, 0.011))
    neck = G.round_cone((0.08, 0, 0.008), (0.155, 0, 0.034), 0.056, 0.047)
    head = G.ellipsoid(HC, (0.053, 0.047, 0.048))
    beakf = G.round_cone((0.205, 0, 0.032), (0.268, 0, 0.022), 0.0155, 0.0065)
    gonys = G.sphere((0.246, 0, 0.0175), 0.0075)
    feet = G.mirror_y(G.ellipsoid((-0.118, 0.022, -0.042), (0.03, 0.013, 0.008), G.rot((0, 1, 0), math.radians(-12))))
    body = G.blend(chest, (rear, 0.05), (tail, 0.03), (neck, 0.04), (head, 0.035), (beakf, 0.012), (gonys, 0.008))
    beak, spot = _gull_head_bits(HC, None, 0.203)
    mantle = K.neg(G.ellipsoid((-0.03, 0, 0.052), (0.125, 0.048, 0.04)))
    allf = G.union(body, feet)

    sb = G.Surface(body, (-0.26, -0.09, -0.09), (0.3, 0.09, 0.11), 0.0028, 500, sym=True,
                   weight=lambda P: G.smoothstep(0.14, 0.2, P[:, 0]))
    white = K.painter(GULL['white'], 0, -0.06, 0.06, dark=0.8, light=1.0)
    pcs = sb.pieces([('spot', spot), ('beak', beak), ('mantle', mantle)],
                    {'base': white, 'mantle': K.painter(GULL['grey'], 1, -0.06, 0.07, dark=0.85, light=1.05),
                     'beak': K.painter(GULL['beak'], 2, 0.0, 0.04, dark=0.82, light=1.06),
                     'spot': K.flat_painter(GULL['spot'], 0, 1.0)}, ao_field=allf, ao_scale=0.02)
    sf = G.Surface(feet, (-0.17, -0.05, -0.06), (-0.07, 0.05, -0.02), 0.002, 60, sym=True)
    pcs += sf.pieces([], {'base': K.painter(GULL['leg'], 0, -0.06, -0.03, dark=0.85, light=1.0)}, ao_field=allf, ao_scale=0.01)
    for s in (1, -1):
        e, _, _ = K.eye(body, HC, (0.2, s * 0.044, 0.056), 0.0115, n=8, rings=2)
        pcs.append(e)

    root_y, tip_y = 0.012, 0.45
    wing, s_of, c_of = gull_wing(root_y, tip_y)
    wl = gull_wing_regions(wing, s_of, c_of, root_y, tip_y)
    wr = [p.mirrored_y() for p in wl]
    piv = 0.03
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('WingL', (0.0, piv, 0.025), wl, motion='flap about X (the body axis), -40..+40 deg'),
             K.Part('WingR', (0.0, -piv, 0.025), wr, motion='flap about X (mirror of WingL)')]
    return K.Model('Seagull', parts, {1: GULL['grey'], 2: GULL['beak']}, 1500,
                   extra={'origin': 'body centre (flying)', 'head': '+X', 'wingspan': 0.9},
                   attach={'Beak': ((0.27, 0, 0.022), 'Body')})


# ================================================================ brown pelican (flying), for Florida
PELICAN = {
    'body': hexc('#8a8378'),      # grey-brown back and wings (part 1)
    'under': hexc('#a59e92'),
    'neck': hexc('#5a3a2a'),      # chestnut back of the neck
    'head': hexc('#f3ead2'),      # white head, a yellow crown
    'crown': hexc('#f1d27a'),
    'bill': hexc('#c9a46a'),      # part 2
    'pouch': hexc('#4c4a46'),
    'tip': hexc('#2a2622'),
    'leg': hexc('#3a3834'),
}


def build_pelican():
    """Florida's brown pelican flying as it does along the bay, its head drawn back on its shoulders and the long bill
    resting on its chest, broad grey-brown wings with dark tips: the Seagull's rig (Body, WingL, WingR at the shoulders,
    head toward +X), 1.4 m across, so the hazard's swoop flies it as it flies the gull."""
    HC = np.array((0.2, 0, 0.07))
    chest = G.ellipsoid((0.03, 0, 0.0), (0.2, 0.1, 0.095))
    rear = G.round_cone((-0.05, 0, 0.0), (-0.26, 0, 0.02), 0.085, 0.03)
    tail = G.ellipsoid((-0.29, 0, 0.02), (0.06, 0.06, 0.012))
    neck = G.round_cone((0.12, 0, 0.03), (0.2, 0, 0.07), 0.07, 0.055)
    head = G.ellipsoid(HC, (0.06, 0.05, 0.05))
    billf = G.round_cone((0.24, 0, 0.065), (0.52, 0, 0.0), 0.022, 0.012)
    pouchf = G.round_cone((0.24, 0, 0.04), (0.47, 0, -0.01), 0.03, 0.012)
    feet = G.mirror_y(G.ellipsoid((-0.22, 0.03, -0.06), (0.04, 0.016, 0.01), G.rot((0, 1, 0), math.radians(-12))))
    body = G.blend(chest, (rear, 0.06), (tail, 0.03), (neck, 0.05), (head, 0.04), (billf, 0.012), (pouchf, 0.015))
    bill = K.neg(G.ellipsoid((0.38, 0, 0.035), (0.15, 0.03, 0.03)))
    pouch = K.neg(G.ellipsoid((0.36, 0, 0.005), (0.13, 0.025, 0.025)))
    headr = K.neg(G.ellipsoid(HC + np.array((0.0, 0, 0.0)), (0.07, 0.06, 0.06)))
    crown = K.neg(G.ellipsoid(HC + np.array((0.0, 0, 0.04)), (0.045, 0.035, 0.02)))
    neckr = K.neg(G.ellipsoid((0.1, 0, 0.06), (0.07, 0.05, 0.045)))
    allf = G.union(body, feet)
    sb = G.Surface(body, (-0.37, -0.13, -0.13), (0.56, 0.13, 0.15), 0.004, 520, sym=True,
                   weight=lambda P: G.smoothstep(0.2, 0.28, P[:, 0]))
    pcs = sb.pieces([('pouch', pouch), ('bill', bill), ('crown', crown), ('head', headr), ('neck', neckr)],
                    {'base': K.painter(PELICAN['body'], 1, -0.08, 0.09, dark=0.8, light=1.05),
                     'neck': K.painter(PELICAN['neck'], 0, -0.02, 0.1, dark=0.85, light=1.05),
                     'head': K.painter(PELICAN['head'], 0, 0.02, 0.12, dark=0.85, light=1.0),
                     'crown': K.flat_painter(PELICAN['crown'], 0, 1.0),
                     'bill': K.painter(PELICAN['bill'], 2, -0.02, 0.08, dark=0.82, light=1.05),
                     'pouch': K.painter(PELICAN['pouch'], 0, -0.04, 0.03, dark=0.85, light=1.0)}, ao_field=allf, ao_scale=0.025)
    sf = G.Surface(feet, (-0.29, -0.06, -0.08), (-0.16, 0.06, -0.04), 0.003, 60, sym=True)
    pcs += sf.pieces([], {'base': K.painter(PELICAN['leg'], 0, -0.08, -0.05, dark=0.85, light=1.0)}, ao_field=allf, ao_scale=0.01)
    for s_ in (1, -1):
        e, _, _ = K.eye(body, HC, (0.235, s_ * 0.045, 0.085), 0.011, n=8, rings=2)
        pcs.append(e)

    # The wings: the gull's airfoil, broader and longer, painted grey-brown with dark primaries.
    root_y, tip_y = 0.02, 0.7
    wing, s_of, c_of = gull_wing(root_y, tip_y)
    wing.V = wing.V * np.array((1.6, 1.0, 1.3))
    tip = lambda P: (s_of(P) + 0.25 * (c_of(P) - 0.5) - 0.72) * 0.4

    def upper(V, N, U, Aocc):
        t = G.smoothstep(-0.35, 0.35, N[:, 2])
        k = (0.92 + 0.1 * t) * (0.85 + 0.15 * Aocc)
        col = G.l2s(PELICAN['under'])[None] * (1 - t[:, None]) + G.l2s(PELICAN['body'])[None] * t[:, None]
        return G.s2l(np.clip(col * k[:, None], 0, 1)), 1

    def dark(V, N, U, Aocc):
        k = 0.85 + 0.25 * G.smoothstep(-0.4, 0.5, N[:, 2])
        return G.shade_srgb(PELICAN['tip'], k), 0
    wl = G.paint_piece(wing, [('tip', tip)], {'base': upper, 'tip': dark})
    wr = [p.mirrored_y() for p in wl]
    piv = 0.05
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('WingL', (0.0, piv, 0.03), wl, motion='flap about X (the body axis), -40..+40 deg'),
             K.Part('WingR', (0.0, -piv, 0.03), wr, motion='flap about X (mirror of WingL)')]
    return K.Model('Pelican', parts, {1: PELICAN['body'], 2: PELICAN['bill']}, 2400,
                   extra={'origin': 'body centre (flying)', 'head': '+X', 'wingspan': 1.4},
                   attach={'Beak': ((0.52, 0, 0.0), 'Body')})


# ================================================================ seagull (standing, static)
def build_seagull_standing():
    HC = np.array((0.118, 0, 0.312))
    pitch = G.rot((0, 1, 0), math.radians(-14))
    body0 = G.ellipsoid((-0.005, 0, 0.178), (0.13, 0.068, 0.074), pitch)
    chest = G.ellipsoid((0.058, 0, 0.19), (0.078, 0.066, 0.084))
    rear = G.round_cone((-0.03, 0, 0.17), (-0.15, 0, 0.13), 0.058, 0.02)
    tail = G.ellipsoid((-0.172, 0, 0.123), (0.05, 0.036, 0.011), G.rot((0, 1, 0), math.radians(14)))
    neck = G.round_cone((0.06, 0, 0.21), (0.105, 0, 0.29), 0.056, 0.045)
    head = G.ellipsoid(HC, (0.052, 0.046, 0.047))
    beakf = G.round_cone((0.157, 0, 0.306), (0.218, 0, 0.297), 0.0145, 0.0062)
    gonys = G.sphere((0.197, 0, 0.292), 0.007)
    wingf = G.mirror_y(G.ellipsoid((-0.045, 0.054, 0.19), (0.135, 0.022, 0.056), G.rot((0, 1, 0), math.radians(10))))
    primaries = G.mirror_y(G.round_cone((-0.12, 0.034, 0.158), (-0.235, 0.014, 0.128), 0.024, 0.006))
    body = G.blend(body0, (chest, 0.05), (rear, 0.05), (tail, 0.03), (neck, 0.04), (head, 0.035),
                   (beakf, 0.012), (gonys, 0.008), (wingf, 0.012), (primaries, 0.012))
    beak, spot = _gull_head_bits(HC, None, 0.156)
    upper = K.above([-0.26, -0.15, -0.08, -0.02, 0.03, 0.065, 0.09], [0.112, 0.128, 0.142, 0.155, 0.178, 0.215, 0.27], xmax=0.085)
    tipm = K.both(upper, lambda P: -0.118 - P[:, 0] - 0.3 * (P[:, 2] - 0.15))
    spotw = G.mirror_y(lambda P: 0.008 - np.linalg.norm(P - np.array((-0.205, 0.024, 0.136)), axis=1))

    def legs_f():
        fs = []
        for s in (1, -1):
            y = s * 0.03
            leg = G.round_cone((0.012, y, 0.13), (0.016, y, 0.012), 0.0085, 0.0065)
            foot = G.ellipsoid((0.04, y, 0.005), (0.034, 0.021, 0.005), G.rot((0, 0, 1), math.radians(s * 8)))
            fs.append(G.blend(leg, (foot, 0.008)))
        return G.union(*fs)
    legs = legs_f()
    allf = G.union(body, legs)
    sb = G.Surface(body, (-0.27, -0.1, 0.07), (0.25, 0.1, 0.38), 0.0028, 720, sym=True,
                   weight=lambda P: G.smoothstep(0.1, 0.16, P[:, 0]))
    white = K.painter(GULL['white'], 0, 0.1, 0.3, dark=0.78, light=1.0)
    grey = K.painter(GULL['grey'], 1, 0.1, 0.27, dark=0.84, light=1.06)
    pcs = sb.pieces([('spot', spot), ('beak', beak), ('mirror', spotw), ('tip', tipm), ('wing', upper)],
                    {'base': white, 'wing': grey,
                     'tip': K.painter(GULL['tip'], 0, 0.1, 0.25, dark=0.85, light=1.15),
                     'mirror': K.painter(GULL['white'], 0, 0.1, 0.25),
                     'beak': K.painter(GULL['beak'], 2, 0.27, 0.32, dark=0.82, light=1.06),
                     'spot': K.flat_painter(GULL['spot'], 0, 1.0)}, ao_field=allf, ao_scale=0.02)
    sl = G.Surface(legs, (-0.03, -0.07, -0.01), (0.09, 0.07, 0.15), 0.0018, 150, sym=True)
    pcs += sl.pieces([], {'base': K.painter(GULL['leg'], 0, 0.0, 0.13, dark=0.8, light=1.02)}, ao_field=allf, ao_scale=0.015)
    for s in (1, -1):
        e, _, _ = K.eye(body, HC, (0.152, s * 0.043, 0.333), 0.0112, n=8, rings=2)
        pcs.append(e)
    return K.Model('SeagullStanding', [K.Part('SeagullStanding', (0, 0, 0), pcs)],
                   {1: GULL['grey'], 2: GULL['beak']}, 1500, kind='static', extra={'origin': 'on the ground', 'head': '+X'})


# ================================================================ pigeon
PIGEON = {
    'grey': hexc('#9aa3b5'),       # blue-grey plumage (part 1)
    'dark': hexc('#4b4f5c'),       # wing bars, tail band
    'pale': hexc('#c3c9d6'),       # wing coverts
    'sheen_g': hexc('#5f9a7c'),    # neck sheen, green (part 2)
    'sheen_p': hexc('#8a6a9e'),    # neck sheen, purple
    'beak': hexc('#3b3a40'),
    'cere': hexc('#ece8e2'),
    'leg': hexc('#d9676a'),
}


def build_pigeon():
    body0 = G.ellipsoid((-0.005, 0, 0.12), (0.105, 0.072, 0.07), G.rot((0, 1, 0), math.radians(-10)))
    breast = G.ellipsoid((0.045, 0, 0.13), (0.075, 0.07, 0.078))
    rear = G.round_cone((-0.06, 0, 0.125), (-0.15, 0, 0.1), 0.05, 0.02)
    tail = G.ellipsoid((-0.165, 0, 0.098), (0.06, 0.038, 0.01), G.rot((0, 1, 0), math.radians(12)))
    wingf = G.mirror_y(G.ellipsoid((-0.04, 0.05, 0.135), (0.105, 0.024, 0.052), G.rot((0, 1, 0), math.radians(8))))
    body = G.blend(body0, (breast, 0.05), (rear, 0.04), (tail, 0.025), (wingf, 0.014))
    NECK = np.array((0.06, 0, 0.165))
    HC = np.array((0.112, 0, 0.228))
    neck = G.round_cone((0.03, 0, 0.14), (0.1, 0, 0.215), 0.05, 0.034)
    head = G.ellipsoid(HC, (0.038, 0.034, 0.035))
    beakf = G.round_cone((0.142, 0, 0.226), (0.17, 0, 0.217), 0.0075, 0.0035)
    cere = G.mirror_y(G.ellipsoid((0.144, 0.003, 0.231), (0.009, 0.006, 0.006)))
    headf = G.blend(head, (neck, 0.03), (beakf, 0.008), (cere, 0.004))

    def legs_f():
        fs = []
        for s in (1, -1):
            y = s * 0.024
            leg = G.round_cone((0.0, y, 0.08), (0.008, y, 0.012), 0.009, 0.0065)
            toes = [G.round_cone((0.008, y, 0.006), (0.04, y + s * 0.006, 0.004), 0.0045, 0.0035),
                    G.round_cone((0.008, y, 0.006), (0.034, y + s * 0.02, 0.004), 0.0042, 0.0032),
                    G.round_cone((0.008, y, 0.006), (-0.014, y, 0.004), 0.0042, 0.0032)]
            fs.append(G.blend(leg, *[(t, 0.006) for t in toes]))
        return G.union(*fs)
    legs = legs_f()
    allf = G.union(body, headf, legs)

    wing_m = K.side_ellipse(-0.05, 0.135, 0.1, 0.045, math.radians(10), ymin=0.03)
    tailband = lambda P: np.minimum(-0.19 - P[:, 0], 0.4)
    side_uv = A.side_uv(A.PIGEON_SIDE, 'pigeon_side')        # the two dark wing bars are painted
    sb = G.Surface(body, (-0.25, -0.1, 0.03), (0.15, 0.1, 0.22), 0.0024, 470, sym=True)
    grey = K.painter(PIGEON['grey'], 1, 0.06, 0.19, dark=0.78, light=1.06, uv=side_uv)
    pcs = sb.pieces([('band', tailband), ('wing', wing_m)],
                    {'base': grey, 'wing': K.painter(PIGEON['pale'], 1, 0.06, 0.19, dark=0.8, light=1.04, uv=side_uv),
                     'band': K.painter(PIGEON['dark'], 0, 0.06, 0.19, dark=0.85, light=1.1, uv=side_uv)}, ao_field=allf, ao_scale=0.02)
    sl = G.Surface(legs, (-0.03, -0.06, -0.006), (0.06, 0.06, 0.1), 0.0015, 130, sym=True)
    pcs += sl.pieces([], {'base': K.painter(PIGEON['leg'], 0, 0.0, 0.08, dark=0.8, light=1.04)}, ao_field=allf, ao_scale=0.012)

    # head: neck sheen (part 2) from green above to purple below
    sheen = K.both(lambda P: 0.205 - P[:, 2] + 0.25 * (P[:, 0] - 0.08), lambda P: P[:, 2] - 0.128)

    def sheen_paint(V, N, Aocc):
        t = G.smoothstep(0.14, 0.2, V[:, 2])[:, None]
        base = G.l2s(PIGEON['sheen_p'])[None] * (1 - t) + G.l2s(PIGEON['sheen_g'])[None] * t
        k = K.soft_shade(V, N, Aocc, 0.13, 0.25, dark=0.82, light=1.12)
        return G.s2l(np.clip(base * k[:, None], 0, 1)), 2
    beak_m = lambda P: 0.0012 - beakf(P)
    cere_m = lambda P: 0.0105 - np.linalg.norm((P - np.array((0.145, 0.0, 0.232))) * np.array((1.0, 0.75, 1.3)), axis=1)
    sh = G.Surface(headf, (-0.03, -0.07, 0.08), (0.19, 0.07, 0.28), 0.002, 330, sym=True,
                   weight=lambda P: G.smoothstep(0.12, 0.15, P[:, 0]))
    hp = sh.pieces([('cere', cere_m), ('beak', beak_m), ('sheen', sheen)],
                   {'base': K.painter(PIGEON['grey'], 1, 0.13, 0.27, dark=0.8, light=1.08),
                    'sheen': sheen_paint,
                    'beak': K.painter(PIGEON['beak'], 0, 0.21, 0.235, dark=0.85, light=1.15),
                    'cere': K.painter(PIGEON['cere'], 0, 0.21, 0.24, dark=0.9, light=1.0)}, ao_field=allf, ao_scale=0.015)
    for s in (1, -1):
        e, _, _ = K.eye(headf, HC, (0.135, s * 0.03, 0.242), 0.0098, kind='eye_bird', n=8, rings=2)
        hp.append(e)
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('Head', NECK, hp, motion='peck: pitch about Y, 0..70 deg nose-down; bob: slide along X')]
    return K.Model('Pigeon', parts, {1: PIGEON['grey'], 2: PIGEON['sheen_g']}, 1500,
                   extra={'origin': 'on the ground', 'head': '+X'}, attach={'Beak': ((0.172, 0, 0.216), 'Head')})


# ================================================================ duck (a mallard drake, floating)
DUCK = {
    'body': hexc('#d9d4ca'),       # pale grey-cream flanks (part 1)
    'back': hexc('#9b9286'),
    'breast': hexc('#8c4d36'),
    'head': hexc('#2f7a55'),
    'ring': hexc('#f3f0e8'),
    'tail': hexc('#2a2a30'),
    'speculum': hexc('#4d5fc0'),
    'bill': hexc('#ecc64c'),       # part 2
    'nail': hexc('#3a3330'),
}


def build_duck():
    W = 0.0                                     # the waterline
    body0 = G.ellipsoid((0.0, 0, 0.035), (0.155, 0.098, 0.082))
    breast = G.ellipsoid((0.075, 0, 0.05), (0.09, 0.088, 0.08))
    stern = G.round_cone((-0.08, 0, 0.05), (-0.185, 0, 0.098), 0.06, 0.014)
    wingf = G.mirror_y(G.ellipsoid((-0.035, 0.064, 0.078), (0.11, 0.034, 0.042), G.rot((0, 1, 0), math.radians(6))))
    keel = G.plane((0, 0, -0.045), (0, 0, -1))
    curl = G.tube([(-0.165, 0, 0.098), (-0.155, 0, 0.13), (-0.135, 0, 0.138), (-0.128, 0, 0.122)], [0.008, 0.007, 0.006, 0.005], n=10)
    body = G.blend(body0, (breast, 0.05), (stern, 0.05), (wingf, 0.016), (curl, 0.006), (keel, 0.01, 'int'))
    NECK = np.array((0.095, 0, 0.1))
    HC = np.array((0.142, 0, 0.198))
    neck = G.round_cone((0.07, 0, 0.07), (0.13, 0, 0.18), 0.05, 0.037)
    head = G.ellipsoid(HC, (0.052, 0.042, 0.046))
    crown = G.ellipsoid((0.13, 0, 0.215), (0.045, 0.034, 0.038))
    cheek = G.mirror_y(G.ellipsoid((0.15, 0.018, 0.188), (0.035, 0.026, 0.03)))
    bill = G.ellipsoid((0.215, 0, 0.18), (0.048, 0.023, 0.0115), G.rot((0, 1, 0), math.radians(14)))
    headf = G.blend(head, (crown, 0.02), (cheek, 0.02), (neck, 0.035), (bill, 0.014))
    allf = G.union(body, headf)

    wing_m = K.above([-0.2, -0.13, -0.06, 0.0, 0.05, 0.08], [0.085, 0.07, 0.066, 0.072, 0.09, 0.13])
    spec = K.side_ellipse(-0.088, 0.083, 0.026, 0.013, math.radians(-8), ymin=0.04)
    tail_m = lambda P: -0.135 - P[:, 0] + 0.5 * (P[:, 2] - 0.05)
    breast_m = K.both(lambda P: P[:, 0] - 0.06 - 0.15 * (P[:, 2] - 0.05), lambda P: P[:, 2] + 0.03)
    sb = G.Surface(body, (-0.22, -0.12, -0.06), (0.18, 0.12, 0.17), 0.0028, 430, sym=True)
    cream = K.painter(DUCK['body'], 1, -0.02, 0.12, dark=0.8, light=1.05)
    pcs = sb.pieces([('spec', spec), ('tail', tail_m), ('breast', breast_m), ('wing', wing_m)],
                    {'base': cream, 'wing': K.painter(DUCK['back'], 1, -0.02, 0.12, dark=0.82, light=1.08),
                     'spec': K.painter(DUCK['speculum'], 0, 0.04, 0.1, dark=0.85, light=1.15),
                     'tail': K.painter(DUCK['tail'], 0, 0.0, 0.14, dark=0.85, light=1.2),
                     'breast': K.painter(DUCK['breast'], 0, -0.02, 0.12, dark=0.8, light=1.08)},
                    ao_field=allf, ao_scale=0.025)
    ring = K.both(lambda P: 0.0055 - np.abs(P[:, 2] - 0.118 - 0.55 * (P[:, 0] - 0.1)), lambda P: 0.2 - P[:, 0])
    green = lambda P: P[:, 2] - 0.118 - 0.55 * (P[:, 0] - 0.1)
    bill_m = lambda P: -G.ellipsoid((0.222, 0, 0.18), (0.05, 0.03, 0.022), G.rot((0, 1, 0), math.radians(14)))(P)
    nail = lambda P: 0.008 - np.linalg.norm((P - np.array((0.262, 0, 0.17))) * np.array((1, 0.8, 1)), axis=1)
    sh = G.Surface(headf, (0.0, -0.07, 0.0), (0.28, 0.07, 0.26), 0.0022, 300, sym=True,
                   weight=lambda P: G.smoothstep(0.17, 0.2, P[:, 0]))

    def head_green(V, N, Aocc):
        k = K.soft_shade(V, N, Aocc, 0.13, 0.24, dark=0.75, light=1.18)
        # a lighter, bluer sheen across the crown
        t = G.smoothstep(0.15, 0.85, N[:, 2])[:, None] * 0.35
        base = G.l2s(DUCK['head'])[None] * (1 - t) + G.l2s(hexc('#3f8f86'))[None] * t
        return G.s2l(np.clip(base * k[:, None], 0, 1)), 0
    hp = sh.pieces([('nail', nail), ('bill', bill_m), ('ring', ring), ('green', green)],
                   {'base': K.painter(DUCK['breast'], 0, 0.04, 0.12, dark=0.8, light=1.08),
                    'green': head_green, 'ring': K.painter(DUCK['ring'], 0, 0.08, 0.14, dark=0.85, light=1.02),
                    'bill': K.painter(DUCK['bill'], 2, 0.16, 0.2, dark=0.85, light=1.06),
                    'nail': K.flat_painter(DUCK['nail'], 0, 1.0)}, ao_field=allf, ao_scale=0.015)
    for s in (1, -1):
        e, _, _ = K.eye(headf, HC, (0.175, s * 0.04, 0.214), 0.0095, n=8, rings=2)
        hp.append(e)
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('Head', NECK, hp, motion='dabble: pitch about Y, 0..45 deg bill-down; look: turn about Z')]
    return K.Model('Duck', parts, {1: DUCK['body'], 2: DUCK['bill']}, 1500,
                   extra={'origin': 'centre of the waterline (z = 0 is the water surface)', 'head': '+X'},
                   attach={'Bill': ((0.266, 0, 0.167), 'Head')})


# ================================================================ black kite (flying), for Kamakura's beach
KITE = {
    'body': hexc('#3f2f26'),      # dark brown mantle and upper wing (part 1)
    'under': hexc('#523629'),     # rufous-brown underparts, streaked
    'head': hexc('#7a6858'),      # a paler, greyish-brown head
    'mask': hexc('#2e221c'),      # the dark patch behind the eye
    'bar': hexc('#87705a'),       # the pale bar across the upper wing coverts
    'prim': hexc('#221b18'),      # dark primaries and fingers
    'window': hexc('#d8c4a2'),    # the pale "window" under the base of the primaries
    'bill': hexc('#b8ac7e'),      # yellow-grey bill and cere (part 2)
    'hook': hexc('#3a3836'),      # the dark hooked tip
    'feet': hexc('#d2b24e'),
}
# The kite's wing planform, (span s 0 at the shoulder .. 0.82 where the fingers part): leading edge, trailing edge
# (x, metres: the head is +X) and thickness. Broad and blunt, the wrist pushed forward, unlike the gull's pointed wing.
_KWING = {
    's':  [0.0, 0.15, 0.38, 0.58, 0.72, 0.82],
    'le': [0.10, 0.118, 0.132, 0.122, 0.104, 0.088],
    'te': [-0.17, -0.185, -0.178, -0.15, -0.118, -0.086],
    'th': [0.05, 0.04, 0.028, 0.02, 0.014, 0.01],
}
_KFINGERS = [(0.074, 0.92), (0.046, 0.98), (0.018, 1.0), (-0.01, 0.98), (-0.038, 0.945), (-0.064, 0.9)]


def kite_wing(root_y, tip_y, stations=12):
    """The left wing (+Y) of a gliding kite, as Pieces: a broad airfoil loft to the hand, its hand drooping a little,
    and six separate fingered primaries fanned out beyond it, their tips turned up. Painted dark brown, a pale bar
    across the upper coverts, and the pale window under the base of the primaries."""
    span = tip_y - root_y
    s_end = _KWING['s'][-1]
    u = np.linspace(0, 1, stations)
    S = s_end * (1 - (1 - u) ** 1.25)
    le = np.interp(S, _KWING['s'], _KWING['le']); te = np.interp(S, _KWING['s'], _KWING['te'])
    th = np.interp(S, _KWING['s'], _KWING['th'])
    zc = lambda s: 0.02 * np.sin(math.pi * np.minimum(s, 1.0) * 0.9) - 0.045 * np.asarray(s) ** 2
    f = lambda c: 2.598 * np.sqrt(c) * (1 - c)
    reg = A.inset('feather', 0.006)
    rings = []; UV = []
    for i, s in enumerate(S):
        y = root_y + s * span
        ring = []
        for c, top in zip(_C, _TOP):
            x = le[i] + c * (te[i] - le[i])
            z = zc(s) + (0.75 if top else -0.25) * th[i] * f(c)
            ring.append((x, y, z))
            UV.append((reg[0] + (reg[2] - reg[0]) * c, reg[1] + (reg[3] - reg[1]) * s / s_end * 0.8))
        rings.append(ring)
    p = G.loft(rings, True, True)
    UV.append((reg[0] + (reg[2] - reg[0]) * 0.4, reg[1])); UV.append((reg[0] + (reg[2] - reg[0]) * 0.4, reg[1] + (reg[3] - reg[1]) * 0.8))
    p.U = np.array(UV)
    G.outward(p)
    p.N = G.vnormals(p.V, p.T)
    s_of = lambda P: (np.abs(P[:, 1]) - root_y) / span

    def c_of(P):
        s = np.clip(s_of(P), 0, s_end)
        l = np.interp(s, _KWING['s'], _KWING['le']); t = np.interp(s, _KWING['s'], _KWING['te'])
        return (l - P[:, 0]) / np.maximum(l - t, 1e-4)

    def paint(V, N, U, Aocc):
        s = s_of(V); c = c_of(V)
        up = G.smoothstep(-0.3, 0.3, N[:, 2])[:, None]
        top = G.l2s(KITE['body'])[None] * np.ones((len(V), 1))
        bar = (G.smoothstep(0.1, 0.2, c) * G.smoothstep(0.46, 0.36, c - 0.25 * s) * G.smoothstep(0.08, 0.18, s)
               * G.smoothstep(0.6, 0.48, s))[:, None]
        top = top * (1 - 0.8 * bar) + G.l2s(KITE['bar'])[None] * 0.8 * bar
        prim = G.smoothstep(0.55, 0.72, s + 0.15 * (c - 0.5))[:, None]
        top = top * (1 - prim) + G.l2s(KITE['prim'])[None] * prim
        und = G.l2s(KITE['under'])[None] * np.ones((len(V), 1))
        win = (G.smoothstep(0.52, 0.64, s) * G.smoothstep(0.18, 0.32, c))[:, None]
        und = und * (1 - win) + G.l2s(KITE['window'])[None] * win
        dark = (G.smoothstep(0.85, 1.0, c) * G.smoothstep(0.3, 0.5, s))[:, None] * 0.7     # the dark trailing edge
        und = und * (1 - dark) + G.l2s(KITE['prim'])[None] * dark
        col = und * (1 - up) + top * up
        k = (0.9 + 0.12 * up[:, 0]) * (0.85 + 0.15 * Aocc)
        return G.s2l(np.clip(col * k[:, None], 0, 1)), 1
    pieces = G.paint_piece(p, [], {'base': paint})
    # the fingers: separate primaries from inside the hand out to the tip, fanned and turned up at their ends
    y0 = root_y + 0.74 * span
    for k, (xb, ls) in enumerate(_KFINGERS):
        yt = root_y + ls * span
        base = np.array((xb, y0, float(zc(0.74))))
        tip = np.array((xb * 1.55 - 0.012, yt, float(zc(0.82)) + 0.03))
        mid = base + (tip - base) * 0.55 + np.array((0, 0, -0.004))
        w = 0.029 if k not in (0, 5) else 0.024
        fp = K.ribbon([base, mid, tip], [w, w * 0.9, w * 0.3], [0.004, 0.0032, 0.0015],
                      lambda t, q, tg: (0, 0, 1), n=5, sides=6)
        t = np.clip((fp.V[:, 1] - y0) / (yt - y0), 0, 1)
        up = G.smoothstep(-0.3, 0.3, fp.N[:, 2])[:, None]
        win = G.smoothstep(0.42, 0.2, t)[:, None] * (1 - up)
        col = G.l2s(KITE['prim'])[None] * (1 - win) + G.l2s(KITE['window'])[None] * win
        fp.color(G.s2l(np.clip(col * (0.9 + 0.15 * up), 0, 1))); fp.part(0)
        pieces.append(fp)
    return pieces


def build_black_kite():
    """Kamakura's black kite (tobi) gliding over the beach, the bird that swoops to snatch food: dark brown, a paler,
    greyish head, broad wings with six fingered primaries and a pale window under their base, a pale bar across the upper
    wing, a long, shallowly forked tail and a hooked yellow-grey bill: the Seagull's rig (Body, WingL, WingR at the
    shoulders, head toward +X, origin at the body's centre), 1.5 m across."""
    HC = np.array((0.15, 0, 0.032))
    chest = G.ellipsoid((0.02, 0, 0.0), (0.13, 0.075, 0.068))
    rear = G.round_cone((-0.03, 0, 0.0), (-0.16, 0, 0.01), 0.064, 0.03)
    neck = G.round_cone((0.07, 0, 0.008), (0.135, 0, 0.026), 0.058, 0.044)
    head = G.ellipsoid(HC, (0.052, 0.042, 0.043))
    brow = G.ellipsoid(HC + np.array((0.01, 0, 0.018)), (0.04, 0.036, 0.02))
    billf = G.tube([(0.178, 0, 0.034), (0.2, 0, 0.035), (0.216, 0, 0.026), (0.219, 0, 0.01)], [0.0135, 0.01, 0.0065, 0.002])
    lower = G.round_cone((0.18, 0, 0.022), (0.205, 0, 0.018), 0.009, 0.004)

    def tailf(P):
        """A long tail, widening to its end and forked: a slab whose end is cut back in a shallow V."""
        x0, x1, z0 = -0.13, -0.39, 0.008
        tt = np.clip((x0 - P[:, 0]) / (x0 - x1), 0, 1)
        w = 0.038 + 0.062 * tt
        th = 0.012 - 0.004 * tt
        xend = x1 + 0.05 * np.clip(1 - np.abs(P[:, 1]) / 0.08, 0, 1)
        return np.maximum.reduce([np.abs(P[:, 2] - z0) - th, np.abs(P[:, 1]) - w, P[:, 0] - x0, xend - P[:, 0]])
    feet = G.mirror_y(G.ellipsoid((-0.09, 0.026, -0.05), (0.032, 0.014, 0.01), G.rot((0, 1, 0), math.radians(-10))))
    body = G.blend(chest, (rear, 0.05), (tailf, 0.02), (neck, 0.04), (head, 0.03), (brow, 0.015), (billf, 0.008), (lower, 0.006))
    allf = G.union(body, feet)
    bill = lambda P: 0.0016 - G.union(billf, lower)(P)
    hook = K.both(bill, lambda P: P[:, 0] - 0.205)
    cere = lambda P: 0.012 - np.linalg.norm((P - np.array((0.181, 0, 0.038))) * np.array((1.0, 0.8, 1.2)), axis=1)
    headr = lambda P: 0.065 - np.linalg.norm((P - HC) * np.array((0.85, 1.0, 1.0)), axis=1)
    mask = K.both(K.side_ellipse(0.13, 0.028, 0.03, 0.011, math.radians(-8)), lambda P: np.abs(P[:, 1]) - 0.025)
    tail = lambda P: -0.14 - P[:, 0]

    def plumage(V, N, Aocc):
        up = G.smoothstep(-0.5, 0.6, N[:, 2])[:, None]
        streak = 1 - 0.1 * (0.5 + 0.5 * np.sin(V[:, 1] * 260 + V[:, 0] * 40))[:, None] * (1 - up)
        col = (G.l2s(KITE['under'])[None] * streak) * (1 - up) + G.l2s(KITE['body'])[None] * up
        k = K.soft_shade(V, N, Aocc, -0.05, 0.06, dark=0.82, light=1.08)
        return G.s2l(np.clip(col * k[:, None], 0, 1)), 1

    def tail_paint(V, N, Aocc):
        bars = 1 - 0.13 * (0.5 + 0.5 * np.cos((V[:, 0] + 0.14) * 2 * math.pi / 0.034))
        k = K.soft_shade(V, N, Aocc, -0.02, 0.03, dark=0.85, light=1.06) * bars
        base = G.lerp(KITE['under'], KITE['body'], G.smoothstep(-0.4, 0.4, N[:, 2]))
        return G.s2l(np.clip(G.l2s(base) * k[:, None], 0, 1)), 1
    sb = G.Surface(body, (-0.42, -0.11, -0.09), (0.24, 0.11, 0.1), 0.0034, 760, sym=True,
                   weight=lambda P: G.smoothstep(0.12, 0.18, P[:, 0]))
    pcs = sb.pieces([('hook', hook), ('cere', cere), ('bill', bill), ('mask', mask), ('head', headr), ('tail', tail)],
                    {'base': plumage, 'tail': tail_paint,
                     'head': K.painter(KITE['head'], 0, -0.01, 0.07, dark=0.82, light=1.06),
                     'mask': K.painter(KITE['mask'], 0, -0.01, 0.07, dark=0.85, light=1.05),
                     'bill': K.painter(KITE['bill'], 2, 0.0, 0.045, dark=0.82, light=1.06),
                     'cere': K.painter(KITE['bill'], 2, 0.0, 0.045, dark=0.9, light=1.08),
                     'hook': K.painter(KITE['hook'], 0, 0.0, 0.04, dark=0.85, light=1.2)}, ao_field=allf, ao_scale=0.02)
    sf = G.Surface(feet, (-0.14, -0.05, -0.07), (-0.05, 0.05, -0.03), 0.003, 50, sym=True)
    pcs += sf.pieces([], {'base': K.painter(KITE['feet'], 0, -0.065, -0.04, dark=0.85, light=1.0)}, ao_field=allf, ao_scale=0.01)
    for s_ in (1, -1):
        e, _, _ = K.eye(body, HC, (0.178, s_ * 0.04, 0.05), 0.0095, n=8, rings=2)
        pcs.append(e)
    root_y, tip_y = 0.025, 0.75
    wl = kite_wing(root_y, tip_y)
    wr = [p.mirrored_y() for p in wl]
    piv = 0.045
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('WingL', (0.0, piv, 0.02), wl, motion='flap about X (the body axis), -40..+40 deg'),
             K.Part('WingR', (0.0, -piv, 0.02), wr, motion='flap about X (mirror of WingL)')]
    return K.Model('BlackKite', parts, {1: KITE['body'], 2: KITE['bill']}, 2400,
                   extra={'origin': 'body centre (flying)', 'head': '+X', 'wingspan': 1.5},
                   attach={'Beak': ((0.22, 0, 0.012), 'Body'), 'Talons': ((-0.09, 0, -0.06), 'Body')})


# ================================================================ jungle crow (standing)
CROW = {
    'black': hexc('#161619'),      # glossy black plumage (part 1)
    'sheen': hexc('#2d2f3e'),      # the blue-violet gloss where the light catches it
    'bill': hexc('#151517'),       # part 2
    'leg': hexc('#1d1d20'),
}


def build_crow():
    """A jungle crow (large-billed crow), the crow of every Kamakura street: glossy black all over with a blue-violet
    sheen, a heavy, arched bill and a steep, domed forehead, a long tail past the folded wings, standing on strong black
    legs: the Pigeon's rig (Body, Head at the neck's base, origin on the ground, head toward +X), 0.55 m long."""
    pitch = G.rot((0, 1, 0), math.radians(-22))
    body0 = G.ellipsoid((-0.03, 0, 0.21), (0.135, 0.08, 0.082), pitch)
    breast = G.ellipsoid((0.04, 0, 0.215), (0.085, 0.076, 0.088))
    belly = G.ellipsoid((-0.03, 0, 0.165), (0.09, 0.066, 0.05))
    rear = G.round_cone((-0.1, 0, 0.185), (-0.21, 0, 0.142), 0.06, 0.03)
    # a long, rounded tail held in line with the back: wide and flat, thickest at its root
    tail = G.ellipsoid((-0.27, 0, 0.134), (0.11, 0.044, 0.016), G.rot((0, 1, 0), math.radians(19)))
    wingf = G.mirror_y(G.ellipsoid((-0.07, 0.058, 0.212), (0.16, 0.027, 0.068), G.rot((0, 1, 0), math.radians(19))))
    prim = G.mirror_y(G.round_cone((-0.15, 0.04, 0.182), (-0.265, 0.02, 0.15), 0.03, 0.012))
    thigh = G.mirror_y(G.ellipsoid((-0.005, 0.04, 0.14), (0.04, 0.025, 0.04)))
    body = G.blend(body0, (breast, 0.05), (belly, 0.04), (rear, 0.045), (tail, 0.03), (wingf, 0.016), (prim, 0.02),
                   (thigh, 0.03))
    NECK = np.array((0.07, 0, 0.255))
    HC = np.array((0.135, 0, 0.335))
    neck = G.round_cone((0.04, 0, 0.23), (0.12, 0, 0.315), 0.062, 0.046)
    throat = G.ellipsoid((0.115, 0, 0.29), (0.045, 0.04, 0.04))
    head = G.ellipsoid(HC, (0.052, 0.045, 0.047))
    crown = G.ellipsoid(HC + np.array((0.008, 0, 0.022)), (0.044, 0.04, 0.034))     # the steep, domed forehead
    culmen = G.tube([(0.165, 0, 0.346), (0.2, 0, 0.347), (0.235, 0, 0.336), (0.258, 0, 0.318)], [0.019, 0.014, 0.008, 0.0025])
    mand = G.round_cone((0.168, 0, 0.322), (0.245, 0, 0.317), 0.015, 0.0035)
    headf = G.blend(head, (crown, 0.03), (neck, 0.035), (throat, 0.02), (culmen, 0.01), (mand, 0.008))

    def legs_f():
        fs = []
        for s in (1, -1):
            y = s * 0.034
            leg = G.round_cone((0.0, y, 0.14), (0.01, y, 0.014), 0.011, 0.0075)
            toes = [G.round_cone((0.01, y, 0.007), (0.062, y + s * 0.006, 0.005), 0.006, 0.0042),
                    G.round_cone((0.01, y, 0.007), (0.05, y + s * 0.03, 0.005), 0.0055, 0.004),
                    G.round_cone((0.01, y, 0.007), (0.05, y - s * 0.016, 0.005), 0.0055, 0.004),
                    G.round_cone((0.01, y, 0.007), (-0.035, y, 0.005), 0.0058, 0.004)]
            fs.append(G.blend(leg, *[(t, 0.007) for t in toes]))
        return G.union(*fs)
    legs = legs_f()
    allf = G.union(body, headf, legs)

    def glossy(z0, z1):
        def fn(V, N, Aocc):
            k = K.soft_shade(V, N, Aocc, z0, z1, dark=0.8, light=1.1)
            sh = (G.smoothstep(0.2, 0.9, N[:, 2]) * 0.6 + 0.2 * G.smoothstep(0.5, 0.95, np.abs(N[:, 1])))[:, None]
            col = G.l2s(CROW['black'])[None] * (1 - sh) + G.l2s(CROW['sheen'])[None] * sh
            return G.s2l(np.clip(col * k[:, None], 0, 1)), 1
        return fn
    wing_m = K.side_ellipse(-0.08, 0.205, 0.15, 0.055, math.radians(18), ymin=0.035)
    sb = G.Surface(body, (-0.4, -0.11, 0.05), (0.16, 0.11, 0.32), 0.0034, 560, sym=True)
    pcs = sb.pieces([('wing', wing_m)], {'base': glossy(0.1, 0.28), 'wing': glossy(0.12, 0.27)}, ao_field=allf, ao_scale=0.025)
    sl = G.Surface(legs, (-0.05, -0.08, -0.006), (0.08, 0.08, 0.16), 0.0018, 170, sym=True)
    pcs += sl.pieces([], {'base': K.painter(CROW['leg'], 0, 0.0, 0.14, dark=0.85, light=1.25)}, ao_field=allf, ao_scale=0.012)
    bill_m = lambda P: 0.0014 - G.union(culmen, mand)(P)
    sh = G.Surface(headf, (-0.04, -0.09, 0.15), (0.28, 0.09, 0.41), 0.0024, 440, sym=True,
                   weight=lambda P: G.smoothstep(0.13, 0.17, P[:, 0]))
    hp = sh.pieces([('bill', bill_m)], {'base': glossy(0.24, 0.38),
                                        'bill': K.painter(CROW['bill'], 2, 0.31, 0.35, dark=0.85, light=1.5)},
                   ao_field=allf, ao_scale=0.015)
    for s in (1, -1):
        e, _, _ = K.eye(headf, HC, (0.16, s * 0.042, 0.35), 0.0095, n=8, rings=2)
        hp.append(e)
    parts = [K.Part('Body', (0, 0, 0), pcs),
             K.Part('Head', NECK, hp, motion='peck: pitch about Y, 0..70 deg nose-down; bob: slide along X')]
    model = K.Model('Crow', parts, {1: CROW['black'], 2: CROW['bill']}, 1700,
                    extra={'origin': 'on the ground', 'head': '+X'}, attach={'Beak': ((0.258, 0, 0.318), 'Head')})
    return K.scaled(model, 0.87)          # modelled a little large: 0.55 m from bill to tail
