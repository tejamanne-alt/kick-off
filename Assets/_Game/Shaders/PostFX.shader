// The camera's finishing pass (see PostFX.cs): a faint bloom on the brightest highlights, then the
// grade of the anime look (docs/ART_DIRECTION.md): a white balance, a toe that sinks the darkest
// tones into deep cool shadow, a little contrast, a shoulder that rolls the highlights off below
// pure white (whites read as paper, not as a blown light), vibrance (quiet colours lifted a touch,
// strong ones left alone), a split tone (cool shadows, faintly mauve mid-greys) and a light
// vignette. Cheap enough for phones: the bloom works on a quarter-size chain of a few textures.
Shader "Hidden/DribbleToSchool/PostFX"
{
    Properties { _MainTex ("Source", 2D) = "white" {} }

    CGINCLUDE
    #include "UnityCG.cginc"
    sampler2D _MainTex;
    float4 _MainTex_TexelSize;
    sampler2D _BloomTex;
    float _Threshold, _Knee, _BloomIntensity, _Saturation, _Vibrance, _Contrast, _Vignette;
    float _ToeEnd, _ToeFloor, _Shoulder, _WhitePoint;
    fixed4 _BloomTint;
    float4 _Balance, _ShadowTint, _MidTint, _HighlightTint;   // full precision: the tints are tiny (lowp would round them away)

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
                const half3 lum = half3(0.299, 0.587, 0.114);
                half3 c = tex2D(_MainTex, i.uv).rgb;
                c += tex2D(_BloomTex, i.uv).rgb * _BloomTint.rgb * _BloomIntensity;
                c = max(c * _Balance.rgb, 0);
                // Toe: tones below _ToeEnd sink toward _ToeFloor of themselves; mid-tones are untouched.
                c *= lerp(_ToeFloor.xxx, half3(1, 1, 1), smoothstep(half3(0, 0, 0), _ToeEnd.xxx, c));
                c = (c - 0.5) * _Contrast + 0.5;
                // Shoulder: above _Shoulder, ease toward _WhitePoint instead of clipping.
                half range = max(_WhitePoint - _Shoulder, 1e-3);
                half3 rolled = _Shoulder + range * (1 - exp(-max(c - _Shoulder, 0) / range));
                c = lerp(c, rolled, step(_Shoulder.xxx, c));
                // Vibrance: greys and soft colours take _Vibrance, strong colours _Saturation.
                half l = dot(c, lum);
                half hi = max(c.r, max(c.g, c.b)), lo = min(c.r, min(c.g, c.b));
                half sat = (hi - lo) / max(hi, 1e-3);
                c = l + (c - l) * lerp(_Vibrance, _Saturation, smoothstep(0, 0.6, sat));
                // Split tone by brightness.
                l = dot(c, lum);
                half shadows = saturate(1 - l * 2); shadows *= shadows;
                half lights = saturate(l * 2 - 1); lights *= lights;
                half mids = saturate(1 - abs(l - 0.45) / 0.3);
                c += shadows * _ShadowTint.rgb + mids * _MidTint.rgb + lights * _HighlightTint.rgb;
                float2 p = i.uv - 0.5;
                c *= 1 - _Vignette * smoothstep(0.25, 0.85, dot(p, p) * 2.2);
                return half4(saturate(c), 1);
            }
            ENDCG
        }
    }
}
