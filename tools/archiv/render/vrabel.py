from __future__ import annotations

from ..index import Archiv
from .common import odkaz_vyroku, odkaz_zdroje


def vrabelovy_zdroje(archiv: Archiv):
    return sorted((z for z in archiv.zdroje if z.prehled),
                  key=lambda z: (z.datum, z.id), reverse=True)


def mesice_vrabel(archiv: Archiv) -> list[str]:
    return sorted({f"{z.datum:%Y-%m}" for z in vrabelovy_zdroje(archiv)}, reverse=True)


def render_vrabel(archiv: Archiv) -> dict[str, str]:
    stranky: dict[str, str] = {}
    for m in mesice_vrabel(archiv):
        casti = [f"# Zpravodajství Vrabel — {m}\n"]
        for z in (z for z in vrabelovy_zdroje(archiv) if f"{z.datum:%Y-%m}" == m):
            casti.append(f"## {z.datum:%Y-%m-%d} — {z.titul}\n")
            for p in z.prehled:
                tema = archiv.temata.get(p.tema)
                radek = f"- **{tema.nazev if tema else p.tema}:** "
                odkaz = odkaz_vyroku(archiv, p.vyrok, "../") if p.vyrok else None
                if odkaz:
                    radek += f"⚡ {p.text} → viz {odkaz}"
                else:
                    radek += p.text
                casti.append(radek)
            casti.append(f"\n**Zdroj:** [Video]({odkaz_zdroje(z, '../')})\n\n---\n")
        stranky[f"zpravodajstvi-vrabel/{m}.md"] = "\n".join(casti)
    return stranky
