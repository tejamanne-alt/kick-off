# REJECTED (docs/LEARNINGS.md, C14): the user found these drawn faces alien (big doll eyes, a stroke for a nose and a
# mouth). polish_all.py no longer runs it; face_ink.py gives the kids' own faces Max's finish instead, and uses the head
# canvas, the feature search and the drawing helpers below (Head, detect, spec_for, smooth_skin, stroke). Don't bring the
# painted faces back.
#
# Paints an illustrated face onto a scanned kid's atlas, so the four primary-school kids read as game characters (drawn
# eyes, clean skin, a simple mouth, in the spirit of Hana's and Max's painted faces) instead of photographs of children,
# while keeping their own skin tone, hair, outfit and head:
#   blenv/bin/python face_paint.py -- <Name> <in.fbx> <in atlas.png> <out atlas.png> [--review review.png]
#   (Name: PrimaryBoy (Kai), PrimaryBoy2 (Leo), PrimaryGirl (Mia), PrimaryGirl2 (Zoe); the style is STYLES[Name])
#
# How: every atlas texel is placed in 3D by the UV rasteriser (polish_lib.rasterize), so the front of the head can be
# seen as a flat front view, a canvas of 640 px for 32 cm centred 12 cm above the Head joint. There the scan's skin is
# replaced by a smooth field of its own colour (a wide Gaussian of the skin with the eyes, brows and lips left out) and new
# features are drawn as supersampled vector shapes: eyes (a white, a warm iris with a darker rim and a pupil, two
# highlights, a dark upper lash line), brows, a small nose stroke, a mouth and a little blush. The new face goes back into
# every atlas texel of the face's skin by its 3D position, divided by the vertex colour the game multiplies by; the sides
# of the head, the ears and the hairline fade back to the scan's own texture. The features sit where the scan's were (the
# darkest blobs for the irises, the darkest band above for the brows, the reddest blob for the mouth: detect()), unless
# the kid's style gives their places (where hair or the scan's texture misleads the search), and every size scales with
# the distance between the eyes. No vertex moves.
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polish_lib import rasterize, coverage, push_pull, load_png, save_png

C = 640           # canvas pixels (32 cm)
SS = 4            # supersampling of the drawn features
SPAN, CZ = 0.32, 0.12

# Each kid's face. eye spacing d is measured; sizes are fractions of it. Positions (canvas px), when given, override
# the detection. Colours are sRGB 0-255.
STYLES = {
    'PrimaryBoy': dict(   # Kai: a big happy grin, as in his model
        iris=(104, 64, 40), brow=(52, 34, 28), lash=0.8, flick=0.0, mouth_style='grin', smile=0.45, open=0.25, mouth_w=0.48),
    'PrimaryBoy2': dict(  # Leo: a calm, friendly smile
        iris=(92, 56, 36), brow=(40, 28, 24), lash=0.8, flick=0.0, mouth_style='smile', smile=0.5, open=0.0, mouth_w=0.36),
    'PrimaryGirl': dict(  # Mia: a sweet smile; her hair and the scan's cheeks mislead the search, so her features are placed
        iris=(84, 52, 34), brow=(44, 30, 26), lash=1.0, flick=0.5, mouth_style='smile', smile=0.55, open=0.18, mouth_w=0.34,
        lip=(214, 110, 112), eyes=[(200, 330), (448, 330)], brows=[(200, 268), (448, 268)], mouth_at=(336, 530)),
    'PrimaryGirl2': dict(  # Zoe: a small smile, pink lips
        iris=(100, 62, 40), brow=(46, 32, 26), lash=1.0, flick=0.5, mouth_style='smile', smile=0.45, open=0.0, mouth_w=0.34,
        lip=(222, 118, 128)),
}


# --------------------------------------------------------------------------------------------- the mesh
def mesh_arrays(fbx):
    """What the painter needs from the character's FBX (via Blender): its triangles' UVs, corners and vertices, the
    vertex positions, colours, Head weights and outfit parts, and the Head and Nose joints."""
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx, use_custom_normals=True, axis_forward='-Z', axis_up='Y', primary_bone_axis='Y',
                             secondary_bone_axis='X')
    kid = bpy.data.objects['Kid']; me = kid.data
    me.calc_loop_triangles()
    LT = len(me.loop_triangles)
    lv = np.zeros(LT * 3, int); me.loop_triangles.foreach_get('loops', lv)
    vv = np.zeros(LT * 3, int); me.loop_triangles.foreach_get('vertices', vv)
    nl = len(me.loops)
    uv0 = np.zeros(nl * 2); me.uv_layers[0].data.foreach_get('uv', uv0)
    uv1 = np.zeros(nl * 2); me.uv_layers[1].data.foreach_get('uv', uv1)
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
    col = me.color_attributes['Col']
    cd = np.zeros(len(col.data) * 4); col.data.foreach_get('color', cd); cd = cd.reshape(-1, 4)
    if col.domain == 'POINT':
        lvi = np.zeros(nl, int); me.loops.foreach_get('vertex_index', lvi); cd = cd[lvi]
    gi = kid.vertex_groups['Head'].index
    hw = np.zeros(len(me.vertices))
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi: hw[v.index] = g.weight
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    B = rig.data.bones
    return dict(tri_loops=lv.reshape(-1, 3), tri_verts=vv.reshape(-1, 3), uv0=uv0.reshape(-1, 2), uv1=uv1.reshape(-1, 2),
                co=co.reshape(-1, 3), col=cd, hw=hw, head=np.array(B['Head'].head_local), nose=np.array(B['Nose'].head_local))


class Head:
    """The atlas' texels placed on the head: canvas coordinates, facing, depth, outfit part, Head weight, vertex colour."""

    def __init__(self, d, atlas):
        self.d = d
        uvt = d['uv0'][d['tri_loops']]
        self.A = atlas[..., :3].copy()
        N = self.A.shape[0]
        self.tri, self.bary = rasterize(uvt, N)
        self.cov = coverage(uvt, N)
        m = self.tri >= 0
        self.m = m
        T = self.tri[m]; B = self.bary[m]
        tv = d['tri_verts'][T]
        self.P = (d['co'][tv] * B[..., None]).sum(1)
        self.hw = (d['hw'][tv] * B).sum(1)
        v = d['co'][d['tri_verts']]
        fn = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
        self.n = fn[T]
        self.part = np.round(d['uv1'][d['tri_loops'][T]][:, 0, 0]).astype(int)
        self.vc = (d['col'][d['tri_loops'][T]][..., :3] * B[..., None]).sum(1)
        self.head = d['head']
        f = d['nose'] - self.head; f[2] = 0; self.fwd = f / np.linalg.norm(f)
        self.side = np.cross(self.fwd, [0, 0, 1.0])
        rel = self.P - self.head
        self.cx = ((rel @ self.side) / SPAN + 0.5) * C
        self.cy = (0.5 - (rel[:, 2] - CZ) / SPAN) * C
        self.facing = self.n @ self.fwd
        self.depth = rel @ self.fwd
        self.skin_front = (self.hw > 0.5) & (self.part == 0) & (self.facing > 0.05) & (rel[:, 2] > -0.05)

    def splat(self, colours, sel):
        """The texels in `sel` drawn into the front view (the nearest wins), small holes closed."""
        img = np.zeros((C, C, 3), np.float32); zb = np.full((C, C), -1e9)
        ix = np.clip(self.cx[sel].astype(int), 0, C - 1); iy = np.clip(self.cy[sel].astype(int), 0, C - 1)
        dp = self.depth[sel]; o = np.argsort(dp)
        img[iy[o], ix[o]] = colours[sel][o]; zb[iy[o], ix[o]] = dp[o]
        filled = zb > -1e9
        di, (yy, xx) = ndimage.distance_transform_edt(~filled, return_indices=True)
        img = np.where((di < 3)[..., None], img[yy, xx], 0.15)
        return img, filled | (di < 3)

    def sample(self, layer):
        """A canvas-sized layer sampled (bilinear) at every covered texel."""
        x = np.clip(self.cx - 0.5, 0, C - 1.001); y = np.clip(self.cy - 0.5, 0, C - 1.001)
        x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
        L = layer
        return L[y0, x0] * (1 - fx) * (1 - fy) + L[y0, x0 + 1] * fx * (1 - fy) + L[y0 + 1, x0] * (1 - fx) * fy + L[y0 + 1, x0 + 1] * fx * fy


def front_view(head):
    return head.splat(head.A[head.m] * head.vc, head.skin_front)


def detect(head):
    """The scan's irises (the darkest compact blob each side of the middle, in the eyes' band), brows (the darkest band
    above each eye) and mouth (the reddest blob below the nose), in canvas px."""
    img, filled = front_view(head)
    lum = img.mean(2)
    yy, xx = np.mgrid[0:C, 0:C]
    band = filled & (yy > 260) & (yy < 430) & (xx > 120) & (xx < 520)
    dark = band & (lum < np.percentile(lum[band], 6))
    lab, n = ndimage.label(ndimage.binary_opening(dark, iterations=1))
    idx = range(1, n + 1)
    sizes = ndimage.sum(dark, lab, idx); cents = ndimage.center_of_mass(dark, lab, idx)
    left = [(s, c) for s, c in zip(sizes, cents) if c[1] < C / 2]
    right = [(s, c) for s, c in zip(sizes, cents) if c[1] >= C / 2]
    eL = max(left)[1] if left else (360, 230); eR = max(right)[1] if right else (360, 430)
    r = img[..., 0] - 0.5 * (img[..., 1] + img[..., 2])
    mb = filled & (yy > 470) & (yy < 600) & (xx > 220) & (xx < 440)
    red = mb & (r > np.percentile(r[mb], 92)) if mb.any() else mb
    my, mx = ndimage.center_of_mass(red) if red.any() else (540, 330)

    def brow(e):
        y0 = int(e[0]) - 110; y1 = int(e[0]) - 25; x0 = int(e[1]) - 50; x1 = int(e[1]) + 50
        sub = lum[y0:y1, x0:x1]; f = filled[y0:y1, x0:x1]
        if not f.any(): return (e[0] - 70, e[1])
        m = f & (sub <= np.percentile(sub[f], 12))
        cy, cx = ndimage.center_of_mass(m)
        return (y0 + cy, x0 + cx)
    bL, bR = brow(eL), brow(eR)
    return dict(eyes=[(eL[1], eL[0]), (eR[1], eR[0])], brows=[(bL[1], bL[0]), (bR[1], bR[0])], mouth=(mx, my))


# --------------------------------------------------------------------------------------------- drawing
def poly(d, pts, fill):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)


def ell(d, cx, cy, rx, ry, fill):
    d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=fill)


def bez(p0, p1, p2, n=24):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0, float) + 2 * (1 - t) * t * np.array(p1, float) + t ** 2 * np.array(p2, float)


def stroke(d, pts, w0, w1, fill, swell=0.25):
    """A tapered stroke along a polyline: width w0 at its start, w1 at its end, a little fuller in the middle."""
    pts = np.asarray(pts, float)
    tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    nor = np.stack([-tang[:, 1], tang[:, 0]], 1)
    t = np.linspace(0, 1, len(pts))
    w = (w0 + (w1 - w0) * t) * ((1 - swell) + swell * np.sin(np.pi * t))
    left = pts + nor * w[:, None] / 2; right = pts - nor * w[:, None] / 2
    poly(d, list(map(tuple, np.concatenate([left, right[::-1]]))), fill)


def clipped(base, draw_fn, clip_pts):
    """Draws draw_fn(ImageDraw) on a layer, keeps only what falls inside the polygon clip_pts, composites it on base."""
    mask = Image.new('L', base.size, 0); poly(ImageDraw.Draw(mask), clip_pts, 255)
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(layer), layer)
    a = np.minimum(np.asarray(layer)[..., 3], np.asarray(mask)).astype(np.uint8)
    layer.putalpha(Image.fromarray(a))
    base.alpha_composite(layer)


def eye(base, cx, cy, w, h, iris, ink, side, lash=1.0, flick=0.0):
    """An illustrated eye: a white with soft lid shade, a warm iris (darker rim, lighter lower half), a pupil, a big and a
    small highlight, a dark upper lash line (a flick at the outer corner for the girls) and a faint lower line.
    side: -1 the kid's right eye (canvas left), +1 the left."""
    s = side
    inner = (cx - s * w * 0.5, cy + h * 0.08); outer = (cx + s * w * 0.5, cy - h * 0.02)
    up = bez(inner, (cx - s * w * 0.04, cy - h * 1.0), outer, 40)
    lo = bez(outer, (cx + s * w * 0.02, cy + h * 0.78), inner, 40)
    opening = list(map(tuple, np.concatenate([up, lo])))
    ir = h * 0.5
    icx, icy = cx + s * w * 0.02, cy + h * 0.08
    darker = tuple(int(c * 0.5) for c in iris)
    lighter = tuple(min(255, int(c * 1.45 + 30)) for c in iris)

    def inside(dr, layer):
        poly(dr, opening, (252, 251, 252, 255))
        ell(dr, icx, icy, ir * 1.02, ir * 1.08, darker + (255,))
        ell(dr, icx, icy, ir * 0.9, ir * 0.96, iris + (255,))
        ell(dr, icx, icy + ir * 0.38, ir * 0.62, ir * 0.42, lighter + (150,))
        ell(dr, icx, icy, ir * 0.44, ir * 0.48, (22, 14, 16, 255))
        # the upper lid's shade across the top of the eye
        shade = Image.new('RGBA', layer.size, (0, 0, 0, 0))
        poly(ImageDraw.Draw(shade), list(map(tuple, np.concatenate([up, (up + [0, h * 0.4])[::-1]]))), (70, 44, 60, 110))
        layer.alpha_composite(shade.filter(ImageFilter.GaussianBlur(SS * 1.6)))
        ell(dr, icx + s * ir * 0.28, icy - ir * 0.36, ir * 0.3, ir * 0.3, (255, 255, 255, 255))
        ell(dr, icx - s * ir * 0.3, icy + ir * 0.36, ir * 0.12, ir * 0.12, (255, 255, 255, 235))
    clipped(base, inside, opening)
    d = ImageDraw.Draw(base)
    stroke(d, up[3:], h * 0.12 * lash, h * 0.24 * lash, ink)
    if flick > 0:
        tip = (up[-1][0] + s * w * 0.13 * flick, up[-1][1] - h * 0.2 * flick)
        stroke(d, bez(up[-6], up[-1] + [s * w * 0.03, -h * 0.02], tip, 10), h * 0.24 * lash, h * 0.05, ink, swell=0.0)
    stroke(d, lo[10:-8], h * 0.04, h * 0.03, ink[:3] + (110,))


def brow(d, cx, cy, w, side, col, th, arch=0.22):
    s = side
    p0 = (cx - s * w * 0.5, cy + w * 0.08); p2 = (cx + s * w * 0.5, cy + w * 0.06)
    stroke(d, bez(p0, (cx, cy - w * arch), p2, 30), th * 1.1, th * 0.5, col)


def smile(d, cx, cy, w, ink, lip, smile_=0.45, open_=0.0):
    """A small smile: a curved line, a hint of an open mouth below it, and a little lip colour under that."""
    p0 = (cx - w / 2, cy - w * 0.06); p2 = (cx + w / 2, cy - w * 0.06); p1 = (cx, cy + w * smile_ * 0.5)
    if open_ > 0:
        top = bez(p0, p1, p2, 30)
        bot = bez(p2, (cx, cy + w * (smile_ * 0.5 + 0.45 * open_)), p0, 30)
        poly(d, list(map(tuple, np.concatenate([top, bot]))), (120, 44, 52, 255))
        tongue = bez((cx - w * 0.2, cy + w * smile_ * 0.5), (cx, cy + w * (smile_ * 0.5 + 0.3 * open_)), (cx + w * 0.2, cy + w * smile_ * 0.5), 16)
        poly(d, list(map(tuple, np.concatenate([tongue, tongue[::-1] + [0, w * 0.04]]))), (224, 118, 124, 255))
    elif lip is not None:
        lp = bez((cx - w * 0.28, cy + w * smile_ * 0.35), (cx, cy + w * (smile_ * 0.5 + 0.2)), (cx + w * 0.28, cy + w * smile_ * 0.35), 20)
        poly(d, list(map(tuple, np.concatenate([bez((cx + w * 0.3, cy + w * smile_ * 0.3), (cx, cy + w * smile_ * 0.55), (cx - w * 0.3, cy + w * smile_ * 0.3), 20), lp]))), lip + (150,))
    stroke(d, bez(p0, p1, p2, 30), w * 0.06, w * 0.06, ink, swell=0.4)
    for sgn in (-1, 1):   # the corners turn up a little
        stroke(d, bez((cx + sgn * w * 0.47, cy - w * 0.05), (cx + sgn * w * 0.54, cy - w * 0.1), (cx + sgn * w * 0.56, cy - w * 0.16), 8), w * 0.05, w * 0.015, ink, swell=0.0)


def grin(d, cx, cy, w, ink, smile_=0.45, open_=0.25):
    """An open, happy mouth: a dark inside, a row of teeth along the top, a little tongue, a line round it."""
    top = bez((cx - w / 2, cy - w * 0.06), (cx, cy + w * 0.02), (cx + w / 2, cy - w * 0.06), 30)
    bot = bez((cx + w / 2, cy - w * 0.06), (cx, cy + w * (0.28 + 0.45 * open_) + w * smile_ * 0.2), (cx - w / 2, cy - w * 0.06), 30)
    shape = list(map(tuple, np.concatenate([top, bot])))

    def inside(dr, layer):
        poly(dr, shape, (110, 38, 46, 255))
        poly(dr, list(map(tuple, np.concatenate([top, (top + [0, w * 0.12])[::-1]]))), (252, 250, 246, 255))
        ell(dr, cx, cy + w * (0.28 + 0.45 * open_) * 0.82, w * 0.22, w * 0.11, (226, 116, 122, 255))
    clipped(d._image, inside, shape)
    stroke(d, np.concatenate([bot, top[1:2]]), w * 0.045, w * 0.045, ink, swell=0.0)
    stroke(d, top, w * 0.04, w * 0.04, ink, swell=0.0)


def nose(d, cx, cy, w, col):
    stroke(d, bez((cx - w * 0.5, cy), (cx, cy + w * 0.35), (cx + w * 0.5, cy), 16), w * 0.2, w * 0.14, col)


def blush(cx, cy, rx, ry, col, alpha):
    yy, xx = np.mgrid[0:C, 0:C]
    r = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    out = np.zeros((C, C, 4), np.float32)
    out[..., :3] = np.array(col) / 255.0
    out[..., 3] = np.clip(1 - r, 0, 1) ** 1.5 * alpha
    return out


def over(dst, src):
    a = src[..., 3:4]
    return dst * (1 - a) + src[..., :3] * a


def smooth_skin(head, sigma=20.0):
    """A smooth field of the skin's own colour over the front view: a normalised Gaussian of the skin texels whose
    colour is close to the median skin (eyes, brows, nostrils, lips and stray hair left out)."""
    img, filled = front_view(head)
    lum = img.mean(2); r = img[..., 0] - img[..., 1]
    med = np.median(img[filled], 0)
    chroma = img / np.maximum(img.sum(2, keepdims=True), 1e-3); mc = med / med.sum()
    good = filled & (np.abs(chroma - mc).sum(2) < 0.06) & (lum > np.percentile(lum[filled], 25)) \
        & (lum < np.percentile(lum[filled], 97)) & (r < np.percentile(r[filled], 85))
    good = ndimage.binary_erosion(good, iterations=2)
    w = ndimage.gaussian_filter(good.astype(np.float32), sigma)
    s = np.stack([ndimage.gaussian_filter(img[..., k] * good, sigma) for k in range(3)], -1) / np.maximum(w, 1e-6)[..., None]
    # most of the field is one even tone: keep a quarter of its variation
    mean = np.median(s[filled], 0)
    return mean + (s - mean) * 0.25, img


def spec_for(name, found):
    st = dict(STYLES[name])
    eyes = st.get('eyes') or found['eyes']
    brows = st.get('brows') or found['brows']
    mouth = st.get('mouth_at') or found['mouth']
    (xL, yL), (xR, yR) = eyes
    dsp = xR - xL
    ey = (yL + yR) / 2
    my = mouth[1]
    return dict(st, eyes=[(xL, ey), (xR, ey)], d=dsp, eye_w=0.5 * dsp, eye_h=0.42 * dsp,
                brows=[(brows[0][0], (brows[0][1] + brows[1][1]) / 2 - 0.03 * dsp), (brows[1][0], (brows[0][1] + brows[1][1]) / 2 - 0.03 * dsp)],
                brow_w=0.5 * dsp, brow_th=0.065 * dsp,
                nose=((xL + xR) / 2, ey + 0.6 * (my - ey)), nose_w=0.15 * dsp,
                mouth=((xL + xR) / 2, my), mouth_w=st['mouth_w'] * dsp,
                cheeks=[(xL - 0.06 * dsp, ey + 0.5 * (my - ey)), (xR + 0.06 * dsp, ey + 0.5 * (my - ey))], cheek_r=0.17 * dsp)


def paint(head, spec, review=None):
    skin, before = smooth_skin(head)
    base = Image.new('RGBA', (C * SS, C * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(base); d._image = base
    ink = (36, 24, 28, 255)
    for i, side in enumerate((-1, 1)):
        ex, ey = spec['eyes'][i]
        eye(base, ex, ey, spec['eye_w'], spec['eye_h'], tuple(spec['iris']), ink, side, spec['lash'], spec['flick'])
        bx, by = spec['brows'][i]
        brow(d, bx, by, spec['brow_w'], side, tuple(spec['brow']) + (255,), spec['brow_th'])
    nose(d, spec['nose'][0], spec['nose'][1], spec['nose_w'], (150, 92, 82, 170))
    mx, my = spec['mouth']
    if spec['mouth_style'] == 'grin':
        grin(d, mx, my, spec['mouth_w'], ink, spec['smile'], spec['open'])
    else:
        smile(d, mx, my, spec['mouth_w'], ink, tuple(spec['lip']) if spec.get('lip') else None, spec['smile'], spec['open'])
    feat = np.asarray(base.resize((C, C), Image.LANCZOS)).astype(np.float32) / 255
    for (bx, by) in spec['cheeks']:
        skin = over(skin, blush(bx, by, spec['cheek_r'] * 1.3, spec['cheek_r'], (236, 122, 122), 0.2))
    face = over(skin, feat)
    # how much each texel takes the new face: the front of the head and, inside the face, the undersides (nostrils, the
    # lip's shadow) too; fading toward the sides, the hairline and the neck
    yy = head.cy; xx = head.cx
    dsp = spec['d']
    fcx = (spec['eyes'][0][0] + spec['eyes'][1][0]) / 2
    fcy = (spec['eyes'][0][1] + spec['mouth'][1]) / 2
    ro = np.sqrt(((xx - fcx) / (dsp * 1.05)) ** 2 + ((yy - fcy) / (dsp * 1.0)) ** 2)
    inner = ro < 1.0
    front = np.clip((head.facing - 0.12) / 0.3, 0, 1)
    under = inner & (head.facing > -0.6) & (head.depth > 0.03)
    # only the face: fading out past its oval, so skin-tagged hair beside the cheeks and the ears keep their texture
    oval = np.clip((1.3 - ro) / 0.3, 0, 1)
    k = np.maximum(front, under * 1.0) * oval * np.clip((head.hw - 0.5) / 0.3, 0, 1)
    sel = (head.hw > 0.5) & (head.part == 0) & ((front > 0) | under)
    newtex = head.sample(face) / np.maximum(head.vc, 0.05)
    A = head.A.copy()
    flat = A.reshape(-1, 3)
    idx = np.flatnonzero(head.m.ravel())
    w = (k * sel)[:, None]
    flat[idx] = flat[idx] * (1 - w) + np.clip(newtex, 0, 1) * w
    if review:
        after, _ = head.splat(flat[idx] * head.vc, sel)
        save_png(np.concatenate([before, face, after], 1), review)
    return flat.reshape(A.shape)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    name, fbx, atlas_in, atlas_out = argv[:4]
    review = argv[argv.index('--review') + 1] if '--review' in argv else None
    d = mesh_arrays(fbx)
    atlas = load_png(atlas_in)
    head = Head(d, atlas)
    found = detect(head)
    spec = spec_for(name, found)
    out = paint(head, spec, review)
    if atlas.shape[2] == 4:
        out = np.concatenate([out, atlas[..., 3:4]], 2)
    save_png(push_pull(out, head.cov), atlas_out)
    print('[face_paint]', name, json.dumps({k: (np.round(v, 1).tolist() if isinstance(v, (list, tuple)) else v) for k, v in found.items()}))
