# The asset review's renders (docs/ASSET_REVIEW.md): every asset in eight views on one sheet, and each of its motions
# as an animated GIF. Used by the kits (kit_animals_km.py --review). Both render many posed copies of the model in one
# frame (linked duplicates, sharing the mesh), so a whole sheet or a whole motion is one render.
#
# The model's frame (the kits' contract): an animal's head +X, its right flank toward -Y (the game camera's side), up +Z;
# a building's or prop's street side -Y. The review camera looks along +Y from -Y; each copy is turned so the side asked
# for faces it.
import math
import os

import bpy
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = math.radians


def _rot(*steps):
    """A rotation from steps applied in order: ('X'|'Z', degrees)."""
    m = Matrix.Identity(3)
    for axis, deg in steps:
        m = Matrix.Rotation(R(deg), 3, axis) @ m
    return m


# (label, rotation that turns that side toward the camera)
VIEWS = [
    ('Front', _rot(('Z', -90))),
    ('Back', _rot(('Z', 90))),
    ('Left', _rot(('Z', 180))),
    ('Right (game view)', _rot()),
    ('Left 3/4', _rot(('Z', -135), ('X', 20))),
    ('Right 3/4', _rot(('Z', -45), ('X', 20))),
    ('Top', _rot(('X', 90))),
    ('Bottom', _rot(('X', -90))),
]


def meshes_of(root):
    return [o for o in root.children_recursive if o.type == 'MESH']


def local_points(root):
    """Every vertex in the root's own frame."""
    inv = root.matrix_world.inverted()
    return [inv @ (o.matrix_world @ v.co) for o in meshes_of(root) for v in o.data.vertices]


def copy_of(root, name):
    """A linked duplicate of root's hierarchy (the meshes shared): {part name: object}, and the new root."""
    new_root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(new_root)
    parts = {}

    def walk(src, dst_parent):
        for c in src.children:
            d = c.copy()
            bpy.context.scene.collection.objects.link(d)
            d.parent = dst_parent
            d.matrix_parent_inverse = c.matrix_parent_inverse.copy()
            d.location, d.rotation_euler, d.scale = c.location.copy(), c.rotation_euler.copy(), c.scale.copy()
            parts[c.name.split('.', 1)[1] if '.' in c.name else c.name] = d
            walk(c, d)

    walk(root, new_root)
    return new_root, parts


def remove(objs):
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)


def _grid_render(posed, cols, rows, cell, path, size, render):
    """Lay out [(root copy, rotation 3x3, local centre)] in a cols x rows grid of square cells, render it once."""
    for i, (root, rot, centre) in enumerate(posed):
        c, r = i % cols, i // cols
        target = Vector(((c - (cols - 1) / 2) * cell, 0.0, ((rows - 1) / 2 - r) * cell))
        root.matrix_world = Matrix.Translation(target - rot @ centre) @ rot.to_4x4()
    bpy.context.view_layer.update()
    names = {o.name for root, _, _ in posed for o in root.children_recursive if o.type == 'MESH'}
    return render(path, (0, -50, 0), (0, 0, 0), ortho=cols * cell, size=size, only=names)


def eight_views(root, path, render, cell_px=400, title=None):
    """The asset from all eight sides on one sheet (4 x 2), each labelled. render: the kit's render function."""
    pts = local_points(root)
    lo = Vector([min(p[k] for p in pts) for k in range(3)])
    hi = Vector([max(p[k] for p in pts) for k in range(3)])
    centre = (lo + hi) / 2
    ext = 0.0
    for _, rot in VIEWS:
        q = [rot @ (p - centre) for p in pts]
        ext = max(ext, max(v.x for v in q) - min(v.x for v in q), max(v.z for v in q) - min(v.z for v in q))
    cell = ext * 1.12
    posed = []
    for label, rot in VIEWS:
        c, _ = copy_of(root, root.name + '.view')
        posed.append((c, rot, centre))
    im = _grid_render(posed, 4, 2, cell, path + '.png', (4 * cell_px, 2 * cell_px), render)
    os.remove(path + '.png')
    remove([o for c, _, _ in posed for o in [c] + list(c.children_recursive)])
    head = 44 if title else 0
    out = Image.new('RGB', (im.width, im.height + head), (36, 36, 42))
    out.paste(im, (0, head))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype(FONT, 22)
    if title:
        d.text((10, 10), title, font=ImageFont.truetype(FONT, 26), fill=(240, 240, 245))
    for i, (label, _) in enumerate(VIEWS):
        x, y = (i % 4) * cell_px, head + (i // 4) * cell_px
        d.rectangle([x, y, x + cell_px - 1, y + cell_px - 1], outline=(70, 70, 80), width=2)
        d.text((x + 8, y + 6), label, font=f, fill=(25, 25, 30), stroke_width=3, stroke_fill=(235, 235, 240))
    out.save(path, quality=82)
    return out


def motion_gif(root, pose, path, render, view=None, frames=12, cell_px=300, ms=80, label=None):
    """One motion as an animated GIF: frames copies of the model, each posed by pose(parts, root_copy, phase 0..1)
    (it sets the parts' rotation_euler and returns (lift metres, pitch degrees[, yaw degrees]) for the whole body),
    rendered once in a
    4-column grid and cut into frames. view: the rotation to show it from (default: the game view, a little above)."""
    view = view if view is not None else _rot(('X', 10))
    pts = local_points(root)
    lo = Vector([min(p[k] for p in pts) for k in range(3)])
    hi = Vector([max(p[k] for p in pts) for k in range(3)])
    centre = (lo + hi) / 2
    q = [view @ (p - centre) for p in pts]
    ext = max(max(v.x for v in q) - min(v.x for v in q), max(v.z for v in q) - min(v.z for v in q))
    cell = ext * 1.45
    cols, rows = 4, (frames + 3) // 4
    posed = []
    for i in range(frames):
        c, parts = copy_of(root, root.name + '.motion')
        moved = pose(parts, c, i / frames)
        lift, pitch, yaw = moved if len(moved) == 3 else (moved[0], moved[1], 0.0)
        # the whole body's turn is composed with the view here (the grid sets each copy's whole transform)
        rot = view @ Matrix.Rotation(R(yaw), 3, 'Z') @ Matrix.Rotation(R(pitch), 3, 'Y')
        posed.append((c, rot, centre - Vector((0, 0, lift))))
    im = _grid_render(posed, cols, rows, cell, path + '.png', (cols * cell_px, rows * cell_px), render)
    remove([o for c, _, _ in posed for o in [c] + list(c.children_recursive)])
    imgs = []
    f = ImageFont.truetype(FONT, 18)
    for i in range(frames):
        x, y = (i % cols) * cell_px, (i // cols) * cell_px
        fr = im.crop((x, y, x + cell_px, y + cell_px)).convert('RGB')
        if label:
            ImageDraw.Draw(fr).text((6, 4), label, font=f, fill=(25, 25, 30), stroke_width=3, stroke_fill=(235, 235, 240))
        imgs.append(fr.convert('P', palette=Image.ADAPTIVE, colors=128))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=ms, loop=0, optimize=True)
    os.remove(path + '.png')
    return imgs


# ------------------------------------------------------------------ the motions, as the game's behaviours move the parts

def _set(parts, name, x=0.0, y=0.0, z=0.0):
    if name in parts:
        parts[name].rotation_euler = (R(x), R(y), R(z))


def walk(height, run=False):
    """A walk (or a run): the legs swing about their hips and shoulders in diagonal pairs, as Hazards/Dog swings them
    (front-right with back-left, front-left with back-right), the tail sways, the head nods, the body bobs."""
    leg, bob, sway = (28, 0.05, 14) if run else (16, 0.018, 9)      # Hazards/Dog swings 28 degrees at a full run

    def pose(parts, root, p):
        a = 2 * math.pi * p
        _set(parts, 'LegFL', y=leg * math.sin(a))
        _set(parts, 'LegBR', y=leg * math.sin(a))
        _set(parts, 'LegFR', y=-leg * math.sin(a))
        _set(parts, 'LegBL', y=-leg * math.sin(a))
        _set(parts, 'Tail', y=sway * 0.5 * math.sin(a), z=sway * math.sin(a))
        _set(parts, 'Head', y=4 * math.sin(2 * a))
        return bob * height * abs(math.sin(a)), (3 if run else 1) * math.sin(2 * a)
    return pose


def hop(height):
    """A bird on the ground: a hop forward, the head bobbing."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        _set(parts, 'Head', y=-12 * math.sin(2 * a))
        return 0.18 * height * max(0.0, math.sin(a)), 0.0
    return pose


def peck(height):
    """A bird pecking: the head goes down and up."""
    def pose(parts, root, p):
        _set(parts, 'Head', y=40 * max(0.0, math.sin(2 * math.pi * p)))
        return 0.0, 0.0
    return pose


def fly(span, beat=40, up_only=False):
    """A wingbeat: the wings rise and fall about the body's long axis, the body rises a little on the downstroke.
    up_only: from flat to beat degrees up and back, never below, as FlitButterfly beats an insect's (38 + 38 sin)."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        w = beat * (0.5 + 0.5 * math.sin(a)) if up_only else beat * math.sin(a)
        _set(parts, 'WingL', x=w)
        _set(parts, 'WingR', x=-w)
        return -0.04 * span * math.sin(a), 0.0
    return pose


def scurry(height):
    """A small animal drawn mid-leap, scurrying: the body bounds and rocks, the tail streams behind."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        _set(parts, 'Tail', y=10 * math.sin(a + 1.2), z=6 * math.sin(a))
        return 0.12 * height * abs(math.sin(a)), 5 * math.sin(a)
    return pose


def swim(length):
    """A fish or a turtle swimming: the body sways side to side."""
    def pose(parts, root, p):
        return 0.0, 0.0, 12 * math.sin(2 * math.pi * p)
    return pose


def idle(height):
    """A sitting or lying animal: its tail swishes, its head turns a little."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        _set(parts, 'Tail', z=18 * math.sin(a), y=6 * math.sin(2 * a))
        _set(parts, 'Head', z=8 * math.sin(a))
        return 0.0, 0.0
    return pose


UP_BELOW = _rot(('Z', -30), ('X', -20))      # a flyer seen from beneath and to the side, as one overhead
UP_ABOVE = _rot(('X', 55))                    # a thing lying flat, seen from in front and above
INSECT = _rot(('Z', -70), ('X', 35))          # an insect, from ahead and to its right, above: both wings in a V
