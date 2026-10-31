# The teens' clothes, shoes and bags. Base space: see teen_lib.
#
# Like the body (teen_body), everything is designed in teen space: the clothes are distance
# fields offset from the body field (so they sit on it everywhere; his loose shirt also hangs
# from a lofted drape), the girl's pleated skirt is a lofted ring mesh, collars are grids laid
# on the shirt round the neckline, and straps and bands are swept along curves found on the
# clothes' surfaces. Each piece is mapped back to base space with teen_body.ungrow.
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
from teen_lib import Part, activate, apply_mods, smooth, shade
import teen_body as TB
from teen_body import (smin, smax, round_cone, ellipsoid, rbox, frame, catmull, chain,
                       sdf_object, mesh_object, grad, field, tj, grow, ungrow)


# ----------------------------------------------------------------------------------------------
# Colours. The game recolours part 1 (top) and part 2 (legwear) from these defaults.
def palette(girl):
    # The school uniform: a white shirt and navy legwear, modelled in the colours the shop's
    # School Uniform recolours to (sRGB (0.97, 0.97, 0.99) and (0.22, 0.23, 0.42)), so wearing it
    # is (nearly) the identity. The skin is a warm, sunny tone that stands off the white shirt.
    if girl:
        return {'skin': (0.89, 0.6, 0.42, 1), 'top': (0.932, 0.932, 0.977, 1), 'legwear': (0.0395, 0.0437, 0.147, 1)}
    return {'skin': (0.85, 0.53, 0.33, 1), 'top': (0.932, 0.932, 0.977, 1), 'legwear': (0.0395, 0.0437, 0.147, 1)}


WHITE = (0.97, 0.97, 0.96, 1)
SOCK = (0.94, 0.94, 0.96, 1)       # off-white, so the cel shadow still reads on the socks
BAG = {True: (0.93, 0.73, 0.3, 1), False: (0.42, 0.065, 0.05, 1)}


def skin_color(girl):
    """The body's colour (bare skin everywhere; socks are their own pieces)."""
    return palette(girl)['skin']


def _bag_dims(girl):
    """Bag box in teen space: centre, half sizes, corner radius. Hers is a backpack (its top,
    handle included, stays below base z 1.17, teen 1.6475, so the ponytail never meets it); his
    is a satchel on a cross-body strap, hanging at the back of his right hip."""
    if girl:
        return np.array([0, 0.157, 1.438]), np.array([0.132, 0.055, 0.166]), 0.05
    return np.array([-0.04, 0.172, 1.07]), np.array([0.168, 0.038, 0.122]), 0.032


def bag_bone(girl):
    """The Bag bone (base space): head at the top edge of the bag, tail toward its bottom."""
    c, h, r = _bag_dims(girl)
    top = c + (0, 0, h[2]); bot = c - (0, 0, h[2] * 0.6)
    return tuple(ungrow(Vector(top), girl)), tuple(ungrow(Vector(bot), girl))


# ----------------------------------------------------------------------------------------------
# Helpers
def unit(v): v = np.asarray(v, dtype=np.float64); return v / np.linalg.norm(v)


def _wrap(a):
    return np.angle(np.exp(1j * np.asarray(a, dtype=np.float64)))


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def tris_of(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)


def ring_on(f, center, axis, n=32, r0=0.0, r1=0.25, ref=(0, -1, 0)):
    """Points where rays from `center` (in the plane normal to `axis`) leave the solid f for the
    last time: the outline of f's cross-section. Returns (points, outward dirs)."""
    center = np.asarray(center, float); ax = unit(axis)
    e1 = np.asarray(ref, float); e1 = unit(e1 - ax * (e1 @ ax)); e2 = np.cross(ax, e1)
    th = np.arange(n) / n * 2 * math.pi
    D = np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2
    rs = np.linspace(r1, r0, 240)
    P = center + D[:, None, :] * rs[None, :, None]
    F = f(P.reshape(-1, 3)).reshape(n, len(rs))
    first = np.argmax(F < 0, 1)
    lo = rs[first]; hi = rs[np.maximum(first - 1, 0)]
    for _ in range(20):
        mid = (lo + hi) / 2
        inn = f(center + D * mid[:, None]) < 0
        lo = np.where(inn, mid, lo); hi = np.where(inn, hi, mid)
    return center + D * ((lo + hi) / 2)[:, None], D


def ring_even(f, center, axis, n, ref=(1, 0, 0), dense=256, bend=0.06):
    """ring_on, densely sampled, then resampled to n points spaced by arc length plus a share of
    the turning angle (so rounded corners get more points). Returns (points, outward dirs in
    the ring's plane)."""
    P, _ = ring_on(f, center, axis, dense, ref=ref)
    ax = unit(axis)
    T = np.roll(P, -1, 0) - P
    seg = np.linalg.norm(T, axis=1)
    Tu = T / np.maximum(seg, 1e-12)[:, None]
    turn = np.arccos(np.clip((Tu * np.roll(Tu, 1, 0)).sum(1), -1, 1))
    w = seg + bend * turn
    cum = np.concatenate([[0], np.cumsum(w)])
    tgt = np.arange(n) / n * cum[-1]
    idx = np.searchsorted(cum, tgt, side='right') - 1
    fr = ((tgt - cum[idx]) / np.maximum(w[idx], 1e-12))[:, None]
    Q = P[idx] + (np.roll(P, -1, 0)[idx] - P[idx]) * fr
    Tq = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
    D = np.cross(Tq, ax); D /= np.linalg.norm(D, axis=1)[:, None]
    D *= np.sign(((Q - np.asarray(center, float)) * D).sum(1))[:, None]
    return Q, D


def sweep(P, U, V, profile, closed=True, caps=True):
    """A tube along the points P: each cross-section is the profile's (a, b) pairs placed at
    P + U*a + V*b (counter-clockwise from U toward V). Returns verts, faces."""
    n = len(P); m = len(profile)
    verts = [P[i] + U[i] * a + V[i] * b for i in range(n) for a, b in profile]
    faces = []
    for i in range(n if closed else n - 1):
        i2 = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((i * m + k, i2 * m + k, i2 * m + k2, i * m + k2))
    if not closed and caps:
        faces.append(tuple(range(m))); faces.append(tuple((n - 1) * m + k for k in range(m))[::-1])
    return verts, faces


def outward(o):
    """Make a closed mesh's normals point outward (flip if its signed volume is negative)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    if bm.calc_volume(signed=True) < 0:
        for f in bm.faces: f.normal_flip()
        bm.to_mesh(o.data); o.data.update()
    bm.free()
    return o


def ellipse_profile(a, b, m=8):
    return [(a * math.cos(2 * math.pi * k / m), b * math.sin(2 * math.pi * k / m)) for k in range(m)]


def rrect_profile(a, b, m=8):
    """A rounded rectangle (superellipse) of half sizes a (U) and b (V)."""
    out = []
    for k in range(m):
        t = 2 * math.pi * (k + 0.5) / m; c, s = math.cos(t), math.sin(t)
        out.append((a * np.sign(c) * abs(c) ** 0.4, b * np.sign(s) * abs(s) ** 0.4))
    return out


def tube(name, P, U, V, profile, girl, closed=True):
    verts, faces = sweep(P, U, V, profile, closed)
    return outward(mesh_object(name, verts, faces, girl))


def band(f, center, axis, thick, height, girl, name, n=36, ref=(0, -1, 0), lift=0.0, m=8):
    """A ribbed band hugging the outline of f round `axis`."""
    P, D = ring_on(f, center, axis, n, ref=ref)
    V = np.tile(unit(axis), (n, 1))
    return tube(name, P + D * lift, D, V, ellipse_profile(thick, height, m), girl)


def blob(name, c, nrm, radii, girl, seg=8, rings=5):
    """A small ellipsoid (a button) with its short axis along nrm."""
    R = frame(nrm, (0, 0, 1)); verts = []; faces = []
    for i in range(1, rings):
        ph = math.pi * i / rings
        for j in range(seg):
            th = 2 * math.pi * j / seg
            verts.append(c + R @ np.array([math.sin(ph) * math.cos(th) * radii[0], math.sin(ph) * math.sin(th) * radii[1], math.cos(ph) * radii[2]]))
    top = len(verts); verts.append(c + R @ np.array([0, 0, radii[2]]))
    bot = len(verts); verts.append(c + R @ np.array([0, 0, -radii[2]]))
    for i in range(rings - 2):
        for j in range(seg):
            j2 = (j + 1) % seg
            faces.append((i * seg + j, i * seg + j2, (i + 1) * seg + j2, (i + 1) * seg + j))
    for j in range(seg):
        j2 = (j + 1) % seg
        faces.append((top, j2, j)); faces.append((bot, (rings - 2) * seg + j, (rings - 2) * seg + j2))
    return outward(mesh_object(name, verts, faces, girl))


def surface_point(f, origin, direction, tmax=0.4):
    """First point along a ray where f becomes negative, and the outward normal there."""
    origin = np.asarray(origin, float); d = unit(direction)
    ts = np.linspace(0, tmax, 400)
    F = f(origin + ts[:, None] * d)
    i = int(np.argmax(F < 0)); lo, hi = ts[max(i - 1, 0)], ts[i]
    for _ in range(30):
        m = (lo + hi) / 2
        if f((origin + m * d)[None])[0] < 0: hi = m
        else: lo = m
    p = origin + hi * d
    return p, unit(grad(f, p[None])[0])


def solid(name, f, lo, hi, h, tris, girl, symmetric=True, dense=None):
    return outward(sdf_object(name, f, lo, hi, h, tris=tris, girl=girl, symmetric=symmetric, dense=dense))


# ----------------------------------------------------------------------------------------------
# Binding helpers (run by teen.py after grow(): coordinates are then teen space)
def _transfer(o, body):
    m = o.modifiers.new('dt', 'DATA_TRANSFER'); m.object = body; m.use_vert_data = True; m.data_types_verts = {'VGROUP_WEIGHTS'}
    m.vert_mapping = 'POLYINTERP_NEAREST'; m.layers_vgroup_select_src = 'ALL'; m.layers_vgroup_select_dst = 'NAME'
    activate(o); bpy.ops.object.datalayout_transfer(modifier=m.name); bpy.ops.object.modifier_apply(modifier=m.name)


def _attach(o, rig):
    o.parent = rig; a = o.modifiers.new('arm', 'ARMATURE'); a.object = rig


def _weights(o):
    names = {g.index: g.name for g in o.vertex_groups}
    return [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in o.data.vertices]


def _set_weights(o, W):
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    groups = {}
    for i, w in enumerate(W):
        s = sum(w.values()) or 1.0
        for n, x in w.items():
            if x / s < 1e-4: continue
            if n not in groups: groups[n] = o.vertex_groups.new(name=n)
            groups[n].add([i], x / s, 'REPLACE')


def bind_with_bag(body, girl):
    """Copy the body's weights, but keep the straps on the ribcage (the arms' weights go to the
    Chest, or the Spine lower down, so a swinging arm never drags the strap with it); then hand
    the ends near the backpack to the Bag bone."""
    c, h, r = _bag_dims(girl)
    bag = rbox(c, h, r)
    j = tj(girl)
    def bind(o, rig):
        _transfer(o, body)
        W = _weights(o)
        V = np.array([v.co for v in o.data.vertices])
        k = 1 - sstep(0.0, 0.08, bag(V))
        up = sstep(j['spine'][2] + 0.05, j['chest'][2], V[:, 2])
        for w, kk, u in zip(W, k, up):
            arm = sum(w.pop(n) for n in list(w) if n.startswith(('UpperArm', 'LowerArm', 'Hand')))
            if arm:
                w['Chest'] = w.get('Chest', 0) + arm * u
                w['Spine'] = w.get('Spine', 0) + arm * (1 - u)
            leg = sum(w.pop(n) for n in list(w) if n.startswith(('UpperLeg', 'LowerLeg', 'Foot')))
            if leg: w['Hips'] = w.get('Hips', 0) + leg
            for n in list(w): w[n] *= (1 - kk)
            w['Bag'] = w.get('Bag', 0) + kk
        _set_weights(o, W); _attach(o, rig)
    return bind


def smooth_knees(body, girl):
    """Soften the knees of the body's (bone-heat) weights: UpperLeg/LowerLeg cross-fade over
    about +-4.5 cm round the joint (50/50 at the joint), so a bent knee stays round instead of
    pinching to a point. Runs once, before any piece copies the body's weights."""
    if body.get('knees_done'): return
    body['knees_done'] = 1
    j = tj(girl)
    W = _weights(body)
    V = np.array([v.co for v in body.data.vertices])
    for n in 'LR':
        kn, hp, an = j['knee' + n], j['hip' + n], j['ankle' + n]
        up = unit(hp - kn); dn = unit(an - kn)
        axis = unit(dn - up)                     # through the knee, thigh -> shin
        rel = V - kn
        s = rel @ axis
        radial = np.linalg.norm(rel - s[:, None] * axis, axis=1)
        sel = np.nonzero((np.abs(s) < 0.06) & (radial < 0.085))[0]
        u, l = 'UpperLeg.' + n, 'LowerLeg.' + n
        for i in sel:
            w = W[i]; tot = w.get(u, 0) + w.get(l, 0)
            if tot < 0.6 * sum(w.values()): continue
            t = float(sstep(-0.045, 0.045, s[i]))
            w[u] = tot * (1 - t); w[l] = tot * t
    _set_weights(body, W)


def bind_damp_legs(body, keep=0.4, girl=None):
    """Copy the body's weights but damp the thighs' pull (a shirt hem near the hips)."""
    def bind(o, rig):
        if girl is not None: smooth_knees(body, girl)
        _transfer(o, body)
        W = _weights(o)
        for w in W:
            for n in list(w):
                if n.startswith('UpperLeg') or n.startswith('LowerLeg'):
                    w['Hips'] = w.get('Hips', 0) + w[n] * (1 - keep); w[n] *= keep
        _set_weights(o, W); _attach(o, rig)
    return bind


def smoother(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * t * (t * (6 * t - 15) + 10)


def bind_skirt(girl, z_top, z_hem):
    """The pleated skirt follows the thighs below the waistband (so they never poke through): the
    legs' pull ramps in smoothly from the band down to the hem; round the skirt the two legs
    cross-fade over a wide band (no seam at the centre), and the centre front and back keep a
    share on the hips, so a lifted thigh pushes out a smooth bell instead of splitting it."""
    def bind(o, rig):
        W = []
        for v in o.data.vertices:
            x, y, z = v.co
            front = float(sstep(0.03, -0.07, y))
            # no pull above the hip joints (points there would swing into the belly), full pull a
            # hand's width below them
            down = float(smoother(z_top, z_hem, z))
            side = float(sstep(-0.09, 0.09, x))
            centre = 1 - abs(2 * side - 1)
            fb = 0.8 + 0.16 * front                                 # the front follows the thighs more
            legs = down * fb * (1 - 0.2 * centre)
            W.append({'Hips': 1 - legs, 'UpperLeg.L': legs * side, 'UpperLeg.R': legs * (1 - side)})
        _set_weights(o, W); _attach(o, rig)
    return bind


def bind_loose_shirt(body, girl, keep=0.5):
    """A loose shirt: copy the body's weights, but only the sleeves follow the arms (the shirt's
    sides hang near the arms, whose weights would tear them open when an arm swings: there the
    arms' share goes to the Chest, or the Spine lower down); the thighs pull the hem half way."""
    j = tj(girl)
    def bind(o, rig):
        smooth_knees(body, girl)
        _transfer(o, body)
        W = _weights(o)
        V = np.array([v.co for v in o.data.vertices])
        up = sstep(j['spine'][2] + 0.05, j['chest'][2], V[:, 2])
        # a vertex is on a sleeve where it lies nearer that sleeve's surface than the body's
        F = fields(girl); BF = F.BF
        db = smin(BF.torso(V) - 0.016, F.drape(V), 0.035)
        ka = {n: sstep(0.006, -0.006, f.raw(V) - db) for n, f in zip('LR', F.sleeves)}
        for i, w in enumerate(W):
            for n in 'LR':
                arm = sum(w.pop(b) for b in list(w) if b.startswith(('UpperArm', 'LowerArm', 'Hand')) and b.endswith(n))
                if not arm: continue
                k = float(ka[n][i])
                w['UpperArm.' + n] = w.get('UpperArm.' + n, 0) + arm * k
                w['Chest'] = w.get('Chest', 0) + arm * (1 - k) * up[i]
                w['Spine'] = w.get('Spine', 0) + arm * (1 - k) * (1 - up[i])
            for b in list(w):
                if b.startswith('UpperLeg') or b.startswith('LowerLeg'):
                    w['Hips'] = w.get('Hips', 0) + w[b] * (1 - keep); w[b] *= keep
        _set_weights(o, W); _attach(o, rig)
    return bind


def bind_trousers(body, girl):
    """Copy the body's weights (knees softened first), but damp the thighs' pull on the waist
    part, which sits under the shirt (that follows the legs only half way)."""
    def bind(o, rig):
        smooth_knees(body, girl)
        _transfer(o, body)
        W = _weights(o)
        V = np.array([v.co for v in o.data.vertices])
        keep = 1 - 0.55 * sstep(1.0, 1.12, V[:, 2])
        for w, kp in zip(W, keep):
            # the hands hang right by the hips: their weights would drag the trousers along
            arm = sum(w.pop(n) for n in list(w) if n.startswith(('UpperArm', 'LowerArm', 'Hand')))
            if arm: w['Hips'] = w.get('Hips', 0) + arm
            for n in list(w):
                if n.startswith('UpperLeg'):
                    w['Hips'] = w.get('Hips', 0) + w[n] * (1 - kp); w[n] *= kp
        _set_weights(o, W); _attach(o, rig)
    return bind


# ----------------------------------------------------------------------------------------------
# The clothes' fields (teen space), shared by the builders and by teen_body (which thins out
# and tucks in the skin the clothes cover).
class Fields:
    pass


_CACHE = {}


def fields(girl):
    if girl in _CACHE: return _CACHE[girl]
    BF = field(girl); j = BF.j; F = Fields(); F.BF = BF
    n0 = j['neck0']
    zf, zb = n0[2] - 0.028, n0[2] + 0.012           # neckline height at the front (y -0.06) and back (y +0.07)
    F.zn = lambda y: zf + (zb - zf) * (y + 0.06) / 0.13
    F.nax = np.array([0, n0[1] + 0.003, 0])
    torso, neck = BF.torso, BF.neck
    if girl:
        def sleeve(n, s):
            sh, el = j['shoulder' + n], j['elbow' + n]
            adir = unit(el - sh)
            ua = BF.uarm[n]
            puff = ellipsoid(sh + adir * 0.055 + (s * 0.006, 0, 0.004), (0.052, 0.054, 0.08), frame(adir))
            hem = sh + adir * 0.16
            def raw(p): return smin(ua(p) - 0.0085, puff(p), 0.035)
            def f(p): return smax(raw(p), (p - hem) @ adir, 0.004)
            f.raw = raw; f.end = hem; f.dir = adir
            return f
        F.sleeves = [sleeve('L', 1), sleeve('R', -1)]
        def top_raw(p, neck_off=0.004):
            z = p[:, 2]; rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            # a soft blousing just above the skirt's waistband (top at 1.335); tucked in under it
            off = 0.011 + 0.003 * sstep(1.42, 1.37, z) * sstep(1.35, 1.37, z) - 0.006 * sstep(1.326, 1.306, z) \
                - 0.006 * sstep(0.11, 0.075, rho) * sstep(1.6, 1.66, z)
            d = smin(torso(p) - off, neck(p) - neck_off, 0.025)
            for f in F.sleeves: d = smin(d, f(p), 0.03)
            return d
        F.hem = 1.248; F.hole = 0.058
    else:
        # straight-cut school trousers to the shoes, under a loose, untucked short-sleeved shirt
        F.trousers_top = 1.19                 # under the shirt only (its hem is at about 1.03-1.06)
        def sleeve(n, s):
            # a wide, loose sleeve to about half way down the upper arm
            sh, el = j['shoulder' + n], j['elbow' + n]
            adir = unit(el - sh)
            end = sh + adir * 0.185
            ru = BF.r['uarm'][0]
            # (its axis a little outside the arm's, so the sleeve stands off the shirt's side)
            out = np.array([s * 0.013, 0, 0])
            cone = round_cone(sh + adir * 0.045 + out, end + adir * 0.01 + out, ru + 0.011, ru + 0.018)
            def raw(p): return smin(BF.uarm[n](p) - 0.008, cone(p), 0.02)
            def f(p): return smax(raw(p), (p - end) @ adir, 0.003)
            f.raw = raw; f.end = end; f.dir = adir
            return f
        F.sleeves = [sleeve('L', 1), sleeve('R', -1)]
        shz = j['shoulderL'][2]
        def leg_tube(n):
            # a straight leg: a gently tapering tube round the leg's axis (roomy over the thigh,
            # hanging straight past the knee and calf), never tighter than the leg itself
            hp, kn, an = j['hip' + n], j['knee' + n], j['ankle' + n]
            s_ = 1 if n == 'L' else -1
            axis = chain([hp + (s_ * 0.006, 0.004, 0.03), kn + (s_ * 0.002, 0.002, 0.0), an + (0, -0.004, -0.02)],
                         (0.093, 0.074, 0.069), 0.0)
            th, sn = BF.thigh[n], BF.shin[n]
            def f(p):
                return smin(axis(p), np.minimum(th(p), sn(p)) - 0.01, 0.03)
            return f
        tubes = [leg_tube('L'), leg_tube('R')]
        F.tubes = tubes
        def trousers_raw(p):
            z = p[:, 2]
            a, b = tubes[0](p), tubes[1](p)
            # the legs meet in a proper crotch seam (no skin between them)
            legs = smin(a, b, 0.008) + (smin(a, b, 0.045) - smin(a, b, 0.008)) * sstep(0.90, 0.985, z)
            return smin(torso(p) - 0.012, legs, 0.035)
        def hem_z(p):
            # resting on the shoe: lower at the heel than over the instep
            return 0.094 - 0.26 * (p[:, 1] - 0.0)
        def trousers(p):
            d = smax(trousers_raw(p), p[:, 2] - F.trousers_top, 0.006)
            return smax(d, hem_z(p) - p[:, 2], 0.003)
        F.trousers_raw, F.trousers, F.trouser_hem = trousers_raw, trousers, hem_z
        # the loose shirt: it falls straight from the chest and shoulder blades (it does not follow
        # the waist in) and flares a little over the hips
        drape = TB.loft([(0.95, 0.188, 0.120, 0.010, 2.4), (1.06, 0.184, 0.118, 0.008, 2.4),
                         (1.20, 0.160, 0.110, 0.002, 2.4), (1.34, 0.146, 0.106, -0.004, 2.4),
                         (1.46, 0.128, 0.110, -0.009, 2.3), (1.56, 0.126, 0.112, -0.012, 2.3),
                         (1.63, 0.110, 0.100, -0.004, 2.2)], 0.94, 1.64, 0.03)
        F.drape = drape
        def top_raw(p, neck_off=0.003):
            z = p[:, 2]; rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            off = 0.016 + 0.006 * sstep(1.6, 1.3, z) - 0.009 * sstep(0.12, 0.08, rho) * sstep(1.66, 1.73, z)
            # closer at the sides under the arms, so the sleeves hang free of the shirt's sides
            off = off - 0.0135 * sstep(0.085, 0.115, np.abs(p[:, 0])) * sstep(1.30, 1.40, z) * sstep(1.68, 1.60, z)
            d = smin(torso(p) - off, neck(p) - neck_off, 0.025)
            d = smin(d, drape(p), 0.035)
            # one continuous slope from the neck over the shoulder into the sleeve; below the
            # armpit the sleeve barely blends (a crisp fold, and no web to the shirt's side)
            w = sstep(shz - 0.07, shz - 0.01, z)
            ka = 0.005 + 0.019 * sstep(shz - 0.13, shz - 0.07, z)
            for f in F.sleeves:
                fp = f(p)
                d = smin(d, fp, ka) + (smin(d, fp, 0.06) - smin(d, fp, ka)) * w
            # untucked: the shirt always hangs over the trousers
            d = smin(d, trousers_raw(p) - 0.010 + 0.08 * sstep(1.22, 1.28, z), 0.01)
            return d
        # the hem: a soft curve, a little higher at the sides than at the front and back
        def hem_fn(p):
            th = np.arctan2(p[:, 0], -(p[:, 1] - 0.01))
            return 1.03 + 0.028 * np.sin(th) ** 2
        F.hem_fn = hem_fn
        F.hem = 1.03; F.hole = 0.064
        # an open collar: the neckline runs round the neck base at the back and dips in a V at the front
        n0z = j['neck0'][2]
        zv, zsd, zbk, av = n0z - 0.085, n0z - 0.006, n0z + 0.016, 0.62
        def zcut_th(a):
            a = np.abs(_wrap(a))
            v = zv + (zsd - zv) * np.clip(a / av, 0, 1)
            return np.where(a < av, v, zsd + (zbk - zsd) * sstep(av, math.pi, a))
        def zcut(p):
            return zcut_th(np.arctan2(p[:, 0], -(p[:, 1] - F.nax[1])))
        F.zcut, F.zcut_th = zcut, zcut_th
        def hole_r(p):
            th = np.arctan2(p[:, 0], -(p[:, 1] - F.nax[1]))
            return 0.105 + 0.05 * np.maximum(np.cos(th), 0) ** 2
        F.hole_r = hole_r
    def top(p):
        if girl:
            d = smax(top_raw(p), F.hem - p[:, 2], 0.005)
            rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            hole = np.maximum(rho - F.hole, F.zn(p[:, 1]) - p[:, 2])
        else:
            d = smax(top_raw(p), F.hem_fn(p) - p[:, 2], 0.004)
            rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            hole = np.maximum(F.zcut(p) + 0.002 - p[:, 2], rho - F.hole_r(p))
        return smax(d, -hole, 0.004)
    F.top_raw, F.top = top_raw, top
    # socks (hers; his are hidden by the trousers)
    F.sock_top = 0.497 if girl else 0.175
    def sock(n):
        sn = BF.shin[n]; t = F.sock_top
        cuff = 0.027 if girl else 0.02
        def f(p):
            z = p[:, 2]
            # a fold-over ribbed cuff at the top, 3-3.5 mm proud
            d = sn(p) - 0.0035 - (0.0034 if girl else 0.0025) * sstep(t - cuff - 0.004, t - cuff, z)
            d = smax(d, z - t, 0.0045)
            return smax(d, 0.045 - z, 0.003)
        return f
    F.socks = {'L': sock('L'), 'R': sock('R')}
    # shoes (uppers), in each foot's frame
    F.shoes = {}
    for n, s in (('L', 1), ('R', -1)):
        an = j['ankle' + n]
        yaw = math.radians(5) * s                      # toes turned out a touch
        Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
        o = np.array([an[0] + s * 0.002, 0.0, 0.0])
        if girl:   # a sleek loafer: slim, low toe and a longer vamp
            parts = (ellipsoid((0, 0.036, 0.046), (0.041, 0.046, 0.043)), ellipsoid((0, -0.042, 0.038), (0.044, 0.082, 0.037)),
                     ellipsoid((0, -0.117, 0.026), (0.041, 0.069, 0.022)))
            zcut = 0.008
        else:      # a sneaker: rounded toe box, the instep rising to the laces
            parts = (ellipsoid((0, 0.038, 0.056), (0.045, 0.05, 0.05)), ellipsoid((0, -0.045, 0.051), (0.05, 0.09, 0.046)),
                     ellipsoid((0, -0.12, 0.042), (0.049, 0.068, 0.04)))
            zcut = 0.016
        zw = 0.03 if girl else 0.046     # below this the sides drop straight to the sole (no ledge)
        def upper(p, Rz=Rz, o=o, parts=parts, zcut=zcut, zw=zw):
            q = (p - o) @ Rz
            body = lambda q: smin(smin(parts[0](q), parts[1](q), 0.03), parts[2](q), 0.03)
            d = body(q)
            qf = q.copy(); qf[:, 2] = zw
            d = smin(d, smax(body(qf), q[:, 2] - zw, 0.012), 0.008)
            return smax(d, zcut - q[:, 2], 0.004)
        upper.Rz = Rz; upper.o = o
        F.shoes[n] = upper
    _CACHE[girl] = F
    return F


def cover(girl):
    """For teen-space points: how deep they lie inside clothes the player never sees through
    (> 0 inside), and whether they are covered only at rest (thighs in the skirt, legs in the
    socks), for thinning out the skin underneath."""
    F = fields(girl); BF = F.BF
    def f(p):
        z = p[:, 2]
        d = -F.top(p)
        for n in 'LR': d = np.maximum(d, -F.shoes[n](p) - 0.006)
        arm = np.minimum(BF.arm_full('L')(p), BF.arm_full('R')(p))
        if girl:   # the hips inside the skirt (the thighs show when she kicks)
            sk = np.minimum(np.minimum(z - 0.99, 1.30 - z), arm - 0.01)
            d = np.maximum(d, np.minimum(sk, 0.02))
            semi = (z > 0.72) & (z < 1.0) & (arm > 0.01)
        else:
            d = np.maximum(d, -F.trousers(p))
            semi = np.zeros(len(p), bool)
        if girl:
            sockd = np.maximum(-F.socks['L'](p), -F.socks['R'](p))
            semi |= sockd > 0.002
        else:
            sockd = np.zeros(len(p))
        return d, semi & (d < 0.006), sockd
    return f


# ----------------------------------------------------------------------------------------------
def build_outfit(girl, body):
    F = fields(girl)
    parts = _girl_clothes(F, body) if girl else _boy_clothes(F, body)
    if girl: parts += _socks(F, girl)
    parts += _shoes(F, girl)
    parts += _backpack(F, body, girl) if girl else _satchel(F, body)
    tot = sum(tris_of(p.obj) for p in parts)
    print('outfit parts', ', '.join('%s %d' % (p.obj.name, tris_of(p.obj)) for p in parts))
    print('outfit tris', tot, 'body tris', tris_of(body), 'sum', tot + tris_of(body))
    bag_top = max(max((p.obj.matrix_world @ v.co).z for v in p.obj.data.vertices) for p in parts if p.bind == 'Bag')
    print('backpack top (base z)', round(bag_top, 4))
    return parts


def _girl_clothes(F, body):
    girl = True; BF = F.BF
    pal = palette(girl); top, leg = pal['top'], pal['legwear']
    parts = []
    bl = solid('Blouse', F.top, (-0.25, -0.13, 1.22), (0.25, 0.13, 1.78), 0.006, 1400, girl)
    parts.append(Part(bl, top, 1, bind_damp_legs(body, 0.0, girl)))
    for f, n in zip(F.sleeves, 'LR'):
        b = band(f.raw, f.end - f.dir * 0.005, f.dir, 0.0055, 0.0075, girl, 'Cuff' + n, 18, ref=(0, 0, 1), m=5)
        parts.append(Part(b, shade(top, 0.96), 1))
    parts.append(Part(_peter_pan(F, girl), leg, 2))     # a navy collar, in the skirt's colour
    for z in (1.555, 1.47, 1.385):    # buttons down the front (low, so they stay out of the silhouette)
        p, nrm = surface_point(F.top, (0, -0.3, z), (0, 1, 0))
        parts.append(Part(blob('Button', p + nrm * 0.0006, nrm, (0.0068, 0.0068, 0.0022), girl, 8, 4), (0.99, 0.98, 0.95, 1), 0))
    parts.append(_skirt(F, girl, leg))
    return parts


def _peter_pan(F, girl):
    """A rounded Peter Pan collar: two lobes lying on the blouse round the neckline, meeting at
    the front. A (round the neck) x (across) grid projected onto the blouse, then given a
    thickness."""
    BF = F.BF
    base = lambda p: F.top_raw(p, 0.0)
    thn, W, Rr = 0.11, 0.05, 0.036
    ts = np.linspace(0, 1, 30)
    ts = 0.5 - 0.5 * np.cos(ts * math.pi)          # denser at the lobe tips
    TH = thn + ts * (2 * math.pi - 2 * thn)
    nv = 5
    cz = F.zn(F.nax[1])
    ztilt = (F.zn(0.07) - F.zn(-0.06)) / 0.13
    ax = unit((0, -ztilt, 1))
    P0, D0 = ring_on(BF.neck, (0, F.nax[1], cz), ax, 720)
    ang0 = np.arctan2(D0[:, 0], -D0[:, 1]) % (2 * math.pi)
    grid = []
    for th in TH:
        k = np.argmin(np.abs((ang0 - th + math.pi) % (2 * math.pi) - math.pi))
        pin = P0[k]
        arc = min(th - thn, 2 * math.pi - thn - th) * 0.07 + 0.0012
        w = W * math.sqrt(max(0.0, 1 - (1 - min(arc / Rr, 1)) ** 2))
        dh = np.array([math.sin(th), -math.cos(th), 0.0])
        grid.append([pin + dh * (0.002 + (i / (nv - 1)) * w) + np.array([0, 0, 0.004]) for i in range(nv)])
    G = np.array(grid).reshape(-1, 3)
    off = np.tile(np.linspace(0.0068, 0.0052, nv), len(TH))
    for _ in range(5):
        g = grad(base, G); g /= np.linalg.norm(g, axis=1)[:, None]
        G = G - g * (base(G) - off)[:, None]
    faces = []
    for a in range(len(TH) - 1):
        for i in range(nv - 1):
            faces.append((a * nv + i, a * nv + i + 1, (a + 1) * nv + i + 1, (a + 1) * nv + i))
    o = mesh_object('Collar', G, faces, None)
    me = o.data; me.update()
    mid = me.polygons[len(faces) // 2]
    if (grad(base, np.array(mid.center)[None])[0] @ np.array(mid.normal)) < 0:
        for poly in me.polygons: poly.flip()
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.0034; so.offset = -1; so.use_rim = True; so.use_even_offset = True
    apply_mods(o); TB.to_base(o, girl); smooth(o)
    return o


def _skirt(F, girl, leg_col):
    """A navy knife-pleated skirt: a crisp 4.5 cm waistband (a shade darker), then pleats that
    start right under it (stitched flat to the hip, opening below), the radius growing smoothly
    from the waist over the hips into an A-line flare."""
    BF = F.BF
    lower = lambda p: smin(BF.torso(p), smin(BF.leg_full('L')(p), BF.leg_full('R')(p), 0.01), 0.06)
    NP = 8                       # knife pleats per side, mirrored about the centre front
    PH1 = 0.88                   # where a pleat's face ends and its fold begins
    ring = []
    for k in range(NP):      # (an extra column in the centre-front pleats: the legs' pull blends there)
        ring += [(math.pi * (k + s_) / NP, s_) for s_ in ((0.0, 0.45, PH1) if k == 0 else (0.0, PH1))]
    ring += [(math.pi, 0.0)]
    ring = ring + [(-a, ph) for a, ph in reversed(ring[1:-1])]
    A = np.array([a for a, _ in ring]); PH = np.array([ph for _, ph in ring])
    M = len(ring)
    D = np.stack([np.sin(A), -np.cos(A), np.zeros(M)], 1)
    zw_top, zw_bot, z_hem = 1.335, 1.29, 0.672
    F.skirt_band = (zw_top, zw_bot); F.skirt_hem = z_hem
    def cy_of(z): return BF.torso_core.prof(np.array([z]))[2][0] if z > 1.03 else 0.008
    def radial(z):
        cen = np.array([0, cy_of(z), z])
        rs = np.linspace(0.32, 0.0, 320)
        P = cen + D[:, None, :] * rs[None, :, None]
        Fv = lower(P.reshape(-1, 3)).reshape(M, len(rs))
        hit = (Fv < 0).any(1)
        return np.where(hit, rs[np.argmax(Fv < 0, 1)], 0.0)
    # the waistband: a vertical band over the tucked-in blouse
    band_r = np.max([radial(z) for z in np.linspace(zw_bot, zw_top, 4)], 0) + 0.026
    # the skirt's profile on a dense ladder of heights, per column: never closer to the body
    # than the ease, monotonic downward, an A-line flare below the hips, then smoothed in z
    zd = np.arange(zw_bot, z_hem - 0.03, -0.005)
    prof = np.array([radial(z) + 0.0125 for z in zd])
    prof = np.maximum(prof, band_r - 0.0045)
    prof = np.maximum.accumulate(prof, 0)
    flare = math.tan(math.radians(10.0))
    x = 1.20 - zd; w = 0.05
    side_k = 1 - 0.28 * np.sin(A) ** 2          # a little less flare at the sides (clear of the hands)
    prof = prof + (flare * np.where(x > w, x - w / 2, np.maximum(x, 0) ** 2 / (2 * w)))[:, None] * side_k[None, :]
    ker = np.exp(-0.5 * (np.arange(-8, 9) * 0.005 / 0.016) ** 2); ker /= ker.sum()
    padded = np.concatenate([np.repeat(prof[:1], 8, 0), prof, np.repeat(prof[-1:], 8, 0)])
    prof = np.stack([np.convolve(padded[:, m], ker, 'valid') for m in range(M)], 1)
    prof = np.maximum.accumulate(np.maximum(prof, band_r - 0.0045), 0)
    zs = [zw_top + 0.0016, zw_top, zw_bot, zw_bot - 0.0012, 1.245, 1.195, 1.145, 1.08, 1.0, 0.915, 0.83, 0.75, z_hem]
    rings = []
    for zi, z in enumerate(zs):
        cen = np.array([0, cy_of(z), z])
        if zi == 0: r = band_r - 0.0016
        elif z >= zw_bot - 1e-6: r = band_r
        else:
            r = np.array([np.interp(-z, -zd, prof[:, m]) for m in range(M)])
            r = r + 0.018 * float(sstep(1.275, 1.15, z)) * PH / PH1      # the pleats open below the hip
        rings.append(cen + D * r[:, None])
    verts = np.concatenate(rings); faces = []
    for i in range(len(zs) - 1):
        for k in range(M):
            k2 = (k + 1) % M
            faces.append((i * M + k, i * M + k2, (i + 1) * M + k2, (i + 1) * M + k))
    o = mesh_object('Skirt', verts, faces, None)
    me = o.data; mid = me.polygons[len(faces) // 2]
    if np.array(mid.normal) @ (np.array(mid.center) - np.array([0, 0.008, mid.center[2]])) < 0:
        for poly in me.polygons: poly.flip()
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.005; so.offset = -1; so.use_rim = True
    so.use_even_offset = True
    apply_mods(o); TB.to_base(o, girl); smooth(o)
    band_c = shade(leg_col, 0.86); fold_c = shade(leg_col, 0.7)
    def col(co, cen):
        p = grow(cen, girl)
        if p.z > zw_bot - 0.0006: return band_c
        u = (abs(math.atan2(p.x, -(p.y - cy_of(p.z)))) / math.pi * NP) % 1.0
        return fold_c if u > PH1 + 0.01 else leg_col
    return Part(o, col, 2, bind_skirt(girl, 1.11, 0.97))


def _boy_clothes(F, body):
    girl = False; BF = F.BF; j = BF.j
    pal = palette(girl); top, leg = pal['top'], pal['legwear']
    parts = []
    def edges(V):      # the neckline (under the rib) and the rolled hem stay dense
        rho = np.hypot(V[:, 0], V[:, 1] - F.nax[1])
        return ((rho < 0.1) & (V[:, 2] > j['neck0'][2] - 0.07)) | (V[:, 2] < F.hem + 0.024)
    def edges(V):      # the open neckline and the sleeve ends stay dense
        rho = np.hypot(V[:, 0], V[:, 1] - F.nax[1])
        ends = np.zeros(len(V), bool)
        for f in F.sleeves: ends |= np.abs((V - f.end) @ f.dir) < 0.02
        return ((rho < 0.16) & (V[:, 2] > j['neck0'][2] - 0.11)) | ends
    sh = solid('Shirt', F.top, (-0.3, -0.16, 1.0), (0.3, 0.16, 1.86), 0.0065, 1450, girl, dense=(edges, 650))
    # the inside of the sleeves and of the hem (seen from below) a shade darker
    def inside(p, n):
        if any(n @ f.dir > 0.6 and (p - f.end) @ f.dir > -0.006 for f in F.sleeves): return True
        return n[2] < -0.6 and p[2] < F.hem_fn(p[None])[0] + 0.006
    parts.append(Part(sh, _two_tone(F.top, top, shade(top, 0.72), inside, girl), 1, bind_loose_shirt(body, girl)))
    parts.append(Part(_shirt_collar(F, girl), top, 1, bind_loose_shirt(body, girl)))
    tr = solid('Trousers', F.trousers, (-0.23, -0.15, 0.04), (0.23, 0.16, F.trousers_top + 0.02), 0.0062, 1800, girl)
    def hem_in(p, n): return n[2] < -0.6 and p[2] < 0.14
    parts.append(Part(tr, _two_tone(F.trousers, leg, shade(leg, 0.6), hem_in, girl), 2, bind_trousers(body, girl)))
    return parts


def _two_tone(f, col, col_in, test, girl):
    """Per-corner colour: col_in on the faces whose centre (teen space) and field normal pass
    test(p, n) (the inside of a sleeve or a hem), col elsewhere."""
    memo = {}
    def c(co, cen):
        key = (round(cen[0], 5), round(cen[1], 5), round(cen[2], 5))
        if key not in memo:
            p = np.array(grow(cen, girl))
            n = unit(grad(f, p[None])[0])
            memo[key] = col_in if test(p, n) else col
        return memo[key]
    return c


def _shirt_collar(F, girl):
    """An open shirt collar: a band lying on the shirt round the neckline, standing up a little
    round the back of the neck and widening into two points at the front of the V. A (round the
    neck) x (across) grid placed on the shirt's surface, then given a thickness."""
    base = lambda p: F.top_raw(p, 0.0)
    a0 = 0.03
    u = np.linspace(0, 1, 46)
    u = u + 0.06 * np.sin(2 * math.pi * u)               # a little denser toward the front ends
    TH = a0 + u * (2 * math.pi - 2 * a0)                  # from the front (his left) round the back
    ax = np.array([0, F.nax[1], 0.0])
    N = []
    for th in TH:
        dh = np.array([math.sin(th), -math.cos(th), 0.0])
        z = float(F.zcut_th(np.array([th]))[0])
        rs = np.linspace(0.3, 0.0, 600)
        P = ax + np.array([0, 0, z]) + dh[None] * rs[:, None]
        k = int(np.argmax(base(P) < 0))
        lo, hi = rs[k], rs[max(k - 1, 0)]
        for _ in range(24):
            m = 0.5 * (lo + hi)
            if base((ax + np.array([0, 0, z]) + dh * m)[None])[0] < 0: lo = m
            else: hi = m
        N.append(ax + np.array([0, 0, z]) + dh * lo)
    N = np.array(N)
    T = np.gradient(N, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    g = grad(base, N); g /= np.linalg.norm(g, axis=1)[:, None]
    D = np.cross(g, T); D /= np.linalg.norm(D, axis=1)[:, None]
    away = np.stack([np.sin(TH), -np.cos(TH), np.full(len(TH), -1.2)], 1)
    D *= np.sign((D * away).sum(1))[:, None]
    a = np.abs(_wrap(TH))
    wid = 0.031 + 0.004 * sstep(2.4, 1.4, a) + 0.02 * sstep(1.0, a0, a) ** 1.5    # the points at the front
    stand = 0.013 * sstep(1.1, 2.2, a)                                            # stands up round the back
    nv = 5
    G = np.array([[N[i] + D[i] * (-stand[i] + (wid[i] + stand[i]) * k / (nv - 1)) for k in range(nv)] for i in range(len(TH))])
    G = G.reshape(-1, 3)
    for _ in range(6):
        gg = grad(base, G); gg /= np.linalg.norm(gg, axis=1)[:, None]
        G = G - gg * (base(G) - 0.0042)[:, None]
    faces = []
    for i in range(len(TH) - 1):
        for k in range(nv - 1):
            faces.append((i * nv + k, i * nv + k + 1, (i + 1) * nv + k + 1, (i + 1) * nv + k))
    o = mesh_object('Collar', G, faces, None)
    me = o.data; me.update()
    mid = me.polygons[len(faces) // 2]
    if (grad(base, np.array(mid.center)[None])[0] @ np.array(mid.normal)) < 0:
        for poly in me.polygons: poly.flip()
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.0034; so.offset = -1; so.use_rim = True; so.use_even_offset = True
    apply_mods(o); TB.to_base(o, girl); smooth(o)
    return o


def _satchel(F, body):
    """His school satchel: a soft rectangular bag with a deep flap and a clasp, on a cross-body
    strap over his left shoulder, hanging at the back of his right hip (Bag bone)."""
    girl = False; parts = []; BF = F.BF; j = BF.j
    c, h, r = _bag_dims(girl)
    col = BAG[girl]
    main = rbox(c, h, r)
    puff = ellipsoid(c + (0, 0.006, -0.01), (h[0] * 0.9, h[1] * 1.15, h[2] * 0.85))
    def bag(p): return smin(main(p), puff(p), 0.02)
    parts.append(Part(solid('Bag', bag, c - h - 0.03, c + h + 0.03, 0.005, 420, girl), col, 0, 'Bag'))
    # the flap: over the top and down the outer (+Y) face to a third of the way from the bottom
    zf = c[2] - h[2] * 0.36
    def flap(p):
        d = smax(bag(p) - 0.0045, zf - p[:, 2], 0.004)
        return smax(d, (c[1] - h[1] * 0.2) - p[:, 1], 0.004)
    parts.append(Part(solid('BagFlap', flap, c - h - 0.03, c + h + 0.03, 0.0038, 520, girl), shade(col, 0.86), 0, 'Bag'))
    # the clasp on the flap's edge
    cp = np.array([c[0], c[1] + h[1] + 0.006, zf + 0.012])
    def clasp(p): return smax(rbox(cp, (0.017, 0.02, 0.015), 0.004)(p), flap(p) - 0.0032, 0.002)
    parts.append(Part(solid('Clasp', clasp, cp - 0.04, cp + 0.04, 0.0022, 90, girl), (0.83, 0.62, 0.27, 1), 0, 'Bag'))
    # the strap: from the bag's right end round his right side, across the chest to the left
    # shoulder, then down his back to the bag's left end; lying on the shirt
    zt = c[2] + h[2]
    ctrl = [(c[0] - h[0] + 0.012, c[1] - 0.004, zt - 0.03), (c[0] - h[0] - 0.004, c[1] - 0.03, zt + 0.02),
            (-0.18, 0.06, 1.24), (-0.172, -0.025, 1.31), (-0.125, -0.098, 1.40), (-0.045, -0.128, 1.5),
            (0.035, -0.125, 1.6), (0.085, -0.075, 1.7), (0.1, -0.005, 1.765), (0.094, 0.07, 1.72),
            (0.075, 0.118, 1.6), (0.055, 0.13, 1.45), (0.04, 0.13, 1.3), (c[0] + h[0] - 0.035, c[1] - 0.02, zt + 0.02),
            (c[0] + h[0] - 0.02, c[1] - 0.004, zt - 0.03)]
    pts = catmull(ctrl, 70)
    thick, half_w = 0.0042, 0.016
    wear = lambda p: F.top_raw(p)
    inner = (bag(pts) > 0.006)[:, None] * 1.0
    for it in range(8):
        g = grad(wear, pts); g /= np.linalg.norm(g, axis=1)[:, None]
        tgt = pts - g * (wear(pts) - (thick + 0.003))[:, None]
        pts = pts * (1 - inner) + tgt * inner
        sm = pts.copy(); sm[1:-1] = (pts[:-2] + pts[1:-1] * 2 + pts[2:]) / 4
        pts = sm
    g = grad(wear, pts); g /= np.linalg.norm(g, axis=1)[:, None]
    t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    g = g - t * (g * t).sum(1)[:, None]; g /= np.linalg.norm(g, axis=1)[:, None]
    so = tube('BagStrap', pts, g, np.cross(g, t), rrect_profile(thick, half_w, 6), girl, False)
    parts.append(Part(so, shade(col, 0.62), 0, bind_with_bag(body, girl)))
    return parts


def _socks(F, girl):
    parts = []
    for n in 'LR':
        x = F.BF.j['ankle' + n][0]
        so = solid('Sock' + n, F.socks[n], (x - 0.075, -0.07, 0.03), (x + 0.075, 0.1, F.sock_top + 0.02), 0.0045,
                   380 if girl else 260, girl, False)
        parts.append(Part(so, SOCK, 0))
    return parts


def _plan_outline(upper, n, zs, c=(0.0, -0.04)):
    """The shoe upper's outline seen from below (the widest of its slices at heights zs), in the
    shoe's own frame: (n, 2) points counter-clockwise from the toe, and their outward normals."""
    Rz, o = upper.Rz, upper.o
    th = np.arange(n) / n * 2 * math.pi
    D = np.stack([np.sin(th), -np.cos(th)], 1)
    rs = np.linspace(0.22, 0.0, 440)
    R = np.zeros(n)
    for z in zs:
        L = np.array(c)[None, None, :] + D[:, None, :] * rs[None, :, None]
        P = np.concatenate([L, np.full(L.shape[:2] + (1,), z)], 2).reshape(-1, 3)
        Fv = upper(P @ Rz.T + o).reshape(n, len(rs))
        R = np.maximum(R, rs[np.argmax(Fv < 0, 1)])
    for _ in range(2): R = (np.roll(R, 1) + 2 * R + np.roll(R, -1)) / 4
    P = np.array(c) + D * R[:, None]
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    N = np.stack([T[:, 1], -T[:, 0]], 1); N /= np.linalg.norm(N, axis=1)[:, None]
    N *= np.sign(((P - np.array(c)) * N).sum(1))[:, None]
    return P, N


def _sole(name, upper, zbot, ztop, off, girl, n=40, zs=(0.03, 0.04, 0.05)):
    """A crisp sole: the upper's footprint grown by `off`, extruded from zbot(y) to ztop(y) (shoe
    frame), with small bevels; flat-shaded caps (hard edges) and a smooth wall."""
    Rz, o = upper.Rz, upper.o
    P, N = _plan_outline(upper, n, zs)
    P = P + N * off
    rows = [(-0.0035, 0, 0.0), (0.0, 0, 0.003), (0.0, 1, -0.0025), (-0.0025, 1, 0.0)]
    verts = []
    for ins, which, dz in rows:
        Q = P + N * ins
        z = (zbot(Q[:, 1]) if which == 0 else ztop(Q[:, 1])) + dz
        L = np.concatenate([Q, z[:, None]], 1)
        verts += list(L @ Rz.T + o)
    faces = []
    for r in range(len(rows) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            faces.append((r * n + i, r * n + i2, (r + 1) * n + i2, (r + 1) * n + i))
    faces.append(tuple(range(n))[::-1]); faces.append(tuple((len(rows) - 1) * n + i for i in range(n)))
    ob = outward(mesh_object(name, verts, faces, girl))
    bm = bmesh.new(); bm.from_mesh(ob.data)
    caps = [f for f in bm.faces if len(f.verts) > 4]
    for f in caps:
        for e in f.edges: e.smooth = False
    bmesh.ops.triangulate(bm, faces=caps, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return ob


def _shoes(F, girl):
    parts = []; BF = F.BF
    for n, s in (('L', 1), ('R', -1)):
        upper = F.shoes[n]; Rz, o = upper.Rz, upper.o; an = BF.j['ankle' + n]
        def L(p, Rz=Rz, o=o): return (p - o) @ Rz
        box = (an[0] - 0.08, -0.22, -0.005), (an[0] + 0.08, 0.11, 0.12)
        if girl:
            def strap(p, L=L, upper=upper):
                q = L(p)
                d = smax(upper(p) - 0.003, np.abs(q[:, 1] + 0.06) - 0.012, 0.003)
                return smax(d, 0.038 - q[:, 2], 0.004)
            shoe_c, sole_c, strap_c = (0.45, 0.27, 0.17, 1), (0.2, 0.125, 0.09, 1), (0.34, 0.2, 0.13, 1)
            sole = _sole('Sole' + n, upper, lambda y: 0.005 * sstep(-0.12, -0.18, y),
                         lambda y: 0.0095 + 0.0095 * sstep(-0.012, 0.012, y) + 0.004 * sstep(-0.12, -0.18, y),
                         0.0028, girl, 30, (0.02, 0.03, 0.04))
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0042, 340, girl, False), shoe_c, 0, 'Foot.' + n),
                      Part(sole, sole_c, 0, 'Foot.' + n),
                      Part(solid('ShoeStrap' + n, strap, *box, 0.0035, 110, girl, False), strap_c, 0, 'Foot.' + n)]
            col_c = (0.38, 0.23, 0.15, 1)
        else:
            def cap(p, L=L, upper=upper):
                # the white rubber toe cap, its top edge sweeping up toward the tip
                q = L(p)
                d = smax(upper(p) - 0.0028, q[:, 1] + 0.122, 0.008)
                return smax(d, q[:, 2] - (0.036 + 0.3 * np.maximum(-0.122 - q[:, 1], 0)), 0.006)
            def laces(p, L=L, upper=upper):
                q = L(p)
                bars = np.abs(((q[:, 1] + 0.1) % 0.021) - 0.0105) - 0.0042
                d = smax(upper(p) - 0.0035, bars, 0.002)
                d = smax(d, np.abs(q[:, 0]) - 0.021, 0.003)
                d = smax(d, np.abs(q[:, 1] + 0.05) - 0.04, 0.003)
                return smax(d, 0.06 - q[:, 2], 0.003)
            # white canvas sneakers on a cool grey sole (so they part from a pale pavement)
            upper_c, sole_c = (0.86, 0.87, 0.9, 1), (0.3, 0.32, 0.4, 1)
            spring = lambda y: 0.016 * sstep(-0.11, -0.19, y)
            sole = _sole('Sole' + n, upper, spring, lambda y: 0.0195 + 0.75 * spring(y), 0.003, girl, 30, (0.03, 0.042, 0.054))
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0045, 330, girl, False), upper_c, 0, 'Foot.' + n),
                      Part(sole, sole_c, 0, 'Foot.' + n),
                      Part(solid('ToeCap' + n, cap, *box, 0.0032, 150, girl, False), WHITE, 0, 'Foot.' + n),
                      Part(solid('Laces' + n, laces, *box, 0.0028, 120, girl, False), WHITE, 0, 'Foot.' + n)]
            col_c = (0.7, 0.1, 0.08, 1)
        # the collar of the opening: a padded rim right where the sock enters the shoe
        sock = lambda p, sn=BF.shin[n]: sn(p) - 0.0035
        P, Dr = _opening(sock, upper, an, 20)
        Vz = np.cross(Dr, np.roll(P, -1, 0) - np.roll(P, 1, 0)); Vz /= np.linalg.norm(Vz, axis=1)[:, None]
        Vz *= np.sign(Vz[:, 2:3] + 1e-9)
        parts.append(Part(tube('ShoeCollar' + n, P + Dr * 0.0035 + Vz * 0.0028, Dr, Vz, ellipse_profile(0.0058, 0.0072, 5), girl),
                          col_c, 0, 'Foot.' + n))
    return parts


def _opening(sock, upper, an, n):
    """Where the sock leaves the shoe: for each direction round the ankle, the highest point
    of the sock's surface still inside the shoe."""
    th = np.arange(n) / n * 2 * math.pi
    D = np.stack([np.sin(th), -np.cos(th), np.zeros(n)], 1)
    zs = np.linspace(0.16, 0.03, 140)
    pts = np.zeros((n, 3))
    for i in range(n):
        best = None
        for z in zs:
            rs = np.linspace(0.08, 0.0, 120)
            Q = np.array([an[0], an[1], z]) + D[i] * rs[:, None]
            k = int(np.argmax(sock(Q) < 0)); q = Q[k]
            if upper(q[None] + D[i] * 0.0015)[0] < 0: best = q; break
        pts[i] = best if best is not None else np.array([an[0], an[1], 0.05]) + D[i] * 0.03
    # smooth the rim a little
    for _ in range(2): pts = (np.roll(pts, 1, 0) + pts * 2 + np.roll(pts, -1, 0)) / 4
    c = pts.mean(0); Dr = pts - c; Dr[:, 2] = 0; Dr /= np.linalg.norm(Dr, axis=1)[:, None]
    return pts, Dr


def _backpack(F, body, girl):
    parts = []; BF = F.BF; j = BF.j
    c, h, r = _bag_dims(girl)
    col = BAG[girl]
    main = rbox(c, h, r)
    puff = ellipsoid(c + (0, 0.02, -0.005), (h[0] * 0.85, h[1] * 1.0, h[2] * 0.9))
    topround = ellipsoid(c + (0, 0, h[2] - 0.07), (h[0], h[1] + 0.002, 0.11))
    def bag(p):
        d = smin(main(p), puff(p), 0.03)
        return smax(d, smin(topround(p), p[:, 2] - (c[2] + h[2] - 0.06), 0.02), 0.02)
    parts.append(Part(solid('Bag', bag, c - h - 0.03, c + h + 0.03, 0.006, 560, girl), col, 0, 'Bag'))
    # front pocket (the outer face is +Y)
    fy = c[1] + h[1]
    pc = np.array([0, fy + 0.012, c[2] - h[2] * 0.42])
    pocket = rbox(pc, (h[0] * 0.78, 0.028, h[2] * 0.46), 0.035)
    def pk(p): return smax(pocket(p), -bag(p) - 0.004, 0.01)
    parts.append(Part(solid('BagPocket', pk, pc - (0.15, 0.06, 0.12), pc + (0.15, 0.06, 0.12), 0.0045, 300, girl), shade(col, 0.9), 0, 'Bag'))
    # the pocket's zip seam and the bag's piping: outlines sampled densely, then resampled with
    # extra points on the rounded corners (smooth corners, no octagon look)
    P, D = ring_even(pocket, pc, (0, 1, 0), 34)
    V = np.tile(np.array([0, 1.0, 0]), (len(P), 1))
    parts.append(Part(tube('Zip', P + V * 0.026, D, V, ellipse_profile(0.003, 0.003, 3), girl), shade(col, 0.62), 0, 'Bag'))
    P, D = ring_even(bag, c + (0, h[1] * 0.35, 0), (0, 1, 0), 40)
    V = np.tile(np.array([0, 1.0, 0]), (len(P), 1))
    parts.append(Part(tube('Piping', P, D, V, ellipse_profile(0.0042, 0.0042, 3), girl), shade(col, 0.72), 0, 'Bag'))
    # grab handle
    ht = c[2] + h[2]
    pts = catmull([(-0.035, c[1] - 0.005, ht - 0.012), (-0.022, c[1] - 0.005, ht + 0.01), (0.022, c[1] - 0.005, ht + 0.01),
                   (0.035, c[1] - 0.005, ht - 0.012)], 14)
    t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    Vv = np.tile(np.array([0, 1.0, 0]), (len(pts), 1)); U = np.cross(Vv, t)
    parts.append(Part(tube('Handle', pts, U, Vv, ellipse_profile(0.005, 0.007, 6), girl, False), shade(col, 0.72), 0, 'Bag'))
    # shoulder straps, lying on the top over each shoulder
    off = 0.011 if girl else 0.016
    def wear(p):
        d = smin(BF.torso(p) - off, BF.neck(p) - off, 0.03)
        for n in 'LR':
            arm = np.maximum(BF.uarm[n](p) - off - 0.01, (j['shoulder' + n][2] - 0.015) - p[:, 2])
            d = smin(d, arm, 0.03)
        return d
    for n, s in (('L', 1), ('R', -1)):
        sh = j['shoulder' + n]
        zt = c[2] + h[2]; zb = c[2] - h[2]
        # over the shoulder, a short run down the front, then under the arm (close to the ribs and
        # behind the arm's swing) to the bag's bottom corner
        if girl:
            ctrl = [(0.062, c[1] - 0.01, zt - 0.03), (0.068, 0.085, zt + 0.03), (0.082, 0.035, sh[2] + 0.06),
                    (0.09, -0.04, sh[2] + 0.025), (0.097, -0.079, sh[2] - 0.05), (0.104, -0.068, sh[2] - 0.11),
                    (0.108, -0.02, sh[2] - 0.165), (0.11, 0.04, zb + 0.08), (0.11, c[1] - 0.02, zb + 0.045)]
        else:
            ctrl = [(0.062, c[1] - 0.01, zt - 0.03), (0.068, 0.085, zt + 0.03), (0.082, 0.035, sh[2] + 0.06),
                    (0.09, -0.04, sh[2] + 0.025), (0.096, -0.082, sh[2] - 0.07), (0.104, -0.072, sh[2] - 0.15),
                    (0.108, -0.01, sh[2] - 0.215), (0.11, 0.045, zb + 0.08), (0.112, c[1] - 0.02, zb + 0.045)]
        pts = catmull([(s * x, y, z) for x, y, z in ctrl], 40)
        thick, half_w = 0.0045, (0.02 if girl else 0.022)
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
        so = tube('BagStrap' + n, pts, g, bvec, rrect_profile(thick, half_w, 6), girl, False)
        parts.append(Part(so, shade(col, 0.84), 0, bind_with_bag(body, girl)))
    return parts
