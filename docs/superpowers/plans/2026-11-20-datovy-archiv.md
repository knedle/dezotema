# Datový archiv výroků — prováděcí plán

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Cíl:** Nahradit ručně psané MD stránky wiki strukturovanými daty výroků (YAML, jeden soubor na zpracovaný zdroj). Všechny stránky se z dat generují při buildu a dosavadní obsah se do dat převede.

**Architektura:** Balík `tools/archiv/` načítá, validuje a renderuje data z `data/`. Kódem z `tools/archiv/hook.py` ho MkDocs volá v `on_config`: hook zapíše generované MD do `wiki/` a dosadí navigaci. Převod je jednorázová sada skriptů v `tools/migrace/`, které parsují dnešní `wiki/*.md` a zapisují `data/`. Nepřiřaditelné zbytky dočistí agenti.

**Technologie:** Python 3.13, PyYAML 6, pytest 9, MkDocs 1.6 + Material 9.7 (hooks), bez dalších závislostí.

**Specifikace:** `docs/superpowers/specs/2026-11-20-datovy-archiv-design.md`

## Globální omezení

- Data: `data/zdroje/YYYY/MM/<id>.yaml`, `data/temata.yaml`, `data/osoby.yaml`, `data/souhrny/{temata,osoby}/<slug>.md`.
- Id zdroje = název datového souboru bez `.yaml` = `<datum>_<mluvci-slug>_<slug-titulu>` (ASCII, malá písmena, `-`). Id výroku = `<mluvci>-<YYYY-MM-DD>-<NN>` (NN dvoumístné, unikátní napříč archivem; kolize se řeší sufixem `b`, `c`).
- `typ` ∈ {`tvrzeni`, `postoj`, `predikce`, `stoch-teror`}. `vztah` ∈ {`pozitivni`, `negativni`, `rozporuplny`, `neutralni`} (zobrazení ✅ ❌ ⚖️ ○). `vazby.typ` ∈ {`posun`, `opakovani`, `konflikt`, `souhlas`}. `predikce.stav` ∈ {`ceka`, `potvrzeno`, `vyvraceno`, `castecne`} (🕐 ✅ ❌ ⚠️). `rezim` ∈ {`standard`, `vrabel`, `preskoceno`}.
- Slugy témat = dnešní názvy souborů bez `.md` (`vetrniky`, `politicky-system`, …). Slugy mluvčích = dnešní `wiki/osoby/<slug>.md`.
- Kotva výroku = jeho `id`. Kotva zdroje na stránce zdrojů = id zdroje.
- Generované cesty (do `.gitignore`): `wiki/temata/`, `wiki/osoby/`, `wiki/zminene/`, `wiki/predikce/`, `wiki/zdroje/`, `wiki/zpravodajstvi-vrabel/`, `wiki/stochasticky-teror.md`, `wiki/data/vyroky.json`. Ručně psané zůstávají: `wiki/index.md`, `wiki/o-strance.md`, `wiki/extra/`, `wiki/css/`, `wiki/js/`, `wiki/prepisy/`.
- Práh členění stránky: 150 výroků → podstránky po rocích.
- Texty se při převodu přenášejí doslova (nadpis, text, citace, odkazy). Nic se nezahazuje: nepřiřaditelné jde do `data/zdroje/_nezarazeno.yaml`.
- Neutrální tón a obsahová pravidla z CLAUDE.md beze změny. Výstup je česky.
- Commit po každém tasku. Push až na konci (pokyn uživatele). Převod běží nad zmrazeným stavem, nová videa se do přepnutí nezpracovávají.
- Celé texty v YAML se zapisují blokovým stylem `|` a s `allow_unicode=True`, aby se dal soubor číst a diffovat.

## Na co se při kontrole zaměřit

1. **Kotvy `_zdroje.md` bez explicitního `{#…}`** (~150 sekcí): odkazy na ně používají slug, který generuje MkDocs (`pymdownx.slugs.slugify(case='lower')`, em dash dává `--`, diakritika zůstává). Parser musí počítat stejný slug, jinak zůstanou tisíce výroků nepřiřazené. Test: `test_slug_matches_mkdocs`.
2. **Datované odstavce bez mluvčího a s mluvčím** (`**16. 11.** —`, `**14. 11. — Černohorský**`, `**14. 11. (23:11)** —`, `**16. 11. — Černohorský (Facebook Live)**`): každý je samostatný výrok s datem a mluvčím (bez mluvčího přebírá mluvčího sekce). Test: `test_split_dated_paragraphs`.
3. **Duplicitní zdroj na více stránkách:** stejný výrok (nadpis + zdroj) je dnes zapsán v tématu i v osobě. Převod nesmí vytvořit dva výroky. Stránky osob se proto neparsují jako výroky, jen jejich tabulky osob. Test: `test_no_duplicate_vyroky`.
4. **Generátor nad prázdnými nebo neúplnými daty** (téma bez výroků, osoba bez souhrnu, výrok bez citace, predikce bez `horizont_do`): stránka se vygeneruje bez výjimky. Test: `test_render_minimal`.
5. **`mkdocs serve` smyčka:** hook generuje jen při změně dat (hash obsahu `data/`), nikdy při změně generovaných souborů. Test: `test_hook_skips_when_unchanged`.

---

## Struktura souborů

```
requirements.txt                      # mkdocs-material, pyyaml, pytest
tools/archiv/__init__.py
tools/archiv/model.py                 # dataclassy Zdroj, Vyrok, Citace, OsobaRef, Vazba, Predikce, Teror, PrehledPolozka, Tema, Osoba
tools/archiv/io.py                    # načtení/zápis YAML ↔ model
tools/archiv/slug.py                  # slugify (shodný s MkDocs), id_zdroje()
tools/archiv/validate.py              # validace + CLI `python -m tools.archiv.validate`
tools/archiv/index.py                 # Archiv: indexy podle tématu, mluvčího, zmíněné osoby, predikcí
tools/archiv/render/common.py         # render jednoho výroku, symboly, odkazy
tools/archiv/render/tema.py
tools/archiv/render/osoba.py          # mluvčí + zmíněné osoby
tools/archiv/render/predikce.py
tools/archiv/render/teror.py
tools/archiv/render/zdroje.py
tools/archiv/render/vrabel.py
tools/archiv/generate.py              # generate(root) -> list[cesty] + nav + vyroky.json
tools/archiv/hook.py                  # MkDocs hook on_config
tools/migrace/zdroje.py               # _zdroje.md -> kostry zdrojů + mapa kotev
tools/migrace/ciselniky.py            # temata.yaml, osoby.yaml z mkdocs.yml + index.md + osoby/*.md
tools/migrace/temata.py               # tematické stránky -> výroky
tools/migrace/predikce.py             # predikce.md -> výroky typ predikce
tools/migrace/teror.py                # stochasticky-teror.md -> výroky typ stoch-teror
tools/migrace/prehled.py              # zpravodajstvi-vrabel/*.md -> zdroj.prehled
tools/migrace/osoby.py                # tabulky „Zmíněné osoby“ -> vyrok.osoby / zdroj.osoby
tools/migrace/souhrny.py              # úvodní texty stránek -> data/souhrny
tools/migrace/report.py               # srovnávací report před/po
tools/migrace/run.py                  # orchestrace celého převodu
tests/…                               # zrcadlí moduly; fixtures v tests/fixtures/
```

---

### Task 1: Datový model, I/O a validace

**Soubory:**
- Vytvořit: `requirements.txt`, `tools/__init__.py`, `tools/archiv/__init__.py`, `tools/archiv/model.py`, `tools/archiv/io.py`, `tools/archiv/slug.py`, `tools/archiv/validate.py`
- Test: `tests/test_model_io.py`, `tests/test_slug.py`, `tests/test_validate.py`, `tests/fixtures/data_min/` (1 zdroj se 3 výroky, `temata.yaml`, `osoby.yaml`)

**Rozhraní:**
- Poskytuje:
  - `model.Zdroj(id, mluvci, kanal, titul, datum: date, url, prepis, rezim='standard', cas=None, delka=None, poznamka=None, osoby: list[OsobaRef]=[], prehled: list[PrehledPolozka]=[], vyroky: list[Vyrok]=[])`
  - `model.Vyrok(id, typ, temata: list[str], nadpis, text, citace: list[Citace]=[], osoby: list[OsobaRef]=[], vazby: list[Vazba]=[], mluvci: str|None=None, dalsi_zdroje: list[str]=[], podtema: str|None=None, predikce: Predikce|None=None, teror: Teror|None=None)`
  - `Citace(text, cas=None)`, `OsobaRef(osoba, vztah, kontext='')`, `Vazba(na, typ)`, `Predikce(horizont, stav='ceka', horizont_do: date|None=None, vyhodnoceni: list[Vyhodnoceni]=[])`, `Vyhodnoceni(datum: date, text, stav: str|None=None)`, `Teror(terc, hranicni=False)`, `PrehledPolozka(tema, text, vyrok: str|None=None)`
  - `Tema(slug, nazev, popis='', nadrazene=None)`, `Osoba(slug, jmeno, aliasy=[], popis='', sledovany=False, vlastni_stranka=False)`
  - `io.nacti_zdroj(path) -> Zdroj`, `io.uloz_zdroj(z: Zdroj, root: Path) -> Path` (cesta `data/zdroje/YYYY/MM/<id>.yaml`), `io.nacti_vse(root) -> tuple[list[Zdroj], dict[str,Tema], dict[str,Osoba]]`
  - `slug.slugify(text) -> str` (shodné s MkDocs toc), `slug.ascii_slug(text) -> str` (pro id: bez diakritiky, `[a-z0-9-]`)
  - `validate.validuj(root) -> list[str]` (seznam chyb; prázdný = OK). CLI: `python -m tools.archiv.validate [root]` vrací exit 1 při chybách.

- [ ] **Krok 1: Napsat failing testy**
  - `test_roundtrip`: `uloz_zdroj` a pak `nacti_zdroj` vrátí shodný objekt. Víceřádkový `text` se uloží blokovým stylem `|` a česká diakritika zůstane nezměněná (soubor obsahuje `„` doslova, ne `„`).
  - `test_slug_matches_mkdocs`: `slugify("Ladislav Vrabel — Zprávy v devět 19. 11. 2026") == "ladislav-vrabel--zprávy-v-devět-19-11-2026"` a `slugify("Jaroslav Turánek — Přednáška VTE/FVE (seminář, sdíleno 14. 6. 2026)") == "jaroslav-turánek--přednáška-vte-fve-seminář-sdíleno-14-6-2026"`. Obě hodnoty jsou ověřené v dnešním `_zdroje.md` a ve `vetrniky.md`.
  - `test_ascii_slug`: `ascii_slug("Ladislav Vrabel") == "ladislav-vrabel"`, `ascii_slug("Zprávy v devět") == "zpravy-v-devet"`.
  - `test_validate_ok`: fixture `data_min` vrátí `[]`.
  - `test_validate_errors`: duplicitní id výroku, neznámé téma, neznámý mluvčí, neplatný `typ`, `typ: predikce` bez bloku `predikce`, `prepis` ukazující na neexistující soubor. Každá chyba má jednu hlášku obsahující id výroku nebo zdroje.
- [ ] **Krok 2:** `python -m pytest tests -q` → FAIL (moduly neexistují).
- [ ] **Krok 3: Implementovat.** Model jako `@dataclass`. Pro `io` použít `yaml.safe_load` a vlastní `Dumper` s reprezentací víceřádkových řetězců jako `|`, `sort_keys=False`, `allow_unicode=True`, prázdné seznamy a `None` vynechat. `slugify` použije `pymdownx.slugs.slugify(case='lower')`, protože je dostupné spolu s Material. Existenci přepisu ověřit relativně k `wiki/`.
- [ ] **Krok 4:** `python -m pytest tests -q` → PASS.
- [ ] **Krok 5: Commit** `feat(archiv): datový model, YAML I/O, validace`

---

### Task 2: Index archivu a render jednoho výroku

**Soubory:**
- Vytvořit: `tools/archiv/index.py`, `tools/archiv/render/__init__.py`, `tools/archiv/render/common.py`
- Test: `tests/test_index.py`, `tests/test_render_common.py`

**Rozhraní:**
- Používá: `io.nacti_vse`, model z Tasku 1
- Poskytuje:
  - `index.Archiv(zdroje, temata, osoby)` s atributy `vyroky: dict[id, (Vyrok, Zdroj)]`, metodami `podle_tematu(slug) -> list[(Vyrok,Zdroj)]` (seřazeno od nejnovějšího), `podle_mluvciho(slug)`, `zminky_osoby(slug) -> list[(OsobaRef, Vyrok|None, Zdroj)]` (sbírá `vyrok.osoby` i `zdroj.osoby`), `predikce() -> list[(Vyrok,Zdroj)]`, `teror()`, `mluvci_vyroku(v, z) -> str`, `nevyhodnocene_propadle(dnes: date)`
  - `common.render_vyrok(v, z, archiv, rel: str) -> str`: MD blok výroku. `rel` je relativní cesta ke kořeni wiki (`"../"` apod.) pro odkazy.
  - `common.SYMBOL_VZTAH`, `common.SYMBOL_STAV`

- [ ] **Krok 1: Failing testy**
  - `test_mluvci_override`: výrok s `mluvci: zitko` ve zdroji `mluvci: peterkova` → `mluvci_vyroku == "zitko"`.
  - `test_podle_tematu_order`: tři výroky s daty 1. 3., 5. 3. a 2. 3. → pořadí 5. 3., 2. 3., 1. 3.
  - `test_zminky_include_zdroj_level`: `OsobaRef` uložený jen v `zdroj.osoby` se objeví v `zminky_osoby` s `Vyrok=None`.
  - `test_propadle`: predikce s `horizont_do=2026-11-01`, `stav=ceka` je v `nevyhodnocene_propadle(date(2026,11,20))`. S `stav=vyvraceno` tam není.
  - `test_render_vyrok_contains`: výstup obsahuje `{#<id>}` u nadpisu, jméno mluvčího, datum ve formátu `19. 11. 2026`, citaci v `> „…“` a za ní `[04:47]`, odkaz `…zdroje/2026-11/#<id-zdroje>` a odkaz na přepis `…prepisy/done/<soubor>`. Vazba `opakovani` se vyrenderuje jako „opakuje [nadpis cíle](…#cíl)“.
  - `test_render_minimal`: výrok bez citací, osob a vazeb se vyrenderuje bez výjimky a bez prázdných nadpisů.
- [ ] **Krok 2:** testy → FAIL.
- [ ] **Krok 3: Implementovat.** Formát bloku výroku:

```markdown
### {nadpis} {#id}

**{Jméno mluvčího}** · {D. M. YYYY} · {typ, pokud není tvrzeni} · [{titul zdroje}]({rel}zdroje/{YYYY-MM}/#{id-zdroje}) · [přepis]({rel}prepisy/done/{soubor})

{text}

> „{citace}“ [{cas}]

*Osoby:* {jméno} {symbol} — {kontext}; …
*Vazby:* posun oproti [..](..#..); …
```

- [ ] **Krok 4:** testy → PASS.
- [ ] **Krok 5: Commit** `feat(archiv): index archivu a render výroku`

---

### Task 3: Generované stránky

**Soubory:**
- Vytvořit: `tools/archiv/render/tema.py`, `osoba.py`, `predikce.py`, `teror.py`, `zdroje.py`, `vrabel.py`, `tools/archiv/generate.py`
- Test: `tests/test_generate.py` (fixture `tests/fixtures/data_gen/`: 2 mluvčí, 2 témata, 1 Vrabelův zdroj s `prehled`, 2 predikce, 1 stoch-teror hraniční, 1 souhrn tématu)

**Rozhraní:**
- Používá: `Archiv`, `render_vyrok`
- Poskytuje: `generate.generate(root: Path, out: Path) -> dict` vrací `{"soubory": [Path...], "nav": list}` (nav ve formátu MkDocs, pro `config['nav']`). Zapíše i `out/data/vyroky.json`.

Stránky (cesty relativně k `out` = `wiki/`):

| Cesta | Obsah |
|---|---|
| `temata/<slug>.md` | `# název`, souhrn (`data/souhrny/temata/<slug>.md` + „aktualizováno“ podle mtime), tabulka „Kdo k tématu mluví“ (mluvčí, počet, odkaz s filtrem `#mluvci-<slug>`), pak výroky seskupené podle `podtema` (bez podtématu na konec pod „Ostatní“), uvnitř od nejnovějšího. Nad 150 výroků: hlavní stránka obsahuje souhrn a odkazy na `temata/<slug>/<rok>.md`. |
| `osoby/<slug>.md` (jen `vlastni_stranka`) | souhrn, „Zdroje“ (počet a odkaz na filtr zdrojů), „Podle témat“ (pro každé téma seznam nadpisů výroků s odkazy na tematickou stránku), „Predikce“ (tabulka a bilance počtů podle stavu), „Stochastický teror“, „Zmínění lidé“ (tabulka ze `zminky` výroků mluvčího seskupená podle osoby, řádky chronologicky). |
| `zminene/<slug>.md` (každá osoba z číselníku, která má aspoň 1 zmínku) | kdo o osobě mluvil, vztah a kontext, datum, odkaz na výrok nebo zdroj, chronologicky. |
| `predikce/index.md` | sekce „Propadlé k vyhodnocení“ (`nevyhodnocene_propadle(date.today())`), tabulka všech predikcí (mluvčí, datum, nadpis s odkazem, horizont, stav symbolem). Pod ní plné bloky predikcí po měsících (`predikce/<YYYY-MM>.md`) včetně vyhodnocení. |
| `stochasticky-teror.md` | tabulka Autor / Terč / Citace / Datum / Zdroj (dnešní formát), pak „Hraniční“ zvlášť, pak ručně psaný text „Poznámky“ ze `data/souhrny/stochasticky-teror.md`. |
| `zdroje/<YYYY-MM>.md` + `zdroje/index.md` | po měsících: `## {titul} {#id}` s Soubor, Kanál, URL, Datum, Poznámka, počet výroků a odkazy na ně. Index: seznam měsíců a sekce „Nezpracované / přeskočené přepisy“ (soubory v `wiki/prepisy/done/` bez zdroje, plus zdroje s `rezim: preskoceno`). Zachovat třídy pro `js/zdroje-filter.js` (filtr podle kanálu). |
| `zpravodajstvi-vrabel/<YYYY-MM>.md` | dnešní formát: `## YYYY-MM-DD — {titul}`, odrážky z `prehled` (u položky s `vyrok` „⚡ … → viz [téma](…#id)“), `**Zdroj:**`. Nejnovější nahoře. |

Nav: Úvod, Témata (abecedně podle názvu, podtémata vnořená podle `nadrazene`), Osoby (`vlastni_stranka`), Predikce, Stochastický teror, Zpravodajství Vrabel (měsíce sestupně), Zdroje, Extra (ručně: `extra/prilis-drahy-vitr.md`), O stránce.

- [ ] **Krok 1: Failing testy** nad `data_gen`:
  - `test_generate_files`: existují `temata/vetrniky.md`, `osoby/zitko.md`, `predikce/index.md`, `stochasticky-teror.md`, `zdroje/index.md`, `zdroje/2026-11.md`, `zpravodajstvi-vrabel/2026-11.md`, `data/vyroky.json`.
  - `test_tema_contains_all`: každý výrok s tématem `vetrniky` má v `temata/vetrniky.md` svou kotvu `{#id}`, a to i výrok, kde je `vetrniky` druhé téma.
  - `test_split_by_year`: fixture s 151 výroky v jednom tématu (generované v testu) → vzniknou `temata/x/2025.md` a `temata/x/2026.md` a hlavní stránka na ně odkazuje.
  - `test_json_export`: `vyroky.json` je seznam objektů s klíči `id, typ, temata, mluvci, datum, zdroj, url, prepis, nadpis, text, citace, osoby, vazby, predikce, teror` a počet odpovídá počtu výroků.
  - `test_vrabel_prehled_link`: položka `prehled` s `vyrok` obsahuje `⚡` a odkaz `../temata/<hlavní téma>.md#<id>`.
  - `test_nezpracovane`: přepis v `prepisy/done/` bez zdroje se objeví v `zdroje/index.md` v sekci „Nezpracované / přeskočené přepisy“.
  - `test_nav_shape`: `nav[0] == {"Úvod": "index.md"}` a položka `"Témata"` obsahuje `{"Větrné elektrárny": "temata/vetrniky.md"}`.
- [ ] **Krok 2:** testy → FAIL.
- [ ] **Krok 3: Implementovat** renderery (čisté f-stringy) a `generate`. Generátor smaže před zápisem pouze generované cesty z Globálních omezení.
- [ ] **Krok 4:** testy → PASS.
- [ ] **Krok 5: Commit** `feat(archiv): generátor stránek, navigace a JSON export`

---

### Task 4: MkDocs hook, CI a .gitignore

**Soubory:**
- Vytvořit: `tools/archiv/hook.py`
- Upravit: `mkdocs.yml` (přidat `hooks: [tools/archiv/hook.py]`, `nav:` zatím ponechat), `.github/workflows/deploy.yml` (`pip install -r requirements.txt`), `.gitignore`
- Test: `tests/test_hook.py`

**Rozhraní:**
- Používá: `generate.generate`
- Poskytuje: `hook.on_config(config) -> config`. Když existuje `data/temata.yaml`, vygeneruje stránky (pokud se změnil hash `data/`) a nastaví `config['nav']`. Když `data/` neexistuje, nic nedělá a ruční nav zůstane (bezpečné během převodu). Hash uloží do `.cache/archiv.hash`.

- [ ] **Krok 1: Failing testy**
  - `test_hook_noop_without_data`: config s `docs_dir` v tmp bez `data/` → `nav` beze změny a žádný soubor nevznikne.
  - `test_hook_generates_and_sets_nav`: s fixturou `data_gen` → `config['nav']` začíná `{"Úvod": "index.md"}` a existuje `temata/vetrniky.md`.
  - `test_hook_skips_when_unchanged`: druhé volání bez změny dat nezmění mtime `temata/vetrniky.md`.
- [ ] **Krok 2:** FAIL → **Krok 3:** implementovat. Hook přijímá `config` jako dict-like (MkDocs `MkDocsConfig` podporuje `config['docs_dir']`, `config['nav']`). Kořen repozitáře = rodič `docs_dir`. → **Krok 4:** PASS.
- [ ] **Krok 5: Ověřit build beze změny webu:** `mkdocs build -q -d <scratch>/site` → exit 0, protože `data/` ještě neexistuje a hook nic nedělá.
- [ ] **Krok 6: Commit** `feat(archiv): MkDocs hook, CI závislosti`

---

### Task 5: Převod — číselníky a kostry zdrojů

**Soubory:**
- Vytvořit: `tools/migrace/__init__.py`, `tools/migrace/ciselniky.py`, `tools/migrace/zdroje.py`
- Test: `tests/migrace/test_zdroje.py`, `tests/migrace/test_ciselniky.py` (fixtures: výřez 3 sekcí `_zdroje.md`, výřez `mkdocs.yml` nav a tabulky z `index.md`)

**Rozhraní:**
- Poskytuje:
  - `zdroje.parsuj_zdroje(md: str) -> list[ZdrojRaw]`, kde `ZdrojRaw(nadpis, kotva, pole: dict[str,str])` a `kotva` je explicitní `{#…}`, jinak `slugify(nadpis)`
  - `zdroje.na_zdroj(raw, osoby: dict) -> Zdroj` (bez výroků; `mluvci` z kanálu nebo jména před „ — “ přes aliasy osob; `datum` z „Datum záznamu“ jen jako `YYYY-MM-DD`, čas z „(…, 23:11)“ do `cas`; `poznamka` = Poznámka, Délka a Zhlédnutí spojené)
  - `zdroje.mapa_kotev(raws, zdroje) -> dict[str, str]` (kotva → id zdroje)
  - `ciselniky.temata_z_wiki(mkdocs_yml: str, index_md: str) -> list[Tema]`, `ciselniky.osoby_z_wiki(wiki: Path) -> list[Osoba]`. Sledovaní mluvčí z `wiki/osoby/*.md` mají `vlastni_stranka=True`. Aliasy jsou ručně doplněné v `ciselniky.ALIASY` (min.: `rajchl: ["Reichl","Rejchl","Jindra Rajchl"]`, `zitko: ["Československo TV2","ČsTV2","Jiří Hradil"]`, `boldy: ["Konspirátor Boldy","KonspyChannel"]`, `si-tin-pching: ["Siti Ping","Xi Jinping","Si"]`).

- [ ] **Krok 1: Failing testy**
  - `test_parse_explicit_and_slug_anchor`: sekce s `{#ladislav-vrabel--zprávy-v-devět-14-11-2026}` dostane tuto kotvu. Sekce „Jindřich Rajchl — FARA, DSA, Dozimetr“ bez explicitní kotvy dostane `jindřich-rajchl--fara-dsa-dozimetr`.
  - `test_na_zdroj_cstv2`: „Datum záznamu: 2026-11-14, 23:11 (soubor datován 15. 11., …)“ → `datum=2026-11-14`, `cas="23:11"`, `mluvci="zitko"`, `prepis` = cesta z „Soubor“.
  - `test_unique_ids`: dva zdroje téhož mluvčího a dne s různým titulem dostanou různá `id`.
  - `test_temata_z_wiki`: z nav vznikne `Tema("vetrniky","Větrné elektrárny", popis z tabulky index.md)`. Témata `konspirace-ceskoslovensko` a `konspirace-deep-state-qanon` mají `nadrazene="konspirace"`.
- [ ] **Krok 2:** FAIL → **Krok 3:** implementovat → **Krok 4:** PASS.
- [ ] **Krok 5: Spustit nad reálnými daty:** `python -m tools.migrace.run --krok zdroje` zapíše `data/temata.yaml`, `data/osoby.yaml` a ~796 koster. Ověřit: `python -m tools.archiv.validate` → 0 chyb. Počet souborů v `data/zdroje/**` = počet sekcí `## ` v `_zdroje.md` minus nadpis `# Zdroje`.
- [ ] **Krok 6: Commit** `feat(migrace): číselníky a kostry zdrojů` (data i kód)

---

### Task 6: Převod — výroky z tematických stránek

**Soubory:**
- Vytvořit: `tools/migrace/temata.py`
- Test: `tests/migrace/test_temata.py` (fixtures: výřez `vetrniky.md` řádky 1–92, sekce z `fara-neziskovky.md` s `**16. 11. — Černohorský**` odstavci, sekce z `predikce.md`-like s více zdroji bez datovaných odstavců)

**Rozhraní:**
- Používá: `mapa_kotev`, `osoby` (aliasy), `slugify`
- Poskytuje:
  - `temata.parsuj_stranku(md: str, tema_slug: str) -> list[Jednotka]`, kde `Jednotka(tema, kapitola, nadpis, datum: date|None, mluvci: str|None, text, citace: list[Citace], kotvy_zdroju: list[str], explicitni_kotva: str|None)`
  - `temata.prirad(jednotky, mapa, zdroje_by_id) -> tuple[list[(Jednotka, zdroj_id)], list[Jednotka]]` (přiřazené, nepřiřazené)
  - `temata.na_vyrok(j, zdroj, poradi) -> Vyrok` (`typ='tvrzeni'`, `temata=[tema]`, `podtema=j.kapitola`, `dalsi_zdroje` = ostatní zdroje, pokud jich jednotka má víc)

Pravidla parsování:
- Jednotka = `###` sekce. Pokud sekce obsahuje datované odstavce (`^\*\*\d{1,2}\. \d{1,2}\.( \(\d{1,2}:\d{2}\))?( — [^*]+)?\*\* — `), první část sekce (do prvního datovaného odstavce) je jedna jednotka a každý datovaný odstavec (až po další datovaný odstavec nebo `**Zdroje:**`) je další jednotka. Následná citace `> „…“ — Jméno` patří k předchozí jednotce.
- Datum: z nadpisu `(…, D. M. YYYY)` nebo `(D. M. YYYY)` nebo `— Mluvčí (D. M. YYYY)`. U datovaného odstavce `D. M.` + rok z nadpisu sekce (pokud by datum odstavce bylo dřív než datum sekce, rok + 1). Mluvčí z nadpisu nebo odstavce přes aliasy.
- Zdroj jednotky: odkazy `_zdroje.md#kotva` z řádku `**Zdroje:**` sekce. U datovaného odstavce se vybere ten zdroj, jehož datum = datum odstavce a mluvčí = mluvčí odstavce. Pokud žádný nesedí, jednotka jde do nepřiřazených. U úvodní části se vybere nejstarší zdroj s mluvčím sekce a ostatní zdroje jdou do `dalsi_zdroje`.
- Kotva: explicitní `{#…}` z nadpisu se uloží jako vazba na kompatibilní id (`Vyrok.id` se generuje podle pravidla, starou kotvu si `run.py` uloží do `data/migrace/stare-kotvy.json` pro přepis vnitřních odkazů v Tasku 9).
- Výrok, který se objeví na dvou tematických stránkách se stejným nadpisem a stejným zdrojem, se nevytvoří dvakrát: druhý výskyt přidá téma do `temata`.
- Text se přenáší doslova (Markdown odkazy uvnitř zůstanou; relativní odkazy `xxx.md#kotva` se přepíší až v Tasku 9).

- [ ] **Krok 1: Failing testy**
  - `test_split_dated_paragraphs`: sekce „Letná 15. 11.: „cirkus…“ (Rajchl, 15. 11. 2026)“ s odstavci `**16. 11.** — …` a `**16. 11. — Černohorský** …` a `**16. 11. — Černohorský (Facebook Live)** …` → 4 jednotky. Mluvčí: rajchl, rajchl, cernohorsky, cernohorsky. Datum 2026-11-15 a 3× 2026-11-16.
  - `test_assign_by_date_and_speaker`: dvě jednotky Černohorského 16. 11. se přiřadí ke dvěma různým zdrojům podle mluvčího a data. Když jsou dva kandidáti, rozhodne shoda slov titulu zdroje (dron / Facebook Live) s textem.
  - `test_unassigned_goes_out`: jednotka s datem, ke kterému není zdroj, je v nepřiřazených, ne zahozená.
  - `test_no_duplicate_vyroky`: stejná sekce na dvou stránkách → 1 výrok se 2 tématy.
  - `test_quotes_extracted`: `> „X“ — Ladislav Vrabel` → `Citace("X")`, z textu odstraněno.
- [ ] **Krok 2:** FAIL → **Krok 3:** implementovat → **Krok 4:** PASS.
- [ ] **Krok 5: Spustit nad reálnými daty:** `python -m tools.migrace.run --krok temata`. Výroky se zapíší do zdrojů, nepřiřazené do `data/zdroje/_nezarazeno.yaml` (struktura: `jednotky: [{tema, kapitola, nadpis, datum, mluvci, text, kotvy_zdroju}]`). Vypsat počty: jednotky, přiřazené, nepřiřazené. Cíl: nepřiřazené < 5 %. Pokud je víc, upravit heuristiky, než se půjde dál.
- [ ] **Krok 6:** `python -m tools.archiv.validate` → 0 chyb. Commit `feat(migrace): výroky z tematických stránek`.

---

### Task 7: Převod — predikce, stochastický teror, Vrabelovy přehledy, zmíněné osoby

**Soubory:**
- Vytvořit: `tools/migrace/predikce.py`, `teror.py`, `prehled.py`, `osoby.py`
- Test: `tests/migrace/test_predikce.py`, `test_teror.py`, `test_prehled.py`, `test_osoby.py` (fixtures z reálných výřezů: záznam „Zítko — EBS a karanténa 3–33 dní…“ s datovanými poznámkami a `**Vyhodnocení 20. 11. 2026:**`, 3 řádky tabulky teroru včetně hraničního, den 2026-11-19 z `zpravodajstvi-vrabel/2026-11.md`, 3 řádky tabulky z `osoby/vrabel.md`)

**Rozhraní:**
- Poskytuje: `predikce.parsuj(md) -> list[PredikceRaw]`, `predikce.na_vyrok(raw, zdroj, poradi) -> Vyrok`; `teror.parsuj(md) -> list[TerorRaw]`, `teror.na_vyrok(...) -> Vyrok`; `prehled.parsuj(md) -> dict[date, list[PrehledPolozka]]` (odkaz `→ viz […](…#kotva)` se přeloží přes `stare-kotvy.json` na id výroku); `osoby.parsuj_tabulku(md) -> list[ZminkaRaw(osoba_text, vztah, kontext, datum, kotva_zdroje)]`, `osoby.prirad(zminky, archiv) -> None` (zapíše do `vyrok.osoby` nebo `zdroj.osoby`).

Pravidla:
- Predikce: nadpis `### Mluvčí — název (D. M. YYYY)`, pole Předpověď → `text`, citace → `citace`, Horizont → `predikce.horizont`. `horizont_do` se odvodí jen z jednoznačného data v horizontu (`do D. M. YYYY`, `D. M. YYYY`, „do roku YYYY“ → 31. 12.), jinak `None`. Stav podle symbolu (🕐 ✅ ❌ ⚠️) a text stavu za pomlčkou → první `Vyhodnoceni`. Datované poznámky `**D. M.** — …` a `**Vyhodnocení 20. 11. 2026:** …` → `vyhodnoceni` s datem. `temata` = témata výroku stejného zdroje a data, jinak `[]` a hlášení. Mluvčí mimo číselník (Putin, Mélenchon, Zalužnyj, VK) → `mluvci` override na osobu z číselníku (doplnit `Osoba`, `vlastni_stranka=False`).
- Teror: řádek tabulky → výrok `typ='stoch-teror'`, `teror.terc` = sloupec terč, `hranicni` = text obsahuje „hraniční“, `citace` = sloupec citace. Zdroj z odkazu, datum ze sloupce.
- Přehled: den → zdroj Vrabela s tím datem (pokud jich je víc, podle titulu v hlavičce dne). Nepřiřazený den jde do `_nezarazeno`.
- Zmíněné osoby: osoba se namapuje přes jméno a aliasy. Neznámá osoba se přidá do číselníku (`slug` = `ascii_slug(jméno)`, sloučená jména „A, B“ se rozdělí na více záznamů se stejným vztahem). Řádek se přiřadí k výroku stejného zdroje, jehož text obsahuje příjmení osoby, jinak do `zdroj.osoby`.

- [ ] **Krok 1: Failing testy**
  - `test_predikce_vyhodnoceni`: fixture „EBS a karanténa…“ → `stav='vyvraceno'`, `vyhodnoceni` obsahuje položky s daty 2026-11-16, 2026-11-17, 2026-11-18 a stav z řádku Stav.
  - `test_horizont_do`: „do cca 18. 12. 2026 (35 dní)…“ → `2026-12-18`, „neurčeno“ → `None`, „do 2028“ → `2028-12-31`.
  - `test_teror_hranicni`: řádek s „(hraniční)“ v terči → `hranicni=True`.
  - `test_prehled_link_to_vyrok`: položka s `→ viz [Válka…](../valka-nato-rusko.md#summit-trump-putin-si-multipolarita-vrabel-19-11-2026)` → `PrehledPolozka.vyrok` = id výroku, které `stare-kotvy.json` přiřadí té kotvě.
  - `test_osoby_split_and_assign`: řádek „Andrej Babiš, Petr Pavel, Jindřich Rajchl | ❌ negativní | „Ohební“…“ → 3 `OsobaRef`. Babiš se přiřadí k výroku, jehož text obsahuje „Babiš“.
- [ ] **Krok 2:** FAIL → **Krok 3:** implementovat → **Krok 4:** PASS.
- [ ] **Krok 5: Spustit:** `python -m tools.migrace.run --krok predikce,teror,prehled,osoby`. Počty musí sedět: predikce = 231, řádky teroru = počet řádků tabulek, dny přehledu = počet `## 2026-` napříč `zpravodajstvi-vrabel/*.md`. Rozdíly vypsat do reportu.
- [ ] **Krok 6:** validate → 0 chyb. Commit `feat(migrace): predikce, teror, přehledy, zmíněné osoby`.

---

### Task 8: Převod — souhrny a srovnávací report

**Soubory:**
- Vytvořit: `tools/migrace/souhrny.py`, `tools/migrace/report.py`, `tools/migrace/run.py` (orchestrace, `--krok` a `--vse`)
- Test: `tests/migrace/test_souhrny.py`, `tests/migrace/test_report.py`

**Rozhraní:**
- Poskytuje: `souhrny.uvod_stranky(md) -> str` (text mezi `# H1` a první `##`/`###`, bez `---`), který se zapíše do `data/souhrny/temata/<slug>.md` nebo `…/osoby/<slug>.md` (u osob úvodní popis před `## Témata`). `report.srovnani(wiki_old: Path, archiv) -> str` vypíše Markdown report do `data/migrace/report.md`.
- Report obsahuje: počet zdrojů (staré `_zdroje.md` / nové), výroků celkem a podle tématu (staré `###` sekce + datované odstavce / nové), predikcí podle stavu, řádků teroru, dní přehledu, zmínek osob (řádky tabulek / `OsobaRef`), velikost `_nezarazeno`, zdroje bez výroků (seznam), osiřelé vnitřní odkazy.

- [ ] **Krok 1: Failing testy:** `test_uvod_vetrniky` (fixture `vetrniky.md` → začíná „Větrné elektrárny a plánované akcelerační zóny“), `test_report_counts` (mini wiki a mini archiv → řádky „Predikce: 2 / 2“ a „Nezařazeno: 1“).
- [ ] **Krok 2:** FAIL → **Krok 3:** implementovat → **Krok 4:** PASS.
- [ ] **Krok 5:** `python -m tools.migrace.run --krok souhrny,report` → `data/migrace/report.md`. Commit `feat(migrace): souhrny, report`.

---

### Task 9: Dočištění agenty a pilotní ukázka uživateli (kontrolní bod)

Není to kód, jde o procesní task.

- [ ] **Krok 1:** Pro `data/zdroje/_nezarazeno.yaml` spustit agenty v dávkách po ~40 jednotkách. Každá dávka dostane jednotky, seznam zdrojů daného mluvčího ±7 dní a přepisy. Agent vrátí pro každou jednotku `{index, zdroj_id | "nelze", duvod}`. Výsledek aplikuje skript `python -m tools.migrace.run --krok aplikuj-prirazeni <json>`. Co zůstane „nelze“, zůstává v `_nezarazeno` (zobrazí se v reportu).
- [ ] **Krok 2:** Přepsat vnitřní odkazy v textech výroků a souhrnů (`xxx.md#stara-kotva`) přes `stare-kotvy.json` na `temata/<slug>.md#<id>`. Neznámé kotvy jdou do reportu.
- [ ] **Krok 3:** Zapnout generátor lokálně: přidat `data/` (už existuje), spustit `mkdocs build -q -d <scratch>/site`, vyhledat `WARNING` (nefunkční odkazy) a počet opravit pod 20, zbytek uvést v reportu.
- [ ] **Krok 4: Kontrolní bod s uživatelem:** publikovat náhled jako Artifact nebo poslat cesty: `temata/vetrniky.md`, `osoby/tarabova.md`, `predikce/index.md`, `data/migrace/report.md`. Uživatel schválí, nebo vrátí připomínky. **Bez schválení se nepokračuje Taskem 10.**
- [ ] **Krok 5:** Commit `chore(migrace): dočištění a odkazy`.

---

### Task 10: Přepnutí

**Soubory:**
- Smazat: staré `wiki/*.md` tematické stránky, `wiki/_zdroje.md`, `wiki/predikce.md`, `wiki/osoby/*.md`, `wiki/zpravodajstvi-vrabel/*.md` (zůstávají `index.md`, `o-strance.md`, `extra/`, `css/`, `js/`, `prepisy/`)
- Upravit: `mkdocs.yml` (odstranit ruční `nav:`, protože navigaci teď dosazuje hook), `wiki/index.md` (tabulka témat → odkaz na generovaný přehled, popis projektu jako archivu), `wiki/o-strance.md`, `wiki/js/zdroje-filter.js` (pokud se změnily selektory), `CLAUDE.md`
- Paměť: aktualizovat `project_struktura_wiki.md`, `project_redo_progress.md`, `feedback_opakovane_tema.md` (opakování = výrok s vazbou)

- [ ] **Krok 1:** Smazat staré stránky, `mkdocs build -q` → exit 0. `python -m pytest tests -q` → PASS. `python -m tools.archiv.validate` → 0 chyb.
- [ ] **Krok 2:** Přepsat CLAUDE.md, sekce „Jak strukturovat výstup“, „Formát záznamu…“, „Soubor _zdroje.md“, „Stránky osob“, „Workflow“ a Vrabelův formát. Nový workflow kroku 6–12: jeden YAML soubor, kterého pole se jak plní (odkaz na `docs/superpowers/specs/…` a na vzor `data/zdroje/2026/11/<nějaký Vrabelův>.yaml` a `<nějaký Rajchlův>.yaml`), číselníky, `python -m tools.archiv.validate`, přesun přepisu, commit. Obsahová pravidla (co extrahovat, neutrální tón, stochastický teror vždy, výběr témat, Vrabel bez ptaní, přeskakování) zachovat doslova.
- [ ] **Krok 3:** Zkušební zpracování: vzít libovolný nově stažený přepis (`bash sync-prepisy.sh`) jen pokud to uživatel zadá. Jinak ověřit postup na kopii existujícího zdroje (smazat a znovu zapsat jeden Tarabové), ověřit validate a build.
- [ ] **Krok 4:** Commit `feat: přepnutí wiki na datový archiv`. Push a ověření deploye (`gh run watch`) až po souhlasu uživatele.

---

## Self-review (provedeno při psaní)

- Pokrytí specifikace: 5.1 → T1, T4, 5.2 → T1, 5.3 → T5, 5.4 → T2, T3, 5.5 → T3 (render), T8 (převod), 5.6 → T10, 5.7 → T5–T9, 5.8 → pořadí tasků, JSON → T3, přeskočené přepisy → T3 (`test_nezpracovane`), pyyaml do CI → T4, nav z hooku → T3, T4.
- Konzistence typů: `Archiv`, `render_vyrok`, `generate`, `mapa_kotev`, `Jednotka`, `stare-kotvy.json` používají stejná jména napříč tasky.
- Body Review Focus mají testy: 1 → T1 `test_slug_matches_mkdocs`, 2 → T6 `test_split_dated_paragraphs`, 3 → T6 `test_no_duplicate_vyroky`, 4 → T2 `test_render_minimal`, 5 → T4 `test_hook_skips_when_unchanged`.
