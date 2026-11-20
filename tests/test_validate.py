import shutil
from pathlib import Path

import yaml

from tools.archiv.validate import validuj

FIX = Path(__file__).parent / "fixtures" / "data_min"
ZDROJ = "data/zdroje/2026/11/2026-11-19_vrabel_test.yaml"


def test_validate_ok():
    assert validuj(FIX) == []


def test_validate_errors(tmp_path):
    root = tmp_path / "r"
    shutil.copytree(FIX, root)
    p = root / ZDROJ
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    v = d["vyroky"]
    v[1]["id"] = v[0]["id"]            # duplicita
    v[0]["temata"] = ["nic"]           # neznámé téma
    v[0]["mluvci"] = "kdosi"           # neznámý mluvčí
    v[2]["typ"] = "blabol"             # neplatný typ
    v.append({"id": "vrabel-2026-11-19-04", "typ": "predikce", "temata": ["volby-2026"],
              "nadpis": "n", "text": "t"})   # chybí blok predikce
    v.append({"id": "vrabel-2026-11-19-05", "typ": "stoch-teror", "temata": ["volby-2026"],
              "nadpis": "n", "text": "t"})   # chybí teror
    d["zdroj"]["prepis"] = "prepisy/done/neni.txt"
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    err = validuj(root)
    joined = "\n".join(err)
    for needle in ["duplicit", "neznámé téma 'nic'", "neznámý mluvčí 'kdosi'",
                   "neplatný typ 'blabol'", "vrabel-2026-11-19-04: typ predikce",
                   "vrabel-2026-11-19-05: typ stoch-teror",
                   "2026-11-19_vrabel_test: přepis neexistuje"]:
        assert needle in joined, needle
    assert all("vrabel-2026-11-19" in e or "2026-11-19_vrabel_test" in e for e in err)
