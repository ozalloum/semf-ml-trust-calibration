#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

STYLES=[
    {"color":"#1f77b4","linestyle":"-","marker":"o"},
    {"color":"#d62728","linestyle":"--","marker":"s"},
    {"color":"#2ca02c","linestyle":"-.","marker":"^"},
    {"color":"#9467bd","linestyle":":","marker":"D"},
    {"color":"#ff7f0e","linestyle":"--","marker":"v"},
    {"color":"#17becf","linestyle":"-.","marker":"P"},
    {"color":"#8c564b","linestyle":":","marker":"X"},
]


def savefig(fig,path):
    path.parent.mkdir(parents=True,exist_ok=True); fig.tight_layout(); fig.savefig(path,dpi=300,bbox_inches="tight"); fig.savefig(path.with_suffix(".pdf"),bbox_inches="tight"); plt.close(fig)


def label_smoke(ax,smoke):
    if smoke: ax.text(.5,.5,"SYNTHETIC SMOKE TEST - NOT EMPIRICAL",transform=ax.transAxes,ha="center",va="center",rotation=24,fontsize=13,alpha=.18)


def fig_trust(stage3f,out,smoke):
    p=stage3f/"STRUCTURED_B_METRICS.csv"
    if not p.exists(): return
    d=pd.read_csv(p); d=d[(d.family.isin(["ridge","hgb","mlp"]))&(d.mechanism.isin(["soft","residual"]))&d.G_vs_data_MAE.notna()]
    regs=[r for r in d.regime.unique() if not str(r).endswith("_broad")]
    if not regs:return
    fig,ax=plt.subplots(figsize=(9,5.4)); x=np.arange(len(regs)); i=0
    for fam in ["ridge","hgb","mlp"]:
        for mech in ["soft","residual"]:
            vals=[]
            for r in regs:
                q=d[(d.regime==r)&(d.family==fam)&(d.mechanism==mech)]
                vals.append(q.G_vs_data_MAE.iloc[0] if len(q) else np.nan)
            st=STYLES[i%len(STYLES)]; ax.plot(x,vals,label=f"{fam} - {mech}",linewidth=1.7,markersize=5,**st); i+=1
    ax.axhline(1,color="black",linewidth=1,alpha=.55); ax.set_ylabel("G = MAE(data-only) / MAE(physics-guided)"); ax.set_xlabel("Frozen evaluation regime")
    ax.set_xticks(x); ax.set_xticklabels([r.replace("_"," ") for r in regs],rotation=35,ha="right"); ax.legend(fontsize=8,ncol=2); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig1_BindingEnergy_Trust_by_Regime.png")


def fig_observable(stage3f,out,smoke):
    p=stage3f/"STRUCTURED_OBSERVABLE_TRUST_G.csv"
    if not p.exists(): return
    d=pd.read_csv(p); reg="R1_Sn" if "R1_Sn" in set(d.regime) else (d.regime.iloc[0] if len(d) else None)
    if reg is None:return
    obs=["Sn","S2n","Sp","S2p","delta2n","delta2p"]
    fig,ax=plt.subplots(figsize=(8.4,5.0)); x=np.arange(len(obs)); i=0
    for mech in ["soft","residual","adaptive"]:
        vals=[]
        for o in obs:
            q=d[(d.regime==reg)&(d.family=="ridge")&(d.mechanism==mech)&(d.observable==o)]
            vals.append(q.G.iloc[0] if len(q) else np.nan)
        st=STYLES[i]; ax.plot(x,vals,label=mech,linewidth=1.8,markersize=6,**st); i+=1
    ax.axhline(1,color="black",linewidth=1,alpha=.55); ax.set_ylabel("Observable-specific G"); ax.set_xlabel("Derived observable (strict out-of-sample rule)")
    ax.set_xticks(x); ax.set_xticklabels(obs); ax.legend(); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig2_Observable_Dependent_Trust.png")


def fig_sn(stage3f,out,smoke):
    p=stage3f/"STRUCTURED_PREDICTIONS.csv"
    if not p.exists(): return
    d=pd.read_csv(p); d=d[d.regime=="R1_Sn"].sort_values("N")
    if len(d)<3:return
    methods=[("B_semf","SEMF"),("B_ridge_data","ridge data-only"),("B_ridge_soft","ridge soft prior"),("B_ridge_residual","ridge residual repair")]
    fig,ax=plt.subplots(figsize=(8.5,5.0));
    for i,(c,lbl) in enumerate(methods):
        if c in d: ax.plot(d.N,d[c]-d.B_true,label=lbl,linewidth=1.7,markersize=4,**STYLES[i])
    ax.axhline(0,color="black",linewidth=1,alpha=.55); ax.axvline(82,color="black",linestyle="--",linewidth=1,alpha=.45); ax.set_xlabel("Neutron number N"); ax.set_ylabel("Binding-energy residual (MeV)"); ax.legend(fontsize=8); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig3a_Sn_Chain_Binding_Residuals.png")
    # S2n from whole-chain held-out predictions.
    q=d.set_index("N"); ns=sorted(set(q.index)&set(q.index+2))
    if ns:
        fig,ax=plt.subplots(figsize=(8.5,5.0));
        truth=[]; nvals=[]
        for n in sorted(q.index):
            if n-2 in q.index: nvals.append(n); truth.append(q.loc[n,"B_true"]-q.loc[n-2,"B_true"])
        ax.plot(nvals,truth,label="experimental",linewidth=2,markersize=5,**STYLES[0])
        for i,(c,lbl) in enumerate(methods[0:4],start=1):
            if c not in q: continue
            vals=[]
            for n in nvals: vals.append(q.loc[n,c]-q.loc[n-2,c])
            ax.plot(nvals,vals,label=lbl,linewidth=1.5,markersize=4,**STYLES[i])
        ax.axvline(82,color="black",linestyle="--",linewidth=1,alpha=.45); ax.set_xlabel("Neutron number N"); ax.set_ylabel("S2n (MeV)"); ax.legend(fontsize=8); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig3b_Sn_Chain_S2n.png")


def fig_light(stage3f,out,smoke):
    p=stage3f/"STRUCTURED_PREDICTIONS.csv"
    if not p.exists():return
    d=pd.read_csv(p); d=d[d.regime=="R7_light_random"].copy()
    if len(d)==0:return
    d["stratum"]=pd.cut(d.A,bins=[-np.inf,19,39,np.inf],labels=["A<20","20<=A<40","A>=40"])
    methods=[("B_semf","SEMF"),("B_ridge_data","data-only"),("B_ridge_soft","soft prior"),("B_ridge_residual","residual repair")]
    fig,ax=plt.subplots(figsize=(7.8,4.8)); x=np.arange(3)
    for i,(c,lbl) in enumerate(methods):
        vals=[]
        for s in ["A<20","20<=A<40","A>=40"]:
            q=d[d.stratum.astype(str)==s]; vals.append(np.mean(np.abs(q[c]-q.B_true)) if len(q) and c in q else np.nan)
        ax.plot(x,vals,label=lbl,linewidth=1.7,markersize=6,**STYLES[i])
    ax.set_xticks(x); ax.set_xticklabels(["A<20","20<=A<40","A>=40"]); ax.set_ylabel("MAE in held-out R7 stratum (MeV)"); ax.set_xlabel("Predeclared mass-number stratum"); ax.legend(fontsize=8); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig4_Light_Nucleus_Stress.png")


def fig_coeff(stage3g,out,smoke):
    p=stage3g/"SEMF_CHRONOLOGICAL_COEFFICIENTS_AND_BOOTSTRAP.json"
    if not p.exists():return
    j=json.loads(p.read_text()); chron=j["chronological"]; years=["2012","2016","2020"]; names=["a_v","a_s","a_c","a_a","a_p"]
    fig,ax=plt.subplots(figsize=(8.0,5.0)); x=np.arange(3)
    for i,n in enumerate(names):
        vals=np.array([chron[y]["fit"]["coef"][n] for y in years],float); base=vals[0] if vals[0]!=0 else 1.; rel=vals/base
        ci=[]
        for y,v in zip(years,vals):
            q=chron[y]["bootstrap"]["ci95"][n]; ci.append([(v-q[0])/abs(base),(q[1]-v)/abs(base)])
        err=np.array(ci).T
        st=STYLES[i]; ax.errorbar(x,rel,yerr=err,label=n,linewidth=1.6,markersize=6,capsize=3,**st)
    ax.axhline(1,color="black",linewidth=1,alpha=.5); ax.set_xticks(x); ax.set_xticklabels(years); ax.set_ylabel("Coefficient / AME2012 coefficient"); ax.set_xlabel("AME vintage"); ax.legend(ncol=3,fontsize=8); ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig5_SEMF_Coefficient_Evolution.png")
    corr=np.array(chron["2020"]["bootstrap"]["correlation"],float)
    fig,ax=plt.subplots(figsize=(5.7,5.0)); im=ax.imshow(corr,vmin=-1,vmax=1,cmap="coolwarm"); ax.set_xticks(range(5));ax.set_xticklabels(names);ax.set_yticks(range(5));ax.set_yticklabels(names);fig.colorbar(im,ax=ax,label="Bootstrap correlation"); label_smoke(ax,smoke); savefig(fig,out/"Fig6_SEMF_Coefficient_Correlation.png")


def fig_misspec(stage3g,out,smoke):
    p=stage3g/"P0_COEFFICIENT_SPECIFIC_MISSPECIFICATION.csv"
    if not p.exists():return
    d=pd.read_csv(p); reg="R4_magic_pm1" if "R4_magic_pm1" in set(d.regime) else (d.regime.iloc[0] if len(d) else None)
    if reg is None:return
    q=d[d.regime==reg]; fig,ax=plt.subplots(figsize=(8.2,5.0));
    for i,c in enumerate(["a_v","a_s","a_c","a_a","a_p"]):
        g=q[q.coefficient==c].sort_values("sigma_multiple");
        if len(g): ax.plot(g.sigma_multiple,g.G_soft,label=c,linewidth=1.7,markersize=6,**STYLES[i])
    ax.axhline(1,color="black",linewidth=1,alpha=.5); ax.set_xlabel("One-at-a-time coefficient perturbation (bootstrap SD)"); ax.set_ylabel("G for fixed soft prior vs data-only"); ax.legend(ncol=3,fontsize=8);ax.grid(alpha=.18); label_smoke(ax,smoke); savefig(fig,out/"Fig7_Term_Specific_Physics_Trust.png")


def write_manuscript(stage3c,stage3d,stage3e,stage3f,stage3g,out,smoke):
    freeze=json.loads((stage3c/"FROZEN_CONFIGURATION_PRE_CONFIRMATION.json").read_text())
    conf=json.loads((stage3e/"CONFIRMATION_RESULTS.json").read_text()) if (stage3e/"CONFIRMATION_RESULTS.json").exists() else {}
    disclaimer="**SYNTHETIC SMOKE-TEST DOCUMENT - NOT EMPIRICAL AME RESULTS.**\n\n" if smoke else ""
    title="When Should Machine Learning Trust the Semi-Empirical Mass Formula?"
    lines=[f"# {title}","## Physics-prior fidelity, integration mechanism, observables, and extrapolation across the nuclear chart","",disclaimer,
           "## Abstract", "This study asks when an interpretable but approximate nuclear-physics prior improves machine-learning prediction and when it becomes harmful. The design separates development from confirmation, interrogates prior fidelity through coefficient uncertainty and model-form controls, and evaluates bulk binding energy together with local separation and shell-sensitive observables. The primary prior is the five-term semi-empirical mass formula (SEMF); a shell-aware BWN formula is admitted only after an independent published-result reproduction gate. A fixed AME2012-to-AME2016 transition is used for development and the AME2016-to-AME2020 newly measured set is reserved for one-time confirmation. Structured whole-chain, frontier, magic-region, isotone, and light-nucleus holdouts then test where physics trust changes across the nuclear chart. " + ("The numerical values in this draft are synthetic pipeline validation only and are intentionally not interpreted as nuclear-mass evidence." if smoke else "Empirical numerical conclusions are generated only after every frozen data and confirmation gate passes."),"",
           "## 1. Introduction", "Nuclear mass prediction is a natural setting for studying physics-guided machine learning because approximate physical models are simultaneously useful, interpretable, and incomplete. A liquid-drop SEMF captures smooth bulk trends, while shell, pairing, deformation, and other correlations generate structured local deviations. The central question is therefore not whether ML can reduce a mass-model residual, but how strongly an ML system should trust an approximate prior as prior fidelity, extrapolation difficulty, nuclear-chart region, observable, and integration mechanism change.","",
           "A key distinction in this paper is between bulk numerical agreement and structural fidelity. Separation energies and shell-gap indicators probe local changes in the mass surface and can expose shell structure even when total binding-energy errors appear modest. The empirical protocol therefore evaluates B, B/A, Sn, S2n, Sp, S2p, Qalpha where support permits, and two-nucleon shell-gap indicators under a strict out-of-sample-neighbor rule.","",
           "## 2. Frozen methods","### 2.1 Data chronology and leakage control","AME2012->AME2016 is the only development historical transition. Hyperparameters, fixed soft-prior weights, adaptive-gate complexity, and numerical tolerances are frozen there. AME2016->AME2020 newly measured primary nuclei are scored once. After that confirmation is closed, structured AME2020 holdouts may be analyzed without redesigning the historical model.","",
           "### 2.2 Physics priors","P0 is the standard five-term SEMF, with all coefficients fit on each regime training set only. P1 is the 2025 shell-aware BWN form, which is used only if its published AME2020 Z,N>=8 binding-energy RMS of 0.887 MeV is reproduced within 0.02 MeV. BWN historical results are retrospective stress tests because the formula form post-dates AME2020.","",
           "### 2.3 Machine-learning comparators and integration","Three deliberately compact ML families are used: fifth-degree polynomial ridge, histogram gradient boosting, and a compact MLP. They are compared as data-only prediction, fixed soft blending with physics, residual repair, and a low-complexity adaptive trust gate. An oracle blend is diagnostic only.","",
           "### 2.4 Evaluation regimes","The frozen regimes are random interpolation, whole Ca/Sn chains with Ni/Pb transfer chains, neutron-rich and proton-rich frontiers, magic-region bands, the historical transition, N=50/82/126 isotones, and a supplementary light-nucleus stress population.","",
           "### 2.5 Statistical analysis","Primary comparisons use paired nucleus bootstraps and dependence-aware chain-block bootstraps. SEMF parameter uncertainty uses 5000 bootstrap refits with the full coefficient covariance retained. Misspecification includes coefficient-specific +/-1 and +/-2 bootstrap-SD perturbations, correlated joint draws, no-pairing, shell-aware comparison, shell suppression, calibration-domain shifts, and AME-vintage coefficient drift.","",
           "## 3. Frozen development configuration"]
    for fam,s in freeze["selected"].items():
        lines.append(f"- **{fam}:** config `{json.dumps(s['config'],sort_keys=True)}`; lambda={s['soft_prior_lambda']}; adaptive gate alpha={s['adaptive_gate_alpha']}.")
    lines += ["","## 4. Results"]
    if smoke:
        lines += ["The end-to-end software chain was executed on a generated synthetic nuclear chart solely as a smoke test. Stage 3C froze development settings, Stage 3D correctly blocked the BWN published-data reproduction gate on synthetic data, Stage 3E enforced a one-time confirmation lock, and Stages 3F-3G completed structured holdouts and uncertainty/misspecification calculations. These values are excluded from scientific interpretation."]
    else:
        lines += ["Empirical results are inserted automatically from the locked result tables after the data gates pass. The manuscript generator does not create prose claims from absent or incomplete stages."]
        if conf:
            for fam,s in conf.get("families",{}).items():
                lines.append(f"- Historical confirmation {fam}: data MAE={s['data_only']['mae']:.4f} MeV; soft G={s['G_soft']:.3f}; residual G={s['G_residual']:.3f}; adaptive G={s['G_adaptive']:.3f}.")
    lines += ["","## 5. Discussion framework","The discussion is organized around five questions: whether physics helps more in interpolation or extrapolation; whether the answer changes near shell closures; whether bulk and local observables disagree; whether residual repair is more robust than direct soft blending under prior misspecification; and whether apparent prior error can be attributed to coefficient uncertainty/calibration drift rather than missing model form.","",
              "The paper does not interpret SEMF fit coefficients as precise nuclear-matter constants. It also does not claim a universal trust threshold, a new state-of-the-art mass model, or prospective performance for formula forms developed with later AME knowledge.","",
              "## 6. Reproducibility","The release package contains frozen protocols, code, data-gate logic, stage locks, synthetic smoke tests, figure generation, manifests, and checksums. Empirical release status is conditional on official AME acquisition/provenance and the independent spot-check gate.","",
              "## Figure inventory","1. Binding-energy trust by regime. 2. Observable-dependent trust. 3a-b. Out-of-sample Sn-chain bulk and S2n behavior. 4. Light-nucleus stress. 5. SEMF coefficient evolution. 6. Bootstrap coefficient correlation. 7. Coefficient-specific trust sensitivity.","",
              "## References to anchor final bibliography","- W. J. Huang et al., Chinese Physics C 45, 030002 (2021).","- M. Wang et al., Chinese Physics C 45, 030003 (2021).","- Wu et al., Chinese Physics C 49, 114103 (2025), with erratum 49, 129001.","- M. Hein, A. Pusch, and S. Heusler, European Journal of Physics 43, 035801 (2022).","- P. Cappellaro, Introduction to Applied Nuclear Physics, MIT OpenCourseWare / LibreTexts."]
    (out/"Paper3_Development_Manuscript.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    ap=argparse.ArgumentParser();
    for n in ["stage3c","stage3d","stage3e","stage3f","stage3g"]: ap.add_argument("--"+n,type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True); ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True); figs=a.out/"figures"; figs.mkdir(exist_ok=True)
    fig_trust(a.stage3f,figs,a.smoke); fig_observable(a.stage3f,figs,a.smoke); fig_sn(a.stage3f,figs,a.smoke); fig_light(a.stage3f,figs,a.smoke); fig_coeff(a.stage3g,figs,a.smoke); fig_misspec(a.stage3g,figs,a.smoke)
    write_manuscript(a.stage3c,a.stage3d,a.stage3e,a.stage3f,a.stage3g,a.out,a.smoke)
    (a.out/"FIGURE_STYLE_RULE.txt").write_text("Every multi-series line plot uses a distinct combination of color, line style, and marker shape.\n")
    print("STAGE 3H: PASS - figures and development manuscript generated")
if __name__=="__main__": main()
