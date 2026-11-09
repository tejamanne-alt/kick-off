// The camera's finishing pass (see PostFX.cs): a faint bloom on the brightest highlights, then the
// grade of the anime look (docs/ART_DIRECTION.md): a white balance, a toe that sinks the darkest
// tones into deep cool shadow, a little contrast, a shoulder that rolls the highlights off below
// pure white (whites read as paper, not as a blown light), vibrance (quiet colours lifted a touch,
// strong ones left alone), a split tone (cool shadows, faintly mauve mid-greys) and a light
// vignette. Cheap enough for phones: the bloom works on a quarter-size chain of a few textures.
//
// The comic halftone filter (Settings, Add-ons & Filters; passes 4 and 5) draws the graded picture
// as a printed comic: punchier colour stepped into cel bands, the shade as a 45-degree halftone dot
// screen, hatching in the deepest shade, an ink line from the camera's depth and normals (the
// shapes, never the textures), then the colour plates printed a little out of register toward the
// edges of the frame, on warm paper with a faint grain. Everything takes it, the characters and the
// ball too. They mark themselves in the picture's alpha (ToonCharacter's _ComicWorld = 0) only so the
// ink line draws no creases across them (a nose, a cheek, the edge of an eye would cross the painted
// face) and the plates slip half as far: their outlines come from the depth jump and their own ink hull.
//
// The pencil sketch filter (pass 6) draws it on warm paper instead: a faint wash of the colour (the
// figures keep theirs, so the kid is easy to find), pencil hatching for the tone, the sky left open, and
// the outline drawn twice with a wandering offset, from the same depth and normals and figure mask.
//
// The classic cartoon filter (passes 7 to 9; the look of the classic theatrical cartoons: inked cels over a painted
// background) grades the picture (7), smooths and colours it (8: Shaders/DtsCartoon.cginc) and inks it (9): the
// people, the ball and the things the kid plays with become cels (flat tones, a bold warm-black outline drawn only
// outside them, so it never covers a face); the scenery is painted (no black lines: warm, saturated colour, faint brush
// streaks, darker strokes of its own colour between forms); the sky is a flat turquoise; a faint grain and vignette.
//
// The picture's alpha says what each pixel is (ToonCharacter's _ComicWorld, Toon's _FilterMask): 0 a person or the
// ball, 0.125 a cel (a car, a coin, an animal, a crate, a cone...), 0.5 foliage, 0.75 a cloud, 1 the scenery. The comic
// and sketch filters read it as alpha x 8 (0 a figure, anything else the street), as they always have.
Shader "Hidden/DribbleToSchool/PostFX"
{
    Properties { _MainTex ("Source", 2D) = "white" {} }

    CGINCLUDE
    #include "UnityCG.cginc"
    #include "DtsCartoon.cginc"
    sampler2D _MainTex;
    float4 _MainTex_TexelSize;
    sampler2D _BloomTex;
    float _Threshold, _Knee, _BloomIntensity, _Saturation, _Vibrance, _Contrast, _Vignette;
    float _ToeEnd, _ToeFloor, _Shoulder, _WhitePoint;
    fixed4 _BloomTint;
    float4 _Balance, _ShadowTint, _MidTint, _HighlightTint;   // full precision: the tints are tiny (lowp would round them away)

    static const half3 lum = half3(0.299, 0.587, 0.114);

    struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };
    v2f vert (appdata_img v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.uv = v.texcoord; return o; }

    half3 Box4(float2 uv, float d)
    {
        float4 o = _MainTex_TexelSize.xyxy * float4(-d, -d, d, d);
        return (tex2D(_MainTex, uv + o.xy).rgb + tex2D(_MainTex, uv + o.zy).rgb + tex2D(_MainTex, uv + o.xw).rgb + tex2D(_MainTex, uv + o.zw).rgb) * 0.25;
    }

    // The grade (pass 3), shared with the comic pass: bloom, balance, toe, contrast, shoulder,
    // vibrance and split tone (the vignette is Vignette, after).
    half3 GradeColour(half3 c, float2 uv)
    {
        c += tex2D(_BloomTex, uv).rgb * _BloomTint.rgb * _BloomIntensity;
        c = max(c * _Balance.rgb, 0);
        // Toe: tones below _ToeEnd sink toward _ToeFloor of themselves; mid-tones are untouched.
        c *= lerp(_ToeFloor.xxx, half3(1, 1, 1), smoothstep(half3(0, 0, 0), _ToeEnd.xxx, c));
        c = (c - 0.5) * _Contrast + 0.5;
        // Shoulder: above _Shoulder, ease toward _WhitePoint instead of clipping.
        half range = max(_WhitePoint - _Shoulder, 1e-3);
        half3 rolled = _Shoulder + range * (1 - exp(-max(c - _Shoulder, 0) / range));
        c = lerp(c, rolled, step(_Shoulder.xxx, c));
        // Vibrance: greys and soft colours take _Vibrance, strong colours _Saturation.
        half l = dot(c, lum);
        half hi = max(c.r, max(c.g, c.b)), lo = min(c.r, min(c.g, c.b));
        half sat = (hi - lo) / max(hi, 1e-3);
        c = l + (c - l) * lerp(_Vibrance, _Saturation, smoothstep(0, 0.6, sat));
        // Split tone by brightness.
        l = dot(c, lum);
        half shadows = saturate(1 - l * 2); shadows *= shadows;
        half lights = saturate(l * 2 - 1); lights *= lights;
        half mids = saturate(1 - abs(l - 0.45) / 0.3);
        c += shadows * _ShadowTint.rgb + mids * _MidTint.rgb + lights * _HighlightTint.rgb;
        return c;
    }

    half3 Vignette(half3 c, float2 uv)
    {
        float2 p = uv - 0.5;
        return saturate(c * (1 - _Vignette * smoothstep(0.25, 0.85, dot(p, p) * 2.2)));
    }

    half3 Grade(half3 c, float2 uv) { return Vignette(GradeColour(c, uv), uv); }

    // ---- The comic halftone filter -----------------------------------------------------------
    sampler2D _CameraDepthNormalsTexture;
    float _MaskOn;            // 1 when the picture's alpha carries the character mask
    float _ComicSat, _ComicContrast, _Bands, _BandMix;
    float _DotPeriod, _DotReach, _DotSize, _DotStrength, _CharacterDots;
    float _HatchStrength;
    float _InkWidth, _InkStrength, _InkFar, _DepthEdge, _NormalEdge;
    float _SlipEdge, _Grain;
    float4 _InkColor, _PaperColor;

    void DepthNormal(float2 uv, out float depth, out float3 n)
    {
        DecodeDepthNormal(tex2D(_CameraDepthNormalsTexture, uv), depth, n);
    }

    // The ink line: where the depth jumps (an outline: one thing in front of another) or the
    // surface turns (a crease: a building's corner, a kerb, a roof's edge). From the shapes, so the
    // textures' noise never draws a line. Thins away into the distance.
    half InkLine(float2 uv, half world)
    {
        float2 o = _MainTex_TexelSize.xy * _InkWidth;
        float d0, d1, d2, d3, d4;
        float3 n0, n1, n2, n3, n4;
        DepthNormal(uv, d0, n0);
        DepthNormal(uv + float2(o.x, 0), d1, n1);
        DepthNormal(uv - float2(o.x, 0), d2, n2);
        DepthNormal(uv + float2(0, o.y), d3, n3);
        DepthNormal(uv - float2(0, o.y), d4, n4);
        float near = min(d0, min(min(d1, d2), min(d3, d4)));
        float jump = max(max(abs(d1 - d0), abs(d2 - d0)), max(abs(d3 - d0), abs(d4 - d0))) / max(near, 1e-4);
        half depthLine = smoothstep(_DepthEdge, _DepthEdge * 2.5, jump);
        float turn = 1 - min(min(dot(n0, n1), dot(n0, n2)), min(dot(n0, n3), dot(n0, n4)));
        // Creases only on the street: a character's own folds (nose, cheeks, fingers) stay unlined.
        half crease = smoothstep(_NormalEdge, _NormalEdge * 2, turn) * world;
        float eye = near * _ProjectionParams.z;
        half fade = 1 - smoothstep(_InkFar * 0.45, _InkFar, eye);
        return saturate(max(depthLine, crease)) * fade * _InkStrength;
    }

    // A 45-degree dot screen: 0 at a dot's centre, about 0.7 at the corner of its cell.
    float DotDistance(float2 px, float period)
    {
        float2 r = float2(px.x + px.y, px.x - px.y) / (period * 1.41421356);
        return length(r - floor(r + 0.5));
    }

    float Hash(float2 p)
    {
        p = frac(p * float2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return frac(p.x * p.y);
    }

    // ---- The pencil sketch filter ----------------------------------------------------------
    sampler2D _NoiseTex;      // 256 x 256 random values, bilinear, repeating: value noise (PostFX.cs)
    float _SketchWash, _FigureWash, _HatchSpacing, _SketchHatch, _LineJitter, _SketchLine;
    float4 _Graphite, _Paper;

    // Smooth noise 0..1 with cells of `cell` pixels (a different `seed` reads another part of the texture).
    float Noise(float2 px, float cell, float seed)
    {
        return tex2D(_NoiseTex, px / (cell * 256.0) + float2(seed * 0.371, seed * 0.613)).r;
    }

    float LaneHash(float lane, float seed)
    {
        return frac(sin(lane * 12.9898 + seed * 78.233) * 43758.5453);
    }

    // One set of pencil strokes across `angle` degrees, `spacing` px apart, pressed harder the darker the tone:
    // strokes of finite length with gaps, offset lane by lane, wobbling, with pencil grain on them.
    float Hatch(float2 px, float angle, float spacing, float tone, float threshold, float grain, float wob, float seed)
    {
        float a = radians(angle);
        float across = (px.x * cos(a) + px.y * sin(a)) / spacing + (wob - 0.5) * 0.5;
        float along = (-px.x * sin(a) + px.y * cos(a)) / spacing;
        float lane = floor(across + 0.5);
        float d = abs(across - lane) * spacing;
        float stroke = saturate(1 - (d - 0.45) / 0.9);
        float seg = frac(along / (5.5 + 3 * LaneHash(lane, seed)) + LaneHash(lane, seed + 7));
        stroke *= step(0.12, seg) * smoothstep(0.12, 0.2, seg) * (1 - smoothstep(0.92, 1.0, seg));
        float pressure = smoothstep(threshold, threshold - 0.22, tone);
        return stroke * pressure * (0.55 + 0.45 * grain);
    }

    // ---- The classic cartoon filter (the colour itself is in DtsCartoon.cginc) ----------------
    float _ClassicScale;      // sizes in pixels at 1080 lines -> this picture
    float _Finish, _FormEdge, _FormDark, _FormStrength;
    float _Brush, _BrushLength, _CelLine, _CelLineFar, _ClassicGrain, _ClassicVignette;
    float4 _SkyTop, _SkyLow, _CloudShade;

    // What a pixel is, from the exact code in alpha (read at the pixel's centre).
    half CodeCel(half a) { return step(a, 0.3); }
    half CodeLeaf(half a) { return 1 - smoothstep(0.08, 0.16, abs(a - 0.5)); }
    half CodeCloud(half a) { return 1 - smoothstep(0.08, 0.16, abs(a - 0.75)); }
    // How much of a cel a bilinear read between codes covers (soft across an edge: the outline's anti-aliasing).
    half CelCover(half a) { return saturate((0.3 - a) / 0.18); }

    float Depth01(float2 uvDN) { return DecodeFloatRG(tex2D(_CameraDepthNormalsTexture, uvDN).zw); }

    // The depth and normals texture is never flipped; the picture can be (Direct3D-style platforms with
    // anti-aliasing): a screen-space offset in the picture's uv, and the matching uv in the depth texture.
    float FlipY()
    {
        #if UNITY_UV_STARTS_AT_TOP
        if (_MainTex_TexelSize.y < 0) return -1;
        #endif
        return 1;
    }
    ENDCG

    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        // 0: bright-pass and downsample
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target
            {
                half3 c = Box4(i.uv, 1.0);
                half br = max(c.r, max(c.g, c.b));
                half soft = clamp(br - _Threshold + _Knee, 0, 2 * _Knee);
                soft = soft * soft / (4 * _Knee + 1e-4);
                half w = max(soft, br - _Threshold) / max(br, 1e-4);
                return half4(c * w, 1);
            }
            ENDCG
        }
        // 1: downsample
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target { return half4(Box4(i.uv, 1.0), 1); }
            ENDCG
        }
        // 2: upsample, added onto the bigger level
        Pass
        {
            Blend One One
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target { return half4(Box4(i.uv, 0.5), 1); }
            ENDCG
        }
        // 3: final: bloom, grade, vignette
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target { return half4(Grade(tex2D(_MainTex, i.uv).rgb, i.uv), 1); }
            ENDCG
        }
        // 4: comic: the grade, then colour, cel bands, halftone, hatching and the ink line.
        //    Keeps the character mask in alpha for pass 5.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            half4 frag (v2f i) : SV_Target
            {
                half4 src = tex2D(_MainTex, i.uv);
                half world = lerp(1, saturate(src.a * 8), _MaskOn);    // 1 the street, 0 a character or the ball
                // The vignette comes last: its soft fall-off would otherwise be stepped into an arc by the bands.
                half3 c = saturate(GradeColour(src.rgb, i.uv));

                // Punchier colour, on everything: the street and the figures alike.
                half l = dot(c, lum);
                half3 vivid = saturate(l + (c - l) * _ComicSat);
                vivid = saturate((vivid - 0.5) * _ComicContrast + 0.5);
                c = vivid;

                // Cel bands: brightness stepped, hue kept. The light tones stay smooth: lit white walls, paving,
                // shirts and the whites of the eyes sit near a step, and a step through them would break them
                // into blotches.
                l = dot(c, lum);
                half stepped = floor(l * _Bands + 0.5) / _Bands;
                half banded = lerp(l, stepped, _BandMix * (1 - smoothstep(0.62, 0.74, l)));
                c = saturate(c * (banded / max(l, 1e-3)));

                // Halftone: the shade drawn as dots in a darker, bluer ink of the colour under them.
                float2 px = i.uv * _MainTex_TexelSize.zw;
                l = dot(c, lum);
                half cover = saturate((_DotReach - l) / 0.5) * _DotSize * lerp(_CharacterDots, 1, world);
                float d = DotDistance(px, _DotPeriod);
                half dotMask = saturate((cover - d) * _DotPeriod * 0.9 + 0.5) * step(0.02, cover);
                half3 dotInk = c * 0.55 * half3(0.85, 0.8, 1.0);
                c = lerp(c, dotInk, dotMask * _DotStrength);

                // Hatching in the deepest shade.
                half hatch = step(0.35, sin((px.x - px.y) * 3.14159 / (_DotPeriod * 0.48)));
                half deep = saturate((0.28 - l) / 0.15) * hatch;
                c *= 1 - deep * _HatchStrength;

                // The ink line. The depth and normals texture is never flipped; the picture can be
                // (Direct3D-style platforms with anti-aliasing): read it the right way up.
                float2 uvDN = i.uv;
                #if UNITY_UV_STARTS_AT_TOP
                if (_MainTex_TexelSize.y < 0) uvDN.y = 1 - uvDN.y;
                #endif
                half ink = InkLine(uvDN, world);
                c = lerp(c, _InkColor.rgb, ink);
                return half4(Vignette(c, i.uv), src.a);
            }
            ENDCG
        }
        // 5: comic: the red and blue plates slip out of register toward the frame's edges (none at
        //    the centre, where the kid plays; half as far on a figure), then warm paper and a faint grain.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target
            {
                half4 s = tex2D(_MainTex, i.uv);
                float2 p = (i.uv - float2(0.5, 0.55)) / float2(0.5, 0.55);
                float r = saturate(length(p) - 0.35);
                // The people and the ball slip half as far, so their eyes stay crisp anywhere on screen.
                half world = lerp(1, saturate(s.a * 8), _MaskOn);
                float2 off = float2(_MainTex_TexelSize.x * _SlipEdge * r * lerp(0.5, 1, world), 0);
                half3 c = s.rgb;
                c.r = tex2D(_MainTex, i.uv + off).r;
                c.b = tex2D(_MainTex, i.uv - off).b;
                c = c * (1 - _PaperColor.a) + _PaperColor.rgb * _PaperColor.a;
                float2 px = floor(i.uv * _MainTex_TexelSize.zw);
                c += (Hash(px) - 0.5) * _Grain;
                return half4(saturate(c), 1);
            }
            ENDCG
        }
        // 6: pencil sketch: the grade, then paper, a wash of the colour (the figures keep theirs), pencil
        //    hatching by tone (one way, crossed, then a dense third set), the sky left open, and the outline
        //    drawn twice with a wandering offset from the depth and normals (no creases across a figure).
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            half4 frag (v2f i) : SV_Target
            {
                half4 src = tex2D(_MainTex, i.uv);
                half world = lerp(1, saturate(src.a * 8), _MaskOn);
                half3 c = saturate(GradeColour(src.rgb, i.uv));
                half tone = dot(c, lum);
                float2 px = i.uv * _MainTex_TexelSize.zw;
                float scale = _MainTex_TexelSize.w / 1080.0;

                float fibre = Noise(px, max(2.0, 3.0 * scale), 1);
                float grain = Noise(px, 1.0, 2);
                float wob = Noise(px, 60.0 * scale, 3);
                float blot = Noise(px, 90.0 * scale, 4);

                // Paper, and the wash on it.
                half3 paper = _Paper.rgb * (1 - 0.05 * fibre);
                half3 soft = 0.32 + 0.68 * (tone + (c - tone) * 0.85);
                half amount = lerp(max(_SketchWash, _FigureWash), _SketchWash, world) * (0.75 + 0.5 * blot);
                half3 col = paper * (1 + (soft - 1) * amount);

                float2 uvDN = i.uv;
                #if UNITY_UV_STARTS_AT_TOP
                if (_MainTex_TexelSize.y < 0) uvDN.y = 1 - uvDN.y;
                #endif
                float d0; float3 n0;
                DepthNormal(uvDN, d0, n0);

                // Hatching, lighter on the figures, none in the sky.
                float sp = _HatchSpacing * scale;
                float hat = Hatch(px, 45, sp, tone, 0.78, grain, wob, 11);
                hat = max(hat, Hatch(px, -45, sp, tone, 0.52, grain, wob, 23));
                hat = max(hat, Hatch(px, 12, sp * 0.7, tone, 0.3, grain, wob, 37));
                hat *= (0.55 + 0.45 * world) * step(d0, 0.999);
                col = lerp(col, _Graphite.rgb, hat * _SketchHatch);

                // The doubled, wandering outline.
                float j1 = (Noise(px, 40.0 * scale, 5) - 0.5) * _LineJitter * scale;
                float j2 = (Noise(px, 40.0 * scale, 6) - 0.5) * _LineJitter * scale;
                float2 t = _MainTex_TexelSize.xy;
                half e1 = InkLine(uvDN + float2(-j2, -j1) * t, world);
                half e2 = InkLine(uvDN + float2(j1, j2) * 0.8 * t, world);
                half outline = saturate(max(e1 * 0.9, e2 * 0.55)) * (0.7 + 0.3 * grain);
                col = lerp(col, _Graphite.rgb, outline * _SketchLine);

                // The paper's edge.
                float2 p = i.uv - 0.5;
                col *= 1 - 0.1 * smoothstep(0.3, 0.9, dot(p, p) * 2.2);
                return half4(saturate(col), 1);
            }
            ENDCG
        }
        // 7: classic cartoon: the grade (no vignette), in display values, the code in alpha kept for passes 8 and 9.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target
            {
                half4 s = tex2D(_MainTex, i.uv);
                return half4(CartoonToDisplay(saturate(GradeColour(s.rgb, i.uv))), lerp(1, s.a, _MaskOn));
            }
            ENDCG
        }
        // 8: classic cartoon: the cored smoothing (25 reads), then the cels' colour or the painted scenery's, the clouds
        //    white, the sky a flat turquoise. Reads pass 7's picture; keeps the code in alpha for pass 9.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            half4 frag (v2f i) : SV_Target
            {
                float2 t = abs(_MainTex_TexelSize.xy) * _ClassicScale;
                half4 s = tex2D(_MainTex, i.uv);
                half cel = CodeCel(s.a), leaf = CodeLeaf(s.a), cloud = CodeCloud(s.a);
                float2 uvDN = i.uv;
                #if UNITY_UV_STARTS_AT_TOP
                if (_MainTex_TexelSize.y < 0) uvDN.y = 1 - uvDN.y;
                #endif
                half sky = step(0.999, Depth01(uvDN));

                float3 m0, m1, m2, m3, cross;
                float v0, v1, v2, v3;
                CARTOON_SECTORS(_MainTex, i.uv, t, m0, m1, m2, m3, v0, v1, v2, v3, cross)
                // The cels' smoothing lets the calmest side win harder (q 6) than the scenery's (q 4).
                half3 flat = lerp(CartoonBlend(m0, m1, m2, m3, v0, v1, v2, v3, 4), CartoonBlend(m0, m1, m2, m3, v0, v1, v2, v3, 6), cel);

                // The scenery is sharpened a little first; the cels (faces) and the foliage (it would speckle) are not.
                half3 c = s.rgb;
                half3 c0 = lerp(c, saturate(c + (c - (half3)cross) * _Sharpen), (1 - cel) * (1 - leaf));
                // The cels and the foliage keep only strong detail (eyes, brows, seams; a crown in painted clumps).
                half strong = max(cel, leaf);
                half3 p = CartoonCore(c0, flat, lerp(_CoreFrom, _CelCoreFrom, strong), lerp(_CoreTo, _CelCoreTo, strong));
                half3 o = lerp(CartoonPainted(p, 1), CartoonCel(p), cel);

                // The clouds white, with a soft blue-grey shade.
                half l = dot(c, cartoonLum);
                half3 white = (1 - (1 - l) * 0.9) * pow(_CloudShade.rgb, 1 - smoothstep(0.75, 0.95, l));
                o = lerp(o, saturate(white), cloud);
                // The sky: a flat turquoise, pale toward the horizon (uvDN.y is up the screen).
                half3 skyColour = lerp(_SkyTop.rgb, _SkyLow.rgb, pow(saturate(1 - uvDN.y), 1.4));
                o = lerp(o, skyColour, sky);
                return half4(o, s.a);
            }
            ENDCG
        }
        // 9: classic cartoon: a light finishing sharpen on the scenery, faint brush streaks, darker strokes of the
        //    scenery's own colour where colours meet and where a nearer form overlaps a farther one, the cels' warm-black
        //    outline drawn only on the far side of their edges (it never covers a face), then a faint grain and vignette.
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            half4 frag (v2f i) : SV_Target
            {
                float2 px = abs(_MainTex_TexelSize.xy);
                float flip = FlipY();
                float sc = _ClassicScale;
                half4 s = tex2D(_MainTex, i.uv);
                half cel = CodeCel(s.a), leaf = CodeLeaf(s.a), cloud = CodeCloud(s.a);
                float2 uvDN = i.uv;
                if (flip < 0) uvDN.y = 1 - uvDN.y;
                float d0; float3 n0;
                DepthNormal(uvDN, d0, n0);
                half sky = step(0.999, d0);
                half scenery = (1 - cel) * (1 - sky) * (1 - cloud);
                float eye = d0 * _ProjectionParams.z;
                half fade = 1 - smoothstep(40, 120, eye);
                half3 c = s.rgb;

                // The eight neighbours, one step out (the finishing sharpen and the strokes).
                float2 o1 = px * sc;
                half3 cR = tex2D(_MainTex, i.uv + float2(o1.x, 0)).rgb, cL = tex2D(_MainTex, i.uv - float2(o1.x, 0)).rgb;
                half3 cU = tex2D(_MainTex, i.uv + float2(0, o1.y)).rgb, cD = tex2D(_MainTex, i.uv - float2(0, o1.y)).rgb;
                half3 cRU = tex2D(_MainTex, i.uv + o1).rgb, cLD = tex2D(_MainTex, i.uv - o1).rgb;
                half3 cRD = tex2D(_MainTex, i.uv + float2(o1.x, -o1.y)).rgb, cLU = tex2D(_MainTex, i.uv + float2(-o1.x, o1.y)).rgb;
                c = lerp(c, saturate(c + (c - (cR + cL + cU + cD) * 0.25) * _Finish), scenery * (1 - leaf));

                // Brush streaks: across the ground (normals facing up), down the walls; a tiling noise, stretched.
                float2 pxc = i.uv * abs(_MainTex_TexelSize.zw);
                float len = _BrushLength * sc;
                half across = tex2D(_NoiseTex, float2(pxc.x / (len * 256.0), pxc.y / 512.0)).r - 0.5;
                half down = tex2D(_NoiseTex, float2(pxc.x / 512.0, pxc.y / (len * 256.0)) + float2(0.37, 0.61)).r - 0.5;
                half up = smoothstep(0.45, 0.75, n0.y);
                half streak = across * up + down * (1 - up) * 0.45;
                c = saturate(c * (1 + streak * _Brush * 2 * (1 - smoothstep(25, 90, eye)) * scenery));

                // Darker strokes of the scenery's own colour where its flat colours meet...
                half stepAcross = max(max(CartoonStepAcross(cR, cL), CartoonStepAcross(cU, cD)), max(CartoonStepAcross(cRU, cLD), CartoonStepAcross(cRD, cLU)));
                half stroke = smoothstep(_StrokeEdge, _StrokeEdge * 1.8, stepAcross);
                c = lerp(c, c * _StrokeDark, stroke * _StrokeStrength * (1 - leaf * 0.7) * fade * scenery);
                // ...and where a nearer form overlaps a farther one (foliage needs a bigger jump: a crown, not its clumps).
                float d1 = Depth01(uvDN + float2(o1.x, 0)), d2 = Depth01(uvDN - float2(o1.x, 0));
                float d3 = Depth01(uvDN + float2(0, o1.y)), d4 = Depth01(uvDN - float2(0, o1.y));
                float nearD = min(d0, min(min(d1, d2), min(d3, d4)));
                float jump = max(max(abs(d1 - d0), abs(d2 - d0)), max(abs(d3 - d0), abs(d4 - d0))) / max(nearD, 1e-4);
                half formEdge = _FormEdge * (1 + 3 * leaf);
                half form = smoothstep(formEdge, formEdge * 1.6, jump);
                c = lerp(c, c * _FormDark, form * _FormStrength * fade * scenery);

                // The cels' outline: a pixel is inked when a cel lies in front of it within the line's width, so the line
                // falls on the far side of every edge (outside a figure, or on a farther part behind a nearer one) and never
                // over a face. Its width follows the nearer side's distance; read at two radii so thin limbs keep it.
                float R = 4 * sc;
                float dNear = min(d0, min(min(Depth01(uvDN + float2(R * px.x, 0)), Depth01(uvDN - float2(R * px.x, 0))),
                                          min(Depth01(uvDN + float2(0, R * px.y)), Depth01(uvDN - float2(0, R * px.y)))));
                float width = lerp(_CelLine, _CelLineFar, smoothstep(4, 60, dNear * _ProjectionParams.z)) * sc + 0.5;
                static const float2 dirs[8] = { float2(1, 0), float2(-1, 0), float2(0, 1), float2(0, -1),
                                                float2(0.7071, 0.7071), float2(-0.7071, 0.7071), float2(0.7071, -0.7071), float2(-0.7071, -0.7071) };
                half ink = 0;
                [unroll] for (int k = 0; k < 12; k++)
                {
                    float2 o = dirs[k % 8] * width * (k < 8 ? 1.0 : 0.5) * px;
                    half a = tex2D(_MainTex, i.uv + o).a;                    // bilinear: soft across an edge
                    float dk = Depth01(uvDN + float2(o.x, o.y * flip));
                    half nearer = smoothstep(0.03, 0.07, (d0 - dk) / max(dk, 1e-4));
                    ink = max(ink, CelCover(a) * nearer);
                }
                c = lerp(c, _CelInk.rgb, ink);

                // The print: a soft vignette and a faint grain.
                float2 v = i.uv - 0.5;
                c *= 1 - _ClassicVignette * smoothstep(0.3, 0.9, dot(v, v) * 2.2);
                c += (Hash(floor(pxc)) - 0.5) * _ClassicGrain;
                return half4(CartoonFromDisplay(saturate(c)), 1);
            }
            ENDCG
        }
    }
}
