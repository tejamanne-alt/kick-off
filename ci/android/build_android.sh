#!/usr/bin/env bash
# Build Kick Off for Google Play end to end: Unity batch build -> signed Android App Bundle (.aab).
#
# Usage (release, for Play):
#   DTS_KEYSTORE_PATH=~/keys/kickoff-upload.jks DTS_KEYSTORE_PASS=... DTS_KEY_ALIAS=upload DTS_KEY_PASS=... \
#   DTS_VERSION=1.0.0 DTS_BUILD_NUMBER=1 ./ci/android/build_android.sh release
# Usage (a development .apk to install on your own phone):
#   ./ci/android/build_android.sh dev
#
# DTS_BUILD_NUMBER is the Android versionCode: every upload to Play needs a higher one.
# Optional: UNITY=/path/to/Unity (defaults to the project's pinned version in Unity Hub,
#           else the newest Unity 6 installed there).
set -euo pipefail

MODE="${1:-release}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Unity Hub's editor folders on macOS, Linux and Windows (Git Bash).
find_unity() {
  local pinned hub v exe
  pinned="$(sed -n 's/^m_EditorVersion: //p' "$ROOT/ProjectSettings/ProjectVersion.txt")"
  for hub in "/Applications/Unity/Hub/Editor" "$HOME/Unity/Hub/Editor" "/c/Program Files/Unity/Hub/Editor"; do
    [ -d "$hub" ] || continue
    for v in "$pinned" $(ls "$hub" | grep '^6000\.' | sort -rV); do
      for exe in "$hub/$v/Unity.app/Contents/MacOS/Unity" "$hub/$v/Editor/Unity" "$hub/$v/Editor/Unity.exe"; do
        if [ -x "$exe" ]; then echo "$exe"; return 0; fi
      done
    done
  done
  return 1
}

UNITY="${UNITY:-$(find_unity || true)}"
[ -x "${UNITY:-}" ] || {
  echo "No Unity 6 found in Unity Hub. Install it with Android Build Support (incl. the SDK, NDK and OpenJDK),"
  echo "or set UNITY=/path/to/Unity"; exit 1; }

case "$MODE" in
  release)
    METHOD=DribbleToSchool.EditorTools.BuildScripts.BuildAndroidRelease
    OUT="$ROOT/Builds/Android/KickOff.aab"
    for var in DTS_KEYSTORE_PATH DTS_KEYSTORE_PASS DTS_KEY_ALIAS DTS_KEY_PASS; do
      [ -n "${!var:-}" ] || { echo "Set $var (the upload key: see docs/RELEASE.md, or make one with ci/android/make_upload_key.sh)."; exit 1; }
    done
    [ -f "$DTS_KEYSTORE_PATH" ] || { echo "No keystore at $DTS_KEYSTORE_PATH"; exit 1; }
    ;;
  dev)
    METHOD=DribbleToSchool.EditorTools.BuildScripts.BuildAndroidDev
    OUT="$ROOT/Builds/Android/KickOff-dev.apk"
    ;;
  *) echo "Mode must be release or dev"; exit 1 ;;
esac

mkdir -p "$ROOT/Builds"
rm -f "$OUT"
echo "==> Building ($MODE) with $UNITY"
echo "    (the first build also generates every level and the art; it takes a while)"
"$UNITY" -batchmode -quit -projectPath "$ROOT" -buildTarget Android \
  -executeMethod "$METHOD" -logFile "$ROOT/Builds/unity-android.log" || {
  echo "Unity reported a failure: see Builds/unity-android.log"; exit 1; }

[ -f "$OUT" ] || { echo "No build at $OUT: see Builds/unity-android.log"; exit 1; }
echo "==> Done: $OUT ($(du -h "$OUT" | cut -f1))"
if [ "$MODE" = release ]; then
  echo "    Upload it in Play Console > Test and release > (Internal testing first) > Create new release."
else
  echo "    Install on a phone with USB debugging on: adb install -r \"$OUT\""
fi
