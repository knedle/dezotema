# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Co je tento projekt

Tematický archiv názorů, postojů a tvrzení z přepisů videí a rozhovorů. Data jsou v YAML (`data/`), stránky se z nich generují při buildu MkDocs a publikují na GitHub Pages.

Živě na **https://knedle.github.io/dezotema/**.

---

## Struktura projektu (datový archiv)

- `data/zdroje/YYYY/MM/<id>.yaml` — **1 soubor = 1 zpracované video**: metadata zdroje + všechny jeho výroky (tvrzení, postoje, predikce, stochastický teror) + u Vrabela denní přehled. **Jediné místo, kam se při zpracování zapisuje obsah.**
- `data/temata.yaml` — číselník témat (slug, název, popis, nadřazené téma)
- `data/osoby.yaml` — číselník osob (slug, jméno, aliasy, popis, `sledovany`, `vlastni_stranka`)
- `data/souhrny/temata/<slug>.md`, `data/souhrny/osoby/<slug>.md`, `data/souhrny/stochasticky-teror.md` — volné úvodní texty stránek; přepisují se jen **na vyžádání** („obnov souhrn větrníků“)
- `data/migrace/` — artefakty jednorázového převodu ze staré wiki (report, mapy starých kotev); při běžné práci se nemění
- `tools/archiv/` — model, načítání/ukládání, validace (`python -m tools.archiv.validate`), generátor stránek a MkDocs hook
- `wiki/` — docs_dir. Ručně psané jsou jen `index.md`, `o-strance.md`, `extra/`, `css/`, `js/`. Stránky `temata/`, `osoby/`, `zminene/`, `predikce/`, `zdroje/`, `zpravodajstvi-vrabel/`, `stochasticky-teror.md` a `data/vyroky.json` **generuje hook** při `mkdocs build/serve` — jsou v `.gitignore`, **nikdy je needituj ručně** (přepíšou se).
- `wiki/prepisy/` — přepisy čekající na zpracování; `wiki/prepisy/done/` — zpracované (i přeskočené) přepisy

> `prepisy/` je uvnitř `wiki/` (docs_dir), aby MkDocs servoval `.txt` přepisy jako přímé prokliky ze stránek zdrojů.

Návrh a datový model podrobně: `docs/superpowers/specs/2026-11-20-datovy-archiv-design.md` (kap. 5.2). Vzory souborů: `data/zdroje/2026/11/2026-11-19_vrabel_zpravy-v-devet-19-11-2026.yaml` (Vrabel), `data/zdroje/2026/11/2026-11-17_rajchl_projev-k-17-listopadu-vitezny-unor-17-11-2026.yaml` (standardní zdroj).

---

## Formát souborů v `wiki/prepisy/`

**Název souboru:** `YYYY-MM-DD_Jméno-Zdroje_Název-videa[_N].txt`

**Obsah souboru** má tři sekce oddělené `===`:
1. `METADATA` — obsahuje pole `Kanál:`, `Datum videa:`, `URL:`, aj.
2. `VÝKON` — technické info o přepisu (ignoruj)
3. `PŘEPIS` — samotný text s časovými značkami `[MM:SS]`

Zdroj se identifikuje z části názvu souboru mezi prvním a druhým podtržítkem, nebo z pole `Kanál:` v METADATA.

### Restart Česko (Adam Šejna) — specifika

`Restart-Cesko` je hlavní kanál **Adama Šejny**, influencera strany Motoristé.

- Zpracovávají se i **krátká videa / krátké texty** — projdou stejným zhodnocením témat jako u ostatních zdrojů (Fáze 1).
- Pokud přepis nese znaky, že **nemluví Šejna** (např. mluví žena, více osob, cizí řečník), soubor **nezpracovávej** — nahlas to uživateli ke kontrole.
- **Pouliční „gotcha" rozhovory** (Šejna klade otázky náhodným účastníkům demonstrací/akcí, hlavní obsah tvoří odpovědi dotazovaných, ne jeho vlastní tvrzení) — **nezpracovávat**. Soubor přesunout do `done/` bez souboru v `data/zdroje/` a bez dalších úprav.

### Ladislav Vrabel — specifika

Kanál má charakter **denního zpravodajského komentáře** — každé video obsahuje velké množství témat, z nichž většina je čistě popisná (referuje aktuální stav/zprávy) bez posunu vůči jeho už zaznamenanému světonázoru. Standardní postup (extrakce jen vybraných témat do tematických stránek) by tím tematické stránky zbytečně zaplevelil opakovaným popisem stavu.

**Odlišný postup zpracování:**

1. **Bez ptaní uživatele** — seznam témat k výběru se nezobrazuje; u každého tématu sám posoudíš, zda jde o pouhý popis stavu, nebo zda Vrabel přidává vlastní hodnocení/rámování/posun (⚡).
2. **Všechna** témata z videa (vybraná i nevybraná) se zaznamenají jako krátká položka (1 věta) do denního přehledu — pole `prehled:` ve zdrojovém souboru (`rezim: vrabel`) — cílem je mít úplný přehled, co všechno ten den pokrýval, i když to není hodné vlastního výroku.
3. Jen témata s posunem/vlastním úhlem (⚡) navíc projdou **plným** zpracováním jako výroky (jako u ostatních zdrojů) — u odpovídající položky přehledu se pak vyplní `vyrok: <id výroku>`. Položka může odkazovat i na starší výrok, který téma už pokrývá (opakování).
4. Predikce a stochastický teror se extrahují bezvýjimečně jako u všech zdrojů, nezávisle na tomto přehledu.
5. Zmíněné osoby (`osoby:`) se zapisují jen u plně zpracovaných výroků, ne u položek, které jsou jen v přehledu.

**Formát přehledu** (pořadí položek = pořadí ve videu; měsíční stránky přehledu i navigaci generuje hook sám):

```yaml
  prehled:
  - tema: Summit USA–Rusko–Čína
    text: 1 věta co k tomu řekl
    vyrok: vrabel-2026-11-19-06      # jen u ⚡ (plně zpracováno)
  - tema: Černá hora uzavřela daňovou kapitolu
    text: v EU nelze zavést jeho 1% daň (opakuje).
```

---

## Výběr souborů ke zpracování

Uživatel vždy sdělí, kolik souborů nebo které konkrétní zpracovat. Bez pokynu nezačínej.

**Kontrola před zpracováním:** Soubor je zpracovaný, pokud se nachází v `wiki/prepisy/done/` nebo na něj odkazuje pole `prepis:` některého souboru v `data/zdroje/`. Vybírej výhradně soubory v `wiki/prepisy/` (nikoliv `wiki/prepisy/done/`).

---

## Pravidla zpracování přepisů

### Fáze 1: Identifikace témat

Po přečtení souboru sestavíš seznam témat a zobrazíš ho uživateli jako **číslovaný textový seznam** (ne interaktivní checkboxy). Uživatel odpoví, která témata zpracovat.

**Formát každého tématu v seznamu:** Název tématu + 1 věta o čem mluvčí k tématu mluví.

**Co vždy identifikuješ jako téma:**
- Každý tematický blok kde mluvčí vyjadřuje tvrzení, postoj nebo predikci — bez ohledu na to, zda je téma politické, zdravotní, konspirační nebo jiné

**Co nikdy nenabídneš jako téma:**
- Čistě osobní příběhy bez obecnějšího závěru (rodinné anekdoty, vzpomínky bez tvrzení)
- Logistika: pozvánky na akce, organizační oznámení, technická sdělení
- Cizí sdílená videa — přepis zachycuje převážně cizí řeč, ne mluvčího kanálu

### Fáze 2: Zpracování vybraných témat

Po výběru uživatele:

**Pokud uživatel vybere alespoň jedno téma** → zpracuj pouze vybraná témata, ostatní ignoruj.

**Pokud uživatel nevybere žádné téma** → přesuň soubor do `done/` bez souboru v `data/zdroje/` a bez jakýchkoli dalších úprav. Commitni se stručnou poznámkou. (Generátor takový přepis sám uvede mezi nezpracovanými/přeskočenými.)

### Co extrahovat (do vybraných témat)
- **Tvrzení** — konkrétní faktuální výroky ("X způsobuje Y", "Z funguje tak, že...")
- **Názory a postoje** — hodnotící výroky, přesvědčení, doporučení
- **Zajímavé citace** — přesné formulace hodné zachování (max 1–2 věty)
- **Predikce** — explicitní předpovědi budoucího vývoje ("za X měsíců nastane Y", "do voleb se stane Z", "Bitcoin dosáhne..."); zaznamenávej jako výrok `typ: predikce`
- **Stochastický teror** — výroky splňující: **pojmenovaný terč** (konkrétní osoba nebo skupina) + **dehumanizace nebo výzva k trestu/násilí**; zaznamenávej jako výrok `typ: stoch-teror` bez ohledu na to, zda bylo téma vybráno — tuto kategorii extrahuj vždy. Hraniční případy se zapisují také, s `hranicni: true`.

### Jak strukturovat výstup
- Obsah se zapisuje **po videích** (jeden YAML soubor na video), stránky témat, osob a predikcí z něj skládá generátor — **tematické řazení zajišťují štítky `temata`**
- Každý výrok má 1..n témat ze `data/temata.yaml` (první = hlavní). Nové téma = nový záznam v `temata.yaml` (navigace se doplní sama); nezakládej téma, které už existuje pod jiným názvem
- Pokud video jen **opakuje** už zaznamenané tvrzení beze změny → krátký výrok (nadpis + 1 věta) s `vazby: [{na: <id původního výroku>, typ: opakovani}]`; text neopakuj
- Pokud tvrzení **posouvá** dřívější → plný výrok s `vazby: [{na: <id>, typ: posun}]`
- Pokud tvrzení z různých zdrojů **souhlasí** → `vazby: [{na: <id>, typ: souhlas}]`
- Pokud si **odporují** → zachovej obě verze, u novější `vazby: [{na: <id>, typ: konflikt}]` a v nadpisu „⚡ Konflikt: …“
- Id dřívějších výroků najdeš grepem v `data/zdroje/` (nadpisy, klíčová slova)

### Formát výroku

```yaml
vyroky:
- id: rajchl-2026-11-17-01        # mluvci-datum-pořadí (01, 02…), unikátní napříč archivem
  typ: tvrzeni                    # tvrzeni | postoj | predikce | stoch-teror
  temata: [politicky-system]      # slugy z data/temata.yaml, první = hlavní
  podtema: Volby 2025             # volitelné — kapitola na stránce tématu
  nadpis: Stručný název tvrzení nebo postoje (Mluvčí, D. M. YYYY)
  text: |
    Stručný popis (2–4 věty vlastními slovy, ne copy-paste). Odkazy na jiné výroky
    kořenově: [název](/temata/<slug>.md#<id-vyroku>), na zdroje [název](/zdroje/YYYY-MM.md#<id-zdroje>).
  citace:
  - text: Přesná citace, pokud stojí za zachování.
    cas: "12:34"                  # volitelné, časová značka z přepisu
  osoby:                          # zmíněné osoby a vztah mluvčího k nim
  - {osoba: babis, vztah: negativni, kontext: Označen za „herce“}
  vazby:                          # volitelné
  - {na: rajchl-2026-11-10-03, typ: posun}
  mluvci: pekova                  # volitelné — jen když mluví host, ne mluvčí kanálu
```

### Formát predikce

```yaml
- id: zitko-2026-11-13-04
  typ: predikce
  temata: [konspirace-deep-state-qanon]
  nadpis: Zítko — EBS a karanténa 3–33 dní (13. 11. 2026)
  text: Co konkrétně předpovídá (vlastními slovy, max 2 věty).
  citace:
  - text: Přesná citace.
  predikce:
    horizont: do cca 18. 12. 2026 (35 dní)   # slovně, jak zaznělo (nebo „neurčeno“)
    horizont_do: 2026-12-18                  # jen při jednoznačném datu; hlídá propadlé
    stav: ceka                               # ceka | potvrzeno | vyvraceno | castecne
```

**Vyhodnocení / doplnění starší predikce** (i když ho mluvčí sám komentuje v novějším videu): přidej položku do `vyhodnoceni` výroku **v jeho původním zdrojovém souboru** a případně změň `stav`:

```yaml
    vyhodnoceni:
    - {datum: 2026-11-20, text: „…“ — stav k datu, odkaz na nový zdroj, stav: vyvraceno}
```

Řazení (nejnovější nahoře) i přehled propadlých dělá generátor.

### Formát stochastického teroru

```yaml
- id: zitko-2026-11-14-07
  typ: stoch-teror
  temata: [covid-vakciny]
  nadpis: Válek „by měl skončit před vojenským tribunálem“
  text: Kontext výroku.
  citace:
  - text: „Takže tady další … by měl skončit před vojenským tribunálem.“
  teror:
    terc: Vlastimil Válek
    hranicni: false
```

### Zdroj (hlavička souboru)

```yaml
zdroj:
  id: 2026-11-17_rajchl_projev-k-17-listopadu   # = název souboru bez .yaml; YYYY-MM-DD_mluvci_ascii-slug-titulu
  mluvci: rajchl                  # slug z data/osoby.yaml
  kanal: Jindřich Rajchl (Facebook)
  titul: Projev k 17. listopadu
  datum: 2026-11-17               # skutečné datum vysílání (u ČsTV2 „vysílala živě“ ověř z úvodu přepisu)
  cas: "23:11"                    # volitelné
  url: https://www.facebook.com/…
  prepis: prepisy/done/2026-11-17_Jindřich-Rajchl_….txt   # cesta po přesunu do done/
  delka: "00:58:31"               # volitelné
  rezim: standard                 # standard | vrabel
  poznamka: Co bylo zpracováno, co přeskočeno, hraniční případy teroru, podle čeho (agent / ověřeno v přepisu).
vyroky: [...]
```

Soubor patří do adresáře podle data (`data/zdroje/2026/11/`), validace to kontroluje.

---

## Osoby (`data/osoby.yaml`) a stránky osob

Stránky mluvčích (`osoby/<slug>`) i zmíněných osob (`zminene/<slug>`) **generuje hook** z výroků — ručně se nic nepíše. Při zpracování:

- U každého výroku vyplň `osoby:` — kdo je zmiňován a s jakým vztahem mluvčího (`kontext` = 1 věta).
- Neznámou osobu přidej do `data/osoby.yaml` (`slug` = ASCII jméno, `jmeno`, případně `aliasy` pro zkomoleniny z přepisu, např. „Reichl“ = Rajchl). Nový **sledovaný** mluvčí dostane `sledovany: true, vlastni_stranka: true`; jednorázoví hosté/přednášející jen `vlastni_stranka: false`.
- Popis mluvčího na jeho stránce = `data/souhrny/osoby/<slug>.md` (mění se jen na vyžádání).

**Hodnoty vztahu:**
- `pozitivni` (✅) — mluví o osobě pochvalně, hájí ji, spolupracuje
- `negativni` (❌) — kritizuje, útočí, zpochybňuje
- `rozporuplny` (⚖️) — smíšené nebo situačně odlišné postoje
- `neutralni` (○) — zmiňuje fakticky bez hodnocení

**Časová osa vztahu** vzniká sama: každé video zapisuje své zmínky, starší se nemažou ani nepřepisují.

---

## Workflow při zpracování přepisu

1. Ověř, že soubor není v `wiki/prepisy/done/` (= již zpracován)
2. Přečti soubor z `wiki/prepisy/` (sekci PŘEPIS, METADATA pro atribuci)
3. Identifikuj témata → zobraz uživateli jako číslovaný seznam, každé s 1větným popisem (u Vrabela se neptej — viz specifika)
4. Čekej na výběr uživatele
5. **Pokud žádné téma nevybráno:** přesuň do `done/`, commitni, konec (u Ladislava Vrabela platí výjimka — viz krok 6a)
6. **Pokud témata vybrána:** zpracuj pouze vybraná témata
6a. **Výjimka — Ladislav Vrabel:** **všechna** témata videa zaznamenej jako krátké položky `prehled:`; plné výroky jen pro ⚡ témata. Viz „Ladislav Vrabel — specifika" výše.
7. Vytvoř `data/zdroje/YYYY/MM/<id>.yaml` — hlavička `zdroj:` + `vyroky:` (tvrzení, postoje, predikce, stochastický teror — ten vždy, bez ohledu na výběr témat) + u Vrabela `prehled:`
8. Nové osoby / témata doplň do `data/osoby.yaml` / `data/temata.yaml`
9. Vyhodnocení či doplnění starších predikcí zapiš do `vyhodnoceni` v jejich původních souborech
10. Přesuň přepis do `wiki/prepisy/done/` pomocí PowerShell `Move-Item` (cesta musí odpovídat poli `prepis:`)
11. `python -m tools.archiv.validate` → musí vypsat `OK` (schéma, slugy, unikátní id, existence přepisu, vazby)
12. Volitelně `mkdocs build -q` (ověří generování a odkazy)
13. Commit (`git add data wiki/prepisy`)

---

## Tón a styl

- Popisuj **co kdo tvrdí**, ne co je pravda ("X zastává názor, že..." vs. "X je pravda")
- Zachovej neutrální tón, i když tvrzení jsou kontroverzní
- Výstup vždy česky

---

## Publikování (MkDocs)

Push na `main` → automatický deploy přes `.github/workflows/deploy.yml` (`pip install -r requirements.txt`, `mkdocs gh-deploy`; stránky vygeneruje hook `tools/archiv/hook.py`). Lokální náhled: `mkdocs serve` (v `mkdocs.yml` je `watch: [data]`, ale na tomto stroji sledování změn souborů nefunguje — po změně dat server restartuj). Testy: `python -m pytest tests -q`.
