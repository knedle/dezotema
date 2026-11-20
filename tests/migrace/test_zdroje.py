from datetime import date

from tools.archiv.model import Osoba
from tools.migrace.zdroje import (mapa_kotev, na_zdroj, parsuj_zdroje,
                                  unikatni_ids)

MD = """﻿# Zdroje

## Ladislav Vrabel — Zprávy v devět (14. 11. 2026) {#ladislav-vrabel--zprávy-v-devět-14-11-2026}
- **Soubor:** [přepis](prepisy/done/2026-11-14_Ladislav-Vrabel_Zpravy.txt)
- **Kanál:** Ladislav Vrabel (Facebook Live)
- **URL:** <https://example.org/v1>
- **Datum záznamu:** 2026-11-14
- **Délka:** 59:24 | Zhlédnutí: ~199 800
- **Poznámka:** Něco důležitého.
- **Zpracováno:** ano

## Jindřich Rajchl — FARA, DSA, Dozimetr
- **Soubor:** [přepis](prepisy/done/2026-03-15_Jindřich-Rajchl_FARA.txt)
- **Kanál:** Jindřich Rajchl (Facebook Live)
- **URL:** <https://example.org/v2>
- **Datum záznamu:** 2026-03-15
- **Zpracováno:** ano

## Československo TV2 — Souhrn týdne
- **Soubor:** [přepis](prepisy/done/2026-11-15_Československo-TV2_Souhrn.txt)
- **Kanál:** Československo TV2 / Pavel Zítko (Facebook)
- **URL:** <https://example.org/v3>
- **Datum záznamu:** 2026-11-14, 23:11 (soubor datován 15. 11., podle data stažení)
- **Zpracováno:** ano
"""

OSOBY = {
    "vrabel": Osoba("vrabel", "Ladislav Vrabel"),
    "rajchl": Osoba("rajchl", "Jindřich Rajchl"),
    "zitko": Osoba("zitko", "Pavel Zítko (Československo TV2)"),
}


def test_parse_explicit_and_slug_anchor():
    raws = parsuj_zdroje(MD)
    assert len(raws) == 3
    assert raws[0].kotva == "ladislav-vrabel--zprávy-v-devět-14-11-2026"
    assert raws[0].nadpis == "Ladislav Vrabel — Zprávy v devět (14. 11. 2026)"
    assert raws[1].kotva == "jindřich-rajchl--fara-dsa-dozimetr"
    assert raws[1].pole["URL"] == "<https://example.org/v2>"


def test_na_zdroj_cstv2():
    z = na_zdroj(parsuj_zdroje(MD)[2], OSOBY)
    assert z.datum == date(2026, 11, 14)
    assert z.cas == "23:11"
    assert z.mluvci == "zitko"
    assert z.prepis == "prepisy/done/2026-11-15_Československo-TV2_Souhrn.txt"
    assert z.url == "https://example.org/v3"
    assert z.titul == "Souhrn týdne"
    assert z.id == "2026-11-14_zitko_souhrn-tydne"


def test_na_zdroj_vrabel_poznamka():
    z = na_zdroj(parsuj_zdroje(MD)[0], OSOBY)
    assert z.rezim == "vrabel"
    assert z.delka == "59:24"
    assert "Něco důležitého." in z.poznamka and "Zhlédnutí: ~199 800" in z.poznamka
    assert z.cas is None


def test_unique_ids():
    raws = parsuj_zdroje(MD)
    zdroje = [na_zdroj(r, OSOBY) for r in raws]
    assert len({z.id for z in zdroje}) == 3
    dup = [na_zdroj(raws[1], OSOBY) for _ in range(3)]
    unikatni_ids(dup)
    ids = [z.id for z in dup]
    assert ids[1] == ids[0] + "-2" and ids[2] == ids[0] + "-3"


def test_mapa_kotev():
    raws = parsuj_zdroje(MD)
    zdroje = [na_zdroj(r, OSOBY) for r in raws]
    m = mapa_kotev(raws, zdroje)
    assert m["jindřich-rajchl--fara-dsa-dozimetr"] == zdroje[1].id
    assert len(m) == 3


def test_soubor_s_poznamkou_v_zavorce():
    raw = parsuj_zdroje(MD)[1]
    raw.pole["Soubor"] = "[přepis](prepisy/done/a.txt) (duplikát: [přepis _1](prepisy/done/a_1.txt), <https://x>)"
    z = na_zdroj(raw, OSOBY)
    assert z.prepis == "prepisy/done/a.txt"
    assert "a_1.txt" in z.poznamka


def test_preskoceno_ma_prioritu_a_zpracovano_se_zachova():
    raw = parsuj_zdroje(MD)[0]  # vrabel
    raw.pole["Zpracováno"] = "přeskočeno"
    z = na_zdroj(raw, OSOBY)
    assert z.rezim == "preskoceno" and "Zpracováno: přeskočeno" in z.poznamka
    raw.pole["Zpracováno"] = "ano (částečně — viz poznámka)"
    z = na_zdroj(raw, OSOBY)
    assert z.rezim == "vrabel" and "Zpracováno: ano (částečně" in z.poznamka
    raw.pole["Zpracováno"] = "ano"
    assert "Zpracováno" not in na_zdroj(raw, OSOBY).poznamka
