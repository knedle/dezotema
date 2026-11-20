from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

from .io import nacti_osoby, nacti_temata, nacti_zdroj
from .model import REZIMY, STAVY, TYPY, VAZBY, VZTAHY


def validuj(root) -> list[str]:
    root = Path(root)
    err: list[str] = []

    def rel(p):
        return p.relative_to(root).as_posix() if p.is_relative_to(root) else str(p)

    def nacti(fn, p):
        try:
            return fn(p)
        except Exception as e:  # noqa: BLE001 - chyba dat se hlásí, ne propaguje
            err.append(f"{rel(p)}: nelze načíst ({type(e).__name__}: {e})")
            return None

    temata = nacti(nacti_temata, root / "data" / "temata.yaml") or {}
    osoby = nacti(nacti_osoby, root / "data" / "osoby.yaml") or {}
    zdroje = []
    for p in sorted((root / "data" / "zdroje").glob("*/*/*.yaml")):
        z = nacti(nacti_zdroj, p)
        if z is None:
            continue
        if z.id != p.stem:
            err.append(f"{rel(p)}: id zdroje '{z.id}' neodpovídá názvu souboru")
        if not isinstance(z.datum, date):
            err.append(f"{rel(p)}: datum není platné datum ({z.datum!r}) (zdroj '{z.id}')")
        elif (p.parent.parent.name, p.parent.name) != (f"{z.datum:%Y}", f"{z.datum:%m}"):
            err.append(f"{rel(p)}: adresář neodpovídá datu {z.datum} (zdroj '{z.id}')")
        zdroje.append(z)
    ids = Counter(v.id for z in zdroje for v in z.vyroky)
    for i, n in ids.items():
        if n > 1:
            err.append(f"{i}: duplicitní id výroku ({n}x)")
    for i, n in Counter(z.id for z in zdroje).items():
        if n > 1:
            err.append(f"{i}: duplicitní id zdroje ({n}x)")
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
            for t in v.temata or []:
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
            for d in v.dalsi_zdroje or []:
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
