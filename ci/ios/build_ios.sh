#!/usr/bin/env bash
# Build an iOS .ipa end to end on a Mac: Unity export -> Xcode archive -> .ipa.
#
# Usage:
#   DTS_APPLE_TEAM_ID=ABCDE12345 ./ci/ios/build_ios.sh [appstore|upload|development]
#     development: an .ipa for your own registered devices
#     appstore:    an .ipa for App Store Connect (upload it with Apple's Transporter app)
#     upload:      archives and uploads straight to App Store Connect (then it appears in TestFlight).
#                  Signs in with Xcode's account, or with an App Store Connect API key when
#                  ASC_KEY_PATH (the .p8 file), ASC_KEY_ID and ASC_ISSUER_ID are set.
#
# Needs Xcode 26 or later (App Store Connect only accepts builds made with the iOS 26 SDK or later).
# Optional: UNITY=/path/to/Unity (defaults to the pinned version, else the newest
#           Unity 6 in Unity Hub that supports UIScene),
#           DTS_VERSION=1.0.1 DTS_BUILD_NUMBER=7
set -euo pipefail

MODE="${1:-development}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "${DTS_APPLE_TEAM_ID:?Set DTS_APPLE_TEAM_ID to your 10-character Apple team id}"

# Apple's current SDK refuses to launch apps without the UIScene lifecycle.
# Unity only generates it from 6000.0.68f1 (6.0 LTS), 6000.3.8f1 (6.3 LTS) or 6000.4+.
# 6000.1.x and 6000.2.x never got it.
has_uiscene() {
  local v="$1" minor patch
  minor="$(echo "$v" | cut -d. -f2)"
  patch="$(echo "$v" | cut -d. -f3 | sed 's/[^0-9].*//')"
  [ "$minor" = 0 ] && [ "$patch" -ge 68 ] && return 0
  [ "$minor" = 3 ] && [ "$patch" -ge 8 ] && return 0
  [ "$minor" -ge 4 ] && return 0
  return 1
}

HUB=/Applications/Unity/Hub/Editor
if [ -z "${UNITY:-}" ]; then
  # Prefer the exact version the project pins, then the newest one with UIScene support.
  PINNED="$(sed -n 's/^m_EditorVersion: //p' "$ROOT/ProjectSettings/ProjectVersion.txt")"
  if [ -x "$HUB/$PINNED/Unity.app/Contents/MacOS/Unity" ]; then
    UNITY="$HUB/$PINNED/Unity.app/Contents/MacOS/Unity"
  else
    for v in $(ls "$HUB" 2>/dev/null | grep '^6000\.' | sort -rV); do
      if has_uiscene "$v" && [ -x "$HUB/$v/Unity.app/Contents/MacOS/Unity" ]; then
        UNITY="$HUB/$v/Unity.app/Contents/MacOS/Unity"; break
      fi
    done
  fi
fi
[ -x "${UNITY:-}" ] || {
  echo "No Unity with UIScene support found in $HUB."
  echo "Install 6000.0.68f1 or newer (or 6000.3.8f1+) with iOS Build Support from Unity Hub,"
  echo "or set UNITY=/path/to/Unity.app/Contents/MacOS/Unity"; exit 1; }
UNITY_VERSION="$(basename "$(dirname "$(dirname "$(dirname "$(dirname "$UNITY")")")")")"
if [[ "$UNITY_VERSION" == 6000.* ]] && ! has_uiscene "$UNITY_VERSION"; then
  echo "Unity $UNITY_VERSION does not generate the UIScene lifecycle; the app will not launch on current iOS."
  echo "Install 6000.0.68f1+ (or 6000.3.8f1+) and run again."; exit 1
fi

case "$MODE" in
  appstore) OPTIONS="$ROOT/ci/ios/ExportOptions-AppStore.plist" ;;
  upload) OPTIONS="$ROOT/ci/ios/ExportOptions-Upload.plist" ;;
  development) OPTIONS="$ROOT/ci/ios/ExportOptions-Development.plist" ;;
  *) echo "Mode must be appstore, upload or development"; exit 1 ;;
esac

XCODE_MAJOR="$(xcodebuild -version | sed -n 's/^Xcode \([0-9]*\).*/\1/p')"
if [ "$MODE" != development ] && [ "${XCODE_MAJOR:-0}" -lt 26 ]; then
  echo "Xcode $XCODE_MAJOR found: App Store Connect needs builds from Xcode 26 or later. Update Xcode and run again."; exit 1
fi

# Optional App Store Connect API key, for uploading without an Xcode account sign-in (e.g. on CI).
AUTH=()
if [ -n "${ASC_KEY_PATH:-}" ]; then
  : "${ASC_KEY_ID:?Set ASC_KEY_ID with ASC_KEY_PATH}" "${ASC_ISSUER_ID:?Set ASC_ISSUER_ID with ASC_KEY_PATH}"
  AUTH=(-authenticationKeyPath "$ASC_KEY_PATH" -authenticationKeyID "$ASC_KEY_ID" -authenticationKeyIssuerID "$ASC_ISSUER_ID")
fi

echo "==> Exporting Xcode project with Unity $UNITY_VERSION"
# Always export fresh: an Xcode project left over from an older Unity keeps the old app delegate.
rm -rf "$ROOT/Builds/iOS"
"$UNITY" -batchmode -quit -projectPath "$ROOT" -buildTarget iOS \
  -executeMethod DribbleToSchool.EditorTools.BuildScripts.BuildIOS \
  -logFile "$ROOT/Builds/unity-ios.log"

if ! grep -q UIApplicationSceneManifest "$ROOT/Builds/iOS/Info.plist"; then
  echo "WARNING: the exported Info.plist has no UIApplicationSceneManifest; iOS may refuse to launch the app."
  echo "         Check the Unity version at the top of Builds/unity-ios.log."
fi

echo "==> Archiving"
xcodebuild -project "$ROOT/Builds/iOS/Unity-iPhone.xcodeproj" -scheme Unity-iPhone \
  -configuration Release -destination "generic/platform=iOS" \
  -archivePath "$ROOT/Builds/KickOff.xcarchive" \
  -allowProvisioningUpdates ${AUTH[@]+"${AUTH[@]}"} DEVELOPMENT_TEAM="$DTS_APPLE_TEAM_ID" archive

echo "==> Exporting ($MODE)"
TMP_OPTIONS="$(mktemp)"
sed "s/TEAM_ID/$DTS_APPLE_TEAM_ID/" "$OPTIONS" > "$TMP_OPTIONS"
xcodebuild -exportArchive -archivePath "$ROOT/Builds/KickOff.xcarchive" \
  -exportPath "$ROOT/Builds/ipa-$MODE" -exportOptionsPlist "$TMP_OPTIONS" -allowProvisioningUpdates ${AUTH[@]+"${AUTH[@]}"}
rm -f "$TMP_OPTIONS"

if [ "$MODE" = upload ]; then
  echo "==> Uploaded to App Store Connect. It shows in TestFlight once Apple has processed it (usually 10-30 minutes)."
else
  echo "==> Done: $(ls "$ROOT/Builds/ipa-$MODE"/*.ipa)"
fi
