# A11 — Browser-saved AME trailing-space normalization (pre-modeling implementation correction)

The user-supplied official AME ASCII tables were provenance-hashed exactly as received. All candidate rows parsed completely, but browser/manual text saving removed trailing blank characters from many fixed-width records. This affects only record length, not any numeric or categorical field.

To preserve the frozen fixed-width integrity gate without altering scientific content:

1. The original files under `data/raw/` remain immutable and are the files referenced by the acquisition/provenance hashes.
2. A separate `data/processing_normalized/` tree is created for parsing/modeling.
3. Only candidate data records shorter than the declared width are right-padded with ASCII spaces to the declared width (2020 mass 135, 2020 reactions 144, legacy mass 123, legacy reactions 120 characters, consistent with the existing Stage 3B implementation).
4. No character before the original end-of-line is modified, inserted, deleted, or reordered.
5. Parsed rows, `(N,Z,A)`, estimated/missing flags, and all parsed numerical fields must be identical before and after normalization.
6. The normalization audit records original and normalized SHA-256 values and row counts.

This is a transport-format repair only. It does not change populations, observables, model choices, hyperparameters, historical labels, or the AME2016→AME2020 confirmation protocol.
