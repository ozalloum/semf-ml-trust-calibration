#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path


def run(cmd):
    print("\n+", " ".join(map(str,cmd)),flush=True); subprocess.run(cmd,check=True)


def main():
    ap=argparse.ArgumentParser(description="Run Paper 3 Stages 3C-3I sequentially with no stage-by-stage approval")
    ap.add_argument("--project-root",type=Path,default=Path.cwd()); ap.add_argument("--processed",type=Path,required=True)
    ap.add_argument("--stage3b-audit",type=Path); ap.add_argument("--run-root",type=Path,required=True); ap.add_argument("--smoke",action="store_true")
    a=ap.parse_args(); root=a.project_root.resolve(); rr=a.run_root.resolve(); rr.mkdir(parents=True,exist_ok=True); code=root/"code"
    smoke=["--smoke"] if a.smoke else []
    run([sys.executable,code/"stage3c_development.py","--processed",a.processed,"--out",rr/"stage3c","--protocol-root",root/"frozen_protocol",*smoke])
    # The BWN gate may intentionally block. In smoke mode it does not raise; in real mode a formula/data discrepancy stops the autonomous chain.
    run([sys.executable,code/"stage3d_bwn_gate.py","--processed",a.processed,"--out",rr/"stage3d",*smoke])
    e=[sys.executable,code/"stage3e_confirmation.py","--processed",a.processed,"--stage3c",rr/"stage3c","--stage3d",rr/"stage3d","--out",rr/"stage3e",*smoke]
    if a.stage3b_audit: e += ["--spotcheck-audit",a.stage3b_audit]
    run(e)
    run([sys.executable,code/"stage3f_structured_holdouts.py","--processed",a.processed,"--stage3c",rr/"stage3c","--stage3d",rr/"stage3d","--stage3e",rr/"stage3e","--out",rr/"stage3f",*smoke])
    run([sys.executable,code/"stage3g_uq_misspecification.py","--processed",a.processed,"--stage3c",rr/"stage3c","--stage3d",rr/"stage3d","--stage3e",rr/"stage3e","--stage3f",rr/"stage3f","--out",rr/"stage3g",*smoke])
    run([sys.executable,code/"stage3h_figures_and_manuscript.py","--stage3c",rr/"stage3c","--stage3d",rr/"stage3d","--stage3e",rr/"stage3e","--stage3f",rr/"stage3f","--stage3g",rr/"stage3g","--out",rr/"stage3h",*smoke])
    run([sys.executable,code/"stage3i_audit_release.py","--project-root",root,"--run-root",rr,"--out",rr/"stage3i",*smoke])
    print("\nPAPER 3 STAGES 3C-3I COMPLETE")

if __name__=="__main__": main()
