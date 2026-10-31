// The camera's finishing pass (see PostFX.cs): a faint bloom on the brightest highlights, then a
// clean grade (a touch of cool in the shadows, a little extra contrast) and a light vignette. Cheap enough for phones: the bloom works on a
// quarter-size chain of a few textures.
Shader "Hidden/DribbleToSchool/PostFX"
{
    Properties { _MainTex ("Source", 2D) = "white" {} }

    CGINCLUDE
    #include "UnityCG.cginc"
    sampler2D _MainTex;
    float4 _MainTex_TexelSize;
    sampler2D _BloomTex;
    float _Threshold, _Knee, _BloomIntensity, _Saturation, _Contrast, _Vignette;
    fixed4 _BloomTint, _Lift, _Gain;

    struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };
    v2f vert (appdata_img v) { v2f o; o.pos = UnityObjectToClipPos(v.vertex); o.uv = v.texcoord; return o; }

    half3 Box4(float2 uv, float d)
    {
        float4 o = _MainTex_TexelSize.xyxy * float4(-d, -d, d, d);
        return (tex2D(_MainTex, uv + o.xy).rgb + tex2D(_MainTex, uv + o.zy).rgb + tex2D(_MainTex, uv + o.xw).rgb + tex2D(_MainTex, uv + o.zw).rgb) * 0.25;
    }
    ENDCG

    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        // 0: bright-pass and downsample
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target
            {
                half3 c = Box4(i.uv, 1.0);
                half br = max(c.r, max(c.g, c.b));
                half soft = clamp(br - _Threshold + _Knee, 0, 2 * _Knee);
                soft = soft * soft / (4 * _Knee + 1e-4);
                half w = max(soft, br - _Threshold) / max(br, 1e-4);
                return half4(c * w, 1);
            }
            ENDCG
        }
        // 1: downsample
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target { return half4(Box4(i.uv, 1.0), 1); }
            ENDCG
        }
        // 2: upsample, added onto the bigger level
        Pass
        {
            Blend One One
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target { return half4(Box4(i.uv, 0.5), 1); }
            ENDCG
        }
        // 3: final: bloom, grade, vignette
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            half4 frag (v2f i) : SV_Target
            {
                half3 c = tex2D(_MainTex, i.uv).rgb;
                c += tex2D(_BloomTex, i.uv).rgb * _BloomTint.rgb * _BloomIntensity;
                // Lift (shadows) and gain (highlights), then contrast round mid-grey and saturation.
                c = c * _Gain.rgb + _Lift.rgb * (1 - c);
                c = (c - 0.5) * _Contrast + 0.5;
                half l = dot(c, half3(0.299, 0.587, 0.114));
                c = lerp(l.xxx, c, _Saturation);
                float2 p = i.uv - 0.5;
                c *= 1 - _Vignette * smoothstep(0.25, 0.85, dot(p, p) * 2.2);
                return half4(saturate(c), 1);
            }
            ENDCG
        }
    }
}
