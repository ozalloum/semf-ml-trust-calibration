# Protocol Implementation Note A10 - Misspecification Architecture Scope

**Freeze date:** 2026-08-31  
**Status:** PRE-RESULT implementation freeze

The empirical misspecification section is designed as a mechanistic physics-prior analysis rather than a large architecture leaderboard.

1. **Full coefficient-resolved map:** the transparent polynomial-ridge family is the primary ML comparator for every one-at-a-time P0 coefficient perturbation (`a_v, a_s, a_c, a_a, a_p` at `-2,-1,+1,+2` bootstrap SD), the no-pairing control, and the correlated-joint coefficient draws. Both fixed-soft-prior and residual-repair integration are evaluated for these deterministic perturbations.
2. **Architecture robustness:** HGB and compact MLP repeat the nominal, no-pairing, and correlated-joint soft-prior summaries. Their role is to test whether the direction of the trust conclusion is architecture-specific, not to reproduce every coefficient-resolved panel.
3. **BWN shell-form control:** if and only if the mandatory BWN reproduction gate passes, shell suppression (`e_m1=0` after the train-split BWN refit) is evaluated in core R0, R1-Sn, and R4 regimes. This is a model-form diagnostic, not a claim that `e_m1=0` is a physically calibrated alternative mass model.

This scope is frozen before any empirical Paper 3 trust result is viewed.
