from tools.archiv.slug import ascii_slug, slugify


def test_slug_matches_mkdocs():
    assert slugify("Ladislav Vrabel — Zprávy v devět 19. 11. 2026") == "ladislav-vrabel--zprávy-v-devět-19-11-2026"
    assert slugify("Jaroslav Turánek — Přednáška VTE/FVE (seminář, sdíleno 14. 6. 2026)") == "jaroslav-turánek--přednáška-vtefve-seminář-sdíleno-14-6-2026"


def test_ascii_slug():
    assert ascii_slug("Ladislav Vrabel") == "ladislav-vrabel"
    assert ascii_slug("Zprávy v devět") == "zpravy-v-devet"
