# Kick Off 2: Google Play listing

Everything to enter in Play Console, field by field. App id (package name): **`com.astradite.kickoff2`**.

## Grow users > Store presence > Main store listing

| Field | Value |
|---|---|
| App name (10 / 30) | `Kick Off 2` |
| Short description (79 / 80) | `Dribble a football through town all the way to school. Collect all 23 stickers!` |
| App icon (512 × 512) | `marketing/googleplay/icon_512.png` |
| Feature graphic (1024 × 500) | `marketing/googleplay/feature_graphic_1024x500.png` |
| Phone screenshots (2–8, 16:9) | the screenshot tour at **1920 × 1080** (see below) |
| 7" and 10" tablet screenshots | the same 1920 × 1080 pictures (optional, but needed to be featured on tablets) |
| Video | leave empty |

**Full description** (the App Store one, which Play also accepts as is):
```
Late for school? Grab your ball and kick off to school!

Kick Off 2 is a football side-scroller in bright anime daylight. Keep the ball at your feet as you run through town: tap in rhythm for perfect touches, drag back to chip it over walls, slide under barriers, double jump over gaps, juggle it past dogs and wait for the green light before you cross.

THE WAY TO SCHOOL
• 23 levels across 5 chapters: Home Street, the Market, the Beach, the Underpass and the Park
• Play as one of six schoolkids: two high-schoolers and four primary-school kids
• Real ball physics: every touch and every kick is about angle and timing
• Beat the school bell, or switch the timer off and take it easy
• Ball-skill challenges: keepy-uppy, target practice and a beach slalom

COLLECT STICKERS
• Every level hides a sticker, from the cat on the gate to the school bell
• Holo and gold stickers shine in your album
• Finish a chapter's set, or reach 5, 10, 15, 20 and all 23 stickers, to unlock exclusive balls, outfits, flags and trails you can't buy

THE LOCKER ROOM
• Earn coins on the way and spend them on ball skins, backpack flags, outfits and trails

FOR EVERYONE
• Simple touch controls, a left-handed layout and a colour-blind friendly aim
• Plays offline
• No ads, no accounts and no data collected
```

### Screenshots for Play
Play wants 16:9 (no side more than twice the other), so the iPhone pictures (2622 × 1206) don't fit. In Unity's Game view add
a Fixed Resolution of **1920 × 1080**, select it and run **Kick Off > Store Screenshots (Play mode)**: the 9 pictures land in
`Screenshots/1920x1080`. Upload the gameplay ones first.

## Store settings
- **App category:** Game > **Sports** (or Casual). Tags: Soccer, Platformer, Casual, Offline.
- **Contact details:** an email (shown publicly on the listing), and the support page as the website.

## Policy and programs > App content
| Declaration | Answer |
|---|---|
| Privacy policy | the published `site/privacy.html` address |
| App access | All functionality is available without special access |
| Ads | No, my app does not contain ads |
| Content rating | IARC questionnaire: category **Game**; answer No to violence, fear, sexuality, language, drugs, gambling, user interaction, sharing location, purchases of digital goods. Expect PEGI 3 / ESRB Everyone. |
| Target audience | Pick the age groups. Including under-13s puts the app under the Families policy, which it already meets (no ads, no data collected, no external links); 13 and over keeps the review simplest. |
| Data safety | Does your app collect or share any of the required user data types? **No.** (Nothing leaves the device.) |
| Government apps | No |
| Financial features | None |
| Health | None |
| News app | No |
| Advertising ID | No, it doesn't use the advertising ID |

## Release notes (version 1.0, 438 / 500 characters)
Release name: `1.0 (1)`. Paste the whole block, tags included, into **Release notes**:
```
<en-US>
Welcome to Kick Off 2, our first release!
• Dribble all the way to school through 23 levels in 5 chapters: Home Street, the Market, the Beach, the Underpass and the Park
• Play as one of six schoolkids: two high-schoolers and four primary-school kids
• Slide under barriers and double jump over gaps
• Find the sticker hidden in every level to unlock exclusive balls, outfits, flags and trails
• Ball-skill challenges: keepy-uppy, target practice and a beach slalom
• No ads, plays offline
</en-US>
```

## Releases
1. **Internal testing** (Test and release > Testing > Internal testing): create a release, upload `Builds/Android/KickOff.aab`,
   add your own Google account as a tester, roll out, open the opt-in link on your Android phone and play through. No review,
   available in minutes.
2. **Closed testing** (new personal developer accounts only): at least **12 testers opted in for 14 days in a row** before you can
   apply for production. Create a closed testing track with the same bundle, add the testers' Google accounts (or a Google
   Group), share the opt-in link, and keep them opted in for the full 14 days.
3. **Apply for production** (Dashboard), answering the questions about the closed test, then **Production > Create new release**
   with the bundle and send it for review (often a few days for a first app).

Every new upload needs a higher version code: run **Kick Off > Build > Bump Build Number** before building again.
