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
        self.land = []
        self.gap_trees = ['PalmRoyal', 'PalmRoyal', 'PalmSabalTall']

    def put(self, kit, model, x, z, yaw=0.0, scale=1.0, y=None):
        if x < self.x0 or x > self.x1: return
        z = clear_of_the_ball(kit, model, z, yaw, scale)
        if self.in_street(kit, model, x, z, scale): return
        it = [kit, model, round(x, 3), round(z, 3), round(yaw, 1), round(scale, 3)]
        if y is not None: it.append(round(y, 3))
        self.items.append(it)

    def in_street(self, kit, model, x, z, scale):
        """Would this model, at x and depth z, stand in a side street (as StreetBuilder.InSideStreet decides)?"""
        if not self.streets: return False
        info = _model_info(kit, model)
        half = max(info['size'][0], info['size'][1]) * scale / 2 if info and 'size' in info else 1.0
        if z - half > SIDE_STREET_END: return False
        return any(x + half > a - 0.3 and x - half < b + 0.3 for a, b in self.streets)

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

    def far_shore(self, z0, z1):
        """The barrier island across the bay (Miami Beach), under its towers."""
        self.land.append({'from': round(self.x0 - 260, 2), 'to': round(self.x1 + 260, 2), 'z0': z0, 'z1': z1})

    def set_water(self, z=WATER_Z, until=None, start=None):
        a = self.x0 if start is None else start
        b = self.x1 if until is None else until
        self.water = {'from': round(a, 2), 'to': round(b, 2), 'z': z, 'y': WATER_Y}

    def to_json(self):
        li = self.li
        d = {'district': li['district'], 'strips': li['strips'], 'items': self.items}
        if self.water: d['water'] = self.water
        if self.land: d['land'] = self.land
        return d


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
    if li['school'] or li['crossings']:
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
    plan.put('Miami', 'CruiseShipMIA', (plan.x0 + plan.x1) / 2 + plan.r(-30, 30), 340.0, 0.0, 1.0, y=WATER_Y)
    plan.put('Miami', 'FreighterMIA', plan.x0 + plan.r(10, 40), 120.0, 0.0, 1.0, y=WATER_Y + 0.2)
    plan.skyline(700, 900, n_per_100=5, scale=(0.8, 1.2))
    plan.far_shore(690, 960)
    if li['school']:
        # (on the school's land only: the bay is open water)
        plan.deep_row([('Plants', 'PalmRoyal', 4), ('Plants', 'LiveOak', 10)], 30, 50, step=(6, 10), x_from=land_from + 2.0)


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
    plan.land.append({'from': round(plan.x0 - 60, 2), 'to': round(plan.x1 + 60, 2), 'z0': 34.0, 'z1': 400.0})
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
    land_from = goal - 26.0
    plan.set_water(z=26.0, until=land_from)
    plan.land.append({'from': round(land_from, 2), 'to': round(plan.x1 + 60, 2), 'z0': 25.0, 'z1': 120.0})
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
    plan.put('Miami', 'CruiseShipMIA', (plan.x0 + plan.x1) / 2, 300.0, 0.0, 1.0, y=WATER_Y)
    plan.ibises(9.0, 22.0, n_per_100=4)
    plan.skyline(650, 850, n_per_100=4, scale=(0.8, 1.2))
    plan.far_shore(640, 900)


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
    plan.put('Miami', 'FreighterMIA', end - 10.0, 70.0, 0.0, 1.0)
    plan.put('Miami', 'CraneMIA', end + 20.0, 85.0, 0.0, 0.9)
    plan.skyline(260, 380, n_per_100=2, scale=(1.0, 1.3))


DISTRICTS = {'riverside': riverside, 'littleHavana': little_havana, 'brickell': brickell, 'bayfront': bayfront,
             'riverwalk': river, 'downtown': downtown, 'underline': underline, 'biscayne': biscayne, 'museumPark': museum_park}


def check(leg, d):
    """Nothing that stands on the ground stands in open water (an item with its own height floats or stands on a piling)."""
    w = d.get('water')
    if not w: return
    bad = []
    for it in d['items']:
        if len(it) > 6: continue
        kit, model, x, z = it[0], it[1], it[2], it[3]
        if not (w['from'] <= x <= w['to'] and z > w['z'] + 0.2): continue
        if any(l['from'] <= x <= l['to'] and l['z0'] <= z <= l['z1'] for l in d.get('land', [])): continue
        bad.append('%s at x %.1f z %.1f' % (model, x, z))
    if bad:
        raise SystemExit('%s: in the water: %s' % (leg, ', '.join(bad[:8])))


def main():
    src = open(LAYOUTS).read()
    info = leg_info(src)
    legs = {}
    for leg, li in sorted(info.items()):
        plan = Plan(leg, li)
        DISTRICTS[li['district']](plan)
        legs[leg] = plan.to_json()
        check(leg, legs[leg])
        print('%-6s %-12s %4d items  x %.0f..%.0f' % (leg, li['district'], len(plan.items), plan.x0, plan.x1))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'version': 1, 'notes': 'Written by tools/blender/miami_plan.py: what stands along each of Florida\'s legs. '
                   'Items are [kit, model, x, z, yaw, scale(, y)]: game axes, yaw as Unity turns a model.', 'legs': legs}, f, indent=0)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
