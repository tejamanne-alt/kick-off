# Kick Off 2: App Store listing

Everything to type into App Store Connect for version 1.0, field by field. Character counts are within Apple's limits.

## Distribution > iOS App > 1.0 (version page)

### App icon
`marketing/appstore/icon_1024.png` (1024 × 1024, opaque PNG; iOS rounds the corners itself): the game's logo artwork (`marketing/source/icon_artwork.png`: a boy kicking a ball along the footpath on the way to school, under the "Kick OFF 2" logo), made into every size by `tools/app_icon_from_image.py`. The build puts the same picture
in the app (`Assets/_Game/Art/Icon/AppIcon.png`, applied by **Kick Off > Build > Apply Store Player Settings**), and App Store
Connect takes the 1024 px icon from the uploaded build: there is nothing to upload by hand.

### Header and Search Results (creative assets, optional)
Key art rendered from the game's own models (the home street, the boy juggling, the girl walking, the Kick Off 2 logo):

| Slot | File | Size |
|---|---|---|
| Header | `marketing/appstore/header_3840x1646.jpg` | 3840 × 1646 |
| Search Results | `marketing/appstore/search_results_3840x2560.jpg` | 3840 × 2560 |

Both are optional: without a search results asset, App Store search shows the screenshots instead.

### App Previews and Screenshots
| Slot | Size (landscape) | Game view size / Simulator |
|---|---|---|
| iPhone with Dynamic Island (medium display) | **2622 × 1206** | 2622 × 1206 / iPhone 17 Pro |
| iPad 13" display | **2752 × 2064** | 2752 × 2064 / iPad Pro 13-inch |

iPhone Duo and Apple Watch: leave empty (the game has no Watch app). The large iPhone display slot is optional.
App previews (videos) are optional.

Take them with the screenshot tour (see "Taking the screenshots" below) and upload them in this order, gameplay first, since the
first three show in search results:

1. `03_chapter2_…` (the Market) — or whichever chapter shot looks best
2. `04_chapter3_…` (the Beach)
3. `07_album`
4. `02_chapter1_…` (Home Street)
5. `05_chapter4_…` (the Underpass)
6. `06_chapter5_…` (the Park)
7. `08_locker_room`
8. `01_title`
9. `09_map`

### Promotional Text (152 / 170)
```
Kick off to school! Dribble through town, chip the ball over walls and slide under barriers. Find all 23 stickers to unlock exclusive balls and outfits.
```

### Description
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

### Keywords (98 / 100)
```
football,soccer,dribble,ball,runner,platformer,school,street,skills,kids,stickers,keepy uppy,anime
```
(Words in the app name are searched already, so "kick" and "off" aren't repeated.)

### Support URL
The web address where you publish `site/index.html` (the support page).

### Marketing URL
Leave empty (optional).

### Version
`1.0`

### Copyright
```
2026 Astradite Private Limited
```

### Build
Pick build **1** (the one uploaded from Xcode).

### Game Center
Off.

### App Review Information
- **Sign-in required:** unticked (no account).
- **Contact:** your first and last name, phone and email (Apple only, not shown on the store).
- **Notes** (answering App Review's Guideline 2.1 "Information Needed" questions; fill in the two [brackets]):
```
1. DEMO VIDEO
Screen recording on an iPhone [model] running iOS [version], starting from the Home Screen with the app launch: [attached below / paste the link]
It shows the title screen, choosing the player, the town map, playing a level (running, kicking, jumping, sliding), collecting a sticker, the results screen, the sticker album and the Locker Room.
The app has no account registration, login or account deletion, and no paid content or in-app purchases. The only thing a player can type is an optional name for local Co-op: it is shown only to the other phones in the same Co-op lobby, directly over Bluetooth (never online, never stored anywhere else), it is filtered (a word list; no special characters), there is no chat, and the lobby's host can remove a player (who then can't rejoin that lobby).

2. PURPOSE AND AUDIENCE
Kick Off 2 is a football (soccer) side-scrolling game for players of all ages, played alone or in local Co-op (up to four phones in the same room race each other to school over Bluetooth, iPhone and Android together, no internet). The player dribbles a ball through town streets to reach school, across 23 short skill-based levels in 5 chapters plus ball-skill challenges. It is a light, ad-free game that plays offline and rewards timing and ball control; a sticker hidden in each level unlocks cosmetic items.

3. HOW TO USE IT
No setup, login or sample files are needed. Launch the app, tap PLAY and choose a level on the town map: six routes from the kid's house to the school, each level a numbered stop on its route (levels unlock in order as each is finished).
Controls (landscape): the two arrow buttons at the bottom left run; KICK touches the ball (drag on it to aim a chip, release to kick); JUMP jumps (tap again in the air for a double jump); SLIDE slides under barriers. Bring the ball through the school gate to finish a level.
Stickers shows the album (tap a sticker to view it). The Locker Room has cosmetic items unlocked with in-game coins earned by playing, or by stickers. Settings has the player choice (six kids: two teenagers and four primary-school children), sound, the school-bell timer, the controls (a left-handed layout, the slide button's place) and the language.

4. EXTERNAL SERVICES
None. The app works fully offline and makes no network requests. Co-op uses Bluetooth LE directly between nearby phones (NSBluetoothAlwaysUsageDescription explains it when the player first opens Co-op); nothing is sent to a server. It uses no third-party services or SDKs: no analytics, advertising, authentication, payment or AI services. It is built with the Unity engine, and progress is stored only on the device.

5. REGIONAL DIFFERENCES
None. The app works the same in every region. Its text is in English and Spanish, following the device language.

6. REGULATED INDUSTRIES AND THIRD-PARTY MATERIAL
Not applicable: the app is not in a regulated industry and contains no protected third-party material. All characters, art, music and sound were made for this game; the fonts (Lilita One and Varela Round) are used under the SIL Open Font License.
```

### App Store Version Release
"Manually release this version" (so you choose the launch day), or "Automatically release" if you'd rather it goes live as soon as it's approved.

## App Information (left menu, General)
- **Name:** `Kick Off 2`
- **Subtitle (29 / 30):** `Dribble all the way to school`
- **Category:** Primary **Games**, subcategories **Sports** and **Casual**. Secondary category: optional, e.g. Entertainment.
- **Content Rights:** "No, it does not contain, show, or access third-party content".
- **Age Rating:** answer "None" / "No" to violence, gambling and loot boxes, chat or messaging, ads, web access and
  medical content. **User-generated content: answer Yes.** Co-op shows a name a player typed to the others in the same
  room, and declaring it is the answer App Review can't dispute. Guideline 1.2's requirements for it are met: names are
  filtered (a word list), the host can remove a player (who can't rejoin that lobby), and the support page gives a
  contact. The review notes above describe it the same way. Expect the lowest rating (4+); if the questionnaire suggests
  another, accept it.
- **License agreement:** Apple's standard EULA.

## Pricing and Availability
- **Price:** Free (USD 0.00).
- **Availability:** all countries and regions.
- **EU (Digital Services Act):** answer the trader question under Business; as a private person who isn't trading, choose
  "not a trader".

## App Privacy
- **Privacy Policy URL:** the web address where you publish `site/privacy.html`.
- **Data collection:** "No, we do not collect data from this app" → Publish.

## Publishing the support and privacy pages
1. The support address, **contact@astradite.com**, is already in `site/index.html` and `site/privacy.html` (and
   `docs/PRIVACY_POLICY.md`); change it there if it ever changes.
2. Upload the `site` folder (the two pages and `style.css`) to any public host: GitHub Pages, Netlify, Vercel, Cloudflare
   Pages or your own domain. Open both pages in a browser to check they load before entering them in App Store Connect.

## Taking the screenshots
The game takes them itself, in Unity's Play mode:

1. In the Game view, open the resolution menu ("Free Aspect") and add two Fixed Resolution sizes with **+**:
   **2622 × 1206** (label it "App Store iPhone") and **2752 × 2064** ("App Store iPad"). Pick the iPhone one.
2. Run **Kick Off > Store Screenshots (Play mode)** and press Start. Don't touch anything: the game stages a well-played
   save, visits the title, a level in every chapter, the album, the Locker Room and the map, and saves a picture of each
   (about two minutes). Finder then opens `Screenshots/2622x1206` (next to `Assets`), and Play mode stops by itself. Your own
   progress and settings are put back.
3. Pick the iPad size and run it again: `Screenshots/2752x2064`.
4. Drag each folder's pictures into the matching slot on the version page.

The same tour also runs in the Simulator (**Kick Off > Build > iOS Screenshot Project (Simulator)**, then run that Xcode
project on the iPhone 17 Pro or iPad Pro 13-inch simulator); its pictures land in the app's `Documents/Screenshots` inside
the Simulator's files. To find them on any simulator, booted or not (the newest first):
```
find ~/Library/Developer/CoreSimulator/Devices -type d -path "*/Documents/Screenshots/*x*" -exec ls -dt {} + 2>/dev/null
```
Then `open` the folder it prints. Xcode's console also prints it on the line starting `[Screenshots] Saving to`.
