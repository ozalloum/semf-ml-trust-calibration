# BWN 2025 reproduction and positioning note

## Citation
Wu et al., "Improvement of nuclear semi-empirical mass formula by including shell effect," *Chinese Physics C* 49, 114103 (2025), DOI: 10.1088/1674-1137/ade954, with erratum DOI: 10.1088/1674-1137/ae23a6.

## Published domain and accuracy
The paper reports a BWN binding-energy RMS deviation of 0.887 MeV for experimental AME2020 nuclei with Z,N >= 8. It reports 0.381 MeV for one-neutron separation energy and 0.394 MeV for one-proton separation energy.

## Exact role in Paper 3
BWN is a **stronger shell-aware physics control**, not the Paper 3 novelty and not a new leaderboard target. Paper 3 uses it to ask whether conclusions about physics trust survive when the prior contains explicit shell-aware structure.

The mandatory gate is frozen before use:
1. implement the published equations;
2. reproduce the 0.887 MeV AME2020 binding-energy RMS within 0.02 MeV;
3. consult the erratum;
4. only after a PASS, refit BWN on each train split for structured holdouts.

The published AME2020-fitted coefficients are used only for the reproduction gate. They are never imported into a holdout fit.

## Historical chronology boundary
Because the BWN form was developed after AME2020, any AME2016->AME2020 BWN result is labeled a **retrospective historical stress test**, not prospective prediction. The historical headline must use physics forms whose fitted parameters and model choices respect the old-evaluation information boundary.

## Formula implementation audit
`code/bwn.py` implements the published BWN expression, including:
- Z^2 Coulomb convention used by BWN;
- isospin-dependent symmetry coefficient;
- A^(-1/3) pairing term with the published delta_np rule;
- exchange-Coulomb and curvature terms;
- valence-nucleon P and linear terms;
- region-dependent delta_shell multiplying the exponential shell correction;
- published magic-number sets through neutron N=184.

The implementation intentionally remains separate from the primary five-term P0 SEMF because the two models use different functional conventions.
