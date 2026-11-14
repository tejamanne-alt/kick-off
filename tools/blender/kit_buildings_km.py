# The KAMAKURA kit (docs/KAMAKURA_BUILD.md): models built by script to the measurements of the user's reference pictures
# (review/kamakura/refs), each street-facing face textured by projecting the picture's own pixels onto it, so seen from the
# street, as the game camera sees it, the model shows exactly the painting. Sides and tops take samples from the same
# pictures (the props sheet shows the props' sides). This first version builds two models, to prove the method: the kid's
# home with its fence and garden (KM1-1) and the red vending machine (KM1-1 front, KM-P1 side).
#   blenv/bin/python kit_buildings_km.py -- /abs/outdir [--board /abs/board.png]
# Writes into outdir: <Model>.fbx per model, KamakuraAtlas.png, Kamakura.json, Kamakura.blend; with --board, a review board
# of each model beside its source picture: the picture, the model straight on, the model at three-quarters.
import bpy
import bmesh
import math
import os
import sys

import cv2
import numpy as np
from mathutils import Vector
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_lib as K
import km_views as KV

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS and not ARGS[0].startswith('--') else os.path.abspath('out_km')
BOARD = ARGS[ARGS.index('--board') + 1] if '--board' in ARGS else None
PROPS_REVIEW = ARGS[ARGS.index('--props-review') + 1] if '--props-review' in ARGS else None
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
REFS = os.path.join(REPO, 'review', 'kamakura', 'refs')
ATLAS_SIZE = 4096


def ref(name):
    return Image.open(os.path.join(REFS, name)).convert('RGB')


# ---------------------------------------------------------------- the atlas: regions packed in rows
class Atlas:
    def __init__(self, size):
        self.size = size
        self.img = Image.new('RGBA', (size, size), (255, 255, 255, 255))
        self.x = self.y = self.row = 8

    def place(self, im):
        """Puts an image in the next free spot; returns its (x, y) in atlas pixels (top left)."""
        if self.x + im.width + 8 > self.size:
            self.x, self.y, self.row = 8, self.y + self.row + 16, 8
        if self.y + im.height + 8 > self.size:
            raise SystemExit('kit_buildings_km.py: the atlas is full')
        pos = (self.x, self.y)
        im = im.convert('RGBA')
        # padded by its own edge pixels, so mipmaps don't bleed white into it
        pad = im.resize((im.width + 16, im.height + 16), Image.NEAREST)
        self.img.paste(pad, (self.x - 8, self.y - 8))
        self.img.paste(im, pos)
        self.x += im.width + 16
        self.row = max(self.row, im.height)
        return pos

    def uv(self, pos, px, py):
        """Atlas UV of pixel (px, py) inside the region placed at pos."""
        return ((pos[0] + px) / self.size, 1.0 - (pos[1] + py) / self.size)


def rectify(im, quad, size):
    """The four-cornered region quad (top left, top right, bottom right, bottom left; picture pixels) straightened into a
    rectangle of size (w, h): a side panel seen at an angle, made flat."""
    w, h = size
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A, b = [], []
    for (x, y), (u, v) in zip(quad, dst):
        A.append([u, v, 1, 0, 0, 0, -u * x, -v * x]); b.append(x)
        A.append([0, 0, 0, u, v, 1, -u * y, -v * y]); b.append(y)
    coeffs = np.linalg.solve(np.array(A, float), np.array(b, float))
    return im.transform((w, h), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)


# ---------------------------------------------------------------- geometry with projected UVs
class Builder:
    """Faces added in metres (x along the street, y into the picture: -y faces the street, z up). A face facing the street
    takes the front picture's pixels by projection; any other face takes a sample region, stretched once across it."""

    def __init__(self, atlas, front_pos, front_map, side_pos, side_size):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.atlas, self.front_pos, self.front_map = atlas, front_pos, front_map
        self.side_pos, self.side_size = side_pos, side_size

    def face(self, pts, side=None, project=True):
        """pts: corners in order, counter-clockwise seen from outside. side: a sample for a non-front face: (pos, size),
        stretched once across the face, or (pos, size, px_per_m), laid at the picture's scale from the face's corner (the
        sample made big enough by tiled())."""
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.normal_update()
        n = f.normal
        front = project and n.y < -0.25    # facing the street (walls, roof slopes toward it)
        if front:
            for loop in f.loops:
                px, py = self.front_map(loop.vert.co)
                loop[self.uv].uv = self.atlas.uv(self.front_pos, px, py)
        else:
            side = side or (self.side_pos, self.side_size)
            pos, (w, h) = side[0], side[1]
            metric = side[2] if len(side) > 2 else None
            # stretch the sample over the face's extent along its two widest axes
            cos = [l.vert.co for l in f.loops]
            ax = sorted(range(3), key=lambda i: -(max(c[i] for c in cos) - min(c[i] for c in cos)))
            a, bax = ax[0], ax[1]
            if a == 2 or (bax != 2 and abs(n.z) < 0.5):
                a, bax = bax, a
            lo_a, hi_a = min(c[a] for c in cos), max(c[a] for c in cos)
            lo_b, hi_b = min(c[bax] for c in cos), max(c[bax] for c in cos)
            if metric:
                # in the face's own plane: u level along it, v up its slope (or across a level face), in metres
                u = Vector((1, 0, 0)) if abs(n.z) > 0.999 else Vector((0, 0, 1)).cross(n).normalized()
                v = n.cross(u).normalized()
                lo_u = min(c.dot(u) for c in cos)
                hi_v = max(c.dot(v) for c in cos)
                for loop in f.loops:
                    c = loop.vert.co
                    px = min((c.dot(u) - lo_u) * metric, w - 1)
                    py = min((hi_v - c.dot(v)) * metric, h - 1)
                    loop[self.uv].uv = self.atlas.uv(pos, px, py)
                return f
            for loop in f.loops:
                c = loop.vert.co
                s = (c[a] - lo_a) / max(hi_a - lo_a, 1e-6)
                t = (c[bax] - lo_b) / max(hi_b - lo_b, 1e-6)
                loop[self.uv].uv = self.atlas.uv(pos, s * (w - 1), (1 - t) * (h - 1))
        return f

    def box(self, x0, x1, y0, y1, z0, z1, side=None, skip=()):
        P = lambda x, y, z: Vector((x, y, z))
        faces = {
            'front': [P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)],
            'back': [P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1)],
            'left': [P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1)],
            'right': [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)],
            'top': [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)],
            'bottom': [P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0)],
        }
        for k, pts in faces.items():
            if k not in skip:
                self.face(pts, side)

    def gable_roof(self, x0, x1, y_eave_front, y_ridge, y_eave_back, z_eave, z_ridge, side=None):
        """A roof of two slopes: the front slope faces the street (projected), the back slope and the gable ends take the sample."""
        P = lambda x, y, z: Vector((x, y, z))
        self.face([P(x0, y_eave_front, z_eave), P(x1, y_eave_front, z_eave), P(x1, y_ridge, z_ridge), P(x0, y_ridge, z_ridge)], side)
        self.face([P(x1, y_eave_back, z_eave), P(x0, y_eave_back, z_eave), P(x0, y_ridge, z_ridge), P(x1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x0, y_eave_front, z_eave), P(x0, y_ridge, z_ridge)], side)
        self.face([P(x1, y_eave_front, z_eave), P(x1, y_eave_back, z_eave), P(x1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x1, y_eave_back, z_eave), P(x1, y_eave_front, z_eave), P(x0, y_eave_front, z_eave)], side)

    def hip_roof(self, x0, x1, xr0, xr1, y_eave_front, y_ridge, y_eave_back, z_eave, z_ridge, side=None, project=True):
        """A hipped roof: the ridge (xr0 to xr1) shorter than the eaves, a sloping triangle at each end."""
        P = lambda x, y, z: Vector((x, y, z))
        self.face([P(x0, y_eave_front, z_eave), P(x1, y_eave_front, z_eave), P(xr1, y_ridge, z_ridge), P(xr0, y_ridge, z_ridge)], side, project)
        self.face([P(x1, y_eave_back, z_eave), P(x0, y_eave_back, z_eave), P(xr0, y_ridge, z_ridge), P(xr1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x0, y_eave_front, z_eave), P(xr0, y_ridge, z_ridge)], side)
        self.face([P(x1, y_eave_front, z_eave), P(x1, y_eave_back, z_eave), P(xr1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x1, y_eave_back, z_eave), P(x1, y_eave_front, z_eave), P(x0, y_eave_front, z_eave)], side)

    def skirt(self, outer, inner, z_eave, side=None, project=True):
        """A ground-floor roof skirt (hisashi): four slopes from an eave rectangle up to the upper storey's walls.
        outer: (x0, x1, y0, y1) at z_eave. inner: (x0, x1, y0, y1, z_left, z_right), the line the slopes meet the walls."""
        P = lambda x, y, z: Vector((x, y, z))
        ox0, ox1, oy0, oy1 = outer
        ix0, ix1, iy0, iy1, zl, zr = inner
        o = [P(ox0, oy0, z_eave), P(ox1, oy0, z_eave), P(ox1, oy1, z_eave), P(ox0, oy1, z_eave)]
        i = [P(ix0, iy0, zl), P(ix1, iy0, zr), P(ix1, iy1, zr), P(ix0, iy1, zl)]
        for k in range(4):
            self.face([o[k], o[(k + 1) % 4], i[(k + 1) % 4], i[k]], side, project)

    def object(self, name, outward=True):
        # every face outward (Unity draws front faces only): turned round where it faces the model's middle; a cut-out
        # is built facing the street and kept so (outward=False)
        mid = sum((v.co for v in self.bm.verts), Vector()) / max(len(self.bm.verts), 1)
        for f in self.bm.faces:
            f.normal_update()
            if outward and f.normal.dot(f.calc_center_median() - mid) < 0:
                f.normal_flip()
            if not outward and f.normal.y > 0:
                f.normal_flip()
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        o = K.new_obj(name, me)
        keep_uv_white(o)
        return o


def keep_uv_white(o):
    """The kit conventions (kit_lib.colorize) without touching the projected UVs: white vertex colour, part 0 in UV2."""
    me = o.data
    if not me.color_attributes:
        me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    col = me.color_attributes[0]
    for c in col.data:
        c.color = (1, 1, 1, 1)
    while len(me.uv_layers) < 2:
        me.uv_layers.new()
    for d in me.uv_layers[1].data:
        d.uv = (0, 0)


# ---------------------------------------------------------------- the models
# KM-P3, the user's photographic texture plates: a 3 x 2 grid (boards, mortar, tiles / concrete block, stone steps, window),
# each about 843 x 848 px, straight on, close up. Their scale, from what they show next to the house's own picture: the
# boards are about 170 px wide in the plate and 0.15 m in life; a tile's column is about 200 px and, on the home, 0.23 m.
P3 = 'KM-P3_texture_plates.png'
P3_PLATES = {'boards': (0, 0), 'mortar': (1, 0), 'tiles': (2, 0), 'block': (0, 1), 'stone': (1, 1), 'window': (2, 1)}
P3_PX_PER_M = {'boards': 1130.0, 'tiles': 880.0}


def p3_plate(name, trim=10):
    im = ref(P3)
    c, r = P3_PLATES[name]
    w, h = im.width / 3, im.height / 2
    return im.crop((round(c * w) + trim, round(r * h) + trim, round((c + 1) * w) - trim, round((r + 1) * h) - trim))


def seamless(im):
    """The plate made to repeat without a seam: blended with itself shifted by half, the shifted copy at the edges (where
    its own wrap is continuous) and the plate in the middle."""
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    h, w = a.shape[:2]
    b = np.roll(a, (h // 2, w // 2), (0, 1))
    tent = lambda n: 1 - np.abs(np.linspace(-1, 1, n))
    wa = np.outer(tent(h), tent(w)) + 1e-3
    wb = np.roll(wa, (h // 2, w // 2), (0, 1))
    return Image.fromarray(((a * wa[..., None] + b * wb[..., None]) / (wa + wb)[..., None]).clip(0, 255).astype(np.uint8))


def match_colours(im, ref_im):
    """im's colours moved to ref_im's (each Lab channel's mean and spread), so a plate takes the house's own colours."""
    a = cv2.cvtColor(np.asarray(im.convert('RGB')), cv2.COLOR_RGB2LAB).astype(np.float32)
    r = cv2.cvtColor(np.asarray(ref_im.convert('RGB')), cv2.COLOR_RGB2LAB).astype(np.float32)
    for c in range(3):
        a[..., c] = (a[..., c] - a[..., c].mean()) / (a[..., c].std() + 1e-6) * r[..., c].std() + r[..., c].mean()
    return Image.fromarray(cv2.cvtColor(a.clip(0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB))


# In the plates' own pixels (p3_plate, its 10 px border trimmed): the boards' grooves, and the tiles' column seams and
# the cut just below each row's shadowed lower edge (one band = one row of tiles with its edge).
P3_BOARD_GROOVES = [0, 142, 317, 490, 665, 823]
P3_TILE_COLUMNS = [180, 385, 590, 795]
P3_TILE_ROWS = [45, 240, 440, 655]


def boards_texture(colours_from, px_per_m, w, h, seed=11):
    """KM-P3's boards, laid one board at a time: each board a random one of the plate's five, made to repeat top to
    bottom without a seam, sometimes upside down, started at a random height; so no patch of the plate repeats in a grid.
    In the house's colours, at px_per_m, w x h px."""
    rng = np.random.default_rng(seed)
    pl = match_colours(p3_plate('boards'), colours_from)
    k = px_per_m / P3_PX_PER_M['boards']
    strips = []
    for x0, x1 in zip(P3_BOARD_GROOVES[:-1], P3_BOARD_GROOVES[1:]):
        a = np.asarray(pl.crop((x0, 0, x1, pl.height))).astype(np.float32)
        b = np.roll(a, a.shape[0] // 2, 0)
        t = 1 - np.abs(np.linspace(-1, 1, a.shape[0])) + 1e-3
        wb = np.roll(t, a.shape[0] // 2)
        a = (a * t[:, None, None] + b * wb[:, None, None]) / (t + wb)[:, None, None]
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        strips.append(np.asarray(im.resize((max(round(im.width * k), 2), max(round(im.height * k), 2)), Image.LANCZOS)))
    out = np.zeros((h, w, 3), np.uint8)
    x = 0
    while x < w:
        st = strips[rng.integers(len(strips))]
        if rng.random() < 0.5:
            st = st[::-1]
        st = np.roll(st, rng.integers(st.shape[0]), 0)
        col = np.concatenate([st] * (h // st.shape[0] + 2), 0)[:h]
        out[:, x:x + st.shape[1]] = col[:, :min(st.shape[1], w - x)]
        x += st.shape[1]
    return Image.fromarray(out)


def tiles_texture(colours_from, px_per_m, w, h, seed=7):
    """KM-P3's tiles, laid one tile at a time: each a random one of the plate's clean tiles (the ones with no nest or
    debris on them), so neither a stain nor a clump repeats in a grid. Each tile cell is one column wide and one row tall
    with its shadowed lower edge, so cells fit in any order. In the house's colours, at px_per_m, w x h px."""
    rng = np.random.default_rng(seed)
    pl = match_colours(p3_plate('tiles'), colours_from)
    raw = np.asarray(p3_plate('tiles')).astype(np.int32)
    cw, ch = 205, 205
    cells = []
    for y0, y1 in zip(P3_TILE_ROWS[:-1], P3_TILE_ROWS[1:]):
        for x0, x1 in zip(P3_TILE_COLUMNS[:-1], P3_TILE_COLUMNS[1:]):
            r = raw[y0:y1, x0:x1]
            debris = ((r[..., 0] - r[..., 2] > 18) & (r[..., 0] > 60)).mean()
            if debris < 0.004:
                cells.append(pl.crop((x0, y0, x1, y1)).resize((cw, ch), Image.LANCZOS))
    k = px_per_m / P3_PX_PER_M['tiles']
    sw, sh = max(round(cw * k), 4), max(round(ch * k), 4)
    cells = [np.asarray(c.resize((sw, sh), Image.LANCZOS)).astype(np.float32) for c in cells]
    # each tile brought to the same average colour (its own stains and sheen kept), so the roof shows no patchwork
    mean = np.mean([c.reshape(-1, 3).mean(0) for c in cells], 0)
    cells = [(c - c.reshape(-1, 3).mean(0) + mean).clip(0, 255).astype(np.uint8) for c in cells]
    out = np.zeros((h + sh, w + sw, 3), np.uint8)
    for y in range(0, h, sh):
        for x in range(0, w, sw):
            out[y:y + sh, x:x + sw] = cells[rng.integers(len(cells))]
    print('tiles: %d clean tiles of KM-P3\'s 9' % len(cells))
    return Image.fromarray(out[:h, :w])


def plate_sample(name, colours_from, px_per_m, w, h):
    """A KM-P3 plate, seamless, in the house's colours, at px_per_m, repeated to w x h px."""
    im = seamless(match_colours(p3_plate(name), colours_from))
    k = px_per_m / P3_PX_PER_M[name]
    im = im.resize((max(round(im.width * k), 8), max(round(im.height * k), 8)), Image.LANCZOS)
    return tiled(im, w, h)


def tiled(im, w, h):
    """The sample repeated to w x h px, so a face laid at the picture's scale never runs off it."""
    out = Image.new('RGB', (w, h))
    for y in range(0, h, im.height):
        for x in range(0, w, im.width):
            out.paste(im, (x, y))
    return out


def unsky(im, box, pale=False):
    """Paints out the sky inside box (the band of the roofs' outlines), so a roof edge that sits a few pixels off the
    drawn one shows tiles, not blue. Sky is the saturated blue (blue 45 above red, 12 above green), widened by 3 px; each takes
    the mean of its non-sky neighbours, growing inward from the roof until none is left."""
    a = np.asarray(im.convert('RGB'), dtype=np.float32).copy()
    x0, y0, x1, y1 = box
    r = a[y0:y1, x0:x1]
    if pale:     # a photograph's pale summer sky (about 194, 212, 232): bright, a little bluer than it is red or green
        sky = (r[..., 2] - r[..., 0] > 25) & (r[..., 2] - r[..., 1] > 8) & (r[..., 2] > 150)
    else:
        sky = (r[..., 2] - r[..., 0] > 45) & (r[..., 2] - r[..., 1] > 12) & (r[..., 2] > 90)
    for _ in range(3):     # and the soft fringe round it, which would otherwise seed the fill with blue
        sky = sky | np.roll(sky, 1, 0) | np.roll(sky, -1, 0) | np.roll(sky, 1, 1) | np.roll(sky, -1, 1)
    for _ in range(400):
        if not sky.any():
            break
        ok = ~sky
        tot = np.zeros_like(r)
        cnt = np.zeros(sky.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh_ok = np.roll(ok, (dy, dx), (0, 1))
            tot += np.roll(r, (dy, dx), (0, 1)) * sh_ok[..., None]
            cnt += sh_ok
        grow = sky & (cnt > 0)
        r[grow] = tot[grow] / cnt[grow][:, None]
        sky &= ~grow
    a[y0:y1, x0:x1] = r
    return Image.fromarray(a.clip(0, 255).astype('uint8'))


def rebrand(im, box, text, font='/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf'):
    """Replaces a drink logo that reads as a real brand with an invented one (the base prompt: invented names only): the
    panel inside box keeps its own red, row by row (from its margins), and takes text in white, centred."""
    from PIL import ImageDraw, ImageFont
    a = np.asarray(im.convert('RGB')).copy()
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        margin = np.concatenate([a[y, x0:x0 + 3], a[y, x1 - 3:x1]])
        a[y, x0:x1] = np.median(margin, axis=0).astype(np.uint8)
    out = Image.fromarray(a)
    d = ImageDraw.Draw(out)
    size = 14
    f = ImageFont.truetype(font, size)
    while d.textlength(text, font=f) > (x1 - x0) - 6 and size > 8:
        size -= 1
        f = ImageFont.truetype(font, size)
    w = d.textlength(text, font=f)
    d.text(((x0 + x1 - w) / 2, (y0 + y1) / 2 - size * 0.6), text, font=f, fill=(250, 248, 244),
           stroke_width=0)
    return out


def build_vending(atlas):
    """KM-A06, the red drink vending machine: its front from the photographic KM1-1 (straight on), its side from KM-P1
    (straightened; KM-P1's photographic version is still to come)."""
    km11, p1 = ref(HOME['src']), ref('KM-P1_props_sheet.png')
    km11 = rebrand_machines(km11)
    W, D, H = 1.0, 0.75, 1.83
    x0, y0, x1, y1 = 1687, 625, 1824, 873        # the front, in the photographic KM1-1's pixels
    front = km11.crop((x0, y0, x1, y1))
    fpos = atlas.place(front)
    side = rectify(p1, [(1700, 48), (1757, 62), (1755, 398), (1700, 428)], (104, 254))
    spos = atlas.place(side)
    top = side.crop((10, 4, 94, 40)).resize((104, 78))
    tpos = atlas.place(top)
    sx, sz = (x1 - x0) / W, (y1 - y0) / H
    fmap = lambda co: ((co.x + W / 2) * sx, (H - co.z) * sz)
    b = Builder(atlas, fpos, fmap, spos, side.size)
    b.box(-W / 2, W / 2, -D / 2, D / 2, 0.0, H, skip=('top', 'bottom'))
    P = lambda x, y, z: Vector((x, y, z))
    b.face([P(-W / 2, -D / 2, H), P(W / 2, -D / 2, H), P(W / 2, D / 2, H), P(-W / 2, D / 2, H)], (tpos, top.size))
    return b.object('KmVendingRed'), dict(source='photo/KM1-1 (front), KM-P1 (side)', real_size=[W, D, H])


def rebrand_machines(im):
    """Both vending machines in the photographic KM1-1 kept the real drink logo through the restyle: each panel gets an
    invented name, and the red machine's round badge is painted out in the panel's white."""
    im = rebrand(im, (1702, 750, 1754, 790), 'うみかぜ')
    im = rebrand(im, (1857, 754, 1910, 793), 'うみかぜ')
    return rebrand(im, (1786, 741, 1818, 763), '')


# The home's picture: the photographic KM1-1 (refs/photo, the restyle of the user's corrected KM1-1), the house at its
# left, with its entrance under the gable and the fence open in front of it. About 120 px to the metre (the entrance
# doors, 2.1 m); the pavement where the pots stand is at y 893; the gable's middle at x 1052.
HOME = dict(src='photo/KM1-1_hase_lanes.png', cx=1052.0, gy=893.0, s=120.0, crop=(270, 40, 1640, 897))


def dewire(im, wires, x0, x1, roof=(210, 305), search=8, half=2):
    """Takes the power lines off a roof. Each wire is (its rough y at x0, at x1, +1 to fill from below or -1 from above);
    along it, column by column, the darkest thin line within search px is the wire (black on light tiles), its track
    smoothed. The band 2 x half + 1 px tall round it is filled from exactly one tile row away, the same for the whole
    wire so the copied tiles stay in line: the tile rows' spacing is measured on the roof (rows roof[0] to roof[1])."""
    a = np.asarray(im.convert('RGB')).copy()
    luma = a.astype(np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
    wire = np.zeros(luma.shape, bool)
    tracks = []
    for ya, yb, side in wires:
        xs = np.arange(x0, x1)
        est = ya + (yb - ya) * (xs - x0) / (x1 - x0)
        track = []
        for x, e in zip(xs, est):
            ys = np.arange(int(e) - search, int(e) + search + 1)
            thin = luma[ys, x] - 0.5 * (luma[ys - 3, x] + luma[ys + 3, x])
            track.append(ys[int(np.argmin(thin))])
        track = np.array(track, np.float32)
        smooth = np.array([np.median(track[max(i - 15, 0):i + 16]) for i in range(len(track))]).round().astype(int)
        tracks.append((xs, smooth, side))
        for x, y in zip(xs, smooth):
            wire[y - half - 1:y + half + 2, x] = True
    # the tile rows' spacing: the shift that best repeats the roof onto itself, away from the wires
    r0, r1 = roof
    cols = slice(x0 + 60, x1 - 200)
    best_d, best_c = None, 1e9
    for d in range(18, 33):
        ok = ~wire[r0:r1 - d, cols] & ~wire[r0 + d:r1, cols]
        c = np.abs(luma[r0:r1 - d, cols] - luma[r0 + d:r1, cols])[ok].mean()
        if c < best_c:
            best_d, best_c = d, c
    for xs, ys, side in tracks:
        d = side * best_d
        for x, y in zip(xs, ys):
            rows = np.arange(y - half, y + half + 1)
            a[rows, x] = a[rows + d, x]
        for x, y in zip(xs, ys):               # soften the band's two edges a little so no seam shows
            for e in (y - half - 1, y + half + 1):
                n = a[e - 1:e + 2, x].astype(np.int32)
                a[e, x] = ((n[0] + 2 * n[1] + n[2]) // 4).astype(np.uint8)
    print('dewire: the tile rows repeat every %d px' % best_d)
    return Image.fromarray(a)


def build_home(atlas):
    """KM-B01, the kid's home (the photographic KM1-1, its left): the two-storey timber house with its hipped upper roof,
    the skirt roof round the ground floor with the entrance gable, the air conditioners on the skirt roof, the entrance
    with its sliding lattice doors, and the board fence either side of it. Every face the picture doesn't show takes
    KM-P3's photographic boards and tiles, in the house's colours. Also returns a trial (not exported): the same house
    with KM-P3's tiles on the street-facing roofs too, the picture's ridge cap and gutters kept as strips."""
    src = ref(HOME['src'])
    # what stands in front of the fence becomes its own models: their pixels leave the fence and the entrance's walls
    masks = garden_masks(src)
    allm = np.zeros(np.asarray(src).shape[:2], np.uint8)
    for m in masks.values():
        allm |= m
    for _, (x0, y0, x1), _ in GARDEN:
        allm[y0 - 4:GARDEN_GROUND + 1, x0 - 4:x1 + 4] = 1
    fixed = paint_out(src, allm, ref_rows=(650, 720))
    fixed = unsky(fixed, (500, 30, 1540, 240), pale=True)     # the upper roof's outline against the sky
    cx, gy, s, crop_box = HOME['cx'], HOME['gy'], HOME['s'], HOME['crop']
    fpos = atlas.place(fixed.crop(crop_box))
    fmap = lambda co: (cx + co.x * s - crop_box[0], gy - co.z * s - crop_box[1])
    # the hidden faces: KM-P3's boards and tiles at 160 px to the metre, coloured like the picture's boards and roof
    dens = 160.0
    boards = boards_texture(fixed.crop((605, 265, 725, 380)), dens, 1320, 440)
    bpos = atlas.place(boards)
    tiles = tiles_texture(fixed.crop((700, 100, 1000, 180)), dens, 1120, 1100)
    tpos = atlas.place(tiles)
    casing = fixed.crop((665, 392, 693, 450))              # the air conditioner's casing beside its grille
    cpos = atlas.place(casing)
    side, roof, ac = (bpos, boards.size, dens), (tpos, tiles.size, dens), (cpos, casing.size)
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    P = lambda x, y, z: Vector((x, y, z))

    def house(name, plate_roofs):
        h = Builder(atlas, fpos, fmap, bpos, boards.size)
        pr = not plate_roofs
        # the ground floor (its front: the entrance between the fences, the walls behind them) and the upper storey,
        # set back
        h.box(X(520), X(1600), -3.0, 4.0, 0.0, Z(548), side=side, skip=('bottom', 'top'))
        h.box(X(598), X(1482), -2.0, 3.0, Z(548), Z(220), side=side, skip=('bottom',))
        # the skirt roof: its eave at y 548 from x 466 to 1624, hipped at both corners, meeting the upper walls at y 470
        h.skirt((X(466), X(1624), -3.6, 4.6), (X(598), X(1482), -2.0, 3.0, Z(470), Z(470)), Z(548), side=roof,
                project=pr)
        # the entrance gable on the skirt roof: its front triangle (eaves at y 522, the ridge ornament's top at 352)
        # faces the street; its two slopes keep the barge line's height at every depth (so straight on they stay inside
        # the triangle) and run back over the skirt roof, meeting it in a valley, to the upper wall
        ga, gb, gm, gpeak, gbase = X(745), X(1360), X(1052), Z(352), Z(522)
        zs = lambda y: Z(548) + (y + 3.6) / 1.6 * (Z(470) - Z(548))     # the skirt roof's height at depth y
        yv = -3.6 + (gbase - Z(548)) / (Z(470) - Z(548)) * 1.6           # where the gable's eave meets the skirt
        t = (zs(-2.0) - gbase) / (gpeak - gbase)                          # how far up the slope the valley reaches
        h.face([P(ga, -3.7, gbase), P(gb, -3.7, gbase), P(gm, -3.7, gpeak)], roof)
        for e in (ga, gb):
            xv = e + (gm - e) * t
            h.face([P(e, -3.7, gbase), P(e, yv, gbase), P(xv, -2.0, zs(-2.0)), P(gm, -2.0, gpeak), P(gm, -3.7, gpeak)],
                   roof)
        # the two air conditioners standing on the skirt roof against the upper wall
        for a0, a1 in ((592, 696), (1315, 1420)):
            h.box(X(a0), X(a1), -2.35, -2.0, Z(455), Z(387), side=ac, skip=('bottom', 'back'))
        # the upper roof, hipped: eaves x 528 to 1507 at y 222, the ridge x 672 to 1478 at y 80 (its cap's top)
        h.hip_roof(X(528), X(1507), X(672), X(1478), -2.6, 0.5, 3.6, Z(222), Z(80), side=roof, project=pr)
        if plate_roofs:
            # the picture's ridge cap and the two gutters, as strips in front of the plate-tiled roofs
            h.box(X(672), X(1478), -0.1, 0.6, Z(104), Z(80), side=roof, skip=('bottom',))
            h.box(X(526), X(1509), -2.7, -2.55, Z(228), Z(214), side=roof, skip=('back',))
            h.box(X(464), X(1626), -3.7, -3.55, Z(553), Z(540), side=roof, skip=('back',))
        return h.object(name)

    home = house('KmHome', False)
    trial = house('KmHomeTrialP3', True)

    fence = Builder(atlas, fpos, fmap, bpos, boards.size)
    for f0, f1 in ((281, 876), (1270, 1622)):            # 2.3 m tall, along the lane, open at the entrance
        fence.box(X(f0), X(f1), -4.6, -4.45, 0.0, Z(620), side=side, skip=('bottom',))
    fence_obj = fence.object('KmHomeFence')
    fence_obj.parent = home
    garden, _ = build_garden(atlas, src, masks, None)
    garden.parent = home
    return home, trial, dict(source='photo/KM1-1 (left): the house, its entrance and its fence; in front of the fence, '
                                    'the pots, hydrangeas and bonsai (KmHomeGarden); the hidden faces in KM-P3\'s boards '
                                    'and tiles',
                             cutouts=['KmHomeGarden'],
                             cutout_material='Toon, _ALPHATEST_ON, _Cutoff 0.5, _Cull 0 (KamakuraCutout)',
                             real_size=[round((1624 - 281) / s, 2), 9.2, round(Z(80), 2)])


# ---------------------------------------------------------------- the things in front of the home
# What stands on the pavement in front of the photographic KM1-1's fence, in groups that touch: (name, the box round it,
# hints of where it surely is: the grey and dark pots, the bonsai trunk, which a colour model alone takes for the
# fence). The ground is at y 893.
GARDEN_GROUND = 893
GARDEN = [
    ('pots_left', (394, 795, 507), [(400, 870, 425, 892), (444, 860, 503, 892), (405, 860, 440, 892)]),
    ('planter_left', (507, 826, 587), [(512, 872, 584, 892)]),
    ('hydrangea_pink', (580, 726, 698), [(645, 852, 690, 892), (600, 862, 640, 892)]),
    ('hydrangea_planter', (698, 744, 810), [(700, 865, 805, 892)]),
    ('hydrangea_pots', (810, 756, 944), [(810, 860, 870, 892), (885, 855, 935, 892)]),
    ('bonsai_bowl', (1293, 795, 1396), [(1316, 873, 1390, 892), (1340, 840, 1360, 873)]),
    ('bonsai_pine', (1387, 754, 1516), [(1427, 801, 1477, 873), (1421, 873, 1499, 892)]),
    ('pot_right', (1529, 812, 1585), [(1535, 851, 1582, 892)]),
]
# fence seen between and beside them: never part of them
GARDEN_BACK = {}


def garden_masks(src, groups=None, back=None, ground=None):
    """Each group's cut-out (a 0/1 mask over the whole picture), by GrabCut: a colour model of the group against one of
    what's round it, seeded with what is surely the group (saturated or bright: leaves, flowers, terracotta, the white
    bin) and what is surely fence (dark, brownish grey and the same all the way up and down a board, as leaves, soil and
    flowers are not), plus the hints. Holes under 80 px (dark gaps in a bush) are filled."""
    A = np.asarray(src.convert('RGB'))
    F = A.astype(np.float32)
    luma = F[..., 0] * 0.3 + F[..., 1] * 0.59 + F[..., 2] * 0.11
    chroma = np.sqrt(((F - luma[..., None]) ** 2).sum(-1))
    vstd = np.sqrt(np.maximum(cv2.blur(luma ** 2, (1, 13)) - cv2.blur(luma, (1, 13)) ** 2, 0))
    fence = (chroma < 24) & (luma < 105) & (vstd < 7) & (F[..., 0] >= F[..., 1] - 2)
    groups = GARDEN if groups is None else groups
    back = GARDEN_BACK if back is None else back
    ground = GARDEN_GROUND if ground is None else ground
    masks = {}
    for name, (x0, y0, x1), hints in groups:
        # the background is learnt from the fence above the group (and the fence-like pixels inside its box), not from
        # beside it, where along a crowded fence the next group's leaves would teach it that leaves are background
        y1, m, mx = ground, 20, 3
        X0, Y0, X1, Y1 = x0 - mx, y0 - m, x1 + mx, y1 + 4
        sub = np.ascontiguousarray(A[Y0:Y1, X0:X1, ::-1])
        lu, ch = luma[Y0:Y1, X0:X1], chroma[Y0:Y1, X0:X1]
        gc = np.full(lu.shape, cv2.GC_BGD, np.uint8)
        inner = np.zeros(lu.shape, bool)
        inner[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
        gc[inner] = cv2.GC_PR_BGD
        gc[inner & ((ch > 26) | (lu > 135))] = cv2.GC_PR_FGD
        gc[inner & ((ch > 50) | (lu > 185))] = cv2.GC_FGD
        gc[inner & fence[Y0:Y1, X0:X1]] = cv2.GC_BGD
        for hx0, hy0, hx1, hy1 in hints:
            gc[hy0 - Y0:hy1 - Y0, hx0 - X0:hx1 - X0] = cv2.GC_FGD
        for hx0, hy0, hx1, hy1 in back.get(name, []):
            gc[max(hy0 - Y0, 0):hy1 - Y0, max(hx0 - X0, 0):hx1 - X0] = cv2.GC_BGD
        cv2.grabCut(sub, gc, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
        fg = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
        keep = np.zeros_like(fg)
        for i in range(1, n):
            if st[i, 4] >= 120:
                keep[lab == i] = 1
        hn, hl, hs, _ = cv2.connectedComponentsWithStats((1 - keep).astype(np.uint8), 4)
        for i in range(1, hn):
            x, y, w, h, a = hs[i]
            if a < 80 and x > 0 and y > 0 and x + w < keep.shape[1] and y + h < keep.shape[0]:
                keep[hl == i] = 1
        full = np.zeros(A.shape[:2], np.uint8)
        full[Y0:Y1, X0:X1] = keep
        masks[name] = full
    return masks


def tree_mask(src, box=(1092, 398, 1512, 627)):
    """The persimmon behind the fence, above the fence's top (y 620): its leaves and its orange fruit against the house."""
    A = np.asarray(src.convert('RGB')).astype(np.int32)
    x0, y0, x1, y1 = box
    r, g, b = A[y0:y1, x0:x1, 0], A[y0:y1, x0:x1, 1], A[y0:y1, x0:x1, 2]
    leaf = (g > r + 8) & (g > b + 2) & (g > 45)
    fruit = (r > 170) & (g > 80) & (g < 175) & (b < 90) & (r > g + 30)
    m = (leaf | fruit).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # the tree is the largest green mass, with what lies close round it (loose leaves, fruit); the neighbours' trees
    # behind the house, further off, are not
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    big = 1 + int(np.argmax(st[1:, 4]))
    near = cv2.dilate((lab == big).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] >= 40 and (i == big or near[lab == i].any()):
            keep[lab == i] = 1
    full = np.zeros(A.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = keep
    return full


def paint_out(img, mask, ref_rows=(700, 727), grow=3):
    """The fence and porch walls behind what stood in front of them: each masked pixel takes its own column's boards
    from the rows above every object (ref_rows), repeated down (the boards run straight up and down)."""
    a = np.asarray(img.convert('RGB')).copy()
    m = cv2.dilate(mask.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)) > 0
    r0, r1 = ref_rows
    ys, xs = np.nonzero(m)
    a[ys, xs] = a[r0 + (ys - r0) % (r1 - r0), xs]
    return Image.fromarray(a)


def cutout_arc(b, atlas, src, mask, box, cx, gy, s, y_back, name, dx=0):
    """One group as a cut-out on half an elliptic cylinder, its ends against the fence (y_back), its middle toward the
    street: straight on it is the picture exactly; turned, it is round. The cut-out's colours are the picture's own; its
    alpha the group's mask."""
    x0, y0, x1, y1 = box
    rgba = np.dstack([np.asarray(src.convert('RGB'))[y0:y1, x0:x1], (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    xa, xb, top = X(x0 + dx), X(x1 + dx), Z(y0)      # placed dx px along from where the picture has it
    half = (xb - xa) / 2
    ry = min(max(0.4 * (xb - xa), 0.08), 0.30)
    N = 8
    ring = [(xa + half - half * math.cos(math.pi * k / N), y_back - ry * math.sin(math.pi * k / N)) for k in range(N + 1)]
    uvl = b.uv
    for k in range(N):
        (xp, yp), (xq, yq) = ring[k], ring[k + 1]
        f = b.bm.faces.new([b.bm.verts.new(Vector(v)) for v in ((xp, yp, 0.0), (xq, yq, 0.0), (xq, yq, top), (xp, yp, top))])
        for loop in f.loops:
            c = loop.vert.co
            loop[uvl].uv = atlas.uv(pos, cx + c.x * s - dx - x0, gy - c.z * s - y0)
    return ry


def build_garden(atlas, src, masks, tmask, shift=None):
    """The pots, plants and the bicycle in front of the fence (KmHomeGarden), and the persimmon behind it (KmHomeTree):
    cut-outs, drawn with the kit's cut-out material."""
    cx, gy, s = HOME['cx'], HOME['gy'], HOME['s']
    g = Builder(atlas, None, None, None, None)
    for i, (name, (x0, y0, x1), _) in enumerate(GARDEN):
        if shift is not None and name not in shift:
            continue
        m = masks[name]
        ys, xs = np.nonzero(m)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, GARDEN_GROUND + 1)
        # each group a little further out than the one before where they overlap, so no two cut-outs share a plane
        cutout_arc(g, atlas, src, m, box, cx, gy, s, -4.62 - 0.01 * (i % 3), name, (shift or {}).get(name, 0))
    garden = g.object('KmHomeGarden', outward=False)
    if tmask is None:
        return garden, None
    t = Builder(atlas, None, None, None, None)
    ys, xs = np.nonzero(tmask)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    rgba = np.dstack([np.asarray(src.convert('RGB'))[y0:y1, x0:x1], (tmask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    f = t.bm.faces.new([t.bm.verts.new(Vector(v)) for v in ((X(x0), -3.8, Z(y1)), (X(x1), -3.8, Z(y1)),
                                                          (X(x1), -3.8, Z(y0)), (X(x0), -3.8, Z(y0)))])
    for loop in f.loops:
        c = loop.vert.co
        loop[t.uv].uv = atlas.uv(pos, cx + c.x * s - x0, gy - c.z * s - y0)
    tree = t.object('KmHomeTree', outward=False)
    return garden, tree

# ---------------------------------------------------------------- the review board
CUTOUTS = ('KmHomeGarden', 'KmHomeTree')     # drawn with the kit's cut-out material (the atlas alpha against 0.5)


def with_cutout(m, tex, surf):
    """m's surface shown where the atlas alpha passes 0.5, nothing elsewhere."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    tex.image.alpha_mode = 'STRAIGHT'
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
    nt.links.new(tex.outputs['Alpha'], gt.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gt.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(surf, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'DITHERED'
    return m


def unlit(atlas_path, cut=False):
    m = bpy.data.materials.new('KmUnlitCut' if cut else 'KmUnlit')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(atlas_path, check_existing=True)
    tex.interpolation = 'Linear'
    em = nt.nodes.new('ShaderNodeEmission')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    if cut:
        with_cutout(m, tex, em.outputs[0])
    return m


def render(path, cam_loc, cam_target, ortho=None, fov=34.0, size=(1200, 900), only=None):
    sc = bpy.context.scene
    for o in sc.objects:
        if o.type == 'MESH':
            o.hide_render = only is not None and o.name not in only
    cam = bpy.data.objects.get('ReviewCam') or K.new_obj('ReviewCam', bpy.data.cameras.new('ReviewCam'))
    cam.location = Vector(cam_loc)
    cam.rotation_euler = (Vector(cam_target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    if ortho:
        cam.data.ortho_scale = ortho
    else:
        cam.data.angle = math.radians(fov)
    sc.camera = cam
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new('W')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return Image.open(path).convert('RGB')


def board(home, vend, atlas_path, out):
    mat, cut = unlit(atlas_path), unlit(atlas_path, cut=True)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(cut if o.name in CUTOUTS else mat)
    tmp = os.path.dirname(out)
    km11 = rebrand_machines(ref(HOME['src']))
    rows = []
    # the home: the picture, the model straight on (orthographic, at the picture's scale), the model at three-quarters
    x0, y0, x1, y1 = HOME['crop']
    sc = HOME['s']
    W, H = x1 - x0, y1 - y0
    a = ref(HOME['src']).crop(HOME['crop'])
    hx, hz = ((x0 + x1) / 2 - HOME['cx']) / sc, (HOME['gy'] - (y0 + y1) / 2) / sc
    b = render(os.path.join(tmp, 'km_home_front.png'), (hx, -40, hz), (hx, 0, hz), ortho=W / sc, size=(W, H),
               only={'KmHome', 'KmHomeFence'} | set(CUTOUTS))
    c = render(os.path.join(tmp, 'km_home_34.png'), (hx - 13, -17, 5.5), (hx, 0, 3.2), fov=40, size=(W, H),
               only={'KmHome', 'KmHomeFence'} | set(CUTOUTS))
    rows.append([a, b, c])
    a = km11.crop((1687, 625, 1824, 873)).resize((276, 500))
    b = render(os.path.join(tmp, 'km_vend_front.png'), (0, -10, 0.915), (0, 0, 0.915), ortho=1.83,
               size=(276, 500), only={'KmVendingRed'})
    c = render(os.path.join(tmp, 'km_vend_34.png'), (2.4, -2.6, 1.6), (0, 0, 0.9), fov=40, size=(560, 490), only={'KmVendingRed'})
    rows.append([a, b, c])
    # close up, turned: the two groups in front of the fence, standing on their own
    names = {'KmHome', 'KmHomeFence'} | set(CUTOUTS)
    X = lambda px: (px - HOME['cx']) / sc
    gl, gr = (X(394) + X(944)) / 2, (X(1293) + X(1585)) / 2
    d = render(os.path.join(tmp, 'km_garden_left.png'), (gl - 2.6, -8.6, 1.5), (gl, -4.7, 0.5), fov=40,
               size=(900, 600), only=names)
    e = render(os.path.join(tmp, 'km_garden_right.png'), (gr + 2.6, -8.6, 1.5), (gr, -4.7, 0.55), fov=40,
               size=(900, 600), only=names)
    from PIL import ImageDraw, ImageFont
    try:
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    except OSError:
        small = ImageFont.load_default()

    def label(text, w=900, h=600):
        im = Image.new('RGB', (w, h), (40, 40, 46))
        ImageDraw.Draw(im).multiline_text((10, 10), text, fill=(235, 235, 240), font=small, spacing=10)
        return im

    rows.append([label('Close up, turned:\nthe pots and plants\nstand on their own'), d, e])
    # the trial: the street-facing roofs in KM-P3's photographic tiles too (the picture's ridge cap and gutters kept)
    trial = {'KmHomeTrialP3', 'KmHomeFence'} | set(CUTOUTS)
    b2 = render(os.path.join(tmp, 'km_trial_front.png'), (hx, -40, hz), (hx, 0, hz), ortho=W / sc, size=(W, H),
                only=trial)
    c2 = render(os.path.join(tmp, 'km_trial_34.png'), (hx - 13, -17, 5.5), (hx, 0, 3.2), fov=40, size=(W, H), only=trial)
    rows.append([label('Trial: every roof in\nKM-P3\'s photographic\ntiles (ridge cap and\ngutters from your\npicture)'), b2, c2])
    # the roofs close up, turned: as now (the picture's tiles in front) and the trial
    rx = X(672)
    cam, tgt = (rx - 2.6, -6.0, 7.4), (rx + 0.6, -1.5, 5.8)
    f1 = render(os.path.join(tmp, 'km_roof_now.png'), cam, tgt, fov=36, size=(900, 600), only=names)
    f2 = render(os.path.join(tmp, 'km_roof_trial.png'), cam, tgt, fov=36, size=(900, 600), only=trial)
    rows.append([label('The roofs close up:\nnow (left) and the\ntrial (right)'), f1, f2])
    pad, head = 24, 70
    widths = [max(r[i].width for r in rows) for i in range(3)]
    W = sum(widths) + pad * 4
    Hh = head + sum(max(im.height for im in r) for r in rows) + pad * (len(rows) + 1)
    sheet = Image.new('RGB', (W, Hh), (40, 40, 46))
    from PIL import ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 38)
    except OSError:
        font = ImageFont.load_default()
    x = pad
    for i, title in enumerate(['Your picture', 'The model, straight on', 'The model, at three-quarters']):
        ImageDraw.Draw(sheet).text((x, 18), title, fill=(235, 235, 240), font=font)
        x += widths[i] + pad
    y = pad + head
    for r in rows:
        x = pad
        for i, im in enumerate(r):
            sheet.paste(im, (x, y))
            x += widths[i] + pad
        y += max(im.height for im in r) + pad
    sheet.save(out, quality=90)
    print('board', out, sheet.size)


def build_props():
    """The street props (km_views.py, docs/KAMAKURA_BUILD.md Step 2): KM1-1's, each carved from the user's own views of it
    (front, right side, back, top) and textured from them, in its own texture (<Model>.png beside its FBX)."""
    props = []
    for name, (pid, folder, height, opts) in KV.props().items():
        root, img, fr = KV.build(name, os.path.join(KV.SHEETS, folder), height, K.new_obj, **opts)
        cut = bool(opts.get('cutout'))
        tex = name + '.png'
        Image.fromarray(img if cut else img[..., :3]).save(os.path.join(OUT, tex))
        for x in [root] + list(root.children_recursive):
            keep_uv_white(x)
            x.data.uv_layers.active_index = 0
        print('%-18s %s views, %.2f x %.2f x %.2f m, top in %s slices, round in %s' % (
            name, folder, fr.W, fr.D, fr.H, fr.slices['top'], fr.slices['round']))
        props.append((root, dict(id=pid, source='sheets/%s (its views, made from KM1-1)' % folder,
                                 real_size=[round(fr.W, 2), round(fr.D, 2), height], texture=tex, cutout=cut)))
    return props


def props_review(props, out_dir):
    """The strict review of the props (docs/ASSET_REVIEW.md), for asset_review_page.py: source/<Model>.jpg (the user's
    front view), views/<Model>.jpg (all eight sides), motion/<Model>_<motion>.gif (the barrier's arm lowering and
    rising), review.json (the seventeen checks, measured where they can be: open edges, triangles, size), and board.jpg
    (each beside its views: the front view and the model straight on at the same scale, the three-quarter view and the
    model at three-quarters, and the model from the street)."""
    import json
    import asset_review as AR
    from PIL import ImageDraw, ImageFont
    for sub in ('views', 'source', 'motion', 'tmp'):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
    for root, info in props:
        m = unlit(os.path.join(OUT, info['texture']), cut=info['cutout'])
        for o in [root] + list(root.children_recursive):
            o.data.materials.clear()
            o.data.materials.append(m)
    tmp = os.path.join(out_dir, 'tmp')
    rows, review = [], {}
    S = 520
    for root, info in props:
        name = root.name
        names = {name} | {c.name for c in root.children_recursive}
        folder = os.path.join(KV.SHEETS, info['source'].split('/')[1].split(' ')[0])
        views = KV.read_views(folder)
        loc = root.location.copy()
        root.location = (0, 0, 0)
        bpy.context.view_layer.update()
        AR.eight_views(root, os.path.join(out_dir, 'views', name + '.jpg'), render, cell_px=360,
                       title='%s: every side (Right is the street side, as the game sees it)' % name)
        W, D, H = info['real_size']

        def crop(im):
            """The view cut to its object with a margin, and the margin's frame in metres (its middle x, z and height),
            the object's box being W x H."""
            x0, y0, x1, y1 = KV.bbox(KV.object_mask(im))
            p = int(0.04 * max(x1 - x0, y1 - y0))
            c = (max(0, x0 - p), max(0, y0 - p), min(im.shape[1], x1 + p), min(im.shape[0], y1 + p))
            s = (y1 - y0) / H
            return (Image.fromarray(im).crop(c), ((c[0] + c[2]) / 2 - x0) / s - W / 2, (y1 - (c[1] + c[3]) / 2) / s,
                    (c[2] - c[0]) / s, (c[3] - c[1]) / s)
        front, fx, fz, fw, fh = crop(views['front'])
        src = front.copy()
        src.thumbnail((600, 600))
        src.save(os.path.join(out_dir, 'source', name + '.jpg'), quality=88)
        motions = []
        if 'Arm' in [c.name.split('.')[0] for c in root.children]:
            def lift(parts, rc, p):
                e = AR._smooth(0.0, 0.4, p) - AR._smooth(0.6, 1.0, p)
                parts['Arm'].rotation_euler = (0, -math.radians(84) * e, 0)
                return 0.0, 0.0
            AR.motion_gif(root, lift, os.path.join(out_dir, 'motion', name + '_lift.gif'), render, frames=24, cell_px=280,
                          ms=120, label='lift')
            motions.append('lift')
        k = S / front.height
        size = (max(60, int(front.width * k)), S)
        a = front.resize(size)
        b = render(os.path.join(tmp, name + '_front.png'), (fx, -60, fz), (fx, 0, fz), ortho=max(fw, fh), size=size,
                   only=names)
        three = views.get('three')
        c0 = crop(three)[0] if three is not None else Image.new('RGB', (S, S), (60, 60, 66))
        c0.thumbnail((S, S))
        top = max(H, W)
        c = render(os.path.join(tmp, name + '_34.png'), (1.0 * top, -1.35 * top, 0.7 * top), (0, 0, 0.45 * H), fov=40,
                   size=(S, S), only=names)
        d = render(os.path.join(tmp, name + '_game.png'), (-2.5, -9.0, 1.6), (0, 0, 0.45 * H), fov=40, size=(S, S),
                   only=names)
        rows.append((name, info, [a, b, c0, c, d]))
        # the checks
        tris = K.tree_tris(root)
        open_edges = 0
        for o in [root] + list(root.children_recursive):
            counts = {}
            for poly in o.data.polygons:
                for ek in poly.edge_keys:
                    counts[ek] = counts.get(ek, 0) + 1
            open_edges += sum(1 for v in counts.values() if v == 1)
        default = {
            1: ('pass', 'one solid carved from its views: each part once, looked at in Top and Bottom'),
            2: ('pass' if open_edges == 0 else 'FAIL', '%d edges with one face' % open_edges),
            3: ('pass', 'carved from its front, side and top views: each part as deep as its side and top show it'),
            4: ('pass', 'every face takes its pixels from the view that faces it squarely and can see it (the solid says '
                        'what hides what); the left side the right side\'s (no view of its own)'),
            5: ('pass' if tris <= 1500 else 'FAIL', '%s m, %d triangles (a prop\'s budget: 1,500), its own %d px texture'
                % (' x '.join('%.2f' % v for v in info['real_size']), tris, 1024)),
            6: ('pass', 'its outline the views\' outlines; no background on its edges (looked at on the board)'),
            7: ('pass', 'no holes; the gaps the views show (between bars, beams and pillars) stay open'),
            8: ('pass', 'stands on its own, its own model'),
            9: ('pass', 'from the user\'s views (BASE KM-S0), made from the photographic KM1-1'),
            10: ('pass', 'solid and whole'),
            11: ('pass', 'no brand or logo'),
            12: ('pass', 'no power line across it, no sky on its edges'),
            13: ('pass', 'none needed'),
            14: ('n/a', 'no moving parts'),
            15: ('n/a', 'no moving parts'),
            16: ('n/a', 'no feet'),
            17: ('n/a', 'one piece'),
        }
        default.update(KV.NOTES.get(name, {}))
        review[name] = dict(id=info.get('id', ''), sheet=info['source'], size=info['real_size'], tris=tris,
                            motions=motions, checks=[[i, AR_CHECK_NAMES[i - 1], default[i][0], default[i][1]]
                                                     for i in range(1, 18)])
        root.location = loc
    json.dump(review, open(os.path.join(out_dir, 'review.json'), 'w'), indent=1, ensure_ascii=False)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except OSError:
        font = small = ImageFont.load_default()
    pad, head = 20, 60
    heads = ['Your front view', 'The model, straight on', 'Your three-quarter view', 'The model at three-quarters',
             'From the street']
    widths = [max(max(r[2][i].width for r in rows), 300) for i in range(len(heads))]
    Wd = sum(widths) + pad * (len(heads) + 1)
    Hh = head + sum(S + 50 for _ in rows) + pad * (len(rows) + 1)
    sheet = Image.new('RGB', (Wd, Hh), (40, 40, 46))
    dr = ImageDraw.Draw(sheet)
    x = pad
    for i, t in enumerate(heads):
        dr.text((x, 16), t, fill=(235, 235, 240), font=font)
        x += widths[i] + pad
    y = head + pad
    for name, info, ims in rows:
        dr.text((pad, y), '%s  %d triangles  %s m' % (name, K.tree_tris(bpy.data.objects[name]),
                                                     ' x '.join('%.2f' % v for v in info['real_size'])),
                fill=(235, 235, 240), font=small)
        y += 40
        x = pad
        for i, im in enumerate(ims):
            sheet.paste(im, (x, y))
            x += widths[i] + pad
        y += S + pad
    sheet.save(os.path.join(out_dir, 'board.jpg'), quality=88)
    print('props board', os.path.join(out_dir, 'board.jpg'), sheet.size)


AR_CHECK_NAMES = ['Every part once', 'Closed shell', "Depth from each part's own width", 'Views the game sees',
                  'Size, triangles', 'Outline whole', 'No holes', 'Own models before walls', 'Look target', 'Solid',
                  'No brands', 'No wires or sky', 'Repairs listed', 'Rig names', 'Joints overlap', 'Feet planted',
                  'Each part only itself']


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = Atlas(ATLAS_SIZE)
    vend, vinfo = build_vending(atlas)
    home, trial, hinfo = build_home(atlas)
    home.location.x = 0
    vend.location.x = 8.5
    props = build_props()
    for k, (o, _) in enumerate(props):
        o.location.x = 11.0 + 3.0 * k
    atlas_path = os.path.join(OUT, 'KamakuraAtlas.png')
    atlas.img.save(atlas_path)
    mat = K.material('Kamakura', atlas_path)
    cut = K.material('KamakuraCutout', atlas_path)
    ct = next(n for n in cut.node_tree.nodes if n.type == 'TEX_IMAGE')
    bsdf = next(n for n in cut.node_tree.nodes if n.type == 'BSDF_DIFFUSE')
    with_cutout(cut, ct, bsdf.outputs[0])
    manifest = K.Manifest('Kamakura', 'KamakuraAtlas.png')
    K.assign(trial, mat)                 # the KM-P3 roof trial: in the .blend and on the board, not exported
    for root, info in [(home, hinfo), (vend, vinfo)] + props:
        if 'texture' in info:                # a prop from its views: its own texture
            pm = K.material(root.name, os.path.join(OUT, info['texture']))
            if info['cutout']:
                pt = next(n for n in pm.node_tree.nodes if n.type == 'TEX_IMAGE')
                pb = next(n for n in pm.node_tree.nodes if n.type == 'BSDF_DIFFUSE')
                with_cutout(pm, pt, pb.outputs[0])
            K.assign(root, pm)
        else:
            K.assign(root, mat)
        for c in root.children_recursive:
            if c.name in CUTOUTS:
                c.data.materials.clear()
                c.data.materials.append(cut)
        loc = root.location.copy()
        root.location = (0, 0, 0)
        K.export_model(root, os.path.join(OUT, root.name + '.fbx'))
        manifest.add(root, **info)
        root.location = loc
        print('%-14s %5d triangles' % (root.name, K.tree_tris(root)))
    manifest.save(os.path.join(OUT, 'Kamakura.json'))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Kamakura.blend'))
    if BOARD:
        home.location.x = 0
        vend.location.x = 0
        board(home, vend, atlas_path, BOARD)
    if PROPS_REVIEW:
        props_review(props, PROPS_REVIEW)


if __name__ == '__main__':
    main()
