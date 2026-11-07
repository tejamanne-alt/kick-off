import sys, math
sys.path.insert(0, '.')
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from comic2 import comic

OUT = '/home/user/kick-off/review/v2'
BANG = 'fonts/Bangers.ttf'
ANTON = 'fonts/Anton.ttf'
INK = (22, 14, 40)
PAPER = (244, 236, 218)
YEL = (255, 214, 58)

hdr = Image.open('/home/user/kick-off/marketing/appstore/header_3840x1646.jpg')
srch = Image.open('/home/user/kick-off/marketing/appstore/search_results_3840x2560.jpg')


def fit(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


street_src = fit(hdr.crop((1216, 0, 3840, 1646)), 1920)
kick_src = fit(srch.crop((1650, 330, 3840, 2560)), 1920)
street = comic(street_src)
kick = comic(kick_src)
street.save(OUT + '/_street.png'); kick.save(OUT + '/_kick.png')


def cover(im, box_w, box_h, crop):
    return im.crop(crop).resize((box_w, box_h), Image.LANCZOS)


def font(p, s):
    return ImageFont.truetype(p, s)


def pop(canvas, text, xy, size, angle=-8, top=(255, 236, 80), bot=(246, 104, 36), dots=(214, 40, 30)):
    """Comic sound-effect lettering: gradient fill, halftone in the lower half, thick ink
    stroke, a hard offset shadow, set at an angle."""
    f = font(BANG, size)
    sw = max(6, size // 11)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    W, H = r - l + sw * 4, b - t + sw * 4
    o = (sw * 2 - l, sw * 2 - t)
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).text(o, text, font=f, fill=255)
    stroke = Image.new('L', (W, H), 0)
    ImageDraw.Draw(stroke).text(o, text, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.clip((yy - H * 0.2) / (H * 0.6), 0, 1)[..., None]
    fill = np.array(top) * (1 - g) + np.array(bot) * g
    per = max(5, size / 14)
    u, v = (xx + yy) / per, (xx - yy) / per
    d = np.hypot(u - np.round(u), v - np.round(v))
    cov = np.clip((yy / H - 0.45) * 1.4, 0, 0.9)
    m = np.clip((np.sqrt(cov) * 0.6 - d) * per + 0.5, 0, 1)[..., None]
    fill = fill * (1 - m) + np.array(dots) * m
    layer = Image.new('RGBA', (W + sw * 2, H + sw * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', (W, H), INK + (255,))
    layer.paste(sh, (sw * 2, sw * 2), stroke)                    # offset shadow
    layer.paste(Image.new('RGBA', (W, H), INK + (255,)), (0, 0), stroke)
    layer.paste(Image.fromarray(fill.astype(np.uint8)).convert('RGBA'), (0, 0), mask)
    layer = layer.rotate(-angle, resample=Image.BICUBIC, expand=True)
    x, y = xy
    canvas.alpha_composite(layer, (int(x - layer.width / 2), int(y - layer.height / 2)))


def burst(canvas, c, r_in, r_out, n=14, fill=YEL, seed=1, inner=(255, 248, 210)):
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n + rng.uniform(-0.1, 0.1)
        r = (r_out * rng.uniform(0.75, 1.15)) if i % 2 == 0 else r_in * rng.uniform(0.8, 1.05)
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    d = ImageDraw.Draw(canvas)
    for k in range(18):                                         # rays
        a = rng.uniform(0, 2 * math.pi); r0, r1 = r_out * 0.9, r_out * rng.uniform(1.4, 2.1)
        d.line([(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)), (c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a))],
               fill=(255, 200, 60, 255) if k % 3 else (255, 250, 230, 255), width=int(rng.uniform(2, 5)))
    d.polygon(pts, fill=fill + (255,), outline=INK + (255,), width=6)
    small = [(c[0] + (x - c[0]) * 0.55, c[1] + (y - c[1]) * 0.55) for x, y in pts]
    d.polygon(small, fill=inner + (255,))


def speed_lines(canvas, box, n=26, direction=-1, seed=2, col=INK, alpha=200):
    """Horizontal motion streaks (the game scrolls sideways) trailing behind the action."""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(canvas)
    for _ in range(n):
        y = rng.uniform(y0, y1); L = rng.uniform(0.25, 0.7) * (x1 - x0)
        xs = rng.uniform(x0, x1 - L)
        w = rng.uniform(1.5, 4.5)
        d.polygon([(xs, y), (xs + L, y - w / 2), (xs + L, y + w / 2)] if direction < 0 else
                  [(xs, y - w / 2), (xs, y + w / 2), (xs + L, y)], fill=col + (alpha,))


def label(canvas, text, xy, size=46, bg=YEL, fg=INK, skew=True):
    f = font(ANTON, size)
    l, t, r, b = f.getbbox(text)
    pad = size // 4
    W, H = r - l + pad * 2, b - t + pad * 2
    lay = Image.new('RGBA', (W + 12, H + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([8, 8, W + 8, H + 8], fill=INK + (255,))
    d.rectangle([0, 0, W, H], fill=bg + (255,), outline=INK + (255,), width=4)
    d.text((pad - l, pad - t), text, font=f, fill=fg)
    if skew:
        lay = lay.transform(lay.size, Image.AFFINE, (1, 0.12, -6, 0, 1, 0), resample=Image.BICUBIC)
    canvas.alpha_composite(lay, xy)


def panel_frame(canvas, box, width=7):
    ImageDraw.Draw(canvas).rectangle(box, outline=INK + (255,), width=width)


# 1. Stages strip ---------------------------------------------------------------------------
crop = (560, 180, 1460, 1020)
stages = comic(street_src.crop(crop), stages=True)
names = ['1  FLAT COLOUR', '2  LIGHT AS DOTS', '3  INK LINE', '4  SLIP + PAPER']
pw = 720; ph = round(pw * (crop[3] - crop[1]) / (crop[2] - crop[0])); g = 22
sheet = Image.new('RGBA', (g + 4 * (pw + g), ph + 2 * g), PAPER + (255,))
for i, (s, n) in enumerate(zip(stages, names)):
    x = g + i * (pw + g)
    sheet.paste(s.resize((pw, ph), Image.LANCZOS), (x, g))
    panel_frame(sheet, (x, g, x + pw, g + ph))
    label(sheet, n, (x + 16, g + 16), 38, bg=PAPER, skew=False)
sheet.convert('RGB').save(OUT + '/1_stages.jpg', quality=90)

# 2. Before / after --------------------------------------------------------------------------
w = 960
a, b = fit(street_src, w), fit(street, w)
ba = Image.new('RGBA', (w * 2 + g * 3, a.height + g * 2), PAPER + (255,))
for i, (im, n) in enumerate([(a, 'ORIGINAL'), (b, 'COMIC FILTER')]):
    x = g + i * (w + g)
    ba.paste(im, (x, g)); panel_frame(ba, (x, g, x + w, g + a.height))
    label(ba, n, (x + 16, g + 16), 40, bg=YEL if i else PAPER, skew=False)
ba.convert('RGB').save(OUT + '/2_before_after.jpg', quality=90)

# 3. In-game frame with a comic HUD, in a phone ----------------------------------------------
game = kick.crop((0, 120, 1920, 120 + 1080)).convert('RGBA')
speed_lines(game, (0, 650, 330, 900), n=14, seed=5, col=(255, 248, 230), alpha=230)
pop(game, 'NICE TOUCH!', (560, 300), 150, angle=-10)
label(game, 'L01  OUT THE DOOR', (40, 36), 50)
label(game, 'HOME  »  BUS STOP', (60, 128), 30, bg=(80, 200, 214))
d = ImageDraw.Draw(game)
# coins + bell timer
label(game, '    128', (1530, 36), 50, bg=PAPER)
d.ellipse([1548, 56, 1600, 108], fill=YEL, outline=INK, width=5)
d.ellipse([1562, 70, 1586, 94], outline=INK, width=4)
label(game, 'BELL 0:42', (1590, 132), 30, bg=(240, 90, 120), fg=(255, 250, 240))
# stick and buttons
d.ellipse([70, 800, 290, 1020], outline=(255, 250, 240), width=6)
d.ellipse([140, 870, 220, 950], fill=(255, 250, 240, 160), outline=INK, width=4)
d.ellipse([1560, 760, 1840, 1040], fill=YEL, outline=INK, width=8)
f = font(ANTON, 72); d.text((1700, 900), 'KICK', font=f, fill=INK, anchor='mm')
d.ellipse([1360, 880, 1530, 1050], fill=(120, 100, 200), outline=INK, width=6)
d.text((1445, 965), 'JUMP', font=font(ANTON, 40), fill=(255, 250, 240), anchor='mm')
# streak bar
d.polygon([(620, 990), (1300, 990), (1285, 1040), (605, 1040)], fill=INK)
d.polygon([(626, 996), (1060, 996), (1048, 1034), (612, 1034)], fill=(246, 104, 36))
d.polygon([(1060, 996), (1294, 996), (1282, 1034), (1048, 1034)], fill=PAPER)
d.text((620, 950), 'STREAK x3', font=font(ANTON, 34), fill=(255, 250, 240), stroke_width=4, stroke_fill=INK)
phone = Image.new('RGBA', (2140, 1300), PAPER + (255,))
pd = ImageDraw.Draw(phone)
pd.rounded_rectangle([40, 40, 2120, 1280], radius=110, fill=(240, 80, 130))
pd.rounded_rectangle([22, 22, 2100, 1262], radius=110, fill=(80, 200, 214))
pd.rounded_rectangle([30, 30, 2110, 1270], radius=110, fill=INK)
mask = Image.new('L', game.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 1919, 1079], radius=70, fill=255)
phone.paste(game, (110, 110), mask)
phone.convert('RGB').save(OUT + '/3_hud_mock.jpg', quality=90)

# 4. The big moment: a volley ------------------------------------------------------------------
mom = kick.copy().convert('RGBA')
bx, by = 415, 870                                              # the ball, in this crop
lay = Image.new('RGBA', mom.size, (0, 0, 0, 0))
burst(lay, (bx + 175, by + 30), 50, 140, n=12, seed=4)
mom = Image.alpha_composite(mom, lay)
speed_lines(mom, (0, 790, 260, 960), n=16, seed=9, col=(255, 248, 230), alpha=230)
pop(mom, 'THWACK!', (560, 560), 220, angle=-11)
mom.convert('RGB').save(OUT + '/4_thwack.jpg', quality=90)

# 5. A comic page: the level's end as three panels ----------------------------------------------
page = Image.new('RGBA', (2400, 1500), PAPER + (255,))
G = 30
pA = (G, G, 1000, 720); pB = (G, 750, 1000, 1500 - G); pC = (1030, G, 2400 - G, 1500 - G)
sA = cover(kick, pA[2] - pA[0], pA[3] - pA[1], (150, 380, 1150, 1091))
sB = cover(street, pB[2] - pB[0], pB[3] - pB[1], (0, 230, 1920, 1205))
cw, ch = pC[2] - pC[0], pC[3] - pC[1]
sC = cover(kick, cw, ch, (430, 0, 1890, 1570))
for s, p in [(sA, pA), (sB, pB), (sC, pC)]:
    page.paste(s, p[:2])
pop(page, 'BOINK!', (560, 130), 140, angle=-12, top=(255, 250, 220), bot=(110, 210, 230), dots=(40, 120, 200))
pop(page, 'TAP  TAP', (300, 860), 100, angle=-6)
pop(page, 'MADE IT!', (1880, 220), 210, angle=-8)
label(page, 'NEXT STOP: THE BUS STOP', (1070, 1340), 54, bg=PAPER)
for p in (pA, pB, pC):
    panel_frame(page, p, 8)
page.convert('RGB').save(OUT + '/5_comic_page.jpg', quality=90)
print('done')
