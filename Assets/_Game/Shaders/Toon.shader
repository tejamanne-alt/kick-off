// The painterly surface shader for the 3D street (see docs/ART_DIRECTION.md):
// - a warm sun with a soft light-to-shade transition (a wrapped diffuse ramp, not hard bands);
// - shade sides that carry the sky's colour (hemispheric ambient: sky above, warm ground bounce
//   below), never black;
// - a gentle warm rim where surfaces turn away toward the sun;
// - real-time sun shadows from the scene's directional light, tinted like the shade side;
// - an optional world-space texture projection (so surfaces tile at any size), with soft
//   world-scale patches of lighter, darker, warmer and cooler ground so the repeat doesn't show;
// - distance haze that leans warm toward the sun, so far layers dissolve into a glowing sky;
// - an optional breeze (_Wind) that sways vertices by their alpha (the plants kit's wind weight).
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
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100

        Pass
        {
            Tags { "LightMode"="ForwardBase" }
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fwdbase nolightmap nodirlightmap nodynlightmap novertexlight
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"
            #include "AutoLight.cginc"
            #include "DtsLook.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            fixed4 _ShadowColor;
            float _WorldUV;
            float _WorldUVScale;
            float _Macro;
            float4 _Scroll;
            float _Haze;
            float _Rim;
            float _Wind;

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
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                if (_Wind > 0.0)
                {
                    // A gentle sway in the breeze: the plants kit bakes a wind weight into vertex
                    // alpha (0 at the root, 1 at the tips); gusts roll along the street.
                    float phase = _Time.y * 1.3 + o.worldPos.x * 0.35 + o.worldPos.z * 0.2;
                    float sway = sin(phase) * 0.6 + sin(phase * 2.3 + 1.7) * 0.25;
                    float w = v.color.a * _Wind;
                    o.worldPos.x += sway * w;
                    o.worldPos.z += sin(phase * 0.8 + 0.5) * w * 0.3;
                }
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
                fixed3 albedo = (tex2D(_MainTex, uv) * _Color * i.color).rgb;
                if (_Macro > 0.001) albedo = DtsMacro(albedo, plane, _Macro);
                float shadow = SHADOW_ATTENUATION(i);
                fixed3 col = DtsShade(albedo, n, i.worldPos, _ShadowColor.rgb, shadow, _Rim);
                col = DtsHaze(col, i.worldPos, _Haze);
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    // The fallback supplies the shadow caster pass.
    FallBack "Legacy Shaders/VertexLit"
}
