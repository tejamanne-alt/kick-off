// The painterly surface shader for the 3D street (see docs/ART_DIRECTION.md):
// - a warm sun with a soft light-to-shade transition (a wrapped diffuse ramp, not hard bands);
// - shade sides that carry the sky's colour (hemispheric ambient: sky above, warm ground bounce
//   below), never black;
// - a gentle warm rim where surfaces turn away toward the sun;
// - real-time sun shadows from the scene's directional light, tinted like the shade side;
// - an optional world-space texture projection (so surfaces tile at any size);
// - distance haze that leans warm toward the sun, so far layers dissolve into a glowing sky.
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
        _WorldUVScale ("World texture scale (tiles per unit)", Float) = 0.25
        _Scroll ("Texture scroll (xy per second)", Vector) = (0,0,0,0)
        _Haze ("Distance haze amount", Range(0,1)) = 1
        _Rim ("Rim light", Range(0,1)) = 0.35
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
            #include "UnityCG.cginc"
            #include "AutoLight.cginc"
            #include "DtsLook.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            fixed4 _ShadowColor;
            float _WorldUV;
            float _WorldUVScale;
            float4 _Scroll;
            float _Haze;
            float _Rim;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
                fixed4 color : COLOR;
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
                float2 uv = i.uv;
                if (_WorldUV > 0.5)
                {
                    // Project along the dominant axis: tops use xz, fronts xy, sides zy.
                    float3 a = abs(n);
                    uv = (a.y >= a.x && a.y >= a.z) ? i.worldPos.xz : ((a.x >= a.z) ? i.worldPos.zy : i.worldPos.xy);
                    uv = uv * _WorldUVScale;
                }
                uv += _Scroll.xy * _Time.y;
                fixed3 albedo = (tex2D(_MainTex, uv) * _Color * i.color).rgb;
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
