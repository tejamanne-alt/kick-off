# Leaf-card crowns for kit_plants.py: trees and bushes whose foliage is many small clumps of
# clover-like leaves (cut-out sprites in PlantsAtlas.png) rather than smooth blobs, in the look
# of a hand-painted anime background. Read docs/ART_DIRECTION.md.
#
# A crown is a few overlapping MASSES (ellipsoids). Each mass carries:
#   - an outer layer of leaf cards over its surface: bright, their clumps break the silhouette
#     into scallops and leave little sky holes near the edge;
#   - an inner layer of darker cards, the shade deep in the crown;
#   - a dark, lumpy CORE (solid, about half the mass) so the crown never reads as see-through
#     in its middle, while the rim stays lacy.
# A card is one quad (the game's material draws both sides) at a random yaw, nearly upright
# (the camera looks at the trees almost level), spun and mirrored in its plane. Trees stand at
# any yaw, so cards that end up nearly edge-on to the camera shrink away in the shader instead
# of showing as slivers (Toon.shader _EdgeFade); the card count allows for them. All four corners
# share one custom normal: the mass's outward direction blended with the crown's and a little
# random, so the toon shader lights each clump as a unit and the sun/shade edge runs between
# clumps. Vertex colours carry the depth (outer bright, inner dark, darker where masses meet
# and toward each lobe's underside); the atlas sprite adds the clover shapes and their own light
# and dark. Every vertex of a card gets the card centre's wind weight (tag 'windz'), so cards
# sway whole.
#
# Branches: the trunk forks into a few main limbs (one per group of masses round the crown),
# each splitting into sub-limbs to its masses, and thin twigs run out toward each mass's rim,
# all in dark bark; faces hidden inside the cores are dropped, so what is left shows through
# the gaps between the clumps.
import math
import numpy as np
import kit_plants_geo as G
import kit_plants_atlas as AT

UP = np.array((0.0, 0.0, 1.0))
PI = math.pi


class Mass:
    def __init__(self, c, r, bright=0.0, cards=1.0, under=1.0):
        self.c = np.asarray(c, float)
        self.r = np.asarray(r if np.ndim(r) else (r, r, r), float)
        self.bright = bright          # a nudge to this mass's leaf brightness
        self.cards = cards            # its card density factor
        self.under = under            # < 1 flattens its underside (a pruned pine's pads)

    def e(self, P, k=1.0):
        """Normalised ellipsoid radius of points P (1 on the surface of the mass scaled by k)."""
        q = (np.atleast_2d(P) - self.c) / (self.r * k)
        q[:, 2] = np.where(q[:, 2] < 0, q[:, 2] / self.under, q[:, 2])
        return np.linalg.norm(q, axis=1)

    def point(self, d, rr):
        """The point at direction d and normalised radius rr."""
        q = d * self.r * rr
        if q[2] < 0: q = q * np.array((1, 1, self.under))
        return self.c + q

    def area(self):
        a, b, c = self.r
        p = 1.6075
        return 4 * PI * (((a * b) ** p + (a * c) ** p + (b * c) ** p) / 3) ** (1 / p)


def masses_from(C0, Rc, n, rng, rf=(0.42, 0.52), shell=0.56, zlo=-0.5, top=0.42, flat_under=0.85, shell_jit=(0.8, 1.2)):
    """n masses spread over a crown envelope (C0, Rc) on a golden-angle spiral from the top down,
    plus a top mass (top > 0: its height as a fraction of Rc z)."""
    C0 = np.asarray(C0, float); Rc = np.asarray(Rc, float)
    out = []
    if top:
        out.append(Mass(C0 + np.array((rng.normal(0, 0.06), rng.normal(0, 0.06), top * Rc[2])),
                        Rc * np.array((0.52, 0.52, 0.47)) * rng.uniform(0.95, 1.05)))
    ga = PI * (3 - 5 ** 0.5); ph = rng.uniform(0, 2 * PI)
    for k in range(n):
        zf = 0.72 - (0.72 - zlo) * (k + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - zf * zf))
        a = ph + ga * k
        d = np.array((rr * math.cos(a), rr * math.sin(a), zf))
        pos = C0 + d * Rc * shell * rng.uniform(*shell_jit)
        rad = Rc.mean() * rng.uniform(*rf) * (1 - (1 - flat_under) * (zf < 0))
        out.append(Mass(pos, (rad, rad * 0.95, rad * 0.88), bright=rng.uniform(-0.05, 0.05)))
    return out


def fib_dirs(n, rng, jitter=0.35):
    """n roughly even unit directions (a jittered golden spiral)."""
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    a = PI * (3 - 5 ** 0.5) * i + rng.uniform(0, 2 * PI)
    rr = np.sqrt(np.clip(1 - z * z, 0, 1))
    D = np.stack([rr * np.cos(a), rr * np.sin(a), z], axis=1)
    D += rng.normal(0, jitter * math.sqrt(4 * PI / max(n, 1)) * 0.5, D.shape)
    return G.unit(D)


def _rand_unit(rng, n=None):
    return G.unit(rng.normal(size=(3,) if n is None else (n, 3)))


def leaf_cards(masses, rng, ramp, part=1, sprite='leaf', size=1.1, density=1.0, inner=0.3,
               C0=None, Rc=None, nmix=(0.7, 0.22, 0.15), tilt=0.25, open_under=0.4, size_jit=0.16,
               rho=(0.78, 1.02), rho_in=(0.42, 0.74), shade=0.0, zmin=None, light_k=1.0, crease=0.45,
               min_z=None):
    """The leaf cards of a crown (one Piece). ramp(s): s 0 deep shade .. 1 sunlit top.
    size: card side (m); density: cover factor; inner: inner-layer cards per outer card."""
    if C0 is None:
        C0 = np.mean([m.c for m in masses], axis=0)
    C0 = np.asarray(C0, float)
    if Rc is None:
        lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
        Rc = (hi - lo) / 2
    Rc = np.asarray(Rc, float)
    z0 = min(m.c[2] - m.r[2] for m in masses) if zmin is None else zmin
    z1 = max(m.c[2] + m.r[2] for m in masses)
    nsp = len(AT.SPRITES[sprite])
    V, N, C, U, F, WZ = [], [], [], [], [], []
    for mi, m in enumerate(masses):
        others = [o for j, o in enumerate(masses) if j != mi]
        # about 1.5 layers of clumps over what the camera sees of the mass, allowing for the cards
        # that face away edge-on (the shader thins those out)
        n_out = int(round(4.6 * density * m.cards * m.area() / (size * size)))
        layers = [(n_out, rho, 0), (int(round(n_out * inner)), rho_in, 1)]
        for count, (r0, r1), layer in layers:
            if count <= 0: continue
            D = fib_dirs(count, rng)
            for d in D:
                rr = rng.uniform(r0, r1)
                p = m.point(d, rr)
                if min_z is not None and p[2] < min_z: continue
                eo = min([o.e(p)[0] for o in others], default=9.0)
                if eo < (0.84 if layer == 0 else 0.62): continue          # buried in a neighbour
                if layer == 0 and d[2] < -0.45 and rng.random() < open_under * G.smoothstep(-0.45, -0.9, d[2]):
                    continue                                             # a ragged, open underside
                # the card: nearly upright, random yaw, spun and mirrored in its plane
                yaw = rng.uniform(0, 2 * PI)
                el = float(np.clip(rng.normal(0, tilt), -0.75, 0.75))
                g = np.array((math.cos(el) * math.cos(yaw), math.cos(el) * math.sin(yaw), math.sin(el)))
                right = G.unit(np.cross(UP, g)); up = np.cross(g, right)
                psi = rng.uniform(0, 2 * PI)
                Rv = math.cos(psi) * right + math.sin(psi) * up
                Uv = -math.sin(psi) * right + math.cos(psi) * up
                s = size * rng.uniform(1 - size_jit, 1 + size_jit) * (0.85 if layer else 1.0)
                h = s / 2
                corners = [p - Rv * h - Uv * h, p + Rv * h - Uv * h, p + Rv * h + Uv * h, p - Rv * h + Uv * h]
                uvs = np.array(((0, 0), (1, 0), (1, 1), (0, 1)), float)
                if rng.random() < 0.5: uvs[:, 0] = 1 - uvs[:, 0]
                k = int(rng.integers(0, nsp))
                # one lighting normal per card
                dm = G.unit((p - m.c) / m.r)
                dc = G.unit((p - C0) / Rc)
                n = G.unit(nmix[0] * dm + nmix[1] * dc + nmix[2] * _rand_unit(rng))
                # brightness: depth in the mass, height, creases where masses meet
                hz = (p[2] - z0) / max(z1 - z0, 1e-3)
                if layer == 0:      # the outer clumps: bright, a little brighter the further out
                    sv = 0.68 + 0.3 * light_k * G.smoothstep(r0, r1, rr)
                else:               # the shade deep in the crown
                    sv = 0.03 + 0.2 * G.smoothstep(r0, r1, rr)
                sv += (0.16 * dm[2] + 0.12 * (2 * hz - 1) + m.bright + shade
                       - crease * G.smoothstep(1.4, 0.85, eo) + rng.uniform(-0.07, 0.07))
                base = len(V)
                V += corners
                N += [n] * 4
                C += [ramp(float(sv))] * 4
                U += list(AT.sprite_uv(sprite, k, uvs[:, 0], uvs[:, 1]))
                WZ += [p[2]] * 4
                F.append((base, base + 1, base + 2, base + 3))
    pc = G.Piece(np.array(V), F, N=np.array(N))
    pc.C[:, :3] = np.array(C).reshape(-1, 3)
    pc.U = np.array(U)
    pc.part(part)
    pc.tag('windz', WZ)
    return pc


def cores(masses, rng, ramp, part=1, scale=0.6, C0=None, Rc=None, s=(0.03, 0.16), freq=2, amp=0.18):
    """A dark lumpy solid inside each mass (faces hidden in another core are dropped)."""
    if C0 is None:
        C0 = np.mean([m.c for m in masses], axis=0)
    C0 = np.asarray(C0, float)
    if Rc is None:
        lo = np.min([m.c - m.r for m in masses], axis=0); hi = np.max([m.c + m.r for m in masses], axis=0)
        Rc = (hi - lo) / 2
    out = []
    for mi, m in enumerate(masses):
        b = G.blob(m.c, m.r * scale, freq, rng, bumps=int(rng.integers(4, 7)), amp=amp, size=0.8, flat=min(0.9, m.under))
        inside = np.zeros(len(b), bool)
        for j, o in enumerate(masses):
            if j != mi:
                inside |= o.e(b.V, scale) < 0.97
        b = G.cull(b, inside)
        if not len(b): continue
        dm = G.unit((b.V - m.c) / m.r); dc = G.unit((b.V - C0) / Rc)
        b.N = G.unit(0.6 * dm + 0.4 * dc)
        b.color(ramp(s[0] + (s[1] - s[0]) * G.smoothstep(-1, 1, b.A['lz']))); b.part(part)
        out.append(b)
    return out


def hidden_in(p, masses, k):
    """Drop a piece's faces that lie wholly inside the masses' cores (scaled by k)."""
    inside = np.zeros(len(p), bool)
    for m in masses:
        inside |= m.e(p.V, k) < 0.95
    return G.cull(p, inside)


def limb(p0, p1, r0, r1, rng, sides=6, segs=5, rise=0.22, wobble=0.07, uv=None):
    """A branch from p0 to p1 that bows upward a little."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    d = p1 - p0; L = np.linalg.norm(d)
    mid = p0 + d * 0.5 + UP * L * rise * 0.5 + rng.normal(0, wobble, 3) * L * 0.3
    path = G.catmull([p0, mid, p1], segs + 1)
    return G.tube(path, np.linspace(r0, r1, len(path)), sides, uv=uv), path


def branches(masses, rng, trunk_path, trunk_r, fork_z, wood_fn, uv_fn, limb_r=(0.42, 0.55), twigs=3,
             twig_r=0.05, core_k=0.6, limb_end=0.3, twig_reach=(0.7, 0.86), sides=6, groups=3, fork_spread=0.9,
             axis_r=0.55):
    """The crown's wood: the trunk forks (from fork_z up) into a few main limbs, one per group of
    masses round the crown; each main limb splits into sub-limbs to its masses; twigs run from the
    sub-limbs out toward each mass's rim. Masses on the trunk's own line hang on the leader (the
    trunk path itself) and only get twigs. wood_fn(piece) colours a piece; uv_fn(offset) gives
    tube() uv specs."""
    pieces = []
    tp = np.asarray(trunk_path, float)

    def trunk_at(z):
        j = int(np.argmin(np.abs(tp[:, 2] - z)))
        return tp[j], 1 - j / max(len(tp) - 1, 1)

    def add(p0, p1, r0, r1, side=sides, segs=5, rise=0.22):
        b, path = limb(p0, p1, r0, r1, rng, sides=side, segs=segs, rise=rise, uv=uv_fn(p0[2]))
        wood_fn(b)
        pieces.append(hidden_in(b, masses, core_k))
        return path

    def twig_set(path, m, n):
        for t in range(n):
            a = rng.uniform(0.45, 0.9)
            q0 = path[int(round(a * (len(path) - 1)))]
            d = G.unit(_rand_unit(rng) * np.array((1, 1, 0.5)) + G.unit(q0 - m.c) * 0.6 + UP * rng.uniform(-0.2, 0.4))
            q1 = m.c + d * m.r * rng.uniform(*twig_reach)
            add(q0, q1, twig_r, twig_r * 0.4, side=4, segs=3, rise=0.12)

    def target(m):
        return m.c - UP * m.r[2] * limb_end + rng.normal(0, 0.06, 3) * m.r

    axis = [m for m in masses if np.linalg.norm(m.c[:2] - tp[-1, :2]) < axis_r * max(m.r[0], 1.0)]
    outer = [m for m in masses if all(m is not a for a in axis)]
    for m in axis:                                       # the leader runs up through these
        j = int(np.argmin(np.linalg.norm(tp - m.c, axis=1)))
        twig_set(tp[max(0, j - 3):j + 1], m, max(1, twigs - 1))
    if outer:
        ang = np.array([math.atan2(m.c[1] - tp[-1, 1], m.c[0] - tp[-1, 0]) for m in outer])
        rot = rng.uniform(0, 2 * PI)
        order = np.argsort((ang - rot) % (2 * PI))
        k = max(1, min(groups, len(outer)))
        for g in np.array_split(order, k):
            ms = [outer[i] for i in g]
            gc = np.mean([target(m) for m in ms], axis=0)
            p0, frac = trunk_at(fork_z + rng.uniform(0, fork_spread))
            r0 = trunk_r * max(0.45, frac) * rng.uniform(*limb_r) * (1.0 + 0.12 * (len(ms) - 1)) ** 0.5
            p1 = p0 + (gc - p0) * rng.uniform(0.5, 0.65)
            main = add(p0, p1, r0, r0 * 0.7)
            for m in ms:
                q0 = main[int(rng.integers(len(main) // 2, len(main)))]
                sub = add(q0, target(m), r0 * 0.62, max(r0 * 0.22, 0.025), segs=4)
                twig_set(sub, m, twigs)
    return pieces
