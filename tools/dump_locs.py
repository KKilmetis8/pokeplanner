"""Dump, per version group, every location with encounters: methods, conditions and the Pokemon found there.
Input for hand-writing config/<vg>.json."""
import csv, collections, os, sys
S = os.path.join(os.path.dirname(__file__), "..", "data_src")
O = os.path.join(os.path.dirname(__file__), "..", "locs")
rd = lambda f: list(csv.DictReader(open(os.path.join(S, f + ".csv"), encoding="utf-8")))
ver = {r["id"]: r for r in rd("versions")}
vg = {r["id"]: r["identifier"] for r in rd("version_groups")}
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
mon = {r["id"]: r["identifier"] for r in rd("pokemon")}
out = collections.defaultdict(lambda: collections.defaultdict(lambda: {"areas": set(), "meth": collections.defaultdict(set), "cond": set()}))
for e in rd("encounters"):
    v = ver[e["version_id"]]; g = vg[v["version_group_id"]]
    a = area[e["location_area_id"]]; L = loc[a["location_id"]]
    d = out[g][L]; d["areas"].add(aname.get(e["location_area_id"], a["identifier"]))
    m = meth[slot[e["encounter_slot_id"]]["encounter_method_id"]]
    d["meth"][m].add(mon[e["pokemon_id"]])
    d["cond"] |= {c for c in cond[e["id"]] if not c.endswith(("-none", "-off", "-no")) and not c.startswith(("time-", "season-", "tv-option"))}
for g, locs in out.items():
    with open(os.path.join(O, g + ".txt"), "w", encoding="utf-8") as f:
        for L in sorted(locs):
            d = locs[L]
            f.write(f"{L}  [{lname.get([k for k,v in loc.items() if v==L][0], '')}]\n")
            f.write("  areas: " + " | ".join(sorted(d["areas"])) + "\n")
            for m, ps in sorted(d["meth"].items()):
                f.write(f"  {m}: {' '.join(sorted(ps))}\n")
            if d["cond"]: f.write("  conditions: " + " ".join(sorted(d["cond"])) + "\n")
    print(g, len(locs))
