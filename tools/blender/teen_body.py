# The teens' bodies: the joint layout (shared with the armature), the skin-modifier body and
# the teen proportions. Base space: see teen_lib.
import bpy
from mathutils import Vector
from teen_lib import C, new_obj, apply_mods, smooth


def joints(girl):
    """Joint centres (base space) and the body's radii there: name -> ((x, y, z), (rx, ry))."""
    pts = {
        'pelvis': ((0, 0, 0.86), (0.11, 0.085)), 'spine': ((0, 0.005, 0.99), (0.098, 0.075)),
        'chest': ((0, 0, 1.12), (0.112, 0.08)),
        'neck0': ((0, 0.005, 1.235), (0.048, 0.045)), 'neck1': ((0, 0.01, 1.29), (0.043, 0.042)),
    }
    for s, n in ((1, 'L'), (-1, 'R')):
        pts['hip' + n] = ((s * 0.072, 0, 0.82), (0.074, 0.072)); pts['knee' + n] = ((s * 0.078, -0.005, 0.47), (0.05, 0.052))
        pts['calf' + n] = ((s * 0.078, 0.008, 0.34), (0.052, 0.054)); pts['ankle' + n] = ((s * 0.078, 0.012, 0.09), (0.034, 0.036))
        pts['shoulder' + n] = ((s * 0.152, 0.0, 1.19), (0.046, 0.046)); pts['elbow' + n] = ((s * 0.172, 0.0, 0.95), (0.035, 0.035))
        pts['wrist' + n] = ((s * 0.178, 0.0, 0.75), (0.027, 0.025)); pts['hand' + n] = ((s * 0.18, -0.004, 0.67), (0.032, 0.016))
    return pts


def bones(girl):
    """The armature (base space): (name, head, tail, parent). The game needs these names."""
    j = {k: v[0] for k, v in joints(girl).items()}
    b = [('Hips', (0, 0, 0.86), (0, 0, 0.98), None), ('Spine', (0, 0, 0.98), (0, 0, 1.12), 'Hips'),
         ('Chest', (0, 0, 1.12), (0, 0, 1.235), 'Spine'),
         ('Neck', (0, 0.005, 1.235), (0, 0.008, 1.3), 'Chest'), ('Head', (0, 0.008, 1.3), (0, 0.008, 1.6), 'Neck')]
    for n in 'LR':
        b += [('UpperLeg.' + n, j['hip' + n], j['knee' + n], 'Hips'),
              ('LowerLeg.' + n, j['knee' + n], j['ankle' + n], 'UpperLeg.' + n),
              ('Foot.' + n, j['ankle' + n], (j['ankle' + n][0], -0.12, 0.03), 'LowerLeg.' + n),
              ('UpperArm.' + n, j['shoulder' + n], j['elbow' + n], 'Chest'),
              ('LowerArm.' + n, j['elbow' + n], j['wrist' + n], 'UpperArm.' + n),
              ('Hand.' + n, j['wrist' + n], (j['wrist' + n][0], -0.004, 0.64), 'LowerArm.' + n)]
    return b


def build_body(girl):
    """The skin: one smooth mesh over the joints (skin modifier + one subdivision)."""
    pts = joints(girl)
    edges = [('pelvis', 'spine'), ('spine', 'chest'), ('chest', 'neck0'), ('neck0', 'neck1')]
    for n in 'LR':
        edges += [('pelvis', 'hip' + n), ('hip' + n, 'knee' + n), ('knee' + n, 'calf' + n), ('calf' + n, 'ankle' + n),
                  ('chest', 'shoulder' + n), ('shoulder' + n, 'elbow' + n), ('elbow' + n, 'wrist' + n), ('wrist' + n, 'hand' + n)]
    names = list(pts)
    me = bpy.data.meshes.new('body')
    me.from_pydata([pts[k][0] for k in names], [(names.index(a), names.index(b)) for a, b in edges], [])
    body = new_obj('Body', me)
    sk = body.modifiers.new('skin', 'SKIN'); sk.use_smooth_shade = True; sk.branch_smoothing = 0.6
    for i, k in enumerate(names):
        body.data.skin_vertices[0].data[i].radius = pts[k][1]
    body.data.skin_vertices[0].data[names.index('pelvis')].use_root = True
    sub = body.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
    apply_mods(body); smooth(body)
    return body


def arm_dist(co, girl):
    """How far down the arm (shoulder to wrist) a point is; 9 if it is not on an arm."""
    j = joints(girl)
    best = 9
    for n in 'LR':
        chain = [Vector(j['shoulder' + n][0]), Vector(j['elbow' + n][0]), Vector(j['wrist' + n][0])]
        run = 0
        for a, b in zip(chain, chain[1:]):
            ab = b - a; t = (co - a).dot(ab) / ab.length_squared
            if abs(co.x) > 0.12 and -0.2 <= t <= 1.0 and (co - (a + ab * max(0, t))).length < 0.08:
                best = min(best, run + max(0, t) * ab.length)
            run += ab.length
    return best


def grow(co, girl):
    """Base space -> teen proportions: longer legs and torso, a little narrower or broader.
    Above the neck (z > 1.24) points are only lifted, so the head keeps its shape."""
    LEG, TORSO, WIDTH = (1.1, 1.05, 0.95) if girl else (1.15, 1.12, 1.05)
    x, y, z = co
    if z < 0.86: nz = z * LEG
    elif z < 1.24: nz = 0.86 * LEG + (z - 0.86) * TORSO
    else: nz = 0.86 * LEG + 0.38 * TORSO + (z - 1.24)
    w = 1.0 if z > 1.24 else WIDTH
    return Vector((x * w, y * w, nz))
