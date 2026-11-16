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


def patch_fill(a, hole, patch=11, window=140, avoid=None):
    """Fills hole by exemplar painting: from the hole's edge inward, each time the edge patch with the most known pixels
    and the strongest line running into the hole takes the patch nearby (within window px) whose known pixels match it
    best, and its missing pixels from it. Trees,
    sky and boards behind a thing taken out stay trees, sky and boards, not a smear (TELEA) or a copied strip (D38).
    avoid: pixels no source patch may touch (besides the hole)."""
    hole = hole.astype(bool)
    if not hole.any():
        return a.copy()
    out = a.copy()
    H, W = hole.shape
    ys, xs = np.nonzero(hole)
    m = window + patch
    Y0, Y1, X0, X1 = max(ys.min() - m, 0), min(ys.max() + m + 1, H), max(xs.min() - m, 0), min(xs.max() + m + 1, W)
    sub = out[Y0:Y1, X0:X1].astype(np.float32)
    hl = hole[Y0:Y1, X0:X1].copy()
    bad = hl.copy() if avoid is None else (hl | avoid[Y0:Y1, X0:X1].astype(bool))
    h = patch // 2
    k3 = np.ones((3, 3), np.uint8)
    sh, sw = hl.shape
    while hl.any():
        known = ~hl
        edge = hl & (cv2.dilate(known.astype(np.uint8), k3) > 0)
        ey, ex = np.nonzero(edge)
        conf = cv2.boxFilter(known.astype(np.float32), -1, (patch, patch), borderType=cv2.BORDER_REPLICATE)
        # first where a line (a tree line against the sky, a roof's edge) runs into the hole (Criminisi's data term),
        # so it is carried on across it before what lies either side of it grows in
        g = sub.mean(-1)
        gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        near = cv2.dilate(hl.astype(np.uint8), k3) > 0
        gx[near], gy[near] = 0, 0
        gx, gy = cv2.boxFilter(gx, -1, (patch, patch)), cv2.boxFilter(gy, -1, (patch, patch))
        hm = cv2.GaussianBlur(hl.astype(np.float32), (5, 5), 0)
        nx, ny = cv2.Sobel(hm, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(hm, cv2.CV_32F, 0, 1, ksize=3)
        nn = np.sqrt(nx[ey, ex] ** 2 + ny[ey, ex] ** 2) + 1e-6
        data = np.abs(-gy[ey, ex] * nx[ey, ex] + gx[ey, ex] * ny[ey, ex]) / nn / 255.0 + 0.001
        i = int(np.argmax(conf[ey, ex] * data))
        y, x = ey[i], ex[i]
        y0, y1, x0, x1 = max(y - h, 0), min(y + h + 1, sh), max(x - h, 0), min(x + h + 1, sw)
        tpl = sub[y0:y1, x0:x1]
        tm = known[y0:y1, x0:x1].astype(np.float32)
        sy0, sy1 = max(y0 - window, 0), min(y1 + window, sh)
        sx0, sx1 = max(x0 - window, 0), min(x1 + window, sw)
        res = cv2.matchTemplate(sub[sy0:sy1, sx0:sx1], tpl, cv2.TM_SQDIFF, mask=np.dstack([tm] * 3))
        nb = cv2.boxFilter(bad[sy0:sy1, sx0:sx1].astype(np.float32), -1, (x1 - x0, y1 - y0), anchor=(0, 0),
                           normalize=False, borderType=cv2.BORDER_CONSTANT)[:res.shape[0], :res.shape[1]]
        res[nb > 0] = np.inf
        ry, rx = np.unravel_index(int(np.argmin(res)), res.shape)
        src = sub[sy0 + ry:sy0 + ry + (y1 - y0), sx0 + rx:sx0 + rx + (x1 - x0)]
        fill = hl[y0:y1, x0:x1].copy()
        sub[y0:y1, x0:x1][fill] = src[fill]
        hl[y0:y1, x0:x1][fill] = False
    out[Y0:Y1, X0:X1] = np.clip(sub, 0, 255).astype(out.dtype)
    return out


def trim_edges(mask, a, band=14, dist=30, ring=8):
    """A measured outline trimmed of the ground caught along its edge: in the band px inside the outline, the pixels
    within dist (RGB) of the ground just outside it (the median of a ring px wide round it) are let go."""
    m = mask.astype(np.uint8)
    out_ring = (cv2.dilate(m, np.ones((2 * ring + 1, 2 * ring + 1), np.uint8)) > 0) & ~m.astype(bool)
    ground = np.median(a[out_ring][:, :3].astype(np.float32), 0)
    edge = m.astype(bool) & ~(cv2.erode(m, np.ones((2 * band + 1, 2 * band + 1), np.uint8)) > 0)
    near = np.linalg.norm(a[..., :3].astype(np.float32) - ground, axis=-1) < dist
    m[edge & near] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    return np.isin(lab, [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= 40]).astype(np.uint8)


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
        f[b.part] = -1                     # kept as built: the front toward the street, the back away from it (D37)
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
