"""The CARTOON filter, written the way a PostFX pass would do it: per pixel, from the graded picture, the camera's
depth and normals and the figure mask in alpha (ToonCharacter's _ComicWorld: 0 the people and the ball). It is run
here over render_scenes.py's renders of the game's own models, so the look can be judged before it is built.

  flatten  - an edge-keeping smoothing (a soft four-sector Kuwahara, 3 px at 1080 lines): paint texture, grain and
             fine noise melt into flat colour while every real edge stays sharp; thin, strong detail it would rub out
             (shop lettering, sign symbols) is kept. The people get very little of it, so their painted eyes, brows
             and mouths stay as drawn.
  cel      - the brightness snapped to a few flat tones with soft-stepped edges (a cartoon's base, shade and deep
             shade), the colour itself kept; highlights left alone so whites stay white.
  colour   - brighter, candy colour (saturation up, a little contrast) and cool, blue-violet shade.
  sky      - the sky's gradient laid in broad flat bands, as a painted cartoon background.
  ink      - bold, even outlines: the silhouettes from the depth (thickest near the camera, thinning with distance),
             creases from the normals (the street only), and thin lines where the flat colours meet (the street only:
             window frames, signs and stripes painted in the texture get a line too); the people and the ball get the
             boldest silhouette and no inner lines, so faces stay clean; foliage (0.5 in the mask) is inked round
             its crown only, not round every leaf clump.
  No dots, no paper, no grain, no colour slip: clean, flat and bright (that is the comic halftone's and the sketch's job).

  python3 -I cartoon_port.py <render dir> <scene> <out dir>     (writes <scene>_original.png and <scene>_cartoon.png)

The 2D version (cartoon_2d) is the same flatten, cel, colour and ink with no depth: for pictures drawn in the UI (the
town map, the stickers, the player cards, the bags, the logo), outlining where the colours meet and where alpha ends."""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'filter'))
import shader_port as sp

FAR = 300.0
LUM = np.array([0.299, 0.587, 0.114])

# PostFX.cs settings for the filter (sizes in pixels at 1080 lines; they scale with the screen)
CARTOON = dict(
    flatten=3.0,            # Kuwahara radius
    flattenSharp=6.0,       # how hard the calmest sector wins (soft Kuwahara's q)
    figureFlatten=0.25,     # how much of the smoothing the people and the ball take
    rescueFrom=0.22,        # thin detail whose brightness the smoothing moved by more than this comes back
    bands=3.0,              # brightness steps
    bandSoft=0.18,          # the steps' edges, as a fraction of a step (0 hard, 0.5 smooth)
    bandMix=0.85,           # 0 none, 1 full steps
    bandTop=0.82,           # brightness above this is left smooth (whites stay white)
    figureBands=0.45,       # how much of the steps the people take
    saturation=1.32,
    contrast=1.04,
    shadeTint=np.array([0.86, 0.86, 1.04]),   # multiplied into the shade (below shadeReach)
    shadeReach=0.42,
    skyBands=6.0,
    lineNear=3.6,           # the silhouette's width close to the camera
    lineFar=1.1,            # ...and by lineFarAt metres
    lineFarAt=60.0,
    figureLine=1.25,        # the people's silhouette, times the street's at the same distance
    depthEdge=0.06,
    leafEdge=4.0,           # foliage needs this many times the depth jump (a crown's outline, not every clump)
    creaseWidth=1.4,
    normalEdge=0.32,
    colourLine=1.0,         # width of the lines between flat colours
    colourEdge=0.2,         # a step in brightness or colour of this much draws one
    colourLineDark=0.38,    # those lines are the colour darkened to this
    inkFar=110.0,           # the lines have faded by this distance (m)
    ink=np.array([0.07, 0.055, 0.12]),
)


def box_mean(a, r):
    """Mean over a (2r+1)^2 window (clamped), by integral image: what a sector average does in the shader."""
    if r <= 0:
        return a.copy()
    pad = [(r + 1, r), (r + 1, r)] + [(0, 0)] * (a.ndim - 2)
    p = np.pad(a, pad, mode='edge')
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s / (k * k)


def shift(a, dy, dx):
    h, w = a.shape[:2]
    ys = np.clip(np.arange(h) + int(round(dy)), 0, h - 1)
    xs = np.clip(np.arange(w) + int(round(dx)), 0, w - 1)
    return a[ys][:, xs]


def kuwahara(c, r, q):
    """Soft four-sector Kuwahara: each sector is a (r+1)^2 square touching the pixel; sectors blend by
    1 / (1 + variance)^q, so the calmest side wins and an edge is never smeared across."""
    if r < 0.5:
        return c
    ri = int(round(r))
    half = ri / 2.0
    l = (c * LUM).sum(-1)
    # a (ri+1)^2 square's mean centred on the pixel, shifted half a square into each quadrant
    m_c = box_mean(c, ri // 2) if ri % 2 == 0 else box_mean(c, (ri + 1) // 2)
    m_l = box_mean(l, ri // 2) if ri % 2 == 0 else box_mean(l, (ri + 1) // 2)
    m_l2 = box_mean(l * l, ri // 2) if ri % 2 == 0 else box_mean(l * l, (ri + 1) // 2)
    acc = np.zeros_like(c); wsum = np.zeros(c.shape[:2])
    for sy, sx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        mc = shift(m_c, sy * half, sx * half)
        var = np.maximum(shift(m_l2, sy * half, sx * half) - shift(m_l, sy * half, sx * half) ** 2, 0)
        w = 1.0 / (1.0 + var * 400.0) ** q
        acc += mc * w[..., None]; wsum += w
    return acc / wsum[..., None]


def rescue(c, flat, k):
    """Thin, strong detail the smoothing would rub out (a shop's lettering, a sign's symbol, a stripe): where the
    smoothed colour has moved far from the picture's, the picture's own colour comes back."""
    moved = np.abs(((c - flat) * LUM).sum(-1))
    keep = sp.smoothstep(k['rescueFrom'], k['rescueFrom'] + 0.16, moved)[..., None]
    return flat + (c - flat) * keep


def bands(l, n, soft):
    """Brightness snapped to n steps with soft edges (soft: the ramp's width as a fraction of a step)."""
    x = l * n
    f = np.floor(x)
    t = x - f
    s = sp.smoothstep(0.5 - soft, 0.5 + soft, t)
    return (f + s) / n


def cel(c, k, figure_k):
    l = (c * LUM).sum(-1)[..., None]
    lq = bands(l, k['bands'], k['bandSoft'])
    mix = k['bandMix'] * (1 - sp.smoothstep(k['bandTop'] - 0.06, k['bandTop'] + 0.04, l)) * figure_k
    lt = l + (lq - l) * mix
    return np.clip(c * (lt / np.maximum(l, 1e-3)), 0, 1)


def candy(c, k):
    l = (c * LUM).sum(-1)[..., None]
    c = np.clip(l + (c - l) * k['saturation'], 0, 1)
    c = np.clip((c - 0.5) * k['contrast'] + 0.5, 0, 1)
    l = (c * LUM).sum(-1)[..., None]
    shade = 1 - sp.smoothstep(k['shadeReach'] - 0.12, k['shadeReach'], l)
    return np.clip(c * (1 + (k['shadeTint'] - 1) * shade), 0, 1)


def colour_lines(c, width, edge):
    """Where flat colours meet: the largest step in brightness or colour across the pixel's neighbours."""
    l = (c * LUM).sum(-1)
    best = np.zeros(c.shape[:2])
    for dy, dx in ((0, width), (width, 0), (width, width), (width, -width)):
        a, b = shift(c, -dy, -dx), shift(c, dy, dx)
        la, lb = (a * LUM).sum(-1), (b * LUM).sum(-1)
        step = np.maximum(np.abs(la - lb), 0.7 * np.sqrt(((a - b) ** 2).sum(-1)))
        best = np.maximum(best, step)
    return sp.smoothstep(edge, edge * 1.8, best)


def sky_bands(c, n):
    """The sky in broad flat bands (its gradient kept as steps)."""
    l = (c * LUM).sum(-1)[..., None]
    lq = bands(l, n * 2.2, 0.12)
    return np.clip(c * (lq / np.maximum(l, 1e-3)), 0, 1)


def cartoon_pass(colour, alpha, depth01, normal, far=FAR, k=CARTOON):
    h, w, _ = colour.shape
    scale = h / 1080.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)
    leaf = (1 - sp.smoothstep(0.15, 0.3, np.abs(alpha - 0.5)))[..., None]   # 0.5: foliage
    world = np.maximum(np.clip(alpha, 0, 1)[..., None], leaf)                # foliage is drawn like the street...
    sky = (depth01 > 0.999)[..., None]
    c = np.clip(sp.grade_colour(colour, uv), 0, 1)

    # flatten (the people take only a little of it)
    flat = rescue(c, kuwahara(c, k['flatten'] * scale, k['flattenSharp']), k)
    fk = k['figureFlatten'] + (1 - k['figureFlatten']) * world
    c = c + (flat - c) * fk
    # colour, then the cel steps (the sky in its own broad bands)
    c = candy(c, k)
    banded = cel(c, k, k['figureBands'] + (1 - k['figureBands']) * world)
    c = np.where(sky, sky_bands(c, k['skyBands']), banded)

    # ink: silhouettes from depth, thick near and thin far; the people's a little bolder
    dist = depth01 * far
    wpx = (k['lineNear'] + (k['lineFar'] - k['lineNear']) * sp.smoothstep(4.0, k['lineFarAt'], dist)) * scale
    wpx = wpx * (1 + (k['figureLine'] - 1) * (1 - world[..., 0]))
    line = np.zeros((h, w))
    # the shader takes the width per pixel; here a few fixed rings, each used where it is the pixel's width
    for ring in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        r = ring * scale
        use = np.clip(1 - np.abs(wpx - r) / (0.5 * scale), 0, 1)
        if use.max() <= 0:
            continue
        ds = [shift(depth01, 0, r), shift(depth01, 0, -r), shift(depth01, r, 0), shift(depth01, -r, 0),
              shift(depth01, 0.7 * r, 0.7 * r), shift(depth01, -0.7 * r, 0.7 * r), shift(depth01, 0.7 * r, -0.7 * r), shift(depth01, -0.7 * r, -0.7 * r)]
        near = np.minimum.reduce([depth01] + ds)
        jump = np.maximum.reduce([np.abs(x - depth01) for x in ds]) / np.maximum(near, 1e-4)
        edge = k['depthEdge'] * (1 + (k['leafEdge'] - 1) * leaf[..., 0])      # ...but inked only round the crown
        line = np.maximum(line, sp.smoothstep(edge, edge * 2.2, jump) * use)
    # creases (the street only)
    cw = k['creaseWidth'] * scale
    ns = [shift(normal, 0, cw), shift(normal, 0, -cw), shift(normal, cw, 0), shift(normal, -cw, 0)]
    turn = 1 - np.minimum.reduce([sp.dot3(normal, x) for x in ns])
    crease = sp.smoothstep(k['normalEdge'], k['normalEdge'] * 1.8, turn) * world[..., 0] * (1 - sky[..., 0]) * (1 - leaf[..., 0])
    fade = 1 - sp.smoothstep(k['inkFar'] * 0.5, k['inkFar'], dist)
    ink = np.clip(np.maximum(line, crease * 0.9), 0, 1) * np.maximum(fade, (1 - world[..., 0]))
    # lines where flat colours meet (the street only), the colour itself darkened
    cl = colour_lines(c, max(1.0, k['colourLine'] * scale), k['colourEdge']) * world[..., 0] * (1 - sky[..., 0]) * fade * (1 - leaf[..., 0])
    c = c + (c * k['colourLineDark'] - c) * cl[..., None] * 0.85
    c = c + (k['ink'] - c) * ink[..., None]
    return np.clip(c, 0, 1)


# ------------------------------------------------------------------ the 2D version, for the UI's pictures
def cartoon_2d(rgba, k=CARTOON, flatten=None, line_px=None, outline_px=None):
    """rgba HxWx4 0..1 (sRGB as stored). The same flatten, colour and cel; lines where colours meet; and the shape's
    own outline where alpha ends (a die-cut sticker, a portrait), sized to the picture."""
    h, w, _ = rgba.shape
    c, a = rgba[..., :3], rgba[..., 3]
    s = max(h, w) / 1024.0
    r = flatten if flatten is not None else 2.0 * s
    flat = rescue(c, kuwahara(c, r, k['flattenSharp']), k)
    flat = candy(flat, k)
    flat = cel(flat, k, 1.0)
    lp = line_px if line_px is not None else max(1.0, 1.2 * s)
    cl = colour_lines(flat, lp, k['colourEdge'] * 1.1)
    out = flat + (flat * k['colourLineDark'] - flat) * cl[..., None] * 0.85
    if outline_px:
        o = outline_px
        near = np.maximum.reduce([shift(a, dy, dx) for dy, dx in ((0, o), (0, -o), (o, 0), (-o, 0), (0.7 * o, 0.7 * o), (-0.7 * o, 0.7 * o), (0.7 * o, -0.7 * o), (-0.7 * o, -0.7 * o))])
        edge = np.clip(near - a, 0, 1) + np.clip(a - np.minimum.reduce([shift(a, dy, dx) for dy, dx in ((0, o * 0.5), (0, -o * 0.5), (o * 0.5, 0), (-o * 0.5, 0))]), 0, 1)
        edge = np.clip(edge * 1.5, 0, 1)
        out = out * (1 - edge[..., None]) + k['ink'] * edge[..., None]
        a = np.maximum(a, np.clip(near - a, 0, 1))
    return np.dstack([np.clip(out, 0, 1), a])


# ------------------------------------------------------------------ the scenes
SKY_TOP = np.array([52, 104, 182]) / 255.0       # WorldLook's zenith as it shows on screen
SKY_LOW = np.array([150, 192, 230]) / 255.0


def load_scene(src, scene):
    def rd(kind):
        return np.asarray(Image.open(os.path.join(src, '%s_%s.png' % (scene, kind)))).astype(np.float64) / 255.0
    col = rd('colour')
    h, w, _ = col.shape
    t = (np.linspace(0, 1, h) ** 0.8)[:, None, None]
    sky = SKY_TOP * (1 - t) + SKY_LOW * t
    colour = col[..., :3] * col[..., 3:] + sky * (1 - col[..., 3:])
    nrm = rd('normal')[..., :3] * 2 - 1
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
    data = rd('data')
    depth01 = np.clip(data[..., 0] + data[..., 1] / 255.0, 0, 1)
    return colour, data[..., 2], depth01, nrm


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


if __name__ == '__main__':
    src, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    colour, alpha, depth01, nrm = load_scene(src, scene)
    to_img(sp.plain(colour)).save(os.path.join(out, '%s_original.png' % scene))
    to_img(cartoon_pass(colour, alpha, depth01, nrm)).save(os.path.join(out, '%s_cartoon.png' % scene))
    print('done', scene)
