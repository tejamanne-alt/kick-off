# Rebuilds every character model the game ships from its pre-polish original, reproducibly (docs/LEARNINGS.md,
# "The characters looked low quality"):
#   python3 polish_all.py [--blender /path/to/blenv/bin/python] [--source <git commit>] [--out <dir>] [--install]
#     --source  the commit holding the original FBXs and atlases (default f1b17b1: the last commit before the polish);
#               taken with `git show`, so a rerun never polishes an already polished model twice
#     --out     where the results go (default ./polished); --install copies them into Assets/_Game/Art/Models
# What it does:
#   the four primary-school kids (Kai, Leo, Mia, Zoe): face_paint.py (an illustrated face in place of the scan's
#     photographic one), then polish_character.py (welded, smoothed normals, the inner face leaned forward, 32k
#     triangles, each Locker Room bag 8k, the atlas' gaps filled);
#   Hana and Max: polish_character.py the same way (their painted faces are kept);
#   the six passers-by: polish_character.py at 14k triangles;
#   the five Locker Room bags' shared atlases (RGBA: the alpha marks the recolourable cloth): the gaps filled;
#   every <Name>.json's "tris" updated.
import argparse, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
MODELS = 'Assets/_Game/Art/Models'
KIDS = ['PrimaryBoy', 'PrimaryBoy2', 'PrimaryGirl', 'PrimaryGirl2']
TEENS = ['Girl', 'BackpackBoy']
WALKERS = ['Jogger', 'Mom', 'OfficeWorker', 'Courier', 'Shopkeeper', 'Grandad']
BAGS = ['KickOff', 'RaceCar', 'Unicorn', 'DenimBow', 'GoldenTrail']
PLAYER_TRIS, BAG_TRIS, WALKER_TRIS = 32000, 8000, 14000

ap = argparse.ArgumentParser()
ap.add_argument('--blender', default=os.environ.get('BLENDER_PY', 'blenv/bin/python'))
ap.add_argument('--source', default='f1b17b1')
ap.add_argument('--out', default=os.path.join(os.getcwd(), 'polished'))
ap.add_argument('--install', action='store_true')
ap.add_argument('--only', nargs='*')
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


for n in KIDS:
    if not want(n): continue
    painted = os.path.join(SRC, n + 'Atlas_painted.png')
    blender('face_paint.py', n, original(n + '.fbx'), original(n + 'Atlas.png'), painted, '--review', os.path.join(OUT, n + '_face.png'))
    blender('polish_character.py', original(n + '.fbx'), painted, OUT, '--name', n, '--tris', PLAYER_TRIS, '--bag-tris', BAG_TRIS, '--face-lean', 0.95)
for n in TEENS:
    if not want(n): continue
    blender('polish_character.py', original(n + '.fbx'), original(n + 'Atlas.png'), OUT, '--name', n, '--tris', PLAYER_TRIS, '--bag-tris', BAG_TRIS, '--face-lean', 0.85)
for n in WALKERS:
    if not want(n): continue
    blender('polish_character.py', original(n + '.fbx'), original(n + 'Atlas.png'), OUT, '--name', n, '--tris', WALKER_TRIS, '--face-lean', 0.85)
if want('bags'):
    for b in BAGS: original('Bag%sAtlas.png' % b)
    blender('polish_bags.py', original('Girl.fbx'), SRC, OUT, *BAGS)

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
