# Build Progress

This file is the resume point. A new session should read it first. All eight phases are done; next comes on-device playtesting and tuning (see "After Phase 8").

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Kid controller, ball physics, dribble, slingshot kick, test track | Done |
| 2 | Level flow: checkpoints, lose/respawn, bell timer, results, pause, camera | Done |
| 3 | Hazard system + Chapters 1-2 (L01-L10) | Done |
| 4 | Coins, stickers, save system, shop, cosmetics, chapter map (uGUI kit) | Done |
| 5 | Chapters 3-5 (L11-L23) + ball skill challenges | Done |
| 6 | Procedural storybook art, kid animation, parallax, FX, synthesized audio, haptics | Done |
| 7 | uGUI HUD/menus, settings, tutorial, localization, accessibility | Done |
| 8 | Store service + full-game unlock, analytics, perf, Android/iOS build setup | Done |

## Conventions (keep these)

- **Scenes are generated.** `Editor/GeneratedContent.cs` holds the level table (chapter, id, name, scene, bell, streak target, layout). `Editor/GreyboxLevels.cs` holds the layouts, and `Editor/LevelBuildKit.cs` holds the track pieces and the gameplay rig. Bump `GeneratedContent.Version` whenever layouts or the rig change.
- **Compile check without Unity.** Scripts are compiled with Mono `mcs` against the UnityEngine 2021.3 module DLLs (NuGet `UnityEngine.Modules`) and `UnityEditor.dll` (NuGet `Unity3D.SDK` 2021.1). The Unity 6 renames (`linearVelocity`, `linearDamping`, `angularDamping`) are mapped back by sed, and the Input System is stubbed. Three configs: legacy input, Input System, editor. Stay at C# 7.3 (no target-typed `new`, no switch expressions).
- **Presentation listens to `Core/GameEvents`.** Gameplay raises typed events; audio, FX, haptics and analytics subscribe to them.
- Restartable objects implement `IResettable`. `LevelManager.BeginRun` resets them; respawning at a checkpoint doesn't.
- The compile check also references `UnityEngine.UI.dll` (NuGet `Unity3D.UnityEngine.UI` 2020.3) and Mono's `netstandard.dll` facade. The Input System stub includes `InputSystemUIInputModule`.
- **Menus are uGUI built from code** with `UI/Kit/UIKit.cs`: canvas at 1920x1080 matched on height, procedural sprites, `UIButtonFx` presses, `UIPopIn` entrances. No prefabs.
- **The shop's contents** live in `Editor/CosmeticsTable.cs`. Cosmetic art is drawn at runtime by `Cosmetics/CosmeticArt.cs`.
- **Progress** is saved to `persistentDataPath/save.json` by `Progression/SaveSystem.cs` (atomic write, corrupt files backed up). Coin economy constants are in `Progression/Rewards.cs`.
- **Art is code.** `Art/ProceduralArt.cs` draws everything on `Art/PixelCanvas.cs` (anti-aliased shapes, ink outline, watercolour grain, wrap-aware tiling). `Editor/ArtBaker.cs` bakes it to `Assets/_Game/Art/Generated` (FullRect meshes, 9-slice borders). Chapter palettes are in `Art/ChapterTheme.cs`.
- **Previewing art and audio without Unity.** The scratchpad harnesses compile ProceduralArt/Synth against tiny Unity stubs (a Color/Vector2/Mathf/Perlin reimplementation) and render PNG/WAV. Use them to eyeball changes before committing.
- **Audio is code.** `Audio/Synth.cs`, `SoundBank.cs` (26 SFX) and `MusicGenerator.cs` (6 loops) are pure C#. `AudioDirector` (auto-booted, DontDestroyOnLoad) maps GameEvents to SFX and haptics and crossfades music per chapter.
- **All UI text goes through `Localization/Loc.T(key)`.** Tables live in `Localization/StringTables.cs` (en, es). Lose reasons are keys (`lose.*`); level names are `level.<id>`.
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

## Phase 6 summary

- Storybook look for every scene:
  - Inked paper blocks (9-sliced) and wooden crates.
  - Tiled ground with a chapter edge: grass, cobbles, sand, kerb or park path.
  - Drawn cars, dogs, gulls and pedestrians.
  - Wooden signposts.
- Parallax backdrop per chapter: a sky gradient and sun on the camera, drifting clouds, a far strip (hills, towers, sea or skyline), mid props (houses, shops, palms, huts, cranes, pillars, trees, the school) and a near strip (hedges, bunting, dune grass, site fence).
- The kid is a paper-doll rig (CharacterRig + KidAnimator): run cycle, idle breathing, jump and fall poses, kick swing, landing squash, celebration and stumble. Pedestrians walk with WalkerAnimator.
- Ball: squash and stretch along velocity and on impacts (BallVisual), plus a ground shadow.
- FX: pooled sprite particles (FxPool) driven by FxDirector. Dust, sparkles, splashes, feathers and confetti, screen shake (can be turned off in settings), a slow-motion goal moment, and the camera zooms out while aiming.
- Audio: synthesized SFX for every event, lo-fi music per chapter plus a menu theme, a referee whistle at the start and the school bell.
- Haptics: Taptic Engine on iOS (`Assets/Plugins/iOS/DTSHaptics.mm`), short amplitude vibrations on Android.
- GameSettings gained music and SFX volume, haptics, screen shake, left-handed, colour-blind aim and language (the UI comes in Phase 7).

## Phase 7 summary

- In-level HUD is now uGUI (`UI/GameHud.cs`):
  - Info card (level, timer, bell clock, coins, streak or challenge status) and a round pause button.
  - Drawn jump button and brake zone, which follow the left-handed setting.
  - Aim meter, toasts, Ready/GO and the respawn fade.
  - Pause menu, and an animated results screen: stars pop in with chimes, coins count up, then Retry / Map / Next.
- Developer tuning sliders moved to `UI/DevTuningPanel.cs`. They only exist in the editor and development builds (Tab key or the Tune button).
- Menus:
  - Title has Play, Locker Room, Stickers, Settings and Credits, plus a first-launch splash.
  - Sticker Album (`FrontEnd/AlbumScreen.cs`) shows procedural die-cut stickers per level (`UI/StickerArt.cs`).
  - Shared Settings modal (`UI/SettingsPanel.cs`): music and SFX volume, vibration, screen shake, school bell (cozy mode), left-handed, colour-blind aim, language, and reset progress with a confirmation.
- Localization: every UI string is shipped in English and Spanish, with device-language detection. Changing language rebuilds the open screens.
- Tutorial: `Tutorial/TutorialHint.cs` triggers show a once-per-player hint card the first time each mechanic appears. There are 18 hints, placed in L01, L04-L07, L09, L12, L13, L15-L17, L19-L21 and C01.
- Accessibility: large touch targets, left-handed mirroring, colour-blind trajectory colours, and toggles for screen shake, vibration and the bell timer.

## Phase 8 summary

- Business model (Option A): `Store/Monetization.cs`, `IStoreService`, `MockStore` (dev purchases succeed; release builds report unavailable), and `UnityIapStore` (IAP 4.x, compiled only with the `DTS_UNITY_IAP` define). The unlock panel shows the localized price, Buy and Restore. Chapters after chapter 1 are gated only when `RequireUnlock` is on (off by default).
- Analytics: `Analytics/AnalyticsService.cs` (local JSON-lines file plus the console in dev; add sinks for a backend) and `AnalyticsTracker` covering app_open, level_start, level_complete, level_quit, ball_lost (with x position, for balancing) and purchase.
- Performance: the HUD only rebuilds text when values change; profiler markers on FX and music upload; menus let the screen sleep while levels keep it awake; pooled particles and allocation-free physics queries throughout.
- Build: `Editor/BuildScripts.cs` applies store player settings, bakes the procedural 1024 px icon, signs from environment variables, and offers menu and CI builds (AAB, dev APK, iOS). The iOS privacy manifest is at `Assets/Plugins/iOS/PrivacyInfo.xcprivacy`.
- `docs/RELEASE.md` has the full release guide, store listing copy, privacy answers and a checklist.

## Post-phase work

- Runtime review: 11 issues found and fixed (lose-zone placement on L17, the L22 gap, cozy-mode lateness, GameInput across scene loads, tunnel coverage, crash-safe saves, analytics quit events, UI animation delays, trail on respawn, button pulse jitter, settings left open after resume).
- Edit-mode tests in `Assets/_Game/Tests/Editor` cover content tables, localization parity, challenge rules, and the generated audio and art.
- First device playtest feedback:
  - Controls: the kid no longer auto-runs. ◀ ▶ buttons walk back and forward, and letting go stops and traps the ball. Dribbling works in both directions and the kid turns around.
  - The kick moved from "touch the ball" to a KICK button left of JUMP: drag the way the ball should go (forward or back), or tap for a quick pass. The button glows when the ball is in reach.
  - A ball kicked back past the level start is lost, and play resumes at the last checkpoint. The start wall stops the kid but not the ball. The "left the ball behind" rule is gone, because you can walk back for it.
  - Signs: posts are now planted in the ground under each sign, with two legs on wide boards. Signs over gaps move to the near edge. SCHOOL hangs as a banner on the gate. The ball gate slides up into a wooden frame instead of floating.
  - Ground and pit fills now reach below the camera's lowest view, so no sky colour shows under the level.
- Character animation: arms and legs are now two pieces each (thigh and shin, upper arm and forearm), with knee and elbow joints and shirt-coloured sleeves. The kid's run folds the knee in the swing and plants a straight leg, and the arms drive with bent elbows. The jump tucks the knee, the kick cocks the knee back and then snaps it straight, and landings crouch. Pedestrians stroll with soft knees. All of this is `RigPose` in `CharacterRig`.
- Art direction moved to an anime look, matching the reference shots:
  - `Art/CharacterArt.cs` draws the teen (512 px per unit, cel-shaded, thin line).
  - `Art/SceneryArt.cs` draws the deep-blue skies, cumulus clouds, per-chapter far strips, large mid props, the tileable utility-pole line and the near strips.
  - Chapter 1's ground is now asphalt with a white kerb.
  - The menu sky matches.

## After Phase 8 (next steps)

1. Open in Unity 6 and fix any compile differences from the 2021 reference DLLs. Likely candidates are deprecated-API warnings for the `BuildTargetGroup` overloads in `BuildScripts`.
2. Playtest on devices and tune the feel (tuning assets plus the Tune panel), then the bell times and streak targets (the level table).
3. Optional: swap `CameraFollow2D` for Cinemachine, and add more languages to `StringTables`.
