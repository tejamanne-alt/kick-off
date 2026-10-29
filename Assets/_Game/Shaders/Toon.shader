// Cel-shaded opaque surface for the 3D street: flat colour bands from a fixed sun
// direction, an optional world-space texture projection (so surfaces tile at any size)
// and distance haze toward the sky colour. Lighting and haze come from globals set
// by WorldLook, so no scene lights are needed.
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
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        LOD 100

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float4 _MainTex_ST;
            fixed4 _Color;
            fixed4 _ShadowColor;
            float _WorldUV;
            float _WorldUVScale;
            float4 _Scroll;
            float _Haze;

            float4 _DtsLightDir;     // xyz: direction toward the sun
            fixed4 _DtsFogColor;     // rgb: haze colour, a: max haze
            float4 _DtsFogRange;     // x: start distance, y: full distance

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
                float2 uv = i.uv;
                if (_WorldUV > 0.5)
                {
                    // Project along the dominant axis: tops use xz, fronts xy, sides zy.
                    float3 a = abs(n);
                    uv = (a.y >= a.x && a.y >= a.z) ? i.worldPos.xz : ((a.x >= a.z) ? i.worldPos.zy : i.worldPos.xy);
                    uv = uv * _WorldUVScale;
                }
                uv += _Scroll.xy * _Time.y;
                fixed4 tex = tex2D(_MainTex, uv) * _Color * i.color;

                float3 l = _DtsLightDir.xyz;
                l = dot(l, l) > 0.0001 ? normalize(l) : float3(0, 1, 0);
                float d = dot(n, l);
                fixed3 col = d > 0.55 ? tex.rgb : (d > 0.12 ? tex.rgb * 0.92 : tex.rgb * _ShadowColor.rgb);

                float dist = distance(_WorldSpaceCameraPos, i.worldPos);
                float f = saturate((dist - _DtsFogRange.x) / max(_DtsFogRange.y - _DtsFogRange.x, 0.01)) * _DtsFogColor.a * _Haze;
                col = lerp(col, _DtsFogColor.rgb, f);
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    FallBack "Unlit/Texture"
}
