// Moving water for the sea, tidal channels, streams and flooded trenches (see docs/ART_DIRECTION.md):
// - two layers of the painted water texture drifting across each other, so the surface never
//   holds still;
// - soft swells rolling in toward the shore (lighter crests, darker troughs), bent by a little
//   noise so they don't read as stripes;
// - glints of sun that come and go;
// - the shared light, shade and distance haze of the street (DtsLook.cginc), and the sun's shadows.
// It works on any flat surface, a single quad included: all the motion is in the shading.
Shader "DribbleToSchool/Water"
{
    Properties
    {
        _MainTex ("Water texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _ShadowColor ("Shadow tint", Color) = (0.72,0.76,0.9,1)
        _WorldUVScale ("World texture scale (tiles per unit)", Float) = 0.125
        _Scroll ("Drift (UV per second)", Vector) = (0.01,0.005,0,0)
        _SwellDir ("Swell travel direction (xz)", Vector) = (0,-1,0,0)
        _SwellLength ("Swell spacing (units)", Float) = 6
        _SwellSpeed ("Swell speed (radians per second)", Float) = 1.1
        _Swell ("Swell strength", Range(0,1)) = 0.8
        _Sparkle ("Glints", Range(0,1)) = 0.6
        _Haze ("Distance haze amount", Range(0,1)) = 1
        _Rim ("Rim light", Range(0,1)) = 0.1
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
            fixed4 _Color;
            fixed4 _ShadowColor;
            float _WorldUVScale;
            float4 _Scroll;
            float4 _SwellDir;
            float _SwellLength;
            float _SwellSpeed;
            float _Swell;
            float _Sparkle;
            float _Haze;
            float _Rim;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                fixed4 color : COLOR;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 normal : TEXCOORD0;
                float3 worldPos : TEXCOORD1;
                fixed4 color : COLOR;
                SHADOW_COORDS(2)
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.color = v.color;
                TRANSFER_SHADOW(o);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float t = _Time.y;
                float2 w = i.worldPos.xz;
                // Two layers of the water texture, drifting different ways at different scales.
                float2 uv1 = w * _WorldUVScale + _Scroll.xy * t;
                float2 uv2 = float2(w.x * 0.82 + w.y * 0.31, -w.x * 0.27 + w.y * 0.9) * (_WorldUVScale * 1.37) - _Scroll.yx * (t * 1.3) + 0.37;
                fixed3 albedo = (tex2D(_MainTex, uv1).rgb + tex2D(_MainTex, uv2).rgb) * 0.5;
                albedo *= _Color.rgb * i.color.rgb;

                // Swells rolling in: lighter on the crests, a little darker in the troughs.
                float2 dir = normalize(_SwellDir.xy + float2(0.0001, 0));
                float phase = dot(w, dir) / max(_SwellLength, 0.1) * 6.2832 - t * _SwellSpeed;
                phase += DtsValueNoise(w * 0.06) * 3.0;
                float s = sin(phase);
                albedo *= 1.0 + _Swell * (smoothstep(0.55, 1.0, s) * 0.2 - smoothstep(-0.3, -1.0, s) * 0.09);

                // Glints of sun, coming and going.
                float g = DtsValueNoise(w * 2.7 + t * float2(0.6, -0.35)) * DtsValueNoise(w * 1.9 - t * float2(0.25, 0.45));
                albedo += _Sparkle * smoothstep(0.42, 0.62, g) * _DtsSunColor.rgb * 0.45;

                float3 n = normalize(i.normal);
                float shadow = SHADOW_ATTENUATION(i);
                fixed3 col = DtsShade(albedo, n, i.worldPos, _ShadowColor.rgb, shadow, _Rim);
                col = DtsHaze(col, i.worldPos, _Haze);
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
    FallBack "Legacy Shaders/VertexLit"
}
