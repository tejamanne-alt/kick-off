# The town map's layout, as data (town_map.py builds the picture and TownMapLayout.json from it).
#
# Everything is in CORE coordinates: x 0..2400, y 0..1350, origin at the top-left of the picture's central 2400 x 1350 core
# (the full picture is 3200 x 1800 and the core sits at x 400, y 225; the ring around it is more town). One metre is PPM px.
# The UI keeps the nodes inside the core's inner area (x 120..2280, y 170..1130) and puts a title over the top 12% and a
# strip of route chips over the bottom 20%, so those bands are kept quiet.
#
# The town is a ladder. Home (H) stands at the corner of the West Street and Elm Street, the school gate (S) on School Lane, and
# long streets run between the two like the rungs of a ladder, so that every route has its own street and a long straight run
# for its nodes. From the north:
#   park       up the West Street, west by Rose Street and Park Lane to the park gate, east through the long park that fills the
#              north of the town (a path), under the railway by a short tunnel, past the school garden, down the East Street
#   underpass  Station Road (y 380): up the West Street, east through the road tunnels under the railway's two tracks
#   site       Yard Road (y 600): up the West Street, then east through the building site (a track between two fenced yards)
#   street     Elm Street (y 820): out of the house and straight east (Elm Street, Hill Road, Garden Lane), then the East Street
#   market     down the West Street, east along Market Street (y 958), up the East Street (Main Road)
#   beach      Seaside Road (y 1136) along the south, then the boardwalk along the sand to the school's promenade
# The railway comes down from the north through the woods, goes over the park path's tunnel and Station Road's two bridges and
# ends at a small station just south of Station Road: only the park and underpass routes cross it, and they go under it.
# The school is by the sea, in the north-east; its football pitch is in its grounds.
#
# The label rules the solver (town_map_nodes.py) and the validator (town_map_check.py) use: the map screen draws the names of the
# focused route's levels only, so a name keeps 30 px from its own route, off the other routes' lines, 6 px from every node disc and
# 6 px from the names of its own route's levels.
import math

PPM = 8.0                       # picture pixels per metre

# ------------------------------------------------------------------ road classes: total width (with pavements), carriageway
CLASSES = {
    'main':   dict(total=100, road=84, pave=8, centre=True),
    'street': dict(total=74, road=60, pave=7, centre=False),
    'avenue': dict(total=72, road=54, pave=9, centre=True),
    'lane':   dict(total=52, road=44, pave=4, centre=False),
    'path':   dict(total=24, road=18, pave=3, centre=False),
    'board':  dict(total=18, road=16, pave=1, centre=False),
    'track':  dict(total=46, road=40, pave=3, centre=False),
}

# ------------------------------------------------------------------ the railway (a gravel bed with two rails), north to south; it ends just south of Station Road
RAIL = dict(pts=[(1540, -300), (1540, -60), (1540, 120), (1540, 260), (1540, 460), (1540, 540)], width=40)
# the station's loop: a second track that leaves the line at y 300, runs beside it to the station and crosses Station Road
# (the underpass) 100 px east of the main line, so the road goes under two tracks (L18: two tunnels)
RAIL2 = dict(pts=[(1540, 270), (1556, 312), (1600, 346), (1640, 376), (1640, 440), (1640, 540)], width=40)

# ------------------------------------------------------------------ junctions
NODES = {
    'H': (420, 820), 'S': (1985, 600),
    # the West Street (x 420): where Station Road, Elm Street, Market Street and Seaside Road leave it
    'wB': (420, 380), 'wA': (420, 430), 'wS': (420, 600), 'wE': (420, 958), 'wF': (420, 1136),
    # the park gate (reached by Park Lane from Rose Street: the park route leaves the West Street where the site route does, 300 px
    # from home, so that it keeps 90 px from the underpass route, which carries on up the West Street)
    'pk_g': (250, 346), 'rW': (250, 600),
    # the park's paths and the short tunnel under the railway
    'pp1': (450, 258), 'pp2': (780, 216), 'pp3': (1090, 176), 'pp4': (1380, 178), 'tpW': (1500, 186), 'tpE': (1580, 186), 'pp5': (1700, 196),
    # the underpass: the road tunnel's two mouths
    'tbW': (1490, 380), 'tbE': (1590, 380),
    # the East Street (x 1855)
    'eA': (1855, 300), 'eB': (1855, 380), 'eS': (1855, 520), 'eC': (1855, 600), 'eD': (1855, 820), 'eE': (1855, 958),
    # the building site's gates
    'st_w': (800, 600), 'st_e': (1462, 600),
    # where Seaside Road meets the sand, and the end of the boardwalk at the school's promenade
    'fa': (1500, 1136), 'ce': (2275, 600),
}


def offset_ctrl(pts, d):
    """Control points shifted d px to the right of the direction of travel (for a parallel path)."""
    out = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1.0
        out.append((p[0] - ty / n * d, p[1] + tx / n * d))
    return out


# the boardwalk along the sand: east along the bottom of the beach, round a corner and north to the school's promenade
BW = [(1650, 1126), (1800, 1123), (1950, 1119), (2100, 1112), (2200, 1096), (2245, 1066), (2275, 1020), (2275, 900), (2275, 760), (2275, 665)]

ROADS = [
    # --- the routes' streets -------------------------------------------------------------------------------------
    ('west_street', 'Home Street', 'street', ['wB', (420, 405), 'wA', (420, 515), 'wS', (420, 710), 'H', (420, 890), 'wE', (420, 1047), 'wF']),
    ('row_c_w1', 'Rose Street', 'street', ['rW', (336, 600), 'wS']),
    ('park_lane', 'Park Lane', 'lane', ['rW', (250, 520), (250, 440), (250, 392), 'pk_g']),
    ('park_path', 'Park path', 'path', ['pk_g', (318, 316), (384, 288), 'pp1', (620, 236), 'pp2', (940, 184), 'pp3', (1230, 176), 'pp4', (1440, 182), 'tpW']),
    ('park_tunnel', 'Park tunnel', 'path', ['tpW', 'tpE']),
    ('park_path_e', 'School garden path', 'path', ['tpE', (1640, 190), 'pp5', (1790, 197), (1851, 214), 'eA']),
    ('row_b_w', 'Station Road', 'street', ['wB', (620, 380), (800, 380), (1000, 380), (1200, 380), (1400, 380), 'tbW']),
    ('tunnel_b', 'Underpass', 'street', ['tbW', 'tbE']),
    ('row_b_e', 'Station Road', 'street', ['tbE', (1700, 380), (1780, 380), 'eB']),
    ('row_c_w', 'Yard Road', 'street', ['wS', (600, 600), 'st_w']),
    ('site_track', 'Site track', 'track', ['st_w', (1000, 600), (1250, 600), 'st_e']),
    ('row_c_e', 'Yard Road', 'street', ['st_e', (1650, 600), (1760, 600), 'eC']),
    ('row_d', 'Elm Street', 'street', ['H', (580, 820), (800, 820), (1100, 820), (1400, 820), (1700, 820), 'eD']),
    ('row_e', 'Market Street', 'street', ['wE', (580, 958), (900, 958), (1200, 958), (1500, 958), (1740, 958), 'eE']),
    ('row_f', 'Seaside Road', 'street', ['wF', (700, 1136), (1100, 1136), (1350, 1136), 'fa']),
    ('boardwalk', 'Boardwalk', 'board', ['fa'] + BW + ['ce']),
    ('east_street', 'Main Road', 'main', ['eA', (1855, 340), 'eB', (1855, 450), 'eS', (1855, 560), 'eC', (1855, 710), 'eD', (1855, 890), 'eE']),
    ('school_lane', 'School Lane', 'street', ['eC', (1915, 600), 'S', (2100, 600), (2200, 600), 'ce']),
]

# --- the rest of the town: streets that no route uses (they cut the strips between the rungs into blocks and fill the ring round the core)
_X0 = -400
ROADS += [
    ('row_b_w0', 'Park Road', 'street', [(_X0, 380), (0, 380), (250, 380), (420, 380)]),
    ('row_c_w0', 'Rose Street', 'street', [(_X0, 600), (0, 600), 'rW']),
    ('oak_street', 'Oak Street', 'street', [(_X0, 820), (0, 820), (250, 820), (420, 820)]),
    ('row_e_w0', 'Mill Street', 'street', [(_X0, 958), (0, 958), (250, 958), (420, 958)]),
    ('row_f_w0', 'Bay Road', 'street', [(_X0, 1136), (0, 1136), (250, 1136), (420, 1136)]),
    ('lime_street', 'Lime Street', 'street', [(-20, 380), (-20, 820), (-20, 1136), (-20, 1350), (-20, 1575)]),
    ('beech_street', 'Beech Street', 'street', [(-330, 380), (-330, 820), (-330, 1136), (-330, 1350), (-330, 1575)]),
    ('lane_700', 'Church Lane', 'lane', [(700, 380), (700, 600), (700, 820), (700, 958), (700, 1136)]),
    ('lane_1000', 'Rose Lane', 'lane', [(1000, 380), (1000, 600)]),
    ('lane_1300', 'Orchard Lane', 'lane', [(1300, 380), (1300, 600)]),
    ('lane_1000s', 'Mill Lane', 'lane', [(1000, 820), (1000, 958), (1000, 1136)]),
    ('lane_1300s', 'Shop Lane', 'lane', [(1300, 820), (1300, 958), (1300, 1136)]),
    ('south_road', 'South Road', 'street', [(_X0, 1350), (0, 1350), (700, 1350), (1400, 1350), (1700, 1350)]),
    ('far_south', 'Mill Lane', 'street', [(_X0, 1560), (700, 1560), (1700, 1560)]),
    ('south_w', 'Home Street South', 'street', [(420, 1136), (420, 1350), (420, 1575)]),
    ('lane_700s', 'Brook Lane', 'lane', [(700, 1136), (700, 1350), (700, 1575)]),
    ('lane_1000t', 'Quay Lane', 'lane', [(1000, 1136), (1000, 1350), (1000, 1575)]),
    ('lane_1300t', 'Quay Street', 'lane', [(1300, 1136), (1300, 1350), (1300, 1575)]),
    ('lane_1600s', 'Dune Lane', 'lane', [(1600, 1136), (1600, 1350), (1600, 1575)]),
]

# ------------------------------------------------------------------ the area polygons (land use, labels)
# The coast: land to the left, sea to the right (the sea polygon is closed far outside the picture).
COAST = [(2500, -300), (2480, 0), (2470, 250), (2470, 500), (2480, 700), (2470, 900), (2440, 1050), (2380, 1180), (2290, 1290), (2180, 1380),
         (2050, 1470), (1950, 1560), (1900, 1650)]
SAND_LAND = [(2262, 200), (2255, 300), (2250, 560), (2040, 566), (2040, 652), (1908, 652), (1906, 1016), (1700, 1052), (1540, 1078), (1500, 1150), (1500, 1650)]
def _blob(cx, cy, rx, ry, seed, n=28, amp=0.14):
    """An irregular rounded outline (woods have no straight edges)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 + amp * math.sin(a * 3 + seed) + amp * 0.6 * math.sin(a * 5 + seed * 1.7) + amp * 0.4 * math.sin(a * 8 + seed * 2.3)
        pts.append((round(cx + math.cos(a) * rx * k), round(cy + math.sin(a) * ry * k)))
    return pts


AREAS = {
    'sea': dict(kind='sea', poly=COAST + [(3400, 1650), (3400, -300)]),
    'sand': dict(kind='sand', poly=SAND_LAND + COAST[::-1]),
    'park': dict(kind='park', poly=[(-260, 75), (1490, 75), (1490, 340), (-260, 340)]),
    'garden': dict(kind='park', poly=[(1575, 75), (1815, 75), (1815, 340), (1575, 340)]),
    'school': dict(kind='school', poly=[(1890, 70), (2240, 70), (2240, 552), (1890, 552)]),
    'market': dict(kind='market', poly=[(380, 850), (470, 850), (470, 884), (1860, 884), (1860, 1100), (380, 1100)]),     # the West Street's lower half and Market Street
    'market_w': dict(kind='market', poly=[(-60, 1000), (380, 1000), (380, 1094), (-60, 1094)]),   # the shop parade west of the West Street (C02's shop windows)
    'site': dict(kind='site', poly=[(800, 428), (1462, 428), (1462, 578), (800, 578)]),            # the building site's yard, north of the track
    'site_s': dict(kind='site', poly=[(800, 622), (1462, 622), (1462, 772), (800, 772)]),          # and south of it
    'station': dict(kind='station', poly=[(1472, 430), (1812, 430), (1812, 556), (1472, 556)]),
    'home_plot': dict(kind='reserve', poly=[(296, 740), (380, 740), (380, 815), (296, 815)]),
    'court': dict(kind='reserve', poly=[(60, 780), (210, 780), (210, 930), (60, 930)]),
    'fields': dict(kind='field', poly=[(-400, -225), (2800, -225), (2800, 70), (-400, 78)]),
    'wood_w': dict(kind='wood', poly=_blob(-40, -110, 450, 128, 1.0)),
    'wood_m': dict(kind='wood', poly=_blob(1180, -118, 330, 118, 2.0)),
    'wood_e': dict(kind='wood', poly=_blob(1870, -118, 300, 118, 3.2)),
    'far_shore': dict(kind='far', poly=[(2700, -225), (2800, -225), (2800, 520), (2740, 470), (2690, 330), (2670, 150), (2680, -40)]),
}
PLACES = {'home': 'H', 'school': 'S'}

# What each route's levels are on (the "Level and map" table of the README, checked by town_map_levels.py): every story node of a
# route lies in the zone named here. 'residential' is the town's default ground (no special area), the rest are the AREAS above or
# the CHECK_ZONES below.
LEVEL_ZONES = {'street': 'residential', 'market': 'market', 'beach': 'sand', 'underpass': 'underpass', 'site': 'site_works', 'park': 'park'}
LAST_ZONE = ('L23', 'school_gate')
CHECK_ZONES = {
    'underpass': [(1290, 320), (1760, 320), (1760, 432), (1290, 432)],
    'school_gate': [(1560, 150), (2020, 150), (2020, 700), (1560, 700)],
    'site_works': [(470, 545), (1800, 545), (1800, 655), (470, 655)],        # Yard Road: the building site stands round wherever its two levels are
    'site_area': [(470, 420), (1800, 420), (1800, 655), (470, 655)],         # the yard and the works round it: where C04's targets are
}
# the challenges that must stand on a particular ground (C05 on the park's lawns, as its level is a park lawn arena)
CHALLENGE_ZONES = {'C03': 'sand', 'C04': 'site_area', 'C05': 'park'}

# ------------------------------------------------------------------ the levels: where each one is (a story node is the point of its route
# nearest to the anchor, free to slide `slack` px along the route to find room for its label; a challenge node is where it says, 130 to 260 px beside its route)
STORY = {
    # street: out of the door, Elm Street's parked cars, Hill Road, Garden Lane, Puddle Lane by the school
    'L01': ('street', (620, 820), 200), 'L02': ('street', (926, 820), 200), 'L03': ('street', (1232, 820), 200), 'L04': ('street', (1538, 820), 200), 'L05': ('street', (1855, 700), 120),
    # market: the market square, the zebra crossing, the corner shop, the fruit stalls, the main road
    'L06': ('market', (420, 890), 60), 'L07': ('market', (741, 958), 250), 'L08': ('market', (1047, 958), 250), 'L09': ('market', (1353, 958), 250), 'L10': ('market', (1659, 958), 300),
    # beach: the boardwalk, the tidal channel, the bay with rocks, the sandcastles
    'L11': ('beach', (1740, 1124), 300), 'L12': ('beach', (2046, 1116), 300), 'L13': ('beach', (2275, 1040), 120), 'L14': ('beach', (2130, 600), 150),
    # underpass and site (chapter 4)
    'L15': ('underpass', (1385, 380), 45), 'L18': ('underpass', (1666, 380), 12),
    'L16': ('site', (1060, 600), 120), 'L17': ('site', (1360, 600), 100),
    # park: the gates, the fountain, the playground, the duck pond, the last stretch to the school gate
    'L19': ('park', (340, 300), 300), 'L20': ('park', (640, 236), 300), 'L21': ('park', (900, 188), 120), 'L22': ('park', (1090, 178), 120), 'L23': ('park', (1690, 196), 300),
}
CHALLENGE = {
    'C01': ('street', (170, 785), 250), 'C02': ('market', (170, 1100), 250), 'C03': ('beach', (2340, 450), 130), 'C04': ('site', (1100, 470), 250), 'C05': ('park', (1250, 318), 55),
}

# ------------------------------------------------------------------ districts: the areas the UI writes names for (the label goes to the point of the area
# that is farthest from routes, nodes and labels)
DISTRICTS = {
    'neighbourhood': dict(poly=[(-300, 480), (200, 480), (200, 1100), (-300, 1100)]),
    'market': dict(poly=[(480, 990), (1750, 990), (1750, 1085), (480, 1085)], clear=40),
    'beach': dict(poly=[(2060, 700), (2300, 700), (2400, 790), (2320, 1050), (2060, 1180)]),
    'sea': dict(poly=[(2500, 800), (2700, 800), (2700, 1300), (2300, 1300), (2300, 1180)]),
    'park': dict(poly=[(-200, 110), (1450, 110), (1450, 320), (-200, 320)]),
    'railway': dict(poly=[(1500, 100), (1580, 100), (1580, 220), (1500, 220)], clear=40),
    'site': dict(poly=[(1050, 440), (1480, 440), (1480, 590), (1050, 590)], clear=40),
    'school': dict(poly=[(1900, 100), (2300, 100), (2300, 300), (1900, 300)]),
}
# street names: (name, road id, the route it must lie on or None, the nodes it goes beside or None, an offset from them). The name goes on
# a straight stretch of the road nearest that point (town_map_build.pick_streets).
STREETS = [
    dict(name='Home Street', road='row_d', route='street', at=(472, 820), reach=50),
    dict(name='Elm Street', road='row_d', route='street', at=(774, 820), reach=90),
    dict(name='Hill Road', road='row_d', route='street', at=(1104, 820), reach=90),
    dict(name='Garden Lane', road='row_d', route='street', at=(1452, 820), reach=90),
    dict(name='Puddle Lane', road='east_street', route=None, at=(1855, 880)),
    dict(name='Market Street', road='row_e', route='market', at=(1000, 958)),
    dict(name='Seaside Road', road='row_f', route='beach', at=(1000, 1136)),
    dict(name='Station Road', road='row_b_w', route='underpass', at=(640, 380)),
    dict(name='Yard Road', road='row_c_w', route=None, at=(700, 600)),
    dict(name='Park Road', road='row_b_w0', route=None, at=(100, 380)),
    dict(name='School Lane', road='school_lane', route=None, at=(2110, 600)),
    dict(name='Main Road', road='east_street', route=None, at=(1855, 450)),
]

ROUTES = {
    'street': ['H', 'eD', 'eC', 'S'],
    'market': ['H', 'wE', 'eE', 'eD', 'eC', 'S'],
    'beach': ['H', 'wE', 'wF', 'fa', 'ce', 'S'],
    'underpass': ['H', 'wB', 'tbW', 'tbE', 'eB', 'eC', 'S'],
    'site': ['H', 'wS', 'st_w', 'st_e', 'eC', 'S'],
    'park': ['H', 'wS', 'rW', 'pk_g', 'pp1', 'pp2', 'pp3', 'pp4', 'tpW', 'tpE', 'pp5', 'eA', 'eB', 'eC', 'S'],
}
