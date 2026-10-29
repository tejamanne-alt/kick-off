# The teens' heads: the head mesh (its front carries the painted face) and the ears.
# Base space: see teen_lib. The face is painted by face_teen.py into the atlas' upper-left
# quadrant through face_uv(): a straight front projection.
import bpy
from mathutils import Vector
from teen_lib import C, Part, bake, finish

# The cranium the hair is fitted to (keep the top and back of the head inside this).
CRANIUM_CENTER = (0, -0.005, 1.425)
CRANIUM_RADII = (0.15, 0.153, 0.162)


def face_uv(co):
    """World (base space) point -> atlas UV: u = x/0.34 + 0.5, v = (z - 1.27)/0.34, upper-left quadrant."""
    u = co.x / 0.34 + 0.5; v = (co.z - 1.27) / 0.34
    return (u * 0.5, 0.5 + v * 0.5)


def build_head(girl, skin):
    parts = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=22, radius=0.15, location=CRANIUM_CENTER)
    head = C.object; head.name = 'Head'
    head.scale = (CRANIUM_RADII[0] / 0.15, CRANIUM_RADII[1] / 0.15, CRANIUM_RADII[2] / 0.15); bake(head)
    for v in head.data.vertices:
        co = v.co
        if co.z < 1.42:   # cheeks and a softly pointed chin
            t = min(1, (1.42 - co.z) / 0.16)
            co.x *= 1 - 0.32 * t * t; co.y = co.y * (1 - 0.18 * t) - 0.012 * t
        if co.y > 0.06: co.y -= 0.015 * min(1, (co.y - 0.06) / 0.08)   # flatter back of the head
    head.modifiers.new('sub', 'SUBSURF').levels = 1
    finish(head)
    parts.append(Part(head, (1, 1, 1, 1), 0, 'Head', uv=face_uv))   # white x the painted atlas
    for s in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(s * 0.142, 0.01, 1.41))
        e = C.object; e.name = 'Ear'; e.scale = (0.45, 0.8, 1.15)
        finish(e); parts.append(Part(e, skin, 0, 'Head'))
    return parts
