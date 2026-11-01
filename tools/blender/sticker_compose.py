# Turns sticker_art.py's renders into the album's die-cut vinyl stickers (512 x 512, transparent):
# a round badge in the chapter's colour with a sunburst behind, the subject popping out over it,
# a blank navy name ribbon along the bottom (the game letters the name on it, in the player's
# language: see UI/StickerBook.RibbonRect), and a thick die-cut border round the lot.
#   normal - white vinyl border
#   holo   - pastel rainbow foil border and a rainbow sunburst, with sparkles (the game adds a moving sheen)
#   gold   - a scalloped gold badge with a gold foil border (the chapter finales)
#   python3 sticker_compose.py <renders dir> <out dir>
# Copy the results to Assets/_Game/Resources/UI/Stickers/ (UiArtImportSettings makes them sprites).
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 512
# Chapter colours (GeneratedContent.Chapters) and each level's chapter and rarity (UI/StickerBook).
CHAPTER = {1: (247, 140, 69), 2: (230, 107, 107), 3: (77, 173, 217), 4: (140, 122, 184), 5: (107, 179, 102)}
LEVELS = {
    'L01': (1, 'normal'), 'L02': (1, 'normal'), 'L03': (1, 'normal'), 'L04': (1, 'holo'), 'L05': (1, 'gold'),
    'L06': (2, 'normal'), 'L07': (2, 'normal'), 'L08': (2, 'holo'), 'L09': (2, 'normal'), 'L10': (2, 'gold'),
    'L11': (3, 'normal'), 'L12': (3, 'holo'), 'L13': (3, 'normal'), 'L14': (3, 'gold'),
    'L15': (4, 'normal'), 'L16': (4, 'holo'), 'L17': (4, 'normal'), 'L18': (4, 'gold'),
    'L19': (5, 'normal'), 'L20': (5, 'holo'), 'L21': (5, 'normal'), 'L22': (5, 'holo'), 'L23': (5, 'gold'),
}
NAVY = (36, 51, 102)
CENTRE = (256, 236)
BADGE_R = 188
RIBBON = (66, 392, 446, 452)        # x0, y0, x1, y1 (y down)
BORDER = 15


def hsv(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def disc_mask(r, centre=CENTRE, scallops=0):
    m = Image.new('L', (S * 2, S * 2), 0)
    d = ImageDraw.Draw(m)
    cx, cy = centre[0] * 2, centre[1] * 2
    if scallops:
        pts = []
        for i in range(720):
            a = i / 720 * math.pi * 2
            rr = r * 2 * (0.94 + 0.06 * abs(math.cos(a * scallops / 2)) ** 0.6)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=255)
    else:
        d.ellipse([cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2], fill=255)
    return m.resize((S, S), Image.LANCZOS)


def sunburst(base, rarity, rays=18):
    """The badge's fill: the colour with alternating lighter rays from the centre (rainbow ones on holo)."""
    im = Image.new('RGBA', (S, S), base + (255,))
    d = ImageDraw.Draw(im)
    cx, cy = CENTRE
    for i in range(rays):
        a0 = (i / rays) * math.pi * 2 - 0.05
        a1 = a0 + math.pi / rays
        if rarity == 'holo':
            col = mix(hsv(i / rays, 0.38, 1.0), base, 0.35)
        elif rarity == 'gold':
            col = (232, 178, 62)
        else:
            col = mix(base, (255, 255, 255), 0.18)
        d.polygon([(cx, cy), (cx + math.cos(a0) * 400, cy + math.sin(a0) * 400), (cx + math.cos(a1) * 400, cy + math.sin(a1) * 400)], fill=col + (255,))
    # A soft light in the middle so the subject stands out.
    glow = Image.new('L', (S, S), 0)
    ImageDraw.Draw(glow).ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=60 if rarity == 'gold' else 110)
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    im = Image.composite(Image.new('RGBA', (S, S), (255, 255, 255, 255)), im, glow)
    return im


def foil(rarity):
    """The border's vinyl: white, rainbow foil (holo) or gold foil."""
    im = Image.new('RGBA', (S, S), (255, 255, 255, 255))
    if rarity == 'normal':
        return im
    d = ImageDraw.Draw(im)
    for i in range(-S, S * 2, 2):
        t = i / S
        if rarity == 'holo':
            c = mix(hsv(t * 0.9 + 0.55, 0.45, 1.0), (255, 255, 255), 0.35)
        else:
            k = 0.5 + 0.5 * math.sin(t * math.pi * 3.2)
            c = mix((214, 150, 30), (255, 238, 160), k)
        d.line([(i, 0), (i - S, S)], fill=c + (255,), width=3)
    return im


def sparkle(d, x, y, r, col=(255, 255, 255, 240)):
    pts = []
    for k in range(8):
        a = k / 8 * math.pi * 2 - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d.polygon(pts, fill=col)


def ribbon_shape():
    m = Image.new('L', (S * 2, S * 2), 0)
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = [v * 2 for v in RIBBON]
    notch = 26
    h = y1 - y0
    # Tails behind each end, then the band, with swallowtail notches.
    for side in (-1, 1):
        tx = x0 - 34 if side < 0 else x1 + 34
        ex = x0 + 20 if side < 0 else x1 - 20
        d.polygon([(ex, y0 + 18), (tx, y0 + 18), (tx + side * -notch, y0 + 18 + h / 2), (tx, y1 + 18), (ex, y1 + 18)], fill=150)
    d.rounded_rectangle([x0, y0, x1, y1], 14, fill=255)
    return m.resize((S, S), Image.LANCZOS)


def compose(render, level):
    chapter, rarity = LEVELS[level]
    base = CHAPTER[chapter]
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0))

    # Badge.
    badge_mask = disc_mask(BADGE_R, scallops=16 if rarity == 'gold' else 0)
    # Gold finales: golden rays on royal navy, so even a golden subject stands out.
    burst = sunburst((40, 54, 116) if rarity == 'gold' else base, rarity)
    badge = Image.composite(burst, Image.new('RGBA', (S, S), (0, 0, 0, 0)), badge_mask)
    # Inner ring a shade deeper, like a printed edge.
    ring = Image.new('L', (S, S), 0)
    inner = disc_mask(BADGE_R - 9, scallops=16 if rarity == 'gold' else 0)
    ring = ImageChops.subtract(badge_mask, inner)
    deep = (236, 182, 58) if rarity == 'gold' else mix(base, (30, 30, 60), 0.3)
    badge = Image.composite(Image.new('RGBA', (S, S), deep + (255,)), badge, ring)
    out.alpha_composite(badge)

    # Subject, fitted into the box above the ribbon, popping out over the badge.
    bb = render.getbbox()
    sub = render.crop(bb)
    box_w, box_h = 404, 352
    k = min(box_w / sub.width, box_h / sub.height)
    sub = sub.resize((max(1, int(sub.width * k)), max(1, int(sub.height * k))), Image.LANCZOS)
    sx = int(256 - sub.width / 2)
    sy = int(232 - sub.height / 2)
    sy = min(sy, 410 - sub.height)          # feet tuck behind the ribbon
    # A soft contact shadow under the subject on the badge.
    sh = Image.new('L', (S, S), 0)
    ImageDraw.Draw(sh).ellipse([256 - sub.width * 0.36, sy + sub.height - 16, 256 + sub.width * 0.36, sy + sub.height + 10], fill=70)
    sh = Image.composite(sh.filter(ImageFilter.GaussianBlur(8)), Image.new('L', (S, S), 0), badge_mask)
    out.alpha_composite(Image.merge('RGBA', (Image.new('L', (S, S), 20),) * 3 + (sh,)))
    out.alpha_composite(sub, (sx, sy))

    # Ribbon (blank: the game letters the name).
    rib = ribbon_shape()
    band_col = (160, 34, 46) if rarity == 'gold' else NAVY
    tails = Image.composite(Image.new('RGBA', (S, S), mix(band_col, (0, 0, 0), 0.35) + (255,)), Image.new('RGBA', (S, S), (0, 0, 0, 0)),
                            rib.point(lambda v: 255 if 100 < v < 200 else 0))
    out.alpha_composite(tails)
    band = Image.composite(Image.new('RGBA', (S, S), band_col + (255,)), Image.new('RGBA', (S, S), (0, 0, 0, 0)), rib.point(lambda v: 255 if v > 200 else 0))
    out.alpha_composite(band)
    trim = ImageChops.subtract(rib.point(lambda v: 255 if v > 200 else 0), rib.point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.MinFilter(7)))
    trim_col = (255, 214, 90) if rarity == 'gold' else (255, 255, 255)
    out.alpha_composite(Image.composite(Image.new('RGBA', (S, S), trim_col + (255,)), Image.new('RGBA', (S, S), (0, 0, 0, 0)), trim))

    # Sparkles on holo and gold.
    if rarity != 'normal':
        d = ImageDraw.Draw(out)
        for x, y, r in ((112, 108, 20), (404, 140, 15), (380, 330, 11), (134, 300, 9)):
            sparkle(d, x, y, r)

    # Die-cut border round everything, then a hairline so it reads on white pages.
    alpha = out.getchannel('A')
    grown = alpha.filter(ImageFilter.GaussianBlur(BORDER * 0.75)).point(lambda v: max(0, min(255, (v - 10) * 12)))
    grown = ImageChops.lighter(grown, alpha)
    sticker = Image.composite(foil(rarity), Image.new('RGBA', (S, S), (0, 0, 0, 0)), grown)
    hair = ImageChops.subtract(grown, grown.filter(ImageFilter.MinFilter(5)))
    sticker.alpha_composite(Image.composite(Image.new('RGBA', (S, S), (190, 196, 214, 255)), Image.new('RGBA', (S, S), (0, 0, 0, 0)), hair))
    sticker.alpha_composite(out)

    # Vinyl gloss: a soft diagonal band of light across the whole sticker.
    gloss = Image.new('L', (S, S), 0)
    ImageDraw.Draw(gloss).polygon([(40, 0), (190, 0), (-20, 300), (-170, 300)], fill=46)
    gloss = gloss.filter(ImageFilter.GaussianBlur(18))
    gloss = ImageChops.multiply(gloss, grown)
    sticker = Image.composite(Image.new('RGBA', (S, S), (255, 255, 255, 255)), sticker, gloss)
    sticker.putalpha(grown)
    return sticker


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for level in sorted(LEVELS):
        path = os.path.join(src, level + '.png')
        if not os.path.exists(path):
            print('missing', path)
            continue
        compose(Image.open(path).convert('RGBA'), level).save(os.path.join(dst, level + '.png'), optimize=True)
        print('sticker', level)
