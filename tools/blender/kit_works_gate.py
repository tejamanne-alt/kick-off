# Gate, underpass and school-entrance models of the WORKS kit (kit_works.py).
# Game z maps to Blender +Y, game y to Blender Z; fronts face -Y (toward the camera).
import math
import numpy as np
from mathutils import Vector, Matrix
from kit_works_geo import *

STONE = (0.92, 0.88, 0.80)


def _sx(M):
    """Attach.Front, required on every model."""
    M.attach.append(('Front', (0.0, -1.0, 0.0)))


# ---------------------------------------------------------------- SlidingGate
def sliding_gate():
    """The steel sliding gate panel, seen end-on from the street. Runs in depth along Y (3.05 m),
    2.4 m high, 0.3 m thick; origin at the bottom centre of the panel (the middle of its length).
    The no-entry sign is on the -Y end (the street end)."""
    M = Model('SlidingGate', p1=STEEL_BLUE, ppm=72, grime=dict(rust=0.35, streaks=0.7, chips=0.35, dirt_h=0.35))
    Ln = 3.05; hy = Ln / 2; H = 2.4; zb = 0.08; st = 0.08
    M.add(cbox((-0.15, -hy + st, H - 0.12), (0.15, hy - st, H), 0.03, 'p1', seg=2))
    M.add(cbox((-0.15, -hy + st, zb), (0.15, hy - st, zb + 0.12), 0.02, 'p1'))
    M.add(cbox((-0.13, -hy + st, 1.20), (0.13, hy - st, 1.28), 0.015, 'p1'))
    for y in (-hy, hy - st):
        M.add(cbox((-0.15, y, zb), (0.15, y + st, H), 0.02, 'p1'))
    pitch = Ln / 15.0
    for k in range(1, 15):
        y = -hy + k * pitch
        for x in (-0.1, 0.1):
            M.add(bar((x, y, zb + 0.11), (x, y, H - 0.11), 0.04, 'p1d', sides=4, caps=False))
    # a diagonal brace between the bar rows keeps the long panel from sagging
    M.add(bar((0, -hy + st + 0.05, zb + 0.16), (0, hy - st - 0.05, 1.18), 0.05, 'p1d', sides=4))
    # wheels in their brackets, on the track
    for y in (-hy + 0.26, hy - 0.26):
        prof = [(0.0, -0.026), (0.07, -0.026), (0.075, -0.019), (0.062, 0.0), (0.075, 0.019), (0.07, 0.026), (0.0, 0.026)]
        wbm, _ = lathe(prof, 14, ['iron', 'iron', 'rubber', 'rubber', 'iron', 'iron'], phase=0.0)
        xform(wbm, T(0, y, 0.075) @ R(PI / 2, 'Y'))
        M.add(wbm)
        for x in (-0.045, 0.045):
            M.add(cbox((x - 0.008, y - 0.10, 0.045), (x + 0.008, y + 0.10, zb + 0.02), 0.004, 'iron'))
        M.add(xform(cyl(0.014, -0.06, 0.06, 6, 'chrome'), T(0, y, 0.075) @ R(PI / 2, 'Y')))
    # the no-entry sign on the street end, on two short brackets
    ys = -hy - 0.05             # back of the disc; its face is 4 cm further toward the street
    zc = 1.45
    prof = [(0.0, 0.0), (0.30, 0.0), (0.30, 0.03), (0.293, 0.04), (0.262, 0.04), (0.0, 0.04)]
    disc, _ = lathe(prof, 28, ['metal', 'whiteg', 'white', 'white', 'red'], phase=0.0)
    Ms = T(0, ys, zc) @ R(PI / 2, 'X')
    xform(disc, Ms); M.add(disc)
    wb = cbox((-0.18, -0.045, 0.036), (0.18, 0.045, 0.047), 0.012, 'white', seg=2)
    xform(wb, Ms); M.add(wb)
    for dz in (-0.14, 0.14):
        M.add(cbox((-0.03, ys - 0.005, zc + dz - 0.025), (0.03, -hy + 0.005, zc + dz + 0.025), 0.006, 'iron'))
    M.attach.append(('Sign', (0.0, ys - 0.04, zc)))
    _sx(M)
    M.extra = {'length': Ln, 'height': H, 'thickness': 0.3, 'signCentre': [0.0, round(ys - 0.04, 3), zc]}
    return M


# ---------------------------------------------------------------- GatePillar
def gate_pillar():
    """A brick pillar with a stone plinth and cap, 0.5 x 0.45 m, 2.75 m to the top of the cap,
    with a steel catch on its -Y face that the gate's end runs into."""
    M = Model('GatePillar', p1=STONE, ppm=90, grime=dict(rust=0.0, chips=0.0, streaks=0.8, mottle=0.1, dirt_h=0.5))
    hx, hy = 0.25, 0.225
    M.add(cbox((-hx - 0.025, -hy - 0.025, 0.0), (hx + 0.025, hy + 0.025, 0.28), 0.02, 'p1'))
    shaft = cbox((-hx, -hy, 0.26), (hx, hy, 2.50), 0.012, 'tex')
    shaft.normal_update()

    def bfn(co, f):
        n = f.normal
        a = co.x if abs(n.y) >= abs(n.x) else co.y
        return ((a + 0.3) / 0.6, co.z / 2.4)
    settile(shaft, 'brick', bfn, [f for f in shaft.faces if abs(f.normal.z) < 0.5])
    M.add(shaft)
    M.add(cbox((-hx - 0.02, -hy - 0.02, 2.48), (hx + 0.02, hy + 0.02, 2.56), 0.015, 'p1'))
    M.add(cbox((-0.30, -0.275, 2.56), (0.30, 0.275, 2.65), 0.02, 'p1', seg=2))
    rings = [[(x, y, 2.65) for x, y in rrect(0.28, 0.255, 0.02, 1)], [(x, y, 2.75) for x, y in rrect(0.06, 0.05, 0.02, 1)]]
    M.add(loft(rings, 'p1', closed_bottom=False, closed_top=True), sm=0)
    # the gate catch: two small steel U guides the gate's end stile runs into, and a rubber stop
    y0 = -hy - 0.08
    for zc in (0.55, 1.85):
        for x in (-0.178, 0.158):
            M.add(cbox((x, y0, zc - 0.07), (x + 0.02, -hy + 0.005, zc + 0.07), 0.005, 'steel'))
        M.add(cbox((-0.178, -hy - 0.012, zc - 0.07), (0.178, -hy + 0.005, zc + 0.07), 0.005, 'steel'))
        for x in (-0.1, 0.1):
            M.add(xform(cyl(0.011, 0, 0.01, 6, 'iron'), T(x, -hy - 0.012, zc) @ R(PI / 2, 'X')))
    M.add(cbox((-0.05, -hy - 0.03, 1.1), (0.05, -hy + 0.005, 1.3), 0.012, 'rubber'))
    _sx(M)
    M.extra = {'footprint': [0.5, 0.45], 'height': 2.75}
    return M


# ---------------------------------------------------------------- CallBollard
def call_bollard():
    """A steel push-button bollard, 0.36 m square and 1.0 m tall, a round recess on its -Y face
    (the game puts its own lit button in it at Attach.Button)."""
    M = Model('CallBollard', p1=STEEL_BLUE, ppm=110, grime=dict(rust=0.25, chips=0.4, streaks=0.5, dirt_h=0.3))
    h = 0.36 / 2
    M.add(cbox((-0.22, -0.22, 0.0), (0.22, 0.22, 0.025), 0.008, 'iron'))
    for x in (-0.18, 0.18):
        for y in (-0.18, 0.18):
            M.add(xform(cyl(0.016, 0.0, 0.02, 6, 'chrome', bevel=0.005), T(x, y, 0.025)))
    M.add(rbox((-h, -h, 0.02), (h, h, 0.95), (0.035, 0.035, 0.012), 'p1', seg=(2, 2, 1), skip=((2, -1),)))
    M.add(rbox((-0.20, -0.20, 0.94), (0.20, 0.20, 1.0), (0.03, 0.03, 0.02), 'iron', seg=(1, 1, 1)))
    # a reflective yellow band
    M.add(cbox((-h - 0.004, -h - 0.004, 0.84), (h + 0.004, h + 0.004, 0.88), 0.01, 'yelloww'))
    # the button recess: a raised bezel ring around a dark floor
    zb = 0.725
    prof = [(0.148, 0.0), (0.148, 0.014), (0.14, 0.024), (0.126, 0.024), (0.122, 0.008), (0.0, 0.008)]
    ring, _ = lathe(prof, 24, ['iron', 'iron', 'chrome', 'iron', 'dark'], phase=0.0)
    xform(ring, T(0, -h, zb) @ R(PI / 2, 'X')); M.add(ring)
    # an access panel below
    M.feat('front', 'lines', lines=[[(-0.12, 0.16), (0.12, 0.16), (0.12, 0.52), (-0.12, 0.52), (-0.12, 0.16)]], w=0.004, col=(0.5, 0.5, 0.52))
    for x in (-0.1, 0.1):
        for z in (0.19, 0.49):
            M.feat('front', 'disc', a=x, b=z, r=0.008, col=(0.55, 0.55, 0.57))
    M.attach.append(('Button', (0.0, -0.19, zb)))
    _sx(M)
    M.extra = {'buttonCentre': [0.0, -0.19, zb], 'height': 1.0}
    return M


# ---------------------------------------------------------------- IntercomPost
def intercom_post():
    """A gooseneck post standing 1.15 m behind (+Y) its origin; its arm reaches forward and hangs
    the intercom panel over the origin (Attach.Panel = the panel's centre, 2.0 m up)."""
    M = Model('IntercomPost', p1=STEEL_BLUE, ppm=70, grime=dict(rust=0.3, streaks=0.5, chips=0.3))
    py = 1.15; za = 2.45; r1 = 0.28; r2 = 0.17
    path = [(0, py, 0.12), (0, py, za - r1)]
    for i in range(1, 7):
        a = (PI / 2) * i / 6
        path.append((0, py - r1 + r1 * math.cos(a), za - r1 + r1 * math.sin(a)))
    path.append((0, r2, za))
    for i in range(1, 7):
        a = PI / 2 + (PI / 2) * i / 6
        path.append((0, r2 * math.cos(a) + r2, za - r2 + r2 * math.sin(a)))
    M.add(tube(path, 0.055, 'p1', sides=10, caps=True))
    # base: a flange on a little concrete pad, and a collar
    M.add(cbox((-0.2, py - 0.2, 0.0), (0.2, py + 0.2, 0.06), 0.02, 'conc'))
    M.add(xform(cyl(0.11, 0.0, 0.025, 14, 'p1d', bevel=0.006), T(0, py, 0.06)))
    for k in range(4):
        a = PI / 4 + k * PI / 2
        M.add(xform(cyl(0.014, 0.0, 0.02, 6, 'chrome'), T(0.08 * math.cos(a), py + 0.08 * math.sin(a), 0.085)))
    M.add(xform(cyl(0.06, 0.0, 0.16, 12, 'p1d', bevel=0.01), T(0, py, 0.08)))
    # the hanger: a clamp plate the panel's top bolts to
    M.add(xform(cyl(0.055, 0.0, 0.04, 12, 'p1d', bevel=0.008), T(0, 0, 2.265)))
    M.add(cbox((-0.10, -0.06, 2.265), (0.10, 0.06, 2.285), 0.006, 'iron'))
    # a junction box on the post
    M.add(rbox((-0.08, py - 0.13, 0.75), (0.08, py - 0.04, 1.02), (0.015, 0.015, 0.015), 'p1', seg=(1, 1, 1)))
    M.add(tube([(0, py - 0.085, 0.75), (0, py - 0.085, 0.4), (0, py - 0.05, 0.25), (0, py - 0.05, 0.06)], 0.014, 'dark', sides=6))
    M.attach.append(('Panel', (0.0, 0.0, 2.0)))
    _sx(M)
    M.extra = {'postY': py, 'panelCentre': [0.0, 0.0, 2.0], 'armHeight': za}
    return M


# ---------------------------------------------------------------- IntercomPanel
def intercom_panel():
    """The intercom: 0.5 x 0.24 x 0.55 m, origin at its centre; speaker grille, camera eye and the
    button recess on its -Y face (Attach.Button, where the game's lit button goes)."""
    M = Model('IntercomPanel', p1=STEEL_BLUE, ppm=150, ground=False, grime=dict(rust=0.1, chips=0.2, streaks=0.5, ground=0.0))
    M.add(rbox((-0.25, -0.10, -0.275), (0.25, 0.12, 0.275), (0.04, 0.04, 0.04), 'p1', seg=(2, 2, 2)))
    M.add(cbox((-0.215, -0.115, -0.24), (0.215, -0.09, 0.24), 0.012, 'metal', seg=2))
    gr = cbox((-0.135, -0.122, 0.05), (0.135, -0.11, 0.19), 0.004, 'iron')
    tile_box(gr, 'grille', Vector((-0.135, 0, 0.05)), Vector((0.135, 0, 0.19)), faces=faces_facing(gr, (0, -1, 0), 0.9), mat='tex', axes=(0, 2))
    M.add(gr)
    # camera eye
    eye, _ = lathe([(0.04, 0.0), (0.04, 0.012), (0.034, 0.018), (0.024, 0.018), (0.016, 0.026), (0.0, 0.028)], 16,
                   ['iron', 'iron', 'iron', 'lens', 'lens'], phase=0.0)
    xform(eye, T(0, -0.115, 0.235) @ R(PI / 2, 'X')); M.add(eye)
    M.add(xform(cyl(0.008, 0, 0.006, 6, 'green'), T(0.16, -0.115, 0.235) @ R(PI / 2, 'X')))
    # the button recess
    zb = -0.08
    prof = [(0.155, 0.0), (0.155, 0.014), (0.146, 0.022), (0.128, 0.022), (0.125, 0.006), (0.0, 0.006)]
    ring, _ = lathe(prof, 24, ['iron', 'iron', 'chrome', 'iron', 'dark'], phase=0.0)
    xform(ring, T(0, -0.115, zb) @ R(PI / 2, 'X')); M.add(ring)
    for x in (-0.19, 0.19):
        for z in (-0.215, 0.215):
            M.add(xform(cyl(0.009, 0, 0.005, 6, 'chrome'), T(x, -0.115, z) @ R(PI / 2, 'X')))
    # a little rain lip over the face
    M.add(cbox((-0.24, -0.12, 0.255), (0.24, -0.08, 0.275), 0.008, 'p1d'))
    M.attach.append(('Button', (0.0, -0.13, zb)))
    _sx(M)
    M.extra = {'buttonCentre': [0.0, -0.13, zb]}
    return M


# ---------------------------------------------------------------- Underpass
TUNNEL_H = 3.3


def underpass_wall():
    """A 2 m segment of the underpass's back wall (tileable along X) at the tunnel's default height
    (3.3 m; scale Z for other heights) and thickness (0.4 m). Origin at the base centre (the game's
    wall centre is z = 2.05, so its front face lands on the property line at z = 1.85)."""
    H = TUNNEL_H
    M = Model('UnderpassWall', p1=(0.80, 0.76, 0.68), p2=(0.42, 0.62, 0.62), ppm=64,
              grime=dict(rust=0.08, chips=0.15, streaks=0.9, dirt_h=0.7, ground=0.8, mottle=0.1, streak_len=2.2))
    hx, hy = 1.0, 0.2
    M.add(box((-hx, -hy, 0.0), (hx, hy, H), 'p1', skip=('-z', '-y')))
    bands = [(0.16, 1.05, 'p1d'), (1.05, 1.11, 'p1'), (1.71, H, 'p1')]
    for z0, z1, m in bands:
        M.add(box((-hx, -hy, z0), (hx, -hy, z1), m, skip=('-z', '+z', '-x', '+x', '+y')))
    tb = box((-hx, -hy - 0.012, 1.11), (hx, -hy, 1.71), 'p2k', skip=('+y', '-x', '+x'))
    settile(tb, 'tiles', lambda co, f: ((co.x + hx) / (2 * hx), (co.z - 1.11) / 0.6), faces=faces_facing(tb, (0, -1, 0), 0.9))
    M.add(tb)
    for z in (1.11, 1.71):
        M.add(tube([(-hx, -hy - 0.006, z), (hx, -hy - 0.006, z)], 0.018, 'p2', sides=6, caps=False))
    M.add(cbox((-hx, -hy - 0.07, 0.0), (hx, -hy + 0.01, 0.16), 0.02, 'concd'))
    M.add(tube([(-hx, -hy - 0.06, 2.95), (hx, -hy - 0.06, 2.95)], 0.032, 'galv', sides=8, caps=False))
    for x in (-0.5, 0.5):
        M.add(cbox((x - 0.03, -hy - 0.1, 2.91), (x + 0.03, -hy, 2.99), 0.008, 'iron'))
    # joints, tie holes, the expansion joint at the seams, stains
    M.feat('front', 'lines', lines=[[(-hx, 2.35), (hx, 2.35)], [(0.0, 1.71), (0.0, H)]], w=0.006, col=(0.62, 0.60, 0.58))
    M.feat('front', 'lines', lines=[[(-hx, 0.0), (-hx, H)], [(hx, 0.0), (hx, H)]], w=0.016, col=(0.42, 0.40, 0.40))
    for x in (-0.5, 0.5):
        for z in (2.0, 2.7):
            M.feat('front', 'disc', a=x, b=z, r=0.018, col=(0.55, 0.53, 0.52))
    M.feat('front', 'streaks', a0=-hx, a1=hx, top=H, n=16, length=(0.6, 2.4), col=(0.66, 0.62, 0.58), alpha=(0.25, 0.55), width=(0.015, 0.05))
    M.feat('front', 'stain', a=0.35, b=0.35, ra=0.7, rb=0.3, col=(0.72, 0.70, 0.62), alpha=0.5)
    _sx(M)
    M.extra = {'segment': 2.0, 'height': H, 'thickness': 0.4, 'tileAxis': 'X', 'tileBand': [1.11, 1.71]}
    return M


def underpass_deck():
    """A 2 m segment of the deck over the underpass (tileable along X): 1.2 m thick and 7.4 m deep
    like the game's TunnelCeiling, a parapet with a steel railing along its front edge. Origin at
    the centre of the deck's underside (game y = ground + tunnel height, z = 0)."""
    M = Model('UnderpassDeck', p1=(0.78, 0.76, 0.71), p2=STEEL_BLUE, ppm=36, ground=False,
              grime=dict(rust=0.2, chips=0.2, streaks=0.9, ground=0.0, mottle=0.1, streak_len=1.6))
    hx, hy, D = 1.0, 3.7, 1.2
    M.add(box((-hx, -hy, 0.0), (hx, hy, D), 'p1', skip=('-z',)))
    M.add(box((-hx, -hy + 0.25, 0.0), (hx, hy, 0.0), 'concd', skip=('+z', '-x', '+x', '-y', '+y')))
    # the front fascia with a drip lip
    M.add(cbox((-hx, -hy - 0.08, -0.12), (hx, -hy + 0.25, 0.05), 0.02, 'p1'))
    M.add(cbox((-hx, -hy - 0.1, 0.9), (hx, -hy + 0.02, 1.2), 0.02, 'p1'))
    # parapet and railing
    M.add(cbox((-hx, -hy - 0.1, 1.2), (hx, -hy + 0.3, 1.5), 0.02, 'p1'))
    M.add(cbox((-hx, -hy - 0.14, 1.5), (hx, -hy + 0.34, 1.58), 0.02, 'concw'))
    for x in (-0.5, 0.5):
        M.add(cbox((x - 0.08, -hy + 0.02, 1.58), (x + 0.08, -hy + 0.18, 1.61), 0.008, 'iron'))
        M.add(bar((x, -hy + 0.1, 1.6), (x, -hy + 0.1, 2.45), 0.06, 'p2', sides=4))
    M.add(tube([(-hx, -hy + 0.1, 2.46), (hx, -hy + 0.1, 2.46)], 0.04, 'p2', sides=8, caps=False))
    M.add(tube([(-hx, -hy + 0.1, 2.02), (hx, -hy + 0.1, 2.02)], 0.025, 'p2', sides=6, caps=False))
    for x in np.arange(-0.875, 1.0, 0.25):
        M.add(bar((x, -hy + 0.1, 1.6), (x, -hy + 0.1, 2.44), 0.022, 'p2', sides=4, caps=False))
    M.add(cbox((-hx, hy - 0.3, 1.2), (hx, hy, 1.45), 0.02, 'p1'))
    M.add(box((-hx, -hy + 0.3, 1.2), (hx, hy - 0.3, 1.23), 'asphalt', skip=('-z', '-x', '+x')))
    M.feat('front', 'lines', lines=[[(-hx, -0.12), (-hx, 1.58)], [(hx, -0.12), (hx, 1.58)], [(-hx, 0.9), (hx, 0.9)]], w=0.012, col=(0.5, 0.48, 0.47))
    M.feat('front', 'streaks', a0=-hx, a1=hx, top=1.18, n=22, length=(0.3, 1.2), col=(0.62, 0.58, 0.54), alpha=(0.3, 0.6), width=(0.01, 0.05))
    M.feat('front', 'band', b0=-0.12, b1=0.0, col=(0.66, 0.64, 0.62), alpha=0.8, soft=0.02)
    _sx(M)
    M.extra = {'segment': 2.0, 'thickness': D, 'depth': 2 * hy, 'tileAxis': 'X', 'origin': 'centre of the underside'}
    return M


def tunnel_lamp():
    """A ceiling lamp fitting for the underpass: 0.9 x 0.3 m, origin at its top centre (on the
    ceiling, the game's LampFitting top at y = height, z = 0.2); Attach.Light marks the glow."""
    M = Model('TunnelLamp', p1=(0.70, 0.72, 0.73), ppm=180, ground=False, grime=dict(ground=0.0, rust=0.2, streaks=0.4, chips=0.2))
    M.add(rbox((-0.45, -0.15, -0.09), (0.45, 0.15, 0.0), (0.03, 0.03, 0.03), 'p1', seg=(1, 1, 1)))
    d = rbox((-0.40, -0.11, -0.115), (0.40, 0.11, -0.08), (0.02, 0.02, 0.015), 'creamw', seg=(1, 1, 1))
    settile(d, 'lampdiff', lambda co, f: ((co.x + 0.4) / 0.8, (co.y + 0.11) / 0.22), faces=faces_facing(d, (0, 0, -1), 0.6), mat='tex')
    M.add(d)
    for y in (-0.085, 0.085):
        M.add(bar((-0.42, y, -0.125), (0.42, y, -0.125), 0.012, 'iron', sides=4))
    for x in (-0.36, -0.18, 0.0, 0.18, 0.36):
        M.add(bar((x, -0.12, -0.13), (x, 0.12, -0.13), 0.01, 'iron', sides=4))
    for x in (-0.47, 0.47):
        M.add(cbox((x - 0.02, -0.06, -0.12), (x + 0.02, 0.06, 0.0), 0.006, 'iron'))
    M.attach.append(('Light', (0.0, -0.05, -0.1)))
    _sx(M)
    M.extra = {'origin': 'top centre (ceiling mount)', 'light': [0.0, -0.05, -0.1]}
    return M


# ---------------------------------------------------------------- School entrance
SCHOOL_STONE = (0.93, 0.89, 0.81)
SCHOOL_TRIM = (0.74, 0.70, 0.64)
ARCH_Y0, ARCH_Y1 = -1.8, 1.85          # pillar centres (game z)
ARCH_H, ARCH_RISE = 3.1, 1.1


def _flower_tub(M, c, seed):
    x, y = c
    prof = [(0.0, 0.0), (0.2, 0.0), (0.22, 0.02), (0.25, 0.34), (0.285, 0.36), (0.29, 0.42), (0.27, 0.43), (0.24, 0.40), (0.0, 0.40)]
    tub, _ = lathe(prof, 16, ['terra', 'terra', 'terra', 'terra', 'terra', 'terra', 'terra', 'soil'], phase=0.0)
    xform(tub, T(x, y, 0)); M.add(tub)
    rng = np.random.default_rng(seed)
    for k in range(5):
        a = 2 * PI * k / 5 + rng.random()
        rr = 0.12 if k else 0.0
        M.add(blob((x + rr * math.cos(a), y + rr * math.sin(a), 0.47 + 0.04 * rng.random()), (0.13, 0.13, 0.11),
                   ['leaf', 'leafl', 'leafd'][k % 3], n=6, rings=2, seed=seed * 10 + k, jitter=0.18))
    for k in range(7):
        a = 2 * PI * rng.random(); rr = 0.17 * math.sqrt(rng.random())
        M.add(blob((x + rr * math.cos(a), y + rr * math.sin(a), 0.56 + 0.06 * rng.random()), (0.045, 0.045, 0.035),
                   ['fl1', 'fl2', 'fl3', 'fl4', 'fl5'][(k + seed) % 5], n=5, rings=1, seed=seed * 20 + k, jitter=0.1))


def school_arch():
    """The school's gate arch over the footpath. In the game it spans DEPTH, so here it spans Y:
    pillars (0.7 m square, 3.1 m) at y = -1.8 and +1.85, the arch rising 1.1 m over them (crown of
    the arch's centre line at 4.2 m), a little tiled gable roof (ridge along Y), flower tubs either
    side of the way in (x = -0.75, the side the kid comes from), and lanterns. Origin at the gate
    line on the ground (game x = goal x + 0.4, z = 0). The game's sign hangs on the -X face."""
    M = Model('SchoolArch', p1=SCHOOL_STONE, p2=SCHOOL_TRIM, ppm=48,
              grime=dict(rust=0.0, chips=0.0, streaks=0.8, mottle=0.1, dirt_h=0.5, streak_len=1.3))
    hp = 0.35
    for yc in (ARCH_Y0, ARCH_Y1):
        M.add(cbox((-0.41, yc - 0.41, 0.0), (0.41, yc + 0.41, 0.4), 0.025, 'p2'))
        M.add(cbox((-0.43, yc - 0.43, 0.0), (0.43, yc + 0.43, 0.06), 0.015, 'p2'))
        M.add(cbox((-hp, yc - hp, 0.4), (hp, yc + hp, 2.95), 0.02, 'p1'))
        M.add(cbox((-0.4, yc - 0.4, 2.95), (0.4, yc + 0.4, 3.1), 0.025, 'p2'))
    # the arch's body: a wall with an elliptical opening
    yc = (ARCH_Y0 + ARCH_Y1) / 2
    ya, yb_ = ARCH_Y0 + hp, ARCH_Y1 - hp
    a = (yb_ - ya) / 2; b = 0.9
    ztop = 4.5
    n = 18
    intr = [(yc + a * math.cos(PI - PI * i / n), ARCH_H + b * math.sin(PI - PI * i / n)) for i in range(n + 1)]
    poly = [(ARCH_Y0 - hp, ARCH_H)] + intr + [(ARCH_Y1 + hp, ARCH_H), (ARCH_Y1 + hp, ztop), (ARCH_Y0 - hp, ztop)]
    body = extrude_poly(poly, 2 * hp, 'p1')
    xform(body, T(-hp, 0, 0) @ basis((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)))
    M.add(fix_normals(body))
    # the voussoir ring, a little proud of both faces and of the soffit
    V = []; F = []
    for i, (y, z) in enumerate(intr):
        t = PI - PI * i / n
        nrm = Vector((0, math.cos(t) / a, math.sin(t) / b)).normalized()
        p = Vector((0, y, z))
        pi_ = p - nrm * 0.012; po = p + nrm * 0.42
        V += [(-0.38, pi_.y, pi_.z), (0.38, pi_.y, pi_.z), (0.38, po.y, po.z), (-0.38, po.y, po.z)]
    for i in range(n):
        o, q = 4 * i, 4 * (i + 1)
        F += [(o + 0, q + 0, q + 1, o + 1), (o + 1, q + 1, q + 2, o + 2), (o + 2, q + 2, q + 3, o + 3), (o + 3, q + 3, q + 0, o + 0)]
    ring, faces = bm_from(V, F, 'p1k')
    fix_normals(ring)
    lt = L(ring)[2]; lu = L(ring)[6]; tid = tile_id('voussoir')
    ring.verts.index_update()
    for fi, f in enumerate(faces):
        if f is None: continue
        f[lt] = tid
        for l in f.loops:
            vi = l.vert.index
            i, c = divmod(vi, 4)
            l[lu].uv = ((c % 4) / 4 + 0.125, i / n)
    M.add(ring)
    M.add(cbox((-0.41, yc - 0.13, ARCH_H + b - 0.05), (0.41, yc + 0.13, ztop + 0.01), 0.02, 'p2'))
    M.add(cbox((-0.43, ARCH_Y0 - hp - 0.06, ztop), (0.43, ARCH_Y1 + hp + 0.06, ztop + 0.1), 0.02, 'p2'))
    # the roof: a little tiled gable, ridge along Y
    y0r, y1r = ARCH_Y0 - hp - 0.3, ARCH_Y1 + hp + 0.3
    ze, zr = ztop + 0.06, ztop + 0.5
    xe = 0.72
    rp = [(-xe, ze), (0.0, zr), (xe, ze), (xe, ze - 0.07), (0.0, zr - 0.075), (-xe, ze - 0.07)]
    roof = extrude_poly(rp, y1r - y0r, 'terra')
    xform(roof, T(0, y0r, 0) @ basis((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, 1, 0)) @ S(1, 1, -1) @ T(0, 0, -(y1r - y0r)))
    fix_normals(roof)
    slopes = [f for f in roof.faces if f.normal.z > 0.4]
    settile(roof, 'rooftile', lambda co, f: ((co.y - y0r) / (y1r - y0r), 1.0 - abs(co.x) / xe), faces=slopes, mat='tex')
    M.add(roof)
    gab = extrude_poly([(-0.43, ztop + 0.1), (0.0, zr - 0.07), (0.43, ztop + 0.1)], (ARCH_Y1 + hp + 0.06) - (ARCH_Y0 - hp - 0.06), 'p1')
    xform(gab, T(0, ARCH_Y0 - hp - 0.06, 0) @ basis((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, 1, 0)) @ S(1, 1, -1) @ T(0, 0, -((ARCH_Y1 + hp + 0.06) - (ARCH_Y0 - hp - 0.06))))
    M.add(fix_normals(gab))
    for y in (y0r - 0.01, y1r + 0.01):
        for sx in (-1, 1):
            M.add(bar((sx * (xe + 0.02), y, ze - 0.04), (0.0, y, zr + 0.01), 0.07, 'creamw', sides=4))
    M.add(tube([(0, y0r - 0.03, zr - 0.01), (0, y1r + 0.03, zr - 0.01)], 0.065, 'terra', sides=8))
    for y in (y0r - 0.03, y1r + 0.03):
        M.add(xform(cyl(0.05, 0.0, 0.12, 8, 'terra', bevel=0.02), T(0, y, zr + 0.03)))
    # eye bolts under the arch for the name board's chains (on the -X side)
    for dy in (-0.405, 0.405):
        y = yc + dy
        z = ARCH_H + b * math.sqrt(max(0.0, 1 - (dy / a) ** 2)) - 0.012
        M.add(xform(cyl(0.012, -0.05, 0.0, 6, 'iron'), T(-0.36, y, z)))
        loop = [(-0.36, y + 0.022 * math.sin(2 * PI * i / 8), z - 0.07 + 0.022 * math.cos(2 * PI * i / 8)) for i in range(8)]
        M.add(tube(loop, 0.006, 'iron', sides=4, closed=True, caps=False))
    # lanterns on the pillars' street side (-X), and a blank brass plaque on the near pillar
    for k, y in enumerate((ARCH_Y0, ARCH_Y1)):
        M.add(cbox((-hp - 0.18, y - 0.02, 2.62), (-hp, y + 0.02, 2.66), 0.008, 'dark'))
        lp, _ = lathe([(0.0, -0.02), (0.07, -0.02), (0.08, 0.0), (0.075, 0.2), (0.11, 0.22), (0.04, 0.3), (0.0, 0.31)], 6,
                      ['dark', 'dark', 'lamp', 'dark', 'dark', 'dark'], phase=0.5)
        xform(lp, T(-hp - 0.2, y, 2.32)); M.add(lp)
        M.attach.append(('Lamp.%d' % k, (-hp - 0.2, y, 2.42)))
    M.add(cbox((-0.16, ARCH_Y0 - hp - 0.02, 1.45), (0.16, ARCH_Y0 - hp + 0.005, 1.67), 0.01, 'brass'))
    for (yy, side) in ((ARCH_Y0 + 0.1, 1), (ARCH_Y1 - 0.1, -1)):
        _flower_tub(M, (-0.75, yy), seed=3 if side > 0 else 7)
    for mp in ('front', 'side'):
        M.feat(mp, 'ashlar', a0=-5, a1=5, b0=0.4, b1=2.95, course=0.32, block=0.55, joint=0.006, col=(0.70, 0.67, 0.62), tone=0.07)
    M.feat('side', 'ashlar', a0=-5, a1=5, b0=3.1, b1=ztop, course=0.32, block=0.55, joint=0.006, col=(0.70, 0.67, 0.62), tone=0.07)
    _sx(M)
    M.extra = {'pillars': [ARCH_Y0, ARCH_Y1], 'pillarHeight': ARCH_H, 'rise': ARCH_RISE, 'crown': ARCH_H + ARCH_RISE,
               'tubs': [[-0.75, ARCH_Y0 + 0.1], [-0.75, ARCH_Y1 - 0.1]], 'signHang': [-0.38, round(yc, 3), 3.4]}
    return M


def school_wall():
    """A 2 m segment of the school's boundary wall (tileable along X): coursed stone, 0.4 m thick,
    2.2 m high with a coping cap (to 2.3 m), half piers at both ends that pair up at the seams."""
    M = Model('SchoolWall', p1=SCHOOL_STONE, p2=SCHOOL_TRIM, ppm=56,
              grime=dict(rust=0.0, chips=0.0, streaks=0.9, mottle=0.1, dirt_h=0.5, streak_len=1.0))
    hx = 1.0
    M.add(cbox((-hx, -0.24, 0.0), (hx, 0.24, 0.36), 0.02, 'p2'))
    M.add(box((-hx, -0.2, 0.36), (hx, 0.2, 2.2), 'p1', skip=('-z', '+z')))
    M.add(cbox((-hx, -0.25, 2.2), (hx, 0.25, 2.3), 0.02, 'p2', seg=2))
    for sx in (-1, 1):
        x0, x1 = (hx - 0.13, hx) if sx > 0 else (-hx, -hx + 0.13)
        M.add(box((x0, -0.26, 0.36), (x1, 0.26, 2.32), 'p1', skip=('-z',) + (('+x',) if sx > 0 else ('-x',))))
        M.add(box((x0 - 0.02 * sx * -1 if False else x0, -0.29, 2.32), (x1, 0.29, 2.42), 'p2', skip=('-z',) + (('+x',) if sx > 0 else ('-x',))))
    for mp in ('front',):
        M.feat(mp, 'ashlar', a0=-hx + 0.13, a1=hx - 0.13, b0=0.36, b1=2.2, course=0.3, block=0.55, joint=0.006, col=(0.70, 0.67, 0.62), tone=0.07)
    M.feat('front', 'lines', lines=[[(-hx + 0.13, 0.36), (-hx + 0.13, 2.32)], [(hx - 0.13, 0.36), (hx - 0.13, 2.32)]], w=0.006, col=(0.7, 0.67, 0.62))
    M.feat('front', 'streaks', a0=-hx, a1=hx, top=2.2, n=14, length=(0.3, 1.1), col=(0.66, 0.70, 0.58), alpha=(0.2, 0.45), width=(0.01, 0.05))
    _sx(M)
    M.extra = {'segment': 2.0, 'height': 2.2, 'capTop': 2.3, 'thickness': 0.4, 'tileAxis': 'X'}
    return M


def school_sign():
    """The school's name board: a blank cream face (the game writes SCHOOL on it) in a green frame
    with a little arched crest, on two chains. Origin at the board's centre (as the game places
    its board); the face looks along -Y; Attach.Face is the face centre; the chains' hooks reach
    0.55 m above the centre (the arch's eye bolts)."""
    M = Model('SchoolSign', p1=(0.98, 0.90, 0.74), p2=(0.32, 0.48, 0.41), ppm=200, ground=False,
              grime=dict(ground=0.0, rust=0.0, chips=0.1, streaks=0.4, mottle=0.06))
    w, h = 1.41, 0.65
    M.add(rbox((-w / 2, -0.03, -h / 2), (w / 2, 0.04, h / 2), (0.02, 0.02, 0.02), 'p1', seg=(1, 1, 1)))
    fw = 0.055
    for (lo, hi) in (((-w / 2 - 0.02, -0.06, h / 2 - fw), (w / 2 + 0.02, 0.05, h / 2 + 0.02)),
                     ((-w / 2 - 0.02, -0.06, -h / 2 - 0.02), (w / 2 + 0.02, 0.05, -h / 2 + fw)),
                     ((-w / 2 - 0.02, -0.06, -h / 2 + fw), (-w / 2 + fw, 0.05, h / 2 - fw)),
                     ((w / 2 - fw, -0.06, -h / 2 + fw), (w / 2 + 0.02, 0.05, h / 2 - fw))):
        M.add(cbox(lo, hi, 0.012, 'p2', seg=2))
    crest = [(-0.42, 0.0)] + [(0.42 * math.cos(PI - PI * i / 10), 0.11 * math.sin(PI - PI * i / 10)) for i in range(1, 10)] + [(0.42, 0.0)]
    cr = extrude_poly(crest, 0.07, 'p2')
    xform(cr, T(0, 0.04, h / 2 + 0.02) @ basis((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0)))
    M.add(fix_normals(cr))
    M.add(xform(cyl(0.035, 0.0, 0.012, 12, 'brass', bevel=0.004), T(0, -0.035, h / 2 + 0.07) @ R(PI / 2, 'X')))
    top = 0.55
    for x in (-0.405, 0.405):
        M.add(xform(cyl(0.012, 0, 0.03, 6, 'iron'), T(x, 0, h / 2 + 0.02)))
        M.add(chain_links((x, 0, h / 2 + 0.05), (x, 0, top - 0.04), 0.024))
        M.add(tube([(x, 0, top - 0.04), (x, 0, top), (x + 0.02, 0, top + 0.01)], 0.006, 'iron', sides=4))
    M.attach.append(('Face', (0.0, -0.03, 0.0)))
    _sx(M)
    M.extra = {'board': [w, h], 'face': [0.0, -0.03, 0.0], 'chainTop': top, 'origin': 'board centre'}
    return M


GATE_MODELS = [sliding_gate, gate_pillar, call_bollard, intercom_post, intercom_panel,
               underpass_wall, underpass_deck, tunnel_lamp, school_arch, school_wall, school_sign]
