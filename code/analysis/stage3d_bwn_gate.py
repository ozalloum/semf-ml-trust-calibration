#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from bwn import PUBLISHED_BWN, fit_bwn, predict_bwn
from common import metrics, sha256_file, write_json


def main():
    ap=argparse.ArgumentParser(description="Stage 3D: mandatory BWN published-form reproduction gate")
    ap.add_argument("--processed",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    p=a.processed/"ame2020_mass_all.csv"
    d=pd.read_csv(p)
    # Wu et al. state their fit uses experimental AME2020 data for Z,N >= 8.
    mask=(d.N>=8)&(d.Z>=8)&d.B_total_MeV.notna()
    if "be_estimated" in d: mask &= ~d.be_estimated.astype(bool)
    q=d.loc[mask].copy()
    pred=predict_bwn(q,PUBLISHED_BWN); y=q.B_total_MeV.to_numpy(float)
    m=metrics(y,pred); diff=abs(m["rmse"]-0.887)
    passed=diff<=0.02
    report={
        "stage":"3D","status":"PASS" if passed else "BLOCKED",
        "domain":"AME2020 experimental/non-estimated finite binding energies with Z,N>=8",
        "n":len(q),"published_target_rms_MeV":0.887,"reproduced_rms_MeV":m["rmse"],
        "absolute_difference_MeV":diff,"tolerance_MeV":0.02,
        "published_coefficients":PUBLISHED_BWN,
        "input_sha256":sha256_file(p),
        "erratum_note":"The 2025 erratum reports a numerical error in Figure 1; it does not supersede the BWN Table-2 coefficients or 0.887 MeV headline RMS used by this gate.",
        "downstream_rule":"BWN is excluded from Paper 3 comparisons unless this gate passes. Published AME2020-fitted coefficients are never used as holdout coefficients.",
        "smoke_mode":bool(a.smoke),
    }
    # A refit is diagnostic after the exact published-coefficient reproduction passes.
    if passed and not a.smoke:
        refit=fit_bwn(q,max_nfev=20000)
        report["same_domain_refit_diagnostic"]=refit
    write_json(report,a.out/"BWN_REPRODUCTION_GATE.json")
    pd.DataFrame({"N":q.N.astype(int),"Z":q.Z.astype(int),"A":q.A.astype(int),"B_exp":y,"B_BWN_published":pred,"residual":y-pred}).to_csv(a.out/"BWN_REPRODUCTION_RESIDUALS.csv",index=False)
    print(f"STAGE 3D: {report['status']} - reproduced RMS {m['rmse']:.6f} MeV (target 0.887)")
    if not passed and not a.smoke:
        raise SystemExit("BWN REPRODUCTION GATE BLOCKED; do not use BWN downstream")

if __name__=="__main__": main()
