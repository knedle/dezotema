from pathlib import Path

from tools.archiv.model import Osoba, Tema
from tools.migrace import souhrny as S

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"


def test_uvod_vetrniky():
    u = S.uvod_stranky((FIX / "vetrniky_1-92.md").read_text(encoding="utf-8"))
    assert u.startswith("Větrné elektrárny a plánované akcelerační zóny")
    assert "---" not in u and "##" not in u and "Rajchl ve videu" not in u


def test_uvod_osoby_bez_popisu_a_prazdny(tmp_path):
    md = "# Jméno\n\nPopis osoby.\n\n---\n\nDalší odstavec.\n\n## Témata\n"
    assert S.uvod_osoby(md, "Popis osoby.") == "Další odstavec."
    assert S.uvod_stranky("# X\n\n---\n\n## A\n") == ""
    wiki = tmp_path / "w"
    (wiki / "osoby").mkdir(parents=True)
    (wiki / "t.md").write_text("# X\n\n---\n\n## A\n", encoding="utf-8")
    (wiki / "u.md").write_text("# U\n\nText *kurz*.\n\n---\n\n## A\n", encoding="utf-8")
    (wiki / "osoby" / "o.md").write_text(md, encoding="utf-8")
    r = S.zapis_souhrny(wiki, tmp_path, {"t": Tema("t", "T"), "u": Tema("u", "U")},
                        {"o": Osoba("o", "O", popis="Popis osoby.", vlastni_stranka=True)})
    assert r["prazdne"] == ["t.md"] and r["temata"] == 1 and r["osoby"] == 1
    assert not (tmp_path / "data/souhrny/temata/t.md").exists()
    assert (tmp_path / "data/souhrny/temata/u.md").read_text(encoding="utf-8") == "Text *kurz*.\n"
