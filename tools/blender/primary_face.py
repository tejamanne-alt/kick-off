# Paints the four primary-school kids' faces into their atlases (2048 square, laid out like the teens':
# the face in the upper-left quadrant through teen_head.face_uv, the ears' folds in the upper-right
# quadrant, a plain white corner the flat-coloured parts sample). The painting is face_teen's (layered
# almond eyes with a gradient iris, lash line and highlights, brows, a nose hint, a mouth, blush); this
# gives it a child's proportions: bigger, rounder eyes set low on a rounder face, a tiny nose and mouth,
# round blushes, a little face-specific character each (freckles, a gap-toothed grin, calm lashes).
#   boy1   dark round eyes, straight brows, a small grin
#   girl1  big warm-brown eyes with a lash flick, freckles, a small smile
#   boy2   dark eyes (behind round glasses), a wide cheerful grin
#   girl2  calm hazel eyes with long lashes, a beauty mark, a soft smile
import math
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import face_teen as FT
from face_teen import Painter, _eye, _brow, _nose, _mouth, _blush, _ear_art, _bez, _prof, S


def _spec(face):
    """Eye shapes are in eye units (hw = half the eye's width); brows in metres from the eye centre
    (x outward, z up). Same keys as face_teen._spec."""
    girl_eye = dict(
        upper=((-1.0, -0.05), (-0.72, 1.08), (0.50, 1.18), (1.0, 0.20)),
        lower=((-1.0, -0.05), (-0.60, -0.95), (0.60, -0.88), (1.0, 0.20)),
        iris=(0.02, 0.05, 0.72, 0.90), pupil=(22, 12, 10), hl=1.15,
        lash=(34, 22, 20), lash_w=(0.0014, 0.0044, 0.0060, 0.0036), flick=True,
        lower_lash=(110, 66, 54), lower_a=0.8, crease=(196, 136, 112))
    boy_eye = dict(
        upper=((-1.0, -0.05), (-0.66, 0.92), (0.52, 1.0), (1.0, 0.16)),
        lower=((-1.0, -0.05), (-0.55, -0.80), (0.56, -0.74), (1.0, 0.16)),
        iris=(0.02, 0.04, 0.72, 0.84), pupil=(16, 10, 9), hl=1.0,
        lash=(28, 20, 20), lash_w=(0.0016, 0.0046, 0.0060, 0.0048), flick=False,
        lower_lash=(112, 70, 56), lower_a=0.7, crease=(190, 128, 102))
    if face == 'girl1':
        return dict(girl_eye, eye_x=0.064, eye_z=1.395, hw=0.0345,
                    iris_top=(52, 28, 18), iris_mid=(104, 62, 36), iris_bot=(156, 100, 58), iris_glow=(176, 118, 66),
                    brow=((-0.0235, 0.0455), (-0.008, 0.0525), (0.014, 0.0555), (0.0315, 0.0455)),
                    brow_w=((0.0, 0.0046), (0.33, 0.0042), (0.66, 0.0027), (1.0, 0.0003)), brow_col=(52, 34, 28),
                    blush=((-0.081, 1.350, 0.0235, 0.0125), (0.081, 1.350, 0.0235, 0.0125), (240, 120, 112), 0.42),
                    mouth='smile', mouth_z=1.338, mouth_col=(150, 70, 64), mouth_k=1.2, mouth_w=1.0,
                    nose_z=1.368, nose_len=0.012, nose_bend=0.0008, nose_a=0.45)
    if face == 'girl2':
        return dict(girl_eye, eye_x=0.063, eye_z=1.396, hw=0.0335,
                    upper=((-1.0, -0.05), (-0.74, 0.96), (0.52, 1.06), (1.0, 0.10)),
                    lower=((-1.0, -0.05), (-0.60, -0.84), (0.60, -0.80), (1.0, 0.10)),
                    iris_top=(36, 40, 24), iris_mid=(96, 84, 44), iris_bot=(150, 130, 70), iris_glow=(170, 148, 84),
                    lash_w=(0.0014, 0.0046, 0.0066, 0.0040),
                    brow=((-0.0235, 0.0432), (-0.008, 0.0482), (0.014, 0.0505), (0.0315, 0.0415)),
                    brow_w=((0.0, 0.0044), (0.33, 0.0040), (0.66, 0.0026), (1.0, 0.0003)), brow_col=(28, 22, 24),
                    blush=((-0.080, 1.351, 0.0230, 0.0120), (0.080, 1.351, 0.0230, 0.0120), (214, 112, 100), 0.34),
                    mouth='smile', mouth_z=1.339, mouth_col=(138, 66, 58), mouth_k=1.15, mouth_w=1.0,
                    nose_z=1.369, nose_len=0.012, nose_bend=0.0006, nose_a=0.42)
    if face == 'mia':                               # dark brown eyes, a small smile; no freckles, no mark
        return dict(girl_eye, eye_x=0.063, eye_z=1.396, hw=0.0345,
                    iris_top=(30, 18, 12), iris_mid=(70, 42, 26), iris_bot=(112, 72, 44), iris_glow=(132, 86, 52),
                    brow=((-0.0235, 0.0445), (-0.008, 0.0510), (0.014, 0.0535), (0.0315, 0.0440)),
                    brow_w=((0.0, 0.0046), (0.33, 0.0042), (0.66, 0.0027), (1.0, 0.0003)), brow_col=(30, 20, 18),
                    blush=((-0.080, 1.350, 0.0230, 0.0120), (0.080, 1.350, 0.0230, 0.0120), (200, 104, 92), 0.30),
                    mouth='smile', mouth_z=1.339, mouth_col=(132, 62, 56), mouth_k=1.15, mouth_w=1.0,
                    nose_z=1.368, nose_len=0.012, nose_bend=0.0006, nose_a=0.42)
    if face == 'boy2':
        return dict(boy_eye, eye_x=0.062, eye_z=1.397, hw=0.0300,
                    iris_top=(20, 14, 12), iris_mid=(46, 30, 22), iris_bot=(80, 54, 36), iris_glow=(96, 64, 40),
                    brow=((-0.0255, 0.0392), (-0.009, 0.0432), (0.012, 0.0440), (0.0310, 0.0402)),
                    brow_w=((0.0, 0.0072), (0.4, 0.0068), (0.75, 0.0052), (1.0, 0.0024)), brow_col=(40, 26, 18),
                    blush=((-0.080, 1.352, 0.0225, 0.0115), (0.080, 1.352, 0.0225, 0.0115), (196, 90, 76), 0.30),
                    mouth='half', mouth_z=1.346, mouth_col=(122, 58, 48), mouth_k=2.0, mouth_w=1.3,
                    nose_z=1.368, nose_len=0.013, nose_bend=0.0004, nose_a=0.5)
    return dict(boy_eye, eye_x=0.062, eye_z=1.396, hw=0.0310,                      # boy1
                iris_top=(26, 18, 14), iris_mid=(54, 36, 28), iris_bot=(88, 58, 40), iris_glow=(104, 68, 46),
                brow=((-0.0250, 0.0382), (-0.009, 0.0428), (0.012, 0.0436), (0.0308, 0.0390)),
                brow_w=((0.0, 0.0070), (0.4, 0.0066), (0.75, 0.0050), (1.0, 0.0022)), brow_col=(30, 24, 26),
                blush=((-0.080, 1.350, 0.0230, 0.0118), (0.080, 1.350, 0.0230, 0.0118), (232, 118, 100), 0.30),
                mouth='half', mouth_z=1.339, mouth_col=(124, 62, 52), mouth_k=1.3, mouth_w=1.25,
                nose_z=1.368, nose_len=0.013, nose_bend=0.0004, nose_a=0.5)


def _freckles(pp, n=7, seed=5):
    """A light dusting over each cheekbone just under the lower lid, and a few over the nose."""
    rng = np.random.RandomState(seed)
    dots = []
    def ok(x, z, gap):
        return all((x - gx) ** 2 + (z - gz) ** 2 > gap ** 2 for gx, gz, _ in dots)
    for sx in (1, -1):
        k = 0; tries = 0
        while k < n and tries < 4000:
            tries += 1
            t = rng.uniform(0, 1)
            x = 0.052 + 0.044 * t
            z = 1.355 + 0.008 * math.sin(math.pi * (0.25 + 0.6 * t)) + rng.uniform(-0.0042, 0.0042)
            x += rng.uniform(-0.003, 0.003)
            if ok(sx * x, z, 0.0066):
                dots.append((sx * x, z, rng.uniform(0.0009, 0.0017))); k += 1
    k = 0; tries = 0
    while k < 4 and tries < 4000:
        tries += 1
        x = rng.uniform(-0.018, 0.018); z = rng.uniform(1.368, 1.378)
        if ok(x, z, 0.006):
            dots.append((x, z, rng.uniform(0.0008, 0.0013))); k += 1
    for (x, z, rad) in dots:
        m = pp.ellipse(x, z, rad, rad * rng.uniform(0.82, 1.0), rot=rng.uniform(0, 3), n=28)
        pp.fill(pp.blur(m, 0.00025), (196, 128, 98), rng.uniform(0.6, 0.75))


def _mole(pp, x, z, r=0.0017):
    m = pp.ellipse(x, z, r, r, n=24)
    pp.fill(pp.blur(m, 0.0003), (92, 58, 44), 0.9)


def _grin(pp, sp):
    """A wide open smile: a dark half-moon with a lighter tongue and a row of teeth above it."""
    z = sp['mouth_z']; k = sp['mouth_k']
    kz = 1.0
    top = _bez((-0.0125 * k, z + 0.0030), (-0.005 * k, z + 0.0012), (0.005 * k, z + 0.0012), (0.0125 * k, z + 0.0030), n=40)
    bot = _bez((0.0125 * k, z + 0.0030), (0.0090 * k, z - 0.0150 * kz), (-0.0090 * k, z - 0.0150 * kz), (-0.0125 * k, z + 0.0030), n=40)
    m = pp.poly(list(map(tuple, top)) + list(map(tuple, bot)))
    pp.fill(m, sp['mouth_col'])
    tongue = ImageChops.multiply(m, pp.ellipse(0.0, z - 0.0112, 0.0072 * k, 0.0042, n=40))
    pp.fill(tongue, (214, 112, 108))
    teeth = ImageChops.multiply(m, pp.poly([(-0.0108 * k, z + 0.0034), (0.0108 * k, z + 0.0034), (0.0098 * k, z - 0.0006), (-0.0098 * k, z - 0.0006)]))
    pp.fill(teeth, (250, 246, 240))
    outline = _bez((-0.0125 * k, z + 0.0030), (-0.005 * k, z + 0.0012), (0.005 * k, z + 0.0012), (0.0125 * k, z + 0.0030), n=40)
    pp.fill(pp.stroke(outline, _prof(np.linspace(0, 1, 40), [(0, 0.0004), (0.5, 0.0013), (1, 0.0004)])), tuple(int(v * 0.8) for v in sp['mouth_col']))


def paint(path, V):
    skin = tuple(int(round(255 * c)) for c in V.skin)
    sp = _spec(V.face)
    pp = Painter(skin)
    _blush(pp, sp)
    if V.face == 'girl1': _freckles(pp)
    _nose(pp, sp)
    if V.face == 'boy2': _grin(pp, sp)
    else: _mouth(pp, sp)
    for sx in (1, -1):
        _eye(pp, sp, sx)
        _brow(pp, sp, sx)
    if V.face == 'girl2': _mole(pp, -0.044, 1.348)
    atlas = Image.new('RGB', (S, S), skin)
    atlas.paste(pp.finish(), (FT.CROP[0], FT.CROP[1]))
    _ear_art(atlas, skin)
    d = ImageDraw.Draw(atlas)
    d.rectangle([S * 3 // 4, S * 3 // 4, S - 1, S - 1], fill=(255, 255, 255))   # WHITE_UV corner
    atlas.save(path)
