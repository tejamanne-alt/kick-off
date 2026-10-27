# Dribble To School

A cozy, hand-drawn soccer side-scroller for iOS and Android, built in Unity 6 (2D).
The full game brief is in [`GAME_PROMPT.md`](GAME_PROMPT.md).

## Status: Phase 2 (level flow)

- **Phase 1 (core feel):** kid controller, ball physics, dribbling, the slingshot kick with a trajectory preview.
- **Phase 2 (level flow):** checkpoints, losing the ball and respawning, the school-bell timer with a cozy mode, the level-complete screen with stars, a pause menu, a level-framing camera, and 3 grey-box levels plus the test track.

## Open the project

1. Install **Unity 6** (6000.0 LTS or newer) with **iOS Build Support** and/or **Android Build Support** from Unity Hub.
2. In Unity Hub choose **Add > Add project from disk** and select this folder. If Hub asks about the editor version, pick any Unity 6 version you have installed.
3. On the first open, Unity imports packages. If it asks to **enable the new Input System backend**, click **Yes** (the editor restarts). The code works with either input backend.
4. Once importing finishes, an editor script generates every level scene and opens **Level 1**. It runs again automatically whenever the generated content is out of date. You can also run it from **Dribble To School > Rebuild All Levels**.
5. Press **Play**. Set the Game view to a landscape phone resolution (for example 1920x1080).

Generated scenes are rebuilt from code, so edits made directly in those scenes get overwritten on the next rebuild. Change the layouts in `Editor/GreyboxLevels.cs` instead, or duplicate a scene before you edit it by hand. Tuning assets and level definitions are never overwritten.

## Levels

| Scene | Level | Bell | 3rd-star streak | Teaches |
|---|---|---|---|---|
| `L01_OutTheDoor` | Out the Door | 0:50 | 3 | dribble, perfect touch, brake, jump, chip, small gap |
| `L02_CornerShop` | Corner Shop | 1:05 | 4 | crates, puddles, ramp and walkway, awning bounce |
| `L03_UpTheHill` | Up the Hill | 1:20 | 5 | stairs, a plateau gap, step + high wall, juggling run-in |
| `Phase1_TestTrack` | Test Track | none | none | every mechanic back to back, for tuning |

The bell times and streak targets live in `Assets/_Game/Levels/L0x.asset`. **Next level** follows the order in `LevelCatalog.asset`.

## Level rules

- **Start:** a short "Ready... GO!" countdown, then the kid starts running.
- **Checkpoints** (grey flags) turn green when the kid passes them with the ball close by.
- **Losing the ball** (falling into a gap or water, falling off the level, or leaving the ball about 9 m behind) fades the screen and sends you back to the last checkpoint. There's no game over, and the clock keeps running.
- **School bell:** a countdown to the bell. When it rings you can still finish, you're just late. Turn it off in the pause menu (cozy mode).
- **Stars:**
  - 1 star for reaching school with the ball.
  - 2 stars for getting there before the bell.
  - 3 stars for also hitting the level's perfect-touch streak target. Coins join this condition in Phase 4.
- **Pause menu:** Resume, Back to checkpoint (if the ball gets stuck), Restart level, School bell on/off, and a dev "Skip to next level".

## Controls

| Action | Phone | Keyboard / mouse |
|---|---|---|
| Brake (hold) | Hold the left side of the screen | `A` / `←` / `Shift` |
| Jump (hold = higher) | JUMP button (bottom-right) or swipe up | `Space` / `W` / `↑` |
| Touch / juggle | Quick tap on the right side | `F` / `J` |
| Kick | Touch the ball, drag back, release | Mouse drag from the ball |
| Pause | Pause button | `Esc` / `P` |
| Restart level | Pause > Restart | `R` |
| Tuning panel | Tuning button | `Tab` |

## How it plays

- The kid **auto-runs** right. Whenever the kid catches up with the ball, it gets a slightly random touch forward.
- **Perfect touch:** tap as the kid closes in and the ball sits in the sweet spot just ahead of the feet. Perfect touches have no randomness and they build a streak.
- **Juggle:** tap while the ball is in the air near the kid.
- **Kick:** drag back from the ball like a slingshot. The direction sets the angle and the length sets the power. Time slows while you aim, and only the first 0.5 s of the flight is previewed. Kicks only work when the ball is within reach (the dots turn red when it isn't).
- **Brake** to stop. A stopping kid traps the ball under the foot.

## Tuning the feel

Every feel value lives in two assets:

- `Assets/_Game/Settings/PlayerTuning.asset`: run speed, acceleration, jump, gravity, coyote time, jump buffer.
- `Assets/_Game/Settings/BallTuning.asset`: bounce, friction, rolling resistance, reach, lead speed, perfect band, juggle, kick power, slow motion, preview.

You can edit them in the Inspector or live in Play mode with the in-game **Tuning** panel. In the editor, panel changes are saved to the assets.

Values worth experimenting with first:

1. `BallTuning.dribbleLeadSpeed` and `rollingResistance` set the dribble rhythm, meaning how far the ball runs ahead and how fast the kid catches up.
2. `BallTuning.perfectTouchBand` sets how forgiving the perfect timing is.
3. `BallTuning.maxKickSpeed`, `maxDragDistance` and `aimTimeScale` set kick power and comfort on a small screen.
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
    Player/     KidController.cs       auto-run, brake, variable jump, coyote time
    Ball/       BallController.cs      physics ball, auto/perfect touches, juggle, kick
                KickAimer.cs           slingshot aim + slow motion
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

## Next: Phase 3

Phase 3 adds the hazard system (pedestrians, crossings with traffic lights, dogs, puddles that slow the ball, wind, moving platforms, switches and gates) and Chapters 1-2 (10 levels).
