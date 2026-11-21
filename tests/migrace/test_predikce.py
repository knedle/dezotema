from datetime import date
from pathlib import Path

from tools.archiv.model import Zdroj
from tools.migrace import predikce as P

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"


def _z():
    return Zdroj(id="2026-11-11_zitko_svatomartinske", mluvci="zitko", kanal="", titul="Svatomartinské",
                 datum=date(2026, 11, 11), url="", prepis="prepisy/done/x.txt")


def test_predikce_vyhodnoceni():
    raw = P.parsuj((FIX / "predikce_ebs.md").read_text(encoding="utf-8"))
    assert len(raw) == 1
    r = raw[0]
    assert r.mluvci_text == "Pavel Zítko" and r.datum == date(2026, 11, 11)
    assert r.stav == "vyvraceno" and len(r.kotvy) == 4
    v = P.na_vyrok(r, _z(), 3)
    assert v.id == "zitko-2026-11-11-03" and v.typ == "predikce"
    assert v.predikce.stav == "vyvraceno"
    datumy = [h.datum for h in v.predikce.vyhodnoceni]
    assert {date(2026, 11, 16), date(2026, 11, 17), date(2026, 11, 18)} <= set(datumy)
    assert datumy == sorted(datumy)                    # chronologicky
    prvni = next(h for h in v.predikce.vyhodnoceni if h.stav)   # text stavu za pomlčkou
    assert prvni.stav == "vyvraceno" and "test 17. 11. proběhl jen jako test" in prvni.text
    assert len(v.citace) == 1 and v.citace[0].text.startswith("Některý predikujou")
    assert v.predikce.horizont.startswith("17. 11. 2026 (EBS")
    assert v.predikce.horizont_do is None            # dvě různá data -> nejednoznačné


def test_vyhodnoceni_20_11_a_stav_castecne():
    r = P.parsuj((FIX / "predikce_vyhodnoceni.md").read_text(encoding="utf-8"))[0]
    assert r.stav == "castecne"
    v = P.na_vyrok(r, _z(), 1)
    audit = [h for h in v.predikce.vyhodnoceni if h.text.startswith("Summit Trump")]
    assert audit and audit[0].datum == date(2026, 11, 20)
    assert any(h.datum == date(2026, 11, 19) for h in v.predikce.vyhodnoceni)


def test_horizont_do():
    assert P.horizont_do("do cca 18. 12. 2026 (35 dní); 1. 12. 2026 (Q-phone); +120 dní (volby)") \
        == date(2026, 12, 18)
    assert P.horizont_do("neurčeno") is None
    assert P.horizont_do("do 2028") == date(2028, 12, 31)
    assert P.horizont_do("do roku 2034") == date(2034, 12, 31)
    assert P.horizont_do("kolem 3. 11. 2026") == date(2026, 11, 3)
    assert P.horizont_do("od 31. 10. 2026") is None
    assert P.horizont_do("2030") is None


def test_horizont_do_nejednoznacny():
    for s in ["21. 9. 2026 (příprava od 13. 8. do 11. 9. 2026)",
              "zhruba do poloviny prosince 2026 (stíhání); 14. 2. 2027 (Super Bowl)",
              "po amerických volbách 2026 (3. 11. 2026)",
              "před 3. 10. 2026 nebo krátce po",
              "do 18. 5.–18. 11. 2027",
              "17. 11. 2026 (EBS, s výhradou); 22. 11. 2026 (QFS)"]:
        assert P.horizont_do(s) is None, s
