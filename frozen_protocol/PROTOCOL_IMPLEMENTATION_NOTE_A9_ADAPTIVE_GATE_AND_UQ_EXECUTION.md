# Protocol Implementation Note A9 - Adaptive Gate Execution and Correlated-Draw Count

**Freeze date:** 2026-08-31  
**Status:** PRE-RESULT implementation freeze

This note resolves computational details left open by v0.2/A7 without changing any scientific endpoint or development-confirmation boundary.

## A9.1 Adaptive gate OOF stochastic convention
For MLP-based adaptive trust, the training-only out-of-fold predictions used to construct the gate target use the canonical frozen MLP seed `211` only. The final MLP data-only, fixed-soft-prior, and residual-repair predictions continue to be evaluated over all five frozen seeds `211, 307, 401, 503, 607` and by their ensemble mean. This prevents the secondary adaptive gate from multiplying the computational budget by five while preserving the predeclared stochastic robustness assessment for the primary ML comparisons.

The gate itself remains a standardized ridge regressor on the A7 feature set with alpha selected only on AME2012->AME2016 development from `[0.1, 1.0, 10.0]` and then frozen.

## A9.2 Correlated SEMF misspecification draws
The empirical correlated-joint coefficient perturbation analysis uses `1000` multivariate draws from the 5000-refit bootstrap coefficient covariance. The 5000 bootstrap refits remain the coefficient-uncertainty reference; the 1000 correlated draws are a downstream sensitivity sample, not a replacement.

## A9.3 BWN scope
After the mandatory published-form reproduction gate passes, train-split BWN refits are included for the core structured regimes `R0`, `R1-Ca`, `R1-Sn`, `R2`, `R3`, and `R4`. Ni/Pb transfer chains, isotones, broad-population repeats, and R7 remain supplementary P0/ML analyses unless BWN compute time is explicitly available. This avoids turning the paper into a mass-model leaderboard.
