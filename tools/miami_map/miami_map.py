"""Florida's map: a top-down picture of Miami (3200 x 1800, its core the central 2400 x 1350) and its layout file, made from
one plan so they agree (the same contract as the town's map: docs/WORLD_MAP.md, Levels/TownMap.cs).

    python3 tools/miami_map/miami_map.py            # writes Assets/_Game/Resources/UI/MiamiMap.jpg and MiamiMapLayout.json

The picture is a stand-in drawn flat (land, the bay, the Miami River, parks, the street grid, the blocks of each district),
until Florida's kit exists and the map can be rendered from it in Blender as the town's is (tools/blender/town_map.py).
It carries no text, route lines, nodes or markers: the game draws those. The layout is marked "placeholder".
The routes follow the trips of docs/CITIES.md: FL1 east along Calle Ocho, the bus to Brickell, over the river's drawbridge to
the bayfront; FL2 north to the river, along the Riverwalk, the drugstore downtown; FL3 south to the Underline, the people
mover round to Biscayne, north to Museum Park; all from the ranch house in Little Havana to Bayside Elementary.
Needs Pillow."""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_IMAGE = os.path.join(REPO, "Assets/_Game/Resources/UI/MiamiMap.jpg")
OUT_LAYOUT = os.path.join(REPO, "Assets/_Game/Resources/MiamiMapLayout.json")
W, H = 3200, 1800
CORE = dict(x=400, y=225, w=2400, h=1350)

HOME, SCHOOL = (700, 1000), (2450, 640)
# The routes, in RouteTable.Florida's order, from home to the school.
ROUTES = {
    "fl1": [HOME, (1950, 1000), (1950, 800), (2350, 800), SCHOOL],
    "fl2": [HOME, (700, 700), (1000, 640), (1700, 640), (2000, 560), (2300, 560), SCHOOL],
    "fl3": [HOME, (700, 1250), (1750, 1250), (2600, 960), (2600, 420), SCHOOL],
}
# Each leg's node, near the start of its leg (after home or the stop it starts at), and the side its name goes.
NODES = [
    ("FL1-1", (930, 1000), "below"), ("FL1-2", (1380, 1000), "below"), ("FL1-3", (1950, 920), "right"), ("FL1-4", (2350, 800), "below"),
    ("FL2-1", (700, 820), "left"), ("FL2-2", (1120, 640), "above"), ("FL2-3", (1340, 640), "above"), ("FL2-4", (1880, 592), "above"),
    ("FL2-5", (2150, 560), "above"),
    ("FL3-1", (930, 1250), "below"), ("FL3-2", (2600, 780), "right"), ("FL3-3", (2600, 420), "right"),
]
# The stops between the legs where the picture shows them (Levels/RouteTable.FloridaStops), on their routes.
STOPS = [
    ("calleOcho", "fl1", (1160, 1000)), ("brickell", "fl1", (1720, 1000)), ("bayfront", "fl1", (2190, 800)),
    ("reysDock", "fl2", (1000, 640)), ("drugstore", "fl2", (1760, 624)),
    ("underline", "fl3", (1750, 1250)), ("museumPark", "fl3", (2600, 570)),
]
DISTRICTS = [("littleHavana", 880, 1120), ("river", 1350, 540), ("brickell", 1800, 1120), ("downtown", 2120, 470),
             ("bay", 2900, 1000), ("museumPark", 2420, 360)]
STREETS = [("Calle Ocho", 1300, 975, 0), ("Brickell Ave", 1985, 1150, -90), ("Biscayne Blvd", 2565, 700, -90)]

SAND = (236, 226, 204)
GRASS = (170, 205, 140)
WATER = (120, 190, 205)
DEEP = (95, 170, 195)
ROAD = (250, 247, 240)
MAIN = (255, 252, 246)


def river_points():
    """The Miami River from the west down to the bay: north of the Riverwalk (FL2), then turning south-east to its mouth."""
    return [(0, 860), (380, 740), (700, 640), (1000, 585), (1700, 585), (1850, 700), (2000, 880), (2400, 890), (2700, 880)]


def draw(rng):
    img = Image.new("RGB", (W, H), SAND)
    d = ImageDraw.Draw(img)
    # The bay to the east, its coast a little uneven, and the barrier islands (Miami Beach) beyond.
    coast = [(2680, 0)]
    for y in range(0, H + 60, 60):
        coast.append((2680 + int(28 * math.sin(y / 170.0)) + rng.randint(-6, 6), y))
    coast += [(W, H), (W, 0)]
    d.polygon(coast, fill=WATER)
    d.polygon([(2980, 0), (3080, 0), (3120, 900), (3060, 1800), (2990, 1800), (3010, 900)], fill=SAND)
    d.ellipse((2780, 1180, 2920, 1260), fill=SAND)
    d.ellipse((2790, 300, 2900, 360), fill=SAND)
    # Parks: Bayfront Park, Museum Park, the Underline's linear park, the domino park in Little Havana.
    for box in [(2250, 680, 2660, 860), (2470, 330, 2670, 490), (700, 1215, 1760, 1285), (1000, 1050, 1120, 1130)]:
        d.rectangle(box, fill=GRASS)
    # The street grid, then the main roads (Calle Ocho, Brickell Avenue, Biscayne Boulevard).
    for x in range(-60, 2660, 120):
        d.line([(x, 0), (x, H)], fill=ROAD, width=10)
    for y in range(-100, H + 120, 120):
        d.line([(0, y), (2660, y)], fill=ROAD, width=10)
    for line in [[(0, 1000), (2000, 1000)], [(1950, H), (1950, 800)], [(2550, 0), (2550, H)], [(700, 0), (700, H)]]:
        d.line(line, fill=MAIN, width=22)
    # The blocks: Little Havana's low pastel houses, Brickell's and downtown's towers (with their shadows to the north-west).
    pastels = [(240, 200, 190), (190, 230, 214), (246, 222, 160), (236, 190, 210), (250, 244, 232)]
    for bx in range(-60, 2620, 120):
        for by in range(-100, H, 120):
            cx, cy = bx + 60, by + 60
            if (2250 <= cx <= 2660 and 680 <= cy <= 860) or (2470 <= cx <= 2670 and 330 <= cy <= 490) or (1215 <= cy <= 1285):
                continue
            if cx > 2640:
                continue
            tower = cx > 1650 and 420 < cy < 1200
            if tower:
                for _ in range(rng.randint(1, 2)):
                    s = rng.randint(34, 56)
                    x0, y0 = cx - 50 + rng.randint(0, 100 - s), cy - 50 + rng.randint(0, 100 - s)
                    d.rectangle((x0 - 14, y0 - 14, x0 + s - 14, y0 + s - 14), fill=(200, 196, 186))
                    d.rectangle((x0, y0, x0 + s, y0 + s), fill=rng.choice([(176, 200, 214), (214, 220, 226), (236, 232, 222)]))
            else:
                for _ in range(rng.randint(3, 6)):
                    s = rng.randint(18, 28)
                    x0, y0 = cx - 48 + rng.randint(0, 96 - s), cy - 48 + rng.randint(0, 96 - s)
                    d.rectangle((x0, y0, x0 + s, y0 + s), fill=rng.choice(pastels))
                if rng.random() < 0.4:
                    tx, ty = cx + rng.randint(-40, 40), cy + rng.randint(-40, 40)
                    d.ellipse((tx - 13, ty - 13, tx + 13, ty + 13), fill=(110, 160, 95))
    # The river over the grid, with its docks; the elevated line over the Underline; the people mover's loop.
    pts = river_points()
    d.line(pts, fill=WATER, width=70, joint="curve")
    d.line(pts, fill=DEEP, width=34, joint="curve")
    for x in range(1050, 1700, 130):
        d.rectangle((x, 615, x + 26, 630), fill=(150, 120, 90))
    d.line([(700, 1250), (1750, 1250), (1950, 1000), (1950, 420)], fill=(150, 150, 156), width=12)
    d.line([(1750, 1250), (2600, 960), (2600, 420)], fill=(165, 165, 172), width=8)
    # Palms along the bayfront.
    for y in range(0, H, 46):
        x = 2640 + rng.randint(-10, 10)
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(96, 150, 84))
    return img.filter(ImageFilter.GaussianBlur(0.8))


def on_route(p, line):
    best = 1e9
    for a, b in zip(line, line[1:]):
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / float(dx * dx + dy * dy)))
        best = min(best, math.hypot(ax + dx * t - p[0], ay + dy * t - p[1]))
    return best


def main():
    rng = random.Random(305)
    draw(rng).save(OUT_IMAGE, quality=88)
    for nid, pos, _ in NODES:
        route = "fl" + nid[2]
        assert on_route(pos, ROUTES[route]) < 1.0, nid
    for sid, route, pos in STOPS:
        assert on_route(pos, ROUTES[route]) < 1.0, sid
    layout = {
        "image": "UI/MiamiMap", "width": W, "height": H, "core": CORE,
        "places": [{"id": "home", "x": HOME[0], "y": HOME[1]}, {"id": "school", "x": SCHOOL[0], "y": SCHOOL[1]}],
        "routes": [{"id": rid, "points": [{"x": x, "y": y} for x, y in pts]} for rid, pts in ROUTES.items()],
        "nodes": [{"id": nid, "x": x, "y": y, "label": side} for nid, (x, y), side in NODES],
        "districts": [{"id": i, "x": x, "y": y} for i, x, y in DISTRICTS],
        "streets": [{"name": n, "x": x, "y": y, "angle": a} for n, x, y, a in STREETS],
        "stops": [{"id": sid, "route": r, "x": x, "y": y} for sid, r, (x, y) in STOPS],
        "placeholder": True,
    }
    with open(OUT_LAYOUT, "w") as f:
        json.dump(layout, f, indent=1)
    print("wrote", OUT_IMAGE, "and", OUT_LAYOUT)


if __name__ == "__main__":
    main()
