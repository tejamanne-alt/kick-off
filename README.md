# Kick Off 2

A football side-scroller for iOS and Android, built in Unity 6: a schoolkid (one of six, from high school or primary school) dribbles a ball through clear-daylight anime streets all the way to school.
The full game brief is in [`GAME_PROMPT.md`](GAME_PROMPT.md).

## Status

All eight phases of the build plan are done (see [`PROGRESS.md`](PROGRESS.md)):

- **Gameplay:** core dribbling and kicking, level flow, 13 hazard types, and 23 story levels across 5 chapters plus 5 ball-skill challenges.
- **Holiday Run:** the campaign with no destination: the same controls and ball along the whole story world, one 120 m stage for each of the 23 levels in story order, a lap a day. See [`docs/HOLIDAY_RUN.md`](docs/HOLIDAY_RUN.md).
- **Progression:** coins, stickers, saving, the Locker Room shop and the town map (a picture of the town with six routes from the kid's house to the school and the stops between their levels, which pans and zooms; see [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md)).
- **Presentation:** procedural storybook art, animation, FX, music and sound effects, and haptics.
- **Menus and options:** settings, localization (English and Spanish), tutorial hints and accessibility options.
- **Release setup:** store and unlock, local analytics, and build scripts.

The next step is playtesting on real devices.

## Open the project

1. Install **Unity 6** (6000.0 LTS or newer) with **iOS Build Support** and/or **Android Build Support** from Unity Hub.
2. In Unity Hub choose **Add > Add project from disk** and select this folder. If Hub asks about the editor version, pick any Unity 6 version you have installed.
3. On the first open, Unity imports packages. If it asks to **enable the new Input System backend**, click **Yes** (the editor restarts). The code works with either input backend.
4. Once importing finishes, an editor script generates the menu, every level scene and the shop items, then opens the **FrontEnd** menu scene. It runs again automatically whenever the generated content is out of date. You can also run it from **Kick Off > Rebuild All Levels** (or **Kick Off > Rebuild Menu (FrontEnd)** for just the menu scene).
5. Press **Play**. Set the Game view to a landscape phone resolution (for example 1920x1080).

Generated scenes are rebuilt from code, so edits made directly in those scenes get overwritten on the next rebuild. Change the layouts in `Editor/GreyboxLevels.cs` instead, or duplicate a scene before you edit it by hand. Tuning assets and level definitions are never overwritten.

## Levels

| Ch | Levels | New ideas |
|---|---|---|
| 1 Home Street | L01 Out the Door, L02 Parked Cars, L03 Up the Hill, L04 Garden Gate, L05 Puddle Lane | Tutorial, cars, stairs, button gates, puddles |
| 2 Market | L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour | Pedestrians, traffic lights, springboards |
| 3 The Beach | L11 Boardwalk, L12 Low Tide, L13 Seagull Bay, L14 Sandcastle Sprint | Sand, tides, seagulls, sea breeze |
| 4 Underpass | L15 The Underpass, L16 Building Site, L17 Cranes, L18 Tunnel Run | Dark tunnels, rolling pipes, moving platforms |
| 5 Park & School | L19 Park Gates, L20 Fountain Square, L21 Playground, L22 Duck Pond, L23 The Final Bell | Dogs, fountains, swings, the finale |

**Every route is one trip from the front door to the school gate, and each story level is one leg of it**, along one of six routes (Home Street, Market Street, Seaside Road, the Underpass, the building site's shortcut and the Park Path; see [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md)). Only a route's first level starts on the doorstep of the house (a cream house with a red front door, then 12 m of home street, in the first chapter's look whatever the level, to a sign with the route's name), and only its last level ends at the school's arch. Every level between runs from one stop on the way to the next, and the next level on the route starts where the last one ended: Home Street goes home, the bus stop, granny's house, the church on the hill, Sam's house, school; Market Street the bakery, the post office, the flower shop, the library; Seaside Road the surf school, the lifeguard tower, the beach cafe; the Underpass the railway station; the building site the site office; the Park Path the bandstand, the park cafe, the boathouse, grandpa's allotment. Each stop is a set piece of its own (a shelter, a bungalow and garden, a church with a spire, shops with their names, a kiosk on the sand, a ticket hall...) with someone waiting at some of them, a chalk line marks where a level ends at one, the route sign says where the level goes ("Granny's house ->, via Home Street"), the HUD shows the leg under the level's name ("Granny's house » Church") and the results say "Made it to the church!". Every story level walks 12 m from its stop before its own street begins, about 3 seconds, added to every bell. The challenges keep their own arenas and starts.

**Ball-skill challenges** are optional. There's one per chapter, unlocked by finishing the chapter's first level:

| Challenge | Type | Stars |
|---|---|---|
| C01 Keepy-Uppy | Juggling (45 s) | 5 / 10 / 15 juggles |
| C02 Window Shopping | Accuracy (60 s) | 3 / 5 / 7 targets |
| C03 Beach Slalom | Slalom: low bars and hoops | under 40 s / 28 s / 22 s (misses +3 s) |
| C04 Site Targets | Accuracy (60 s) | 4 / 6 / 8 targets |
| C05 Juggle Champion | Juggling (60 s) | 10 / 20 / 30 juggles |

Bell times and streak targets are in the level table in `Editor/GeneratedContent.cs` (a story level's bell is its street's seconds, as written there, plus the walk from the front door: `Bell(...)`). Change them there, then run **Kick Off > Rebuild All Levels**.

## Hazards

| Hazard | Behaviour |
|---|---|
| Pedestrian | Walks and pauses. The ball bounces off; the kid slips past. |
| Crossing | A zebra over a side street with a pedestrian signal: green man, flashing green man, red man. Cars wait at the stop line up the street, then drive through the crossing toward the camera on the red man; the kid or the ball on the road then loses the ball. |
| Dog | Wanders and chases low balls, nosing them back. Chip over it. |
| Puddle / Sand | Slows the ball and the kid. |
| Wind | A headwind or an updraft on the ball; can gust. |
| Moving platform | Slides back and forth and carries the kid. |
| Button + gate | Kick the ball at the button to open the gate. |
| Springboard | Launches the kid or the ball upward. |
| Seagull | Swoops across and knocks the ball. |
| Tide | Water washes in and out; cross at low tide. |
| Tunnel | Darkens the screen to a pool of light around the kid. |
| Rolling pipes | Roll down slopes at you; jump them. |
| Swing | A pendulum seat that carries the kid over pits. |
| Fountain | A plaza floor fountain: pulsing jets from a grate in the paving that lift the ball as high as the jet currently reaches. |
| Slide-under barrier | Solid from 0.85 m up: slide under it (the ball rolls under too). Every level has one or two, picked to suit it from the Barriers kit: painters' boards on trestles, a car-park barrier arm, a hedge trimmer's work platform or an apple tree's propped bough in the home street; a fruit stall under its awning, a half-raised roll shutter or a delivery conveyor at the market; a surf rack, a rowing boat upturned on trestles, a boardwalk crossing or a lifeguard's rescue board on the beach; a sheeted scaffold, steel beams on trestles, a pipe rack or a site barrier on the building site; a fallen trunk, an old oak's propped bough, a rope-net tunnel or a play tower in the park. Low ones can be hopped too; tall ones have to be slid under; the round trunk can be double jumped. `TrackBuilder.SlideUnder(x, SlideLook)`. |

## Level rules

- **Start:** you stand on the doorstep with the ball, a short "Ready... GO!" countdown, then you're in control. Restarting a level, or losing the ball before the first checkpoint, puts you back at the doorstep.
- **Checkpoints** (grey flags) turn green when the kid passes them with the ball close by.
- **Losing the ball** (falling into a gap or water, falling off the level, or kicking it back past the start of the level: "the ball rolled back home") fades the screen and sends you back to the last checkpoint. There's no game over, and the clock keeps running. If you walk off without the ball, just walk back for it.
- **School bell:** a countdown to the bell. When it rings you can still finish, you're just late. Turn it off in the pause menu (cozy mode).
- **Stars:**
  - 1 star for reaching school with the ball.
  - 2 stars for getting there before the bell.
  - 3 stars for also hitting the level's perfect-touch streak target. Coins join this condition in Phase 4.
- **Pause menu:** Resume, Back to checkpoint (if the ball gets stuck), Restart level, School bell on/off, and a dev "Skip to next level".

## Controls

| Action | Phone | Keyboard / mouse |
|---|---|---|
| Walk back / forward (hold) | The stick (bottom-left): push left or right; let go to stop | `A` / `←`, `D` / `→` |
| Jump (hold = higher) | JUMP button (the leaping kid in the bottom-right corner) or swipe up | `Space` / `W` / `↑` |
| Double jump | JUMP again in the air | `Space` / `W` / `↑` again |
| Slide | Pull the stick down (down-right slides forward, down-left back), or swipe down | `S` / `↓` |
| Touch / juggle | Quick tap anywhere else | `F` / `J` |
| Kick (aimed) | Drag from the KICK button (left of JUMP) the way the ball should go, release | Mouse drag from KICK |
| Kick (quick pass) | Tap KICK | `K` |
| Pause | Pause button | `Esc` / `P` |
| Restart level | Pause > Restart | `R` |
| Tuning panel | Tuning button | `Tab` |

Holiday Run uses exactly these controls.

## How it plays

- **Walk** with the stick: push it right to go forward, left to go back. Whenever the kid walks into the ball, it gets a slightly random touch in the walking direction, so you can dribble forward or back.
- **Perfect touch:** tap as the kid closes in and the ball sits in the sweet spot just ahead of the feet. Perfect touches have no randomness and they build a streak.
- **Juggle:** tap while the ball is in the air near the kid.
- **Kick:** drag from the KICK button (left of JUMP) in the direction you want the ball to go: up-right to chip forward, up-left to chip back. The length sets the power. Time slows while you aim, and only the first 0.5 s of the flight is previewed. A quick tap on KICK is a short pass the way the kid faces. Kicks only work when the ball is within reach: the KICK button glows green when it is, and the dots turn red when it isn't.
- **Stop** by letting go of the stick. A stopping kid traps the ball under the foot.
- **Double jump:** press JUMP again in the air for a second, slightly lower jump with a tucked somersault (hold for its full height, like the first). It reaches about 2.2 m: over 1.6 m walls and fallen trees and up to high coins, but not over the 2.4 m gates. A trampoline bounce gives it back.
- **Slide:** pull the stick down (or swipe down anywhere else) for a feet-first slide along the ground, a little faster than running, for about 0.7 s. The kid is low enough to pass under anything with a 0.85 m gap, and won't stand up while something is overhead (they shuffle on until clear). A sliding kid nudges the ball on along the ground without breaking a perfect-touch streak. Jump out of a slide for a longer jump. The way the stick leans as it goes down picks the way: down and right slides forward, down and left slides back, straight down slides the way the kid is going (or facing). It slides once per pull: bring the stick back up past the middle to slide again.
- **Left-handed mode** (Settings > Controls) puts the stick on the right and JUMP and KICK on the left.
- **Touch layout:** each thumb has a job. The left thumb walks and slides with one stick: a see-through glass ring with a knob resting in the bottom-left corner. Touch anywhere in the bottom-left area and the ring comes to the thumb (kept whole on screen); the knob follows the thumb, a push past a small dead zone walks, and a pull down slides. Small marks inside the ring (‹ › and the slide glyph) say what it does, and the one it points to lights up. If the thumb drifts past the ring, the ring follows it. The right thumb jumps and kicks: JUMP in the corner where the thumb rests and KICK a thumb's width to its left on the same baseline (with the whole screen above it to aim in). JUMP and KICK are one size. They are nearly see-through until touched (a faint rim, a faint icon; held, they light up; KICK glows green while the ball is in reach). JUMP's icon is a kid leaping off a ground line. A touch near a button goes to that button first; anywhere else on the left goes to the stick, and on the right it is a tap or a swipe. Sizes are in screen heights, so the buttons are the same size on every phone and shrink only on screens narrower than 4:3. **The kid is never under a thumb:** the camera stands the kid a set fraction of the way across the screen (38%), further right on narrow screens as far as the stick's area on the left needs (`GameInput.KidSafeScreenX`, `CameraFollow2D.kidScreenX`). Positions and feel are on the `GameInput` object (`jumpButton`, `kickButton`, `walkStick`, `stickRoamIn`, `stickRoamUp`, `stickDeadZone`, `stickSlideDown`, `stickSlideRelease`); the look is `UI/Kit/StickView`.

## Holiday Run

The campaign with no destination, from the title screen: the same controls, the same ball and the same hazards, along one long street made of all 23 story levels end to end (Home Street, the Market, the Beach, the Underpass and building site, then the Park and the school gate). Nothing runs by itself and there is no bell and no finish: you dribble, jump, slide and kick on. Reaching the school gate ends the day and the street starts again at home. Along the way:

- Obstacles use the same kit models and hazards as the story levels, in three random layouts per stage, so no two days play the same. Light, haze and music change gradually from one chapter to the next.
- You have three balls: losing one sends you back to the stage's checkpoint, as in a level, and the last one ends the run.
- Score is new ground, coins and a multiplier that climbs with every obstacle passed in a row; close shaves score bonuses, and a hard kick smashes crates and sandcastles for coins.
- Magnet, Shield and Turbo power-ups; three missions at a time that pay coins; spend coins to revive with one more ball (the coins of a run are banked when it ends).
- Stages stream in as additive scenes, so only about three exist at a time however long the run.

Design, scoring, tuning knobs, the streaming contract and a first-run checklist are in [`docs/HOLIDAY_RUN.md`](docs/HOLIDAY_RUN.md).

## Tuning the feel

Every feel value lives in two assets:

- `Assets/_Game/Settings/PlayerTuning.asset`: run speed, acceleration, jump, gravity, coyote time, jump buffer.
- `Assets/_Game/Settings/BallTuning.asset`: bounce, friction, rolling resistance, reach, lead speed, perfect band, juggle, kick power, slow motion, preview.

You can edit them in the Inspector or live in Play mode with the in-game **Tuning** panel. In the editor, panel changes are saved to the assets.

Values worth experimenting with first:

1. `BallTuning.dribbleLeadSpeed` and `rollingResistance` set the dribble rhythm, meaning how far the ball runs ahead and how fast the kid catches up.
2. `BallTuning.perfectTouchBand` sets how forgiving the perfect timing is.
3. `BallTuning.maxKickSpeed`, `maxDragDistance` and `aimTimeScale` set kick power and comfort on a small screen. The button positions are on the `GameInput` object in each scene.
4. `PlayerTuning.runSpeed` and `jumpVelocity` set whether the gap and the wall feel fair.

Selecting the Ball in the Scene view draws gizmos for the reach radius (yellow) and the perfect band (green).

## Test on a phone

- **Android:** File > Build Profiles > Android > Switch Platform. Connect the phone with USB debugging on, then **Build And Run**.
- **iOS:** Switch to iOS, **Build**, open the generated Xcode project, set your signing team, then run it on the device.

Touch drags feel very different from a mouse, so tune the kick on a real phone.

## Project layout

```
Assets/_Game/
  Scripts/
    Input/      GameInput.cs           touch / mouse / keyboard -> game intents (blockable)
    Player/     KidController.cs       walk back/forward, stop, variable jump, coyote time
    Ball/       BallController.cs      physics ball, auto/perfect touches, juggle, kick
                KickAimer.cs           kick-button aim (forward or back) + slow motion
                TrajectoryPreview.cs   dotted arc for the first ~0.5 s
    CameraRig/  CameraFollow2D.cs      the kid kept clear of the left thumb, vertical dead zone, level bounds
    Core/       LevelManager.cs        intro, bell, checkpoints, lose/respawn, pause, stars
                Checkpoint.cs, LoseZone.cs, GoalZone.cs, TimeControl.cs, GameSettings.cs
    Levels/     LevelDefinition.cs, LevelCatalog.cs (ScriptableObjects)
    UI/         LevelHud.cs            grey-box HUD, pause, results, live tuning panel
    Tuning/     BallTuning.cs, PlayerTuning.cs (ScriptableObjects)
    Holiday/    HolidayRunDirector.cs  the endless mode's rules: pace, score, combo, power-ups, revive, days
                RunWorldStreamer.cs    loads and unloads the 23 stage scenes round the kid
                HolidayStages.cs       the stage table (one per story level) and the world's geometry
                BallSmasher.cs, HolidayAtmosphere.cs, RunChunk.cs, RunSolid.cs, RunBreakable.cs, PowerUp.cs
                HolidayRunHud.cs, HolidayRunPanels.cs, HolidayMissions.cs   the run's screen, its pause and results menus, the missions
    Editor/     LevelBuildKit.cs       sprites, assets, gameplay rig, track pieces
                GreyboxLevels.cs       the level layouts
                GeneratedContent.cs    builds every scene + build settings
                HolidayRunBuilder.cs   builds the Holiday Run core scene and its 23 stage scenes
```

## About the camera

The original plan named Cinemachine for the camera. For now the project uses its own `CameraFollow2D`, which already keeps the kid clear of the control buttons with the view ahead of them, a vertical dead zone, level bounds and a snap on respawn. The reason is that I couldn't compile against Cinemachine's API while building this, and a single wrong API call would stop the project from entering Play mode. It's a self-contained swap once the levels are verified in the editor.

## Progression

- **Coins:** collected by the kid or the ball. Bonuses come from perfect touches, new stars, new stickers, and collecting every coin in a level.
- **Stickers:** one is hidden in each level, often high up, so a well-kicked ball can collect it.
- **Stars:** 1 for finishing, 2 for beating the bell, 3 for also hitting the streak target and collecting every coin.
- **Locker Room:** buy and equip ball skins, backpack flags, outfits and ball trails. All of them are drawn in code. Eleven items can't be bought: stickers earn them (below).
- **Stickers:** each story level hides one, themed to the level (a cat on the garden gate, a vending machine, a crab, a tower crane, the school bell...): die-cut vinyl stickers drawn from the game's own models (`tools/blender/sticker_art.py` renders them in the toon look, `sticker_compose.py` cuts them out into `Resources/UI/Stickers`). Most are plain, six are holo (a rainbow sheen sweeps across them), the five chapter finales are gold. The album (`FrontEnd/AlbumScreen`) is a collector's book: the collector track (rewards at 5, 10, 15, 20 and all 23 stickers), and per chapter its progress, its set reward and its stickers; tap one to see it up close with a line about it, or, if it's still missing, a hint about where it hides and a button to play that level. Completing a chapter's set or reaching a count unlocks exclusive Locker Room items (`Cosmetics/StickerRewards`; a celebration the first time, and older saves get what their stickers already earned).
- **Saving:** progress goes to `save.json` in the app's data folder. The **Kick Off** menu has Reset Save Data and Give 1000 Coins for testing.

## Look and sound

All art and audio are generated in code, so the repo has no art or audio files to maintain:

- **Art.** A bright anime look in a real 3D street. The camera is a low perspective camera looking along the street, and play stays on a 2D plane along the footpath, with the house walls behind and the road in front. The ground is 3D from front to back and never breaks: road, kerbs, footpath, cobbles, sand, gravel or grass strips, with side streets and raised zebra crossings running into the distance. Gaps are drain works or flooded trenches in the footpath, marked with cones. Block walls, houses, shops, apartments, warehouses, the school, hedges and utility poles with sagging wires are 3D meshes built in code (`Scripts/World`). They use a cel-shaded toon shader (`Shaders/Toon.shader`) with tileable baked textures and facades, and distance haze fades them into the sky. Trees, bushes, clouds and people are hazed cut-outs that stand in the 3D world. Each chapter has its own layout (suburb, market, beach with the sea to the horizon, city, park). On the beach the tide's wash is the sea running on up the sand, one sheet of the same water with no seam or strip of sand between them, and the beach level that ends at the school ends on the school's own land, the coast turning away behind a sea wall before the gate. The editor bakes everything to `Assets/_Game/Art/Generated` when levels are rebuilt.
- **Animation.** The player is one of six Blender-made kids picked in the player picker (`Core/PlayerRoster`): the high-school boy and girl, Ren and Hana (`tools/blender/teen.py`, exported to `Art/Models/Boy.fbx` and `Girl.fbx`) and four primary-school kids (`tools/blender/primary.py`, `PrimaryBoy`, `PrimaryGirl`, `PrimaryBoy2` and `PrimaryGirl2` in `Art/Models`), posed by code. Other characters are 3D too: one smooth skinned mesh per character (`Presentation/CharacterBody3D`) on a code-animated rig with hips, knees, shoulders and elbows, so joints bend as skin with no seams. They are cel-shaded with an ink outline (`Shaders/ToonCharacter.shader`). Both teens wear the school uniform: a white shirt tucked in under a red striped tie (the boy's with a belt and navy trousers, a red satchel across his chest; the girl's blouse has a navy collar and tucks under a navy pleated skirt, with knee socks and a yellow backpack). The primary-school kids are about five heads tall (1.27 to 1.34 m, against the teens' 1.65 and 1.73 m): the boys wear knee-length shorts (navy or grey) with bare knees and crew socks, the girls a pleated skirt or a pinafore, and each carries a hard school backpack in a colour of their own with a neckerchief or bow at the collar. The clothes follow the body in every pose (`tools/blender/review_poses.py` renders each pose the game uses to check that no bare skin or torn cloth shows). Adults wear long sleeves and trousers. The kid runs, jumps, kicks, lands, celebrates and stumbles, and turns around by spinning through facing the camera. The ball, coins, cars, pipes, signs, posts, swings, the springboard, targets, the dog and the seagull are 3D too.
- **Feel.** Parallax backdrops, particles for every action, screen shake, a slow-motion finish, and the camera zooms out while aiming.
- **Audio.** Synthesized sound effects for every action and a lo-fi music loop per chapter, plus a menu theme.
- **Haptics.** Taptic feedback on iOS (prepared generators; a rigid click when a button goes down and a soft tap when it comes up) and the system click effects on Android 10+, short vibrations before that.
- **Controls and type.** The on-screen buttons are borderless, see-through glass discs with soft white icons, so they never compete with the game. Held, they brighten and shrink slightly with a faint ripple; a soft green halo pulses behind KICK while the ball is in reach. Menu buttons push in the same way. Text uses Lilita One for titles, buttons and numbers and Varela Round for body text (both SIL Open Font License, in `Resources/Fonts`).

## Menus, settings and accessibility

- **Menu:** the launch screen is a live 3D scene (`FrontEnd/MenuStage`, built into the FrontEnd scene by `LevelBuildKit.BuildMenuStage` with the levels' own builders): a stretch of the home street in the game's daylight, real clouds, and the chosen kid doing keepy-uppy (`FrontEnd/MenuKid`) with a ball of a real football's size for them (a size 5 for the teens, a size 4 for the primary kids: smaller than the levels' easy-to-read ball, since the title screen shows the kid close up) while the camera drifts. The KICK OFF logo is built in code (`UI/KickOffLogo`: Lilita One lettering with an extrusion and ink outline by `UI/Kit/UILogoText`, on a turf badge with the centre circle chalked on it). Play (the town map, below), Locker Room (shop; the kid in the street tries items on), Stickers (album), Settings and Credits; the map and album tilt the camera up to the sky. Panels and buttons are clean, slightly see-through white with a thin dark line (`UI/Kit/UIKit`, `UITheme`).
- **Town map:** Play opens a rendered picture of the town (`Resources/UI/TownMap.jpg`, laid out by `Resources/TownMapLayout.json`, read by `Levels/TownMap`) that fills the screen behind the header and the bars, with the six routes from the kid's house to the school drawn over it as coloured lines, every story level a numbered node on its route (stars, a lock, the next one pulsing), the stops between the levels as small markers on the line, and each challenge a gold "!" node beside its route (`FrontEnd/ChapterMapScreen`). It pans and zooms (`UI/Kit/UIMapView`): drag with a finger, pinch with two, the mouse wheel, or the + / - / fit buttons at the right; it zooms to 3x, and the nodes, names, pins and lines grow on screen more slowly than the town as it zooms in, so they come further apart and stay easy to tap; zoomed in, the focused route's stops are named where there is room. The route with the next level is in focus; along the bottom a strip of that route's levels, and a chip for each route to change it. At zoom 1 everything drawn on the picture fits between the header and the strip on any screen from 4:3 to 21:9 (about 0.6 canvas units a picture pixel at 16:9, a quarter bigger than before). The picture, the layout format and the checks (`Tests/Editor/TownMapTests`, `MapViewTests`): [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md).
- **Player:** one of six kids (`Core/PlayerRoster`): the high-school boy and girl, Ren and Hana, and four primary-school kids (Kai, Mia, Leo and Zoe), picked on cards with portraits of the real models, a row for each school (`UI/PlayerPicker`; portraits rendered by `tools/blender/portrait_teen.py` into `Resources/UI`). From the title screen (tap the kid or the player card), in the Locker Room, and in Settings (which shows the chosen kid and opens the picker). It sets `GameSettings.Character`; the menu kid and every level's `CharacterChoice` follow it live, and the menu camera frames each kid by their height. To add a kid: build the model, add a row to `PlayerRoster` and a name to the string tables.
- **Settings:** grouped rows laid out to fit any aspect ratio from 4:3 to 21:9: Audio (music, sound effects), Gameplay (school bell (off = cozy mode), left-handed controls, colour-blind aim colours, vibration, screen shake), Player, Language (English / Español), and reset progress.
- **Tutorial:** short hint cards appear the first time each new mechanic shows up.
- **Developer tools:** the tuning sliders are only in the editor and development builds (Tab, or the Tune button in the HUD).

## Tests

Edit-mode tests live in `Assets/_Game/Tests/Editor/GameLogicTests.cs`. Run them from **Window > General > Test Runner > EditMode**. They check:

- every language has every string, and every level has a translated name,
- the level table (23 story levels, one challenge per chapter, unique ids and scenes),
- the shop table (unique ids, free defaults),
- challenge star thresholds, and that Next level skips challenges,
- generated sound effects and music (no invalid samples, no clipping),
- generated art (solid blocks, seamless ground edges),
- the touch layout on six screen shapes from 4:3 to 21:9, both handednesses and both layouts (`ControlLayoutTests.cs`),
- the town map's picture and layout against the six routes and the level table (`TownMapTests.cs`, `RouteTableTests.cs`),
- the Holiday Run: the stage table and its order, the three layouts of every stage against their fairness rules, the missions, and the stage logic (`HolidayStageTests.cs`, `HolidayPatternsTests.cs`, `GameLogicTests.cs`).

The tests never touch the player's save file. The file is wrapped in `UNITY_INCLUDE_TESTS`, so it compiles to nothing unless the Test Framework is active.

## Release

See [`docs/RELEASE.md`](docs/RELEASE.md) for:

- the business model switch (paid app, or free with a one-time Full Game unlock) and the IAP setup,
- one-click and CI builds (Android AAB and APK, iOS Xcode project) with signing from environment variables,
- privacy answers (no data collected), store listing copy, a screenshot plan and the pre-submission checklist.
