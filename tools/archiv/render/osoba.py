from __future__ import annotations

from ..index import Archiv
from ..model import Osoba
from .common import (SYMBOL_VZTAH, bunka, datum_cz, jmeno_osoby, odkaz_vyroku, odkaz_zdroje)
from .predikce import HLAVICKA as PRED_HLAVICKA, bilance, radek_predikce
from .teror import HLAVICKA as TERROR_HLAVICKA, radek_teroru


def _odkaz_mluvci_zminky(archiv: Archiv, v, z, rel: str) -> str:
    if v is not None:
        o = odkaz_vyroku(archiv, v.id, rel)
        if o:
            return o
    return f"[{bunka(z.titul)}]({odkaz_zdroje(z, rel)})"


def render_osoba(archiv: Archiv, osoba: Osoba, souhrn_text: str) -> str:
    rel = "../"
    vyroky = archiv.podle_mluvciho(osoba.slug)
    zdroje = [z for z in archiv.zdroje if z.mluvci == osoba.slug]
    out = [f"# {osoba.jmeno}\n"]
    if osoba.popis:
        out.append(osoba.popis.strip() + "\n")
    if souhrn_text:
        out.append(souhrn_text)
    out += ["## Zdroje\n", f"Zpracovaných zdrojů: {len(zdroje)} — [přehled zdrojů](../zdroje/index.md)\n"]

    out.append("## Podle témat\n")
    podle: dict[str, list] = {}
    for v, z in vyroky:
        for t in v.temata:
            podle.setdefault(t, []).append(v)
    for t in sorted(podle, key=lambda s: (archiv.temata[s].nazev if s in archiv.temata else s).casefold()):
        out.append(f"### {archiv.temata[t].nazev if t in archiv.temata else t}\n")
        out += [f"- [{bunka(v.nadpis)}]({rel}{archiv.stranka_vyroku(v.id, t)}#{v.id})" for v in podle[t]]
        out.append("")

    pred = [(v, z) for v, z in archiv.predikce() if archiv.mluvci_vyroku(v, z) == osoba.slug]
    if pred:
        out += ["## Predikce\n", f"Bilance: {bilance(pred)}\n", *PRED_HLAVICKA]
        out += [radek_predikce(archiv, v, z, rel) for v, z in pred]
        out.append("")

    ter = [(v, z) for v, z in archiv.teror() if archiv.mluvci_vyroku(v, z) == osoba.slug]
    if ter:
        out += ["## Stochastický teror\n", *TERROR_HLAVICKA]
        out += [radek_teroru(archiv, v, z, rel) for v, z in ter]
        out.append("")

    zminky: dict[str, list] = {}
    for v, z in vyroky:
        for r in v.osoby:
            zminky.setdefault(r.osoba, []).append((r, v, z))
    if zminky:
        out.append("## Zmínění lidé\n")
        for slug in sorted(zminky, key=lambda s: jmeno_osoby(archiv, s).casefold()):
            out.append(f"### [{jmeno_osoby(archiv, slug)}]({rel}zminene/{slug}.md)\n")
            out += ["| Datum | Vztah | Kontext | Výrok |", "|---|---|---|---|"]
            for r, v, z in sorted(zminky[slug], key=lambda t: t[2].datum):
                out.append(f"| {datum_cz(z.datum)} | {SYMBOL_VZTAH.get(r.vztah, '')} {r.vztah} "
                           f"| {bunka(r.kontext)} | {_odkaz_mluvci_zminky(archiv, v, z, rel)} |")
            out.append("")
    return "\n".join(out)


def render_zminene(archiv: Archiv, osoba: Osoba) -> str:
    rel = "../"
    out = [f"# {osoba.jmeno}\n"]
    if osoba.popis:
        out.append(osoba.popis.strip() + "\n")
    out += ["## Kdo o osobě mluvil\n", "| Datum | Mluvčí | Vztah | Kontext | Odkaz |", "|---|---|---|---|---|"]
    for r, v, z in sorted(archiv.zminky_osoby(osoba.slug), key=lambda t: t[2].datum):
        mluvci = archiv.mluvci_vyroku(v, z) if v is not None else z.mluvci
        out.append(f"| {datum_cz(z.datum)} | {jmeno_osoby(archiv, mluvci)} "
                   f"| {SYMBOL_VZTAH.get(r.vztah, '')} {r.vztah} | {bunka(r.kontext)} "
                   f"| {_odkaz_mluvci_zminky(archiv, v, z, rel)} |")
    return "\n".join(out) + "\n"
