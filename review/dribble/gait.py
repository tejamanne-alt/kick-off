# The kid's leg angles over time, as KidAnimator poses them: the old run cycle (with a kick swing on every dribble touch)
# and the new gait (stride rate and swing from the pace, a reach on touches). Angles in degrees, as RigPose.
import math
RUN_SPEED, STRIDE_FREQ, MAX_LEG, MAX_ARM = 4.2, 1.9, 42.0, 34.0

def knee_fold(a):
    s = max(0.0, math.cos(a + 0.9)); return 14.0 + 80.0 * s * s

def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

class Old:
    def __init__(s): s.phase = 0.0; s.kick = -10.0
    def touch(s, t): s.kick = t
    def pose(s, t, dt, v, L):
        runK = min(1.0, v / RUN_SPEED)
        s.phase += dt * STRIDE_FREQ * v * math.pi * 0.5
        sn = math.sin(s.phase)
        p = dict(legF=sn * MAX_LEG * runK, legB=-sn * MAX_LEG * runK,
                 kneeF=-(3 + (knee_fold(s.phase) - 3) * runK), kneeB=-(3 + (knee_fold(s.phase + math.pi) - 3) * runK),
                 armF=-sn * MAX_ARM * runK - 6 * runK, armB=sn * MAX_ARM * runK - 6 * runK,
                 elbowF=12 + (70 + 25 * max(0, -sn) - 12) * runK, elbowB=12 + (70 + 25 * max(0, sn) - 12) * runK, lean=7 * runK)
        if runK < 0.1: p.update(kneeF=-5, kneeB=-5, armF=-3, armB=3, elbowF=14, elbowB=14)
        kt = (t - s.kick) / 0.3
        if 0 <= kt <= 1:
            if kt < 0.3: u = kt / 0.3; th = p['legF'] + (-30 - p['legF']) * u; kn = p['kneeF'] + (-100 - p['kneeF']) * u
            elif kt < 0.7: u = (kt - 0.3) / 0.4; th = -30 + 110 * math.sin(u * math.pi / 2); kn = -100 + 100 * smoothstep(0, 1, min(1, u * 1.6))
            else: u = (kt - 0.7) / 0.3; th = 80 + (p['legF'] - 80) * u; kn = 0 + (p['kneeF'] - 0) * u
            k = 0.45
            p['legF'] += (th - p['legF']) * k; p['kneeF'] += (kn - p['kneeF']) * k; p['kneeB'] += (-14 - p['kneeB']) * k
            p['armB'] += (60 - p['armB']) * k * 0.7; p['armF'] += (-45 - p['armF']) * k * 0.6
            p['lean'] += (-8 - p['lean']) * k * math.sin(kt * math.pi)
        return p

def stride_rate(pace, run_rate): return run_rate * math.sqrt(min(1, max(0, pace)))
def stride_swing(v, rate, L, pace, run_swing):
    if rate <= 1e-4 or L <= 1e-4: return 0.0
    planted = math.degrees(abs(v) / (L * 2 * math.pi * rate)); p = min(1, max(0, pace))
    return min(planted + (run_swing - planted) * p * p * p, run_swing)

class New:
    def __init__(s): s.phase = 0.0; s.touch_t = -10.0; s.front = True
    def touch(s, t): s.touch_t = t; s.front = math.cos(s.phase) >= 0
    def pose(s, t, dt, v, L):
        runK = min(1.0, v / RUN_SPEED)
        rate = stride_rate(runK, STRIDE_FREQ * RUN_SPEED * 0.25)
        s.phase += dt * rate * 2 * math.pi
        swing = stride_swing(v, rate, L, runK, MAX_LEG)
        moving = smoothstep(0, 1, runK / 0.12)
        sn = math.sin(s.phase)
        fold = (0.55 + 0.45 * runK) * moving
        arm = MAX_ARM * swing / MAX_LEG
        p = dict(legF=sn * swing, legB=-sn * swing,
                 kneeF=-(3 + (knee_fold(s.phase) - 3) * fold), kneeB=-(3 + (knee_fold(s.phase + math.pi) - 3) * fold),
                 armF=-sn * arm - 6 * runK, armB=sn * arm - 6 * runK,
                 elbowF=12 + (70 + 25 * max(0, -sn) - 12) * runK, elbowB=12 + (70 + 25 * max(0, sn) - 12) * runK, lean=7 * runK)
        still = 1 - moving
        for k, v0 in (('armF', -3), ('armB', 3), ('elbowF', 14), ('elbowB', 14), ('kneeF', -5), ('kneeB', -5)):
            p[k] += (v0 - p[k]) * still
        tt = (t - s.touch_t) / 0.24
        if 0 <= tt <= 1:
            r = math.sin(tt * math.pi); k = 0.8 * r * r
            if s.front: p['legF'] += 14 * k; p['kneeF'] += (-10 - p['kneeF']) * 0.6 * k
            else: p['legB'] += 14 * k; p['kneeB'] += (-10 - p['kneeB']) * 0.6 * k
            p['lean'] -= 2 * k
        return p

def feet(p, L):
    """Each foot's x and height relative to the hip (thigh then shin, each half the leg; knee bends the shin back)."""
    out = {}
    for f in 'FB':
        th = math.radians(p['leg' + f]); kn = math.radians(p['knee' + f])
        kx, ky = 0.5 * L * math.sin(th), -0.5 * L * math.cos(th)
        sx, sy = kx + 0.5 * L * math.sin(th + kn), ky - 0.5 * L * math.cos(th + kn)
        out[f] = (sx, sy)
    return out

def simulate(cls, v, L, T=3.0, dt=1 / 60, touch_every=0.41):
    a = cls(); x = 0.0; t = 0.0; nt = 0.2; rows = []
    while t < T:
        if v > 0.3 and t >= nt: a.touch(t); nt += touch_every
        p = a.pose(t, dt, v, L); x += v * dt; t += dt
        rows.append((t, x, p, feet(p, L)))
    return rows

def slip(rows, v):
    """The planted foot's speed over the ground: each frame the lower foot is the one on the ground."""
    tot = 0.0; n = 0
    for (t0, x0, p0, f0), (t1, x1, p1, f1) in zip(rows, rows[1:]):
        low = 'F' if f1['F'][1] <= f1['B'][1] else 'B'
        low0 = 'F' if f0['F'][1] <= f0['B'][1] else 'B'
        if low != low0: continue
        gx0 = x0 + f0[low][0]; gx1 = x1 + f1[low][0]
        tot += abs(gx1 - gx0) / (t1 - t0); n += 1
    return tot / max(n, 1)

if __name__ == '__main__':
    L = 0.62   # a primary-school kid's leg (game units: the neck at 1.3)
    print('pace  speed   old: slip  steps/s     new: slip  steps/s  swing')
    for pace in (0.21, 0.3, 0.5, 0.75, 1.0):
        v = pace * RUN_SPEED
        o = simulate(Old, v, L); n = simulate(New, v, L)
        old_rate = STRIDE_FREQ * v * 0.25 * 2; new_rate = stride_rate(pace, STRIDE_FREQ * RUN_SPEED * 0.25) * 2
        sw = stride_swing(v, new_rate / 2, L, pace, MAX_LEG)
        print('%.2f  %.2f   %10.2f  %6.2f   %10.2f  %6.2f  %5.1f' % (pace, v, slip(o, v), old_rate, slip(n, v), new_rate, sw))
