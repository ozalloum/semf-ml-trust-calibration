#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from common import (
    MLP_SEEDS, bootstrap_semf, chain_block_bootstrap, ensemble_mean, family_predictions,
    fit_semf, make_regime_splits, metrics, paired_bootstrap, semf_design, semf_predict,
    write_json
)
from bwn import fit_bwn, predict_bwn

CORE_MISSPEC=["R0_random","R1_Ca","R1_Sn","R2_neutron_rich","R3_proton_rich","R4_magic_pm1"]
BWN_SHELL_CORE={"R0_random","R1_Sn","R4_magic_pm1"}
COEFS=["a_v","a_s","a_c","a_a","a_p"]


def loadj(p): return json.loads(Path(p).read_text(encoding="utf-8"))


def boot_samples(df,n_boot,seed=20260913):
    d=df.dropna(subset=["B_total_MeV"]).reset_index(drop=True)
    X=semf_design(d,True); y=d.B_total_MeV.to_numpy(float); n=len(d)
    rng=np.random.default_rng(seed); out=np.empty((n_boot,5),float)
    for i in range(n_boot):
        ix=rng.integers(0,n,size=n); out[i]=np.linalg.lstsq(X[ix],y[ix],rcond=None)[0]
    return out


def pred_with_coef(df,coef):
    return semf_design(df,True)@np.asarray(coef,float)


def coef_vec(fit): return np.array([fit["coef"][k] for k in COEFS],float)


def statistical_bootstraps(stage3e,stage3f,n_boot,smoke):
    rows=[]; blocks=[]
    files=[]
    cp=stage3e/"CONFIRMATION_PREDICTIONS.csv"
    if cp.exists(): files.append(("R5_historical_confirmation",pd.read_csv(cp)))
    sp=stage3f/"STRUCTURED_PREDICTIONS.csv"
    if sp.exists():
        sdf=pd.read_csv(sp)
        for reg,g in sdf.groupby("regime"): files.append((str(reg),g.copy()))
    for reg,g in files:
        y=g.B_true.to_numpy(float)
        for fam in ["ridge","hgb","mlp"]:
            dc=f"B_{fam}_data"
            if dc not in g: continue
            for mech in ["soft","residual","adaptive"]:
                gc=f"B_{fam}_{mech}"
                if gc not in g: continue
                r=paired_bootstrap(y,g[dc].to_numpy(float),g[gc].to_numpy(float),n_boot=n_boot,seed=20260911)
                rows.append({"regime":reg,"family":fam,"mechanism":mech,**r})
                if "Z" in g:
                    gg=g[["Z","B_true",dc,gc]].copy()
                    br=chain_block_bootstrap(gg,"B_true",dc,gc,n_boot=n_boot,seed=20260912)
                    blocks.append({"regime":reg,"family":fam,"mechanism":mech,**br})
    return rows,blocks


def main():
    ap=argparse.ArgumentParser(description="Stage 3G: uncertainty, misspecification, coefficient drift, and bootstrap inference")
    ap.add_argument("--processed",type=Path,required=True); ap.add_argument("--stage3c",type=Path,required=True)
    ap.add_argument("--stage3d",type=Path); ap.add_argument("--stage3e",type=Path,required=True); ap.add_argument("--stage3f",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True); ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    freeze=loadj(a.stage3c/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.json")
    nboot=150 if a.smoke else 5000; njoint=40 if a.smoke else 1000

    # 11. Statistical uncertainty for every primary family/mechanism comparison.
    pr,br=statistical_bootstraps(a.stage3e,a.stage3f,nboot,a.smoke)
    pd.DataFrame(pr).to_json(a.out/"PAIRED_BOOTSTRAP_PRIMARY_COMPARISONS.jsonl",orient="records",lines=True)
    pd.DataFrame(br).to_json(a.out/"CHAIN_BLOCK_BOOTSTRAP_SENSITIVITY.jsonl",orient="records",lines=True)

    # A3 chronological fits, coefficient uncertainty, drift and calibration-domain sensitivity.
    chrono={}; domain_rows=[]; samples={}
    for v in [2012,2016,2020]:
        prim=pd.read_csv(a.processed/f"ame{v}_primary_precision.csv"); broad=pd.read_csv(a.processed/f"ame{v}_broad_measured.csv")
        fit=fit_semf(prim); bs=boot_samples(prim,nboot,20260913+v); samples[v]=bs
        boot={"names":COEFS,"mean":dict(zip(COEFS,bs.mean(0).tolist())),"sd":dict(zip(COEFS,bs.std(0,ddof=1).tolist())),"ci95":{k:list(map(float,q)) for k,q in zip(COEFS,np.quantile(bs,[.025,.975],axis=0).T)},"covariance":np.cov(bs,rowvar=False).tolist(),"correlation":np.corrcoef(bs,rowvar=False).tolist()}
        chrono[v]={"fit":fit,"bootstrap":boot}
        domains={"D0_primary":prim,"D1_A_ge_50":prim[prim.A>=50],"D2_broad_measured":broad,"D3_primary_precision":prim}
        for name,d in domains.items():
            if len(d)<20: continue
            f=fit_semf(d)
            domain_rows.append({"vintage":v,"domain":name,"n":len(d),**f["coef"],"condition_number":f["condition_number"],"rank":f["rank"]})
    drifts=[]
    for old,new in [(2012,2016),(2016,2020)]:
        vo=coef_vec(chrono[old]["fit"]); vn=coef_vec(chrono[new]["fit"]); diff=vn-vo
        cov=np.array(chrono[old]["bootstrap"]["covariance"],float); inv=np.linalg.pinv(cov); md=float(np.sqrt(max(0,diff@inv@diff)))
        sd=np.array([chrono[old]["bootstrap"]["sd"][k] for k in COEFS])
        for i,k in enumerate(COEFS):
            drifts.append({"old":old,"new":new,"coefficient":k,"old_value":vo[i],"new_value":vn[i],"absolute_change":diff[i],"fractional_change":diff[i]/vo[i] if vo[i] else np.nan,"change_in_old_bootstrap_sd":diff[i]/sd[i] if sd[i] else np.nan,"vector_mahalanobis_distance":md})
    write_json({"stage":"3G","n_bootstrap":nboot,"chronological":chrono},a.out/"SEMF_CHRONOLOGICAL_COEFFICIENTS_AND_BOOTSTRAP.json")
    pd.DataFrame(drifts).to_csv(a.out/"SEMF_COEFFICIENT_DRIFT.csv",index=False)
    pd.DataFrame(domain_rows).to_csv(a.out/"SEMF_CALIBRATION_DOMAIN_SENSITIVITY.csv",index=False)

    # Mechanistic misspecification map on frozen structured regimes.
    primary=pd.read_csv(a.processed/"ame2020_primary_precision.csv"); splits=make_regime_splits(primary,None)
    pred_all=pd.read_csv(a.stage3f/"STRUCTURED_PREDICTIONS.csv")
    bwn_pass=False
    if a.stage3d and (a.stage3d/"BWN_REPRODUCTION_GATE.json").exists(): bwn_pass=loadj(a.stage3d/"BWN_REPRODUCTION_GATE.json").get("status")=="PASS"
    miss=[]; joint=[]; form=[]
    regimes=["R0_random","R1_Sn"] if a.smoke else CORE_MISSPEC
    for reg in regimes:
        if reg not in splits: continue
        tr,te=splits[reg]
        if len(te)<2 or len(tr)<30: continue
        fit=fit_semf(tr); c0=coef_vec(fit); bs=boot_samples(tr,nboot,20260913); sd=bs.std(0,ddof=1); cov=np.cov(bs,rowvar=False)
        y=te.B_total_MeV.to_numpy(float); p0=pred_with_coef(te,c0)
        rp=pred_all[pred_all.regime==reg].sort_values(["N","Z"]); te2=te.sort_values(["N","Z"])
        # Merge to guarantee identical order to frozen structured prediction table.
        keys=te2[["N","Z","B_total_MeV"]].merge(rp,on=["N","Z"],how="inner")
        if len(keys)==0:
            continue
        y2=keys.B_total_MeV.to_numpy(float)
        ridge_data=keys.B_ridge_data.to_numpy(float); ridge_cfg=freeze["selected"]["ridge"]["config"]; ridge_lam=float(freeze["selected"]["ridge"]["soft_prior_lambda"])
        # Full coefficient-specific map for transparent ridge.
        for j,k in enumerate(COEFS):
            for mult in [-2,-1,1,2]:
                c=c0.copy(); c[j]+=mult*sd[j]
                pp=pred_with_coef(keys,c)
                soft=(1-ridge_lam)*ridge_data+ridge_lam*pp
                # Residual repair is refit against the perturbed physics prior.
                pptr=pred_with_coef(tr,c)
                rr=ensemble_mean(family_predictions("ridge",ridge_cfg,tr,keys,residual_base_train=pptr,residual_base_test=pp,seeds=[-1]))
                dm=metrics(y2,ridge_data)["mae"]
                miss.append({"regime":reg,"coefficient":k,"sigma_multiple":mult,"physics_mae":metrics(y2,pp)["mae"],"data_mae":dm,"soft_mae":metrics(y2,soft)["mae"],"residual_mae":metrics(y2,rr)["mae"],"G_soft":dm/metrics(y2,soft)["mae"],"G_residual":dm/metrics(y2,rr)["mae"]})
        # No-pairing model-form control for all architectures.
        npfit=fit_semf(tr,include_pairing=False); npphys=semf_predict(keys,npfit,include_pairing=False); nptrain=semf_predict(tr,npfit,include_pairing=False)
        for fam in ["ridge","hgb","mlp"]:
            dc=f"B_{fam}_data"
            if dc not in keys: continue
            data=keys[dc].to_numpy(float); lam=float(freeze["selected"][fam]["soft_prior_lambda"]); cfg=freeze["selected"][fam]["config"]
            soft=(1-lam)*data+lam*npphys
            use_seeds=MLP_SEEDS[:1] if (a.smoke and fam=="mlp") else (MLP_SEEDS if fam=="mlp" else [-1])
            rr=ensemble_mean(family_predictions(fam,cfg,tr,keys,residual_base_train=nptrain,residual_base_test=npphys,seeds=use_seeds))
            dmae=metrics(y2,data)["mae"]
            form.append({"regime":reg,"family":fam,"control":"P0_no_pairing","data_mae":dmae,"physics_mae":metrics(y2,npphys)["mae"],"soft_mae":metrics(y2,soft)["mae"],"residual_mae":metrics(y2,rr)["mae"],"G_soft":dmae/metrics(y2,soft)["mae"],"G_residual":dmae/metrics(y2,rr)["mae"]})
        # Correlated joint coefficient draws: soft-prior distributions for all families.
        rng=np.random.default_rng(20260931)
        draws=rng.multivariate_normal(c0,cov,size=njoint,check_valid="warn")
        for fam in ["ridge","hgb","mlp"]:
            dc=f"B_{fam}_data"; data=keys[dc].to_numpy(float); dm=metrics(y2,data)["mae"]; lam=float(freeze["selected"][fam]["soft_prior_lambda"])
            gs=[]
            for c in draws:
                pp=pred_with_coef(keys,c); soft=(1-lam)*data+lam*pp; sm=metrics(y2,soft)["mae"]; gs.append(dm/sm if sm else np.nan)
            joint.append({"regime":reg,"family":fam,"n_draws":njoint,"G_median":float(np.nanmedian(gs)),"G_q025":float(np.nanquantile(gs,.025)),"G_q975":float(np.nanquantile(gs,.975)),"fraction_G_gt1":float(np.nanmean(np.asarray(gs)>1))})
        if bwn_pass and reg in BWN_SHELL_CORE and not a.smoke:
            bf=fit_bwn(tr); bp=predict_bwn(keys,bf["params"]); suppressed=copy.deepcopy(bf["params"]); suppressed["e_m1"]=0.0; bsp=predict_bwn(keys,suppressed)
            form.append({"regime":reg,"family":"BWN","control":"shell_suppressed_e_m1_0","nominal_mae":metrics(y2,bp)["mae"],"suppressed_mae":metrics(y2,bsp)["mae"],"delta_mae":metrics(y2,bsp)["mae"]-metrics(y2,bp)["mae"]})
    pd.DataFrame(miss).to_csv(a.out/"P0_COEFFICIENT_SPECIFIC_MISSPECIFICATION.csv",index=False)
    pd.DataFrame(joint).to_csv(a.out/"P0_CORRELATED_JOINT_TRUST.csv",index=False)
    pd.DataFrame(form).to_csv(a.out/"MODEL_FORM_MISSPECIFICATION.csv",index=False)
    write_json({"stage":"3G","status":"PASS","bootstrap_refits":nboot,"correlated_draws":njoint,"bwn_shell_control_enabled":bwn_pass,"smoke_mode":bool(a.smoke)},a.out/"STAGE3G_STATUS.json")
    print("STAGE 3G: PASS")

if __name__=="__main__": main()
