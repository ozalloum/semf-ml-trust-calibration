#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from common import (
    MLP_SEEDS, ensemble_mean, family_predictions, fit_adaptive_gate, fit_semf,
    make_regime_splits, metrics, observable_metrics_from_test, semf_predict, write_json
)
from bwn import fit_bwn, predict_bwn

CORE_BWN = {"R0_random","R1_Ca","R1_Sn","R2_neutron_rich","R3_proton_rich","R4_magic_pm1"}


def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))


def add_magic_pm2(d, splits, suffix=""):
    mZ=np.min(np.abs(d.Z.to_numpy()[:,None]-np.array([20,28,50,82])[None,:]),axis=1)<=2
    mN=np.min(np.abs(d.N.to_numpy()[:,None]-np.array([20,28,50,82,126])[None,:]),axis=1)<=2
    mask=mZ|mN
    splits["R4_magic_pm2"+suffix]=(d.loc[~mask].copy(),d.loc[mask].copy())


def evaluate_regime(name, train, test, freeze, bwn_allowed, smoke):
    if len(test)<2 or len(train)<30:
        return None, [], [], None
    y=test.B_total_MeV.to_numpy(float)
    sf=fit_semf(train); ptrain=semf_predict(train,sf); phys=semf_predict(test,sf)
    preds=pd.DataFrame({"regime":name,"N":test.N.astype(int),"Z":test.Z.astype(int),"A":test.A.astype(int),"B_true":y,"B_semf":phys,"is_test":True})
    b_rows=[{"regime":name,"population":"broad" if name.endswith("_broad") else ("light" if name.startswith("R7") else "primary"),"family":"physics","mechanism":"physics_only",**metrics(y,phys)}]
    method_cols=["B_semf"]
    seeds=MLP_SEEDS[:1] if smoke else MLP_SEEDS
    for fam,sel in freeze["selected"].items():
        cfg=sel["config"]; lam=float(sel["soft_prior_lambda"]); ga=float(sel["adaptive_gate_alpha"])
        use_seeds=seeds if fam=="mlp" else [-1]
        dp=family_predictions(fam,cfg,train,test,seeds=use_seeds); rp=family_predictions(fam,cfg,train,test,residual_base_train=ptrain,residual_base_test=phys,seeds=use_seeds)
        dm=ensemble_mean(dp); rm=ensemble_mean(rp); sm=(1-lam)*dm+lam*phys
        ad,_=fit_adaptive_gate(fam,cfg,train,test,dm,phys,ga)
        vals={"data":dm,"soft":sm,"residual":rm,"adaptive":ad}
        dmae=metrics(y,dm)["mae"]
        for mech,p in vals.items():
            met=metrics(y,p); row={"regime":name,"population":"broad" if name.endswith("_broad") else ("light" if name.startswith("R7") else "primary"),"family":fam,"mechanism":mech,**met}
            if mech!="data" and met["mae"]:
                row["G_vs_data_MAE"]=dmae/met["mae"]
            b_rows.append(row)
            col=f"B_{fam}_{mech}"; preds[col]=p; method_cols.append(col)
        if fam=="mlp":
            frac_soft=[]; frac_res=[]
            for s,p in dp.items():
                d=metrics(y,p)["mae"]; ss=metrics(y,(1-lam)*p+lam*phys)["mae"]; rr=metrics(y,rp[s])["mae"]
                frac_soft.append(d/ss>1); frac_res.append(d/rr>1)
            b_rows.append({"regime":name,"population":"primary","family":fam,"mechanism":"seed_robustness","n":len(use_seeds),"fraction_G_soft_gt1":float(np.mean(frac_soft)),"fraction_G_residual_gt1":float(np.mean(frac_res))})
    bwn_fit=None
    if bwn_allowed and name in CORE_BWN and not smoke:
        bwn_fit=fit_bwn(train); bp=predict_bwn(test,bwn_fit["params"]); preds["B_bwn"]=bp; method_cols.append("B_bwn")
        b_rows.append({"regime":name,"population":"primary","family":"BWN","mechanism":"physics_only_shell_aware",**metrics(y,bp)})
    obs_rows=observable_metrics_from_test(preds,method_cols)
    for r in obs_rows: r["regime"]=name
    return preds,b_rows,obs_rows,{"regime":name,"semf_fit":sf,"bwn_fit":bwn_fit,"n_train":len(train),"n_test":len(test)}


def main():
    ap=argparse.ArgumentParser(description="Stage 3F: frozen structured AME2020 holdouts")
    ap.add_argument("--processed",type=Path,required=True); ap.add_argument("--stage3c",type=Path,required=True)
    ap.add_argument("--stage3d",type=Path); ap.add_argument("--stage3e",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    if not (a.stage3e/"CONFIRMATION_COMPLETED.json").exists() and not a.smoke:
        raise RuntimeError("Structured holdouts open only after one-time historical confirmation is completed")
    freeze=load_json(a.stage3c/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.json")
    primary=pd.read_csv(a.processed/"ame2020_primary_precision.csv")
    broad=pd.read_csv(a.processed/"ame2020_broad_measured.csv")
    light=pd.read_csv(a.processed/"ame2020_light_stress.csv")
    splits=make_regime_splits(primary,light)
    add_magic_pm2(primary,splits)
    broad_s=make_regime_splits(broad,None); add_magic_pm2(broad,broad_s)
    for k,v in broad_s.items(): splits[k+"_broad"]=v
    if a.smoke:
        keep={"R0_random","R1_Sn","R2_neutron_rich","R4_magic_pm1","R7_light_random","R0_random_broad"}
        splits={k:v for k,v in splits.items() if k in keep}
    bwn_allowed=False
    if a.stage3d and (a.stage3d/"BWN_REPRODUCTION_GATE.json").exists(): bwn_allowed=load_json(a.stage3d/"BWN_REPRODUCTION_GATE.json").get("status")=="PASS"
    all_pred=[]; b=[]; o=[]; fits=[]
    for name,(tr,te) in splits.items():
        print("evaluating",name,"train",len(tr),"test",len(te))
        p,br,orows,fit=evaluate_regime(name,tr,te,freeze,bwn_allowed,a.smoke)
        if p is None: continue
        all_pred.append(p); b+=br; o+=orows; fits.append(fit)
    pred=pd.concat(all_pred,ignore_index=True) if all_pred else pd.DataFrame(); pred.to_csv(a.out/"STRUCTURED_PREDICTIONS.csv",index=False)
    bdf=pd.DataFrame(b); bdf.to_csv(a.out/"STRUCTURED_B_METRICS.csv",index=False)
    odf=pd.DataFrame(o); odf.to_csv(a.out/"STRUCTURED_OBSERVABLE_METRICS.csv",index=False)
    # Observable-specific G from paired method MAEs, matching data-only family to each physics-guided integration.
    trust=[]
    if not odf.empty:
        for (reg,fam),grp in bdf[bdf.family.isin(["ridge","hgb","mlp"])].groupby(["regime","family"]):
            pass
        for reg in odf.regime.unique():
            rg=odf[odf.regime==reg]
            for fam in ["ridge","hgb","mlp"]:
                data_method=f"B_{fam}_data"
                for mech in ["soft","residual","adaptive"]:
                    guided=f"B_{fam}_{mech}"
                    for obs in ["Sn","S2n","Sp","S2p","Qalpha","delta2n","delta2p"]:
                        arow=rg[(rg.method==data_method)&(rg.observable==obs)]
                        grow=rg[(rg.method==guided)&(rg.observable==obs)]
                        if len(arow)==1 and len(grow)==1 and arow.iloc[0].n>0 and grow.iloc[0].mae and np.isfinite(grow.iloc[0].mae):
                            trust.append({"regime":reg,"family":fam,"mechanism":mech,"observable":obs,"n":int(min(arow.iloc[0].n,grow.iloc[0].n)),"G":float(arow.iloc[0].mae/grow.iloc[0].mae)})
    pd.DataFrame(trust).to_csv(a.out/"STRUCTURED_OBSERVABLE_TRUST_G.csv",index=False)
    write_json({"stage":"3F","status":"PASS","regimes_evaluated":sorted(pred.regime.unique().tolist()) if not pred.empty else [],"bwn_allowed":bwn_allowed,"smoke_mode":bool(a.smoke),"fit_diagnostics":fits},a.out/"STAGE3F_STATUS_AND_FITS.json")
    print("STAGE 3F: PASS",len(splits),"requested regimes")

if __name__=="__main__": main()
