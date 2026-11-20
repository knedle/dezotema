import shutil
from datetime import date
from pathlib import Path

import yaml

from tools.archiv.validate import main, validuj

FIX = Path(__file__).parent / "fixtures" / "data_min"
ZDROJ = "data/zdroje/2026/11/2026-11-19_vrabel_test.yaml"


def test_validate_ok():
    assert validuj(FIX) == []


def test_nezarazeno_is_not_a_source(tmp_path):
    """data/zdroje/_nezarazeno.yaml (migrace) není zdroj: validace ani načítání ho neberou."""
    from tools.archiv.io import nacti_vse
    root = tmp_path / "r"
    shutil.copytree(FIX, root)
    (root / "data" / "zdroje" / "_nezarazeno.yaml").write_text(
        "jednotky:\n- tema: kauzy\n  nadpis: n\n  text: t\n  kotvy_zdroju: []\n", encoding="utf-8")
    assert validuj(root) == []
    assert all(z.id != "_nezarazeno" for z in nacti_vse(root)[0])


def test_validate_errors(tmp_path):
    root = tmp_path / "r"
    shutil.copytree(FIX, root)
    p = root / ZDROJ
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    v = d["vyroky"]
    v[1]["id"] = v[0]["id"]            # duplicita
    v[0]["temata"] = ["nic"]           # neznámé téma
    v[0]["mluvci"] = "kdosi"           # neznámý mluvčí
    v[2]["typ"] = "blabol"             # neplatný typ
    v.append({"id": "vrabel-2026-11-19-04", "typ": "predikce", "temata": ["volby-2026"],
              "nadpis": "n", "text": "t"})   # chybí blok predikce
    v.append({"id": "vrabel-2026-11-19-05", "typ": "stoch-teror", "temata": ["volby-2026"],
              "nadpis": "n", "text": "t"})   # chybí teror
    d["zdroj"]["prepis"] = "prepisy/done/neni.txt"
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    err = validuj(root)
    joined = "\n".join(err)
    for needle in ["duplicit", "neznámé téma 'nic'", "neznámý mluvčí 'kdosi'",
                   "neplatný typ 'blabol'", "vrabel-2026-11-19-04: typ predikce",
                   "vrabel-2026-11-19-05: typ stoch-teror",
                   "2026-11-19_vrabel_test: přepis neexistuje"]:
        assert needle in joined, needle
    assert all("vrabel-2026-11-19" in e or "2026-11-19_vrabel_test" in e for e in err)


def _kopie(tmp_path, uprav):
    root = tmp_path / "r"
    shutil.copytree(FIX, root)
    p = root / ZDROJ
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    uprav(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    return root


def _chyby(tmp_path, uprav):
    return "\n".join(validuj(_kopie(tmp_path, uprav)))


def test_validate_reference_branches(tmp_path):
    def uprav(d):
        v = d["vyroky"]
        v[1]["osoby"] = [{"osoba": "nikdo", "vztah": "zvlastni"}]
        v[1]["vazby"] = [{"na": "neni-id", "typ": "divny"}]
        v[1]["dalsi_zdroje"] = ["neni-zdroj"]
        v[1]["predikce"]["stav"] = "hmm"
        d["zdroj"]["rezim"] = "jiny"
        d["zdroj"]["prehled"] = [{"tema": "t", "text": "x", "vyrok": "neni-vyrok"}]
    e = _chyby(tmp_path, uprav)
    for needle in ["vrabel-2026-11-19-02: neznámá osoba 'nikdo'",
                   "vrabel-2026-11-19-02: neplatný vztah 'zvlastni'",
                   "vazba na neexistující výrok 'neni-id'",
                   "neplatný typ vazby 'divny'",
                   "neexistující zdroj 'neni-zdroj'",
                   "neplatný stav predikce 'hmm'",
                   "2026-11-19_vrabel_test: neplatný režim 'jiny'",
                   "neexistující výrok 'neni-vyrok'"]:
        assert needle in e, needle


def test_malformed_files_reported_with_path(tmp_path):
    root = _kopie(tmp_path, lambda d: d["vyroky"][0].pop("nadpis"))
    assert any(ZDROJ in x and "nadpis" in x for x in validuj(root))
    root = _kopie(tmp_path / "b", lambda d: d["vyroky"][0].update(preklep="x"))
    assert any(ZDROJ in x for x in validuj(root))
    root = _kopie(tmp_path / "c", lambda d: d.pop("zdroj"))
    assert any(ZDROJ in x for x in validuj(root))
    root = _kopie(tmp_path / "d", lambda d: d["vyroky"][0].update(temata=None, citace=None))
    assert any("vrabel-2026-11-19-01" in x for x in validuj(root))
    (root / "data" / "temata.yaml").unlink()
    assert any("temata.yaml" in x for x in validuj(root))


def test_source_id_and_dir_checks(tmp_path):
    e = _chyby(tmp_path, lambda d: d["zdroj"].update(id="jine-id"))
    assert "id zdroje 'jine-id' neodpovídá" in e
    e = _chyby(tmp_path / "b", lambda d: d["zdroj"].update(datum=date(2026, 10, 1)))
    assert "adresář neodpovídá datu" in e
    root = _kopie(tmp_path / "c", lambda d: None)
    kopie = root / "data" / "zdroje" / "2026" / "11" / "2026-11-19_vrabel_test2.yaml"
    kopie.write_text((root / ZDROJ).read_text(encoding="utf-8"), encoding="utf-8")
    assert "duplicitní id zdroje" in "\n".join(validuj(root))


def test_cli_exit_codes(tmp_path, capsys):
    assert main([str(FIX)]) == 0
    root = _kopie(tmp_path, lambda d: d["vyroky"][0].update(temata=["nic"]))
    assert main([str(root)]) == 1
    assert "nic" in capsys.readouterr().out


def test_datum_and_null_dalsi_zdroje(tmp_path):
    e = _chyby(tmp_path, lambda d: d["zdroj"].update(datum="nejaky text"))
    assert "datum není platné datum" in e and ZDROJ in e
    # citované ISO datum se akceptuje
    assert _chyby(tmp_path / "b", lambda d: d["zdroj"].update(datum="2026-11-19")) == ""
    assert _chyby(tmp_path / "c", lambda d: d["vyroky"][0].update(dalsi_zdroje=None)) == ""
