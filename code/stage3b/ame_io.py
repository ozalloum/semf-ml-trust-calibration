#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class MassRow:
    vintage: int
    N: int
    Z: int
    A: int
    element: str
    origin: str
    mass_excess_keV: float | None
    mass_excess_unc_keV: float | None
    be_per_A_keV: float | None
    be_per_A_unc_keV: float | None
    beta_mode: str
    beta_keV: float | None
    beta_unc_keV: float | None
    atomic_mass_u: float | None
    atomic_mass_unc_micro_u: float | None
    mass_estimated: bool
    be_estimated: bool
    beta_estimated: bool
    atomic_mass_estimated: bool
    mass_excess_raw: str
    be_per_A_raw: str
    raw_line: str


@dataclass
class ReactionRow:
    vintage: int
    kind: str
    A: int
    Z: int
    N: int
    element: str
    v1: float | None
    u1: float | None
    v2: float | None
    u2: float | None
    v3: float | None
    u3: float | None
    v4: float | None
    u4: float | None
    v5: float | None
    u5: float | None
    v6: float | None
    u6: float | None
    e1: bool
    e2: bool
    e3: bool
    e4: bool
    e5: bool
    e6: bool
    raw_line: str

    def named(self) -> dict:
        if self.kind == "rct1":
            names = ["S2n_keV", "S2p_keV", "Qalpha_keV", "Q2beta_keV", "Qep_keV", "Qbeta_n_keV"]
        elif self.kind == "rct2":
            names = ["Sn_keV", "Sp_keV", "Q4beta_keV", "Qda_keV", "Qpa_keV", "Qna_keV"]
        else:
            raise ValueError(self.kind)
        vals = [self.v1, self.v2, self.v3, self.v4, self.v5, self.v6]
        uncs = [self.u1, self.u2, self.u3, self.u4, self.u5, self.u6]
        ests = [self.e1, self.e2, self.e3, self.e4, self.e5, self.e6]
        d = {"vintage": self.vintage, "kind": self.kind, "N": self.N, "Z": self.Z, "A": self.A, "element": self.element}
        for n, v, u, e in zip(names, vals, uncs, ests):
            d[n] = v
            d[n.replace("_keV", "_unc_keV")] = u
            d[n.replace("_keV", "_estimated")] = e
        d["raw_line"] = self.raw_line
        return d


def parse_num(token: str) -> tuple[float | None, bool]:
    raw = token.strip()
    if not raw or "*" in raw:
        return None, False
    estimated = "#" in raw
    clean = raw.replace("#", ".")
    try:
        return float(clean), estimated
    except ValueError:
        return None, estimated


def decimal_places(token: str) -> int | None:
    raw = token.strip().replace("#", ".")
    if not raw or "*" in raw:
        return None
    m = re.search(r"\.(\d+)", raw)
    return len(m.group(1)) if m else 0


def _atom(ai: str, afr: str) -> tuple[float | None, bool]:
    estimated = "#" in (ai + afr)
    if not ai.strip() or not afr.strip() or "*" in (ai + afr):
        return None, estimated
    try:
        return float(ai.strip()) + 1e-6 * float(afr.strip().replace("#", ".")), estimated
    except ValueError:
        return None, estimated


def parse_mass_line(line: str, vintage: int) -> MassRow | None:
    if vintage == 2020:
        if len(line) < 123:
            return None
        try:
            N = int(line[4:9]); Z = int(line[9:14]); A = int(line[14:19])
        except ValueError:
            return None
        if A != N + Z:
            return None
        element = line[20:23].strip(); origin = line[23:27].strip()
        mass_raw = line[28:42]; mass, mass_est = parse_num(mass_raw)
        mass_unc, _ = parse_num(line[42:54])
        be_raw = line[54:67]; be, be_est = parse_num(be_raw)
        be_unc, _ = parse_num(line[68:78])
        beta_mode = line[79:81].strip()
        beta, beta_est = parse_num(line[81:94])
        beta_unc, _ = parse_num(line[94:105])
        atom, atom_est = _atom(line[106:109], line[110:123])
        atom_unc, _ = parse_num(line[123:135] if len(line) >= 135 else "")
    elif vintage in (2012, 2016):
        if len(line) < 112:
            return None
        try:
            N = int(line[4:9]); Z = int(line[9:14]); A = int(line[14:19])
        except ValueError:
            return None
        if A != N + Z:
            return None
        element = line[20:23].strip(); origin = line[23:27].strip()
        mass_raw = line[28:41]; mass, mass_est = parse_num(mass_raw)
        mass_unc, _ = parse_num(line[41:52])
        be_raw = line[52:63]; be, be_est = parse_num(be_raw)
        be_unc, _ = parse_num(line[63:72])
        beta_mode = line[73:75].strip()
        beta, beta_est = parse_num(line[75:86])
        beta_unc, _ = parse_num(line[86:95])
        atom, atom_est = _atom(line[96:99], line[100:112])
        atom_unc, _ = parse_num(line[112:123] if len(line) >= 123 else "")
    else:
        raise ValueError(f"Unsupported vintage: {vintage}")
    if not element:
        return None
    return MassRow(
        vintage=vintage, N=N, Z=Z, A=A, element=element, origin=origin,
        mass_excess_keV=mass, mass_excess_unc_keV=mass_unc,
        be_per_A_keV=be, be_per_A_unc_keV=be_unc,
        beta_mode=beta_mode, beta_keV=beta, beta_unc_keV=beta_unc,
        atomic_mass_u=atom, atomic_mass_unc_micro_u=atom_unc,
        mass_estimated=mass_est, be_estimated=be_est, beta_estimated=beta_est,
        atomic_mass_estimated=atom_est,
        mass_excess_raw=mass_raw.strip(), be_per_A_raw=be_raw.strip(), raw_line=line,
    )


def parse_mass_file(path: Path, vintage: int) -> list[MassRow]:
    rows: list[MassRow] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            row = parse_mass_line(line.rstrip("\n\r"), vintage)
            if row is not None:
                rows.append(row)
    return rows


def parse_reaction_line(line: str, vintage: int, kind: str) -> ReactionRow | None:
    if kind not in {"rct1", "rct2"}:
        raise ValueError(kind)
    if len(line) < 12:
        return None
    try:
        A = int(line[1:4]); element = line[5:8].strip(); Z = int(line[8:11])
    except ValueError:
        return None
    if not element or A < Z:
        return None
    N = A - Z
    start = 12
    if vintage == 2020:
        vw, uw = 12, 10
    elif vintage in (2012, 2016):
        vw, uw = 10, 8
    else:
        raise ValueError(vintage)
    vals: list[float | None] = []
    uncs: list[float | None] = []
    ests: list[bool] = []
    pos = start
    for _ in range(6):
        vtok = line[pos:pos+vw]; pos += vw
        utok = line[pos:pos+uw]; pos += uw
        v, est_v = parse_num(vtok)
        u, est_u = parse_num(utok)
        vals.append(v); uncs.append(u); ests.append(est_v or est_u)
    return ReactionRow(vintage, kind, A, Z, N, element, *sum(([vals[i], uncs[i]] for i in range(6)), []), *ests, line)


def parse_reaction_file(path: Path, vintage: int, kind: str) -> list[ReactionRow]:
    rows: list[ReactionRow] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            row = parse_reaction_line(line.rstrip("\n\r"), vintage, kind)
            if row is not None:
                rows.append(row)
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_stats(path: Path) -> dict:
    with path.open("rb") as f:
        lines = sum(1 for _ in f)
    return {"bytes": path.stat().st_size, "lines": lines, "sha256": sha256(path)}


def write_csv(rows: Iterable[dict], path: Path) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k); fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def download(urls: list[str], dest: Path, timeout: int = 60) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ctx = ssl.create_default_context()
    errors = []
    for url in urls:
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Paper3-SEMF-reproducibility/1.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp, tmp.open("wb") as out:
                shutil.copyfileobj(resp, out)
            if tmp.stat().st_size < 1000:
                raise RuntimeError(f"Downloaded file unexpectedly small: {tmp.stat().st_size} bytes")
            tmp.replace(dest)
            return {"url": url, **file_stats(dest)}
        except Exception as e:
            errors.append(f"{url}: {type(e).__name__}: {e}")
            if tmp.exists():
                tmp.unlink()
    raise RuntimeError("All download sources failed:\n" + "\n".join(errors))



def mass_file_structure_audit(path: Path, vintage: int) -> dict:
    expected_width = 135 if vintage == 2020 else 123
    candidate_rows = parsed_rows = short_width = a_fail = empty_element = 0
    lengths: list[int] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n\r")
            if len(line) < 19:
                continue
            try:
                N = int(line[4:9]); Z = int(line[9:14]); A = int(line[14:19])
            except ValueError:
                continue
            candidate_rows += 1
            lengths.append(len(line))
            short_width += int(len(line) < expected_width)
            a_fail += int(A != N + Z)
            empty_element += int(len(line) < 23 or not line[20:23].strip())
            parsed_rows += int(parse_mass_line(line, vintage) is not None)
    return {
        "candidate_rows": candidate_rows,
        "parsed_rows": parsed_rows,
        "unparsed_candidate_rows": candidate_rows - parsed_rows,
        "expected_min_width": expected_width,
        "short_width_candidates": short_width,
        "min_candidate_width": min(lengths) if lengths else None,
        "max_candidate_width": max(lengths) if lengths else None,
        "A_identity_failures": a_fail,
        "empty_element": empty_element,
    }


def reaction_file_structure_audit(path: Path, vintage: int, kind: str) -> dict:
    expected_width = 144 if vintage == 2020 else 120
    candidate_rows = parsed_rows = short_width = a_fail = empty_element = 0
    lengths: list[int] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n\r")
            if len(line) < 11:
                continue
            try:
                A = int(line[1:4]); Z = int(line[8:11])
            except ValueError:
                continue
            candidate_rows += 1
            lengths.append(len(line))
            short_width += int(len(line) < expected_width)
            empty_element += int(len(line) < 8 or not line[5:8].strip())
            row = parse_reaction_line(line, vintage, kind)
            parsed_rows += int(row is not None)
            if row is not None:
                a_fail += int(row.A != row.N + row.Z)
    return {
        "candidate_rows": candidate_rows,
        "parsed_rows": parsed_rows,
        "unparsed_candidate_rows": candidate_rows - parsed_rows,
        "expected_min_width": expected_width,
        "short_width_candidates": short_width,
        "min_candidate_width": min(lengths) if lengths else None,
        "max_candidate_width": max(lengths) if lengths else None,
        "A_identity_failures": a_fail,
        "empty_element": empty_element,
    }

def mass_audit(rows: list[MassRow]) -> dict:
    keys = [(r.N, r.Z) for r in rows]
    return {
        "rows": len(rows),
        "unique_keys": len(set(keys)),
        "duplicates": len(keys) - len(set(keys)),
        "A_identity_failures": sum(r.A != r.N + r.Z for r in rows),
        "empty_element": sum(not r.element for r in rows),
        "estimated_mass_rows": sum(r.mass_estimated for r in rows),
        "estimated_be_rows": sum(r.be_estimated for r in rows),
        "missing_mass_rows": sum(r.mass_excess_keV is None for r in rows),
        "missing_be_rows": sum(r.be_per_A_keV is None for r in rows),
    }


def reaction_audit(rows: list[ReactionRow]) -> dict:
    keys = [(r.N, r.Z) for r in rows]
    return {
        "rows": len(rows),
        "unique_keys": len(set(keys)),
        "duplicates": len(keys) - len(set(keys)),
        "A_identity_failures": sum(r.A != r.N + r.Z for r in rows),
        "empty_element": sum(not r.element for r in rows),
    }


def dump_json(obj: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
