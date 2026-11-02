#!/usr/bin/env python3
"""Validates TownMapLayout.json (the world map's layout data) against the contract the map screen codes to. Pure Python, no
bpy, no numpy; it fails loudly (exit code 1, every broken rule printed).

    python3 town_map_check.py [path/to/TownMapLayout.json] [path/to/RouteTable.cs]

The picture is 3200 x 1800 px with its core (x 400, y 225, 2400 x 1350) where all the content lives; the data is in picture
pixels, origin top-left, y down. A node disc is 150 px across; a label (a level's name) is a 300 x 56 px box 10 px off the disc
on the node's side (below / above / left / right). The map screen draws the names of the focused route's levels only, over every
route line, so: a name keeps 30 px from its OWN route's centre line and only must not cross the other routes' centre lines (more
than 1 px off), it keeps 6 px from every node disc, and 6 px from the names of the levels of its own route (its story levels and
its challenge); names of different routes may overlap. Nodes are 190 px apart and 120 px from the home and the school.

When town_map_layout.py and town_map_levels.py are next to this file the level / map rules are checked too: every story node in
the zone of its route (street: the residential town, market, beach: the sand and boardwalk, underpass, site, park; L23 at the
school gate), C03 on the sand, C04 in the building site's yard, C05 on the park's lawns, and only the underpass route (under one
or two tracks) and the park route (once) crossing the railway.
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Resources', 'TownMapLayout.json'))
DEFAULT_TABLE = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Scripts', 'Levels', 'RouteTable.cs'))
DEFAULT_STRINGS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Scripts', 'Localization', 'StringTables.cs'))

IMG_W, IMG_H = 3200, 1800
CORE = dict(x=400, y=225, w=2400, h=1350)
INNER = (120.0, 170.0, 2280.0, 1130.0)           # inside the core: x0, y0, x1, y1
NODE_R = 75.0
LABEL_W, LABEL_H, LABEL_GAP = 300.0, 56.0, 10.0
ROUTE_CLEAR = 30.0               # a name from its own route's centre line
OTHER_ROUTE_CROSS = 1.0          # a name must be more than this from every other route's centre line (not cross it)
NAME_DISC_CLEAR = 6.0            # a name from every node disc
NAME_NAME_CLEAR = 6.0            # a name from the names of the levels of its own route
PLACE_GAP = 120.0                # a node from home and from the school
NODE_GAP = 190.0
ROUTE_GAP = 90.0
STEM = 300.0
HOME_END_TOL = 25.0
STORY_ON_ROUTE = 12.0
MIN_ROUTE_LEN = 1200.0
DISTRICTS = ['neighbourhood', 'market', 'beach', 'park', 'railway', 'site', 'school', 'sea']
SIDES = ('below', 'above', 'left', 'right')


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_closest(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    q = (a[0] + dx * t, a[1] + dy * t)
    return q, t, dist(p, q)


def project(p, pts):
    """(distance from p to the polyline, arc length of the closest point)"""
    best, run, at = 1e18, 0.0, 0.0
    for i in range(len(pts) - 1):
        q, t, d = seg_closest(p, pts[i], pts[i + 1])
        sl = dist(pts[i], pts[i + 1])
        if d < best:
            best, at = d, run + sl * t
        run += sl
    return best, at


def length(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def label_box(node, side):
    x, y = node
    if side == 'below':
        return (x - LABEL_W / 2, y + NODE_R + LABEL_GAP, x + LABEL_W / 2, y + NODE_R + LABEL_GAP + LABEL_H)
    if side == 'above':
        return (x - LABEL_W / 2, y - NODE_R - LABEL_GAP - LABEL_H, x + LABEL_W / 2, y - NODE_R - LABEL_GAP)
    if side == 'right':
        return (x + NODE_R + LABEL_GAP, y - LABEL_H / 2, x + NODE_R + LABEL_GAP + LABEL_W, y + LABEL_H / 2)
    return (x - NODE_R - LABEL_GAP - LABEL_W, y - LABEL_H / 2, x - NODE_R - LABEL_GAP, y + LABEL_H / 2)


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _crosses(p1, p2, p3, p4):
    return _orient(p1, p2, p3) * _orient(p1, p2, p4) < 0 and _orient(p3, p4, p1) * _orient(p3, p4, p2) < 0


def box_seg_dist(box, a, b):
    x0, y0, x1, y1 = box
    if (x0 <= a[0] <= x1 and y0 <= a[1] <= y1) or (x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    best = 1e18
    for i in range(4):
        c, d = corners[i], corners[(i + 1) % 4]
        if _crosses(a, b, c, d):
            return 0.0
        best = min(best, seg_closest(a, c, d)[2], seg_closest(b, c, d)[2], seg_closest(c, a, b)[2], seg_closest(d, a, b)[2])
    return best


def box_poly_dist(box, pts):
    return min(box_seg_dist(box, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def box_point_dist(box, p):
    return math.hypot(max(box[0] - p[0], p[0] - box[2], 0.0), max(box[1] - p[1], p[1] - box[3], 0.0))


def box_box_dist(a, b):
    return math.hypot(max(b[0] - a[2], a[0] - b[2], 0.0), max(b[1] - a[3], a[1] - b[3], 0.0))


def parse_route_table(path):
    src = open(path, encoding='utf-8').read()
    out = []
    for m in re.finditer(r'new Route\("(\w+)",\s*\d+,\s*new\[\]\s*\{([^}]*)\}\s*,\s*(null|"\w+")\)', src):
        levels = re.findall(r'"(L\d+)"', m.group(2))
        out.append((m.group(1), levels, None if m.group(3) == 'null' else m.group(3).strip('"')))
    return out


def parse_route_names(path):
    """{route id: English route name} from the string table ("route.street" -> "Home Street")."""
    if not path or not os.path.exists(path):
        return {}
    src = open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'\{\s*"route\.(\w+)"\s*,\s*"([^"]+)"\s*\}', src):
        out.setdefault(m.group(1), m.group(2))
    return out


def parse_level_names(path):
    """{level id: English level name} ("level.L05" -> "Puddle Lane"), first occurrence = the English table."""
    if not path or not os.path.exists(path):
        return {}
    src = open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'\{\s*"level\.([LC]\d+)"\s*,\s*"([^"]+)"\s*\}', src):
        out.setdefault(m.group(1), m.group(2))
    return out


# the street names that sit beside the street route's levels (the levels are on Elm Street, Hill Road, Garden Lane and Puddle Lane)
LEVEL_STREETS = (('Elm Street', 'L02'), ('Hill Road', 'L03'), ('Garden Lane', 'L04'), ('Puddle Lane', 'L05'))
LEVEL_STREET_MAX = 260.0          # px from the level's node
ROUTE_NAME_MAX = 60.0             # px from the route's polyline


class Report:
    def __init__(self):
        self.errors, self.notes = [], []

    def fail(self, msg):
        self.errors.append(msg)

    def ok(self, msg):
        self.notes.append(msg)


def in_core(p):
    return CORE['x'] <= p[0] <= CORE['x'] + CORE['w'] and CORE['y'] <= p[1] <= CORE['y'] + CORE['h']


def in_inner(p):
    return (CORE['x'] + INNER[0] <= p[0] <= CORE['x'] + INNER[2]) and (CORE['y'] + INNER[1] <= p[1] <= CORE['y'] + INNER[3])


def check(data, table, rep, strings=None):
    # ---- the picture and its core
    if data.get('image') != 'UI/TownMap':
        rep.fail(f"image is {data.get('image')!r}, expected 'UI/TownMap'")
    if (data.get('width'), data.get('height')) != (IMG_W, IMG_H):
        rep.fail(f"size is {data.get('width')} x {data.get('height')}, expected {IMG_W} x {IMG_H}")
    if data.get('core') != CORE:
        rep.fail(f"core is {data.get('core')}, expected {CORE}")
    # ---- places
    places = {p['id']: (float(p['x']), float(p['y'])) for p in data.get('places', [])}
    for pid in ('home', 'school'):
        if pid not in places:
            rep.fail(f'place {pid} missing')
        elif not in_inner(places[pid]):
            rep.fail(f'place {pid} {places[pid]} is outside the core\'s inner area')
    if len(places) != 2:
        rep.fail(f'{len(places)} places, expected exactly home and school')
    home, school = places.get('home', (0, 0)), places.get('school', (0, 0))
    # ---- routes
    routes = {}
    got = [r['id'] for r in data.get('routes', [])]
    want = [t[0] for t in table]
    if got != want:
        rep.fail(f'route ids {got} are not RouteTable\'s {want}')
    for r in data.get('routes', []):
        pts = [(float(p['x']), float(p['y'])) for p in r['points']]
        routes[r['id']] = pts
        n = len(pts)
        if not (30 <= n <= 90):
            rep.fail(f"route {r['id']}: {n} points, expected 30 to 90")
        if n < 2:
            continue
        if dist(pts[0], home) > HOME_END_TOL:
            rep.fail(f"route {r['id']}: starts {dist(pts[0], home):.0f} px from home (max {HOME_END_TOL:.0f})")
        if dist(pts[-1], school) > HOME_END_TOL:
            rep.fail(f"route {r['id']}: ends {dist(pts[-1], school):.0f} px from the school (max {HOME_END_TOL:.0f})")
        L = length(pts)
        if L < MIN_ROUTE_LEN:
            rep.fail(f"route {r['id']}: {L:.0f} px long, expected at least {MIN_ROUTE_LEN:.0f}")
        out = [p for p in pts if not in_core(p)]
        if out:
            rep.fail(f"route {r['id']}: {len(out)} points outside the core, first {out[0]}")
        # smooth: no sharp turn between neighbouring segments, no zig-zag (many alternating turns within a short run)
        turns = []
        for i in range(1, n - 1):
            a = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            b = (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            if math.hypot(*a) < 1e-6 or math.hypot(*b) < 1e-6:
                continue
            ang = math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1]))
            turns.append((i, ang))
            if abs(ang) > 75:
                rep.fail(f"route {r['id']}: a {abs(ang):.0f} degree turn at point {i} ({pts[i]}): not smooth")
        sharp = [(i, a) for i, a in turns if abs(a) > 12]
        flips = [(i, j) for (i, a), (j, b) in zip(sharp, sharp[1:]) if a * b < 0 and j - i <= 2]
        if len(flips) >= 3:
            rep.fail(f"route {r['id']}: zig-zags ({len(flips)} quick back-and-forth turns, first near point {flips[0][0]})")
        rep.ok(f"route {r['id']}: {n} points, {L:.0f} px")
    # routes keep 90 px apart outside the stems (300 px round home and the school)
    ids = [r for r in want if r in routes]

    def far(p):
        return dist(p, home) > STEM and dist(p, school) > STEM
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = routes[ids[i]], routes[ids[j]]
            best, where = 1e18, None
            for p in a:
                if not far(p):
                    continue
                for k in range(len(b) - 1):
                    if not (far(b[k]) and far(b[k + 1])):
                        continue
                    d = seg_closest(p, b[k], b[k + 1])[2]
                    if d < best:
                        best, where = d, p
            if best < ROUTE_GAP:
                rep.fail(f'routes {ids[i]} and {ids[j]} come within {best:.0f} px of each other at {tuple(round(v) for v in where)} (min {ROUTE_GAP:.0f}, except within {STEM:.0f} px of home and school)')
    # ---- nodes
    nodes = {}
    want_ids = [lid for t in table for lid in t[1]] + [t[2] for t in table if t[2]]
    for n in data.get('nodes', []):
        if n['id'] in nodes:
            rep.fail(f"node {n['id']} appears twice")
        nodes[n['id']] = n
    if sorted(nodes) != sorted(want_ids):
        missing = sorted(set(want_ids) - set(nodes))
        extra = sorted(set(nodes) - set(want_ids))
        rep.fail(f'node ids differ from RouteTable: missing {missing}, extra {extra}')
    if len(nodes) != 28:
        rep.fail(f'{len(nodes)} nodes, expected 28')
    pos = {k: (float(v['x']), float(v['y'])) for k, v in nodes.items()}
    for k, n in nodes.items():
        if n.get('label') not in SIDES:
            rep.fail(f"node {k}: label side {n.get('label')!r} is not one of {SIDES}")
        if not in_inner(pos[k]):
            rep.fail(f'node {k} {pos[k]} is outside the core\'s inner area')
    for rid, levels, ch in table:
        pts = routes.get(rid)
        if not pts:
            continue
        last = -1.0
        for lid in levels:
            if lid not in pos:
                continue
            d, at = project(pos[lid], pts)
            if d > STORY_ON_ROUTE:
                rep.fail(f'story node {lid} is {d:.1f} px from its route {rid} (max {STORY_ON_ROUTE:.0f})')
            if at <= last:
                rep.fail(f'story node {lid} is not after the previous level along route {rid} (arc {at:.0f} <= {last:.0f})')
            last = at
        if ch and ch in pos:
            d, at = project(pos[ch], pts)
            if not (130.0 <= d <= 260.0):
                rep.fail(f'challenge node {ch} is {d:.0f} px from its route {rid} (expected 130 to 260)')
    keys = sorted(pos)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            d = dist(pos[a], pos[b])
            if d < NODE_GAP:
                rep.fail(f'nodes {a} and {b} are {d:.0f} px apart (min {NODE_GAP:.0f})')
    for k in keys:
        for pid, pp in (('home', home), ('school', school)):
            if dist(pos[k], pp) < PLACE_GAP:
                rep.fail(f'node {k} is {dist(pos[k], pp):.0f} px from the {pid} (min {PLACE_GAP:.0f})')
    # The names: the map screen draws the names of the focused route's levels only, over every route line. A name keeps 30 px from
    # its OWN route's centre line and only must not cross the other routes' lines, it keeps 6 px from every node disc, and 6 px from
    # the names of the levels of its own route (its story levels and its challenge); names of different routes may overlap.
    route_of = {}
    for rid, levels, ch in table:
        for lid in levels:
            route_of[lid] = rid
        if ch:
            route_of[ch] = rid
    boxes = {k: label_box(pos[k], nodes[k]['label']) for k in keys if nodes[k].get('label') in SIDES}
    for k, box in boxes.items():
        for rid, pts in routes.items():
            d = box_poly_dist(box, pts)
            if rid == route_of.get(k):
                if d < ROUTE_CLEAR:
                    rep.fail(f'label of {k} ({nodes[k]["label"]}) is {d:.0f} px from its own route {rid} (min {ROUTE_CLEAR:.0f})')
            elif d <= OTHER_ROUTE_CROSS:
                rep.fail(f'label of {k} ({nodes[k]["label"]}) crosses the centre line of route {rid} (must stay more than {OTHER_ROUTE_CROSS:.0f} px off)')
        for k2 in keys:
            if k2 != k and box_point_dist(box, pos[k2]) < NODE_R + NAME_DISC_CLEAR:
                rep.fail(f'label of {k} ({nodes[k]["label"]}) is {box_point_dist(box, pos[k2]) - NODE_R:.0f} px from the disc of node {k2} (min {NAME_DISC_CLEAR:.0f})')
        for k2, box2 in boxes.items():
            if k2 > k and route_of.get(k2) == route_of.get(k) and box_box_dist(box, box2) < NAME_NAME_CLEAR:
                rep.fail(f'labels of {k} and {k2} (same route {route_of.get(k)}) are {box_box_dist(box, box2):.0f} px apart (min {NAME_NAME_CLEAR:.0f})')
    # ---- districts and streets
    dist_ids = [d['id'] for d in data.get('districts', [])]
    if sorted(dist_ids) != sorted(DISTRICTS):
        rep.fail(f'districts {sorted(dist_ids)} are not {sorted(DISTRICTS)}')
    for d in data.get('districts', []):
        if not in_core((float(d['x']), float(d['y']))):
            rep.fail(f"district {d['id']} is outside the core")
    streets = data.get('streets', [])
    if not (8 <= len(streets) <= 14):
        rep.fail(f'{len(streets)} streets, expected 8 to 14')
    for s in streets:
        if not s.get('name') or not isinstance(s.get('angle'), (int, float)):
            rep.fail(f'street {s} has no name or angle')
        elif not in_core((float(s['x']), float(s['y']))):
            rep.fail(f"street {s['name']} is outside the core")
        elif not (-90 <= s['angle'] <= 90):
            rep.fail(f"street {s['name']}: angle {s['angle']} outside -90..90")
    # ---- the street names must not contradict the route signs and level names the levels show ("School -> via <route name>")
    route_names = parse_route_names(strings)
    level_names = parse_level_names(strings)
    if strings and not route_names:
        rep.fail(f'cannot read the route names from {strings}')
    for rid in ('street', 'market', 'beach'):
        name = route_names.get(rid)
        pts = routes.get(rid)
        if not name or not pts:
            continue
        mine = [s for s in streets if s.get('name') == name]
        if not mine:
            rep.fail(f'no street is called {name!r} (the name of the {rid} route): the road the route follows must carry it')
            continue
        best = min(project((float(s['x']), float(s['y'])), pts)[0] for s in mine)
        if best > ROUTE_NAME_MAX:
            rep.fail(f'the street {name!r} is {best:.0f} px from the {rid} route (max {ROUTE_NAME_MAX:.0f}): the name must sit on the road the route follows')
        else:
            rep.ok(f'street {name!r} is {best:.0f} px from the {rid} route')
    for name, lid in LEVEL_STREETS:
        mine = [s for s in streets if s.get('name') == name]
        if not mine:
            rep.fail(f'no street is called {name!r} (it is beside {lid} on the street route)')
        elif lid in pos:
            best = min(dist((float(s['x']), float(s['y'])), pos[lid]) for s in mine)
            if best > LEVEL_STREET_MAX:
                rep.fail(f'the street {name!r} is {best:.0f} px from {lid} (max {LEVEL_STREET_MAX:.0f})')
    taken = {v.lower(): k for k, v in level_names.items() if v.lower() != 'puddle lane'}
    for s in streets:
        if s.get('name', '').lower() in taken:
            rep.fail(f"street {s['name']!r} is the name of level {taken[s['name'].lower()]}: a street must not be called after a level (only Puddle Lane is)")
    return rep


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_JSON
    table_path = argv[2] if len(argv) > 2 else DEFAULT_TABLE
    strings_path = argv[3] if len(argv) > 3 else DEFAULT_STRINGS
    data = json.load(open(path, encoding='utf-8'))
    table = parse_route_table(table_path)
    if len(table) != 6:
        print(f'cannot read the six routes from {table_path}')
        return 1
    rep = check(data, table, Report(), strings_path)
    # levels match the map: every level's node is in its zone and only the underpass and park routes cross the railway (this needs
    # the layout the picture is made from, town_map_layout.py, which lives next to this file)
    try:
        sys.path.insert(0, HERE)
        import town_map_layout as TL
        import town_map_levels as LV
    except ImportError:
        TL = None
        rep.ok('town_map_layout.py not importable: the level / map zone and railway checks were skipped')
    if TL is not None:
        probs = LV.check_json(TL, data, table)
        for line in probs:
            rep.fail('level / map: ' + line)
        if not probs:
            rail = LV.rail_polylines(TL)
            cross = {rid: LV.count_crossings([(p['x'] - data['core']['x'], p['y'] - data['core']['y']) for p in r['points']], rail) for r in data['routes'] for rid in [r['id']]}
            rep.ok('level / map: every story node is in the zone of its route, L23 at the school gate, C03 on the sand, C04 in the site yard, C05 on the park '
                   'lawns; railway crossings (under it) ' + ', '.join(f'{k} {v}' for k, v in cross.items()))
    for line in rep.notes:
        print('  ok  ', line)
    for line in rep.errors:
        print('  FAIL', line)
    print(f'{os.path.basename(path)}: {len(rep.errors)} problem(s)' if rep.errors else f'{os.path.basename(path)}: all checks passed')
    return 1 if rep.errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
