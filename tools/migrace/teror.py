"""Převod tabulky `stochasticky-teror.md` staré wiki na výroky typu stoch-teror (Task 7)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from tools.archiv.model import Citace, Teror, Vyrok, Zdroj
from tools.migrace.pomocne import kotvy_z_textu, strip_citace
from tools.migrace.temata import _datum_z

_HRANICNI = re.compile(r"\s*\(\s*hraniční\s*\)", re.I)
# „citace“ — komentář: první uzavírací uvozovka následovaná pomlčkou
_CITACE_KONTEXT = re.compile(r"^(?P<q>„.*?[“”\"])\s+[—–]\s+(?P<k>.+)$", re.S)


@dataclass
class TerorRaw:
    autor_text: str
    terc: str                 # bez značky „(hraniční)“
    hranicni: bool
    citace: str               # citace (bez uvozovek, bez komentáře)
    kontext: str              # komentář za citací (může být prázdný)
    datum: date | None
    kotvy: list[str]
    sloupec_citace: str = ""  # původní obsah sloupce


def parsuj(md: str) -> list[TerorRaw]:
    out: list[TerorRaw] = []
    v_tabulce = False
    for r in md.splitlines():
        if r.startswith("| Autor"):
            v_tabulce = True
            continue
        if not v_tabulce:
            continue
        if not r.startswith("|"):
            if out:
                break
            continue
        if r.startswith("|--") or r.startswith("| --"):
            continue
        bunky = [b.strip() for b in r.strip().strip("|").split("|")]
        if len(bunky) < 5:
            raise ValueError(f"řádek tabulky teroru má {len(bunky)} sloupců: {r[:80]!r}")
        autor, terc, citace = bunky[0], bunky[1], " | ".join(bunky[2:-2])
        datum, zdroj = bunky[-2], bunky[-1]
        # „hraniční“ je značka u terče, nebo (častěji) poznámka v komentáři ke citaci
        hr = "hraničn" in (terc + " " + citace).lower()
        terc = _HRANICNI.sub("", terc).strip()
        m = _CITACE_KONTEXT.match(citace)
        if m:
            q, k = strip_citace(m.group("q")), m.group("k").strip()
        elif citace.startswith("„"):
            q, k = strip_citace(citace), ""
        else:                      # popis bez citace (např. e-mail s předmětem …)
            q, k = citace, ""
        out.append(TerorRaw(autor, terc, hr, q, k, _datum_z(datum), kotvy_z_textu(zdroj), citace))
    return out


def na_vyrok(raw: TerorRaw, zdroj: Zdroj, poradi: int | str, mluvci: str | None = None,
             temata: list[str] | None = None) -> Vyrok:
    kdo = mluvci or zdroj.mluvci
    cislo = f"{poradi:02d}" if isinstance(poradi, int) else poradi
    return Vyrok(
        id=f"{kdo}-{zdroj.datum.isoformat()}-{cislo}",
        typ="stoch-teror",
        temata=list(temata or []),
        nadpis=raw.terc,
        text=raw.kontext or f"Terč: {raw.terc}.",
        citace=[Citace(raw.citace)] if raw.citace else [],
        mluvci=kdo if kdo != zdroj.mluvci else None,
        teror=Teror(terc=raw.terc, hranicni=raw.hranicni),
    )
