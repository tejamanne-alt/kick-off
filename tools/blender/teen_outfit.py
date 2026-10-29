# The teens' clothes, shoes and backpacks. Base space: see teen_lib.
#
# Like the body (teen_body), everything is designed in teen space: the clothes are distance
# fields offset from the body field (so they sit on it everywhere), the girl's pleated skirt is
# a lofted ring mesh, and straps, collars and ribbed bands are swept along curves found on the
# clothes' surfaces. Each piece is mapped back to base space with teen_body.ungrow.
import bpy, bmesh, math
import numpy as np
from mathutils import Vector
from teen_lib import Part, activate, apply_mods, smooth, shade
import teen_body as TB
from teen_body import (smin, smax, round_cone, ellipsoid, rbox, frame, catmull,
                       sdf_object, mesh_object, grad, field, tj, grow, ungrow)


# ----------------------------------------------------------------------------------------------
# Colours. The game recolours part 1 (top) and part 2 (legwear) from these defaults.
def palette(girl):
    if girl:
        return {'skin': (1.0, 0.88, 0.8, 1), 'top': (0.57, 0.76, 0.93, 1), 'legwear': (0.2, 0.24, 0.42, 1)}
    return {'skin': (0.96, 0.82, 0.7, 1), 'top': (0.29, 0.57, 0.42, 1), 'legwear': (0.78, 0.68, 0.5, 1)}


WHITE = (0.97, 0.97, 0.96, 1)
BAG = {True: (0.93, 0.73, 0.3, 1), False: (0.18, 0.24, 0.45, 1)}


def skin_color(girl):
    """The body's colour (bare skin everywhere; socks are their own pieces)."""
    return palette(girl)['skin']


def _bag_dims(girl):
    """Backpack box in teen space: centre, half sizes, corner radius. Its top (handle included)
    stays below base z 1.17 (teen 1.6475 girl, 1.7258 boy) so the girl's ponytail never meets it."""
    if girl:
        return np.array([0, 0.153, 1.438]), np.array([0.132, 0.055, 0.166]), 0.05
    return np.array([0, 0.158, 1.515]), np.array([0.142, 0.058, 0.175]), 0.05


def bag_bone(girl):
    """The Bag bone (base space): head at the top edge of the bag, tail toward its bottom."""
    c, h, r = _bag_dims(girl)
    top = c + (0, 0, h[2]); bot = c - (0, 0, h[2] * 0.6)
    return tuple(ungrow(Vector(top), girl)), tuple(ungrow(Vector(bot), girl))


# ----------------------------------------------------------------------------------------------
# Helpers
def unit(v): v = np.asarray(v, dtype=np.float64); return v / np.linalg.norm(v)


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


def solid(name, f, lo, hi, h, tris, girl, symmetric=True):
    return outward(sdf_object(name, f, lo, hi, h, tris=tris, girl=girl, symmetric=symmetric))


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
    """Copy the body's weights, then hand the ends near the backpack to the Bag bone."""
    c, h, r = _bag_dims(girl)
    bag = rbox(c, h, r)
    def bind(o, rig):
        _transfer(o, body)
        W = _weights(o)
        V = np.array([v.co for v in o.data.vertices])
        k = 1 - sstep(0.0, 0.08, bag(V))
        for w, kk in zip(W, k):
            for n in list(w): w[n] *= (1 - kk)
            w['Bag'] = w.get('Bag', 0) + kk
        _set_weights(o, W); _attach(o, rig)
    return bind


def bind_damp_legs(body, keep=0.4):
    """Copy the body's weights but damp the thighs' pull (a shirt hem near the hips)."""
    def bind(o, rig):
        _transfer(o, body)
        W = _weights(o)
        for w in W:
            for n in list(w):
                if n.startswith('UpperLeg') or n.startswith('LowerLeg'):
                    w['Hips'] = w.get('Hips', 0) + w[n] * (1 - keep); w[n] *= keep
        _set_weights(o, W); _attach(o, rig)
    return bind


def bind_skirt(girl):
    """The pleated skirt follows the thighs below the hips (so they never poke through): the hem
    turns with the nearer thigh, the centre front and back share both legs and the hips."""
    j = tj(girl)
    zt, zb = j['hipL'][2] + 0.07, j['hipL'][2] - 0.12
    def bind(o, rig):
        W = []
        for v in o.data.vertices:
            x, y, z = v.co
            down = float(sstep(zt, zb, z))
            side = float(sstep(-0.03, 0.03, x))
            centre = 1 - abs(2 * side - 1)
            fb = 0.92 if y < 0 else 0.8
            legs = down * fb * (1 - 0.25 * centre)
            W.append({'Hips': 1 - legs, 'UpperLeg.L': legs * side, 'UpperLeg.R': legs * (1 - side)})
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
            off = 0.011 + 0.004 * sstep(1.40, 1.35, z) * sstep(1.315, 1.34, z) - 0.005 * sstep(1.33, 1.31, z) \
                - 0.006 * sstep(0.11, 0.075, rho) * sstep(1.6, 1.66, z)
            d = smin(torso(p) - off, neck(p) - neck_off, 0.025)
            for f in F.sleeves: d = smin(d, f(p), 0.03)
            return d
        F.hem = 1.248; F.hole = 0.058
    else:
        def sleeve(n, s):
            sh, el = j['shoulder' + n], j['elbow' + n]
            adir = unit(el - sh)
            end = sh + adir * 0.165
            cone = round_cone(sh + adir * 0.03, end, BF.r['uarm'][0] + 0.013, BF.r['uarm'][0] + 0.008)
            def raw(p): return smin(BF.uarm[n](p) - 0.012, cone(p), 0.015)
            def f(p): return smax(raw(p), (p - end) @ adir, 0.004)
            f.raw = raw; f.end = end; f.dir = adir
            return f
        F.sleeves = [sleeve('L', 1), sleeve('R', -1)]
        def top_raw(p, neck_off=0.004):
            z = p[:, 2]; rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            off = 0.015 + 0.012 * sstep(1.32, 1.14, z) - 0.009 * sstep(0.12, 0.08, rho) * sstep(1.66, 1.73, z) \
                + 0.0025 * sstep(1.185, 1.179, z)        # the stitched hem
            d = smin(torso(p) - off, neck(p) - neck_off, 0.025)
            for f in F.sleeves: d = smin(d, f(p), 0.03)
            return d
        F.hem = 1.155; F.hole = 0.064
        # crew neck: an elliptical opening, a little forward of the neck so it dips at the front
        F.crew = (0.074, 0.073, F.nax[1] - 0.008)
        zh = 0.655; F.shorts_hem = zh
        def leg_tube(n):
            th = BF.thigh[n]
            def f(p):
                z = p[:, 2]
                ease = 0.012 + 0.016 * sstep(1.0, 0.72, z) + 0.0055 * sstep(zh + 0.039, zh + 0.033, z)
                return th(p) - ease
            return f
        tubes = [leg_tube('L'), leg_tube('R')]
        def shorts_raw(p):
            return smin(torso(p) - 0.012, smin(tubes[0](p), tubes[1](p), 0.008), 0.035)
        def shorts(p):
            d = smax(shorts_raw(p), p[:, 2] - 1.345, 0.004)
            return smax(d, zh - p[:, 2], 0.004)
        F.shorts_raw, F.shorts = shorts_raw, shorts
    def top(p):
        d = smax(top_raw(p), F.hem - p[:, 2], 0.005)
        if girl:
            rho = np.hypot(p[:, 0], p[:, 1] - F.nax[1])
            hole = np.maximum(rho - F.hole, F.zn(p[:, 1]) - p[:, 2])
        else:
            rx, ry, cy = F.crew
            hole = np.maximum((np.hypot(p[:, 0] / rx, (p[:, 1] - cy) / ry) - 1) * 0.07, (j['neck0'][2] - 0.07) - p[:, 2])
        return smax(d, -hole, 0.004)
    F.top_raw, F.top = top_raw, top
    # socks
    F.sock_top = 0.497 if girl else 0.175
    def sock(n):
        sn = BF.shin[n]; t = F.sock_top
        def f(p):
            z = p[:, 2]
            d = sn(p) - 0.0035 - 0.0028 * sstep(t - 0.034, t - 0.028, z)
            d = smax(d, z - t, 0.003)
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
        if girl:
            parts = (ellipsoid((0, 0.036, 0.046), (0.041, 0.046, 0.043)), ellipsoid((0, -0.04, 0.038), (0.045, 0.08, 0.038)),
                     ellipsoid((0, -0.112, 0.03), (0.042, 0.066, 0.027)))
            zcut = 0.012
        else:
            parts = (ellipsoid((0, 0.038, 0.056), (0.045, 0.05, 0.05)), ellipsoid((0, -0.045, 0.05), (0.05, 0.09, 0.045)),
                     ellipsoid((0, -0.118, 0.04), (0.049, 0.068, 0.035)))
            zcut = 0.018
        def upper(p, Rz=Rz, o=o, parts=parts, zcut=zcut):
            q = (p - o) @ Rz
            d = smin(smin(parts[0](q), parts[1](q), 0.03), parts[2](q), 0.03)
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
            d = np.maximum(d, -F.shorts(p))
            semi = np.zeros(len(p), bool)
        sockd = np.maximum(-F.socks['L'](p), -F.socks['R'](p))
        semi |= sockd > 0.002
        return d, semi & (d < 0.006), sockd
    return f


# ----------------------------------------------------------------------------------------------
def build_outfit(girl, body):
    F = fields(girl)
    parts = _girl_clothes(F, body) if girl else _boy_clothes(F, body)
    parts += _socks(F, girl)
    parts += _shoes(F, girl)
    parts += _backpack(F, body, girl)
    tot = sum(tris_of(p.obj) for p in parts)
    print('outfit tris', tot, 'body tris', tris_of(body), 'sum', tot + tris_of(body))
    bag_top = max(max((p.obj.matrix_world @ v.co).z for v in p.obj.data.vertices) for p in parts if p.bind == 'Bag')
    print('backpack top (base z)', round(bag_top, 4))
    return parts


def _girl_clothes(F, body):
    girl = True; BF = F.BF
    pal = palette(girl); top, leg = pal['top'], pal['legwear']
    parts = []
    bl = solid('Blouse', F.top, (-0.25, -0.13, 1.22), (0.25, 0.13, 1.78), 0.006, 1450, girl)
    parts.append(Part(bl, top, 1, bind_damp_legs(body, 0.0)))
    for f, n in zip(F.sleeves, 'LR'):
        b = band(f.raw, f.end - f.dir * 0.005, f.dir, 0.0055, 0.0075, girl, 'Cuff' + n, 20, ref=(0, 0, 1), m=6)
        parts.append(Part(b, shade(top, 0.96), 1))
    parts.append(Part(_peter_pan(F, girl), WHITE, 0))
    for z in (1.555, 1.47, 1.385):    # buttons down the front
        p, nrm = surface_point(F.top, (0, -0.3, z), (0, 1, 0))
        parts.append(Part(blob('Button', p + nrm * 0.0015, nrm, (0.0072, 0.0072, 0.0032), girl, 8, 4), (0.99, 0.98, 0.95, 1), 0))
    parts.append(_skirt(F, girl, leg))
    return parts


def _peter_pan(F, girl):
    """A rounded Peter Pan collar: two lobes lying on the blouse round the neckline, meeting at
    the front. A (round the neck) x (across) grid projected onto the blouse, then given a
    thickness."""
    BF = F.BF
    base = lambda p: F.top_raw(p, 0.0)
    thn, W, Rr = 0.11, 0.05, 0.036
    ts = np.linspace(0, 1, 40)
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
    BF = F.BF
    lower = lambda p: smin(BF.torso(p), smin(BF.leg_full('L')(p), BF.leg_full('R')(p), 0.01), 0.06)
    NP = 8                       # knife pleats per side, mirrored about the centre front
    ring = []
    for k in range(NP):      # extra columns at the centre front and back let the legs' pull blend smoothly
        sub = [0.0, 0.3, 0.6, 0.9] if k in (0, NP - 1) else [0.0, 0.9]
        ring += [(math.pi * (k + s_) / NP, s_) for s_ in sub]
    ring += [(math.pi, 0.0)]
    ring = ring + [(-a, ph) for a, ph in reversed(ring[1:-1])]
    A = np.array([a for a, _ in ring]); PH = np.array([ph for _, ph in ring])
    M = len(ring)
    zw_top, zw_bot = 1.325, 1.258
    zs = [zw_top + 0.0035, zw_top, zw_bot, zw_bot - 0.006, 1.19, 1.12, 1.03, 0.93, 0.83, 0.74, 0.672]
    zf = 1.22; flare = math.tan(math.radians(7.5))
    D = np.stack([np.sin(A), -np.cos(A), np.zeros(M)], 1)
    rings = []; prev = None; band_r = None
    for zi, z in enumerate(zs):
        cy = BF.torso_core.prof(np.array([z]))[2][0] if z > 1.03 else 0.008
        cen = np.array([0, cy, z])
        rs = np.linspace(0.32, 0.0, 320)
        P = cen + D[:, None, :] * rs[None, :, None]
        Fv = lower(P.reshape(-1, 3)).reshape(M, len(rs))
        hit = (Fv < 0).any(1)
        rb = np.where(hit, rs[np.argmax(Fv < 0, 1)], 0.0)
        if z >= zw_bot - 1e-6:                     # the waistband, over the tucked-in blouse
            r = rb + 0.0245 - (0.003 if zi == 0 else 0)
            band_r = r if band_r is None else np.maximum(band_r, r)
        else:
            r = np.maximum(rb + 0.0125, band_r - 0.0045)
            if prev is not None: r = np.maximum(r, prev)
            prev = r.copy()
        rr = r + (flare * (zf - z) if z < zf else 0)
        depth = 0.018 * float(sstep(1.13, 1.02, z))
        rr = rr + depth * PH / 0.9
        rings.append(cen + D * rr[:, None])
    verts = np.concatenate(rings); faces = []
    for i in range(len(zs) - 1):
        for k in range(M):
            k2 = (k + 1) % M
            faces.append((i * M + k, i * M + k2, (i + 1) * M + k2, (i + 1) * M + k))
    o = mesh_object('Skirt', verts, faces, None)
    me = o.data; mid = me.polygons[len(faces) // 2]
    if np.array(mid.normal) @ (np.array(mid.center) - np.array([0, 0.008, mid.center[2]])) < 0:
        for poly in me.polygons: poly.flip()
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.0055; so.offset = -1; so.use_rim = True
    so.use_even_offset = True
    apply_mods(o); TB.to_base(o, girl); smooth(o)
    dark = shade(leg_col, 0.72); mid = shade(leg_col, 0.9)
    def col(co, cen):
        p = grow(cen, girl)
        if p.z > zw_bot - 0.002: return shade(leg_col, 1.06)
        a = math.atan2(p.x, -(p.y - 0.008))
        u = (abs(a) / math.pi * NP) % 1.0
        if p.z < 1.10 and u > 0.9: return dark
        q = grow(co, girl); uq = (abs(math.atan2(q.x, -(q.y - 0.008))) / math.pi * NP) % 1.0
        return mid if (p.z < 1.10 and uq > 0.6) else leg_col
    return Part(o, col, 2, bind_skirt(girl))


def _boy_clothes(F, body):
    girl = False; BF = F.BF; j = BF.j
    pal = palette(girl); top, leg = pal['top'], pal['legwear']
    parts = []
    sh = solid('Shirt', F.top, (-0.27, -0.14, 1.12), (0.27, 0.14, 1.86), 0.0065, 1700, girl)
    parts.append(Part(sh, top, 1, bind_damp_legs(body, 0.5)))
    rx, ry, cy = F.crew
    NB = 32
    th = np.arange(NB) / NB * 2 * math.pi
    D = np.stack([np.sin(th), -np.cos(th), np.zeros(NB)], 1)
    E = np.stack([rx * np.sin(th), cy - ry * np.cos(th), np.zeros(NB)], 1)
    zs = np.linspace(j['neck0'][2] + 0.025, j['neck0'][2] - 0.07, 200)
    P = np.zeros((NB, 3))
    for i in range(NB):
        Q = np.repeat(E[i:i + 1], len(zs), 0); Q[:, 2] = zs
        k = int(np.argmax(F.top_raw(Q + D[i] * 0.004) < 0)); P[i] = Q[k]
    for _ in range(2): P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4
    Nr = np.stack([np.sin(th) / rx, -np.cos(th) / ry, np.zeros(NB)], 1); Nr /= np.linalg.norm(Nr, axis=1)[:, None]
    up = np.tile(np.array([0, 0, 1.0]), (NB, 1))
    nb = tube('NeckBand', P + Nr * 0.001 + up * 0.003, Nr, up, ellipse_profile(0.0075, 0.0105, 6), girl)
    parts.append(Part(nb, WHITE, 0))
    for f, n in zip(F.sleeves, 'LR'):
        b = band(f.raw, f.end - f.dir * 0.0085, f.dir, 0.005, 0.0095, girl, 'SleeveBand' + n, 20, ref=(0, 0, 1), lift=0.001, m=6)
        parts.append(Part(b, WHITE, 0))
    so = solid('Shorts', F.shorts, (-0.22, -0.14, 0.62), (0.22, 0.15, 1.36), 0.0065, 1450, girl)
    parts.append(Part(so, leg, 2))
    for n, s in (('L', 1), ('R', -1)):
        def pocket(p, s=s):
            return smax(F.shorts_raw(p) - 0.0045, rbox((s * 0.2, 0.004, 0.86), (0.08, 0.046, 0.065), 0.016)(p), 0.003)
        def flap(p, s=s):
            return smax(F.shorts_raw(p) - 0.0085, rbox((s * 0.2, 0.004, 0.925), (0.08, 0.05, 0.02), 0.01)(p), 0.003)
        x0 = s * 0.17
        lo = (min(x0, x0 + s * 0.09) - 0.02, -0.08, 0.78); hi = (max(x0, x0 + s * 0.09) + 0.02, 0.08, 0.96)
        parts.append(Part(solid('Pocket' + n, pocket, lo, hi, 0.004, 130, girl, False), shade(leg, 0.96), 2))
        parts.append(Part(solid('Flap' + n, flap, lo, hi, 0.004, 110, girl, False), shade(leg, 0.9), 2))
    return parts


def _socks(F, girl):
    parts = []
    for n in 'LR':
        x = F.BF.j['ankle' + n][0]
        so = solid('Sock' + n, F.socks[n], (x - 0.07, -0.07, 0.03), (x + 0.07, 0.09, F.sock_top + 0.02), 0.0045,
                   380 if girl else 280, girl, False)
        parts.append(Part(so, WHITE, 0))
    return parts


def _shoes(F, girl):
    parts = []; BF = F.BF
    for n, s in (('L', 1), ('R', -1)):
        upper = F.shoes[n]; Rz, o = upper.Rz, upper.o; an = BF.j['ankle' + n]
        def L(p, Rz=Rz, o=o): return (p - o) @ Rz
        def flat(p, z, upper=upper, Rz=Rz, o=o):
            q = (p - o) @ Rz; q[:, 2] = z
            return upper(q @ Rz.T + o)
        box = (an[0] - 0.08, -0.22, -0.005), (an[0] + 0.08, 0.11, 0.12)
        if girl:
            def sole(p, L=L, flat=flat):
                q = L(p)
                d = flat(p, 0.03) - 0.0035
                d = smax(d, q[:, 2] - np.where(q[:, 1] > 0.0, 0.024, 0.0135), 0.003)
                return smax(d, -q[:, 2], 0.002)
            def strap(p, L=L, upper=upper):
                q = L(p)
                d = smax(upper(p) - 0.003, np.abs(q[:, 1] + 0.058) - 0.012, 0.003)
                return smax(d, 0.042 - q[:, 2], 0.004)
            shoe_c, sole_c, strap_c = (0.45, 0.27, 0.17, 1), (0.24, 0.15, 0.11, 1), (0.34, 0.2, 0.13, 1)
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0042, 340, girl, False), shoe_c, 0, 'Foot.' + n),
                      Part(solid('Sole' + n, sole, *box, 0.0035, 160, girl, False), sole_c, 0, 'Foot.' + n),
                      Part(solid('ShoeStrap' + n, strap, *box, 0.0035, 110, girl, False), strap_c, 0, 'Foot.' + n)]
            col_c = (0.38, 0.23, 0.15, 1)
        else:
            def sole(p, L=L, flat=flat):
                q = L(p)
                d = flat(p, 0.034) - 0.0045
                spring = 0.012 * sstep(-0.13, -0.2, q[:, 1])
                d = smax(d, q[:, 2] - 0.026 - spring * 0.6, 0.004)
                return smax(d, spring - q[:, 2], 0.003)
            def cap(p, L=L, upper=upper):
                q = L(p)
                d = smax(upper(p) - 0.003, q[:, 1] + 0.136, 0.014)
                return smax(d, q[:, 2] - 0.05, 0.01)
            def laces(p, L=L, upper=upper):
                q = L(p)
                bars = np.abs(((q[:, 1] + 0.1) % 0.021) - 0.0105) - 0.0042
                d = smax(upper(p) - 0.0035, bars, 0.002)
                d = smax(d, np.abs(q[:, 0]) - 0.021, 0.003)
                d = smax(d, np.abs(q[:, 1] + 0.05) - 0.04, 0.003)
                return smax(d, 0.06 - q[:, 2], 0.003)
            red = (0.85, 0.22, 0.2, 1)
            parts += [Part(solid('Shoe' + n, upper, *box, 0.0045, 340, girl, False), red, 0, 'Foot.' + n),
                      Part(solid('Sole' + n, sole, *box, 0.0035, 220, girl, False), WHITE, 0, 'Foot.' + n),
                      Part(solid('ToeCap' + n, cap, *box, 0.0035, 140, girl, False), WHITE, 0, 'Foot.' + n),
                      Part(solid('Laces' + n, laces, *box, 0.0028, 130, girl, False), WHITE, 0, 'Foot.' + n)]
            col_c = shade(red, 0.8)
        # the collar of the opening: a padded rim right where the sock enters the shoe
        sock = lambda p, sn=BF.shin[n]: sn(p) - 0.0035
        P, Dr = _opening(sock, upper, an, 22)
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
    pocket = rbox(pc, (h[0] * 0.78, 0.028, h[2] * 0.46), 0.024)
    def pk(p): return smax(pocket(p), -bag(p) - 0.004, 0.01)
    parts.append(Part(solid('BagPocket', pk, pc - (0.15, 0.06, 0.12), pc + (0.15, 0.06, 0.12), 0.0045, 300, girl), shade(col, 0.9), 0, 'Bag'))
    # the pocket's zip seam and the bag's piping
    P, D = ring_on(pocket, pc, (0, 1, 0), 26, ref=(1, 0, 0))
    V = np.tile(np.array([0, 1.0, 0]), (26, 1))
    parts.append(Part(tube('Zip', P + V * 0.026, D, V, ellipse_profile(0.003, 0.003, 4), girl), shade(col, 0.62), 0, 'Bag'))
    P, D = ring_on(bag, c + (0, h[1] * 0.35, 0), (0, 1, 0), 34, ref=(1, 0, 0))
    V = np.tile(np.array([0, 1.0, 0]), (34, 1))
    parts.append(Part(tube('Piping', P, D, V, ellipse_profile(0.0042, 0.0042, 4), girl), shade(col, 0.72), 0, 'Bag'))
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
        ctrl = [(0.062, c[1] - 0.01, zt - 0.03), (0.068, 0.085, zt + 0.03), (0.082, 0.035, sh[2] + 0.06),
                (0.09, -0.04, sh[2] + 0.025), (0.096, -0.08, sh[2] - 0.07), (0.106, -0.075, sh[2] - 0.16),
                (0.12, -0.035, sh[2] - 0.23), (0.128, 0.04, zb + 0.09), (0.118, c[1] - 0.02, zb + 0.05)]
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
