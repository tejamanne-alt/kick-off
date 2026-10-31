// The sky dome: an inverted sphere centred on the camera, drawn behind everything. A clear
// anime sky: pale blue at the horizon deepening quickly to the chapter's rich zenith blue, a
// faint bright band right at the horizon, and a soft glow and disc where the sun sits (high, so
// usually only the glow shows). Colours come from the WorldLook globals, so the sky, the haze and
// the light always agree.
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
                // Gradient: pale just above the horizon, deepening quickly to the zenith blue, so
                // most of the sky in view is a rich blue.
                float h = saturate(y * 2.2 + 0.03);
                fixed3 col = lerp(_DtsSkyHorizon.rgb, _DtsSkyZenith.rgb, pow(h, 0.5));
                // A thin brighter band right at the horizon.
                col = lerp(col, lerp(_DtsSkyHorizon.rgb, fixed3(1, 1, 1), 0.35), saturate(1.0 - abs(y) * 16.0) * 0.45);
                // The sun: a soft glow and a tighter one round a small disc.
                float c = saturate(dot(d, s));
                col += _DtsSunGlow.rgb * (pow(c, 8.0) * 0.18 + pow(c, 64.0) * 0.4);
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
