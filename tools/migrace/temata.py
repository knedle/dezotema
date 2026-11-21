"""Převod tematických stránek staré wiki na výroky (Task 6).

Jednotka = sekce `###` (nebo `##` bez podsekcí, pokud má vlastní „Zdroje:“); uvnitř se
dál dělí podle datovaných odstavců `**D. M.** — …`. Každá jednotka se přiřadí ke zdroji
podle odkazů `_zdroje.md#kotva` v sekci, data a mluvčího.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from urllib.parse import unquote

from tools.archiv.model import Citace, Osoba, Vyrok, Zdroj
from tools.archiv.slug import ascii_slug, slugify
from tools.migrace.ciselniky import ALIASY


@dataclass
class Jednotka:
    tema: str
    kapitola: str | None
    nadpis: str
    datum: date | None
    mluvci: str | None
    text: str
    citace: list[Citace] = field(default_factory=list)
    kotvy_zdroju: list[str] = field(default_factory=list)
    explicitni_kotva: str | None = None
    # doplňující údaje parseru
    den_mesic: tuple[int, int] | None = None     # datovaný odstavec bez známého roku
    uvod: bool = True                            # úvodní část sekce (ne datovaný odstavec)
    kvalifikator: str = ""                       # např. „Facebook Live“ z tučného štítku
    sekce: int = 0                               # pořadí sekce na stránce
    sekce_kotvy: list[str] = field(default_factory=list)
    kapitola_kotvy: list[str] = field(default_factory=list)
    # doplní prirad()
    dalsi_zdroje: list[str] = field(default_factory=list)
    mluvci_textu: str | None = None              # osoba mezi prvními slovy textu jednotky
    duvod: str = ""
    zpusob: str = ""
    vyrok_id: str | None = None                  # jen pro jednotku sloučenou pripoj_neprirazene()
    zdroje_radky: list[list[str]] = field(default_factory=list)  # kotvy po řádcích „Zdroje:“
    odstavce_mluvci: list[str | None] = field(default_factory=list)  # mluvčí začátku odstavců
    kapitola_datum: date | None = None           # datum / mluvčí z nadpisu nadřazené `##`
    kapitola_mluvci: str | None = None


# ---------------------------------------------------------------- mluvčí

def _bez_zavorek(s: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


# slova, která nejsou příjmením (z aliasů typu „Restart Česko“, „Jiří Černohorský Živě“)
_NE_PRIJMENI = {"cesko", "zive", "ping", "jinping", "channel", "konspychannel"}


def index_osob(osoby: dict[str, Osoba]) -> dict[str, str]:
    """Normalizované jméno / alias / příjmení -> slug osoby."""
    idx: dict[str, str] = {}
    prijmeni: dict[str, str] = {}
    for slug, o in osoby.items():
        jmena = [slug, o.jmeno, _bez_zavorek(o.jmeno), *o.aliasy, *ALIASY.get(slug, [])]
        for jm in jmena:
            k = ascii_slug(jm)
            if len(k) >= 3:
                idx.setdefault(k, slug)
            slova = _bez_zavorek(jm).split()
            if len(slova) >= 2:
                p = ascii_slug(slova[-1])
                if len(p) >= 4 and p not in _NE_PRIJMENI:
                    prijmeni.setdefault(p, slug)
    for k, v in prijmeni.items():
        idx.setdefault(k, v)
    return idx


def _osoba(text: str, idx: dict[str, str]) -> str | None:
    k = ascii_slug(text.strip(" „“\"':;,.!?—–-"))
    return idx.get(k) if k else None


def _osoba_volne(text: str, idx: dict[str, str], max_slov: int = 3) -> str | None:
    """Celý text, pak první 1–max_slov slova."""
    t = _bez_zavorek(text)
    o = _osoba(t, idx)
    if o:
        return o
    slova = re.split(r"[\s/]+", t.strip())
    for n in range(1, min(max_slov, len(slova)) + 1):
        o = _osoba(" ".join(slova[:n]), idx)
        if o:
            return o
    return None


# ---------------------------------------------------------------- data

_DATUM = re.compile(r"(\d{1,2})\.(?:\s?[–-]\s?\d{1,2}\.)?\s?(\d{1,2})\.\s?(\d{4})")
_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _datum_z(text: str) -> date | None:
    ms = list(_DATUM.finditer(text))
    for m in reversed(ms):
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
    m = _ISO.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _hlavicka(nadpis: str, idx: dict[str, str]) -> tuple[date | None, str | None]:
    t = re.sub(r"^⚡\s*Konflikt\s*[:—–-]\s*", "", nadpis).strip()
    datum = _datum_z(t)
    mluvci = None
    m = re.search(r"\(([^()]*)\)\s*$", t)
    if m:
        for cast in m.group(1).split(","):
            if _DATUM.search(cast) or re.fullmatch(r"\s*\d.*", cast):
                continue
            mluvci = _osoba_volne(cast, idx, 2)
            if mluvci:
                break
    if not mluvci and " — " in t:
        posledni = _bez_zavorek(t.rsplit(" — ", 1)[1])
        if " vs. " not in posledni:    # „Zítko/Konspirátor vs. Vrabel“ = spor, ne mluvčí
            mluvci = _osoba_volne(posledni, idx, 2)
    if not mluvci:
        prvni = re.split(r"\s+—\s+|:", t, maxsplit=1)[0]
        if prvni != t:
            mluvci = _osoba(prvni, idx)   # jen když je celý první úsek jménem („Boldy: …“)
    return datum, mluvci


# ---------------------------------------------------------------- odstavce

_DATOVANY = re.compile(
    r"^\*\*(?P<d>\d{1,2})\.\s?(?:[–-]\s?\d{1,2}\.\s?)?(?P<m>\d{1,2})\.(?:\s?(?P<y>\d{4}))?"
    r"(?P<rest>[^*]*)\*\*(?P<after>.*)$")
_DATOVANY_JMENO = re.compile(
    r"^\*\*(?:⚡\s*Konflikt\s*[—:–-]\s*)?(?P<who>[^*()\d]+?)\s*\((?P<d>\d{1,2})\.\s?(?P<m>\d{1,2})\."
    r"(?:\s?(?P<y>\d{4}))?(?P<rest>[^)]*)\):?\*\*(?P<after>.*)$")
_ZDROJE = re.compile(r"^\*\*Zdroje?:\*\*")
_KOTVA_ZDROJE = re.compile(r"_zdroje\.md#([^)\s]+)\)")
_CITACE = re.compile(r"^>\s*„(?P<q>.*)[“\"”]\s*(?:—\s*(?P<a>.*))?$")
_ODKAZ = re.compile(r"\[[^\]]*\]\([^)]*\)")
_EXPL = re.compile(r"\s*\{#([^}]+)\}\s*$")


@dataclass
class _Odstavec:
    d: int
    m: int
    y: int | None
    mluvci: str | None
    kvalifikator: str


def _datovany(radek: str, idx: dict[str, str]) -> _Odstavec | None:
    m = _DATOVANY.match(radek)
    if m:
        rest = m.group("rest").strip()
        mluvci, kval = None, []
        # „— Jméno (kvalifikátor)“ / „(Jméno, kvalifikátor)“
        for cast in re.split(r"[—–]", rest):
            cast = cast.strip(" :")
            if not cast:
                continue
            hlavni = _bez_zavorek(cast)
            if hlavni:
                o = _osoba_volne(hlavni, idx, 2)
                if o and not mluvci:
                    mluvci = o
                else:
                    kval.append(hlavni)
            for p in re.findall(r"\(([^)]*)\)", cast):
                for c in p.split(","):
                    o = _osoba(c, idx)
                    if o and not mluvci:
                        mluvci = o
                    elif c.strip():
                        kval.append(c.strip())
        if not mluvci:
            # „**1. 8.** — Zítko doplňuje …“: jméno mezi prvními slovy odstavce
            slova = re.sub(r"^[\s—–:-]+", "", m.group("after")).split()[:2]
            for s in slova:
                o = _osoba(s, idx)
                if o:
                    mluvci = o
                    break
        return _Odstavec(int(m.group("d")), int(m.group("m")),
                         int(m.group("y")) if m.group("y") else None, mluvci, " ".join(kval))
    m = _DATOVANY_JMENO.match(radek)
    if m:
        o = _osoba_volne(m.group("who"), idx, 2)
        if o:
            return _Odstavec(int(m.group("d")), int(m.group("m")),
                             int(m.group("y")) if m.group("y") else None, o,
                             m.group("rest").strip(" ,"))
    return None


def _cista_atribuce(a: str) -> str:
    a = _ODKAZ.sub("", a)
    a = re.sub(r"\s+a\s*$", "", a.strip())
    return a.strip(" ,;")


def _plain(nadpis: str) -> str:
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", nadpis)
    return t.replace("**", "").replace("`", "")


# ---------------------------------------------------------------- parser

def parsuj_stranku(md: str, tema_slug: str, osoby: dict[str, Osoba] | None = None) -> list[Jednotka]:
    idx = index_osob(osoby or {})
    md = md.lstrip("﻿")
    radky = md.splitlines()

    # bloky podle nadpisů; MkDocs-like id (attr_list {#…} nebo unikátní slug)
    bloky: list[tuple[int, str, list[str], list[str], str | None]] = []
    pouzite: set[str] = set()
    for r in radky:
        m = _EXPL.search(r)
        if re.match(r"^#{1,6} ", r) and m:
            pouzite.add(m.group(1))
    for r in radky:
        hm = re.match(r"^(#{1,6}) (.*)$", r)
        if hm:
            text = hm.group(2).strip()
            em = _EXPL.search(text)
            if em:
                nadpis = text[:em.start()].strip()
                kotvy, expl = [em.group(1)], em.group(1)
                s = slugify(_plain(nadpis))
                if s not in kotvy:
                    kotvy.append(s)
            else:
                nadpis, expl = text, None
                s0 = slugify(_plain(nadpis))
                s, n = s0, 0
                while s in pouzite:
                    n += 1
                    s = f"{s0}_{n}"
                pouzite.add(s)
                kotvy = [s]
            bloky.append((len(hm.group(1)), nadpis, kotvy, [], expl))
        elif bloky:
            bloky[-1][3].append(r)

    out: list[Jednotka] = []
    kapitola: str | None = None
    kap_kotvy: list[str] = []
    kap_hlav: tuple = (None, None)
    for i, (uroven, nadpis, kotvy, telo, explicitni) in enumerate(bloky):
        if uroven <= 2:
            kapitola, kap_kotvy = (nadpis, kotvy) if uroven == 2 else (None, [])
            kap_hlav = _hlavicka(nadpis, idx) if uroven == 2 else (None, None)
            if uroven == 1 or not any(_ZDROJE.match(r) for r in telo):
                continue  # úvod stránky / kapitoly bez zdrojů -> není jednotka
            kap = None
        elif uroven == 3:
            kap = kapitola
        else:
            continue
        sekce_j = _parsuj_sekci(tema_slug, kap, nadpis, telo, idx, i, kotvy, kap_kotvy,
                                explicitni)
        if uroven == 3:
            for j in sekce_j:
                j.kapitola_datum, j.kapitola_mluvci = kap_hlav
        out.extend(sekce_j)
    return out


def _parsuj_sekci(tema, kapitola, nadpis, telo, idx, sekce, kotvy, kap_kotvy, explicitni):
    h_datum, h_mluvci = _hlavicka(nadpis, idx)
    pool: list[str] = []
    ostatni: list[str] = []
    radky_zdroju: list[list[str]] = []
    for r in telo:
        if _ZDROJE.match(r):
            radky_zdroju.append([unquote(k) for k in _KOTVA_ZDROJE.findall(r)])
        cil = pool if _ZDROJE.match(r) else ostatni
        for k in _KOTVA_ZDROJE.findall(r):
            k = unquote(k)
            if k not in cil:
                cil.append(k)
    pool += [k for k in ostatni if k not in pool]

    def nova(datum, mluvci, uvod, dm=None, kval=""):
        return Jednotka(tema, kapitola, nadpis, datum, mluvci, "", [], list(pool), explicitni,
                        den_mesic=dm, uvod=uvod, kvalifikator=kval, sekce=sekce,
                        sekce_kotvy=list(kotvy) if uvod else [],
                        kapitola_kotvy=list(kap_kotvy),
                        zdroje_radky=[list(x) for x in radky_zdroju])

    jednotky = [nova(h_datum, h_mluvci, True)]
    texty: list[list[str]] = [[]]
    for r in telo:
        if _ZDROJE.match(r) or r.strip() == "---":
            continue
        od = _datovany(r, idx)
        if od:
            if od.y:
                d = _bezpecne(od.y, od.m, od.d)
            elif h_datum:
                d = _bezpecne(h_datum.year, od.m, od.d)
                if d and d < h_datum:
                    d = _bezpecne(h_datum.year + 1, od.m, od.d)
            else:
                d = None
            jednotky.append(nova(d, od.mluvci or h_mluvci, False,
                                 None if d else (od.d, od.m), od.kvalifikator))
            texty.append([r])
            continue
        cm = _CITACE.match(r)
        if cm:
            j = jednotky[-1]
            a = cm.group("a")
            if a is None:
                j.citace.append(Citace(cm.group("q")))
                continue
            atr = _cista_atribuce(a)
            kdo = _osoba(atr, idx) if atr else None
            if not atr or (kdo and (j.mluvci is None or kdo == j.mluvci)):
                if j.mluvci is None and kdo:
                    j.mluvci = kdo
                j.citace.append(Citace(cm.group("q")))
                continue
        texty[-1].append(r)

    out = []
    for j, t in zip(jednotky, texty):
        j.text = re.sub(r"\n{3,}", "\n\n", "\n".join(t)).strip()
        j.mluvci_textu = _mluvci_zacatku(j.text, idx)
        j.odstavce_mluvci = [_mluvci_zacatku(o, idx) for o in j.text.split("\n\n")]
        if j.uvod and not j.text and not j.citace:
            continue
        out.append(j)
    if out and not out[0].uvod:
        out[0].sekce_kotvy = list(kotvy)
    return out


def _mluvci_zacatku(text: str, idx: dict[str, str]) -> str | None:
    slova = re.sub(r"^\*\*[^*]*\*\*", "", text).lstrip(" —–:-").split()[:3]
    return next((o for o in (_osoba(w, idx) for w in slova) if o), None)


def _bezpecne(y, m, d) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


# ---------------------------------------------------------------- přiřazení

def _slova(text: str) -> set[str]:
    return {w[:4] for w in re.findall(r"[a-z0-9]+", ascii_slug(text).replace("-", " "))
            if len(w) >= 4 and not w.isdigit()}


def _skore(z: Zdroj, j: Jednotka) -> int:
    return len(_slova(z.titul) & _slova(j.kvalifikator + " " + j.text))


def _vyber(kand: list[Zdroj], j: Jednotka, pouzite: set[str]) -> Zdroj:
    """Nepoužitý před použitým, pak shoda slov titulu, pak pořadí."""
    return max(enumerate(kand), key=lambda iz: (iz[1].id not in pouzite, _skore(iz[1], j),
                                                -iz[0]))[1]


def prirad(jednotky: list[Jednotka], mapa: dict[str, str], zdroje_by_id: dict[str, Zdroj]
           ) -> tuple[list[tuple[Jednotka, str]], list[Jednotka]]:
    podle_md: dict[tuple[str, date], list[Zdroj]] = defaultdict(list)
    for z in zdroje_by_id.values():
        if isinstance(z.datum, date):
            podle_md[(z.mluvci, z.datum)].append(z)

    def globalne(j: Jednotka, datum: date, mluvci: str | None = None) -> list[Zdroj]:
        """Zdroj mimo odkazy sekce: stejný mluvčí a datum (±1 den) v celém archivu."""
        mluvci = j.mluvci or j.mluvci_textu or mluvci
        if not mluvci:
            return []
        for delta in (0, -1, 1):
            k = podle_md.get((mluvci, datum + timedelta(days=delta)), [])
            if k:
                return sorted(k, key=lambda z: z.id)
        return []

    vysledek: dict[int, str] = {}
    sekce: dict[tuple[str, int], list[int]] = defaultdict(list)
    for n, j in enumerate(jednotky):
        sekce[(j.tema, j.sekce)].append(n)
    presunute = _oprav_presunute_radky(jednotky, sekce, mapa, zdroje_by_id)
    navic: dict[int, list[tuple[Jednotka, str]]] = defaultdict(list)

    for cleny in sekce.values():
        prvni = jednotky[cleny[0]]
        pool = []
        for k in prvni.kotvy_zdroju:
            zid = mapa.get(k)
            if zid in zdroje_by_id and zid not in [z.id for z in pool]:
                pool.append(zdroje_by_id[zid])
        pouzite: set[str] = set()
        roky = Counter(z.datum.year for z in pool)

        # 1) datované odstavce
        for n in cleny:
            j = jednotky[n]
            if j.uvod:
                continue
            if j.datum is None and j.den_mesic:
                d, m = j.den_mesic
                shoda = [z.datum.year for z in pool if (z.datum.day, z.datum.month) == (d, m)]
                rok = shoda[0] if shoda else (roky.most_common(1)[0][0] if roky else None)
                j.datum = _bezpecne(rok, m, d) if rok else None
            if j.datum is None:
                j.duvod = "datovaný odstavec bez určitelného data"
                continue
            kand: list[Zdroj] = []
            # rok odhadnutý z nadpisu (+1 při „přetočení“) se ověří proti zdrojům sekce
            alternativy = [j.datum] + [x for x in (_bezpecne(j.datum.year - 1, j.datum.month,
                                                              j.datum.day),) if x]
            for datum in alternativy:
                for delta in (0, -1, 1):
                    dd = datum + timedelta(days=delta)
                    kand = [z for z in pool
                            if z.datum == dd and (j.mluvci is None or z.mluvci == j.mluvci)]
                    if kand:
                        j.zpusob = "datum" if delta == 0 else "datum±1"
                        j.datum = datum
                        break
                if kand:
                    break
            if not kand:
                kand = globalne(j, j.datum)
                j.zpusob = "globalne"
            if not kand and j.mluvci:
                # mluvčí odhadnutý chybně? Zdroj sekce se stejným datem (autor ho uvedl)
                for delta in (0, -1, 1):
                    dd = j.datum + timedelta(days=delta)
                    kand = [z for z in pool if z.datum == dd]
                    if kand:
                        j.zpusob = "datum-jiny-mluvci"
                        j.mluvci = j.mluvci_textu
                        break
            if not kand:
                j.duvod = (f"žádný zdroj s datem {j.datum} a mluvčím {j.mluvci} "
                           f"(sekce má {len(pool)} zdrojů)")
                continue
            z = _vyber(kand, j, pouzite)
            pouzite.add(z.id)
            vysledek[n] = z.id

        # 2) úvodní část
        for n in cleny:
            j = jednotky[n]
            if not j.uvod:
                continue
            s_mluvcim = [z for z in pool if j.mluvci is None or z.mluvci == j.mluvci]
            kand = []
            if j.datum:
                for delta in (0, -1, 1):
                    dd = j.datum + timedelta(days=delta)
                    kand = [z for z in s_mluvcim if z.datum == dd]
                    if kand:
                        j.zpusob = "uvod-datum"
                        break
            if not kand:
                volne = [z for z in s_mluvcim if z.id not in pouzite] or s_mluvcim
                if volne:
                    nej = min(z.datum for z in volne)
                    kand = [z for z in volne if z.datum == nej]
                    j.zpusob = "uvod-nejstarsi"
            if not kand and j.datum:
                kand = globalne(j, j.datum)
                j.zpusob = "globalne"
            if not kand and not pool and j.kapitola_datum:
                # sekce bez odkazů: datum a mluvčí z nadřazeného nadpisu `##`
                kand = globalne(j, j.kapitola_datum, j.kapitola_mluvci)
                j.zpusob = "kapitola"
            if not kand and pool and j.mluvci:
                # host / jiný mluvčí ve zdroji jiné osoby: nejstarší zdroj sekce, mluvčí se přepíše
                volne = [z for z in pool if z.id not in pouzite] or pool
                nej = min(z.datum for z in volne)
                kand = [z for z in volne if z.datum == nej]
                j.zpusob = "uvod-jiny-mluvci"
                # mluvčí z nadpisu není u žádného zdroje sekce (host): přednost má jméno
                # na začátku textu, jinak zůstává mluvčí z nadpisu
                j.mluvci = j.mluvci_textu or j.mluvci
            if not kand:
                j.duvod = ("sekce bez odkazu na zdroj" if not pool else
                           f"žádný zdroj sekce neodpovídá mluvčímu {j.mluvci}")
                continue
            z = _vyber(kand, j, pouzite)
            pouzite.add(z.id)
            vysledek[n] = z.id
            if n in presunute:
                j.zpusob = "presunuty-radek-zdroju"
            # odstavec jiného mluvčího uvnitř úvodu -> vlastní jednotka pro jeho zdroj sekce
            vlastni = j.mluvci or z.mluvci
            for ciz in [x for x in pool if x.id not in pouzite and x.mluvci != vlastni]:
                nova = _oddel_odstavce(j, ciz)
                if nova is not None:
                    pouzite.add(ciz.id)
                    navic[n].append((nova, ciz.id))

        # 3) zbylé zdroje sekce -> dalsi_zdroje první přiřazené jednotky (přednostně úvodu)
        prirazene_cleny = [n for n in cleny if n in vysledek]
        if prirazene_cleny:
            hlavni = next((n for n in prirazene_cleny if jednotky[n].uvod), prirazene_cleny[0])
            for z in pool:
                if z.id not in pouzite and z.id not in jednotky[hlavni].dalsi_zdroje:
                    jednotky[hlavni].dalsi_zdroje.append(z.id)

    prirazene = []
    for n, j in enumerate(jednotky):
        if n in vysledek:
            prirazene.append((j, vysledek[n]))
            prirazene.extend(navic.get(n, []))
    neprirazene = [j for n, j in enumerate(jednotky) if n not in vysledek]
    return prirazene, neprirazene


def _oprav_presunute_radky(jednotky, sekce, mapa, zdroje_by_id) -> set[int]:
    """Řádek „Zdroje:“ omylem pod následující sekcí: sekce bez odkazů, další sekce téže
    stránky má víc řádků Zdroje a některý z nich patří jen mluvčímu předchozí sekce.
    Kotvy se přesunou (mění jednotky na místě). Vrací indexy jednotek, které je dostaly."""
    klice = list(sekce)
    out: set[int] = set()
    for a, b in zip(klice, klice[1:]):
        if a[0] != b[0]:
            continue
        pa, pb = jednotky[sekce[a][0]], jednotky[sekce[b][0]]
        if pa.kotvy_zdroju or len(pb.zdroje_radky) < 2:
            continue
        mluvci_a = pa.mluvci or pa.mluvci_textu
        mluvci_b = pb.mluvci or pb.mluvci_textu
        if not mluvci_a or mluvci_a == mluvci_b:
            continue
        for radek in reversed(pb.zdroje_radky):
            zz = [zdroje_by_id.get(mapa.get(k)) for k in radek]
            if radek and all(z is not None and z.mluvci == mluvci_a for z in zz):
                for n in sekce[a]:
                    jednotky[n].kotvy_zdroju = list(radek)
                    out.add(n)
                for n in sekce[b]:
                    jednotky[n].kotvy_zdroju = [k for k in jednotky[n].kotvy_zdroju
                                                if k not in radek]
                break
    return out


def _oddel_odstavce(j: Jednotka, ciz: Zdroj) -> Jednotka | None:
    """Odstavce úvodu začínající jménem mluvčího zdroje `ciz` (ne první odstavec) se oddělí
    do nové jednotky; končí před odstavcem, který začíná jiným jménem."""
    odst = j.text.split("\n\n")
    mluv = j.odstavce_mluvci if len(j.odstavce_mluvci) == len(odst) else [None] * len(odst)
    k = next((i for i in range(1, len(odst)) if mluv[i] == ciz.mluvci), None)
    if k is None:
        return None
    m = next((i for i in range(k + 1, len(odst)) if mluv[i] and mluv[i] != ciz.mluvci),
             len(odst))
    nova = replace(j, uvod=False, mluvci=ciz.mluvci, text="\n\n".join(odst[k:m]), citace=[],
                   datum=ciz.datum, den_mesic=None, sekce_kotvy=[], dalsi_zdroje=[],
                   odstavce_mluvci=mluv[k:m], zpusob="odstavec-jineho-mluvciho",
                   mluvci_textu=ciz.mluvci)
    zbytek = odst[:k] + odst[m:]
    j.text = "\n\n".join(zbytek)
    j.odstavce_mluvci = mluv[:k] + mluv[m:]
    return nova


# ---------------------------------------------------------------- výroky

def na_vyrok(j: Jednotka, zdroj: Zdroj, poradi: int | str) -> Vyrok:
    mluvci = j.mluvci or zdroj.mluvci
    cislo = f"{poradi:02d}" if isinstance(poradi, int) else poradi
    return Vyrok(
        id=f"{mluvci}-{zdroj.datum.isoformat()}-{cislo}",
        typ="tvrzeni",
        temata=[j.tema],
        nadpis=j.nadpis,
        text=j.text,
        citace=list(j.citace),
        mluvci=j.mluvci if j.mluvci and j.mluvci != zdroj.mluvci else None,
        dalsi_zdroje=[d for d in j.dalsi_zdroje if d != zdroj.id],
        podtema=j.kapitola,
    )


@dataclass
class Sestaveni:
    vyroky: dict[str, list[Vyrok]]            # id zdroje -> nové výroky
    id_jednotek: list[str]                    # id výroku pro každý vstupní pár (stejné pořadí)
    slouceno: int = 0                         # druhé výskyty sloučené do existujícího výroku
    slouceno_jiny_text: int = 0               # … z toho s odlišným textem


def sestav_vyroky(prirazene: list[tuple[Jednotka, str]], zdroje_by_id: dict[str, Zdroj],
                  obsazena: set[str] | None = None) -> Sestaveni:
    obsazena = set(obsazena or ())
    citac: Counter = Counter()
    podle_klice: dict[tuple[str, str], list[Vyrok]] = defaultdict(list)
    out = Sestaveni(defaultdict(list), [])
    for j, zid in prirazene:
        z = zdroje_by_id[zid]
        existujici = next((v for v in podle_klice[(j.nadpis, zid)] if j.tema not in v.temata),
                          None)
        if existujici is not None:
            existujici.temata.append(j.tema)
            for d in j.dalsi_zdroje:
                if d != zid and d not in existujici.dalsi_zdroje:
                    existujici.dalsi_zdroje.append(d)
            out.slouceno += 1
            if existujici.text.strip() != j.text.strip():
                out.slouceno_jiny_text += 1
            out.id_jednotek.append(existujici.id)
            continue
        mluvci = j.mluvci or z.mluvci
        klic = (mluvci, z.datum)
        citac[klic] += 1
        v = na_vyrok(j, z, citac[klic])
        base, suf = v.id, iter("bcdefghijklmnopqrstuvwxyz")
        while v.id in obsazena:
            v.id = base + next(suf)
        obsazena.add(v.id)
        podle_klice[(j.nadpis, zid)].append(v)
        out.vyroky[zid].append(v)
        out.id_jednotek.append(v.id)
    return out


def pripoj_neprirazene(neprirazene: list[Jednotka], s: Sestaveni) -> list[Jednotka]:
    """Nepřiřazená jednotka se stejným nadpisem jako (jednoznačně) jeden výrok z jiné stránky
    = kopie téže sekce bez odkazu na zdroj: přidá se jen téma. Vrací zbylé nepřiřazené."""
    podle_nadpisu: dict[str, list[Vyrok]] = defaultdict(list)
    for vs in s.vyroky.values():
        for v in vs:
            podle_nadpisu[v.nadpis].append(v)
    zbytek = []
    for j in neprirazene:
        kand = [v for v in podle_nadpisu.get(j.nadpis, []) if j.tema not in v.temata]
        if len(kand) == 1:
            kand[0].temata.append(j.tema)
            j.zpusob = "nadpis-jine-stranky"
            j.vyrok_id = kand[0].id
            s.slouceno += 1
            if kand[0].text.strip() != j.text.strip():
                # odlišný text se nesmí ztratit: zůstává i v nepřiřazených k ruční kontrole
                s.slouceno_jiny_text += 1
                j.duvod = (f"kopie sekce bez zdroje s odlišným textem; téma připojeno "
                           f"k výroku {kand[0].id}")
                zbytek.append(j)
        else:
            zbytek.append(j)
    return zbytek
