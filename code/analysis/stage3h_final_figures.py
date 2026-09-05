#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from common import derived_from_predictions

# Frozen user plot rule: every multi-series line differs in color + line style + marker.
STYLES=[
    dict(color='#1f77b4',linestyle='-',marker='o'),
    dict(color='#d62728',linestyle='--',marker='s'),
    dict(color='#2ca02c',linestyle='-.',marker='^'),
    dict(color='#9467bd',linestyle=':',marker='D'),
    dict(color='#ff7f0e',linestyle=(0,(5,1)),marker='v'),
    dict(color='#17becf',linestyle=(0,(3,1,1,1)),marker='P'),
    dict(color='#8c564b',linestyle=(0,(1,1)),marker='X'),
    dict(color='#e377c2',linestyle=(0,(7,2,1,2)),marker='*'),
]
REG_LABEL={
'R0_random':'Random','R1_Ca':'Ca chain','R1_Sn':'Sn chain','R1_Ni':'Ni chain','R1_Pb':'Pb chain',
'R2_neutron_rich':'Neutron-rich','R3_proton_rich':'Proton-rich','R4_magic_pm1':'Magic +/-1',
'R4_magic_pm2':'Magic +/-2','R6_N50':'N=50','R6_N82':'N=82','R6_N126':'N=126','R7_light_random':'Light stress'}
KEY_REGS=['R0_random','R1_Ca','R1_Sn','R1_Ni','R1_Pb','R2_neutron_rich','R3_proton_rich','R4_magic_pm1','R6_N50','R6_N82','R6_N126','R7_light_random']

def setup():
    plt.rcParams.update({
        'font.size':9.5,'axes.titlesize':10.5,'axes.labelsize':9.5,'legend.fontsize':8,
        'xtick.labelsize':8.5,'ytick.labelsize':8.5,'figure.dpi':120,'savefig.dpi':320,
        'axes.spines.top':False,'axes.spines.right':False,'axes.grid':False,
        'pdf.fonttype':42,'ps.fonttype':42,
    })

def save(fig,out,name):
    out.mkdir(parents=True,exist_ok=True)
    fig.tight_layout()
    fig.savefig(out/f'{name}.png',bbox_inches='tight')
    fig.savefig(out/f'{name}.pdf',bbox_inches='tight')
    plt.close(fig)

def get_conf(stage3e):
    return pd.read_csv(stage3e/'CONFIRMATION_PREDICTIONS.csv')

def fig1_confirmation(stage3e,out):
    d=get_conf(stage3e); y=d.B_true.to_numpy(float)
    semf=np.mean(np.abs(d.B_semf-y)); bwn=np.mean(np.abs(d.B_bwn_retrospective-y))
    fig,axs=plt.subplots(1,2,figsize=(9.3,3.9),sharey=True)
    for ax,fam,title in zip(axs,['hgb','mlp'],['Histogram gradient boosting','Compact MLP ensemble']):
        mechs=['data','soft','residual','adaptive']; vals=[]
        for m in mechs: vals.append(np.mean(np.abs(d[f'B_{fam}_{m}']-y)))
        bars=ax.bar(np.arange(4),vals,edgecolor='black',linewidth=.45)
        for i,b in enumerate(bars): b.set_hatch(['','//','xx','..'][i])
        ax.axhline(semf,color='#444444',linestyle='--',linewidth=1.3,label=f'SEMF = {semf:.3f} MeV')
        ax.axhline(bwn,color='#7f7f7f',linestyle=':',linewidth=1.3,label=f'BWN retrospective = {bwn:.3f} MeV')
        ax.set_xticks(range(4),['Data only','Soft prior','Residual repair','Adaptive'],rotation=18,ha='right')
        ax.set_title(title); ax.set_ylabel('MAE on 51 genuinely new AME2020 nuclei (MeV)')
        ax.set_ylim(0,max(vals)*1.14); ax.grid(axis='y',alpha=.18); ax.legend(frameon=False,fontsize=7.6)
        for i,v in enumerate(vals): ax.text(i,v+max(vals)*.025,f'{v:.3f}',ha='center',va='bottom',fontsize=7.5)
    save(fig,out,'Fig1_Historical_Confirmation_MAE')

def fig2_structured(stage3g,out):
    b=pd.read_json(stage3g/'PAIRED_BOOTSTRAP_PRIMARY_COMPARISONS.jsonl',lines=True)
    fig,axs=plt.subplots(2,1,figsize=(10.0,7.2),sharex=True)
    x=np.arange(len(KEY_REGS))
    for ax,fam,title in zip(axs,['hgb','mlp'],['HGB','MLP ensemble']):
        for j,mech in enumerate(['soft','residual']):
            vals=[]; lo=[]; hi=[]
            for r in KEY_REGS:
                q=b[(b.regime==r)&(b.family==fam)&(b.mechanism==mech)]
                if len(q):
                    v=float(q.G_a_over_b.iloc[0]); ci=q.G_ci95.iloc[0]; vals.append(v); lo.append(v-float(ci[0])); hi.append(float(ci[1])-v)
                else: vals.append(np.nan);lo.append(np.nan);hi.append(np.nan)
            st=STYLES[j]
            ax.errorbar(x,vals,yerr=np.array([lo,hi]),label=('Fixed soft prior' if mech=='soft' else 'Residual repair'),
                        capsize=2.2,linewidth=1.6,markersize=4.8,**st)
        ax.axhline(1,color='black',linewidth=1,alpha=.65); ax.set_ylabel('G for binding energy')
        ax.set_title(title); ax.grid(axis='y',alpha=.18); ax.legend(frameon=False,ncol=2)
    axs[-1].set_xticks(x,[REG_LABEL[r] for r in KEY_REGS],rotation=32,ha='right')
    axs[-1].set_xlabel('Predeclared structured holdout')
    save(fig,out,'Fig2_Structured_Trust_with_95CI')

def assemble_obs(stage3f,stage3g5,reg='R1_Sn'):
    derived=pd.read_csv(stage3f/'STRUCTURED_OBSERVABLE_TRUST_G.csv')
    ba=pd.read_csv(stage3g5/'BA_TRUST_BY_REGIME.csv')
    bm=pd.read_csv(stage3f/'STRUCTURED_B_METRICS.csv')
    rows=[]
    for fam in ['hgb','mlp']:
        dm=bm[(bm.regime==reg)&(bm.family==fam)&(bm.mechanism=='data')].iloc[0]
        for mech in ['soft','residual']:
            pm=bm[(bm.regime==reg)&(bm.family==fam)&(bm.mechanism==mech)].iloc[0]
            rows.append(dict(family=fam,mechanism=mech,observable='B',G=float(dm.mae/pm.mae),n=int(pm.n)))
            q=ba[(ba.regime==reg)&(ba.family==fam)&(ba.mechanism==mech)]
            rows.append(dict(family=fam,mechanism=mech,observable='B/A',G=float(q.G_vs_data_MAE.iloc[0]),n=int(q.n.iloc[0])))
            for o in ['Sn','S2n','delta2n']:
                q=derived[(derived.regime==reg)&(derived.family==fam)&(derived.mechanism==mech)&(derived.observable==o)]
                rows.append(dict(family=fam,mechanism=mech,observable=o,G=float(q.G.iloc[0]) if len(q) else np.nan,n=int(q.n.iloc[0]) if len(q) else 0))
    return pd.DataFrame(rows)

def fig3_observable(stage3f,stage3g5,out):
    d=assemble_obs(stage3f,stage3g5)
    obs=['B','B/A','Sn','S2n','delta2n']; x=np.arange(len(obs))
    fig,ax=plt.subplots(figsize=(8.7,4.8))
    combos=[('hgb','soft','HGB soft'),('hgb','residual','HGB residual'),('mlp','soft','MLP soft'),('mlp','residual','MLP residual')]
    for i,(fam,mech,label) in enumerate(combos):
        vals=[]
        for o in obs:
            q=d[(d.family==fam)&(d.mechanism==mech)&(d.observable==o)]; vals.append(float(q.G.iloc[0]) if len(q) else np.nan)
        ax.plot(x,vals,label=label,linewidth=1.8,markersize=6,**STYLES[i])
    ax.axhline(1,color='black',linewidth=1,alpha=.65)
    ax.fill_between([-0.3,len(obs)-.7],0,1,color='0.96',zorder=0)
    ax.set_xticks(x,[r'$B$',r'$B/A$',r'$S_n$',r'$S_{2n}$',r'$\delta_{2n}$'])
    ax.set_ylabel('Observable-specific trust gain G')
    ax.set_title('Whole Sn-chain holdout: the sign of physics trust depends on the observable')
    ax.legend(frameon=False,ncol=2); ax.grid(axis='y',alpha=.18)
    save(fig,out,'Fig3_Observable_Dependent_Trust_Sn')

def calc_chain_derived(d,col):
    q=d[['N','Z','A',col]].copy(); q['is_test']=True
    return derived_from_predictions(q.rename(columns={col:'Btmp'}),'Btmp','is_test')

def fig4_sn(stage3f,out):
    d=pd.read_csv(stage3f/'STRUCTURED_PREDICTIONS.csv'); d=d[d.regime=='R1_Sn'].sort_values('N').copy(); d['is_test']=True
    methods=[('B_semf','SEMF'),('B_bwn','BWN'),('B_hgb_data','HGB data only'),('B_hgb_soft','HGB soft'),('B_hgb_residual','HGB residual')]
    fig,axs=plt.subplots(2,2,figsize=(10.0,7.0),sharex=True)
    # B residual
    for i,(c,l) in enumerate(methods):
        if c in d: axs[0,0].plot(d.N,d[c]-d.B_true,label=l,linewidth=1.4,markersize=3.8,**STYLES[i])
    axs[0,0].axhline(0,color='black',lw=.9); axs[0,0].set_ylabel(r'$B_{pred}-B_{exp}$ (MeV)'); axs[0,0].set_title('Binding-energy residual')
    # BA residual
    for i,(c,l) in enumerate(methods):
        if c in d: axs[0,1].plot(d.N,(d[c]-d.B_true)/d.A,label=l,linewidth=1.4,markersize=3.8,**STYLES[i])
    axs[0,1].axhline(0,color='black',lw=.9); axs[0,1].set_ylabel(r'$(B_{pred}-B_{exp})/A$ (MeV)'); axs[0,1].set_title('Binding energy per nucleon residual')
    # derived truth and methods
    truth=calc_chain_derived(d,'B_true')
    for panel,o,ylabel in [(axs[1,0],'S2n',r'$S_{2n}$ (MeV)'),(axs[1,1],'delta2n',r'$\delta_{2n}$ (MeV)')]:
        panel.plot(truth.N,truth[o],label='Experimental',linewidth=1.8,markersize=4.5,**STYLES[0])
        for i,(c,l) in enumerate(methods,start=1):
            if c not in d: continue
            z=calc_chain_derived(d,c); panel.plot(z.N,z[o],label=l,linewidth=1.25,markersize=3.4,**STYLES[i%len(STYLES)])
        panel.set_ylabel(ylabel); panel.set_title(('Two-neutron separation energy' if o=='S2n' else 'Two-neutron shell-gap diagnostic'))
    for ax in axs.flat:
        ax.axvline(82,color='black',ls='--',lw=1,alpha=.55); ax.grid(alpha=.15); ax.set_xlabel('Neutron number N')
    axs[0,0].legend(frameon=False,fontsize=7.1,ncol=2)
    axs[1,0].legend(frameon=False,fontsize=6.9,ncol=2)
    save(fig,out,'Fig4_Sn_Chain_Bulk_and_Local_Observables')

def chart_scatter(ax,d,col,title,quant=.98):
    vals=d[col].to_numpy(float); lim=max(1e-6,float(np.nanquantile(np.abs(vals),quant)))
    sc=ax.scatter(d.N,d.Z,c=vals,s=9,cmap='coolwarm',norm=TwoSlopeNorm(vcenter=0,vmin=-lim,vmax=lim),linewidths=0)
    for n in [20,28,50,82,126]: ax.axvline(n,color='k',lw=.35,alpha=.14)
    for z in [20,28,50,82]: ax.axhline(z,color='k',lw=.35,alpha=.14)
    ax.set_title(title); ax.set_xlabel('N'); ax.set_ylabel('Z')
    cb=plt.colorbar(sc,ax=ax,fraction=.046,pad=.02); cb.ax.tick_params(labelsize=7); return lim

def fig5_buildup(stage3g5,out):
    d=pd.read_csv(stage3g5/'SEMF_TERM_LANDSCAPE_AME2020.csv')
    stages=[(1,'volume','Volume'),(2,'surface','+ surface'),(3,'coulomb','+ Coulomb'),(4,'asymmetry','+ asymmetry'),(5,'pairing','+ pairing')]
    fig,axs=plt.subplots(1,5,figsize=(14.8,3.3),sharex=True,sharey=True)
    for ax,(i,t,lbl) in zip(axs,stages):
        lim=chart_scatter(ax,d,f'residual_BA_{i}_{t}',lbl,.98)
        ax.text(.03,.04,f'98% |res.| = {lim:.3g}',transform=ax.transAxes,fontsize=6.5,bbox=dict(facecolor='white',alpha=.75,edgecolor='none'))
    fig.suptitle('Sequential SEMF term build-up: AME2020 diagnostic residual $B_{exp}/A-B_{stage}/A$',y=1.02,fontsize=11)
    save(fig,out,'Fig5_SEMF_Term_Buildup_Residual_Maps')

def fig6_landscape(stage3g5,out):
    d=pd.read_csv(stage3g5/'SEMF_TERM_LANDSCAPE_AME2020.csv')
    fig,ax=plt.subplots(figsize=(8.0,5.1)); lim=chart_scatter(ax,d,'residual_BA_5_pairing','Five-term SEMF residual landscape',.99)
    ax.set_title(f'Experimental minus fitted SEMF binding energy per nucleon (99% scale +/-{lim:.3f} MeV)')
    save(fig,out,'Fig6_Experimental_minus_SEMF_BA_Landscape')

def fig7_terms(stage3g5,stage3g,out):
    rem=pd.read_csv(stage3g5/'SEMF_TERM_REMOVAL_METRICS.csv')
    regs=['R0_random','R1_Sn','R2_neutron_rich','R3_proton_rich','R4_magic_pm1','R7_light_random']
    fig,axs=plt.subplots(1,2,figsize=(10.0,4.2))
    x=np.arange(len(regs))
    for i,t in enumerate(['surface','coulomb','asymmetry','pairing']):
        vals=[]
        for r in regs:
            full=rem[(rem.regime==r)&(rem.removed_term=='none')].B_mae.iloc[0]
            q=rem[(rem.regime==r)&(rem.removed_term==t)].B_mae.iloc[0]; vals.append(q/full)
        axs[0].plot(x,vals,label=f'Remove {t}',linewidth=1.5,markersize=5,**STYLES[i])
    axs[0].axhline(1,color='black',lw=1); axs[0].set_yscale('log'); axs[0].set_ylabel('MAE ratio: term-removed / full SEMF'); axs[0].set_xticks(x,[REG_LABEL[r] for r in regs],rotation=28,ha='right'); axs[0].set_title('One-term-removal diagnostics'); axs[0].legend(frameon=False,fontsize=7.2); axs[0].grid(axis='y',alpha=.15)
    form=pd.read_csv(stage3g/'MODEL_FORM_MISSPECIFICATION.csv'); q=form[form.family=='BWN'].copy()
    q=q[q.regime.isin(['R0_random','R1_Sn','R4_magic_pm1'])]
    labs=[REG_LABEL[r] for r in q.regime]; xx=np.arange(len(q)); w=.36
    axs[1].bar(xx-w/2,q.nominal_mae,width=w,label='BWN nominal',edgecolor='black',lw=.4)
    axs[1].bar(xx+w/2,q.suppressed_mae,width=w,label='BWN shell term suppressed',edgecolor='black',lw=.4,hatch='//')
    axs[1].set_xticks(xx,labs); axs[1].set_ylabel('Binding-energy MAE (MeV)'); axs[1].set_title('Shell-aware model-form control'); axs[1].legend(frameon=False,fontsize=7.4); axs[1].grid(axis='y',alpha=.15)
    save(fig,out,'Fig7_Model_Form_and_Term_Removal')

def fig8_coeff(stage3g,out):
    j=json.load(open(stage3g/'SEMF_CHRONOLOGICAL_COEFFICIENTS_AND_BOOTSTRAP.json'))['chronological']
    domains=pd.read_csv(stage3g/'SEMF_CALIBRATION_DOMAIN_SENSITIVITY.csv')
    names=['a_v','a_s','a_c','a_a','a_p']; years=['2012','2016','2020']
    fig,axs=plt.subplots(1,2,figsize=(10.0,4.2))
    x=np.arange(3)
    for i,n in enumerate(names):
        vals=np.array([j[y]['fit']['coef'][n] for y in years]); base=vals[0]; rel=vals/base
        lo=[]; hi=[]
        for y,v in zip(years,vals):
            ci=j[y]['bootstrap']['ci95'][n]; lo.append((v-ci[0])/abs(base)); hi.append((ci[1]-v)/abs(base))
        axs[0].errorbar(x,rel,yerr=np.array([lo,hi]),capsize=2,label=n,linewidth=1.4,markersize=5,**STYLES[i])
    axs[0].axhline(1,color='black',lw=.9); axs[0].set_xticks(x,years); axs[0].set_ylabel('Coefficient / AME2012 value'); axs[0].set_title('Chronological coefficient drift'); axs[0].legend(frameon=False,ncol=3,fontsize=7.2); axs[0].grid(axis='y',alpha=.15)
    q=domains[domains.vintage==2020].drop_duplicates('domain',keep='first').copy(); order=['D0_primary','D1_A_ge_50','D2_broad_measured','D3_primary_precision']; q=q.set_index('domain').reindex(order); x=np.arange(len(order))
    for i,n in enumerate(names):
        base=float(q.loc['D0_primary',n]); axs[1].plot(x,q[n].to_numpy(float)/base,label=n,linewidth=1.4,markersize=5,**STYLES[i])
    axs[1].axhline(1,color='black',lw=.9); axs[1].set_xticks(x,['D0 primary','D1 A>=50','D2 broad','D3 precision'],rotation=20,ha='right'); axs[1].set_ylabel('Coefficient / 2020 D0 value'); axs[1].set_title('Calibration-domain sensitivity (AME2020)'); axs[1].legend(frameon=False,ncol=3,fontsize=7.2); axs[1].grid(axis='y',alpha=.15)
    save(fig,out,'Fig8_Coefficient_Drift_and_Calibration_Domain')

def supp_corr_condition(stage3g,out):
    j=json.load(open(stage3g/'SEMF_CHRONOLOGICAL_COEFFICIENTS_AND_BOOTSTRAP.json'))['chronological']; names=['a_v','a_s','a_c','a_a','a_p']
    fig,axs=plt.subplots(1,2,figsize=(9.4,4.0))
    corr=np.array(j['2020']['bootstrap']['correlation'],float); im=axs[0].imshow(corr,vmin=-1,vmax=1,cmap='coolwarm'); axs[0].set_xticks(range(5),names); axs[0].set_yticks(range(5),names); axs[0].set_title('AME2020 bootstrap coefficient correlation'); plt.colorbar(im,ax=axs[0],fraction=.046,pad=.04)
    x=np.arange(1,6)
    for i,y in enumerate(['2012','2016','2020']):
        s=np.array(j[y]['fit']['singular_values'],float); axs[1].plot(x,s/s[0],label=f"AME{y} (cond={j[y]['fit']['condition_number']:.2e})",linewidth=1.5,markersize=5,**STYLES[i])
    axs[1].set_yscale('log'); axs[1].set_xlabel('Singular-value index'); axs[1].set_ylabel(r'$\sigma_i/\sigma_1$'); axs[1].set_title('SEMF design-matrix conditioning'); axs[1].legend(frameon=False,fontsize=7); axs[1].grid(axis='y',alpha=.15)
    save(fig,out,'SuppFig_S1_Correlation_and_Conditioning')

def supp_natural(stage3g5,out):
    d=pd.read_csv(stage3g5/'HISTORICAL_OBSERVABLE_TRUST.csv'); d=d[(d.family.isin(['hgb','mlp']))&(d.mechanism.isin(['soft','residual']))]
    obs=['B','B/A','Sn','S2n']; x=np.arange(len(obs)); fig,axs=plt.subplots(1,2,figsize=(9.3,3.7),sharey=False)
    for ax,(trans,title) in zip(axs,[('AME2012_to_AME2016_development','AME2012 -> AME2016 development'),('AME2016_to_AME2020_confirmation','AME2016 -> AME2020 confirmation')]):
        q=d[d.transition==trans]
        for i,(fam,mech,label) in enumerate([('hgb','soft','HGB soft'),('hgb','residual','HGB residual'),('mlp','soft','MLP soft'),('mlp','residual','MLP residual')]):
            vals=[]
            for o in obs:
                z=q[(q.family==fam)&(q.mechanism==mech)&(q.observable==o)]; vals.append(float(z.G_vintage.iloc[0]) if len(z) else np.nan)
            ax.plot(x,vals,label=label,linewidth=1.4,markersize=5,**STYLES[i])
        ax.axhline(1,color='black',lw=.9); ax.set_xticks(x,obs); ax.set_ylabel(r'$G_{vintage}$'); ax.set_title(title); ax.grid(axis='y',alpha=.15)
    axs[1].legend(frameon=False,ncol=2,fontsize=6.8); save(fig,out,'SuppFig_S2_Natural_Prior_Aging_Trust')

def supp_light(stage3f,out):
    d=pd.read_csv(stage3f/'STRUCTURED_PREDICTIONS.csv'); d=d[d.regime=='R7_light_random'].copy(); d['stratum']=pd.cut(d.A,[-np.inf,19,39,np.inf],labels=['A<20','20<=A<40','A>=40'])
    fig,ax=plt.subplots(figsize=(7.4,4.0)); x=np.arange(3)
    combos=[('B_hgb_soft','HGB soft'),('B_hgb_residual','HGB residual'),('B_mlp_soft','MLP soft'),('B_mlp_residual','MLP residual')]
    for i,(c,l) in enumerate(combos):
        vals=[]
        for s in ['A<20','20<=A<40','A>=40']:
            q=d[d.stratum.astype(str)==s]; vals.append(float(np.mean(np.abs(q[c]-q.B_true))))
        ax.plot(x,vals,label=l,linewidth=1.5,markersize=5,**STYLES[i])
    ax.set_xticks(x,['A<20','20<=A<40','A>=40']); ax.set_ylabel('Binding-energy MAE (MeV)'); ax.set_title('Supplementary light-nucleus model-validity stress test'); ax.legend(frameon=False,ncol=2); ax.grid(axis='y',alpha=.15); save(fig,out,'SuppFig_S3_Light_Nucleus_Stress')

def supp_local(stage3g5,out):
    d=pd.read_csv(stage3g5/'LOCAL_PAIRED_ERROR_IMPROVEMENT_R0.csv'); d=d[(d.family=='hgb')&(d.mechanism.isin(['soft','residual']))&(d.observable.isin(['B','S2n']))]
    fig,axs=plt.subplots(2,2,figsize=(8.4,7.0),sharex=True,sharey=True)
    for ax,(mech,o) in zip(axs.flat,[('soft','B'),('residual','B'),('soft','S2n'),('residual','S2n')]):
        q=d[(d.mechanism==mech)&(d.observable==o)]; vals=q.paired_error_improvement.to_numpy(float); lim=max(.01,float(np.quantile(np.abs(vals),.98))) if len(vals) else 1
        sc=ax.scatter(q.N,q.Z,c=vals,s=14,cmap='PiYG',norm=TwoSlopeNorm(vcenter=0,vmin=-lim,vmax=lim),linewidths=0)
        ax.set_title(f'HGB {mech}: {o}'); ax.set_xlabel('N'); ax.set_ylabel('Z'); plt.colorbar(sc,ax=ax,fraction=.046,pad=.03,label='|err(data)| - |err(physics+ML)|')
    save(fig,out,'SuppFig_S4_Local_Paired_Error_Maps_R0')

def supp_heatmap(stage3f,stage3g5,out):
    der=pd.read_csv(stage3f/'STRUCTURED_OBSERVABLE_TRUST_G.csv'); ba=pd.read_csv(stage3g5/'BA_TRUST_BY_REGIME.csv'); bm=pd.read_csv(stage3f/'STRUCTURED_B_METRICS.csv')
    regs=['R0_random','R1_Ca','R1_Sn','R1_Ni','R1_Pb','R2_neutron_rich','R3_proton_rich','R4_magic_pm1','R7_light_random']; obs=['B','B/A','Sn','S2n','Sp','S2p','delta2n','delta2p']
    M=np.full((len(regs),len(obs)),np.nan)
    for i,r in enumerate(regs):
        dm=bm[(bm.regime==r)&(bm.family=='hgb')&(bm.mechanism=='data')]; pm=bm[(bm.regime==r)&(bm.family=='hgb')&(bm.mechanism=='residual')]
        if len(dm) and len(pm): M[i,0]=float(dm.mae.iloc[0]/pm.mae.iloc[0])
        q=ba[(ba.regime==r)&(ba.family=='hgb')&(ba.mechanism=='residual')];
        if len(q): M[i,1]=float(q.G_vs_data_MAE.iloc[0])
        for j,o in enumerate(obs[2:],start=2):
            q=der[(der.regime==r)&(der.family=='hgb')&(der.mechanism=='residual')&(der.observable==o)]
            if len(q): M[i,j]=float(q.G.iloc[0])
    fig,ax=plt.subplots(figsize=(8.8,5.2)); im=ax.imshow(np.log2(M),cmap='RdBu_r',vmin=-2.2,vmax=3.6,aspect='auto'); ax.set_xticks(range(len(obs)),[r'$B$',r'$B/A$',r'$S_n$',r'$S_{2n}$',r'$S_p$',r'$S_{2p}$',r'$\delta_{2n}$',r'$\delta_{2p}$']); ax.set_yticks(range(len(regs)),[REG_LABEL[r] for r in regs]); ax.set_title('HGB residual-repair trust matrix (color = log2 G)'); cb=plt.colorbar(im,ax=ax); cb.set_label('log2 G')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i,j]): ax.text(j,i,f'{M[i,j]:.1f}',ha='center',va='center',fontsize=6.7,color=('white' if abs(np.log2(M[i,j]))>2 else 'black'))
    save(fig,out,'SuppFig_S5_Observable_Trust_Matrix_HGB_Residual')

def main():
    setup(); ap=argparse.ArgumentParser()
    for n in ['stage3e','stage3f','stage3g','stage3g5']: ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); main=a.out/'main'; supp=a.out/'supplementary'
    fig1_confirmation(a.stage3e,main); fig2_structured(a.stage3g,main); fig3_observable(a.stage3f,a.stage3g5,main); fig4_sn(a.stage3f,main); fig5_buildup(a.stage3g5,main); fig6_landscape(a.stage3g5,main); fig7_terms(a.stage3g5,a.stage3g,main); fig8_coeff(a.stage3g,main)
    supp_corr_condition(a.stage3g,supp); supp_natural(a.stage3g5,supp); supp_light(a.stage3f,supp); supp_local(a.stage3g5,supp); supp_heatmap(a.stage3f,a.stage3g5,supp)
    (a.out/'FIGURE_STYLE_RULE.txt').write_text('Every multi-series line plot uses a distinct combination of color, line style, and marker shape.\n',encoding='utf-8')
    print('FINAL FIGURES: PASS',len(list(main.glob('*.png'))),'main',len(list(supp.glob('*.png'))),'supplementary')
if __name__=='__main__': main()
