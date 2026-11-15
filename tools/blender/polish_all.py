# Rebuilds every character model the game ships from its pre-polish original, reproducibly (docs/LEARNINGS.md,
# "The characters looked low quality"):
#   python3 polish_all.py [--blender /path/to/blenv/bin/python] [--source <git commit>] [--out <dir>] [--install] [--no-ink]
#     --source  the commit holding the original FBXs and atlases (default f1b17b1: the last commit before the polish);
#               taken with `git show`, so a rerun never polishes an already polished model twice
#     --out     where the results go (default ./polished); --install copies them into Assets/_Game/Art/Models
#     --no-ink  the kids' scanned faces exactly as they are (no face_ink.py finish)
# What it does:
#   the four primary-school kids (Kai, Leo, Mia, Zoe): face_ink.py (their own scanned faces given the finish of Max's:
#     a dark lash line along each eye's own top edge, solid brows, the lips' parting, an even skin tone; nothing redrawn
#     or moved), then polish_character.py (welded, smoothed normals, the inner face leaned forward, 32k triangles, each
#     Locker Room bag 8k, the atlas' gaps filled). (face_paint.py's drawn faces were rejected: docs/LEARNINGS.md, C14.)
#   Hana and Max: polish_character.py the same way (their painted faces are kept);
#   the six passers-by: polish_character.py at 14k triangles;
#   the extra bags (EXTRA_BAGS: the two randoseru, built from the user's views) fitted onto each kid's original first;
#   the Locker Room bags' shared atlases (RGBA: the alpha marks the recolourable cloth): the gaps filled;
#   every <Name>.json's "tris" updated.
import argparse, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
MODELS = 'Assets/_Game/Art/Models'
KIDS = ['PrimaryBoy', 'PrimaryBoy2', 'PrimaryGirl', 'PrimaryGirl2']
TEENS = ['Girl', 'BackpackBoy']
WALKERS = ['Jogger', 'Mom', 'OfficeWorker', 'Courier', 'Shopkeeper', 'Grandad']
BAGS = ['KickOff', 'RaceCar', 'Unicorn', 'DenimBow', 'GoldenTrail']
# Bags added after the source commit, so in none of the originals: each built from the user's views (bag_views.py),
# prepared (meshy_bag.py prep, with its own colour arguments), and fitted onto every kid's original before its polish.
EXTRA_BAGS = [('RandoseruRed', ['--hue', '340,18', '--sat', '0.5']),     # its red body recolourable
              ('RandoseruBlack', ['--sat', '2'])]                       # its own colours (black stays black)
PLAYER_TRIS, BAG_TRIS, WALKER_TRIS = 32000, 8000, 14000

ap = argparse.ArgumentParser()
ap.add_argument('--blender', default=os.environ.get('BLENDER_PY', 'blenv/bin/python'))
ap.add_argument('--source', default='f1b17b1')
ap.add_argument('--out', default=os.path.join(os.getcwd(), 'polished'))
ap.add_argument('--install', action='store_true')
ap.add_argument('--only', nargs='*')
ap.add_argument('--no-ink', action='store_true')
a = ap.parse_args()
OUT = os.path.abspath(a.out)
SRC = os.path.join(OUT, '_source')
os.makedirs(SRC, exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')


def original(name):
    """The file as it was at the source commit."""
    dst = os.path.join(SRC, name)
    if not os.path.exists(dst):
        data = subprocess.run(['git', '-C', REPO, 'show', '%s:%s/%s' % (a.source, MODELS, name)], check=True,
                              capture_output=True).stdout
        with open(dst, 'wb') as f: f.write(data)
    return dst


def blender(script, *args):
    cmd = [a.blender, os.path.join(HERE, script), '--'] + [str(x) for x in args]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if l.startswith('[')]
    print('\n'.join(lines))
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit('failed: ' + ' '.join(cmd))


def want(n): return not a.only or n in a.only


# the extra bags, built and prepared once (and their Locker Room pictures)
BAGDIR = os.path.join(OUT, '_bags')
os.makedirs(BAGDIR, exist_ok=True)
for bag, args in EXTRA_BAGS:
    if not os.path.exists(os.path.join(BAGDIR, 'Bag%s.blend' % bag)):
        blender('bag_views.py', bag, BAGDIR)
        blender('meshy_bag.py', 'prep', os.path.join(BAGDIR, bag + '.fbx'), BAGDIR, '--id', bag, '--tris', 12000, '--even', *args)
        blender('meshy_bag.py', 'icon', os.path.join(BAGDIR, 'Bag%s.blend' % bag), os.path.join(OUT, 'bag_%s.png' % bag.lower()))
    for f in ('Bag%sAtlas.png' % bag, 'Bag%s.json' % bag):
        shutil.copy2(os.path.join(BAGDIR, f), os.path.join(SRC if f.endswith('.png') else OUT, f))


def with_extra_bags(n):
    """The kid's original with the extra bags fitted on (the FBX polish_character.py then takes)."""
    if not EXTRA_BAGS:
        return original(n + '.fbx')
    work = os.path.join(SRC, 'fit_' + n)
    os.makedirs(work, exist_ok=True)
    blend = os.path.join(work, n + '.blend')
    blender('fit_source_blend.py', original(n + '.fbx'), blend)
    for bag, _ in EXTRA_BAGS:
        blender('meshy_bag.py', 'fit', blend, os.path.join(BAGDIR, 'Bag%s.blend' % bag), work)
    return os.path.join(work, n + '.fbx')


for n in KIDS:
    if not want(n): continue
    atlas = original(n + 'Atlas.png')
    if not a.no_ink:
        inked = os.path.join(SRC, n + 'Atlas_inked.png')
        blender('face_ink.py', n, original(n + '.fbx'), atlas, inked, '--review', os.path.join(OUT, n + '_face.png'))
        atlas = inked
    blender('polish_character.py', with_extra_bags(n), atlas, OUT, '--name', n, '--tris', PLAYER_TRIS, '--bag-tris', BAG_TRIS, '--face-lean', 0.95)
for n in TEENS:
    if not want(n): continue
    blender('polish_character.py', with_extra_bags(n), original(n + 'Atlas.png'), OUT, '--name', n, '--tris', PLAYER_TRIS, '--bag-tris', BAG_TRIS, '--face-lean', 0.85)
for n in WALKERS:
    if not want(n): continue
    blender('polish_character.py', original(n + '.fbx'), original(n + 'Atlas.png'), OUT, '--name', n, '--tris', WALKER_TRIS, '--face-lean', 0.85)
if want('bags'):
    for b in BAGS: original('Bag%sAtlas.png' % b)
    # (the islands from a kid who has every bag: the extra bags are only in the fitted copy)
    girl = os.path.join(SRC, 'fit_Girl', 'Girl.fbx')
    if EXTRA_BAGS and not os.path.exists(girl): girl = with_extra_bags('Girl')
    blender('polish_bags.py', girl if EXTRA_BAGS else original('Girl.fbx'), SRC, OUT, *(BAGS + [b for b, _ in EXTRA_BAGS]))

# the json files: the original's colours, the new triangle count
for n in KIDS + TEENS + WALKERS:
    if not want(n): continue
    rep = os.path.join(OUT, n + '_polish.json')
    if not os.path.exists(rep): continue
    with open(original(n + '.json')) as f: data = json.load(f)
    with open(rep) as f: data['tris'] = json.load(f)['meshes']['Kid']['tris_out']
    with open(os.path.join(OUT, n + '.json'), 'w') as f: json.dump(data, f)

if a.install:
    dst = os.path.join(REPO, MODELS)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.fbx') or f.endswith('Atlas.png') or (f.endswith('.json') and not f.endswith('_polish.json')):
            shutil.copy2(os.path.join(OUT, f), os.path.join(dst, f))
            print('installed', f)
        elif f.startswith('bag_') and f.endswith('.png'):      # an extra bag's Locker Room picture
            shutil.copy2(os.path.join(OUT, f), os.path.join(REPO, 'Assets/_Game/Resources/UI', f))
            print('installed', f)
