# Lays out the app icon from app_icon.py's layer (ball.png) in the Kick Off 2 logo's language, with no characters: a big
# football flying at us out of a morning sunburst, a curving golden kick trail sweeping up behind it with sparkles, over
# the logo's mown green pitch and its chalk lines. Writes every size the stores need:
#   python3 app_icon_compose.py <layers dir> <repo root> [--preview <dir>]
#     marketing/appstore/icon_1024.png               App Store icon: 1024 x 1024, opaque (iOS adds its own corners)
#     marketing/googleplay/icon_512.png              Google Play listing icon: 512 x 512, opaque (Play adds its own mask)
#     Assets/_Game/Art/Icon/AppIcon.png              the game's icon for every platform (BuildScripts), 1024, opaque
#     Assets/_Game/Art/Icon/AppIconBackground.png    Android adaptive icon, back layer: the sky, the sun and the pitch, 1024
#     Assets/_Game/Art/Icon/AppIconForeground.png    Android adaptive icon, front layer: the ball and its trail, the ball
#                                                    inside the middle 66 dp circle every launcher's mask keeps, 1024
# --preview also writes a sheet of the icon masked the way iOS and Android show it, at home-screen and settings sizes;
# --two adds the logo's sunny "2" (read "to": kick off to school) in the top right corner.
import math, os, sys
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


def pitch(size, horizon):
    """The logo's mown pitch: two greens in broad diagonal stripes under a gently curved horizon, a chalk line on it."""
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    top = horizon + ((x - size * 0.5) / size) ** 2 * size * 0.18          # the ground curves away at the sides
    ground = y >= top
    stripe = (np.floor((x * 0.9 + y * 0.45) / (size * 0.085)) % 2) == 0
    g1, g2 = np.array(hexc('#2F9C45'), np.float32), np.array(hexc('#41B656'), np.float32)
    col = np.where(stripe[..., None], g1, g2)
    shade = np.clip((y - top) / (size * 0.3), 0, 1)[..., None]          # a little darker toward us
    col = col * (1 - 0.18 * shade)
    rgba = np.zeros((size, size, 4), np.float32)
    rgba[..., :3] = col; rgba[..., 3] = ground * 255
    layer = Image.fromarray(rgba.astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(layer)
    # The centre circle's near arc, chalked across the grass, and the far edge of the pitch.
    w = int(size * 0.014)
    d.arc([size * -0.25, horizon + size * 0.05, size * 1.25, horizon + size * 0.95], 200, 340, fill=(240, 248, 240, 220), width=w)
    return layer


def speed_line(d, a, b, width, s=1.0):
    """A chalk speed line: white with a navy edge, rounded ends."""
    for col, w in ((NAVY + (255,), width + int(10 * s)), (WHITE + (255,), width)):
        d.line([a, b], fill=col, width=w)
        for p in (a, b):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)


def ball_layer(size, cx, cy, diameter):
    """The ball render clipped to a true circle, with an ink ring round it."""
    b = Image.open(os.path.join(layers, 'ball.png')).convert('RGBA')
    bb = b.getbbox()
    b = b.crop(bb)
    d = int(diameter)
    b = b.resize((d, d), Image.LANCZOS)
    mask = Image.new('L', (d * 4, d * 4), 0)
    ImageDraw.Draw(mask).ellipse([6, 6, d * 4 - 6, d * 4 - 6], fill=255)
    mask = mask.resize((d, d), Image.LANCZOS)
    b.putalpha(Image.fromarray(np.minimum(np.array(b.split()[3]), np.array(mask))))
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    ring = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    rw = diameter * 0.045
    ImageDraw.Draw(ring).ellipse([cx - d / 2 - rw * 0.55, cy - d / 2 - rw * 0.55, cx + d / 2 + rw * 0.55, cy + d / 2 + rw * 0.55], fill=(14, 12, 18, 255))
    layer.alpha_composite(ring)
    layer.alpha_composite(b, (int(cx - d / 2), int(cy - d / 2)))
    return layer


def halo(layer, width, alpha=210):
    """A soft white rim round everything drawn on <layer> (outside its ink line), so it stands off the rays."""
    a = layer.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(int(width) * 2 + 1)).filter(ImageFilter.GaussianBlur(width * 0.35))
    rim = Image.new('RGBA', layer.size, (255, 255, 255, 0))
    rim.putalpha(grown.point(lambda v: min(255, v) * alpha // 255))
    rim.alpha_composite(layer)
    return rim


BALL = (0.53, 0.53, 0.56)                   # the ball's centre (x, y) and diameter, as fractions of the square


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


def subject(size, scale=1.0, dx=0.0, dy=0.0):
    """The ball, its kick trail, the sparkles and its shadow, laid out for a full square (scale 1) or smaller and moved
    (the adaptive icon's front layer)."""
    S = size * scale
    ox, oy = size * (1 - scale) / 2 + dx * size, size * (1 - scale) / 2 + dy * size
    P = lambda fx, fy: np.array((ox + fx * S, oy + fy * S), np.float32)
    bx, by, bd = BALL
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    # Its shadow far below on the grass: the ball is high in the air.
    sh = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    c = P(bx - 0.05, 0.93)
    ImageDraw.Draw(sh).ellipse([c[0] - S * 0.17, c[1] - S * 0.028, c[0] + S * 0.17, c[1] + S * 0.028], fill=(14, 48, 20, 110))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S * 0.014)))
    # The kick trail: from low on the left (where it was struck) curving up into the ball, in the logo's gold to orange
    # with a white-hot core near the ball and a navy ink edge.
    path = bezier(P(-0.10, 1.02), P(0.06, 1.0), P(0.16, 0.66), P(bx - 0.03, by + 0.03), 220)
    outer = ribbon(path, S * 0.05, S * 0.44)
    inner = ribbon(path, S * 0.015, S * 0.31)
    core = ribbon(path[60:], S * 0.005, S * 0.16)
    ink = Image.new('L', (size, size), 0)
    ImageDraw.Draw(ink).polygon(outer, fill=255)
    ink = ink.filter(ImageFilter.MaxFilter(int(S * 0.012) * 2 + 1))
    edge = Image.new('RGBA', (size, size), NAVY + (0,)); edge.putalpha(ink.point(lambda v: v * 0.92))
    layer.alpha_composite(edge)
    layer.alpha_composite(gradient_fill(size, outer, path, [(250, 120, 40, 0), (250, 120, 40, 255), (255, 165, 50, 255), (255, 200, 70, 255)]))
    layer.alpha_composite(gradient_fill(size, inner, path, [(255, 205, 80, 0), (255, 214, 90, 255), (255, 236, 140, 255)]))
    layer.alpha_composite(gradient_fill(size, core, path[60:], [(255, 250, 225, 0), (255, 252, 236, 255)]))
    # Speed streaks along the trail.
    d = ImageDraw.Draw(layer)
    for (a, b, w) in (((0.04, 0.42), (0.16, 0.33), 0.022), ((0.07, 0.53), (0.15, 0.47), 0.018)):
        speed_line(d, tuple(P(*a)), tuple(P(*b)), int(S * w), scale)
    # Sparkles round the ball.
    for (fx, fy, r) in ((0.27, 0.17, 0.05), (0.88, 0.80, 0.045), (0.92, 0.46, 0.03), (0.47, 0.11, 0.025)):
        cx, cy = P(fx, fy)
        sparkle(d, cx, cy, S * r * 1.25, NAVY + (255,))
        sparkle(d, cx, cy, S * r, (255, 246, 196, 255))
    # The ball, in front of everything, with a white rim to stand it off the rays.
    layer.alpha_composite(halo(ball_layer(size, *P(bx, by), S * bd), S * 0.010))
    return layer


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


def background(size):
    sun = (size * BALL[0], size * BALL[1])             # the sunburst behind the ball
    bg = sky(size, sun)
    bg.alpha_composite(pitch(size, size * 0.80))
    return bg


def vignette(size, img, strength=0.16):
    v = radial(size, size / 2, size / 2, size * 0.75, (0, 0, 0, 0), (8, 14, 40, int(255 * strength)), 2.2)
    img.alpha_composite(v)
    return img


def save_rgb(img, path, px):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert('RGB').resize((px, px), Image.LANCZOS).save(path, optimize=True)
    print('wrote', path, px)


full = background(N)
full.alpha_composite(subject(N))
full = vignette(N, full)
if TWO:
    full.alpha_composite(two(N, N * 0.835, N * 0.175, N * 0.25))

save_rgb(full, os.path.join(root, 'marketing/appstore/icon_1024.png'), 1024)
save_rgb(full, os.path.join(root, 'marketing/googleplay/icon_512.png'), 512)
save_rgb(full, os.path.join(root, 'Assets/_Game/Art/Icon/AppIcon.png'), 1024)

# Android adaptive icon: the back layer full bleed; the front layer is the subject shrunk into the middle 66 % (a launcher
# may crop the 108 dp layer to its middle 72 dp and mask it to a circle as small as 66 dp across).
back = vignette(N, background(N), 0.10)
save_rgb(back, os.path.join(root, 'Assets/_Game/Art/Icon/AppIconBackground.png'), 1024)
# The ball (centred) and most of its trail fit the 66 dp safe circle (no "2" here: a round mask would clip it, and the launcher writes the
# app's name under its icon anyway).
front = subject(N, 0.62, dx=-(BALL[0] - 0.5) * 0.62, dy=-(BALL[1] - 0.5) * 0.62)
p = os.path.join(root, 'Assets/_Game/Art/Icon/AppIconForeground.png')
front.resize((1024, 1024), Image.LANCZOS).save(p, optimize=True)
print('wrote', p)

if preview:
    os.makedirs(preview, exist_ok=True)
    icon = full.convert('RGB').resize((1024, 1024), Image.LANCZOS)
    icon.save(os.path.join(preview, 'icon_1024.png'))

    def squircle(px, radius=0.2237):
        m = Image.new('L', (px * 4, px * 4), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, px * 4 - 1, px * 4 - 1], radius=int(px * 4 * radius), fill=255)
        return m.resize((px, px), Image.LANCZOS)

    def circle(px):
        m = Image.new('L', (px * 4, px * 4), 0)
        ImageDraw.Draw(m).ellipse([0, 0, px * 4 - 1, px * 4 - 1], fill=255)
        return m.resize((px, px), Image.LANCZOS)

    adaptive = background(N); adaptive = vignette(N, adaptive, 0.10); adaptive.alpha_composite(front)
    adaptive = adaptive.convert('RGB')
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
