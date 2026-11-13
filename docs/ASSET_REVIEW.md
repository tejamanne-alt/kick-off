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
fault (D16: the cat's legs came off when it walked). Each motion is checked against how the real species moves, not
only against the measures (D21): a pigeon's head holds and thrusts, a perched bird looks about in quick turns and
holds, a foot lifts heel first and lands flat, a back tilts with the stride, a dragonfly's hind wings lead its fore. Each motion is the game's own: the behaviour's code ported line by
line (`World/LegGait.cs` and `tools/blender/asset_review.py` share the gait), changed in both together, never made up
for the review (D19: the review bounced birds the game walks). It is shown at 24 frames a cycle and looked at frame by
frame before it is shown: at full size, every second frame at least, never only as thumbnails on a contact sheet
(D20: four-legged birds looked right at 170 px).

An animal that moves is one skin on bones (D21): a continuous mesh bound to an armature, every bone named as the
behaviour finds it, sharing the skin across each joint, never rigid pieces turning over a body (their edges show at
every joint). A walking animal's legs are jointed as the animal's are (a thigh, a shin, a foot of its own, turning at
the ankle and rolling over its toes, a bird's toes in the round; a bird's bare leg one bone hinged at the heel), its feet planted on the ground through the stance and lifted
forward in the swing, its knees bending as in the picture (D19: rigid legs swung from the hip scissored and floated).
A bird walks on its feet, never bounces on the spot, and pecks by tipping its body on planted feet, no further than
its legs can keep them planted. Every other part that bends in the real animal bends in the model: a tail in three
links and a bird's wing in two (`World/PartChain.cs`: each link a share of the angle, each trailing the one before), a
fish's tail, a turtle's flippers; an insect's wings stay rigid, as real ones are. A part with no source motion stays
still, and the review says so.

Each motion plays at the game's own speed (24 frames a cycle); one too quick for a GIF to show (a wingbeat, a
butterfly's flutter) is slowed to 30 ms a frame and labelled with how much (x1/4). The motion's source is named: the
behaviour (WallCat, Dog, GroundBird, TreeSquirrel, PondDuck, CritterIdle, FlitButterfly) and its numbers, which the
kit's manifest records for the level builder (`game` in `KamakuraAnimals.json`).

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
6. The outline is whole: parts close to the background's grey are found (the kite's pale tail, a grey pigeon, a
   squirrel's grey-brown fur: by texture as well as colour, D18), and nothing of the background or the shadow is
   included (the squirrel's shadow). Judged against the picture at full size, part by part.
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
16. Feet planted, measured (D19): through every motion each foot point's height, and the lowest point of every leg
    (the posed skin's leg vertices: thigh, shin and toes), is read from the posed model. No foot or leg goes more than 1 % of the animal's height
    below the ground, some foot is always down in a walk, and no foot moves in a peck. A foot point on the ground says
    nothing of the toes beside it: a bird's long toes, rigid in its shin, sank by a fifth of its height while every
    foot point stood (D20); each foot is now its own part, kept level. The numbers are printed on the review.
17. Each part holds only itself (D20: birds walked on four legs, a raised leg stayed in the body as a third, fins were
    cut in two, all while checks 1 to 16 passed). The model's parts are drawn in colour on its picture at full size
    (`parts/<Model>.jpg` beside its source on the review), and each is looked at. Each leg part holds one leg. A far leg
    is copied from the near one only where the picture hides it. The body keeps nothing a motion should carry (a toe, a
    raised leg, a plume's tip), and a part carries nothing that should stay (a strip of tail on a leg, belly fur on a
    thigh). No fin is cut across two links. Where shape can't part them, legs and fins are drawn on the sheet
    (`leg_area`, `leg_lines`, `leg_drop`, `leg_seeds`, `front_fins`).

A check is marked passed only after the thing it names has been looked at for that asset, and its note says what was
looked at (D18: "checked on the cuts sheet" was written for 43 cut-outs before the sheet was read).

## 4. What the user is shown

One review per asset or per kit: the eight views, the motions, the asset beside its source and its part map, the
checks with their results (passed, or the fault and what is being done about it). It is published as a page the user
can open on a phone (an Artifact), the files kept in `review/<city>/`. A check that fails is said plainly, never left
for the user to find.
