# The PLANTS kit for Dribble To School: original stylized 3D vegetation (trees, palms, bushes,
# clipped hedges, grasses and flowers) that replaces the flat 2D tree and bush cut-outs.
#   blenv/bin/python kit_plants.py -- /abs/outdir [--only A,B]
# Writes into outdir: <Model>.fbx per model, PlantsAtlas.png, Plants.json, Plants.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Plants.blend /abs/outdir/plants_sheet.png
#
# Look (docs/ART_DIRECTION.md): chunky, slightly exaggerated shapes with crisp silhouettes;
# painted vertex-colour gradients (light, warm tops; dark, cool undersides and crevices); a few
# crafted strokes from the atlas (bark, birch marks, needles, palm leaflets, hedge leaves).
#   Conifers   stacked drooping tiers: smooth skirts that split into spiky fronds at the rim, trunk at the base
#   Broadleaf  lumpy cumulus crowns of clumps, crevice shading and a dark core showing in the gaps
#   Birch      white twin stems with dark marks, small airy clumps
#   Cherry     a dark twisting trunk under a wide, frothy blossom crown dotted with pale sprays
#   Palms      ringed curved trunks, arching comb-edged fronds, coconuts, a dry frond hanging under
#   Bushes     clump masses; the flowering shrub adds flower dots
#   Hedges     clipped blocks with a lumpy leafy top that tile end to end along X
#   Grasses    fans of solid tapered blades (triangular section, no alpha)
#
# Space: metres, Z up, front faces -Y, origin at the base on the ground (z = 0). Trunks, stems
# and hedges reach a few centimetres below z = 0 so they sit into uneven ground.
# Each FBX: one mesh named after the model, plus Attach.Front at (0, -1, 0).
# Vertex data (kit_lib contract): colour (sRGB in the FBX) x PlantsAtlas.png; UV0 the atlas;
# UV1.x the recolour part (0 fixed: wood, coconuts, dry palm fronds, flower centres, reed heads; 1 foliage;
# 2 flowers and blossom). Part 1 and 2 colours carry baked shading around the part's base colour
# (recorded in Plants.json), so the game's brightness-ratio recolour keeps it.
# Vertex colour ALPHA is a wind weight: 0 at the rooted base, rising to 1 at the top and tips
# ((height / model height)^1.5 for trees and bushes, along the blade for grasses).
# Normals are custom: clumps shade like soft balls (blended with the crown's own roundness),
# tiers and fronds blend their surface with the plant's overall form, so cel light falls in
# clean, large shapes.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
import kit_lib as K
import kit_plants_geo as G
import kit_plants_atlas as AT

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS and not ARGS[0].startswith('--') else os.path.abspath('plants_out')
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None
UP = np.array((0.0, 0.0, 1.0))
PI = math.pi

# ---------------------------------------------------------------- palette (sRGB hex)
# Foliage ramps: (deep shade, base, sunlit top). The base is the part's recorded base colour.
R_CONIFER = G.Ramp('#123433', '#2f6450', '#93bb66')
R_BROAD = G.Ramp('#284a38', '#5f9440', '#d2d872')
R_BROAD_L = G.Ramp('#2a4636', '#6f9038', '#dccf6a')
R_BIRCH = G.Ramp('#3e6038', '#93b84a', '#eeea86')
R_BLOSSOM = G.Ramp('#9c3f6e', '#ec93b5', '#ffcfdf')
R_PALM = G.Ramp('#24503c', '#5c9a44', '#cfe07a')
R_BUSH = G.Ramp('#223f30', '#4f863e', '#a9c862')
R_SHRUB = G.Ramp('#1f3b33', '#477a40', '#97ba5e')
R_SHRUB_FL = G.Ramp('#a8345e', '#e8628f', '#ffc4d6')
R_HEDGE = G.Ramp('#1c362b', '#4a7a3a', '#a8c664')
R_GOLD = G.Ramp('#6e5a2a', '#d0a54c', '#f7e3a0')
R_GOLD_T = G.Ramp('#6a5028', '#c9973f', '#f6dc96')
R_DUNE = G.Ramp('#4f5f38', '#a2a660', '#f0e09a')
R_REED = G.Ramp('#34502e', '#7a9646', '#cfd47c')
R_MEADOW = G.Ramp('#2a5432', '#5b9a46', '#b4d874')
R_DRY = G.Ramp('#5e4628', '#a5854f', '#dcc38a')        # old palm fronds (fixed, part 0)

WOOD = '#6c5242'       # broadleaf bark
WOOD_CONIFER = '#6e4a36'
WOOD_BIRCH = '#f1ede4'
WOOD_TWIG = '#4a403c'
WOOD_CHERRY = '#4c3538'
WOOD_PALM = '#a3845f'

RNG = lambda seed: np.random.default_rng(seed)


def uvr(name, span, offset=0.0):
    """tube() uv spec: around the region's width, along its height (span metres per region)."""
    u0, v0, u1, v1 = AT.REG[name]; m = AT.MARGIN
    return (u0 + m, v0 + m, u1 - m, v1 - m, lambda s, i: min(max((s + offset) / span, 0.0), 1.0))


def wood_color(p, hexcol, ground=0.62, shade_z=None, shade=0.35):
    """Bark colour, darker at the ground and in the crown's shade (part 0)."""
    z = p.V[:, 2]
    k = 1 - (1 - ground) * G.smoothstep(0.7, 0.0, z)
    if shade_z is not None:
        k = k * (1 - shade * G.smoothstep(shade_z - 1.4, shade_z + 0.2, z))
    p.color(G.hexc(hexcol)[None, :] * k[:, None])
    p.part(0)
    return p


def sink_base(p, z=-0.15):
    """Level a leaning trunk's first ring below the ground, so no edge of it peeks above z = 0."""
    p.V[p.A['ring'] == 0, 2] = z
    return p


def ground(pieces, height=None, sink=0.03):
    """Set a clump mass down on the ground: its lowest point `sink` below z = 0 and, if given,
    its top at `height` (a vertical stretch; normals follow)."""
    zmin = min(p.V[:, 2].min() for p in pieces); zmax = max(p.V[:, 2].max() for p in pieces)
    k = 1.0 if height is None else (height + sink) / (zmax - zmin)
    M = np.eye(4); M[2, 2] = k; M[2, 3] = -sink - zmin * k
    for p in pieces:
        p.move(M)
    return pieces


def flare(path, amount=0.45, height=0.75, roots=4, phase=0.0, ripple=0.04):
    """Root flare: buttress lobes at the base fading out by `height`, a slight ripple above."""
    def f(i, ang):
        z = path[i][2]
        a = float(G.smoothstep(height, 0.0, z))
        lob = np.maximum(0.0, np.cos(roots * (ang - phase))) ** 3
        return 1 + a * (amount * lob + 0.12) + ripple * np.cos(3 * ang + 1.7 * i)
    return f


# ---------------------------------------------------------------- foliage crowns
def make_clumps(spec, rng, freq_front=3, freq_back=2, small=0.42, big=None):
    """spec: list of (centre, radius or (rx, ry, rz)[, flat]). Back clumps (y > 0.35 r) and clumps
    smaller than `small` get a lighter mesh."""
    out = []
    for s in spec:
        c = np.array(s[0], float)
        r = np.array(s[1] if np.ndim(s[1]) else (s[1], s[1] * 0.94, s[1] * 0.9), float)
        flat = s[2] if len(s) > 2 else 0.72
        f = freq_front if c[1] < 0.35 * r.mean() else freq_back
        if r.mean() < small: f = min(f, 2)
        if big is not None and r.mean() > big and c[1] < 0.35 * r.mean(): f = freq_front + 1
        out.append({'c': c, 'r': r, 'flat': flat, 'f': f})
    return out


def crown(clumps, ramp, part, rng, C0, Rc, core=0.62, nmix=(0.5, 0.35, 0.15), shade_bias=0.0,
          bumps=(5, 8), amp=0.13, size=0.8, crev=0.38):
    """Lumpy clump masses: blobs, culled where hidden inside each other, shaded light on top, dark
    under and in the creases between clumps; a dark core fills the gaps with depth."""
    C0 = np.asarray(C0, float); Rc = np.asarray(Rc, float)
    zmin = min(c['c'][2] - c['r'][2] * c['flat'] for c in clumps)
    zmax = max(c['c'][2] + c['r'][2] * 1.1 for c in clumps)
    out = []
    for i, cl in enumerate(clumps):
        b = G.blob(cl['c'], cl['r'], cl['f'], rng, bumps=int(rng.integers(bumps[0], bumps[1] + 1)),
                   amp=cl.get('amp', amp), size=size, flat=cl['flat'])
        inside = np.zeros(len(b), bool); emin = np.full(len(b), 9.0)
        for j, o in enumerate(clumps):
            if j == i: continue
            e = G.ellipsoid_e(b.V, o['c'], o['r'], o['flat'])
            inside |= e < 0.97
            emin = np.minimum(emin, e)
        b.tag('emin', emin)
        b = G.cull(b, inside)
        if not len(b): continue
        dl = G.unit((b.V - cl['c']) / cl['r'])
        dc = G.unit((b.V - C0) / Rc)
        hz = (b.V[:, 2] - zmin) / max(zmax - zmin, 1e-3)
        outward = np.sum(dl * dc, axis=1)
        cr = G.smoothstep(1.28, 1.0, b.A['emin'])
        s = (0.5 + shade_bias + 0.22 * b.A['lz'] + 0.22 * (2 * hz - 1) + 0.10 * outward - crev * cr
             + rng.uniform(-0.05, 0.05))
        b.color(ramp(s)); b.part(part)
        b.N = G.unit(nmix[0] * dl + nmix[1] * dc + nmix[2] * b.N)
        out.append(b)
    if core:
        cb = G.blob(C0, Rc * core, 2, rng, bumps=4, amp=0.1, flat=0.8)
        inside = np.zeros(len(cb), bool)
        for o in clumps:
            inside |= G.ellipsoid_e(cb.V, o['c'], o['r'], o['flat']) < 0.97
        cb = G.cull(cb, inside)
        if len(cb):
            cb.color(ramp(0.06 + 0.12 * G.smoothstep(C0[2] - Rc[2], C0[2] + Rc[2], cb.V[:, 2])))
            cb.part(part)
            out.append(cb)
    return out


def cull_in(p, clumps, thresh=0.92):
    inside = np.zeros(len(p), bool)
    for o in clumps:
        inside |= G.ellipsoid_e(p.V, o['c'], o['r'], o['flat']) < thresh
    return G.cull(p, inside)


def branch(p0, p1, r0, r1, rng, sides=6, bend=0.25, segs=4, mid=None, region='bark', span=8.0, offset=0.0):
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    if mid is None:
        d = p1 - p0
        mid = p0 + d * 0.5 + UP * np.linalg.norm(d) * bend * 0.5 + rng.normal(0, 0.06, 3)
    path = G.catmull([p0, mid, p1], segs + 1)
    radii = np.linspace(r0, r1, len(path))
    return G.tube(path, radii, sides, uv=uvr(region, span, offset))


# ---------------------------------------------------------------- broadleaf trees
def broadleaf_tree(seed, crown_c, crown_r, n_clumps, trunk_r, fork_z, ramp, n_limbs=5, clump_rf=(0.36, 0.47),
                   leader=True, wood=WOOD, core=0.6, big=1.05, limb_r=(0.42, 0.55), zlo=-0.55):
    """A cumulus crown (a big central clump and a golden-angle spiral of clumps over the crown
    envelope, top to bottom) on a gently S-curved trunk whose limbs reach the lower clumps."""
    rng = RNG(seed)
    C0 = np.array(crown_c, float); Rc = np.array(crown_r, float)
    spec = [(C0 + rng.normal(0, 0.05, 3), Rc * 0.66)]
    ga = PI * (3 - 5 ** 0.5); ph = rng.uniform(0, 2 * PI)
    for k in range(n_clumps):
        zf = max(1 - 1.55 * (k + 0.5) / n_clumps, zlo)      # from the top down, stop short of the bottom
        rr = math.sqrt(max(0.0, 1 - zf * zf))
        a = ph + ga * k
        d = np.array((rr * math.cos(a), rr * math.sin(a) * 0.9, zf))
        pos = C0 + d * Rc * rng.uniform(0.6, 0.7)
        rad = Rc.mean() * rng.uniform(*clump_rf) * (1.0 + 0.12 * zf)
        spec.append((pos, (rad, rad * 0.95, rad * 0.86)))
    clumps = make_clumps(spec, rng, big=big)
    pieces = crown(clumps, ramp, 1, rng, C0, Rc, core=core)
    # trunk: a gentle S up to the fork, then on as a leader into the crown
    top_z = C0[2] + (0.15 * Rc[2] if leader else -0.3 * Rc[2])
    tpath = G.catmull([(0, 0, -0.12), (0.03, -0.02, fork_z * 0.45), (-0.04, 0.02, fork_z),
                       (0.05, 0.0, (fork_z + top_z) / 2), (0.0, 0.05, top_z)], 10)
    radii = trunk_r * (1 - 0.66 * np.linspace(0, 1, len(tpath)) ** 0.8)
    trunk = G.tube(tpath, radii, 9, lobe=flare(tpath, 0.5, 0.8, 4, rng.uniform(0, 6)), uv=uvr('bark', 8.0))
    wood_color(trunk, wood, shade_z=C0[2] - Rc[2] * 0.72)
    trunk = cull_in(trunk, clumps)
    parts = [trunk]
    # limbs from around the fork to the lower clumps, so they show under the crown and in the gaps
    low = sorted(range(len(clumps)), key=lambda i: clumps[i]['c'][2])
    chosen = [i for i in low if np.linalg.norm(clumps[i]['c'][:2] - C0[:2]) > 0.25 * Rc[0]][:n_limbs]
    for k, i in enumerate(chosen):
        cl = clumps[i]
        z0 = fork_z + rng.uniform(-0.15, 0.6) * (1 if k else 0)
        p0 = np.array((0.0, 0.0, z0))
        p1 = cl['c'] + np.array((0, 0, -0.1 * cl['r'][2]))
        p1 = p0 + (p1 - p0) * 0.92
        b = branch(p0, p1, trunk_r * rng.uniform(*limb_r), trunk_r * 0.16, rng, sides=6, bend=0.2, offset=z0)
        wood_color(b, wood, shade_z=z0 + 0.3, shade=0.4)
        parts.append(cull_in(b, clumps))
    return pieces + parts, clumps


def build_broadleaf():
    tr = 0.27
    pieces, clumps = broadleaf_tree(21, (0, 0, 4.45), (2.75, 2.35, 2.45), 12, tr, 2.3, R_BROAD)
    return pieces, {0: G.hexc(WOOD), 1: R_BROAD.base}, {'kind': 'tree', 'trunkRadius': tr}


def build_broadleaf_large():
    # a broad, spreading crown: wider than tall, on a stout trunk with two big limbs
    tr = 0.4
    pieces, clumps = broadleaf_tree(78, (0, 0.05, 6.05), (4.1, 2.8, 2.75), 16, tr, 2.5, R_BROAD_L,
                                    n_limbs=7, clump_rf=(0.32, 0.41), core=0.5, limb_r=(0.4, 0.5), zlo=-0.45, big=1.2)
    return pieces, {0: G.hexc(WOOD), 1: R_BROAD_L.base}, {'kind': 'tree', 'trunkRadius': tr}


def shell_clumps(center, radii, n, rng, rf=(0.42, 0.55), shell=(0.62, 0.74), zlo=-0.5, elong=1.12, flat=0.78):
    """Clumps spread over an ellipsoidal crown envelope (golden-angle spiral, top to bottom)."""
    c0 = np.array(center, float); R = np.array(radii, float)
    ga = PI * (3 - 5 ** 0.5); ph = rng.uniform(0, 2 * PI)
    out = []
    for k in range(n):
        zf = 1 - (1 - zlo) * (k + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - zf * zf))
        a = ph + ga * k
        d = np.array((rr * math.cos(a), rr * math.sin(a), zf))
        pos = c0 + d * R * rng.uniform(*shell)
        r = R[:2].mean() * rng.uniform(*rf)
        out.append((pos, (r, r * 0.92, r * elong), flat))
    return out


def build_birch():
    rng = RNG(31)
    # two white stems, the second leaning away to the left
    s1 = G.catmull([(0.05, 0, -0.1), (0.12, 0.02, 2.0), (0.02, 0.05, 4.2), (0.22, 0.0, 6.5)], 9)
    s2 = G.catmull([(-0.08, 0.06, -0.1), (-0.3, 0.05, 1.8), (-0.7, 0.12, 3.8), (-0.98, 0.18, 5.4)], 8)
    stems = [(s1, 0.15), (s2, 0.11)]
    # loose groups of small drooping clumps along the upper stems, with gaps between the groups
    groups = [((0.85, -0.05, 3.75), 3, 0), ((0.6, 0.12, 5.05), 4, 0), ((0.12, -0.05, 6.3), 4, 0),
              ((-0.32, -0.22, 5.45), 3, 0), ((-1.5, 0.08, 3.95), 3, 1), ((-1.02, 0.22, 5.25), 4, 1)]
    spec = []
    for (gc, n, si) in groups:
        gc = np.array(gc)
        r = rng.uniform(0.47, 0.54)
        spec.append((gc, (r, r * 0.9, r * 1.12), 0.85))
        a0 = rng.uniform(0, 2 * PI)
        for k in range(n - 1):
            a = a0 + 2 * PI * k / (n - 1) + rng.normal(0, 0.3)
            off = np.array((math.cos(a) * 0.46, math.sin(a) * 0.32, rng.uniform(-0.3, 0.12)))
            rr = rng.uniform(0.34, 0.42)
            spec.append((gc + off, (rr, rr * 0.9, rr * 1.15), 0.85))
    clumps = make_clumps(spec, rng, small=0.44)
    C0 = np.array((-0.3, 0.05, 5.0)); Rc = np.array((1.9, 1.0, 1.8))
    pieces = crown(clumps, R_BIRCH, 1, rng, C0, Rc, core=0, nmix=(0.62, 0.23, 0.15), crev=0.32, amp=0.16, size=0.7)
    for (path, r0) in stems:
        radii = r0 * (1 - 0.75 * np.linspace(0, 1, len(path)) ** 1.1)
        t = G.tube(path, radii, 8, lobe=flare(path, 0.25, 0.5, 3, rng.uniform(0, 6), 0.02), uv=uvr('birch', 7.0))
        wood_color(t, WOOD_BIRCH, ground=0.8, shade_z=None)
        pieces.append(cull_in(t, clumps))
    # thin dark twigs from the stems out to each group
    for (gc, n, si) in groups:
        path = stems[si][0]
        gc = np.array(gc)
        j = int(np.argmin(np.linalg.norm(path - (gc - UP * 0.9), axis=1)))
        p0 = path[max(j, 2)]
        b = branch(p0, gc - UP * 0.1, 0.045, 0.016, rng, sides=4, bend=0.12, segs=3)
        wood_color(b, WOOD_TWIG, ground=1.0)
        pieces.append(cull_in(b, clumps))
    return pieces, {0: G.hexc(WOOD_BIRCH), 1: R_BIRCH.base}, {'kind': 'tree', 'trunkRadius': 0.15}


def build_cherry():
    rng = RNG(47)
    # a dark trunk that twists and leans, splitting into spreading limbs under a wide blossom crown
    tpath = G.catmull([(0, 0, -0.1), (0.15, 0.0, 0.8), (-0.12, 0.05, 1.5), (-0.05, 0.0, 2.0)], 8)
    trunk = G.tube(tpath, np.linspace(0.27, 0.2, len(tpath)), 9, twist=2.2,
                   lobe=lambda i, ang: flare(tpath, 0.45, 0.6, 3, 0.5)(i, ang) * (1 + 0.10 * np.cos(3 * ang)),
                   uv=uvr('cherry', 7.0))
    wood_color(trunk, WOOD_CHERRY, ground=0.7, shade_z=2.6, shade=0.25)
    sink_base(trunk)
    C0 = np.array((0.0, 0.05, 3.7)); Rc = np.array((3.05, 1.65, 2.05))
    spec = [(C0 + np.array((0, 0, 0.15)), Rc * np.array((0.6, 0.62, 0.6)), 0.6)]
    spec += shell_clumps(C0, Rc, 18, rng, rf=(0.31, 0.39), shell=(0.66, 0.76), zlo=-0.45, elong=0.86, flat=0.66)
    clumps = make_clumps(spec, rng, big=1.05)
    fork = np.array((-0.05, 0.0, 1.95))
    pieces = [trunk]
    low = sorted(range(1, len(clumps)), key=lambda i: clumps[i]['c'][2])
    ends = [i for i in low if abs(clumps[i]['c'][0]) > 0.8][:6]
    for li, ci in enumerate(ends):
        c = clumps[ci]['c'] - UP * 0.2
        a0 = fork if li < 4 else fork + UP * 0.45
        mid = a0 + (c - a0) * 0.45 + UP * 0.35 + rng.normal(0, 0.12, 3)
        path = G.catmull([a0, mid, c], 6)
        r0 = 0.15 if li < 4 else 0.1
        t = G.tube(path, np.linspace(r0, r0 * 0.35, len(path)), 7, twist=1.2, uv=uvr('cherry', 7.0, a0[2]))
        wood_color(t, WOOD_CHERRY, ground=1.0, shade_z=3.2, shade=0.3)
        pieces.append(cull_in(t, clumps))
    blossom = crown(clumps, R_BLOSSOM, 2, rng, C0, Rc, core=0.5, nmix=(0.5, 0.35, 0.15), amp=0.2, size=0.62, crev=0.45,
                    bumps=(6, 9))
    pieces += blossom
    pieces[0] = cull_in(pieces[0], clumps)

    # pale blossom sprays dotted over the sunny face of the crown
    def col(h, rng):
        sh = 0.86 + 0.14 * h + rng.uniform(-0.05, 0.03)
        return R_BLOSSOM(sh), G.hexc('#fff3f6')
    pieces += scatter_dots(blossom[:-1], rng, 18, (2, 3), (0.08, 0.11), 0.55, col, zmin=3.0, spread=0.17)
    return pieces, {0: G.hexc(WOOD_CHERRY), 2: R_BLOSSOM.base}, {'kind': 'tree', 'trunkRadius': 0.27}


# ---------------------------------------------------------------- conifers
def flat_radial(V, ctr):
    """Horizontal unit vectors away from the axis through ctr (straight up on the axis)."""
    d = np.concatenate([V[:, :2] - np.asarray(ctr)[:2], np.zeros((len(V), 1))], 1)
    n = np.linalg.norm(d, axis=1)
    d[n < 1e-6] = UP
    return G.unit(d)


def conifer_tier(z0, R, D, N, rng, rt, fr, ramp, apex=None, center=(0, 0)):
    """One tier: a smooth drooping skirt near the trunk that splits into spiky fronds at the rim
    (a star outline with concave notches between drooping tips), closed by a dark underside."""
    M = 4 * N
    phase = rng.uniform(0, 2 * PI)
    slen = rng.uniform(0.88, 1.08, N) * np.where(np.arange(N) % 2, 0.93, 1.0)
    sjit = rng.uniform(-0.1, 0.1, N)
    sbri = rng.uniform(-0.05, 0.05, N)
    ang = np.zeros(M); W = np.zeros(M); RF = np.zeros(M); BR = np.zeros(M)
    for k in range(N):
        for q, (w, rf) in enumerate(((0.0, 0.6), (0.5, 0.76), (1.0, 1.0), (0.5, 0.76))):
            j = k * 4 + q
            jj = sjit[k] if q == 2 else (sjit[k] * 0.5 if q in (1, 3) else 0.0)
            ang[j] = phase + 2 * PI * (k + q / 4.0 + jj) / N
            W[j] = w
            RF[j] = rf * (slen[k] if q == 2 else ((1 + slen[k]) / 2 if q in (1, 3) else 1.0))
            BR[j] = sbri[k] if q else 0.0
    cs = np.stack([np.cos(ang), np.sin(ang), np.zeros(M)], axis=1)
    ctr = np.array((center[0], center[1], 0.0))
    top_h = (apex - (z0 - D)) if apex is not None else None

    def star(t):
        return G.smoothstep(0.3, 1.0, t)

    def radius(t):
        return rt + (R - rt) * t * (1 + (RF - 1) * star(t))

    def zprof(t, w):
        if apex is None:
            z = z0 - D * (0.25 * t + 0.75 * t ** 2.1)
        else:
            z = apex - top_h * (0.5 * t + 0.5 * t ** 1.7)
        return z + 0.07 * R * star(t) * (w - 0.45) - 0.16 * R * w * t ** 3.5

    ts = [0.0, 0.5, 0.8, 1.0]
    V = []; Wt = []; Tt = []; Bt = []; offs = []; n0 = 0
    for j, t in enumerate(ts):
        if apex is not None and j == 0:
            V.append(np.array([[ctr[0], ctr[1], apex]])); Wt.append([0.5]); Tt.append([0.0]); Bt.append([0.0])
            offs.append(None); n0 += 1
            continue
        V.append(ctr + cs * radius(t)[:, None] + np.outer(zprof(t, W), UP))
        Wt.append(W); Tt.append(np.full(M, t)); Bt.append(BR)
        offs.append(n0); n0 += M
    V = np.concatenate(V); Wt = np.concatenate(Wt); Tt = np.concatenate(Tt); Bt = np.concatenate(Bt)
    F = []
    for j in range(len(ts) - 1):
        o1 = offs[j + 1]
        if offs[j] is None:
            F += [(0, o1 + k, o1 + (k + 1) % M) for k in range(M)]
        else:
            o0 = offs[j]
            F += [(o0 + k, o0 + (k + 1) % M, o1 + (k + 1) % M, o1 + k) for k in range(M)]
    top = G.Piece(V, F)
    top = G.orient(top, lambda c, i: UP)
    radial = flat_radial(top.V, ctr)
    top.N = G.unit(0.35 * top.N + 0.42 * radial + 0.45 * UP)
    sw = star(Tt)
    s = 0.22 + 0.46 * Tt ** 0.9 + 0.20 * (Wt - 0.5) * sw + 0.14 * fr + Bt + 0.08 * (Tt > 0.99) * (Wt > 0.99)
    top.color(ramp(s)); top.part(1)
    top.U = AT.region_uv('needle', Wt * sw + 0.5 * (1 - sw), Tt)
    # underside: a dark cone from the rim up to the axis
    rim = ctr + cs * radius(1.0)[:, None] + np.outer(zprof(1.0, W), UP)
    rim_z = zprof(1.0, W).mean()
    pole_z = (z0 - 0.62 * D) if apex is None else rim_z + 0.35 * (apex - rim_z)
    V = np.vstack([rim, [[ctr[0], ctr[1], pole_z]]])
    F = [(k, M, (k + 1) % M) for k in range(M)]
    und = G.Piece(V, F)
    und = G.orient(und, lambda c, i: -UP)
    radial = flat_radial(und.V, ctr)
    und.N = G.unit(0.55 * und.N + 0.45 * radial)
    tu = np.concatenate([np.ones(M), [0.0]])
    und.color(ramp(0.06 + 0.10 * tu + 0.05 * fr)); und.part(1)
    und.U = AT.region_uv('needle', np.concatenate([W, [0.5]]), tu)
    return [top, und]


def conifer(seed, H, Rmax, trunk_r, spacing, z_rim0, k=0.72, d=0.95, rmin=0.21, lean=0.0, top_wide=1.3):
    """Tiers follow a cone from the lowest rim to the apex; each tier sits k x its radius above the
    last (smaller tiers closer together) and droops d x its radius, so every rim hangs over the
    tier below and no trunk shows between them. The last tier is the pointed top."""
    rng = RNG(seed)
    slope = (H - z_rim0) / Rmax
    tiers = []
    z = z_rim0
    while True:
        R = (H - z) / slope
        if R <= Rmax * rmin:
            break
        tiers.append((z, R))
        z += k * R
    n = len(tiers) + 1
    pieces = []
    last_attach = 0.0
    for i, (zr, R) in enumerate(tiers):
        R *= rng.uniform(0.97, 1.04)
        D = d * R
        z0 = zr + D
        N = max(5, int(round(2 * PI * R / spacing)))
        rt = trunk_r * max(0.2, 1 - z0 / H)
        c = (lean * z0 / H + rng.normal(0, 0.025 * Rmax), rng.normal(0, 0.02 * Rmax))
        pieces += conifer_tier(z0, R, D, N, rng, rt, i / (n - 1), R_CONIFER, center=c)
        last_attach = z0
    # the pointed top: a little star-skirted spire
    R = (H - z) / slope * top_wide
    D = min(0.9 * R, (H - z) * 0.4)
    pieces += conifer_tier(z + D, R, D, 5, rng, 0.0, 1.0, R_CONIFER, apex=H, center=(lean, 0))
    tpath = G.catmull([(0, 0, -0.12), (0.0, 0.0, z_rim0), (lean * last_attach / H, 0, last_attach)], 7)
    radii = trunk_r * (1 - 0.8 * np.linspace(0, 1, len(tpath)) * last_attach / H)
    trunk = G.tube(tpath, radii, 8, lobe=flare(tpath, 0.55, 0.55, 5, rng.uniform(0, 6)), uv=uvr('bark', 8.0))
    wood_color(trunk, WOOD_CONIFER, ground=0.6, shade_z=z_rim0 + 0.2, shade=0.45)
    pieces.append(trunk)
    return pieces


def build_conifer_tall():
    tr = 0.29
    return conifer(3, 10.0, 2.1, tr, 1.2, 1.75), \
        {0: G.hexc(WOOD_CONIFER), 1: R_CONIFER.base}, {'kind': 'tree', 'trunkRadius': tr}


def build_conifer_mid():
    tr = 0.22
    return conifer(8, 6.0, 1.7, tr, 1.0, 1.15, k=0.74), \
        {0: G.hexc(WOOD_CONIFER), 1: R_CONIFER.base}, {'kind': 'tree', 'trunkRadius': tr}


def build_conifer_small():
    tr = 0.15
    return conifer(14, 3.5, 1.15, tr, 0.8, 0.78, k=0.78, rmin=0.3), \
        {0: G.hexc(WOOD_CONIFER), 1: R_CONIFER.base}, {'kind': 'tree', 'trunkRadius': tr}


# ---------------------------------------------------------------- palms
def frond(base, az, elev, L, Wmax, rng, droop=0.35, rows=15, teeth=True, fold=0.55, ramp=R_PALM, age=0.0):
    d = np.array((math.cos(az), math.sin(az), 0.0))
    ce, se = math.cos(elev), math.sin(elev)
    p0 = np.asarray(base, float)
    p1 = p0 + (d * ce + UP * se) * L * 0.5
    p2 = p0 + d * L * (0.62 + 0.3 * ce) + UP * L * (0.45 * se - droop)
    path = G.bezier(p0, p1, p2, rows + 1)
    T = G.tangents(path)
    S = G.unit(np.cross(T, UP))
    Nup = G.unit(np.cross(S, T))
    t = np.linspace(0, 1, rows + 1)
    w = Wmax * np.clip(np.sin(PI * np.clip(t, 0, 1) ** 0.8), 0, 1) ** 0.9 * G.smoothstep(0.0, 0.16, t)
    seg = G.arclen(path)[-1] / rows
    V = []; Uu = []; Vv = []; side = []
    th = 0.018
    for i in range(rows):
        wi = w[i]; fw = 1.0; fwd = 0.0
        if teeth and 2 <= i < rows - 1:
            if i % 2 == 0: fw = 1.0; fwd = 0.55 * seg
            else: fw = 0.62
        P = path[i]
        L_ = P - S[i] * wi * fw - Nup[i] * fold * wi * fw + T[i] * fwd
        R_ = P + S[i] * wi * fw - Nup[i] * fold * wi * fw + T[i] * fwd
        Mt = P + Nup[i] * th; Mb = P - Nup[i] * th
        V += [L_, Mt, R_, L_.copy(), Mb, R_.copy()]
        Uu += [0.0, 0.5, 1.0, 0.0, 0.5, 1.0]; Vv += [t[i]] * 6; side += [1, 1, 1, -1, -1, -1]
    tipi = len(V)
    V += [path[-1], path[-1].copy()]; Uu += [0.5, 0.5]; Vv += [1.0, 1.0]; side += [1, -1]
    F = []
    for i in range(rows - 1):
        a = i * 6; b = (i + 1) * 6
        F += [(a + 0, b + 0, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2)]          # top
        F += [(a + 3, a + 4, b + 4, b + 3), (a + 4, a + 5, b + 5, b + 4)]          # bottom
    a = (rows - 1) * 6
    F += [(a + 0, tipi, a + 1), (a + 1, tipi, a + 2), (a + 3, a + 4, tipi + 1), (a + 4, a + 5, tipi + 1)]
    p = G.Piece(V, F)
    side = np.array(side, float)
    p = G.orient(p, lambda c, i: (Nup[min(int(np.argmin(np.linalg.norm(path - c, axis=1))), rows)]) * (1 if side[p.F[i][0]] > 0 else -1))
    p.N = G.vnormals(p.V, p.F)
    tt = np.array(Vv); uu = np.array(Uu)
    mid = 1 - np.abs(uu - 0.5) * 2
    s_top = 0.36 + 0.30 * G.smoothstep(0.0, 0.5, tt) + 0.20 * mid + 0.1 * G.smoothstep(0.7, 1.0, tt) - 0.15 * age
    s = np.where(side > 0, s_top, 0.12 + 0.12 * tt)
    p.color(ramp(s + rng.uniform(-0.04, 0.04))); p.part(1)
    p.U = AT.region_uv('frond', uu, tt)
    return p


def palm(seed, trunk_pts, r_base, r_top, ring_len, n_fronds, frond_len, frond_w, n_nuts, elev=(0.15, 0.85), droop=0.4,
         n_dead=1):
    rng = RNG(seed)
    dense = G.catmull(trunk_pts, 60)
    Ld = G.arclen(dense)
    total = Ld[-1]
    n_rings = max(3, int(total / ring_len))
    ring_len = total / n_rings
    rows_s = []; rows_r = []; vrow = []
    taper = lambda s: r_base + (r_top - r_base) * (s / total) ** 0.7
    # a swollen base, then stacked rings each widest at its top lip
    rows_s += [0.0, 0.18]; rows_r += [r_base * 1.45, r_base * 1.12]; vrow += [0.0, 0.5]
    for k in range(n_rings):
        s0 = max(k * ring_len, 0.3); s1 = (k + 1) * ring_len - 0.16 * ring_len
        if s1 <= s0 + 0.05: continue
        rows_s += [s0, s1]; rows_r += [taper(s0) * 0.9, taper(s1) * 1.05]; vrow += [0.0, 1.0]
    rows_s.append(total); rows_r.append(taper(total) * 0.95); vrow.append(0.2)
    path = np.array([[np.interp(s, Ld, dense[:, j]) for j in range(3)] for s in rows_s])
    vr = list(vrow)
    u0, v0, u1, v1 = AT.REG['palm']; m = AT.MARGIN
    trunk = G.tube(path, np.array(rows_r), 8, lobe=lambda i, ang: 1 + 0.035 * np.cos(2 * ang + i * 1.3),
                   uv=(u0 + m, v0 + m, u1 - m, v1 - m, lambda s, i: vr[i]))
    z = trunk.V[:, 2]
    lip = np.array([vr[int(r)] for r in trunk.A['ring']])
    k = (0.70 + 0.30 * lip) * (1 - 0.35 * G.smoothstep(0.5, 0.0, z))
    trunk.color(G.hexc(WOOD_PALM)[None, :] * k[:, None]); trunk.part(0)
    sink_base(trunk, -0.2)
    pieces = [trunk]
    top = path[-1]; tdir = G.unit(path[-1] - path[-2])
    # crown shaft: a fibrous knob where the fronds spring from
    knob = G.blob(top + tdir * 0.05, (r_top * 1.5, r_top * 1.5, r_top * 1.25), 2, rng, bumps=6, amp=0.18, flat=0.9)
    knob.color(G.hexc('#7d6a3e') * (0.8 + 0.25 * G.smoothstep(-1, 1, knob.A['lz']))[:, None]); knob.part(0)
    pieces.append(knob)
    ga = PI * (3 - 5 ** 0.5); ph = rng.uniform(0, 2 * PI)
    for k in range(n_fronds):
        az = ph + ga * k * 1.0 + rng.normal(0, 0.12)
        f = k / max(n_fronds - 1, 1)
        el = elev[1] - (elev[1] - elev[0]) * f + rng.normal(0, 0.06)     # first fronds up, later ones droop
        ln = frond_len * rng.uniform(0.88, 1.06) * (0.85 + 0.2 * (1 - abs(el - 0.45)))
        base = top + tdir * 0.12 + np.array((math.cos(az), math.sin(az), 0)) * r_top * 0.9
        pieces.append(frond(base, az, el, ln, frond_w * rng.uniform(0.9, 1.08), rng,
                            droop=droop * (1.15 - 0.5 * el), age=0.6 * f * (f > 0.75)))
    # an old, dry frond or two hanging under the crown
    for k in range(n_dead):
        az = ph + PI * (0.35 + 0.8 * k) + rng.normal(0, 0.1)
        base = top - tdir * 0.05 + np.array((math.cos(az), math.sin(az), 0)) * r_top * 0.9
        f = frond(base, az, -1.0 - 0.15 * k, frond_len * 0.62, frond_w * 0.75, rng, droop=0.15, ramp=R_DRY, fold=0.7)
        f.part(0)
        pieces.append(f)
    # coconuts tucked under the crown
    for k in range(n_nuts):
        a = ph + 2 * PI * k / n_nuts + rng.normal(0, 0.2)
        c = top - tdir * (0.12 + 0.08 * (k % 2)) + np.array((math.cos(a), math.sin(a), 0)) * (r_top + 0.1)
        nut = G.blob(c, (0.14, 0.14, 0.16), 2, rng, bumps=3, amp=0.06, flat=0.9)
        nut.color(G.hexc('#7a6a30') * (0.7 + 0.35 * G.smoothstep(-1, 1, nut.A['lz']))[:, None]); nut.part(0)
        pieces.append(nut)
    return pieces


def build_palm():
    pieces = palm(91, [(0, 0, -0.12), (0.35, 0.0, 2.0), (1.05, 0.05, 4.0), (1.45, 0.1, 5.6), (1.5, 0.12, 6.3)],
                  0.24, 0.17, 0.42, 11, 3.5, 0.44, 4)
    return pieces, {0: G.hexc(WOOD_PALM), 1: R_PALM.base}, {'kind': 'tree', 'trunkRadius': 0.24}


def build_palm_short():
    pieces = palm(57, [(0, 0, -0.12), (0.45, -0.05, 1.2), (1.15, -0.05, 2.4), (1.4, 0.0, 3.4), (1.38, 0.0, 3.8)],
                  0.3, 0.2, 0.36, 10, 2.8, 0.42, 3, elev=(0.05, 0.9), droop=0.5, n_dead=2)
    return pieces, {0: G.hexc(WOOD_PALM), 1: R_PALM.base}, {'kind': 'tree', 'trunkRadius': 0.3}


# ---------------------------------------------------------------- bushes
def bush(seed, spec, ramp, C0, Rc, shade_bias=0.0, small=0.26):
    """A low clump mass sitting on the ground (no visible stems)."""
    rng = RNG(seed)
    clumps = make_clumps(spec, rng, freq_front=3, freq_back=2, small=small)
    pieces = crown(clumps, ramp, 1, rng, C0, Rc, core=0.55, shade_bias=shade_bias, amp=0.15, size=0.8)
    return pieces, clumps


def build_bush_round():
    spec = [((0, 0.02, 0.6), (0.6, 0.55, 0.52)), ((-0.42, -0.08, 0.42), 0.38), ((0.44, -0.04, 0.45), 0.4),
            ((0.05, -0.38, 0.42), 0.38), ((-0.1, 0.4, 0.45), 0.36), ((0.2, -0.12, 0.92), 0.36),
            ((-0.25, 0.05, 0.86), 0.34)]
    pieces, _ = bush(4, spec, R_BUSH, (0, 0, 0.6), (0.7, 0.62, 0.6))
    return ground(pieces, 1.2), {1: R_BUSH.base}, {'kind': 'bush'}


def build_bush_wide():
    spec = [((-0.55, 0.0, 0.48), (0.55, 0.48, 0.45)), ((0.5, 0.02, 0.5), (0.55, 0.48, 0.46)),
            ((0.0, 0.05, 0.62), (0.5, 0.45, 0.38)), ((-0.85, -0.12, 0.35), 0.32), ((0.88, -0.1, 0.33), 0.3),
            ((-0.25, -0.3, 0.38), 0.33), ((0.28, -0.32, 0.4), 0.32), ((0.15, 0.2, 0.82), 0.25),
            ((-0.35, 0.05, 0.78), 0.26)]
    pieces, _ = bush(9, spec, R_BUSH, (0, 0, 0.5), (1.1, 0.55, 0.5), shade_bias=0.02, small=0.36)
    return ground(pieces, 1.0), {1: R_BUSH.base}, {'kind': 'bush'}


def flower_dot(c, n, r, rng, k=6):
    """A small domed flower dot sitting on a surface, facing n (k rim points round a raised centre)."""
    n = G.unit(n)
    M = G.frame_to(c, n, x_hint=rng.normal(size=3))
    pts = [np.array((0, 0, r * 0.6))]
    for j in range(k):
        a = 2 * PI * j / k
        pts.append(np.array((math.cos(a) * r, math.sin(a) * r, 0.05 * r)))
    V = np.array(pts) @ M[:3, :3].T + M[:3, 3]
    F = [(0, 1 + j, 1 + (j + 1) % k) for j in range(k)]
    p = G.Piece(V, F)
    p = G.orient(p, lambda cc, i: n)
    p.N = G.unit(np.tile(n, (len(V), 1)) * 0.55 + G.unit(V - (c - n * r)) * 0.45)
    return p


def scatter_dots(leaf, rng, sites, per_site, size, spacing, color, zmin=0.25, part=2, spread=0.08):
    """Clusters of flower dots on the sunny side the game camera sees (front, from above).
    leaf: foliage pieces to sit on; color(height, rng) -> (rim RGB, centre RGB)."""
    V = np.concatenate([p.V for p in leaf]); N = np.concatenate([p.N for p in leaf])
    view = G.unit(np.array((0.15, -0.75, 0.65)))
    score = N @ view + rng.uniform(0, 0.4, len(V))
    chosen = []
    for i in np.argsort(-score):
        if len(chosen) >= sites or score[i] < 0.2: break
        if V[i][2] < zmin: continue
        if any(np.linalg.norm(V[i] - q) < spacing for q, _ in chosen): continue
        chosen.append((V[i], N[i]))
    out = []
    zlo, zhi = V[:, 2].min(), V[:, 2].max()
    for (c, n) in chosen:
        t1 = G.unit(np.cross(n, rng.normal(size=3))); t2 = np.cross(n, t1)
        for j in range(int(rng.integers(per_site[0], per_site[1] + 1))):
            a = rng.uniform(0, 2 * PI); rr = 0.0 if j == 0 else rng.uniform(spread * 0.6, spread)
            q = c + (t1 * math.cos(a) + t2 * math.sin(a)) * rr + n * 0.012
            f = flower_dot(q, G.unit(n + rng.normal(0, 0.15, 3)), rng.uniform(*size), rng)
            rim, ctr = color((q[2] - zlo) / max(zhi - zlo, 1e-3), rng)
            col = np.tile(rim, (len(f), 1)); col[0] = ctr
            f.color(col); f.part(part)
            out.append(f)
    return out


def build_shrub_flowering():
    rng = RNG(12)
    spec = [((0, 0.0, 0.58), (0.55, 0.5, 0.52)), ((-0.38, -0.1, 0.42), 0.36), ((0.4, -0.06, 0.44), 0.37),
            ((0.02, -0.33, 0.4), 0.34), ((0.0, 0.36, 0.45), 0.34), ((0.16, -0.1, 0.86), 0.32),
            ((-0.2, 0.08, 0.82), 0.3)]
    pieces, clumps = bush(15, spec, R_SHRUB, (0, 0, 0.58), (0.65, 0.58, 0.55), small=0.35)

    def col(h, rng):
        sh = 0.45 + 0.35 * h + rng.uniform(-0.1, 0.1)
        return R_SHRUB_FL(sh), R_SHRUB_FL(min(sh + 0.35, 1.0))
    pieces += scatter_dots([p for p in pieces if p.P[0] == 1], rng, 12, (3, 4), (0.038, 0.05), 0.26, col)
    return ground(pieces, 1.1), {1: R_SHRUB.base, 2: R_SHRUB_FL.base}, {'kind': 'bush'}


# ---------------------------------------------------------------- hedges
HEDGE_PERIOD = 1.0      # the lumps repeat every metre, so any block joins any other


def hedge_profile():
    """The clipped section (y, z), from the front foot over the top to the back foot."""
    pts = [(-0.38, -0.05), (-0.386, 0.22), (-0.382, 0.48), (-0.374, 0.68), (-0.356, 0.795), (-0.318, 0.88),
           (-0.25, 0.932), (-0.13, 0.955), (0.0, 0.96)]
    back = [(-y, z) for (y, z) in reversed(pts[:-1])]
    P = np.array(pts + back)
    P[:, 0] *= 1.035
    return P


def hedge_lumps(x, s):
    """Periodic lump field (period HEDGE_PERIOD along x); s is the position around the section (0..1)."""
    X = 2 * PI * x / HEDGE_PERIOD
    return (0.65 * np.sin(2 * X + 5.1 * s + 0.4) + 0.35 * np.sin(2 * X - 7.3 * s + 1.9)
            + 0.3 * np.sin(1 * X + 3.0 * s + 2.3)) / 1.3


def build_hedge(length):
    prof = hedge_profile()
    seg = np.linalg.norm(np.diff(prof, axis=0), axis=1)
    sl = np.concatenate([[0], np.cumsum(seg)]); S = sl / sl[-1]
    pn = np.zeros_like(prof)                          # outward 2D normals of the section
    tang = np.gradient(prof, axis=0)
    pn[:, 0] = -tang[:, 1]; pn[:, 1] = tang[:, 0]
    pn = pn / np.linalg.norm(pn, axis=1, keepdims=True)
    pn[0] = (-1, 0); pn[-1] = (1, 0)
    dx = 0.125
    nx = int(round(length / dx))
    xs = np.linspace(-length / 2, length / 2, nx + 1)
    xs_ext = np.concatenate([[xs[0] - dx], xs, [xs[-1] + dx]])
    zf = prof[:, 1]
    amp = 0.026 + 0.04 * G.smoothstep(0.6, 0.95, zf)
    amp[0] = amp[-1] = 0.0
    P = len(prof)

    def section(xl):
        d = (0.45 + 0.55 * hedge_lumps(xl, S)) * amp            # leafy bulges, outward
        return prof[:, 0] + pn[:, 0] * d, prof[:, 1] + pn[:, 1] * d
    # fit the lumpy section to 0.8 m deep and 1.0 m high, measured over one lump period, so
    # every block length gets the same scale and the ends still match
    ref = [section(xl) for xl in np.arange(0, HEDGE_PERIOD, dx)]
    ky = 0.4 / max(np.abs(y).max() for y, z in ref)
    kz = 1.0 / max(z.max() for y, z in ref)
    V = []
    for x in xs_ext:
        y, z = section(x + length / 2)
        V.append(np.stack([np.full(P, x), y * ky, z * kz], axis=1))
    V = np.concatenate(V)
    F = []
    for i in range(len(xs_ext) - 1):
        for k in range(P - 1):
            a = i * P + k
            F.append((a, a + 1, a + 1 + P, a + P))
    full = G.Piece(V, F)
    full = G.orient(full, lambda c, i: np.array((0, c[1], c[2] - 0.45)))
    full.N = G.vnormals(full.V, full.F)
    N = full.N.reshape(len(xs_ext), P, 3)[1:-1].reshape(-1, 3)
    V = V.reshape(len(xs_ext), P, 3)[1:-1]
    # duplicate the columns at whole metres so the leaf texture can restart (it tiles every metre)
    cols = []; ucol = []
    for i, x in enumerate(xs):
        xl = x + length / 2
        frac = xl / HEDGE_PERIOD
        if 0 < i < nx and abs(frac - round(frac)) < 1e-6:
            cols.append(i); ucol.append(1.0)
            cols.append(i); ucol.append(0.0)
        else:
            cols.append(i); ucol.append((frac - math.floor(frac)) if i < nx else (1.0 if frac > 0 else 0.0))
    Vs = np.concatenate([V[i] for i in cols]); Ns = np.concatenate([N.reshape(nx + 1, P, 3)[i] for i in cols])
    Us = np.concatenate([np.full(P, u) for u in ucol])
    Ss = np.tile(S, len(cols))
    F = []
    for j in range(len(cols) - 1):
        if cols[j] == cols[j + 1]: continue
        for k in range(P - 1):
            a = j * P + k
            F.append((a, a + 1, a + 1 + P, a + P))
    side = G.Piece(Vs, F, N=Ns)
    side = G.orient(side, lambda c, i: np.array((0, c[1], c[2] - 0.45)))
    side.N = Ns
    # shading: lit top, dark foot; lump crowns lighter, hollows darker (periodic, so blocks match)
    xl = Vs[:, 0] + length / 2
    lump = hedge_lumps(xl, Ss)
    z = Vs[:, 2]
    s = 0.2 + 0.5 * G.smoothstep(-0.05, 0.95, z) ** 0.9 + 0.2 * G.smoothstep(0.78, 0.98, z) + 0.1 * lump
    side.color(R_HEDGE(s)); side.part(1)
    side.U = AT.region_uv('hedge', Us, Ss)
    pieces = [side]
    # end caps (hidden where blocks meet, closing the run's ends)
    for sgn in (-1, 1):
        ring = V[0] if sgn < 0 else V[-1]
        ctr = np.array((sgn * length / 2, 0.0, 0.5))
        cv = np.vstack([ring, ctr])
        F = [(k, k + 1, P) for k in range(P - 1)] + [(P - 1, 0, P)]
        cap = G.Piece(cv, F)
        cap = G.orient(cap, lambda c, i: np.array((sgn, 0, 0)))
        cap.N = np.tile(np.array((sgn * 0.8, 0, 0.6)), (len(cv), 1))
        cap.color(R_HEDGE(0.1 + 0.45 * G.smoothstep(0.0, 1.0, cv[:, 2]))); cap.part(1)
        cap.U = AT.region_uv('hedge', (cv[:, 1] + 0.4) / 0.8 * 0.7 + 0.15, cv[:, 2] * 0.3 + 0.3)
        pieces.append(cap)
    return pieces, {1: R_HEDGE.base}, {'kind': 'hedge', 'tileLength': length, 'tileAxis': 'x'}


# ---------------------------------------------------------------- grasses and flowers
def blade(base, az, L, wd, lean, curl, segs=4, wind=(0, 0, 0), thick=0.28, twist=0.0):
    """A solid tapered blade (triangular section, the flat face outward) from base, curving out
    along azimuth az. Tag 't': 0 at the base -> 1 at the tip."""
    base = np.asarray(base, float); wind = np.asarray(wind, float)
    out = np.array((math.cos(az), math.sin(az), 0.0))
    side0 = np.array((-math.sin(az), math.cos(az), 0.0))
    p1 = base + UP * L * 0.55 + out * L * lean * 0.35 + wind * L * 0.2
    p2 = base + UP * L * (0.97 - 0.5 * curl) + out * L * (lean * 0.8 + curl * 0.55) + wind * L * 0.75
    path = G.bezier(base, p1, p2, segs + 1)
    T = G.tangents(path)
    V = []; tt = []
    for i in range(segs):
        t = i / segs
        w = wd * (1 - t) ** 0.85 * (0.75 + 0.25 * G.smoothstep(0, 0.25, t))
        a = twist * t
        side = side0 * math.cos(a) + np.cross(T[i], side0) * math.sin(a)
        side = G.unit(side - T[i] * np.dot(side, T[i]))
        nf = G.unit(np.cross(side, T[i]))
        P = path[i]
        V += [P - side * w / 2, P + side * w / 2, P - nf * w * thick]
        tt += [t] * 3
    tip = len(V); V.append(path[-1]); tt.append(1.0)
    F = []
    for i in range(segs - 1):
        a = i * 3; b = a + 3
        F += [(a, a + 1, b + 1, b), (a + 1, a + 2, b + 2, b + 1), (a + 2, a, b, b + 2)]
    a = (segs - 1) * 3
    F += [(a, a + 1, tip), (a + 1, a + 2, tip), (a + 2, a, tip)]
    p = G.Piece(V, F)
    soft = G.unit(UP * 0.9 + out * 0.5 + wind * 0.3)
    p.N = G.unit(0.4 * p.N + 0.6 * soft)
    p.tag('t', tt)
    return p


def grass_color(p, ramp, rng, lo=0.12, hi=0.95, bias=0.0):
    t = p.A['t']
    s = lo + (hi - lo) * t ** 0.8 + bias + rng.uniform(-0.07, 0.07)
    p.color(ramp(s)); p.part(1)
    p.C[:, 3] = t ** 1.3
    return p


def tuft(seed, n, L, wd, ramp, spread=0.09, lean=(0.25, 0.7), curl=(0.05, 0.5), wind=(0, 0, 0), segs=4,
         lrange=(0.55, 1.0), bias=0.0, thick=0.28):
    rng = RNG(seed)
    pieces = []
    ga = PI * (3 - 5 ** 0.5)
    for k in range(n):
        a = k * ga + rng.normal(0, 0.15)
        r = spread * math.sqrt((k + 0.5) / n)
        base = np.array((math.cos(a) * r, math.sin(a) * r * 0.85, -0.03))
        inner = 1 - r / max(spread, 1e-3)
        ln = L * rng.uniform(*lrange) * (0.8 + 0.3 * inner)
        b = blade(base, a + rng.normal(0, 0.25), ln, wd * rng.uniform(0.8, 1.15), rng.uniform(*lean) * (1.2 - 0.6 * inner),
                  rng.uniform(*curl), segs=segs, wind=wind, thick=thick, twist=rng.normal(0, 0.4))
        pieces.append(grass_color(b, ramp, rng, bias=bias))
    return pieces, rng


def build_grass_tuft():
    pieces, _ = tuft(2, 28, 0.56, 0.05, R_GOLD, spread=0.08)
    return pieces, {1: R_GOLD.base}, {'kind': 'grass'}


def build_tall_grass():
    wind = np.array((0.55, 0.0, 0.0))                 # swept toward +X
    pieces, rng = tuft(6, 19, 0.82, 0.05, R_GOLD_T, spread=0.12, lean=(0.1, 0.45), curl=(0.2, 0.6), wind=wind,
                       segs=5, lrange=(0.6, 1.0))
    for k in range(4):
        a = rng.uniform(0, 2 * PI)
        base = np.array((math.cos(a) * 0.05, math.sin(a) * 0.05, -0.03))
        L = rng.uniform(0.7, 0.88)
        top = base + UP * L * 0.92 + wind * L * 0.55 + np.array((math.cos(a), math.sin(a), 0)) * 0.08
        mid = base + UP * L * 0.55 + wind * L * 0.12
        stem = G.tube(G.bezier(base, mid, top, 4), np.linspace(0.009, 0.006, 4), 3, seam=False)
        stem.tag('t', G.smoothstep(base[2], top[2], stem.V[:, 2]))
        grass_color(stem, R_GOLD_T, rng, lo=0.2, hi=0.8)
        d = G.unit(top - mid)
        hp = G.bezier(top, top + d * 0.09, top + d * 0.2, 5)
        head = G.tube(hp, [0.01, 0.026, 0.028, 0.018, 0.0], 5, tip=True, seam=False)
        head.N = G.unit(0.5 * head.N + 0.5 * G.unit(head.V - hp[2] + UP * 0.05))
        head.tag('t', np.ones(len(head)))
        grass_color(head, R_GOLD_T, rng, lo=0.8, hi=0.8, bias=0.1)
        pieces += [stem, head]
    return pieces, {1: R_GOLD_T.base}, {'kind': 'grass', 'windLean': [1, 0, 0]}


def build_dune_grass():
    pieces, _ = tuft(17, 27, 0.92, 0.034, R_DUNE, spread=0.12, lean=(0.2, 0.6), curl=(0.12, 0.6), segs=5,
                     lrange=(0.55, 1.0), thick=0.35)
    return pieces, {1: R_DUNE.base}, {'kind': 'grass'}


def build_reeds():
    pieces, rng = tuft(23, 16, 1.0, 0.045, R_REED, spread=0.12, lean=(0.05, 0.3), curl=(0.0, 0.35), segs=5,
                       lrange=(0.65, 1.0))
    for k in range(4):
        a = 2 * PI * k / 4 + rng.normal(0, 0.3)
        base = np.array((math.cos(a) * 0.06, math.sin(a) * 0.06, -0.03))
        H = rng.uniform(0.82, 0.98)
        lean = np.array((math.cos(a), math.sin(a), 0)) * rng.uniform(0.03, 0.12)
        path = G.bezier(base, base + UP * H * 0.5, base + UP * H + lean, 5)
        stem = G.tube(path, np.linspace(0.011, 0.007, 5), 3, seam=False)
        stem.tag('t', G.smoothstep(0, H, stem.V[:, 2]))
        grass_color(stem, R_REED, rng, lo=0.25, hi=0.7)
        d = G.unit(path[-1] - path[-2])
        h0 = path[-1] - d * 0.28
        hpath = np.array([h0 + d * f for f in (0.0, 0.03, 0.1, 0.17, 0.22, 0.25)])
        head = G.tube(hpath, [0.012, 0.03, 0.036, 0.036, 0.03, 0.0], 6, tip=True, seam=False)
        hz = G.smoothstep(-1, 1, (head.V - hpath.mean(0)) @ np.array((0.3, -0.3, 0.9)) / 0.04)
        head.color(G.hexc('#6e4630')[None, :] * (0.7 + 0.45 * hz)[:, None]); head.part(0)
        spike = G.tube(np.array([path[-1], path[-1] + d * 0.12]), [0.006, 0.0], 3, tip=True, seam=False)
        spike.color(G.hexc('#8a7a52')); spike.part(0)
        pieces += [stem, head, spike]
    return pieces, {1: R_REED.base, 0: G.hexc('#6e4630')}, {'kind': 'grass'}


FLOWERS = [('#f7f2e8', '#f1c232'), ('#e4573f', '#3a2a2a'), ('#6f8de0', '#30386a'), ('#f4cd3f', '#e58f2a'),
           ('#f08db0', '#f6e08a'), ('#f7f2e8', '#f1c232'), ('#e4573f', '#3a2a2a'), ('#b58be0', '#f6e08a')]


def flower_head(c, n, r, petals, rng):
    """A double-sided flower: rounded petals (two tip points each) round a raised centre, cupped toward n."""
    n = G.unit(n)
    M = G.frame_to(c, n, x_hint=rng.normal(size=3))
    pitch = 2 * PI / petals
    rim = []
    for k in range(petals):
        a = k * pitch
        rim += [(a - 0.2 * pitch, r), (a + 0.2 * pitch, r), (a + 0.5 * pitch, r * 0.4)]
    m = len(rim)
    top = [np.array((0, 0, r * 0.28))] + [np.array((math.cos(a) * rr, math.sin(a) * rr, 0.32 * rr)) for a, rr in rim]
    top = np.array(top)
    bot = top.copy(); bot[:, 2] -= r * 0.12; bot[0, 2] = -r * 0.3
    V = np.vstack([top, bot]) @ M[:3, :3].T + M[:3, 3]
    F = [(0, 1 + k, 1 + (k + 1) % m) for k in range(m)]
    o = m + 1
    F += [(o, o + 1 + (k + 1) % m, o + 1 + k) for k in range(m)]
    p = G.Piece(V, F)
    nn = np.array([n] * (m + 1) + [-n] * (m + 1))
    p.N = G.unit(nn * 0.6 + G.unit(V - c) * 0.4)
    return p


def build_flower_patch():
    rng = RNG(29)
    pieces = []
    # a low mound of leaves: broad, arching blades
    leaves, _ = tuft(41, 17, 0.24, 0.07, R_MEADOW, spread=0.15, lean=(0.35, 0.8), curl=(0.25, 0.6), segs=4,
                     lrange=(0.6, 1.0), thick=0.25)
    pieces += leaves
    ga = PI * (3 - 5 ** 0.5)
    cols = []
    for k in range(7):
        a = k * ga * 1.3 + 0.4
        r = 0.04 + 0.12 * math.sqrt((k + 0.5) / 7)
        base = np.array((math.cos(a) * r, math.sin(a) * r * 0.8, -0.02))
        H = rng.uniform(0.2, 0.31)
        top = base + UP * H + np.array((math.cos(a), math.sin(a), 0)) * rng.uniform(0.03, 0.07)
        stem = G.tube(G.bezier(base, base + UP * H * 0.5, top, 4), [0.008, 0.007, 0.006, 0.005], 3, seam=False)
        stem.tag('t', G.smoothstep(0, H, stem.V[:, 2]))
        grass_color(stem, R_MEADOW, rng, lo=0.25, hi=0.6)
        pet, cen = FLOWERS[k]
        rr = rng.uniform(0.05, 0.062)
        n = G.unit(np.array((math.cos(a) * 0.3, -0.55 + math.sin(a) * 0.2, 1.0)))
        head = flower_head(top + n * 0.005, n, rr, 5 if k % 3 else 6, rng)
        m = (len(head) // 2) - 1
        col = np.tile(G.hexc(pet), (len(head), 1))
        sh = np.concatenate([[1.0], np.tile([1.0, 1.0, 0.82], m // 3), [0.75], np.full(m, 0.68)])
        col = col * sh[:, None]
        col[0] = G.hexc(cen); col[m + 1] = G.hexc(cen) * 0.8
        head.color(col); head.P[:] = 2; head.P[0] = 0; head.P[m + 1] = 0
        cols.append(G.hexc(pet))
        pieces += [stem, head]
    base2 = np.mean(cols, axis=0)
    return pieces, {0: G.hexc(FLOWERS[0][1]), 1: R_MEADOW.base, 2: base2}, {'kind': 'grass', 'flowerColorsVary': True}


# ---------------------------------------------------------------- assembly
MODELS = [
    ('ConiferTall', build_conifer_tall), ('ConiferMid', build_conifer_mid), ('ConiferSmall', build_conifer_small),
    ('Broadleaf', build_broadleaf), ('BroadleafLarge', build_broadleaf_large), ('Birch', build_birch),
    ('CherryBlossom', build_cherry), ('Palm', build_palm), ('PalmShort', build_palm_short),
    ('BushRound', build_bush_round), ('BushWide', build_bush_wide), ('ShrubFlowering', build_shrub_flowering),
    ('HedgeBlock1', lambda: build_hedge(1.0)), ('HedgeBlock2', lambda: build_hedge(2.0)),
    ('GrassTuft', build_grass_tuft), ('TallGrass', build_tall_grass), ('DuneGrass', build_dune_grass),
    ('Reeds', build_reeds), ('FlowerPatch', build_flower_patch),
]
BUDGET = {'tree': 2500, 'bush': 800, 'grass': 800, 'hedge': 600}


def main():
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    atlas = os.path.join(OUT, 'PlantsAtlas.png')
    AT.paint_atlas(atlas)
    mat = K.material('Plants', atlas)
    man = K.Manifest('Plants', 'PlantsAtlas.png')
    man.data['notes'] = {
        'front': '-Y (Attach.Front at (0, -1, 0)); origin at the base on the ground',
        'parts': '0 fixed (wood, coconuts, dry palm fronds, flower centres, reed heads), 1 foliage, 2 flowers/blossom',
        'vertexAlpha': 'wind weight: 0 at the rooted base -> 1 at the top / blade tips',
        'hedgeTiling': 'HedgeBlock1/2 tile end to end along X (lumps repeat every 1 m)',
    }
    report = []
    for name, fn in MODELS:
        if ONLY and name not in ONLY: continue
        pieces, parts, extra = fn()
        p = G.merge(pieces)
        H = max(p.V[:, 2].max(), 0.1)
        if extra.get('kind') != 'grass':
            p.C[:, 3] = np.clip(p.V[:, 2] / H, 0, 1) ** 1.5
        o = G.to_object(name, p)
        K.assign(o, mat)
        front = K.attach(o, 'Front', (0, -1, 0))
        assert front.name == 'Attach.Front', front.name
        parts = {k: tuple(float(x) for x in v) for k, v in sorted(parts.items())}
        man.add(o, parts=parts, **extra)
        K.export_model(o, os.path.join(OUT, name + '.fbx'))
        # object names are unique per .blend: once exported, give this marker a model-specific
        # name so the next model's marker is exported as exactly 'Attach.Front' too
        front.name = 'Attach.Front.' + name
        t = K.tree_tris(o)
        lim = BUDGET[extra['kind']]
        report.append((name, t, lim, man.data['models'][name]['size']))
    man.save(os.path.join(OUT, 'Plants.json'))
    bpy.context.preferences.filepaths.save_version = 0          # no Plants.blend1 next to the kit
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Plants.blend'))
    for name, t, lim, size in report:
        print('PLANT %-15s %5d / %4d tris %s  size %s' % (name, t, lim, 'OK ' if t <= lim else 'OVER', size))


main()
