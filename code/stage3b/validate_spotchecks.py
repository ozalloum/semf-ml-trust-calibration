#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

OBS=["mass_excess_keV","be_per_A_keV","Sn_keV","Sp_keV","S2n_keV","S2p_keV","Qalpha_keV"]


def f(x):
    try: return float(x) if str(x).strip() else None
    except Exception: return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sheet", type=Path, default=Path("audit/SELECTED_NUCLEI_SPOTCHECK_TARGETS.csv"))
    ap.add_argument("--out", type=Path, default=Path("audit/SELECTED_NUCLEI_SPOTCHECK_AUDIT.json"))
    ap.add_argument("--tol-kev", type=float, default=2.0)
    a=ap.parse_args()
    rows=list(csv.DictReader(a.sheet.open(newline='',encoding='utf-8')))
    comparisons=[]; errors=[]; measured_rows=0
    for r in rows:
        if r.get("present_in_ame2020") != "True": continue
        measured = r.get("target_primary_eligible") == "True"
        if measured: measured_rows += 1
        src=r.get("reference_source","").strip().lower(); url=r.get("reference_url","").strip()
        if measured and (not src or "nndc" not in src and "nudat" not in src):
            errors.append(f"{r.get('selection_role')}: measured target lacks NNDC/NuDat reference_source")
        if measured and not url:
            errors.append(f"{r.get('selection_role')}: measured target lacks reference_url")
        supplied=0
        for o in OBS:
            av=f(r.get("ame_"+o)); rv=f(r.get("reference_"+o))
            if rv is None: continue
            supplied += 1
            if av is None:
                errors.append(f"{r.get('selection_role')} {o}: reference supplied but AME derived value is NA under A5")
                continue
            diff=abs(av-rv)
            comparisons.append({"selection_role":r.get("selection_role"),"observable":o,"ame":av,"reference":rv,"abs_diff_keV":diff})
            if diff > a.tol_kev:
                errors.append(f"{r.get('selection_role')} {o}: |AME-reference|={diff:.6g} keV > {a.tol_kev} keV")
        if measured and (f(r.get("reference_mass_excess_keV")) is None or f(r.get("reference_be_per_A_keV")) is None):
            errors.append(f"{r.get('selection_role')}: measured target requires reference mass excess and BE/A")
        if measured and supplied < 2:
            errors.append(f"{r.get('selection_role')}: fewer than two quantitative reference fields supplied")
    report={"tolerance_keV":a.tol_kev,"measured_target_rows":measured_rows,"comparison_count":len(comparisons),"errors":errors,"comparisons":comparisons,"status":"PASS" if measured_rows>=5 and not errors else "BLOCKED"}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report["status"] != "PASS": raise SystemExit("INDEPENDENT SPOT-CHECK GATE BLOCKED; see "+str(a.out))
    print(f"INDEPENDENT SPOT-CHECK GATE: PASS ({len(comparisons)} comparisons across {measured_rows} measured targets)")

if __name__=="__main__": main()
