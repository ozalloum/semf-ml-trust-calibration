#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict
from pathlib import Path
from ame_io import (
    MassRow, decimal_places, dump_json, mass_audit, mass_file_structure_audit, parse_mass_file,
    parse_reaction_file, reaction_audit, reaction_file_structure_audit, write_csv,
)

MASS_NAMES = {2012: "mass.mas12", 2016: "mass16.txt", 2020: "mass_1.mas20"}
RCT1_NAMES = {2012: "rct1.mas12", 2016: "rct1-16.txt", 2020: "rct1.mas20"}
RCT2_NAMES = {2012: "rct2.mas12", 2016: "rct2-16.txt", 2020: "rct2_1.mas20"}


def row_dict(r: MassRow) -> dict:
    d = asdict(r)
    d["B_total_MeV"] = None if r.be_per_A_keV is None else r.A * r.be_per_A_keV / 1000.0
    d["B_total_unc_MeV"] = None if r.be_per_A_unc_keV is None else r.A * r.be_per_A_unc_keV / 1000.0
    d["I"] = (r.N - r.Z) / r.A
    d["even_N"] = int(r.N % 2 == 0)
    d["even_Z"] = int(r.Z % 2 == 0)
    return d


def eligible_primary(r: MassRow) -> bool:
    return (
        r.Z >= 8 and r.N >= 8 and
        r.mass_excess_keV is not None and r.be_per_A_keV is not None and
        not r.mass_estimated and not r.be_estimated and
        r.mass_excess_unc_keV is not None and r.mass_excess_unc_keV < 100.0
    )


def eligible_broad(r: MassRow) -> bool:
    return (
        r.Z >= 8 and r.N >= 8 and
        r.mass_excess_keV is not None and r.be_per_A_keV is not None and
        not r.mass_estimated and not r.be_estimated
    )


def eligible_light(r: MassRow) -> bool:
    return (
        r.Z >= 2 and r.N >= 2 and
        r.mass_excess_keV is not None and r.be_per_A_keV is not None and
        not r.mass_estimated and not r.be_estimated
    )


def derive_observables(rows: list[MassRow]) -> list[dict]:
    # A5 freeze: a derived experimental observable is defined only from finite,
    # non-estimated binding-energy entries. Estimated (#) constituents are never
    # silently treated as measured neighbors.
    measured_bmap = {
        (r.N, r.Z): r.A * r.be_per_A_keV
        for r in rows
        if r.be_per_A_keV is not None and not r.be_estimated
    }
    alpha_B = measured_bmap.get((2, 2))
    first = []
    for r in rows:
        if r.be_per_A_keV is None:
            continue
        key = (r.N, r.Z)
        B = measured_bmap.get(key)
        target_measured = B is not None
        vals = {}
        if not target_measured:
            vals = {"Sn_keV": None, "S2n_keV": None, "Sp_keV": None, "S2p_keV": None, "Qalpha_keV": None}
            first.append({"vintage": r.vintage, "N": r.N, "Z": r.Z, "A": r.A, "element": r.element, "target_measured": False, **vals})
            continue
        for name, nkey in [
            ("Sn_keV", (r.N-1, r.Z)), ("S2n_keV", (r.N-2, r.Z)),
            ("Sp_keV", (r.N, r.Z-1)), ("S2p_keV", (r.N, r.Z-2)),
        ]:
            nb = measured_bmap.get(nkey)
            vals[name] = None if nb is None else B - nb
        daughter = measured_bmap.get((r.N-2, r.Z-2))
        vals["Qalpha_keV"] = None if daughter is None or alpha_B is None else daughter + alpha_B - B
        first.append({"vintage": r.vintage, "N": r.N, "Z": r.Z, "A": r.A, "element": r.element, "target_measured": True, **vals})
    fmap = {(d["N"], d["Z"]): d for d in first}
    for d in first:
        s2n_next = fmap.get((d["N"]+2, d["Z"]), {}).get("S2n_keV")
        s2p_next = fmap.get((d["N"], d["Z"]+2), {}).get("S2p_keV")
        d["delta2n_keV"] = None if d["S2n_keV"] is None or s2n_next is None else d["S2n_keV"] - s2n_next
        d["delta2p_keV"] = None if d["S2p_keV"] is None or s2p_next is None else d["S2p_keV"] - s2p_next
    return first


def compare_official(derived: list[dict], rct1, rct2) -> dict:
    dmap = {(d["N"], d["Z"]): d for d in derived}
    r1 = {(r.N, r.Z): r.named() for r in rct1}
    r2 = {(r.N, r.Z): r.named() for r in rct2}
    comparisons = []
    checks = [("Sn_keV", r2), ("Sp_keV", r2), ("S2n_keV", r1), ("S2p_keV", r1), ("Qalpha_keV", r1)]
    for key, d in dmap.items():
        N, Z = key
        for name, official_map in checks:
            dv = d.get(name); ov = official_map.get(key, {}).get(name)
            est = official_map.get(key, {}).get(name.replace("_keV", "_estimated"), False)
            if dv is None or ov is None or est:
                continue
            comparisons.append({"N": N, "Z": Z, "observable": name, "derived_keV": dv, "official_keV": ov, "abs_diff_keV": abs(dv-ov)})
    if comparisons:
        mx = max(x["abs_diff_keV"] for x in comparisons)
        q95 = sorted(x["abs_diff_keV"] for x in comparisons)[max(0, math.ceil(0.95*len(comparisons))-1)]
    else:
        mx = q95 = None
    return {"n": len(comparisons), "max_abs_diff_keV": mx, "p95_abs_diff_keV": q95, "fail_gt_2keV": sum(x["abs_diff_keV"] > 2.0 for x in comparisons), "rows": comparisons}


def common_precision_equal(a: MassRow, b: MassRow) -> bool:
    if a.mass_excess_keV is None or b.mass_excess_keV is None:
        return False
    da = decimal_places(a.mass_excess_raw); db = decimal_places(b.mass_excess_raw)
    if da is None or db is None:
        return False
    d = min(da, db)
    return round(a.mass_excess_keV, d) == round(b.mass_excess_keV, d)


def historical_membership(old: list[MassRow], new: list[MassRow], old_v: int, new_v: int) -> list[dict]:
    old_map = {(r.N, r.Z): r for r in old if r.mass_excess_keV is not None and not r.mass_estimated}
    out = []
    for r in new:
        if r.mass_excess_keV is None or r.mass_estimated:
            continue
        prior = old_map.get((r.N, r.Z))
        if prior is None:
            label = "new"
            delta = None
        else:
            delta = r.mass_excess_keV - prior.mass_excess_keV
            label = "unchanged" if common_precision_equal(prior, r) else "changed"
        out.append({
            "old_vintage": old_v, "new_vintage": new_v, "N": r.N, "Z": r.Z, "A": r.A,
            "element": r.element, "label": label, "delta_mass_excess_keV": delta,
            "new_primary_eligible": eligible_primary(r), "new_broad_eligible": eligible_broad(r),
            "old_mass_excess_keV": None if prior is None else prior.mass_excess_keV,
            "new_mass_excess_keV": r.mass_excess_keV,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    ap.add_argument("--audit", type=Path, default=Path("audit"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True); args.audit.mkdir(parents=True, exist_ok=True)

    masses = {}; reaction_reports = {}; mass_reports = {}; consistency = {}
    for v in (2012, 2016, 2020):
        mpath = args.raw / str(v) / MASS_NAMES[v]
        r1path = args.raw / str(v) / RCT1_NAMES[v]
        r2path = args.raw / str(v) / RCT2_NAMES[v]
        for p in (mpath, r1path, r2path):
            if not p.exists():
                raise FileNotFoundError(f"Missing required raw file: {p}")
        m = parse_mass_file(mpath, v); r1 = parse_reaction_file(r1path, v, "rct1"); r2 = parse_reaction_file(r2path, v, "rct2")
        masses[v] = m
        mass_reports[v] = {"parsed": mass_audit(m), "file_structure": mass_file_structure_audit(mpath, v)}
        reaction_reports[v] = {
            "rct1": {"parsed": reaction_audit(r1), "file_structure": reaction_file_structure_audit(r1path, v, "rct1")},
            "rct2": {"parsed": reaction_audit(r2), "file_structure": reaction_file_structure_audit(r2path, v, "rct2")},
        }
        pm = mass_reports[v]["parsed"]; fm = mass_reports[v]["file_structure"]
        if (pm["duplicates"] or pm["A_identity_failures"] or pm["empty_element"] or
                fm["unparsed_candidate_rows"] or fm["short_width_candidates"] or fm["A_identity_failures"] or fm["empty_element"]):
            raise RuntimeError(f"Mass parser/file-structure integrity gate failed for {v}: {mass_reports[v]}")
        for rk in ("rct1", "rct2"):
            pr = reaction_reports[v][rk]["parsed"]; fr = reaction_reports[v][rk]["file_structure"]
            if pr["duplicates"] or pr["A_identity_failures"] or pr["empty_element"] or fr["unparsed_candidate_rows"] or fr["short_width_candidates"]:
                raise RuntimeError(f"Reaction parser/file-structure gate failed for {v} {rk}: {reaction_reports[v][rk]}")
        write_csv((row_dict(x) for x in m), args.out / f"ame{v}_mass_all.csv")
        write_csv((row_dict(x) for x in m if eligible_primary(x)), args.out / f"ame{v}_primary_precision.csv")
        write_csv((row_dict(x) for x in m if eligible_broad(x)), args.out / f"ame{v}_broad_measured.csv")
        write_csv((row_dict(x) for x in m if eligible_light(x)), args.out / f"ame{v}_light_stress.csv")
        write_csv((x.named() for x in r1), args.out / f"ame{v}_rct1.csv")
        write_csv((x.named() for x in r2), args.out / f"ame{v}_rct2.csv")
        derived = derive_observables(m)
        write_csv(derived, args.out / f"ame{v}_derived_observables.csv")
        c = compare_official(derived, r1, r2)
        write_csv(c.pop("rows"), args.audit / f"ame{v}_derived_vs_official.csv")
        consistency[v] = c

    h1216 = historical_membership(masses[2012], masses[2016], 2012, 2016)
    h1620 = historical_membership(masses[2016], masses[2020], 2016, 2020)
    write_csv(h1216, args.out / "historical_2012_to_2016_membership.csv")
    write_csv(h1620, args.out / "historical_2016_to_2020_membership.csv")
    write_csv((r for r in h1216 if r["label"] == "new" and r["new_primary_eligible"]), args.out / "historical_2012_to_2016_new_primary.csv")
    write_csv((r for r in h1620 if r["label"] == "new" and r["new_primary_eligible"]), args.out / "historical_2016_to_2020_new_primary_LOCKED_CONFIRMATION.csv")

    summary = {
        "mass_audits": mass_reports,
        "reaction_audits": reaction_reports,
        "derived_observable_consistency": consistency,
        "historical_counts": {
            "2012_to_2016": {k: sum(x["label"] == k for x in h1216) for k in ("new", "changed", "unchanged")},
            "2016_to_2020": {k: sum(x["label"] == k for x in h1620) for k in ("new", "changed", "unchanged")},
            "2012_to_2016_new_primary": sum(x["label"] == "new" and x["new_primary_eligible"] for x in h1216),
            "2016_to_2020_new_primary_LOCKED_CONFIRMATION": sum(x["label"] == "new" and x["new_primary_eligible"] for x in h1620),
        },
        "historical_label_rule": "new=absent as measured non-estimated in old vintage; unchanged=same mass excess after rounding both vintages to the coarser reported decimal precision; changed=otherwise",
    }
    dump_json(summary, args.audit / "DATA_PRODUCT_SUMMARY.json")
    bad = {v: c["fail_gt_2keV"] for v, c in consistency.items()}
    if any(n > 0 for n in bad.values()):
        raise RuntimeError(f"Derived-observable consistency gate failed (>2 keV): {bad}")
    print("DATA PRODUCTS: PASS")
    print(summary["historical_counts"])

if __name__ == "__main__":
    main()
