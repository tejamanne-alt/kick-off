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
#       [--tint 0.8,0.05,0.05,0.278]   the bags' cloth recoloured (linear r,g,b, then the cloth's own luminance:
#                              Bag<Id>.json) as the game's Settings colour does
#       [--bag Bag_RaceCar]    which of the kid's bags to show (the first by default; none: no bag)
#       [--list]               list the poses and exit
#       [--walker]             a passer-by's poses instead of the kid's (WALKER_POSES, WalkerAnimator.cs ported line by
#                              line): its stroll cycle (walk_00..23), chatting (chat_00..23: the hands going, nodding)
#                              and waiting at the kerb (wait_00..23)
#       [--views8]             the standing figure from all eight sides (front, back, left, right, the two
#                              three-quarters from a little above, top, bottom): docs/ASSET_REVIEW.md, section 1
#       [--outfit "r,g,b;r,g,b;r,g,b" --outfit-from /abs/<Name>.json]   dress parts 1, 2 and 3 (top, legwear, the
#                              third: hair, a cap, a randoseru) in these colours ("-" keeps one) as ModelOutfit.cs
#                              does: each vertex the new colour times its brightness over its part's default (the json)
#       [--frames /abs/dir]    also keep each cell as dir/<pose>.png, framed the same in every cell (the
#                              standing figure's frame, not each pose's own), for a motion's animated preview
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
    d = dict(legF=0, legB=0, kneeF=-4, kneeB=-4, armF=0, armB=0, elbowF=12, elbowB=12, lean=0, headTilt=0, bag=0, bob=0)
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
             lean=7, headTilt=0.75 * 7 - 2 - 2.5 * math.cos(2 * (phase - 0.35)), bag=-10 - math.sin(phase * 2) * 6)   # (KidAnimator.RunHeadTilt)


BALANCE = dict(legF=4, legB=-2, kneeF=-8, kneeB=-8, armF=22, elbowF=34, armB=-16, elbowB=28, headTilt=-13)
KICK_ARMS = dict(armB=43, elbowB=29, armF=-28, elbowF=30)       # the kick's blend into the stand
# the double jump (KidAnimator): launch (stretched tall, arms thrown up), the tuck (spun a quarter turn at a time, the bag
# flung out behind), and the open-out (legs reaching for the ground, arms wide)
LAUNCH = dict(legF=6, kneeF=-12, legB=-8, kneeB=-28, armF=128, elbowF=12, armB=118, elbowB=12, lean=8, bag=-10)
TUCK = dict(legF=108, legB=96, kneeF=-138, kneeB=-132, armF=62, elbowF=95, armB=48, elbowB=100, headTilt=-26, bag=-36)
OPEN = dict(legF=28, kneeF=-24, legB=-12, kneeB=-34, armF=88, elbowF=30, armB=-34, elbowB=26, lean=8, bag=-6)

# name, pose, has an (L) variant, yaws
POSES = [
    ('idle', P(kneeF=-5, kneeB=-5, armF=-3, armB=3, elbowF=14, elbowB=14), False, DEFAULT_YAWS),
    ('balance', P(**BALANCE), False, DEFAULT_YAWS),
    ('run_pass', run_pose(0.0), True, DEFAULT_YAWS),
    ('run_stride', run_pose(math.pi / 2), True, DEFAULT_YAWS),
    ('run_kneeup', run_pose(-0.9), True, DEFAULT_YAWS),
    ('jump_rise', P(legF=48, kneeF=-95, legB=-22, kneeB=-70, armF=-35, elbowF=85, armB=55, elbowB=60, lean=8, bag=-25), True, DEFAULT_YAWS),
    ('jump_fall', P(legF=18, kneeF=-25, legB=-12, kneeB=-35, armF=80, elbowF=30, armB=70, elbowB=25, lean=2, bag=24), True, DEFAULT_YAWS),
    ('launch', P(**LAUNCH), False, DEFAULT_YAWS),
    ('tuck_0', P(lean=6, **TUCK), True, DEFAULT_YAWS),
    ('tuck_90', P(lean=96, **TUCK), False, DEFAULT_YAWS),
    ('tuck_180', P(lean=186, **TUCK), False, DEFAULT_YAWS),
    ('tuck_270', P(lean=276, **TUCK), False, DEFAULT_YAWS),
    ('open', P(**OPEN), True, DEFAULT_YAWS),
    ('kick_windup', P(legF=-30, kneeF=-100, kneeB=-14, lean=-6.5, **KICK_ARMS), True, DEFAULT_YAWS),
    ('kick_contact', P(legF=80, kneeF=0, kneeB=-14, lean=-6.5, **KICK_ARMS), True, DEFAULT_YAWS),
    # the slide dives in with an overshoot (the lean 10% over its 58, as limbs are written relative to the lean), then settles
    ('slide_lunge', P(legF=19, kneeF=-6, legB=71, kneeB=-80, armB=-40, elbowB=10, armF=31, elbowF=30, headTilt=-44, lean=-64, bag=-95), True, DEFAULT_YAWS),
    ('slide', P(legF=24, kneeF=-6, legB=77, kneeB=-80, armB=-34, elbowB=10, armF=37, elbowF=30, headTilt=-44, lean=-58, bag=-95), True, DEFAULT_YAWS),
    ('landing', P(legF=30, legB=30, kneeF=-64, kneeB=-64, armF=-3, armB=3, elbowF=34, elbowB=34, lean=10), False, DEFAULT_YAWS),
    ('celebrate_air', P(legF=12, legB=-8, kneeF=-10, kneeB=-10, armF=172, armB=-172, elbowF=15, elbowB=15, headTilt=6), False, DEFAULT_YAWS),
    ('celebrate_crouch', P(legF=22, legB=2, kneeF=-55, kneeB=-55, armF=160, armB=-160, elbowF=15, elbowB=15), False, DEFAULT_YAWS),
    ('keepy_foot', P(**dict(BALANCE, legF=42, kneeF=-58, kneeB=-14, lean=-4)), True, MENU_YAWS),
    ('keepy_thigh', P(**dict(BALANCE, legF=86, kneeF=-96, kneeB=-12, lean=-4)), True, MENU_YAWS),
]


# ---- a passer-by's poses: WalkerAnimator.cs, line by line ----
def walker_knee(leg_phase):
    """WalkerAnimator.Knee."""
    sw = max(0.0, math.cos(leg_phase + 0.9))
    return 5.0 + 35.0 * sw * sw


def walker_pose(phase, amp=1.0, stoop=0.0, swing=25.0):
    """WalkerAnimator.LateUpdate's stroll at a stride phase: amp the stride's share of its full (speed / 0.9, clamped)."""
    lerp = lambda a, b, t: a + (b - a) * t
    if stoop > 0: amp *= 0.8
    s = math.sin(phase)
    p = P(bob=abs(math.cos(phase)) * 0.03 * amp, legF=s * swing * amp, legB=-s * swing * amp,
          armF=-s * swing * 0.7 * amp, armB=s * swing * 0.7 * amp,
          kneeF=lerp(-4.0, -walker_knee(phase), amp), kneeB=lerp(-4.0, -walker_knee(phase + math.pi), amp),
          elbowF=12.0 + (4.0 + 12.0 * max(0.0, -s)) * amp, elbowB=12.0 + (4.0 + 12.0 * max(0.0, s)) * amp,
          lean=2.0 * amp + stoop)
    if stoop > 0: p['headTilt'] = stoop * 0.4
    return p


def walker_gesture(kind, t):
    """WalkerAnimator.Perform at full weight, stopped (amp 0), at time t seconds."""
    p = walker_pose(0.0, amp=0.0)
    if kind == 'chat':
        p.update(armF=10 + math.sin(t * 1.3) * 9, elbowF=40 + 30 * max(0.0, math.sin(t * 2.2)),
                 armB=4 + math.sin(t * 0.9 + 1) * 5, elbowB=20 + 18 * max(0.0, math.sin(t * 1.7 + 2)),
                 headTilt=math.sin(t * 1.9) * 6)
    elif kind == 'wait':
        p.update(lean=math.sin(t * 0.6) * 1.5, headTilt=math.sin(t * 0.4) * 4)
    return p


# a stride cycle in 24 frames; chatting over one nod (2 pi / 1.9 s); waiting over one sway of the head (2 pi / 0.4 s)
WALKER_POSES = ([('walk_%02d' % k, walker_pose(2 * math.pi * k / 24), False, (66,)) for k in range(24)] +
                [('chat_%02d' % k, walker_gesture('chat', 2 * math.pi / 1.9 * k / 24), False, (24,)) for k in range(24)] +
                [('wait_%02d' % k, walker_gesture('wait', 2 * math.pi / 0.4 * k / 24), False, (66,)) for k in range(24)])
# the eight views (docs/ASSET_REVIEW.md, section 1): yaw as above, and the camera's elevation in degrees
VIEWS8 = [('Front', 0, 0), ('Back', 180, 0), ('Left', -90, 0), ('Right', 90, 0), ('Left 3/4', -45, 20),
          ('Right 3/4', 45, 20), ('Top', 0, 90), ('Bottom', 0, -90)]
ELEV = {}


def cells(names, yaws_override):
    out = []
    if '--views8' in sys.argv:
        for name, yaw, elev in VIEWS8:
            ELEV[name] = elev
            out.append((name, P(kneeF=-5, kneeB=-5, armF=-3, armB=3, elbowF=14, elbowB=14), (yaw,)))
        return out
    for name, pose, has_l, yaws in (WALKER_POSES if '--walker' in sys.argv else POSES):
        if names and name not in names: continue
        ys = yaws_override or yaws
        out.append((name, pose, ys))
        if has_l: out.append((name + ' (L)', mirror(pose), ys))
    return out


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default

if '--list' in args:
    for name, pose, has_l, yaws in (WALKER_POSES if '--walker' in args else POSES):
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
FRAMES = opt('--frames')                 # keep each cell as <dir>/<pose>.png, all framed alike
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
    per_row = 4 if '--views8' in args else 2
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


def keep_frames(tiles):
    if not FRAMES: return
    os.makedirs(FRAMES, exist_ok=True)
    for k, (name, _, _) in enumerate(GRID):
        shutil.copy2(os.path.join(tiles, 'tile_%04d.png' % k), os.path.join(FRAMES, name.replace(' ', '_').replace('/', '') + '.png'))


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
    keep_frames(tiles)
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
def toon(mat, tint=None):
    """The toon look on a material made by meshy_boy.atlas_material (its atlas times its vertex colours); with tint, the
    atlas's cloth (alpha 0, meshy_bag.py) recoloured as ToonCharacter's _MaskTint does."""
    nt = mat.node_tree
    mix = [n for n in nt.nodes if n.type == 'MIX'][0]
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    tex.image.alpha_mode = 'CHANNEL_PACKED'                    # (a bag's alpha is its cloth mask, not coverage)
    if tint is not None:
        lum = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(tex.outputs['Color'], lum.inputs[0])
        k = nt.nodes.new('ShaderNodeMath'); k.operation = 'DIVIDE'; k.inputs[1].default_value = tint[3]
        nt.links.new(lum.outputs[0], k.inputs[0])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
        nt.links.new(tex.outputs['Alpha'], inv.inputs[1])
        pick = nt.nodes.new('ShaderNodeMix'); pick.data_type = 'RGBA'
        nt.links.new(inv.outputs[0], pick.inputs['Factor']); nt.links.new(tex.outputs['Color'], pick.inputs['A'])
        # (tint times the texel's luminance over the cloth's own)
        sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
        sc.inputs[0].default_value = tuple(tint[:3]); nt.links.new(k.outputs[0], sc.inputs['Scale'])
        nt.links.new(sc.outputs[0], pick.inputs['B'])
        nt.links.new(pick.outputs['Result'], mix.inputs['A'])
    _l = nt.nodes.new('ShaderNodeCombineXYZ'); LS.append(_l); L = _l
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
    rim.inputs['From Min'].default_value = 0.34; rim.inputs['From Max'].default_value = 0.2
    rim.inputs['To Min'].default_value = 0.0; rim.inputs['To Max'].default_value = 1.0
    nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
    side = nt.nodes.new('ShaderNodeMapRange'); side.inputs['From Min'].default_value = -0.35; side.inputs['From Max'].default_value = 0.65
    side.inputs['To Min'].default_value = 0.4; side.inputs['To Max'].default_value = 1.0
    nt.links.new(dot.outputs['Value'], side.inputs['Value'])
    rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'
    nt.links.new(rim.outputs['Result'], rk.inputs[0]); nt.links.new(side.outputs['Result'], rk.inputs[1])
    rk2 = nt.nodes.new('ShaderNodeMath'); rk2.operation = 'MULTIPLY'; rk2.inputs[1].default_value = 0.22
    nt.links.new(rk.outputs[0], rk2.inputs[0])
    # the rim's colour, as ToonCharacter: the albedo whitened by 45% of its lightness (its brightest channel), times the sun
    _sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(mix.outputs['Result'], _sep.inputs['Color'])
    _m1 = nt.nodes.new('ShaderNodeMath'); _m1.operation = 'MAXIMUM'; nt.links.new(_sep.outputs[0], _m1.inputs[0]); nt.links.new(_sep.outputs[1], _m1.inputs[1])
    _m2 = nt.nodes.new('ShaderNodeMath'); _m2.operation = 'MAXIMUM'; nt.links.new(_m1.outputs[0], _m2.inputs[0]); nt.links.new(_sep.outputs[2], _m2.inputs[1])
    _fk = nt.nodes.new('ShaderNodeMath'); _fk.operation = 'MULTIPLY'; _fk.inputs[1].default_value = 0.45; nt.links.new(_m2.outputs[0], _fk.inputs[0])
    _tint = nt.nodes.new('ShaderNodeMix'); _tint.data_type = 'RGBA'; nt.links.new(_fk.outputs[0], _tint.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], _tint.inputs['A']); _tint.inputs['B'].default_value = (1, 1, 1, 1)
    _tsun = nt.nodes.new('ShaderNodeMix'); _tsun.data_type = 'RGBA'; _tsun.blend_type = 'MULTIPLY'; _tsun.inputs['Factor'].default_value = 1
    nt.links.new(_tint.outputs['Result'], _tsun.inputs['A']); _tsun.inputs['B'].default_value = SUN + (1,)
    add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
    nt.links.new(_tsun.outputs['Result'], add.inputs['B'])
    nt.links.new(rk2.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    mat.use_backface_culling = True


def dress(me, outfit, defaults):
    """ModelOutfit.Dress: part k's vertices (UV2.x) take outfit[k - 1] times (their colour's sum over the part's default's),
    in the colours as stored (sRGB bytes)."""
    if len(me.uv_layers) < 2 or 'Col' not in me.color_attributes: return
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[1].data.foreach_get('uv', uv)
    part = np.round(uv.reshape(-1, 2)[:, 0]).astype(int)
    col = me.color_attributes['Col']
    for li, d in enumerate(col.data):
        k = part[li]
        if k < 1 or k > 3 or outfit[k - 1] is None: continue
        c = d.color_srgb
        f = (c[0] + c[1] + c[2]) / max(0.01, sum(defaults[k - 1]))
        to = outfit[k - 1]
        d.color_srgb = (min(1.0, to[0] * f), min(1.0, to[1] * f), min(1.0, to[2] * f), c[3])


if opt('--outfit'):
    _d = json.load(open(opt('--outfit-from')))
    dress(me, [None if t.strip() == '-' else [float(x) for x in t.split(',')] for t in opt('--outfit').split(';')],
          [_d['top'], _d['legwear'], _d['hair']])

LS = []
TINT = None
if '--tint' in args:
    TINT = [float(x) for x in args[args.index('--tint') + 1].split(',')]   # r,g,b (linear),cloth luminance
mat = kid.data.materials[0]
toon(mat)
BAGS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Bag_')]
if BAGS:
    # one bag on at a time, as in the game (BagWear): --bag Bag_RaceCar, else the first; --bag none for no bag
    wear = args[args.index('--bag') + 1] if '--bag' in args else BAGS[0].name
    off = [b for b in BAGS if b.name != wear]
    BAGS = [b for b in BAGS if b.name == wear]
    for b in off: bpy.data.objects.remove(b)
for b in BAGS: toon(b.data.materials[0], TINT)
ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
on = ol.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
# the outline: hull copies of the figure and its bag set back from the camera (ink_hull.py; docs/LEARNINGS.md C20)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ink_hull
hull, sol = ink_hull.make(kid, ol, 0.005)
BAG_HULLS = [ink_hull.make(b, ol, 0.005) for b in BAGS]
S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'
try: S.eevee.taa_render_samples = 8
except Exception: pass
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()      # the game's sun in the review camera's world (see review_teen.py)
for _l in LS: _l.inputs[0].default_value, _l.inputs[1].default_value, _l.inputs[2].default_value = SUNDIR

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

NECK_M = rig.data.bones['Head'].head_local.z * rig.matrix_world.to_scale().z   # (the game scales by its neck)
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
    # (a bag of the Locker Room's swings less than one sewn on: LevelBuildKit sets CharacterRig.bagSwing so)
    if 'Bag' in rig.pose.bones: swing('Bag', p['bag'] * (0.3 if BAGS else 1.0))
    swing('Head', p['headTilt'])
    swing('Hips', p['lean'], sign=+1)      # a forward lean tips the top toward -Y (forward): +X
    # the stroll's bob (RigPose.bob, game units: the kid's neck at 1.3 of them), in the model's own height
    rig.location.z = p.get('bob', 0.0) * NECK_M / 1.3

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
# the standing figure's frame (--frames, --views8): its middle, and room for it turned any way and from above
REST_C = (lo + hi) / 2
REST_SCALE = max(SCALE, (max(hi[0] - lo[0], hi[1] - lo[1]) * 1.3) * CH / CW) if ELEV else SCALE
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
    if FRAMES or ELEV:                     # every cell framed as the standing figure is: a motion's frames line up
        c = REST_C.copy(); scale = REST_SCALE
    if DIST > 0: cam.data.angle = 2 * math.atan(scale / 2 / DIST)
    else: cam.data.ortho_scale = scale
    e = math.radians(ELEV.get(name, 0))
    d = DIST if DIST > 0 else 6.0
    cam.location = (c[0], c[1] - d * math.cos(e), c[2] + d * math.sin(e))
    cam.rotation_euler = (math.radians(90) - e, 0, 0)
    sol.thickness = 0.0045
    for bh, bs in BAG_HULLS: bs.thickness = 0.0045
    _co = np.empty(len(kid.data.vertices) * 3); kid.data.vertices.foreach_get('co', _co)   # (bpy 5 takes no slice steps)
    _z = (_co.reshape(-1, 3)[::50] @ np.array(kid.matrix_world)[:3, :3].T)[:, 2]
    _top = _z.max() - _z.min()
    ink_hull.set_back(hull, kid, (0, 1, 0), ink_hull.PUSH * _top / 1.6)
    for (bh, bs), b in zip(BAG_HULLS, BAGS): ink_hull.set_back(bh, b, (0, 1, 0), ink_hull.PUSH * _top / 1.6)
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
    keep_frames(tmp)
    shutil.rmtree(tmp, ignore_errors=True)
