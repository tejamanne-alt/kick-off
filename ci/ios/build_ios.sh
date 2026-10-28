#!/usr/bin/env bash
# Build an iOS .ipa end to end on a Mac: Unity export -> Xcode archive -> .ipa.
#
# Usage:
#   DTS_APPLE_TEAM_ID=ABCDE12345 ./ci/ios/build_ios.sh [appstore|development]
#
# Optional: UNITY=/path/to/Unity (defaults to the newest Unity 6 in Unity Hub),
#           DTS_VERSION=1.0.1 DTS_BUILD_NUMBER=7
set -euo pipefail

MODE="${1:-development}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "${DTS_APPLE_TEAM_ID:?Set DTS_APPLE_TEAM_ID to your 10-character Apple team id}"

if [ -z "${UNITY:-}" ]; then
  UNITY="$(ls -d /Applications/Unity/Hub/Editor/6000.*/Unity.app/Contents/MacOS/Unity 2>/dev/null | sort -V | tail -1 || true)"
fi
[ -x "$UNITY" ] || { echo "Unity 6 not found. Set UNITY=/path/to/Unity.app/Contents/MacOS/Unity"; exit 1; }

case "$MODE" in
  appstore) OPTIONS="$ROOT/ci/ios/ExportOptions-AppStore.plist" ;;
  development) OPTIONS="$ROOT/ci/ios/ExportOptions-Development.plist" ;;
  *) echo "Mode must be appstore or development"; exit 1 ;;
esac

echo "==> Exporting Xcode project with $UNITY"
"$UNITY" -batchmode -quit -projectPath "$ROOT" -buildTarget iOS \
  -executeMethod DribbleToSchool.EditorTools.BuildScripts.BuildIOS \
  -logFile "$ROOT/Builds/unity-ios.log"

echo "==> Archiving"
xcodebuild -project "$ROOT/Builds/iOS/Unity-iPhone.xcodeproj" -scheme Unity-iPhone \
  -configuration Release -destination "generic/platform=iOS" \
  -archivePath "$ROOT/Builds/DribbleToSchool.xcarchive" \
  -allowProvisioningUpdates DEVELOPMENT_TEAM="$DTS_APPLE_TEAM_ID" archive

echo "==> Exporting .ipa ($MODE)"
TMP_OPTIONS="$(mktemp)"
sed "s/TEAM_ID/$DTS_APPLE_TEAM_ID/" "$OPTIONS" > "$TMP_OPTIONS"
xcodebuild -exportArchive -archivePath "$ROOT/Builds/DribbleToSchool.xcarchive" \
  -exportPath "$ROOT/Builds/ipa-$MODE" -exportOptionsPlist "$TMP_OPTIONS" -allowProvisioningUpdates
rm -f "$TMP_OPTIONS"

echo "==> Done: $(ls "$ROOT/Builds/ipa-$MODE"/*.ipa)"
