# The Blender side of the town map: the painted ground on a plane, the models as linked duplicates, a low sun from the
# south-west with soft shadows, a sky for the shade, and a camera looking straight down with a slight perspective (tall
# things lean a little outward from the middle, which is what makes the picture feel like a real aerial view).
import bpy, math, os, time
import numpy as np
from mathutils import Vector
import town_map_kit as K
import town_map_raster as R

PPM = 8.0
CAM_HEIGHT = 900.0                       # metres above the ground: a long lens, so only a gentle perspective
SUN_DIR = Vector((-0.5, -0.55, 0.9)).normalized()          # towards the sun (south-west, about 50 degrees up)


def world_xy(x, y):
    """Core px (x east, y down) to Blender metres (x east, y north), the picture's centre at the origin."""
    return ((x + R.ORIGIN[0] - R.IMG_W / 2) / PPM, (R.IMG_H / 2 - (y + R.ORIGIN[1])) / PPM)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    K.reset()
    S = bpy.context.scene
    S.render.engine = 'BLENDER_EEVEE'
    try:
        S.view_settings.view_transform = 'Standard'
        S.view_settings.look = 'None'
    except Exception:
        pass
    return S


def ground(S, png, margin=60.0):
    """The painted ground on a plane that covers the picture plus `margin` metres each way (the texture's edge pixels
    continue outward, so shadows of things just outside the picture still land on something)."""
    w, h = R.IMG_W / PPM, R.IMG_H / PPM
    hw, hh = w / 2 + margin, h / 2 + margin
    me = bpy.data.meshes.new('ground')
    me.from_pydata([(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)], [], [(0, 1, 2, 3)])
    me.update()
    uv = me.uv_layers.new(name='UVMap')
    u0, u1 = -(hw - w / 2) / w, 1 + (hw - w / 2) / w
    v0, v1 = -(hh - h / 2) / h, 1 + (hh - h / 2) / h
    for loop, (u, v) in zip(me.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
        uv.data[loop.index].uv = (u, v)
    o = bpy.data.objects.new('ground', me)
    S.collection.objects.link(o)
    m = bpy.data.materials.new('ground')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png, check_existing=True)
    tex.extension = 'EXTEND'
    tex.interpolation = 'Cubic'
    surf = K.shade(nt, tex.outputs['Color'])
    nt.links.new(surf, out.inputs['Surface'])
    me.materials.append(m)
    return o


def lights(S, sun_energy=3.2, sky_energy=0.55, sun_angle_deg=3.5):
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    S.collection.objects.link(sun)
    sun.data.color = (1.0, 0.95, 0.88)
    sun.data.energy = sun_energy
    sun.data.angle = math.radians(sun_angle_deg)
    sun.rotation_euler = (-SUN_DIR).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('sky')
    S.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.60, 0.72, 0.95, 1)
    bg.inputs['Strength'].default_value = sky_energy


def camera(S, res_scale=1.0):
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    S.collection.objects.link(cam)
    S.camera = cam
    cam.location = (0, 0, CAM_HEIGHT)
    cam.rotation_euler = (0, 0, 0)
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.sensor_width = 36.0
    w = R.IMG_W / PPM
    cam.data.lens = 36.0 * CAM_HEIGHT / w
    cam.data.clip_start = 10
    cam.data.clip_end = 4000
    S.render.resolution_x = int(R.IMG_W * res_scale)
    S.render.resolution_y = int(R.IMG_H * res_scale)
    S.render.resolution_percentage = 100
    return cam


_colour_mats = {}
_box_meshes = {}


def _colour_material(rgb):
    key = tuple(round(c, 3) for c in rgb)
    if key not in _colour_mats:
        m = bpy.data.materials.new('col%d' % len(_colour_mats))
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        rgbn = nt.nodes.new('ShaderNodeRGB')
        rgbn.outputs[0].default_value = tuple(K.lin(rgb)) + (1,)
        surf = K.shade(nt, rgbn.outputs[0])
        nt.links.new(surf, out.inputs['Surface'])
        _colour_mats[key] = m
    return _colour_mats[key]


def _blob(bm, w, d, h, seed):
    """A tree canopy: a lumpy ball w x d wide and h high (its underside flattened), smooth shaded, so that from above it is a round
    green crown with a sun side and a shade side, like the trees of the reference picture."""
    import bmesh, random
    from mathutils import Vector
    rng = random.Random(seed)
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    lumps = []
    for _ in range(9):
        c = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) * 0.6 + 0.4)).normalized()
        lumps.append((c, rng.uniform(0.05, 0.16), rng.uniform(0.18, 0.4)))
    for v in bm.verts:
        n = v.co.normalized()
        k = 1.0
        for c, amp, wid in lumps:
            k += amp * math.exp(-(1.0 - n.dot(c)) / wid)
        k += 0.025 * math.sin(7 * n.x + 3 * n.y) * math.cos(5 * n.z)
        z = n.z * k
        v.co = Vector((n.x * k * w / 2, n.y * k * d / 2, h * 0.5 + max(z, -0.55) * h * 0.5))


def _wedge(bm, w, d, h):
    """A ramp: w wide, d long (along local Y), rising from nothing at -Y to h at +Y."""
    v = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0), (-w / 2, d / 2, h), (w / 2, d / 2, h)]
    vs = [bm.verts.new(c) for c in v]
    for f in ((0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 5), (0, 4, 3), (3, 4, 5, 2)):
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass


def _box_mesh(w, d, h, roof):
    key = (round(w, 2), round(d, 2), round(h, 2), roof)
    if key in _box_meshes:
        return _box_meshes[key]
    import bmesh
    bm = bmesh.new()
    if roof and roof.startswith('blob'):
        _blob(bm, w, d, h, int(roof[4:] or 0))
    elif roof == 'wedge':
        _wedge(bm, w, d, h)
    elif roof == 'frame':
        # a football goal: two posts and a crossbar along local Y (d is the width of the mouth)
        r = 0.07
        for yy in (-d / 2, d / 2):
            bmesh.ops.create_cube(bm, size=1.0, matrix=__import__('mathutils').Matrix.Translation((0, yy, h / 2)) @ __import__('mathutils').Matrix.Diagonal((w if w > 0.3 else 0.2, 0.15, h, 1.0)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=__import__('mathutils').Matrix.Translation((0, 0, h - 0.07)) @ __import__('mathutils').Matrix.Diagonal((0.15, d, 0.14, 1.0)))
    elif roof == 'ridge':
        wall = h * 0.62
        v = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
             (-w / 2, -d / 2, wall), (w / 2, -d / 2, wall), (w / 2, d / 2, wall), (-w / 2, d / 2, wall), (0, -d / 2 - 0.3, h), (0, d / 2 + 0.3, h)]
        vs = [bm.verts.new(c) for c in v]
        for f in ((0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 8), (5, 6, 9, 8), (6, 7, 9), (7, 4, 8, 9)):
            try:
                bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
    else:
        bmesh.ops.create_cube(bm, size=1.0, matrix=__import__('mathutils').Matrix.Translation((0, 0, h / 2)) @ __import__('mathutils').Matrix.Diagonal((w, d, h, 1.0)))
        if roof == 'round':
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(0.5, h * 0.18), segments=3, affect='EDGES')
    bm.normal_update()
    me = bpy.data.meshes.new('box')
    bm.to_mesh(me)
    bm.free()
    for p_ in me.polygons:
        p_.use_smooth = (roof == 'round' or bool(roof and roof.startswith('blob')))
    _box_meshes[key] = me
    return me


def add_items(S, items):
    coll = bpy.data.collections.new('town')
    S.collection.children.link(coll)
    n = 0
    for it in items:
        X, Y = world_xy(it.x, it.y)
        if it.kit == 'custom':
            p = it.params
            me = _box_mesh(p['w'], p['d'], p['h'], p.get('roof'))
            if not me.materials:
                me.materials.append(_colour_material((0.7, 0.7, 0.7)))
            o = bpy.data.objects.new('box', me)
            coll.objects.link(o)
            slot = o.material_slots[0]
            slot.link = 'OBJECT'
            slot.material = _colour_material(it.tints or (0.7, 0.7, 0.7))
            o.location = (X, Y, it.z)
            o.rotation_euler = (0, 0, math.radians(180.0 - it.face))
        else:
            K.place(it.kit, it.name, X, Y, face=it.face, scale=it.scale, z=it.z, tints=it.tints, collection=coll)
        n += 1
    return n


def render(S, out, samples=32, crop=None):
    """Render to a PNG. crop = (x0, y0, x1, y1) in picture px (of the full 3200 x 1800) renders only that part."""
    S.eevee.taa_render_samples = samples
    S.render.filepath = out
    S.render.image_settings.file_format = 'PNG'
    if crop:
        S.render.use_border = True
        S.render.use_crop_to_border = True
        S.render.border_min_x = crop[0] / R.IMG_W
        S.render.border_max_x = crop[2] / R.IMG_W
        S.render.border_min_y = 1 - crop[3] / R.IMG_H
        S.render.border_max_y = 1 - crop[1] / R.IMG_H
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t
