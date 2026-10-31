// Anime-style shading for characters, the ball and other smooth, rounded things, drawn to
// stand apart from the painterly street: two flat cel bands (lit and a cool shadow) from the
// global sun, a bright rim round the whole silhouette (strongest on the sunny side), a dark ink
// outline of constant on-screen width (an inverted hull pushed out along the smooth normals),
// and the same distance haze as the street. Colours come from the vertex colours times the
// texture and tint. Lighting and haze are set by WorldLook.
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
                o.pos = UnityObjectToClipPos(v.vertex);
                float3 worldNormal = UnityObjectToWorldNormal(v.normal);
                float2 clipNormal = mul((float3x3)UNITY_MATRIX_VP, worldNormal).xy;
                float len = length(clipNormal);
                if (len > 0.0001)
                {
                    clipNormal /= len;
                    clipNormal.x *= _ScreenParams.y / _ScreenParams.x;
                    o.pos.xy += clipNormal * _OutlineWidth * 2.0 * o.pos.w;
                }
                o.color = v.color;
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed3 col = lerp(_OutlineColor.rgb, i.color.rgb * _Color.rgb * 0.3, 0.2);
                col = DtsHaze(col, i.worldPos, 1.0);
                return fixed4(col, 1);
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
                fixed4 tex = tex2D(_MainTex, i.uv) * _Color * i.color;
                float3 l = DtsLightDir();
                float d = dot(n, l);
                // Two cel bands with a narrow soft edge (the anime look), the shade tinted by the
                // sky and the warm bounce like the street around it; sun shadows fall into the shade.
                float lit = smoothstep(-0.02, 0.06, d) * lerp(0.15, 1.0, SHADOW_ATTENUATION(i));
                fixed3 col = lerp(tex.rgb * DtsShadeTint(_ShadowColor.rgb, n), tex.rgb * DtsSun(), lit);

                // A rim of light round the silhouette, brightest on the sunny side, so the figure
                // lifts off whatever is behind it.
                float3 v = normalize(_WorldSpaceCameraPos - i.worldPos);
                float rim = smoothstep(0.6, 0.76, 1.0 - saturate(dot(n, v))) * lerp(0.4, 1.0, saturate(d + 0.35));
                col += rim * _RimStrength * DtsSun();

                col = DtsHaze(col, i.worldPos, 1.0);
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    // The fallback supplies the shadow caster pass.
    FallBack "Legacy Shaders/VertexLit"
}
