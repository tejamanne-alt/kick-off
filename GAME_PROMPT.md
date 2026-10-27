# Master Prompt: Cozy Soccer Side-Scroller for iOS & Android

> Inspired by *Kick* (Shoreline Games / nospacelost, Steam app 3760370).
> Use this to build an **original** game in the same genre. Do not reuse its name, art, characters, music, or level layouts.

Copy everything inside the block below into your AI coding assistant (Claude Code, Cursor, etc.).
Build it phase by phase: give the full prompt once, then ask for "Phase 1", "Phase 2", and so on, testing on a real device after each phase.

---

```text
You are a senior mobile game developer. Build a complete, shippable 2D mobile game
for iOS and Android called "<YOUR GAME NAME>" (working title: "Dribble to School").

## 1. Concept
A cozy, hand-drawn, side-scrolling soccer game. The player controls a kid who
dribbles a soccer ball through town on the way to school. The aim is to reach the
school gate before the bell rings without losing the ball. It is a slice-of-life
adventure: calm, charming and satisfying, never punishing. The challenge comes from
ball physics, kick angle and dribbling rhythm, not from enemies or combat.

## 2. Tech stack
- Engine: Unity 6 LTS (2D URP), C#. One codebase builds for iOS and Android.
  (Alternative if I say so: Godot 4.x with GDScript.)
- Physics: Unity 2D physics (Rigidbody2D, CircleCollider2D, PhysicsMaterial2D).
- Input: the new Input System, with touch as the primary input.
- Orientation: landscape only. Target 60 FPS on mid-range devices from 2021 on.
- Min OS: iOS 15+, Android 8.0 (API 26)+. Handle safe areas and notches.
- Data: ScriptableObjects for levels, skins and tuning values, so I can tweak
  them without touching code.
- Save: local JSON save file, with optional cloud save later.
- Keep the architecture clean: GameManager, LevelManager, PlayerController,
  BallController, HazardBase, UIManager, AudioManager, SaveSystem, ShopSystem.

## 3. Core mechanics (most important, get these right first)
### Player (the Kid)
- Auto-walks or runs right at a steady pace. The player controls speed:
  hold the left side of the screen to slow down or stop, and release to keep going.
- Jump: swipe up or tap the jump button. Short hop on a tap, higher jump on a hold.
- The kid can't carry the ball. It must stay near his feet through dribbling.

### Ball physics
- The ball is a real physics object: bouncy, rolling, with spin and friction.
- Dribble: when the ball is within reach of the kid's feet, it gets small automatic
  touches that keep it rolling just ahead. Rhythm matters: well-timed manual taps
  give a "perfect touch" with better control and a small coin bonus.
- Kick: drag back from the ball and release, like a slingshot. The drag direction
  sets the angle and the drag length sets the power. Show a dotted trajectory
  preview (first ~0.5 s only, so there is still skill involved).
- Kicks are used to clear obstacles, chip the ball over gaps or crates, bounce it off
  walls, and hit switches. The kid must then run to catch up with the ball.
- Juggle or keepy-uppy: tap while the ball is in the air near the kid to keep it up.
  Used in special challenges.
- Losing the ball (it falls in water or a pit, rolls into traffic, or is too far behind)
  sends you back to the last checkpoint. No game-over screen.
- Tune everything through a BallTuning ScriptableObject: mass, bounce, friction,
  max kick force, dribble touch strength, and reach radius.

### Win and lose
- Reach the school gate with the ball to finish the level.
- The bell timer is optional per level and can be turned off in Settings (cozy mode).
- Star rating (1-3): finished, finished before the bell, and all coins plus a
  perfect-touch streak.

## 4. Levels (23 levels in 5 chapters)
Each level is a hand-built side-scrolling route, 60-120 seconds long, with checkpoints.
Each one has its own hazards and its own opportunities.
1. Home Street: tutorial (walk, dribble, jump, kick), parked cars, low walls.
2. Market and Crossings: pedestrians who walk across, zebra crossings with
   traffic lights (wait for green), stacked crates (kick or chip over them),
   fruit stalls.
3. The Beach: sand slows the ball, waves and puddles, seagulls, a boardwalk with gaps.
4. Underpass and Construction: dark tunnels, rolling pipes, moving platforms,
   puddles, slopes and ramps.
5. The Park and School: dogs that chase the ball, fountains, swings, a final run
   through the school yard before the bell.
- Each chapter brings in one new mechanic and mixes it with the earlier ones.
- Hidden side paths hold extra coins and collectible stickers.
- Optional "Ball Skill Challenges" in each chapter: juggling count, accuracy
  (kick through a window or a tyre), and dribble slalom.
- Build levels with Tilemaps plus prefabs, and include a simple level-data format
  so I can add new levels quickly.

## 5. Hazards and interactables (each its own prefab with a HazardBase)
Pedestrians (walk, sometimes block, react with a funny animation if hit gently),
cars and bikes at crossings, traffic lights, crates (stackable, pushable,
breakable), puddles (slow the ball), sand, water and pits (lose the ball),
dogs, seagulls, wind, moving platforms, ramps, springboards, awnings
(bounce the ball), switches and gates, and breakable windows (bonus challenge only).

## 6. Progression and economy
- Coins come from levels, perfect touches, challenges and stars.
- The shop sells cosmetics only: ball skins (classic, retro leather, beach ball,
  neon, planets, fruit, etc.), flags or country banners on the kid's backpack,
  outfits, and trail effects.
- A chapter map screen shows level nodes, stars, a lock state and the next goal.
- Achievements and a sticker album as long-term collectibles.

## 7. Monetization (fair, cozy-friendly)
- Option A (recommended): paid upfront, or free with a one-time "Full Game" unlock
  after Chapter 1. No ads.
- Option B: free with an optional rewarded ad (double coins after a level),
  plus IAP for coin packs and a remove-ads purchase. No forced interstitials mid-level.
- Use Unity IAP and Unity LevelPlay / AdMob behind an interface so either option
  can be switched on.

## 8. Art direction
- Hand-drawn, warm, storybook look: soft pencil or ink outlines, watercolor or
  gouache textures, a pastel morning palette that warms up as the day goes on.
- Parallax backgrounds with 3-4 layers per chapter.
- The kid gets expressive, bouncy animations: idle, walk, run, jump, kick, juggle,
  stumble and celebrate. Use 2D Animation (skeletal) or sprite sheets.
- Juice: squash and stretch on the ball, dust puffs, ball trail, screen shake on
  big kicks, a slow-mo "nice!" moment on perfect chips.
- Use placeholder shapes first and keep art in clearly named folders so I can
  swap in final assets.

## 9. Audio
- A gentle acoustic or lo-fi soundtrack, one theme per chapter.
- Satisfying SFX: ball thumps (varied pitch), dribble taps, crowd "ooh",
  the school bell, birds, traffic, waves.
- Light haptics on kicks and perfect touches (iOS Taptic, Android vibration),
  with a toggle.

## 10. UI and UX
- Screens: Splash, Main Menu, Chapter Map, Level HUD, Pause, Level Complete
  (stars, coins, time), Shop, Sticker Album, Settings, Credits.
- HUD: coins, bell timer (if on), checkpoint indicator, pause button, and a
  jump button on the right.
- Settings: music and SFX volume, haptics, bell timer on/off (cozy mode),
  left-handed controls, language, and a colorblind-friendly trajectory color.
- Use large touch targets (min 48dp), one-handed friendly where possible, and
  show a contextual tutorial the first time each mechanic appears.

## 11. Technical requirements
- Object pooling for coins, particles and pedestrians.
- Fixed timestep physics; interpolate the ball for smooth visuals.
- Camera: Cinemachine 2D follow with look-ahead, framing both the kid and the ball.
- Localization-ready (Unity Localization package); English first.
- Analytics hooks: level start, level complete, ball lost, and where it was lost.
- Store-ready builds: app icons, splash, iOS privacy manifest, Android
  App Bundle (AAB), target API level required by Google Play.

## 12. Build in phases (wait for my "next" between phases)
Phase 1: Project setup, the kid controller, ball physics, dribble and kick with
         trajectory, and a grey-box test level. (Must feel great before moving on.)
Phase 2: Camera, checkpoints, the lose-ball/respawn flow, the bell timer and level
         complete, with 3 grey-box levels.
Phase 3: The hazard system and all hazard prefabs, then Chapters 1-2 (10 levels).
Phase 4: Coins, stars, save system, shop, skins, chapter map.
Phase 5: Chapters 3-5 (13 levels) and ball skill challenges.
Phase 6: Art and animation pass, parallax, particles, audio, haptics.
Phase 7: Menus, settings, tutorial, localization, accessibility.
Phase 8: Monetization, analytics, performance profiling on device, and iOS/Android
         build setup plus store listing checklist.

For every phase:
- List the files you will create or change before you write code.
- Write complete, compilable code with no "TODO: implement" stubs.
- Explain how to test it in the editor and on a phone.
- Note which tuning values I should play with.

Start with Phase 1 now.
```

---

## Follow-up prompts you can use

- "The ball feels too floaty. Give me 3 tuning presets (arcade, realistic, cozy) and a debug slider panel in-game."
- "Design Level 7 (Market chapter) in detail: layout beat by beat, hazards, coin placement, secret path, and par time."
- "Generate a list of 30 ball skin ideas with names, rarity and coin prices."
- "Write the App Store and Google Play listings: title, subtitle, short and long description, keywords."
- "Create AI image-generation prompts for the kid character sheet, each chapter's background layers, and the app icon, all in a consistent hand-drawn storybook style."

## Tips
- Prototype the dribble and kick feel before anything else. It is the whole game.
- Test on real phones early, because touch drag and kick feels very different from mouse input.
- Keep it original: your own name, character, town and art. The genre and mechanics are fair game; the assets and branding are not.
