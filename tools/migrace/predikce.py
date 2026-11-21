"""Převod `predikce.md` staré wiki na výroky typu predikce (Task 7)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from tools.archiv.model import Citace, Predikce, Vyhodnoceni, Vyrok, Zdroj
from tools.migrace.pomocne import kotvy_z_textu, strip_citace

# datum vyhodnocení bez vlastního data (audit staré wiki z 20. 11. 2026)
DATUM_AUDITU = date(2026, 11, 20)

STAVY_SYMBOL = {"🕐": "ceka", "✅": "potvrzeno", "❌": "vyvraceno", "⚠": "castecne"}
_STAV_STITEK = re.compile(r"^(Čeká na vyhodnocení|Potvrzeno|Vyvráceno|Částečně|Nerozhodnuto)\s*")

_NADPIS = re.compile(r"^(?P<mluvci>.+?) — (?P<nazev>.+?)\s*\((?P<d>\d{1,2})\.(?:\s?[–-]\s?\d{1,2}\.)?\s?(?P<m>\d{1,2})\.(?:\s+a\s+\d{1,2}\.\s?\d{1,2}\.)?"
                     r"\s?(?P<y>\d{4})(?:,\s*(?P<ex>[^)]*))?\)\s*$")
_POLE = re.compile(r"^\*\*(Předpověď|Horizont|Stav|Zdroj):\*\*\s*(.*)$")
_DATOVANA = re.compile(r"^\*\*(\d{1,2})\.\s?(\d{1,2})\.([^*]*)\*\*\s*(?:—\s*)?(.*)$")
_VYHODNOCENI = re.compile(r"^\*\*Vyhodnocení(?:\s+(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4}))?:\*\*\s*(.*)$")
_POZNAMKA = re.compile(r"^(⚡\s*)?\*\*(Poznámka|Konflikt):\*\*\s*(.*)$")
_DM = re.compile(r"^(\d{1,2})\.\s?(\d{1,2})\.\s*")
_CITACE = re.compile(r"^>\s*(.*)$")
_DATUM_V_HORIZONTU = re.compile(r"(?<![\d.])(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})(?!\d)")
_DO_DATA = re.compile(r"\bdo\s+(?:cca\s+)?(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})(?!\d)")
_DO_ROKU = re.compile(r"\bdo\s+(?:roku\s+)?(\d{4})\b(?!\s*[./]\s*\d)")


@dataclass
class PredikceRaw:
    mluvci_text: str
    nazev: str
    datum: date
    predpoved: str = ""
    citace: list[str] = field(default_factory=list)
    horizont: str = ""
    stav: str = "ceka"
    stav_text: str = ""
    vyhodnoceni: list[Vyhodnoceni] = field(default_factory=list)   # datované poznámky
    doplneni: list[str] = field(default_factory=list)              # nedatované odstavce
    kotvy: list[str] = field(default_factory=list)
    nadpis_md: str = ""


def _bezpecne(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def horizont_do(horizont: str) -> date | None:
    """Datum jen z jednoznačného údaje: `do [cca] D. M. YYYY`, jediné `D. M. YYYY`
    (mimo „od …“), `do [roku] YYYY` -> 31. 12. Jinak None."""
    m = _DO_DATA.search(horizont)
    if m:
        return _bezpecne(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    data = [mm for mm in _DATUM_V_HORIZONTU.finditer(horizont)
            if not re.search(r"\b(od|po)\s+(?:cca\s+)?$", horizont[:mm.start()])]
    if len(data) == 1:
        mm = data[0]
        return _bezpecne(int(mm.group(3)), int(mm.group(2)), int(mm.group(1)))
    if not data:
        m = _DO_ROKU.search(horizont)
        if m and 1990 <= int(m.group(1)) <= 2100:
            return date(int(m.group(1)), 12, 31)
    return None


def _rok(d: int, m: int, hlavicka: date) -> date | None:
    """Rok datované poznámky = rok výroku (po přelomu roku +1)."""
    x = _bezpecne(hlavicka.year, m, d)
    if x is not None and x < hlavicka:
        x = _bezpecne(hlavicka.year + 1, m, d)
    return x


def _stav(text: str) -> tuple[str, str]:
    text = text.strip()
    kod = STAVY_SYMBOL.get(text[:1], "ceka")
    zbytek = text.lstrip("🕐✅❌⚠️️ ").strip()
    m = _STAV_STITEK.match(zbytek)
    stitek = m.group(1) if m else ""
    zbytek = zbytek[m.end():] if m else zbytek
    zbytek = re.sub(r"^—\s*", "", zbytek.strip()).strip()
    if stitek == "Nerozhodnuto":
        zbytek = f"Nerozhodnuto — {zbytek}" if zbytek else "Nerozhodnuto"
    return kod, zbytek


def _poznamka_datum(text: str, hlavicka: date) -> tuple[date, str]:
    m = _DM.match(text)
    if m:
        d = _rok(int(m.group(1)), int(m.group(2)), hlavicka)
        if d:
            return d, text
    return hlavicka, text


def parsuj(md: str) -> list[PredikceRaw]:
    md = md.lstrip("﻿")
    bloky = re.split(r"(?m)^### ", md)[1:]
    out: list[PredikceRaw] = []
    for blok in bloky:
        radky = blok.splitlines()
        nadpis = radky[0].strip()
        m = _NADPIS.match(nadpis)
        if not m:
            raise ValueError(f"nelze parsovat nadpis predikce: {nadpis!r}")
        datum = date(int(m.group("y")), int(m.group("m")), int(m.group("d")))
        nazev = m.group("nazev").strip()
        if m.group("ex"):                     # např. „(30. 5. 2026, citováno Vrabel)“
            nazev = f"{nazev} ({m.group('ex').strip()})"
        raw = PredikceRaw(m.group("mluvci").strip(), nazev, datum, nadpis_md=nadpis)
        for r in radky[1:]:
            r = r.rstrip()
            if not r.strip() or r.strip() == "---" or r.startswith("<!--"):
                continue
            pm = _POLE.match(r)
            if pm:
                pole, hod = pm.groups()
                if pole == "Předpověď":
                    raw.predpoved = hod
                elif pole == "Horizont":
                    raw.horizont = hod
                elif pole == "Stav":
                    raw.stav, raw.stav_text = _stav(hod)
                else:
                    raw.kotvy = kotvy_z_textu(hod)
                continue
            cm = _CITACE.match(r)
            if cm:
                q = cm.group(1)
                # „citace“ — Jméno: atribuce se zahodí (mluvčí je v nadpisu)
                qm = re.match(r"^(„.*?[“”\"])\s*(?:—\s*[^„“”\"]*)?$", q)
                raw.citace.append(strip_citace(qm.group(1) if qm else q))
                continue
            vm = _VYHODNOCENI.match(r)
            if vm:
                if vm.group(1):
                    d = _bezpecne(int(vm.group(3)), int(vm.group(2)), int(vm.group(1))) or DATUM_AUDITU
                else:
                    d = DATUM_AUDITU
                raw.vyhodnoceni.append(Vyhodnoceni(d, vm.group(4).strip()))
                continue
            dm = _DATOVANA.match(r)
            if dm:
                d = _rok(int(dm.group(1)), int(dm.group(2)), datum) or datum
                stitek = dm.group(3).strip()
                text = dm.group(4).strip()
                if stitek:
                    text = f"{stitek} {text}".strip()
                raw.vyhodnoceni.append(Vyhodnoceni(d, text))
                continue
            zm = _POZNAMKA.match(r)
            if zm:
                konflikt = zm.group(2) == "Konflikt"
                d, text = _poznamka_datum(zm.group(3).strip(), datum)
                if konflikt:
                    text = f"Konflikt: {text}"
                raw.vyhodnoceni.append(Vyhodnoceni(d, text))
                continue
            raw.doplneni.append(r.strip())
        out.append(raw)
    return out


def na_vyrok(raw: PredikceRaw, zdroj: Zdroj, poradi: int | str, mluvci: str | None = None,
             temata: list[str] | None = None, dalsi_zdroje: list[str] | None = None) -> Vyrok:
    """`mluvci` = slug mluvčího (id výroku); do pole `mluvci` se zapíše jen když se liší
    od mluvčího zdroje."""
    kdo = mluvci or zdroj.mluvci
    cislo = f"{poradi:02d}" if isinstance(poradi, int) else poradi
    vyh: list[Vyhodnoceni] = []
    if raw.stav != "ceka" or raw.stav_text:
        vyh.append(Vyhodnoceni(DATUM_AUDITU, raw.stav_text or "—", raw.stav))
    vyh += raw.vyhodnoceni
    text = "\n\n".join([raw.predpoved] + raw.doplneni).strip()
    return Vyrok(
        id=f"{kdo}-{zdroj.datum.isoformat()}-{cislo}",
        typ="predikce",
        temata=list(temata or []),
        nadpis=raw.nazev,
        text=text,
        citace=[Citace(c) for c in raw.citace],
        mluvci=kdo if kdo != zdroj.mluvci else None,
        dalsi_zdroje=[d for d in (dalsi_zdroje or []) if d != zdroj.id],
        predikce=Predikce(horizont=raw.horizont, stav=raw.stav, horizont_do=horizont_do(raw.horizont),
                          vyhodnoceni=vyh),
    )
