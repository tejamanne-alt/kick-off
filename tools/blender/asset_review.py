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


class Bone:
    """A skinned model's bone with what the motions use of a part object (D21): rotation_euler (in its rest frame, which
    is the model's own: every bone points along +Y with no roll), location (its pivot's offset from its parent's, as a
    part's was), matrix_world (at its pivot), type ('MESH' if it moves skin, 'EMPTY' if it only marks a point)."""

    def __init__(self, rig, pb):
        self.rig, self.pb, self.name = rig, pb, pb.name
        b = pb.bone
        self._rest = (b.head_local - b.parent.head_local) if b.parent else b.head_local.copy()
        self.type = 'MESH' if b.use_deform else 'EMPTY'

    @property
    def rotation_euler(self):
        return self.pb.rotation_euler

    @rotation_euler.setter
    def rotation_euler(self, value):
        self.pb.rotation_euler = value

    @property
    def location(self):
        return self._rest + self.pb.location

    @location.setter
    def location(self, value):
        self.pb.location = Vector(value) - self._rest

    @property
    def matrix_world(self):
        return self.rig.matrix_world @ self.pb.matrix


def copy_of(root, name):
    """A linked duplicate of root's hierarchy (the meshes shared): {part name: object}, and the new root. A skinned
    model's root is its armature: the copy shares the skeleton and the skin's mesh but has its own pose, and its parts
    are its bones (Bone)."""
    if root.type == 'ARMATURE':
        new_root = root.copy()
        new_root.name = name
        bpy.context.scene.collection.objects.link(new_root)
        for c in root.children:
            d = c.copy()
            bpy.context.scene.collection.objects.link(d)
            d.parent = new_root
            d.matrix_parent_inverse = c.matrix_parent_inverse.copy()
            d.location, d.rotation_euler, d.scale = c.location.copy(), c.rotation_euler.copy(), c.scale.copy()
            for m in d.modifiers:
                if m.type == 'ARMATURE':
                    m.object = new_root
        for pb in new_root.pose.bones:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
        return new_root, {pb.name: Bone(new_root, pb) for pb in new_root.pose.bones}
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
    """Lay out [(root copy, rotation 3x3, local centre[, the body's own move: a 4x4 in its frame])] in a cols x rows grid
    of square cells, render it once. The body's move (a lift and a pitch about the model's origin on the ground, as the
    game turns it) is applied before the view, so planted feet stay planted in the frame (D21)."""
    for i, entry in enumerate(posed):
        root, rot, centre = entry[:3]
        body = entry[3] if len(entry) > 3 else Matrix.Identity(4)
        c, r = i % cols, i // cols
        target = Vector(((c - (cols - 1) / 2) * cell, 0.0, ((rows - 1) / 2 - r) * cell))
        root.matrix_world = Matrix.Translation(target - rot @ centre) @ rot.to_4x4() @ body
    bpy.context.view_layer.update()
    names = {o.name for entry in posed for o in entry[0].children_recursive if o.type == 'MESH'}
    # Blender's orthographic scale spans the frame's longer side
    return render(path, (0, -50, 0), (0, 0, 0), ortho=max(cols, rows) * cell, size=size, only=names)


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
        # the whole body's move, about the model's origin on the ground as the game moves it, then the view
        body = (Matrix.Translation((0.0, 0.0, lift)) @ Matrix.Rotation(R(yaw), 4, 'Z') @
                Matrix.Rotation(R(pitch), 4, 'Y'))
        posed.append((c, view, centre, body))
    # framed on every posed frame, not the rest pose: a peck or a stride reaches past the animal at rest (D21: the
    # pecking birds' heads were cut off at the frame's edge)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo_v, hi_v = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for c, rot, _, body in posed:
        c.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for c, rot, _, body in posed:
        m4 = rot.to_4x4() @ body
        for o in c.children_recursive:
            if o.type != 'MESH':
                continue
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            mw = m4 @ o.matrix_world
            for v in me.vertices:
                q = mw @ v.co
                lo_v = Vector((min(lo_v.x, q.x), min(lo_v.y, q.y), min(lo_v.z, q.z)))
                hi_v = Vector((max(hi_v.x, q.x), max(hi_v.y, q.y), max(hi_v.z, q.z)))
            ev.to_mesh_clear()
    if hi_v.x > lo_v.x:
        cv = (lo_v + hi_v) / 2
        cell = max(hi_v.x - lo_v.x, hi_v.z - lo_v.z) * 1.12
        posed = [(c, rot, rot.inverted() @ cv, body) for c, rot, _, body in posed]
    im = _grid_render(posed, cols, rows, cell, path + '.png', (cols * cell_px, rows * cell_px), render)
    remove([o for entry in posed for o in [entry[0]] + list(entry[0].children_recursive)])
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


def measure_feet(root, pose, frames=48):
    """How a motion keeps the feet to the ground (D19), measured, not looked at: a copy of the model posed at frames
    phases, the root lifted and tipped as the motion says, each Foot empty's height read in the world (the ground at
    0), and the lowest point of every leg's meshes (thigh, shin, toes: D20, a bird's toes tipped into the floor while
    its foot points stood on it). Returns None for a model without feet, else {'sink': how far the lowest foot or leg
    ever goes below the ground,
    'contact': the highest the lowest foot gets in any frame (0: some foot always down), 'held': the most any foot moves
    over the motion (0: planted throughout)}, metres."""
    c, parts = copy_of(root, root.name + '.feet')
    feet = [o for n, o in parts.items() if n.startswith('Foot')]
    if not feet:
        remove([c] + list(c.children_recursive))
        return None
    track = {f.name: [] for f in feet}
    legs = [o for n, o in parts.items() if n[:3] in ('Leg', 'Shi', 'Toe') and o.type == 'MESH']
    skin = {}           # a skinned model: each skin mesh's vertices that are mostly leg
    if c.type == 'ARMATURE':
        legs = []
        for o in c.children:
            if o.type != 'MESH':
                continue
            names = {g.index: g.name for g in o.vertex_groups}
            idx = []
            for v in o.data.vertices:
                best = max(v.groups, key=lambda g: g.weight, default=None)
                if best is not None and best.weight > 0.5 and names[best.group][:3] in ('Leg', 'Shi', 'Toe'):
                    idx.append(v.index)
            if idx:
                skin[o] = idx
    lows, deep = [], 0.0
    for i in range(frames):
        for o in parts.values():
            o.rotation_euler = (0.0, 0.0, 0.0)
            if isinstance(o, Bone):
                o.pb.location = (0.0, 0.0, 0.0)
        moved = pose(parts, c, i / frames)
        lift, pitch = moved[0], moved[1]
        c.matrix_world = Matrix.Translation((0.0, 0.0, lift)) @ Matrix.Rotation(R(pitch), 4, 'Y')
        bpy.context.view_layer.update()
        zs = []
        for f in feet:
            w = f.matrix_world.translation
            track[f.name].append((w.x, w.z))
            zs.append(w.z)
        lows.append(min(zs))
        for o in legs:
            mw = o.matrix_world
            deep = max(deep, -min((mw @ v.co).z for v in o.data.vertices))
        if skin:
            dg = bpy.context.evaluated_depsgraph_get()
            for o, idx in skin.items():
                me = o.evaluated_get(dg).to_mesh()
                mw = o.matrix_world
                deep = max(deep, -min((mw @ me.vertices[i].co).z for i in idx))
                o.evaluated_get(dg).to_mesh_clear()
    remove([c] + list(c.children_recursive))
    held = max(max(math.hypot(x - t[0][0], z - t[0][1]) for x, z in t) for t in track.values())
    return dict(sink=round(max(0.0, -min(lows), deep), 4), contact=round(max(lows), 4), held=round(held, 4))


# ------------------------------------------------------------------ the motions, as the game's behaviours move the parts

def head_bob(phase):
    """GroundBird.HeadBob: a walking bird's head against its body at walk phase phase (radians; a step every 2 pi), -1
    back to +1 forward (D21): it holds still in the air for most of the step, then thrusts forward, eased."""
    u = phase / (2 * math.pi)
    u -= math.floor(u)
    v = (u - 0.45) % 1.0
    if v < 0.7:
        return 1 - 2 * v / 0.7
    t = (v - 0.7) / 0.3
    return -1 + 2 * t * t * (3 - 2 * t)


LOOKS = (0.0, 0.85, 0.35, -0.6, -0.15, 0.55, -0.9, -0.35)


def look_about(x):
    """CritterIdle.Look: a bird's look about (-1..1; the pattern repeats every 2 pi): a quick eased turn to a new
    direction (a fifth of each spell), held, eight spells a turn (D21)."""
    u = (x / (2 * math.pi)) % 1.0
    n = len(LOOKS)
    f = u * n
    i = min(n - 1, int(f))
    k = min(1.0, max(0.0, (f - i) / 0.2))
    k = k * k * (3 - 2 * k)
    return LOOKS[(i - 1) % n] + (LOOKS[i] - LOOKS[(i - 1) % n]) * k


def _slide(parts, name, x):
    """GroundBird's head.Slide: the part moved x metres forward from its rest place (in its parent's frame)."""
    o = parts.get(name)
    if o is None:
        return
    if isinstance(o, Bone):
        o.pb.location = (x, 0.0, 0.0)
    else:
        o.location.x += x


def _set(parts, name, x=0.0, y=0.0, z=0.0):
    if name in parts:
        parts[name].rotation_euler = (R(x), R(y), R(z))


# ------------------------------------------------------------------ the gait (D19): World/LegGait.cs is the same
#
# Every walking leg is a thigh (Leg.., origin at the hip) with a shin under it (Shin.., origin at the knee) and an
# empty at the foot's contact point (Foot..). Each foot follows a path: planted on the ground while the body passes
# over it (the stance), then lifted and carried forward (the swing); the thigh and the shin are turned to reach it,
# the knee bending the way it bends in the picture (two_bone). So the feet stay on the ground and the knees bend,
# where a rigid leg swung from the hip scissors and lifts its foot at both ends of its swing.

GAITS = {
    # a four-beat walk (back-left, front-left, back-right, front-right), three feet down most of the time
    'walk': dict(duty=0.65, stride=0.6, step=0.14, bob=-0.012, phase={'BL': 0.0, 'FL': 0.25, 'BR': 0.5, 'FR': 0.75}),
    # a trot: diagonal pairs together, a moment with no foot down between them
    'trot': dict(duty=0.42, stride=0.9, step=0.22, bob=0.03, phase={'FR': 0.0, 'BL': 0.0, 'FL': 0.5, 'BR': 0.5}),
    # a bird's walk: one foot then the other
    'step': dict(duty=0.6, stride=0.55, step=0.12, bob=-0.008, phase={'R': 0.0, 'L': 0.5}),   # a low shuffle (D22)
}


def foot_path(p, duty, stride, step):
    """Where the foot is at phase p (0..1), from the middle of its path: (forward, up). In stance it slides back
    along the ground at an even pace; in swing it lifts and comes forward, eased."""
    p %= 1.0
    if p < duty:
        return stride * (0.5 - p / duty), 0.0
    t = (p - duty) / (1.0 - duty)
    return stride * (t * t * (3 - 2 * t) - 0.5), step * math.sin(math.pi * t)


BEND = -1     # LegGait.Bend: the knee (an elbow, a hock, a heel) behind the hip-to-foot line


def two_bone(knee, foot, target, bend):
    """A thigh from the hip to knee and a shin from knee to foot (rest positions from the hip, in the side plane:
    forward, up) turned so the foot reaches target (as near as the leg reaches). bend: +1 the knee forward of the
    hip-to-foot line, -1 behind. Returns the thigh's turn and the shin's turn on top of it (radians, forward-to-up)."""
    l1 = math.hypot(knee[0], knee[1])
    l2 = math.hypot(foot[0] - knee[0], foot[1] - knee[1])
    d = min(max(math.hypot(target[0], target[1]), abs(l1 - l2) + 1e-6), l1 + l2 - 1e-6)
    phi = math.atan2(target[1], target[0])
    a = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    th1 = phi + bend * a
    kx, kz = l1 * math.cos(th1), l1 * math.sin(th1)
    th2 = math.atan2(d * math.sin(phi) - kz, d * math.cos(phi) - kx)
    d1 = th1 - math.atan2(knee[1], knee[0])
    return d1, th2 - math.atan2(foot[1] - knee[1], foot[0] - knee[0]) - d1


def legs_of(parts):
    """Each jointed leg: {suffix: (thigh, shin, hip (x, z), knee from the hip, foot from the hip, length, bend, toe or
    None, end from the hip, the foot from the end)}. The toe (Toe..: a bird's toes, a paw) hangs from the shin at the
    ankle, the Foot point under it, and is kept level (D20); the bones end at the ankle (the end), or at the foot when
    there is no toe. LegGait.Rig.Find is the same."""
    out = {}
    for name, thigh in parts.items():
        if not name.startswith('Leg') or thigh.type != 'MESH':
            continue
        sfx = name[3:]
        shin, foot = parts.get('Shin' + sfx), parts.get('Foot' + sfx)
        if shin is None or foot is None:
            continue
        toe = parts.get('Toe' + sfx)
        knee = (shin.location.x, shin.location.z)
        end = (knee[0] + toe.location.x, knee[1] + toe.location.z) if toe is not None else None
        base = end or knee                              # the Foot point hangs from the toe, or from the shin
        f = (base[0] + foot.location.x, base[1] + foot.location.z)
        end = end or f
        l1, l2 = math.hypot(*knee), math.hypot(end[0] - knee[0], end[1] - knee[1])
        # every joint here bends back, whatever pose the picture caught (D22): a front leg's elbow, a hind leg's hock, a
        # bird's heel. Read from the picture, a front leg caught reaching back bent its joint forward all through its step
        bend = BEND
        mark = parts.get('Tip' + sfx)       # the front of the toes on the ground (LegGait.Rig.Find); else the foot
        tip = (end[0] + mark.location.x, end[1] + mark.location.z) if (mark is not None and toe is not None) else f
        # a leg hanging from a back's rear half (Hips) that flexes: its hip in the root's frame, and the Hips with it
        hips = parts.get('Hips')
        under = hips if (hips is not None and isinstance(thigh, Bone) and thigh.pb.parent is not None
                         and thigh.pb.parent.name == 'Hips') else None
        hip = (thigh.location.x, thigh.location.z)
        if under is not None:
            hip = (hip[0] + hips.location.x, hip[1] + hips.location.z)
        out[sfx] = (thigh, shin, hip, knee, f, l1 + l2, bend, toe, end,
                    (f[0] - end[0], f[1] - end[1]), tip, (end[0] - tip[0], end[1] - tip[1]), under,
                    (hips.location.x, hips.location.z) if under is not None else None)
    return out


def _place(leg, target_root, tip=0.0, roll=0.0):
    """Turn a leg's thigh and shin so the front of its toes is at target_root (x, z in the root's frame), the foot rolled
    by roll (radians, toes down: D21) and turned back by the thigh's and shin's turns and by the body's tip (degrees,
    the review's pitch), so with no roll it lies level: the bones end at the ankle, set back from the toes as the foot
    lies (LegGait.Rig.Place)."""
    thigh, shin, hip, knee, foot, _, bend, toe, end, off, tipr, from_tip, under, hp = leg
    if under is not None:
        # the Hips turned by h (forward toward up; Blender's +Y turn is the other way): the target into their frame
        h = -under.rotation_euler[1]
        c0, s0 = math.cos(-h), math.sin(-h)
        dx, dz = target_root[0] - hp[0], target_root[1] - hp[1]
        target_root = (hp[0] + dx * c0 - dz * s0, hp[1] + dx * s0 + dz * c0)
        tip = tip - math.degrees(h)
    a = R(tip) - roll
    c, s = math.cos(a), math.sin(a)
    bx, bz = from_tip[0] * c - from_tip[1] * s, from_tip[0] * s + from_tip[1] * c
    d1, d2 = two_bone(knee, end, (target_root[0] + bx - hip[0], target_root[1] + bz - hip[1]), bend)
    thigh.rotation_euler = (0, -d1, 0)      # Blender's +Y turns forward toward down: the opposite of forward-to-up
    shin.rotation_euler = (0, -d2, 0)
    if toe is not None:
        toe.rotation_euler = (0, d1 + d2 - R(tip) + roll, 0)


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def foot_roll(kind, front, p):
    """LegGait.Roll: how far a foot is rolled at phase p of its cycle (radians, toes down, D21): the heel lifting late
    in the stance, a bird's toes curling and a mammal's paw folding back in the swing, level again before it lands."""
    p -= math.floor(p)
    if kind == 'step':
        off, swing = 20.0, 35.0
    elif kind == 'walk':
        off, swing = (30.0, 75.0) if front else (25.0, 40.0)
    else:
        off, swing = (35.0, 90.0) if front else (30.0, 50.0)
    duty = GAITS[kind]['duty']
    if p < duty:
        r = off * _smooth(0.75, 1.0, p / duty)
    else:
        u = (p - duty) / (1 - duty)
        r = (off + (swing - off) * _smooth(0.0, 0.35, u) if u < 0.35 else
             swing * (1 - _smooth(0.35, 0.85, u)) if u < 0.85 else 0.0)
    return R(r)


def _lift_at(x, hF, hB, xF, xB, nF, nB):
    if nF == 0 or nB == 0 or abs(xF - xB) < 1e-4:
        return min(hF, hB)
    return hB + (x - xB) * (hF - hB) / (xF - xB)


# LegGait's bound (a squirrel's dash, D21): keys at k, each pair's foot against its hip in leg lengths, rolls, the back
BOUND_K = (0.0, 0.14, 0.38, 0.65, 0.88)
HIND_KEYS = ((0.15, 0.0), (-0.45, 0.03), (-0.55, 0.25), (-0.05, 0.35), (0.35, 0.18))
FRONT_KEYS = ((-0.05, 0.0), (-0.35, 0.15), (0.45, 0.3), (0.5, 0.22), (0.4, 0.08))
HIND_ROLL = (30.0, 40.0, 50.0, 30.0, 0.0)
FRONT_ROLL = (0.0, 60.0, 40.0, 15.0, 0.0)
SPINE_KEYS = (12.0, -8.0, -6.0, 4.0, 10.0)


def loop_f(ks, vs, k):
    """LegGait.LoopF: a periodic Catmull-Rom curve through vs at ks, sampled at k."""
    n = len(ks)
    k -= math.floor(k)
    i = n - 1
    for j in range(n):
        if ks[j] <= k:
            i = j
    i0, i2, i3 = (i + n - 1) % n, (i + 1) % n, (i + 2) % n
    t0, t1 = ks[i], (ks[0] + 1.0 if i2 == 0 else ks[i2])
    u = min(1.0, max(0.0, (k - t0) / max(1e-5, t1 - t0)))
    p0, p1, p2, p3 = vs[i0], vs[i], vs[i2], vs[i3]
    return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def bound_foot(hind, k):
    keys = HIND_KEYS if hind else FRONT_KEYS
    return loop_f(BOUND_K, [v[0] for v in keys], k), max(0.0, loop_f(BOUND_K, [v[1] for v in keys], k))


def bound_legs(legs, k, amount=1.0, pitch=0.0):
    """LegGait.Rig.Bound: each pair's feet on the bound's loop (the far leg 0.06 behind), for a level body turned back by
    the body's pitch (radians, forward toward up), the feet rolled."""
    c, s = math.cos(-pitch), math.sin(-pitch)
    for sfx, leg in legs.items():
        hind = sfx.startswith('B')
        q = k + (-0.06 if len(sfx) > 1 and sfx[1] == 'L' else 0.0)
        hip, tipr = leg[2], (leg[2][0] + leg[10][0], leg[2][1] + leg[10][1])
        kx, kz = bound_foot(hind, q)
        L = leg[5]
        wx = tipr[0] + (hip[0] + kx * L - tipr[0]) * amount
        wz = tipr[1] + ((kz + (0.04 if hind else 0.08)) * L - tipr[1]) * amount   # above the ground (z 0), on the pads
        wx, wz = wx * c - wz * s, wx * s + wz * c
        roll = R(max(0.0, loop_f(BOUND_K, HIND_ROLL if hind else FRONT_ROLL, q))) * amount    # never heel down
        _place(leg, (wx, wz), tip=-math.degrees(pitch), roll=roll)


def walk_legs(legs, kind, p, lift, pitched=True):
    """LegGait.Rig.Walk (Pose): each foot's toes on its path and its roll; each end of the body as low as its legs need
    to reach their ankles, the body pitched between them (a four-legged one: D21); every leg placed. Returns (the lift
    at the root's origin, the pitch: radians, forward toward up)."""
    g = GAITS[kind]
    want, roll = {}, {}
    for sfx, leg in legs.items():
        hip, tipr = leg[2], (leg[2][0] + leg[10][0], leg[2][1] + leg[10][1])
        middle = tipr[0] if len(sfx) == 1 else (hip[0] + tipr[0]) / 2      # a bird's foot stays where it stands
        q = p + g['phase'].get(sfx, 0.0)
        dx, dz = foot_path(q, g['duty'], g['stride'] * leg[5], g['step'] * leg[5])
        want[sfx] = (middle + dx, dz)               # planted on the ground (z 0), not at the picture's height
        roll[sfx] = foot_roll(kind, sfx.startswith('F'), q)
    hF = hB = lift
    xF = xB = 0.0
    nF = nB = 0
    pitch = 0.0
    for pas in range(2):
        lift0 = _lift_at(0.0, hF, hB, xF, xB, nF, nB) if pitched else lift
        c, s = math.cos(pitch), math.sin(pitch)
        dipF = dipB = 0.0
        nF = nB = 0
        xF = xB = 0.0
        for sfx, leg in legs.items():
            hip, ft = leg[2], leg[11]
            cr, sr = math.cos(roll[sfx]), math.sin(roll[sfx])
            ax = want[sfx][0] + ft[0] * cr + ft[1] * sr
            az = want[sfx][1] - ft[0] * sr + ft[1] * cr
            gx, gz = ax, az - lift0
            tx, tz = gx * c + gz * s - hip[0], -gx * s + gz * c - hip[1]
            r = 0.98 * leg[5]
            dip = max(0.0, -tz - math.sqrt(r * r - tx * tx)) if (tz < 0 and abs(tx) < r) else 0.0
            if pitched and sfx.startswith('F'):
                dipF, xF, nF = max(dipF, dip), xF + hip[0], nF + 1
            else:
                dipB, xB, nB = max(dipB, dip), xB + hip[0], nB + 1
        xF = xF / nF if nF else 0.0
        xB = xB / nB if nB else 0.0
        if pas == 0:
            hF, hB = lift - (dipF if nF else dipB), lift - dipB
        else:
            hF, hB = hF - (dipF if nF else dipB), hB - dipB
        if not pitched:
            hF = hB = min(hF, hB)
        pitch = math.atan2(hF - hB, xF - xB) if (pitched and nF and nB and abs(xF - xB) > 1e-4) else 0.0
    used = _lift_at(0.0, hF, hB, xF, xB, nF, nB) if pitched else min(hF, hB)
    c, s = math.cos(pitch), math.sin(pitch)
    for sfx, leg in legs.items():
        gx, gz = want[sfx][0], want[sfx][1] - used
        # in the review's terms the body's tip is nose-down: -pitch
        _place(leg, (gx * c + gz * s, -gx * s + gz * c), tip=-math.degrees(pitch), roll=roll[sfx])
    return used, pitch


def gait(kind, height, head_nod=0.0, tail=None, period=1.0, tail_axis='y', bob=0.0):
    """A walk, a trot or a bird's walk (GAITS), its feet planted: the motion LegGait gives the game. Stride, step and
    bob are shares of the leg's length. head_nod: a bird's head nodding forward and back with each step (degrees,
    about the neck: GroundBird's headNod; a photo cut-out's head can't slide without its cut edge showing, D19).
    tail_axis: the tail's swing axis, 'y' its side (in the picture's plane), 'x' its long axis (a curled tail, D20).
    bob: how far a bird's head thrusts and holds with each step (metres: GroundBird's headSlide, head_bob)."""
    g = GAITS[kind]
    track = None
    # a bird's head nods in links (its neck and its head: GroundBird's head.Set through PartChain), two nods a cycle
    nod = chain_track(lambda t: 6 + head_nod * math.sin(4 * math.pi * t / period), period) if head_nod else None
    if tail:        # (degrees either side, about centre, beats a second): wagged in links, whole beats in a cycle
        amp, mid, rate = tail
        beats = max(1, round(rate * period))
        track = chain_track(lambda t: mid + amp * math.sin(2 * math.pi * beats * t / period), period)

    def pose(parts, root, p):
        a = 2 * math.pi * p
        legs = legs_of(parts)
        L = sum(l[5] for l in legs.values()) / max(1, len(legs))
        lift = g['bob'] * L * 0.5 * (1 - math.cos(2 * a))
        lift, pitch = walk_legs(legs, kind, p, lift)
        down = -math.degrees(pitch)                 # the review's pitch: nose down
        if track is not None:
            set_chain(parts, 'Tail', tail_axis, track, p)
        if 'Head' in parts:
            if nod is not None:     # a bird: its neck and head nod, its head thrusting and holding (GroundBird)
                set_chain(parts, 'Head', 'y', nod, p)
                _slide(parts, 'Head', bob * head_bob(4 * math.pi * p))
                _set(parts, 'Plume', y=-0.8 * head_nod * math.sin(2 * a))
            else:                   # a four-legged animal holds its head steady as its back tilts (Dog: the same)
                _set(parts, 'Head', y=4.0 - down)
        return lift, down
    return pose


# ------------------------------------------------------------------ links (World/PartChain.cs is the same)
#
# A tail, a wing, a fish's tail in links (Tail, Tail2, Tail3): each link takes a share of the angle (the first the most:
# n - i over 1 + .. + n) and each further link follows the one before it LAG seconds late, so a swish runs down the part
# like a whip instead of swinging one stick.

LAG = 0.06


def chain_share(i, n):
    return (n - i) / (n * (n + 1) * 0.5)


def chain_track(angle, period, samples=240):
    """The links' angles through one period of a motion whose first link follows angle(t) (degrees, t in seconds): the
    lag filter run as the game runs it (on fine steps), past its start, then sampled. Returns f(p, i): link i's angle
    at phase p (0..1)."""
    n_max, sub = 6, 20
    dt = period / (samples * sub)
    a = [0.0] * n_max
    rec = []
    follow = 1.0 - math.exp(-dt / LAG)
    for cycle in range(3):
        for k in range(samples):
            for j in range(sub):
                t = (k + j / sub) * period / samples
                a[0] = angle(t)
                for i in range(1, n_max):
                    a[i] += (a[i - 1] - a[i]) * follow
            if cycle == 2:
                rec.append(list(a))
    return lambda p, i: rec[int(p % 1.0 * samples) % samples][i]


def set_chain(parts, name, axis, track, p):
    """Bend the chain name, name2, .. by track (chain_track) at phase p, about axis ('x', 'y' or 'z' of each link)."""
    links = [name] + [name + str(k) for k in range(2, 10) if name + str(k) in parts]
    links = [l for l in links if l in parts]
    n = len(links)
    for i, l in enumerate(links):
        deg = track(p, i) * chain_share(i, n)
        r = {'x': (R(deg), 0, 0), 'y': (0, R(deg), 0), 'z': (0, 0, R(deg))}[axis]
        parts[l].rotation_euler = r


def walk(height, run=False):
    """A four-legged walker's walk, or its run (a trot)."""
    return gait('trot' if run else 'walk', height)


def hop_feet(u, L):
    """LegGait.HopFoot: where a hopping bird's foot is at u (0..1 of one hop: the air first, then the ground), from where
    it stands, and its roll (toes down, radians), for a leg of length L (D22). On the ground it is planted and the body
    passes over it, from a little forward (landing) to trailing behind (the push), the heel lifting at the push; in the
    air it trails off the push, tucks up under the belly with its toes curled, and reaches forward to land: one loop."""
    u -= math.floor(u)
    if u < 0.5:
        a = u / 0.5
        return (L * (-0.3 + 0.4 * _smooth(0.0, 1.0, a)), 0.45 * L * math.sin(math.pi * a),
                0.5 * (1 - a) + 0.6 * math.sin(math.pi * a))
    b = (u - 0.5) / 0.5
    return L * (0.1 - 0.4 * b), 0.0, 0.5 * _smooth(0.7, 1.0, b)


def hop(height, hop_height=0.05):
    """A bird that hops with both feet (GroundBird's hopper): it crouches deep on its heels, springs (up 5 cm), its
    feet trailing, tucks them up under its belly, reaches them forward and lands on them (hop_feet, D22: the feet had
    moved a few pixels, the legs hanging the same all through the hop)."""
    def pose(parts, root, p):
        sa = math.sin(2 * math.pi * p)
        legs = legs_of(parts)
        L = sum(l[5] for l in legs.values()) / max(1, len(legs))
        lift = hop_height * sa if sa > 0 else HOP_CROUCH * L * sa
        for sfx, leg in legs.items():
            hip, tipr = leg[2], (leg[2][0] + leg[10][0], leg[2][1] + leg[10][1])
            dx, dz, roll = hop_feet(p, leg[5])
            # in the air from where it stands, lifted with the body; on the ground on the ground
            _place(leg, (tipr[0] + dx, tipr[1] + dz if sa > 0 else -lift), roll=roll)
        _set(parts, 'Head', y=-8 * sa)
        return lift, -6 * max(0.0, sa)
    return pose


HOP_CROUCH = 0.3        # GroundBird's hopper: the body down into the heels by this share of the leg between hops


def peck(height, turn=25.0, tip=30.0, period=0.22 / 0.45):
    """A bird pecking, as GroundBird pecks (peckTurn, peckTip): the body tipping forward on its feet and the head
    turning beak-down with it, so the beak reaches the ground; then a pause. A photo cut-out's head turned alone by
    62 degrees (the original kit's) folds at the neck like a broken one (D19): most of the reach is the body's."""
    def reachable(legs, deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        for leg in legs.values():
            fx, fz = leg[2][0] + leg[8][0], leg[2][1] + leg[8][1]       # the ankle over the planted, level foot
            tx, tz = fx * c - fz * s - leg[2][0], fx * s + fz * c - leg[2][1]
            l1 = math.hypot(*leg[3])
            l2 = math.hypot(leg[8][0] - leg[3][0], leg[8][1] - leg[3][1])
            d = math.hypot(tx, tz)
            if d > 0.98 * (l1 + l2) or d < abs(l1 - l2):
                return False
        return True

    def head_angle(t):
        k = (t / period) / 0.45
        return 8 + turn * (math.sin(math.pi * k) if k <= 1 else 0.0)
    track = chain_track(head_angle, period)     # the neck bends, the head following a moment late (PartChain)

    def pose(parts, root, p):
        k = p / 0.45
        e = math.sin(math.pi * k) if k <= 1 else 0.0
        set_chain(parts, 'Head', 'y', track, p)
        legs = legs_of(parts)
        # a crest's plumes hang: turned back by most of the head's and the body's turn (GroundBird's plume)
        _set(parts, 'Plume', y=-0.8 * (turn * e + tip * e))
        want = tip * e
        if not reachable(legs, want):       # LegGait.Rig.Reach: no further than both feet can stay planted
            lo, hi = 0.0, want
            for _ in range(16):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if reachable(legs, mid) else (lo, mid)
            want = lo
        # the body tips about its origin, between its feet; each foot stays where it stood: its place turned back by
        # the tip, in the tipped body's frame (Blender's +Y turn: x' = x cos + z sin, z' = -x sin + z cos)
        c, s = math.cos(math.radians(want)), math.sin(math.radians(want))
        for leg in legs.values():
            fx, fz = leg[2][0] + leg[10][0], leg[2][1] + leg[10][1]
            _place(leg, (fx * c - fz * s, fx * s + fz * c), tip=want)
        return 0.0, want
    return pose


def swish(rate, amp=17.0, mid=3.0, period=None):
    """WallCat's tail (its sitting cat): 3 + 17 (sin f + 0.25 sin 2.1 f), f turning rate radians a second (1.6 sitting,
    3.2 on the move); the 2.1 shown as 2 so the loop closes. In links about the tail's side axis."""
    period = period or 2 * math.pi / rate
    track = chain_track(lambda t: mid + amp * (math.sin(rate * t) + 0.25 * math.sin(2 * rate * t)), period)

    def pose(parts, root, p):
        set_chain(parts, 'Tail', 'y', track, p)
        return 0.0, 0.0
    return pose, period


def critter(part, axis, amp, speed, offset=0.0, snap=False):
    """CritterIdle: offset + amp (sin(t speed) + 0.25 sin 2(t speed)), speed radians a second, about axis; a part in
    links bends link by link. snap: a bird's look about, quick turns and holds (look_about)."""
    period = 2 * math.pi / speed
    if snap:
        track = chain_track(lambda t: offset + amp * look_about(speed * t), period)
    else:
        track = chain_track(lambda t: offset + amp * (math.sin(speed * t) + 0.25 * math.sin(2 * speed * t)), period)

    def pose(parts, root, p):
        set_chain(parts, part, axis, track, p)
        return 0.0, 0.0
    return pose, period


def flick(period=1.2):
    """TreeSquirrel's tail flick: 4 + 24 sin(k pi) over 0.35 s, then settling (a flick every period seconds)."""
    track = chain_track(lambda t: 4 + (24 * math.sin(math.pi * t / 0.35) if t < 0.35 else 0.0), period)

    def pose(parts, root, p):
        set_chain(parts, 'Tail', 'y', track, p)
        return 0.0, 0.0
    return pose, period


def smooth_damp(current, target, vel, smooth_time, dt):
    """Unity's Mathf.SmoothDamp (a critically damped spring), as the game eases a pitch or a yaw."""
    omega = 2.0 / smooth_time
    x = omega * dt
    e = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    change = current - target
    temp = (vel + omega * change) * dt
    vel = (vel - omega * temp) * e
    return target + (change + temp) * e, vel


def dash(height, hop_time=0.18):
    """TreeSquirrel's dash: long low hops, the body 12 cm up at the top of each (lift 0.12 sin(k pi)), pitched from 12
    degrees nose up to 12 nose down across each (eased by SmoothDamp over 0.1 s, as the game does: D21, the review had
    left it flat), the tail streaming behind the pitch (-8 + 0.7 pitch), in links so it whips; a model with jointed legs
    and a back (Hips) bounds with them (LegGait.Bound, BoundSpine), as TreeSquirrel drives them."""
    steps = 240
    dt = hop_time / steps
    pitch, vel, rec = 0.0, 0.0, []
    for cycle in range(4):
        for i in range(steps):
            k = i / steps
            pitch, vel = smooth_damp(pitch, 12.0 + (-24.0) * k, vel, 0.1, dt)
            if cycle == 3:
                rec.append(pitch)

    def game_pitch(t):
        return rec[int((t / hop_time) % 1.0 * steps) % steps]
    track = chain_track(lambda t: -8.0 + 0.7 * game_pitch(t), hop_time)

    def pose(parts, root, p):
        if 'Tail' in parts:
            set_chain(parts, 'Tail', 'y', track, p)
        gp = game_pitch(p * hop_time)
        if 'Hips' in parts:     # the back's rear half: its CCW flex is the Blender +Y turn's opposite
            parts['Hips'].rotation_euler = (0, -R(loop_f(BOUND_K, SPINE_KEYS, p)), 0)
        legs = legs_of(parts)
        if legs:
            bound_legs(legs, p, 1.0, R(gp))
        # the review's pitch is nose down; the game's nose up
        return 0.12 * math.sin(math.pi * p), -gp
    return pose, hop_time


def bound(height):
    """WallCat padding along a wall top in soft bounds of 0.34 s: up 9 cm and down, the body rocking 8 degrees
    (sin 2 pi k), a walking model's legs tucked through the bound and landing (LegGait.Rig.Hop)."""
    def pose(parts, root, p):
        s = math.sin(math.pi * p)
        for leg in legs_of(parts).values():
            tipr = (leg[2][0] + leg[10][0], leg[2][1] + leg[10][1])
            L = leg[5]
            _place(leg, (tipr[0] - 0.15 * L * s, tipr[1] + 0.25 * L * s) if s > 0 else (tipr[0], 0.0),
                   roll=0.6 * s if s > 0 else 0.0)
        # WallCat's pitchRock is the game's nose-up turn; the review's pitch is nose-down
        return 0.09 * s, -8 * math.sin(2 * math.pi * p)
    return pose, 0.34


def pond(tail=None, flippers=None, recoil=0.0, fins=None):
    """PondDuck's koi and turtle: a tail swept tail[0] degrees either side tail[1] times a second, in links (about the
    vertical: they are seen from above), the whole fish yawing recoil of it the other way (its head recoiling, D21),
    its pectoral fins (fins: (sweep, strokes a second)) sculling in turn; or four flippers paddled flippers[0] degrees
    at flippers[1] strokes a second, front right with back left, then the others."""
    if tail:
        sweep, beat = tail
        period = 1.0 / beat
        if fins:        # two tail beats a loop, so the slower fins loop too
            period = max(period, round(beat / fins[1]) / beat if fins[1] > 0 else period)
        track = chain_track(lambda t: sweep * math.sin(2 * math.pi * beat * t), period)
    else:
        sweep, beat = flippers
        period = 1.0 / beat

    def pose(parts, root, p):
        if tail:
            set_chain(parts, 'Tail', 'z', track, p)
            t = p * period
            yaw = -recoil * sweep * math.sin(2 * math.pi * beat * t)
            if fins:
                fs, fb = fins
                for i, name in enumerate(('FinL', 'FinR')):
                    if name in parts:
                        out = (0.5 + 0.5 * math.sin(2 * math.pi * fb * t + i * math.pi)) * fs
                        parts[name].rotation_euler = (0, 0, R(out if name == 'FinL' else -out))
            return 0.0, 0.0, yaw
        else:
            for name, ph in (('FlipperFR', 0.0), ('FlipperBL', 0.0), ('FlipperFL', math.pi), ('FlipperBR', math.pi)):
                if name in parts:
                    side = 1 if name.endswith('R') else -1
                    parts[name].rotation_euler = (0, 0, R(side * sweep * math.sin(2 * math.pi * p + ph)))
        return 0.0, 0.0
    return pose, period


DOWN_SHARE = 0.55


def wing_stroke(u, up, down, fold, sweep):
    """WingStroke.At at u (0..1 of a beat, 0 its top): (flap up, wrist fold, sweep back: degrees; the body's rise -1..1)
    (D21): spread and sweeping a little forward on the downstroke, folded at the wrist and swept back on the upstroke."""
    u -= math.floor(u)
    if u < DOWN_SHARE:
        w = u / DOWN_SHARE
        e, sn = 0.5 - 0.5 * math.cos(math.pi * w), math.sin(math.pi * w)
        return up + (-down - up) * e, 0.0, -0.3 * sweep * sn, sn
    v = (u - DOWN_SHARE) / (1 - DOWN_SHARE)
    ev, sv = 0.5 - 0.5 * math.cos(math.pi * v), math.sin(math.pi * v)
    return -down + (up + down) * ev, fold * sv, sweep * sv, -0.4 * sv


def flight(span, up=40.0, down=40.0, fold=0.0, sweep=0.0, rate=15.0, tail_tilt=6.0, bob=0.01):
    """GroundBird's take-off flight (and SkyFlock's bursts): with fold or sweep, a real bird's beat (wing_stroke: the
    wing in two links, its outer link folding at the wrist; swept about the vertical), the tail tilting and the body
    rising with each downstroke; without, the original kit's even beat of +-up degrees, the tip trailing. rate radians
    a second."""
    period = 2 * math.pi / rate
    track = chain_track(lambda t: up * math.sin(rate * t), period)

    def pose(parts, root, p):
        if fold > 0 or sweep > 0:
            fl, fo, sw, rise = wing_stroke(p, up, down, fold, sweep)
            for wing, sign in (('WingL', 1), ('WingR', -1)):
                if wing in parts:       # flap about the long axis, sweep about the vertical (Part.SetWing)
                    parts[wing].rotation_euler = (R(sign * fl), 0, R(sign * sw))
                if wing + '2' in parts:
                    parts[wing + '2'].rotation_euler = (R(-sign * fo), 0, 0)
            _set(parts, 'Tail', y=-tail_tilt * rise)
            return bob * rise, 0.0
        for wing, sign in (('WingL', 1), ('WingR', -1)):
            if wing in parts:
                links = [wing] + ([wing + '2'] if wing + '2' in parts else [])
                for i, l in enumerate(links):
                    parts[l].rotation_euler = (R(sign * track(p, i) * chain_share(i, len(links))), 0, 0)
        return -0.04 * span * math.sin(2 * math.pi * p), 0.0
    return pose, period


def fly(span, mid=38.0, swing=38.0, hind_lead=1.6):
    """FlitButterfly's wingbeat: mid + swing sin, about the body's long axis (a butterfly's 38 + 38: from flat to 76
    degrees up and back; a dragonfly's about flat, D20), the body rising a little on the downstroke; a dragonfly's
    hind wings (HindL, HindR) hind_lead radians ahead of its forewings (D21)."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        w = mid + swing * math.sin(a)
        _set(parts, 'WingL', x=w)
        _set(parts, 'WingR', x=-w)
        if 'HindL' in parts:
            wh = mid + swing * math.sin(a + hind_lead)
            _set(parts, 'HindL', x=wh)
            _set(parts, 'HindR', x=-wh)
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
