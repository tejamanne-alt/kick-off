// Anime-style shading for characters, the ball and other smooth, rounded things:
// two cel bands (lit and a cool shadow) from the global sun, a thin rim light, an
// ink outline of constant on-screen width (an inverted hull pushed out along the
// smooth normals), and the same distance haze as the street. Colours come from the
// vertex colours times the texture and tint. Lighting and haze are set by WorldLook.
Shader "DribbleToSchool/ToonCharacter"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _ShadowColor ("Shadow tint", Color) = (0.74,0.72,0.9,1)
        _RimStrength ("Rim light", Range(0,1)) = 0.22
        _OutlineColor ("Outline colour", Color) = (0.13,0.1,0.14,1)
        _OutlineWidth ("Outline width (fraction of screen height)", Float) = 0.0022
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100

        CGINCLUDE
        #include "UnityCG.cginc"

        sampler2D _MainTex;
        float4 _MainTex_ST;
        fixed4 _Color;
        fixed4 _ShadowColor;
        float _RimStrength;
        fixed4 _OutlineColor;
        float _OutlineWidth;

        float4 _DtsLightDir;
        fixed4 _DtsFogColor;
        float4 _DtsFogRange;

        float HazeAmount(float3 worldPos)
        {
            float dist = distance(_WorldSpaceCameraPos, worldPos);
            return saturate((dist - _DtsFogRange.x) / max(_DtsFogRange.y - _DtsFogRange.x, 0.01)) * _DtsFogColor.a;
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
                fixed3 col = lerp(_OutlineColor.rgb, i.color.rgb * _Color.rgb * 0.32, 0.35);
                col = lerp(col, _DtsFogColor.rgb, HazeAmount(i.worldPos));
                return fixed4(col, 1);
            }
            ENDCG
        }

        Pass
        {
            Name "Toon"
            Cull Back
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; float2 uv : TEXCOORD0; fixed4 color : COLOR; };
            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
                fixed4 color : COLOR;
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float3 n = normalize(i.normal);
                fixed4 tex = tex2D(_MainTex, i.uv) * _Color * i.color;

                float3 l = _DtsLightDir.xyz;
                l = dot(l, l) > 0.0001 ? normalize(l) : float3(0, 1, 0);
                float d = dot(n, l);
                // Two bands with a narrow soft edge (anime cel shading).
                float lit = smoothstep(-0.02, 0.06, d);
                fixed3 col = lerp(tex.rgb * _ShadowColor.rgb, tex.rgb, lit);

                // Rim light on the sunny side's silhouette.
                float3 v = normalize(_WorldSpaceCameraPos - i.worldPos);
                float rim = smoothstep(0.62, 0.78, 1.0 - saturate(dot(n, v))) * saturate(d + 0.35);
                col += rim * _RimStrength;

                col = lerp(col, _DtsFogColor.rgb, HazeAmount(i.worldPos));
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    FallBack "Unlit/Texture"
}
