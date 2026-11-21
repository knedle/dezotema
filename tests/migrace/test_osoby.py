from datetime import date
from pathlib import Path

from tools.archiv.index import Archiv
from tools.archiv.model import Osoba, Vyrok, Zdroj
from tools.migrace import osoby as O

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "migrace"
KOTVA = "ladislav-vrabel--zprávy-v-devět-19-11-2026"


def _archiv():
    osoby = {"vrabel": Osoba("vrabel", "Ladislav Vrabel", ["Vrabel"], vlastni_stranka=True),
             "babis": Osoba("babis", "Andrej Babiš"), "pavel": Osoba("pavel", "Petr Pavel"),
             "rajchl": Osoba("rajchl", "Jindřich Rajchl")}
    z = Zdroj(id="2026-11-19_vrabel_zpravy", mluvci="vrabel", kanal="", titul="Zprávy v devět",
              datum=date(2026, 11, 19), url="", prepis="p")
    z.vyroky = [Vyrok("vrabel-2026-11-19-01", "tvrzeni", ["kauzy"], "Summit", "Summit proběhl v Číně."),
                Vyrok("vrabel-2026-11-19-02", "tvrzeni", ["volby-2026"], "Referendum",
                      "Babiš zakázal referendum o EU, říká Vrabel.")]
    return Archiv([z], {}, osoby), z


def test_osoby_split_and_assign():
    zm = O.parsuj_tabulku((FIX / "osoby_vrabel.md").read_text(encoding="utf-8"), "vrabel")
    assert len(zm) == 3 and zm[0].vztah == "pozitivni" and zm[1].vztah == "neutralni"
    assert zm[2].vztah == "negativni" and zm[2].datum == date(2026, 11, 19)
    assert zm[2].kotva_zdroje == KOTVA
    arch, z = _archiv()
    vys = O.prirad(zm, arch, {x.kotva_zdroje: z.id for x in zm})
    v2 = z.vyroky[1]
    assert [r.osoba for r in v2.osoby] == ["babis"]       # příjmení v textu výroku
    sl = {r.osoba for r in z.osoby}
    assert {"pavel", "rajchl", "scott-ritter", "christine-lagarde"} <= sl   # bez shody -> zdroj
    assert all(r.vztah == "negativni" for r in z.osoby if r.osoba in ("pavel", "rajchl"))
    assert "scott-ritter" in arch.osoby and arch.osoby["scott-ritter"].vlastni_stranka is False
    assert vys.nove_osoby == 2 and not vys.nezarazeno


def test_rozdel_jmena_zavorky():
    assert O.rozdel_jmena("A B, C D (role, funkce), E F") == ["A B", "C D (role, funkce)", "E F"]


def _z(mluvci, vyroky, zid="2026-11-19_x"):
    z = Zdroj(id=zid, mluvci=mluvci, kanal="", titul="t", datum=date(2026, 11, 19), url="",
              prepis="p")
    z.vyroky = vyroky
    return z


def test_prijmeni_rozlisuje_velikost_a_diakritiku():
    z = _z("vrabel", [Vyrok("v1", "tvrzeni", ["kauzy"], "N", "Prezident vůči nim jedná jako vždy.")])
    assert O.najdi_vyrok(z, "Aleksandar Vučić") is None      # „vůči“ není Vučić
    assert O.najdi_vyrok(z, "Jan Jakob") is None             # „jako“ není Jakob
    z.vyroky.append(Vyrok("v2", "tvrzeni", ["kauzy"], "N", "Vučić a Babišovi se to líbí."))
    assert O.najdi_vyrok(z, "Aleksandar Vučić").id == "v2"
    assert O.najdi_vyrok(z, "Andrej Babiš").id == "v2"       # pádová přípona „-ovi“


def test_zminka_jen_k_mluvcimu_stranky():
    osoby = {"pekova": Osoba("pekova", "Soňa Peková"), "zitko": Osoba("zitko", "Pavel Zítko"),
             "vrabel": Osoba("vrabel", "Ladislav Vrabel")}
    z = _z("zitko", [Vyrok("v1", "tvrzeni", ["kauzy"], "N", "Zítko mluví o Rajchlovi.")])
    arch = Archiv([z], {}, osoby)
    zm = [O.ZminkaRaw("Pavel Zítko", "pozitivni", "k", date(2026, 11, 19), "kot", "pekova")]
    vys = O.prirad(zm, arch, {"kot": z.id})
    assert len(vys.nezarazeno) == 1 and not z.osoby and not z.vyroky[0].osoby
    zm = [O.ZminkaRaw("Jindřich Rajchl", "negativni", "k", date(2026, 11, 19), "kot", "zitko")]
    osoby["rajchl"] = Osoba("rajchl", "Jindřich Rajchl")
    vys = O.prirad(zm, Archiv([z], {}, osoby), {"kot": z.id})
    assert not vys.nezarazeno and z.vyroky[0].osoby[0].osoba == "rajchl"
