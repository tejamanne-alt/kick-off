"""Lays the game's sky behind render_pier.py's pictures and puts them on one board:
    python3 -I compose.py <render dir> <out dir> [today screenshot]
    python3 -I compose.py <render dir> <out dir> --course        (the climb: course_board.jpg)"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

SKY_TOP, SKY_LOW = (52, 108, 200), (120, 178, 232)


def with_sky(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    sky = Image.new('RGBA', (w, h))
    px = sky.load()
    for y in range(h):
        t = min(1.0, (y / h) / 0.42) ** 1.3
        c = tuple(int(SKY_TOP[i] + (SKY_LOW[i] - SKY_TOP[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c + (255,)
    return Image.alpha_composite(sky, im).convert('RGB')


def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def label(im, text):
    d = ImageDraw.Draw(im)
    f = font(max(18, im.size[1] // 28))
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    pad = f.size // 2
    d.rectangle((0, 0, x1 + 2 * pad, y1 + 2 * pad), fill=(20, 24, 32))
    d.text((pad, pad - y0 // 2), text, font=f, fill=(255, 255, 255))
    return im


COURSE = [('course_up', 'Up the steps with the ball: the camera rises with the kid'),
          ('course_top', 'Over the landing in front of the pier, at the top'),
          ('course_down', 'Down the other side to the sand (the camera follows them down)'),
          ('course_whole', 'The climb across the lane: no rail on the camera side, so the kid is never behind bars')]


def course_board(src, out):
    W, gap, rows = 2400, 16, []
    for name, title in COURSE:
        p = os.path.join(src, name + '.png')
        if not os.path.exists(p):
            continue
        im = with_sky(p)
        im.save(os.path.join(out, name + '.jpg'), quality=92)
        rows.append(label(im.resize((W, int(im.size[1] * W / im.size[0])), Image.LANCZOS), title))
    board = Image.new('RGB', (W, sum(r.size[1] for r in rows) + gap * (len(rows) - 1)), (245, 245, 245))
    y = 0
    for r in rows:
        board.paste(r, (0, y)); y += r.size[1] + gap
    board.save(os.path.join(out, 'course_board.jpg'), quality=88)
    print('course board', board.size)


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    if '--course' in sys.argv:
        os.makedirs(out, exist_ok=True)
        course_board(src, out)
        sys.exit(0)
    os.makedirs(out, exist_ok=True)
    shots = {}
    for name in ('game', 'whole', 'close'):
        p = os.path.join(src, name + '.png')
        if os.path.exists(p):
            shots[name] = with_sky(p)
            shots[name].save(os.path.join(out, name + '.jpg'), quality=92)
    W = 2400
    rows = []
    titles = {'game': 'In the game: the stairs from the play camera (Low Tide, California)',
              'whole': 'The whole front: a landing at deck height, a flight down each side, a mid-landing halfway',
              'close': 'Close: timber treads, white rails both sides, a boardwalk path at each foot'}
    if len(sys.argv) > 3:
        today = Image.open(sys.argv[3]).convert('RGB')
        rows.append(label(today.resize((W, int(today.size[1] * W / today.size[0]))), 'Today: no way up to the deck'))
    for name in ('game', 'whole', 'close'):
        if name in shots:
            im = shots[name]
            rows.append(label(im.resize((W, int(im.size[1] * W / im.size[0])), Image.LANCZOS), titles[name]))
    gap = 16
    board = Image.new('RGB', (W, sum(r.size[1] for r in rows) + gap * (len(rows) - 1)), (245, 245, 245))
    y = 0
    for r in rows:
        board.paste(r, (0, y)); y += r.size[1] + gap
    board.save(os.path.join(out, 'pier_stairs_board.jpg'), quality=88)
    print('board', board.size)
