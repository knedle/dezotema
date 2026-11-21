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
