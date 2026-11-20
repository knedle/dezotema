from tools.migrace.ciselniky import osoby_z_wiki, temata_z_wiki

MKDOCS = """site_name: x
markdown_extensions:
  - toc:
      slugify: !!python/object/apply:pymdownx.slugs.slugify
        kwds: {case: lower}
nav:
  - Úvod: index.md
  - Témata:
    - Větrné elektrárny: vetrniky.md
    - Konspirační teorie: konspirace.md
    - "Konspirace: Československo": konspirace-ceskoslovensko.md
    - "Konspirace: Deep State a QAnon": konspirace-deep-state-qanon.md
    - Predikce: predikce.md
  - Osoby:
    - Jindřich Rajchl: osoby/rajchl.md
"""

INDEX = """# X

| Téma | Popis |
|------|-------|
| [Větrné elektrárny](vetrniky.md) | Akcelerační zóny, kritika |
| [Konspirační teorie](konspirace.md) | Elity, okultismus |
"""


def test_temata_z_wiki():
    t = {x.slug: x for x in temata_z_wiki(MKDOCS, INDEX)}
    assert t["vetrniky"].nazev == "Větrné elektrárny"
    assert t["vetrniky"].popis == "Akcelerační zóny, kritika"
    assert t["konspirace-ceskoslovensko"].nadrazene == "konspirace"
    assert t["konspirace-deep-state-qanon"].nadrazene == "konspirace"
    assert t["konspirace-deep-state-qanon"].nazev == "Konspirace: Deep State a QAnon"
    assert t["konspirace"].nadrazene is None
    assert "predikce" not in t


def test_osoby_z_wiki(tmp_path):
    (tmp_path / "osoby").mkdir()
    (tmp_path / "osoby" / "rajchl.md").write_text(
        "# Jindřich Rajchl\n\nPředseda strany PRO.\n\n---\n", encoding="utf-8")
    (tmp_path / "osoby" / "pekova.md").write_text(
        "# Soňa Peková\n\nBioložka.\n", encoding="utf-8")
    o = {x.slug: x for x in osoby_z_wiki(tmp_path)}
    assert o["rajchl"].vlastni_stranka and o["rajchl"].sledovany
    assert "Reichl" in o["rajchl"].aliasy
    assert o["rajchl"].popis == "Předseda strany PRO."
    assert o["pekova"].vlastni_stranka and not o["pekova"].sledovany
    assert not o["turanek"].vlastni_stranka and not o["turanek"].sledovany
    assert "si-tin-pching" in o
