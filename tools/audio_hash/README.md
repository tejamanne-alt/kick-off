# Audio hash: is the synthesized sound still the same, sample for sample?

The game makes all its music, ambience and sound effects in code (`Assets/_Game/Scripts/Audio/`). Those generators are
pure C#, so this compiles them unchanged outside Unity and prints a hash of every clip they make: each place's music in
each country, each place's bed and cues (with their timings and levels), and every sound effect. 102 clips in all.

```
dotnet run -c Release --project tools/audio_hash > /tmp/now.txt && diff tools/audio_hash/expected.txt /tmp/now.txt
dotnet run -c Release --project tools/audio_hash -- alloc     # what each generation allocates, and how long it takes
```

- **A change meant to keep the sound** (an optimisation, a refactor) must leave the output identical to `expected.txt`.
  The November 2026 buffer reuse was checked this way (`docs/LEARNINGS.md` B8).
- **A change meant to alter the sound** changes some lines: check that only the clips you meant to change did, listen to
  them, then write the new `expected.txt` in the same commit.

The hashes come from .NET 8 on the desktop. A phone running the IL2CPP build can differ in the last bit of a maths
function (`Math.Sin`, `Exp`, `Tanh`, `Pow`), about 1e-7, far below what 16-bit audio can hold. So this is a check of the
code, not of a device. It needs dotnet 8.
