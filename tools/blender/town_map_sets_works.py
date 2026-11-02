# The building site (L16, L17, C04), the railway with its bridges over the underpass (L15, L18) and the park tunnel, the station,
# and the school with its grounds and pitch.
import math, random
import town_map_graph as G
import town_map_place as P
from town_map_sets import (PPM, C_STONE, C_WHITE, C_GRASS, C_GRASS_L, C_DIRT, C_GRAVEL, C_CONCRETE, C_CONCRETE_D, C_WET, C_PUDDLE,
                           ang, bearing, fill, rect, disc, stroke, ellipse, textured, zebra)

BALLAST = (0.52, 0.50, 0.46)
RAILC = (0.80, 0.80, 0.82)


class WorksSets:
    def works(self):
        self.site()
        self.railway()
        self.school()

    # ---------------------------------------------------------------- the building site: a fenced yard on both sides of Yard Road
    def site(self):
        rng = self.rng
        x0, x1, x1s = 800.0, 1462.0, 1318.0
        yn0, yn1, ys0, ys1 = 428.0, 578.0, 622.0, 772.0
        for (xa, xb, ya, yb) in ((x0, x1, yn0, yn1), (x0, x1s, ys0, ys1)):
            self.reserve(((xa + xb) / 2, (ya + yb) / 2), xb - xa, yb - ya)
        # the ground: mud with tyre tracks, a concrete slab, gravel, a few puddles
        def ground(cv):
            for (xa, xb, ya, yb, sd) in ((x0, x1, yn0, yn1, 91), (x0, x1s, ys0, ys1, 93)):
                textured(cv, [(xa, ya), (xb, ya), (xb, yb), (xa, yb)], (0.60, 0.51, 0.39), sd, amp=(0.07, 0.06, 0.05), cells=(70, 16, 4), blur=0.8)
            for (cx, cy, w, h, sd) in ((1272, 536, 150, 60, 1), (990, 700, 160, 80, 2), (1110, 462, 110, 46, 3)):
                textured(cv, [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], C_GRAVEL, 90 + sd, amp=(0.06, 0.05, 0.05), cells=(30, 8, 2), a=0.85, blur=2.0)
            for (cx, cy, w, h) in ((1340, 480, 150, 70), (1150, 750, 120, 36)):
                rect(cv, (cx, cy), w, h, 0, (0.70, 0.69, 0.66), 1.0)
            for ty, xe in ((562, x1), (637, x1s)):
                stroke(cv, [(x0, ty), (1000, ty - 3), (1200, ty + 2), (xe, ty - 2)], 3.0, (0.36, 0.28, 0.20), 0.5)
            for (px_, py_, rr) in ((1160, 560, 14), (1020, 650, 11), (1250, 640, 12), (870, 540, 9)):
                ellipse(cv, (px_, py_), rr * 1.4, rr, 5, (0.46, 0.50, 0.55), 0.75, blur=0.8)
        self.op(ground)
        # the fence all round both yards with the gates on the track, a second barrier across the track (L16's gate)
        for per in ([(x0, yn0), (x1, yn0), (x1, yn1), (x0, yn1), (x0, yn0)], [(x0, ys0), (x1s, ys0), (x1s, ys1), (x0, ys1), (x0, ys0)]):
            self.line_of(per, 'Works', 'SiteFence', 30, None, tag='sitefence')
        for gx in (x0, x1):
            for sy in (-1, 1):
                self.add('Works', 'GatePillar', gx, 600 + sy * 28, 0, 0.8, None, tag='gate')
            self.add('Works', 'SlidingGate', gx, 575, 0, 0.9, None, tag='gate')
        # L16: ramps and platforms, pipe racks, rolling pipes, a security gate on the track
        n = self.node('L16')
        gx = n[0] - 150
        self.add('Works', 'IntercomPost', gx - 18, 626, 0, 1.0, None, tag='gate')
        self.box(gx, 600, 0.3, 5.6, 1.1, 0, (0.95, 0.80, 0.20), z=0.9, tag='boom')
        self.add('Barriers', 'BoomBarrier', gx, 600, 90, 1.0, None, tag='boom')
        for k in range(2):
            self.box(n[0] - 190 + k * 34, 530, 3.0, 6.0, 1.6, 0, (0.60, 0.58, 0.54), tag='ramp', roof='wedge')
            self.add('Barriers', 'AccessPlatform', n[0] - 190 + k * 34, 506, 0, 1.4, None, tag='platform')
        self.add('Barriers', 'AccessPlatform', n[0] - 126, 520, 90, 1.4, None, tag='platform')
        for k in range(3):
            self.add('Barriers', 'PipeRack', n[0] + 104 + k * 38, 524, 0, 1.3, None, tag='pipes')
        for k in range(7):
            self.add('Works', 'ConcretePipe', n[0] + 98 + k * 17 + rng.uniform(-3, 3), 562 + rng.uniform(-6, 4), rng.choice((90, 90, 60, 120)), 1.2, None, tag='pipe')
        self.add('Works', 'PipeStack', n[0] + 188, 540, 0, 1.3, None, tag='pipes')
        for k in range(3):
            self.add('Works', 'SiteCabin', n[0] - 74 + k * 54, 444, 0, 1.0, [(0.90, 0.88, 0.80), None, None], tag='site')
        self.add('Works', 'PortaLoo', n[0] + 118, 446, 0, 1.0)
        self.add('Works', 'PortaLoo', n[0] + 134, 446, 0, 1.0)
        for k in range(5):
            self.add('Barriers', 'SiteBarrier', n[0] - 20 + k * 20, 585, 90, 0.9, None, tag='barrier')
        # L17: two tower cranes swinging pallets over open trenches, the builder's lift, a digger, a mixer
        n = self.node('L17')
        for (tx, ty, ex, ey, sc) in ((n[0] - 150, 692, -1.0, 0.0, 0.5), (n[0] - 380, 748, 1.0, -0.2, 0.46)):
            d = (ex / math.hypot(ex, ey), ey / math.hypot(ex, ey))
            self.add('Works', 'TowerCrane', tx, ty, math.degrees(math.atan2(-d[1], -d[0])), sc, None, tag='crane')
            jl = 40 * sc * PPM * 0.72
            self.add('Works', 'CraneLoad', tx + d[0] * jl, ty + d[1] * jl, math.degrees(math.atan2(-d[1], -d[0])), 0.9, None, z=9.0, tag='load')
            self.add('Works', 'CraneTrolley', tx + d[0] * jl, ty + d[1] * jl, 0, 1.2, None, z=34.0 * sc, tag='trolley')
        trenches = [(n[0] - 250, 706, 120, 14), (n[0] - 280, 745, 100, 13), (n[0] - 190, 742, 64, 12)]
        for (cx, cy, w, h) in trenches:
            self.op(lambda cv, cx=cx, cy=cy, w=w, h=h: (rect(cv, (cx, cy), w + 6, h + 6, 0, (0.50, 0.42, 0.32), 1.0), rect(cv, (cx, cy), w, h, 0, (0.22, 0.17, 0.13), 1.0), rect(cv, (cx, cy + 2), w - 4, h * 0.45, 0, (0.14, 0.11, 0.08), 0.8)), post=True)
            for k in range(3):
                self.add('Barriers', 'PlankTrestles', cx - w / 2 + 14 + k * (w - 28) / 2, cy - h / 2 - 6, 0, 0.8, None, tag='trestle')
        lift = (n[0] - 104, 538)
        for k in range(5):
            self.add('Works', 'HoistMast', lift[0], lift[1], 0, 1.0, None, z=k * 3.0, tag='lift')
        self.add('Works', 'HoistMastCap', lift[0], lift[1], 0, 1.0, None, z=15.0, tag='lift')
        self.add('Works', 'HoistCage', lift[0], lift[1] + 10, 0, 1.0, None, z=4.0, tag='lift')
        for k in range(2):
            self.add('Works', 'Scaffold', lift[0] + 22 + k * 24, lift[1] - 6, 0, 1.0, None, tag='scaffold')
        self.add('Works', 'Digger', n[0] - 360, 660, 200, 1.0, None, tag='digger')
        self.add('Works', 'CementMixer', n[0] - 180, 650, 40, 1.0)
        self.add('Works', 'Skip', n[0] - 336, 758, 20, 1.0)
        self.add('Works', 'Skip', n[0] - 294, 764, 350, 1.0)
        self.add('Works', 'SteelBeams', n[0] - 150, 760, 8, 1.2)
        for (gx_, gy_) in ((n[0] - 150, 540), (n[0] - 300, 650)):
            self.add('Terrain', 'GravelPile', gx_, gy_, rng.uniform(0, 360), 1.5)
        self.add('Works', 'Wheelbarrow', n[0] - 230, 640, 25, 1.2)
        for k in range(6):
            self.add('Street', 'TrafficCone', x0 + 40 + k * 7, 640 + (k % 2) * 16, 0, 1.2)
        # C04: the targets in the yard, on a slab (north-west of the yard, beside the node)
        c4 = self.node('C04')
        for k in range(5):
            a = -0.9 + k * 0.45
            self.add('Leisure', 'Target', c4[0] + 98 + k * 21, c4[1] + 18 + math.sin(a) * 6, 180, 1.7, None, tag='target')
        self.op(lambda cv: rect(cv, (c4[0] + 142, c4[1] + 28), 140, 56, 0, (0.70, 0.69, 0.66), 1.0))
        self.op(lambda cv: stroke(cv, [(c4[0] + 80, c4[1] + 52), (c4[0] + 206, c4[1] + 52)], 1.4, (0.95, 0.80, 0.20), 0.9), post=True)

    # ---------------------------------------------------------------- the railway: bridges over the underpass and the park path, the station
    def deck(self, c, w, d, along='y', parapet=True):
        """A railway bridge deck carrying a track over a road: w px across the track, d px along it, centred on c. Rails run along `along`."""
        face = 0.0 if along == 'y' else 90.0
        self.box(c[0], c[1], w / PPM, d / PPM, 0.9, face, (0.60, 0.60, 0.58), z=2.7, tag='deck')
        self.box(c[0], c[1], (w - 6) / PPM, d / PPM, 0.3, face, BALLAST, z=3.6, tag='deck')
        for off in (-4.5, 4.5):
            ox, oy = (c[0] + off, c[1]) if along == 'y' else (c[0], c[1] + off)
            self.box(ox, oy, 0.22, d / PPM, 0.22, face, RAILC, z=3.9, tag='rail')
        if parapet:
            for sg in (-1, 1):
                ox, oy = (c[0] + sg * (w / 2 - 1.2), c[1]) if along == 'y' else (c[0], c[1] + sg * (w / 2 - 1.2))
                self.box(ox, oy, 0.28, d / PPM, 0.7, face, (0.50, 0.50, 0.48), z=3.6, tag='deck')

    def cutting(self, x0, x1, y, half, gaps=()):
        """Retaining walls along both sides of a road running east-west at y between x0 and x1 (the road in a cutting)."""
        for sg in (-1, 1):
            self.line_of([(x0, y + sg * half), (x1, y + sg * half)], 'Works', 'UnderpassWall', 16, [(0.66, 0.64, 0.60)], skip=gaps, tag='cutting')

    def railway(self):
        rng = self.rng
        # the railway corridor (the main line and the station's loop, with their banks) is kept free of houses and trees
        for rail in (self.L.RAIL, self.L.RAIL2):
            for p in G.catmull_rom(list(rail['pts']), step=14.0)[0]:
                self.reserve(p, 80, 44)
        # the underpass: Station Road in a cutting under two tracks (the main line at x 1540 and the station's loop at x 1640)
        ry = 380.0
        self.cutting(1440, 1800, ry, 44)
        self.deck((1540, ry), 46, 100, 'y')
        self.deck((1640, ry), 46, 100, 'y')
        # the station's ticket hall stands over the road east of the loop: the third dark stretch (L18's second tunnel, under the station)
        hall = (1770.0, ry)
        self.box(hall[0], hall[1], 6.4, 11.4, 2.0, 0, (0.70, 0.68, 0.64), z=2.7, tag='hall')
        self.box(hall[0], hall[1], 6.0, 11.4, 2.6, 0, (0.66, 0.30, 0.26), z=4.7, tag='hall', roof='ridge')
        for sg in (-1, 1):
            self.box(hall[0] + sg * 24, hall[1] - 48, 0.6, 0.6, 2.8, 0, (0.45, 0.45, 0.46), tag='hall')
            self.box(hall[0] + sg * 24, hall[1] + 48, 0.6, 0.6, 2.8, 0, (0.45, 0.45, 0.46), tag='hall')
        # the road dark and wet through the cutting
        self.op(lambda cv: rect(cv, (1620, ry), 360, 62, 0, (0.14, 0.14, 0.16), 0.5), post=True)
        # the embankment slopes either side of the road: grass banks along the tracks, trees on top
        def bank(cv):
            for (cx, cy, w, h) in ((1540, 300, 84, 100), (1540, 460, 84, 100), (1640, 450, 84, 150), (1590, 286, 110, 38)):
                rect(cv, (cx, cy), w, h, 0, (0.40, 0.52, 0.32), 0.9)
        self.op(bank)
        # L15: barriers across the road, puddles, pipes, a builder's lift, ramps and platforms, scaffolding at the west portal
        n = self.node('L15')
        for k in range(4):
            p, t = self.frame('L15', -92 - k * 14, 0)
            self.add('Barriers', 'SiteBarrier', p[0], p[1] + (k - 1.5) * 9, 0, 0.9, None, tag='barrier')
        for (dx, dy, rx, ry_) in ((-130, 8, 22, 9), (-62, -10, 18, 8), (30, 12, 24, 10), (96, -6, 20, 8)):
            self.op(lambda cv, c=(n[0] + dx, ry + dy), rx=rx, ry_=ry_: (ellipse(cv, c, rx + 6, ry_ + 4, 3, C_WET, 0.6, blur=2.0), ellipse(cv, c, rx, ry_, 3, C_PUDDLE, 0.95, blur=0.5)), post=True)
        for k in range(2):
            self.add('Barriers', 'PipeRack', n[0] - 150 + k * 44, ry + 56, 0, 1.2, None, tag='pipes')
        for k in range(5):
            self.add('Works', 'ConcretePipe', n[0] - 160 + k * 15, ry + 74, 90, 1.2, None, tag='pipe')
        lift = (n[0] + 112, ry - 58)
        for k in range(4):
            self.add('Works', 'HoistMast', lift[0], lift[1], 0, 1.0, None, z=k * 3.0, tag='lift')
        self.add('Works', 'HoistMastCap', lift[0], lift[1], 0, 1.0, None, z=12.0, tag='lift')
        self.add('Works', 'HoistCage', lift[0], lift[1] + 10, 0, 1.0, None, z=3.0, tag='lift')
        self.box(n[0] - 70, ry - 58, 3.0, 5.0, 1.4, 0, (0.60, 0.58, 0.54), tag='ramp', roof='wedge')
        self.add('Barriers', 'AccessPlatform', n[0] - 70, ry - 80, 0, 1.4, None, tag='platform')
        self.add('Barriers', 'ScaffoldGantry', n[0] + 62, ry + 62, 0, 1.2, None, tag='scaffold')
        self.add('Works', 'Scaffold', n[0] + 92, ry + 64, 0, 1.0, None, tag='scaffold')
        self.add('Works', 'TunnelLamp', 1502, ry - 20, 0, 1.4, None, z=2.5, tag='lamp')
        # L18: the cutting between the two bridges (scaffolding, a lift, barriers) and the road leaving under the loop
        n = self.node('L18')
        self.add('Barriers', 'ScaffoldGantry', 1590, ry - 58, 0, 1.2, None, tag='scaffold')
        self.add('Barriers', 'ScaffoldGantry', 1590, ry + 62, 180, 1.2, None, tag='scaffold')
        for k in range(3):
            self.add('Barriers', 'SiteBarrier', 1592, ry + (k - 1) * 18, 0, 0.9, None, tag='barrier')
        for (dx, dy, rx, ry_) in ((-44, 10, 20, 8), (-100, -8, 17, 8)):
            self.op(lambda cv, c=(n[0] + dx, ry + dy), rx=rx, ry_=ry_: (ellipse(cv, c, rx + 6, ry_ + 4, 0, C_WET, 0.6, blur=2.0), ellipse(cv, c, rx, ry_, 0, C_PUDDLE, 0.95, blur=0.5)), post=True)
        self.add('Barriers', 'PipeRack', n[0] - 150, ry + 58, 0, 1.2, None, tag='pipes')
        self.add('Barriers', 'AccessPlatform', n[0] + 40, ry - 62, 0, 1.4, None, tag='platform')
        self.box(n[0] + 66, ry - 60, 3.0, 5.0, 1.4, 0, (0.60, 0.58, 0.54), tag='ramp', roof='wedge')
        for k in range(3):
            self.add('Works', 'ConcretePipe', n[0] + 20 + k * 15, ry + 72, 90, 1.2, None, tag='pipe')
        # the park path's short tunnel: a bridge deck, wing walls, a lamp
        py = 186.0
        self.deck((1540, py), 46, 44, 'y')
        self.cutting(1496, 1584, py, 16)
        self.add('Works', 'TunnelLamp', 1506, py - 12, 0, 1.4, None, z=2.5, tag='lamp')
        self.op(lambda cv: rect(cv, (1540, py), 120, 24, 0, (0.30, 0.31, 0.30), 0.35), post=True)
        self.op(lambda cv: (rect(cv, (1540, 236), 84, 100, 0, (0.40, 0.52, 0.32), 0.9), rect(cv, (1540, 136), 84, 100, 0, (0.40, 0.52, 0.32), 0.9)))
        # the station: an island platform between the tracks, a canopy, a train on the loop, the station building, buffers
        def platform(cv):
            rect(cv, (1590, 488), 50, 106, 0, (0.76, 0.75, 0.72), 1.0)
            for sx in (-1, 1):
                stroke(cv, [(1590 + sx * 22, 436), (1590 + sx * 22, 540)], 1.8, (0.96, 0.82, 0.25), 1.0)
            rect(cv, (1590, 488), 50, 106, 0, (0.55, 0.55, 0.53), 0.0)
        self.op(platform, post=True)
        self.slab((1590, 488), (0, 1), 90, 40, 0.35, (0.62, 0.30, 0.26), z=3.2, tag='canopy')
        for yy in (452, 488, 524):
            for sx in (-1, 1):
                self.box(1590 + sx * 16, yy, 0.3, 0.3, 3.2, 0, (0.40, 0.40, 0.42), tag='canopy')
        for yy in (462, 514):
            self.add('Street', 'Bench', 1590, yy, 90, 1.0)
        self.slab((1640, 478), (0, 1), 46, 22, 3.4, (0.82, 0.84, 0.86), z=0.35, roof='round', tag='train')
        self.slab((1640, 520), (0, 1), 36, 22, 3.0, (0.80, 0.32, 0.28), z=0.35, roof='round', tag='train')
        self.slab((1640, 452), (0, 1), 4, 20, 2.6, (0.35, 0.40, 0.46), z=0.35, tag='train')
        for bx in (1540, 1640):
            self.box(bx, 546, 2.4, 0.8, 0.9, 0, (0.30, 0.22, 0.20), tag='buffer')
        O = P.origin_for('Buildings', 'Warehouse', (1721.0, 500.0), 270.0, 0.85)
        self.add('Buildings', 'Warehouse', O[0], O[1], 270.0, 0.85, [(0.93, 0.86, 0.72), (0.55, 0.30, 0.25), (0.46, 0.30, 0.28)], tag='station')
        self.world.occupy(P.footprint('Buildings', 'Warehouse', O[0], O[1], 270.0, 0.85, pad=0.5))
        self.op(lambda cv: textured(cv, [(1672, 440), (1800, 440), (1800, 556), (1672, 556)], (0.74, 0.73, 0.70), 71, amp=(0.03, 0.02, 0.02), cells=(40, 9, 3)))
        for k in range(3):
            self.add('Street', 'BikeRack', 1700 + k * 26, 450, 0, 1.0)
        self.add('Street', 'StreetLamp', 1668, 470, 180)
        self.add('Street', 'StreetLamp', 1668, 540, 180)
        self.line_of([(1480, 432), (1480, 556)], 'Works', 'SiteFence', 30, [(0.42, 0.52, 0.46)], tag='railfence')
        for (hx, hy) in ((1490, 450), (1490, 505)):
            self.crown(hx, hy, 11)

    # ---------------------------------------------------------------- the school: the building, its gate and arch, the pitch, the grounds
    def school(self):
        rng = self.rng
        S = self.B['places']['school']
        x0, x1, y0, y1 = 1890.0, 2240.0, 70.0, 556.0
        self.reserve(((x0 + x1) / 2, (y0 + y1) / 2), x1 - x0, y1 - y0)
        O = P.origin_for('Buildings', 'School', (2065.0, 262.0), 180.0, 1.0)
        self.add('Buildings', 'School', O[0], O[1], 180.0, 1.0, None, tag='school')
        # the entrance steps and a forecourt, the path from the gate to it
        self.op(lambda cv: rect(cv, (2065, 296), 150, 62, 0, (0.80, 0.77, 0.71), 1.0))
        for k in range(5):
            self.op(lambda cv, k=k: rect(cv, (2065, 266 + k * 4.4), 46, 4.4, 0, (0.84, 0.82, 0.77), 1.0), post=True)
            self.op(lambda cv, k=k: rect(cv, (2065, 268 + k * 4.4), 46, 1.2, 0, (0.45, 0.43, 0.40), 0.7), post=True)
        self.op(lambda cv: stroke(cv, [(S[0], 552), (S[0], 380), (2020, 330), (2065, 322)], 14, (0.80, 0.77, 0.71), 1.0))
        # the gate arch, the wall along the lane, the fences
        self.add('Works', 'SchoolArch', S[0], 556, 90, 1.0, None, tag='arch')
        self.add('Works', 'SchoolSign', S[0] - 34, 552, 180, 1.4, None, tag='sign')
        self.line_of([(x0, 556), (x1, 556)], 'Works', 'SchoolWall', 16, None, skip=[(S[0], 556, 28)], tag='wall')
        self.line_of([(x0, y0), (x0, 556)], 'Works', 'SchoolWall', 16, None, skip=[(x0, 215, 16)], tag='wall')
        self.line_of([(x1, y0), (x1, 556)], 'Works', 'SchoolWall', 16, None, tag='wall')
        self.line_of([(x0, y0), (x1, y0)], 'Street', 'PicketFence2', 16, [(0.34, 0.47, 0.38)], tag='fence')
        # the football pitch with its running track
        pc = (2124.0, 440.0)
        pw, ph = 196.0, 118.0

        def pitch(cv):
            tw, th = pw + 40, ph + 40
            rect(cv, pc, tw, th, 0, (0.72, 0.36, 0.28), 1.0)
            rect(cv, pc, tw - 12, th - 12, 0, (0.64, 0.30, 0.24), 1.0)
            rect(cv, pc, pw + 12, ph + 12, 0, (0.72, 0.36, 0.28), 1.0)
            m = cv.rect_mask(pc, pw, ph, 0.0)
            cv.blend(m, cv.textured(m, (0.40, 0.62, 0.32), (0.04, 0.03, 0.02), (60, 14, 4), 88))
            for k in range(-4, 5):
                rect(cv, (pc[0] + k * 22, pc[1]), 11, ph, 0, (0.45, 0.66, 0.36), 0.5)
            wl = (0.95, 0.95, 0.92)
            stroke(cv, [(pc[0] - pw / 2 + 4, pc[1] - ph / 2 + 4), (pc[0] + pw / 2 - 4, pc[1] - ph / 2 + 4), (pc[0] + pw / 2 - 4, pc[1] + ph / 2 - 4), (pc[0] - pw / 2 + 4, pc[1] + ph / 2 - 4), (pc[0] - pw / 2 + 4, pc[1] - ph / 2 + 4)], 1.3, wl, 0.95)
            stroke(cv, [(pc[0], pc[1] - ph / 2 + 4), (pc[0], pc[1] + ph / 2 - 4)], 1.3, wl, 0.95)
            disc(cv, pc, 14, wl, 0.9)
            disc(cv, pc, 12.8, (0.43, 0.65, 0.35), 1.0)
            for sx in (-1, 1):
                stroke(cv, [(pc[0] + sx * (pw / 2 - 4), pc[1] - 26), (pc[0] + sx * (pw / 2 - 28), pc[1] - 26), (pc[0] + sx * (pw / 2 - 28), pc[1] + 26), (pc[0] + sx * (pw / 2 - 4), pc[1] + 26)], 1.2, wl, 0.9)
        self.op(pitch, post=True)
        for sx in (-1, 1):
            self.box(pc[0] + sx * (pw / 2 - 1), pc[1], 0.15, 7.3, 2.4, 0, (0.95, 0.95, 0.95), tag='goal', roof='frame')
        # the playground, bike racks, a flag, trees and hedges
        self.op(lambda cv: rect(cv, (1936, 470), 60, 64, 0, (0.68, 0.46, 0.38), 0.95))
        self.add('Leisure', 'SeeSaw', 1936, 456, 0, 1.3)
        self.add('Leisure', 'Slide', 1930, 490, 0, 1.3)
        self.add('Street', 'BikeRack', 1978, 300, 90, 1.0)
        self.add('Street', 'BikeRack', 2160, 300, 90, 1.0)
        for (tx, ty, r) in ((1912, 110, 20), (1990, 100, 17), (2200, 96, 22), (2226, 160, 18), (1910, 380, 17), (2222, 380, 16), (1916, 532, 15), (2228, 536, 16), (2030, 120, 15), (2140, 110, 15)):
            self.crown(tx, ty, r, blossom=0.1)
        for k in range(4):
            self.add('Plants', 'HedgeBlock2', 1964 + k * 38 + 4, 222, 0, 1.0, None, tag='hedge')
