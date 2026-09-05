# Protocol Implementation Note A12 - Exact Chain-Bootstrap Computational Optimization

**Recorded:** 2026-08-31  
**Status:** implementation-only; no scientific endpoint, model choice, seed, resampling unit, or inferential rule changed.

Stage 3G predeclares 5,000 isotope-chain block-bootstrap replicates. The original reference implementation materialized a concatenated pandas DataFrame for every resample. Before Stage 3G was run on the real data, this implementation was replaced by an algebraically exact sufficient-statistic form: for each isotope chain Z, the code precomputes the number of nuclei and the sums of absolute errors for the two paired predictors. A bootstrap resample that repeats chains then repeats those counts and error sums, yielding exactly the same MAE as physical row concatenation.

The following are unchanged:
- block unit: isotope chain Z;
- sorted set of eligible Z chains;
- 5,000 bootstrap replicates;
- replacement sampling;
- NumPy Generator and frozen seed 20260912;
- one `rng.choice(..., size=len(zs), replace=True)` call per replicate;
- MAE-difference and G quantiles at 0.025 and 0.975.

The pre-optimization function is retained as `code/common_pre_A12_exact_reference.py`. An equivalence test was run before Stage 3G using the same seed and bootstrap samples; outputs agree to floating-point precision. This change is solely to avoid repeated DataFrame construction and does not use any empirical Stage 3G result.
