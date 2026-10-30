# Small creatures for the ANIMALS kit: the beach crab (Body, ClawL, ClawR; it faces the camera
# and scuttles sideways) and the park butterfly (Body, WingL, WingR). See kit_animals_common.py.
import math
import numpy as np
import kit_animals_geo as G
import kit_animals_common as K
import kit_animals_atlas as A

hexc = G.hexc


_scaled = K.scaled


# ================================================================ crab
CRAB = {
    'shell': hexc('#e86a3f'),      # coral (part 1)
    'belly': hexc('#f7cba4'),
    'tip': hexc('#a93c2a'),
    'eye': hexc('#2a2224'),
}


def build_crab():
    ground = G.plane((0, 0, 0.0), (0, 0, -1))
    cara = G.ellipsoid((0, 0.008, 0.07), (0.105, 0.078, 0.042))
    rim = G.ellipsoid((0, -0.026, 0.066), (0.1, 0.052, 0.037))
    belly = G.ellipsoid((0, 0.004, 0.05), (0.086, 0.064, 0.027))
    bumps = G.mirror_x(G.union(G.sphere((0.052, -0.068, 0.074), 0.012), G.sphere((0.083, -0.048, 0.07), 0.011),
                               G.sphere((0.098, -0.018, 0.068), 0.01)))
    stalk = G.mirror_x(G.round_cone((0.026, -0.046, 0.09), (0.032, -0.057, 0.127), 0.0078, 0.0068))
    eyeball = G.mirror_x(G.sphere((0.032, -0.058, 0.136), 0.0135))
    body = G.blend(cara, (rim, 0.03), (belly, 0.02), (bumps, 0.012), (stalk, 0.008), (eyeball, 0.006))

    def claw_f(sx):
        piv = np.array((sx * 0.07, -0.045, 0.062))
        arm = G.round_cone(piv, (sx * 0.112, -0.082, 0.083), 0.015, 0.017)
        palm = G.ellipsoid((sx * 0.128, -0.092, 0.113), (0.029, 0.026, 0.041), G.rot((0, 1, 0), math.radians(-14 * sx)))
        fixed = G.round_cone((sx * 0.138, -0.093, 0.143), (sx * 0.152, -0.097, 0.184), 0.0155, 0.0055)
        move = G.round_cone((sx * 0.113, -0.093, 0.147), (sx * 0.113, -0.097, 0.178), 0.0115, 0.0045)
        return G.blend(arm, (palm, 0.02), (fixed, 0.012), (move, 0.008)), piv

    claws = {'ClawL': claw_f(1), 'ClawR': claw_f(-1)}
    legs = []
    for sx in (-1, 1):
        for k, y in enumerate((-0.024, 0.01, 0.042)):
            path = G.catmull([(sx * 0.075, y, 0.056), (sx * 0.126, y - 0.004, 0.088), (sx * 0.162, y - 0.006, 0.058),
                              (sx * 0.172 - sx * 0.004 * k, y - 0.008, 0.003)], 5)
            legs.append(G.tube_mesh(path, np.linspace(0.0105, 0.0058, len(path)), sides=5))
    everything = G.union(body, *[f for f, _ in claws.values()])

    under = lambda P: 0.052 - P[:, 2] + 0.25 * np.maximum(-P[:, 1] - 0.05, 0)
    eyes_m = lambda P: 0.0145 - np.linalg.norm(np.column_stack([np.abs(P[:, 0]) - 0.032, P[:, 1] + 0.058, P[:, 2] - 0.136]), axis=1)
    face_uv = A.front_uv(A.CRAB_FACE, 'crab_face')
    shell = lambda uv=None: K.painter(CRAB['shell'], 1, 0.03, 0.11, dark=0.78, light=1.1, uv=uv)
    sb = G.Surface(body, (-0.14, -0.1, 0.0), (0.14, 0.1, 0.16), 0.0024, 420, sym=False)
    body_p = sb.pieces([('eyes', eyes_m), ('under', under)],
                       {'base': shell(face_uv), 'under': K.painter(CRAB['belly'], 0, 0.02, 0.07, dark=0.85, light=1.05, uv=face_uv),
                        'eyes': K.painter(CRAB['eye'], 0, 0.12, 0.15, dark=0.9, light=1.2)},
                       ao_field=everything, ao_scale=0.02)
    for sx in (-1, 1):
        c = np.array((sx * 0.032, -0.058, 0.136))
        d = G.unit(np.array((sx * 0.25, -1.0, 0.45)))
        e = G.bead(c + d * 0.0118, d, 0.0105, 0.4, n=8, rings=2, uvreg=A.inset('eye'))
        e.color(np.ones(3)).part(0)
        body_p.append(e)
    for L in legs:
        K.shade_piece(L, CRAB['shell'], 1, 0.0, 0.09, aofield=body, ao_scale=0.02, dark=0.8, light=1.08)
    body_p += legs
    parts = [K.Part('Body', (0, 0, 0), body_p)]
    for name, (f, piv) in claws.items():
        sx = 1 if name == 'ClawL' else -1
        lo = np.array((min(sx * 0.03, sx * 0.21), -0.14, 0.0)); hi = np.array((max(sx * 0.03, sx * 0.21), 0.0, 0.22))
        sc = G.Surface(f, lo, hi, 0.002, 175, sym=False)
        tip = lambda P: P[:, 2] - 0.168
        pcs = sc.pieces([('tip', tip)], {'base': K.painter(CRAB['shell'], 1, 0.06, 0.18, dark=0.8, light=1.1),
                                         'tip': K.painter(CRAB['tip'], 0, 0.06, 0.18, dark=0.85, light=1.1)},
                        ao_field=everything, ao_scale=0.02)
        parts.append(K.Part(name, piv, pcs, motion='wave/snap: rotate about Y (the depth axis, in the camera plane), -20..+35 deg'))
    return K.Model('Crab', parts, {1: CRAB['shell']}, 1500,
                   extra={'origin': 'on the ground', 'head': '-Y (faces the camera; scuttles sideways along X)'})


# ================================================================ butterfly
BUTTERFLY = {
    'wing': hexc('#f3a23c'),       # apricot (part 1; the pattern is painted in the atlas)
    'body': hexc('#3a2e2c'),
    'fuzz': hexc('#6e5848'),
}


def _wing_contour(n=34):
    s0, t0 = -0.004, 0.004
    pts = []
    for phi in np.linspace(math.radians(4), math.radians(176), n):
        d = np.array((math.cos(phi), math.sin(phi)))
        lo, hi = 0.0, 0.2
        for _ in range(40):
            m = 0.5 * (lo + hi)
            q = np.array((s0, t0)) + d * m
            if A.wing_outline(np.array([q[0]]), np.array([q[1]]))[0] < 0:
                lo = m
            else:
                hi = m
        pts.append(np.array((s0, t0)) + d * lo)
    return np.array((s0, t0)), np.array(pts)


def butterfly_wing(z=0.003, th=0.0016):
    """The left wing (+Y) spread flat: a thin double-sided plate with the atlas pattern."""
    root, C = _wing_contour()
    n = len(C)
    fr = [0.38, 0.72, 1.0]
    V = []; T = []; Nn = []; UV = []

    def add(s, t, zz, nrm):
        V.append((s, t, zz)); Nn.append(nrm); UV.append(A.wing_uv(s, t)); return len(V) - 1
    for side, zz, nz in ((0, z + th * 0.5, 1.0), (1, z - th * 0.5, -1.0)):
        c = add(root[0], root[1], zz, (0, 0, nz))
        rings = []
        for f in fr:
            rings.append([add(*(root + (p - root) * f), zz + (0.0005 if side == 0 else -0.0005) * (1 - f), (0, 0, nz)) for p in C])
        for i in range(n - 1):
            T.append((c, rings[0][i], rings[0][i + 1]) if side == 0 else (c, rings[0][i + 1], rings[0][i]))
            for r in range(len(fr) - 1):
                a, b, cc, d = rings[r][i], rings[r][i + 1], rings[r + 1][i + 1], rings[r + 1][i]
                T += [(a, d, cc), (a, cc, b)] if side == 0 else [(a, cc, d), (a, b, cc)]
    # the rim: a strip around the outline between the two plates
    top = [add(p[0], p[1], z + th * 0.5, None) for p in C]
    bot = [add(p[0], p[1], z - th * 0.5, None) for p in C]
    for i in range(n - 1):
        a, b, cc, d = top[i], top[i + 1], bot[i + 1], bot[i]
        T += [(a, b, cc), (a, cc, d)]
    out2 = np.gradient(C, axis=0); out2 = np.column_stack([out2[:, 1], -out2[:, 0]])
    out2 = G.unit(np.column_stack([out2, np.zeros(n)]))
    Nn = [x if x is not None else None for x in Nn]
    N = np.zeros((len(V), 3))
    for i, x in enumerate(Nn):
        if x is not None:
            N[i] = x
    for k, i in enumerate(top):
        N[i] = out2[k]
    for k, i in enumerate(bot):
        N[i] = out2[k]
    p = G.Piece(np.array(V), np.array(T), N)
    p.U = np.array(UV)
    # the outline runs from front to back: flip the rim normals if they point inward
    mid = C.mean(axis=0)
    if np.dot(out2[n // 2][:2], C[n // 2] - mid) < 0:
        N[top] *= -1; N[bot] *= -1; p.N = N
    G.orient_by_normals(p)
    return p


def build_butterfly():
    thorax = G.ellipsoid((0.004, 0, 0.0), (0.016, 0.0095, 0.0095))
    abdomen = G.round_cone((-0.008, 0, -0.001), (-0.05, 0, -0.005), 0.0085, 0.0035)
    head = G.sphere((0.0245, 0, 0.002), 0.0078)
    body = G.blend(thorax, (abdomen, 0.006), (head, 0.004))
    sb = G.Surface(body, (-0.065, -0.02, -0.02), (0.04, 0.02, 0.02), 0.0009, 220, sym=True)
    fuzz = lambda P: 0.016 - np.linalg.norm((P - np.array((0.004, 0, 0.003))) * np.array((1.0, 1.4, 1.4)), axis=1)
    body_p = sb.pieces([('fuzz', fuzz)], {'base': K.painter(BUTTERFLY['body'], 0, -0.01, 0.01, dark=0.85, light=1.2),
                                          'fuzz': K.painter(BUTTERFLY['fuzz'], 0, -0.01, 0.01, dark=0.85, light=1.15)})
    for s in (1, -1):
        path = G.catmull([(0.028, s * 0.003, 0.007), (0.042, s * 0.011, 0.022), (0.054, s * 0.02, 0.036), (0.06, s * 0.026, 0.04)], 5)
        ant = G.tube_mesh(path, np.linspace(0.0011, 0.0009, len(path)), sides=4)
        knob = G.lathe([(0, -0.0028), (0.0024, -0.0012), (0.0024, 0.0012), (0, 0.0028)], 5, t=path[-1])
        for q in (ant, knob):
            K.shade_piece(q, BUTTERFLY['body'], 0, -0.01, 0.04, dark=0.9, light=1.2)
        body_p += [ant, knob]
    for s in (1, -1):
        e, _, _ = K.eye(body, (0.0245, 0, 0.002), (0.03, s * 0.006, 0.005), 0.0034, n=6, rings=1, sink=0.3)
        body_p.append(e)

    wl = butterfly_wing()
    k = 0.92 + 0.1 * G.smoothstep(-0.5, 0.5, wl.N[:, 2])
    wl.color(G.shade_srgb(BUTTERFLY['wing'], k)).part(1)
    wr = wl.mirrored_y()
    parts = [K.Part('Body', (0, 0, 0), body_p),
             K.Part('WingL', (0.0, 0.003, 0.003), [wl], motion='flap about X (the body axis), 0..+80 deg up'),
             K.Part('WingR', (0.0, -0.003, 0.003), [wr], motion='flap about X (mirror of WingL)')]
    model = K.Model('Butterfly', parts, {1: BUTTERFLY['wing']}, 1500,
                    extra={'origin': 'body centre (flying)', 'head': '+X'})
    return _scaled(model, 0.85)
