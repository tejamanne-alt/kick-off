"""Floating parts in the kits' models: every loose piece of a model (a column, a canopy, a sign, a lamp) must stand on the
ground or touch a piece that does, through any chain of pieces. A piece that touches nothing is reported, with its size and
height: a column that starts at a plinth's height in front of the plinth (the museum's, v139), a lamp head left off its pole.

    tools/blender/blenv/bin/python tools/model_support/support.py -- <kit> [<kit> ...]  [--min 0.25] [--json out.json]

Pure geometry on the kits' FBX files (Assets/_Game/Art/Models/<kit>/*.fbx): pieces are the meshes' connected parts; two
pieces touch when their bounding boxes meet within TOUCH. Animals, plants and clouds are not checked (they fly, hang or
sway by design). It reports; deciding what is meant to hang (a sign on a wall the level puts behind it) is a reading."""
import bpy, bmesh, json, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
MIN = 0.25
OUT = None
if '--min' in argv:
    MIN = float(argv[argv.index('--min') + 1]); del argv[argv.index('--min'):argv.index('--min') + 2]
if '--json' in argv:
    OUT = argv[argv.index('--json') + 1]; del argv[argv.index('--json'):argv.index('--json') + 2]
KITS = argv
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TOUCH = float(os.environ.get("TOUCH", "0.1"))
GROUND = 0.06


def pieces(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    boxes = []
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH': continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        bm.verts.ensure_lookup_table()
        seen = set()
        for v in bm.verts:
            if v.index in seen: continue
            stack, part = [v], []
            seen.add(v.index)
            while stack:
                a = stack.pop(); part.append(a.co.copy())
                for e in a.link_edges:
                    b = e.other_vert(a)
                    if b.index not in seen:
                        seen.add(b.index); stack.append(b)
            xs = [p.x for p in part]; ys = [p.y for p in part]; zs = [p.z for p in part]
            boxes.append((min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)))
        bm.free()
    return boxes


def touching(a, b):
    return all(a[i] <= b[i + 3] + TOUCH and b[i] <= a[i + 3] + TOUCH for i in range(3))


def floating(boxes):
    # (on the ground: reaching the model's origin, z 0, where the game stands it; a footing may go below it)
    supported = [b[2] <= GROUND for b in boxes]
    changed = True
    while changed:
        changed = False
        for i, b in enumerate(boxes):
            if supported[i]: continue
            if any(supported[j] and touching(b, boxes[j]) for j in range(len(boxes)) if j != i):
                supported[i] = True; changed = True
    out = []
    for i, b in enumerate(boxes):
        if supported[i]: continue
        gap = min((max(max(boxes[j][k] - b[k + 3], b[k] - boxes[j][k + 3], 0.0) for k in range(3)) for j in range(len(boxes)) if supported[j]), default=99.0)
        below = any(supported[j] and boxes[j][5] <= b[2] + TOUCH and all(boxes[j][k] <= b[k + 3] and b[k] <= boxes[j][k + 3] for k in (0, 1))
                    for j in range(len(boxes)))
        out.append(tuple(b) + (round(gap, 2), below))
    return out


report = {}
for kit in KITS:
    d = os.path.join(REPO, 'Assets/_Game/Art/Models', kit)
    for f in sorted(os.listdir(d)):
        if not f.endswith('.fbx'): continue
        model = f[:-4]
        try:
            boxes = pieces(os.path.join(d, f))
        except Exception as e:
            print('skip', kit, model, e); continue
        if not boxes: continue
        bad = [b for b in floating(boxes) if max(b[3] - b[0], b[4] - b[1], b[5] - b[2]) >= MIN]
        bad.sort(key=lambda b: -b[6])
        if bad:
            report[kit + '/' + model] = [[round(v, 2) for v in b] for b in bad]
            b = bad[0]
            print('%s/%s: %d floating piece(s); the farthest: x %.2f..%.2f, y %.2f..%.2f, z(up) %.2f..%.2f, %.2f m from the nearest support%s'
                  % (kit, model, len(bad), b[0], b[3], b[1], b[4], b[2], b[5], b[6], '' if b[7] else ', nothing under it'))
print('models with floating pieces:', len(report))
if OUT: json.dump(report, open(OUT, 'w'), indent=1)
