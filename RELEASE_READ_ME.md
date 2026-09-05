# Paper - Final real empirical release

**Title:** *When Should Machine Learning Trust the Semi-Empirical Mass Formula? Mechanism- and Observable-Dependent Tests Across the Nuclear Chart*

## Release status

This is the completed real-data Paper reproducibility release. It uses the official unrounded AME2012, AME2016, and AME2020 mass/reaction tables; the controlled synthetic benchmark remains a separate earlier mechanism study and is not used as empirical evidence here.

The final empirical integrity audit reports **85 PASS checks, 0 failures, and 1 disclosed nonblocking warning**. The warning is one structured MLP fit reaching the frozen maximum iteration count; the frozen five-seed ensemble was retained without post-hoc retuning and the limitation is stated in the manuscript.

## Chronology firewall

- Development/model selection: AME2012 -> genuinely new AME2016 primary nuclei (32 targets).
- Frozen configuration SHA-256: `4c58f61fdfd868bcff38a009eb036ff8dfba5cbfea6ba0f1c4c34618a7be63d7`.
- One-time confirmation: AME2016 -> genuinely new AME2020 primary nuclei (51 targets).
- Confirmation status: `COMPLETED_ONCE`; no retuning permitted after opening.

## Main empirical results

- HGB one-time confirmation: data-only MAE 5.710 MeV; fixed soft prior 2.342 MeV; **residual repair 0.574 MeV**, giving **G=9.946** (95% paired-bootstrap CI 8.023-12.643).
- MLP one-time confirmation: data-only MAE 5.025 MeV; fixed soft prior 2.212 MeV; **residual repair 0.654 MeV**, giving **G=7.684** (95% CI 5.600-10.334).
- Across all primary structured holdouts, residual repair improved total binding-energy MAE for both HGB and MLP.
- Whole Sn-chain HGB fixed blending shows the central observable-dependent reversal: **G_B=0.616** and **G_B/A=0.641** (harm), while **G_Sn=1.686**, **G_S2n=1.401**, and **G_delta2n=2.024** (benefit).
- Correlated SEMF coefficient uncertainty did not reverse the principal sign patterns.
- Suppressing the explicit shell term in the shell-aware BWN control increased MAE by 1.246 MeV on Sn and 0.960 MeV in the primary magic-region holdout.

## Claim boundary

The paper is a mechanistic study of **conditional physics trust**, not a claim of a new state-of-the-art mass model. BWN scores on the AME2016->2020 transition are explicitly retrospective because that functional form postdates AME2020. Derived observables obey the strict all-neighbors-held-out rule.

## Package map

- `manuscript/` - final Markdown, editable DOCX, publication PDF, PDF preflight report.
- `figures/main/` - 8 main figures in PNG and PDF.
- `figures/supplementary/` - 5 supplementary figures in PNG and PDF.
- `tables/` - main frozen result tables.
- `data/raw/` - all 9 official AME raw files plus acquisition/provenance records.
- `data/processed/` - parsed populations, derived observables, and locked historical memberships.
- `results/` - Stages 3C through 3G.5 real empirical outputs, including the one-time confirmation lock.
- `frozen_protocol/` - frozen empirical protocol, A1-A3 amendments, and A4-A13 implementation notes.
- `code/` - Stage 3B data-gate code and Stages 3C-3I analysis code.
- `audit/` - Stage 3B audit evidence and final empirical audit.

## Human metadata still required before journal submission

The scientific analysis and manuscript are complete, but the manuscript intentionally retains placeholders for author names/affiliations, funding, competing interests, and author contributions. Those must be supplied by the authors before submission.
