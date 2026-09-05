#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from ame_io import download, dump_json

FILES = [
    (2020, "mass", "mass_1.mas20", [
        "https://www-nds.iaea.org/amdc/ame2020/mass_1.mas20.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2020/mass_1.mas20",
    ]),
    (2020, "rct1", "rct1.mas20", [
        "https://www-nds.iaea.org/amdc/ame2020/rct1.mas20.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2020/rct1.mas20",
    ]),
    (2020, "rct2", "rct2_1.mas20", [
        "https://www-nds.iaea.org/amdc/ame2020/rct2_1.mas20.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2020/rct2_1.mas20",
    ]),
    (2016, "mass", "mass16.txt", [
        "https://www-nds.iaea.org/amdc/ame2016/mass16.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2016/mass16.txt",
    ]),
    (2016, "rct1", "rct1-16.txt", [
        "https://www-nds.iaea.org/amdc/ame2016/rct1-16.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2016/rct1-16.txt",
    ]),
    (2016, "rct2", "rct2-16.txt", [
        "https://www-nds.iaea.org/amdc/ame2016/rct2-16.txt",
        "https://amdc.impcas.ac.cn/masstables/Ame2016/rct2-16.txt",
    ]),
    (2012, "mass", "mass.mas12", [
        "https://www-nds.iaea.org/amdc/ame2012/mass.mas12",
        "https://www-nds.iaea.org/amdc/masstables/Ame2012/mass.mas12",
        "https://amdc.impcas.ac.cn/masstables/ame2012/mass.mas12",
    ]),
    (2012, "rct1", "rct1.mas12", [
        "https://www-nds.iaea.org/amdc/ame2012/rct1.mas12",
        "https://www-nds.iaea.org/amdc/masstables/Ame2012/rct1.mas12",
        "https://amdc.impcas.ac.cn/masstables/ame2012/rct1.mas12",
    ]),
    (2012, "rct2", "rct2.mas12", [
        "https://www-nds.iaea.org/amdc/ame2012/rct2.mas12",
        "https://www-nds.iaea.org/amdc/masstables/Ame2012/rct2.mas12",
        "https://amdc.impcas.ac.cn/masstables/ame2012/rct2.mas12",
    ]),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/raw"))
    args = ap.parse_args()
    records = []
    for vintage, kind, basename, urls in FILES:
        dest = args.out / str(vintage) / basename
        print(f"Acquiring {vintage} {kind}: {basename}")
        rec = download(urls, dest)
        rec.update({"vintage": vintage, "kind": kind, "basename": basename, "local_path": str(dest), "acquisition_mode": "automated_official_download"})
        records.append(rec)
        print(f"  {rec['bytes']} bytes  sha256={rec['sha256'][:16]}...")
    dump_json({"mode": "automated_official_download", "files": records}, args.out / "ACQUISITION_RECORD.json")
    print("Acquisition complete.")

if __name__ == "__main__":
    main()
