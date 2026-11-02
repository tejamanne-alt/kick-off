# Builds one of the two playable teens (original characters) in Blender:
#   blenv/bin/python teen.py -- /abs/path/Boy.fbx --boy
#   blenv/bin/python teen.py -- /abs/path/Girl.fbx --girl
# Writes <Name>.fbx, <Name>.blend, <Name>Atlas.png (the painted face atlas) and
# <Name>.json (the default outfit colours the game recolours from) next to the .fbx.
# (The four primary-school kids are built the same way by primary.py; the steps are in teen_build.py.)
#
# The pieces live in modules: teen_body (joints, skin, proportions), teen_outfit (clothes,
# shoes, bag), teen_head (head and ears), teen_hair, face_teen (the face painting), with
# shared helpers in teen_lib. teen_build colours, rigs, joins and exports them.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import teen_build, primary
if primary.run(sys.argv): sys.exit(0)           # --primary-boy / --primary-girl / --primary-boy2 / --primary-girl2

OUT = sys.argv[sys.argv.index('--') + 1]
GIRL = '--girl' in sys.argv
NAME = 'Girl' if GIRL else 'Boy'
# --fast (for iterating on the clothes): no head, no hair, and the face atlas painted only if it is not there yet
FAST = '--fast' in sys.argv
teen_build.build(OUT, GIRL, NAME, FAST)
