# Where the town map's models stand (pure Python + numpy, no bpy): houses and shops along the roads' frontages, fences and
# hedges along the lots, trees in the gardens and along the streets, cars on the kerbs, lamps, bins. Everything is
# deterministic (seeded) and comes out as a list of Items in CORE px (x east, y down); town_map_scene.py turns them into
# Blender objects, and town_map_ground.py paints the lots (lawns, paths, drives) under them.
#
# A frontage walk: along each side of a road, a building is dealt from its zone's deck, its front-centre is put on the lot's
# front line, it faces the road, and it is kept only if its footprint is free (not on a road, not in another zone, not on
# another building). So the streets can curve, fan out and meet at any angle and the houses follow.
import math, random, zlib
import numpy as np
from PIL import Image, ImageDraw
import town_map_raster as R
import town_map_graph as G
import town_map_models as M

CELL = 4                                   # px per occupancy cell (0.5 m)
PPM = 8.0
GW, GH = R.IMG_W // CELL, R.IMG_H // CELL


class Item:
    """One model to place: a kit model at a core-px position, facing a compass bearing (0 = up the picture, 90 = right)."""
    __slots__ = ('kit', 'name', 'x', 'y', 'face', 'scale', 'tints', 'z', 'tag', 'params')

    def __init__(self, kit, name, x, y, face=0.0, scale=1.0, tints=None, z=0.0, tag='', params=None):
        self.kit, self.name, self.x, self.y, self.face, self.scale, self.tints, self.z, self.tag, self.params = kit, name, x, y, face, scale, tints, z, tag, params


# ------------------------------------------------------------------ colours (sRGB) for the tinted parts (1 wall, 2 trim/door, 3 roof)
ROOFS_WARM = [(0.80, 0.42, 0.28), (0.88, 0.52, 0.27), (0.72, 0.36, 0.26), (0.82, 0.47, 0.34), (0.76, 0.40, 0.24), (0.86, 0.58, 0.34)]
ROOFS_COOL = [(0.34, 0.38, 0.46), (0.42, 0.44, 0.48), (0.28, 0.30, 0.35), (0.46, 0.50, 0.52), (0.31, 0.37, 0.36), (0.38, 0.42, 0.50)]
WALLS = [(0.95, 0.91, 0.80), (0.93, 0.93, 0.90), (0.95, 0.86, 0.66), (0.93, 0.80, 0.68), (0.82, 0.86, 0.88), (0.80, 0.88, 0.93),
         (0.85, 0.91, 0.80), (0.89, 0.79, 0.73), (0.97, 0.95, 0.88), (0.96, 0.84, 0.74)]
DOORS = [(0.80, 0.22, 0.17), (0.25, 0.45, 0.65), (0.25, 0.55, 0.35), (0.90, 0.70, 0.20), (0.45, 0.30, 0.20), (0.90, 0.90, 0.88), (0.55, 0.30, 0.55)]
AWNINGS = [(0.82, 0.30, 0.26), (0.25, 0.50, 0.62), (0.30, 0.58, 0.40), (0.93, 0.70, 0.22), (0.85, 0.45, 0.20), (0.55, 0.35, 0.60)]
CAR_PAINT = [(0.80, 0.47, 0.35), (0.32, 0.58, 0.59), (0.47, 0.60, 0.72), (0.87, 0.69, 0.32), (0.55, 0.65, 0.50), (0.85, 0.85, 0.85), (0.80, 0.25, 0.22), (0.25, 0.28, 0.34)]


# ------------------------------------------------------------------ the occupancy world
class World:
    def __init__(self, L, B, masks):
        self.L, self.B = L, B

        def down(m):
            return m.reshape(GH, CELL, GW, CELL).any(axis=(1, 3))
        self.road = down(masks.pave_c)                 # carriageways and pavements
        self.path = down(masks.path | masks.board)
        self.built = np.zeros((GH, GW), bool)          # buildings and big things (with their margin)
        self.zone = np.zeros((GH, GW), np.uint8)       # 0 = residential (the default), else a kind from self.kinds
        self.kinds = {}                                # code -> kind
        code = 1
        for name, a in L.AREAS.items():
            kind = a.get('kind', name)
            c = None
            for k, v in self.kinds.items():
                if v == kind:
                    c = k
            if c is None:
                c = code
                self.kinds[c] = kind
                code += 1
            m = self.poly_cells(a['poly'])
            if m is not None:
                x0, y0, arr = m
                self.zone[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]][arr] = c
        self.rng = random.Random(20250611)

    @staticmethod
    def to_cell(p):
        return ((p[0] + R.ORIGIN[0]) / CELL, (p[1] + R.ORIGIN[1]) / CELL)

    def poly_cells(self, pts):
        cp = [self.to_cell(p) for p in pts]
        xs = [p[0] for p in cp]; ys = [p[1] for p in cp]
        x0, y0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1)
        x1, y1 = min(GW, int(max(xs)) + 2), min(GH, int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            return None
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).polygon([(p[0] - x0, p[1] - y0) for p in cp], fill=255)
        return x0, y0, np.asarray(im) > 0

    def kind_at(self, p):
        cx, cy = int((p[0] + R.ORIGIN[0]) / CELL), int((p[1] + R.ORIGIN[1]) / CELL)
        if not (0 <= cx < GW and 0 <= cy < GH):
            return 'out'
        c = self.zone[cy, cx]
        return 'residential' if c == 0 else self.kinds[c]

    def free(self, pts, kinds=('residential',), roads=True):
        """True if the polygon touches no road, no building and only the allowed kinds of zone."""
        m = self.poly_cells(pts)
        if m is None:
            return False
        x0, y0, a = m
        h, w = a.shape
        if x0 <= 1 or y0 <= 1 or x0 + w >= GW - 1 or y0 + h >= GH - 1:
            return False
        reg_b = self.built[y0:y0 + h, x0:x0 + w] | self.path[y0:y0 + h, x0:x0 + w]
        if roads:
            reg_b = reg_b | self.road[y0:y0 + h, x0:x0 + w]
        if (reg_b & a).any():
            return False
        z = self.zone[y0:y0 + h, x0:x0 + w][a]
        allowed = [c for c, k in self.kinds.items() if k in kinds]
        if 'residential' in kinds:
            allowed.append(0)
        return bool(np.isin(z, allowed).all())

    def occupy(self, pts):
        m = self.poly_cells(pts)
        if m is None:
            return
        x0, y0, a = m
        self.built[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a

    def is_built(self, p):
        """True if the point is on something the set pieces or the houses took (a building, a bridge, the railway corridor)."""
        cx, cy = int((p[0] + R.ORIGIN[0]) / CELL), int((p[1] + R.ORIGIN[1]) / CELL)
        return 0 <= cx < GW and 0 <= cy < GH and bool(self.built[cy, cx])

    def free_cells_frac(self, cx, cy, r):
        """Fraction of the cells in a square of half-size r px around (cx, cy) that are neither road nor building."""
        x0, y0 = int((cx + R.ORIGIN[0] - r) / CELL), int((cy + R.ORIGIN[1] - r) / CELL)
        x1, y1 = int((cx + R.ORIGIN[0] + r) / CELL) + 1, int((cy + R.ORIGIN[1] + r) / CELL) + 1
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(GW, x1), min(GH, y1)
        if x1 <= x0 or y1 <= y0:
            return 0.0
        blocked = self.built[y0:y1, x0:x1] | self.road[y0:y1, x0:x1] | self.path[y0:y1, x0:x1]
        return 1.0 - float(blocked.mean())


# ------------------------------------------------------------------ footprints
def axes(face):
    """The model's local x axis and depth axis in core px (y down) when it faces the compass bearing `face`."""
    b = math.radians(face)
    return (-math.cos(b), -math.sin(b)), (-math.sin(b), math.cos(b))


def footprint(kit, name, x, y, face, scale=1.0, pad=0.0):
    """The footprint polygon (core px) of a model whose origin is at (x, y) facing `face`; pad in metres."""
    x0, x1, y0, y1, _ = M.bounds(kit, name)
    ex, ey = axes(face)
    k = PPM * scale
    pts = []
    for lx, ly in ((x0 - pad, y0 - pad), (x1 + pad, y0 - pad), (x1 + pad, y1 + pad), (x0 - pad, y1 + pad)):
        pts.append((x + (lx * k) * ex[0] + (ly * k) * ey[0], y + (lx * k) * ex[1] + (ly * k) * ey[1]))
    return pts


def origin_for(kit, name, front_pt, face, scale=1.0, along=0.0):
    """The origin that puts a model's front (its -Y face) at front_pt and its middle `along` metres along the front line."""
    x0, x1, y0, y1, _ = M.bounds(kit, name)
    ex, ey = axes(face)
    k = PPM * scale
    mid = (x0 + x1) / 2
    return (front_pt[0] - (mid - along) * k * ex[0] - y0 * k * ey[0], front_pt[1] - (mid - along) * k * ex[1] - y0 * k * ey[1])


def to_world(kit, name, O, face, lx, ly, scale=1.0):
    """A point given in a model's local metres, in core px."""
    ex, ey = axes(face)
    k = PPM * scale
    return (O[0] + lx * k * ex[0] + ly * k * ey[0], O[1] + lx * k * ex[1] + ly * k * ey[1])


# ------------------------------------------------------------------ the decks
class Deck:
    """Models dealt at random with weights, never the same twice in a row."""

    def __init__(self, entries, rng):
        self.entries, self.rng = entries, rng
        self.last = None

    def draw(self):
        e = None
        for _ in range(8):
            e = self.rng.choices(self.entries, weights=[w for _, w in self.entries], k=1)[0][0]
            if e != self.last:
                break
        self.last = e
        return e


def house_tints(rng, name):
    roof = rng.choice(ROOFS_WARM if rng.random() < 0.6 else ROOFS_COOL)
    wall = rng.choice(WALLS)
    door = rng.choice(DOORS)
    return [wall, door, roof]


SHOP_ROOFS = [(0.62, 0.42, 0.35), (0.50, 0.54, 0.60), (0.72, 0.62, 0.50), (0.46, 0.52, 0.48), (0.68, 0.38, 0.31), (0.78, 0.70, 0.60)]


def shop_tints(rng, name):
    return [rng.choice(WALLS), rng.choice(AWNINGS), rng.choice(SHOP_ROOFS)]


HOUSES = [(('Buildings', 'HouseGable'), 30), (('Buildings', 'HouseLong'), 10), (('Buildings', 'Bungalow'), 32), (('Buildings', 'HouseFlat'), 12),
          (('Buildings', 'HouseLeanTo'), 6), (('Buildings', 'HouseCarport'), 10)]
SHOPS = [(('Buildings', 'ShopFruit'), 10), (('Buildings', 'ShopShutter'), 7), (('Buildings', 'ShopMart'), 8), (('Buildings', 'ShopCafe'), 10), (('Buildings', 'ShopBooks'), 9),
         (('Buildings', 'ShopFlorist'), 9), (('Buildings', 'ShopNoodle'), 9), (('Buildings', 'ShopTall'), 5), (('Buildings', 'ShopBoutique'), 6), (('Buildings', 'ShopKonbini'), 5)]
FLATS = [(('Buildings', 'Apartment'), 10), (('Buildings', 'HouseFlat'), 3)]


# ------------------------------------------------------------------ the frontage walk
def side_normal(t, side):
    """Unit vector pointing away from the road centre on `side` (+1 the right of the direction of travel)."""
    return (side * -t[1], side * t[0])


class Lot:
    """A lot, for the ground painter: a quad from the pavement to the back, the door's path and the house's front."""
    __slots__ = ('poly', 'kind', 'path', 'drive', 'seed')

    def __init__(self, poly, kind, path, seed):
        self.poly, self.kind, self.path, self.seed = poly, kind, path, seed
        self.drive = None


def frontage(world, L, B, items, lots, rng, skip_roads=()):
    decks = {'residential': (Deck(HOUSES, rng), (3, 7), (2, 9), house_tints),
             'market': (Deck(SHOPS, rng), (1, 4), (0, 3), shop_tints),
             'flats': (Deck(FLATS, rng), (8, 12), (10, 20), house_tints)}
    graph = B['graph']
    for r in graph.roads:
        if r.cls in ('path', 'board') or r.id in skip_roads:
            continue
        cls = L.CLASSES[r.cls]
        curve = G.resample(r.curve, 4.0)
        total = G.poly_length(curve)
        for side in (1, -1):
            s = 10.0
            while s < total - 10:
                p, t = G.point_at(curve, s)
                nrm = side_normal(t, side)
                zk = world.kind_at((p[0] + nrm[0] * (cls['total'] / 2 + 14), p[1] + nrm[1] * (cls['total'] / 2 + 14)))
                if zk not in decks:
                    s += 8.0
                    continue
                deck, setback, gap, tint_fn = decks[zk]
                kit, name = deck.draw()
                scale = rng.uniform(0.97, 1.06) if zk == 'residential' else 1.0
                w = M.width(kit, name) * PPM * scale
                sb = rng.uniform(*setback)
                d = cls['total'] / 2 + sb
                pc, tc = G.point_at(curve, min(total, s + w / 2))
                nc = side_normal(tc, side)
                front = (pc[0] + nc[0] * d, pc[1] + nc[1] * d)
                face = math.degrees(math.atan2(-nc[0], nc[1]))       # looking at the road
                O = origin_for(kit, name, front, face, scale)
                fp = footprint(kit, name, O[0], O[1], face, scale, pad=0.25)
                if world.free(fp, (zk,)):
                    tints = tint_fn(rng, name)
                    items.append(Item(kit, name, O[0], O[1], face, scale, tints, tag=zk))
                    world.occupy(fp)
                    if zk == 'market':
                        shop_awnings(items, front, face, w, tints[1])
                    # the lot: from the pavement edge back past the house
                    g = rng.uniform(*gap)
                    half = (w + g) / 2
                    ex, ey = axes(face)
                    base = (pc[0] + nc[0] * cls['total'] / 2, pc[1] + nc[1] * cls['total'] / 2)
                    dep = sb + M.depth(kit, name) * PPM * scale + 14
                    q = [(base[0] - ex[0] * half, base[1] - ex[1] * half), (base[0] + ex[0] * half, base[1] + ex[1] * half)]
                    q += [(q[1][0] + ey[0] * dep, q[1][1] + ey[1] * dep), (q[0][0] + ey[0] * dep, q[0][1] + ey[1] * dep)]
                    door = to_world(kit, name, O, face, M.door_x(kit, name), M.bounds(kit, name)[2], scale)
                    lots.append(Lot(q, zk, (base, door), rng.randrange(1 << 30)))
                    # a fence or a hedge along the front of a house lot, with a gap for the gate
                    if zk != 'market':
                        fence_or_hedge(items, rng, base, ex, ey, face, w + g, door)
                        furniture(items, rng, base, ex, ey, face, w, door)
                    s += w + g
                else:
                    s += 9.0


def shop_awnings(items, front, face, w, colour):
    """Two awnings in the shop's colour out over the pavement in front of a shopfront (the front-centre point `front`, facing `face`)."""
    ex, ey = axes(face)
    for u in (-0.26, 0.26):
        items.append(Item('Street', 'Awning', front[0] + ex[0] * w * u, front[1] + ex[1] * w * u, face, 2.0, [colour], tag='awning'))


def road_samples(L, B, step=6.0):
    """The roads' centre lines sampled every `step` px: points, unit tangents and half widths (numpy), for nearest-road queries."""
    pts, tans, hws = [], [], []
    for r in B['graph'].roads:
        if r.cls in ('path', 'board'):
            continue
        curve = G.resample(r.curve, step)
        hw = L.CLASSES[r.cls]['total'] / 2
        for i in range(len(curve)):
            a = curve[max(0, i - 1)]; b = curve[min(len(curve) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            n = math.hypot(tx, ty) or 1.0
            pts.append(curve[i]); tans.append((tx / n, ty / n)); hws.append(hw)
    return np.array(pts, np.float32), np.array(tans, np.float32), np.array(hws, np.float32)


def infill(world, L, B, items, lots, rng, attempts=9000, reach=60.0):
    """Houses in the gaps the frontage walk left (corners, wedges, the ends of blocks): at random free spots within `reach` px
    of a pavement, turned to face the nearest road."""
    P, T, HW = road_samples(L, B)
    deck = Deck(HOUSES, rng)
    free = ~(world.road | world.built | world.path) & (world.zone == 0)
    cells = np.argwhere(free)
    if len(cells) == 0:
        return 0
    order = rng.sample(range(len(cells)), min(len(cells), attempts))
    n_new = 0
    for ci in order:
        cy, cx = cells[ci]
        if not free[cy, cx] or world.built[cy, cx]:
            continue
        x, y = (cx + 0.5) * CELL - R.ORIGIN[0], (cy + 0.5) * CELL - R.ORIGIN[1]
        d = np.hypot(P[:, 0] - x, P[:, 1] - y)
        k = int(np.argmin(d))
        gap = float(d[k] - HW[k])
        if gap < 7 or gap > reach:
            continue
        t = (float(T[k][0]), float(T[k][1]))
        nrm0 = ((x - float(P[k][0])), (y - float(P[k][1])))
        side = 1 if (-t[1] * nrm0[0] + t[0] * nrm0[1]) > 0 else -1
        nc = side_normal(t, side)
        kit, name = deck.draw()
        scale = rng.uniform(0.96, 1.08)
        face = math.degrees(math.atan2(-nc[0], nc[1]))
        # the front of the house at the candidate, centred on it
        O = origin_for(kit, name, (x, y), face, scale)
        fp = footprint(kit, name, O[0], O[1], face, scale, pad=0.25)
        if not world.free(fp, ('residential',)):
            continue
        items.append(Item(kit, name, O[0], O[1], face, scale, house_tints(rng, name), tag='residential'))
        world.occupy(fp)
        n_new += 1
        w = M.width(kit, name) * PPM * scale
        ex, ey = axes(face)
        half = w / 2 + rng.uniform(2, 8)
        base = (x - ey[0] * min(gap, 9.0), y - ey[1] * min(gap, 9.0))
        dep = min(gap, 9.0) + M.depth(kit, name) * PPM * scale + 12
        q = [(base[0] - ex[0] * half, base[1] - ex[1] * half), (base[0] + ex[0] * half, base[1] + ex[1] * half)]
        q += [(q[1][0] + ey[0] * dep, q[1][1] + ey[1] * dep), (q[0][0] + ey[0] * dep, q[0][1] + ey[1] * dep)]
        door = to_world(kit, name, O, face, M.door_x(kit, name), M.bounds(kit, name)[2], scale)
        lots.append(Lot(q, 'residential', (base, door), rng.randrange(1 << 30)))
        if rng.random() < 0.5:
            fence_or_hedge(items, rng, base, ex, ey, face, w + 8, door)
    return n_new


def fence_or_hedge(items, rng, base, ex, ey, face, length, door):
    roll = rng.random()
    if roll < 0.42:
        kit, name, step, ph = 'Street', 'PicketFence2', 16.0, 2.0
        tints = [(0.96, 0.94, 0.88)]
    elif roll < 0.72:
        kit, name, step, ph = 'Plants', 'HedgeBlock2', 16.0, 2.0
        tints = None
    else:
        return
    n = max(1, int(length // step))
    start = -length / 2 + step / 2
    # the gate: the piece nearest the door's position along the front is left out
    doorpos = ((door[0] - base[0]) * ex[0] + (door[1] - base[1]) * ex[1])
    for i in range(n):
        u = start + i * step + (length - n * step) / 2
        if abs(u - doorpos) < step * 0.8:
            continue
        # fence pieces tile along their local X; face the road like the house
        pos = (base[0] + ex[0] * u + ey[0] * 1.5, base[1] + ex[1] * u + ey[1] * 1.5)
        items.append(Item(kit, name, pos[0], pos[1], face, 1.0, tints, tag='fence'))


def furniture(items, rng, base, ex, ey, face, w, door):
    """A bin, a bike, a pot by the door; sometimes."""
    if rng.random() < 0.35:
        u = rng.uniform(-w * 0.45, w * 0.45)
        d = rng.uniform(8, 20)
        pos = (base[0] + ex[0] * u + ey[0] * d, base[1] + ex[1] * u + ey[1] * d)
        kit, name = rng.choice([('Street', 'Bin'), ('Street', 'BinPair'), ('Street', 'Bicycle'), ('Street', 'PotGroup')])
        items.append(Item(kit, name, pos[0], pos[1], face + rng.uniform(-30, 30), 1.0, None, tag='bit'))


# ------------------------------------------------------------------ cars on the kerbs
CARS = [('Cars', 'Hatch'), ('Cars', 'Wagon'), ('Cars', 'Van'), ('Cars', 'Pickup'), ('Cars', 'Fourby')]


def kerb_cars(world, L, B, masks, items, rng, density=0.16, classes=('street', 'lane')):
    graph = B['graph']
    for r in graph.roads:
        if r.cls not in classes:
            continue
        cls = L.CLASSES[r.cls]
        curve = G.resample(r.curve, 4.0)
        total = G.poly_length(curve)
        for side in (1, -1):
            s = rng.uniform(40, 120)
            while s < total - 50:
                if rng.random() > density:
                    s += rng.uniform(40, 90)
                    continue
                p, t = G.point_at(curve, s)
                nrm = side_normal(t, side)
                off = cls['road'] / 2 - 10
                pos = (p[0] + nrm[0] * off, p[1] + nrm[1] * off)
                px, py = int(pos[0] + R.ORIGIN[0]), int(pos[1] + R.ORIGIN[1])
                if not (0 <= px < R.IMG_W and 0 <= py < R.IMG_H) or masks.junction[max(0, py - 34):py + 34, max(0, px - 34):px + 34].any():
                    s += 40
                    continue
                kit, name = rng.choice(CARS)
                face = math.degrees(math.atan2(t[0], -t[1])) + (0 if rng.random() < 0.5 else 180)
                items.append(Item(kit, name, pos[0], pos[1], face, 1.0, None, tag='car'))
                s += M.depth(kit, name) * PPM + rng.uniform(16, 110)


# ------------------------------------------------------------------ trees
# Round crowns (a lumpy ball, see town_map_scene._blob) in muted greens, with a few cherry-blossom pinks, are most of the town's
# trees; the kit's own conifers, birches and pines stand among them for variety.
GREENS = [(0.34, 0.50, 0.28), (0.38, 0.54, 0.30), (0.30, 0.46, 0.27), (0.42, 0.57, 0.32), (0.36, 0.52, 0.31), (0.29, 0.43, 0.26), (0.45, 0.58, 0.33)]
BLOSSOMS = [(0.93, 0.70, 0.75), (0.90, 0.62, 0.71), (0.95, 0.78, 0.81)]
AUTUMNS = [(0.80, 0.58, 0.28), (0.72, 0.47, 0.24)]
KIT_TREES = [(('Plants', 'Birch'), 10), (('Plants', 'GardenPine'), 6), (('Plants', 'ConiferSmall'), 5), (('Plants', 'BroadleafLarge'), 8), (('Plants', 'ConiferMid'), 3)]
TREES = KIT_TREES                       # (kept for the callers that deal from a deck)
STREET_TREES = KIT_TREES


def crown(x, y, rng, r=None, blossom=0.07, autumn=0.02, tag='tree'):
    """A round tree crown of radius r px (default 14 to 26) as a custom item the scene turns into a lumpy ball."""
    r = r if r is not None else rng.uniform(12, 21)
    roll = rng.random()
    col = rng.choice(BLOSSOMS) if roll < blossom else (rng.choice(AUTUMNS) if roll < blossom + autumn else rng.choice(GREENS))
    w = 2 * r / PPM
    h = w * rng.uniform(0.78, 1.0)
    return Item('custom', 'box', x, y, 0.0, 1.0, col, 1.4 + 0.3 * w, tag, dict(w=w, d=w * rng.uniform(0.9, 1.08), h=h, roof='blob%d' % rng.randrange(8)))


def tree_item(x, y, rng, r=None, kit_share=0.14, blossom=0.07):
    """A tree: mostly a crown, sometimes a kit tree (birch, pine, conifer) for variety."""
    if rng.random() < kit_share:
        kit, name = rng.choices(KIT_TREES, weights=[w for _, w in KIT_TREES], k=1)[0][0]
        return Item(kit, name, x, y, rng.uniform(0, 360), rng.uniform(1.0, 1.3), None, tag='tree')
    return crown(x, y, rng, r, blossom)


def garden_trees(world, lots, items, rng, kinds=('residential',)):
    """A tree in the back yard of most lots and a smaller one by the side of some: the picture's quiet greens."""
    placed = []
    for lot in lots:
        if lot.kind != 'residential':
            continue
        q = lot.poly
        for tries in range(2):
            if rng.random() > (0.7 if tries == 0 else 0.3):
                continue
            r = rng.uniform(11, 19)
            for k in range(6):
                u = rng.random(); v = rng.random()
                # a random point in the lot's quad (bilinear)
                x = (1 - u) * ((1 - v) * q[0][0] + v * q[3][0]) + u * ((1 - v) * q[1][0] + v * q[2][0])
                y = (1 - u) * ((1 - v) * q[0][1] + v * q[3][1]) + u * ((1 - v) * q[1][1] + v * q[2][1])
                rr = r * 0.62
                pts = [(x - rr, y - rr), (x + rr, y - rr), (x + rr, y + rr), (x - rr, y + rr)]
                if not world.free(pts, kinds):
                    continue
                if any((x - px) ** 2 + (y - py) ** 2 < (0.55 * (r + pr)) ** 2 for px, py, pr in placed):
                    continue
                placed.append((x, y, r))
                items.append(tree_item(x, y, rng, r))
                world.occupy(pts)
                break


def street_trees(world, L, B, masks, items, rng, skip_routes=True):
    """Trees on the pavements of the streets (round crowns, a kit tree now and then); the streets that carry a route get fewer."""
    graph = B['graph']
    route_roads = set()
    for ids in B['used'].values():
        route_roads.update(ids)
    for r in graph.roads:
        if r.cls in ('path', 'board'):
            continue
        cls = L.CLASSES[r.cls]
        share = 0.35 if r.id in route_roads else 0.85
        curve = G.resample(r.curve, 4.0)
        total = G.poly_length(curve)
        for side in (1, -1):
            s = rng.uniform(20, 60)
            while s < total - 20:
                p, t = G.point_at(curve, s)
                nrm = side_normal(t, side)
                off = cls['road'] / 2 + cls['pave'] * 0.5
                pos = (p[0] + nrm[0] * off, p[1] + nrm[1] * off)
                px, py = int(pos[0] + R.ORIGIN[0]), int(pos[1] + R.ORIGIN[1])
                if world.kind_at(pos) in ('site', 'station', 'sea', 'sand', 'wood', 'far', 'school', 'reserve') or world.is_built(pos):
                    s += rng.uniform(46, 84)
                    continue
                if 0 <= px < R.IMG_W and 0 <= py < R.IMG_H and not masks.junction[max(0, py - 26):py + 26, max(0, px - 26):px + 26].any() and rng.random() < share:
                    items.append(tree_item(pos[0], pos[1], rng, rng.uniform(9, 14), kit_share=0.08, blossom=0.1))
                s += rng.uniform(46, 84)


def fill_pockets(world, L, items, rng, kinds=('residential',), step=9.0, min_free=0.9, tries_per=1):
    """The corners and middles of the blocks that the houses left empty: round crowns where there is room for them, shrubs and
    hedges in the narrow bits, so that no block is left as plain lawn (the reference's blocks are full of small things)."""
    free = ~(world.road | world.built | world.path)
    zmask = np.zeros_like(free)
    codes = [0] if 'residential' in kinds else []
    codes += [c for c, k in world.kinds.items() if k in kinds]
    zmask = np.isin(world.zone, codes)
    free &= zmask
    # distance to the nearest blocked cell, in cells, by repeated erosion (cheap: the cells are 4 px)
    dist = np.zeros(free.shape, np.uint8)
    cur = free.copy()
    for k in range(1, 12):
        cur = R.erode_disc(cur, 1)
        if not cur.any():
            break
        dist[cur] = k
    cells = np.argwhere(dist >= 2)
    if len(cells) == 0:
        return 0
    order = list(range(len(cells)))
    rng.shuffle(order)
    placed = []
    n = 0
    for ci in order[:24000]:
        cy, cx = cells[ci]
        d = int(dist[cy, cx])
        x, y = (cx + 0.5) * CELL - R.ORIGIN[0], (cy + 0.5) * CELL - R.ORIGIN[1]
        if world.built[cy, cx]:
            continue
        # the crown that fits: radius up to ~ 3.2 x the free distance, between 9 and 26 px
        r = min(19.0, d * CELL * 1.5)
        if r < 8:
            continue
        r = rng.uniform(max(8.0, r * 0.7), r)
        if any((x - px) ** 2 + (y - py) ** 2 < (0.6 * (r + pr)) ** 2 for px, py, pr in placed):
            continue
        rr = r * 0.62
        pts = [(x - rr, y - rr), (x + rr, y - rr), (x + rr, y + rr), (x - rr, y + rr)]
        if not world.free(pts, kinds):
            continue
        if r >= 12:
            items.append(tree_item(x, y, rng, r, kit_share=0.08))
        else:
            kit, name = rng.choice([('Plants', 'BushRound'), ('Plants', 'BushWide'), ('Plants', 'ShrubFlowering')])
            items.append(Item(kit, name, x, y, rng.uniform(0, 360), rng.uniform(1.2, 1.8), None, tag='bush'))
        placed.append((x, y, r))
        world.occupy(pts)
        n += 1
    return n


def lamps(world, L, B, items, rng):
    graph = B['graph']
    for r in graph.roads:
        if r.cls not in ('street', 'main'):
            continue
        cls = L.CLASSES[r.cls]
        curve = G.resample(r.curve, 4.0)
        total = G.poly_length(curve)
        side = 1 if zlib.crc32(r.id.encode()) % 2 == 0 else -1
        s = 60.0
        while s < total - 40:
            p, t = G.point_at(curve, s)
            n = side_normal(t, side)
            off = cls['road'] / 2 + 3
            pos = (p[0] + n[0] * off, p[1] + n[1] * off)
            # the lamp's arm reaches its local +X: turn it over the road (local +X = -n)
            face = math.degrees(math.atan2(n[1], n[0]))
            if not world.is_built(pos):
                items.append(Item('Street', 'StreetLamp', pos[0], pos[1], face, 1.0, None, tag='lamp'))
            s += 130.0


def generate(L, B, masks, sets_cls=None):
    """The town's models. The set pieces (town_map_sets: the home, the level scenes, the park, the school, the site, the station,
    the beach) are laid out first so that they keep their ground; then the frontage walk, the infill and the trees fill the rest."""
    world = World(L, B, masks)
    rng = random.Random(7)
    items, lots = [], []
    sets = None
    if sets_cls is not None:
        sets = sets_cls(L, B, world, masks)
        items += sets.build()
    frontage(world, L, B, items, lots, rng)
    infill(world, L, B, items, lots, rng)
    infill(world, L, B, items, lots, rng, attempts=12000, reach=90.0)
    garden_trees(world, lots, items, rng)
    fill_pockets(world, L, items, rng)
    street_trees(world, L, B, masks, items, rng)
    kerb_cars(world, L, B, masks, items, rng)
    lamps(world, L, B, items, rng)
    return world, items, lots, sets
