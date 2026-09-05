# Theory integration note - Cappellaro, *Introduction to Applied Nuclear Physics*

## Source
Paola Cappellaro, Massachusetts Institute of Technology, *Introduction to Applied Nuclear Physics*, MIT OpenCourseWare / LibreTexts compilation (source PDF supplied to this project on 2026-08-31).

## Why this source matters for this Paper
The source gives an unusually clean theoretical bridge between the macroscopic semi-empirical mass formula (SEMF) and the local structural observables used in this Paper.

### 1. Binding energy is a bulk observable; separation energies probe local structure
On PDF pp. 10-11, the text introduces binding energy and neutron/proton separation energies, explicitly noting that separation energies show signatures of nuclear shell structure. This supports the Paper choice not to judge a physics prior only by total binding-energy MAE.

**Paper consequence:** evaluate the same predictions at multiple physical resolutions:
`B -> B/A -> Sn, S2n, Sp, S2p -> delta2n, delta2p`.
A prior may reproduce the smooth bulk energy while missing local shell curvature.

### 2. The SEMF is deliberately smooth and macroscopic
PDF pp. 11-13 describe the liquid-drop interpretation and the volume, surface, Coulomb, symmetry, and pairing terms. The source emphasizes short-range nuclear saturation for the volume term, reduced coordination at the surface, proton-proton Coulomb repulsion, symmetry/exclusion effects, and pairing.

**Paper consequence:** the five coefficients are not just generic regression parameters. Their perturbations have distinct physical interpretations, making coefficient-specific trust curves scientifically meaningful.

### 3. Two-nucleon separation energies are direct shell evidence
In the nuclear-model discussion (PDF p. 88), the source labels two-nucleon separation energy as evidence of nuclear shell structure and connects the observed discontinuities with magic numbers.

**Paper consequence:** `S2n`, `S2p`, and shell-gap indicators are central rather than decorative secondary metrics. They test whether a model that is numerically good in `B` has captured structural changes at closures.

### 4. Magic numbers require shell physics beyond a simple drop
PDF pp. 88-94 develops the shell-model argument and spin-orbit splitting that reproduces the standard closures. The treatment reinforces the conceptual distinction between a smooth macroscopic prior and local quantal shell structure.

**Paper consequence:** the magic-region holdout is not defined as a region where SEMF must have the largest total-mass error. It is defined as a region where the *structural content* of the prior is most strongly interrogated.

### 5. Collective physics provides a second failure mode
PDF p. 95 notes that more complex nuclear structure can require collective descriptions involving vibrations and rotations rather than a single-particle picture.

**Paper consequence:** residual structure away from magic numbers should not automatically be called 'shell error'. The discussion should distinguish at least shell, pairing, deformation/collective, and remaining correlations as possible contributors to the learned residual.

## Final theoretical framing strengthened by this source
This Paper should state the problem as:

> The usefulness of an approximate nuclear-physics prior cannot be inferred from its global binding-energy accuracy alone. The same prior can be adequate for smooth bulk energetics yet structurally incomplete for local observables that expose shell closures, pairing, or collective correlations. Therefore physics trust must be tested as a function of observable, nuclear-chart region, extrapolation difficulty, prior fidelity, and integration mechanism.

## Figure implications
The source also motivates the predeclared term-build-up visualization: volume -> surface -> Coulomb -> asymmetry -> pairing. This paper will use that concept quantitatively on the AME population, while the novelty claim remains the ML physics-trust analysis rather than the visualization itself.
