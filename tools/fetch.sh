#!/bin/bash
mkdir -p "$(dirname "$0")/../data_src" && cd "$(dirname "$0")/../data_src"
B=https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv
for f in encounters encounter_slots encounter_methods encounter_condition_value_map encounter_condition_values location_areas locations location_area_prose location_names pokemon pokemon_types pokemon_types_past pokemon_species pokemon_species_names pokemon_evolution evolution_triggers versions version_groups types type_efficacy type_efficacy_past items generations; do
  curl -sfO "$B/$f.csv" || echo "FAIL $f"
done
wc -l *.csv
