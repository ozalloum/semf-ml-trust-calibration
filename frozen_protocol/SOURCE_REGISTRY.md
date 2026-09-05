# Frozen Source Registry

## A. Authoritative AME source
Atomic Mass Data Center (AMDC), Institute of Modern Physics, Chinese Academy of Sciences.

AME2020 main files:
- mass_1.mas20 - atomic masses
- rct1.mas20 - S2n, S2p, Qalpha and related reaction energies
- rct2_1.mas20 - Sn, Sp and related reaction energies

AME2016 main files:
- mass16.txt
- rct1-16.txt
- rct2-16.txt

AME2012 main files:
- mass.mas12
- rct1.mas12
- rct2.mas12

Primary papers must be cited rather than treating the electronic table itself as the scientific publication.

## B. IAEA NDS mirror
Use as acquisition fallback for AME files when the AMDC host is unavailable. A commonly referenced AME2020 raw endpoint is:
https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt

## C. NNDC / NuDat
Role: cross-check selected parsed values and derived observables; nuclear-structure/decay context for case studies.
Important methodological caution: NuDat's mass-derived quantities use AME2020, so agreement is a pipeline validation, not statistical replication from an independent mass experiment.

## D. KAERI Nuclear Data Center
Role: secondary nuclide-property, decay-diagram and evaluation cross-check. Do not use it to replace AME for Paper 3 mass targets.

## E. Physics LibreTexts / MIT OCW (Paola Cappellaro)
Role: accessible derivation/notation support for binding energy, Sn, Sp, and physical interpretation of the five SEMF terms. Not used for numerical targets or coefficient fitting.

## F. Gjorgievska et al. 2024
Sara Gjorgievska, Hristijan Kochankovski, Koviljka Stankovic, Lambe Barandovski,
"Revision of the semi-empirical mass formula coefficients by using the AME2020 database",
Nuclear Engineering and Design 426, 113403 (2024), DOI 10.1016/j.nucengdes.2024.113403.
Role: coefficient/calibration-domain benchmark and literature comparison. Their fit uses 2548 AME2020 nuclei and reports separate all-A and A>=50 coefficient sets.
