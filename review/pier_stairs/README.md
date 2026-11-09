# Stairs up to the pier: design pictures

The California beach's pier (Coast kit `PierSpan`, deck 4.8 m over the sea) started in mid-air over the sand with no
way up. The design: a landing at deck height in front of the first span, a flight of stairs down to the sand on the
left and on the right (a mid-landing halfway on each), and a boardwalk path on the sand from each foot toward the lane.

| Picture | What it shows |
|---|---|
| `pier_stairs_board.jpg` | The three views below on one board |
| `game.jpg` | From the game's play camera (CameraFollow2D's framing, a phone's width), the kid running past |
| `whole.jpg` | The whole front: the landing, both flights, the mid-landings, the lamps |
| `close.jpg` | The left flight close up: timber treads, white risers and cut stringers, rails, the path at the foot |

Built in the game as `World/PierStairs.cs` (one mesh), placed by `Editor/StreetBuilder.Coast.cs` (`Pier`,
`PierStairsUp`). `pier_stairs.py` is a step-for-step Python copy of that layout, so the pictures show what the build
makes; `render_pier.py` renders it in Blender with the game's own pier, palms, tower, kid and ball, and the toon
materials from `review/cartoon/render_scenes.py`:

```
blenv/bin/python render_pier.py -- $PWD/../../Assets/_Game/Art/Models /abs/renders
python3 -I compose.py /abs/renders .
```
