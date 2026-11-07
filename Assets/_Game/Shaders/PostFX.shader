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
// edges of the frame, on warm paper with a faint grain. The characters and the ball mark themselves
// in the picture's alpha (ToonCharacter's _ComicWorld = 0): they keep their own outline, painted
// faces and eyes, take no cel bands and no creases from the filter, only lighter dots in their shade.
Shader "Hidden/DribbleToSchool/PostFX"
{
    Properties { _MainTex ("Source", 2D) = "white" {} }

    CGINCLUDE
    #include "UnityCG.cginc"
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
                half world = lerp(1, saturate(src.a), _MaskOn);    // 1 the street, 0 a character or the ball
                // The vignette comes last: its soft fall-off would otherwise be stepped into an arc by the bands.
                half3 c = saturate(GradeColour(src.rgb, i.uv));

                // Punchier colour: the street takes it all, the characters half (their colours are already set).
                half l = dot(c, lum);
                half3 vivid = saturate(l + (c - l) * _ComicSat);
                vivid = saturate((vivid - 0.5) * _ComicContrast + 0.5);
                c = lerp(c, vivid, lerp(0.5, 1, world));

                // Cel bands on the street: brightness stepped, hue kept. The characters are cel-shaded already.
                // The light tones stay smooth: lit white walls and paving sit near a step, and a step through
                // them would break their faint texture into blotches.
                l = dot(c, lum);
                half stepped = floor(l * _Bands + 0.5) / _Bands;
                half banded = lerp(l, stepped, _BandMix * (1 - smoothstep(0.62, 0.74, l)));
                c = lerp(c, saturate(c * (banded / max(l, 1e-3))), world);

                // Halftone: the shade drawn as dots in a darker, bluer ink of the colour under them.
                float2 px = i.uv * _MainTex_TexelSize.zw;
                l = dot(c, lum);
                half cover = saturate((_DotReach - l) / 0.5) * _DotSize * lerp(_CharacterDots, 1, world);
                float d = DotDistance(px, _DotPeriod);
                half dotMask = saturate((cover - d) * _DotPeriod * 0.9 + 0.5) * step(0.02, cover);
                half3 dotInk = c * 0.55 * half3(0.85, 0.8, 1.0);
                c = lerp(c, dotInk, dotMask * _DotStrength);

                // Hatching in the deepest shade of the street.
                half hatch = step(0.35, sin((px.x - px.y) * 3.14159 / (_DotPeriod * 0.48)));
                half deep = saturate((0.28 - l) / 0.15) * hatch * world;
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
        //    the centre, where the kid plays; hardly any on a figure), then warm paper and a faint grain.
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
                // The people and the ball barely slip, so their faces stay sharp anywhere on screen.
                half world = lerp(1, saturate(s.a), _MaskOn);
                float2 off = float2(_MainTex_TexelSize.x * _SlipEdge * r * lerp(0.15, 1, world), 0);
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
    }
}
