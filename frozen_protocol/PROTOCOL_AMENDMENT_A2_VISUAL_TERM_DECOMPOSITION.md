# Protocol Amendment A2 — Term-Resolved and Visual Physics-Trust Diagnostics

**Branch:** Paper 3 empirical SEMF trust study
**Status:** PRE-EVALUATION AMENDMENT
**Date:** 2026-08-30

## Purpose
This amendment adds a predeclared visualization and term-decomposition layer inspired by the open-access SEMF visualization work of Hein, Pusch, and Heusler (Eur. J. Phys. 43, 035801, 2022) and its companion SEMF video page. It does not alter the frozen primary training/test regimes, primary metric, model families, or confirmation chronology.

## A2.1 Sequential SEMF build-up
For each evaluated nucleus, compute cumulative predictions after adding the standard SEMF terms in the following physical order:

1. volume term only;
2. + surface term;
3. + Coulomb term;
4. + asymmetry term;
5. + pairing term.

The purpose is diagnostic, not to claim that this order is a unique derivation of the model.

For every cumulative stage, report at minimum:
- binding-energy residual `B_exp - B_stage`;
- binding-energy-per-nucleon residual `(B_exp-B_stage)/A`;
- MAE and RMSE on each frozen evaluation regime.

## A2.2 Term-removal diagnostics
In addition to the coefficient perturbation experiments already frozen, evaluate one-at-a-time model-form ablations:
- full SEMF minus pairing;
- full SEMF minus asymmetry;
- full SEMF minus Coulomb;
- full SEMF minus surface.

The volume-only omission is not used as a primary ablation because it changes the scale of the model too drastically; it may be shown only as an educational/diagnostic control.

## A2.3 Observable-resolved trust maps
For each predeclared observable `O`, where supported by neighboring measured/predicted nuclei, compute a local or binned trust statistic

`G_O = E_data-only(O) / E_physics-guided(O)`

for:
- `B`;
- `B/A`;
- `S_n`;
- `S_2n`;
- `S_p`;
- `S_2p`;
- `Q_alpha`;
- two-neutron and two-proton shell-gap indicators.

No local map will replace the predeclared aggregate metrics. Maps are explanatory diagnostics.

## A2.4 Main-paper visualization family
Predeclare the following main-paper figures, subject to data availability and legibility:

### Figure V1 — SEMF term build-up
A five-stage sequence showing how the nuclear-chart residual landscape changes as volume, surface, Coulomb, asymmetry, and pairing terms are introduced.

### Figure V2 — Experimental-minus-SEMF landscape
A nuclear-chart map of `B_exp/A - B_SEMF/A`, with conventional shell closures overlaid. This is the direct conceptual bridge to Hein et al. but uses the Paper 3 empirical population and fitting protocol.

### Figure V3 — Observable-dependent trust
Matched panels for `G_B`, `G_S2n`, and `G_delta2n` (or the closest shell-gap endpoint supported by the data).

### Figure V4 — Out-of-sample Sn-chain case study
Whole-chain holdout predictions for binding-energy residuals and `S_2n`, with the `N=82` closure marked.

### Figure V5 — Term-specific sensitivity by region
Effect of perturbing or removing each SEMF term across interpolation, neutron-rich, proton-rich, magic-region, and light-nucleus regimes.

## A2.5 Supplementary animation
If journal supplementary media are practical, generate an MP4/GIF showing:
1. cumulative SEMF term build-up;
2. transition from SEMF prediction to experimental residual landscape;
3. optional transition between `G_B`, `G_S2n`, and shell-gap trust maps.

This animation is supplementary communication only. No scientific claim depends on it.

## A2.6 Plot-style rule
Every multi-series line plot must distinguish series simultaneously by:
- different color;
- different line style;
- different marker shape.

## A2.7 Claim boundary
The visual comparison must not imply that low `B/A` residual at a magic nucleus proves the SEMF contains shell physics. The explicit test is whether bulk agreement coexists with disagreement in shell-sensitive observables.

## A2.8 No post-hoc selection
The specific Ca, Sn, 132Sn, 208Pb, and supplementary 100Sn examples remain those already predeclared. No new nucleus may be promoted to a headline case because it produces a visually striking result after evaluation.
