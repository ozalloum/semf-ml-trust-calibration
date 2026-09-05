# Protocol Implementation Note A13 - Predeclared Completeness Execution

**Execution date:** 2026-08-31  
**Status:** POST-CONFIRMATION REPORTING/DIAGNOSTIC COMPLETENESS NOTE  
**Scope:** frozen Amendments A1-A3 only; no model selection, split, hyperparameter, seed, or confirmation decision is changed.

## Reason

A protocol-to-code audit performed after Stage 3G identified that the autonomous Stage 3H reporting script did not materialize every diagnostic that had already been predeclared before empirical evaluation. Specifically, A1 required binding energy per nucleon (`B/A`) in the observable trust vector, A2 required cumulative SEMF term build-up and one-term-removal diagnostics, and A3 required calibration-domain/conditioning visual diagnostics.

These omissions concern **reporting and diagnostic execution only**. The one-time AME2016->AME2020 confirmation has already been completed and locked. This note does not reopen or rescore that confirmation with altered models.

## Frozen execution interpretations

1. **B/A:** For every already-generated held-out binding-energy prediction, `B/A` is obtained by dividing both truth and prediction by the same mass number `A`. No model is refit.
2. **Sequential SEMF build-up:** Fit the full five-term P0 SEMF on each regime training split exactly as already specified. Evaluate cumulative contributions in the predeclared order volume -> surface -> Coulomb -> asymmetry -> pairing, using the coefficients of that same full training-only fit. This is a decomposition diagnostic, not a sequence of newly optimized models.
3. **Term-removal diagnostics:** For each required omission (pairing, asymmetry, Coulomb, surface), remove the corresponding design column and refit the remaining SEMF coefficients by ordinary least squares on the same training split, then evaluate the unchanged held-out test split. This mirrors the already-executed no-pairing model-form control and isolates the effect of removing one model term while allowing the remaining coefficients to readjust.
4. **Historical observable trust:** The already-frozen 2012->2016 development transition and one-time 2016->2020 confirmation predictions are used without refitting. Derived observables continue to obey A8: every required neighbor must itself be held out in the same transition; unavailable values remain `NA`.
5. **Chart-resolved diagnostic maps:** A full-AME2020 P0 fit may be used only for descriptive residual landscapes after the historical confirmation is closed. Such maps are diagnostic visualizations and are not historical prediction results.
6. **Natural prior aging:** `G_vintage` is reported only on the chronology-respecting transitions explicitly defined in A3.5. A3.9's wording about interpolation/frontier/magic panels is not used to invent a new post-hoc aged-prior experiment on structured AME2020 splits.
7. **Single-chain block bootstrap:** When a whole-chain holdout contains only one isotope chain, a chain-block bootstrap is degenerate by construction; such intervals are not interpreted as dependence-robust uncertainty estimates.
8. **Ridge fixed-soft null:** The frozen development selected `lambda=0` for ridge fixed-soft integration. Therefore ridge fixed-soft misspecification curves are identically data-only and are retained as a null diagnostic rather than retuned after confirmation.

## Claim boundary

Results produced under A13 may complete predeclared tables/figures and strengthen traceability, but they may not be used to alter the frozen model configuration, select a different regime, or rerun the one-time AME2020 confirmation.
