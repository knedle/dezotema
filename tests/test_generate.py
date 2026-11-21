import json
import shutil
from datetime import date
from pathlib import Path

from tools.archiv.generate import generate, main
from tools.archiv.io import uloz_zdroj
from tools.archiv.model import Vyrok, Zdroj

FIX = Path(__file__).parent / "fixtures" / "data_gen"


def _gen(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    out = root / "wiki"
    return root, out, generate(root, out)


def test_generate_files(tmp_path):
    root, out, res = _gen(tmp_path)
    for p in ["temata/vetrniky.md", "osoby/zitko.md", "predikce/index.md",
              "stochasticky-teror.md", "zdroje/index.md", "zdroje/2026-11.md",
              "zpravodajstvi-vrabel/2026-11.md", "data/vyroky.json", "zminene/minar.md"]:
        assert (out / p).is_file(), p
    assert out / "temata/vetrniky.md" in res["soubory"]
    assert not (out / "osoby/minar.md").exists()


def test_tema_contains_all(tmp_path):
    root, out, _ = _gen(tmp_path)
    t = (out / "temata/vetrniky.md").read_text(encoding="utf-8")
    assert "{#zitko-2026-03-10-01}" in t
    assert "{#zitko-2026-03-10-02}" in t  # druhé téma
    assert "{#vrabel-2026-11-19-01}" in t
    assert "{#zitko-2026-03-10-03}" not in t
    assert "Souhrn větrníků." in t
    assert "Ceny" in t and "Ostatní" in t


def test_split_by_year(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    vy = [Vyrok(id=f"x-{i}", typ="tvrzeni", temata=["vetrniky"], nadpis=f"N{i}", text="t")
          for i in range(151)]
    for rok, sl in ((2025, vy[:75]), (2026, vy[75:])):
        uloz_zdroj(Zdroj(id=f"{rok}-01-01_s", mluvci="zitko", kanal="k", titul="t",
                         datum=date(rok, 1, 1), url="u",
                         prepis="prepisy/done/2026-03-10_zitko_prvni.txt", vyroky=sl), root)
    generate(root, root / "wiki")
    out = root / "wiki"
    assert (out / "temata/vetrniky/2025.md").is_file()
    assert (out / "temata/vetrniky/2026.md").is_file()
    main_page = (out / "temata/vetrniky.md").read_text(encoding="utf-8")
    assert "vetrniky/2025.md" in main_page and "vetrniky/2026.md" in main_page
    assert "{#x-0}" not in main_page
    assert "{#x-0}" in (out / "temata/vetrniky/2025.md").read_text(encoding="utf-8")


def test_json_export(tmp_path):
    root, out, _ = _gen(tmp_path)
    data = json.loads((out / "data/vyroky.json").read_text(encoding="utf-8"))
    klice = {"id", "typ", "temata", "mluvci", "datum", "zdroj", "url", "prepis", "nadpis",
             "text", "citace", "osoby", "vazby", "predikce", "teror"}
    assert all(set(d) == klice for d in data)
    assert len(data) == 5
    assert {d["mluvci"] for d in data} == {"zitko", "vrabel"}


def test_vrabel_prehled_link(tmp_path):
    root, out, _ = _gen(tmp_path)
    t = (out / "zpravodajstvi-vrabel/2026-11.md").read_text(encoding="utf-8")
    assert "## 2026-11-19 — Denní komentář" in t
    assert "⚡" in t
    assert "../temata/vetrniky.md#vrabel-2026-11-19-01" in t
    assert "Jen popis stavu." in t
    assert "**Zdroj:**" in t


def test_nezpracovane(tmp_path):
    root, out, _ = _gen(tmp_path)
    t = (out / "zdroje/index.md").read_text(encoding="utf-8")
    sekce = t.split("Nezpracované / přeskočené přepisy")[1]
    assert "2026-01-01_orphan.txt" in sekce
    assert "zitko_prvni" not in sekce


def test_nav_shape(tmp_path):
    root, out, res = _gen(tmp_path)
    nav = res["nav"]
    assert nav[0] == {"Úvod": "index.md"}
    temata = next(i for i in nav if "Témata" in i)["Témata"]
    assert {"Větrné elektrárny": "temata/vetrniky.md"} in temata
    assert any("Osoby" in i for i in nav)


def test_zdroje_predikce_teror_osoba(tmp_path):
    root, out, _ = _gen(tmp_path)
    z = (out / "zdroje/2026-03.md").read_text(encoding="utf-8")
    assert "## Pavel Zítko — První video {#2026-03-10_zitko_prvni}" in z
    assert "../prepisy/done/2026-03-10_zitko_prvni.txt" in z
    assert "prepisy/done/prepisy" not in z
    p = (out / "predikce/index.md").read_text(encoding="utf-8")
    assert "Propadlé k vyhodnocení" in p and "Konec covidu" in p
    assert "Potvrzeno" in (out / "predikce/2026-11.md").read_text(encoding="utf-8")
    s = (out / "stochasticky-teror.md").read_text(encoding="utf-8")
    assert "Hraniční" in s and "Ruční poznámka." in s and "Nějaký lékař" in s
    o = (out / "osoby/zitko.md").read_text(encoding="utf-8")
    assert "Mikuláš Minář" in o and "../zminene/minar.md" in o


def test_clean_only_generated(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    out = root / "wiki"
    (out / "index.md").write_text("keep", encoding="utf-8")
    (out / "temata").mkdir()
    (out / "temata" / "stary.md").write_text("old", encoding="utf-8")
    generate(root, out)
    assert (out / "index.md").read_text(encoding="utf-8") == "keep"
    assert not (out / "temata/stary.md").exists()
    assert (out / "prepisy/done/2026-01-01_orphan.txt").exists()


def test_deterministic_and_cli(tmp_path, capsys):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    out = root / "wiki"
    assert main(["--root", str(root), "--out", str(out)]) == 0
    assert capsys.readouterr().out.strip()
    a = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    generate(root, out)
    b = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    assert a == b


def test_links_target_split_year_page(tmp_path):
    from tools.archiv.model import Vazba, PrehledPolozka
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    vy = [Vyrok(id=f"x-{i}", typ="tvrzeni", temata=["vetrniky"], nadpis=f"N{i}", text="t")
          for i in range(151)]
    vy[100].vazby = [Vazba(na="x-0", typ="souhlas")]
    uloz_zdroj(Zdroj(id="2025-01-01_s", mluvci="zitko", kanal="k", titul="t",
                     datum=date(2025, 1, 1), url="u",
                     prepis="prepisy/done/2026-03-10_zitko_prvni.txt", vyroky=vy[:1]), root)
    uloz_zdroj(Zdroj(id="2026-01-01_s", mluvci="vrabel", kanal="k", titul="t2",
                     datum=date(2026, 1, 1), url="u",
                     prepis="prepisy/done/2026-03-10_zitko_prvni.txt",
                     prehled=[PrehledPolozka(tema="vetrniky", text="p", vyrok="x-0")],
                     vyroky=vy[1:]), root)
    generate(root, root / "wiki")
    out = root / "wiki"
    assert "../../temata/vetrniky/2025.md#x-0" in (
        out / "temata/vetrniky/2026.md").read_text(encoding="utf-8")
    assert "../temata/vetrniky/2025.md#x-0" in (
        out / "zpravodajstvi-vrabel/2026-01.md").read_text(encoding="utf-8")


def test_klic_cs():
    from tools.archiv.generate import klic_cs
    assert sorted(["Žena", "Čas", "Cena", "Zdroj", "Ceny"], key=klic_cs) == [
        "Cena", "Ceny", "Čas", "Zdroj", "Žena"]
    assert sorted(["Chata", "Hrad", "Ivan"], key=klic_cs) == ["Hrad", "Chata", "Ivan"]


def test_souhrn_front_matter(tmp_path):
    from tools.archiv.render.tema import souhrn
    s = tmp_path / "a.md"
    s.write_text("---\naktualizovano: 2026-11-05\n---\nTělo souhrnu.\n", encoding="utf-8")
    t = souhrn(s)
    assert "Tělo souhrnu." in t and "Aktualizováno: 5. 11. 2026" in t and "---" not in t
    s.write_text("Bez hlavičky.\n", encoding="utf-8")
    t = souhrn(s)
    assert t.strip() == "Bez hlavičky." and "ktualizov" not in t


def test_pipe_in_cell_escaped(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    f = root / "data/zdroje/2026/03/2026-03-10_zitko_prvni.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("kritika", "a|b"), encoding="utf-8")
    generate(root, root / "wiki")
    out = root / "wiki"
    assert r"a\|b" in (out / "osoby/zitko.md").read_text(encoding="utf-8")
    assert r"a\|b" in (out / "zminene/minar.md").read_text(encoding="utf-8")


def test_vrabel_heading(tmp_path):
    root, out, res = _gen(tmp_path)
    assert "# Zpravodajství Vrabel — 2026-11" in (
        out / "zpravodajstvi-vrabel/2026-11.md").read_text(encoding="utf-8")
    assert any("Zpravodajství Vrabel" in i for i in res["nav"])


def test_korenove_odkazy_v_datech_se_relativizuji_podle_stranky(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(FIX, root)
    v = Vyrok(id="odk-1", typ="tvrzeni", temata=["vetrniky"], nadpis="N",
              text="Viz [zdroj](/zdroje/2026-03.md#x) a [web](https://e.cz/).")
    uloz_zdroj(Zdroj(id="2026-03-20_s", mluvci="zitko", kanal="k", titul="t",
                     datum=date(2026, 3, 20), url="u",
                     prepis="prepisy/done/2026-03-10_zitko_prvni.txt", vyroky=[v]), root)
    generate(root, root / "wiki")
    t = (root / "wiki/temata/vetrniky.md").read_text(encoding="utf-8")
    assert "[zdroj](../zdroje/2026-03.md#x)" in t and "](https://e.cz/)" in t
    assert "](/" not in t
