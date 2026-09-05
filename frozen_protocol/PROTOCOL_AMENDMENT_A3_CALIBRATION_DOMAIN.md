# Protocol Amendment A3 - Calibration Domain and Coefficient Drift

**Date frozen:** 2026-08-30  
**Status:** pre-AME empirical evaluation amendment  
**Parent:** EMPIRICAL_PROTOCOL_v0.2 + Amendments A1-A2  

## Rationale

Recent SEMF coefficient-update studies show that fitted Bethe-Weizsaecker coefficients depend on both the AME vintage and the population used for calibration. Gjorgievska et al. (Nuclear Engineering and Design 426, 113403, 2024; DOI 10.1016/j.nucengdes.2024.113403) fit the five-term formula to AME2020 and report separate fits for all nuclei and for A >= 50, with 95% confidence intervals. Benzaid et al. (Nuclear Science and Techniques 31, 9, 2020; DOI 10.1007/s41365-019-0718-8) likewise report materially different coefficient sets for all AME2016 nuclei and for A >= 50. Kirson (Nuclear Physics A 798, 29-60, 2008; DOI 10.1016/j.nuclphysa.2007.10.011) shows that mass-formula terms can be mutually correlated and that nominal fit errors may understate coefficient uncertainty.

This amendment therefore separates four distinct sources of physics-prior imperfection:

1. **parameter estimation uncertainty** within a fixed training population;
2. **calibration-domain shift** (for example all A versus A >= 50);
3. **evaluation-vintage drift** (AME2012 -> AME2016 -> AME2020);
4. **model-form error** (for example missing pairing or missing shell structure).

No existing headline endpoint or frozen split is changed.

## A3.1 Primary SEMF fit remains unchanged

The primary P0 prior remains the five-term SEMF fitted by ordinary least squares on the training nuclei available within each frozen regime:

B = a_v A - a_s A^(2/3) - a_c Z(Z-1)/A^(1/3) - a_a (N-Z)^2/A + delta_pair,

with delta_pair = +a_p/sqrt(A) for even-even, -a_p/sqrt(A) for odd-odd, and 0 otherwise.

The primary result is therefore not replaced by a literature coefficient table and is never fit on a test set.

## A3.2 Formula-convention gate

Published SEMF coefficients are **not directly interchangeable**. Before reproducing or comparing a published coefficient set, record at minimum:

- Coulomb form: Z^2 or Z(Z-1);
- pairing exponent and parity convention;
- whether atomic or nuclear binding energy is fit;
- inclusion/exclusion of electron binding corrections;
- data domain (all A, A >= 50, Z/N restrictions);
- treatment of estimated (`#`) AME entries;
- least-squares weighting rule.

Coefficient magnitudes may only be compared directly when conventions are equivalent or after an explicit conversion/re-fit.

## A3.3 Calibration-domain sensitivity (secondary)

For each AME vintage used in development/confirmation, fit the same P0 functional form under the following calibration domains using training data only:

- **D0 - Primary:** the frozen eligible training population for that regime;
- **D1 - Heavy-only:** A >= 50, evaluated only where the test target also satisfies A >= 50;
- **D2 - Broad measured:** all non-estimated finite targets satisfying Z,N >= 8, irrespective of the 100-keV precision cut;
- **D3 - Primary precision:** non-estimated targets satisfying Z,N >= 8 and the frozen <100-keV uncertainty rule.

D0 remains the headline fit. D1-D3 are sensitivity analyses and cannot replace D0 after test inspection.

## A3.4 Chronological coefficient drift

Fit the P0 coefficient vector separately on chronologically available data:

- theta_2012 from AME2012 training data;
- theta_2016 from AME2016 training data;
- theta_2020 from AME2020 only after the historical AME2016->AME2020 confirmation has been opened and scored.

For each adjacent vintage, report:

- absolute coefficient change;
- fractional coefficient change;
- change relative to the older-fit bootstrap standard deviation;
- Mahalanobis distance using the older-fit bootstrap covariance, when numerically stable.

The AME2020-fit coefficient vector is **diagnostic only** for the historical AME2016->AME2020 experiment and may not be used to generate its predictions.

## A3.5 Natural misspecification experiment

In addition to synthetic +/-1 sigma and +/-2 sigma perturbations, define a chronology-respecting natural misspecification:

- use theta_2012 as the physics prior for AME2016-new nuclei;
- use theta_2016 as the physics prior for AME2020-new nuclei.

This tests a realistic form of prior aging: the physics functional form is unchanged, but its empirically calibrated coefficients come from an older mass evaluation.

The resulting trust ratio is denoted G_vintage(O) for observable O.

## A3.6 Identifiability diagnostics

For every SEMF fit used in a headline comparison, save:

- design-matrix rank;
- singular values;
- 2-norm condition number;
- coefficient covariance/correlation matrix from the paired bootstrap;
- coefficient bootstrap intervals.

If the design matrix is ill-conditioned, report this explicitly. The paper will not interpret fitted coefficients as precise nuclear-matter constants.

## A3.7 Fit uncertainty

The existing 5000 bootstrap refits remain the primary coefficient-uncertainty procedure. Standard OLS covariance is retained only as a computational diagnostic.

Because neighboring nuclei are structurally related, a secondary chain-block bootstrap may be used to test whether nucleus-wise resampling understates coefficient uncertainty.

## A3.8 Metrics

The paper may reproduce literature-style percentage error for context, but the Paper 3 headline remains:

- MAE in MeV;
- RMSE in MeV;
- G = E_data-only / E_physics-guided.

Percentage error will not replace these endpoints because total binding energy scales strongly with A.

## A3.9 New figures

Predeclared figures/supplement panels:

1. **Coefficient evolution plot:** a_v, a_s, a_c, a_a, a_p across AME2012, AME2016, AME2020 with bootstrap 95% intervals.
2. **Calibration-domain plot:** D0 versus D1-D3 coefficient estimates.
3. **Coefficient-correlation heat map:** bootstrap correlation matrix for each AME vintage.
4. **Natural prior-aging trust plot:** G_vintage across interpolation, frontier, magic-region, and observable families.
5. **Conditioning diagnostic:** singular-value spectrum or condition number in supplementary material.

All multi-series line figures must distinguish series using different colors, line styles, and markers.

## A3.10 Claims allowed / forbidden

Allowed if supported:

- SEMF trust changes when coefficients are calibrated on a different nuclear population or older mass evaluation;
- some apparent prior misspecification can arise from calibration drift rather than missing physical terms;
- coefficient uncertainty and coefficient correlation affect how a numerical 'physics error' should be interpreted.

Forbidden:

- treating AME-vintage coefficient drift as a change in fundamental nuclear constants;
- claiming a coefficient set is universally best;
- using AME2020-calibrated coefficients in the untouched AME2016->AME2020 historical prediction;
- comparing published coefficient numbers without matching formula conventions.
