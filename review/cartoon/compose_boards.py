"""Composes the classic cartoon filter's review boards (classic_port.py: inked cels over painted backgrounds, the look
of the classic Road Runner shorts the review asked for) from render_scenes.py's renders and the game's own UI pictures.
Every board shows three versions side by side: the game today, Classic cartoon, and its calmer setting.
  python3 -I compose_boards.py <render dir> <out dir>
  1_levels.jpg        every chapter and the California add-on
  2_characters.jpg    the six kids, a passer-by and the animals close up, and every face at 2x
  3_ui_art.jpg        the pictures the menus draw: player cards, bags, all 23 stickers, the logo, the town map
  4_screens.jpg       the title screen and the Add-ons & Filters panel with the filter on (mock-ups)
  5_details.jpg       100% crops: the first version beside the crisper one (detail kept)
  6_outline.jpg       every kid's face at 3x: the outline drawn outside the silhouette, so it never covers a face
  frames/<scene>.jpg  each scene at full size: today, Classic cartoon, calmer"""
import os, sys, subprocess, importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
CALMC = (150, 220, 255)
SOFT = (196, 202, 222)
FIRST = 'ab5be92'   # the commit with the first version of the look (for 5_details.jpg)
INSIDE = 'dd738b6'  # the commit whose outline lay inside the silhouette (for 6_outline.jpg)
LOOKS = [('TODAY', SOFT), ('CLASSIC CARTOON', YELLOW), ('CALMER', CALMC)]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


TITLE = lambda s: font('LilitaOne-Regular.ttf', s)
BODY = lambda s: font('VarelaRound-Regular.ttf', s)

FRAMES = {}


def frames(scene):
    """today, classic, calmer (PIL), and the mask and depth."""
    if scene not in FRAMES:
        colour, alpha, depth01, nrm = cp.load_scene(SRC, scene)
        FRAMES[scene] = (cp.to_img(sp.plain(colour)), cp.to_img(cl.classic_pass(colour, alpha, depth01, nrm)),
                         cp.to_img(cl.classic_pass(colour, alpha, depth01, nrm, k=cl.CALM)), alpha, depth01)
    return FRAMES[scene]


def tag(im, text, colour=YELLOW, size=34):
    im = im.copy(); d = ImageDraw.Draw(im); f = TITLE(size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([12, 12, 12 + w + 26, 12 + size + 18], radius=10, fill=(20, 18, 36))
    d.text((25, 19), text, font=f, fill=colour)
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


def titled(width, title, line, body_h):
    row = Image.new('RGB', (width, 80 + body_h), BG); d = ImageDraw.Draw(row)
    d.text((GAP, 12), title, font=TITLE(44), fill=(255, 255, 255))
    if line:
        d.text((GAP + d.textlength(title, font=TITLE(44)) + 24, 28), line, font=BODY(26), fill=SOFT)
    return row, d


def three(row, ims, y, tw, th):
    for i, (im, (label, colour)) in enumerate(zip(ims, LOOKS)):
        row.paste(tag(im.resize((tw, th), Image.LANCZOS), label, colour, 26), (GAP + i * (tw + GAP), y))


# ------------------------------------------------------------------ 1. the levels
LEVELS = [
    ('home', 'Chapter 1 · Home Street', 'Leo, the block walls and houses, a utility pole, a bicycle, the post box, a cat, coins'),
    ('market', 'Chapter 2 · Market & Crossings', 'Mia, a passer-by, the shops and stall, crates, pigeons, the crossing light'),
    ('beach', 'Chapter 3 · The Beach', 'Zoe mid-jump, gulls, a crab, the lifeguard tower, parasol, sandcastle, palms, the sea'),
    ('site', 'Chapter 4 · Underpass & Building Site', 'Kai, a builder, the digger, mixer, scaffold, pipe, cones, barrier, the crane'),
    ('park', 'Chapter 5 · Park & School', 'Hana, the dog, swings, the duck pond, trees, the school and its arch'),
    ('california', 'Add-on · California, Santa Monica', 'Max, stucco villas, palms, a picket fence, a 4x4'),
]
TW, TH, GAP = 1040, 585, 24
W = TW * 3 + GAP * 4
rows = [header(W, 'CLASSIC CARTOON · every level', 'Today  |  Classic cartoon (inked cels on painted scenery, as the Road Runner samples)  |  Calmer.  The game’s own models and camera.')]
for scene, title, line in LEVELS:
    o, c, m, _, _ = frames(scene)
    row, d = titled(W, title, line, TH + GAP)
    three(row, (o, c, m), 76, TW, TH)
    rows.append(row)
    full = Image.new('RGB', (o.width, o.height * 3 + 32), BG)
    for i, (im, (label, colour)) in enumerate(zip((o, c, m), LOOKS)):
        full.paste(tag(im, label, colour), (0, i * (o.height + 16)))
    full.save(os.path.join(OUT, 'frames', '%s.jpg' % scene), quality=88)
stack(rows, W).save(os.path.join(OUT, '1_levels.jpg'), quality=88)
print('1_levels')


# ------------------------------------------------------------------ 2. the characters
def heads(alpha, depth01, min_height=300):
    """The figures' heads (the figure mask's tall blobs): their crowns' x and y."""
    fig = (alpha < 0.25) & (depth01 < 0.999)
    xs = np.nonzero(fig.any(0))[0]
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
        cx = a + int(np.nonzero(sub[top:top + 60].any(0))[0].mean())
        out.append((cx, top, ys[-1] - ys[0]))
    return out


rows = [header(W, 'CLASSIC CARTOON · the characters', 'Cels: flat tones and a bold, smooth warm-black outline. Faces kept clean: eyes, brows and mouths sharp, skin smooth.')]
names = {'cast_a': ['Hana', 'Max', 'Kai'], 'cast_b': ['Mia', 'Leo', 'Zoe', 'Passer-by']}
crops = []
for scene in ('cast_a', 'cast_b'):
    o, c, m, alpha, depth01 = frames(scene)
    row = Image.new('RGB', (W, TH + GAP), BG)
    three(row, (o, c, m), 0, TW, TH)
    rows.append(row)
    for (cx, top, hgt), name in zip(heads(alpha, depth01), names[scene]):
        s = int(hgt * 0.34)
        y0 = max(0, top - s // 8)
        box = (cx - s // 2, y0, cx + s // 2, y0 + s)
        crops.append((name, o.crop(box), c.crop(box), m.crop(box)))
FS = 300
for i in range(0, len(crops), 3):
    row = Image.new('RGB', (W, 60 + FS + GAP), BG); d = ImageDraw.Draw(row)
    for j, (name, a, b, cm) in enumerate(crops[i:i + 3]):
        x = GAP + j * (FS * 3 + 16 + 60)
        d.text((x, 10), name, font=TITLE(36), fill=(255, 255, 255))
        d.text((x + d.textlength(name, font=TITLE(36)) + 14, 22), 'today  |  classic  |  calmer', font=BODY(22), fill=SOFT)
        for q, im in enumerate((a, b, cm)):
            row.paste(im.resize((FS, FS), Image.LANCZOS), (x + q * (FS + 8), 60))
    rows.append(row)
stack(rows, W).save(os.path.join(OUT, '2_characters.jpg'), quality=88)
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


def looks2d(a, **kw):
    return [a, cl.classic_2d(a, **kw), cl.classic_2d(a, k=cl.CALM, **kw)]


CARD_BG = (236, 240, 248)
parts = [header(W, 'CLASSIC CARTOON · the menus’ pictures', 'Kids, bags, stickers and the logo as inked cels; the town map painted like the scenery. Text stays crisp.')]


def section(title, line):
    s = Image.new('RGB', (W, 80), BG); d = ImageDraw.Draw(s)
    d.text((GAP, 14), title, font=TITLE(44), fill=(255, 255, 255))
    d.text((GAP + d.textlength(title, font=TITLE(44)) + 24, 30), line, font=BODY(26), fill=SOFT)
    return s


cards = ['PlayerGirl', 'PlayerBackpackBoy', 'PlayerPrimaryBoy', 'PlayerPrimaryGirl', 'PlayerPrimaryBoy2', 'PlayerPrimaryGirl2']
parts.append(section('Player cards', 'rows: today, classic cartoon, calmer'))
CS = 300
cardlooks = [looks2d(rgba(os.path.join(UI, n + '.png')), outline_px=3) for n in cards]
for k in range(3):
    row = Image.new('RGB', (W, CS + 14), BG); d = ImageDraw.Draw(row)
    d.text((GAP, CS // 2 - 20), LOOKS[k][0].title(), font=TITLE(34), fill=LOOKS[k][1])
    for i in range(len(cards)):
        row.paste(on(CARD_BG, cardlooks[i][k], CS), (GAP + 230 + i * (CS + 14), 0))
    parts.append(row)
parts.append(section('Locker Room bags  ·  the logo', 'rows: today, classic cartoon, calmer'))
bags = ['bag_kickoff', 'bag_racecar', 'bag_unicorn', 'bag_denimbow', 'bag_goldentrail']
BS = 220
logo = rgba(os.path.join(UI, 'KickOffLogo.png'))
baglooks = [looks2d(rgba(os.path.join(UI, n + '.png')), outline_px=3) for n in bags]
logolooks = looks2d(logo)
LX = GAP + 230 + 5 * (BS + 14) + 30
LW = W - LX - GAP
for k in range(3):
    row = Image.new('RGB', (W, BS + 14), BG); d = ImageDraw.Draw(row)
    d.text((GAP, BS // 2 - 20), LOOKS[k][0].title(), font=TITLE(34), fill=LOOKS[k][1])
    for i in range(len(bags)):
        row.paste(on(CARD_BG, baglooks[i][k], BS), (GAP + 230 + i * (BS + 14), 0))
    im = Image.fromarray((logolooks[k] * 255 + 0.5).astype(np.uint8), 'RGBA'); im.thumbnail((LW, BS), Image.LANCZOS)
    t = Image.new('RGBA', (LW, BS), (52, 104, 182, 255)); t.alpha_composite(im, ((LW - im.width) // 2, (BS - im.height) // 2))
    row.paste(t.convert('RGB'), (LX, 0))
    parts.append(row)
parts.append(section('Sticker album', 'all 23 stickers: today  |  classic cartoon  |  calmer'))
SS = 152
GW = 6 * (SS + 8)
grid = Image.new('RGB', (W, 4 * (SS + 8) + GAP), BG)
for i in range(23):
    lk = looks2d(rgba(os.path.join(UI, 'Stickers', 'L%02d.png' % (i + 1))), outline_px=3)
    r, col = divmod(i, 6)
    for k in range(3):
        grid.paste(on(CARD_BG, lk[k], SS), (GAP + k * (GW + 50) + col * (SS + 8), r * (SS + 8)))
parts.append(grid)
parts.append(section('Town map', 'a stretch of the map screen at its full size: today  |  classic cartoon  |  calmer'))
mp = rgba(os.path.join(UI, 'TownMap.jpg'))[560:1160, 900:1900]
mm = np.dstack([mp[..., :3], np.ones(mp.shape[:2])])
maps = [mp[..., :3], cl.classic_2d(mm, painted=True, flatten=1.5)[..., :3], cl.classic_2d(mm, painted=True, flatten=1.5, k=cl.CALM)[..., :3]]
MH = int(TW * 600 / 1000)
row = Image.new('RGB', (W, MH + GAP), BG)
for k in range(3):
    row.paste(cp.to_img(maps[k]).resize((TW, MH), Image.LANCZOS), (GAP + k * (TW + GAP), 0))
parts.append(row)
stack(parts, W).save(os.path.join(OUT, '3_ui_art.jpg'), quality=88)
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


def title_screen(look):
    """look: 0 today, 1 classic cartoon, 2 calmer."""
    fr = frames('menu')
    im = fr[look].convert('RGBA')
    cartoon = look > 0
    k = cl.CALM if look == 2 else cl.CLASSIC
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    col = 740
    lg = cl.classic_2d(logo, k=k) if cartoon else logo
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
    bx1, by1 = 1920 - 40, 1080 - 44
    button(d, (bx1 - 330, by1 - 104, bx1, by1), PAPER, '', 30, cartoon, radius=24)
    card = rgba(os.path.join(UI, 'PlayerPrimaryBoy2.png'))
    if cartoon:
        card = cl.classic_2d(card, k=k, outline_px=3)
    ci = Image.fromarray((card * 255 + 0.5).astype(np.uint8), 'RGBA').resize((84, 84), Image.LANCZOS)
    d.ellipse([bx1 - 330 + 12, by1 - 52 - 42, bx1 - 330 + 96, by1 - 52 + 42], fill=(214, 226, 246))
    ov.alpha_composite(ci, (bx1 - 330 + 12, by1 - 52 - 42 - 4))
    d.text((bx1 - 330 + 112, by1 - 84), 'Leo', font=TITLE(38), fill=INK)
    d.text((bx1 - 330 + 112, by1 - 40), 'Tap to change', font=BODY(24), fill=(90, 96, 120))
    im.alpha_composite(ov)
    return im.convert('RGB')


def addons_panel():
    im = frames('menu')[1].convert('RGBA')
    im.alpha_composite(Image.new('RGBA', im.size, (10, 18, 46, 128)))
    d = ImageDraw.Draw(im)
    cw, ch = 1340, 960
    x0, y0 = (1920 - cw) // 2, (1080 - ch) // 2
    d.rounded_rectangle([x0 + 6, y0 + 12, x0 + cw + 6, y0 + ch + 12], radius=40, fill=(18, 14, 34))
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=40, fill=PAPER, outline=(18, 14, 34), width=4)
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


p = [header(W, 'CLASSIC CARTOON · menus (mock-ups)', 'The menu’s live street goes through the filter like a level; the buttons take an ink edge and a hard shadow; the logo and player card are inked cels.')]
row, d = titled(W, 'Title screen', 'today  |  classic cartoon  |  calmer', TH + GAP)
three(row, [title_screen(i) for i in range(3)], 76, TW, TH)
p.append(row)
row, d = titled(W, 'Add-ons & Filters: a fourth filter card, Classic cartoon (selected)', '', TH + GAP)
row.paste(addons_panel().resize((TW, TH), Image.LANCZOS), (GAP, 76))
nx = GAP * 2 + TW + 10
d.text((nx, 90), 'Where it lives', font=TITLE(40), fill=YELLOW)
notes = ['• A fourth card under Filters, beside Original, Comic halftone and Pencil sketch.', '• Applies at once, in every scene, and is saved with the game.',
         '• It fills the empty fourth slot, so the panel keeps its size (two rows of two).', '', 'What it touches',
         '• Every level, the challenges, the Holiday Run and co-op races (one camera filter).', '• The menu’s live street and the Locker Room.',
         '• The pictures the menus draw: player cards, bags, stickers, the logo, the town map.', '• The menu buttons: an ink edge and a hard shadow (agreed).',
         '• Not the text: words and numbers stay crisp.', '• No pop-up sound-effect words with this filter (agreed).']
y = 150
for n in notes:
    is_head = n == 'What it touches'
    d.text((nx, y), n, font=TITLE(40) if is_head else BODY(30), fill=YELLOW if is_head else (230, 233, 245))
    y += 54 if is_head else 42
p.append(row)
stack(p, W).save(os.path.join(OUT, '4_screens.jpg'), quality=88)
for i, n in ((1, 'title_screen'), (2, 'title_screen_calmer')):
    title_screen(i).save(os.path.join(OUT, 'frames', '%s.jpg' % n), quality=88)
print('4_screens')


# ------------------------------------------------------------------ 5. detail at 100%: the first version beside the crisper one
def version_at(commit):
    """classic_port.py as it was at a commit, to compare with now."""
    try:
        src = subprocess.run(['git', '-C', HERE, 'show', commit + ':review/cartoon/classic_port.py'], capture_output=True, text=True, check=True).stdout
    except Exception:
        return None
    spec = importlib.util.spec_from_loader('classic_' + commit, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__['__file__'] = os.path.join(HERE, 'classic_port.py')
    exec(compile(src, 'classic_' + commit, 'exec'), mod.__dict__)
    return mod


first = version_at(FIRST)
DETAILS = [('market', (380, 280, 980, 620), 'Shop sign, awning, window'), ('home', (1150, 560, 1750, 900), 'Bicycle, coins, post box, block wall'),
           ('cast_a', (760, 230, 1180, 520), 'Max’s face and jacket'), ('cast_a', (1330, 400, 1680, 640), 'Kai’s face, the ball'),
           ('park', (1180, 180, 1780, 520), 'School, arch, lamps'), ('site', (60, 300, 660, 640), 'Digger, scaffold, site fence')]
cols = [('TODAY', SOFT), ('FIRST VERSION', (255, 150, 120)), ('NOW: CRISPER', YELLOW), ('NOW: CALMER', CALMC)]
DW = 720
W5 = DW * 4 + GAP * 5
p = [header(W5, 'CLASSIC CARTOON · detail at 100%', 'The first version smoothed with a big brush. Now only weak texture is smoothed: frames, lettering, spokes and seams stay sharp; faces stay clean.')]
for scene, box, title in DETAILS:
    colour, alpha, depth01, nrm = cp.load_scene(SRC, scene)
    x0, y0, x1, y1 = box
    dh = int(DW * (y1 - y0) / (x1 - x0))
    ims = [frames(scene)[0].crop(box),
           cp.to_img(first.classic_pass(colour, alpha, depth01, nrm)).crop(box) if first else None,
           frames(scene)[1].crop(box), frames(scene)[2].crop(box)]
    row, d = titled(W5, title, '', dh + GAP)
    for i, (im, (label, colour_)) in enumerate(zip(ims, cols)):
        if im is not None:
            row.paste(tag(im.resize((DW, dh), Image.NEAREST if (x1 - x0) * 2 <= DW else Image.LANCZOS), label, colour_, 24), (GAP + i * (DW + GAP), 76))
    p.append(row)
stack(p, W5).save(os.path.join(OUT, '5_details.jpg'), quality=90)
print('5_details')


# ------------------------------------------------------------------ 6. the outline: outside the silhouette, never over a face
inside = version_at(INSIDE)
cols6 = [('TODAY', SOFT), ('BEFORE: LINE INSIDE', (255, 150, 120)), ('NOW: LINE OUTSIDE', YELLOW)]
FS6 = 330
blocks = []
for scene in ('cast_a', 'cast_b'):
    colour, alpha, depth01, nrm = cp.load_scene(SRC, scene)
    o, c, _, _, _ = frames(scene)
    b = cp.to_img(inside.classic_pass(colour, alpha, depth01, nrm)) if inside else None
    for (cx, top, hgt), name in zip(heads(alpha, depth01), names[scene]):
        if name == 'Passer-by':
            continue
        sz = int(hgt * 0.3)
        y0 = max(0, top - sz // 10)
        box = (cx - sz // 2, y0, cx + sz // 2, y0 + sz)
        blocks.append((name, [o.crop(box), b.crop(box) if b else None, c.crop(box)]))
W6 = 2 * (3 * FS6 + 2 * 8) + GAP * 3 + 40
p = [header(W6, 'CLASSIC CARTOON \u00b7 the kids\u2019 outline', 'The outline is now drawn only outside the silhouette (on the far side of an edge), so it wraps a face and never covers it.')]
for i in range(0, len(blocks), 2):
    row = Image.new('RGB', (W6, 64 + FS6 + GAP), BG); d = ImageDraw.Draw(row)
    for j, (name, ims) in enumerate(blocks[i:i + 2]):
        x = GAP + j * (3 * FS6 + 16 + GAP + 40)
        d.text((x, 10), name, font=TITLE(38), fill=(255, 255, 255))
        for q, (im, (label, colour_)) in enumerate(zip(ims, cols6)):
            if im is not None:
                row.paste(tag(im.resize((FS6, FS6), Image.LANCZOS), label, colour_, 20), (x + q * (FS6 + 8), 60))
    p.append(row)
stack(p, W6).save(os.path.join(OUT, '6_outline.jpg'), quality=90)
print('6_outline')
