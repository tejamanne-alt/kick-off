# The Miami kit's play pieces (kit_buildings_mia.py's rows): what the kid slides under, hops, waits at and passes in Florida's
# legs, so that none of them is the original town's (docs/LEARNINGS.md D9). Each slide-under is the same solid as the look it
# stands for in the Barriers kit (LevelBuildKit.Spec: its half length, its top, the 0.85 m gap under it), only Miami's: a
# Cuban fruit stand for the market's stall, a sidewalk shed for the scaffold, a center-console boat on its stands, a mango
# bough, a roll-up shutter painted with a mural, the Underline's pull-up rig, a parking garage's boom gate, a banyan's aerial
# roots. Then the work zone's barricade and drum, a crate of mangoes, the crossing's walk signal, the signs' board and posts,
# the checkpoint's pole and flag, the bayfront's splash fountain, a white ibis, the Metromover's car and a tower crane.
# Axes as the kit's: X along the street, -Y toward the camera, Z up; the slide-unders' origin is the middle of the lane.
import math
import numpy as np
from kit_buildings_mia import *          # the kit's helpers and materials
from kit_buildings_mia import _label, _c

GAP = 0.85                               # LevelBuildKit.SlideGap: the kid slides under this


def _leaves(B, centre, radii, seed, n=5, mats=('leaf', 'leafd', 'leafl')):
    """A clump of leaves: overlapping lumpy blobs."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        c = (centre[0] + rng.uniform(-radii[0], radii[0]) * 0.6, centre[1] + rng.uniform(-radii[1], radii[1]) * 0.6,
             centre[2] + rng.uniform(-radii[2], radii[2]) * 0.4)
        r = tuple(v * rng.uniform(0.5, 0.75) for v in radii)
        B.add(blob(c, r, mats[k % len(mats)], 6, 2, seed * 7 + k, 0.18))


# ================================================================ slide-unders (the Barriers looks' solids)
def stall_awning_mia(B):
    """A Cuban fruit stand on the sidewalk (StallAwning: the table from 0.85 to 1.22 over 2.2 m, the awning 2.13 to 2.5 over
    2.7 m): a painted wooden stand heaped with mangoes, papayas, pineapples and coconuts, bunches of plantains hanging from
    its front rail, a striped awning on four poles."""
    hx, hy = 1.1, 0.5
    for x in (-hx + 0.05, hx - 0.05):
        for y in (-hy + 0.04, hy - 0.04):
            B.add(cbox2((x - 0.03, y - 0.03, 0.0), (x + 0.03, y + 0.03, GAP), 0.01, 'woodd'))
    B.add(cbox2((-hx, -hy, GAP), (hx, hy, GAP + 0.24), 0.02, 'cuban'))                # the stand's painted body
    B.add(box((-hx + 0.05, -hy - 0.005, GAP + 0.05), (hx - 0.05, -hy, GAP + 0.19), 'yellow'))
    B.add(cbox2((-hx - 0.02, -hy - 0.02, GAP + 0.24), (hx + 0.02, hy + 0.02, GAP + 0.28), 0.01, 'woodc'))
    top = GAP + 0.28
    rng = np.random.default_rng(31)
    kinds = [('mango', (0.07, 0.055, 0.06)), ('mangog', (0.07, 0.055, 0.06)), ('orange', (0.12, 0.08, 0.08)), ('woodd', (0.08, 0.08, 0.08))]
    for k in range(46):
        mat, r = kinds[k % 4]
        x, y = rng.uniform(-hx + 0.12, hx - 0.12), rng.uniform(-hy + 0.1, hy - 0.1)
        B.add(blob((x, y, top + r[2] + rng.uniform(0, 0.07)), r, mat, 6, 2, k, 0.06))
    for x in (-0.55, 0.45):                                                            # pineapples
        B.add(blob((x, 0.18, top + 0.14), (0.07, 0.07, 0.13), 'yellow', 7, 3, 77, 0.04))
        B.add(blob((x, 0.18, top + 0.32), (0.06, 0.06, 0.08), 'leafd', 5, 2, 78, 0.3))
    for x in np.linspace(-hx + 0.25, hx - 0.25, 4):                                    # plantains under the front rail
        for k in range(5):
            B.add(tube([(x + (k - 2) * 0.035, -hy - 0.03, GAP + 0.22), (x + (k - 2) * 0.05, -hy - 0.08, GAP + 0.04)], 0.022, 'mangog', 5))
    zf, zb, yf, yb = 2.13, 2.45, -0.82, 0.78
    for x in (-hx - 0.12, hx + 0.12):
        B.add(tube([(x, yf + 0.05, 0.0), (x, yf + 0.05, zf)], 0.025, 'white', 6))
        B.add(tube([(x, yb, 0.0), (x, yb, zb)], 0.025, 'white', 6))
    n, cw = 9, 2 * 1.35
    for i in range(n):
        x0, x1 = -cw / 2 + cw * i / n, -cw / 2 + cw * (i + 1) / n
        mat = 'havred' if i % 2 == 0 else 'white'
        B.add(quad_slab([(x0, yf - 0.12, zf), (x1, yf - 0.12, zf), (x1, yb + 0.05, zb + 0.04), (x0, yb + 0.05, zb + 0.04)], 0.03, mat))
        B.add(box((x0, yf - 0.13, zf - 0.22), (x1, yf - 0.11, zf), mat))              # the valance
    return 2.5


def quad_slab(pts, t, mat):
    """A thin slab over four corner points (a sloping awning), t thick."""
    V = list(pts) + [(p[0], p[1], p[2] + t) for p in pts]
    F = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    bm, _ = bm_from(V, F, mat)
    return fix_normals(bm)


def scaffold_gantry_mia(B):
    """A Brickell sidewalk shed under a tower going up (ScaffoldGantry: solid from 0.85 to 4.25 over 2.64 m): galvanized
    scaffold frames, green safety netting from a ledger at 0.85 up to the plywood deck, the deck painted with the builder's
    hoarding, orange warning lights."""
    hx, hy, top = 1.32, 1.15, 4.25
    for x in (-hx, hx):
        for y in (-hy, hy):
            B.add(tube([(x, y, 0.0), (x, y, top)], 0.03, 'galv', 6))
            B.add(cbox2((x - 0.08, y - 0.08, 0.0), (x + 0.08, y + 0.08, 0.03), 0.01, 'woodc'))
    for z in (GAP, 2.5, top - 0.3):
        for y in (-hy, hy):
            B.add(tube([(-hx, y, z), (hx, y, z)], 0.025, 'galv', 6))
        for x in (-hx, hx):
            B.add(tube([(x, -hy, z), (x, hy, z)], 0.025, 'galv', 6))
    for x in (-hx, hx):                                               # cross braces on the ends
        B.add(tube([(x, -hy, GAP), (x, hy, top - 0.3)], 0.02, 'galv', 5))
    for x in (-hx - 0.02, hx + 0.02):                                 # the netting on the ends the kid comes to
        B.add(box((x - 0.006, -hy, GAP + 0.04), (x + 0.006, hy, top - 0.35), 'leafd'))
    B.add(cbox2((-hx - 0.1, -hy - 0.15, top - 0.3), (hx + 0.1, hy + 0.15, top), 0.02, 'woodc'))     # the deck
    B.add(box((-hx - 0.1, -hy - 0.16, top - 0.28), (hx + 0.1, -hy - 0.15, top - 0.02), 'navy'))
    B.add(box((-hx + 0.2, -hy - 0.17, top - 0.22), (hx - 0.2, -hy - 0.16, top - 0.08), 'white'))
    for x in (-hx, hx):
        B.add(blob((x, -hy - 0.05, top + 0.08), (0.06, 0.06, 0.06), 'orange', 6, 2, 3, 0.0))
    return top + 0.15


def boat_trestles_mia(B):
    """A center-console fishing boat up on its stands by a dock (BoatTrestles: solid from 0.85 to 1.53 over 3.44 m): white
    hull with a teal boot stripe, the console under a T-top, an outboard motor on the stern, two jack stands at the ends."""
    L = 3.44
    for x in (-L / 2 + 0.35, L / 2 - 0.4):
        for y in (-0.5, 0.5):
            B.add(tube([(x, y * 1.2, 0.0), (x, y * 0.5, GAP + 0.02)], 0.03, 'galv', 5))
        B.add(cbox2((x - 0.12, -0.3, GAP - 0.05), (x + 0.12, 0.3, GAP + 0.02), 0.02, 'black'))
    # the hull (the kit's: flat-sided, its bow drawn to a point at +X) raised onto the stands, its rail and a boot stripe
    class Up:
        def add(self, bm):
            xform(bm, T(0, 0, GAP + 0.02)); B.add(bm)
    hull(Up(), L, 1.46, 0.55, bow=0.3, mat='busw', top='chrome')
    B.add(box((-L / 2, -0.735, GAP + 0.2), (L / 2 * 0.55, -0.73, GAP + 0.3), 'teal'))
    B.add(cbox2((-0.35, -0.3, 1.53), (0.35, 0.3, 2.3), 0.04, 'white'))                # the console
    B.add(box((0.3, -0.28, 1.9), (0.36, 0.28, 2.25), 'glassd'))
    for x in (-0.4, 0.4):
        for y in (-0.42, 0.42):
            B.add(tube([(x, y, 1.53), (x, y, 2.9)], 0.02, 'chrome', 5))
    B.add(cbox2((-0.55, -0.55, 2.9), (0.55, 0.55, 2.98), 0.03, 'navy'))
    B.add(cbox2((-L / 2 - 0.35, -0.2, 1.0), (-L / 2 - 0.05, 0.2, 1.75), 0.06, 'black'))   # the outboard
    B.add(box((-L / 2 - 0.36, -0.21, 1.55), (-L / 2 - 0.04, 0.21, 1.6), 'white'))
    return 2.98


def apple_bough_mia(B):
    """A mango tree's low bough over the sidewalk (AppleBough: solid from 0.85 to 1.09 over 1.7 m): the tree in a yard behind
    the lane, its limb reaching out over the sidewalk at head height, heavy with long dark leaves and mangoes hanging below it
    on their stalks down to just over a sliding kid."""
    B.add(tube([(0.0, 2.6, 0.0), (0.0, 2.5, 2.0), (0.3, 2.4, 3.4)], 0.22, 'woodd', 8))
    _leaves(B, (0.2, 2.6, 4.6), (2.0, 1.4, 1.2), 3, 9)
    B.add(tube([(0.0, 2.45, 2.2), (0.0, 1.2, 1.75), (0.05, -0.4, 1.5), (0.1, -1.5, 1.55)], 0.1, 'woodd', 7))
    for k, y in enumerate(np.linspace(1.6, -1.5, 8)):
        _leaves(B, (0.0, y, 1.62), (0.85, 0.36, 0.32), 10 + k, 5)
    rng = np.random.default_rng(5)
    for k in range(14):
        x, y = rng.uniform(-0.65, 0.65), rng.uniform(-1.4, 1.4)
        z = rng.uniform(0.98, 1.2)
        B.add(tube([(x, y, 1.45), (x, y, z + 0.06)], 0.006, 'woodd', 3))
        B.add(blob((x, y, z), (0.05, 0.04, 0.07), 'mango' if k % 3 else 'mangog', 6, 2, k, 0.03))
    return 5.8


def roll_shutter_mia(B):
    """A shop's roll-up shutter half down across the sidewalk (RollShutter: a wall 0.2 thick from 0.85 to 3.15): galvanized
    slats painted with a bright mural, the roller's box on top, the guides on either side."""
    hy = 1.75
    B.add(cbox2((-0.14, -hy - 0.1, 2.9), (0.14, hy + 0.3, 3.15), 0.04, 'galv'))
    for y in (-hy - 0.05, hy + 0.2):
        B.add(cbox2((-0.08, y - 0.05, 0.0), (0.08, y + 0.05, 2.9), 0.01, 'galv'))
    for k, z in enumerate(np.arange(GAP, 2.9, 0.09)):
        B.add(cbox2((-0.04, -hy, z), (0.04, hy + 0.2, z + 0.085), 0.02, 'galv'))
    for s in (-1, 1):                                        # the mural on both faces of the slats
        mb = MB()
        x = s * 0.045
        pts = [(x, -hy, GAP), (x, hy + 0.2, GAP), (x, hy + 0.2, 2.88), (x, -hy, 2.88)]
        if s > 0: pts = pts[::-1]
        mb.face(pts, 'tex', (s, 0, 0), 1.0, lambda co: reg_uv('mi_mural3', (co.y + hy) / (2 * hy + 0.2), (co.z - GAP) / (2.88 - GAP), 0.0))
        B.add(mb.bm())
    B.add(box((-0.05, -hy, GAP - 0.04), (0.05, hy + 0.2, GAP), 'black'))   # the bottom rail
    return 3.15


def pipe_rack_mia(B):
    """The Underline's outdoor gym rig (PipeRack: solid from 0.85 to 2.04 over 4.1 m): green steel posts, monkey bars along
    the top, a run of parallel dip bars at 0.9, rings hanging between, on a rubber pad."""
    hx = 2.05
    for x in (-hx + 0.05, 0.0, hx - 0.05):
        for y in (-0.55, 0.55):
            B.add(tube([(x, y, 0.0), (x, y, 2.04)], 0.045, 'green', 8))
    for y in (-0.55, 0.55):
        B.add(tube([(-hx, y, 2.0), (hx, y, 2.0)], 0.035, 'green', 8))
        B.add(tube([(-hx, y * 0.45, GAP + 0.05), (hx, y * 0.45, GAP + 0.05)], 0.03, 'galv', 6))
    for x in np.arange(-hx + 0.25, hx - 0.1, 0.3):
        B.add(tube([(x, -0.55, 2.0), (x, 0.55, 2.0)], 0.018, 'galv', 6))
    for x in (-1.0, 1.0):
        for y in (-0.15, 0.15):
            B.add(tube([(x, y, 2.0), (x, y, 1.45)], 0.008, 'black', 3))
            r = tube([(x + 0.09 * math.cos(a), y, 1.36 + 0.09 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 11)], 0.014, 'black', 4, caps=False)
            B.add(r)
    B.add(box((-hx - 0.2, -0.9, 0.0), (hx + 0.2, 0.9, 0.02), 'rubber'))
    return 2.1


def boom_barrier_mia(B):
    """A parking garage's boom gate across the sidewalk (BoomBarrier: the arm 0.12 thick from 0.85 to 0.95): the gate's
    cabinet behind the lane, the red-and-white arm across, its tip resting on a fork post near the kerb; a ticket pillar."""
    B.add(cbox2((-0.22, 1.9, 0.0), (0.22, 2.3, 1.05), 0.04, 'yellow'))
    B.add(box((-0.23, 1.89, 0.6), (0.23, 1.9, 0.75), 'black'))
    for k in range(8):
        y0 = 1.9 - k * 0.45
        B.add(cbox2((-0.05, y0 - 0.45, GAP), (0.05, y0, 0.95), 0.02, 'havred' if k % 2 == 0 else 'white'))
    B.add(tube([(0.0, -1.75, 0.0), (0.0, -1.75, GAP - 0.02)], 0.03, 'yellow', 6))
    B.add(cbox2((-0.07, -1.8, GAP - 0.06), (0.07, -1.7, GAP), 0.01, 'black'))
    B.add(cbox2((0.5, 2.0, 0.0), (0.85, 2.3, 1.4), 0.05, 'alu'))                     # the ticket pillar
    B.add(box((0.52, 1.99, 1.0), (0.83, 2.0, 1.3), 'neonb'))
    return 1.4


def oak_bough_mia(B):
    """A banyan's limb over the path with its aerial roots hanging down in a curtain to just over a sliding kid (OakBough:
    solid from 0.85 to 1.19 over 2.1 m), the thick prop roots down to the lawn behind the lane, the crown above."""
    B.add(tube([(0.0, 3.4, 0.0), (0.0, 3.1, 2.4), (0.0, 1.0, 2.9), (0.0, -1.8, 2.7)], 0.22, 'woodd', 8))
    for x in (-0.3, 0.35):                                       # prop roots behind the lane
        B.add(tube([(x, 2.0, 2.85), (x * 1.2, 2.1, 1.0), (x * 1.3, 2.15, 0.0)], 0.07, 'woodd', 6))
    rng = np.random.default_rng(12)
    for k in range(34):
        x = rng.uniform(-1.0, 1.0)
        y = rng.uniform(-1.5, 1.6)
        z0 = 2.75 + rng.uniform(-0.05, 0.1)
        z1 = GAP + 0.02 + rng.uniform(0.0, 0.1)
        B.add(tube([(x * 0.3, y, z0), (x * 0.8, y + rng.uniform(-0.1, 0.1), (z0 + z1) / 2), (x, y, z1)], 0.012 + 0.008 * (k % 3), 'woodd', 4))
    for k, y in enumerate(np.linspace(-1.6, 3.2, 6)):
        _leaves(B, (0.0, y, 3.3), (1.6, 1.0, 0.6), 40 + k, 5)
    return 3.9


# ================================================================ the street's play things
def barricade_mia(B):
    """A work zone's barricade (US Type III): orange-and-white striped boards on two white legs, a flashing amber lamp."""
    L = B.W
    for x in (-L / 2 + 0.15, L / 2 - 0.15):
        B.add(cbox2((x - 0.04, -0.04, 0.0), (x + 0.04, 0.04, 1.35), 0.01, 'white'))
        B.add(cbox2((x - 0.05, -0.3, 0.0), (x + 0.05, 0.3, 0.06), 0.01, 'black'))
    for z in (0.35, 0.75, 1.15):
        n = int(L / 0.3)
        for k in range(n):
            x0 = -L / 2 + L * k / n
            B.add(box((x0, -0.07, z), (x0 + L / n, -0.05, z + 0.2), 'orange' if k % 2 == 0 else 'white'))
    B.add(blob((-L / 2 + 0.15, -0.06, 1.45), (0.07, 0.04, 0.07), 'yellow', 6, 2, 2, 0.0))
    return 1.52


def drum_mia(B):
    """A traffic drum: orange with white reflective bands, a black rubber base."""
    d, _ = lathe([(0.0, 0.0), (0.38, 0.0), (0.38, 0.08), (0.27, 0.1), (0.25, 0.95), (0.2, 1.0), (0.0, 1.0)], 14, 'orange')
    B.add(d)
    for z in (0.35, 0.6, 0.82):
        b, _ = lathe([(0.262, z), (0.264, z + 0.09)], 14, 'white'); B.add(b)
    base, _ = lathe([(0.0, 0.0), (0.4, 0.0), (0.4, 0.07), (0.0, 0.07)], 14, 'black'); B.add(base)
    return 1.0


def crate_mia(B):
    """A field crate of mangoes from the fruit stands (0.7 m: the game's crate, stacked): slatted wood, the fruit showing."""
    s = 0.35
    for z in (0.02, 0.24, 0.46):
        for y in (-s, s - 0.03):
            B.add(cbox2((-s, y, z), (s, y + 0.03, z + 0.18), 0.005, 'woodc'))
        for x in (-s, s - 0.03):
            B.add(cbox2((x, -s, z), (x + 0.03, s, z + 0.18), 0.005, 'woodc'))
    for x in (-s, s - 0.05):
        for y in (-s, s - 0.05):
            B.add(cbox2((x, y, 0.0), (x + 0.05, y + 0.05, 0.7), 0.005, 'woodd'))
    B.add(box((-s, -s, 0.0), (s, s, 0.02), 'woodd'))
    rng = np.random.default_rng(4)
    for k in range(40):
        x, y = rng.uniform(-0.28, 0.28), rng.uniform(-0.28, 0.28)
        z = rng.uniform(0.1, 0.62)
        B.add(blob((x, y, z), (0.07, 0.055, 0.06), 'mango' if k % 4 else 'mangog', 5, 2, k, 0.05))
    return 0.7


def ped_signal_mia(B):
    """A crossing's pedestrian signal (US): a pole with a black signal head, the orange hand over the white walking man
    (the game lights them: Attach.Red, Attach.Green), a push button, and the street's green name blade on top."""
    B.add(tube([(0, 0, 0.0), (0, 0, 3.4)], 0.06, 'metald', 8))
    B.add(cbox2((-0.2, -0.32, 2.05), (0.2, -0.06, 2.85), 0.03, 'black'))
    for z in (2.24, 2.64):
        B.add(cbox2((-0.15, -0.33, z - 0.16), (0.15, -0.32, z + 0.16), 0.01, 'dark'))
        B.add(cbox2((-0.17, -0.38, z + 0.15), (0.17, -0.32, z + 0.18), 0.01, 'black'))   # the visor
    B.attach.append(('Red', (0.0, -0.35, 2.64)))
    B.attach.append(('Green', (0.0, -0.35, 2.24)))
    B.add(cbox2((-0.08, -0.12, 1.0), (0.08, -0.05, 1.2), 0.01, 'yellow'))
    B.add(blob((0.0, -0.13, 1.1), (0.03, 0.01, 0.03), 'black', 5, 2, 1, 0.0))
    # the name blade, in front of the pole's top (the pole must not cut through the name)
    mb = MB()
    mb.face([(-0.6, -0.1, 3.2), (0.6, -0.1, 3.2), (0.6, -0.1, 3.4), (-0.6, -0.1, 3.4)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('mi_street', (co.x + 0.6) / 1.2, (co.z - 3.2) / 0.2, 0.0))
    B.add(mb.bm())
    B.add(box((-0.6, -0.09, 3.2), (0.6, -0.07, 3.4), 'green'))
    B.add(cbox2((-0.05, -0.08, 3.25), (0.05, -0.05, 3.35), 0.005, 'metald'))
    return 3.4


def sign_board_mia(B):
    """The board of a Florida leg's sign (1.8 x 0.9 m, its middle 1.45 m up, as the game stretches it to the words): a white
    enamel panel in a teal Art Deco frame with a sunrise of coral rays on top."""
    z0, z1 = 1.0, 1.9
    B.add(cbox2((-0.9, -0.03, z0), (0.9, 0.03, z1), 0.02, 'whitep'))
    for (a, b) in (((-0.95, z0 - 0.05), (0.95, z0)), ((-0.95, z1), (0.95, z1 + 0.05)), ((-0.95, z0), (-0.9, z1)), ((0.9, z0), (0.95, z1))):
        B.add(cbox2((a[0], -0.05, a[1]), (b[0], 0.05, b[1]), 0.01, 'teal'))
    for k in range(5):
        a = math.radians(30 + 30 * k)
        B.add(tube([(0.0, -0.01, z1 + 0.05), (0.3 * math.cos(a), -0.01, z1 + 0.05 + 0.18 * math.sin(a))], 0.025, 'coral', 4))
    return z1 + 0.25


def sign_posts_mia(B):
    """The sign's two posts (teal, rounded caps), from the ground to the board's middle at 1.45 m: the game stretches them."""
    for x in (-0.65, 0.65):
        B.add(tube([(x, 0.06, 0.0), (x, 0.06, 1.45)], 0.045, 'teal', 8))
    return 1.45


def checkpoint_pole_mia(B):
    """A checkpoint's pole: a slim Art Deco pole in teal and coral bands on a round foot, a little sunburst finial."""
    p, _ = lathe([(0.0, 0.0), (0.18, 0.0), (0.16, 0.06), (0.04, 0.1), (0.035, 2.0), (0.0, 2.0)], 10, 'teal')
    B.add(p)
    for z in (0.5, 1.0, 1.5):
        b, _ = lathe([(0.04, z), (0.04, z + 0.08)], 10, 'coral'); B.add(b)
    B.add(blob((0.0, 0.0, 2.06), (0.06, 0.06, 0.06), 'gold', 6, 2, 1, 0.0))
    return 2.12


def checkpoint_flag_mia(B):
    """The checkpoint's flag (white: the game paints it as it is reached), a swallowtail pennant on the pole's top."""
    pts = [(0.04, 1.95), (0.62, 1.88), (0.5, 1.78), (0.62, 1.66), (0.04, 1.6)]
    n = len(pts)
    V = [(x, -0.006, z) for x, z in pts] + [(x, 0.006, z) for x, z in pts]
    F = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(a, (a + 1) % n, n + (a + 1) % n, n + a) for a in range(n)]
    bm, _ = bm_from(V, F, 'white')
    B.add(fix_normals(bm))
    return 1.95


def fountain_mia(B):
    """The bayfront plaza's splash fountain (jets at x 0 and +-0.45): a flush ring of keystone paving with teal and coral tile
    rings and three bronze jet nozzles in a drain grate."""
    for r, mat, z in ((1.2, 'cream2', 0.0), (1.0, 'teal', 0.004), (0.85, 'cream2', 0.006), (0.7, 'coral', 0.008), (0.58, 'galvw', 0.01)):
        d, _ = lathe([(0.0, z), (r, z), (r, z + 0.012), (0.0, z + 0.012)], 24, mat)
        B.add(d)
    for x in (-0.45, 0.0, 0.45):
        n, _ = lathe([(0.0, 0.02), (0.05, 0.02), (0.04, 0.05), (0.0, 0.05)], 8, 'brass')
        xform(n, T(x, 0, 0)); B.add(n)
    for k in range(7):
        x = -0.5 + k * 0.166
        B.add(box((x - 0.006, -0.12, 0.022), (x + 0.006, 0.12, 0.026), 'black'))
    return 0.06


def ibis_mia(B):
    """A white ibis probing the lawn: white body, black wingtips, a long down-curved orange-red bill, orange legs."""
    B.add(blob((0.0, 0.0, 0.42), (0.2, 0.09, 0.1), 'whitep', 7, 3, 5, 0.05))
    B.add(blob((-0.19, 0.0, 0.45), (0.06, 0.07, 0.04), 'black', 5, 2, 6, 0.05))
    B.add(tube([(0.14, 0, 0.46), (0.22, 0, 0.56), (0.27, 0, 0.5)], 0.035, 'whitep', 6))
    B.add(blob((0.28, 0.0, 0.5), (0.045, 0.035, 0.035), 'whitep', 6, 2, 7, 0.0))
    B.add(tube([(0.31, 0, 0.5), (0.4, 0, 0.42), (0.43, 0, 0.33)], 0.012, 'orange', 5))
    for y in (-0.03, 0.03):
        B.add(tube([(0.0, y, 0.34), (0.02, y, 0.18), (0.0, y, 0.0)], 0.01, 'orange', 4))
    return 0.6


def metromover_mia(B):
    """The Metromover's car (Miami's free driverless people mover; the ride between FL3-1 and FL3-2): a rounded white car,
    blue band and ends, wide windows on both sides and the ends, rubber-tyred bogies under it."""
    L, Wd, H = B.W, B.D, 3.0
    B.add(cbox2((-L / 2, -Wd / 2, 0.5), (L / 2, Wd / 2, H), 0.35, 'busw'))
    B.add(box((-L / 2 + 0.2, -Wd / 2 - 0.01, 0.75), (L / 2 - 0.2, -Wd / 2, 1.0), 'cuban'))
    B.add(box((-L / 2 + 0.2, Wd / 2, 0.75), (L / 2 - 0.2, Wd / 2 + 0.01, 1.0), 'cuban'))
    for x in np.arange(-L / 2 + 0.8, L / 2 - 0.6, 1.5):
        for y, s in ((-Wd / 2 - 0.012, -1), (Wd / 2 + 0.002, 1)):
            B.add(box((x, y, 1.25), (x + 1.25, y + 0.01, 2.5), 'glassb'))
    for x, s in ((-L / 2 - 0.012, -1), (L / 2 + 0.002, 1)):
        B.add(box((x, -Wd / 2 + 0.3, 1.2), (x + 0.01, Wd / 2 - 0.3, 2.6), 'glassd'))
        B.add(box((x, -Wd / 2 + 0.2, 0.55), (x + 0.01, Wd / 2 - 0.2, 0.75), 'cuban'))
    for x in (-L / 2 + 1.8, L / 2 - 1.8):
        B.add(cbox2((x - 0.9, -Wd / 2 + 0.2, 0.0), (x + 0.9, Wd / 2 - 0.2, 0.5), 0.05, 'metald'))
        for y in (-Wd / 2 + 0.25, Wd / 2 - 0.25):
            w, _ = lathe([(0.0, -0.12), (0.32, -0.12), (0.34, 0.0), (0.32, 0.12), (0.0, 0.12)], 12, 'tire')
            xform(w, T(x, y, 0.34) @ R(math.pi / 2, 'X')); B.add(w)
    B.add(cbox2((-1.0, -0.9, H), (1.0, 0.9, H + 0.25), 0.08, 'busw'))
    return H + 0.25


def crane_mia(B):
    """A tower crane over a Brickell building site: a square lattice mast (white), the slewing cab, a long jib and the
    counter-jib with its concrete counterweights, the trolley and hook, the developer's red banner on the mast's top."""
    H, J, C = 46.0, 36.0, 12.0
    a = 1.0
    for x in (-a, a):
        for y in (-a, a):
            B.add(tube([(x, y, 0.0), (x, y, H)], 0.09, 'white', 4))
    z = 0.0
    k = 0
    while z < H - 3:
        for (p0, p1) in (((-a, -a), (a, -a)), ((a, -a), (a, a)), ((a, a), (-a, a)), ((-a, a), (-a, -a))):
            q0, q1 = (p0, p1) if k % 2 == 0 else (p1, p0)
            B.add(tube([(q0[0], q0[1], z), (q1[0], q1[1], z + 3.0)], 0.04, 'white', 3, caps=False))
        z += 3.0; k += 1
    B.add(cbox2((-1.3, -1.3, H), (1.3, 1.3, H + 1.0), 0.05, 'orange'))           # the slewing ring and cab
    B.add(cbox2((0.8, -1.9, H + 0.2), (2.2, -0.6, H + 2.0), 0.08, 'white'))
    B.add(box((2.2, -1.85, H + 1.0), (2.22, -0.65, H + 1.9), 'glassd'))
    for side in (1, -1):                                                           # the jib (+X) and the counter-jib (-X)
        L = J if side > 0 else C
        for y in (-0.6, 0.6):
            B.add(tube([(0.0, y, H + 1.0), (side * L, y, H + 1.0)], 0.06, 'orange', 4))
        B.add(tube([(0.0, 0.0, H + 2.3), (side * L, 0.0, H + 1.1)], 0.06, 'orange', 4))
        x = 0.0
        while abs(x) < L - 1.5:
            nx = x + side * 3.0
            B.add(tube([(x, -0.6, H + 1.0), (nx, 0.0, H + 2.3 - 1.2 * abs(nx) / L)], 0.03, 'orange', 3, caps=False))
            B.add(tube([(x, 0.6, H + 1.0), (nx, 0.0, H + 2.3 - 1.2 * abs(nx) / L)], 0.03, 'orange', 3, caps=False))
            x = nx
    B.add(tube([(0.0, 0.0, H + 1.0), (0.0, 0.0, H + 6.0)], 0.12, 'white', 4))     # the A-frame's top and its ties
    for side, L in ((1, J * 0.7), (-1, C)):
        B.add(tube([(0.0, 0.0, H + 6.0), (side * L, 0.0, H + 1.1)], 0.025, 'black', 3))
    for k in range(3):                                                             # the counterweights
        x = -C + 0.6 + k * 1.3
        B.add(cbox2((x, -0.9, H - 1.2), (x + 1.2, 0.9, H + 0.9), 0.04, 'concw'))
    B.add(cbox2((J * 0.6 - 0.5, -0.5, H + 0.6), (J * 0.6 + 0.5, 0.5, H + 1.0), 0.04, 'dark'))
    B.add(tube([(J * 0.6, 0.0, H + 0.6), (J * 0.6, 0.0, H - 12.0)], 0.015, 'black', 3))
    B.add(cbox2((J * 0.6 - 0.25, -0.25, H - 12.6), (J * 0.6 + 0.25, 0.25, H - 12.0), 0.04, 'yellow'))
    B.add(box((-1.05, -1.06, H - 9.0), (1.05, -1.04, H - 2.0), 'havred'))       # the banner
    B.add(cbox2((-2.0, -2.0, -0.4), (2.0, 2.0, 0.6), 0.1, 'concw'))               # its footing
    return H + 6.0


def t_street(dr, w, h, k):
    """The street's green name blade: SW 8 ST (Calle Ocho)."""
    dr.rectangle([0, 0, w, h], fill=_c((0.08, 0.42, 0.24)))
    dr.rectangle([2, 2, w - 3, h - 3], outline=_c((0.95, 0.95, 0.95)), width=max(1, int(2 * k)))
    _label(dr, w, h, 'SW 8 ST', BOLD, 0.62, (0.97, 0.97, 0.97), maxw=0.9)


TILES = [('mi_street', 384, 64)]


def paint(img, pp):
    pp(img, 'mi_street', t_street, (0.08, 0.42, 0.24))


def rows(gl, prop):
    """The play pieces' rows of the kit's SPECS (name, W, H, D, roof, builder, palette, front-map top, styles, extras)."""
    p = gl((0.95, 0.95, 0.93), (0.13, 0.6, 0.6), (0.56, 0.55, 0.54))
    big = {'ppm': 24}
    return [
        ('StallAwningMIA', 2.7, 2.5, 1.8, 0.0, stall_awning_mia, p, 2.6, {'ppm': 32}, {}),
        ('ScaffoldGantryMIA', 2.9, 4.4, 2.6, 0.0, scaffold_gantry_mia, p, 4.5, big, {}),
        ('BoatTrestlesMIA', 4.2, 3.0, 1.6, 0.0, boat_trestles_mia, p, 3.1, big, {}),
        ('AppleBoughMIA', 3.0, 5.8, 5.4, 0.0, apple_bough_mia, p, 5.9, big, {}),
        ('RollShutterMIA', 0.3, 3.15, 4.0, 0.0, roll_shutter_mia, p, 3.2, big, {}),
        ('PipeRackMIA', 4.5, 2.1, 1.8, 0.0, pipe_rack_mia, p, 2.2, big, {}),
        ('BoomBarrierMIA', 1.0, 1.4, 4.2, 0.0, boom_barrier_mia, p, 1.5, big, {}),
        ('OakBoughMIA', 3.2, 3.9, 6.6, 0.0, oak_bough_mia, p, 4.0, big, {}),
        ('BarricadeMIA', 2.0, 1.52, 0.6, 0.0, barricade_mia, p, 1.6, prop, {}),
        ('DrumMIA', 0.8, 1.0, 0.8, 0.0, drum_mia, p, 1.1, prop, {}),
        ('CrateMIA', 0.7, 0.7, 0.7, 0.0, crate_mia, p, 0.8, prop, {}),
        ('PedSignalMIA', 1.2, 3.4, 0.4, 0.0, ped_signal_mia, p, 3.5, {'ppm': 24}, {}),
        ('SignBoardMIA', 1.8, 2.15, 0.1, 0.0, sign_board_mia, p, 2.2, prop, {}),
        ('SignPostsMIA', 1.4, 1.45, 0.1, 0.0, sign_posts_mia, p, 1.5, prop, {}),
        ('CheckpointPoleMIA', 0.4, 2.12, 0.4, 0.0, checkpoint_pole_mia, p, 2.2, prop, {}),
        ('CheckpointFlagMIA', 0.7, 1.95, 0.05, 0.0, checkpoint_flag_mia, p, 2.0, prop, {}),
        ('FountainMIA', 2.4, 0.06, 2.4, 0.0, fountain_mia, p, 0.2, prop, {}),
        ('IbisMIA', 0.7, 0.6, 0.2, 0.0, ibis_mia, p, 0.7, prop, {}),
        ('MetromoverMIA', 11.0, 3.25, 2.7, 0.0, metromover_mia, p, 3.3, {'ppm': 24}, {}),
        ('CraneMIA', 48.0, 52.0, 4.0, 0.0, crane_mia, p, 52.5, {'ppm': 4}, {}),
    ]
