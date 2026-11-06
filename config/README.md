# config/&lt;version-group&gt;.json

Hand-written per game. `tools/build.py` combines it with PokeAPI encounters (`data_src/`) into `data/<version>.json`.
`locs/<version-group>.txt` lists every location with encounters in that game (methods, Pokémon, conditions).

## Segments
Integer 0–9, meaning "obtainable from this point of the story on":

| seg | meaning |
|---|---|
| 0 | before gym 1 (start of game) |
| 1–7 | after badge N, before gym N+1 |
| 8 | after badge 8, before the Elite Four |
| 9 | post-game (after the first Hall of Fame) |

An encounter's segment = max(location or area segment, method gate, condition gates).
Evolutions inherit the base form's segment automatically (ignoring level/item/trade requirements).

## Schema
```jsonc
{
  "gen": 4,
  "versions": {"diamond": "Diamond", "pearl": "Pearl"},   // PokeAPI version id -> display name
  "backfill": {"omega-ruby": ["ruby"]},                   // optional: also use these versions' wild encounters (not gifts/statics/trades)
  "gyms":  [["Roark", "rock"], ...],                      // exactly 8, in story order; type null if it varies (BW Striaton)
  "elite": [["Aaron", "bug"], ..., ["Cynthia", null]],    // E4 in order, champion last; type null for mixed teams
  "starters": [["turtwig","grotle","torterra"], ...],     // starter families; picking one hides the others
  "locations": {"route-201": 0, "distortion-world": 7, "some-unreachable-place": null},
                                                          // EVERY location in locs/<vg>.txt; null = not obtainable in this game
  "areas": {"Lake Verity (after Galactic intervention)": 7},  // optional: English area name (see "areas:" in locs) -> seg; beats "locations"
  "methods": {"surf": 5, "old-rod": 0, "good-rod": 2, "super-rod": 9, "rock-smash": 3, "headbutt": 1},
                                                          // method -> earliest seg it is usable (HM badge, rod given, ...); unlisted = 0
  "conditions": {"swarm-yes": 9},                         // condition value -> earliest seg; build already sends swarm/radar/dual-slot/radio/national-dex/hall-of-fame to 9
  "override": {"eevee": [2, "Hearthome City — gift"], "mew": null, "xerneas": {"x": [7, "..."]}},
                                                          // final word per species: [seg, how], null to remove, or {version: [seg, how] | null}; evolutions never overwrite it
  "exclude": ["mew"],                                     // species never shown (event-only)
  "caveats": "One paragraph shown under the app: what is approximate, what counts as post-game, version quirks."
}
```

Check: `python3 -I tools/build.py <vg>` must print no `!! locations without a segment` line. Then sanity-check
`data/<version>.json` `mons` rows `[name, seg, types, how, isEvolution]`.
