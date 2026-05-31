# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Co je tento projekt

Tematická wiki názorů, postojů a tvrzení z přepisů videí a rozhovorů. Výstupem jsou MD soubory publikované přes MkDocs na GitHub Pages.

---

## Stav projektu (pilotní fáze)

- `wiki/prepisy/` — soubory čekající na zpracování
- `wiki/prepisy/done/` — přesunuté zpracované soubory (jsou v `_zdroje.md` jako `prepisy/done/…`)
- `wiki/` — existuje, obsahuje tematické MD soubory a podadresář `osoby/`
- `mkdocs.yml` — existuje, nakonfigurován

> `prepisy/` je uvnitř `wiki/` (docs_dir), aby MkDocs servoval `.txt` přepisy jako přímé prokliky ze `_zdroje.md`.

---

## Formát souborů v `wiki/prepisy/`

**Název souboru:** `YYYY-MM-DD_Jméno-Zdroje_Název-videa[_N].txt`

**Obsah souboru** má tři sekce oddělené `===`:
1. `METADATA` — obsahuje pole `Kanál:`, `Datum videa:`, `URL:`, aj.
2. `VÝKON` — technické info o přepisu (ignoruj)
3. `PŘEPIS` — samotný text s časovými značkami `[MM:SS]`

**Zdroje aktuálně v `wiki/prepisy/`:**
- `Jindřich-Rajchl`
- `Lenka-Tarabová`
- `Konspirátor-Boldy-KonspyChannel`
- `Československo-TV2`
- `Jiří-Černohorský-Živě`

Zdroj se identifikuje z části názvu souboru mezi prvním a druhým podtržítkem, nebo z pole `Kanál:` v METADATA.

---

## Výběr souborů ke zpracování

Uživatel vždy sdělí, kolik souborů nebo které konkrétní zpracovat. Bez pokynu nezačínej.

**Kontrola před zpracováním:** Soubor je zpracovaný, pokud se nachází v `wiki/prepisy/done/` nebo je uveden v `wiki/_zdroje.md`. Vybírej výhradně soubory v `wiki/prepisy/` (nikoliv `wiki/prepisy/done/`).

---

## Pravidla zpracování přepisů

### Fáze 1: Identifikace témat

Po přečtení souboru sestavíš seznam témat a zobrazíš ho uživateli jako **interaktivní checkboxy** (multiSelect). Uživatel zaškrtne, která témata zpracovat.

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

**Pokud uživatel nevybere žádné téma** → přesuň soubor do `done/` bez záznamu v `_zdroje.md` a bez jakýchkoli wiki úprav. Commitni se stručnou poznámkou.

### Co extrahovat (do vybraných témat)
- **Tvrzení** — konkrétní faktuální výroky ("X způsobuje Y", "Z funguje tak, že...")
- **Názory a postoje** — hodnotící výroky, přesvědčení, doporučení
- **Zajímavé citace** — přesné formulace hodné zachování (max 1–2 věty)
- **Predikce** — explicitní předpovědi budoucího vývoje ("za X měsíců nastane Y", "do voleb se stane Z", "Bitcoin dosáhne..."); zaznamenávej do `wiki/predikce.md`
- **Stochastický teror** — výroky splňující: **pojmenovaný terč** (konkrétní osoba nebo skupina) + **dehumanizace nebo výzva k trestu/násilí**; zaznamenávej do `wiki/stochasticky-teror.md` bez ohledu na to, zda bylo téma vybráno v checkboxech — tuto kategorii extrahuj vždy

### Jak strukturovat výstup
- Obsah organizuj **tematicky**, ne podle videí
- Každé téma = jeden MD soubor ve `wiki/`
- Pokud téma už existuje → **rozšiřuj**, nevytvářej duplicity
- Pokud tvrzení z různých zdrojů **souhlasí** → sluč je, přidej oba zdroje
- Pokud si **odporují** → zachovej obě verze, označ jako ⚡ Konflikt

### Formát záznamu v MD souboru

```markdown
## Název tématu / podtématu

### Tvrzení nebo název postoje

Stručný popis (2–4 věty vlastními slovy, ne copy-paste).

> „Přesná citace pokud stojí za zachování." — Jméno, [zdroj](_zdroje.md)

**Zdroje:** [Video 01](_zdroje.md#video-01), [Video 03](_zdroje.md#video-03)

---
```

### Formát záznamu predikce v `wiki/predikce.md`

```markdown
### [Mluvčí] — [Stručný název] (datum výroku)

**Předpověď:** Co konkrétně předpovídá (vlastními slovy, max 2 věty).

> „Přesná citace." — Jméno

**Horizont:** Do kdy / kdy má nastat (nebo „neurčeno")
**Stav:** 🕐 Čeká na vyhodnocení
**Zdroj:** [Název videa](_zdroje.md#anchor)

---
```

Záznamy řaď **od nejnovějšího výroku** (nejnovější nahoře).

### Soubor `_zdroje.md`

```markdown
## Název videa
- **Soubor:** [přepis](prepisy/done/YYYY-MM-DD_Zdroj_Název.txt)
- **Kanál:** ...
- **URL:** <https://...>
- **Datum záznamu:** ...
- **Zpracováno:** ano
```

---

## Stránky osob (`wiki/osoby/`)

Každý mluvčí má vlastní stránku v `wiki/osoby/[jmeno].md`. Stránka obsahuje:
- Stručný popis osoby
- Odkaz na zpracované zdroje v `_zdroje.md`
- Tabulku **témat** (které tematické stránky se jí týkají)
- Tabulku **zmíněných osob** — kdo je zmiňován, s jakým vztahem

### Formát tabulky zmíněných osob

```markdown
## Zmíněné osoby

| Osoba | Vztah | Kontext | Datum | Zdroj |
|-------|-------|---------|-------|-------|
| Mikuláš Minář | ❌ negativní | Označen za jednoho z největších lhářů v ČR | 2026-03-27 | [Kettner](../_zdroje.md#...) |
| Zdeněk Kettner | ✅ pozitivní | Obhajuje ho v kauze AI fotografie | 2026-03-27 | [Kettner](../_zdroje.md#...) |
```

**Symboly vztahu:**
- `✅ pozitivní` — mluví o osobě pochvalně, hájí ji, spolupracuje
- `❌ negativní` — kritizuje, útočí, zpochybňuje
- `⚖️ rozporuplný` — smíšené nebo situačně odlišné postoje
- `○ neutrální` — zmiňuje fakticky bez hodnocení

**Pravidlo aktualizace:** Pokud se vztah v novém přepisu změní nebo doplní, přidej **nový řádek** se stejnou osobou a novým datem — nesmazávej starý. Tím vzniká časová osa vývoje vztahu.

---

## Workflow při zpracování přepisu

1. Ověř, že soubor není v `wiki/prepisy/done/` (= již zpracován)
2. Přečti soubor z `wiki/prepisy/` (sekci PŘEPIS, METADATA pro atribuci)
3. Identifikuj témata → zobraz uživateli jako interaktivní checkboxy (multiSelect), každé s 1větným popisem
4. Čekej na výběr uživatele
5. **Pokud žádné téma nevybráno:** přesuň do `done/`, commitni, konec
6. **Pokud témata vybrána:** zpracuj pouze vybraná témata
7. Rozšiř existující nebo vytvoř nový MD soubor ve `wiki/`
8. Přidej záznam do `wiki/_zdroje.md` — soubor jako `[přepis](prepisy/done/název.txt)`, URL jako `<https://...>`
9. Přesuň soubor do `wiki/prepisy/done/` pomocí PowerShell `Move-Item`
10. Aktualizuj stránku mluvčího v `wiki/osoby/` — témata i zmíněné osoby
11. Přidej nalezené predikce do `wiki/predikce.md` (řazeno od nejnovějšího)
11a. Přidej výroky stochastického teroru do `wiki/stochasticky-teror.md` — vždy, bez ohledu na výběr témat
12. Aktualizuj `mkdocs.yml` nav sekci, pokud vznikl nový soubor

---

## Tón a styl

- Popisuj **co kdo tvrdí**, ne co je pravda ("X zastává názor, že..." vs. "X je pravda")
- Zachovej neutrální tón, i když tvrzení jsou kontroverzní
- Výstup vždy česky

---

## Publikování (MkDocs)

```bash
pip install mkdocs-material
mkdocs serve          # lokální náhled
mkdocs gh-deploy      # publikování na GitHub Pages
```

**`mkdocs.yml` šablona:**
```yaml
site_name: Wiki názorů
theme:
  name: material
  language: cs
  features:
    - navigation.tabs
    - search.suggest
docs_dir: wiki
nav:
  - Úvod: index.md
  - Zdroje: _zdroje.md
```

**GitHub Actions** (`.github/workflows/deploy.yml`) — automatický deploy při `git push` na `main`:
```yaml
name: Deploy wiki
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --force
```
