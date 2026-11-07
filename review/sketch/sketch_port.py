"""Preview of a SKETCH filter, written the way a PostFX pass would do it (per pixel, from the picture, the
camera's depth and normals and the figure mask in alpha, plus a noise texture), run over render_street.py's
renders of the game's own models:

  paper   - warm drawing paper with a fibre grain; the vignette as a paper edge
  wash    - the picture's colour laid on softly (coloured pencil) or barely (graphite), patchy like a wash;
            the figures keep their colour even on the graphite page, so the kid is easy to find
  sky     - left open (a wash, no hatching)
  hatch   - pencil hatching for the tone: one direction below 0.78, crossed below 0.52, a third, denser
            set below 0.3; strokes of finite length with gaps, a wobble, and pencil grain on them
  line    - the outline drawn twice with a wandering offset (a sketcher's doubled, overshooting line) from
            the depth jumps and the creases; figures get no creases (their painted eyes stay clean) and
            lighter hatching

    python3 -I sketch_port.py <render dir> <out dir> [suffix]"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'filter'))
import shader_port as sp

GRAPHITE = np.array([0.17, 0.17, 0.2])
PAPER = np.array([0.965, 0.945, 0.9])
FAR = 300.0


def noise(h, w, cell, seed):
    """Smooth value noise 0..1 (a tiling noise texture sampled at 1/cell in the shader)."""
    rng = np.random.default_rng(seed)
    g = rng.random((h // cell + 3, w // cell + 3))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC)
    return np.asarray(im).astype(np.float64)[:h, :w] / 255


def hashp(a, b):
    return np.modf(np.sin(a * 12.9898 + b * 78.233) * 43758.5453)[0] % 1.0


def sample(a, yy, xx):
    h, w = a.shape[:2]
    return a[np.clip(np.rint(yy).astype(int), 0, h - 1), np.clip(np.rint(xx).astype(int), 0, w - 1)]


def edges(depth, normal, world, yy, xx, inkw, far, depth_edge=0.05, normal_edge=0.3, ink_far=90.0):
    """sp.InkLine at a jittered spot: outlines from depth jumps, creases from normals (street only)."""
    d0, n0 = sample(depth, yy, xx), sample(normal, yy, xx)
    ds = [sample(depth, yy, xx + inkw), sample(depth, yy, xx - inkw), sample(depth, yy - inkw, xx), sample(depth, yy + inkw, xx)]
    ns = [sample(normal, yy, xx + inkw), sample(normal, yy, xx - inkw), sample(normal, yy - inkw, xx), sample(normal, yy + inkw, xx)]
    near = np.minimum.reduce([d0] + ds)
    jump = np.maximum.reduce([np.abs(x - d0) for x in ds]) / np.maximum(near, 1e-4)
    line = sp.smoothstep(depth_edge, depth_edge * 2.5, jump)
    turn = 1 - np.minimum.reduce([(n0 * x).sum(-1) for x in ns])
    crease = sp.smoothstep(normal_edge, normal_edge * 2, turn) * world
    fade = 1 - sp.smoothstep(ink_far * 0.45, ink_far, near * far)
    return np.clip(np.maximum(line, crease), 0, 1) * fade


def hatch(px, py, angle, spacing, tone, threshold, grain, wob, seed):
    """One set of pencil strokes: lines across `angle`, `spacing` px apart, pressed harder the darker the tone."""
    a = np.radians(angle)
    across = (px * np.cos(a) + py * np.sin(a)) / spacing + (wob - 0.5) * 0.5
    along = (-px * np.sin(a) + py * np.cos(a)) / spacing
    lane = np.floor(across + 0.5)
    d = np.abs(across - lane) * spacing                       # px from the stroke's centre
    stroke = np.clip(1 - (d - 0.45) / 0.9, 0, 1)
    # finite strokes: each lane cut into lengths of 4-9 spacings with gaps, offset lane by lane
    seg = (along / (5.5 + 3 * hashp(lane, seed)) + hashp(lane, seed + 7)) % 1.0
    stroke *= (seg > 0.12) * sp.smoothstep(0.12, 0.2, seg) * (1 - sp.smoothstep(0.92, 1.0, seg))
    pressure = sp.smoothstep(threshold, threshold - 0.22, tone)
    return stroke * pressure * (0.55 + 0.45 * grain)


def sketch(colour, alpha, depth01, normal, wash_amount):
    h, w, _ = colour.shape
    scale = h / 1080.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    px, py = xx, (h - 1 - yy)
    uv = np.stack([(xx + 0.5) / w, 1 - (yy + 0.5) / h], -1)
    world = np.clip(alpha, 0, 1)
    c = sp.saturate(sp.grade_colour(colour, uv))
    tone = (c * sp.LUM).sum(-1)

    fibre = noise(h, w, max(2, int(3 * scale)), 1)
    grain = noise(h, w, 1, 2)
    wob = noise(h, w, int(60 * scale), 3)
    blot = noise(h, w, int(90 * scale), 4)

    # paper, and the wash on it
    paper = PAPER * (1 - 0.05 * fibre[..., None])
    soft = 0.32 + 0.68 * (tone[..., None] + (c - tone[..., None]) * 0.85)
    # the figures (the kids, passers-by, the ball) keep their colour even on a pencil page: the kid stays easy to find
    figure_wash = np.maximum(wash_amount, 0.75)
    amount = (wash_amount + (figure_wash - wash_amount) * (1 - world))[..., None] * (0.75 + 0.5 * blot)[..., None]
    out = paper * (1 + (soft - 1) * amount)

    # hatching (lighter on the figures)
    sp_ = 7.0 * scale
    hat = hatch(px, py, 45, sp_, tone, 0.78, grain, wob, 11)
    hat = np.maximum(hat, hatch(px, py, -45, sp_, tone, 0.52, grain, wob, 23))
    hat = np.maximum(hat, hatch(px, py, 12, sp_ * 0.7, tone, 0.3, grain, wob, 37))
    hat *= 0.55 + 0.45 * world
    hat *= depth01 < 0.999          # the sky is left open: no hatching, only the wash
    out = out + (GRAPHITE - out) * (hat * 0.62)[..., None]

    # the doubled, wandering outline
    inkw = max(0.75, 1.3 * scale)
    j1 = (noise(h, w, int(40 * scale), 5) - 0.5) * 3.2 * scale
    j2 = (noise(h, w, int(40 * scale), 6) - 0.5) * 3.2 * scale
    e1 = edges(depth01, normal, world, yy + j1, xx - j2, inkw, FAR)
    e2 = edges(depth01, normal, world, yy - j2 * 0.8, xx + j1 * 0.8, inkw, FAR)
    line = np.clip(np.maximum(e1 * 0.9, e2 * 0.55), 0, 1) * (0.7 + 0.3 * grain)
    out = out + (GRAPHITE - out) * line[..., None] * 0.92

    # the paper's edge
    p = uv - 0.5
    out = out * (1 - 0.1 * sp.smoothstep(0.3, 0.9, (p * p).sum(-1)[..., None] * 2.2))
    return sp.saturate(out)


def load(src, name):
    a = np.asarray(Image.open(os.path.join(src, name))).astype(np.float64) / 255
    return a[..., :3]


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    suffix = sys.argv[3] if len(sys.argv) > 3 else ''
    os.makedirs(out, exist_ok=True)
    colour = load(src, 'colour%s.png' % suffix)
    n = load(src, 'normal%s.png' % suffix) * 2 - 1
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
    data = load(src, 'data%s.png' % suffix)
    depth = np.clip(data[..., 0] + data[..., 1] / 255.0, 0, 1)
    alpha = data[..., 2]
    for tag, wash in (('pencil', 0.12), ('coloured', 0.6)):
        img = sketch(colour, alpha, depth, n, wash)
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, '%s%s.png' % (tag, suffix)))
    Image.fromarray((sp.plain(colour) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, 'original%s.png' % suffix))
    print('done', suffix)
