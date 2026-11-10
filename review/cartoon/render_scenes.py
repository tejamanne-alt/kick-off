# Renders the game's places from its own models (the kits, the cars, the six kids, the passers-by, the animals, the
# ball) from the game's camera, in the game's toon look, plus what a full-screen filter reads from the camera:
#   blenv/bin/python render_scenes.py -- <models dir> <out dir> <scene> [width height] [--close]
# scenes: home market beach site park california cast_a cast_b menu
# Writes <scene>_colour.png (RGBA: alpha 0 where the sky shows; the sky is laid in by the filter preview),
# <scene>_normal.png (view-space normals, 0.5 + 0.5 n) and <scene>_data.png (r, g: depth as a fraction of FAR in two
# 8-bit halves, b: the mask: 1 street, 0.5 foliage (the plants kit), 0 a figure or a cel: the people, the ball, and
# the things the kid plays with (coins, animals, cars, crates, cones, the pipe: CELS)).
# Characters cast no shadows, as in the game (NO_CHAR_SHADOWS=0 lets them). Review scenes: kids (the four primary kids),
# teens (Hana and Max), solo (SOLO=<Model>, SOLO_H=<height>, SOLO_BAG, SOLO_POSE: one figure three-quarter, front and
# running), gait (SOLO at four moments of its run, GAIT_OFFSET radians on; GAIT=walk for a walk); for those and the cast scenes, CAM_FOV, CAM_X, CAM_Z, CAM_TZ move the camera, and HEAD_TILT=<degrees> nods
# every head (the menu nods 6 to 20 down, a slide 44). DIAG=<mode> isolates a character fault (docs/LEARNINGS.md C16, C17):
# norim (no rim), crack (no rim; the ink hull magenta, so cracks and inner outlines show), vc (vertex colours only), tex
# (the atlas only), parts (each face coloured by its outfit part, UV2.x: 0 white, 1 red, 2 blue, 3 green, 4 yellow;
# PARTS_UV names the layer, 'Parts' in the polished FBXs). RIM_FLAT=1 draws the rim as v111 to v113 did (whitened by 45%
# whatever the colour), for before-and-after boards. TORSO=0 keeps the torso rigid (as before v115: CharacterRig.Torso).
# The figures' ink hull is set back 1.2 cm from the camera as ToonCharacter's (OUTLINE_PUSH=0: the hull of before v116,
# which also lost the figure's own normals: docs/LEARNINGS.md C20).
# --data-only renders only the data pass. The toon look: the albedo (atlas x vertex colour)
# times a band between the shade tint and the sun, the sun's cast shadows, and for the people the ink hull and a rim.
import bpy, math, os, sys, random
from mathutils import Vector, Quaternion, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
MODELS, OUT, SCENE = argv[0], argv[1], argv[2]
RW, RH = (int(argv[3]), int(argv[4])) if len(argv) > 4 and argv[3].isdigit() else (1920, 1080)
FAR = 300.0
os.makedirs(OUT, exist_ok=True)
random.seed(7)

DIAG = os.environ.get('DIAG', '')

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
SUN = (1.0, 0.979, 0.962)
SUNDIR = Vector((0.45, -0.4, 0.8)).normalized()   # WorldLook.sunDirection in Blender's axes (toward the camera is -y)
KIT_SHADE = (0.72, 0.76, 0.9)
FIG_SHADE = (0.68, 0.7, 0.88)
CAST = 0.6                                        # WorldLook.castShadow: a cast shadow on the ground, of the shade colour

# ---- one switch for the three passes, shared by every material (a node group) ----
PASS = bpy.data.node_groups.new('Pass', 'ShaderNodeTree')
PASS.interface.new_socket('normal', in_out='OUTPUT', socket_type='NodeSocketFloat')
PASS.interface.new_socket('data', in_out='OUTPUT', socket_type='NodeSocketFloat')
_go = PASS.nodes.new('NodeGroupOutput')
PN = PASS.nodes.new('ShaderNodeValue'); PN.outputs[0].default_value = 0
PD = PASS.nodes.new('ShaderNodeValue'); PD.outputs[0].default_value = 0
PASS.links.new(PN.outputs[0], _go.inputs[0]); PASS.links.new(PD.outputs[0], _go.inputs[1])


def set_pass(kind):
    PN.outputs[0].default_value = 1.0 if kind == 'normal' else 0.0
    PD.outputs[0].default_value = 1.0 if kind == 'data' else 0.0


def image(path, packed=False):
    im = bpy.data.images.load(path, check_existing=True)
    if packed:
        im.alpha_mode = 'CHANNEL_PACKED'
    return im


def _mix(nt, a, b, fac, blend='MIX'):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = blend
    if isinstance(fac, float):
        m.inputs['Factor'].default_value = fac
    else:
        nt.links.new(fac, m.inputs['Factor'])
    for sock, v in (('A', a), ('B', b)):
        if isinstance(v, tuple):
            m.inputs[sock].default_value = v + (1,) if len(v) == 3 else v
        else:
            nt.links.new(v, m.inputs[sock])
    return m.outputs['Result']


def toon(name, tex=None, colour=(1, 1, 1), shade=KIT_SHADE, mask=1.0, vcol=True, lighting=1.0, rim=0.0, clip=False,
         shadows=True, ink=False):
    """Toon / ToonCharacter as nodes, with the three passes (colour, view normals, depth + mask) behind one switch.
    ink: the ink hull's material (shown only in the colour pass: the camera's depth-normals pass draws no hull)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    sw = nt.nodes.new('ShaderNodeGroup'); sw.node_tree = PASS
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    if ink:
        e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (1.0, 0.0, 1.0, 1) if DIAG == 'crack' else (0.012, 0.01, 0.016, 1)
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
        nt.links.new(sw.outputs['normal'], mx.inputs[0]); nt.links.new(sw.outputs['data'], mx.inputs[1])
        ms = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(mx.outputs[0], ms.inputs[0]); nt.links.new(e.outputs[0], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs['Surface'])
        m['comicworld'] = mask
        return m
    rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = tuple(colour) + (1,)
    albedo = rgb.outputs[0]
    alpha = None
    if DIAG == 'parts' and name.startswith('fig'):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = os.environ.get('PARTS_UV', 'Parts')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(attr.outputs['Vector'], sep.inputs[0])
        ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
        mp = nt.nodes.new('ShaderNodeMath'); mp.operation = 'DIVIDE'; mp.inputs[1].default_value = 5.0
        nt.links.new(sep.outputs[0], mp.inputs[0]); nt.links.new(mp.outputs[0], ramp.inputs[0])
        el = ramp.color_ramp.elements; el[0].position = 0.0; el[0].color = (1, 1, 1, 1); el[1].position = 0.18; el[1].color = (1, 0, 0, 1)
        for pos, c in ((0.38, (0, 0.2, 1, 1)), (0.58, (0, 0.8, 0, 1)), (0.78, (1, 0.9, 0, 1))):
            e = el.new(pos); e.color = c
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(ramp.outputs[0], em.inputs[0])
        nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
        m.use_backface_culling = True
        return m
    if tex is not None and DIAG == 'vc' and name.startswith('fig'): tex = None
    if vcol and DIAG == 'tex' and name.startswith('fig'): vcol = False
    if tex is not None:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = tex
        albedo = _mix(nt, t.outputs['Color'], albedo, 1.0, 'MULTIPLY')
        if clip:
            alpha = t.outputs['Alpha']
    if vcol:
        vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        albedo = _mix(nt, albedo, vc.outputs['Color'], 1.0, 'MULTIPLY')
    # the sun: N.L banded (smoothstep -0.02..0.06) and the cast shadow (a lit white diffuse, read back)
    L = nt.nodes.new('ShaderNodeCombineXYZ')
    L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = SUNDIR
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
    lit = nt.nodes.new('ShaderNodeMapRange'); lit.interpolation_type = 'SMOOTHSTEP'
    lit.inputs['From Min'].default_value = -0.02; lit.inputs['From Max'].default_value = 0.06
    nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
    light = lit.outputs['Result']
    if shadows:
        dif = nt.nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value = (1, 1, 1, 1)
        s2r = nt.nodes.new('ShaderNodeShaderToRGB'); nt.links.new(dif.outputs[0], s2r.inputs[0])
        bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(s2r.outputs['Color'], bw.inputs[0])
        # unshadowed, the diffuse reads max(N.L, 0) x SUNPOWER; a shadowed point far less
        ndl = nt.nodes.new('ShaderNodeMath'); ndl.operation = 'MAXIMUM'; ndl.inputs[1].default_value = 0.02
        nt.links.new(dot.outputs['Value'], ndl.inputs[0])
        ratio = nt.nodes.new('ShaderNodeMath'); ratio.operation = 'DIVIDE'
        nt.links.new(bw.outputs[0], ratio.inputs[0]); nt.links.new(ndl.outputs[0], ratio.inputs[1])
        sh = nt.nodes.new('ShaderNodeMapRange'); sh.interpolation_type = 'SMOOTHSTEP'
        sh.inputs['From Min'].default_value = 0.25; sh.inputs['From Max'].default_value = 0.7
        nt.links.new(ratio.outputs[0], sh.inputs['Value'])
        both = nt.nodes.new('ShaderNodeMath'); both.operation = 'MULTIPLY'
        nt.links.new(light, both.inputs[0]); nt.links.new(sh.outputs['Result'], both.inputs[1])
        light = both.outputs[0]
    shd = tuple(s + (1 - s) * (1 - lighting) for s in shade)
    band = _mix(nt, shd, SUN, light)
    col = _mix(nt, albedo, band, 1.0, 'MULTIPLY')
    if rim > 0:
        ndv = nt.nodes.new('ShaderNodeVectorMath'); ndv.operation = 'DOT_PRODUCT'
        nt.links.new(geo.outputs['Normal'], ndv.inputs[0]); nt.links.new(geo.outputs['Incoming'], ndv.inputs[1])
        rr = nt.nodes.new('ShaderNodeMapRange'); rr.interpolation_type = 'SMOOTHSTEP'
        # ToonCharacter's rim: smoothstep(0.66, 0.8, 1 - N.V), tinted by the albedo (lerp(albedo, 1, 0.45 * max(albedo)));
        # OLD_LOOK=1 draws the rim as it was before November 2026 (white, wider)
        OLD = os.environ.get('OLD_LOOK') == '1'
        rr.inputs['From Min'].default_value = 0.4 if OLD else 0.34; rr.inputs['From Max'].default_value = 0.24 if OLD else 0.2
        nt.links.new(ndv.outputs['Value'], rr.inputs['Value'])
        rk = nt.nodes.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'; rk.inputs[1].default_value = rim
        nt.links.new(rr.outputs['Result'], rk.inputs[0])
        # whitened by 45% of the albedo's lightness (its brightest channel), as ToonCharacter
        _sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(albedo, _sep.inputs['Color'])
        _m1 = nt.nodes.new('ShaderNodeMath'); _m1.operation = 'MAXIMUM'; nt.links.new(_sep.outputs[0], _m1.inputs[0]); nt.links.new(_sep.outputs[1], _m1.inputs[1])
        _m2 = nt.nodes.new('ShaderNodeMath'); _m2.operation = 'MAXIMUM'; nt.links.new(_m1.outputs[0], _m2.inputs[0]); nt.links.new(_sep.outputs[2], _m2.inputs[1])
        _fk = nt.nodes.new('ShaderNodeMath'); _fk.operation = 'MULTIPLY'; _fk.inputs[1].default_value = 0.45; nt.links.new(_m2.outputs[0], _fk.inputs[0])
        # (RIM_FLAT=1: whitened by 45% whatever the colour, as from November 2026 to v113)
        tint = _mix(nt, albedo, (1, 1, 1), 1.0 if OLD else (0.45 if os.environ.get('RIM_FLAT') == '1' else _fk.outputs[0]))
        tsun = _mix(nt, tint, SUN, 1.0, 'MULTIPLY')
        col = _mix(nt, col, tsun, rk.outputs[0], 'ADD')
    # the normal pass: view-space normal, 0.5 + 0.5 n
    vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    nt.links.new(geo.outputs['Normal'], vt.inputs[0])
    ma = nt.nodes.new('ShaderNodeVectorMath'); ma.operation = 'MULTIPLY_ADD'
    ma.inputs[1].default_value = (0.5, 0.5, 0.5); ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(vt.outputs[0], ma.inputs[0])
    # the data pass: depth / FAR in two 8-bit halves, the mask in blue
    cd = nt.nodes.new('ShaderNodeCameraData')
    dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = FAR
    nt.links.new(cd.outputs['View Z Depth'], dv.inputs[0])
    m255 = nt.nodes.new('ShaderNodeMath'); m255.operation = 'MULTIPLY'; m255.inputs[1].default_value = 255.0
    nt.links.new(dv.outputs[0], m255.inputs[0])
    fl = nt.nodes.new('ShaderNodeMath'); fl.operation = 'FLOOR'; nt.links.new(m255.outputs[0], fl.inputs[0])
    hi = nt.nodes.new('ShaderNodeMath'); hi.operation = 'DIVIDE'; hi.inputs[1].default_value = 255.0; nt.links.new(fl.outputs[0], hi.inputs[0])
    lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'FRACT'; nt.links.new(m255.outputs[0], lo.inputs[0])
    cc = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(hi.outputs[0], cc.inputs[0]); nt.links.new(lo.outputs[0], cc.inputs[1]); cc.inputs[2].default_value = mask
    final = _mix(nt, col, ma.outputs[0], sw.outputs['normal'])
    final = _mix(nt, final, cc.outputs[0], sw.outputs['data'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(final, em.inputs['Color'])
    surf = em.outputs[0]
    if alpha is not None:
        cut = nt.nodes.new('ShaderNodeMath'); cut.operation = 'GREATER_THAN'; cut.inputs[1].default_value = 0.5
        nt.links.new(alpha, cut.inputs[0])
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        ms = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(cut.outputs[0], ms.inputs[0]); nt.links.new(tr.outputs[0], ms.inputs[1]); nt.links.new(surf, ms.inputs[2])
        surf = ms.outputs[0]
        m.use_backface_culling = False
    nt.links.new(surf, out.inputs['Surface'])
    m['comicworld'] = mask
    return m


# ---------------------------------------------------------------- placing things
def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def meshes(objs):
    return [o for o in objs if o.type == 'MESH']


def bounds(objs, evaluated=False):
    bpy.context.view_layer.update()
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes(objs):
        if evaluated:
            ev = o.evaluated_get(dg); me = ev.to_mesh()
            n = len(me.vertices)
            co = [0.0] * (n * 3); me.vertices.foreach_get('co', co)
            M = ev.matrix_world
            pts += [M @ Vector(co[i * 3:i * 3 + 3]) for i in range(0, n, 5)]
            ev.to_mesh_clear()
        else:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def place(objs, loc, yaw=0.0, scale=1.0, anchor='front', evaluated=False):
    """Turn, scale and move a model so its footprint's front (or centre) and its base sit at loc."""
    roots = [o for o in objs if o.parent is None]
    for r in roots:
        r.scale = r.scale * scale
        r.rotation_euler.z += math.radians(yaw)
    mn, mx = bounds(objs, evaluated)
    c = Vector(((mn.x + mx.x) / 2, mn.y if anchor == 'front' else (mn.y + mx.y) / 2, mn.z))
    for r in roots:
        r.location += Vector(loc) - c
    bpy.context.view_layer.update()


MATS = {}


def kit_material(kit, cel=False):
    """The kit's toon material; cel: a copy that marks the model as a cel (0 in the mask, like the people), for the
    things the kid plays with (the classic cartoon filter inks them like the people; the scenery is painted)."""
    if cel:
        key = kit + 'Cel'
        if key not in MATS:
            atlas = kit + 'Atlas.png'
            MATS[key] = toon(key, tex=image(os.path.join(MODELS, kit, atlas)), mask=0.0)
        return MATS[key]
    if kit not in MATS:
        atlas = 'BuildingsCAAtlas.png' if kit == 'BuildingsCA' else kit + 'Atlas.png'
        folder = 'Buildings' if kit == 'BuildingsCA' else kit
        clip = kit == 'Plants'
        # the plants write 0.5 into the mask (foliage: the filter inks a crown's outline, not every leaf clump)
        MATS[kit] = toon(kit, tex=image(os.path.join(MODELS, folder, atlas)), clip=clip, lighting=0.85 if clip else 1.0,
                         mask=0.5 if clip else 1.0)
    return MATS[kit]


def ink(mask, key):
    k = 'ink%s' % key
    if k not in MATS:
        MATS[k] = toon(k, mask=mask, ink=True)
    return MATS[k]


HOLLOW = None


def outline(objs, width, mask, push=0.0):
    """ToonCharacter's ink hull: back faces pushed out (a flipped solidify). push (m): the hull set back from the camera, as
    ToonCharacter's _OutlinePush (0.012), so the folds inside the figure (round a nose, a mouth's corner) draw no ink: the
    hull is then a copy of the figure (its own surface drawn as nothing) moved that far away from the camera, which looks
    along +y in every scene here (docs/LEARNINGS.md C20: without it the review boards drew ink specks the game doesn't)."""
    global HOLLOW
    mat = ink(mask, mask)
    for o in meshes(objs):
        if push <= 0:
            o.data.materials.append(mat)
            sol = o.modifiers.new('ink', 'SOLIDIFY'); sol.thickness = width; sol.offset = 1
            sol.use_flip_normals = True; sol.material_offset = len(o.data.materials) - 1
            continue
        if HOLLOW is None:
            HOLLOW = bpy.data.materials.new('hollow'); HOLLOW.use_nodes = True
            nt = HOLLOW.node_tree; tr = nt.nodes.new('ShaderNodeBsdfTransparent')
            nt.links.new(tr.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
        d = o.copy(); d.data = o.data.copy(); d.name = o.name + '.ink'
        for c in o.users_collection: c.objects.link(d)
        d.data.materials.clear(); d.data.materials.append(HOLLOW); d.data.materials.append(mat)
        for poly in d.data.polygons: poly.material_index = 0
        sol = d.modifiers.new('ink', 'SOLIDIFY'); sol.thickness = width; sol.offset = 1
        sol.use_flip_normals = True; sol.material_offset = 1
        d.visible_shadow = False
        d.matrix_world = Matrix.Translation((0.0, push, 0.0)) @ o.matrix_world


CELS = {'Animals': None, 'Street': {'CrateStack', 'Crate', 'TrafficCone', 'RoadBarrier', 'ProduceCrate'},
        'Works': {'ConcretePipe', 'Wheelbarrow'}, 'Leisure': {'CheckpointFlag', 'Target', 'SlalomFlag'}}


def kit(kitname, model, loc, yaw=0.0, scale=1.0, anchor='front'):
    folder = 'Buildings' if kitname == 'BuildingsCA' else kitname
    objs = import_fbx(os.path.join(MODELS, folder, model + '.fbx'))
    cel = kitname in CELS and (CELS[kitname] is None or model in CELS[kitname])
    mat = kit_material(kitname, cel)
    for o in meshes(objs):
        o.data.materials.clear(); o.data.materials.append(mat)
    place(objs, loc, yaw, scale, anchor)
    return objs


def car(model, loc, yaw=90.0):
    objs = import_fbx(os.path.join(MODELS, 'Cars', model + '.fbx'))
    k = 'car' + model
    if k not in MATS:
        MATS[k] = toon(k, tex=image(os.path.join(MODELS, 'Cars', model + 'Atlas.png')), shade=(0.66, 0.68, 0.86), mask=0.0)
    for o in meshes(objs):
        o.data.materials.clear(); o.data.materials.append(MATS[k])
    place(objs, loc, yaw, 1.0, 'centre')
    outline(objs, 0.03, 0.0)
    return objs


def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def plain(name, colour, shade=KIT_SHADE, mask=1.0, lighting=1.0, rim=0.0):
    k = 'plain' + name
    if k not in MATS:
        MATS[k] = toon(k, colour=colour, shade=shade, mask=mask, vcol=False, lighting=lighting, rim=rim)
    return MATS[k]


# ---------------------------------------------------------------- the people: posed as CharacterRig does
def P(**k):
    d = dict(legF=0, legB=0, kneeF=-4, kneeB=-4, armF=0, armB=0, elbowF=12, elbowB=12, lean=0, headTilt=0, bag=0)
    d.update(k)
    return d


def walk_pose(phase):
    s = math.sin(phase)
    return P(legF=s * 20, legB=-s * 20, kneeF=-(6 + 22 * max(0, math.cos(phase + 0.9))), kneeB=-(6 + 22 * max(0, math.cos(phase + math.pi + 0.9))),
             armF=-s * 16, armB=s * 16, elbowF=16, elbowB=16)


def run_pose(phase):
    def fold(a):
        s = max(0.0, math.cos(a + 0.9)); return 14.0 + 80.0 * s * s
    s = math.sin(phase)
    return P(legF=s * 42, legB=-s * 42, kneeF=-fold(phase), kneeB=-fold(phase + math.pi),
             armF=-s * 34 - 6, armB=s * 34 - 6, elbowF=70 + 25 * max(0, -s), elbowB=70 + 25 * max(0, s),
             lean=7, headTilt=0.75 * 7 - 2 - 2.5 * math.cos(2 * (phase - 0.35)), bag=-10 - math.sin(phase * 2) * 6)


BALANCE = dict(legF=4, legB=-2, kneeF=-8, kneeB=-8, armF=22, elbowF=34, armB=-16, elbowB=28, headTilt=-13)
KICK_ARMS = dict(armB=43, elbowB=29, armF=-28, elbowF=30)
POSES = {
    'idle': P(kneeF=-5, kneeB=-5, armF=-3, armB=3, elbowF=14, elbowB=14),
    'walk': P(legF=18, legB=-16, kneeF=-12, kneeB=-30, armF=-14, armB=12, elbowF=20, elbowB=24),
    'run_stride': run_pose(math.pi / 2),
    'run_kneeup': run_pose(-0.9),
    'jump_rise': P(legF=48, kneeF=-95, legB=-22, kneeB=-70, armF=-35, elbowF=85, armB=55, elbowB=60, lean=8, bag=-25),
    'kick_contact': P(legF=80, kneeF=0, kneeB=-14, lean=-6.5, **KICK_ARMS),
    'keepy_thigh': P(**dict(BALANCE, legF=86, kneeF=-96, kneeB=-12, lean=-4)),
    'celebrate': P(legF=12, legB=-8, kneeF=-10, kneeB=-10, armF=172, armB=-172, elbowF=15, elbowB=15, headTilt=6),
}


def person(model, loc, yaw, pose, height, bag=None, mask=0.0, ink_w=0.006, rim=0.2, lift=0.0):
    if DIAG in ('norim', 'crack', 'vc', 'tex', 'parts'): rim = 0.0
    """A kid or a passer-by from its FBX: its atlas times its vertex colours, one Locker Room bag (or none), posed
    with the game's joint angles, scaled to its standing height, turned by yaw (66 = the game's three-quarter view
    running right; 0 faces the camera), its feet on the ground (or lift above it)."""
    objs = import_fbx(os.path.join(MODELS, model + '.fbx'))
    rig = [o for o in objs if o.type == 'ARMATURE'][0]
    k = 'fig' + model
    if k not in MATS:
        MATS[k] = toon(k, tex=image(os.path.join(MODELS, model + 'Atlas.png'), packed=True), shade=FIG_SHADE, mask=mask, rim=rim)
    body = None
    keep = [o for o in objs if not (o.type == 'MESH' and o.name.startswith('Bag_') and o.name[4:].split('.')[0] != bag)]
    for o in objs:
        if o not in keep:
            bpy.data.objects.remove(o)
    objs = keep
    for o in meshes(objs):
        if o.name.startswith('Bag_'):
            bid = o.name[4:].split('.')[0]
            bk = 'bag' + bid
            if bk not in MATS:
                MATS[bk] = toon(bk, tex=image(os.path.join(MODELS, 'Bag%sAtlas.png' % bid), packed=True), shade=FIG_SHADE, mask=mask, rim=rim)
            o.data.materials.clear(); o.data.materials.append(MATS[bk])
        else:
            o.data.materials.clear(); o.data.materials.append(MATS[k]); body = o
    zs = [v.co.z for v in body.data.vertices]
    native = max(zs) - min(zs)
    p = POSES[pose]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    side = Vector((1, 0, 0))

    def swing(bone, a, sign=-1):
        if bone not in rig.pose.bones:
            return
        pb = rig.pose.bones[bone]
        axis = pb.bone.matrix_local.to_3x3().inverted() @ side
        pb.rotation_quaternion = Quaternion(axis, math.radians(sign * a))
    for n, f in (('R', 'F'), ('L', 'B')):
        swing('UpperLeg.' + n, p['leg' + f]); swing('LowerLeg.' + n, min(p['knee' + f], 0))
        swing('UpperArm.' + n, p['arm' + f]); swing('LowerArm.' + n, max(p['elbow' + f], 0))
    swing('Bag', p['bag'] * 0.3); swing('Head', float(os.environ['HEAD_TILT']) if os.environ.get('HEAD_TILT') else p['headTilt']); swing('Hips', p['lean'], sign=+1)
    # the torso, as CharacterRig.Torso (TORSO=0: the rigid torso of v114 and before). In Blender's axes the figure faces -y,
    # its near (right) side is -x: a turn about +z brings the near side forward; a sway about +y tips the top to +x (away).
    if os.environ.get('TORSO', '1') == '1' and 'Spine' in rig.pose.bones:
        def turn(bone, turn_deg, sway_deg, dip_deg=0.0):
            # dip: forward, about the side axis (+x here: a positive turn about +x tips the top toward -y, forward)
            if bone not in rig.pose.bones: return
            pb = rig.pose.bones[bone]; inv = pb.bone.matrix_local.to_3x3().inverted()
            q = Quaternion(inv @ Vector((0, 0, 1)), math.radians(turn_deg)) @ Quaternion(inv @ Vector((0, 1, 0)), math.radians(-sway_deg)) \
                @ Quaternion(inv @ Vector((1, 0, 0)), math.radians(dip_deg))
            pb.rotation_quaternion = q @ pb.rotation_quaternion
        sn = lambda a: math.sin(math.radians(a))
        arms = sn(p['armF']) - sn(p['armB']); legs = sn(p['legF']) - sn(p['legB'])
        ct = max(-15.0, min(15.0, arms * 11.0)); ht = max(-10.0, min(10.0, legs * 6.5))
        apart = min(1.0, abs(legs) / 0.4)
        sway = max(-1.0, min(1.0, (abs(p['kneeB']) - abs(p['kneeF'])) / 40.0)) * apart * 3.0
        dip = 2.0 * min(1.0, abs(legs) / 1.2)
        back = (ct - ht) * 0.5
        turn('Hips', ht, 0.0); turn('Spine', back, sway, dip * 0.5); turn('Chest', back, 0.0, dip * 0.5); turn('Head', -ct, -sway, -dip)
    rig.scale = (height / native,) * 3
    rig.rotation_euler.z = math.radians(yaw)
    bpy.context.view_layer.update()
    mn, mx = bounds(objs, evaluated=True)
    rig.location += Vector((loc[0] - (mn.x + mx.x) / 2, loc[1] - (mn.y + mx.y) / 2, loc[2] + lift - mn.z))
    bpy.context.view_layer.update()
    outline(objs, ink_w * native / height * 0.6, mask, push=float(os.environ.get('OUTLINE_PUSH', '0.012')))
    # as in the game (LevelBuildKit.BuildModelCharacter): characters cast no shadows (and receive none)
    if os.environ.get('NO_CHAR_SHADOWS', '1') == '1':
        for o in objs:
            if o.type == 'MESH': o.visible_shadow = False
    return objs


def ball(loc, r=0.15):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=loc)
    b = bpy.context.object; b.name = 'Ball'
    bpy.ops.object.shade_smooth()
    b.data.materials.append(plain('BallWhite', (0.95, 0.95, 0.95), FIG_SHADE, mask=0.0, rim=0.2))
    b.data.materials.append(plain('BallBlack', (0.06, 0.06, 0.08), FIG_SHADE, mask=0.0))
    cs = [Vector(v).normalized() for v in [(0, 0, 1), (0.89, 0, 0.45), (0.28, 0.85, 0.45), (-0.72, 0.53, 0.45), (-0.72, -0.53, 0.45),
                                           (0.28, -0.85, 0.45), (0, 0, -1), (-0.89, 0, -0.45), (0.72, 0.53, -0.45), (0.72, -0.53, -0.45),
                                           (-0.28, 0.85, -0.45), (-0.28, -0.85, -0.45)]]
    for f in b.data.polygons:
        if max(f.normal.normalized().dot(c) for c in cs) > 0.93:
            f.material_index = 1
    b.rotation_euler = (0.4, 0.3, 0.2)
    outline([b], 0.008, 0.0)
    return b


def cloud(centre, size):
    """WorldLook's cumulus: a heap of puffs with a flat bottom, white with blue-grey undersides."""
    mat = plain('Cloud', (1.0, 1.0, 1.0), shade=(0.86, 0.9, 0.97), lighting=0.6)
    cx, cy, cz = centre
    for i in range(9):
        r = size * random.uniform(0.35, 0.6)
        dx = random.uniform(-1.1, 1.1) * size
        dz = r * random.uniform(0.2, 0.9) * (1.0 - abs(dx) / (1.6 * size))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=(cx + dx, cy + random.uniform(-0.3, 0.3) * size, cz + dz))
        o = bpy.context.object; bpy.ops.object.shade_smooth(); o.data.materials.append(mat)
        for v in o.data.vertices:
            if (o.matrix_world @ v.co).z < cz:
                v.co.z = (cz - o.location.z)


# ---------------------------------------------------------------- the ground
def street(road=True, footpath=(0.74, 0.71, 0.70), length=120):
    box('Footpath', (0, 0.0, -0.05), (length, 5.2, 0.1), plain('Paving', footpath))
    if road:
        box('Kerb', (0, -2.7, -0.03), (length, 0.25, 0.16), plain('Kerb', (0.82, 0.8, 0.78)))
        box('Road', (0, -7.0, -0.12), (length, 8.4, 0.1), plain('Road', (0.4, 0.38, 0.41)))
        for i in range(-12, 13):
            box('Dash%d' % i, (i * 5.0, -6.2, -0.065), (2.6, 0.14, 0.01), plain('Paint', (0.92, 0.92, 0.9)))
    box('Back', (0, 132.4, -0.06), (length * 4, 260, 0.1), plain('Lot', (0.62, 0.66, 0.5)))


def coins(x0, z, n=3, gap=0.75, y=0.0):
    for i in range(n):
        kit('Animals', 'Coin', (x0 + i * gap, y, z), yaw=random.uniform(-25, 25), anchor='centre')


def hills(y=170, kind='HillsRolling', x=0.0, scale=1.0):
    kit('Terrain', kind, (x, y, -1.0), scale=scale, anchor='front')


# ---------------------------------------------------------------- the places
CAM = dict(x=0.0, back=10.5, up=2.6, look=2.4, fov=34.0)


def scene_home():
    street()
    for i in range(-9, 10):
        kit('Street', 'BlockWall2', (i * 2.0 + 1.0, 2.62, 0.0))
        if i % 2 == 0:
            kit('Street', 'WallPillar', (i * 2.0, 2.55, 0.0))
    kit('Buildings', 'HouseFlat', (-8.8, 5.2, 0.0))
    kit('Buildings', 'Bungalow', (0.6, 5.0, 0.0))
    kit('Buildings', 'HouseGable', (10.6, 5.6, 0.0))
    kit('Buildings', 'HouseLeanTo', (-19.5, 5.6, 0.0))
    kit('Buildings', 'Garage', (5.6, 4.4, 0.0))
    kit('Plants', 'GardenPine', (-3.8, 3.5, 0.0))
    kit('Plants', 'CherryBlossom', (16.5, 3.8, 0.0))
    kit('Plants', 'BroadleafSmall', (16.0, 3.4, 0.0))
    kit('Street', 'UtilityPole', (-4.6, -2.35, 0.0))
    kit('Street', 'UtilityPole', (13.0, -2.35, 0.0))
    kit('Street', 'VendingRed', (-10.6, 1.4, 0.0))
    kit('Street', 'PostBox', (4.9, 1.7, 0.0))
    kit('Street', 'BinPair', (-6.6, 1.65, 0.0))
    kit('Street', 'Bicycle', (2.6, 1.85, 0.0))
    kit('Street', 'PotGroup', (9.4, 1.8, 0.0))
    kit('Animals', 'Cat', (6.0, 2.6, 1.62), yaw=200)
    car('Hatch', (-7.0, -5.0, 0.0), yaw=90)
    hills(180)
    for c in [(-30, 170, 38, 9), (14, 160, 46, 11), (52, 190, 34, 8)]:
        cloud(c[:3], c[3])
    person('PrimaryBoy2', (0.0, -0.3, 0.0), 66, 'run_stride', 1.32, bag='KickOff')
    ball((0.85, -0.45, 0.15))
    coins(2.4, 1.35)


def scene_market():
    street()
    for j in range(7):
        box('Stripe%d' % j, (4.6 + j * 0.9, -6.9, -0.065), (0.5, 7.6, 0.01), plain('Paint', (0.92, 0.92, 0.9)))
    kit('Buildings', 'ShopFruit', (-9.0, 3.4, 0.0))
    kit('Buildings', 'ShopCafe', (-1.2, 3.4, 0.0))
    kit('Buildings', 'ShopFlorist', (6.0, 3.4, 0.0))
    kit('Buildings', 'ShopNoodle', (12.8, 3.4, 0.0))
    kit('Buildings', 'ShopBooks', (-15.8, 3.4, 0.0))
    kit('Street', 'MarketStall', (-4.8, 1.5, 0.0))
    kit('Street', 'CrateStack', (2.9, 0.6, 0.0))
    kit('Street', 'ProduceCrate', (-6.9, 1.7, 0.0))
    kit('Street', 'DrinksCrates', (-2.6, 2.4, 0.0))
    kit('Street', 'SignBoardA', (1.2, 2.2, 0.0), yaw=-20)
    kit('Street', 'BannerFlag', (8.9, 2.3, 0.0))
    kit('Street', 'Planter2', (-11.6, 2.4, 0.0))
    kit('Street', 'PedSignal', (4.0, -2.35, 0.0))
    kit('Street', 'SignCrossing', (10.6, -2.4, 0.0))
    kit('Street', 'StreetLamp', (-8.0, -2.35, 0.0))
    kit('Animals', 'Pigeon', (-1.6, 1.2, 0.0), yaw=160)
    kit('Animals', 'Pigeon', (-1.1, 1.5, 0.0), yaw=20)
    car('Van', (8.4, -5.4, 0.0), yaw=90)
    hills(200, 'MountainRange1', scale=0.8)
    for c in [(-24, 160, 40, 10), (26, 175, 50, 12)]:
        cloud(c[:3], c[3])
    person('Adult', (-3.0, 0.9, 0.0), -70, 'walk', 1.7, mask=0.0, rim=0.22)
    person('PrimaryGirl', (0.4, -0.3, 0.0), 66, 'kick_contact', 1.27, bag='DenimBow')
    ball((1.45, -0.4, 0.62))
    coins(3.0, 1.9, 2)


def scene_beach():
    box('Sand', (0, 4, -0.05), (160, 30, 0.1), plain('Sand', (0.93, 0.83, 0.62)))
    box('Wet', (0, 19.6, -0.06), (160, 1.6, 0.1), plain('WetSand', (0.78, 0.68, 0.52)))
    box('Foam', (0, 20.6, -0.055), (160, 0.5, 0.1), plain('Foam', (0.97, 0.98, 0.98), lighting=0.4))
    box('Shallows', (0, 23.5, -0.07), (400, 5.5, 0.1), plain('Shallows', (0.33, 0.78, 0.8), lighting=0.3))
    box('Sea', (0, 140, -0.08), (900, 230, 0.1), plain('Sea', (0.1, 0.42, 0.72), lighting=0.3))
    kit('Terrain', 'Headland', (-70, 120, -0.5), yaw=10)
    kit('Terrain', 'SandDune1', (-12.0, 8.0, -0.3))
    kit('Terrain', 'SandDune2', (14.0, 10.0, -0.3))
    kit('Plants', 'Palm', (-8.8, 5.2, 0.0))
    kit('Plants', 'PalmShort', (10.6, 6.5, 0.0))
    kit('Plants', 'PalmFan', (-16.0, 12.0, 0.0))
    kit('Plants', 'DuneGrass', (-5.0, 2.2, 0.0)); kit('Plants', 'DuneGrass', (6.6, 2.6, 0.0)); kit('Plants', 'DuneGrass', (-11.4, 1.8, 0.0))
    kit('Leisure', 'LifeguardTower', (5.2, 6.4, 0.0))
    kit('Leisure', 'Parasol', (-3.4, 3.6, 0.0))
    kit('Leisure', 'BeachTowel', (-3.0, 3.0, 0.0), yaw=8)
    kit('Leisure', 'CoolBox', (-1.6, 3.5, 0.0))
    kit('Leisure', 'SandCastle', (2.7, 0.7, 0.0))
    kit('Leisure', 'BucketSpade', (3.4, 0.5, 0.0))
    kit('Barriers', 'RescueBoardStand', (-8.0, 1.6, 0.0))
    kit('Barriers', 'SurfRack', (12.6, 3.0, 0.0), yaw=90)
    kit('Animals', 'SeagullStanding', (4.3, 1.4, 0.0), yaw=200)
    kit('Animals', 'Seagull', (-2.0, 2.0, 4.0), yaw=20, anchor='centre')
    kit('Animals', 'Seagull', (7.0, 6.0, 6.2), yaw=-160, anchor='centre')
    kit('Animals', 'Crab', (-1.4, -1.2, 0.0), yaw=30)
    for c in [(-40, 180, 32, 10), (8, 170, 42, 12), (50, 185, 30, 9)]:
        cloud(c[:3], c[3])
    person('PrimaryGirl2', (0.0, -0.2, 0.0), 66, 'jump_rise', 1.29, bag='Unicorn', lift=0.45)
    ball((1.2, -0.3, 1.05))
    coins(2.2, 2.1, 3, 0.7)


def scene_site():
    street(road=True, footpath=(0.66, 0.6, 0.52))
    for i in range(-5, 6):
        kit('Works', 'SiteFence', (i * 3.7, 3.0, 0.0))
    kit('Street', 'Hoarding3', (-1.5, 2.55, 0.0))
    kit('Works', 'Scaffold', (-6.0, 6.2, 0.0)); kit('Works', 'Scaffold', (-3.8, 6.2, 0.0)); kit('Works', 'Scaffold', (-1.6, 6.2, 0.0))
    kit('Buildings', 'Apartment', (-4.5, 7.8, 0.0))
    kit('Works', 'TowerCrane', (12.0, 120.0, 0.0), yaw=-15)
    kit('Works', 'Digger', (-7.6, 2.0, 0.0), yaw=15)
    kit('Works', 'CementMixer', (4.4, 1.1, 0.0))
    kit('Works', 'Skip', (10.4, 2.4, 0.0))
    kit('Works', 'ConcretePipe', (-2.9, 0.0, 0.0), yaw=90)
    kit('Works', 'PipeStack', (7.2, 1.4, 0.0))
    kit('Works', 'SiteCabin', (15.0, 4.2, 0.0))
    kit('Works', 'PortaLoo', (7.5, 4.4, 0.0))
    kit('Works', 'Wheelbarrow', (2.6, 1.7, 0.0), yaw=-20)
    kit('Works', 'SteelBeams', (12.4, 0.8, 0.0))
    for x in (-6.0, -5.0, 3.8, 4.4):
        kit('Street', 'TrafficCone', (x, -2.0, 0.0))
    kit('Street', 'RoadBarrier', (-4.1, -1.9, 0.0))
    hills(200, 'MountainRange2', scale=0.8)
    for c in [(-20, 160, 44, 10), (30, 185, 36, 9)]:
        cloud(c[:3], c[3])
    person('Adult', (-4.6, 1.3, 0.0), -30, 'idle', 1.75, mask=0.0, rim=0.22)
    person('PrimaryBoy', (0.6, -0.4, 0.0), 66, 'run_kneeup', 1.30, bag='RaceCar')
    ball((1.45, -0.5, 0.15))
    coins(-1.7, 2.0, 3, 0.6)


def scene_park():
    box('Grass', (0, 129, -0.06), (600, 262, 0.1), plain('Grass', (0.45, 0.68, 0.32)))
    box('Path', (0, -0.2, -0.04), (160, 3.4, 0.1), plain('Gravel', (0.86, 0.78, 0.62)))
    box('Verge', (0, -6.0, -0.05), (160, 8.0, 0.1), plain('Grass', (0.45, 0.68, 0.32)))
    kit('Plants', 'Broadleaf', (-9.5, 7.0, 0.0))
    kit('Plants', 'BroadleafLarge', (-19.0, 11.0, 0.0))
    kit('Plants', 'Birch', (-3.6, 9.0, 0.0))
    kit('Plants', 'CherryBlossom', (2.4, 8.2, 0.0))
    kit('Plants', 'BushRound', (-6.2, 2.5, 0.0)); kit('Plants', 'ShrubFlowering', (0.6, 2.6, 0.0))
    kit('Plants', 'FlowerPatch', (-1.0, 2.0, 0.0)); kit('Plants', 'FlowerPatch', (3.0, 2.2, 0.0))
    kit('Leisure', 'DuckPond', (-7.2, 4.6, 0.0))
    kit('Animals', 'Duck', (-6.8, 5.6, 0.42), yaw=160)
    kit('Leisure', 'SwingSet', (-2.6, 6.0, 0.0))
    kit('Leisure', 'Slide', (-15.8, 4.8, 0.0))
    kit('Street', 'Bench', (-1.8, 2.3, 0.0))
    kit('Leisure', 'ParkLamp', (-4.4, 1.9, 0.0))
    kit('Animals', 'Squirrel', (-1.6, 2.3, 0.45), yaw=200)
    kit('Works', 'SchoolArch', (4.6, -0.2, 0.0), anchor='centre')
    for i in range(6):
        kit('Works', 'SchoolWall', (6.6 + i * 2.0, 2.9, 0.0))
    kit('Works', 'SchoolSign', (7.4, 2.55, 0.9))
    kit('Buildings', 'School', (20.0, 9.5, 0.0))
    kit('Plants', 'HedgeBlock2', (-13.5, 1.8, 0.0))
    for c in [(-28, 165, 42, 11), (20, 180, 50, 10)]:
        cloud(c[:3], c[3])
    hills(200)
    kit('Animals', 'Dog', (-1.7, -0.5, 0.0), yaw=0)
    person('Girl', (0.6, -0.2, 0.0), 66, 'run_stride', 1.65, bag='GoldenTrail')
    ball((1.6, -0.35, 0.15))
    coins(2.6, 1.8, 2)


def scene_california():
    street(footpath=(0.8, 0.77, 0.72))
    for i in range(-10, 10):
        kit('Street', 'PicketFence2', (i * 2.0 + 1.0, 2.7, 0.0))
    kit('Coast', 'VillaStucco', (-9.5, 4.2, 0.0))
    kit('Coast', 'ShopMission', (2.0, 4.0, 0.0))
    kit('Coast', 'CraftsmanPorch', (11.2, 4.2, 0.0))
    kit('Coast', 'BeachCondo', (-21.0, 5.0, 0.0))
    kit('Plants', 'Palm', (-4.6, 3.6, 0.0))
    kit('Plants', 'PalmShort', (7.4, 3.4, 0.0))
    kit('Plants', 'PalmFan', (-14.0, 9.0, 0.0))
    kit('Plants', 'PalmDate', (16.5, 4.2, 0.0))
    kit('Plants', 'BushRound', (-5.6, 3.3, 0.0))
    kit('Street', 'StreetLamp', (-5.0, -2.35, 0.0))
    kit('Street', 'Bin', (4.6, 1.9, 0.0))
    kit('Leisure', 'SignBoard', (-12.5, 2.1, 0.0))
    car('Fourby', (6.0, -5.2, 0.0), yaw=90)
    hills(200, 'MountainRange1', scale=0.9)
    for c in [(-30, 170, 40, 10), (20, 165, 46, 11)]:
        cloud(c[:3], c[3])
    person('BackpackBoy', (0.0, -0.3, 0.0), 66, 'run_stride', 1.75, bag='KickOff')
    ball((1.0, -0.45, 0.15))
    coins(2.4, 1.9, 3)


def cast_backdrop():
    box('Footpath', (0, 0.0, -0.05), (40, 6, 0.1), plain('Paving', (0.74, 0.71, 0.70)))
    box('Back', (0, 20, -0.06), (60, 30, 0.1), plain('Lot', (0.62, 0.66, 0.5)))
    for i in range(-5, 6):
        kit('Street', 'BlockWall2', (i * 2.0 + 1.0, 2.1, 0.0))
        if i % 2 == 0:
            kit('Street', 'WallPillar', (i * 2.0, 2.05, 0.0))
    kit('Plants', 'GardenPine', (-2.4, 3.2, 0.0))
    kit('Buildings', 'Bungalow', (1.8, 4.4, 0.0))
    for c in [(-20, 150, 30, 9), (18, 140, 36, 10)]:
        cloud(c[:3], c[3])


def scene_cast_a():
    """Hana, Max and Kai, the dog and the ball, close up, three-quarter on (as the menus and a zoomed camera see them)."""
    cast_backdrop()
    person('Girl', (-1.7, 0.0, 0.0), 30, 'idle', 1.65, bag='GoldenTrail')
    person('BackpackBoy', (0.0, 0.1, 0.0), 30, 'idle', 1.75, bag='KickOff')
    person('PrimaryBoy', (1.6, 0.0, 0.0), 30, 'keepy_thigh', 1.30, bag='RaceCar')
    kit('Animals', 'Dog', (-0.75, -0.9, 0.0), yaw=-25)
    ball((1.95, -0.25, 0.95))


def scene_cast_b():
    """Mia, Leo and Zoe, a passer-by, the cat on the wall, a gull and the ball."""
    cast_backdrop()
    person('PrimaryGirl', (-1.7, 0.0, 0.0), 30, 'idle', 1.27, bag='DenimBow')
    person('PrimaryBoy2', (-0.1, 0.0, 0.0), 30, 'celebrate', 1.32, bag='KickOff')
    person('PrimaryGirl2', (1.4, 0.0, 0.0), 30, 'idle', 1.29, bag='Unicorn')
    person('Adult', (2.55, 0.7, 0.0), -20, 'walk', 1.72)
    kit('Animals', 'Cat', (-0.9, 2.1, 1.62), yaw=200)
    kit('Animals', 'SeagullStanding', (0.75, -0.9, 0.0), yaw=-40)
    ball((-1.0, -0.6, 0.15))


def scene_menu():
    """The title screen's live backdrop: down the home street, the chosen kid (Leo) juggling on the footpath, right of
    the menu's column."""
    cast_backdrop()
    kit('Street', 'PostBox', (3.6, 1.4, 0.0))
    kit('Street', 'Bicycle', (-1.0, 1.55, 0.0))
    person('PrimaryBoy2', (1.55, -0.3, 0.0), 30, 'keepy_thigh', 1.32, bag='KickOff')
    ball((1.95, -0.55, 1.0))


def scene_kids():
    """the four primary-school kids side by side, three-quarter on, as the menus see them"""
    cast_backdrop()
    person('PrimaryBoy', (-1.95, 0.0, 0.0), 25, 'idle', 1.30, bag='RaceCar')
    person('PrimaryBoy2', (-0.65, 0.0, 0.0), 25, 'idle', 1.32, bag='KickOff')
    person('PrimaryGirl', (0.65, 0.0, 0.0), 25, 'idle', 1.27, bag='DenimBow')
    person('PrimaryGirl2', (1.95, 0.0, 0.0), 25, 'idle', 1.29, bag='Unicorn')


def scene_teens():
    """Hana and Max, front and three-quarter"""
    cast_backdrop()
    person('Girl', (-1.6, 0.0, 0.0), 25, 'idle', 1.65, bag='GoldenTrail')
    person('Girl', (-0.55, 0.0, 0.0), 0, 'idle', 1.65, bag='GoldenTrail')
    person('BackpackBoy', (0.55, 0.0, 0.0), 0, 'idle', 1.75, bag='KickOff')
    person('BackpackBoy', (1.65, 0.0, 0.0), 25, 'idle', 1.75, bag='KickOff')


def scene_gait():
    """one character at four moments of its run, three-quarter on (as the game's camera sees a run): GAIT=walk for the
    walk; SOLO, SOLO_H, SOLO_BAG as for solo"""
    cast_backdrop()
    m = os.environ.get('SOLO', 'PrimaryBoy'); bag = os.environ.get('SOLO_BAG') or None
    h = float(os.environ.get('SOLO_H', '1.3'))
    walk = os.environ.get('GAIT') == 'walk'
    off = float(os.environ.get('GAIT_OFFSET', '0'))      # (radians: pi gives the other half of the cycle)
    for i in range(4):
        ph = off + i * math.pi / 4
        key = 'gait%d' % i
        POSES[key] = walk_pose(ph) if walk else run_pose(ph)
        person(m, (-1.95 + i * 1.3, 0.0, 0.0), 66, key, h, bag=bag)


def scene_solo():
    """one character close up for review: three-quarter idle, front idle and running, against the cast backdrop"""
    cast_backdrop()
    m = os.environ.get('SOLO', 'PrimaryBoy'); bag = os.environ.get('SOLO_BAG') or None
    h = float(os.environ.get('SOLO_H', '1.3'))
    person(m, (-1.15, 0.0, 0.0), 30, 'idle', h, bag=bag)
    person(m, (0.15, 0.0, 0.0), 0, 'idle', h, bag=bag)
    person(m, (1.45, 0.0, 0.0), 66, os.environ.get('SOLO_POSE', 'run_stride'), h, bag=bag)


SCENES = dict(gait=scene_gait, kids=scene_kids, teens=scene_teens, solo=scene_solo, home=scene_home, market=scene_market, beach=scene_beach, site=scene_site, park=scene_park,
              california=scene_california, cast_a=scene_cast_a, cast_b=scene_cast_b, menu=scene_menu)
SCENES[SCENE]()

# ---- the camera: the game's (34 degree lens, about 9.5 m back, under 3 m up, a touch down) ----
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
cam.data.sensor_fit = 'VERTICAL'
cam.data.clip_start = 0.3; cam.data.clip_end = FAR
if SCENE.startswith('cast') or SCENE in ('solo', 'kids', 'teens', 'gait'):
    cam.data.angle_y = math.radians(float(os.environ.get('CAM_FOV', '20')))
    cam.location = (float(os.environ.get('CAM_X', '0.15')), -8.6, float(os.environ.get('CAM_Z', '1.25')))
    target = Vector((float(os.environ.get('CAM_X', '0.15')), 0.0, float(os.environ.get('CAM_TZ', '1.05'))))
else:
    cam.data.angle_y = math.radians(CAM['fov'])
    cam.location = (CAM['x'], -CAM['back'], CAM['up'])
    target = Vector((CAM['x'], 0.0, CAM['look']))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

# ---- the sun: cast shadows only (the toon materials read a white diffuse back) ----
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); S.collection.objects.link(sun)
sun.data.energy = math.pi; sun.data.angle = math.radians(1.5)
sun.rotation_euler = (-SUNDIR).to_track_quat('-Z', 'Y').to_euler()
S.world = bpy.data.worlds.new('w'); S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)

S.render.engine = 'BLENDER_EEVEE'
S.render.resolution_x, S.render.resolution_y = RW, RH
S.render.image_settings.file_format = 'PNG'
S.render.dither_intensity = 0.0
try:
    S.eevee.taa_render_samples = 8
    S.eevee.use_shadows = True
    S.eevee.shadow_resolution_scale = 1.0
except Exception:
    pass


def render(path, kind):
    set_pass(kind)
    S.view_settings.view_transform = 'Standard' if kind == 'colour' else 'Raw'
    S.render.film_transparent = kind == 'colour'
    S.render.image_settings.color_mode = 'RGBA' if kind == 'colour' else 'RGB'
    bg = S.world.node_tree.nodes['Background'].inputs['Color']
    bg.default_value = {'colour': (0, 0, 0, 1), 'normal': (0.5, 0.5, 1.0, 1), 'data': (1.0, 0.0, 1.0, 1)}[kind]
    S.render.filter_size = 1.5 if kind != 'data' else 0.01
    S.eevee.taa_render_samples = 8 if kind != 'data' else 1
    S.render.filepath = path
    bpy.ops.render.render(write_still=True)


for kind in (('data',) if '--data-only' in argv else ('colour', 'normal', 'data')):
    render(os.path.join(OUT, '%s_%s.png' % (SCENE, kind)), kind)
print('rendered', SCENE)
