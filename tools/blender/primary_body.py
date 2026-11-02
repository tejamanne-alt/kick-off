# The primary-school kids' bodies (see primary_spec.py). Same construction as the teens' (teen_body:
# signed distance fields, surface nets, decimation; coordinates are "final" space, the proportions the
# player sees, mapped to base space with teen_body.ungrow), with a younger body: about five heads tall, a
# big head that is not scaled down, a short neck, a round tummy, short legs and arms, small hands.
#
# Everything above the hips hangs from the neck joint (N1 = base 1.30 + lift), so the lift only
# changes how long the legs are: the torso, shoulders and arms are the same on every kid.
import numpy as np
import teen_body as TB
from teen_body import (BodyField, round_cone, chain, ellipsoid, smin, loft, frame, grow, ungrow)

BASE_NECK1 = (0.0, 0.01, 1.30)          # the Head bone's joint, in base space (teen_body.tj does the same)
BASE_TOP = (0.0, 0.01, 1.60)            # the crown


def _a(*v): return np.array(v, dtype=np.float64)


def TO_sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def profile(V):
    """The body's numbers for V (a Variant): joints and shapes in final space."""
    girl = bool(V.girl)
    N1 = 1.30 + V.lift                      # the neck joint's height
    hip = N1 - 0.62                         # the hip joints' height: the legs take up the kid's extra height
    ankle = 0.085
    knee = ankle + (hip - ankle) * 0.49
    sx = 0.108 if girl else 0.114           # shoulder joints' x
    sh = N1 - 0.100                         # shoulder joint height
    j = dict(pelvis=(0, 0.006, hip + 0.02), spine=(0, 0.002, N1 - 0.43), chest=(0, 0.004, N1 - 0.27), neck0=(0, 0.012, N1 - 0.055))
    side = dict(
        hip=((0.068 if girl else 0.070), 0.0, hip), knee=((0.070 if girl else 0.072), -0.005, knee),
        ankle=((0.073 if girl else 0.075), 0.016, ankle), toe=((0.076 if girl else 0.078), -0.125, 0.03),
        shoulder=(sx, 0.008, sh), elbow=(sx + 0.038, 0.018, sh - 0.245),
        wrist=(sx + 0.060, 0.006, sh - 0.245 - 0.225), tip=(sx + 0.064, -0.003, sh - 0.245 - 0.225 - 0.115))
    # the torso: (height below the neck joint, half width, half depth, centre y, roundness)
    rel = [(-0.012, 0.056, 0.050, 0.016, 2.0), (-0.036, 0.060, 0.052, 0.016, 2.0), (-0.055, 0.082, 0.058, 0.012, 2.1),
           (-0.075, 0.104, 0.064, 0.006, 2.3), (-0.105, 0.107, 0.072, 0.002, 2.3), (-0.17, 0.100, 0.078, -0.003, 2.2),
           (-0.25, 0.097, 0.083, -0.006, 2.1), (-0.34, 0.100, 0.088, -0.004, 2.05), (-0.43, 0.104, 0.090, 0.0, 2.0),
           (-0.50, 0.108, 0.088, 0.006, 2.0), (-0.57, 0.108, 0.082, 0.010, 2.0), (-0.62, 0.092, 0.070, 0.012, 2.0),
           (-0.645, 0.070, 0.060, 0.012, 2.0)]
    if girl:      # narrower through the shoulders, a little rounder at the hips
        rel = [(z, w * (0.95 if -0.2 < z < -0.07 else 1.0) * (1.03 if z < -0.5 else 1.0), d, cy, n) for z, w, d, cy, n in rel]
    keys = [(N1 + z, w, d, cy, n) for z, w, d, cy, n in rel]
    return dict(N1=N1, hip=hip, joints=j, side=side, keys=keys, zlo=hip - 0.045, zhi=N1 - 0.012,
                r=dict(neck=(0.044, 0.040), uarm=(0.043, 0.037), farm=(0.036, 0.033, 0.024),
                       thigh=(0.068, 0.059, 0.047), shin=(0.046, 0.028), calf=(0.046, 0.044, 0.095), delt=(0.042, 0.044, 0.052)),
                hand=0.80, foot=0.84)


def tj(V):
    """Joints in final space, name -> (x, y, z) (see teen_body.tj); L/R are mirrored."""
    if getattr(V, '_tj', None) is None:
        P = profile(V)
        j = dict(P['joints'])
        j['neck1'] = tuple(grow(BASE_NECK1, V)); j['headtop'] = tuple(grow(BASE_TOP, V))
        for k, (x, y, z) in P['side'].items():
            j[k + 'L'] = (x, y, z); j[k + 'R'] = (-x, y, z)
        V._tj = {k: np.array(v, dtype=np.float64) for k, v in j.items()}
    return V._tj


class KidBodyField(BodyField):
    """BodyField for a primary kid: the same union of tapered capsules, ellipsoids and a lofted torso
    (its __call__, hands, arms and legs are the teens'), with the kid's own numbers."""
    def __init__(self, V):
        self.girl = V
        P = self.P = profile(V)
        j = self.j = tj(V)
        self.keys = P['keys']
        self.torso_core = loft(self.keys, P['zlo'], P['zhi'], 0.025)
        self.r = r = P['r']
        self.hand_scale = P['hand']
        girl = bool(V.girl)
        hz = j['hipL'][2]
        glutes = [ellipsoid((s * 0.046, 0.036, hz + 0.004), (0.060, 0.052, 0.066)) for s in (1, -1)]
        tc = self.torso_core
        self.torso = lambda p: smin(smin(tc(p), glutes[0](p), 0.028), glutes[1](p), 0.028)
        n0 = j['neck0']; n1 = j['neck1']
        self.neck = round_cone(n0 + (0, 0.003, -0.03), n1 + (0, 0.012, 0.01), r['neck'][0], r['neck'][1])
        self.hand = {}; self.foot = {}; self.uarm = {}; self.farm = {}
        self.thigh = {}; self.shin = {}
        for n, s in (('L', 1), ('R', -1)):
            sh, el, wr, tip = j['shoulder' + n], j['elbow' + n], j['wrist' + n], j['tip' + n]
            adir = (el - sh) / np.linalg.norm(el - sh)
            delt = ellipsoid(sh + adir * 0.025 + (-s * 0.005, -0.002, 0.004), r['delt'], frame(adir))
            ua = round_cone(sh, el, r['uarm'][0], r['uarm'][1])
            mid = el + (wr - el) * 0.3
            fa = chain([el, mid, wr], r['farm'], 0.0)
            self.uarm[n] = lambda p, ua=ua, delt=delt: smin(ua(p), delt(p), 0.018)
            self.farm[n] = fa
            self.hand[n] = self._hand(wr, tip, s)
            hp, kn, an = j['hip' + n], j['knee' + n], j['ankle' + n]
            midt = hp + (kn - hp) * 0.5 + (0, -0.004, 0)
            th = chain([hp, midt, kn], r['thigh'], 0.0)
            sn = round_cone(kn, an, r['shin'][0], r['shin'][1])
            calf = ellipsoid(kn + (an - kn) * 0.33 + (-s * 0.003, 0.020, 0), r['calf'])
            kcap = ellipsoid(kn + (0, -0.026, 0.010), (0.034, 0.024, 0.036))        # round little knees
            self.thigh[n] = th
            self.shin[n] = lambda p, sn=sn, calf=calf, kcap=kcap: smin(smin(sn(p), calf(p), 0.03), kcap(p), 0.02)
            fs = P['foot']
            ft = ellipsoid((an[0] + s * 0.001, -0.026 * fs, 0.04), (0.031 * fs, 0.082 * fs, 0.027))
            heel = ellipsoid((an[0], 0.024, 0.047), (0.028, 0.032, 0.035))
            self.foot[n] = lambda p, ft=ft, heel=heel: smin(ft(p), heel(p), 0.026)

    def __call__(self, p):
        d = smin(self.torso(p), self.neck(p), 0.03)
        for n in 'LR': d = smin(d, self.leg_full(n)(p), 0.05)
        # the arms blend into the shoulders softly, but below the armpit hardly at all: a hand that hangs beside the hip
        # must not be webbed to it
        z = p[:, 2]; sz = self.j['shoulderL'][2]
        k = 0.004 + 0.034 * (1 - TO_sstep(sz - 0.07, sz - 0.14, z))
        for n in 'LR': d = smin(d, self.arm_full(n)(p), k)
        return d
