from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

MAGIC_N = np.array([8, 20, 28, 50, 82, 126, 184], dtype=float)
MAGIC_Z = np.array([8, 20, 28, 50, 82, 126], dtype=float)
BASE_FEATURES = ["N", "Z", "A", "I", "even_N", "even_Z"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(obj), encoding="utf-8")


def read_csv_nonempty(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing/empty required CSV: {path}")
    return pd.read_csv(path)


def ensure_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "A" not in out:
        out["A"] = out["N"] + out["Z"]
    if "I" not in out:
        out["I"] = (out["N"] - out["Z"]) / out["A"]
    if "even_N" not in out:
        out["even_N"] = (out["N"].astype(int) % 2 == 0).astype(int)
    if "even_Z" not in out:
        out["even_Z"] = (out["Z"].astype(int) % 2 == 0).astype(int)
    return out


def semf_design(df: pd.DataFrame, include_pairing: bool = True) -> np.ndarray:
    d = ensure_features(df)
    A = d["A"].to_numpy(float)
    N = d["N"].to_numpy(float)
    Z = d["Z"].to_numpy(float)
    pair_sign = np.where((N % 2 == 0) & (Z % 2 == 0), 1.0,
                         np.where((N % 2 == 1) & (Z % 2 == 1), -1.0, 0.0))
    cols = [
        A,
        -np.power(A, 2.0 / 3.0),
        -(Z * (Z - 1.0)) / np.power(A, 1.0 / 3.0),
        -np.square(N - Z) / A,
    ]
    if include_pairing:
        cols.append(pair_sign / np.sqrt(A))
    return np.column_stack(cols)


def fit_semf(df: pd.DataFrame, y_col: str = "B_total_MeV", include_pairing: bool = True) -> dict:
    d = ensure_features(df).dropna(subset=[y_col]).copy()
    X = semf_design(d, include_pairing=include_pairing)
    y = d[y_col].to_numpy(float)
    coef, residuals, rank, singular = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    names = ["a_v", "a_s", "a_c", "a_a"] + (["a_p"] if include_pairing else [])
    return {
        "coef": {k: float(v) for k, v in zip(names, coef)},
        "rank": int(rank),
        "singular_values": [float(x) for x in singular],
        "condition_number": float(np.linalg.cond(X)),
        "n": int(len(d)),
        "rmse_train": float(np.sqrt(np.mean((y - pred) ** 2))),
        "mae_train": float(np.mean(np.abs(y - pred))),
    }


def semf_predict(df: pd.DataFrame, fit: dict, include_pairing: bool = True) -> np.ndarray:
    X = semf_design(df, include_pairing=include_pairing)
    names = ["a_v", "a_s", "a_c", "a_a"] + (["a_p"] if include_pairing else [])
    coef = np.array([fit["coef"][k] for k in names], dtype=float)
    return X @ coef


def model_from_config(family: str, cfg: dict, seed: int | None = None):
    if family == "ridge":
        return Pipeline([
            ("poly", PolynomialFeatures(degree=5, include_bias=False)),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=float(cfg["alpha"]))),
        ])
    if family == "hgb":
        return HistGradientBoostingRegressor(
            learning_rate=float(cfg["learning_rate"]),
            max_iter=int(cfg["max_iter"]),
            max_leaf_nodes=int(cfg["max_leaf_nodes"]),
            min_samples_leaf=int(cfg["min_samples_leaf"]),
            l2_regularization=0.0,
            random_state=20260910,
        )
    if family == "mlp":
        return Pipeline([
            ("scale", StandardScaler()),
            ("mlp", MLPRegressor(
                hidden_layer_sizes=tuple(cfg["hidden_layers"]),
                alpha=float(cfg["alpha"]),
                learning_rate_init=float(cfg["learning_rate_init"]),
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=int(cfg.get("_n_iter_test", 80)),
                tol=1e-6,
                max_iter=int(cfg.get("_max_iter_test", 4000)),
                random_state=int(seed if seed is not None else 211),
            )),
        ])
    raise ValueError(f"Unknown family: {family}")


def model_grid() -> dict[str, list[dict]]:
    ridge = [{"alpha": x} for x in [1e-4, 1e-3, 1e-2, 1e-1]]
    hgb = []
    for lr in [0.03, 0.05]:
        for it in [200, 500]:
            for leaves in [15, 31]:
                for msl in [10, 20]:
                    hgb.append({"learning_rate": lr, "max_iter": it, "max_leaf_nodes": leaves, "min_samples_leaf": msl})
    mlp = []
    for hidden in [(64, 64), (128, 64)]:
        for alpha in [1e-5, 1e-4, 1e-3]:
            for lr in [5e-4, 1e-3]:
                mlp.append({"hidden_layers": list(hidden), "alpha": alpha, "learning_rate_init": lr})
    return {"ridge": ridge, "hgb": hgb, "mlp": mlp}


def primary_X(df: pd.DataFrame) -> np.ndarray:
    return ensure_features(df)[BASE_FEATURES].to_numpy(float)


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, float); y_pred = np.asarray(y_pred, float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[mask]; y_pred = y_pred[mask]
    if len(y_true) == 0:
        return {"n": 0, "mae": None, "rmse": None, "bias": None, "median_ae": None, "p95_ae": None}
    err = y_pred - y_true
    ae = np.abs(err)
    return {
        "n": int(len(y_true)),
        "mae": float(np.mean(ae)),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "bias": float(np.mean(err)),
        "median_ae": float(np.median(ae)),
        "p95_ae": float(np.quantile(ae, 0.95)),
    }


def nearest_magic_distance(values: np.ndarray, magic: np.ndarray) -> np.ndarray:
    values = np.asarray(values, float)
    return np.min(np.abs(values[:, None] - magic[None, :]), axis=1)


def nearest_training_l1(eval_df: pd.DataFrame, train_df: pd.DataFrame) -> np.ndarray:
    e = ensure_features(eval_df)[["N", "Z"]].to_numpy(float)
    t = ensure_features(train_df)[["N", "Z"]].to_numpy(float)
    if len(t) == 0:
        return np.full(len(e), np.nan)
    out = np.empty(len(e), dtype=float)
    # small nuclear charts: chunking keeps memory predictable
    for i in range(0, len(e), 256):
        block = e[i:i+256]
        dist = np.abs(block[:, None, :] - t[None, :, :]).sum(axis=2)
        out[i:i+256] = dist.min(axis=1)
    return out


def gate_features(eval_df: pd.DataFrame, train_df: pd.DataFrame) -> np.ndarray:
    d = ensure_features(eval_df)
    cols = np.column_stack([
        np.abs(d["I"].to_numpy(float)),
        d["even_N"].to_numpy(float),
        d["even_Z"].to_numpy(float),
        nearest_magic_distance(d["N"].to_numpy(float), MAGIC_N),
        nearest_magic_distance(d["Z"].to_numpy(float), MAGIC_Z),
        nearest_training_l1(d, train_df),
    ])
    return cols


def oracle_lambda(y: np.ndarray, ml: np.ndarray, phys: np.ndarray) -> np.ndarray:
    y = np.asarray(y, float); ml = np.asarray(ml, float); phys = np.asarray(phys, float)
    d = phys - ml
    out = np.zeros_like(y)
    nz = np.abs(d) > 1e-12
    out[nz] = (y[nz] - ml[nz]) / d[nz]
    return np.clip(out, 0.0, 1.0)


def derived_from_predictions(pred_df: pd.DataFrame, pred_col: str, strict_oos_col: str = "is_test") -> pd.DataFrame:
    d = pred_df.copy()
    idx = {(int(r.N), int(r.Z)): r for r in d.itertuples(index=False)}
    rows = []
    for r in d.itertuples(index=False):
        if hasattr(r, strict_oos_col) and not bool(getattr(r, strict_oos_col)):
            continue
        N, Z = int(r.N), int(r.Z)
        B = float(getattr(r, pred_col))
        base = {"N": N, "Z": Z, "A": int(r.A)}
        def get_b(n, z):
            rr = idx.get((n, z))
            if rr is None:
                return None
            if hasattr(rr, strict_oos_col) and not bool(getattr(rr, strict_oos_col)):
                return None
            v = getattr(rr, pred_col)
            return float(v) if np.isfinite(v) else None
        b_n1 = get_b(N-1, Z); b_n2 = get_b(N-2, Z)
        b_p1 = get_b(N, Z-1); b_p2 = get_b(N, Z-2)
        b_d = get_b(N-2, Z-2); b_alpha = get_b(2,2)
        row = dict(base)
        row["Sn"] = None if b_n1 is None else B - b_n1
        row["S2n"] = None if b_n2 is None else B - b_n2
        row["Sp"] = None if b_p1 is None else B - b_p1
        row["S2p"] = None if b_p2 is None else B - b_p2
        row["Qalpha"] = None if b_d is None or b_alpha is None else b_d + b_alpha - B
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    omap = {(int(r.N), int(r.Z)): r for r in out.itertuples(index=False)}
    d2n=[]; d2p=[]
    for r in out.itertuples(index=False):
        rnn = omap.get((int(r.N)+2, int(r.Z)))
        rpp = omap.get((int(r.N), int(r.Z)+2))
        d2n.append(None if pd.isna(r.S2n) or rnn is None or pd.isna(rnn.S2n) else float(r.S2n-rnn.S2n))
        d2p.append(None if pd.isna(r.S2p) or rpp is None or pd.isna(rpp.S2p) else float(r.S2p-rpp.S2p))
    out["delta2n"] = d2n; out["delta2p"] = d2p
    return out


def paired_bootstrap(y: np.ndarray, a: np.ndarray, b: np.ndarray, n_boot: int = 5000, seed: int = 20260911) -> dict:
    y = np.asarray(y,float); a=np.asarray(a,float); b=np.asarray(b,float)
    mask=np.isfinite(y)&np.isfinite(a)&np.isfinite(b)
    y=y[mask];a=a[mask];b=b[mask]
    n=len(y)
    if n==0:
        return {"n":0}
    rng=np.random.default_rng(seed)
    vals=[]
    for _ in range(n_boot):
        ix=rng.integers(0,n,size=n)
        ea=np.mean(np.abs(a[ix]-y[ix])); eb=np.mean(np.abs(b[ix]-y[ix]))
        vals.append((ea-eb, ea/eb if eb>0 else np.nan))
    arr=np.array(vals,float)
    return {
        "n":n,
        "mae_diff_a_minus_b":float(np.mean(np.abs(a-y))-np.mean(np.abs(b-y))),
        "mae_diff_ci95":[float(np.nanquantile(arr[:,0],0.025)),float(np.nanquantile(arr[:,0],0.975))],
        "G_a_over_b":float(np.mean(np.abs(a-y))/np.mean(np.abs(b-y))) if np.mean(np.abs(b-y))>0 else None,
        "G_ci95":[float(np.nanquantile(arr[:,1],0.025)),float(np.nanquantile(arr[:,1],0.975))],
    }


def chain_block_bootstrap(df: pd.DataFrame, y_col: str, a_col: str, b_col: str, n_boot: int = 5000, seed: int = 20260912) -> dict:
    d=df[["Z",y_col,a_col,b_col]].dropna().copy()
    zs=np.array(sorted(d["Z"].unique()))
    if len(zs)==0:
        return {"n_chains":0}
    groups={z:d[d["Z"]==z] for z in zs}
    rng=np.random.default_rng(seed)
    vals=[]
    for _ in range(n_boot):
        sample_z=rng.choice(zs,size=len(zs),replace=True)
        parts=[groups[z] for z in sample_z]
        s=pd.concat(parts,ignore_index=True)
        y=s[y_col].to_numpy(float);a=s[a_col].to_numpy(float);b=s[b_col].to_numpy(float)
        ea=np.mean(np.abs(a-y));eb=np.mean(np.abs(b-y))
        vals.append((ea-eb,ea/eb if eb>0 else np.nan))
    arr=np.array(vals,float)
    return {"n_chains":int(len(zs)),"mae_diff_ci95":[float(np.nanquantile(arr[:,0],.025)),float(np.nanquantile(arr[:,0],.975))],"G_ci95":[float(np.nanquantile(arr[:,1],.025)),float(np.nanquantile(arr[:,1],.975))]}


def bootstrap_semf(df: pd.DataFrame, n_boot: int = 5000, seed: int = 20260913) -> dict:
    d=ensure_features(df).dropna(subset=["B_total_MeV"]).reset_index(drop=True)
    X=semf_design(d,True); y=d["B_total_MeV"].to_numpy(float); n=len(d)
    rng=np.random.default_rng(seed)
    coefs=np.empty((n_boot,5),float)
    for i in range(n_boot):
        ix=rng.integers(0,n,size=n)
        coefs[i]=np.linalg.lstsq(X[ix],y[ix],rcond=None)[0]
    names=["a_v","a_s","a_c","a_a","a_p"]
    cov=np.cov(coefs,rowvar=False); corr=np.corrcoef(coefs,rowvar=False)
    return {
        "names":names,
        "mean":{n:float(v) for n,v in zip(names,coefs.mean(axis=0))},
        "sd":{n:float(v) for n,v in zip(names,coefs.std(axis=0,ddof=1))},
        "ci95":{n:[float(q[0]),float(q[1])] for n,q in zip(names,np.quantile(coefs,[.025,.975],axis=0).T)},
        "covariance":cov.tolist(),
        "correlation":corr.tolist(),
    }


def make_regime_splits(primary: pd.DataFrame, broad_light: pd.DataFrame | None = None) -> dict[str, tuple[pd.DataFrame,pd.DataFrame]]:
    d=ensure_features(primary).copy().reset_index(drop=True)
    rng=np.random.default_rng(20260910)
    perm=rng.permutation(len(d)); ntest=max(1,int(math.ceil(.20*len(d))))
    test_ix=set(perm[:ntest].tolist())
    r0_test=d.iloc[sorted(test_ix)].copy(); r0_train=d.drop(index=sorted(test_ix)).copy()
    out={"R0_random":(r0_train,r0_test)}
    for z,name in [(20,"R1_Ca"),(50,"R1_Sn"),(28,"R1_Ni"),(82,"R1_Pb")]:
        te=d[d.Z==z].copy(); tr=d[d.Z!=z].copy(); out[name]=(tr,te)
    nr=[];pr=[]
    for z,g in d.groupby("Z"):
        g=g.sort_values("N")
        m=len(g)
        if m<8: continue
        k=max(2,int(math.ceil(.20*m)))
        if m-k<5: continue
        pr.extend(g.index[:k].tolist()); nr.extend(g.index[-k:].tolist())
    out["R2_neutron_rich"]=(d.drop(index=sorted(set(nr))).copy(),d.loc[sorted(set(nr))].copy())
    out["R3_proton_rich"]=(d.drop(index=sorted(set(pr))).copy(),d.loc[sorted(set(pr))].copy())
    mZ=np.min(np.abs(d.Z.to_numpy()[:,None]-np.array([20,28,50,82])[None,:]),axis=1)<=1
    mN=np.min(np.abs(d.N.to_numpy()[:,None]-np.array([20,28,50,82,126])[None,:]),axis=1)<=1
    mask=mZ|mN
    out["R4_magic_pm1"]=(d.loc[~mask].copy(),d.loc[mask].copy())
    for n,name in [(50,"R6_N50"),(82,"R6_N82"),(126,"R6_N126")]:
        te=d[d.N==n].copy(); tr=d[d.N!=n].copy(); out[name]=(tr,te)
    if broad_light is not None and len(broad_light):
        l=ensure_features(broad_light).copy().reset_index(drop=True)
        rng=np.random.default_rng(20260910); perm=rng.permutation(len(l)); nt=max(1,int(math.ceil(.20*len(l))))
        te=l.iloc[perm[:nt]].copy(); tr=l.iloc[perm[nt:]].copy(); out["R7_light_random"]=(tr,te)
    return out

MLP_SEEDS = [211, 307, 401, 503, 607]
LAMBDA_GRID = [i / 10.0 for i in range(11)]


def historical_test(processed: Path, old_v: int, new_v: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return old-vintage primary training data and genuinely-new primary test data in new vintage."""
    train = read_csv_nonempty(processed / f"ame{old_v}_primary_precision.csv")
    if (old_v, new_v) == (2016, 2020):
        membership = read_csv_nonempty(processed / "historical_2016_to_2020_new_primary_LOCKED_CONFIRMATION.csv")
    else:
        membership = read_csv_nonempty(processed / "historical_2012_to_2016_new_primary.csv")
    new = read_csv_nonempty(processed / f"ame{new_v}_primary_precision.csv")
    ids = membership[["N", "Z"]].drop_duplicates()
    test = ids.merge(new, on=["N", "Z"], how="inner", validate="one_to_one")
    return ensure_features(train), ensure_features(test)


def family_predictions(family: str, cfg: dict, train: pd.DataFrame, test: pd.DataFrame,
                       target: str = "B_total_MeV", residual_base_train: np.ndarray | None = None,
                       residual_base_test: np.ndarray | None = None,
                       seeds: list[int] | None = None) -> dict[int, np.ndarray]:
    """Fit one family; MLP returns one prediction vector per frozen seed, deterministic families use key -1."""
    train = ensure_features(train); test = ensure_features(test)
    Xtr = primary_X(train); Xte = primary_X(test)
    y = train[target].to_numpy(float)
    if residual_base_train is not None:
        y = y - np.asarray(residual_base_train, float)
    use_seeds = (seeds or MLP_SEEDS) if family == "mlp" else [-1]
    out = {}
    for seed in use_seeds:
        model = model_from_config(family, cfg, seed=None if seed == -1 else seed)
        model.fit(Xtr, y)
        pred = np.asarray(model.predict(Xte), float)
        if residual_base_test is not None:
            pred = pred + np.asarray(residual_base_test, float)
        out[int(seed)] = pred
    return out


def ensemble_mean(preds: dict[int, np.ndarray]) -> np.ndarray:
    return np.mean(np.vstack(list(preds.values())), axis=0)


def score_prediction_dict(y: np.ndarray, preds: dict[int, np.ndarray]) -> dict:
    per_seed = {str(k): metrics(y, v) for k, v in preds.items()}
    mean_pred = ensemble_mean(preds)
    return {"ensemble": metrics(y, mean_pred), "per_seed": per_seed}


def select_lambda(y: np.ndarray, ml_preds: dict[int, np.ndarray], phys: np.ndarray,
                  grid: list[float] | None = None) -> tuple[float, list[dict]]:
    grid = grid or LAMBDA_GRID
    rows = []
    for lam in grid:
        maes = []
        for p in ml_preds.values():
            blend = (1-lam)*p + lam*phys
            maes.append(metrics(y, blend)["mae"])
        rows.append({"lambda": float(lam), "mean_seed_mae": float(np.mean(maes)), "seed_maes": [float(x) for x in maes]})
    rows.sort(key=lambda r: (r["mean_seed_mae"], r["lambda"]))
    return rows[0]["lambda"], rows


def gate_training_data(family: str, cfg: dict, train: pd.DataFrame, n_splits: int = 5):
    """Construct training-only OOF oracle weights once for the frozen adaptive gate."""
    from sklearn.model_selection import KFold
    d = ensure_features(train).reset_index(drop=True)
    y = d["B_total_MeV"].to_numpy(float)
    ns = min(n_splits, max(2, len(d)//20))
    kf = KFold(n_splits=ns, shuffle=True, random_state=20260910)
    oof_ml = np.full(len(d), np.nan); oof_phys = np.full(len(d), np.nan)
    for tr_ix, va_ix in kf.split(d):
        tr = d.iloc[tr_ix].copy(); va = d.iloc[va_ix].copy()
        sf = fit_semf(tr)
        p_va = semf_predict(va, sf)
        preds = family_predictions(family, cfg, tr, va, seeds=[211] if family == "mlp" else None)
        oof_ml[va_ix] = ensemble_mean(preds)
        oof_phys[va_ix] = p_va
    lam_star = oracle_lambda(y, oof_ml, oof_phys)
    Xg = gate_features(d, d)
    return d, Xg, lam_star


def fit_adaptive_gate(family: str, cfg: dict, train: pd.DataFrame, eval_df: pd.DataFrame,
                      eval_ml: np.ndarray, eval_phys: np.ndarray, gate_alpha: float,
                      n_splits: int = 5) -> tuple[np.ndarray, Ridge]:
    d, Xg, lam_star = gate_training_data(family, cfg, train, n_splits=n_splits)
    gate = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=float(gate_alpha)))])
    gate.fit(Xg, lam_star)
    lam_eval = np.clip(gate.predict(gate_features(eval_df, d)), 0.0, 1.0)
    pred = (1-lam_eval)*np.asarray(eval_ml,float) + lam_eval*np.asarray(eval_phys,float)
    return pred, gate


def select_gate_alpha(family: str, cfg: dict, train: pd.DataFrame, dev_test: pd.DataFrame,
                      dev_ml: np.ndarray, dev_phys: np.ndarray,
                      alphas: list[float] | None = None) -> tuple[float, list[dict]]:
    alphas = alphas or [0.1, 1.0, 10.0]
    y = dev_test["B_total_MeV"].to_numpy(float)
    d, Xg, lam_star = gate_training_data(family, cfg, train)
    Xeval = gate_features(dev_test, d)
    rows=[]
    for a in alphas:
        gate = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=float(a)))])
        gate.fit(Xg, lam_star)
        lam_eval=np.clip(gate.predict(Xeval),0.0,1.0)
        pred=(1-lam_eval)*np.asarray(dev_ml,float)+lam_eval*np.asarray(dev_phys,float)
        rows.append({"alpha":float(a),"mae":float(metrics(y,pred)["mae"])})
    rows.sort(key=lambda r:(r["mae"],r["alpha"]))
    return rows[0]["alpha"],rows


def observable_metrics_from_test(test_pred_df: pd.DataFrame, method_cols: list[str]) -> list[dict]:
    """Strict A8 derived-observable metrics from held-out binding-energy predictions only."""
    base = test_pred_df[["N","Z","A","B_true","is_test",*method_cols]].copy()
    truth = derived_from_predictions(base.rename(columns={"B_true":"Btmp"}), "Btmp", "is_test")
    if truth.empty:
        return []
    truth = truth.rename(columns={c:f"true_{c}" for c in ["Sn","S2n","Sp","S2p","Qalpha","delta2n","delta2p"]})
    out=[]
    for method in method_cols:
        pred = derived_from_predictions(base.rename(columns={method:"Btmp"}), "Btmp", "is_test")
        if pred.empty: continue
        m = truth.merge(pred, on=["N","Z","A"], how="inner")
        for obs in ["Sn","S2n","Sp","S2p","Qalpha","delta2n","delta2p"]:
            met=metrics(m[f"true_{obs}"].to_numpy(float),m[obs].to_numpy(float))
            out.append({"method":method,"observable":obs,**met})
    return out
