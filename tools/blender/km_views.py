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
    1_front_left_half.png and 2_front_right_half.png ('_half' may be left out)."""
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
    out, halves = {}, {}
    for view, ps in parts.items():
        if None in ps:
            out[view] = ps[None]
        elif 'top' in ps and 'bottom' in ps:
            halves[view] = (ps['top'], ps['bottom'], True)
        elif 'left' in ps and 'right' in ps:
            # a long object's halves, turned so the join runs top to bottom like a tall one's
            halves[view] = (np.transpose(ps['left'], (1, 0, 2)), np.transpose(ps['right'], (1, 0, 2)), False)
    # each view's ways to join its halves, then the one that agrees with the others: the same object at one scale is as
    # tall (or as long) in its front, side and back (the top view has a scale of its own)
    joins = {v: joins_of(a, b) for v, (a, b, _) in halves.items()}
    for group in ([v for v in joins if v != 'top'], [v for v in joins if v == 'top']):
        for v, (a, b, vertical) in ((v, halves[v]) for v in group):
            shift = pick_join(joins[v], [joins[w] for w in group if w != v])
            im = stitch(a, b, shift)
            out[v] = im if vertical else np.transpose(im, (1, 0, 2))
    return out


def joins_of(a, b):
    """The ways two halves of a view (a above b, as turned by read_views) could join: [(dy, dx, error, size)] for the shift
    most of their matched features agree on and the one a band of a's end finds inside b, error how much the halves'
    objects differ where they overlap, size how tall the object stitched that way is; and how tall b and a's objects
    are without their overlap (for a shift set from another view's size)."""
    ma, mb = object_mask(a), object_mask(b)
    ra, rb = np.nonzero(ma.any(1))[0], np.nonzero(mb.any(1))[0]
    out = []
    for sh in (_shift_by_features(a, b, ma, mb), _shift_by_band(a, b, ma)):
        if sh is not None:
            out.append((sh[0], sh[1], _overlap_error(a, b, ma, mb, *sh), sh[0] + rb[-1] - ra[0]))
    return dict(found=out, span=rb[-1] - ra[0])


def pick_join(own, others, tol=0.02):
    """The join for a view: the one that agrees best where the halves overlap, among those within tol of the size the views
    agree on (the median of each view's best); if none is, the shift that gives that size. A platform's posts repeat, so a
    shift a post away matches some features too; a pole's back drawn apart from its front can match better a little off
    (D27)."""
    best = lambda j: min(j['found'], key=lambda f: f[2]) if j['found'] else None
    sizes = [best(j)[3] for j in [own] + others if best(j) is not None]
    if not sizes:
        raise ValueError('two halves that do not join')
    target = float(np.median(sizes))
    near = [f for f in own['found'] if abs(f[3] - target) <= tol * target]
    if near:
        f = min(near, key=lambda f: f[2])
        return f[0], f[1]
    dx = best(own)[1] if own['found'] else 0
    return int(round(target - own['span'])), dx


def stitch(a, b, shift):
    """Two halves of one view (a above b) laid together with b's row 0 at a's row dy and its column 0 at a's column dx:
    b laid on from the middle of the objects' overlap, not of the images' (a half can end in a grey margin past its
    cut: the station platform's halves, D27)."""
    dy, dx = shift
    ma, mb = object_mask(a), object_mask(b)
    ha, wa = a.shape[:2]
    hb, wb = b.shape[:2]
    x0 = min(0, dx)
    H, W = max(ha, dy + hb), max(wa, dx + wb) - x0
    out = np.full((H, W, 3), np.median(np.concatenate([a[:8].reshape(-1, 3), b[-8:].reshape(-1, 3)]), 0).astype(np.uint8),
                  np.uint8)
    out[:ha, -x0:-x0 + wa] = a
    a_end = np.nonzero(ma.any(1))[0][-1]
    b_start = np.nonzero(mb.any(1))[0][0] + dy
    seam = int(np.clip((a_end + b_start) // 2, max(dy, 0), ha))   # a above the middle of the objects' overlap, b below
    out[seam:dy + hb, dx - x0:dx - x0 + wb] = b[seam - dy:]
    return out


def _overlap_error(a, b, ma, mb, dy, dx):
    """How much the two halves' objects differ where they overlap with b shifted by (dy, dx): their mean colour
    difference there (infinite if they hardly overlap)."""
    r0, r1 = max(dy, 0), min(a.shape[0], dy + b.shape[0])
    c0, c1 = max(dx, 0), min(a.shape[1], dx + b.shape[1])
    if r1 - r0 < 20 or c1 - c0 < 20:
        return float('inf')
    m = ma[r0:r1, c0:c1] & mb[r0 - dy:r1 - dy, c0 - dx:c1 - dx]
    if m.sum() < 500:
        return float('inf')
    d = np.abs(a[r0:r1, c0:c1].astype(np.float32) - b[r0 - dy:r1 - dy, c0 - dx:c1 - dx].astype(np.float32)).mean(-1)
    return float(d[m].mean())


def _shift_by_features(a, b, ma, mb, tol=4.0):
    """(dy, dx) where b lies on a, the shift most matched ORB features on the objects agree on; None if too few do."""
    ga = cv2.cvtColor(np.ascontiguousarray(a), cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(np.ascontiguousarray(b), cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(6000)
    ka, da = orb.detectAndCompute(ga, ma.astype(np.uint8) * 255)
    kb, db = orb.detectAndCompute(gb, mb.astype(np.uint8) * 255)
    if da is None or db is None:
        return None
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(matches) < 12:
        return None
    d = np.array([np.subtract(ka[m.queryIdx].pt, kb[m.trainIdx].pt) for m in matches])   # (dx, dy) of each match
    ha, wa = a.shape[:2]
    d = d[(d[:, 1] > 0.2 * ha) & (d[:, 1] < ha) & (np.abs(d[:, 0]) < 0.3 * wa)]       # b below a's top, roughly under it
    if len(d) < 12:
        return None
    near = (np.abs(d[:, None, :] - d[None, :, :]) <= tol).all(-1).sum(1)
    best = d[near.argmax()]
    inl = d[(np.abs(d - best) <= tol).all(1)]
    if len(inl) < 12:
        return None
    dx, dy = np.median(inl, 0)
    return int(round(dy)), int(round(dx))


def _shift_by_band(a, b, ma):
    """(dy, dx) where b lies on a: a band near the end of a's object matched inside b's start."""
    rows = np.nonzero(ma.any(1))[0]
    end = rows[-1] + 1
    band = a[end - 260:end - 40]
    cols = np.nonzero(ma[end - 260:end - 40].any(0))[0]
    x0, x1 = (max(0, cols.min() - 40), min(a.shape[1], cols.max() + 40)) if len(cols) else (0, a.shape[1])
    tpl = cv2.cvtColor(np.ascontiguousarray(band[:, x0:x1]), cv2.COLOR_RGB2GRAY)
    search = cv2.cvtColor(np.ascontiguousarray(b[:min(b.shape[0], 900)]), cv2.COLOR_RGB2GRAY)
    if search.shape[0] < tpl.shape[0] or search.shape[1] < tpl.shape[1]:
        return None
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    _, _, _, (bx, by) = cv2.minMaxLoc(res)
    return (end - 260) - by, x0 - bx          # a's row end - 260 is b's row by, its column x0 b's column bx


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
    # each hole's mean colour and spread, all at once
    lab = hl.ravel()
    cnt = np.maximum(np.bincount(lab, minlength=hn), 1)
    mean = np.stack([np.bincount(lab, a[..., c].ravel(), hn) / cnt for c in range(3)], 1)
    sq = np.stack([np.bincount(lab, (a[..., c] ** 2).ravel(), hn) / cnt for c in range(3)], 1)
    spread = np.sqrt(np.maximum(sq - mean ** 2, 0)).mean(1)
    fill = np.zeros(hn, bool)
    for i in range(1, hn):
        x, y, w, h, area = hs[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            # the background seen through a gap is as flat as the background (its pixels spread about 1); glass or a
            # shadowed inside the grey's colour is not (about 5: the red machine's window, D25)
            fill[i] = area < small or np.abs(mean[i] - bg).sum() > thresh or spread[i] > 3.0
    m = m | fill[hl]
    return m.astype(bool)


def bbox(m):
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


# ---------------------------------------------------------------- the solid
class Frame:
    """The views sized to one another and to the real height (each view's pixel mapping), and the solid carved from them
    as a field on a grid of nodes vox apart: negative inside, metres to the surface."""

    def __init__(self, views, height, vox=0.01, hole_fill=0.004, view_map=None, cutout=False, thin=0.0, turn=None,
                 flip=()):
        """views: {view: image}; view_map renames the user's views where an image was made from another side than its
        name says (a bicycle's 'back' from its rear end: {'back': 'left'}). A side with no view of its own takes the
        opposite side's (a far side looks like the near one): the back the front's, the left the right's. cutout: each
        view's alpha is the object's own outline, its gaps open (a wheel's spokes), for a cut-out material. thin: what is
        thinner than this many metres in a view (a pole's step bolts, a hanging cable) is left out of the solid, shown
        only by the texture where it crosses the solid. turn: {view: quarter turns anticlockwise} for a view drawn turned
        (the street lamp's top, its arm toward the street); flip: views drawn unmirrored (the tram's back, its pantograph
        at the same end as in its front), mirrored left to right. The images on disk stay as made."""
        views = {(view_map or {}).get(k, k): v for k, v in views.items()}
        views = {k: np.ascontiguousarray(np.rot90(v, (turn or {}).get(k, 0))) for k, v in views.items()}
        views = {k: np.ascontiguousarray(v[:, ::-1]) if k in flip else v for k, v in views.items()}
        self.views = views
        self.masks = {k: object_mask(v, hole_fill=hole_fill) for k, v in views.items() if k != 'three'}
        # where each view shows the object (before thin parts are taken out of the carving): a view colours a point only
        # where it does, so a view drawn narrower than the others leaves its edges to them (the shrine's back, D27)
        self.cover = {k: m.astype(np.float32) for k, m in self.masks.items()}
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
        """The view's silhouette as a signed distance in metres (negative inside), at the points P seen from the view
        ('front_outer': the front's outline with its holes filled)."""
        if view not in self._sdf:
            m = self.masks[view.replace('_outer', '')].astype(np.uint8)
            if view.endswith('_outer'):
                inv = (1 - m).astype(np.uint8)
                n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
                for i in range(1, n):
                    x, y, w, h, _ = st[i]
                    if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
                        m[lab == i] = 1
            inside = cv2.distanceTransform(m, cv2.DIST_L2, 5)
            outside = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
            self._sdf[view] = (outside - inside).astype(np.float32)
        base = view.replace('_outer', '')
        u, v = self.px(base, P)
        return remap(self._sdf[view], u, v, cv2.BORDER_CONSTANT, 1e4).reshape(-1) / self.scale[base]

    def carve(self, top='auto', round_z=(), round_max=1.6, round_w=0.3, top_cover=0.9):
        """The field: inside where the front and the right side both show the object. Each horizontal slice also inside the
        top view where the top agrees with it (top='auto': cut by the top, the slice still reaches top_cover of what the
        front and the side show at that height, so the top only hollows it, a frame open from above; 'always'; False:
        never; a top drawn otherwise, a barrier's arm lowered in it, is left out there). In the
        heights round_z ((z0, z1) pairs), each round piece of a slice (its sides within round_max of each other, neither
        over round_w metres) made round in section: a post, under a beam the top view cannot see past."""
        xs, ys, zs = self.xs, self.ys, self.zs
        gx, gz = np.meshgrid(xs, zs, indexing='ij')
        pts = np.stack([gx.ravel(), np.zeros(gx.size), gz.ravel()], 1)
        F = self.sdf('front', pts).reshape(gx.shape)
        if 'back' in self.masks:
            # a gap the front shows is a gap only where the back shows it too: the station platform's front draws its
            # gateway open to the grey, its back a wall there (D27); inside the front's outline, the back fills it
            B = self.sdf('back', pts).reshape(gx.shape)
            outer = self.sdf('front_outer', pts).reshape(gx.shape)
            F = np.minimum(F, np.maximum(B, outer))
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
    its edges' crossings; one quad across each crossed edge. Closed and outward-facing where the field is negative inside.
    Only the crossed edges are kept (a house's grid has 20 million nodes, its surface a few hundred thousand)."""
    f = np.pad(field, 1, constant_values=1e3)
    cells = tuple(n - 1 for n in f.shape)
    acc = np.zeros((int(np.prod(cells)), 3), np.float64)
    cnt = np.zeros(int(np.prod(cells)), np.int32)
    edges = []
    for axis in range(3):
        a = [slice(None)] * 3
        b = [slice(None)] * 3
        a[axis] = slice(0, -1)
        b[axis] = slice(1, None)
        fa, fb = f[tuple(a)], f[tuple(b)]
        cross = (fa < 0) != (fb < 0)
        e = np.argwhere(cross)                          # each crossed edge by its low end's node
        va, vb = fa[cross], fb[cross]
        p = e.astype(np.float64)
        p[:, axis] += va / (va - vb)                    # where along it the surface crosses, in node units
        u, w = [ax for ax in range(3) if ax != axis]
        for du in (0, 1):                               # the four cells around the edge
            for dw in (0, 1):
                c = e.copy()
                c[:, u] -= du
                c[:, w] -= dw
                ok = (c >= 0).all(1) & (c[:, 0] < cells[0]) & (c[:, 1] < cells[1]) & (c[:, 2] < cells[2])
                flat = np.ravel_multi_index(tuple(c[ok].T), cells)
                np.add.at(acc, flat, p[ok])
                np.add.at(cnt, flat, 1)
        edges.append((axis, e, va < 0))
    has = cnt > 0
    vid = np.full(cnt.shape, -1, np.int64)
    vid[has] = np.arange(has.sum())
    verts = acc[has] / cnt[has][:, None]
    verts = (verts - 1) * vox + origin                  # the pad shifted every node by one
    vid = vid.reshape(cells)
    quads = []
    for axis, e, ins in edges:
        u, w = [ax for ax in range(3) if ax != axis]
        keep = (e[:, u] >= 1) & (e[:, w] >= 1) & (e[:, u] < f.shape[u] - 1) & (e[:, w] < f.shape[w] - 1)
        e, ins = e[keep], ins[keep]
        corners = []
        for du, dw in ((-1, -1), (0, -1), (0, 0), (-1, 0)):
            c = e.copy()
            c[:, u] += du
            c[:, w] += dw
            corners.append(vid[c[:, 0], c[:, 1], c[:, 2]])
        q = np.stack(corners, 1)
        flip = ins if axis == 1 else ~ins              # inside at the edge's low end: the surface faces +axis
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
        sel = np.nonzero(w > 1e-4)[0]
        if not len(sel):
            continue
        u, v = frame.px(view, P[sel])
        w_sel = w[sel] * (covered(frame, view, u, v) > 0.5)        # only where this view shows the object
        acc[sel] += sample(frame.image(view), u, v) * w_sel[:, None]
        wsum[sel] += w_sel
    miss = np.nonzero(wsum < 1e-3)[0]
    if len(miss):                                      # seen by none of the views facing it (a wall's inner face that a
        names = [v for v in views if v != 'top']       # side view leaves out, a canopy under the eaves): the side view
        face = np.stack([N[miss] @ np.asarray(NORMALS[v], np.float32) for v in names], 1)   # facing it most, its pixels
                                                       # reflected into its outline (never the top's: what hides it from
                                                       # above is what the top shows there, the house's roof tiles)
        best = face.argmax(1)
        for i, view in enumerate(names):
            sel = miss[best == i]
            if not len(sel):
                continue
            u, v = reflected(frame, view, *frame.px(view, P[sel]))
            acc[sel] = sample(frame.image(view), u, v) * 0.85        # a little darker: a face no view shows is in shade
            wsum[sel] = 1.0
    return acc / np.maximum(wsum, 1e-6)[:, None]


def reflected(frame, view, u, v):
    """The view's pixels (u, v) moved onto its object: one off it reflected about the nearest pixel on it (so a texture
    carries on past the outline instead of smearing its edge), or that nearest pixel if the reflection is off it too."""
    src = frame.src[view]
    if not hasattr(frame, '_near'):
        frame._near = {}
    if src not in frame._near:
        on = frame.cover[src] > 0.5
        _, lab = cv2.distanceTransformWithLabels((~on).astype(np.uint8), cv2.DIST_L2, 5,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(on)                     # the object's pixels, each its own label
        table = np.zeros((int(lab.max()) + 1, 2), np.float32)
        table[lab[ys, xs]] = np.stack([xs, ys], 1)
        frame._near[src] = (lab, table)
    lab, table = frame._near[src]
    ui = np.clip(np.round(u).astype(int), 0, lab.shape[1] - 1)
    vi = np.clip(np.round(v).astype(int), 0, lab.shape[0] - 1)
    c = table[lab[vi, ui]]
    ru, rv = 2 * c[:, 0] - u, 2 * c[:, 1] - v
    ok = covered(frame, view, ru, rv) > 0.5
    return np.where(ok, ru, c[:, 0]), np.where(ok, rv, c[:, 1])


def covered(frame, view, u, v):
    """How much of the view's object is at its pixels (u, v): 1 on it, 0 off it (bilinear between)."""
    return remap(frame.cover[frame.src[view]], u, v, cv2.BORDER_CONSTANT, 0.0).reshape(-1)


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
        'KmCrossingSignal': ('KM-A05', 'KM-A05_level_crossing_signal', 3.6,
                             dict(round_z=[(0.95, 3.6)], round_w=0.2, shape=hollow_below(0.95, 0.07, [(0.0, 0.0, 0.12)]))),
        'KmCrossingBarrier': ('KM-A04', 'KM-A04_level_crossing_barrier', 4.5,
                              dict(round_z=[(1.75, 4.5)], round_w=0.15,
                                                                         parts=split_above(1.50, 'Arm', 1.56))),
        'KmToriiSmall': ('KM-A11', 'KM-A11_small_vermilion_torii', 2.6, dict(round_z=[(0.0, 1.75)])),
        'KmBicycle': ('KM-A08', 'KM-A08_city_bicycle', 1.15,
                      dict(view_map={'back': 'left'}, top='always', cutout=True, hole_fill=0.05,
                           shape=slab_below(0.68, 0.02))),
        # KM1-1's second batch
        'KmVendingRed': ('KM-A06', 'KM-A06_red_vending_machine', 1.83, dict()),
        'KmRecyclingBins': ('KM-A20', 'KM-A20_recycling_bins', 1.0, dict()),
        'KmAirConditioner': ('KM-A22', 'KM-A22_air_conditioner_outdoor_unit', ('width', 0.8),
                             dict(shape=hollow_below(0.55, 0.06))),
        'KmMeters': ('KM-A23', 'KM-A23_gas_and_electricity_meters', ('width', 0.8),
                     dict(round_z=[(0.0, 0.15)], round_w=0.1)),
        'KmLetterbox': ('KM-A24', 'KM-A24_house_letterbox', 1.55, dict()),
        'KmControlCabinet': ('KM-A25', 'KM-A25_grey_control_cabinet', 1.6, dict()),
        'KmStreetLamp': ('KM-A26', 'KM-A26_street_lamp', 7.0,
                         dict(vox=0.02, round_z=[(0.0, 7.0)], round_w=0.5, thin=0.05)),
        'KmTicketGate': ('KM-A28', 'KM-A28_ticket_gate', 1.0,
                         dict(ignore=('top',), thin=0.03, shape=plate_beyond(-0.04, -0.204, 0.012))),
        'KmStationSign': ('KM-A29', 'KM-A29_station_name_board', ('width', 1.8),
                          dict(round_z=[(0.0, 2.4)], round_w=0.09)),
        # the tram: a vehicle, 12 m long (its own budget, docs/PERFORMANCE.md)
        'KmTram': ('KM-V01', 'KM-V01_tram', ('width', 12.0), dict(vox=0.03, budget=4000, tex=2048)),
        # KM1-1's last batch: the plain pole, and the buildings and set pieces (their own budgets, docs/PERFORMANCE.md)
        'KmPolePlain': ('KM-A02', 'KM-A02_plain_concrete_utility_pole', 10.0,
                        dict(vox=0.02, round_z=[(0.0, 10.0)], round_w=0.7, thin=0.08)),
        'KmHouseBeige': ('KM-B04', 'KM-B04_beige_stucco_house', 7.5,
                         dict(vox=0.03, budget=5000, tex=2048,
                              shape=regions((-9, 9, 2.55, 5.4, 'flush', -3.43,
                                             [(-0.7, 3.5, 3.25, 4.65),          # the balcony
                                              (-3.75, -0.95, 2.75, 3.3),        # the entrance canopy
                                              (-1.0, 2.9, 2.7, 3.0)])))),       # the lower window's hood
        'KmShrineSmall': ('KM-B05', 'KM-B05_little_shrine', 4.0,
                          dict(vox=0.015, budget=4000, tex=2048,
                               shape=regions((-9, -0.85, -1, 1.55, 'front_top'), (0.80, 9, -1, 1.55, 'front_top'),
                                             (1.05, 9, 1.55, 2.9, 'depth', -0.27, 0.32)))),
        'KmStationPlatform': ('KM-B06', 'KM-B06_hase_station_platform', 3.2,             # its views make it 7.6 m long
                              dict(vox=0.02, budget=4000, tex=2048, thin=0.03)),
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
    'KmCrossingSignal': {3: ('pass', 'the post round in section; the guard frame open, its bars only (no view shows '
                                     'its hollow: its far bars show through its near ones, and from above the crossbuck '
                                     'covers it, so the band its views show is kept and the middle left open)')},
    'KmCrossingBarrier': {
        3: ('pass', 'the arm drawn lowered in its top view, raised in the others: the top used only for the box'),
        14: ('pass', 'its arm is its own part, Arm, its origin at the pivot on the box: shown lowering and rising'),
        15: ('pass', 'the arm\'s foot stays on the box at every angle of its swing (looked at in the motion)'),
        17: ('pass', 'the arm carries only the arm; the box and its leg stay'),
    },
    'KmToriiSmall': {3: ('pass', 'the pillars round in section below the tie beam (the top view sees only the top beam)')},
    'KmVendingRed': {11: ('pass', 'its logo panel reads うみかぜ, as the prompt asks (no real drink logo)')},
    'KmRecyclingBins': {11: ('pass', 'its labels are generic words (カン, ペットボトル, ペット) with invented lines under '
                                     'them, as the prompt asks; no brand')},
    'KmAirConditioner': {
        3: ('pass', 'the stand open: its legs and rails only, the band its views show (the front\'s and the side\'s '
                    'rails crossing would otherwise fill it with a shelf)'),
        11: ('pass', 'its maker\'s plate an invented code (KM-50)'),
    },
    'KmMeters': {3: ('pass', 'the board and meters carved from its front, side and top; the pipes below the board round')},
    'KmLetterbox': {11: ('pass', 'its labels generic (郵便, post) and invented; no brand')},
    'KmControlCabinet': {3: ('pass', 'as deep as its side and three-quarter views show it (0.28 m); its top view draws it '
                                     'deeper, and the side\'s depth is kept')},
    'KmStreetLamp': {
        3: ('pass', 'the column round in section; the arm and lamp from the front, side and top'),
        12: ('pass', 'its cables, thinner than 5 cm, in its texture only'),
        13: ('pass', 'its front, side and back each made in two halves; joined where they overlap'),
    },
    'KmTicketGate': {
        3: ('limit', 'its flap a plate 2.4 cm thick at the body\'s front end: its side view draws the flap as a rod and its '
                     'top view repeats its front (each redone once), so the flap\'s depth is set by hand'),
        4: ('limit', 'its top takes the nearest sides\' pixels: its top view is left out (it shows the front)'),
    },
    'KmStationSign': {
        3: ('pass', 'the posts round in section; the board as thin as its side view shows it'),
        11: ('pass', 'the station\'s and its neighbours\' names (長谷, 極楽寺, 由比ヶ浜), no brand'),
    },
    'KmTram': {
        4: ('limit', 'its BACK draws the roof units where its FRONT and TOP have them, not mirrored: their far faces take '
                     'the roof\'s pixels (seen only from the far side, above the roof line)'),
        7: ('pass', 'its windows show the car\'s inside, the plain grey through the far windows (its FRONT redone)'),
        12: ('pass', 'its pantograph stands free; the overhead wire is the level\'s'),
    },
    'KmPolePlain': {
        3: ('pass', 'carved from its front, side and top: the column round in section, the crossarms as deep as its side and '
                    'top show them'),
        12: ('pass', 'its cables, thinner than 8 cm, in its texture only'),
        13: ('pass', 'its front, side and back each made in two halves; each joined so the three come out the same height'),
    },
    'KmHouseBeige': {
        3: ('pass', 'its front flush with its wall but over the balcony, the entrance canopy and the lower window\'s hood: '
                    'the side view shows how far they stand out, the front where, and carved from both alone they ran the '
                    'whole front as ledges'),
        4: ('pass', 'faces no view sees (the canopy\'s top under the eaves) take the side view facing them'),
    },
    'KmShrineSmall': {
        3: ('limit', 'its walls beside the steps carved from its front and top alone (its side view draws the steps '
                     'standing out in front of them); its lantern kept to its own depth'),
        4: ('limit', 'its back is drawn a quarter narrower than its front, so its back\'s edges take its sides\' pixels; '
                     'the walls\' inner faces, seen by no view, take the side view\'s stones reflected; its left side is '
                     'its right side\'s, the lantern there included'),
    },
    'KmStationPlatform': {
        3: ('pass', 'the gap its front draws through the back wall at the gateway left out (its back shows a wall there)'),
        13: ('pass', 'its front, back and top each made in two halves from one master; 7.6 m long at its 3.2 m height, by its '
                     'views\' proportions (the prompt: 10 m)'),
    },
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
          round_w=0.3, hole_fill=0.004, view_map=None, cutout=False, thin=0.0, turn=None, flip=(), ignore=(),
          shape=None, parts=None, smooth_angle=35.0):
    """The prop named name from the views in folder, height metres tall (or ('width', metres) for one measured along the
    street), its origin on the ground under its middle: its
    mesh (at most budget triangles), UVs and texture (tex x tex, RGBA). shape(frame) may change the carved field (a
    bicycle's wheels a thin slab); parts(frame) may split it into [(name or None, field, pivot or None)], each its own
    object (None: the root), a child's origin at its pivot. Returns (root, texture array, frame)."""
    import bpy
    import time
    t0 = time.time()

    def stage(what):
        print('  %s: %s %.0f s' % (name, what, time.time() - t0), flush=True)
    views = {k: v for k, v in read_views(folder).items() if k not in ignore}     # a view that shows something else
    if isinstance(height, tuple):                       # ('width', metres) or ('length', metres): along the street
        x0, y0, x1, y1 = bbox(object_mask(views['front']))
        height = height[1] * (y1 - y0) / (x1 - x0)
    frame = Frame(views, height, vox, hole_fill, view_map, cutout, thin, turn, flip)
    stage('views read and registered')
    frame.carve(top, round_z, round_max, round_w)
    stage('carved')
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
    stage('surfaced and remeshed, %d faces' % sum(len(o.data.polygons) for o in objs))
    counts = [len(o.data.polygons) for o in objs]
    for o, c in zip(objs, counts):
        decimate(o, max(60, int(budget * c / sum(counts))))
    stage('cut to %d triangles' % sum(len(o.data.polygons) for o in objs))
    # one texture for them all: joined for the UVs and the bake, then parted again by a material slot each
    slots = [bpy.data.materials.new('_part%d' % k) for k in range(len(objs))]
    for o, m in zip(objs, slots):
        o.data.materials.append(m)
    root = objs[0]
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=root, selected_editable_objects=objs, object=root):
            bpy.ops.object.join()
    uv_unwrap(root, smooth_angle)
    stage('unwrapped')
    tri_pos, tri_uv, tri_nrm = triangles(root)
    views = [v for v in ('front', 'back', 'right', 'left', 'top') if v != 'top' or 'top' in frame.masks]
    img = bake(frame, tri_pos, tri_uv, tri_nrm, tex, views)
    stage('baked')
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


def plate_beyond(x0, y0, half):
    """shape(): beyond x0 along the street only a plate half metres either side of y0, in the front's outline (a ticket
    gate's flap, which its side view draws otherwise)."""
    def shape(frame):
        X = frame.xs[:, None, None]
        Y = frame.ys[None, :, None]
        plate = np.maximum(frame.F[:, None, :], np.abs(Y - y0) - half)
        return np.where(X > x0, plate, frame.field).astype(np.float32)
    return shape


def hollow_below(z0, d, posts=()):
    """shape(): below z0 only a band d metres deep inside each slice's outline (a stand's legs and rails, a guard frame's
    bars), the middle left open, but for posts ((x, y, radius) kept whole): where the front's and the side's bars cross,
    the carving alone fills the middle with a shelf no view shows."""
    def shape(frame):
        f = frame.field.copy()
        X, Y = frame.xs[:, None], frame.ys[None, :]
        for k, z in enumerate(frame.zs):
            if z >= z0:
                break
            inside = f[:, :, k] < 0
            if not inside.any():
                continue
            ii, jj = np.nonzero(inside.any(1))[0], np.nonzero(inside.any(0))[0]
            xl, xh, yl, yh = frame.xs[ii[0]], frame.xs[ii[-1]], frame.ys[jj[0]], frame.ys[jj[-1]]
            g = np.minimum(np.minimum(X - xl, xh - X), np.minimum(Y - yl, yh - Y)) - d
            for px, py, r in posts:
                g = np.minimum(g, np.sqrt((X - px) ** 2 + (Y - py) ** 2) - r)
            f[:, :, k] = np.maximum(f[:, :, k], g)
        return f
    return shape


def regions(*rules):
    """shape(): rules for boxes of the solid ((x0, x1, z0, z1) in metres) where its views disagree:
    ('front_top',): carved from the front and the top alone there (its side view draws something else there: the little
    shrine's side shows its steps standing out in front of the wall, its front, top and three-quarter views walls beside
    them);
    ('depth', y0, y1): kept to y0..y1 there (a part a view draws apart from the rest: the shrine's lantern, which its
    side view merges with the shrine's own depth);
    ('flush', y_face, [(x0, x1, z0, z1), ...]): no further forward than y_face there but in the boxes listed (what stands
    out from a wall: the side view shows how far a balcony or a canopy comes out, the front view where it is, and carved
    from both it would run the wall's whole width: the beige house's ledges, D27)."""
    def shape(frame):
        f = frame.field.copy()
        X = frame.xs[:, None, None]
        Y = frame.ys[None, :, None]
        Z = frame.zs[None, None, :]
        T = None
        for x0, x1, z0, z1, kind, *arg in rules:
            inbox = (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
            if kind == 'front_top':
                if T is None:
                    gx, gy = np.meshgrid(frame.xs, frame.ys, indexing='ij')
                    T = frame.sdf('top', np.stack([gx.ravel(), gy.ravel(), np.zeros(gx.size)], 1)).reshape(gx.shape)
                g = np.maximum(frame.F[:, None, :], T[:, :, None])
            elif kind == 'flush':
                y_face, allowed = arg
                out = np.ones(np.broadcast(X, Z).shape, bool)
                for a0, a1, b0, b1 in allowed:
                    out &= ~((X >= a0) & (X <= a1) & (Z >= b0) & (Z <= b1))
                g = np.where(out, np.maximum(f, y_face - Y), f)
            else:
                y0, y1 = arg
                g = np.maximum(f, np.maximum(y0 - Y, Y - y1))
            f = np.where(inbox, g, f)
        return f.astype(np.float32)
    return shape


def slab_below(z0, half):
    """shape(): below z0 only a slab half metres either side of the middle, in the front's outline (a bicycle: its wheels,
    frame and guards one plane, the cut-out texture showing the spokes); above it the carved solid (saddle, bars, basket)."""
    def shape(frame):
        Y = frame.ys[None, :, None]
        Z = frame.zs[None, None, :]
        slab = np.maximum(frame.F[:, None, :], np.abs(Y) - half)
        return np.minimum(slab, np.maximum(frame.field, z0 - Z)).astype(np.float32)
    return shape


def decimate(o, budget, big=1_000_000):
    """Down to the budget: planar faces merged first (a box's sides one face each), then collapsed. A surface of more
    than big triangles (a building's) is first collapsed to a few hundred thousand: merging the planar faces of millions
    took the station platform over ten minutes (D27)."""
    import bpy
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris <= budget:
        return
    if tris > big:
        m = o.modifiers.new('Rough', 'DECIMATE')
        m.decimate_type = 'COLLAPSE'
        m.use_collapse_triangulate = True
        m.ratio = 300_000 / tris
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=m.name)
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
