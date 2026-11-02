# The town, the routes and the way to school

One home, one school, six ways between them. **Every story level is one trip from the front door to the school gate along one route**: it starts on the home front, runs through that route's own streets (the level's chapter look) and ends at the school's arch, the same arch and grounds in every level. The map shows the town with the six routes drawn from the house to the school and each level on its route.

Nothing here has been run in Unity or on a device (see PROGRESS.md for what was checked offline).

## The routes (`Levels/RouteTable.cs`)

| Route (en / es) | Chapter | Levels along it (place) | The challenge beside it |
|---|---|---|---|
| **Home Street** / Mi calle (`street`) | 1 | L01 Out the Door (the front of the house), L02 Parked Cars (Elm Street), L03 Up the Hill (Hill Road), L04 Garden Gate (Garden Lane), L05 Puddle Lane | C01 Keepy-Uppy (the front garden) |
| **Market Street** / Calle del mercado (`market`) | 2 | L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour | C02 Window Shopping |
| **Seaside Road** / Paseo marítimo (`beach`) | 3 | L11 Boardwalk, L12 Low Tide, L13 Seagull Bay, L14 Sandcastle Sprint | C03 Beach Slalom |
| **The Underpass** / El paso subterráneo (`underpass`) | 4 | L15 The Underpass, L18 Tunnel Run (the road tunnel under the railway) | none |
| **Building Site Shortcut** / Atajo de las obras (`site`) | 4 | L16 Building Site, L17 Cranes | C04 Site Targets |
| **Park Path** / Camino del parque (`park`) | 5 | L19 Park Gates, L20 Fountain Square, L21 Playground, L22 Duck Pond, L23 The Final Bell | C05 Juggle Champion |

Chapters stay the unit of the paywall (`Store/Monetization.IsChapterUnlocked`), of the Holiday Run's stages and of the level catalog; routes are how the map and the levels present them. Chapter 4 has two routes, and its levels alternate between them (15 underpass, 16 and 17 site, 18 underpass). Progression is unchanged: a story level unlocks when the one before it in the catalog is done (`Progression/LevelUnlocks`); a challenge unlocks with its chapter's first level.

## The town (the map's geography)

The map is a **rendered picture of the town** with a **layout file** that says where everything is on it:

| File | What |
|---|---|
| `Assets/_Game/Resources/UI/TownMap.jpg` | The picture, **3200 x 1800 px**, a top-down render of the town. Its **core**, the central **2400 x 1350 px** (offset 400, 225), holds everything the player needs; the **ring** round it is more town (not a border), so screens of other shapes still see town. |
| `Assets/_Game/Resources/TownMapLayout.json` | The layout, in the picture's pixels (origin top left, y down). Read by `Levels/TownMap.cs`. |

The composition below is the brief for the picture (the layout is what the game reads, so the art may move things within it):

- **Home** at the south-west of the core: the kid's house on Home Street, in a neighbourhood of small houses on a street grid. **The school** at the north-east, near the sea: the stone arch, the wall and the grounds.
- **The sea and the beach** along the east and south-east: the coast runs from the school's side down to the south-east corner, with a sand strip, a boardwalk, a lifeguard tower, parasols and palms. The beach route follows the coast road from home along the south and up the shore to the school.
- **The park** in the north-west and north: a fenced green area with a gate on its south side, a fountain square, a playground, a duck pond and trees. The park route enters at the gate and crosses to the school from the west.
- **The market** in the middle of the south: a block of shops with awnings, a market square, a zebra crossing and the main road with traffic. The market route runs along Market Street to the school.
- **The railway** across the middle from the west edge to the east, with the **underpass** (a road tunnel under the line) and the **building site** (fenced, with a tower crane and a digger) beside it. The underpass route goes through the tunnel; the site route is the shortcut through the site's gate.
- **Home Street's route** is the direct way: from the house up the hill and through the garden lanes, between the park and the market.
- Streets are realistic: the routes follow them (and the park's paths, the coast road, the tunnel) and meet only at the two ends, at most sharing a short stem near home and near the school. The picture carries no text of its own and no route lines, nodes or markers: the game draws those.

### The layout file (`Resources/TownMapLayout.json`)

```
{ "image": "UI/TownMap", "width": 3200, "height": 1800,
  "core":      {"x": 400, "y": 225, "w": 2400, "h": 1350},
  "places":    [ {"id": "home", "x": .., "y": ..}, {"id": "school", "x": .., "y": ..} ],
  "routes":    [ {"id": "street", "points": [{"x": .., "y": ..}, ...]}, ... ],   six, in RouteTable's order
                 (street, market, beach, underpass, site, park), each from home to the school
  "nodes":     [ {"id": "L01", "x": .., "y": .., "label": "below" | "above" | "left" | "right"}, ... ],   every story level and challenge
  "districts": [ {"id": "neighbourhood" | "market" | "beach" | "park" | "railway" | "site" | "school" | "sea", "x": .., "y": ..}, ... ],
  "streets":   [ {"name": "Elm Street", "x": .., "y": .., "angle": ..}, ... ] }
```

`label` is the side of its node on which the level's name is written; `angle` is the street name's rotation in degrees, clockwise on screen (y down). A node is a 150 px disc, and a name is written in a 300 x 56 px box 12 px from the disc (`TownMap.LabelRect`). District names are the strings `district.<id>` (English and Spanish); street names are shown as given, never translated.

`Tests/Editor/TownMapTests.cs` checks the file against the picture and `RouteTable`: the frame and core are as agreed and the picture is 3200 x 1800; every story level and challenge has exactly one node, each with a name side (below, above, left or right); nodes and places lie inside the core's inner area (core-relative x 120..2280, y 170..1130); node discs are 190 px or more apart; a story node is within 12 px of its own route and the nodes follow the playing order along it; a challenge node is 130 to 260 px from its route; the routes are RouteTable's six in its order, start at home and end at the school (within 25 px), are 1200 px or longer, and keep 90 px apart except within 320 px of the two ends; a level name's box is clear of every route (30 px), node and other name; the six route colours tell apart; every string the map uses exists in both languages.

**The picture and layout in the repo now are a placeholder** made from abstract geometry (a flat, vector-looking map; `"placeholder": true` in the layout; its routes are straight-ish diagonals, so the name-box clearance check is skipped for it). To swap in the real art: overwrite those two files (the real layout has no `placeholder` field), run the EditMode tests (`TownMapTests`) and look at the map screen. Nothing in the code depends on the placeholder's numbers.

## The map screen (`FrontEnd/ChapterMapScreen.cs`, data in `Levels/TownMap.cs`)

- **The picture** is a `RawImage` in a 3200 x 1800 block that `UI/Kit/UIFitRect` scales (the same scale both ways, never stretched) so the **core** fits the room between the title row and the level strip, centred: about 0.48 canvas units per picture pixel on the 1080-tall canvas, at every aspect ratio from 4:3 to 21:9. The ring shows round it as far as it reaches, and the picture's edges fade into the navy mat. If the picture is missing, a plain background takes its place and everything else still works; if the layout is missing, the picture shows with only the strip and the chips to play from.
- **On the picture** the game draws: the **six routes** as coloured lines with a white casing from home to the school (the focused route 54 px wide with a dashed centre, the others 30 px and dimmed; chapter 4's two routes are two shades of its colour) and a dotted branch to each challenge; a red **house** pin and a blue **school** pin with their names, and "You are here" by the house; each level as a **numbered node** (a 150 px disc in the route's colour, the stars on a white pill on its lower rim, a lock and no stars when locked, the next level to play pulsing), each challenge as a gold **"!"** node; the focused route's **level names** (white with a dark outline) on the side the layout gives; the **district names** (small capitals) and **street names** (small, along the road at the angle given), each only where it touches no node, name, pin or route line. The school district's name is left out: its pin already says School.
- **Along the top:** the title ("Choose your way to school") and a card with the focused route's colour, name and stars out of the total. **Along the bottom:** the focused route's levels as a strip like a level select (a **LEVELS** tag, a house, a chip for each level with its number or a lock and its stars, a "!" chip for the challenge, the school, and a marker over the next level) and under it a **chip for each of the six routes** (colour, name, stars out of the total) that moves the focus. Level chips and nodes play the level (`Controller.PlayLevel`); locked ones do nothing.
- The route with the next level to play (`LevelUnlocks.NextToPlay`), or the one asked for through `FrontEndController.RequestedChapter` (the route of that chapter that holds the next level, else its first), starts in focus.
- Paywalled chapters (`Monetization.IsChapterUnlocked`) keep today's behaviour: their levels are locked and an unlock button (`UnlockPanel`) sits on the focused route.
- Touch targets: a node's tap area is a clear box at least 118 canvas units across (more than its 72 unit disc), a strip slot 100 x 104, a route chip about 120 x 110. Text is never under 22 canvas units (names 24; a route chip's name shrinks to 22 and takes a second line on a narrow screen); every string goes through `Loc` in English and Spanish.
- The picture is loaded when the map is shown and released (`Resources.UnloadAsset`) when it is hidden or the screen is rebuilt. `Editor/UiArtImportSettings` imports it as an opaque texture (up to 4096, no mipmaps, bilinear, clamped, kept at 3200 x 1800, high-quality compression), not as a sprite like the other pictures in `Resources/UI`.

## Every level starts at home (`Editor/LevelBuildKit*.cs`, `StreetBuilder*.cs`)

- Each story level gets a **home lead-in** of about 12 m before its own start: the kid starts on the doorstep of the house with the ball, walks along the front of the house and its garden, and reaches the route's own street where the level begins (x = 0 as before, so every layout and its feasibility audit is unchanged).
- The lead-in is the **home street's look** (chapter 1: lawns, houses, walls, poles) in every level, even on the beach, at the site and in the park, with a short **route signpost** ("School -> Seaside Road") where the route's own environment takes over.
- The **home front** is one set piece built from the kits: the house with its door, a garden gate, picket fence, mailbox, flower pots, a bike and a parent at the door.
- The school end is the existing `TrackBuilder.Goal` arch in every level.
- Challenges (C01 to C05) are ball-skill arenas and keep their own start.
- The Holiday Run keeps its own world: all 23 stages in story order from the home street to the school gate.
