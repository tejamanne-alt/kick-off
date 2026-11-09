# The kid dribbling slowly (the stick's gentlest push, KICK held: about a fifth of a run, a touch every 0.41 s) with the
# old run cycle and with the new gait (gait.py: KidAnimator's leg angles, ported), in the game's look, the camera
# following as the game's does, paving joints on the ground to show whether the planted foot stays put.
#   blenv/bin/python render_gait.py -- <models dir> <out dir>   ->  <out dir>/old_###.png, new_###.png
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:]
sys.argv = sys.argv[:sys.argv.index('--') + 1] + [argv[0], argv[1], 'gait']
src = open(os.path.join(HERE, '..', 'cartoon', 'render_scenes.py')).read()
exec(src[:src.index('SCENES = dict(')])
sys.path.insert(0, HERE)
import gait

PACE, TOUCH_EVERY, SECONDS, FPS = 0.21, 0.41, 2.4, 30
street(road=True, footpath=(0.74, 0.71, 0.70))
for i in range(-20, 60):                      # paving joints, every half metre
    box('Joint%d' % i, (i * 0.5, 0.0, 0.001), (0.025, 5.0, 0.004), plain('Joint', (0.55, 0.53, 0.53)))
for i in range(-10, 40):
    kit('Street', 'PicketFence2', (i * 2.0 + 1.0, 2.7, 0.0))
objs = person('PrimaryGirl', (0.0, 0.4, 0.0), 66, 'idle', 1.27)
rig = [o for o in objs if o.type == 'ARMATURE'][0]
bpy.context.view_layer.update()
W = lambda b: rig.matrix_world @ rig.pose.bones[b].head
neck_r = W('Head').z; hip_r = W('UpperLeg.L').z
k = neck_r / 1.3                                  # render metres per game unit (the kid's neck is 1.3 units)
L_game = hip_r / k
x0, base = rig.location.x, rig.location.copy()
print('neck %.3f hip %.3f k %.3f leg %.3f game units' % (neck_r, hip_r, k, L_game))
b = ball((0.0, 0.4, 0.0), r=0.11)
side = Vector((1, 0, 0))

def swing(bone, a, sign=-1):
    if bone not in rig.pose.bones: return
    pb = rig.pose.bones[bone]
    axis = pb.bone.matrix_local.to_3x3().inverted() @ side
    pb.rotation_quaternion = Quaternion(axis, math.radians(sign * a))

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(24)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = math.pi; sun.rotation_euler = (-SUNDIR).to_track_quat('-Z', 'Y').to_euler()
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.68, 0.92, 1)
S.render.engine = 'BLENDER_EEVEE'; S.render.resolution_x, S.render.resolution_y = 640, 400
S.view_settings.view_transform = 'Standard'; S.eevee.taa_render_samples = 8
set_pass('colour')

for name, cls in (('old', gait.Old), ('new', gait.New)):
    a = cls(); t = 0.0; x = 0.0; nt = 0.2; dt = 1.0 / 60; frame = 0; step = 0
    v = PACE * gait.RUN_SPEED
    while t < SECONDS:
        if t >= nt: a.touch(t); nt += TOUCH_EVERY
        p = a.pose(t, dt, v, L_game); x += v * dt; t += dt; step += 1
        if step % (60 // FPS): continue
        for pb in rig.pose.bones:
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
        for n, f in (('R', 'F'), ('L', 'B')):
            swing('UpperLeg.' + n, p['leg' + f]); swing('LowerLeg.' + n, min(p['knee' + f], 0))
            swing('UpperArm.' + n, p['arm' + f]); swing('LowerArm.' + n, max(p['elbow' + f], 0))
        swing('Hips', p['lean'], sign=+1)
        X = x * k
        rig.location = base + Vector((X, 0, 0))
        b.location = (x0 + X + 0.36 * k, 0.4, 0.11); b.rotation_euler = (0.4, -X / 0.11, 0.2)
        cam.location = (x0 + X + 0.3, -5.2, 0.95)
        cam.rotation_euler = (Vector((x0 + X + 0.3, 0.4, 0.62)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        S.render.filepath = os.path.join(OUT, '%s_%03d.png' % (name, frame)); bpy.ops.render.render(write_still=True)
        frame += 1
    print('rendered', name, frame)
