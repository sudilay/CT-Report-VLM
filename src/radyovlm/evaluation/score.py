# -*- coding: utf-8 -*-
"""TASK-13 / C4: Altin aciklamaya karsi puanlama (K4-K10).

ESLESTIRME KURALLARI OLCUMDEN ONCE SABITLENDI (docs/10 bolum 5).
Sonucu gorup esleştirmeyi gevsetmek, esigi gevsetmekle ayni seydir.

  KATI  : kavram ayni VE aralik birebir
  GEVSEK: kavram ayni VE araliklar kesisiyor
  Ikisi de AYRI raporlanir - yalnizca kati sistemi haksiz dusuk gosterir,
  yalnizca gevsek sinir hatalarini gizler.

  Kesinlik atamalari (K6/K7) YALNIZCA eslesen varliklarda olculur; aksi hâlde
  varlik hatasi negasyon hatasi gibi gorunur.

  Eslestirme KONUMSALDIR, kume temelli degil: ayni kavramin iki anmasindan
  birini kacirmak duyarliligi dusurmelidir.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ------------------------------------------------------------------ eslestirme

@dataclass
class Span:
    bas: int
    son: int
    kavram: str
    ek: dict = field(default_factory=dict)


def _kesisiyor(a: Span, b: Span) -> bool:
    return a.bas < b.son and b.bas < a.son


def esle(altin: list[Span], sistem: list[Span], kati: bool) -> tuple[list, list, list]:
    """Konumsal eslestirme. Doner: (ciftler, kacirilan, fazladan).

    Her altin span EN FAZLA bir sistem span'ina eslenir ve tersi. Boylece
    ayni kavramin iki anmasindan birini kacirmak duyarliligi dusurur.
    """
    kalan = list(range(len(sistem)))
    ciftler, kacirilan = [], []
    for a in altin:
        bulundu = None
        for i in kalan:
            s = sistem[i]
            if s.kavram != a.kavram:
                continue
            uyar = (a.bas == s.bas and a.son == s.son) if kati else _kesisiyor(a, s)
            if uyar:
                bulundu = i
                break
        if bulundu is None:
            kacirilan.append(a)
        else:
            kalan.remove(bulundu)
            ciftler.append((a, sistem[bulundu]))
    return ciftler, kacirilan, [sistem[i] for i in kalan]


# --------------------------------------------------------------------- olcum

def kesinlik_duyarlilik(altin_hepsi, sistem_hepsi, kati: bool) -> dict:
    """K4 (kesinlik) ve K5 (duyarlilik). AYRI raporlanir - tek F1 sozluk
    cikariminin dogal asimetrisini (yuksek kesinlik, dusuk duyarlilik) gizler."""
    tp = fn = fp = 0
    bos_dogru = 0
    for a, s in zip(altin_hepsi, sistem_hepsi):
        if not a and not s:
            bos_dogru += 1          # ikisi de bos: dogru ama paydaya girmez
            continue
        c, kac, faz = esle(a, s, kati)
        tp += len(c)
        fn += len(kac)
        fp += len(faz)
    kes = tp / (tp + fp) if (tp + fp) else float("nan")
    duy = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * kes * duy / (kes + duy) if (kes == kes and duy == duy and kes + duy) else float("nan")
    return {"tp": tp, "fp": fp, "fn": fn, "kesinlik": kes, "duyarlilik": duy,
            "f1": f1, "bos_dogru": bos_dogru}


def makro_f1(ciftler: list[tuple], alan: str, siniflar: list[str]) -> dict:
    """Bir alan icin (assertion / temporality) makro-F1.

    YALNIZCA eslesen varliklar uzerinde (docs/10 bolum 5.2).
    """
    per = {}
    for s in siniflar:
        tp = sum(1 for a, y in ciftler if a.ek.get(alan) == s and y.ek.get(alan) == s)
        fp = sum(1 for a, y in ciftler if a.ek.get(alan) != s and y.ek.get(alan) == s)
        fn = sum(1 for a, y in ciftler if a.ek.get(alan) == s and y.ek.get(alan) != s)
        p = tp / (tp + fp) if (tp + fp) else float("nan")
        r = tp / (tp + fn) if (tp + fn) else float("nan")
        f = 2 * p * r / (p + r) if (p == p and r == r and p + r) else float("nan")
        per[s] = {"tp": tp, "fp": fp, "fn": fn, "p": p, "r": r, "f1": f,
                  "destek": tp + fn}
    gecerli = [v["f1"] for v in per.values() if v["f1"] == v["f1"]]
    dogru = sum(1 for a, y in ciftler if a.ek.get(alan) == y.ek.get(alan))
    return {"sinif": per,
            "makro_f1": sum(gecerli) / len(gecerli) if gecerli else float("nan"),
            "dogruluk": dogru / len(ciftler) if ciftler else float("nan"),
            "n": len(ciftler)}


def celdirici_denetimi(yargilar: list[dict]) -> dict:
    """Isaretleyici her seye 'dogru' mu diyor?

    Celdiriciler sistemin URETMEDIGI sahte adaylardir; 'H' denmeleri beklenir.
    Ret orani dusukse isaretleme guvenilmezdir ve K4/K6/K7 yorumlanamaz.
    """
    cel = [y for y in yargilar if y.get("sahte")]
    if not cel:
        return {"n": 0, "ret_orani": float("nan")}

    # DUZELTME (pilot sonrasi): ilk surum YALNIZCA dogru_varlik_mi'ye bakiyordu
    # ve ret oranini %54 gosterdi - oysa gercek %100'du.
    # Sebep: celdirici uretici cumleden RASTGELE kelime secip rastgele kavram
    # atiyor. O kelimelerin cogu ('pleura', 'lungs', 'lesion') GERCEKTEN varlik;
    # yanlis olan KAVRAM. Dogru cevap "varlik=E, kavram=H".
    # Bir celdirici, iki sorudan HERHANGI BIRINDE reddedilmisse yakalanmistir.
    def _reddedildi(y):
        v = str(y.get("dogru_varlik_mi", "")).strip().upper()
        kk = str(y.get("dogru_kavram_mi", "")).strip().upper()
        return v == "H" or kk == "H"

    ret = sum(1 for y in cel if _reddedildi(y))
    varlik_red = sum(1 for y in cel
                     if str(y.get("dogru_varlik_mi", "")).strip().upper() == "H")
    return {"n": len(cel), "ret": ret, "ret_orani": 100 * ret / len(cel),
            "varlik_red": varlik_red, "kavram_red": ret - varlik_red}


def olcut_durumu(deger: float, esik: float) -> str:
    if deger != deger:
        return "olculemedi"
    return "gecti" if deger >= esik else "KALDI"
