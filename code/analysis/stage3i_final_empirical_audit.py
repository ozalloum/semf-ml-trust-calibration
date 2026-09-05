#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, py_compile, re
from pathlib import Path

FREEZE='4c58f61fdfd868bcff38a009eb036ff8dfba5cbfea6ba0f1c4c34618a7be63d7'

def sha256(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def loadj(p): return json.loads(Path(p).read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root',type=Path,required=True)
    ap.add_argument('--run-root',type=Path,required=True)
    ap.add_argument('--stage3b-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    checks=[]; warnings=[]
    def check(name,ok,detail=None):
        d={'check':name,'status':'PASS' if ok else 'FAIL'}
        if detail is not None: d['detail']=detail
        checks.append(d); return ok
    def warn(name,detail): warnings.append({'warning':name,'detail':detail})

    # Stage 3B provenance/data integrity
    raw=loadj(a.stage3b_root/'audit/RAW_FILE_INTEGRITY.json')
    check('3B raw provenance PASS', raw.get('status')=='PASS')
    check('3B all nine raw AME files present', len(raw.get('files',[]))==9 and not raw.get('missing'))
    check('3B no provenance errors', not raw.get('provenance_errors'))
    current_hash_ok=all(Path(x['path']).exists() and sha256(Path(x['path']))==x['sha256'] for x in raw.get('files',[]))
    check('3B raw file SHA-256 values still match', current_hash_ok)
    dp=loadj(a.stage3b_root/'audit/DATA_PRODUCT_SUMMARY.json')
    check('3B AME mass parser row counts', [dp['mass_audits'][v]['parsed']['rows'] for v in ['2012','2016','2020']]==[3353,3436,3558])
    check('3B A=N+Z integrity', all(dp['mass_audits'][v]['parsed']['A_identity_failures']==0 for v in ['2012','2016','2020']))
    check('3B no duplicate mass keys', all(dp['mass_audits'][v]['parsed']['duplicates']==0 for v in ['2012','2016','2020']))
    check('3B derived-observable reconstruction <=2 keV', all(dp['derived_observable_consistency'][v]['fail_gt_2keV']==0 for v in ['2012','2016','2020']))
    check('3B development membership =32 new primary', dp['historical_counts']['2012_to_2016_new_primary']==32)
    check('3B locked confirmation membership =51 new primary', dp['historical_counts']['2016_to_2020_new_primary_LOCKED_CONFIRMATION']==51)
    g5=loadj(a.stage3b_root/'audit/SELECTED_NUCLEI_SPOTCHECK_AUDIT.json')
    check('3B G5 NuDat interface check PASS', g5.get('status')=='PASS')
    check('3B G5 has 35 comparisons', g5.get('comparison_count')==35)
    check('3B G5 maximum discrepancy <2 keV', max(x['abs_diff_keV'] for x in g5['comparisons'])<2.0)
    check('A11 browser-normalization note exists', (a.stage3b_root/'frozen_protocol/PROTOCOL_IMPLEMENTATION_NOTE_A11_BROWSER_TRAILING_SPACE_NORMALIZATION.md').exists())

    # Stage 3C freeze
    c=loadj(a.run_root/'stage3c/STAGE3C_STATUS.json')
    check('3C development PASS', c.get('status')=='PASS' and not c.get('smoke_mode'))
    check('3C frozen hash exact', c.get('freeze_sha256')==FREEZE, c.get('freeze_sha256'))
    check('3C development train/test sizes 2235/32', c.get('train_n')==2235 and c.get('development_test_n')==32)

    # Stage 3D BWN gate
    d=loadj(a.run_root/'stage3d/BWN_REPRODUCTION_GATE.json')
    check('3D BWN reproduction PASS', d.get('status')=='PASS' and not d.get('smoke_mode'))
    check('3D BWN reproduction within 0.02 MeV', d.get('absolute_difference_MeV',99)<0.02)
    check('3D reproduced BWN RMS ~0.886854 MeV', abs(d.get('reproduced_rms_MeV',0)-0.8868544696188632)<1e-12)

    # Stage 3E one-time confirmation integrity
    lock=loadj(a.run_root/'stage3e/CONFIRMATION_OPENED_LOCK.json')
    done=loadj(a.run_root/'stage3e/CONFIRMATION_COMPLETED.json')
    er=loadj(a.run_root/'stage3e/CONFIRMATION_RESULTS.json')
    check('3E lock created before scoring', lock.get('status')=='LOCKED_BEFORE_SCORING')
    check('3E completed exactly once', done.get('status')=='COMPLETED_ONCE')
    check('3E lock/final freeze hashes agree', lock.get('freeze_sha256')==done.get('freeze_sha256')==FREEZE)
    check('3E no-retuning flag preserved', lock.get('no_retuning_permitted') is True and done.get('no_retuning_permitted') is True)
    check('3E confirmation membership digest preserved', lock.get('confirmation_membership_sha256')==done.get('confirmation_membership_sha256'))
    check('3E confirmation train/test sizes 2271/51', er.get('n_train')==2271 and er.get('n_test')==51)
    check('3E predictions checksum locked', sha256(a.run_root/'stage3e/CONFIRMATION_PREDICTIONS.csv')==done['predictions_sha256'])
    check('3E results checksum locked', sha256(a.run_root/'stage3e/CONFIRMATION_RESULTS.json')==done['results_sha256'])
    check('3E HGB residual headline exact', abs(er['families']['hgb']['residual_repair']['mae']-0.5741132719001353)<1e-12 and abs(er['families']['hgb']['G_residual']-9.946166574948272)<1e-12)
    check('3E MLP residual headline exact', abs(er['families']['mlp']['residual_repair']['mae']-0.6538561227258926)<1e-12 and abs(er['families']['mlp']['G_residual']-7.68443305721585)<1e-12)
    check('3E BWN historical claim labeled retrospective', 'retrospective' in er['bwn_retrospective_stress']['claim_boundary'].lower())

    # Stage 3F/3G/G.5
    f=loadj(a.run_root/'stage3f/STAGE3F_STATUS_AND_FITS.json')
    check('3F structured holdouts PASS', f.get('status')=='PASS' and not f.get('smoke_mode'))
    check('3F exactly 25 regimes', len(f.get('regimes_evaluated',[]))==25, len(f.get('regimes_evaluated',[])))
    g=loadj(a.run_root/'stage3g/STAGE3G_STATUS.json')
    check('3G uncertainty/misspecification PASS', g.get('status')=='PASS' and g.get('bootstrap_refits')==5000 and g.get('correlated_draws')==1000)
    g5c=loadj(a.run_root/'stage3g5/STAGE3G5_STATUS.json')
    check('3G.5 predeclared completeness PASS', g5c.get('status')=='PASS')
    check('3G.5 did not reopen confirmation', g5c.get('confirmation_reopened') is False)
    check('A1 B/A endpoint executed', g5c.get('n_BA_rows')==350)
    check('A2 term build-up executed', g5c.get('n_term_buildup_rows')==125)
    check('A2 term-removal executed', g5c.get('n_term_removal_rows')==125)
    check('A3 chart/calibration diagnostics executed', g5c.get('n_landscape_rows')==2339 and g5c.get('n_local_map_rows')==4092)
    for name in ['PROTOCOL_AMENDMENT_A1.md','PROTOCOL_AMENDMENT_A2_VISUAL_TERM_DECOMPOSITION.md','PROTOCOL_AMENDMENT_A3_CALIBRATION_DOMAIN.md','PROTOCOL_IMPLEMENTATION_NOTE_A12_EXACT_CHAIN_BOOTSTRAP_OPTIMIZATION.md','PROTOCOL_IMPLEMENTATION_NOTE_A13_PREDECLARED_COMPLETENESS_EXECUTION.md']:
        check('protocol exists: '+name, (a.project_root/'frozen_protocol'/name).exists())

    # Locked confidence intervals -> reporting tables/manuscript
    paired=[]
    for line in (a.run_root/'stage3g/PAIRED_BOOTSTRAP_PRIMARY_COMPARISONS.jsonl').read_text().splitlines():
        if line.strip(): paired.append(json.loads(line))
    by={(x['family'],x['mechanism']):x for x in paired if x['regime']=='R5_historical_confirmation'}
    expected={
      ('hgb','soft'):[2.1355024911,2.7805185192],('hgb','residual'):[8.0229381944,12.6425819858],('hgb','adaptive'):[1.8236457878,2.1774035589],
      ('mlp','soft'):[1.9239775632,2.6090524031],('mlp','residual'):[5.6004638426,10.3339592098],('mlp','adaptive'):[1.7119298381,2.1649365658]}
    check('3G locked confirmation CIs present', all(k in by and all(abs(a-b)<1e-10 for a,b in zip(by[k]['G_ci95'],v)) for k,v in expected.items()))

    table2=a.run_root/'stage3h/tables/Table2_Historical_Confirmation.csv'
    rows=list(csv.DictReader(table2.open()))
    tr={r['Method']:r for r in rows}
    check('Table 2 HGB adaptive CI corrected', tr['HGB adaptive']['95% CI for G']=='[1.824, 2.177]')
    check('Table 2 MLP adaptive CI corrected', tr['MLP adaptive']['95% CI for G']=='[1.712, 2.165]')
    table4=list(csv.DictReader((a.run_root/'stage3h/tables/Table4_Sn_Observable_Trust.csv').open()))
    t4={(r['Family'],r['Mechanism'],r['Observable']):float(r['G']) for r in table4}
    check('Sn HGB soft sign reversal preserved', t4[('HGB','soft','B')]<1 and t4[('HGB','soft','B/A')]<1 and t4[('HGB','soft','Sn')]>1 and t4[('HGB','soft','S2n')]>1 and t4[('HGB','soft','delta2n')]>1)

    # Stage 3H publication artifacts
    s3h=a.run_root/'stage3h'
    main_png=sorted((s3h/'main').glob('Fig*.png')); supp_png=sorted((s3h/'supplementary').glob('SuppFig*.png'))
    check('3H has 8 main figures', len(main_png)==8, [p.name for p in main_png])
    check('3H has 5 supplementary figures', len(supp_png)==5, [p.name for p in supp_png])
    check('3H figure-style rule recorded', (s3h/'FIGURE_STYLE_RULE.txt').exists())
    md=s3h/'Paper3_FINAL_Empirical_Manuscript.md'; docx=s3h/'Paper3_FINAL_Empirical_Manuscript.docx'; pdf=s3h/'Paper3_FINAL_Empirical_Manuscript.pdf'
    check('final manuscript Markdown exists', md.exists() and md.stat().st_size>30000)
    check('final manuscript DOCX exists', docx.exists() and docx.stat().st_size>1000000)
    check('final manuscript PDF exists', pdf.exists() and pdf.stat().st_size>500000)
    mdt=md.read_text(encoding='utf-8')
    check('final manuscript contains corrected adaptive CIs', '[1.824, 2.177]' in mdt and '[1.712, 2.165]' in mdt)
    check('final manuscript excludes synthetic/smoke result language', not re.search(r'\bsynthetic\b|smoke[_ -]?mode|fabricat(?:ed|ion)',mdt,re.I))
    check('final manuscript labels BWN historical use retrospective', mdt.lower().count('retrospective')>=3)
    check('final manuscript acknowledges single-chain bootstrap degeneracy', 'degenerate for a single whole-chain holdout' in mdt)
    check('final manuscript acknowledges MLP iteration-limit warning', 'maximum iteration count' in mdt)
    check('author/funding/COI remain explicit placeholders', '[Author name(s) and affiliations to be inserted]' in mdt and '[To be supplied by the authors before submission.]' in mdt)
    try:
        import fitz
        pdfdoc=fitz.open(pdf); check('final PDF opens and has 13 pages', pdfdoc.page_count==13, pdfdoc.page_count); pdfdoc.close()
    except Exception as e:
        check('final PDF opens and has 13 pages',False,str(e))

    # Code compilation: empirical + Stage3B source.
    for base,label in [(a.project_root/'code','analysis'),(a.stage3b_root/'code','stage3b')]:
        for p in sorted(base.glob('*.py')):
            try:
                py_compile.compile(str(p),doraise=True); check(f'compile {label}/{p.name}',True)
            except Exception as e:
                check(f'compile {label}/{p.name}',False,str(e))

    # Known nonblocking warning already disclosed in manuscript.
    warn('MLP convergence','One structured MLP fit reached the frozen maximum iteration count; the frozen five-seed ensemble was retained without post-hoc retuning and this is disclosed in Limitations.')

    failed=[x for x in checks if x['status']=='FAIL']
    report={
      'stage':'3I-FINAL-EMPIRICAL','status':'PASS' if not failed else 'BLOCKED',
      'pass_count':sum(x['status']=='PASS' for x in checks),'failed_count':len(failed),'warning_count':len(warnings),
      'freeze_sha256':FREEZE,'checks':checks,'warnings':warnings,
      'claim_boundary':'All empirical claims trace to frozen AME products, predeclared analyses, and the locked one-time AME2016->AME2020 confirmation. BWN historical scores are retrospective.'}
    (a.out/'FINAL_EMPIRICAL_AUDIT_REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    lines=[f"Paper 3 final empirical audit: {report['status']}",f"PASS checks: {report['pass_count']}",f"Failed checks: {report['failed_count']}",f"Warnings: {report['warning_count']}",f"Freeze SHA-256: {FREEZE}",""]
    for x in checks: lines.append(f"[{x['status']}] {x['check']}"+(f" :: {x['detail']}" if 'detail' in x else ''))
    if warnings:
        lines.append(''); lines.append('Warnings:'); lines += [f"[WARN] {w['warning']} :: {w['detail']}" for w in warnings]
    (a.out/'FINAL_EMPIRICAL_AUDIT_REPORT.txt').write_text('\n'.join(lines)+'\n')
    print(f"FINAL EMPIRICAL AUDIT: {report['status']} | pass={report['pass_count']} failed={report['failed_count']} warnings={report['warning_count']}")
    if failed: raise SystemExit(2)

if __name__=='__main__': main()
