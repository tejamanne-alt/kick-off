# Paints the faces of the two playable teens into the atlas: layered almond eyes (sclera with
# a soft lid shadow, a gradient iris, pupil, highlights, a tapered lash line and a fine lid
# crease), brows, a small nose shadow, the mouth, blush and her freckles. His face is in the
# hand-drawn style of 1990s anime films: tall dark eyes that are nearly all iris with one bright
# highlight under a heavy lid line, thin slanted brows, and blush drawn as a few short hatched
# lines; and his hair's strand texture is painted in the hair tile (HAIR_TILE).
#
# Atlas layout (2048 square): the face is a straight front projection into the upper-left
# quadrant, u = x/0.34 + 0.5, v = (z - 1.27)/0.34 in head (base) space, matching
# teen_head.face_uv(); the rest of the left half is plain skin (the back of the head samples
# it); the bottom-right corner is plain white for the vertex-coloured parts; beside it, the
# hair tile (HAIR_TILE) holds the boy's strand texture.
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
SKIN_LINEAR = {True: (0.89, 0.6, 0.42), False: (0.88, 0.62, 0.47)}
# The hair tile (u0, v0, u1, v1 in atlas UV): strand texture, multiplied over the hair's colours. u runs across a lock
# (or round the crown), v from the root to the tip (or from the crown to the hairline): teen_hair lays it out.
HAIR_TILE = (0.525, 0.03, 0.725, 0.47)
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
    """Eye shapes are in eye units (hw = half the eye's width); brows in metres from the eye
    centre (x outward, z up)."""
    if girl:   # larger, slightly tall almond eyes with a lash flick; freckles
        return dict(
            eye_x=0.059, eye_z=1.432, hw=0.0300,
            upper=((-1.0, -0.1), (-0.7, 1.02), (0.48, 1.12), (1.0, 0.24)),
            lower=((-1.0, -0.1), (-0.55, -0.86), (0.58, -0.8), (1.0, 0.24)),
            iris=(0.03, 0.08, 0.64, 0.8),
            iris_top=(36, 22, 18), iris_mid=(74, 46, 32), iris_bot=(116, 74, 46), iris_glow=(132, 84, 52),
            pupil=(20, 12, 10), hl=1.0,
            lash=(30, 20, 19), lash_w=(0.0014, 0.0042, 0.0058, 0.0034), flick=True,
            lower_lash=(110, 66, 54), lower_a=0.85, crease=(190, 128, 104),
            brow=((-0.0225, 0.0425), (-0.007, 0.0505), (0.014, 0.0548), (0.0305, 0.0442)),
            brow_w=((0.0, 0.0046), (0.33, 0.0042), (0.66, 0.0026), (1.0, 0.0003)),
            brow_col=(48, 32, 28),
            blush=((-0.076, 1.382, 0.022, 0.011), (0.076, 1.382, 0.022, 0.011), (240, 128, 116), 0.36),
            mouth='smile', mouth_z=1.337, mouth_col=(146, 70, 62), mouth_k=1.2, mouth_w=1.0,
            nose_z=1.389, nose_len=0.0165, nose_bend=0.0012, nose_a=0.55)
    # boy: tall, dark eyes that are nearly all iris (near-black, a hint of warm brown low down) with one bright
    # highlight, under a heavy dark lid line that reaches a little past the outer corner; a faint lower lid and no
    # crease; thin, straight-ish brows slanting up and out; blush drawn as short hatched lines; a small nose and a
    # small smile. (The look of hand-drawn 1990s anime films: simple, clean shapes that read at a small size.)
    return dict(
        eye_x=0.058, eye_z=1.43, hw=0.0268,
        upper=((-1.0, -0.06), (-0.62, 0.98), (0.48, 1.06), (1.0, 0.22)),
        lower=((-1.0, -0.06), (-0.52, -0.82), (0.56, -0.78), (1.0, 0.22)),
        iris=(0.06, 0.04, 0.6, 0.98),
        iris_top=(14, 11, 14), iris_mid=(22, 16, 18), iris_bot=(40, 27, 24), iris_glow=(50, 33, 28),
        pupil=(6, 5, 7), hl=0.9, hl2=False, hl_same_side=True,
        lash=(14, 13, 20), lash_w=(0.0013, 0.0042, 0.0052, 0.0046), flick=False,
        lower_lash=(120, 82, 72), lower_a=0.45, crease=(186, 124, 98), crease_a=0.0,
        brow=((-0.0235, 0.0452), (-0.008, 0.0498), (0.013, 0.0514), (0.0315, 0.048)),
        brow_w=((0.0, 0.0033), (0.4, 0.0031), (0.75, 0.0023), (1.0, 0.0007)),
        brow_col=(22, 22, 34),
        blush=((-0.075, 1.385, 0.02, 0.0095), (0.075, 1.385, 0.02, 0.0095), (232, 140, 130), 0.22),
        hatch=dict(x=0.075, z=1.386, n=3, gap=0.0052, length=0.0105, angle=62, width=0.0011, col=(212, 92, 92), a=0.8),
        plaster=False,
        mouth='smile', mouth_z=1.334, mouth_col=(138, 70, 64), mouth_k=0.92, mouth_w=1.0,
        nose_z=1.388, nose_len=0.016, nose_bend=0.0004, nose_a=0.45)


def _eye(pp, sp, sx):
    """One eye. sx = +1 for the character's left (+X), -1 for the right."""
    cx, cz, hw = sp['eye_x'] * sx, sp['eye_z'], sp['hw']
    def E(u, w): return (cx + sx * u * hw, cz + w * hw)       # eye-local units (hw) -> face metres
    up = _bez(*[E(*p) for p in sp['upper']], n=90)
    lo = _bez(*[E(*p) for p in sp['lower']], n=90)
    opening = pp.poly(list(map(tuple, up)) + list(map(tuple, lo[::-1])))
    eh = max(p[1] for p in sp['upper']) - min(p[1] for p in sp['lower'])     # eye height (hw units)

    # sclera: clean white, a narrow soft shadow just under the upper lash line
    pp.fill(opening, (247, 245, 247))
    sh = pp.blur(pp.stroke(up, np.full(len(up), hw * eh * 0.24)), hw * 0.06)
    pp.fill(ImageChops.multiply(sh, opening), (222, 215, 230), 0.75)
    c = pp.blur(pp.ellipse(*E(-1.0, 0.0), hw * 0.16, hw * 0.3), hw * 0.08)        # a hint of the inner corner
    pp.fill(ImageChops.multiply(c, opening), (236, 222, 224), 0.5)

    # iris: dark at the top, lighter toward the bottom, a crisp darker rim and a warm crescent below
    iu, iw, irx, irz = sp['iris']
    icx, icz = E(iu, iw); rx, rz = irx * hw, irz * hw
    iris = ImageChops.multiply(pp.ellipse(icx, icz, rx, rz), opening)
    top, mid, bot = sp['iris_top'], sp['iris_mid'], sp['iris_bot']
    rim = tuple(int(c * 0.6) for c in mid)
    def irisc(X, Z):
        t = (icz + rz - Z) / (2 * rz)          # 0 top .. 1 bottom
        c = np.where((t < 0.5)[..., None], _mix(top, mid, t / 0.5), _mix(mid, bot, (t - 0.5) / 0.5))
        r = np.sqrt(((X - icx) / rx) ** 2 + ((Z - icz) / rz) ** 2)
        return _mix(c, rim, (r - 0.86) / 0.07)
    pp.fill_fn(iris, irisc)
    # the lid's shadow across the top of the iris
    pp.fill(ImageChops.multiply(pp.blur(pp.stroke(up, np.full(len(up), hw * 0.42)), hw * 0.08), iris), (40, 24, 20), 0.35)
    # a warm, light crescent in the lower third
    cres = ImageChops.subtract(pp.ellipse(icx, icz - rz * 0.2, rx * 0.74, rz * 0.62),
                               pp.ellipse(icx, icz + rz * 0.1, rx * 0.86, rz * 0.66))
    pp.fill(ImageChops.multiply(pp.blur(cres, hw * 0.05), iris), sp['iris_glow'], 0.85)
    # pupil
    pup = ImageChops.multiply(pp.ellipse(icx, icz + rz * 0.06, rx * 0.4, rz * 0.42), opening)
    pp.fill(pup, sp['pupil'])
    # highlights: a big one upper-outer, a small one lower-inner
    k = sp['hl']
    hx = -1.0 if sp.get('hl_same_side') else sx      # the highlight toward the light: the same side in both eyes, or outward
    hl = pp.ellipse(icx + hx * rx * 0.36, icz + rz * 0.36, rx * 0.33 * k, rz * 0.3 * k)
    pp.fill(ImageChops.multiply(hl, opening), (255, 255, 255))
    if sp.get('hl2', True):
        hs = pp.ellipse(icx - sx * rx * 0.4, icz - rz * 0.5, rx * 0.14, rz * 0.13)
        pp.fill(ImageChops.multiply(hs, opening), (255, 253, 250), 0.95)

    # upper lash line: thin at the inner corner, heavy toward the outer part
    t = np.linspace(0, 1, len(up))
    w0, w1, w2, w3 = sp['lash_w']
    if sp['flick']:
        # tapers into the corner; a single flick leaves the lid's outer part and lifts outward
        wid = _prof(t, [(0, w0), (0.35, w1), (0.78, w2), (0.92, w2 * 0.8), (1.0, w3)])
        pp.fill(pp.stroke(up, wid, cap=(True, False)), sp['lash'])
        i0 = int(len(up) * 0.7)
        p0 = up[i0]; d0 = up[i0 + 1] - up[i0 - 1]; d0 = d0 / np.linalg.norm(d0)
        tip = up[-1] + np.array([sx * hw * 0.36, hw * 0.34])
        fl = _bez(p0, p0 + d0 * hw * 0.22, tip - np.array([sx * hw * 0.16, hw * 0.1]), tip, n=40)
        tt = np.linspace(0, 1, len(fl))
        # the flick's lower edge runs along the lid line, so the corner stays one clean shape
        m = pp.stroke(fl - np.array([0, w2 * 0.12]), _prof(tt, [(0, w2), (0.4, w2 * 0.92), (1, 0.0)]))
        pp.fill(m, sp['lash'])
    else:
        # flatter and a little heavier, ending bluntly (no flick, no tail)
        wid = _prof(t, [(0, w0), (0.3, w1), (0.75, w2), (1.0, w3)])
        pp.fill(pp.stroke(up, wid, cap=(True, True)), sp['lash'])
    # short lower lash hint under the outer part of the lower lid, starting inside the corner
    seg = lo[int(len(lo) * 0.55):int(len(lo) * 0.87)]
    tt = np.linspace(0, 1, len(seg))
    pp.fill(pp.stroke(seg - np.array([0, hw * 0.035]), _prof(tt, [(0, 0.0), (0.35, 0.0011), (0.8, 0.0012), (1, 0.0)])),
            sp['lower_lash'], sp['lower_a'])
    # fine lid crease above the lash line
    cr = up[int(len(up) * 0.22):int(len(up) * 0.86)] + np.array([0, hw * 0.3])
    tt = np.linspace(0, 1, len(cr))
    if sp.get('crease_a', 0.9) > 0:
        pp.fill(pp.stroke(cr, _prof(tt, [(0, 0.0), (0.3, 0.00075), (0.75, 0.0009), (1, 0.0)])), sp['crease'], sp.get('crease_a', 0.9))


def _brow(pp, sp, sx):
    """A brow: fuller at the inner end, a soft arch, tapering to a fine tail."""
    cx, cz = sp['eye_x'] * sx, sp['eye_z']
    c = _bez(*[(cx + sx * dx, cz + dz) for dx, dz in sp['brow']], n=80)
    t = np.linspace(0, 1, len(c))
    pp.fill(pp.stroke(c, _prof(t, list(sp['brow_w'])), cap=(True, True)), sp['brow_col'])


def _nose(pp, sp):
    """A soft wedge of shadow down the shaded (+X) side of the button nose, a small soft
    shadow under its tip and a pale catch-light on the tip: no outline."""
    z, L, bend, a = sp['nose_z'], sp['nose_len'], sp['nose_bend'], sp['nose_a']
    side = _bez((0.0022, z + L * 0.82), (0.0036 + bend, z + L * 0.5), (0.0052 + bend, z + L * 0.16), (0.0046, z - 0.0018), n=40)
    t = np.linspace(0, 1, len(side))
    m = pp.stroke(side, _prof(t, [(0, 0.0), (0.4, 0.0022), (0.85, 0.003), (1, 0.0016)]), cap=(False, True))
    pp.fill(pp.blur(m, 0.0011), (222, 162, 144), a)
    tip = pp.blur(pp.ellipse(0.0012, z - 0.0052, 0.0046, 0.0015), 0.0008)
    pp.fill(tip, (214, 150, 132), a * 0.85)
    hl = pp.blur(pp.ellipse(-0.0016, z - 0.0004, 0.0019, 0.0014), 0.0007)
    pp.fill(hl, (255, 248, 242), 0.55)


def _mouth(pp, sp):
    z, col, k, mw = sp['mouth_z'], sp['mouth_col'], sp['mouth_k'], sp['mouth_w']
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
        pp.fill(pp.stroke(c, _prof(t, [(0, 0.0005 * mw), (0.2, 0.0013 * mw), (0.55, 0.0017 * mw), (0.85, 0.0015 * mw), (1, 0.0008 * mw)]),
                          cap=(True, True)), col)
        dark = tuple(int(v * 0.72) for v in col)
        tick = _bez2((0.0114, z + 0.0068), (0.0131, z + 0.0064), (0.0139, z + 0.005), (0.0136, z + 0.0032), n=24)
        tt = np.linspace(0, 1, len(tick))
        pp.fill(pp.stroke(tick, _prof(tt, [(0, 0.0), (0.45, 0.0012), (1, 0.0003)])), dark, 0.95)
        ll = _bez2((-0.004, z - 0.0058), (-0.0015, z - 0.0071), (0.0025, z - 0.007), (0.005, z - 0.0055), n=40)
        tl = np.linspace(0, 1, len(ll))
        pp.fill(pp.blur(pp.stroke(ll, _prof(tl, [(0, 0.0), (0.5, 0.0012), (1, 0.0)])), 0.0005), (226, 168, 150), 0.5)


def _blush(pp, sp):
    e1, e2, col, a = sp['blush']
    m = pp.blank()
    for (bx, bz, rx, rz) in (e1, e2):      # right (-X) and left (+X) cheek
        m = ImageChops.lighter(m, pp.ellipse(bx, bz, rx, rz))
    pp.fill(pp.blur(m, 0.0055), col, a)


def _hatch(pp, sp):
    """Blush drawn as a few short parallel lines on each cheek (///), all leaning the same way, over the soft blush."""
    h = sp.get('hatch')
    if not h: return
    m = pp.blank()
    ang = math.radians(h['angle'])
    d = np.array([math.cos(ang), math.sin(ang)]); nrm = np.array([1.0, 0.0])
    for sx in (1, -1):
        c = np.array([sx * h['x'], h['z']])
        for i in range(h['n']):
            o = c + nrm * (i - (h['n'] - 1) / 2) * h['gap']
            L = h['length'] * (0.85 if i == h['n'] - 1 else 1.0)
            pts = np.stack([o + d * t for t in np.linspace(-L / 2, L / 2, 24)])
            tt = np.linspace(0, 1, len(pts))
            m = ImageChops.lighter(m, pp.stroke(pts, _prof(tt, [(0, h['width'] * 0.3), (0.3, h['width']), (0.7, h['width']), (1, h['width'] * 0.3)]), cap=(True, True)))
    pp.fill(pp.blur(m, 0.0002), h['col'], h['a'])


def _hair_tile(atlas):
    """The boy's hair texture, multiplied over the hair's colours: near white, with the fine dark lines that part hair
    into strands running along the locks (u across, v from the root up to the tip), a few longer and darker where the
    clumps part, and a soft shade at the roots where locks overlap. Mirrored at u = 0 and 1 (the lock wraps it both ways)."""
    u0, v0, u1, v1 = HAIR_TILE
    x0, x1 = int(round(u0 * S)), int(round(u1 * S)); y0, y1 = int(round((1 - v1) * S)), int(round((1 - v0) * S))
    W, H = (x1 - x0) * 2, (y1 - y0) * 2            # drawn at 2x
    rng = np.random.RandomState(5)
    v = np.linspace(1, 0, H)[:, None]              # 0 at the root (the tile's bottom), 1 at the tip
    base = 0.96 - 0.16 * _ss01(0.22, 0.0, v)        # the roots a little darker
    im = np.repeat(np.repeat(base, W, 1)[..., None], 3, 2) * 255.0
    canvas = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(canvas)
    def line(u, va, vb, width, val, wave):
        ts = np.linspace(va, vb, 60)
        xs = (u + wave * np.sin(ts * 7.0 + u * 11.0)) * W; ys = (1 - ts) * H
        for i in range(len(ts) - 1):
            f = min(1.0, (ts[i] - va) / 0.08, (vb - ts[i]) / 0.12)          # tapered ends
            wdt = max(1, int(round(width * max(f, 0.15))))
            g = int(round(255 * (1 - (1 - val) * max(f, 0.3))))
            d.line([(xs[i], ys[i]), (xs[i + 1], ys[i + 1])], fill=(g, g, int(min(255, g * 1.04))), width=wdt)
    # the clump partings: long, darker lines
    for u in (0.13, 0.29, 0.44, 0.58, 0.73, 0.88):
        u += rng.uniform(-0.02, 0.02)
        line(u, rng.uniform(0.0, 0.18), rng.uniform(0.72, 0.97), W * 0.012, rng.uniform(0.46, 0.58), 0.008)
    # finer strands between them
    for u in np.linspace(0.06, 0.95, 13):
        u += rng.uniform(-0.015, 0.015)
        line(u, rng.uniform(0.05, 0.35), rng.uniform(0.55, 0.9), W * 0.005, rng.uniform(0.74, 0.84), 0.006)
    canvas = canvas.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    atlas.paste(canvas, (x0, y0))


def _ss01(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _freckles(pp):
    """Her signature: a light dusting in a loose arc over each cheekbone just under the lower
    lid, and a few across the bridge above the nose tip. Round soft dots of varied size."""
    rng = np.random.RandomState(11)
    dots = []
    def ok(x, z, gap):
        return all((x - gx) ** 2 + (z - gz) ** 2 > gap ** 2 for gx, gz, _ in dots)
    for sx in (1, -1):
        n = 0; tries = 0
        while n < 8 and tries < 4000:
            tries += 1
            t = rng.uniform(0, 1)
            x = 0.05 + 0.042 * t                                  # along the arc, inner to outer
            z = 1.394 + 0.008 * math.sin(math.pi * (0.25 + 0.6 * t)) + rng.uniform(-0.0038, 0.0038)
            x += rng.uniform(-0.003, 0.003)
            if ok(sx * x, z, 0.0062):
                dots.append((sx * x, z, rng.uniform(0.00085, 0.00165))); n += 1
    n = 0; tries = 0
    while n < 5 and tries < 4000:
        tries += 1
        x = rng.uniform(-0.019, 0.019); z = rng.uniform(1.404, 1.414)
        if ok(x, z, 0.0058):
            dots.append((x, z, rng.uniform(0.0008, 0.0013))); n += 1
    for (x, z, rad) in dots:
        m = pp.ellipse(x, z, rad, rad * rng.uniform(0.82, 1.0), rot=rng.uniform(0, 3), n=28)
        pp.fill(pp.blur(m, 0.00025), (199, 133, 102), rng.uniform(0.6, 0.75))


def _plaster(pp):
    """A sticking plaster across his left cheek: beige strip, paler pad, a few vent dots."""
    cx, cz, ang = 0.072, 1.389, math.radians(-24)
    L2, W2 = 0.0194, 0.0072
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
    pp.fill(sh, (176, 120, 90), 0.5)
    pp.fill(rrect(L2 + 0.0004, W2 + 0.0004, W2 * 0.75), (190, 150, 118))          # edge
    pp.fill(rrect(L2, W2, W2 * 0.72), (250, 236, 214))                            # strip (pale, on his tan)
    pp.fill(rrect(L2 * 0.36, W2 * 0.86, W2 * 0.3), (255, 250, 242))               # pad
    pp.fill(rrect(L2 * 0.36, W2 * 0.86, W2 * 0.3).filter(ImageFilter.FIND_EDGES), (226, 204, 178), 0.6)
    for end in (1, -1):
        for i in (0, 1):
            for j in (-1, 0, 1):
                u = end * (L2 * 0.56 + i * 0.0051); w = j * 0.0029
                pp.fill(pp.ellipse(*R(u, w), 0.0006, 0.0006, n=16), (214, 186, 150), 0.9)
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
    w = _prof(np.linspace(0, 1, 90), [(0, 0.0), (0.12, 0.0009), (0.7, 0.0009), (1, 0.0)])
    fill(blur(stroke(arc, w), 0.0003), tuple(int(c * f) for c, f in zip(skin, (0.86, 0.66, 0.62))), 0.9)
    # the antihelix: a soft inner ridge line
    ah = _bez((0.0062, 0.0135), (0.0068, 0.004), (0.0045, -0.006), (0.0008, -0.0125), n=50)
    fill(blur(stroke(ah, _prof(np.linspace(0, 1, 50), [(0, 0.0), (0.3, 0.001), (1, 0.0)])), 0.0003),
         tuple(int(c * f) for c, f in zip(skin, (0.9, 0.72, 0.68))), 0.8)
    im = im.resize((n // SS, n // SS), Image.LANCZOS)
    atlas.paste(im, (int((cu - half * sc) * S), int((1 - cv - half * sc) * S)))


def paint(path, girl):
    from teen_lib import Variant
    if isinstance(girl, Variant): return girl.mod('face').paint(path, girl)
    skin = skin_rgb(girl)
    sp = _spec(girl)
    pp = Painter(skin)
    _blush(pp, sp)
    _hatch(pp, sp)
    if girl: _freckles(pp)
    elif sp.get('plaster', True): _plaster(pp)
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
    if not girl: _hair_tile(atlas)
    atlas.save(path)


if __name__ == '__main__':
    paint(sys.argv[1], '--girl' in sys.argv)
