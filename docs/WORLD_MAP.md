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

Map space is 1600 x 900 units, origin top left, y down; the map is drawn in a fixed-aspect frame and scaled to the screen. Positions below are the intended composition; tune them for looks.

- **Home** at the south-west (about 200, 700): the kid's house on Home Street, in a neighbourhood of small houses on a street grid. **The school** at the north-east (about 1360, 190), near the sea: the stone arch, the wall and the grounds, with its name.
- **The sea and the beach** along the east and south-east: the coast runs from the school's side down to the south-east corner, with a sand strip, a boardwalk, a lifeguard tower, parasols and palms. The beach route follows the coast road from home along the south and up the shore to the school.
- **The park** in the north-west and north: a fenced green area (its boundary drawn as a fence line) with a gate on its south side, a fountain square, a playground, a duck pond and trees. The park route enters at the gate and crosses to the school from the west.
- **The market** in the middle of the south: a block of shops with awnings, a market square, a zebra crossing and the main road with traffic. The market route runs along Market Street to the school.
- **The railway** across the middle from the west edge to the east, with the **underpass** (a road tunnel under the line) and the **building site** (fenced, with a tower crane and a digger) beside it. The underpass route goes through the tunnel; the site route is the shortcut through the site's gate.
- **Home Street's route** is the direct way: from the house up the hill and through the garden lanes, between the park and the market.
- A **town boundary** (a dotted line a little inside the frame), main streets with names, side streets, a few blocks of buildings, a compass and a "you are here" at home. Streets are realistic: the routes follow them (and the park's paths, the coast road, the tunnel) and meet only at the two ends, at most sharing a short stem near home and near the school.

## The map screen (`FrontEnd/ChapterMapScreen.cs`, data in `Levels/TownMap.cs`)

- Draws the town (land, sea, beach, park, market blocks, railway, site, streets, boundary, labels), the **house** and the **school**, and the **six routes** as coloured lines with a white casing from home to the school; each level is a numbered node on its route (stars below, a lock when locked, the next level to play pulses); each challenge a gold "!" node beside its route.
- The route that holds the next level to play (or the chapter asked for through `FrontEndController.RequestedChapter`) is in focus: full colour, thicker; the others are dimmed. A strip of route chips (name, stars out of the total) along the bottom focuses a route; a node can be tapped at any time.
- Paywalled chapters (`Monetization`) keep today's behaviour: their nodes are locked and an unlock button (`UnlockPanel`) appears for the focused route.
- Fits any aspect ratio from 4:3 to 21:9 without overlaps (the map is scaled to fit, the sea and land colours fill the rest), uses the safe area, and every string goes through `Loc` in English and Spanish.

## Every level starts at home (`Editor/LevelBuildKit.Home.cs`, `StreetBuilder.Home.cs`, `HomeLeadInRules.cs`, `Levels/HomeInfo.cs`)

**Nothing here has been seen in Unity** (see PROGRESS.md for what was checked offline and what was not).

- **A home lead-in of 12 m** (`LevelBuildKit.HomeLeadIn`, from `HomeLeadInRules.Length`) in front of every story level (L01 to L23). The kid starts on the doorstep of the house with the ball, walks the lead-in, and the route's own street begins where the layout's own x = 0 always was. Layouts are unchanged: the track builder shifts what must move (`TrackBuilder.LeadIn`, set by `BuildScene` for every level that is not a challenge and has a definition). The Start checkpoint (the kid's and the ball's spawn, and where a restart or a lost ball before the first checkpoint brings them back) is 12 m left of the layout's start, the back wall (`StartWall`), `MinX`, the camera's `minX` and `LevelManager.startBoundaryX` move with it, and the layout's first ground span (it always starts at its walls) grows back to the new wall: flat ground at the same height, one piece, so there is no joint to roll over. Every hint, sign, obstacle and pit keeps its x, so the feasibility audit says what it said (`HomeLeadInRules.GroundBefore` is the safety net for a layout whose first span starts elsewhere). The challenges (C01 to C05), the test track and the Holiday Run have no lead-in.
- **The bell grows by the walk:** `GeneratedContent.Bell(seconds)` adds `HomeLeadInRules.BellSeconds` (12 m at 4.2 m/s is 2.9 s, rounded up to 3) to each story level's authored street seconds, so the star thresholds mean what they did.
- **The lead-in looks like the home street** (chapter 1: lawns, houses, garden walls, poles, the footpath, road and verge of chapter 1) in every level. A chapter-1 level is one street, no seam. In the other four chapters the track has a **seam** at the layout's start (`TrackBuilder.SeamX`, on the sand's half-unit lattice):
  - *Ground:* the home street's slabs (road, footpath, verge; `LevelBuildKit.AsChapter(1, ...)` sets the static `Chapter` and `Theme` and puts them back) run from the world's start to the seam and are closed there; the route's own slabs (or, on the beach, its sand: `BeachGround` starts exactly at the seam) begin at the seam and are closed on that side, as the Holiday Run's stages are where chapters change (their surfaces stand at slightly different heights; each cap shows only as a step).
  - *Scenery:* two passes of the Holiday Run's stage scenery (`StreetBuilder.SceneryWithSeam`): the route's own chapter from the seam to 50 m past the level's end, built first, with the distant land too (`StageSpec.level`: fields and hills, the sea and its headlands, the site's cranes, because a level has no core scene), and chapter 1 from 50 m behind the back wall to the seam. Each pass builds exactly its stretch (lots, shops, poles, animals fit and stop at the seam; no back-row building or far row straddles it), the home pass's road gets ragged patches of the route's road surface and the route's pass patches of the home road, and on the beach a few props of the home street stand on the sand's edge (the stages' `SeamDressing`).
  - *At the seam itself:* a kerb stone across the footpath, a pair of bollards beside it, and **the route sign** 2.3 m before it.
- **The route sign** reads "School ->" and "via <route name>" (the English name from `RouteTable.Of(levelId).NameKey`; the levels' signs are English in every language, see `StringTables`). It is also on chapter-1 levels ("via Home Street").
- **The home front** (`TrackBuilder.HomeFront(x)` with `StreetBuilder.HomeFront`) is one set piece, the same in every level: the Buildings kit's **HouseGable** in `HomeInfo`'s colours (cream walls, a warm red front door, slate roof) with its door under the **gate** where the kid starts; a picket fence along the street, an open garden gate between two pillars (a pot on each, the house number 7 on one), hedges at the ends, a path to the doorstep, flower beds, a bush and pots, a bike on its stand, the bins, a post box on the footpath and a **parent** (the pedestrians' adult model, in its rest pose) on the top step. `HomeInfo` (house model, door colour, number) holds what the map needs to draw the same house, so the two match. The plot (`StreetBuilder.HomePlotLeft` to `HomePlotRight` around the gate) is a quiet area: the street's own lots keep out of it.
- **Tutorial:** L01's first lesson moved with the start (the "dribble" hint to x = -10.5, the walk sign to x = -8: 1.5 m and 4 m from the doorstep as they were from the old start). In every other level the first sign was 5 to 10 m from the start and is now 17 to 22 m from the doorstep, and the first hint (7 to 24 m before) is now 19 to 36 m: all of them come right after the seam, where they introduce the route's own street.
- The school end is the existing `TrackBuilder.Goal` arch in every level (all 23 story layouts call it exactly once; the audit checks it).
- Challenges (C01 to C05) are ball-skill arenas and keep their own start.
- The Holiday Run keeps its own world: all 23 stages in story order from the home street to the school gate. Its lap also starts at the kid's front door: stage 1 builds the same home front at the spawn point (`HolidayRunBuilder`, `TrackBuilder.HomeFront(HolidayStages.SpawnX)`).
