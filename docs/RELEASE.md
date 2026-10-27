# Release Guide

Everything needed to take Dribble To School from this repo to the App Store and Google Play.

## 1. Before the first build

1. Open the project in Unity 6. The editor generates the menu, the levels and the art automatically.
2. In `Assets/_Game/Scripts/Editor/BuildScripts.cs`, set `CompanyName` and `ApplicationId` (for example `com.yourstudio.dribbletoschool`). The bundle id can't change after the first upload.
3. Run **Dribble To School > Build > Apply Store Player Settings**. This sets:
   - the ids, version and build number,
   - landscape-only orientation,
   - Android API 26+ (target: highest installed), ARM64 + IL2CPP,
   - iOS 15+,
   - the procedural app icon and the splash colour.
4. Pick the business model in `Assets/_Game/Scripts/Store/Monetization.cs`:
   - **Free + Full Game unlock (recommended):** set `RequireUnlock = true` and enable IAP (section 2). Chapter 1 and its challenge are free; chapters 2-5 need the one-time purchase.
   - **Paid app:** leave `RequireUnlock = false` and set the price in the store consoles.

## 2. Enabling in-app purchases (only for Free + unlock)

1. Install **In-App Purchasing** (`com.unity.purchasing`, version 4.x) from the Package Manager.
2. Add the scripting define `DTS_UNITY_IAP` in Player Settings > Other Settings > Scripting Define Symbols, for both Android and iOS. This compiles `Store/UnityIapStore.cs`. Without it, the game uses `MockStore`: test purchases succeed in the editor and in development builds, and the store reports "unavailable" in release builds.
3. Create a **non-consumable** product with the id `dribbletoschool.fullgame` in App Store Connect and in Google Play Console. The id is the `FullGameProductId` constant.
4. iOS needs a working Restore Purchases button. It's shown in the unlock panel, and in Settings whenever `RequireUnlock` is on.
5. Test on device with sandbox testers (App Store) and license testers (Play).

## 3. Building

| Target | Menu | CI method |
|---|---|---|
| Android release (AAB) | Build > Android App Bundle (release) | `DribbleToSchool.EditorTools.BuildScripts.BuildAndroidRelease` |
| Android test (APK) | Build > Android APK (development) | `DribbleToSchool.EditorTools.BuildScripts.BuildAndroidDev` |
| iOS (Xcode project) | Build > iOS Xcode Project | `DribbleToSchool.EditorTools.BuildScripts.BuildIOS` |

CI example:

```
Unity -batchmode -quit -projectPath . -buildTarget Android \
  -executeMethod DribbleToSchool.EditorTools.BuildScripts.BuildAndroidRelease
```

Environment variables:

- `DTS_VERSION` and `DTS_BUILD_NUMBER`: the version string and build number.
- `DTS_KEYSTORE_PATH`, `DTS_KEYSTORE_PASS`, `DTS_KEY_ALIAS`, `DTS_KEY_PASS`: the Android upload key. Never commit the keystore.
- `DTS_APPLE_TEAM_ID`: turns on automatic signing for iOS.

Builds are written to `Builds/` (git-ignored). For iOS, open `Builds/iOS/Unity-iPhone.xcodeproj`, check signing, then Product > Archive.

## 4. Privacy answers

The game has no ads, no accounts, no network calls and no third-party SDKs (Unity IAP only if you enable it).

- **Apple App Privacy:** "Data Not Collected". Tracking: No. The privacy manifest is at `Assets/Plugins/iOS/PrivacyInfo.xcprivacy`.
- **Google Play Data safety:** no data collected or shared. Purchase history is handled by Google Play itself.
- **Analytics:** events are written only to `analytics.jsonl` on the device (useful for playtests: collect it from test devices). If you add a backend later via `AnalyticsService.AddSink`, update both forms and your privacy policy.
- **Families:** the game suits kids. If you opt into Google Play's Families programme or Apple's Kids category, keep it ad-free with no external links, which is already the case.

## 5. Store listing (draft)

**Name:** Dribble To School
**Subtitle (iOS, 30 chars):** Cozy soccer side-scroller
**Short description (Play, 80 chars):** Dribble a ball all the way to school. Cozy, hand-drawn, no rush (unless you like).

**Description:**

> Late for school? Grab your ball and go!
>
> Dribble To School is a cozy, hand-drawn soccer side-scroller. Keep the ball at your feet as you run through town: tap in rhythm for perfect touches, drag back to chip it over walls, juggle it past dogs, and wait for the green light before you cross.
>
> - 23 levels across 5 storybook chapters: Home Street, the Market, the Beach, the Underpass and the Park
> - Real ball physics: every kick is about angle and timing
> - Ball-skill challenges: keepy-uppy, target practice and beach slalom
> - Earn coins to unlock ball skins, backpack flags, outfits and trails
> - Find the hidden sticker in every level
> - Cozy mode: switch off the school bell and play at your own pace
> - Left-handed controls, colour-blind options and gentle haptics
> - No ads. Ever.

**Keywords (iOS, 100 chars):** soccer,football,dribble,cozy,kids,platformer,ball,juggle,side scroller,casual,offline,family
**Category:** Games > Sports (secondary: Casual)
**Age rating:** 4+ (Apple) / Everyone (IARC). There's no violence or user-generated content, and all purchases are clearly labelled.

**Screenshots (landscape, 6.7" iPhone + 12.9" iPad + Play phone and tablet):**

1. L01 with a perfect-touch sparkle and the "Perfect touch x3" toast
2. Aiming a chip over the parked car (trajectory dots, camera zoomed out)
3. The beach chapter with a seagull swooping
4. The tunnel's pool of light
5. The results screen with three stars and coins counting up
6. The Locker Room with the Saturn ball selected
7. The chapter map

Record these on a device with the HUD visible. In the editor, the Tune button and dev skip don't appear in screenshots as long as you hide the tuning panel.

## 6. Pre-submission checklist

- [ ] Ids, version and build number set; icon present at every size (Unity generates them from the 1024 px source)
- [ ] `RequireUnlock` and IAP settings match the chosen model, sandbox purchase and restore tested
- [ ] Played every level on a mid-range Android phone and an older iPhone at 60 fps (use the Profiler markers `DTS.FxPool.Update` and `DTS.Audio.MusicUpload`)
- [ ] Settings persist across restarts; Reset progress works; both languages checked
- [ ] Release build has no Tune button or dev skip (they only appear in development builds)
- [ ] Android: signed with the upload key; App Bundle under 150 MB; target API meets Play's current requirement
- [ ] iOS: privacy manifest included in the Xcode project; export compliance set to "no encryption" (standard HTTPS only, or none)
- [ ] Store listing, screenshots, privacy forms and age rating completed
