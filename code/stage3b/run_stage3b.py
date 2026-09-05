#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("+", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--skip-download", action="store_true", help="Use already supplied and provenance-registered raw files under data/raw")
    args = ap.parse_args()
    root = args.root.resolve()
    code = root / "code"
    raw = root / "data" / "raw"
    proc = root / "data" / "processed"
    audit = root / "audit"
    raw.mkdir(parents=True, exist_ok=True); proc.mkdir(parents=True, exist_ok=True); audit.mkdir(parents=True, exist_ok=True)
    if not args.skip_download:
        run([sys.executable, str(code / "acquire_ame.py"), "--out", str(raw)])
    run([sys.executable, str(code / "run_gate.py"), "--raw", str(raw), "--audit", str(audit)])
    run([sys.executable, str(code / "build_data_products.py"), "--raw", str(raw), "--out", str(proc), "--audit", str(audit)])
    run([sys.executable, str(code / "build_spotcheck_targets.py"), "--mass", str(raw / "2020" / "mass_1.mas20"), "--out", str(audit / "SELECTED_NUCLEI_SPOTCHECK_TARGETS.csv")])
    print("STAGE 3B CORE DATA GATES: PASS")
    print("G5 independent NNDC/NuDat spot-check: PENDING until reference_* columns are populated and validate_spotchecks.py passes.")
    print("AME2016->AME2020 confirmation index is constructed but MUST NOT be scored before Stage 3C is frozen.")

if __name__ == "__main__":
    main()
