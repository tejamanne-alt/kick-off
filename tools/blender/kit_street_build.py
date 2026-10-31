# Assembly for the street kit: a Model collects bmesh pieces; build_object() joins them into one
# mesh with smooth area-weighted normals, then bakes per-corner vertex colours (the material's
# colour times soft shading: darker low down and in crevices, lighter on top), atlas UVs (UV0) and
# the recolour part (UV2.x). Palette values are sRGB, as stored in the FBX and in Unity.
import bpy, bmesh, math, zlib
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import kit_lib as K
from kit_street_geo import MATS, new_bm, merge, lay
from kit_street_atlas import reg_uv, WHITE_UV, SIDE_TOP, TOP0, TOP1

# ---------------------------------------------------------------- palette (sRGB)
PAL = {
    'concrete': (0.78, 0.76, 0.72), 'concrete_l': (0.86, 0.84, 0.80), 'concrete_d': (0.60, 0.58, 0.55),
    'pole': (0.77, 0.76, 0.73), 'stone': (0.74, 0.72, 0.68),
    'steel': (0.56, 0.57, 0.58), 'steel_d': (0.31, 0.32, 0.34), 'galv': (0.71, 0.72, 0.71),
    'iron': (0.44, 0.43, 0.42), 'black': (0.17, 0.17, 0.18), 'rubber': (0.20, 0.20, 0.21),
    'porcelain': (0.93, 0.91, 0.86), 'trans': (0.60, 0.65, 0.63), 'lampgreen': (0.31, 0.42, 0.38),
    'housing': (0.26, 0.27, 0.29), 'signalgrey': (0.57, 0.59, 0.60),
    'yellow': (0.93, 0.74, 0.26), 'orange': (0.92, 0.48, 0.24), 'red': (0.78, 0.25, 0.21),
    'white': (0.93, 0.92, 0.88), 'cream': (0.95, 0.91, 0.81), 'decal': (1.0, 1.0, 1.0),
    'wood': (0.77, 0.59, 0.41), 'wood_d': (0.58, 0.43, 0.30), 'wood_g': (0.76, 0.67, 0.53),
    'soil': (0.42, 0.32, 0.24), 'leaf': (0.43, 0.62, 0.33), 'leaf_d': (0.31, 0.50, 0.29),
    'leaf_l': (0.58, 0.73, 0.37), 'stem': (0.40, 0.55, 0.30), 'bark': (0.50, 0.40, 0.31),
    'terracotta': (0.80, 0.48, 0.33), 'glass': (0.32, 0.40, 0.44), 'lampglow': (1.0, 0.96, 0.84),
    'burlap': (0.79, 0.67, 0.49), 'twine': (0.66, 0.55, 0.38), 'canvas': (0.95, 0.92, 0.84),
    'apple': (0.83, 0.26, 0.21), 'orangef': (0.95, 0.59, 0.22), 'lemon': (0.96, 0.84, 0.34),
    'greenf': (0.62, 0.77, 0.34), 'cabbage': (0.60, 0.77, 0.44), 'aubergine': (0.42, 0.27, 0.44),
    'tomato': (0.87, 0.32, 0.23), 'carrot': (0.93, 0.53, 0.22),
    'petal_w': (0.97, 0.96, 0.92), 'petal_v': (0.66, 0.54, 0.80), 'petal_y': (0.98, 0.84, 0.40),
    'chrome': (0.80, 0.81, 0.82), 'saddle': (0.30, 0.24, 0.21), 'brass': (0.80, 0.66, 0.36),
    'blue': (0.30, 0.49, 0.73), 'green': (0.38, 0.60, 0.42), 'amber': (0.55, 0.33, 0.17),
    'cap': (0.88, 0.84, 0.76), 'ac': (0.90, 0.89, 0.85), 'insul': (0.86, 0.84, 0.78),
    'meter': (0.80, 0.80, 0.77), 'gaspipe': (0.90, 0.74, 0.30), 'dish': (0.90, 0.89, 0.86),
    'chalkframe': (0.62, 0.46, 0.32), 'darkwood': (0.46, 0.34, 0.25), 'amberlens': (0.98, 0.68, 0.26), 'flowerc': (0.86, 0.58, 0.26),
}
# The grime map each material samples when its piece doesn't set UVs (None: the white corner).
MODE = {
    'concrete': 'conc', 'concrete_l': 'conc', 'concrete_d': 'conc', 'pole': 'conc', 'stone': 'conc',
    'terracotta': 'conc', 'paintc': 'conc',
    'steel': 'paint', 'steel_d': 'paint', 'galv': 'paint', 'iron': 'paint', 'trans': 'paint',
    'lampgreen': 'paint', 'housing': 'paint', 'signalgrey': 'paint', 'yellow': 'paint', 'red': 'paint',
    'white': 'paint', 'cream': 'paint', 'paint': 'paint', 'ac': 'paint', 'meter': 'paint',
    'gaspipe': 'paint', 'dish': 'paint', 'blue': 'paint', 'green': 'paint',
    'orange': 'plastic', 'rubber': 'plastic', 'black': 'plastic', 'paintp': 'plastic', 'insul': 'plastic',
    'paint2p': 'plastic',
}
NOSHADE = {'lampglow'}


def part_of(mat):
    if mat.startswith('paint2'): return 2
    if mat.startswith('paint'): return 1
    return 0


def lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


def ss(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0); return t * t * (3 - 2 * t)


class Model:
    """name, the main paint (part 1) and secondary (part 2) colours, tile period along X (or None),
    mount 'ground' (origin at the base centre) or 'wall' (origin at the back centre, the wall at y = 0)."""
    def __init__(self, name, paint=None, paint2=None, tile=None, mount='ground', note=None):
        self.name = name; self.pieces = []; self.paint = paint; self.paint2 = paint2
        self.tile = tile; self.mount = mount; self.attach = {}; self.pal = {}; self.note = note
        self.extra = {}

    def add(self, bm):
        self.pieces.append(bm); return bm

    def at(self, name, loc):
        self.attach[name] = tuple(round(float(c), 4) for c in loc)

    def colour(self, mat):
        if mat in self.pal: return self.pal[mat]
        p = part_of(mat)
        if p == 1: return self.paint
        if p == 2: return self.paint2
        return PAL[mat]


def _dirs(n=40):
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - z * z); a = ga * i
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return out


DIRS = _dirs()


def ambient_occlusion(me, m, lo, hi):
    V = [v.co.copy() for v in me.vertices]
    Pl = [tuple(p.vertices) for p in me.polygons]
    allV = list(V); allP = list(Pl)
    if m.tile:
        for sh in (-m.tile, m.tile):
            base = len(allV)
            allV += [v + Vector((sh, 0, 0)) for v in V]
            allP += [tuple(i + base for i in p) for p in Pl]
    base = len(allV)
    if m.mount == 'ground':
        allV += [Vector((-60, -60, 0)), Vector((60, -60, 0)), Vector((60, 60, 0)), Vector((-60, 60, 0))]
    else:
        allV += [Vector((-60, 0.0, -60)), Vector((60, 0.0, -60)), Vector((60, 0.0, 60)), Vector((-60, 0.0, 60))]
    allP.append((base, base + 1, base + 2, base + 3))
    bvh = BVHTree.FromPolygons(allV, allP)
    D = min(max(0.22 * max(hi - lo), 0.12), 0.55)
    ao = np.ones(len(V), np.float32)
    for i, v in enumerate(me.vertices):
        n = v.normal
        o = v.co + n * 0.004
        occ = 0.0; ws = 0.0
        for d in DIRS:
            c = d.dot(n)
            if c <= 0.05: continue
            ws += c
            loc, nrm, idx, dist = bvh.ray_cast(o, d, D)
            if loc is not None:
                occ += c * (1.0 - dist / D) ** 0.7
        ao[i] = 1.0 - occ / max(ws, 1e-6)
    return ao


def build_object(m):
    bm = new_bm()
    for b in m.pieces: merge(bm, b)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    me = bpy.data.meshes.new(m.name); bm.to_mesh(me); bm.free()
    ob = K.new_obj(m.name, me)
    me.shade_smooth()
    K.activate(ob)
    md = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); md.mode = 'FACE_AREA'; md.weight = 50; md.keep_sharp = False
    bpy.ops.object.modifier_apply(modifier=md.name)
    md = ob.modifiers.new('tri', 'TRIANGULATE'); md.quad_method = 'BEAUTY'; md.ngon_method = 'BEAUTY'
    if hasattr(md, 'keep_custom_normals'): md.keep_custom_normals = True
    bpy.ops.object.modifier_apply(modifier=md.name)
    n = len(me.polygons)
    mats = np.zeros(n, np.int32); me.attributes['mat'].data.foreach_get('value', mats)
    uvks = np.zeros(n, np.int32); me.attributes['uvk'].data.foreach_get('value', uvks)
    co = np.array([v.co[:] for v in me.vertices]) if len(me.vertices) else np.zeros((0, 3))
    lo = Vector(co.min(axis=0)); hi = Vector(co.max(axis=0))
    ao = ambient_occlusion(me, m, lo, hi)
    H = max(hi.z - lo.z, 1e-3); W = hi.x - lo.x; Dp = hi.y - lo.y; Sxy = max(W, Dp, 1e-3)
    off = (zlib.crc32(m.name.encode()) % 1000) / 1000.0 * 0.45
    hz = min(max(0.45 * H, 0.25), 1.2)
    uv = me.uv_layers['UVMap']; part = me.uv_layers.new(name='Part')
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = col; me.color_attributes.render_color_index = 0
    cols = []; uvs = []; parts = []
    used_parts = set()
    for p in me.polygons:
        mname = MATS[mats[p.index]]
        rgb = m.colour(mname)
        pid = part_of(mname); used_parts.add(pid)
        k_uv = uvks[p.index]
        region = MODE.get(mname)
        pn = p.normal
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            v = me.vertices[vi]; c = v.co
            if mname in NOSHADE:
                k = 1.0
            else:
                if m.mount == 'ground':
                    kh = 0.80 + 0.20 * ss(0.0, hz, c.z - max(lo.z, 0.0))
                else:
                    kh = 0.90 + 0.10 * ss(lo.z, hi.z, c.z)
                k = kh * (0.56 + 0.44 * float(ao[vi])) * (1.0 + 0.05 * v.normal.z)
                k = min(k, 1.0)
            cols.extend((rgb[0] * k, rgb[1] * k, rgb[2] * k, 1.0))
            if k_uv == 1:
                uvs.extend(uv.data[li].uv)
            elif k_uv == 2 and region:
                uvs.extend(reg_uv(region, uv.data[li].uv[0], SIDE_TOP * (c.z - lo.z) / H))
            elif region:
                if pn.z > 0.7:
                    s = (c.x - lo.x) / Sxy; t = TOP0 + (TOP1 - TOP0) * (c.y - lo.y) / max(Dp, 1e-3)
                    if m.tile: s = (c.x + m.tile / 2) / m.tile
                    else: s = off + 0.5 * s
                else:
                    side = abs(pn.x) > abs(pn.y)
                    s = ((c.y - lo.y) if side else (c.x - lo.x)) / Sxy
                    if m.tile and not side: s = (c.x + m.tile / 2) / m.tile
                    else: s = off + 0.5 * s
                    t = SIDE_TOP * (c.z - lo.z) / H
                uvs.extend(reg_uv(region, s, t))
            else:
                uvs.extend(WHITE_UV)
            parts.extend((float(pid), 0.0))
    col.data.foreach_set('color_srgb', cols)
    uv.data.foreach_set('uv', uvs); part.data.foreach_set('uv', parts)
    me.attributes.remove(me.attributes['mat']); me.attributes.remove(me.attributes['uvk'])
    for name, loc in m.attach.items():
        K.attach(ob, name, loc)
    K.attach(ob, 'Front', (0, -1, 0))
    parts_out = {}
    if 1 in used_parts and m.paint: parts_out[1] = lin(m.paint)
    if 2 in used_parts and m.paint2: parts_out[2] = lin(m.paint2)
    return ob, parts_out
