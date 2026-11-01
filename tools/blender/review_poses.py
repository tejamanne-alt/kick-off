# Pose audit: renders a built teen in every pose the game uses, from the game's camera yaws and
# a side view, into one contact sheet, so skin showing through clothes, torn fabric and clipping
# can be spotted systematically (review_teen.py shows a teen's look; this shows how the clothes
# survive the poses). The same toon look as review_teen.py / ToonCharacter.shader.
#   blenv/bin/python review_poses.py -- /abs/Boy.blend /abs/boy_poses.png
#       [--yaws 24,66,90]      camera yaws (degrees about the vertical, 0 = facing the camera, positive
#                              turns the face toward the screen's right, so the near side is the right
#                              one; the game's look is 66 = 24 degrees toward the camera from side-on)
#       [--poses run_kneeup,slide]   only these poses (see --list); default all
#       [--cell 360x480] [--scale 1.14]   size of one cell in pixels / the height it frames, in model heights
#       [--dist 12]            camera distance in metres (the game's is about 12 with a 34 degree lens);
#                              0 renders orthographic
#       [--focus 0.45,0.75]    frame only this band of the standing figure's height (0 = feet, 1 = crown),
#                              for close-ups of the hips and knees, the collar and tie, ...
#       [--jobs 3]             render in this many parallel Blender processes
#       [--leaks]              also write <out>_leaks.png: the body's skin that lies under the clothes
#                              at rest, in magenta wherever it is visible in the pose, and print the
#                              pixel counts per cell (a cue to look at the cell, not a verdict)
#       [--body-only]          render only the body's skin (the clothes removed), to see what moves under them
#       [--list]               list the poses and exit
#
# Every pose is the game's own joint angles (KidAnimator.cs, MenuKid.cs), in degrees about the
# character's side axis (CharacterRig): positive swings a limb forward, knees fold with negative
# angles, elbows flex with positive ones, `lean` tilts the whole body forward (positive) about the
# hips and `headTilt` tips the head back (positive). "F" limbs are the right ones (the near side
# at a positive yaw); the "(L)" variants swap the legs and arms, so the other leg is the raised one
# (in game the model also faces left, which puts the same leg on the far side).
import math, sys, os, json, subprocess, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_YAWS = (24, 66, 90)
MENU_YAWS = (24, 42, 90)           # the menu turns the teen 48 degrees toward the camera: yaw 42


def P(**k):
    """A RigPose: RigPose.Neutral (knees -4, elbows 12) with the given joints."""
    d = dict(legF=0, legB=0, kneeF=-4, kneeB=-4, armF=0, armB=0, elbowF=12, elbowB=12, lean=0, headTilt=0, bag=0)
    d.update(k)
    return d


def mirror(p):
    q = dict(p)
    for a, b in (('legF', 'legB'), ('kneeF', 'kneeB'), ('armF', 'armB'), ('elbowF', 'elbowB')):
        q[a], q[b] = p[b], p[a]
    return q


def run_pose(phase):
    """KidAnimator's run cycle at full speed (runK = 1) at a leg phase."""
    def fold(a):
        s = max(0.0, math.cos(a + 0.9)); return 14.0 + 80.0 * s * s
    s = math.sin(phase)
    return P(legF=s * 42, legB=-s * 42, kneeF=-fold(phase), kneeB=-fold(phase + math.pi),
             armF=-s * 34 - 6, armB=s * 34 - 6, elbowF=70 + 25 * max(0, -s), elbowB=70 + 25 * max(0, s),
             lean=7, headTilt=-4, bag=-10 - math.sin(phase * 2) * 6)


BALANCE = dict(legF=4, legB=-2, kneeF=-8, kneeB=-8, armF=22, elbowF=34, armB=-16, elbowB=28, headTilt=-13)
KICK_ARMS = dict(armB=43, elbowB=29, armF=-28, elbowF=30)       # the kick's blend into the stand

# name, pose, has an (L) variant, yaws
POSES = [
    ('idle', P(kneeF=-5, kneeB=-5, armF=-3, armB=3, elbowF=14, elbowB=14), False, DEFAULT_YAWS),
    ('balance', P(**BALANCE), False, DEFAULT_YAWS),
    ('run_pass', run_pose(0.0), True, DEFAULT_YAWS),
    ('run_stride', run_pose(math.pi / 2), True, DEFAULT_YAWS),
    ('run_kneeup', run_pose(-0.9), True, DEFAULT_YAWS),
    ('jump_rise', P(legF=48, kneeF=-95, legB=-22, kneeB=-70, armF=-35, elbowF=85, armB=55, elbowB=60, lean=8, bag=-28), True, DEFAULT_YAWS),
    ('jump_fall', P(legF=18, kneeF=-25, legB=-12, kneeB=-35, armF=80, elbowF=30, armB=70, elbowB=25, lean=2, bag=14), True, DEFAULT_YAWS),
    ('tuck_0', P(legF=108, legB=96, kneeF=-138, kneeB=-132, armF=62, elbowF=95, armB=48, elbowB=100, headTilt=-24, lean=6, bag=-10), True, DEFAULT_YAWS),
    ('tuck_90', P(legF=108, legB=96, kneeF=-138, kneeB=-132, armF=62, elbowF=95, armB=48, elbowB=100, headTilt=-24, lean=96, bag=-10), False, DEFAULT_YAWS),
    ('tuck_180', P(legF=108, legB=96, kneeF=-138, kneeB=-132, armF=62, elbowF=95, armB=48, elbowB=100, headTilt=-24, lean=186, bag=-10), False, DEFAULT_YAWS),
    ('tuck_270', P(legF=108, legB=96, kneeF=-138, kneeB=-132, armF=62, elbowF=95, armB=48, elbowB=100, headTilt=-24, lean=276, bag=-10), False, DEFAULT_YAWS),
    ('kick_windup', P(legF=-30, kneeF=-100, kneeB=-14, lean=-6.5, **KICK_ARMS), True, DEFAULT_YAWS),
    ('kick_contact', P(legF=80, kneeF=0, kneeB=-14, lean=-8, **KICK_ARMS), True, DEFAULT_YAWS),
    ('slide', P(legF=24, kneeF=-6, legB=38, kneeB=-148, armB=-34, elbowB=10, armF=37, elbowF=30, headTilt=-44, lean=-58, bag=-95), True, DEFAULT_YAWS),
    ('landing', P(legF=30, legB=30, kneeF=-64, kneeB=-64, armF=-3, armB=3, elbowF=34, elbowB=34, lean=10), False, DEFAULT_YAWS),
    ('celebrate_air', P(legF=12, legB=-8, kneeF=-10, kneeB=-10, armF=172, armB=-172, elbowF=15, elbowB=15, headTilt=6), False, DEFAULT_YAWS),
    ('celebrate_crouch', P(legF=22, legB=2, kneeF=-55, kneeB=-55, armF=160, armB=-160, elbowF=15, elbowB=15), False, DEFAULT_YAWS),
    ('keepy_foot', P(**dict(BALANCE, legF=42, kneeF=-58, kneeB=-14, lean=-4)), True, MENU_YAWS),
    ('keepy_thigh', P(**dict(BALANCE, legF=86, kneeF=-96, kneeB=-12, lean=-4)), True, MENU_YAWS),
]


def cells(names, yaws_override):
    out = []
    for name, pose, has_l, yaws in POSES:
        if names and name not in names: continue
        ys = yaws_override or yaws
        out.append((name, pose, ys))
        if has_l: out.append((name + ' (L)', mirror(pose), ys))
    return out


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default

if '--list' in args:
    for name, pose, has_l, yaws in POSES:
        print('%-18s %s%s' % (name, ' '.join('%s %g' % (k, v) for k, v in pose.items() if v), '   (+ mirrored)' if has_l else ''))
    sys.exit(0)

blend, out = args[0], args[1]
yaws_override = tuple(float(v) for v in opt('--yaws').split(',')) if opt('--yaws') else None
names = opt('--poses').split(',') if opt('--poses') else None
CW, CH = (int(v) for v in opt('--cell', '360x480').split('x'))
SCALE_K = float(opt('--scale', '1.14'))
FOCUS = tuple(float(v) for v in opt('--focus').split(',')) if opt('--focus') else None
DIST = float(opt('--dist', '12'))
JOBS = int(opt('--jobs', '1'))
LEAKS = '--leaks' in args
BODY_ONLY = '--body-only' in args
worker = opt('--worker')                 # 'i/n': render every n-th cell, write tiles (spawned by the driver)
tiles = opt('--tiles')
CELLS = cells(names, yaws_override)
GRID = [(c[0], c[1], y) for c in CELLS for y in c[2]]
HEAD = 24                      # a strip above each cell for its label


# ---------------------------------------------------------------------------------------------
# Driver: spawn the workers, then compose the sheet(s).
def compose():
    from PIL import Image, ImageDraw, ImageFont
    try: font = ImageFont.load_default(size=15)
    except Exception: font = ImageFont.load_default()
    info = json.load(open(os.path.join(tiles, 'leaks.json'))) if LEAKS else {}
    n_poses = len(CELLS)
    per_row = 2
    ny = max(len(c[2]) for c in CELLS)
    rows = (n_poses + per_row - 1) // per_row
    for kind, path in (('tile', out),) + ((('leak', out[:-4] + '_leaks.png'),) if LEAKS else ()):
        sheet = Image.new('RGB', (per_row * ny * CW, rows * (CH + HEAD)), (62, 62, 66))
        d = ImageDraw.Draw(sheet)
        k = 0
        for pi, (name, pose, ys) in enumerate(CELLS):
            for yi, y in enumerate(ys):
                x0 = ((pi % per_row) * ny + yi) * CW; y0 = (pi // per_row) * (CH + HEAD)
                im = Image.open(os.path.join(tiles, '%s_%04d.png' % (kind, k))).convert('RGB')
                sheet.paste(im, (x0, y0 + HEAD))
                label = '%s  yaw %g' % (name, y)
                if LEAKS and str(k) in info and info[str(k)]: label += '   skin %d px' % info[str(k)]
                d.rectangle([x0, y0, x0 + CW - 1, y0 + HEAD - 1], fill=(36, 36, 40))
                d.text((x0 + 8, y0 + 3), label, fill=(255, 235, 140) if info.get(str(k), 0) else (230, 230, 235), font=font)
                k += 1
        sheet.save(path); print('sheet', path, sheet.size)


if worker is None and JOBS > 1:
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(out)), '_poses_tmp'), ignore_errors=True)
    tiles = os.path.join(os.path.dirname(os.path.abspath(out)), '_poses_tmp'); os.makedirs(tiles)
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), '--'] + args + ['--worker', '%d/%d' % (i, JOBS), '--tiles', tiles])
             for i in range(JOBS)]
    for p in procs: p.wait()
    if any(p.returncode for p in procs): sys.exit('a worker failed')
    if LEAKS:
        merged = {}
        for i in range(JOBS): merged.update(json.load(open(os.path.join(tiles, 'leaks_%d.json' % i))))
        json.dump(merged, open(os.path.join(tiles, 'leaks.json'), 'w'))
        for k in sorted(merged, key=int):
            if merged[k]: print('cell %s  %s yaw %g  skin %d px' % (k, GRID[int(k)][0], GRID[int(k)][2], merged[k]))
    compose()
    shutil.rmtree(tiles, ignore_errors=True)
    sys.exit(0)

# ---------------------------------------------------------------------------------------------
# Rendering (in this process: the only one, or one worker)
import bpy
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene
kid = bpy.data.objects['Kid']; rig = bpy.data.objects['KidRig']
me = kid.data

# The leak flags: body faces that lie under another piece (clothes, hair, head) at rest. The body is
# the first piece of the joined mesh: the connected island of polygon 0.
leak_flags = None
if LEAKS or BODY_ONLY:
    nv = len(me.vertices)
    parent = list(range(nv))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for p in me.polygons:
        r = find(p.vertices[0])
        for v in p.vertices[1:]:
            q = find(v)
            if q != r: parent[q] = r
    root = find(me.polygons[0].vertices[0])
    body = np.array([find(p.vertices[0]) == root for p in me.polygons])
    V = np.empty(nv * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    if BODY_ONLY:
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not body[f.index]], context='FACES')
        bm.to_mesh(me); bm.free(); me.update()
        LEAKS = False
if LEAKS:
    others = [tuple(p.vertices) for p, b in zip(me.polygons, body) if not b]
    bvh = BVHTree.FromPolygons([tuple(v) for v in V], others, epsilon=0.0)
    W = {g.index: g.name for g in kid.vertex_groups}
    def dominant(v):
        return W[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else ''
    leak_flags = np.zeros(len(me.polygons), bool)
    for p in me.polygons:
        if not body[p.index]: continue
        if not all(dominant(me.vertices[v]).startswith(('Hips', 'Spine', 'Chest', 'Neck', 'UpperLeg', 'LowerLeg', 'Foot')) for v in p.vertices): continue
        c = Vector(p.center); n = Vector(p.normal)
        hit = bvh.ray_cast(c + n * 1e-4, n, 0.03)
        if hit[0] is not None: leak_flags[p.index] = True
    print('skin faces under clothes at rest:', int(leak_flags.sum()), 'of', int(body.sum()))

# ---- the game's toon shading (as in review_teen.py) ----
SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
mat = kid.data.materials[0]; nt = mat.node_tree
mix = [n for n in nt.nodes if n.type == 'MIX'][0]
L = nt.nodes.new('ShaderNodeCombineXYZ')
geo = nt.nodes.new('ShaderNodeNewGeometry')
dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
lit = nt.nodes.new('ShaderNodeMapRange'); lit.interpolation_type = 'SMOOTHSTEP'
lit.inputs['From Min'].default_value = -0.02; lit.inputs['From Max'].default_value = 0.06
nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
band = nt.nodes.new('ShaderNodeMix'); band.data_type = 'RGBA'
band.inputs['A'].default_value = SHADE + (1,); band.inputs['B'].default_value = SUN + (1,)
nt.links.new(lit.outputs['Result'], band.inputs['Factor'])
m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
nt.links.new(mix.outputs['Result'], m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
rim = nt.nodes.new('ShaderNodeMapRange'); rim.interpolation_type = 'SMOOTHSTEP'
rim.inputs['From Min'].default_value = 0.4; rim.inputs['From Max'].default_value = 0.24
rim.inputs['To Min'].default_value = 0.0; rim.inputs['To Max'].default_value = 1.0
nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
side = nt.nodes.new('ShaderNodeMapRange'); side.inputs['From Min'].default_value = -0.35; side.inputs['From Max'].default_value = 0.65
side.inputs['To Min'].default_value = 0.4; side.inputs['To Max'].default_value = 1.0
nt.links.new(dot.outputs['Value'], side.inputs['Value'])
rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'
nt.links.new(rim.outputs['Result'], rk.inputs[0]); nt.links.new(side.outputs['Result'], rk.inputs[1])
rk2 = nt.nodes.new('ShaderNodeMath'); rk2.operation = 'MULTIPLY'; rk2.inputs[1].default_value = 0.22
nt.links.new(rk.outputs[0], rk2.inputs[0])
add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
add.inputs['B'].default_value = SUN + (1,)
nt.links.new(rk2.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
kid.data.materials.append(ol)
sol = kid.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = 0.005; sol.offset = 1; sol.use_flip_normals = True; sol.material_offset = 1
mat.use_backface_culling = True
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
try: S.eevee.taa_render_samples = 8
except Exception: pass
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()      # the game's sun in the review camera's world (see review_teen.py)
L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR

# the leak pass: flat colour, the covered skin in magenta
leak_mat = None
if LEAKS:
    me.color_attributes.new('Leak', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.render_color_index = me.color_attributes.keys().index('Col')
    me.color_attributes.active_color = me.color_attributes['Col']
    la = me.color_attributes['Leak']
    for p in me.polygons:
        c = (1, 0, 1, 1) if leak_flags[p.index] else (0.25, 0.25, 0.27, 1)
        for li in p.loop_indices: la.data[li].color = c
    leak_mat = bpy.data.materials.new('LeakMat'); leak_mat.use_nodes = True
    ln = leak_mat.node_tree; vcn = ln.nodes.new('ShaderNodeVertexColor'); vcn.layer_name = 'Leak'
    le = ln.nodes.new('ShaderNodeEmission'); ln.links.new(vcn.outputs['Color'], le.inputs['Color'])
    ln.links.new(le.outputs[0], ln.nodes['Material Output'].inputs['Surface'])
    leak_mat.use_backface_culling = True

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
S.render.resolution_x, S.render.resolution_y = CW, CH
S.render.film_transparent = False

# ---- posing, as CharacterRig does it ----
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
side_axis = Vector((1, 0, 0))        # the character's side axis in the rig's own space (it faces -Y)
def swing(bone, game_angle, sign=-1):
    """Rotate a bone about the side axis by a game angle (positive: forward for a limb hanging down)."""
    pb = rig.pose.bones[bone]
    axis = pb.bone.matrix_local.to_3x3().inverted() @ side_axis       # the axis in the bone's rest frame
    pb.rotation_quaternion = Quaternion(axis, math.radians(sign * game_angle))

def pose(p):
    for pb in rig.pose.bones: pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    # the right limbs are the "front" ones (the near side); the game folds knees only backward
    # and flexes elbows only forward
    for n, f in (('R', 'F'), ('L', 'B')):
        swing('UpperLeg.' + n, p['leg' + f]); swing('LowerLeg.' + n, min(p['knee' + f], 0))
        swing('UpperArm.' + n, p['arm' + f]); swing('LowerArm.' + n, max(p['elbow' + f], 0))
    if 'Bag' in rig.pose.bones: swing('Bag', p['bag'])
    swing('Head', p['headTilt'])
    swing('Hips', p['lean'], sign=+1)      # a forward lean tips the top toward -Y (forward): +X

def world_bounds():
    dg = C.evaluated_depsgraph_get(); ev = kid.evaluated_get(dg); m = ev.to_mesh()
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    M = np.array(ev.matrix_world); V = V @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    return V.min(0), V.max(0)

def render(path):
    S.render.filepath = path; bpy.ops.render.render(write_still=True)

def count_magenta(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    return int(((a[..., 0] > 200) & (a[..., 1] < 60) & (a[..., 2] > 200)).sum())

lo, hi = world_bounds()
H0 = hi[2] - lo[2]
SCALE = H0 * SCALE_K                       # the height one cell frames, metres: the standing model's height and a margin
if FOCUS: SCALE = H0 * (FOCUS[1] - FOCUS[0]) * 1.08
if DIST > 0:
    cam.data.type = 'PERSP'; cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle = 2 * math.atan(SCALE / 2 / DIST)
else:
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = SCALE
wi, wn = (int(v) for v in worker.split('/')) if worker else (0, 1)
tmp = tiles or os.path.join(os.path.dirname(os.path.abspath(out)), '_poses_tmp')
os.makedirs(tmp, exist_ok=True)
leaks = {}
for k, (name, p, yaw) in enumerate(GRID):
    if k % wn != wi: continue
    pose(p)
    rig.rotation_euler = (0, 0, math.radians(yaw))
    C.view_layer.update()
    lo, hi = world_bounds()
    c = (lo + hi) / 2
    if FOCUS: c[2] = lo[2] + H0 * (FOCUS[0] + FOCUS[1]) / 2
    # a pose wider or taller than the cell (the slide, the tuck) gets a bigger frame, so nothing is cut off
    scale = SCALE if FOCUS else max(SCALE, (hi[2] - lo[2]) * 1.09, (hi[0] - lo[0]) * 1.09 * CH / CW)
    if DIST > 0: cam.data.angle = 2 * math.atan(scale / 2 / DIST)
    else: cam.data.ortho_scale = scale
    cam.location = (c[0], -(DIST if DIST > 0 else 6.0), c[2]); cam.rotation_euler = (math.radians(90), 0, 0)
    sol.thickness = 0.0045
    S.render.film_transparent = False
    kid.data.materials[0] = mat
    render(os.path.join(tmp, 'tile_%04d.png' % k))
    if LEAKS:
        # flat, unshaded, unsmoothed: the exact pixels the covered skin shows in
        kid.data.materials[0] = leak_mat; sol.show_viewport = False; sol.show_render = False
        S.view_settings.view_transform = 'Standard'
        try: S.eevee.taa_render_samples = 1
        except Exception: pass
        S.render.film_transparent = True
        render(os.path.join(tmp, 'leak_%04d.png' % k))
        leaks[str(k)] = count_magenta(os.path.join(tmp, 'leak_%04d.png' % k))
        # composite: the toon render with the covered skin painted magenta
        from PIL import Image
        base = Image.open(os.path.join(tmp, 'tile_%04d.png' % k)).convert('RGB')
        lk = np.asarray(Image.open(os.path.join(tmp, 'leak_%04d.png' % k)).convert('RGB')).astype(int)
        mask = (lk[..., 0] > 200) & (lk[..., 1] < 60) & (lk[..., 2] > 200)
        arr = np.asarray(base).copy(); arr[mask] = (255, 0, 255)
        Image.fromarray(arr).save(os.path.join(tmp, 'leak_%04d.png' % k))
        sol.show_viewport = True; sol.show_render = True
        try: S.eevee.taa_render_samples = 8
        except Exception: pass
    print('cell', k, name, 'yaw', yaw, ('skin %d px' % leaks[str(k)]) if LEAKS else '')

if worker is not None:
    if LEAKS: json.dump(leaks, open(os.path.join(tmp, 'leaks_%d.json' % wi), 'w'))
else:
    if LEAKS:
        json.dump(leaks, open(os.path.join(tmp, 'leaks.json'), 'w'))
        for k, v in leaks.items():
            if v: print('cell %s  %s yaw %g  skin %d px' % (k, GRID[int(k)][0], GRID[int(k)][2], v))
    tiles = tmp
    compose()
    shutil.rmtree(tmp, ignore_errors=True)
