"""The pier's stairs, as built by the game (World/PierStairs.cs, placed by Editor/StreetBuilder.Coast.cs Pier), ported
step for step so the review pictures show what the build makes. Plain Python: no Blender needed.

Coordinates are the game's (Unity): x along the beach, y up, z away from the camera (into the sea). The stairs' origin is
the pier's near end at deck height, on its centre line; the landing and the flights lie in front of it (z < 0).

    the landing      in front of the pier's first span, as wide as the deck, at deck height
    two flights      leaving the landing's left and right ends, down to the sand; a mid-landing halfway when the
                     drop is more than about 2.7 m
    rails            white rails on both sides of each flight and across the landing's front (the pier's rails)
    supports         a bent of four concrete piles under the landing, two under each mid-landing
    feet             a concrete pad at each flight's foot
    lamps            a globe lamp on each of the landing's front corners (the pier's lamps)
"""
import math

GOING = 0.27        # a tread's depth
RISER = 0.19        # the riser aimed for (the real one divides the drop evenly)
MID = 1.3           # a mid-landing's length
SPLIT_OVER = 14     # more risers than this: a mid-landing halfway
NOSING = 0.03
TREAD = 0.06
BAND = 0.3          # the stringer's depth below the steps (measured upright)
RAIL = 1.06         # the handrail's top above the nosings

WHITE = (0.95, 0.94, 0.9)
TIMBER = (0.46, 0.32, 0.22)
CONCRETE = (0.8, 0.78, 0.74)
METAL = (0.1, 0.1, 0.11)
GLOBE = (1.0, 0.93, 0.72)
BOARDS = (0.5, 0.35, 0.24)


def plan(drop):
    """(risers, riser height, risers to the mid-landing, risers after it, horizontal run) for a flight dropping `drop`."""
    n = max(2, int(round(drop / RISER)))
    r = drop / n
    k1 = (n + 1) // 2 if n > SPLIT_OVER else n
    k2 = n - k1
    run = (k1 - 1) * GOING + ((MID + (k2 - 1) * GOING) if k2 > 0 else 0.0)
    return n, r, k1, k2, run


# ---------------------------------------------------------------- a MeshBuilder work-alike (World/MeshBuilder.cs)
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class MB:
    def __init__(self):
        self.v, self.faces = [], []      # faces: (vertex indices, colour), wound as Unity's (clockwise from outside)

    def quad(self, bl, tl, tr, br, outward, col):
        n = cross(sub(tl, bl), sub(tr, bl))
        i = len(self.v); self.v += [bl, tl, tr, br]
        self.faces.append(([i, i + 1, i + 2, i + 3] if dot(n, outward) >= 0 else [i, i + 3, i + 2, i + 1], col))

    def tri(self, a, b, c, outward, col):
        n = cross(sub(b, a), sub(c, a))
        i = len(self.v); self.v += [a, b, c]
        self.faces.append(([i, i + 1, i + 2] if dot(n, outward) >= 0 else [i, i + 2, i + 1], col))

    def box(self, mn, mx, col, bottom=False):
        x0, y0, z0 = mn; x1, y1, z1 = mx
        self.quad((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (0, 0, -1), col)
        self.quad((x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (0, 0, 1), col)
        self.quad((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (0, 1, 0), col)
        if bottom:
            self.quad((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (0, -1, 0), col)
        self.quad((x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (-1, 0, 0), col)
        self.quad((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0), col)

    def cylinder(self, centre, radius, length, col, segments=10):
        """Upright, smooth sides, flat ends (the shape is faceted here: the toon look bands it anyway)."""
        cx, cy, cz = centre
        y0, y1 = cy - length / 2, cy + length / 2
        ring = [(cx + radius * math.cos(2 * math.pi * s / segments), cz + radius * math.sin(2 * math.pi * s / segments)) for s in range(segments)]
        for s in range(segments):
            (ax, az), (bx, bz) = ring[s], ring[(s + 1) % segments]
            mid = ((ax + bx) / 2 - cx, 0, (az + bz) / 2 - cz)
            self.quad((ax, y0, az), (ax, y1, az), (bx, y1, bz), (bx, y0, bz), mid, col)
        for s in range(segments):
            (ax, az), (bx, bz) = ring[s], ring[(s + 1) % segments]
            self.tri((cx, y1, cz), (ax, y1, az), (bx, y1, bz), (0, 1, 0), col)

    def sphere(self, centre, radius, col, lon=10, lat=6):
        cx, cy, cz = centre
        def p(i, j):
            th = math.pi * j / lat; ph = 2 * math.pi * i / lon
            return (cx + radius * math.sin(th) * math.cos(ph), cy + radius * math.cos(th), cz + radius * math.sin(th) * math.sin(ph))
        for j in range(lat):
            for i in range(lon):
                a, b, c, d = p(i, j), p(i, j + 1), p(i + 1, j + 1), p(i + 1, j)
                m = ((a[0] + c[0]) / 2 - cx, (a[1] + c[1]) / 2 - cy, (a[2] + c[2]) / 2 - cz)
                self.quad(a, b, c, d, m, col)

    def prism(self, pts, za, zb, col):
        """A convex outline in the x-y plane (in order round it), extruded from za to zb."""
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        A = [(p[0], p[1], za) for p in pts]; B = [(p[0], p[1], zb) for p in pts]
        if len(pts) == 4:
            self.quad(A[0], A[1], A[2], A[3], (0, 0, -1), col)
            self.quad(B[0], B[1], B[2], B[3], (0, 0, 1), col)
        else:
            self.tri(A[0], A[1], A[2], (0, 0, -1), col)
            self.tri(B[0], B[1], B[2], (0, 0, 1), col)
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            out = ((p[0] + q[0]) / 2 - cx, (p[1] + q[1]) / 2 - cy, 0)
            self.quad(A[i], B[i], B[(i + 1) % len(pts)], A[(i + 1) % len(pts)], out, col)


# ---------------------------------------------------------------- the stairs (World/PierStairs.Build)
def span(a, b):
    return (min(a, b), max(a, b))


def build(mb, width=6.0, depth=1.9, drop_left=4.55, drop_right=4.55, landing_drop=4.55):
    hw = width / 2
    # the landing: timber on a concrete beam, as the pier's deck
    mb.box((-hw, -0.08, -depth), (hw, 0.0, 0.0), TIMBER)
    mb.box((-hw, -0.45, -depth), (hw, -0.08, 0.0), CONCRETE, bottom=True)
    # its front rail, and a lamp on each front corner
    zr = -depth + 0.08
    mb.box((-hw, 0.95, zr - 0.08), (hw, 1.08, zr + 0.08), WHITE, bottom=True)
    mb.box((-hw, 0.48, zr - 0.05), (hw, 0.56, zr + 0.05), WHITE, bottom=True)
    for x in (-hw + 0.09, -1.0, 1.0, hw - 0.09):
        mb.box((x - 0.09, 0.0, zr - 0.09), (x + 0.09, 1.0, zr + 0.09), WHITE)
    for x in (-hw + 0.09, hw - 0.09):
        mb.box((x - 0.13, 1.08, zr - 0.13), (x + 0.13, 1.4, zr + 0.13), METAL)
        mb.cylinder((x, 2.65, zr), 0.07, 2.5, METAL, 6)
        mb.sphere((x, 4.12, zr), 0.22, GLOBE)
    # the bent under it: a cross beam on four piles
    zb = -depth / 2
    mb.box((-hw + 0.1, -1.05, zb - 0.28), (hw - 0.1, -0.45, zb + 0.28), CONCRETE, bottom=True)
    for x in (-hw + 0.35, -0.9, 0.9, hw - 0.35):
        bottom = -landing_drop - 0.6
        mb.cylinder((x, (bottom - 1.05) / 2, zb), 0.24, -1.05 - bottom, CONCRETE, 10)
    for side, drop in ((-1, drop_left), (1, drop_right)):
        flight(mb, side, hw, depth, drop, landing_drop)


def flight(mb, s, hw, depth, drop, landing_drop):
    n, r, k1, k2, run = plan(drop)
    def X(u): return s * (hw + u)
    def ground(u): return -(landing_drop + (drop - landing_drop) * min(1.0, u / max(run, 1e-3)))
    near, far = (-depth, -depth + 0.1), (-0.1, 0.0)
    parts = [(0.0, 0.0, k1)]
    if k2 > 0:
        parts.append(((k1 - 1) * GOING + MID, -k1 * r, k2))
    for u0, y0, k in parts:
        u_end = u0 + (k - 1) * GOING
        for i in range(1, k):
            y = y0 - i * r
            a, b = span(X(u0 + (i - 1) * GOING), X(u0 + i * GOING + NOSING))
            mb.box((a, y - TREAD, -depth + 0.1), (b, y, -0.1), TIMBER, bottom=True)                      # the tread
            a, b = span(X(u0 + i * GOING - 0.025), X(u0 + i * GOING))
            mb.box((a, y - r, -depth + 0.1), (b, y - TREAD, -0.1), WHITE)                                # the riser under its nosing
        # the cut stringers either side: a band under the steps and a tooth under each tread
        def yb(u): return y0 - r - TREAD - r * (u - u0) / GOING
        for za, zb in (near, far):
            mb.prism([(X(u0), yb(u0)), (X(u_end), yb(u_end)), (X(u_end), yb(u_end) - BAND), (X(u0), yb(u0) - BAND)][::s], za, zb, WHITE)
            for i in range(1, k):
                y = y0 - i * r - TREAD
                mb.prism([(X(u0 + (i - 1) * GOING), y), (X(u0 + i * GOING), y), (X(u0 + i * GOING), y - r)][::s], za, zb, WHITE)
        # rails either side: a sloping handrail and mid rail, posts on the treads
        def yn(u): return y0 - r * (u - u0) / GOING
        for zc in (-depth + 0.08, -0.08):
            mb.prism([(X(u0), yn(u0) + RAIL - 0.11), (X(u_end), yn(u_end) + RAIL - 0.11), (X(u_end), yn(u_end) + RAIL), (X(u0), yn(u0) + RAIL)][::s],
                     zc - 0.07, zc + 0.07, WHITE)
            mb.prism([(X(u0), yn(u0) + 0.48), (X(u_end), yn(u_end) + 0.48), (X(u_end), yn(u_end) + 0.55), (X(u0), yn(u0) + 0.55)][::s],
                     zc - 0.04, zc + 0.04, WHITE)
            posts = max(1, int(math.ceil((u_end - u0) / 1.4)))
            for p in range(posts + 1):
                u = u0 + 0.06 + (u_end - u0 - 0.12) * p / posts
                i = min(k - 1, max(1, int((u - u0) / GOING) + 1))
                a, b = span(X(u - 0.06), X(u + 0.06))
                mb.box((a, y0 - i * r, zc - 0.06), (b, yn(u) + RAIL - 0.05, zc + 0.06), WHITE)
        if u0 == 0.0 and k2 > 0:
            # the mid-landing: timber on a concrete beam, rails both sides, two piles
            ym = -k1 * r
            a, b = span(X(u_end), X(u_end + MID))
            mb.box((a, ym - 0.08, -depth), (b, ym, 0.0), TIMBER)
            mb.box((a, ym - 0.4, -depth), (b, ym - 0.08, 0.0), CONCRETE, bottom=True)
            for zc in (-depth + 0.08, -0.08):
                mb.box((a, ym + RAIL - 0.11, zc - 0.07), (b, ym + RAIL, zc + 0.07), WHITE, bottom=True)
                mb.box((a, ym + 0.48, zc - 0.04), (b, ym + 0.55, zc + 0.04), WHITE, bottom=True)
                for u, top in ((u_end, yn(u_end) + RAIL + 0.04), (u_end + MID, ym + RAIL + 0.04)):
                    c, d = span(X(u - 0.07), X(u + 0.07))
                    mb.box((c, ym, zc - 0.07), (d, top, zc + 0.07), WHITE)
            um = u_end + MID / 2
            for z in (-depth + 0.4, -0.4):
                bottom = ground(um) - 0.6
                mb.cylinder((X(um), (bottom + ym - 0.4) / 2, z), 0.18, ym - 0.4 - bottom, CONCRETE, 8)
    # the foot: a concrete pad, and a newel post either side
    a, b = span(X(run - 0.2), X(run + 1.2))
    mb.box((a, -drop - 0.12, -depth - 0.1), (b, -drop + 0.04, 0.1), CONCRETE)
    for zc in (-depth + 0.08, -0.08):
        a, b = span(X(run - 0.08), X(run + 0.08))
        mb.box((a, -drop + 0.04, zc - 0.08), (b, -drop + r + RAIL + 0.06, zc + 0.08), WHITE)


# ---------------------------------------------------------------- the paths on the sand (StreetBuilder.Coast PierPaths)
def path_slats(pier_x, z0, deck_y, width, depth, run_l, run_r, ground, lane_back=2.2):
    """Boardwalk slats from each stair's foot toward the lane: (centre, size) boxes in world coordinates."""
    out = []
    for s, run in ((-1, run_l), (1, run_r)):
        cx = pier_x + s * (width / 2 + run + 0.5)
        z = z0 - depth - 0.2
        while z - 0.18 > lane_back:
            g = max(ground(cx - 0.65, z - 0.08), ground(cx + 0.65, z - 0.08))
            out.append(((cx, g + 0.01, z - 0.09), (1.3, 0.05, 0.18)))
            z -= 0.28
    return out
