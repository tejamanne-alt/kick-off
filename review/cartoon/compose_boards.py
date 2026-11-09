"""Composes the classic cartoon filter's review boards (classic_port.py: inked cels over painted backgrounds, the look
of the classic Road Runner shorts the review asked for) from render_scenes.py's renders and the game's own UI pictures:
  python3 -I compose_boards.py <render dir> <out dir>
  1_levels.jpg        every chapter and the California add-on, the game today beside the filter
  2_characters.jpg    the six kids, a passer-by and the animals close up, and every kid's face at 2x
  3_ui_art.jpg        the pictures the menus draw: player cards, bags, all 23 stickers, the logo, the town map
  4_screens.jpg       the title screen and the Add-ons & Filters panel with the filter on (mock-ups)
  frames/<scene>.jpg  each scene at full size, the game today above the filter"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cartoon_port as cp
import classic_port as cl
import shader_port as sp

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)
GAME = os.path.join(HERE, '..', '..', 'Assets', '_Game')
UI = os.path.join(GAME, 'Resources', 'UI')
FONTS = os.path.join(GAME, 'Resources', 'Fonts')
BG = (22, 24, 38)
YELLOW = (255, 214, 80)
SOFT = (196, 202, 222)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


TITLE = lambda s: font('LilitaOne-Regular.ttf', s)
BODY = lambda s: font('VarelaRound-Regular.ttf', s)

FRAMES = {}


def frames(scene):
    if scene not in FRAMES:
        colour, alpha, depth01, nrm = cp.load_scene(SRC, scene)
        FRAMES[scene] = (cp.to_img(sp.plain(colour)), cp.to_img(cl.classic_pass(colour, alpha, depth01, nrm)), alpha, depth01)
    return FRAMES[scene]


def tag(im, text, colour=YELLOW, size=34):
    im = im.copy(); d = ImageDraw.Draw(im); f = TITLE(size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([14, 14, 14 + w + 28, 14 + size + 20], radius=10, fill=(20, 18, 36))
    d.text((28, 22), text, font=f, fill=colour)
    return im


def header(width, title, line, height=150):
    h = Image.new('RGB', (width, height), BG); d = ImageDraw.Draw(h)
    d.text((40, 26), title, font=TITLE(64), fill=YELLOW)
    d.text((42, 100), line, font=BODY(30), fill=SOFT)
    return h


def stack(parts, width, gap=0):
    hgt = sum(p.height for p in parts) + gap * (len(parts) - 1)
    out = Image.new('RGB', (width, hgt), BG); y = 0
    for p in parts:
        out.paste(p, ((width - p.width) // 2, y)); y += p.height + gap
    return out


# ------------------------------------------------------------------ 1. the levels
LEVELS = [
    ('home', 'Chapter 1 · Home Street', 'Leo, the block walls and houses, a utility pole, a bicycle, the post box, a cat, coins'),
    ('market', 'Chapter 2 · Market & Crossings', 'Mia, a passer-by, the shops and stall, crates, pigeons, the crossing light'),
    ('beach', 'Chapter 3 · The Beach', 'Zoe mid-jump, gulls, a crab, the lifeguard tower, parasol, sandcastle, palms, the sea'),
    ('site', 'Chapter 4 · Underpass & Building Site', 'Kai, a builder, the digger, mixer, scaffold, pipe, cones, barrier, the crane'),
    ('park', 'Chapter 5 · Park & School', 'Hana, the dog, swings, the duck pond, trees, the school and its arch'),
    ('california', 'Add-on · California, Santa Monica', 'Max, stucco villas, palms, a picket fence, a 4x4'),
]
TW, TH, GAP = 1200, 675, 24
W = TW * 2 + GAP * 3
rows = [header(W, 'CLASSIC CARTOON · every level', 'Left: the game today.  Right: inked cels on painted backgrounds, as in the Road Runner samples.  The game’s own models and camera.')]
for scene, title, line in LEVELS:
    o, c, _, _ = frames(scene)
    row = Image.new('RGB', (W, 92 + TH + GAP), BG); d = ImageDraw.Draw(row)
    d.text((GAP, 14), title, font=TITLE(44), fill=(255, 255, 255))
    d.text((GAP + d.textlength(title, font=TITLE(44)) + 24, 30), line, font=BODY(26), fill=SOFT)
    row.paste(tag(o.resize((TW, TH), Image.LANCZOS), 'TODAY', SOFT, 28), (GAP, 80))
    row.paste(tag(c.resize((TW, TH), Image.LANCZOS), 'CLASSIC CARTOON', YELLOW, 28), (GAP * 2 + TW, 80))
    rows.append(row)
    full = Image.new('RGB', (o.width, o.height * 2 + 16), BG)
    full.paste(tag(o, 'TODAY', SOFT), (0, 0)); full.paste(tag(c, 'CLASSIC CARTOON', YELLOW), (0, o.height + 16))
    full.save(os.path.join(OUT, 'frames', '%s.jpg' % scene), quality=88)
stack(rows, W).save(os.path.join(OUT, '1_levels.jpg'), quality=88)
print('1_levels')


# ------------------------------------------------------------------ 2. the characters
def heads(alpha, depth01, min_height=300):
    """The figures' heads (the figure mask's tall blobs): their crowns' x and y."""
    fig = (alpha < 0.5) & (depth01 < 0.999)
    cols = fig.any(0)
    xs = np.nonzero(cols)[0]
    groups, start = [], None
    for i, x in enumerate(xs):
        if start is None:
            start = x
        if i == len(xs) - 1 or xs[i + 1] - x > 12:
            groups.append((start, x)); start = None
    out = []
    for a, b in groups:
        sub = fig[:, a:b + 1]
        ys = np.nonzero(sub.any(1))[0]
        if ys[-1] - ys[0] < min_height:
            continue
        top = ys[0]
        band = sub[top:top + 60]
        cx = a + int(np.nonzero(band.any(0))[0].mean())
        out.append((cx, top, ys[-1] - ys[0]))
    return out


W2 = TW * 2 + GAP * 3
rows = [header(W2, 'CLASSIC CARTOON · the characters', 'The six kids, a passer-by, the dog, the cat, a gull and the ball as cels: flat tones and a bold warm-black outline; painted eyes kept as drawn.')]
names = {'cast_a': ['Hana', 'Max', 'Kai'], 'cast_b': ['Mia', 'Leo', 'Zoe', 'Passer-by']}
crops = []
for scene in ('cast_a', 'cast_b'):
    o, c, alpha, depth01 = frames(scene)
    row = Image.new('RGB', (W2, TH + GAP), BG)
    row.paste(tag(o.resize((TW, TH), Image.LANCZOS), 'TODAY', SOFT, 28), (GAP, 0))
    row.paste(tag(c.resize((TW, TH), Image.LANCZOS), 'CLASSIC CARTOON', YELLOW, 28), (GAP * 2 + TW, 0))
    rows.append(row)
    for (cx, top, hgt), name in zip(heads(alpha, depth01), names[scene]):
        s = int(hgt * 0.36)
        box = (cx - s // 2, max(0, top - s // 8), cx + s // 2, max(0, top - s // 8) + s)
        crops.append((name, o.crop(box), c.crop(box)))
FS = 268
face_rows = []
for i in range(0, len(crops), 4):
    row = Image.new('RGB', (W2, 60 + FS + GAP), BG); d = ImageDraw.Draw(row)
    for j, (name, a, b) in enumerate(crops[i:i + 4]):
        x = GAP + j * (FS * 2 + 12 + GAP + 22)
        d.text((x, 10), name, font=TITLE(36), fill=(255, 255, 255))
        d.text((x + d.textlength(name, font=TITLE(36)) + 14, 22), 'today  |  classic cartoon', font=BODY(22), fill=SOFT)
        row.paste(a.resize((FS, FS), Image.LANCZOS), (x, 60)); row.paste(b.resize((FS, FS), Image.LANCZOS), (x + FS + 12, 60))
    face_rows.append(row)
rows += face_rows
stack(rows, W2).save(os.path.join(OUT, '2_characters.jpg'), quality=88)
print('2_characters')


# ------------------------------------------------------------------ 3. the UI's pictures
def rgba(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(np.float64) / 255.0


def on(bg, a, size):
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')
    im.thumbnail((size, size), Image.LANCZOS)
    t = Image.new('RGBA', (size, size), bg + (255,))
    t.alpha_composite(im, ((size - im.width) // 2, (size - im.height) // 2))
    return t.convert('RGB')


CARD_BG = (236, 240, 248)
W3 = 2460
parts = [header(W3, 'CLASSIC CARTOON · the menus’ pictures', 'Kids, bags, stickers and the logo as inked cels; the town map painted like the scenery. Text stays crisp.')]


def section(title, line):
    s = Image.new('RGB', (W3, 80), BG); d = ImageDraw.Draw(s)
    d.text((GAP, 14), title, font=TITLE(44), fill=(255, 255, 255))
    d.text((GAP + d.textlength(title, font=TITLE(44)) + 24, 30), line, font=BODY(26), fill=SOFT)
    return s


# player cards
cards = ['PlayerGirl', 'PlayerBackpackBoy', 'PlayerPrimaryBoy', 'PlayerPrimaryGirl', 'PlayerPrimaryBoy2', 'PlayerPrimaryGirl2']
parts.append(section('Player cards', 'the picker and the title screen’s player button  (top: today, bottom: classic cartoon)'))
CS = 380
for k, label in ((0, 'TODAY'), (1, 'CLASSIC CARTOON')):
    row = Image.new('RGB', (W3, CS + GAP), BG)
    for i, n in enumerate(cards):
        a = rgba(os.path.join(UI, n + '.png'))
        if k:
            a = cl.classic_2d(a, outline_px=3)
        row.paste(on(CARD_BG, a, CS), (GAP + i * (CS + 26), 0))
    parts.append(row)
# bags and logo
parts.append(section('Locker Room bags  ·  the logo', 'today, then classic cartoon'))
bags = ['bag_kickoff', 'bag_racecar', 'bag_unicorn', 'bag_denimbow', 'bag_goldentrail']
BS = 220
row = Image.new('RGB', (W3, BS * 2 + GAP * 2), BG)
for i, n in enumerate(bags):
    a = rgba(os.path.join(UI, n + '.png'))
    row.paste(on(CARD_BG, a, BS), (GAP + i * (BS + 14), 0))
    row.paste(on(CARD_BG, cl.classic_2d(a, outline_px=3), BS), (GAP + i * (BS + 14), BS + 14))
logo = rgba(os.path.join(UI, 'KickOffLogo.png'))
LW = 2460 - (GAP + 5 * (BS + 14) + 40) - GAP
for k in (0, 1):
    a = cl.classic_2d(logo) if k else logo
    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'RGBA'); im.thumbnail((LW, BS), Image.LANCZOS)
    t = Image.new('RGBA', (LW, BS), (52, 104, 182, 255)); t.alpha_composite(im, ((LW - im.width) // 2, (BS - im.height) // 2))
    row.paste(t.convert('RGB'), (GAP + 5 * (BS + 14) + 40, k * (BS + 14)))
parts.append(row)
# stickers: all 23
parts.append(section('Sticker album', 'all 23 stickers  (left: today, right: classic cartoon)'))
SS = 186
grid = Image.new('RGB', (W3, 4 * (SS + 10) + GAP), BG)
for i in range(23):
    a = rgba(os.path.join(UI, 'Stickers', 'L%02d.png' % (i + 1)))
    r, ccol = divmod(i, 6)
    grid.paste(on(CARD_BG, a, SS), (GAP + ccol * (SS + 10), r * (SS + 10)))
    grid.paste(on(CARD_BG, cl.classic_2d(a, outline_px=3), SS), (W3 // 2 + GAP // 2 + ccol * (SS + 10), r * (SS + 10)))
parts.append(grid)
# the town map
parts.append(section('Town map', 'a stretch of the map screen at its full size  (left: today, right: classic cartoon)'))
m = rgba(os.path.join(UI, 'TownMap.jpg'))[560:1160, 900:2000]
mm = np.dstack([m[..., :3], np.ones(m.shape[:2])])
mc = cl.classic_2d(mm, painted=True, flatten=1.5)
MW = (W3 - GAP * 3) // 2
row = Image.new('RGB', (W3, int(MW * 600 / 1100) + GAP), BG)
row.paste(cp.to_img(m[..., :3]).resize((MW, int(MW * 600 / 1100)), Image.LANCZOS), (GAP, 0))
row.paste(cp.to_img(mc[..., :3]).resize((MW, int(MW * 600 / 1100)), Image.LANCZOS), (GAP * 2 + MW, 0))
parts.append(row)
stack(parts, W3).save(os.path.join(OUT, '3_ui_art.jpg'), quality=88)
print('3_ui_art')


# ------------------------------------------------------------------ 4. screens (mock-ups)
def button(d, box, colour, label, size, cartoon, ink=(255, 255, 255), radius=26):
    x0, y0, x1, y1 = box
    base = tuple(int(c * 0.72) for c in colour)
    if cartoon:   # an ink edge and a hard shadow, as a cartoon's
        d.rounded_rectangle([x0 + 6, y0 + 10, x1 + 6, y1 + 10], radius=radius, fill=(18, 14, 34))
        d.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], radius=radius + 4, fill=(18, 14, 34))
        d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=base)
        d.rounded_rectangle([x0, y0, x1, y1 - 8], radius=radius, fill=colour)
        d.rounded_rectangle([x0 + 14, y0 + 8, x1 - 14, y0 + (y1 - y0) * 0.36], radius=radius // 2, fill=tuple(min(255, int(c + (255 - c) * 0.35)) for c in colour))
    else:
        d.rounded_rectangle([x0, y0 + 8, x1, y1 + 8], radius=radius, fill=(40, 50, 90))
        d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=base)
        d.rounded_rectangle([x0, y0, x1, y1 - 7], radius=radius, fill=colour)
    f = TITLE(size)
    lines = label.split('\n')
    lh = size * 1.0
    ty = (y0 + y1 - 8) / 2 - lh * len(lines) / 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((x0 + x1) / 2 - w / 2 + 2, ty + 3), ln, font=f, fill=(0, 0, 0, 90) if not cartoon else (18, 14, 34))
        d.text(((x0 + x1) / 2 - w / 2, ty), ln, font=f, fill=ink)
        ty += lh


def rgb255(c):
    return tuple(int(round(v * 255)) for v in c)


ACCENT, BLUE, GREEN = rgb255((0.98, 0.54, 0.18)), rgb255((0.2, 0.47, 0.86)), rgb255((0.27, 0.7, 0.42))
HOLIDAY, COOP, ADDON = rgb255((0.16, 0.72, 0.82)), rgb255((0.55, 0.38, 0.88)), rgb255((0.95, 0.55, 0.25))
PAPER, INK, NAVY = (251, 252, 255), rgb255((0.11, 0.13, 0.2)), rgb255((0.14, 0.2, 0.4))


def title_screen(cartoon):
    o, c, _, _ = frames('menu')
    im = (c if cartoon else o).convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    col = 740
    lg = cl.classic_2d(logo) if cartoon else logo
    li = Image.fromarray((lg * 255 + 0.5).astype(np.uint8), 'RGBA'); li = li.resize((640, int(640 * li.height / li.width)), Image.LANCZOS)
    ov.alpha_composite(li, (col // 2 + 20 - li.width // 2, 300 - li.height // 2))
    button(d, (col // 2 + 20 - 225, 604 - 68, col // 2 + 20 + 225, 604 + 68), ACCENT, 'PLAY', 68, cartoon)
    button(d, (col // 2 + 20 - 172 - 165, 744 - 56, col // 2 + 20 - 172 + 165, 744 + 56), HOLIDAY, 'HOLIDAY RUN', 42, cartoon)
    button(d, (col // 2 + 20 + 172 - 165, 744 - 56, col // 2 + 20 + 172 + 165, 744 + 56), COOP, 'CO-OP', 42, cartoon)
    w, gap = 176, 12
    x0 = 20 + (col - (w * 4 + gap * 3)) // 2
    for i, (lab, colr, sz) in enumerate([('Locker Room', BLUE, 30), ('Stickers', BLUE, 32), ('Add-ons\n& Filters', ADDON, 28), ('Settings', BLUE, 32)]):
        button(d, (x0 + i * (w + gap), 880 - 44, x0 + i * (w + gap) + w, 880 + 44), colr, lab, sz, cartoon, radius=20)
    button(d, (40, 1080 - 44 - 74, 240, 1080 - 44), PAPER, 'Credits', 30, cartoon, ink=INK, radius=20)
    # the player button (bottom right) with the kid's card
    bx1, by1 = 1920 - 40, 1080 - 44
    button(d, (bx1 - 330, by1 - 104, bx1, by1), PAPER, '', 30, cartoon, radius=24)
    card = rgba(os.path.join(UI, 'PlayerPrimaryBoy2.png'))
    if cartoon:
        card = cl.classic_2d(card, outline_px=3)
    ci = Image.fromarray((card * 255 + 0.5).astype(np.uint8), 'RGBA').resize((84, 84), Image.LANCZOS)
    d.ellipse([bx1 - 330 + 12, by1 - 52 - 42, bx1 - 330 + 96, by1 - 52 + 42], fill=(214, 226, 246))
    ov.alpha_composite(ci, (bx1 - 330 + 12, by1 - 52 - 42 - 4))
    d.text((bx1 - 330 + 112, by1 - 84), 'Leo', font=TITLE(38), fill=INK)
    d.text((bx1 - 330 + 112, by1 - 40), 'Tap to change', font=BODY(24), fill=(90, 96, 120))
    im.alpha_composite(ov)
    return im.convert('RGB')


def addons_panel():
    _, c, _, _ = frames('menu')
    im = c.convert('RGBA')
    im.alpha_composite(Image.new('RGBA', im.size, (10, 18, 46, 128)))
    d = ImageDraw.Draw(im)
    cw, ch = 1340, 960
    x0, y0 = (1920 - cw) // 2, (1080 - ch) // 2
    d.rounded_rectangle([x0 + 6, y0 + 12, x0 + cw + 6, y0 + ch + 12], radius=40, fill=(18, 14, 34))
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=40, fill=PAPER, outline=(18, 14, 34), width=4)
    # the header ribbon
    d.rounded_rectangle([x0 + cw // 2 - 320, y0 - 34, x0 + cw // 2 + 320, y0 + 50], radius=24, fill=NAVY, outline=(18, 14, 34), width=4)
    t = 'Add-ons & Filters'; f = TITLE(52)
    d.text((x0 + cw / 2 - d.textlength(t, font=f) / 2, y0 - 28), t, font=f, fill=(255, 255, 255))
    pad, cardh, gap = 40, 132, 16
    cwid = (cw - pad * 2 - gap) // 2
    y = y0 + 80
    d.text((x0 + pad, y), 'Add-ons', font=TITLE(36), fill=INK); y += 52
    addons = [('Original', 'Kamakura, Japan', 'Selected', True, True), ('California', 'Santa Monica, USA', 'Tap to choose', False, True),
              ('India', 'Mumbai', 'Coming soon', False, False), ('Tokyo', 'Japan', 'Coming soon', False, False)]
    filters = [('Original', 'The game’s own look', 'Tap to choose', False, True), ('Comic halftone', 'Ink lines, halftone dots, printed paper', 'Tap to choose', False, True),
               ('Pencil sketch', 'Pencil lines and hatching on paper', 'Tap to choose', False, True), ('Classic cartoon', 'Inked characters, painted scenery', 'Selected', True, True)]

    def card(i, entry, ytop):
        name, line, status, chosen, open_ = entry
        cx = x0 + pad + (i % 2) * (cwid + gap); cy = ytop + (i // 2) * (cardh + gap)
        face = rgb255((0.2, 0.47, 0.86)) if chosen else (250, 251, 255) if open_ else rgb255((0.86, 0.89, 0.94))
        ink = (255, 255, 255) if chosen else INK if open_ else (120, 126, 146)
        d.rounded_rectangle([cx + 4, cy + 8, cx + cwid + 4, cy + cardh + 8], radius=22, fill=(18, 14, 34))
        d.rounded_rectangle([cx, cy, cx + cwid, cy + cardh], radius=22, fill=face, outline=(18, 14, 34), width=3)
        d.text((cx + 24, cy + 14), name, font=TITLE(38), fill=ink)
        d.text((cx + 24, cy + 60), line, font=BODY(26), fill=ink)
        d.text((cx + 24, cy + 96), status, font=TITLE(24), fill=(255, 255, 255) if chosen else NAVY if open_ else (120, 126, 146))
    for i, e in enumerate(addons):
        card(i, e, y)
    y += 2 * (cardh + gap) + 6
    d.text((x0 + pad, y), 'Filters', font=TITLE(36), fill=INK)
    t = 'More filters coming soon'; d.text((x0 + cw - pad - d.textlength(t, font=BODY(26)), y + 8), t, font=BODY(26), fill=(110, 116, 136))
    y += 52
    for i, e in enumerate(filters):
        card(i, e, y)
    d.text((x0 + pad, y0 + ch - 92), 'An add-on applies from the next level you play,', font=BODY(26), fill=(110, 116, 136))
    d.text((x0 + pad, y0 + ch - 60), 'a filter at once. Each country has its own music.', font=BODY(26), fill=(110, 116, 136))
    button(d, (x0 + cw - pad - 260, y0 + ch - 104, x0 + cw - pad, y0 + ch - 24), GREEN, 'Done', 40, True, radius=22)
    return im.convert('RGB')


W4 = TW * 2 + GAP * 3
p = [header(W4, 'CLASSIC CARTOON · menus (mock-ups)', 'The menu’s live street goes through the filter like a level; buttons take an ink edge and a hard shadow; the logo and player card are inked cels.')]
row = Image.new('RGB', (W4, 70 + TH + GAP), BG); d = ImageDraw.Draw(row)
d.text((GAP, 10), 'Title screen', font=TITLE(44), fill=(255, 255, 255))
row.paste(tag(title_screen(False).resize((TW, TH), Image.LANCZOS), 'TODAY', SOFT, 28), (GAP, 70))
row.paste(tag(title_screen(True).resize((TW, TH), Image.LANCZOS), 'CLASSIC CARTOON', YELLOW, 28), (GAP * 2 + TW, 70))
p.append(row)
row = Image.new('RGB', (W4, 70 + TH + GAP), BG); d = ImageDraw.Draw(row)
d.text((GAP, 10), 'Add-ons & Filters: a fourth filter card, Classic cartoon (selected)', font=TITLE(44), fill=(255, 255, 255))
row.paste(addons_panel().resize((TW, TH), Image.LANCZOS), (GAP, 70))
d.text((GAP * 2 + TW + 10, 90), 'Where it lives', font=TITLE(40), fill=YELLOW)
notes = ['• A fourth card under Filters, beside Original,', '   Comic halftone and Pencil sketch.', '• Like the others it applies at once, in every', '   scene, and is saved with the game.',
         '• It fills the empty fourth slot, so the panel', '   keeps its size (two rows of two).', '', 'What it touches', '• Every level, the challenges, the Holiday Run', '   and co-op races (one camera filter).',
         '• The menu’s live street and the Locker Room.', '• The pictures the menus draw: player cards,', '   bags, stickers, the logo, the town map.', '• Not the text: words and numbers stay crisp.']
y = 150
for n in notes:
    is_head = n in ('What it touches',)
    d.text((GAP * 2 + TW + 10, y), n, font=TITLE(40) if is_head else BODY(30), fill=YELLOW if is_head else (230, 233, 245))
    y += 52 if is_head else 40
p.append(row)
stack(p, W4).save(os.path.join(OUT, '4_screens.jpg'), quality=88)
title_screen(True).save(os.path.join(OUT, 'frames', 'title_screen.jpg'), quality=88)
print('4_screens')
