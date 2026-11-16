# What every Kamakura leg's set-piece builder shares (km_komachi.py for KM1-3, km_shrine_school.py for KM1-4): the
# leg's own texture (4096 x 2048), the paint-out helpers, upright cut-outs, the sky's test, and the export, install and
# strict review (docs/ASSET_REVIEW.md) of a leg's models. The builder sets sys.argv for the kit module
# (kit_buildings_km.py reads its own arguments) before importing this.
import json
import os
import shutil

import bpy
import cv2
import numpy as np
from mathutils import Vector
from PIL import Image

import asset_review as AR
import kit_buildings_km as KB
import kit_lib as K


class Atlas(KB.Atlas):
    """The kit's atlas, w wide and h tall (a leg's: 4096 x 2048)."""
    def __init__(self, w, h):
        super().__init__(w)
        self.w, self.h = w, h
        self.img = Image.new('RGBA', (w, h), (255, 255, 255, 255))

    def place(self, im):
        if self.x + im.width + 8 > self.w:
            self.x, self.y, self.row = 8, self.y + self.row + 16, 8
        if self.y + im.height + 8 > self.h:
            raise SystemExit('km_leg_kit: the atlas is full')
        pos = (self.x, self.y)
        im = im.convert('RGBA')
        pad = im.resize((im.width + 16, im.height + 16), Image.NEAREST)
        self.img.paste(pad, (self.x - 8, self.y - 8))
        self.img.paste(im, pos)
        self.x += im.width + 16
        self.row = max(self.row, im.height)
        return pos

    def uv(self, pos, px, py):
        return ((pos[0] + px) / self.w, 1.0 - (pos[1] + py) / self.h)


# ---------------------------------------------------------------- painting out what becomes its own model
def copy_patch(a, box, dx=0, dy=0):
    """Fills box with the pixels dx, dy away (the same wall's boards beside it, the paving's rows beside it)."""
    x0, y0, x1, y1 = box
    a[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]


def inpaint(a, mask, r=4):
    return cv2.inpaint(a, mask.astype(np.uint8), r, cv2.INPAINT_TELEA)


def colour_sample(img, box, size=(64, 64)):
    """A plain sample of a part's own colour (a post's red, a cap's black), its box shrunk to size."""
    return img.crop(box).convert('RGB').resize(size, Image.BILINEAR)


def flat_sample(img, box, size=(64, 64)):
    """A plain sample of one colour: the median of box (a pond's water, a sports ground's sand, where a stretched patch
    would carry a line or a stone across the whole face)."""
    a = np.asarray(img.crop(box).convert('RGB')).reshape(-1, 3)
    return Image.new('RGB', size, tuple(int(v) for v in np.median(a, 0)))


def sky_mask(a):
    """The pale summer sky of the photographic pictures (as unsky's pale test), and its soft fringe."""
    a = a.astype(np.int32)
    sky = (a[..., 2] - a[..., 0] > 18) & (a[..., 2] - a[..., 1] > 4) & (a[..., 2] > 170)
    return cv2.dilate(sky.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


def overcast_mask(a, below=None):
    """An overcast sky (KM1-4's: pale grey, a little blue), bright and with almost no colour of its own; only above the
    row `below`, where nothing else is that bright and grey."""
    f = a.astype(np.int32)
    m = (f.min(-1) > 195) & (f.max(-1) - f.min(-1) < 26)
    if below is not None:
        m[below:] = False
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


# ---------------------------------------------------------------- cut-outs
def card_faces(b, atlas, pos, crop, cx, gy, s, y, both=True):
    """Adds to builder b an upright cut-out at depth y, its image placed at pos: the picture exactly from the street,
    mirrored from behind."""
    x0, y0, x1, y1 = crop
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    for back in ((False, True) if both else (False,)):
        pts = [(X(x0), Z(y1)), (X(x1), Z(y1)), (X(x1), Z(y0)), (X(x0), Z(y0))]
        if back:
            pts = pts[::-1]
        f = b.bm.faces.new([b.bm.verts.new(Vector((px, y + (0.002 if back else 0.0), pz))) for px, pz in pts])
        for loop in f.loops:
            c = loop.vert.co
            loop[b.uv].uv = atlas.uv(pos, cx + c.x * s - x0, gy - c.z * s - y0)


def card(atlas, rgba, crop, cx, gy, s, y, name, both=True):
    """A cut-out standing upright at depth y: the picture exactly from the street, mirrored from behind."""
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    b = KB.Builder(atlas, None, None, None, None)
    card_faces(b, atlas, pos, crop, cx, gy, s, y, both)
    return b.object(name, outward=False)


def cutout_model(atlas, src, mask, box, name, info, s, both=True):
    """A thing cut out of the picture by its mask, standing upright at its middle, its foot at the box's bottom."""
    x0, y0, x1, y1 = box
    a = np.asarray(src.convert('RGB'))[y0:y1, x0:x1]
    m = mask[y0:y1, x0:x1]
    o = card(atlas, np.dstack([a, m * 255]), box, (x0 + x1) / 2, float(y1), s, 0.0, name, both)
    info.setdefault('real_size', [round((x1 - x0) / s, 2), 0.01, round((y1 - y0) / s, 2)])
    return o, info


# ---------------------------------------------------------------- export, install, review
def shell_counts(o):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    open_edges = sum(1 for e in bm.edges if e.is_boundary)
    fins = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bm.free()
    return open_edges, fins


def export(models, atlas, out, review_dir, atlas_name, manifest_name, src, boxes, checks, install=None):
    """Each model to <out>/<Model>.fbx (its Attach.Front for the game), the shared texture <out>/<atlas_name>, their
    manifest entries in <out>/<manifest_name>.json and the scene in <out>/<manifest_name>.blend; the strict review into
    review_dir; with install, the models, the texture and their entries into the game's Kamakura folder."""
    atlas_path = os.path.join(out, atlas_name)
    atlas.img.save(atlas_path)
    manifest = K.Manifest('Kamakura', None)
    review_mats = {False: KB.unlit(atlas_path), True: KB.unlit(atlas_path, cut=True)}
    game_mats = {}
    stem = os.path.splitext(atlas_name)[0]
    for o, info in models:
        o.location = (0, 0, 0)
        cut = bool(info.get('cutout'))
        if cut not in game_mats:
            game_mats[cut] = K.material(stem + ('Cut' if cut else ''), atlas_path)
        K.assign(o, game_mats[cut])
        front = K.attach(o, 'Front', (0, -1, 0))
        K.export_model(o, os.path.join(out, o.name + '.fbx'))
        manifest.add(o, texture=atlas_name, tex_px=atlas.w, **info)
        bpy.data.objects.remove(front)
        print('%-18s %5d triangles' % (o.name, K.tree_tris(o)))
    manifest.save(os.path.join(out, manifest_name + '.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, manifest_name + '.blend'))
    review(models, review_mats, src, review_dir, boxes, checks)
    if install:
        installed_path = os.path.join(install, 'Kamakura.json')
        installed = json.load(open(installed_path))
        for o, info in models:
            shutil.copy(os.path.join(out, o.name + '.fbx'), install)
            installed['models'][o.name] = manifest.data['models'][o.name]
        shutil.copy(atlas_path, install)
        json.dump(installed, open(installed_path, 'w'), indent=1, ensure_ascii=False)
        print('installed', len(models), 'models in', install)


def review(models, mats, src, review_dir, boxes, checks):
    """The strict review (docs/ASSET_REVIEW.md): each model's eight views, its part of the picture, its seventeen checks
    (checks(o, info, open_edges, fins, tris) gives them, as {number: (result, words)})."""
    os.makedirs(os.path.join(review_dir, 'views'), exist_ok=True)
    os.makedirs(os.path.join(review_dir, 'source'), exist_ok=True)
    out = {}
    names = KB.AR_CHECK_NAMES
    for o, info in models:
        K.assign(o, mats[bool(info.get('cutout'))])
        AR.eight_views(o, os.path.join(review_dir, 'views', o.name + '.jpg'), KB.render, cell_px=360,
                       title='%s: every side (Right is the street side, as the game sees it)' % o.name)
        src.crop(boxes[o.name]).save(os.path.join(review_dir, 'source', o.name + '.jpg'), quality=88)
        oe, fins = shell_counts(o)
        tris = K.tree_tris(o)
        c = checks(o, info, oe, fins, tris)
        out[o.name] = dict(id=info['id'], sheet=info['source'], size=info['real_size'], tris=tris, motions=[],
                           checks=[[i, names[i - 1], c[i][0], c[i][1]] for i in range(1, 18)])
    json.dump(out, open(os.path.join(review_dir, 'review.json'), 'w'), indent=1, ensure_ascii=False)
