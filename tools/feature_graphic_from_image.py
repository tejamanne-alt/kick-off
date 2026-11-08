# Makes Google Play's feature graphic (1024 x 500, the banner at the top of the store listing) from the game's banner
# artwork. Art already about 2 : 1 is scaled to fill and the sliver left over trimmed. Wider art is kept whole: the art is 3 : 1 and the graphic about 2 : 1, so rather than crop off the kid or the logo, a
# little is trimmed from the sides and the art is laid over an out-of-focus enlargement of itself, which fills the room
# above and below; the art fades into it over its top and bottom edges, so there is no seam.
#   python3 tools/feature_graphic_from_image.py marketing/source/banner_artwork.png [--trim 0.08] [--preview /abs/out.png]
#     -> marketing/googleplay/feature_graphic_1024x500.png
import os, sys
import numpy as np
from PIL import Image, ImageFilter

args = sys.argv[1:]
src = args[0]
trim = float(args[args.index('--trim') + 1]) if '--trim' in args else 0.08   # (off the left: the logo runs to the right edge)
preview = args[args.index('--preview') + 1] if '--preview' in args else None
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
W, H = 1024, 500

art = Image.open(src).convert('RGB')
w, h = art.size
if abs((w / h) / (W / H) - 1) < 0.08:
    # Art already about 2 : 1 (as drawn for this slot): scaled to fill and the sliver left over trimmed off its middle.
    k = max(W / w, H / h)
    art = art.resize((round(w * k), round(h * k)), Image.LANCZOS)
    x, y = (art.width - W) // 2, (art.height - H) // 2
    out = art.crop((x, y, x + W, y + H)).filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=2))
    path = os.path.join(root, 'marketing/googleplay/feature_graphic_1024x500.png')
    out.save(path, optimize=True)
    print('wrote', os.path.relpath(path, root), out.size, '(scaled to fill, %d px trimmed off each side, %d off top and bottom)' % (x, y))
    if preview:
        out.save(preview)
    sys.exit(0)
cut = int(w * trim)
art = art.crop((cut, 0, w - int(w * 0.005), h))            # (the tree at the left edge: nothing there to lose)
w = art.width
need = int(round(w * H / W))                                # the height that width needs at 1024 : 500
pad = max(0, need - h)
top, bottom = pad // 2, pad - pad // 2
# Behind it, the art itself enlarged to fill the taller frame and thrown well out of focus (the same sky, trees and grass,
# soft); the art over it fades in over its top and bottom few rows, so there is no seam.
H2 = h + pad
k = H2 / h
bg = art.resize((int(w * k), H2), Image.LANCZOS)
bg = bg.crop(((bg.width - w) // 2, 0, (bg.width - w) // 2 + w, H2)).filter(ImageFilter.GaussianBlur(28))
canvas = bg.copy()
feather = int(h * 0.06)
alpha = np.ones((h, w), np.float32)
ramp = np.linspace(0, 1, feather, dtype=np.float32) ** 1.5
alpha[:feather] *= ramp[:, None]; alpha[h - feather:] *= ramp[::-1][:, None]
canvas.paste(art, (0, top), Image.fromarray((alpha * 255).astype(np.uint8)))
out = canvas.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.0, percent=50, threshold=2))
path = os.path.join(root, 'marketing/googleplay/feature_graphic_1024x500.png')
out.save(path, optimize=True)
print('wrote', os.path.relpath(path, root), out.size, '(trimmed %d px off the left, extended %d px above and %d below)' % (cut, top, bottom))
if preview:
    out.save(preview)
