# Shared helpers for the teen character modules (teen.py builds a character from them).
#
# Coordinates are Blender's: metres, Z up, the character faces -Y, feet at z = 0, the
# character's own left is +X. Everything is built in "base space" (a younger, shorter body);
# teen_body.grow() then stretches the legs and torso to teen proportions. Above the neck
# (z > 1.24) grow() only lifts things, so heads and hair keep their shape.
#
# Each module returns a list of Part records; teen.py colours them, rigs them and joins them
# into one skinned mesh with one material (vertex colours times the face atlas).
import bpy, bmesh, math
from mathutils import Vector, Matrix

C = bpy.context
WHITE_UV = (0.97, 0.03)      # the plain white corner of the atlas


class Part:
    """One piece of the character.

    obj    the Blender mesh object (transforms applied: mesh coordinates are world coordinates)
    color  an RGBA tuple, or fn(co, face_center) -> RGBA, evaluated per face corner (world coords)
    part   outfit part id for the game's recolouring (UV2.x): 0 skin and fixed parts,
           1 shirt/blouse/dress top, 2 legwear (trousers, shorts, skirt), 3 hair;
           an int or fn(co, face_center) -> int
    bind   'transfer' to copy the body's bone weights (clothes that bend with the body), or a
           bone name to follow that bone rigidly ('Head', 'Hips', 'Foot.L', 'Bag', ...)
    uv     None for the white swatch, or fn(co) -> (u, v) into the atlas (the face)
    """
    def __init__(self, obj, color, part=0, bind='transfer', uv=None):
        self.obj, self.color, self.part, self.bind, self.uv = obj, color, part, bind, uv


def new_obj(name, me):
    o = bpy.data.objects.new(name, me); C.scene.collection.objects.link(o); return o


def activate(o):
    for x in C.scene.objects: x.select_set(False)
    o.select_set(True); C.view_layer.objects.active = o


def apply_mods(o):
    """Apply the object's transform (so mesh coordinates are world coordinates) and its modifiers."""
    activate(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)


def bake(o):
    activate(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def smooth(o):
    activate(o); bpy.ops.object.shade_smooth()


def finish(o):
    """Apply transform and modifiers, then smooth-shade (curves are converted to meshes first)."""
    if o.type == 'CURVE':
        activate(o); bpy.ops.object.convert(target='MESH')
    apply_mods(o); smooth(o)
    return o


def shell(src, name, keep, offset, flare_fn=None):
    """A copy of src's faces whose centres pass keep(center), pushed out along the normals by
    offset (+ flare_fn(co)): clothes cut from the body."""
    o = src.copy(); o.data = src.data.copy(); o.name = name; C.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    dele = [f for f in bm.faces if not keep(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bm.normal_update()
    for v in bm.verts:
        d = offset + (flare_fn(v.co) if flare_fn else 0)
        v.co += v.normal * d
    bm.to_mesh(o.data); bm.free()
    return o


def shade(rgba, k):
    """rgba darkened (k < 1) or lightened (k > 1)."""
    return tuple(min(1.0, x * k) for x in rgba[:3]) + (1,)
