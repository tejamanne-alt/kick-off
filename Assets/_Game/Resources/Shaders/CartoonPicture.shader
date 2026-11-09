// The classic cartoon filter on the menus' pictures (UI/CartoonPicture: the player cards, the bags, the stickers, the
// logo, the town map), so they match the street drawn by the camera's pass (Shaders/PostFX 7 to 9) and share its colour
// (Shaders/DtsCartoon.cginc). A cel (_Painted 0: a kid, a bag, a sticker, the logo): the cored smoothing, saturated flat
// tones, a warm-black line where the colours meet, and an outline drawn outside the picture's shape (so nothing of it is
// covered). Painted (_Painted 1: the town map): the scenery's warm, painted colour with darker strokes of its own colour.
// A UI shader like UI/Default (stencil masks, rect clipping, alpha clip). In Resources so a build includes it.
Shader "Hidden/DribbleToSchool/CartoonPicture"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite Texture", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _Painted ("Painted like the scenery (1) or a cel (0)", Float) = 0
        _OutlineTexels ("Outline outside the shape (texels)", Float) = 3

        _StencilComp ("Stencil Comparison", Float) = 8
        _Stencil ("Stencil ID", Float) = 0
        _StencilOp ("Stencil Operation", Float) = 0
        _StencilWriteMask ("Stencil Write Mask", Float) = 255
        _StencilReadMask ("Stencil Read Mask", Float) = 255
        _ColorMask ("Color Mask", Float) = 15
        [Toggle(UNITY_UI_ALPHACLIP)] _UseUIAlphaClip ("Use Alpha Clip", Float) = 0
    }

    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }

        Stencil
        {
            Ref [_Stencil]
            Comp [_StencilComp]
            Pass [_StencilOp]
            ReadMask [_StencilReadMask]
            WriteMask [_StencilWriteMask]
        }

        Cull Off
        Lighting Off
        ZWrite Off
        ZTest [unity_GUIZTestMode]
        Blend SrcAlpha OneMinusSrcAlpha
        ColorMask [_ColorMask]

        Pass
        {
            Name "Default"
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "UnityCG.cginc"
            #include "UnityUI.cginc"
            #include "../../Shaders/DtsCartoon.cginc"
            #pragma multi_compile_local _ UNITY_UI_CLIP_RECT
            #pragma multi_compile_local _ UNITY_UI_ALPHACLIP

            struct appdata_t
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
                float2 texcoord : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
                fixed4 color : COLOR;
                float2 texcoord : TEXCOORD0;
                float4 worldPosition : TEXCOORD1;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _MainTex_TexelSize;
            fixed4 _Color;
            fixed4 _TextureSampleAdd;
            float4 _ClipRect;
            float _Painted, _OutlineTexels;

            v2f vert (appdata_t v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.worldPosition = v.vertex;
                o.vertex = UnityObjectToClipPos(o.worldPosition);
                o.texcoord = TRANSFORM_TEX(v.texcoord, _MainTex);
                o.color = v.color * _Color;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                float2 texel = _MainTex_TexelSize.xy;
                half4 s = tex2D(_MainTex, i.texcoord) + _TextureSampleAdd;
                s.rgb = CartoonToDisplay(s.rgb);           // the look is matched on display values
                half painted = step(0.5, _Painted);

                // The cored smoothing (the cels' calmest side wins harder), after a light sharpen.
                float3 m0, m1, m2, m3, cross;
                float v0, v1, v2, v3;
                // The smoothing's step follows the picture's size (half a texel on a 512 px card or sticker, a texel on the
                // town map), so a picture of any size is smoothed as much on screen.
                float step1 = painted > 0.5 ? 1.0 : clamp(max(_MainTex_TexelSize.z, _MainTex_TexelSize.w) / 1024.0, 0.5, 1.5);
                CARTOON_SECTORS(_MainTex, i.texcoord, texel * step1, m0, m1, m2, m3, v0, v1, v2, v3, cross)
                half3 flat = CartoonToDisplay(CartoonBlend(m0, m1, m2, m3, v0, v1, v2, v3, lerp(6, 4, painted)));
                half3 c = saturate(s.rgb + (s.rgb - CartoonToDisplay(cross)) * _Sharpen * 0.8);
                half3 p = CartoonCore(c, flat, lerp(_CelCoreFrom, _CoreFrom, painted), lerp(_CelCoreTo, _CoreTo, painted));

                // Where the colours meet: a warm-black line on a cel, a darker stroke of its own colour when painted.
                float2 o1 = texel;
                half3 cR = CartoonToDisplay(tex2D(_MainTex, i.texcoord + float2(o1.x, 0)).rgb), cL = CartoonToDisplay(tex2D(_MainTex, i.texcoord - float2(o1.x, 0)).rgb);
                half3 cU = CartoonToDisplay(tex2D(_MainTex, i.texcoord + float2(0, o1.y)).rgb), cD = CartoonToDisplay(tex2D(_MainTex, i.texcoord - float2(0, o1.y)).rgb);
                half3 cRU = CartoonToDisplay(tex2D(_MainTex, i.texcoord + o1).rgb), cLD = CartoonToDisplay(tex2D(_MainTex, i.texcoord - o1).rgb);
                half3 cRD = CartoonToDisplay(tex2D(_MainTex, i.texcoord + float2(o1.x, -o1.y)).rgb), cLU = CartoonToDisplay(tex2D(_MainTex, i.texcoord + float2(-o1.x, o1.y)).rgb);
                half stepAcross = max(max(CartoonStepAcross(cR, cL), CartoonStepAcross(cU, cD)), max(CartoonStepAcross(cRU, cLD), CartoonStepAcross(cRD, cLU)));

                half3 col;
                if (painted > 0.5)
                {
                    col = CartoonPainted(p, 0.5);
                    half stroke = smoothstep(_StrokeEdge, _StrokeEdge * 1.8, stepAcross);
                    col = lerp(col, col * _StrokeDark, stroke * _StrokeStrength);
                }
                else
                {
                    col = CartoonCel(p);
                    half inkLine = smoothstep(0.3, 0.54, stepAcross);   // (`line` is reserved in HLSL)
                    col = lerp(col, _CelInk.rgb, inkLine * 0.85);
                }

                // A cel's outline, outside its shape only (the shape's alpha read round it, bilinear: anti-aliased).
                half a = s.a;
                if (painted < 0.5 && _OutlineTexels > 0)
                {
                    float2 r = texel * (_OutlineTexels + 0.5);
                    half nearA = max(max(tex2D(_MainTex, i.texcoord + float2(r.x, 0)).a, tex2D(_MainTex, i.texcoord - float2(r.x, 0)).a),
                                     max(tex2D(_MainTex, i.texcoord + float2(0, r.y)).a, tex2D(_MainTex, i.texcoord - float2(0, r.y)).a));
                    float2 rd = r * 0.7071;
                    nearA = max(nearA, max(max(tex2D(_MainTex, i.texcoord + rd).a, tex2D(_MainTex, i.texcoord - rd).a),
                                           max(tex2D(_MainTex, i.texcoord + float2(rd.x, -rd.y)).a, tex2D(_MainTex, i.texcoord + float2(-rd.x, rd.y)).a)));
                    half edge = saturate((nearA - a) * 1.5);
                    col = lerp(col, _CelInk.rgb, edge);
                    a = max(a, edge);
                }

                half4 colour = half4(CartoonFromDisplay(col), a) * i.color;
                #ifdef UNITY_UI_CLIP_RECT
                colour.a *= UnityGet2DClipping(i.worldPosition.xy, _ClipRect);
                #endif
                #ifdef UNITY_UI_ALPHACLIP
                clip(colour.a - 0.001);
                #endif
                return colour;
            }
            ENDCG
        }
    }
}
