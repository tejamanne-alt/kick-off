# Checks Packages/manifest.json against the Unity version ProjectSettings/ProjectVersion.txt pins: a package too old for
# that Unity fails to compile in the user's editor, and nothing else here compiles the packages (docs/LEARNINGS.md A15).
#   python3 package_minimums.py <repo root>
# Each row: (package, the first Unity it applies to, the oldest package version that compiles there, why).
import json, os, re, sys

MINIMUMS = [
    ('com.unity.inputsystem', (6000, 2), (1, 14, 1),
     'Unity 6.2 made the non-generic TreeView obsolete (an error from 6.6); 1.14.1 uses TreeView<int>'),
]


def version(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


root = sys.argv[1] if len(sys.argv) > 1 else '.'
with open(os.path.join(root, 'ProjectSettings', 'ProjectVersion.txt')) as f:
    unity = version(re.search(r'm_EditorVersion:\s*(\S+)', f.read()).group(1))
with open(os.path.join(root, 'Packages', 'manifest.json')) as f:
    deps = json.load(f)['dependencies']
bad = 0
for pkg, since, oldest, why in MINIMUMS:
    if pkg not in deps or unity[:2] < since: continue
    have = version(deps[pkg])
    if have < oldest:
        bad += 1
        print('PACKAGE %s %s is too old for Unity %s: needs %s or newer (%s)' % (
            pkg, deps[pkg], '.'.join(map(str, unity)), '.'.join(map(str, oldest)), why))
print('packages checked against Unity %s: %s' % ('.'.join(map(str, unity)), 'ok' if not bad else '%d too old' % bad))
sys.exit(1 if bad else 0)
