#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from common import ensure_features, fit_semf, make_regime_splits, metrics, semf_design, derived_from_predictions, write_json

TERM_NAMES=["volume","surface","coulomb","asymmetry","pairing"]
COEF_NAMES=["a_v","a_s","a_c","a_a","a_p"]


def add_magic_pm2(d, splits, suffix=""):
    mZ=np.min(np.abs(d.Z.to_numpy()[:,None]-np.array([20,28,50,82])[None,:]),axis=1)<=2
    mN=np.min(np.abs(d.N.to_numpy()[:,None]-np.array([20,28,50,82,126])[None,:]),axis=1)<=2
    mask=mZ|mN
    splits["R4_magic_pm2"+suffix]=(d.loc[~mask].copy(),d.loc[mask].copy())


def all_splits(processed:Path):
    primary=pd.read_csv(processed/"ame2020_primary_precision.csv")
    broad=pd.read_csv(processed/"ame2020_broad_measured.csv")
    light=pd.read_csv(processed/"ame2020_light_stress.csv")
    splits=make_regime_splits(primary,light); add_magic_pm2(primary,splits)
    bs=make_regime_splits(broad,None); add_magic_pm2(broad,bs)
    for k,v in bs.items(): splits[k+"_broad"]=v
    return splits


def m_ba(y,p,A):
    return metrics(np.asarray(y,float)/np.asarray(A,float),np.asarray(p,float)/np.asarray(A,float))


def ba_trust(stage3f:Path):
    p=pd.read_csv(stage3f/"STRUCTURED_PREDICTIONS.csv")
    rows=[]
    for reg,g in p.groupby("regime"):
        y=g.B_true.to_numpy(float); A=g.A.to_numpy(float)
        # physics-only error
        if "B_semf" in g:
            mm=m_ba(y,g.B_semf,A); rows.append({"regime":reg,"family":"physics","mechanism":"physics_only","observable":"B/A",**mm})
        if "B_bwn" in g:
            mm=m_ba(y,g.B_bwn,A); rows.append({"regime":reg,"family":"BWN","mechanism":"physics_only_shell_aware","observable":"B/A",**mm})
        for fam in ["ridge","hgb","mlp"]:
            dc=f"B_{fam}_data"
            if dc not in g: continue
            dm=m_ba(y,g[dc],A)
            rows.append({"regime":reg,"family":fam,"mechanism":"data","observable":"B/A",**dm})
            for mech in ["soft","residual","adaptive"]:
                pc=f"B_{fam}_{mech}"
                if pc not in g: continue
                mm=m_ba(y,g[pc],A)
                row={"regime":reg,"family":fam,"mechanism":mech,"observable":"B/A",**mm}
                if mm["mae"]>0: row["G_vs_data_MAE"]=dm["mae"]/mm["mae"]
                rows.append(row)
    return pd.DataFrame(rows)


def historical_observable_rows(stage3c:Path,stage3e:Path):
    rows=[]
    specs=[("AME2012_to_AME2016_development",stage3c/"DEVELOPMENT_PREDICTIONS.csv"),
           ("AME2016_to_AME2020_confirmation",stage3e/"CONFIRMATION_PREDICTIONS.csv")]
    for transition,path in specs:
        d=pd.read_csv(path).copy(); d["is_test"]=True
        y=d.B_true.to_numpy(float); A=d.A.to_numpy(float)
        methods=[c for c in d.columns if c.startswith("B_") and c not in {"B_true"}]
        # B and BA method metrics, then G for family/mechanism pairs.
        by={}
        for c in methods:
            by[(c,"B")]=metrics(y,d[c].to_numpy(float))
            by[(c,"B/A")]=m_ba(y,d[c].to_numpy(float),A)
        truth=derived_from_predictions(d.rename(columns={"B_true":"Btmp"}),"Btmp","is_test")
        derived={}
        for c in methods:
            pred=derived_from_predictions(d.rename(columns={c:"Btmp"}),"Btmp","is_test")
            if truth.empty or pred.empty: continue
            merged=truth.merge(pred,on=["N","Z","A"],suffixes=("_true","_pred"))
            for o in ["Sn","S2n","Sp","S2p","Qalpha","delta2n","delta2p"]:
                a=merged[f"{o}_true"].to_numpy(float); b=merged[f"{o}_pred"].to_numpy(float)
                mask=np.isfinite(a)&np.isfinite(b)
                derived[(c,o)]=metrics(a[mask],b[mask]) if mask.any() else {"n":0,"mae":np.nan,"rmse":np.nan,"bias":np.nan}
        for fam in ["ridge","hgb","mlp"]:
            dc=f"B_{fam}_data"
            if dc not in d: continue
            for mech in ["soft","residual","adaptive"]:
                pc=f"B_{fam}_{mech}"
                if pc not in d: continue
                for o in ["B","B/A"]:
                    dm=by[(dc,o)]; pm=by[(pc,o)]
                    rows.append({"transition":transition,"family":fam,"mechanism":mech,"observable":o,
                                 "n":pm["n"],"data_mae":dm["mae"],"physics_guided_mae":pm["mae"],
                                 "G_vintage":dm["mae"]/pm["mae"] if pm["mae"] else np.nan})
                for o in ["Sn","S2n","Sp","S2p","Qalpha","delta2n","delta2p"]:
                    dm=derived.get((dc,o)); pm=derived.get((pc,o))
                    if dm is None or pm is None or not pm.get("n"):
                        rows.append({"transition":transition,"family":fam,"mechanism":mech,"observable":o,"n":0,"data_mae":np.nan,"physics_guided_mae":np.nan,"G_vintage":np.nan})
                    else:
                        rows.append({"transition":transition,"family":fam,"mechanism":mech,"observable":o,
                                     "n":int(pm["n"]),"data_mae":dm["mae"],"physics_guided_mae":pm["mae"],
                                     "G_vintage":dm["mae"]/pm["mae"] if pm["mae"] else np.nan})
    return pd.DataFrame(rows)


def fit_ablated(train,omit_idx):
    tr=ensure_features(train).dropna(subset=["B_total_MeV"]).copy()
    X=semf_design(tr,True); keep=[i for i in range(5) if i!=omit_idx]
    y=tr.B_total_MeV.to_numpy(float); coef,res,rank,sing=np.linalg.lstsq(X[:,keep],y,rcond=None)
    return {"keep":keep,"coef":coef,"rank":int(rank),"condition_number":float(np.linalg.cond(X[:,keep]))}


def pred_ablated(test,fit):
    return semf_design(test,True)[:,fit["keep"]]@fit["coef"]


def term_diagnostics(processed:Path):
    build=[]; removal=[]
    for reg,(train,test) in all_splits(processed).items():
        if len(test)<2 or len(train)<30: continue
        tr=ensure_features(train); te=ensure_features(test)
        full=fit_semf(tr); X=semf_design(te,True)
        c=np.array([full["coef"][k] for k in COEF_NAMES],float)
        y=te.B_total_MeV.to_numpy(float); A=te.A.to_numpy(float)
        cum=np.zeros(len(te),float)
        for i,t in enumerate(TERM_NAMES):
            cum=cum+X[:,i]*c[i]
            mb=metrics(y,cum); mba=m_ba(y,cum,A)
            build.append({"regime":reg,"stage_index":i+1,"cumulative_stage":"+".join(TERM_NAMES[:i+1]),
                          "n":len(te),"B_mae":mb["mae"],"B_rmse":mb["rmse"],"BA_mae":mba["mae"],"BA_rmse":mba["rmse"],
                          "fit_condition_number":full["condition_number"]})
        # Full SEMF and one-term removals with remaining coefficients refit on train.
        pf=X@c; mb=metrics(y,pf); mba=m_ba(y,pf,A)
        removal.append({"regime":reg,"model":"full","removed_term":"none","n":len(te),"B_mae":mb["mae"],"B_rmse":mb["rmse"],"BA_mae":mba["mae"],"BA_rmse":mba["rmse"],"rank":full["rank"],"condition_number":full["condition_number"]})
        for i,t in [(1,"surface"),(2,"coulomb"),(3,"asymmetry"),(4,"pairing")]:
            f=fit_ablated(tr,i); pp=pred_ablated(te,f); mb=metrics(y,pp); mba=m_ba(y,pp,A)
            removal.append({"regime":reg,"model":"term_removed_refit","removed_term":t,"n":len(te),"B_mae":mb["mae"],"B_rmse":mb["rmse"],"BA_mae":mba["mae"],"BA_rmse":mba["rmse"],"rank":f["rank"],"condition_number":f["condition_number"]})
    return pd.DataFrame(build),pd.DataFrame(removal)


def global_landscape(processed:Path):
    d=ensure_features(pd.read_csv(processed/"ame2020_primary_precision.csv"))
    fit=fit_semf(d); X=semf_design(d,True); c=np.array([fit["coef"][k] for k in COEF_NAMES],float)
    y=d.B_total_MeV.to_numpy(float); A=d.A.to_numpy(float); out=d[["N","Z","A","B_total_MeV"]].copy()
    cum=np.zeros(len(d),float)
    for i,t in enumerate(TERM_NAMES):
        cum=cum+X[:,i]*c[i]
        out[f"B_{i+1}_{t}"]=cum
        out[f"residual_B_{i+1}_{t}"]=y-cum
        out[f"residual_BA_{i+1}_{t}"]=(y-cum)/A
    out["is_magic_Z"]=out.Z.isin([20,28,50,82])
    out["is_magic_N"]=out.N.isin([20,28,50,82,126])
    return out,fit


def local_error_map(stage3f:Path):
    d=pd.read_csv(stage3f/"STRUCTURED_PREDICTIONS.csv"); d=d[d.regime=="R0_random"].copy(); d["is_test"]=True
    rows=[]
    for fam in ["hgb","mlp"]:
        dc=f"B_{fam}_data"
        for mech in ["soft","residual"]:
            pc=f"B_{fam}_{mech}"
            if dc not in d or pc not in d: continue
            for r in d.itertuples(index=False):
                rows.append({"regime":"R0_random","family":fam,"mechanism":mech,"observable":"B","N":int(r.N),"Z":int(r.Z),"A":int(r.A),
                             "paired_error_improvement":abs(getattr(r,dc)-r.B_true)-abs(getattr(r,pc)-r.B_true)})
                rows.append({"regime":"R0_random","family":fam,"mechanism":mech,"observable":"B/A","N":int(r.N),"Z":int(r.Z),"A":int(r.A),
                             "paired_error_improvement":abs((getattr(r,dc)-r.B_true)/r.A)-abs((getattr(r,pc)-r.B_true)/r.A)})
            truth=derived_from_predictions(d.rename(columns={"B_true":"Btmp"}),"Btmp","is_test")
            dd=derived_from_predictions(d.rename(columns={dc:"Btmp"}),"Btmp","is_test")
            pp=derived_from_predictions(d.rename(columns={pc:"Btmp"}),"Btmp","is_test")
            if not truth.empty and not dd.empty and not pp.empty:
                m=truth.merge(dd,on=["N","Z","A"],suffixes=("_true","_data")).merge(pp,on=["N","Z","A"])
                for o in ["S2n","delta2n"]:
                    for rr in m.itertuples(index=False):
                        tv=getattr(rr,f"{o}_true"); dv=getattr(rr,f"{o}_data"); pv=getattr(rr,o)
                        if pd.notna(tv) and pd.notna(dv) and pd.notna(pv):
                            rows.append({"regime":"R0_random","family":fam,"mechanism":mech,"observable":o,"N":int(rr.N),"Z":int(rr.Z),"A":int(rr.A),
                                         "paired_error_improvement":abs(float(dv)-float(tv))-abs(float(pv)-float(tv))})
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--processed",type=Path,required=True); ap.add_argument("--stage3c",type=Path,required=True); ap.add_argument("--stage3e",type=Path,required=True); ap.add_argument("--stage3f",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    ba=ba_trust(a.stage3f); ba.to_csv(a.out/"BA_TRUST_BY_REGIME.csv",index=False)
    hist=historical_observable_rows(a.stage3c,a.stage3e); hist.to_csv(a.out/"HISTORICAL_OBSERVABLE_TRUST.csv",index=False)
    build,rem=term_diagnostics(a.processed); build.to_csv(a.out/"SEMF_TERM_BUILDUP_METRICS.csv",index=False); rem.to_csv(a.out/"SEMF_TERM_REMOVAL_METRICS.csv",index=False)
    land,fit=global_landscape(a.processed); land.to_csv(a.out/"SEMF_TERM_LANDSCAPE_AME2020.csv",index=False)
    local=local_error_map(a.stage3f); local.to_csv(a.out/"LOCAL_PAIRED_ERROR_IMPROVEMENT_R0.csv",index=False)
    write_json({"stage":"3G.5","status":"PASS","purpose":"execution of already-predeclared A1-A3 diagnostics omitted from the original reporting script","n_BA_rows":len(ba),"n_historical_trust_rows":len(hist),"n_term_buildup_rows":len(build),"n_term_removal_rows":len(rem),"n_landscape_rows":len(land),"n_local_map_rows":len(local),"diagnostic_global_AME2020_semf_fit":fit,"confirmation_reopened":False},a.out/"STAGE3G5_STATUS.json")
    print("STAGE 3G.5: PASS",len(ba),len(hist),len(build),len(rem),len(land),len(local))
if __name__=="__main__": main()
