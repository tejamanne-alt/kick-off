# The primary-school kids' heads (see primary_spec.py): teen_head's implicit head with a younger
# shape (a rounder face with full cheeks, a short lower face and a small round chin), the ears,
# and what sits on the face (round glasses for PrimaryBoy2).
import math
import numpy as np


def shape(V):
    """Shape parameters for teen_head.head_sdf (see teen_head._shape): the front outline's half-widths by
    height (base z), and how the jaw, chin, nape and nose sit. A child's head: cheeks stay full right
    down to the mouth, the lower face is short, the chin small and round."""
    girl = bool(V.girl)
    w = V.head_width
    return dict(width=tuple((z, v * w) for z, v in ((1.46, 0.1463), (1.44, 0.1478), (1.42, 0.1465), (1.40, 0.1425),
                                                    (1.38, 0.1375), (1.36, 0.1320), (1.34, 0.1250), (1.32, 0.1150),
                                                    (1.30, 0.1010), (1.285, 0.0820), (1.27, 0.0560), (1.255, 0.0250))),
                taper_front=0.03,
                nape=(0.40, 1.41, 1.335), funnel=0.5,
                fwd=(0.010, 1.38, 1.27), down=0.0,
                floor=(1.262, 0.85, 2.0, -0.05), back=(20.0, 0.07), fk=0.025,
                nose=((0, -0.1625, 1.378), (0.0085, 0.011, 0.011)), nk=0.008)


# ---------------------------------------------------------------- what sits on the face
def extras(V):
    """Parts that go with the head: round glasses (PrimaryBoy2)."""
    return _glasses(V) if getattr(V, 'glasses', None) else []


def _glasses(V):
    """Round glasses: two rings in front of the eyes, a bridge over the nose and two temples back over the ears, all
    resting a few millimetres off the built head (base space, bound to the Head bone)."""
    from mathutils import Vector
    from teen_hair import Fit, _unit
    from teen_lib import Part
    from teen_outfit import tube, ellipse_profile, lin
    from teen_body import catmull
    import primary_face
    fit = Fit()
    sp = primary_face._spec(V.face)
    ex, ez = sp['eye_x'], sp['eye_z']
    def on_face(x, z, lift):
        loc, nrm, idx, dist = fit.head.ray_cast(Vector((x, -0.45, z)), Vector((0, 1, 0)), 0.8)
        n = np.array(nrm); return np.array(loc) + n * lift, n
    colour = tuple(lin(V.glasses)) + (1,)
    parts = []
    R = 0.0375                                  # the ring's radius to the middle of its rim
    rim = ellipse_profile(0.0044, 0.0046, 5)
    for s in (1, -1):
        c, n = on_face(s * ex, ez, 0.0105)
        up = np.array([0.0, 0.0, 1.0]); u = _unit(np.cross(up, n)); w = np.cross(n, u)
        th = np.linspace(0, 2 * math.pi, 22, endpoint=False)
        D = np.cos(th)[:, None] * u + np.sin(th)[:, None] * w
        P = c + D * R
        N = np.tile(n, (len(P), 1))
        parts.append(Part(tube('Rim' + ('L' if s > 0 else 'R'), P, D, N, rim, None), colour, 0, 'Head'))
    # the bridge over the nose
    pts = []
    for x in (0.0285, 0.014, 0.0, -0.014, -0.0285):
        p, n = on_face(x, ez + 0.008 + 0.006 * (1 - abs(x) / 0.0285), 0.0092); pts.append(p)
    pts = np.array(pts)
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    U = np.cross(T, [0, 0, 1.0]); U /= np.linalg.norm(U, axis=1)[:, None]
    Wv = np.cross(U, T)
    parts.append(Part(tube('Bridge', pts, U, Wv, ellipse_profile(0.0034, 0.0034, 5), None, False), colour, 0, 'Head'))
    # the temples
    for s in (1, -1):
        pts = [on_face(s * (ex + R + 0.004), ez + 0.004, 0.008)[0]]
        for x, dz in ((0.124, 0.010), (0.140, 0.016), (0.1475, 0.022)):
            pts.append(on_face(s * x, ez + dz, 0.006)[0])
        pts += [np.array([s * 0.1535, -0.020, 1.435]), np.array([s * 0.1550, 0.008, 1.449]), np.array([s * 0.1540, 0.034, 1.436])]
        P = fit.clear(np.array(pts), 0.0035)
        P = catmull(P, 22)
        T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
        U = np.cross(T, [0, 0, 1.0]); U /= np.linalg.norm(U, axis=1)[:, None]
        Wv = np.cross(U, T)
        parts.append(Part(tube('Temple' + ('L' if s > 0 else 'R'), P, U, Wv, ellipse_profile(0.0027, 0.0027, 4), None, False), colour, 0, 'Head'))
    return parts
