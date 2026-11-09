// The classic cartoon filter's colour (Settings, Add-ons & Filters): shared by the camera's pass (Shaders/PostFX,
// passes 7 to 9) and the menus' pictures (Resources/Shaders/CartoonPicture), so the street and the UI's player cards,
// bags, stickers, logo and town map look the same. The values are set from World/ClassicLook.cs. Colours here are
// display (gamma) values: the look was matched on screen values (review/cartoon/classic_port.py is the reference).
//
// Two treatments, as an animation cel over a painted background:
//   the cels (the people, the ball, and the things the kid plays with) - flat colour in a few soft-edged tones,
//     saturated, outlined in a warm black by the caller;
//   the painted scenery - warm colours pushed to orange and gold (blues and greens keep their hue), quiet colours
//     lifted, rich warm shadows (never grey), in broad soft tones; the caller adds the darker strokes between forms.
// Both start from an edge-keeping smoothing (a soft four-sector Kuwahara) that is "cored": of what it takes away, weak
// texture (stains, noise) stays away and anything with real contrast (a window frame, a letter, a spoke) comes back
// exactly as drawn, so the detail stays crisp.
#ifndef DTS_CARTOON_INCLUDED
#define DTS_CARTOON_INCLUDED

float _CoreFrom, _CoreTo, _CelCoreFrom, _CelCoreTo, _Sharpen;
float _CelSat, _CelBands, _CelBandSoft, _CelBandMix;
float _BgSat, _BgVibrance, _BgBands, _BgBandSoft, _BgBandMix, _ShadowReach;
float4 _Warm, _ShadowWarm, _CelInk;
float _StrokeEdge, _StrokeDark, _StrokeStrength;   // darker strokes of the scenery's own colour where its colours meet

static const half3 cartoonLum = half3(0.299, 0.587, 0.114);

// Brightness snapped to n steps with soft edges (soft: the ramp's width as a fraction of a step).
half CartoonStep(half l, half n, half soft)
{
    half x = l * n;
    half f = floor(x);
    return (f + smoothstep(0.5 - soft, 0.5 + soft, x - f)) / n;
}

// The colour in flat tones, its hue kept; brightness above `top` stays smooth (whites stay white).
half3 CartoonTones(half3 c, half n, half soft, half mixAmount, half top)
{
    half l = dot(c, cartoonLum);
    half m = mixAmount * (1 - smoothstep(top - 0.06, top + 0.04, l));
    half t = lerp(l, CartoonStep(l, n, soft), m);
    return saturate(c * (t / max(l, 1e-3)));
}

half3 CartoonSaturate(half3 c, half s)
{
    half l = dot(c, cartoonLum);
    return saturate(l + (c - l) * s);
}

// Reds, oranges, yellows and beiges (red leads both green and blue): the colours a desert palette warms.
half CartoonWarmMask(half3 c)
{
    return smoothstep(-0.02, 0.08, c.r - max(c.b, c.g * 0.92));
}

// Quiet colours lifted far more than strong ones (a cartoon background has no greys): sand goes golden, beige goes
// ochre; true greys and whites stay as they are, and greens are lifted less (olive, not lime).
half3 CartoonVibrance(half3 c, half v)
{
    half l = dot(c, cartoonLum);
    half hi = max(c.r, max(c.g, c.b)), lo = min(c.r, min(c.g, c.b));
    half sat = (hi - lo) / max(hi, 1e-3);
    half green = smoothstep(0, 0.08, c.g - max(c.r, c.b));
    half f = 1 + v * (1 - sat) * (1 - sat) * smoothstep(0.03, 0.12, sat) * (1 - 0.7 * green);
    return saturate(l + (c - l) * f);
}

// The painted scenery's colour. vibranceScale: 1 for the street, less for a picture already rich in colour.
half3 CartoonPainted(half3 c, half vibranceScale)
{
    c = saturate(c * (1 + (_Warm.rgb - 1) * CartoonWarmMask(c)));
    c = CartoonVibrance(c, _BgVibrance * vibranceScale);
    c = CartoonSaturate(c, _BgSat);
    half l = dot(c, cartoonLum);
    half dark = 1 - smoothstep(_ShadowReach - 0.2, _ShadowReach, l);
    c = saturate(c * (1 + (_ShadowWarm.rgb - 1) * dark));
    c = CartoonSaturate(c, 1 + 0.25 * dark);             // shadows richer, not greyer
    return CartoonTones(c, _BgBands, _BgBandSoft, _BgBandMix, 0.9);
}

// A cel's colour: saturated, in a few flat tones.
half3 CartoonCel(half3 c)
{
    return CartoonTones(CartoonSaturate(c, _CelSat), _CelBands, _CelBandSoft, _CelBandMix, 0.86);
}

// Coring: of what the smoothing took away (c - flat), the weak part stays away and the strong part comes back.
half3 CartoonCore(half3 c, half3 flat, half from, half to)
{
    half3 d = c - flat;
    return flat + d * smoothstep(from, to, max(abs(d.r), max(abs(d.g), abs(d.b))));
}

// The largest step in brightness or colour between two neighbours on opposite sides of a pixel.
half CartoonStepAcross(half3 a, half3 b)
{
    half3 d = a - b;
    return max(abs(dot(d, cartoonLum)), 0.7 * length(d));
}

// The soft four-sector Kuwahara, in two parts. CARTOON_SECTORS reads the 5 x 5 pixels round UV (`T` apart: 25 reads)
// into the means (M0..M3) and brightness variances (V0..V3) of four 3x3 sectors touching the pixel, and the mean of
// its four nearest neighbours (CROSS, for a sharpen). CartoonBlend then lets the calmest sector win, by
// ((1 + 400 Vmin) / (1 + 400 V))^q: the calmest weighs 1, so the blend never divides by a vanishing sum.
#define CARTOON_SECTORS(TEX, UV, T, M0, M1, M2, M3, V0, V1, V2, V3, CROSS)                                      \
{                                                                                                               \
    float3 a0 = 0, a1 = 0, a2 = 0, a3 = 0;                                                                      \
    float s0 = 0, s1 = 0, s2 = 0, s3 = 0, q0 = 0, q1 = 0, q2 = 0, q3 = 0;                                       \
    CROSS = 0;                                                                                                  \
    [unroll] for (int ky = -2; ky <= 2; ky++)                                                                   \
    [unroll] for (int kx = -2; kx <= 2; kx++)                                                                   \
    {                                                                                                           \
        float3 kc = tex2D(TEX, UV + float2(kx, ky) * T).rgb;                                                    \
        float kl = dot(kc, cartoonLum);                                                                         \
        if (kx <= 0 && ky <= 0) { a0 += kc; s0 += kl; q0 += kl * kl; }                                          \
        if (kx >= 0 && ky <= 0) { a1 += kc; s1 += kl; q1 += kl * kl; }                                          \
        if (kx <= 0 && ky >= 0) { a2 += kc; s2 += kl; q2 += kl * kl; }                                          \
        if (kx >= 0 && ky >= 0) { a3 += kc; s3 += kl; q3 += kl * kl; }                                          \
        if (abs(kx) + abs(ky) == 1) CROSS += kc * 0.25;                                                         \
    }                                                                                                           \
    M0 = a0 / 9; M1 = a1 / 9; M2 = a2 / 9; M3 = a3 / 9;                                                         \
    V0 = max(q0 / 9 - (s0 / 9) * (s0 / 9), 0); V1 = max(q1 / 9 - (s1 / 9) * (s1 / 9), 0);                      \
    V2 = max(q2 / 9 - (s2 / 9) * (s2 / 9), 0); V3 = max(q3 / 9 - (s3 / 9) * (s3 / 9), 0);                      \
}

float3 CartoonBlend(float3 m0, float3 m1, float3 m2, float3 m3, float v0, float v1, float v2, float v3, float q)
{
    float lo = 1 + 400 * min(min(v0, v1), min(v2, v3));
    float w0 = pow(lo / (1 + 400 * v0), q), w1 = pow(lo / (1 + 400 * v1), q);
    float w2 = pow(lo / (1 + 400 * v2), q), w3 = pow(lo / (1 + 400 * v3), q);
    return (m0 * w0 + m1 * w1 + m2 * w2 + m3 * w3) / (w0 + w1 + w2 + w3);
}

half3 CartoonToDisplay(half3 c)
{
#if defined(UNITY_COLORSPACE_GAMMA)
    return c;
#else
    return LinearToGammaSpace(c);
#endif
}

half3 CartoonFromDisplay(half3 c)
{
#if defined(UNITY_COLORSPACE_GAMMA)
    return c;
#else
    return GammaToLinearSpace(c);
#endif
}

#endif
