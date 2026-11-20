from __future__ import annotations

import dataclasses
from pathlib import Path

import yaml

from .model import (Citace, Osoba, OsobaRef, Predikce, PrehledPolozka, Tema,
                    Teror, Vazba, Vyhodnoceni, Vyrok, Zdroj)


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str)


def _clean(obj):
    """Dataclass -> dict; prázdné seznamy, None a prázdné řetězce se vynechají."""
    if dataclasses.is_dataclass(obj):
        d = {}
        for f in dataclasses.fields(obj):
            v = _clean(getattr(obj, f.name))
            if v is None or v == [] or v == "":
                continue
            d[f.name] = v
        return d
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    return obj


def _list(cls, items):
    return [cls(**i) for i in (items or [])]


def _vyrok(d: dict) -> Vyrok:
    d = dict(d)
    d["citace"] = _list(Citace, d.get("citace"))
    d["osoby"] = _list(OsobaRef, d.get("osoby"))
    d["vazby"] = _list(Vazba, d.get("vazby"))
    p = d.get("predikce")
    if p is not None:
        p = dict(p)
        p["vyhodnoceni"] = _list(Vyhodnoceni, p.get("vyhodnoceni"))
        d["predikce"] = Predikce(**p)
    if d.get("teror") is not None:
        d["teror"] = Teror(**d["teror"])
    return Vyrok(**d)


def _zdroj(data: dict) -> Zdroj:
    z = dict(data["zdroj"])
    z["osoby"] = _list(OsobaRef, z.get("osoby"))
    z["prehled"] = _list(PrehledPolozka, z.get("prehled"))
    z["vyroky"] = [_vyrok(v) for v in data.get("vyroky") or []]
    return Zdroj(**z)


def nacti_zdroj(path) -> Zdroj:
    with open(path, encoding="utf-8") as f:
        return _zdroj(yaml.safe_load(f))


def uloz_zdroj(z: Zdroj, root) -> Path:
    root = Path(root)
    path = root / "data" / "zdroje" / f"{z.datum:%Y}" / f"{z.datum:%m}" / f"{z.id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    full = _clean(z)
    vyroky = full.pop("vyroky", [])
    out = {"zdroj": full}
    if vyroky:
        out["vyroky"] = vyroky
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(out, f, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=100)
    return path


def nacti_vse(root) -> tuple[list[Zdroj], dict[str, Tema], dict[str, Osoba]]:
    root = Path(root)
    zdroje = [nacti_zdroj(p) for p in sorted((root / "data" / "zdroje").glob("*/*/*.yaml"))]
    temata, osoby = {}, {}
    with open(root / "data" / "temata.yaml", encoding="utf-8") as f:
        for t in (yaml.safe_load(f) or {}).get("temata") or []:
            temata[t["slug"]] = Tema(**t)
    with open(root / "data" / "osoby.yaml", encoding="utf-8") as f:
        for o in (yaml.safe_load(f) or {}).get("osoby") or []:
            osoby[o["slug"]] = Osoba(**o)
    return zdroje, temata, osoby
