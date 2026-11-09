# New passers-by: image prompts

Every adult in the game is one body, recoloured. Six new adults, made the way the playable kids were: an image of
each, turned into a rigged 3D model by an image-to-3D tool (the kids came from Meshy, rigged with its humanoid
skeleton), then brought into the game with `tools/blender/meshy_rigged.py` (one skinned mesh, the outfit's parts
recolourable, so each can still change coat colour as passers-by do).

## How to use them

1. Paste the **base prompt**, then one **character line** at its end.
2. **ChatGPT (GPT image):** ask for the 3-view sheet (front, side, back in one image, feet on one line). It keeps the
   three views consistent. Crop the views apart for the 3D tool's multi-view input, or use the front view alone.
3. **Gemini:** ask for the front view only, then edit that image: "Same character, same outfit and proportions, now
   seen from the left side, same A-pose, same background", and again for the back. Gemini keeps a character best
   by editing its own image rather than starting over.
4. In the 3D tool: image to 3D, humanoid, A-pose, auto-rig on, texture on, about 30k triangles, export **FBX with the
   skeleton** (no animation needed). Send the FBX (and the front image).

## Base prompt

> Full-body character design for a stylised 3D game character, front view, standing in a relaxed A-pose: arms held
> about 30 degrees away from the body, hands open and relaxed with palms facing the thighs, feet shoulder-width apart
> and pointing forward. Whole figure in frame from head to shoes, centred, with space around it. Orthographic, camera
> at chest height. Plain flat light-grey background, soft even studio lighting, no cast shadows, no props, nothing in
> the hands, no bag straps across the body. Stylised semi-realistic look of a modern animated mobile game: clean
> shapes, slightly large head and hands, friendly face with a neutral, pleasant expression, mouth closed. Clothing in
> clear, separate, mostly solid colour blocks (each garment one main colour), hair close to the head (no loose strands
> or flowing hair), trousers or a knee-length hem (nothing that hides the legs), closed shoes. No text, no logos, no
> patterns finer than a check, no watermark. The character:

## Character lines

1. **Morning jogger:** a woman in her early thirties, East Asian, slim and athletic, black hair in a high ponytail,
   a teal zip-up running jacket, black leggings, white running shoes, a small black sports watch.
2. **Grandad:** a man of about seventy, white, a little stout, short grey hair and a grey moustache, a brown flat cap,
   a mustard-yellow cardigan over a blue-and-white checked shirt, brown corduroy trousers, brown lace-up shoes.
3. **Office worker:** a man of about forty, Black, medium build, short cropped hair and a trimmed beard, a navy blazer
   over a pale-blue shirt with an open collar (no tie), mid-grey trousers, brown leather shoes.
4. **Parent on the school run:** a woman of about forty, South Asian, curvy, dark hair in a low bun, a coral knitted
   jumper, dark-green wide-leg trousers, white trainers.
5. **Delivery courier:** a young man of about twenty-five, Latino, lean, short curly black hair under a navy cap worn
   backwards, a plain red polo shirt (no logo), khaki knee-length cargo shorts, grey trainers with white socks.
6. **The shopkeeper:** a woman of about sixty, Middle Eastern, medium build, a plain blue headscarf, a long-sleeved
   lilac tunic to mid-thigh over dark-grey trousers, flat comfortable black shoes.

Optional, for the building site: **Builder:** a man of about fifty, broad, a yellow hard hat, an orange hi-vis vest
over a grey T-shirt, dark work trousers with knee pads, tan work boots.

## 3-view sheet (ChatGPT): add after the character line

> Show three views of this same character side by side on one wide image: front, left side, and back, all in the same
> A-pose, the same size, feet on the same line, evenly spaced, nothing overlapping.
