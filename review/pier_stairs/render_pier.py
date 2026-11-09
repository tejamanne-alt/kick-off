# The pier on a California beach with its new stairs, in the game's toon look, from three cameras:
#   blenv/bin/python render_pier.py -- <models dir> <out dir> [before]
# Writes game.png (the game's camera, a phone's width), whole.png (the whole front) and close.png (the left flight close up),
# each RGBA with the sky left transparent (compose.py lays in the sky). "before" leaves the stairs out.
# Uses review/cartoon/render_scenes.py for the toon materials and the kit models, and pier_stairs.py for the stairs.
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index('--') + 1:]
BEFORE = 'before' in argv
sys.argv = sys.argv[:sys.argv.index('--') + 1] + [argv[0], argv[1], 'pier']
src = open(os.path.join(HERE, '..', 'cartoon', 'render_scenes.py')).read()
exec(src[:src.index('SCENES = dict(')])
import bmesh
import pier_stairs as ps

SEA_Y = -0.3                 # the sea, 0.3 under the beach (StreetBuilder.Beach)
DECK = SEA_Y + 4.8           # the pier's deck (Coast/PierSpan)
PIER_X, PIER_Z = 0.0, 6.2    # where StreetBuilder puts the pier's near end
DEPTH, WIDTH = 1.9, 6.0


def ease(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def sand_y(x, z):
    """SandField.Height on the open beach (baseTop 0): flat, a little lower where it turns wet, then down under the sea."""
    return -0.12 * ease((z - 5.6) / 1.4) - 0.44 * ease((z - 8.6) / 2.4)


def unity_mesh(name, mb, mat):
    """A MeshBuilder's mesh (Unity axes, Unity winding) as a Blender object, its colours in the 'Col' attribute."""
    me = bpy.data.meshes.new(name)
    verts = [(x, z, y) for (x, y, z) in mb.v]            # Unity (x, y up, z depth) -> Blender (x, y depth, z up)
    faces = [list(reversed(f)) for f, _ in mb.faces]      # (the axis swap turns the winding over)
    me.from_pydata(verts, [], faces)
    me.update()
    col = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    k = 0
    for poly, (_, c) in zip(me.polygons, mb.faces):
        for li in poly.loop_indices:
            col.data[li].color = (c[0], c[1], c[2], 1.0)
    o = bpy.data.objects.new(name, me)
    S.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


SOLID = toon('Solid', colour=(1, 1, 1), vcol=True)


def solid(name, centre, size, colour):
    """StreetBuilder.Solid: a box of one colour (Unity centre and size)."""
    mb = ps.MB()
    c, h = centre, [v / 2 for v in size]
    mb.box((c[0] - h[0], c[1] - h[1], c[2] - h[2]), (c[0] + h[0], c[1] + h[1], c[2] + h[2]), colour)
    return unity_mesh(name, mb, SOLID)


# ---------------------------------------------------------------- the beach
def sand():
    bm = bmesh.new()
    xs = [i * 1.0 for i in range(-70, 71)]
    zs = [-14 + j * 0.25 for j in range(0, 105)]       # to z = 12
    grid = [[bm.verts.new((x, z, sand_y(x, z))) for x in xs] for z in zs]
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    me = bpy.data.meshes.new('Sand'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('Sand', me); S.collection.objects.link(o)
    o.data.materials.append(plain('Sand', (0.62, 0.42, 0.3)))


sand()
box('Sea', (0, 300, SEA_Y - 0.05), (1400, 600, 0.1), plain('Sea', (0.16, 0.62, 0.78), lighting=0.35))
for x0, x1 in ((-70, 70),):
    box('Foam', ((x0 + x1) / 2, 9.6, SEA_Y + 0.02), (x1 - x0, 0.6, 0.02), plain('Foam', (0.97, 0.98, 0.98), lighting=0.4))

# the pier: spans from the beach out to sea, the end platform
SPAN = 12.0
for i in range(7):
    objs = import_fbx(os.path.join(MODELS, 'Coast', 'PierSpan.fbx'))
    for o in meshes(objs):
        o.data.materials.clear(); o.data.materials.append(kit_material('Coast'))
    for r in [o for o in objs if o.parent is None]:
        r.location = (PIER_X, PIER_Z + i * SPAN, SEA_Y)
bpy.context.view_layer.update()

# the stairs, and the paths on the sand
if not BEFORE:
    def drop_at(x):
        return DECK - sand_y(x, PIER_Z - DEPTH / 2)
    runs = []
    drops = []
    for s in (-1, 1):
        run = ps.plan(drop_at(PIER_X + s * (WIDTH / 2 + 7.0)))[4]
        for _ in range(2):
            d = drop_at(PIER_X + s * (WIDTH / 2 + run))
            run = ps.plan(d)[4]
        drops.append(d); runs.append(run)
    print('drops', drops, 'plan', [ps.plan(d) for d in drops])
    mb = ps.MB()
    ps.build(mb, WIDTH, DEPTH, drops[0], drops[1], DECK - sand_y(PIER_X, PIER_Z - DEPTH / 2))
    mb.v = [(x + PIER_X, y + DECK, z + PIER_Z) for (x, y, z) in mb.v]
    unity_mesh('PierStairs', mb, SOLID)
    for k, (c, size) in enumerate(ps.path_slats(PIER_X, PIER_Z, DECK, WIDTH, DEPTH, runs[0], runs[1], sand_y)):
        solid('Slat%d' % k, c, size, ps.BOARDS)

# the beach around it: a lifeguard tower, palms, parasols, the kid and the ball
kit('Leisure', 'LifeguardTower', (-19.0, 7.4, sand_y(-19, 7.4)))
kit('Plants', 'Palm', (-15.0, 6.0, -0.1))
kit('Plants', 'PalmShort', (15.5, 6.6, -0.1))
kit('Plants', 'PalmDate', (22.0, 2.8, 0.0), scale=0.7)
kit('Leisure', 'Parasol', (-25.0, 4.2, 0.0))
kit('Leisure', 'BeachTowel', (-24.6, 3.8, 0.0), yaw=95)
kit('Leisure', 'Parasol', (17.5, 3.8, 0.0))
kit('Leisure', 'BeachTowel', (17.8, 3.4, 0.0), yaw=80)
kit('Animals', 'SeagullStanding', (6.0, 1.9, 0.0), yaw=200)
kit('Animals', 'Seagull', (3.0, 9.0, 7.5), yaw=20, anchor='centre')
kit('Plants', 'DuneGrass', (-8.0, -4.4, 0.0)); kit('Plants', 'DuneGrass', (3.5, -4.0, 0.0))
for c in [(-40, 260, 40, 12), (25, 250, 52, 13), (80, 270, 36, 10)]:
    cloud(c[:3], c[3])
hills(420, 'Headland', x=60, scale=2.6)
person('BackpackBoy', (-6.2, -0.2, 0.0), 66, 'run_stride', 1.75, bag='KickOff')
ball((-5.2, -0.35, 0.15))

# ---- the sun, the engine (as render_scenes.py) ----
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = math.pi; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (-SUNDIR).to_track_quat('-Z', 'Y').to_euler()
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
S.render.engine = 'BLENDER_EEVEE'
S.render.image_settings.file_format = 'PNG'
S.render.image_settings.color_mode = 'RGBA'
S.render.film_transparent = True
S.render.dither_intensity = 0.0
S.view_settings.view_transform = 'Standard'
S.eevee.taa_render_samples = 16
S.render.filter_size = 1.5
set_pass('colour')

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'
cam.data.clip_start = 0.3; cam.data.clip_end = 900


def shoot(name, loc, target, fov, w, h):
    cam.data.angle_y = math.radians(fov)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    S.render.resolution_x, S.render.resolution_y = w, h
    S.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)


# the game's camera (CameraFollow2D: 2.7 m half-height at the kid, 4 degrees down, the kid 38% across a phone's width)
half = 2.7; fov = 34.0
back = half / math.tan(math.radians(fov / 2))
cx = -6.2 + 1.41
shoot('game', (cx, -back, 1.95), (cx, 0.0, 1.95 - back * math.tan(math.radians(4))), fov, 2168, 1000)
if '--game-only' not in argv:
    shoot('whole', (0.0, -17.0, 3.2), (0.0, 5.0, 2.4), 36.0, 1920, 1000)
    shoot('close', (-15.5, -4.0, 1.7), (-6.5, 5.3, 2.0), 40.0, 1600, 1000)
print('rendered pier', 'before' if BEFORE else 'after')
