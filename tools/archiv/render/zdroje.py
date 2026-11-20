from __future__ import annotations

from pathlib import Path

from ..index import Archiv
from ..model import Zdroj
from .common import datum_cz, jmeno_osoby, odkaz_prepisu, odkaz_vyroku


def _razene(zdroje: list[Zdroj]) -> list[Zdroj]:
    return sorted(zdroje, key=lambda z: (z.datum, z.id), reverse=True)


def mesice(zdroje: list[Zdroj]) -> list[str]:
    return sorted({f"{z.datum:%Y-%m}" for z in zdroje}, reverse=True)


def render_zdroj(archiv: Archiv, z: Zdroj) -> str:
    r = [f"## {jmeno_osoby(archiv, z.mluvci)} — {z.titul} {{#{z.id}}}",
         f"- **Soubor:** [přepis]({odkaz_prepisu('../', z.prepis)})",
         f"- **Kanál:** {z.kanal}",
         f"- **URL:** <{z.url}>",
         f"- **Datum záznamu:** {datum_cz(z.datum)}"]
    if z.delka:
        r.append(f"- **Délka:** {z.delka}")
    if z.poznamka:
        r.append(f"- **Poznámka:** {z.poznamka}")
    if z.rezim == "preskoceno":
        r.append("- **Stav:** přeskočeno")
    if z.vyroky:
        odk = ", ".join(o for o in (odkaz_vyroku(archiv, v.id, "../") for v in z.vyroky) if o)
        r.append(f"- **Výroků:** {len(z.vyroky)}" + (f" — {odk}" if odk else ""))
    return "\n".join(r) + "\n"


def render_zdroje(archiv: Archiv, out: Path) -> dict[str, str]:
    stranky: dict[str, str] = {}
    for m in mesice(archiv.zdroje):
        zm = _razene([z for z in archiv.zdroje if f"{z.datum:%Y-%m}" == m])
        stranky[f"zdroje/{m}.md"] = (f"# Zdroje\n\nZdroje z měsíce {m}.\n\n"
                                      + "\n".join(render_zdroj(archiv, z) for z in zm))
    zname = {Path(z.prepis).name for z in archiv.zdroje}
    done = out / "prepisy" / "done"
    nezpr = sorted(p.name for p in done.glob("*.txt") if p.name not in zname) if done.is_dir() else []
    preskocene = [z for z in _razene(archiv.zdroje) if z.rezim == "preskoceno"]
    idx = ["# Zdroje — přehled\n", "## Podle měsíců\n"]
    idx += [f"- [{m}]({m}.md)" for m in mesice(archiv.zdroje)]
    idx += ["", "## Nezpracované / přeskočené přepisy\n"]
    idx += [f"- [{n}](../prepisy/done/{n})" for n in nezpr]
    idx += [f"- [{z.titul}]({z.datum:%Y-%m}.md#{z.id}) (přeskočeno)" for z in preskocene]
    if not nezpr and not preskocene:
        idx.append("*Žádné.*")
    stranky["zdroje/index.md"] = "\n".join(idx) + "\n"
    return stranky
