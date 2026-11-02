# "Levels match the map": what the levels contain has to be what the map shows at their nodes, and the map must not show what
# the levels contradict. The JSON has no zones, but the layout knows them, so this checks the layout the picture and the JSON
# are made from (pure Python, no bpy, no numpy):
#   1. every story node lies in the zone of its route (street: the residential town, market: the market, beach: the sand and
#      boardwalk, underpass: the underpass by the railway, site: the building site, park: the park, L23: at the school gate),
#      and the juggling challenge C05 lies on the park's lawns;
#   2. the railway is crossed only by the routes whose levels have a tunnel: the underpass route once or twice and the park
#      route once, under the line; the street, market, beach and site routes never cross it (not even by a level crossing).
# town_map.py runs this on every build; python town_map_levels.py prints the report.
import math, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import town_map_graph as G

# area kinds that are NOT the residential town (a point inside one of them is not "residential")
SPECIAL_KINDS = ('sea', 'sand', 'park', 'school', 'site', 'station', 'market', 'wood', 'field', 'far', 'underpass', 'school_gate')


def point_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def zones_at(L, p):
    """The names of the zones a point of the layout lies in ('residential' if it is in none of the special areas)."""
    out = set()
    for name, a in L.AREAS.items():
        kind = a.get('kind', name)
        if kind in SPECIAL_KINDS and point_in_poly(p, a['poly']):
            out.add(kind)
    for name, poly in getattr(L, 'CHECK_ZONES', {}).items():
        if point_in_poly(p, poly):
            out.add(name)
    if not out & {'sea', 'sand', 'park', 'school', 'site', 'station', 'market', 'underpass'}:
        out.add('residential')
    return out


def _cross(a, b, c, d):
    """True if the segments ab and cd cross."""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def crossings(route, rail):
    """How many times a route polyline crosses the railway polyline (the line the tracks run along)."""
    n = 0
    for i in range(len(route) - 1):
        for j in range(len(rail) - 1):
            if _cross(route[i], route[i + 1], rail[j], rail[j + 1]):
                n += 1
    return n


def rail_polylines(L):
    """The tracks of the railway (the main line and the station's loop) as polylines."""
    out = [G.catmull_rom(list(L.RAIL['pts']), step=20.0)[0]]
    if getattr(L, 'RAIL2', None):
        out.append(G.catmull_rom(list(L.RAIL2['pts']), step=20.0)[0])
    return out


def count_crossings(route, rails):
    return sum(crossings(route, r) for r in rails)


def check_levels(L, built):
    """A list of problems (empty if the layout matches the levels)."""
    problems = []
    nodes = built['nodes']
    for rid, levels, challenge in built['table']:
        zone = L.LEVEL_ZONES.get(rid)
        for lid in levels:
            n = nodes[lid]
            z = zones_at(L, (n['x'], n['y']))
            want = zone
            if (lid, ) == (L.LAST_ZONE[0],):
                want = L.LAST_ZONE[1]
            if want not in z:
                problems.append(f'{lid} (route {rid}) at ({n["x"]:.0f}, {n["y"]:.0f}) is in {sorted(z)}, not in the {want} zone')
        if challenge and challenge in getattr(L, 'CHALLENGE_ZONES', {}):
            n = nodes[challenge]
            z = zones_at(L, (n['x'], n['y']))
            want = L.CHALLENGE_ZONES[challenge]
            if want not in z:
                problems.append(f'{challenge} (route {rid}) at ({n["x"]:.0f}, {n["y"]:.0f}) is in {sorted(z)}, not in the {want} zone')
    rail = rail_polylines(L)
    want = {'street': (0, 0), 'market': (0, 0), 'beach': (0, 0), 'site': (0, 0), 'underpass': (1, 2), 'park': (1, 1)}
    for rid, pts in built['routes'].items():
        k = count_crossings(pts, rail)
        lo, hi = want[rid]
        if not lo <= k <= hi:
            problems.append(f'route {rid} crosses the railway {k} times (must be {lo}' + ('' if lo == hi else f' to {hi}') + ')')
    return problems


def check_json(L, data, table):
    """The same checks on a TownMapLayout.json (picture px): [problems]."""
    ox, oy = data['core']['x'], data['core']['y']
    routes = {r['id']: [(p['x'] - ox, p['y'] - oy) for p in r['points']] for r in data['routes']}
    nodes = {n['id']: dict(x=n['x'] - ox, y=n['y'] - oy) for n in data['nodes']}
    return check_levels(L, dict(nodes=nodes, routes=routes, table=table))


def report(L, built):
    rail = rail_polylines(L)
    lines = []
    for rid, pts in built['routes'].items():
        lines.append(f'railway crossings of the {rid} route: {count_crossings(pts, rail)}')
    for lid, n in sorted(built['nodes'].items()):
        lines.append(f'{lid}: ({n["x"]:.0f}, {n["y"]:.0f}) zones {sorted(zones_at(L, (n["x"], n["y"])))}')
    probs = check_levels(L, built)
    lines.append('level / map problems: ' + ('none' if not probs else '; '.join(probs)))
    return '\n'.join(lines)


if __name__ == '__main__':
    import town_map_layout as L
    import town_map_build as B
    b = B.build(L)
    print(report(L, b))
    sys.exit(1 if check_levels(L, b) else 0)
