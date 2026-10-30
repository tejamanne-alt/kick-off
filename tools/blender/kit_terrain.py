# The TERRAIN asset kit for Dribble To School: original stylized rocks, cliffs, a sea headland,
# distant landscape strips (mountain ranges, rolling hills, a forest band), sand dunes and site
# piles. Read docs/ART_DIRECTION.md first.
#   blenv/bin/python kit_terrain.py -- /abs/outdir
# Writes into outdir: <Model>.fbx (one per model), TerrainAtlas.png, Terrain.json, Terrain.blend.
# Review:  blenv/bin/python review_kit.py -- outdir/Terrain.blend outdir/sheet.png --models A,B
#
# Conventions (kit_lib): metres, Z up, the front faces -Y, origin at the footprint centre on the
# ground; an Attach.Front empty 1 m in front of the origin. One material (vertex colour x atlas).
# Vertex colours carry the colour and the baked soft shading: a warm top light, cool lilac
# undersides, a darker foot, ambient occlusion (ray cast) in crevices and at the ground, and a
# little low-frequency variation. UV0 samples painted detail in the atlas (rock mottling and
# lichen, cliff strata, grass strokes, gullies, field patchwork, sand ripples, pebbles) by
# projecting world positions; flat parts use the white corner.
# Recolour parts (UV2.x): 0 rock and the rest, 1 grass / vegetation, 2 snow, or the sand and
# gravel of dunes and piles. Terrain.json records each model's part base colours (sRGB).
#
# Modules: kit_terrain_geo (chunks, heightfields, cuts, AO), kit_terrain_rocks (boulders, cliffs,
# headland), kit_terrain_land (mountains, hills, forest, dunes, piles), kit_terrain_atlas.
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import kit_lib as K
import kit_terrain_geo as G
import kit_terrain_atlas as A
import kit_terrain_rocks as R
import kit_terrain_land as L

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else os.path.abspath('terrain_out')
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None


# ---------------------------------------------------------------- palette (sRGB in, linear out)
def lin(rgb):
    return tuple((c / 255.0) / 12.92 if c / 255.0 <= 0.04045 else ((c / 255.0 + 0.055) / 1.055) ** 2.4 for c in rgb)


# kind: (underside / shadow, mid (the part base colour), lit top)
PAL = {
    'rock':    (lin((88, 86, 124)), lin((146, 138, 162)), lin((214, 190, 170))),
    'cliff':   (lin((92, 88, 124)), lin((152, 142, 162)), lin((216, 192, 168))),
    'mrock':   (lin((86, 88, 128)), lin((132, 128, 158)), lin((200, 180, 172))),
    'pebble':  (lin((96, 92, 110)), lin((150, 144, 152)), lin((206, 196, 184))),
    'grass':   (lin((60, 100, 74)), lin((108, 146, 72)), lin((160, 182, 92))),
    'meadow':  (lin((74, 108, 82)), lin((122, 150, 82)), lin((172, 186, 100))),
    'hill':    (lin((70, 110, 80)), lin((116, 152, 76)), lin((170, 190, 94))),
    'conifer': (lin((30, 62, 66)), lin((52, 98, 80)), lin((104, 146, 96))),
    'snow':    (lin((160, 164, 210)), lin((218, 220, 236)), lin((240, 234, 226))),
    'sand':    (lin((196, 158, 138)), lin((228, 198, 154)), lin((244, 222, 182))),
    'gravel':  (lin((118, 112, 118)), lin((168, 160, 150)), lin((208, 198, 182))),
    'trunk':   (lin((60, 46, 44)), lin((92, 68, 56)), lin((120, 92, 72))),
    'soil':    (lin((92, 84, 98)), lin((120, 110, 116)), lin((140, 130, 130))),
}
PRIORITY = ('rock', 'cliff', 'mrock', 'pebble', 'trunk', 'soil', 'conifer', 'grass', 'hill', 'meadow',
            'snow', 'sand', 'gravel')
PART = {'rock': 0, 'cliff': 0, 'mrock': 0, 'pebble': 0, 'trunk': 0, 'soil': 0,
        'grass': 1, 'meadow': 1, 'hill': 1, 'conifer': 1,
        'snow': 2, 'sand': 2, 'gravel': 2}
# How strongly each kind takes the warm top colour, its shadow floor and AO strength.
LOOK = {
    'rock': (1.0, 0.44, 1.0), 'cliff': (0.9, 0.44, 1.0), 'mrock': (0.8, 0.5, 0.9), 'pebble': (0.7, 0.5, 0.8),
    'grass': (0.5, 0.5, 0.9), 'meadow': (0.6, 0.55, 0.8), 'hill': (0.6, 0.55, 0.8), 'conifer': (0.7, 0.42, 1.0),
    'snow': (0.7, 0.6, 0.8), 'sand': (0.6, 0.62, 0.75), 'gravel': (0.6, 0.5, 0.9), 'trunk': (0.2, 0.6, 0.6),
    'soil': (0.2, 0.6, 0.6),
}


# How much convex edges and ridges lighten (and hollows darken) each kind.
CAV = {'rock': 0.14, 'cliff': 0.14, 'mrock': 0.3, 'pebble': 0.1, 'grass': 0.12, 'meadow': 0.22, 'hill': 0.26,
       'conifer': 0.12, 'snow': 0.26, 'sand': 0.2, 'gravel': 0.12, 'trunk': 0.0, 'soil': 0.0}


def shade_fn(kind, ctx, vdata, noise):
    low, mid, top = PAL[kind]
    top_amt, floor, ao_k = LOOK[kind]
    cav_k = CAV.get(kind, 0.15)
    nz_k = {'grass': 0.15, 'hill': 0.1, 'meadow': 0.1}.get(kind, 0.07)     # painterly mottling
    top_amt *= ctx.top_amt if ctx.top_amt is not None else 1.0
    z0, z1 = ctx.z0, max(ctx.z1, 1e-3)
    wet = ctx.wet or 0.0
    hard = kind in ('rock', 'cliff', 'mrock', 'pebble')

    def col(co, nf):
        key = (round(co.x, 3), round(co.y, 3), round(co.z, 3))
        nv, ao, cv = vdata.get(key, (nf, 1.0, 0.0))
        n = (nv * 0.6 + nf * 0.4).normalized() if hard else nv
        up = n.z
        c = G.mix3(low, mid, G.sstep(-0.7, 0.3, up))
        c = G.mix3(c, top, G.sstep(0.4, 0.95, up) * top_amt)
        hz = G.sstep(z0, z1, co.z)
        k = 0.8 + 0.24 * hz
        k *= floor + (1 - floor) * (1 - ao_k * (1 - ao))
        k *= 1.0 + nz_k * noise(co.x, co.y, co.z)
        k *= 1.0 - cav_k * max(-1.0, min(1.0, cv * 2.5))
        if wet > 0 and hard:
            w = G.sstep(wet, wet - 0.5, co.z)
            c = G.mix3(c, (c[0] * 0.62, c[1] * 0.66, c[2] * 0.74), w)
        if kind == 'conifer':
            # tips of the fronds a little lighter, the inner shadow cooler
            k *= 0.86 + 0.28 * G.sstep(-0.2, 0.7, up)
        return (c[0] * k, c[1] * k, c[2] * k, 1.0)
    return col


def uv_fn(kind, ctx, lo, hi):
    """World position (and face normal) -> atlas UV for a kind."""
    W = ctx.period
    span = ctx.span or max(hi.x - lo.x, hi.y - lo.y, 1.0)
    cx, cy = (lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5

    def proj(co, n, side_reg, top_reg, sp, zsp=None, topcut=0.6):
        zsp = zsp or sp
        if n.z > topcut:
            return A.reg_uv(top_reg, 0.5 + (co.x - cx) / sp, 0.5 + (co.y - cy) / sp)
        if abs(n.y) >= abs(n.x):
            return A.reg_uv(side_reg, 0.5 + (co.x - cx) / sp, co.z / zsp)
        return A.reg_uv(side_reg, 0.5 + (co.y - cy) / sp, co.z / zsp)

    if kind in ('rock', 'pebble'):
        return lambda co, n: proj(co, n, 'stone', 'stonetop', span)
    if kind == 'cliff':
        sh = ctx.strata_h or span
        return lambda co, n: proj(co, n, 'strata', 'stonetop', span, sh)
    if kind == 'grass':
        sp = ctx.grass_span or max(span, 4.0)
        return lambda co, n: A.reg_uv('grass', 0.5 + (co.x - cx) / sp, 0.5 + (co.y - cy) / sp)
    if kind == 'mrock' and W:
        hm = (ctx.hmax or 90.0) * 1.1
        return lambda co, n: A.reg_uv('mountain', (co.x + W / 2) / W, co.z / hm)
    if kind in ('hill', 'meadow') and W and ctx.depth:
        y0, y1 = ctx.depth
        return lambda co, n: A.reg_uv('fields', (co.x + W / 2) / W, (co.y - y0) / (y1 - y0))
    if kind == 'sand':
        reg = ctx.sand_region or 'sand'
        sp = max(span, 6.0)
        if reg == 'grain':
            return lambda co, n: A.reg_uv('grain', 0.5 + (co.x - cx) / 2.4, 0.5 + (co.y - cy) / 2.4)
        return lambda co, n: A.reg_uv('sand' if n.z > 0.8 else 'grain', 0.5 + (co.x - cx) / sp, 0.5 + (co.y - cy) / sp)
    if kind == 'gravel':
        sp = 2.2
        return lambda co, n: proj(co, n, 'gravel', 'gravel', sp, sp, 0.45)
    return None


# ---------------------------------------------------------------- finalize
def set_normals(o, mode, W=None):
    """Smooth shading; 'weighted' keeps broad planes flat up to their rounded edges (rocks).
    A tiling strip (W) gets custom normals with its seam vertices averaged across the seam."""
    K.finish(o, None)
    if mode == 'weighted':
        m = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.mode = 'FACE_AREA'; m.weight = 50; m.keep_sharp = False
        K.activate(o); bpy.ops.object.modifier_apply(modifier=m.name)
    if W:
        me = o.data
        nv = G.seam_normals(G.vertex_normals(me), [v.co for v in me.vertices], W)
        me.normals_split_custom_set_from_vertices([tuple(n) for n in nv])


def fit(bm, ctx):
    """Scale to the target size (largest dimension) and centre the footprint on the origin
    (not for the tiling strips, whose x range is their period)."""
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    if ctx.fit:
        k = ctx.fit / (max(zs) if ctx.fit_axis == 'z' else max(max(xs) - min(xs), max(ys) - min(ys), max(zs)))
        for v in bm.verts: v.co *= k
        for key in ('z1', 'strata_h'):
            if ctx.get(key): ctx[key] *= k
        xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]
    if not ctx.period:
        dx, dy = (max(xs) + min(xs)) * 0.5, (max(ys) + min(ys)) * 0.5
        for v in bm.verts: v.co.x -= dx; v.co.y -= dy


def finalize(name, bm, ctx, mat, man):
    t0 = time.time()
    fit(bm, ctx)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    if not ctx.period:
        G.fix_normals(bm)
    lk = G.klayer(bm)
    # shading data on the whole model: normals as they will be, AO by ray casts
    me = bpy.data.meshes.new(name + '_shade'); bm.to_mesh(me)
    tmp = K.new_obj(name + '_shade', me)
    W = ctx.period
    set_normals(tmp, ctx.normals, W)
    nv = G.vertex_normals(me)
    shifts = [(W, 0, 0), (-W, 0, 0)] if W else []
    ao = G.bake_ao(me, nv, ctx.ao_radius, rays=ctx.ao_rays or 40, shifts=shifts)
    cav = G.cavity(bm, nv, W)
    vdata = {(round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3)): (nv[i], ao[i], cav[i]) for i, v in enumerate(me.vertices)}
    lo = Vector((min(v.co.x for v in me.vertices), min(v.co.y for v in me.vertices), min(v.co.z for v in me.vertices)))
    hi = Vector((max(v.co.x for v in me.vertices), max(v.co.y for v in me.vertices), max(v.co.z for v in me.vertices)))
    bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me)
    noise = G.Waves(ctx.seed or 1, ctx.noise_scale or 5.0, 3, W=W)
    # one object per kind, coloured with kit_lib.colorize, then joined back together
    kinds = sorted({f[lk] for f in bm.faces})
    objs = []
    present = [G.KINDS[k] for k in kinds]
    parts = {}
    for kind in PRIORITY:            # each part's base colour: its leading kind's mid colour
        if kind in present and PART[kind] not in parts:
            parts[PART[kind]] = (kind, PAL[kind][1])
    for kid in kinds:
        kind = G.KINDS[kid]
        b2 = bm.copy(); l2 = G.klayer(b2)
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f[l2] != kid], context='FACES')
        m2 = bpy.data.meshes.new(name + '_' + kind); b2.to_mesh(m2); b2.free()
        o = K.new_obj(name + '_' + kind, m2)
        K.colorize(o, shade_fn(kind, ctx, vdata, noise), part=PART[kind], uv=uv_fn(kind, ctx, lo, hi))
        objs.append(o)
    bm.free()
    root = K.join(objs, name)
    b3 = bmesh.new(); b3.from_mesh(root.data)
    bmesh.ops.remove_doubles(b3, verts=b3.verts[:], dist=1e-5)
    b3.to_mesh(root.data); b3.free()
    set_normals(root, ctx.normals, W)
    root.data.color_attributes.active_color = root.data.color_attributes[0]
    K.assign(root, mat)
    K.attach(root, 'Front', (0, -1, 0))
    tris = K.tris(root)
    extra = {'category': ctx.category, 'budget': ctx.budget,
             'partKinds': {str(p): k for p, (k, _) in sorted(parts.items())}}
    for k in ('tileWidth', 'notes', 'trees'):
        if ctx.get(k) is not None: extra[k] = ctx[k]
    man.add(root, parts={p: c for p, (k, c) in sorted(parts.items())}, **extra)
    K.export_model(root, os.path.join(OUT, name + '.fbx'))
    flag = '' if tris <= (ctx.budget or 1e9) else '  OVER BUDGET'
    print('MODEL %-15s %5d tris  %s  %.1fs%s' % (name, tris, man.data['models'][name]['size'], time.time() - t0, flag))
    return root


MODELS = [
    ('Boulder1', R.boulder1), ('Boulder2', R.boulder2), ('Boulder3', R.boulder3), ('Boulder4', R.boulder4),
    ('BoulderLarge1', R.boulder_large1), ('BoulderLarge2', R.boulder_large2), ('SteppingStone', R.stepping_stone),
    ('RockCluster', R.rock_cluster), ('CliffChunk1', R.cliff_chunk1), ('CliffChunk2', R.cliff_chunk2),
    ('Headland', R.headland), ('MountainRange1', L.mountain_range1), ('MountainRange2', L.mountain_range2),
    ('HillsRolling', L.hills_rolling), ('ForestStrip', L.forest_strip), ('SandDune1', L.sand_dune1),
    ('SandDune2', L.sand_dune2), ('SandPile', L.sand_pile), ('GravelPile', L.gravel_pile),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = os.path.join(OUT, 'TerrainAtlas.png')
    A.paint(atlas)
    mat = K.material('Terrain', atlas)
    man = K.Manifest('Terrain', 'TerrainAtlas.png')
    man.data['parts'] = {'0': 'rock and the rest (fixed)', '1': 'grass and vegetation', '2': 'snow, or the sand / gravel of dunes and piles'}
    for name, build in MODELS:
        if ONLY and name not in ONLY: continue
        bm, ctx = build()
        finalize(name, bm, ctx, mat, man)
    man.save(os.path.join(OUT, 'Terrain.json'))
    bpy.context.preferences.filepaths.save_version = 0      # no Terrain.blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Terrain.blend'))
    print('wrote', OUT)


main()
