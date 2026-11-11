#!/bin/bash
# A city's light, computed by the game's own code: compiles Progression/Cities.cs's CityClimate and Art/ChapterTheme.cs with
# tiny Unity stand-ins (Unity.cs), checks it, and writes each chapter's mood in that city for preview_street.py --mood-json.
#   tools/city_climate/run.sh Florida 1 3 /abs/out/dir      (needs dotnet 8 and Python 3)
set -e
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
WORK=${CLIMATE_WORK:-/tmp/city_climate}; rm -rf "$WORK"; mkdir -p "$WORK" "${@: -1}"
cp "$HERE/climate.csproj" "$HERE/Unity.cs" "$HERE/Program.cs" "$REPO/Assets/_Game/Scripts/Art/ChapterTheme.cs" "$WORK/"
python3 "$HERE/extract.py" "$REPO/Assets/_Game/Scripts/Progression/Cities.cs" "$WORK/Climate.cs"
(cd "$WORK" && dotnet build -nologo -v q -o "$WORK/bin" >/dev/null)
dotnet "$WORK/bin/climate.dll" "$@"
