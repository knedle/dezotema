"""Parsování staré wiki/_zdroje.md na kostry zdrojů (bez výroků)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from tools.archiv.model import Osoba, Zdroj
from tools.archiv.slug import ascii_slug, slugify
from tools.migrace.ciselniky import ALIASY

_KOTVA = re.compile(r"\s*\{#([^}]+)\}\s*$")
_POLE = re.compile(r"^- \*\*([^*]+?):\*\*\s*(.*)$")
_ODKAZ = re.compile(r"^\[[^\]]*\]\(([^)\s]+)\)")


@dataclass
class ZdrojRaw:
    nadpis: str
    kotva: str
    pole: dict[str, str]


def parsuj_zdroje(md: str) -> list[ZdrojRaw]:
    md = md.lstrip("﻿")
    out: list[ZdrojRaw] = []
    for sekce in re.split(r"^(?=## )", md, flags=re.M)[1:]:
        radky = sekce.splitlines()
        nadpis = radky[0][3:].strip()
        m = _KOTVA.search(nadpis)
        if m:
            kotva, nadpis = m.group(1), nadpis[:m.start()].strip()
        else:
            kotva = slugify(nadpis)
        pole: dict[str, str] = {}
        for r in radky[1:]:
            pm = _POLE.match(r)
            if pm:
                pole[pm.group(1)] = pm.group(2).strip()
        out.append(ZdrojRaw(nadpis, kotva, pole))
    return out


def _norm(s: str) -> str:
    return ascii_slug(s)


def _bez_zavorek(s: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


def _lookup(osoby: dict[str, Osoba]) -> dict[str, str]:
    idx: dict[str, str] = {}
    for slug, o in osoby.items():
        for jm in [slug, o.jmeno, _bez_zavorek(o.jmeno), *o.aliasy, *ALIASY.get(slug, [])]:
            idx.setdefault(_norm(jm), slug)
    return idx


def _najdi_mluvce(nadpis: str, kanal: str, osoby: dict[str, Osoba]) -> str:
    idx = _lookup(osoby)
    prefix = nadpis.split(" — ", 1)[0] if " — " in nadpis else ""
    kandidati = []
    if prefix:
        kandidati += [prefix, _bez_zavorek(prefix), *reversed(prefix.split("/"))]
    m = re.search(r"mluvčí:\s*\**([^*;]+?)\**\s*$", kanal)
    if m:
        kandidati.append(m.group(1))
    kandidati += [kanal, _bez_zavorek(kanal), *kanal.split("/")]
    for k in kandidati:
        k = _bez_zavorek(k.strip())
        if k and _norm(k) in idx:
            return idx[_norm(k)]
    raise ValueError(f"neznámý mluvčí: {nadpis!r} / {kanal!r}")


def _titul(nadpis: str) -> str:
    return nadpis.split(" — ", 1)[1].strip() if " — " in nadpis else nadpis


def na_zdroj(raw: ZdrojRaw, osoby: dict[str, Osoba]) -> Zdroj:
    p = raw.pole
    kanal = p.get("Kanál", "")
    mluvci = _najdi_mluvce(raw.nadpis, kanal, osoby)
    dm = re.match(r"(\d{4}-\d{2}-\d{2})(?:,\s*(?:cca\s*)?(\d{1,2}:\d{2}))?", p.get("Datum záznamu", ""))
    if not dm:
        raise ValueError(f"nelze přečíst datum: {raw.nadpis!r}")
    datum = date.fromisoformat(dm.group(1))
    soubor = _ODKAZ.search(p.get("Soubor", ""))
    if not soubor:
        raise ValueError(f"chybí soubor přepisu: {raw.nadpis!r}")
    url = p.get("URL", "").strip().strip("<>")
    titul = _titul(raw.nadpis)
    delka_raw = p.get("Délka", "")
    delka, _, zhl = delka_raw.partition(" | ")
    casti = [p.get("Poznámka", "")]
    zbytek = p["Soubor"][soubor.end():].strip()
    if zbytek:
        casti.append(f"Soubor: {zbytek}")
    if zhl:
        casti.append(zhl.strip().rstrip("."))
    if p.get("Popis"):
        casti.append(f"Popis: {p['Popis']}")
    if p.get("Řečník"):
        casti.append(f"Řečník: {p['Řečník']}")
    poznamka = " ".join(c for c in casti if c) or None
    if mluvci == "vrabel":
        rezim = "vrabel"
    elif "přeskočeno" in p.get("Poznámka", "").lower():
        rezim = "preskoceno"
    else:
        rezim = "standard"
    zid = f"{datum.isoformat()}_{mluvci}_{ascii_slug(titul)[:60].strip('-')}"
    return Zdroj(id=zid, mluvci=mluvci, kanal=kanal, titul=titul, datum=datum, url=url,
                 prepis=soubor.group(1), rezim=rezim, cas=dm.group(2),
                 delka=delka.strip() or None, poznamka=poznamka)


def unikatni_ids(zdroje: list[Zdroj]) -> list[Zdroj]:
    """Při kolizi přidá -2, -3 … (mění zdroje na místě)."""
    videno: set[str] = set()
    for z in zdroje:
        zaklad, n = z.id, 1
        while z.id in videno:
            n += 1
            z.id = f"{zaklad}-{n}"
        videno.add(z.id)
    return zdroje


def mapa_kotev(raws: list[ZdrojRaw], zdroje: list[Zdroj]) -> dict[str, str]:
    """Kotva (jak ji vygeneruje MkDocs, i s příponou _1 při duplicitě) -> id zdroje."""
    out: dict[str, str] = {}
    for r, z in zip(raws, zdroje, strict=True):
        k, n = r.kotva, 0
        while k in out:
            n += 1
            k = f"{r.kotva}_{n}"
        out[k] = z.id
    return out
