# Renders the subject of each level's album sticker (one per story level, L01-L23) from the
# game's own models, in the game's toon look (ToonCharacter's two flat cel bands from the sun,
# cool shade, a rim of light and a dark ink outline), on a transparent background.
#   blenv/bin/python sticker_art.py -- <kits dir> <cars dir> <teens dir> <out dir> [--only L01,L02] [--size 512]
# <kits dir> holds one folder per kit with <Kit>.blend inside (as for preview_street.py);
# <cars dir> holds Hatch.blend etc. (car.py); <teens dir> holds Boy.blend (teen.py).
# Then sticker_compose.py turns each render into a die-cut vinyl sticker for the album.
import bpy, math, sys, os, glob
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
kits_dir, cars_dir, teens_dir, out_dir = args[:4]
only = args[args.index('--only') + 1].split(',') if '--only' in args else None
SIZE = int(args[args.index('--size') + 1]) if '--size' in args else 512
os.makedirs(out_dir, exist_ok=True)

# (level id, source, model, yaw: degrees the model turns to show its side, elevation: degrees the
#  camera looks down, tints for recolourable parts 1-3 (sRGB) or None)
STICKERS = [
    ('L01', 'teen', 'Boy', 55, 6, None),
    ('L02', 'car', 'Hatch', -38, 16, None),
    ('L03', 'Street', 'Bicycle', -28, 12, [(0.2, 0.7, 0.75), None, None]),
    ('L04', 'Animals', 'Cat', -32, 14, None),
    ('L05', 'Buildings', 'HouseGable', -30, 10, None),
    ('L06', 'Street', 'MarketStall', -30, 14, None),
    ('L07', 'Street', 'SignCrossing', -24, 6, None),
    ('L08', 'Street', 'VendingRed', -30, 8, None),
    ('L09', 'Street', 'ProduceCrate', -30, 28, None),
    ('L10', 'Buildings', 'ShopNoodle', -28, 8, None),
    ('L11', 'Leisure', 'LifeguardTower', -34, 10, None),
    ('L12', 'Animals', 'Crab', -22, 30, None),
    ('L13', 'Animals', 'SeagullStanding', -40, 10, None),
    ('L14', 'Leisure', 'SandCastle', -28, 22, None),
    ('L15', 'Street', 'TrafficCone', -30, 16, None),
    ('L16', 'Works', 'Digger', -38, 14, None),
    ('L17', 'Works', 'TowerCrane', -26, 8, None),
    ('L18', 'Works', 'CementMixer', -36, 12, None),
    ('L19', 'Animals', 'Dog', -38, 12, None),
    ('L20', 'Leisure', 'Fountain', -22, 22, None),
    ('L21', 'Leisure', 'SwingSet', -28, 10, None),
    ('L22', 'Animals', 'Duck', -36, 14, None),
    ('L23', 'bell', 'Bell', -20, 10, None),
]

SUN = (1.0, 0.97, 0.92)
SHADE = tuple(0.25 * a + 0.75 * b for a, b in zip((0.68, 0.7, 0.88), (0.52, 0.56, 0.66)))
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()


def lin(c):
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c[:3])


def fresh():
    global OUTLINE
    OUTLINE = None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    S = bpy.context.scene
    S.render.engine = 'BLENDER_EEVEE'
    S.view_settings.view_transform = 'Standard'
    S.render.film_transparent = True
    try:
        S.eevee.taa_render_samples = 16
    except Exception:
        pass
    S.world = bpy.data.worlds.new('w'); S.world.color = (0.62, 0.78, 0.95)
    S.render.resolution_x = S.render.resolution_y = SIZE
    return S


def load_objects(blend, root_name=None):
    """Objects from a .blend: the model rooted at root_name (kits), or every object (cars, teens)."""
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    objs = [o for o in dst.objects if o is not None]
    if root_name is not None:
        root = next((o for o in objs if o.name == root_name and o.parent is None), None)
        if root is None:
            return []
        keep = [root] + list(root.children_recursive)
        root.location = (0, 0, 0)
    else:
        keep = objs
    S = bpy.context.scene
    for o in keep:
        if o.name not in S.collection.objects:
            S.collection.objects.link(o)
    return keep


def toon(mat):
    """Replace a material's surface with the game's toon shading, keeping its colour (vertex colour x atlas)."""
    if mat is None or not mat.use_nodes or mat.get('toon'):
        return
    nt = mat.node_tree
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    bsdf = next((n for n in nt.nodes if n.type in ('BSDF_DIFFUSE', 'BSDF_PRINCIPLED')), None)
    if out is None:
        return
    color_in = None
    if bsdf is not None:
        sock = bsdf.inputs.get('Color') or bsdf.inputs.get('Base Color')
        if sock is not None and sock.is_linked:
            color_in = sock.links[0].from_socket
        elif sock is not None:
            rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = sock.default_value
            color_in = rgb.outputs[0]
    if color_in is None:
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = (0.8, 0.8, 0.8, 1)
        color_in = rgb.outputs[0]
    L = nt.nodes.new('ShaderNodeCombineXYZ')
    L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR
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
    nt.links.new(color_in, m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
    ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
    rim = nt.nodes.new('ShaderNodeMapRange'); rim.interpolation_type = 'SMOOTHSTEP'
    rim.inputs['From Min'].default_value = 0.4; rim.inputs['From Max'].default_value = 0.24
    nt.links.new(ndv.outputs['Value'], rim.inputs['Value'])
    rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'; rk.inputs[1].default_value = 0.2
    nt.links.new(rim.outputs['Result'], rk.inputs[0])
    add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
    add.inputs['B'].default_value = SUN + (1,)
    nt.links.new(rk.outputs[0], add.inputs['Factor']); nt.links.new(m2.outputs['Result'], add.inputs['A'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(add.outputs['Result'], em.inputs['Color'])
    # Keep cut-out alpha (leaf cards) if the material has it.
    alpha = None
    if bsdf is not None and bsdf.inputs.get('Alpha') is not None and bsdf.inputs['Alpha'].is_linked:
        alpha = bsdf.inputs['Alpha'].links[0].from_socket
    if alpha is not None:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(alpha, mix.inputs['Fac']); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        mat['leafy'] = True      # cut-out cards: no ink outline shell
    else:
        nt.links.new(em.outputs[0], out.inputs['Surface'])
    mat.use_backface_culling = False
    mat['toon'] = True


OUTLINE = None


def outline_material():
    global OUTLINE
    if OUTLINE is None:
        OUTLINE = bpy.data.materials.new('Outline'); OUTLINE.use_nodes = True; OUTLINE.use_backface_culling = True
        on = OUTLINE.node_tree; e = on.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
        on.links.new(e.outputs[0], on.nodes['Material Output'].inputs['Surface'])
    return OUTLINE


def dress(objs, thickness):
    for o in objs:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            toon(slot.material)
        if any(s.material and s.material.get('leafy') for s in o.material_slots):
            continue
        n = len(o.material_slots)
        o.data.materials.append(outline_material())
        sol = o.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = thickness; sol.offset = 1
        sol.use_flip_normals = True; sol.material_offset = n
        for slot in o.material_slots[:n]:
            if slot.material:
                slot.material.use_backface_culling = True


def recolour(objs, tints):
    """Parts 1-3 (UV2.x) take the tint, keeping brightness relative to the part's mean (as ModelTint)."""
    import numpy as np
    for o in objs:
        if o.type != 'MESH' or len(o.data.uv_layers) < 2 or not o.data.color_attributes:
            continue
        me = o.data
        attr = me.color_attributes.active_color or me.color_attributes[0]
        if attr.domain != 'CORNER':
            continue
        n = len(me.loops)
        part = np.zeros(n * 2); me.uv_layers[1].data.foreach_get('uv', part)
        part = np.rint(part.reshape(-1, 2)[:, 0]).astype(int) - 1
        cols = np.zeros(n * 4); attr.data.foreach_get('color', cols); cols = cols.reshape(-1, 4)
        for p in range(3):
            if tints[p] is None:
                continue
            sel = part == p
            if not sel.any():
                continue
            mean = cols[sel, :3].mean(axis=0).sum() + 1e-4
            k = cols[sel, :3].sum(axis=1) / mean
            cols[sel, :3] = np.clip(np.array(lin(tints[p]))[None, :] * k[:, None], 0, 1)
        attr.data.foreach_set('color', cols.ravel())


def football(radius, location):
    """A classic ball: white with 12 dark pentagon spots at the icosahedron's corners (vertex colours)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=radius, location=location)
    o = bpy.context.object
    me = o.data
    phi = (1 + 5 ** 0.5) / 2
    corners = [Vector(v).normalized() for v in [(0, 1, phi), (0, -1, phi), (0, 1, -phi), (0, -1, -phi), (1, phi, 0), (-1, phi, 0),
                                                 (1, -phi, 0), (-1, -phi, 0), (phi, 0, 1), (-phi, 0, 1), (phi, 0, -1), (-phi, 0, -1)]]
    rot = Matrix.Rotation(0.4, 3, 'X') @ Matrix.Rotation(0.3, 3, 'Z')
    corners = [rot @ c for c in corners]
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    for poly in me.polygons:
        d = (me.vertices[poly.vertices[0]].co).normalized()
        c = poly.center.normalized()
        dark = max(c.dot(k) for k in corners) > 0.91
        for li in poly.loop_indices:
            col.data[li].color = (0.06, 0.06, 0.08, 1) if dark else (0.95, 0.95, 0.95, 1)
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new('Ball'); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    me.materials.append(mat)
    return o


def bell():
    """The school bell: a golden hand bell on a turned wooden handle, swung mid-ring, by lathe."""
    prof = [(0.40, 0.0), (0.43, 0.03), (0.39, 0.08), (0.31, 0.22), (0.27, 0.38), (0.25, 0.52),
            (0.22, 0.62), (0.15, 0.69), (0.06, 0.72), (0.0, 0.73)]
    verts, faces = [], []
    n = 56
    for i in range(n):
        a = i / n * math.pi * 2
        for r, z in prof:
            verts.append((r * math.cos(a), r * math.sin(a), z))
    m = len(prof)
    for i in range(n):
        j = (i + 1) % n
        for k in range(m - 1):
            faces.append((i * m + k + 1, j * m + k + 1, j * m + k, i * m + k))
    me = bpy.data.meshes.new('Bell'); me.from_pydata(verts, [], faces); me.update()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    waist = min(bm.faces, key=lambda f: abs(f.calc_center_median().z - 0.38))
    c = waist.calc_center_median()
    if waist.normal.dot(Vector((c.x, c.y, 0))) < 0:       # the shell faces in: turn it out
        for f in bm.faces:
            f.normal_flip()
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    body = bpy.data.objects.new('Bell', me); bpy.context.scene.collection.objects.link(body)
    gold = bpy.data.materials.new('Gold'); gold.use_nodes = True
    gold.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin((0.98, 0.74, 0.22)) + (1,)
    me.materials.append(gold)
    wood = bpy.data.materials.new('Wood'); wood.use_nodes = True
    wood.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin((0.5, 0.29, 0.16)) + (1,)
    objs = [body]
    bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.42, location=(0, 0, 0.93)); h = bpy.context.object
    h.data.materials.append(wood); objs.append(h)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, location=(0, 0, 1.18)); k = bpy.context.object
    k.data.materials.append(wood); objs.append(k)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0.05, 0, 0.02)); c = bpy.context.object
    c.data.materials.append(gold); objs.append(c)
    # Two raised bands round the shoulder and the lip, a shade deeper.
    band = bpy.data.materials.new('Band'); band.use_nodes = True
    band.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin((0.86, 0.55, 0.12)) + (1,)
    for z, rr in ((0.52, 0.255), (0.06, 0.405)):
        bpy.ops.mesh.primitive_torus_add(major_radius=rr, minor_radius=0.022, location=(0, 0, z))
        t = bpy.context.object; t.data.materials.append(band); objs.append(t)
    for o in objs[1:]:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
    # Swung mid-ring.
    pivot = bpy.data.objects.new('Swing', None); bpy.context.scene.collection.objects.link(pivot)
    for o in objs:
        o.parent = pivot
    pivot.rotation_euler = (0, math.radians(-22), 0)
    bpy.context.view_layer.update()
    return objs


def teen_with_ball():
    objs = load_objects(os.path.join(teens_dir, 'Boy.blend'))
    rig = bpy.data.objects.get('KidRig'); kid = bpy.data.objects.get('Kid')
    # A side-volley: the near leg swung up to meet the ball, arms out for balance.
    pose = {'UpperLeg.R': -70, 'LowerLeg.R': 25, 'UpperLeg.L': 12, 'LowerLeg.L': 18,
            'UpperArm.R': 40, 'LowerArm.R': -30, 'UpperArm.L': -55, 'LowerArm.L': -40, 'Head': 10}
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
    for b, a in pose.items():
        if b in rig.pose.bones:
            rig.pose.bones[b].rotation_euler = (math.radians(a), 0, 0)
    zs = [(kid.matrix_world @ v.co).z for v in kid.data.vertices]
    top = max(zs)
    ball = football(top * 0.11, (0, -top * 0.42, top * 0.33))
    return [kid, ball], top


def frame(objs, yaw, elev, crop=1.0):
    """An orthographic camera looking at the objects from the front (-Y), turned by yaw and down by elev,
    framing the top <crop> of their height (1 = all of it)."""
    S = bpy.context.scene
    bpy.context.view_layer.update()
    pts = []
    for o in objs:
        if o.type != 'MESH':
            continue
        dg = bpy.context.evaluated_depsgraph_get()
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        pts += [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    if crop < 1.0:
        z0 = min(p.z for p in pts); z1 = max(p.z for p in pts)
        pts = [p for p in pts if p.z >= z1 - (z1 - z0) * crop]
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
    cam.data.type = 'ORTHO'
    a, e = math.radians(yaw), math.radians(elev)
    fwd = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), -math.sin(e)))   # looking toward +Y (at the front)
    rot = fwd.to_track_quat('-Z', 'Y')
    inv = rot.to_matrix().inverted()
    loc = [inv @ p for p in pts]
    xs = [p.x for p in loc]; ys = [p.y for p in loc]; zs = [p.z for p in loc]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.06
    centre = rot.to_matrix() @ Vector((cx, cy, max(zs) + 50))
    cam.location = centre
    cam.rotation_euler = rot.to_euler()
    cam.data.ortho_scale = span
    cam.data.clip_end = 1000
    return span


CROP = {'L17': 0.34, 'L07': 0.45}


def jets(objs):
    """The floor fountain playing: a tall jet in the middle and arcs of droplets curving out from the grate."""
    pts = [o.matrix_world @ v.co for o in objs if o.type == 'MESH' for v in o.data.vertices]
    cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    top = max(p.z for p in pts); r = max(max(p.x for p in pts) - cx, max(p.y for p in pts) - cy)
    water = bpy.data.materials.new('Jet'); water.use_nodes = True
    water.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin((0.72, 0.9, 1.0)) + (1,)
    made = []
    bpy.ops.mesh.primitive_cone_add(radius1=r * 0.13, radius2=r * 0.05, depth=r * 1.7, location=(cx, cy, top + r * 0.85))
    c = bpy.context.object; c.data.materials.append(water); made.append(c)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.16, location=(cx, cy, top + r * 1.72))
    c = bpy.context.object; c.data.materials.append(water); made.append(c); bpy.ops.object.shade_smooth()
    for k in range(7):
        ang = k / 7 * math.pi * 2 + 0.3
        for i in range(1, 8):
            t = i / 8
            d = r * 0.85 * t
            z = top + r * 1.25 * 4 * t * (1 - t) * 0.9 + r * 0.05
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * (0.085 - 0.04 * t), segments=12, ring_count=8,
                                                 location=(cx + math.cos(ang) * d, cy + math.sin(ang) * d, z))
            c = bpy.context.object; c.data.materials.append(water); made.append(c); bpy.ops.object.shade_smooth()
    return made


for sid, source, model, yaw, elev, tints in STICKERS:
    if only and sid not in only:
        continue
    S = fresh()
    if source == 'teen':
        objs, top = teen_with_ball()
        size = top
    elif source == 'car':
        objs = load_objects(os.path.join(cars_dir, model + '.blend'))
        objs = [o for o in objs if o.type in ('MESH', 'EMPTY')]
    elif source == 'bell':
        objs = bell()
    else:
        blends = glob.glob(os.path.join(kits_dir, '*', source + '.blend'))
        if not blends:
            print('missing kit', source); continue
        objs = load_objects(blends[0], model)
        if not objs:
            print('missing model', source, model); continue
        if tints:
            recolour(objs, tints)
        if sid == 'L20':
            objs = objs + jets(objs)
    meshes = [o for o in objs if o.type == 'MESH']
    bpy.context.view_layer.update()
    span = frame(objs, yaw, elev, CROP.get(sid, 1.0))
    # The ink line: about 0.7% of the framed size, like the in-game outline at sticker scale.
    dress(objs, span * 0.007)
    S.render.filepath = os.path.join(out_dir, sid + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', sid, model)
