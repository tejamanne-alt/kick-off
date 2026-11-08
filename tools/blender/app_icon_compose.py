# Lays out the app icon from app_icon_scene.py's render (scene.png, ball_front.png, scene.json): the walk to school, Max
# kicking a football along the footpath with the school ahead, under a morning sky with the sun rising behind the clock
# tower, a golden kick trail from his toe to the ball, a puff of dust and sparkles, and the logo's sunny "2".
# Writes every size the stores need:
#   python3 app_icon_compose.py <layers dir> <repo root> [--preview <dir>]
#     marketing/appstore/icon_1024.png               App Store icon: 1024 x 1024, opaque (iOS adds its own corners)
#     marketing/googleplay/icon_512.png              Google Play listing icon: 512 x 512, opaque (Play adds its own mask)
#     Assets/_Game/Art/Icon/AppIcon.png              the game's icon for every platform (BuildScripts), 1024, opaque
#     Assets/_Game/Art/Icon/AppIconBackground.png    Android adaptive icon, back layer: the whole picture in the middle 72 dp, 1024
#     Assets/_Game/Art/Icon/AppIconForeground.png    Android adaptive icon, front layer: clear (the picture is in the back), 1024
# --preview also writes a sheet of the icon masked the way iOS and Android show it, at home-screen and settings sizes;
# --two adds the logo's sunny "2" (read "to": kick off to school) in the top left corner, in the sky.
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

args = sys.argv[1:]
layers, root = args[0], args[1]
preview = args[args.index('--preview') + 1] if '--preview' in args else None
TWO = '--two' in args                       # the logo's sunny "2" in the top corner
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Assets', '_Game', 'Resources', 'Fonts', 'LilitaOne-Regular.ttf')

N = 2048                                    # drawn at twice the largest size, then scaled down
NAVY = (27, 37, 80)                         # the logo's ink
WHITE = (255, 255, 255)


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def radial(size, cx, cy, r, inner, outer, power=1.6):
    """An RGBA layer: inner colour (with its alpha) at (cx, cy) fading to outer by radius r."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.clip(np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r, 0, 1) ** power
    out = np.zeros((size, size, 4), np.float32)
    for c in range(4):
        out[..., c] = inner[c] + (outer[c] - inner[c]) * d
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def sky(size, sun):
    """Deep blue at the top to a pale morning blue at the horizon, the sun's warm glow and soft rays round it."""
    t = np.linspace(0, 1, size, dtype=np.float32)[:, None]
    top, mid, low = np.array(hexc('#1442B0'), np.float32), np.array(hexc('#2C78DE'), np.float32), np.array(hexc('#8CCBFF'), np.float32)
    a = top[None, None, :] + (mid - top)[None, None, :] * np.clip(t / 0.5, 0, 1)[..., None]
    b = mid[None, None, :] + (low - mid)[None, None, :] * np.clip((t - 0.5) / 0.35, 0, 1)[..., None]
    img = np.where((t < 0.5)[..., None], a, b)
    img = np.broadcast_to(img, (size, size, 3)).copy()
    base = Image.fromarray(img.astype(np.uint8), 'RGB').convert('RGBA')
    # Rays: 18 soft wedges turning from the sun, fading out with distance.
    sx, sy = sun
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    ang = np.arctan2(y - sy, x - sx)
    dist = np.sqrt((x - sx) ** 2 + (y - sy) ** 2) / size
    wedge = (np.sin(ang * 9 + 0.4) > 0.15).astype(np.float32)
    fade = np.clip(1.0 - dist / 0.95, 0, 1) ** 1.3
    rays = np.zeros((size, size, 4), np.float32)
    rays[..., 0:3] = 255
    rays[..., 3] = wedge * fade * 52
    base.alpha_composite(Image.fromarray(rays.astype(np.uint8), 'RGBA'))
    # The sun's glow: the sky pales toward it (a clean light blue, never grey), warm white at its heart.
    base.alpha_composite(radial(size, sx, sy, size * 0.70, (190, 228, 255, 200), (150, 205, 255, 0), 1.1))
    base.alpha_composite(radial(size, sx, sy, size * 0.40, (255, 236, 160, 225), (255, 226, 150, 0), 1.25))
    base.alpha_composite(radial(size, sx, sy, size * 0.20, (255, 252, 232, 250), (255, 240, 190, 0), 1.1))
    return base


def halo(layer, width, alpha=210):
    """A soft white rim round everything drawn on <layer> (outside its ink line), so it stands off the rays."""
    a = layer.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(int(width) * 2 + 1)).filter(ImageFilter.GaussianBlur(width * 0.35))
    rim = Image.new('RGBA', layer.size, (255, 255, 255, 0))
    rim.putalpha(grown.point(lambda v: min(255, v) * alpha // 255))
    rim.alpha_composite(layer)
    return rim


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + (t ** 3) * p3


def ribbon(path, w0, w1):
    """A polygon round a path, tapering from w0 at its start to w1 at its end (a comet's tail)."""
    d = np.gradient(path, axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    w = np.linspace(w0, w1, len(path))[:, None] * (np.sin(np.linspace(0, np.pi / 2, len(path))) ** 0.6)[:, None]
    left, right = path + nrm * w / 2, path - nrm * w / 2
    return [tuple(p) for p in np.concatenate([left, right[::-1]])]


def gradient_fill(size, poly, path, colours):
    """The polygon filled with colours running along the path (from its start to its end)."""
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    a, b = path[0], path[-1]
    v = b - a
    t = np.clip(((x - a[0]) * v[0] + (y - a[1]) * v[1]) / float(v @ v), 0, 1)
    out = np.zeros((size, size, 4), np.float32)
    stops = np.linspace(0, 1, len(colours))
    for c in range(3):
        out[..., c] = np.interp(t, stops, [col[c] for col in colours])
    alpha = np.interp(t, stops, [col[3] if len(col) > 3 else 255 for col in colours])
    out[..., 3] = np.array(mask, np.float32) * alpha / 255
    return Image.fromarray(out.astype(np.uint8), 'RGBA')


def sparkle(d, cx, cy, r, fill, ink=None, iw=0):
    """A four-pointed star."""
    k = 0.28
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * k
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    if ink:
        d.polygon(pts, fill=ink, outline=ink, width=iw)
    d.polygon(pts, fill=fill)


def two(size, cx, cy, height):
    """The logo's "2": Lilita One leaning forward, sunshine gold at the top to the accent orange, a thick ink outline."""
    from PIL import ImageFont
    font = ImageFont.truetype(FONT, int(height * 1.25))
    box = font.getbbox('2')
    w, h = box[2] - box[0], box[3] - box[1]
    pad = int(height * 0.3)
    m = Image.new('L', (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - box[0], pad - box[1]), '2', font=font, fill=255)
    m = m.transform(m.size, Image.AFFINE, (1, 0.16, -0.16 * m.size[1] * 0.5, 0, 1, 0), Image.BICUBIC)   # lean forward
    face = np.zeros((m.size[1], m.size[0], 4), np.float32)
    t = np.linspace(0, 1, m.size[1], dtype=np.float32)[:, None]
    gold, orange = np.array(hexc('#FFDB4D'), np.float32), np.array(hexc('#FA8A2E'), np.float32)
    k = np.clip((t - 0.3) / 0.45, 0, 1)
    face[..., :3] = gold + (orange - gold) * k[..., None]
    face[..., 3] = np.array(m, np.float32)
    face = Image.fromarray(face.astype(np.uint8), 'RGBA')
    ow = max(2, int(height * 0.085))
    edge = m.filter(ImageFilter.MaxFilter(ow * 2 + 1))
    ink = Image.new('RGBA', m.size, (20, 23, 38, 0)); ink.putalpha(edge)
    shadow = Image.new('RGBA', m.size, (8, 14, 40, 0)); shadow.putalpha(edge.filter(ImageFilter.GaussianBlur(ow)).point(lambda v: v * 0.55))
    glyph = Image.new('RGBA', m.size, (0, 0, 0, 0))
    glyph.alpha_composite(shadow, (int(ow * 0.4), int(ow * 0.9)))
    glyph.alpha_composite(ink)
    glyph.alpha_composite(face)
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    layer.alpha_composite(glyph, (int(cx - m.size[0] / 2), int(cy - m.size[1] / 2)))
    return layer


def vignette(size, img, strength=0.16):
    v = radial(size, size / 2, size / 2, size * 0.75, (0, 0, 0, 0), (8, 14, 40, int(255 * strength)), 2.2)
    img.alpha_composite(v)
    return img


def save_rgb(img, path, px):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = img.convert('RGB').resize((px, px), Image.LANCZOS)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=2))   # crisp after the downscale
    out.save(path, optimize=True)
    print('wrote', path, px)


# ------------------------------------------------------------------------------------------------ the walk to school
# app_icon_scene.py's render: Max kicking the ball along the footpath to school, the sky transparent.
scene = json.load(open(os.path.join(layers, 'scene.json')))


def street(size):
    """The morning sky (the sun rising behind the school's clock tower) with the street over it, quietened (a pale
    morning haze, a little less contrast) so Max and the ball stand out, and Max over that with a soft white rim."""
    img = sky(size, (size * 0.52, size * 0.24))
    scene_img = Image.open(os.path.join(layers, 'scene.png')).convert('RGBA').resize((size, size), Image.LANCZOS)
    hero = Image.open(os.path.join(layers, 'hero.png')).convert('RGBA').resize((size, size), Image.LANCZOS)
    a = np.asarray(scene_img, np.float32)
    haze = np.array((214, 230, 246), np.float32)
    lum = a[..., :3].mean(-1, keepdims=True)
    rgb = a[..., :3] * 0.85 + lum * 0.15                      # a little less saturated
    rgb = rgb * 0.88 + haze * 0.12                             # and hazed toward the morning sky
    a[..., :3] = rgb
    img.alpha_composite(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA'))
    img.alpha_composite(halo(hero, size * 0.006, alpha=230))
    return img


def kick(size):
    """The kick: a golden trail from his toe up to the ball, a puff of dust at his toe, sparkles by the ball, and the ball
    over it all."""
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    P = lambda fx, fy: np.array((fx * size, fy * size), np.float32)
    tx, ty = scene['toe']; bx, by = scene['ball']; br = scene['ball_r']
    path = bezier(P(tx + 0.01, ty - 0.01), P(tx + 0.08, ty - 0.12), P(bx + 0.02, by + 0.16), P(bx, by), 200)
    outer = ribbon(path, size * 0.01, size * br * 2.0)
    inner = ribbon(path, size * 0.004, size * br * 1.35)
    core = ribbon(path[70:], size * 0.002, size * br * 0.7)
    ink = Image.new('L', (size, size), 0)
    ImageDraw.Draw(ink).polygon(outer, fill=255)
    ink = ink.filter(ImageFilter.MaxFilter(int(size * 0.006) * 2 + 1))
    edge = Image.new('RGBA', (size, size), NAVY + (0,)); edge.putalpha(ink.point(lambda v: v * 0.85))
    layer.alpha_composite(edge)
    layer.alpha_composite(gradient_fill(size, outer, path, [(250, 120, 40, 0), (250, 125, 40, 255), (255, 170, 50, 255), (255, 200, 70, 255)]))
    layer.alpha_composite(gradient_fill(size, inner, path, [(255, 205, 80, 0), (255, 214, 90, 255), (255, 236, 140, 255)]))
    layer.alpha_composite(gradient_fill(size, core, path[70:], [(255, 250, 225, 0), (255, 252, 236, 255)]))
    d = ImageDraw.Draw(layer)
    # A comic burst where his toe met the ball: gold spikes inked navy, a white heart.
    c = P(tx + 0.02, ty - 0.025)
    for (r0, r1, fill) in ((0.032, 0.060, NAVY + (255,)), (0.025, 0.049, (255, 200, 60, 255)), (0.014, 0.027, (255, 250, 230, 255))):
        pts = []
        for i in range(18):
            ang = math.pi * 2 * i / 18 + 0.15
            rr = (r1 if i % 2 == 0 else r0) * size
            pts.append((c[0] + rr * math.cos(ang), c[1] + rr * 0.8 * math.sin(ang)))
        d.polygon(pts, fill=fill)
    # Pebbles on the footpath (the stones every kid kicked along on the way to school).
    for (fx, fy, rx) in ((0.14, 0.90, 0.020), (0.20, 0.93, 0.013), (0.56, 0.91, 0.016), (0.88, 0.86, 0.012)):
        c = P(fx, fy); w, h = size * rx, size * rx * 0.62
        d.ellipse([c[0] - w - 5, c[1] - h - 5, c[0] + w + 5, c[1] + h + 5], fill=NAVY + (230,))
        d.ellipse([c[0] - w, c[1] - h, c[0] + w, c[1] + h], fill=(150, 142, 132, 255))
        d.ellipse([c[0] - w * 0.6, c[1] - h * 0.75, c[0] + w * 0.25, c[1] - h * 0.05], fill=(205, 198, 186, 255))
    for (fx, fy, r) in ((bx + 0.10, by + 0.02, 0.035), (bx - 0.10, by - 0.05, 0.028), (bx + 0.05, by + 0.13, 0.022)):
        c = P(fx, fy)
        sparkle(d, c[0], c[1], size * r * 1.25, NAVY + (255,))
        sparkle(d, c[0], c[1], size * r, (255, 246, 196, 255))
    ball = Image.open(os.path.join(layers, 'ball_front.png')).convert('RGBA').resize((size, size), Image.LANCZOS)
    layer.alpha_composite(halo(ball, size * 0.006))
    return layer


full = street(N)
full.alpha_composite(kick(N))
full = vignette(N, full, 0.12)
if TWO:
    full.alpha_composite(two(N, N * 0.155, N * 0.14, N * 0.22))

save_rgb(full, os.path.join(root, 'marketing/appstore/icon_1024.png'), 1024)
save_rgb(full, os.path.join(root, 'marketing/googleplay/icon_512.png'), 512)
save_rgb(full, os.path.join(root, 'Assets/_Game/Art/Icon/AppIcon.png'), 1024)

# Android adaptive icon: a launcher shows only the middle 72 of the layer's 108 dp, masked as small as a 66 dp circle. So
# the back layer is the whole picture (without the "2", which a round mask would clip) shrunk into that middle 72/108,
# over a blurred, enlarged copy of itself for the margin; the front layer is left clear.
plain = vignette(N, street(N), 0.10); plain.alpha_composite(kick(N))
inner_px = int(N * 72 / 108)
back = plain.resize((N, N), Image.LANCZOS).filter(ImageFilter.GaussianBlur(N * 0.02))
back.alpha_composite(plain.resize((inner_px, inner_px), Image.LANCZOS), ((N - inner_px) // 2, (N - inner_px) // 2))
save_rgb(back, os.path.join(root, 'Assets/_Game/Art/Icon/AppIconBackground.png'), 1024)
p = os.path.join(root, 'Assets/_Game/Art/Icon/AppIconForeground.png')
Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)).save(p, optimize=True)
print('wrote', p)

if preview:
    os.makedirs(preview, exist_ok=True)
    icon = full.convert('RGB').resize((1024, 1024), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=2))
    icon.save(os.path.join(preview, 'icon_1024.png'))

    def squircle(px, radius=0.2237):
        m = Image.new('L', (px * 4, px * 4), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, px * 4 - 1, px * 4 - 1], radius=int(px * 4 * radius), fill=255)
        return m.resize((px, px), Image.LANCZOS)

    def circle(px):
        m = Image.new('L', (px * 4, px * 4), 0)
        ImageDraw.Draw(m).ellipse([0, 0, px * 4 - 1, px * 4 - 1], fill=255)
        return m.resize((px, px), Image.LANCZOS)

    adaptive = back.convert('RGB')
    sheet = Image.new('RGB', (1500, 760), hexc('#20242C'))
    x = 30
    for px in (300, 180, 120, 80, 58, 40):
        im = icon.resize((px, px), Image.LANCZOS); sheet.paste(im, (x, 40), squircle(px)); x += px + 30
    x = 30
    for px in (300, 180, 120, 80, 58, 40):
        # Android: the adaptive icon's middle 72/108 shown in a circle.
        crop = adaptive.crop((N // 6, N // 6, N - N // 6, N - N // 6)).resize((px, px), Image.LANCZOS)
        sheet.paste(crop, (x, 400), circle(px)); x += px + 30
    sheet.save(os.path.join(preview, 'sheet.png'))
    print('wrote preview sheet')
