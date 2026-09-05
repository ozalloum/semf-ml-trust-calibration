#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd

from common import (
    MLP_SEEDS, bootstrap_semf, canonical_json, ensemble_mean, family_predictions,
    fit_semf, historical_test, metrics, model_grid, select_gate_alpha, select_lambda,
    semf_predict, sha256_file, write_json
)


def cfg_key(cfg):
    return json.dumps(cfg, sort_keys=True, separators=(",", ":"))


def main():
    ap=argparse.ArgumentParser(description="Stage 3C: AME2012->AME2016 development and pre-confirmation freeze")
    ap.add_argument("--processed",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--protocol-root",type=Path,default=Path("frozen_protocol"))
    ap.add_argument("--smoke",action="store_true",help="Synthetic/CI smoke mode: reduced grids/seeds/bootstraps; never scientific")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    train,test=historical_test(a.processed,2012,2016)
    if len(train)<100 or len(test)<5:
        raise RuntimeError(f"Development data too small: train={len(train)} test={len(test)}")
    y=test.B_total_MeV.to_numpy(float)
    semf=fit_semf(train); phys=semf_predict(test,semf); phys_train=semf_predict(train,semf)
    grids=model_grid()
    seeds=MLP_SEEDS[:1] if a.smoke else MLP_SEEDS
    if a.smoke:
        grids={"ridge":grids["ridge"][:2],"hgb":grids["hgb"][:2],"mlp":[{**grids["mlp"][0],"_max_iter_test":120,"_n_iter_test":12}]}

    all_rows=[]; selected={}; dev_preds={"N":test.N.astype(int).tolist(),"Z":test.Z.astype(int).tolist(),"A":test.A.astype(int).tolist(),"B_true":y.tolist(),"B_semf":phys.tolist()}
    for fam in ["ridge","hgb","mlp"]:
        fam_rows=[]
        for cfg in grids[fam]:
            preds=family_predictions(fam,cfg,train,test,seeds=seeds)
            seed_mae={str(s):float(metrics(y,p)["mae"]) for s,p in preds.items()}
            row={"family":fam,"config":cfg,"config_key":cfg_key(cfg),"mean_seed_mae":float(np.mean(list(seed_mae.values()))),"seed_mae":seed_mae}
            fam_rows.append(row); all_rows.append(row)
        fam_rows.sort(key=lambda r:(r["mean_seed_mae"],r["config_key"]))
        best=fam_rows[0]; cfg=best["config"]
        ml_preds=family_predictions(fam,cfg,train,test,seeds=seeds)
        ml_mean=ensemble_mean(ml_preds)
        lam,lam_rows=select_lambda(y,ml_preds,phys)
        # Residual repair reuses the same family hyperparameters by A7.
        rr_preds=family_predictions(fam,cfg,train,test,residual_base_train=phys_train,residual_base_test=phys,seeds=seeds)
        rr_mean=ensemble_mean(rr_preds)
        gate_alpha,gate_rows=select_gate_alpha(fam,cfg,train,test,ml_mean,phys)
        selected[fam]={
            "config":cfg,"development_data_only_mean_seed_mae":best["mean_seed_mae"],
            "soft_prior_lambda":float(lam),"adaptive_gate_alpha":float(gate_alpha),
            "lambda_development_curve":lam_rows,"gate_development_curve":gate_rows,
            "seeds":seeds if fam=="mlp" else [-1],
            "development_metrics":{
                "physics_only":metrics(y,phys),"data_only_ensemble":metrics(y,ml_mean),
                "soft_prior_ensemble":metrics(y,(1-lam)*ml_mean+lam*phys),
                "residual_repair_ensemble":metrics(y,rr_mean),
            }
        }
        dev_preds[f"B_{fam}_data"]=ml_mean.tolist()
        dev_preds[f"B_{fam}_soft"]=((1-lam)*ml_mean+lam*phys).tolist()
        dev_preds[f"B_{fam}_residual"]=rr_mean.tolist()

    # A3 training-only coefficient uncertainty. Full run uses the frozen 5000 refits.
    boot=bootstrap_semf(train,n_boot=200 if a.smoke else 5000,seed=20260913)
    write_json({"training_vintage":2012,"test_vintage":2016,"semf_fit":semf,"bootstrap":boot},a.out/"SEMF_2012_DEVELOPMENT_FIT_AND_BOOTSTRAP.json")
    pd.DataFrame(all_rows).to_json(a.out/"DEVELOPMENT_GRID_RESULTS.jsonl",orient="records",lines=True)
    pd.DataFrame(dev_preds).to_csv(a.out/"DEVELOPMENT_PREDICTIONS.csv",index=False)

    protocol_hashes={}
    for p in sorted(a.protocol_root.glob("*.md")):
        protocol_hashes[p.name]=sha256_file(p)
    input_hashes={p.name:sha256_file(p) for p in [a.processed/"ame2012_primary_precision.csv",a.processed/"ame2016_primary_precision.csv",a.processed/"historical_2012_to_2016_new_primary.csv"]}
    freeze={
        "stage":"3C","status":"FROZEN_AFTER_DEVELOPMENT","created_unix":time.time(),"smoke_mode":bool(a.smoke),
        "development_transition":"AME2012->AME2016","confirmation_transition":"AME2016->AME2020",
        "no_2020_label_access_in_this_stage":True,
        "selected":selected,"semf_2012_fit":semf,
        "protocol_hashes":protocol_hashes,"development_input_hashes":input_hashes,
        "rules":{
            "no_hyperparameter_retuning_after_this_freeze":True,
            "residual_repair_reuses_data_only_hyperparameters":True,
            "soft_lambda_frozen_per_family":True,
            "adaptive_gate_complexity_frozen_per_family":True,
        },
    }
    freeze_text=canonical_json(freeze)
    freeze_path=a.out/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.json"
    freeze_path.write_text(freeze_text,encoding="utf-8")
    digest=sha256_file(freeze_path)
    (a.out/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.sha256").write_text(digest+"  "+freeze_path.name+"\n",encoding="utf-8")
    write_json({"status":"PASS","freeze_sha256":digest,"train_n":len(train),"development_test_n":len(test),"smoke_mode":bool(a.smoke)},a.out/"STAGE3C_STATUS.json")
    print("STAGE 3C: PASS - development choices frozen")
    print("freeze_sha256",digest)

if __name__=="__main__": main()
