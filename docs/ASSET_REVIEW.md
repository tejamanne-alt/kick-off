# Asset review: the strict rules

**Every asset is reviewed this way before it is shown to the user or put in a level. No exceptions, no partial
boards.** The user asked for it after the cat came out with two tails and the kite looked wrong in flight, which a
single straight-on board had hidden. Each rule below comes from a fault that reached the user; the entry in
`docs/LEARNINGS.md` says what happened.

## 1. Every view

Render each asset from all eight sides, on one sheet, at the same scale, each labelled:

| View | From | For an animal (head +X, its right flank toward the game camera) | For a building or prop (street side -Y) |
|---|---|---|---|
| Front | straight at what the asset faces | head-on, at the face | the street side |
| Back | straight from behind | tail-on | the back |
| Left | its left side | the left flank | the left end |
| Right | its right side | the right flank: the side the game camera sees | the right end |
| Left 3/4 | front-left, a little above | | |
| Right 3/4 | front-right, a little above | | |
| Top | straight down | the back, from above | the roofs |
| Bottom | straight up | the belly, from beneath | the underside |

Also shown, on the same review: the asset beside its source picture, straight on, and from the game camera at play
size. A view that shows nothing the game will ever see is still shown: a fault there (a gap, a doubled part) is a fault.

## 2. Every motion

Every asset with moving parts is shown moving, as animated previews, one per motion that applies:

| Asset | Motions shown |
|---|---|
| An animal that walks | walk and run (legs, tail, body bob) |
| A bird on the ground | walk (hops, head nodding) and peck |
| A bird or insect in flight | fly (wingbeat) |
| A fish or a swimming turtle | swim |
| A sitting or lying animal | idle (its tail or head) |
| A machine or a door | its own motion (a barrier lifting, a door sliding) |

A part that tears from the body at its joint, swings the wrong way, or moves something that should stay still is a
fault (D16: the cat's legs came off when it walked). Each motion is shown at the game's own amplitude (the swing its
behaviour uses, e.g. Hazards/Dog's 28 degrees at a full run), and looked at frame by frame before it is shown.

Views the source picture can't show (an animal relief's top, bottom, front and back, built from one side) are still
rendered and labelled as built from the side alone. The review says which views the game's camera actually sees.

## 3. The checks (each one a fault that happened)

**Shape**
1. Every part is there once: one tail, one head (D14: the cat had two tails). Check the top and bottom views.
2. The shell is closed: front and back faces meet (D14: a gap all round), and no edge has only one face (D17: flat
   fins at the outline's tips, which vanish from behind because the Toon shader culls back faces). The count of
   edges where the two faces touch along a thin part is printed too.
3. Depth comes from each part's own width, round in section: a thin part is never a tall blade (D14).
4. Every view the game will see has real source data: no flat body from the side, no back that is the underside
   mirrored (D15: the kite in flight). If the source can't show a view, a sheet that does is asked for first.
5. Real size, stated, with the triangle count against its budget (`docs/ART_DIRECTION.md`) and the atlas's memory.

**Cut-outs**
6. The outline is whole: parts close to the background's grey are found (the kite's pale tail, a grey pigeon), and
   nothing of the background or the shadow is included (D14 work: the squirrel's shadow).
7. No holes in the asset; a gap that is really background (between a squirrel's tail and back) stays open.
8. Things standing in front of a wall are their own models; a moved cut-out paints out its whole box, never just its
   outline (D13: the bicycle's ghost, the bonsai with no canopy).

**The picture it comes from**
9. The picture is in the look target's look (D10: painted pictures under a photographic target).
10. Buildings are solid and whole: nothing ghosted or see-through (D9).
11. No real brand or logo anywhere, vending machines included (D11).
12. No power line across a front or roof (`dewire`); no sky on a roof's edge (`unsky`); crisp outlines (D12).
13. Every repair of the picture is listed on the review, and a glitched picture is never shown as the reference
    without saying so (D9).

**Rig**
14. Parts are named as the game's behaviour expects (Tail, Head, LegFL, LegFR, LegBL, LegBR, WingL, WingR), each with
    its origin at its joint; the motions in section 2 show them moving.
15. Every moving part overlaps what it's joined to, far enough to stay covered at the largest swing: no seam at rest,
    no gap mid-stride (D16). Every leg the picture shows is its own part, near legs in front of the body, far ones
    behind.

## 4. What the user is shown

One review per asset or per kit: the eight views, the motions, the asset beside its source, the checks with their
results (passed, or the fault and what is being done about it). It is published as a page the user can open on a
phone (an Artifact), the files kept in `review/<city>/`. A check that fails is said plainly, never left for the user to
find.
