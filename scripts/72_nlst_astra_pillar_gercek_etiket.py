# -*- coding: utf-8 -*-
"""NLST: Astra rapor bulgusu ve Pillar skoru, GERCEK kanser etiketine karsi.

BIMCV'de zemin dogrusu radyoloji raporuydu ve bir kanser referansi degildi.
Burada `Kanser_Etiketi_y` gercek sonuc verisidir; bu yuzden bu olcum BIMCV
sonuclarinin nasil yorumlanacagini belirler.

BOLUNME KILIDI: olcum yalniz `train` uzerinde yapilir. `dev` ve `held_out`
acilmaz (configs/splits_astra.json · astra-split-1.0, on-ilan D98-D100).

Cikti: reports/nlst_gercek_etiket_olcumu.txt
"""
import ast
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
XLSX = KOK / "astra_radiology_reports_with_labels_all.xlsx"
SPLIT = KOK / "configs" / "splits_astra.json"
CIKTI = KOK / "reports"
BOOTSTRAP = 4000
TOHUM = 20260909


def astra_modulu():
    """67 numarali betikteki Ingilizce cikarim mantigini yeniden kullanir."""
    yol = KOK / "scripts" / "67_astra_rapor_karsilastirma.py"
    spec = importlib.util.spec_from_file_location("astra67", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def auc(y, s):
    y = np.asarray(y, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(np.asarray(s, float)).rank().values
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def kumeli_ga(y, s, hasta, B=BOOTSTRAP, tohum=TOHUM):
    rng = np.random.default_rng(tohum)
    y = np.asarray(y, bool)
    s = np.asarray(s, float)
    hasta = np.asarray(hasta)
    tekil = np.unique(hasta)
    idx = {h: np.where(hasta == h)[0] for h in tekil}
    v = []
    for _ in range(B):
        sec = rng.choice(tekil, len(tekil), replace=True)
        i = np.concatenate([idx[h] for h in sec])
        if y[i].sum() < 3 or (~y[i]).sum() < 3:
            continue
        a = auc(y[i], s[i])
        if not np.isnan(a):
            v.append(a)
    return (np.percentile(v, [2.5, 97.5]) if v else (float("nan"),) * 2)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cikti = []

    def yaz(*p):
        t = " ".join(str(x) for x in p)
        print(t)
        cikti.append(t)

    m = astra_modulu()
    d = pd.read_excel(XLSX)
    s = json.load(open(SPLIT, encoding="utf-8"))

    # --- bolunme filtresi ve train secimi ---
    filtre = d.Seri_Anahtari.isin(s["filtre"]["dislanan_seri_anahtarlari"])
    d = d[~filtre].copy()
    train_pid = {str(x) for x in s["bolunme"]["train"]["pid_listesi"]}
    d = d[d.PID.astype(str).isin(train_pid)].copy()
    yaz("Bolunme kilidi: %s" % s["surum"])
    yaz("train: %d seri / %d PID (kilitte %d / %d)"
        % (len(d), d.PID.nunique(), s["bolunme"]["train"]["seri"],
           s["bolunme"]["train"]["pid"]))
    yaz("dev ve held_out ACILMADI.")
    yaz("")

    # --- Pillar skoru ---
    d["P1"] = d.Pillar_Ensemble_Skoru.apply(lambda x: ast.literal_eval(x)[0])

    # --- Astra metninden odak lezyon ---
    odak = r"|".join([m.BULGULAR["nodul"]["en"], m.BULGULAR["kitle"]["en"]])
    d["astra_lezyon"] = [
        m.bulgu_var_mi(m.astra_torasik_metin(t), odak, m.EN_NEGASYON,
                       m.EN_NEG_KIRICI, m.cumleler_en,
                       toraks_filtre=m.astra_cumlesi_torasik,
                       ardil=m.EN_ARDIL_NEGASYON)
        for t in d.Radyoloji_Raporu]

    y = d.Kanser_Etiketi_y.astype(bool).values
    yaz("Kanser etiketi: %d / %d seri (%%%.1f)" % (y.sum(), len(y), 100 * y.mean()))
    yaz("Astra 'odak lezyon var': %d seri (%%%.1f)"
        % (d.astra_lezyon.sum(), 100 * d.astra_lezyon.mean()))
    yaz("")

    # --- Pillar ---
    yaz("=== PILLAR skoru, gercek kanser etiketine karsi ===")
    a = auc(y, d.P1)
    lo, hi = kumeli_ga(y, d.P1, d.PID.values)
    yaz("  seri duzeyi AUC = %.3f  %%95 GA [%.3f, %.3f]" % (a, lo, hi))
    yaz("  medyan skor: kanserli %.4f | kanserssiz %.4f"
        % (d.P1[y].median(), d.P1[~y].median()))
    yaz("  yil bazinda AUC:")
    for i in range(1, 7):
        yy = d["Kanser_Yil_%d" % i].astype(bool).values
        if yy.sum() >= 5:
            yaz("    Yil %d  poz=%3d  AUC=%.3f" % (i, yy.sum(), auc(yy, d.P1)))
    yaz("")

    # --- Astra ---
    yaz("=== ASTRA metin bulgusu, gercek kanser etiketine karsi ===")
    al = d.astra_lezyon.values
    tp, fp = int((al & y).sum()), int((al & ~y).sum())
    fn, tn = int((~al & y).sum()), int((~al & ~y).sum())
    yaz("  lezyon var / kanser var : %d" % tp)
    yaz("  lezyon var / kanser yok : %d" % fp)
    yaz("  lezyon yok / kanser var : %d" % fn)
    yaz("  lezyon yok / kanser yok : %d" % tn)
    yaz("  yakalama %.1f%%  |  temiz vakada sessiz kalma %.1f%%"
        % (100 * tp / max(1, tp + fn), 100 * tn / max(1, tn + fp)))
    yaz("  AUC (ikili) = %.3f" % auc(y, al.astype(float)))
    yaz("")

    # --- Pillar esikleri, Astra ile ayni alarm sayisinda ---
    yaz("=== Ayni alarm sayisinda karsilastirma ===")
    k = int(al.sum())
    esik = np.sort(d.P1.values)[::-1][k - 1] if k else np.nan
    pil = (d.P1 >= esik).values
    yaz("  Astra %d seriye alarm veriyor; Pillar'in ayni sayida alarm verdigi"
        " esik %.4f" % (k, esik))
    yaz("  Astra yakalama : %d/%d" % (tp, int(y.sum())))
    yaz("  Pillar yakalama: %d/%d" % (int((pil & y).sum()), int(y.sum())))
    yaz("")

    # --- birlikte ---
    yaz("=== Astra, Pillar'a ek katki saglıyor mu ===")
    for t in [0.2, 0.5]:
        p = (d.P1 >= t).values
        kac = (~p) & y
        yaz("  Pillar esik %.1f: kacirdigi %d kanser serisi" % (t, int(kac.sum())))
        yaz("    bunlardan Astra'nin isaretledigi: %d (%%%.1f)"
            % (int((kac & al).sum()), 100 * (kac & al).sum() / max(1, kac.sum())))
        temiz = (~p) & (~y)
        yaz("    Pillar'in dogru sessiz kaldigi %d seride Astra alarm: %d (%%%.1f)"
            % (int(temiz.sum()), int((temiz & al).sum()),
               100 * (temiz & al).sum() / max(1, temiz.sum())))

    (CIKTI / "nlst_gercek_etiket_olcumu.txt").write_text("\n".join(cikti),
                                                         encoding="utf-8")
    yaz("")
    yaz("Cikti: reports/nlst_gercek_etiket_olcumu.txt")


if __name__ == "__main__":
    main()
