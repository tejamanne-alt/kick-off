# Unity API check: what a newer Unity refuses to compile

`run.sh` checks two things, and exits with an error if either fails:
- every script parses under every combination of the `#if` symbols the scripts use, the tests included;
- no Unity API the scripts use is an error in the given Unity version.

The repository's compile checks run against Unity 2021's reference assemblies, since no Unity 6 references are
published. So an API that a newer Unity has removed compiles "clean" there and only fails in the user's editor.
`Object.GetInstanceID()`, an error from Unity 6.5, put the editor into Safe Mode that way (`docs/LEARNINGS.md` A11).

This check reads the removals from Unity's own C# reference source (github.com/Unity-Technologies/UnityCsReference,
one branch per version) instead:

```
tools/unity_api_check/run.sh 6000.5          # ERROR lines: what Unity 6.5 refuses to compile
tools/unity_api_check/run.sh 6000.7 --all    # the newest 6000 branch, with its deprecation warnings too
```

Run it against the newest Unity 6 branch before pushing, not only the version in `ProjectSettings/ProjectVersion.txt`.
A user can open the project in anything newer.

How it works:
- `Program.cs` (`apiscan`): Roslyn compiles every script under `Assets/` against the 2021 reference assemblies (NuGet
  `Unity3D.SDK`) with `Stubs.cs` standing in for uGUI and the Input System. It does this once per set of `#if` symbols
  the scripts use: editor, iOS and Android players, tests, the optional IAP and screenshot code. It prints every Unity
  type and member each identifier resolves to, with its full signature. With `WARNINGS=1` it prints the compiler's
  warnings instead (CS0675 and the like, which Unity would show).
- `obsolete_check.py`: lists every `[Obsolete]` member of the reference source, finding its type by brace depth and its
  parameter count, and prints the project's uses of the ones that are errors (`true`).
  - Uses of another overload (another parameter count) are left out.
  - A line can still be a different type's member of the same name, so check the signature it prints.
- With `ERRORS=1`, `apiscan` prints the parser's syntax errors (`SYNTAX`) and the compiler's errors (`ERROR`) instead.
  `run.sh` fails on any `SYNTAX` line. A file behind an `#if` that no symbol set defines is never parsed, which is how
  a broken test reached the user (`docs/LEARNINGS.md` A12). The `ERROR` lines include the stand-ins' expected misses, so
  compare them with a clean tree's.
- `run.sh`: fetches the inputs (the reference assemblies, NUnit for the tests, the reference source) into
  `/tmp/unity_api_check` (or `$UNITY_API_CHECK_WORK`), builds `apiscan` and runs all three steps. It needs dotnet 8,
  Python 3, git and curl.

What it can't see:
- APIs that didn't exist in Unity 2021 resolve to nothing. They are newer than the removals so far, but a Unity 7 might
  remove one.
- The uGUI and Input System packages are not in the reference source. Their errors show in the editor's console as
  `Packages/...`.
