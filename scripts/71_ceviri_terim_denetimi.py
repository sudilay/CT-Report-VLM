# -*- coding: utf-8 -*-
"""Ispanyolca terimlerin makine cevirisindeki akibetini terim duzeyinde siniflar.

Her terim icin, terimin gectigi raporlarda Ingilizce karsiligin durumu dort
kategoriye ayrilir:

  dogru        : yerlesik Ingilizce radyoloji terimi metinde var
  ispanyolca   : sozcuk cevrilmeden Ispanyolca birakilmis
  bozuk        : bir karsilik uretilmis ama dogru terim degil
  yok          : kavram hicbir bicimde gecmiyor

Oncelik sirasi: dogru > ispanyolca > bozuk > yok. Yani raporda dogru terim bir
kez bile geciyorsa o rapor "dogru" sayilir.

Cikti: reports/ceviri_terim_denetimi.csv
"""
import sys
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
XLSX = KOK / "bimcv-analysis" / "BIMCV_Sybil_Pillar_Astra_317_Clean_Results.xlsx"
CIKTI = KOK / "reports"

# (turkce, ispanyolca desen, dogru Ingilizce terim, Ispanyolca kalinti, bozuk karsilik)
TERIMLER = [
    ("buzlu cam", "vidrio deslustrado", r"vidrio deslustrado|vidrio esmerilado",
     r"ground[- ]?glass", r"deslustrad\w*|esmerilad\w*", r"\bglass\b|\branting\b"),
    ("hiler bölge", "hiliar / hilio", r"\bhilio|hiliar",
     r"\bhilar\b|\bhilum\b", r"\bhilio\b|\bhiliar\b|hiliomediastinic\w*",
     r"hiliary|hilia\b|hiliomedia\w*"),
    ("plevral efüzyon", "derrame pleural", r"derrame pleural",
     r"pleural effusion|\beffusion\b", r"\bderrame\b", r"pleural spill|\bspill\w*"),
    ("perikardiyal efüzyon", "derrame pericárdico", r"derrame pericardico",
     r"pericardial effusion", r"\bderrame\b|pericardico", r"pericardic\w*|pericardium"),
    ("metastaz", "metástasis", r"metastasi\b|metastasis",
     r"\bmetastasis\b|\bmetastatic\b|\bmetastases\b", r"metastasico|metastasicas",
     r"goalsta\w*|tastasis"),
    ("nodül", "nódulo", r"\bnodulo\b|\bnodulos\b",
     r"\bnodule\b|\bnodules\b|\bnodular\b", r"\bnodulo\b|\bnodulos\b|\bnodulillos\b",
     r"nodulous|nodulum|\bnodes?\b"),
    ("fissür", "cisura", r"\bcisura", r"\bfissur\w*", r"\bcisura\w*", r"\bslit\b|\bcleft\b"),
    ("apeks", "vértice", r"\bvertice", r"\bapex\b|\bapical\b|\bvertex\b",
     r"\bvertice\w*", r"\bsummit\b|\btop\b"),
    ("amfizem", "enfisema", r"enfisema", r"emphysem\w*", r"\benfisema\b", r""),
    ("granülom", "granuloma", r"granulom", r"granulom\w*", r"", r""),
    ("parankim", "parénquima", r"parenquima", r"parenchym\w*", r"\bparenquima\b", r""),
    ("kalınlaşma", "engrosamiento", r"engrosamiento", r"thicken\w*",
     r"\bengrosamiento\w*", r""),
    ("bronşektazi", "bronquiectasias", r"bronquiectasi", r"bronchiectas\w*",
     r"\bbronquiectasi\w*", r""),
    ("konsolidasyon", "condensación", r"condensacion", r"consolidat\w*|condensat\w*",
     r"\bcondensacion\w*", r""),
    ("konsolidasyon", "consolidación", r"consolidacion", r"consolidat\w*",
     r"\bconsolidacion\w*", r""),
    ("adenopati", "adenopatías", r"adenopat", r"adenopath\w*|lymphadenopath\w*|lymph node\w*",
     r"\badenopatias\b", r"\bganglia\b"),
    ("kitle", "masa", r"\bmasa\b|\bmasas\b", r"\bmass\b|\bmasses\b", r"\bmasa\b", r""),
    ("atelektazi", "atelectasia", r"atelectasi", r"atelectas\w*", r"\batelectasia\b", r""),
    ("neoplazi", "neoplasia", r"neoplasi", r"neoplas\w*", r"", r""),
    ("spiküle", "espiculado", r"espiculad", r"spiculat\w*|speculat\w*", r"\bespiculad\w*", r""),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = pd.read_excel(XLSX, "Skorlar ve Raporlar")
    es = d.iloc[:, 17].astype(str)
    en = d.iloc[:, 18].astype(str)

    satirlar = []
    for tr, esp, rx_es, rx_dogru, rx_kalinti, rx_bozuk in TERIMLER:
        var = es.str.contains(rx_es, regex=True)
        n = int(var.sum())
        if n == 0:
            continue
        alt = en[var]
        dogru = alt.str.contains(rx_dogru, case=False, regex=True)
        kalinti = (alt.str.contains(rx_kalinti, case=False, regex=True)
                   if rx_kalinti else pd.Series(False, index=alt.index))
        bozuk = (alt.str.contains(rx_bozuk, case=False, regex=True)
                 if rx_bozuk else pd.Series(False, index=alt.index))
        # oncelik: dogru > ispanyolca > bozuk > yok
        k_dogru = int(dogru.sum())
        k_isp = int((~dogru & kalinti).sum())
        k_bozuk = int((~dogru & ~kalinti & bozuk).sum())
        k_yok = n - k_dogru - k_isp - k_bozuk
        satirlar.append(dict(turkce=tr, ispanyolca=esp, rapor=n,
                             dogru=k_dogru, ispanyolca_kalmis=k_isp,
                             bozuk_terim=k_bozuk, karsilik_yok=k_yok,
                             dogru_oran=round(100 * k_dogru / n, 1)))

    t = pd.DataFrame(satirlar).sort_values("dogru_oran")
    t.to_csv(CIKTI / "ceviri_terim_denetimi.csv", index=False, encoding="utf-8-sig")

    print("%-22s %-22s %5s %6s %8s %7s %6s %7s"
          % ("terim", "ispanyolca", "rapor", "dogru", "isp.kalmis", "bozuk", "yok", "dogru%"))
    for _, r in t.iterrows():
        print("%-22s %-22s %5d %6d %8d %7d %6d %6.0f%%"
              % (r.turkce, r.ispanyolca, r.rapor, r.dogru, r.ispanyolca_kalmis,
                 r.bozuk_terim, r.karsilik_yok, r.dogru_oran))

    print()
    print("TOPLAM terim gecisi: %d" % t.rapor.sum())
    for k, ad in [("dogru", "dogru cevrilmis"), ("ispanyolca_kalmis", "Ispanyolca kalmis"),
                  ("bozuk_terim", "bozuk terime cevrilmis"), ("karsilik_yok", "karsiligi yok")]:
        print("  %-26s %4d  (%%%.1f)" % (ad, t[k].sum(), 100 * t[k].sum() / t.rapor.sum()))


if __name__ == "__main__":
    main()
