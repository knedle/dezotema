from datetime import date

from tools.archiv.index import Archiv
from tools.archiv.model import OsobaRef, Predikce, Vyrok, Zdroj


def _z(id, datum, mluvci="peterkova", vyroky=(), osoby=()):
    return Zdroj(id=id, mluvci=mluvci, kanal="k", titul="T " + id, datum=datum,
                 url="https://x", prepis=f"{id}.txt", osoby=list(osoby),
                 vyroky=list(vyroky))


def _v(id, typ="tvrzeni", temata=("t",), **kw):
    return Vyrok(id=id, typ=typ, temata=list(temata), nadpis="N " + id, text="x", **kw)


def test_mluvci_override():
    v = _v("a", mluvci="zitko")
    v2 = _v("b")
    z = _z("z1", date(2026, 3, 1), vyroky=[v, v2])
    a = Archiv([z], {}, {})
    assert a.mluvci_vyroku(v, z) == "zitko"
    assert a.mluvci_vyroku(v2, z) == "peterkova"


def test_podle_tematu_order():
    zs = [_z("z1", date(2026, 3, 1), vyroky=[_v("a")]),
          _z("z2", date(2026, 3, 5), vyroky=[_v("b")]),
          _z("z3", date(2026, 3, 2), vyroky=[_v("c")])]
    ids = [v.id for v, _ in Archiv(zs, {}, {}).podle_tematu("t")]
    assert ids == ["b", "c", "a"]


def test_zminky_include_zdroj_level():
    ref = OsobaRef(osoba="minar", vztah="negativni")
    z = _z("z1", date(2026, 3, 1), osoby=[ref], vyroky=[_v("a")])
    zm = Archiv([z], {}, {}).zminky_osoby("minar")
    assert zm == [(ref, None, z)]


def test_propadle():
    p = _v("a", typ="predikce",
           predikce=Predikce(horizont="x", horizont_do=date(2026, 11, 1), stav="ceka"))
    q = _v("b", typ="predikce",
           predikce=Predikce(horizont="x", horizont_do=date(2026, 11, 1), stav="vyvraceno"))
    z = _z("z1", date(2026, 3, 1), vyroky=[p, q])
    a = Archiv([z], {}, {})
    assert [v.id for v, _ in a.nevyhodnocene_propadle(date(2026, 11, 20))] == ["a"]
    assert len(a.predikce()) == 2
