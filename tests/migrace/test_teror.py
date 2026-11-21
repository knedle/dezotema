from datetime import date
from pathlib import Path

from tools.archiv.model import Zdroj
from tools.migrace import teror as T

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"


def test_teror_hranicni():
    rows = T.parsuj((FIX / "teror.md").read_text(encoding="utf-8"))
    assert len(rows) == 3
    assert [r.hranicni for r in rows] == [False, True, False]
    assert rows[1].terc == "dárci sbírek „Dárek pro Putina“"       # značka se odstraní
    assert rows[0].datum == date(2026, 4, 2) and rows[0].kotvy
    z = Zdroj(id="2026-06-13_vrabel_x", mluvci="vrabel", kanal="", titul="x", datum=date(2026, 6, 13),
              url="", prepis="p")
    v = T.na_vyrok(rows[2], z, 2, temata=["kauzy"])
    assert v.typ == "stoch-teror" and v.id == "vrabel-2026-06-13-02"
    assert v.teror.terc == "Adam Vojtěch" and v.teror.hranicni is False
    assert v.citace[0].text.startswith("držte mě, nebo pusťte mě na něj")
    assert all(" — " not in c.text for c in v.citace)      # redakční komentář není citace
    assert "pojmenovaný terč" in v.text



_HLAVICKA = ("| Autor | Jmenovaná osoba / skupina | Přesná citace | Datum | Zdroj |\n"
             "|---|---|---|---|---|\n")


def _radek(col, terc="X"):
    return _HLAVICKA + f"| Ladislav Vrabel | {terc} | {col} | 16. 10. 2026 | [Z](_zdroje.md#a-b) |\n"


def test_hranicni_neni_zahranicni():
    assert T.parsuj(_radek("„Mluví o zahraničního agentovi.“"))[0].hranicni is False
    assert T.parsuj(_radek("„Text.“ — hraniční, bez výzvy"))[0].hranicni is True


def test_citace_jen_citovana_cast():
    r = T.parsuj(_radek("Pavel „ta svině“; o Pavlové: „táhni dělat do Lidlu“ — dehumanizace bez výzvy"))[0]
    assert r.citace == ["ta svině", "táhni dělat do Lidlu"]
    assert r.kontext == "Pavel …; o Pavlové: … — dehumanizace bez výzvy"


def test_citace_bez_uvozovek_je_text():
    r = T.parsuj(_radek("Email s předmětem a hrozbou, veřejně obhajoval"))[0]
    assert r.citace == [] and r.kontext == "Email s předmětem a hrozbou, veřejně obhajoval"


def test_citace_cista_bez_komentare():
    r = T.parsuj(_radek('„Jen citace [...] druhá věta."'))[0]
    assert r.citace == ["Jen citace [...] druhá věta."] and r.kontext == ""
