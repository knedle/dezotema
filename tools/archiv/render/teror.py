from __future__ import annotations

from ..index import Archiv
from .common import bunka as _bunka, datum_cz, jmeno_osoby, odkaz_vyroku, odkaz_zdroje


def radek_teroru(archiv: Archiv, v, z, rel: str) -> str:
    citace = " […] ".join(c.text for c in v.citace) or v.text
    terc = v.teror.terc if v.teror else ""
    odkazy = f"[zdroj]({odkaz_zdroje(z, rel)})"
    vyrok = odkaz_vyroku(archiv, v.id, rel)
    if vyrok:
        odkazy += f" · {vyrok}"
    return (f"| {jmeno_osoby(archiv, archiv.mluvci_vyroku(v, z))} | {_bunka(terc)} "
            f"| „{_bunka(citace)}“ | {datum_cz(z.datum)} | {odkazy} |")


HLAVICKA = ["| Autor | Terč | Citace | Datum | Zdroj |", "|---|---|---|---|---|"]


def render_teror(archiv: Archiv, poznamky: str) -> str:
    vse = archiv.teror()
    hlavni = [(v, z) for v, z in vse if not (v.teror and v.teror.hranicni)]
    hranicni = [(v, z) for v, z in vse if v.teror and v.teror.hranicni]
    out = ["# Stochastický teror — sledované výroky\n",
           "Evidence výroků s pojmenovaným terčem a dehumanizací nebo výzvou k trestu.\n",
           "## Přehled výroků\n", *HLAVICKA]
    out += [radek_teroru(archiv, v, z, "") for v, z in hlavni]
    out.append("")
    if hranicni:
        out += ["## Hraniční případy\n", *HLAVICKA]
        out += [radek_teroru(archiv, v, z, "") for v, z in hranicni]
        out.append("")
    if poznamky.strip():
        out += ["## Poznámky\n", poznamky.strip(), ""]
    return "\n".join(out)
