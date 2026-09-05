#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd

from common import (
    MLP_SEEDS, ensemble_mean, family_predictions, fit_adaptive_gate, fit_semf,
    metrics, semf_predict, sha256_file, write_json
)
from bwn import fit_bwn, predict_bwn


def load_json(p:Path): return json.loads(p.read_text(encoding="utf-8"))


def verify_freeze(freeze_path:Path):
    digest_path=freeze_path.with_suffix(".sha256")
    # Stage 3C names its digest by replacing .json with .sha256.
    if not digest_path.exists():
        digest_path=freeze_path.parent/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.sha256"
    expected=digest_path.read_text().split()[0].strip()
    actual=sha256_file(freeze_path)
    if expected!=actual: raise RuntimeError(f"Frozen configuration hash mismatch: expected {expected}, got {actual}")
    return actual


def main():
    ap=argparse.ArgumentParser(description="Stage 3E: one-time AME2016->AME2020 confirmation")
    ap.add_argument("--processed",type=Path,required=True)
    ap.add_argument("--stage3c",type=Path,required=True)
    ap.add_argument("--stage3d",type=Path,required=False)
    ap.add_argument("--spotcheck-audit",type=Path,required=False)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    freeze_path=a.stage3c/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.json"
    freeze_sha=verify_freeze(freeze_path); freeze=load_json(freeze_path)
    if freeze.get("smoke_mode") and not a.smoke:
        raise RuntimeError("Refusing real confirmation with a smoke-mode development freeze")
    if not a.smoke:
        if a.spotcheck_audit is None or not a.spotcheck_audit.exists():
            raise RuntimeError("Stage 3B G5 spot-check PASS audit is required before real confirmation")
        sp=load_json(a.spotcheck_audit)
        if sp.get("status")!="PASS": raise RuntimeError("Stage 3B independent spot-check is not PASS")

    lock=a.out/"CONFIRMATION_OPENED_LOCK.json"
    done=a.out/"CONFIRMATION_COMPLETED.json"
    if lock.exists() and not done.exists():
        raise RuntimeError("Confirmation lock already exists without completed results; do not rerun or retune. Audit the interrupted run.")
    if done.exists():
        print("STAGE 3E already completed; refusing to rescore confirmation.")
        return

    train_path=a.processed/"ame2016_primary_precision.csv"
    idx_path=a.processed/"historical_2016_to_2020_new_primary_LOCKED_CONFIRMATION.csv"
    test_path=a.processed/"ame2020_primary_precision.csv"
    # Freeze the exact confirmation membership and configuration BEFORE loading 2020 labels.
    lock_obj={
        "stage":"3E","status":"LOCKED_BEFORE_SCORING","created_unix":time.time(),
        "freeze_sha256":freeze_sha,"training_sha256":sha256_file(train_path),
        "confirmation_membership_sha256":sha256_file(idx_path),"test_population_file_sha256":sha256_file(test_path),
        "no_retuning_permitted":True,"smoke_mode":bool(a.smoke),
    }
    write_json(lock_obj,lock)

    train=pd.read_csv(train_path); ids=pd.read_csv(idx_path)[["N","Z"]].drop_duplicates(); full20=pd.read_csv(test_path)
    test=ids.merge(full20,on=["N","Z"],how="inner",validate="one_to_one")
    if len(test)<1: raise RuntimeError("Confirmation set empty")
    y=test.B_total_MeV.to_numpy(float)
    semf=fit_semf(train); phys_train=semf_predict(train,semf); phys=semf_predict(test,semf)
    pred_table=pd.DataFrame({"N":test.N.astype(int),"Z":test.Z.astype(int),"A":test.A.astype(int),"B_true":y,"B_semf":phys,"is_test":True})
    summary={"stage":"3E","transition":"AME2016->AME2020","n_train":len(train),"n_test":len(test),"physics_only":metrics(y,phys),"families":{},"smoke_mode":bool(a.smoke)}

    for fam,sel in freeze["selected"].items():
        cfg=sel["config"]; lam=float(sel["soft_prior_lambda"]); ga=float(sel["adaptive_gate_alpha"])
        seeds=(MLP_SEEDS[:1] if a.smoke else MLP_SEEDS) if fam=="mlp" else [-1]
        data_preds=family_predictions(fam,cfg,train,test,seeds=seeds)
        rr_preds=family_predictions(fam,cfg,train,test,residual_base_train=phys_train,residual_base_test=phys,seeds=seeds)
        data_mean=ensemble_mean(data_preds); rr_mean=ensemble_mean(rr_preds); soft_mean=(1-lam)*data_mean+lam*phys
        adapt,_=fit_adaptive_gate(fam,cfg,train,test,data_mean,phys,ga)
        per_seed=[]
        for s,p in data_preds.items():
            dmet=metrics(y,p); smet=metrics(y,(1-lam)*p+lam*phys); rmet=metrics(y,rr_preds[s])
            per_seed.append({"seed":int(s),"data_mae":dmet["mae"],"soft_mae":smet["mae"],"residual_mae":rmet["mae"],"G_soft":dmet["mae"]/smet["mae"] if smet["mae"] else None,"G_residual":dmet["mae"]/rmet["mae"] if rmet["mae"] else None})
        summary["families"][fam]={
            "config":cfg,"lambda":lam,"gate_alpha":ga,
            "data_only":metrics(y,data_mean),"soft_prior":metrics(y,soft_mean),"residual_repair":metrics(y,rr_mean),"adaptive_trust":metrics(y,adapt),
            "G_soft":metrics(y,data_mean)["mae"]/metrics(y,soft_mean)["mae"],
            "G_residual":metrics(y,data_mean)["mae"]/metrics(y,rr_mean)["mae"],
            "G_adaptive":metrics(y,data_mean)["mae"]/metrics(y,adapt)["mae"],
            "per_seed":per_seed,
            "fraction_seeds_G_soft_gt1":float(np.mean([r["G_soft"]>1 for r in per_seed])),
            "fraction_seeds_G_residual_gt1":float(np.mean([r["G_residual"]>1 for r in per_seed])),
        }
        pred_table[f"B_{fam}_data"]=data_mean
        pred_table[f"B_{fam}_soft"]=soft_mean
        pred_table[f"B_{fam}_residual"]=rr_mean
        pred_table[f"B_{fam}_adaptive"]=adapt

    bwn_gate=None
    if a.stage3d and (a.stage3d/"BWN_REPRODUCTION_GATE.json").exists():
        bwn_gate=load_json(a.stage3d/"BWN_REPRODUCTION_GATE.json")
    if bwn_gate and bwn_gate.get("status")=="PASS" and not a.smoke:
        # Retrospective historical stress only: formula form post-dates AME2020, parameters are fit on AME2016 training only.
        bf=fit_bwn(train); bp=predict_bwn(test,bf["params"])
        pred_table["B_bwn_retrospective"]=bp
        summary["bwn_retrospective_stress"]={"fit":bf,"metrics":metrics(y,bp),"claim_boundary":"retrospective historical stress test; not a prospective pre-2020 prediction"}
    else:
        summary["bwn_retrospective_stress"]={"status":"SKIPPED","reason":"BWN reproduction gate not PASS or smoke mode"}

    pred_path=a.out/"CONFIRMATION_PREDICTIONS.csv"; pred_table.to_csv(pred_path,index=False)
    summary_path=a.out/"CONFIRMATION_RESULTS.json"; write_json(summary,summary_path)
    completed={**lock_obj,"status":"COMPLETED_ONCE","completed_unix":time.time(),"predictions_sha256":sha256_file(pred_path),"results_sha256":sha256_file(summary_path)}
    write_json(completed,done)
    print(f"STAGE 3E: PASS - confirmation scored once on n={len(test)} nuclei")

if __name__=="__main__": main()
