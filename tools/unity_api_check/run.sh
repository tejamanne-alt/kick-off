#!/bin/bash
# Checks that every script parses in every #if combination (the tests included), and every Unity API the game's scripts
# use against a Unity version's [Obsolete] list, before opening the project in that version (docs/LEARNINGS.md A11, A12). Needs dotnet 8, python 3 and git; downloads Unity's 2021 reference assemblies
# (NuGet unity3d.sdk) to resolve the calls, and the version's C# reference source to read what it removed.
#   tools/unity_api_check/run.sh 6000.5          # ERROR lines: what that Unity refuses to compile
#   tools/unity_api_check/run.sh 6000.5 --all    # and its deprecation warnings
set -e
VERSION=${1:?a Unity version branch, e.g. 6000.5}; shift || true
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
WORK=${UNITY_API_CHECK_WORK:-/tmp/unity_api_check}; mkdir -p "$WORK"
NUGET=https://api.nuget.org/v3-flatcontainer
if [ ! -f "$WORK/sdk/lib/UnityEngine.dll" ]; then
  curl -sL $NUGET/unity3d.sdk/2021.1.14.1/unity3d.sdk.2021.1.14.1.nupkg -o "$WORK/sdk.nupkg"
  (cd "$WORK" && rm -rf sdk && mkdir sdk && cd sdk && unzip -q ../sdk.nupkg)
fi
if [ ! -f "$WORK/nunit.framework.dll" ]; then     # (the edit-mode tests bind against it)
  curl -sL $NUGET/nunit/3.14.0/nunit.3.14.0.nupkg -o "$WORK/nunit.nupkg"
  (cd "$WORK" && rm -rf nunit && mkdir nunit && cd nunit && unzip -q ../nunit.nupkg && cp lib/netstandard2.0/nunit.framework.dll ..)
fi
if [ ! -d "$WORK/ref-$VERSION" ]; then
  git clone -q --depth 1 --branch "$VERSION" --filter=blob:limit=2m https://github.com/Unity-Technologies/UnityCsReference "$WORK/ref-$VERSION"
fi
mkdir -p "$WORK/stubs"; cp "$HERE/Stubs.cs" "$WORK/stubs/"
(cd "$HERE" && dotnet build -nologo -v q -o "$WORK/bin" >/dev/null)
L="$WORK/sdk/lib"; REFS="$L/UnityEngine.dll;$L/UnityEditor.dll;$WORK/nunit.framework.dll"
: > "$WORK/uses.txt"; : > "$WORK/syntax.txt"
# every combination of the #if symbols the scripts use (the editor with the tests, both players, the optional code): a file
# behind an #if no set defines is never even parsed (docs/LEARNINGS.md A12)
for d in "UNITY_ANDROID;UNITY_EDITOR;ENABLE_INPUT_SYSTEM;UNITY_INCLUDE_TESTS;UNITY_6000_0_OR_NEWER" \
         "UNITY_IOS;UNITY_EDITOR;ENABLE_LEGACY_INPUT_MANAGER;UNITY_INCLUDE_TESTS;UNITY_6000_0_OR_NEWER" \
         "UNITY_IOS;ENABLE_INPUT_SYSTEM;UNITY_6000_0_OR_NEWER" "UNITY_ANDROID;ENABLE_INPUT_SYSTEM;UNITY_6000_0_OR_NEWER" \
         "DTS_UNITY_IAP;DTS_SCREENSHOTS;UNITY_STANDALONE;UNITY_EDITOR;UNITY_6000_0_OR_NEWER"; do
  dotnet "$WORK/bin/apiscan.dll" "$REPO/Assets" "$REFS" "$WORK/stubs" "$d" >> "$WORK/uses.txt" 2>/dev/null
  ERRORS=1 dotnet "$WORK/bin/apiscan.dll" "$REPO/Assets" "$REFS" "$WORK/stubs" "$d" 2>/dev/null | grep '^SYNTAX' >> "$WORK/syntax.txt" || true
done
if [ -s "$WORK/syntax.txt" ]; then echo "SYNTAX ERRORS (Unity will not compile these):"; sort -u "$WORK/syntax.txt"; fi
# the packages, against the pinned Unity (nothing here compiles them: docs/LEARNINGS.md A15)
python3 "$HERE/package_minimums.py" "$REPO" || PACKAGES_BAD=1
python3 "$HERE/obsolete_check.py" "$WORK/ref-$VERSION" "$WORK/uses.txt" "$@"
[ ! -s "$WORK/syntax.txt" ] && [ -z "${PACKAGES_BAD:-}" ]
