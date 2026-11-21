from datetime import date

from tools.archiv.index import Archiv
from tools.archiv.model import Osoba, Predikce, Tema, Vyrok, Zdroj
from tools.migrace.report import srovnani

PRED = """# Predikce

### Jindřich Rajchl — první (1. 5. 2026)

**Předpověď:** A.

**Horizont:** neurčeno
**Stav:** 🕐 Čeká na vyhodnocení
**Zdroj:** [Z](_zdroje.md#a)

---

### Jindřich Rajchl — druhá (2. 5. 2026)

**Předpověď:** B.

**Horizont:** neurčeno
**Stav:** ✅ Potvrzeno
**Zdroj:** [Z](_zdroje.md#a)

---
"""


def test_report_counts(tmp_path):
    (tmp_path / "predikce.md").write_text(PRED, encoding="utf-8")
    vs = [Vyrok(id=f"rajchl-2026-05-0{i}-01", typ="predikce", temata=["t"], nadpis="n", text="x",
                predikce=Predikce(horizont="neurčeno", stav=s))
          for i, s in ((1, "ceka"), (2, "potvrzeno"))]
    z = Zdroj(id="z", mluvci="rajchl", kanal="k", titul="Z", datum=date(2026, 5, 1), url="",
              prepis="prepisy/done/z.txt", vyroky=vs)
    a = Archiv([z], {"t": Tema("t", "T")}, {"rajchl": Osoba("rajchl", "Rajchl")})
    r = srovnani(tmp_path, a, {"jednotky": [{"x": 1}], "teror": []})
    assert "Predikce: 2 / 2" in r
    assert "Nezařazeno: 1" in r
    assert "Predikce — stav potvrzeno: 1 / 1" in r
