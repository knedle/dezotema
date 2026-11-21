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
    assert "pojmenovaný terč" in v.text
