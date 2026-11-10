#!/bin/bash
# Checks every Unity API the game's scripts use against a Unity version's [Obsolete] list, before opening the project in
# that version (docs/LEARNINGS.md A11). Needs dotnet 8, python 3 and git; downloads Unity's 2021 reference assemblies
# (NuGet unity3d.sdk) to resolve the calls, and the version's C# reference source to read what it removed.
#   tools/unity_api_check/run.sh 6000.5          # ERROR lines: what that Unity refuses to compile
#   tools/unity_api_check/run.sh 6000.5 --all    # and its deprecation warnings
set -e
VERSION=${1:?a Unity version branch, e.g. 6000.5}; shift || true
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
WORK=${UNITY_API_CHECK_WORK:-/tmp/unity_api_check}; mkdir -p "$WORK"
if [ ! -f "$WORK/sdk/lib/UnityEngine.dll" ]; then
  curl -sL https://www.nuget.org/api/v2/package/Unity3D.SDK/2021.1.14.1 -o "$WORK/sdk.nupkg"
  (cd "$WORK" && rm -rf sdk && mkdir sdk && cd sdk && unzip -q ../sdk.nupkg)
fi
if [ ! -d "$WORK/ref-$VERSION" ]; then
  git clone -q --depth 1 --branch "$VERSION" --filter=blob:limit=2m https://github.com/Unity-Technologies/UnityCsReference "$WORK/ref-$VERSION"
fi
mkdir -p "$WORK/stubs"; cp "$HERE/Stubs.cs" "$WORK/stubs/"
(cd "$HERE" && dotnet build -nologo -v q -o "$WORK/bin" >/dev/null)
L="$WORK/sdk/lib"; : > "$WORK/uses.txt"
for d in "UNITY_ANDROID;UNITY_EDITOR;ENABLE_INPUT_SYSTEM;UNITY_INCLUDE_TESTS;UNITY_6000_0_OR_NEWER" \
         "UNITY_IOS;UNITY_EDITOR;ENABLE_LEGACY_INPUT_MANAGER;UNITY_6000_0_OR_NEWER" \
         "UNITY_IOS;ENABLE_INPUT_SYSTEM;UNITY_6000_0_OR_NEWER" "UNITY_ANDROID;ENABLE_INPUT_SYSTEM;UNITY_6000_0_OR_NEWER" \
         "DTS_UNITY_IAP;DTS_SCREENSHOTS;UNITY_STANDALONE;UNITY_6000_0_OR_NEWER"; do
  dotnet "$WORK/bin/apiscan.dll" "$REPO/Assets" "$L/UnityEngine.dll;$L/UnityEditor.dll" "$WORK/stubs" "$d" >> "$WORK/uses.txt" 2>/dev/null
done
python3 "$HERE/obsolete_check.py" "$WORK/ref-$VERSION" "$WORK/uses.txt" "$@"
