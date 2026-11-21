"""Srovnávací report staré wiki a datového archivu -> data/migrace/report.md.

Report je deterministický (žádné časové značky, vše řazeno).
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from tools.archiv.index import Archiv
from tools.migrace import predikce as P
from tools.migrace import prehled as H
from tools.migrace import teror as T
from tools.migrace.osoby import parsuj_tabulku
from tools.migrace.temata import parsuj_stranku
from tools.migrace.zdroje import parsuj_zdroje

_ODKAZ = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_STAVY = ("ceka", "potvrzeno", "vyvraceno", "castecne")


def _cti(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")


def _radek(popis: str, stare, nove) -> str:
    return f"- {popis}: {stare} / {nove}"


def _nezarazeno_pocty(nezarazeno: dict | None) -> dict[str, int]:
    return {k: len(v or []) for k, v in (nezarazeno or {}).items()}


def _osiracele_odkazy(wiki_old: Path, archiv: Archiv, stare_kotvy: dict, kotvy_zdroju: dict
                      ) -> tuple[int, list[str]]:
    """Vnitřní odkazy staré wiki, jejichž cíl nelze přeložit na nový výrok / zdroj / stránku."""
    temata = set(archiv.temata)
    osoby = {o.slug for o in archiv.osoby.values() if o.vlastni_stranka}
    mesice = {f"{z.datum:%Y-%m}" for z in archiv.zdroje if z.prehled}
    stranky_ok = ({f"{t}.md" for t in temata} | {f"osoby/{s}.md" for s in osoby}
                  | {"index.md", "predikce.md", "stochasticky-teror.md", "o-strance.md",
                     "_zdroje.md"}
                  | {f"zpravodajstvi-vrabel/{m}.md" for m in mesice})
    prepisy = {Path(z.prepis).name for z in archiv.zdroje}
    kotvy_stranek = set(stare_kotvy.get("stranky", {})) | set(stare_kotvy.get("kapitoly", {}))
    holé = set(stare_kotvy.get("kotvy", {}))
    celkem, osirele = 0, []
    for p in sorted(wiki_old.rglob("*.md")):
        rel_zdroj = p.relative_to(wiki_old).as_posix()
        if rel_zdroj.startswith(("prepisy/", "extra/", "css/", "js/")):
            continue
        for url in _ODKAZ.findall(_cti(p)):
            if re.match(r"^[a-z]+:", url) or url.startswith("<"):
                continue
            cesta, _, kotva = url.partition("#")
            kotva = unquote(kotva)
            if cesta:
                cil = (p.parent / unquote(cesta)).resolve()
                try:
                    cil_rel = cil.relative_to(wiki_old.resolve()).as_posix()
                except ValueError:
                    cil_rel = unquote(cesta)
            else:
                cil_rel = rel_zdroj
            celkem += 1
            if cil_rel.endswith(".txt"):
                ok = Path(cil_rel).name in prepisy
            elif cil_rel not in stranky_ok:
                ok = cil_rel.startswith(("extra/", "css/", "js/"))
            elif not kotva:
                ok = True
            elif cil_rel == "_zdroje.md":
                ok = kotva in kotvy_zdroju
            elif cil_rel.endswith(".md") and cil_rel[:-3] in temata:
                ok = f"{cil_rel}#{kotva}" in kotvy_stranek or kotva in holé
            else:
                ok = False      # kotva uvnitř osoby/predikce/teroru/přehledu: viz report
            if not ok:
                osirele.append(f"{rel_zdroj} -> {url}")
    return celkem, sorted(set(osirele))


def srovnani(wiki_old: Path, archiv: Archiv, nezarazeno: dict | None = None,
             migrace_dir: Path | None = None, ciselnik: dict | None = None) -> str:
    """Markdown report: stará wiki (vlevo) / nový archiv (vpravo)."""
    wiki_old = Path(wiki_old)
    migrace_dir = Path(migrace_dir) if migrace_dir else None
    L: list[str] = ["# Report migrace: stará wiki / datový archiv", "",
                    "Formát řádků: `stará wiki / nový archiv`.", ""]

    # --- zdroje
    zd = wiki_old / "_zdroje.md"
    stare_zdroje = len(parsuj_zdroje(_cti(zd))) if zd.is_file() else 0
    L += ["## Zdroje", "", _radek("Zdroje", stare_zdroje, len(archiv.zdroje))]
    bez = sorted(z.id for z in archiv.zdroje if not z.vyroky)
    bez_prehledu = sorted(z.id for z in archiv.zdroje if not z.vyroky and not z.prehled)
    L += [f"- Zdroje bez výroků: {len(bez)} (z toho {len(bez_prehledu)} ani bez přehledu dne)", ""]

    # --- výroky
    osoby_c = ciselnik if ciselnik is not None else archiv.osoby
    jednotky = Counter()
    for slug in sorted(archiv.temata):
        p = wiki_old / f"{slug}.md"
        if p.is_file():
            jednotky[slug] = len(parsuj_stranku(_cti(p), slug, osoby_c))
    nove_t = Counter(t for v, _ in archiv.vyroky.values() if v.typ == "tvrzeni" for t in set(v.temata))
    nove_tv = sum(1 for v, _ in archiv.vyroky.values() if v.typ == "tvrzeni")
    L += ["## Výroky", "",
          "Staré = `###` sekce + datované odstavce (jednotky parseru); nové = výroky typu `tvrzeni` "
          "(výrok s více tématy se počítá v každém z nich, slučování duplicit a nepřiřazené "
          "jednotky snižují počet).", "",
          _radek("Výroky celkem (tvrzení)", sum(jednotky.values()), nove_tv),
          f"- Výroky všech typů v archivu: {len(archiv.vyroky)}", "",
          "| Téma | Staré | Nové | Rozdíl |", "|---|---:|---:|---:|"]
    for slug in sorted(archiv.temata):
        s, n = jednotky.get(slug, 0), nove_t.get(slug, 0)
        L.append(f"| {slug} | {s} | {n} | {n - s:+d} |")
    L.append("")

    # --- predikce
    pm = wiki_old / "predikce.md"
    raw_p = P.parsuj(_cti(pm)) if pm.is_file() else []
    nove_p = [v for v, _ in archiv.predikce()]
    st_s = Counter(r.stav for r in raw_p)
    st_n = Counter((v.predikce.stav if v.predikce else "ceka") for v in nove_p)
    L += ["## Predikce", "", _radek("Predikce", len(raw_p), len(nove_p))]
    for s in sorted(set(_STAVY) | set(st_s) | set(st_n)):
        L.append(_radek(f"Predikce — stav {s}", st_s.get(s, 0), st_n.get(s, 0)))
    L.append("")

    # --- teror
    tm = wiki_old / "stochasticky-teror.md"
    raw_t = T.parsuj(_cti(tm)) if tm.is_file() else []
    L += ["## Stochastický teror", "", _radek("Řádky teroru", len(raw_t), len(archiv.teror())), ""]

    # --- přehled dní (Vrabel)
    pd = wiki_old / "zpravodajstvi-vrabel"
    dny = 0
    if pd.is_dir():
        for p in sorted(pd.glob("*.md")):
            dny += len(H.parsuj_dny(_cti(p)))
    nove_dny = sum(1 for z in archiv.zdroje if z.prehled)
    L += ["## Přehled zpravodajství", "", _radek("Dny přehledu", dny, nove_dny),
          _radek("Položky přehledu", "—", sum(len(z.prehled) for z in archiv.zdroje)), ""]

    # --- zmínky osob
    stare_z = 0
    od = wiki_old / "osoby"
    if od.is_dir():
        for p in sorted(od.glob("*.md")):
            stare_z += len(parsuj_tabulku(_cti(p), p.stem))
    nove_z = sum(len(z.osoby) + sum(len(v.osoby) for v in z.vyroky) for z in archiv.zdroje)
    L += ["## Zmíněné osoby", "", _radek("Zmínky osob (řádky tabulek / OsobaRef)", stare_z, nove_z), ""]

    # --- nezařazeno
    poc = _nezarazeno_pocty(nezarazeno)
    L += ["## Nezařazeno", "", f"- Nezařazeno: {sum(poc.values())}"]
    for k in sorted(poc):
        L.append(f"  - {k}: {poc[k]}")
    L.append("")

    # --- zdroje bez výroků
    L += [f"## Zdroje bez výroků ({len(bez)})", ""]
    L += [f"- `{i}`" for i in bez] or ["- (žádné)"]
    L.append("")

    # --- cizí dalsi_zdroje, osiřelé odkazy
    cizi = []
    stare_kotvy, kotvy_zdroju = {}, {}
    if migrace_dir:
        pc = migrace_dir / "dalsi-zdroje-cizi.json"
        if pc.is_file():
            cizi = json.loads(pc.read_text(encoding="utf-8"))
        pk = migrace_dir / "stare-kotvy.json"
        if pk.is_file():
            stare_kotvy = json.loads(pk.read_text(encoding="utf-8"))
        pz = migrace_dir / "kotvy-zdroju.json"
        if pz.is_file():
            kotvy_zdroju = json.loads(pz.read_text(encoding="utf-8"))
    L += [f"## dalsi_zdroje s jiným mluvčím ({len(cizi)}) — k ruční kontrole",
          "", "Úplný seznam s výňatky: `data/migrace/dalsi-zdroje-cizi.json`.", ""]
    for c in cizi:
        L.append(f"- `{c['vyrok']}` (zdroj `{c['zdroj']}`) <- `{c['cizi_zdroj']}` "
                 f"({c['cizi_mluvci']}); stará kotva `{c.get('stara_kotva')}`")
    L.append("")
    celkem, osirele = _osiracele_odkazy(wiki_old, archiv, stare_kotvy, kotvy_zdroju) \
        if migrace_dir else (0, [])
    po = (migrace_dir / "odkazy.json") if migrace_dir else None
    if po and po.is_file():
        od = json.loads(po.read_text(encoding="utf-8"))
        L += [f"## Odkazy přepsané v datech ({od['prelozeno']} z {od['celkem']})", "",
              f"Neznámé odkazy zůstaly v textech beze změny ({len(od['nepreložené'])}):", ""]
        L += [f"- `{o}`" for o in od["nepreložené"]] or ["- (žádné)"]
        L.append("")
    L += [f"## Osiřelé vnitřní odkazy ({len(osirele)} z {celkem} vnitřních odkazů)", "",
          "Odkazy ve staré wiki, jejichž cíl nelze přeložit na nový výrok, zdroj ani stránku "
          "(kotvy uvnitř `osoby/*`, `predikce.md`, `stochasticky-teror.md` a přehledu se "
          "nepřekládají).", ""]
    L += [f"- `{o}`" for o in osirele] or ["- (žádné)"]
    L.append("")
    return "\n".join(L)
