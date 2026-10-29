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

// Soft painterly diffuse: a wrapped ramp from shade to sun, sun shadows tinted like the shade,
// a gentle sky fill, and a warm rim on silhouettes that face away toward the sun.
fixed3 DtsShade(fixed3 albedo, float3 n, float3 worldPos, fixed3 shadowTint, float shadow, float rimAmount)
{
    float3 l = DtsLightDir();
    float wrap = saturate((dot(n, l) + 0.3) / 1.3);
    float lit = smoothstep(0.3, 0.56, wrap) * shadow;
    float full = smoothstep(0.62, 0.86, wrap);
    fixed3 sun = DtsSun();
    fixed3 col = albedo * lerp(DtsShadeTint(shadowTint, n), sun * lerp(0.93, 1.0, full), lit);
    col *= lerp(0.9, 1.04, saturate(n.y * 0.5 + 0.5));
    float3 v = normalize(_WorldSpaceCameraPos - worldPos);
    float rim = pow(1.0 - saturate(dot(n, v)), 3.0) * saturate(0.3 + 0.7 * dot(-v, l)) * rimAmount;
    col += rim * sun * 0.28 * (0.5 + 0.5 * shadow);
    return col;
}

// Distance haze, warmer toward the sun's side of the sky.
fixed3 DtsHaze(fixed3 col, float3 worldPos, float amount)
{
    float dist = distance(_WorldSpaceCameraPos, worldPos);
    float f = saturate((dist - _DtsFogRange.x) / max(_DtsFogRange.y - _DtsFogRange.x, 0.01));
    f = f * f * (3.0 - 2.0 * f) * _DtsFogColor.a * amount;
    float3 vdir = normalize(worldPos - _WorldSpaceCameraPos);
    float3 sdir = dot(_DtsSkySunDir.xyz, _DtsSkySunDir.xyz) > 0.0001 ? normalize(_DtsSkySunDir.xyz) : float3(0, 0.3, 1);
    float toward = pow(saturate(dot(vdir, sdir)), 5.0) * _DtsSunGlow.a;
    fixed3 fogCol = lerp(_DtsFogColor.rgb, _DtsSunGlow.rgb, saturate(toward));
    return lerp(col, fogCol, f);
}

#endif
