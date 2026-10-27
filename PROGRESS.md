# Build Progress

This file is the resume point. A new session should read it first, then continue with the first phase that isn't done.

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Kid controller, ball physics, dribble, slingshot kick, test track | Done |
| 2 | Level flow: checkpoints, lose/respawn, bell timer, results, pause, camera | Done |
| 3 | Hazard system + Chapters 1-2 (L01-L10) | Done |
| 4 | Coins, stickers, save system, shop, cosmetics, chapter map (uGUI kit) | Done |
| 5 | Chapters 3-5 (L11-L23) + ball skill challenges | Done |
| 6 | Procedural storybook art, kid animation, parallax, FX, synthesized audio, haptics | Next |
| 7 | uGUI HUD/menus, settings, tutorial, localization, accessibility | Pending |
| 8 | Store service + full-game unlock, analytics, perf, Android/iOS build setup | Pending |

## Conventions (keep these)

- **Scenes are generated.** `Editor/GeneratedContent.cs` holds the level table (chapter, id, name, scene, bell, streak target, layout). `Editor/GreyboxLevels.cs` holds the layouts, and `Editor/LevelBuildKit.cs` holds the track pieces and the gameplay rig. Bump `GeneratedContent.Version` whenever layouts or the rig change.
- **Compile check without Unity.** Scripts are compiled with Mono `mcs` against the UnityEngine 2021.3 module DLLs (NuGet `UnityEngine.Modules`) and `UnityEditor.dll` (NuGet `Unity3D.SDK` 2021.1). The Unity 6 renames (`linearVelocity`, `linearDamping`, `angularDamping`) are mapped back by sed, and the Input System is stubbed. Three configs: legacy input, Input System, editor. Stay at C# 7.3 (no target-typed `new`, no switch expressions).
- **Presentation listens to `Core/GameEvents`.** Gameplay raises typed events; audio, FX, haptics and analytics subscribe to them.
- Restartable objects implement `IResettable`. `LevelManager.BeginRun` resets them; respawning at a checkpoint doesn't.
- The compile check also references `UnityEngine.UI.dll` (NuGet `Unity3D.UnityEngine.UI` 2020.3) and Mono's `netstandard.dll` facade. The Input System stub includes `InputSystemUIInputModule`.
- **Menus are uGUI built from code** with `UI/Kit/UIKit.cs`: canvas at 1920x1080 matched on height, procedural sprites, `UIButtonFx` presses, `UIPopIn` entrances. No prefabs.
- **The shop's contents** live in `Editor/CosmeticsTable.cs`. Cosmetic art is drawn at runtime by `Cosmetics/CosmeticArt.cs`.
- **Progress** is saved to `persistentDataPath/save.json` by `Progression/SaveSystem.cs` (atomic write, corrupt files backed up). Coin economy constants are in `Progression/Rewards.cs`.
- No Cinemachine yet: `CameraRig/CameraFollow2D.cs` covers look-ahead, the dead zone and bounds.

## Phase 3 summary

- Hazards (`Scripts/Hazards`): Pedestrian (bounces the ball, the kid passes), Crossing with traffic light and passing car (red = lose), Dog (chases low balls and noses them back), SlowZone (puddle/sand), WindArea (headwind or updraft, optional gusts), MovingPlatform (carries the kid via `IMovingSurface`), BallSwitch + Gate, Springboard (flush trigger pad).
- Chapter 1 Home Street: L01 Out the Door, L02 Parked Cars, L03 Up the Hill, L04 Garden Gate, L05 Puddle Lane.
- Chapter 2 Market and Crossings: L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour.

## Phase 4 summary

- Coins (kid or ball collects; restored on restart) and one hidden sticker per level (often placed high, so a kicked ball can collect it).
- 3rd star = beat the bell + hit the streak target + collect every coin.
- Rewards: coins collected + 1 per perfect touch + 10 per new star + 15 per new sticker + 10 for collecting every coin.
- `FrontEnd` scene (the first scene in the build) has three screens. Title has a bouncing equipped ball, Play and Locker Room. The Chapter Map has a winding path of nodes with stars, locks and a pulsing next level, plus chapter tabs. The Locker Room covers balls, flags, outfits and trails, with buy and equip.
- Levels: the kid wears the equipped outfit, has a flag on the backpack, and the ball shows its skin and trail.
- Editor menu: Open Menu, Reset Save Data, Give 1000 Coins (testing).

## Phase 5 summary

- New hazards:
  - Seagull: swoops and knocks the ball.
  - Tide: water that rises and falls, with a lose zone.
  - DarkZone + DarknessOverlay: a light pool around the kid inside tunnels.
  - PipeSpawner: rolling pipes.
  - SwingPlatform: a pendulum seat that carries the kid.
  - Fountain: an updraft WindArea with a spray visual.
- Challenges (`Scripts/Challenges`): `ChallengeObjective` base (clock, score, star thresholds, lower-is-better), JuggleChallenge (kid stands still via `KidController.autoRun`), AccuracyChallenge with ChallengeTarget, SlalomChallenge with SlalomGate (low bars and hoops, +3 s per miss, finishes at the GoalZone).
- Challenges are optional. One per chapter, unlocked by the chapter's first story level and skipped by "Next level". They show as gold "!" nodes on the map. A 0-star challenge result is not saved.
- Chapter 3 The Beach: L11 Boardwalk, L12 Low Tide, L13 Seagull Bay, L14 Sandcastle Sprint, C03 Beach Slalom.
- Chapter 4 Underpass: L15 The Underpass, L16 Building Site, L17 Cranes, L18 Tunnel Run, C04 Site Targets.
- Chapter 5 Park & School: L19 Park Gates, L20 Fountain Square, L21 Playground, L22 Duck Pond, L23 The Final Bell, C05 Juggle Champion.
- Also C01 Keepy-Uppy (Ch1) and C02 Window Shopping (Ch2). Total: 23 story levels + 5 challenges.
