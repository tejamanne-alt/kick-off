// The shared light and atmosphere of the game's shaders (see docs/ART_DIRECTION.md and
// WorldLook, which sets these globals per chapter).
#ifndef DTS_LOOK_INCLUDED
#define DTS_LOOK_INCLUDED

float4 _DtsLightDir;        // xyz: direction toward the sun (the light)
fixed4 _DtsSunColor;        // rgb: sunlight tint; a > 0.5 when set
fixed4 _DtsAmbientSky;      // rgb: colour of shade lit by the sky; a > 0.5 when set
fixed4 _DtsAmbientGround;   // rgb: warm bounce on downward-facing shade
fixed4 _DtsFogColor;        // rgb: haze colour; a: how much haze far away
float4 _DtsFogRange;        // x: haze starts, y: haze is full (distance from the camera)
fixed4 _DtsSunGlow;         // rgb: the glow around the sun in the sky; a: its strength in the haze
float4 _DtsSkySunDir;       // xyz: where the sun shows in the sky, from the camera

float3 DtsLightDir()
{
    float3 l = _DtsLightDir.xyz;
    return dot(l, l) > 0.0001 ? normalize(l) : float3(0, 1, 0);
}

fixed3 DtsSun()
{
    return _DtsSunColor.a > 0.5 ? _DtsSunColor.rgb : fixed3(1, 1, 1);
}

// The colour shade takes on: the material's own shadow tint, pulled toward the sky above and the
// warm ground bounce below.
fixed3 DtsShadeTint(fixed3 shadowTint, float3 n)
{
    if (_DtsAmbientSky.a < 0.5) return shadowTint;
    fixed3 hemi = lerp(_DtsAmbientGround.rgb, _DtsAmbientSky.rgb, saturate(n.y * 0.5 + 0.5));
    return lerp(shadowTint, hemi, 0.75);
}

// Clean anime daylight: a crisp step from cool shade to sun (a narrow soft edge, not a long
// ramp), a gentle falloff across the lit side so forms still read, sun shadows tinted like the
// shade, and a light rim on silhouettes that face away toward the sun.
fixed3 DtsShade(fixed3 albedo, float3 n, float3 worldPos, fixed3 shadowTint, float shadow, float rimAmount)
{
    float3 l = DtsLightDir();
    float wrap = saturate((dot(n, l) + 0.3) / 1.3);
    float lit = smoothstep(0.36, 0.46, wrap) * shadow;
    float full = smoothstep(0.5, 0.86, wrap);
    fixed3 sun = DtsSun();
    fixed3 col = albedo * lerp(DtsShadeTint(shadowTint, n), sun * lerp(0.93, 1.0, full), lit);
    col *= lerp(0.9, 1.04, saturate(n.y * 0.5 + 0.5));
    float3 v = normalize(_WorldSpaceCameraPos - worldPos);
    float rim = pow(1.0 - saturate(dot(n, v)), 3.0) * saturate(0.3 + 0.7 * dot(-v, l)) * rimAmount;
    col += rim * sun * 0.28 * (0.5 + 0.5 * shadow);
    return col;
}

// Cheap value noise for world-scale variation (no texture needed).
float DtsHash(float2 p)
{
    p = frac(p * float2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return frac(p.x * p.y);
}

float DtsValueNoise(float2 p)
{
    float2 i = floor(p), f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = DtsHash(i), b = DtsHash(i + float2(1, 0)), c = DtsHash(i + float2(0, 1)), d = DtsHash(i + float2(1, 1));
    return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}

// Large soft patches of lighter, darker, warmer and cooler ground over a tiling texture, so its
// repeat doesn't show across a long street. w: world position on the surface's plane.
fixed3 DtsMacro(fixed3 albedo, float2 w, float amount)
{
    float m = DtsValueNoise(w * 0.11) * 0.55 + DtsValueNoise(w * 0.031 + 17.3) * 0.45;
    float h = DtsValueNoise(w * 0.05 + 41.7);
    fixed3 tint = lerp(fixed3(1.03, 1.0, 0.95), fixed3(0.97, 1.0, 1.04), h);
    return albedo * lerp(fixed3(1, 1, 1), tint * (1.0 + (m - 0.5) * 0.3), amount);
}

// Distance haze: a little sky blue in the distance, lighter toward the sun's side of the sky.
fixed3 DtsHaze(fixed3 col, float3 worldPos, float amount)
{
    float dist = distance(_WorldSpaceCameraPos, worldPos);
    // Eased out over a long range, so each layer of the distance sits a step deeper in the haze:
    // the street stays clear, a wood 100 m off is softened, hills are half gone, far mountains
    // are pale silhouettes.
    float f = saturate((dist - _DtsFogRange.x) / max(_DtsFogRange.y - _DtsFogRange.x, 0.01));
    f = (1.0 - (1.0 - f) * (1.0 - f)) * _DtsFogColor.a * amount;
    float3 vdir = normalize(worldPos - _WorldSpaceCameraPos);
    float3 sdir = dot(_DtsSkySunDir.xyz, _DtsSkySunDir.xyz) > 0.0001 ? normalize(_DtsSkySunDir.xyz) : float3(0, 0.3, 1);
    float toward = pow(saturate(dot(vdir, sdir)), 5.0) * _DtsSunGlow.a;
    fixed3 fogCol = lerp(_DtsFogColor.rgb, _DtsSunGlow.rgb, saturate(toward));
    return lerp(col, fogCol, f);
}

#endif
