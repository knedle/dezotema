from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..index import Archiv
from ..model import Tema
from .common import datum_cz, jmeno_osoby, render_vyrok

PRAH_ROZDELENI = 150


def souhrn(path: Path) -> str:
    """Obsah souhrnu s datem poslední aktualizace (mtime souboru); prázdný řetězec, pokud není."""
    if not path.is_file():
        return ""
    from datetime import date
    text = path.read_text(encoding="utf-8").strip()
    dne = date.fromtimestamp(path.stat().st_mtime)
    return f"{text}\n\n*Souhrn aktualizován: {datum_cz(dne)}*\n"


def _skupiny(dvojice) -> list[tuple[str, list]]:
    s: dict[str, list] = {}
    for v, z in dvojice:
        s.setdefault(v.podtema or "", []).append((v, z))
    nazvy = sorted((n for n in s if n), key=str.casefold)
    out = [(n, s[n]) for n in nazvy]
    if "" in s:
        out.append(("Ostatní" if nazvy else "Výroky", s[""]))
    return out


def _vyroky_bloky(archiv: Archiv, dvojice, rel: str) -> str:
    videno: set[str] = set()
    casti: list[str] = []
    for nazev, skupina in _skupiny(dvojice):
        casti.append(f"## {nazev}\n")
        for v, z in skupina:
            m = archiv.mluvci_vyroku(v, z)
            if m not in videno:
                videno.add(m)
                casti.append(f'<span id="mluvci-{m}"></span>\n')
            casti.append(render_vyrok(v, z, archiv, rel))
            casti.append("---\n")
    return "\n".join(casti)


def _tabulka_mluvcich(archiv: Archiv, dvojice, rel_filtr: bool) -> str:
    pocty = Counter(archiv.mluvci_vyroku(v, z) for v, z in dvojice)
    radky = ["## Kdo k tématu mluví\n", "| Mluvčí | Počet výroků |", "|---|---|"]
    for m, n in sorted(pocty.items(), key=lambda kv: (-kv[1], jmeno_osoby(archiv, kv[0]))):
        pocet = f"[{n}](#mluvci-{m})" if rel_filtr else str(n)
        radky.append(f"| {jmeno_osoby(archiv, m)} | {pocet} |")
    return "\n".join(radky) + "\n"


def render_tema(archiv: Archiv, tema: Tema, souhrn_text: str) -> dict[str, str]:
    """Vrací {relativní cesta: obsah} pro téma (hlavní stránka + případné roční podstránky)."""
    dvojice = archiv.podle_tematu(tema.slug)
    hlava = [f"# {tema.nazev}\n"]
    if tema.popis:
        hlava.append(tema.popis.strip() + "\n")
    if souhrn_text:
        hlava.append(souhrn_text)
    if not dvojice:
        hlava.append("*K tématu zatím nejsou zaznamenány žádné výroky.*\n")
        return {f"temata/{tema.slug}.md": "\n".join(hlava)}

    if len(dvojice) <= PRAH_ROZDELENI:
        hlava.append(_tabulka_mluvcich(archiv, dvojice, True))
        hlava.append(_vyroky_bloky(archiv, dvojice, "../"))
        return {f"temata/{tema.slug}.md": "\n".join(hlava)}

    hlava.append(_tabulka_mluvcich(archiv, dvojice, False))
    roky: dict[int, list] = {}
    for v, z in dvojice:
        roky.setdefault(z.datum.year, []).append((v, z))
    radky = ["## Výroky podle let\n"]
    out: dict[str, str] = {}
    for rok in sorted(roky, reverse=True):
        radky.append(f"- [{rok}]({tema.slug}/{rok}.md) ({len(roky[rok])} výroků)")
        out[f"temata/{tema.slug}/{rok}.md"] = (
            f"# {tema.nazev} — {rok}\n\n[← {tema.nazev}](../{tema.slug}.md)\n\n"
            + _vyroky_bloky(archiv, roky[rok], "../../"))
    hlava.append("\n".join(radky) + "\n")
    out[f"temata/{tema.slug}.md"] = "\n".join(hlava)
    return out
