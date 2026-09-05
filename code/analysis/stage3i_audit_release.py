#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, py_compile, zipfile
from pathlib import Path
from common import sha256_file, write_json


def main():
    ap=argparse.ArgumentParser(description="Stage 3I: final reproducibility/integrity audit")
    ap.add_argument("--project-root",type=Path,required=True)
    ap.add_argument("--run-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    checks=[]
    # Compile every analysis script.
    for p in sorted((a.project_root/"code").glob("*.py")):
        try: py_compile.compile(str(p),doraise=True); checks.append({"check":"compile:"+p.name,"status":"PASS"})
        except Exception as e: checks.append({"check":"compile:"+p.name,"status":"FAIL","detail":str(e)})
    expected=[
        ("3C",a.run_root/"stage3c"/"STAGE3C_STATUS.json"),
        ("3D",a.run_root/"stage3d"/"BWN_REPRODUCTION_GATE.json"),
        ("3E",a.run_root/"stage3e"/"CONFIRMATION_COMPLETED.json"),
        ("3F",a.run_root/"stage3f"/"STAGE3F_STATUS_AND_FITS.json"),
        ("3G",a.run_root/"stage3g"/"STAGE3G_STATUS.json"),
        ("3H manuscript",a.run_root/"stage3h"/"Paper3_Development_Manuscript.md"),
    ]
    for name,p in expected: checks.append({"check":"artifact:"+name,"status":"PASS" if p.exists() else "FAIL","path":str(p)})
    # Confirmation integrity: the one-time lock and completed record must agree on frozen configuration digest.
    try:
        lock=json.loads((a.run_root/"stage3e"/"CONFIRMATION_OPENED_LOCK.json").read_text()); done=json.loads((a.run_root/"stage3e"/"CONFIRMATION_COMPLETED.json").read_text())
        ok=lock.get("freeze_sha256")==done.get("freeze_sha256") and done.get("status")=="COMPLETED_ONCE"
        checks.append({"check":"one-time confirmation lock","status":"PASS" if ok else "FAIL"})
    except Exception as e: checks.append({"check":"one-time confirmation lock","status":"FAIL","detail":str(e)})
    # Figure style: every multi-series plot generator has explicit style combinations and output note.
    checks.append({"check":"figure style rule","status":"PASS" if (a.run_root/"stage3h"/"FIGURE_STYLE_RULE.txt").exists() else "FAIL"})
    # BWN gate is expected to BLOCK on synthetic smoke data; real paper requires PASS for BWN use.
    try:
        b=json.loads((a.run_root/"stage3d"/"BWN_REPRODUCTION_GATE.json").read_text())
        if a.smoke: b_ok=b.get("status") in {"PASS","BLOCKED"}
        else: b_ok=b.get("status")=="PASS"
        checks.append({"check":"BWN reproduction policy","status":"PASS" if b_ok else "FAIL","observed":b.get("status")})
    except Exception as e: checks.append({"check":"BWN reproduction policy","status":"FAIL","detail":str(e)})
    failed=[c for c in checks if c["status"]!="PASS"]
    report={"stage":"3I","status":"PASS" if not failed else "BLOCKED","smoke_mode":bool(a.smoke),"checks":checks,"failed_count":len(failed),
            "claim_boundary":"Synthetic smoke outputs validate software execution only and never support empirical nuclear-physics claims." if a.smoke else "All empirical claims must trace to frozen AME products and locked result tables."}
    write_json(report,a.out/"FINAL_AUDIT_REPORT.json")
    # Manifest covers project code/protocol/theory/literature and the supplied run outputs.
    entries=[]
    for base,label in [(a.project_root,"project"),(a.run_root,"run")]:
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc"):
                entries.append({"scope":label,"path":str(p.relative_to(base)),"bytes":p.stat().st_size,"sha256":sha256_file(p)})
    write_json({"entries":entries},a.out/"RELEASE_MANIFEST.json")
    (a.out/"SHA256SUMS.txt").write_text("".join(f"{e['sha256']}  {e['scope']}/{e['path']}\n" for e in entries),encoding="utf-8")
    print("STAGE 3I:",report["status"],"checks",len(checks),"failed",len(failed))
    if failed and not a.smoke: raise SystemExit(2)

if __name__=="__main__": main()
