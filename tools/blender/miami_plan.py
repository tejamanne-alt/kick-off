"""Florida's districts: what stands along each of Florida's own legs (docs/CITIES.md, FL1 to FL3), written once as data that
both the game's builder (Editor/StreetBuilder.Miami.cs) and the preview (preview_street.py --miami) read, so the preview is
the game. Pure Python: it reads the legs' layouts from Editor/FloridaLevels.cs (their walls, goals, drawbridges, arcades) and
writes Assets/_Game/Art/Models/Miami/MiamiDistricts.json.

    python3 tools/blender/miami_plan.py            (deterministic: the same layouts give the same file)

Game axes: x along the street, z away from the camera (the kid's lane is z -1.5 to 1.5; shopfronts at about 1.85), yaw in
degrees as Unity turns a model (0 faces the camera). Nothing taller than about 0.4 m stands in front of the lane (LEARNINGS
E10): every building, tree and pole here is behind it.

The districts, as a child walking to school in Miami would see them:
  littleHavana  FL1-1   one- and two-storey shops of Calle Ocho (the walk-up café, the cigar shop, the fruit shop, mural
                        walls), ranch houses near home, the domino park, royal palms, wooden poles, and downtown's towers far off
  brickell      FL1-2   tower podiums with their valet canopies under glass condo towers, a construction site with its crane,
                        a coffee kiosk, royal palms in grates; the skyline crowding the sky
  bayfront      FL1-3   a promenade by the bay: its balustrade, pelicans on their pilings, the water, a tug, a cruise ship far
                        off and the towers across the water; the school on its own land at the end
  riverwalk     FL2-2   the Riverwalk: its rail and bollards, coiled lines, freighters moored along it, towers across the river
  downtown      FL2-3   old downtown: Art Deco and Mediterranean Revival blocks with arcades, the pharmacy, the skyline
  underline     FL3-1   the linear park under the elevated railway: the guideway overhead on its painted piers, fitness bars,
                        palms and planting, Little Havana's houses behind
  biscayne      FL3-2   the boulevard: royal palms, tower podiums, the Spanish-style tower, the people mover's guideway
  museumPark    FL3-3   the park by the bay: banyans, lawns, the museum under its hanging gardens, the bay behind; the school
FL2-1 is Riverside Street (riverside). The mini-game legs (the Metrobus, Uncle Rey's boat, the drugstore) and their districts
were removed in v128; the legs after them took their numbers.
"""
import json, math, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
LAYOUTS = os.path.join(REPO, 'Assets/_Game/Scripts/Editor/FloridaLevels.cs')
OUT = os.path.join(REPO, 'Assets/_Game/Art/Models/Miami/MiamiDistricts.json')

# Nothing that stands behind the lane may reach forward over the ball's plane (z 0) above the ground: a Deco block's canvas
# arcade (3 m deep) placed with its front wall at 2.35 hung 0.7 m in front of the ball, and the ball flew up through it with no
# collider to stop it (docs/LEARNINGS.md E17). Such a model is pushed back until its front edge is LANE_CLEAR behind the ball.
# The game's builder applies the same rule to every street model (StreetBuilder.ClearOfTheBall).
LANE_CLEAR = 0.45
# How far back a side street runs (StreetBuilder.CrossingStreet: to z 70), and a little more.
SIDE_STREET_END = 72.0
_MANIFESTS = {}


def _model_info(kit, model):
    if kit not in _MANIFESTS:
        path = os.path.join(REPO, 'Assets/_Game/Art/Models', kit, kit + '.json')
        try:
            _MANIFESTS[kit] = json.load(open(path)).get('models', {})
        except (OSError, ValueError):
            _MANIFESTS[kit] = {}
    return _MANIFESTS[kit].get(model)


def street_halves(kit, model, scale, yaw):
    """Half a model's footprint along the street and across it, turned as it stands (StreetBuilder.InSideStreet the same)."""
    info = _model_info(kit, model)
    if not info or 'size' not in info: return 1.0, 1.0
    a = math.radians(yaw)
    c, s = abs(math.cos(a)), abs(math.sin(a))
    w, d = info['size'][0] * scale, info['size'][1] * scale
    return max((c * w + s * d) / 2, 0.5), max((s * w + c * d) / 2, 0.5)


def clear_of_the_ball(kit, model, z, yaw, scale):
    """z, pushed back if the model (standing behind the lane) would reach over the ball's plane above 1.2 m."""
    if kit in ('Plants', 'Animals', 'Terrain') or z < 0.6:
        return z
    info = _model_info(kit, model)
    if not info or 'min' not in info or info['max'][2] * scale < 1.2:
        return z
    a = math.radians(yaw)
    # the footprint's corners (x across, forward = -y in the manifest's Blender axes), turned as Unity turns the model
    xs = (info['min'][0] * scale, info['max'][0] * scale)
    fs = (info['min'][1] * scale, info['max'][1] * scale)
    front = min(-x * math.sin(a) + f * math.cos(a) for x in xs for f in fs)
    if z + front < LANE_CLEAR:
        z = LANE_CLEAR - front
    return z

LEAD_IN = 12.0                       # HomeLeadInRules.Length: a leg starts 12 m before its own street, at its stop's door
STOP_PLOT = (-4.6 - 0.6, 7.6 + 0.6)  # StreetBuilder.StopPlot (and a margin), round a stop's door
HOME_PLOT = (-5.6 - 0.6, 7.8 + 0.6)  # StreetBuilder.HomePlotFL
SCHOOL_PLOT = (-8.0, 60.0)           # LevelBuildKit.FloridaSchool: the gate a little before the goal, the grounds after it
PROPERTY_Z, POLE_Z = 1.85, 1.55      # StreetBuilder.PropertyZ, PoleZ
WATER_Z, WATER_Y = 4.6, -0.9         # where the promenade's seawall stands, and the water's surface
STRIP_BACK = 90.0                    # StreetBuilder.BackZ: how far back a street's own strips run (a plan's 'back' can say less)
# v142: the ground reaches the horizon (the camera sees 2,500 m: LevelBuildKit's farClipPlane, 34 degrees high, about 2.2
# wide on a phone) so no tower stands on the sky: everything from the strips' back to FAR_Z, and SIDE either side of the leg,
# is land or water.
FAR_Z, SIDE = 2400.0, 1700.0
CITY_Z0, CITY_Z1 = 200.0, 650.0      # the band of low city blocks behind every street (Plan.city)

# leg id -> (layout method, district, strips, starts at home, ends at school)
LEGS = {
    'FL1-1': ('LittleHavana', 'littleHavana', 'havana', True, False),
    'FL1-2': ('BrickellAvenue', 'brickell', 'street', False, False),
    'FL1-3': ('Bayfront', 'bayfront', 'promenade', False, True),
    'FL2-1': ('RiversideStreet', 'riverside', 'havana', True, False),
    'FL2-2': ('Riverwalk', 'riverwalk', 'promenade', False, False),
    'FL2-3': ('Downpour', 'downtown', 'street', False, True),
    'FL3-1': ('Underline', 'underline', 'havana', True, False),
    'FL3-2': ('BiscayneBoulevard', 'biscayne', 'street', False, False),
    'FL3-3': ('MuseumPark', 'museumPark', 'park', False, True),
}
# The legs renumbered in v128 keep the streets they were reviewed with: each district's random draw is seeded by its id before.
SEED_ID = {'FL1-2': 'FL1-3', 'FL1-3': 'FL1-4', 'FL2-2': 'FL2-3', 'FL2-3': 'FL2-5'}


# ---------------------------------------------------------------- reading the layouts
def methods(src):
    for m in re.finditer(r'public static void (\w+)\(TrackBuilder t\)\s*\{', src):
        i, depth = m.end(), 1
        while depth:
            depth += {'{': 1, '}': -1}.get(src[i], 0)
            i += 1
        yield m.group(1), src[m.end():i - 1]


def calls(body, name):
    out = []
    for m in re.finditer(r'\bt\.' + name + r'\(([^;]*)\);', body):
        nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?(?=f\b)', m.group(1))]
        out.append(nums)
    return out


def leg_info(src):
    bodies = dict(methods(src))
    info = {}
    for leg, (method, district, strips, home, school) in LEGS.items():
        b = bodies[method]
        walls = calls(b, 'Walls')[0]
        goal = calls(b, 'Goal')[0][0] if calls(b, 'Goal') else walls[1] - 4.0
        lead = LEAD_IN
        info[leg] = dict(
            district=district, strips=strips, home=home, school=school,
            minX=walls[0] - lead, maxX=walls[1], start=-lead, goal=goal,
            canals=[(c[0], c[1]) for c in calls(b, 'Drawbridge')],
            # the side streets that cross the lane (LevelBuildKit.Crossing opens fromX - 0.8 to toX + 0.8)
            crossings=[(c[0] - 0.8, c[1] + 0.8) for c in calls(b, 'Crossing')],
            arcades=[(c[0], c[1]) for c in calls(b, 'Arcade')])
    return info


# ---------------------------------------------------------------- the plan of one leg
class Plan:
    def __init__(self, leg, li):
        self.leg, self.li = leg, li
        self.items = []
        seed = SEED_ID.get(leg, leg)
        self.rng = random.Random(sum(ord(c) * (i + 7) for i, c in enumerate(seed)))
        self.x0, self.x1 = li['minX'] - 50.0, li['maxX'] + 50.0
        # where the front row keeps out: the stops' plots (or home's), the school, the canals and the arcades (whose buildings
        # the arcades place themselves)
        s = li['start']
        self.keep_out = [(s + (HOME_PLOT if li['home'] else STOP_PLOT)[0], s + (HOME_PLOT if li['home'] else STOP_PLOT)[1])]
        g = li['goal']
        self.keep_out.append((g + SCHOOL_PLOT[0], g + SCHOOL_PLOT[1]) if li['school'] else (g + STOP_PLOT[0], g + STOP_PLOT[1]))
        self.canals = [(a - 3.0, b + 3.0) for a, b in li['canals']]
        self.keep_out += self.canals
        self.keep_out += [((a + b) / 2 - 5.5, (a + b) / 2 + 5.5) for a, b in li['arcades']]     # the 10 m Deco block (LevelBuildKit.Arcade)
        # The side streets: nothing of the district stands in one, from the lane back to its end (v139: a kiosk and a tower's
        # podium stood across Biscayne Boulevard's; StreetBuilder.Miami leaves out anything that still would).
        self.streets = [(a - 0.3, b + 0.3) for a, b in li['crossings']]
        self.keep_out += self.streets
        self.water = None
        self.back = None     # where the street's own strips end, when not StreetBuilder.BackZ (a basin or river behind)
        self.fill = 'Grass'  # the ground the plan lays out to the horizon behind everything else
        self.land = []
        self.boxes = []      # built shapes (the port's quay, cranes, gate and containers): game and preview build the same
        self.labels = []
        self.gap_trees = ['PalmRoyal', 'PalmRoyal', 'PalmSabalTall']

    def put(self, kit, model, x, z, yaw=0.0, scale=1.0, y=None):
        if x < self.x0 or x > self.x1: return
        z = clear_of_the_ball(kit, model, z, yaw, scale)
        if self.in_street(kit, model, x, z, scale, yaw): return
        it = [kit, model, round(x, 3), round(z, 3), round(yaw, 1), round(scale, 3)]
        if y is not None: it.append(round(y, 3))
        self.items.append(it)

    def in_street(self, kit, model, x, z, scale, yaw=0.0):
        """Would this model, at x and depth z, stand in a side street (as StreetBuilder.InSideStreet decides)? Its footprint
        turned as it stands (v140: a freighter moored along the port's quay, end on to the street, is 7 m wide, not 30)."""
        if not self.streets: return False
        hx, hz = street_halves(kit, model, scale, yaw)
        if z - hz > SIDE_STREET_END: return False
        return any(x + hx > a - 0.3 and x - hx < b + 0.3 for a, b in self.streets)

    def free(self, a, b, deep=False):
        """Is [a, b] clear of the stops, the school, the canals and the arcades (deep rows: only of the canals)?"""
        for lo, hi in (self.canals if deep else self.keep_out):
            if b > lo and a < hi: return False
        return True

    def r(self, a, b): return self.rng.uniform(a, b)

    def deck(self, names):
        """A shuffled deck: each in turn, never the same twice running, reshuffled when it runs out."""
        pool = []
        last = [None]
        def draw():
            if not pool:
                pool.extend(names); self.rng.shuffle(pool)
                if pool[-1] == last[0] and len(pool) > 1: pool[0], pool[-1] = pool[-1], pool[0]
            last[0] = pool.pop()
            return last[0]
        return draw

    # ---- rows
    def front_row(self, deck, z, widths, gap=(0.6, 2.4), extras=None, x_from=None, x_to=None):
        x = self.x0 if x_from is None else x_from
        end = self.x1 if x_to is None else x_to
        while x < end:
            kit, model = deck()
            w = widths[model]
            if not self.free(x, x + w):
                # step past the obstacle it hit
                x = next((hi for lo, hi in self.keep_out if x + w > lo and x < hi), x + 1.0) + 0.3
                continue
            self.put(kit, model, x + w / 2, z, 0.0)
            if extras: extras(x, x + w)
            g = self.r(*gap)
            if self.gap_trees and g >= 1.1 and self.free(x + w, x + w + g):
                self.put('Plants', self.rng.choice(self.gap_trees), x + w + g / 2, max(2.5, z + 0.4), self.r(0, 360), self.r(0.8, 1.05))
            x += w + g

    def street_things(self, things, step=(5.0, 9.0), z=POLE_Z, skip_canals=True):
        x = self.x0 + self.r(0, 4)
        while x < self.x1:
            kit, model, dz = things(x)
            if model and self.free(x - 0.6, x + 0.6) or (model and not skip_canals):
                self.put(kit, model, x, z + dz, self.r(-6, 6) if model.startswith('Palm') else 0.0, self.r(0.85, 1.1) if model.startswith('Palm') else 1.0)
            x += self.r(*step)

    def deep_row(self, models, z0, z1, step=(10.0, 22.0), scale=(0.9, 1.1), x_from=None, x_to=None):
        x = (self.x0 if x_from is None else x_from) + self.r(0, 10)
        while x < (self.x1 if x_to is None else x_to):
            kit, model, w = models[self.rng.randrange(len(models))]
            if self.free(x - w / 2, x + w / 2, deep=True):
                self.put(kit, model, x, self.r(z0, z1), 0.0, self.r(*scale))
            x += max(w * 0.8, self.r(*step))

    def skyline(self, z0, z1, n_per_100=4, scale=(0.9, 1.25), kinds=None):
        kinds = kinds or [('Miami', 'CondoTowerMIA'), ('Miami', 'OfficeTowerMIA'), ('Miami', 'CondoTower2MIA'), ('Miami', 'CondoTowerMIA')]
        x = self.x0 - 40
        while x < self.x1 + 40:
            kit, model = kinds[self.rng.randrange(len(kinds))]
            self.put(kit, model, x, self.r(z0, z1), self.r(-8, 8), self.r(*scale))
            x += 100.0 / n_per_100 * self.r(0.6, 1.4)

    def palms(self, z0, z1, step=(7.0, 12.0), model='PalmRoyal', scale=(0.85, 1.1)):
        x = self.x0 + self.r(0, 5)
        while x < self.x1:
            if self.free(x - 1, x + 1, deep=True):
                self.put('Plants', model, x, self.r(z0, z1), self.r(0, 360), self.r(*scale))
            x += self.r(*step)

    def ibises(self, z0, z1, n_per_100=4):
        """White ibises probing the lawns (Miami's everyday bird), in little groups."""
        x = self.x0 + self.r(5, 30)
        while x < self.x1:
            for k in range(self.rng.randrange(1, 4)):
                xx = x + self.r(-1.5, 1.5)
                if self.free(xx - 0.4, xx + 0.4):
                    self.put('Miami', 'IbisMIA', xx, self.r(z0, z1), self.r(0, 360))
            x += 100.0 / n_per_100 * self.r(0.6, 1.4)

    def far_shore(self, z0, z1=None):
        """The barrier island across the bay (Miami Beach), under its towers, out to the horizon (v142: it was a strip 0.9 m
        over the water, a hairline from the street, and its towers stood on the water): its seawall's face, and a waterfront
        of low buildings and palms along it, so the towers rise from a city."""
        self.land.append({'from': round(self.x0 - SIDE, 2), 'to': round(self.x1 + SIDE, 2), 'z0': z0, 'z1': FAR_Z})
        self.box('ShoreWall', self.x0 - SIDE, self.x1 + SIDE, WATER_Y - 0.4, 0.0, z0 - 0.6, z0, (0.8, 0.78, 0.74), 'Concrete')
        x = self.x0 - 900
        while x < self.x1 + 900:
            w = self.r(18, 46)
            h = self.r(7, 24) if self.rng.random() < 0.8 else self.r(26, 40)
            d = self.r(12, 22)
            self.box('Waterfront', x, x + w, 0.0, h, z0 + 4.0, z0 + 4.0 + d, self.rng.choice(SHORE_COLOURS))
            x += w + self.r(4, 16)

    def plazas(self):
        """A paved plaza under each tower standing out on the plan's own ground (v142: they stood on bare lawn)."""
        for it in self.items:
            if len(it) > 6 or it[1] not in TOWERS: continue
            x, z, sc = it[2], it[3], it[5]
            if z < self.strip_back() + 2: continue
            info = _model_info(it[0], it[1])
            half = info['size'][0] * sc / 2 + 6.0
            self.box('Plaza', x - half, x + half, -0.05, 0.03, z - 1.4 * sc - 6.0, z + info['max'][1] * sc + 6.0, (0.84, 0.83, 0.8), 'Concrete')

    def city(self, z0=CITY_Z0, z1=CITY_Z1):
        """The city between the street and its skyline (v142: the towers stood alone on a lawn): rows of low blocks, 5 to 24 m,
        with streets between, on the plan's own ground only (never in the water, the port or a park the district laid), clear
        of the towers' plazas, across the width the camera sees at each distance. Plain boxes: from 200 m back they read as
        a city's roofs and walls in the haze."""
        fills = [l for l in self.land if l.get('fill')]
        plazas = [(b['c'][0] - b['s'][0] / 2 - 4, b['c'][0] + b['s'][0] / 2 + 4, b['c'][2] - b['s'][2] / 2 - 4, b['c'][2] + b['s'][2] / 2 + 4)
                  for b in self.boxes if b['n'] == 'Plaza']
        def ok(a, b, c, d):
            if not any(l['from'] <= a and b <= l['to'] and l['z0'] <= c and d <= l['z1'] for l in fills): return False
            return not any(b > p0 and a < p1 and d > q0 and c < q1 for p0, p1, q0, q1 in plazas)
        z = max(z0, self.strip_back() + 40.0)
        while z < z1:
            depth = self.r(16, 30) if z < 300 else self.r(24, 45)
            half = 0.7 * (z + 10.0)
            x = self.x0 - half + self.r(0, 20)
            while x < self.x1 + half:
                w = self.r(22, 55) if z < 300 else self.r(35, 80)
                # (low in front, so from the street they are distant roofs over the houses, not walls)
                h = self.r(5, 11) if z < 300 else (self.r(6, 16) if self.rng.random() < 0.75 else self.r(16, 24))
                if ok(x, x + w, z, z + depth):
                    self.box('Block', x, x + w, 0.0, h, z, z + depth, self.rng.choice(SHORE_COLOURS))
                x += w + self.r(8, 20)
            z += depth + (self.r(10, 18) if z < 300 else self.r(18, 40))

    def strip_back(self):
        """Where the street's own strips end (StreetBuilder.MiamiStrips)."""
        if self.back is not None: return self.back
        kind = self.li['strips']
        if kind == 'promenade' and self.water: return self.water['z']
        if kind == 'park' and self.water: return min(self.water['z'], STRIP_BACK)
        return STRIP_BACK

    def ground(self):
        """The ground out to the horizon (v142): the water out to the horizon and to the sides where it reaches the leg's ends,
        then land on everything that is neither water nor land already, from the strips' back to FAR_Z and SIDE either side."""
        X0, X1 = self.x0 - SIDE, self.x1 + SIDE
        rects = [(l['from'], l['to'], l['z0'], l['z1']) for l in self.land]
        if self.water:
            w = self.water
            if w['from'] <= self.x0 + 0.5: w['from'] = round(X0, 2)
            if w['to'] >= self.x1 - 0.5: w['to'] = round(X1, 2)
            w.setdefault('z1', FAR_Z)
            rects.append((w['from'], w['to'], w['z'], w['z1']))
        zb = self.strip_back()
        xs = sorted(set([X0, X1] + [v for r in rects for v in r[:2] if X0 < v < X1]))
        zs = sorted(set([zb, FAR_Z] + [v for r in rects for v in r[2:] if zb < v < FAR_Z]))
        free = {}
        for i in range(len(xs) - 1):
            for j in range(len(zs) - 1):
                cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
                free[i, j] = not any(a <= cx <= b and c <= cz <= d for a, b, c, d in rects)
        # merge: runs along x in each row, then rows with the same run stacked
        runs = {}
        for j in range(len(zs) - 1):
            i = 0
            while i < len(xs) - 1:
                if not free[i, j]: i += 1; continue
                k = i
                while k + 1 < len(xs) - 1 and free[k + 1, j]: k += 1
                runs.setdefault((xs[i], xs[k + 1]), []).append(j)
                i = k + 1
        for (a, b), rows in runs.items():
            rows.sort()
            start = prev = rows[0]
            for j in rows[1:] + [None]:
                if j is not None and j == prev + 1: prev = j; continue
                l = {'from': round(a, 2), 'to': round(b, 2), 'z0': round(zs[start], 2), 'z1': round(zs[prev + 1], 2), 'fill': True}
                if self.fill != 'Grass': l['surface'] = self.fill
                self.land.append(l)
                if j is not None: start = prev = j
        # nothing grounded stands in the water unless it is on land there
        kept, dropped = [], []
        for it in self.items:
            if len(it) <= 6 and self.wet(it[2], it[3]): dropped.append(it[1])
            else: kept.append(it)
        self.items = kept
        return dropped

    def wet(self, x, z):
        """Is (x, z) open water (no land drawn over it)?"""
        w = self.water
        if not w or not (w['from'] <= x <= w['to'] and w['z'] + 0.2 < z < w.get('z1', FAR_Z)): return False
        return not any(l['from'] <= x <= l['to'] and l['z0'] <= z <= l['z1'] for l in self.land)

    def set_water(self, z=WATER_Z, until=None, start=None, z1=None):
        a = self.x0 if start is None else start
        b = self.x1 if until is None else until
        self.water = {'from': round(a, 2), 'to': round(b, 2), 'z': z, 'y': WATER_Y}
        if z1 is not None: self.water['z1'] = z1

    def to_json(self):
        li = self.li
        d = {'district': li['district'], 'strips': li['strips'], 'items': self.items}
        if self.water: d['water'] = self.water
        if self.back is not None: d['back'] = self.back
        if self.land: d['land'] = self.land
        if self.boxes: d['boxes'] = self.boxes
        if self.labels: d['labels'] = self.labels
        return d

    def box(self, name, x0, x1, y0, y1, z0, z1, rgb, surface=None, rz=0.0):
        """A built shape from (x0, y0, z0) to (x1, y1, z1) in game axes, turned rz degrees round the z axis about its middle."""
        b = {'n': name, 'c': [round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round((z0 + z1) / 2, 3)],
             's': [round(abs(x1 - x0), 3), round(abs(y1 - y0), 3), round(abs(z1 - z0), 3)], 'rgb': [round(v, 3) for v in rgb]}
        if surface: b['surf'] = surface
        if rz: b['rz'] = round(rz, 2)
        self.boxes.append(b)

    def beam(self, name, x0, y0, x1, y1, z, thick, rgb):
        """A straight member from (x0, y0) to (x1, y1) at depth z: a stay, a brace."""
        length = math.hypot(x1 - x0, y1 - y0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.box(name, cx - length / 2, cx + length / 2, cy - thick / 2, cy + thick / 2, z - thick / 2, z + thick / 2, rgb,
                 rz=math.degrees(math.atan2(y1 - y0, x1 - x0)))


W = {   # the front row's widths along the street (the models' own, with their eaves and awnings)
    'VentanitaMIA': 9.4, 'TabaqueriaMIA': 8.2, 'FruteriaMIA': 8.6, 'MuralWallMIA': 10.4, 'MuralShedMIA': 12.2, 'DominoParkMIA': 9.2,
    'PharmacyMIA': 11.2, 'MedRevivalMIA': 15.0, 'DecoArcadeMIA': 12.1, 'DecoArcade2MIA': 10.1, 'TowerPodiumMIA': 24.2,
    'SiteFenceMIA': 8.4, 'RanchFL': 12.4, 'RanchSmallFL': 8.8, 'CottageFL': 8.4, 'MuseumMIA': 46.0,
    'DecoCafeFL': 6.5, 'DecoShutFL': 7.2, 'DecoIceFL': 8.3, 'DecoBaitFL': 6.5,
}


def kit_of(model):
    if model.endswith('MIA'): return 'Miami'
    if model.endswith('FL'): return 'Florida'
    return 'Plants'


def make_deck(plan, names):
    d = plan.deck(names)
    def draw():
        n = d()
        return kit_of(n), n
    return draw


# ---------------------------------------------------------------- the districts
def havana_things(plan):
    """Calle Ocho's kerb: wooden utility poles, royal palms and sabals in their grates, lamps, a hydrant, bins, a fruit cart."""
    k = [0]
    def f(x):
        k[0] += 1
        c = k[0] % 6
        if c == 0: return ('Street', 'UtilityPoleWood', 0.05)
        if c in (1, 4): return ('Plants', 'PalmRoyal' if plan.rng.random() < 0.6 else 'PalmSabalTall', -0.6)
        if c == 2: return ('Florida', 'LampFL', 0.0)
        if c == 3: return ('Florida', plan.rng.choice(['HydrantFL', 'TrashFL', 'MailboxFL']), 0.1)
        return ('Miami', 'FruitCartMIA', 0.55) if plan.rng.random() < 0.4 else ('Florida', 'BenchFL', 0.4)
    return f


def little_havana(plan, x_to=None, x_from=None):
    li = plan.li
    # near home: ranch houses (Little Havana's side streets), then Calle Ocho's shops
    shops_from = (li['start'] + 26.0) if li['home'] else plan.x0
    houses = make_deck(plan, ['RanchFL', 'RanchSmallFL', 'CottageFL'])
    if li['home']:
        plan.front_row(houses, PROPERTY_Z + 2.6, W, gap=(2.0, 4.0), x_from=plan.x0 if x_from is None else x_from, x_to=shops_from)
    shops = make_deck(plan, ['VentanitaMIA', 'TabaqueriaMIA', 'FruteriaMIA', 'MuralWallMIA', 'TabaqueriaMIA', 'DominoParkMIA', 'MuralShedMIA'])
    plan.front_row(shops, PROPERTY_Z + 0.45, W, gap=(0.3, 2.6), x_from=max(shops_from, plan.x0 if x_from is None else x_from),
                   x_to=x_to)
    plan.street_things(havana_things(plan), step=(4.5, 8.0))
    # behind: a second row of low buildings and yards, mango and live oak trees, sabals; Brickell's towers far off
    plan.deep_row([('Florida', 'RanchFL', 12), ('Miami', 'MuralShedMIA', 12), ('Miami', 'TabaqueriaMIA', 8), ('Florida', 'CottageFL', 8)], 17, 22)
    plan.deep_row([('Plants', 'LiveOak', 10), ('Plants', 'Banyan', 12), ('Plants', 'PalmSabalTall', 4), ('Plants', 'PalmRoyal', 4)], 11, 15,
                  step=(6, 12))
    plan.deep_row([('Florida', 'RanchFL', 12), ('Florida', 'RanchSmallFL', 9), ('Plants', 'LiveOak', 10)], 34, 46, step=(9, 16))
    plan.palms(26, 40, step=(9, 18), model='PalmSabalTall')
    plan.ibises(3.2, 5.5, n_per_100=2)
    plan.skyline(380, 520, n_per_100=2, scale=(1.0, 1.3))


def brickell(plan, x_from=None, x_to=None):
    li = plan.li
    def extras(a, b):
        pass
    fronts = make_deck(plan, ['TowerPodiumMIA', 'SiteFenceMIA', 'TowerPodiumMIA', 'MedRevivalMIA', 'TowerPodiumMIA', 'SiteFenceMIA'])
    x = plan.x0 if x_from is None else x_from
    end = plan.x1 if x_to is None else x_to
    while x < end:
        kit, m = fronts()
        if m == 'SiteFenceMIA':
            # a construction site: two fence sections, the tower crane behind, the half-built tower's frame
            w = 17.0
            if plan.free(x, x + w):
                plan.put('Miami', 'SiteFenceMIA', x + 4.2, PROPERTY_Z + 0.6)
                plan.put('Miami', 'SiteFenceMIA', x + 12.6, PROPERTY_Z + 0.6)
                plan.put('Miami', 'CraneMIA', x + 9.0, 18.0, 0.0, 1.0)
                plan.put('Miami', 'CondoTower2MIA', x + 8.5, 16.0, 0.0, 0.55)
                x += w + plan.r(0.5, 2)
                continue
        w = W[m]
        if not plan.free(x, x + w):
            x = next((hi for lo, hi in plan.keep_out if x + w > lo and x < hi), x + 1.0) + 0.3
            continue
        plan.put(kit, m, x + w / 2, PROPERTY_Z + (0.5 if m != 'TowerPodiumMIA' else 3.8))
        if m == 'TowerPodiumMIA':
            plan.put('Miami', plan.rng.choice(['CondoTowerMIA', 'OfficeTowerMIA', 'CondoTower2MIA']), x + w / 2, 15.0, 0.0, plan.r(0.95, 1.1))
            forecourt(plan, x, w)
        g = plan.r(1.4, 3.4)
        if plan.free(x + w, x + w + g):
            plan.put('Plants', 'PalmRoyal', x + w + g / 2, 2.6, plan.r(0, 360), plan.r(0.9, 1.05))
            if plan.rng.random() < 0.35: plan.put('Miami', 'CoffeeKioskMIA', x + w + g / 2 + 0.2, 3.4)
        x += w + g
    def things(xx):
        c = plan.rng.random()
        if c < 0.55: return ('Florida', 'LampFL', 0.0)
        if c < 0.8: return ('Miami', 'ScooterUpMIA', 0.3)
        if c < 0.9: return ('Florida', 'BenchFL', 0.4)
        return ('Florida', 'TrashFL', 0.1)
    plan.street_things(things, step=(5.0, 9.0))
    plan.skyline(60, 120, n_per_100=6, scale=(0.9, 1.2))
    plan.skyline(150, 260, n_per_100=5, scale=(1.0, 1.4))


def forecourt(plan, x, w):
    """A tower's forecourt between the sidewalk and its glass lobby: royal palms in their planters at the corners, a bench,
    now and then a coffee kiosk or a fruit cart, a valet's scooter."""
    for px in (x + 2.2, x + w - 2.2):
        plan.put('Plants', 'PalmRoyal', px, PROPERTY_Z + 1.6, plan.r(0, 360), plan.r(0.85, 1.0))
    c = plan.rng.random()
    if c < 0.35: plan.put('Miami', 'CoffeeKioskMIA', x + w / 2 + plan.r(-3, 3), PROPERTY_Z + 1.5)
    elif c < 0.6: plan.put('Miami', 'FruitCartMIA', x + w / 2 + plan.r(-3, 3), PROPERTY_Z + 1.4)
    else: plan.put('Florida', 'BenchFL', x + w / 2 + plan.r(-3, 3), PROPERTY_Z + 1.2)
    if plan.rng.random() < 0.5: plan.put('Miami', 'ScooterUpMIA', x + plan.r(4, w - 4), PROPERTY_Z + 0.3, plan.r(-20, 20))


def bayfront(plan):
    li = plan.li
    goal = li['goal']
    land_from = goal - 26.0 if li['school'] else plan.x1
    # A side street runs back from the lane on land, never into the bay (v139: Bayfront's crossing came out of the water, and
    # the school's lawn covered its road): the land starts 4 m before the first crossing.
    for a, b in li['crossings']:
        land_from = min(land_from, a - 4.0)
    plan.set_water(until=land_from)
    if li['crossings']:
        # The side street leads into the port (v140: on land it still read as a road out of the bay): its gate across the
        # street's far end, the quay along the water's edge beside it, cranes, ships alongside, the container yard.
        port(plan, land_from, li['crossings'][0], WATER_Z)
    elif li['school']:
        plan.land.append({'from': round(land_from, 2), 'to': round(plan.x1 + 60, 2), 'z0': WATER_Z - 0.4, 'z1': 120.0})
    x = plan.x0
    while x < land_from:
        if plan.free(x, x + 4.0, deep=True):
            plan.put('Miami', 'BayRailMIA', x + 2.0, WATER_Z - 0.35)
        x += 4.0
    x = plan.x0 + 3
    while x < land_from - 2:
        if plan.free(x - 1, x + 1, deep=True):
            plan.put('Miami', 'PelicanPostMIA', x, WATER_Z + 0.6, plan.r(-30, 30), 1.0, y=WATER_Y + 0.5)
        x += plan.r(9, 16)
    plan.palms(2.4, 3.4, step=(11.0, 17.0))
    # on the water: a tug, a moored freighter far, the cruise ship; across the bay the barrier islands' towers
    plan.put('Miami', 'TugMIA', plan.x0 + plan.r(40, 80), 45.0, 180.0, 1.0, y=WATER_Y + 0.3)
    # (the cruise ship clear of the land beside the bay: v142's ground reaches the horizon there)
    plan.put('Miami', 'CruiseShipMIA', min((plan.x0 + plan.x1) / 2 + plan.r(-30, 30), land_from - 75.0), 340.0, 0.0, 1.0, y=WATER_Y)
    plan.put('Miami', 'FreighterMIA', plan.x0 + plan.r(10, 40), 120.0, 0.0, 1.0, y=WATER_Y + 0.2)
    plan.skyline(725, 900, n_per_100=5, scale=(0.8, 1.2))
    plan.far_shore(690)
    if li['school']:
        # (on the school's land only: the bay is open water)
        plan.deep_row([('Plants', 'PalmRoyal', 4), ('Plants', 'LiveOak', 10)], 30, 50, step=(6, 10), x_from=land_from + 2.0)


TOWERS = {'CondoTowerMIA', 'CondoTower2MIA', 'OfficeTowerMIA', 'SpanishTowerMIA'}
SHORE_COLOURS = [(0.95, 0.94, 0.9), (0.93, 0.88, 0.78), (0.94, 0.82, 0.8), (0.78, 0.86, 0.9), (0.86, 0.9, 0.84), (0.9, 0.9, 0.92)]
PORT_GATE_Z = 62.0           # the port's fence and gate, across the side street before its end (StreetBuilder: z 70)
PORT_BACK_Z = 150.0          # the yard's far side
PORT_CRANE_RED, PORT_WHITE = (0.78, 0.2, 0.15), (0.92, 0.92, 0.89)
CONTAINER_COLOURS = [(0.16, 0.4, 0.68), (0.72, 0.2, 0.15), (0.2, 0.48, 0.32), (0.88, 0.52, 0.16), (0.56, 0.58, 0.6),
                     (0.9, 0.9, 0.87), (0.1, 0.52, 0.58), (0.52, 0.26, 0.16), (0.92, 0.78, 0.22), (0.2, 0.22, 0.4)]


def port(plan, quay, crossing, front=WATER_Z, side='Grass'):
    """The port behind Bayfront's side street (v140): the street runs back between the quay and the school's lawn to the
    port's gate; past the fence the yard, its ship-to-shore cranes on the quay with a freighter under them, another
    freighter alongside the quay by the street, a tug, and the container stacks. All on land: the water stays left of
    the quay (x < quay), from `front` back (the promenade's seawall on Bayfront, the park's or the downtown basin's edge).
    The land on the street's other side, to the gate, is `side` (the school's lawn, or downtown's paving). Built at the
    end of a district, it clears whatever the district stood where the port now is (v142: Downpour and Museum Park)."""
    road_a, road_b = crossing                  # TrackBuilder.Crossing's open area (leg_info widens it): the street's asphalt
    yard_to = road_b + 95.0
    rgb_conc, rgb_fence = (0.8, 0.79, 0.76), (0.42, 0.44, 0.45)
    end = plan.x1 + 60
    z0 = front - 0.4 if front < 10 else front      # (a promenade's strip ends at its seawall; a park's or a street's at `front`)
    # whatever the district stood where the port now is goes (the quay, the yard, the street's far side)
    plan.items = [it for it in plan.items if len(it) > 6 or not (quay - 2 <= it[2] <= yard_to + 2 and front <= it[3] <= PORT_BACK_Z + 4)]
    # the ground: the quay's apron beside the street, the land on its other side to the fence, the yard past the fence
    # (the rest, out to the horizon, is the plan's ground: Plan.ground)
    plan.land.append({'from': round(quay, 2), 'to': round(road_a, 2), 'z0': round(z0, 2), 'z1': PORT_GATE_Z, 'surface': 'Concrete'})
    l = {'from': round(road_a, 2), 'to': round(end, 2), 'z0': round(z0, 2), 'z1': PORT_GATE_Z}
    if side != 'Grass': l['surface'] = side
    plan.land.append(l)
    plan.land.append({'from': round(quay, 2), 'to': round(yard_to, 2), 'z0': PORT_GATE_Z, 'z1': PORT_BACK_Z, 'surface': 'Concrete'})
    # the quay's face down into the water (out to the horizon, where the land beside the water goes on), its fenders, the
    # yellow line along its edge, bollards
    plan.box('QuayWall', quay - 0.3, quay, WATER_Y - 0.5, 0.0, front - 0.34, FAR_Z, (0.74, 0.73, 0.7), 'Concrete')
    z = front + 4.0
    while z < PORT_BACK_Z - 2:
        plan.box('Fender', quay - 0.55, quay - 0.3, WATER_Y - 0.2, -0.15, z - 0.4, z + 0.4, (0.13, 0.13, 0.14))
        z += 9.0
    plan.box('QuayLine', quay + 0.35, quay + 0.5, 0.0, 0.015, front + 0.4, PORT_BACK_Z, (0.95, 0.8, 0.2))
    z = front + 6.0
    while z < PORT_BACK_Z - 2:
        plan.put('Miami', 'BollardMIA', quay + 0.6, z)
        if plan.rng.random() < 0.3: plan.put('Miami', 'LineCoilMIA', quay + 1.3, z + 0.8, plan.r(0, 360))
        z += 11.0
    # alongside: a freighter by the street, another under the cranes, a tug between
    plan.put('Miami', 'FreighterMIA', quay - 4.7, max(34.0, front + 18.0), 90.0, 1.0, y=WATER_Y + 0.2)
    plan.put('Miami', 'FreighterMIA', quay - 4.7, 118.0, 270.0, 1.0, y=WATER_Y + 0.2)
    plan.put('Miami', 'TugMIA', quay - 9.0, 78.0, 90.0, 1.0, y=WATER_Y + 0.3)
    # the ship-to-shore cranes: legs on rails along the quay, the boom out over the water, the A-frame and its stays
    for cz in (98.0, 122.0, 140.0):
        sea, land = quay + 1.4, quay + 17.4
        for lx in (sea, land):
            for dz in (-5.5, 5.5):
                plan.box('CraneLeg', lx - 0.5, lx + 0.5, 0.0, 28.0, cz + dz - 0.5, cz + dz + 0.5, PORT_CRANE_RED)
            plan.box('CraneSill', lx - 0.45, lx + 0.45, 9.0, 9.8, cz - 5.5, cz + 5.5, PORT_CRANE_RED)
            plan.box('CraneHead', lx - 0.55, lx + 0.55, 27.0, 28.4, cz - 6.0, cz + 6.0, PORT_CRANE_RED)
        for dz in (-5.5, 5.5):
            plan.box('CranePortal', sea - 0.5, land + 0.5, 27.2, 28.4, cz + dz - 0.5, cz + dz + 0.5, PORT_CRANE_RED)
        tip, back = quay - 30.0, quay + 27.0
        plan.box('CraneBoom', tip, back, 28.4, 30.2, cz - 1.7, cz + 1.7, PORT_WHITE)
        plan.box('CraneHouse', back - 6.5, back - 0.5, 30.2, 33.4, cz - 2.6, cz + 2.6, PORT_WHITE)
        plan.box('CraneCab', quay - 1.2, quay + 0.8, 26.6, 28.4, cz + 1.0, cz + 2.6, (0.3, 0.36, 0.42))
        apex = quay + 9.0
        for dz in (-1.5, 1.5):
            plan.box('CraneTower', apex - 0.4, apex + 0.4, 30.2, 43.0, cz + dz - 0.4, cz + dz + 0.4, PORT_CRANE_RED)
            plan.beam('CraneStay', apex, 42.6, tip + 1.0, 30.0, cz + dz, 0.3, PORT_WHITE)
            plan.beam('CraneStay', apex, 42.6, back - 1.0, 30.0, cz + dz, 0.3, PORT_WHITE)
        plan.box('CraneTowerTop', apex - 0.4, apex + 0.4, 42.6, 43.4, cz - 1.9, cz + 1.9, PORT_CRANE_RED)
        trolley = quay - plan.r(3.0, 9.0)
        plan.box('CraneTrolley', trolley - 1.5, trolley + 1.5, 27.4, 28.4, cz - 1.6, cz + 1.6, (0.3, 0.32, 0.34))
        hang = plan.r(14.0, 20.0)
        for dx in (-0.9, 0.9):
            plan.box('CraneRope', trolley + dx - 0.04, trolley + dx + 0.04, hang + 0.4, 27.4, cz - 0.04, cz + 0.04, (0.2, 0.2, 0.2))
        plan.box('CraneSpreader', trolley - 3.0, trolley + 3.0, hang, hang + 0.4, cz - 1.2, cz + 1.2, (0.9, 0.72, 0.18))
    # the fence along the gate's line (open for the street), and down the yard's far end
    def fence_x(a, b, z):
        n = max(1, int(round((b - a) / 3.0)))
        for i in range(n + 1):
            x = a + (b - a) * i / n
            plan.box('FencePost', x - 0.05, x + 0.05, 0.0, 2.5, z - 0.05, z + 0.05, rgb_fence)
        for y in (0.15, 1.3, 2.4):
            plan.box('FenceRail', a, b, y - 0.03, y + 0.03, z - 0.03, z + 0.03, rgb_fence)
    def fence_z(x, a, b):
        n = max(1, int(round((b - a) / 3.0)))
        for i in range(n + 1):
            z = a + (b - a) * i / n
            plan.box('FencePost', x - 0.05, x + 0.05, 0.0, 2.5, z - 0.05, z + 0.05, rgb_fence)
        for y in (0.15, 1.3, 2.4):
            plan.box('FenceRail', x - 0.03, x + 0.03, y - 0.03, y + 0.03, a, b, rgb_fence)
    fence_x(quay + 0.8, road_a - 2.0, PORT_GATE_Z)
    fence_x(road_b + 2.0, yard_to, PORT_GATE_Z)
    fence_z(yard_to, PORT_GATE_Z, PORT_BACK_Z)
    # the gate: its booths either side of the street, the sign gantry over it (clear 5 m up), the barriers raised
    for bx in (road_a - 1.2, road_b + 1.2):
        plan.box('GateBooth', bx - 0.8, bx + 0.8, 0.0, 2.5, PORT_GATE_Z - 1.0, PORT_GATE_Z + 1.0, PORT_WHITE)
        plan.box('GateBoothRoof', bx - 1.0, bx + 1.0, 2.5, 2.7, PORT_GATE_Z - 1.2, PORT_GATE_Z + 1.2, (0.16, 0.36, 0.6))
        plan.box('GatePost', bx - 0.2, bx + 0.2, 2.7, 6.8, PORT_GATE_Z - 0.2, PORT_GATE_Z + 0.2, (0.6, 0.62, 0.64))
    plan.box('GateSign', road_a - 1.4, road_b + 1.4, 5.0, 6.6, PORT_GATE_Z - 0.15, PORT_GATE_Z + 0.15, (0.16, 0.36, 0.6))
    plan.labels.append({'t': 'PORT  GATE 3', 'c': [round((road_a + road_b) / 2, 3), 5.8, round(PORT_GATE_Z - 0.2, 3)], 'size': 0.16,
                        'rgb': [1.0, 1.0, 1.0]})
    for bx in (road_a - 0.25, road_b + 0.25):          # (beside the street, clear of its asphalt)
        plan.box('GateArm', bx - 0.06, bx + 0.06, 1.0, 4.6, PORT_GATE_Z - 0.06, PORT_GATE_Z + 0.06, (0.92, 0.25, 0.2))
    # light masts over the yard
    for lx, lz in ((road_b + 4.0, PORT_GATE_Z + 6.0), (road_b + 52.0, PORT_GATE_Z + 6.0), (road_b + 4.0, PORT_BACK_Z - 8.0)):
        plan.box('LightMast', lx - 0.25, lx + 0.25, 0.0, 24.0, lz - 0.25, lz + 0.25, (0.6, 0.62, 0.64))
        plan.box('LightHead', lx - 1.4, lx + 1.4, 24.0, 24.7, lz - 0.6, lz + 0.6, (0.3, 0.32, 0.34))
    # the container stacks, in blocks: 12.2 m boxes end to end along the street, rows behind each other, one to four high
    for bz in (PORT_GATE_Z + 12.0, PORT_GATE_Z + 34.0, PORT_GATE_Z + 56.0):
        for bx0, bays in ((road_b + 8.0, 3), (road_b + 8.0 + 3 * 12.6 + 5.0, 3)):
            for row in range(5):
                z0 = bz + row * 2.74
                for bay in range(bays):
                    x0 = bx0 + bay * 12.6
                    if x0 + 12.2 > yard_to - 2.0: continue
                    high = plan.rng.choice([0, 1, 2, 2, 3, 3, 3, 4])
                    for k in range(high):
                        plan.box('Container', x0, x0 + 12.2, k * 2.6, k * 2.6 + 2.56, z0, z0 + 2.44, plan.rng.choice(CONTAINER_COLOURS))
    # trucks waiting on the apron under the cranes, a container on each
    for tz in (PORT_GATE_Z + 26.0, PORT_GATE_Z + 50.0):
        tx = quay + plan.r(6.0, 12.0)
        colour = plan.rng.choice(CONTAINER_COLOURS)
        plan.box('TruckCab', tx - 1.25, tx + 1.25, 0.5, 3.4, tz - 2.4, tz, (0.85, 0.85, 0.82))
        plan.box('TruckChassis', tx - 1.2, tx + 1.2, 0.5, 1.3, tz, tz + 12.6, (0.2, 0.2, 0.22))
        plan.box('TruckBox', tx - 1.22, tx + 1.22, 1.3, 3.86, tz + 0.2, tz + 12.4, colour)


def river(plan, rail='RiverRailMIA'):
    li = plan.li
    plan.set_water()
    x = plan.x0
    while x < plan.x1:
        if plan.free(x, x + 4.0, deep=True):
            plan.put('Miami', rail, x + 2.0, WATER_Z - 0.35)
        x += 4.0
    x = plan.x0 + 2
    while x < plan.x1:
        if plan.free(x - 1, x + 1, deep=True):
            plan.put('Miami', 'BollardMIA', x, WATER_Z - 1.0)
            if plan.rng.random() < 0.5: plan.put('Miami', 'LineCoilMIA', x + 1.0, WATER_Z - 1.4, plan.r(0, 360))
        x += plan.r(8, 13)
    # moored along the far side of the channel, and across it the far bank's towers and sheds
    x = plan.x0 + plan.r(0, 20)
    while x < plan.x1:
        kind = plan.rng.random()
        if plan.free(x - 16, x + 16, deep=True):
            if kind < 0.6: plan.put('Miami', 'FreighterMIA', x, 16.0, 0.0, 1.0, y=WATER_Y + 0.2)
            else: plan.put('Miami', 'TugMIA', x, 13.0, 0.0, 1.0, y=WATER_Y + 0.3)
        x += plan.r(36, 60)
    plan.water['z1'] = 34.0
    plan.land.append({'from': round(plan.x0 - SIDE, 2), 'to': round(plan.x1 + SIDE, 2), 'z0': 34.0, 'z1': FAR_Z, 'fill': True})
    plan.box('RiverBank', plan.x0 - SIDE, plan.x1 + SIDE, WATER_Y - 0.4, 0.0, 34.0, 34.4, (0.74, 0.73, 0.7), 'Concrete')
    plan.deep_row([('Miami', 'MuralShedMIA', 12), ('Miami', 'MedRevivalMIA', 15), ('Miami', 'TowerPodiumMIA', 24)], 38, 44, step=(14, 26))
    plan.palms(36, 40, step=(8, 14))
    plan.skyline(60, 110, n_per_100=6)
    plan.skyline(150, 260, n_per_100=4, scale=(1.0, 1.4))


def downtown(plan):
    li = plan.li
    fronts = make_deck(plan, ['DecoArcade2MIA', 'MedRevivalMIA', 'DecoArcadeMIA', 'PharmacyMIA', 'DecoCafeFL', 'DecoShutFL', 'DecoIceFL'])
    plan.front_row(fronts, PROPERTY_Z + 0.5, W, gap=(0.0, 2.0))
    def things(x):
        c = plan.rng.random()
        if c < 0.5: return ('Florida', 'LampFL', 0.0)
        if c < 0.7: return ('Florida', 'TrashFL', 0.1)
        if c < 0.8: return ('Florida', 'HydrantFL', 0.1)
        return ('Florida', 'BenchFL', 0.4)
    plan.street_things(things, step=(6.0, 10.0))
    plan.deep_row([('Miami', 'DecoArcadeMIA', 12), ('Miami', 'MedRevivalMIA', 15), ('Miami', 'TowerPodiumMIA', 24)], 16, 20, step=(12, 20))
    plan.deep_row([('Miami', 'SpanishTowerMIA', 14)], 70, 90, step=(120, 200), scale=(0.9, 1.0))
    plan.skyline(45, 90, n_per_100=6)
    plan.skyline(130, 220, n_per_100=4, scale=(1.0, 1.4))
    if li['crossings'] and li['school']:
        # v142: the port beside the school, as on Bayfront. Downtown meets the bay here: a basin of it behind the blocks, 60 m
        # wide, from behind the deep row (z 34) out to the horizon, its quay along the port road. The street's own paving
        # ends at the basin's edge; downtown's other blocks keep their towers.
        cr = li['crossings'][0]
        quay = cr[0] - 4.0
        plan.back = BASIN_Z
        plan.set_water(z=BASIN_Z, start=quay - 60.0, until=quay)
        plan.box('BasinWall', quay - 60.3, quay - 60.0, WATER_Y - 0.5, 0.0, BASIN_Z - 0.34, FAR_Z, (0.74, 0.73, 0.7), 'Concrete')
        port(plan, quay, cr, BASIN_Z, side='Concrete')


BASIN_Z = 34.0      # downtown's bay basin starts behind its deep row


def underline(plan):
    li = plan.li
    # the guideway overhead along the street, behind the lane, one pier every 30 m
    x = plan.x0 + 15
    while x < plan.x1:
        plan.put('Miami', 'GuidewayMIA', x, 6.0)
        x += 30.0
    # the park under it: fitness bars, palms and planting; Little Havana's houses behind
    x = plan.x0 + 8
    while x < plan.x1:
        if plan.free(x - 2, x + 2):
            c = plan.rng.random()
            if c < 0.25: plan.put('Miami', 'FitnessBarsMIA', x, 3.6)
            elif c < 0.55: plan.put('Plants', 'PalmRoyal', x, plan.r(3.0, 4.0), plan.r(0, 360), plan.r(0.8, 1.0))
            elif c < 0.8: plan.put('Plants', plan.rng.choice(['SawPalmetto', 'PalmSabal']), x, plan.r(2.6, 4.2), plan.r(0, 360))
            else: plan.put('Florida', 'BenchFL', x, 2.4)
        x += plan.r(3.5, 7.0)
    houses = make_deck(plan, ['RanchFL', 'RanchSmallFL', 'CottageFL', 'MuralShedMIA'])
    plan.front_row(houses, 12.0, W, gap=(2.0, 5.0))
    plan.deep_row([('Plants', 'LiveOak', 10), ('Plants', 'PalmSabalTall', 4)], 22, 30, step=(7, 14))
    plan.ibises(2.6, 4.4, n_per_100=3)
    plan.skyline(300, 450, n_per_100=2, scale=(1.0, 1.3))


def biscayne(plan):
    li = plan.li
    fronts = make_deck(plan, ['TowerPodiumMIA', 'MedRevivalMIA', 'TowerPodiumMIA', 'DecoArcadeMIA'])
    x = plan.x0
    while x < plan.x1:
        kit, m = fronts()
        w = W[m]
        if not plan.free(x, x + w):
            x = next((hi for lo, hi in plan.keep_out if x + w > lo and x < hi), x + 1.0) + 0.3
            continue
        plan.put(kit, m, x + w / 2, PROPERTY_Z + (3.8 if m == 'TowerPodiumMIA' else 0.5))
        if m == 'TowerPodiumMIA':
            plan.put('Miami', plan.rng.choice(['CondoTowerMIA', 'OfficeTowerMIA']), x + w / 2, 15.0, 0.0, plan.r(0.95, 1.15))
            forecourt(plan, x, w)
        g = plan.r(2.0, 5.0)
        if plan.free(x + w, x + w + g):
            plan.put('Plants', 'PalmRoyal', x + w + g / 2, 2.6, plan.r(0, 360), plan.r(0.9, 1.1))
        x += w + g
    def things(xx):
        c = plan.rng.random()
        if c < 0.45: return ('Florida', 'LampFL', 0.0)
        if c < 0.65: return ('Plants', 'PalmRoyal', -0.6)
        if c < 0.8: return ('Miami', 'ScooterUpMIA', 0.3)
        if c < 0.9: return ('Florida', 'BenchFL', 0.4)
        return ('Florida', 'TrashFL', 0.1)
    plan.street_things(things, step=(5.0, 8.0))
    plan.put('Miami', 'SpanishTowerMIA', (plan.x0 + plan.x1) / 2 + plan.r(-20, 20), 40.0, 0.0, 1.0)
    x = plan.x0 + 10
    while x < plan.x1:
        plan.put('Miami', 'GuidewayMIA', x, 28.0)
        x += 30.0
    plan.skyline(60, 120, n_per_100=6)
    plan.skyline(150, 260, n_per_100=4, scale=(1.0, 1.4))


def museum_park(plan):
    li = plan.li
    goal = li['goal']
    # v142: the port beside the school, as on Bayfront: the bay ends at the quay, 4 m before the port road (its crossing)
    land_from = li['crossings'][0][0] - 4.0 if li['crossings'] else goal - 26.0
    plan.set_water(z=26.0, until=land_from)
    plan.put('Miami', 'MuseumMIA', li['start'] + 40.0, 9.0)
    x = plan.x0 + 5
    while x < plan.x1:
        if plan.free(x - 4, x + 4):
            c = plan.rng.random()
            if c < 0.35: plan.put('Plants', 'Banyan', x, plan.r(5.5, 8.0), plan.r(0, 360), plan.r(0.85, 1.05))
            elif c < 0.7: plan.put('Plants', 'PalmRoyal', x, plan.r(2.6, 4.0), plan.r(0, 360), plan.r(0.85, 1.05))
            else: plan.put('Plants', plan.rng.choice(['SawPalmetto', 'PalmSabal']), x, plan.r(2.5, 4.5), plan.r(0, 360))
        x += plan.r(6.0, 11.0)
    x = plan.x0
    while x < land_from:
        plan.put('Miami', 'BayRailMIA', x + 2.0, 25.6)
        x += 4.0
    plan.put('Miami', 'CruiseShipMIA', min((plan.x0 + plan.x1) / 2, land_from - 75.0), 300.0, 0.0, 1.0, y=WATER_Y)
    plan.ibises(9.0, 22.0, n_per_100=4)
    plan.skyline(675, 850, n_per_100=4, scale=(0.8, 1.2))
    plan.far_shore(640)
    if li['crossings']: port(plan, land_from, li['crossings'][0], 26.0)
    else: plan.land.append({'from': round(land_from, 2), 'to': round(plan.x1 + 60, 2), 'z0': 25.0, 'z1': 120.0})


RIVER_NEAR, RIVER_FAR = 56.0, 96.0      # Riverside Street's river behind the yards


def riverside(plan):
    """FL2-1 Riverside Street: from the ranch house down to the Miami River through a street of ranch houses and Old Florida
    cottages in their yards, live oaks hung with moss, sabals and royal palms, mailboxes on posts, wooden poles; the river's
    freighters and cranes beyond the roofs toward the end."""
    li = plan.li
    houses = make_deck(plan, ['RanchFL', 'RanchSmallFL', 'CottageFL', 'RanchFL', 'RanchSmallFL'])
    plan.front_row(houses, PROPERTY_Z + 2.6, W, gap=(2.0, 4.5))
    def things(x):
        c = plan.rng.random()
        if c < 0.3: return ('Street', 'UtilityPoleWood', 0.05)
        if c < 0.55: return ('Florida', 'MailboxPostFL', 0.1)
        if c < 0.8: return ('Plants', 'PalmSabalTall', -0.6)
        return ('Florida', 'HydrantFL', 0.1)
    plan.street_things(things, step=(6.0, 10.0))
    plan.deep_row([('Plants', 'LiveOak', 10), ('Plants', 'PalmSabalTall', 4), ('Plants', 'PalmRoyal', 4), ('Plants', 'Banyan', 12)], 13, 18,
                  step=(7, 13))
    plan.deep_row([('Florida', 'RanchFL', 12), ('Florida', 'CottageFL', 8), ('Florida', 'RanchSmallFL', 9)], 24, 30, step=(10, 16))
    plan.deep_row([('Plants', 'LiveOak', 10), ('Plants', 'PalmRoyal', 4)], 34, 44, step=(8, 15))
    plan.ibises(3.0, 5.0, n_per_100=3)
    end = li['goal']
    # v142: the Miami River runs behind the yards (the freighter stood on the lawn): the street's own ground ends at its
    # near bank, the freighter is moored on it, the crane and the skyline stand on the far bank.
    plan.back = RIVER_NEAR
    plan.set_water(z=RIVER_NEAR, z1=RIVER_FAR)
    plan.box('RiverBank', plan.x0 - SIDE, plan.x1 + SIDE, WATER_Y - 0.4, 0.0, RIVER_FAR, RIVER_FAR + 0.4, (0.74, 0.73, 0.7), 'Concrete')
    plan.put('Miami', 'FreighterMIA', end - 10.0, 72.0, 0.0, 1.0, y=WATER_Y + 0.2)
    plan.put('Miami', 'CraneMIA', end + 20.0, RIVER_FAR + 6.0, 0.0, 0.9)
    plan.skyline(260, 380, n_per_100=2, scale=(1.0, 1.3))


DISTRICTS = {'riverside': riverside, 'littleHavana': little_havana, 'brickell': brickell, 'bayfront': bayfront,
             'riverwalk': river, 'downtown': downtown, 'underline': underline, 'biscayne': biscayne, 'museumPark': museum_park}


def check(leg, d, plan):
    """What the camera sees stands on something (v142):
    - nothing that stands on the ground stands in open water or beyond the ground (an item with its own height floats or
      stands on a piling);
    - every boat floats on open water, over no land;
    - from the street's strips out to the horizon, across the whole width the camera sees at each distance, every point
      is land or water: no tower on the sky."""
    w = d.get('water')
    lands = d.get('land', [])
    back = plan.strip_back()
    def on_land(x, z): return any(l['from'] <= x <= l['to'] and l['z0'] <= z <= l['z1'] for l in lands)
    def wet(x, z):
        return bool(w) and w['from'] <= x <= w['to'] and w['z'] + 0.2 < z < w.get('z1', FAR_Z) and not on_land(x, z)
    bad = []
    for it in d['items']:
        kit, model, x, z = it[0], it[1], it[2], it[3]
        if len(it) > 6:
            if it[6] < -0.3 and not wet(x, z): bad.append('%s afloat off the water at x %.1f z %.1f' % (model, x, z))
            continue
        if wet(x, z): bad.append('%s in the water at x %.1f z %.1f' % (model, x, z))
        elif z > back + 0.5 and not on_land(x, z): bad.append('%s off the ground at x %.1f z %.1f' % (model, x, z))
    # the ground under the camera's view: 0.7 of the distance either side (34 degrees high on a 2.2:1 screen: 0.67)
    z = back + 1.0
    while z < FAR_Z - 1.0:
        half = 0.7 * (z + 10.0)
        x = plan.x0 - half
        while x <= plan.x1 + half:
            if not (on_land(x, z) or (w and w['from'] <= x <= w['to'] and w['z'] <= z <= w.get('z1', FAR_Z))):
                bad.append('no ground at x %.0f z %.0f' % (x, z))
                break
            x += 25.0
        z += 25.0 if z < 300 else 100.0
    if bad:
        raise SystemExit('%s: %s' % (leg, '; '.join(bad[:8])))


def main():
    src = open(LAYOUTS).read()
    info = leg_info(src)
    legs = {}
    for leg, li in sorted(info.items()):
        plan = Plan(leg, li)
        DISTRICTS[li['district']](plan)
        dropped = plan.ground()
        plan.plazas()
        plan.city()
        if dropped: print('  %s: %d left out of the water: %s' % (leg, len(dropped), ', '.join(sorted(set(dropped)))))
        legs[leg] = plan.to_json()
        check(leg, legs[leg], plan)
        print('%-6s %-12s %4d items  x %.0f..%.0f' % (leg, li['district'], len(plan.items), plan.x0, plan.x1))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'version': 1, 'notes': 'Written by tools/blender/miami_plan.py: what stands along each of Florida\'s legs. '
                   'Items are [kit, model, x, z, yaw, scale(, y)]: game axes, yaw as Unity turns a model.', 'legs': legs}, f, indent=0)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
