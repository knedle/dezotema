# Datový archiv výroků — změna „střev“ DezoTema

Datum: 2026-11-20
Stav: návrh k odsouhlasení

## 1. Záměr a proč

DezoTema není primárně web. Je to **historický archiv toho, co kdo z vybrané scény kdy tvrdil**. Slouží jako podklad pro budoucí rozbory, které bude dělat uživatel nebo Claude za dobu X. Web je vedlejší produkt: když už se data zpracovávají, mohou se i zveřejnit.

Typické budoucí výstupy:

- **Profil osoby.** „Kdo je Zítko“: jeho pohled na svět, hlavní teze, jak se vyvíjely, vztahy k jiným osobám. Musí jít předat třetí straně s doložením zdrojů.
- **Tematický výběr.** Například „větrníky“: co všichni mluvčí k tématu říkali v čase.

Postup rozboru: „vezmi URL tématu nebo osoby a zpracuj“. Tematické a osobní stránky jsou tedy **předpřipravené souhrny pro bližší rozbor** a musí obsahovat všechny informace k dané osobě či tématu.

### Současný problém

Za 8 měsíců je to ~1000 přepisů a ~800 zpracovaných zdrojů. Současná struktura se rozjíždí:

- **Tematické stránky jsou obří a rostou jen přidáváním na konec.** Například `politicky-system.md` (300 kB, 172 sekcí). Nové výroky se lepí jako datované odstavce pod starší sekce, takže jedna sekce míchá více mluvčích i dnů.
- **Stránky osob se rozpadají.** `osoby/vrabel.md` má 500 kB, opakované nadpisy typu „(pokrač. 17)“ a tabulku zmíněných osob se stovkami řádků.
- **Obří jednostránkové seznamy.** `_zdroje.md` (560 kB), `predikce.md` (230 záznamů), `stochasticky-teror.md`.
- **Jeden údaj se zapisuje ručně na 3–5 místech** (téma, osoba, zdroje, predikce, u Vrabela denní přehled). To je pomalé a nekonzistentní.

Rozsekání na menší stránky by problém jen odložilo. Proto se mění samotný systém.

## 2. Cíle, ne-cíle, anti-cíle

**Cíle**

1. Jediný zdroj pravdy: **strukturovaná data výroků**. Každý výrok se zapíše jednou.
2. Všechny stránky (témata, osoby, predikce, stochastický teror, zdroje, Vrabelův přehled) se **generují** z dat.
3. Stránka tématu i osoby obsahuje **vše** k danému tématu či osobě v jedné URL (případně s automatickým členěním na podstránky), aby šla předat k rozboru.
4. Data jsou samostatně použitelná i bez webu (strojově čitelná, předatelná).
5. Celý dosavadní obsah se převede do nového formátu (plný převod).

**Ne-cíle**

- Zvyšování návštěvnosti, SEO, design webu.
- Databázový server nebo dynamický web. Zůstává statický MkDocs na GitHub Pages.
- Opětovné zpracování všech přepisů od nuly.

**Anti-cíle** (selhání, i kdyby to technicky fungovalo)

- Ztráta dat nebo atribuce při převodu: výrok bez mluvčího, data nebo zdroje.
- Zápis jednoho videa je pracnější než dnes.
- Formát, který znovu svádí k ručnímu přepisování na více místech.
- Neutrální tón a pravidla z CLAUDE.md (výběr témat uživatelem, stochastický teror vždy, Vrabelův režim) přestanou platit nebo se obejdou.

## 3. Omezení

- MkDocs Material, deploy přes GitHub Actions (`mkdocs gh-deploy`), docs_dir `wiki/`.
- Zápis dělá Claude v Claude Code na Windows (Bash i PowerShell, Python 3.13 dostupný).
- Přepisy zůstávají ve `wiki/prepisy/done/` a jsou dál servírované jako proklik ze zdrojů.
- Zpracování dál po jednom souboru, commit po každém, push na konci session (viz paměť).
- Současné kotvy a URL nemusí přežít, protože návštěvnost je minimální. Slugy témat a osob se ale ponechají stejné.

## 4. Zvažované přístupy

| | Přístup | Výhody | Nevýhody |
|---|---|---|---|
| **A** | **Jeden datový soubor na zpracovaný zdroj (YAML), stránky generované skriptem** | Odpovídá workflow 1 video → 1 zápis. Data jsou kompaktní a předatelná. Generátor může stránky libovolně členit. | Napsat generátor. Převést 8 měsíců obsahu. |
| B | Jeden výrok = jeden MD soubor s frontmatter, stránky přes MkDocs plugin a tagy | Čitelné přímo na GitHubu. | Tisíce souborů, 10–20 souborů na jedno video, slabší kontrola nad podobou stránek. |
| C | Ponechat MD, rozdělit témata podle čtvrtletí, osoby generovat parsováním | Nejlevnější. | Jen odloží problém, ruční vícenásobný zápis zůstane. |

**Zvoleno: A** (uživatel, 2026-11-20).

**Rozsah převodu: plný převod stávajícího obsahu** (uživatel, 2026-11-20). Zamítnuto: zmrazit staré stránky jako archiv (rozbory by musely číst dva formáty) a znovu zpracovat všechny přepisy (příliš drahé, ztratil by se uživatelův výběr témat).

## 5. Návrh

### 5.1 Adresářová struktura

```
data/
  zdroje/                    # 1 soubor = 1 zpracovaný zdroj (video/přepis)
    2026/11/2026-11-19_ladislav-vrabel_zpravy-v-devet.yaml
  temata.yaml                # číselník témat (slug, název, popis, nadřazené téma)
  osoby.yaml                 # číselník osob (slug, jméno, aliasy, popis, sledovaný mluvčí ano/ne)
  souhrny/                   # ručně/AI psané souhrny nad tématy a osobami (viz 5.5)
    temata/vetrniky.md
    osoby/zitko.md
tools/
  generate.py                # generátor stránek
  validate.py                # kontrola dat (schéma, existence slugů, duplicity id)
wiki/                        # docs_dir; generované stránky se sem zapisují při buildu
  prepisy/done/…             # beze změny
  (ručně psané stránky: index.md, o-strance.md, extra/…)
```

**Moje rozhodnutí:** Generované MD stránky **se necommitují**. Vznikají při buildu přes MkDocs hook (`hooks:` v mkdocs.yml), v CI i lokálně. V gitu jsou jen data, souhrny a ručně psané stránky. Generované cesty budou v `.gitignore`.

- Hook v `on_config` vygeneruje stránky a dosadí **navigaci** z číselníků. Ručně psaná navigace v `mkdocs.yml` zmizí, zůstanou jen ručně psané stránky.
- Při `mkdocs serve` se generuje jen tehdy, když se změnila data (porovnání mtime nebo hashe), a generované cesty se nesledují, aby nevznikla nekonečná smyčka přegenerování.
- `deploy.yml`: přidá se `pip install pyyaml` (a případně další knihovny). Hook najde `data/` a `tools/` relativně ke kořeni repozitáře. Jinak workflow zůstane stejné (`mkdocs gh-deploy`).

### 5.2 Datový model — soubor zdroje

```yaml
zdroj:
  id: 2026-11-19_ladislav-vrabel_zpravy-v-devet      # = název souboru
  mluvci: vrabel                                     # slug z osoby.yaml
  kanal: Ladislav Vrabel
  titul: "19. 11. 2026 Zprávy v devět s komentářem"
  datum: 2026-11-19            # skutečné datum vysílání (u ČsTV2 ověřit z obsahu)
  cas: "21:21"                 # volitelné
  url: https://www.facebook.com/…
  prepis: prepisy/done/2026-11-19_Ladislav-Vrabel_19-11-2026-Zprávy-v-devět-s-komentářem.txt
  delka: "01:14:08"
  rezim: standard              # standard | vrabel | preskoceno
  poznamka: "…"                # dnešní „Poznámka“ ze _zdroje.md
  prehled:                     # jen rezim: vrabel — denní přehled všech témat
    - tema: "Summit USA–Rusko–Čína"
      text: "…1 věta…"
      vyrok: vrabel-2026-11-19-01   # odkaz, pokud bylo plně zpracováno (⚡)

vyroky:
  - id: vrabel-2026-11-19-01   # mluvci-datum-pořadí, unikátní napříč archivem
    typ: tvrzeni               # tvrzeni | postoj | predikce | stoch-teror
    temata: [valka-nato-rusko]   # 1..n slugů; první = hlavní téma
    nadpis: "Po summitu Trump–Putin–Si: „nový světový pořádek“…"
    text: |                    # 2–6 vět vlastními slovy (dnešní styl)
      …
    citace:                    # 0..n
      - text: "Je to ukázka především toho, že tady máme nový světový pořádek…"
        cas: "04:47"
    osoby:                     # zmíněné osoby a vztah mluvčího k nim
      - {osoba: trump, vztah: rozporuplny, kontext: "„Putin je můj kamarád“ = USA nezasáhnou"}
    vazby:                     # volitelné: vztah k dřívějším výrokům
      - {na: vrabel-2026-11-14-03, typ: posun}   # posun | opakovani | konflikt | souhlas
    mluvci: vrabel             # volitelné přepsání (host, spolumluvčí); jinak ze zdroje

    # jen typ: predikce
    predikce:
      horizont: "po summitu APEC (od 19. 11. 2026)"
      horizont_do: 2026-12-07  # volitelné, strojově; slouží k hlídání propadlých
      stav: ceka               # ceka | potvrzeno | vyvraceno | castecne
      vyhodnoceni:             # 0..n datovaných poznámek
        - {datum: 2026-11-20, text: "…", stav: castecne}

    # jen typ: stoch-teror
    teror:
      terc: "Mikuláš Minář"
      hranicni: false
```

**Poznámky k modelu (moje rozhodnutí):**

- **Rozdělení `tvrzeni` a `postoj`** zachovává dnešní CLAUDE.md. Pokud se v praxi nebude rozlišovat, sloučí se (default `tvrzeni`).
- **Predikce a stochastický teror jsou výroky** se speciálním blokem, nejsou to samostatné seznamy. Stejný výrok tak může být zároveň tematickým tvrzením i predikcí (dnes se zapisuje dvakrát).
- **Hraniční případy stochastického teroru**, které se dnes jen zmiňují v poznámce zdroje, se zapisují jako `typ: stoch-teror` s `hranicni: true`. Generátor je zobrazí odděleně.
- **Opakované téma beze změny** (pravidlo z paměti: „jen přidat zdroj“) se zapíše jako krátký výrok s `vazby: [{typ: opakovani}]`, nadpisem a jednou větou. Text se neopakuje. Na stránce se zobrazí jako „opakuje (zdroj)“ pod původním výrokem.
- **Přeskočené soubory** (cizí řeč, gotcha rozhovory) dostanou zdrojový soubor s `rezim: preskoceno` a důvodem, bez výroků. Dnes nejsou nikde, jen v commitu. Generátor je ve zdrojích nezobrazí, nebo je zobrazí odděleně.

### 5.3 Číselníky

- `temata.yaml`: slug (= dnešní název souboru bez `.md`), název, popis (dnešní tabulka v index.md), volitelně `nadrazene` pro hierarchii (např. `konspirace-ceskoslovensko` pod `konspirace`). Podtémata (dnešní `##` kapitoly uvnitř stránek) se stanou **štítky** `podtemata` na výroku, nebo podtématy v číselníku. Rozhodne se při převodu podle četnosti.
- `osoby.yaml`: slug, jméno, aliasy (pro ASR zkomoleniny: „Reichl“ = Rajchl, „Siti Ping“ = Si Ťin-pching), popis, `sledovany: true/false` (mluvčí s vlastní stránkou a kanálem), `vlastni_stranka: true/false`. Pravidlo z paměti (hosté semináře nemají stránku osoby) se projeví jako `vlastni_stranka: false`.

### 5.4 Generované stránky

| Stránka | Obsah | Členění |
|---|---|---|
| **Téma** `/temata/<slug>/` | Souhrn (z `data/souhrny`, pokud existuje), pak výroky tématu chronologicky (nejnovější nahoře). Každý výrok: nadpis, mluvčí, datum, text, citace s časem, odkaz na zdroj a přepis, vazby. Nahoře přehled „kdo k tématu mluví“ (počty a odkazy) a filtr podle mluvčího. | Nad cca 150 výroků automaticky podstránky po rocích nebo čtvrtletích. Hlavní stránka ponechá souhrn a odkazy. |
| **Osoba (mluvčí)** `/osoby/<slug>/` | Souhrn, zdroje osoby, výroky seskupené podle témat (pro profil), časová osa, predikce osoby a jejich bilance (✅/❌/⚠️), stochastický teror osoby. | Stejně: po rocích, pokud přeroste. |
| **Osoba (zmíněná)** | Generuje se automaticky z `osoby:` napříč výroky: kdo o ní mluvil, jak (vztah v čase). Nahradí dnešní tabulky „Zmíněné osoby“. | — |
| **Predikce** | Tabulka všech predikcí (mluvčí, datum, horizont, stav), filtry a sekce „propadlé k vyhodnocení“ (`horizont_do` < dnes a stav `ceka`). | Podle stavu nebo měsíce. |
| **Stochastický teror** | Tabulka (dnešní formát), hraniční zvlášť. | — |
| **Zdroje** | Seznam zdrojů (dnešní obsah `_zdroje.md`), filtr podle mluvčího (dnešní `zdroje-filter.js`). | Po měsících. |
| **Vrabelův denní přehled** | Generuje se z `prehled:` v jeho zdrojích. | Po měsících (jako dnes). |
| **Index a navigace** | Generuje se z číselníků. | — |

**Kotvy:** každý výrok má kotvu `#<id>`, takže odkazy na výroky jsou stabilní a nezávislé na nadpisech.

**Export (moje rozhodnutí):** generátor navíc zapíše `wiki/data/vyroky.json` (všechny výroky s metadaty jedním souborem). To slouží pro budoucí rozbory i pro předání dat třetí straně.

### 5.5 Souhrny

Dnešní tematické stránky nejsou jen seznam výroků, mají i úvodní souhrnné odstavce (např. „Petr Pavel — hodnocení Jiřím Černohorským“). V novém systému:

- `data/souhrny/temata/<slug>.md` a `data/souhrny/osoby/<slug>.md` obsahují **volný text** (Markdown), který generátor vloží na začátek stránky.
- Souhrn píše nebo přepisuje Claude **na vyžádání** („obnov souhrn větrníků“), ne při každém videu. Souhrn uvádí datum poslední aktualizace a odkazuje na výroky přes `#id`.
- Při převodu se do souhrnů přesunou existující úvodní a obecné texty, které nejsou vázané na konkrétní zdroj.

### 5.6 Nový postup zpracování videa (změna CLAUDE.md)

1. Fáze 1 beze změny: přečíst přepis, nabídnout témata (u Vrabela bez ptaní).
2. Fáze 2: místo editace 3–5 MD stránek **vytvořit jeden soubor** `data/zdroje/YYYY/MM/<id>.yaml`. Obsahuje zdroj, výroky (vč. predikcí a stochastického teroru) a u Vrabela `prehled`.
3. Doplnit případné nové osoby nebo témata do číselníků.
4. Vyhodnocení starších predikcí = přidat položku do `vyhodnoceni` příslušného výroku (v jeho zdrojovém souboru).
5. `python tools/validate.py` (schéma, slugy, unikátní id, existence přepisu).
6. Přesunout přepis do `done/`, commit.

CLAUDE.md se přepíše tak, aby popisoval nový formát. Pravidla obsahu (neutrální tón, co extrahovat, stochastický teror vždy, výběr témat, Vrabelův režim, přeskakování cizí řeči) zůstávají.

### 5.7 Převod existujícího obsahu

Zdroj převodu: současné MD stránky. Témata, osoby, predikce a stochastický teror jsou primární, `_zdroje.md` dodá metadata zdrojů.

1. **Kostra:** skript vygeneruje zdrojové soubory z `_zdroje.md` (id, mluvčí, datum, URL, přepis, poznámka) a číselníky z existujících stránek a navigace.
2. **Výroky:** skript rozparsuje tematické stránky na jednotky: sekce `###` a uvnitř nich datované odstavce `**D. M.** —` a `**D. M. — Mluvčí**`. Každou jednotku přiřadí ke zdroji podle odkazů `_zdroje.md#…` v jejím „Zdroje:“. Tam, kde jednoznačné přiřazení selže (víc zdrojů na sekci bez datovaných odstavců), jednotku označí k ruční kontrole.
3. **Agenti:** nejasné jednotky, osoby (dnešní tabulky zmíněných osob → `osoby:` u výroků), predikce (→ blok `predikce`, stav a vyhodnocení), stochastický teror (→ výroky typu `stoch-teror`) a Vrabelovy denní přehledy (→ `prehled`). Agenti pracují v dávkách podle mluvčího a měsíce.
4. **Kontrola:** `validate.py` a srovnávací report: počty zdrojů, výroků, predikcí a stochastického teroru před a po převodu, zdroje bez výroků, osiřelé odkazy. Uživatel dostane vzorek (např. 1 téma a 1 osobu) ke kontrole, než se starý formát smaže.
5. **Přepnutí:** staré MD stránky se smažou až po kontrole a vygenerovaný web nahradí současný.

**Zmrazený stav (uživatel):** nová videa se zpracovávají jen na pokyn uživatele, takže převod běží nad zmrazeným stavem repozitáře. Převodní skript je **jednorázový**, nemusí se dát spouštět opakovaně. Zpracování nových přepisů a vyhodnocování predikcí se obnoví až po přepnutí, rovnou v novém formátu.

**Pravidla převodu (moje rozhodnutí):**

- **Texty se přenášejí doslova** z dnešních odstavců: nadpis, text, citace, zdroje. Nepřepisují se. Chybějící časové značky citací zůstanou prázdné.
- **Sloučené sekce s více zdroji** se rozdělí podle datovaných odstavců (`**D. M.** —`). Kde to nejde, vznikne jeden výrok v nejstarším zdroji s polem `dalsi_zdroje: [id, …]`. Pole je ve schématu povolené (nepovinné). Do budoucna se souhlas mezi zdroji zapisuje jako samostatné výroky s vazbou `souhlas`.
- **Nepřiřaditelné jednotky** se nezahazují. Půjdou do `data/zdroje/_nezarazeno.yaml` a do reportu. Přepnutí neblokují, pokud jich je řádově jednotky procent. Uživatel je uvidí v reportu.
- **Tabulky zmíněných osob** ze stránek osob se přiřadí k výroku téhož zdroje a podobného kontextu. Když to nejde jednoznačně, uloží se na úroveň zdroje do pole `zdroj.osoby` (schéma ho povoluje). Generované stránky osob čtou obojí.
- **Rozpočet:** primárně skript. Agenti dostanou jen nepřiřazené jednotky, tabulky osob, predikce a Vrabelovy přehledy, v dávkách podle mluvčího a měsíce.
- **Přepisy bez záznamu** (~200 souborů v `done/` bez sekce v `_zdroje.md`: přeskočené, duplicitní, bez vybraných témat) se z historie gitu **nedohledávají**. Generátor je pozná sám (přepis v `done/` bez datového souboru) a vypíše je na stránce zdrojů zvlášť jako „nezpracováno / přeskočeno“. Od přepnutí se přeskočené soubory zapisují jako `rezim: preskoceno` s důvodem.

### 5.8 Pořadí realizace

1. Schéma, číselníky, `validate.py`.
2. `generate.py` s MkDocs hookem a vzhledem stránek (téma, osoba, predikce, zdroje).
3. Pilotní převod jednoho mluvčího (např. Tarabová, malý objem) a jednoho tématu (větrníky). Ukázka uživateli.
4. Plný převod po dávkách.
5. Přepnutí, nový CLAUDE.md, aktualizace paměti.

## 6. Co je rozhodnuto kým

| Rozhodnutí | Kdo |
|---|---|
| Účel: datový archiv pro budoucí rozbory, web vedlejší | uživatel |
| Rozbory budou po osobách a tématech („vezmi URL a zpracuj“) | uživatel |
| Přístup A (data podle zdroje + generované stránky) | uživatel |
| Plný převod stávajícího obsahu | uživatel |
| YAML jako formát, generované stránky necommitovat, MkDocs hook | Claude |
| Predikce a stochastický teror jako typy výroků | Claude |
| Opakování jako krátký výrok s vazbou | Claude |
| Souhrny jako ruční/AI text, aktualizace na vyžádání | Claude |
| JSON export | Claude |
| Automatické členění velkých stránek po rocích/čtvrtletích (práh ~150 výroků) | Claude |
| Převod nad zmrazeným stavem, nová videa až po přepnutí (zpracování je vždy jen na pokyn uživatele) | uživatel |
| Texty se při převodu přenášejí doslova; sloučené sekce → `dalsi_zdroje`; nepřiřaditelné → `_nezarazeno` | Claude |
| Tabulky osob → výrok, jinak `zdroj.osoby` | Claude |
| Přeskočené přepisy z historie nedohledávat, generátor je odvodí | Claude |
| Navigace z hooku (`on_config`), `pyyaml` do deploy workflow | Claude |

## 7. Ponecháno na realizátorovi

- Přesná podoba šablon stránek (Markdown a CSS), práh členění.
- Implementace parseru pro převod a strategie dávek pro agenty.
- Knihovny (PyYAML, Jinja2 nebo čisté f-stringy), struktura `generate.py`.
- Zda podtémata modelovat v číselníku, nebo jako volné štítky (podle dat při převodu).
