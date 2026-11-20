import os
import shutil
from pathlib import Path

from tools.archiv import hook

FIX = Path(__file__).parent / "fixtures" / "data_gen"
NAV = [{"Úvod": "index.md"}, {"Ruční": "x.md"}]


def _cfg(tmp_path, data=True):
    root = tmp_path / "repo"
    if data:
        shutil.copytree(FIX, root)
    else:
        (root / "wiki").mkdir(parents=True)
    return root, {"docs_dir": str(root / "wiki"), "nav": list(NAV)}


def test_hook_noop_without_data(tmp_path):
    root, cfg = _cfg(tmp_path, data=False)
    hook.on_config(cfg)
    assert cfg["nav"] == NAV
    assert [p.name for p in (root / "wiki").iterdir()] == []
    assert not (root / ".cache").exists()


def test_hook_noop_when_zdroje_exists(tmp_path):
    root, cfg = _cfg(tmp_path)
    (root / "wiki" / "_zdroje.md").write_text("# staré", encoding="utf-8")
    hook.on_config(cfg)
    assert cfg["nav"] == NAV
    assert not (root / "wiki" / "temata").exists()
    assert not (root / ".cache").exists()


def test_hook_generates_and_sets_nav(tmp_path):
    root, cfg = _cfg(tmp_path)
    hook.on_config(cfg)
    assert cfg["nav"][0] == {"Úvod": "index.md"}
    assert (root / "wiki" / "temata" / "vetrniky.md").is_file()
    assert (root / ".cache" / "archiv.hash").is_file()


def test_hook_skips_when_unchanged(tmp_path):
    root, cfg = _cfg(tmp_path)
    hook.on_config(cfg)
    p = root / "wiki" / "temata" / "vetrniky.md"
    os.utime(p, (1_000_000, 1_000_000))
    cfg2 = {"docs_dir": cfg["docs_dir"], "nav": list(NAV)}
    hook.on_config(cfg2)
    assert p.stat().st_mtime == 1_000_000
    assert cfg2["nav"][0] == {"Úvod": "index.md"}


def test_hook_regenerates_on_change_or_missing_output(tmp_path):
    root, cfg = _cfg(tmp_path)
    hook.on_config(cfg)
    shutil.rmtree(root / "wiki" / "temata")
    hook.on_config(cfg)
    assert (root / "wiki" / "temata" / "vetrniky.md").is_file()
    t = root / "data" / "temata.yaml"
    t.write_text(t.read_text(encoding="utf-8") + "\n# změna\n", encoding="utf-8")
    p = root / "wiki" / "temata" / "vetrniky.md"
    os.utime(p, (1_000_000, 1_000_000))
    hook.on_config(cfg)
    assert p.stat().st_mtime != 1_000_000
