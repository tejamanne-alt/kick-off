# The BARRIERS kit for Dribble To School: real things a kid ducks under on the way to school,
# modelled by script in Blender (read docs/ART_DIRECTION.md first). Each spans the footpath with a
# clear 0.85 m gap over the kid's line for the game's slide (TrackBuilder.SlideUnder):
#   blenv/bin/python kit_barriers.py -- /abs/outdir [--only PlankTrestles,SurfRack]
# Writes into outdir: <Model>.fbx per model, BarriersAtlas.png, Barriers.json, Barriers.blend.
# Review: blenv/bin/python review_kit.py -- /abs/outdir/Barriers.blend /abs/outdir/sheet.png [--models A,B]
#
# Built with the WORKS kit's machinery (kit_works_geo.py: pieces, primitives, the atlas layout,
# baked soft shading; kit_works_atlas.py: grime maps and shared tiles), with this kit's own extra
# materials and tiles (bark, sawn log ends, shutter slats, debris netting) and its own atlas and
# manifest, so it stands alone in Art/Models/Barriers/. The models are in kit_barriers_models.py.
#
# The manifest's extras tell the game the solid to build a collider for: slideHalf / slideTop (a box
# from the gap up, centred on the origin along x) or slideRadius / slideCentre (a round one), and for
# the market stall its awning (canopyHalf, canopyBottom, canopyTop).
#
# The propped boughs' foliage is leaf-clump cards like the Plants kit's trees (kit_plants_leaves.py):
# their sprites are painted into atlas rows the packer leaves free, in the atlas's alpha channel (alpha
# is 1 everywhere else), and the game's Barriers material cuts them out (Toon.shader _ALPHATEST_ON).
# The cards are built once the atlas is laid out and joined into their model; they take no part in
# the slide solid.
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import bpy
import kit_lib as K
import kit_works_geo as G
import kit_works_atlas as ATL
import kit_plants_geo as PG
import kit_plants_atlas as PAT
import kit_plants_leaves as LV
from kit_barriers_models import BARRIER_MODELS

LEAF_CELLS = 4          # clover-clump sprites, 128 px each
LEAF_PX = 128

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(ARGS[0]) if ARGS else '/tmp/barriers'
ONLY = ARGS[ARGS.index('--only') + 1].split(',') if '--only' in ARGS else None


def leaf_cells(used, pad=8):
    """Place the leaf sprites' cells in the rows below what the packer used."""
    y0 = used + pad
    if y0 + LEAF_PX > G.AT - 64 - pad:
        raise RuntimeError('atlas full: no room for the leaf sprites')
    for k in range(LEAF_CELLS):
        x0 = pad + k * (LEAF_PX + 2 * pad)
        G.REG['leafspr.%d' % k] = (x0 / G.AT, (G.AT - (y0 + LEAF_PX)) / G.AT, (x0 + LEAF_PX) / G.AT, (G.AT - y0) / G.AT)


def leaf_uv(sprite, k, s, t, inset=2.0):
    u0, v0, u1, v1 = G.REG['leafspr.%d' % (k % LEAF_CELLS)]
    f = inset / LEAF_PX
    s = f + np.asarray(s) * (1 - 2 * f); t = f + np.asarray(t) * (1 - 2 * f)
    return np.stack([u0 + s * (u1 - u0), v0 + t * (v1 - v0)], axis=-1)


def paint_leaf_sprites(path):
    """Add the leaf sprites (grey value and alpha) to the painted atlas; alpha 1 everywhere else."""
    img = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255
    alpha = np.ones(img.shape[:2], np.float32)
    rng = np.random.default_rng(7)
    for k in range(LEAF_CELLS):
        x0, y0, x1, y1 = G.reg_px('leafspr.%d' % k)
        v, a = PAT.paint_sprite(rng, 'leaf', x1 - x0)
        img[y0:y1, x0:x1] = v[..., None]
        alpha[y0:y1, x0:x1] = a
    rgba = np.concatenate([img, alpha[..., None]], axis=2)
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(path)


def leaf_object(M):
    """The model's leaf cards and their dark cores as one mesh (custom normals, part 0, no sway)."""
    rng = np.random.default_rng(len(M.name) * 7 + 3)
    pieces = []
    for spec in M.leafcards:
        ms = spec['masses']
        pieces.append(LV.leaf_cards(ms, rng, spec['ramp'], 0, 'leaf', size=spec['size'], density=spec.get('density', 1.0),
                                    inner=spec.get('inner', 0.3), open_under=0.3, uvfn=leaf_uv, nsprites=LEAF_CELLS,
                                    keep_out=spec.get('keep_out')))
        if spec.get('core', 0.55):
            pieces += LV.cores(ms, rng, spec['ramp'], 0, scale=spec.get('core', 0.55), s=(0.0, 0.12))
    p = PG.merge(pieces)
    p.C[:, 3] = 1.0
    return PG.to_object(M.name + '.leaves', p)


def main():
    t0 = time.time()
    K.reset()
    os.makedirs(OUT, exist_ok=True)
    models = []
    for fn in BARRIER_MODELS:
        M = fn()
        if ONLY and M.name not in ONLY:
            for b in M.pieces: b.free()
            continue
        models.append(M)
    items = ATL.tile_items()
    for M in models:
        items += M.plan_maps()
    used = G.allocate(items)
    print('atlas rows used', used, 'of', G.AT)
    leaf_cells(used)
    atlas = os.path.join(OUT, 'BarriersAtlas.png')
    ATL.paint(atlas, models)
    paint_leaf_sprites(atlas)
    mat = LV.cutout_material(K.material('Barriers', atlas))
    man = K.Manifest('Barriers', 'BarriersAtlas.png')
    for M in models:
        ob = G.to_object(M)
        if getattr(M, 'leafcards', None):
            ob = K.join([ob, leaf_object(M)], M.name)
        K.assign(ob, mat)
        for nm, loc in M.attach:
            K.attach(ob, nm, loc)
        parts = {}
        used_parts = set()
        for p in ob.data.uv_layers['Part'].data:
            used_parts.add(int(round(p.uv[0])))
        if 1 in used_parts and M.p1: parts[1] = G.s2l(M.p1)
        if 2 in used_parts and M.p2: parts[2] = G.s2l(M.p2)
        extra = dict(M.extra)
        extra['attach'] = {nm: [round(v, 3) for v in loc] for nm, loc in M.attach}
        man.add(ob, parts=parts, **extra)
        print('%-18s tris %5d  parts %s' % (M.name, K.tree_tris(ob), sorted(used_parts)))
        names = sorted(c.name for c in ob.children)
        assert names == sorted('Attach.' + nm for nm, _ in M.attach), (M.name, names)
        K.export_model(ob, os.path.join(OUT, M.name + '.fbx'))
        for c in ob.children: c.name = M.name + ':' + c.name
    man.save(os.path.join(OUT, 'Barriers.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Barriers.blend'))
    print('done', OUT, '%.1fs' % (time.time() - t0))


main()
