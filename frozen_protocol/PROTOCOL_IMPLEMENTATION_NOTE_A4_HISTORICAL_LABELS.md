# Protocol Implementation Note A4 - Historical AME Membership Labels

**Freeze date:** 2026-08-31  
**Status:** pre-data implementation rule  
**Applies to:** AME2012->AME2016 development and AME2016->AME2020 confirmation set construction.

## Purpose
The frozen Stage 2 protocol required later-version nuclides to be labelled `new`, `changed`, or `unchanged`, but did not define how to avoid falsely calling a value `changed` merely because a later AME table prints more decimal places.

## Frozen rule
For a later AME vintage:

- **new:** the `(N,Z)` nuclide is present as a finite, non-estimated mass target in the later vintage and is absent as a finite, non-estimated mass target in the earlier vintage;
- **unchanged:** the nuclide is measured in both vintages and the two mass-excess values agree after both are rounded to the **coarser of the two reported decimal precisions**;
- **changed:** the nuclide is measured in both vintages but fails the common-reported-precision equality test.

The signed numerical difference in mass excess is always stored separately as `delta_mass_excess_keV`.

## Primary historical target
The historical headline remains the **new** high-precision population. `changed` nuclei are secondary and are never merged with `new` nuclei.

## Why this is safe
This rule is frozen before any Paper 3 empirical prediction error is inspected. It is a data-engineering classification rule, not a model-selection choice.
