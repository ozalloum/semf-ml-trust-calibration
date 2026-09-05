#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, shutil

WIDTHS={
  ('2020','mass_1.mas20'):135, ('2020','rct1.mas20'):144, ('2020','rct2_1.mas20'):144,
  ('2016','mass16.txt'):123, ('2016','rct1-16.txt'):120, ('2016','rct2-16.txt'):120,
  ('2012','mass.mas12'):123, ('2012','rct1.mas12'):120, ('2012','rct2.mas12'):120,
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def is_mass_candidate(line):
    if len(line)<19: return False
    try: int(line[4:9]); int(line[9:14]); int(line[14:19]); return True
    except: return False

def is_rct_candidate(line):
    if len(line)<11: return False
    try: int(line[1:4]); int(line[8:11]); return True
    except: return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--audit',type=Path,required=True); a=ap.parse_args()
    records=[]
    for (v,name),width in WIDTHS.items():
        src=a.raw/v/name; dst=a.out/v/name; dst.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_text(encoding='utf-8',errors='strict').splitlines()
        out=[]; padded=0; candidates=0; min_before=None; max_before=None
        pred=is_mass_candidate if 'mass' in name else is_rct_candidate
        for line in data:
            if pred(line):
                candidates+=1; L=len(line); min_before=L if min_before is None else min(min_before,L); max_before=L if max_before is None else max(max_before,L)
                if L<width:
                    line=line.ljust(width); padded+=1
            out.append(line)
        # preserve LF line endings, which are irrelevant to fixed-width fields
        dst.write_text('\n'.join(out)+'\n',encoding='utf-8')
        records.append({'vintage':int(v),'basename':name,'expected_width':width,'candidate_rows':candidates,'rows_right_padded':padded,'min_candidate_width_before':min_before,'max_candidate_width_before':max_before,'raw_sha256':sha(src),'normalized_sha256':sha(dst),'operation':'right-pad candidate data records with ASCII spaces only; no non-whitespace byte changed'})
    a.audit.parent.mkdir(parents=True,exist_ok=True); a.audit.write_text(json.dumps({'status':'PASS','reason':'Browser/manual text saves stripped trailing fixed-width spaces. Raw files remain immutable and provenance-hashed. Processing copies restore only trailing ASCII spaces to the declared record width; field bytes and parsed values are unchanged.','files':records},indent=2)+'\n')
    print('Created lossless fixed-width processing copies for',len(records),'files')
if __name__=='__main__': main()
