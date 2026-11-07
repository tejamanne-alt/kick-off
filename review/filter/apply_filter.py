"""Runs the shader port over render_street.py's passes and writes the review images:
   python3 apply_filter.py <render dir> <out dir>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shader_port as sp

src, out = sys.argv[1], sys.argv[2]
suffix = sys.argv[3] if len(sys.argv) > 3 else ''
os.makedirs(out, exist_ok=True)
FAR = 300.0


def load(name, bits16=False):
    a = np.asarray(Image.open(os.path.join(src, name)))
    a = a.astype(np.float64) / (65535.0 if a.dtype == np.uint16 or bits16 else 255.0)
    return a[..., :3]


colour = load('colour%s.png' % suffix)
normal = load('normal%s.png' % suffix) * 2 - 1
normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
data = load('data%s.png' % suffix)
depth01 = np.clip(data[..., 0] + data[..., 1] / 255.0, 0, 1)
alpha = data[..., 2]

before = sp.plain(colour)
after = sp.print_pass(sp.comic_pass(colour, alpha, depth01, normal, FAR), alpha)
# For comparison: the same filter without the character mask (lines and bands across the faces too).
nomask = sp.print_pass(sp.comic_pass(colour, alpha, depth01, normal, FAR, mask_on=0.0), alpha, mask_on=0.0)


def img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


B, A, N = img(before), img(after), img(nomask)
B.save(os.path.join(out, 'game_original%s.png' % suffix))
A.save(os.path.join(out, 'game_comic%s.png' % suffix))

try:
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
except Exception:
    f = ImageFont.load_default()


def labelled(im, text):
    c = im.copy(); d = ImageDraw.Draw(c)
    d.rectangle([0, 0, 18 + d.textlength(text, font=f), 48], fill=(24, 18, 40))
    d.text((9, 8), text, font=f, fill=(255, 214, 80))
    return c


w, h = B.size
sheet = Image.new('RGB', (w, h * 2 + 20), (24, 18, 40))
sheet.paste(labelled(B, 'ORIGINAL'), (0, 0)); sheet.paste(labelled(A, 'COMIC HALFTONE'), (0, h + 20))
sheet.save(os.path.join(out, 'before_after%s.jpg' % suffix), quality=92)

N.save(os.path.join(out, 'game_nomask%s.png' % suffix))
if suffix == '_close':
    tw = w // 2
    tiles = [im.resize((tw, h * tw // w), Image.LANCZOS) for im in (B, N, A)]
    cs = Image.new('RGB', (tw * 3 + 40, tiles[0].height + 70), (24, 18, 40))
    d = ImageDraw.Draw(cs)
    for j, (t, name) in enumerate(zip(tiles, ['ORIGINAL', 'FILTER WITHOUT THE MASK', 'COMIC HALFTONE (SHIPPED)'])):
        cs.paste(t, (10 + j * (tw + 10), 60))
        d.text((10 + j * (tw + 10), 14), name, font=f, fill=(255, 214, 80))
    cs.save(os.path.join(out, 'faces_compare.jpg'), quality=92)
print('done', suffix)
