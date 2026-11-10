# ToonCharacter's ink outline for the Blender renderers (portrait_teen.py's player cards, review_teen.py, review_poses.py):
# an inverted hull, as a copy of the figure set back from the camera (docs/LEARNINGS.md C20).
#
# The renderers used to put a flipped Solidify on the figure itself. That threw away the figure's own normals, the smoothed
# and face-leaned ones polish_character.py writes and the game shades with, so the cards and reviews showed the scan's raw
# normals: brown patches, a jagged chin. Nor was the hull set back from the camera, as ToonCharacter's _OutlinePush (1.2 cm)
# sets it, so it poked through round every nose and mouth corner as black specks. Here the figure is left as it is; a copy
# of it (its own surface drawn as nothing) carries the Solidify, and is moved back along the camera's view.
import bpy
from mathutils import Matrix, Vector

PUSH = 0.012          # m, as ToonCharacter's _OutlinePush


def make(kid, ink, thickness):
    """The hull of `kid` in the ink material `ink`, `thickness` thick. Returns the hull object and its Solidify (whose
    thickness a renderer may change per shot)."""
    hollow = bpy.data.materials.get('InkHollow')
    if hollow is None:
        hollow = bpy.data.materials.new('InkHollow'); hollow.use_nodes = True
        nt = hollow.node_tree; tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        nt.links.new(tr.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    d = kid.copy(); d.data = kid.data.copy(); d.name = kid.name + 'Ink'
    for c in kid.users_collection: c.objects.link(d)
    d.data.materials.clear(); d.data.materials.append(hollow); d.data.materials.append(ink)
    for p in d.data.polygons: p.material_index = 0
    for m in list(d.modifiers):
        if m.type == 'SOLIDIFY': d.modifiers.remove(m)
    sol = d.modifiers.new('ink', 'SOLIDIFY'); sol.thickness = thickness; sol.offset = 1
    sol.use_flip_normals = True; sol.material_offset = 1
    d.visible_shadow = False
    return d, sol


def set_back(hull, kid, view, push):
    """Moves the hull `push` (in the scene's units) along the camera's view direction `view`, from where `kid` is now.
    Call after posing and turning the figure, just before rendering."""
    bpy.context.view_layer.update()
    hull.matrix_world = Matrix.Translation(Vector(view).normalized() * push) @ kid.matrix_world
