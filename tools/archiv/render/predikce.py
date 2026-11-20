from __future__ import annotations

from collections import Counter
from datetime import date

from ..index import Archiv
from .common import SYMBOL_STAV, bunka, datum_cz, jmeno_osoby, odkaz_zdroje, render_vyrok


def _mesic(z) -> str:
    return f"{z.datum:%Y-%m}"


def radek_predikce(archiv: Archiv, v, z, rel: str) -> str:
    p = v.predikce
    odkaz = f"[{bunka(v.nadpis)}]({rel}predikce/{_mesic(z)}.md#{v.id})"
    return (f"| {jmeno_osoby(archiv, archiv.mluvci_vyroku(v, z))} | {datum_cz(z.datum)} "
            f"| {odkaz} | {bunka(p.horizont) if p else ''} "
            f"| {SYMBOL_STAV.get(p.stav, '') if p else ''} |")


HLAVICKA = ["| Mluvčí | Datum | Predikce | Horizont | Stav |", "|---|---|---|---|---|"]


def bilance(dvojice) -> str:
    c = Counter(v.predikce.stav for v, _ in dvojice if v.predikce)
    return " · ".join(f"{SYMBOL_STAV[s]} {c[s]}" for s in SYMBOL_STAV if c.get(s))


def render_predikce(archiv: Archiv, dnes: date) -> dict[str, str]:
    vse = archiv.predikce()
    out = ["# Predikce\n"]
    if vse:
        out.append(f"Celkem {len(vse)} predikcí. Bilance: {bilance(vse)}\n")
    propadle = archiv.nevyhodnocene_propadle(dnes)
    if propadle:
        out += ["## Propadlé k vyhodnocení\n", *HLAVICKA]
        out += [radek_predikce(archiv, v, z, "../") for v, z in propadle]
        out.append("")
    out += ["## Všechny predikce\n", *HLAVICKA]
    out += [radek_predikce(archiv, v, z, "../") for v, z in vse]
    out.append("")
    mesice: dict[str, list] = {}
    for v, z in vse:
        mesice.setdefault(_mesic(z), []).append((v, z))
    out.append("## Podle měsíců\n")
    out += [f"- [{m}]({m}.md) ({len(mesice[m])})" for m in sorted(mesice, reverse=True)]
    stranky = {"predikce/index.md": "\n".join(out) + "\n"}
    for m, dv in mesice.items():
        casti = [f"# Predikce {m}\n"]
        for v, z in dv:
            casti.append(render_vyrok(v, z, archiv, "../"))
            p = v.predikce
            if p:
                radky = [f"**Horizont:** {p.horizont}  ", f"**Stav:** {SYMBOL_STAV.get(p.stav, '')} {p.stav}"]
                for h in p.vyhodnoceni:
                    radky.append(f"\n**Vyhodnocení {datum_cz(h.datum)}:** {h.text}"
                                 + (f" ({SYMBOL_STAV.get(h.stav, '')})" if h.stav else ""))
                casti.append("\n".join(radky) + "\n")
            casti.append("---\n")
        stranky[f"predikce/{m}.md"] = "\n".join(casti)
    return stranky
