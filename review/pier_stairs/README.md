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
| `course_board.jpg` | Low Tide in California, where the course climbs the pier: the four views below on one board |
| `course_up.jpg`, `course_top.jpg`, `course_down.jpg` | The game's camera following the kid up the steps with the ball, over the landing and down |
| `course_whole.jpg` | The climb across the lane: a 2 m landing fenced at the back (one rail from foot to foot), gentler flights, no rail on the camera's side |

## On the course (Low Tide, California)

The kid climbs the pier with the ball: its stairs stand across the lane (`TrackBuilder.PierClimb`, used by
`GreyboxLevels.LowTide` when the California scene is built), one collider up the nosings, across the landing and down.
The deck stands 2.3 m over the lane and the flights are about 21 degrees (risers 13.5 cm, treads 35 cm), no steeper than
the dunes, so the run keeps its pace; the kid keeps to slopes (`KidController`) instead of sliding back down them.

Built in the game as `World/PierStairs.cs` (one mesh), placed by `Editor/StreetBuilder.Coast.cs` (`Pier`,
`PierStairsUp`). `pier_stairs.py` is a step-for-step Python copy of that layout, so the pictures show what the build
makes; `render_pier.py` renders it in Blender with the game's own pier, palms, tower, kid and ball, and the toon
materials from `review/cartoon/render_scenes.py`:

```
blenv/bin/python render_pier.py -- $PWD/../../Assets/_Game/Art/Models /abs/renders
python3 -I compose.py /abs/renders .
blenv/bin/python render_pier.py -- $PWD/../../Assets/_Game/Art/Models /abs/course course
python3 -I compose.py /abs/course . --course
```
