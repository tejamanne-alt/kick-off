# A quick 2D plan of the town map layout: roads at their real widths, the areas, the routes, the nodes and their label
# boxes, over a coordinate grid. No bpy needed: this is how the geography is designed before anything is rendered.
#   python3 town_map_plan.py out.png [--scale 0.5] [--no-grid]
import sys, os, math
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import town_map_graph as G


def draw_plan(L, built, out, scale=0.5, grid=True, ring=True):
    """L: the layout module; built: the dict from town_map_build.build(L)."""
    ox, oy = (400, 225) if ring else (0, 0)
    W, H = (G.IMG_W, G.IMG_H) if ring else (G.CORE['w'], G.CORE['h'])
    img = Image.new('RGB', (int(W * scale), int(H * scale)), (200, 214, 176))
    d = ImageDraw.Draw(img, 'RGBA')

    def P(p):
        return ((p[0] + (ox if ring else 0)) * scale, (p[1] + (oy if ring else 0)) * scale)

    def poly(pts, fill=None, outline=None, width=1):
        d.polygon([P(p) for p in pts], fill=fill, outline=outline)

    areas = getattr(L, 'AREAS', {})
    colours = dict(sea=(120, 190, 220), sand=(236, 218, 160), park=(150, 200, 120), school=(215, 215, 170), site=(190, 165, 130),
                   market=(235, 200, 170), field=(185, 205, 140), wood=(110, 160, 100), railbed=(150, 150, 150), residential=(214, 224, 190))
    for name, a in areas.items():
        col = colours.get(a.get('kind', name), (210, 210, 210))
        poly(a['poly'], fill=col + (255,))
    # roads
    for r in built['graph'].roads:
        cls = L.CLASSES[r.cls]
        w = cls['total'] * scale
        pts = [P(p) for p in r.curve]
        d.line(pts, fill=(175, 175, 170, 255), width=max(1, int(w)), joint='curve')
    for r in built['graph'].roads:
        cls = L.CLASSES[r.cls]
        w = cls['road'] * scale
        pts = [P(p) for p in r.curve]
        d.line(pts, fill=(95, 95, 100, 255), width=max(1, int(w)), joint='curve')
    rail = getattr(L, 'RAIL', None)
    if rail:
        pts = [P(p) for p in rail['pts']]
        d.line(pts, fill=(150, 130, 110, 255), width=int(rail.get('width', 36) * scale), joint='curve')
        d.line(pts, fill=(60, 60, 60, 255), width=max(1, int(4 * scale)), joint='curve')
    for name, p in built['graph'].nodes.items():
        x, y = P(p)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
    # routes
    rc = dict(street=(240, 140, 60), market=(220, 70, 70), beach=(50, 140, 220), underpass=(110, 80, 180), site=(190, 110, 210), park=(60, 160, 80))
    for rid, pts in built['routes'].items():
        col = rc.get(rid, (0, 0, 0))
        d.line([P(p) for p in pts], fill=col + (220,), width=max(2, int(18 * scale)), joint='curve')
    # nodes and labels
    font = ImageFont.load_default()
    for nid, n in built['nodes'].items():
        x, y = P((n['x'], n['y']))
        r = G.NODE_R * scale
        col = (250, 200, 50) if nid.startswith('C') else rc.get(n['route'], (0, 0, 0))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,), outline=(20, 20, 40, 255), width=2)
        d.text((x - 8, y - 5), nid, fill=(255, 255, 255, 255), font=font)
        b = G.label_box((n['x'], n['y']), n['label'])
        d.rectangle([P((b[0], b[1])), P((b[2], b[3]))], outline=(0, 0, 0, 255), fill=(255, 255, 255, 160))
    for pid, p in built['places'].items():
        x, y = P(p)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(0, 0, 0, 255))
        d.text((x + 8, y - 5), pid, fill=(0, 0, 0, 255), font=font)
    for did, p in built['districts'].items():
        x, y = P(p)
        d.text((x - 20, y), did.upper(), fill=(120, 20, 20, 255), font=font)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(120, 20, 20, 255))
    for s in built['streets']:
        x, y = P((s['x'], s['y']))
        d.text((x - 20, y - 4), s['name'], fill=(40, 40, 120, 255), font=font)
    # frame of the core and the inner area, grid
    if ring:
        c = G.CORE
        d.rectangle([c['x'] * scale, c['y'] * scale, (c['x'] + c['w']) * scale, (c['y'] + c['h']) * scale], outline=(255, 0, 255, 255), width=2)
        i = G.INNER
        d.rectangle([P((i[0], i[1])), P((i[2], i[3]))], outline=(255, 0, 255, 160), width=1)
    if grid:
        for gx in range(-400, 2801, 200):
            x, _ = P((gx, 0))
            d.line([(x, 0), (x, img.size[1])], fill=(0, 0, 0, 40), width=1)
            d.text((x + 2, 2), str(gx), fill=(0, 0, 0, 160), font=font)
        for gy in range(-200, 1601, 200):
            _, y = P((0, gy))
            d.line([(0, y), (img.size[0], y)], fill=(0, 0, 0, 40), width=1)
            d.text((2, y + 2), str(gy), fill=(0, 0, 0, 160), font=font)
    img.save(out)
    return img


ROUTE_COLOURS = dict(street=(240, 140, 60), market=(220, 70, 70), beach=(50, 140, 220), underpass=(110, 80, 180), site=(190, 110, 210), park=(60, 160, 80))


def draw_overlay(img, built, font_size=22):
    """Draws what the map screen will: the six routes (18 px with a white casing), the nodes (150 px discs, gold for the
    challenges), the label boxes (300 x 56 px on their side of the node), the places, the district and street anchors, and the
    core and its inner area, over the picture (image pixel coordinates). For checking the picture against the data."""
    ox, oy = G.CORE['x'], G.CORE['y']
    img = img.convert('RGBA')
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    def P(p):
        return (p[0] + ox, p[1] + oy)
    for rid, pts in built['routes'].items():
        q = [P(p) for p in pts]
        d.line(q, fill=(255, 255, 255, 235), width=26, joint='curve')
    for rid, pts in built['routes'].items():
        q = [P(p) for p in pts]
        d.line(q, fill=ROUTE_COLOURS.get(rid, (0, 0, 0)) + (255,), width=18, joint='curve')
    try:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', font_size)
    except Exception:
        font = ImageFont.load_default()
    for nid, n in built['nodes'].items():
        x, y = P((n['x'], n['y']))
        b = G.label_box((n['x'], n['y']), n['label'])
        d.rectangle([P((b[0], b[1])), P((b[2], b[3]))], outline=(20, 20, 40, 255), fill=(255, 255, 255, 150), width=2)
        col = (250, 200, 50) if nid.startswith('C') else ROUTE_COLOURS.get(n['route'], (0, 0, 0))
        d.ellipse([x - G.NODE_R, y - G.NODE_R, x + G.NODE_R, y + G.NODE_R], fill=col + (255,), outline=(20, 20, 40, 255), width=4)
        d.text((x, y), nid, fill=(255, 255, 255, 255), font=font, anchor='mm')
    for pid, p in built['places'].items():
        x, y = P(p)
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(0, 0, 0, 255))
        d.text((x + 16, y - 10), pid, fill=(0, 0, 0, 255), font=font)
    for did, p in built['districts'].items():
        x, y = P(p)
        d.text((x, y), did.upper(), fill=(150, 20, 20, 255), font=font, anchor='mm')
    for s in built['streets']:
        x, y = P((s['x'], s['y']))
        d.text((x, y), s['name'], fill=(30, 30, 120, 255), font=font, anchor='mm')
    c = G.CORE
    d.rectangle([c['x'], c['y'], c['x'] + c['w'], c['y'] + c['h']], outline=(255, 0, 255, 255), width=3)
    i = G.INNER
    d.rectangle([P((i[0], i[1])), P((i[2], i[3]))], outline=(255, 0, 255, 160), width=2)
    return Image.alpha_composite(img, over).convert('RGB')
