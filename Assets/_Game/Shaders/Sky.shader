// The sky dome: an inverted sphere centred on the camera, drawn behind everything. A soft
// gradient from a warm, glowing horizon up to the chapter's zenith colour, a wide halo and a
// small soft disc where the sun sits, and a few pale bands of haze low down. Colours come from
// the WorldLook globals, so the sky, the haze and the light always agree.
Shader "DribbleToSchool/Sky"
{
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" }
        Cull Front
        ZWrite Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "DtsLook.cginc"

            fixed4 _DtsSkyZenith;     // rgb: colour high overhead
            fixed4 _DtsSkyHorizon;    // rgb: colour at the horizon
            fixed4 _DtsSunDisc;       // rgb: the sun's disc; a: its size (0..1)

            struct v2f { float4 pos : SV_POSITION; float3 dir : TEXCOORD0; };

            v2f vert (float4 vertex : POSITION)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(vertex);
                o.dir = mul((float3x3)unity_ObjectToWorld, vertex.xyz);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float3 d = normalize(i.dir);
                float3 s = dot(_DtsSkySunDir.xyz, _DtsSkySunDir.xyz) > 0.0001 ? normalize(_DtsSkySunDir.xyz) : float3(0, 0.3, 1);
                float y = d.y;
                // Gradient: the horizon colour holds low down, then gives way to the zenith.
                float h = saturate(y * 1.6 + 0.04);
                fixed3 col = lerp(_DtsSkyHorizon.rgb, _DtsSkyZenith.rgb, pow(h, 0.55));
                // A thin brighter band right at the horizon, and pale haze streaks just above it.
                col = lerp(col, lerp(_DtsSkyHorizon.rgb, fixed3(1, 1, 1), 0.25), saturate(1.0 - abs(y) * 14.0) * 0.5);
                float streak = 0.5 + 0.5 * sin(y * 90.0 + d.x * 3.0);
                col = lerp(col, _DtsSkyHorizon.rgb, saturate(1.0 - y * 9.0) * saturate(y * 40.0) * streak * 0.18);
                // The sun: a wide warm halo, a tighter glow and a soft disc.
                float c = saturate(dot(d, s));
                col += _DtsSunGlow.rgb * (pow(c, 6.0) * 0.45 + pow(c, 48.0) * 0.5);
                float size = lerp(0.9996, 0.9975, saturate(_DtsSunDisc.a));
                col = lerp(col, _DtsSunDisc.rgb, smoothstep(size - 0.0004, size + 0.0002, c));
                // Below the horizon: the haze colour (hidden by the ground, but it keeps edges clean).
                col = lerp(col, _DtsFogColor.rgb, saturate(-y * 12.0));
                return fixed4(col, 1);
            }
            ENDCG
        }
    }
}
