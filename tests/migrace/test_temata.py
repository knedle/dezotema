from datetime import date
from pathlib import Path

from tools.archiv.model import Citace, Osoba, Zdroj
from tools.migrace import temata as T

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"

OSOBY = {
    "rajchl": Osoba("rajchl", "Jindřich Rajchl", ["Reichl", "Rejchl", "Jindra Rajchl"]),
    "cernohorsky": Osoba("cernohorsky", "Jiří Černohorský Živě", ["Jiří Černohorský"]),
    "vrabel": Osoba("vrabel", "Ladislav Vrabel", ["Vrabel"]),
    "tarabova": Osoba("tarabova", "Lenka Tarabová"),
    "zitko": Osoba("zitko", "Pavel Zítko (Československo TV2)", ["Československo TV2", "ČsTV2"]),
    "si-tin-pching": Osoba("si-tin-pching", "Si Ťin-pching", ["Si"]),
}


def _z(zid, mluvci, titul, d):
    return Zdroj(id=zid, mluvci=mluvci, kanal="", titul=titul, datum=d, url="",
                 prepis=f"prepisy/done/{zid}.txt")


LETNA = """# FARA a neziskovky

---

## Milion chvilek — struktura a financování

### Letná 15. 11.: „cirkus Mikuláše Mináře“, odpovědí je FARA (Rajchl, 15. 11. 2026) {#letna-cirkus-minare-rajchl-15-11-2026}

Údaj o 450 tisících účastnících Rajchl označuje za „regulérní lež“.

> „Mám jim říct, vážení přátelé…?“ — Jindřich Rajchl

Šídlo podle něj na Rajchla útočí (viz [kauzy.md](kauzy.md)).

**16. 11.** — V televizní debatě Rajchl opakuje, že vláda by na Letnou neměla reagovat.

> „Pokud bychom teď ustoupili…“ — Jindřich Rajchl

**16. 11. — Černohorský** zpochybňuje i oficiální záběry Letné z dronu.

> „Nevidím tam jedinou vlajku.“ — Jiří Černohorský

**16. 11. — Černohorský (Facebook Live)** se vysmívá přesnému údaji o 436 tisících účastnících.

**Zdroje:** [Rajchl — Letná (15. 11. 2026)](_zdroje.md#rajchl-letna-15-11), [Rajchl — Jak reagovat (16. 11. 2026)](_zdroje.md#rajchl-reagovat-16-11), [Černohorský — dron](_zdroje.md#cerno-dron-16-11), [Černohorský — FB](_zdroje.md#cerno-fb-16-11)

---
"""

MAPA = {
    "rajchl-letna-15-11": "2026-11-15_rajchl_letna",
    "rajchl-reagovat-16-11": "2026-11-16_rajchl_jak-reagovat",
    "cerno-dron-16-11": "2026-11-16_cernohorsky_450-tisic-ovecek-zabery-z-dronu",
    "cerno-fb-16-11": "2026-11-16_cernohorsky_facebook-live",
    "cerno-fara-1": "2026-03-15_rajchl_fara",
    "rajchl-fara-2": "2026-10-13_rajchl_videoportal",
}

ZDROJE = {z.id: z for z in [
    _z("2026-11-15_rajchl_letna", "rajchl", "Nedělní vysílání: Letná", date(2026, 11, 15)),
    _z("2026-11-16_rajchl_jak-reagovat", "rajchl", "Jak by měla vláda reagovat na Letnou?",
       date(2026, 11, 16)),
    _z("2026-11-16_cernohorsky_450-tisic-ovecek-zabery-z-dronu", "cernohorsky",
       "450 tisíc oveček — záběry z dronu", date(2026, 11, 16)),
    _z("2026-11-16_cernohorsky_facebook-live", "cernohorsky", "Facebook Live 16. 11. 2026",
       date(2026, 11, 16)),
    _z("2026-03-15_rajchl_fara", "rajchl", "FARA, DSA, Dozimetr", date(2026, 3, 15)),
    _z("2026-10-13_rajchl_videoportal", "rajchl", "Videoportál: FARA", date(2026, 10, 13)),
]}


def test_split_dated_paragraphs():
    js = T.parsuj_stranku(LETNA, "fara-neziskovky", OSOBY)
    assert len(js) == 4
    assert [j.mluvci for j in js] == ["rajchl", "rajchl", "cernohorsky", "cernohorsky"]
    assert [j.datum for j in js] == [date(2026, 11, 15)] + [date(2026, 11, 16)] * 3
    assert all(j.tema == "fara-neziskovky" for j in js)
    assert js[0].kapitola == "Milion chvilek — struktura a financování"
    assert js[0].explicitni_kotva == "letna-cirkus-minare-rajchl-15-11-2026"
    assert js[0].nadpis.endswith("(Rajchl, 15. 11. 2026)")
    assert "{#" not in js[0].nadpis
    # citace patří k předchozí jednotce; zbytek úvodní části zůstává v textu
    assert js[0].citace == [Citace("Mám jim říct, vážení přátelé…?")]
    assert "Šídlo podle něj" in js[0].text and "[kauzy.md](kauzy.md)" in js[0].text
    assert js[1].citace == [Citace("Pokud bychom teď ustoupili…")]
    assert js[1].text.startswith("**16. 11.** — V televizní debatě")
    assert js[2].citace == [Citace("Nevidím tam jedinou vlajku.")]
    assert "**Zdroje:**" not in js[3].text and "---" not in js[3].text
    for j in js:
        assert j.kotvy_zdroju == ["rajchl-letna-15-11", "rajchl-reagovat-16-11",
                                  "cerno-dron-16-11", "cerno-fb-16-11"]


def test_assign_by_date_and_speaker():
    js = T.parsuj_stranku(LETNA, "fara-neziskovky", OSOBY)
    prirazene, neprirazene = T.prirad(js, MAPA, ZDROJE)
    assert neprirazene == []
    ids = [zid for _, zid in prirazene]
    assert ids == ["2026-11-15_rajchl_letna", "2026-11-16_rajchl_jak-reagovat",
                   "2026-11-16_cernohorsky_450-tisic-ovecek-zabery-z-dronu",
                   "2026-11-16_cernohorsky_facebook-live"]


def test_unassigned_goes_out():
    md = LETNA.replace("**16. 11. — Černohorský (Facebook Live)**",
                       "**20. 11. — Černohorský (Facebook Live)**")
    js = T.parsuj_stranku(md, "fara-neziskovky", OSOBY)
    prirazene, neprirazene = T.prirad(js, MAPA, ZDROJE)
    assert len(prirazene) == 3
    assert len(neprirazene) == 1
    assert neprirazene[0].datum == date(2026, 11, 20)
    assert neprirazene[0].mluvci == "cernohorsky"


MULTI = """## Zákon FARA

### Obsah a záměr návrhu

Jindřich Rajchl se prohlašuje za autora návrhu českého zákona FARA.

> „Jediné, co chceme…“ — Jindřich Rajchl, [FARA](_zdroje.md#cerno-fara-1)

**Zdroje:** [Rajchl — Videoportál (13. 10. 2026)](_zdroje.md#rajchl-fara-2), [Rajchl — FARA, 2026-03-15](_zdroje.md#cerno-fara-1)

---
"""


def test_multi_source_without_dated_paragraphs():
    js = T.parsuj_stranku(MULTI, "fara-neziskovky", OSOBY)
    assert len(js) == 1 and js[0].datum is None and js[0].mluvci == "rajchl"
    assert js[0].citace == [Citace("Jediné, co chceme…")]
    prirazene, neprirazene = T.prirad(js, MAPA, ZDROJE)
    assert neprirazene == []
    (j, zid), = prirazene
    assert zid == "2026-03-15_rajchl_fara"          # nejstarší
    assert j.dalsi_zdroje == ["2026-10-13_rajchl_videoportal"]
    v = T.na_vyrok(j, ZDROJE[zid], 1)
    assert v.id == "rajchl-2026-03-15-01"
    assert v.typ == "tvrzeni" and v.temata == ["fara-neziskovky"]
    assert v.podtema == "Zákon FARA"
    assert v.dalsi_zdroje == ["2026-10-13_rajchl_videoportal"]
    assert v.mluvci is None


def test_guest_speaker_sets_vyrok_mluvci():
    js = T.parsuj_stranku(LETNA, "fara-neziskovky", OSOBY)
    prirazene, _ = T.prirad(js, MAPA, ZDROJE)
    j, zid = prirazene[2]
    # zdroj Černohorského -> mluvčí shodný se zdrojem, nepřepisuje se
    assert T.na_vyrok(j, ZDROJE[zid], 3).mluvci is None
    host = _z("2026-11-16_rajchl_jak-reagovat", "rajchl", "x", date(2026, 11, 16))
    v = T.na_vyrok(j, host, 2)
    assert v.mluvci == "cernohorsky" and v.id == "cernohorsky-2026-11-16-02"


def test_no_duplicate_vyroky():
    js1 = T.parsuj_stranku(MULTI, "fara-neziskovky", OSOBY)
    js2 = T.parsuj_stranku(MULTI, "politicky-system", OSOBY)
    p1, _ = T.prirad(js1, MAPA, ZDROJE)
    p2, _ = T.prirad(js2, MAPA, ZDROJE)
    vysledek = T.sestav_vyroky(p1 + p2, ZDROJE)
    vyroky = [v for vs in vysledek.vyroky.values() for v in vs]
    assert len(vyroky) == 1
    assert vyroky[0].temata == ["fara-neziskovky", "politicky-system"]
    assert vysledek.slouceno == 1


def test_quotes_extracted():
    md = """## Kapitola

### Něco o válce (Vrabel, 19. 11. 2026)

Vrabel tvrdí, že je to nový světový pořádek.

> „X“ — Ladislav Vrabel

> „Y“ — Vladimír Putin (citováno Vrabelem)

**Zdroje:** [Vrabel](_zdroje.md#vrabel-19-11)
"""
    j, = T.parsuj_stranku(md, "valka-nato-rusko", OSOBY)
    assert j.citace == [Citace("X")]
    assert "„X“" not in j.text
    # cizí / komentovaná atribuce zůstává doslova v textu (neztrácí se informace)
    assert "> „Y“ — Vladimír Putin (citováno Vrabelem)" in j.text
    assert j.text.startswith("Vrabel tvrdí")


def test_vetrniky_fixture():
    md = (FIX / "vetrniky_1-92.md").read_text(encoding="utf-8")
    js = T.parsuj_stranku(md, "vetrniky", OSOBY)
    assert len(js) == 7
    assert [j.mluvci for j in js] == ["rajchl", "tarabova", "rajchl", "vrabel", "cernohorsky",
                                      "cernohorsky", "cernohorsky"]
    assert js[2].citace[0].text == "Ideologie vás vždycky stojí peníze. Vždycky."
    assert len(js[2].citace) == 1   # druhá citace má komentovanou atribuci -> v textu
    assert js[5].datum is None and js[6].datum is None and js[6].den_mesic == (17, 8)
    assert js[4].datum == date(2026, 8, 23)
    mapa = {
        "jiří-černohorský--fb-live-10-5-2026": "2026-05-10_cernohorsky_fb-live-10-5-2026",
        "jiří-černohorský--fb-live-13-5-2026": "2026-05-13_cernohorsky_fb-live-13-5-2026",
        "jiří-černohorský--facebook-live-17-8-2026-2": "2026-08-17_cernohorsky_facebook-live-2",
    }
    zdroje = {z.id: z for z in [
        _z("2026-05-10_cernohorsky_fb-live-10-5-2026", "cernohorsky", "FB Live 10. 5. 2026",
           date(2026, 5, 10)),
        _z("2026-05-13_cernohorsky_fb-live-13-5-2026", "cernohorsky", "FB Live 13. 5. 2026",
           date(2026, 5, 13)),
        _z("2026-08-17_cernohorsky_facebook-live-2", "cernohorsky", "Facebook Live 17. 8. 2026",
           date(2026, 8, 17)),
    ]}
    prirazene, neprirazene = T.prirad(js[5:], mapa, zdroje)
    assert neprirazene == []
    assert [z for _, z in prirazene] == ["2026-05-10_cernohorsky_fb-live-10-5-2026",
                                         "2026-08-17_cernohorsky_facebook-live-2"]
    assert prirazene[0][0].dalsi_zdroje == ["2026-05-13_cernohorsky_fb-live-13-5-2026"]
    assert prirazene[1][0].datum == date(2026, 8, 17)


def test_h2_section_with_sources_is_unit():
    md = """## Fauci se odvolal na 5. dodatek (Vrabel, 30. 7. 2026)

Anthony Fauci byl předvolán.

**Zdroje:** [Vrabel](_zdroje.md#v)

**1. 8.** — Zítko doplňuje detaily.

**Zdroje:** [ČsTV2](_zdroje.md#z)
"""
    js = T.parsuj_stranku(md, "covid-vakciny", OSOBY)
    assert len(js) == 2
    assert js[0].kapitola is None and js[0].nadpis.startswith("Fauci")
    assert js[1].mluvci == "zitko" and js[1].datum == date(2026, 8, 1)
    assert js[0].kotvy_zdroju == ["v", "z"]


def test_stare_kotvy():
    from tools.archiv.slug import slugify
    js = T.parsuj_stranku(LETNA, "fara-neziskovky", OSOBY)
    # explicitní kotva i slug z textu nadpisu; všechny jednotky sekce sdílejí index sekce
    assert js[0].sekce_kotvy == ["letna-cirkus-minare-rajchl-15-11-2026", slugify(js[0].nadpis)]
    assert len({j.sekce for j in js}) == 1


def test_kotvy_dedupe_like_mkdocs():
    md = "# A\n\n## Kap\n\n### Stejné\n\nx\n\n**Zdroje:** [a](_zdroje.md#a)\n\n" \
         "### Stejné\n\ny\n\n**Zdroje:** [a](_zdroje.md#a)\n"
    js = T.parsuj_stranku(md, "kauzy", OSOBY)
    assert js[0].sekce_kotvy == ["stejné"] or js[0].sekce_kotvy == [slugify_("Stejné")]
    assert js[1].sekce_kotvy == [js[0].sekce_kotvy[0] + "_1"]


def slugify_(t):
    from tools.archiv.slug import slugify
    return slugify(t)


def test_guest_from_text_when_heading_speaker_not_in_sources():
    md = """## Kauza

### Rajchl slíbil pomoc s dopisem — a nesplnil

Peková na akci uvádí, že se spoléhala na Jindřicha Rajchla.

**Zdroje:** [Zítko](_zdroje.md#z1)
"""
    osoby = dict(OSOBY, pekova=Osoba("pekova", "Soňa Peková"))
    j, = T.parsuj_stranku(md, "kauzy", osoby)
    assert j.mluvci is None            # „Rajchl slíbil…“ není jen jméno -> není mluvčí
    assert j.mluvci_textu == "pekova"
    zdroje = {"z": _z("z", "zitko", "Soběšovice", date(2026, 3, 29))}
    (j2, zid), = T.prirad([j], {"z1": "z"}, zdroje)[0]
    assert zid == "z"


def test_heading_speaker_missing_in_sources_uses_text_speaker():
    md = """## K

### Vzorky vakcín bez zájmu úřadů — Rajchl

Peková tvrdí, že vzorky nikoho nezajímají.

**Zdroje:** [Zítko](_zdroje.md#z1)
"""
    osoby = dict(OSOBY, pekova=Osoba("pekova", "Soňa Peková"))
    j, = T.parsuj_stranku(md, "covid-vakciny", osoby)
    assert j.mluvci == "rajchl"
    zdroje = {"z": _z("z", "zitko", "Soběšovice", date(2026, 3, 29))}
    (j2, zid), = T.prirad([j], {"z1": "z"}, zdroje)[0]
    assert zid == "z" and j2.mluvci == "pekova" and j2.zpusob == "uvod-jiny-mluvci"


def test_dated_paragraph_name_only_at_start():
    md = """## K

### Kauza Vlasákové (Černohorský, 24. 9. 2026)

Úvod.

**5. 10.** — Spolek Čest Svoboda Respekt podle Černohorského sehnal advokáta.

**6. 10.** — Zítko doplňuje.

**Zdroje:** [a](_zdroje.md#a)
"""
    osoby = dict(OSOBY, svoboda=Osoba("svoboda", "Jakub Svoboda"))
    js = T.parsuj_stranku(md, "rodina-deti", osoby)
    assert [j.mluvci for j in js] == ["cernohorsky", "cernohorsky", "zitko"]


def test_restart_cesko_alias_is_not_surname():
    osoby = dict(OSOBY, sejna=Osoba("sejna", "Adam Šejna", ["Restart Česko"]))
    md = """## K

### „Česko je plán" — záměrná eroze národní identity

Jiří Černohorský tvrdí, že označení „Česko“ je plán.

**Zdroje:** [a](_zdroje.md#a)
"""
    j, = T.parsuj_stranku(md, "konspirace", osoby)
    assert j.mluvci is None and j.mluvci_textu == "cernohorsky"


def test_unassigned_duplicate_heading_joins_existing_vyrok():
    a = T.parsuj_stranku(MULTI, "fara-neziskovky", OSOBY)
    b = T.parsuj_stranku(MULTI.split("**Zdroje:**")[0]
                         .replace(", [FARA](_zdroje.md#cerno-fara-1)", ""), "kauzy", OSOBY)
    p, _ = T.prirad(a, MAPA, ZDROJE)
    _, n = T.prirad(b, MAPA, ZDROJE)
    assert len(n) == 1
    s = T.sestav_vyroky(p, ZDROJE)
    zbytek = T.pripoj_neprirazene(n, s)
    assert zbytek == []
    v, = [v for vs in s.vyroky.values() for v in vs]
    assert v.temata == ["fara-neziskovky", "kauzy"]


PRESUNUTE = """## Ceny

### Pekarová: plat 394 tisíc (Černohorský)

Černohorský se vrací k platům politiků.

---

### Odklad valorizace důchodů (Vrabel, 15. 7. 2026)

Vrabel to sarkasticky srovnává s chlebíčky.

**Zdroje:** [Vrabel](_zdroje.md#vrabel-15-7)

**Zdroje:** [Černohorský — Brno](_zdroje.md#cerno-6-4)

---
"""

ZDROJE_FIX = {z.id: z for z in [
    _z("v157", "vrabel", "Facebook Live 15. 7. 2026", date(2026, 7, 15)),
    _z("c64", "cernohorsky", "Brno a Landsmannschaft", date(2026, 4, 6)),
    _z("v315", "vrabel", "Nedělní vysílání", date(2026, 5, 31)),
    _z("r315", "rajchl", "Facebook Live 31. 5. 2026", date(2026, 5, 31)),
    _z("z167", "zitko", "Videoportál 16. 7. 2026", date(2026, 7, 16)),
]}
MAPA_FIX = {"vrabel-15-7": "v157", "cerno-6-4": "c64", "v-31-5": "v315", "r-31-5": "r315"}


def test_misplaced_sources_line_moves_to_previous_section():
    js = T.parsuj_stranku(PRESUNUTE, "politicky-system", OSOBY)
    assert js[1].zdroje_radky == [["vrabel-15-7"], ["cerno-6-4"]]
    p, n = T.prirad(js, MAPA_FIX, ZDROJE_FIX)
    assert n == []
    assert [(j.nadpis[:8], z) for j, z in p] == [("Pekarová", "c64"), ("Odklad v", "v157")]
    assert all(j.dalsi_zdroje == [] for j, _ in p)
    assert p[0][0].zpusob == "presunuty-radek-zdroju"


ODSTAVEC = """## K

### Kryptoměny: sledování státem (Vrabel, 31. 5. 2026)

Vrabel tvrdí, že stát sleduje kryptoměny.

Kvantové počítače podle něj prolomí šifry.

Rajchl ve svém vysílání doplňuje, že EU chystá registr peněženek.

**Zdroje:** [Vrabel](_zdroje.md#v-31-5), [Rajchl](_zdroje.md#r-31-5)
"""


def test_paragraph_of_other_speaker_split_into_own_unit():
    js = T.parsuj_stranku(ODSTAVEC, "digitalni-kontrola", OSOBY)
    assert js[0].odstavce_mluvci == ["vrabel", None, "rajchl"]
    p, n = T.prirad(js, MAPA_FIX, ZDROJE_FIX)
    assert n == []
    (j1, z1), (j2, z2) = p
    assert z1 == "v315" and j1.dalsi_zdroje == []
    assert "Rajchl" not in j1.text and j1.text.endswith("prolomí šifry.")
    assert z2 == "r315" and j2.mluvci == "rajchl" and not j2.uvod
    assert j2.text.startswith("Rajchl ve svém vysílání") and j2.nadpis == j1.nadpis
    assert j2.zpusob == "odstavec-jineho-mluvciho"
    s = T.sestav_vyroky(p, ZDROJE_FIX)
    assert [v.id for vs in s.vyroky.values() for v in vs] == ["vrabel-2026-05-31-01",
                                                              "rajchl-2026-05-31-01"]


def test_parent_heading_fallback_for_section_without_sources():
    md = """## „Pfizergate" a rod von der Leyenových (Zítko, 16. 7. 2026)

Úvod kapitoly.

**Zdroje:** [Zítko](_zdroje.md#z-16-7)

### SMS-ky s Bourlou a objednávka 10 vakcín

Narativ o SMS zprávách.
"""
    js = T.parsuj_stranku(md, "covid-vakciny", OSOBY)
    sms = js[-1]
    assert sms.kapitola_datum == date(2026, 7, 16) and sms.kapitola_mluvci == "zitko"
    p, n = T.prirad([sms], {}, ZDROJE_FIX)
    assert n == [] and p[0][1] == "z167" and p[0][0].zpusob == "kapitola"


def test_unassigned_duplicate_with_different_text_stays_for_review():
    a = T.parsuj_stranku(MULTI, "fara-neziskovky", OSOBY)
    b = T.parsuj_stranku(MULTI.split("**Zdroje:**")[0].replace("autora", "jediného autora")
                         .replace(", [FARA](_zdroje.md#cerno-fara-1)", ""), "kauzy", OSOBY)
    p, _ = T.prirad(a, MAPA, ZDROJE)
    _, n = T.prirad(b, MAPA, ZDROJE)
    s = T.sestav_vyroky(p, ZDROJE)
    zbytek = T.pripoj_neprirazene(n, s)
    assert len(zbytek) == 1 and "odlišným textem" in zbytek[0].duvod
    assert zbytek[0].vyrok_id == "rajchl-2026-03-15-01"
