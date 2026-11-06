"""Build data/<version>.json for every game from PokeAPI CSVs (data_src/) + hand config (config/<vg>.json).

Segments: 0..7 = before gym 1..8, 8 = before Elite Four, 9 = post-game.
Earliest segment of an encounter = max(location/area segment, method gate, condition gates).
Evolutions inherit the base form's segment when that is earlier than their own.

Usage: python3 -I tools/build.py [vg ...]     (no args = all configs)
"""
import csv, collections, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
S, CFG, OUT = (os.path.join(ROOT, d) for d in ("data_src", "config", "data"))
rd = lambda f: list(csv.DictReader(open(os.path.join(S, f + ".csv"), encoding="utf-8")))

ver = {r["identifier"]: r for r in rd("versions")}
vg_id = {r["identifier"]: r["id"] for r in rd("version_groups")}
loc = {r["id"]: r["identifier"] for r in rd("locations")}
lname = {r["location_id"]: r["name"] for r in rd("location_names") if r["local_language_id"] == "9"}
area = {r["id"]: r for r in rd("location_areas")}
aname = {r["location_area_id"]: r["name"] for r in rd("location_area_prose") if r["local_language_id"] == "9"}
slot = {r["id"]: r for r in rd("encounter_slots")}
meth = {r["id"]: r["identifier"] for r in rd("encounter_methods")}
cval = {r["id"]: r["identifier"] for r in rd("encounter_condition_values")}
cond = collections.defaultdict(set)
for r in rd("encounter_condition_value_map"):
    cond[r["encounter_id"]].add(cval[r["encounter_condition_value_id"]])
mon_species = {r["id"]: r["species_id"] for r in rd("pokemon")}
default_mon = {r["species_id"]: r["id"] for r in rd("pokemon") if r["is_default"] == "1"}
species = {r["id"]: r for r in rd("pokemon_species")}
sp_by_name = {r["identifier"]: r["id"] for r in species.values()}
children = collections.defaultdict(list)
for r in species.values():
    if r["evolves_from_species_id"]:
        children[r["evolves_from_species_id"]].append(r["id"])
tname = {r["id"]: r["identifier"] for r in rd("types")}
cur_types = collections.defaultdict(list)
for r in sorted(rd("pokemon_types"), key=lambda r: r["slot"]):
    cur_types[r["pokemon_id"]].append(tname[r["type_id"]])
past_types = collections.defaultdict(lambda: collections.defaultdict(list))  # mon -> last gen -> types
for r in sorted(rd("pokemon_types_past"), key=lambda r: r["slot"]):
    past_types[r["pokemon_id"]][int(r["generation_id"])].append(tname[r["type_id"]])
eff_now = {(tname[r["damage_type_id"]], tname[r["target_type_id"]]): int(r["damage_factor"]) for r in rd("type_efficacy")}
eff_past = collections.defaultdict(dict)  # last gen -> {(a,d): f}
for r in rd("type_efficacy_past"):
    eff_past[int(r["generation_id"])][(tname[r["damage_type_id"]], tname[r["target_type_id"]])] = int(r["damage_factor"])
encs_by_version = collections.defaultdict(list)
for e in rd("encounters"):
    encs_by_version[e["version_id"]].append(e)

GEN_TYPES = {1: 15, 2: 17, 3: 17, 4: 17, 5: 17, 6: 18}
ALL_T = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground", "flying",
         "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"]
GEN1_T = [t for t in ALL_T if t not in ("dark", "steel", "fairy")]
POST = 9
# conditions that push an encounter to post-game unless a config says otherwise
DEFAULT_COND = {"swarm-yes": POST, "radar-on": POST, "slot2-ruby": POST, "slot2-sapphire": POST, "slot2-emerald": POST,
                "slot2-firered": POST, "slot2-leafgreen": POST, "radio-hoenn": POST, "radio-sinnoh": POST,
                "story-progress-national-dex": POST, "story-progress-hall-of-fame": POST, "story-progress-beat-red": POST,
                "story-progress-beat-elite-four-round-two": POST}
METHOD_LABEL = {"walk": "grass/cave", "npc-trade": "trade", "gift-egg": "gift egg", "only-one": "static"}
METHOD_PREF = ["walk", "gift", "static", "npc-trade", "gift-egg", "old-rod", "good-rod", "surf", "super-rod"]
SKIP_BACKFILL = {"gift", "gift-egg", "static", "npc-trade", "only-one", "roaming-grass", "roaming-water"}


def types_for(mon_id, gen):
    for g in sorted(past_types[mon_id]):
        if gen <= g:
            return past_types[mon_id][g]
    return cur_types[mon_id]


def chart(gen):
    """Attacker -> {defender: multiplier} with only non-1 entries."""
    T = GEN1_T if gen == 1 else ALL_T[:GEN_TYPES[gen]]
    c = {}
    for a in T:
        row = {}
        for d in T:
            f = eff_now.get((a, d), 100)
            for g in sorted(eff_past):
                if gen <= g and (a, d) in eff_past[g]:
                    f = eff_past[g][(a, d)]
                    break
            if f != 100:
                row[d] = f / 100
        c[a] = row
    return T, c


def build(vg, cfg):
    gen = cfg["gen"]
    T, C = chart(gen)
    locs, areas = cfg["locations"], cfg.get("areas", {})
    gates = cfg.get("methods", {})
    cgates = {**DEFAULT_COND, **cfg.get("conditions", {})}
    exclude = set(cfg.get("exclude", []))
    missing = set()
    for v, vname in cfg["versions"].items():
        sources = [(v, False)] + [(b, True) for b in cfg.get("backfill", {}).get(v, [])]
        best = {}  # species id -> (seg, pref, how)
        for src, backfill in sources:
            for e in encs_by_version[ver[src]["id"]]:
                a = area[e["location_area_id"]]
                L = loc[a["location_id"]]
                m = meth[slot[e["encounter_slot_id"]]["encounter_method_id"]]
                if backfill and m in SKIP_BACKFILL:
                    continue
                an = aname.get(e["location_area_id"], "")
                if an in areas:
                    seg = areas[an]
                elif L in locs:
                    seg = locs[L]
                else:
                    missing.add(L)
                    continue
                if seg is None:  # location not reachable in this game
                    continue
                cs = cond[e["id"]]
                seg = max([seg, gates.get(m, 0)] + [cgates.get(c, 0) for c in cs])
                sp = mon_species[e["pokemon_id"]]
                name = species[sp]["identifier"]
                if name in exclude or seg is None:
                    continue
                times = sorted(c[5:] for c in cs if c.startswith("time-"))
                place = an or lname.get(a["location_id"], L)
                place = re.sub(r"\s*\(?unknown area \d+\)?", "", re.sub(r"^Road (\d)", r"Route \1", place)) or lname.get(a["location_id"], L)
                how = f"{place} — {METHOD_LABEL.get(m, m.replace('-', ' '))}" + (f" ({', '.join(times)})" if times and len(times) < 3 else "")
                key = (seg, METHOD_PREF.index(m) if m in METHOD_PREF else 99, backfill)
                if sp not in best or key < best[sp][0]:
                    best[sp] = (key, how)
        fixed = set()  # overridden species: evolution inheritance leaves them alone
        for name, o in cfg.get("override", {}).items():
            if isinstance(o, dict):  # per-version: {"x": [seg, how], "y": null}; versions not listed are untouched
                if v not in o:
                    continue
                o = o[v]
            fixed.add(sp_by_name[name])
            if o is None:
                best.pop(sp_by_name[name], None)
            else:
                best[sp_by_name[name]] = ((o[0], -1, False), o[1])
        # evolutions inherit base segment
        rows = {sp: [seg_key[0], how, 0] for sp, (seg_key, how) in best.items()}
        order = sorted(rows, key=lambda s: rows[s][0])
        for sp in order:
            stack = [(c, sp) for c in children[sp]]
            while stack:
                c, root = stack.pop()
                if int(species[c]["generation_id"]) > gen or species[c]["identifier"] in exclude or c in fixed:
                    continue
                if c not in rows or rows[c][0] > rows[sp][0]:
                    base = rows[sp][1].startswith("evolve ") and rows[sp][1] or "evolve " + species[sp]["identifier"]
                    rows[c] = [rows[sp][0], base, 1]
                stack += [(g, root) for g in children[c]]
        mons = [[species[sp]["identifier"], seg, types_for(default_mon[sp], gen), how, ev]
                for sp, (seg, how, ev) in sorted(rows.items(), key=lambda kv: int(kv[0]))]
        doc = {k: cfg[k] for k in ("gen", "gyms", "elite", "starters", "caveats") if k in cfg}
        doc.update(id=v, name=vname, types=T, chart=C, mons=mons)
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, v + ".json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
        print(f"{v}: {len(mons)} Pokémon, by segment {collections.Counter(m[1] for m in mons)}")
    if missing:
        print(f"!! {vg}: locations without a segment: {' '.join(sorted(missing))}")
    return not missing


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(f[:-5] for f in os.listdir(CFG) if f.endswith(".json"))
    ok = all([build(n, json.load(open(os.path.join(CFG, n + ".json"), encoding="utf-8"))) for n in names])
    sys.exit(0 if ok else 1)
