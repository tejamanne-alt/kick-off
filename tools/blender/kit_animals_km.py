# Kamakura's animals (docs/KAMAKURA_BUILD.md, "The sheets' assets, by id": KM-N01 to N28), from the user's photographic
# sheets KM-P4 and KM-P8. Each animal is a relief shaped from its outline in one view of the sheet, round in section: a
# limb of half-width R is sqrt(d (2R - d)) deep at d from its edge, so a tail is as deep as it is wide, and a body is
# capped softly at its real half-depth; the faces meet at the outline (depth 0 there). The photo
# projected onto both faces, so straight on it is the photo exactly and turned it has a body. Each moving part (a tail,
# wings) is its own mesh with its origin at its pivot, under an empty root named after the model, as the animals kit's
# rig contract has it (kit_animals.py), so the game's behaviours (World/WallCat, Hazards/Seagull, World/SkyFlock) move
# them. This first version builds the proof: the ginger cat sitting (KM-N01) and the black kite flying (KM-N05).
#   blenv/bin/python kit_animals_km.py -- /abs/outdir [--board /abs/board.jpg]
# Writes into outdir: <Model>.fbx per model, KamakuraAnimalsAtlas.png, KamakuraAnimals.json, KamakuraAnimals.blend.
import math
import os
import sys

import bpy
import bmesh
import cv2
import numpy as np
from mathutils import Vector, Euler
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_lib as K
import kit_buildings_km as KB      # its Atlas, the unlit and cut-out review materials, the board's render

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS and not ARGS[0].startswith('--') else os.path.abspath('out_km_animals')
BOARD = ARGS[ARGS.index('--board') + 1] if '--board' in ARGS else None
REFS = KB.REFS

# Each animal: the sheet, the figure's box in it, the view (side: head to the right, the camera's side toward -Y; below:
# head up, seen from beneath), pixels to the metre, the origin (in sheet pixels), the deepest half-depth (m) of each part,
# the parts (name, rule picking its pixels, pivot in sheet pixels), and whether a soft shadow lies under the figure.
ANIMALS = {
    'KmCatSitting': dict(
        sheet='KM-P4_animals_sheet.png', box=(500, 18, 858, 284), view='side', px_per_m=646.0,
        origin=(725, 271), shadow=True, step=13,
        # its sitting height (ear tips to paws) is 246 px: about 0.38 m, a cat 25 cm at the shoulder
        parts=[('Body', lambda x, y: ~((x < 650) & (y > 228)), None, 0.075),
               ('Tail', lambda x, y: (x < 656) & (y > 228), (648, 262), 0.075)]),
    'KmKiteFlying': dict(
        sheet='KM-P4_animals_sheet.png', box=(455, 684, 920, 880), view='below', px_per_m=280.0,
        origin=(687, 760), shadow=False, refine=True, step=14,
        # its wingspan is 449 px: 1.6 m; head to tail 183 px, 0.65 m
        parts=[('Body', lambda x, y: (np.abs(x - 687) < 26) | (y > 800), None, 0.055),
               ('WingR', lambda x, y: (x < 667) & (y <= 806), (663, 735), 0.010),
               ('WingL', lambda x, y: (x > 707) & (y <= 806), (711, 735), 0.010)]),
}


def figure_mask(sheet, box, shadow, refine=False):
    """The figure in box: what differs from the sheet's grey, its holes filled, the largest piece; with shadow, the soft
    neutral shadow under it left out (darker than the grey, no colour of its own)."""
    a = np.asarray(sheet.convert('RGB')).astype(np.int32)
    x0, y0, x1, y1 = box
    r = a[y0:y1, x0:x1]
    border = np.concatenate([r[:4].reshape(-1, 3), r[-4:].reshape(-1, 3), r[:, :4].reshape(-1, 3), r[:, -4:].reshape(-1, 3)])
    bg = np.median(border, 0)
    m = (np.abs(r - bg).sum(-1) > 42).astype(np.uint8)
    if shadow:
        lum = r.mean(-1)
        chroma = r.max(-1) - r.min(-1)
        m[(chroma < 14) & (lum < bg.mean() - 2) & (lum > bg.mean() - 45)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    big = 1 + int(np.argmax(st[1:, 4]))
    m = (lab == big).astype(np.uint8)
    if refine:
        # parts nearly the sheet's grey (the kite's pale tail fan): GrabCut, sure of the found figure (eroded), unsure
        # inside its convex hull, sure of the background at the box's edge
        gc = np.full(m.shape, cv2.GC_PR_BGD, np.uint8)
        hull = cv2.convexHull(cv2.findNonZero(m))
        cv2.fillConvexPoly(gc, hull, cv2.GC_PR_FGD)
        gc[cv2.erode(m, np.ones((5, 5), np.uint8)) > 0] = cv2.GC_FGD
        gc[:3], gc[-3:], gc[:, :3], gc[:, -3:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
        cv2.grabCut(np.ascontiguousarray(r.astype(np.uint8)[:, :, ::-1]), gc, None, np.zeros((1, 65)), np.zeros((1, 65)),
                    6, cv2.GC_INIT_WITH_MASK)
        m = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    inv = (1 - m).astype(np.uint8)
    hn, hl, hs, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, hn):
        x, y, w, h, area = hs[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            m[hl == i] = 1
    return m


def relief(mask, step):
    """A triangulation of the mask: points along its outline every 5 px and inside it every step px, Delaunay, the
    triangles inside the mask kept. Returns the points (px, in the mask's frame), the triangles, each point's distance
    from the outline, and the local half-width there (the largest distance from the outline nearby: the radius of the
    limb the point is on)."""
    h, w = mask.shape
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = []
    for c in cs:
        c = c[:, 0, :].astype(np.float32)
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        for s in np.arange(0, L[-1], 5.0):
            i = min(np.searchsorted(L, s), len(c) - 1)
            pts.append((float(c[i][0]), float(c[i][1])))
    for y in np.arange(step / 2, h, step):
        for x in np.arange(step / 2 + (step / 2 if int(y / step) % 2 else 0), w, step):
            if dist[int(y), int(x)] > step * 0.45:
                pts.append((float(x), float(y)))
    sub = cv2.Subdiv2D((0, 0, w + 1, h + 1))
    uniq = {}
    for p in pts:
        key = (round(p[0], 1), round(p[1], 1))
        if key not in uniq:
            uniq[key] = len(uniq)
            sub.insert(key)
    keys = list(uniq)
    tris = []
    for t in sub.getTriangleList():
        a, b, c = (round(t[0], 1), round(t[1], 1)), (round(t[2], 1), round(t[3], 1)), (round(t[4], 1), round(t[5], 1))
        if a not in uniq or b not in uniq or c not in uniq:
            continue
        cx, cy = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
        if 0 <= int(cy) < h and 0 <= int(cx) < w and mask[int(cy), int(cx)]:
            tris.append((uniq[a], uniq[b], uniq[c]))
    d = np.array([dist[min(int(round(k[1])), h - 1), min(int(round(k[0])), w - 1)] for k in keys], np.float32)
    # the local half-width: the distance field's largest value within a few half-widths, so a tail's points see the
    # tail's own radius, not the body's
    local = dist.copy()
    for k in (9, 17, 33):
        grown = cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        local = np.where(dist > k / 4.0, grown, local)
    local = np.maximum(cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))), local)
    r = np.array([local[min(int(round(k[1])), h - 1), min(int(round(k[0])), w - 1)] for k in keys], np.float32)
    return np.array(keys, np.float32), tris, d, r


def build(name, spec, atlas, sheet):
    x0, y0, x1, y1 = spec['box']
    mask = figure_mask(sheet, spec['box'], spec['shadow'], spec.get('refine', False))
    rgb = np.ascontiguousarray(np.asarray(sheet.convert('RGB'))[y0:y1, x0:x1])
    # the figure's own colours carried outward past its outline (the sheet's grey there would show as a seam where the
    # two faces meet, and as a halo at the edge)
    inner = cv2.erode(mask, np.ones((3, 3), np.uint8))
    rgb = cv2.inpaint(rgb, (1 - inner).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    alpha = cv2.dilate(mask, np.ones((3, 3), np.uint8)) * 255
    pos = atlas.place(Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), 'RGBA'))
    s, (ox, oy) = spec['px_per_m'], spec['origin']
    side = spec['view'] == 'side'
    yy, xx = np.mgrid[y0:y1, x0:x1]
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    tris_total = 0
    for part, rule, pivot, depth in spec['parts']:
        pm = (mask & rule(xx, yy).astype(np.uint8)).astype(np.uint8)
        pts, tris, dist, radius = relief(pm, spec['step'])
        # a round cross-section: a limb of radius R seen side-on is sqrt(d (2R - d)) deep at d from its edge, so a tail
        # is as deep as it is wide; a body wider than it is deep is capped, softly, at its half-depth (depth, metres)
        # the outline's own pixels are 1 from the edge in the distance field: they get depth 0, so the two faces meet
        d, R = np.maximum(dist - 1.0, 0.0) / s, np.maximum(radius - 1.0, np.maximum(dist - 1.0, 0.5)) / s
        round_z = np.sqrt(np.maximum(d * (2 * R - d), 0.0))
        dz = depth * np.tanh(round_z / depth)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        px, py = pivot if pivot else (ox, oy)

        def place(p, z, sign):
            gx, gy = p[0] + x0, p[1] + y0
            if side:      # head to +X, up +Z, the camera's side toward -Y
                return Vector(((gx - px) / s, sign * z, (py - gy) / s))
            return Vector(((py - gy) / s, (gx - px) / s, sign * z))      # seen from below: head +X, beneath -Z

        for sign in (-1, 1):
            vs = [bm.verts.new(place(p, dz[i], sign)) for i, p in enumerate(pts)]
            for a, b, c in tris:
                try:
                    f = bm.faces.new((vs[a], vs[b], vs[c]) if sign < 0 else (vs[a], vs[c], vs[b]))
                except ValueError:
                    continue
                for loop, k in zip(f.loops, ((a, b, c) if sign < 0 else (a, c, b))):
                    loop[uvl].uv = atlas.uv(pos, pts[k][0], pts[k][1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # a check: edges outside the closed shell (flat slivers where a triangle's three corners all lie on the outline;
        # they close nothing that shows, but a gap between the faces would add hundreds here)
        open_edges = sum(1 for e in bm.edges if not e.is_manifold)
        print('  %s.%s: %d edges outside the closed shell' % (name, part, open_edges))
        me = bpy.data.meshes.new(name + '.' + part)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name + '.' + part, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent = root
        o.location = (((px - ox) / s, 0, (oy - py) / s) if side else ((oy - py) / s, (px - ox) / s, 0)) if pivot else (0, 0, 0)
        KB.keep_uv_white(o)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        tris_total += len(me.polygons)
    front = bpy.data.objects.new(name + '.Attach.Front', None)
    bpy.context.scene.collection.objects.link(front)
    front.parent = root
    front.location = (0, -1, 0)
    size = [round((x1 - x0) / s, 2), None, round((y1 - y0) / s, 2)]
    return root, tris_total, size


def export(root, path):
    """One FBX per model with the game's part names (Body, Tail, WingL...): the Blender names carry the model's name
    first only so that two models' parts can live in one file."""
    kids = [root] + list(root.children_recursive)
    old = {o: o.name for o in kids}
    for o in kids[1:]:
        o.name = o.name.split('.', 1)[1]
    K.export_model(root, path)
    for o, n in old.items():
        o.name = n


def board(roots, atlas_path, out, sheet):
    mat = KB.unlit(atlas_path, cut=True)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)
    tmp = os.path.dirname(out)
    cat, kite = roots['KmCatSitting'], roots['KmKiteFlying']
    names = lambda r: {o.name for o in r.children_recursive if o.type == 'MESH'}
    sc = bpy.context.scene

    def shot(path, loc, tgt, ortho=None, fov=40, size=(700, 520), only=None):
        return KB.render(os.path.join(tmp, path), loc, tgt, ortho=ortho, fov=fov, size=size, only=only)

    rows = []
    # the cat: the sheet, straight on, turned, and turned with the tail swished as WallCat swishes it
    spec = ANIMALS['KmCatSitting']
    x0, y0, x1, y1 = spec['box']
    a = sheet.crop(spec['box']).resize((700, round(700 * (y1 - y0) / (x1 - x0))))
    w, hgt = (x1 - x0) / spec['px_per_m'], (y1 - y0) / spec['px_per_m']
    cx = ((x0 + x1) / 2 - spec['origin'][0]) / spec['px_per_m']
    cz = (spec['origin'][1] - (y0 + y1) / 2) / spec['px_per_m']
    b = shot('cat_front.png', (cx, -6, cz), (cx, 0, cz), ortho=w, size=a.size, only=names(cat))
    c = shot('cat_34.png', (cx - 0.75, -0.95, 0.45), (cx - 0.05, 0, 0.17), fov=40, size=(700, 520), only=names(cat))
    top = shot('cat_top.png', (cx, -0.001, 2.0), (cx, 0, 0), ortho=w * 1.05, size=(700, 300), only=names(cat))
    tail = bpy.data.objects['KmCatSitting.Tail']
    tail.rotation_euler = Euler((0, 0, math.radians(35)))
    d = shot('cat_swish.png', (cx + 0.75, -0.95, 0.42), (cx - 0.05, 0, 0.16), fov=40, size=(700, 520), only=names(cat))
    tail.rotation_euler = Euler((0, 0, 0))
    rows.append([a, b, c, d])
    from PIL import ImageDraw as _D
    lab = Image.new('RGB', (700, 300), (40, 40, 46))
    _D.Draw(lab).multiline_text((10, 10), 'The cat from above:\none tail, round,\nas deep as it is wide', fill=(235, 235, 240),
                                font=__import__('PIL.ImageFont', fromlist=['x']).truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28),
                                spacing=8)
    rows.append([lab, top, Image.new('RGB', (10, 10), (40, 40, 46)), Image.new('RGB', (10, 10), (40, 40, 46))])
    # the kite: the sheet, from beneath, from the side and below as the game sees one overhead, and with its wings up
    spec = ANIMALS['KmKiteFlying']
    x0, y0, x1, y1 = spec['box']
    a = sheet.crop(spec['box']).resize((700, round(700 * (y1 - y0) / (x1 - x0))))
    w = (x1 - x0) / spec['px_per_m']
    cxk = (spec['origin'][1] - (y0 + y1) / 2) / spec['px_per_m']
    cy = ((x0 + x1) / 2 - spec['origin'][0]) / spec['px_per_m']
    # straight up from beneath: aimed a hair toward the tail, so the camera's up is the head's way, as on the sheet
    b = shot('kite_below.png', (cxk, cy, -6), (cxk - 0.02, cy, 0), ortho=w, size=a.size, only=names(kite))
    c = shot('kite_side.png', (0.6, -3.2, -1.4), (0, 0, 0), fov=32, size=(700, 520), only=names(kite))
    for part, sign in (('WingL', 1), ('WingR', -1)):        # both wings up: WingL is on +Y, WingR on -Y
        bpy.data.objects['KmKiteFlying.' + part].rotation_euler = Euler((math.radians(28 * sign), 0, 0))
    d = shot('kite_flap.png', (0.6, -3.2, -1.4), (0, 0, 0), fov=32, size=(700, 520), only=names(kite))
    for part in ('WingL', 'WingR'):
        bpy.data.objects['KmKiteFlying.' + part].rotation_euler = Euler((0, 0, 0))
    rows.append([a, b, c, d])
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    pad, head = 20, 60
    widths = [max(r[i].width for r in rows) for i in range(4)]
    W = sum(widths) + pad * 5
    H = head + sum(max(im.height for im in r) for r in rows) + pad * (len(rows) + 1)
    sheet_im = Image.new('RGB', (W, H), (40, 40, 46))
    dr = ImageDraw.Draw(sheet_im)
    x = pad
    for i, t in enumerate(['Your sheet', 'The model, straight on', 'Turned', 'Moving (tail, wings)']):
        dr.text((x, 16), t, font=font, fill=(235, 235, 240))
        x += widths[i] + pad
    y = head + pad
    for r in rows:
        x = pad
        for i, im in enumerate(r):
            sheet_im.paste(im, (x, y))
            x += widths[i] + pad
        y += max(im.height for im in r) + pad
    sheet_im.save(out, quality=90)
    print('board', out, sheet_im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = KB.Atlas(2048)
    sheets = {}
    roots, info = {}, {}
    for name, spec in ANIMALS.items():
        sheet = sheets.setdefault(spec['sheet'], Image.open(os.path.join(REFS, spec['sheet'])).convert('RGB'))
        root, tris, size = build(name, spec, atlas, sheet)
        roots[name] = root
        info[name] = dict(tris=tris, parts=[p[0] for p in spec['parts']], view=spec['view'], sheet=spec['sheet'])
        print('%-14s %5d triangles  parts %s' % (name, tris, ', '.join(p[0] for p in spec['parts'])))
    atlas_path = os.path.join(OUT, 'KamakuraAnimalsAtlas.png')
    atlas.img.save(atlas_path)
    mat = K.material('KamakuraAnimals', atlas_path)
    for name, root in roots.items():
        for o in root.children_recursive:
            if o.type == 'MESH':
                o.data.materials.clear()
                o.data.materials.append(mat)
        export(root, os.path.join(OUT, name + '.fbx'))
    import json
    json.dump({'kit': 'KamakuraAnimals', 'atlas': 'KamakuraAnimalsAtlas.png', 'models': info},
              open(os.path.join(OUT, 'KamakuraAnimals.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'KamakuraAnimals.blend'))
    if BOARD:
        board(roots, atlas_path, BOARD, sheets['KM-P4_animals_sheet.png'])


if __name__ == '__main__':
    main()
