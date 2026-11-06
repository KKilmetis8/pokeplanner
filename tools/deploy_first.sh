#!/bin/bash
set -e
cd ~/pokeplanner
git init -q -b main 2>/dev/null || git init -q
git checkout -q -B main
git add -A
git status --short | head -50
git commit -q -m "Pokémon team planner for Gens 1-6

Generalizes the Platinum planner to every main-series game from Red/Blue to ORAS.
Data built offline from PokeAPI CSVs plus per-game gym-stretch configs.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
gh repo create KKilmetis8/pokeplanner --public --description "Plan a Pokémon playthrough team (Gens 1-6) from what is catchable before each gym" --source . --remote origin --push
gh api -X POST repos/KKilmetis8/pokeplanner/pages -f "source[branch]=main" -f "source[path]=/" >/dev/null
gh api repos/KKilmetis8/pokeplanner/pages
