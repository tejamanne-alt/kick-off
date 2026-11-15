# A Locker Room bag built from the user's own views of it (review/bags/<name>/: 1_front.png the side away from the
# wearer, 2_right_side.png, 3_back.png the straps' side; a 4_left_side.png is kept for reference, the right side
# serving for both), carved and textured by km_views.py like the Kamakura props, then exported as one textured FBX that
# meshy_bag.py's prep reads like a Meshy model (its straps' "D" standing off the back panel, as if worn).
#
#   blenv/bin/python bag_views.py -- <Id> /abs/outdir
#     -> outdir/<Id>.fbx (textured, the texture embedded), outdir/<Id>.png, outdir/<Id>_renders.jpg
#   then: meshy_bag.py -- prep /abs/outdir/<Id>.fbx /abs/bagdir --id <Id> --tris 12000 --even (its flat sides keep no
#         vertices inside them: --even measures it by points spread over its surface), then its icon and fit
#
# Carved from outlines alone, the two straps would merge with the back panel between them into one sheet (the back
# view shows the bag's body behind them, the same colour), which reads as a vest on a kid (docs/LEARNINGS.md C11): so
# behind the back panel only two bands are kept, where the back view draws the straps, their middles measured in
# metres at a few heights.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# Each bag: its views, its width (m), the back panel's depth (y, the straps' side +y), the straps' middles (|x|) at
# heights (z) and their half-width, and the height under which the rule holds (the handle above stays as carved).
BAGS = {
    'RandoseruRed': dict(folder='review/bags/randoseru_red', width=0.25, panel=0.033,
                         straps=[(0.02, 0.085), (0.15, 0.080), (0.30, 0.065)], half=0.026, top=0.30, crown=0.305),
    'RandoseruBlack': dict(folder='review/bags/randoseru_black', width=0.25, panel=0.037,
                           straps=[(0.03, 0.074), (0.17, 0.048), (0.30, 0.032)], half=0.018, top=0.30, crown=0.31),
}


def two_straps(b):
    """shape(): behind the back panel, below the handle, only the two straps' bands are left."""
    zs = np.array([z for z, _ in b['straps']], np.float32)
    cs = np.array([c for _, c in b['straps']], np.float32)

    def shape(frame):
        X = frame.xs[:, None, None]
        Y = frame.ys[None, :, None]
        Z = frame.zs[None, None, :]
        c = np.interp(Z, zs, cs).astype(np.float32)
        outside = (Y > b['panel'] + 0.002) & (Z < b['top']) & (np.abs(np.abs(X) - c) > b['half'])
        return np.where(outside, np.maximum(frame.field, 0.004), frame.field).astype(np.float32)
    return shape


def crown(b):
    """paint: the top, which no view shows (the flap's cover curving over it), the flap's own yellow from the front view,
    front to back taking it from its upper part down: not the front's one top row drawn across it (docs/LEARNINGS.md D29)."""
    return [('front', (-0.14, 0.14, -0.14, b['panel'] - 0.003, b['crown'] - 0.04, b['crown']),
             {'z': ('y', b['crown'] - 0.01, b['crown'] - 0.07)})]


def main():
    import bpy
    from PIL import Image
    import kit_lib as K
    import km_views as KV
    argv = sys.argv[sys.argv.index('--') + 1:]
    bag_id, out = argv[0], argv[1]
    os.makedirs(out, exist_ok=True)
    b = BAGS[bag_id]
    K.reset()
    root, img, fr = KV.build(bag_id, os.path.join(REPO, b['folder']), ('width', b['width']), K.new_obj,
                             vox=0.0025, budget=12000, tex=1024, shape=two_straps(b), smooth_angle=30.0, paint=crown(b))
    print('built %s W D H %.3f %.3f %.3f tris %d' % (bag_id, fr.W, fr.D, fr.H, len(root.data.polygons)), flush=True)
    tex = os.path.join(out, bag_id + '.png')
    Image.fromarray(img[..., :3]).save(tex)
    # a Principled material, the texture on its Base Color: what meshy_bag.py's prep looks for in a Meshy model
    m = bpy.data.materials.new(bag_id)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ti = nt.nodes.new('ShaderNodeTexImage')
    ti.image = bpy.data.images.load(tex)
    nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    root.data.materials.clear()
    root.data.materials.append(m)
    for o in list(bpy.context.scene.objects):
        o.select_set(o is root)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, bag_id + '.fbx'), use_selection=True, path_mode='COPY',
                             embed_textures=True, apply_unit_scale=True, bake_space_transform=False)
    # a look at it: four sides and a three-quarter, textured as baked
    import kit_buildings_km as KB
    mat = KB.unlit(tex)
    root.data.materials.clear()
    root.data.materials.append(mat)
    ims = []
    c = fr.H / 2
    H = max(fr.H, fr.W) * 1.1
    for loc, kw in [((0, -5, c), dict(ortho=H)), ((5, 0, c), dict(ortho=H)), ((0, 5, c), dict(ortho=H)),
                    ((-5, 0, c), dict(ortho=H)), ((0.45, -0.55, 0.42), dict(fov=40))]:
        ims.append(KB.render(os.path.join(out, 'tmp.png'), loc, (0, 0, c), size=(600, 700), only={root.name}, **kw))
    row = Image.new('RGB', (3000, 700))
    for i, im in enumerate(ims):
        row.paste(im, (600 * i, 0))
    row.save(os.path.join(out, bag_id + '_renders.jpg'), quality=88)
    print('wrote', os.path.join(out, bag_id + '.fbx'), flush=True)


if __name__ == '__main__':
    main()
