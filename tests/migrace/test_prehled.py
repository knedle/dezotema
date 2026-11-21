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
