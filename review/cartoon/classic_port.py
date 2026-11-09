"""The CLASSIC CARTOON filter: the look of a 1950s theatrical cartoon (the Road Runner samples the review asked for),
written the way a PostFX pass would do it, per pixel, from the graded picture, the camera's depth and normals and the
mask in alpha (0 the people and the ball, 0.5 foliage, 1 the street). Two treatments, as an animation cel over a
painted background:

  the people and the ball (the cels)
    flat colour in two or three tones (an edge-keeping smoothing, then the brightness snapped to steps), saturated,
    and a bold, warm-black ink outline all round; no inner lines, so their painted eyes and mouths stay as drawn.
  everything else (the painted background)
    no black outlines: a painterly smoothing (bigger brush), soft airbrushed tone, warm, saturated Technicolor colour
    with rich warm shadows (never grey), brush streaks along the surfaces (across the ground, down the walls), and
    the forms separated by darker strokes of their own colour; foliage painted the same way.
  the sky
    flat turquoise, pale toward the horizon; the clouds stay white with soft shading.
  crisp detail
    the smoothing takes away only weak texture (stains, noise); anything with real contrast (a window frame, a
    letter, a stripe, an edge) comes back exactly as drawn, the strokes are 1 px, and a light sharpen finishes it.
  the print
    a faint film grain and a soft vignette.
  CALM is the calmer setting: the same, with gentler colour.

  python3 -I classic_port.py <render dir> <scene> <out dir>"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cartoon_port as cp
import shader_port as sp

LUM = cp.LUM
FAR = cp.FAR

CLASSIC = dict(
    # crisp detail: weak texture (stains, noise) is smoothed away; anything with real contrast (frames, lettering,
    # stripes, edges) comes back exactly as drawn; then a light sharpen
    coreFrom=0.035, coreTo=0.09, sharpen=0.55, finish=0.35,
    # the cels
    # (the cels keep only strong detail: eyes, brows, mouths, seams; the painted shading's patches are smoothed away)
    celFlatten=1.5, celCoreFrom=0.08, celCoreTo=0.16, celBands=3.0, celBandSoft=0.22, celBandMix=0.6, celSat=1.3,
    celLine=4.0, celLineFar=1.6, inkWarm=np.array([0.11, 0.06, 0.045]),
    # the painted background
    bgFlatten=2.5, bgSat=1.35, bgVibrance=1.8, bgBands=4.0, bgBandSoft=0.32, bgBandMix=0.6,
    warm=np.array([1.1, 0.97, 0.8]),                  # warm colours pushed toward orange (blues and greens stay)
    shadowWarm=np.array([1.05, 0.86, 0.72]),          # dark tones pushed to rich warm browns and reds
    shadowReach=0.45,
    strokeEdge=0.16, strokeDark=0.6, strokeWidth=1.0, strokeStrength=0.75,   # darker strokes of the region's own colour
    formEdge=0.05, formDark=0.62, formStrength=0.8,    # where a nearer form overlaps a farther one (from the depth)
    brush=0.025, brushLength=26.0,                    # brush streaks along the surfaces (faint: they blur detail)
    rescueFrom=0.24,
    # the sky
    skyTop=np.array([62, 190, 222]) / 255.0, skyLow=np.array([168, 228, 236]) / 255.0, cloudShade=np.array([0.86, 0.9, 0.95]),
    # the print
    grain=0.012, vignette=0.2,
)

# The calmer setting: the same cels and painted scenery, with gentler colour (less saturation, less orange, softer
# warm shadows, a paler sky) and a lighter vignette.
CALM = dict(CLASSIC, celSat=1.2, bgSat=1.22, bgVibrance=1.15, warm=np.array([1.07, 0.98, 0.86]),
            shadowWarm=np.array([1.03, 0.9, 0.8]), skyTop=np.array([78, 186, 222]) / 255.0,
            skyLow=np.array([176, 228, 237]) / 255.0, vignette=0.15)


def noise_streaks(h, w, along, length, seed=3):
    """Brush streaks: random value noise stretched `length` px along one direction (0 across, 1 down)."""
    rng = np.random.default_rng(seed)
    if along == 0:
        g = rng.random((h // 2 + 2, int(w / length) + 3))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((int(w / length + 3) * int(length), (h // 2 + 2) * 2), Image.BICUBIC)
    else:
        g = rng.random((int(h / length) + 3, w // 2 + 2))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize(((w // 2 + 2) * 2, int(h / length + 3) * int(length)), Image.BICUBIC)
    return np.asarray(im).astype(np.float64)[:h, :w] / 255.0 - 0.5


def warm_mask(c):
    """Reds, oranges, yellows and beiges (red leads both green and blue): the colours a desert palette warms."""
    return sp.smoothstep(-0.02, 0.08, c[..., 0:1] - np.maximum(c[..., 2:3], c[..., 1:2] * 0.92))


def vibrance(c, v):
    """Quiet colours lifted far more than strong ones (a cartoon background has no greys): sand goes golden, beige
    goes ochre; true greys and whites stay as they are."""
    l = (c * LUM).sum(-1)[..., None]
    hi, lo = c.max(-1, keepdims=True), c.min(-1, keepdims=True)
    sat = (hi - lo) / np.maximum(hi, 1e-3)
    green = sp.smoothstep(0.0, 0.08, c[..., 1:2] - np.maximum(c[..., 0:1], c[..., 2:3]))
    f = 1 + v * (1 - sat) ** 2 * sp.smoothstep(0.03, 0.12, sat) * (1 - 0.7 * green)
    return np.clip(l + (c - l) * f, 0, 1)


def core(c, flat, lo, hi):
    """Coring: of what the smoothing took away, the weak part (texture, stains, noise) stays away and the strong part
    (a frame, a letter, a stripe, an edge) comes back exactly as drawn."""
    d = c - flat
    keep = sp.smoothstep(lo, hi, np.abs(d).max(-1, keepdims=True))
    return flat + d * keep


def sharpen(c, amount, r=1.0):
    """A light unsharp mask (four taps): edges crisp, flat areas untouched."""
    m = (cp.shift(c, 0, r) + cp.shift(c, 0, -r) + cp.shift(c, r, 0) + cp.shift(c, -r, 0)) / 4.0
    return np.clip(c + (c - m) * amount, 0, 1)


def shift_lin(a, dy, dx):
    """Sample at a fractional offset with bilinear filtering (as a texture read does): a hard mask read half a pixel
    off comes back soft at its edge, which anti-aliases the ink for free."""
    y0, x0 = np.floor(dy), np.floor(dx)
    fy, fx = dy - y0, dx - x0
    a00, a01 = cp.shift(a, y0, x0), cp.shift(a, y0, x0 + 1)
    a10, a11 = cp.shift(a, y0 + 1, x0), cp.shift(a, y0 + 1, x0 + 1)
    return (a00 * (1 - fx) + a01 * fx) * (1 - fy) + (a10 * (1 - fx) + a11 * fx) * fy


def hsv_sat(c, s):
    l = (c * LUM).sum(-1)[..., None]
    return np.clip(l + (c - l) * s, 0, 1)


def classic_pass(colour, alpha, depth01, normal, far=FAR, k=CLASSIC):
    h, w, _ = colour.shape
    scale = h / 1080.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)
    fig = (alpha < 0.25)[..., None].astype(np.float64)
    sky = (depth01 > 0.999)[..., None].astype(np.float64)
    bg = (1 - fig) * (1 - sky)
    graded = np.clip(sp.grade_colour(colour, uv), 0, 1)
    leaf = (1 - sp.smoothstep(0.15, 0.3, np.abs(alpha - 0.5)))
    # the scenery sharpened; the cels (faces) and the foliage (leaf clumps would speckle) are not
    c0 = graded + (sharpen(graded, k['sharpen'], max(1.0, scale)) - graded) * (1 - leaf[..., None])
    dist = depth01 * far

    # ---- the cels: flat colour in a few tones
    kc = dict(cp.CARTOON, rescueFrom=k['rescueFrom'], bands=k['celBands'], bandSoft=k['celBandSoft'], bandMix=k['celBandMix'], bandTop=0.86)
    cel = core(graded, cp.kuwahara(graded, k['celFlatten'] * scale, 6.0), k['celCoreFrom'], k['celCoreTo'])
    cel = hsv_sat(cel, k['celSat'])
    cel = cp.cel(cel, kc, 1.0)

    # ---- the painted background
    kb = dict(cp.CARTOON, rescueFrom=k['rescueFrom'], bands=k['bgBands'], bandSoft=k['bgBandSoft'], bandMix=k['bgBandMix'], bandTop=0.9)
    # (foliage keeps only its strong detail, as the cels do: a crown reads as painted clumps, not speckle)
    pb = core(c0, cp.kuwahara(c0, k['bgFlatten'] * scale, 4.0), k['coreFrom'] + (k['celCoreFrom'] - k['coreFrom']) * leaf[..., None],
              k['coreTo'] + (k['celCoreTo'] - k['coreTo']) * leaf[..., None])
    warmish = warm_mask(pb)
    pb = np.clip(pb * (1 + (k['warm'] - 1) * warmish), 0, 1)
    pb = vibrance(pb, k['bgVibrance'])
    pb = hsv_sat(pb, k['bgSat'])
    l = (pb * LUM).sum(-1)[..., None]
    dark = 1 - sp.smoothstep(k['shadowReach'] - 0.2, k['shadowReach'], l)
    pb = np.clip(pb * (1 + (k['shadowWarm'] - 1) * dark), 0, 1)
    pb = hsv_sat(pb, 1 + 0.25 * dark)                       # shadows richer, not greyer
    pb = cp.cel(pb, kb, 1.0)
    # brush streaks: across the ground (normals facing up), down the walls
    up = sp.smoothstep(0.45, 0.75, normal[..., 1])[..., None]
    across = noise_streaks(h, w, 0, k['brushLength'] * scale, 5)[..., None]
    down = noise_streaks(h, w, 1, k['brushLength'] * scale, 9)[..., None]
    streak = across * up + down * (1 - up) * 0.45
    fadeb = 1 - sp.smoothstep(25.0, 90.0, dist)[..., None]
    pb = np.clip(pb * (1 + streak * k['brush'] * 2 * fadeb), 0, 1)   # (the streaks: a tiling texture in the shader)
    # darker strokes of the region's own colour where colours meet, and where a nearer form overlaps a farther one
    sw = max(1.0, k['strokeWidth'] * scale)
    stroke = cp.colour_lines(pb, sw, k['strokeEdge'])
    ds = [cp.shift(depth01, 0, sw), cp.shift(depth01, 0, -sw), cp.shift(depth01, sw, 0), cp.shift(depth01, -sw, 0)]
    near = np.minimum.reduce([depth01] + ds)
    jump = np.maximum.reduce([np.abs(x - depth01) for x in ds]) / np.maximum(near, 1e-4)
    form = sp.smoothstep(k['formEdge'] * (1 + 3 * leaf), k['formEdge'] * (1 + 3 * leaf) * 1.6, jump)
    fade = 1 - sp.smoothstep(40.0, 120.0, dist)
    pb = pb + (pb * k['strokeDark'] - pb) * (stroke * k['strokeStrength'] * (1 - leaf * 0.7) * fade)[..., None]
    pb = pb + (pb * k['formDark'] - pb) * (form * k['formStrength'] * fade)[..., None]

    # ---- the sky: flat turquoise; white clouds keep soft shading
    t = (np.linspace(0, 1, h) ** 1.4)[:, None, None]
    sk = k['skyTop'] * (1 - t) + k['skyLow'] * t

    out = cel * fig + pb * bg + sk * sky
    # a light final sharpen on the scenery (the sky and the cels stay smooth)
    out = out + (sharpen(out, k['finish'], max(1.0, scale)) - out) * bg * (1 - leaf[..., None])
    # clouds (geometry far away and bright) read as white with soft blue-grey shade
    lb = (c0 * LUM).sum(-1)[..., None]
    cloud = (1 - fig) * (1 - sky) * sp.smoothstep(100.0, 135.0, dist)[..., None] * sp.smoothstep(0.62, 0.8, lb)
    cl = np.clip(1 - (1 - lb) * 0.9, 0, 1) * np.array([1.0, 1.0, 1.0]) * k['cloudShade'] ** (1 - sp.smoothstep(0.75, 0.95, lb))
    out = out * (1 - cloud) + cl * cloud

    # ---- the cels' ink: a bold warm-black outline all round each figure (from the depth and the mask)
    wpx = (k['celLine'] + (k['celLineFar'] - k['celLine']) * sp.smoothstep(4.0, 60.0, dist)) * scale
    ink = np.zeros((h, w))
    figm = fig[..., 0]
    for ring in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5):
        r = ring * scale
        use = np.clip(1 - np.abs(wpx - r) / (0.5 * scale), 0, 1)
        if use.max() <= 0:
            continue
        # the mask read at half-pixel offsets (bilinear), so the line's edge is anti-aliased, not stair-stepped
        rh = r + 0.5
        offs = [(0, rh), (0, -rh), (rh, 0), (-rh, 0), (0.7 * rh, 0.7 * rh), (-0.7 * rh, 0.7 * rh), (0.7 * rh, -0.7 * rh), (-0.7 * rh, -0.7 * rh)]
        # a figure pixel next to anything that is not the figure, or nearer than it
        other = np.maximum.reduce([1 - shift_lin(figm, dy, dx) for dy, dx in offs])
        ds = [cp.shift(depth01, dy, dx) for dy, dx in offs]
        jumpf = np.maximum.reduce([np.abs(x - depth01) for x in ds]) / np.maximum(np.minimum.reduce([depth01] + ds), 1e-4)
        edge = np.maximum(other, sp.smoothstep(0.04, 0.09, jumpf)) * figm
        # and the background pixel just outside a figure (the line straddles the silhouette)
        outside = np.maximum.reduce([shift_lin(figm, dy, dx) for dy, dx in offs[:4]]) * (1 - figm) * (ring <= 2.5)
        ink = np.maximum(ink, np.maximum(edge, outside) * use)
    out = out + (k['inkWarm'] - out) * ink[..., None]

    # ---- the print
    p = uv - 0.5
    out = out * (1 - k['vignette'] * sp.smoothstep(0.3, 0.9, sp.dot3(p, p)[..., None] * 2.2))
    rng = np.random.default_rng(11)
    out = out + (rng.random((h, w, 1)) - 0.5) * k['grain']
    return np.clip(out, 0, 1)


def classic_2d(rgba, painted=False, k=CLASSIC, flatten=None, outline_px=None):
    """The menus' pictures: a kid, a bag, a sticker as a cel (flat tones, warm-black ink round the shape and where the
    colours meet); a picture of the town (the map) painted, like the background."""
    h, w, _ = rgba.shape
    c, a = rgba[..., :3], rgba[..., 3]
    s = max(h, w) / 1024.0
    c = sharpen(c, k['sharpen'] * 0.8)
    if painted:
        kb = dict(cp.CARTOON, rescueFrom=k['rescueFrom'], bands=k['bgBands'], bandSoft=k['bgBandSoft'], bandMix=k['bgBandMix'], bandTop=0.9)
        r = flatten if flatten is not None else 2.0 * s
        pb = core(c, cp.kuwahara(c, r, 4.0), k['coreFrom'], k['coreTo'])
        warmish = warm_mask(pb)
        pb = hsv_sat(vibrance(np.clip(pb * (1 + (k['warm'] - 1) * warmish), 0, 1), k['bgVibrance'] * 0.5), k['bgSat'])
        l = (pb * LUM).sum(-1)[..., None]
        dark = 1 - sp.smoothstep(k['shadowReach'] - 0.2, k['shadowReach'], l)
        pb = np.clip(pb * (1 + (k['shadowWarm'] - 1) * dark), 0, 1)
        pb = cp.cel(pb, kb, 1.0)
        st = cp.colour_lines(pb, 1.0, k['strokeEdge'])
        pb = pb + (pb * k['strokeDark'] - pb) * (st * k['strokeStrength'])[..., None]
        return np.dstack([pb, a])
    kc = dict(cp.CARTOON, rescueFrom=k['rescueFrom'], bands=k['celBands'], bandSoft=k['celBandSoft'], bandMix=k['celBandMix'], bandTop=0.86)
    r = flatten if flatten is not None else 1.6 * s
    cel = core(c, cp.kuwahara(c, r, 6.0), k['coreFrom'], k['coreTo'])
    cel = hsv_sat(cel, k['celSat'])
    cel = cp.cel(cel, kc, 1.0)
    lines = cp.colour_lines(cel, 1.0, 0.3)
    out = cel + (k['inkWarm'] - cel) * (lines * 0.85)[..., None]
    if outline_px:
        o = outline_px
        offs = [(0, o), (0, -o), (o, 0), (-o, 0), (0.7 * o, 0.7 * o), (-0.7 * o, 0.7 * o), (0.7 * o, -0.7 * o), (-0.7 * o, -0.7 * o)]
        near = np.maximum.reduce([cp.shift(a, dy, dx) for dy, dx in offs])
        inner = np.minimum.reduce([cp.shift(a, dy, dx) for dy, dx in offs[:4]])
        edge = np.clip((np.clip(near - a, 0, 1) + np.clip(a - inner, 0, 1)) * 1.5, 0, 1)
        out = out * (1 - edge[..., None]) + k['inkWarm'] * edge[..., None]
        a = np.maximum(a, np.clip(near - a, 0, 1))
    return np.dstack([np.clip(out, 0, 1), a])


if __name__ == '__main__':
    src, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    colour, alpha, depth01, nrm = cp.load_scene(src, scene)
    cp.to_img(classic_pass(colour, alpha, depth01, nrm)).save(os.path.join(out, '%s_classic.png' % scene))
    print('done', scene)
