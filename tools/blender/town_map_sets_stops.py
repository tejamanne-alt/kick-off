# The stops between the levels (Levels/RouteTable.cs: one level ends at a stop and the next level on the route starts there), each
# built where the layout puts it (town_map_layout.STOPS, snapped onto its route: town_map_build.place_stops), beside the route line so
# that the map's stop marker sits on the road in front of it. They are the town map's versions of the levels' set pieces
# (Editor/StreetBuilder.Stops.cs): the same places, from the same kit models where the kits have them.
#   Home Street   the bus stop (a shelter on Elm Street's south pavement), granny's pink bungalow, St Mary's church with its tower and
#                 spire at the top of Hill Road, Sam's bright flat-roofed house
#   Market Street the bakery on the market square, the post office, the flower shop, the library (shops built to the south pavement)
#   Seaside Road  the surf school's hut where the boardwalk runs out over the sand, the lifeguard tower, the beach cafe's kiosk
#   Underpass     the station's brick ticket hall at the foot of the railway bridge on Station Road
#   Site          the site office's cabin at the security gate halfway through the building site
#   Park Path     the bandstand inside the gate, the park cafe, the boathouse on the duck pond, grandpa's allotment by the railway
import math
import town_map_place as P
import town_map_models as M
from town_map_sets import (PPM, C_STONE, C_STONE_D, C_PAVE, C_WATER, C_WATER_D, C_BANK, C_WHITE, C_GRASS, C_GRASS_L, C_FLOWERS,
                           ang, bearing, fill, rect, disc, stroke, ellipse, textured)

C_BRICK = (0.74, 0.44, 0.36)
C_SLATE = (0.34, 0.36, 0.42)
C_RAIL_RED = (0.80, 0.18, 0.16)          # the red of the railway's band and the map's train


class StopSets:
    def stops(self):
        for sid in self.B.get('stops', {}):
            fn = getattr(self, 'stop_' + sid, None)
            if fn is not None:
                fn(self.stop_at(sid))

    def stop_at(self, sid):
        s = self.B['stops'][sid]
        return (s['x'], s['y'])

    def shop_front(self, kit, name, x, y_front, face, tints, scale=1.0):
        """A kit shop with its front's middle at (x, y_front), facing `face`, its plot taken."""
        O = P.origin_for(kit, name, (x, y_front), face, scale)
        self.add(kit, name, O[0], O[1], face, scale, tints, tag='stop')
        self.world.occupy(P.footprint(kit, name, O[0], O[1], face, scale, pad=0.4))
        return O

    # ---------------------------------------------------------------- Home Street (Elm Street, y 820)
    def stop_busStop(self, p):
        """A glass-roofed shelter at the back of Elm Street's south pavement, a bench in it, the stop's pole with its round sign at the
        kerb, a bin, a hedge behind, two people waiting."""
        x, y = p[0], 871.0
        self.reserve((x, y + 2), 52, 24)
        self.op(lambda cv: rect(cv, (x, y + 1), 46, 16, 0, C_PAVE, 1.0))
        self.box(x, y, 4.4, 1.6, 2.5, 0, (0.62, 0.72, 0.78), tag='shelter')                 # the glass roof
        self.box(x, y + 6, 4.4, 0.2, 2.3, 0, (0.30, 0.34, 0.40), tag='shelter')             # the back panel's frame
        self.add('Street', 'Bench', x, y + 1, 0, 0.9, None, tag='bench')
        self.box(x - 24, 861, 0.15, 0.15, 2.8, 0, (0.35, 0.36, 0.40), tag='pole')
        self.box(x - 24, 861, 0.7, 0.12, 0.7, 0, (0.85, 0.20, 0.18), z=2.4, tag='sign', roof='round')
        self.add('Street', 'Bin', x + 26, 866, 0, 1.0)
        for hx in (x - 14, x + 14):
            self.add('Plants', 'HedgeBlock2', hx, y + 13, 0, 1.0, None, tag='hedge')
        self.person(x - 10, 862, 200)
        self.person(x + 12, 863, 160)

    def stop_granny(self, p):
        """Granny's pink bungalow on the south side of Elm Street at the foot of Hill Road: a white picket fence with a gate, roses and
        flower beds either side of the path, her ginger cat on the gatepost, granny at the gate."""
        x = p[0]
        front = 864.0
        self.shop_front('Buildings', 'Bungalow', x, front, 0.0, [(0.96, 0.82, 0.86), (0.97, 0.97, 0.95), (0.55, 0.40, 0.38)])
        self.reserve((x, 890), 80, 58)
        self.line_of([(x - 36, 860), (x + 36, 860)], 'Street', 'PicketFence2', 16, [(0.97, 0.97, 0.95)], skip=[(x, 860, 6)])
        for sx in (-1, 1):
            self.add('Street', 'WallPillar', x + sx * 6, 860, 0, 0.6, [(0.97, 0.97, 0.95)], tag='gate')
            for k in range(5):
                fx = x + sx * (14 + k * 4.5)
                self.op(lambda cv, fx=fx, c=C_FLOWERS[k % len(C_FLOWERS)]: disc(cv, (fx, 862), 2.3, c, 0.95), post=True)
            self.add('Plants', 'ShrubFlowering', x + sx * 33, 866, 0, 1.1, None, tag='roses')
        self.add('Animals', 'Cat', x + 6, 859, 30, 3.0, [(0.92, 0.55, 0.22)], z=1.15, tag='cat')
        self.person(x - 2, 856, 0)

    def stop_church(self, p):
        """St Mary's at the top of Hill Road: a stone church with its gable to the street, a square tower with a slate spire at its front,
        the churchyard wall with its gateway, a path, conifers, a bench, a few gravestones and the notice board."""
        x = p[0] + 4
        self.reserve((x, 722), 88, 120)
        self.op(lambda cv: rect(cv, (x, 722), 86, 118, 0, (0.45, 0.58, 0.34), 1.0))           # the churchyard's grass
        self.op(lambda cv: rect(cv, (x, 772), 8, 18, 0, C_STONE, 1.0))                        # the path to the door
        # the nave (7 x 10 m: stone walls under a slate roof, its ridge running back from the street) and the tower (3.6 m square,
        # 12 m) at its front, with a slate spire stepping in to a gold cross
        self.box(x, 714, 7.0, 10.0, 5.0, 0, (0.80, 0.77, 0.70), tag='church')
        self.box(x, 714, 7.6, 10.6, 3.4, 0, C_SLATE, z=4.9, tag='church', roof='ridge')
        self.box(x, 765, 3.6, 3.6, 12.0, 0, (0.76, 0.73, 0.66), tag='tower')
        z = 12.0
        for (w, h) in ((3.0, 1.4), (2.2, 1.6), (1.4, 1.8), (0.6, 2.2)):
            self.box(x, 765, w, w, h, 0, C_SLATE, z=z, tag='spire')
            z += h
        self.box(x, 765, 0.15, 0.9, 0.12, 0, (0.92, 0.82, 0.40), z=z + 0.2, tag='cross')
        # the churchyard: the wall along the pavement with a gateway, conifers, gravestones, a bench, the notice board
        self.line_of([(x - 42, 781), (x + 42, 781)], 'Street', 'BlockWall2', 16, [(0.78, 0.74, 0.66)], skip=[(x, 781, 8)], tag='wall')
        for (cx, cy) in ((x - 36, 674), (x + 36, 672), (x - 36, 744)):
            self.add('Plants', 'ConiferMid', cx, cy, 0, 1.0, None, tag='conifer')
        for k in range(5):
            self.box(x + 36, 690 + k * 12, 0.6, 0.25, 0.8, 0, (0.70, 0.70, 0.68), tag='grave')
        self.add('Street', 'Bench', x - 34, 768, 90, 0.9)
        self.add('Leisure', 'SignBoard', x + 18, 778, 180, 0.9, [(0.25, 0.30, 0.40)], tag='board')

    def stop_samsHouse(self, p):
        """Sam's bright flat-roofed house in Garden Lane: a yellow house with a blue door, bikes and a ball on the lawn, Sam at the gate."""
        x = p[0]
        self.shop_front('Buildings', 'HouseFlat', x, 770.0, 180.0, [(0.98, 0.84, 0.36), (0.22, 0.46, 0.78), (0.86, 0.86, 0.82)])
        self.reserve((x, 742), 76, 70)
        self.op(lambda cv: rect(cv, (x, 776), 70, 12, 0, C_GRASS_L, 1.0))
        self.op(lambda cv: rect(cv, (x + 8, 776), 6, 12, 0, C_STONE, 1.0))
        self.add('Street', 'Bicycle', x - 22, 775, 80, 1.0, None, tag='bike')
        self.add('Street', 'Bicycle', x - 12, 777, 100, 1.0, None, tag='bike')
        self.box(x + 22, 776, 0.3, 0.3, 0.3, 0, (0.97, 0.97, 0.97), tag='ball', roof='round')
        self.line_of([(x - 36, 782), (x + 36, 782)], 'Street', 'PicketFence2', 16, [(0.30, 0.55, 0.80)], skip=[(x + 8, 782, 6)])
        self.person(x + 8, 786, 180)

    # ---------------------------------------------------------------- Market Street (y 958): shops built to its south pavement
    def market_shop(self, x, kit, name, tints, bits):
        front = 958.0 + 37.0 + 3.0
        self.shop_front(kit, name, x, front, 0.0, tints)
        w = M.width(kit, name) * PPM
        P.shop_awnings(self.items, (x, front), 0.0, w, tints[1])
        for (kit2, name2, dx, dy, face, scale, tint) in bits:
            self.add(kit2, name2, x + dx, front - dy, face, scale, tint, tag='bit')

    def stop_bakery(self, p):
        """The bakery on the market square: a cream shop with brown trim and awnings, a chalkboard, a bench, a planter, a bike."""
        self.market_shop(p[0], 'Buildings', 'ShopCafe', [(0.98, 0.92, 0.80), (0.62, 0.38, 0.22), (0.42, 0.30, 0.26)],
                         [('Street', 'SignBoardA', -16, 8, -20, 1.0, None), ('Street', 'Bench', 20, 8, 0, 1.0, None),
                          ('Street', 'Planter1', -30, 7, 0, 1.0, None), ('Street', 'Bicycle', 36, 7, 8, 1.0, None)])

    def stop_postOffice(self, p):
        """The post office: a tall shop in red and cream, the post box at the kerb, a bike rack with a red bike."""
        self.market_shop(p[0], 'Buildings', 'ShopTall', [(0.97, 0.94, 0.86), (0.82, 0.18, 0.16), (0.34, 0.36, 0.42)],
                         [('Street', 'PostBox', -14, 10, 0, 1.0, None), ('Street', 'BikeRack', 18, 7, 0, 1.0, None),
                          ('Street', 'Bicycle', 16, 8, 0, 1.0, [(0.82, 0.18, 0.16)])])

    def stop_florist(self, p):
        """The flower shop: white and green, buckets and pots of flowers out front under the window, an A-board."""
        bits = [('Street', 'SignBoardA', 12, 8, 15, 1.0, None)]
        for i in range(5):
            bits.append(('Street', 'PotGroup' if i % 2 == 0 else 'PotA', -30 + i * 9, 6, 0, 1.0, [C_FLOWERS[i % len(C_FLOWERS)]]))
        self.market_shop(p[0], 'Buildings', 'ShopFlorist', [(0.95, 0.97, 0.93), (0.36, 0.58, 0.42), (0.30, 0.34, 0.36)], bits)
        for i in range(6):
            fx = p[0] - 30 + i * 9
            self.op(lambda cv, fx=fx, c=C_FLOWERS[(i + 2) % len(C_FLOWERS)]: disc(cv, (fx, 1000), 2.6, c, 0.95), post=True)

    def stop_library(self, p):
        """The library: a stone-coloured building with blue trim, a bike rack with bikes, a bench, a planter."""
        self.market_shop(p[0], 'Buildings', 'ShopBooks', [(0.85, 0.78, 0.68), (0.24, 0.36, 0.60), (0.30, 0.32, 0.38)],
                         [('Street', 'BikeRack', -18, 7, 0, 1.0, None), ('Street', 'Bicycle', -21, 8, 0, 1.0, [(0.25, 0.45, 0.65)]),
                          ('Street', 'Bench', 18, 8, 0, 1.0, None)])

    # ---------------------------------------------------------------- the beach
    def stop_surfSchool(self, p):
        """The surf school's white and blue hut on the sand, on the sea side of the boardwalk where it runs out from the end of Seaside
        Road (the land side is the market's back yards), with its board racks, its flag and towels."""
        x, front = p[0] - 6, 1137.0
        self.shop_front('Buildings', 'Garage', x, front, 0.0, [(0.97, 0.97, 0.95), (0.18, 0.50, 0.78), (0.85, 0.42, 0.32)])
        self.reserve((x, 1162), 70, 56)
        for dx in (-28, 28):
            self.add('Barriers', 'SurfRack', x + dx, 1148, 0, 1.2, None, tag='surfrack')
        self.add('Street', 'BannerFlag', x + 44, 1140, 0, 1.4, [(0.18, 0.50, 0.78), (0.97, 0.97, 0.95)], tag='flag')
        for k, col in enumerate(((0.95, 0.55, 0.6), (1.0, 0.85, 0.35))):
            self.add('Leisure', 'BeachTowel', x - 44 + k * 14, 1150 + k * 3, 10, 1.2, [col, (0.97, 0.93, 0.84)], tag='towel')
        self.person(x + 14, 1136, 0)

    def stop_lifeguard(self, p):
        """The lifeguard tower on the sand south of the boardwalk, looking out to sea, with its rescue boards, the red and yellow flags
        and a lifeguard."""
        x = p[0] + 8
        self.add('Leisure', 'LifeguardTower', x, 1166, 135, 1.3, None, tag='lifeguard')
        self.reserve((x, 1166), 40, 40)
        self.add('Barriers', 'RescueBoardStand', x + 36, 1152, 90, 1.2, None, tag='rescue')
        for dx in (-18, 30):
            self.add('Street', 'BannerFlag', x + dx, 1140, 0, 1.4, [(0.90, 0.20, 0.18), (1.0, 0.82, 0.20)], tag='flag')
        self.person(x + 18, 1176, 135)

    def stop_beachCafe(self, p):
        """The beach cafe's kiosk on the sand beside the boardwalk below the school, with tables, parasols and people."""
        x, y = p[0] - 40, p[1]
        self.reserve((x, y), 60, 60)
        self.op(lambda cv: rect(cv, (x + 4, y), 54, 46, 0, (0.66, 0.50, 0.34), 1.0))         # the deck
        for k in range(-5, 6):
            self.op(lambda cv, k=k: stroke(cv, [(x - 23, y + k * 4), (x + 31, y + k * 4)], 0.8, (0.40, 0.28, 0.18), 0.6), post=True)
        self.box(x - 8, y, 4.0, 3.0, 2.8, 90, (0.95, 0.93, 0.86), tag='kiosk')
        self.box(x - 8, y, 4.6, 3.6, 0.35, 90, (0.20, 0.58, 0.62), z=2.8, tag='kiosk', roof='round')
        for (dx, dy) in ((14, -14), (16, 14)):
            self.add('Leisure', 'PicnicTable', x + dx, y + dy, 0, 1.0, None, tag='table')
            self.add('Leisure', 'Parasol', x + dx, y + dy, 0, 1.1, [(0.20, 0.58, 0.62), (0.97, 0.93, 0.84)], tag='parasol')
        self.person(x + 4, y + 2, 90)

    # ---------------------------------------------------------------- the station, the site office
    def stop_station(self, p):
        """The station's brick ticket hall on Station Road at the foot of the railway bridge (west of the main line): a slate roof, the
        railway's red band along its front, a clock, a forecourt with a bike rack, a bench and travellers; the platforms are up between
        the tracks, behind it."""
        x, y = p[0] - 10, 448.0
        self.reserve((x, y), 72, 56)
        self.op(lambda cv: textured(cv, [(x - 38, 418), (x + 30, 418), (x + 30, 478), (x - 38, 478)], (0.76, 0.74, 0.70), 73, amp=(0.03, 0.02, 0.02), cells=(30, 8, 3)))
        self.box(x, y + 4, 5.4, 7.4, 4.4, 90, C_BRICK, tag='hall')                         # 7.4 m along the road, its ridge too
        self.box(x, y + 4, 5.9, 7.9, 2.6, 90, C_SLATE, z=4.4, tag='hall', roof='ridge')
        self.box(x, y - 18, 7.6, 0.2, 0.3, 0, C_RAIL_RED, z=3.6, tag='band')
        self.box(x + 14, y - 19, 0.7, 0.15, 0.7, 0, (0.97, 0.97, 0.95), z=3.0, tag='clock', roof='round')
        self.add('Street', 'BikeRack', x - 28, 426, 0, 1.0)
        self.add('Street', 'Bench', x + 24, 426, 0, 0.9)
        self.add('Leisure', 'SignBoard', x - 16, 422, 0, 1.0, [C_RAIL_RED], tag='sign')
        for (dx, dy, f) in ((-4, 424, 20), (8, 427, 300), (18, 422, 90)):
            self.person(x + dx, dy, f)

    def stop_siteOffice(self, p):
        """The site office halfway through the building site: the blue and white cabin beside the track, the security gate across it (a
        boom barrier and the intercom post), a portable loo, a cement mixer, a wheelbarrow and a builder."""
        x = p[0]
        self.add('Works', 'SiteCabin', x + 10, 572, 180, 1.0, [(0.22, 0.40, 0.68), (0.97, 0.97, 0.95), None], tag='site')
        self.box(x - 24, 600, 0.3, 5.6, 1.1, 0, (0.95, 0.80, 0.20), z=0.9, tag='boom')
        self.add('Barriers', 'BoomBarrier', x - 24, 600, 90, 1.0, None, tag='boom')
        self.add('Works', 'IntercomPost', x - 34, 628, 0, 1.0, None, tag='gate')
        self.add('Works', 'PortaLoo', x + 44, 562, 180, 1.0, [(0.22, 0.40, 0.68)])
        self.add('Works', 'CementMixer', x - 20, 640, 30, 1.0, [(0.95, 0.5, 0.15)])
        self.add('Works', 'Wheelbarrow', x + 12, 642, -25, 1.2)
        self.person(x - 6, 584, 180)

    # ---------------------------------------------------------------- the park (its path)
    def stop_bandstand(self, p):
        """The park's white bandstand on a round paved floor north of the path, benches round it, flower beds."""
        c = (p[0] - 8, 196.0)
        self.reserve(c, 70, 70)
        self.op(lambda cv: (disc(cv, c, 34, (0.74, 0.72, 0.67), 1.0), disc(cv, c, 30, (0.84, 0.82, 0.77), 1.0)))
        self.op(lambda cv: rect(cv, (c[0], (c[1] + p[1]) / 2 + 8), 8, p[1] - c[1] - 30, 0, (0.80, 0.77, 0.71), 1.0))
        self.add('Leisure', 'Gazebo', c[0], c[1], 0, 1.3, [(0.97, 0.97, 0.95), (0.30, 0.50, 0.42)], tag='bandstand')
        for (dx, dy, f) in ((-40, 6, 90), (40, 6, 270)):
            self.add('Street', 'Bench', c[0] + dx, c[1] + dy, f, 1.0)
        for k in range(10):
            a = -0.4 + k * 0.33
            self.op(lambda cv, a=a, k=k: disc(cv, (c[0] + math.cos(a + 3.6) * 42, c[1] + math.sin(a + 3.6) * 42), 3.0, C_FLOWERS[k % len(C_FLOWERS)], 0.95))

    def stop_parkCafe(self, p):
        """The park cafe beside the path: a white shop with green trim facing the path, a terrace with tables under parasols."""
        x = p[0] + 16
        self.shop_front('Buildings', 'ShopCafe', x, p[1] - 22, 180.0, [(0.96, 0.95, 0.88), (0.30, 0.50, 0.32), (0.34, 0.30, 0.28)])
        self.op(lambda cv: rect(cv, (x, p[1] - 16), 66, 10, 0, C_PAVE, 1.0))
        for dx in (-26, 30):
            self.add('Leisure', 'PicnicTable', x + dx, p[1] - 14, 90, 0.9, None, tag='table')
            self.add('Leisure', 'Parasol', x + dx, p[1] - 14, 0, 1.0, [(0.30, 0.50, 0.32), (0.97, 0.93, 0.84)], tag='parasol')

    def stop_boathouse(self, p):
        """The boathouse at the west end of the duck pond: a wooden shed with a green roof, its door to the water, a raft at the jetty."""
        x, y = p[0] + 42, 118.0
        self.add('Buildings', 'Garage', x, y, 90, 1.0, [(0.62, 0.44, 0.30), (0.25, 0.42, 0.32), (0.25, 0.42, 0.32)], tag='boathouse')
        self.reserve((x - 22, y), 40, 40)
        self.op(lambda cv: rect(cv, (x + 10, y + 8), 20, 6, 0, (0.62, 0.46, 0.30), 1.0), post=True)    # the jetty
        self.add('Leisure', 'Raft', x + 26, y + 16, 0, 1.2, None, tag='raft')
        self.add('Street', 'Bench', x - 30, p[1] - 20, 0, 1.0)

    def stop_allotment(self, p):
        """Grandpa's allotment at the railway end of the park: vegetable beds in rows, a green shed, a wheelbarrow, a low fence along
        the path with its gate, a birch, and grandpa among the rows."""
        x0, x1, y0, y1 = p[0] - 78, p[0] + 2, 96.0, 162.0
        self.reserve(((x0 + x1) / 2, (y0 + y1) / 2), x1 - x0 + 6, y1 - y0 + 6)
        self.op(lambda cv: rect(cv, ((x0 + x1) / 2, (y0 + y1) / 2), x1 - x0, y1 - y0, 0, (0.55, 0.42, 0.32), 1.0))
        for k in range(5):
            yy = y0 + 10 + k * 12
            self.op(lambda cv, yy=yy: rect(cv, ((x0 + x1) / 2 - 8, yy), x1 - x0 - 26, 5, 0, (0.40, 0.58, 0.30), 1.0), post=True)
            for j in range(6):
                self.add('Plants', 'BushRound' if k % 2 else 'GrassTuft', x0 + 10 + j * 9, yy, (j * 47) % 360, 0.5 if k % 2 else 1.1, None, tag='veg')
        self.add('Buildings', 'Garage', x1 - 4, y0 + 22, 90, 0.8, [(0.40, 0.58, 0.42), (0.95, 0.93, 0.85), (0.30, 0.30, 0.32)], tag='shed')
        self.add('Works', 'Wheelbarrow', x1 - 26, y1 - 8, 25, 1.2)
        self.line_of([(x0, y1 + 4), (x1, y1 + 4)], 'Street', 'PicketFence2', 16, [(0.62, 0.50, 0.38)], skip=[(x1 - 16, y1 + 4, 6)])
        self.add('Plants', 'Birch', x0 - 8, y0 + 6, 0, 1.0, None, tag='tree')
        self.person(x0 + 34, y0 + 30, 200)
