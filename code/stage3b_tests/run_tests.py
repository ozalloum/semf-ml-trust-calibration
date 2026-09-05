#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from ame_io import parse_mass_line, parse_reaction_line, mass_audit, reaction_audit, mass_file_structure_audit, reaction_file_structure_audit
from build_data_products import derive_observables, historical_membership


def mass2020_line(*, N, Z, el, mass="-12345.678901", massu="0.123456", be="8000.12345", beu="0.01234", beta="123.45678", betau="0.12345", atom_i=None, atom_frac="123456.789012", atomu="0.123456", origin="", cc=" "):
    A=N+Z; nz=N-Z; atom_i = A if atom_i is None else atom_i
    line = (
        f"{cc}{nz:3d}{N:5d}{Z:5d}{A:5d} {el:<3}{origin:<4} "
        f"{mass:>14}{massu:>12}{be:>13} {beu:>10} {'B-':<2}{beta:>13}{betau:>11} "
        f"{atom_i:3d} {atom_frac:>13}{atomu:>12}"
    )
    assert len(line) == 135, (len(line), repr(line))
    return line


def mass_legacy_line(*, vintage, N, Z, el, mass="-12345.67890", massu="0.12345", be="8000.123", beu="0.012", beta="123.456", betau="0.123", atom_i=None, atom_frac="123456.78901", atomu="0.12345", origin="", cc=" "):
    A=N+Z; nz=N-Z; atom_i = A if atom_i is None else atom_i
    line = (
        f"{cc}{nz:3d}{N:5d}{Z:5d}{A:5d} {el:<3}{origin:<4} "
        f"{mass:>13}{massu:>11}{be:>11}{beu:>9} {'B-':<2}{beta:>11}{betau:>9} "
        f"{atom_i:3d} {atom_frac:>12}{atomu:>11}"
    )
    assert len(line) == 123, (len(line), repr(line))
    return line


def reaction_line(*, vintage, kind, A, Z, el, vals, uncs, cc=" "):
    assert len(vals)==6 and len(uncs)==6
    vw, uw = (12,10) if vintage == 2020 else (10,8)
    parts = [f"{cc}{A:3d} {el:<3}{Z:3d} "]
    for v,u in zip(vals,uncs):
        parts.append(f"{v:>{vw}}{u:>{uw}}")
    return "".join(parts)


def test_mass_2020():
    line=mass2020_line(N=82,Z=50,el="Sn",mass="-76500.123456",be="8250.54321")
    r=parse_mass_line(line,2020)
    assert r and (r.N,r.Z,r.A)==(82,50,132)
    assert r.element=="Sn"
    assert abs(r.mass_excess_keV + 76500.123456)<1e-9
    assert abs(r.be_per_A_keV-8250.54321)<1e-9
    est=mass2020_line(N=83,Z=50,el="Sn",mass="-76000#",massu="200#",be="8200#",beu="20#",atom_frac="000000#",atomu="100#")
    e=parse_mass_line(est,2020)
    assert e and e.mass_estimated and e.be_estimated and e.atomic_mass_estimated


def test_mass_legacy():
    for vintage in (2012,2016):
        line=mass_legacy_line(vintage=vintage,N=126,Z=82,el="Pb",mass="-21750.12345",be="7867.123")
        r=parse_mass_line(line,vintage)
        assert r and (r.N,r.Z,r.A)==(126,82,208)
        assert r.element=="Pb"
        assert abs(r.mass_excess_keV + 21750.12345)<1e-9
        assert abs(r.be_per_A_keV-7867.123)<1e-9


def test_reaction_parsers():
    vals=["12345.6789","5432.1000","-1000.2500","*","50#","-1.0000"]
    uncs=["0.1000","0.2000","0.3000","*","20#","0.0100"]
    line=reaction_line(vintage=2020,kind="rct1",A=132,Z=50,el="Sn",vals=vals,uncs=uncs)
    r=parse_reaction_line(line,2020,"rct1")
    assert r and (r.N,r.Z)==(82,50)
    n=r.named(); assert abs(n["S2n_keV"]-12345.6789)<1e-9 and n["Qep_estimated"] is True
    vals16=["12345.67","5432.10","-1000.25","*","50#","-1.00"]
    uncs16=["0.10","0.20","0.30","*","20#","0.01"]
    line16=reaction_line(vintage=2016,kind="rct2",A=48,Z=20,el="Ca",vals=vals16,uncs=uncs16)
    r16=parse_reaction_line(line16,2016,"rct2")
    assert r16 and (r16.N,r16.Z)==(28,20)
    n16=r16.named(); assert abs(n16["Sn_keV"]-12345.67)<1e-9 and n16["Qpa_estimated"] is True


def test_audits():
    rows=[parse_mass_line(mass2020_line(N=28,Z=20,el="Ca"),2020), parse_mass_line(mass2020_line(N=82,Z=50,el="Sn"),2020)]
    au=mass_audit(rows)
    assert au["duplicates"]==0 and au["A_identity_failures"]==0 and au["rows"]==2
    rr=[parse_reaction_line(reaction_line(vintage=2020,kind="rct2",A=48,Z=20,el="Ca",vals=["1"]*6,uncs=["0"]*6),2020,"rct2")]
    rau=reaction_audit(rr); assert rau["duplicates"]==0 and rau["rows"]==1




def test_file_structure_audits():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        mp=td/'mass.txt'
        mp.write_text('HEADER\n'+mass2020_line(N=28,Z=20,el='Ca')+'\n',encoding='utf-8')
        ma=mass_file_structure_audit(mp,2020)
        assert ma['candidate_rows']==1 and ma['parsed_rows']==1 and ma['short_width_candidates']==0
        rp=td/'rct.txt'
        rp.write_text('HEADER\n'+reaction_line(vintage=2020,kind='rct2',A=48,Z=20,el='Ca',vals=['1']*6,uncs=['0']*6)+'\n',encoding='utf-8')
        ra=reaction_file_structure_audit(rp,2020,'rct2')
        assert ra['candidate_rows']==1 and ra['parsed_rows']==1 and ra['short_width_candidates']==0

def test_derived_observables_and_history():
    # Synthetic positive binding energies in keV.
    rows=[]
    specs=[
        (2,2,"He",7000.0),
        (4,4,"Be",7100.0),
        (5,4,"Be",7200.0),
        (6,4,"Be",7300.0),
        (7,4,"Be",7350.0),
        (8,4,"Be",7400.0),
        (6,5,"B",7250.0),
        (6,6,"C",7500.0),
    ]
    for N,Z,el,bea in specs:
        rows.append(parse_mass_line(mass2020_line(N=N,Z=Z,el=el,mass="-10000.000000",massu="1.000000",be=f"{bea:.5f}"),2020))
    d={(x["N"],x["Z"]):x for x in derive_observables(rows)}
    target=d[(6,4)]
    B=lambda N,Z: (N+Z)*next(r.be_per_A_keV for r in rows if r.N==N and r.Z==Z)
    assert abs(target["Sn_keV"]-(B(6,4)-B(5,4)))<1e-9
    assert abs(target["S2n_keV"]-(B(6,4)-B(4,4)))<1e-9
    assert abs(target["Sp_keV"]-(B(6,4)-B(6,3)))<1e-9 if (6,3) in d else target["Sp_keV"] is None
    # alpha Q value uses daughter + alpha - parent.
    qtarget=d[(6,6)]
    assert abs(qtarget["Qalpha_keV"]-(B(4,4)+B(2,2)-B(6,6)))<1e-9
    # A5: an estimated required neighbor makes the derived observable unavailable.
    rows_est=[]
    for r in rows:
        if (r.N,r.Z)==(5,4):
            rows_est.append(parse_mass_line(mass2020_line(N=5,Z=4,el="Be",mass="-10000.000000",massu="1.000000",be="7200#",beu="20#"),2020))
        else:
            rows_est.append(r)
    d_est={(x["N"],x["Z"]):x for x in derive_observables(rows_est)}
    assert d_est[(6,4)]["Sn_keV"] is None
    assert d_est[(6,4)]["S2n_keV"] is not None
    # Historical common-precision rule: extra printed decimals alone do not imply changed.
    old=parse_mass_line(mass_legacy_line(vintage=2016,N=28,Z=20,el="Ca",mass="-44224.68"),2016)
    new_same=parse_mass_line(mass2020_line(N=28,Z=20,el="Ca",mass="-44224.680001"),2020)
    new_diff=parse_mass_line(mass2020_line(N=29,Z=20,el="Ca",mass="-41000.123456"),2020)
    h=historical_membership([old],[new_same,new_diff],2016,2020)
    labels={(x["N"],x["Z"]):x["label"] for x in h}
    assert labels[(28,20)]=="unchanged"
    assert labels[(29,20)]=="new"


def main():
    tests=[test_mass_2020,test_mass_legacy,test_reaction_parsers,test_audits,test_file_structure_audits,test_derived_observables_and_history]
    for t in tests:
        t(); print(t.__name__+": PASS")
    print(f"ALL TESTS PASS ({len(tests)}/{len(tests)})")

if __name__=="__main__": main()
