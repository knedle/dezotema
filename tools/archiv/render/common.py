from __future__ import annotations

from ..index import Archiv
from ..model import Vyrok, Zdroj

SYMBOL_VZTAH = {"pozitivni": "✅", "negativni": "❌", "rozporuplny": "⚖️", "neutralni": "○"}
SYMBOL_STAV = {"ceka": "🕐", "potvrzeno": "✅", "vyvraceno": "❌", "castecne": "⚠️"}

_VAZBA_TEXT = {"posun": "posun oproti", "opakovani": "opakuje",
               "konflikt": "⚡ konflikt s", "souhlas": "souhlasí s"}


def datum_cz(d) -> str:
    return f"{d.day}. {d.month}. {d.year}"


def jmeno_osoby(archiv: Archiv, slug: str) -> str:
    o = archiv.osoby.get(slug)
    return o.jmeno if o and o.jmeno else slug


def odkaz_vyroku(archiv: Archiv, vid: str, rel: str) -> str | None:
    cil = archiv.vyroky.get(vid)
    if not cil:
        return None
    v, _ = cil
    tema = v.temata[0] if v.temata else ""
    return f"[{v.nadpis}]({rel}temata/{tema}.md#{v.id})"


def render_vyrok(v: Vyrok, z: Zdroj, archiv: Archiv, rel: str) -> str:
    hlavicka = [f"**{jmeno_osoby(archiv, archiv.mluvci_vyroku(v, z))}**", datum_cz(z.datum)]
    if v.typ != "tvrzeni":
        hlavicka.append(v.typ)
    hlavicka.append(f"[{z.titul}]({rel}zdroje/{z.datum:%Y-%m}.md#{z.id})")
    hlavicka.append(f"[přepis]({rel}prepisy/done/{z.prepis})")

    bloky = [f"### {v.nadpis} {{#{v.id}}}", " · ".join(hlavicka), v.text.strip()]
    for c in v.citace:
        bloky.append(f"> „{c.text}“" + (f" [{c.cas}]" if c.cas else ""))

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
