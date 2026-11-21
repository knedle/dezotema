from __future__ import annotations

import posixpath
import re

from ..index import Archiv
from ..model import Vyrok, Zdroj

SYMBOL_VZTAH = {"pozitivni": "✅", "negativni": "❌", "rozporuplny": "⚖️", "neutralni": "○"}
SYMBOL_STAV = {"ceka": "🕐", "potvrzeno": "✅", "vyvraceno": "❌", "castecne": "⚠️"}

_VAZBA_TEXT = {"posun": "posun oproti", "opakovani": "opakuje",
               "konflikt": "⚡ konflikt s", "souhlas": "souhlasí s"}


def bunka(text: str) -> str:
    """Text bezpečný pro buňku tabulky (bez zalomení a svislítek)."""
    return " ".join(str(text).split()).replace("|", "\\|")


def datum_cz(d) -> str:
    return f"{d.day}. {d.month}. {d.year}"


def jmeno_osoby(archiv: Archiv, slug: str) -> str:
    o = archiv.osoby.get(slug)
    return o.jmeno if o and o.jmeno else slug


def odkaz_prepisu(rel: str, prepis: str) -> str:
    """Cesta k přepisu: `prepis` je buď cesta relativní k wiki (prepisy/done/x.txt), nebo holé jméno."""
    return f"{rel}{prepis}" if prepis.startswith("prepisy/") else f"{rel}prepisy/done/{prepis}"


def odkaz_zdroje(z: Zdroj, rel: str) -> str:
    return f"{rel}zdroje/{z.datum:%Y-%m}.md#{z.id}"


def odkaz_vyroku(archiv: Archiv, vid: str, rel: str) -> str | None:
    cil = archiv.vyroky.get(vid)
    if not cil:
        return None
    v, _ = cil
    stranka = archiv.stranka_vyroku(vid)
    if not stranka:
        return None
    return f"[{bunka(v.nadpis)}]({rel}{stranka}#{v.id})"


def render_vyrok(v: Vyrok, z: Zdroj, archiv: Archiv, rel: str) -> str:
    hlavicka = [f"**{jmeno_osoby(archiv, archiv.mluvci_vyroku(v, z))}**", datum_cz(z.datum)]
    if v.typ != "tvrzeni":
        hlavicka.append(v.typ)
    hlavicka.append(f"[{z.titul}]({odkaz_zdroje(z, rel)})")
    hlavicka.append(f"[přepis]({odkaz_prepisu(rel, z.prepis)})")

    bloky = [f"### {v.nadpis} {{#{v.id}}}", " · ".join(hlavicka), v.text.strip()]
    for c in v.citace:
        radky = f"„{c.text}“".splitlines() or [""]
        if c.cas:
            radky[-1] += f" [{c.cas}]"
        bloky.append("\n".join(f"> {r}".rstrip() for r in radky))

    if v.osoby:
        casti = []
        for r in v.osoby:
            s = f"{jmeno_osoby(archiv, r.osoba)} {SYMBOL_VZTAH.get(r.vztah, '')}".rstrip()
            casti.append(s + (f" — {r.kontext}" if r.kontext else ""))
        bloky.append("*Osoby:* " + "; ".join(casti))
    if v.vazby:
        casti = []
        for va in v.vazby:
            cil = odkaz_vyroku(archiv, va.na, rel) or va.na
            casti.append(f"{_VAZBA_TEXT.get(va.typ, va.typ)} {cil}")
        bloky.append("*Vazby:* " + "; ".join(casti))
    return "\n\n".join(bloky) + "\n"


_KOREN_ODKAZ = re.compile(r"(\]\()/(?!/)([^)\s]*)")


def zrelativni(text: str, stranka: str) -> str:
    """Odkazy v datech jsou kořenové (`](/temata/x.md#id)`, kořen = wiki); při vykreslení stránky
    `stranka` (cesta vůči wiki) se převedou na relativní. Jiné odkazy se nemění."""
    zakladna = posixpath.dirname(stranka) or "."

    def nahrad(m):
        cesta, hash_, kotva = m.group(2).partition("#")
        rel = posixpath.relpath(cesta, zakladna) if cesta else ""
        return f"{m.group(1)}{rel}{hash_}{kotva}"

    return _KOREN_ODKAZ.sub(nahrad, text)
