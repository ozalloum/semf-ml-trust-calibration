#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from ame_io import file_stats, dump_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Register provenance for manually downloaded official AME files.")
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--manifest", type=Path, default=Path("frozen_protocol/ACQUISITION_MANIFEST_STAGE3B.json"))
    ap.add_argument("--source", choices=["iaea", "amdc"], required=True,
                    help="Official site from which the user manually downloaded the files")
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    domain = "www-nds.iaea.org" if args.source == "iaea" else "amdc.impcas.ac.cn"
    records = []
    missing = []
    for spec in manifest["files"]:
        path = args.raw / str(spec["vintage"]) / spec["basename"]
        if not path.exists():
            missing.append(str(path)); continue
        candidates = [u for u in spec["urls"] if domain in u]
        if not candidates:
            raise RuntimeError(f"No frozen {args.source} URL for {spec['vintage']} {spec['basename']}")
        records.append({
            "vintage": spec["vintage"], "kind": spec["kind"], "basename": spec["basename"],
            "local_path": str(path), "url": candidates[0],
            "acquisition_mode": "manual_official_download_attested",
            "source_attestation": f"User supplied the file and selected official source={args.source}.",
            **file_stats(path),
        })
    if missing:
        raise SystemExit("Cannot register provenance; missing files:\n" + "\n".join(missing))
    dump_json({"files": records, "mode": "manual_official_download_attested"}, args.raw / "ACQUISITION_RECORD.json")
    print(f"Registered {len(records)} files with {args.source} provenance attestation and SHA-256 hashes.")

if __name__ == "__main__":
    main()
