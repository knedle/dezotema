"""Krok `odkazy`: přepíše vnitřní odkazy ve starém tvaru (`tema.md#stara-kotva`, `_zdroje.md#x`,
`predikce.md#x`, `../x.md`) na kořenové odkazy do nové struktury (`/temata/x.md#id`).

Odkazy se v datech ukládají kořenově (kořen = wiki, vždy s úvodním `/`), tedy nezávisle na stránce,
na které se text vykreslí (téma, osoba, zdroj, predikce). Generátor je při zápisu stránky převede na
relativní (`render.common.zrelativni`). Neznámé odkazy zůstanou beze změny a jdou do reportu.
"""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote

from tools.archiv.index import Archiv

ODKAZ = re.compile(r"(?<!!)(\[[^\]]*\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")
_PREJMENOVANE = {"zmíněné-osoby": "zmínění-lidé"}   # přejmenovaný nadpis na stránce osoby
_STATICKE = {"index.md", "o-strance.md", "stochasticky-teror.md"}


class Prekladac:
    def __init__(self, archiv: Archiv, stare: dict, kotvy_zdroju: dict, prepisy_navic=()):
        self.a = archiv
        self.stranky = stare.get("stranky", {})
        self.kapitoly = stare.get("kapitoly", {})
        self.hole = stare.get("kotvy", {})
        self.kotvy_zdroju = kotvy_zdroju
        self.zdroje = {z.id: z for z in archiv.zdroje}
        self.prepisy = {Path(z.prepis).name for z in archiv.zdroje} | set(prepisy_navic)
        self.nepreložené: list[str] = []
        self.zaznamy: list[tuple[str, str, str | None]] = []   # (kde, původní, nový/None)
        self.celkem = 0
        self.prelozeno = 0

    def _vid(self, klic: str):
        return self.stranky.get(klic) or self.kapitoly.get(klic)

    def _cil_vyroku(self, vid: str, tema: str | None) -> str | None:
        cil = self.a.vyroky.get(vid)
        if not cil:
            return None
        v, z = cil
        s = self.a.stranka_vyroku(vid, tema) or self.a.stranka_vyroku(vid)
        if not s:
            s = (f"predikce/{z.datum:%Y-%m}.md" if v.predikce or v.typ == "predikce"
                 else f"zdroje/{z.datum:%Y-%m}.md")
        return f"/{s}#{vid}"

    def _vid_libovolne(self, kotva: str):
        """Výrok, na který míří kotva na kterékoli staré stránce (musí být jednoznačný)."""
        cile = {v for sl in (self.stranky, self.kapitoly) for k, v in sl.items()
                if k.partition("#")[2] == kotva}
        return next(iter(cile)) if len(cile) == 1 else None

    def nadpisy_osoby(self) -> set[str]:
        """Kotvy nadpisů na vygenerované stránce osoby (pevné + názvy témat)."""
        from tools.archiv.slug import slugify
        return set(_NADPISY["osoby"]) | {slugify(t.nazev) for t in self.a.temata.values()}

    def _zdroj_kotva(self, kotvy) -> str | None:
        for k in kotvy:
            z = self.zdroje.get(self.kotvy_zdroju.get(k, ""))
            if z:
                return f"/zdroje/{z.datum:%Y-%m}.md#{z.id}"
        return None

    def cil(self, url: str, zakladna: str, tema: str | None,
            zdroje_prvne: bool = False) -> str | None:
        """Nový kořenový odkaz, nebo None (neznámý). Holá `#kotva` je kotva tématu (a výroků),
        nebo — v textech, které ve staré wiki žily na `_zdroje.md` (`zdroje_prvne`) — kotva zdroje;
        druhá možnost je vždy záložní."""
        cesta, _, kotva = url.partition("#")
        kotvy = [kotva, unquote(kotva)] if kotva else []
        if not cesta and kotvy:
            zk = self._zdroj_kotva(kotvy)
            if zdroje_prvne and zk:
                return zk
            for k in kotvy:
                vid = self._vid(f"{tema}.md#{k}") if tema else None
                vid = vid or self.hole.get(k) or self._vid_libovolne(k)
                if vid:
                    return self._cil_vyroku(vid, tema)
            return zk
        if cesta:
            norm = posixpath.normpath(posixpath.join(zakladna, unquote(cesta)))
            while norm.startswith("../"):
                norm = norm[3:]
        else:
            norm = f"{tema}.md" if tema else ""
        if not norm:                                    # holá kotva bez kontextu
            for k in kotvy:
                if k in self.hole:
                    return self._cil_vyroku(self.hole[k], None)
            return None
        if norm.endswith(".txt"):
            nm = Path(norm).name
            return f"/prepisy/done/{nm}" if nm in self.prepisy else None
        if norm.startswith(("extra/", "css/", "js/")) or norm in _STATICKE:
            return f"/{norm}" + (f"#{kotva}" if kotva else "")
        if norm == "_zdroje.md":
            if not kotva:
                return "/zdroje/index.md"
            for k in kotvy:
                zid = self.kotvy_zdroju.get(k)
                z = self.zdroje.get(zid) if zid else None
                if z:
                    return f"/zdroje/{z.datum:%Y-%m}.md#{z.id}"
            return None
        if norm == "predikce.md":
            if not kotva:
                return "/predikce/index.md"
            for k in kotvy:
                vid = self._vid(f"predikce.md#{k}")
                if vid:
                    return self._cil_vyroku(vid, None)
            return None
        if norm.startswith("zpravodajstvi-vrabel/") and norm.endswith(".md"):
            m = Path(norm).stem
            ok = any(f"{z.datum:%Y-%m}" == m for z in self.a.zdroje if z.prehled)
            return f"/{norm}" if ok and not kotva else None
        if norm.startswith("osoby/") and norm.endswith(".md"):
            o = self.a.osoby.get(Path(norm).stem)
            if not (o and o.vlastni_stranka):
                return None
            if not kotva:
                return f"/{norm}"
            k = unquote(kotva)
            k = _PREJMENOVANE.get(k) or (k if k in self.nadpisy_osoby() else None)
            return f"/{norm}#{k}" if k else None
        if norm.endswith(".md") and norm[:-3] in self.a.temata:
            slug = norm[:-3]
            if not kotva:
                return f"/temata/{slug}.md"
            for k in kotvy:
                vid = self._vid(f"{norm}#{k}") or self.hole.get(k)
                if vid:
                    return self._cil_vyroku(vid, slug)
            return None
        return None

    def text(self, text: str, kde: str, zakladna: str = "", tema: str | None = None,
             zdroje_prvne: bool = False) -> str:
        def nahrad(m):
            url = m.group(2)
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url) or url.startswith("/"):
                return m.group(0)
            self.celkem += 1
            novy = self.cil(url, zakladna, tema, zdroje_prvne)
            self.zaznamy.append((kde, url, novy))
            if novy is None:
                self.nepreložené.append(f"{kde} -> {url}")
                # neznámá kotva: cesta se opraví na správnou stránku, kotva zůstane (jen INFO v MkDocs)
                cesta, hash_, kotva = url.partition("#")
                strana = self.cil(cesta, zakladna, tema) if cesta and hash_ else None
                return m.group(1) + strana + "#" + kotva + m.group(3) if strana else m.group(0)
            self.prelozeno += 1
            return m.group(1) + novy + m.group(3)

        return ODKAZ.sub(nahrad, text)


_NADPISY = {"osoby": {"zdroje", "podle-témat", "predikce", "stochastický-teror", "zmínění-lidé"},
            "stochasticky-teror.md": {"přehled-výroků", "hraniční-případy", "poznámky"}}


def _existuje(a: Archiv, novy: str, _cache: dict = {}) -> bool:
    """Existuje v generovaném webu stránka i kotva `novy` (kořenový odkaz)? Kotvy výroků a zdrojů
    se ověřují přesně, stránky mimo data (extra, index) jen podle stránky."""
    klic = id(a)
    if _cache.get("a") != klic:
        kot: set[tuple[str, str]] = set()
        for vid, (v, z) in a.vyroky.items():
            for t in v.temata:
                s = a.stranka_vyroku(vid, t)
                if s:
                    kot.add((s, vid))
            if v.predikce or v.typ == "predikce":
                kot.add((f"predikce/{z.datum:%Y-%m}.md", vid))
        for z in a.zdroje:
            kot.add((f"zdroje/{z.datum:%Y-%m}.md", z.id))
        _cache.update(a=klic, kot=kot)
    cesta, _, kotva = novy.lstrip("/").partition("#")
    if not kotva:
        return True
    if (cesta, kotva) in _cache["kot"]:
        return True
    if cesta.startswith("osoby/"):
        from tools.archiv.slug import slugify
        return unquote(kotva) in (_NADPISY["osoby"] | {slugify(x.nazev) for x in a.temata.values()})
    if cesta in _NADPISY:
        return unquote(kotva) in _NADPISY[cesta]
    return cesta.startswith(("extra/", "index", "o-strance"))


def _kotvy_stare_wiki(stara: Path) -> set[str]:
    """Všechny kotvy staré wiki: explicitní `{#x}` i slugifikované nadpisy."""
    from tools.archiv.slug import slugify
    out: set[str] = set()
    for f in Path(stara).rglob("*.md"):
        for r in f.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"^#{1,6}\s+(.*?)\s*(\{#([^}]+)\})?\s*$", r)
            if m:
                out.add(m.group(3) or slugify(m.group(1)))
    return out


def vyhodnot(p: Prekladac, stara_wiki: Path | None) -> dict:
    """Klasifikace odkazů: přeložené s existujícím cílem / přeložené s chybějícím cílem /
    nepřeložené mrtvé už ve staré wiki / nepřeložené, které ve staré wiki fungovaly (nově mrtvé)."""
    stare = _kotvy_stare_wiki(stara_wiki) if stara_wiki and Path(stara_wiki).is_dir() else None
    ok = chybi_cil = 0
    mrtve_stare, mrtve_nove, jen_kotva = [], [], []
    for kde, url, novy in p.zaznamy:
        if novy is not None:
            if _existuje(p.a, novy):
                ok += 1
            else:
                chybi_cil += 1
                jen_kotva.append(f"{kde} -> {url} => {novy}")
            continue
        kotva = unquote(url.partition("#")[2])
        radek = f"{kde} -> {url}"
        if stare is not None and kotva and kotva in stare:
            mrtve_nove.append(radek)       # kotva ve staré wiki existovala -> odkaz mohl fungovat
        else:
            mrtve_stare.append(radek)
    return {"cil_existuje": ok, "cil_chybi": sorted(set(jen_kotva)),
            "mrtve_ve_stare_wiki": sorted(set(mrtve_stare)),
            "nove_mrtve": sorted(set(mrtve_nove))}


def _fyzicke_prepisy(root: Path) -> set[str]:
    """Přepisy ve wiki/prepisy/done i bez záznamu ve zdrojích (odkaz na ně je platný)."""
    d = Path(root) / "wiki" / "prepisy" / "done"
    return {f.name for f in d.glob("*.txt")} if d.is_dir() else set()


def _zdroj(p: Prekladac, z) -> None:
    kde = z.id
    if z.poznamka:
        z.poznamka = p.text(z.poznamka, kde, zdroje_prvne=True)
    for r in z.osoby:
        r.kontext = p.text(r.kontext, kde, zdroje_prvne=True)
    for it in z.prehled:
        it.text = p.text(it.text, f"{kde} (přehled)")
    for v in z.vyroky:
        k = f"{kde}#{v.id}"
        v.text = p.text(v.text, k)
        for c in v.citace:
            c.text = p.text(c.text, k)
        for r in v.osoby:
            r.kontext = p.text(r.kontext, k)
        if v.predikce:
            for h in v.predikce.vyhodnoceni:
                h.text = p.text(h.text, k)


def _souhrn(p: Prekladac, f: Path, kde: str, zakladna: str = "", tema: str | None = None) -> None:
    t = f.read_text(encoding="utf-8")
    n = p.text(t, kde, zakladna, tema)
    if n != t:
        f.write_text(n, encoding="utf-8", newline="\n")


def prepis_odkazy(root: Path, stara_wiki: Path | None = None) -> dict:
    """Přepíše odkazy v data/zdroje/** a data/souhrny/**; zapíše data/migrace/odkazy.json."""
    from tools.archiv.io import nacti_vse, uloz_zdroj
    from tools.migrace.run import _s_opakovanim

    root = Path(root)
    zdroje, temata, osoby = nacti_vse(root)
    md = root / "data" / "migrace"
    p = Prekladac(Archiv(zdroje, temata, osoby),
                  json.loads((md / "stare-kotvy.json").read_text(encoding="utf-8")),
                  json.loads((md / "kotvy-zdroju.json").read_text(encoding="utf-8")),
                  _fyzicke_prepisy(root))
    for z in zdroje:
        _zdroj(p, z)
        _s_opakovanim(lambda z=z: uloz_zdroj(z, root))
    sou = root / "data" / "souhrny"
    for f in sorted((sou / "temata").glob("*.md")):
        _souhrn(p, f, f"souhrn temata/{f.stem}", "", f.stem)
    for f in sorted((sou / "osoby").glob("*.md")):
        _souhrn(p, f, f"souhrn osoby/{f.stem}", "osoby")
    if (sou / "stochasticky-teror.md").is_file():
        _souhrn(p, sou / "stochasticky-teror.md", "souhrn stochasticky-teror")
    out = {"celkem": p.celkem, "prelozeno": p.prelozeno,
           "nepreložené": sorted(set(p.nepreložené)), **vyhodnot(p, stara_wiki)}
    (md / "odkazy.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                    encoding="utf-8", newline="\n")
    return out


def prepis_staticke(root: Path, wiki: Path,
                    soubory=("index.md", "o-strance.md", "extra/prilis-drahy-vitr.md")) -> list[str]:
    """Totéž pro statické stránky mimo data/ (index, o-strance, extra): přepíše je přímo v `wiki`
    (kořenové odkazy hned převede na relativní). Vrací neznámé odkazy. Určeno pro náhled a Task 10."""
    from tools.archiv.io import nacti_vse
    from tools.archiv.render.common import zrelativni

    root, wiki = Path(root), Path(wiki)
    zdroje, temata, osoby = nacti_vse(root)
    md = root / "data" / "migrace"
    p = Prekladac(Archiv(zdroje, temata, osoby),
                  json.loads((md / "stare-kotvy.json").read_text(encoding="utf-8")),
                  json.loads((md / "kotvy-zdroju.json").read_text(encoding="utf-8")),
                  _fyzicke_prepisy(root))
    for s in soubory:
        f = wiki / s
        if f.is_file():
            n = p.text(f.read_text(encoding="utf-8"), s, posixpath.dirname(s))
            f.write_text(zrelativni(n, s), encoding="utf-8", newline="\n")
    return sorted(set(p.nepreložené))
