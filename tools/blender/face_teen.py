# Paints the faces of the two playable teens into the atlas: layered almond eyes (sclera with
# a soft lid shadow, a gradient iris, pupil, two highlights, a tapered lash line and a fine lid
# crease), brows, a small nose shadow, the mouth, blush, her freckles and his sticking plaster.
#
# Atlas layout (2048 square): the face is a straight front projection into the upper-left
# quadrant, u = x/0.34 + 0.5, v = (z - 1.27)/0.34 in head (base) space, matching
# teen_head.face_uv(); the rest of the left half is plain skin (the back of the head samples
# it); the bottom-right corner is plain white for the vertex-coloured parts.
#
# Everything is drawn 4x oversize in face metres and downscaled with LANCZOS, so lines are
# clean and anti-aliased. Colours are display (sRGB) values. The skin is the sRGB encoding of
# the body's skin vertex colour (vertex colours are linear), so face, ears and neck match.
#   python face_teen.py out.png [--girl]
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 2048          # atlas size
Q = S // 2        # the face quadrant
SS = 4            # supersampling
CROP = (130, 200, 900, 1000)   # the part of the quadrant that holds painted features (px)
SKIN_LINEAR = {True: (1.0, 0.88, 0.8), False: (0.96, 0.82, 0.7)}
# The ears' drawing in the upper-right quadrant: centre (u, v) and UV units per metre of the
# ear's own side projection (teen_head.ear_uv): local y (front -, back +), local z (up).
EAR_UV = (0.75, 0.75, 3.0)


def _srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def skin_rgb(girl):
    """The face's skin: the body's skin vertex colour (linear) encoded to sRGB bytes."""
    lin = SKIN_LINEAR[girl]
    try:
        import teen_outfit
        lin = tuple(teen_outfit.palette(girl)['skin'][:3])
    except Exception:
        pass
    return tuple(int(round(255 * _srgb(v))) for v in lin)


def _bez(p0, p1, p2, p3, n=72):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def _prof(t, keys):
    """Piecewise-smooth profile through (t, value) keys."""
    ts = [k[0] for k in keys]; vs = [k[1] for k in keys]
    out = np.empty_like(t)
    for i, tt in enumerate(t):
        if tt <= ts[0]: out[i] = vs[0]; continue
        if tt >= ts[-1]: out[i] = vs[-1]; continue
        j = max(k for k in range(len(ts) - 1) if ts[k] <= tt)
        f = (tt - ts[j]) / (ts[j + 1] - ts[j]); f = f * f * (3 - 2 * f)
        out[i] = vs[j] + (vs[j + 1] - vs[j]) * f
    return out


class Painter:
    def __init__(self, skin):
        self.x0, self.y0, self.x1, self.y1 = CROP
        self.w = (self.x1 - self.x0) * SS; self.h = (self.y1 - self.y0) * SS
        self.im = Image.new('RGB', (self.w, self.h), skin)
        self.k = Q / 0.34 * SS        # px per metre

    # face metres -> canvas pixels
    def P(self, x, z):
        u = x / 0.34 + 0.5; v = (z - 1.27) / 0.34
        return ((u * Q - self.x0) * SS, ((1 - v) * Q - self.y0) * SS)

    def px(self, m): return m * self.k

    def blank(self): return Image.new('L', (self.w, self.h), 0)

    def poly(self, pts):
        m = self.blank(); ImageDraw.Draw(m).polygon([self.P(*p) for p in pts], fill=255); return m

    def ellipse(self, cx, cz, rx, rz, rot=0.0, n=96):
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        c, s = math.cos(rot), math.sin(rot)
        ex, ez = rx * np.cos(a), rz * np.sin(a)
        return self.poly(list(zip(cx + ex * c - ez * s, cz + ex * s + ez * c)))

    def stroke(self, pts, widths, cap=(False, False)):
        """A filled polygon around a centre line with per-point widths (metres)."""
        pts = np.asarray(pts, float); w = np.asarray(widths, float)
        tg = np.gradient(pts, axis=0); tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-12)
        nm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        left = pts + nm * w[:, None] / 2; right = pts - nm * w[:, None] / 2
        outline = list(map(tuple, left))
        if cap[1] and w[-1] > 0:
            a0 = math.atan2(nm[-1, 1], nm[-1, 0])
            for a in np.linspace(a0, a0 - math.pi, 12)[1:-1]:
                outline.append((pts[-1, 0] + math.cos(a) * w[-1] / 2, pts[-1, 1] + math.sin(a) * w[-1] / 2))
        outline += list(map(tuple, right[::-1]))
        if cap[0] and w[0] > 0:
            a0 = math.atan2(-nm[0, 1], -nm[0, 0])
            for a in np.linspace(a0, a0 - math.pi, 12)[1:-1]:
                outline.append((pts[0, 0] + math.cos(a) * w[0] / 2, pts[0, 1] + math.sin(a) * w[0] / 2))
        return self.poly(outline)

    def blur(self, m, metres):
        return m.filter(ImageFilter.GaussianBlur(self.px(metres)))

    def fill(self, m, col, a=1.0):
        if a < 1.0: m = m.point(lambda v: int(v * a + 0.5))
        self.im.paste(tuple(col), (0, 0), m)

    def fill_fn(self, m, fn, a=1.0):
        """Fill through mask m with colours fn(X, Z) (arrays of face metres) -> (..., 3)."""
        bb = m.getbbox()
        if not bb: return
        x0, y0, x1, y1 = bb
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(float) + 0.5
        X = (xs / SS + self.x0) / Q; X = (X - 0.5) * 0.34
        Z = (1 - (ys / SS + self.y0) / Q) * 0.34 + 1.27
        col = np.clip(fn(X, Z), 0, 255).astype(np.uint8)
        tile = Image.fromarray(col, 'RGB')
        mm = m.crop(bb)
        if a < 1.0: mm = mm.point(lambda v: int(v * a + 0.5))
        self.im.paste(tile, (x0, y0), mm)

    def finish(self):
        return self.im.resize((self.x1 - self.x0, self.y1 - self.y0), Image.LANCZOS)


def _mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


# ------------------------------------------------------------------ the characters
def _spec(girl):
    if girl:
        return dict(
            eye_x=0.056, eye_z=1.432, hw=0.0285,
            upper=((-1.0, -0.1), (-0.7, 1.02), (0.48, 1.12), (1.03, 0.22)),
            lower=((-1.0, -0.1), (-0.55, -0.86), (0.58, -0.8), (1.03, 0.22)),
            iris=(0.03, 0.08, 0.64, 0.8),
            iris_top=(70, 40, 27), iris_mid=(128, 82, 51), iris_bot=(192, 136, 76), iris_ring=(70, 42, 28),
            pupil=(38, 21, 15), lash=(48, 29, 24), lash_w=(0.0012, 0.0036, 0.0054, 0.0056), flick=True,
            lower_lash=(122, 76, 62), lower_a=0.9, crease=(206, 148, 134),
            brow=((-0.88, 1.5), (-0.25, 1.84), (0.55, 1.8), (1.2, 1.44)), brow_w=(0.0036, 0.0033, 0.0009),
            brow_col=(112, 62, 42),
            blush=(0.074, 1.386, 0.021, 0.0105, (255, 146, 140), 0.42),
            mouth='smile', mouth_z=1.344, mouth_col=(160, 80, 72), mouth_k=1.2,
            nose_z=1.392)
    return dict(
        eye_x=0.056, eye_z=1.43, hw=0.0272,
        upper=((-1.0, -0.06), (-0.62, 0.84), (0.48, 0.94), (1.03, 0.16)),
        lower=((-1.0, -0.06), (-0.5, -0.72), (0.56, -0.66), (1.03, 0.16)),
        iris=(0.03, 0.08, 0.64, 0.72),
        iris_top=(46, 27, 19), iris_mid=(82, 51, 33), iris_bot=(140, 94, 58), iris_ring=(42, 25, 17),
        pupil=(26, 15, 11), lash=(42, 29, 25), lash_w=(0.0012, 0.0034, 0.0047, 0.0042), flick=False,
        lower_lash=(136, 94, 80), lower_a=0.7, crease=(202, 150, 130),
        brow=((-0.98, 1.4), (-0.3, 1.6), (0.5, 1.62), (1.2, 1.46)), brow_w=(0.0062, 0.0058, 0.0024),
        brow_col=(50, 35, 30),
        blush=(0.075, 1.384, 0.02, 0.01, (240, 140, 130), 0.18),
        mouth='half', mouth_z=1.339, mouth_col=(142, 78, 68), mouth_k=1.2,
        nose_z=1.39)


def _eye(pp, sp, sx):
    """One eye. sx = +1 for the character's left (+X), -1 for the right."""
    cx, cz, hw = sp['eye_x'] * sx, sp['eye_z'], sp['hw']
    def E(u, w): return (cx + sx * u * hw, cz + w * hw)       # eye-local units (hw) -> face metres
    up = _bez(*[E(*p) for p in sp['upper']], n=90)
    lo = _bez(*[E(*p) for p in sp['lower']], n=90)
    opening = pp.poly(list(map(tuple, up)) + list(map(tuple, lo[::-1])))

    # sclera: warm off-white, a soft cool shadow under the upper lid and in the corners
    pp.fill(opening, (252, 250, 247))
    sh = pp.blur(pp.stroke(up, np.full(len(up), hw * 0.62)), hw * 0.16)
    pp.fill(ImageChops.multiply(sh, opening), (205, 196, 214), 0.75)
    for u in (-0.95, 1.0):
        c = pp.blur(pp.ellipse(*E(u, 0.05), hw * 0.28, hw * 0.5), hw * 0.12)
        pp.fill(ImageChops.multiply(c, opening), (222, 212, 222), 0.6)

    # iris: dark at the top, warm and light toward the bottom, a darker rim
    iu, iw, irx, irz = sp['iris']
    icx, icz = E(iu, iw); rx, rz = irx * hw, irz * hw
    iris = ImageChops.multiply(pp.ellipse(icx, icz, rx, rz), opening)
    top, mid, bot = sp['iris_top'], sp['iris_mid'], sp['iris_bot']
    def irisc(X, Z):
        t = (icz + rz - Z) / (2 * rz)          # 0 top .. 1 bottom
        c = np.where((t < 0.5)[..., None], _mix(top, mid, t / 0.5), _mix(mid, bot, (t - 0.5) / 0.5))
        r = np.sqrt(((X - icx) / rx) ** 2 + ((Z - icz) / rz) ** 2)
        return _mix(c, sp['iris_ring'], (r - 0.78) / 0.2)
    pp.fill_fn(iris, irisc)
    # the lid's shadow across the top of the iris
    pp.fill(ImageChops.multiply(pp.blur(pp.stroke(up, np.full(len(up), hw * 0.5)), hw * 0.1), iris), (40, 24, 20), 0.35)
    # a warm glow in the lower iris
    glow = pp.blur(pp.ellipse(icx, icz - rz * 0.48, rx * 0.62, rz * 0.3), hw * 0.08)
    pp.fill(ImageChops.multiply(glow, iris), tuple(min(255, int(c * 1.12) + 12) for c in bot), 0.55)
    # pupil
    pup = ImageChops.multiply(pp.ellipse(icx, icz + rz * 0.06, rx * 0.4, rz * 0.42), opening)
    pp.fill(pup, sp['pupil'])
    # highlights: a big one upper-outer, a small one lower-inner
    hl = pp.ellipse(icx + sx * rx * 0.36, icz + rz * 0.36, rx * 0.33, rz * 0.3)
    pp.fill(ImageChops.multiply(hl, opening), (255, 255, 255))
    hs = pp.ellipse(icx - sx * rx * 0.4, icz - rz * 0.5, rx * 0.14, rz * 0.13)
    pp.fill(ImageChops.multiply(hs, opening), (255, 253, 250), 0.95)

    # upper lash line: thin at the inner corner, heavy toward the outer corner
    t = np.linspace(0, 1, len(up))
    w0, w1, w2, w3 = sp['lash_w']
    wid = _prof(t, [(0, w0), (0.35, w1), (0.8, w2), (1.0, w3)])
    pp.fill(pp.stroke(up, wid, cap=(True, False)), sp['lash'])
    ox, oz = up[-1]
    if sp['flick']:   # a small outer flick: leaves the lash line before the corner and lifts
        i0 = int(len(up) * 0.74)
        p0 = up[i0]
        tip = up[-1] + np.array([sx * hw * 0.34, hw * 0.36])
        fl = _bez(p0, p0 + np.array([sx * hw * 0.16, -hw * 0.02]), tip - np.array([sx * hw * 0.14, hw * 0.08]), tip, n=40)
        tt = np.linspace(0, 1, len(fl))
        pp.fill(pp.stroke(fl, _prof(tt, [(0, w2), (0.45, w3 * 0.85), (1, 0.0)])), sp['lash'])
        # fill the corner between the lid and the flick with a soft concave edge
        j = int(len(fl) * 0.55)
        c0 = up[-1]; c1 = fl[j]
        ctrl = np.array([c0[0] + sx * hw * 0.16, c0[1] + hw * 0.02])
        tq = np.linspace(0, 1, 16)[:, None]
        edge = (1 - tq) ** 2 * c0 + 2 * (1 - tq) * tq * ctrl + tq ** 2 * c1
        pp.fill(pp.poly(list(map(tuple, up[i0:])) + list(map(tuple, edge[1:])) + list(map(tuple, fl[j:0:-1]))), sp['lash'])
    else:             # a short tapered tail past the outer corner (reads in profile)
        d = up[-1] - up[-8]; d /= np.linalg.norm(d)
        tail = _bez(up[-10], up[-1] - d * hw * 0.02, up[-1] + d * hw * 0.06 + np.array([sx * hw * 0.05, 0.0]),
                    up[-1] + np.array([sx * hw * 0.16, -hw * 0.01]), n=30)
        pp.fill(pp.stroke(tail, _prof(np.linspace(0, 1, 30), [(0, w2), (0.45, w3), (1, 0.0)])), sp['lash'])
    # short lower lash hint under the outer part of the lower lid
    seg = lo[int(len(lo) * 0.56):int(len(lo) * 0.93)]
    tt = np.linspace(0, 1, len(seg))
    pp.fill(pp.stroke(seg - np.array([0, hw * 0.035]), _prof(tt, [(0, 0.0), (0.35, 0.0011), (0.8, 0.0012), (1, 0.0003)])),
            sp['lower_lash'], sp['lower_a'])
    # fine lid crease above the lash line
    cr = up[int(len(up) * 0.22):int(len(up) * 0.86)] + np.array([0, hw * 0.3])
    tt = np.linspace(0, 1, len(cr))
    pp.fill(pp.stroke(cr, _prof(tt, [(0, 0.0), (0.3, 0.00075), (0.75, 0.0009), (1, 0.0)])), sp['crease'], 0.9)


def _brow(pp, sp, sx):
    cx, cz, hw = sp['eye_x'] * sx, sp['eye_z'], sp['hw']
    def E(u, w): return (cx + sx * u * hw, cz + w * hw)
    c = _bez(*[E(*p) for p in sp['brow']], n=80)
    t = np.linspace(0, 1, len(c))
    a, b, e = sp['brow_w']
    pp.fill(pp.stroke(c, _prof(t, [(0, a), (0.4, b), (1, e)]), cap=(True, True)), sp['brow_col'])


def _nose(pp, sp):
    """A small soft wedge of shadow on the right (-X) side of the button nose, a hint of
    the nostril under the tip and a faint shadow below it."""
    z = sp['nose_z']
    side = _bez((-0.0026, z + 0.0125), (-0.0058, z + 0.0068), (-0.0068, z + 0.0012), (-0.0046, z - 0.0042), n=40)
    t = np.linspace(0, 1, len(side))
    m = pp.stroke(side, _prof(t, [(0, 0.0), (0.45, 0.0019), (0.85, 0.0021), (1, 0.0008)]))
    pp.fill(pp.blur(m, 0.0006), (218, 156, 138), 0.85)
    tip = _bez((-0.0046, z - 0.0045), (-0.0024, z - 0.0062), (0.0012, z - 0.0062), (0.0032, z - 0.0046), n=30)
    pp.fill(pp.blur(pp.stroke(tip, _prof(np.linspace(0, 1, 30), [(0, 0.0012), (0.5, 0.0011), (1, 0.0)])), 0.0004),
            (206, 142, 124), 0.75)
    under = pp.blur(pp.ellipse(0.0, z - 0.0085, 0.0048, 0.0013), 0.0009)
    pp.fill(under, (230, 176, 158), 0.4)


def _mouth(pp, sp):
    z, col, k = sp['mouth_z'], sp['mouth_col'], sp['mouth_k']
    def _bez2(*pts, n=72):   # the mouth's curves, scaled by mouth_k about its centre
        return _bez(*[(p[0] * k, z + (p[1] - z) * k) for p in pts], n=n)
    if sp['mouth'] == 'smile':
        c = _bez2((-0.0118, z + 0.0036), (-0.0052, z - 0.0026), (0.0052, z - 0.0026), (0.0118, z + 0.0036), n=80)
        t = np.linspace(0, 1, len(c))
        pp.fill(pp.stroke(c, _prof(t, [(0, 0.0004), (0.18, 0.0013), (0.5, 0.0018), (0.82, 0.0013), (1, 0.0004)])), col)
        # a soft lower-lip hint
        ll = _bez2((-0.0048, z - 0.0052), (-0.002, z - 0.0068), (0.002, z - 0.0068), (0.0048, z - 0.0052), n=40)
        tl = np.linspace(0, 1, len(ll))
        pp.fill(pp.blur(pp.stroke(ll, _prof(tl, [(0, 0.0), (0.5, 0.0013), (1, 0.0)])), 0.0005), (232, 160, 150), 0.6)
    else:   # his half-smile: the left (+X) corner lifts
        c = _bez2((-0.0112, z + 0.0006), (-0.004, z - 0.0026), (0.0046, z - 0.0024), (0.0122, z + 0.0046), n=80)
        t = np.linspace(0, 1, len(c))
        pp.fill(pp.stroke(c, _prof(t, [(0, 0.0004), (0.2, 0.0013), (0.55, 0.0017), (0.85, 0.0014), (1, 0.0006)])), col)
        tick = _bez2((0.0117, z + 0.0074), (0.0133, z + 0.0068), (0.014, z + 0.0052), (0.0137, z + 0.0034), n=24)
        tt = np.linspace(0, 1, len(tick))
        pp.fill(pp.stroke(tick, _prof(tt, [(0, 0.0), (0.45, 0.0009), (1, 0.0)])), col, 0.8)
        ll = _bez2((-0.004, z - 0.0058), (-0.0015, z - 0.0071), (0.0025, z - 0.007), (0.005, z - 0.0055), n=40)
        tl = np.linspace(0, 1, len(ll))
        pp.fill(pp.blur(pp.stroke(ll, _prof(tl, [(0, 0.0), (0.5, 0.0012), (1, 0.0)])), 0.0005), (226, 168, 150), 0.5)


def _blush(pp, sp):
    bx, bz, rx, rz, col, a = sp['blush']
    m = pp.blank()
    for sx in (1, -1):
        m = ImageChops.lighter(m, pp.ellipse(sx * bx, bz, rx, rz))
    pp.fill(pp.blur(m, 0.0055), col, a)


def _freckles(pp):
    """A light dusting over the nose bridge and the upper cheeks: scattered (not in rows),
    denser toward the middle of each patch, a little irregular in size and strength."""
    rng = np.random.RandomState(5)
    # patches: centre x, z, radii, count
    patches = [(0.0, 1.4035, 0.012, 0.0045, 6), (0.047, 1.3995, 0.026, 0.0085, 13), (-0.047, 1.3995, 0.026, 0.0085, 13)]
    dots = []
    for (px_, pz, rx, rz, n) in patches:
        tries = 0
        got = []
        while len(got) < n and tries < 4000:
            tries += 1
            a = rng.uniform(0, 2 * math.pi); r = math.sqrt(rng.uniform(0, 1)) ** 1.3
            x = px_ + r * rx * math.cos(a); z = pz + r * rz * math.sin(a)
            if all((x - gx) ** 2 + (z - gz) ** 2 > 0.0034 ** 2 for gx, gz, _ in got + dots):
                got.append((x, z, r))
        dots += got
    for (x, z, r) in dots:
        rad = rng.uniform(0.0008, 0.00125) * (1.0 - 0.25 * r)
        m = pp.ellipse(x, z, rad, rad * rng.uniform(0.78, 1.0), rot=rng.uniform(0, 3), n=24)
        pp.fill(pp.blur(m, 0.0002), (190, 116, 86), (0.78 - 0.3 * r) * rng.uniform(0.85, 1.0))


def _plaster(pp):
    """A sticking plaster across his left cheek: beige strip, paler pad, a few vent dots."""
    cx, cz, ang = 0.071, 1.383, math.radians(-24)
    L2, W2 = 0.0172, 0.0064
    c, s = math.cos(ang), math.sin(ang)
    def R(u, w): return (cx + u * c - w * s, cz + u * s + w * c)
    def rrect(hl, hw, r, n=10):
        pts = []
        for (ux, wy, a0) in ((hl - r, hw - r, 0), (-hl + r, hw - r, 90), (-hl + r, -hw + r, 180), (hl - r, -hw + r, 270)):
            for a in np.linspace(math.radians(a0), math.radians(a0 + 90), n):
                pts.append(R(ux + r * math.cos(a), wy + r * math.sin(a)))
        return pp.poly(pts)
    # a soft contact shadow so it reads as stuck on
    sh = pp.blur(rrect(L2 + 0.0006, W2 + 0.0006, W2 * 0.8), 0.0009)
    pp.fill(sh, (206, 160, 136), 0.5)
    pp.fill(rrect(L2 + 0.0004, W2 + 0.0004, W2 * 0.75), (196, 150, 112))          # edge
    pp.fill(rrect(L2, W2, W2 * 0.72), (234, 197, 152))                            # strip
    pp.fill(rrect(L2 * 0.36, W2 * 0.86, W2 * 0.3), (248, 230, 204))               # pad
    pp.fill(rrect(L2 * 0.36, W2 * 0.86, W2 * 0.3).filter(ImageFilter.FIND_EDGES), (226, 200, 168), 0.6)
    for end in (1, -1):
        for i in (0, 1):
            for j in (-1, 0, 1):
                u = end * (L2 * 0.56 + i * 0.0046); w = j * 0.0026
                pp.fill(pp.ellipse(*R(u, w), 0.00055, 0.00055, n=16), (208, 168, 124), 0.9)
    # a light catch along the top edge
    hl = _bez(R(-L2 * 0.8, W2 * 0.55), R(-L2 * 0.3, W2 * 0.62), R(L2 * 0.3, W2 * 0.62), R(L2 * 0.8, W2 * 0.55), n=40)
    pp.fill(pp.stroke(hl, _prof(np.linspace(0, 1, 40), [(0, 0.0), (0.5, 0.0009), (1, 0.0)])), (250, 228, 196), 0.6)


def _ear_art(atlas, skin):
    """The ear's folds, drawn in ear-local metres (y front-/back+, z up) at 4x."""
    cu, cv, sc = EAR_UV
    half = 0.05                                   # drawn area: +-5 cm round the ear centre
    n = int(2 * half * sc * S) * SS
    im = Image.new('RGB', (n, n), skin)
    k = n / (2 * half)
    def P(y, z): return ((y + half) * k, (half - z) * k)
    def poly(pts):
        m = Image.new('L', (n, n), 0); ImageDraw.Draw(m).polygon([P(*p) for p in pts], fill=255); return m
    def stroke(pts, w):
        pts = np.asarray(pts, float); tg = np.gradient(pts, axis=0)
        tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-12)
        nm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        return poly(list(map(tuple, pts + nm * w[:, None] / 2)) + list(map(tuple, (pts - nm * w[:, None] / 2)[::-1])))
    def blur(m, metres): return m.filter(ImageFilter.GaussianBlur(metres * k))
    def fill(m, col, a=1.0):
        if a < 1: m = m.point(lambda v: int(v * a + 0.5))
        im.paste(col, (0, 0), m)
    sh = tuple(int(c * f) for c, f in zip(skin, (0.94, 0.78, 0.76)))
    a = np.linspace(0, 2 * math.pi, 80)
    concha = poly(list(zip(-0.0025 + 0.0088 * np.cos(a), -0.006 + 0.0135 * np.sin(a))))
    fill(blur(concha, 0.0018), sh, 0.75)
    # the helix's inner fold: an arc from the front of the top, over and down the back
    t = np.radians(np.linspace(128, -62, 90))
    arc = np.stack([0.0142 * np.cos(t), 0.0242 * np.sin(t) + 0.001], 1)
    w = _prof(np.linspace(0, 1, 90), [(0, 0.0), (0.12, 0.0013), (0.7, 0.0013), (1, 0.0)])
    fill(blur(stroke(arc, w), 0.0003), tuple(int(c * f) for c, f in zip(skin, (0.86, 0.66, 0.62))), 0.9)
    # the antihelix: a soft inner ridge line
    ah = _bez((0.0062, 0.0135), (0.0068, 0.004), (0.0045, -0.006), (0.0008, -0.0125), n=50)
    fill(blur(stroke(ah, _prof(np.linspace(0, 1, 50), [(0, 0.0), (0.3, 0.001), (1, 0.0)])), 0.0003),
         tuple(int(c * f) for c, f in zip(skin, (0.9, 0.72, 0.68))), 0.8)
    im = im.resize((n // SS, n // SS), Image.LANCZOS)
    atlas.paste(im, (int((cu - half * sc) * S), int((1 - cv - half * sc) * S)))


def paint(path, girl):
    skin = skin_rgb(girl)
    sp = _spec(girl)
    pp = Painter(skin)
    _blush(pp, sp)
    if girl: _freckles(pp)
    else: _plaster(pp)
    _nose(pp, sp)
    _mouth(pp, sp)
    for sx in (1, -1):
        _eye(pp, sp, sx)
        _brow(pp, sp, sx)
    atlas = Image.new('RGB', (S, S), skin)
    atlas.paste(pp.finish(), (CROP[0], CROP[1]))
    _ear_art(atlas, skin)
    d = ImageDraw.Draw(atlas)
    d.rectangle([S * 3 // 4, S * 3 // 4, S - 1, S - 1], fill=(255, 255, 255))   # WHITE_UV corner
    atlas.save(path)


if __name__ == '__main__':
    paint(sys.argv[1], '--girl' in sys.argv)
