# Cuts the game's logo ("Kick OFF 2", its yellow swoosh) out of the banner artwork as a picture with a clear background,
# for the title screen, the splash and the credits (UI/KickOffLogo, Resources/UI/KickOffLogo.png):
#   python3 tools/logo_from_banner.py marketing/source/banner_artwork.png [--preview /abs/dir]
# The logo is ringed by a thick dark navy outline: everything that outline closes in is the logo (the flood from the
# picture's edges never reaches it). The swoosh's yellow tail, which runs out past the outline under "Kick", is grown back
# from the swoosh along its own yellow. The edge is softened by a pixel so it sits cleanly on any background.
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

args = sys.argv[1:]
src = args[0]
preview = args[args.index('--preview') + 1] if '--preview' in args else None
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BOX = (860, 300, 1774, 660)                                 # the logo's corner of the banner (it is at the right, mid height)

art = Image.open(src).convert('RGB')
sx = art.width / 1774.0                                     # (the box is given for the 1774 x 887 artwork)
box = tuple(int(round(v * sx)) for v in BOX)
im = art.crop(box)
a = np.asarray(im, np.float32) / 255
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mx, mn = a.max(-1), a.min(-1)

# The outline: dark and blue (tree shadows nearby are dark but green or brown).
navy = (mx < 0.36) & (b >= r) & (b >= g * 0.95)
wall = Image.fromarray(np.where(navy, 0, 255).astype(np.uint8))
# A wall a pixel thicker, so the flood can't slip through a thin spot in the outline.
wall = wall.filter(ImageFilter.MinFilter(3))
fill = wall.copy()
W, H = fill.size
for x in range(0, W, 4):
    for y in (0, H - 1):
        if fill.getpixel((x, y)) == 255:
            ImageDraw.floodfill(fill, (x, y), 128)
for y in range(0, H, 4):
    for x in (0, W - 1):
        if fill.getpixel((x, y)) == 255:
            ImageDraw.floodfill(fill, (x, y), 128)
logo = np.asarray(fill) != 128

# The swoosh's tail: yellow pixels joined to the logo, grown out from it.
hsv = np.asarray(im.convert('HSV'), np.float32) / 255
yellow = (hsv[..., 0] > 0.10) & (hsv[..., 0] < 0.19) & (hsv[..., 1] > 0.45) & (hsv[..., 2] > 0.75)
grown = logo.copy()
for _ in range(400):
    nb = grown.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb |= np.roll(grown, (dy, dx), (0, 1))
    new = nb & yellow & ~grown
    if not new.any():
        break
    grown |= new
logo = grown

# Keep only the biggest piece (a stray patch of the background the flood couldn't reach would otherwise come along).
lab = Image.fromarray(np.where(logo, 255, 0).astype(np.uint8))
ys, xs = np.where(logo)
seed = (int(np.median(xs)), int(np.median(ys)))             # (inside the lettering)
if lab.getpixel(seed) != 255:
    k = np.argmin((xs - seed[0]) ** 2 + (ys - seed[1]) ** 2); seed = (int(xs[k]), int(ys[k]))
lab = lab.copy(); ImageDraw.floodfill(lab, seed, 200)   # (a copy: floodfill needs an image of its own)
lab = Image.fromarray(np.where(np.asarray(lab) == 200, 255, 0).astype(np.uint8))
alpha = np.asarray(lab.filter(ImageFilter.GaussianBlur(0.8)), np.float32)
out = np.dstack([np.asarray(im), alpha.astype(np.uint8)])
ys, xs = np.where(alpha > 8)
pad = 6
crop = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad + 1), min(H, ys.max() + pad + 1))
result = Image.fromarray(out, 'RGBA').crop(crop)
path = os.path.join(root, 'Assets/_Game/Resources/UI/KickOffLogo.png')
result.save(path, optimize=True)
print('wrote', os.path.relpath(path, root), result.size, '%.0f%% of the box is logo' % (100 * logo.mean()))
if preview:
    os.makedirs(preview, exist_ok=True)
    for name, colour in (('on_dark', (24, 30, 46)), ('on_sky', (110, 170, 235)), ('on_white', (255, 255, 255))):
        bg = Image.new('RGBA', result.size, colour + (255,)); bg.alpha_composite(result)
        bg.convert('RGB').save(os.path.join(preview, name + '.png'))
