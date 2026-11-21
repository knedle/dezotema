"""Převod denních přehledů `zpravodajstvi-vrabel/*.md` na `zdroj.prehled` (Task 7)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import unquote

from tools.archiv.model import PrehledPolozka, Zdroj
from tools.archiv.slug import ascii_slug
from tools.migrace.pomocne import kotvy_z_textu
from tools.migrace.temata import _slova

_DEN = re.compile(r"^## (\d{4})-(\d{2})-(\d{2})(?:\s*\(([^)]*)\))?(?:\s+—\s+(.*))?$")
_POLOZKA = re.compile(r"^- (.*)$")
_TUCNA = re.compile(r"^\*\*(?P<t>.+?)\*\*\s*(?P<r>.*)$")
_LINK = r"\[[^\]]*\]\([^)]*\)"
_VIZ = re.compile(rf"\s*→\s*viz\s+(?P<links>{_LINK}(?:\s*,\s*{_LINK})*)\s*$")
_LINK_RX = re.compile(r"\[(?P<n>[^\]]*)\]\((?P<u>[^)]*)\)")
_ZDROJ = re.compile(r"^\*\*Zdroj:\*\*")
_PLNE = re.compile(r"^\*\*Plně zpracováno do:\*\*")
_STITEK = re.compile(r"^\*\*(?P<l>[^*]+?):\*\*\s*(?P<r>.*)$")
_ODKAZ_ZDROJE = re.compile(r";?\s*\[[^\]]*\]\([^)]*_zdroje\.md#[^)]*\)")

# běžná slova (kmen 4 písmena), která samy o sobě neprokazují shodu
_STOP = {"podl", "kter", "jako", "jeho", "jeji", "take", "kdyz", "bude", "jsou", "bylo", "tedy",
         "nebo", "proto", "pres", "musi", "muze", "jest", "toho", "tohl", "tuto", "tato", "vice",
         "nema", "zase", "nove", "nova", "vrab", "pouz"}


@dataclass
class Den:
    datum: date
    titul: str
    polozky: list[PrehledPolozka] = field(default_factory=list)
    kotvy: list[str] = field(default_factory=list)       # kotvy z řádku „Zdroj:“
    odkazy: list[str] = field(default_factory=list)      # nepřeložené odkazy „viz …“
    # položky patřící jinému zdroji (řádek s odkazem na `_zdroje.md#…`): (kotvy, položka)
    vlastni: list[tuple[list[str], PrehledPolozka]] = field(default_factory=list)
    nerozpoznano: list[str] = field(default_factory=list)  # řádky, které nešlo zařadit


def _tema_a_text(obsah: str) -> tuple[str, str]:
    m = _TUCNA.match(obsah)
    if m:
        return m.group("t").strip().rstrip(":").strip(), m.group("r").strip()
    # starší formát bez tučného názvu: „Téma — popis“ / „Téma: popis“
    for sep in (" — ", ": "):
        if sep in obsah:
            t, r = obsah.split(sep, 1)
            if 0 < len(t) <= 80 and r.strip():
                return t.strip(), r.strip()
    return obsah[:60].rsplit(" ", 1)[0] if len(obsah) > 60 else obsah, obsah


def odkaz_na_vyrok(url: str, stare_kotvy: dict | None) -> str | None:
    """`../valka-nato-rusko.md#kotva` -> id výroku podle stare-kotvy.json."""
    if not stare_kotvy or "#" not in url:
        return None
    strana, kotva = url.split("#", 1)
    strana = strana.removeprefix("../").removeprefix("./")
    kotva = unquote(kotva)
    return (stare_kotvy.get("stranky", {}).get(f"{strana}#{kotva}")
            or stare_kotvy.get("kotvy", {}).get(kotva))


def _slozit(text: str, linky: list[tuple[str, str]]) -> str:
    if not linky:
        return text
    return f"{text} → viz " + ", ".join(f"[{n}]({u})" for n, u in linky)


def _bez_vlajky(text: str) -> str:
    return re.sub(r"^⚡\s*", "", text)


def _stitkovy_radek(r: str, stare_kotvy: dict | None):
    """`**Predikce:** [..](..)`, `**Stochastický teror:** …`, `**Samostatné video (5. 9.):** …`
    -> (kotvy zdroje v řádku, položka); štítek je téma, odkazy zůstávají v textu."""
    sm = _STITEK.match(r.strip())
    if not sm:
        return None
    rest = sm.group("r").strip()
    kotvy = kotvy_z_textu(rest)
    text = _ODKAZ_ZDROJE.sub("", rest).strip(" ;")
    vyrok = next((v for v in (odkaz_na_vyrok(u, stare_kotvy) for _, u in _LINK_RX.findall(text))
                  if v), None)
    tema = sm.group("l").strip()
    return kotvy, PrehledPolozka(tema=tema, text=text or tema, vyrok=vyrok)


def parsuj_dny(md: str, stare_kotvy: dict | None = None) -> list[Den]:
    md = md.lstrip("﻿")
    out: list[Den] = []
    for r in md.splitlines():
        dm = _DEN.match(r)
        if dm:
            titul = (dm.group(5) or "").strip()
            if dm.group(4):                    # „2026-08-26 (dovětek) — …“
                titul = f"{titul} ({dm.group(4).strip()})".strip()
            out.append(Den(date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3))), titul))
            continue
        if not out:
            continue
        den = out[-1]
        if _ZDROJ.match(r):
            den.kotvy = kotvy_z_textu(r)
            continue
        pm = _POLOZKA.match(r)
        if not pm:
            if not r.strip() or r.strip() == "---" or _PLNE.match(r):
                continue                      # „Plně zpracováno do“ je odvoditelné z výroků
            sr = _stitkovy_radek(r, stare_kotvy)
            if sr is None:
                den.nerozpoznano.append(r.strip())
            elif sr[0]:
                den.vlastni.append(sr)
            else:
                den.polozky.append(sr[1])
            continue
        tema, text = _tema_a_text(pm.group(1).strip())
        vyrok = None
        vm = _VIZ.search(text)
        if vm:
            hlavni = text[:vm.start()].strip()
            linky = [(n, u) for n, u in _LINK_RX.findall(vm.group("links"))]
            zbyle = []
            for n, u in linky:
                v = odkaz_na_vyrok(u, stare_kotvy)
                if v and vyrok is None:
                    vyrok = v
                else:
                    zbyle.append((n, u))
            if vyrok:
                # ⚡ je u přeložené vazby zbytečné (odkaz na výrok ho nese)
                text = _slozit(_bez_vlajky(hlavni), zbyle)
            else:
                den.odkazy += [u for _, u in zbyle]
        den.polozky.append(PrehledPolozka(tema=tema, text=text or tema, vyrok=vyrok))
    return out


def _vyznamna(text: str) -> set[str]:
    """Významová slova (kmen 4 písmena, bez diakritiky, bez běžných slov)."""
    return _slova(text) - _STOP


def _plna_slova(text: str) -> set[str]:
    """Celá slova (bez diakritiky) o délce >= 6 písmen."""
    return {w for w in ascii_slug(text).split("-") if len(w) >= 6 and not w.isdigit()}


def _shoda(a: str, b: str) -> int:
    """Počet sdílených kmenů; jediný sdílený kmen stačí jen při shodě celého slova (>= 6 písmen)."""
    n = len(_vyznamna(a) & _vyznamna(b))
    if n == 1 and not (_plna_slova(a) & _plna_slova(b)):
        return 0
    return n


def prirad_stranky(polozky: list[PrehledPolozka], zdroj: Zdroj, temata) -> int:
    """Odkaz „viz [Téma](../tema.md)“ bez kotvy -> výrok téhož zdroje s tímto tématem, ale jen
    při shodě aspoň jednoho významového slova (i u jediného kandidáta); jinak zůstává odkaz
    v textu položky. Vrací počet přiřazených položek."""
    n = 0
    for p in polozky:
        if p.vyrok is not None:
            continue
        vm = _VIZ.search(p.text)
        if not vm:
            continue
        hlavni = p.text[:vm.start()].strip()
        linky = _LINK_RX.findall(vm.group("links"))
        zbyle = []
        for nazev, u in linky:
            strana = u.removeprefix("../").removeprefix("./")
            slug = strana[:-3] if strana.endswith(".md") and "#" not in strana else None
            kand = [v for v in zdroj.vyroky if v.typ in ("tvrzeni", "postoj") and slug in v.temata] \
                if slug in temata and p.vyrok is None else []
            shody = [(_shoda(p.tema + " " + hlavni, v.nadpis + " " + v.text), -i, v)
                     for i, v in enumerate(kand)]
            shody = [s for s in shody if s[0] >= 1]
            if shody:
                p.vyrok = max(shody, key=lambda s: (s[0], s[1]))[2].id
            else:
                zbyle.append((nazev, u))
        if p.vyrok:
            p.text = _slozit(_bez_vlajky(hlavni), zbyle) or p.tema
            n += 1
    return n


def parsuj(md: str, stare_kotvy: dict | None = None) -> dict[date, list[PrehledPolozka]]:
    """Datum -> položky (více přehledů téhož dne se spojí; rozlišení zdrojů dělá `parsuj_dny`)."""
    out: dict[date, list[PrehledPolozka]] = {}
    for den in parsuj_dny(md, stare_kotvy):
        out.setdefault(den.datum, []).extend(den.polozky)
    return out
