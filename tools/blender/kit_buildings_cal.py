# California houses and shops for the BUILDINGS kit (kit_buildings.py imports this): stucco villas
# under hipped terracotta roofs, a single-storey ranch house with a two-car garage, a two-storey
# Craftsman house with a deep front porch, a white beach condo with glass balconies and a beach
# town's shops. Same contract as the rest of the kit (see kit_buildings.py): origin at the centre of
# the front wall's base, the street face looking along -Y, parts 1 wall / 2 accent / 3 roof.
import math
import numpy as np
from mathutils import Vector
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import decal, flat_ac


# ---------------------------------------------------------------- pieces
def hip(B, x0, x1, y0, y1, ze, rise, over=0.45, t=0.14, mat='roof', edge='roofw', soffit='soffit', caps=True):
    """A hipped roof over the walls' rectangle [x0, x1] x [y0, y1]: four slopes, the ridge along the
    longer side, eaves `over` beyond the walls at height ze (underside), rising `rise` to the ridge.
    The slopes are painted as Spanish barrel tiles (the atlas' 'hip' feature): rounded tiles running
    down the slope in rows, each row's lower edge a little shadowed, every tile its own tone."""
    X0, X1, Y0, Y1 = x0 - over, x1 + over, y0 - over, y1 + over
    dx, dy = X1 - X0, Y1 - Y0
    h = min(dx, dy) / 2
    zt, zr = ze + t, ze + rise + t
    if dx >= dy:
        ym = (Y0 + Y1) / 2
        R0, R1 = (X0 + h, ym, zr), (X1 - h, ym, zr)
        quads = [([(X0, Y0, zt), (X1, Y0, zt), R1, R0], (0, -1, 1)), ([(X1, Y1, zt), (X0, Y1, zt), R0, R1], (0, 1, 1))]
        tris = [([(X0, Y1, zt), (X0, Y0, zt), R0], (-1, 0, 1)), ([(X1, Y0, zt), (X1, Y1, zt), R1], (1, 0, 1))]
        hips = [((X0, Y0, zt), R0), ((X0, Y1, zt), R0), ((X1, Y0, zt), R1), ((X1, Y1, zt), R1)]
    else:
        xm = (X0 + X1) / 2
        R0, R1 = (xm, Y0 + h, zr), (xm, Y1 - h, zr)
        quads = [([(X0, Y1, zt), (X0, Y0, zt), R0, R1], (-1, 0, 1)), ([(X1, Y0, zt), (X1, Y1, zt), R1, R0], (1, 0, 1))]
        tris = [([(X0, Y0, zt), (X1, Y0, zt), R0], (0, -1, 1)), ([(X1, Y1, zt), (X0, Y1, zt), R1], (0, 1, 1))]
        hips = [((X0, Y0, zt), R0), ((X1, Y0, zt), R0), ((X0, Y1, zt), R1), ((X1, Y1, zt), R1)]
    mb = MB()
    # The slopes in rows of tiles, eaves to ridge: each row an inset ring of four slopes whose lower
    # edge stands proud of the row below it by a lip (the tiles' overlap), so the courses catch the
    # light and throw a thin shadow, as real tile courses do. The rings close to the ridge line.
    k = rise / h
    rows = max(3, int(round(h / 0.34)))
    lip = 0.045
    def ring(d):
        dd = min(d, h)
        return (X0 + dd, X1 - dd, Y0 + dd, Y1 - dd), zt + dd * k
    for i in range(rows):
        (ax0, ax1, ay0, ay1), za = ring(h * i / rows)
        (bx0, bx1, by0, by1), zb = ring(h * (i + 1) / rows)
        zl = za + (lip if i > 0 else 0.0)
        sides = [([(ax0, ay0), (ax1, ay0)], [(bx0, by0), (bx1, by0)], (0, -1)),
                 ([(ax1, ay0), (ax1, ay1)], [(bx1, by0), (bx1, by1)], (1, 0)),
                 ([(ax1, ay1), (ax0, ay1)], [(bx1, by1), (bx0, by1)], (0, 1)),
                 ([(ax0, ay1), (ax0, ay0)], [(bx0, by1), (bx0, by0)], (-1, 0))]
        for (pa, pb), (qa, qb), (ex, ey) in sides:
            mb.face([(pa[0], pa[1], zl), (pb[0], pb[1], zl), (qb[0], qb[1], zb), (qa[0], qa[1], zb)], mat, (ex, ey, 1), 1.0)
            if i > 0:
                mb.face([(pa[0], pa[1], za), (pb[0], pb[1], za), (pb[0], pb[1], zl), (pa[0], pa[1], zl)], edge, (ex, ey, 0), 0.5)
    # the tile ends round the eaves, and the soffit under them
    rim = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    outs = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
    for i in range(4):
        (ax, ay), (bx, by) = rim[i], rim[(i + 1) % 4]
        mb.face([(ax, ay, ze), (bx, by, ze), (bx, by, zt), (ax, ay, zt)], edge, outs[i], 0.62)
    mb.face([(X0, Y1, ze), (X1, Y1, ze), (X1, Y0, ze), (X0, Y0, ze)], soffit, (0, 0, -1), 0.85)
    B.add(mb.bm())
    if caps:
        # round ridge and hip tiles, laid over the joints
        if (Vector(R1) - Vector(R0)).length > 0.05:
            B.add(tube([R0, R1], 0.085, edge, 6, caps=True, sm=1))
        for a, b in hips:
            B.add(tube([a, b], 0.075, edge, 6, caps=True, sm=1))
    B.feat('roof', 'hip', x0=X0, x1=X1, y0=Y0, y1=Y1, row=0.34, pitch=0.23)
    if not hasattr(B, 'hips'): B.hips = []
    B.hips.append((X0, X1, Y0, Y1, zt, k, h))
    return zr


def roof_z(B, x, y):
    """The top of the highest hipped roof at the plan point (x, y), or None."""
    best = None
    for X0, X1, Y0, Y1, zt, k, h in getattr(B, 'hips', []):
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            z = zt + min(min(x - X0, X1 - x, y - Y0, Y1 - y), h) * k + 0.04
            best = z if best is None else max(best, z)
    return best


def arch_head(B, wf, u0, u1, v, out=0.05, band=0.13, glass='glass0', mat='trim', n=12):
    """A round arch over an opening: a glazed half-round fanlight from u0 to u1 springing at v, in
    a moulded band (Spanish Revival)."""
    r = (u1 - u0) / 2; c = (u0 + u1) / 2
    mb = MB()
    for i in range(n):
        a0 = math.pi * i / n; a1 = math.pi * (i + 1) / n
        p = lambda a, rr: (c + math.cos(a) * rr, v + math.sin(a) * rr)
        (ia, ja), (ib, jb) = p(a0, r), p(a1, r)
        (oa, pa), (ob, pb) = p(a0, r + band), p(a1, r + band)
        mb.face([(ia, ja, out), (oa, pa, out), (ob, pb, out), (ib, jb, out)], mat, (0, 0, 1), 1.0)
        mb.face([(oa, pa, 0.0), (ob, pb, 0.0), (ob, pb, out), (oa, pa, out)], mat, None, 0.8)
        g = lambda uu, vv: reg_uv(glass, 0.5 + (uu - c) / (2 * r) * 0.9, 0.62 + (vv - v) / r * 0.36, 0.0)
        mb.face([(c, v, 0.012), (ia, ja, 0.012), (ib, jb, 0.012)], 'glass', (0, 0, 1), 1.0, lambda co: g(co.x, co.y))
    put(B, wf, mb.bm())
    # the frame's spokes
    for k in (1, 2):
        a = math.pi * k / 3
        put(B, wf, fbox((c - 0.02, v, 0.0), (c + 0.02, v + r * 0.98, 0.05), 0.005, 'frame') if k == 0 else
            fbox((c + math.cos(a) * 0.0 - 0.02, v, 0.0), (c + 0.02, v + 0.04, 0.05), 0.005, 'frame'))
    put(B, wf, fbox((u0, v - 0.03, 0.0), (u1, v + 0.03, 0.05), 0.005, 'frame'))


def iron_rail(B, wf, u0, u1, v, h=0.9, out=0.32, n=None):
    """A wrought-iron balconette: a top rail, bars and a little ledge under it."""
    n = n or max(4, int((u1 - u0) / 0.12))
    put(B, wf, fbox((u0 - 0.06, v - 0.08, 0.0), (u1 + 0.06, v, out + 0.06), 0.01, 'trim'))
    put(B, wf, tube([(u0, v + h, out), (u1, v + h, out)], 0.025, 'black', 5))
    put(B, wf, tube([(u0, v + 0.12, out), (u1, v + 0.12, out)], 0.018, 'black', 4))
    for x in np.linspace(u0, u1, n):
        put(B, wf, tube([(x, v, out), (x, v + h, out)], 0.012, 'black', 4))
    for x in (u0, u1):
        put(B, wf, tube([(x, v + h, out), (x, v + h, 0.0)], 0.02, 'black', 4))


def garage_door(B, wf, u0, u1, h=2.25, depth=0.16, name='Garage', glazed=True):
    """A sectional garage door: four horizontal panels of raised squares in a white leaf."""
    mb = MB()
    reveal(mb, u0, u1, 0.0, h, depth, bottom=False)
    zf = -depth + 0.04
    mb.face([(u0, 0.0, zf), (u1, 0.0, zf), (u1, h, zf), (u0, h, zf)], 'whitep', (0, 0, 1), 1.0)
    put(B, wf, mb.bm())
    cols = max(4, int(round((u1 - u0) / 0.55)))
    pw = (u1 - u0 - 0.12) / cols
    for r in range(4):
        z0 = 0.08 + r * (h - 0.1) / 4; z1 = z0 + (h - 0.1) / 4 - 0.1
        put(B, wf, fbox((u0, z1 + 0.02, zf), (u1, z1 + 0.06, zf + 0.012), 0.002, 'trimw'))
        for c in range(cols):
            x0 = u0 + 0.06 + c * pw + 0.05
            if r == 3 and glazed:
                # the top section glazed: small dark panes in a white frame
                gm = MB()
                gm.face([(x0, z0 + 0.06, zf + 0.004), (x0 + pw - 0.1, z0 + 0.06, zf + 0.004), (x0 + pw - 0.1, z1 - 0.04, zf + 0.004),
                         (x0, z1 - 0.04, zf + 0.004)], 'glass', (0, 0, 1), 1.0,
                        lambda co, x0=x0, z0=z0, z1=z1: reg_uv('glass0', 0.15 + (co.x - x0) / (pw - 0.1) * 0.7, 0.55 + (co.y - z0) / (z1 - z0) * 0.4))
                put(B, wf, gm.bm())
                for xx, ww in ((x0 - 0.02, 0.03), (x0 + pw - 0.11, 0.03)):
                    put(B, wf, fbox((xx, z0 + 0.04, zf), (xx + ww, z1 - 0.02, zf + 0.03), 0.004, 'whitep'))
                continue
            put(B, wf, fbox((x0, z0 + 0.04, zf), (x0 + pw - 0.1, z1 - 0.02, zf + 0.03), 0.01, 'whitep'))
    # weathering: dust along the bottom of the door
    a0, b0 = wf.ab(u0, 0.0); a1, b1 = wf.ab(u1, h)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=h, length=0.35, k=0.4)
    B.attach.append((name, tuple(round(v, 3) for v in wf.P((u0 + u1) / 2, 1.1, 0.0))))


def column(B, x, y, z0, z1, s=0.26, mat='trim'):
    """A square porch column with a base and a capital."""
    B.add(cbox2((x - s / 2, y - s / 2, z0), (x + s / 2, y + s / 2, z1), 0.02, mat))
    B.add(cbox2((x - s / 2 - 0.05, y - s / 2 - 0.05, z0), (x + s / 2 + 0.05, y + s / 2 + 0.05, z0 + 0.22), 0.02, mat))
    B.add(cbox2((x - s / 2 - 0.05, y - s / 2 - 0.05, z1 - 0.16), (x + s / 2 + 0.05, y + s / 2 + 0.05, z1), 0.02, mat))


# ---------------------------------------------------------------- lived-in detail
def surround(B, wf, u0, u1, v0, v1, w=0.11, out=0.035, mat='trim'):
    """A stucco foam surround round an opening (the California tract house's window trim): a flat band
    a little proud of the wall on the sides and head, the sill below doing for the bottom."""
    put(B, wf, fbox((u0 - w, v1, 0.0), (u1 + w, v1 + w, out), 0.012, mat))
    for a, b in ((u0 - w, u0), (u1, u1 + w)):
        put(B, wf, fbox((a, v0 - 0.02, 0.0), (b, v1, out), 0.012, mat))


def gutter(B, x0, x1, y, z, mat='trim', pipe_x=None, pipe_wall_y=None, pipe_to=0.12, out=-1):
    """A white aluminium gutter along an eave from x0 to x1 at depth y (the eave's edge), hanging
    just under z, and a downpipe from it at pipe_x down to the ground against the wall at depth
    pipe_wall_y."""
    eave_gutter(B, [(x0, y - 0.045 * -out), (x1, y - 0.045 * -out)] if out < 0 else [(x1, y + 0.045), (x0, y + 0.045)], z, mat=mat, size=0.12)
    if pipe_x is None: return
    yg = y - 0.1 if out < 0 else y + 0.1
    yw = pipe_wall_y
    pts = [(pipe_x, yg, z - 0.1), (pipe_x, yg, z - 0.25), (pipe_x, yw, z - 0.6), (pipe_x, yw, pipe_to + 0.25), (pipe_x, yw + 0.12 * out, pipe_to)]
    downpipe(B, pts, r=0.045, mat=mat, brackets=[(pipe_x, yw, zz) for zz in np.arange(0.8, z - 0.8, 1.4)])


def condenser(B, x, y, wall_x=None, wall_y=None, face=(0, -1), z_in=2.2):
    """An AC condenser on a little pad beside the house: a boxy grey cabinet with louvred sides, the
    fan grille on top, the insulated line set running to the wall and up into it, a disconnect box."""
    w, d, h = 0.78, 0.78, 0.72
    B.add(box((x - w / 2 - 0.08, y - d / 2 - 0.08, 0.0), (x + w / 2 + 0.08, y + d / 2 + 0.08, 0.06), 'concw', skip=('-z',)))
    body = cbox2((x - w / 2, y - d / 2, 0.06), (x + w / 2, y + d / 2, 0.06 + h), 0.03, 'galvw')
    B.add(body)
    for sx, sy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        fr = MB()
        if sy:
            yy = y + sy * (d / 2 + 0.002)
            pts = [(x - w * 0.42, yy, 0.12), (x + w * 0.42, yy, 0.12), (x + w * 0.42, yy, h - 0.02), (x - w * 0.42, yy, h - 0.02)]
            uv = lambda co: reg_uv('louvre', (co.x - x + w * 0.42) / (w * 0.84), (co.z - 0.12) / (h - 0.14))
        else:
            xx = x + sx * (w / 2 + 0.002)
            pts = [(xx, y - d * 0.42, 0.12), (xx, y + d * 0.42, 0.12), (xx, y + d * 0.42, h - 0.02), (xx, y - d * 0.42, h - 0.02)]
            uv = lambda co: reg_uv('louvre', (co.y - y + d * 0.42) / (d * 0.84), (co.z - 0.12) / (h - 0.14))
        fr.face(pts, 'tex', (sx, sy, 0), 0.9, uv)
        B.add(fr.bm())
    g, _ = lathe([(0.0, 0.0), (0.3, 0.0), (0.31, 0.02), (0.0, 0.03)], 14, 'black')
    xform(g, T(x, y, 0.06 + h)); B.add(g)
    for i in range(4):
        a = i * math.pi / 2 + 0.4
        B.add(tube([(x, y, 0.06 + h + 0.035), (x + 0.28 * math.cos(a), y + 0.28 * math.sin(a), 0.06 + h + 0.035)], 0.012, 'galvw', 4))
    if wall_x is not None or wall_y is not None:
        wx = wall_x if wall_x is not None else x
        wy = wall_y if wall_y is not None else y
        sx = x + (0.3 if wall_x is None else math.copysign(w / 2, wall_x - x))
        sy = y + (math.copysign(d / 2, wall_y - y) if wall_y is not None else 0.25)
        line = [(sx, sy, 0.35), ((sx + wx) / 2, (sy + wy) / 2, 0.35), (wx, wy, 0.4), (wx, wy, z_in)]
        B.add(tube(line, 0.035, 'black', 6, caps=True, sm=1))
        B.add(tube([(p[0] + 0.07 * (wall_y is not None), p[1] + 0.07 * (wall_x is not None), p[2]) for p in line], 0.016, 'brass', 5, caps=True, sm=1))
        B.add(cbox2((wx - 0.14, wy - 0.14, 1.2), (wx + 0.14, wy + 0.14, 1.62), 0.02, 'galvw'))


def roof_vents(B, pts):
    """Low clay vents set into the tiles (the hooded 'O'Hagin' vents of a tile roof)."""
    for x, y in pts:
        z = roof_z(B, x, y)
        if z is None: continue
        B.add(cbox2((x - 0.24, y - 0.2, z - 0.06), (x + 0.24, y + 0.2, z + 0.16), 0.05, 'roofp'))
        B.add(box((x - 0.17, y - 0.205, z + 0.0), (x + 0.17, y - 0.19, z + 0.09), 'dark'))


def house_number(B, wf, u, v, n=3):
    """A dark plaque with brass numerals beside the door."""
    put(B, wf, fbox((u - 0.06 * n - 0.04, v - 0.09, 0.0), (u + 0.06 * n + 0.04, v + 0.09, 0.025), 0.008, 'metald'))
    for i in range(n):
        x = u - 0.06 * n + 0.06 + i * 0.12
        put(B, wf, fbox((x - 0.03, v - 0.06, 0.025), (x + 0.03, v + 0.06, 0.035), 0.006, 'brass'))


def hose_bib(B, wf, u, v=0.55):
    put(B, wf, tube([(u, v, 0.0), (u, v, 0.1), (u, v - 0.06, 0.13)], 0.018, 'brass', 5))
    put(B, wf, fbox((u - 0.035, v + 0.02, 0.07), (u + 0.035, v + 0.05, 0.1), 0.006, 'red'))


def surfboard(B, x, y, mat, lean=0.18, L=2.1, W_=0.52, t=0.06):
    """A surfboard leaning against the shopfront: a pointed oval, a stripe, a fin."""
    n = 16
    pts = []
    for i in range(n + 1):
        s_ = i / n
        half = W_ / 2 * (math.sin(math.pi * min(1.0, s_ * 1.05)) ** 0.6)
        pts.append((half, s_ * L))
    outline = [(w_, z_) for w_, z_ in pts] + [(-w_, z_) for w_, z_ in reversed(pts)]
    mb = MB()
    import math as _m
    c, sn = _m.cos(lean), _m.sin(lean)
    P = lambda u, z, d: (x + u, y - z * sn + d, z * c + 0.02)
    mb.face([P(u, z, 0.0) for u, z in outline], mat, (0, -1, 0), 1.0)
    mb.face([P(u, z, t) for u, z in reversed(outline)], mat, (0, 1, 0), 0.9)
    for (u0, z0), (u1, z1) in zip(outline, outline[1:] + outline[:1]):
        mb.face([P(u0, z0, 0.0), P(u1, z1, 0.0), P(u1, z1, t), P(u0, z0, t)], 'white', None, 0.9)
    B.add(mb.bm())
    B.add(box((x - 0.035, y - 0.6 * sn - 0.002, 0.6 * c), (x + 0.035, y - 0.6 * sn + 0.002, 1.4 * c), 'white'))


def glass_panel(B, wf, u0, u1, v0, v1, w):
    """A sheet of balcony glass facing out of the wall frame at depth w: the reflective upper part of
    a glass tile, so it reads as glass (dark, the sky caught along its top), not as a painted wall."""
    mb = MB()
    uv = lambda co: reg_uv('glass0', 0.1 + (co.x - u0) / (u1 - u0) * 0.8, 0.45 + (co.y - v0) / (v1 - v0) * 0.5)
    mb.face([(u0, v0, w), (u1, v0, w), (u1, v1, w), (u0, v1, w)], 'glass', (0, 0, 1), 1.0, uv)
    mb.face([(u1, v0, w - 0.012), (u0, v0, w - 0.012), (u0, v1, w - 0.012), (u1, v1, w - 0.012)], 'glass', (0, 0, -1), 0.8, uv)
    put(B, wf, mb.bm())


def wall_vent(B, wf, u, v, w=0.36, h=0.14):
    """A screened foundation / garage vent: a slot in the stucco with a louvred grille."""
    vv = fbox((u - w / 2, v - h / 2, -0.01), (u + w / 2, v + h / 2, 0.012), 0.004, 'tex')
    uv_fn(vv, faces_facing(vv, (0, 0, 1), 0.9), 'vent', lambda co: ((co.x - u + w / 2) / w, (co.y - v + h / 2) / h), 0.02)
    put(B, wf, vv)


def stucco_box(B, x0, x1, y0, y1, h, fronts=(), rights=(), lefts=(), backs=(), v0=0.0, front_wf=None, base=True):
    """Four plain stucco walls round [x0, x1] x [y0, y1], up to h, with openings in each, and a
    low painted base course (stucco houses have no plinth)."""
    F = WF((0, y0, 0), (1, 0, 0), 'front')
    Rt = WF((x1, 0, 0), (0, 1, 0), 'right')
    Lf = WF((x0, 0, 0), (0, -1, 0), 'left')
    Bk = WF((0, y1, 0), (-1, 0, 0), 'back')
    wall(B, F, x0, x1, h, list(fronts), v0)
    wall(B, Rt, y0, y1, h, list(rights), v0)
    wall(B, Lf, -y1, -y0, h, list(lefts), v0)
    wall(B, Bk, -x1, -x0, h, list(backs), v0)
    if base:
        plinth(B, [(x0, y1), (x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.2, out=0.03, mat='conc')
    return F, Rt, Lf, Bk


def cal_window(B, wf, u0, u1, v0, v1, cols=2, seed=0, glass='glass0', cheap=False, register=True, rows=1, trim=True):
    """A white vinyl window deep in the stucco: a slim frame, grid muntins when rows > 1, a sill and a
    flat stucco surround round the sides and head."""
    window(B, wf, u0, u1, v0, v1, depth=0.19, fw=0.06, cols=cols, rows=rows, frame='frame', glass=glass, sill='trim', head=None,
           seed=seed, cheap=cheap, register=register)
    if trim: surround(B, wf, u0, u1, v0, v1)


# ---------------------------------------------------------------- VillaStucco
def villa_stucco(B):
    """Two storeys of smooth stucco under a hipped tile roof, a single-storey two-car garage beside
    it under its own lower hip, an arched entry with a fanlight, an arched picture window, an iron
    balconette upstairs, coach lamps and a terracotta pot or two."""
    W, H, D = B.W, B.H, B.D
    xl, xg = -W / 2, W / 2 - 4.6           # the house; the garage from xg to the right
    gh, gd = 3.0, 6.6
    door_o = (xg - 2.4, xg - 1.35, 0.0, 2.35)
    pic = (xl + 0.9, xl + 2.9, 0.75, 2.2)
    up = [(xl + 0.9, xl + 2.3, 3.6, 4.9), (xg - 2.55, xg - 1.2, 3.6, 4.9)]
    F, Rt, Lf, Bk = stucco_box(B, xl, xg, 0.0, D, H, fronts=[door_o, pic] + up, rights=[(6.5, 7.6, 3.7, 4.9)],
                               lefts=[(-6.0, -4.8, 1.0, 2.2), (-6.0, -4.8, 3.7, 4.9)])
    GF, GR, GL, GB = stucco_box(B, xg, W / 2, 0.0, gd, gh, fronts=[(xg + 0.55, W / 2 - 0.55, 0.0, 2.3)], rights=[(3.6, 4.5, 1.1, 2.0)])
    # entry: a stucco surround with an arch over the door and a fanlight
    door(B, F, *door_o, mat='accent', glass=None, panels=((2, 3),), name='Door')
    arch_head(B, F, door_o[0], door_o[1], door_o[3] + 0.02, band=0.12)
    put(B, F, fbox((door_o[0] - 0.42, 0.0, 0.0), (door_o[0] - 0.12, 3.15, 0.14), 0.03, 'wall'))
    put(B, F, fbox((door_o[1] + 0.12, 0.0, 0.0), (door_o[1] + 0.42, 3.15, 0.14), 0.03, 'wall'))
    put(B, F, fbox((door_o[0] - 0.42, 3.15, 0.0), (door_o[1] + 0.42, 3.4, 0.16), 0.03, 'trim'))
    steps(B, F, door_o[0] - 0.5, door_o[1] + 0.5, [0.16], tread=0.45)
    lantern(B, F, door_o[0] - 0.27, 2.2, out=0.2, name='Lamp')
    # the picture window under its own arch, the upstairs windows, a balconette on one
    cal_window(B, F, *pic, cols=3, seed=611, glass='glass1')
    arch_head(B, F, pic[0], pic[1], pic[3] + 0.0, band=0.12, glass='glass0')
    for k, wo in enumerate(up):
        cal_window(B, F, *wo, cols=2, rows=2, seed=612 + k, glass=('glass0', 'glass3')[k])
    iron_rail(B, F, up[1][0] - 0.1, up[1][1] + 0.1, up[1][2] - 0.05, h=0.75, out=0.3)
    cal_window(B, Rt, 6.5, 7.6, 3.7, 4.9, cols=2, seed=614, cheap=True)
    cal_window(B, Lf, -6.0, -4.8, 1.0, 2.2, cols=2, seed=615, cheap=True, register=False)
    cal_window(B, Lf, -6.0, -4.8, 3.7, 4.9, cols=2, seed=616, cheap=True, register=False)
    # the garage: a white sectional door, coach lamps either side, a side window
    garage_door(B, GF, xg + 0.55, W / 2 - 0.55, h=2.3)
    for u in (xg + 0.3, W / 2 - 0.3):
        lantern(B, GF, u, 2.05, out=0.17, name='Lamp')
    cal_window(B, GR, 3.6, 4.5, 1.1, 2.0, cols=1, seed=617, cheap=True)
    B.add(box((xg + 0.2, -1.6, 0.0), (W / 2 - 0.2, 0.0, 0.03), 'conc', skip=('-z',)))       # the driveway's end
    # trim: a slim band under the eaves all round
    cornice(B, [(xl, D), (xl, 0.0), (xg, 0.0), (xg, D)], H - 0.2, steps=((0.04, 0.08), (0.08, 0.1)))
    cornice(B, [(xg, gd), (xg, 0.0), (W / 2, 0.0), (W / 2, gd)], gh - 0.18, steps=((0.04, 0.07), (0.07, 0.08)))
    top = hip(B, xl, xg, 0.0, D, H, B.RH, over=0.5)
    hip(B, xg, W / 2, 0.0, gd, gh, 1.35, over=0.42)
    # a chimney in stucco with a little hipped cap
    B.add(cbox2((xl + 0.5, D - 2.4, H - 0.5), (xl + 1.3, D - 1.6, top + 0.5), 0.04, 'wall'))
    B.add(cbox2((xl + 0.4, D - 2.5, top + 0.5), (xl + 1.4, D - 1.5, top + 0.62), 0.03, 'trim'))
    for P, seed in (((door_o[0] - 0.75, -0.45, 0.0), 618), ((door_o[1] + 0.75, -0.5, 0.0), 619)):
        pot(B, P, 0.24, 0.5, 'pot', 'flowers', seed=seed)
    # the lived-in detail: gutters and downpipes, the AC condenser on its pad with the line set up
    # the side wall, the meter and a vent on the garage, roof vents, a tap, the house number
    gutter(B, xl - 0.5, xg + 0.5, -0.5, H - 0.04, pipe_x=xl + 0.16, pipe_wall_y=-0.07)
    gutter(B, xg - 0.42, W / 2 + 0.42, -0.42, gh - 0.04, pipe_x=W / 2 - 0.16, pipe_wall_y=-0.07)
    condenser(B, xl - 0.8, 3.6, wall_x=xl - 0.07, z_in=2.3)
    meter_box(B, GR, 1.6, 1.1)
    wall_vent(B, GR, 4.4, 0.35)
    roof_vents(B, [(xl + 2.2, 1.4), (xg - 1.4, 1.2)])
    hose_bib(B, F, xl + 0.55)
    house_number(B, F, door_o[1] + 0.62, 1.72)
    B.feat('front', 'ao', a0=xl, a1=xg, b=H - 0.02, length=0.6, k=0.45)
    return top + 0.62


# ---------------------------------------------------------------- VillaRanch
def villa_ranch(B):
    """A single-storey stucco ranch house: long and low under a hipped tile roof, a two-car garage
    standing forward of it, a recessed entry with a slim column, wide windows, solar panels on the
    roof and a strip of planting in front."""
    W, H, D = B.W, B.H, B.D
    xl, xg = -W / 2, W / 2 - 4.4
    gf = -0.9                                # the garage's front, forward of the house
    door_o = (xg - 1.7, xg - 0.75, 0.0, 2.3)
    wins = [(xl + 0.8, xl + 3.2, 0.8, 2.15), (xl + 4.0, xl + 5.8, 0.8, 2.15)]
    F, Rt, Lf, Bk = stucco_box(B, xl, xg, 0.0, D, H, fronts=[door_o] + wins, lefts=[(-6.4, -5.2, 1.0, 2.1)])
    GF, GR, GL, GB = stucco_box(B, xg, W / 2, gf, D - 2.0, H, fronts=[(xg + 0.5, W / 2 - 0.5, 0.0, 2.2)], rights=[(2.0, 3.0, 1.1, 2.0)],
                                lefts=[(-(gf + 1.6), -(gf + 0.6), 1.0, 2.0)])
    door(B, F, *door_o, mat='accent', glass=0.3, panels=((1, 2),), name='Door')
    for k, wo in enumerate(wins):
        cal_window(B, F, *wo, cols=3 if k == 0 else 2, rows=2, seed=621 + k, glass=('glass1', 'glass0')[k])
    lantern(B, F, door_o[1] + 0.3, 2.0, out=0.18, name='Lamp')
    # the entry porch: the roof's eave carried forward on a slim square column
    column(B, door_o[0] - 0.9, -1.25, 0.0, H - 0.05, s=0.22)
    B.add(box((door_o[0] - 1.2, -1.5, 0.0), (xg, 0.0, 0.12), 'concw', skip=('-z',)))
    garage_door(B, GF, xg + 0.5, W / 2 - 0.5, h=2.2)
    lantern(B, GF, xg + 0.27, 2.0, out=0.16, name='Lamp')
    cal_window(B, GR, 2.0, 3.0, 1.1, 2.0, cols=1, seed=623, cheap=True)
    cal_window(B, GL, -(gf + 1.6), -(gf + 0.6), 1.0, 2.0, cols=1, seed=624, cheap=True, register=False)
    cal_window(B, Lf, -6.4, -5.2, 1.0, 2.1, cols=2, seed=625, cheap=True, register=False)
    cornice(B, [(xl, D), (xl, 0.0), (xg, 0.0)], H - 0.16, steps=((0.04, 0.07), (0.07, 0.08)))
    # one hip over the house and its porch, a second, crossing it, over the garage
    top = hip(B, xl, xg, -1.4, D, H, B.RH, over=0.45)
    hip(B, xg, W / 2, gf, D - 2.0, H, B.RH * 0.95, over=0.45)
    # solar panels on the hip at the front of the house's roof (its ridge runs front to back), on the tiles
    X0, X1, Y0, Y1, zt_, k_, h_ = B.hips[0]
    xm = (X0 + X1) / 2
    for x0 in (xm - 0.86, xm + 0.86):
        yy = Y0 + 1.75
        zz = zt_ + (yy - Y0) * k_ + 0.12
        sp = fbox((-0.82, -0.55, -0.025), (0.82, 0.55, 0.025), 0.01, 'tex', back=True)
        uv_fn(sp, faces_facing(sp, (0, 0, 1), 0.9), 'solar', lambda co: (0.5 + co.x / 1.64, 0.5 + co.y / 1.1), 0.02)
        xform(sp, T(x0, yy, zz) @ R(math.atan(k_), 'X')); B.add(sp)
    # a strip of gravel and shrubs along the front
    B.add(box((xl + 0.3, -0.75, 0.0), (door_o[0] - 1.4, -0.05, 0.08), 'concw', skip=('-z',)))
    for x in (xl + 1.0, xl + 2.5, xl + 4.3):
        pot(B, (x, -0.42, 0.06), 0.001, 0.001, 'soil', 'bush', seed=int(x * 10) + 700, scale=1.6)
    gutter(B, xl - 0.45, xg + 0.45, -1.85, H - 0.04)
    gutter(B, xg - 0.45, W / 2 + 0.45, gf - 0.45, H - 0.04, pipe_x=W / 2 - 0.16, pipe_wall_y=gf - 0.07)
    condenser(B, xl - 0.8, 4.2, wall_x=xl - 0.07, z_in=2.0)
    meter_box(B, GR, 4.5, 1.1)
    wall_vent(B, GR, 1.0, 0.35)
    roof_vents(B, [(xl + 7.0, 1.6), (W / 2 - 1.9, 0.6)])
    hose_bib(B, F, xl + 0.5)
    house_number(B, F, door_o[0] - 0.45, 1.75)
    B.feat('front', 'ao', a0=xl, a1=W / 2, b=H - 0.02, length=0.5, k=0.45)
    return top + 0.1


# ---------------------------------------------------------------- CraftsmanPorch
def craftsman_porch(B):
    """A two-storey Craftsman house in white lap siding under a gable to the street: a full-width
    front porch with square columns, a rail and a low-pitched roof of its own, a gabled dormer-like
    upper front with paired windows, and painted trim."""
    W, H, D, RH = B.W, B.H, B.D, B.RH
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    gf = 3.0
    t, cap = 0.16, 0.1
    k = (RH - t - cap) / (W / 2)
    apex = H + (W / 2) * k
    door_o = (-0.55, 0.45, 0.25, 2.5)
    wg = [(-W / 2 + 0.8, -1.4, 0.95, 2.4), (1.4, W / 2 - 0.8, 0.95, 2.4)]
    wu = [(-2.2, -0.9, 3.6, 4.95), (0.9, 2.2, 3.6, 4.95)]
    gable = [(-W / 2, H), (0.0, apex), (W / 2, H)]
    wall(B, F, -W / 2 + c, W / 2 - c, gf, [door_o] + wg, 0.2, 'lap')
    wall(B, Rt, c, D - c, gf, [(3.0, 4.2, 1.0, 2.3)], 0.2, 'lap')
    wall(B, Lf, -D + c, -c, gf, [(-4.2, -3.0, 1.0, 2.3)], 0.2, 'lap')
    wall(B, Bk, -W / 2 + c, W / 2 - c, gf, [], 0.2, 'lap')
    box_shell_corners(B, 0.2, gf, c)
    wall(B, F, -W / 2, W / 2, gable, wu, gf, 'lap')
    wall(B, Rt, 0, D, H, [(3.2, 4.3, 3.7, 4.9)], gf, 'lap')
    wall(B, Lf, -D, 0, H, [], gf, 'lap')
    wall(B, Bk, -W / 2, W / 2, gable, [], gf, 'flat')
    for x, y in ((W / 2, 0), (-W / 2, 0), (W / 2, D), (-W / 2, D)):
        corner_board(B, x, y, 0.2, H - 0.02)
    for path, closed in ring_path(B):
        string_course(B, path, gf - 0.08, gf + 0.08, out=0.06)
        plinth(B, path, 0.3, mat='stone', closed=closed)
    e = 0.45
    a0, a1 = -W / 2 - e, W / 2 + e
    z0 = H - e * k
    top = pitched(B, 'y', a0, a1, -0.3, D + 0.3, z0, (W / 2 + e) * k, t=t)
    knee_brackets(B, F, [-W / 2 + 0.3, W / 2 - 0.3], z0 - 0.02, 0.45)
    attic_vent(B, F, 0.0, apex - 1.1, r=0.32)
    door(B, F, *door_o, mat='accent', glass=0.35, panels=((1, 2),), name='Door')
    for kk, wo in enumerate(wg):
        window(B, F, *wo, cols=3, transom=0.75, head='casing', frame='frame', glass=('glass0', 'glass1')[kk], seed=631 + kk)
    for kk, wo in enumerate(wu):
        window(B, F, *wo, cols=2, head='casing', frame='frame', glass=('glass2', 'glass3')[kk], seed=633 + kk)
    window(B, Rt, 3.0, 4.2, 1.0, 2.3, cols=2, frame='frame', glass='glass0', seed=635, cheap=True)
    window(B, Rt, 3.2, 4.3, 3.7, 4.9, cols=2, frame='frame', glass='glass1', seed=636, cheap=True)
    window(B, Lf, -4.2, -3.0, 1.0, 2.3, cols=2, frame='frame', glass='glass2', seed=637, cheap=True, register=False)
    # the porch: a deck on a stone base, columns on piers, a rail, a low hipped roof
    pd = 2.3
    B.add(cbox2((-W / 2 - 0.1, -pd, 0.0), (W / 2 + 0.1, 0.0, 0.42), 0.02, 'stone'))
    B.add(box((-W / 2, -pd + 0.05, 0.42), (W / 2, 0.0, 0.47), 'woodc', skip=('-z',)))
    steps(B, F, door_o[0] - 0.4, door_o[1] + 0.4, [0.3, 0.15], tread=0.32, back=pd)
    for x in (-W / 2 + 0.2, -1.2, 1.2, W / 2 - 0.2):
        B.add(cbox2((x - 0.22, -pd + 0.02, 0.47), (x + 0.22, -pd + 0.46, 1.05), 0.02, 'stone'))
        column(B, x, -pd + 0.24, 1.05, 2.85, s=0.24)
    for x0, x1 in ((-W / 2 + 0.42, -1.42), (1.42, W / 2 - 0.42)):
        B.add(cbox2((x0, -pd + 0.18, 1.32), (x1, -pd + 0.3, 1.4), 0.01, 'trim'))
        B.add(cbox2((x0, -pd + 0.18, 0.55), (x1, -pd + 0.3, 0.62), 0.01, 'trim'))
        for x in np.linspace(x0 + 0.08, x1 - 0.08, int((x1 - x0) / 0.14)):
            B.add(box((x - 0.022, -pd + 0.21, 0.62), (x + 0.022, -pd + 0.27, 1.32), 'trimw'))
    B.add(cbox2((-W / 2 - 0.1, -pd - 0.05, 2.85), (W / 2 + 0.1, -pd + 0.4, 3.05), 0.02, 'trim'))
    shed(B, -W / 2 - 0.35, W / 2 + 0.35, -pd - 0.4, 0.05, 3.05, 3.55, t=0.12, pitch=0.3, depth=0.03, mat='roof', edge_mat='roofw',
         fascia_mat='trim', feat=False)
    lantern(B, F, door_o[1] + 0.35, 2.05, name='Lamp')
    # porch life: a pair of chairs, a mat, a hanging plant
    for x in (-2.3, -1.65):
        B.add(cbox2((x - 0.25, -1.2, 0.47), (x + 0.25, -0.7, 0.9), 0.04, 'woodc'))
        B.add(cbox2((x - 0.25, -0.75, 0.9), (x + 0.25, -0.68, 1.35), 0.03, 'woodc'))
    B.add(box((door_o[0] - 0.1, -0.7, 0.47), (door_o[1] + 0.1, -0.1, 0.49), 'cloth5', skip=('-z',)))
    pot(B, (2.6, -0.9, 0.47), 0.2, 0.36, 'pot3', 'flowers', seed=638)
    gable_gutters(B, a0, a1, -0.3, D + 0.3, z0 - 0.04, pipe_y=0.35)
    condenser(B, W / 2 + 0.8, 5.2, wall_x=W / 2 + 0.07, z_in=2.1)
    meter_box(B, Rt, 6.6, 1.15)
    mailbox(B, F, door_o[1] + 0.6, 1.35)
    house_number(B, F, door_o[0] - 0.55, 2.05)
    hose_bib(B, F, -W / 2 + 0.45, 0.6)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=gf - 0.02, length=0.6, k=0.35)
    return top + 0.11


# ---------------------------------------------------------------- BeachCondo
def beach_condo(B):
    """A white three-storey beach condo: smooth stucco, a flat roof with a glass-railed roof deck,
    wide sliding windows behind glass balconies on the upper floors, a garage at street level and
    a stair up to a recessed front door."""
    W, H, D = B.W, B.H, B.D
    pp = 0.5
    ff = [0.0, 3.0, 6.0]                     # floor levels
    door_o = (W / 2 - 1.6, W / 2 - 0.65, 0.0, 2.3)
    gar = (-W / 2 + 0.6, -W / 2 + 4.0, 0.0, 2.3)
    slides = [(-W / 2 + 0.7, W / 2 - 2.4, f + 0.15, f + 2.45) for f in ff[1:]]
    side_win = (W / 2 - 2.0, W / 2 - 0.7, 4.0, 5.2)
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H + pp, [door_o, gar] + slides + [(W / 2 - 1.9, W / 2 - 0.8, 3.9, 5.1), (W / 2 - 1.9, W / 2 - 0.8, 6.9, 8.1)], 0.0)
    wall(B, Rt, 0, D, H + pp, [(2.0, 3.5, 3.6, 5.0), (2.0, 3.5, 6.6, 8.0)], 0.0)
    wall(B, Lf, -D, 0, H + pp, [(-3.5, -2.0, 3.6, 5.0), (-3.5, -2.0, 6.6, 8.0)], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp, [], 0.0)
    flat_top(B, H, pp)
    for f in ff[1:]:
        string_course(B, [(-W / 2, D), (-W / 2, 0.0), (W / 2, 0.0), (W / 2, D)], f - 0.12, f + 0.02, out=0.04, mat='wall')
    door(B, F, *door_o, mat='accent', glass=0.6, panels=((1, 1),), name='Door')
    garage_door(B, F, gar[0], gar[1], h=2.3)
    for k, s in enumerate(slides):
        window(B, F, *s, depth=0.2, fw=0.06, cols=3, frame='alu', glass=('glass1', 'glass3')[k], sill=None, head=None, seed=641 + k)
        # the glass balcony: a slab, frosted-clear panels and a slim aluminium top rail
        bx0, bx1 = s[0] - 0.25, s[1] + 0.25
        z = s[2] - 0.15
        put(B, F, fbox((bx0, z - 0.2, 0.0), (bx1, z, 1.3), 0.02, 'whitep'))
        for side, (u0, u1) in enumerate(((bx0 + 0.03, bx1 - 0.03),)):
            glass_panel(B, F, u0, u1, z, z + 1.0, 1.215)
            put(B, F, tube([(u0, z + 1.02, 1.215), (u1, z + 1.02, 1.215)], 0.025, 'alu', 5))
        for u in (bx0 + 0.03, bx1 - 0.03):
            put(B, F, fbox((u, z, 0.0), (u + 0.02, z + 1.0, 1.23), 0.004, 'alu'))
    for k, v in enumerate((3.9, 6.9)):
        window(B, F, W / 2 - 1.9, W / 2 - 0.8, v, v + 1.2, cols=1, frame='alu', glass='glass0', sill=None, head=None, seed=643 + k)
    for k, v in enumerate((3.6, 6.6)):
        window(B, Rt, 2.0, 3.5, v, v + 1.4, cols=2, frame='alu', glass='glass2', seed=645 + k, cheap=True)
        window(B, Lf, -3.5, -2.0, v, v + 1.4, cols=2, frame='alu', glass='glass1', seed=647 + k, cheap=True, register=False)
    # the roof deck's glass rail
    for (u0, u1, y0, y1) in ((-W / 2 + 0.3, W / 2 - 0.3, 0.2, 0.25),):
        glass_panel(B, WF((0, y0, 0), (1, 0, 0), 'front'), u0, u1, H + pp, H + pp + 0.95, 0.0)
        B.add(tube([(u0, (y0 + y1) / 2, H + pp + 0.97), (u1, (y0 + y1) / 2, H + pp + 0.97)], 0.025, 'alu', 5))
    B.add(cbox2((W / 2 - 2.6, D - 3.0, H), (W / 2 - 0.6, D - 1.0, H + pp + 2.2), 0.03, 'wall'))      # the stair head
    lantern(B, F, door_o[0] - 0.28, 2.0, out=0.16, name='Lamp')
    pot(B, (door_o[0] - 0.7, -0.4, 0.0), 0.26, 0.55, 'pot2', 'bush', seed=649, scale=1.2)
    B.add(box((-W / 2, -1.4, 0.0), (W / 2, 0.0, 0.03), 'conc', skip=('-z',)))
    for x in (-W / 2 + 1.4, -W / 2 + 2.6):
        flat_ac(B, x, D - 2.2, H)
    wall_pipe(B, -W / 2 + 0.16, -0.08, H + pp - 0.1)
    meter_box(B, Rt, 1.4, 1.0)
    house_number(B, F, door_o[0] - 0.4, 2.55)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H + pp - 0.02, length=0.4, k=0.3)
    return H + pp + 2.2


# ---------------------------------------------------------------- ShopBeach
def shop_beach(B):
    """A beach town's shop: one tall storey of stucco with a stepped parapet, a wide shopfront
    under a fabric awning, a painted sign board and a bench out front."""
    W, H, D = B.W, B.H, B.D
    pp = 0.9
    sf = (-W / 2 + 0.6, W / 2 - 1.9, 0.0, 3.0)
    door_o = (W / 2 - 1.6, W / 2 - 0.6, 0.0, 2.55)
    F, Rt, Bk, Lf = frames(B)
    step = [(-W / 2, H + pp - 0.35), (-1.2, H + pp - 0.35), (-1.2, H + pp), (1.2, H + pp), (1.2, H + pp - 0.35), (W / 2, H + pp - 0.35)]
    wall(B, F, -W / 2, W / 2, step, [sf, door_o], 0.0)
    wall(B, Rt, 0, D, H + pp - 0.35, [(3.0, 4.0, 1.4, 2.6)], 0.0)
    wall(B, Lf, -D, 0, H + pp - 0.35, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp - 0.35, [], 0.0)
    flat_top(B, H, pp - 0.35)
    put(B, F, fbox((-1.3, H + pp - 0.08, 0.0), (1.3, H + pp + 0.05, 0.1), 0.02, 'trim'))
    for x0, x1 in ((-W / 2 - 0.05, -1.2), (1.2, W / 2 + 0.05)):
        put(B, F, fbox((x0, H + pp - 0.43, 0.0), (x1, H + pp - 0.3, 0.08), 0.02, 'trim'))
    window(B, F, *sf, depth=0.18, fw=0.07, cols=3, frame='alud', glass='glass3', sill='conc', head=None, seed=651)
    door(B, F, *door_o, mat='alud', glass=0.85, panels=((1, 1),), name='Door')
    awning(B, F, sf[0] - 0.1, sf[1] + 0.1, sf[3] + 0.55, 1.2, 0.5, 6, mat_a='accent', mat_b='cream', valance=0.24, scallops=False)
    pw = sign_board(B, F, -W / 2 + 0.9, W / 2 - 0.9, H - 0.2, H + 0.55, out=0.12, frame='accentp', panel='creamp')
    decal(B, F, -W / 2 + 1.0, W / 2 - 1.0, H - 0.1, H + 0.45, pw + 0.004, 'sg_surf')
    gooseneck(B, F, -1.4, H + 0.65, name='Lamp')
    gooseneck(B, F, 1.4, H + 0.65, name='Lamp')
    bench(B, F, sf[0] + 0.4, sf[0] + 2.0)
    pot(B, (door_o[1] + 0.35, -0.4, 0.0), 0.22, 0.45, 'pot', 'flowers', seed=652)
    for x in (-1.2, 1.4):
        flat_ac(B, x, D - 2.5, H)
    wall_pipe(B, W / 2 - 0.16, -0.08, H + pp - 0.45)
    meter_box(B, Rt, 6.4, 1.1)
    for k, (x, col) in enumerate(((sf[0] + 2.35, 'cloth2'), (sf[0] + 2.85, 'cloth3'))):
        surfboard(B, x, -0.12 - 0.05 * k, col, lean=0.16 + 0.04 * k)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.4, k=0.3)
    return H + pp + 0.05


# ---------------------------------------------------------------- ShopMission
def shop_mission(B):
    """A Spanish Revival corner shop: two storeys of stucco, a curved Mission parapet over the
    middle, a tiled pent roof over the shopfront on carved brackets, arched upper windows with iron
    balconettes, a recessed corner door."""
    W, H, D = B.W, B.H, B.D
    pp = 0.6
    n = 9
    curve = [(-W / 2, H + pp)]
    for i in range(n + 1):
        u = -1.8 + 3.6 * i / n
        curve.append((u, H + pp + 0.95 * math.cos((u / 1.8) * math.pi / 2) ** 0.7))
    curve.append((W / 2, H + pp))
    sf = (-W / 2 + 0.6, W / 2 - 2.0, 0.0, 2.9)
    door_o = (W / 2 - 1.7, W / 2 - 0.7, 0.0, 2.55)
    up = [(-W / 2 + 1.0, -W / 2 + 2.2, 4.0, 5.4), (-0.6, 0.6, 4.0, 5.4), (W / 2 - 2.2, W / 2 - 1.0, 4.0, 5.4)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, curve, [sf, door_o] + [(a, b_, c, d - 0.55) for a, b_, c, d in up], 0.0)
    wall(B, Rt, 0, D, H + pp, [(3.0, 4.2, 4.0, 5.3)], 0.0)
    wall(B, Lf, -D, 0, H + pp, [], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp, [], 0.0)
    flat_top(B, H, pp)
    window(B, F, *sf, depth=0.18, fw=0.07, cols=3, frame='woodd', glass='glass3', sill='conc', head=None, seed=661)
    door(B, F, *door_o, mat='woodd', glass=0.55, panels=((1, 2),), name='Door')
    for k, wo in enumerate(up):
        window(B, F, wo[0], wo[1], wo[2], wo[3] - 0.55, cols=2, frame='frame', glass=('glass0', 'glass1', 'glass3')[k], sill=None, head=None, seed=662 + k)
        arch_head(B, F, wo[0], wo[1], wo[3] - 0.55, band=0.1, glass='glass0')
        iron_rail(B, F, wo[0] - 0.1, wo[1] + 0.1, wo[2] - 0.05, h=0.7, out=0.28)
    window(B, Rt, 3.0, 4.2, 4.0, 5.3, cols=2, frame='frame', glass='glass0', seed=665, cheap=True)
    # the tiled pent roof over the shopfront, on timber brackets
    knee_brackets(B, F, [sf[0] + 0.2, sf[1] - 0.2, door_o[1] + 0.2], 3.55, 0.8, drop=0.6)
    shed(B, -W / 2 - 0.1, W / 2 + 0.1, -0.95, 0.05, 3.55, 3.95, t=0.12, pitch=0.3, depth=0.03, mat='roof', edge_mat='roofw',
         fascia_mat='woodd', feat=False)
    B.feat('roof', 'hip', x0=-W / 2 - 0.1, x1=W / 2 + 0.1, y0=-1.05, y1=0.05, row=0.3, pitch=0.22)
    pw = sign_board(B, F, -1.5, 1.5, 3.05, 3.45, out=0.1, frame='woodd', panel='creamp')
    decal(B, F, -1.4, 1.4, 3.13, 3.37, pw + 0.004, 'sg_cantina')
    lantern(B, F, door_o[0] - 0.3, 2.2, name='Lamp')
    for P, s in (((sf[0] + 0.3, -0.45, 0.0), 666), ((door_o[1] + 0.35, -0.45, 0.0), 667)):
        pot(B, P, 0.26, 0.55, 'pot', 'bush', seed=s, scale=1.2)
    flat_ac(B, 1.5, D - 2.4, H)
    wall_pipe(B, -W / 2 + 0.16, -0.08, H + pp - 0.1)
    for k, x in enumerate((sf[0] + 0.2, sf[1] - 0.2)):          # hanging baskets from the brackets
        B.add(tube([(x, -0.75, 3.5), (x, -0.75, 3.05)], 0.008, 'black', 4))
        pot(B, (x, -0.75, 2.78), 0.2, 0.22, 'pot', 'flowers', seed=668 + k, scale=1.1)
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H - 0.02, length=0.4, k=0.3)
    return H + pp + 0.95


# ---------------------------------------------------------------- the pier
def pier_deck(B, x0, x1, y0, y1, zt, rail=True, lamps=(), piles_y=(), pile_xs=None):
    """A pier's deck: dark timber planking on a concrete edge beam, white railings along both
    sides, concrete pile bents underneath down into the water, globe lamps on the rail."""
    B.add(cbox2((x0, y0, zt - 0.45), (x1, y1, zt - 0.08), 0.03, 'conc'))
    B.add(box((x0 + 0.08, y0, zt - 0.08), (x1 - 0.08, y1, zt), 'woodd', skip=('-z',)))
    for k in range(int((y1 - y0) / 0.6)):
        y = y0 + 0.3 + k * 0.6
        B.add(box((x0 + 0.1, y - 0.012, zt), (x1 - 0.1, y + 0.012, zt + 0.004), 'black'))
    xs = pile_xs or [x0 + 0.35, (x0 + x1) / 2 - 0.9, (x0 + x1) / 2 + 0.9, x1 - 0.35]
    for y in piles_y:
        for x in xs:
            B.add(tube([(x, y, -4.0), (x, y, zt - 0.45)], 0.24, 'conc', 8, caps=False, sm=1))
        B.add(cbox2((x0 + 0.1, y - 0.28, zt - 1.05), (x1 - 0.1, y + 0.28, zt - 0.45), 0.03, 'conc'))
        for a, b in ((xs[0], xs[1]), (xs[2], xs[3])):
            B.add(tube([(a, y, 0.4), (b, y, zt - 1.1)], 0.07, 'conc', 5, caps=True, sm=1))
    if rail:
        for x in (x0 + 0.12, x1 - 0.12):
            B.add(cbox2((x - 0.08, y0, zt + 0.95), (x + 0.08, y1, zt + 1.08), 0.02, 'trim'))
            B.add(cbox2((x - 0.05, y0, zt + 0.48), (x + 0.05, y1, zt + 0.56), 0.01, 'trim'))
            for k in range(int((y1 - y0) / 2.0) + 1):
                y = min(y0 + k * 2.0, y1 - 0.1)
                B.add(cbox2((x - 0.09, y - 0.09, zt), (x + 0.09, y + 0.09, zt + 1.0), 0.02, 'trim'))
    for (x, y) in lamps:
        B.add(tube([(x, y, zt + 0.95), (x, y, zt + 3.9)], 0.07, 'metald', 6, caps=True, sm=1))
        B.add(cbox2((x - 0.13, y - 0.13, zt + 0.95), (x + 0.13, y + 0.13, zt + 1.4), 0.03, 'metald'))
        gl, _ = lathe([(0.0, 0.0), (0.16, 0.04), (0.22, 0.22), (0.16, 0.42), (0.0, 0.46)], 8, 'lamp')
        xform(gl, T(x, y, zt + 3.9)); B.add(gl)
        B.lamps.append({'name': 'Lamp.%d' % len(B.lamps), 'center': [round(x, 3), round(y, 3), round(zt + 4.12, 3)]})


def pier_span(B):
    """One 12 m span of a seaside pier, its near end at the origin and running away from the street
    (+Y): a timber deck 4.8 m over the water on two concrete pile bents, white rails, a lamp."""
    W, H, D = B.W, B.H, B.D
    pier_deck(B, -W / 2, W / 2, 0.0, D, H, lamps=[(W / 2 - 0.12, 0.5), (-W / 2 + 0.12, D / 2 + 0.5)], piles_y=(2.0, 8.0))
    B.add(cbox2((-W / 2 + 1.0, D * 0.3, H), (-W / 2 + 2.6, D * 0.3 + 0.5, H + 0.48), 0.04, 'woodc'))     # a bench
    B.add(cbox2((-W / 2 + 1.0, D * 0.3 + 0.4, H + 0.48), (-W / 2 + 2.6, D * 0.3 + 0.5, H + 0.9), 0.03, 'woodc'))
    B.attach.append(('Next', (0.0, D, H)))
    return H + 4.4


def pier_end(B):
    """The pier's end: a wider platform with an octagonal roundhouse (white walls, round windows, a
    tiled roof and a lantern on top), rails all round, lamps at the corners."""
    W, H, D = B.W, B.H, B.D
    pier_deck(B, -W / 2, W / 2, 0.0, D, H, rail=False, piles_y=(2.0, 7.0, 12.0),
              pile_xs=[-W / 2 + 0.4, -2.2, 2.2, W / 2 - 0.4],
              lamps=[(-W / 2 + 0.15, 1.0), (W / 2 - 0.15, 1.0), (-W / 2 + 0.15, D - 0.2), (W / 2 - 0.15, D - 0.2)])
    for x0, x1, y0, y1 in ((-W / 2, -W / 2 + 0.16, 0.6, D), (W / 2 - 0.16, W / 2, 0.6, D), (-W / 2, W / 2, D - 0.16, D)):
        B.add(cbox2((x0, y0, H + 0.95), (x1, y1, H + 1.08), 0.02, 'trim'))
        n = int(max(x1 - x0, y1 - y0) / 2.0) + 1
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
            B.add(cbox2((x - 0.08, y - 0.08, H), (x + 0.08, y + 0.08, H + 1.0), 0.02, 'trim'))
    # the roundhouse: eight white walls, a door to the street, round windows, a tiled roof
    cx, cy, r, h = 0.0, D * 0.58, 3.0, 3.3
    pts = [(cx + r * math.cos(math.pi / 8 + i * math.pi / 4), cy + r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
    for i in range(8):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % 8]
        U = Vector((bx - ax, by - ay, 0)); L_ = U.length; U.normalize()
        wf = WF((ax, ay, H), U, 'front' if i in (4, 5) else 'right')
        mid = (ax + bx) / 2, (ay + by) / 2
        facing_street = mid[1] < cy - r * 0.6
        ops = [(L_ / 2 - 0.55, L_ / 2 + 0.55, 0.0, 2.3)] if facing_street and abs(mid[0]) < 0.6 else [(L_ / 2 - 0.45, L_ / 2 + 0.45, 1.1, 2.0)]
        wall(B, wf, 0.0, L_, h, ops, 0.0)
        o = ops[0]
        if o[2] == 0.0: door(B, wf, *o, mat='accent', glass=0.5, panels=((1, 1),), name='Door')
        else: window(B, wf, *o, cols=1, frame='frame', glass='glass1', head=None, seed=670 + i, cheap=True, register=False)
    B.add(cbox2((-r - 0.2, cy - r - 0.2, H + h - 0.05), (r + 0.2, cy + r + 0.2, H + h + 0.1), 0.05, 'trim'))
    mb = MB()
    apex = (cx, cy, H + h + 2.0)
    R2 = r + 0.55
    rp = [(cx + R2 * math.cos(math.pi / 8 + i * math.pi / 4), cy + R2 * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
    for i in range(8):
        (ax, ay), (bx, by) = rp[i], rp[(i + 1) % 8]
        mb.face([(ax, ay, H + h + 0.1), (bx, by, H + h + 0.1), apex], 'roof', None, 1.0)
        mb.face([(ax, ay, H + h - 0.05), (bx, by, H + h - 0.05), (bx, by, H + h + 0.1), (ax, ay, H + h + 0.1)], 'roofw', None, 0.6)
    B.add(mb.bm())
    B.add(tube([(cx, cy, H + h + 1.9), (cx, cy, H + h + 2.7)], 0.06, 'metald', 6, caps=True, sm=1))
    gl, _ = lathe([(0.0, 0.0), (0.2, 0.05), (0.26, 0.28), (0.18, 0.5), (0.0, 0.55)], 8, 'lamp')
    xform(gl, T(cx, cy, H + h + 2.6)); B.add(gl)
    for x in (-W / 2 + 2.2, W / 2 - 2.2):
        B.add(cbox2((x - 0.8, 1.6, H), (x + 0.8, 2.1, H + 0.48), 0.04, 'woodc'))
    return H + h + 3.2


def pal_cal(pal):
    """The California rows of the kit's SPECS (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps).
    Base colours are the muted, sun-softened tones of real stucco and clay (the street repaints parts 1 to 3)."""
    terracotta = (0.72, 0.40, 0.28)
    st = {'wall': 'stucco'}
    return [
        ('VillaStucco', 12.0, 6.0, 9.0, 2.0, villa_stucco,
         pal((0.87, 0.81, 0.70), (0.36, 0.27, 0.20), terracotta, frame=(0.95, 0.95, 0.93), conc=(0.74, 0.72, 0.68), pipe=(0.93, 0.92, 0.9)), 9.2, st, {}),
        ('VillaRanch', 12.0, 3.1, 9.0, 1.4, villa_ranch,
         pal((0.84, 0.78, 0.68), (0.33, 0.38, 0.40), terracotta, frame=(0.95, 0.95, 0.93), pipe=(0.93, 0.92, 0.9)), 5.2, st, {}),
        ('CraftsmanPorch', 8.0, 5.8, 8.0, 2.4, craftsman_porch,
         pal((0.92, 0.92, 0.9), (0.28, 0.35, 0.42), (0.32, 0.33, 0.36), trim=(0.95, 0.95, 0.93), pipe=(0.93, 0.92, 0.9)), 9.0, {}, {}),
        ('BeachCondo', 9.0, 9.0, 10.0, 0.0, beach_condo,
         pal((0.92, 0.92, 0.9), (0.36, 0.5, 0.58), (0.56, 0.55, 0.54)), 12.0, st, {}),
        ('ShopBeach', 8.0, 4.6, 9.0, 0.0, shop_beach,
         pal((0.9, 0.85, 0.75), (0.2, 0.5, 0.56), (0.56, 0.55, 0.54)), 6.0, st, {}),
        ('ShopMission', 9.0, 6.4, 9.0, 0.0, shop_mission,
         pal((0.88, 0.82, 0.72), (0.30, 0.22, 0.17), terracotta), 8.6, st, {}),
        ('PierSpan', 6.0, 4.8, 12.0, 0.0, pier_span,
         pal((0.95, 0.95, 0.93), (0.30, 0.48, 0.62), (0.56, 0.55, 0.54), conc=(0.80, 0.78, 0.74)), 9.6, {}, {}),
        ('PierEnd', 13.0, 4.8, 14.0, 0.0, pier_end,
         pal((0.96, 0.96, 0.94), (0.24, 0.46, 0.62), (0.30, 0.50, 0.66), conc=(0.80, 0.78, 0.74)), 11.0, {}, {}),
    ]
