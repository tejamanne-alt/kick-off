// Anime-style shading for characters, the ball and other smooth, rounded things, drawn to
// stand apart from the painterly street: two flat cel bands (lit and a cool shadow) from the
// global sun, a rim of light round the silhouette (strongest on the sunny side), a dark ink
// outline of constant on-screen width (an inverted hull pushed out along the smooth normals),
// and the same distance haze as the street. Colours come from the vertex colours times the
// texture and tint. Lighting and haze are set by WorldLook.
// For a clean figure at any size (docs/LEARNINGS.md, "The characters looked low quality"):
// - the outline is pushed out by the same number of pixels whichever way the edge runs (the push
//   is measured in pixels, not in clip space, which squashed it on wide screens), never thinner
//   than _OutlineMinPx (a 720-line picture would make it a hairline), and set a little behind
//   the figure (_OutlinePush), so the small folds inside the silhouette draw no specks of ink;
// - the step from shade to light is as narrow as before but anti-aliased: it widens to a pixel
//   where the surface turns faster than a pixel can show, instead of shimmering;
// - the rim is a narrower band and takes the colour under it (hair stays dark hair with a soft
//   sheen, not white flecks).
// Alpha carries _ComicWorld for the filters (Shaders/PostFX): 0 (people and the ball) takes the comic filter
// except creases across it (its painted face and eyes stay clear) and slips half as far; 0.125 (the cars: a cel) is
// drawn like the street by the comic and sketch filters (creases and all) and as an inked cel by the classic cartoon,
// as the people are; 1 is drawn like the street by every filter.
// A texture whose alpha is below 1 marks a part that can be recoloured (a Locker Room bag's cloth: tools/blender/
// meshy_bag.py): with _MaskTint's alpha up, those texels take _MaskTint's colour, as light or dark as they were
// against _MaskBase (the part's own colour). Opaque textures (every other model) are drawn as they are.
Shader "DribbleToSchool/ToonCharacter"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _ShadowColor ("Shadow tint", Color) = (0.74,0.72,0.9,1)
        _RimStrength ("Rim light", Range(0,1)) = 0.3
        _OutlineColor ("Outline colour", Color) = (0.08,0.07,0.1,1)
        _OutlineWidth ("Outline width (fraction of screen height)", Float) = 0.0022
        _OutlineMinPx ("Outline: never thinner than (pixels)", Float) = 1.25
        _OutlinePush ("Outline: set back from the camera (m)", Float) = 0.012
        _ComicWorld ("Filters: a figure (0), a cel (0.125: the cars) or the street (1)", Range(0,1)) = 0
        _MaskTint ("Recolour of the texture's marked part (alpha 0: none)", Color) = (1,1,1,0)
        _MaskBase ("The marked part's own colour", Color) = (0.5,0.5,0.5,1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100

        CGINCLUDE
        #include "UnityCG.cginc"
        #include "AutoLight.cginc"
        #include "DtsLook.cginc"

        sampler2D _MainTex;
        float4 _MainTex_ST;
        fixed4 _Color;
        fixed4 _ShadowColor;
        float _RimStrength;
        fixed4 _OutlineColor;
        float _OutlineWidth;
        float _OutlineMinPx;
        float _OutlinePush;
        float _ComicWorld;
        fixed4 _MaskTint;
        fixed4 _MaskBase;

        // The texture with its marked part (alpha below 1) recoloured to _MaskTint, keeping its light and shade.
        fixed4 MaskedTexture(float2 uv)
        {
            fixed4 tex = tex2D(_MainTex, uv);
            float m = (1.0 - tex.a) * _MaskTint.a;
            const float3 lumW = float3(0.299, 0.587, 0.114);
            float k = dot(tex.rgb, lumW) / max(dot(_MaskBase.rgb, lumW), 0.001);
            tex.rgb = lerp(tex.rgb, saturate(_MaskTint.rgb * k), m);
            tex.a = 1.0;
            return tex;
        }
        ENDCG

        // Ink outline: back faces pushed out in clip space, so the line stays the same
        // thickness on screen at any distance. Tinted toward a dark version of the surface.
        Pass
        {
            Name "Outline"
            Cull Front
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; fixed4 color : COLOR; };
            struct v2f { float4 pos : SV_POSITION; fixed4 color : COLOR; float3 worldPos : TEXCOORD0; };

            v2f vert (appdata v)
            {
                v2f o;
                // set back a little from the camera, so only the true silhouette shows round the figure
                float3 viewPos = UnityObjectToViewPos(v.vertex);
                viewPos.z -= _OutlinePush;
                o.pos = mul(UNITY_MATRIX_P, float4(viewPos, 1.0));
                float3 worldNormal = UnityObjectToWorldNormal(v.normal);
                // the normal's direction on screen, in pixels (so a slanted edge is as thick as an upright one)
                float2 dir = mul((float3x3)UNITY_MATRIX_VP, worldNormal).xy * _ScreenParams.xy;
                float len = length(dir);
                if (len > 0.0001)
                {
                    float px = max(_OutlineWidth * _ScreenParams.y, _OutlineMinPx);
                    o.pos.xy += (dir / len) * px * 2.0 / _ScreenParams.xy * o.pos.w;
                }
                o.color = v.color;
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed3 col = lerp(_OutlineColor.rgb, i.color.rgb * _Color.rgb * 0.3, 0.2);
                col = DtsHaze(col, i.worldPos, 1.0);
                return fixed4(col, _ComicWorld);
            }
            ENDCG
        }

        Pass
        {
            Name "Toon"
            Tags { "LightMode"="ForwardBase" }
            Cull Back
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fwdbase nolightmap nodirlightmap nodynlightmap novertexlight
            #pragma target 3.0

            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
                fixed4 color : COLOR;
                SHADOW_COORDS(3)
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color;
                TRANSFER_SHADOW(o);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float3 n = normalize(i.normal);
                fixed4 tex = MaskedTexture(i.uv) * _Color * i.color;
                float3 l = DtsLightDir();
                float d = dot(n, l);
                // Two cel bands with a narrow soft edge (the anime look), the shade tinted by the
                // sky and the warm bounce like the street around it; sun shadows fall into the shade.
                // (the step's width: as before, or one pixel's worth of turn where the surface turns faster)
                float aa = max(fwidth(d), 0.04);
                float lit = smoothstep(0.02 - aa, 0.02 + aa, d) * lerp(0.15, 1.0, SHADOW_ATTENUATION(i));
                fixed3 col = lerp(tex.rgb * DtsShadeTint(_ShadowColor.rgb, n), tex.rgb * DtsSun(), lit);

                // A rim of light round the silhouette, brightest on the sunny side, so the figure
                // lifts off whatever is behind it; tinted by the colour under it, so dark hair keeps
                // a soft sheen rather than white flecks.
                float3 v = normalize(_WorldSpaceCameraPos - i.worldPos);
                float rim = smoothstep(0.66, 0.8, 1.0 - saturate(dot(n, v))) * lerp(0.4, 1.0, saturate(d + 0.35));
                col += rim * _RimStrength * DtsSun() * lerp(tex.rgb, fixed3(1, 1, 1), 0.45);

                col = DtsHaze(col, i.worldPos, 1.0);
                return fixed4(col, _ComicWorld);
            }
            ENDCG
        }
    }
    // The fallback supplies the shadow caster pass.
    FallBack "Legacy Shaders/VertexLit"
}
