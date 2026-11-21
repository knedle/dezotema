"""Souhrny: úvod staré tematické / osobní stránky -> data/souhrny/{temata,osoby}/<slug>.md.

Text je doslovný (Markdown zachován), jen se vynechají řádky `---`. Bez front matteru,
tj. bez data aktualizace (R8: datum jen z YAML, nikdy nevymýšlet).
"""
from __future__ import annotations

import re
from pathlib import Path


def uvod_stranky(md: str) -> str:
    """Text mezi `# H1` a první `##`/`###`, bez řádků `---`."""
    md = md.lstrip("﻿")
    m = re.search(r"(?m)^# .*$", md)
    zbytek = md[m.end():] if m else md
    out = []
    for r in zbytek.splitlines():
        if re.match(r"^#{2,3} ", r):
            break
        if r.strip() == "---":
            continue
        out.append(r.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def uvod_osoby(md: str, popis: str = "") -> str:
    """Úvod osobní stránky bez úvodního odstavce, který už je v `osoby.yaml` jako `popis`
    (generátor ho vypisuje zvlášť, jinak by byl dvakrát)."""
    u = uvod_stranky(md)
    if popis and u.startswith(popis.strip()):
        u = u[len(popis.strip()):].strip()
    return u


def _zapis(p: Path, text: str) -> None:
    from tools.migrace.run import _s_opakovanim
    p.parent.mkdir(parents=True, exist_ok=True)
    _s_opakovanim(lambda: p.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n"))


def zapis_souhrny(stara_wiki: Path, root: Path, temata: dict, osoby: dict) -> dict:
    """Zapíše souhrny; vrací {'temata': n, 'osoby': n, 'prazdne': [...], 'chybi': [...]}."""
    sou = Path(root) / "data" / "souhrny"
    res = {"temata": 0, "osoby": 0, "prazdne": [], "chybi": []}
    for slug in sorted(temata):
        p = Path(stara_wiki) / f"{slug}.md"
        if not p.is_file():
            res["chybi"].append(f"{slug}.md")
            continue
        u = uvod_stranky(p.read_text(encoding="utf-8"))
        if not u:
            res["prazdne"].append(f"{slug}.md")
            continue
        _zapis(sou / "temata" / f"{slug}.md", u)
        res["temata"] += 1
    for slug in sorted(osoby):
        o = osoby[slug]
        if not o.vlastni_stranka:
            continue
        p = Path(stara_wiki) / "osoby" / f"{slug}.md"
        if not p.is_file():
            res["chybi"].append(f"osoby/{slug}.md")
            continue
        u = uvod_osoby(p.read_text(encoding="utf-8-sig"), o.popis)
        if not u:
            res["prazdne"].append(f"osoby/{slug}.md")
            continue
        _zapis(sou / "osoby" / f"{slug}.md", u)
        res["osoby"] += 1
    return res
