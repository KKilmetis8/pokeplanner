# Pokémon team planner

Plan a playthrough team for any main-series game from Gen 1 to Gen 6: Red/Blue/Yellow through X/Y and Omega Ruby/Alpha Sapphire.

## Install (Android)
1. Open the app link in **Chrome**.
2. Tap **⋮ → Install app** (or *Add to Home screen*).
3. Open it from the home-screen icon. Games you have opened work offline.

## Using it
- Pick the **game** at the top.
- Toggle the **stretches** (before each gym, before the Elite Four, post-game) you want to catch in. Each Pokémon shows the earliest stretch it can be obtained, and how.
- **+** adds to the team (max 6). Picking a starter hides the other starters.
- The right side shows gym and Elite Four matchups, defensive weaknesses and STAB coverage, using that game's generation type chart.

Your team is stored only on your own device. Nothing is shared.

## Data
Encounters come from the [PokeAPI](https://github.com/PokeAPI/pokeapi) CSV dump at build time; the app makes no API calls.
Which gym stretch each location belongs to is hand-assigned per game in `config/` and is approximate.

```
bash tools/fetch.sh                 # download PokeAPI CSVs into data_src/
python3 -I tools/dump_locs.py       # optional: locs/<game>.txt, input for writing configs
python3 -I tools/build.py           # config/ + data_src/ -> data/<version>.json
```
Bump `VERSION` in `sw.js` after changing `index.html` or `data/`.
