#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from ame_io import parse_mass_file, write_csv
from build_data_products import derive_observables, eligible_primary

MAGIC_N = (20, 28, 50, 82, 126)
MAGIC_Z = (20, 28, 50, 82)
ANCHORS = [(28,20,"anchor_48Ca"), (50,50,"anchor_100Sn"), (82,50,"anchor_132Sn"), (126,82,"anchor_208Pb")]


def midshell_score(r) -> int:
    return min(min(abs(r.N-m) for m in MAGIC_N), min(abs(r.Z-m) for m in MAGIC_Z))


def choose_midshell(rows, amin: int, amax: int, role: str):
    anchor_keys={(n,z) for n,z,_ in ANCHORS}
    c=[r for r in rows if eligible_primary(r) and amin <= r.A <= amax and (r.N,r.Z) not in anchor_keys]
    if not c:
        return None
    c.sort(key=lambda r: (-midshell_score(r), r.mass_excess_unc_keV if r.mass_excess_unc_keV is not None else 1e99, r.A, r.Z, r.N))
    return c[0], role


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mass", type=Path, default=Path("data/raw/2020/mass_1.mas20"))
    ap.add_argument("--out", type=Path, default=Path("audit/SELECTED_NUCLEI_SPOTCHECK_TARGETS.csv"))
    args=ap.parse_args()
    rows=parse_mass_file(args.mass,2020)
    by={(r.N,r.Z):r for r in rows}
    derived={(d["N"],d["Z"]):d for d in derive_observables(rows)}
    selected=[]
    for n,z,role in ANCHORS:
        r=by.get((n,z)); selected.append((r,role))
    for band in [(60,119,"midshell_medium_deterministic"),(120,199,"midshell_heavy_deterministic")]:
        x=choose_midshell(rows,*band)
        if x: selected.append(x)
    out=[]
    for r,role in selected:
        if r is None:
            out.append({"selection_role":role,"present_in_ame2020":False})
            continue
        d=derived.get((r.N,r.Z),{})
        out.append({
            "selection_role": role, "present_in_ame2020": True,
            "N":r.N,"Z":r.Z,"A":r.A,"element":r.element,
            "midshell_score": midshell_score(r),
            "target_primary_eligible": eligible_primary(r),
            "mass_estimated": r.mass_estimated, "be_estimated": r.be_estimated,
            "ame_mass_excess_keV":r.mass_excess_keV,"ame_mass_excess_unc_keV":r.mass_excess_unc_keV,
            "ame_be_per_A_keV":r.be_per_A_keV,"ame_be_per_A_unc_keV":r.be_per_A_unc_keV,
            "ame_Sn_keV":d.get("Sn_keV"),"ame_Sp_keV":d.get("Sp_keV"),
            "ame_S2n_keV":d.get("S2n_keV"),"ame_S2p_keV":d.get("S2p_keV"),"ame_Qalpha_keV":d.get("Qalpha_keV"),
            "reference_source":"", "reference_url":"",
            "reference_mass_excess_keV":"", "reference_be_per_A_keV":"",
            "reference_Sn_keV":"", "reference_Sp_keV":"", "reference_S2n_keV":"", "reference_S2p_keV":"", "reference_Qalpha_keV":"",
            "review_status":"PENDING",
        })
    write_csv(out,args.out)
    print(f"Wrote {len(out)} predeclared spot-check targets to {args.out}")
    print("Populate reference_* columns from NNDC NuDat (and optionally KAERI), then run validate_spotchecks.py.")

if __name__=="__main__": main()
