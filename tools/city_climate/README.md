# A city's light, from the game's own code

`run.sh` compiles the game's `CityClimate` (`Progression/Cities.cs`, copied out by `extract.py`) and `Art/ChapterTheme.cs`
against tiny Unity stand-ins (`Unity.cs`), checks what the city tests check (Kamakura changes nothing, a sun keeps its
brightness, the haze never hides the street), and writes each chapter's mood in a city's climate as JSON for
`tools/blender/preview_street.py --mood-json`:

```
tools/city_climate/run.sh Florida 1 3 /abs/out/dir     # florida_ch1.json, florida_ch3.json
```

It needs dotnet 8 and Python 3, and builds in `/tmp/city_climate` (or `$CLIMATE_WORK`), never in the repository. If
`Cities.cs` moves its climate code, `extract.py` stops with an error rather than mirroring numbers by hand
(`docs/LEARNINGS.md` A6).
