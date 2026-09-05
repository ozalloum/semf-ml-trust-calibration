from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

MAGIC_P = np.array([2,8,20,28,50,82,126], dtype=float)
MAGIC_N = np.array([2,8,20,28,50,82,126,184], dtype=float)
PARAM_NAMES = [
    "alpha_v","alpha_s","alpha_c","c_sym","alpha_p","alpha_xc","alpha_r",
    "alpha_m","beta_m","c_m","e_m1","e_m2","k","xi","kappa_s"
]
PUBLISHED_BWN = {
    "alpha_v":16.7043,"alpha_s":-26.3000,"alpha_c":-0.7615,"c_sym":-35.3636,
    "alpha_p":5.9751,"alpha_xc":1.4405,"alpha_r":14.1287,"alpha_m":-1.0877,
    "beta_m":0.1615,"c_m":-0.2343,"e_m1":5.4713,"e_m2":-0.0444,
    "k":2.0829,"xi":1.2216,"kappa_s":0.2491,
}
PUBLISHED_RMS_B = 0.887


def _nearest(x: np.ndarray, magic: np.ndarray) -> np.ndarray:
    return np.min(np.abs(x[:,None]-magic[None,:]),axis=1)


def bwn_components(df: pd.DataFrame):
    N=df["N"].to_numpy(float); Z=df["Z"].to_numpy(float); A=N+Z
    I=(N-Z)/A; absI=np.abs(I)
    vp=_nearest(Z,MAGIC_P); vn=_nearest(N,MAGIC_N)
    denom=vp+vn; P=np.divide(vp*vn,denom,out=np.zeros_like(denom),where=denom!=0)
    evenN=(N.astype(int)%2==0); evenZ=(Z.astype(int)%2==0)
    delta_np=np.empty(len(A),float)
    both_even=evenN&evenZ; both_odd=(~evenN)&(~evenZ)
    delta_np[both_even]=(2-absI[both_even]-I[both_even]**2)*17/16
    delta_np[both_odd]=absI[both_odd]-I[both_odd]**2
    m=(evenN&(~evenZ)&(N>Z)) | ((~evenN)&evenZ&(N<Z))
    delta_np[m]=1-absI[m]
    m2=(evenN&(~evenZ)&(N<Z)) | ((~evenN)&evenZ&(N>Z))
    delta_np[m2]=1.0
    # exact region rule in Wu et al. Eq. 12
    ds=np.ones(len(A),float)
    ds[(Z>=8)&(Z<=24)&(N>=8)&(N<=24)] = -1.0
    ds[(Z>=8)&(Z<=24)&(N>24)&(N<=66)] = 0.0
    ds[(Z>24)&(Z<=39)&(N>=8)&(N<=66)] = 0.0
    return N,Z,A,I,absI,vp,vn,P,delta_np,ds


def vector_from_dict(p: dict) -> np.ndarray:
    return np.array([p[k] for k in PARAM_NAMES],float)


def dict_from_vector(x: np.ndarray) -> dict:
    return {k:float(v) for k,v in zip(PARAM_NAMES,x)}


def predict_bwn(df: pd.DataFrame, params: dict | np.ndarray) -> np.ndarray:
    x=vector_from_dict(params) if isinstance(params,dict) else np.asarray(params,float)
    (av,as_,ac,csym,ap,axc,ar,am,bm,cm,em1,em2,k,xi,ks)=x
    N,Z,A,I,absI,vp,vn,P,dnp,ds=bwn_components(df)
    # Wu et al. Eqs. 7-9, following the publisher HTML notation literally:
    # c_sym * (1-k/A^(1/3) + xi*(2-|I|)/(2+|I|*A))
    asymI=csym*(1-k/np.cbrt(A)+xi*(2-absI)/(2+absI*A))
    fs=1+ks*((I-0.4*A/(A+200))**2-I**4)*np.cbrt(A)
    expo=np.exp(np.clip(em2*(vp**2+vn**2),-700,100))
    return (
        av*A + as_*A**(2/3) + ac*Z**2/A**(1/3) + asymI*I**2*A*fs
        + dnp*ap*A**(-1/3) + axc*Z**(4/3)*A**(-1/3) + ar*A**(1/3)
        + am*P + bm*P**2 + cm*(vn+vp) + em1*ds*expo
    )


def fit_bwn(df: pd.DataFrame, y_col: str="B_total_MeV", start: dict|None=None, max_nfev: int=20000) -> dict:
    d=df.dropna(subset=[y_col]).copy()
    y=d[y_col].to_numpy(float)
    x0=vector_from_dict(start or PUBLISHED_BWN)
    lb=np.array([10,-50,-1.5,-70,0,-5,-30,-10,-1,-5,0,-1e0,0,-5,-2],float)
    ub=np.array([25,-5,-0.1,-10,25,5,50,10,1,5,25,-1e-7,6,6,2],float)
    def residual(x): return predict_bwn(d,x)-y
    res=least_squares(residual,x0,bounds=(lb,ub),max_nfev=max_nfev,xtol=1e-11,ftol=1e-11,gtol=1e-11)
    pred=predict_bwn(d,res.x)
    return {
        "params":dict_from_vector(res.x),"success":bool(res.success),"status":int(res.status),
        "message":str(res.message),"cost":float(res.cost),"nfev":int(res.nfev),"n":int(len(d)),
        "rmse":float(np.sqrt(np.mean((pred-y)**2))),"mae":float(np.mean(np.abs(pred-y))),
    }


def published_reproduction(df: pd.DataFrame, y_col: str="B_total_MeV") -> dict:
    d=df[(df.N>=8)&(df.Z>=8)].dropna(subset=[y_col]).copy()
    pred=predict_bwn(d,PUBLISHED_BWN); y=d[y_col].to_numpy(float)
    rmse=float(np.sqrt(np.mean((pred-y)**2)))
    return {"n":int(len(d)),"rmse":rmse,"target_rmse":PUBLISHED_RMS_B,"abs_difference":abs(rmse-PUBLISHED_RMS_B),"pass_tolerance_0p02":abs(rmse-PUBLISHED_RMS_B)<=0.02}
