# Four-legged animals for the ANIMALS kit: the dog, the cat and the squirrel. See
# kit_animals_common.py for the conventions (head +X, right flank toward the camera at -Y).
import math
import numpy as np
import kit_animals_geo as G
import kit_animals_common as K
import kit_animals_atlas as A

hexc = G.hexc


_scaled = K.scaled


# ================================================================ dog
DOG = {
    'fur': hexc('#cf8a52'),        # warm honey-ginger (part 1, the game recolours it)
    'cream': hexc('#f4e3c6'),      # muzzle, chest, socks, tail tip
    'ear': hexc('#b06e40'),        # ear flaps, a shade deeper than the fur (part 1)
    'collar': hexc('#d4473b'),     # part 2
    'tag': hexc('#f2c24e'),
    'mouth': hexc('#4a2c25'),
    'tongue': hexc('#e8788a'),
}


def build_dog():
    S = 0.89                      # designed a little large, scaled to ~0.55 m at the head
    # ---------------- fields (design units)
    chest = G.ellipsoid((0.065, 0, 0.30), (0.14, 0.115, 0.125))
    rump = G.ellipsoid((-0.105, 0, 0.305), (0.125, 0.11, 0.118))
    neckb = G.round_cone((0.09, 0, 0.33), (0.155, 0, 0.42), 0.09, 0.072)
    front = G.ellipsoid((0.14, 0, 0.30), (0.08, 0.09, 0.108))
    haunch = G.mirror_y(G.ellipsoid((-0.125, 0.06, 0.285), (0.09, 0.058, 0.10)))
    shoulder = G.mirror_y(G.ellipsoid((0.10, 0.066, 0.285), (0.066, 0.05, 0.08)))
    tuck = G.ellipsoid((0.0, 0, 0.13), (0.14, 0.2, 0.055))
    body = G.blend(chest, (rump, 0.08), (neckb, 0.06), (front, 0.05), (haunch, 0.035), (shoulder, 0.035),
                   (tuck, 0.05, 'sub'))

    HC = np.array((0.215, 0, 0.525))          # cranium centre
    cran = G.ellipsoid(HC, (0.112, 0.113, 0.104))
    muz = G.ellipsoid((0.31, 0, 0.485), (0.07, 0.058, 0.05))
    cheek = G.mirror_y(G.ellipsoid((0.262, 0.05, 0.478), (0.058, 0.05, 0.05)))
    chin = G.ellipsoid((0.297, 0, 0.458), (0.052, 0.04, 0.028))
    hneck = G.round_cone((0.11, 0, 0.35), (0.20, 0, 0.49), 0.072, 0.075)
    brow = G.mirror_y(G.sphere((0.282, 0.045, 0.56), 0.028))
    lick = G.union(G.round_cone((0.205, 0, 0.615), (0.188, 0.0, 0.66), 0.024, 0.006),
                   G.round_cone((0.185, 0, 0.61), (0.158, 0.0, 0.645), 0.022, 0.005))
    head = G.blend(cran, (muz, 0.045), (cheek, 0.03), (chin, 0.025), (hneck, 0.05), (brow, 0.025), (lick, 0.022))

    ground = G.plane((0, 0, 0.0), (0, 0, -1))

    def leg_front(y):
        upper = G.round_cone((0.11, y, 0.29), (0.118, y, 0.075), 0.054, 0.04)
        paw = G.ellipsoid((0.137, y, 0.034), (0.056, 0.044, 0.036))
        return G.blend(upper, (paw, 0.03), (ground, 0.006, 'int'))

    def leg_hind(y):
        thigh = G.round_cone((-0.125, y, 0.30), (-0.088, y, 0.182), 0.054, 0.047)
        shin = G.round_cone((-0.088, y, 0.182), (-0.152, y, 0.088), 0.047, 0.036)
        foot = G.round_cone((-0.152, y, 0.088), (-0.13, y, 0.04), 0.036, 0.034)
        paw = G.ellipsoid((-0.112, y, 0.034), (0.055, 0.044, 0.036))
        return G.blend(thigh, (shin, 0.025), (foot, 0.02), (paw, 0.03), (ground, 0.006, 'int'))

    tail_pts = [(-0.19, 0, 0.36), (-0.255, 0, 0.405), (-0.29, 0, 0.47), (-0.285, 0, 0.535), (-0.262, 0, 0.568)]
    tail = G.tube(tail_pts, [0.032, 0.042, 0.043, 0.036, 0.02], n=16)

    def ear_field(s):
        root = G.ellipsoid((0.19, s * 0.092, 0.598), (0.036, 0.03, 0.016), G.rot((1, 0, 0), math.radians(-30 * s)))
        flap = G.ellipsoid((0.198, s * 0.128, 0.53), (0.045, 0.0125, 0.068), G.rot((1, 0, 0), math.radians(12 * s)))
        return G.blend(root, (flap, 0.018))

    LY = 0.064
    legs = {'LegFL': (leg_front(LY), (0.11, LY, 0.28)), 'LegFR': (leg_front(-LY), (0.11, -LY, 0.28)),
            'LegBL': (leg_hind(LY), (-0.125, LY, 0.29)), 'LegBR': (leg_hind(-LY), (-0.125, -LY, 0.29))}
    ears = {'EarL': (ear_field(1), (0.19, 0.088, 0.598)), 'EarR': (ear_field(-1), (0.19, -0.088, 0.598))}
    everything = G.union(body, head, tail, *[f for f, _ in legs.values()], *[f for f, _ in ears.values()])

    # ---------------- markings (positive inside)
    cream_chest = K.neg(G.ellipsoid((0.17, 0, 0.30), (0.085, 0.072, 0.125)))
    cream_belly = K.neg(G.ellipsoid((-0.01, 0, 0.17), (0.17, 0.072, 0.06)))
    cream_muzzle = K.neg(G.ellipsoid((0.338, 0, 0.452), (0.092, 0.076, 0.044)))
    BROW = G.project(head, np.array([(0.296, 0.05, 0.594)]))[0]       # cream brow dots above the eyes
    brows = G.mirror_y(lambda P: 0.0115 - np.linalg.norm((P - BROW) * np.array((1.0, 1.0, 1.35)), axis=1))
    socks = lambda P: 0.075 - P[:, 2] + 0.006 * np.sin(P[:, 0] * 90)
    tail_tip = lambda P: 0.05 - np.linalg.norm(P - np.array((-0.262, 0, 0.568)), axis=1)

    face_uv = A.side_uv(A.DOG_FACE, 'dog_face')       # the smile is painted in the atlas

    fur = lambda z0, z1, **kw: K.painter(DOG['fur'], 1, z0, z1, **kw)
    cream = lambda z0, z1, **kw: K.painter(DOG['cream'], 1, z0, z1, **kw)

    # ---------------- Body
    sb = G.Surface(body, (-0.28, -0.16, 0.12), (0.27, 0.16, 0.5), 0.004, 390, sym=True)
    body_p = sb.pieces([('chest', K.either(cream_chest, cream_belly))],
                       {'base': fur(0.17, 0.42), 'chest': cream(0.17, 0.42)}, ao_field=everything, ao_scale=0.035)
    # collar: a flat band hugging the neck, with a little tag
    a0, a1 = np.array((0.09, 0, 0.33)), np.array((0.155, 0, 0.42))
    axis = G.unit(a1 - a0)
    ctr = a0 + (a1 - a0) * 0.6
    M = G.frame(axis, (1, 0, 0))
    neck_both = G.union(body, head)
    loop = []
    for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
        d = M @ np.array((math.cos(a), math.sin(a), 0.0))
        p, n = G.surface_point(neck_both, ctr + d * 0.2, -d)
        loop.append(p + n * 0.003)
    loop = np.array(loop)
    rings = []
    for i in range(len(loop)):
        p = loop[i]
        out = G.unit(p - ctr - axis * np.dot(p - ctr, axis))
        sec = [(-0.004, -0.015), (0.010, -0.011), (0.010, 0.011), (-0.004, 0.015)]
        rings.append([p + out * a_ + axis * b_ for a_, b_ in sec])
    collar = _closed_band(rings)
    K.shade_piece(collar, DOG['collar'], 2, 0.3, 0.46, dark=0.8, light=1.08)
    bottom = loop[np.argmin(loop[:, 2] - loop[:, 0] * 0.8)]
    tag = G.lathe([(0, -0.0035), (0.019, -0.0035), (0.0205, 0.0), (0.019, 0.0035), (0, 0.0035)], 8,
                  R=G.frame((0, -1, 0)), t=bottom + np.array((0.006, 0, -0.024)))
    K.shade_piece(tag, DOG['tag'], 0, 0.3, 0.4, dark=0.85, light=1.1)
    body_pieces = body_p + [collar, tag]

    # ---------------- Head
    sh = G.Surface(head, (0.02, -0.14, 0.26), (0.41, 0.14, 0.65), 0.003, 390, sym=True,
                   weight=lambda P: G.smoothstep(0.25, 0.36, P[:, 0]))
    head_p = sh.pieces([('muzzle', K.either(cream_muzzle, brows))],
                       {'base': fur(0.42, 0.62, uv=face_uv), 'muzzle': cream(0.42, 0.62, uv=face_uv)},
                       ao_field=everything, ao_scale=0.03)
    eyes = []
    for s in (1, -1):
        e, _, _ = K.eye(head, HC, (0.32, s * 0.08, 0.556), 0.0195, n=8, rings=2)
        eyes.append(e)
    tip, tn = G.surface_point(head, (0.6, 0, 0.496), (-1, 0, 0))
    nose = G.bead(tip - np.array((0.011, 0, 0.0)), G.unit(np.array((1, 0, 0.35))), 0.03, 0.75, n=10, rings=2,
                  uvreg=A.inset('nose'), squash=0.72)
    nose.color(np.ones(3)).part(0)
    head_pieces = head_p + eyes + [nose]

    # ---------------- ears (floppy, hinged at the top of the head)
    ear_parts = []
    for name, (f, piv) in ears.items():
        lo = np.array(piv) + np.array((-0.07, -0.08, -0.16)); hi = np.array(piv) + np.array((0.07, 0.08, 0.04))
        se = G.Surface(f, lo, hi, 0.002, 76, sym=False)
        pcs = se.pieces([], {'base': K.painter(DOG['ear'], 1, 0.46, 0.62, dark=0.72, light=1.05)},
                        ao_field=everything, ao_scale=0.02)
        ear_parts.append(K.Part(name, piv, pcs, parent='Head', motion='flop: rotate about X (out from the head), 0..30 deg'))

    # ---------------- legs and tail
    leg_parts = []
    for name, (f, piv) in legs.items():
        lo = np.array(piv) + np.array((-0.11, -0.09, -0.30)); hi = np.array(piv) + np.array((0.11, 0.09, 0.08))
        lo[2] = -0.01
        sl = G.Surface(f, lo, hi, 0.003, 74, sym=False)
        pcs = sl.pieces([('sock', socks)], {'base': fur(0.0, 0.3, nz_w=0.35), 'sock': cream(0.0, 0.3, nz_w=0.35)},
                        ao_field=everything, ao_scale=0.03)
        leg_parts.append(K.Part(name, piv, pcs, motion='swing about Y (fore-aft), +-30 deg'))
    st = G.Surface(tail, (-0.36, -0.07, 0.3), (-0.15, 0.07, 0.63), 0.0028, 110, sym=True)
    tail_p = st.pieces([('tip', tail_tip)], {'base': fur(0.36, 0.56), 'tip': cream(0.36, 0.56)},
                       ao_field=everything, ao_scale=0.02)

    parts = [K.Part('Body', (0, 0, 0), body_pieces),
             K.Part('Head', (0.145, 0, 0.415), head_pieces, motion='nod about Y, turn about Z'),
             K.Part('Tail', (-0.2, 0, 0.372), tail_p, motion='wag about Z, lift about Y')]
    parts += leg_parts + ear_parts
    model = K.Model('Dog', parts, {1: DOG['fur'], 2: DOG['collar']}, 2000,
                    extra={'origin': 'on the ground', 'head': '+X'}, attach={'Nose': (tip + np.array((0.012, 0, 0)), 'Head')})
    return _scaled(model, S)


def _closed_band(rings):
    """A closed loop of rings (each ring an open polyline section) -> a band mesh with end caps
    folded in (the section is closed by its first and last points)."""
    rings = [np.asarray(r, float) for r in rings]
    m = len(rings[0]); n = len(rings)
    V = np.concatenate(rings); T = []
    for i in range(n):
        j = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            a, b, c, d = i * m + k, i * m + k2, j * m + k2, j * m + k
            T += [(a, b, c), (a, c, d)]
    p = G.Piece(V, np.array(T))
    # orient outward from the loop's centre line
    ctr = V.mean(axis=0)
    fn = np.cross(V[p.T[:, 1]] - V[p.T[:, 0]], V[p.T[:, 2]] - V[p.T[:, 0]])
    cen = V[p.T].mean(axis=1)
    loopc = np.repeat(np.array([r.mean(axis=0) for r in rings]), m, axis=0)
    out = V[p.T[:, 0]] - loopc[p.T[:, 0]]
    if np.einsum('ij,ij->i', fn, out).sum() < 0:
        p.T = p.T[:, ::-1]
    p.N = G.vnormals(p.V, p.T)
    return p


# ================================================================ cat (sitting, for a garden wall)
CAT = {
    'fur': hexc('#e08a4c'),        # ginger (part 1)
    'cream': hexc('#f7e7cd'),      # chest, muzzle, paws
    'ear': hexc('#efa59f'),        # inner ears
    'nose': hexc('#e5878a'),
    'collar': hexc('#4c84c6'),     # part 2
    'bell': hexc('#f2c24e'),
}


def _local(f, center, R):
    """Field f designed around the origin, placed at center with rotation R."""
    c = np.asarray(center, float)
    return lambda P: f((P - c) @ R)


def build_cat():
    ground = G.plane((0, 0, 0.0), (0, 0, -1))
    hips = G.ellipsoid((-0.045, 0, 0.088), (0.105, 0.082, 0.088))
    torso = G.ellipsoid((0.0, 0, 0.165), (0.07, 0.066, 0.115), G.rot((0, 1, 0), math.radians(15)))
    chest = G.ellipsoid((0.04, 0, 0.17), (0.05, 0.06, 0.075))
    haunch = G.mirror_y(G.ellipsoid((-0.04, 0.045, 0.085), (0.08, 0.05, 0.075)))
    fleg = G.mirror_y(G.round_cone((0.045, 0.03, 0.17), (0.068, 0.033, 0.03), 0.026, 0.02))
    fpaw = G.mirror_y(G.ellipsoid((0.078, 0.034, 0.016), (0.03, 0.022, 0.017)))
    hfoot = G.mirror_y(G.ellipsoid((0.012, 0.062, 0.016), (0.05, 0.024, 0.017)))
    neck = G.round_cone((0.02, 0, 0.23), (0.045, 0, 0.29), 0.05, 0.045)
    body = G.blend(hips, (torso, 0.06), (chest, 0.04), (haunch, 0.03), (fleg, 0.02), (fpaw, 0.015), (hfoot, 0.02),
                   (neck, 0.04), (ground, 0.006, 'int'))

    # the head, designed facing +X about its centre, then turned toward the camera
    cran = G.ellipsoid((0, 0, 0), (0.068, 0.074, 0.062))
    cheeks = G.mirror_y(G.ellipsoid((0.016, 0.04, -0.02), (0.045, 0.042, 0.04)))
    pads = G.mirror_y(G.sphere((0.058, 0.0135, -0.023), 0.0165))
    chin = G.ellipsoid((0.05, 0, -0.04), (0.02, 0.017, 0.012))
    bridge = G.ellipsoid((0.054, 0, -0.004), (0.02, 0.016, 0.016))
    ear_pts = [(0.0, 0.04, 0.035), (-0.004, 0.054, 0.104)]
    ear_n = G.unit(np.array((1.0, 0.35, 0.25)))
    ear = G.mirror_y(G.flat_tube(ear_pts, [0.03, 0.004], 0.42, ear_n))
    ear_in = G.mirror_y(G.flat_tube([np.array(p) + ear_n * 0.007 + np.array((0, 0, -0.004)) for p in ear_pts], [0.019, 0.002], 0.4, ear_n))
    head_l = G.blend(cran, (cheeks, 0.025), (pads, 0.012), (chin, 0.012), (bridge, 0.02), (ear, 0.012))
    HC = np.array((0.058, 0, 0.318))
    HR = G.rot((0, 0, 1), math.radians(-28)) @ G.rot((0, 1, 0), math.radians(-6))
    head = _local(head_l, HC, HR)
    whole = G.blend(body, (head, 0.03))

    tail_pts = [(-0.118, 0, 0.03), (-0.172, 0, 0.042), (-0.212, 0, 0.09), (-0.224, 0, 0.16), (-0.205, 0, 0.215), (-0.168, 0, 0.236)]
    tail = G.tube(tail_pts, [0.022, 0.021, 0.02, 0.019, 0.018, 0.0145], n=16)
    everything = G.union(whole, tail)

    # markings
    chest_m = K.neg(G.ellipsoid((0.06, 0, 0.17), (0.05, 0.05, 0.1)))
    paws_m = lambda P: 0.03 - P[:, 2] + 0.08 * np.maximum(P[:, 0] - 0.04, 0)
    muzzle_m = _local(K.neg(G.ellipsoid((0.05, 0, -0.03), (0.035, 0.04, 0.026))), HC, HR)
    inner_m = _local(lambda P: -ear_in(P) + 0.0025, HC, HR)
    collar_ctr = np.array((0.032, 0, 0.255)); collar_ax = G.unit(np.array((0.025, 0, 0.06)))
    face_uv = A.head_uv(A.CAT_FACE, 'cat_face', HC, HR)
    side_uv = A.side_uv(A.CAT_SIDE, 'cat_side')
    fur = lambda z0, z1, uv=None, **kw: K.painter(CAT['fur'], 1, z0, z1, uv=uv, **kw)
    cream = lambda z0, z1, uv=None, **kw: K.painter(CAT['cream'], 1, z0, z1, uv=uv, **kw)

    # the face decal and the flank decal meet where the neck joins the head: a cut there keeps
    # every triangle on one mapping (each region below picks its own)
    neck_cut = lambda P: (P - HC) @ HR[:, 2] + 0.045
    sb = G.Surface(whole, (-0.17, -0.12, -0.01), (0.15, 0.12, 0.43), 0.0028, 640, sym=False,
                   weight=lambda P: G.smoothstep(0.22, 0.3, P[:, 2]))
    body_p = sb.pieces([('inner', inner_m), ('muzzle', muzzle_m), ('chest', K.either(chest_m, paws_m)),
                        ('headfur', neck_cut)],
                       {'base': fur(0.04, 0.38, uv=side_uv), 'headfur': fur(0.04, 0.38, uv=face_uv),
                        'chest': cream(0.04, 0.38, uv=side_uv), 'muzzle': cream(0.04, 0.38, uv=face_uv),
                        'inner': K.painter(CAT['ear'], 0, 0.3, 0.42, dark=0.85, light=1.02, uv=face_uv)},
                       ao_field=everything, ao_scale=0.025)
    # eyes, nose
    eyes = []
    for s in (1, -1):
        e, _, _ = K.eye(head, HC, HC + HR @ np.array((0.07, s * 0.036, 0.012)), 0.0165, kind='eye_cat', n=8, rings=2, squash=0.82)
        eyes.append(e)
    tipn, nn = G.surface_point(head, HC + HR @ np.array((0.2, 0, -0.006)), HR @ np.array((-1, 0, 0)))
    nose = G.bead(tipn - nn * 0.002, nn, 0.0085, 0.6, n=6, rings=1, squash=0.7)
    K.shade_piece(nose, CAT['nose'], 0, 0.3, 0.33, dark=0.9, light=1.05)
    # collar with a bell
    loop = []
    M = G.frame(collar_ax, (1, 0, 0))
    for a in np.linspace(0, 2 * math.pi, 14, endpoint=False):
        d = M @ np.array((math.cos(a), math.sin(a), 0.0))
        p, n = G.surface_point(whole, collar_ctr + d * 0.15, -d)
        loop.append(p + n * 0.002)
    loop = np.array(loop)
    rings = []
    for p in loop:
        out = G.unit(p - collar_ctr - collar_ax * np.dot(p - collar_ctr, collar_ax))
        rings.append([p + out * a_ + collar_ax * b_ for a_, b_ in [(-0.003, -0.009), (0.006, -0.007), (0.006, 0.007), (-0.003, 0.009)]])
    collar = _closed_band(rings)
    K.shade_piece(collar, CAT['collar'], 2, 0.2, 0.3, dark=0.82, light=1.08)
    front = loop[np.argmax(loop[:, 0] - 0.5 * loop[:, 2])]
    bell = G.lathe([(0, -0.011), (0.007, -0.0105), (0.0105, -0.004), (0.0105, 0.004), (0.006, 0.009), (0, 0.0105)], 8,
                   t=front + np.array((0.007, -0.002, -0.009)))
    K.shade_piece(bell, CAT['bell'], 0, 0.21, 0.24, dark=0.8, light=1.15)

    # tail with rings
    tdense = G.catmull(tail_pts, 40)
    tlen = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(tdense, axis=0), axis=1))])

    def t_of(V):
        d = np.linalg.norm(V[:, None, :] - tdense[None], axis=2)
        return tlen[np.argmin(d, axis=1)] / tlen[-1]
    st = G.Surface(tail, (-0.27, -0.05, -0.01), (-0.09, 0.05, 0.28), 0.0022, 170, sym=True)
    tail_p = st.pieces([], {'base': fur(0.02, 0.26, uv=A.ring_uv(t_of))}, ao_field=everything, ao_scale=0.02)

    parts = [K.Part('Body', (0, 0, 0), body_p + eyes + [nose, collar, bell]),
             K.Part('Tail', (-0.12, 0, 0.032), tail_p, motion='swish about Y (in the camera plane), -15..+20 deg; flick about Z')]
    return K.Model('Cat', parts, {1: CAT['fur'], 2: CAT['collar']}, 1500,
                   extra={'origin': 'on the ground (the wall top)', 'head': '+X (turned 28 deg toward the camera)'})


# ================================================================ squirrel (park)
SQUIRREL = {
    'fur': hexc('#c86a34'),        # rust (part 1)
    'cream': hexc('#f5e5cd'),
    'tuft': hexc('#874322'),
    'nose': hexc('#3a2a26'),
}


def build_squirrel():
    ground = G.plane((0, 0, 0.0), (0, 0, -1))
    body0 = G.ellipsoid((-0.008, 0, 0.078), (0.08, 0.05, 0.057), G.rot((0, 1, 0), math.radians(-22)))
    chest = G.ellipsoid((0.042, 0, 0.098), (0.042, 0.042, 0.05))
    haunch = G.mirror_y(G.ellipsoid((-0.045, 0.026, 0.066), (0.052, 0.03, 0.052)))
    neck = G.round_cone((0.04, 0, 0.1), (0.08, 0, 0.135), 0.036, 0.032)
    HC = np.array((0.088, 0, 0.142))
    head = G.ellipsoid(HC, (0.043, 0.037, 0.038))
    snout = G.ellipsoid((0.121, 0, 0.133), (0.025, 0.021, 0.019))
    cheek = G.mirror_y(G.ellipsoid((0.102, 0.022, 0.13), (0.026, 0.02, 0.02)))
    ear_n = G.unit(np.array((1.0, 0.3, 0.0)))
    ear = G.mirror_y(G.flat_tube([(0.074, 0.021, 0.168), (0.068, 0.026, 0.199)], [0.011, 0.004], 0.5, ear_n))
    tuftf = G.mirror_y(G.round_cone((0.068, 0.026, 0.194), (0.062, 0.028, 0.219), 0.0055, 0.0015))
    fleg = G.mirror_y(G.round_cone((0.05, 0.021, 0.085), (0.068, 0.021, 0.014), 0.0135, 0.0095))
    fpaw = G.mirror_y(G.ellipsoid((0.073, 0.021, 0.008), (0.013, 0.01, 0.008)))
    hfoot = G.mirror_y(G.ellipsoid((-0.018, 0.038, 0.011), (0.046, 0.015, 0.011)))
    body = G.blend(body0, (chest, 0.03), (haunch, 0.025), (neck, 0.03), (head, 0.025), (snout, 0.015),
                   (cheek, 0.012), (ear, 0.008), (tuftf, 0.004), (fleg, 0.012), (fpaw, 0.008), (hfoot, 0.015),
                   (ground, 0.004, 'int'))
    tail_pts = [(-0.068, 0, 0.066), (-0.122, 0, 0.088), (-0.15, 0, 0.155), (-0.135, 0, 0.228), (-0.088, 0, 0.268), (-0.04, 0, 0.258)]
    tail0 = G.tube(tail_pts, [0.016, 0.034, 0.047, 0.05, 0.043, 0.022], n=18)
    tdense = G.catmull(tail_pts, 40)
    # tufts: a soft wavy fringe along the tail's silhouette
    tail = G.displaced(tail0, lambda P: 0.0045 * np.sin(P[:, 0] * 95 + P[:, 2] * 60) * np.sin(P[:, 2] * 70 - P[:, 0] * 30))
    everything = G.union(body, tail)

    belly = K.neg(G.ellipsoid((0.05, 0, 0.075), (0.05, 0.035, 0.07), G.rot((0, 1, 0), math.radians(-25))))
    under = K.neg(G.ellipsoid((-0.01, 0, 0.03), (0.07, 0.03, 0.03)))
    chin = K.neg(G.ellipsoid((0.112, 0, 0.115), (0.03, 0.03, 0.022)))
    tuft_m = lambda P: P[:, 2] - 0.2
    sb = G.Surface(body, (-0.12, -0.08, -0.01), (0.16, 0.08, 0.24), 0.0018, 720, sym=True,
                   weight=lambda P: G.smoothstep(0.06, 0.1, P[:, 0]) * G.smoothstep(0.1, 0.13, P[:, 2]))
    fur = K.painter(SQUIRREL['fur'], 1, 0.02, 0.17, dark=0.74, light=1.1)
    cream = K.painter(SQUIRREL['cream'], 1, 0.02, 0.17, dark=0.8, light=1.04)
    body_p = sb.pieces([('tuft', tuft_m), ('belly', K.either(belly, under, chin))],
                       {'base': fur, 'belly': cream,
                        'tuft': K.painter(SQUIRREL['tuft'], 0, 0.19, 0.22, dark=0.9, light=1.1)},
                       ao_field=everything, ao_scale=0.018)
    for s in (1, -1):
        e, _, _ = K.eye(body, HC, (0.12, s * 0.036, 0.157), 0.0098, n=8, rings=2)
        body_p.append(e)
    tipn, nn = G.surface_point(body, (0.3, 0, 0.137), (-1, 0, 0))
    nose = G.bead(tipn - nn * 0.002, nn, 0.0065, 0.7, n=6, rings=1, squash=0.8)
    K.shade_piece(nose, SQUIRREL['nose'], 0, 0.13, 0.15, dark=0.9, light=1.2)
    st = G.Surface(tail, (-0.22, -0.075, 0.0), (0.0, 0.075, 0.34), 0.0024, 350, sym=True)

    def tail_paint(V, N, Aocc):
        k = K.soft_shade(V, N, Aocc, 0.06, 0.3, dark=0.78, light=1.12)
        # the fringe a little paler than the core
        q = np.min(np.linalg.norm(V[:, None, :] - tdense[None], axis=2), axis=1)
        return G.shade_srgb(SQUIRREL['fur'], k * (0.96 + 0.1 * G.smoothstep(0.03, 0.05, q))), 1
    tail_p = st.pieces([], {'base': tail_paint}, ao_field=everything, ao_scale=0.02)
    parts = [K.Part('Body', (0, 0, 0), body_p + [nose]),
             K.Part('Tail', (-0.07, 0, 0.068), tail_p, motion='flick about Y, -15..+25 deg (up/back)')]
    return K.Model('Squirrel', parts, {1: SQUIRREL['fur']}, 1500, extra={'origin': 'on the ground', 'head': '+X'})
