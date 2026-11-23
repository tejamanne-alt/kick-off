"""What of a kit model the ball can meet: every surface of the model, placed as a level places it, that crosses the ball's
plane (z within +-SLAB of 0), rasterized onto a 4 cm grid in the street's x (along) and y (up). Run in Blender's Python:

    tools/blender/blenv/bin/python tools/ball_solidity/silhouette.py -- <requests.json> <out.json>

requests: [{"key": ..., "kit": ..., "model": ..., "yaw": deg, "z": placed depth, "scale": s}, ...]
out: {key: {"cells": [[ix, iy], ...], "cell": 0.04, "bounds": [x0, y0, x1, y1]}} in the model's local x and y (metres from
its origin, at its placed depth and turn). Game axes as the kits' manifests: x along, y up, z away from the camera (Blender's
y). Pure geometry: it says where the model is, not where its colliders are (audit.py compares the two)."""
import bpy, json, math, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
REQ, OUT = argv[0], argv[1]
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SLAB = 0.17      # the ball's radius (0.115) and a margin
CELL = 0.04


def load(kit, model):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    path = os.path.join(REPO, 'Assets/_Game/Art/Models', kit, model + '.fbx')
    bpy.ops.import_scene.fbx(filepath=path)
    tris = []
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH': continue
        me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        me.calc_loop_triangles()
        mw = ob.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            tris.append([tuple(vs[i]) for i in t.vertices])
    return tris


def silhouette(tris, yaw, z0, scale):
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    cells = set()
    for tri in tris:
        pts = []
        for (bx, by, bz) in tri:
            x, y, z = bx * scale, bz * scale, by * scale          # Blender (x, y depth, z up) to game (x, y up, z depth)
            pts.append((x * c + z * s, y, z0 - x * s + z * c))   # turned as Unity turns a model by yaw, then placed
        zs = [p[2] for p in pts]
        if min(zs) > SLAB or max(zs) < -SLAB: continue
        # sample the triangle densely; keep the samples inside the slab
        (ax, ay, az), (bx2, by2, bz2), (cx, cy, cz) = pts
        edge = max(math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2]), math.dist(pts[2], pts[0]))
        n = max(1, int(edge / (CELL * 0.4)))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                w = 1 - u - v
                x = ax * w + bx2 * u + cx * v
                y = ay * w + by2 * u + cy * v
                z = az * w + bz2 * u + cz * v
                if abs(z) <= SLAB:
                    cells.add((int(math.floor(x / CELL)), int(math.floor(y / CELL))))
    return cells


out = {}
cache = {}
for r in json.load(open(REQ)):
    k = (r['kit'], r['model'])
    if k not in cache:
        try:
            cache[k] = load(*k)
        except Exception as e:
            print('skip', k, e); cache[k] = None
    if cache[k] is None: continue
    cells = silhouette(cache[k], r.get('yaw', 0.0), r.get('z', 0.0), r.get('scale', 1.0))
    if cells:
        xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
        bounds = [min(xs) * CELL, min(ys) * CELL, (max(xs) + 1) * CELL, (max(ys) + 1) * CELL]
    else:
        bounds = None
    out[r['key']] = {'cells': sorted(cells), 'cell': CELL, 'bounds': bounds}
    print(r['key'], len(cells), bounds)
json.dump(out, open(OUT, 'w'))
