# Architectural parts of the buildings kit (kit_buildings.py): wall frames, walls with openings
# (flat render, lap siding, ribbed cladding), windows, doors, canopies, pitched / shed / flat roofs,
# gutters and downpipes, and the small things that make a building lived in (lamps, AC units,
# meter boxes, planters, pots, laundry, awnings, shutters).
#
# Parts on a wall are modelled in the wall's own space: x along the wall (u), y up (v), z out of
# the wall (w), then placed with the wall frame's matrix.
from kit_buildings_geo import *


class WF:
    """A wall's frame: u along the wall (U), v up, w out of the wall (N = U x Z)."""
    def __init__(self, O, U, mp):
        self.O = Vector(O); self.U = Vector(U).normalized(); self.V = Vector((0, 0, 1))
        self.N = self.U.cross(self.V); self.mp = mp

    def P(self, u, v, w=0.0):
        return self.O + self.U * u + self.V * v + self.N * w

    @property
    def M(self):
        return basis(self.O, self.U, self.V, self.N)

    def ab(self, u, v):
        p = self.P(u, v)
        return (p.x, p.z) if abs(self.N.y) > 0.5 else (p.y, p.z)

    def off(self, w):
        return WF(self.P(0, 0, w), self.U, self.mp)


def frames(B):
    W, D = B.W, B.D
    return (WF((0, 0, 0), (1, 0, 0), 'front'), WF((W / 2, 0, 0), (0, 1, 0), 'right'),
            WF((0, D, 0), (-1, 0, 0), 'back'), WF((-W / 2, 0, 0), (0, -1, 0), 'left'))


def put(B, wf, bm, mat=None, sm=None, shade=None):
    xform(bm, wf.M)
    return B.add(bm, mat, sm, shade)


class MB:
    """Collects separate faces (own vertices each) with a material, an expected normal, a shade
    and optional UVs, then makes one bmesh."""
    def __init__(self):
        self.V = []; self.F = []; self.M = []; self.E = []; self.S = []; self.UV = []

    def face(self, pts, mat, expect=None, shade=1.0, uv=None):
        pts = [tuple(map(float, p)) for p in pts]
        clean = []
        for p in pts:
            if not clean or (Vector(p) - Vector(clean[-1])).length > 1e-6: clean.append(p)
        if len(clean) > 2 and (Vector(clean[0]) - Vector(clean[-1])).length < 1e-6: clean.pop()
        if len(clean) < 3: return
        i0 = len(self.V); self.V += clean
        self.F.append(list(range(i0, i0 + len(clean)))); self.M.append(mat); self.E.append(expect)
        self.S.append(shade); self.UV.append(uv)

    def bm(self, sm=0):
        bm, faces = bm_from(self.V, self.F, self.M, sm)
        lm, ls, lsh, lu = L(bm)
        for f, e, s, uv in zip(faces, self.E, self.S, self.UV):
            if f is None: continue
            f[lsh] = s
            if e is not None and f.normal.dot(Vector(e)) < 0: f.normal_flip()
            if uv is not None:
                for l in f.loops: l[lu].uv = uv(l.vert.co)
        bm.normal_update()
        return bm


# ---------------------------------------------------------------- walls
def top_at(top, u):
    if u <= top[0][0]: return top[0][1]
    for (u0, v0), (u1, v1) in zip(top[:-1], top[1:]):
        if u0 - 1e-9 <= u <= u1 + 1e-9:
            if u1 - u0 < 1e-9: return max(v0, v1)
            return v0 + (u - u0) / (u1 - u0) * (v1 - v0)
    return top[-1][1]


def span(top, v):
    """The u interval where the top outline is at or above v (outlines are single peaks or ramps)."""
    lo = hi = None
    for (u0, v0), (u1, v1) in zip(top[:-1], top[1:]):
        if max(v0, v1) < v - 1e-9: continue
        if abs(v1 - v0) < 1e-9:
            a, b = u0, u1
        else:
            uc = u0 + (v - v0) / (v1 - v0) * (u1 - u0)
            if v1 > v0: a, b = max(u0, uc), u1
            else: a, b = u0, min(u1, uc)
        lo = a if lo is None else min(lo, a); hi = b if hi is None else max(hi, b)
    return lo, hi


def rib_w(u, pitch, depth, ph=0.0):
    f = ((u - ph) / pitch) % 1.0
    if f < 0.35: return 0.0
    if f < 0.5: return depth * (f - 0.35) / 0.15
    if f < 0.85: return depth
    return depth * (1 - (f - 0.85) / 0.15)


def wall(B, wf, u0, u1, top, openings=(), v0=0.0, mode='flat', mat='wall', zones=(), vlines=(),
         rib=(0.2, 0.035), lap=(0.22, 0.028), shade=1.0, lip_mat='wallw'):
    """A wall surface over [u0, u1] from v0 up to the top outline (a height or [(u, v), ...]),
    with rectangular openings (ua, ub, va, vb) left out. zones: (ua, ub, va, vb, mat) cells of
    another material. mode: 'flat', 'lap' (horizontal boards, each row's bottom edge proud, with
    a shadowed lip) or 'rib' (vertical box-profile cladding)."""
    if isinstance(top, (int, float)): top = [(u0, float(top)), (u1, float(top))]
    ops = list(openings)
    levels = set(vlines) | {v for o in ops for v in (o[2], o[3])} | {v for z in zones for v in (z[2], z[3])}
    mb = MB()

    def matat(u, v):
        for z in zones:
            if z[0] - 1e-6 <= u <= z[1] + 1e-6 and z[2] - 1e-6 <= v <= z[3] + 1e-6: return z[4]
        return mat
    if mode in ('flat', 'rib'):
        us = {u0, u1} | {p[0] for p in top} | {x for o in ops for x in (o[0], o[1])} | {x for z in zones for x in (z[0], z[1])}
        if mode == 'rib':
            p = rib[0]
            k = math.floor(u0 / p) - 1
            while k * p < u1 + p:
                for fr in (0.0, 0.35, 0.5, 0.85): us.add(k * p + fr * p)
                k += 1
        for (ua, va), (ub, vb) in zip(top[:-1], top[1:]):
            for lv in levels:
                if (va - lv) * (vb - lv) < 0: us.add(ua + (lv - va) / (vb - va) * (ub - ua))
        us = sorted(u for u in us if u0 - 1e-7 <= u <= u1 + 1e-7)
        uu = []
        for u in us:
            if not uu or u - uu[-1] > 1e-5: uu.append(u)
        for a, b in zip(uu[:-1], uu[1:]):
            m = (a + b) / 2
            ta, tb = top_at(top, a), top_at(top, b); tm = min(ta, tb)
            wa = rib_w(a, *rib) if mode == 'rib' else 0.0
            wb = rib_w(b, *rib) if mode == 'rib' else 0.0
            holes = [o for o in ops if o[0] - 1e-6 <= m <= o[1] + 1e-6]
            zs = [z for z in zones if z[0] - 1e-6 <= m <= z[1] + 1e-6]
            mine = set(vlines) | {v for o in holes for v in (o[2], o[3])} | {v for z in zs for v in (z[2], z[3])}
            cuts = sorted({v0} | {lv for lv in mine if v0 + 1e-6 < lv < tm - 1e-6})
            for i, c in enumerate(cuts):
                hi = cuts[i + 1] if i + 1 < len(cuts) else None
                vm = (c + (hi if hi is not None else tm)) / 2
                if any(o[2] - 1e-6 <= vm <= o[3] + 1e-6 for o in holes): continue
                ha = hi if hi is not None else ta; hb = hi if hi is not None else tb
                if ha - c < 1e-6 and hb - c < 1e-6: continue
                mb.face([(a, c, wa), (b, c, wb), (b, hb, wb), (a, ha, wa)], matat(m, vm), (0, 0, 1), shade)
    else:  # lap
        h, d = lap
        vmax = max(p[1] for p in top)
        cuts = set()
        v = v0
        while v < vmax - 1e-6: cuts.add(round(v, 6)); v += h
        cuts |= {lv for lv in levels if v0 < lv < vmax} | {p[1] for p in top if v0 < p[1] < vmax}
        cuts = sorted(cuts) + [vmax]
        for va, vb in zip(cuts[:-1], cuts[1:]):
            k = math.floor((va - v0) / h + 1e-6); rlo = v0 + k * h

            def wv(v, rlo=rlo):
                return d * (1 - min(max((v - rlo) / h, 0.0), 1.0))
            La, Ra = span(top, va); Lb, Rb = span(top, vb)
            if La is None: continue
            if Lb is None: Lb = Rb = (La + Ra) / 2
            La, Ra, Lb, Rb = max(La, u0), min(Ra, u1), max(Lb, u0), min(Rb, u1)
            vm = (va + vb) / 2
            holes = sorted([o for o in ops if o[2] - 1e-6 <= vm <= o[3] + 1e-6], key=lambda o: o[0])
            segs = []; left = None
            for o in holes:
                segs.append((left, o[0])); left = o[1]
            segs.append((left, None))
            for l, r in segs:
                lA = La if l is None else max(l, La); lB = Lb if l is None else max(l, Lb)
                rA = Ra if r is None else min(r, Ra); rB = Rb if r is None else min(r, Rb)
                if rA - lA < 1e-5 and rB - lB < 1e-5: continue
                mm = matat((lA + rA) / 2, vm)
                mb.face([(lA, va, wv(va)), (rA, va, wv(va)), (rB, vb, wv(vb)), (lB, vb, wv(vb))], mm, (0, 0, 1), shade)
                if abs(va - rlo) < 1e-6 and k > 0 and rA - lA > 1e-4:
                    mb.face([(lA, va, 0.0), (rA, va, 0.0), (rA, va, d), (lA, va, d)], lip_mat, (0, -1, 0), 0.55)
    bm = mb.bm()
    return put(B, wf, bm)


def corner(B, P0, P1, v0, v1, mat='wall', vlines=(), zones=()):
    """A chamfer strip between two walls, from P0 to P1 (x, y), going round the building
    counter-clockwise seen from above."""
    P0 = Vector((P0[0], P0[1], 0)); P1 = Vector((P1[0], P1[1], 0))
    wf = WF(P0, P1 - P0, 'front')
    n = wf.N
    wf.mp = 'front' if n.y < -0.5 else ('right' if n.x > 0.5 else ('left' if n.x < -0.5 else 'back'))
    w = (P1 - P0).length
    return wall(B, wf, 0, w, v1, (), v0, 'flat', mat, [(0, w, z[0], z[1], z[2]) for z in zones], vlines)


def corner_board(B, x, y, v0, v1, s=0.075, mat='trim', r=0.02):
    pts = [(x - s + r, y - s), (x + s - r, y - s), (x + s, y - s + r), (x + s, y + s - r), (x + s - r, y + s), (x - s + r, y + s),
           (x - s, y + s - r), (x - s, y - s + r)]
    return B.add(prism(pts, v0, v1, mat, caps=(False, True)))


def box_shell_corners(B, v0, v1, c, mat='wall', vlines=(), zones=(), which=('fr', 'br', 'bl', 'fl')):
    W, D = B.W, B.D
    pairs = {'fr': ((W / 2 - c, 0), (W / 2, c)), 'br': ((W / 2, D - c), (W / 2 - c, D)),
             'bl': ((-W / 2 + c, D), (-W / 2, D - c)), 'fl': ((-W / 2, c), (-W / 2 + c, 0))}
    for k in which:
        a, b = pairs[k]
        vv = v1[k] if isinstance(v1, dict) else v1
        corner(B, a, b, v0, vv, mat, vlines, zones)


# ---------------------------------------------------------------- openings
def reveal(mb, u0, u1, v0, v1, depth, mat='reveal', bottom=True, shade=0.8):
    z0, z1 = 0.0, -depth
    mb.face([(u0, v0, z0), (u0, v1, z0), (u0, v1, z1), (u0, v0, z1)], mat, (1, 0, 0), shade)
    mb.face([(u1, v0, z0), (u1, v0, z1), (u1, v1, z1), (u1, v1, z0)], mat, (-1, 0, 0), shade)
    mb.face([(u0, v1, z0), (u1, v1, z0), (u1, v1, z1), (u0, v1, z1)], mat, (0, -1, 0), shade * 0.85)
    if bottom:
        mb.face([(u0, v0, z0), (u0, v0, z1), (u1, v0, z1), (u1, v0, z0)], mat, (0, 1, 0), shade * 1.05)


def ring(mb, o, i, zo, zi, mat, ex, shade=1.0):
    """Four faces joining the outer rect o = (x0, y0, x1, y1) at zo to the inner rect i at zi.
    ex: 'front' (normals +z) or 'in' (normals toward the centre)."""
    oc = [(o[0], o[1]), (o[2], o[1]), (o[2], o[3]), (o[0], o[3])]
    ic = [(i[0], i[1]), (i[2], i[1]), (i[2], i[3]), (i[0], i[3])]
    inward = [(0, 1, 0), (-1, 0, 0), (0, -1, 0), (1, 0, 0)]
    for k in range(4):
        k2 = (k + 1) % 4
        e = (0, 0, 1) if ex == 'front' else tuple(a + b for a, b in zip(inward[k], (0, 0, 0.5)))
        mb.face([(oc[k][0], oc[k][1], zo), (oc[k2][0], oc[k2][1], zo), (ic[k2][0], ic[k2][1], zi), (ic[k][0], ic[k][1], zi)], mat, e, shade)


def bar(mb, x0, y0, x1, y1, z0, z1, mat, shade=1.0, ends=False):
    """A bar seen from the front: front face and its four sides (no back)."""
    mb.face([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], mat, (0, 0, 1), shade)
    mb.face([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], mat, (-1, 0, 0), shade * 0.9)
    mb.face([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], mat, (1, 0, 0), shade * 0.9)
    if ends:
        mb.face([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], mat, (0, 1, 0), shade)
        mb.face([(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)], mat, (0, -1, 0), shade * 0.8)


def glass_uv(rect, region):
    x0, y0, x1, y1 = rect

    def f(co):
        return reg_uv(region, (co.x - x0) / (x1 - x0), (co.y - y0) / (y1 - y0), 0.01)
    return f


def window(B, wf, u0, u1, v0, v1, depth=0.16, fw=0.075, cols=2, rows=1, transom=None, frame='frame',
           glass='glass0', sill='trim', head='lintel', shutters=None, planter=None, casing=None, bars=0,
           mull=0.055, register=True, cheap=False, flowers=None, seed=0):
    """A recessed window: reveal, a chunky frame with mullions, glass with a reflection streak,
    sill, head (lintel / key / casing / none), optional shutters, flower box and casing boards."""
    mb = MB()
    zf = -depth + 0.065                 # frame front
    zg = -depth + 0.02                  # glass
    reveal(mb, u0, u1, v0, v1, depth)
    c = 0.016
    o = (u0, v0, u1, v1); i = (u0 + fw, v0 + fw, u1 - fw, v1 - fw)
    ic = (i[0] - c, i[1] - c, i[2] + c, i[3] + c)
    if cheap:
        ring(mb, o, i, zf, zf, frame, 'front')
        ring(mb, i, i, zf, zg, frame, 'in', 0.85)
    else:
        ring(mb, o, ic, zf, zf, frame, 'front')
        ring(mb, ic, i, zf, zf - c, frame, 'front')
        ring(mb, i, i, zf - c, zg, frame, 'in', 0.85)
    mb.face([(i[0], i[1], zg), (i[2], i[1], zg), (i[2], i[3], zg), (i[0], i[3], zg)], 'glass', (0, 0, 1), 1.0, glass_uv(i, glass))
    iw, ih = i[2] - i[0], i[3] - i[1]
    zb = zf - 0.012
    for k in range(1, cols):
        x = i[0] + iw * k / cols
        bar(mb, x - mull / 2, i[1], x + mull / 2, i[3], zg, zb, frame)
    for k in range(1, rows):
        y = i[1] + ih * k / rows
        bar(mb, i[0], y - mull / 2, i[2], y + mull / 2, zg, zb, frame)
    if transom is not None:
        y = i[1] + ih * transom
        bar(mb, i[0], y - mull / 2, i[2], y + mull / 2, zg, zb + 0.004, frame)
    for k in range(bars):
        x = i[0] + iw * (k + 0.5) / bars
        bar(mb, x - 0.012, v0, x + 0.012, v1, -0.06, -0.035, 'metald')
    put(B, wf, mb.bm())
    parts = []
    if casing:                          # boards round the opening (on clad walls)
        cw, cz = casing if isinstance(casing, tuple) else (0.11, 0.055)
        cm = 'trim'
        parts.append(fbox((u0 - cw, v0 - 0.02, 0), (u0, v1, cz), 0.014, cm))
        parts.append(fbox((u1, v0 - 0.02, 0), (u1 + cw, v1, cz), 0.014, cm))
        parts.append(fbox((u0 - cw - 0.03, v1, 0), (u1 + cw + 0.03, v1 + 0.15, cz), 0.016, cm))
        parts.append(fbox((u0 - cw - 0.06, v1 + 0.15, 0), (u1 + cw + 0.06, v1 + 0.2, cz + 0.035), 0.014, cm))
    if sill:
        so = 0.13 if not cheap else 0.1
        ext = 0.1 if not casing else (casing[0] if isinstance(casing, tuple) else 0.11) + 0.05
        if cheap:
            sb = box((u0 - ext, v0 - 0.07, -depth + 0.06), (u1 + ext, v0 + 0.012, so), sill, skip=('-z',))
        else:
            sb = fbox((u0 - ext, v0 - 0.075, -depth + 0.06), (u1 + ext, v0 + 0.015, so), 0.022, sill)
        parts.append(sb)
        a0, b0 = wf.ab(u0 - ext, v0 - 0.075); a1, _ = wf.ab(u1 + ext, v0)
        B.feat(wf.mp, 'streak', a0=min(a0, a1), a1=max(a0, a1), b=b0, length=0.9 + 0.5 * B.rng.random(), k=1.0)
        B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=b0, length=0.12, k=0.35)
    if head == 'lintel':
        parts.append(fbox((u0 - 0.08, v1, -0.01), (u1 + 0.08, v1 + 0.14, 0.035), 0.014, sill or 'trim') if not cheap
                     else box((u0 - 0.08, v1, -0.01), (u1 + 0.08, v1 + 0.13, 0.035), sill or 'trim', skip=('-z',)))
    elif head == 'key':
        parts.append(fbox((u0 - 0.08, v1, -0.01), (u1 + 0.08, v1 + 0.15, 0.035), 0.014, sill or 'trim'))
        kb = extrude_poly([(-0.11, 0), (0.11, 0), (0.15, 0.27), (-0.15, 0.27)], 0.075, sill or 'trim')
        xform(kb, T((u0 + u1) / 2, v1 - 0.05, -0.01)); parts.append(kb)
    elif head == 'hood':
        parts.append(fbox((u0 - 0.12, v1 + 0.02, -0.01), (u1 + 0.12, v1 + 0.13, 0.12), 0.03, sill or 'trim'))
    if shutters:
        sw = (u1 - u0) / 2 * 0.98
        gap = 0.03 + ((casing[0] if isinstance(casing, tuple) else 0.11) if casing else 0.0)
        for sx in (-1, 1):
            x0 = u0 - gap - sw if sx < 0 else u1 + gap
            x1 = x0 + sw
            sb = box((x0, v0 + 0.01, 0.0), (x1, v1 - 0.01, 0.045), 'accentk' if shutters == 'accent' else shutters, skip=('-z',))
            fr = faces_facing(sb, (0, 0, 1), 0.9)
            uv_fn(sb, fr, 'louvre', lambda co, x0=x0, x1=x1: ((co.x - x0) / (x1 - x0), (co.y - v0) / (v1 - v0)), 0.01)
            parts.append(sb)
            for hy in (v0 + 0.2, v1 - 0.2):
                hx = x1 if sx < 0 else x0
                parts.append(box((hx - 0.05, hy - 0.025, 0.0), (hx + 0.05, hy + 0.025, 0.055), 'metald', skip=('-z',)))
        a0, b0 = wf.ab(u0 - gap - sw, v0); a1, _ = wf.ab(u1 + gap + sw, v0)
        B.feat(wf.mp, 'ao_rect', a0=min(a0, a1), a1=max(a0, a1), b0=v0, b1=v1, k=0.12)
    for p in parts: put(B, wf, p)
    if planter:
        flower_box(B, wf, u0 + 0.04, u1 - 0.04, v0 - 0.085, planter, seed=seed, flowers=flowers)
    if register:
        c3 = wf.P((u0 + u1) / 2, (v0 + v1) / 2, zg)
        B.windows.append({'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(u1 - u0, 3), round(v1 - v0, 3)], 'wall': wf.mp})


def flower_box(B, wf, x0, x1, ytop, mat='accent', seed=0, flowers=None, depth=0.24, h=0.22, z0=0.03, density=0.27, nfl=2):
    rng = np.random.default_rng(seed + 11)
    bx = fbox((x0, ytop - h, z0), (x1, ytop, z0 + depth), 0.03, mat if mat != 'accent' else 'accentp')
    put(B, wf, bx)
    put(B, wf, box((x0 + 0.03, ytop - 0.03, z0 + 0.03), (x1 - 0.03, ytop - 0.02, z0 + depth - 0.03), 'soil', skip=('-z', '-x', '+x', '-y', '+y')))
    n = max(2, int((x1 - x0) / density))
    fl = flowers or rng.choice(['fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'fl6'], 2)
    leaves = ['leaf', 'leafl', 'leafd']
    for k in range(n):
        x = x0 + 0.1 + (x1 - x0 - 0.2) * (k + 0.5) / n + rng.uniform(-0.03, 0.03)
        r = rng.uniform(0.11, 0.15)
        put(B, wf, blob((x, ytop + r * 0.45, z0 + depth * 0.55), (r, r * 0.95, r * 0.8), leaves[k % 3], n=6, rings=2, seed=seed * 31 + k))
        for j in range(nfl):
            fx = x + rng.uniform(-0.1, 0.1); fy = ytop + r * 0.75 + rng.uniform(0.0, 0.07)
            put(B, wf, blob((fx, fy, z0 + depth * 0.55 + r * 0.55), (0.05, 0.045, 0.04), fl[(k + j) % len(fl)], n=4, rings=1, seed=seed * 7 + k * 3 + j, jitter=0.05))
    # trailing leaves over the front edge
    for k in range(2):
        x = x0 + 0.15 + (x1 - x0 - 0.3) * (0.2 + 0.6 * k + 0.1 * rng.random())
        put(B, wf, blob((x, ytop - h * 0.45, z0 + depth + 0.02), (0.07, 0.16, 0.05), 'leafd', n=5, rings=2, seed=seed * 13 + k))


def door(B, wf, u0, u1, v0, v1, depth=0.2, mat='accent', panels=((2, 3),), glass=None, casing=True,
         lining='trim', knob='brass', double=False, fan=None, register=True, glass_region='glass0', name='Door'):
    """A recessed panelled door: reveal, lining, leaf (raised panels via sunken fields, optional
    glazed top), casing boards, knob and letter plate. glass: fraction of the leaf height that
    is glazed at the top (None for none)."""
    mb = MB()
    reveal(mb, u0, u1, v0, v1, depth, bottom=False)
    lw = 0.06
    zl = -depth + 0.075
    o = (u0, v0, u1, v1); i = (u0 + lw, v0, u1 - lw, v1 - lw)
    # lining (left, right, head)
    mb.face([(u0, v0, zl), (i[0], v0, zl), (i[0], i[3], zl), (u0, v1, zl)], lining, (0, 0, 1))
    mb.face([(i[2], v0, zl), (u1, v0, zl), (u1, v1, zl), (i[2], i[3], zl)], lining, (0, 0, 1))
    mb.face([(i[0], i[3], zl), (i[2], i[3], zl), (u1, v1, zl), (u0, v1, zl)], lining, (0, 0, 1))
    zf = -depth + 0.035
    mb.face([(i[0], v0, zl), (i[0], i[3], zl), (i[0], i[3], zf), (i[0], v0, zf)], lining, (1, 0, 0), 0.8)
    mb.face([(i[2], v0, zl), (i[2], v0, zf), (i[2], i[3], zf), (i[2], i[3], zl)], lining, (-1, 0, 0), 0.8)
    mb.face([(i[0], i[3], zl), (i[2], i[3], zl), (i[2], i[3], zf), (i[0], i[3], zf)], lining, (0, -1, 0), 0.7)
    put(B, wf, mb.bm())
    leaves = [(i[0], i[2])] if not double else [(i[0], (i[0] + i[2]) / 2), ((i[0] + i[2]) / 2, i[2])]
    for li, (x0, x1) in enumerate(leaves):
        lw_ = x1 - x0; lh = i[3] - v0
        holes = []; glazed = []
        m = 0.11 * min(1.0, lw_ / 0.9)
        ncols, nrows = panels[0]
        gtop = None
        if glass:
            gy0 = v0 + lh * (1 - glass)
            glazed.append((x0 + m, x1 - m, gy0, i[3] - m)); gtop = gy0
        ytop = (gtop - 0.1) if gtop else i[3] - m
        ybot = v0 + 0.2
        if nrows > 0 and ytop - ybot > 0.3:
            pw = (lw_ - 2 * m - (ncols - 1) * 0.08) / ncols
            ph = (ytop - ybot - (nrows - 1) * 0.09) / nrows
            for r in range(nrows):
                for c in range(ncols):
                    px0 = x0 + m + c * (pw + 0.08); py0 = ybot + r * (ph + 0.09)
                    holes.append((px0, px0 + pw, py0, py0 + ph))
        lf = wf.off(zf)
        wall(B, lf, x0, x1, i[3], holes + glazed, v0, 'flat', mat)
        mb = MB()
        for (a, b, c_, d) in holes:      # sunken fields with a bevelled edge
            e = 0.022
            ring(mb, (a, c_, b, d), (a + e, c_ + e, b - e, d - e), 0.0, -0.016, mat, 'front', 0.92)
            mb.face([(a + e, c_ + e, -0.016), (b - e, c_ + e, -0.016), (b - e, d - e, -0.016), (a + e, d - e, -0.016)], mat, (0, 0, 1))
        for (a, b, c_, d) in glazed:
            ring(mb, (a, c_, b, d), (a, c_, b, d), 0.0, -0.03, mat, 'in', 0.8)
            mb.face([(a, c_, -0.03), (b, c_, -0.03), (b, d, -0.03), (a, d, -0.03)], 'glass', (0, 0, 1), 1.0, glass_uv((a, c_, b, d), glass_region))
            if (b - a) > 0.45:
                xm = (a + b) / 2
                bar(mb, xm - 0.025, c_, xm + 0.025, d, -0.03, -0.005, mat)
        put(B, lf, mb.bm())
        # knob and letter plate
        kx = x1 - 0.1 if (li == len(leaves) - 1 or not double) else x1 - 0.08
        if double and li == 0: kx = x1 - 0.08
        if double and li == 1: kx = x0 + 0.08
        kb, _ = lathe([(0, 0), (0.03, 0), (0.03, 0.02), (0.012, 0.035), (0.03, 0.06), (0.03, 0.075), (0, 0.08)], 8, knob)
        xform(kb, T(kx, v0 + 1.0, 0)); put(B, lf, kb)
        if not double and not glass:
            put(B, lf, fbox((x0 + lw_ * 0.3, v0 + 0.85, 0), (x0 + lw_ * 0.7, v0 + 0.93, 0.015), 0.006, knob))
    parts = []
    if casing:
        cw = 0.1
        parts.append(fbox((u0 - cw, v0, 0), (u0, v1, 0.05), 0.014, 'trim'))
        parts.append(fbox((u1, v0, 0), (u1 + cw, v1, 0.05), 0.014, 'trim'))
        parts.append(fbox((u0 - cw - 0.03, v1, 0), (u1 + cw + 0.03, v1 + 0.14, 0.055), 0.016, 'trim'))
        parts.append(fbox((u0 - cw - 0.06, v1 + 0.14, 0), (u1 + cw + 0.06, v1 + 0.19, 0.09), 0.014, 'trim'))
    if fan:   # a glazed fanlight above the door
        fy0, fy1 = fan
        window(B, wf, u0, u1, fy0, fy1, depth=depth, cols=3, head=None, sill=None, register=False, glass=glass_region)
    for p in parts: put(B, wf, p)
    a0, _ = wf.ab(u0, v0); a1, _ = wf.ab(u1, v0)
    B.feat(wf.mp, 'opening', a0=min(a0, a1), a1=max(a0, a1), b0=v0, b1=v1)
    if register:
        c3 = wf.P((u0 + u1) / 2, v0, 0)
        B.doors.append({'name': name, 'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(u1 - u0, 3), round(v1 - v0, 3)], 'wall': wf.mp})



def steps(B, wf, x0, x1, heights, tread=0.3, back=0.25, mat='conc'):
    """Steps in front of a wall: heights from the top step down, each one a tread further out and
    a little wider; they run back into the door's reveal."""
    for k, h in enumerate(heights):
        e = 0.08 * k
        put(B, wf, fbox((x0 - e, 0.0, -back), (x1 + e, h, tread * (k + 1)), 0.03, mat))



def lantern(B, wf, x, y, out=0.2, mat='metald', glow='lamp', name='Lamp'):
    """A wall lantern: back plate, arm, a tapered glass box under a pyramid cap."""
    put(B, wf, fbox((x - 0.07, y - 0.12, 0), (x + 0.07, y + 0.12, 0.03), 0.01, mat))
    put(B, wf, box((x - 0.018, y + 0.02, 0.03), (x + 0.018, y + 0.06, out), mat, skip=('-z',)))
    body, _ = lathe([(0, -0.17), (0.055, -0.17), (0.075, -0.15), (0.095, 0.08), (0.075, 0.1), (0.125, 0.11),
                     (0.07, 0.19), (0.0, 0.22)], 4, [mat, mat, glow, mat, mat, mat, mat], phase=0.5)
    xform(body, T(x, y, out) @ R(-PI / 2, 'X'))
    put(B, wf, body)
    p = wf.P(x, y, out)
    B.lamps.append({'name': name, 'center': [round(p.x, 3), round(p.y, 3), round(p.z, 3)]})
    a, b = wf.ab(x, y)
    B.feat(wf.mp, 'glow', a=a, b=b, r=0.45)



def gooseneck(B, wf, x, y, reach=0.6, rise=0.32, name='Lamp', mat='metald', shade_mat='accentw'):
    """A wall lamp on a curved arm with a wide enamel shade hanging at its end."""
    put(B, wf, fbox((x - 0.06, y - 0.09, 0), (x + 0.06, y + 0.09, 0.03), 0.01, mat))
    path = [(x, y + rise * math.sin(PI / 2 * k / 7), 0.03 + reach * (1 - math.cos(PI / 2 * k / 7))) for k in range(8)]
    put(B, wf, tube(path, 0.022, mat, sides=6))
    sh, _ = lathe([(0, -0.15), (0.18, -0.15), (0.17, -0.13), (0.06, -0.02), (0.05, 0.0), (0.0, 0.02)], 12,
                  ['lamp', shade_mat, shade_mat, shade_mat, shade_mat], phase=0.5)
    end = path[-1]
    xform(sh, T(x, end[1] - 0.02, end[2]) @ R(-PI / 2, 'X'))
    put(B, wf, sh)
    p = wf.P(x, end[1] - 0.17, end[2])
    B.lamps.append({'name': name, 'center': [round(p.x, 3), round(p.y, 3), round(p.z, 3)]})
    a, b = wf.ab(x, y)
    B.feat(wf.mp, 'glow', a=a, b=b - 0.2, r=0.8)


def ac_unit(B, wf, x, y, z=0.0, w=0.82, h=0.56, d=0.28, brackets=True, mat='whitep', pipe=True):
    """An air-conditioner condenser on brackets: a rounded body, a grille face (atlas), a pipe."""
    body = fbox((x - w / 2, y, z + 0.02), (x + w / 2, y + h, z + d), 0.035, mat)
    fr = [f for f in faces_facing(body, (0, 0, 1), 0.95)]
    setmat(body, 'tex', fr)
    uv_fn(body, fr, 'ac', lambda co: ((co.x - (x - w / 2)) / w, (co.y - y) / h), 0.02)
    put(B, wf, body)
    if brackets:
        for sx in (-1, 1):
            bx = x + sx * (w / 2 - 0.1)
            put(B, wf, box((bx - 0.02, y - 0.05, 0), (bx + 0.02, y, z + d + 0.03), 'metal', skip=('-z', '+x' if sx < 0 else '-x')))
    if pipe:
        put(B, wf, tube([(x + w / 2 - 0.05, y + h * 0.4, z + 0.12), (x + w / 2 + 0.1, y + h * 0.4, 0.05), (x + w / 2 + 0.1, y + h + 0.6, 0.05)], 0.025, 'white', 4))
    a0, b0 = wf.ab(x - w / 2, y); a1, b1 = wf.ab(x + w / 2, y + h)
    B.feat(wf.mp, 'ao_rect', a0=min(a0, a1), a1=max(a0, a1), b0=b0, b1=b1, k=0.28)
    B.feat(wf.mp, 'streak', a0=min(a0, a1) + 0.1, a1=max(a0, a1) - 0.1, b=b0, length=0.7, k=0.8)


def meter_box(B, wf, x, y, w=0.36, h=0.5, mat='whitep'):
    bx = fbox((x - w / 2, y, 0), (x + w / 2, y + h, 0.14), 0.02, mat)
    put(B, wf, bx)
    put(B, wf, box((x - w * 0.3, y + h * 0.55, 0.14), (x + w * 0.3, y + h * 0.8, 0.15), 'glass', skip=('-z',)))
    put(B, wf, box((x - 0.012, y + 0.05, 0.0), (x + 0.012, y + 0.01, 0.06), 'metald'))
    put(B, wf, tube([(x, y, 0.07), (x, y - 0.25, 0.07), (x, y - 0.6, 0.07)], 0.02, 'metald', 5))
    a0, b0 = wf.ab(x - w / 2, y); a1, b1 = wf.ab(x + w / 2, y + h)
    B.feat(wf.mp, 'ao_rect', a0=min(a0, a1), a1=max(a0, a1), b0=b0, b1=b1, k=0.2)


def vent(B, wf, x, y, s=0.32):
    v = fbox((x - s / 2, y - s / 2, 0), (x + s / 2, y + s / 2, 0.03), 0.008, 'tex')
    uv_fn(v, faces_facing(v, (0, 0, 1), 0.9), 'vent', lambda co: ((co.x - x + s / 2) / s, (co.y - y + s / 2) / s), 0.02)
    put(B, wf, v)


def pot(B, P, r=0.2, h=0.3, mat='pot', plant='bush', seed=0, scale=1.0):
    """A pot with a plant, standing at the world point P."""
    rng = np.random.default_rng(seed + 101)
    P = Vector(P)
    pb, tags = lathe([(r * 0.72, 0), (r * 0.9, h * 0.84), (r, h * 0.86), (r, h), (r * 0.86, h), (0, h * 0.92)],
                     9, [mat, mat, mat, mat, 'soil'])
    xform(pb, T(P)); B.add(pb)
    top = P + Vector((0, 0, h * 0.9))
    s = scale
    if plant == 'bush':
        for k in range(3):
            a = 2 * PI * k / 4 + rng.random()
            c = top + Vector((math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, r * 0.6 * s + rng.random() * 0.1 * s))
            B.add(blob(c, (r * 0.8 * s, r * 0.8 * s, r * 0.72 * s), ['leaf', 'leafl', 'leafd', 'leaf'][k], 6, 2, seed * 5 + k))
        B.add(blob(top + Vector((0, 0, r * 1.25 * s)), (r * 0.72 * s, r * 0.72 * s, r * 0.66 * s), 'leafl', 6, 2, seed * 5 + 9))
    elif plant == 'flowers':
        for k in range(3):
            a = 2 * PI * k / 3 + rng.random()
            c = top + Vector((math.cos(a) * r * 0.4, math.sin(a) * r * 0.4, r * 0.45 * s))
            B.add(blob(c, (r * 0.6 * s, r * 0.6 * s, r * 0.5 * s), ['leaf', 'leafd', 'leaf'][k], 6, 2, seed * 5 + k))
        fl = rng.choice(['fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'fl6'])
        for k in range(6):
            a = 2 * PI * k / 6 + rng.random() * 0.5
            c = top + Vector((math.cos(a) * r * 0.55, math.sin(a) * r * 0.55, r * 0.8 * s + rng.random() * 0.05))
            B.add(blob(c, (0.055, 0.055, 0.045), fl, 4, 1, seed * 3 + k, 0.05))
    elif plant == 'tall':          # a leafy upright plant (rubber plant / palm-ish clumps)
        for k in range(4):
            zc = r * 0.8 + k * r * 0.8 * s
            a = rng.random() * 2 * PI
            c = top + Vector((math.cos(a) * r * 0.3, math.sin(a) * r * 0.3, zc))
            rr = r * (0.85 - 0.08 * k) * s
            B.add(blob(c, (rr, rr, rr * 0.75), ['leafd', 'leaf', 'leafl', 'leaf', 'leafl'][k], 6, 2, seed * 9 + k))
        B.add(tube([top, top + Vector((0, 0, r * 2.5 * s))], 0.02, 'woodd', 4, caps=False))
    elif plant == 'grass':
        for k in range(5):
            a = 2 * PI * k / 5 + rng.random()
            c = top + Vector((math.cos(a) * r * 0.35, math.sin(a) * r * 0.35, r * 0.9 * s))
            B.add(blob(c, (r * 0.3 * s, r * 0.3 * s, r * 1.0 * s), ['leafl', 'leafy', 'leaf'][k % 3], 5, 2, seed * 4 + k))


def laundry(B, wf, x0, x1, y, z, seed=0, n=4):
    """A line between two points with clothes pegged on it (in the wall's space)."""
    rng = np.random.default_rng(seed + 7)
    put(B, wf, tube([(x0, y, z), ((x0 + x1) / 2, y - 0.04, z), (x1, y, z)], 0.008, 'white', 4))
    cl = ['cloth1', 'cloth2', 'cloth3', 'cloth4', 'cloth5', 'cloth6']
    xs = sorted(rng.uniform(x0 + 0.2, x1 - 0.2, n))
    last = x0
    for k, xc in enumerate(xs):
        kind = rng.choice(['tee', 'towel', 'towel', 'shorts', 'tee'])
        m = cl[int(rng.integers(0, len(cl)))]
        if kind == 'tee':
            w, h = 0.46, 0.55
            pts = [(-0.23, 0), (0.23, 0), (0.28, -0.16), (0.17, -0.2), (0.16, -0.55), (-0.16, -0.55), (-0.17, -0.2), (-0.28, -0.16)]
        elif kind == 'towel':
            w = rng.uniform(0.35, 0.5); h = rng.uniform(0.5, 0.75)
            pts = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)]
        else:
            pts = [(-0.2, 0), (0.2, 0), (0.22, -0.45), (0.04, -0.45), (0.0, -0.18), (-0.04, -0.45), (-0.22, -0.45)]
        if xc - last < 0.28: continue
        last = xc + 0.25
        cb = extrude_poly(pts, 0.02, m, back=True)
        for v in cb.verts:
            v.co.z += 0.03 * math.sin(v.co.x * 9 + k)
        xform(cb, T(xc, y - 0.01, z - 0.01) @ R(rng.uniform(-0.05, 0.05), 'Z'))
        put(B, wf, cb)
        for px in (pts[0][0] + 0.03, pts[1][0] - 0.03):
            put(B, wf, box((xc + px - 0.012, y - 0.03, z - 0.03), (xc + px + 0.012, y + 0.03, z + 0.03), 'woodc', skip=('-z', '+y', '-y')))


def awning(B, wf, x0, x1, z_top, out, drop, stripes, mat_a='accent', mat_b='cream', valance=0.24, scallops=True,
           arms=True, segs=3, cheeks=False):
    """A striped fabric awning from the wall at z_top (wall space y) out to `out`, dropping by
    `drop`, with a scalloped valance and folding arms."""
    mb = MB()
    n = stripes
    ws = (x1 - x0) / n

    def prof(t):          # t 0 at the wall, 1 at the front edge: (y, z) with a soft billow
        y = z_top - drop * (t ** 1.15) + 0.06 * math.sin(PI * t)
        return y, out * t
    ts = [k / segs for k in range(segs + 1)]
    for s in range(n):
        xa, xb = x0 + s * ws, x0 + (s + 1) * ws
        m = mat_a if s % 2 == 0 else mat_b
        for a, b in zip(ts[:-1], ts[1:]):
            ya, za = prof(a); yb, zb = prof(b)
            mb.face([(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], m, (0, 1, 0.3))
            mb.face([(xa, ya - 0.025, za), (xa, yb - 0.025, zb), (xb, yb - 0.025, zb), (xb, ya - 0.025, za)], m, (0, -1, 0), 0.7)
        # valance
        yf, zf = prof(1.0)
        pts = [(xa, yf, zf), (xb, yf, zf), (xb, yf - valance * 0.7, zf)]
        if scallops:
            for k in range(1, 6):
                a = PI * k / 6
                pts.append((xb - ws * k / 6, yf - valance * 0.7 - valance * 0.3 * math.sin(a), zf))
            pts.append((xa, yf - valance * 0.7, zf))
        else:
            pts = [(xa, yf, zf), (xb, yf, zf), (xb, yf - valance, zf), (xa, yf - valance, zf)]
        mb.face(pts, m, (0, 0, 1), 1.0)
        mb.face([(p[0], p[1], p[2] - 0.012) for p in reversed(pts)], m, (0, 0, -1), 0.65)
    # front rail (rolled bar) and the ends
    yf, zf = prof(1.0)
    bm = mb.bm()
    put(B, wf, bm)
    put(B, wf, tube([(x0 - 0.02, yf - 0.01, zf - 0.005), (x1 + 0.02, yf - 0.01, zf - 0.005)], 0.03, 'metald', 6))
    if arms:
        for x in (x0 + 0.12, x1 - 0.12):
            put(B, wf, tube([(x, z_top - drop - 0.55, 0.02), (x, yf - 0.02, out - 0.04)], 0.022, 'metald', 5))
            put(B, wf, fbox((x - 0.05, z_top - drop - 0.65, 0), (x + 0.05, z_top - drop - 0.45, 0.04), 0.01, 'metald'))
    put(B, wf, fbox((x0 - 0.05, z_top - 0.05, 0), (x1 + 0.05, z_top + 0.1, 0.1), 0.03, 'metald'))
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z_top - 0.02, length=0.5, k=0.5)


# ---------------------------------------------------------------- roofs
def pitched(B, ax, a0, a1, r0, r1, z0, rise, t=0.17, row=0.3, lip=0.038, mat='roof', barge=(True, True),
            barge_mat='trim', soffit='soffit', fascia=True, fascia_mat='trim', ridge=True, over=0.05, slopes=(0, 1),
            feat=True, barge_w=0.24, fmap='roof'):
    """Two tiled slopes meeting at a ridge. ax 'y': the ridge runs along Y over r0..r1, the eaves
    are at x = a0 and a1; ax 'x': the ridge runs along X, eaves at y = a0 (front) and a1 (back).
    z0: the underside at the eaves; rise: from the eaves' underside to the ridge's underside.
    Tile rows are stepped (each row's lower edge proud, a dark lip below it)."""
    hs = (a1 - a0) / 2
    k = rise / hs
    sl = math.atan(k); cs = math.cos(sl)
    nrow = max(2, int(round(hs / (row * cs))))
    srow = hs / nrow

    def ztop(s): return z0 + s * k + t
    rows_plan = []
    for side in slopes:
        mb = MB()
        sgn = 1 if side == 0 else -1
        base = a0 if side == 0 else a1

        def P(s, z, r):
            a = base + sgn * s
            return (a, r, z) if ax == 'y' else (r, a, z)
        # section polygon (s, z): underside, ridge, sawtooth down to the eave
        sec = [(0.0, z0), (hs, z0 + rise), (hs, ztop(hs))]
        for j in range(nrow - 1, -1, -1):
            s0 = j * srow
            sec.append((s0, ztop(s0) + lip))
            if j > 0: sec.append((s0, ztop(s0)))
        # outward normals of the section edges (polygon is counter-clockwise in (s, z) when sgn = 1)
        area = sum(sec[i][0] * sec[(i + 1) % len(sec)][1] - sec[(i + 1) % len(sec)][0] * sec[i][1] for i in range(len(sec)))
        ccw = area > 0
        for i in range(len(sec)):
            (sa, za), (sb, zb) = sec[i], sec[(i + 1) % len(sec)]
            ds, dz = sb - sa, zb - za
            nx, nz = (dz, -ds) if ccw else (-dz, ds)
            ns = nx * sgn
            e = (ns, 0, nz) if ax == 'y' else (0, ns, nz)
            ra, rb = r0 - over, r1 + over
            pts = [P(sa, za, ra), P(sb, zb, ra), P(sb, zb, rb), P(sa, za, rb)]
            if i == 0: m, sh = soffit, 0.9
            elif i == 1: m, sh = 'roofw', 0.7          # ridge face (hidden)
            elif abs(ds) < 1e-9 and i == len(sec) - 1: m, sh = 'roofw', 0.6   # eave end
            elif abs(ds) < 1e-9: m, sh = 'roofw', 0.5     # lips
            else: m, sh = mat, 1.0
            mb.face(pts, m, e, sh)
        # gable ends of the slab (sawtooth profile)
        for r, sg in ((r0 - over, -1), (r1 + over, 1)):
            e = (0, sg, 0) if ax == 'y' else (sg, 0, 0)
            mb.face([P(s, z, r) for s, z in sec], 'roofw', e, 0.75)
        B.add(mb.bm())
        for j in range(nrow):
            s0, s1 = j * srow, (j + 1) * srow
            pa, pb = base + sgn * s0, base + sgn * s1
            rows_plan.append((pa, pb))
    if feat:
        B.feat(fmap, 'tiles', axis=ax, rows=rows_plan, r0=r0 - over, r1=r1 + over, joint=0.27)
    top = z0 + rise + t
    if ridge:
        sec = [(-0.02, -0.17), (0.07, -0.13), (0.12, -0.05), (0.13, 0.03), (0.07, 0.09), (0.0, 0.11),
               (-0.07, 0.09), (-0.13, 0.03), (-0.12, -0.05), (-0.07, -0.13)]
        sec = [(z_, x_) for x_, z_ in sec]
        mid = (a0 + a1) / 2
        if ax == 'y':
            path = [(mid, r0 - over - 0.03, top), (mid, r1 + over + 0.03, top)]
            up = (0, 0, 1)
        else:
            path = [(r0 - over - 0.03, mid, top), (r1 + over + 0.03, mid, top)]
            up = (0, 0, 1)
        rb = sweep(path, up, [(a, b) for a, b in sec], 'roofw', caps=True, sm=0)
        setshade(rb, 0.92)
        B.add(rb)
    if any(barge):
        def P3(a, z, rr):
            return (a, rr, z) if ax == 'y' else (rr, a, z)
        for r, sg, on in ((r0 - over, -1, barge[0]), (r1 + over, 1, barge[1])):
            if not on: continue
            mb = MB()
            rr1 = r - sg * 0.05            # outer face, tucked under the tile ends
            rr0 = rr1 - sg * 0.05
            e = (0, sg, 0) if ax == 'y' else (sg, 0, 0)
            for side in slopes:
                sgn = 1 if side == 0 else -1
                base = a0 if side == 0 else a1
                lo = [(base + sgn * s_, z0 + s_ * k - 0.07) for s_ in (-0.03, hs)]
                hi = [(base + sgn * s_, z0 + s_ * k - 0.07 + barge_w) for s_ in (-0.03, hs)]
                mb.face([P3(a, z, rr1) for a, z in (lo[0], lo[1], hi[1], hi[0])], barge_mat, e)
                ee = (-sgn, 0, 0) if ax == 'y' else (0, -sgn, 0)
                for (pa, pb), x_ in (((lo[0], lo[1]), (0, 0, -1)), ((hi[1], hi[0]), (0, 0, 1)), ((lo[0], hi[0]), ee)):
                    mb.face([P3(pa[0], pa[1], rr0), P3(pb[0], pb[1], rr0), P3(pb[0], pb[1], rr1), P3(pa[0], pa[1], rr1)], barge_mat, x_, 0.85)
            B.add(mb.bm())
    if fascia:
        for side in slopes:
            sgn = 1 if side == 0 else -1
            base = a0 if side == 0 else a1
            lo_, hi_ = z0 - 0.1, z0 + t * 0.55
            if ax == 'y':
                x = base - sgn * 0.0
                b = cbox2((min(x, x - sgn * 0.045), r0 - over, lo_), (max(x, x - sgn * 0.045), r1 + over, hi_), 0.01, fascia_mat)
            else:
                y = base
                b = cbox2((r0 - over, min(y, y - sgn * 0.045), lo_), (r1 + over, max(y, y - sgn * 0.045), hi_), 0.01, fascia_mat)
            B.add(b)
    return top


def eave_gutter(B, path, z, mat='pipe', size=0.13):
    """A rounded gutter hanging along a 2D path (x, y), going round the building counter-clockwise."""
    s = size
    prof = [(-0.005, z + 0.01), (0.0, z - 0.04), (0.02, z - s * 0.72), (s * 0.5, z - s * 0.95), (s * 0.9, z - s * 0.75),
            (s * 1.05, z - s * 0.2), (s * 1.08, z + 0.02), (s * 0.96, z + 0.02), (s * 0.9, z - s * 0.3), (s * 0.5, z - s * 0.55),
            (0.04, z - s * 0.35), (0.02, z + 0.01)]
    bm = B.add(band(path, prof, mat, closed=False, caps=True))
    # solid end plates, so the open section never shows as a dark hook
    for (p0, p1) in ((path[0], path[1]), (path[-1], path[-2])):
        d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0)).normalized()
        o = Vector((d.y, -d.x, 0))
        ctr = Vector((p0[0], p0[1], 0)) + o * (s * 0.52) + d * 0.005
        half = o * (s * 0.58) + d * 0.012
        lo = Vector((min(ctr.x - half.x, ctr.x + half.x), min(ctr.y - half.y, ctr.y + half.y), z - s * 0.97))
        hi = Vector((max(ctr.x - half.x, ctr.x + half.x), max(ctr.y - half.y, ctr.y + half.y), z + 0.025))
        B.add(cbox2(lo, hi, 0.01, mat))
    return bm


def downpipe(B, pts, r=0.052, mat='pipe', brackets=None, shoe=True):
    """A downpipe along world points (top to bottom), with brackets."""
    B.add(tube(pts, r, mat, sides=7))
    for p in (brackets or []):
        B.add(tube([Vector(p) + Vector((0, 0, 0.035)), Vector(p) - Vector((0, 0, 0.035))], r * 1.3, mat, sides=7, caps=False))


def coping(B, path, ztop, mat='trim', inner=0.24, out=0.07, h=0.1, closed=True):
    prof = [(-0.01, ztop - 0.03), (out, ztop - 0.03), (out, ztop + h * 0.55), (out - 0.035, ztop + h), (-inner + 0.035, ztop + h),
            (-inner, ztop + h * 0.55), (-inner, ztop - 0.03)]
    return B.add(band(path, prof, mat, closed=closed))


def cornice(B, path, z, mat='trim', steps=((0.05, 0.08), (0.1, 0.08), (0.17, 0.12)), closed=False):
    """A stepped moulding: steps (out, height) from the bottom up."""
    prof = [(0.0, z)]
    zz = z
    for o, h in steps:
        prof.append((o, zz)); prof.append((o, zz + h)); zz += h
    prof.append((0.0, zz))
    return B.add(band(path, prof, mat, closed=closed))


def string_course(B, path, z0, z1, out=0.06, mat='trim', closed=False):
    c = min(0.02, (z1 - z0) * 0.3)
    prof = [(0.0, z0), (out - c, z0), (out, z0 + c), (out, z1 - c), (out - c, z1), (0.0, z1)]
    return B.add(band(path, prof, mat, closed=closed))


def plinth(B, path, h, out=0.05, mat='stone', closed=False):
    prof = [(-0.02, 0.0), (out, 0.0), (out, h - 0.035), (out - 0.035, h), (0.0, h)]
    return B.add(band(path, prof, mat, closed=closed))



def ring_path(B, gaps=(), inset=0.0):
    """Paths round the building (counter-clockwise seen from above), split at front gaps (x
    ranges). Returns [(path, closed)]."""
    W, D = B.W, B.D
    hw = W / 2 + inset
    if not gaps:
        return [([(-hw, -inset), (hw, -inset), (hw, D + inset), (-hw, D + inset)], True)]
    gaps = sorted(gaps)
    out = [([(gaps[-1][1], -inset), (hw, -inset), (hw, D + inset), (-hw, D + inset), (-hw, -inset), (gaps[0][0], -inset)], False)]
    for (a, b), (c, d) in zip(gaps[:-1], gaps[1:]):
        out.append(([(b, -inset), (c, -inset)], False))
    return out


def u_path(B, z_back=None, inset=0.0, back=None):
    """Front and both sides: from the left side's back end round the front to the right side's back."""
    W, D = B.W, B.D
    yb = D if back is None else back
    hw = W / 2 + inset
    return [(-hw, yb), (-hw, -inset), (hw, -inset), (hw, yb)]


def shed(B, x0, x1, y0, y1, zf, zb, t=0.12, pitch=0.24, depth=0.04, mat='roof', edge_mat='roofw', fascia_mat='trim',
         soffit='soffit', flash_mat='galvw', feat=True):
    """A ribbed metal single-slope roof from the front edge (y0, zf: top of the ribs' troughs) to
    the back (y1, zb); ribs run down the slope. feat: paint its rib lines and rust into the roof map
    (off for small hoods and canopies under a bigger roof)."""
    mb = MB()
    us = []
    k = math.floor(x0 / pitch) - 1
    while k * pitch < x1 + pitch:
        for fr in (0.0, 0.35, 0.5, 0.85):
            u = k * pitch + fr * pitch
            if x0 < u < x1: us.append(u)
        k += 1
    us = [x0] + sorted(us) + [x1]
    dz = zb - zf

    def zat(y): return zf + (y - y0) / (y1 - y0) * dz
    nrm = Vector((0, -dz, y1 - y0)).normalized()
    for a, b in zip(us[:-1], us[1:]):
        wa, wb = rib_w(a, pitch, depth), rib_w(b, pitch, depth)
        mb.face([(a, y0, zat(y0) + wa), (b, y0, zat(y0) + wb), (b, y1, zat(y1) + wb), (a, y1, zat(y1) + wa)], mat, tuple(nrm))
        mb.face([(a, y0, zat(y0) + wa), (a, y0, zat(y0) - t), (b, y0, zat(y0) - t), (b, y0, zat(y0) + wb)], edge_mat, (0, -1, 0), 0.6)
    mb.face([(x0, y0, zat(y0) - t), (x0, y1, zat(y1) - t), (x1, y1, zat(y1) - t), (x1, y0, zat(y0) - t)], soffit, (0, 0, -1), 0.85)
    for x, sg in ((x0, -1), (x1, 1)):
        mb.face([(x, y0, zat(y0) - t), (x, y0, zat(y0) + depth), (x, y1, zat(y1) + depth), (x, y1, zat(y1) - t)], edge_mat, (sg, 0, 0), 0.7)
    mb.face([(x0, y1, zat(y1) - t), (x1, y1, zat(y1) - t), (x1, y1, zat(y1)), (x0, y1, zat(y1))], edge_mat, (0, 1, 0), 0.7)
    B.add(mb.bm())
    # barge flashings along the sides and a fascia under the front edge
    for x, sg in ((x0, -1), (x1, 1)):
        fb = MB()
        xa, xb = (x - 0.03, x + 0.03)
        za0, za1 = zat(y0 - 0.02) - t - 0.05, zat(y0 - 0.02) + depth + 0.04
        zb0, zb1 = zat(y1) - t - 0.05, zat(y1) + depth + 0.04
        fb.face([(xb if sg > 0 else xa, y0 - 0.02, za0), (xb if sg > 0 else xa, y1, zb0), (xb if sg > 0 else xa, y1, zb1), (xb if sg > 0 else xa, y0 - 0.02, za1)], flash_mat, (sg, 0, 0))
        fb.face([(xa, y0 - 0.02, za1), (xb, y0 - 0.02, za1), (xb, y1, zb1), (xa, y1, zb1)], flash_mat, (0, 0, 1))
        fb.face([(xa, y0 - 0.02, za0), (xb, y0 - 0.02, za0), (xb, y0 - 0.02, za1), (xa, y0 - 0.02, za1)], flash_mat, (0, -1, 0), 0.8)
        fb.face([(xb if sg < 0 else xa, y0 - 0.02, za0), (xb if sg < 0 else xa, y0 - 0.02, za1), (xb if sg < 0 else xa, y1, zb1), (xb if sg < 0 else xa, y1, zb0)], flash_mat, (-sg, 0, 0), 0.7)
        B.add(fb.bm())
    B.add(cbox2((x0, y0 + 0.02, zf - t - 0.16), (x1, y0 + 0.07, zf - t + 0.02), 0.012, fascia_mat))
    if feat: B.feat('roof', 'ribs', x0=x0, x1=x1, y0=y0, y1=y1, pitch=pitch)
    return zb + depth



def chimney(B, x, y, z0, z1, w=0.62, d=0.62, pots=2, cap='conc'):
    """A brick stack from below the roof to z1, a corbel band, a concrete cap and clay pots."""
    B.add(_brick_uv(box((x - w / 2, y - d / 2, z0), (x + w / 2, y + d / 2, z1), 'brick', skip=('-z',)), x, y, w, d, z1))
    B.add(_brick_uv(cbox2((x - w / 2 - 0.03, y - d / 2 - 0.03, z1 - 0.22), (x + w / 2 + 0.03, y + d / 2 + 0.03, z1 - 0.12), 0.012, 'brick'), x, y, w, d, z1))
    B.add(cbox2((x - w / 2 - 0.07, y - d / 2 - 0.07, z1), (x + w / 2 + 0.07, y + d / 2 + 0.07, z1 + 0.1), 0.02, cap))
    for k in range(pots):
        px = x + (k - (pots - 1) / 2) * w * 0.48
        pb, _ = lathe([(0.1, 0.0), (0.1, 0.05), (0.072, 0.09), (0.07, 0.3), (0.092, 0.34), (0.06, 0.36), (0, 0.3)],
                      7, ['pot'] * 6)
        xform(pb, T(px, y, z1 + 0.1)); B.add(pb)
    B.attach.append(('Chimney', (x, y, round(z1 + 0.5, 3))))


def _brick_uv(bm, x, y, w, d, z1):
    lu = L(bm)[3]; bm.normal_update()
    for f in bm.faces:
        ax = max(range(3), key=lambda i: abs(f.normal[i]))
        for l in f.loops:
            co = l.vert.co
            hcoord = co.x - (x - w / 2) if ax != 0 else co.y - (y - d / 2)
            l[lu].uv = reg_uv('brick', hcoord / 0.8, (co.z - (z1 - 2.4)) / 2.4, 0.0)
    return bm
