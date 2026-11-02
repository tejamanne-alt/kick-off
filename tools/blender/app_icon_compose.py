# Lays out the app icon from app_icon.py's layers (kid.png, ball.png) in the Kick Off 2 logo's language: a morning sky with
# the sun rising behind the kid, the logo's mown green pitch with a chalk line, chalk speed lines with a navy edge, the
# kid running to the right (to school, as in every level) after a big football. Writes every size the stores need:
#   python3 app_icon_compose.py <layers dir> <repo root> [--preview <dir>]
#     marketing/appstore/icon_1024.png               App Store icon: 1024 x 1024, opaque (iOS adds its own corners)
#     marketing/googleplay/icon_512.png              Google Play listing icon: 512 x 512, opaque (Play adds its own mask)
#     Assets/_Game/Art/Icon/AppIcon.png              the game's icon for every platform (BuildScripts), 1024, opaque
#     Assets/_Game/Art/Icon/AppIconBackground.png    Android adaptive icon, back layer: the sky, the sun and the pitch, 1024
#     Assets/_Game/Art/Icon/AppIconForeground.png    Android adaptive icon, front layer: the kid and the ball, his face and
#                                                    the ball inside the middle 66 dp circle every launcher's mask keeps, 1024
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


def kid_layer(size, head_x, top_y, height, lean=0.0):
    """The kid render scaled so the frame is <height> tall, its hair's top at top_y and his head centred on head_x, leaning
    forward (to the right) by <lean> degrees about his hips."""
    k = Image.open(os.path.join(layers, 'kid.png')).convert('RGBA')
    a = np.array(k.split()[3])
    rows = np.where(a.max(axis=1) > 40)[0]
    top = rows[0]
    band = a[top:top + int(k.height * 0.12)]                 # the head: the top 12 % of the frame below the hair's top
    cols = np.where(band.max(axis=0) > 40)[0]
    hx = (cols[0] + cols[-1]) / 2
    s = height / k.height
    k = k.resize((int(k.width * s), int(k.height * s)), Image.LANCZOS)
    if lean:
        # Turn about his hips (60 % down the frame), then put his head back where it was asked for.
        piv = (hx * s, k.height * 0.6)
        r = math.radians(lean)
        hx0, hy0 = hx * s - piv[0], top * s - piv[1]
        hx1 = piv[0] + hx0 * math.cos(r) - hy0 * math.sin(r)
        hy1 = piv[1] + hx0 * math.sin(r) + hy0 * math.cos(r)
        k = k.rotate(-lean, resample=Image.BICUBIC, center=piv)
        hx, top = hx1 / s, hy1 / s
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    layer.alpha_composite(k, (int(head_x - hx * s), int(top_y - top * s)))
    return layer


def halo(layer, width, alpha=210):
    """A soft white rim round everything drawn on <layer> (outside its ink line), so it stands off the rays."""
    a = layer.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(int(width) * 2 + 1)).filter(ImageFilter.GaussianBlur(width * 0.35))
    rim = Image.new('RGBA', layer.size, (255, 255, 255, 0))
    rim.putalpha(grown.point(lambda v: min(255, v) * alpha // 255))
    rim.alpha_composite(layer)
    return rim


def subject(size, scale=1.0, dx=0.0, dy=0.0):
    """The kid, the ball, the speed lines and the ball's shadow, laid out for a full square (scale 1) or smaller and
    moved (the adaptive icon's front layer)."""
    S = size * scale
    ox, oy = size * (1 - scale) / 2 + dx * size, size * (1 - scale) / 2 + dy * size
    P = lambda fx, fy: (ox + fx * S, oy + fy * S)
    layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    # The ball at his feet, ahead of him, close to us: he is dribbling it to school. Its shadow on the grass under it.
    bx, by, bd = 0.735, 0.745, 0.37        # at his feet, clear of his hands; its far edge inside the corner iOS rounds off
    sh = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cx, cy = P(bx + 0.01, 0.945)
    ImageDraw.Draw(sh).ellipse([cx - S * 0.15, cy - S * 0.03, cx + S * 0.15, cy + S * 0.03], fill=(16, 52, 22, 120))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S * 0.012)))
    d = ImageDraw.Draw(layer)
    # Speed lines streaming back from behind him, clear of his arm.
    w = int(S * 0.024)
    for (fx0, fy, ln) in ((0.025, 0.23, 0.12), (0.0, 0.32, 0.16), (0.03, 0.41, 0.10)):
        speed_line(d, P(fx0, fy), P(fx0 + ln, fy - ln * 0.06), w, scale)
    # The kid.
    hx, hy = P(0.40, 0.06)
    layer.alpha_composite(halo(kid_layer(size, hx, hy, S * 1.48, lean=5.0), S * 0.009))
    # The ball, in front of everything.
    layer.alpha_composite(halo(ball_layer(size, *P(bx, by), S * bd), S * 0.008))
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
    sun = (size * 0.37, size * 0.30)
    bg = sky(size, sun)
    bg.alpha_composite(pitch(size, size * 0.79))
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
# The face and the ball fit the 66 dp safe circle (no "2" here: a round mask would clip it, and the launcher writes the
# app's name under its icon anyway).
front = subject(N, 0.60)
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
