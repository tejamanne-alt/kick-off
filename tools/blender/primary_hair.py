# The primary-school kids' hair (outfit part 3, follows the Head bone): built like the teens' (teen_hair:
# an under-layer cap on a polar grid plus swept locks, fitted to the built head), with a child's cuts and
# a far smaller triangle budget (each style is about 2.5 to 3.5 thousand triangles).
#   crop   PrimaryBoy:   a neat short cut, a fringe of broad rounded locks, ears free, a small tuft
#   twin   PrimaryGirl:  a centre-parted fringe, locks framing the face, two bunches at the sides with red ties
#   spiky  PrimaryBoy2:  a tousled mass of spikes pointing up, back and forward
#   bob    PrimaryGirl2: a chin-length bob with a straight fringe and a hairband
import math
import numpy as np
import teen_hair as TH
from teen_hair import (Fit, Shell, Mesh, sweep, front_pt, _unit, _ss, _wrap, _bump, _azimuth_fn, _colour_fn, _ring, CC, CR,
                       BASE, SHINE, GROOVE)
from teen_lib import Part
from teen_outfit import lin


def hair_colors(V):
    """Base colour and shine colour (linear). The base colour is the game's default hair colour."""
    return lin(V.hair) + (1,), lin(V.hair_shine) + (1,)


def _groove(V):
    base = lin(V.hair)
    return tuple(c * 0.55 for c in base) + (1,)


def build_hair(V):
    base, shine = hair_colors(V)
    fit = Fit()
    mesh = Mesh(); extra = []
    {'crop': _crop, 'twin': _twin, 'spiky': _spiky, 'bob': _bob}[V.hair_style](V, fit, mesh, extra)
    hair = mesh.build('Hair')
    parts = [Part(hair, _colour_fn(hair, mesh, base, shine, _groove(V)), 3, 'Head')]
    for name, m, colour in extra:           # (things in their own colour: ties, a hairband)
        o = m.build(name)
        parts.append(Part(o, _colour_fn(o, m, colour, colour, colour), 0, 'Head'))
    return parts


def _lock_fn(mesh, fit, sh):
    over = lambda pts, lifts: sh.on(np.array(pts, dtype=np.float64), np.asarray(lifts, dtype=np.float64))
    def lock(pts, w, h, n=8, m=9, shine=None, tip=(0.5, 0.5), clear=0.0, curl=0.45, inner=0.35, root=(0.14, 1.0), grow=1.0):
        """A chunky lock through (x, y or None for the front of the head, z, lift) points; its end is rounded off."""
        P = over([front_pt(x, z, y) for x, y, z, l in pts], [l for x, y, z, l in pts])
        if clear: P = fit.clear(P, clear)
        sweep(mesh, P, [(0, w * 0.55), (0.2, w), (0.55, w * 0.9 * grow), (1, w * 0.62)],
              [(0, h * 0.5), (0.25, h), (0.7, h * 0.85), (1, h * 0.55)], n=n, m=m, inner=inner, curl=curl,
              shine=shine, tip=tip, root=root, tip_rows=0.8)
    return over, lock


def _spike(mesh, sh, base, direction, length, w, bend=(0, 0, 0), lift=-0.004, n=8, m=7, flat=0.8):
    """A pointed tuft standing out of the cap at `base` (a point on or near the head: only its direction from the head's centre
    counts), pointing along `direction`, `length` long and `w` wide, curling by `bend` toward its tip."""
    b = sh.on(np.array([base], dtype=np.float64), np.array([lift]))[0]
    d = _unit(direction); bend = np.asarray(bend, dtype=np.float64)
    pts = [b - d * 0.005, b + d * length * 0.30 + bend * 0.12, b + d * length * 0.68 + bend * 0.45, b + d * length + bend]
    ref = np.array([0.0, -1.0, 0.0]) if abs(d[1]) < 0.72 else np.array([0.0, 0.0, 1.0])
    sweep(mesh, pts, [(0, w), (0.3, w), (1, w * 0.45)], [(0, w * flat), (0.3, w * flat), (1, w * flat * 0.45)],
          n=n, m=m, up=ref, inner=1.0, curl=0.0, tip=(0.35, 1.0), root=(0.12, 1.0), tip_rows=0.5)


def _hairline(extra_front=0.0):
    """The cap's edge for a short cut: a straight front, short sides that free the ears, a low nape (base space)."""
    hl = [(0, -0.140, 1.528 + extra_front), (0, 0.077, 1.33)]
    hl += [(0.03, -0.138, 1.531), (0.06, -0.130, 1.534), (0.088, -0.115, 1.530), (0.108, -0.097, 1.524)]
    hl += [(-0.03, -0.138, 1.531), (-0.06, -0.130, 1.534), (-0.088, -0.115, 1.530), (-0.108, -0.097, 1.524)]
    for sx in (1, -1):
        hl += [(sx * 0.120, -0.080, 1.506), (sx * 0.130, -0.062, 1.484), (sx * 0.138, -0.046, 1.466),
               (sx * 0.143, -0.030, 1.468), (sx * 0.147, -0.012, 1.478), (sx * 0.150, 0.010, 1.481),
               (sx * 0.145, 0.036, 1.462), (sx * 0.132, 0.050, 1.412), (sx * 0.116, 0.058, 1.380),
               (sx * 0.085, 0.065, 1.352), (sx * 0.055, 0.070, 1.336), (sx * 0.026, 0.074, 1.318), (sx * 0.012, 0.076, 1.322)]
    return hl


def _cap_off(full=0.0078, edge=0.0066, taper=0.020):
    def off_fn(D, s, se, a):
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        # a neat cap: a little fuller over the top and the crown, close at the sides and the nape
        o = edge + full * _ss(0.3, 0.92, z) + 0.003 * _ss(-0.2, 0.5, y) * _ss(-0.1, 0.6, z)
        o = o - 0.002 * _ss(0.6, 0.9, np.abs(x)) * _ss(0.3, -0.2, z)
        dist = (se - s) * Shell.R
        e = 0.0009
        return e + (o - e) * _ss(0.0, taper, dist)
    return off_fn


def _creases(angles):
    return [(np.pi / 2 + ang, u0, u1, w, 0.0009) for ang, u0, u1, w in angles]


# ----------------------------------------------------------------------------------- PrimaryBoy: crop
def _crop(V, fit, mesh, extra):
    """A neat short cut: a cap hugging the head to the nape, a straight fringe of broad locks with rounded ends just above
    the brows, short sides that leave the ears free, and a small tuft at the crown."""
    pole = _unit([0.02, 0.40, 0.92])                # the crown whorl
    G = _creases([(-0.3, 0.12, 0.72, 0.0011), (0.55, 0.10, 0.62, 0.001), (1.35, 0.14, 0.72, 0.0011),
                  (2.3, 0.10, 0.62, 0.001), (3.2, 0.14, 0.7, 0.0011), (-1.2, 0.14, 0.66, 0.001)])
    twist = lambda u: 0.25 * _ss(0.0, 0.75, u)
    sh = Shell(mesh, fit, pole, [1, 0, 0], _hairline(), _cap_off(), None, G, na=44, rows=(4, 1, 6), sigma=0.04, twist=twist)
    over, lock = _lock_fn(mesh, fit, sh)
    fr_shine = (lambda Pm: (Pm[:, 2] > 1.525) & (Pm[:, 2] < 1.55), 0.15)
    # --- the fringe: seven broad locks side by side, ending just above the brows (1.44)
    for x0, x1, z1, w in [(0.0, 0.004, 1.476, 0.031), (0.038, 0.044, 1.482, 0.030), (0.074, 0.082, 1.472, 0.029), (0.108, 0.118, 1.486, 0.026),
                          (-0.038, -0.044, 1.479, 0.030), (-0.074, -0.084, 1.488, 0.029), (-0.108, -0.120, 1.474, 0.026)]:
        lock([(x0, -0.062, 1.598, -0.002), (x0 + (x1 - x0) * 0.3, None, 1.552, 0.010), (x1, None, 1.512, 0.008), (x1 * 1.02, None, z1, 0.004)],
             w, 0.0072, shine=fr_shine, tip=(0.6, 0.42))
    # --- in front of the ears, a short side lock each, and over the top of the ear
    for sx in (1, -1):
        lock([(sx * 0.118, -0.04, 1.572, -0.002), (sx * 0.138, -0.050, 1.526, 0.009), (sx * 0.146, -0.048, 1.488, 0.006),
              (sx * 0.146, -0.044, 1.462, 0.004)], 0.016, 0.006, clear=0.004)
        lock([(sx * 0.124, 0.0, 1.584, -0.002), (sx * 0.148, 0.006, 1.534, 0.011), (sx * 0.158, 0.014, 1.494, 0.011),
              (sx * 0.160, 0.022, 1.466, 0.012)], 0.020, 0.0066, clear=0.005)
    # --- the back: short points to the nape
    for x0, x1, x2, ln, w in [(0.0, 0.0, 0.003, 1.332, 0.030), (0.058, 0.070, 0.082, 1.342, 0.028), (-0.058, -0.070, -0.084, 1.34, 0.028),
                              (0.104, 0.122, 0.134, 1.368, 0.024), (-0.104, -0.122, -0.136, 1.37, 0.024)]:
        yb = lambda x: 0.075 + 0.07 * (1 - (abs(x) / 0.16) ** 2)
        lock([(x0, 0.09, 1.57, -0.002), (x1, yb(x1) + 0.03, 1.49, 0.012), (x2, yb(x2), 1.41, 0.011), (x2 * 1.06, yb(x2) - 0.015, ln, 0.014)],
             w, 0.0075, n=8, m=9, clear=0.004, tip=(0.45, 0.8))
    # --- the tuft: two short rounded points at the crown, leaning forward
    Wp = sh.on((pole * 0.1 + CC)[None], 0.0)[0]
    fwd = _unit(np.cross(pole, [1, 0, 0])); side = _unit(np.cross(fwd, pole))
    for (dx, dy, ln, lean, w) in [(0.0, -0.004, 0.030, -0.35, 0.0105), (0.010, 0.004, 0.024, 0.25, 0.0085)]:
        b = Wp + side * dx - fwd * dy - pole * 0.004
        fwdv = _unit(fwd * math.cos(lean) + side * math.sin(lean))
        pts = [b, b + pole * ln * 0.5 + fwdv * ln * 0.10, b + pole * ln * 0.85 + fwdv * ln * 0.45, b + pole * ln * 0.95 + fwdv * ln * 0.95]
        sweep(mesh, pts, [(0, w), (0.45, w * 0.85), (1, w * 0.7)], [(0, w * 0.8), (0.45, w * 0.66), (1, w * 0.5)],
              n=8, m=8, up=fwdv, inner=0.85, curl=0.12, tip=(0.5, 0.8))


# ----------------------------------------------------------------------------------- PrimaryGirl: twin
def _twin(V, fit, mesh, extra):
    """A centre-parted fringe that frames the face, a cap pulled back to two bunches high at the sides of the head,
    each tied with a ring (a hair tie in the accent colour) and falling in a soft curve past the ear."""
    pole = _unit([0.0, 0.34, 0.94])
    hl = _hairline()
    a_front = 1.5 * np.pi
    def band(a):
        al = _wrap(a - a_front)                # 0 at the front, +-pi/2 at the sides
        w = _bump((al + 2.3) / 4.6, 1.2)
        return 1.0 - 0.3 * (al / 2.3) ** 2, 0.075 * w
    G = _creases([(-0.5, 0.2, 0.75, 0.0011), (0.6, 0.18, 0.7, 0.001), (1.5, 0.14, 0.7, 0.0011), (2.5, 0.14, 0.7, 0.001), (3.4, 0.16, 0.7, 0.0011)])
    sh = Shell(mesh, fit, pole, [1, 0, 0], hl, _cap_off(0.0070, 0.0066), band, G, na=44, rows=(4, 1, 6), sigma=0.04)
    over, lock = _lock_fn(mesh, fit, sh)
    fr_shine = (lambda Pm: (Pm[:, 2] > 1.53) & (Pm[:, 2] < 1.555), 0.14)
    # --- the fringe, parted in the middle: each side sweeps outward to the temple
    for sx in (1, -1):
        for x0, x1, z1, w in [(0.012, 0.034, 1.482, 0.030), (0.048, 0.078, 1.470, 0.031), (0.086, 0.116, 1.458, 0.029), (0.118, 0.142, 1.436, 0.024)]:
            lock([(sx * x0, -0.062, 1.60, -0.002), (sx * (x0 + (x1 - x0) * 0.35), None, 1.556, 0.010), (sx * (x0 + (x1 - x0) * 0.75), None, 1.512, 0.008),
                  (sx * x1, None, z1, 0.004)], w, 0.0070, shine=fr_shine, tip=(0.6, 0.45), n=8, m=9)
    # --- locks framing the face, in front of the ears and down to the jaw
    for sx in (1, -1):
        lock([(sx * 0.116, -0.052, 1.55, -0.002), (sx * 0.134, -0.058, 1.50, 0.009), (sx * 0.143, -0.054, 1.44, 0.008),
              (sx * 0.145, -0.048, 1.385, 0.006), (sx * 0.141, -0.042, 1.345, 0.005)], 0.0155, 0.0062, clear=0.004, n=8, m=11, tip=(0.5, 0.7))
    # --- two bunches: tied at the side of the crown, out and down past the ear
    scr = Mesh()
    for sx in (1, -1):
        T = sh.on(np.array([[sx * 0.108, 0.040, 1.512]]), 0.0)[0]
        d = _unit([sx * 0.86, 0.20, 0.46])
        path = [T - d * 0.012, T + d * 0.010, T + d * 0.030, (sx * 0.172, 0.062, 1.514), (sx * 0.208, 0.076, 1.484), (sx * 0.222, 0.088, 1.432),
                (sx * 0.218, 0.096, 1.378), (sx * 0.208, 0.098, 1.334)]
        pw = [(0, 0.0165), (0.08, 0.0172), (0.24, 0.032), (0.5, 0.0385), (0.75, 0.033), (1, 0.021)]
        ph = [(0, 0.0150), (0.08, 0.0155), (0.24, 0.0285), (0.5, 0.0335), (0.75, 0.0285), (1, 0.017)]
        sweep(mesh, path, pw, ph, n=12, m=17, up=_unit([sx * 1.0, 0.3, 0.0]), inner=1.0, curl=0.0, shine=(0.16, 0.5, 0.45), tip=(0.8, 0.5), tip_rows=1.2,
              root=(0.1, 1.0), grooves=[(np.pi / 2 + 1.0, 0.22, 0.88, 0.03), (-0.2, 0.25, 0.85, 0.03)], dents=[(np.pi / 2 + 1.0, 0.05, 0.25), (-0.2, 0.05, 0.25)])
        _ring(scr, T + d * 0.021, d, 0.0200, 0.0092, nt=22, nr=6)
    extra.append(('Ties', scr, lin(V.accent) + (1,)))


# ----------------------------------------------------------------------------------- PrimaryBoy2: spiky
def _spiky(V, fit, mesh, extra):
    """Tousled hair: a full cap, a fringe of pointed locks swept to one side, and a crown of long locks that radiate from the
    whorl and lift off the head at their tips (a spiky silhouette that still flows), a few flicking out at the nape."""
    pole = _unit([0.03, 0.35, 0.94])
    G = _creases([(-0.3, 0.12, 0.7, 0.0011), (0.6, 0.1, 0.62, 0.001), (1.4, 0.14, 0.7, 0.0011), (2.3, 0.1, 0.62, 0.001), (3.3, 0.14, 0.7, 0.0011)])
    sh = Shell(mesh, fit, pole, [1, 0, 0], _hairline(0.004), _cap_off(0.0120, 0.0070), None, G, na=44, rows=(4, 1, 6), sigma=0.04, twist=lambda u: 0.3 * _ss(0, 0.75, u))
    over, lock = _lock_fn(mesh, fit, sh)
    fr_shine = (lambda Pm: (Pm[:, 2] > 1.53) & (Pm[:, 2] < 1.555), 0.15)
    # --- the fringe: pointed locks swept to his right (+X)
    for x0, x1, z1, w in [(-0.104, -0.096, 1.478, 0.026), (-0.068, -0.056, 1.484, 0.029), (-0.032, -0.016, 1.468, 0.030), (0.004, 0.028, 1.476, 0.031),
                          (0.042, 0.072, 1.462, 0.031), (0.082, 0.110, 1.470, 0.028), (0.112, 0.134, 1.452, 0.022)]:
        lock([(x0, -0.062, 1.60, -0.002), (x0 + (x1 - x0) * 0.35, None, 1.556, 0.011), (x0 + (x1 - x0) * 0.75, None, 1.514, 0.009), (x1, None, z1, 0.004)],
             w, 0.0072, shine=fr_shine, tip=(0.5, 0.8), n=8, m=9)
    # --- over and in front of the ears
    for sx in (1, -1):
        lock([(sx * 0.118, -0.04, 1.572, -0.002), (sx * 0.138, -0.050, 1.526, 0.009), (sx * 0.147, -0.048, 1.488, 0.006), (sx * 0.147, -0.044, 1.458, 0.004)],
             0.017, 0.006, clear=0.004, tip=(0.5, 0.8))
    # --- the crown: locks out from the whorl, each lifting off the head toward its tip
    def radial(a, s1, lifts, w, h=0.0085, turn=0.3):
        n = len(lifts)
        se = float(sh.SE(a))
        ss = np.linspace(0.06, min(s1, se * 0.93), n)
        aa = a + turn * np.linspace(0, 1, n)
        D = sh.dirs(ss, aa)
        P = sh.on(CC + D * 0.16, np.asarray(lifts, dtype=np.float64))
        sweep(mesh, P, [(0, w * 0.6), (0.2, w), (0.62, w * 0.9), (1, w * 0.5)], [(0, h * 0.5), (0.25, h), (0.7, h * 0.8), (1, h * 0.45)],
              n=8, m=9, inner=0.4, curl=0.4, tip=(0.45, 0.85), root=(0.14, 1.0), tip_rows=0.6)
    lifts = [-0.002, 0.005, 0.015, 0.031, 0.054]
    for a, s1, w in [(0.2, 0.95, 0.034), (0.95, 0.9, 0.033), (1.7, 0.95, 0.034), (2.5, 0.9, 0.033), (3.25, 0.95, 0.034),
                     (3.95, 0.8, 0.032), (4.75, 0.75, 0.031), (5.5, 0.82, 0.032)]:
        radial(a, s1, lifts, w)
    radial(1.2, 0.55, [-0.002, 0.010, 0.027, 0.050], 0.029, turn=-0.25)       # two shorter ones standing on top
    radial(4.4, 0.5, [-0.002, 0.010, 0.026, 0.046], 0.028, turn=-0.25)
    # --- flicking out at the nape
    for x0, x1, x2, ln, fl in [(0.0, 0.0, 0.004, 1.33, 0.024), (0.058, 0.07, 0.082, 1.342, 0.026), (-0.058, -0.07, -0.084, 1.34, 0.025),
                               (0.104, 0.124, 0.138, 1.37, 0.028), (-0.104, -0.124, -0.14, 1.372, 0.028)]:
        yb = lambda x: 0.075 + 0.07 * (1 - (abs(x) / 0.16) ** 2)
        lock([(x0, 0.09, 1.57, -0.002), (x1, yb(x1) + 0.03, 1.49, 0.014), (x2, yb(x2), 1.41, 0.014), (x2 * 1.08, yb(x2) - 0.02, ln, fl)],
             0.030, 0.0078, n=8, m=9, clear=0.004, tip=(0.45, 0.9))


# ----------------------------------------------------------------------------------- PrimaryGirl2: bob
def _bob(V, fit, mesh, extra):
    """A chin-length bob: the cap runs down over the ears to the jaw and round to a low nape, thick at its edge; a straight
    fringe of broad locks; a hairband across the crown."""
    pole = _unit([0.0, 0.30, 0.95])
    hl = [(0, -0.140, 1.526), (0, 0.082, 1.262)]
    hl += [(0.06, -0.133, 1.532), (0.10, -0.108, 1.522), (-0.06, -0.133, 1.532), (-0.10, -0.108, 1.522)]
    for sx in (1, -1):
        hl += [(sx * 0.128, -0.075, 1.474), (sx * 0.146, -0.050, 1.404), (sx * 0.152, -0.028, 1.338), (sx * 0.150, -0.002, 1.296),
               (sx * 0.141, 0.028, 1.272), (sx * 0.122, 0.054, 1.258), (sx * 0.090, 0.072, 1.254), (sx * 0.045, 0.079, 1.254)]
    def off_fn(D, s, se, a):
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        o = 0.0125 + 0.007 * _ss(0.3, 0.92, z) + 0.005 * _ss(0.4, 1.0, np.abs(x)) * _ss(0.1, -0.5, z)     # fuller over the top and at the sides
        dist = (se - s) * Shell.R
        e = 0.0085                                               # (the edge stays thick: a bob's blunt hem)
        return e + (o - e) * _ss(0.0, 0.035, dist)
    G = _creases([(-0.4, 0.2, 0.8, 0.0011), (0.5, 0.2, 0.8, 0.001), (1.4, 0.2, 0.8, 0.0011), (2.4, 0.2, 0.8, 0.001), (3.3, 0.2, 0.8, 0.0011)])
    a_front = 1.5 * np.pi
    def band(a):
        al = _wrap(a - a_front)
        w = _bump((al + 2.3) / 4.6, 1.2)
        return 1.0 - 0.25 * (al / 2.3) ** 2, 0.07 * w
    sh = Shell(mesh, fit, pole, [1, 0, 0], hl, off_fn, band, G, na=48, rows=(4, 1, 7), sigma=0.045)
    over, lock = _lock_fn(mesh, fit, sh)
    fr_shine = None
    # --- a straight fringe of broad, softly rounded locks
    for x0, z1, w in ([] if getattr(V, 'no_fringe', False) else       # (Mia: pulled back under the headband)
                      [(0.0, 1.478, 0.034), (0.042, 1.482, 0.032), (0.082, 1.474, 0.030), (0.116, 1.466, 0.026),
                       (-0.042, 1.480, 0.032), (-0.082, 1.476, 0.030), (-0.116, 1.468, 0.026)]):
        lock([(x0, -0.062, 1.60, -0.002), (x0 * 1.02, None, 1.554, 0.011), (x0 * 1.06, None, 1.512, 0.009), (x0 * 1.10, None, z1, 0.005)],
             w, 0.0075, shine=fr_shine, tip=(0.7, 0.35), n=8, m=9)
    # --- locks framing the face, down in front of the ears to the chin
    for sx in (1, -1):
        lock([(sx * 0.114, -0.060, 1.56, -0.002), (sx * 0.136, -0.070, 1.505, 0.013), (sx * 0.148, -0.062, 1.43, 0.015),
              (sx * 0.152, -0.050, 1.36, 0.015), (sx * 0.148, -0.040, 1.305, 0.013)], 0.021, 0.0072, clear=0.004, n=8, m=11, tip=(0.65, 0.5))
    # --- the hairband: a yellow band over the crown from ear to ear, just behind the fringe
    bandm = Mesh()
    pts = [(-0.152, 0.030, 1.440), (-0.146, 0.014, 1.505), (-0.112, -0.008, 1.562), (-0.060, -0.026, 1.595), (0.0, -0.032, 1.604),
           (0.060, -0.026, 1.595), (0.112, -0.008, 1.562), (0.146, 0.014, 1.505), (0.152, 0.030, 1.440)]
    P = sh.on(np.array(pts), np.full(len(pts), 0.0062))
    from teen_body import catmull
    P = catmull(P, 40)
    sweep(bandm, P, [(0, 0.0105), (1, 0.0105)], [(0, 0.0040), (1, 0.0040)], n=8, m=24, inner=1.0, curl=0.0, tip=(0.97, 0.5), root=None, root_cap=True)
    extra.append(('Hairband', bandm, lin(V.accent) + (1,)))
