# From the layout data (town_map_layout.py) to everything the picture and the JSON need, with no bpy:
# the road graph, the six routes (shortest path through their waypoints, smoothed and resampled), the 28 nodes (on their
# routes, in play order), the label sides, the district label anchors and the street-name stretches.
import math, os, re, json
import town_map_graph as G
import town_map_nodes as N

HERE = os.path.dirname(os.path.abspath(__file__))
ROUTE_TABLE = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Scripts', 'Levels', 'RouteTable.cs'))


def parse_route_table(path=ROUTE_TABLE):
    """[(route id, [level ids], challenge id or None)] in the order of RouteTable.All."""
    src = open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'new Route\("(\w+)",\s*\d+,\s*new\[\]\s*\{([^}]*)\}\s*,\s*(null|"\w+")\)', src):
        levels = re.findall(r'"(L\d+)"', m.group(2))
        ch = None if m.group(3) == 'null' else m.group(3).strip('"')
        out.append((m.group(1), levels, ch))
    return out


def point_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def poly_centroid(poly):
    a = cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        c = x1 * y2 - x2 * y1
        a += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
    if abs(a) < 1e-9:
        return poly[0]
    return (cx / (3 * a), cy / (3 * a))


def build(L, solve=True):
    nodes = dict(L.NODES)
    roads = [G.Road(r[0], r[1], r[2], r[3], nodes) for r in L.ROADS]
    graph = G.Graph(nodes, roads)
    table = parse_route_table()
    routes, used = {}, {}
    for rid, levels, challenge in table:
        wp = L.ROUTES[rid]
        curve, ids = graph.route_curve(wp)
        routes[rid] = G.route_points(curve)
        used[rid] = ids
    home = nodes[L.PLACES['home']]
    school = nodes[L.PLACES['school']]
    places = {'home': home, 'school': school}
    out = dict(graph=graph, routes=routes, used=used, nodes={}, places=places, table=table, label_error=None)
    if not solve:
        return out
    # the nodes and their labels: an exact constraint search (arc consistency) near the anchors the layout gives; if the layout
    # leaves no room it says which node it could not place, and a local search puts the nodes where the fewest rules break
    try:
        placed = N.solve_joint(L, routes, table)
        warn = None
    except ValueError as e:
        warn = str(e)
        print('warning:', warn)
        placed = N.solve_ls(L, routes, table, seed=1, iters=40000, restarts=8, strict=False)
    built_nodes = {k: dict(x=v['x'], y=v['y'], route=v['route'], s=v['s'], anchor_dist=G.dist((v['x'], v['y']), v['anchor']),
                           anchor=v['anchor'], label=v['label']) for k, v in placed.items()}
    out['nodes'] = built_nodes
    out['label_error'] = warn
    out['districts'] = pick_districts(L, out)
    out['streets'] = pick_streets(L, out)
    return out


def pick_districts(L, b):
    """The label anchor of each district: the point of its area that is farthest from routes, nodes and labels."""
    res = {}
    routes = list(b['routes'].values())
    boxes = [G.label_box((n['x'], n['y']), n['label']) for n in b['nodes'].values()]
    npos = [(n['x'], n['y']) for n in b['nodes'].values()]
    ii = G.INNER
    for did, spec in L.DISTRICTS.items():
        if 'at' in spec:
            res[did] = spec['at']
            continue
        poly = spec['poly']
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        cen = poly_centroid(poly)
        best, bs = cen, -1e9
        step = 12
        x = min(xs)
        while x <= max(xs):
            y = min(ys)
            while y <= max(ys):
                p = (x, y)
                if point_in_poly(p, poly) and 60 <= p[0] <= 2340 and 60 <= p[1] <= 1290:
                    dr = min(min(G.dist_to_poly(p, r) for r in routes), 400)
                    dn = min(min(G.dist(p, q) for q in npos) - G.NODE_R, 400)
                    db = min(min(G.box_dist_to_point(bx, p) for bx in boxes), 400)
                    clear = min(dr, dn, db)
                    score = min(clear, spec.get('clear', 130)) * 3 - G.dist(p, cen) * 0.15
                    if score > bs:
                        best, bs = p, score
                y += step
            x += step
        res[did] = best
    return res


def straight_stretches(curve, length=170.0, tol=5.0, step=12.0):
    """Anchors along a road curve where it is straight over `length` px: [(point, tangent, angle in degrees)]."""
    total = G.poly_length(curve)
    out = []
    s = length / 2
    while s <= total - length / 2:
        a, _ = G.point_at(curve, s - length / 2)
        b, _ = G.point_at(curve, s + length / 2)
        m, t = G.point_at(curve, s)
        dev = 0.0
        k = s - length / 2
        while k <= s + length / 2:
            p, _ = G.point_at(curve, k)
            dev = max(dev, G.seg_closest(p, a, b)[2])
            k += 15
        if dev <= tol:
            ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
            if ang > 90:
                ang -= 180
            if ang <= -90:
                ang += 180
            out.append((m, t, ang))
        s += step
    return out


def pick_streets(L, b):
    """A point on a straight stretch of each named road, clear of nodes, label boxes, junctions and the other names; if a
    route runs along the road's middle the point is moved to the side of the carriageway that the route leaves free."""
    res = []
    npos = [(n['x'], n['y']) for n in b['nodes'].values()]
    boxes = [G.label_box((n['x'], n['y']), n['label']) for n in b['nodes'].values()]
    routes = list(b['routes'].values())
    roads = {r.id: r for r in b['graph'].roads}
    junctions = list(b['graph'].nodes.values())
    taken = []
    for spec in L.STREETS:
        name, rid = spec['name'], spec['road']
        r = roads[rid]
        half = L.CLASSES[r.cls]['road'] / 2
        own = b['routes'].get(spec.get('route')) if spec.get('route') else None
        target = spec.get('at')
        if target is None and spec.get('near'):
            ps = [(b['nodes'][k]['x'], b['nodes'][k]['y']) for k in spec['near'] if k in b['nodes']]
            if ps:
                sh = spec.get('shift', (0, 0))
                target = (sum(p[0] for p in ps) / len(ps) + sh[0], sum(p[1] for p in ps) / len(ps) + sh[1])
        best, bs = None, -1e9
        # the clearances relax tier by tier: from the nodes (always), from the label boxes (the screen shows the names of one route's
        # levels at a time, so the last tiers allow a street name under a name box), from the junctions and from the other street names
        for length, nclear, bclear, jclear, spread in ((170, 105, 70, 70, 220), (140, 85, 50, 55, 200), (110, 70, 35, 40, 180), (90, 62, 25, 30, 160),
                                                       (70, 55, 20, 25, 150), (70, 55, -1, 25, 150), (60, 50, -1, 20, 130)):
            for m, t, ang in straight_stretches(r.curve, length):
                if not (150 <= m[0] <= 2250 and 190 <= m[1] <= 1140):
                    continue
                if own is not None and G.dist_to_poly(m, own) > 12:
                    continue                      # the route must really run along this stretch
                dn = min(G.dist(m, q) for q in npos) if npos else 999
                if dn < G.NODE_R + nclear:
                    continue
                if bclear >= 0 and any(G.box_dist_to_point(bx, m) < bclear for bx in boxes):
                    continue
                dj = min(G.dist(m, q) for q in junctions)
                if dj < jclear:
                    continue
                if any(G.dist(m, q) < spread for q in taken):
                    continue
                if target is not None and G.dist(m, target) > spec.get('reach', 340):
                    continue
                # try the centre and the two sides of the carriageway (a route's own name stays within 60 px of the route)
                nx, ny = -t[1], t[0]
                for off in (0.0, half * 0.5, -half * 0.5):
                    q = (m[0] + nx * off, m[1] + ny * off)
                    ends = [(q[0] + t[0] * k, q[1] + t[1] * k) for k in (-length * 0.35, 0.0, length * 0.35)]
                    dr = min(min(G.dist_to_poly(e, rt) for rt in routes) for e in ends)
                    score = min(dr, 26) * 2 + min(dj, 150) * 0.1 + min(dn, 300) * 0.05 - abs(off) * 0.2
                    if target is not None:
                        score -= G.dist(q, target) * 0.35
                    if score > bs:
                        best, bs = (q, ang), score
            if best is not None:
                break
        if best is None:
            print(f'warning: street {name}: no straight stretch of {rid} clear of the nodes (left out)')
            continue
        q, ang = best
        taken.append(q)
        res.append(dict(name=name, x=q[0], y=q[1], angle=ang, road=rid, route=spec.get('route')))
    return res


def to_json(L, b):
    """The TownMapLayout.json content, in image pixel coordinates."""
    ox, oy = G.CORE['x'], G.CORE['y']

    def P(p):
        return {'x': int(round(p[0] + ox)), 'y': int(round(p[1] + oy))}
    data = {
        'image': 'UI/TownMap', 'width': G.IMG_W, 'height': G.IMG_H,
        'core': dict(G.CORE),
        'places': [dict(id='home', **P(b['places']['home'])), dict(id='school', **P(b['places']['school']))],
        'routes': [{'id': rid, 'points': [P(p) for p in b['routes'][rid]]} for rid, _, _ in b['table']],
        'nodes': [],
        'districts': [dict(id=k, **P(v)) for k, v in b['districts'].items()],
        'streets': [dict(name=s['name'], x=int(round(s['x'] + ox)), y=int(round(s['y'] + oy)), angle=round(s['angle'], 1)) for s in b['streets']],
    }
    for nid in sorted(b['nodes'], key=lambda k: (k[0] == 'C', int(k[1:]))):
        n = b['nodes'][nid]
        data['nodes'].append(dict(id=nid, **P((n['x'], n['y'])), label=n['label']))
    return data
