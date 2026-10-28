# Dribble To School

A cozy, hand-drawn soccer side-scroller for iOS and Android, built in Unity 6 (2D).
The full game brief is in [`GAME_PROMPT.md`](GAME_PROMPT.md).

## Status

All eight phases of the build plan are done (see [`PROGRESS.md`](PROGRESS.md)):

- **Gameplay:** core dribbling and kicking, level flow, 13 hazard types, and 23 story levels across 5 chapters plus 5 ball-skill challenges.
- **Progression:** coins, stickers, saving, the Locker Room shop and the chapter map.
- **Presentation:** procedural storybook art, animation, FX, music and sound effects, and haptics.
- **Menus and options:** settings, localization (English and Spanish), tutorial hints and accessibility options.
- **Release setup:** store and unlock, local analytics, and build scripts.

The next step is playtesting on real devices.

## Open the project

1. Install **Unity 6** (6000.0 LTS or newer) with **iOS Build Support** and/or **Android Build Support** from Unity Hub.
2. In Unity Hub choose **Add > Add project from disk** and select this folder. If Hub asks about the editor version, pick any Unity 6 version you have installed.
3. On the first open, Unity imports packages. If it asks to **enable the new Input System backend**, click **Yes** (the editor restarts). The code works with either input backend.
4. Once importing finishes, an editor script generates the menu, every level scene and the shop items, then opens the **FrontEnd** menu scene. It runs again automatically whenever the generated content is out of date. You can also run it from **Dribble To School > Rebuild All Levels**.
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

**Ball-skill challenges** are optional. There's one per chapter, unlocked by finishing the chapter's first level:

| Challenge | Type | Stars |
|---|---|---|
| C01 Keepy-Uppy | Juggling (45 s) | 5 / 10 / 15 juggles |
| C02 Window Shopping | Accuracy (60 s) | 3 / 5 / 7 targets |
| C03 Beach Slalom | Slalom: low bars and hoops | under 40 s / 28 s / 22 s (misses +3 s) |
| C04 Site Targets | Accuracy (60 s) | 4 / 6 / 8 targets |
| C05 Juggle Champion | Juggling (60 s) | 10 / 20 / 30 juggles |

Bell times and streak targets are in the level table in `Editor/GeneratedContent.cs`. Change them there, then run **Dribble To School > Rebuild All Levels**.

## Hazards

| Hazard | Behaviour |
|---|---|
| Pedestrian | Walks and pauses. The ball bounces off; the kid slips past. |
| Crossing | Green, amber, red cycle. On red, the kid or the ball on the road loses the ball. |
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
| Fountain | Spray that lifts the ball. |

## Level rules

- **Start:** a short "Ready... GO!" countdown, then you're in control.
- **Checkpoints** (grey flags) turn green when the kid passes them with the ball close by.
- **Losing the ball** (falling into a gap or water, falling off the level, or kicking it back past the start of the level) fades the screen and sends you back to the last checkpoint. There's no game over, and the clock keeps running. If you walk off without the ball, just walk back for it.
- **School bell:** a countdown to the bell. When it rings you can still finish, you're just late. Turn it off in the pause menu (cozy mode).
- **Stars:**
  - 1 star for reaching school with the ball.
  - 2 stars for getting there before the bell.
  - 3 stars for also hitting the level's perfect-touch streak target. Coins join this condition in Phase 4.
- **Pause menu:** Resume, Back to checkpoint (if the ball gets stuck), Restart level, School bell on/off, and a dev "Skip to next level".

## Controls

| Action | Phone | Keyboard / mouse |
|---|---|---|
| Walk back / forward (hold) | ◀ ▶ buttons (bottom-left); let go to stop | `A` / `←`, `D` / `→` |
| Jump (hold = higher) | JUMP button (bottom-right) or swipe up | `Space` / `W` / `↑` |
| Touch / juggle | Quick tap anywhere else | `F` / `J` |
| Kick (aimed) | Drag from the KICK button the way the ball should go, release | Mouse drag from KICK |
| Kick (quick pass) | Tap KICK | `K` |
| Pause | Pause button | `Esc` / `P` |
| Restart level | Pause > Restart | `R` |
| Tuning panel | Tuning button | `Tab` |

## How it plays

- **Walk** with the ◀ ▶ buttons. Whenever the kid walks into the ball, it gets a slightly random touch in the walking direction, so you can dribble forward or back.
- **Perfect touch:** tap as the kid closes in and the ball sits in the sweet spot just ahead of the feet. Perfect touches have no randomness and they build a streak.
- **Juggle:** tap while the ball is in the air near the kid.
- **Kick:** drag from the KICK button (just left of JUMP) in the direction you want the ball to go: up-right to chip forward, up-left to chip back. The length sets the power. Time slows while you aim, and only the first 0.5 s of the flight is previewed. A quick tap on KICK is a short pass the way the kid faces. Kicks only work when the ball is within reach: the KICK button glows green when it is, and the dots turn red when it isn't.
- **Stop** by letting go of the arrows. A stopping kid traps the ball under the foot.
- **Left-handed mode** swaps the two button clusters.

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
    CameraRig/  CameraFollow2D.cs      look-ahead, vertical dead zone, level bounds
    Core/       LevelManager.cs        intro, bell, checkpoints, lose/respawn, pause, stars
                Checkpoint.cs, LoseZone.cs, GoalZone.cs, TimeControl.cs, GameSettings.cs
    Levels/     LevelDefinition.cs, LevelCatalog.cs (ScriptableObjects)
    UI/         LevelHud.cs            grey-box HUD, pause, results, live tuning panel
    Tuning/     BallTuning.cs, PlayerTuning.cs (ScriptableObjects)
    Editor/     LevelBuildKit.cs       sprites, assets, gameplay rig, track pieces
                GreyboxLevels.cs       the level layouts
                GeneratedContent.cs    builds every scene + build settings
```

## About the camera

The original plan named Cinemachine for the camera. For now the project uses its own `CameraFollow2D`, which already has look-ahead, a vertical dead zone, level bounds and a snap on respawn. The reason is that I couldn't compile against Cinemachine's API while building this, and a single wrong API call would stop the project from entering Play mode. It's a self-contained swap once the levels are verified in the editor.

## Progression

- **Coins:** collected by the kid or the ball. Bonuses come from perfect touches, new stars, new stickers, and collecting every coin in a level.
- **Stickers:** one is hidden in each level, often high up, so a well-kicked ball can collect it.
- **Stars:** 1 for finishing, 2 for beating the bell, 3 for also hitting the streak target and collecting every coin.
- **Locker Room:** buy and equip ball skins, backpack flags, outfits and ball trails. All of them are drawn in code.
- **Saving:** progress goes to `save.json` in the app's data folder. The **Dribble To School** menu has Reset Save Data and Give 1000 Coins for testing.

## Look and sound

All art and audio are generated in code, so the repo has no art or audio files to maintain:

- **Art.** A storybook style throughout: watercolour grain, wobbly ink outlines, and a warm palette per chapter that shifts through the school morning. The editor bakes it to `Assets/_Game/Art/Generated` when levels are rebuilt.
- **Animation.** The kid is a paper-doll rig with run, jump, kick, land, celebrate and stumble animations. The ball squashes and stretches and casts a shadow.
- **Feel.** Parallax backdrops, particles for every action, screen shake, a slow-motion finish, and the camera zooms out while aiming.
- **Audio.** Synthesized sound effects for every action and a lo-fi music loop per chapter, plus a menu theme.
- **Haptics.** Taptic feedback on iOS and short vibrations on Android.

## Menus, settings and accessibility

- **Menu:** Play (chapter map), Locker Room (shop), Stickers (album), Settings, Credits.
- **Settings:** music and SFX volume, vibration, screen shake, school bell (off = cozy mode), left-handed controls, colour-blind aim colours, language (English / Español) and reset progress.
- **Tutorial:** short hint cards appear the first time each new mechanic shows up.
- **Developer tools:** the tuning sliders are only in the editor and development builds (Tab, or the Tune button in the HUD).

## Tests

Edit-mode tests live in `Assets/_Game/Tests/Editor/GameLogicTests.cs`. Run them from **Window > General > Test Runner > EditMode**. They check:

- every language has every string, and every level has a translated name,
- the level table (23 story levels, one challenge per chapter, unique ids and scenes),
- the shop table (unique ids, free defaults),
- challenge star thresholds, and that Next level skips challenges,
- generated sound effects and music (no invalid samples, no clipping),
- generated art (solid blocks, seamless ground edges).

The tests never touch the player's save file. The file is wrapped in `UNITY_INCLUDE_TESTS`, so it compiles to nothing unless the Test Framework is active.

## Release

See [`docs/RELEASE.md`](docs/RELEASE.md) for:

- the business model switch (paid app, or free with a one-time Full Game unlock) and the IAP setup,
- one-click and CI builds (Android AAB and APK, iOS Xcode project) with signing from environment variables,
- privacy answers (no data collected), store listing copy, a screenshot plan and the pre-submission checklist.
