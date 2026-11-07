// The comic filter's sound-effect lettering (UI/ComicPops, UI/ComicLettering): the font's coverage
// times the vertex colour (ComicLettering paints the ink stroke, the drop shadow and the fill's
// yellow-to-orange gradient into the vertices), with a halftone dot screen printed over the lower
// part of the fill. uv1.x is how much of the dot screen a vertex takes, uv1.y is 1 on the fill and
// 0 on the ink. The dots are in screen pixels (8 at 1080 lines), on a 45-degree screen like the
// filter's own. In Resources so a build includes it (it is loaded by name).
Shader "Hidden/DribbleToSchool/ComicLettering"
{
    Properties
    {
        [PerRendererData] _MainTex ("Font Texture", 2D) = "white" {}
        _DotColor ("Dot colour", Color) = (0.84, 0.16, 0.12, 1)
        _DotPeriod ("Dot period (px at 1080 lines)", Float) = 8
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }
        Cull Off Lighting Off ZWrite Off
        ZTest [unity_GUIZTestMode]
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            fixed4 _TextureSampleAdd;
            fixed4 _DotColor;
            float _DotPeriod;

            struct appdata { float4 vertex : POSITION; float4 color : COLOR; float2 uv : TEXCOORD0; float2 uv1 : TEXCOORD1; };
            struct v2f { float4 pos : SV_POSITION; fixed4 color : COLOR; float2 uv : TEXCOORD0; float2 dots : TEXCOORD1; float4 screen : TEXCOORD2; };

            v2f vert (appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.color = v.color;
                o.uv = v.uv;
                o.dots = v.uv1;
                o.screen = ComputeScreenPos(o.pos);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 c = i.color;
                c.a *= (tex2D(_MainTex, i.uv) + _TextureSampleAdd).a;
                float period = max(3.0, _DotPeriod * _ScreenParams.y / 1080.0);
                float2 px = i.screen.xy / max(i.screen.w, 1e-5) * _ScreenParams.xy;
                float2 r = float2(px.x + px.y, px.x - px.y) / (period * 1.41421356);
                float d = length(r - floor(r + 0.5));
                float cover = saturate(i.dots.x);
                float m = saturate((sqrt(cover) * 0.6 - d) * period * 0.8 + 0.5) * step(0.02, cover) * i.dots.y;
                c.rgb = lerp(c.rgb, _DotColor.rgb, m);
                return c;
            }
            ENDCG
        }
    }
}
