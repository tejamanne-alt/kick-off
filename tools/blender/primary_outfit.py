# The primary-school kids' uniform (see primary_spec.py): a short-sleeved polo (boys) or blouse (girls),
# shorts that end above the knee (boys), a pleated skirt or a pinafore (girls), white socks, shoes, a hard rectangular
# school backpack (a randoseru) on the Bag bone, and a small neckerchief or bow at the collar (outfit
# part 4: separate shells, so a game mode can make it vanish by collapsing its vertices).
#
# Built like the teens' clothes (teen_outfit): offset surfaces of the body field, mapped from final to
# base space with ungrow, skin weights shared with the skin underneath (teen_outfit.leg_skin_weights),
# and the teens' binders, skirt and collars with this kid's measures.
import math
import numpy as np
import bpy
from mathutils import Vector
from teen_lib import Part, activate, apply_mods, smooth, shade
import teen_body as TB
from teen_body import smin, smax, round_cone, ellipsoid, rbox, frame, catmull, chain, grad, field, tj, grow, ungrow, mesh_object
import teen_outfit as TO
from teen_outfit import (unit, sstep, tris_of, ring_on, ring_even, outward, ellipse_profile, rrect_profile, tube,
                         solid, lin, ksc, _weights, _set_weights, _transfer, _attach, smooth_knees, leg_skin_weights, LEG_BONES)

WHITE = (0.97, 0.97, 0.96, 1)
SOCK = (0.94, 0.94, 0.96, 1)           # off-white, so the cel shadow still reads on the socks
GOLD = (0.83, 0.62, 0.27, 1)


class Fields:
    pass


def palette(V):
    return {'skin': tuple(V.skin_lin) + (1,), 'top': lin(V.top) + (1,), 'legwear': lin(V.legwear) + (1,), 'accent': lin(V.accent) + (1,)}


# ----------------------------------------------------------------------------------------------
# The backpack's box, in final space: centre, half sizes, corner radius
def _bag_dims(V):
    N1 = field(V).P['N1']
    return np.array([0.0, 0.166, N1 - 0.300]), np.array([0.128, 0.066, 0.170]), 0.030


def bag_bone(V):
    """The Bag bone (base space): head at the top edge of the bag, tail toward its bottom."""
    c, h, r = _bag_dims(V)
    top = c + (0, 0, h[2]); bot = c - (0, 0, h[2] * 0.6)
    return tuple(ungrow(Vector(top), V)), tuple(ungrow(Vector(bot), V))


# ----------------------------------------------------------------------------------------------
# The clothes' fields (final space)
def fields(V):
    BF = field(V); j = BF.j; P = BF.P; girl = bool(V.girl)
    F = Fields(); F.BF = BF; F.V = V
    N1 = P['N1']; hip = P['hip']
    n0 = j['neck0']
    kn_z = j['kneeL'][2]
    zf, zb = N1 - 0.064, N1 - 0.050                 # neckline height at the front (y -0.05) and back (y +0.06): on the slope of the shoulders
    F.zn = lambda y: zf + (zb - zf) * (y + 0.05) / 0.11
    F.nax = np.array([0, n0[1] + 0.003, 0])
    torso, neck = BF.torso, BF.neck
    shz = j['shoulderL'][2]

    # --- sleeves: short and loose, a little puffed for the girls
    def sleeve(n, s):
        sh, el = j['shoulder' + n], j['elbow' + n]
        adir = unit(el - sh)
        ru = BF.r['uarm'][0]
        if girl:
            puff = ellipsoid(sh + adir * 0.046 + (s * 0.005, 0, 0.004), (0.046, 0.048, 0.068), frame(adir))
            end = sh + adir * 0.118
            def raw(p): return smin(BF.uarm[n](p) - 0.0075, puff(p), 0.03)
        else:
            end = sh + adir * 0.125
            out = np.array([s * 0.010, 0, 0])
            cone = round_cone(sh + adir * 0.035 + out, end + adir * 0.008 + out, ru + 0.009, ru + 0.015)
            def raw(p): return smin(BF.uarm[n](p) - 0.007, cone(p), 0.016)
        def f(p): return smax(raw(p), (p - end) @ adir, 0.003)
        f.raw = raw; f.end = end; f.dir = adir
        return f
    F.sleeves = [sleeve('L', 1), sleeve('R', -1)]

    # --- the top, tucked in under the waistband (shorts), the skirt, or the pinafore's seam
    pina = V.garment == 'pinafore'
    F.seam = N1 - 0.40                         # the pinafore's waist seam (just under the ribs)
    F.waist = F.seam if pina else hip + 0.125  # the top of the shorts' waistband / the skirt's waist
    def top_raw(p, neck_off=0.003):
        z = p[:, 2]; rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
        off = 0.0125 + 0.004 * sstep(N1 - 0.22, N1 - 0.42, z) - 0.005 * sstep(0.10, 0.07, rho) * sstep(N1 - 0.09, N1 - 0.045, z)
        tuck = sstep(F.waist + 0.02, F.waist - 0.012, z)
        off = off + (0.0035 - off) * tuck
        d = smin(torso(p) - off, neck(p) - neck_off, 0.02)
        w = sstep(shz - 0.05, shz - 0.008, z)
        ka = 0.004 + 0.014 * sstep(shz - 0.10, shz - 0.05, z)
        for f in F.sleeves:
            fp = f(p)
            d = smin(d, fp, ka) + (smin(d, fp, 0.045) - smin(d, fp, ka)) * w
        return d
    F.hem = F.waist - 0.045                    # the hem hides inside the shorts / skirt
    # the neck opening: a wide ellipse on the shoulder slope, under a flat collar that lies round it
    F.hole = (0.092, 0.073)
    F.hole_drop = 0.010
    def top(p):
        d = smax(top_raw(p), F.hem - p[:, 2], 0.004)
        rho = np.hypot(p[:, 0] / F.hole[0], (p[:, 1] - F.nax[1]) / F.hole[1])
        hole = np.maximum((rho - 1) * 0.07, F.zn(p[:, 1]) - F.hole_drop - p[:, 2])
        return smax(d, -hole, 0.004)
    F.top_raw, F.top = top_raw, top

    # --- what the kid wears below: shorts, a pleated skirt, or a pinafore
    F.skirt_k = None
    if V.garment == 'shorts':
        F.shorts_hem = kn_z + 0.085
        def leg_tube(n):
            hp, kn = j['hip' + n], j['knee' + n]
            s_ = 1 if n == 'L' else -1
            # (the legs' axes flare outward a little: a loose A-line short, and the two hems never touch)
            a = hp + (s_ * 0.004, 0.003, 0.03)
            m = hp + (kn - hp) * 0.55 + (s_ * 0.011, 0.002, 0)
            e = hp + (kn - hp) * 0.86 + (s_ * 0.020, 0.001, 0)
            axis = chain([a, m, e], (0.086, 0.078, 0.072), 0.0)
            th = BF.thigh[n]
            return lambda p: smin(axis(p), th(p) - 0.010, 0.025)
        tubes = [leg_tube('L'), leg_tube('R')]
        def shorts_raw(p):
            z = p[:, 2]
            a, b = tubes[0](p), tubes[1](p)
            # the legs meet in a proper crotch seam (no skin between them)
            legs = smin(a, b, 0.008) + (smin(a, b, 0.040) - smin(a, b, 0.008)) * sstep(hip - 0.075, hip - 0.01, z)
            return smin(torso(p) - 0.012, legs, 0.03)
        def shorts(p):
            d = smax(shorts_raw(p), p[:, 2] - F.waist, 0.006)
            return smax(d, F.shorts_hem - p[:, 2], 0.003)
        F.lower = shorts
    else:
        # a skirt: the pleated loft of teen_outfit._skirt with this kid's measures
        top_z = F.seam if pina else F.waist
        F.skirt_top = top_z
        hem = kn_z + (0.09 if pina else 0.075)
        band = 0.022 if pina else 0.03
        span = top_z - band - hem
        F.skirt_k = dict(NP=5 if pina else 6, zw_top=top_z, zw_bot=top_z - band, z_hem=hem, zhip=hip + 0.085, loft_bottom=hip - 0.04,
                         rings=[top_z - band - span * t for t in (0.07, 0.17, 0.29, 0.42, 0.56, 0.72, 0.87)],
                         open=(hip + 0.15, hip + 0.055), open_amt=0.014, band_ease=0.020, ease=0.010, flare=9.0 if not pina else 8.0,
                         thick=0.0045, bind=(hip + 0.095, hip - 0.057))
        a_z, b_z = hip - 0.045, top_z
        BFa = BF
        def skirt_zone(p):          # inside the skirt round the hips, never the arms
            z = p[:, 2]
            arm = np.minimum(BFa.arm_full('L')(p), BFa.arm_full('R')(p))
            return np.minimum(np.minimum(z - a_z, b_z - z), arm - 0.01)
        F.skirt_zone = skirt_zone
        F.skirt_hem = hem
        if pina:
            F.bib = N1 - 0.20
            F.vest_off = 0.0185                                            # a hair proud of the blouse
            def vest(p):
                z = p[:, 2]
                d = torso(p) - F.vest_off
                d = smax(d, z - F.bib, 0.005)                             # the bib's top edge, front and back
                d = smax(d, F.seam - 0.03 - z, 0.004)                   # (the bottom hides inside the skirt's waistband)
                return smax(d, np.abs(p[:, 0]) - 0.092, 0.006)           # its sides stop short of the arms
            F.vest = vest
            F.vest_surface = lambda p: smin(torso(p) - F.vest_off, neck(p) - F.vest_off, 0.03)
            def lower_zone(p): return np.maximum(skirt_zone(p), -vest(p))
            F.lower = lower_zone
        else:
            F.lower = skirt_zone

    # --- socks
    F.sock_top = 0.085 + (kn_z - 0.085) * (0.90 if V.sock_high else 0.30 if getattr(V, 'ankle_socks', False) else 0.66)
    def sock(n):
        sn = BF.shin[n]; t = F.sock_top
        cuff = 0.024
        def f(p):
            z = p[:, 2]
            d = sn(p) - 0.0035 - 0.0030 * sstep(t - cuff - 0.004, t - cuff, z)      # a fold-over ribbed cuff at the top
            d = smax(d, z - t, 0.0045)
            return smax(d, 0.038 - z, 0.003)
        return f
    F.socks = {'L': sock('L'), 'R': sock('R')}

    # --- shoes (uppers), in each foot's frame
    F.shoes = {}
    for n, s in (('L', 1), ('R', -1)):
        an = j['ankle' + n]
        yaw = math.radians(5) * s
        Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
        o = np.array([an[0] + s * 0.002, 0.0, 0.0])
        parts = (ellipsoid((0, 0.030, 0.046), (0.038, 0.042, 0.042)), ellipsoid((0, -0.036, 0.042), (0.042, 0.072, 0.038)),
                 ellipsoid((0, -0.098, 0.034), (0.042, 0.054, 0.033)))
        zcut, zw = 0.013, 0.038
        def upper(p, Rz=Rz, o=o, parts=parts, zcut=zcut, zw=zw):
            q = (p - o) @ Rz
            body = lambda q: smin(smin(parts[0](q), parts[1](q), 0.025), parts[2](q), 0.025)
            d = body(q)
            qf = q.copy(); qf[:, 2] = zw
            d = smin(d, smax(body(qf), q[:, 2] - zw, 0.010), 0.007)
            return smax(d, zcut - q[:, 2], 0.003)
        upper.Rz = Rz; upper.o = o
        F.shoes[n] = upper
    return F


def cover(V):
    """For final-space points: how deep they lie inside clothes the player never sees through (> 0 inside), and
    whether they are covered only at rest (thighs in the skirt, legs in the socks), for thinning out the skin."""
    F = TO.fields(V); BF = F.BF
    hip = BF.P['hip']
    def f(p):
        z = p[:, 2]
        d = -F.top(p)
        for n in 'LR': d = np.maximum(d, -F.shoes[n](p) - 0.006)
        arm = np.minimum(BF.arm_full('L')(p), BF.arm_full('R')(p))
        if V.garment == 'shorts':
            d = np.maximum(d, np.minimum(-F.lower(p), arm - 0.012))     # (the hands hang beside the shorts: not what they cover)
            semi = np.zeros(len(p), bool)
        else:
            d = np.maximum(d, np.minimum(F.lower(p), 0.02))
            semi = (z > F.skirt_hem + 0.05) & (z < hip - 0.035) & (arm > 0.01)
        sockd = np.maximum(-F.socks['L'](p), -F.socks['R'](p))
        semi |= sockd > 0.002
        return d, semi & (d < 0.006), sockd
    return f


def skin_part(V, body):
    """The body's Part. Skin the clothes cover takes the colour (and the outfit part) of the garment over it, so
    where a bent limb or a lifted thigh makes it poke through the cloth it shows as more cloth, never as a sliver of
    bare skin. Only skin that is really bare (head, neck, arms, the legs below the hem) is skin."""
    F = TO.fields(V); pal = palette(V)
    me = body.data; mw = body.matrix_world
    C = [tuple(mw @ p.center) for p in me.polygons]
    P = TB.grow_np(np.array(C), V)
    shirt = -F.top(P)
    arm = np.minimum(F.BF.arm_full('L')(P), F.BF.arm_full('R')(P))
    lower = np.minimum(-F.lower(P), arm - 0.012) if V.garment == 'shorts' else F.lower(P)     # (the hands hang beside the shorts)
    sockd = np.maximum(-F.socks['L'](P), -F.socks['R'](P))
    m = -0.0015                      # (a hair outside the cloth counts: the skin is then more cloth, not a speck)
    cls = np.where(lower > m, 2, np.where(shirt > m, 1, np.where(sockd > 0.002, 5, 0)))
    table = {tuple(round(v, 5) for v in c): int(k) for c, k in zip(C, cls)}
    colours = {0: pal['skin'], 1: pal['top'], 2: pal['legwear'], 5: SOCK}
    def cls_of(cen): return table.get(tuple(round(v, 5) for v in cen), 0)
    def color(co, cen): return colours[cls_of(cen)]
    def part(co, cen): return {0: 0, 1: 1, 2: 2, 5: 0}[cls_of(cen)]
    print('skin faces: %d skin, %d under the shirt, %d under the legwear, %d under socks' %
          tuple(int((cls == k).sum()) for k in (0, 1, 2, 5)))
    return Part(body, color, part, 'body')


def refine_body_weights(body, V):
    """After the body's bone-heat weights: the wide knee blend, and the analytic leg weights (the cloth's own) on the
    skin under the shorts and, below the hips, on the whole leg, so the skin and the cloth over it move together and
    the long triangles of a thigh never crush into fins when it lifts."""
    smooth_knees(body, V)
    F = TO.fields(V)
    W = _weights(body)
    Vx = np.array([v.co for v in body.data.vertices])
    j = tj(V); hz = j['hipL'][2]
    armd = np.minimum(F.BF.arm_full('L')(Vx), F.BF.arm_full('R')(Vx))
    a = sstep(0.004, 0.02, armd) * (1 - sstep(hz - 0.10, hz + 0.03, Vx[:, 2]))          # the legs, from the hips down
    if V.garment == 'shorts':
        a = np.maximum(a, sstep(0.0, 0.012, -F.lower(Vx)) * sstep(0.004, 0.02, armd))    # and whatever is inside the shorts
    A = leg_skin_weights(V, Vx)
    for i, w in enumerate(W):
        if a[i] <= 1e-4: continue
        for n in list(w): w[n] *= 1 - a[i]
        for k, n in enumerate(LEG_BONES):
            if A[i, k] > 1e-5: w[n] = w.get(n, 0) + a[i] * A[i, k]
        if len(w) > 4:                                           # (the game skins with at most 4 bones a vertex)
            keep = sorted(w.items(), key=lambda kv: -kv[1])[:4]
            w.clear(); w.update(keep)
    _set_weights(body, W)


def bind_shorts(body, V):
    """Analytic weights (leg_skin_weights): the waistband follows the hips, the legs' pull ramps in round the hip joints,
    and the thigh stays a thigh down to the hem; the skin under the shorts has the same weights."""
    def bind(o, rig):
        Vx = np.array([v.co for v in o.data.vertices])
        A = leg_skin_weights(V, Vx)
        W = [{n: float(a) for n, a in zip(LEG_BONES, row) if a > 1e-5} for row in A]
        _set_weights(o, W); _attach(o, rig)
    return bind


def bind_torso(body, V, with_bag=False):
    """Pieces that ride the ribcage (the backpack's straps, the pinafore's bodice): the body's weights, but the arms' share
    goes to the Chest, or the Spine lower down (a swinging arm never drags them along), and the legs' to the Hips; with
    with_bag the ends near the backpack go to the Bag bone."""
    c, h, r = _bag_dims(V)
    bag = rbox(c, h, r)
    j = tj(V); k = ksc(V)
    def bind(o, rig):
        _transfer(o, body)
        W = _weights(o)
        Vx = np.array([v.co for v in o.data.vertices])
        kk_ = (1 - sstep(0.0, 0.07, bag(Vx))) if with_bag else np.zeros(len(Vx))
        up = sstep(j['spine'][2] + 0.05 * k, j['chest'][2], Vx[:, 2])
        for w, kk, u in zip(W, kk_, up):
            arm = sum(w.pop(n) for n in list(w) if n.startswith(('UpperArm', 'LowerArm', 'Hand')))
            if arm:
                w['Chest'] = w.get('Chest', 0) + arm * u
                w['Spine'] = w.get('Spine', 0) + arm * (1 - u)
            leg = sum(w.pop(n) for n in list(w) if n.startswith(('UpperLeg', 'LowerLeg', 'Foot')))
            if leg: w['Hips'] = w.get('Hips', 0) + leg
            if with_bag:
                for n in list(w): w[n] *= (1 - kk)
                w['Bag'] = w.get('Bag', 0) + kk
        _set_weights(o, W); _attach(o, rig)
    return bind


# ----------------------------------------------------------------------------------------------
def build_outfit(V, body):
    F = TO.fields(V)
    parts = _clothes(F, body, V)
    parts += _socks(F, V)
    parts += _shoes(F, V)
    parts += _randoseru(F, body, V)
    tot = sum(tris_of(p.obj) for p in parts)
    print('outfit parts', ', '.join('%s %d' % (p.obj.name, tris_of(p.obj)) for p in parts))
    print('outfit tris', tot, 'body tris', tris_of(body), 'sum', tot + tris_of(body))
    return parts


def _clothes(F, body, V):
    BF = F.BF; j = BF.j
    pal = palette(V); top, leg = pal['top'], pal['legwear']
    girl = bool(V.girl)
    parts = []
    def edges(Vv):      # the neckline and the sleeve ends stay dense
        rho = np.hypot(Vv[:, 0], Vv[:, 1] - F.nax[1])
        ends = np.zeros(len(Vv), bool)
        for f in F.sleeves: ends |= np.abs((Vv - f.end) @ f.dir) < 0.016
        return ((rho < 0.12) & (Vv[:, 2] > j['neck0'][2] - 0.08)) | ends
    sh = solid('Shirt', F.top, (-0.26, -0.15, F.hem - 0.02), (0.26, 0.15, j['neck0'][2] + 0.09), 0.0055, 1050, V, dense=(edges, 560))
    def inside(p, n):
        return any(n @ f.dir > 0.6 and (p - f.end) @ f.dir > -0.006 for f in F.sleeves)
    parts.append(Part(sh, TO._two_tone(F.top, top, shade(top, 0.72), inside, V), 1, TO.bind_loose_shirt(body, V, keep=0.0 if girl else 0.5)))
    if getattr(V, 'tee', False):
        pass                                        # (a plain T-shirt: a round neck, no collar)
    elif girl:
        # a rounded collar: the skirt's colour (navy), or white over a pinafore
        pina = V.garment == 'pinafore'
        parts.append(Part(TO._shirt_collar(F, V, 0.95, 26, 'round', 0.0016), shade(top, 0.97) if pina else leg, 1 if pina else 2, TO.bind_loose_shirt(body, V, keep=0.0)))
    else:
        parts.append(Part(TO._shirt_collar(F, V, 0.8, 26, 'point', 0.0012), shade(top, 0.93), 1, TO.bind_loose_shirt(body, V)))
    for f, n in zip(F.sleeves, 'LR'):
        b = TO.band(f.raw, f.end - f.dir * 0.004, f.dir, 0.0048, 0.0065, V, 'Cuff' + n, 18, ref=(0, 0, 1), m=5)
        parts.append(Part(b, shade(top, 0.96), 1))
    if V.garment == 'shorts':
        # the shorts: rings back at the hips (decimation leaves long flat tubes there)
        tr = solid('Shorts', F.lower, (-0.21, -0.14, F.shorts_hem - 0.02), (0.21, 0.15, F.waist + 0.02), 0.0056, 1100, V,
                   refine=(TB.joint_zone(V, knee=0.05, hip_below=0.1, hip_above=0.1), 0.05))
        def hem_in(p, n): return n[2] < -0.93 and p[2] < F.shorts_hem + 0.03       # (only the flat underside: the rounded edge keeps the cloth's colour, so the hem has a clean line)
        band_c = shade(leg, 0.9)
        two = TO._two_tone(F.lower, leg, shade(leg, 0.6), hem_in, V)
        def shorts_col(co, cen):
            p = grow(cen, V)
            if p.z > F.waist - 0.028: return band_c          # the elastic waistband
            return two(co, cen)
        parts.append(Part(tr, shorts_col, 2, bind_shorts(body, V)))
    else:
        parts.append(TO._skirt(F, V, leg, F.skirt_k))
        if V.garment == 'pinafore':
            parts += _bodice(F, body, V, leg)
    parts += _accent(F, V, sh)
    return parts


def _bodice(F, body, V, leg):
    """The pinafore's bodice: a bib over the chest with two straps over the shoulders (the vest field's scoop and armholes
    leave them), in the skirt's colour, a shade darker below the seam (the brightest colour of a part is the one in the
    .json, shading only ever darkens it)."""
    j = F.BF.j; N1 = F.BF.P['N1']
    vest = F.vest
    def edges(Vv):
        return Vv[:, 2] > F.bib - 0.04
    bo = solid('Bodice', vest, (-0.20, -0.15, F.seam - 0.04), (0.20, 0.15, F.bib + 0.03), 0.0050, 560, V, dense=(edges, 260))
    top_c = tuple(leg)
    def col(co, cen):
        p = grow(cen, V)
        return shade(leg, 0.82) if p.z < F.seam - 0.004 else top_c
    parts = [Part(bo, col, 2, bind_torso(body, V))]
    # the straps: ribbons from the front bib's top over the shoulder to the back's, lying on the vest's surface
    surf = F.vest_surface
    for s in (1, -1):
        ctrl = [(0.062, -0.076, F.bib - 0.012), (0.067, -0.066, N1 - 0.120), (0.070, -0.044, N1 - 0.078), (0.073, -0.012, N1 - 0.060),
                (0.073, 0.020, N1 - 0.066), (0.070, 0.046, N1 - 0.102), (0.064, 0.062, F.bib - 0.012)]
        pts = catmull([(s * x, y, z) for x, y, z in ctrl], 30)
        thick, half_w = 0.0045, 0.0155
        for it in range(8):
            g = grad(surf, pts); g /= np.linalg.norm(g, axis=1)[:, None]
            pts = pts - g * (surf(pts) - (thick - 0.001))[:, None]
            sm = pts.copy(); sm[1:-1] = (pts[:-2] + pts[1:-1] * 2 + pts[2:]) / 4
            pts = sm
        g = grad(surf, pts); g /= np.linalg.norm(g, axis=1)[:, None]
        t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
        g = g - t * (g * t).sum(1)[:, None]; g /= np.linalg.norm(g, axis=1)[:, None]
        so = tube('PinaStrap' + ('L' if s > 0 else 'R'), pts, g, np.cross(g, t), rrect_profile(thick, half_w, 5), V, False)
        parts.append(Part(so, top_c, 2, bind_torso(body, V)))
    return parts


# ----------------------------------------------------------------------------------------------
# the accent: a neckerchief (boys) or a bow (girls), part 4, bound to the shirt it lies on
def _surface_points(f, X, Z, tmax=0.5, n=300):
    """Where rays along +y through (X, Z), from y = -0.3, first enter the solid f, and the outward normals there."""
    X = np.asarray(X, dtype=np.float64); Z = np.asarray(Z, dtype=np.float64)
    ts = np.linspace(0, tmax, n)
    P = np.zeros((len(X), n, 3)); P[:, :, 0] = X[:, None]; P[:, :, 1] = -0.3 + ts[None, :]; P[:, :, 2] = Z[:, None]
    Fv = f(P.reshape(-1, 3)).reshape(len(X), n)
    idx = np.argmax(Fv < 0, 1)
    lo = ts[np.maximum(idx - 1, 0)]; hi = ts[idx]
    for _ in range(26):
        m = (lo + hi) / 2
        inside = f(np.stack([X, -0.3 + m, Z], 1)) < 0
        hi = np.where(inside, m, hi); lo = np.where(inside, lo, m)
    pts = np.stack([X, -0.3 + hi, Z], 1)
    g = grad(f, pts); g /= np.linalg.norm(g, axis=1)[:, None]
    return pts, g


def _neckerchief(F, V, shirt):
    """A small triangular neckerchief: a band round the base of the neck, a knot with two little ears at the front, and the
    triangle hanging over the chest, lying on the shirt (a grid of points projected onto its surface)."""
    BF = F.BF; N1 = BF.P['N1']
    base = lambda q: F.top_raw(q, 0.0)
    acc = V.accent
    colour = lin(acc) + (1,)
    parts = []
    # the band round the neck's base
    zr = N1 - 0.047
    P, D = ring_even(base, (0.0, F.nax[1], zr), (0, 0, 1), 20)
    Vv = np.tile(np.array([0, 0, 1.0]), (len(P), 1))
    # the band dips toward the knot at the front and rides high at the back of the neck
    ang = np.arctan2(P[:, 0], -(P[:, 1] - F.nax[1]))                     # 0 at the front
    dz = -0.0125 * np.cos(ang / 2) ** 6 + 0.004 * np.cos((np.pi - np.abs(ang)) / 2) ** 2
    Q = P + D * 0.0034; Q[:, 2] += dz
    for _ in range(4):
        g = grad(base, Q); g /= np.linalg.norm(g, axis=1)[:, None]
        Q = Q - g * (base(Q) - 0.0034)[:, None]
    ring = tube('ScarfBand', Q, D, Vv, ellipse_profile(0.0052, 0.0072, 5), V)
    parts.append(Part(ring, colour, 4, TO.bind_follow(shirt)))
    # the triangle on the chest
    z_top = zr - 0.0125 - 0.003; z_tip = z_top - 0.080; hw_top = 0.034
    zs = np.linspace(z_top, z_tip, 8)
    nc = 5
    X = []; Z = []; idx = []
    for ri, z in enumerate(zs):
        t = max((z - z_tip) / (z_top - z_tip), 0.0)
        hw = hw_top * t ** 0.85
        ids = []
        for c in range(nc):
            x = -hw + 2 * hw * c / (nc - 1)
            if ri == len(zs) - 1 and c > 0: ids.append(ids[0]); continue     # the tip: one point
            X.append(x); Z.append(z + 0.011 * t ** 2 * (x / hw_top) ** 2); ids.append(len(X) - 1)      # (the top edge curves up round the neck)
        idx.append(ids)
    pts, nrm = _surface_points(base, X, Z)
    X = np.array(X); Zr = np.array(Z)
    mid = 1 - np.abs(X) / hw_top
    h = 0.0046 + 0.0014 * np.clip(mid, 0, 1)
    pts = pts + nrm * h[:, None]
    faces = []
    for r in range(len(idx) - 1):
        for c in range(nc - 1):
            quad = [idx[r][c], idx[r][c + 1], idx[r + 1][c + 1], idx[r + 1][c]]
            quad = [v for k, v in enumerate(quad) if v != quad[k - 1]]
            if len(quad) >= 3: faces.append(tuple(quad))
    o = mesh_object('Scarf', pts, faces, None)
    me = o.data; me.update()
    mp = me.polygons[len(faces) // 2]
    if (grad(base, np.array(mp.center)[None])[0] @ np.array(mp.normal)) < 0:
        for poly in me.polygons: poly.flip()
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.0034; so.offset = -1; so.use_rim = True; so.use_even_offset = True
    apply_mods(o); TB.to_base(o, V); smooth(o)
    parts.append(Part(o, tuple(c * 0.97 for c in colour[:3]) + (1,), 4, TO.bind_follow(shirt)))
    # the knot: a soft block with two little ears, standing off the chest at the band's front
    kp, kn = _surface_points(base, [0.0], [zr - 0.0125 - 0.001])
    c0 = kp[0] + kn[0] * 0.0085
    R = frame(kn[0], (0, 0, 1))                      # columns: sideways, up, out
    def knot(q):
        l = (q - c0) @ R
        body_ = ellipsoid((0, 0, 0), (0.0105, 0.0085, 0.0070))(l)
        ears = [ellipsoid((s * 0.0125, -0.0065, -0.0005), (0.0050, 0.0035, 0.0090), frame(unit((s * 0.55, -0.45, 0.3)), (0, 0, 1)))(l) for s in (1, -1)]
        return smin(smin(body_, ears[0], 0.004), ears[1], 0.004)
    ko = solid('ScarfKnot', knot, c0 - 0.03, c0 + 0.03, 0.0021, 130, V)
    parts.append(Part(ko, tuple(c * 0.9 for c in colour[:3]) + (1,), 4, TO.bind_follow(shirt)))
    return parts


def _bow(F, V, shirt):
    """A small ribbon bow at the front of the collar: a knot, two loops and two short tails, lying on the blouse (the
    bow is made flat in the tangent plane of its place, then draped on the blouse's surface)."""
    BF = F.BF; N1 = BF.P['N1']
    base = lambda q: F.top_raw(q, 0.0)
    colour = lin(V.accent) + (1,)
    zc = float(F.zn(-0.05)) - 0.004
    p0, n0 = _surface_points(base, [0.0], [zc]); p0 = p0[0]; n0 = n0[0]
    R = frame(n0, (0, 0, 1))                        # columns: sideways, up, out
    def to_l(q): return (q - p0) @ R
    def bow(q):
        l = to_l(q)
        knot = ellipsoid((0, 0, 0.0052), (0.0085, 0.0082, 0.0062))(l)
        d = knot
        for s in (1, -1):
            ang = math.radians(16) * s
            Rl = np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
            loop = ellipsoid((s * 0.0185, 0.003, 0.0035), (0.0165, 0.0095, 0.0040), Rl)(l)
            d = smin(d, loop, 0.004)
            at = math.radians(11) * s
            Rt = np.array([[math.cos(at), -math.sin(at), 0], [math.sin(at), math.cos(at), 0], [0, 0, 1]])
            tail = ellipsoid((s * 0.0065, -0.0215, 0.0020), (0.0060, 0.0170, 0.0026), Rt)(l)
            d = smin(d, tail, 0.003)
        return d
    lo = p0 - 0.06; hi = p0 + 0.06
    flat = solid('BowFlat', bow, lo, hi, 0.0022, 300, None, False)        # (built in final space: draped, then mapped to base)
    # drape on the blouse: every vertex keeps its height over the tangent plane, but stands on the blouse's surface there
    me = flat.data
    Vp = np.array([v.co for v in me.vertices])
    sp, sn = _surface_points(base, Vp[:, 0], Vp[:, 2])
    hgt = (Vp - p0) @ n0
    newp = sp + sn * (np.maximum(hgt, 0.0) + 0.0014)[:, None]
    faces = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(flat)
    bo = outward(mesh_object('Bow', newp, faces, V))
    return [Part(bo, colour, 4, TO.bind_follow(shirt))]


def _accent(F, V, shirt):
    if V.accessory == 'none': return []
    return _neckerchief(F, V, shirt) if V.accessory == 'neckerchief' else _bow(F, V, shirt)


# ----------------------------------------------------------------------------------------------
def _socks(F, V):
    parts = []
    for n in 'LR':
        x = F.BF.j['ankle' + n][0]
        so = solid('Sock' + n, F.socks[n], (x - 0.07, -0.06, 0.03), (x + 0.07, 0.09, F.sock_top + 0.02), 0.0042, 230, V, False)
        parts.append(Part(so, SOCK, 0))
    return parts


def _shoes(F, V):
    parts = []; BF = F.BF
    girl = bool(V.girl)
    for n, s in (('L', 1), ('R', -1)):
        upper = F.shoes[n]; Rz, o = upper.Rz, upper.o; an = BF.j['ankle' + n]
        def L(p, Rz=Rz, o=o): return (p - o) @ Rz
        box = (an[0] - 0.07, -0.19, -0.005), (an[0] + 0.07, 0.10, 0.11)
        upper_c, sole_c = tuple(lin(V.shoe)) + (1,), tuple(lin(V.sole)) + (1,)
        if girl:
            def strap(p, L=L, upper=upper):
                q = L(p)
                d = smax(upper(p) - 0.0028, np.abs(q[:, 1] + 0.046) - 0.010, 0.003)
                return smax(d, 0.034 - q[:, 2], 0.004)
            spring = lambda y: 0.004 * sstep(-0.09, -0.15, y)
            sole = TO._sole('Sole' + n, upper, spring, lambda y: 0.0125 + 0.0075 * sstep(-0.01, 0.01, y) + spring(y), 0.0024, V, 22, (0.02, 0.03, 0.04))
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0040, 220, V, False), upper_c, 0, 'Foot.' + n),
                      Part(sole, sole_c, 0, 'Foot.' + n),
                      Part(solid('ShoeStrap' + n, strap, *box, 0.0032, 80, V, False), shade(upper_c, 0.82), 0, 'Foot.' + n)]
        else:
            def cap(p, L=L, upper=upper):
                # the white rubber toe cap, its top edge sweeping up toward the tip
                q = L(p)
                d = smax(upper(p) - 0.0026, q[:, 1] + 0.098, 0.007)
                return smax(d, q[:, 2] - (0.030 + 0.3 * np.maximum(-0.098 - q[:, 1], 0)), 0.005)
            spring = lambda y: 0.012 * sstep(-0.09, -0.15, y)
            sole = TO._sole('Sole' + n, upper, spring, lambda y: 0.0165 + 0.75 * spring(y), 0.0026, V, 22, (0.025, 0.035, 0.045))
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0040, 220, V, False), upper_c, 0, 'Foot.' + n),
                      Part(sole, sole_c, 0, 'Foot.' + n),
                      Part(solid('ToeCap' + n, cap, *box, 0.003, 90, V, False), WHITE, 0, 'Foot.' + n)]
        sock = lambda p, sn=BF.shin[n]: sn(p) - 0.0035
        P, Dr = TO._opening(sock, upper, an, 14)
        Vz = np.cross(Dr, np.roll(P, -1, 0) - np.roll(P, 1, 0)); Vz /= np.linalg.norm(Vz, axis=1)[:, None]
        Vz *= np.sign(Vz[:, 2:3] + 1e-9)
        parts.append(Part(tube('ShoeCollar' + n, P + Dr * 0.003 + Vz * 0.0025, Dr, Vz, ellipse_profile(0.0052, 0.0064, 5), V),
                          shade(upper_c, 0.8), 0, 'Foot.' + n))
    return parts


def _randoseru(F, body, V):
    """The school backpack: a hard rounded box with a flap over its upper two thirds, a lock, and two wide padded
    straps that go over the shoulders and under the arms (the straps follow the ribcage, the box the Bag bone)."""
    parts = []; BF = F.BF; j = BF.j
    c, h, r = _bag_dims(V)
    col = lin(V.bag_colour) + (1,)
    main = rbox(c, h, r)
    def bag(p): return main(p)
    parts.append(Part(solid('Bag', bag, c - h - 0.03, c + h + 0.03, 0.0056, 330, V), col, 0, 'Bag'))
    # the flap: the box's skin, a hair proud, over the top and down the outer (+Y) face
    zf = c[2] - h[2] * 0.30
    def flap(p):
        d = smax(bag(p) - 0.0065, zf - p[:, 2], 0.004)
        return smax(d, (c[1] - h[1] * 0.15) - p[:, 1], 0.004)
    parts.append(Part(solid('BagFlap', flap, c - h - 0.03, c + h + 0.03, 0.0042, 380, V), shade(col, 0.88), 0, 'Bag'))
    # the lock, on the flap's lower edge
    cp = np.array([c[0], c[1] + h[1] + 0.008, zf + 0.012])
    def lock(p): return smax(rbox(cp, (0.020, 0.011, 0.020), 0.006)(p), flap(p) - 0.003, 0.002)
    parts.append(Part(solid('Lock', lock, cp - 0.05, cp + 0.05, 0.0022, 90, V), GOLD, 0, 'Bag'))
    # the straps: over the shoulder, a short run down the front, then under the arm to the bag's bottom corner
    off = 0.0105 + (F.vest_off - 0.0125 if V.garment == 'pinafore' else 0.0)
    def wear(p):
        d = smin(BF.torso(p) - off, BF.neck(p) - off, 0.03)
        for n in 'LR':
            arm = np.maximum(BF.uarm[n](p) - off - 0.01, (j['shoulder' + n][2] - 0.012) - p[:, 2])
            d = smin(d, arm, 0.03)
        return d
    zt = c[2] + h[2]; zb = c[2] - h[2]
    for n, s in (('L', 1), ('R', -1)):
        sh = j['shoulder' + n]
        ctrl = [(0.050, c[1] - 0.01, zt - 0.025), (0.054, 0.075, zt + 0.022), (0.066, 0.030, sh[2] + 0.048),
                (0.072, -0.034, sh[2] + 0.022), (0.078, -0.064, sh[2] - 0.038), (0.084, -0.056, sh[2] - 0.088),
                (0.088, -0.016, sh[2] - 0.135), (0.090, 0.034, zb + 0.07), (0.092, c[1] - 0.02, zb + 0.04)]
        pts = catmull([(s * x, y, z) for x, y, z in ctrl], 27)
        thick, half_w = 0.0045, 0.022
        inner = (bag(pts) > 0.004)[:, None] * 1.0
        for it in range(6):
            g = grad(wear, pts); g /= np.linalg.norm(g, axis=1)[:, None]
            tgt = pts - g * (wear(pts) - (thick + 0.002))[:, None]
            pts = pts * (1 - inner) + tgt * inner
            sm = pts.copy(); sm[1:-1] = (pts[:-2] + pts[1:-1] * 2 + pts[2:]) / 4
            pts = sm
        g = grad(wear, pts); g /= np.linalg.norm(g, axis=1)[:, None]
        t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
        g = g - t * (g * t).sum(1)[:, None]; g /= np.linalg.norm(g, axis=1)[:, None]
        bvec = np.cross(g, t)
        so = tube('BagStrap' + n, pts, g, bvec, rrect_profile(thick, half_w, 6), V, False)
        parts.append(Part(so, shade(col, 0.82), 0, bind_torso(body, V, with_bag=True)))
    return parts
