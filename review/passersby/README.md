# Passers-by

`walkers.jpg`: the jogger in four of her outfits (her own teal, then three the game can give her), beside the procedural
adult, in the game's look. Rendered by `render_walkers.py` (on `review/cartoon/render_scenes.py`), which recolours her
parts the way `ModelOutfit` does in the game.

Each new passer-by: a rigged FBX (Mixamo skeleton, A-pose rest, one mesh, texture embedded) through
`tools/blender/meshy_rigged.py -- <fbx> <out> --profile <name> --tris 30000`, a profile there saying which faces are its
jacket or top (1), trousers or skirt (2) and hair (3), then its name in `LevelBuildKit.PasserbyModels` and its colours in
`TrackBuilder.Walker`.
