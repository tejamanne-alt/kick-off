"""A prop built from its own views (BASE KM-S0, docs/KAMAKURA_BUILD.md Step 0; docs/LEARNINGS.md D24): front, right side,
back, top and three-quarter, each a full-size image of the object alone on an even grey, made by the user in ChatGPT or
Gemini and saved in review/kamakura/sheets/<id>_<name>/.

1. Each view's object is cut from its grey (what differs from it, or is textured); a view in halves (a pole too tall for
   one image) is stitched where the halves overlap.
2. The views are sized and registered by the object, not its box (D25): the front and the right side set the width,
   depth and height (the real height given); the back is slid and stretched across until its outline best covers the
   front's mirrored, the top until its extent matches the front's and the side's.
3. The solid is carved as a field (each outline's signed distance) on a grid 1 to 2 cm apart: inside the front's and the
   side's outlines, and inside the top's in each horizontal slice where that only hollows the slice (a top drawn
   otherwise, a barrier's arm lowered in it, is left out there). In the heights given, posts the top cannot see under a
   beam are made round in section; parts thinner than a few centimetres are left to the texture.
4. Its surface is extracted (surface nets), re-meshed closed and manifold, reduced to the triangle budget and unwrapped,
   the faces toward the street given twice the texels.
5. Its texture is baked from the views: each point takes the views that face it and can see it (the carved solid says
   what hides what), sharply weighted by how squarely each faces it: the front, the back, the right side, the left
   (its own view, or the right side's), the top. The three-quarter view is for checking (the review board).

Object frame: x along the street (the front's left to right), y away from the street (the front at -y), z up from the
ground; the origin on the ground under the middle."""
import math
import os

import cv2
import numpy as np
from PIL import Image

VIEWS = ('front', 'right', 'back', 'top', 'three')


# ---------------------------------------------------------------- the views
def read_views(folder):
    """{view: RGB uint8 array}: each view's image, a view in halves stitched. File names as the user saved them:
    1_front.png, 2_right_side.png or 2_right.png, ...; halves as 1_front_top_half.png and 2_front_bottom_half.png, or
    1_front_left.png and 1_front_right.png."""
    parts = {}
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        toks = os.path.splitext(f.lower())[0].split('_')
        toks = [t for t in toks if not t.isdigit()]
        part = None
        if 'half' in toks:
            part = toks[toks.index('half') - 1]
            toks = [t for t in toks if t not in ('half', part)]
        view = next((t for t in toks if t in VIEWS), None)
        if view is None and 'three' in f.lower():
            view = 'three'
        if view is None:
            continue
        if part is None and len(toks) > 1 and toks[-1] in ('left', 'right', 'top', 'bottom') and toks[0] != toks[-1]:
            part = toks[-1]
        im = np.asarray(Image.open(os.path.join(folder, f)).convert('RGB'))
        parts.setdefault(view, {})[part] = im
    out = {}
    for view, ps in parts.items():
        if None in ps:
            out[view] = ps[None]
        elif 'top' in ps and 'bottom' in ps:
            out[view] = stitch(ps['top'], ps['bottom'], vertical=True)
        elif 'left' in ps and 'right' in ps:
            out[view] = stitch(ps['left'], ps['right'], vertical=False)
    return out


def stitch(a, b, vertical=True):
    """Two halves of one view (a: the top or left, b: the bottom or right), overlapping: b's start found in a by matching a
    band of a's end inside b, then b laid on from there."""
    if not vertical:
        return np.transpose(stitch(np.transpose(a, (1, 0, 2)), np.transpose(b, (1, 0, 2))), (1, 0, 2))
    ha, wa = a.shape[:2]
    hb = b.shape[0]
    band = a[ha - 260:ha - 40]
    m = object_mask(a)
    cols = np.nonzero(m[ha - 260:ha - 40].any(0))[0]
    x0, x1 = (max(0, cols.min() - 40), min(wa, cols.max() + 40)) if len(cols) else (0, wa)
    tpl = cv2.cvtColor(np.ascontiguousarray(band[:, x0:x1]), cv2.COLOR_RGB2GRAY)
    search = cv2.cvtColor(np.ascontiguousarray(b[:min(hb, 900)]), cv2.COLOR_RGB2GRAY)
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (bx, by) = cv2.minMaxLoc(res)
    # a's row ha - 260 is b's row by, its column x0 is b's column bx
    dy = (ha - 260) - by
    dx = x0 - bx
    H = dy + hb
    W = max(wa, b.shape[1] + max(0, dx))
    out = np.full((H, W, 3), np.median(a[:8].reshape(-1, 3), 0).astype(np.uint8), np.uint8)
    out[:ha, :wa] = a
    xs = max(0, dx)
    seam = ha - 150                     # a above the seam, b below it (in the overlap)
    out[seam:dy + hb, xs:xs + b.shape[1]] = b[seam - dy:, :min(b.shape[1], W - xs)]
    stitch.last_score = score
    return out


def object_mask(im, thresh=24.0, tex=3.0, hole_fill=0.004):
    """The object in a view: what differs from the even grey around it, or is textured; specks dropped, holes filled that
    are not the grey or are small (under hole_fill of the object: a slot's shadowed inside, not a gap through it)."""
    a = im.astype(np.float32)
    edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    bg = np.median(edge, 0)
    diff = np.abs(a - bg).sum(-1)
    g = a.mean(-1)
    mean = cv2.blur(g, (5, 5))
    dev = np.sqrt(np.maximum(cv2.blur(g * g, (5, 5)) - mean * mean, 0))
    m = ((diff > thresh) | (dev > tex)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        big = st[1:, 4].max()
        keep = 1 + np.nonzero(st[1:, 4] >= max(300, 0.004 * big))[0]
        m = np.isin(lab, keep).astype(np.uint8)
    inv = (1 - m).astype(np.uint8)
    hn, hl, hs, _ = cv2.connectedComponentsWithStats(inv, 4)
    small = max(60, hole_fill * m.sum())
    for i in range(1, hn):
        x, y, w, h, area = hs[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            hole = hl == i
            if area < small or np.abs(np.median(a[hole], 0) - bg).sum() > thresh:
                m[hole] = 1
    return m.astype(bool)


def bbox(m):
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


# ---------------------------------------------------------------- the solid
class Frame:
    """The views sized to one another and to the real height (each view's pixel mapping), and the solid carved from them
    as a field on a grid of nodes vox apart: negative inside, metres to the surface."""

    def __init__(self, views, height, vox=0.01, hole_fill=0.004, view_map=None, cutout=False, thin=0.0):
        """views: {view: image}; view_map renames the user's views where an image was made from another side than its
        name says (a bicycle's 'back' from its rear end: {'back': 'left'}). A side with no view of its own takes the
        opposite side's (a far side looks like the near one): the back the front's, the left the right's. cutout: each
        view's alpha is the object's own outline, its gaps open (a wheel's spokes), for a cut-out material. thin: what is
        thinner than this many metres in a view (a pole's step bolts, a hanging cable) is left out of the solid, shown
        only by the texture where it crosses the solid."""
        views = {(view_map or {}).get(k, k): v for k, v in views.items()}
        self.views = views
        self.masks = {k: object_mask(v, hole_fill=hole_fill) for k, v in views.items() if k != 'three'}
        self.box = {k: bbox(m) for k, m in self.masks.items()}
        self.src = {k: k for k in self.masks}
        self.src.setdefault('back', 'front')
        self.src.setdefault('left', 'right')
        fx0, fy0, fx1, fy1 = self.box['front']
        sx0, sy0, sx1, sy1 = self.box['right']
        self.H = height
        self.scale = {k: (self.box[k][3] - self.box[k][1]) / height for k in self.masks if k != 'top'}
        self.W = (fx1 - fx0) / self.scale['front']
        self.D = (sx1 - sx0) / self.scale['right']
        # each view's mapping (u0, su, v0, sv): u = u0 + a su along its width (a metres from its own left edge), v = v0 - c sv
        # (c the height, or for the top the depth from the front). The front and the right side set the width and depth;
        # the others are registered to them: slid (and the top scaled) until their outline's extent along the street (the
        # columns any part of it reaches) or into it best matches the front's or the side's (a protruding cable or arm in
        # one view moves its box, not its object)
        self.map = {'front': (fx0, self.scale['front'], fy1, self.scale['front']),
                    'right': (sx0, self.scale['right'], sy1, self.scale['right'])}
        ref_x = self._profile('front', self.W)
        ref_y = self._profile('right', self.D)
        for k, opp, L in (('back', 'front', self.W), ('left', 'right', self.D)):
            if k in self.masks:
                self.map[k] = self._register_opposite(k, opp, L)
        if 'top' in self.masks:
            tx0, ty0, tx1, ty1 = self.box['top']
            s0 = (tx1 - tx0) / self.W
            u0, su = self._register(self.masks['top'].any(0), ref_x, self.W, s0 * np.linspace(0.85, 1.15, 31), tx0)
            rows = self.masks['top'].any(1)[::-1]       # from the bottom (the front) up
            H = len(rows)
            t0 = (ty1 - ty0) / self.D
            r0, sv = self._register(rows, ref_y, self.D, t0 * np.linspace(0.85, 1.15, 31), H - ty1)
            self.map['top'] = (u0, su, H - 1 - r0, sv)
        self.scale.update({k: v[1] for k, v in self.map.items()})
        if thin > 0:
            for k, m in self.masks.items():
                r = max(1, int(round(thin * self.scale[k] / 2)))
                ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
                self.masks[k] = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, ker).astype(bool)
        self.rgba = {}
        for k in self.masks:
            alpha = object_mask(views[k], hole_fill=0.0) if cutout else np.ones(self.masks[k].shape, bool)
            self.rgba[k] = np.dstack([views[k], alpha.astype(np.uint8) * 255])
        self.vox = vox
        pad = 3 * vox
        self.xs = np.arange(-self.W / 2 - pad, self.W / 2 + pad + vox, vox)
        self.ys = np.arange(-self.D / 2 - pad, self.D / 2 + pad + vox, vox)
        self.zs = np.arange(-pad, self.H + pad + vox, vox)
        self.origin = np.array([self.xs[0], self.ys[0], self.zs[0]])
        self._sdf = {}

    def _profile(self, view, L, step=0.002):
        """Which points along the view's width axis (metres from its left edge, -10 % to 110 % of L) the object reaches."""
        a = np.arange(-0.1 * L, 1.1 * L, step)
        u0, su = self.map[view][:2]
        cols = self.masks[view].any(0)
        u = np.round(u0 + a * su).astype(int)
        return np.where((u >= 0) & (u < len(cols)), cols[np.clip(u, 0, len(cols) - 1)], False)

    def _register_opposite(self, view, opp, L, step=4):
        """The mapping of a view from the side opposite opp: its outline, read right to left, slid along (and stretched
        across, by up to 8 %) until it best covers opp's (the area of both, so a body counts more than a thin arm drawn
        at another angle)."""
        u0o, so, v0o, _ = self.map[opp]
        x0, y0, x1, y1 = self.box[opp]
        m = self.masks[opp]
        vs, us = np.mgrid[y0:y1:step, x0:x1:step]
        ref = m[vs, us]
        a = (us - u0o) / so                             # metres from opp's left edge
        z = (v0o - vs) / so
        mv = self.masks[view]
        s = self.scale[view]
        bx0, by0, bx1, by1 = self.box[view]
        v = np.clip(np.round(by1 - z * s).astype(int), 0, mv.shape[0] - 1)
        best = (-1, bx0, s)
        span = int(0.15 * L * s) + 1
        for sh in s * np.linspace(0.92, 1.08, 17):      # drawn a little wider or narrower than its height says
            for u0 in range(bx0 - span, bx0 + span + 1, 2):
                u = np.round(u0 + (L - a) * sh).astype(int)
                ok = (u >= 0) & (u < mv.shape[1])
                c = ok & mv[v, np.clip(u, 0, mv.shape[1] - 1)]
                iou = (c & ref).sum() / max((c | ref).sum(), 1)
                if iou > best[0]:
                    best = (iou, u0, sh)
        return best[1], best[2], by1, s

    @staticmethod
    def _register(cols, ref, L, scales, guess, flip=False, step=0.002):
        """The offset and scale (from scales) best laying cols (a view's columns reached) over ref (_profile's), the view
        read right to left if flip; offsets searched 15 % of its width either side of guess."""
        a = np.arange(-0.1 * L, 1.1 * L, step)
        if flip:
            a = L - a
        best = (-1, guess, scales[0])
        for s in scales:
            span = int(0.15 * L * s) + 1
            for u0 in range(int(guess) - span, int(guess) + span + 1):
                u = np.round(u0 + a * s).astype(int)
                c = np.where((u >= 0) & (u < len(cols)), cols[np.clip(u, 0, len(cols) - 1)], False)
                iou = (c & ref).sum() / max((c | ref).sum(), 1)
                if iou > best[0]:
                    best = (iou, u0, s)
        return best[1], best[2]


    def px(self, view, P):
        """Metres to the pixels (u right, v down) of the image the view takes its colours from: its own, or for a side with
        none, the opposite side's at the same place."""
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        src = self.src[view]
        u0, su, v0, sv = self.map[src]
        if src == 'top':                                # seen from above, the front at the bottom
            return u0 + (x + self.W / 2) * su, v0 - (y + self.D / 2) * sv
        a = {'front': lambda: x + self.W / 2,           # seen from -y: x to the right
             'back': lambda: self.W / 2 - x,            # from +y
             'right': lambda: y + self.D / 2,           # from +x: the front (-y) on its left
             'left': lambda: self.D / 2 - y}[src]()     # from -x
        return u0 + a * su, v0 - z * sv

    def image(self, view):
        return self.rgba[self.src[view]]

    def sdf(self, view, P):
        """The view's silhouette as a signed distance in metres (negative inside), at the points P seen from the view."""
        if view not in self._sdf:
            m = self.masks[view].astype(np.uint8)
            inside = cv2.distanceTransform(m, cv2.DIST_L2, 5)
            outside = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
            self._sdf[view] = (outside - inside).astype(np.float32)
        u, v = self.px(view, P)
        return remap(self._sdf[view], u, v, cv2.BORDER_CONSTANT, 1e4).reshape(-1) / self.scale[view]

    def carve(self, top='auto', round_z=(), round_max=1.6, round_w=0.3, top_cover=0.9):
        """The field: inside where the front and the right side both show the object. Each horizontal slice also inside the
        top view where the top agrees with it (top='auto': cut by the top, the slice still reaches top_cover of what the
        front and the side show at that height, so the top only hollows it, a frame open from above; 'always'; False:
        never; a top drawn otherwise, a barrier's arm lowered in it, is left out there). In the
        heights round_z ((z0, z1) pairs), each round piece of a slice (its sides within round_max of each other, neither
        over round_w metres) made round in section: a post, under a beam the top view cannot see past."""
        xs, ys, zs = self.xs, self.ys, self.zs
        gx, gz = np.meshgrid(xs, zs, indexing='ij')
        F = self.sdf('front', np.stack([gx.ravel(), np.zeros(gx.size), gz.ravel()], 1)).reshape(gx.shape)
        gy, gz = np.meshgrid(ys, zs, indexing='ij')
        S = self.sdf('right', np.stack([np.zeros(gy.size), gy.ravel(), gz.ravel()], 1)).reshape(gy.shape)
        field = np.maximum(F[:, None, :], S[None, :, :]).astype(np.float32)
        self.F = F
        T = None
        if top and 'top' in self.masks:
            gx, gy = np.meshgrid(xs, ys, indexing='ij')
            T = self.sdf('top', np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], 1)).reshape(gx.shape)
        self.slices = {'top': 0, 'round': 0}
        for k, z in enumerate(zs):
            inside = field[:, :, k] < 0
            n = inside.sum()
            if not n:
                continue
            use_t = T is not None and (top == 'always' or self.top_agrees(inside, T < 0, top_cover))
            if use_t:
                field[:, :, k] = np.maximum(field[:, :, k], T)
                self.slices['top'] += 1
            if any(z0 <= z <= z1 for z0, z1 in round_z):
                E = self.round_pieces(inside, round_max, round_w)
                if E is not None:
                    field[:, :, k] = np.maximum(field[:, :, k], E)
                    self.slices['round'] += 1
        self.field = field
        self.V = field < 0
        return field

    @staticmethod
    def top_agrees(inside, T, cover):
        """Whether the slice cut by the top view still reaches cover of the columns and rows the slice reaches."""
        cut = inside & T
        ok = True
        for ax in (0, 1):
            want = inside.any(1 - ax)
            got = cut.any(1 - ax)
            ok &= (got & want).sum() >= cover * max(want.sum(), 1)
        return bool(ok)

    def round_pieces(self, inside, round_max, round_w):
        """A slice's constraint: each round piece's ellipse (signed distance, metres); none on the others."""
        n, lab, st, _ = cv2.connectedComponentsWithStats(inside.astype(np.uint8), 8)
        big = 1e3
        E = np.full(inside.shape, big, np.float32)
        anyround = False
        for c in range(1, n):
            y, x, h, w, area = st[c]                    # cv2's x runs along j (y), its y along i (x)
            i0, j0, ni, nj = x, y, w, h
            a, b = ni * self.vox / 2, nj * self.vox / 2
            pad = 4
            I0, J0 = max(i0 - pad, 0), max(j0 - pad, 0)
            I1, J1 = min(i0 + ni + pad, inside.shape[0]), min(j0 + nj + pad, inside.shape[1])
            if max(a, b) > round_max * min(a, b) or min(ni, nj) < 3 or 2 * max(a, b) > round_w:
                E[I0:I1, J0:J1] = -big
                continue
            ci, cj = i0 + (ni - 1) / 2, j0 + (nj - 1) / 2
            ii, jj = np.mgrid[I0:I1, J0:J1]
            dx, dy = (ii - ci) * self.vox, (jj - cj) * self.vox
            e = (np.sqrt((dx / a) ** 2 + (dy / b) ** 2) - 1) * min(a, b)
            E[I0:I1, J0:J1] = np.minimum(E[I0:I1, J0:J1], e)
            anyround = True
        return E if anyround else None

    def grid(self):
        """The nodes' coordinates, each (nx, ny, nz)."""
        return np.meshgrid(self.xs, self.ys, self.zs, indexing='ij')


def surface_nets(field, vox, origin):
    """The field's zero surface as quads (naive surface nets): one vertex in each cell the surface crosses, at the mean of
    its edges' crossings; one quad across each crossed edge. Closed and outward-facing where the field is negative inside."""
    f = np.pad(field, 1, constant_values=1e3)
    nx, ny, nz = f.shape
    inside = f < 0
    acc = np.zeros((nx - 1, ny - 1, nz - 1, 3), np.float64)
    cnt = np.zeros((nx - 1, ny - 1, nz - 1), np.int32)
    for axis in range(3):
        a = [slice(None)] * 3
        b = [slice(None)] * 3
        a[axis] = slice(0, -1)
        b[axis] = slice(1, None)
        fa, fb = f[tuple(a)], f[tuple(b)]
        cross = (fa < 0) != (fb < 0)
        t = np.where(cross, fa / np.where(cross, fa - fb, 1), 0)
        # each crossed edge's point, in node units, added to the four cells around it
        idx = np.indices(fa.shape).astype(np.float64)
        idx[axis] += t
        pts = np.moveaxis(idx, 0, -1)
        others = [ax for ax in range(3) if ax != axis]
        for du in (0, 1):
            for dw in (0, 1):
                sl = [slice(None)] * 3
                sl[others[0]] = slice(du, du + f.shape[others[0]] - 1)
                sl[others[1]] = slice(dw, dw + f.shape[others[1]] - 1)
                c = cross[tuple(sl)]
                acc += np.where(c[..., None], pts[tuple(sl)], 0)
                cnt += c
    has = cnt > 0
    vid = np.full(cnt.shape, -1, np.int64)
    vid[has] = np.arange(has.sum())
    verts = acc[has] / cnt[has][:, None]
    verts = (verts - 1) * vox + origin                  # the pad shifted every node by one
    quads = []
    for axis in range(3):
        a = [slice(None)] * 3
        b = [slice(None)] * 3
        a[axis] = slice(0, -1)
        b[axis] = slice(1, None)
        fa, fb = f[tuple(a)], f[tuple(b)]
        cross = (fa < 0) != (fb < 0)
        u, w = [ax for ax in range(3) if ax != axis]
        e = np.argwhere(cross)
        e = e[(e[:, u] >= 1) & (e[:, w] >= 1) & (e[:, u] < f.shape[u] - 1) & (e[:, w] < f.shape[w] - 1)]
        corners = []
        for du, dw in ((-1, -1), (0, -1), (0, 0), (-1, 0)):
            c = e.copy()
            c[:, u] += du
            c[:, w] += dw
            corners.append(vid[c[:, 0], c[:, 1], c[:, 2]])
        q = np.stack(corners, 1)
        ins = fa[e[:, 0], e[:, 1], e[:, 2]] < 0         # inside at the edge's low end: the surface faces +axis
        flip = ins if axis == 1 else ~ins
        q[flip] = q[flip][:, ::-1]
        quads.append(q)
    quads = np.concatenate(quads)
    return verts, quads[(quads >= 0).all(1)]


# ---------------------------------------------------------------- the texture
NORMALS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'right': (1, 0, 0), 'left': (-1, 0, 0), 'top': (0, 0, 1)}


def first_hits(frame):
    """For each line of sight of each view, the node index where it first meets the solid."""
    V = frame.V
    big = 10 ** 6
    f = {}
    any_y, any_x, any_z = V.any(1), V.any(0), V.any(2)
    f['front'] = np.where(any_y, V.argmax(1), big)                                      # [i, k]
    f['back'] = np.where(any_y, V.shape[1] - 1 - V[:, ::-1, :].argmax(1), -big)
    f['left'] = np.where(any_x, V.argmax(0), big)                                       # [j, k]
    f['right'] = np.where(any_x, V.shape[0] - 1 - V[::-1, :, :].argmax(0), -big)
    f['top'] = np.where(any_z, V.shape[2] - 1 - V[:, :, ::-1].argmax(2), -big)          # [i, j]
    return f


def visible(frame, hits, view, P, tol=2.5):
    """Whether each point P (metres, on the surface) is on what the view sees."""
    n = np.round((P - frame.origin) / frame.vox).astype(int)
    i = np.clip(n[:, 0], 0, frame.V.shape[0] - 1)
    j = np.clip(n[:, 1], 0, frame.V.shape[1] - 1)
    k = np.clip(n[:, 2], 0, frame.V.shape[2] - 1)
    fi = (P - frame.origin) / frame.vox
    h = hits[view]
    if view == 'front':
        return fi[:, 1] <= h[i, k] + tol
    if view == 'back':
        return fi[:, 1] >= h[i, k] - tol
    if view == 'left':
        return fi[:, 0] <= h[j, k] + tol
    if view == 'right':
        return fi[:, 0] >= h[j, k] - tol
    return fi[:, 2] >= h[i, j] - tol


def remap(img, u, v, border=cv2.BORDER_REPLICATE, value=0.0):
    """Bilinear samples of img (one or three channels) at pixel coordinates (u, v), any number of them (cv2.remap takes at
    most 32767 a side, so they go in rows of 4096)."""
    m = len(u)
    cols = 4096
    rows = max(1, -(-m // cols))
    mx = np.zeros(rows * cols, np.float32)
    my = np.zeros(rows * cols, np.float32)
    mx[:m], my[:m] = u, v
    r = cv2.remap(img, mx.reshape(rows, cols), my.reshape(rows, cols), cv2.INTER_LINEAR, borderMode=border,
                  borderValue=value)
    return r.reshape(rows * cols, -1)[:m].astype(np.float32)


def sample(img, u, v):
    return remap(img, u, v)


def colours(frame, hits, P, N, views, sharp=8.0):
    """Each point's colour and alpha from the views that face and see it, weighted by how squarely each faces it."""
    acc = np.zeros((len(P), 4), np.float32)
    wsum = np.zeros(len(P), np.float32)
    for view in views:
        w = np.clip(N @ np.asarray(NORMALS[view], np.float32), 0, 1) ** sharp
        w = w * visible(frame, hits, view, P)
        sel = w > 1e-4
        if not sel.any():
            continue
        u, v = frame.px(view, P[sel])
        acc[sel] += sample(frame.image(view), u, v) * w[sel, None]
        wsum[sel] += w[sel]
    miss = wsum < 1e-3
    if miss.any():                                     # seen squarely by none: the nearest-facing view, shaded
        for view in views:
            w = (np.clip(N[miss] @ np.asarray(NORMALS[view], np.float32), 0, 1) + 0.05) ** 2
            u, v = frame.px(view, P[miss])
            acc[miss] += sample(frame.image(view), u, v) * w[:, None] * 0.7
            wsum[miss] += w
    return acc / np.maximum(wsum, 1e-6)[:, None]


def bake(frame, tri_pos, tri_uv, tri_nrm, size, views):
    """The texture (size x size, RGBA: the alpha the outline, for a cut-out): each triangle rasterised in UV space, each texel's colour from the views at its point on
    the solid; the islands' edges grown outward 8 texels so mipmaps don't bleed."""
    Ps, Ns, T = [], [], []
    for pos, uv, nrm in zip(tri_pos, tri_uv, tri_nrm):
        p = uv * size
        p[:, 1] = size - p[:, 1]                        # image rows run down
        x0, y0 = np.floor(p.min(0)).astype(int)
        x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l3 = 1 - l1 - l2
        e = -0.75 / max(np.abs(p[0] - p[1]).max(), np.abs(p[1] - p[2]).max(), 1)   # a little past the edge
        inside = (l1 >= e) & (l2 >= e) & (l3 >= e)
        if not inside.any():
            continue
        L = np.clip(np.stack([l1[inside], l2[inside], l3[inside]], 1), 0, 1)
        L /= L.sum(1, keepdims=True)
        Ps.append(L @ pos)
        Ns.append(L @ nrm)
        T.append(np.stack([(ys[inside] - 0.5).astype(int), (xs[inside] - 0.5).astype(int)], 1))
    P, N, T = np.concatenate(Ps), np.concatenate(Ns), np.concatenate(T)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    col = colours(frame, first_hits(frame), P, N, views)
    img = np.zeros((size, size, 4), np.float32)
    filled = np.zeros((size, size), bool)
    img[T[:, 0], T[:, 1]] = col
    filled[T[:, 0], T[:, 1]] = True
    for _ in range(8):                                  # each empty texel by a filled one: the mean of its filled neighbours
        fm = filled.astype(np.float32)
        acc, cnt = cv2.blur(img * fm[..., None], (3, 3)), cv2.blur(fm, (3, 3))
        new = ~filled & (cnt > 0)
        img[new] = acc[new] / cnt[new][:, None]
        filled |= new
    return np.clip(img + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- the props
SHEETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'review', 'kamakura', 'sheets')


def props():
    """KM1-1's props from their views: {model: (id, folder, height in metres, build options)}. The heights are the real
    ones (docs/KAMAKURA_BUILD.md Step 2); widths and depths come from the views' own proportions."""
    return {
        'KmPoleTransformer': ('KM-A01', 'KM-A01_concrete_utility_pole_with_transformer', 10.0,
                              dict(vox=0.02, round_z=[(0.0, 10.0)], round_w=0.7, thin=0.08)),
        'KmMirror': ('KM-A03', 'KM-A03_convex_corner_mirror', 3.8, dict(round_z=[(0.0, 2.9)], hole_fill=0.2)),
        'KmVendingBlue': ('KM-A19', 'KM-A19_blue_vending_machine', 1.83, dict()),
        'KmCrossingSignal': ('KM-A05', 'KM-A05_level_crossing_signal', 3.6, dict(round_z=[(0.95, 3.6)], round_w=0.2)),
        'KmCrossingBarrier': ('KM-A04', 'KM-A04_level_crossing_barrier', 4.5,
                              dict(round_z=[(1.75, 4.5)], round_w=0.15,
                                                                         parts=split_above(1.50, 'Arm', 1.56))),
        'KmToriiSmall': ('KM-A11', 'KM-A11_small_vermilion_torii', 2.6, dict(round_z=[(0.0, 1.75)])),
        'KmBicycle': ('KM-A08', 'KM-A08_city_bicycle', 1.15,
                      dict(view_map={'back': 'left'}, top='always', cutout=True, hole_fill=0.05,
                           shape=slab_below(0.68, 0.02))),
    }


NOTES = {           # each prop's own check results (asset_review: the seventeen checks), beside the general ones
    'KmPoleTransformer': {
        3: ('pass', 'carved from its front, side and top: the top used where it agrees with them (the crossarms, the '
                    'column), the column round in section'),
        12: ('pass', 'the step bolts and the cables, thinner than 8 cm, are in its texture only, not its solid'),
        13: ('pass', 'its front, side and back each made in two halves; joined where they overlap (the warning plate)'),
    },
    'KmMirror': {13: ('pass', 'the glass is as grey as the views\' background: its holes in the outline filled')},
    'KmVendingBlue': {11: ('pass', 'its logo panel reads うみかぜ, as the prompt asks (no real drink logo)')},
    'KmCrossingSignal': {3: ('limit', 'the post round in section; the guard frame solid: its front and side see its far '
                                      'bars through its near ones, and from above the crossbuck and lamps cover it')},
    'KmCrossingBarrier': {
        3: ('pass', 'the arm drawn lowered in its top view, raised in the others: the top used only for the box'),
        14: ('pass', 'its arm is its own part, Arm, its origin at the pivot on the box: shown lowering and rising'),
        15: ('pass', 'the arm\'s foot stays on the box at every angle of its swing (looked at in the motion)'),
        17: ('pass', 'the arm carries only the arm; the box and its leg stay'),
    },
    'KmToriiSmall': {3: ('pass', 'the pillars round in section below the tie beam (the top view sees only the top beam)')},
    'KmBicycle': {
        3: ('pass', 'below the saddle a slab 4 cm thick in its front\'s outline (wheels, frame, guards); the saddle, bars '
                    'and basket carved from all its views'),
        4: ('pass', 'its rear view is its left (from behind, as the views were made); its far side takes its near side\'s '
                    'pixels (no view of it)'),
        7: ('pass', 'the spokes and the basket\'s mesh open in its texture\'s alpha (the cut-out material)'),
    },
}


# ---------------------------------------------------------------- in Blender
def build(name, folder, height, new_obj, budget=1500, vox=0.01, tex=1024, top='auto', round_z=(), round_max=1.6,
          round_w=0.3, hole_fill=0.004, view_map=None, cutout=False, thin=0.0, shape=None, parts=None,
          smooth_angle=35.0):
    """The prop named name from the views in folder, height metres tall, its origin on the ground under its middle: its
    mesh (at most budget triangles), UVs and texture (tex x tex, RGBA). shape(frame) may change the carved field (a
    bicycle's wheels a thin slab); parts(frame) may split it into [(name or None, field, pivot or None)], each its own
    object (None: the root), a child's origin at its pivot. Returns (root, texture array, frame)."""
    import bpy
    frame = Frame(read_views(folder), height, vox, hole_fill, view_map, cutout, thin)
    frame.carve(top, round_z, round_max, round_w)
    if shape is not None:
        frame.field = shape(frame)
        frame.V = frame.field < 0
    pieces = parts(frame) if parts else [(None, frame.field, None)]
    objs = []
    for k, (pname, fld, pivot) in enumerate(pieces):
        verts, quads = surface_nets(fld, frame.vox, frame.origin)
        o = new_obj(pname or name, mesh_from(pname or name, verts, quads, frame.vox))
        remesh(o, frame.vox)
        objs.append(o)
    counts = [len(o.data.polygons) for o in objs]
    for o, c in zip(objs, counts):
        decimate(o, max(60, int(budget * c / sum(counts))))
    # one texture for them all: joined for the UVs and the bake, then parted again by a material slot each
    slots = [bpy.data.materials.new('_part%d' % k) for k in range(len(objs))]
    for o, m in zip(objs, slots):
        o.data.materials.append(m)
    root = objs[0]
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=root, selected_editable_objects=objs, object=root):
            bpy.ops.object.join()
    uv_unwrap(root, smooth_angle)
    tri_pos, tri_uv, tri_nrm = triangles(root)
    views = [v for v in ('front', 'back', 'right', 'left', 'top') if v != 'top' or 'top' in frame.masks]
    img = bake(frame, tri_pos, tri_uv, tri_nrm, tex, views)
    if len(objs) > 1:
        for x in bpy.context.scene.objects:
            x.select_set(False)
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')
        made = [x for x in bpy.context.selected_objects]
        for x in made:
            idx = [i for i, m in enumerate(x.data.materials) if m in slots and
                   any(p.material_index == i for p in x.data.polygons)]
            k = slots.index(x.data.materials[idx[0]])
            pname, _, pivot = pieces[k]
            if pname is None:
                root = x
                x.name = x.data.name = name
            else:
                x.name = x.data.name = pname
                x['pivot'] = pivot
        for x in made:
            if x is not root:
                p = x['pivot']
                x.data.transform(__import__('mathutils').Matrix.Translation((-p[0], -p[1], -p[2])))
                x.location = p
                x.parent = root
                del x['pivot']
    for o in [root] + list(root.children):
        o.data.materials.clear()
    for m in slots:
        bpy.data.materials.remove(m)
    return root, img, frame


def mesh_from(name, verts, quads, vox):
    """A mesh of the surface's quads, its coincident corners merged, triangulated."""
    import bpy
    import bmesh
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], quads.tolist())
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=vox * 0.05)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def remesh(o, vox):
    """Re-surfaced on a grid finer than the carving's (Blender's voxel remesh): one closed, manifold surface where the
    surface met itself at an edge or a corner (two posts touching diagonally)."""
    import bpy
    m = o.modifiers.new('Remesh', 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = vox * 0.6
    m.adaptivity = 0.0
    m.use_smooth_shade = False
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=m.name)


def split_above(z_cut, part_name, pivot_z):
    """parts(): the solid cut at z_cut, what is above it its own part (a barrier's arm), turning about the middle of its
    foot at pivot_z."""
    def parts(frame):
        Z = frame.zs[None, None, :]
        below = np.maximum(frame.field, Z - z_cut)
        above = np.maximum(frame.field, z_cut - Z)
        foot = (above < 0) & (Z < z_cut + 0.08)
        ii, jj, _ = np.nonzero(foot)
        pivot = (float(frame.xs[ii].mean()), float(frame.ys[jj].mean()), pivot_z)
        return [(None, below, None), (part_name, above, pivot)]
    return parts


def slab_below(z0, half):
    """shape(): below z0 only a slab half metres either side of the middle, in the front's outline (a bicycle: its wheels,
    frame and guards one plane, the cut-out texture showing the spokes); above it the carved solid (saddle, bars, basket)."""
    def shape(frame):
        Y = frame.ys[None, :, None]
        Z = frame.zs[None, None, :]
        slab = np.maximum(frame.F[:, None, :], np.abs(Y) - half)
        return np.minimum(slab, np.maximum(frame.field, z0 - Z)).astype(np.float32)
    return shape


def decimate(o, budget):
    """Down to the budget: planar faces merged first (a box's sides one face each), then collapsed."""
    import bpy
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris <= budget:
        return
    m = o.modifiers.new('Planar', 'DECIMATE')
    m.decimate_type = 'DISSOLVE'
    m.angle_limit = math.radians(2.0)
    m.delimit = set()
    m2 = o.modifiers.new('Tri', 'TRIANGULATE')
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.ops.object.modifier_apply(modifier=m2.name)
    tris = len(o.data.polygons)
    if tris > budget:
        m = o.modifiers.new('Collapse', 'DECIMATE')
        m.decimate_type = 'COLLAPSE'
        m.use_collapse_triangulate = True
        m.ratio = budget / tris * 0.97
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=m.name)
    close(o)


def close(o):
    """Closes any hole the decimation opened (where the surface met itself at an edge), faces outward."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


def uv_unwrap(o, smooth_angle):
    """Smart UV islands, packed, the faces toward the street (the front) given twice the texels; shaded smooth below
    smooth_angle."""
    import bpy
    import bmesh
    for x in bpy.context.scene.objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.active
    # islands: faces joined across edges whose UVs agree on both ends
    bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f1, f2 = e.link_faces
        def uvs(f):
            return {l.vert.index: tuple(l[uv].uv) for l in f.loops if l.vert in e.verts}
        a, b = uvs(f1), uvs(f2)
        if all(abs(a[k][0] - b[k][0]) < 1e-6 and abs(a[k][1] - b[k][1]) < 1e-6 for k in a):
            parent[find(f1.index)] = find(f2.index)
    islands = {}
    for f in bm.faces:
        islands.setdefault(find(f.index), []).append(f)
    for faces in islands.values():
        area = sum(f.calc_area() for f in faces)
        n = sum((f.normal * f.calc_area() for f in faces), faces[0].normal * 0) / max(area, 1e-9)
        k = 2.0 if n.y < -0.7 else 1.0                  # toward the street: twice the texels each way
        if k == 1.0:
            continue
        cu = sum(l[uv].uv.x for f in faces for l in f.loops) / sum(len(f.loops) for f in faces)
        cv = sum(l[uv].uv.y for f in faces for l in f.loops) / sum(len(f.loops) for f in faces)
        for f in faces:
            for l in f.loops:
                l[uv].uv = (cu + (l[uv].uv.x - cu) * k, cv + (l[uv].uv.y - cv) * k)
    bm.to_mesh(o.data)
    bm.free()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004, shape_method='CONCAVE', scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.data.shade_smooth()
    o.data.set_sharp_from_angle(angle=math.radians(smooth_angle))


def triangles(o):
    """Each triangle's corners: positions, UVs and (split) normals, as arrays (n, 3, 3), (n, 3, 2), (n, 3, 3)."""
    me = o.data
    me.calc_loop_triangles()
    lt = me.loop_triangles
    n = len(lt)
    loops = np.zeros(n * 3, np.int64)
    lt.foreach_get('loops', loops)
    verts = np.zeros(n * 3, np.int64)
    lt.foreach_get('vertices', verts)
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    uvl = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers.active.data.foreach_get('uv', uvl)
    uvl = uvl.reshape(-1, 2)
    nrm = np.zeros(len(me.loops) * 3, np.float32)
    me.corner_normals.foreach_get('vector', nrm)
    nrm = nrm.reshape(-1, 3)
    return co[verts].reshape(n, 3, 3), uvl[loops].reshape(n, 3, 2), nrm[loops].reshape(n, 3, 3)
