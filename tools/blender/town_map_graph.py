# The town map's road graph and what comes out of it (pure Python: no bpy, no numpy).
#
# town_map_layout.py says WHERE things are (junctions, roads, areas, landmarks, the six routes as waypoints through the
# road graph). This module turns that into geometry: every road becomes a smooth curve (a centripetal Catmull-Rom spline
# through its control points), the junctions cut the roads into edges, a route is the shortest path through its waypoints
# (smoothed and resampled), nodes are projected onto their route, label sides are chosen so that no label meets a route, a
# node or another label, and street names get a straight stretch of road to be written along.
# town_map.py draws the picture from the same objects, so the picture and TownMapLayout.json cannot disagree.
import math
import heapq

# ---- the picture's frame (the layout data is written in core coordinates: x 0..2400, y 0..1350, the core's top-left is 0, 0)
IMG_W, IMG_H = 3200, 1800
CORE = dict(x=400, y=225, w=2400, h=1350)
INNER = (120.0, 170.0, 2280.0, 1130.0)        # x0, y0, x1, y1 of the inner area, in core coordinates
NODE_R = 75.0                                  # a node disc is 150 px across
LABEL_W, LABEL_H = 300.0, 56.0
LABEL_GAP = 10.0                               # between a node's disc and its label
ROUTE_CLEAR = 30.0                             # a label keeps this far from every route
STEM = 300.0                                   # routes may share a stem within this distance of home and of the school


# ------------------------------------------------------------------ small geometry
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def poly_length(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def seg_closest(p, a, b):
    """Closest point to p on the segment ab: (point, parameter 0..1, distance)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    q = (a[0] + dx * t, a[1] + dy * t)
    return q, t, dist(p, q)


def project(p, pts):
    """Closest point of a polyline to p: (point, arc length from the start, distance)."""
    best = (None, 0.0, 1e18)
    run = 0.0
    for i in range(len(pts) - 1):
        q, t, d = seg_closest(p, pts[i], pts[i + 1])
        sl = dist(pts[i], pts[i + 1])
        if d < best[2]:
            best = (q, run + sl * t, d)
        run += sl
    return best


def dist_to_poly(p, pts):
    return project(p, pts)[2]


def point_at(pts, s):
    """Point and unit tangent at arc length s along a polyline."""
    if s <= 0:
        s = 0.0
    run = 0.0
    for i in range(len(pts) - 1):
        sl = dist(pts[i], pts[i + 1])
        if run + sl >= s or i == len(pts) - 2:
            t = 0.0 if sl == 0 else min(1.0, max(0.0, (s - run) / sl))
            p = lerp(pts[i], pts[i + 1], t)
            tx, ty = (pts[i + 1][0] - pts[i][0]), (pts[i + 1][1] - pts[i][1])
            n = math.hypot(tx, ty) or 1.0
            return p, (tx / n, ty / n)
        run += sl
    return pts[-1], (1.0, 0.0)


def resample(pts, step):
    """Points every `step` along the polyline (the last point is the polyline's end)."""
    total = poly_length(pts)
    n = max(1, int(round(total / step)))
    out = []
    run = 0.0
    i = 0
    seglen = [dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1)]
    for k in range(n + 1):
        s = total * k / n
        while i < len(seglen) - 1 and run + seglen[i] < s:
            run += seglen[i]
            i += 1
        t = 0.0 if seglen[i] == 0 else (s - run) / seglen[i]
        out.append(lerp(pts[i], pts[i + 1], min(1.0, max(0.0, t))))
    return out


def catmull_rom(ctrl, step=3.0):
    """A centripetal Catmull-Rom spline through the control points: (dense polyline about `step` px apart, the index of
    every control point in it)."""
    if len(ctrl) < 3:
        line = resample(list(ctrl), step) if len(ctrl) == 2 else list(ctrl)
        return line, [0, len(line) - 1] if len(ctrl) == 2 else [0]
    p = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    # extend the end tangents so that the curve leaves the first and last point straight on
    p[0] = (2 * ctrl[0][0] - ctrl[1][0], 2 * ctrl[0][1] - ctrl[1][1])
    p[-1] = (2 * ctrl[-1][0] - ctrl[-2][0], 2 * ctrl[-1][1] - ctrl[-2][1])
    out = [ctrl[0]]
    idx = [0]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        d1 = max(math.sqrt(dist(p0, p1)), 1e-6); d2 = max(math.sqrt(dist(p1, p2)), 1e-6); d3 = max(math.sqrt(dist(p2, p3)), 1e-6)
        seg = dist(p1, p2)
        n = max(2, int(seg / step))
        t0, t1, t2, t3 = 0.0, d1, d1 + d2, d1 + d2 + d3
        for k in range(1, n + 1):
            tt = t1 + (t2 - t1) * k / n

            def mix(a, b, ta, tb):
                if tb == ta:
                    return a
                w = (tt - ta) / (tb - ta)
                return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)
            a1 = mix(p0, p1, t0, t1); a2 = mix(p1, p2, t1, t2); a3 = mix(p2, p3, t2, t3)
            b1 = mix(a1, a2, t0, t2); b2 = mix(a2, a3, t1, t3)
            out.append(mix(b1, b2, t1, t2))
        out[-1] = p2                      # land exactly on the control point
        idx.append(len(out) - 1)
    return out, idx


def smooth_polyline(pts, sigma=14.0, step=4.0):
    """The polyline resampled every `step` and smoothed with a Gaussian along its length (the ends stay where they are):
    a right-angle turn at a junction becomes a rounded corner a few pixels inside the road's own edge."""
    r = resample(pts, step)
    n = len(r)
    k = int(3 * sigma / step)
    wts = [math.exp(-0.5 * ((j * step) / sigma) ** 2) for j in range(-k, k + 1)]
    out = []
    for i in range(n):
        sx = sy = sw = 0.0
        for j in range(-k, k + 1):
            ii = i + j
            # reflect about the end points so that the ends keep their place and direction
            if ii < 0:
                q = (2 * r[0][0] - r[-ii][0], 2 * r[0][1] - r[-ii][1])
            elif ii >= n:
                q = (2 * r[-1][0] - r[2 * (n - 1) - ii][0], 2 * r[-1][1] - r[2 * (n - 1) - ii][1])
            else:
                q = r[ii]
            w = wts[j + k]
            sx += q[0] * w; sy += q[1] * w; sw += w
        out.append((sx / sw, sy / sw))
    out[0] = r[0]
    out[-1] = r[-1]
    return out


# ------------------------------------------------------------------ the road graph
class Road:
    """One named road: a curve through control points, some of them junctions (named nodes shared with other roads)."""

    def __init__(self, rid, name, cls, ctrl, nodes, width=None, **extra):
        self.id, self.name, self.cls = rid, name, cls
        self.extra = extra
        self.pts = []                      # the control points (x, y)
        self.node_at = {}                  # index into self.pts -> node name
        for i, c in enumerate(ctrl):
            if isinstance(c, str):
                self.pts.append(nodes[c]); self.node_at[i] = c
            else:
                self.pts.append((float(c[0]), float(c[1])))
        self.width = width
        self.curve, self.ctrl_idx = catmull_rom(self.pts)             # dense polyline, index of each control point in it
        self.length = poly_length(self.curve)

    def edges(self):
        """Edges between consecutive junction nodes: (node a, node b, polyline)."""
        keys = sorted(self.node_at)
        out = []
        for a, b in zip(keys, keys[1:]):
            poly = self.curve[self.ctrl_idx[a]:self.ctrl_idx[b] + 1]
            out.append((self.node_at[a], self.node_at[b], poly))
        return out


class Graph:
    def __init__(self, nodes, roads):
        self.nodes = dict(nodes)
        self.roads = roads
        self.edges = []                    # (a, b, polyline, road)
        self.adj = {n: [] for n in self.nodes}
        for r in roads:
            for a, b, poly in r.edges():
                self.edges.append((a, b, poly, r))
                L = poly_length(poly)
                self.adj.setdefault(a, []).append((b, L, len(self.edges) - 1, False))
                self.adj.setdefault(b, []).append((a, L, len(self.edges) - 1, True))

    def shortest(self, a, b):
        """The shortest path between two junctions: a list of (edge index, reversed)."""
        if a == b:
            return []
        dists = {a: 0.0}
        prev = {}
        pq = [(0.0, a)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == b:
                break
            if d > dists.get(u, 1e18):
                continue
            for v, L, ei, rev in self.adj.get(u, []):
                nd = d + L
                if nd < dists.get(v, 1e18):
                    dists[v] = nd
                    prev[v] = (u, ei, rev)
                    heapq.heappush(pq, (nd, v))
        if b not in prev:
            raise ValueError(f'no road from {a} to {b}')
        path = []
        cur = b
        while cur != a:
            u, ei, rev = prev[cur]
            path.append((ei, rev))
            cur = u
        path.reverse()
        return path

    def route_curve(self, waypoints):
        """The dense polyline of the shortest path through the waypoints (junction names), and the roads it uses."""
        pts = []
        used = []
        for a, b in zip(waypoints, waypoints[1:]):
            for ei, rev in self.shortest(a, b):
                poly = self.edges[ei][2]
                poly = list(reversed(poly)) if rev else list(poly)
                if pts and dist(pts[-1], poly[0]) < 1e-6:
                    pts.extend(poly[1:])
                else:
                    pts.extend(poly)
                used.append(self.edges[ei][3].id)
        return pts, used


# ------------------------------------------------------------------ routes, nodes, labels
def route_points(curve, count_per_px=1 / 40.0, lo=30, hi=90):
    """The smoothed route resampled to 30..90 points (about one per 40 px)."""
    sm = smooth_polyline(curve, sigma=16.0, step=4.0)
    L = poly_length(sm)
    n = int(round(L * count_per_px))
    n = max(lo, min(hi, n))
    return resample(sm, L / (n - 1)) if n > 1 else sm


def label_box(node, side):
    """(x0, y0, x1, y1) of a node's label placed on a side."""
    x, y = node
    if side == 'below':
        return (x - LABEL_W / 2, y + NODE_R + LABEL_GAP, x + LABEL_W / 2, y + NODE_R + LABEL_GAP + LABEL_H)
    if side == 'above':
        return (x - LABEL_W / 2, y - NODE_R - LABEL_GAP - LABEL_H, x + LABEL_W / 2, y - NODE_R - LABEL_GAP)
    if side == 'right':
        return (x + NODE_R + LABEL_GAP, y - LABEL_H / 2, x + NODE_R + LABEL_GAP + LABEL_W, y + LABEL_H / 2)
    return (x - NODE_R - LABEL_GAP - LABEL_W, y - LABEL_H / 2, x - NODE_R - LABEL_GAP, y + LABEL_H / 2)


def box_dist_to_seg(box, a, b):
    """Distance from an axis-aligned box to a segment (0 if they touch)."""
    x0, y0, x1, y1 = box
    # a segment crossing or inside the box
    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    best = 1e18
    for i in range(4):
        c, d = corners[i], corners[(i + 1) % 4]
        if _seg_seg_intersect(a, b, c, d):
            return 0.0
        best = min(best, seg_closest(a, c, d)[2], seg_closest(b, c, d)[2], seg_closest(c, a, b)[2], seg_closest(d, a, b)[2])
    return best


def _seg_seg_intersect(p1, p2, p3, p4):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    o1, o2, o3, o4 = orient(p1, p2, p3), orient(p1, p2, p4), orient(p3, p4, p1), orient(p3, p4, p2)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def box_dist_to_poly(box, pts):
    return min(box_dist_to_seg(box, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def box_dist_to_box(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)


def box_dist_to_point(box, p):
    dx = max(box[0] - p[0], p[0] - box[2], 0.0)
    dy = max(box[1] - p[1], p[1] - box[3], 0.0)
    return math.hypot(dx, dy)


def choose_sides(nodes, routes, preferred=None):
    """For each node id, a side for its label such that the box keeps ROUTE_CLEAR from every route, clear of every other
    node's disc and of every other label. A small search (nodes are few): greedy by how constrained a node is, then a
    backtracking pass. nodes: {id: (x, y)}; routes: {id: polyline}; preferred: {id: [sides in order]}."""
    sides = ['below', 'above', 'right', 'left']
    prefs = {k: list(sides) for k in nodes}
    for k, v in (preferred or {}).items():
        prefs[k] = list(v) + [s for s in sides if s not in v]
    allroutes = list(routes.values())
    ok = {}
    for k, p in nodes.items():
        ok[k] = []
        for s in prefs[k]:
            box = label_box(p, s)
            if any(box_dist_to_poly(box, r) < ROUTE_CLEAR for r in allroutes):
                continue
            if any(k2 != k and box_dist_to_point(box, p2) < NODE_R + 4 for k2, p2 in nodes.items()):
                continue
            ok[k].append(s)
    order = sorted(nodes, key=lambda k: len(ok[k]))
    chosen = {}

    def clash(k, s):
        box = label_box(nodes[k], s)
        for k2, s2 in chosen.items():
            if box_dist_to_box(box, label_box(nodes[k2], s2)) < 6:
                return True
        return False

    def solve(i):
        if i == len(order):
            return True
        k = order[i]
        for s in ok[k]:
            if not clash(k, s):
                chosen[k] = s
                if solve(i + 1):
                    return True
                del chosen[k]
        return False

    if not solve(0):
        bad = [k for k in nodes if not ok[k]]
        raise ValueError('no label placement: nodes without any free side: ' + ', '.join(bad) if bad else 'no consistent label placement')
    return chosen
