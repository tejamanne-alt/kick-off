# Cuts a model sheet (docs/KAMAKURA_BUILD.md, "the model sheet base prompt") into its four views, ready to upload to
# Meshy's Multi-Image to 3D: <name>_1_front.png, _2_right.png, _3_back.png, _4_three_quarter.png.
#   python3 tools/blender/crop_sheet_views.py <sheet.png | sheets dir> <out dir>
# A square sheet is a 2 x 2 grid (front, right / back, three-quarter); a sheet about four times as wide as it is tall is
# taken as one row of four in the same order. Each view is trimmed of the thin gap between panels and saved as RGB.
import os
import sys

from PIL import Image

VIEWS = ['1_front', '2_right', '3_back', '4_three_quarter']
GAP = 0.02    # of a panel's side, trimmed off each edge (the gap between panels and any line drawn along it)


def panels(size):
    w, h = size
    ratio = w / h
    if 0.8 <= ratio <= 1.25:
        cols, rows = 2, 2
    elif 3.2 <= ratio <= 4.8:
        cols, rows = 4, 1
    else:
        raise SystemExit('crop_sheet_views.py: a sheet must be square (2 x 2) or about 4:1 (a row of four), not %d x %d' % (w, h))
    pw, ph = w / cols, h / rows
    boxes = []
    for i in range(4):
        c, r = i % cols, i // cols
        x0, y0 = c * pw + GAP * pw, r * ph + GAP * ph
        boxes.append((round(x0), round(y0), round(x0 + pw * (1 - 2 * GAP)), round(y0 + ph * (1 - 2 * GAP))))
    return boxes


def crop(path, out_dir):
    name = os.path.splitext(os.path.basename(path))[0]
    im = Image.open(path).convert('RGB')
    written = []
    for view, box in zip(VIEWS, panels(im.size)):
        out = os.path.join(out_dir, '%s_%s.png' % (name, view))
        im.crop(box).save(out)
        written.append(out)
    return written


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__ or 'usage: crop_sheet_views.py <sheet.png | sheets dir> <out dir>')
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    sheets = [os.path.join(src, f) for f in sorted(os.listdir(src)) if f.lower().endswith('.png')] if os.path.isdir(src) else [src]
    for s in sheets:
        for w in crop(s, out_dir):
            print(w)


if __name__ == '__main__':
    main()
