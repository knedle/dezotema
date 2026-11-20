"""Migrace staré wiki -> data/. Použití: python -m tools.migrace.run --krok zdroje"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.archiv.io import uloz_osoby, uloz_temata, uloz_zdroj
from tools.migrace.ciselniky import osoby_z_wiki, temata_z_wiki
from tools.migrace.zdroje import (mapa_kotev, na_zdroj, parsuj_zdroje,
                                  unikatni_ids)


def krok_zdroje(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    temata = temata_z_wiki(mkdocs.read_text(encoding="utf-8"),
                           (stara_wiki / "index.md").read_text(encoding="utf-8"))
    osoby = osoby_z_wiki(stara_wiki)
    uloz_temata(temata, root / "data" / "temata.yaml")
    uloz_osoby(osoby, root / "data" / "osoby.yaml")
    osoby_d = {o.slug: o for o in osoby}

    raws = parsuj_zdroje((stara_wiki / "_zdroje.md").read_text(encoding="utf-8"))
    zdroje, ok_raws, chyby = [], [], []
    for r in raws:
        try:
            zdroje.append(na_zdroj(r, osoby_d))
            ok_raws.append(r)
        except ValueError as e:
            chyby.append(str(e))
    unikatni_ids(zdroje)
    for z in zdroje:
        uloz_zdroj(z, root)
    kotvy = mapa_kotev(ok_raws, zdroje)
    out = root / "data" / "migrace" / "kotvy-zdroju.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kotvy, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"zdroje: {len(zdroje)} zapsáno z {len(raws)} sekcí; "
          f"{len(temata)} témat, {len(osoby)} osob, {len(kotvy)} kotev")
    for c in chyby:
        print("NEPARSOVÁNO:", c)


KROKY = {"zdroje": krok_zdroje}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--krok", required=True, help="čárkou oddělený seznam kroků")
    ap.add_argument("--stara-wiki", default=".superpowers/stara-wiki/wiki")
    ap.add_argument("--root", default=".")
    ap.add_argument("--mkdocs", default=None, help="výchozí <root>/mkdocs.yml")
    a = ap.parse_args(argv)
    root = Path(a.root)
    mkdocs = Path(a.mkdocs) if a.mkdocs else root / "mkdocs.yml"
    for krok in a.krok.split(","):
        if krok not in KROKY:
            print(f"neznámý krok: {krok}", file=sys.stderr)
            return 2
        KROKY[krok](Path(a.stara_wiki), root, mkdocs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
