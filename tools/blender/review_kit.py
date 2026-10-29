# Review sheet for an asset kit, in the game's target look (docs/ART_DIRECTION.md): a warm low sun
# with soft shadows, cool sky-coloured shadow sides, a hazy gradient sky, a ground plane.
#   blenv/bin/python review_kit.py -- /abs/Kit.blend /abs/kit_sheet.png [--models A,B,C] [--cols 4]
# Tiles: each model alone, three-quarter front, framed to its size, with its name and triangle count.
# Bottom: every model in a row, seen roughly as the game camera sees the street (front, slightly
# above, with distance haze).
import bpy, math, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
blend, out = args[0], args[1]
only = None
cols = 4
if '--models' in args: only = args[args.index('--models') + 1].split(',')
if '--cols' in args: cols = int(args[args.index('--cols') + 1])
bpy.ops.wm.open_mainfile(filepath=blend)
C = bpy.context; S = C.scene

roots = [o for o in S.objects if o.parent is None and not o.name.startswith('Attach') and o.type in ('MESH', 'EMPTY')]
if only: roots = [o for o in roots if o.name in only]
roots.sort(key=lambda o: o.name)


def bbox(root):
    pts = []
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH':
            pts += [o.matrix_world @ v.co for v in o.data.vertices]
    if not pts: return Vector((0, 0, 0)), Vector((1, 1, 1))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def tris(root):
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in [root] + list(root.children_recursive) if o.type == 'MESH')


# ---- the look: gradient sky as world light, a warm sun, soft shadows
S.render.engine = 'BLENDER_EEVEE'
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
world = bpy.data.worlds.new('sky'); S.world = world; world.use_nodes = True
wn = world.node_tree; bg = wn.nodes['Background']
tc = wn.nodes.new('ShaderNodeTexCoord'); sep = wn.nodes.new('ShaderNodeSeparateXYZ')
ramp = wn.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (1.0, 0.78, 0.66, 1)
ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = (0.52, 0.66, 0.92, 1)
e = ramp.color_ramp.elements.new(0.12); e.color = (0.92, 0.8, 0.86, 1)
wn.links.new(tc.outputs['Generated'], sep.inputs[0]); wn.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
wn.links.new(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.85
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.color = (1.0, 0.88, 0.72); sun.data.energy = 3.6; sun.data.angle = math.radians(4)
sun.rotation_euler = (math.radians(58), 0, math.radians(-38))   # from the front-right, above
try:
    S.eevee.use_shadows = True
except AttributeError:
    pass

gm = bpy.data.meshes.new('ground')
gm.from_pydata([(-2000, -2000, 0), (2000, -2000, 0), (2000, 2000, 0), (-2000, 2000, 0)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new('ReviewGround', gm); S.collection.objects.link(ground)
gmat = bpy.data.materials.new('ground'); gmat.use_nodes = True
gb = gmat.node_tree.nodes.get('Principled BSDF')
gb.inputs['Base Color'].default_value = (0.62, 0.58, 0.52, 1); gb.inputs['Roughness'].default_value = 1.0
gm.materials.append(gmat)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.lens = 50

tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_kit_tmp'); os.makedirs(tmp, exist_ok=True)


def show(only_root):
    for r in roots:
        hide = only_root is not None and r is not only_root
        for o in [r] + list(r.children_recursive):
            o.hide_render = hide


def look_at(obj, target):
    d = target - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


files = []
S.render.resolution_x = S.render.resolution_y = 420
for r in roots:
    show(r)
    lo, hi = bbox(r)
    c = (lo + hi) * 0.5
    size = max((hi - lo).length, 0.3)
    d = size * 1.45
    cam.location = c + Vector((d * 0.55, -d * 0.85, d * 0.38))
    look_at(cam, c + Vector((0, 0, -size * 0.05)))
    cam.data.clip_end = d * 20
    p = os.path.join(tmp, r.name + '.png'); S.render.filepath = p
    bpy.ops.render.render(write_still=True); files.append((r.name, p, tris(r), hi - lo))

# Lineup: everything in a row, the game's view (front, a little above), with haze via the mist pass.
show(None)
x = 0.0
spans = []
for r in roots:
    lo, hi = bbox(r)
    w = hi.x - lo.x
    off = Vector((x - lo.x, 0, 0))
    for o in [r]:
        o.location += off
    spans.append((r.name, x, x + w))
    x += w + 1.0
total = max(x - 1.0, 1.0)
height = max((bbox(r)[1].z for r in roots), default=2.0)
S.render.resolution_x, S.render.resolution_y = 1680, 520
cam.data.lens = 35
dist = max(total * 0.55, height * 2.5, 8.0)
cam.location = Vector((total * 0.5, -dist, height * 0.45 + dist * 0.12))
look_at(cam, Vector((total * 0.5, 0, height * 0.45)))
cam.data.clip_end = 5000
S.view_layers[0].use_pass_mist = True
S.world.mist_settings.start = dist * 0.6
S.world.mist_settings.depth = dist * 4
HAZE = (0.96, 0.8, 0.74, 1)
if hasattr(S, 'node_tree'):            # Blender 4.x compositor
    S.use_nodes = True
    nt = S.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers'); comp = nt.nodes.new('CompositorNodeComposite')
    mix = nt.nodes.new('CompositorNodeMixRGB'); mix.inputs[2].default_value = HAZE
    nt.links.new(rl.outputs['Image'], mix.inputs[1]); nt.links.new(rl.outputs['Mist'], mix.inputs[0])
    nt.links.new(mix.outputs[0], comp.inputs['Image'])
else:                                  # Blender 5: a compositor node group on the scene
    nt = bpy.data.node_groups.new('Haze', 'CompositorNodeTree')
    nt.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = nt.nodes.new('CompositorNodeRLayers'); go = nt.nodes.new('NodeGroupOutput')
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['B'].default_value = HAZE
    nt.links.new(rl.outputs['Image'], mix.inputs['A']); nt.links.new(rl.outputs['Mist'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], go.inputs[0])
    S.compositing_node_group = nt
lp = os.path.join(tmp, '_lineup.png'); S.render.filepath = lp
bpy.ops.render.render(write_still=True)

from PIL import Image, ImageDraw
tw = 420
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (max(cols * tw, 1680), rows * (tw + 34) + 540), (52, 52, 58))
dr = ImageDraw.Draw(sheet)
for i, (name, p, t, size) in enumerate(files):
    x0, y0 = (i % cols) * tw, (i // cols) * (tw + 34)
    sheet.paste(Image.open(p).convert('RGB'), (x0, y0))
    dr.text((x0 + 8, y0 + tw + 4), f"{name}  {t} tris  {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m", fill=(235, 235, 235))
sheet.paste(Image.open(lp).convert('RGB'), (0, rows * (tw + 34) + 10))
sheet.save(out)
print('sheet', out)
