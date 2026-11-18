"""Florida's map rendered in Blender from the game's own kits (the Miami, Florida, Plants and Cars kits), as the town's map is
(town_map.py), on the layout tools/miami_map/miami_map.py writes: the same routes, nodes, stops, districts and street labels,
so the game's route lines and markers land on the picture's streets.

    cd tools/blender && blenv/bin/python miami_map_render.py -- [--scale 0.5] [--samples 24] [--out path.jpg]

It is an aerial view from the south, looking down at 38 degrees (an orthographic camera): the ground is laid out so that a point
of the layout (x, y in picture pixels) is at that pixel, and everything standing on it rises up the picture, its front (the kits'
-Y, turned south) toward the viewer. Little Havana's low pastel shops and ranch houses under royal palms and live oaks, Calle
Ocho and its buses; the Miami River with its docks, tugs and a freighter; Brickell's glass towers and Brickell Avenue's palm
median; downtown's Deco blocks, the Mediterranean Revival tower and the Metrorail and Metromover guideways; Bayfront Park, Museum
Park and the museum; the bay with a cruise ship at the port and Miami Beach's Deco strip beyond. No text, route lines or
markers: the game draws those. Writes Assets/_Game/Resources/UI/MiamiMap.jpg (3200 x 1800)."""
import bpy, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'miami_map'))
import town_map_kit as K
import miami_map as MM
from PIL import Image, ImageDraw, ImageFilter

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RES = float(args[args.index('--scale') + 1]) if '--scale' in args else 1.0
SAMPLES = int(args[args.index('--samples') + 1]) if '--samples' in args else 24
OUT = args[args.index('--out') + 1] if '--out' in args else MM.OUT_IMAGE
W, H = MM.W, MM.H
PPM = 4.0                                     # picture pixels per metre on the ground
TILT = math.radians(48.0)                     # the camera's turn from straight down (it looks down at 42 degrees)
COS = math.cos(TILT)
SUN = Vector((0.45, -0.62, 0.78)).normalized()    # towards the sun: the south-east, a Miami morning
rng = random.Random(305)


def X(px): return (px - W / 2) / PPM
def Y(py): return (H / 2 - py) / PPM / COS


# ---------------------------------------------------------------- the plan: streets, blocks, water, parks (picture pixels)
NS_STREETS = [(-40, 30), (220, 34), (460, 34), (700, 56), (940, 34), (1180, 34), (1420, 34), (1660, 34), (1950, 64), (2200, 34),
              (2380, 30), (2600, 70)]                     # (x, width): 700 and 1950 (Brickell Avenue) and 2600 (Biscayne) are main
EW_STREETS = [(180, 34), (400, 34), (760, 34), (1000, 60), (1250, 44), (1480, 34), (1700, 34)]   # 1000: Calle Ocho
MAIN = {700, 1950, 2600, 1000}
COAST = 2680
PARKS = [(2250, 680, COAST - 14, 860), (2470, 300, COAST - 14, 480), (1000, 1050, 1120, 1130)]
PORT = (2780, 440, 2990, 610)                 # Dodge Island: the cruise port
BEACH = 2990                                  # Miami Beach's strip begins


def river(): return MM.river_points()


def in_box(x, y, b, pad=0): return b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad


def near_river(x, y, pad=60):
    pts = river()
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / float(dx * dx + dy * dy)))
        if math.hypot(ax + dx * t - x, ay + dy * t - y) < pad:
            return True
    return False


def coast_x(y): return COAST + 22 * math.sin(y / 170.0)


def district(x, y):
    if x >= coast_x(y) - 8: return 'water'
    for b in PARKS:
        if in_box(x, y, b): return 'park'
    if near_river(x, y): return 'river'
    if x > 1680 and 800 < y < 1240: return 'brickell'
    if x > 1680 and y <= 800: return 'downtown'
    return 'havana'


def blocks():
    xs = sorted(NS_STREETS); ys = sorted(EW_STREETS)
    for (x0, w0), (x1, w1) in zip(xs, xs[1:]):
        for (y0, h0), (y1, h1) in zip([(-80, 34)] + ys, ys + [(H + 80, 34)]):
            yield (x0 + w0 / 2 + 6, y0 + h0 / 2 + 6, x1 - w1 / 2 - 6, y1 - h1 / 2 - 6)


# ---------------------------------------------------------------- the painted ground
LAND, YARD, LAWN, PARK = (226, 221, 208), (200, 210, 166), (170, 200, 132), (146, 192, 116)
ASPHALT, WALK, LINE, YELLOW = (104, 106, 112), (214, 210, 200), (240, 240, 236), (238, 196, 70)
WATER, DEEP, SAND = (96, 186, 196), (52, 138, 172), (238, 224, 190)


def paint(path):
    img = Image.new('RGB', (W, H), LAND)
    d = ImageDraw.Draw(img)
    # the blocks: yards in Little Havana, paved plazas downtown and in Brickell
    for b in blocks():
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        kind = district(cx, cy)
        if kind == 'havana':
            d.rectangle(b, fill=YARD)
            for _ in range(5):
                px, py = rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3])
                d.ellipse((px - 26, py - 18, px + 26, py + 18), fill=(184, 204, 148))
            for k in range(int(b[0]) + 30, int(b[2]) - 20, 56):        # driveways out to the street
                d.rectangle((k, b[3] - 26, k + 9, b[3]), fill=(214, 210, 200))
        elif kind in ('brickell', 'downtown'):
            d.rectangle(b, fill=(214, 210, 200))
            d.rectangle((b[0] + 10, b[1] + 10, b[2] - 10, b[3] - 10), fill=(224, 218, 204))
            for _ in range(3):                                          # plazas' lawns and planters
                px, py = rng.uniform(b[0] + 30, b[2] - 30), rng.uniform(b[1] + 30, b[3] - 30)
                d.rounded_rectangle((px - 34, py - 22, px + 34, py + 22), radius=10, fill=(176, 204, 142))
    # the parks with their paths
    for b in PARKS:
        d.rectangle(b, fill=PARK)
    for b in PARKS[:2]:
        d.line([(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2)], fill=(232, 224, 204), width=10)
        d.line([((b[0] + b[2]) / 2, b[1]), ((b[0] + b[2]) / 2, b[3])], fill=(232, 224, 204), width=10)
    d.ellipse((2420, 730, 2500, 810), fill=(232, 224, 204))
    d.ellipse((2436, 746, 2484, 794), fill=WATER)                       # Bayfront Park's fountain
    d.rectangle((700, 1278, 1760, 1300), fill=PARK)                      # the Underline's strip of park under the line
    d.line([(700, 1292), (1760, 1292)], fill=(232, 224, 204), width=6)
    # the streets: sidewalks, asphalt, the lines
    for x, w in NS_STREETS:
        d.rectangle((x - w / 2 - 6, 0, x + w / 2 + 6, H), fill=WALK)
    for y, w in EW_STREETS:
        d.rectangle((0, y - w / 2 - 6, coast_x(y) - 20, y + w / 2 + 6), fill=WALK)
    for x, w in NS_STREETS:
        d.rectangle((x - w / 2, 0, x + w / 2, H), fill=ASPHALT)
    for y, w in EW_STREETS:
        d.rectangle((0, y - w / 2, coast_x(y) - 26, y + w / 2), fill=ASPHALT)
    for x, w in NS_STREETS:
        if x in MAIN:
            if x == 1950:
                d.rectangle((x - 5, 0, x + 5, H), fill=(150, 186, 110))      # Brickell Avenue's planted median
            else:
                d.line([(x - 2, 0), (x - 2, H)], fill=YELLOW, width=2); d.line([(x + 2, 0), (x + 2, H)], fill=YELLOW, width=2)
            for k in (-1, 1):
                for y in range(0, H, 28):
                    d.line([(x + k * w / 4, y), (x + k * w / 4, y + 14)], fill=LINE, width=2)
        else:
            for y in range(0, H, 30):
                d.line([(x, y), (x, y + 14)], fill=LINE, width=2)
    for y, w in EW_STREETS:
        if y in MAIN:
            d.line([(0, y - 2), (coast_x(y) - 26, y - 2)], fill=YELLOW, width=2); d.line([(0, y + 2), (coast_x(y) - 26, y + 2)], fill=YELLOW, width=2)
            for k in (-1, 1):
                for x in range(0, int(coast_x(y)) - 30, 28):
                    d.line([(x, y + k * w / 4), (x + 14, y + k * w / 4)], fill=LINE, width=2)
        else:
            for x in range(0, int(coast_x(y)) - 30, 30):
                d.line([(x, y), (x + 14, y)], fill=LINE, width=2)
    # crossings on the main roads
    for x, w in NS_STREETS:
        for y, h in EW_STREETS:
            if x in MAIN or y in MAIN:
                for k in range(-int(w / 2) + 3, int(w / 2) - 2, 7):
                    d.rectangle((x + k, y - h / 2 - 12, x + k + 3, y - h / 2 - 2), fill=LINE)
                    d.rectangle((x + k, y + h / 2 + 2, x + k + 3, y + h / 2 + 12), fill=LINE)
    # the river: its seawalls, its water, the docks along the Riverwalk
    pts = river()
    d.line(pts, fill=(205, 202, 194), width=84, joint='curve')
    d.line(pts, fill=WATER, width=72, joint='curve')
    d.line(pts, fill=(78, 166, 186), width=40, joint='curve')
    for x in range(1050, 1700, 130):
        d.rectangle((x, 617, x + 30, 634), fill=(150, 120, 90))
    # the bay: shallows by the coast, deeper out; the port island, Miami Beach and the ocean beyond
    for x in range(int(COAST) - 40, W):
        t = min(1.0, max(0.0, (x - COAST) / 300.0))
        c = tuple(int(WATER[i] * (1 - t) + DEEP[i] * t) for i in range(3))
        d.line([(x, 0), (x, H)], fill=c)
    coast = [(0, 0)] + [(coast_x(y), y) for y in range(0, H + 30, 30)] + [(0, H)]
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon(coast, fill=255)
    land = img.copy()
    img = Image.new('RGB', (W, H), DEEP)
    img.paste(land, (0, 0))
    d = ImageDraw.Draw(img)
    for x in range(int(COAST) - 40, W):
        t = min(1.0, max(0.0, (x - COAST) / 300.0))
        c = tuple(int(WATER[i] * (1 - t) + DEEP[i] * t) for i in range(3))
        d.line([(x, 0), (x, H)], fill=c)
    img.paste(land, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.line([(coast_x(y), y) for y in range(0, H + 30, 30)], fill=(206, 203, 196), width=8)        # the bay's seawall
    d.rounded_rectangle(PORT, radius=26, fill=(214, 211, 204))
    d.rounded_rectangle((PORT[0] + 12, PORT[1] + 12, PORT[2] - 12, PORT[3] - 12), radius=20, fill=(226, 223, 216))
    d.polygon([(BEACH, 0), (3090, 0), (3120, 900), (3070, H), (BEACH + 10, H), (BEACH + 20, 900)], fill=(206, 214, 180))
    d.polygon([(3060, 0), (3090, 0), (3120, 900), (3070, H), (3040, H), (3080, 900)], fill=SAND)
    d.rectangle((3118, 0, W, H), fill=(40, 120, 168))
    d.line([(3120, 0), (3120, H)], fill=(250, 250, 246), width=5)     # the surf line
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(path)
    return path


# ---------------------------------------------------------------- the Blender scene
def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.reset()
    S = bpy.context.scene
    S.render.engine = 'BLENDER_EEVEE'
    try:
        S.view_settings.view_transform = 'Standard'; S.view_settings.look = 'None'
    except Exception:
        pass
    try:
        S.eevee.use_shadows = True
    except Exception:
        pass
    return S


def ground(S, png, margin=200.0):
    w, h = W / PPM, H / PPM / COS
    hw, hh = w / 2 + margin, h / 2 + margin
    me = bpy.data.meshes.new('ground')
    me.from_pydata([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)], [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    u0, u1 = -(hw - w / 2) / w, 1 + (hw - w / 2) / w
    v0, v1 = -(hh - h / 2) / h, 1 + (hh - h / 2) / h
    for loop, (u, v) in zip(me.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
        uv.data[loop.index].uv = (u, v)
    o = bpy.data.objects.new('ground', me)
    S.collection.objects.link(o)
    m = bpy.data.materials.new('ground')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png, check_existing=True)
    tex.extension = 'EXTEND'
    nt.links.new(K.shade(nt, tex.outputs['Color']), out.inputs['Surface'])
    me.materials.append(m)


def lights(S):
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    S.collection.objects.link(sun)
    sun.data.color = (1.0, 0.96, 0.88)
    sun.data.energy = 3.4
    sun.data.angle = math.radians(3.0)
    sun.rotation_euler = (-SUN).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('sky')
    S.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.62, 0.76, 0.96, 1)
    bg.inputs['Strength'].default_value = 0.6


def camera(S):
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    S.collection.objects.link(cam)
    S.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.ortho_scale = W / PPM
    # turned TILT from looking straight down, toward the north: the ground shows at cos(TILT), heights at sin(TILT)
    dist = 2500.0
    cam.location = (0, -dist * math.sin(TILT), dist * math.cos(TILT))
    cam.rotation_euler = (TILT, 0, 0)
    cam.data.clip_start = 10
    cam.data.clip_end = 8000
    S.render.resolution_x = int(W * RES)
    S.render.resolution_y = int(H * RES)
    S.render.resolution_percentage = 100


# ---------------------------------------------------------------- what stands on it
placed = 0


def put(kit, name, px, py, face=180.0, scale=1.0, z=0.0, tints=None, where='build'):
    """where: 'build' keeps out of the water, the river and the parks; 'land' only out of the water and the river; 'water' anywhere."""
    global placed
    if not K.has(kit, name):
        return None
    if where != 'water' and (px > coast_x(py) - 14 and px < BEACH or near_river(px, py, 46)):
        return None
    if where == 'build' and any(in_box(px, py, b, 6) for b in PARKS):
        return None
    placed += 1
    return K.place(kit, name, X(px), Y(py), face=face, scale=scale, z=z, tints=tints)


def free_of_route(px, py, pad=34):
    for pts in MM.ROUTES.values():
        if MM.on_route((px, py), pts) < pad:
            return False
    return True


SHOPS = ['VentanitaMIA', 'TabaqueriaMIA', 'FruteriaMIA', 'MuralWallMIA', 'MuralShedMIA', 'DominoParkMIA']
HOUSES = [('Florida', 'RanchFL'), ('Florida', 'RanchSmallFL'), ('Florida', 'CottageFL')]
ROOFS = [(0.80, 0.44, 0.32), (0.86, 0.52, 0.38), (0.95, 0.94, 0.90), (0.72, 0.80, 0.86), (0.80, 0.44, 0.32)]   # barrel tile, white, metal
HOUSE_TINTS = [(0.70, 0.86, 0.82), (0.98, 0.86, 0.62), (0.96, 0.72, 0.70), (0.98, 0.96, 0.90), (0.80, 0.84, 0.96)]
TREES = [('Plants', 'PalmRoyal', 0.9), ('Plants', 'PalmSabalTall', 1.0), ('Plants', 'LiveOak', 0.9), ('Plants', 'BroadleafWide', 1.0),
         ('Plants', 'PalmSabal', 1.0)]


def tree(px, py, kinds=TREES):
    kit, name, s = kinds[rng.randrange(len(kinds))]
    put(kit, name, px, py, face=rng.uniform(0, 360), scale=s * rng.uniform(0.85, 1.15), where='land')


def havana_block(b):
    x0, y0, x1, y1 = b
    on_ocho = abs(y1 - (1000 - 30 - 6)) < 8           # the block's south edge is Calle Ocho's north sidewalk
    south_of_ocho = abs(y0 - (1000 + 30 + 6)) < 8     # its north edge is the south sidewalk
    n = max(1, int((y1 - y0) / 78))
    rows = [y1 - 6 - k * (y1 - y0 - 30) / max(1, n - 1 if n > 1 else 1) for k in range(n)] if n > 1 else [y1 - 6]
    if south_of_ocho: rows = [y0 + 36] + rows[:-1]
    for r, ry in enumerate(rows):
        x = x0 + rng.uniform(4, 14)
        shops = (on_ocho and r == 0) or (south_of_ocho and r == 0)
        while x < x1 - 30:
            if shops:
                name = SHOPS[rng.randrange(len(SHOPS))]
                wpx = K.info('Miami', name)['size'][0] * PPM
                if x + wpx > x1: break
                put('Miami', name, x + wpx / 2, ry, 180.0)
                x += wpx + rng.uniform(2, 10)
            else:
                kit, name = HOUSES[rng.randrange(len(HOUSES))]
                wpx = K.info(kit, name)['size'][0] * PPM
                if x + wpx > x1: break
                t = HOUSE_TINTS[rng.randrange(len(HOUSE_TINTS))]
                roof = ROOFS[rng.randrange(len(ROOFS))]
                put(kit, name, x + wpx / 2, ry - 10, 180.0, tints=[t, None, roof])
                if rng.random() < 0.8: tree(x + wpx + 6, ry - rng.uniform(0, 34))
                x += wpx + rng.uniform(10, 22)
    for _ in range(4):
        tree(rng.uniform(x0 + 10, x1 - 10), rng.uniform(y0 + 10, y1 - 10))


TOWERS = ['CondoTowerMIA', 'OfficeTowerMIA', 'CondoTower2MIA']


def tower_block(b, downtown):
    """Brickell's glass towers (two or three a block, on their podiums) and downtown's mix: the towers among Deco blocks with
    their arcades and Mediterranean Revival buildings along the street."""
    x0, y0, x1, y1 = b
    nx = max(1, int((x1 - x0) / 78)); ny = max(1, int((y1 - y0) / 92))
    for j in range(ny):
        for k in range(nx):
            cx = x0 + (x1 - x0) * (k + 0.5) / nx + rng.uniform(-8, 8)
            cy = y0 + (y1 - y0) * (j + 0.5) / ny + 30
            if downtown and (j == ny - 1 or rng.random() < 0.35):
                name = rng.choice(['DecoArcadeMIA', 'DecoArcade2MIA', 'MedRevivalMIA'])
                put('Miami', name, cx, min(cy + 20, y1 - 6), 180.0)
                continue
            name = TOWERS[rng.randrange(len(TOWERS))]
            put('Miami', name, cx, cy, 180.0 + rng.choice([0, 0, 90]), scale=(0.8, 0.8, rng.uniform(0.5, 0.85)))
            if j == ny - 1 and rng.random() < 0.6:
                put('Miami', 'TowerPodiumMIA', cx, y1 - 6, 180.0, scale=(0.9, 0.9, 1.0))
    for _ in range(int((x1 - x0) * (y1 - y0) / 9000)):
        tree(rng.uniform(x0 + 8, x1 - 8), rng.uniform(y0 + 8, y1 - 8),
             [('Plants', 'PalmRoyal', 0.85), ('Plants', 'BroadleafWide', 1.0), ('Plants', 'Banyan', 0.7)])
    for x in range(int(x0) + 10, int(x1) - 6, 26):
        put('Plants', 'PalmRoyal', x, y1 - 2, rng.uniform(0, 360), 0.8)


def guideway(points, scale=1.0):
    """Guideway spans (30 m each, the kit's) along a polyline of picture points, each turned to its piece's bearing."""
    step = 30.0 * scale * PPM
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        lx, ly = (bx - ax), (by - ay) / COS            # the piece on the ground (picture px, its depth unsquashed)
        n = max(1, int(round(math.hypot(lx, ly) / step)))
        # bearing of the piece on the ground (x east, y north): its front faces 90 degrees to its left
        bearing = math.degrees(math.atan2(lx, -ly))
        for k in range(n):
            t = (k + 0.5) / n
            put('Miami', 'GuidewayMIA', ax + (bx - ax) * t, ay + (by - ay) * t, bearing + 90.0,
                scale=(math.hypot(lx, ly) / n / (30.0 * PPM), scale, scale), where='land')


def cars_on(axis, at, span, n, bus=0):
    kinds = ['Hatch', 'Fourby', 'Pickup', 'Van']
    for k in range(n + bus):
        p = rng.uniform(*span)
        lane = rng.choice([-1, 1])
        name, kit = ('BusMIA', 'Miami') if k < bus else (rng.choice(kinds), 'Cars')
        # (the vehicles' noses are their +X: on an east-west road the side faces the viewer)
        if axis == 'x':
            put(kit, name, p, at + lane * 9, 180.0 if lane > 0 else 0.0, where='land')
        else:
            put(kit, name, at + lane * 9, p, 90.0 if lane > 0 else 270.0, where='land')


def build():
    # the blocks
    for b in blocks():
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        kind = district(cx, cy)
        if b[2] - b[0] < 40 or b[3] - b[1] < 40 or kind in ('water', 'park'):
            continue
        if kind == 'river':          # a block the river crosses: by its corner away from the river
            kind = 'havana' if cx < 1680 else ('brickell' if cy > 800 else 'downtown')
        if kind == 'havana':
            havana_block(b)
        else:
            tower_block(b, kind == 'downtown')
    # home and the school
    put('Florida', 'RanchFL', MM.HOME[0] + 46, MM.HOME[1] - 42, 180.0, tints=[(0.70, 0.86, 0.82), (0.80, 0.22, 0.17), (0.88, 0.87, 0.84)])
    sx, sy = MM.SCHOOL
    put('Florida', 'SchoolFL', sx - 10, sy - 26, 180.0)
    put('Florida', 'FlagpoleFL', sx - 80, sy + 6, 180.0)
    for x in range(int(sx - 70), int(sx + 60), 10):
        put('Florida', 'FenceAluFL', x, sy + 20, 180.0, scale=(0.42, 1, 1))
    # Freedom Tower's cousin by the boulevard, the museum, the parks' palms and banyans
    put('Miami', 'SpanishTowerMIA', 2400, 520, 180.0, scale=(1.0, 1.0, 0.7))
    put('Miami', 'MuseumMIA', 2560, 410, 180.0, where='land')
    for b in PARKS[:2]:
        for x in range(int(b[0]) + 16, int(b[2]) - 10, 34):
            for y in (b[1] + 12, b[3] - 8):
                put('Plants', 'PalmRoyal', x, y, rng.uniform(0, 360), 0.9, where='land')
    for p in [(2300, 760), (2360, 830), (2620, 720), (2500, 340)]:
        put('Plants', 'Banyan', p[0], p[1], rng.uniform(0, 360), 1.0, where='land')
    put('Miami', 'CoffeeKioskMIA', 2330, 700, 180.0, where='land')
    # Little Havana's domino park, the port's terminal and its palms
    put('Miami', 'DominoParkMIA', 1060, 1110, 180.0, where='land')
    for p in [(1015, 1070), (1105, 1075)]:
        put('Plants', 'Banyan', p[0], p[1], rng.uniform(0, 360), 0.8, where='land')
    put('Miami', 'TowerPodiumMIA', 2880, 500, 180.0, where='water')
    for x in range(PORT[0] + 20, PORT[2] - 10, 36):
        put('Plants', 'PalmRoyal', x, PORT[1] + 18, rng.uniform(0, 360), 0.8, where='water')
    # the Underline's park and the guideways (the Metrorail over the Underline and up Brickell, the Metromover's loop)
    for x in range(720, 1750, 40):
        if rng.random() < 0.6:
            tree(x, 1290 + rng.uniform(-6, 8), [('Plants', 'PalmRoyal', 0.85), ('Plants', 'BushWide', 1.4), ('Plants', 'ShrubFlowering', 1.4)])
    guideway([(700, 1250), (1750, 1250), (1950, 1000), (1950, 420)])
    guideway([(1750, 1250), (2600, 960), (2600, 420)], 0.7)
    # the river: Uncle Rey's dock and boats along the Riverwalk, a tug and a freighter by the mouth
    for x in range(1060, 1700, 130):
        put('Miami', 'FishingBoatMIA', x + 15, 600, 90.0 + rng.uniform(-5, 5), where='water')
    put('Miami', 'TugMIA', 2150, 885, 180.0, where='water')
    put('Miami', 'FreighterMIA', 2820, 980, 200.0, scale=0.9, where='water')
    put('Miami', 'TugMIA', 2760, 1060, 160.0, where='water')
    # the port: a cruise ship along the island, containers
    put('Miami', 'CruiseShipMIA', 2885, 640, 180.0, scale=0.75, where='water')
    for k in range(3):
        put('Miami', 'FishingBoatMIA', 2760 + k * 70, 1320 + k * 40, rng.uniform(0, 360), 0.9, where='water')
    # Miami Beach: Deco hotels and motels along the strip under palms
    deco = [('Florida', n) for n in ('DecoSurfFL', 'DecoCafeFL', 'DecoBaitFL', 'DecoIceFL', 'DecoShutFL', 'MotelFL')] + [('Miami', 'DecoArcade2MIA')]
    y = 30
    while y < H:
        kit, name = deco[rng.randrange(len(deco))]
        put(kit, name, 3030, y, 180.0, scale=0.9, where='water')
        put('Plants', 'PalmRoyal', 3085, y + 20, rng.uniform(0, 360), 0.85, where='water')
        y += rng.uniform(70, 110)
    # traffic: the 8 bus on Calle Ocho, cars on the main roads
    cars_on('x', 1000, (40, 1900), 14, bus=2)
    cars_on('y', 1950, (440, 1780), 10, bus=1)
    cars_on('y', 2600, (60, 1780), 10)
    cars_on('y', 700, (40, 1780), 8)
    # street palms along Calle Ocho and Biscayne
    for x in range(30, 1900, 60):
        put('Plants', 'PalmRoyal', x, 1000 - 40, rng.uniform(0, 360), 0.8, where='land')
    for y in range(40, H, 50):
        put('Plants', 'PalmRoyal', 2645, y, rng.uniform(0, 360), 0.85, where='land')


def main():
    S = scene()
    out_dir = os.path.dirname(OUT)
    ground_png = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'miami_map_ground.png')
    paint(ground_png)
    ground(S, ground_png)
    lights(S)
    camera(S)
    build()
    print('placed', placed)
    S.eevee.taa_render_samples = SAMPLES
    png = os.path.splitext(OUT)[0] + '_render.png'
    S.render.filepath = png
    S.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    im = Image.open(png).convert('RGB')
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    im.save(OUT, quality=88)
    os.remove(png)
    print('wrote', OUT)


main()
