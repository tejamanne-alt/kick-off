# Kamakura's own plants for the PLANTS kit (kit_plants.py registers them in its MODELS): the trees and shrubs of the
# Shonan coast in the user's brief (docs/KAMAKURA_BRIEF.md, PLANTS; a clear May morning), built as the kit's other trees
# are (docs/ART_DIRECTION.md, section 6): crowns of cut-out leaf-clump cards over dark cores (kit_plants_leaves.py), bark
# from the atlas's bark tiles, every vertex colour carrying its baked light and shade.
#   BlackPine   a Japanese black pine (kuromatsu) from the sea front: a crooked dark-grey trunk leaning away from the sea
#               (toward +X), long low limbs ending in flat-bottomed pads of dark blue-green needle tufts, layered and
#               swept downwind, the top flattened by the wind
#   Camphor     a camphor tree (kusunoki) from a shrine hill: a thick, buttressed trunk forking into great limbs under a
#               dense, rounded crown of glossy bright-green leaves, May's light yellow-green flush over its top
#   Cedar       a Japanese cedar (sugi) on the hills: a tall, straight reddish-brown trunk, clear of branches low down, under
#               a narrow cone of dark green needle clumps to a pointed top
#   CherryLeaf  a Somei-yoshino cherry in full green leaf (May, no blossom): a dark trunk banded with lenticels that forks
#               low into wide-spreading limbs under a broad, flat-topped crown
#   Bamboo      a clump of bamboo: slender green culms with pale-banded nodes, their tops arching over under feathery
#               sprays of narrow hanging leaves (the bamboo sprite)
#   Hydrangea   a hydrangea bush: broad leaves, big mophead flower heads in blue and violet (the floret sprite)
#   Azalea      a clipped azalea mound (o-karikomi), smothered in pink-magenta flowers (late April to May)
#   Persimmon   a persimmon tree (kaki): an open, irregular crown of fresh light-green May leaves on a dark, blocky-barked
#               trunk with crooked limbs (no fruit until autumn)
# Every model keeps the kit's contract (kit_plants.py's header): origin at the base on the ground, front -Y, parts 0 fixed
# (wood, culms), 1 foliage, 2 flowers; the trees within the tree budget, the shrubs within the bush budget.
#
# This module is self-contained (kit_plants.py runs its build on import, so it can't be imported back): the few wood
# helpers it shares with kit_plants.py are repeated below.
import math
import numpy as np
import kit_plants_geo as G
import kit_plants_atlas as AT
import kit_plants_leaves as LV

UP = np.array((0.0, 0.0, 1.0))
PI = math.pi
RNG = lambda seed: np.random.default_rng(seed)

# ---------------------------------------------------------------- palette (sRGB hex): (deep shade, base, sunlit top)
R_KURO = G.Ramp('#0a1f1d', '#24493d', '#73985f')        # black pine needles: dark blue-green
R_KUSU = G.Ramp('#11321c', '#3f7f2c', '#b9d95e')        # camphor: glossy bright green
R_KUSU_NEW = G.Ramp('#4a5c24', '#a3c048', '#dfea92')    # camphor's May flush: light yellow-green
R_SUGI = G.Ramp('#0a1c15', '#26452d', '#6c8c50')        # cedar: dark green
R_SAKURA = G.Ramp('#18361f', '#548a36', '#bcd96a')      # cherry leaves in May
R_TAKE = G.Ramp('#1d361d', '#5b8a38', '#c4dc74')        # bamboo leaves
R_KAKI = G.Ramp('#26461f', '#7aa83f', '#e0ee92')        # persimmon: fresh light green
R_AJISAI = G.Ramp('#173421', '#467c3c', '#9fc464')      # hydrangea leaves
R_TSUTSUJI_L = G.Ramp('#13281a', '#36602f', '#7fa452')  # azalea leaves: small, dark
R_TSUTSUJI = G.Ramp('#7a1446', '#d4378a', '#ffa8d4')    # azalea flowers: pink-magenta
HYDRANGEA = [('#2e4a9a', '#5f86d8', '#b9cdf6'), ('#4b3a94', '#8670cf', '#cdbff2'), ('#3a4fa0', '#7a8ee0', '#d0dcfa'),
             ('#5a3a8c', '#9a72c8', '#dcc6ee')]            # mopheads: blue, violet, pale blue, mauve
R_HYD_BASE = G.Ramp(*HYDRANGEA[0])

WOOD_KURO = '#4a4542'      # black pine: dark grey plates
WOOD_KUSU = '#5e5048'      # camphor: grey-brown, finely furrowed
WOOD_SUGI = '#7e4b36'      # cedar: reddish-brown, stringy
WOOD_SAKURA = '#3e2c2d'    # cherry: dark, glossy, banded
WOOD_KAKI = '#3a3330'      # persimmon: dark, blocky
CULM = '#7a9844'           # bamboo culms: green
CULM_OLD = '#a2a463'       # older culms go yellow-grey


# ---------------------------------------------------------------- wood (as kit_plants.py)
def uvr(name, span, offset=0.0):
    u0, v0, u1, v1 = AT.REG[name]; m = AT.MARGIN
    return (u0 + m, v0 + m, u1 - m, v1 - m, lambda s, i: min(max((s + offset) / span, 0.0), 1.0))


def wood_color(p, hexcol, ground=0.62, shade_z=None, shade=0.35):
    z = p.V[:, 2]
    k = 1 - (1 - ground) * G.smoothstep(0.7, 0.0, z)
    if shade_z is not None:
        k = k * (1 - shade * G.smoothstep(shade_z - 1.4, shade_z + 0.2, z))
    p.color(G.hexc(hexcol)[None, :] * k[:, None])
    p.part(0)
    return p


def sink_base(p, z=-0.15):
    p.V[p.A['ring'] == 0, 2] = z
    return p


def ground(pieces, height=None, sink=0.03):
    zmin = min(p.V[:, 2].min() for p in pieces); zmax = max(p.V[:, 2].max() for p in pieces)
    k = 1.0 if height is None else (height + sink) / (zmax - zmin)
    M = np.eye(4); M[2, 2] = k; M[2, 3] = -sink - zmin * k
    for p in pieces:
        p.move(M)
        if 'windz' in p.A:
            p.A['windz'] = p.A['windz'] * k + M[2, 3]
    return pieces


def flare(path, amount=0.45, height=0.75, roots=4, phase=0.0, ripple=0.04):
    def f(i, ang):
        z = path[i][2]
        a = float(G.smoothstep(height, 0.0, z))
        lob = np.maximum(0.0, np.cos(roots * (ang - phase))) ** 3
        return 1 + a * (amount * lob + 0.12) + ripple * np.cos(3 * ang + 1.7 * i)
    return f


def limb_path(p0, p1, rng, sag=0.0, rise=0.0, n=6, wob=0.08):
    """A limb from p0 to p1: it can sag below the straight line and rise again at its end (a pine's limbs)."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0; L = np.linalg.norm(d)
    m1 = p0 + d * 0.35 + UP * L * (rise * 0.5 - sag) + rng.normal(0, wob, 3) * L * 0.3
    m2 = p0 + d * 0.7 + UP * L * (rise - sag * 0.6) + rng.normal(0, wob, 3) * L * 0.3
    return G.catmull([p0, m1, m2, p1], n)


def leaf_tree(seed, masses, trunk_ctrl, trunk_r, fork_z, ramp, wood, card=1.35, density=1.0, inner=0.3, twigs=3,
              core=0.55, sprite='leaf', region='bark', limb_r=(0.42, 0.55), flare_amt=0.5, trunk_sides=9, taper=0.62,
              twig_r=0.05, shade=0.0, light_k=1.0, open_under=0.4, tilt=0.25, core_s=(0.0, 0.12), limb_end=0.3,
              groups=3, fork_spread=0.8, nmix=(0.7, 0.22, 0.15), rng=None):
    """kit_plants.leaf_tree: a broadleaf crown of leaf cards over dark cores on a branching trunk."""
    rng = rng or RNG(seed)
    lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
    C0 = (lo + hi) / 2; Rc = (hi - lo) / 2
    pieces = [LV.leaf_cards(masses, rng, ramp, 1, sprite, size=card, density=density, inner=inner, C0=C0, Rc=Rc,
                            shade=shade, light_k=light_k, open_under=open_under, tilt=tilt, nmix=nmix)]
    pieces += LV.cores(masses, rng, ramp, 1, scale=core, C0=C0, Rc=Rc, s=core_s)
    tpath = G.catmull(trunk_ctrl, 14)
    radii = trunk_r * (1 - taper * np.linspace(0, 1, len(tpath)) ** 0.85)
    trunk = G.tube(tpath, radii, trunk_sides, lobe=flare(tpath, flare_amt, 0.8, 4, rng.uniform(0, 6)), uv=uvr(region, 8.0))
    crown_z = lo[2] + 0.4
    wood_color(trunk, wood, shade_z=crown_z)
    pieces.append(LV.hidden_in(trunk, masses, core))

    def paint(p):
        return wood_color(p, wood, ground=1.0, shade_z=crown_z + 0.6, shade=0.3)
    pieces += LV.branches(masses, rng, tpath, trunk_r, fork_z, paint, lambda off: uvr(region, 8.0, off),
                          limb_r=limb_r, twigs=twigs, twig_r=twig_r, core_k=core, limb_end=limb_end, groups=groups,
                          fork_spread=fork_spread)
    return pieces, C0, Rc


def hanging_cards(masses, rng, ramp, sprite, size, density=1.0, inner=0.3, spin=0.35, part=1, rho=(0.75, 1.02),
                  rho_in=(0.4, 0.72), C0=None, Rc=None, nmix=(0.55, 0.3, 0.2), size_jit=0.18, crease=0.3):
    """LV.leaf_cards for sprites with a top and a bottom (the bamboo's hanging sprays): each card stays upright in its
    plane (spun only by `spin` radians), so its leaves hang down."""
    if C0 is None:
        lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
        C0 = (lo + hi) / 2; Rc = (hi - lo) / 2
    z0 = min(m.c[2] - m.r[2] for m in masses); z1 = max(m.c[2] + m.r[2] for m in masses)
    nsp = len(AT.SPRITES[sprite])
    V, N, C, U, F, WZ = [], [], [], [], [], []
    for mi, m in enumerate(masses):
        others = [o for j, o in enumerate(masses) if j != mi]
        n_out = int(round(4.6 * density * m.cards * m.area() / (size * size)))
        for count, (r0, r1), layer in ((n_out, rho, 0), (int(round(n_out * inner)), rho_in, 1)):
            if count <= 0: continue
            for d in LV.fib_dirs(count, rng):
                rr = rng.uniform(r0, r1)
                p = m.point(d, rr)
                eo = min([o.e(p)[0] for o in others], default=9.0)
                if eo < (0.8 if layer == 0 else 0.6): continue
                yaw = rng.uniform(0, 2 * PI)
                el = float(np.clip(rng.normal(0, 0.2), -0.6, 0.6))
                g = np.array((math.cos(el) * math.cos(yaw), math.cos(el) * math.sin(yaw), math.sin(el)))
                right = G.unit(np.cross(UP, g)); up = np.cross(g, right)
                psi = rng.normal(0, spin)
                Rv = math.cos(psi) * right + math.sin(psi) * up
                Uv = -math.sin(psi) * right + math.cos(psi) * up
                s = size * rng.uniform(1 - size_jit, 1 + size_jit) * (0.85 if layer else 1.0)
                h = s / 2
                V += [p - Rv * h - Uv * h, p + Rv * h - Uv * h, p + Rv * h + Uv * h, p - Rv * h + Uv * h]
                uvs = np.array(((0, 0), (1, 0), (1, 1), (0, 1)), float)
                if rng.random() < 0.5: uvs[:, 0] = 1 - uvs[:, 0]
                dm = G.unit((p - m.c) / m.r); dc = G.unit((p - C0) / Rc)
                n = G.unit(nmix[0] * dm + nmix[1] * dc + nmix[2] * G.unit(rng.normal(size=3)))
                hz = (p[2] - z0) / max(z1 - z0, 1e-3)
                sv = (0.66 + 0.3 * G.smoothstep(r0, r1, rr)) if layer == 0 else (0.05 + 0.2 * G.smoothstep(r0, r1, rr))
                sv += 0.14 * dm[2] + 0.14 * (2 * hz - 1) + m.bright - crease * G.smoothstep(1.4, 0.85, eo) + rng.uniform(-0.07, 0.07)
                base = len(V) - 4
                N += [n] * 4
                C += [ramp(float(sv))] * 4
                U += list(AT.sprite_uv(sprite, int(rng.integers(0, nsp)), uvs[:, 0], uvs[:, 1]))
                WZ += [p[2]] * 4
                F.append((base, base + 1, base + 2, base + 3))
    pc = G.Piece(np.array(V), F, N=np.array(N))
    pc.C[:, :3] = np.array(C).reshape(-1, 3)
    pc.U = np.array(U)
    pc.part(part)
    pc.tag('windz', WZ)
    return pc


# ================================================================ Japanese black pine
def build_black_pine():
    # A kuromatsu of the sea front: a long, bare, crooked trunk leaning away from the sea (+X), one long low limb reaching
    # downwind, and above it a few layers of broad, flat-bottomed plates of needle tufts on level limbs that sag and turn
    # up at their ends, with sky between the layers; the top is a wide, flat, wind-pressed plate.
    rng = RNG(907)
    tr = 0.28
    ctrl = [(0, 0, -0.15), (0.14, 0.0, 1.2), (0.55, 0.06, 2.4), (0.78, -0.04, 3.4), (1.32, 0.05, 4.4), (1.6, -0.02, 5.3),
            (2.2, 0.05, 6.2), (2.6, 0.0, 6.85)]
    tpath = G.catmull(ctrl, 24)
    radii = tr * (1 - 0.7 * np.linspace(0, 1, len(tpath)) ** 0.8)

    def trunk_at(z):
        j = int(np.argmin(np.abs(tpath[:, 2] - z)))
        return j, tpath[j]

    def plate(c, d, R, n):
        """A broad, flat plate of n needle pads round c, spread across the limb's direction d."""
        side = np.array((-d[1], d[0], 0.0))
        out = [LV.Mass(c, (R, R * 0.8, R * 0.3), under=0.3, bright=rng.uniform(-0.04, 0.05))]
        for k in range(n - 1):
            off = (side * (1 if k % 2 else -1) * rng.uniform(0.55, 0.85) * R
                   + d * rng.uniform(-0.45, 0.55) * R + UP * rng.uniform(-0.18, 0.12))
            rr = R * rng.uniform(0.58, 0.75)
            out.append(LV.Mass(c + off, (rr, rr * 0.85, rr * 0.36), under=0.3, bright=rng.uniform(-0.07, 0.03)))
        return out
    # (height on the trunk, [(azimuth (0 = +X, downwind), reach, plate radius, pads)])
    layers = [(3.0, [(0.12, 2.9, 1.0, 3)]),
              (4.3, [(2.75, 1.1, 0.75, 2), (1.5, 1.4, 0.85, 3), (-1.3, 1.5, 0.85, 3), (0.35, 2.3, 0.95, 3)]),
              (5.4, [(2.4, 0.9, 0.7, 2), (0.95, 1.6, 0.85, 3), (-0.7, 1.7, 0.85, 3)])]
    masses = []; limbs = []
    for z, arms in layers:
        for az, reach, R, n in arms:
            az += rng.normal(0, 0.12)
            j, p0 = trunk_at(z + rng.uniform(-0.2, 0.2))
            d = np.array((math.cos(az), math.sin(az) * 0.85, 0.0))
            c = p0 + d * reach + UP * rng.uniform(0.0, 0.2)
            pl = plate(c, G.unit(d), R, n)
            masses += pl
            limbs.append((j, p0, c, pl))
    # the wind-pressed top: one wide, flat plate over the trunk's head, longer downwind
    top = tpath[-1]
    pl = [LV.Mass(top + np.array((0.35, 0.0, 0.32)), (1.35, 1.05, 0.4), under=0.3, bright=0.05),
          LV.Mass(top + np.array((-0.75, 0.3, 0.12)), (0.75, 0.65, 0.3), under=0.3),
          LV.Mass(top + np.array((1.55, -0.25, 0.1)), (0.8, 0.7, 0.3), under=0.3, bright=0.02),
          LV.Mass(top + np.array((0.4, 0.85, 0.15)), (0.7, 0.6, 0.28), under=0.3),
          LV.Mass(top + np.array((0.6, -0.85, 0.12)), (0.7, 0.6, 0.28), under=0.3)]
    masses += pl
    limbs.append((len(tpath) - 1, top, top, pl))
    pieces = [LV.leaf_cards(masses, rng, R_KURO, 1, 'pine', size=0.72, density=0.85, inner=0.22, open_under=0.0,
                            nmix=(0.78, 0.1, 0.14), tilt=0.3, crease=0.15)]
    pieces += LV.cores(masses, rng, R_KURO, 1, scale=0.64, s=(0.02, 0.14))
    trunk = G.tube(tpath, radii, 9, twist=0.3, lobe=flare(tpath, 0.4, 0.6, 3, rng.uniform(0, 6), ripple=0.06),
                   uv=uvr('bark', 8.0))
    wood_color(trunk, WOOD_KURO, ground=0.72)
    sink_base(trunk)
    pieces.append(LV.hidden_in(trunk, masses, 0.64))

    def wood(path, r0, r1, sides, z0):
        b = G.tube(path, np.linspace(r0, r1, len(path)), sides, twist=0.3, uv=uvr('bark', 8.0, z0))
        wood_color(b, WOOD_KURO, ground=1.0)
        pieces.append(LV.hidden_in(b, masses, 0.64))
    for (j, p0, c, pl) in limbs:
        r0 = max(0.05, radii[j] * 0.55)
        if np.linalg.norm(c - p0) > 0.3:          # the limb: out level, sagging, turning up into its plate
            path = limb_path(p0, c - UP * 0.15, rng, sag=0.1, rise=0.12, n=7)
            wood(path, r0, r0 * 0.4, 6, p0[2])
            q = path[-2]
        else:
            q = p0
        for m in pl[1:]:                          # short crooked branches out to each pad of the plate
            wood(limb_path(q, m.c - UP * m.r[2] * 0.3, rng, sag=0.04, rise=0.1, n=4), r0 * 0.4, r0 * 0.18, 4, q[2])
    return pieces, {0: G.hexc(WOOD_KURO), 1: R_KURO.base}, {'kind': 'tree', 'trunkRadius': tr, 'lean': '+X (away from the sea)'}


# ================================================================ camphor
def build_camphor():
    # A kusunoki: a thick, buttressed trunk forking at about 3 m into great limbs under a dense, rounded crown, wider
    # than tall; glossy bright-green leaves, and May's light flush of new leaves over the top of the crown.
    rng = RNG(311)
    tr = 0.5
    masses = LV.masses_from((0, 0.0, 7.3), (5.6, 4.5, 3.7), 13, rng, rf=(0.31, 0.38), shell=0.64, zlo=-0.62)
    ctrl = [(0, 0, -0.15), (0.1, 0.0, 1.2), (-0.06, 0.04, 2.3), (0.05, 0.0, 3.8), (0.0, 0.05, 6.2)]
    pieces, C0, Rc = leaf_tree(311, masses, ctrl, tr, 2.7, R_KUSU, WOOD_KUSU, card=1.75, density=0.95, limb_r=(0.5, 0.62),
                               flare_amt=0.8, trunk_sides=10, taper=0.66, open_under=0.3, groups=5, fork_spread=0.9,
                               limb_end=0.22, twig_r=0.06, rng=rng)
    # the flush: light cards scattered over the sunlit top of the crown
    top = [m for m in masses if m.c[2] > C0[2] - 0.3]
    pieces.append(LV.leaf_cards(top, rng, R_KUSU_NEW, 1, 'leaf', size=1.0, density=0.3, inner=0.0, C0=C0, Rc=Rc,
                                rho=(0.96, 1.07), open_under=1.0, nmix=(0.7, 0.22, 0.15), crease=0.2))
    return pieces, {0: G.hexc(WOOD_KUSU), 1: R_KUSU.base}, {'kind': 'tree', 'trunkRadius': tr}


# ================================================================ Japanese cedar
def build_cedar():
    # A sugi: a dead-straight trunk, reddish-brown and stringy, clear of branches for the first few metres (a few dead
    # stubs), then a narrow cone of dark needle clumps to a pointed top.
    rng = RNG(523)
    H = 18.2
    tr = 0.4
    zb = 4.6                                   # the lowest live branches
    Rmax = 2.25
    tpath = np.array([(0.03 * math.sin(t * 2.3), 0.02 * math.sin(t * 3.1), -0.15 + (H - 0.3) * t) for t in np.linspace(0, 1, 16)])
    radii = tr * (1 - 0.92 * np.linspace(0, 1, len(tpath)) ** 0.9)

    def R_at(z):
        return Rmax * max(0.0, 1 - (z - zb) / (H - zb)) ** 0.82

    masses = []
    ga = PI * (3 - 5 ** 0.5); a0 = rng.uniform(0, 2 * PI)
    n = 30
    for k in range(n):
        f = (k + 0.5) / n
        z = zb + 0.55 + (H - 1.5 - zb) * f ** 1.05
        R = R_at(z)
        a = a0 + ga * k
        out = R * rng.uniform(0.42, 0.6)
        c = np.array((math.cos(a) * out, math.sin(a) * out, z + rng.uniform(-0.1, 0.1)))
        rr = max(0.42, R * 0.58)
        masses.append(LV.Mass(c, (rr, rr * 0.92, max(0.45, rr * 0.75)), under=0.6, bright=rng.uniform(-0.06, 0.05)))
    # the axis: masses up the middle so the cone is solid, the last one the pointed leader
    for z in np.arange(zb + 0.9, H - 1.4, 1.6):
        R = R_at(z)
        masses.append(LV.Mass((0, 0, z), (R * 0.55, R * 0.55, 0.9), under=0.7, cards=0.5))
    masses.append(LV.Mass((0.0, 0.0, H - 1.1), (0.42, 0.42, 0.85), under=0.7))
    masses.append(LV.Mass((0.0, 0.0, H - 0.45), (0.22, 0.22, 0.45), under=0.8))
    pieces = [LV.leaf_cards(masses, rng, R_SUGI, 1, 'pine', size=0.82, density=0.72, inner=0.22, open_under=0.15,
                            nmix=(0.6, 0.3, 0.15), tilt=0.3, crease=0.25)]
    pieces += LV.cores(masses, rng, R_SUGI, 1, scale=0.62, s=(0.0, 0.1))
    trunk = G.tube(tpath, radii, 9, twist=0.15, lobe=flare(tpath, 0.5, 0.7, 5, rng.uniform(0, 6), ripple=0.05),
                   uv=uvr('bark', 8.0))
    wood_color(trunk, WOOD_SUGI, ground=0.7, shade_z=zb + 0.3, shade=0.4)
    pieces.append(LV.hidden_in(trunk, masses, 0.62))
    # limbs out to the outer clumps (they show in the gaps), and dead stubs on the clear trunk below
    for m in masses[:n]:
        j = int(np.argmin(np.abs(tpath[:, 2] - (m.c[2] - 0.35))))
        p0 = tpath[j]
        r0 = max(0.025, radii[j] * 0.28)
        path = limb_path(p0, m.c - UP * m.r[2] * 0.3, rng, sag=0.06, rise=0.0, n=4, wob=0.04)
        b = G.tube(path, np.linspace(r0, r0 * 0.4, len(path)), 5, uv=uvr('bark', 8.0, p0[2]))
        wood_color(b, WOOD_SUGI, ground=1.0, shade_z=H, shade=0.0)
        b.color(b.C[:, :3] * 0.7)
        pieces.append(LV.hidden_in(b, masses, 0.62))
    for k in range(5):
        z = rng.uniform(2.4, zb - 0.1); a = rng.uniform(0, 2 * PI)
        j = int(np.argmin(np.abs(tpath[:, 2] - z)))
        d = np.array((math.cos(a), math.sin(a), -0.25))
        stub = G.tube(np.array([tpath[j], tpath[j] + d * rng.uniform(0.3, 0.6)]), [radii[j] * 0.16, 0.012], 4,
                      uv=uvr('bark', 8.0, z))
        wood_color(stub, '#5a463c', ground=1.0)
        pieces.append(stub)
    return pieces, {0: G.hexc(WOOD_SUGI), 1: R_SUGI.base}, {'kind': 'tree', 'trunkRadius': tr}


# ================================================================ cherry in leaf
def build_cherry_leaf():
    # A Somei-yoshino in May: the dark, lenticel-banded trunk forks low into a few wide, rising limbs that spread a
    # broad, rather flat-topped crown of fresh green leaves (the blossom is long gone).
    rng = RNG(613)
    tr = 0.34
    masses = LV.masses_from((0.0, 0.05, 4.7), (4.2, 3.1, 1.85), 13, rng, rf=(0.31, 0.39), shell=0.68, zlo=-0.45,
                            top=0.32)
    for m in masses:                                     # the crown flattens and droops a little at its rim
        m.c[2] -= 0.35 * (abs(m.c[0]) / 3.6) ** 2
    ctrl = [(0, 0, -0.12), (0.16, 0.0, 0.7), (-0.08, 0.05, 1.3), (0.04, 0.0, 1.9), (0.0, 0.05, 3.4)]
    pieces, C0, Rc = leaf_tree(613, masses, ctrl, tr, 1.35, R_SAKURA, WOOD_SAKURA, card=1.3, density=0.95,
                               region='cherry', limb_r=(0.62, 0.75), flare_amt=0.5, taper=0.72, open_under=0.35,
                               groups=5, fork_spread=0.4, limb_end=0.25, twigs=3, twig_r=0.05, rng=rng)
    return pieces, {0: G.hexc(WOOD_SAKURA), 1: R_SAKURA.base}, {'kind': 'tree', 'trunkRadius': tr}


# ================================================================ persimmon
def build_persimmon():
    # A kaki in a house garden: a dark, blocky trunk and crooked limbs, an open, irregular crown with sky and branches
    # showing through, its May leaves a fresh light yellow-green.
    rng = RNG(719)
    tr = 0.19
    masses = LV.masses_from((0.1, 0.0, 4.05), (2.6, 2.2, 1.65), 8, rng, rf=(0.31, 0.4), shell=0.74, zlo=-0.5,
                            top=0.36, shell_jit=(0.85, 1.25))
    ctrl = [(0, 0, -0.1), (0.1, 0.0, 0.8), (-0.08, 0.03, 1.5), (0.14, 0.0, 2.5), (0.05, 0.05, 3.9)]
    pieces, C0, Rc = leaf_tree(719, masses, ctrl, tr, 1.45, R_KAKI, WOOD_KAKI, card=1.1, density=0.8, inner=0.25,
                               core=0.48, limb_r=(0.55, 0.7), flare_amt=0.35, taper=0.62, open_under=0.5, twigs=4,
                               twig_r=0.04, groups=4, fork_spread=0.8, limb_end=0.12, rng=rng)
    return pieces, {0: G.hexc(WOOD_KAKI), 1: R_KAKI.base}, {'kind': 'tree', 'trunkRadius': tr}


# ================================================================ bamboo
def culm(base, out, H, r0, rng, lean, arch, old=False, sides=5):
    """One culm: it rises almost straight, leaning outward by `lean` per metre, and its top arches over (out) by `arch`
    metres. Below the leafy top it is a stack of internodes, each mapped once over the palm-ring tile: the tile's dark
    groove at the bottom of an internode and its pale lip at the top read as the node's ring with the pale waxy band
    under it."""
    base = np.asarray(base, float); out = G.unit(np.asarray(out, float))
    ctrl = [base - UP * 0.12, base + out * lean * H * 0.3 + UP * H * 0.3,
            base + out * lean * H * 0.58 + UP * H * 0.58,
            base + out * (lean * H * 0.8 + arch * 0.3) + UP * (H * 0.82 - arch * 0.05),
            base + out * (lean * H * 0.9 + arch) + UP * (H - arch * 0.75)]
    path = G.catmull(ctrl, 60)
    L = G.arclen(path)
    total = L[-1]
    col = G.hexc(CULM_OLD if old else CULM)
    u0, v0, u1, v1 = AT.REG['palm']; m = AT.MARGIN
    pieces = []
    s = 0.0
    node_end = total * 0.55
    nodes = []
    while s < node_end:
        ln = 0.24 + 0.2 * min(1.0, s / 3.0)                  # short internodes low down, longer above
        a = np.array([np.interp(s, L, path[:, i]) for i in range(3)])
        b = np.array([np.interp(min(s + ln, total), L, path[:, i]) for i in range(3)])
        ra = r0 * (1 - 0.5 * s / total); rb = r0 * (1 - 0.5 * (s + ln) / total)
        seg = G.tube(np.array([a, b]), [ra, rb * 1.06], sides, uv=(u0 + m, v0 + m, u1 - m, v1 - m, lambda s_, i: float(i)))
        z = seg.V[:, 2]
        seg.color(col[None, :] * (0.72 + 0.28 * G.smoothstep(0.0, 2.5, z))[:, None]); seg.part(0)
        pieces.append(seg)
        nodes.append((s + ln, b))
        s += ln
    # the leafy top: one smooth tapering tube to the tip
    i0 = int(np.searchsorted(L, s - 1e-6))
    top = [nodes[-1][1]]
    for q in list(path[i0 + 1::5]) + [path[-1]]:
        if np.linalg.norm(q - top[-1]) > 0.15:
            top.append(q)
    top = np.array(top)
    rt = r0 * (1 - 0.5 * s / total)
    tt = G.tube(top, np.linspace(rt, rt * 0.12, len(top)), 4, tip=True, uv=(u0 + m, v0 + m, u1 - m, v1 - m, lambda s_, i: 0.55))
    tt.color(col * 0.95); tt.part(0)
    pieces.append(tt)
    return pieces, path, L


def build_bamboo():
    # A clump of bamboo by a temple path: a dozen slender culms, a few older and yellower, rising close together and
    # fanning out a little, their tops arching over under feathery sprays of narrow hanging leaves that run down the
    # upper half of each culm, with sky between the culms' sprays.
    rng = RNG(829)
    pieces = []; masses = []; twigs = []
    n = 12
    ga = PI * (3 - 5 ** 0.5)
    for k in range(n):
        f = math.sqrt((k + 0.5) / n)
        a = ga * k + rng.normal(0, 0.2)
        base = np.array((math.cos(a) * f * 0.8, math.sin(a) * f * 0.55, 0.0))
        outward = np.array((math.cos(a), math.sin(a) * 0.8, 0.0)) + np.array((0.2, 0.0, 0.0)) + rng.normal(0, 0.25, 3) * np.array((1, 1, 0))
        H = rng.uniform(8.4, 9.8) - 1.2 * (k % 5 == 4)
        r0 = rng.uniform(0.04, 0.052)
        lean = 0.06 + 0.1 * f + rng.uniform(-0.01, 0.02)
        arch = rng.uniform(1.8, 2.8)
        cp, path, L = culm(base, outward, H, r0, rng, lean, arch, old=(k % 4 == 3))
        pieces += cp
        total = L[-1]
        dirn = G.unit(path[-1] - path[len(path) // 2])
        side = G.unit(np.cross(UP, G.unit(outward)))
        tone = rng.uniform(-0.06, 0.06)
        for j, t in enumerate(np.linspace(0.46, 0.98, 8)):
            sp = t * total
            q = np.array([np.interp(sp, L, path[:, i]) for i in range(3)])
            sd = side * (1 if j % 2 else -1)
            r = (0.26 + 0.2 * t) * rng.uniform(0.85, 1.15)
            c = q + sd * r * 0.7 - UP * r * 0.45
            masses.append(LV.Mass(c, (r * 1.1, r, r * 0.7), bright=tone + rng.uniform(-0.04, 0.04)))
            twigs.append((q, c, r))
    lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
    C0 = (lo + hi) / 2; Rc = (hi - lo) / 2
    pieces.append(hanging_cards(masses, rng, R_TAKE, 'bamboo', 0.5, density=0.45, inner=0.2, spin=0.3, C0=C0, Rc=Rc,
                                rho=(0.55, 1.0), crease=0.15))
    # the branchlets out to the sprays: thin, dark green
    for (q, c, r) in twigs:
        p1 = c + rng.normal(0, 0.12, 3) * r
        b = G.tube(limb_path(q, p1, rng, sag=0.08, rise=0.0, n=3, wob=0.05), np.linspace(0.011, 0.005, 3), 3)
        b.color(G.hexc('#4f6a32') * 0.85); b.part(0)
        pieces.append(b)
    return pieces, {0: G.hexc(CULM), 1: R_TAKE.base}, {'kind': 'tree', 'trunkRadius': 0.05, 'culms': n}


# ================================================================ shrubs
def card_bush(seed, spec, ramp, height, card=0.68, density=1.35, inner=0.3, rho=(0.74, 1.0), tilt=0.3, core=0.52,
              flowers=None, rng=None):
    """kit_plants.card_bush: a low cluster of leaf cards over dark cores. Returns (pieces, masses, rng) before
    grounding, so flowers can be added. flowers: (ramp, density, sprite, size, rho)."""
    rng = rng or RNG(seed)
    masses = [LV.Mass(np.array(c) * (0.85, 0.85, 1.0), np.array(r if np.ndim(r) else (r, r * 0.94, r * 0.88)) * 0.78,
                      bright=rng.uniform(-0.04, 0.04)) for c, r in spec]
    pieces = [LV.leaf_cards(masses, rng, ramp, 1, 'leaf', size=card, density=density, inner=inner, open_under=0.1,
                            nmix=(0.65, 0.3, 0.2), tilt=tilt, crease=0.25, rho=rho)]
    if flowers:
        fr, fd, fs, fsize, frho = flowers
        pieces.append(LV.leaf_cards(masses, rng, fr, 2, fs, size=fsize, density=fd, inner=0.0, rho=frho,
                                    open_under=0.7, nmix=(0.7, 0.25, 0.15), tilt=0.45, crease=0.1))
    pieces += LV.cores(masses, rng, ramp, 1, scale=core, s=(0.0, 0.1))
    return pieces, masses, rng


def build_hydrangea():
    # An ajisai: a rounded bush of broad leaves carrying big mophead flower heads, blue and violet, over its top and
    # sides (each a dense ball of florets: a small solid core under crossed floret cards).
    spec = [((0, 0.0, 0.62), (0.62, 0.55, 0.5)), ((-0.48, -0.06, 0.45), 0.42), ((0.5, -0.02, 0.48), 0.43),
            ((0.05, -0.4, 0.44), 0.4), ((-0.08, 0.38, 0.46), 0.38), ((0.22, -0.12, 0.9), 0.38),
            ((-0.28, 0.04, 0.86), 0.35)]
    pieces, masses, rng = card_bush(37, spec, R_AJISAI, 1.2, card=0.66, density=0.97, inner=0.2)
    heads = []
    lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
    C0 = (lo + hi) / 2
    tries = 0
    while len(heads) < 18 and tries < 600:
        tries += 1
        m = masses[int(rng.integers(len(masses)))]
        d = G.unit(rng.normal(size=3) + np.array((0, -0.35, 0.55)))
        if d[2] < -0.05: continue
        p = m.point(d, rng.uniform(0.9, 1.02))
        if min(o.e(p)[0] for o in masses if o is not m) < 0.9: continue
        r = rng.uniform(0.12, 0.155)
        if any(np.linalg.norm(p - h[0]) < (r + h[1]) * 1.05 for h in heads): continue
        heads.append((p, r, int(rng.integers(len(HYDRANGEA)))))
    for (p, r, ci) in heads:
        ramp = G.Ramp(*HYDRANGEA[ci])
        out = G.unit(p - C0 + np.array((0, 0, 0.3)))
        b = G.blob(p, (r * 0.85, r * 0.85, r * 0.72), 1, rng, bumps=4, amp=0.12, size=0.9, flat=0.6)
        b.N = G.unit(0.6 * G.unit(b.V - p) + 0.4 * out)
        b.color(ramp(0.25 + 0.5 * G.smoothstep(-1, 1, b.A['lz']))); b.part(2)
        pieces.append(b)
        V, F, N, C, U = [], [], [], [], []
        yaw0 = rng.uniform(0, PI)
        for q in range(3):                    # three crossed floret cards, each lit as the head's outward side
            yaw = yaw0 + q * PI / 3
            g = np.array((math.cos(yaw), math.sin(yaw), rng.normal(0, 0.25)))
            right = G.unit(np.cross(UP, g)); up = np.cross(G.unit(g), right)
            psi = rng.uniform(0, 2 * PI)
            Rv = math.cos(psi) * right + math.sin(psi) * up; Uv = -math.sin(psi) * right + math.cos(psi) * up
            h = r * 1.15
            c = p + out * r * 0.15
            base = len(V)
            V += [c - Rv * h - Uv * h, c + Rv * h - Uv * h, c + Rv * h + Uv * h, c - Rv * h + Uv * h]
            N += [out] * 4
            C += [ramp(0.62 + rng.uniform(-0.05, 0.08))] * 4
            U += list(AT.sprite_uv('floret', 0, np.array((0, 1, 1, 0.0)), np.array((0, 0, 1, 1.0))))
            F.append((base, base + 1, base + 2, base + 3))
        pc = G.Piece(np.array(V), F, N=np.array(N)); pc.C[:, :3] = np.array(C); pc.U = np.array(U); pc.part(2)
        pc.tag('windz', [p[2]] * len(V))
        pieces.append(pc)
    pieces = ground(pieces, 1.2)
    base2 = np.mean([G.Ramp(*h).base for h in HYDRANGEA[:2]], axis=0)
    return pieces, {1: R_AJISAI.base, 2: base2}, {'kind': 'bush', 'flowerColorsVary': True}


def build_azalea():
    # A clipped azalea (tsutsuji) mound in a front garden: one smooth, low dome of small dark leaves, clipped close, so
    # thickly covered in pink-magenta flowers that the leaves show only in its shade.
    spec = [((0, 0.0, 0.5), (0.95, 0.75, 0.62)), ((-0.55, 0.05, 0.36), (0.5, 0.5, 0.42)),
            ((0.58, -0.02, 0.38), (0.5, 0.5, 0.42))]
    flowers = (R_TSUTSUJI, 1.5, 'blossom', 0.42, (0.93, 1.03))
    pieces, masses, rng = card_bush(41, spec, R_TSUTSUJI_L, 0.9, card=0.44, density=0.7, inner=0.15, rho=(0.84, 1.0),
                                    tilt=0.4, core=0.7, flowers=flowers)
    pieces = ground(pieces, 0.9)
    return pieces, {1: R_TSUTSUJI_L.base, 2: R_TSUTSUJI.base}, {'kind': 'bush'}
