"""Převod tabulek „Zmíněné osoby“ ze stránek `osoby/*.md` na `OsobaRef` (Task 7)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from tools.archiv.model import OsobaRef, Vyrok, Zdroj
from tools.archiv.slug import ascii_slug
from tools.migrace.pomocne import (kotvy_z_textu, najdi_zdroje, zajisti_osobu,
                                   zdroj_podle_mluvciho)
from tools.migrace.temata import _datum_z, index_osob

SYMBOLY = {"✅": "pozitivni", "❌": "negativni", "⚖": "rozporuplny", "○": "neutralni"}


@dataclass
class ZminkaRaw:
    osoba_text: str
    vztah: str
    kontext: str
    datum: date | None
    kotva_zdroje: str | None
    mluvci_stranky: str | None = None


def vztah_ze_symbolu(text: str) -> str:
    for s, v in SYMBOLY.items():
        if text.strip().startswith(s):
            return v
    raise ValueError(f"neznámý symbol vztahu: {text!r}")


def parsuj_tabulku(md: str, mluvci_stranky: str | None = None) -> list[ZminkaRaw]:
    i = md.find("## Zmíněné osoby")
    if i < 0:
        return []
    out: list[ZminkaRaw] = []
    for r in md[i:].splitlines()[1:]:
        if r.startswith("## "):
            break
        if not r.startswith("|") or r.startswith("|--") or r.startswith("| Osoba"):
            continue
        b = [x.strip() for x in r.strip().strip("|").split("|")]
        if len(b) < 5:
            raise ValueError(f"řádek zmíněných osob má {len(b)} sloupců: {r[:80]!r}")
        kotvy = kotvy_z_textu(b[-1])
        out.append(ZminkaRaw(b[0], vztah_ze_symbolu(b[1]), " | ".join(b[2:-2]), _datum_z(b[-2]),
                             kotvy[0] if kotvy else None, mluvci_stranky))
    return out


def rozdel_jmena(text: str) -> list[str]:
    """„A, B (role, funkce), C“ -> ['A', 'B (role, funkce)', 'C'] (čárky v závorkách se nedělí)."""
    out, hloubka, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            hloubka += 1
        elif ch == ")":
            hloubka = max(0, hloubka - 1)
        if ch == "," and hloubka == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


_PISMENO = "A-Za-zÁ-žÀ-ÿ"
_KONCOVKY = "aeiouyáéíóúůýě"


def _vzor_prijmeni(jmeno: str) -> re.Pattern | None:
    """Příjmení s diakritikou, VELKÝM počátečním písmenem a českými pádovými příponami."""
    slova = re.sub(r"\([^)]*\)", "", jmeno).split()
    if not slova:
        return None
    p = slova[-1].strip(".,;:")
    if len(p) < 4 or not p[0].isupper():
        return None
    kmen = p[:-1] if len(p) >= 5 and p[-1].lower() in _KONCOVKY else p
    kmeny = [kmen]
    if len(p) >= 5 and p[-2:].lower() in ("ec", "ek", "el"):    # Moravec -> Moravce, Moravcovo
        kmeny.append(p[:-2] + p[-1])
    alt = "|".join(re.escape(k) for k in kmeny)
    return re.compile(rf"(?<![{_PISMENO}])(?:{alt})[a-zá-žà-ÿ]{{0,4}}(?![{_PISMENO}])")


def efektivni_mluvci(v: Vyrok | None, z: Zdroj) -> str:
    return (v.mluvci if v is not None and v.mluvci else None) or z.mluvci


def najdi_vyrok(z: Zdroj, jmeno: str, mluvci: str | None = None) -> Vyrok | None:
    """Výrok zdroje (s efektivním mluvčím `mluvci`, je-li zadán), jehož text (nadpis, text,
    citace) nejčastěji obsahuje příjmení osoby – rozlišuje velikost písmen i diakritiku."""
    rx = _vzor_prijmeni(jmeno)
    if rx is None:
        return None
    nej, nej_n = None, 0
    for v in z.vyroky:
        if mluvci and efektivni_mluvci(v, z) != mluvci:
            continue
        t = " ".join([v.nadpis, v.text, *[c.text for c in v.citace]])
        n = len(rx.findall(t))
        if n > nej_n:
            nej, nej_n = v, n
    return nej


@dataclass
class Vysledek:
    do_vyroku: int = 0
    do_zdroje: int = 0
    nezarazeno: list[ZminkaRaw] = None  # type: ignore[assignment]
    nove_osoby: int = 0


def prirad(zminky: list[ZminkaRaw], archiv, kotvy: dict[str, str] | None = None) -> Vysledek:
    """Zapíše `OsobaRef` do výroku (příjmení v textu) nebo do `zdroj.osoby`, ale jen k výroku /
    zdroji, jehož efektivní mluvčí je autor stránky (`mluvci_stranky`; None = bez omezení).
    `kotvy` = mapa kotva `_zdroje.md` -> id zdroje. Neznámé osoby se doplní do `archiv.osoby`."""
    by_id = {z.id: z for z in archiv.zdroje}
    idx = index_osob(archiv.osoby)
    vys = Vysledek(nezarazeno=[])
    pred = len(archiv.osoby)
    for zm in zminky:
        z = None
        if zm.kotva_zdroje and kotvy:
            nalez = najdi_zdroje([zm.kotva_zdroje], kotvy, by_id)
            z = nalez[0] if nalez else None
        if z is None:
            z = zdroj_podle_mluvciho(by_id, zm.mluvci_stranky, zm.datum)
        strana = zm.mluvci_stranky
        if z is not None and strana and z.mluvci != strana \
                and not any(v.mluvci == strana for v in z.vyroky):
            z = None            # zdroj jiného mluvčího: řádek nelze přiřadit
        if z is None:
            vys.nezarazeno.append(zm)
            continue
        for jm in rozdel_jmena(zm.osoba_text):
            slug = zajisti_osobu(jm, archiv.osoby, idx)
            if not slug:
                vys.nezarazeno.append(ZminkaRaw(jm, zm.vztah, zm.kontext, zm.datum,
                                                zm.kotva_zdroje, zm.mluvci_stranky))
                continue
            ref = OsobaRef(slug, zm.vztah, zm.kontext)
            v = najdi_vyrok(z, jm, strana)
            if v is None and strana and z.mluvci != strana:
                v = next((x for x in z.vyroky if x.mluvci == strana), None)
            cil = v.osoby if v is not None else z.osoby
            if ref not in cil:
                cil.append(ref)
            if v is not None:
                vys.do_vyroku += 1
            else:
                vys.do_zdroje += 1
    vys.nove_osoby = len(archiv.osoby) - pred
    return vys
