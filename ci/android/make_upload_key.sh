#!/usr/bin/env bash
# Create the Android upload key for Google Play, once. Play App Signing keeps the real app-signing
# key; this key only signs your uploads (Google can reset it if it is ever lost).
#
# Usage: ./ci/android/make_upload_key.sh ~/keys/kickoff-upload.jks
#
# keytool asks for the passwords. Keep the .jks file and both passwords safe (a password manager
# and a backup) and NEVER commit them to git. Then build with:
#   DTS_KEYSTORE_PATH=~/keys/kickoff-upload.jks DTS_KEYSTORE_PASS=... DTS_KEY_ALIAS=upload DTS_KEY_PASS=... \
#   ./ci/android/build_android.sh release
set -euo pipefail

OUT="${1:?Give the path for the new keystore, outside the repository, e.g. ~/keys/kickoff-upload.jks}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
case "$(cd "$(dirname "$OUT")" 2>/dev/null && pwd)/" in
  "$ROOT"/*) echo "Put the keystore outside the repository ($ROOT) so it can never be committed."; exit 1 ;;
esac
[ -e "$OUT" ] && { echo "$OUT already exists: keep using it (a new key would need a reset in Play Console)."; exit 1; }

# A JDK's keytool; else the OpenJDK that Unity's Android Build Support installs.
KEYTOOL="${KEYTOOL:-$(command -v keytool || true)}"
if [ -z "$KEYTOOL" ]; then
  for hub in "/Applications/Unity/Hub/Editor" "$HOME/Unity/Hub/Editor" "/c/Program Files/Unity/Hub/Editor"; do
    KEYTOOL="$(ls -d "$hub"/6000.*/{Unity.app/Contents,Editor}/Data/PlaybackEngines/AndroidPlayer/OpenJDK/bin/keytool* 2>/dev/null | sort -rV | head -n 1 || true)"
    [ -n "$KEYTOOL" ] && break
  done
fi
[ -x "${KEYTOOL:-}" ] || { echo "No keytool found: install a JDK, or set KEYTOOL=/path/to/keytool"; exit 1; }

mkdir -p "$(dirname "$OUT")"
"$KEYTOOL" -genkeypair -v -keystore "$OUT" -alias upload -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Astradite, O=Astradite"
echo "==> Created $OUT with the key alias 'upload'. Back it up now."
