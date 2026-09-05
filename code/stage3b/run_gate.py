#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from ame_io import file_stats, dump_json

EXPECTED = {
    2020: ["mass_1.mas20", "rct1.mas20", "rct2_1.mas20"],
    2016: ["mass16.txt", "rct1-16.txt", "rct2-16.txt"],
    2012: ["mass.mas12", "rct1.mas12", "rct2.mas12"],
}
ALLOWED_HOSTS = {"www-nds.iaea.org", "amdc.impcas.ac.cn"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--audit", type=Path, default=Path("audit"))
    args = ap.parse_args()
    files = []
    missing = []
    actual = {}
    for v, names in EXPECTED.items():
        for n in names:
            p = args.raw / str(v) / n
            if not p.exists():
                missing.append(str(p)); continue
            stat = file_stats(p)
            rec = {"vintage": v, "basename": n, "path": str(p), **stat}
            files.append(rec); actual[(v, n)] = rec

    provenance_path = args.raw / "ACQUISITION_RECORD.json"
    provenance_errors = []
    provenance_mode = None
    if not provenance_path.exists():
        provenance_errors.append("Missing data/raw/ACQUISITION_RECORD.json. Automated acquisition creates it; manual files must be registered with register_manual_provenance.py.")
    else:
        try:
            prov = json.loads(provenance_path.read_text(encoding="utf-8"))
            provenance_mode = prov.get("mode", "automated_or_unspecified")
            records = {(int(r["vintage"]), r["basename"]): r for r in prov.get("files", [])}
            for key, a in actual.items():
                r = records.get(key)
                if r is None:
                    provenance_errors.append(f"No provenance record for {key[0]} {key[1]}")
                    continue
                host = urlparse(str(r.get("url", ""))).hostname
                if host not in ALLOWED_HOSTS:
                    provenance_errors.append(f"Unapproved source host for {key[0]} {key[1]}: {host}")
                if r.get("sha256") != a["sha256"]:
                    provenance_errors.append(f"SHA-256 mismatch for {key[0]} {key[1]}")
                if int(r.get("bytes", -1)) != a["bytes"]:
                    provenance_errors.append(f"Byte-count mismatch for {key[0]} {key[1]}")
            extra = set(records) - set(actual)
            if extra:
                provenance_errors.append(f"Provenance contains unexpected entries: {sorted(extra)}")
        except Exception as exc:
            provenance_errors.append(f"Invalid acquisition record: {type(exc).__name__}: {exc}")

    status = "PASS" if not missing and not provenance_errors and len(files) == 9 else "BLOCKED"
    report = {
        "missing": missing, "files": files,
        "provenance_record": str(provenance_path),
        "provenance_mode": provenance_mode,
        "provenance_errors": provenance_errors,
        "status": status,
    }
    dump_json(report, args.audit / "RAW_FILE_INTEGRITY.json")
    if missing or provenance_errors or len(files) != 9:
        details = missing + provenance_errors
        raise SystemExit("RAW/PROVENANCE GATE BLOCKED:\n" + "\n".join(details))
    print("RAW FILE + PROVENANCE INTEGRITY: PASS (9/9)")

if __name__ == "__main__":
    main()
