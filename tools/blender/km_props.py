"""Kamakura's street props (KM-A, docs/KAMAKURA_BUILD.md Step 2), built by script like the home (kit_buildings_km.py,
one atlas, one kit): each measured in its photographic picture, made of simple solids at real size (cylinders, boards,
boxes, discs, tubes) and given the picture's own pixels by projecting it straight on onto every face. A cylinder's back
half takes its front's pixels mirrored, which is what a round pole looks like from behind; a deep box takes its sides
from the props sheet KM-P1 or from its own front. Nothing is a flat card: every prop is solid from all eight sides.

Scales are measured in the picture, from a known size beside the prop, never from the plan's guessed size: the vending
machines are 1.83 m and 248 px tall in the photographic KM1-1, so 135.5 px to the metre on the pavement where they, the
mirror and the transformer pole stand."""
import math

import bmesh
import numpy as np
from mathutils import Vector
from PIL import Image

KM11 = 'photo/KM1-1_hase_lanes.png'
CROPS = {}                  # each prop's picture region for its review: (box, cx, gy, px per m)
SHRINK = 0.85               # a round part's pixels from 85 % of its radius: its edge not the background's
INSET_PX = 2.5              # an edge face's pixels from this far inside the picture's outline
PAVEMENT_S = 135.5          # px to the metre on KM1-1's pavement (the vending machines: 1.83 m, 248 px)


class Pic:
    """A region of a picture placed in the atlas, and the projection onto it: metres (x along the street from the prop's
    middle, z up from its ground) to the picture's pixels (cx: the middle's column, gy: the ground's row, s: px per m)."""

    def __init__(self, atlas, im, box, cx, gy, s):
        self.atlas, self.box, self.cx, self.gy, self.s = atlas, box, cx, gy, s
        self.pos = atlas.place(im.crop(box))
        self.w, self.h = box[2] - box[0], box[3] - box[1]

    def px(self, x, z):
        return self.cx + x * self.s - self.box[0], self.gy - z * self.s - self.box[1]

    def uv(self, x, z):
        px, py = self.px(x, z)
        return self.atlas.uv(self.pos, min(max(px, 0.5), self.w - 0.5), min(max(py, 0.5), self.h - 0.5))


class Sample:
    """An image placed in the atlas and stretched once across a face (a box's side from the props sheet)."""

    def __init__(self, atlas, im):
        self.atlas, self.pos, self.size = atlas, atlas.place(im), im.size


class Mesh:
    """Solids added in metres (x along the street, y into the picture: -y faces the street, z up), each face's UVs
    projected from a Pic, or a Sample stretched across it; every face turned outward from its own solid's middle."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uvl = self.bm.loops.layers.uv.new('UVMap')

    def _face(self, pts, uvs, mid):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        for loop, uv in zip(f.loops, uvs):
            loop[self.uvl].uv = uv
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - mid) < 0:
            f.normal_flip()
        return f

    def proj(self, pts, pic, mid, flat=None):
        """A face whose pixels come straight on from pic. flat: (u, v) metres axes to project along instead of (x, z),
        for a face seen edge on from the street (a board's end, a box's top): its pixels from the nearest strip."""
        return self._face(pts, [pic.uv(p.x, p.z) for p in pts], mid)

    def sample(self, pts, smp, mid, axes):
        """A face with smp stretched once across it, along axes (i, j) of the face's corners (0 x, 1 y, 2 z)."""
        i, j = axes
        lo_i, hi_i = min(p[i] for p in pts), max(p[i] for p in pts)
        lo_j, hi_j = min(p[j] for p in pts), max(p[j] for p in pts)
        (w, h), pos = smp.size, smp.pos
        uvs = [smp.atlas.uv(pos, (p[i] - lo_i) / max(hi_i - lo_i, 1e-6) * (w - 1),
                            (1 - (p[j] - lo_j) / max(hi_j - lo_j, 1e-6)) * (h - 1)) for p in pts]
        return self._face(pts, uvs, mid)

    # ------------------------------------------------------------------ solids
    def cyl(self, pic, x, y, z0, z1, r0, r1, n=10, ry=None, top=True, bottom=False, ux=None, dz=0.0):
        """An upright cylinder, tapering from r0 at z0 to r1 at z1 (ry: its depth radius, for an oval). Every face from
        the picture straight on: a vertex's pixel is the one in front of it, so the back half takes the front's, mirrored.
        ux: the column the cylinder is projected from, if not x (a pole moved along the street keeps its own pixels); dz:
        metres higher in the picture than where it stands (a part the picture hides takes what is just above it)."""
        ux = x if ux is None else ux
        ry0, ry1 = (r0, r1) if ry is None else (ry * r0 / max(r0, 1e-6), ry * r1 / max(r0, 1e-6))
        mid = Vector((x, y, (z0 + z1) / 2))
        ring = lambda z, r, rr: [Vector((x + r * math.sin(a), y - rr * math.cos(a), z))
                                 for a in (2 * math.pi * k / n for k in range(n))]
        lo, hi = ring(z0, r0, ry0), ring(z1, r1, ry1)
        # sampled a little inside its outline (SHRINK), so its edge never takes what stands behind it in the picture
        uv = lambda p: pic.uv(ux + (p.x - x) * SHRINK, p.z + dz)
        for k in range(n):
            q = [lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]]
            self._face(q, [uv(p) for p in q], mid)
        e = INSET_PX / pic.s
        if top:
            self._face(hi, [uv(Vector((p.x, 0, z1 - e))) for p in hi], mid)
        if bottom:
            self._face(lo, [uv(Vector((p.x, 0, z0 + e))) for p in lo], mid)

    def disc(self, pic, x, z, rx, rz, y0, y1, n=20, back=None, dome=0.0):
        """An oval facing the street, from y0 (its face) back to y1, its face bulging toward the street by dome (a convex
        mirror's glass). Face and rim from the picture straight on; the back from back (a Sample) or the face's pixels."""
        mid = Vector((x, (y0 + y1) / 2, z))
        ang = [2 * math.pi * k / n for k in range(n)]
        front = [Vector((x + rx * math.cos(a), y0, z + rz * math.sin(a))) for a in ang]
        rear = [Vector((x + rx * math.cos(a), y1, z + rz * math.sin(a))) for a in ang]
        uv = lambda p: pic.uv(p.x, p.z)
        for k in range(n):
            q = [front[k], front[(k + 1) % n], rear[(k + 1) % n], rear[k]]
            self._face(q, [uv(p) for p in q], mid)
        if dome > 0:
            c = Vector((x, y0 - dome, z))
            for k in range(n):
                q = [front[k], front[(k + 1) % n], c]
                self._face(q, [uv(p) for p in q], mid)
        else:
            self._face(front, [uv(p) for p in front], mid)
        if back is not None:
            self.sample(rear, back, mid, (0, 2))
        else:
            self._face(rear, [uv(p) for p in rear], mid)

    def board(self, pic, cx, cz, length, width, angle, y0, y1, ucx=None, ucz=None):
        """A board in the street's plane, its long axis turned angle degrees from level (counter-clockwise seen from the
        street), from y0 back to y1. Every face from the picture straight on (its ends and edges take the strip of
        pixels along them). ucx, ucz: where in the picture it is projected from, if not where it stands."""
        ucx, ucz = (cx if ucx is None else ucx), (cz if ucz is None else ucz)
        a = math.radians(angle)
        u, v = Vector((math.cos(a), 0, math.sin(a))), Vector((-math.sin(a), 0, math.cos(a)))
        c = Vector((cx, 0, cz))
        corners = [c + u * (s * length / 2) + v * (t * width / 2) for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = [Vector((p.x, y0, p.z)) for p in corners]
        b = [Vector((p.x, y1, p.z)) for p in corners]
        mid = Vector((cx, (y0 + y1) / 2, cz))
        uv = lambda p: pic.uv(p.x - cx + ucx, p.z - cz + ucz)
        for q in (f, b[::-1]) + tuple([f[k], f[(k + 1) % 4], b[(k + 1) % 4], b[k]] for k in range(4)):
            self._face(q, [uv(p) for p in q], mid)

    def box(self, pic, x0, x1, y0, y1, z0, z1, side=None, top=None, back=None):
        """A box: its street face and its back from the picture straight on (the back mirrored, or back: a Sample), its
        ends from side (a Sample; else the picture's edge strip) and its top from top (else the picture's top row)."""
        P = Vector
        mid = P(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        uv = lambda p: pic.uv(p.x, p.z)
        front = [P((x0, y0, z0)), P((x1, y0, z0)), P((x1, y0, z1)), P((x0, y0, z1))]
        self._face(front, [uv(p) for p in front], mid)
        rear = [P((x1, y1, z0)), P((x0, y1, z0)), P((x0, y1, z1)), P((x1, y1, z1))]
        if back is not None:
            self.sample(rear, back, mid, (0, 2))
        else:
            self._face(rear, [uv(p) for p in rear], mid)
        for xe in (x0, x1):
            q = [P((xe, y0, z0)), P((xe, y1, z0)), P((xe, y1, z1)), P((xe, y0, z1))]
            if side is not None:
                self.sample(q, side, mid, (1, 2))
            else:
                inset = INSET_PX / pic.s * (1 if xe == x0 else -1)
                self._face(q, [pic.uv(xe + inset, p.z) for p in q], mid)
        e = INSET_PX / pic.s
        for ze, inset in ((z1, -e), (z0, e)):
            q = [P((x0, y0, ze)), P((x1, y0, ze)), P((x1, y1, ze)), P((x0, y1, ze))]
            if top is not None and ze == z1:
                self.sample(q, top, mid, (0, 1))
            else:
                self._face(q, [pic.uv(p.x, ze + inset) for p in q], mid)

    def prism(self, pic, outline, y0, y1, top=None):
        """An outline in the street's plane ((x, z) points, around it) extruded from y0 back to y1: a beam with a curved
        top (a torii's kasagi). Every face from the picture straight on, except those facing up when top (a Sample) is
        given: a beam's upper face, which the picture shows only as a thin line against what is behind it."""
        f = [Vector((x, y0, z)) for x, z in outline]
        b = [Vector((x, y1, z)) for x, z in outline]
        mid = Vector((sum(p.x for p in f) / len(f), (y0 + y1) / 2, sum(p.z for p in f) / len(f)))
        uv = lambda p: pic.uv(p.x, p.z)
        self._face(f, [uv(p) for p in f], mid)
        self._face(b[::-1], [uv(p) for p in b[::-1]], mid)
        n = len(f)
        e = INSET_PX / pic.s
        for k in range(n):
            q = [f[k], f[(k + 1) % n], b[(k + 1) % n], b[k]]
            # its edge faces take the pixels just inside the outline, not the background along it
            inward = [(mid.x - p.x, mid.z - p.z) for p in q]
            uvs = [pic.uv(p.x + d[0] / max(math.hypot(*d), 1e-6) * e, p.z + d[1] / max(math.hypot(*d), 1e-6) * e)
                   for p, d in zip(q, inward)]
            up = (q[1] - q[0]).cross(q[3] - q[0]).normalized()
            if top is not None and abs(up.z) > 0.5 and (q[0].z + q[1].z) / 2 > mid.z:
                self.sample(q, top, mid, (0, 1))
            else:
                self._face(q, uvs, mid)

    def tube(self, pic, a, b, r, n=6, ua=None, caps=(True, True)):
        """A round bar from a to b (any direction), r across. Its pixels straight on from the picture, from where it
        stands (or shifted by ua: (dx, dz) metres to where the picture shows it). caps: close its ends at a and at b (not
        where it carries on into another tube)."""
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        t = d.cross(Vector((0, 1, 0)))
        if t.length < 1e-4:
            t = d.cross(Vector((1, 0, 0)))
        t.normalize()
        w = d.cross(t).normalized()
        ring = lambda c: [c + (t * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * r
                          for k in range(n)]
        ra, rb = ring(a), ring(b)
        mid = (a + b) / 2
        dx, dz = ua or (0.0, 0.0)

        def uv(p):
            # sampled a little inside its outline about its axis (SHRINK)
            on = a + d * (p - a).dot(d)
            q = on + (p - on) * SHRINK
            return pic.uv(q.x + dx, q.z + dz)
        for k in range(n):
            q = [ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k]]
            self._face(q, [uv(p) for p in q], mid)
        for ring, cap in ((ra, caps[0]), (rb, caps[1])):
            if cap:
                self._face(ring, [uv(p) for p in ring], mid)

    def object(self, name, new_obj):
        # corners where solids' faces meet become one: each solid a closed shell (docs/ASSET_REVIEW.md check 2)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        me = __import__('bpy').data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        return new_obj(name, me)


# ---------------------------------------------------------------- the props
def hue_to(im, hue_deg, sat_min=0.25):
    """The picture's saturated colours turned to one hue (a red machine's side, for the blue one), white and grey kept."""
    hsv = np.asarray(im.convert('HSV')).copy()
    sat = hsv[..., 1] / 255.0
    hsv[..., 0] = np.where(sat > sat_min, int(hue_deg / 360 * 255), hsv[..., 0])
    return Image.fromarray(hsv, 'HSV').convert('RGB')


def pole_column(im, x0, x1, y0, y1, height):
    """A clean band of a pole's column, repeated to height px: the pole carried on above the picture's top."""
    band = im.crop((x0, y0, x1, y1))
    out = Image.new('RGB', (x1 - x0, height))
    for k in range(0, height, band.height):
        out.paste(band if (k // band.height) % 2 == 0 else band.transpose(Image.FLIP_TOP_BOTTOM), (0, k))
    return out


def build_pole_transformer(atlas, im, new_obj):
    """KM-A01, the concrete utility pole with its transformers (the pole by the vending machines in KM1-1, x 1648).
    The pole: 38 px across at its foot, 34 at the picture's top (0.28 m to 0.25 m), its foot on the pavement at y 891;
    the picture ends 6.58 m up, so the column is carried on to 10 m from a clean band of itself (y 300 to 380). The two
    transformers (x 1580 to 1634 and 1674 to 1710, y 47 to 139), their crossarm (y 147 to 155, x 1575 to 1724) and the
    steel bands round the pole are the picture's. The wires and the street lamp's arm are left to the level (KM-A26)."""
    s, cx, gy = PAVEMENT_S, 1648.0, 891.0
    pic = Pic(atlas, im, (1570, 0, 1730, 893), cx, gy, s)
    top_z = gy / s
    ext = pole_column(im, 1630, 1667, 300, 380, int((10.0 - top_z) * s) + 4)
    # the band's bottom row where the picture's top was (z top_z), its rows going up from there
    epic = Pic(atlas, ext, (0, 0, ext.width, ext.height), 1648.5 - 1630, ext.height + top_z * s, s)
    m = Mesh()
    r_foot, r_top = 19.5 / s, 17.0 / s
    m.cyl(pic, 0, 0, 0.0, top_z, r_foot, r_top, n=12, top=False, bottom=True)
    # the column above the picture: its own pixels, the band's ground row set where the picture's top was
    m.cyl(epic, 0, 0, top_z, 10.0, r_top, r_top * 0.95, n=12, top=True)
    # the transformers: drums behind the pole's middle, on brackets (their bands and fins are the picture's)
    z = lambda py: (gy - py) / s
    for x0, x1, y0, y1 in ((1580, 1634, 47, 139), (1674, 1710, 70, 139)):
        r = (x1 - x0) / 2 / s
        xc = ((x0 + x1) / 2 - cx) / s
        m.cyl(pic, xc, 0.02, z(y1), z(y0), r, r, n=14, top=True, bottom=True)
    # the crossarm: a steel channel across the pole, a little in front of it
    m.box(pic, (1575 - cx) / s, (1724 - cx) / s, -0.16, -0.08, z(155), z(147))
    o = m.object('KmPoleTransformer', new_obj)
    CROPS[o.name] = ((1570, 0, 1730, 893), cx, gy, s)
    return o, dict(id='KM-A01', source='photo/KM1-1 (x 1570 to 1730), its column carried on above the picture', real_size=[1.1, 0.4, 10.0])


def build_mirror(atlas, im, new_obj):
    """KM-A03, the convex corner mirror by the vending machines in KM1-1: its glass and orange hood an oval 104 px
    across and 118 tall centred on (1837, 471) (0.77 m by 0.87 m), on a post 10 px across (7 cm) from y 893 to its
    capped top at y 377 (3.8 m). The glass bulges toward the street; the hood's back is its rim's orange."""
    s, gy = PAVEMENT_S, 893.0
    pic = Pic(atlas, im, (1780, 370, 1895, 893), 1826.0, gy, s)
    m = Mesh()
    z = lambda py: (gy - py) / s
    m.cyl(pic, 0, 0.06, 0.0, z(377), 5.0 / s, 5.0 / s, n=8, top=True, bottom=True)
    back = Sample(atlas, im.crop((1787, 458, 1791, 484)).resize((32, 32)))     # the hood's orange, from its rim
    m.disc(pic, (1837.5 - 1826) / s, z(471), 52 / s, 59 / s, -0.02, 0.05, n=24, back=back, dome=0.06)
    # the bracket from the post to the hood's back
    m.box(pic, -0.03, 0.06, 0.03, 0.07, z(480), z(462))
    o = m.object('KmMirror', new_obj)
    CROPS[o.name] = ((1770, 360, 1905, 900), 1826.0, gy, s)
    return o, dict(id='KM-A03', source='photo/KM1-1 (x 1780 to 1895)', real_size=[0.77, 0.15, 3.8])


def build_vending_blue(atlas, im, p1, new_obj, rectify):
    """KM-A19, the blue drink vending machine beside the red one in KM1-1 (its front x 1846 to 1982, y 622 to 873; its
    real logo already repainted with an invented name by rebrand_machines). Its side is the red machine's from KM-P1,
    turned blue."""
    W, D, H = 1.0, 0.75, 1.83
    x0, y0, x1, y1 = 1846, 622, 1982, 873
    pic = Pic(atlas, im, (x0, y0, x1, y1), (x0 + x1) / 2, y1, (x1 - x0) / W)
    side = hue_to(rectify(p1, [(1700, 48), (1757, 62), (1755, 398), (1700, 428)], (104, 254)), 215)
    sm = Sample(atlas, side)
    top = Sample(atlas, side.crop((10, 4, 94, 40)).resize((104, 78)))
    m = Mesh()
    m.box(pic, -W / 2, W / 2, -D / 2, D / 2, 0.0, (y1 - y0) / pic.s, side=sm, top=top, back=sm)
    o = m.object('KmVendingBlue', new_obj)
    CROPS[o.name] = ((x0 - 10, y0 - 10, x1 + 10, y1 + 10), (x0 + x1) / 2, y1, pic.s)
    return o, dict(id='KM-A19', source='photo/KM1-1 (front), KM-P1 (side, turned blue)', real_size=[W, D, H])


CROSS_S = 510.0 / 3.6       # the crossing signal: its post 3.6 m from its cap (y 383) to the ground (y 893)


def build_crossing_signal(atlas, im, new_obj):
    """KM-A05, the level-crossing signal in KM1-1: the striped post (x 2457 to 2472, its cap at y 383), the crossbuck
    (two boards 24 px wide crossing at (2465, 425), each 37 degrees off level), the two red lamps on their arms
    ((2423, 528) and (2423, 592), 22 px across), the direction indicator (x 2437 to 2497, y 643 to 687), the rounded
    striped housing on its pedestal (x 2472 to 2537, y 753 to 890) and the low striped guard frame (x 2372 to 2450,
    y 770 to 890). At 141.7 px to the metre (the plan's 3.6 m post)."""
    s, cx, gy = CROSS_S, 2464.5, 893.0
    pic = Pic(atlas, im, (2360, 370, 2545, 895), cx, gy, s)
    z = lambda py: (gy - py) / s
    X = lambda px: (px - cx) / s
    m = Mesh()
    m.cyl(pic, 0, 0, 0.0, z(395), 7.5 / s, 7.0 / s, n=10, top=True, bottom=True)
    m.cyl(pic, 0, 0, z(408), z(383), 8.5 / s, 7.5 / s, n=10, top=True, bottom=True)   # the cap
    L, Wd = 156.0 / s, 23.0 / s
    m.board(pic, 0, z(425), L, Wd, -37.0, -0.07, -0.04)
    m.board(pic, 0, z(425), L, Wd, 37.0, -0.10, -0.07)
    for ly in (528, 592):
        m.disc(pic, X(2423), z(ly), 22 / s, 22 / s, -0.12, 0.0, n=18, dome=0.0)
        m.tube(pic, (X(2423), 0.0, z(ly - 24)), (0.0, 0.0, z(ly - 24)), 3.0 / s, n=6)
    m.box(pic, X(2437), X(2497), -0.12, 0.05, z(687), z(643))                    # the direction indicator
    m.box(pic, X(2474), X(2536), 0.05, 0.30, z(817), z(753))                     # the rounded housing
    m.box(pic, X(2490), X(2517), 0.12, 0.24, 0.0, z(817))                        # its pedestal
    # the guard frame: three striped rails on two posts, open between them
    for y0, y1 in ((770, 792), (803, 830), (848, 872)):
        m.box(pic, X(2372), X(2450), -0.30, -0.26, z(y1), z(y0))
    for x0 in (2372, 2440):
        m.box(pic, X(x0), X(x0 + 10), -0.30, -0.24, 0.0, z(770))
    o = m.object('KmCrossingSignal', new_obj)
    CROPS[o.name] = ((2355, 365, 2550, 900), cx, gy, s)
    return o, dict(id='KM-A05', source='photo/KM1-1 (x 2360 to 2545)', real_size=[1.3, 0.6, 3.6])


def build_crossing_barrier(atlas, im, new_obj):
    """KM-A04, the level-crossing barrier in KM1-1, its arm raised: the striped motor box (x 2548 to 2602, y 732 to
    817) on its leg (x 2555 to 2577), and the striped arm (12 px across, 3.4 m) up from (2566, 735) to (2534, 258). The
    arm is its own part, Arm, with its origin at its pivot on the box, so a level lowers it for the tram."""
    s, cx, gy = CROSS_S, 2575.0, 893.0
    pic = Pic(atlas, im, (2525, 250, 2610, 895), cx, gy, s)
    z = lambda py: (gy - py) / s
    X = lambda px: (px - cx) / s
    m = Mesh()
    m.box(pic, X(2548), X(2602), -0.06, 0.20, z(817), z(732))
    m.cyl(pic, X(2566), 0.07, 0.0, z(817), 11.0 / s, 11.0 / s, n=8, top=True, bottom=True)
    box = m.object('KmCrossingBarrier', new_obj)
    CROPS[box.name] = ((2515, 245, 2615, 900), cx, gy, s)
    a = Mesh()
    # the arm, standing up from its pivot (2566, 735) to its tip (2534, 258), 3.4 m: built in the barrier's frame, then
    # given the pivot as its origin
    p0, p1 = Vector((X(2566), -0.10, z(735))), Vector((X(2534.5), -0.10, z(262)))
    a.tube(pic, p0, p1, 6.0 / s, n=8)
    arm = a.object('Arm', new_obj)
    arm.parent = box
    for v in arm.data.vertices:
        v.co -= p0
    arm.location = p0
    return box, dict(id='KM-A04', source='photo/KM1-1 (x 2525 to 2610)', real_size=[0.4, 0.3, 4.5])


TORII_S = 68.0              # the small torii, further back: 2.8 m across its top beam, 190 px


def build_torii(atlas, im, new_obj):
    """KM-A11, the small vermilion torii above the steps in KM1-1, 68 px to the metre (2.7 m across, 2.7 m tall):
    - its top beam (kasagi) curves up to its tips: its top 563 at the middle (x 2089), 562 at 30 px out, 560 at 60, 556
      at 85, 553 at the tips (92 px out), 10 px deep; the straight beam under it (shimaki) x 2006 to 2170, y 567 to 581;
    - the tie beam (nuki) x 2008 to 2167, y 600 to 610, and the strut between the beams at the middle;
    - the pillars lean in toward the top, as torii pillars do: centred at 2036.5 and 2141.5 under the beams, 4 px further
      out at y 682; the leaves cover the left one's foot from y 683 and the stone wall both from y 700, so below 682 each
      takes the vermilion of the 40 rows above, and stands on a black foot 0.2 m tall (from the dark of the shrine
      behind: the plan's black feet) on the ground at y 736."""
    s, cx, gy = TORII_S, 2089.0, 736.0
    pic = Pic(atlas, im, (1990, 545, 2205, 700), cx, gy, s)
    z = lambda py: (gy - py) / s
    X = lambda px: (px - cx) / s
    m = Mesh()
    # the kasagi: its top edge along the curve, 10 px deep, symmetric about the middle
    prof = [(0, 563), (30, 562), (60, 560), (85, 556), (92, 553)]
    top = [(-dx, y) for dx, y in prof[::-1]] + [(dx, y) for dx, y in prof[1:]]
    outline = [(X(cx + dx), z(y)) for dx, y in top] + [(X(cx + dx), z(y + 10)) for dx, y in top[::-1]]
    cap = Sample(atlas, im.crop((2070, 563, 2110, 566)).resize((64, 16)))      # the cap's own grey-brown, its middle
    m.prism(pic, outline, -0.12, 0.12, top=cap)
    m.box(pic, X(2006), X(2170), -0.09, 0.09, z(581), z(567))                    # the shimaki
    m.box(pic, X(2008), X(2167), -0.08, 0.08, z(610), z(600))                    # the nuki
    m.box(pic, X(2083), X(2095), -0.05, 0.05, z(600), z(581))                    # the strut between them
    black = im.crop((2104, 664, 2110, 676)).resize((24, 48))
    bpic = Pic(atlas, black, (0, 0, 24, 48), 12.0, 48.0, 48.0 / z(722))
    r = 6.8 / s
    for xt, sign in ((2036.5, -1), (2141.5, 1)):
        lean = sign * 4.0 / (682 - 581)          # px out per px down
        xa = lambda py: xt + lean * (py - 581)
        a, b, c = (X(xa(581)), 0, z(581)), (X(xa(682)), 0, z(682)), (X(xa(722)), 0, z(722))
        m.tube(pic, b, a, r, n=10, caps=(False, True))
        m.tube(pic, c, b, r, n=10, ua=(0.0, 40.0 / s), caps=(True, False))   # the hidden part: the 40 rows above
        m.tube(bpic, (X(xa(736)), 0, 0.0), c, r * 1.12, n=10, ua=(-X(xa(736)), 0.0))   # the black foot
    o = m.object('KmToriiSmall', new_obj)
    CROPS[o.name] = ((1990, 545, 2205, 740), cx, gy, s)
    return o, dict(id='KM-A11', source='photo/KM1-1 (x 1990 to 2205); its feet, hidden by the leaves and the stone wall, made',
                   real_size=[2.7, 0.3, 2.7])


# ---------------------------------------------------------------- the review's checks (docs/ASSET_REVIEW.md section 3)
# What was looked at for each prop, by check number, where it differs from the kit's default note; written after
# looking at its eight views and its board at full size.
NOTES = {
    'KmPoleTransformer': {
        4: ('pass', 'round: its back is its front mirrored, as a concrete pole looks; the column above the picture is its own '
                    'band carried on'),
        12: ('pass', 'the wires and the street lamp\'s arm crossing the pole are left out of the model (the level hangs '
                     'its own); the transformers\' faces show none'),
        13: ('pass', 'the column above the picture\'s top (6.6 m to 10 m) made from a clean band of the pole (y 300 to 380)'),
    },
    'KmMirror': {4: ('pass', 'the glass from the picture; the hood\'s back its rim\'s orange; the post round')},
    'KmVendingBlue': {
        4: ('pass', 'its sides and back from KM-P1\'s red machine, turned blue (the photographic KM1-1 shows only its front)'),
        11: ('pass', 'its real drink logo repainted with an invented name (rebrand_machines), as on the red machine'),
        13: ('pass', 'the logo panel repainted (うみかぜ); the side from KM-P1, turned blue'),
    },
    'KmCrossingSignal': {
        4: ('limit', 'the direction indicator\'s, the housing\'s and the guard frame\'s ends are their fronts\' edge '
                     'pixels stretched: KM-P1 draws the crossing from the front only. Seen at three-quarters from the '
                     'street they read; a sheet (ASSET KM-A05) would give them their own'),
    },
    'KmCrossingBarrier': {
        4: ('limit', 'the motor box\'s ends are its front\'s edge pixels stretched (KM-P1 shows the front only)'),
        14: ('pass', 'its arm is its own part, Arm, its origin at the pivot on the box: shown lowering and rising'),
        15: ('pass', 'the arm\'s foot stays inside the box at every angle of its swing (looked at in the motion)'),
    },
    'KmToriiSmall': {
        13: ('pass', 'the pillars\' feet, hidden by leaves and the stone wall in the picture, made: the 40 rows above for '
                     'the vermilion, black feet from the shrine\'s shadow'),
    },
}
