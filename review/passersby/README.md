# Passers-by

`walkers.jpg`: the six rigged passers-by (the jogger, Mom, the office worker, the courier, the shopkeeper, Grandad)
beside the procedural adult, in the game's look: first as they came, then dressed for three levels the way
`TrackBuilder.Walker` picks (top, legwear, and hair, cap or hijab from each one's wardrobe in `LevelBuildKit.Passersby`,
by the walker and the level). Rendered by `render_walkers.py` (on `review/cartoon/render_scenes.py`), which reads the
wardrobes from the code and recolours the parts the way `ModelOutfit` does in the game.

Each new passer-by: a rigged FBX (Mixamo skeleton, A-pose rest, one mesh, texture embedded) through
`tools/blender/meshy_rigged.py -- <fbx> <out> --profile <name> --tris 30000`, a profile there saying which colours are
its top (1), its legwear (2) and its hair or headwear (3), then a line in `LevelBuildKit.Passersby`: its file, its
height, its neck joint's share of its height (the script's log gives it), and its wardrobe.
