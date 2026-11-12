# Kamakura's map plan (docs/KAMAKURA_BUILD.md, "The map plan"): the three routes traced on the user's clean map
# (review/kamakura/refs/KM-MAP2_clean.png, 2752 x 1536) along its own roads, as docs/CITIES.md designs them; the stops
# between the levels at their places; each level's node near the start of its leg, as the game's map screen puts it.
#   python3 tools/city_map/kamakura.py [out dir]        (default review/kamakura/map)
# Writes KM-MAP3_plan_game.png (the plan drawn on the clean map, at the game's sizes), KamakuraMapLayout.json (the
# layout in the game's 3200 x 1800 picture, TownMapLayout's format) and checks.txt; exits 1 if a check fails.
# The checks are the map screen's (Tests/Editor/TownMapTests.cs, docs/WORLD_MAP.md) with Kamakura's two differences:
# a route may cross another once at a right angle (the avenue crosses the tram line), and the shared ends follow the
# user's rule (5 to 15 % of each route at home, at most 15 % at the school) instead of TownMapTests' 320 px.
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
CLEAN = os.path.join(REPO, 'review', 'kamakura', 'refs', 'KM-MAP2_clean.png')
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(REPO, 'review', 'kamakura', 'map')

# ------------------------------------------------------------------ the plan, in the clean map's pixels
HOME = (283, 1185)            # the gate of the two-storey house on the lane west of the tram line's end
SCHOOL = (2215, 346)          # Yukinoshita Elementary's gate, on the road east of the shrine's upper torii

STEM = [HOME, (295, 1120), (300, 1062)]                          # out of the gate to the corner: all three routes
APPROACH = [(1868, 358), (1960, 358), (2100, 360), SCHOOL]       # from under the upper torii to the school gate
SHRINE_STEPS = [(1876, 470), (1872, 420), (1868, 358)]           # the central path and steps up to the torii's foot

ROUTES = {
    # KM1 The Enoden: the lane by the tracks to Hase Station, the tram to Kamakura Station, up Komachi-dori to the
    # shrine's side gate, then straight on up the street along the shrine's east side and right to the school (the user:
    # "after 1-3 go straight and right to school, instead of shrine route")
    'KM1': STEM + [(330, 1078), (370, 1090), (420, 1092), (540, 1092), (720, 1090), (860, 1080),
                   (900, 1078), (1100, 1077), (1300, 1077), (1500, 1077), (1700, 1077), (1880, 1078), (2100, 1080),
                   (2250, 1080),
                   (2265, 1020), (2268, 940), (2285, 885), (2260, 800), (2230, 700), (2205, 600), (2188, 520),
                   (2180, 490), (2120, 485), (2100, 483),
                   (2100, 430)] + APPROACH[2:],
    # KM2 The Shonan Coast: down the lane, across the coast road, through the tunnel to the boardwalk, along the sand
    # to Grandma's shop, past the lifeguard tower to the rocks, back to the avenue's foot, up the avenue under both torii
    'KM2': STEM + [(330, 1078), (370, 1090), (395, 1105), (397, 1180), (400, 1245), (437, 1272), (437, 1330),
                   (445, 1380), (500, 1396), (600, 1396),
                   (700, 1372), (850, 1366), (1000, 1365), (1200, 1360), (1400, 1355), (1480, 1345), (1534, 1330),
                   (1600, 1336), (1700, 1340), (1800, 1342),
                   (1850, 1358), (1950, 1362), (2010, 1368), (2035, 1330), (2028, 1292), (1960, 1283), (1895, 1278),
                   (1888, 1200), (1886, 1110),
                   (1884, 1000), (1880, 800), (1878, 600), (1876, 517)] + SHRINE_STEPS + APPROACH[1:],
    # KM3 The Temple Hills: up the lane, the hydrangea steps to the temple, the ridge walkway, past the cave tomb to
    # Genjiyama, through the bamboo to the bell tower, down its steps and along to the torii and school
    'KM3': STEM + [(300, 1000), (298, 930), (292, 900), (250, 885), (205, 840), (185, 760), (168, 680), (183, 617),
                   (250, 575), (296, 517), (285, 480), (300, 452),
                   (340, 420), (380, 350), (433, 312), (508, 278), (580, 245), (650, 215), (720, 200), (800, 195),
                   (880, 180), (975, 165), (1040, 190), (1100, 235), (1160, 268), (1240, 262), (1290, 262),
                   (1350, 290), (1420, 300), (1500, 295), (1560, 290), (1562, 330), (1565, 372), (1630, 385),
                   (1700, 360), (1780, 358)] + APPROACH,
}
KEY = (780, 1462)             # where the plan's key sits (in the sea)
COLOURS = {'KM1': (226, 52, 45), 'KM2': (38, 112, 220), 'KM3': (247, 196, 28)}
NAMES = {'KM1': 'The Enoden', 'KM2': 'The Shonan Coast', 'KM3': 'The Temple Hills'}

# The stops between the levels (RouteTable's ids to be), each at its place on its route: (id, route, name, point)
STOPS = [
    ('hase', 'KM1', 'Hase Station', (860, 1080)),
    ('kamakuraStation', 'KM1', 'Kamakura Station', (2250, 1080)),
    ('shrineSideGate', 'KM1', "Shrine side gate", (2100, 483)),
    ('boardwalk', 'KM2', 'The boardwalk', (600, 1396)),
    ('grandmasShop', 'KM2', "Grandma's shop", (1534, 1330)),
    ('lifeguardTower', 'KM2', 'Lifeguard tower', (1800, 1342)),
    ('greatTorii', 'KM2', 'The great torii', (1886, 1110)),
    ('trailSign', 'KM3', 'Trail sign', (300, 452)),
    ('genjiyama', 'KM3', 'Genjiyama park', (1290, 262)),
]
LEGS = {   # each level: its route, where it starts (home or a stop), its name
    'KM1-1': ('KM1', 'home', 'Hase Lanes'), 'KM1-2': ('KM1', 'hase', 'Ride the Enoden'),
    'KM1-3': ('KM1', 'kamakuraStation', 'Komachi-dori'), 'KM1-4': ('KM1', 'shrineSideGate', 'The Shrine Bridge'),
    'KM2-1': ('KM2', 'home', 'Down to Yuigahama'), 'KM2-2': ('KM2', 'boardwalk', 'Yuigahama Morning'),
    'KM2-3': ('KM2', 'grandmasShop', "Grandma's Whitebait Shop"), 'KM2-4': ('KM2', 'lifeguardTower', 'The Kite Thief'),
    'KM2-5': ('KM2', 'greatTorii', 'Wakamiya-oji'),
    'KM3-1': ('KM3', 'home', 'Hydrangea Steps'), 'KM3-2': ('KM3', 'trailSign', 'The Hiking Trail'),
    'KM3-3': ('KM3', 'genjiyama', 'Genjiyama Down to School'),
}
NODE_AFTER = {'KM1-4': 100}      # px past its stop where a level's node goes, if not the usual 120 (KM1-4: clear of the school's pin)
RIDES = [('KM1', 'hase', 'kamakuraStation')]       # drawn dashed: the tram
DISTRICTS = [('hase', (520, 960)), ('yuigahama', (1100, 1430)), ('komachi', (2330, 640)), ('wakamiya', (1990, 800)),
             ('shrine', (1860, 160)), ('hills', (560, 120)), ('sea', (900, 1500))]
STREETS = [('Enoden', (1300, 1050), 0.0), ('Komachi-dori', (2300, 700), -76.0), ('Wakamiya-oji', (1940, 700), -90.0),
           ('Coast Road', (1200, 1262), 0.0)]
LABEL = {'KM1-1': 'above', 'KM1-2': 'above', 'KM1-3': 'right', 'KM1-4': 'below', 'KM2-1': 'left', 'KM2-2': 'above',
         'KM2-3': 'above', 'KM2-4': 'below', 'KM2-5': 'left', 'KM3-1': 'left', 'KM3-2': 'right', 'KM3-3': 'below'}

# ------------------------------------------------------------------ the game's picture: 3200 x 1800, the map inside
# The clean map sits in the middle of the game's picture at K game pixels per map pixel, so that every node and both
# places fall in the core's inner area (docs/WORLD_MAP.md: x 520..2680, y 395..1355); the ring round it is the clean
# map extended outward (MAP KM-MAP3 in docs/IMAGE_PROMPTS.md).
GAME_W, GAME_H = 3200, 1800
CORE = (400, 225, 2400, 1350)
INNER = (CORE[0] + 120, CORE[1] + 170, CORE[0] + 2280, CORE[1] + 1130)
NODE_D, STOP_R = 150.0, 21.0
K = 0.83
OFF = ((GAME_W - 2752 * K) / 2, 209.0)
game = lambda p: (OFF[0] + K * p[0], OFF[1] + K * p[1])


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def at(pts, s):
    """The point s along the polyline."""
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if s <= d:
            t = s / d if d else 0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        s -= d
    return pts[-1]


def along(pts, p):
    """How far along the polyline its nearest point to p lies, and how far p is from it."""
    best, s0 = (1e9, 0.0), 0.0
    for a, b in zip(pts, pts[1:]):
        ab = np.subtract(b, a)
        L = float(np.hypot(*ab))
        t = 0.0 if L == 0 else max(0.0, min(1.0, float(np.dot(np.subtract(p, a), ab)) / L ** 2))
        q = np.add(a, ab * t)
        d = float(np.hypot(*np.subtract(p, q)))
        if d < best[0]:
            best = (d, s0 + t * L)
        s0 += L
    return best[1], best[0]


def dense(pts, step=4.0):
    L = length(pts)
    return [at(pts, s) for s in np.arange(0, L + step, step)]


def plan():
    routes = {r: [game(p) for p in pts] for r, pts in ROUTES.items()}
    stops = {sid: (r, name, game(p)) for sid, r, name, p in STOPS}
    home, school = game(HOME), game(SCHOOL)
    # where each route's own stretch begins: the first point 75 px (game) from every other route
    own = {}
    for r, pts in routes.items():
        others = [dense(q) for k, q in routes.items() if k != r]
        L = length(pts)
        for s in np.arange(0, L, 4.0):
            p = at(pts, s)
            if all(min(math.dist(p, q) for q in o) >= 75 for o in others):
                own[r] = s
                break
    # each level's node: a route's first 150 px into its own stretch; a later one 120 px past the stop it starts from
    nodes = {}
    for lid, (r, start, _) in LEGS.items():
        pts = routes[r]
        s = own[r] + 150 if start == 'home' else along(pts, stops[start][2])[0] + NODE_AFTER.get(lid, 120)
        nodes[lid] = at(pts, s)
    return routes, stops, nodes, home, school, own


def checks(routes, stops, nodes, home, school, own):
    out, ok = [], True

    def check(cond, text):
        nonlocal ok
        ok &= bool(cond)
        out.append(('ok   ' if cond else 'FAIL ') + text)

    for r, pts in routes.items():
        L = length(pts)
        check(math.dist(pts[0], home) <= 25 and math.dist(pts[-1], school) <= 25, '%s starts at home and ends at school' % r)
        check(L >= 1200, '%s is %d px long (1200 or more)' % (r, L))
    # shared ends: the stretch at each end within 40 px of another route
    for r, pts in routes.items():
        L = length(pts)
        others = [dense(q) for k, q in routes.items() if k != r]
        near = lambda s: any(min(math.dist(at(pts, s), q) for q in o) < 40 for o in others)
        s0 = 0.0
        while s0 < L and near(s0):
            s0 += 4
        s1 = L
        while s1 > 0 and near(s1):
            s1 -= 4
        a, b = s0 / L * 100, (L - s1) / L * 100
        check(5 <= a <= 15, '%s shares %.1f %% of its length with another route leaving home (5 to 15 %%)' % (r, a))
        check(b <= 15, '%s shares %.1f %% with another route at the school end (15 %% at most)' % (r, b))
    # apart in the middles: 90 px except near the ends and at the one crossing
    rs = list(routes)
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            A, B = routes[rs[i]], routes[rs[j]]
            LA, LB = length(A), length(B)
            dB = dense(B)
            close = []
            for s in np.arange(0, LA, 4.0):
                p = at(A, s)
                if s < 0.15 * LA + 40 or s > LA - 0.15 * LA - 40:
                    continue
                d = min(math.dist(p, q) for q in dB)
                if d < 90:
                    sB, _ = along(B, p)
                    if sB < 0.15 * LB + 40 or sB > LB - 0.15 * LB - 40:
                        continue
                    close.append(s)
            runs = 0 if not close else 1 + sum(1 for a, b in zip(close, close[1:]) if b - a > 8)
            span = 0 if not close else max(close) - min(close) if runs == 1 else sum(4 for _ in close)
            check(runs <= 1 and span <= 200, '%s and %s keep 90 px apart in their middles, but for %d crossing(s) %d px long'
                  % (rs[i], rs[j], runs, span))
    # nodes
    ids = list(nodes)
    for lid in ids:
        x, y = nodes[lid]
        check(INNER[0] <= x <= INNER[2] and INNER[1] <= y <= INNER[3], '%s node (%d, %d) inside the core\'s inner area' % (lid, x, y))
    for p, name in ((home, 'home'), (school, 'school')):
        check(INNER[0] <= p[0] <= INNER[2] and INNER[1] <= p[1] <= INNER[3], '%s (%d, %d) inside the core\'s inner area' % (name, *p))
    worst = min((math.dist(nodes[a], nodes[b]), a, b) for i, a in enumerate(ids) for b in ids[i + 1:])
    check(worst[0] >= 190, 'node discs 190 px apart or more (closest: %s and %s, %d px)' % (worst[1], worst[2], worst[0]))
    for r, pts in routes.items():
        mine = sorted((along(pts, nodes[l])[0], l) for l in ids if LEGS[l][0] == r)
        check([l for _, l in mine] == sorted(l for l in ids if LEGS[l][0] == r), '%s nodes in playing order along it' % r)
        check(all(along(pts, nodes[l])[1] <= 12 for _, l in mine), '%s nodes within 12 px of it' % r)
        first = mine[0]
        check(first[0] - own[r] <= 500, '%s first node %d px into its own stretch (500 at most)' % (r, first[0] - own[r]))
    for sid, (r, name, p) in stops.items():
        pts = routes[r]
        s, d = along(pts, p)
        check(d <= 2, 'stop %s within 2 px of %s' % (sid, r))
        before = [l for l in ids if LEGS[l][0] == r and LEGS[l][1] != sid and along(pts, nodes[l])[0] < s]
        after = [l for l in ids if LEGS[l][0] == r and LEGS[l][1] == sid]
        check(after and along(pts, nodes[after[0]])[0] - s <= 260, 'the level starting at %s has its node within 260 px after it' % sid)
        check(bool(before), 'stop %s lies after a node of its route' % sid)
        clear = min(math.dist(p, n) for n in nodes.values())
        check(clear >= NODE_D / 2 + STOP_R, 'stop %s clear of every node (%d px)' % (sid, clear))
    return ok, out


def draw(routes, stops, nodes, home, school, out_png):
    im = Image.open(CLEAN).convert('RGB')
    inv = lambda p: ((p[0] - OFF[0]) / K, (p[1] - OFF[1]) / K)
    d = ImageDraw.Draw(im, 'RGBA')
    big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
    mid = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
    s = 1 / K
    # the others first, then the casing and colour of each route; the tram ride dashed
    for r in ('KM3', 'KM2', 'KM1'):
        pts = [inv(p) for p in routes[r]]
        d.line(pts, fill=(255, 255, 255, 255), width=int(30 * s), joint='curve')
    for r in ('KM3', 'KM2', 'KM1'):
        pts = [inv(p) for p in routes[r]]
        d.line(pts, fill=COLOURS[r] + (255,), width=int(20 * s), joint='curve')
    for r, a, b in RIDES:
        pts = [inv(p) for p in routes[r]]
        s0, s1 = along(pts, inv(stops[a][2]))[0], along(pts, inv(stops[b][2]))[0]
        x = s0
        while x < s1:
            d.line([at(pts, x), at(pts, min(x + 26, s1))], fill=(255, 255, 255, 255), width=int(8 * s))
            x += 52
    for sid, (r, name, p) in stops.items():
        x, y = inv(p)
        rr = STOP_R * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, 255), outline=(40, 40, 40, 255), width=3)
        d.ellipse([x - rr / 2, y - rr / 2, x + rr / 2, y + rr / 2], fill=COLOURS[r] + (255,))
    for lid, p in nodes.items():
        x, y = inv(p)
        rr = NODE_D / 2 * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=COLOURS[LEGS[lid][0]] + (235,), outline=(255, 255, 255, 255), width=8)
        t = lid[2:]
        tw = d.textlength(t, font=big)
        d.text((x - tw / 2, y - 24), t, font=big, fill=(255, 255, 255), stroke_width=3, stroke_fill=(30, 30, 30))
    # the stops' names last, each on the first side clear of every node disc and of the names already placed
    discs = [(inv(p), NODE_D / 2 * s + 6) for p in nodes.values()]
    taken = []
    hit = lambda b, c, r: max(b[0], min(c[0], b[2])) - c[0] <= r and False or \
        (max(b[0], min(c[0], b[2])) - c[0]) ** 2 + (max(b[1], min(c[1], b[3])) - c[1]) ** 2 < r * r
    for sid, (r, name, p) in stops.items():
        x, y = inv(p)
        rr = STOP_R * s
        tw = d.textlength(name, font=mid)
        w, h = tw + 24, 38
        spots = []
        for g in (0, 40, 80, 120):          # beside the marker first, then a little further out
            spots += [(x + rr + 6 + g, y - h / 2), (x - rr - 6 - g - w, y - h / 2), (x - w / 2, y - rr - 8 - g - h),
                      (x - w / 2, y + rr + 8 + g), (x + rr + g, y - rr - g - h), (x + rr + g, y + rr + g),
                      (x - rr - g - w, y - rr - g - h), (x - rr - g - w, y + rr + g)]
        clash = lambda b: sum(hit(b, c, rad) for c, rad in discs) + \
            sum(b[0] < t[2] and t[0] < b[2] and b[1] < t[3] and t[1] < b[3] for t in taken) + \
            (b[0] < 0 or b[2] > im.width or b[1] < 0 or b[3] > KEY[1])
        box = min(((bx, by, bx + w, by + h) for bx, by in spots), key=lambda b: (clash(b), spots.index((b[0], b[1]))))
        taken.append(box)
        if math.dist(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), (x, y)) > w / 2 + h:
            d.line([(x, y), (max(box[0], min(x, box[2])), max(box[1], min(y, box[3])))], fill=(255, 255, 255, 255), width=4)
        d.rounded_rectangle(box, 8, fill=(255, 255, 255, 230), outline=COLOURS[r] + (255,), width=3)
        d.text((box[0] + 12, box[1] + 5), name, font=mid, fill=(30, 30, 30))
    for p, text, col in ((home, 'HOME', (210, 40, 40)), (school, 'SCHOOL', (40, 90, 210))):
        x, y = inv(p)
        d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (255,), outline=(255, 255, 255, 255), width=6)
        tw = d.textlength(text, font=big)
        d.rounded_rectangle([x - tw / 2 - 14, y - 98, x + tw / 2 + 14, y - 38], 12, fill=col + (240,))
        d.text((x - tw / 2, y - 92), text, font=big, fill=(255, 255, 255))
    # the key, in the sea
    kx, ky = KEY
    d.rounded_rectangle([kx, ky, kx + 1820, ky + 70], 18, fill=(255, 255, 255, 225))
    d.text((kx + 20, ky + 14), 'Kamakura:', font=big, fill=(30, 30, 30))
    x = kx + 300
    for r in ('KM1', 'KM2', 'KM3'):
        n = sum(1 for l in LEGS if LEGS[l][0] == r)
        d.line([(x, ky + 36), (x + 70, ky + 36)], fill=COLOURS[r] + (255,), width=16)
        t = '%s %s (%d)' % (r, NAMES[r], n)
        d.text((x + 84, ky + 20), t, font=mid, fill=(30, 30, 30))
        x += 84 + d.textlength(t, font=mid) + 50
    d.text((x - 20, ky + 20), '- - - the tram', font=mid, fill=(30, 30, 30))
    im.save(out_png)


def layout(routes, stops, nodes, home, school):
    r2 = lambda p: {'x': round(p[0]), 'y': round(p[1])}
    return {
        'image': 'UI/KamakuraMap', 'width': GAME_W, 'height': GAME_H,
        'core': {'x': CORE[0], 'y': CORE[1], 'w': CORE[2], 'h': CORE[3]},
        'source': {'picture': 'review/kamakura/refs/KM-MAP2_clean.png', 'scale': K, 'offset': [round(OFF[0], 1), OFF[1]],
                   'note': 'game = offset + scale * map pixel; the ring outside the map comes from MAP KM-MAP3'},
        'places': [dict(id='home', **r2(home)), dict(id='school', **r2(school))],
        'routes': [{'id': r, 'points': [r2(p) for p in dense(pts, 40.0)] + [r2(pts[-1])]} for r, pts in routes.items()],
        'nodes': [dict(id=l, label=LABEL[l], **r2(p)) for l, p in nodes.items()],
        'districts': [dict(id=i, **r2(game(p))) for i, p in DISTRICTS],
        'streets': [{'name': n, **r2(game(p)), 'angle': a} for n, p, a in STREETS],
        'stops': [dict(id=sid, route=r, **r2(p)) for sid, (r, name, p) in stops.items()],
        'rides': [{'route': r, 'from': a, 'to': b} for r, a, b in RIDES],
        'placeholder': False,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    routes, stops, nodes, home, school, own = plan()
    ok, lines = checks(routes, stops, nodes, home, school, own)
    stats = ['%s: %d px in the game (%d on the map)' % (r, length(p), length(ROUTES[r])) for r, p in routes.items()]
    text = '\n'.join(stats + [''] + lines) + '\n'
    open(os.path.join(OUT, 'checks.txt'), 'w').write(text)
    print(text)
    json.dump(layout(routes, stops, nodes, home, school), open(os.path.join(OUT, 'KamakuraMapLayout.json'), 'w'), indent=1)
    draw(routes, stops, nodes, home, school, os.path.join(OUT, 'KM-MAP3_plan_game.png'))
    print('wrote', OUT)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
