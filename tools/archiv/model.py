from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

TYPY = ("tvrzeni", "postoj", "predikce", "stoch-teror")
VZTAHY = ("pozitivni", "negativni", "rozporuplny", "neutralni")
VAZBY = ("posun", "opakovani", "konflikt", "souhlas")
STAVY = ("ceka", "potvrzeno", "vyvraceno", "castecne")
REZIMY = ("standard", "vrabel", "preskoceno")


@dataclass
class Citace:
    text: str
    cas: str | None = None


@dataclass
class OsobaRef:
    osoba: str
    vztah: str
    kontext: str = ""


@dataclass
class Vazba:
    na: str
    typ: str


@dataclass
class Vyhodnoceni:
    datum: date
    text: str
    stav: str | None = None


@dataclass
class Predikce:
    horizont: str
    stav: str = "ceka"
    horizont_do: date | None = None
    vyhodnoceni: list[Vyhodnoceni] = field(default_factory=list)


@dataclass
class Teror:
    terc: str
    hranicni: bool = False


@dataclass
class PrehledPolozka:
    tema: str
    text: str
    vyrok: str | None = None


@dataclass
class Vyrok:
    id: str
    typ: str
    temata: list[str]
    nadpis: str
    text: str
    citace: list[Citace] = field(default_factory=list)
    osoby: list[OsobaRef] = field(default_factory=list)
    vazby: list[Vazba] = field(default_factory=list)
    mluvci: str | None = None
    dalsi_zdroje: list[str] = field(default_factory=list)
    podtema: str | None = None
    predikce: Predikce | None = None
    teror: Teror | None = None


@dataclass
class Zdroj:
    id: str
    mluvci: str
    kanal: str
    titul: str
    datum: date
    url: str
    prepis: str
    rezim: str = "standard"
    cas: str | None = None
    delka: str | None = None
    poznamka: str | None = None
    osoby: list[OsobaRef] = field(default_factory=list)
    prehled: list[PrehledPolozka] = field(default_factory=list)
    vyroky: list[Vyrok] = field(default_factory=list)


@dataclass
class Tema:
    slug: str
    nazev: str
    popis: str = ""
    nadrazene: str | None = None


@dataclass
class Osoba:
    slug: str
    jmeno: str
    aliasy: list[str] = field(default_factory=list)
    popis: str = ""
    sledovany: bool = False
    vlastni_stranka: bool = False
