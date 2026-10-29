# The teens' hair (outfit part 3, follows the Head bone). Base space: see teen_lib; fitted to
# teen_head's cranium.
import bpy, bmesh, math
from mathutils import Vector
from teen_lib import C, Part, bake, finish
from teen_head import CRANIUM_CENTER

R = math.radians


def hair_colors(girl):
    """Base colour and shine colour. The base colour is the game's default hair colour."""
    return ((0.5, 0.22, 0.14, 1), (0.72, 0.4, 0.28, 1)) if girl else ((0.09, 0.065, 0.07, 1), (0.24, 0.2, 0.22, 1))


def build_hair(girl):
    base, shine = hair_colors(girl)
    def col(co, c):
        d = co - Vector((0, 0, 1.44))
        lit = 0.42 < d.normalized().z < 0.6 and d.y > -0.05 and d.length < 0.2
        return shine if lit else base
    objs = []
    cx, cy, cz = CRANIUM_CENTER
    bpy.ops.mesh.primitive_uv_sphere_add(segments=30, ring_count=20, radius=0.162, location=(0, 0.0, 1.44)); cap = C.object; cap.scale = (1.04, 1.06, 1.07); bake(cap)
    bm = bmesh.new(); bm.from_mesh(cap.data)
    def keep_cap(c):
        d = (c - Vector((0, 0, 1.44))).normalized()
        front = max(0, -d.y)
        thr = (0.3 if girl else 0.36) - 1.1 * (1 - front) ** 1.3 * 0.9
        return d.z > thr
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep_cap(f.calc_center_median())], context='FACES'); bm.to_mesh(cap.data); bm.free()
    s = cap.modifiers.new('solid', 'SOLIDIFY'); s.thickness = 0.012; s.offset = 1
    objs.append(cap)

    def lock(loc, scale, rot, wave=0.0, point=0.75):
        """A clump of hair: a stretched sphere tapering to a point at its lower end, optionally wavy."""
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=10, radius=1, location=loc, rotation=rot); o = C.object; o.scale = scale
        for v in o.data.vertices:
            if v.co.z < 0: v.co.x *= 1 + v.co.z * point; v.co.y *= 1 + v.co.z * point
            if wave: v.co.x += wave * math.sin(v.co.z * 4.5)
        objs.append(o); return o

    if girl:
        for s in (1, -1):
            lock((s * 0.055, -0.142, 1.53), (0.06, 0.024, 0.06), (R(-25), R(s * 25), R(s * 35)))
            lock((s * 0.105, -0.11, 1.49), (0.04, 0.024, 0.08), (R(-15), R(s * 40), R(s * 20)))
        for i in range(11):
            a = R(-75 + i * 15)
            x = math.sin(a) * 0.155; y = math.cos(a) * 0.12 + 0.02
            lock((x * 1.08, y, 1.3), (0.05, 0.042, 0.2), (R(18) * math.cos(a), -math.sin(a) * R(18), 0), wave=0.12, point=0.5)
            lock((x * 1.25, y * 1.1, 1.16), (0.04, 0.035, 0.07), (R(10), 0, (1 if x > 0 else -1) * R(40)), wave=0, point=0.6)
        for s in (1, -1):
            lock((s * 0.14, -0.06, 1.33), (0.035, 0.03, 0.17), (R(-5), 0, R(s * 6)), wave=0.1, point=0.6)
    else:
        for i, x in enumerate([-0.1, -0.055, -0.01, 0.035, 0.08]):
            lock((x, -0.145 + abs(x) * 0.3, 1.535 - abs(x + 0.02) * 0.25), (0.05, 0.026, 0.072), (R(-22), R(x * 100), R(-12 + i * 4)), point=0.7)
        for s in (1, -1):
            lock((s * 0.152, -0.03, 1.43), (0.03, 0.045, 0.07), (0, R(s * 10), R(s * 8)), point=1.0)
            lock((s * 0.13, 0.06, 1.4), (0.045, 0.045, 0.08), (R(20), 0, R(s * 15)), point=1.0)
        for i, (x, y) in enumerate([(-0.05, 0.06), (0.03, 0.08), (0.07, 0.0), (-0.08, -0.02)]):
            lock((x, y, 1.6), (0.035, 0.03, 0.07), (R(-160 + i * 15), R(x * 200), 0), point=1.0)
        for x in (-0.06, 0.0, 0.06):
            lock((x, 0.14, 1.37), (0.04, 0.03, 0.07), (R(25), 0, R(x * 150)), point=1.0)
    return [Part(finish(o), col, 3, 'Head') for o in objs]
