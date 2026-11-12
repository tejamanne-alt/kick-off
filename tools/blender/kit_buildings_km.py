# The KAMAKURA kit (docs/KAMAKURA_BUILD.md): models built by script to the measurements of the user's reference pictures
# (review/kamakura/refs), each street-facing face textured by projecting the picture's own pixels onto it, so seen from the
# street, as the game camera sees it, the model shows exactly the painting. Sides and tops take samples from the same
# pictures (the props sheet shows the props' sides). This first version builds two models, to prove the method: the kid's
# home with its fence (KM-x2) and the red vending machine (KM1-1 front, KM-P1 side).
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

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS else os.path.abspath('out_km')
BOARD = ARGS[ARGS.index('--board') + 1] if '--board' in ARGS else None
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

    def face(self, pts, side=None):
        """pts: corners in order, counter-clockwise seen from outside. side: a sample for a non-front face: (pos, size),
        stretched once across the face, or (pos, size, px_per_m), laid at the picture's scale from the face's corner (the
        sample made big enough by tiled())."""
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.normal_update()
        n = f.normal
        front = n.y < -0.25    # facing the street (walls, roof slopes toward it)
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

    def hip_roof(self, x0, x1, xr0, xr1, y_eave_front, y_ridge, y_eave_back, z_eave, z_ridge, side=None):
        """A hipped roof: the ridge (xr0 to xr1) shorter than the eaves, a sloping triangle at each end."""
        P = lambda x, y, z: Vector((x, y, z))
        self.face([P(x0, y_eave_front, z_eave), P(x1, y_eave_front, z_eave), P(xr1, y_ridge, z_ridge), P(xr0, y_ridge, z_ridge)], side)
        self.face([P(x1, y_eave_back, z_eave), P(x0, y_eave_back, z_eave), P(xr0, y_ridge, z_ridge), P(xr1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x0, y_eave_front, z_eave), P(xr0, y_ridge, z_ridge)], side)
        self.face([P(x1, y_eave_front, z_eave), P(x1, y_eave_back, z_eave), P(xr1, y_ridge, z_ridge)], side)
        self.face([P(x0, y_eave_back, z_eave), P(x1, y_eave_back, z_eave), P(x1, y_eave_front, z_eave), P(x0, y_eave_front, z_eave)], side)

    def skirt(self, outer, inner, z_eave, side=None):
        """A ground-floor roof skirt (hisashi): four slopes from an eave rectangle up to the upper storey's walls.
        outer: (x0, x1, y0, y1) at z_eave. inner: (x0, x1, y0, y1, z_left, z_right), the line the slopes meet the walls."""
        P = lambda x, y, z: Vector((x, y, z))
        ox0, ox1, oy0, oy1 = outer
        ix0, ix1, iy0, iy1, zl, zr = inner
        o = [P(ox0, oy0, z_eave), P(ox1, oy0, z_eave), P(ox1, oy1, z_eave), P(ox0, oy1, z_eave)]
        i = [P(ix0, iy0, zl), P(ix1, iy0, zr), P(ix1, iy1, zr), P(ix0, iy1, zl)]
        for k in range(4):
            self.face([o[k], o[(k + 1) % 4], i[(k + 1) % 4], i[k]], side)

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
def tiled(im, w, h):
    """The sample repeated to w x h px, so a face laid at the picture's scale never runs off it."""
    out = Image.new('RGB', (w, h))
    for y in range(0, h, im.height):
        for x in range(0, w, im.width):
            out.paste(im, (x, y))
    return out


def unsky(im, box):
    """Paints out the sky inside box (the band of the roofs' outlines), so a roof edge that sits a few pixels off the
    drawn one shows tiles, not blue. Sky is the saturated blue (blue 45 above red, 12 above green), widened by 3 px; each takes
    the mean of its non-sky neighbours, growing inward from the roof until none is left."""
    a = np.asarray(im.convert('RGB'), dtype=np.float32).copy()
    x0, y0, x1, y1 = box
    r = a[y0:y1, x0:x1]
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
    """KM-A06, the red drink vending machine: its front from KM1-1 (straight on), its side from KM-P1 (straightened)."""
    km11, p1 = ref('KM1-1_hase_lanes.png'), ref('KM-P1_props_sheet.png')
    # the corrected KM1-1's machine carries a logo that reads as a real drink brand: an invented one instead
    km11 = rebrand(km11, (1700, 746, 1749, 786), 'うみかぜ')
    W, D, H = 1.0, 0.75, 1.83
    x0, y0, x1, y1 = 1686, 623, 1824, 868        # the front, in KM1-1's pixels (the corrected KM1-1)
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
    return b.object('KmVendingRed'), dict(source='KM1-1 (front), KM-P1 (side)', real_size=[W, D, H])


# The home's picture (KM-x2, the user's clean picture of the kid's home: KM1-1 drew a ghosted building over its right
# half) and its measurements: the sliding entrance doors (about 1.9 m) and the vending machine beside it (1.83 m) give
# about 110 px to the metre; the pavement (where the pots stand) is at y 881; the upper storey's middle at x 1766.
HOME = dict(src='KM-x2_home_street.png', cx=1766.0, gy=881.0, s=110.0, crop=(1340, 175, 2270, 884))


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
    """KM-B01, the kid's home (KM-x2): the two-storey timber house with its hipped upper roof, the skirt roof round the
    ground floor with the entrance gable, the air conditioners on the skirt roof, and the board fence either side of the
    entrance."""
    src = ref(HOME['src'])
    # what stands in front of the fence, and the garden tree, become their own models: their pixels leave the walls
    masks = garden_masks(src)
    tmask = tree_mask(src)
    allm = np.zeros_like(tmask)
    for m in masks.values():
        allm |= m
    fixed = paint_out(src, allm)
    a = np.asarray(fixed).copy()
    tm = cv2.dilate(tmask, np.ones((5, 5), np.uint8)) > 0
    ys, xs = np.nonzero(tm)
    a[ys, xs] = a[ys, xs - 620]          # the wall behind the tree: its window and frames, as the left half shows them
    fixed = Image.fromarray(a)
    # the two power lines across the upper roof belong to the street's poles, not the house
    fixed = dewire(fixed, [(229, 256, +1), (267.5, 299, -1)], 1340, 2300)
    fixed = unsky(fixed, (1340, 170, 2300, 330))    # the upper roof's outline against the sky
    cx, gy, s, crop_box = HOME['cx'], HOME['gy'], HOME['s'], HOME['crop']
    fpos = atlas.place(fixed.crop(crop_box))
    fmap = lambda co: (cx + co.x * s - crop_box[0], gy - co.z * s - crop_box[1])
    # the samples for the sides, laid at the picture's scale (110 px to the metre), repeated to cover the largest face
    # the upper storey's dark boards (left of the window, under the light band), drawn out along their grain to a
    # storey's height so no seam crosses them, then repeated along the wall
    boards = tiled(fixed.crop((1432, 385, 1528, 440)).resize((96, 330), Image.BICUBIC), 1056, 330)
    bpos = atlas.place(boards)
    tiles = tiled(fixed.crop((1600, 255, 1800, 305)), 1000, 750)     # the upper roof's tiles (two rows), wires taken off
    tpos = atlas.place(tiles)
    casing = fixed.crop((1480, 450, 1504, 494))            # the air conditioner's casing beside its grille
    cpos = atlas.place(casing)
    side, roof, ac = (bpos, boards.size, s), (tpos, tiles.size, s), (cpos, casing.size)
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    P = lambda x, y, z: Vector((x, y, z))

    house = Builder(atlas, fpos, fmap, bpos, boards.size)
    # the ground floor, under the skirt roof (its front: the entrance bay and, behind the fence, the walls), and the upper
    # storey, set back
    house.box(X(1390), X(2255), -3.0, 4.0, 0.0, Z(582), side=side, skip=('bottom', 'top'))
    house.box(X(1425), X(2110), -2.0, 3.0, Z(582), Z(312), side=side, skip=('bottom',))
    # the skirt roof: its eave at y 582 from x 1345 to 2258, hipped at both corners, meeting the upper walls at y 497-500
    house.skirt((X(1345), X(2258), -3.6, 4.6), (X(1425), X(2110), -2.0, 3.0, Z(497), Z(500)), Z(582), side=roof)
    # the entrance gable on the skirt roof: its front triangle (eaves at y 557, the ridge ornament's top at 412) faces
    # the street; its two slopes run back to the upper wall
    # the street; its two slopes keep the barge line's height at every depth (so straight on they stay inside the
    # triangle) and run back over the skirt roof, meeting it in a valley, to the upper wall
    ga, gb, gm, gpeak, gbase = X(1565), X(2065), X(1813), Z(412), Z(557)
    zs = lambda y: Z(582) + (y + 3.6) / 1.6 * (Z(498) - Z(582))     # the skirt roof's height at depth y
    yv = -3.6 + (gbase - Z(582)) / (Z(498) - Z(582)) * 1.6           # where the gable's eave meets the skirt
    t = (zs(-2.0) - gbase) / (gpeak - gbase)                          # how far up the slope the valley reaches the wall
    house.face([P(ga, -3.7, gbase), P(gb, -3.7, gbase), P(gm, -3.7, gpeak)], roof)
    for e in (ga, gb):
        xv = e + (gm - e) * t
        house.face([P(e, -3.7, gbase), P(e, yv, gbase), P(xv, -2.0, zs(-2.0)), P(gm, -2.0, gpeak), P(gm, -3.7, gpeak)], roof)
    # the two air conditioners standing on the skirt roof against the upper wall
    for a0, a1 in ((1420, 1510), (2010, 2097)):
        house.box(X(a0), X(a1), -2.35, -2.0, Z(502), Z(443), side=ac, skip=('bottom', 'back'))
    # the upper roof, hipped: eaves x 1385 to 2147 at y 310, the ridge x 1450 to 2103 at y 184 (its cap's top)
    house.hip_roof(X(1385), X(2147), X(1450), X(2103), -2.6, 0.5, 3.6, Z(310), Z(184), side=roof)
    home = house.object('KmHome')

    fence = Builder(atlas, fpos, fmap, bpos, boards.size)
    for f0, f1 in ((1388, 1655), (1968, 2255)):            # either side of the entrance, 2.1 m tall
        fence.box(X(f0), X(f1), -3.45, -3.3, 0.0, Z(645), side=side, skip=('bottom',))
    fence_obj = fence.object('KmHomeFence')
    fence_obj.parent = home
    garden, tree = build_garden(atlas, src, masks, tmask)
    garden.parent = home
    tree.parent = home
    return home, dict(source='KM-x2 (the middle): the house and its fence; in front of it, the pots, plants, bin, urn and '
                             'stand (KmHomeGarden), behind the right fence the garden tree (KmHomeTree)',
                      cutouts=list(CUTOUTS), cutout_material='Toon, _ALPHATEST_ON, _Cutoff 0.5, _Cull 0 (KamakuraCutout)',
                      real_size=[round((2258 - 1345) / s, 2), 8.2, round(Z(184), 2)])



# ---------------------------------------------------------------- the things in front of the home
# What stands on the pavement in front of KM-x2's fence, in groups that touch: (name, the box round it, hints of where it
# surely is: the dark bowls and the grey urn, which a colour model alone takes for the fence). The ground is at y 882.
GARDEN_GROUND = 882
GARDEN = [
    ('bin', (1386, 788, 1430), [(1392, 802, 1424, 878)]),
    ('pots_left', (1424, 793, 1522), [(1432, 856, 1458, 879), (1476, 837, 1493, 851), (1467, 855, 1490, 879),
                                      (1493, 860, 1517, 879)]),
    ('planter_left', (1519, 818, 1592), [(1524, 860, 1585, 879)]),
    ('pot_small', (1588, 833, 1622), [(1595, 864, 1614, 879)]),
    ('white_flowers', (1612, 802, 1662), [(1624, 855, 1658, 879)]),
    ('urn', (1655, 791, 1697), [(1664, 806, 1690, 870), (1662, 858, 1679, 876)]),
    ('bonsai', (1915, 753, 2098), [(1940, 856, 1998, 878), (2008, 854, 2028, 878), (2014, 830, 2060, 878),
                                   (2028, 775, 2042, 826)]),
    ('planter_right', (2063, 828, 2146), []),
    ('stand', (2094, 768, 2161), [(2108, 812, 2150, 876), (2121, 790, 2148, 804)]),
    ('hydrangea', (2155, 748, 2268), [(2168, 857, 2250, 878)]),
]
# fence and porch seen between and beside them: never part of them
GARDEN_BACK = {'bonsai': [(1913, 846, 1934, 886), (2064, 812, 2098, 851)],
               'stand': [(2092, 766, 2115, 803), (2153, 766, 2163, 803)],
               'hydrangea': [(2153, 852, 2166, 886), (2253, 852, 2272, 886)]}


def garden_masks(src):
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
    masks = {}
    for name, (x0, y0, x1), hints in GARDEN:
        y1, m = GARDEN_GROUND, 20
        X0, Y0, X1, Y1 = x0 - m, y0 - m, x1 + m, y1 + 4
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
        for hx0, hy0, hx1, hy1 in GARDEN_BACK.get(name, []):
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


def tree_mask(src, box=(2010, 576, 2240, 650)):
    """The garden tree behind the right fence, above the fence's top (y 645): its green against the house wall."""
    A = np.asarray(src.convert('RGB')).astype(np.int32)
    x0, y0, x1, y1 = box
    r, g, b = A[y0:y1, x0:x1, 0], A[y0:y1, x0:x1, 1], A[y0:y1, x0:x1, 2]
    green = ((g > r + 8) & (g > b + 2) & (g > 45)).astype(np.uint8)
    green = cv2.morphologyEx(green, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(green, 8)
    keep = np.zeros_like(green)
    for i in range(1, n):
        if st[i, 4] >= 150:
            keep[lab == i] = 1
    full = np.zeros(A.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = keep
    return full


def paint_out(img, mask, ref_rows=(732, 749), grow=3):
    """The fence and porch walls behind what stood in front of them: each masked pixel takes its own column's boards
    from the rows above every object (ref_rows), repeated down (the boards run straight up and down)."""
    a = np.asarray(img.convert('RGB')).copy()
    m = cv2.dilate(mask.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)) > 0
    r0, r1 = ref_rows
    ys, xs = np.nonzero(m)
    a[ys, xs] = a[r0 + (ys - r0) % (r1 - r0), xs]
    return Image.fromarray(a)


def cutout_arc(b, atlas, src, mask, box, cx, gy, s, y_back, name):
    """One group as a cut-out on half an elliptic cylinder, its ends against the fence (y_back), its middle toward the
    street: straight on it is the picture exactly; turned, it is round. The cut-out's colours are the picture's own; its
    alpha the group's mask."""
    x0, y0, x1, y1 = box
    rgba = np.dstack([np.asarray(src.convert('RGB'))[y0:y1, x0:x1], (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    xa, xb, top = X(x0), X(x1), Z(y0)
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
            loop[uvl].uv = atlas.uv(pos, cx + c.x * s - x0, gy - c.z * s - y0)
    return ry


def build_garden(atlas, src, masks, tmask):
    """The pots, plants, the bin, the urn and the stand in front of the fence (KmHomeGarden), and the garden tree behind
    the right fence (KmHomeTree): cut-outs, drawn with the kit's cut-out material."""
    cx, gy, s = HOME['cx'], HOME['gy'], HOME['s']
    g = Builder(atlas, None, None, None, None)
    for i, (name, (x0, y0, x1), _) in enumerate(GARDEN):
        m = masks[name]
        ys, xs = np.nonzero(m)
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, GARDEN_GROUND + 1)
        # each group a little further out than the one before where they overlap, so no two cut-outs share a plane
        cutout_arc(g, atlas, src, m, box, cx, gy, s, -3.47 - 0.01 * (i % 3), name)
    garden = g.object('KmHomeGarden', outward=False)
    t = Builder(atlas, None, None, None, None)
    ys, xs = np.nonzero(tmask)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    rgba = np.dstack([np.asarray(src.convert('RGB'))[y0:y1, x0:x1], (tmask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    pos = atlas.place(Image.fromarray(rgba, 'RGBA'))
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s
    f = t.bm.faces.new([t.bm.verts.new(Vector(v)) for v in ((X(x0), -3.2, Z(y1)), (X(x1), -3.2, Z(y1)),
                                                          (X(x1), -3.2, Z(y0)), (X(x0), -3.2, Z(y0)))])
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
    km11 = ref('KM1-1_hase_lanes.png')
    rows = []
    # the home: the picture, the model straight on (orthographic, at the picture's scale), the model at three-quarters
    x0, y0, x1, y1 = HOME['crop']
    sc = HOME['s']
    W, H = x1 - x0, y1 - y0
    a = ref(HOME['src']).crop(HOME['crop'])
    hx, hz = ((x0 + x1) / 2 - HOME['cx']) / sc, (HOME['gy'] - (y0 + y1) / 2) / sc
    b = render(os.path.join(tmp, 'km_home_front.png'), (hx, -40, hz), (hx, 0, hz), ortho=W / sc, size=(W, H),
               only={'KmHome', 'KmHomeFence'} | set(CUTOUTS))
    c = render(os.path.join(tmp, 'km_home_34.png'), (hx - 11, -14, 5.0), (hx, 0, 3.2), fov=40, size=(W, H),
               only={'KmHome', 'KmHomeFence'} | set(CUTOUTS))
    rows.append([a, b, c])
    a = km11.crop((1681, 621, 1819, 866)).resize((276, 490))
    b = render(os.path.join(tmp, 'km_vend_front.png'), (0, -10, 0.915), (0, 0, 0.915), ortho=1.83,
               size=(276, 490), only={'KmVendingRed'})
    c = render(os.path.join(tmp, 'km_vend_34.png'), (2.4, -2.6, 1.6), (0, 0, 0.9), fov=40, size=(560, 490), only={'KmVendingRed'})
    rows.append([a, b, c])
    # close up, turned: the two groups in front of the fence, standing on their own
    names = {'KmHome', 'KmHomeFence'} | set(CUTOUTS)
    X = lambda px: (px - HOME['cx']) / sc
    gl, gr = (X(1386) + X(1697)) / 2, (X(1915) + X(2268)) / 2
    d = render(os.path.join(tmp, 'km_garden_left.png'), (gl - 2.2, -7.2, 1.4), (gl, -3.5, 0.45), fov=38,
               size=(900, 600), only=names)
    e = render(os.path.join(tmp, 'km_garden_right.png'), (gr + 2.2, -7.2, 1.4), (gr, -3.5, 0.55), fov=38,
               size=(900, 600), only=names)
    rows.append([Image.new('RGB', (10, 10), (40, 40, 46)), d, e])
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


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = Atlas(ATLAS_SIZE)
    vend, vinfo = build_vending(atlas)
    home, hinfo = build_home(atlas)
    home.location.x = 0
    vend.location.x = 8.5
    atlas_path = os.path.join(OUT, 'KamakuraAtlas.png')
    atlas.img.save(atlas_path)
    mat = K.material('Kamakura', atlas_path)
    cut = K.material('KamakuraCutout', atlas_path)
    ct = next(n for n in cut.node_tree.nodes if n.type == 'TEX_IMAGE')
    bsdf = next(n for n in cut.node_tree.nodes if n.type == 'BSDF_DIFFUSE')
    with_cutout(cut, ct, bsdf.outputs[0])
    manifest = K.Manifest('Kamakura', 'KamakuraAtlas.png')
    for root, info in ((home, hinfo), (vend, vinfo)):
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


if __name__ == '__main__':
    main()
