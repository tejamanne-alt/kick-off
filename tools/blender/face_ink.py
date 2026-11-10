# Gives a scanned kid's own face the finish of Max's painted one, without redrawing it (docs/LEARNINGS.md, the kids'
# faces): their eyes, brows, nose and mouth stay exactly where and as big as the scan made them; only the drawing changes.
#   blenv/bin/python face_ink.py -- <Name> <in.fbx> <in atlas.png> <out atlas.png> [--review review.png]
#   (Name: PrimaryBoy (Kai), PrimaryBoy2 (Leo), PrimaryGirl (Mia), PrimaryGirl2 (Zoe))
#
# Why not face_paint.py: it drew new eyes, brows and a mouth from a style sheet, sized from the distance between the
# eyes, and the kids came out with big doll eyes and tiny strokes for a nose and mouth: alien, not like Max. Max's face
# reads as drawn because of its finish, not its shapes: one even skin tone, a bold dark line along the top of each eye,
# solid brows, a clean white and iris, and a single line for the mouth. So this keeps the scan's shapes and gives them that
# finish:
#   - each eye's opening (its white and iris) is found in the scan, and a dark lash line is drawn along its own top edge,
#     thin at the inner corner and fuller at the outer one (a small flick for the girls), with a faint line under it;
#     the white is cleaned toward white and the iris gets a little more contrast; the scan's highlights stay;
#   - each brow keeps its own outline, filled with one dark brown (its own darkest colour, warmed toward the hair's);
#   - the parting of the lips is darkened along its own curve; the lips keep their colour;
#   - the skin is flattened (an edge-preserving filter, then halfway toward its own smooth tone), so the scan's pores and
#     blotches go and the features stand out on an even tone, as on Max.
# The work happens in a front view of the head (face_paint.Head: every atlas texel placed in 3D), and only the change is
# carried back to the atlas texels (divided by the vertex colour the game multiplies by), so whatever is not changed
# keeps the atlas' own sharpness. No vertex moves.
import sys, os, json
import numpy as np
import cv2
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_paint as fp
from polish_lib import push_pull, load_png, save_png

C, SS = fp.C, fp.SS
INK = (36, 24, 28)
# per kid: the lash line's weight, the outer-corner flick (the girls), the brows' share of the hair's brown
# (taper: how much the line thins again at the outer corner; the boys' lines end there, the girls' turn into the flick)
STYLES = {
    'PrimaryBoy': dict(lash=0.9, flick=0.0, taper=0.55),
    'PrimaryBoy2': dict(lash=0.95, flick=0.0, taper=0.55),
    'PrimaryGirl': dict(lash=1.05, flick=0.45, taper=0.0),
    'PrimaryGirl2': dict(lash=1.05, flick=0.45, taper=0.0),
}


def line(dr, pts, widths, fill):
    """A stroke along a polyline with a width at each point."""
    pts = np.asarray(pts, float)
    tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
    nor = np.stack([-tang[:, 1], tang[:, 0]], 1)
    w = np.asarray(widths, float)[:, None] / 2
    fp.poly(dr, list(map(tuple, np.concatenate([pts + nor * w, (pts - nor * w)[::-1]]))), fill)


def ellipse(cx, cy, rx, ry, soft=0.25):
    yy, xx = np.mgrid[0:C, 0:C].astype(np.float32)
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return np.clip((1 - r) / soft, 0, 1)


def clean_shape(a, s, lo, hi, min_area):
    """A soft mask made into a clean shape: blurred, re-thresholded with an anti-aliased edge, specks dropped."""
    b = ndimage.gaussian_filter(a.astype(np.float32), s)
    b = np.clip((b - lo) / (hi - lo), 0, 1); b = b * b * (3 - 2 * b)
    lab, k = ndimage.label(b > 0.5)
    if k:
        sz = ndimage.sum(np.ones_like(b), lab, range(1, k + 1))
        keep = np.zeros(k + 1, bool); keep[1:] = sz >= min_area
        b = b * ndimage.binary_dilation(keep[lab], iterations=2)
    return b


def opening(img, L, Ls, dark, ex, ey, D):
    """The eye's opening (its white and its iris) around the found eye, as a mask."""
    z = ellipse(ex, ey, 0.42 * D, 0.24 * D) > 0.2
    sat = img.max(2) - img.min(2)
    white = z & (L > Ls * 1.12) & (sat < 0.3)
    iris = z & (dark > 0.42)
    op = ndimage.binary_closing(white | iris, iterations=2)
    op = ndimage.binary_opening(ndimage.binary_fill_holes(op), iterations=1)
    lab, k = ndimage.label(op)
    if k == 0: return None, None
    dist = [np.hypot(*(np.array(ndimage.center_of_mass(lab == i)) - (ey, ex))) for i in range(1, k + 1)]
    op = lab == (int(np.argmin(dist)) + 1)
    return op, white & op


def edge_curve(op, top, deg=3):
    """The opening's top (or bottom) edge as a smooth curve: (x, y) points from its left end to its right."""
    ys, xs = np.nonzero(op)
    cols = np.arange(xs.min(), xs.max() + 1)
    ey = np.array([ys[xs == c].min() if top else ys[xs == c].max() for c in cols], float)
    cnt = np.array([(xs == c).sum() for c in cols])
    ok = cnt >= 2
    co = np.polyfit(cols[ok], ey[ok], deg, w=np.sqrt(cnt[ok]))
    x = np.linspace(cols[0] - 0.5, cols[-1] + 0.5, 48)
    return np.stack([x, np.polyval(co, x)], 1)


def lip_line(img, dark, mx, my, D):
    """The lips' parting: in each column round the mouth's middle, the darkest row; fitted with a gentle curve."""
    xs = np.arange(int(mx - 0.26 * D), int(mx + 0.26 * D) + 1)
    y0, y1 = int(my - 0.12 * D), int(my + 0.12 * D)
    rows, ws = [], []
    for x in xs:
        col = ndimage.gaussian_filter1d(dark[y0:y1, x], 1.0)
        rows.append(y0 + int(np.argmax(col))); ws.append(col.max())
    rows = np.array(rows, float); ws = np.array(ws)
    if np.median(ws) < 0.12: return None           # no clear parting: leave the mouth as it is
    co = np.polyfit(xs, rows, 2, w=ws + 1e-3)
    if abs(co[0]) * (0.26 * D) ** 2 > 0.08 * D: co = np.polyfit(xs, rows, 1, w=ws + 1e-3)   # no wild bends
    x = np.linspace(xs[0], xs[-1], 32)
    return np.stack([x, np.polyval(co, x)], 1)


def finish(head, name, spec):
    """The face in front view, before and after."""
    st = STYLES[name]
    img, filled = fp.front_view(head)
    img = img.astype(np.float32)
    skin, _ = fp.smooth_skin(head)
    L = img.mean(2); Ls = skin.mean(2)
    dark = np.clip((Ls - L) / np.maximum(Ls, 1e-3), 0, 1)
    D = spec['d']
    # 1) the skin: an edge-preserving filter, then plain skin halfway toward its own smooth tone
    out = img.copy()
    for _ in range(2):
        out = cv2.bilateralFilter(out, 0, 0.06, 5.0)
    eyes = np.maximum.reduce([ellipse(x, y, 0.4 * D, 0.24 * D) for x, y in spec['eyes']])
    brows = np.maximum.reduce([ellipse(x, y, 0.36 * D, 0.15 * D) for x, y in spec['brows']])
    mouth = ellipse(spec['mouth'][0], spec['mouth'][1], 0.34 * D, 0.16 * D)
    nose = ellipse(spec['nose'][0], spec['nose'][1] + 0.12 * D, 0.22 * D, 0.16 * D)
    feat = np.maximum.reduce([eyes, brows, mouth, nose])
    chroma = img / np.maximum(img.sum(2, keepdims=True), 1e-3); mc = np.median(chroma[filled], 0)
    plain = filled & (np.abs(chroma - mc).sum(2) < 0.08) & (dark < 0.25)
    plain = ndimage.gaussian_filter(plain.astype(np.float32), 1.5) * (1 - feat)
    out = out + (skin - out) * (0.5 * plain)[..., None]
    # 2) the brows: their own outline, one dark brown
    for (bx, by) in spec['brows']:
        z = ellipse(bx, by, 0.36 * D, 0.15 * D)
        m = (z > 0.5) & filled
        if m.sum() < 20: continue
        dk = m & (L <= np.percentile(L[m], 15))
        col = 0.5 * np.median(img[dk], 0) * 0.8 + 0.5 * np.array(fp.STYLES[name]['brow'], np.float32) / 255
        a = clean_shape(np.clip((dark - 0.14) / 0.12, 0, 1) * (z > 0.05), 1.2, 0.35, 0.65, 40) * z
        # mostly the one brown, a little of the brow's own hairs left in it (so it is drawn, not a cut-out)
        fill = col * 0.8 + np.minimum(img, col * 1.6) * 0.2
        out = out * (1 - 0.92 * a[..., None]) + fill * 0.92 * a[..., None]
    # 3) the eyes: a clean white, a little more contrast in the iris, then the lines drawn over
    lines = Image.new('RGBA', (C * SS, C * SS), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lines)
    cxm = (spec['eyes'][0][0] + spec['eyes'][1][0]) / 2
    for (ex, ey) in spec['eyes']:
        op, white = opening(img, L, Ls, dark, ex, ey, D)
        if op is None: continue
        wm = ndimage.gaussian_filter(white.astype(np.float32), 0.8)[..., None]
        out = out * (1 - 0.6 * wm) + np.array([0.96, 0.95, 0.95], np.float32) * 0.6 * wm
        im = ndimage.gaussian_filter((op & ~white).astype(np.float32), 0.8)[..., None]
        imean = np.median(out[op & ~white], 0) if (op & ~white).any() else out[int(ey), int(ex)]
        out = out * (1 - im) + np.clip(imean + (out - imean) * 1.2, 0, 1) * im
        outer_left = ex < cxm                       # the outer corner is on the side away from the nose
        up = edge_curve(op, True)
        lo = edge_curve(op, False)
        if outer_left: up, lo = up[::-1], lo[::-1]  # inner corner first
        th0, th1 = 0.016 * D * st['lash'], 0.048 * D * st['lash']
        t = np.linspace(0, 1, len(up))
        grow = np.clip(t / 0.75, 0, 1); grow = grow * grow * (3 - 2 * grow)
        wid = th0 + (th1 - th0) * grow
        wid *= 1 - st['taper'] * np.clip((t - 0.8) / 0.2, 0, 1) ** 1.5      # the boys' lines thin out at the corner
        wid *= np.clip(t / 0.08, 0.35, 1)                                      # and every line starts thin at the inner one
        centre = up + np.array([0, 1.0]) * (0.35 * wid)[:, None]
        line(dr, centre[1:], wid[1:], INK + (255,))
        if st['flick'] > 0:
            s = -1 if outer_left else 1
            tip = centre[-1] + np.array([s * 0.07 * D * st['flick'], -0.06 * D * st['flick']])
            fp.stroke(dr, fp.bez(centre[-5], centre[-1] + [s * 0.015 * D, -0.005 * D], tip, 10), th1, 0.006 * D, INK + (255,), swell=0.0)
        n = len(lo)
        fp.stroke(dr, lo[int(n * 0.3):-2], 0.008 * D, 0.014 * D, INK + (120,), swell=0.3)
    # 4) the mouth: the lips' parting along its own curve
    ll = lip_line(img, dark, spec['mouth'][0], spec['mouth'][1], D)
    if ll is not None:
        mid = ll[len(ll) // 2]
        lip = np.median(img[(mouth > 0.5) & (dark > 0.05)], 0) if ((mouth > 0.5) & (dark > 0.05)).any() else img[int(mid[1]), int(mid[0])]
        col = tuple(int(c) for c in np.clip(lip * 0.45 * 255, 0, 255))
        fp.stroke(dr, ll, 0.012 * D, 0.012 * D, col + (200,), swell=0.5)
    ln = np.asarray(lines.resize((C, C), Image.LANCZOS)).astype(np.float32) / 255
    out = fp.over(out, ln)
    out = np.where(filled[..., None], np.clip(out, 0, 1), img)
    return img, out, filled


def apply(head, spec, before, after):
    """The change from before to after carried back to the face's atlas texels, fading out round the face's oval and
    toward the sides, the hairline and the neck (the same reach as face_paint)."""
    yy, xx = head.cy, head.cx
    D = spec['d']
    fcx = (spec['eyes'][0][0] + spec['eyes'][1][0]) / 2
    fcy = (spec['eyes'][0][1] + spec['mouth'][1]) / 2
    ro = np.sqrt(((xx - fcx) / (D * 1.05)) ** 2 + ((yy - fcy) / (D * 1.0)) ** 2)
    front = np.clip((head.facing - 0.12) / 0.3, 0, 1)
    under = (ro < 1.0) & (head.facing > -0.6) & (head.depth > 0.03)
    oval = np.clip((1.3 - ro) / 0.3, 0, 1)
    k = np.maximum(front, under * 1.0) * oval * np.clip((head.hw - 0.5) / 0.3, 0, 1)
    sel = (head.hw > 0.5) & (head.part == 0) & ((front > 0) | under)
    delta = (head.sample(after) - head.sample(before)) / np.maximum(head.vc, 0.05)
    A = head.A.copy()
    flat = A.reshape(-1, 3)
    idx = np.flatnonzero(head.m.ravel())
    w = (k * sel)[:, None]
    flat[idx] = np.clip(flat[idx] + delta * w, 0, 1)
    return flat.reshape(A.shape), sel


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    name, fbx, atlas_in, atlas_out = argv[:4]
    review = argv[argv.index('--review') + 1] if '--review' in argv else None
    arrays = argv[argv.index('--arrays') + 1] if '--arrays' in argv else None   # cached mesh_arrays (npz), for iterating
    d = dict(np.load(arrays)) if arrays and os.path.exists(arrays) else fp.mesh_arrays(fbx)
    atlas = load_png(atlas_in)
    head = fp.Head(d, atlas)
    found = fp.detect(head)
    spec = fp.spec_for(name, found)
    before, after, filled = finish(head, name, spec)
    out, sel = apply(head, spec, before, after)
    if review:
        res, _ = head.splat(out.reshape(-1, 3)[np.flatnonzero(head.m.ravel())] * head.vc, sel)
        save_png(np.concatenate([before, after, res], 1), review)
    if atlas.shape[2] == 4:
        out = np.concatenate([out, atlas[..., 3:4]], 2)
    save_png(push_pull(out, head.cov), atlas_out)
    print('[face_ink]', name, json.dumps({'eyes': np.round(spec['eyes'], 1).tolist(), 'mouth': np.round(spec['mouth'], 1).tolist()}))
