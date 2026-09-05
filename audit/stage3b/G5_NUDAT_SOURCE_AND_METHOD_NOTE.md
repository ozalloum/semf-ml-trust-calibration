# G5 NuDat source and method note

**Run date:** 2026-08-31

## Purpose
This is the frozen Stage 3B data-engineering/interface check, not statistically independent experimental evidence.

## Source basis
NNDC NuDat 3 documents the 2020 Atomic Mass Evaluation as its source for mass excess, neutron/proton separation energies, Q-alpha, and binding energy per nucleon. The NuDat chart also exposes S2n and S2p as observables.

Source pages:
- https://www.nndc.bnl.gov/nudat3/guide/
- https://www.nndc.bnl.gov/nudat3/

The current NuDat page for 208Pb visibly reports a ground-state mass excess of -21748.5 keV, consistent with the parsed AME2020 value -21748.519 keV.

## Recording rule
For every selected primary-eligible target, the NuDat/AME2020 quantities were recorded at 0.1 keV display precision before comparison to the higher-precision parsed AME values. This intentionally checks parsing, units, signs, nucleus indexing, and derived-observable reconstruction at a precision far tighter than the frozen 2 keV investigation threshold.

NuDat uses AME2020 for these mass-derived quantities, so agreement must not be described as an independent experimental replication.
