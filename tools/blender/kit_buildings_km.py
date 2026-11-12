# The KAMAKURA kit (docs/KAMAKURA_BUILD.md): models built by script to the measurements of the user's reference pictures
# (review/kamakura/refs), each street-facing face textured by projecting the picture's own pixels onto it, so seen from the
# street, as the game camera sees it, the model shows exactly the painting. Sides and tops take samples from the same
# pictures (the props sheet shows the props' sides). This first version builds two models, to prove the method: the kid's
# home with its fence (KM1-1) and the red vending machine (KM1-1 front, KM-P1 side).
#   blenv/bin/python kit_buildings_km.py -- /abs/outdir [--board /abs/board.png]
# Writes into outdir: <Model>.fbx per model, KamakuraAtlas.png, Kamakura.json, Kamakura.blend; with --board, a review board
# of each model beside its source picture: the picture, the model straight on, the model at three-quarters.
import bpy
import bmesh
import math
import os
import sys

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
        self.img = Image.new('RGB', (size, size), (255, 255, 255))
        self.x = self.y = self.row = 8

    def place(self, im):
        """Puts an image in the next free spot; returns its (x, y) in atlas pixels (top left)."""
        if self.x + im.width + 8 > self.size:
            self.x, self.y, self.row = 8, self.y + self.row + 16, 8
        if self.y + im.height + 8 > self.size:
            raise SystemExit('kit_buildings_km.py: the atlas is full')
        pos = (self.x, self.y)
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
        """pts: corners in order, counter-clockwise seen from outside. side: a (pos, size) sample for a non-front face."""
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
            pos, (w, h) = side or (self.side_pos, self.side_size)
            # stretch the sample over the face's extent along its two widest axes
            cos = [l.vert.co for l in f.loops]
            ax = sorted(range(3), key=lambda i: -(max(c[i] for c in cos) - min(c[i] for c in cos)))
            a, bax = ax[0], ax[1]
            if a == 2 or (bax != 2 and abs(n.z) < 0.5):
                a, bax = bax, a
            lo_a, hi_a = min(c[a] for c in cos), max(c[a] for c in cos)
            lo_b, hi_b = min(c[bax] for c in cos), max(c[bax] for c in cos)
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

    def object(self, name):
        # every face outward (Unity draws front faces only): turned round where it faces the model's middle
        mid = sum((v.co for v in self.bm.verts), Vector()) / max(len(self.bm.verts), 1)
        for f in self.bm.faces:
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - mid) < 0:
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


def build_vending(atlas):
    """KM-A06, the red drink vending machine: its front from KM1-1 (straight on), its side from KM-P1 (straightened)."""
    km11, p1 = ref('KM1-1_hase_lanes.png'), ref('KM-P1_props_sheet.png')
    W, D, H = 1.0, 0.75, 1.83
    x0, y0, x1, y1 = 1681, 621, 1819, 866        # the front, in KM1-1's pixels
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


def build_home(atlas):
    """KM-B01, the kid's home (KM1-1, left): the two-storey timber house, its roofs and the fence in front. The picture is
    about 119 px to the metre at the house; the ground is at y 890, the house's middle at x 1029."""
    km11 = ref('KM1-1_hase_lanes.png')
    # the ghosted patch beside the upper roof (a generation glitch in KM1-1): the roof is mirrored from its good left half
    fixed = km11.copy()
    # and the wall under its right half, where the same glitch shows a ghosted neighbour (above the right air conditioner)
    for band in ((1200, 79, 1480, 232), (1267, 225, 1410, 383)):
        mirror = km11.crop((2 * 987 - band[2], band[1], 2 * 987 - band[0], band[3])).transpose(Image.FLIP_LEFT_RIGHT)
        fixed.paste(mirror, band[:2])
    fixed = unsky(fixed, (440, 50, 1620, 272))    # the roofs and the light band under the upper eave
    cx, gy, s = 1029.0, 890.0, 119.0
    crop_box = (280, 60, 1620, 892)
    fpos = atlas.place(fixed.crop(crop_box))
    fmap = lambda co: (cx + co.x * s - crop_box[0], gy - co.z * s - crop_box[1])
    boards = fixed.crop((580, 270, 700, 380))              # the upper storey's dark boards (left of the window), for the sides
    bpos = atlas.place(boards)
    tiles = fixed.crop((700, 110, 900, 200))               # the roof's tiles, for the back slopes and gable ends
    tpos = atlas.place(tiles)
    side, roof = (bpos, boards.size), (tpos, tiles.size)
    X = lambda px: (px - cx) / s
    Z = lambda py: (gy - py) / s

    house = Builder(atlas, fpos, fmap, bpos, boards.size)
    # the ground floor (seen between the skirt roof and the fence) and the upper storey, symmetric about x 987 like the
    # roof (the picture's wall stops at x 1267, where the glitch starts; the repair above carries it on to 1407)
    house.box(X(475), X(1585), -3.0, 4.0, 0.0, Z(546), side=side, skip=('bottom', 'top'))
    house.box(X(567), X(1407), -2.0, 3.0, Z(546), Z(226), side=side, skip=('bottom',))
    # the skirt roof round the ground floor: its eave at y 546 from x 462 to 1605, hipped at both corners, meeting the
    # upper storey's wall at y 455 on the left and 432 on the right (as drawn)
    P = lambda x, y, z: Vector((x, y, z))
    house.skirt((X(462), X(1605), -3.6, 4.6), (X(567), X(1407), -2.0, 3.0, Z(455), Z(432)), Z(546), side=roof)
    # the entrance gable on the porch roof: its front triangle faces the street
    ga, gb, gpeak = X(720), X(1275), Z(355)
    house.face([P(ga, -3.7, Z(530)), P(gb, -3.7, Z(530)), P((ga + gb) / 2, -3.7, gpeak)], roof)
    house.face([P(gb, -3.7, Z(530)), P(gb, -2.2, Z(450)), P((ga + gb) / 2, -2.2, gpeak), P((ga + gb) / 2, -3.7, gpeak)], roof)
    house.face([P(ga, -2.2, Z(450)), P(ga, -3.7, Z(530)), P((ga + gb) / 2, -3.7, gpeak), P((ga + gb) / 2, -2.2, gpeak)], roof)
    # the upper roof
    house.hip_roof(X(500), X(1474), X(643), X(1331), -2.6, 0.5, 3.6, Z(224), Z(79), side=roof)
    home = house.object('KmHome')

    fence = Builder(atlas, fpos, fmap, bpos, boards.size)
    fence.box(X(284), X(1612), -4.6, -4.45, 0.0, Z(620), side=side, skip=('bottom',))
    fence_obj = fence.object('KmHomeFence')
    fence_obj.parent = home
    return home, dict(source='KM1-1 (left): the house and its fence', real_size=[round((1612 - 284) / s, 2), 8.6, round(Z(79), 2)])


# ---------------------------------------------------------------- the review board
def unlit(atlas_path):
    m = bpy.data.materials.new('KmUnlit')
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
    mat = unlit(atlas_path)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)
    tmp = os.path.dirname(out)
    km11 = ref('KM1-1_hase_lanes.png')
    rows = []
    # the home: the picture, the model straight on (orthographic, at the picture's scale), the model at three-quarters
    hw, hh = (1620 - 280) / 119.0, (892 - 60) / 119.0
    a = km11.crop((280, 60, 1620, 892))
    hx, hz = ((280 + 1620) / 2 - 1029) / 119.0, (890 - (60 + 892) / 2) / 119.0
    b = render(os.path.join(tmp, 'km_home_front.png'), (hx, -40, hz), (hx, 0, hz), ortho=hw, size=(1340, 832),
               only={'KmHome', 'KmHomeFence'})
    c = render(os.path.join(tmp, 'km_home_34.png'), (hx - 13, -16, 5.0), (hx, 0, 3.0), fov=40, size=(1340, 832),
               only={'KmHome', 'KmHomeFence'})
    rows.append([a, b, c])
    a = km11.crop((1681, 621, 1819, 866)).resize((276, 490))
    b = render(os.path.join(tmp, 'km_vend_front.png'), (0, -10, 0.915), (0, 0, 0.915), ortho=1.83,
               size=(276, 490), only={'KmVendingRed'})
    c = render(os.path.join(tmp, 'km_vend_34.png'), (2.4, -2.6, 1.6), (0, 0, 0.9), fov=40, size=(560, 490), only={'KmVendingRed'})
    rows.append([a, b, c])
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
    manifest = K.Manifest('Kamakura', 'KamakuraAtlas.png')
    for root, info in ((home, hinfo), (vend, vinfo)):
        K.assign(root, mat)
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
