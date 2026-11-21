from datetime import date
from pathlib import Path

from tools.migrace import prehled as H

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"
KOTVY = {"stranky": {"valka-nato-rusko.md#summit-trump-putin-si-multipolarita-vrabel-19-11-2026":
                     "vrabel-2026-11-19-01"}, "kotvy": {}}


def test_prehled_link_to_vyrok():
    md = (FIX / "prehled_2026-11-19.md").read_text(encoding="utf-8")
    dny = H.parsuj(md, KOTVY)
    pol = dny[date(2026, 11, 19)]
    assert len(pol) == 23
    prvni = pol[0]
    assert prvni.tema == "Summit USA–Rusko–Čína" and prvni.vyrok == "vrabel-2026-11-19-01"
    assert "→ viz" not in prvni.text and "nový světový pořádek" in prvni.text
    assert any(p.vyrok is None and "→ viz [" in p.text for p in pol)     # nepřeložený odkaz zůstane
    assert any(p.vyrok is None and "→ viz" not in p.text for p in pol)   # položka bez odkazu
    den = H.parsuj_dny(md, KOTVY)[0]
    assert den.kotvy == ["ladislav-vrabel--zprávy-v-devět-19-11-2026"]
    assert den.titul.startswith("Zprávy v devět")


DEN = """## 2026-08-21 — Zprávy v devět

- **Krypto:** ⚡ dno cyklu → viz [Ceny energie](../ceny-energie.md)
- Ostatní — nic

**Predikce:** [Kryptoměny dosáhly dna](../predikce.md#ladislav-vrabel--krypto-21-8-2026)
**Stochastický teror:** [Babiš — výzva](../stochasticky-teror.md)
**Zdroj:** [Z](../_zdroje.md#a--b)

**Samostatné video (5. 9.):** celé věnováno zatčení → [DSA a cenzura](../dsa-cenzura.md); [zdroj](../_zdroje.md#c--d)

---
"""


def test_stitkove_radky_nejsou_ztraceny():
    kotvy = {"stranky": {"predikce.md#ladislav-vrabel--krypto-21-8-2026": "vrabel-2026-08-21-09"}}
    den = H.parsuj_dny(DEN, kotvy)[0]
    temata = [p.tema for p in den.polozky]
    assert "Predikce" in temata and "Stochastický teror" in temata
    pred = next(p for p in den.polozky if p.tema == "Predikce")
    assert pred.vyrok == "vrabel-2026-08-21-09" and "Kryptoměny dosáhly dna" in pred.text
    assert len(den.vlastni) == 1 and den.vlastni[0][0] == ["c--d"]
    assert den.vlastni[0][1].tema == "Samostatné video (5. 9.)"
    assert "_zdroje" not in den.vlastni[0][1].text and not den.nerozpoznano


def test_nerozpoznany_radek_se_hlasi():
    den = H.parsuj_dny("## 2026-08-21 — X\n\nnějaký odstavec bez štítku\n", {})[0]
    assert den.nerozpoznano == ["nějaký odstavec bez štítku"]


def test_prirad_stranky_vyzaduje_shodu_slov():
    from tools.archiv.model import PrehledPolozka, Vyrok, Zdroj
    z = Zdroj(id="z", mluvci="vrabel", kanal="", titul="t", datum=date(2026, 9, 26), url="",
              prepis="p")
    z.vyroky = [Vyrok("v1", "tvrzeni", ["politicky-system"], "Rozpočet", "Debata o státním rozpočtu.")]
    temata = {"politicky-system": object()}
    shoda = PrehledPolozka("Rozpočet státu", "⚡ rozpočet se zvyšuje → viz [P](../politicky-system.md)")
    bez = PrehledPolozka("Hrušková, Štěpán a Rajchl", "⚡ spor → viz [P](../politicky-system.md)")
    assert H.prirad_stranky([shoda, bez], z, temata) == 1
    assert shoda.vyrok == "v1" and "→ viz" not in shoda.text
    assert bez.vyrok is None and "../politicky-system.md" in bez.text      # odkaz zůstává v textu
