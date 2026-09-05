# Protocol Implementation Note A5 - Derived Observable Conventions

**Freeze date:** 2026-08-31  
**Status:** pre-computation convention freeze

All binding energies `B(N,Z)` are positive binding energies in MeV unless a formula explicitly says keV.

## Separation energies
- `S_n(N,Z) = B(N,Z) - B(N-1,Z)`
- `S_2n(N,Z) = B(N,Z) - B(N-2,Z)`
- `S_p(N,Z) = B(N,Z) - B(N,Z-1)`
- `S_2p(N,Z) = B(N,Z) - B(N,Z-2)`

## Shell-gap convention
Use the second-difference convention in which a positive peak marks a closure:

- `delta_2n(N,Z) = S_2n(N,Z) - S_2n(N+2,Z)`
- `delta_2p(N,Z) = S_2p(N,Z) - S_2p(N,Z+2)`

Equivalently,

- `delta_2n = 2B(N,Z) - B(N-2,Z) - B(N+2,Z)`
- `delta_2p = 2B(N,Z) - B(N,Z-2) - B(N,Z+2)`.

This is the convention used for the Paper 3 observable-trust analysis and is not changed after results are viewed.

## Q-alpha
For positive binding energies,

`Q_alpha(N,Z) = B(N-2,Z-2) + B_alpha - B(N,Z)`.

For the data-engineering cross-check, official AME `Q(alpha)` from the rct1 table remains the reference. If a mass-excess implementation is used, its sign must reproduce the official AME value before analysis.

## Missing neighbors
Any derived observable requiring a missing, estimated, or ineligible neighboring target is recorded as `NA`; it is never imputed.
