# Kick Off 2: App Store listing

Everything to type into App Store Connect for version 1.0, field by field. Character counts are within Apple's limits.

## Distribution > iOS App > 1.0 (version page)

### App Previews and Screenshots
| Slot | Size (landscape) | Simulator to use |
|---|---|---|
| iPhone with Dynamic Island (medium display) | **2622 × 1206** | iPhone 17 Pro |
| iPad 13" display | **2752 × 2064** | iPad Pro 13-inch |

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
• Play as the boy or the girl
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
2026 Astradite
```

### Build
Pick build **1** (the one uploaded from Xcode).

### Game Center
Off.

### App Review Information
- **Sign-in required:** unticked (no account).
- **Contact:** your first and last name, phone and email (Apple only, not shown on the store).
- **Notes:**
```
Kick Off 2 needs no account and has no in-app purchases; every level can be played.
Controls (landscape): the two arrow buttons at the bottom left run; KICK touches the ball (drag on it to aim a chip, release to kick); JUMP jumps (tap again in the air for a double jump); SLIDE slides under barriers.
Stickers are found inside levels and unlock cosmetic items; they can't be bought.
```

### App Store Version Release
"Manually release this version" (so you choose the launch day), or "Automatically release" if you'd rather it goes live as soon as it's approved.

## App Information (left menu, General)
- **Name:** `Kick Off 2`
- **Subtitle (29 / 30):** `Dribble all the way to school`
- **Category:** Primary **Games**, subcategories **Sports** and **Casual**. Secondary category: optional, e.g. Entertainment.
- **Content Rights:** "No, it does not contain, show, or access third-party content".
- **Age Rating:** answer every question "None" / "No" (no violence, no gambling or loot boxes, no user-generated content,
  no chat, no ads, no web access, no medical content). Expect the lowest rating (4+).
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
1. Replace `SUPPORT_EMAIL` in `site/index.html` and `site/privacy.html` with the address to show (on a Mac:
   `sed -i '' 's/SUPPORT_EMAIL/you@example.com/g' site/*.html`).
2. Upload the `site` folder (the two pages and `style.css`) to any public host: GitHub Pages, Netlify, Vercel, Cloudflare
   Pages or your own domain. Open both pages in a browser to check they load before entering them in App Store Connect.

## Taking the screenshots
The game takes them itself in a special Simulator build:

1. Pull the branch, open the project, and run **Kick Off > Build > iOS Screenshot Project (Simulator)**. It writes
   `Builds/iOS-Screenshots`. Never upload this build: the store build is still **iOS Xcode Project**.
2. Open `Builds/iOS-Screenshots/Unity-iPhone.xcodeproj` in Xcode, pick the **iPhone 17 Pro** simulator and press ▶.
   Don't touch anything: the game stages a well-played save, visits the title, a level in every chapter, the album, the
   Locker Room and the map, and saves a picture of each (about two minutes). "Store screenshots: 9 saved" means it's done.
3. Open the pictures (Terminal):
   ```
   open "$(xcrun simctl get_app_container booted com.astradite.kickoff2 data)/Documents/Screenshots"
   ```
   The folder is named after the size: check it says `2622x1206`.
4. Quit the Simulator (or Device > Shut Down), pick the **iPad Pro 13-inch** simulator, press ▶ again, and repeat step 3
   (folder `2752x2064`).
5. Drag each folder's pictures into the matching slot on the version page.
