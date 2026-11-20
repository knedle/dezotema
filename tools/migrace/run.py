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


def _s_opakovanim(fn, pokusu=5):
    """Windows občas vrátí EINVAL/EACCES při zápisu (zámek souboru antivirem) — zkus znovu."""
    import time
    for i in range(pokusu):
        try:
            return fn()
        except OSError:
            if i == pokusu - 1:
                raise
            time.sleep(0.2 * (i + 1))


def krok_temata(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    """Výroky z tematických stránek. Smaže dříve zapsané výroky typu tvrzeni (idempotence)."""
    from collections import Counter

    import yaml

    from tools.archiv.io import _Dumper, _clean, nacti_vse
    from tools.migrace.temata import (parsuj_stranku, pripoj_neprirazene, prirad,
                                      sestav_vyroky)

    zdroje, temata, osoby = nacti_vse(root)
    for z in zdroje:
        z.vyroky = [v for v in z.vyroky if v.typ != "tvrzeni"]
    by_id = {z.id: z for z in zdroje}
    obsazena = {v.id for z in zdroje for v in z.vyroky}
    mapa = json.loads((root / "data" / "migrace" / "kotvy-zdroju.json").read_text(encoding="utf-8"))

    jednotky, stranky = [], 0
    for slug in temata:
        p = stara_wiki / f"{slug}.md"
        if not p.is_file():
            print(f"CHYBÍ stránka tématu: {p}")
            continue
        stranky += 1
        jednotky += parsuj_stranku(p.read_text(encoding="utf-8"), slug, osoby)
    prirazene, neprirazene = prirad(jednotky, mapa, by_id)
    s = sestav_vyroky(prirazene, by_id, obsazena)
    neprirazene = pripoj_neprirazene(neprirazene, s)
    zmenene = set()
    for zid, vs in s.vyroky.items():
        by_id[zid].vyroky.extend(vs)
        zmenene.add(zid)
    for zid in sorted(zmenene):
        _s_opakovanim(lambda: uloz_zdroj(by_id[zid], root))

    # nepřiřazené jednotky
    nez = [{"tema": j.tema, "kapitola": j.kapitola, "nadpis": j.nadpis,
            "datum": j.datum.isoformat() if j.datum else None, "mluvci": j.mluvci,
            "text": j.text, "citace": [_clean(c) for c in j.citace],
            "kotvy_zdroju": j.kotvy_zdroju, "duvod": j.duvod} for j in neprirazene]
    with open(root / "data" / "zdroje" / "_nezarazeno.yaml", "w", encoding="utf-8",
              newline="\n") as f:
        yaml.dump({"jednotky": nez}, f, Dumper=_Dumper, allow_unicode=True, sort_keys=False,
                  width=100)

    # staré kotvy sekcí (a kapitol) -> id prvního přiřazeného výroku sekce
    id_podle = {id(j): vid for (j, _), vid in zip(prirazene, s.id_jednotek)}
    id_podle.update({id(j): j.vyrok_id for j in jednotky if j.vyrok_id})
    prvni_v_sekci: dict = {}
    for j in jednotky:
        if id_podle.get(id(j)):
            prvni_v_sekci.setdefault((j.tema, j.sekce), id_podle[id(j)])
    stranky_map: dict[str, str] = {}
    kapitoly_map: dict[str, str] = {}
    bez_vyroku: list[str] = []
    videne_sekce = set()
    for j in jednotky:
        klic_sekce = (j.tema, j.sekce)
        vid = id_podle.get(id(j))
        if klic_sekce not in videne_sekce and j.sekce_kotvy:
            # první přiřazená jednotka sekce
            prvni = prvni_v_sekci.get(klic_sekce)
            for k in j.sekce_kotvy:
                if prvni:
                    stranky_map.setdefault(f"{j.tema}.md#{k}", prvni)
                else:
                    bez_vyroku.append(f"{j.tema}.md#{k}")
            videne_sekce.add(klic_sekce)
        if vid:
            for k in j.kapitola_kotvy:
                kapitoly_map.setdefault(f"{j.tema}.md#{k}", vid)
    holy: dict[str, str] = {}
    kolize: dict[str, list[str]] = {}
    cile: dict[str, set[str]] = {}
    for k, vid in stranky_map.items():
        cile.setdefault(k.split("#", 1)[1], set()).add(vid)
    for k, vid in stranky_map.items():
        a = k.split("#", 1)[1]
        if len(cile[a]) == 1:        # unikátní, nebo víc stránek míří na tentýž výrok
            holy[a] = vid
        else:
            kolize.setdefault(a, []).append(k)
    out = {"stranky": stranky_map, "kotvy": holy, "kolize": kolize,
           "kapitoly": kapitoly_map, "bez_vyroku": bez_vyroku}
    (root / "data" / "migrace" / "stare-kotvy.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    n = len(jednotky)
    zp = Counter(j.zpusob for j, _ in prirazene)
    print(f"temata: {stranky} stránek, {n} jednotek, přiřazeno {len(prirazene)}, "
          f"nepřiřazeno {len(neprirazene)} ({100 * len(neprirazene) / max(n, 1):.1f} %); "
          f"{sum(1 for j in jednotky if j.vyrok_id)} nepřiřazených připojeno (téma) ke kopii sekce "
          f"jiné stránky")
    print(f"  výroků zapsáno {sum(len(v) for v in s.vyroky.values())} do {len(zmenene)} zdrojů; "
          f"sloučeno (více témat) {s.slouceno}, z toho s jiným textem {s.slouceno_jiny_text}")
    print(f"  dalsi_zdroje: {sum(1 for j, _ in prirazene if j.dalsi_zdroje)} jednotek, "
          f"{sum(len(j.dalsi_zdroje) for j, _ in prirazene)} odkazů")
    print(f"  způsob přiřazení: {dict(zp)}")
    print(f"  mluvčí přepsán (host): "
          f"{sum(1 for z in zmenene for v in by_id[z].vyroky if v.mluvci)}")
    print(f"  stare-kotvy: {len(stranky_map)} (stránka#kotva), {len(holy)} holých, "
          f"{len(kolize)} kolizí, {len(kapitoly_map)} kapitol, {len(bez_vyroku)} bez výroku")
    for a, ks in sorted(kolize.items()):
        print(f"  KOLIZE kotvy {a}: {', '.join(ks)}")
    print(f"  důvody nepřiřazení: {dict(Counter(j.duvod.split(' (')[0][:40] for j in neprirazene))}")


KROKY = {"zdroje": krok_zdroje, "temata": krok_temata}


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
