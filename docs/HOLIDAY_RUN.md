# Holiday Run

The endless mode of Kick Off 2, in the spirit of Temple Run and Subway Surfers: the kid runs by
themselves along one long street that is the whole story world laid end to end, and you only
decide **when to jump, slide and kick**. Nothing is a level to beat; the run goes on until you
hit something.

## The idea

- **One day = one lap of the story.** The street runs from the front door (Home Street) through the
  Market, the Beach, the Underpass and building site, and the Park, to the school gate: 23 stages, one for
  each story level (L01 to L23), in story order, 120 m each. At the gate the day is done (a bonus, a
  fade) and the next day begins again at home, **faster and busier**. Day after day, the loop is the game.
- **Each stage is its level.** The stage for L11 (Beach Walk) is built from the same kit models, hazards,
  street scenery and animals as the story level, with the traits that level introduced: gaps in the
  boardwalk, awnings to slide under, soft sand, gulls, the tide. Crossing from one chapter to the next the
  light, the haze and the music change gradually (the same moods the story chapters use).
- **Simple controls, deep rhythm.** JUMP, double JUMP, SLIDE and KICK (see Controls). Running faster
  means less time to read the street, and the obstacles come in combinations that are only fair when you
  chain the right moves.

## Controls

The runner layout puts the thumbs on different jobs, since the kid runs by themselves and there are no
walking arrows to look after:

| Action | Phone | Keyboard |
|---|---|---|
| Jump (hold = higher), again in the air = double jump | JUMP (right thumb, bottom-right corner) or swipe up | `Space` / `W` / `↑` |
| Slide under things | SLIDE (left thumb, bottom-left corner) or swipe down | `S` / `↓` |
| Kick: shoot the ball ahead to smash crates and targets | KICK (right thumb, above-left of JUMP), a press | `K` |
| Pause | Pause button | `Esc` / `P` |

Left-handed mode mirrors the layout. See `GameInput.LayoutOn` for the geometry and
`Tests/Editor/ControlLayoutTests.cs` for the guarantees (round, large, well apart, on every landscape
shape).

## The loop

```
Ready (GET READY ... GO!) -> Running -> Crashed -> Results -> Revive (coins)  -> Running
                              |                         \-> Run again / Home
                              +-> Day done at the gate -> next day (faster)
```

- **Pace.** Day 1 starts at 6.5 m/s and ends at 11 m/s at the school gate; every further day starts and
  ends 1 m/s faster, up to 10 and 14 m/s. The pace follows a smooth curve along the lap.
- **Crash.** Hitting something head-on ends the run (landing on top of it, or sliding under it, is fine).
  Falling in a pit or the sea is also a crash. A crash bonks the kid back and shakes the screen, then
  the results show.
- **Revive.** Spend coins (40, then 80, then 120; at most three times a run) to carry on from just past the
  thing you hit, with a moment of shield. The coins you collected in the run count: they are banked as soon
  as the run ends.
- **Day done.** Reaching the school gate pays 40 coins and 500 points times the day number, plays a fade,
  and starts the next day at the front door at the new pace. The combo is kept half.

### Scoring

- Points for **distance** (one per metre), times the multiplier.
- **Coins** are 10 points each (times the multiplier).
- **Multiplier**: it goes up by one for every 6 obstacles cleared in a row (max x5) and drops to x1 on a crash.
  Smashing a crate with the ball also counts.
- **Near misses**: passing an obstacle closer than 0.3 m without touching it is worth 40 points (times the
  multiplier), with a small flourish.
- **Smashes**: kicking a crate or a target breaks it, pays its coins and counts toward the combo.

### Power-ups

Found along the street in glowing bubbles. Each is a different colour and has a timer ring on the screen.

| Power-up | Lasts | Does |
|---|---|---|
| Magnet (pink) | 9 s | Pulls every coin within 6 m to the kid |
| Shield (blue) | 15 s | Takes one hit: the thing is knocked out of the way and you carry on with a moment of invulnerability |
| Turbo (orange) | 5.5 s | 40% faster, smashes through everything in the way, doubles points |

### The ball

On the run the ball cannot be dribbled by hand: it is carried just ahead of the feet, hopping with the stride,
and a **KICK** shoots it forward in an arc. It smashes crates and targets (and passes through the burst with
most of its speed), bounces off anything else, and is called back to the feet after about a second, ready for
the next kick. While carried it is a trigger, so it collects coins and pick-ups it touches and can never be
knocked into a pit.

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
  RunMarkers.cs           RunChunk (a stage's root and layout variants), RunSolid / RunBreakable (obstacles
                          the director counts), PowerUp
  RunWorldStreamer.cs     loads the stages near the kid as additive scenes, wakes them one a frame, unloads
                          what is behind
  HolidayRunDirector.cs   the rules: pace, score, combo, power-ups, crash, revive, days, saving
  EndlessBall.cs          the ball on the run (carried, shot, recalled)
  HolidayAtmosphere.cs    carries the sun, sky and haze from one chapter's mood to the next
  HolidayRunHud.cs        the run's screen: score card, multiplier, stage ribbon and chapter banner, toasts,
                          power-up timers, the touch buttons, the day splash
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
the hazards and coins expect (with `endless` on: losing the ball is a crash, not a respawn). The stage
scenes `HolidayRun_S01 ... HolidayRun_S23` are loaded additively:

1. **Load** a stage when it begins within 190 m of the kid (`loadAhead`), one at a time.
2. Its root `Stage` is **inactive in the scene file**, so nothing in it has woken. When the scene has arrived
   the streamer picks one of the `RunChunk.variants` at random, then switches the root on: one stage per
   frame at most.
3. **Unload** a stage once it ends more than 80 m behind the kid (`keepBehind`). About three stages exist
   at any time, however long the run.
4. At the start of a run and a new day the kid is frozen (no physics) until the stages around them are on
   (`IsReady`), so they never fall through a world that has not arrived.

The director adds itself to the obstacles through `RunSolid` (an obstacle's colliders count a head-on touch as
a crash, a pass as cleared, a close pass as a near miss); anything without a `RunSolid` is not part of the
scoring. Story-mode hazards (`Hazard*`) keep working as they are.

### Tuning

All on `HolidayRunDirector` in the core scene: `firstDaySpeed`, `firstDayTopSpeed`, `perDayGain`,
`startSpeedCap`, `topSpeedCap`, `acceleration`, `turboFactor`; `pointsPerCoin`, `nearMissPoints`, `dayPoints`,
`streakPerStep`, `maxMultiplier`, `nearMissGap`, `dayBonusCoins`; `magnetRadius`, `firstReviveCost`, `maxRevives`;
power-up durations in `Duration(kind)`. Stage difficulty and traits are in `HolidayStages.All`; the streaming
distances are on `RunWorldStreamer`; the ball is on `EndlessBall` (`kickSpeed`, `kickLift`, `flightTime`,
`lead`, `hop`).

### Rebuilding

The editor generates every Holiday Run scene (like the story levels); edits made in those scenes are
overwritten. Change the stage table, the patterns or the rig and rebuild:

- **Kick Off > Rebuild All Levels** also rebuilds the Holiday Run (it is part of the generated content;
  `GeneratedContent.Version` is 49 for it), and it runs by itself on the first open.
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

## Analytics

`holiday_run_start`, `holiday_run_end` (score, distance, coins, stage, day, reason, revives, near misses) and
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
4. Run to the school gate (set `firstDaySpeed` high on the director to get there quickly): the fade, the second day
   (faster, the DAY 2 splash), no stage from day 1 left standing.
5. Crash on purpose: the results, revive (it is paid with the coins you just collected), run again, quit to the menu
   from the pause menu (the coins are kept).
6. Kick at a crate; collect each power-up; check the missions after a run.
7. On a phone: JUMP under the right thumb, SLIDE under the left, KICK above-left of JUMP, none hard to reach.
8. Profile a long run: only about three stages in memory, and no frame spike when a stage wakes.

Assumptions in the code that only a run can confirm:

- `StaticBatcher` on a stage's street combines it when the stage is switched on, and that does not cost a visible
  hitch each time (if it does, bake the stage's street instead).
- The streamer calls `RunChunk.Prepare` while a stage is still inactive and then switches it on, and the hazards
  (pedestrians, dogs, gulls, fountains, springboards, the tide, slow zones, tunnel darkness) start fine without
  anything from outside their stage.
- The rolling pipes (made at run time by `PipeSpawner` from a template carrying a `RunSolid`) crash the kid when
  hit head-on and score when passed; a rolling pipe is the only obstacle that moves.
- The crossing's "stopped on green" trick (`greenTime` 100000, `phaseOffset` 95000, trigger off) behaves as the
  fields' names say.
- The first-stage banner (the HUD, a moment after GO), toasts above the kid (clear of the KICK button), the radial
  ring sprites and the best-fit text are as the mock-ups show.
- Kit models missing from the project fall back to the old procedural builders; how the transitions, the themed lots
  and the tunnel look has not been seen.
