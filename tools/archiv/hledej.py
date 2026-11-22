"""Rychlé hledání výroků v archivu (pro dohledání vazeb při zpracování).

Použití:
    python -m tools.archiv.hledej [-m MLUVCI] [-n N] [-t] VZOR [VZOR ...]

Každý VZOR je regulární výraz (bez ohledu na velikost písmen) hledaný v nadpisu
a textu výroku (s -t jen v nadpisu). Výpis: id | typ | nadpis | vazby.
Pořadí: od nejstaršího, takže první řádek je obvykle původní výrok.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

try:
    _Loader = yaml.CSafeLoader
except AttributeError:  # pragma: no cover
    _Loader = yaml.SafeLoader

KOREN = Path(__file__).resolve().parents[2] / "data" / "zdroje"


def nacti():
    rows = []
    for f in sorted(KOREN.rglob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            d = yaml.load(fh, Loader=_Loader) or {}
        for v in d.get("vyroky") or []:
            rows.append(v)
    return rows


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("vzory", nargs="+")
    ap.add_argument("-m", "--mluvci", help="prefix id, např. zitko")
    ap.add_argument("-n", type=int, default=8, help="max. výsledků na vzor")
    ap.add_argument("-t", action="store_true", help="hledat jen v nadpisu")
    a = ap.parse_args(argv)
    rows = nacti()
    if a.mluvci:
        rows = [v for v in rows if v["id"].startswith(a.mluvci + "-")]
    for vzor in a.vzory:
        rx = re.compile(vzor, re.I)
        print(f"== {vzor}")
        c = 0
        for v in rows:
            hay = v.get("nadpis", "") if a.t else f"{v.get('nadpis', '')} {v.get('text', '') or ''}"
            if rx.search(hay):
                vaz = ",".join(f"{x['typ']}:{x['na']}" for x in v.get("vazby") or [])
                print(f"  {v['id']} | {v.get('typ')} | {v.get('nadpis', '')[:100]}" + (f" | {vaz}" if vaz else ""))
                c += 1
                if c >= a.n:
                    break


if __name__ == "__main__":
    main()
