# How far a shipped character goes below the ground in the game's poses, before and after CharacterRig's ground contact
# (docs/LEARNINGS.md C21). Poses the model as CharacterRig does (each joint swung about the body's side axis from its rest,
# the body leaned about its pivot, 0.6 x neck / 1.3 above the feet, and bobbed), with KidAnimator's slide, run, kick and
# landing, and measures the posed mesh's lowest point against the ground it stands on at rest. Then it lifts the body as
# CharacterRig.KeepOnGround does, from the ground points LevelBuildKit.MeasureGroundPoints picks (the vertices each of the
# seat's, legs', feet's, forearms' and hands' bones carries most of that reach furthest in 14 directions of its frame),
# and measures again.
#   blenv/bin/python ground_check.py -- <Name>.fbx <neck height (PlayerRoster)>
# Prints one line a pose: cm under the ground as posed, the lift, cm under after the lift (negative: above).
import bpy, sys, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
FBX, NECK = argv[0], float(argv[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX, axis_forward='-Z', axis_up='Y')
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
kid = bpy.data.objects['Kid']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not kid: bpy.data.objects.remove(o)
C = bpy.context
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
B = rig.data.bones
s = NECK / (rig.matrix_world @ B['Head'].head_local).z
base = rig.matrix_world.copy()
SIDE = Vector((1, 0, 0))                                  # the side axis (the rig faces -y)
PIVOT = 0.6 * NECK / 1.3
HIP_H = (rig.matrix_world @ B['UpperLeg.L'].head_local).z * s
HIP_Y = (rig.matrix_world @ B['Hips'].head_local).y * s


def verts():
    dg = C.evaluated_depsgraph_get(); ev = kid.evaluated_get(dg); m = ev.to_mesh()
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    M = np.array(ev.matrix_world); V = V @ M[:3, :3].T + M[:3, 3]; ev.to_mesh_clear(); return V


def swing(bone, ang, sign=-1):
    pb = rig.pose.bones[bone]
    pb.rotation_quaternion = Quaternion(pb.bone.matrix_local.to_3x3().inverted() @ SIDE, math.radians(sign * ang))


def pose(p):
    for pb in rig.pose.bones: pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    for n, f in (('R', 'F'), ('L', 'B')):
        swing('UpperLeg.' + n, p.get('leg' + f, 0)); swing('LowerLeg.' + n, min(p.get('knee' + f, -4), 0))
        swing('UpperArm.' + n, p.get('arm' + f, 0)); swing('LowerArm.' + n, max(p.get('elbow' + f, 12), 0))
    swing('Head', p.get('headTilt', 0))
    R = Matrix.Rotation(math.radians(p.get('lean', 0)), 4, 'X')
    T = Matrix.Translation((0, HIP_Y, PIVOT)) @ R @ Matrix.Translation((0, -HIP_Y, -PIVOT))
    rig.matrix_world = Matrix.Translation((0, 0, p.get('bob', 0))) @ T @ Matrix.Scale(s, 4) @ base
    C.view_layer.update()


def slide(spent=0.0, over=0.0, scuff=0.0, old=False):
    """KidAnimator.SlidePose (old: the back leg as before v119, its shin folded back under a level thigh)."""
    lean = 58 * (1 + over) * (1 - 0.15 * spent)
    p = dict(lean=-lean, legF=82 - lean, kneeF=-6, armB=24 - lean, elbowB=10, armF=95 - lean, elbowF=30, headTilt=-44)
    if old: p.update(legB=96 - lean + scuff, kneeB=-148 + scuff * 1.5)
    else: p.update(legB=135 - lean + scuff, kneeB=-80 + scuff * 1.5)
    p['bob'] = 0.2 * HIP_H - PIVOT - (HIP_H - PIVOT) * math.cos(math.radians(lean))
    return p


def run(ph, k=1.0):
    fold = lambda a: 14 + 80 * max(0, math.cos(a + 0.9)) ** 2
    sw = 42 * k; x = math.sin(ph)
    return dict(legF=x * sw, legB=-x * sw, kneeF=-fold(ph), kneeB=-fold(ph + math.pi), lean=7 * k, bob=abs(x) * 0.05 * k - 0.02 * k)


def kick(kt, b):
    p = dict(b)
    if kt < 0.3: u = kt / 0.3; th = p['legF'] + (-30 - p['legF']) * u; kn = p['kneeF'] + (-100 - p['kneeF']) * u
    elif kt < 0.7:
        u = (kt - 0.3) / 0.4; th = -30 + 110 * math.sin(u * math.pi / 2); x = min(1, u * 1.6); kn = -100 + 100 * (x * x * (3 - 2 * x))
    else: u = (kt - 0.7) / 0.3; th = 80 + (p['legF'] - 80) * u; kn = p['kneeF'] * u
    p.update(legF=th, kneeF=kn, kneeB=-14, lean=p.get('lean', 0) + (-8 - p.get('lean', 0)) * math.sin(kt * math.pi))
    return p


def land(b):
    p = dict(b)
    for k, d in (('legF', 30), ('legB', 30), ('kneeF', -60), ('kneeB', -60), ('lean', 10), ('bob', -0.07)): p[k] = p.get(k, 0) + d
    return p


# the ground points, as LevelBuildKit.MeasureGroundPoints picks them
pose({})
ground = verts()[:, 2].min()
NAMES = ['Hips', 'UpperLeg.L', 'UpperLeg.R', 'LowerLeg.L', 'LowerLeg.R', 'Foot.L', 'Foot.R', 'LowerArm.L', 'LowerArm.R', 'Hand.L', 'Hand.R']
dirs = [np.array(d, float) / np.linalg.norm(d) for d in
        [(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if abs(x) + abs(y) + abs(z) in (1, 3)]]
me = kid.data
gname = {g.index: g.name for g in kid.vertex_groups}
dom = [gname[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
probes = []
for b in NAMES:
    if b not in rig.data.bones: continue
    inv = rig.data.bones[b].matrix_local.inverted()
    sel = [v.index for v in me.vertices if dom[v.index] == b]
    if not sel: continue
    L = np.array([(inv @ (kid.matrix_parent_inverse @ me.vertices[i].co))[:] for i in sel])
    for k in {int(np.argmax(L @ d)) for d in dirs}: probes.append((b, Vector(L[k])))


def lowest_probe():
    return min((rig.matrix_world @ rig.pose.bones[b].matrix @ l).z for b, l in probes)


pose({}); rest = lowest_probe()


def check(p):
    pose(p); raw = (ground - verts()[:, 2].min()) * 100
    lift = max(0.0, rest - lowest_probe())
    pose(dict(p, bob=p.get('bob', 0) + lift)); after = (ground - verts()[:, 2].min()) * 100
    return raw, lift * 100, after


idle = dict(legF=0, legB=0, kneeF=-5, kneeB=-5)
CASES = [('slide (before v119)', slide(old=True)), ('slide', slide()), ('slide, spent', slide(1)), ('slide, lunge', slide(0, 0.15)),
         ('slide, scuff', slide(0, 0, 5))] + [('run %.1f' % ph, run(ph)) for ph in np.linspace(0, math.pi, 4, endpoint=False)] + \
        [('kick %.1f from a stand' % t, kick(t, idle)) for t in (0.2, 0.5, 0.8)] + \
        [('kick %.1f from a stride' % t, kick(t, run(0))) for t in (0.2, 0.5, 0.8)] + [('landing', land(idle)), ('idle', idle)]
print('[ground] %s: %d ground points' % (FBX.split('/')[-1], len(probes)))
for name, p in CASES:
    print('[ground] %-24s under %5.1f cm   lift %5.1f cm   after %5.1f cm' % ((name,) + check(p)))
