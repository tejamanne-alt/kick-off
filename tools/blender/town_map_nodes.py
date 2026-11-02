# Places the 28 level nodes and their labels. The layout names a place for each level (an anchor and how far the node may
# slide along its route, or around the anchor for a challenge); this searches for positions near the anchors such that every
# node lies on its route, the nodes keep 190 px apart and in play order, and every label (300 x 56 px, on the node's below /
# above / left / right side) keeps clear of every route, every other node and every other label.
# A small constraint search (numpy): forward checking, the most constrained node first, the nearest-to-the-anchor option first.
import math
import numpy as np
import town_map_graph as G

SIDES = ('below', 'above', 'right', 'left')
SIDE_COST = {'below': 0.0, 'above': 4.0, 'right': 8.0, 'left': 9.0}
MIN_NODE_GAP = 190.8
# The label rules of the map screen (it draws the names of the focused route's levels only, over every route line): a name keeps
# 30 px from its OWN route's centre line and only must not cross the other routes' lines; it keeps 6 px from every node disc;
# it keeps 6 px from the names of the levels of its own route (story levels and challenge); names of different routes may overlap.
OWN_ROUTE_CLEAR = 30.6
OTHER_ROUTE_CLEAR = 2.0
LABEL_DISC_CLEAR = G.NODE_R + 6.6                # from a node's centre to a name box
LABEL_LABEL_CLEAR = 6.6
PLACE_CLEAR = 120.6                              # a node keeps this far from home and the school
CORE_W, CORE_H = float(G.CORE['w']), float(G.CORE['h'])


def _inner(p):
    i = G.INNER
    return i[0] <= p[0] <= i[2] and i[1] <= p[1] <= i[3]


def _box_in_core(b):
    return b[0] >= 4 and b[1] >= 4 and b[2] <= CORE_W - 4 and b[3] <= CORE_H - 4


class Var:
    """One node: its candidate (position, side) options as arrays."""

    def __init__(self, nid, route, order, kind, anchor, options):
        self.id, self.route, self.order, self.kind, self.anchor = nid, route, order, kind, anchor
        options = sorted(options, key=lambda o: o[4])
        self.opts = options
        n = len(options)
        self.x = np.array([o[0] for o in options], float)
        self.y = np.array([o[1] for o in options], float)
        self.s = np.array([(-1.0 if o[2] is None else o[2]) for o in options], float)
        self.cost = np.array([o[4] for o in options], float)
        self.box = np.array([G.label_box((o[0], o[1]), o[3]) for o in options], float).reshape(n, 4)


def _segments(routes):
    """All the routes' segments as two (n, 2) arrays."""
    P, Q = [], []
    for pts in routes:
        for i in range(len(pts) - 1):
            P.append(pts[i]); Q.append(pts[i + 1])
    return np.array(P, float), np.array(Q, float)


def box_min_dist(box, P, Q):
    """The smallest distance from an axis-aligned box (x0, y0, x1, y1) to any of the segments P[i]Q[i] (0 if one touches it)."""
    x0, y0, x1, y1 = box
    # endpoints inside the box
    inside = lambda A: (A[:, 0] >= x0) & (A[:, 0] <= x1) & (A[:, 1] >= y0) & (A[:, 1] <= y1)
    if (inside(P) | inside(Q)).any():
        return 0.0
    # segment / box intersection (Liang-Barsky for all segments at once)
    d = Q - P
    t0 = np.zeros(len(P)); t1 = np.ones(len(P))
    ok = np.ones(len(P), bool)
    for axis, lo, hi in ((0, x0, x1), (1, y0, y1)):
        da = d[:, axis]
        pa = P[:, axis]
        par = np.abs(da) < 1e-12
        ok &= ~(par & ((pa < lo) | (pa > hi)))
        with np.errstate(divide='ignore', invalid='ignore'):
            ta = np.where(par, -np.inf, (lo - pa) / da)
            tb = np.where(par, np.inf, (hi - pa) / da)
        tmin = np.minimum(ta, tb); tmax = np.maximum(ta, tb)
        t0 = np.maximum(t0, tmin); t1 = np.minimum(t1, tmax)
    if (ok & (t0 <= t1)).any():
        return 0.0
    # otherwise the closest approach is between an endpoint and the box, or a corner and a segment
    best = 1e18
    for A in (P, Q):
        dx = np.maximum(np.maximum(x0 - A[:, 0], A[:, 0] - x1), 0.0)
        dy = np.maximum(np.maximum(y0 - A[:, 1], A[:, 1] - y1), 0.0)
        best = min(best, float(np.hypot(dx, dy).min()))
    l2 = np.maximum((d * d).sum(axis=1), 1e-12)
    for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        t = np.clip(((cx - P[:, 0]) * d[:, 0] + (cy - P[:, 1]) * d[:, 1]) / l2, 0.0, 1.0)
        qx = P[:, 0] + t * d[:, 0]; qy = P[:, 1] + t * d[:, 1]
        best = min(best, float(np.hypot(cx - qx, cy - qy).min()))
    return best


def candidates(L, routes, table, challenge_range=(132.0, 256.0), step=6.0, grid=12.0):
    """{node id: Var}"""
    own_seg = {rid: _segments([pts]) for rid, pts in routes.items()}
    other_seg = {rid: _segments([p for r2, p in routes.items() if r2 != rid]) for rid in routes}
    places = [L.NODES[L.PLACES['home']], L.NODES[L.PLACES['school']]]
    out = {}
    cache = {}

    def sides_for(rid, x, y):
        key = (rid, round(x, 1), round(y, 1))
        if key in cache:
            return cache[key]
        res = []
        for side in SIDES:
            box = G.label_box((x, y), side)
            if not _box_in_core(box):
                continue
            if box_min_dist(box, *own_seg[rid]) < OWN_ROUTE_CLEAR:
                continue
            if box_min_dist(box, *other_seg[rid]) < OTHER_ROUTE_CLEAR:
                continue
            res.append(side)
        cache[key] = res
        return res

    def near_place(p):
        return any(math.hypot(p[0] - q[0], p[1] - q[1]) < PLACE_CLEAR for q in places)

    import town_map_levels as LV
    zone_cache = {}

    def in_zone(p, zone):
        """The layout's zones (see town_map_levels): a node of a level must stand on what the level is on."""
        if zone is None:
            return True
        key = (round(p[0]), round(p[1]))
        if key not in zone_cache:
            zone_cache[key] = LV.zones_at(L, p)
        return zone in zone_cache[key]

    for rid, levels, challenge in table:
        pts = routes[rid]
        total = G.poly_length(pts)
        for order, lid in enumerate(levels):
            spec = L.STORY[lid]
            anchor = spec[1]
            slack = spec[2] if len(spec) > 2 else 600.0
            zone = L.LAST_ZONE[1] if lid == L.LAST_ZONE[0] else L.LEVEL_ZONES.get(rid)
            q0, s0, d0 = G.project(anchor, pts)
            opts = []
            s = max(6.0, s0 - slack)
            while s <= min(total - 6.0, s0 + slack):
                p, _ = G.point_at(pts, s)
                if _inner(p) and in_zone(p, zone) and not near_place(p):
                    for side in sides_for(rid, *p):
                        opts.append((p[0], p[1], s, side, abs(s - s0) + SIDE_COST[side]))
                s += step
            out[lid] = Var(lid, rid, order, 'story', anchor, opts)
        if challenge:
            spec = L.CHALLENGE[challenge]
            anchor = spec[1]
            slack = spec[2] if len(spec) > 2 else 200.0
            czone = getattr(L, 'CHALLENGE_ZONES', {}).get(challenge)
            opts = []
            dx = -slack
            while dx <= slack:
                dy = -slack
                while dy <= slack:
                    p = (anchor[0] + dx, anchor[1] + dy)
                    if _inner(p) and in_zone(p, czone) and not near_place(p):
                        d = G.dist_to_poly(p, pts)
                        if challenge_range[0] <= d <= challenge_range[1]:
                            # a disc that covers another route's line is allowed but costly (the pockets between the routes are tight)
                            over = 0.0
                            for r2, pts2 in routes.items():
                                if r2 != rid:
                                    d2 = G.dist_to_poly(p, pts2)
                                    if d2 < G.NODE_R + 6:
                                        over += 300.0 + (G.NODE_R + 6 - d2) * 4
                            for side in sides_for(rid, *p):
                                opts.append((p[0], p[1], None, side, math.hypot(dx, dy) + SIDE_COST[side] + over))
                    dy += grid
                dx += grid
            out[challenge] = Var(challenge, rid, None, 'challenge', anchor, opts)
    return out


def _box_point_dist(box, px, py):
    dx = np.maximum(np.maximum(box[0] - px, px - box[2]), 0.0)
    dy = np.maximum(np.maximum(box[1] - py, py - box[3]), 0.0)
    return np.hypot(dx, dy)


def _box_box_dist(a, boxes):
    dx = np.maximum(np.maximum(boxes[:, 0] - a[2], a[0] - boxes[:, 2]), 0.0)
    dy = np.maximum(np.maximum(boxes[:, 1] - a[3], a[1] - boxes[:, 3]), 0.0)
    return np.hypot(dx, dy)


def compat(a, i, b):
    """Boolean mask over b's options: compatible with option i of a."""
    ax, ay, abox = a.x[i], a.y[i], a.box[i]
    ok = np.hypot(b.x - ax, b.y - ay) >= MIN_NODE_GAP
    ok &= _box_point_dist(abox, b.x, b.y) >= LABEL_DISC_CLEAR
    dx = np.maximum(np.maximum(b.box[:, 0] - ax, ax - b.box[:, 2]), 0.0)
    dy = np.maximum(np.maximum(b.box[:, 1] - ay, ay - b.box[:, 3]), 0.0)
    ok &= np.hypot(dx, dy) >= LABEL_DISC_CLEAR
    if a.route == b.route:
        ok &= _box_box_dist(abox, b.box) >= LABEL_LABEL_CLEAR
        if a.kind == 'story' and b.kind == 'story':
            ok &= ((a.order < b.order) == (a.s[i] < b.s))
    return ok


def _pair_matrix(a, b):
    """Boolean matrix [option of a, option of b]: the two options can live together (same rules as compat(), all at once)."""
    na, nb = len(a.opts), len(b.opts)
    ax, ay = a.x[:, None], a.y[:, None]
    bx, by = b.x[None, :], b.y[None, :]
    ok = np.hypot(bx - ax, by - ay) >= MIN_NODE_GAP
    # a's label against b's node disc
    abx0, aby0, abx2, aby2 = (a.box[:, k][:, None] for k in range(4))
    dx = np.maximum(np.maximum(abx0 - bx, bx - abx2), 0.0)
    dy = np.maximum(np.maximum(aby0 - by, by - aby2), 0.0)
    ok &= np.hypot(dx, dy) >= LABEL_DISC_CLEAR
    # b's label against a's node disc
    bbx0, bby0, bbx2, bby2 = (b.box[:, k][None, :] for k in range(4))
    dx = np.maximum(np.maximum(bbx0 - ax, ax - bbx2), 0.0)
    dy = np.maximum(np.maximum(bby0 - ay, ay - bby2), 0.0)
    ok &= np.hypot(dx, dy) >= LABEL_DISC_CLEAR
    if a.route == b.route:
        # label against label (only the names shown together: those of one route)
        dx = np.maximum(np.maximum(bbx0 - abx2, abx0 - bbx2), 0.0)
        dy = np.maximum(np.maximum(bby0 - aby2, aby0 - bby2), 0.0)
        ok &= np.hypot(dx, dy) >= LABEL_LABEL_CLEAR
        if a.kind == 'story' and b.kind == 'story':
            ok &= ((a.order < b.order) == (a.s[:, None] < b.s[None, :]))
    return ok


def build_matrices(vars_, keys):
    n = len(keys)
    C = {}
    for i in range(n):
        for j in range(i + 1, n):
            m = _pair_matrix(vars_[keys[i]], vars_[keys[j]])
            C[(i, j)] = m
            C[(j, i)] = m.T
    return C


def _ac(D, C, n, queue=None):
    """Arc consistency (AC-3 over numpy boolean domains). Returns the index of a variable whose domain emptied, or -1."""
    if queue is None:
        queue = [(i, j) for i in range(n) for j in range(n) if i != j]
    inq = set(queue)
    while queue:
        i, j = queue.pop()
        inq.discard((i, j))
        sup = C[(i, j)][:, D[j]].any(axis=1)
        new = D[i] & sup
        if new.sum() != D[i].sum():
            if not new.any():
                return i
            D[i] = new
            for k in range(n):
                if k != i and k != j and (k, i) not in inq:
                    queue.append((k, i)); inq.add((k, i))
    return -1


def solve_joint(L, routes, table, grids=(12.0, 8.0, 6.0)):
    """Every node by the exact search (challenge nodes first), the challenge pockets sampled on a coarse grid first and a finer one
    if that fails. Same result as solve_mac()."""
    last = None
    for g in grids:
        try:
            return solve_challenge_first(L, routes, table, grid=g)
        except ValueError as e:
            last = e
    raise last


def solve_phased(L, routes, table, budget=40000, vars_=None):
    """The story nodes by the exact search (they are what the routes and the levels depend on), then each challenge node, the most
    constrained first, at the cheapest option that lives with everything already placed. Returns the same dict as solve_mac;
    raises ValueError if the story nodes cannot all be placed or a challenge node finds no room."""
    V = dict(vars_) if vars_ is not None else candidates(L, routes, table)
    story = {k: v for k, v in V.items() if v.kind == 'story'}
    chal = {k: v for k, v in V.items() if v.kind == 'challenge'}
    idx = _solve_mac_idx(story, budget)
    for ck in sorted(chal, key=lambda k: len(chal[k].opts)):
        v = chal[ck]
        if len(v.opts) == 0:
            raise ValueError(f'no position with a free label side near the anchor of: {ck}')
        ok = np.ones(len(v.opts), bool)
        for k, a in idx.items():
            ok &= compat(V[k], a, v)
        if not ok.any():
            raise ValueError(f'no room for the challenge node {ck} beside the placed nodes')
        cand = np.nonzero(ok)[0]
        idx[ck] = int(min(cand, key=lambda a: v.cost[a]))
    out = {}
    for k, a in idx.items():
        v = V[k]
        o = v.opts[a]
        out[k] = dict(x=o[0], y=o[1], s=o[2], label=o[3], route=v.route, disp=o[4], anchor=v.anchor)
    return out


def solve_mac(L, routes, table, budget=60000, vars_=None, seed=1):
    """Exact search: maintaining arc consistency, smallest domain first, the option nearest its anchor first. Raises ValueError
    if there is no placement (naming the variable whose domain emptied first) or the budget runs out."""
    vars_ = dict(vars_) if vars_ is not None else candidates(L, routes, table)
    idx = _solve_mac_idx(vars_, budget)
    out = {}
    for k, a in idx.items():
        v = vars_[k]
        o = v.opts[a]
        out[k] = dict(x=o[0], y=o[1], s=o[2], label=o[3], route=v.route, disp=o[4], anchor=v.anchor)
    return out


def solve_challenge_first(L, routes, table, grid=24.0, tries=200, per_budget=400, vars_=None):
    """The picky nodes first: the challenge nodes (their pockets are small) are fixed one by one at one of their cheapest options
    that arc consistency still allows, depth first, and the story nodes are then solved by the exact search around them. Far
    faster than the plain exact search when the pockets are tight. Same result as solve_mac()."""
    V = dict(vars_) if vars_ is not None else candidates(L, routes, table, grid=grid)
    keys = sorted(V)
    empty = [k for k in keys if len(V[k].opts) == 0]
    if empty:
        raise ValueError('no position with a free label side near the anchor of: ' + ', '.join(empty))
    n = len(keys)
    pos = {k: i for i, k in enumerate(keys)}
    C = build_matrices(V, keys)
    D0 = [np.ones(len(V[k].opts), bool) for k in keys]
    bad = _ac(D0, C, n)
    if bad >= 0:
        raise ValueError('arc consistency empties the domain of ' + keys[bad])
    chal = sorted([k for k in keys if V[k].kind == 'challenge'], key=lambda k: int(D0[pos[k]].sum()))
    state = dict(last=None)

    def rec(ci, D):
        if ci == len(chal):
            try:
                return _mac_search(V, keys, C, D, per_budget)
            except ValueError as e:
                state['last'] = str(e)
                return None
        k = chal[ci]
        i = pos[k]
        cand = sorted(np.nonzero(D[i])[0], key=lambda a: V[k].cost[a])
        # spread the tries over the whole pocket, not only its cheapest corner
        if len(cand) > tries:
            step = len(cand) / float(tries)
            cand = [cand[int(j * step)] for j in range(tries)]
        for a in cand:
            D2 = [d.copy() for d in D]
            D2[i] = np.zeros_like(D[i]); D2[i][a] = True
            if _ac(D2, C, n, queue=[(j, i) for j in range(n) if j != i]) < 0:
                res = rec(ci + 1, D2)
                if res is not None:
                    return res
        return None

    res = rec(0, D0)
    if res is None:
        raise ValueError('no consistent placement of the nodes (challenge-first search: %s)' % (state['last'] or 'every pocket option failed'))
    out = {}
    for i, a in res.items():
        k = keys[i]
        v = V[k]
        o = v.opts[a]
        out[k] = dict(x=o[0], y=o[1], s=o[2], label=o[3], route=v.route, disp=o[4], anchor=v.anchor)
    return out


def _solve_mac_idx(vars_, budget):
    keys = sorted(vars_)
    empty = [k for k in keys if len(vars_[k].opts) == 0]
    if empty:
        raise ValueError('no position with a free label side near the anchor of: ' + ', '.join(empty))
    n = len(keys)
    C = build_matrices(vars_, keys)
    D = [np.ones(len(vars_[k].opts), bool) for k in keys]
    bad = _ac(D, C, n)
    if bad >= 0:
        raise ValueError('arc consistency empties the domain of ' + keys[bad])
    res = _mac_search(vars_, keys, C, D, budget)
    return {keys[i]: a for i, a in res.items()}


def _mac_search(vars_, keys, C, D, budget):
    """The exact search from the domains D (already arc consistent): index of each variable -> its option index."""
    n = len(keys)
    steps = [0]
    deepest = [0, None]
    chosen = {}

    def search(D):
        steps[0] += 1
        if steps[0] > budget:
            return None
        free = [i for i in range(n) if i not in chosen]
        if not free:
            return dict(chosen)
        i = min(free, key=lambda k: int(D[k].sum()))
        if len(chosen) > deepest[0]:
            deepest[0], deepest[1] = len(chosen), keys[i]
        cost = vars_[keys[i]].cost
        for a in sorted(np.nonzero(D[i])[0], key=lambda a: cost[a]):
            D2 = [d.copy() for d in D]
            D2[i] = np.zeros_like(D[i]); D2[i][a] = True
            chosen[i] = int(a)
            bad = _ac(D2, C, n, queue=[(j, i) for j in range(n) if j != i])
            if bad < 0:
                res = search(D2)
                if res is not None:
                    return res
            del chosen[i]
            if steps[0] > budget:
                return None
        return None

    res = search(D)
    if res is None:
        raise ValueError(f'no consistent placement of the nodes (exhaustive search stuck near {deepest[1]} after {deepest[0]} nodes, {steps[0]} steps)')
    return res


def solve(L, routes, table, budget=150000, skip=(), vars_=None):
    vars_ = dict(vars_) if vars_ is not None else candidates(L, routes, table)
    for k in skip:
        vars_.pop(k, None)
    empty = [k for k, v in vars_.items() if len(v.opts) == 0]
    if empty:
        raise ValueError('no position with a free label side near the anchor of: ' + ', '.join(empty))
    masks = {k: np.ones(len(v.opts), bool) for k, v in vars_.items()}
    chosen = {}
    steps = [0]
    deepest = [0, None]

    def search(masks):
        steps[0] += 1
        if steps[0] > budget:
            return None
        if len(chosen) == len(vars_):
            return dict(chosen)
        k = min((k for k in masks if k not in chosen), key=lambda k: int(masks[k].sum()))
        if len(chosen) > deepest[0]:
            deepest[0], deepest[1] = len(chosen), k
        v = vars_[k]
        for i in np.nonzero(masks[k])[0]:
            chosen[k] = int(i)
            nm = {}
            ok = True
            for k2, m2 in masks.items():
                if k2 in chosen:
                    continue
                f = m2 & compat(v, int(i), vars_[k2])
                if not f.any():
                    ok = False
                    break
                nm[k2] = f
            if ok:
                for k2 in chosen:
                    nm[k2] = masks[k2]
                res = search(nm)
                if res is not None:
                    return res
            del chosen[k]
        return None

    res = search(masks)
    if res is None:
        raise ValueError(f'no consistent placement of the nodes (stuck near {deepest[1]} after {deepest[0]} nodes, {steps[0]} steps)')
    out = {}
    for k, i in res.items():
        v = vars_[k]
        o = v.opts[i]
        out[k] = dict(x=o[0], y=o[1], s=o[2], label=o[3], route=v.route, disp=o[4], anchor=v.anchor)
    return out


def solve_ls(L, routes, table, seed=1, iters=60000, skip=(), vars_=None, restarts=8, strict=True):
    """The same search by local search (min-conflicts with noise and restarts, then a greedy pass towards the anchors):
    much faster than the exhaustive search when there is room, and it finds placements the exhaustive one runs out of
    budget on. Returns the same dict as solve(), or raises ValueError."""
    import random
    vars_ = dict(vars_) if vars_ is not None else candidates(L, routes, table)
    for k in skip:
        vars_.pop(k, None)
    keys = sorted(vars_)
    empty = [k for k in keys if len(vars_[k].opts) == 0]
    if empty:
        raise ValueError('no position with a free label side near the anchor of: ' + ', '.join(empty))
    n = len(keys)
    idx = {k: i for i, k in enumerate(keys)}
    # pairwise compatibility matrices: C[i][j][a, b] is True when option a of i and option b of j can live together
    C = {}
    for i, ki in enumerate(keys):
        vi = vars_[ki]
        for j in range(i + 1, n):
            vj = vars_[keys[j]]
            m = np.zeros((len(vi.opts), len(vj.opts)), bool)
            for a in range(len(vi.opts)):
                m[a] = compat(vi, a, vj)
            C[(i, j)] = m
            C[(j, i)] = m.T
    rng = random.Random(seed)
    best_state, best_viol, best_pairs = None, 1e9, []

    def viol_vector(i, state):
        """For each option of variable i: the number of other variables it clashes with."""
        v = np.zeros(len(vars_[keys[i]].opts), int)
        for j in range(n):
            if j != i:
                v += ~C[(i, j)][:, state[j]]
        return v

    for attempt in range(restarts):
        state = [0] * n
        for i in range(n):
            # start from a random one of the cheapest options
            state[i] = rng.randrange(min(len(vars_[keys[i]].opts), 6))
        for it in range(iters // restarts):
            conflicted = [i for i in range(n) if any(not C[(i, j)][state[i], state[j]] for j in range(n) if j != i)]
            if not conflicted:
                break
            i = rng.choice(conflicted)
            v = viol_vector(i, state)
            cost = vars_[keys[i]].cost
            score = v * 1000.0 + cost * 0.2 + np.array([rng.random() * 40 for _ in range(len(v))])
            if rng.random() < 0.08:
                state[i] = rng.randrange(len(v))
            else:
                state[i] = int(np.argmin(score))
        total = sum(1 for i in range(n) for j in range(i + 1, n) if not C[(i, j)][state[i], state[j]])
        if total < best_viol:
            best_viol, best_state = total, list(state)
            best_pairs = [(keys[i], keys[j]) for i in range(n) for j in range(i + 1, n) if not C[(i, j)][state[i], state[j]]]
        if total == 0:
            break
    if best_viol > 0 and strict:
        raise ValueError(f'no consistent placement of the nodes (local search left {best_viol} clashes: {best_pairs})')
    state = best_state
    # greedy descent towards the anchors: move each node to a cheaper option that clashes with nothing
    for rnd in range(6):
        changed = False
        for i in range(n):
            v = viol_vector(i, state)
            cost = vars_[keys[i]].cost
            ok = np.nonzero(v == 0)[0]
            if len(ok):
                b = int(ok[np.argmin(cost[ok])])
                if cost[b] < cost[state[i]] - 1e-6:
                    state[i] = b
                    changed = True
        if not changed:
            break
    out = {}
    for i, k in enumerate(keys):
        v = vars_[k]
        o = v.opts[state[i]]
        out[k] = dict(x=o[0], y=o[1], s=o[2], label=o[3], route=v.route, disp=o[4], anchor=v.anchor)
    return out
