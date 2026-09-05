# EMPIRICAL PROTOCOL v0.2 — FROZEN BEFORE FULL AME EVALUATION

**Freeze date:** 2026-08-30  
**Branch:** empirical confirmation of the frozen controlled SEMF trust study  
**Rule:** no final-test retuning after the AME2016→AME2020 confirmation set is materialized.

---

## 1. Central question

How much should machine learning trust an approximate nuclear-physics prior when the prior is imperfect, and how does that trust change with:

1. prior fidelity;
2. nuclear-chart region;
3. extrapolation distance;
4. shell structure and pairing;
5. physics-integration mechanism;
6. predicted observable;
7. uncertainty in fitted physics parameters?

The primary benefit statistic remains

`G = E_data-only / E_physics-guided`,

where `E` is the predeclared error metric for the relevant endpoint. `G>1` means the physics-guided method improves on the paired data-only comparator; `G<1` means it harms.

No numerical value of `G`, no coefficient perturbation size, and no crossover threshold will be treated as universal.

---

## 2. Data sources and primary population

### 2.1 AME2020

Primary source: official Atomic Mass Data Center / IAEA mirror of AME2020 `mass_1.mas20` / `mass_1.mas20.txt`.

Primary citations:

- W. J. Huang et al., Chinese Physics C 45, 030002 (2021), DOI 10.1088/1674-1137/abddb0.
- M. Wang et al., Chinese Physics C 45, 030003 (2021), DOI 10.1088/1674-1137/abddaf.

The AME format marks estimated/non-experimental values with `#`. Such entries are retained by the parser but excluded from the **primary supervised targets**.

### 2.2 Primary precision population

Unless a regime requires a broader sensitivity population, the main empirical population is:

- `Z >= 8` and `N >= 8`;
- AME value is not marked estimated (`#` absent in the relevant target field);
- target is finite;
- mass-excess experimental uncertainty `< 100 keV` when that uncertainty is available and reliably parsed.

This threshold is predeclared because recent open nuclear-mass extrapolation work has used the same high-precision criterion and because it prevents large measurement uncertainties from dominating a study about model trust.

### 2.3 Broad sensitivity population

A secondary sensitivity analysis uses all non-estimated finite AME2020 targets with `Z,N >= 8`, irrespective of the 100 keV precision threshold.

Primary claims must survive qualitatively or any precision-population dependence must be stated explicitly.

---

## 3. Historical development and confirmation

### 3.1 Development historical transition

`AME2012 -> AME2016`

This transition is used for:

- selecting ML hyperparameters;
- selecting the fixed soft-prior weight rule;
- selecting any adaptive-trust model complexity;
- deciding numerical optimization tolerances;
- debugging historical set construction.

### 3.2 Frozen historical confirmation

`AME2016 -> AME2020`

Primary historical-confirmation nuclei are those that:

- are non-estimated/high-confidence in AME2020;
- were not available as non-estimated measured targets in AME2016;
- satisfy the primary domain restrictions.

A secondary **changed-mass** set may contain nuclei present in both evaluations but whose recommended mass changed. It must never be merged silently with genuinely new masses.

### 3.3 Chronology caveat

The 2025 BWN shell-aware formula was developed after AME2020. Therefore:

- it is valid as a strong physics comparator in structured AME2020 holdouts;
- it is **not** a genuinely prospective pre-2020 model;
- BWN results on AME2016→2020 will be labeled a *retrospective historical stress test*, not a prospective prediction claim;
- the historical headline will rely on physics forms whose fitted parameters use the old evaluation only, with the post-2020 formula-form issue stated explicitly.

---

## 4. Frozen evaluation regimes

Every regime constructs its own training and test sets. Overlap between test nuclei across different regimes is allowed because each regime answers a different question, but there is no leakage within a regime.

### R0 — Random interpolation reference

- fixed 20% holdout;
- split seed `20260910`;
- used as a reference only, never as sole evidence of extrapolation.

### R1 — Whole isotopic-chain holdout

Main predeclared chains:

- Ca: `Z=20`;
- Sn: `Z=50`.

Supplementary transfer chains:

- Ni: `Z=28`;
- Pb: `Z=82`.

For a chain test, **all eligible nuclei with that Z are excluded from training**.

### R2 — Neutron-rich frontier

For each proton number Z with at least 8 eligible nuclei:

1. sort eligible nuclei by N;
2. hold out the most neutron-rich `max(2, ceil(0.20*m))` nuclei;
3. require at least five nuclei to remain in training for that Z.

The union of per-Z frontier nuclei forms the test set.

### R3 — Proton-rich frontier

Mirror of R2 using the most proton-rich / smallest-N side of each eligible isotopic chain.

### R4 — Magic-region holdout

Primary shell-closure neighborhoods are bands of width ±1 around conventional closures:

- proton closures: `Z = 20, 28, 50, 82`;
- neutron closures: `N = 20, 28, 50, 82, 126`.

A nucleus is in the primary magic-region test if it lies within ±1 of at least one listed closure. A ±2 band is a predeclared sensitivity analysis.

### R5 — Historical holdout

- development: AME2012→AME2016;
- frozen confirmation: AME2016→AME2020.

### R6 — Isotone holdout (supplementary)

Whole isotone families at `N=50`, `N=82`, and `N=126`, where sufficient measured data exist.

---

## 5. Physics priors

### P0 — Standard interpretable SEMF

Primary five-term form:

`B = a_v A - a_s A^(2/3) - a_c Z(Z-1)/A^(1/3) - a_a (N-Z)^2/A + delta_pair`

with

- `+a_p/sqrt(A)` for even-even nuclei;
- `-a_p/sqrt(A)` for odd-odd nuclei;
- `0` otherwise.

All coefficients are fit **on the regime training set only**.

### P1 — Shell-aware BWN control

Use the functional form published by Wu et al. (Chinese Physics C 49, 114103, 2025; DOI `10.1088/1674-1137/ade954`) together with its erratum/addendum (49, 129001; DOI `10.1088/1674-1137/ae23a6`).

The published BWN form includes bulk, pairing, exchange-Coulomb, curvature, valence-nucleon and exponential shell terms with a region-dependent `delta_shell` factor.

#### Mandatory reproduction gate

Before BWN is allowed into any Paper 3 comparison:

1. implement the published equations exactly;
2. fit/reproduce on the same `Z,N >= 8` AME2020 domain used by Wu et al.;
3. reproduce the published BWN binding-energy RMS of `0.887 MeV` within an absolute tolerance of `0.02 MeV`, or explain any source/version discrepancy;
4. check the erratum/addendum and do not use superseded erroneous numbers;
5. only then refit BWN parameters on each Paper 3 training split.

Published AME2020-fitted BWN coefficients may be used only for this reproduction gate, not as train-split coefficients in holdout tests.

### P2 — External modern mass model

Deferred from the core Stage 2 analysis. At most one external model (FRDM2012 or Duflo–Zuker) may be added later as a **supplementary transfer test**. It will not become a multi-model leaderboard.

---

## 6. ML comparators

The purpose is architecture robustness, not architecture competition.

### M0 — Transparent polynomial ridge

- primary features: `N, Z, A, I=(N-Z)/A, even_N, even_Z`;
- polynomial degree 5;
- ridge alpha selected on AME2012→2016 development from `[1e-4, 1e-3, 1e-2, 1e-1]`.

### M1 — Gradient-boosted trees

Use a compact scikit-learn gradient-boosted tree implementation. Development grid only:

- learning rate: `[0.03, 0.05]`;
- maximum iterations: `[200, 500]`;
- maximum leaf nodes: `[15, 31]`;
- minimum samples per leaf: `[10, 20]`.

### M2 — Compact MLP

Development grid only:

- hidden layers: `[(64,64), (128,64)]`;
- L2 alpha: `[1e-5, 1e-4, 1e-3]`;
- initial learning rate: `[5e-4, 1e-3]`;
- early stopping enabled;
- stochastic seeds: `[211,307,401,503,607]`.

### Physics-feature sensitivity

Magic-distance and collectivity features may be added in a clearly labeled **secondary sensitivity** model. They are excluded from the primary data-only comparator so that the main contrast does not silently inject the shell prior into the supposedly data-only baseline.

---

## 7. Physics-integration mechanisms

### I0 — Physics only

`B_hat = B_physics`

### I1 — Data only

`B_hat = B_ML`

### I2 — Fixed soft prior

`B_hat(lambda) = (1-lambda) B_ML + lambda B_physics`

`lambda` is selected on the AME2012→2016 development transition from

`{0.0, 0.1, ..., 1.0}`

and then frozen before the AME2016→2020 confirmation.

### I3 — Residual repair

`B_hat = B_physics + DeltaB_ML`,

where ML is trained on the physics residual using training nuclei only.

### I4 — Adaptive/local trust (secondary)

A low-complexity gate may learn `lambda(N,Z)` from development/training data only. The gate is constrained to use a small predeclared feature set such as `|I|`, parity, distance to the nearest shell closure, and distance to training support.

This is secondary because local model mixing is established in the literature. Our interpretation is restricted to **trust in one interrogated physics prior**, not a claim that local weighting itself is novel.

### I5 — Oracle trust diagnostic (non-predictive)

An analytical/test-set `lambda*` may be computed only as a **mechanism diagnostic** showing the blend weight that would minimize squared error if test labels were known. It must never be reported as a deployable prediction method.

---

## 8. Empirical physics misspecification

The synthetic percentage ladder remains frozen in v0.1. The empirical branch uses statistically and physically interpretable misspecification.

### A. Parameter misspecification

For P0:

1. fit SEMF coefficients on training data;
2. perform `5000` bootstrap refits to estimate coefficient uncertainty and covariance;
3. perturb each coefficient one at a time by `±1 sigma` and `±2 sigma`;
4. repeat with correlated joint draws from the empirical bootstrap covariance.

Because liquid-drop parameters can be strongly correlated, marginal perturbations and joint-covariance perturbations are reported separately.

### B. Model-form misspecification

Predeclared controls:

- remove pairing from P0;
- compare bare P0 with shell-aware P1;
- suppress the explicit BWN shell term after the BWN reproduction gate;
- optionally attenuate the BWN shell amplitude continuously for a shell-fidelity curve.

### C. Term-specific sensitivity

For P0, quantify change in `G` under perturbation of:

- volume coefficient `a_v`;
- surface coefficient `a_s`;
- Coulomb coefficient `a_c`;
- asymmetry coefficient `a_a`;
- pairing coefficient `a_p`.

The aim is mechanistic interpretation, not estimation of nuclear-matter constants.

---

## 9. Endpoints

### Primary

- total binding-energy MAE (MeV);
- total binding-energy RMSE (MeV);
- `G` using MAE as the headline ratio unless otherwise stated.

### Secondary global

- bias;
- median absolute error;
- 95th percentile absolute error;
- mass-excess error where conversion is unambiguous.

### Derived nuclear observables

From predicted binding energies, where all required neighboring nuclei are available:

- `S_n`;
- `S_2n`;
- `S_p`;
- `S_2p`;
- `Q_alpha`;
- two-neutron and two-proton shell gaps.

Odd-even staggering indicators may be added only after their exact sign convention is sourced and frozen in the analysis note; they are not required for the first confirmatory pass.

---

## 10. Predeclared real-nucleus case studies

Case studies are selected **before** viewing their Paper 3 prediction errors.

### C1 — Ca isotopic chain

- whole-chain holdout, `Z=20`;
- purpose: shell closure at `N=28`, pairing, and separation-energy behavior.

### C2 — Sn isotopic chain

- whole-chain holdout, `Z=50`;
- purpose: long chain, `N=82` closure, neutron-rich extrapolation, `132Sn`.

### C3 — `132Sn` neighborhood

- evaluated inside the magic-region protocol rather than fitted locally;
- purpose: doubly magic + neutron-rich tension between smooth bulk physics and local shell correction.

### C4 — `208Pb` neighborhood

- evaluated inside the magic-region protocol;
- purpose: heavy doubly magic case with large Coulomb contribution and shell closure.

### C5 — `100Sn` neighborhood (supplementary)

- proton-rich doubly magic counterpart to `132Sn` where data quality permits.

These examples illustrate global findings; they do not define the headline conclusion.

---

## 11. Statistical uncertainty

For every primary model comparison:

- paired nucleus-level bootstrap: `5000` resamples;
- 95% percentile confidence interval for MAE difference and `G`;
- chain-block bootstrap by proton number Z as a dependence-aware sensitivity analysis for global regimes;
- report the fraction of stochastic seeds with `G>1` where applicable.

For physics-parameter uncertainty:

- `5000` bootstrap SEMF refits;
- retain full coefficient covariance, not only marginal standard errors.

---

## 12. No-retuning and stopping rules

1. AME2012→2016 is the development historical transition.
2. Model grids and integration rules are selected there.
3. The AME2016→2020 new-mass confirmation is evaluated once after freezing.
4. A poor or null result is reported; it does not trigger a new hyperparameter search.
5. Structured AME2020 regimes may be analyzed in depth after the historical confirmation, but their test labels may not be used to redesign the historical model.
6. BWN cannot be used until its reproduction gate passes.
7. Any post hoc exploratory model is labeled exploratory and separated from confirmatory tables.

---

## 13. Claim boundary

A successful empirical paper may support a statement of the form:

> The value of an approximate nuclear-physics prior depends jointly on its fidelity, the nuclear-chart region, extrapolation difficulty, observable, and integration mechanism; global accuracy alone is not sufficient to determine how strongly the prior should be trusted.

The study will **not** claim:

- a universal SEMF trust threshold;
- a new state-of-the-art nuclear mass model;
- extraction of fundamental nuclear-matter parameters from the ML sensitivity experiment;
- genuine prospective performance for a model form that was designed using later AME knowledge;
- that local/adaptive weighting itself is a novel concept.

