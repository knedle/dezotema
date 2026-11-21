from datetime import date

from tools.archiv.index import Archiv
from tools.archiv.model import Citace, Osoba, OsobaRef, Vazba, Vyrok, Zdroj
from tools.archiv.render.common import render_vyrok


def _arch():
    cil = Vyrok(id="cil", typ="tvrzeni", temata=["valka"], nadpis="Cílový nadpis", text="c")
    v = Vyrok(id="vyrok-1", typ="postoj", temata=["valka"], nadpis="Nadpis", text="Text výroku.",
              citace=[Citace(text="Přesná citace", cas="04:47")],
              osoby=[OsobaRef(osoba="minar", vztah="negativni", kontext="lhář")],
              vazby=[Vazba(na="cil", typ="opakovani")])
    z = Zdroj(id="2026-11-19_vrabel_test", mluvci="vrabel", kanal="k", titul="Test video",
              datum=date(2026, 11, 19), url="https://x", prepis="2026-11-19_vrabel_test.txt",
              vyroky=[v, cil])
    osoby = {"vrabel": Osoba(slug="vrabel", jmeno="Ladislav Vrabel"),
             "minar": Osoba(slug="minar", jmeno="Mikuláš Minář")}
    return Archiv([z], {}, osoby), v, z


def test_render_vyrok_contains():
    a, v, z = _arch()
    out = render_vyrok(v, z, a, "../")
    assert "### Nadpis {#vyrok-1}" in out
    assert "Ladislav Vrabel" in out
    assert "19. 11. 2026" in out
    assert "postoj" in out
    assert "> „Přesná citace“ [04:47]" in out
    assert "../zdroje/2026-11.md#2026-11-19_vrabel_test" in out
    assert "../prepisy/done/2026-11-19_vrabel_test.txt" in out
    assert "opakuje [Cílový nadpis](../temata/valka.md#cil)" in out
    assert "Mikuláš Minář ❌ — lhář" in out


def test_render_minimal():
    v = Vyrok(id="m", typ="tvrzeni", temata=["t"], nadpis="M", text="Jen text.")
    z = Zdroj(id="z", mluvci="neznamy", kanal="k", titul="T", datum=date(2026, 3, 1),
              url="u", prepis="z.txt", vyroky=[v])
    out = render_vyrok(v, z, Archiv([z], {}, {}), "")
    assert "### M {#m}" in out
    assert "*Osoby:*" not in out and "*Vazby:*" not in out
    assert "tvrzeni" not in out
    assert "neznamy" in out
    assert "\n> " not in out


def test_vazba_cil_bez_temat():
    cil = Vyrok(id="cil", typ="tvrzeni", temata=[], nadpis="C", text="c")
    v = Vyrok(id="v", typ="tvrzeni", temata=["t"], nadpis="V", text="x",
              vazby=[Vazba(na="cil", typ="posun")])
    z = Zdroj(id="z", mluvci="m", kanal="k", titul="T", datum=date(2026, 3, 1),
              url="u", prepis="z.txt", vyroky=[v, cil])
    out = render_vyrok(v, z, Archiv([z], {}, {}), "")
    assert "temata/.md" not in out
    assert "posun oproti cil" in out


def test_viceradkova_citace():
    v = Vyrok(id="v", typ="tvrzeni", temata=["t"], nadpis="V", text="x",
              citace=[Citace(text="první\ndruhý", cas="01:02")])
    z = Zdroj(id="z", mluvci="m", kanal="k", titul="T", datum=date(2026, 3, 1),
              url="u", prepis="z.txt", vyroky=[v])
    out = render_vyrok(v, z, Archiv([z], {}, {}), "")
    assert "> „první\n> druhý“ [01:02]" in out


def test_zrelativni_korenove_odkazy():
    from tools.archiv.render.common import zrelativni
    t = "[a](/temata/x.md#id) [b](/zdroje/2026-11.md#s) [c](https://e.cz/) [d](../x.md) [e](/index.md)"
    assert zrelativni(t, "temata/y.md") == (
        "[a](x.md#id) [b](../zdroje/2026-11.md#s) [c](https://e.cz/) [d](../x.md) [e](../index.md)")
    assert zrelativni(t, "temata/y/2026.md").startswith("[a](../x.md#id) [b](../../zdroje/2026-11.md#s)")
    assert zrelativni("[a](/temata/x.md)", "stochasticky-teror.md") == "[a](temata/x.md)"
    assert zrelativni("[a](/temata/x.md)", "temata/x.md") == "[a](x.md)"


def test_zrelativni_nesaha_do_kodu_a_korenoveho_odkazu():
    from tools.archiv.render.common import zrelativni
    t = "`[a](/x.md)` [b](/x.md)\n```\n[c](/x.md)\n```\n[d](/)\n~~~md\n[e](/x.md)\n~~~\n[f](/y.md#k)"
    assert zrelativni(t, "temata/p.md") == (
        "`[a](/x.md)` [b](../x.md)\n```\n[c](/x.md)\n```\n[d](/)\n~~~md\n[e](/x.md)\n~~~\n"
        "[f](../y.md#k)")
