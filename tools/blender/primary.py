# Builds one of the four primary-school kids (original characters) in Blender, with the teen pipeline:
#   blenv/bin/python primary.py -- /abs/path/PrimaryBoy.fbx --boy      # boy 1
#   blenv/bin/python primary.py -- /abs/path/PrimaryGirl.fbx --girl    # girl 1
#   blenv/bin/python primary.py -- /abs/path/PrimaryBoy2.fbx --boy2    # boy 2
#   blenv/bin/python primary.py -- /abs/path/PrimaryGirl2.fbx --girl2  # girl 2
# (teen.py takes the same as --primary-boy, --primary-girl, --primary-boy2, --primary-girl2.)
# Writes <Name>.fbx, <Name>.blend, <Name>Atlas.png and <Name>.json next to the .fbx, like teen.py.
# primary_spec.py says who they are; primary_body / _outfit / _head / _face / _hair are what the teen
# modules hand a teen_lib.Variant on to. --fast skips the head, hair and face atlas (for the clothes).
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FLAGS = {'--primary-boy': 'PrimaryBoy', '--primary-girl': 'PrimaryGirl', '--primary-boy2': 'PrimaryBoy2', '--primary-girl2': 'PrimaryGirl2'}


def run(argv):
    """Build the kid that argv names with a --primary-* flag; returns False if it names none."""
    names = [FLAGS[a] for a in argv if a in FLAGS]
    if not names: return False
    import teen_build, primary_spec
    out = argv[argv.index('--') + 1]
    r = teen_build.build(out, primary_spec.make(names[0]), names[0], '--fast' in argv)
    want = primary_spec.HEIGHT[names[0]]
    print('%s: for a standing height of %.2f m give the game a neck height of %.3f' % (names[0], want, r['head_z'] * want / r['height']))
    return True


if __name__ == '__main__':
    argv = [{'--boy': '--primary-boy', '--girl': '--primary-girl', '--boy2': '--primary-boy2', '--girl2': '--primary-girl2'}.get(a, a) for a in sys.argv]
    if not run(argv):
        sys.exit('primary.py -- /abs/Name.fbx --boy | --girl | --boy2 | --girl2 [--fast]')
