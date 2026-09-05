# Protocol Implementation Note A7 - Autonomous Modeling Decisions

**Freeze date:** 2026-08-31
**Status:** PRE-RESULT implementation freeze
**Parent:** EMPIRICAL_PROTOCOL_v0.2 + Amendments A1-A3 + Notes A4-A6

This note resolves computational details required to execute the remaining stages without using AME2016->AME2020 confirmation outcomes for tuning.

## A7.1 Development target and scoring
All model selection uses only the AME2012->AME2016 `new_primary` historical transition. Total binding energy `B_total_MeV` is the development target. The primary selection metric is MAE; RMSE is retained as a secondary tie-breaker. Ties within 1e-12 MAE are resolved by the simpler/lower-complexity setting in deterministic grid order.

## A7.2 Ridge implementation
M0 uses `PolynomialFeatures(degree=5, include_bias=False)` on the frozen primary features `N,Z,A,I,even_N,even_Z`, followed by `StandardScaler` and `Ridge`. The alpha grid remains exactly `[1e-4,1e-3,1e-2,1e-1]`.

## A7.3 Boosted-tree implementation
M1 is `HistGradientBoostingRegressor` with the frozen grid:
- learning_rate `[0.03,0.05]`;
- max_iter `[200,500]`;
- max_leaf_nodes `[15,31]`;
- min_samples_leaf `[10,20]`;
- l2_regularization `0`;
- random_state `20260910`.

## A7.4 MLP implementation
M2 is `StandardScaler` + `MLPRegressor` with the frozen grids and seeds in v0.2. `max_iter=4000`, `early_stopping=True`, `validation_fraction=0.15`, `n_iter_no_change=80`, and `tol=1e-6`. The development score for a hyperparameter combination is the mean MAE over the five frozen seeds.

## A7.5 Integration mechanism isolation
ML hyperparameters are selected using the data-only development task and are then held fixed when the same family is used for residual repair. This prevents the comparison between I1 and I3 from becoming a second architecture search.

For fixed soft priors (I2), lambda is selected separately for each ML family using only AME2012->AME2016 from `{0.0,0.1,...,1.0}`.

## A7.6 Adaptive/local trust
I4 remains secondary. It uses a linear Ridge gate trained to predict a clipped oracle blend weight on out-of-fold development-training predictions. Gate features are:
- `abs(I)`;
- `even_N`, `even_Z`;
- distance to nearest conventional neutron magic number;
- distance to nearest conventional proton magic number;
- Manhattan distance in `(N,Z)` to the nearest training nucleus.

Gate alpha is selected on AME2012->AME2016 from `[0.1,1.0,10.0]`. Final gate outputs are clipped to `[0,1]`.

## A7.7 Randomness
All random-interpolation splits use seed `20260910`. Non-ML bootstraps use seed `20260911`; chain-block bootstraps use `20260912`; SEMF coefficient bootstrap uses `20260913`. No seed is changed after confirmation is opened.

## A7.8 Confirmation protection
Stage 3C writes a canonical JSON development freeze and SHA-256 digest. Stage 3E refuses to score AME2016->AME2020 unless that freeze exists. On first scoring it writes a non-overwritable confirmation-opened marker containing the freeze digest and input-data hashes. Reruns are allowed only as exact reproducibility reruns with the same freeze digest and same input hashes; they cannot trigger tuning.
