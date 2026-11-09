"""A step-for-step numpy mirror of the classic cartoon passes as built (Shaders/PostFX.shader passes 8 and 9,
Shaders/DtsCartoon.cginc, the values in Scripts/World/ClassicLook.cs), to check the shader's order of operations
against the look approved on the boards (classic_port.py). Run over render_scenes.py's renders:
    python3 -I shader_mirror.py <render dir> <scene> <out dir>     (writes <scene>_shader.png and <scene>_diff.png)
The renders' mask uses 0 for both figures and cels (the game writes 0.125 for a cel; both are cels here)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cartoon_port as cp
import classic_port as cl
import shader_port as sp

LUM = cp.LUM
K = dict(coreFrom=0.035, coreTo=0.09, sharpen=0.55, finish=0.35, celCoreFrom=0.08, celCoreTo=0.16, celBands=3.0, celBandSoft=0.22,
         celBandMix=0.6, celSat=1.3, celLine=3.4, celLineFar=1.5, celInk=np.array([0.11, 0.06, 0.045]), bgSat=1.35, bgVibrance=1.8,
         bgBands=4.0, bgBandSoft=0.32, bgBandMix=0.6, shadowReach=0.45, warm=np.array([1.1, 0.97, 0.8]),
         shadowWarm=np.array([1.05, 0.86, 0.72]), strokeEdge=0.16, strokeDark=0.6, strokeStrength=0.75, formEdge=0.05, formDark=0.62,
         formStrength=0.8, brush=0.025, brushLength=26.0, skyTop=np.array([62, 190, 222]) / 255.0,
         skyLow=np.array([168, 228, 236]) / 255.0, cloudShade=np.array([0.86, 0.9, 0.95]), grain=0.012, vignette=0.2)


def step_tone(l, n, soft):
    x = l * n; f = np.floor(x)
    return (f + sp.smoothstep(0.5 - soft, 0.5 + soft, x - f)) / n


def tones(c, n, soft, mix, top):
    l = (c * LUM).sum(-1)[..., None]
    m = mix * (1 - sp.smoothstep(top - 0.06, top + 0.04, l))
    t = l + (step_tone(l, n, soft) - l) * m
    return np.clip(c * (t / np.maximum(l, 1e-3)), 0, 1)


def painted(c, vscale=1.0):
    c = np.clip(c * (1 + (K['warm'] - 1) * cl.warm_mask(c)), 0, 1)
    c = cl.vibrance(c, K['bgVibrance'] * vscale)
    c = cl.hsv_sat(c, K['bgSat'])
    l = (c * LUM).sum(-1)[..., None]
    dark = 1 - sp.smoothstep(K['shadowReach'] - 0.2, K['shadowReach'], l)
    c = np.clip(c * (1 + (K['shadowWarm'] - 1) * dark), 0, 1)
    c = cl.hsv_sat(c, 1 + 0.25 * dark)
    return tones(c, K['bgBands'], K['bgBandSoft'], K['bgBandMix'], 0.9)


def celled(c):
    return tones(cl.hsv_sat(c, K['celSat']), K['celBands'], K['celBandSoft'], K['celBandMix'], 0.86)


def sectors(c, t):
    """CARTOON_SECTORS: four 3x3 sectors (t apart) touching each pixel: means, brightness variances, and the 4-neighbour mean."""
    l = (c * LUM).sum(-1)
    taps = {(x, y): (cp.shift(c, y * t, x * t), cp.shift(l, y * t, x * t)) for x in range(-2, 3) for y in range(-2, 3)}
    out = []
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        keys = [(x, y) for x in range(-2, 3) for y in range(-2, 3) if x * sx >= 0 and y * sy >= 0]
        m = sum(taps[k][0] for k in keys) / 9
        s = sum(taps[k][1] for k in keys) / 9
        q = sum(taps[k][1] ** 2 for k in keys) / 9
        out.append((m, np.maximum(q - s * s, 0)))
    cross = (taps[(1, 0)][0] + taps[(-1, 0)][0] + taps[(0, 1)][0] + taps[(0, -1)][0]) / 4
    return out, cross


def blend(sec, q):
    lo = 1 + 400 * np.minimum.reduce([v for _, v in sec])
    ws = [(lo / (1 + 400 * v)) ** q for _, v in sec]
    return sum(m * w[..., None] for (m, _), w in zip(sec, ws)) / sum(ws)[..., None]


def core(c, flat, lo, hi):
    d = c - flat
    return flat + d * sp.smoothstep(lo, hi, np.abs(d).max(-1, keepdims=True))


def step_across(a, b):
    d = a - b
    return np.maximum(np.abs((d * LUM).sum(-1)), 0.7 * np.sqrt((d * d).sum(-1)))


def shader(colour, alpha, depth01, normal, far=cp.FAR):
    h, w, _ = colour.shape
    sc = max(0.75, h / 1080.0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)
    graded = np.clip(sp.grade_colour(colour, uv), 0, 1)          # pass 7
    cel = (alpha <= 0.3).astype(float)[..., None]
    leaf = (1 - sp.smoothstep(0.08, 0.16, np.abs(alpha - 0.5)))[..., None]
    cloud = (1 - sp.smoothstep(0.08, 0.16, np.abs(alpha - 0.75)))[..., None]   # (the renders mark no clouds)
    sky = (depth01 >= 0.999).astype(float)[..., None]

    # pass 8
    sec, cross = sectors(graded, sc)
    flat = blend(sec, 4) + (blend(sec, 6) - blend(sec, 4)) * cel
    c = graded
    c0 = c + (np.clip(c + (c - cross) * K['sharpen'], 0, 1) - c) * (1 - cel) * (1 - leaf)
    strong = np.maximum(cel, leaf)
    p = core(c0, flat, K['coreFrom'] + (K['celCoreFrom'] - K['coreFrom']) * strong, K['coreTo'] + (K['celCoreTo'] - K['coreTo']) * strong)
    o = painted(p) * (1 - cel) + celled(p) * cel
    l = (c * LUM).sum(-1)[..., None]
    white = (1 - (1 - l) * 0.9) * K['cloudShade'] ** (1 - sp.smoothstep(0.75, 0.95, l))
    o = o + (np.clip(white, 0, 1) - o) * cloud
    ty = (yy / h)[..., None] ** 1.4
    o = o + (K['skyTop'] * (1 - ty) + K['skyLow'] * ty - o) * sky
    flatpic = o

    # pass 9
    c = flatpic
    scenery = (1 - cel) * (1 - sky) * (1 - cloud)
    eye = depth01 * far
    fade = (1 - sp.smoothstep(40, 120, eye))[..., None]
    o1 = sc
    cR, cL, cU, cD = cp.shift(c, 0, o1), cp.shift(c, 0, -o1), cp.shift(c, -o1, 0), cp.shift(c, o1, 0)
    cRU, cLD, cRD, cLU = cp.shift(c, -o1, o1), cp.shift(c, o1, -o1), cp.shift(c, o1, o1), cp.shift(c, -o1, -o1)
    c = c + (np.clip(c + (c - (cR + cL + cU + cD) / 4) * K['finish'], 0, 1) - c) * scenery * (1 - leaf)
    up = sp.smoothstep(0.45, 0.75, normal[..., 1])[..., None]
    across = cl.noise_streaks(h, w, 0, K['brushLength'] * sc, 5)[..., None]
    down = cl.noise_streaks(h, w, 1, K['brushLength'] * sc, 9)[..., None]
    streak = across * up + down * (1 - up) * 0.45
    c = np.clip(c * (1 + streak * K['brush'] * 2 * (1 - sp.smoothstep(25, 90, eye))[..., None] * scenery), 0, 1)
    st = np.maximum.reduce([step_across(cR, cL), step_across(cU, cD), step_across(cRU, cLD), step_across(cRD, cLU)])
    stroke = sp.smoothstep(K['strokeEdge'], K['strokeEdge'] * 1.8, st)[..., None]
    c = c + (c * K['strokeDark'] - c) * stroke * K['strokeStrength'] * (1 - leaf * 0.7) * fade * scenery
    ds = [cp.shift(depth01, 0, o1), cp.shift(depth01, 0, -o1), cp.shift(depth01, -o1, 0), cp.shift(depth01, o1, 0)]
    near = np.minimum.reduce([depth01] + ds)
    jump = (np.maximum.reduce([np.abs(x - depth01) for x in ds]) / np.maximum(near, 1e-4))[..., None]
    fe = K['formEdge'] * (1 + 3 * leaf)
    form = sp.smoothstep(fe, fe * 1.6, jump)
    c = c + (c * K['formDark'] - c) * form * K['formStrength'] * fade * scenery
    # the cels' outline: two radii, eight and four directions, the code read bilinear
    R = 4 * sc
    dnear = np.minimum.reduce([depth01] + [cp.shift(depth01, dy, dx) for dy, dx in ((0, R), (0, -R), (R, 0), (-R, 0))])
    width = (K['celLine'] + (K['celLineFar'] - K['celLine']) * sp.smoothstep(4, 60, dnear * far)) * sc + 0.5
    ink = np.zeros((h, w))
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
    wm = float(np.median(width))      # (one width per pass here: the shader takes it per pixel)
    for k in range(12):
        dx, dy = dirs[k % 8]
        r = wm * (1.0 if k < 8 else 0.5)
        a = cl.shift_lin(alpha, -dy * r, dx * r)
        dk = cp.shift(depth01, -dy * r, dx * r)
        nearer = sp.smoothstep(0.03, 0.07, (depth01 - dk) / np.maximum(dk, 1e-4))
        ink = np.maximum(ink, np.clip((0.3 - a) / 0.18, 0, 1) * nearer)
    c = c + (K['celInk'] - c) * ink[..., None]
    v = uv - 0.5
    c = c * (1 - K['vignette'] * sp.smoothstep(0.3, 0.9, sp.dot3(v, v)[..., None] * 2.2))
    c = c + (np.random.default_rng(11).random((h, w, 1)) - 0.5) * K['grain']
    return np.clip(c, 0, 1)


if __name__ == '__main__':
    from PIL import Image
    src, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    colour, alpha, depth01, nrm = cp.load_scene(src, scene)
    a = shader(colour, alpha, depth01, nrm)
    b = cl.classic_pass(colour, alpha, depth01, nrm)
    cp.to_img(a).save(os.path.join(out, '%s_shader.png' % scene))
    diff = np.abs(a - b).max(-1)
    print(scene, 'mean |shader - reference| = %.4f, 99th percentile %.3f' % (diff.mean(), np.percentile(diff, 99)))
    cp.to_img(np.clip(diff * 4, 0, 1)[..., None].repeat(3, -1)).save(os.path.join(out, '%s_diff.png' % scene))
