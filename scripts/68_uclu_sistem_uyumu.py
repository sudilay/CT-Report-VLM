# -*- coding: utf-8 -*-
"""BIMCV-R 317 seri: Astra, Sybil ve Pillar ciktilarinin birbiriyle ve
Ispanyolca raporla uyumu.

Uyum yalnizca ortusme sayisiyla olculmez. Pillar serilerin %30'unu isaretledigi
icin salt ortusme oranlari sisirilir; bu yuzden sansa gore duzeltilmis uyum
(Cohen kappa) ve pozitif uyum ayrica verilir.

Cikti:
  reports/uclu_uyum_tablolari.txt
  reports/uclu_uyum_ikili.csv
  reports/uclu_uyum_uclu_capraz.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "reports"
ESIK = 0.20
BOOTSTRAP = 4000
TOHUM = 20260909


# =========================================================================
# Uyum olculeri
# =========================================================================

def ikili_olcum(a, b):
    """Iki ikili karar arasindaki uyum olculeri."""
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    n = len(a)
    ikisi = int((a & b).sum())
    yalniz_a = int((a & ~b).sum())
    yalniz_b = int((~a & b).sum())
    ikisi_yok = int((~a & ~b).sum())

    gozlenen = (ikisi + ikisi_yok) / n
    # sansa dusen uyum
    beklenen = ((a.sum() * b.sum()) + ((~a).sum() * (~b).sum())) / (n * n)
    kappa = (gozlenen - beklenen) / (1 - beklenen) if beklenen < 1 else float("nan")
    # pozitif uyum: iki tarafin da pozitif dedigi / en az birinin pozitif dedigi
    birlesim = ikisi + yalniz_a + yalniz_b
    pozitif_uyum = ikisi / birlesim if birlesim else float("nan")

    return dict(ikisi=ikisi, yalniz_a=yalniz_a, yalniz_b=yalniz_b,
                ikisi_yok=ikisi_yok, gozlenen=gozlenen, kappa=kappa,
                pozitif_uyum=pozitif_uyum)


def kappa_ga(a, b, hasta, B=BOOTSTRAP, tohum=TOHUM):
    """Hasta duzeyinde kumeli bootstrap ile kappa guven araligi."""
    rng = np.random.default_rng(tohum)
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    hasta = np.asarray(hasta)
    tekil = np.unique(hasta)
    indeks = {h: np.where(hasta == h)[0] for h in tekil}
    degerler = []
    for _ in range(B):
        secim = rng.choice(tekil, len(tekil), replace=True)
        idx = np.concatenate([indeks[h] for h in secim])
        k = ikili_olcum(a[idx], b[idx])["kappa"]
        if not np.isnan(k):
            degerler.append(k)
    if not degerler:
        return float("nan"), float("nan")
    return tuple(np.percentile(degerler, [2.5, 97.5]))


def auc_hesapla(y, skor):
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(np.asarray(skor, float)).rank().values
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def spearman(x, y):
    return pd.Series(x).corr(pd.Series(y), method="spearman")


def kappa_yorumu(k):
    """Landis-Koch olceginin sade karsiligi."""
    if np.isnan(k):
        return "hesaplanamadi"
    if k < 0.01:
        return "yok denecek kadar az"
    if k < 0.20:
        return "cok zayif"
    if k < 0.40:
        return "zayif"
    if k < 0.60:
        return "orta"
    if k < 0.80:
        return "iyi"
    return "cok iyi"


# =========================================================================
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    satirlar = []

    def yaz(*p):
        s = " ".join(str(x) for x in p)
        print(s)
        satirlar.append(s)

    sinif = pd.DataFrame(json.load(
        open(CIKTI / "bimcv_317_siniflama.json", encoding="utf-8")))
    bulgu = pd.read_csv(CIKTI / "astra_bulgu_matrisi.csv")
    d = sinif.merge(bulgu, on="no", suffixes=("", "_b"))

    d["rapor_odak"] = d.es_nodul | d.es_kitle
    d["astra_odak"] = d.astra_nodul | d.astra_kitle
    d["sybil_ust"] = d.sybil1 >= ESIK
    d["pillar_ust"] = d.pillar1 >= ESIK

    hasta = d.hasta.values
    n = len(d)

    yaz("BIMCV-R %d seri / %d hasta   esik = %.2f" % (n, d.hasta.nunique(), ESIK))
    yaz("")
    yaz("Her sistemin kac seride 'lezyon var' dedigi:")
    yaz("  Ispanyolca rapor (nodul/kitle) : %d" % int(d.rapor_odak.sum()))
    yaz("  Astra (nodul/kitle)            : %d" % int(d.astra_odak.sum()))
    yaz("  Sybil (skor >= %.2f)            : %d" % (ESIK, int(d.sybil_ust.sum())))
    yaz("  Pillar (skor >= %.2f)           : %d" % (ESIK, int(d.pillar_ust.sum())))

    # ---------------------------------------------------------------
    # 1. Ikili uyum
    # ---------------------------------------------------------------
    ciftler = [
        ("Astra", "astra_odak", "Sybil", "sybil_ust"),
        ("Astra", "astra_odak", "Pillar", "pillar_ust"),
        ("Sybil", "sybil_ust", "Pillar", "pillar_ust"),
        ("Rapor", "rapor_odak", "Astra", "astra_odak"),
        ("Rapor", "rapor_odak", "Sybil", "sybil_ust"),
        ("Rapor", "rapor_odak", "Pillar", "pillar_ust"),
    ]
    yaz("")
    yaz("=== Ikili uyum ===")
    yaz("%-16s %6s %7s %7s %8s %8s %7s %-18s"
        % ("cift", "ikisi", "yalnA", "yalnB", "gozlenen", "kappa", "poz.uy", "yorum"))
    kayit = []
    for ad_a, kol_a, ad_b, kol_b in ciftler:
        o = ikili_olcum(d[kol_a], d[kol_b])
        lo, hi = kappa_ga(d[kol_a], d[kol_b], hasta)
        yaz("%-16s %6d %7d %7d %7.1f%% %8.3f %6.1f%% %-18s"
            % ("%s-%s" % (ad_a, ad_b), o["ikisi"], o["yalniz_a"], o["yalniz_b"],
               100 * o["gozlenen"], o["kappa"], 100 * o["pozitif_uyum"],
               kappa_yorumu(o["kappa"])))
        kayit.append(dict(cift="%s-%s" % (ad_a, ad_b), **o,
                          kappa_ga_alt=lo, kappa_ga_ust=hi,
                          yorum=kappa_yorumu(o["kappa"])))
    pd.DataFrame(kayit).to_csv(CIKTI / "uclu_uyum_ikili.csv", index=False,
                               encoding="utf-8-sig", float_format="%.4f")
    yaz("")
    yaz("kappa %95 guven araliklari (hasta kumeli bootstrap):")
    for r in kayit:
        yaz("  %-16s %.3f [%.3f, %.3f]" % (r["cift"], r["kappa"],
                                           r["kappa_ga_alt"], r["kappa_ga_ust"]))

    # ---------------------------------------------------------------
    # 2. Surekli skorlar
    # ---------------------------------------------------------------
    yaz("")
    yaz("=== Surekli skorlar ===")
    yaz("  Sybil - Pillar skor korelasyonu (Spearman): %.3f"
        % spearman(d.sybil1, d.pillar1))
    yaz("  Astra 'lezyon var' dedigi serilerde skorun siralama gucu:")
    yaz("    Sybil  AUC = %.3f" % auc_hesapla(d.astra_odak, d.sybil1))
    yaz("    Pillar AUC = %.3f" % auc_hesapla(d.astra_odak, d.pillar1))
    yaz("  Karsilastirma icin ayni skorun rapor lezyonuyla iliskisi:")
    yaz("    Sybil  AUC = %.3f" % auc_hesapla(d.rapor_odak, d.sybil1))
    yaz("    Pillar AUC = %.3f" % auc_hesapla(d.rapor_odak, d.pillar1))

    # skor medyanlari
    yaz("")
    yaz("  Astra lezyon diyor / demiyor ayriminda skor medyanlari:")
    for ad, kol in [("Sybil", "sybil1"), ("Pillar", "pillar1")]:
        var = d.loc[d.astra_odak, kol].median()
        yok = d.loc[~d.astra_odak, kol].median()
        yaz("    %-7s var=%.4f  yok=%.4f" % (ad, var, yok))

    # ---------------------------------------------------------------
    # 3. Uclu capraz
    # ---------------------------------------------------------------
    yaz("")
    yaz("=== Uclu capraz: rapor / Astra / skor esigi ===")
    for ad, kol in [("Sybil", "sybil_ust"), ("Pillar", "pillar_ust")]:
        yaz("-- %s" % ad)
        g = (d.groupby(["rapor_odak", "astra_odak", kol]).size()
             .rename("seri").reset_index())
        yaz(g.to_string(index=False))

    # kac sistem isaretledi
    yaz("")
    yaz("=== Raporda lezyon olan %d seride kac sistem isaretledi ===" % int(d.rapor_odak.sum()))
    alt = d[d.rapor_odak]
    sayi = (alt.astra_odak.astype(int) + alt.sybil_ust.astype(int)
            + alt.pillar_ust.astype(int))
    for k in range(4):
        yaz("  %d sistem: %d seri" % (k, int((sayi == k).sum())))

    yaz("")
    yaz("=== Raporda lezyon OLMAYAN %d seride kac sistem isaretledi ===" % int((~d.rapor_odak).sum()))
    alt2 = d[~d.rapor_odak]
    sayi2 = (alt2.astra_odak.astype(int) + alt2.sybil_ust.astype(int)
             + alt2.pillar_ust.astype(int))
    for k in range(4):
        yaz("  %d sistem: %d seri" % (k, int((sayi2 == k).sum())))

    capraz = d[["no", "hasta", "rapor_odak", "astra_odak", "sybil_ust",
                "pillar_ust", "sybil1", "pillar1"]]
    capraz.to_csv(CIKTI / "uclu_uyum_uclu_capraz.csv", index=False,
                  encoding="utf-8-sig")
    (CIKTI / "uclu_uyum_tablolari.txt").write_text("\n".join(satirlar),
                                                   encoding="utf-8")
    yaz("")
    yaz("Ciktilar reports/ altina yazildi.")


if __name__ == "__main__":
    main()
