"""Kroky migrace predikce, teror, prehled, osoby (Task 7). Spouští je tools.migrace.run."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.archiv.index import Archiv
from tools.archiv.io import _clean, nacti_vse, uloz_osoby, uloz_zdroj
from tools.archiv.slug import slugify
from tools.migrace import osoby as O
from tools.migrace import predikce as P
from tools.migrace import prehled as H
from tools.migrace import teror as T
from tools.migrace.pomocne import (dalsi_cislo, najdi_zdroje, vyber_temata,
                                   vyber_temata_globalne, zajisti_osobu, zdroj_podle_mluvciho)
from tools.migrace.run import _s_opakovanim, _uloz_nezarazeno
from tools.migrace.temata import _osoba_volne, _slova, index_osob


def _ulozit_zmenene(zdroje, snimky: dict, root: Path) -> int:
    n = 0
    for z in zdroje:
        if _clean(z) != snimky[z.id]:
            _s_opakovanim(lambda z=z: uloz_zdroj(z, root))
            n += 1
    return n


def _nacti_kontext(root: Path):
    zdroje, temata, osoby = nacti_vse(root)
    snimky = {z.id: _clean(z) for z in zdroje}
    mapa = json.loads((root / "data" / "migrace" / "kotvy-zdroju.json").read_text(encoding="utf-8"))
    return zdroje, temata, osoby, snimky, mapa


def _ulozit_osoby(osoby: dict, root: Path) -> None:
    _s_opakovanim(lambda: uloz_osoby(list(osoby.values()), root / "data" / "osoby.yaml"))


def _vsechna_id(zdroje) -> set[str]:
    return {v.id for z in zdroje for v in z.vyroky}


def krok_predikce(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    """Výroky typu predikce z predikce.md. Nahrazuje jen dříve zapsané výroky typu predikce."""
    zdroje, temata, osoby, snimky, mapa = _nacti_kontext(root)
    for z in zdroje:
        z.vyroky = [v for v in z.vyroky if v.typ != "predikce"]
    by_id = {z.id: z for z in zdroje}
    ids = _vsechna_id(zdroje)
    idx = index_osob(osoby)
    pocet_osob = len(osoby)
    raws = P.parsuj((stara_wiki / "predikce.md").read_text(encoding="utf-8"))
    nez, bez_temat, override, anchor = [], [], Counter(), {}
    pouzite_kotvy: set[str] = set()
    zapsano = 0
    for raw in raws:
        kdo = zajisti_osobu(raw.mluvci_text, osoby, idx)
        kand = najdi_zdroje(raw.kotvy, mapa, by_id)
        if kand:
            primarni = max(enumerate(kand), key=lambda iz: (iz[1].datum == raw.datum,
                                                            iz[1].mluvci == kdo, -iz[0]))[1]
        else:
            primarni = zdroj_podle_mluvciho(by_id, kdo, raw.datum)
        if primarni is None or kdo is None:
            nez.append({"nadpis": raw.nadpis_md, "kotvy": raw.kotvy, "duvod": "zdroj nenalezen"})
            continue
        temata_v = vyber_temata(primarni, raw.nazev + " " + raw.predpoved)
        if not temata_v:
            temata_v = vyber_temata_globalne(zdroje, kdo, raw.nazev + " " + raw.predpoved)                 or vyber_temata_globalne(zdroje, primarni.mluvci, raw.nazev + " " + raw.predpoved)
            bez_temat.append(f"{raw.nadpis_md} -> {temata_v}")
        v = P.na_vyrok(raw, primarni, dalsi_cislo(ids, kdo, primarni.datum), mluvci=kdo,
                       temata=temata_v, dalsi_zdroje=[z.id for z in kand])
        ids.add(v.id)
        primarni.vyroky.append(v)
        zapsano += 1
        if v.mluvci:
            override[v.mluvci] += 1
        a0 = slugify(raw.nadpis_md)
        a, n = a0, 0
        while a in pouzite_kotvy:
            n += 1
            a = f"{a0}_{n}"
        pouzite_kotvy.add(a)
        anchor[f"predikce.md#{a}"] = v.id
    zm = _ulozit_zmenene(zdroje, snimky, root)
    if len(osoby) != pocet_osob:
        _ulozit_osoby(osoby, root)
    _uloz_nezarazeno(root, "predikce", nez)
    p = root / "data" / "migrace" / "stare-kotvy.json"
    sk = json.loads(p.read_text(encoding="utf-8"))
    sk["stranky"] = {k: v for k, v in sk["stranky"].items() if not k.startswith("predikce.md#")}
    sk["stranky"].update(anchor)
    p.write_text(json.dumps(sk, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    stav = Counter(v.predikce.stav for z in zdroje for v in z.vyroky if v.typ == "predikce")
    print(f"predikce: {len(raws)} v souboru, {zapsano} zapsáno do {zm} zdrojů, "
          f"{len(nez)} nezařazeno, {len(bez_temat)} bez témat; nové osoby {len(osoby) - pocet_osob}")
    print(f"  stavy: {dict(stav)}; mluvčí přepsán: {dict(override)}")
    for b in bez_temat:
        print(f"  BEZ TÉMAT: {b}")


def krok_teror(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    """Výroky typu stoch-teror z tabulky stochasticky-teror.md."""
    zdroje, temata, osoby, snimky, mapa = _nacti_kontext(root)
    for z in zdroje:
        z.vyroky = [v for v in z.vyroky if v.typ != "stoch-teror"]
    by_id = {z.id: z for z in zdroje}
    ids = _vsechna_id(zdroje)
    idx = index_osob(osoby)
    raws = T.parsuj((stara_wiki / "stochasticky-teror.md").read_text(encoding="utf-8"))
    nez, bez_temat, nerozpoznan, cizi = [], 0, [], Counter()
    zapsano = hranicnich = 0
    for raw in raws:
        kand = najdi_zdroje(raw.kotvy, mapa, by_id)
        autor = None
        if "(" not in raw.autor_text:
            autor = _osoba_volne(raw.autor_text, idx, 3)
            if autor is None:
                nerozpoznan.append(raw.autor_text)
        z = kand[0] if kand else zdroj_podle_mluvciho(by_id, autor, raw.datum)
        if z is None:
            nez.append({"autor": raw.autor_text, "terc": raw.terc, "citace": raw.sloupec_citace,
                        "datum": raw.datum.isoformat() if raw.datum else None,
                        "kotvy": raw.kotvy, "hranicni": raw.hranicni, "duvod": "zdroj nenalezen"})
            continue
        kdo = autor or z.mluvci
        temata_v = vyber_temata(z, raw.terc + " " + raw.citace + " " + raw.kontext)
        if not temata_v:
            temata_v = vyber_temata_globalne(zdroje, kdo, raw.terc + " " + raw.citace)
            bez_temat += 1
        v = T.na_vyrok(raw, z, dalsi_cislo(ids, kdo, z.datum), mluvci=kdo, temata=temata_v)
        ids.add(v.id)
        z.vyroky.append(v)
        zapsano += 1
        hranicnich += raw.hranicni
        if v.mluvci:
            cizi[v.mluvci] += 1
    zm = _ulozit_zmenene(zdroje, snimky, root)
    _uloz_nezarazeno(root, "teror", nez)
    print(f"teror: {len(raws)} řádků, {zapsano} zapsáno do {zm} zdrojů, {len(nez)} nezařazeno, "
          f"{bez_temat} bez témat, {hranicnich} hraničních; autor nerozpoznán: {nerozpoznan}; "
          f"mluvčí přepsán: {dict(cizi)}")


def krok_prehled(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    """zdroj.prehled z denních přehledů zpravodajstvi-vrabel/*.md (nahradí celé zdroj.prehled)."""
    zdroje, temata, osoby, snimky, mapa = _nacti_kontext(root)
    for z in zdroje:
        z.prehled = []
    by_id = {z.id: z for z in zdroje}
    stare = json.loads((root / "data" / "migrace" / "stare-kotvy.json").read_text(encoding="utf-8"))
    nez, dnu, polozek, podle_data, podle_stranky = [], 0, 0, 0, 0
    for p in sorted((stara_wiki / "zpravodajstvi-vrabel").glob("*.md")):
        for den in H.parsuj_dny(p.read_text(encoding="utf-8"), stare):
            dnu += 1
            kand = najdi_zdroje(den.kotvy, mapa, by_id)
            z = kand[0] if kand else None
            if z is None:
                shoda = sorted((x for x in zdroje if x.mluvci == "vrabel" and x.datum == den.datum),
                               key=lambda x: x.id)
                if shoda:
                    z = max(enumerate(shoda),
                            key=lambda iz: (len(_slova(den.titul) & _slova(iz[1].titul)), -iz[0]))[1]
                    podle_data += 1
            if z is None:
                nez.append({"datum": den.datum.isoformat(), "titul": den.titul,
                            "polozky": [{"tema": x.tema, "text": x.text, "vyrok": x.vyrok}
                                        for x in den.polozky]})
                continue
            podle_stranky += H.prirad_stranky(den.polozky, z, temata)
            z.prehled.extend(den.polozky)
            polozek += len(den.polozky)
    zm = _ulozit_zmenene(zdroje, snimky, root)
    _uloz_nezarazeno(root, "prehled", nez)
    vsechny = [x for z in zdroje for x in z.prehled]
    print(f"prehled: {dnu} dnů, {dnu - len(nez)} přiřazeno ke zdroji ({podle_data} podle data), "
          f"{len(nez)} nezařazeno; {polozek} položek, z toho {sum(1 for x in vsechny if x.vyrok)} "
          f"s odkazem na výrok (z toho {podle_stranky} podle stránky bez kotvy + zdroje), "
          f"{sum(1 for x in vsechny if x.vyrok is None and '→ viz' in x.text)} s nepřeloženým "
          f"odkazem „viz“; zapsáno {zm} zdrojů")


def krok_osoby(stara_wiki: Path, root: Path, mkdocs: Path) -> None:
    """Zmíněné osoby z osoby/*.md. Smaže všechny OsobaRef (zdroje i výroky) a přiřadí znovu."""
    zdroje, temata, osoby, snimky, mapa = _nacti_kontext(root)
    for z in zdroje:
        z.osoby = []
        for v in z.vyroky:
            v.osoby = []
    zminky = []
    for p in sorted((stara_wiki / "osoby").glob("*.md")):
        if p.stem not in osoby:
            print(f"CHYBÍ osoba pro stránku {p.name}")
        zminky += O.parsuj_tabulku(p.read_text(encoding="utf-8"), p.stem)
    pocet_osob = len(osoby)
    vys = O.prirad(zminky, Archiv(zdroje, temata, osoby), mapa)
    zm = _ulozit_zmenene(zdroje, snimky, root)
    if len(osoby) != pocet_osob:
        _ulozit_osoby(osoby, root)
    _uloz_nezarazeno(root, "zminky", [
        {"osoba": x.osoba_text, "vztah": x.vztah, "kontext": x.kontext,
         "datum": x.datum.isoformat() if x.datum else None, "kotva": x.kotva_zdroje,
         "stranka": x.mluvci_stranky} for x in vys.nezarazeno])
    print(f"osoby: {len(zminky)} řádků tabulek; OsobaRef do výroku {vys.do_vyroku}, "
          f"do zdroje {vys.do_zdroje}; nezařazeno {len(vys.nezarazeno)}; "
          f"nové osoby {vys.nove_osoby}; zapsáno {zm} zdrojů")
