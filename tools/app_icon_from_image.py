# Makes every app icon the stores and the game need from one supplied square picture (the game's logo artwork):
#   python3 tools/app_icon_from_image.py /abs/logo.png [--inset 0.035] [--preview /abs/dir]
#     marketing/appstore/icon_1024.png               App Store icon: 1024 x 1024, opaque, square corners (iOS rounds them)
#     marketing/googleplay/icon_512.png              Google Play listing icon: 512 x 512, opaque (Play adds its own mask)
#     Assets/_Game/Art/Icon/AppIcon.png              the game's icon for every platform (BuildScripts.ApplyIcon), 1024
#     Assets/_Game/Art/Icon/AppIconBackground.png    Android adaptive icon, back layer: the whole picture in the middle
#                                                    72 of the layer's 108 dp (all a launcher shows), over a blurred copy
#     Assets/_Game/Art/Icon/AppIconForeground.png    Android adaptive icon, front layer: clear
# A picture drawn with its own rounded frame (a border and dark or clear corners outside it) has --inset of each side cut
# off, so the art runs to the square's edge: the stores round the corners themselves, and a drawn frame would show a
# second, smaller rounding with dark corners. --preview writes it masked as iOS and Android show it, 300 px down to 40 px.
import os, sys
from PIL import Image, ImageDraw, ImageFilter

args = sys.argv[1:]
src = args[0]
inset = float(args[args.index('--inset') + 1]) if '--inset' in args else 0.0
preview = args[args.index('--preview') + 1] if '--preview' in args else None
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
N = 2048

im = Image.open(src).convert('RGBA')
w, h = im.size
side = min(w, h)
im = im.crop(((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side))
cut = int(side * inset)
if cut:
    im = im.crop((cut, cut, side - cut, side - cut))
art = Image.new('RGBA', im.size, (255, 255, 255, 255))          # (opaque: anything clear left at the corners goes white)
art.alpha_composite(im)
art = art.convert('RGB').resize((N, N), Image.LANCZOS)


def save(img, rel, px):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.resize((px, px), Image.LANCZOS).save(path, optimize=True)
    print('wrote', rel, px)


save(art, 'marketing/appstore/icon_1024.png', 1024)
save(art, 'marketing/googleplay/icon_512.png', 512)
save(art, 'Assets/_Game/Art/Icon/AppIcon.png', 1024)
# Android's adaptive icon: a launcher shows only the middle 72 of the layer's 108 dp, masked as small as a 66 dp circle,
# so the whole picture goes in that middle over a blurred, enlarged copy of itself for the margin.
inner = int(N * 72 / 108)
back = art.filter(ImageFilter.GaussianBlur(N * 0.02))
back.paste(art.resize((inner, inner), Image.LANCZOS), ((N - inner) // 2, (N - inner) // 2))
save(back, 'Assets/_Game/Art/Icon/AppIconBackground.png', 1024)
clear = os.path.join(root, 'Assets/_Game/Art/Icon/AppIconForeground.png')
Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)).save(clear, optimize=True)
print('wrote Assets/_Game/Art/Icon/AppIconForeground.png 1024')

if preview:
    os.makedirs(preview, exist_ok=True)

    def mask(px, round_):
        m = Image.new('L', (px * 4, px * 4), 0)
        d = ImageDraw.Draw(m)
        if round_:
            d.ellipse([0, 0, px * 4 - 1, px * 4 - 1], fill=255)
        else:
            d.rounded_rectangle([0, 0, px * 4 - 1, px * 4 - 1], radius=int(px * 4 * 0.2237), fill=255)
        return m.resize((px, px), Image.LANCZOS)

    sheet = Image.new('RGB', (1500, 760), (32, 36, 44))
    x = 30
    for px in (300, 180, 120, 80, 58, 40):
        sheet.paste(art.resize((px, px), Image.LANCZOS), (x, 40), mask(px, False)); x += px + 30
    x = 30
    for px in (300, 180, 120, 80, 58, 40):
        crop = back.crop((N // 6, N // 6, N - N // 6, N - N // 6)).resize((px, px), Image.LANCZOS)
        sheet.paste(crop, (x, 400), mask(px, True)); x += px + 30
    sheet.save(os.path.join(preview, 'sheet.png'))
    print('wrote preview sheet')
