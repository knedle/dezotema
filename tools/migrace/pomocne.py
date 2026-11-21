"""Společné pomůcky kroků predikce / teror / prehled / osoby (Task 7)."""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import unquote

from tools.archiv.model import Osoba, Vyrok, Zdroj
from tools.archiv.slug import ascii_slug
from tools.migrace.temata import _bez_zavorek, _osoba, _slova

_KOTVA = re.compile(r"_zdroje\.md#([^)\s]+)\)")
_ODKAZ = re.compile(r"\[[^\]]*\]\([^)]*\)")


def kotvy_z_textu(text: str) -> list[str]:
    """Kotvy `_zdroje.md#…` v textu (v pořadí výskytu, bez duplicit, odkódované)."""
    out: list[str] = []
    for k in _KOTVA.findall(text):
        k = unquote(k)
        if k not in out:
            out.append(k)
    return out


def najdi_zdroje(kotvy: list[str], mapa: dict[str, str], by_id: dict[str, Zdroj]) -> list[Zdroj]:
    out: list[Zdroj] = []
    for k in kotvy:
        z = by_id.get(mapa.get(k, ""))
        if z is not None and z not in out:
            out.append(z)
    return out


def zdroj_podle_mluvciho(by_id: dict[str, Zdroj], mluvci: str | None, datum: date | None
                         ) -> Zdroj | None:
    """Jediný zdroj daného mluvčího a data (jinak None)."""
    if not mluvci or not datum:
        return None
    kand = [z for z in by_id.values() if z.mluvci == mluvci and z.datum == datum]
    return kand[0] if len(kand) == 1 else None


def dalsi_cislo(ids: set[str], mluvci: str, datum: date) -> int:
    """Další volné pořadové číslo výroku (max + 1; id se nikdy nepoužije znovu)."""
    prefix = f"{mluvci}-{datum.isoformat()}-"
    nej = 0
    for i in ids:
        if i.startswith(prefix):
            m = re.match(r"\d+", i[len(prefix):])
            if m:
                nej = max(nej, int(m.group()))
    return nej + 1


def vyber_temata(zdroj: Zdroj, text: str) -> list[str]:
    """Témata výroku téhož zdroje, který se textem nejvíc shoduje; jinak []."""
    kand = [v for v in zdroj.vyroky if v.typ in ("tvrzeni", "postoj") and v.temata]
    if not kand:
        kand = [v for v in zdroj.vyroky if v.temata]
    if not kand:
        return []
    slova = _slova(text)
    nej = max(enumerate(kand), key=lambda iv: (len(slova & _slova(iv[1].nadpis + " " + iv[1].text)),
                                              -iv[0]))[1]
    return list(nej.temata)


def vyber_temata_globalne(zdroje: list[Zdroj], mluvci: str, text: str) -> list[str]:
    """Nouzově (zdroj nemá žádný výrok s tématem): témata výroku téhož mluvčího z celého
    archivu s největší shodou slov; bez shody nejčastější téma mluvčího."""
    from collections import Counter
    kand = [v for z in zdroje if z.mluvci == mluvci for v in z.vyroky
            if v.typ in ("tvrzeni", "postoj") and v.temata]
    if not kand:
        return []
    slova = _slova(text)
    shody = [(len(slova & _slova(v.nadpis + " " + v.text)), v) for v in kand]
    nej = max(s for s, _ in shody)
    if nej > 0:
        return list(next(v for s, v in shody if s == nej).temata)
    return [Counter(t for v in kand for t in v.temata).most_common(1)[0][0]]


# varianty přepisu téhož jména -> jeden slug
SLOUCENI_SLUGU = {"valerij-zaluznyj": "valerij-zaluzny"}


def zajisti_osobu(text: str, osoby: dict[str, Osoba], idx: dict[str, str],
                  max_slov: int = 3) -> str | None:
    """Slug osoby z jména; neznámá se doplní do číselníku (vlastni_stranka=False)."""
    popis = ""
    m = re.search(r"\(([^)]*)\)", text)
    if m:
        popis = m.group(1).strip()
    jm = _bez_zavorek(text).strip(" ,;:")
    if not jm:
        return None
    slug = _osoba(jm, idx)
    if slug:
        return slug
    slova = jm.split()
    for n in range(min(max_slov, len(slova) - 1), 1, -1):
        slug = _osoba(" ".join(slova[:n]), idx)
        if slug:
            return slug
    slug = ascii_slug(jm)
    if not slug:
        return None
    idx.setdefault(slug, slug)
    slug = SLOUCENI_SLUGU.get(slug, slug)        # varianty přepisu téhož jména
    if slug not in osoby:
        osoby[slug] = Osoba(slug=slug, jmeno=jm, popis=popis)
    elif jm != osoby[slug].jmeno and jm not in osoby[slug].aliasy:
        osoby[slug].aliasy.append(jm)
    idx[ascii_slug(jm)] = slug
    return slug


def bez_odkazu(text: str) -> str:
    return _ODKAZ.sub("", text)


def strip_citace(q: str) -> str:
    q = q.strip()
    if q[:1] in "„“\"":
        q = q[1:]
    if q[-1:] in "“”\"":
        q = q[:-1]
    return q.strip()

