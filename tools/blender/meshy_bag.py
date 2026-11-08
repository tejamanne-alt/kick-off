# The Locker Room's bags: a backpack the user supplied (an AI-generated model: one fused, textured mesh, its shoulder
# straps hanging in a "D" as if worn) made ready for the game and fitted to a kid, as a second skinned mesh in the kid's
# own FBX ('Bag_<Id>', beside 'Kid', under 'KidRig'), so any bag can be worn by any kid who has no bag of their own.
#
#   prep  blenv/bin/python meshy_bag.py -- prep /abs/bag.fbx /abs/outdir --id KickOff [--tris 30000] [--size 1024]
#           -> outdir/Bag<Id>.blend (the bag facing the wearer on -y, its back panel's top middle at the origin, its body
#              one unit tall), outdir/Bag<Id>Atlas.png, outdir/Bag<Id>.json
#   icon  blenv/bin/python meshy_bag.py -- icon /abs/Bag<Id>.blend /abs/bag_<id>.png [--size 256]
#           -> the bag's Locker Room picture in the game's toon look (two cel bands, an ink outline) on a clear ground
#   fit   blenv/bin/python meshy_bag.py -- fit /abs/Kid.blend /abs/Bag<Id>.blend /abs/outdir
#           -> the kid's .blend and .fbx again in outdir, with the bag on: its body on the Bag bone, its straps over the
#              shoulders and down the chest on the Chest bone.
#
# The atlas is the bag's own texture with the bag's cloth marked in its alpha (0 where the cloth's colour is, 1 for the
# zips, the logo, the black mesh pockets): the game's character shader recolours the marked texels to the colour the
# player picks in Settings (ToonCharacter's _MaskTint), keeping their light and shade, and leaves the rest as made.
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:]
sys.argv = sys.argv[:sys.argv.index('--') + 1] + ['/dev/null', '/tmp']     # (meshy_boy reads two leading arguments)
import meshy_boy as mb
from meshy_boy import activate, verts_np, edges_np, texture_pixels, hsv, decimate, weights, export_fbx, components

C = bpy.context
mb.log = lambda *a: print('[meshy_bag]', *a, flush=True)
log = mb.log

# The cloth's colour, for the recolouring mask: purple hues, saturated enough (the navy zips and the black mesh are
# not cloth; nor the white or the orange of the logo).
CLOTH_HUE = (255.0, 320.0)
CLOTH_SAT = 0.3


def cloth_mask(rgb):
    """0..1: how much a texel (sRGB, 0..1) is the bag's cloth, softened at the edges of the hue band."""
    shape = rgb.shape[:-1]
    h, s, v = (x.reshape(shape) for x in hsv(rgb.reshape(-1, 3)))
    lo, hi = CLOTH_HUE
    hw = np.clip(np.minimum(h - lo, hi - h) / 12.0 + 0.5, 0, 1)
    sw = np.clip((s - CLOTH_SAT) / 0.12 + 0.5, 0, 1)
    vw = np.clip((v - 0.06) / 0.05, 0, 1)
    return hw * sw * vw


# ------------------------------------------------------------------------------------------------ prep
def prep(src, out, bag_id, tris, size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    o = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    for x in [x for x in bpy.data.objects if x is not o]: bpy.data.objects.remove(x)
    activate(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    img = [n.image for n in o.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and
           any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links)][0]
    px = texture_pixels(img)
    decimate(o, tris)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(o.data); bm.free(); o.data.update()

    # Which side the straps are on: the side that reaches furthest from the middle column (the straps' "D" stands
    # further off the back panel than the front pocket does from the front).
    V = verts_np(o)
    mid = (V[:, 2] > np.percentile(V[:, 2], 40)) & (V[:, 2] < np.percentile(V[:, 2], 75))
    centre = mid & (np.abs(V[:, 0]) < 0.1 * np.ptp(V[:, 0]))
    ys = V[mid, 1]; reach_plus = ys.max() - np.median(V[centre, 1]); reach_minus = np.median(V[centre, 1]) - ys.min()
    plus = reach_plus > reach_minus
    if plus:                                                    # the straps toward -y: the wearer's side
        o.data.transform(Matrix.Rotation(math.pi, 4, 'Z')); o.data.update()
    V = verts_np(o)
    # the back panel: the wearer's side of the middle column (no straps there), at the body's middle heights
    zlo, zhi = V[:, 2].min(), V[:, 2].max()
    band = (V[:, 2] > zlo + 0.45 * (zhi - zlo)) & (V[:, 2] < zlo + 0.75 * (zhi - zlo)) & (np.abs(V[:, 0]) < 0.08 * np.ptp(V[:, 0]))
    yb = np.percentile(V[band, 1], 1)
    # the body's top: the highest point of the back panel's middle (the carry handle above it is left out)
    panel = (np.abs(V[:, 1] - yb) < 0.06 * np.ptp(V[:, 1])) & (np.abs(V[:, 0]) < 0.08 * np.ptp(V[:, 0]))
    top = np.percentile(V[panel, 2], 99.5)
    body_h = top - zlo
    k = 1.0 / body_h
    o.data.transform(Matrix.Diagonal((k, k, k, 1)) @ Matrix.Translation((0, -yb, -top))); o.data.update()
    V = verts_np(o)
    strap = V[:, 1] < -0.02
    width = np.ptp(V[(V[:, 2] > -0.6) & (V[:, 2] < -0.3) & ~strap, 0])
    log('prep: straps were on %s y; back panel y %.3f, body %.3f tall, %d of %d vertices in the straps, body %.3f wide' % (
        '+' if plus else '-', yb, body_h, strap.sum(), len(V), width))

    # the atlas: the texture at the asked size, the cloth marked in the alpha (0: recolourable)
    from PIL import Image
    H, W = px.shape[:2]
    rgb = np.clip(px[::-1, :, :3], 0, 1)                         # (Blender's rows are bottom up)
    m = cloth_mask(rgb)
    a = 1.0 - m
    # (the colour and the mask resized apart: PIL would premultiply the colour by the mask)
    im_rgb = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), 'RGB')
    im_a = Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'L')
    if size != W: im_rgb, im_a = im_rgb.resize((size, size), Image.LANCZOS), im_a.resize((size, size), Image.LANCZOS)
    im = im_rgb.copy(); im.putalpha(im_a)
    png = os.path.join(out, 'Bag%sAtlas.png' % bag_id); im.save(png)
    cloth = rgb[m > 0.9]
    lum = float(np.median(cloth @ np.array([0.299, 0.587, 0.114])))
    base = np.median(cloth, 0)
    log('prep: cloth %.1f%% of the texture, its colour sRGB %s, luminance %.3f' % (100 * (m > 0.5).mean(), np.round(base, 3), lum))

    me = o.data
    me.materials.clear(); me.materials.append(mb.atlas_material('Bag' + bag_id, png))
    for n in me.materials[0].node_tree.nodes:
        if n.type == 'TEX_IMAGE': n.image.alpha_mode = 'CHANNEL_PACKED'   # (the alpha is the cloth mask)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); col.data.foreach_set('color', np.ones(len(me.loops) * 4))
    o.name = me.name = 'Bag_' + bag_id
    o['width'] = float(width)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'Bag%s.blend' % bag_id))
    with open(os.path.join(out, 'Bag%s.json' % bag_id), 'w') as f:
        json.dump({'id': bag_id, 'cloth': [round(float(c), 4) for c in base], 'luminance': round(lum, 4),
                   'tris': sum(len(p.vertices) - 2 for p in me.polygons)}, f)


# ------------------------------------------------------------------------------------------------ fit
CLEAR = 0.012            # how far the straps stand off the kid's clothes (Blender units: the kid is 2.14 tall)
BAG_GAP = 0.008          # between the back and the bag's back panel
WIDTH = 0.92             # the bag's body this much of the kid's back's width
HEIGHT = 1.0             # the bag's body this much of the way from the Bag marker down to the hip joints


def fit(kid_blend, bag_blend, out):
    bpy.ops.wm.open_mainfile(filepath=kid_blend)
    kid = bpy.data.objects['Kid']; rig = bpy.data.objects['KidRig']
    with bpy.data.libraries.load(bag_blend) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith('Bag_')]
    bag = dst.objects[0]; C.scene.collection.objects.link(bag)
    name = bag.name
    for x in [x for x in bpy.data.objects if x.name.startswith('Bag_') and x is not bag]: bpy.data.objects.remove(x)
    bag.name = name

    B = rig.data.bones
    mark = np.array(B['Bag'].head_local); hips = np.array(B['UpperLeg.L'].head_local)
    K = verts_np(kid); W, names = weights(kid)
    arms = sum(W[:, names.index(n)] for n in names if 'Arm' in n or 'Hand' in n)
    head = sum(W[:, names.index(n)] for n in ('Head', 'Neck') if n in names)
    torso = (arms < 0.3) & (head < 0.3)
    # the back's width at the marker, the arms left out
    sl = torso & (np.abs(K[:, 2] - mark[2]) < 0.02)
    back_w = np.ptp(K[sl, 0])
    s_w = WIDTH * back_w / bag['width']
    s_h = HEIGHT * (mark[2] - hips[2])
    s = min(s_w, s_h)
    bag.data.transform(Matrix.Diagonal((s, s, s, 1))); bag.data.update()
    V = verts_np(bag)
    strap = V[:, 1] < -0.02 * s
    # behind the back wherever the bag's body reaches it
    zr = (K[:, 2] < mark[2] + 0.02) & (K[:, 2] > mark[2] - s) & (np.abs(K[:, 0] - mark[0]) < 0.5 * bag['width'] * s) & torso
    yback = K[zr, 1].max() + BAG_GAP
    bag.data.transform(Matrix.Translation((mark[0], yback, mark[2]))); bag.data.update()
    log('fit: back %.3f wide, scale %.3f (width %.3f, height %.3f), panel at y %.3f' % (back_w, s, s_w, s_h, yback))

    # The straps: the "D" made as deep as the kid's chest (front to back at each height, where the strap is), their
    # top run raised over the shoulder, their lower front run drawn out to the side (under the arm), then anything
    # still inside the kid pushed out and smoothed.
    V = verts_np(bag); E = edges_np(bag)
    d = yback - V[:, 1]                                          # depth in front of the back panel
    dmax = d[strap].max()
    ztop = mark[2]
    chest_front = {}
    for side in (-1, 1):
        xs = V[strap & (np.sign(V[:, 0] - mark[0]) == side), 0]
        xc = np.median(xs)
        m = torso & (np.abs(K[:, 0] - xc) < 0.03) & (K[:, 2] < ztop + 0.05) & (K[:, 2] > ztop - 0.75 * s)
        front = K[m, 1].min()
        shoulder = K[torso & (np.abs(K[:, 0] - xc) < 0.03) & (K[:, 1] > front) & (K[:, 1] < yback)][:, 2].max()
        edge = np.percentile(np.abs(K[torso & (np.abs(K[:, 2] - (ztop - 0.45 * s)) < 0.03), 0] - mark[0]), 97)
        chest_front[side] = (xc, front, shoulder, edge)
        log('fit: %s strap at x %.3f: the chest\'s front at y %.3f, the shoulder\'s top at z %.3f, the side at |x| %.3f' % (
            'left' if side > 0 else 'right', xc, front, shoulder, edge))
    P = V.copy()
    for side in (-1, 1):
        xc, front, shoulder, edge = chest_front[side]
        m = strap & (np.sign(V[:, 0] - mark[0]) == side)
        depth = (yback - front) + CLEAR
        f = d[m] / dmax                                          # 0 at the back panel .. 1 at the strap's front run
        P[m, 1] = yback - d[m] * depth / dmax
        # the top run over the shoulder: raised by up to how far the shoulder's top is above the bag's
        lift = max(0.0, shoulder + CLEAR - ztop)
        top_w = np.clip((V[m, 2] - (ztop - 0.25 * s)) / (0.25 * s), 0, 1)
        P[m, 2] = V[m, 2] + lift * top_w * np.clip(f * 1.5, 0, 1)
        # the lower front run out to the side, so it goes back under the arm
        low = np.clip(((ztop - 0.3 * s) - V[m, 2]) / (0.4 * s), 0, 1)
        target = mark[0] + side * (edge + CLEAR)
        P[m, 0] = V[m, 0] + (target - V[m, 0]) * low * f * 0.6
    disp = P - V
    deg = np.zeros(len(V)); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    for _ in range(6):                                           # (a smooth bend, not kinks at the band edges)
        acc = np.zeros_like(disp); np.add.at(acc, E[:, 0], disp[E[:, 1]]); np.add.at(acc, E[:, 1], disp[E[:, 0]])
        sm = 0.5 * disp + 0.5 * acc / np.maximum(deg, 1)[:, None]
        disp[strap] = sm[strap]
    P = V + disp
    # out of the kid: a strap vertex under the clothes goes to the surface, CLEAR out along its normal
    bm = bmesh.new(); bm.from_mesh(kid.data); tree = BVHTree.FromBMesh(bm)
    pushed = 0
    for it in range(3):
        moved = np.zeros_like(P)
        for i in np.where(strap)[0]:
            hit, n, _, dist = tree.find_nearest(Vector(P[i]))
            if hit is None: continue
            if (Vector(P[i]) - hit).dot(n) < CLEAR:
                moved[i] = np.array(hit + n * CLEAR) - P[i]; pushed += 1
        for _ in range(2):
            acc = np.zeros_like(moved); np.add.at(acc, E[:, 0], moved[E[:, 1]]); np.add.at(acc, E[:, 1], moved[E[:, 0]])
            moved = np.where(np.abs(moved).sum(1, keepdims=True) > 0, moved, acc / np.maximum(deg, 1)[:, None]) * strap[:, None]
        P = P + moved
    bm.free()
    bag.data.vertices.foreach_set('co', P.ravel()); bag.data.update()
    log('fit: %d strap vertex moves out of the clothes' % pushed)

    # skin: the body on the Bag bone; the straps on the Chest, blending into the Bag bone where they meet the body
    activate(rig); bpy.ops.object.mode_set(mode='EDIT'); rig.data.edit_bones['Bag'].use_deform = True
    bpy.ops.object.mode_set(mode='OBJECT')
    on_chest = np.clip((d / dmax - 0.15) / 0.35, 0, 1) * strap
    for g in list(bag.vertex_groups): bag.vertex_groups.remove(g)
    gb = bag.vertex_groups.new(name='Bag'); gc = bag.vertex_groups.new(name='Chest')
    for i, w in enumerate(on_chest):
        if w < 1: gb.add([i], float(1 - w), 'REPLACE')
        if w > 0: gc.add([i], float(w), 'REPLACE')
    bag.parent = rig; bag.matrix_parent_inverse = Matrix()
    for mo in list(bag.modifiers): bag.modifiers.remove(mo)
    mo = bag.modifiers.new('Armature', 'ARMATURE'); mo.object = rig
    # the kid's own deform bones are unchanged: the Bag bone deforms nothing of the kid's
    name = os.path.splitext(os.path.basename(kid_blend))[0]
    bags = [x for x in bpy.data.objects if x.name.startswith('Bag_')]
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, name + '.blend'))
    export_fbx([kid, rig] + bags, os.path.join(out, name + '.fbx'))
    log('fit: %s exported with %s' % (name, ', '.join(b.name for b in bags)))


# ------------------------------------------------------------------------------------------------ icon
def icon(bag_blend, png, size):
    bpy.ops.wm.open_mainfile(filepath=bag_blend)
    bag = [x for x in bpy.data.objects if x.name.startswith('Bag_')][0]
    for x in [x for x in bpy.data.objects if x is not bag]: bpy.data.objects.remove(x)
    S = C.scene
    mat = bag.data.materials[0]; nt = mat.node_tree
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]; tex.image.alpha_mode = 'CHANNEL_PACKED'
    mix = [n for n in nt.nodes if n.type == 'MIX'][0]
    geo = nt.nodes.new('ShaderNodeNewGeometry'); L = nt.nodes.new('ShaderNodeCombineXYZ')
    sun = Vector((-0.35, 0.6, 0.75)).normalized(); L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = sun
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
    lit = nt.nodes.new('ShaderNodeMapRange'); lit.interpolation_type = 'SMOOTHSTEP'
    lit.inputs['From Min'].default_value = -0.02; lit.inputs['From Max'].default_value = 0.06
    nt.links.new(dot.outputs['Value'], lit.inputs['Value'])
    band = nt.nodes.new('ShaderNodeMix'); band.data_type = 'RGBA'
    band.inputs['A'].default_value = (0.62, 0.64, 0.8, 1); band.inputs['B'].default_value = (1.0, 0.98, 0.95, 1)
    nt.links.new(lit.outputs['Result'], band.inputs['Factor'])
    m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'; m2.inputs['Factor'].default_value = 1
    nt.links.new(mix.outputs['Result'], m2.inputs['A']); nt.links.new(band.outputs['Result'], m2.inputs['B'])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(m2.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    mat.use_backface_culling = True
    ol = bpy.data.materials.new('Outline'); ol.use_nodes = True; ol.use_backface_culling = True
    e = ol.node_tree.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0.012, 0.009, 0.014, 1)
    ol.node_tree.links.new(e.outputs[0], ol.node_tree.nodes['Material Output'].inputs['Surface'])
    bag.data.materials.append(ol)
    sol = bag.modifiers.new('outline', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1; sol.use_flip_normals = True; sol.material_offset = 1
    # a three-quarter view of its front (the pocket's side, +y) from a little above
    V = verts_np(bag); c = (V.min(0) + V.max(0)) / 2; ext = np.ptp(V, 0)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); S.collection.objects.link(cam); S.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(ext) * 1.16
    d = Vector((0.55, 1.0, 0.35)).normalized()
    cam.location = Vector(c) + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    S.render.engine = 'BLENDER_EEVEE'; S.view_settings.view_transform = 'Standard'; S.render.film_transparent = True
    S.render.resolution_x = S.render.resolution_y = size; S.render.image_settings.file_format = 'PNG'
    S.render.image_settings.color_mode = 'RGBA'; S.render.filepath = png
    S.world = bpy.data.worlds.new('w')
    bpy.ops.render.render(write_still=True)
    log('icon: %s' % png)


if __name__ == '__main__':
    os.makedirs(argv[-1] if argv[0] == 'fit' else (os.path.dirname(argv[2]) if argv[0] == 'icon' else argv[2]), exist_ok=True)
    if argv[0] == 'prep':
        bag_id = argv[argv.index('--id') + 1]
        tris = int(argv[argv.index('--tris') + 1]) if '--tris' in argv else 30000
        size = int(argv[argv.index('--size') + 1]) if '--size' in argv else 1024
        prep(argv[1], argv[2], bag_id, tris, size)
    elif argv[0] == 'icon':
        icon(argv[1], argv[2], int(argv[argv.index('--size') + 1]) if '--size' in argv else 256)
    elif argv[0] == 'fit':
        fit(argv[1], argv[2], argv[3])
