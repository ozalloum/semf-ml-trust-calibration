# Paper 3 Empirical Protocol Amendment A1
## Observable-dependent physics trust and model-validity stress tests

**Date:** 2026-08-30  
**Applies to:** `EMPIRICAL_PROTOCOL_v0_2`  
**Status:** PRE-EVALUATION AMENDMENT  
**Reason:** incorporation of Hein, Pusch & Heusler, *European Journal of Physics* 43, 035801 (2022), DOI 10.1088/1361-6404/ac4d7c, before full AME empirical evaluation.

## A1.1 Preservation rule

The original `EMPIRICAL_PROTOCOL_v0_2` remains unchanged and is retained verbatim in this package. This amendment does not replace the frozen record; it documents a scientifically motivated refinement made **before** inspection of Paper 3 empirical prediction errors or the AME2016->AME2020 confirmation results.

No model hyperparameter, split rule, seed, bootstrap count, or historical no-retuning rule is relaxed by this amendment.

## A1.2 Key conceptual correction

The empirical study must not assume that magic nuclei are automatically the worst cases for SEMF binding-energy error.

Hein et al. compare experimental and SEMF binding energies per nucleon through a difference landscape and report two relevant observations:

1. deviations are especially large for small-A nuclei, where basic liquid-drop assumptions become questionable;
2. the binding-energy-per-nucleon difference can become small at magic and doubly-magic nuclei even though explicit shell structure is absent from the liquid-drop SEMF.

Therefore the magic-region experiment is reformulated as a **non-directional test**:

> Does a physics prior that is numerically accurate in a bulk observable also preserve local shell-sensitive observables, and does the answer depend on the way physics is integrated with ML?

The paper must distinguish **numerical agreement** from **physical/structural fidelity**.

## A1.3 Observable hierarchy

The following hierarchy is added to the empirical analysis. The total binding-energy endpoint remains the primary headline endpoint, so this amendment does not move the primary goalpost.

### O1 — Total binding energy

- `B` MAE and RMSE in MeV.
- `G_B = E_data-only(B) / E_physics-guided(B)`.

### O2 — Binding energy per nucleon

- `B/A` MAE and RMSE in MeV per nucleon.
- `G_BA = E_data-only(B/A) / E_physics-guided(B/A)`.
- This endpoint directly connects the empirical study to the difference-energy landscape discussed by Hein et al.

### O3 — One- and two-nucleon separation energies

Where all required neighboring nuclei exist in the same eligible evaluation population:

- `S_n`, `S_2n`, `S_p`, `S_2p`;
- paired MAE/RMSE and endpoint-specific `G` values.

### O4 — Shell-sensitive local differences

Two-neutron and two-proton shell-gap diagnostics remain predeclared. Their exact sign convention must be sourced and frozen in the analysis implementation note **before computation**. The convention may not be changed after inspecting results.

### O5 — Q-alpha

`Q_alpha` remains a secondary derived endpoint where all required masses are available.

## A1.4 Observable-dependent trust matrix

For every major regime and integration mechanism, report a compact trust vector:

`T = (G_B, G_BA, G_Sn, G_S2n, G_Sp, G_S2p, G_shell, G_Qalpha)`

with unavailable components explicitly marked `NA` rather than imputed.

A change in sign around `G=1` across observables is a scientific result, not an inconsistency. In particular, the analysis will test whether the same prior can:

- improve `B` or `B/A`, yet
- harm `S_2n` or a shell-gap endpoint,

or the reverse.

No claim of "physics helps" or "physics hurts" may be made without naming the observable.

## A1.5 Revised magic-region interpretation

The existing R4 magic-region holdout is retained exactly:

- proton closures: `Z = 20, 28, 50, 82`;
- neutron closures: `N = 20, 28, 50, 82, 126`;
- primary band: +/-1;
- sensitivity band: +/-2.

However, the directional hypothesis is now explicitly neutral:

- do **not** predict in advance that bare SEMF must have larger `B` or `B/A` error in the magic region;
- test whether shell-aware physics changes **local derivative observables** more strongly than global binding observables;
- distinguish a prior that matches a magic nucleus numerically from one that reproduces the surrounding isotopic/isotonic structure.

## A1.6 New R7 — light-nucleus model-validity stress test

A new **supplementary** regime is added to probe the domain where liquid-drop assumptions are least secure.

This regime is not part of the primary `Z,N >= 8` precision population and cannot replace any primary result.

### Population

Use measured, finite, non-estimated AME entries satisfying:

- `Z >= 2`, `N >= 2`;
- experimental target present;
- no `#` estimate marker in the target field.

### Predeclared mass-number strata

- `A < 20` — very-light stress stratum;
- `20 <= A < 40` — light transition stratum;
- `A >= 40` — comparison stratum within this supplementary analysis.

The cut points are analysis conventions chosen before model errors are viewed and must not be interpreted as sharp physical validity boundaries.

### Purpose

Test whether physics guidance becomes less useful or more fragile when the assumptions underlying a smooth liquid-drop description are weakest.

The result is descriptive/supplementary unless it reproduces across AME versions and model families.

## A1.7 Case-study amendments

The predeclared cases remain fixed; their interpretation is refined.

### C1 — Ca chain

Add `B/A` and shell-sensitive local differences to the existing `B`, `S_n`, and `S_2n` analysis around `N=20` and `N=28` where available.

### C2 — Sn chain

Use the full out-of-sample chain to contrast bulk `B`/`B/A` behavior with `S_2n` and shell-sensitive behavior near `N=82`.

### C3 — 132Sn neighborhood

Do not frame this case as "SEMF must fail badly in total binding energy." Instead test:

> Can a smooth SEMF prior show small bulk binding error while failing to encode the local shell structure around a doubly-magic neutron-rich nucleus?

### C4 — 208Pb neighborhood

Apply the same bulk-versus-local distinction in a heavy doubly-magic region with a large Coulomb contribution.

### C5 — 100Sn neighborhood

Retain as supplementary proton-rich counterpart where data quality allows.

### C6 — light-nucleus regional case study

Add a regional, non-cherry-picked visualization of the R7 `A<20` stratum. No single light nucleus may be promoted to a headline example based on having a visually large error.

## A1.8 Figure plan added before evaluation

### F1 — Experimental-minus-SEMF landscape

A nuclear-chart map of `B_exp/A - B_SEMF/A` for eligible measured nuclei. This is a quantitative research analogue of the difference-energy landscape concept, not a reproduction of Hein et al.'s teaching visualization.

### F2 — Observable-dependent trust map

For selected models/integration mechanisms, show chart-resolved trust or paired error difference for `B` and `S_2n` in separate panels.

### F3 — Sn chain case study

Out-of-sample predictions along the Sn isotopic chain showing at minimum:

- `B` or residual in `B`;
- `B/A` or residual in `B/A`;
- `S_2n`;
- shell-sensitive diagnostic once its convention is frozen.

### F4 — Light-nucleus stress figure

Error/trust versus `A` for the supplementary R7 population, with the predeclared mass-number strata shown.

All multi-series plots must use distinct color, line style, and marker combinations.

## A1.9 Claim-boundary addition

The final paper may support a stronger, observable-specific statement only if the empirical results do so:

> Global numerical agreement of a nuclear-physics prior is not sufficient to determine its usefulness for all derived observables; physics trust can vary between bulk binding quantities and local shell-sensitive quantities even for the same nuclei.

The paper must not claim:

- that magic numbers necessarily maximize SEMF mass error;
- that a small `B` or `B/A` error proves shell physics is represented correctly;
- that the `A<20` analysis defines a universal liquid-drop breakdown threshold.

## A1.10 Status after amendment

The protocol remains safe to proceed to data materialization and the BWN reproduction gate. No empirical Paper 3 prediction result has been used to formulate this amendment.
