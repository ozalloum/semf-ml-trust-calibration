# Protocol Implementation Note A8 - Derived Predictions and R7

**Freeze date:** 2026-08-31
**Status:** PRE-RESULT implementation freeze

## A8.1 Derived-observable prediction rule
For a derived observable to enter the primary out-of-sample score, every binding-energy term required by that observable must have an out-of-sample prediction under the same regime. This strict rule avoids a derived endpoint that silently mixes held-out and in-sample binding-energy predictions.

A secondary operational sensitivity may use a known measured neighbor where scientifically meaningful, but it must be labeled separately and cannot replace the strict primary derived-observable score.

Conventions follow A5:
- `Sn(N,Z)=B(N,Z)-B(N-1,Z)`;
- `S2n(N,Z)=B(N,Z)-B(N-2,Z)`;
- `Sp(N,Z)=B(N,Z)-B(N,Z-1)`;
- `S2p(N,Z)=B(N,Z)-B(N,Z-2)`;
- `Qalpha(N,Z)=B(N-2,Z-2)+B(2,2)-B(N,Z)`;
- `delta2n(N,Z)=S2n(N,Z)-S2n(N+2,Z)`;
- `delta2p(N,Z)=S2p(N,Z)-S2p(N,Z+2)`.

## A8.2 R7 implementation
The supplementary light-nucleus stress test is implemented as a fixed 20% random holdout (seed `20260910`) within the A1 light population (`Z>=2`, `N>=2`, finite non-estimated target). Errors and trust are then reported in the predeclared strata `A<20`, `20<=A<40`, and `A>=40`.

This is a population-stratified stress test, not a claim that `A=20` or `A=40` is a physical validity boundary.
