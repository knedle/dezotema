"""Převod tabulky `stochasticky-teror.md` staré wiki na výroky typu stoch-teror (Task 7)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from tools.archiv.model import Citace, Teror, Vyrok, Zdroj
from tools.migrace.pomocne import kotvy_z_textu
from tools.migrace.temata import _datum_z

_HRANICNI = re.compile(r"\s*\(\s*hraniční\s*\)", re.I)
# „hraniční“ jako slovo (ne „zahraničního“): před kmenem nesmí být písmeno
_HRANICNI_SLOVO = re.compile(r"(?<![^\W\d_])hraničn", re.I)
_BEZ_SLOV = re.compile(r"\[\s*(?:\.\.\.|…)\s*\]|…|\.\.\.")


@dataclass
class TerorRaw:
    autor_text: str
    terc: str                 # bez značky „(hraniční)“
    hranicni: bool
    citace: list[str]         # jen doslovné „citované“ části sloupce (bez uvozovek)
    kontext: str              # redakční text sloupce mimo citace (citace nahrazeny „…“)
    datum: date | None
    kotvy: list[str]
    sloupec_citace: str = ""  # původní obsah sloupce


def rozdel_sloupec(sloupec: str) -> tuple[list[str], str]:
    """Sloupec -> (citace nejvyšší úrovně „…“, redakční zbytek). Vnořené uvozovky zůstávají
    v citaci; bez citované části je celý sloupec zbytek."""
    spans: list[tuple[int, int]] = []
    hloubka, start = 0, 0
    for i, ch in enumerate(sloupec):
        if ch == "„":
            if hloubka == 0:
                start = i
            hloubka += 1
        elif ch in "“”\"" and hloubka > 0:
            hloubka -= 1
            if hloubka == 0:
                spans.append((start, i))
    if hloubka > 0:                       # neuzavřená uvozovka: citace do konce
        spans.append((start, len(sloupec)))
    if not spans:
        return [], sloupec.strip()
    citace, zbytek, pos = [], "", 0
    for s, e in spans:
        zbytek += sloupec[pos:s] + "…"
        citace.append(sloupec[s + 1:e].strip())
        pos = e + 1
    zbytek += sloupec[pos:]
    if not re.search(r"[A-Za-zÁ-ž]{3,}", _BEZ_SLOV.sub("", zbytek)):
        return citace, ""                 # nic redakčního mimo citace
    zbytek = re.sub(r"^(?:…[\s—–/;,.]*)+", "", zbytek.strip()).strip()
    return citace, zbytek


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
        autor, terc, sloupec = bunky[0], bunky[1], " | ".join(bunky[2:-2])
        datum, zdroj = bunky[-2], bunky[-1]
        # „hraniční“ je značka u terče, nebo (častěji) poznámka v komentáři ke citaci
        hr = bool(_HRANICNI_SLOVO.search(terc + " " + sloupec))
        terc = _HRANICNI.sub("", terc).strip()
        citace, kontext = rozdel_sloupec(sloupec)
        out.append(TerorRaw(autor, terc, hr, citace, kontext, _datum_z(datum),
                            kotvy_z_textu(zdroj), sloupec))
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
        # bez redakčního textu mimo citace: nouzově jen terč (hlásí se v reportu)
        text=raw.kontext or f"Terč: {raw.terc}.",
        citace=[Citace(c) for c in raw.citace],
        mluvci=kdo if kdo != zdroj.mluvci else None,
        teror=Teror(terc=raw.terc, hranicni=raw.hranicni),
    )
