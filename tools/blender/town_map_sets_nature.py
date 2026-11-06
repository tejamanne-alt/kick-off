# The park (L19 to L23, C05), the beach (L11 to L14, C03), the school's grounds and the country round the town.
import math, random, zlib
import town_map_graph as G
import town_map_place as P
from town_map_sets import (PPM, C_STONE, C_PAVE, C_WATER, C_WATER_D, C_BANK, C_WHITE, C_GRASS, C_GRASS_D, C_GRASS_L, C_FLOWERS,
                           ang, bearing, fill, rect, disc, stroke, ellipse, textured, zebra)


class NatureSets:
    def nature(self):
        self.park()
        self.beach()
        self.country()

    # ---------------------------------------------------------------- the park
    def park(self):
        rng = self.rng
        L = self.L
        poly = L.AREAS['park']['poly']
        gate = self.B['graph'].nodes['pk_g']
        # the fence round it with the gate where Park Lane ends; the pillars; lamps and benches along the path
        gap = [(gate[0], 342, 20)]
        self.line_of([(-260, 342), (1488, 342)], 'Street', 'PicketFence2', 16, [(0.34, 0.47, 0.38)], skip=gap + [(420, 342, 6)], tag='parkfence')
        self.line_of([(-260, 77), (1488, 77)], 'Street', 'PicketFence2', 16, [(0.34, 0.47, 0.38)], tag='parkfence')
        for sx in (-1, 1):
            self.add('Works', 'GatePillar', gate[0] + sx * 18, 342, 0, 0.7, [(0.92, 0.88, 0.80)], tag='gate')
        # L19 (from home, in at the gate): dogs, a net tunnel, a bench, and the fallen tree before the bandstand (its stop)
        n = self.node('L19')
        for dx, dy in ((-96, -14), (-112, 8), (-80, 24), (-86, -34), (-128, -22)):
            self.add('Animals', 'Dog', n[0] + dx, n[1] + dy, rng.uniform(0, 360), 3.2, None, tag='dog')
        self.add('Barriers', 'NetTunnel', n[0] + 36, n[1] - 62, 20, 1.7, None, tag='nettunnel')
        self.add('Barriers', 'FallenTrunk', n[0] + 58, n[1] - 114, 250, 1.6, None, tag='trunk')
        self.add('Street', 'Bench', n[0] - 40, n[1] + 40, 0)
        self.add('Street', 'Bin', n[0] - 56, n[1] + 40, 0)
        self.op(lambda cv: ellipse(cv, (n[0] - 100, n[1] + 4), 48, 30, 0, C_GRASS_L, 0.55, blur=3.0))
        # L20 (from the bandstand): three fountains on paved plazas, trampolines, a play tower (before the park cafe, its stop)
        n = self.node('L20')
        for k, (dx, dy) in enumerate(((-92, 50), (0, 80), (92, 50))):
            c = (n[0] + dx, n[1] + dy)
            self.op(lambda cv, c=c: (disc(cv, c, 36, (0.74, 0.72, 0.67), 1.0), disc(cv, c, 32, (0.84, 0.82, 0.77), 1.0)))
            self.add('Leisure', 'Fountain', c[0], c[1], 0, 4.0, None, tag='fountain')
            for j in range(6):
                a = j * math.pi / 3 + 0.4
                self.op(lambda cv, c=c, a=a, j=j: disc(cv, (c[0] + math.cos(a) * 41, c[1] + math.sin(a) * 41), 3.2, C_FLOWERS[j % 5], 0.95))
        for dx, dy in ((-84, -76), (-12, -100), (50, -88)):
            self.add('Leisure', 'Trampoline', n[0] + dx, n[1] + dy, 0, 2.4, None, tag='trampoline')
            self.op(lambda cv, c=(n[0] + dx, n[1] + dy): disc(cv, c, 19, (0.62, 0.52, 0.40), 0.6))
        self.add('Barriers', 'PlayTower', n[0] - 36, n[1] - 50, 180, 2.0, None, tag='playtower')
        # L21 (from the park cafe): the playground: a stream with rope swings over it, trampolines, a climbing frame, a net tunnel (before
        # the boathouse, its stop)
        n = self.node('L21')
        sx = n[0] + 40
        stream = self.smooth([(sx + 10, 78), (sx - 6, 130), (sx + 6, 178), (sx + 18, 232), (sx + 2, 290), (sx + 8, 340)])
        self.op(lambda cv: stroke(cv, stream, 20, C_BANK, 0.9, cap=True))
        self.op(lambda cv: stroke(cv, stream, 14, C_WATER, 1.0, cap=True))
        self.op(lambda cv: stroke(cv, [(a + 2, b) for a, b in stream], 4, C_WATER_D, 0.6))
        yb = G.project((sx + 6, 200), self.roads['park_path'].curve)[0][1]       # the little bridge where the path crosses it
        self.op(lambda cv: rect(cv, (sx + 6, yb), 30, 22, 0, (0.62, 0.46, 0.30), 1.0), post=True)
        for k in range(-4, 5):
            self.op(lambda cv, k=k: stroke(cv, [(sx - 9, yb + k * 2.4), (sx + 21, yb + k * 2.4)], 0.5, (0.40, 0.28, 0.18), 0.7), post=True)
        self.add('Leisure', 'SwingTree', sx + 38, 108, 180, 1.0, None, tag='swingtree')
        self.add('Leisure', 'SwingTree', sx - 38, 122, 180, 0.9, None, tag='swingtree')
        for dx, dy in ((30, 260), (62, 268)):
            self.add('Leisure', 'Trampoline', sx + dx, dy, 0, 2.3, None, tag='trampoline')
        self.add('Leisure', 'SwingFrame', sx - 84, 116, 180, 1.5, None, tag='frame')
        self.add('Barriers', 'NetTunnel', sx + 20, 296, 90, 1.7, None, tag='nettunnel')
        self.op(lambda cv: rect(cv, (sx - 4, 128), 118, 80, 0, (0.68, 0.52, 0.40), 0.85))
        self.op(lambda cv: rect(cv, (sx + 44, 278), 70, 50, 0, (0.68, 0.52, 0.40), 0.85))
        for r_ in ((sx + 14, 100), (sx - 14, 150), (sx + 20, 255), (sx - 6, 318)):
            self.add('Plants', 'Reeds', r_[0], r_[1], rng.uniform(0, 360), 2.0, None, tag='reeds')
        self.playground = (sx - 4, 128)
        # L22 (from the boathouse at the pond's west end): the duck pond north of the path: stepping stones across it, a rope ferry (a raft
        # on a rope), a fountain, ducks (before the long walk past the lawn arena to grandpa's allotment, its stop)
        n = self.node('L22')
        pc = (n[0] + 42, 116)
        lake = (pc[0] - 24, 116)
        self.op(lambda cv: (ellipse(cv, lake, 106, 42, 0, (0.70, 0.66, 0.52), 0.5, blur=4.0), ellipse(cv, lake, 100, 36, 0, C_BANK, 0.9, blur=2.0),
                            ellipse(cv, lake, 94, 31, 0, C_WATER, 1.0, blur=0.8)))
        self.add('Leisure', 'DuckPond', pc[0], pc[1], 0, 3.2, None, tag='pond')
        for k in range(7):
            self.add('Terrain', 'SteppingStone', pc[0] - 40 + k * 13, pc[1] + 14 - (k % 2) * 4, rng.uniform(0, 360), 1.6, None, tag='stone')
        self.op(lambda cv: stroke(cv, [(pc[0] - 56, pc[1] - 16), (pc[0] + 56, pc[1] - 16)], 0.9, (0.25, 0.22, 0.18), 0.9), post=True)
        for sxx in (-1, 1):
            self.add('Street', 'Bollard', pc[0] + sxx * 58, pc[1] - 16, 0, 1.4)
        self.add('Leisure', 'Raft', pc[0] + 12, pc[1] - 16, 90, 1.5, None, tag='raft')
        self.add('Leisure', 'Fountain', pc[0] - 22, pc[1] - 4, 0, 2.4, None, tag='fountain')
        for k in range(6):
            self.add('Animals', 'Duck', pc[0] + rng.uniform(-48, 48), pc[1] + rng.uniform(-26, 26), rng.uniform(0, 360), 2.4, None, tag='duck')
        for k in range(7):
            a = rng.uniform(0, 6.28)
            self.add('Plants', 'Reeds', pc[0] + math.cos(a) * 62, pc[1] + math.sin(a) * 40, rng.uniform(0, 360), 2.0, None, tag='reeds')
        # C05: the lawn arena (mown stripes, a ring, goals, benches) at the school end of the park
        c5 = self.node('C05')
        ac = (c5[0], min(c5[1], 262.0) + 4)
        self.reserve(ac, 150, 96)
        x0, x1, y0, y1 = c5[0] - 76, c5[0] + 76, 232.0, 334.0
        self.op(lambda cv: rect(cv, ((x0 + x1) / 2, (y0 + y1) / 2), x1 - x0, y1 - y0, 0, (0.50, 0.65, 0.38), 1.0))
        for k in range(-6, 7):
            self.op(lambda cv, k=k: rect(cv, (c5[0] + k * 12, (y0 + y1) / 2), 6.5, y1 - y0, 0, (0.55, 0.70, 0.42), 0.8))
        wl = [(x0 + 5, y0 + 5), (x1 - 5, y0 + 5), (x1 - 5, y1 - 5), (x0 + 5, y1 - 5), (x0 + 5, y0 + 5)]
        self.op(lambda cv: stroke(cv, wl, 1.2, C_WHITE, 0.9), post=True)
        self.op(lambda cv: stroke(cv, [(c5[0], y0 + 5), (c5[0], y1 - 5)], 1.2, C_WHITE, 0.9), post=True)
        self.op(lambda cv: (disc(cv, (c5[0], (y0 + y1) / 2), 15, C_WHITE, 0.9), disc(cv, (c5[0], (y0 + y1) / 2), 13.8, (0.55, 0.70, 0.42), 1.0)), post=True)
        for sx_ in (-1, 1):
            self.box(c5[0] + sx_ * 70, (y0 + y1) / 2, 0.15, 5.4, 2.2, 0, (0.95, 0.95, 0.95), tag='goal', roof='frame')
        # L23 (from grandpa's allotment, under the railway by the park's tunnel): the school garden east of the line: a fountain, a swing,
        # seagulls, a crossing of the East Street, the school's side steps
        n = self.node('L23')
        fc = (n[0] + 70, n[1] + 78)
        self.op(lambda cv: (disc(cv, fc, 32, (0.74, 0.72, 0.67), 1.0), disc(cv, fc, 28, (0.84, 0.82, 0.77), 1.0)))
        self.add('Leisure', 'Fountain', fc[0], fc[1], 0, 3.6, None, tag='fountain')
        self.add('Leisure', 'SwingSet', n[0] + 150, n[1] + 72, 180, 1.6, None, tag='swing')
        self.op(lambda cv: rect(cv, (n[0] + 150, n[1] + 76), 60, 34, 0, (0.68, 0.52, 0.40), 0.85))
        for k in range(8):
            self.add('Animals', 'SeagullStanding', n[0] + rng.uniform(0, 190), n[1] + 40 + rng.uniform(0, 100), rng.uniform(0, 360), 3.0, None, tag='bird')
        for k in range(3):
            self.add('Animals', 'Seagull', n[0] + 20 + k * 50, n[1] + 112 + rng.uniform(-10, 10), rng.uniform(0, 360), 3.0, None, z=4.0, tag='bird')
        self.op(lambda cv: zebra(cv, (1855, 300), (0, 1), 100, 22.0, 4.6, 4.2), post=True)
        self.add('Street', 'PedSignal', 1815, 288, 90)
        self.add('Street', 'PedSignal', 1895, 312, 270)
        sc = (1925.0, 215.0)
        for k in range(6):
            self.op(lambda cv, k=k: rect(cv, (sc[0] - 3 - k * 4.4, sc[1]), 4.4, 28, 0, (0.84, 0.82, 0.77), 1.0), post=True)
            self.op(lambda cv, k=k: rect(cv, (sc[0] - 5 - k * 4.4, sc[1]), 1.2, 28, 0, (0.45, 0.43, 0.40), 0.7), post=True)
        self.add('Works', 'SchoolSign', 1932, 190, 270, 1.4, None, tag='sign')
        # the park's lamps, benches, flower beds and the trees (crowns, a few conifers, cherry blossom)
        path = self.roads['park_path'].curve
        total = G.poly_length(path)
        s = 60.0
        while s < total - 30:
            q, t = G.point_at(path, s)
            self.add('Leisure', 'ParkLamp', q[0] - t[1] * 17, q[1] + t[0] * 17, 0, 1.0, tag='lamp')
            if rng.random() < 0.35:
                self.add('Street', 'Bench', q[0] + t[1] * 17, q[1] - t[0] * 17, bearing((-t[1], t[0])) + 180, 1.0)
            s += 115.0
        for (bx, by) in ((120, 290), (170, 120), (480, 150), (760, 120), (840, 290), (1180, 300), (1440, 120)):
            self.op(lambda cv, bx=bx, by=by: rect(cv, (bx, by), 44, 22, 0, (0.52, 0.38, 0.28), 0.9))
            for k in range(8):
                fx, fy = bx + rng.uniform(-18, 18), by + rng.uniform(-7, 7)
                self.op(lambda cv, fx=fx, fy=fy, c=rng.choice(C_FLOWERS): disc(cv, (fx, fy), 2.6, c, 0.95))
        avoid = [(n_['x'], n_['y'], 38) for n_ in self.nodes.values() if True]
        avoid += [(fc[0], fc[1], 44), (pc[0] - 24, pc[1], 104), (c5[0], 283, 96), (self.playground[0], self.playground[1], 70), (sx + 44, 278, 44)]
        avoid += [(self.node('L20')[0] + dx, self.node('L20')[1] + dy, 52) for dx, dy in ((-92, 50), (0, 80), (92, 50), (-84, -76), (-12, -100), (50, -88), (-36, -50))]
        self.trees_in(poly, 78, 5, 13, 23, avoid=avoid, kinds=('park',), kit_share=0.14, blossom=0.06)
        self.trees_in(L.AREAS['garden']['poly'], 14, 6, 12, 19, avoid=avoid, kinds=('park',), kit_share=0.1, blossom=0.08)

    # ---------------------------------------------------------------- the beach
    def beach(self):
        rng = self.rng
        board = self.roads['boardwalk'].curve
        # the boardwalk's posts along both edges
        total = G.poly_length(board)
        s = 20.0
        while s < total - 10:
            p, t = G.point_at(board, s)
            for sg in (-1, 1):
                self.add('Street', 'Bollard', p[0] - t[1] * 9.5 * sg, p[1] + t[0] * 9.5 * sg, 0, 1.0, tag='post')
            s += 36.0
        # L11 (from home down the West Street, along Seaside Road and out on the boardwalk to the surf school, its stop): at the corner
        # of Seaside Road the beach shop with its racks of boards, buckets and spades and beach balls out front, the sign to the beach,
        # people with boards and towels on their way down; then the boardwalk's flags where it leaves the road for the sand
        n = self.node('L11')
        shop = (n[0] + 120, 1096.0)
        tints = [(0.55, 0.82, 0.88), (0.95, 0.55, 0.30), (0.95, 0.93, 0.86)]
        O = P.origin_for('Buildings', 'ShopFruit', shop, 180.0, 1.0)
        self.add('Buildings', 'ShopFruit', O[0], O[1], 180.0, 1.0, tints, tag='shop')
        self.world.occupy(P.footprint('Buildings', 'ShopFruit', O[0], O[1], 180.0, 1.0, pad=0.4))
        P.shop_awnings(self.items, shop, 180.0, 8.8 * PPM, tints[1])
        for dx in (-30, 30):
            self.add('Barriers', 'SurfRack', shop[0] + dx, shop[1] + 6, 0, 1.0, None, tag='surfrack')
        for k in range(4):
            self.add('Leisure', 'BucketSpade', shop[0] - 12 + k * 8, shop[1] + 5, rng.uniform(0, 360), 2.2, None, tag='bucket')
        for k, col in enumerate(((0.95, 0.30, 0.25), (0.98, 0.85, 0.25), (0.25, 0.55, 0.90))):
            self.box(shop[0] + 42 + k * 6, shop[1] + 6, 0.5, 0.5, 0.5, 0, col, tag='beachball', roof='round')
        self.add('Leisure', 'SignBoard', n[0] + 46, 1110, 135, 1.3, [(0.30, 0.62, 0.74)], tag='sign')
        for k in range(5):
            self.person(n[0] + 200 + k * 46 + rng.uniform(-8, 8), 1103 + rng.uniform(-2, 2), 90)
        for x in (1430, 1520):
            self.add('Street', 'BannerFlag', x, 1112, 0, 1.4, [(0.30, 0.62, 0.74)], tag='flag')
        # L12: wet sand with several tidal channels running to the sea, and boat trestles
        n = self.node('L12')
        # (the surf school's hut stands just west of them, on the sand by the boardwalk)
        chans = [[(n[0] - 82, 1132), (n[0] - 70, 1190), (n[0] - 96, 1250), (n[0] - 86, 1320), (n[0] - 118, 1392)],
                 [(n[0] - 2, 1136), (n[0] + 16, 1198), (n[0] - 4, 1262), (n[0] + 22, 1318)],
                 [(n[0] + 76, 1132), (n[0] + 60, 1180), (n[0] + 84, 1232)]]
        self.op(lambda cv: ellipse(cv, (n[0] + 4, 1236), 150, 90, 8, (0.70, 0.60, 0.44), 0.55, blur=10.0))
        for ch in chans:
            ch = self.smooth(ch)
            self.op(lambda cv, ch=ch: stroke(cv, ch, 30, (0.62, 0.52, 0.38), 0.45, cap=True))
            self.op(lambda cv, ch=ch: stroke(cv, ch, 19, (0.56, 0.46, 0.34), 0.85, cap=True))
            self.op(lambda cv, ch=ch: stroke(cv, ch, 9, (0.50, 0.68, 0.70), 0.95, cap=True))
            self.op(lambda cv, ch=ch: stroke(cv, [(a + 1.5, b) for a, b in ch], 2, (0.90, 0.94, 0.94), 0.5))
        for dx, dy, f in ((-30, 52, 20), (50, 70, 340), (-124, 82, 80)):
            self.add('Barriers', 'BoatTrestles', n[0] + dx, 1160 + dy, f, 1.5, None, tag='boat')
        # L13: gulls, a rescue-board stand, a breezy bay with rocks and flags
        n = self.node('L13')
        self.add('Barriers', 'RescueBoardStand', n[0] + 100, n[1] + 14, 270, 1.4, None, tag='rescue')
        for k in range(10):
            self.add('Animals', 'SeagullStanding', n[0] + 40 + rng.uniform(0, 140), n[1] - 70 + rng.uniform(0, 150), rng.uniform(0, 360), 3.0, None, tag='bird')
        for k in range(4):
            self.add('Animals', 'Seagull', n[0] + 40 + rng.uniform(0, 140), n[1] - 60 + rng.uniform(0, 140), rng.uniform(0, 360), 3.2, None, z=5.0, tag='bird')
        for dy in (-60, 70):
            self.add('Street', 'BannerFlag', n[0] + 92, n[1] + dy, 0, 1.5, [(0.90, 0.42, 0.36)], tag='flag')
        for k in range(6):
            a = rng.uniform(0, 6.28)
            self.add('Terrain', rng.choice(['Boulder3', 'Boulder4', 'BoulderLarge1', 'RockCluster']), n[0] + 160 + math.cos(a) * 34, n[1] + 70 + math.sin(a) * 40, rng.uniform(0, 360), rng.uniform(1.0, 1.5), None, tag='rock')
        # L14 (from the beach cafe, up the boardwalk to the promenade and the school): sandcastles on the sand beside it, surf racks, the
        # boardwalk crossing the promenade
        n = self.node('L14')
        for k in range(6):
            self.add('Leisure', 'SandCastle', n[0] - 150 + (k % 3) * 22, n[1] - 30 + (k // 3) * 44 + (k % 2) * 8, rng.uniform(0, 360), 3.4, None, tag='castle')
            self.add('Leisure', 'BucketSpade', n[0] - 142 + (k % 3) * 22, n[1] - 14 + (k // 3) * 44, rng.uniform(0, 360), 2.4, None, tag='bucket')
        for dx in (-40, -12):
            self.add('Barriers', 'SurfRack', n[0] + dx, n[1] - 108, 180, 1.25, None, tag='surfrack')
        ce = self.B['graph'].nodes['ce']
        self.op(lambda cv: rect(cv, (ce[0], ce[1]), 62, 62, 0, (0.66, 0.50, 0.34), 1.0), post=True)
        for k in range(-7, 8):
            self.op(lambda cv, k=k: stroke(cv, [(ce[0] - 28, ce[1] + k * 4), (ce[0] + 28, ce[1] + k * 4)], 0.8, (0.38, 0.27, 0.18), 0.7), post=True)
        # C03: slalom flags in a zig-zag down the sand east of the school, start and finish gates
        n = self.node('C03')
        for k in range(10):
            self.add('Leisure', 'SlalomFlag', n[0] + 30 + (-16 if k % 2 else 16), n[1] - 150 + k * 31, 0, 2.2, [rng.choice([(0.9, 0.3, 0.3), (0.95, 0.85, 0.3), (0.3, 0.6, 0.85)])], tag='flag')
        for dy in (-170, 160):
            self.add('Leisure', 'CheckpointFlag', n[0] + 14, n[1] + dy, 0, 2.2, None, tag='gate')
            self.add('Leisure', 'CheckpointFlag', n[0] + 56, n[1] + dy, 180, 2.2, None, tag='gate')
        # parasols, towels, palms, dune grass: scattered over the rest of the sand (the lifeguard tower is a stop: town_map_sets_stops)
        placed = []
        keep = [(self.node(k)[0], self.node(k)[1], 60) for k in ('L12', 'L13', 'L14', 'C03')]
        keep += [(s['x'], s['y'], 40) for s in self.B.get('stops', {}).values() if s['route'] == 'beach']
        n_ok, tries = 0, 0
        while n_ok < 34 and tries < 6000:
            tries += 1
            x, y = rng.uniform(1520, 2440), rng.uniform(560, 1360)
            if self.world.kind_at((x, y)) != 'sand' or self.sand_dist((x, y)) < 46:
                continue
            cx, cy = int((x + 400) / P.CELL), int((y + 225) / P.CELL)
            if self.world.path[cy, cx] or self.world.road[cy, cx] or self.world.built[cy, cx]:
                continue
            if any(math.hypot(x - px, y - py) < 78 for px, py in placed) or any(math.hypot(x - kx, y - ky) < kr + 20 for kx, ky, kr in keep):
                continue
            placed.append((x, y))
            n_ok += 1
            self.add('Leisure', 'Parasol', x, y, rng.uniform(0, 360), 1.2, [rng.choice([(0.88, 0.42, 0.36), (0.30, 0.62, 0.74), (0.94, 0.78, 0.30), (0.40, 0.68, 0.46)]), (0.97, 0.93, 0.84)], tag='parasol')
            for k in range(rng.randint(1, 2)):
                self.add('Leisure', 'BeachTowel', x + rng.uniform(-18, 18), y + rng.uniform(8, 22), rng.uniform(0, 360), 1.2, [rng.choice([(0.34, 0.66, 0.78), (0.9, 0.5, 0.5), (0.95, 0.85, 0.35)]), (0.97, 0.93, 0.84)], tag='towel')
        for k in range(14):
            x, y = rng.uniform(1520, 2440), rng.uniform(600, 1350)
            if self.world.kind_at((x, y)) == 'sand' and self.sand_dist((x, y)) > 150:
                cx, cy = int((x + 400) / P.CELL), int((y + 225) / P.CELL)
                if not (self.world.path[cy, cx] or self.world.road[cy, cx]):
                    self.add('Plants', rng.choice(['Palm', 'PalmShort']), x, y, rng.uniform(0, 360), 1.0, None, tag='palm')
        for k in range(20):
            x, y = rng.uniform(1520, 2440), rng.uniform(580, 1350)
            if self.world.kind_at((x, y)) == 'sand' and self.sand_dist((x, y)) > 70:
                cx, cy = int((x + 400) / P.CELL), int((y + 225) / P.CELL)
                if not (self.world.path[cy, cx] or self.world.road[cy, cx]):
                    self.add('Plants', 'DuneGrass', x, y, rng.uniform(0, 360), 1.8, None, tag='grass')

    # ---------------------------------------------------------------- the country: woods in the north, the far shore, hedgerows
    def country(self):
        rng = self.rng
        L = self.L
        for name in ('wood_w', 'wood_m', 'wood_e'):
            poly = L.AREAS[name]['poly']
            xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            self.trees_in(poly, int(area / 480), zlib.crc32(name.encode()) % 1000, 14, 25, kinds=('wood', 'field'), kit_share=0.3, blossom=0.02, min_gap=0.42)
        poly = L.AREAS['far_shore']['poly']
        self.trees_in(poly, 70, 17, 15, 26, kinds=('far',), kit_share=0.35, blossom=0.0, min_gap=0.4)
        for k in range(70):
            x, y = rng.uniform(-400, 2700), rng.uniform(-200, 50)
            pts = [(x - 9, y - 9), (x + 9, y - 9), (x + 9, y + 9), (x - 9, y + 9)]
            if self.world.free(pts, ('field',)):
                self.items.append(P.tree_item(x, y, rng, rng.uniform(11, 20), kit_share=0.1))
