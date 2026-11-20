from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from .io import nacti_vse
from .model import REZIMY, STAVY, TYPY, VAZBY, VZTAHY


def validuj(root) -> list[str]:
    root = Path(root)
    zdroje, temata, osoby = nacti_vse(root)
    err: list[str] = []
    ids = Counter(v.id for z in zdroje for v in z.vyroky)
    for i, n in ids.items():
        if n > 1:
            err.append(f"{i}: duplicitní id výroku ({n}x)")
    zdroj_ids = {z.id for z in zdroje}
    vyrok_ids = set(ids)

    def osoba_refs(refs, kde):
        for r in refs:
            if r.osoba not in osoby:
                err.append(f"{kde}: neznámá osoba '{r.osoba}'")
            if r.vztah not in VZTAHY:
                err.append(f"{kde}: neplatný vztah '{r.vztah}'")

    for z in zdroje:
        if z.rezim not in REZIMY:
            err.append(f"{z.id}: neplatný režim '{z.rezim}'")
        if z.mluvci not in osoby:
            err.append(f"{z.id}: neznámý mluvčí '{z.mluvci}'")
        if not (root / "wiki" / z.prepis).is_file():
            err.append(f"{z.id}: přepis neexistuje: wiki/{z.prepis}")
        osoba_refs(z.osoby, z.id)
        for p in z.prehled:
            if p.vyrok and p.vyrok not in vyrok_ids:
                err.append(f"{z.id}: přehled odkazuje na neexistující výrok '{p.vyrok}'")
        for v in z.vyroky:
            if v.typ not in TYPY:
                err.append(f"{v.id}: neplatný typ '{v.typ}'")
            if v.mluvci and v.mluvci not in osoby:
                err.append(f"{v.id}: neznámý mluvčí '{v.mluvci}'")
            if not v.temata:
                err.append(f"{v.id}: výrok nemá žádné téma")
            for t in v.temata:
                if t not in temata:
                    err.append(f"{v.id}: neznámé téma '{t}'")
            if v.typ == "predikce" and v.predikce is None:
                err.append(f"{v.id}: typ predikce vyžaduje blok predikce")
            if v.typ == "stoch-teror" and v.teror is None:
                err.append(f"{v.id}: typ stoch-teror vyžaduje blok teror")
            if v.predikce:
                if v.predikce.stav not in STAVY:
                    err.append(f"{v.id}: neplatný stav predikce '{v.predikce.stav}'")
                for h in v.predikce.vyhodnoceni:
                    if h.stav is not None and h.stav not in STAVY:
                        err.append(f"{v.id}: neplatný stav vyhodnocení '{h.stav}'")
            osoba_refs(v.osoby, v.id)
            for va in v.vazby:
                if va.typ not in VAZBY:
                    err.append(f"{v.id}: neplatný typ vazby '{va.typ}'")
                if va.na not in vyrok_ids:
                    err.append(f"{v.id}: vazba na neexistující výrok '{va.na}'")
            for d in v.dalsi_zdroje:
                if d not in zdroj_ids:
                    err.append(f"{v.id}: dalsi_zdroje odkazuje na neexistující zdroj '{d}'")
    for t in temata.values():
        if t.nadrazene and t.nadrazene not in temata:
            err.append(f"{t.slug}: neznámé nadřazené téma '{t.nadrazene}'")
    return err


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path(".")
    errors = validuj(root)
    for e in errors:
        print(e)
    print(f"{len(errors)} chyb" if errors else "OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
