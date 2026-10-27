# Dribble To School

A cozy, hand-drawn soccer side-scroller for iOS and Android, built in Unity 6 (2D).
The full game brief is in [`GAME_PROMPT.md`](GAME_PROMPT.md).

## Status: Phase 1 (core feel)

The Phase 1 grey-box covers the kid controller, ball physics, dribbling, the slingshot kick with a trajectory preview, and a test track.

## Open the project

1. Install **Unity 6** (6000.0 LTS or newer) with **iOS Build Support** and/or **Android Build Support** from Unity Hub.
2. In Unity Hub choose **Add > Add project from disk** and select this folder. If Hub asks about the editor version, pick any Unity 6 version you have installed.
3. On the first open, Unity imports packages. If it asks to **enable the new Input System backend**, click **Yes** (the editor restarts). The code works with either input backend.
4. Once importing finishes, an editor script builds the test track automatically:
   `Assets/_Game/Scenes/Phase1_TestTrack.unity`. You can rebuild it any time from **Dribble To School > Rebuild Phase 1 Test Track**.
5. Open that scene and press **Play**. Set the Game view to a landscape phone resolution (for example 1920x1080).

## Controls

| Action | Phone | Keyboard / mouse |
|---|---|---|
| Brake (hold) | Hold the left side of the screen | `A` / `←` / `Shift` |
| Jump (hold = higher) | JUMP button (bottom-right) or swipe up | `Space` / `W` / `↑` |
| Touch / juggle | Quick tap on the right side | `F` / `J` |
| Kick | Touch the ball, drag back, release | Mouse drag from the ball |
| Reset run | Reset button | `R` |
| Tuning panel | Tuning button | `Tab` |

## How it plays

- The kid **auto-runs** right. Whenever the kid catches up with the ball, it gets a slightly random touch forward.
- **Perfect touch:** tap as the kid closes in and the ball sits in the sweet spot just ahead of the feet. Perfect touches have no randomness and they build a streak.
- **Juggle:** tap while the ball is in the air near the kid.
- **Kick:** drag back from the ball like a slingshot. The direction sets the angle and the length sets the power. Time slows while you aim, and only the first 0.5 s of the flight is previewed. Kicks only work when the ball is within reach (the dots turn red when it isn't).
- **Brake** to stop. A stopping kid traps the ball under the foot.
- The run resets if the ball or the kid falls off the track, or if the ball is left far behind.

The test track runs, in order: free dribbling, a kerb, a low wall (chip it), a gap, a crate stack (kick it down), a ramp and a raised platform, a bouncy awning, a step plus a high wall, a juggling stretch, then the school gate.

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
    Input/      GameInput.cs           touch / mouse / keyboard -> game intents
    Player/     KidController.cs       auto-run, brake, variable jump, coyote time
    Ball/       BallController.cs      physics ball, auto/perfect touches, juggle, kick
                KickAimer.cs           slingshot aim + slow motion
                TrajectoryPreview.cs   dotted arc for the first ~0.5 s
    CameraRig/  CameraFollow2D.cs      look-ahead follow (Cinemachine in Phase 2)
    Core/       TestTrackSession.cs    timer, resets, finish; TimeControl, GoalZone
    UI/         DevHud.cs              grey-box HUD + live tuning panel
    Tuning/     BallTuning.cs, PlayerTuning.cs (ScriptableObjects)
    Editor/     TestTrackBuilder.cs    generates sprites, assets and the test scene
```

## Next: Phase 2

Phase 2 adds the Cinemachine camera, checkpoints, the lose-ball/respawn flow, the bell timer, the level-complete flow, and three grey-box levels.
