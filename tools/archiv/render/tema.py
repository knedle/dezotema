from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from ..index import PRAH_ROZDELENI, Archiv
from ..model import Tema
from .common import datum_cz, jmeno_osoby, render_vyrok


def _front_matter(text: str):
    """Oddělí YAML front matter (`aktualizovano: YYYY-MM-DD`); datum je None, pokud chybí."""
    text = text.lstrip("\ufeff")
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not m:
        return text, None
    meta = yaml.safe_load(m.group(1)) or {}
    dne = meta.get("aktualizovano") if isinstance(meta, dict) else None
    if isinstance(dne, str):
        try:
            dne = date.fromisoformat(dne)
        except ValueError:
            dne = None
    return text[m.end():], dne if isinstance(dne, date) else None


def souhrn(path: Path) -> str:
    """Obsah souhrnu; datum aktualizace jen z front matteru, jinak bez datové řádky."""
    if not path.is_file():
        return ""
    text, dne = _front_matter(path.read_text(encoding="utf-8"))
    text = text.strip()
    if dne is None:
        return text + "\n"
    return f"{text}\n\n*Aktualizováno: {datum_cz(dne)}*\n"


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
