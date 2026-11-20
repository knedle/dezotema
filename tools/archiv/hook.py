"""MkDocs hook: vygeneruje stránky z data/ a nastaví navigaci."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def _hash_dat(data: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(data.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(data).as_posix().encode("utf-8") + b"\0")
            h.update(p.read_bytes() + b"\0")
    return h.hexdigest()


def on_config(config):
    docs = Path(config["docs_dir"])
    root = docs.parent
    data = root / "data"
    if not (data / "temata.yaml").is_file() or (docs / "_zdroje.md").exists():
        return config

    # MkDocs načítá hook jako samostatný soubor, kořen repa není v sys.path
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.archiv.generate import _nav, generate
    from tools.archiv.index import Archiv
    from tools.archiv.io import nacti_vse

    novy = _hash_dat(data)
    cache = root / ".cache" / "archiv.hash"
    try:
        stary = cache.read_text(encoding="utf-8").strip()
    except OSError:
        stary = ""

    if novy != stary or not (docs / "temata").is_dir():
        nav = generate(root, docs)["nav"]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(novy, encoding="utf-8")
    else:
        nav = _nav(Archiv(*nacti_vse(root)))
    config["nav"] = nav
    return config
