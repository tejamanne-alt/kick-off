# A preview of a stretch of street in the game, built from the asset kits the way the game's
# StreetBuilder places them, seen through the game camera (34 degree vertical field of view, about
# 12 m back and under 3 m up, tilted 4 degrees down) in the chapter's light and haze (ChapterTheme moods).
# Kit models get the street's paint schemes (ModelTint's brightness-ratio recolour). The shading is
# Blender's, not the game's toon ramp, so judge layout, scale, silhouettes and colour, not shading.
#   blenv/bin/python preview_street.py -- <kits dir> <out.png> [--chapter 1..5] [--seed N] [--wide] [--haze-end M] [--surfaces DIR]
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
rng = random.Random(seed * 31 + chapter)

# ---------------------------------------------------------------- the chapter's light (sRGB)
MOODS = {
    1: dict(sun=(1, .97, .92), zenith=(.16, .39, .75), horizon=(.52, .73, .92), glow=(1, .97, .9), shade=(.52, .56, .66),
            haze=(.68, .78, .88), sun_dir=(.45, .78, -.45), haze_start=40, haze_end=700, haze_k=.6),
    2: dict(sun=(1, .97, .92), zenith=(.16, .39, .75), horizon=(.53, .73, .92), glow=(1, .97, .9), shade=(.52, .56, .66),
            haze=(.68, .78, .88), sun_dir=(.4, .85, -.35), haze_start=40, haze_end=700, haze_k=.58),
    3: dict(sun=(1, .98, .94), zenith=(.14, .39, .76), horizon=(.48, .74, .93), glow=(1, .97, .9), shade=(.54, .58, .68),
            haze=(.66, .8, .9), sun_dir=(.5, .75, -.45), haze_start=45, haze_end=760, haze_k=.55),
    4: dict(sun=(1, .97, .93), zenith=(.18, .4, .74), horizon=(.56, .74, .9), glow=(1, .97, .91), shade=(.52, .55, .64),
            haze=(.7, .77, .85), sun_dir=(.5, .75, -.4), haze_start=38, haze_end=640, haze_k=.62),
    5: dict(sun=(1, .96, .9), zenith=(.16, .39, .75), horizon=(.54, .74, .92), glow=(1, .96, .88), shade=(.52, .57, .64),
            haze=(.68, .78, .86), sun_dir=(.55, .7, -.45), haze_start=40, haze_end=700, haze_k=.58),
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


if chapter == 3:
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
SUMMER = [(.38, .5, .25), (.34, .46, .25), (.42, .52, .27), (.3, .43, .25), (.4, .48, .23)]
MEADOW = [(.48, .58, .3), (.52, .6, .32), (.42, .54, .28)]
PALM, HEDGE = (.36, .48, .24), (.27, .4, .22)


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


def plant(model, x, y, z, scale):
    leaves = None
    if model.startswith('Broadleaf') or model == 'Birch' or model.startswith('Bush'):
        leaves = rng.choice(SUMMER)
    elif model.startswith('Palm'):
        leaves = PALM
    elif model in ('TallGrass', 'GrassTuft') and rng.random() < .8:
        leaves = rng.choice(MEADOW)
    place('Plants', model, x, y, z, rng.uniform(0, 360), scale, [leaves, None, None] if leaves else None)


def poles():
    if chapter in (2, 3, 5) or not has('Street', 'UtilityPole'):
        return
    xs = [x for x in np.arange(X0 - 21, X1 + 21, 21.0)]
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
    layer('ForestStrip', X0 - 250, X1 + 250, -0.3, 70, 1.0, 0)
    layer('HillsRolling', X0 - 450, X1 + 450, -0.4, 230, 1.0, 0)
    layer('MountainRange1', X0 - 700, X1 + 700, -0.8, 440, 0.75, 0)
    layer('MountainRange2', X0 - 900, X1 + 900, -0.8, 640, 1.0, 0.5)


# The town's fronts and houses (StreetBuilder.MarketFronts / HomeHouses / FrontPaints / Deck).
MARKET = ['ShopFruit', 'ShopShutter', 'ShopMart', 'ShopCafe', 'ShopBooks', 'ShopFlorist', 'ShopNoodle', 'ShopTall', 'ShopBoutique', 'ShopKonbini']
HOMES = ['HouseGable', 'HouseLong', 'Bungalow', 'HouseLeanTo', 'HouseFlat', 'HouseCarport']
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
                self.left = [m for m in self.models if has('Buildings', m)]
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
    if model in ('HouseGable', 'HouseLong', 'Bungalow') or not has('Buildings', model):
        return False
    place('Buildings', model, x, 0, z, 0, 1, list(paint_for(model, HOUSE, x, z)))
    return True


def suburb():
    houses = Deck(HOMES)
    x = X0
    while x < X1:
        lot = rng.uniform(9, 13); cx = x + lot / 2
        gate = rng.uniform(x + 2, x + lot - 4)
        picket = rng.random() < .3 and has('Street', 'PicketFence2')
        if picket:
            row('Street', 'PicketFence2', x + .1, gate, 0, PROP + .15); row('Street', 'PicketFence2', gate + 1.4, x + lot - .1, 0, PROP + .15)
        else:
            for a, b, pa, pb in ((x + .1, gate, True, True), (gate + 2.2, x + lot - .1, True, False)):
                if b - a >= .4 and row('Street', 'BlockWall2', a, b, 0, PROP + .15):
                    if pa: place('Street', 'WallPillar', a, 0, PROP + .15)
                    if pb: place('Street', 'WallPillar', b, 0, PROP + .15)
        life = rng.random()
        if life < .12: place('Street', 'PostBox', x + rng.uniform(1, lot - 1), 0, POLE_Z - .1)
        elif life < .3 and not picket and gate - x > 3.4:
            place('Street', 'Bicycle', rng.uniform(x + 1.2, gate - 1), 0, PROP - .32, 180 + rng.uniform(-6, 6), 1, [rng.choice(BIKES), None, None])
        house = houses.next(lambda m: size('Buildings', m).x <= lot - .8)
        kind = rng.randrange(3)
        z = PROP + 1.6 + rng.uniform(0, 1.4) + (.3 if house == 'HouseLeanTo' else 0)
        model = 'HouseGable' if kind == 0 else 'HouseLong' if kind == 1 and lot >= 11 else 'Bungalow'
        if house in ('HouseGable', 'HouseLong', 'Bungalow'): model = house
        town = house is not None and town_house(house, cx, z)
        if town: model = house
        else: building(model, cx, z, HOUSE)
        half = (size('Buildings', model).x if town else WIDTH[model]) / 2
        if has('Street', 'BinPair'):
            d = rng.random()
            if d < .3 and not picket:
                place('Street', 'BinPair', gate + 1.1, 0, PROP + .55, rng.uniform(-10, 10), 1, [rng.choice(BINS), rng.choice(BINS), None])
            elif d < .55:
                place('Street', 'PotGroup', gate + .55, 0, PROP + .6, rng.uniform(-20, 20), 1, [rng.choice(PETALS), None, None])
        yard = x + lot - (cx + half)
        if not picket and yard > 1.2 and rng.random() < .6 and has('Plants', 'BushRound'):
            plant(rng.choice(['BushRound', 'ShrubFlowering']), x + lot - yard / 2, 0, PROP + 1.35, rng.uniform(1.3, 1.6))
        if house == 'HouseCarport' and town and rng.random() < .8:
            place('Street', 'Bicycle', cx + 3.4, 0, z + 1.3, 180 + rng.uniform(-5, 5), 1, [rng.choice(BIKES), None, None])
        if rng.random() < .7:
            plant(rng.choice(['Broadleaf', 'BroadleafLarge', 'ConiferTall', 'Broadleaf', 'Birch']), cx + rng.uniform(-half, half), 0, z + 8 + rng.uniform(0, 3), rng.uniform(.9, 1.25))
        gap = (cx - half) - x
        if gap > 4 and house != 'HouseCarport' and rng.random() < .4 and has('Buildings', 'Garage'):
            p = HOUSE[scramble(abs(int(round(cx * 7 + z * 13))) + 1) % len(HOUSE)]
            place('Buildings', 'Garage', x + gap / 2, 0, z + .8, 0, 1, list(p))
        elif gap > 1.8 and rng.random() < .6:
            m = rng.choice(['Birch', 'ConiferSmall', 'ConiferMid', 'ShrubFlowering'])
            plant(m, x + gap / 2, 0, PROP + 1.4 + rng.uniform(0, 1.2), rng.uniform(1.3, 1.6) if m == 'ShrubFlowering' else rng.uniform(.7, .95))
        x += lot
    back = Deck(['HouseGable', 'HouseLong', 'HouseLeanTo', 'HouseFlat'])
    x = X0 - 20
    while x < X1 + 20:
        house = back.next()
        bz = rng.uniform(20, 24)
        if not town_house(house, x, bz):
            building(house if house in ('HouseGable', 'HouseLong') else rng.choice(['HouseGable', 'HouseLong']), x, bz, HOUSE)
        x += rng.uniform(10, 14)
    distant((.44, .54, .32), None)


def market():
    deck = Deck(MARKET)
    vended = False
    x, i = X0, 0
    while x < X1:
        front = deck.next()
        w = size('Buildings', front).x if front else 8
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
            place('Street', 'VendingRed', x + .7, 0, PROP + .2); place('Street', 'VendingBlue', x + 1.75, 0, PROP + .2)
            x += 2.6
        i += 1
    x = X0 - 20
    while x < X1 + 20:
        building('Apartment', x, rng.uniform(22, 28), HOUSE)
        x += rng.uniform(13, 16)


def beach():
    g = SAND.height
    towers = []
    x = X0
    while x < X1:
        place('Leisure', 'LifeguardTower', x, g(x, 7.4), 7.4); towers.append(x)
        x += rng.uniform(30, 45)
    canopy = [(.9, .3, .28), (.25, .5, .85), (1, .75, .2), (.3, .66, .62)]
    towels = [(.95, .55, .6), (.45, .75, .9), (1, .85, .35), (.55, .8, .55)]
    x = X0 + 8
    while x < X1:
        z = rng.uniform(3.4, 5.2)
        if any(abs(t - x) < 3 for t in towers):
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
        place('Terrain', 'RockCluster', x, g(x, rz) - .15, rz, rng.uniform(-30, 30), s_ * .8)
        if rng.random() < .5:
            place('Terrain', rng.choice(['Boulder1', 'Boulder2']), bx, g(bx, bz) - .1, bz, rng.uniform(0, 360), rng.uniform(.7, 1.1))
        x += rng.uniform(12, 24)
    x = X0 + rng.uniform(5, 15)
    while x < X1:
        for k in range(rng.randrange(1, 4)):
            px, pz = x + k * rng.uniform(2.2, 3.4), rng.uniform(5.6, 7)
            if any(abs(t - px) < 4.5 for t in towers): continue
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
        plant(rng.choice(['BroadleafLarge', 'Broadleaf', 'ConiferTall', 'BroadleafLarge', 'ConiferMid', 'Birch']), x, .04, rng.uniform(22, 40), rng.uniform(.95, 1.35))
        x += rng.uniform(3, 6)
    x = X0
    while x < X1:
        plant(rng.choice(['TallGrass', 'GrassTuft', 'FlowerPatch', 'GrassTuft', 'TallGrass']), x, .08, rng.uniform(-6.5, -2.4), rng.uniform(1.1, 1.8))
        x += rng.uniform(.8, 2.6)
    distant((.44, .54, .32), None)


{1: suburb, 2: market, 3: beach, 4: city, 5: park}[chapter]()
poles()

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
    t.links.new(k.outputs[0], mix.inputs['Fac'])
    t.links.new(shader, mix.inputs[1]); t.links.new(em.outputs['Emission'], mix.inputs[2])
    t.links.new(mix.outputs['Shader'], outn.inputs['Surface'])

S.render.filepath = out
bpy.ops.render.render(write_still=True)
print('preview', out, len(placed), 'models placed')
