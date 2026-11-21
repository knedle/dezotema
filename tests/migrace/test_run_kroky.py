import yaml

from tools.migrace import run as R
from tools.migrace import teror as T


def test_nezarazeno_nahrazuje_jen_svuj_klic(tmp_path):
    (tmp_path / "data" / "zdroje").mkdir(parents=True)
    R._uloz_nezarazeno(tmp_path, "jednotky", [{"a": 1}])
    R._uloz_nezarazeno(tmp_path, "teror", [{"b": 2}])
    R._uloz_nezarazeno(tmp_path, "jednotky", [{"a": 3}])
    d = yaml.safe_load((tmp_path / "data" / "zdroje" / "_nezarazeno.yaml").read_text(encoding="utf-8"))
    assert d == {"jednotky": [{"a": 3}], "teror": [{"b": 2}]}
    R._uloz_nezarazeno(tmp_path, "teror", [])
    d = yaml.safe_load((tmp_path / "data" / "zdroje" / "_nezarazeno.yaml").read_text(encoding="utf-8"))
    assert d == {"jednotky": [{"a": 3}], "teror": []}


def test_neznamy_krok(tmp_path):
    assert R.main(["--krok", "nesmysl", "--root", str(tmp_path)]) == 2


def test_teror_hranicni_v_komentari():
    md = ("| Autor | Jmenovaná osoba / skupina | Přesná citace | Datum | Zdroj |\n"
          "|---|---|---|---|---|\n"
          "| Ladislav Vrabel | Donald Trump | „Je to diktátor.“ — hraniční: popisné rámování | "
          "16. 10. 2026 | [Z](_zdroje.md#a-b) |\n")
    r = T.parsuj(md)[0]
    assert r.hranicni is True and r.kontext.startswith("hraniční:")
    assert r.citace == "Je to diktátor."
