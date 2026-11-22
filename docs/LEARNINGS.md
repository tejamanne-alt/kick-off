# Learnings: every mistake, its cause, its fix, and the rule it taught

Read this before changing anything. Each entry is something that went wrong, or nearly did, in building Kick Off 2. Every entry gives:
- **What happened**, with the version (`vN` is `GeneratedContent.Version`) or commit;
- **Why**;
- **The fix**;
- **The rule** to follow from now on.

Add a new entry whenever something has to be fixed, reverted or redone, in the same commit as the fix. The rules at the top are the ones broken most often or at the highest cost. The sources are `PROGRESS.md`, the git history (PRs #1 to #45 and later) and the audits of November 2026.

## The rules that matter most

1. **The phone is the truth.** A change to cost, feel or GPU output isn't done until it has run on the low-end reference phone (a OnePlus Nord CE5: Mali-G615 MC6, 2392×1080, 120 Hz). Record the fps and frame pacing in `PROGRESS.md`. Compiling, glslang, numpy shader ports and Blender renders are proxies. They prove "it builds" and "the mock looks right", never "it runs well".
2. **Budget before you add.** Every mesh, texture, shadow setting, full-screen pass and per-frame script has a cost per device tier (`docs/PERFORMANCE.md`). Every change states its delta. The game reached 28 fps by adding cost that was each time noted as "not checked on a low-end phone".
3. **Settings live in code.** `ProjectSettings/` is not in git, so every player, quality, graphics, frame-rate and import setting is applied from code: `Editor/BuildScripts.cs`, `Core/GraphicsQuality.cs`, the asset postprocessors. Never rely on what a fresh checkout defaults to.
4. **Write the target before changing a character.** That means style references, a triangle budget and an acceptance board. Let the user choose from side-by-sides. Never swap a character's source back on your own judgement.
5. **Review characters as players see them.** That means:
   - at the current camera's play size, close up, and on the title screen;
   - from the game's camera angles;
   - in all four looks (Original, Comic halftone, Pencil sketch, Classic cartoon);
   - with characters casting no shadows, as in the game;
   - with the head nodded and turned as the menu and the run move it, not only in the idle pose (C15).
6. **A fix for one asset is a fix for all of them.** When a pipeline bug is found and fixed, rebuild every asset made by the old pipeline in the same change.
7. **Record every revert,** with who decided, why, and "don't retry X".

## A. Process and verification

**A1. Nothing had ever run in Unity or on a device.**
- *What:* 57 sections of `PROGRESS.md` say "Not run in Unity". The shaders were never compiled by Unity. The 60 fps release check (`docs/RELEASE.md`) was never done, although the brief asked for device testing after every phase. The first real performance data was the user's Nord CE5 recording: about 28 fps, with frames from 17 to 79 ms.
- *Why:* there is no Unity in the build environment, so proxies stood in.
- *Fix:* none possible here. Every change since is labelled with what was and wasn't verified.
- *Rule:* rule 1. Say plainly, in the commit and in `PROGRESS.md`, what still has to be checked on a device.

**A2. A compile error reached the user (PR #22, fixed in #23).**
- *What:* `LevelBuildKit`'s own `Cosmetics` member hid the `DribbleToSchool.Cosmetics` namespace in a partial class.
- *Why:* the compile check wasn't run over every changed editor file.
- *Fix:* the type is now fully qualified.
- *Rule:* run the compile check on every commit. In the editor's partial classes, fully qualify types from other namespaces.

**A3. The compile check was blind to method bodies (found November 2026).**
- *What:* against reference DLLs that lack the uGUI and Input System types, Roslyn stops after declaration errors and never binds method bodies. A deliberately wrong API call compiled "clean".
- *Fix:* the check uses empty stubs for `UnityEngine.UI`, `EventSystems` and `InputSystem`, so declarations bind and method bodies get checked. It diffs the errors against a clean-tree baseline, ignoring line numbers, and allow-lists Unity 6-only APIs that are missing from the 2021 references (`Resolution.refreshRateRatio`).
- *Rule:* a check is only trusted after it has caught a planted error. Plant one whenever the harness changes.

**A4. Unity 6 and Xcode warnings only the user could see.**
- *What:* the deprecated `DEVELOPMENT_BUILD` directive; Xcode run-script warnings.
- *Rule:* treat the user's console logs as test results. A property whose name moved between Unity versions (for example `optimizedFramePacing`, `meshDeformation`, the tier settings) is set by reflection and logs when it is missing.

**A5. Shader checks are syntax only.**
- *What:* glslang caught `line` (a reserved word) twice and a missing uniform. Nothing checked GPU behaviour or cost.
- *Rule:* compile every pass with glslang, and plant an error to prove the harness works. Give every full-screen pass a millisecond budget and a resolution scale.

**A6. Tools that copy game code rot silently.**
- *What:* the town-map tools stopped running when `RouteTable` gained an argument. `review_poses.py` hand-copies the game's poses. The Blender review renderers copy `ToonCharacter`'s shading.
- *Rule:* a tool that mirrors C# or a shader either parses the source or fails loudly. When `ToonCharacter.shader` changes, update `review/cartoon/render_scenes.py`, `tools/blender/portrait_teen.py`, `review_teen.py` and `review_poses.py` in the same change. Otherwise the review boards and the menu's player cards drift from the game.

**A7. Reversals with no written record.**
- *What:* Two reversals were left out of `PROGRESS.md`:
  - v84: Mia rebuilt in the scripted anime style (`a4a19ad`), reverted five minutes later at the user's request (`2ea2e7d`). The user wanted their own supplied design, not a generic anime kid.
  - v86: the camera moved closer (`eedac25`), reverted as v87 because collectibles fell out of view.
- *Rule:* rule 7. Gaps in the version numbers must match recorded reverts.

**A8. Approval boards before building: keep doing this.**
- *What:* the comic, sketch and classic-cartoon filters were each approved from boards first. The boards caught eyes turned into black dots, an outline lying over a cheek, and lost detail.
- *Rule:* use the same method for characters (see `review/characters_v2/`) and for cost: put an estimate on the board.

**A9. Claims that stopped being true.**
- *What:* the README says "All art and audio are generated in code". The store text says every character was "made for this game", though the characters come from an image-to-3D generator.
- *Rule:* when an asset's source changes, update the credits, README and store text in the same change. Keep a list of each supplied asset's source and licence.

**A10. Settings that lived in one checkout.**
- *What:* Android version codes went backwards. Phones defaulted to 2 bones per vertex. HDR, MSAA, the Android blit, frame pacing and shadow cascades were all whatever the building machine generated.
- *Fix:* a version code that always rises; `Bone4` set in code; and, from November 2026, `BuildScripts.ApplyAndroidPerformanceSettings` plus `Core/GraphicsQuality`.
- *Rule:* rule 3.

**A11. The editor opened in Safe Mode on Unity 6.5 (introduced in v115, fixed November 2026 without a content rebuild).**
- *What:* the user opened the project in a newer Unity 6 and got "The project you are opening contains compilation errors". The cause was `Object.GetInstanceID()` in `CharacterRig` (added in v115 for the breathing's phase): an error from Unity 6.5 (`[Obsolete("Use GetEntityId instead.", true)]`), a warning in 6.4, fine in 6.0.
  - The console also listed five CS0675 warnings in `RoomBeacon` (int fields widened to `ulong` straight from a signed int, which sign-extends), and "This project uses Input Manager, which is marked for deprecation".
  - Unity compiles the editor scripts only after the game's, so nothing past the first error was ever checked.
- *Why:* every check here compiles against Unity 2021's reference assemblies (no Unity 6 references are published). An API that a newer Unity removed compiles clean, and the project's `6000.0.68f1` says nothing about the editor a user actually opens it in. The Input Manager was the default of a fresh project, as `ProjectSettings` isn't in git (A10).
- *Fix:*
  - `CharacterRig` spreads the breathing by a golden-ratio counter, with no id.
  - `RoomBeacon` widens through `uint`; the bits are the same, since every field is masked small and positive first.
  - `Editor/InputHandling` sets Active Input Handling to the Input System package on load and offers the restart. The game already read input through the Input System when it is on, and `UIKit` builds its `InputSystemUIInputModule`.
  - Five "never assigned" or "never used" field warnings that the editor and player builds would have shown are gone.
  - `tools/unity_api_check` resolves every Unity API the scripts use (Roslyn, every `#if` combination) and checks it against the `[Obsolete]` list of Unity's own C# reference source for any version (`run.sh 6000.5`). For 6000.5 and 6000.7 the only error was `GetInstanceID`; the old code was flagged, the new is clean.
  - `ScriptConventionTests.NoScriptCallsAnApiANewerUnityRemoved` fails on the known removed calls inside any Unity.
- *Rule:*
  - Before a change is pushed, run `tools/unity_api_check/run.sh` against the newest Unity 6 branch, not only the compile check: what the user opens the project in can be newer than `ProjectVersion.txt`.
  - Use no instance ids at all.
  - Widen signed values through an unsigned type.

**A12. The check for A11 broke the build itself (PR #49, fixed in #50).**
- *What:* `ScriptConventionTests.NoScriptCallsAnApiANewerUnityRemoved`, added in #49, had the pattern `@"new\s+Material\s*\(\s*\""`. In a C# verbatim string `\"` is a backslash and then the end of the string, so the line didn't parse. Unity reported nine syntax errors on line 78 and stopped compiling the editor assembly. That assembly holds the tests and the editor scripts, including the new `InputHandling`, so the Input Manager warning stayed too.
- *Why:*
  - The test file is wrapped in `#if UNITY_INCLUDE_TESTS`, which Unity defines when the Test Framework package is installed.
  - None of the checks defined it. Text behind an `#if` that isn't defined is skipped by the compiler, not even parsed.
  - The checks reported "clean" for a file they never read. The Roslyn API scan did define it, but only collected API names, not errors.
- *Fix:*
  - `""` is the quote inside a verbatim string.
  - `tools/unity_api_check/run.sh` now also parses every script under every combination of the `#if` symbols the scripts use (the editor with the tests, both players, the optional IAP and screenshot code), with NUnit referenced so the tests bind. It fails on any syntax error.
  - Planted back, the broken line is caught with Unity's own errors. All binding errors were compared with the tree before #49: none new.
- *Rule:*
  - A check covers only the code it compiles. List the `#if` symbols the scripts use, and compile once per combination, tests included.
  - In a verbatim string, a quote is `""`.
  - A new check is itself code: run it before pushing it (A3: plant an error, see it caught).

**A13. Xcode's GameAssembly warnings, and a builder warning on every Holiday Run build (fixed November 2026).**
- *What:* once the project compiled in Unity 6.5, the user's first iPhone build showed 13 issues in Xcode's GameAssembly target. The Unity console showed four warnings from the level build.
  - One "The selected platform is no longer supported by libc++" (`-W#warnings`): the IL2CPP code was compiled for an iOS older than 15.
  - Twelve libtool "'x.o' has no symbols": IL2CPP files of assemblies with no code of their own. They are expected, but libtool warns about each.
  - "Holiday Run stage 11 to 14: 'Waves' was left outside the Stage object; moved under it", from the level build.
- *Why:*
  - The iOS minimum (15.0) was only set by `BuildScripts.ApplyPlayerSettings`, which only the "Kick Off > Build" menu items call. A build from Unity's own Build button kept Unity's older default. ProjectSettings isn't in git (A10).
  - The beach's waves were built at the scene's root to keep them out of the street's static batch. A Holiday Run stage must hold everything under one Stage object, so its builder moved them and warned, on every build.
- *Fix:*
  - `BuildScripts.IosMinimumVersion` is applied whenever the editor loads (`AppleSigning.Apply`, with the signing), never lowering a higher setting.
  - `IosPostBuild` raises every target's and configuration's `IPHONEOS_DEPLOYMENT_TARGET` in the exported project to at least that.
  - `IosPostBuild` gives GameAssembly (and the project, which static libraries inherit) `OTHER_LIBTOOLFLAGS = -no_warning_for_no_symbols`.
  - The waves go under the animals' root, with the other moving things outside the batch, which the Holiday builder already files under the Stage.
  - The Input Manager warning that remained is Unity's own, printed at start-up. It stops after the restart `InputHandling` offers (A11).
- *Rule:*
  - Treat the user's Xcode issue navigator like the Unity console (A4): every warning there is fixed in the export step.
  - Settings every build needs are applied on load, not only in our build menu.
  - A builder that tidies up after itself should not warn about its own normal output: fix the code that made it.

**A14. An APK from Unity's own Build button wouldn't install over a test build (fixed November 2026).**
- *What:* the user built an APK (version name 1.0, 148 MB), sent it to the Nord CE5 over WhatsApp, and the phone said only "Installation failed. Please try again." The phone already had test builds of the game.
- *Why:* Android refuses an APK over an installed copy when:
  - its version code is lower (`INSTALL_FAILED_VERSION_DOWNGRADE`), or
  - it is signed with another key (`INSTALL_FAILED_UPDATE_INCOMPATIBLE`).
  OxygenOS shows neither reason.
  - The "Kick Off > Build" menu gave test APKs a version code that always rises (about a million and up), but an APK from Unity's own Build button carried the store build number, a small number. The iOS minimum had the same gap (A13): settings applied only by our build menu.
- *Fix:*
  - `Editor/AndroidApkVersionCode` writes the rising version code into every APK's generated Gradle project, whatever builds it. It never touches Player Settings' store build number, even if the build fails. App bundles (the store uploads) keep the store number.
  - A copy signed with another key still needs one uninstall (`docs/RELEASE.md`).
- *Rule:*
  - Anything every build needs goes in a build callback or an on-load step, not only in our build menu: the user builds with whatever button is in front of them.
  - When an install fails, get the reason from `adb install -r` before guessing.

**A15. Pinning Unity 6.6 broke the Input System package (fixed November 2026).**
- *What:* after the project was pinned to 6000.6.7f1 (#58), the editor stopped with about a hundred CS0619 errors in
  `Library/PackageCache/com.unity.inputsystem@.../Editor`: `'TreeView' / 'TreeViewItem' / 'TreeViewState' is obsolete`.
  A follow-on UXML error ("Could not load type InputActionAsset") and the Input Manager warning came from the same
  failure.
- *Why:*
  - `Packages/manifest.json` pinned Input System 1.11.2 (October 2024). Unity 6.2 made the non-generic `TreeView`
    classes obsolete, and 6.6 made that an error. Input System 1.14.1 switched to `TreeView<int>`.
  - The pin's PR said "Unity raises any package below its minimums when it opens the project". That was wrong for this
    package: Unity only raises packages below the editor's own declared minimum, and 1.11.2 isn't one.
  - None of the checks compile packages: `unity_api_check` reads only `Assets/`.
- *Fix:*
  - Input System 1.20.1, the newest release. It also carries the `EntityId` changes for 6.5 and newer. The game's
    calls are unchanged since 1.11: `Keyboard`, `Mouse` and `Touchscreen.current`, and
    `InputSystemUIInputModule.AssignDefaultActions`.
  - `tools/unity_api_check/package_minimums.py`, run by `run.sh`, fails when a package is older than the pinned Unity
    needs (a table of known minimums).
- *Rule:*
  - Before changing the pinned Unity version, read each package's changelog for that version.
  - Add a row to `package_minimums.py` for every package a Unity release breaks.
  - Say only what was checked. "Unity upgrades it" was a guess.

**A16. An attach point that the game never found (v125, fixed in v126).**
- *What:* Miami's walk signal was built with `B.attach.append(('Attach.Red', ...))`; `kit_lib.attach` adds the `Attach.`
  prefix itself, so the FBX held `Attach.Attach.Red` and the crossing's lamps were never lit. Nothing failed: the builder
  skips a missing attach point quietly.
- *Fix:* the names without the prefix; the rebuilt `PedSignalMIA.fbx` has `Attach.Red` and `Attach.Green`.
- *Rule:* pass attach names bare (`'Red'`), never `'Attach.Red'`. After a kit build, list each model's `Attach.` empties in
  the review sheet's log and compare them with what the builder looks up.

**A17. The phone got levels several versions old (found November 2026, fixed in v129).**
- *What:* the user's screenshots of FL2-3 Downpour to School and FL2-2 The Riverwalk showed the v123 streets: the market's
  English shops and nobori banners, Kamakura's park trees, a red slab for an arcade, "Project: soaked" (removed in v128). The
  code was v128; the levels on the phone were not.
- *Why:*
  - The generated levels were rebuilt only on the first script load of an editor session (`SessionState` bool). A pull with
    Unity open recompiles the scripts, but the levels stayed as they were.
  - `BuildScripts` rebuilt them only when there were no scenes at all, and Unity's own Build button checks nothing.
  - A Florida leg whose Miami kit or plan couldn't be found fell back to a Kamakura chapter's street without a word.
- *Fix:*
  - `GeneratedContent.AutoBuild` checks once per *version* in a session, so a recompile with a newer `Version` rebuilds.
  - `BuildScripts` rebuilds stale levels before building.
  - `GeneratedContentBuildCheck` (an `IPreprocessBuildWithReport`) fails any other build while `GeneratedContent.OutOfDate`.
  - A Florida leg built without its district logs an error and leaves the levels out of date, so they can't ship.
- *Rule:* generated content must say which version built it, and every way to a player build must refuse an older one.
  When the user reports something from the phone, first check which version their levels were built by.

**A18. The v129 check passed while every Florida leg was on a Kamakura street (found November 2026, fixed in v130).**
- *What:* after v129 the phone's Florida legs were still on Kamakura's market and park streets. Downpour to School, for
  example, had Kamakura market shops, crates and sacks, with Miami's arcade, flower-bed kerbs and grey pigeons placed on top.
  The new build check passed anyway.
- *Why:* the check asked a separate question ("are the plan file, its leg and the kit there?") instead of looking at what the
  builder had done. The builder used a plan cache made once per editor session from a path relative to the working
  directory, so an empty first read stayed empty. Whatever the exact trigger on the user's machine, the two answers could
  differ.
- *Fix:*
  - The builder records each Florida leg whose district it really built (`StreetBuilder.MiamiDistrictsBuilt`), and
    `GeneratedContent.BuildAll` checks that list. A leg missing from it leaves the levels out of date and shows a dialog.
  - The plan is read from the project folder and read again whenever it changes.
  - The fallback's error names each input: the Florida flag, the level id, the plan file, its legs and the kit.
- *Rule:* verify what was built, not a model of it. A guard that recomputes the inputs can agree with itself and still be
  wrong.

**A19. No Florida leg was ever built in its Miami district (v124 to v130; found by v130's diagnosis).**
- *What:* every Florida leg in Unity was dressed in a Kamakura chapter's street, though the Blender previews showed the
  districts. v130's error named it: "level id=(none)".
- *Why:* `LevelBuildKit.BuildScene` set `LevelId` from the definition *after* `EditorSceneManager.NewScene`, which unloads a
  definition nothing references. It then compares equal to null, so `LevelId` was always empty and the Miami plan, keyed by
  it, was never found. The function's own remarks warned about this (and E1 before it), and the lines above it read the
  route the right way.
- *Fix:* the id is read with the rest, before the new scene. `MiamiKitTests` fails if it moves after it again.
- *Rule:* in `BuildScene`, read everything the definition holds before `NewScene`. A preview that renders the plan is not
  proof the game builds it: check a built scene, or a check that sees the build's outcome (A18).

## B. Performance and mobile

**B1. 28 fps with uneven frames on a mid-range phone (November 2026).**
- *What:* the recording showed about 28 fps in a level and 21 to 23 fps on the title screen, with frame gaps of 17 to 79 ms.
- *Why:* several costs stacked up, and each was added unmeasured:
  - Every frame rendered at the panel's full 2392×1080, into an FP16 HDR target.
  - Screen-space shadows (soft, two cascades, 35 m) added a depth pre-pass of the whole scene and a full-screen shadow-collect pass.
  - Each filter added a DepthNormals pass over the whole scene, plus 2 to 3 full-screen passes.
  - Each 100k-triangle kid (plus a 30k-triangle bag) was drawn 3 to 4 times.
  - Android's "Blit Type Always" added another full-screen copy.
  - There was no frame pacing: a 60 fps target on a 120 Hz panel, so a missed frame showed for 25, 33 or 42 ms in an irregular pattern.
  - Every scene change caused one-off stalls:
    - music and ambience synthesized at runtime (about 100 MB of garbage);
    - audio clips uploaded in one frame;
    - shaders compiled on first use.
- *Fix:*
  - `Core/GraphicsQuality`: device tiers, 720/864/1080 lines, shadows and bloom per tier, and a frame-rate governor that steps down and remembers.
  - Cameras without HDR or MSAA.
  - Tier settings with no screen-space shadows.
  - Optimized Frame Pacing and Blit Type Auto.
  - PostFX warms up every pass on its first frame.
  - Characters at 32k triangles (bags 8k, passers-by 14k).
  - Per-frame CPU fixes.
  - Full detail in `docs/PERFORMANCE.md`.
- *Rule:* rules 1 to 3. Every full-screen effect has a resolution scale and a cheap low-tier path.

**B2. Character cost grew with no budget.**
- *What:* the playable kids grew from 17k to 26k, then 30k, then 100k triangles (v89, to fix "mitten" hands). Every kid FBX also carried five 30k bags. All six kids and 30 bag meshes were built into every scene, readable: about 270 MB of mesh memory, for one kid on screen. That is 3 to 4.5 triangles per pixel at play size.
- *Why:* detail was fixed by raising the global triangle count instead of spending triangles where they show. Mia's hair took over half her 100k.
- *Fix:* the November 2026 polish: 32k for each playable kid, with the head, hands and texture seams protected in decimation; 8k bags; 14k passers-by. The character FBX files went from 90 MB to 28 MB.
- *Then (v112):* the kids' and bags' meshes moved out of the scenes. The builder saves their renderers empty, and a `LazyRenderer` loads each from a `CastPart` under `Resources/Cast/` only while it is shown. So a scene loads one kid and one bag: about 46k vertices instead of 545k.
- *Rule:* a triangle budget per character type (`docs/PERFORMANCE.md`). Decimate with weights: spend triangles on the face, hands and printed detail, not on hair mass.

**B2a. Script order decides what loads.**
- *What:* the scenes are saved with every kid active, and `CharacterChoice` hides all but one as it starts. With lazy meshes, each kid's loader would have run before being hidden, loading every kid anyway. The bags are the same under `BagWear`.
- *Fix:* `CharacterChoice` runs first (execution order -2000) and hides the others before anything on them wakes. The builder saves every bag hidden, and `BagWear` shows the worn one.
- *Rule:* when a component's start-up cost depends on whether its object is shown, decide who runs first: set it with `DefaultExecutionOrder` or with the state the scene is saved in. Never leave it to Unity's unspecified order.

**B3. The filters' cost was never measured.**
- *What:* classic cartoon is about 73 texture reads per pixel, at native resolution, on the title screen too. "If older phones struggle, pass 8 can run at half resolution" was written down and never done.
- *Rule:* rule 2. Measure in milliseconds on the reference phone before shipping a pass.

**B4. Shadows forced to the top setting on every device.**
- *What:* `WorldLook` forced soft, high-resolution, two-cascade shadows at 35 m whenever the game was playing.
- *Fix:* the tier decides: High as before; Medium hard, one cascade, 25 m; Low none (the contact and blob shadows remain).
- *Rule:* shadow resolution, cascades, distance, softness and extra casters are per-tier settings.

**B5. Runtime audio synthesis spikes.**
- *What:* each scene change generated 1.5 to 4 s of audio on two threads, made about 100 MB of garbage, and uploaded 10 to 13 MB of clips in one frame.
- *Fix (partial):* one clip upload per frame. Then (B8) the generators reuse their work buffers, and the cues' samples are
  let go once uploaded.
- *Still to do:* bake the loops offline.
- *Rule:* never synthesize or upload large assets while a level runs. Spread uploads over frames.

**B6. Per-frame waste in scripts.**
- *What:*
  - Buttons rewrote their rects every frame for 5 s after each press, rebuilding the canvas.
  - Hundreds of procedural shapes ran an empty `Update`.
  - Off-screen coins animated.
  - The dev panel's `OnGUI` ran in release builds.
  - Settings were read from PlayerPrefs (a JNI call) every frame.
  - Haptics made a JNI class lookup per pulse.
  - The comic words rasterized glyphs on first use.
  - Outfit recolouring allocated whole colour arrays.
- *Fix:* the November 2026 CPU pass. Each change was reviewed by a second reader and checked to compile.
- *Rule:* write only on change, snap animations to rest, cache what doesn't change, and put editor-only callbacks behind `#if UNITY_EDITOR`.

**B7. Build size.**
- *What:* the APK reached 854 MB. The `_CA` scenes double the level scenes.
- *Rule:* review build size every release. Share assets between skins instead of copying them.

**B8. Work nobody sees, and memory nobody frees (November 2026 audit, generated content v118).**
- *What:* a four-part audit (gameplay scripts; UI, audio and co-op; GPU; loading, memory and builds) found costs paid
  for nothing:
  - **Off screen or at rest:** about 45 breaking-wave crests per beach level, the tide washes (a mesh rebuilt and
    re-uploaded every frame each), crossings' signals and cars, fountains, springboards, the underpass darkness and
    collected coins all wrote their transforms, colours or meshes every frame, in view or not, changed or not.
  - **Hidden:** the map screen's opaque mat hid the whole 3D menu street, which still drew every frame with its
    shadows and filter (3 to 6 ms of GPU with a filter, est.). The story HUD drew an alpha-0 full-screen fade every
    frame. The sky dome was shaded under every street pixel before they covered it.
  - **Rebuilt per frame:** the challenge status line (a new string 10 times a second), the coach card's signature
    string and rect, the Holiday HUD's button rects, the co-op join list (rebuilt about twice a second because the raw
    signal strength jitters, though it only shows three words), and the touch layout (5 times a frame).
  - **Main-thread I/O:** each analytics event opened and appended to its file in the frame it happened.
  - **Garbage:** the music and ambience generators threw away whole-loop buffers voice after voice (Market: 170 MB
    of garbage a visit, six visits a Holiday Run lap), and kept every cue's samples after Unity had its own copy.
  - **Leaks:** a Holiday Run stage's combined street mesh and its tide meshes belong to no scene, so unloading the
    stage left them in memory: a lap's worth more each day of the run.
  - **Builds:** the scripted builds were ZIP-compressed, so on Android no texture or mesh used the async upload
    pipeline, and the `asyncUpload` settings did nothing.
- *Why:* each was written to be correct, and nobody asked what it cost when nothing changes or nothing shows. B6's
  rule had been applied where the cost was noticed, not everywhere.
- *Fix:* see PROGRESS "The audit: work nobody sees" for the full list. Each change keeps what is drawn and played
  exactly the same: the audio generators were checked sample for sample (SHA-256 of all 95 clips before and after),
  every rest test is on a pose that follows the clock alone, and what a covered screen hides is opaque.
- *Rule:*
  - Every per-frame script asks two questions: what if nothing changed, and what if it isn't on screen? Rest on a pose
    that follows the clock alone (so it is exact on return), write on change, and skip what a covering screen hides.
  - Whatever is created at runtime (a mesh, a combined batch, a texture) is destroyed by whoever made it: scene
    unloads don't free it, and an additive scene never calls `UnloadUnusedAssets`.
  - A change to generated sound is checked bit for bit against the old output (the harness in PROGRESS).

## C. Characters

**C1. All six playable kids were torn into thousands of pieces (found November 2026).**
- *What:* Hana, Max, Kai, Leo, Mia and Zoe each had 66k to 103k open edges. 79 to 91% of their vertices sat on an open edge, and gaps ran from 0.2 to 24 mm. In the game:
  - the dark ink hull showed through the cracks as scratches;
  - each torn edge had one-sided normals, so the rim light and the cel step flared along every seam, drawing light lines across faces and jeans;
  - the filters inked the cracks.
  This was the main cause of the "low-quality assets" look.
- *Why:* the Meshy scans split their vertices along every texture island, and they were decimated before being welded. The weld fix (`meshy_rigged.weld`, commit `318993d`) was made for the passers-by and never applied to the six kids built a day earlier.
- *Fix:* `tools/blender/polish_character.py`:
  - welds open-edge vertices within 2 mm;
  - drops loose vertices;
  - turns back-to-front triangles round;
  - recomputes normals from the surface around each vertex, so they are continuous across any gap left.
  Run on every character by `polish_all.py`.
- *Rule:* rule 6. Always weld UV-split scans before decimating. Treat a rising open-edge count as a build failure. Check normals, not just shapes: render a normal pass.

**C2. Shattered normals made scanned characters blotchy.**
- *What:* the scans' normals deviated a median of about 19° from the smoothed surface, against a cel step about 4.6° wide. The light/shade boundary crossed about 18k edges on Hana (6k with smoothed normals), and the silhouette broke into thousands of tiny contours, each one an ink speck.
- *Fix:* normals smoothed by surface proximity: 12 mm on skin, 20 mm on clothes, 35 mm on hair. Hair also points away from the centre of its own mass, so the rim light shows only at its outline. The inner face leans toward the head's forward direction, so it is lit as one shape.
- *Rule:* scanned or AI-made meshes always get their normals rebuilt for toon shading.

**C3. White flecks on dark hair.**
- *What:* the rim light was added as white whatever the colour under it, and it lit every noisy hair strand.
- *Fix:* the hair volume normals (C2), and a rim in `ToonCharacter` that is narrower and tinted by the albedo.
- *Rule:* a light term that adds light must respect the surface colour, or it speckles dark materials.

**C4. The primary-school kids changed source eight times.**
- *What:*
  - scripted (anime);
  - supplied Meshy scans (v74 to v77);
  - scripted again (v80, Claude's call);
  - supplied again (v81, the user's call);
  - Mia in the anime style (v84, reverted at the user's request);
  - rigged supplied models (v90 to v95).
  Then the user said the kids "look a bit real life" and that even Hana and Max "look like low-quality assets".
- *Why:* there was never a written target for style, fidelity or budget, and the photographic texture (baked lighting, a real child's face) was never addressed.
- *Fix (November 2026):* the user's own designs are kept, but restyled:
  - an illustrated face replaced the photographic one (`tools/blender/face_paint.py`): drawn eyes with highlights, simple brows, a nose stroke, the kid's own mouth, a little blush, in their own skin tone. The user rejected it as alien (C14). Since v113 each kid keeps their own face with Max's finish (`face_ink.py`);
  - the mesh is repaired (C1, C2).
  Reviewed before and after in `review/characters_v2/`.
- *Rule:* rule 4. "Make it a game character" means the user's design with a game finish. It does not mean a generic replacement: that is exactly what was reverted in v84.

**C5. Scans with arms fused to the body.**
- *What:* Leo, Zoe and Kai, scanned with their arms hanging against the body, smeared at the shoulders. Several repair attempts were dropped.
- *Fix:* rigged models in an A-pose (v90 to v95).
- *Rule:* accept a generated character only in an A-pose, with the arms a hand's width from the body and a Mixamo-style rig. Ask for flat, unlit, cel-style colour (no baked lighting, no photographic skin) and game proportions. Reject a fused scan instead of spending days repairing it.

**C6. Guessed weights folded the faces.**
- *What:* weights by nearness put 18 to 29% of the front of the head partly on the Neck bone, so faces folded as the head turned.
- *Fix:* a rigid head above the jaw (v79).
- *Rule:* use the source's own skin weights where they exist, and check weight distributions with numbers.
- *Later:* the source's own weights were no better. The rigged scans folded the same way until v114 (C15).

**C7. Decimation removed joints, and later dragged prints.**
- *What:*
  - The trousers' knee became one long hinge (bare skin showed through).
  - In November 2026, cutting to 32k first stretched Leo's "01" and Kai's plaid into blocks: vertices on texture-island borders moved and dragged the paint with them.
- *Fix:* edge rings put back at the joints, and texture-island border vertices held back in decimation (`polish_lib.seam_vertices`).
- *Rule:* decimation keeps joint loops and texture seams. Compare printed detail before and after.

**C8. Texture-island seams.**
- *What:* atlases of 1,300 to 2,400 tiny UV islands, sampled at mip level 2.4 to 3.3 in a level, where an island is about 4 texels across. Padding was fixed only in the app-icon render (`9d71268`).
- *Fix:* every gap in every character and bag atlas is push-pull filled from its island (`polish_lib.push_pull`).
- *Rule:* pad every game atlas island deeply enough for the whole mip chain. Check at play size with mipmaps on.

**C9. Review renders that weren't the game.**
- *What:*
  - Reviews used a 215 px "in-game size" from before the v85 camera (the kid is about 254 to 350 px tall now).
  - The EEVEE review scenes let characters shadow themselves (hair on face, nose on cheek), which the game never does (`shadowCastingMode` off). That made faces look dirtier in the review than in the game, and hid what the shader really did.
- *Fix:* the November 2026 review scenes turn character shadows off and mirror the new rim.
- *Rule:* rule 5. When reviewing, first confirm the renderer matches the game on one known case.

**C10. Assets still showing replaced characters.**
- *What:* after Ren was removed, the icon and the Play feature graphic still showed him. The App Store header art still shows Ren and the scripted Hana.
- *Rule:* when a character changes, regenerate in the same change every asset that shows them: the player cards (`Resources/UI/Player*.png`, `portrait_teen.py`), the icon, stickers, store art and co-op ghosts.

**C11. Backpack fit, one fix after another.**
- *What:* straps slid off shoulders. A pack sat as a lump. Straps read as a vest. Handles were counted as the bag's top. A bag was sized by its wheels.
- *Rule:* fit accessories by body landmarks (the shoulder joints), not by the mesh's extremes, and review them at child scale.

**C12. The player's outline was thinner than the passers-by's.**
- *What:* 0.0018 against 0.0022 of the screen height, although the art direction says the kid's line is the thickest.
- *Fix:* 0.0024. The outline is now measured in pixels, never under 1.25 px, and set back 1.2 cm from the camera so inner folds draw no ink specks.
- *Rule:* check implementation numbers against `docs/ART_DIRECTION.md` when touching a look.

**C13. Rigs and heights.**
- *What:* `CharacterRig` once reset adults to kid size. One shared neck height would have made all four kids the same height.
- *Rule:* rig code never writes absolute scale. Heights live in the roster table. Check feet on the ground.

**C14. The drawn kid faces looked alien (v111, reverted in v113).**
- *What:* `face_paint.py` replaced Kai's, Leo's, Mia's and Zoe's scanned faces with drawn ones:
  - new eyes, sized from the distance between the scan's eyes (half of it wide, 0.42 of it tall), with big irises and two highlights;
  - a short stroke for the nose;
  - a small stroke for the mouth;
  - blush, on a skin flattened to one tone.
  The user's verdict, with screenshots of Mia close up, in game and on the player cards: "They look terrible and look like aliens. The nose, eyes and mouth are rendered the worst. Max's eyes and facial features look good enough."
- *Why:*
  - The style sheet copied the *shapes* of an anime face (big round eyes, a dot nose, a tiny mouth) onto a child's head with realistic proportions. Doll eyes over a real face read as uncanny.
  - Max's face reads as drawn because of its *finish*: an even skin tone, a bold lash line, solid brows, a clean white and iris, and one line for the mouth. Its proportions are realistic.
  - It was shipped on Blender front views and renders alone. The user saw it first on the phone. Rule 4 says to let the user choose from side-by-sides before replacing a character's face.
- *Fix:*
  - Every kid is rebuilt from their own scanned face.
  - `face_ink.py` gives that face Max's finish without redrawing it:
    - a dark lash line along each eye's own top edge (the boys' lines end at the corner, the girls' end in a small flick), with a faint line under the eye;
    - the brows' own outline, filled with one dark brown;
    - the lips' parting darkened along its own curve;
    - the skin flattened, keeping half its shading.
  - Each eye's opening, brow and mouth is measured from the scan. The nose is left as scanned.
  - `polish_all.py --no-ink` ships the plain scans.
  - Reviewed at in-game, menu and close-up distance and on the player cards (`review/characters_v2/faces_v113.jpg`). Approval still to come from the user.
- *Rule:*
  - Restyle a face by its finish (line weight, flat colour, clean edges), never by replacing its features' shapes or proportions.
  - Keep each kid's own eyes, nose and mouth.
  - Show a face change to the user as a side-by-side before it ships.

**C15. Faces folded as the head nodded (every rigged character, fixed in v114).**
- *What:* the user's recording of the title screen showed Hana's face creasing across the mouth and chin as she watched the ball. The numbers:
  - 38% of Hana's face above the Head joint, and three-quarters of her jaw, were partly on the Neck bone;
  - Mom had over 1,000 face vertices on the Neck, the Shopkeeper about 400, and Max's and every kid's jaw some.
  The menu nods the head 6 to 20° down to watch the ball, and a slide 44°. The part on the Neck stayed behind, and the lower face squashed into the neck. The face lean (C2) took only vertices at least 90% on the Head, so Hana's lower face also kept the scan's noisy normals. The light/shade step then ran across it as a jagged crease that crawled as she moved.
- *Why:*
  - The scans' automatic rigs blend Head and Neck over the whole lower face. C6 was fixed for the scripted kids (v79) but never checked on the rigged scans. That is rule 6 again.
  - Every review used a still pose with the head level.
- *Fix* (`polish_lib.rigid_head`, run on every character by `polish_all.py`):
  - The whole head moves with the Head bone: everything above a cut through the Head joint that dips forward under the chin. Below the cut, the weights blend back to the neck over 12% of the head's height.
  - `face_lean` now takes every head vertex, the jaw included. It leans toward a sphere behind the face instead of one flat forward direction, so the face shades as one rounded shape: lit whole in front light, with a clean curved edge when the sun is to one side.
  - Checked at the menu's -20° and the slide's -44°: `review/characters_v2/head_tilt_v114.jpg`.
- *Rule:*
  - Check skin weights by numbers on every new character: the face is 100% on the Head.
  - Review heads in motion, nodded and turned, never only in the idle pose.

**C16. White tears in dark clothes and hair (every scanned character, fixed in v114).**
- *What:* white specks, slivers and streaks in Hana's jacket and trousers, Max's jeans and the other kids' clothes. The user: "lots of white tears in all the characters, from hair to face to clothing".
- *Why:*
  - A render of the vertex colours alone showed them all; the atlas alone was clean.
  - The rigs' `paint()` (`meshy_boy.py`) gives each garment's faces the garment's colour and divides its texels by it. Faces whose texel wasn't recognised as the garment (light folds, highlights, unpainted seams) stayed "no part": a white vertex colour times a light texel.
  - Cutting to 32k triangles made them bigger.
  - The shop's recolouring left them white.
  - Most of them share no edge with their garment (the scans are cut along every colour line), so a check by connected faces found almost none.
- *Fix* (`polish_lib.absorb_tears`): by surface, not topology. A greyish face of no part joins garment p when p covers 65% of the surface within 2 cm of it (the face itself not counted). This moved 969 of Hana's faces. Skin never moves (its colour is too saturated), and wide features keep their middles: her jacket's "H", the hoodie, the striped cuffs.
- *Rule:* diagnose a colour fault by splitting the render: vertex colours only, atlas only, rim off, ink hull coloured, outfit parts (`review/cartoon/render_scenes.py` `DIAG`). Look at a garment in the parts view before trusting it.

**C17. The rim light drew white scratches on dark clothes and hair, and the review renderer lagged the shader.**
- *What:* with the tears gone, thin white lines remained along every crease of Hana's black trousers and every clump of her hair.
- *Why:* `ToonCharacter`'s rim whitened the colour under it by 45%, whatever that colour was. On near-black cloth (0.02) that adds 0.45 × 0.3: a light line on every inner crease, pocket edge and hair clump, not only round the silhouette. C3 tinted the rim, but not enough for black.
- *Fix:* the rim is whitened by 45% of the colour's lightness (its brightest channel). A light shirt and skin keep their bright edge, and dark hair and clothes keep only a faint sheen of their own colour.
- *Also:* `review/cartoon/render_scenes.py` had never received v111's rim, its characters-cast-no-shadows, or the close-up review scenes. They lived only in a scratch copy, so its renders were not the game's (C9 again). It is now up to date, with the diagnostics above.
- *Rule:*
  - A light term that adds light scales with the surface's own lightness.
  - Copy every scratch copy of a review tool back before committing. The mirrors listed in `CLAUDE.md` include the review renderer.

**C18. Mia's right eye (v114).**
- *What:* after C14, the user found Mia's own right eye (on the left as we look at her) narrower and squinting next to her left: "Take a reference from the right eye and fix it."
- *Fix:* `face_ink.py` replaces it with her left eye, mirrored across the middle of the face, before the lash lines are drawn. Inside the replaced eye the result is written as it is, not as a change, or the old iris showed through as grey specks.
- *Rule:* when one side of a scanned face is worse, mirror the good side rather than redraw it. That keeps the kid's own eye, which C14's rule asks for.

**C19. The torso was one rigid block (every character, fixed in v115).**
- *What:* the user's recordings of Hana and Max dribbling: "the characters' bodies are so stiff, the chest to abdomen part. Because of that hand movement, it looks like hanging from a fixed thing."
- *Why:*
  - `CharacterRig` swung the legs, knees, arms, elbows, head and bag about the body's side axis, and pitched the whole body as one piece.
  - The models' Hips, Spine and Chest bones were never moved; they weren't even on the rig. So the arms swung from a ribcage that never moved.
  - In a real stride:
    - the pelvis turns with the legs and the ribcage the other way with the arms;
    - the trunk sways over the standing leg and dips as the legs reach apart;
    - the chest breathes all the while.
- *Fix* (`CharacterRig.Torso`, worked out from the limbs' own pose, so every animator gets it):
  - the chest turns up to ±15° with the arms' swing, using the sine of each arm's swing so both arms raised overhead turn nothing;
  - the pelvis turns up to ±10° the other way with the legs;
  - the torso sways 3° over the straighter leg and dips 2° at full stride;
  - the chest breathes 0.9°;
  - the head turns, sways and dips back, so the eyes stay level and ahead;
  - the builder puts Hips, Spine and Chest on the rig (v115).
- *Why no weight change:* the torso's weights already blend Hips to Spine to Chest over about 30 cm, so the turn bends through the waist rather than creasing.
- *Reviewed:* `review/cartoon/render_scenes.py` mirrors it (`TORSO=0` gives the old rigid torso). Its `gait` scene renders a run or walk cycle: `review/characters_v2/torso_run_v115.gif`, `torso_walk_v115.gif`.
- *Rule:*
  - Animate the trunk, not only the limbs: a procedural gait needs the pelvis and chest turning against each other.
  - Review motion as motion (a whole cycle), not as one pose.

**C20. The review boards showed faults the game doesn't have, and hid ones it does (found and fixed in v116).**
- *What:* the user, looking at the v114 boards, saw black spots on Kai's face (and brown patches on every chin). The user also saw white tears left at Hana's and Max's trouser hems, on Max's belt, and along Mia's hairline.
- *Why:*
  - **The review renderer.** `review/cartoon/render_scenes.py` drew the ink hull with a Solidify modifier on the figure itself. That threw away the figure's own normals: the smoothed, face-leaned normals the game shades with. Every face was therefore shaded with the scan's raw normals: brown patches, a jagged chin.
  - **The hull's set-back.** The hull was also never set back from the camera as `ToonCharacter`'s `_OutlinePush` (1.2 cm) sets it, so it poked through round every nose and mouth corner as black spots.
  - The game had neither fault. It took a split render (`DIAG=crack` turned the spots magenta) to see it.
  - **The tears were real.** The v114 rule needed the garment to cover 65% of the surface around a face. A trouser hem's pale band sits against the white shoe, a belt's streaks against the hoodie's hem, and a fringe's tips against the face, so the other untagged thing outvoted the garment.
- *Fix:*
  - The renderer's hull is now a copy of the figure (its own surface drawn as nothing), set 1.2 cm back from the camera. The figure keeps its normals. `OUTLINE_PUSH=0` gives the old hull.
  - **The player cards had the same fault.** They are Blender renders shipped in the game: `portrait_teen.py` put the same Solidify on the figure, so the cards' faces had black specks round the nose. The cards, `review_teen.py` and `review_poses.py` now share `tools/blender/ink_hull.py`, and the six cards are rendered again.
  - `absorb_tears` has a second test: the garment against only the neighbours that look like the face (texels within 0.2), while that kind stays sparse round it (a streak, not a printed letter: Leo's "01" and Hana's "H" stay). It runs four rounds, so a band a few faces wide goes too. The face must also be nearly grey, white or cream (saturation under 0.21). On the first try, Mia's beige patterned headband (0.25 and up) passed as "sparse streaks" and went black; the review board caught it before it shipped. Hana's cream cuff stripes (about 0.17) still go.
- *Rule:*
  - Before trusting a review renderer, check it on one known case against the game, and check that each modifier keeps what the game reads (custom normals, vertex colours, UVs). C9 again.
  - Look at a garment's edges (hems, waistbands, fringes) in the parts view, not only its middle.

**C21. Feet and legs through the pavement in a slide, a kick and a landing (every playable kid, fixed in v119).**
- *What:* the user's screenshots of Mia sliding: her legs went into the ground. Posed on the shipped models and measured
  against the ground (a Blender copy of `CharacterRig` and `KidAnimator`), the slide put the back foot and shin 17 to 25 cm
  under the pavement on all six kids, the front heel 5 to 9 cm. The landing crouch sank 1 to 5 cm, a kick from a stride
  2 to 3 cm, and even the run's passing step 2 to 3 cm.
- *Why:*
  - The poses are joint angles, written for the procedural kid long ago. Nothing ever checked where the model's surface
    ends up: the feet can't point (no ankle on the rig), so a shin folded back under a level thigh, as the slide's back
    leg was, drives the foot straight down.
  - Every pose review (`review_poses.py`) framed the figure on its own, with no ground line.
- *Fix:*
  - The slide's back leg is tucked with its knee up (the thigh 45 degrees above level) and its foot planted ahead of it.
  - `CharacterRig` keeps the model above the ground: `LevelBuildKit` measures about 140 points on each model's surface
    (the extremes of the soles, shins, knees, seat, forearms and hands, each in its bone's frame), and after every pose
    the body is lifted just enough that none is lower than the lowest stands at rest. Every animator gets it: the kid,
    the menu's keepy-uppies, co-op ghosts, passers-by.
  - Measured on all six kids after the fix: at most 0.6 cm under the ground in any of the poses above.
- *Rule:* a pose is checked against the ground on the real models (the depth below it, in cm), not only by eye from
  the side. A pose written as joint angles needs a contact constraint, or it drifts through the floor on the next model.

**C22. White and stray patches in any outfit but the character's own (every scanned character, fixed in v119).**
- *What:* after v116, the user still saw "white tears/patches across all the models", with Mia in the game as the
  example: a white collar, white slivers at the sleeves, red and white streaks down her shorts, khaki flecks on her
  socks, a zebra of green and pink in the shorts. They were playing in the Holiday kit (a teal top, khaki shorts).
- *Why:*
  - The shop recolours outfit parts 1 to 3 only. A face painted the garment's colour but left with no part keeps its
    own colour; a garment-tagged face on something else takes the garment's new colour.
  - C16 and C20 absorbed only *greyish* faces of no part, and every review board was made in each character's own
    colours, where a white face on a white shirt, a red one on red shorts or a navy one on navy jeans is invisible.
  - The atlas divides a garment's texels by its colour channel by channel. For a saturated colour (Mia's red shorts)
    the faint green and blue channels blew up into stripes that show in any other outfit.
  - The other characters had the same faults: Max's navy waistband and turned-up hems, the red and white slivers in
    Kai's plaid, and so on.
- *Fix:* `polish_lib.settle_parts`, run on every character by `polish_all.py`:
  - a face takes the part covering most of the surface round it (bare skin has no vote for a face that isn't skin, and
    a face's own kind has none) when a good share of that part there is painted like it, or when it is a sparse pale
    streak; skin never joins a garment, and prints and logos keep their part (their colours are unlike the garment's);
  - a stray island of a garment on something else (the shorts-tagged flecks on a sock) leaves the garment and shows its
    texel as painted;
  - a face moved into a garment takes its vertex colour, and its texels become their light against the garment's colour,
    in grey; a saturated garment's texels become grey the same way (no zebra);
  - along the hairline: the scans painted Max's fringe (white highlights, grey tips, brown spots) across his forehead,
    where the modelled fringe doesn't lie, and the shading turned it into the "black spots". Light paint on the skin
    within 2 cm of the hair takes the colour of that face's own skin; slivers of no part on the hair's edge take the
    skin, and specks inside the hair join it. Partly done: the white slivers and dark spots are gone, the grey tips are
    much fainter but still show on his card (`review/characters_v2/max_forehead_v119.jpg`).
- *Then the brows (the user's word: "Don't wipe out the eyebrows, keep them as they were").* The first hairline rules
  painted over the jogger's brows (her scan tags them as hair) and broke Mom's (they lie within 2 cm of her hair).
  Now nothing in `settle_parts` touches a face or texel within 7 mm of a mark on the face that isn't joined to the hair
  (a brow, even one tagged as hair, the eyes, the lips), and the hairline steps take only light paint. Checked by a
  pixel difference of every head before and after (`heads_changed_pixels_v119.jpg`): the changes lie on the hairlines
  only.
- *Rule:*
  - Review every character in an outfit that is not its own (the Holiday kit: `outfit_render.py`) as well as its
    default. A fault that only shows in one colour is still a fault.
  - A clean-up of paint near the face is checked with a pixel difference of the heads before and after: it must not
    reach the brows, eyes or mouth.
  - A rule that moves parts by colour judges once on the parts as they came, never round by round from its own
    results (each cascade here ate a garment: a shirt into the hair, cream sleeves into a jacket), and compares colours
    by ratio, not difference (every dark colour is near every other by difference).

**C23. Still white on Mia; walking on the spot on a platform; a splash nobody saw; a vibrating leg in the slide (v120).**
- *What:* the user's screenshots and recordings after v119:
  - Mia in her own colours still showed white streaks down the sides of her red shorts and white specks along her hair;
  - on Duck Pond's moving platforms the kid kept walking on the spot instead of standing still;
  - a ball or a kid falling into water showed only the word "Splash!";
  - in a slide, one leg vibrated.
- *Why:*
  - **Mia.** Decimation to 32k triangles left a few very large triangles (up to 20 cm²) across her shorts' white side
    stripe, the red and the bare leg at once. A triangle has one outfit part, so no tagging rule could fix it. The rest
    were bands of white faces (a stripe is mostly itself round each face, so C22's per-face rules left it), and faces
    half white, half red, whose average colour is a skin-like pink, so the skin guard kept them out.
  - **The platform.** `KidAnimator` drove the walk cycle from the body's world speed. A moving platform carries the
    body, so standing still on it read as walking.
  - **The splash.** It was raised by the water's `LoseZone`, two metres under the surface: under the water and as the
    screen faded. It was also only 14 small drops.
  - **The leg.** The slide's trailing leg was "scuffed" on purpose: ±5 degrees at 3 to 5 swings a second, the knee half
    as much again, plus a judder of the body.
- *Fix:*
  - `polish_lib.split_mixed`: a large triangle painted in two colours is split (twice at most, the largest first, about
    1,000 triangles a figure at most), so the pieces take their own parts. `settle_parts` judges skin by a face's own
    texels (at least a quarter skin-coloured), joins small pale clusters near a garment or the hair to it whole, and joins
    a mostly pure-white face to the garment closing it in. A face with bare skin in its texels never joins a garment.
  - `KidController.StrideSpeedX` (the speed less the surface's) drives the gait.
  - `WaterSplash` at the surface of every trench, stream and tidal channel raises the splash where things go in, and
    `FxDirector.Splash` draws foam rings, a crown of drops, a column, spray and the drops landing back.
  - The slide holds its pose: no scuff, no judder.
- *Still to do:* a few small white slivers by Mia's fist and the shirt's hem at her waistband remain.
- *Rule:*
  - An effect is raised where it shows, and checked in a recording or a frame-by-frame look, not only in the code.
  - An animation driven by speed uses the speed over the ground under the feet.
  - Don't add a high-frequency wobble to a held pose: at 60 fps it reads as a fault, not as life.
  - When a fault survives tagging fixes, look at the triangles themselves (a face-ID render: `outfit_render.py`'s
    approach), not only at the tags.

## D. Art direction and look

**D1. A golden-hour haze hid the kid** (before v37).
- *Rule:* the player's legibility constrains every lighting and grade change.

**D2. Tuning by eye drifted from the references.**
- *What:* v38 "calmed" the palette. v67 measured screenshots against the references and found the sky, paving, whites and shadows all off, because three warm multipliers were stacked.
- *Rule:* measure screenshots against the reference numbers in `docs/ART_DIRECTION.md`. Never tune by eye, and never stack tints.

**D3. The character blended into the ground.**
- *What:* a sage shirt and khaki shorts on grass and paths.
- *Rule:* check character colours against every chapter's palette and every filter.

**D4. California replaced the original town** (v69), and the user wanted the original back (v71).
- *Rule:* add a new regional look beside the shipped one, never in its place, and keep the random draw order.

**D5. Filters damaged faces.**
- *What:* lines traced from the picture turned eyes into black dots. A cartoon outline was drawn over a cheek.
- *Fix:* a figure code in alpha; lines only from depth and normals; outlines only on the far side of an edge.
- *Rule:* filters never derive lines from texture, protect faces through the mask, and are reviewed on faces at 3x.

**D6. Repetition from shared seeds.**
- *What:* every level of a chapter had the same background.
- *Fix:* `StreetBuilder.LevelSalt`.
- *Rule:* salt seeds by level, and audit repetition when content is added.

**D7. Texture detail raised with no memory line** (the Coast atlas at 4096², TownMap.jpg at 23 MB uncompressed).
- *Rule:* every texture increase states its compressed memory per platform.

**D8. Add-ons that only reskinned the same levels (v69 to v121, replaced in v122).**
- *What:* California and Florida put the original town's levels in another country's streets. The user, after Florida's
  Home Street: the cities were "boring with same gameplay styles". In v122 the add-ons became five cities, each with its own
  routes, transit, errands and mini-games (`docs/CITIES.md`).
- *Why:* a new place was treated as a look over existing play, so each one cost a whole kit and gave the player nothing new
  to do. Florida's own drawbridge, golf cart and sprinklers (v121) were the first play of a place's own.
- *California, retired:* not one of the user's five cities. The question about it closed unanswered (the session's worker
  restarted), so the recommended option was taken: it left the picker and its `_CA` scenes are no longer built; its Coast
  kit and builder code stay, since Florida shares them. To bring it back: add it to `Cities.All` and build its scenes again
  in `GeneratedContent`. Don't re-add it unasked.
- *Then (v123):* the user asked for "all the levels from Florida". Making Florida's remaining chapters into more `_FL` copies
  would have broken this rule again; Florida got the three routes of `docs/CITIES.md` instead (twelve legs, three of them
  mini-games), and its nine interim copies were dropped. Their own play (the drawbridge, the sprinklers, the golf cart, the
  storm) moved into Florida's legs.
- *Rule:* a new place brings new play: its own routes, how people there get around, and what a child there does on the way.
  A reskin is not a city. When a request reads either way ("the rest of Florida's levels"), build it to the city's design.

**D9. A city's own routes in another city's streets, with grey boxes for its things (v123, redone in v124).**
- *What:* Florida's twelve legs had their own play but were built in a Kamakura chapter's street ("the look chapter"):
  Kamakura's houses, poles, hills, train station and bandstand under Florida's light, its obstacles Kamakura's bins, crates
  and (on the Riverwalk, built as the beach) boulders. Its own things were boxes: the scooters were a flat teal deck on the
  footpath, the arcades slabs on posts, the Metrobus a white wall with boxes sliding past behind it. The map was a flat
  drawing of rectangles. The user, from the phone: the bus level "not at all understandable", "green flat objects on the
  footpath. Don't understand what they are", the levels "naive and repeatable and redundant to Kamakura".
- *Why:* v123 shipped the play first and left the look "until Florida's own kit is modelled". A stand-in that is only a
  colour and a size doesn't read as anything, and a borrowed street makes a new city look like the old one, whatever its
  play.
- *Fix:* the Miami kit (`kit_buildings_mia.py`: 41 models, Little Havana to the bay), royal palms and banyans, and a plan per
  leg (`tools/blender/miami_plan.py`, `MiamiDistricts.json`) that the game builds (`StreetBuilder.Miami`) and the preview
  renders, so the preview is the game. The Metrobus is the kit's bus, its near side taken away as the kid boards, the
  district's street sliding past its windows. Every grey box became its model; the stops, the obstacles and the map are
  Miami's.
- *Rule:* a place ships with its own things modelled. Nothing goes to the user as a coloured box standing for an object,
  and no city borrows another city's street, stops or obstacles. Render every leg through the game camera
  (`preview_street.py --miami`) before it goes in.

**D10. What the first pass at a city's own look missed (v124, finished in v125).**
- *What:* v124 gave Florida's legs their own districts, but the play pieces were still built by chapter from the original
  town's kits: the slide-unders (Kamakura's market stall, scaffold, boat on trestles, apple bough, roll shutter, pipe rack,
  boom barrier, oak bough), the pit's cones and barrier, the produce crates, the crossing's signal and its little cars, the
  wooden notice boards, the checkpoint flags, the park fountain, the pelican (a gull scaled up), the building site's crane in
  the plan, Kamakura's trees and shrubs, the walkers' wardrobes, the shade on the road. Riverside Street (FL2-1) still had the
  suburb's street; the people mover's ride was boxes; the school was signed "Seagrove High"; every leg played one of Kamakura's
  ambience beds. The user: "make sure nothing overlaps between Kamakura and Florida".
- *Why:* the v124 audit looked at the scenery a leg places, not at what each track piece builds; a piece picks its look by
  chapter, and a Florida leg is built as a chapter.
- *Fix:* Miami versions of every piece a Florida leg uses (same solids and play: `<Look>MIA` for the slide-unders), chosen by
  `TrackBuilder.MiamiLook`; the Animals kit's pelican; FL2-1 in the plan; the ride from the kit; Miami's soundscapes.
  `MiamiKitTests` now fail if the plan places anything but Florida's own models, if a Florida leg uses a slide-under look
  without its Miami model, or if a Florida stop has no Miami set piece.
- *Rule:* when a city gets its own look, audit every track piece its layouts call (`grep -o "t\.[A-Z][A-Za-z]*(" ...`) and
  what each builds for that city, not only the scenery; then hold it with a test. What may be shared: the kid, the ball, coins,
  stickers, the cast's bodies (dressed for the city), dogs and pigeons, the sky.

**D11. Kamakura, the original town, was a generic town (v126).**
- *What:* Kamakura's streets were built from the shared kits, which had grown toward no city in particular: picket
  fences, American post boxes and garages, a bodega-style "KOTORI MART" and a striped fruit awning, Victorian lamps, spruce
  forests on the hills, palms on the beach, sea gulls. Next to Florida's own districts it read as "anywhere". The user asked
  for Kamakura to be made as real as Florida and gave a brief (`docs/KAMAKURA_BRIEF.md`).
- *Why:* the first city's look came before there was a second city to tell it apart from; nothing ever asked "is this
  Japanese?" of a shared model.
- *Fix:* Kamakura's own kits, taken point by point from the brief: homes with kawara and standing-seam roofs, block walls,
  board fences and gates (`Kamakura`, `kit_buildings_kmhouse.py`); shops with noren, signboards and lanterns and invented,
  correctly written names (`kit_buildings_kmshop.py`); torii, temple gate, shrine hall, stone lanterns and steps, moss walls,
  ema, mirrors, phones, vending machines, the tram, its poles, track and crossing, kei vehicles, a scooter and a rickshaw
  (`KamakuraStreet`, `kit_buildings_kamst.py`); black pine, camphor, cedar, cherry in leaf, bamboo, hydrangea, azalea and
  persimmon; black kites and crows. `StreetBuilder.Kamakura` uses them when the kit is present (`StreetBuilder.KM`), with a
  flush lane and a green walking strip in place of the raised kerb. `KamakuraKitTests` fail if a name the builder uses is
  missing from its kit.
- *Still to do:* the beach's lifeguard tower and the building site's warehouses are still the shared ones; some park lamps
  are still the Victorian lamp; mirrors, bus poles, manholes and tactile strips are modelled but not yet placed.
- *Then:* the audit after it (`docs/KAMAKURA_AUDIT.md`) found that v126 reached the streets but not the play: the track
  pieces, the stops, home and school, the walkers, sounds and words were still the shared town's. Same lesson as D10.
- *Rule:* every city, the first one included, is checked against its own brief: a shared model stays only if it would be
  normal in that city's street. When a new city gets its own look, look again at the old ones beside it.

**D12. The cartoon filter's orange cast; a sketch that was not black and white (v134, from the user's screenshot).** The
classic cartoon was matched to 1950s desert cartoons: warm colours multiplied toward orange (`ClassicLook.warm`),
shadows toward brown (`shadowWarm`), quiet colours lifted hard (`vibrance` 1.8: beige to ochre, sand to gold). Over
Miami's cream stucco and concrete, already warm in Florida's 5,000 K sun, the whole street went orange: "a yellow/
orangish tint". The pencil sketch kept a colour wash and the figures 75% of their colour, on cream paper. *Fix:* the
cartoon keeps each thing's own hue (warm and shadowWarm 1, vibrance 0.35, saturation 1.1, a neutral black outline, a
natural blue sky); the sketch pass returns grey whatever its colours are set to, and its comic words are grey.
`FilterLookTests` holds both. *Rule:* a grade matched to one reference (a desert palette) must be checked on every
city's own colours, not only the reference's; "black and white" is enforced in the pass, not left to a colour
setting a scene might have saved.

## E. Levels and world

- **E1. Every level had chapter-1 scenery.** A new-scene call unloaded the level definition. *Rule:* pass data into scene builders explicitly; never hold asset references across a new-scene call.
- **E2. A scene that wouldn't load.** Four components shared `RunMarkers.cs`. *Rule:* one component per file (enforced by `ScriptConventionTests`).
- **E3. Holiday Run trenches nobody could cross.** *Rule:* every gap and wall size comes from `JumpReach`; `LevelFeasibility` checks every layout.
- **E4. The kid trapped in L16 by pushed crates.** *Rule:* physics props near a choke point get one-way constraints and reset-ahead, and every mode has a "Stuck?" escape.
- **E5. Floating cones, a stream you couldn't fall into, a pier starting in mid-air.** *Rule:* place props after the ground is known; every structure has believable access.
- **E6. Coins the drawn kid ran through.** The capsule was 1.2 m tall; the drawn kid is about 1.6 m. *Rule:* collision matches the drawn character; run `tools/coin_audit.py` after a layout change.
- **E7. Camera framing back and forth** (v85 closer; v86 closer still, reverted). *Rule:* any camera change passes a collectible-visibility sweep and the control-layout check.
- **E8. The map and the levels disagreed.** *Rule:* one layout is the source of truth, with validators in both directions.
- **E9. A flower obstacle that looked painted on the floor (fixed in v119).** Chapter 1's low obstacle was sometimes three of the Plants kit's flower patches standing straight on the paving, their leaves flat on it, with nothing to say what blocks the way. *Fix:* a raised bed: a stone kerb, soil and the patches growing out of it (`FlowerBed`). *Rule:* an obstacle reads as solid from the side: give soft things (plants, cloth) a hard base or container.
- **E10. A bridge rail that would have hidden the ball (caught in preview, v121).** Florida's canal balustrade was first put on the road's edge, between the camera and the lane: at 1.15 m, 1.65 m in front of the kid, it would have hidden the ball and the kid's legs all the way across the drawbridge. *Fix:* the balustrades stand along the canal's banks behind the street, and the leaves keep their own rail behind the lane. *Rule:* nothing taller than about 0.4 m stands between the camera and the lane (z < -1.5) where the kid plays; check every new set piece in `preview_street.py` through the game camera before it goes in.
- **E11. Water across the street is not a side street.** A canal added as an `OpenArea` would get a side street's road paved over it (`SideStreetEnd`), and the verge behind the lane bridges every gap. *Fix:* `TrackBuilder.Canals`, which the back rows, far rows and the verge's slabs keep out of, plus a `QuietArea` for the front lots. *Rule:* a feature that crosses the street's depth gets its own list; don't overload `OpenAreas`.
- **E12. One set of routes was assumed everywhere (found in v123).** Giving Florida routes of its own touched the map (one picture, one layout, `RouteTable.All` in every loop), unlocks (a city's first leg waited on the other city's last), Next and the album (mini-game legs with no sticker), the music (chosen by the scene's suffix), co-op (location by chapter), tests (23 story levels counted) and the stops' set pieces. *Fix:* routes, maps and the story order are per city (`RouteTable.ForCity`, `TownMap.Use`, `Cities.Has(level)`, `LevelUnlocks.PreviousStory` stops at a city's edge); lookups by level id search every city (`RouteTable.Every`); `GeneratedContent.LevelTable` stays Kamakura's for its tests and `CityLevelTable` gives another city's. *Rule:* where the city matters, never loop over `RouteTable.All` (that is Kamakura's): ask the city for its routes. A level id is unique across cities.
- **E13. Road markings under the road (v126, fixed in v127).** v126 laid Kamakura's home street flush (the road strip at lift 0), but the edge lines, centre dashes, drains and manholes were still placed at the old sunken road's height (`top - 0.14`), 14 cm under the asphalt. Found by the Kamakura audit, not by a render: the preview draws its own road. *Fix:* `StreetBuilder.Slab` puts them on Kamakura's flush road. *Rule:* when a strip's height changes, grep for everything placed at the old height (`- 0.14f`, `RoadNear`, `RoadFar`).
- **E14. The mini-games removed (v128).** The user: "remove the mini games completely and do not replace them with anything else in both Kamakura and Florida". Florida's three mini-game legs (FL1-2 The Metrobus, FL2-2 Uncle Rey's Boat, FL2-4 The Drugstore, v123 to v125) had grown hooks well beyond their own scripts: the HUD's and the guide's star lines, a route-leg path through `LevelManager`, the level definition's flag, the errand they handed over (the science project, its Delivered badge, the downpour's stake), the plan's districts and the bus's moving street strip, two kit models, the map's nodes, strings in both languages, and the leg numbers of every leg after them. Kamakura's two were only in the design (`docs/CITIES.md`). *Fix:* all of it out, using the commits that added them (`git show --stat 7122d16`, `64840b0`) as the checklist; the legs after them renumbered so each route's legs are 1, 2, 3 again, with save version 3 (`Progression/FloridaLegs`) moving a player's records, stickers and trip times with their legs; the plan's districts seeded by their old ids so the reviewed streets stay identical; `FloridaRoutesTests.TheMiniGamesAreGoneForGood` holds it. *Rule:* to remove a feature, walk the diffs that added it file by file rather than grepping its name: the hooks that matter don't carry it (a `HasStickerSlot`, an `AfterRig`, a "Retry, not Next" line). Renumbering persisted ids needs a save upgrade in the same change (H7).
- **E15. Gates that stopped nothing, rain that hung in the air, gulls at chest height (v129, from the user's screenshots).**
  - **Gates:** the drawbridge's arms fell *along* the street behind the lane, so they read as a fence the kid walked in front
    of. Nothing held the kid back, so they could stand at the hinge while the leaf rose through them. *Fix:* the arms fall
    across the path toward the camera, cut to end at the lane's front edge (E10). While an arm is down, a one-way blocker at
    its post, 2.4 m back from the hinge, stops the kid and the ball coming toward the water; it never traps someone already over.
  - **Rain:** static streak quads, built once and toggled, read as scratches on the screen. The downpour's only stake was the
    removed errand (E14). *Fix:* `World/RainCurtain`, falling streaks round the camera with splashes and puddle ripples, none
    under the arcades, in one mesh. The light dims with each burst through `WorldLook`, and a burst out in the open slows
    the kid's run. Its warning pill sits under the HUD card, not across its edge.
  - **Birds:** startled pigeons and the sky's pigeon and crow flocks flew on the gull's rig. The gull's body can't be
    painted, so they flew as white gulls, some at chest height. *Fix:* they fly on the black kite's rig, painted all over.
  - **The low kerb** in Florida was a bare grey block. It is now a raised planting bed (E9).
  - **Puddles** were a pale blue fill inside a dark ring, a sticker. They now mirror the street, with a soft wet edge.
  - *Rule:* in a side view, something that crosses the path (a gate, a barrier) must fall across it toward the camera and
    must physically stop what it stops. Weather moves. A model standing in for an animal must be paintable all over.
- **E16. Brown blocks, a ball stuck on the awnings, green tiles and a stray red light (v130, from the user's screenshots and
  screen recording).**
  - **Platforms** were a plain box in the chapter's colour (sand-brown in Miami's parks: "what are those brown blocks?"), and
    ramps a tilted slab in the air. *Fix:* `LevelBuildKit.Dressing` builds a retaining wall with its coping. In a park it has
    a lawn top and shrubs along the back (Kamakura granite, Miami coral keystone); in a street a paved top; on a site
    concrete with a safety edge. A ramp is a solid wedge under its slope.
  - **Stranded balls:** the market's bouncy awnings (2.6 to 3.2 m) let a ball settle out of reach with no way back but a
    restart, and Miami's arcade canopies let it pass through the canvas.
    - The awnings are striped canopies on poles, marked `BallTrap`.
    - The arcade canopies are a low-ridged collider: a ball kicked into one bounces back, and one landing on top rolls off.
    - `LevelManager.BallOutOfReach` catches any other resting ball more than 2.4 m above a nearby kid's feet for 3.5 s,
      with the alert "The ball can't be reached - back to the checkpoint".
  - **The green strip** in Kamakura was 2.5 m of green paving slabs, which read as tiles. It is now about 1.5 m of green
    paint on the asphalt.
  - **The drawbridge's red lamps** were discs on the tender's tower wall. They are now a two-lamp signal head on a mast
    before each gate.
  - *Rule:* every collider the ball can land on must either be reachable or say it strands the ball. Anything the camera
    sees across the lane must answer the ball the way it looks (a canopy stops it).
- **E17. The ball still went through a shop canopy (v133, from the user's recording of Biscayne Boulevard).** v130 gave the
  level's own arcades a canopy collider, but the Miami district placed the same Deco block as scenery, its wall at 2.35 m and
  its 3 m canvas hanging 0.7 m in front of the ball's plane (z 0), with no collider: the ball flew up behind the canvas and
  fell back through it. Downtown had one too. v130's fix looked at the play pieces only, not at the scenery made of the same
  models. *Fix:* nothing that stands behind the lane may reach over the ball: `StreetBuilder.Model` (every street model in
  both cities) and `miami_plan.py` push such a model back until its front is 0.45 m behind the ball
  (`StreetBuilder.ClearOfTheBall`, a test over the whole plan). The district's arcades now stand at 3.5 m; nothing in
  Kamakura's streets came closer than 0.65 m. *Rule:* a rule about how a model meets the ball holds wherever the model is
  placed; audit the scenery against the ball's plane, not only the play pieces.

- **E18. The ball through the street sweeper's cab, after two canopy fixes (v136, from the user's recording; "run a strict
  audit for this pass-through across all levels and cities").** The sweeper's only collider was a box from 0.3 m to its flat
  back at 1.2 m; the kit's truck stands 2.43 m with its cab over the front, so a ball chipped onto the back rolled into the
  cab and out of its front. The same shape of bug as E16 and E17: a piece's collider is drawn by hand for the kid's play
  (the part to ride, jump or slide under), its model is the kit's, and nothing checks one against the other. Measuring every
  in-lane model where it crosses the ball's plane (`tools/ball_solidity/silhouette.py`, Blender) showed the same gap on the
  golf cart's body, the domino table's stools, the arcade canopies' thickness, a standing scooter's handlebar, the crane
  load's beams, the slide-unders' posts above their gaps. Fixing them one by one is how it kept coming back.
  - *Fix:* every level's build ends with `LevelBuildKit.BallShells`. It finds every mesh surface crossing the ball's plane
    (|z| <= 0.17 m) that is not on a collider and adds ball-only colliders there (`World/BallShell` ignores the kid's
    colliders, as pedestrians do, so no jump, slide or ride changes). They go on the piece's own moving body, so the cab rides
    with the sweeper. Pickups, zones, animals, plants, people, water, lips under 12 cm and anything that moves without a
    body are left alone. Each level's build logs what it shelled and what it left out.
  - *Rule:* a collider drawn by hand is checked against what the player sees, by code, every build. Where the kid's play
    needs a smaller collider than the model, the ball still gets the model's.

- **E19. Road crossings into a shop and out of the sea, and columns in the air (v139, from the user's screenshots).** The
  Miami plan (`miami_plan.py`) kept its buildings out of the stops, the school, the canals and the arcades, but nobody told
  it where the side streets were. So a coffee kiosk, a bench and a tower's podium stood across Biscayne Boulevard's, and on
  Bayfront the bay ran right up to the crossing while the school's lawn was laid over its road. The museum's canopy columns
  stood 3 m in front of its plinth but started at the plinth's height, 1.2 m, so they hung over the lawn; its hanging gardens
  stopped short of the canopy, and the canal dock's boat hung in its lift with no cradle.
  - *Fix:*
    - The plan keeps every side street clear (`crossings` from the layouts, `in_street`), and on the waterfront the land
      starts before a crossing.
    - The builder leaves out any district model still in one and cuts the district's land round it
      (`StreetBuilder.InSideStreet`, `Without`).
    - The three models are fixed.
    - `tools/model_support/support.py` checks every kit model for pieces that touch nothing on the way to the ground.
  - *Then:* Kamakura's streets were already clear: their dressing asks `Blocked` and `OnSideStreet` at every placement.
  - *Rule:* a generator that places scenery must be given every corridor the play uses (stops, canals, side streets), and a
    model's every piece must reach the ground through the pieces it touches.
  - *And:* a single model may be copied out of a kit's rebuild only when the rebuild's atlas is byte-identical to the
    committed one. The Miami atlas predates v128's removal of two models from the script, so today's script packs a
    different layout; the museum was rebuilt from the v125 script with the fix applied, and its atlas matched exactly.

- **E20. The kid walked into the sweeper's cab, and Bayfront's side street still came out of the bay (v140, from the user's
  screenshots).**
  - *Sweeper:* the v136 ball shells covered the cab for the ball only, on purpose: they ignore the kid so no tuned jump
    changes. But the sweeper's designed collider was only its back (0.3 to 1.2 m). Nothing stopped the kid walking from the
    back into the cab, so the cab was a ghost for the kid.
  - *Bayfront:* v139 moved the bay's end 4 m before the crossing and put land under the road. From the game camera the road
    still ran back along the water's edge into an empty lawn, so it read as a road out of the bay.
  - *Fix:*
    - The cab has its own collider on the sweeper's body, up to its 2.43 m roof. The way past is up onto the back and over
      the cab with a double jump (it peaks 2.07 m up against the cab's 1.23 m).
    - The side street now leads to a port: the quay along the water's edge, cranes, freighters alongside, the gate across the
      street before its end, and the container yard on concrete. The plan carries the port as built shapes, which the game
      and the preview build alike.
  - *Rule:* a ball-only collider is not a fix for something the kid can see. When a model is bigger than its designed
    collider, the kid's collider must follow it too, or the level must be designed around it.
  - *Rule:* a road must lead somewhere. Moving the water off the road is not enough: put something at the end of it that
    explains it (a gate, a building, a junction), and look at it from the game's camera.

## F. UI and menus

- **F1. The anchor and pivot trap** caused overlaps in the credits, results, guides and pause menu. *Rule:* lay screens out top down by explicit edges; check 4:3, 16:9 and 21:9 in both languages.
- **F2. Full screens.** The Settings card's two columns are full (718 of 724 units on the left), so a new row overflows. *Rule:* measure the column before adding a row. Graphics quality is automatic for this reason.
- **F3. Map labels too small for Spanish; a test rule stricter than the screen.** *Rule:* measure text with the real font in every language; test rules mirror what is drawn.
- **F4. Wrong instruction text** ("tap KICK" is a pass). *Rule:* check every how-to string against the real input.

## G. Audio

- **G1. Music redone four times on taste.** *Rule:* get reference tracks and adjectives first, then short A/B previews.
- **G2. A park hiss that drowned the music; every bed at the same loudness; coin and whistle too loud.** *Rule:* check spectra and loudness per place, and mix against the music at default volumes.
- **G3. Florida's music "looks sad" (redone in v132).** v122's Florida loops were Caribbean and Cuban styles (son, salsa,
  soca, calypso, one-drop) at 86 to 126 BPM, with steel pan, marimba and vibes; two were minor or Dorian, the menu and park
  were slow, and the soft mallet leads over sparse hand drums read as wistful, not sunny. The style was chosen from the
  place ("Florida = Caribbean") without asking the user what they wanted to feel. *Fix:* the user named the references
  (Justice, Tame Impala): Florida now plays original French electro (four on the floor, a pumping sidechain, a growling saw
  bass, filtered disco stabs, a gliding saw lead) and psychedelic synth-pop (a phased pad on major sevenths, a fuzzy
  melodic bass, big squashed drums, tape wobble), all in major, Mixolydian or a bright Dorian at 112 to 126 BPM. Previews
  went to the user as MP3s before the commit was called done. *Rule:* G1 again: for a new country's music, ask for
  reference artists and the mood first; energy (tempo, four on the floor, a major key) is what reads as happy, not the
  instruments' "local" colour.
- **G4. Florida's music "still bad" after the redo (v132, redone in v133); "the background beats are good enough".** v132
  kept the old random tune-maker (a melody walking the scale from a seed) and put it on new synths that glided into every
  note, wobbled (vibrato, and 5 to 6 cents of tape wow on the whole mix) and honked (resonant, overdriven stabs, the filter
  starting at 700 Hz). Nobody listened before it shipped: the checks were loudness, peaks and a spectrogram, none of which
  hears a tune. *Fix:* the drums and bass kept; every loop now has two written four-bar hooks over simple four-bar chord
  cycles, on synths that hold their pitch (a glide only between tied notes, no wow, a bright pluck for the riffs), and calmer
  stabs. `tools/music_hooks/check.py` fails if a strong beat of a hook is off its chord. *Rule:* a tune is written, not
  generated, when the user is listening for it; check what can be checked (notes against chords, pitch held), and say plainly
  that taste can only be judged by ear: send the previews and ask what is wrong in their words before a third take.

- **G5. Florida's music "still bad", a fourth time (v138).** Asked what was wrong, the user ticked every answer: too
  repetitive, some places' tunes, the synth sound grating over a whole level, too loud and distracting. Each earlier take
  fixed one axis (style, then tunes) and was checked by loudness, peaks, spectrograms and chord tones, none of which
  measures fatigue. The loops were 31 s of the same four bars twice, at the same loudness as Kamakura's mellower music but
  brighter, with saw stabs and leads, a deep sidechain pump and an open hat on every off-beat. Under Little Havana (now the
  first level played) a cafe radio also ran a second song, in another key, under the music the whole time, and downtown's
  air conditioners droned a chord half a semitone off. *Fix:*
  - 64 s loops in four sections (an opening, the groove, the lift, a breakdown with the kick out and the hook an octave
    down on a Rhodes);
  - Rhodes and soft plucks in place of the saw stabs and the saw lead;
  - a shallow pump, softer hats and claps, less drive, a darker tone;
  - Florida's loudness 0.11 to 0.115 against the others' 0.14;
  - no radio and no pitched hum in any bed.
  - *Rule:* ask early which of repetition, tune, timbre and level is wrong (a multiple-choice question works); check a
    loop's length against how long a level lasts; nothing pitched may play under the music unless it is the music.

- **G6. "Only the background beat is good" (v139).** Each Florida take had changed the synths, the tunes or the arrangement
  but kept one voice family: synths (electro, psych, then softer synths). The one part the user always kept was the drums.
  *Fix:* the drums as they were; everything else is on the band Kamakura's and California's music uses and the user never
  minded (guitars, Rhodes, organ, glockenspiel, vibes, whistle, a picked bass), in sunny pop-funk with new chords and
  tunes. Measured per note, the voices differ by up to 17 dB (a clean guitar's note at 0.033 RMS against a Rhodes chord's
  0.23), so the arranger now levels each tune voice and comp (`LeadLevel`, `CompLevel`). The tune shows over the chords in
  the spectrogram. *Rule:* when a user keeps rejecting one family of sounds, change the family, keep what they named as
  good, and measure the voices' levels against each other before mixing.

## H. Co-op, store, release and testing

- **H1. A design that punished the player who stayed connected.** *Rule:* design for reconnection.
- **H2. Distributed bugs that only a 2,000-storm chaos sweep found.** *Rule:* stateful distributed logic gets randomized chaos tests with written invariants.
- **H3. Platform limits found late:** iOS advertisement size, Android scan limits, R8 stripping a JNI-only plugin. *Rule:* write each platform's limits into the design before coding.
- **H4. Version codes going backwards; a debug-signed release bundle.** *Rule:* derive build numbers; release builds refuse to fall back to a debug key.
- **H5. Store and privacy answers that contradict each other** (user-generated content). *Rule:* one source for compliance answers; update every document together.
- **H6. Review notes describing removed controls.** *Rule:* after a control change, update the store text and review notes in the same change.
- **H7. Tests checked by breaking their rules, offline audits, careful save compatibility.** *Keep doing all three:*
  - Planted bad copies make the tests fail.
  - `LevelFeasibility`, the coin audit, the map check and the pose audit run after the relevant change.
  - Persisted ids, enum orders and save keys never change.

## Standing preferences of the user

Never re-propose what is rejected here.
- **Characters:** keep the user's own character designs: outfit, hair, likeness and their reference photos and drawings. Don't replace them with generic anime models (v84 was reverted at once). They should look like polished game characters, not photographs.
- **Brows:** keep every character's eyebrows exactly as they are; no clean-up may wipe or repaint them (C22).
- **Kids' faces:**
  - Keep each kid's own scanned eyes, nose and mouth, at their own sizes.
  - No drawn-on doll eyes or stroke noses and mouths (v111 was reverted as "aliens").
  - The target is Max's face: realistic proportions with a drawn finish.
- **Comic filter:** dots and hatching on the characters as well as the street (raised on request).
- **Controls:**
  - nothing inside the stick's ring;
  - a ball icon on the KICK button, not a boot;
  - no auto-run.
- **Cities, not add-ons (v122):** each city a chapter with its own routes and play, picked after PLAY and HOLIDAY RUN.
  **Only Kamakura (the original town, still first) and Florida (v132):** Madrid, New York and Mumbai were removed at the
  user's request, with their designs, prompts and strings; don't re-add them or list cities as coming soon. Each city has its
  own colour temperature and climate. No reskins of another city's levels (D8).
- **The name is Kick Off 2 School (v137):** in every player-facing text; the logo is the "Kick OFF 2" artwork over a
  "SCHOOL" ribbon; the app ID stays `com.astradite.kickoff2`.
- **Both cities open from the start (v135):** Florida listed first, then Kamakura; Florida no longer waits for Kamakura's
  levels.
- **Florida's music (v132):** upbeat and original, in the spirit of Justice (French electro, filter house) and Tame Impala
  (psychedelic synth-pop). Not Caribbean or sad (G3). The user likes its beats (drums and bass, v132): keep them; the
  tunes are written hooks on steady synths (G4); it must not tire over a whole level: long loops that change, soft
  timbres, sitting back (G5).
- **The look:** the user's bar is a recent big-budget open-world game's look and feel (warm sun against cool shade, haze,
  weathered, dense streets), reached through light, grade and baked texture within the phone's budget, never by copying
  that game's content. The filters must keep working in every city.
- **No mini-games (v128):** none in Kamakura or Florida, and nothing put in their place: every leg of a route is a
  dribble. A transit hop between two legs is simply not shown (the next leg starts where it would have ended). Don't
  re-propose the bus, boat or shop mini-games, or errands that depend on them (E14).
- **Filters:** easy to reach: on the title screen and in every pause menu.
  The pencil sketch is black and white only; the classic cartoon keeps natural colour, nothing tinted orange (v134, D12).
- **Store art:** use the user's own artwork for the app icon.

## How to add an entry

Add an entry to the right section in the same commit as the fix. Use this shape: what happened (with version or commit), why, the fix, and the rule. If the fix is partial, say what is still to do.
