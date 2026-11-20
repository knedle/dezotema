from __future__ import annotations

from datetime import date

from .model import Osoba, OsobaRef, Tema, Vyrok, Zdroj


class Archiv:
    def __init__(self, zdroje: list[Zdroj], temata: dict[str, Tema], osoby: dict[str, Osoba]):
        self.zdroje = zdroje
        self.temata = temata
        self.osoby = osoby
        self.vyroky: dict[str, tuple[Vyrok, Zdroj]] = {}
        for z in zdroje:
            for v in z.vyroky:
                self.vyroky[v.id] = (v, z)

    def _razene(self, dvojice):
        # stabilní řazení: nejnovější datum první, jinak pořadí načtení
        return sorted(dvojice, key=lambda vz: vz[1].datum, reverse=True)

    def _vse(self):
        return [(v, z) for z in self.zdroje for v in z.vyroky]

    def mluvci_vyroku(self, v: Vyrok, z: Zdroj) -> str:
        return v.mluvci or z.mluvci

    def podle_tematu(self, slug: str) -> list[tuple[Vyrok, Zdroj]]:
        return self._razene((v, z) for v, z in self._vse() if slug in v.temata)

    def podle_mluvciho(self, slug: str) -> list[tuple[Vyrok, Zdroj]]:
        return self._razene((v, z) for v, z in self._vse()
                            if self.mluvci_vyroku(v, z) == slug)

    def zminky_osoby(self, slug: str) -> list[tuple[OsobaRef, Vyrok | None, Zdroj]]:
        out: list[tuple[OsobaRef, Vyrok | None, Zdroj]] = []
        for z in self.zdroje:
            out += [(r, None, z) for r in z.osoby if r.osoba == slug]
            for v in z.vyroky:
                out += [(r, v, z) for r in v.osoby if r.osoba == slug]
        return sorted(out, key=lambda t: t[2].datum, reverse=True)

    def predikce(self) -> list[tuple[Vyrok, Zdroj]]:
        return self._razene((v, z) for v, z in self._vse()
                            if v.typ == "predikce" or v.predikce is not None)

    def teror(self) -> list[tuple[Vyrok, Zdroj]]:
        return self._razene((v, z) for v, z in self._vse()
                            if v.typ == "stoch-teror" or v.teror is not None)

    def nevyhodnocene_propadle(self, dnes: date) -> list[tuple[Vyrok, Zdroj]]:
        return [(v, z) for v, z in self.predikce()
                if v.predikce is not None and v.predikce.stav == "ceka"
                and v.predikce.horizont_do is not None and v.predikce.horizont_do < dnes]
