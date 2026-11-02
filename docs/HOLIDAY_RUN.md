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
  water, off the street, left too far behind, or "Back to checkpoint" from the pause menu (for a stuck ball)) costs one
  and sends the kid back to the last checkpoint with the ball, as in a level; the last one ends the run. The
  balls left are the little footballs under the score card. A new day gives back at least two.
- **Checkpoints.** Every stage has one, on the clear ground at its start; it is reached when the kid passes it
  with the ball close by. Stages load and unload as you go, so the checkpoints come and go with them.
- **No walking back into the past.** Streets far behind are gone, so an invisible wall follows the furthest
  point reached, 40 m behind (`walkBackLimit`), and never ahead of the checkpoint a lost ball goes back to, so the
  kid can't be put down behind it. The ball passes through it.
- **Revive.** Spend coins (40, then 80, then 120; at most three times a run) to carry on with one more ball
  from the last checkpoint, with a moment of shield. The coins you collected in the run count: they are banked
  as soon as the run ends.
- **Day done.** Reaching the school gate pays 40 coins and 500 points times the day number, plays a fade,
  and the street starts again at the front door. The combo is kept half.

### Scoring

- Points for **new ground** (one per metre, times the multiplier): walking back and forth earns nothing.
- **Coins** are 10 points each (times the multiplier); a star coin is worth five.
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
| Collect coins | best single run | 70 / 180 / 400 | 50 / 110 / 220 |
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

Every stage also has, whatever its traits: something to smash (crates, a sandcastle on the beach, cones on the site, now and then
a pile of crates), people strolling and dogs, floating targets (balloons, paper lanterns, beach balls) that burst into coins when
the ball flies into them, a trail of coins, and a middle checkpoint. The beach has more gulls than the story's.

The table with every stage's traits and difficulty (`density`, from 0.28 in the first stage to 1.0 at the
school) is `Holiday/HolidayStages.cs`. The first 22 m of a day, the first 14 m of every stage and the last 8 m have
no obstacles, street life or targets in them (only the trail of coins, and the first checkpoint 8 m in): time to get going, and to
look around. Every stage carries **three layout variants** of its obstacles and pick-ups, and one is chosen at random each time the
stage loads, so no two days are the same while the scenery stays put.

## How it is built

```
Scripts/Holiday/
  HolidayStages.cs        the stage table (levels, chapters, traits, difficulty) and the world's geometry
  RunChunk.cs             a stage's root and its layout variants
  JumpReach.cs            what the kid can reach (single, double, trampoline, slide), replayed from KidController, and the
                          limits for gaps and walls that follow from it; pure arithmetic, no Unity objects
  RunSolid.cs, RunBreakable.cs   obstacles the director counts (passed, close shave); a smashable crate; or (floating)
                          a balloon, lantern or beach ball that is no obstacle and bursts when the ball flies into it
  PowerUp.cs              the magnet, shield and turbo pickups
  RunWorldStreamer.cs     loads the stages near the kid as additive scenes, wakes them one a frame, unloads
                          what is behind
  HolidayRunDirector.cs   the rules: balls, score, combo, power-ups, revive, days, saving
  BallSmasher.cs          on the ball: a hard kick into a crate smashes it; a ball flying through a balloon bursts it
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
  HolidayPatterns.cs      what goes where in each stage: three layouts of obstacles, street life, targets, coins and
                          power-ups, and the rules that keep them fair (pure logic, checked at build time and in tests)
  LevelFeasibility.cs     the build-time check that a level or stage can be done: holes, steps, walls, platforms, barriers
                          and roofs against JumpReach (the track builder records, Finish() warns; also pure logic)
  LevelBuildKit.Feasibility.cs  what the track builder records for the check (Audit), and the PlayerTuning check
  LevelBuildKit.Holiday.cs  the core scene's rig (camera, kid, ball, director, HUD) and the runner's obstacles, targets and stars
  StreetBuilder.Holiday.cs  the street scenery of one stage's stretch (lots fitted between side streets,
                          chapter transitions, poles on one lattice)
Tests/Editor/
  HolidayStageTests.cs, HolidayPatternsTests.cs, JumpReachTests.cs, LevelFeasibilityTests.cs,
  GameLogicTests.cs (missions, stage logic), ControlLayoutTests.cs
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
`HolidayStages.All`; the streaming distances are on `RunWorldStreamer`; the ball smashes a crate with
`BallSmasher.minSpeed` (6 m/s) and bursts a balloon with that target's own `RunBreakable.minSpeed` (2.5 m/s, a ball flying at it).
The reach of the jump, and so every limit on a gap or a wall, comes from `JumpReach.Defaults` (see below): retune `PlayerTuning` and
that has to follow.

### Rebuilding

The editor generates every Holiday Run scene (like the story levels); edits made in those scenes are
overwritten. Change the stage table, the patterns or the rig and rebuild:

- **Kick Off > Rebuild All Levels** also rebuilds the Holiday Run (it is part of the generated content;
  `GeneratedContent.Version` is 52 for it), and it runs by itself on the first open.
- **Kick Off > Rebuild Holiday Run** rebuilds only the Holiday Run (its core scene and 23 stages) and swaps its
  entries in the build settings, leaving the levels and the menu alone.
- The scenes are `Assets/_Game/Scenes/Holiday/HolidayRun.unity` (the core) and `HolidayRun_S01..S23.unity`, all in
  the build settings after the story levels. If a build lacks them, the title button logs an error and stays on
  the menu.
- The first open builds 24 more scenes than before; expect a few extra minutes (not measured).

### How a stage is made

A stage scene has one root, `Stage`, **inactive in the file**, with a `RunChunk` and, under it: the ground (split at
the gaps), the 3D street, the scenery with its animals, the stage's furniture (tunnel, crossings, fountains, gulls, the tide,
cranes, a checkpoint in the middle), and three inactive layouts `Layout_A` to `Layout_C` of obstacles, things to smash, beats of
walkers and dogs, floating targets, coins and power-ups. `HolidayPatterns` decides what goes where, once, the same every time
it is asked.

**What the kid can do sets the sizes, and it is worked out, not guessed.** The kid walks at 4.2 m/s (`PlayerTuning.runSpeed`;
the turbo, x1.35, only adds reach, so everything is designed for walking). `Holiday/JumpReach.cs` replays
`KidController`'s jump one physics step at a time (gravity 3 x 9.81, jump 9 m/s, air jump 7 m/s, fall gravity x1.4, the
trampoline's throw 13 m/s, step 1/60 s) and the limits follow from the flights:

| What | Flight / limit at 4.2 m/s |
|---|---|
| single jump | flies 2.3 m, peaks 1.30 m (3.1 m at turbo speed) |
| double jump, second press at the top | flies 3.6 m, peaks 2.07 m (4.9 m at turbo speed) |
| longest flight (second press as late as the game allows) | 4.1 m, but only 1.3 m high |
| **plain gap** (one jump) | made 1.4 to 1.9 m, never over **2.0** (the flight less 0.3 m: an early take-off, the feet box at the edge) |
| **wide gap** (a double jump) | made 2.7 to 3.1 m, never over **3.2** (the flight less 0.42 m), never under 2.6 |
| round every gap | 6 m of clear ground before it (run-up, room to kick the ball across), 4 m after (landing, room to fetch the ball), no wall, beat or power-up in either; the ball is chipped 3 to 6 m, so 3.2 m is fine for it |
| low / mid / tall / highest wall | 0.5 / 1.0 (a single jump) / 1.7 (a double jump) / **1.8** m; a parked car (1.55 m) is climbed in two hops, a pile of crates is 1.42 m |
| barrier to slide under | 0.85 m clear (the sliding kid is 0.5 m); up to 4.4 m long (the slide itself carries 2.9 m, the low shuffle under a longer barrier the rest) |
| underpass deck | 3.8 m; the head of a double jump is at 3.27 m. Rolling pipes are 0.9 m across |
| coins | up to 3.5 m (a double jump's head), up to 5 m on a trampoline's throw |
| trampoline throw | peaks 2.76 m, flies 3.4 m (4.6 m with the air jump it gives back), so 4.8 m of the street after the pad are kept clear and under a ceiling of 4.7 m |

`JumpReachTests` compares `JumpReach.Defaults` with `PlayerTuning`'s real defaults, the engine's gravity, the physics step and the
trampoline, and pins the flights to the figures above: retune the jump and a test fails (and `LevelBuildKit.CheckJumpTuning`
warns when the asset the scenes use differs), instead of every trench quietly becoming impossible. `Validate` fails any layout with
a gap over its limit, a wall too high, too little run-up or landing, or street life, a power-up or a coin trail over a gap or in a solid.

- **Things in the way**: low (0.3 to 0.5 m: kerbs, steps, borders, sometimes a hurdle run of two or three 8 to 9.5 m apart),
  mid (0.6 to 1.0 m), tall (1.5 to 1.7 m, a double jump: rare and always with a coin arc over it), parked cars, barriers to slide
  under (chapter by chapter from the Barriers kit), gaps, puddles and soft sand that slow you down, trampolines, rolling pipes in
  the tunnel.
- **Things to smash** (`RunBreakable`, a hard kick breaks them for coins): a crate, a sandcastle on the beach, a stack of cones on the
  site (every other one) in every stage, and now and then a pile of two crates and one on top (a big sandcastle on the beach, 1.42 m:
  too high for a single jump, so a double jump or a hard kick). No more than three single ones and one pile in a stage, and they are as fair as a wall of
  their size: the kid goes over them, the ball is chipped over or kicked through.
- **Floating targets** (`RunBreakable` with `floating`): 2 to 4 per stage, balloons at home and on the site, paper lanterns in the
  market and the park, beach balls on the beach, hanging 2.3 to 3.4 m up in the open stretches (4 m from a gap, never in the tunnel or
  over a crossing). They are triggers: the kid passes through them, the director does not count them as obstacles, and a ball flying
  at 2.5 m/s or more through one (a chip, a kick at it, a trampoline throw) bursts it for 5 coins, "Smash!", and flies on.
- **Street life**: beats of walkers (`Pedestrian`) and dogs (`Dog`) in the layouts, in different places in each: 1 to 2 at the lowest
  density, 3 to 4 at the highest; the first is a walker and the second a dog, so every stage with two beats or more has both (the
  park's stages start with a dog; the stages that have Pedestrians or Dogs as a trait always have that kind). A beat is 4.5 to 7 m long on open ground 1.5 m clear of every solid, more than 6 m before a gap and 4 m after it, off a
  trampoline's throw and away from the middle checkpoint. The walkers probe the footpath themselves and stop short of holes, walls and checkpoints.
  Gulls on every beach stage (3, or 5 in Seagull Bay), swooping 3.0 to 3.6 m up, so they clip a high lob or a shot at a balloon and
  never a ball rolling along the ground. Cats on the garden walls, pigeons, crabs, squirrels, ducks and the flocks crossing the sky
  (now over every stage) are the street builder's scenery.
- **Coins**: a trail every 1.6 to 2.4 m in gentle waves (0.5 to 1.1 m up) from the start of the stage to its end between everything
  else; an arc of coins along the real flight over every wall and gap (a single jump's path, a double jump's for the tall things,
  the stacks and the wide gaps), a row at 0.4 m under every barrier, on the slow ground and on top of the broad walls, coins on a
  car's bonnet and roof, an arc up each trampoline's throw with a star at the top of it. None hangs in a solid, and none low over a
  gap (the arc over it is 0.95 m and up there). A **star** is the Animals kit's star at 1.7 times the size, worth five coins,
  where only a double jump or a throw gets to; one **bonus detour** in most layouts is a high arc along a double jump with a star
  at the top (nothing else is in the way). A broken crate pays 3 coins, a pile 6, a balloon 5. About 70 coins a stage (the old
  stages had 29), so the **Collect coins** mission was raised to 70 / 180 / 400.
- **Power-ups**: every layout of every second stage (the first, the third...) has one, so there is one in any two consecutive
  stages whichever layouts load; the others have one about one time in two. A shield when a gap is coming within 30 m, else a magnet
  or a turbo, 1.0 to 1.6 m up, 3 m from any obstacle.
- **A checkpoint in the middle**: besides the one 8 m in, a flag near the middle of the open ground (with 4 m clear before it
  and 6 m after: the kid is put down there with the ball a metre ahead), so a lost ball costs half a stage of walking, not a whole
  one. A stage too full to spare the ground goes without (Tunnel Run).
- **Spacing for walking**: the player sets the pace, so spacing is about clutter and the ball, not reaction time. Between two demands
  there are 20 m at density 0.3 down to 9 m at density 1, at least 10 m between two different kinds (and more after a slide or a
  pipe lane), and a stage has 5 to 9 demands (gaps and obstacles; 4 in the underpass stages, which have the tunnel as well) with
  something on every stretch: no 25 m of open ground is bare. Where a stage cannot fit all its traits at that spacing it is
  tightened toward the minimums (one stage in the lap).
- **Three layouts per stage** hold the same kinds and counts of obstacles, things to smash, beats and targets (so they are as hard
  as each other) in different places, orders, sizes, looks, coins and power-ups. Power-ups are in 47 of the 69 layouts.
- **Scenery as scenery**: crossings stay on the green man (traffic waits at the line), the tide never reaches the footpath, cranes
  carry their load out of reach (5 m, above even a trampoline throw), swings and the pond are clearings. Left out on purpose:
  moving or swinging platforms as bridges (no gap needs one), the crossing's red man and the tide as real hazards (they would be
  fair in manual play, the kid waits for the green man or the low water, but a lost ball goes back to a checkpoint up to half a
  stage away and none of it could be run), and a ledge of crates for a detour.
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
Mono (the stage table, all 69 pattern layouts against their fairness rules and the feasibility check, the pure edit-mode
tests with a work-alike NUnit whose asserts really fail, the 29 story layouts through a recording stand-in for the track builder,
the missions, the HUD and menus against a fake Unity with a random-event fuzz, the layout arithmetic); the HUD's layout was
rendered as mock-ups at 4:3, 16:9 and 21:9 in both languages; and the character poses were rendered in Blender. No scene has been
generated, opened or played, and no NUnit test has been run in the Test Runner (the two that need a running Unity, the
`PlayerTuning` defaults and the trampoline's launch, could not run at all). The jump reach is a replay of `KidController`
and the physics step, not a measurement: nothing says a thumb on a phone takes a 2.0 m trench as comfortably as the model does.
First thing in the editor:

1. Open the project and let the generated content rebuild (Kick Off > Rebuild All Levels); read the Console for
   anything red, any "Holiday Run layout" warning, and any "can't be done" warning (a pit, step, wall, barrier or roof
   that the feasibility check says the kid cannot get past; there should be none) or "PlayerTuning asset differs" warning.
   Shaders have never been compiled either (see PROGRESS.md "After Phase 8").
2. Run the edit-mode tests (Window > General > Test Runner).
3. Title screen > **Holiday Run**. Check: GET READY then GO once; the kid stays on the ground at the start; the
   first stage and the next two stream in without a hitch; the stage ribbon names each stage and the chapter banner
   each chapter.
4. Get to the school gate (the street is 2.7 km: about 11 minutes at the campaign's pace, so for a quick check
   drag the Kid object far along x in the Scene view while playing): the fade, the second day (the DAY 2 splash), no
   stage from day 1 left standing, the kid and the ball back at the front door.
5. Lose the ball on purpose (walk into a pit, or leave it behind): you come back at the checkpoint with the ball,
   a football under the score card goes dim, and "Back to checkpoint" in the pause menu does the same. Lose
   the third: the results, revive (it is paid with the coins you just collected), run again, quit to the menu from
   the pause menu (the coins are kept). Walk back past the wall 40 m behind the furthest point: it stops you.
6. Kick hard at a crate and a sandcastle (they smash for coins); lob the ball at a balloon, a lantern and a beach ball (they
   burst for 5 coins and the ball flies on; the kid walks through them); collect each power-up and a star; walk through the
   trail of coins; check the missions after a run. Try the trenches at the walking pace: a 1.9 m one should take a single
   jump with room to spare, a 3.1 m one a double jump; if they feel tight, `JumpReach.PlainSlack` and `WideSlack` are the knobs.
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
- A balloon is a trigger collider with a `RunBreakable` (`floating`): Unity delivers `OnTriggerEnter2D` to the ball's
  `BallSmasher` when its collider enters it (the ball has a Rigidbody2D, the balloon none), and the kid's capsule, which
  passes through, does nothing. Its bobbing (`RunBreakable.Update`) moves a plain transform.
- The star coin is the Animals kit's `Star` model on a `Pickups.Coin` with `value` 5, spun like a coin; `LevelManager` counts
  the value, and the magnet pulls it like any coin.
- The second checkpoint registers with the level manager when its layout is switched on, like the first (`Checkpoint.OnEnable`).
- Beats of walkers and dogs are built into the layouts, not the stage (so each layout has its own); `Pedestrian.ClaimLane`
  (which the dogs use for their patch too) only runs while a layout is active.
- The obstacles were laid out as things to get past (a wall to jump, a bar to slide under, a pit to cross); the ball
  has to get past them too, by a kick over or round them, as in a level. How that plays with the ball (walls the ball
  cannot be carried over, a ball that ends up stuck) is unseen: the pause menu's "Back to checkpoint" is the way out.
- The crossing's "stopped on green" trick (`greenTime` 100000, `phaseOffset` 95000, trigger off) behaves as the
  fields' names say.
- The first-stage banner (the HUD, a moment after GO), toasts above the kid (clear of the KICK button), the radial
  ring sprites and the best-fit text are as the mock-ups show.
- Kit models missing from the project fall back to the old procedural builders; how the transitions, the themed lots
  and the tunnel look has not been seen.
