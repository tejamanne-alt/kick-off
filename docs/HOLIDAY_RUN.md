# Holiday Run

The endless mode of Kick Off 2: **the campaign with no destination.** You play exactly as in the story
levels (walk with the arrows, dribble, jump, slide, aim and kick) along one long street that is the whole
story world laid end to end, and nothing ends the run until your balls do.

## The idea

- **The same game as the campaign.** The kid is yours to steer: nothing runs by itself. The ball is the
  real ball (perfect touches, juggles, aimed kicks), the hazards are the story's, a lost ball sends you
  back to the last checkpoint, and there is no bell and no school to reach. What is new is only that the street
  never stops, and a score to beat.
- **One day = one lap of the story.** The street runs from the front door (Home Street) through the
  Market, the Beach, the Underpass and building site, and the Park, to the school gate: 23 stages, one for
  each story level (L01 to L23), in story order, 120 m each. At the gate the day is done (a bonus, a fade)
  and the street starts again at home. Day after day, the loop is the game.
- **Each stage is its level.** The stage for L11 (Boardwalk) is built from the same kit models, hazards,
  street scenery and animals as the story level, with the traits that level introduced: gaps in the
  boardwalk, awnings to slide under, soft sand, gulls, the tide. Crossing from one chapter to the next the
  light, the haze and the music change gradually (the same moods the story chapters use).

## Controls

The campaign's, unchanged: the left thumb walks (the arrows), the right thumb has JUMP and SLIDE stacked at
the edge and KICK beside them (drag from it to aim, release to shoot; a tap is a short pass), and a quick
tap anywhere else touches the ball. The keyboard is the story's too (`A D` or the arrows, `Space`, `S`, `K`,
mouse drag from KICK). See the README for the table, and `GameInput.LayoutOn` and
`Tests/Editor/ControlLayoutTests.cs` for the layout and its guarantees.

## The loop

```
Ready (GET READY ... GO!) -> Running -> last ball lost -> Results -> Revive (coins) -> Running
                              |                              \-> Run again / Home
                              +-> Day done at the gate -> the street starts again
```

- **Balls.** A run starts with 3 balls (`ballsPerRun`; 0 = unlimited). Losing the ball (into a pit or the
  water, off the street, left too far behind, or "Stuck? Back to checkpoint" from the pause menu) costs one
  and sends the kid back to the last checkpoint with the ball, as in a level; the last one ends the run. The
  balls left are the little footballs under the score card. A new day gives back at least two.
- **Checkpoints.** Every stage has one, on the clear ground at its start; it is reached when the kid passes it
  with the ball close by. Stages load and unload as you go, so the checkpoints come and go with them.
- **No walking back into the past.** Streets far behind are gone, so an invisible wall follows the furthest
  point reached, 40 m behind (`walkBackLimit`). The ball passes through it.
- **Revive.** Spend coins (40, then 80, then 120; at most three times a run) to carry on with one more ball
  from the last checkpoint, with a moment of shield. The coins you collected in the run count: they are banked
  as soon as the run ends.
- **Day done.** Reaching the school gate pays 40 coins and 500 points times the day number, plays a fade,
  and the street starts again at the front door. The combo is kept half.

### Scoring

- Points for **new ground** (one per metre, times the multiplier): walking back and forth earns nothing.
- **Coins** are 10 points each (times the multiplier).
- **Multiplier**: it goes up by one for every 6 obstacles passed in a row (max x5) and drops to x1 when a ball
  is lost. Smashing a crate with a kick also counts.
- **Close shaves**: passing an obstacle closer than 0.3 m without touching it (a jump that only just clears
  a wall, a slide that skims a bar) is worth 40 points (times the multiplier), with a chime and a sparkle.
- **Smashes**: a hard kick into a crate, a sandcastle or a stack of cones breaks it, pays its coins and counts
  toward the combo (`BallSmasher` on the ball).

### Power-ups

Found along the street in glowing bubbles. Each is a different colour and has a timer ring on the screen.

| Power-up | Lasts | Does |
|---|---|---|
| Magnet (pink) | 9 s | Pulls every coin within 6 m to the kid |
| Shield (blue) | 15 s | The next ball you lose is free (it still goes back to the checkpoint) |
| Turbo (orange) | 5.5 s | The kid walks 35% faster and the distance points count double |

### Missions

Three at a time from a pool of twelve kinds, each with three tiers (easy, mid, hard) that pay coins. A finished
mission is replaced in the same slot by a kind that is not on the list and not just finished; the tier rises with
how many of that kind have been finished. Progress is saved (`SaveData.holidayMissions`, `holidayMissionTally`) and
shown on the results screen with bars, and the coins go to the wallet when the run is saved.

| Mission | Counts | Targets (easy / mid / hard) | Coins |
|---|---|---|---|
| Run a distance | best single run | 600 / 1400 / 2800 m | 60 / 120 / 240 |
| Collect coins | best single run | 30 / 80 / 160 | 50 / 110 / 220 |
| Reach a stage | best single run | 6 / 12 / 23 | 70 / 140 / 250 |
| Reach a multiplier | best single run | x3 / x4 / x5 | 50 / 90 / 150 |
| Clear obstacles | best single run | 25 / 60 / 120 | 60 / 130 / 240 |
| Slide | in total | 15 / 40 / 100 | 60 / 120 / 220 |
| Double jump | in total | 10 / 30 / 80 | 60 / 120 / 220 |
| Near misses | in total | 3 / 10 / 25 | 70 / 140 / 250 |
| Smash crates and targets | in total | 5 / 15 / 40 | 60 / 120 / 230 |
| Collect power-ups | in total | 3 / 8 / 20 | 60 / 120 / 220 |
| Jump | in total | 40 / 120 / 300 | 50 / 110 / 200 |
| Finish days | in total | 1 / 2 / 4 | 100 / 160 / 250 |

The targets and rewards are first guesses: none are calibrated against real play.

## The world

| Chapter | Stages (story levels) | Lives in the stage |
|---|---|---|
| 1 Home Street | Out the Door, Parked Cars, Up the Hill, Garden Gate, Puddle Lane | kerbs, garden steps, planters, parked cars, awnings, drain works, puddles, a stroller or two |
| 2 Market | Market Morning, First Crossing, Corner Shop, Fruit Stalls, Rush Hour | crates, stall awnings, zebra crossings with traffic, pedestrians, springboards |
| 3 The Beach | Boardwalk, Low Tide, Seagull Bay, Sandcastle Sprint | boardwalk gaps, sandcastles, soft sand, gulls, the tide, springboards |
| 4 Underpass | The Underpass, Building Site, Cranes, Tunnel Run | tunnel lamps, trenches, scaffolds, cranes with pallets, rolling pipes |
| 5 Park & School | Park Gates, Fountain Square, Playground, Duck Pond, The Final Bell | hedges, dogs, fountain jets, swings over the stream, the school gate |

The table with every stage's traits and difficulty (`density`, from 0.28 in the first stage to 1.0 at the
school) is `Holiday/HolidayStages.cs`. The first 22 m of a day and the first 14 m of every stage are empty:
time to get going, and to look around. Every stage carries **three layout variants** of its obstacles and
pick-ups, and one is chosen at random each time the stage loads, so no two days are the same while the
scenery stays put.

## How it is built

```
Scripts/Holiday/
  HolidayStages.cs        the stage table (levels, chapters, traits, difficulty) and the world's geometry
  RunChunk.cs             a stage's root and its layout variants
  RunSolid.cs, RunBreakable.cs   obstacles the director counts (passed, close shave; a smashable crate)
  PowerUp.cs              the magnet, shield and turbo pickups
  RunWorldStreamer.cs     loads the stages near the kid as additive scenes, wakes them one a frame, unloads
                          what is behind
  HolidayRunDirector.cs   the rules: balls, score, combo, power-ups, revive, days, saving
  BallSmasher.cs          on the ball: a hard kick into a crate smashes it
  HolidayAtmosphere.cs    carries the sun, sky and haze from one chapter's mood to the next
  HolidayRunHud.cs        the run's screen: score card, balls left, multiplier, stage ribbon and chapter banner, toasts,
                          power-up timers, the touch buttons (arrows, aim), the day splash
  HolidayRunPanels.cs     the pause and results menus (revive, run again, home, mission bars)
  HolidayMissions.cs      the mission pool and its saved progress
Scripts/FrontEnd/
  TitleScreen.cs          the HOLIDAY RUN button under PLAY (shows the best distance once there is one)
  FrontEndController.cs   OpenHolidayRun()
Scripts/Editor/
  HolidayRunBuilder.cs    builds the core scene and the 23 stage scenes
  HolidayPatterns.cs      what goes where in each stage: three layouts of obstacles, coins and power-ups,
                          and the rules that keep them fair (pure logic, checked at build time and in tests)
  LevelBuildKit.Holiday.cs  the core scene's rig (camera, kid, ball, director, HUD) and the runner's obstacles
  StreetBuilder.Holiday.cs  the street scenery of one stage's stretch (lots fitted between side streets,
                          chapter transitions, poles on one lattice)
Tests/Editor/
  HolidayStageTests.cs, HolidayPatternsTests.cs, GameLogicTests.cs (missions, stage logic),
  ControlLayoutTests.cs
```

### Streaming contract

Why streaming and not one huge scene: the 23 stages hold about 2.8 km of street with its scenery, and the
existing hazards, animals and tides keep their **absolute world coordinates**, so each stage is built where it
finally stands in the world (stage *n* occupies x = 120n to 120n + 120) and never moved. The core scene
`HolidayRun` holds only the kid, ball, camera, sky, director and HUD, with `LevelManager` kept as the host that
the hazards, coins and checkpoints expect (with `endless` on: no goal, no bell, and the last ball ends the run). The stage
scenes `HolidayRun_S01 ... HolidayRun_S23` are loaded additively:

1. **Load** a stage when it begins within 190 m of the kid (`loadAhead`), one at a time.
2. Its root `Stage` is **inactive in the scene file**, so nothing in it has woken. When the scene has arrived
   the streamer picks one of the `RunChunk.variants` at random, then switches the root on: one stage per
   frame at most.
3. **Unload** a stage once it ends more than 80 m behind the kid (`keepBehind`). About three stages exist
   at any time, however long the run.
4. At the start of a run and a new day the kid is frozen (no physics) until the stages around them are on
   (`IsReady`), so they never fall through a world that has not arrived.

The director follows the obstacles through `RunSolid` (the kid is simply blocked by them, as in a level; the
director counts one as passed once the kid is past it, and a close pass as a close shave); anything without a
`RunSolid` is not part of the scoring. Story-mode hazards (`Hazard*`) keep working as they are.
Checkpoints register with the level manager when their stage is switched on and leave when it goes
(`LevelManager.RegisterCheckpoint`), and if the one to go back to is unloaded, the nearest reached one still
standing takes over.

### Tuning

All on `HolidayRunDirector` in the core scene: `ballsPerRun`, `walkBackLimit`, `turboFactor`; `pointsPerCoin`,
`nearMissPoints`, `dayPoints`, `streakPerStep`, `maxMultiplier`, `nearMissGap`, `dayBonusCoins`; `magnetRadius`,
`firstReviveCost`, `maxRevives`; power-up durations in `Duration(kind)`. The kid and the ball are tuned by the
same two assets as the campaign (`PlayerTuning`, `BallTuning`); `LevelManager.maxBallBehindDistance` (16 m in
the core scene) is how far behind the kid the ball may be left. Stage difficulty and traits are in
`HolidayStages.All`; the streaming distances are on `RunWorldStreamer`; the ball smashes with
`BallSmasher.minSpeed`.

### Rebuilding

The editor generates every Holiday Run scene (like the story levels); edits made in those scenes are
overwritten. Change the stage table, the patterns or the rig and rebuild:

- **Kick Off > Rebuild All Levels** also rebuilds the Holiday Run (it is part of the generated content;
  `GeneratedContent.Version` is 51 for it), and it runs by itself on the first open.
- **Kick Off > Rebuild Holiday Run** rebuilds only the Holiday Run (its core scene and 23 stages) and swaps its
  entries in the build settings, leaving the levels and the menu alone.
- The scenes are `Assets/_Game/Scenes/Holiday/HolidayRun.unity` (the core) and `HolidayRun_S01..S23.unity`, all in
  the build settings after the story levels. If a build lacks them, the title button logs an error and stays on
  the menu.
- The first open builds 24 more scenes than before; expect a few extra minutes (not measured).

### How a stage is made

A stage scene has one root, `Stage`, **inactive in the file**, with a `RunChunk` and, under it: the ground (split at
the gaps), the 3D street, the scenery with its animals, the stage's furniture (tunnel, crossings, fountains, beats
of pedestrians and dogs, gulls, the tide, cranes), and three inactive layouts `Layout_A` to `Layout_C` of obstacles,
coins and power-ups. `HolidayPatterns` decides what goes where, once, the same every time it is asked.

What the kid can do sets the sizes: a single jump clears about 1.3 m and spans about 5 m of ground at 9 m/s, a
double jump clears about 2.1 m, a slide lasts 0.7 s and passes under 0.85 m.

- **Things in the way**: low (0.3 to 0.5 m: kerbs, steps, borders, sometimes a hurdle run of two or three), mid
  (0.6 to 1.0 m), tall (1.5 to 1.9 m, a double jump: rare and always with a coin arc over it), parked cars,
  barriers to slide under (chapter by chapter from the Barriers kit), gaps (plain 2.0 to 3.4 m, wide 4.0 to 5.2 m
  where the density is over 0.5), puddles and soft sand that slow you down, trampolines, rolling pipes in the
  tunnel, crates and sandcastles a kicked ball smashes.
- **Spacing**: between two demands there are 28 m at density 0.3 down to 11 m at density 1, and at least 12 m
  between two different kinds of demand (more after a slide, a wide gap or a trampoline); nothing within 6 m of a
  power-up. Two stages could not fit all their mandatory traits at that spacing, so it is tightened by 40% toward
  the minimums there.
- **Three layouts per stage** hold the same kinds and counts of obstacles (so they are as hard as each other) in
  different places, orders, sizes, looks, coins and power-ups. Power-ups appear in 29 of the 69 layouts.
- **Scenery as scenery**: crossings stay on the green man (traffic waits at the line), gulls fly high, the tide
  never reaches the footpath, cranes carry their load out of reach, swings and the pond are clearings. Moving or
  swinging platforms and passing traffic were left out on purpose: they would need runtime fairness work.
- **Seams**: the ground colliders overlap their neighbours by a metre, the street slabs meet exactly at the stage
  ends (a cap is added only where the chapter changes), poles stand on one 21 m lattice, lots are fitted to the run
  between side streets, every urban stage but the last ends on a 7 m cross street, and at chapter changes the lots
  on either side of the seam take on the neighbour's look. The sea, the headlands, the cranes and the far fields
  are in the core scene, so none of them pops with streaming.

## Save data

`SaveData` gained `holidayBestScore`, `holidayBestDistance`, `holidayRuns`, `holidayDays`,
`holidayTotalDistance` and `holidayMissions` (a list of `HolidayMissionRecord`). Older saves load with
zeros and no missions. Coins earned in a run go into the same wallet as the story mode.

## Store

The lap runs through every chapter, so where chapters are sold (`Monetization.RequireUnlock`, off by default) the Holiday Run is part of the full game: its title button opens the unlock panel first and starts the run once the game is bought. Nothing changes while `RequireUnlock` is off. A free taste (say, a lap that ends at the end of chapter 1) would be a different design: the director would need to end the day at the last free stage.

## Analytics

`holiday_run_start`, `holiday_run_end` (score, distance, coins, stage, day, reason, revives, close shaves) and
`holiday_revive`. The streamed stage loads are not levels: they raise no `level_start` events.

## What has been checked, and what has not

Everything here was written and checked **without Unity or a device**: the C# compiles against the Unity
reference DLLs in four configurations (legacy input, Input System, editor, tests); pure logic ran for real under
Mono (the stage table, all 69 pattern layouts against their fairness rules, the missions, the HUD and menus against
a fake Unity with a random-event fuzz, the layout arithmetic); the HUD's layout was rendered as mock-ups at 4:3,
16:9 and 21:9 in both languages; and the character poses were rendered in Blender. No scene has been generated,
opened or played, and no NUnit test has been run in the Test Runner. First thing in the editor:

1. Open the project and let the generated content rebuild (Kick Off > Rebuild All Levels); read the Console for
   anything red or any "Holiday Run layout" warning. Shaders have never been compiled either (see PROGRESS.md
   "After Phase 8").
2. Run the edit-mode tests (Window > General > Test Runner).
3. Title screen > **Holiday Run**. Check: GET READY then GO once; the kid stays on the ground at the start; the
   first stage and the next two stream in without a hitch; the stage ribbon names each stage and the chapter banner
   each chapter.
4. Get to the school gate (the street is 2.7 km: about 11 minutes at the campaign's pace, so for a quick check
   drag the Kid object far along x in the Scene view while playing): the fade, the second day (the DAY 2 splash), no
   stage from day 1 left standing, the kid and the ball back at the front door.
5. Lose the ball on purpose (walk into a pit, or leave it behind): you come back at the checkpoint with the ball,
   a football under the score card goes dim, and "Stuck? Back to checkpoint" in the pause menu does the same. Lose
   the third: the results, revive (it is paid with the coins you just collected), run again, quit to the menu from
   the pause menu (the coins are kept). Walk back past the wall 40 m behind the furthest point: it stops you.
6. Kick hard at a crate and a sandcastle (they smash for coins); collect each power-up; check the missions after a run.
7. On a phone: the arrows under the left thumb, JUMP at the bottom of the stack at the right edge with SLIDE straight
   above it and KICK beside them, all the same size and see-through, none hard to reach, and the aim drag from KICK
   working with the aim bar showing.
8. Profile a long run: only about three stages in memory, and no frame spike when a stage wakes.

Assumptions in the code that only a run can confirm:

- `StaticBatcher` on a stage's street combines it when the stage is switched on, and that does not cost a visible
  hitch each time (if it does, bake the stage's street instead).
- The streamer calls `RunChunk.Prepare` while a stage is still inactive and then switches it on, and the hazards
  (pedestrians, dogs, gulls, fountains, springboards, the tide, slow zones, tunnel darkness) start fine without
  anything from outside their stage.
- The rolling pipes (made at run time by `PipeSpawner` from a template carrying a `RunSolid`) shove the kid and the
  ball as in the campaign and count as passed once the kid is beyond them; a rolling pipe is the only obstacle that moves.
- The obstacles were laid out as things to get past (a wall to jump, a bar to slide under, a pit to cross); the ball
  has to get past them too, by a kick over or round them, as in a level. How that plays with the ball (walls the ball
  cannot be carried over, a ball that ends up stuck) is unseen: the pause menu's "Back to checkpoint" is the way out.
- The crossing's "stopped on green" trick (`greenTime` 100000, `phaseOffset` 95000, trigger off) behaves as the
  fields' names say.
- The first-stage banner (the HUD, a moment after GO), toasts above the kid (clear of the KICK button), the radial
  ring sprites and the best-fit text are as the mock-ups show.
- Kit models missing from the project fall back to the old procedural builders; how the transitions, the themed lots
  and the tunnel look has not been seen.
