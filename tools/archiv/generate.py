from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
from datetime import date
from pathlib import Path

from .index import Archiv
from .io import nacti_vse
from .render.osoba import render_osoba, render_zminene
from .render.predikce import render_predikce
from .render.teror import render_teror
from .render.tema import render_tema, souhrn
from .render.vrabel import mesice_vrabel, render_vrabel
from .render.zdroje import mesice, render_zdroje

GENEROVANE_ADRESARE = ("temata", "osoby", "zminene", "predikce", "zdroje", "zpravodajstvi-vrabel")
GENEROVANE_SOUBORY = ("stochasticky-teror.md", "data/vyroky.json")


def _vycisti(out: Path) -> None:
    for a in GENEROVANE_ADRESARE:
        shutil.rmtree(out / a, ignore_errors=True)
    for s in GENEROVANE_SOUBORY:
        (out / s).unlink(missing_ok=True)


def _json(archiv: Archiv) -> str:
    def prevod(o):
        return o.isoformat() if isinstance(o, date) else str(o)

    data = []
    for vid in sorted(archiv.vyroky):
        v, z = archiv.vyroky[vid]
        data.append({
            "id": v.id, "typ": v.typ, "temata": v.temata,
            "mluvci": archiv.mluvci_vyroku(v, z), "datum": z.datum.isoformat(),
            "zdroj": z.id, "url": z.url, "prepis": z.prepis, "nadpis": v.nadpis,
            "text": v.text,
            "citace": [dataclasses.asdict(c) for c in v.citace],
            "osoby": [dataclasses.asdict(o) for o in v.osoby],
            "vazby": [dataclasses.asdict(x) for x in v.vazby],
            "predikce": dataclasses.asdict(v.predikce) if v.predikce else None,
            "teror": dataclasses.asdict(v.teror) if v.teror else None,
        })
    return json.dumps(data, ensure_ascii=False, indent=1, default=prevod) + "\n"


def _nav(archiv: Archiv) -> list:
    deti: dict[str | None, list] = {}
    for t in archiv.temata.values():
        rodic = t.nadrazene if t.nadrazene in archiv.temata else None
        deti.setdefault(rodic, []).append(t)

    def polozky(rodic):
        out = []
        for t in sorted(deti.get(rodic, []), key=lambda t: t.nazev.casefold()):
            cesta = f"temata/{t.slug}.md"
            if t.slug in deti:
                out.append({t.nazev: [{t.nazev: cesta}, *polozky(t.slug)]})
            else:
                out.append({t.nazev: cesta})
        return out

    osoby = sorted((o for o in archiv.osoby.values() if o.vlastni_stranka),
                   key=lambda o: o.jmeno.casefold())
    return [
        {"Úvod": "index.md"},
        {"Témata": polozky(None)},
        {"Osoby": [{o.jmeno: f"osoby/{o.slug}.md"} for o in osoby]},
        {"Predikce": "predikce/index.md"},
        {"Stochastický teror": "stochasticky-teror.md"},
        {"Zpravodajství Vrabel": [{m: f"zpravodajstvi-vrabel/{m}.md"} for m in mesice_vrabel(archiv)]},
        {"Zdroje": [{"Přehled": "zdroje/index.md"},
                    *[{m: f"zdroje/{m}.md"} for m in mesice(archiv.zdroje)]]},
        {"Extra": [{"Příliš drahý vítr": "extra/prilis-drahy-vitr.md"}]},
        {"O stránce": "o-strance.md"},
    ]


def generate(root: Path, out: Path, dnes: date | None = None) -> dict:
    root, out = Path(root), Path(out)
    dnes = dnes or date.today()
    zdroje, temata, osoby = nacti_vse(root)
    archiv = Archiv(zdroje, temata, osoby)
    sou = root / "data" / "souhrny"

    stranky: dict[str, str] = {}
    for t in sorted(temata.values(), key=lambda t: t.slug):
        stranky.update(render_tema(archiv, t, souhrn(sou / "temata" / f"{t.slug}.md")))
    for o in sorted(osoby.values(), key=lambda o: o.slug):
        if o.vlastni_stranka:
            stranky[f"osoby/{o.slug}.md"] = render_osoba(archiv, o, souhrn(sou / "osoby" / f"{o.slug}.md"))
        if archiv.zminky_osoby(o.slug):
            stranky[f"zminene/{o.slug}.md"] = render_zminene(archiv, o)
    stranky.update(render_predikce(archiv, dnes))
    pozn = sou / "stochasticky-teror.md"
    stranky["stochasticky-teror.md"] = render_teror(
        archiv, pozn.read_text(encoding="utf-8") if pozn.is_file() else "")
    stranky.update(render_zdroje(archiv, out))
    stranky.update(render_vrabel(archiv))
    stranky["data/vyroky.json"] = _json(archiv)

    _vycisti(out)
    soubory = []
    for rel in sorted(stranky):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(stranky[rel], encoding="utf-8", newline="\n")
        soubory.append(p)
    return {"soubory": soubory, "nav": _nav(archiv)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Vygeneruje wiki stránky z datového archivu")
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    res = generate(a.root, a.out)
    print(f"Zapsáno souborů: {len(res['soubory'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
