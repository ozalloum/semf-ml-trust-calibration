# Stage 3A Data Gate

The following gates must all pass before development fitting.

## G1 - provenance
- file basename matches the frozen manifest;
- source is AMDC or IAEA NDS AME mirror;
- evaluation vintage is unambiguous (2012, 2016, 2020);
- SHA-256 is recorded locally after acquisition.

## G2 - parser integrity
- header and data-line widths are compatible with the declared AME format;
- integer identity `A = N + Z` holds for all parsed nuclides;
- `(N,Z)` keys are unique within each evaluation;
- element symbols are non-empty for nuclide rows;
- no silent coercion of `*` missing values.

## G3 - estimated-value semantics
AME uses `#` in place of a decimal point for estimated/non-experimental quantities.
The parser must retain an explicit estimated flag. Primary supervised targets exclude estimated values; estimated entries may be retained only for clearly labelled sensitivity/visualization uses.

## G4 - units
- mass excess: keV;
- binding energy per nucleon: keV;
- total binding energy reconstructed as `A * BE_per_A / 1000` in MeV;
- reaction/separation energies from rct files: keV unless explicitly converted.

## G5 - independent spot checks
For predeclared nuclei/regions (including 48Ca, 100Sn, 132Sn, 208Pb where available), compare selected values against NNDC NuDat export/display and optionally KAERI.
Required spot-check quantities when available:
- mass excess;
- BE/A;
- Sn, Sp;
- S2n, S2p;
- Qalpha.
The comparison is a data-engineering validation, not an independent experimental dataset claim, because NNDC mass-derived quantities themselves use AME2020.

## G6 - derived-observable consistency
Where all neighbouring measured nuclei exist, recompute from parsed binding energies:
- Sn, Sp, S2n, S2p;
then compare against the official AME reaction tables (`rct1`, `rct2`).
Differences above 2 keV trigger a parser/unit investigation; the final tolerance can be tightened after observing official rounding conventions, but must not be loosened to hide discrepancies.

## G7 - historical-set integrity
For AME2012->AME2016 and AME2016->AME2020:
- distinguish genuinely new measured targets from nuclei present previously with revised values;
- do not merge `new` and `changed` sets;
- freeze membership before model scoring.
