"""Lokální náhled nového webu (R6): vygeneruje stránky do scratch adresáře a postaví MkDocs site.

Živá `wiki/` ani `mkdocs.yml` se nemění. Do scratch se zkopírují statické části wiki (index,
o-strance, extra, css, js, prepisy), vygenerují se stránky z `data/`, `mkdocs.yml` se zkopíruje
bez `hooks:` a se starým `nav:` nahrazeným generovaným.

Použití: python -m tools.migrace.nahled --scratch <adresář> [--root .]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

STATICKE = ("index.md", "o-strance.md", "extra", "css", "js", "prepisy")


def _mkdocs_yml(text: str, nav: list) -> str:
    """Odstraní `hooks:` a `nav:` bloky (jen top-level) a připojí generovaný nav."""
    out, skip = [], False
    for r in text.splitlines():
        if re.match(r"^(hooks|nav):", r):
            skip = True
            continue
        if skip and (r.startswith((" ", "\t", "-")) or not r.strip()):
            continue
        skip = False
        out.append(r)
    nav_yaml = yaml.safe_dump({"nav": nav}, allow_unicode=True, sort_keys=False)
    return "\n".join(out).rstrip() + "\n\n" + nav_yaml


def postav(root: Path, scratch: Path, stavet: bool = True) -> list[str]:
    """Vrací seznam řádků WARNING z `mkdocs build`."""
    from tools.archiv.generate import generate

    root, scratch = Path(root).resolve(), Path(scratch).resolve()
    wiki = scratch / "wiki"
    shutil.rmtree(wiki, ignore_errors=True)
    wiki.mkdir(parents=True)
    for n in STATICKE:
        src = root / "wiki" / n
        if src.is_dir():
            shutil.copytree(src, wiki / n)
        elif src.is_file():
            shutil.copy2(src, wiki / n)
    nav = generate(root, wiki)["nav"]
    from tools.migrace.odkazy import prepis_staticke
    prepis_staticke(root, wiki)      # statické stránky se v náhledu přepíšou na nové cesty
    yml = _mkdocs_yml((root / "mkdocs.yml").read_text(encoding="utf-8"), nav)
    (scratch / "mkdocs.yml").write_text(yml, encoding="utf-8", newline="\n")
    if not stavet:
        return []
    site = scratch / "site"
    shutil.rmtree(site, ignore_errors=True)
    r = subprocess.run([sys.executable, "-m", "mkdocs", "build", "-d", str(site),
                        "-f", str(scratch / "mkdocs.yml")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (r.stdout or "") + (r.stderr or "")
    (scratch / "build.log").write_text(log, encoding="utf-8", newline="\n")
    if r.returncode != 0:
        print(log[-3000:])
    return [l for l in log.splitlines() if "WARNING" in l]


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--root", default=".", type=Path)
    a = ap.parse_args(argv)
    w = postav(a.root, a.scratch)
    print(f"WARNING: {len(w)}  (log: {a.scratch / 'build.log'}; web: {a.scratch / 'site' / 'index.html'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
