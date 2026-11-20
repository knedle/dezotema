"""Číselníky témat a osob ze staré wiki (mkdocs.yml nav, index.md, osoby/*.md)."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from tools.archiv.model import Osoba, Tema

# Ručně doplněné aliasy (přepisy zkomolí jména; kanály = osoby)
ALIASY: dict[str, list[str]] = {
    "rajchl": ["Reichl", "Rejchl", "Jindra Rajchl"],
    "zitko": ["Československo TV2", "ČsTV2", "Jiří Hradil"],
    "boldy": ["Konspirátor Boldy", "KonspyChannel"],
    "si-tin-pching": ["Siti Ping", "Xi Jinping", "Si"],
    "cernohorsky": ["Jiří Černohorský"],
    "sejna": ["Restart Česko", "Restart Cesko"],
    "vrabel": ["Vrabel"],
}

# Hosté a zmiňované osoby bez vlastní stránky: slug -> (jméno, popis)
BEZ_STRANKY: dict[str, tuple[str, str]] = {
    "turanek": ("Jaroslav Turánek", "Profesor, přednášející na sněmovním semináři o VTE/FVE."),
    "zlinsky": ("Vladimír Zlínský", "Lékař, přednášející na sněmovním semináři o VTE/FVE."),
    "cimprichova": ("Pynelopi Cimprichová", "Přednášející na sněmovním semináři o VTE/FVE."),
    "svoboda": ("Jakub Svoboda", "Občanský aktivista (Ralsko), přednášející na semináři o VTE/FVE."),
    "hamplova": ("Jana Zwyrtek Hamplová", "Senátorka, advokátka (veřejné a ústavní právo)."),
    "ondrusova": ("Katarína Ondrušová", "Slovenská aktivistka, přednášející na semináři o VTE/FVE."),
    "si-tin-pching": ("Si Ťin-pching", "Čínský prezident (zmiňovaná osoba)."),
}

# Podtémata: slug -> nadřazené téma
NADRAZENE = {
    "konspirace-ceskoslovensko": "konspirace",
    "konspirace-deep-state-qanon": "konspirace",
}

# Stránky v nav „Témata“, které nejsou tematické (typy záznamů)
NETEMATA = {"predikce", "stochasticky-teror"}

# Nesledované osoby se stránkou
NESLEDOVANI = {"pekova"}


class _Loader(yaml.SafeLoader):
    pass


_Loader.add_multi_constructor("", lambda loader, suffix, node: None)


def _popisy(index_md: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"^\|\s*\[[^\]]*\]\(([^)]+?)\.md\)\s*\|\s*(.*?)\s*\|\s*$", index_md, re.M):
        out[m.group(1)] = m.group(2)
    return out


def temata_z_wiki(mkdocs_yml: str, index_md: str) -> list[Tema]:
    nav = yaml.load(mkdocs_yml, Loader=_Loader)["nav"]
    sekce = next(v for it in nav if isinstance(it, dict) for k, v in it.items() if k == "Témata")
    popisy = _popisy(index_md)
    out = []
    for it in sekce:
        for nazev, cesta in it.items():
            slug = cesta.removesuffix(".md")
            if "/" in slug or slug in NETEMATA:
                continue
            out.append(Tema(slug, nazev, popisy.get(slug, ""), NADRAZENE.get(slug)))
    return out


def osoby_z_wiki(wiki: Path) -> list[Osoba]:
    wiki = Path(wiki)
    out = []
    for p in sorted((wiki / "osoby").glob("*.md")):
        text = p.read_text(encoding="utf-8-sig")
        h1 = re.search(r"^# (.+)$", text, re.M)
        po_h1 = text[h1.end():] if h1 else text
        popis = next((b.strip() for b in re.split(r"\n\s*\n", po_h1)
                      if b.strip() and not b.strip().startswith(("---", "#", ">"))), "")
        slug = p.stem
        out.append(Osoba(slug, h1.group(1).strip() if h1 else slug, list(ALIASY.get(slug, [])),
                         popis, slug not in NESLEDOVANI, True))
    for slug, (jmeno, popis) in BEZ_STRANKY.items():
        out.append(Osoba(slug, jmeno, list(ALIASY.get(slug, [])), popis, False, False))
    return out
