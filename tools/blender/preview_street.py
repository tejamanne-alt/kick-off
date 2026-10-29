# A preview of a stretch of street in the game, built from the asset kits the way the game's
# StreetBuilder places them, seen through the game camera (30 degree vertical field of view, about
# 18 m back and 4 m up, tilted 5 degrees down) in the chapter's light and haze (ChapterTheme moods).
# Kit models get the street's paint schemes (ModelTint's brightness-ratio recolour). The shading is
# Blender's, not the game's toon ramp, so judge layout, scale, silhouettes and colour, not shading.
#   blenv/bin/python preview_street.py -- <kits dir> <out.png> [--chapter 1..5] [--seed N] [--wide] [--haze-end M]
# <kits dir> holds one folder per kit with <Kit>.blend and <Kit>.json inside (any folder names).
# Missing kits or models are left out, as the game falls back to its procedural look.
import bpy, bmesh, math, sys, os, glob, json, random
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
kits_dir, out = args[0], args[1]
chapter = int(args[args.index('--chapter') + 1]) if '--chapter' in args else 1
seed = int(args[args.index('--seed') + 1]) if '--seed' in args else 7
wide = '--wide' in args
rng = random.Random(seed * 31 + chapter)

# ---------------------------------------------------------------- the chapter's light (sRGB)
MOODS = {
    1: dict(sun=(1, .93, .8), zenith=(.42, .62, .9), horizon=(.98, .86, .75), glow=(1, .82, .6), shade=(.72, .75, .93),
            haze=(.96, .86, .8), sun_dir=(.45, .75, -.45), haze_start=26, haze_end=260, haze_k=.82),
    2: dict(sun=(1, .96, .87), zenith=(.38, .6, .92), horizon=(.95, .88, .8), glow=(1, .9, .74), shade=(.74, .78, .94),
            haze=(.93, .88, .84), sun_dir=(.4, .85, -.35), haze_start=30, haze_end=280, haze_k=.75),
    3: dict(sun=(1, .91, .8), zenith=(.5, .62, .9), horizon=(1, .83, .79), glow=(1, .78, .64), shade=(.77, .73, .93),
            haze=(.98, .85, .83), sun_dir=(.5, .7, -.45), haze_start=24, haze_end=240, haze_k=.86),
    4: dict(sun=(1, .89, .74), zenith=(.55, .62, .86), horizon=(.98, .81, .69), glow=(1, .75, .54), shade=(.75, .71, .88),
            haze=(.96, .81, .71), sun_dir=(.5, .72, -.4), haze_start=22, haze_end=220, haze_k=.9),
    5: dict(sun=(1, .88, .68), zenith=(.46, .58, .88), horizon=(1, .81, .63), glow=(1, .73, .46), shade=(.71, .69, .9),
            haze=(.98, .83, .67), sun_dir=(.55, .6, -.45), haze_start=24, haze_end=240, haze_k=.86),
}
mood = dict(MOODS[chapter])
if '--haze-end' in args:          # try a different haze range
    mood['haze_end'] = float(args[args.index('--haze-end') + 1])


def lin(c):
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c[:3])


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.render.engine = 'BLENDER_EEVEE'
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
S.render.resolution_x, S.render.resolution_y = (1950, 900) if wide else (1560, 720)
try:
    S.eevee.use_shadows = True
except AttributeError:
    pass

world = bpy.data.worlds.new('sky'); S.world = world; world.use_nodes = True
wn = world.node_tree; bg = wn.nodes['Background']
tc = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ')
ramp = wn.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = lin(mood['horizon']) + (1,)
ramp.color_ramp.elements[1].position = 0.35; ramp.color_ramp.elements[1].color = lin(mood['zenith']) + (1,)
wn.links.new(tc.outputs['Generated'], sep.inputs[0]); wn.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
wn.links.new(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.9

# Game axes (x right, y up, z away from the camera) to Blender's (x right, y away, z up).
def B(x, y, z):
    return Vector((x, z, y))


sd = mood['sun_dir']
sun_vec = Vector((sd[0], sd[2], sd[1])).normalized()       # toward the sun
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.color = lin(mood['sun']); sun.data.energy = 3.4; sun.data.angle = math.radians(3)
sun.rotation_euler = (-sun_vec).to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- kits
kits = {}      # kit -> {'models': manifest models, 'objects': {name: root}}
for blend in sorted(glob.glob(os.path.join(kits_dir, '*', '*.blend'))):
    kit = os.path.splitext(os.path.basename(blend))[0]
    manifest_path = os.path.join(os.path.dirname(blend), kit + '.json')
    if not os.path.exists(manifest_path) or kit in kits:
        continue
    manifest = json.load(open(manifest_path))
    names = set(manifest.get('models', {}).keys())
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    roots = {}
    for o in dst.objects:
        if o is None:
            continue
        if o.parent is None and o.name in names:
            roots[o.name] = o
    kits[kit] = {'models': manifest['models'], 'objects': roots}
    print('kit', kit, len(roots), 'models')

model_cols = {}


def has(kit, model):
    return kit in kits and model in kits[kit]['objects']


def size(kit, model):
    s = kits[kit]['models'][model].get('size', [1, 1, 1])
    return Vector((s[0], s[1], s[2]))        # x across, y deep, z up (Blender axes)


def srgb(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)


def linear(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.04045, v / 12.92, np.power((v + 0.055) / 1.055, 2.4))


def recolour(mesh, bases, tints):
    """ModelTint: parts 1-3 take the tint, keeping their brightness relative to the part's base (sRGB)."""
    if len(mesh.uv_layers) < 2 or not mesh.color_attributes:
        return
    attr = mesh.color_attributes.active_color or mesh.color_attributes[0]
    n_loops = len(mesh.loops)
    part = np.zeros(n_loops * 2); mesh.uv_layers[1].data.foreach_get('uv', part)
    part = np.rint(part.reshape(-1, 2)[:, 0]).astype(int) - 1
    if attr.domain == 'CORNER':
        cols = np.zeros(n_loops * 4); attr.data.foreach_get('color', cols); cols = cols.reshape(-1, 4)
    else:      # point colours: spread to corners and write back per point (first corner wins)
        pc = np.zeros(len(mesh.vertices) * 4); attr.data.foreach_get('color', pc); pc = pc.reshape(-1, 4)
        vi = np.zeros(n_loops, dtype=int); mesh.loops.foreach_get('vertex_index', vi)
        cols = pc[vi]
    rgb = srgb(cols[:, :3])
    for p in range(3):
        if tints[p] is None:
            continue
        sel = part == p
        if not sel.any():
            continue
        base = np.array(bases[p][:3]); to = np.array(tints[p][:3])
        k = rgb[sel].sum(axis=1) / max(0.01, base.sum())
        rgb[sel] = np.clip(to[None, :] * k[:, None], 0, 1)
    cols[:, :3] = linear(rgb)
    if attr.domain == 'CORNER':
        attr.data.foreach_set('color', cols.ravel())
    else:
        pc[vi] = cols
        attr.data.foreach_set('color', pc.ravel())


def collection_for(kit, model, tints=None):
    key = (kit, model, tuple(tuple(round(c, 3) for c in t) if t else None for t in (tints or (None, None, None))))
    if key in model_cols:
        return model_cols[key]
    root = kits[kit]['objects'][model]
    root.location = (0, 0, 0)          # the kit file may lay its models out side by side
    col = bpy.data.collections.new('%s_%d' % (model, len(model_cols)))
    if tints is None or all(t is None for t in tints):
        for o in [root] + list(root.children_recursive):
            col.objects.link(o)
    else:
        parts = kits[kit]['models'][model].get('parts', {})
        bases = [parts.get(str(p + 1), [1, 1, 1]) for p in range(3)]
        mapping = {}
        for o in [root] + list(root.children_recursive):
            c = o.copy()
            if o.type == 'MESH':
                c.data = o.data.copy()
                recolour(c.data, bases, tints)
            mapping[o] = c
            col.objects.link(c)
        for o, c in mapping.items():
            if o.parent in mapping:
                c.parent = mapping[o.parent]
                c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    model_cols[key] = col
    return col


placed = []


def place(kit, model, x, y, z, yaw=0.0, scale=1.0, tints=None, stretch=None):
    """A kit model at game position (x, y, z), turned yaw degrees as Unity turns it (clockwise from above)."""
    if not has(kit, model):
        return None
    col = collection_for(kit, model, tints)
    e = bpy.data.objects.new(model, None)
    e.instance_type = 'COLLECTION'; e.instance_collection = col
    e.location = B(x, y, z)
    e.rotation_euler = (0, 0, -math.radians(yaw))
    s = Vector((scale, scale, scale)) if stretch is None else Vector(stretch)
    e.scale = s
    S.collection.objects.link(e)
    placed.append(e)
    return e


def attach_points(kit, model, prefix):
    root = kits[kit]['objects'][model]
    pts = []
    for o in root.children_recursive:
        if o.name.startswith(prefix) or o.name.startswith(prefix.replace('.', '_')):
            pts.append((root.matrix_world.inverted() @ o.matrix_world).translation)
    return pts


def row(kit, model, a, b, y, z, tints=None):
    if not has(kit, model):
        return False
    length = size(kit, model).x
    n = max(1, round((b - a) / length)); step = (b - a) / n
    for i in range(n):
        place(kit, model, a + step * (i + 0.5), y, z, 0, 1, tints, stretch=(step / length, 1, 1))
    return True


# ---------------------------------------------------------------- ground
mats = {}


def flat_mat(rgb):
    key = tuple(round(v, 3) for v in rgb)
    if key not in mats:
        m = bpy.data.materials.new('g%d' % len(mats)); m.use_nodes = True
        b = m.node_tree.nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value = lin(rgb) + (1,); b.inputs['Roughness'].default_value = 1.0
        mats[key] = m
    return mats[key]


def box(x0, x1, y0, y1, z0, z1, rgb, name='box'):
    me = bpy.data.meshes.new(name)
    v = [B(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata([tuple(p) for p in v], [], f); me.materials.append(flat_mat(rgb))
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    return o


X0, X1 = -40.0, 40.0
CAM_X = 0.0


def strip(z0, z1, rgb, top=0.0, lift=0.0):
    box(X0 - 600, X1 + 600, top + lift - 0.2, top + lift, z0, z1, rgb, 'strip')


FRONT, PATH, PROP, POLE_Z = -16.0, 1.5, 1.85, 1.55
if chapter == 3:
    strip(FRONT, -PATH, (.9, .8, .62)); strip(-PATH, PATH, (.86, .76, .6)); strip(PATH, 5.6, (.9, .8, .62))
    strip(5.6, 9, (.74, .64, .5), lift=-0.12)
    box(X0 - 1500, X1 + 1500, -0.5, -0.35, 9, 1000, (.36, .66, .74), 'sea')
elif chapter == 5:
    strip(FRONT, -PATH, (.56, .66, .36), lift=.04); strip(-PATH, PATH, (.8, .72, .6)); strip(PATH, 90, (.56, .66, .36), lift=.04)
elif chapter == 2:
    strip(FRONT, -PATH, (.66, .6, .56), lift=-.06); strip(-PATH, 90, (.82, .79, .74))
else:
    pave = (.74, .73, .7) if chapter == 4 else (.78, .76, .72)
    strip(FRONT, -8.3, pave); strip(-8.3, -8.1, (.86, .86, .84)); strip(-8.1, -1.7, (.34, .34, .37), lift=-.14)
    strip(-1.7, -PATH, (.86, .86, .84)); strip(-PATH, PROP + .6, pave); strip(PROP + .6, 90, (.72, .72, .7))
    for z in (-2.0, -7.8):
        box(X0 - 600, X1 + 600, -0.14, -0.13, z - .06, z + .06, (.95, .95, .93), 'line')
    for x in range(int(X0) - 60, int(X1) + 60, 6):
        box(x, x + 3, -0.14, -0.128, -4.96, -4.84, (.95, .95, .93), 'dash')

# ---------------------------------------------------------------- scenery (as StreetBuilder)
HOUSE = [((.96, .92, .82), (.32, .5, .52), (.38, .43, .52)), ((.98, .85, .6), (.95, .95, .92), (.72, .38, .3)),
         ((.95, .76, .64), (.36, .42, .56), (.42, .36, .34)), ((.74, .83, .72), (.96, .94, .88), (.34, .44, .42)),
         ((.73, .82, .9), (.96, .95, .92), (.36, .4, .5)), ((.93, .72, .7), (.97, .95, .9), (.48, .34, .32))]
SHOP = [((.97, .93, .84), (.27, .47, .72), (.6, .6, .62)), ((.95, .82, .62), (.75, .27, .25), (.6, .6, .62)),
        ((.8, .87, .84), (.3, .56, .4), (.6, .6, .62)), ((.94, .78, .7), (.92, .68, .2), (.6, .6, .62))]
WORK = [((.78, .82, .76), (.85, .6, .2), (.5, .53, .57)), ((.72, .79, .86), (.78, .3, .26), (.46, .5, .55)),
        ((.86, .76, .62), (.3, .45, .6), (.52, .5, .5))]
WIDTH = {'HouseGable': 7, 'HouseLong': 10, 'Bungalow': 7, 'ShopFruit': 8, 'ShopShutter': 8, 'Apartment': 12, 'Warehouse': 11, 'School': 32}
AUTUMN = [(.96, .72, .3), (.93, .52, .24), (.82, .36, .25), (.98, .84, .4), (.66, .64, .32)]


def building(model, x, z, schemes):
    if not has('Buildings', model):
        return False
    w = size('Buildings', model).x
    sc = min(1.25, max(0.8, WIDTH.get(model, w) / w))
    p = schemes[abs(int(round(x * 7 + z * 13))) % len(schemes)] if schemes else None
    place('Buildings', model, x, 0, z, 0, sc, list(p) if p else None)
    return True


def plant(model, x, y, z, scale):
    leaves = None
    if chapter == 5 and (model.startswith('Broadleaf') or model == 'Birch' or model.startswith('Bush')):
        leaves = rng.choice(AUTUMN)
    place('Plants', model, x, y, z, rng.uniform(0, 360), scale, [leaves, None, None] if leaves else None)


def poles():
    if chapter in (3, 5) or not has('Street', 'UtilityPole'):
        return
    xs = [x for x in np.arange(X0 - 21, X1 + 21, 21.0)]
    anchors = attach_points('Street', 'UtilityPole', 'Attach.Wire')
    yaw = 90.0
    R = Matrix.Rotation(-math.radians(yaw), 3, 'Z')
    for x in xs:
        place('Street', 'UtilityPole', float(x), 0, POLE_Z, yaw)
    for a in anchors:
        a = R @ a
        pts = []
        for i in range(len(xs) - 1):
            p0 = B(float(xs[i]), 0, POLE_Z) + a; p1 = B(float(xs[i + 1]), 0, POLE_Z) + a
            for k in range(10):
                t = k / 10
                pts.append(p0.lerp(p1, t) - Vector((0, 0, 0.9 * 4 * t * (1 - t))))
        pts.append(B(float(xs[-1]), 0, POLE_Z) + a)
        cu = bpy.data.curves.new('wire', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.018
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p.x, p.y, p.z, 1)
        cu.materials.append(flat_mat((.12, .12, .15)))
        S.collection.objects.link(bpy.data.objects.new('wire', cu))


def distant(fields, grass):
    if not has('Terrain', 'HillsRolling'):
        return
    box(X0 - 1500, X1 + 1500, -0.16, -0.06, 89, 700, fields, 'fields')

    def layer(models, a, b, y, z, zj, scale):
        models = [m for m in models if has('Terrain', m)]
        if not models:
            return
        i = rng.randrange(len(models)); x = a
        while x < b:
            m = models[i % len(models)]; w = size('Terrain', m).x * scale
            place('Terrain', m, x + w / 2, y, z + rng.uniform(-zj, zj), rng.uniform(-8, 8), scale * rng.uniform(.9, 1.1),
                  [grass, None, None] if grass else None)
            x += w * 0.82; i += 1
    layer(['ForestStrip'], X0 - 250, X1 + 250, -0.3, 120, 15, 1.0)
    layer(['HillsRolling'], X0 - 450, X1 + 450, -0.5, 230, 30, 1.0)
    layer(['MountainRange1', 'MountainRange2'], X0 - 700, X1 + 700, -1, 440, 50, 0.9)


def suburb():
    x = X0
    while x < X1:
        lot = rng.uniform(9, 13); cx = x + lot / 2
        gate = rng.uniform(x + 2, x + lot - 4)
        for a, b, pa, pb in ((x + .1, gate, True, True), (gate + 2.2, x + lot - .1, True, False)):
            if b - a >= .4 and row('Street', 'BlockWall2', a, b, 0, PROP + .15):
                if pa: place('Street', 'WallPillar', a, 0, PROP + .15)
                if pb: place('Street', 'WallPillar', b, 0, PROP + .15)
        kind = rng.randrange(3)
        z = PROP + 1.6 + rng.uniform(0, 1.4)
        model = 'HouseGable' if kind == 0 else 'HouseLong' if kind == 1 and lot >= 11 else 'Bungalow'
        building(model, cx, z, HOUSE)
        half = WIDTH[model] / 2
        if rng.random() < .7:
            plant(rng.choice(['Broadleaf', 'BroadleafLarge', 'ConiferTall', 'Broadleaf', 'Birch']), cx + rng.uniform(-half, half), 0, z + 8 + rng.uniform(0, 3), rng.uniform(.9, 1.25))
        gap = (cx - half) - x
        if gap > 1.8 and rng.random() < .6:
            m = rng.choice(['Birch', 'ConiferSmall', 'ConiferMid', 'ShrubFlowering'])
            plant(m, x + gap / 2, 0, PROP + 1.4 + rng.uniform(0, 1.2), rng.uniform(1.3, 1.6) if m == 'ShrubFlowering' else rng.uniform(.7, .95))
        x += lot
    x = X0 - 20
    while x < X1 + 20:
        building(rng.choice(['HouseGable', 'HouseLong']), x, rng.uniform(20, 24), HOUSE)
        x += rng.uniform(10, 14)
    distant((.6, .68, .42), None)


def market():
    x, i = X0, 0
    while x < X1:
        building('ShopFruit' if i % 2 == 0 else 'ShopShutter', x + 4, PROP + .6, SHOP)
        x += 8
        if rng.random() < .35:
            place('Street', 'VendingRed', x + .7, 0, PROP + .2); place('Street', 'VendingBlue', x + 1.75, 0, PROP + .2)
            x += 2.6
        i += 1
    x = X0 - 20
    while x < X1 + 20:
        building('Apartment', x, rng.uniform(22, 28), HOUSE)
        x += rng.uniform(13, 16)


def beach():
    x = X0 + 8
    while x < X1:
        if has('Terrain', 'RockCluster') and rng.random() < .5:
            place('Terrain', 'RockCluster', x + rng.uniform(5, 15), -0.22, rng.uniform(8.6, 11), rng.uniform(-30, 30), rng.uniform(.65, 1.3))
        x += rng.uniform(22, 38)
    x = X0 + rng.uniform(5, 20)
    while x < X1:
        for k in range(rng.randrange(1, 4)):
            plant(rng.choice(['Palm', 'PalmShort']), x + k * rng.uniform(2.2, 3.4), -0.1, rng.uniform(5.6, 7), rng.uniform(.85, 1.15))
        x += rng.uniform(30, 55)
    x = X0
    while x < X1:
        plant('DuneGrass', x, 0, rng.uniform(-6.5, -2.4), rng.uniform(.7, 1.3))
        x += rng.uniform(2.5, 7)
    for i in range(3):
        place('Terrain', 'Headland', X0 + (X1 - X0) * (.15 + i * .4) + rng.uniform(-40, 40), -0.8, 650 + i * 60, rng.uniform(-15, 15), rng.uniform(2.2, 3))


def city():
    x = X0
    while x < X1:
        w = rng.uniform(11, 14); cx = x + w / 2
        if rng.random() < .5:
            row('Street', 'Hoarding3', x + .15, x + w - .15, 0, PROP + .2)
        else:
            px = x + rng.uniform(1.5, 3)
            place('Terrain', rng.choice(['SandPile', 'GravelPile']), px, 0, PROP + 1.6, rng.uniform(0, 360), rng.uniform(.8, 1.2))
            place('Street', 'Pallet', px + rng.uniform(2.2, 3), 0, PROP + 1.1, rng.uniform(-20, 20))
            for k in range(2):
                place('Street', 'TrafficCone', x + w - 1.2 - k * .8, 0, PROP + .5, rng.uniform(0, 360))
        if rng.random() < .5:
            building('Warehouse', cx, PROP + 3, WORK)
        else:
            building('Apartment', cx, PROP + 5, HOUSE)
        x += w
    distant((.68, .68, .56), None)


def park():
    x = X0
    while x < X1:
        w = rng.uniform(6, 10); cx = x + w / 2
        row('Plants', 'HedgeBlock2', x + .6, x + w - .6, .04, PROP + .4)
        plant(rng.choice(['ShrubFlowering', 'BushRound']), cx - w * .25, .04, PROP + 1.5, rng.uniform(1.2, 1.6))
        if rng.random() < .4:
            place('Street', 'Bench', cx + 1.5, .04, PROP - .55)
        x += w
    x = X0
    while x < X1:
        r = rng.random()
        plant('CherryBlossom' if r < .3 else 'Broadleaf' if r < .65 else 'BroadleafLarge' if r < .85 else 'Birch', x, .04, rng.uniform(6.5, 16), rng.uniform(.85, 1.15))
        x += rng.uniform(4, 8)
    x = X0
    while x < X1:
        plant('BushWide' if rng.random() < .6 else 'BushRound', x, .04, rng.uniform(3.5, 6), rng.uniform(1, 1.5))
        x += rng.uniform(4, 9)
    x = X0 - 20
    while x < X1 + 20:
        plant(rng.choice(['BroadleafLarge', 'Broadleaf', 'ConiferTall', 'BroadleafLarge', 'ConiferMid', 'Birch']), x, .04, rng.uniform(22, 40), rng.uniform(.95, 1.35))
        x += rng.uniform(3, 6)
    x = X0
    while x < X1:
        plant(rng.choice(['TallGrass', 'GrassTuft', 'FlowerPatch', 'GrassTuft', 'TallGrass']), x, .08, rng.uniform(-6.5, -2.4), rng.uniform(1.1, 1.8))
        x += rng.uniform(.8, 2.6)
    distant((.74, .66, .4), (.8, .68, .36))


{1: suburb, 2: market, 3: beach, 4: city, 5: park}[chapter]()
poles()

# A kid-sized marker on the footpath for scale (1.55 m), where the player would stand.
box(CAM_X - 1.5 - .2, CAM_X - 1.5 + .2, 0, 1.55, -.15, .15, (.9, .35, .3), 'kid')

# ---------------------------------------------------------------- the game camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(30); cam.data.clip_end = 3000
pitch = math.radians(5); half = 4.8; dist = half / math.tan(math.radians(15))
focus = Vector((CAM_X, 0, 2.5))            # Blender coords: (x, depth, up)
fwd = Vector((0, math.cos(pitch), -math.sin(pitch)))
cam.location = focus - fwd * dist
cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()

# Distance haze like DtsHaze, in every material: toward the haze colour by a smoothstep of the
# distance from the camera between haze_start and haze_end, times the strength. The sky stays clear.
haze = lin(mood['haze']) + (1,)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    t = m.node_tree
    outn = next((n for n in t.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if outn is None or not outn.inputs['Surface'].is_linked:
        continue
    shader = outn.inputs['Surface'].links[0].from_socket
    camd = t.nodes.new('ShaderNodeCameraData')
    mr = t.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = mood['haze_start']; mr.inputs['From Max'].default_value = mood['haze_end']
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = mood['haze_k']
    em = t.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = haze; em.inputs['Strength'].default_value = 1.0
    mix = t.nodes.new('ShaderNodeMixShader')
    t.links.new(camd.outputs['View Distance'], mr.inputs['Value']); t.links.new(mr.outputs['Result'], mix.inputs['Fac'])
    t.links.new(shader, mix.inputs[1]); t.links.new(em.outputs['Emission'], mix.inputs[2])
    t.links.new(mix.outputs['Shader'], outn.inputs['Surface'])

S.render.filepath = out
bpy.ops.render.render(write_still=True)
print('preview', out, len(placed), 'models placed')
