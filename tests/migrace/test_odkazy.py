from datetime import date

from tools.archiv.index import Archiv
from tools.archiv.model import Osoba, Predikce, Tema, Vyrok, Zdroj
from tools.migrace.odkazy import Prekladac


def _p():
    v1 = Vyrok(id="zitko-1", typ="tvrzeni", temata=["vetrniky", "ceny"], nadpis="N", text="t")
    v2 = Vyrok(id="vrabel-1", typ="predikce", temata=[], nadpis="P", text="t",
               predikce=Predikce(horizont="x"))
    z1 = Zdroj(id="z1", mluvci="zitko", kanal="k", titul="T", datum=date(2026, 3, 10), url="u",
               prepis="prepisy/done/a.txt", vyroky=[v1])
    z2 = Zdroj(id="z2", mluvci="vrabel", kanal="k", titul="T", datum=date(2026, 11, 2), url="u",
               prepis="prepisy/done/b.txt", vyroky=[v2], prehled=[])
    a = Archiv([z1, z2], {"vetrniky": Tema("vetrniky", "V"), "ceny": Tema("ceny", "C")},
               {"zitko": Osoba("zitko", "Z", vlastni_stranka=True), "x": Osoba("x", "X")})
    stare = {"stranky": {"vetrniky.md#stara": "zitko-1", "predikce.md#pr": "vrabel-1",
                         "ceny.md#c": "zitko-1"},
             "kapitoly": {}, "kotvy": {"holá": "zitko-1"}}
    return Prekladac(a, stare, {"zdroj-kotva": "z1"})


def _t(p, text, **kw):
    return p.text(text, "kde", **kw)


def test_tema_kotva_a_relativni_cesta_o_uroven_vys():
    p = _p()
    assert _t(p, "[a](vetrniky.md#stara)") == "[a](/temata/vetrniky.md#zitko-1)"
    assert _t(p, "[a](../vetrniky.md#stara)") == "[a](/temata/vetrniky.md#zitko-1)"
    assert _t(p, "[a](ceny.md#c)") == "[a](/temata/ceny.md#zitko-1)"
    assert _t(p, "[a](#holá)") == "[a](/temata/vetrniky.md#zitko-1)"
    assert _t(p, "[a](vetrniky.md)") == "[a](/temata/vetrniky.md)"


def test_zdroje_predikce_osoby_prepis():
    p = _p()
    assert _t(p, "[a](_zdroje.md#zdroj-kotva)") == "[a](/zdroje/2026-03.md#z1)"
    assert _t(p, "[a](../predikce.md#pr)") == "[a](/predikce/2026-11.md#vrabel-1)"
    assert _t(p, "[a](predikce.md)") == "[a](/predikce/index.md)"
    assert _t(p, "[a](osoby/zitko.md)") == "[a](/osoby/zitko.md)"
    assert _t(p, "[a](prepisy/done/a.txt)") == "[a](/prepisy/done/a.txt)"
    assert _t(p, "[a](../stochasticky-teror.md#přehled-výroků)") == (
        "[a](/stochasticky-teror.md#přehled-výroků)")


def test_souhrn_osoby_ma_zakladnu_osoby():
    p = _p()
    assert p.text("[a](../vetrniky.md#stara) [b](zitko.md)", "s", "osoby") == (
        "[a](/temata/vetrniky.md#zitko-1) [b](/osoby/zitko.md)")


def test_neznama_kotva_opravi_stranku_ostatni_beze_zmeny():
    p = _p()
    assert _t(p, "[a](../vetrniky.md#nic)") == "[a](/temata/vetrniky.md#nic)"
    t = "Text [a](neni.md#x) a [w](https://e.cz/x) a ![i](img.png) a [r](/uz/root.md)"
    assert _t(p, t) == t
    assert p.nepreložené == ["kde -> ../vetrniky.md#nic", "kde -> neni.md#x"]
    assert (p.celkem, p.prelozeno) == (2, 0)


def test_idempotence():
    p = _p()
    jednou = _t(p, "[a](vetrniky.md#stara)")
    assert _t(p, jednou) == jednou
