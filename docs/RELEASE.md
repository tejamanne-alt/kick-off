# Release Guide

Everything needed to take Kick Off 2 from this repo to the App Store and Google Play.

**The app's id is `com.astradite.kickoff2`** (iOS bundle identifier and Android package name, set in
`Assets/_Game/Scripts/Editor/BuildScripts.cs`). It can never change once the app is uploaded to either store.

## 0. What you need

| | Google Play | App Store |
|---|---|---|
| Account | [Play Console](https://play.google.com/console) developer account (one-off fee) | [Apple Developer Program](https://developer.apple.com/programs/) membership (yearly) |
| Machine | Mac, Windows or Linux with Unity 6 + **Android Build Support** (incl. Android SDK & NDK, OpenJDK) from Unity Hub | A Mac with Unity 6 + **iOS Build Support** and **Xcode 26 or later** |
| Store rule | New apps and updates must target **Android 16 (API 36)**: the build sets it (`BuildScripts.AndroidTargetApi`) | Uploads must be built with **Xcode 26 / the iOS 26 SDK** or later |

Unity version for iOS: use **6000.0.68f1 or newer** (6.0 LTS), **6000.3.8f1 or newer** (6.3 LTS), or any **6000.4+**. Older
Unity 6 versions export an Xcode project without the UIKit scene life cycle, and apps built that way with the current
SDK refuse to launch ("UIScene life cycle is required"). After changing Unity, delete `Builds/iOS` before exporting again.

## 1. Before the first build

1. Open the project in Unity 6. The editor generates the menu, the levels and the art automatically.
2. Choose the business model in `Assets/_Game/Scripts/Store/Monetization.cs`:
   - **Free + Full Game unlock (recommended):** set `RequireUnlock = true` and enable IAP (section 2). Chapter 1 and its challenge are free; chapters 2–5 need a one-time purchase, and so does the Holiday Run (its lap runs through every chapter: its title button opens the unlock panel first).
   - **Paid app:** leave `RequireUnlock = false` and set the price in the store consoles.
3. Run **Kick Off > Build > Apply Store Player Settings** once to check everything is set:
   - the app id, version and build number, company "Astradite", product "Kick Off 2";
   - landscape only;
   - Android: minimum API 26, target API 36, ARM64 + IL2CPP;
   - iOS: 15.0+, automatic signing with your team (see `Editor/AppleSigning.cs`);
   - the app icon (drawn by code at 1024 px; Unity makes every size) and the splash colour.
4. Host the privacy policy (`docs/PRIVACY_POLICY.md`, fill in the contact email) at a public URL, e.g. GitHub Pages or your
   website. Both stores ask for that link.

## 2. Enabling in-app purchases (only for Free + unlock)

1. Install **In-App Purchasing** (`com.unity.purchasing`, version 4.x) from the Package Manager.
2. Add the scripting define `DTS_UNITY_IAP` in Player Settings > Other Settings > Scripting Define Symbols, for both Android and iOS. This compiles `Store/UnityIapStore.cs`. Without it, the game uses `MockStore`: test purchases succeed in the editor and in development builds, and the store reports "unavailable" in release builds.
3. Create a **non-consumable** product with the id `kickoff.fullgame` in App Store Connect and in Google Play Console (the `FullGameProductId` constant).
4. iOS needs a working Restore Purchases button. It's shown in the unlock panel, and in Settings whenever `RequireUnlock` is on.
5. Test on device with sandbox testers (App Store) and license testers (Play).

## 3. Version and build numbers

- `DTS_VERSION` is the version people see (`1.0.0`, then `1.0.1`, `1.1.0`…).
- `DTS_BUILD_NUMBER` must go **up by at least 1 for every upload** to either store (Android versionCode, iOS build number).
  Both stores reject a number they have already seen.
- Building from the editor menus keeps whatever is in Player Settings (a fresh project starts at 1.0.0, build 1). Before each new
  upload run **Kick Off > Build > Bump Build Number**; change the version in Player Settings > Version when you release a new one.
  The environment variables, when set, override both (the command-line scripts use them).

## 4. Google Play

Every Play Console field, the store graphics and the screenshot sizes are in [`GOOGLE_PLAY_LISTING.md`](GOOGLE_PLAY_LISTING.md).

### Once
1. Unity Hub: add **Android Build Support** to your Unity version, with **OpenJDK** and **Android SDK & NDK Tools**.
2. The upload key, made in Unity: **Edit > Project Settings > Player > Android > Publishing Settings > Keystore Manager >
   Keystore... > Create New > Anywhere**, saved outside the project (e.g. `~/keys/kickoff2-upload.keystore`), then **Add Key**:
   alias `upload`, a password, validity 50 years. Back the file and both passwords up: every future update must be signed
   with this key. (Or from Terminal: `./ci/android/make_upload_key.sh ~/keys/kickoff2-upload.jks`.)
3. In Play Console: **Create app** → name "Kick Off 2", default language, Game, Free, accept the declarations.
   Leave **Play App Signing** on (the default): Google keeps the app-signing key, your key only signs uploads.

### Build the App Bundle
In Unity: **File > Build Profiles > Android > Switch Platform**, then in **Publishing Settings** tick **Custom Keystore**, pick the
keystore and the `upload` key and type both passwords (Unity forgets them when it closes), then **Kick Off > Build > Android App
Bundle (release)**. It writes `Builds/Android/KickOff.aab` and shows it in Finder. Without a key it stops and says what to set,
rather than building a bundle Play would refuse. If Unity offers to update the Android SDK (target API 36), accept.

From Terminal instead (Unity closed):
```
DTS_KEYSTORE_PATH=~/keys/kickoff2-upload.jks DTS_KEYSTORE_PASS='…' DTS_KEY_ALIAS=upload DTS_KEY_PASS='…' \
./ci/android/build_android.sh release
```
For a quick test on your own phone: **Kick Off > Build > Android APK (development)**, then `adb install -r Builds/Android/KickOff-dev.apk`.

### Upload and release
1. **Test and release > Testing > Internal testing** → create a release → upload `KickOff.aab` → add testers' emails → roll out.
   Install from the opt-in link and play through.
2. **New personal developer accounts** (created after 13 November 2023) must run a **closed test with at least 12 testers who stay
   opted in for 14 days in a row** before they can apply for production access. Start this early. Organisation accounts are exempt.
3. Fill in **App content** (privacy policy, ads, app access, content rating, target audience, data safety) and the store listing,
   as in `GOOGLE_PLAY_LISTING.md`.
4. **Production** → create a release with the same (or a newer) bundle → send for review. First reviews often take a few days.

## 5. App Store

### Once
1. Sign in to Xcode with your Apple ID (Xcode > Settings > Accounts) and note your **Team ID** (10 characters, shown there and on
   developer.apple.com > Membership).
2. In [App Store Connect](https://appstoreconnect.apple.com): **Apps > + > New App** → iOS, name "Kick Off 2", primary language,
   bundle ID `com.astradite.kickoff2` (if it isn't in the list yet, register it at developer.apple.com > Identifiers, or run one
   build first: automatic signing registers it), SKU e.g. `kickoff2-ios`.

### Build and upload (on the Mac)
```
DTS_APPLE_TEAM_ID=ABCDE12345 DTS_VERSION=1.0.0 DTS_BUILD_NUMBER=1 ./ci/ios/build_ios.sh upload
```
This exports the Xcode project from Unity, archives it with Xcode 26 and uploads it straight to App Store Connect. Other modes:
`appstore` writes `Builds/ipa-appstore/*.ipa` for Apple's **Transporter** app, and `development` makes an .ipa for your own devices.
To upload without signing in to Xcode (e.g. on CI), create an App Store Connect API key (Users and Access > Integrations) and set
`ASC_KEY_PATH` (the .p8 file, kept out of git), `ASC_KEY_ID` and `ASC_ISSUER_ID`.
By hand instead: **Kick Off > Build > iOS Xcode Project**, open `Builds/iOS/Unity-iPhone.xcodeproj`, then Product > Archive >
Distribute App > App Store Connect.

That project is for real iPhones and iPads: in the Simulator it installs but fails to launch ("Launchd job spawn failed").
To try the game in the Simulator, or to take store screenshots there, use **Kick Off > Build > iOS Simulator Project (testing
only)** instead. It writes a separate project to `Builds/iOS-Simulator`, which needs no signing and can't be uploaded.

A post-build step (`Editor/IosPostBuild.cs`) sets two Info.plist keys:
- `ITSAppUsesNonExemptEncryption = NO`, so App Store Connect stops asking about encryption on every upload.
- `UIRequiresFullScreen = YES`, which a landscape-only iPad app requires.

### TestFlight and review
1. Once processed (usually 10–30 minutes), the build appears in **TestFlight**: add yourself and testers, install with the
   TestFlight app and play through.
2. On the app's version page: screenshots (section 7), description, keywords, support URL, privacy policy URL, **App Privacy**
   ("Data Not Collected", section 6), **age rating** questionnaire, price, then pick the build and **Add for Review → Submit**.

## 6. Privacy answers

The game has no ads, no accounts, no network calls and no third-party SDKs (Unity IAP only if you enable it).

- **Apple App Privacy:** "Data Not Collected". Tracking: No. The privacy manifest is at `Assets/Plugins/iOS/PrivacyInfo.xcprivacy`.
- **Google Play Data safety:** no data collected or shared. Purchase history is handled by Google Play itself.
- **Analytics:** events are written only to `analytics.jsonl` on the device (useful for playtests: collect it from test devices). If you add a backend later via `AnalyticsService.AddSink`, update both forms and your privacy policy.
- **Families:** the game suits kids. If you opt into Google Play's Families programme or Apple's Kids category, keep it ad-free with no external links, which is already the case.

## 7. Store listing (draft)

The App Store version, field by field (with the screenshot sizes and how to take them), is in
[`APP_STORE_LISTING.md`](APP_STORE_LISTING.md). The support and privacy pages it links to are in `site/`.

**Name:** Kick Off 2

The "2" reads as "to" (kick off to school), not a sequel: the tagline and the first lines of the description say so.

**Subtitle (iOS, 30 chars):** Dribble all the way to school
**Short description (Play, 80 chars):** Dribble a football through town all the way to school. No rush (unless you like).

**Description:**

> Late for school? Grab your ball and kick off to school!
>
> Kick Off 2 is a football side-scroller in bright anime daylight. Keep the ball at your feet as you run through town: tap in rhythm for perfect touches, drag back to chip it over walls, juggle it past dogs, and wait for the green light before you cross.
>
> - Play as one of six schoolkids: two high-schoolers and four primary-school kids
> - 23 levels across 5 chapters: Home Street, the Market, the Beach, the Underpass and the Park
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

**Screenshots (landscape):** App Store: 6.9" iPhone (2868×1320) and 13" iPad (2752×2064); Play: at least 2 phone screenshots (16:9 or wider, e.g. 1920×1080) plus a 1024×500 feature graphic.

1. L01 with a perfect-touch sparkle and the "Perfect touch x3" toast
2. Aiming a chip over the parked car (trajectory dots, camera zoomed out)
3. The beach chapter with a seagull swooping
4. The tunnel's pool of light
5. The results screen with three stars and coins counting up
6. The Locker Room with the Saturn ball selected
7. The chapter map

Record these on a device with the HUD visible. In the editor, the Tune button and dev skip don't appear in screenshots as long as you hide the tuning panel.

## 8. Pre-submission checklist

- [ ] App id `com.astradite.kickoff2`, version and a new build number; icon present at every size (Unity generates them from the 1024 px source)
- [ ] `RequireUnlock` and IAP settings match the chosen model, sandbox purchase and restore tested
- [ ] Played every level on a mid-range Android phone and an older iPhone at 60 fps (use the Profiler markers `DTS.FxPool.Update` and `DTS.Audio.MusicUpload`)
- [ ] Settings persist across restarts; Reset progress works; both languages checked
- [ ] Release build has no Tune button or dev skip (they only appear in development builds)
- [ ] Android: signed with the upload key; App Bundle under 200 MB; targets API 36 (Android 16)
- [ ] iOS: built with Xcode 26+; privacy manifest included in the Xcode project; export compliance set to "no encryption"
- [ ] Privacy policy hosted at a public URL and entered in both consoles
- [ ] Store listing, screenshots, privacy forms and age rating completed
