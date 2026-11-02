# The set pieces of the town map: the home, what each level shows beside its node (the street, the market, the beach, the
# underpass, the building site, the park), the school, the station. Each piece is a list of kit models to stand on the ground
# (Items) and painting operations for the flat ground under and around them. They are placed from the SOLVED level nodes and
# their routes (frame(): a point 80 to 200 px along the route from the node, on either side of it), so the picture shows the
# level's content where its node is and TownMapLayout.json agrees with it.
#   town_map_sets.py        the base (helpers, painting shapes), the home and the street, market and level scenes of the town
#   town_map_sets_nature.py the park, the beach, the school's grounds and the country round the town
#   town_map_sets_works.py  the building site, the railway with the station and the underpass bridges, the school building
import math, random
import town_map_raster as R
import town_map_graph as G
import town_map_models as M
import town_map_place as P
from town_map_place import Item

PPM = 8.0
CHARS = ['Kid', 'PrimaryBoy', 'PrimaryGirl', 'Adult', 'Girl', 'Boy', 'PrimaryBoy2', 'PrimaryGirl2']

# colours (sRGB) of the painted details
C_STONE = (0.78, 0.76, 0.71)
C_STONE_D = (0.62, 0.60, 0.56)
C_PAVE = (0.80, 0.77, 0.71)
C_WATER = (0.40, 0.68, 0.76)
C_WATER_D = (0.30, 0.56, 0.68)
C_BANK = (0.58, 0.52, 0.40)
C_WET = (0.30, 0.31, 0.34)
C_PUDDLE = (0.46, 0.55, 0.64)
C_WHITE = (0.94, 0.94, 0.91)
C_GRASS = (0.47, 0.60, 0.35)
C_GRASS_D = (0.40, 0.54, 0.32)
C_GRASS_L = (0.55, 0.67, 0.40)
C_DIRT = (0.62, 0.53, 0.41)
C_GRAVEL = (0.66, 0.62, 0.56)
C_CONCRETE = (0.72, 0.71, 0.68)
C_CONCRETE_D = (0.55, 0.55, 0.54)
C_RED = (0.78, 0.30, 0.26)
C_FLOWERS = [(0.92, 0.55, 0.62), (0.98, 0.84, 0.35), (0.90, 0.42, 0.36), (0.80, 0.62, 0.86), (0.96, 0.96, 0.9)]


def ang(t):
    """The angle (degrees, counter-clockwise on the screen) of a direction in core px: for rectangle masks."""
    return math.degrees(math.atan2(-t[1], t[0]))


def bearing(t):
    """The compass bearing (0 = up the picture, 90 = right) of a direction in core px: the `face` of a model that looks along it."""
    return math.degrees(math.atan2(t[0], -t[1]))


# ------------------------------------------------------------------ painting shapes (core px)
def fill(cv, pts, col, a=1.0, blur=0.0):
    cv.blend(cv.poly_mask(pts, blur=blur), col, a)


def rect(cv, c, w, h, angle, col, a=1.0):
    cv.blend(cv.rect_mask(c, w, h, angle), col, a)


def disc(cv, c, r, col, a=1.0):
    cv.blend(cv.disc_mask(c, r), col, a)


def stroke(cv, pts, w, col, a=1.0, cap=False):
    cv.blend(cv.line_mask(pts, w, cap=cap), col, a)


def ellipse(cv, c, rx, ry, angle, col, a=1.0, blur=0.0):
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    pts = []
    for k in range(40):
        t = k * math.pi / 20
        x, y = math.cos(t) * rx, math.sin(t) * ry
        pts.append((c[0] + x * ca + y * sa, c[1] - x * sa + y * ca))
    cv.blend(cv.poly_mask(pts, blur=blur), col, a)


def textured(cv, pts, col, seed, amp=(0.05, 0.035, 0.02), cells=(60, 16, 4), a=1.0, blur=0.6):
    m = cv.poly_mask(pts, blur=blur)
    if m is not None:
        cv.blend(m, cv.textured(m, col, amp, cells, seed), a)


def zebra(cv, c, t, span, length=24.0, bar=4.2, gap=4.0):
    """A zebra crossing: bars along the road direction t, spread across the carriageway (`span` px wide) round the point c."""
    n = (-t[1], t[0])
    k = int(span // (bar + gap))
    for i in range(-(k // 2), k // 2 + 1):
        off = i * (bar + gap)
        rect(cv, (c[0] + n[0] * off, c[1] + n[1] * off), length, bar, ang(t), C_WHITE, 0.93)


class Base:
    def __init__(self, L, B, world, masks):
        self.L, self.B, self.world, self.masks = L, B, world, masks
        self.items = []
        self.pre, self.post = [], []
        self.rng = random.Random(99)
        self.nodes = B['nodes']
        self.routes = B['routes']
        self.roads = {r.id: r for r in B['graph'].roads}

    # ---------------------------------------------------------------- helpers
    def node(self, nid):
        n = self.nodes[nid]
        return (n['x'], n['y'])

    def frame(self, nid, ds=0.0, off=0.0):
        """The point at arc length ds from node nid along its route (positive = on towards the school), shifted `off` px to the RIGHT of
        the direction of travel (negative = left); and the unit tangent there."""
        pts = self.routes[self.nodes[nid]['route']]
        p, t = G.point_at(pts, max(0.0, self.nodes[nid]['s'] + ds))
        return (p[0] - t[1] * off, p[1] + t[0] * off), t

    def add(self, kit, name, x, y, face=0.0, scale=1.0, tints=None, z=0.0, tag='set', params=None):
        it = Item(kit, name, x, y, face, scale, tints, z, tag, params)
        self.items.append(it)
        return it

    def box(self, x, y, w, d, h, face, colour, z=0.0, tag='box', roof=None):
        """A custom block w x d x h metres (a roof 'ridge', 'flat', 'round', 'wedge' for a ramp, 'frame' for a goal)."""
        return self.add('custom', 'box', x, y, face, 1.0, colour, z, tag, params=dict(w=w, d=d, h=h, roof=roof))

    def slab(self, c, t, length, width, h, colour, z=0.0, roof=None, tag='box'):
        """A block whose long side (length px) runs along the direction t, centred on c."""
        face = math.degrees(math.atan2(-t[1], -t[0]))
        return self.box(c[0], c[1], length / PPM, width / PPM, h, face, colour, z, tag, roof)

    @staticmethod
    def smooth(pts, step=3.0):
        """A smooth curve through the points (a stream, a channel), as a dense polyline."""
        return G.catmull_rom([tuple(p) for p in pts], step=step)[0] if len(pts) >= 3 else list(pts)

    def op(self, fn, post=False):
        (self.post if post else self.pre).append(fn)

    def paint(self, cv, stage='pre'):
        for fn in (self.post if stage == 'post' else self.pre):
            fn(cv)

    def reserve(self, c, w, h, angle=0.0):
        self.world.occupy(R.rect_pts(c, w, h, angle))

    def line_of(self, pts, kit, name, step, tints=None, scale=1.0, skip=(), tag='fence'):
        """Models along a polyline every `step` px, their local X along the line (tiling models); skip = [(x, y, r)] gaps."""
        total = G.poly_length(pts)
        s = step / 2
        while s < total:
            p, t = G.point_at(pts, s)
            if not any((p[0] - gx) ** 2 + (p[1] - gy) ** 2 < gr * gr for gx, gy, gr in skip):
                face = math.degrees(math.atan2(-t[1], -t[0]))
                self.add(kit, name, p[0], p[1], face, scale, tints, tag=tag)
            s += step

    def car(self, x, y, t, flip=False, kit=None, tag='car'):
        k = kit or self.rng.choice(P.CARS)
        self.add(k[0], k[1], x, y, bearing(t) + (180.0 if flip else 0.0), 1.0, None, tag=tag)

    def person(self, x, y, face=None, scale=2.3):
        self.add('Chars', self.rng.choice(CHARS), x, y, self.rng.uniform(0, 360) if face is None else face, scale, None, tag='person')

    def crowd(self, c, rx, ry, n, angle=0.0):
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        for _ in range(n):
            u, v = self.rng.uniform(-1, 1) * rx, self.rng.uniform(-1, 1) * ry
            self.person(c[0] + u * ca + v * sa, c[1] - u * sa + v * ca)

    def crown(self, x, y, r=None, **kw):
        self.items.append(P.crown(x, y, self.rng, r, **kw))
        rr = (r or 18) * 0.5
        self.world.occupy([(x - rr, y - rr), (x + rr, y - rr), (x + rr, y + rr), (x - rr, y + rr)])

    def trees_in(self, poly, count, seed, rmin=14, rmax=26, avoid=(), kinds=('park',), kit_share=0.1, blossom=0.08, min_gap=0.55):
        """Round crowns at random inside a polygon on free ground (not on roads, buildings, paths or `avoid` discs)."""
        rng = random.Random(seed)
        xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
        placed = []
        tries = 0
        while len(placed) < count and tries < count * 80:
            tries += 1
            x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
            if not self._inside(poly, (x, y)):
                continue
            r = rng.uniform(rmin, rmax)
            if any(math.hypot(x - ax, y - ay) < ar + r * 0.6 for ax, ay, ar in avoid):
                continue
            rr = r * 0.6
            pts = [(x - rr, y - rr), (x + rr, y - rr), (x + rr, y + rr), (x - rr, y + rr)]
            if not self.world.free(pts, kinds, roads=True):
                continue
            if any(math.hypot(x - px, y - py) < min_gap * (r + pr) for px, py, pr in placed):
                continue
            placed.append((x, y, r))
            self.items.append(P.tree_item(x, y, rng, r, kit_share=kit_share, blossom=blossom))
            self.world.occupy(pts)
        return placed

    @staticmethod
    def _inside(poly, p):
        x, y = p
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
                inside = not inside
        return inside

    def awning_stall(self, x, y, face, col=None):
        self.add('Street', 'MarketStall', x, y, face, 1.0, [col or self.rng.choice(P.AWNINGS)], tag='stall')

    def sand_dist(self, p):
        """Distance from p to the coast curve (px), for keeping beach things out of the water."""
        best = 1e9
        coast = self.L.COAST
        for i in range(len(coast) - 1):
            best = min(best, G.seg_closest(p, coast[i], coast[i + 1])[2])
        return best


# ------------------------------------------------------------------ the town: home, the street levels, the market levels
class TownSets:
    def town(self):
        self.home()
        self.street_levels()
        self.market_levels()
        self.court_c01()
        self.parade_c02()

    # ---------------------------------------------------------------- home: the red-door house at the first corner of the street
    def home(self):
        rng = self.rng
        face = 180.0
        front = (522.0, 750.0)
        O = P.origin_for('Buildings', 'HouseGable', front, face, 1.0)
        self.add('Buildings', 'HouseGable', O[0], O[1], face, 1.0, [(0.97, 0.93, 0.82), (0.80, 0.20, 0.16), (0.32, 0.35, 0.43)], tag='home')
        self.world.occupy(P.footprint('Buildings', 'HouseGable', O[0], O[1], face, 1.0, pad=0.6))
        self.reserve((522, 732), 104, 100)
        self.home_front = front
        # the front garden: lawn, a path from the gate to the red door, flower beds, a low fence with a gate, hedges, a post box and a bike
        self.op(lambda cv: rect(cv, (522, 764), 92, 28, 0, C_GRASS_L, 0.95))
        self.op(lambda cv: rect(cv, (522, 764), 8, 28, 0, C_STONE, 1.0))
        for sx in (-1, 1):
            self.op(lambda cv, sx=sx: ellipse(cv, (522 + sx * 24, 766), 14, 5, 0, (0.50, 0.36, 0.26), 0.95))
            for k in range(7):
                fx, fy = 522 + sx * (12 + k * 4), 766 + (k % 3 - 1) * 2.2
                self.op(lambda cv, fx=fx, fy=fy, c=rng.choice(C_FLOWERS): disc(cv, (fx, fy), 2.2, c, 0.95))
        self.line_of([(476, 777), (568, 777)], 'Street', 'PicketFence2', 16, [(0.97, 0.95, 0.90)], skip=[(522, 777, 15)])
        self.add('Street', 'WallPillar', 507, 777, 0, 0.8, [(0.9, 0.88, 0.8)], tag='gate')
        self.add('Street', 'WallPillar', 537, 777, 0, 0.8, [(0.9, 0.88, 0.8)], tag='gate')
        for hx in (484, 560):
            self.add('Plants', 'HedgeBlock2', hx, 758, 180, 1.0, None, tag='hedge')
        self.add('Street', 'PostBox', 573, 772, 180)
        self.add('Street', 'Bicycle', 492, 770, 100)
        self.add('Street', 'PotGroup', 508, 760, 180)
        self.add('Street', 'BinPair', 481, 735, 90)
        self.crown(560, 698, 17)
        self.crown(490, 690, 15, blossom=0.8)
        # the first kerb: a dropped kerb with red tactile paving on the pavement and across the street
        for sy in (784, 856):
            self.op(lambda cv, sy=sy: rect(cv, (592, sy), 22, 10, 0, (0.78, 0.36, 0.32), 0.95), post=True)
            for kx in range(-4, 5):
                for ky in (-2, 2):
                    self.op(lambda cv, kx=kx, ky=ky, sy=sy: disc(cv, (592 + kx * 2.4, sy + ky), 0.6, (0.55, 0.22, 0.2), 0.8), post=True)
        self.op(lambda cv: rect(cv, (592, 790), 22, 5, 0, C_STONE, 0.9), post=True)

    # ---------------------------------------------------------------- the street levels L01 to L05 on Elm Street (y 820)
    def street_levels(self):
        rng = self.rng
        # L02: four cars parked nose to tail on the north kerb, painters' trestles with paint pots and a dust sheet on the south pavement
        for k in range(4):
            p, t = self.frame('L02', 98 + 37 * k, -21)
            self.car(p[0], p[1], t, kit=rng.choice(P.CARS))
        for k, ds in enumerate((150, 186)):
            p, t = self.frame('L02', ds, 38)
            self.op(lambda cv, p=p, t=t: rect(cv, p, 30, 10, ang(t), (0.92, 0.91, 0.86), 0.9), post=True)
            self.add('Barriers', 'PlankTrestles', p[0], p[1], bearing(t), 1.2, None, tag='trestle')
            self.add('Street', 'PotA', p[0] - 14, p[1] + 5, 0, 1.2, [(0.30, 0.55, 0.75)], tag='paint')
            self.add('Street', 'PotA', p[0] + 13, p[1] - 4, 0, 1.2, [(0.88, 0.80, 0.30)], tag='paint')
        # L03: Hill Road: terraces climbing the hill on the north side, steps, a stream under the road, garden apple trees
        n3 = self.node('L03')
        x0 = max(n3[0] + 70, 1340.0)
        self.reserve((x0 + 80, 718), 170, 112)
        for k, (yy, col) in enumerate(((764, C_GRASS), (730, C_GRASS_L), (696, C_GRASS), (662, C_GRASS_L))):
            self.op(lambda cv, yy=yy, col=col, x0=x0: rect(cv, (x0 + 80, yy), 170, 30, 0, col, 1.0))
            self.op(lambda cv, yy=yy, x0=x0: rect(cv, (x0 + 80, yy + 15), 170, 2.5, 0, (0.30, 0.34, 0.26), 0.55))
            self.line_of([(x0 - 4, yy + 16), (x0 + 164, yy + 16)], 'Street', 'BlockWall2', 16, [(0.78, 0.74, 0.66)], skip=[(x0 + 92, yy + 16, 10)], tag='terrace')
        # the steps up the hill (light treads), the handrail posts
        for k in range(8):
            self.op(lambda cv, k=k, x0=x0: rect(cv, (x0 + 92, 772 - k * 14), 14, 6.5, 0, (0.84, 0.82, 0.77), 1.0), post=True)
            self.op(lambda cv, k=k, x0=x0: rect(cv, (x0 + 92, 768.5 - k * 14), 14, 1.4, 0, (0.45, 0.43, 0.40), 0.7), post=True)
        for (ax_, ay_) in ((x0 + 28, 742), (x0 + 142, 706), (x0 + 36, 676), (x0 + 150, 750)):
            self.add('Barriers', 'AppleBough', ax_, ay_ - 8, 180, 1.0, None, tag='apple')
        for (cx_, cy_) in ((x0 + 128, 680), (x0 + 60, 664)):
            self.crown(cx_, cy_, 14)
        # the small stream: out of the gardens, under a little bridge in the road, away to a grate south of it
        sx = x0 + 176
        stream = self.smooth([(sx + 14, 648), (sx + 6, 690), (sx - 4, 735), (sx, 778), (sx + 2, 868), (sx + 10, 905)])
        self.op(lambda cv: stroke(cv, stream, 15, C_BANK, 0.9, cap=True))
        self.op(lambda cv: stroke(cv, stream, 10, C_WATER, 1.0, cap=True))
        self.op(lambda cv: stroke(cv, [(a + 1.5, b) for a, b in stream], 3, C_WATER_D, 0.6))
        for yy in (790, 850):
            self.op(lambda cv, yy=yy: rect(cv, (sx, yy), 18, 6, 0, C_STONE, 1.0), post=True)
        self.op(lambda cv: rect(cv, (sx, 820), 6, 66, 0, (0.36, 0.38, 0.40), 0.35), post=True)
        for (rx_, ry_) in ((sx + 14, 650), (sx - 10, 700), (sx + 12, 740), (sx + 14, 880), (sx - 8, 900)):
            self.add('Plants', 'Reeds', rx_, ry_, rng.uniform(0, 360), 1.8, None, tag='reeds')
        self.add('Street', 'DrainGrate', sx + 10, 908, 0, 1.6)
        self.stream_x = sx
        # L04: Garden Lane: a garden wall with three gates, apple trees behind it, a parked car
        n4 = self.node('L04')
        wx0, wx1 = n4[0] + 82, n4[0] + 172
        gates = [wx0 + 18, wx0 + 45, wx0 + 72]
        self.reserve(((wx0 + wx1) / 2, 730), wx1 - wx0 + 8, 90)
        self.op(lambda cv: rect(cv, ((wx0 + wx1) / 2, 728), wx1 - wx0, 82, 0, C_GRASS, 1.0))
        self.line_of([(wx0, 775), (wx1, 775)], 'Street', 'BlockWall2', 16, [(0.80, 0.76, 0.68)], skip=[(g, 775, 9) for g in gates], tag='wall')
        for g, col in zip(gates, ((0.25, 0.45, 0.70), (0.30, 0.58, 0.40), (0.82, 0.30, 0.26))):
            self.add('Street', 'WallPillar', g - 8, 775, 0, 0.8, [(0.82, 0.78, 0.70)], tag='gate')
            self.add('Street', 'WallPillar', g + 8, 775, 0, 0.8, [(0.82, 0.78, 0.70)], tag='gate')
            self.add('Street', 'PicketFence2', g, 774, 90, 0.7, [col], tag='gate')
            self.op(lambda cv, g=g: rect(cv, (g, 758), 5, 34, 0, C_STONE, 0.95))
        for ax_ in (wx0 + 8, wx0 + 38, wx0 + 66):
            self.add('Barriers', 'AppleBough', ax_, 722 + rng.uniform(-6, 6), 180, 1.0, None, tag='apple')
        p, t = self.frame('L04', 118, 21)
        self.car(p[0], p[1], t)
        # L05: Puddle Lane: a wet lane, four big puddles on the carriageway, cars parked along it
        n5 = self.node('L05')
        for (px_, py_, rx_, ry_, a_) in ((n5[0] - 175, 838, 21, 10, 6), (n5[0] - 138, 806, 17, 9, -10), (n5[0] - 100, 836, 24, 11, 4), (n5[0] - 214, 812, 15, 8, 0)):
            self.op(lambda cv, px_=px_, py_=py_, rx_=rx_, ry_=ry_, a_=a_: (ellipse(cv, (px_, py_), rx_ + 7, ry_ + 5, a_, C_WET, 0.55, blur=2.0),
                                                                          ellipse(cv, (px_, py_), rx_, ry_, a_, C_PUDDLE, 0.95, blur=0.6),
                                                                          ellipse(cv, (px_ - rx_ * 0.25, py_ - ry_ * 0.3), rx_ * 0.5, ry_ * 0.35, a_, (0.75, 0.82, 0.88), 0.7, blur=0.8)), post=True)
        self.op(lambda cv: rect(cv, (n5[0] - 140, 820), 150, 56, 0, C_WET, 0.22), post=True)
        for ds, off in ((-205, 22), (-246, 22), (150, -22)):
            p, t = self.frame('L05', ds, off)
            self.car(p[0], p[1], t)
        for ds in (-150, -230):
            p, t = self.frame('L05', ds, 40)
            self.add('Street', 'TrafficCone', p[0], p[1], 0, 1.1)

    # ---------------------------------------------------------------- the market levels L06 to L10 (Market Street, y 958)
    def market_levels(self):
        rng = self.rng
        # L06: the market square at the west end: a paved plaza across the street, stalls with awnings in two rows, crowds, crates
        sq = (590.0, 958.0)
        plaza = [(468, 902), (700, 902), (700, 1012), (468, 1012)]
        self.op(lambda cv: textured(cv, plaza, (0.80, 0.77, 0.71), 41, amp=(0.03, 0.03, 0.02), cells=(40, 9, 3)))
        for k in range(-5, 6):
            self.op(lambda cv, k=k: stroke(cv, [(468, 957 + k * 10), (700, 957 + k * 10)], 0.7, (0.62, 0.59, 0.54), 0.5))
        for k in range(6):
            self.awning_stall(486 + k * 37, 920, 180)
            self.awning_stall(500 + k * 37, 996, 0)
        for k in range(8):
            self.add('Street', rng.choice(['ProduceCrate', 'Crate', 'CrateStack']), 482 + k * 28 + rng.uniform(-4, 4), rng.choice((934, 983)), rng.uniform(0, 360), 1.2)
        self.crowd((590, 958), 112, 17, 22)
        for k in range(3):
            self.add('Street', 'Bench', 540 + k * 60, 958, 90 if k % 2 else 270, 1.0)
        # L07: three zebra crossings in a row across Market Street, each with its traffic lights; a delivery van with a conveyor to a shop
        n7 = self.node('L07')
        cross = [n7[0] + 100, n7[0] + 138, n7[0] + 176]
        for zx in cross:
            self.op(lambda cv, zx=zx: zebra(cv, (zx, 958), (1, 0), 56, 22.0, 4.2, 3.6), post=True)
            for sy, f in ((922, 180), (994, 0)):
                self.add('Street', 'PedSignal', zx + 13, sy, f, 1.0, None, tag='light')
        for k in range(3):
            self.person(cross[k] + rng.uniform(-6, 6), 919 + rng.uniform(-3, 2))
            self.person(cross[k] + rng.uniform(-6, 6), 998)
        self.car(n7[0] + 214, 975, (1, 0), kit=('Cars', 'Van'))
        self.add('Barriers', 'DeliveryConveyor', n7[0] + 216, 997, 0, 1.0, None, tag='conveyor')
        for k in range(3):
            self.add('Street', 'ProduceCrate', n7[0] + 216, 989 + k * 9, 0, 1.2)
        # L08: the corner shop at Mill Lane: steps, an awning, a roll shutter, crates
        n8 = self.node('L08')
        sh = (n8[0] - 122.0, 1003.0)
        O = P.origin_for('Buildings', 'ShopShutter', sh, 0.0, 1.0)
        self.add('Buildings', 'ShopShutter', O[0], O[1], 0.0, 1.0, [(0.93, 0.86, 0.68), (0.82, 0.30, 0.26), None], tag='shop')
        self.world.occupy(P.footprint('Buildings', 'ShopShutter', O[0], O[1], 0.0, 1.0, pad=0.4))
        for sx_ in (sh[0] - 16, sh[0] + 18):
            self.add('Street', 'Awning', sx_, 1000, 0, 1.2, [(0.82, 0.30, 0.26)], tag='awning')
        for k in range(3):
            self.op(lambda cv, k=k: rect(cv, (sh[0], 1005 + k * 4.5), 26 - k * 2, 4, 0, (0.84, 0.82, 0.77), 1.0), post=True)
        self.add('Barriers', 'RollShutter', sh[0] + 40, 1040, 90, 0.8, None, tag='shutter')
        for (cx_, cy_) in ((sh[0] - 28, 1000), (sh[0] - 40, 1004), (sh[0] + 30, 1000)):
            self.add('Street', 'CrateStack', cx_, cy_, rng.uniform(-20, 20), 1.0)
        self.add('Street', 'VendingRed', sh[0] + 44, 1002, 0)
        # L09: fruit stalls with awnings, the toy shop with trampolines out front, a zebra crossing
        n9 = self.node('L09')
        for k in range(4):
            self.awning_stall(n9[0] + 92 + k * 30, 998, 0, [(0.93, 0.70, 0.22), (0.82, 0.30, 0.26), (0.30, 0.58, 0.40), (0.93, 0.70, 0.22)][k])
        for k in range(8):
            self.add('Street', 'ProduceCrate', n9[0] + 86 + k * 15, 1010, rng.uniform(0, 360), 1.3)
        toy = (n9[0] - 166.0, 1036.0)
        O = P.origin_for('Buildings', 'ShopBoutique', toy, 0.0, 1.0)
        self.add('Buildings', 'ShopBoutique', O[0], O[1], 0.0, 1.0, [(0.98, 0.84, 0.45), (0.90, 0.35, 0.55), (0.35, 0.60, 0.85)], tag='shop')
        self.world.occupy(P.footprint('Buildings', 'ShopBoutique', O[0], O[1], 0.0, 1.0, pad=0.4))
        self.op(lambda cv: rect(cv, (toy[0], 1018), 70, 34, 0, (0.80, 0.77, 0.71), 1.0))
        for tx_ in (toy[0] - 16, toy[0] + 16):
            self.add('Leisure', 'Trampoline', tx_, 1018, 0, 2.0, None, tag='trampoline')
        zx9 = n9[0] - 112
        cross.append(zx9)
        self.op(lambda cv: zebra(cv, (zx9, 958), (1, 0), 56, 22.0, 4.2, 3.6), post=True)
        self.add('Street', 'PedSignal', zx9 + 13, 922, 180)
        self.add('Street', 'PedSignal', zx9 + 13, 994, 0)
        # L10: the main road at rush hour: a queue of cars in both lanes, three crossings, crowds, stalls on the pavements
        n10 = self.node('L10')
        z10 = [n10[0] - 196, n10[0] - 154, n10[0] - 112]
        cross += z10
        for zx in z10:
            self.op(lambda cv, zx=zx: zebra(cv, (zx, 958), (1, 0), 56, 22.0, 4.2, 3.6), post=True)
            for sy, f in ((922, 180), (994, 0)):
                self.add('Street', 'PedSignal', zx + 13, sy, f)
            self.crowd((zx + 4, 909), 16, 6, 4)
            self.crowd((zx + 4, 1005), 16, 6, 4)
        qx = [x for x in range(int(n10[0] - 290), int(n10[0] + 90), 40) if all(abs(x - z) > 24 for z in z10)]
        for x in qx:
            if abs(x - n10[0]) > 75 or True:
                self.car(x + rng.uniform(-3, 3), 973, (1, 0), kit=rng.choice(P.CARS))
        for x in qx:
            self.car(x + 14 + rng.uniform(-3, 3), 943, (-1, 0), kit=rng.choice(P.CARS))
        for k in range(4):
            self.awning_stall(n10[0] - 205 + k * 52, 905, 180)
        # the north strip of Market Street (between it and Elm Street): stalls along the pavement
        for x in range(740, 1500, 46):
            if any(abs(x - z) < 30 for z in cross) or abs(x - self.stream_x) < 24 or x > n10[0] - 215:
                continue
            if rng.random() < 0.7:
                self.awning_stall(x, 905, 180)
            else:
                self.add('Street', rng.choice(['Planter2', 'Bench', 'Bin']), x, 905, 180, 1.0)
        self.op(lambda cv: rect(cv, (1160, 889), 1400, 2.5, 0, (0.45, 0.45, 0.45), 0.0))

    # ---------------------------------------------------------------- C01: the open spot by the house; C02: shop windows
    def court_c01(self):
        c = self.node('C01')
        cc = (c[0] + 4, c[1] - 78)
        self.reserve(cc, 120, 62)
        self.op(lambda cv: rect(cv, cc, 112, 56, 0, (0.70, 0.68, 0.63), 1.0))
        self.op(lambda cv: stroke(cv, [(cc[0] - 50, cc[1] - 22), (cc[0] + 50, cc[1] - 22), (cc[0] + 50, cc[1] + 22), (cc[0] - 50, cc[1] + 22), (cc[0] - 50, cc[1] - 22)], 1.2, C_WHITE, 0.9), post=True)
        self.op(lambda cv: stroke(cv, [(cc[0], cc[1] - 22), (cc[0], cc[1] + 22)], 1.2, C_WHITE, 0.9), post=True)
        self.op(lambda cv: (disc(cv, cc, 10.5, C_WHITE, 0.9), disc(cv, cc, 9.2, (0.70, 0.68, 0.63), 1.0)), post=True)
        for sx in (-1, 1):
            self.box(cc[0] + sx * 52, cc[1], 0.15, 6.0, 2.2, 0, (0.95, 0.95, 0.95), tag='goal', roof='frame')
        self.add('Street', 'Bench', cc[0] - 20, cc[1] + 34, 0)
        self.add('Street', 'Bench', cc[0] + 24, cc[1] - 34, 180)
        self.crown(cc[0] - 66, cc[1] - 14, 16)
        self.crown(cc[0] + 70, cc[1] + 12, 14, blossom=0.8)

    def parade_c02(self):
        """C02, shop windows: the block round the node is a row of shopfronts: the kit's shops built to the pavement of Mill Street
        (their fronts 3 px from the pavement edge, facing the street the market route turns into), each with coloured awnings out over
        the pavement, an A-board, planters and bikes; and a second row of shops back to back with it facing Bay Road."""
        rng = self.rng
        n = self.node('C02')
        road = self.roads['row_e_w0']
        half = self.L.CLASSES[road.cls]['total'] / 2
        y_front = 958.0 + half + 3.0
        kits = [('Buildings', k) for k in ('ShopCafe', 'ShopFlorist', 'ShopBooks', 'ShopFruit', 'ShopNoodle', 'ShopBoutique', 'ShopMart', 'ShopTall', 'ShopKonbini', 'ShopShutter')]
        rng.shuffle(kits)
        x_right = 342.0
        k = 0
        while x_right > 70.0 and k < len(kits):
            kit, name = kits[k]
            k += 1
            w = M.width(kit, name) * PPM
            if x_right - w < 20.0:
                continue
            cx = x_right - w / 2
            tints = P.shop_tints(rng, name)
            O = P.origin_for(kit, name, (cx, y_front), 0.0, 1.0)
            self.add(kit, name, O[0], O[1], 0.0, 1.0, tints, tag='shop')
            self.world.occupy(P.footprint(kit, name, O[0], O[1], 0.0, 1.0, pad=0.3))
            P.shop_awnings(self.items, (cx, y_front), 0.0, w, tints[1])
            self.add('Street', 'SignBoardA', cx + rng.uniform(-w * 0.3, w * 0.3), y_front - 10, rng.uniform(-25, 25), 1.0, tag='board')
            if rng.random() < 0.6:
                self.add('Street', rng.choice(['Planter1', 'PotGroup', 'Bicycle']), cx + w * 0.38, y_front - 8, 0, 1.0, tag='bit')
            x_right -= w + 2.0
        # the shops' back yards (paved) and a back row facing Bay Road
        self.op(lambda cv: rect(cv, (200, 1086), 360, 24, 0, (0.74, 0.72, 0.67), 1.0))
        for bx in (60, 130, 196, 262, 330):
            self.add('Street', rng.choice(['Bin', 'BinPair', 'CrateStack', 'Pallet']), bx + rng.uniform(-8, 8), 1086, rng.uniform(0, 360), 1.0, tag='bit')


# ------------------------------------------------------------------ all the pieces together
from town_map_sets_nature import NatureSets      # noqa: E402  (they import the helpers above)
from town_map_sets_works import WorksSets        # noqa: E402


class Sets(Base, TownSets, NatureSets, WorksSets):
    def build(self):
        self.works()
        self.town()
        self.nature()
        return self.items
