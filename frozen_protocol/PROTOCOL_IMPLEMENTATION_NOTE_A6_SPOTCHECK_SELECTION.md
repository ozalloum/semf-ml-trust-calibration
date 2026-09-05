# Protocol Implementation Note A6 - Independent Spot-Check Selection

**Freeze date:** 2026-08-31  
**Status:** pre-data / pre-model implementation rule

Stage 3A required independent data-engineering spot checks against NNDC NuDat (and optionally KAERI), including 48Ca, 100Sn, 132Sn and 208Pb where available, plus two deterministic mid-shell nuclei.

## Fixed anchors
- 48Ca: N=28, Z=20
- 100Sn: N=50, Z=50
- 132Sn: N=82, Z=50
- 208Pb: N=126, Z=82

If an anchor is estimated rather than measured in AME2020, it remains visible in the audit sheet but is not silently promoted into the measured primary population.

## Deterministic mid-shell selection
Select one AME2020 primary-eligible nucleus from each band:
- medium: 60 <= A <= 119;
- heavy: 120 <= A <= 199.

For each candidate define

`d_mid = min( min_m |N-m|, min_k |Z-k| )`,

with neutron magic numbers `m in {20,28,50,82,126}` and proton magic numbers `k in {20,28,50,82}`.

Within each band select the nucleus with maximum `d_mid`; break ties by:
1. smaller reported mass-excess uncertainty;
2. smaller A;
3. smaller Z;
4. smaller N.

This selection is frozen before the full AME2020 table is parsed, so no result-dependent nucleus selection is possible.

## Required cross-check
For every measured selected target, record NNDC/NuDat provenance and compare at least mass excess and BE/A. Where NuDat exposes the corresponding quantity, also compare Sn, Sp, S2n, S2p and Qalpha. Numerical differences above 2 keV trigger investigation rather than tolerance relaxation.
