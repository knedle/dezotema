from datetime import date

from tools.archiv.io import nacti_zdroj, uloz_zdroj
from tools.archiv.model import (Citace, OsobaRef, Predikce, Vazba, Vyhodnoceni,
                                Vyrok, Zdroj)


def _zdroj():
    return Zdroj(
        id="x_test", mluvci="vrabel", kanal="K", titul="T", datum=date(2026, 11, 19),
        url="https://e.org", prepis="prepisy/done/x.txt", cas="21:21",
        osoby=[OsobaRef("trump", "neutralni")],
        vyroky=[Vyrok(
            id="vrabel-2026-11-19-01", typ="predikce", temata=["a"], nadpis="N",
            text="Řádek jedna.\nŘádek dvě.\n",
            citace=[Citace("„Je to tak.“", "04:47")],
            osoby=[OsobaRef("trump", "rozporuplny", "k")],
            vazby=[Vazba("vrabel-2026-11-14-03", "posun")],
            predikce=Predikce("do roku", horizont_do=date(2026, 12, 7),
                              vyhodnoceni=[Vyhodnoceni(date(2026, 11, 20), "t", "castecne")]),
        )],
    )


def test_roundtrip(tmp_path):
    z = _zdroj()
    p = uloz_zdroj(z, tmp_path)
    assert p == tmp_path / "data" / "zdroje" / "2026" / "11" / "x_test.yaml"
    assert nacti_zdroj(p) == z
    raw = p.read_text(encoding="utf-8")
    assert "„Je to tak.“" in raw
    assert "text: |" in raw
    assert "[]" not in raw and "null" not in raw


def test_zdroj_bez_url_a_seznamy_roundtrip(tmp_path):
    from datetime import date
    from tools.archiv.io import (nacti_osoby, nacti_temata, nacti_zdroj,
                                 uloz_osoby, uloz_temata, uloz_zdroj)
    from tools.archiv.model import Osoba, Tema, Zdroj
    z = Zdroj("2026-01-01_a_b", "a", "k", "t", date(2026, 1, 1), "", "prepisy/done/x.txt")
    assert nacti_zdroj(uloz_zdroj(z, tmp_path)).url == ""
    uloz_temata([Tema("t", "T", "", "n")], tmp_path / "t.yaml")
    uloz_osoby([Osoba("a", "A", ["x"], "", True, True)], tmp_path / "o.yaml")
    assert nacti_temata(tmp_path / "t.yaml")["t"].nadrazene == "n"
    assert nacti_osoby(tmp_path / "o.yaml")["a"].aliasy == ["x"]
