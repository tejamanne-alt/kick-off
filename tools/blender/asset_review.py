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
    lows, deep = [], 0.0
    for i in range(frames):
        for o in parts.values():
            o.rotation_euler = (0.0, 0.0, 0.0)
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
    remove([c] + list(c.children_recursive))
    held = max(max(math.hypot(x - t[0][0], z - t[0][1]) for x, z in t) for t in track.values())
    return dict(sink=round(max(0.0, -min(lows), deep), 4), contact=round(max(lows), 4), held=round(held, 4))


# ------------------------------------------------------------------ the motions, as the game's behaviours move the parts

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
    'step': dict(duty=0.6, stride=0.55, step=0.22, bob=-0.008, phase={'R': 0.0, 'L': 0.5}),
}


def foot_path(p, duty, stride, step):
    """Where the foot is at phase p (0..1), from the middle of its path: (forward, up). In stance it slides back
    along the ground at an even pace; in swing it lifts and comes forward, eased."""
    p %= 1.0
    if p < duty:
        return stride * (0.5 - p / duty), 0.0
    t = (p - duty) / (1.0 - duty)
    return stride * (t * t * (3 - 2 * t) - 0.5), step * math.sin(math.pi * t)


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
        cross = knee[0] * (end[1] - knee[1]) - knee[1] * (end[0] - knee[0])
        # the knee bends as it does in the picture; a straight leg: a front leg's forward, a hind leg's or a bird's back
        bend = -math.copysign(1, cross) if abs(cross) > 0.08 * l1 * l2 else (1 if sfx.startswith('F') else -1)
        out[sfx] = (thigh, shin, (thigh.location.x, thigh.location.z), knee, f, l1 + l2, bend, toe, end,
                    (f[0] - end[0], f[1] - end[1]))
    return out


def _place(leg, target_root, tip=0.0):
    """Turn a leg's thigh and shin so its foot is at target_root (x, z in the root's frame), its toe kept level with
    the ground: turned back by the thigh's and shin's turns and by the body's tip (degrees, the review's pitch). The
    bones end at the ankle, the foot's offset below it turned into the root's frame by the tip (LegGait.Rig.Place)."""
    thigh, shin, hip, knee, foot, _, bend, toe, end, off = leg
    c, s = math.cos(R(tip)), math.sin(R(tip))
    ox, oz = off[0] * c - off[1] * s, off[0] * s + off[1] * c
    d1, d2 = two_bone(knee, end, (target_root[0] - ox - hip[0], target_root[1] - oz - hip[1]), bend)
    thigh.rotation_euler = (0, -d1, 0)      # Blender's +Y turns forward toward down: the opposite of forward-to-up
    shin.rotation_euler = (0, -d2, 0)
    if toe is not None:
        toe.rotation_euler = (0, d1 + d2 - R(tip), 0)


def gait(kind, height, head_nod=0.0, tail=None, period=1.0, tail_axis='y'):
    """A walk, a trot or a bird's walk (GAITS), its feet planted: the motion LegGait gives the game. Stride, step and
    bob are shares of the leg's length. head_nod: a bird's head nodding forward and back with each step (degrees,
    about the neck: GroundBird's headNod; a photo cut-out's head can't slide without its cut edge showing, D19).
    tail_axis: the tail's swing axis, 'y' its side (in the picture's plane), 'x' its long axis (a curled tail, D20)."""
    g = GAITS[kind]
    track = None
    if tail:        # (degrees either side, about centre, beats a second): wagged in links, whole beats in a cycle
        amp, mid, rate = tail
        beats = max(1, round(rate * period))
        track = chain_track(lambda t: mid + amp * math.sin(2 * math.pi * beats * t / period), period)

    def pose(parts, root, p):
        a = 2 * math.pi * p
        legs = legs_of(parts)
        L = sum(l[5] for l in legs.values()) / max(1, len(legs))
        lift = g['bob'] * L * 0.5 * (1 - math.cos(2 * a))
        want, dip = {}, 0.0
        for sfx, leg in legs.items():
            hip, foot = leg[2], (leg[2][0] + leg[4][0], leg[2][1] + leg[4][1])
            middle = foot[0] if len(sfx) == 1 else (hip[0] + foot[0]) / 2      # a bird's foot stays where it stands
            dx, dz = foot_path(p + g['phase'].get(sfx, 0.0), g['duty'], g['stride'] * leg[5], g['step'] * leg[5])
            want[sfx] = (middle + dx, dz)               # planted on the ground (z 0), not at the picture's height
            # the body comes down as far as a foot needs to reach the ground (98 % of the leg: a straight one can't step);
            # the bones reach the ankle above the foot
            tx, tz = want[sfx][0] - leg[9][0] - hip[0], want[sfx][1] - leg[9][1] - hip[1]
            r = 0.98 * leg[5]
            if tz < 0 and abs(tx) < r:
                dip = max(dip, -tz - math.sqrt(r * r - tx * tx))
        lift -= dip
        for sfx, leg in legs.items():
            _place(leg, (want[sfx][0], want[sfx][1] - lift))
        if track is not None:
            set_chain(parts, 'Tail', tail_axis, track, p)
        if 'Head' in parts:
            _set(parts, 'Head', y=(6 + head_nod * math.sin(2 * a)) if head_nod else 3 * math.sin(2 * a))
        return lift, 0.0            # the body doesn't pitch: the game's Dog and GroundBird don't
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


def hop(height, hop_height=0.05):
    """A bird that hops with both feet (GroundBird's hopper: lifts |sin| x 5 cm): it crouches, springs, tucks its
    feet in the air and lands on them."""
    def pose(parts, root, p):
        sa = math.sin(2 * math.pi * p)
        legs = legs_of(parts)
        L = sum(l[5] for l in legs.values()) / max(1, len(legs))
        lift = hop_height * sa if sa > 0 else 0.12 * L * sa
        for sfx, leg in legs.items():
            hip, foot = leg[2], (leg[2][0] + leg[4][0], leg[2][1] + leg[4][1])
            if sa > 0:      # in the air: the feet tucked under it, a little back
                _place(leg, (foot[0] - 0.15 * L * sa, foot[1] + 0.25 * L * sa))
            else:           # on the ground: planted, the knees taking the crouch
                _place(leg, (foot[0], -lift))
        _set(parts, 'Head', y=-8 * sa)
        return lift, -6 * max(0.0, sa)
    return pose


def peck(height, turn=25.0, tip=30.0):
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

    def pose(parts, root, p):
        k = p / 0.45
        e = math.sin(math.pi * k) if k <= 1 else 0.0
        _set(parts, 'Head', y=8 + turn * e)
        legs = legs_of(parts)
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
            fx, fz = leg[2][0] + leg[4][0], leg[2][1] + leg[4][1]
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


def critter(part, axis, amp, speed, offset=0.0):
    """CritterIdle: offset + amp (sin(t speed) + 0.25 sin 2(t speed)), speed radians a second, about axis; a part in
    links bends link by link."""
    period = 2 * math.pi / speed
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


def dash(height, hop_time=0.18):
    """TreeSquirrel's dash: long low hops, the body 12 cm up at the top of each (lift 0.12 sin(k pi)), the tail held
    back at -8 degrees."""
    def pose(parts, root, p):
        if 'Tail' in parts:
            for l in ['Tail'] + [n for n in ('Tail2', 'Tail3') if n in parts]:
                parts[l].rotation_euler = (0, R(-8 * chain_share(0, 1)), 0) if l == 'Tail' else (0, 0, 0)
        return 0.12 * math.sin(math.pi * p), 0.0
    return pose, hop_time


def bound(height):
    """WallCat padding along a wall top in soft bounds of 0.34 s: up 9 cm and down, the body rocking 8 degrees
    (sin 2 pi k), a walking model's legs tucked through the bound and landing (LegGait.Rig.Hop)."""
    def pose(parts, root, p):
        s = math.sin(math.pi * p)
        for leg in legs_of(parts).values():
            hip, foot = leg[2], (leg[2][0] + leg[4][0], leg[2][1] + leg[4][1])
            L = leg[5]
            _place(leg, (foot[0] - 0.15 * L * s, foot[1] + 0.25 * L * s) if s > 0 else (foot[0], 0.0))
        # WallCat's pitchRock is the game's nose-up turn; the review's pitch is nose-down
        return 0.09 * s, -8 * math.sin(2 * math.pi * p)
    return pose, 0.34


def pond(tail=None, flippers=None):
    """PondDuck's koi and turtle: a tail swept tail[0] degrees either side tail[1] times a second, in links (about the
    vertical: they are seen from above), or four flippers paddled flippers[0] degrees at flippers[1] strokes a second,
    front right with back left, then the others."""
    if tail:
        sweep, beat = tail
        period = 1.0 / beat
        track = chain_track(lambda t: sweep * math.sin(2 * math.pi * beat * t), period)
    else:
        sweep, beat = flippers
        period = 1.0 / beat

    def pose(parts, root, p):
        if tail:
            set_chain(parts, 'Tail', 'z', track, p)
        else:
            for name, ph in (('FlipperFR', 0.0), ('FlipperBL', 0.0), ('FlipperFL', math.pi), ('FlipperBR', math.pi)):
                if name in parts:
                    side = 1 if name.endswith('R') else -1
                    parts[name].rotation_euler = (0, 0, R(side * sweep * math.sin(2 * math.pi * p + ph)))
        return 0.0, 0.0
    return pose, period


def flight(span, beat=40.0, rate=15.0):
    """GroundBird's take-off flight (and the small birds' SkyFlock beat): the wings beat +-beat degrees, rate radians a
    second, about the body's long axis, each wing in two links so its tip trails the beat."""
    period = 2 * math.pi / rate
    track = chain_track(lambda t: beat * math.sin(rate * t), period)

    def pose(parts, root, p):
        for wing, sign in (('WingL', 1), ('WingR', -1)):
            if wing in parts:
                links = [wing] + ([wing + '2'] if wing + '2' in parts else [])
                for i, l in enumerate(links):
                    parts[l].rotation_euler = (R(sign * track(p, i) * chain_share(i, len(links))), 0, 0)
        return -0.04 * span * math.sin(2 * math.pi * p), 0.0
    return pose, period


def fly(span, mid=38.0, swing=38.0):
    """FlitButterfly's wingbeat: mid + swing sin, about the body's long axis (a butterfly's 38 + 38: from flat to 76
    degrees up and back; a dragonfly's about flat, D20), the body rising a little on the downstroke."""
    def pose(parts, root, p):
        a = 2 * math.pi * p
        w = mid + swing * math.sin(a)
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
