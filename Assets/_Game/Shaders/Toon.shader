// The painterly surface shader for the 3D street (see docs/ART_DIRECTION.md):
// - a clear sun with a crisp, slightly soft step to shade (anime daylight), easing across the lit side;
// - shade sides that carry the sky's cool colour (hemispheric ambient: sky above, ground bounce
//   below), never black;
// - a gentle rim where surfaces turn away toward the sun;
// - real-time sun shadows from the scene's directional light, tinted like the shade side;
// - an optional world-space texture projection (so surfaces tile at any size), with soft
//   world-scale patches of lighter, darker, warmer and cooler ground so the repeat doesn't show;
// - a little blue distance haze, lighter toward the sun, so far layers sit back without fading out;
// - an optional breeze (_Wind) that sways vertices by their alpha (the plants kit's wind weight);
// - optional alpha cut-out (_ALPHATEST_ON, off by default) for the plants kit's leaf cards: the
//   texture's alpha against _Cutoff, cast shadows cut the same way. Cut-out texels (alpha below
//   0.97: the leaf sprites) can shrink away on cards seen edge-on (_EdgeFade) and take sun
//   shadows more softly (_LeafShadow); fully opaque texels (bark, needles) are never cut.
// Colours and directions come from globals set by WorldLook; the directional light only casts
// the shadows.
Shader "DribbleToSchool/Toon"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _ShadowColor ("Shadow tint", Color) = (0.72,0.76,0.9,1)
        _WorldUV ("Project texture in world space (0/1)", Float) = 0
        _WorldUVScale ("World texture scale (tiles per unit)", Float) = 0.125
        _Macro ("World-scale variation (world UV only)", Range(0,1)) = 0
        _Scroll ("Texture scroll (xy per second)", Vector) = (0,0,0,0)
        _Haze ("Distance haze amount", Range(0,1)) = 1
        _Rim ("Rim light", Range(0,1)) = 0.35
        _Wind ("Wind sway (m at the tips; vertex alpha weights it)", Range(0,0.5)) = 0
        [Toggle(_ALPHATEST_ON)] _AlphaClip ("Alpha cut-out (leaf cards)", Float) = 0
        _Cutoff ("Cut-out threshold", Range(0,1)) = 0.5
        _EdgeFade ("Cut-out cards fade when seen edge-on", Range(0,1)) = 0
        _LeafShadow ("Sun shadow strength on cut-out texels", Range(0,1)) = 1
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100
        Cull [_Cull]

        CGINCLUDE
        #include "UnityCG.cginc"

        sampler2D _MainTex;
        float4 _MainTex_ST;
        fixed4 _Color;
        float _Wind;
        float _Cutoff;
        float _EdgeFade;
        float _LeafShadow;

        // A gentle sway in the breeze: the plants kit bakes a wind weight into vertex alpha (0 at
        // the root, 1 at the tips); gusts roll along the street.
        float3 DtsWindSway(float3 worldPos, float weight)
        {
            if (_Wind > 0.0)
            {
                float phase = _Time.y * 1.3 + worldPos.x * 0.35 + worldPos.z * 0.2;
                float sway = sin(phase) * 0.6 + sin(phase * 2.3 + 1.7) * 0.25;
                float w = weight * _Wind;
                worldPos.x += sway * w;
                worldPos.z += sin(phase * 0.8 + 0.5) * w * 0.3;
            }
            return worldPos;
        }

        // Is this texel part of a cut-out sprite (the leaf sprites top out at alpha 0.9)?
        float DtsCutTexel(float alpha)
        {
            return alpha < 0.97 ? 1.0 : 0.0;
        }
        ENDCG

        Pass
        {
            Tags { "LightMode"="ForwardBase" }
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #pragma multi_compile_fwdbase nolightmap nodirlightmap nodynlightmap novertexlight
            #pragma multi_compile_instancing
            #pragma shader_feature_local _ALPHATEST_ON
            #include "AutoLight.cginc"
            #include "DtsLook.cginc"

            fixed4 _ShadowColor;
            float _WorldUV;
            float _WorldUVScale;
            float _Macro;
            float4 _Scroll;
            float _Haze;
            float _Rim;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
                fixed4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

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
                UNITY_SETUP_INSTANCE_ID(v);
                o.worldPos = DtsWindSway(mul(unity_ObjectToWorld, v.vertex).xyz, v.color.a);
                o.pos = mul(UNITY_MATRIX_VP, float4(o.worldPos, 1.0));
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color;
                TRANSFER_SHADOW(o);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float3 n = normalize(i.normal);
                float2 uv = i.uv;
                float2 plane = 0;
                if (_WorldUV > 0.5)
                {
                    // Project along the dominant axis: tops use xz, fronts xy, sides zy.
                    float3 a = abs(n);
                    plane = (a.y >= a.x && a.y >= a.z) ? i.worldPos.xz : ((a.x >= a.z) ? i.worldPos.zy : i.worldPos.xy);
                    uv = plane * _WorldUVScale;
                }
                uv += _Scroll.xy * _Time.y;
                fixed4 tex = tex2D(_MainTex, uv);
                float shadow = SHADOW_ATTENUATION(i);
            #if defined(_ALPHATEST_ON)
                // Leaf cards: cut the sprite out. A card turned nearly edge-on to the camera would
                // show as a smeared sliver, so its sprite shrinks away (the threshold rises past
                // the sprite's alpha) as it turns; solid texels keep the plain threshold.
                float alpha = tex.a * _Color.a;
                float cutTexel = DtsCutTexel(alpha);
                float3 faceN = cross(ddx(i.worldPos), ddy(i.worldPos));
                faceN *= rsqrt(max(dot(faceN, faceN), 1e-20));
                float facing = abs(dot(faceN, normalize(_WorldSpaceCameraPos - i.worldPos)));
                float edgeOn = (1.0 - smoothstep(0.4, 0.62, facing)) * _EdgeFade * cutTexel;
                clip(alpha - lerp(_Cutoff, 1.01, edgeOn));
                // Leaves take the sun's shadows more softly than wood and ground: their depth
                // is painted in already, and a crown's own shadow on itself would only add noise.
                shadow = lerp(shadow, lerp(1.0, shadow, _LeafShadow), cutTexel);
            #endif
                fixed3 albedo = (tex * _Color * i.color).rgb;
                if (_Macro > 0.001) albedo = DtsMacro(albedo, plane, _Macro);
                fixed3 col = DtsShade(albedo, n, i.worldPos, _ShadowColor.rgb, shadow, _Rim);
                col = DtsHaze(col, i.worldPos, _Haze);
                return fixed4(col, 1);
            }
            ENDCG
        }

        // Casts the sun's shadow: swayed like the surface, and cut out like it when _ALPHATEST_ON
        // is set (without the keyword this is the plain caster the VertexLit fallback gave).
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual
            CGPROGRAM
            #pragma vertex vertShadow
            #pragma fragment fragShadow
            #pragma multi_compile_shadowcaster
            #pragma multi_compile_instancing
            #pragma shader_feature_local _ALPHATEST_ON

            struct appdataShadow
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
                fixed4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2fShadow
            {
                V2F_SHADOW_CASTER;
                float2 uv : TEXCOORD1;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            v2fShadow vertShadow (appdataShadow v)
            {
                v2fShadow o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                if (_Wind > 0.0)
                {
                    float3 wp = DtsWindSway(mul(unity_ObjectToWorld, v.vertex).xyz, v.color.a);
                    v.vertex.xyz = mul(unity_WorldToObject, float4(wp, 1.0)).xyz;
                }
                TRANSFER_SHADOW_CASTER_NORMALOFFSET(o)
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            float4 fragShadow (v2fShadow i) : SV_Target
            {
            #if defined(_ALPHATEST_ON)
                clip(tex2D(_MainTex, i.uv).a * _Color.a - _Cutoff);
            #endif
                SHADOW_CASTER_FRAGMENT(i)
            }
            ENDCG
        }
    }
    FallBack "Legacy Shaders/VertexLit"
}
