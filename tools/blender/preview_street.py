# A preview of a stretch of street in the game, built from the asset kits the way the game's
# StreetBuilder places them, seen through the game camera (34 degree vertical field of view, about
# 12 m back and under 3 m up, tilted 4 degrees down) in the chapter's light and haze (ChapterTheme moods).
# Kit models get the street's paint schemes (ModelTint's brightness-ratio recolour). The shading is
# Blender's, not the game's toon ramp, so judge layout, scale, silhouettes and colour, not shading.
#   blenv/bin/python preview_street.py -- <kits dir> <out.png> [--chapter 1..5] [--seed N] [--wide] [--haze-end M] [--surfaces DIR] [--samples N]
#       [--mood-json FILE] (a city's light: see --mood-json below)
#       [--miami FL1-1 --plan MiamiDistricts.json] (one of Florida's own legs, from the plan the game builds it from)
# <kits dir> holds one folder per kit with <Kit>.blend and <Kit>.json inside (any folder names).
# --surfaces: a folder of the game's ground textures (Surface_<Name>.png, 8 x 8 units each), e.g.
# exported from ProceduralArt.SurfaceTexture; without it the ground is flat colour.
# Missing kits or models are left out, as the game falls back to its procedural look.
import bpy, bmesh, math, sys, os, glob, json, random
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
kits_dir, out = args[0], args[1]
chapter = int(args[args.index('--chapter') + 1]) if '--chapter' in args else 1
seed = int(args[args.index('--seed') + 1]) if '--seed' in args else 7
wide = '--wide' in args
surfaces_dir = args[args.index('--surfaces') + 1] if '--surfaces' in args else None
# --spans x0:x1:top,...  the level's ground spans (beach: dunes and channels as LevelBuildKit.BeachGround draws them)
spans_arg = [tuple(float(v) for v in t.split(':')) for t in args[args.index('--spans') + 1].split(',')] if '--spans' in args else None
cam_x = float(args[args.index('--cam') + 1]) if '--cam' in args else 0.0
# --florida (chapter 3): the Florida add-on's beach town on its seawall terraces (StreetBuilder.Florida); --level L11..L14
# picks where the strip starts; --open a:b,... are stretches left as open beach (the level's tides, channels, dunes, stops).
florida = '--florida' in args
# --kamakura: Kamakura's own look (StreetBuilder.Kamakura: the Kamakura and KamakuraStreet kits, Japan's trees).
kamakura_mode = '--kamakura' in args
fl_level = args[args.index('--level') + 1] if '--level' in args else 'L11'
fl_open = [tuple(float(v) for v in t.split(':')) for t in args[args.index('--open') + 1].split(',')] if '--open' in args else []
# --florida with --chapter 1: Florida's Home Street (StreetBuilder.FloridaHome); --canal a:b a canal under a drawbridge
# (LevelBuildKit.Drawbridge) with --lift degrees of its leaves up; --home x the kid's ranch house with its door at x.
fl_home = florida and chapter == 1
canal = tuple(float(v) for v in args[args.index('--canal') + 1].split(':')) if '--canal' in args else None
lift = float(args[args.index('--lift') + 1]) if '--lift' in args else 0.0
home_x = float(args[args.index('--home') + 1]) if '--home' in args else None
rng = random.Random(seed * 31 + chapter)

# ---------------------------------------------------------------- the chapter's light (sRGB)
MOODS = {
    1: dict(sun=(1, .979, .962), zenith=(.234, .421, .67), horizon=(.306, .537, .733), glow=(1, .97, .92), shade=(.56, .565, .64),
            haze=(.34, .54, .75), sun_dir=(.45, .78, -.45), haze_start=50, haze_end=700, haze_k=.45),
    2: dict(sun=(1, .979, .962), zenith=(.234, .421, .67), horizon=(.306, .537, .733), glow=(1, .97, .92), shade=(.56, .565, .64),
            haze=(.34, .54, .75), sun_dir=(.4, .85, -.35), haze_start=50, haze_end=700, haze_k=.45),
    3: dict(sun=(1, .979, .967), zenith=(.22, .412, .676), horizon=(.295, .537, .745), glow=(1, .97, .92), shade=(.57, .57, .64),
            haze=(.34, .55, .76), sun_dir=(.5, .75, -.45), haze_start=55, haze_end=760, haze_k=.42),
    4: dict(sun=(1, .979, .962), zenith=(.25, .432, .666), horizon=(.33, .552, .73), glow=(1, .97, .92), shade=(.56, .565, .64),
            haze=(.36, .54, .72), sun_dir=(.5, .75, -.4), haze_start=45, haze_end=640, haze_k=.5),
    5: dict(sun=(1, .969, .942), zenith=(.234, .421, .67), horizon=(.306, .537, .733), glow=(1, .96, .9), shade=(.55, .57, .62),
            haze=(.34, .54, .74), sun_dir=(.55, .7, -.45), haze_start=50, haze_end=700, haze_k=.45),
}
mood = dict(MOODS[chapter])
if '--haze-end' in args:          # try a different haze range
    mood['haze_end'] = float(args[args.index('--haze-end') + 1])
# --mood-json FILE: a city's mood (Progression/Cities, CityClimate.Apply over the chapter's), as the climate harness in
# tools/blender/README.md ("A city's light") writes it from the game's own C#: its keys replace the chapter's.
if '--mood-json' in args:
    with open(args[args.index('--mood-json') + 1]) as f:
        city_mood = json.load(f)
    unknown = set(city_mood) - set(mood)
    if unknown:
        raise SystemExit('--mood-json: keys this preview does not know: %s' % sorted(unknown))
    mood.update({k: (tuple(v) if isinstance(v, list) else v) for k, v in city_mood.items()})


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
    # Cut-out leaf cards (the plants kit) cast stochastic shadows that Eevee redraws every sample,
    # so fewer samples keep a preview to a few minutes; --samples raises them for a final image.
    S.eevee.taa_render_samples = int(args[args.index('--samples') + 1]) if '--samples' in args else 16
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
# The camera sees the sky gradient; everything else is lit by the chapter's shade colour (like the
# game's DtsShadeTint), not by the deep blue of the sky, which would tint the whole street blue.
fill = wn.nodes.new('ShaderNodeBackground'); fill.inputs['Color'].default_value = lin(mood['shade']) + (1,)
fill.inputs['Strength'].default_value = 0.75
lp = wn.nodes.new('ShaderNodeLightPath'); mix = wn.nodes.new('ShaderNodeMixShader')
wn.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
wn.links.new(fill.outputs['Background'], mix.inputs[1]); wn.links.new(bg.outputs['Background'], mix.inputs[2])
wn.links.new(mix.outputs['Shader'], wn.nodes['World Output'].inputs['Surface'])

# Game axes (x right, y up, z away from the camera) to Blender's (x right, y away, z up).
def B(x, y, z):
    return Vector((x, z, y))


sd = mood['sun_dir']
sun_vec = Vector((sd[0], sd[2], sd[1])).normalized()       # toward the sun
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.color = lin(mood['sun']); sun.data.energy = 4.0; sun.data.angle = math.radians(3)
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
SURFACE_COLOUR = {'Asphalt': (.5, .5, .52), 'Paving': (.8, .78, .74), 'Kerb': (.86, .86, .84), 'Concrete': (.76, .75, .72),
                  'Cobbles': (.62, .57, .52), 'Sand': (.92, .84, .66), 'Gravel': (.76, .68, .56), 'Grass': (.52, .62, .32), 'Sea': (.3, .6, .7)}


def flat_mat(rgb, surface=None):
    key = (tuple(round(v, 3) for v in rgb), surface)
    if key not in mats:
        m = bpy.data.materials.new('g%d' % len(mats)); m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes.get('Principled BSDF')
        b.inputs['Roughness'].default_value = 1.0
        flat = SURFACE_COLOUR.get(surface, (1, 1, 1))     # stands in for the texture when there is none
        b.inputs['Base Color'].default_value = lin(tuple(a * c for a, c in zip(rgb, flat))) + (1,)
        path = os.path.join(surfaces_dir, 'Surface_%s.png' % surface) if surfaces_dir and surface else None
        if path and os.path.exists(path):
            # The game projects ground textures from above in world space, one tile per 8 units.
            tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
            mp.inputs['Scale'].default_value = (0.125, 0.125, 0.125)
            img = nt.nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(path)
            mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
            mul.inputs['Factor'].default_value = 1.0; mul.inputs['B'].default_value = lin(rgb) + (1,)
            nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], img.inputs['Vector'])
            nt.links.new(img.outputs['Color'], mul.inputs['A']); nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
        mats[key] = m
    return mats[key]


def box(x0, x1, y0, y1, z0, z1, rgb, name='box', surface=None):
    me = bpy.data.meshes.new(name)
    v = [B(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata([tuple(p) for p in v], [], f); me.materials.append(flat_mat(rgb, surface))
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)
    return o


CAM_X = cam_x
X0, X1 = CAM_X - 40.0, CAM_X + 40.0


def strip(z0, z1, rgb, top=0.0, lift=0.0, surface=None):
    # (Florida's canal cuts the lane and everything behind it; the road in front crosses it.)
    if canal and z1 > -1.5 + 1e-3:
        box(X0 - 600, canal[0] - .3, top + lift - 0.2, top + lift, z0, z1, rgb, 'strip', surface)
        box(canal[1] + .3, X1 + 600, top + lift - 0.2, top + lift, z0, z1, rgb, 'strip', surface)
        return
    box(X0 - 600, X1 + 600, top + lift - 0.2, top + lift, z0, z1, rgb, 'strip', surface)


W = (1, 1, 1)
FRONT, PATH, PROP, POLE_Z = -16.0, 1.5, 1.85, 1.55
def patches(name, faces, rgb, surface):
    # A mesh of quads and triangles given in game coordinates (LevelBuildKit's PatchShape).
    verts, polys = [], []
    for f in faces:
        idx = []
        for p in f:
            verts.append(tuple(B(*p))); idx.append(len(verts) - 1)
        polys.append(idx)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], polys); me.materials.append(flat_mat(rgb, surface))
    bm = bmesh.new(); bm.from_mesh(me)
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < -0.01 or (abs(f.normal.z) <= 0.01 and f.normal.y > 0): f.normal_flip()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); S.collection.objects.link(o)


def _i32(v):
    v &= 0xffffffff
    return v - 0x100000000 if v & 0x80000000 else v


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def noise(x, y):
    # SandField.Noise: smooth value noise over an integer hash (C# int arithmetic).
    def hsh(i, j):
        h = _i32(i * 374761393 + j * 668265263)
        h = _i32((h ^ (h >> 13)) * 1274126177)
        return ((h ^ (h >> 16)) & 0xffff) / 65535.0
    i, j = math.floor(x), math.floor(y)
    u, v = ease(x - i), ease(y - j)
    lerp = lambda a, b, t: a + (b - a) * t
    return lerp(lerp(hsh(i, j), hsh(i + 1, j), u), lerp(hsh(i, j + 1), hsh(i + 1, j + 1), u), v)


class Sand:
    # A port of World/SandField (keep in step): the beach as one smooth surface from the ground spans.
    SLOPE_RUN, WET_FROM, SHORE_FROM, CHANNEL_DEPTH = 3.6, 5.6, 8.6, 0.6
    DRY, TRODDEN, WET = (1, 1, 1), (.97, .95, .92), (.8, .74, .7)

    def __init__(self, spans, calm=()):
        self.spans = sorted(spans); self.calm = list(calm)
        self.base = min(t for _, _, t in self.spans)
        self.first_from, self.first_top = self.spans[0][0], self.spans[0][2]
        self.last_to, self.last_top = -1e9, 0
        for a, b, t in self.spans:
            if b > self.last_to: self.last_to, self.last_top = b, t
        self.steps, self.gaps = [], []
        for a in self.spans:
            for b in self.spans:
                if abs(a[1] - b[0]) > .01 or abs(a[2] - b[2]) < .02: continue
                drop = abs(a[2] - b[2])
                if a[2] > b[2]: st = (a[1], a[2], b[2], min(self.SLOPE_RUN * drop, (b[1] - b[0]) * .9))
                else: st = (b[0], b[2], a[2], -min(self.SLOPE_RUN * drop, (a[1] - a[0]) * .9))
                if abs(st[3]) > .05: self.steps.append(st)
        reach, reach_top = self.spans[0][1], self.spans[0][2]
        for a, b, t in self.spans[1:]:
            if a > reach + .01: self.gaps.append((reach, a, reach_top, t))
            if b > reach: reach, reach_top = b, t

    def lane(self, x):
        h = max([t for a, b, t in self.spans if a <= x <= b], default=None)
        if h is None:
            if x < self.first_from: h = self.first_top
            elif x > self.last_to: h = self.last_top
            else:
                h = self.base - self.CHANNEL_DEPTH
                for g in self.gaps:
                    if g[0] < x < g[1]: h = self.channel(g, x)
        for edge, top, bottom, run in self.steps:
            d = (x - edge) / run
            if 0 <= d < 1: h = max(h, bottom + (top - bottom) * ease(1 - d))
        return h

    def channel(self, g, x):
        l, r, hl, hr = g
        bed, bank = self.base - self.CHANNEL_DEPTH, min(.6, (r - l) * .4)
        return max(hl + (bed - hl) * ease((x - l) / bank), hr + (bed - hr) * ease((r - x) / bank))

    @staticmethod
    def dune(x, z, lift):
        front, back = -1.65 - .6 * noise(x * .09, 3.7), 1.8 + 1.8 * noise(x * .06, 9.2)
        if z < front: return ease(1 - (front - z) / (1.4 + 2.2 * lift))
        if z > back: return ease(1 - (z - back) / (1.8 + 2.8 * lift))
        return 1.0

    @staticmethod
    def channel_reach(z):
        return ease((z + 3.6) / 2)

    def hummocks(self, x, z):
        m = ease((abs(z) - 1.7) / 1.8) * (1 - ease((z - 4.4) / 1.2))
        for a, b in self.calm:
            d = a - x if x < a else x - b if x > b else 0
            m *= ease(d / 3)
        if m <= 0: return 0.0
        return m * (.18 * (noise(x * .19, z * .26) - .5) + .07 * (noise(x * .55 + 11, z * .6 + 5) - .5))

    def shore(self, z):
        return -.12 * ease((z - self.WET_FROM) / 1.4) - .44 * ease((z - self.SHORE_FROM) / 2.4)

    def height(self, x, z, lane=None):
        lift = (self.lane(x) if lane is None else lane) - self.base
        h = self.base + lift * (self.dune(x, z, lift) if lift > 0 else self.channel_reach(z))
        return h + self.hummocks(x, z) + self.shore(z)

    def tint(self, x, z, lane=None):
        k = 1 - ease((abs(z) - 1.3) / .5)
        c = [a + (b - a) * k for a, b in zip(self.DRY, self.TRODDEN)]
        wet = ease((z - (self.WET_FROM - .2)) / 1.2)
        lift = (self.lane(x) if lane is None else lane) - self.base
        if lift < 0: wet = max(wet, min(1, -lift / self.CHANNEL_DEPTH) * self.channel_reach(z))
        return [a + (b - a) * wet for a, b in zip(c, self.WET)]


SAND = None
SAND_ROWS = [-16 + k * 1.25 for k in range(8)] + [-6 + k * .4 for k in range(42)] + [11.2]


def beach_ground(sand):
    # LevelBuildKit.BeachGround: the sand as one smooth mesh (SandDunes) with vertex tints, water in any channel.
    xs = [X0 - 60 + i * .5 for i in range(int((X1 - X0 + 120) / .5) + 1)]
    verts, cols, faces = [], [], []
    for x in xs:
        lane = sand.lane(x)
        for z in SAND_ROWS:
            verts.append(tuple(B(x, sand.height(x, z, lane), z))); cols.append(sand.tint(x, z, lane))
    n = len(SAND_ROWS)
    for i in range(len(xs) - 1):
        for j in range(n - 1):
            a = i * n + j
            faces.append((a, a + n, a + n + 1, a + 1))
    me = bpy.data.meshes.new('sand'); me.from_pydata(verts, [], faces)
    for f in me.polygons: f.use_smooth = True
    attr = me.color_attributes.new('tint', 'FLOAT_COLOR', 'POINT')
    for k, c in enumerate(cols): attr.data[k].color = lin(c) + (1,)
    m = flat_mat(W, 'Sand').copy(); nt = m.node_tree
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'tint'
    bsdf = nt.nodes.get('Principled BSDF')
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    src = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    if src is not None: nt.links.new(src, mix.inputs['A'])
    else: mix.inputs['A'].default_value = bsdf.inputs['Base Color'].default_value
    nt.links.new(vc.outputs['Color'], mix.inputs['B']); nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
    me.materials.append(m)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    o = bpy.data.objects.new('sand', me); S.collection.objects.link(o)
    if sand.gaps:
        y = sand.base - .3
        patches('streams', [[(l, y, -3.6), (l, y, 12), (r, y, 12), (r, y, -3.6)] for l, r, _, _ in sand.gaps], W, 'Sea')
    # LevelBuildKit.BeachDressing: dune grass down the dunes' faces.
    r_ = random.Random(seed + 5)
    for a, b, top in sand.spans:
        h = top - sand.base
        if h < .05: continue
        x = a + r_.uniform(.3, 1.2)
        while x < b - .3:
            z = -r_.uniform(2.6 + .6 * h, 3.2 + 2 * h) if r_.random() < .75 else r_.uniform(2.4, 3 + 2 * h)
            place('Plants', 'DuneGrass', x, sand.height(x, z), z, r_.uniform(0, 360), r_.uniform(.7, 1.3))
            x += r_.uniform(.7, 2)


if '--miami' in args:
    pass          # a Florida leg's own ground (miami() below)
elif chapter == 3:
    SAND = Sand(spans_arg or [(X0 - 600, X1 + 600, 0.0)])
    beach_ground(SAND)
    box(X0 - 1500, X1 + 1500, SAND.base - 0.5, SAND.base - 0.3, 9, 1000, W, 'sea', 'Sea')
elif chapter == 5:
    strip(FRONT, -PATH, W, lift=.04, surface='Grass'); strip(-PATH, PATH, W, surface='Gravel')
    strip(PATH, PROP + .6, W, lift=.04, surface='Grass'); strip(PROP + .6, 90, (.92, .95, .9), lift=.04, surface='Grass')
elif chapter == 2:
    strip(FRONT, -PATH, W, lift=-.06, surface='Cobbles'); strip(-PATH, PROP + .6, (1, .97, .92), surface='Paving')
    strip(PROP + .6, 90, (.92, .9, .86), surface='Paving')
else:
    pave = 'Concrete' if chapter == 4 else 'Paving'
    strip(FRONT, -8.3, W, surface=pave); strip(-8.3, -8.1, W, surface='Kerb'); strip(-8.1, -1.7, W, lift=-.14, surface='Asphalt')
    strip(-1.7, -PATH, W, surface='Kerb'); strip(-PATH, PROP + .6, W, surface=pave)
    if chapter == 4: strip(PROP + .6, 90, (.9, .9, .88), surface='Concrete')
    else: strip(PROP + .6, 90, (.96, .97, .92), surface='Grass')
    for z in (-2.0, -7.8):
        box(X0 - 600, X1 + 600, -0.14, -0.13, z - .06, z + .06, (.95, .95, .93), 'line')
    for x in range(int(X0) - 60, int(X1) + 60, 6):
        box(x, x + 3, -0.14, -0.128, -4.96, -4.84, (.95, .95, .93), 'dash')
# ---------------------------------------------------------------- scenery (as StreetBuilder)
HOUSE = [((.95, .95, .93), (.3, .3, .32), (.32, .34, .38)), ((.9, .88, .84), (.97, .97, .95), (.66, .38, .3)),
         ((.82, .84, .86), (.96, .96, .95), (.3, .38, .48)), ((.92, .88, .8), (.42, .32, .26), (.36, .33, .32)),
         ((.88, .91, .92), (.96, .96, .95), (.24, .42, .46)), ((.96, .94, .9), (.55, .3, .25), (.42, .42, .44))]
SHOP = [((.94, .94, .92), (.2, .42, .74), (.56, .57, .6)), ((.88, .86, .82), (.82, .22, .2), (.56, .57, .6)),
        ((.84, .86, .86), (.18, .52, .36), (.56, .57, .6)), ((.93, .91, .86), (.96, .72, .12), (.56, .57, .6))]
WORK = [((.82, .82, .81), (.9, .56, .14), (.5, .53, .57)), ((.8, .81, .82), (.8, .26, .22), (.46, .5, .55)),
        ((.86, .84, .8), (.24, .44, .64), (.52, .52, .54))]
WIDTH = {'HouseGable': 7, 'HouseLong': 10, 'Bungalow': 7, 'ShopFruit': 8, 'ShopShutter': 8, 'Apartment': 12, 'Warehouse': 11, 'School': 32}
SUMMER = [(.243, .327, .207), (.218, .302, .207), (.268, .352, .207), (.201, .293, .217), (.26, .335, .186)]
MEADOW = [(.46, .57, .26), (.5, .6, .28), (.4, .53, .25)]
PALM, HEDGE = (.3, .42, .2), (.21, .33, .17)

# The Coast kit's California houses and shops (StreetBuilder.Coast.cs).
COAST = {'VillaStucco', 'VillaRanch', 'CraftsmanPorch', 'BeachCondo', 'ShopBeach', 'ShopMission', 'PierSpan', 'PierEnd'}
SETBACK = {'CraftsmanPorch': 2.2, 'VillaRanch': 1.0, 'VillaStucco': .4, 'BeachCondo': .6}
TERRA = (.72, .4, .28)
VILLA = [((.87, .81, .7), (.36, .27, .2), TERRA), ((.84, .77, .66), (.3, .38, .42), (.66, .36, .26)), ((.9, .87, .8), (.24, .33, .28), (.74, .44, .31)),
         ((.86, .76, .66), (.4, .28, .22), (.68, .38, .28)), ((.91, .9, .87), (.2, .25, .32), (.7, .4, .29)), ((.8, .76, .68), (.32, .24, .19), (.62, .36, .27))]
CRAFT = [((.92, .92, .9), (.28, .35, .42), (.32, .33, .36)), ((.76, .82, .84), (.56, .2, .18), (.34, .35, .38)), ((.86, .82, .74), (.22, .33, .28), (.38, .34, .31)),
         ((.78, .76, .68), (.28, .28, .3), (.31, .31, .34))]
CONDO = [((.92, .92, .9), (.36, .5, .58), (.56, .55, .54)), ((.88, .86, .81), (.28, .31, .35), (.56, .55, .54)), ((.86, .88, .89), (.22, .42, .5), (.56, .55, .54))]
BSHOP = [((.9, .85, .75), (.2, .5, .56), (.56, .55, .54)), ((.9, .89, .86), (.8, .38, .28), (.56, .55, .54)), ((.87, .8, .66), (.22, .32, .54), (.56, .55, .54)),
         ((.86, .88, .86), (.88, .66, .2), (.56, .55, .54))]
MISSION = [((.88, .82, .72), (.3, .22, .17), TERRA), ((.85, .78, .69), (.22, .28, .24), (.68, .36, .25)), ((.9, .88, .83), (.34, .19, .15), (.74, .42, .29))]


# The Florida kit's houses (StreetBuilder.FloridaHouse) and their paints.
FLH = {'RanchFL', 'RanchSmallFL', 'CottageFL'}
SETBACK.update({'CottageFL': 2.3, 'RanchFL': .7, 'RanchSmallFL': .4})
RANCH = [((.70, .86, .82), (.80, .22, .17), (.88, .87, .84)), ((.94, .76, .78), (.20, .42, .50), (.86, .85, .82)),
         ((.96, .88, .60), (.22, .36, .56), (.84, .84, .82)), ((.72, .84, .93), (.92, .92, .88), (.80, .80, .79)),
         ((.97, .80, .66), (.24, .46, .38), (.88, .86, .82)), ((.94, .93, .89), (.16, .50, .56), (.62, .64, .66))]
COTTAGE = [((.95, .78, .80), (.95, .95, .92), (.80, .81, .80)), ((.78, .88, .80), (.95, .95, .92), (.78, .79, .78)),
           ((.97, .91, .66), (.95, .95, .92), (.80, .80, .79)), ((.76, .85, .94), (.95, .95, .92), (.76, .77, .78))]


def kit_of(model):
    if model and model.endswith('KM'): return km_kit(model)
    return 'Florida' if model in FLH else 'Coast' if model in COAST else 'Buildings'


def coast_house(model, x, y, z):
    if model in FLH:
        if not has('Florida', model):
            return False
        schemes = COTTAGE if model == 'CottageFL' else RANCH
        place('Florida', model, x, y, z, 0, 1, list(schemes[scramble(abs(int(round(x * 7 + z * 13)))) % len(schemes)]))
        return True
    if not has('Coast', model):
        return False
    schemes = {'CraftsmanPorch': CRAFT, 'BeachCondo': CONDO, 'ShopBeach': BSHOP, 'ShopMission': MISSION}.get(model, VILLA)
    place('Coast', model, x, y, z, 0, 1, list(schemes[scramble(abs(int(round(x * 7 + z * 13)))) % len(schemes)]))
    return True


def palm_skyline(z0, z1, s0, s1):
    if not has('Plants', 'PalmFan'):
        return
    x = X0 - 40
    while x < X1 + 40:
        n = 1 if rng.random() < .45 else rng.randrange(2, 4)
        z = rng.uniform(z0, z1)
        for k in range(n):
            plant('PalmFan', x + k * rng.uniform(2.2, 4.5), 0, z + rng.uniform(-3, 3), rng.uniform(.85, 1.25))
        x += rng.uniform(s0, s1)


def street_palms(z, s0, s1, ground=lambda x, z: 0.0):
    if not has('Plants', 'PalmDate'):
        return
    x = X0 + rng.uniform(2, s1)
    while x < X1 - 1:
        fan = rng.random() < .35
        pz = z + rng.uniform(-.3, .3)
        if in_canal(x - 1.2, x + 1.2) or in_home(x - 1.2, x + 1.2):
            x += rng.uniform(s0, s1); continue
        plant('PalmFan' if fan else 'PalmDate', x, ground(x, pz), pz, rng.uniform(.42, .5) if fan else rng.uniform(.62, .8))
        x += rng.uniform(s0, s1)


def in_canal(a, b):
    # (StreetBuilder.Blocked: the canal's quiet area, 2.8 m either side of it, keeps the street's things off its banks)
    return canal is not None and b > canal[0] - 2.8 - .6 and a < canal[1] + 2.8 + .6


def in_home(a, b):
    # (the home's plot is a quiet area too: StreetBuilder.HomePlot)
    return home_x is not None and b > home_x - 5.6 - .6 and a < home_x + 7.8 + .6


def scramble(seed):
    # StreetBuilder.Scramble: mixes a position-derived seed so evenly spaced buildings vary.
    h = (seed * 2654435761) & 0xffffffff
    h ^= h >> 15
    h = (h * 2246822519) & 0xffffffff
    return (h ^ (h >> 13)) & 0x7fffffff


def building(model, x, z, schemes):
    if not has('Buildings', model):
        return False
    w = size('Buildings', model).x
    sc = min(1.25, max(0.8, WIDTH.get(model, w) / w))
    p = schemes[scramble(abs(int(round(x * 7 + z * 13)))) % len(schemes)] if schemes else None
    place('Buildings', model, x, 0, z, 0, sc, list(p) if p else None)
    return True


KM_TREES = {'Palm': 'BlackPine', 'PalmShort': 'BlackPine', 'PalmDate': 'GardenPine', 'PalmFan': 'BlackPine', 'Broadleaf': 'Camphor',
            'BroadleafLarge': 'Camphor', 'BroadleafWide': 'CherryLeaf', 'BroadleafSmall': 'Persimmon', 'BroadleafYoung': 'Persimmon',
            'ConiferTall': 'Cedar', 'ConiferMid': 'Cedar', 'ConiferSmall': 'GardenPine', 'Birch': 'CherryLeaf', 'CherryBlossom': 'CherryLeaf',
            'BushRound': 'Azalea', 'BushWide': 'Hydrangea', 'ShrubFlowering': 'Hydrangea'}   # (StreetBuilder.Kamakura's lists)


def plant(model, x, y, z, scale):
    if kamakura_mode and has('Plants', KM_TREES.get(model, model)):
        model = KM_TREES.get(model, model)
    if florida and has('Plants', 'PalmSabal'):        # StreetBuilder.FloridaPalm
        model = {'PalmDate': 'PalmSabal', 'PalmFan': 'PalmSabalTall'}.get(model, model)
    leaves = None
    if model.startswith('Broadleaf') or model == 'Birch' or model.startswith('Bush'):
        leaves = rng.choice(SUMMER)
    elif model.startswith('Palm') and not model.startswith('PalmSabal'):
        leaves = PALM
    elif model in ('TallGrass', 'GrassTuft') and rng.random() < .8:
        leaves = rng.choice(MEADOW)
    place('Plants', model, x, y, z, rng.uniform(0, 360), scale, [leaves, None, None] if leaves else None)


def poles():
    if chapter in (2, 3, 5) or not has('Street', 'UtilityPole'):
        return
    xs = [x for x in np.arange(X0 - 21, X1 + 21, 21.0) if not in_canal(x - .5, x + .5) and not in_home(x - .5, x + .5)]
    anchors = attach_points('Street', 'UtilityPole', 'Attach.Wire')
    yaw = 90.0
    R = Matrix.Rotation(-math.radians(yaw), 3, 'Z')
    for x in xs:
        place('Street', 'UtilityPole', float(x), 0, POLE_Z, yaw)
        if has('Street', 'StreetLamp'):
            place('Street', 'StreetLamp', float(x) + 10.5, 0, POLE_Z)
            if rng.random() < .45: place('Street', 'Bin', float(x) + 11.2, 0, POLE_Z + .05, rng.uniform(-10, 10))
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
    box(X0 - 2000, X1 + 2000, -0.16, -0.06, 89, 760, fields, 'fields')

    def layer(model, a, b, y, z, scale, phase):
        if not has('Terrain', model):
            return
        tile = kits['Terrain']['models'][model].get('tileWidth', size('Terrain', model).x) * scale
        x = math.floor(a / tile) * tile + phase * tile
        while x < b + tile:
            place('Terrain', model, x, y, z, 0, scale, [grass, None, None] if grass else None)
            x += tile
    if not kamakura_mode: layer('ForestStrip', X0 - 250, X1 + 250, -0.3, 70, 1.0, 0)
    if florida: return          # (Florida is flat: StreetBuilder.DistantHills)
    if kamakura_mode:           # (Kamakura's low wooded hills, no snowy ranges: StreetBuilder.DistantHills)
        layer('HillsRolling', X0 - 450, X1 + 450, -0.4, 230, 1.0, 0)
        layer('HillsRolling', X0 - 700, X1 + 700, -0.6, 420, 1.25, 0.5)
        return
    layer('HillsRolling', X0 - 450, X1 + 450, -0.4, 230, 1.0, 0)
    layer('MountainRange1', X0 - 700, X1 + 700, -0.8, 440, 0.75, 0)
    layer('MountainRange2', X0 - 900, X1 + 900, -0.8, 640, 1.0, 0.5)


# The town's fronts and houses (StreetBuilder.MarketFronts / HomeHouses / FrontPaints / Deck).
MARKET = ['ShopFruit', 'ShopBeach', 'ShopShutter', 'ShopMission', 'ShopMart', 'ShopCafe', 'ShopBeach', 'ShopBooks', 'ShopFlorist', 'ShopMission', 'ShopTall', 'ShopBoutique']
HOMES = ['VillaStucco', 'CraftsmanPorch', 'VillaRanch', 'VillaStucco', 'CraftsmanPorch', 'VillaRanch']
if fl_home: HOMES = ['RanchFL', 'CottageFL', 'RanchSmallFL', 'RanchFL', 'RanchSmallFL', 'CottageFL']
SR = (.56, .57, .6)
FRONT = {
    'ShopMart': [((.95, .95, .93), (.84, .26, .2), SR), ((.93, .91, .86), (.93, .55, .18), SR), ((.86, .87, .87), (.2, .42, .72), SR), ((.94, .92, .87), (.96, .76, .2), SR)],
    'ShopCafe': [((.94, .93, .9), (.22, .4, .42), SR), ((.9, .88, .84), (.2, .26, .4), SR), ((.92, .9, .86), (.5, .2, .22), SR), ((.86, .87, .86), (.42, .46, .28), SR)],
    'ShopBooks': [((.8, .62, .52), (.18, .36, .3), SR), ((.84, .8, .72), (.2, .27, .42), SR), ((.68, .52, .44), (.2, .34, .3), SR), ((.8, .8, .78), (.46, .18, .18), SR)],
    'ShopFlorist': [((.95, .94, .9), (.34, .55, .37), SR), ((.9, .9, .88), (.52, .62, .5), SR), ((.94, .92, .87), (.4, .58, .74), SR), ((.88, .89, .9), (.74, .42, .32), SR)],
    'ShopNoodle': [((.93, .9, .84), (.3, .22, .18), SR), ((.95, .95, .93), (.3, .22, .18), SR), ((.84, .85, .86), (.3, .22, .18), SR)],
    'ShopTall': [((.84, .82, .78), (.62, .64, .66), SR), ((.9, .9, .89), (.72, .73, .72), SR), ((.32, .34, .4), (.66, .68, .7), SR),
                 ((.66, .56, .48), (.6, .62, .6), SR), ((.78, .81, .84), (.5, .58, .54), SR)],
    'ShopBoutique': [((.26, .28, .33), (.3, .31, .33), SR), ((.36, .31, .28), (.3, .31, .33), SR), ((.3, .35, .34), (.62, .64, .66), SR),
                     ((.56, .54, .51), (.3, .31, .33), SR)],
    'ShopKonbini': [((.95, .95, .94), (.62, .66, .7), SR), ((.88, .89, .9), (.62, .66, .7), SR)],
}
BANNERS = [(.84, .28, .22), (.24, .42, .72), (.26, .54, .36), (.94, .55, .2)]
BANDS = [(.98, .82, .3), (.96, .95, .92)]
CRATES = [(.93, .74, .26), (.3, .5, .74), (.36, .6, .42), (.84, .3, .26)]
BINS = [(.32, .5, .4), (.36, .46, .6), (.46, .48, .5), (.26, .38, .3)]
BIKES = [(.52, .72, .68), (.86, .42, .36), (.95, .8, .35), (.4, .5, .72)]
PETALS = [(.98, .5, .6), (.95, .3, .32), (1, .82, .3), (.97, .96, .94), (.72, .5, .9)]


class Deck:
    def __init__(self, models):
        self.models, self.left, self.last = models, [], None

    def next(self, fits=lambda m: True):
        for p in range(2):
            if p == 1 or not self.left:
                self.left = [m for m in self.models if has(kit_of(m), m)]
                rng.shuffle(self.left)
            for i, m in enumerate(self.left):
                if m != self.last and fits(m):
                    del self.left[i]; self.last = m
                    return m
        return None


def paint_for(model, fallback, x, z):
    schemes = FRONT.get(model, fallback)
    return schemes[scramble(abs(int(round(x * 7 + z * 13)))) % len(schemes)]


def banner(x):
    place('Street', 'BannerFlag', x, 0, POLE_Z + .3, rng.uniform(-6, 6), 1, [rng.choice(BANNERS), rng.choice(BANDS), None])


def shop_front(model, cx, w):
    if model in COAST:
        coast_house(model, cx, 0, PROP + .6); return
    z = PROP + (2.6 if model == 'ShopKonbini' else .6)
    p = paint_for(model, SHOP, cx, z)
    place('Buildings', model, cx, 0, z, 0, 1, list(p))
    board = PROP + .02
    if model == 'ShopMart':
        place('Street', 'DrinksCrates', cx + 3.55, 0, PROP + .32, rng.uniform(-8, 8), 1, [rng.choice(CRATES), None, None])
        if rng.random() < .5: place('Street', 'CrateStack', cx - 3.1, 0, PROP + .35, rng.uniform(-10, 10))
        banner(cx - 2.4); banner(cx + 2.2)
    elif model == 'ShopCafe':
        place('Street', 'SignBoardA', cx + .75, 0, board, rng.uniform(-15, 15), 1, [(.3, .26, .22), None, None])
    elif model == 'ShopBooks':
        place('Street', 'SignBoardA', cx - 1.7, 0, board, rng.uniform(-15, 15), 1, [(.2, .3, .26), None, None])
    elif model == 'ShopNoodle':
        place('Street', 'SignBoardA', cx + .1, 0, board, 180 + rng.uniform(-15, 15), 1, [(.3, .22, .18), None, None])
        banner(cx + 2.75)
    elif model == 'ShopTall':
        place('Street', 'UtilityBox', cx - .5, 0, z - .32)
        if rng.random() < .5: place('Street', 'Bicycle', cx + 1.35, 0, z - .45, 180 + rng.uniform(-6, 6), 1, [rng.choice(BIKES), None, None])
    elif model == 'ShopBoutique':
        banner(cx - 2.15)
        if rng.random() < .5: place('Street', 'PotGroup', cx + 1.4, 0, z - .55, rng.uniform(-20, 20), 1, [rng.choice(PETALS), None, None])
    elif model == 'ShopKonbini':
        place('Street', 'VendingRed', cx - 4.1, 0, z - .45); place('Street', 'VendingBlue', cx - 3.05, 0, z - .45)
        if place('Street', 'BikeRack', cx - .9, 0, z - 1.2):
            for k in range(3):
                if rng.random() < .6:
                    place('Street', 'Bicycle', cx - 1.8 + .9 * k + .25, 0, z - 1.15 - .08 * k, 180 + rng.uniform(-5, 5), 1, [rng.choice(BIKES), None, None])


def town_house(model, x, z):
    if model in COAST or model in FLH:
        return coast_house(model, x, 0, z)
    if model in ('HouseGable', 'HouseLong', 'Bungalow') or not has('Buildings', model):
        return False
    place('Buildings', model, x, 0, z, 0, 1, list(paint_for(model, HOUSE, x, z)))
    return True


def suburb():
    houses = Deck(HOMES)
    quiet = []
    if canal: quiet.append((canal[0] - 2.8, canal[1] + 2.8))
    if home_x is not None: quiet.append((home_x - 5.6, home_x + 7.8))
    x = X0
    while x < X1:
        lot = rng.uniform(12.9, 15); cx = x + lot / 2
        hit = [q for q in quiet if x + lot > q[0] - .6 and x < q[1] + .6]
        if hit:
            x = hit[0][1] + .8; continue
        gate = rng.uniform(x + 2, x + lot - 4)
        front = rng.random()
        picket = front < (.2 if fl_home else .35) and has('Street', 'PicketFence2')
        garden = fl_home and scramble(abs(int(round(x * 7))) + 17) % 3 == 0      # StreetBuilder.GardenLot
        hedge = not picket and not garden and front < (.4 if fl_home else .65) and has('Plants', 'HedgeBlock2')
        if picket:
            row('Street', 'PicketFence2', x + .1, gate, 0, PROP + .15); row('Street', 'PicketFence2', gate + 1.4, x + lot - .1, 0, PROP + .15)
        elif hedge:
            if gate - x > 1.6: row('Plants', 'HedgeBlock2', x + .3, gate - .2, 0, PROP + .4, [HEDGE, None, None])
            if x + lot - gate > 3.6: row('Plants', 'HedgeBlock2', gate + 1.6, x + lot - .3, 0, PROP + .4, [HEDGE, None, None])
        elif not has('Coast', 'VillaStucco'):
            for a, b, pa, pb in ((x + .1, gate, True, True), (gate + 2.2, x + lot - .1, True, False)):
                if b - a >= .4 and row('Street', 'BlockWall2', a, b, 0, PROP + .15):
                    if pa: place('Street', 'WallPillar', a, 0, PROP + .15)
                    if pb: place('Street', 'WallPillar', b, 0, PROP + .15)
        life = rng.random()
        if fl_home and life < .6: place('Florida', 'MailboxPostFL', gate + rng.uniform(-.6, .6), 0, POLE_Z + .05)
        elif life < .12: place('Street', 'PostBox', x + rng.uniform(1, lot - 1), 0, POLE_Z - .1)
        elif life < .3 and not picket and not hedge and gate - x > 3.4:
            place('Street', 'Bicycle', rng.uniform(x + 1.2, gate - 1), 0, PROP - .32, 180 + rng.uniform(-6, 6), 1, [rng.choice(BIKES), None, None])
        house = houses.next(lambda m: size(kit_of(m), m).x <= lot - .8)
        kind = rng.randrange(3)
        z = PROP + 1.6 + rng.uniform(0, 1.4) + (.3 if house == 'HouseLeanTo' else 0) + SETBACK.get(house, 0) + (3.2 if garden else 0)
        model = 'HouseGable' if kind == 0 else 'HouseLong' if kind == 1 and lot >= 11 else 'Bungalow'
        if house in ('HouseGable', 'HouseLong', 'Bungalow'): model = house
        town = house is not None and town_house(house, cx, z)
        if town: model = house
        else: building(model, cx, z, HOUSE)
        half = (size(kit_of(model), model).x if town else WIDTH[model]) / 2
        if garden and town: front_garden(house, x, lot, gate, cx, half, z)
        if has('Street', 'BinPair'):
            d = rng.random()
            if d < .3 and not picket and not garden:
                place('Street', 'BinPair', gate + 1.1, 0, PROP + .55, rng.uniform(-10, 10), 1, [rng.choice(BINS), rng.choice(BINS), None])
            elif d < .55 and not garden:
                place('Street', 'PotGroup', gate + .55, 0, PROP + .6, rng.uniform(-20, 20), 1, [rng.choice(PETALS), None, None])
        yard = x + lot - (cx + half)
        if not picket and yard > 1.2 and rng.random() < .6 and has('Plants', 'BushRound'):
            plant(rng.choice(['BushRound', 'ShrubFlowering']), x + lot - yard / 2, 0, PROP + 1.35, rng.uniform(1.3, 1.6))
        if house == 'HouseCarport' and town and rng.random() < .8:
            place('Street', 'Bicycle', cx + 3.4, 0, z + 1.3, 180 + rng.uniform(-5, 5), 1, [rng.choice(BIKES), None, None])
        if rng.random() < .7:
            t = rng.choice(['LiveOak', 'PalmDate', 'PalmFan', 'PalmDate', 'BroadleafWide', 'PalmFan', 'PalmDate', 'LiveOak'] if fl_home else
                           ['Broadleaf', 'PalmDate', 'BroadleafLarge', 'PalmFan', 'BroadleafWide', 'Broadleaf', 'PalmDate', 'BroadleafSmall'])
            if fl_home: t = {'PalmDate': 'PalmSabal', 'PalmFan': 'PalmSabalTall'}.get(t, t)
            tz = z + (10.5 if fl_home else 8) + rng.uniform(0, 3)
            if fl_home: tz = min(tz, 24 - 2.5)
            plant(t, cx + rng.uniform(-half, half), 0, tz, rng.uniform(.45, .55) if t == 'PalmFan' else rng.uniform(.9, 1.25))
        gap = (cx - half) - x
        if gap > 4 and house != 'HouseCarport' and house not in COAST and house not in FLH and rng.random() < .4 and has('Buildings', 'Garage'):
            p = HOUSE[scramble(abs(int(round(cx * 7 + z * 13))) + 1) % len(HOUSE)]
            place('Buildings', 'Garage', x + gap / 2, 0, z + .8, 0, 1, list(p))
        elif gap > 1.8 and rng.random() < .6:
            m = rng.choice(['PalmDate', 'ShrubFlowering', 'BroadleafYoung', 'PalmDate', 'ConiferSmall', 'BushWide'])
            plant(m, x + gap / 2, 0, PROP + 1.4 + rng.uniform(0, 1.2), rng.uniform(1.3, 1.6) if m in ('ShrubFlowering', 'BushWide') else rng.uniform(.55, .72) if m == 'PalmDate' else rng.uniform(.7, .95))
        x += lot
    street_palms(PROP + .95, 12, 26)
    cut = [(canal[0] - .3, canal[1] + .3)] if canal else []
    if fl_home and has('Plants', 'LiveOak'):           # StreetBuilder.StreetOaks
        x = X0 + rng.uniform(6, 20)
        while x < X1 - 2:
            if not any(x + 4 > a - .6 and x - 4 < b + .6 for a, b in cut):
                z = rng.uniform(20, 21); plant('LiveOak', x, 0, z, rng.uniform(.95, 1.2))
            x += rng.uniform(24, 36)
    back = Deck(['RanchFL', 'CottageFL', 'RanchSmallFL', 'RanchFL', 'CottageFL'] if fl_home else ['VillaStucco', 'VillaRanch', 'CraftsmanPorch', 'VillaStucco', 'VillaRanch'])
    x = X0 - 20
    while x < X1 + 20:
        house = back.next()
        bz = rng.uniform(20, 24) + (4 if fl_home else 0)
        hw = size(kit_of(house), house).x / 2 + .3 if has(kit_of(house), house) else 4
        if any(x + hw > a - .6 and x - hw < b + .6 for a, b in cut):
            x += rng.uniform(10, 14); continue
        if not town_house(house, x, bz):
            building(house if house in ('HouseGable', 'HouseLong') else rng.choice(['HouseGable', 'HouseLong']), x, bz, HOUSE)
        x += rng.uniform(10, 14)
    # (StreetBuilder.Depth: the next street over and the palm skyline.)
    deck = Deck(['RanchFL', 'CottageFL', 'RanchSmallFL', 'RanchFL'] if fl_home else ['VillaStucco', 'VillaRanch', 'CraftsmanPorch', 'VillaStucco'])
    x = X0 - 40
    while x < X1 + 40:
        m = deck.next(); w = size(kit_of(m), m).x
        if not any(x + w > a - .6 and x < b + .6 for a, b in cut): coast_house(m, x + w / 2, 0, rng.uniform(40, 46))
        x += w + rng.uniform(1.5, 5)
    if fl_home and home_x is not None: home_fl(home_x)
    if canal: drawbridge(*canal)
    palm_skyline(64, 105, 10, 26)
    distant((.44, .54, .32), None)


def front_garden(house, x, lot, gate, cx, half, z):
    # StreetBuilder.FrontGardenFL: lawn, walk, beds along the front, an island bed, corner shrubs.
    r = random.Random(int(round(x * 13)) + 977)
    m = kits['Florida']['models'][house]
    front = z + m['min'][1]
    door = cx + (m.get('doors') or [{'center': [0]}])[0]['center'][0]
    a, mid, g = PROP + .45, (PROP + .45 + front) / 2, gate + .7
    box(x + .3, x + lot - .3, 0, .012, a, front - .05, (.56, .74, .36), 'lawn', 'Grass')
    for x0, x1, z0, z1, k in ((g - .55, g + .55, PROP + .2, mid + .55, .016), (min(g, door) - .55, max(g, door) + .55, mid - .55, mid + .55, .017),
                              (door - .55, door + .55, mid - .55, front + .02, .016)):
        box(x0, x1, 0, k, z0, z1, (.9, .89, .86), 'walk', 'Concrete')
    bx, beds = cx - half + .7, 0
    while bx < cx + half - .6 and beds < 4:
        if abs(bx - door) >= 1.1:
            place('Plants', 'FlowerPatch', bx, 0, front - .45, r.uniform(0, 360), r.uniform(1.1, 1.4), [r.choice(PETALS), None, None]); beds += 1
        bx += r.uniform(1.4, 2.2)
    ix = min(max(cx - half * .5 if door > cx else cx + half * .5, x + 1.6), x + lot - 1.6)
    if abs(ix - g) > 1.8 and abs(ix - door) > 1.6:
        palm = r.random() < .35
        plant('PalmSabal' if palm else 'SawPalmetto', ix, 0, mid, r.uniform(.5, .6) if palm else r.uniform(1.1, 1.35))
        for k in range(3):
            t = (k / 3 + r.uniform(0, .1)) * 2 * math.pi
            place('Plants', 'FlowerPatch', ix + math.cos(t) * .9, 0, mid + math.sin(t) * .6, r.uniform(0, 360), r.uniform(1, 1.25), [r.choice(PETALS), None, None])
    for sx in (x + .9, x + lot - .9):
        if abs(sx - g) > 1.4: plant('ShrubFlowering', sx, 0, a + .55, r.uniform(1.1, 1.4))


def home_fl(gx):
    # StreetBuilder.HomeFrontFL: the ranch with its door at gx, the walk, beds, a young sabal, the mailbox, a live oak behind.
    hz = PROP + 2.5
    place('Florida', 'RanchFL', gx + 1.2, 0, hz, 0, 1, [(.70, .86, .82), (.80, .22, .17), (.88, .87, .84)])
    box(gx - .65, gx + .65, 0, .014, PROP - .05, hz - 1.19, (.9, .89, .86), 'walk', 'Concrete')
    for dx, dz in ((-1.7, 3.5), (-2.4, 3.75), (-3.1, 3.45), (-3.7, 3.7)):
        place('Plants', 'FlowerPatch', gx + dx, 0, dz, rng.uniform(0, 360), 1.2, [rng.choice(PETALS), None, None])
    plant('ShrubFlowering', gx - 4.6, 0, hz - .3, 1.15); plant('ShrubFlowering', gx + 6.9, 0, hz - .4, 1.05)
    plant('PalmSabal', gx - 4.3, 0, PROP + 1.15, .7)
    place('Street', 'Bicycle', gx + 3.9, 0, 3.1, 0, 1, [BIKES[1], None, None])
    place('Florida', 'MailboxPostFL', gx - 1.55, 0, POLE_Z + .05)
    plant('LiveOak', gx + 3.4, 0, hz + 11, 1.05)


def drawbridge(a, b):
    # LevelBuildKit.Drawbridge: the canal (water 1.25 under the street, seawalls, from the road's edge back), the road's rail,
    # the two leaves hinged at the banks (turned up --lift degrees), the tender towers, the gate posts and arms, docks, the sign.
    w, cx, water = b - a, (a + b) / 2, -1.25
    box(a - .3, b + .3, water - .1, water, -2.0, 90, (1, 1, 1), 'canal', 'Sea')
    for x in (a - .15, b + .15):
        box(x - .15, x + .15, water - 1, -.02, -2.0, 90, (.8, .78, .74), 'seawall', 'Concrete')
    place('Florida', 'CanalRailFL', a - .35, 0, 8.6, -90); place('Florida', 'CanalRailFL', b + .35, 0, 8.6, 90)
    L = w / 2 - .03
    for hinge, sgn in ((a, 1), (b, -1)):
        e = place('Florida', 'DrawLeafFL', hinge, 0, 0, 0, stretch=(sgn * L / 2.5, 1, 1))
        if e is not None:       # (both tip up about the hinge: the right one mirrored along its length, its railing still behind)
            e.rotation_euler = (0, -sgn * math.radians(lift), 0)
    up = lift > 0.5
    for bank in (a - 1.6, b + 1.6):
        place('Florida', 'DrawTowerFL', bank, 0, PATH + 1.4)
        post = bank + (-.8 if bank < cx else .8)
        # the path's traffic signal (LevelBuildKit.Drawbridge since v130): a mast before the gate, a black head, two red lamps
        mx, mz = bank + (-1.35 if bank < cx else 1.35), PATH + .35
        box(mx - .05, mx + .05, 0, 2.9, mz - .05, mz + .05, (.42, .43, .45), 'mast')
        box(mx - .33, mx + .33, 2.53, 2.87, mz - .19, mz - .01, (.08, .08, .09), 'head')
        box(mx - .43, mx + .43, 2.45, 2.95, mz - .025, mz + .005, (.08, .08, .09), 'backplate')
        for dx in (-.16, .16):
            box(mx + dx - .09, mx + dx + .09, 2.61, 2.79, mz - .215, mz - .19, (1, .22, .18) if lift > 0.5 else (.28, .06, .05), 'lens')
        place('Florida', 'GatePostFL', post, 0, PATH + .3)
        # (LevelBuildKit.Drawbridge since v129: the arm falls ACROSS the path toward the camera, cut to end at the lane's front
        # edge; it used to fall along the street behind the kid)
        arm_len = PATH * 2 + .4
        arm_h = size('Florida', 'GateArmFL').z if has('Florida', 'GateArmFL') else 4.2
        arm = place('Florida', 'GateArmFL', post, .9, PATH + .3, 0, arm_len / max(arm_h, 1.0))
        if arm is not None and up: arm.rotation_euler = (math.radians(90), 0, 0)
    if w >= 4:
        place('Florida', 'DockFL', a + 1.5, water + .3, 12)
        place('Florida', 'DockFL', b - 1.5, water + .3, 24, 180)
    place('Florida', 'SignNoWakeFL', cx + .6, water - .35, 6.2)


def market():
    deck = Deck(MARKET)
    vended = False
    x, i = X0, 0
    while x < X1:
        front = deck.next()
        w = size(kit_of(front), front).x if front else 8
        if front: shop_front(front, x + w / 2, w)
        else: building('ShopFruit' if i % 2 == 0 else 'ShopShutter', x + 4, PROP + .6, SHOP)
        x += w
        between = rng.random() < .5
        if not between and i % 2 == 1: place('Street', 'StreetLamp', x, 0, POLE_Z - .1)
        if between:
            gx, gz = x + rng.uniform(-.25, .25), PROP + .25
            r = rng.random()
            if r < .25: place('Street', 'PotC', gx, 0, gz, rng.uniform(0, 360))
            elif r < .42: place('Street', 'PotB', gx, 0, gz, rng.uniform(0, 360))
            elif r < .58: place('Street', 'PotGroup', gx, 0, gz, rng.uniform(-20, 20), 1, [rng.choice(PETALS), None, None])
            elif r < .72: place('Street', 'BinPair', gx, 0, PROP + .35, rng.uniform(-8, 8), 1, [rng.choice(BINS), rng.choice(BINS), None])
            else:
                place('Street', rng.choice(['CrateStack', 'ProduceCrate']), gx, 0, gz, rng.uniform(-15, 15)); place('Street', 'Sack', gx + .75, 0, gz - .1, rng.uniform(0, 360))
        vend = not vended and front != 'ShopKonbini' and rng.random() < .28
        vended = vend
        if vend:
            plant('PalmDate', x + 1.3, 0, PROP + .5, rng.uniform(.6, .75))
            x += 2.6
        i += 1
    x = X0 - 20
    while x < X1 + 20:
        z = rng.uniform(22, 28)
        if not (rng.random() < .5 and coast_house('BeachCondo', x, 0, z)): building('Apartment', x, z, HOUSE)
        x += rng.uniform(13, 16)
    palm_skyline(64, 100, 12, 28)


# ---------------------------------------------------------------- Florida's strip (StreetBuilder.Florida)
FL_FRONT, FL_FRONTAGE, FL_BACK, FL_RISE = 2.5, 5.0, 18.0, 0.22
FL_LOTS = [
    ('Restroom', 8.8, [('RestroomFL', 4.2, FL_FRONTAGE + .4), ('SignTurtleFL', .6, 3.3)]),
    ('Shack', 10.2, [('ShackFL', 2.6, FL_FRONTAGE), ('KayakRackFL', 7.1, FL_FRONTAGE + .8), ('SignAccessFL', 9.4, 3.4)]),
    ('Diner', 17.4, [('DinerSignFL', 1.4, 3.7), ('DinerFL', 10.0, FL_FRONTAGE + .6), ('SignHurricaneFL', 3.6, 3.3)]),
    ('Motel', 22.4, [('MotelSignFL', 1.9, 3.7), ('MotelPoolFL', 12.2, 3.3), ('MotelFL', 12.6, 8.4)]),
    ('Rentals', 13.2, [('PoleSignalFL', .4, 3.2), ('RentalsFL', 5.6, FL_FRONTAGE), ('HydrantFL', 11.9, 3.4)]),
    ('DecoSurf', 7.8, [('DecoSurfFL', 3.9, FL_FRONTAGE)]), ('DecoCafe', 6.5, [('DecoCafeFL', 3.25, FL_FRONTAGE)]),
    ('DecoBait', 6.5, [('DecoBaitFL', 3.25, FL_FRONTAGE)]), ('DecoIce', 8.3, [('DecoIceFL', 4.5, FL_FRONTAGE)]),
    ('DecoShut', 7.2, [('DecoShutFL', 3.6, FL_FRONTAGE)]),
]
FL_START = {'L12': 2, 'L13': 3, 'L14': 5}


def florida_strip(x0, x1):
    """The Florida beach town (StreetBuilder.FloridaStrip): lots in order on seawall terraces, open beach left between."""
    strip = []
    open_ = sorted(fl_open)
    nxt = FL_START.get(fl_level, 0)
    r_ = random.Random(311)
    a = x0 + 1.5
    for _ in range(400):
        if a >= x1 - 6: break
        moved = False
        for o in open_:
            if o[0] <= a < o[1]: a = o[1]; moved = True
        if moved: continue
        b = x1 - 1
        for o in open_:
            if a < o[0] < b: b = o[0]
        y = max([SAND.base] + [max(SAND.height(sx, FL_FRONT), SAND.height(sx, FL_FRONT + .25)) for sx in np.arange(a, b + .01, .5)]) + FL_RISE
        x, tries = a, 0
        while tries < len(FL_LOTS):
            name, w, models = FL_LOTS[nxt % len(FL_LOTS)]; nxt += 1
            if x + w > b: tries += 1; continue
            for m, dx, z in models: place('Florida', m, x + dx, y, z)
            x += w; tries = 0
        if x - a > 1:
            box(a - .3, x + .3, SAND.base - 1.5, y - .06, FL_FRONT + .25, FL_BACK, (.82, .8, .76), 'seawall', 'Concrete')
            box(a - .3, x + .3, y - .06, y, FL_FRONT, FL_BACK, (.86, .84, .81), 'promenade', 'Paving')
            box(a - .3, x + .3, SAND.base - .2, y, FL_FRONT, FL_FRONT + .25, (.78, .77, .74), 'kerb', 'Concrete')
            px = a + r_.uniform(1.5, 4)
            while px < x - 1: plant('PalmSabal', px, y, r_.uniform(3.2, 3.6), r_.uniform(.85, 1.1)); px += r_.uniform(9, 14)
            lx, k = a + r_.uniform(5, 8), 0
            while lx < x - 2:
                place('Florida', 'LampFL', lx, y, 3.0)
                if k % 2 == 0: place('Florida', 'BenchFL', lx + 2.2, y, 4.3); place('Florida', 'TrashFL', lx + 3.8, y, 4.2)
                lx += r_.uniform(14, 19); k += 1
            tx = a + r_.uniform(2, 6)
            while tx < x - 1: plant('PalmSabalTall', tx, y, r_.uniform(FL_BACK - 2.4, FL_BACK - .8), r_.uniform(.9, 1.15)); tx += r_.uniform(10, 16)
            strip.append((a - .5, x + .5))
        a = b + .01
    return strip


def in_strip(strip, a, b):
    return any(b > s0 and a < s1 for s0, s1 in strip)


def beach():
    g = SAND.height
    towers = []
    strip = florida_strip(X0 - 30, X1 + 30) if florida else []
    x = X0
    while x < X1:
        if not in_strip(strip, x - 2.5, x + 2.5):
            place('Florida', 'LifeguardFL', x, g(x, 7.4), 7.4) if florida else place('Leisure', 'LifeguardTower', x, g(x, 7.4), 7.4)
            towers.append(x)
        x += rng.uniform(30, 45)
    # (StreetBuilder.Beach: the pier, and date palms along the back of the beach.)
    pier_x = X0 + (X1 - X0) * .55
    while any(abs(t - pier_x) < 9 for t in towers): pier_x += 7
    if has('Coast', 'PierSpan') and not florida:
        for i in range(13): coast_house('PierSpan', pier_x, SAND.base - .3, 6.2 + 12 * i)
        coast_house('PierEnd', pier_x, SAND.base - .3, 6.2 + 12 * 13)
    if not florida: street_palms(2.8, 14, 30, lambda x, z: g(x, z) - .1)
    canopy = [(.9, .3, .28), (.25, .5, .85), (1, .75, .2), (.3, .66, .62)]
    towels = [(.95, .55, .6), (.45, .75, .9), (1, .85, .35), (.55, .8, .55)]
    x = X0 + 8
    while x < X1:
        z = rng.uniform(3.4, 5.2)
        if any(abs(t - x) < 3 for t in towers) or abs(x - pier_x) < 5 or in_strip(strip, x - 1.5, x + 2.6):
            x += rng.uniform(5, 11); continue
        p = place('Leisure', 'Parasol', x, g(x, z) - .05, z, rng.uniform(0, 360), 1, [rng.choice(canopy), None, None])
        if p: p.rotation_euler = (math.radians(rng.uniform(-7, 7)), math.radians(rng.uniform(-7, 7)), p.rotation_euler.z)
        tx = x + rng.uniform(-.3, .3)
        place('Leisure', 'BeachTowel', tx, g(tx, z - .4), z - .4, 90 + rng.uniform(-15, 15), 1, [rng.choice(towels), None, None])
        if rng.random() < .4:
            place('Leisure', 'CoolBox', x + .9, g(x + .9, z + .3), z + .3, rng.uniform(-25, 25), 1, [rng.choice(canopy), None, None])
        if rng.random() < .3:
            cx, cz, bx, bz = x + rng.uniform(1.3, 1.8), z - rng.uniform(1, 1.6), x + rng.uniform(2.1, 2.5), z - rng.uniform(.8, 1.3)
            place('Leisure', 'SandCastle', cx, g(cx, cz) - .03, cz, rng.uniform(-20, 20))
            place('Leisure', 'BucketSpade', bx, g(bx, bz), bz, rng.uniform(0, 360))
        x += rng.uniform(5, 11)
    x = X0 + 15
    while x < X1:
        s_ = rng.uniform(.8, 1.6); rz = rng.uniform(8.6, 11); bx, bz = x + rng.uniform(2, 3.5), rz - rng.uniform(.5, 1.2)
        if in_strip(strip, x - 3, x + 4): x += rng.uniform(12, 24); continue
        place('Terrain', 'RockCluster', x, g(x, rz) - .15, rz, rng.uniform(-30, 30), s_ * .8)
        if rng.random() < .5:
            place('Terrain', rng.choice(['Boulder1', 'Boulder2']), bx, g(bx, bz) - .1, bz, rng.uniform(0, 360), rng.uniform(.7, 1.1))
        x += rng.uniform(12, 24)
    x = X0 + rng.uniform(5, 15)
    while x < X1:
        for k in range(rng.randrange(1, 4)):
            px, pz = x + k * rng.uniform(2.2, 3.4), rng.uniform(5.6, 7)
            if any(abs(t - px) < 4.5 for t in towers) or in_strip(strip, px - 1.5, px + 1.5): continue
            plant(rng.choice(['Palm', 'PalmShort']), px, g(px, pz) - .1, pz, rng.uniform(.85, 1.15))
        x += rng.uniform(16, 32)
    x = X0
    while x < X1:
        z = rng.uniform(-6.5, -3.4)
        for k in range(rng.randrange(1, 4)):
            gx, gz = x + k * rng.uniform(.5, .9), z + rng.uniform(-.4, .4)
            plant('DuneGrass', gx, g(gx, gz) - .03, gz, rng.uniform(.7, 1.4))
        x += rng.uniform(1.2, 4)
    for i in range(3):
        place('Terrain', 'Headland', X0 + (X1 - X0) * (.15 + i * .4) + rng.uniform(-40, 40), SAND.base - 0.8, 650 + i * 60, rng.uniform(-15, 15), rng.uniform(2.2, 3))
    # The foam at the waterline (StreetBuilder.Beach's shoreline, at rest).
    box(X0 - 60, X1 + 60, SAND.base - .3, SAND.base - .28, 9.2, 10, (.97, .98, 1), 'foam')


def site_yard(x, w, deep):
    z = PROP + 1.4
    k = rng.randrange(4 if deep else 3)
    if k == 0:
        place('Works', 'Digger', x + rng.uniform(3, 4.5), 0, z + .4, rng.uniform(-25, 25))
        place('Terrain', 'SandPile', x + w - rng.uniform(2, 3), 0, z, rng.uniform(0, 360), rng.uniform(.9, 1.2))
    elif k == 1:
        place('Works', 'Skip', x + rng.uniform(2.5, 3.5), 0, z + .3, rng.uniform(-10, 10))
        place('Works', 'Wheelbarrow', x + rng.uniform(6, 7), 0, z - .2, rng.uniform(-40, 40))
        place('Works', 'CementMixer', x + w - rng.uniform(1.8, 2.6), 0, z, rng.uniform(-30, 30))
    elif k == 2:
        place('Works', 'PipeStack', x + rng.uniform(2, 3), 0, z + .2, rng.uniform(-10, 10))
        place('Works', 'SteelBeams', x + rng.uniform(6.5, 7.5), 0, z, rng.uniform(-15, 15))
        place('Street', 'TrafficCone', x + w - 1.2, 0, PROP + .5, rng.uniform(0, 360))
    else:
        place('Works', 'SiteCabin', x + rng.uniform(3.6, 4.4), 0, z + 1.3, rng.uniform(-5, 5))
        place('Works', 'PortaLoo', x + w - rng.uniform(1.4, 2), 0, z + .4, rng.uniform(-20, 20))
        return True
    return False


def city():
    x = X0
    while x < X1:
        w = rng.uniform(11, 14); cx = x + w / 2
        flats = rng.random() >= .5; cabin = False
        front = rng.random()
        if front < .35:
            if rng.random() < .5: place('Street', 'SignNoEntry', cx - w / 2 + .5, 0, POLE_Z - .15)
            row('Street', 'Hoarding3', x + .15, x + w - .15, 0, PROP + .2)
        elif front < .55:
            row('Works', 'SiteFence', x + .2, x + w - .2, 0, PROP + .2); cabin = site_yard(x, w, flats)
        else:
            cabin = site_yard(x, w, flats)
        if front >= .35 and rng.random() < .35: place('Street', 'UtilityBox', x + w - 1, 0, PROP + .65, rng.uniform(-4, 4))
        if flats and rng.random() < .35 and has('Buildings', 'ShopTall') and has('Buildings', 'ShopBoutique'):
            two = ['ShopTall', 'ShopBoutique'] if rng.random() < .5 else ['ShopBoutique', 'ShopTall']
            for k, m in enumerate(two):
                hw = size('Buildings', m).x / 2
                bx = cx - hw - .1 if k == 0 else cx + hw + .1
                place('Buildings', m, bx, 0, PROP + 4, 0, 1, list(paint_for(m, WORK, bx, PROP + 4)))
        elif not flats:
            building('Warehouse', cx, PROP + 3, WORK)
        else:
            building('Apartment', cx, PROP + 5, HOUSE)
            if not cabin and rng.random() < .4: row('Works', 'Scaffold', cx - 6.2, cx + 6.2, 0, PROP + 5 - .9)
        x += w
    x = X0
    while x < X1:
        place('Works', 'TowerCrane', x + rng.uniform(-20, 20), 0, rng.uniform(170, 230), rng.uniform(-40, 40) + (180 if rng.random() < .5 else 0), rng.uniform(.85, 1.05))
        x += rng.uniform(70, 120)
    palm_skyline(66, 110, 15, 35)
    distant((.54, .58, .46), None)


def park_features():
    clearings = []
    if not has('Leisure', 'Slide'):
        return clearings
    kind = rng.randrange(4)
    x = X0 + rng.uniform(10, 30)
    while x < X1:
        k = kind % 4; kind += 1
        if k == 0:
            place('Leisure', 'Sandpit', x - .5, .04, 6.8, rng.uniform(-10, 10)); place('Leisure', 'Slide', x - 3.8, .04, 8.8, rng.uniform(-20, 20))
            place('Leisure', 'SwingSet', x + 1.2, .04, 10, rng.uniform(-10, 10)); place('Leisure', 'SeeSaw', x + 4.6, .04, 7.4, rng.uniform(-25, 25))
        elif k == 1:
            place('Leisure', 'DuckPond', x, .02, 9, rng.uniform(-10, 10), rng.uniform(1.3, 1.6))
            for j in range(4):
                plant('Reeds', x + rng.uniform(-3.2, 3.2), .04, 9 + (-1 if j % 2 == 0 else 1) * rng.uniform(1.6, 2.2), rng.uniform(.9, 1.3))
        elif k == 2:
            place('Leisure', 'Gazebo', x, .04, 11, rng.uniform(-20, 20))
        else:
            place('Leisure', 'PicnicTable', x - 1.8, .04, 6.8, rng.uniform(-15, 15)); place('Leisure', 'PicnicTable', x + 2, .04, 8.2, rng.uniform(-15, 15))
        clearings.append((x - 6, x + 6))
        x += rng.uniform(45, 75)
    return clearings


def park():
    x = X0
    seg = 0
    while x < X1:
        w = rng.uniform(6, 10); cx = x + w / 2
        if seg % 2 == 0: place('Leisure', 'ParkLamp', x, .04, PROP - .1)
        seg += 1
        row('Plants', 'HedgeBlock2', x + .6, x + w - .6, .04, PROP + .4, [HEDGE, None, None])
        plant(rng.choice(['ShrubFlowering', 'BushRound']), cx - w * .25, .04, PROP + 1.5, rng.uniform(1.2, 1.6))
        if rng.random() < .4:
            place('Street', 'Bench', cx + 1.5, .04, PROP - .55)
        x += w
    clearings = park_features()
    x = X0
    while x < X1:
        r = rng.random()
        if any(a - 3 < x < b + 3 for a, b in clearings):
            x += rng.uniform(4, 8); continue
        plant('CherryBlossom' if r < .3 else 'Broadleaf' if r < .65 else 'BroadleafLarge' if r < .85 else 'Birch', x, .04, rng.uniform(6.5, 16), rng.uniform(.85, 1.15))
        x += rng.uniform(4, 8)
    x = X0
    while x < X1:
        if not any(a - 1.5 < x < b + 1.5 for a, b in clearings):
            plant('BushWide' if rng.random() < .6 else 'BushRound', x, .04, rng.uniform(3.5, 6), rng.uniform(1, 1.5))
        x += rng.uniform(4, 9)
    x = X0 - 20
    while x < X1 + 20:
        plant(rng.choice(['BroadleafLarge', 'Broadleaf', 'BroadleafWide', 'ConiferTall', 'BroadleafLarge', 'ConiferMid', 'Birch']), x, .04, rng.uniform(22, 40), rng.uniform(.95, 1.35))
        x += rng.uniform(3, 6)
    x = X0
    while x < X1:
        plant(rng.choice(['TallGrass', 'GrassTuft', 'FlowerPatch', 'GrassTuft', 'TallGrass']), x, .08, rng.uniform(-6.5, -2.4), rng.uniform(1.1, 1.8))
        x += rng.uniform(.8, 2.6)
    palm_skyline(66, 100, 14, 30)
    distant((.44, .54, .32), None)


def miami(leg, plan_path):
    """Florida's own legs (docs/CITIES.md): the ground strips, the water and every placement of the leg's district, read from
    the plan the game builds from (tools/blender/miami_plan.py, MiamiDistricts.json: StreetBuilder.Miami)."""
    plan = json.load(open(plan_path))['legs'][leg]
    kind = plan['strips']
    pave, conc, asph, kerb, grass = (.86, .85, .82), (.82, .81, .78), (.42, .43, .45), (.9, .9, .88), (.5, .64, .34)
    if kind in ('street', 'havana'):
        strip(-16.0, -8.3, conc, 0.0, 0.0, "Concrete"); strip(-8.3, -8.1, kerb, 0.0, 0.0, 'Kerb')
        strip(-8.1, -1.7, asph, -0.14, 0.0, 'Asphalt'); strip(-1.7, -1.5, kerb, 0.0, 0.0, 'Kerb')
        strip(-1.5, PATH, conc, 0.0, 0.0, 'Concrete'); strip(PATH, PROP + 0.6, conc, 0.0, 0.0, 'Concrete')
        strip(PROP + 0.6, plan.get('back', 90.0), grass if kind == 'havana' else conc, 0.0, 0.0, 'Grass' if kind == 'havana' else 'Concrete')
        for zl in (-2.0, -7.8):
            box(X0 - 600, X1 + 600, -0.14, -0.13, zl - .06, zl + .06, (.95, .95, .93), 'line')
        for xl in range(int(X0) - 60, int(X1) + 60, 6):
            box(xl, xl + 3, -0.14, -0.128, -4.96, -4.84, (.98, .82, .25), 'dash')
    elif kind == 'promenade':
        strip(-16.0, -1.5, grass, 0.04, 0.0, "Grass"); strip(-1.5, PATH, pave, 0.0, 0.0, 'Paving')
        strip(PATH, plan.get('water', {}).get('z', 4.6), pave, 0.0, 0.0, 'Paving')
    else:
        strip(-16.0, -1.5, grass, 0.04, 0.0, "Grass"); strip(-1.5, PATH, pave, 0.0, 0.0, 'Paving')
        strip(PATH, plan.get('water', {}).get('z', 90.0), grass, 0.04, 0.0, 'Grass')
    w = plan.get('water')
    if w:
        box(w['from'], w['to'], w['y'] - 0.1, w['y'], w['z'], w.get('z1', w['z'] + 1200), (1, 1, 1), 'water', 'Sea')
        box(w['from'], w['to'], w['y'] - 0.4, 0.0, w['z'] - 0.35, w['z'], (.8, .79, .76), 'seawall', 'Concrete')
    # The side streets (StreetBuilder.CrossingStreet: asphalt from the footpath back to z 70) and the land round them
    # (StreetBuilder.Miami cuts the land for each up to SideStreetDepth, z 72).
    streets = [(a, b) for a, b in fl_open]
    for a, b in streets:
        box(a, b, -0.2, 0.004, -PATH, 70.0, asph, 'sidestreet', 'Asphalt')
    for l in plan.get('land', []):
        surf = l.get('surface', 'Grass')
        rgb = conc if surf == 'Concrete' else grass
        pieces = [(l['from'], l['to'])]
        if l['z0'] < 72.0:
            for a, b in streets:
                nxt = []
                for p0, p1 in pieces:
                    if b <= p0 or a >= p1: nxt.append((p0, p1)); continue
                    if a > p0: nxt.append((p0, a))
                    if b < p1: nxt.append((b, p1))
                pieces = nxt
            for a, b in streets:
                sa, sb = max(l['from'], a), min(l['to'], b)
                if sb > sa and l['z1'] > 72.0: box(sa, sb, -0.2, 0.0, 72.0, l['z1'], rgb, 'land', surf)
        for p0, p1 in pieces:
            box(p0, p1, -0.2, 0.0, l['z0'], l['z1'], rgb, 'land', surf)
    # Built shapes (the port, v140: StreetBuilder.Miami builds the same from the plan), turned rz degrees about the z axis.
    for bx in plan.get('boxes', []):
        cx, cy, cz = bx['c']; sx, sy, sz = bx['s']
        a = math.radians(bx.get('rz', 0.0)); ca, sa_ = math.cos(a), math.sin(a)
        me = bpy.data.meshes.new(bx['n'])
        v = []
        for dx in (-sx / 2, sx / 2):
            for dy in (-sy / 2, sy / 2):
                for dz in (-sz / 2, sz / 2):
                    v.append(tuple(B(cx + dx * ca - dy * sa_, cy + dx * sa_ + dy * ca, cz + dz)))
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        me.from_pydata(v, [], f); me.materials.append(flat_mat(tuple(bx['rgb']), bx.get('surf')))
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(bx['n'], me); S.collection.objects.link(o)
    for lb in plan.get('labels', []):
        cu = bpy.data.curves.new('label', 'FONT'); cu.body = lb['t']; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        cu.size = lb['size'] * 4.8      # (TextMesh: characterSize x fontSize 48 / 10)
        o = bpy.data.objects.new('label', cu); S.collection.objects.link(o)
        o.location = B(*lb['c']); o.rotation_euler = (math.radians(90), 0, 0)
        o.data.materials.append(flat_mat(tuple(lb['rgb'])))
    for it in plan['items']:
        kit, model, x, z, yaw, scale = it[:6]
        y = it[6] if len(it) > 6 else 0.0
        if abs(x - CAM_X) > 400 and z < 100: continue
        place(kit, model, x, y, z, yaw, scale)


def km_kit(m):
    return 'Kamakura' if has('Kamakura', m) else 'KamakuraStreet'


def kamakura_home():
    """StreetBuilder.Suburb in Kamakura (StreetBuilder.Kamakura): the flush lane with its green walking strip, block walls,
    board fences and hedges with their gates, the timber-and-mortar homes, pots and bonsai at the gates, laundry poles and
    sheds, hydrangeas and azaleas, persimmons, cherries, camphors and black pines behind, a back row of homes."""
    asph, pave, grass = (.42, .43, .45), (.8, .79, .77), (.5, .64, .34)
    strip(-16.0, -8.3, pave, 0.0, 0.0, 'Paving'); strip(-8.3, -8.1, (.9, .9, .88), 0.0, 0.0, 'Kerb')
    strip(-8.1, -1.38, asph, 0.0, 0.0, 'Asphalt'); strip(-1.38, -1.26, (.96, .96, .94), 0.0, 0.0, 'Paving')
    strip(-1.26, 0.3, tuple(v * t for v, t in zip(asph, (.62, 1.0, .7))), 0.0, 0.0, 'Asphalt'); strip(0.3, PROP + 0.6, asph, 0.0, 0.0, 'Asphalt')   # (green paint on the asphalt, v130)
    strip(PROP + 0.6, 90.0, grass, 0.0, 0.0, 'Grass')
    houses = Deck(['HouseTileKM', 'HouseMetalKM', 'HouseOldKM', 'HouseShedKM', 'HouseCarportKM', 'BungalowKM', 'ApartmentKM'])
    walls = [(.86, .8, .68), (.92, .91, .88), (.78, .77, .74), (.88, .84, .76)]
    back = [t for t in ['Persimmon', 'CherryLeaf', 'Camphor', 'BlackPine', 'CherryLeaf', 'Bamboo'] if has('Plants', t)]
    x = X0 - 12
    while x < X1 + 12:
        lot = rng.uniform(9, 13)
        gate = rng.uniform(x + 2, x + lot - 4)
        f = rng.random()
        wall = 'BlockWallKM' if f < 0.55 else 'BoardFenceKM' if f < 0.85 else None
        if wall:
            row('Kamakura', wall, x + 0.1, gate, 0, PROP + 0.15); row('Kamakura', wall, gate + 1.8, x + lot - 0.1, 0, PROP + 0.15)
        else:
            row('Plants', 'HedgeBlock2', x + 0.3, gate - 0.2, 0, PROP + 0.4); row('Plants', 'HedgeBlock2', gate + 1.6, x + lot - 0.3, 0, PROP + 0.4)
        place('Kamakura', 'GateKM', gate + 0.9, 0, PROP + 0.15)
        m = houses.next(lambda m: size('Kamakura', m).x <= lot - 0.8)
        cx = x + lot / 2
        z = PROP + 1.6 + rng.uniform(0, 1.4)
        half = size('Kamakura', m).x / 2 if m else 3.5
        if m: place('Kamakura', m, cx, 0, z, 0, 1, [rng.choice(walls), None, None])
        if rng.random() < 0.6: place('KamakuraStreet', 'PotShelfKM', gate + 0.9, 0, PROP + 0.75, rng.uniform(-8, 8))
        yard = x + lot - (cx + half)
        if yard > 2.6 and rng.random() < 0.5:
            place('KamakuraStreet', rng.choice(['LaundryPoleKM', 'CorrugatedShedKM']), x + lot - yard / 2, 0, z + 1.2, rng.uniform(-5, 5))
        side = (cx - half) - x
        if side > 2.2 and rng.random() < 0.5: plant(rng.choice(['Hydrangea', 'Azalea']), x + side / 2, 0, PROP + 0.9, rng.uniform(0.9, 1.2))
        if m == 'HouseCarportKM': place('KamakuraStreet', 'KeiCarKM', cx + half - 1.7, 0, z - 0.4)
        if rng.random() < 0.25 and gate - x > 3.4: place('Street', 'Bicycle', rng.uniform(x + 1.2, gate - 1), 0, PROP - 0.32, 180, 1, [rng.choice(BIKES), None, None])
        if back and rng.random() < 0.7: plant(rng.choice(back), cx + rng.uniform(-half, half), 0, z + 8 + rng.uniform(0, 3), rng.uniform(0.9, 1.2))
        x += lot
    deck = Deck(['HouseTileKM', 'HouseMetalKM', 'HouseOldKM', 'ApartmentKM', 'HouseShedKM'])
    x = X0 - 20
    while x < X1 + 20:
        m = deck.next()
        if m: place('Kamakura', m, x, 0, rng.uniform(20, 24), 0, 1, [rng.choice(walls), None, None])
        x += rng.uniform(10, 14)
    distant((.44, .54, .32), None)


def kamakura_market():
    """StreetBuilder.Market in Kamakura: the shops with noren and lanterns at the back of the footpath, nobori banners, drinks
    machines and a green phone in the gaps, scooters and bicycles; homes behind."""
    strip(-16.0, -1.5, (.62, .6, .58), -0.06, 0.0, 'Cobbles'); strip(-1.5, PROP + 0.6, (.86, .85, .83), 0.0, 0.0, 'Paving')
    strip(PROP + 0.6, 90.0, (.8, .79, .77), 0.0, 0.0, 'Paving')
    shops = Deck(['ShopSembeiKM', 'ShopSobaKM', 'ShopWagashiKM', 'ShopSouvenirKM', 'ShopFishKM', 'ShopKissaKM', 'ShopTeaKM', 'ShopSouvenirKM'])
    x = X0 - 12
    while x < X1 + 12:
        m = shops.next()
        if not m: break
        w = size('Kamakura', m).x
        cx = x + w / 2
        place('Kamakura', m, cx, 0, PROP + 0.6)
        d = rng.random()
        if d < 0.35: place('Kamakura', 'NoboriKM', cx - w / 2 + 0.5, 0, PROP + 0.25, rng.uniform(-10, 10))
        elif d < 0.55: place('KamakuraStreet', rng.choice(['VendingKM', 'VendingKM2']), cx + w / 2 - 0.6, 0, PROP + 0.45)
        elif d < 0.7: place('KamakuraStreet', 'ScooterKM', cx + w / 2 - 0.9, 0, PROP + 0.35, 180)
        x += w
        if rng.random() < 0.28:
            place('KamakuraStreet', 'VendingKM', x + 0.7, 0, PROP + 0.2)
            place('KamakuraStreet', 'PhoneBoothKM' if rng.random() < 0.5 else 'VendingKM2', x + 1.8, 0, PROP + 0.3)
            x += 2.6
    walls = [(.86, .8, .68), (.92, .91, .88), (.78, .77, .74)]
    deck = Deck(['HouseTileKM', 'HouseMetalKM', 'HouseOldKM', 'ApartmentKM'])
    x = X0 - 20
    while x < X1 + 20:
        m = deck.next()
        if m: place('Kamakura', m, x, 0, rng.uniform(16, 20), 0, 1, [rng.choice(walls), None, None])
        x += rng.uniform(9, 13)
    distant((.44, .54, .32), None)


def kamakura_extras():
    """Chapter 4's tram line behind the street (StreetBuilder.KamakuraTramLine) and chapter 5's temple ground
    (StreetBuilder.KamakuraTempleGrounds), on top of the chapter's own street."""
    if chapter == 4 and has('KamakuraStreet', 'TrackKM'):
        row('KamakuraStreet', 'TrackKM', X0 - 20, X1 + 20, 0, 12.5)
        x = math.ceil((X0 - 20) / 30.0) * 30.0
        while x < X1 + 20:
            place('KamakuraStreet', 'TramPoleKM', x, 0, 14.3); x += 30.0
        place('KamakuraStreet', 'TramKM', CAM_X + 6, 0.32, 12.5)
    if chapter == 5 and has('KamakuraStreet', 'ToriiKM'):
        x = CAM_X + 4
        place('KamakuraStreet', 'ToriiKM', x, 0, PROP + 2.2)
        for sg in (-1, 1):
            place('KamakuraStreet', 'StoneLanternKM', x + sg * 3.4, 0, PROP + 1.6)
            for k in range(2): place('KamakuraStreet', 'MossWallKM', x + sg * (5.4 + k * 4), 0, PROP + 3.9)
        place('KamakuraStreet', 'StoneStepsKM', x, 0, PROP + 3.4)
        place('KamakuraStreet', 'TempleGateKM', x, 0, 16)
        place('KamakuraStreet', 'EmaRackKM', x + 7.5, 0, PROP + 2.4)


if '--miami' in args:
    miami(args[args.index('--miami') + 1], args[args.index('--plan') + 1])
    if canal: drawbridge(*canal)      # (a leg's drawbridge: --canal a:b [--lift degrees], as LevelBuildKit.Drawbridge builds it)
    # set pieces the game's builder places (the arcades, the sweeper...): --extra kit:model:x:y:z[:yaw[:scale]],...
    if '--extra' in args:
        for spec in args[args.index('--extra') + 1].split(','):
            f = spec.split(':')
            v = [float(t) for t in f[2:]]
            place(f[0], f[1], v[0], v[1], v[2], v[3] if len(v) > 3 else 0.0, v[4] if len(v) > 4 else 1.0)
elif kamakura_mode and chapter in (1, 2):
    {1: kamakura_home, 2: kamakura_market}[chapter]()
    poles()
else:
    {1: suburb, 2: market, 3: beach, 4: city, 5: park}[chapter]()
    poles()
    if kamakura_mode: kamakura_extras()

# A kid-sized marker on the footpath for scale (1.55 m), where the player would stand, and the ball
# (34 cm across, a little larger than life, as in the game) at their feet.
kid_y = SAND.lane(CAM_X - 2.2) if SAND else 0.0
box(CAM_X - 2.2 - .2, CAM_X - 2.2 + .2, kid_y, kid_y + 1.55, -.15, .15, (.9, .35, .3), 'kid')
ball_y = SAND.lane(CAM_X - 1.6) if SAND else 0.0
box(CAM_X - 1.6 - .17, CAM_X - 1.6 + .17, ball_y, ball_y + .34, -.17, .17, (.97, .97, .95), 'ball')

# ---------------------------------------------------------------- the game camera
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
# CameraFollow2D's framing: 34 degrees, 3.6 m half-height at the gameplay plane, tilted 4 degrees,
# centred 1.9 m above the kid's feet and 2.2 m ahead of them.
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(34); cam.data.clip_end = 3000
pitch = math.radians(4); half = 3.6; dist = half / math.tan(math.radians(17))
focus = Vector((CAM_X, 0, 1.9))            # Blender coords: (x, depth, up)
fwd = Vector((0, math.cos(pitch), -math.sin(pitch)))
cam.location = focus - fwd * dist
cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
if '--camup' in args:      # a look from above the street at its far ground (a check, not the game's view)
    cam.location.z += float(args[args.index('--camup') + 1])
    cam.rotation_euler = (Vector((CAM_X, 300.0, 0.0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()

# Distance haze like DtsHaze, in every material: toward the haze colour by an eased-out ramp of the
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
    mr = t.nodes.new('ShaderNodeMapRange')       # linear, clamped: 0 at haze_start, 1 at haze_end
    mr.inputs['From Min'].default_value = mood['haze_start']; mr.inputs['From Max'].default_value = mood['haze_end']
    inv = t.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    sq = t.nodes.new('ShaderNodeMath'); sq.operation = 'POWER'; sq.inputs[1].default_value = 2.0
    ease = t.nodes.new('ShaderNodeMath'); ease.operation = 'SUBTRACT'; ease.inputs[0].default_value = 1.0
    k = t.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = mood['haze_k']
    em = t.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = haze; em.inputs['Strength'].default_value = 1.0
    mix = t.nodes.new('ShaderNodeMixShader')
    t.links.new(camd.outputs['View Distance'], mr.inputs['Value'])
    t.links.new(mr.outputs['Result'], inv.inputs[1]); t.links.new(inv.outputs[0], sq.inputs[0])
    t.links.new(sq.outputs[0], ease.inputs[1]); t.links.new(ease.outputs[0], k.inputs[0])
    hole = t.nodes.get('AlphaMask')          # cut-out leaf cards (kit_plants.py): no haze in the holes
    if hole is not None:
        km = t.nodes.new('ShaderNodeMath'); km.operation = 'MULTIPLY'
        t.links.new(k.outputs[0], km.inputs[0]); t.links.new(hole.outputs[0], km.inputs[1])
        k = km
    t.links.new(k.outputs[0], mix.inputs['Fac'])
    t.links.new(shader, mix.inputs[1]); t.links.new(em.outputs['Emission'], mix.inputs[2])
    t.links.new(mix.outputs['Shader'], outn.inputs['Surface'])

S.render.filepath = out
if '--save' in args:          # the scene as a .blend, to look into (no render)
    bpy.ops.wm.save_as_mainfile(filepath=args[args.index('--save') + 1]); sys.exit(0)
bpy.ops.render.render(write_still=True)
print('preview', out, len(placed), 'models placed')
