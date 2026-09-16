"""SUDE-VLM-34 denetim duzeltmeleri.

Bagimsiz denetimin alti bulgusuna karsilik gelen yeniden analizler:

A. ESTIMAND. "Hasta duzeyi = taramalarin maksimumu" tek-BT tahmini degildir; izlem
   boyunca HERHANGI bir taramada alarm verilmesini olcer. Uc estimand yan yana konur:
     - tarama basina (seri)      : tek BT'den 1 yillik risk; yayimlanmis Sybil ile ayni soru
     - indeks BT (en erken tarama): hasta basina TEK gozlem, kumelenme yok
     - hasta-max (herhangi bir yil): izlem boyunca en az bir alarm

B. SPLIT. astra-split-1.0 yalniz filtre olarak kullanilmisti; train/dev/held_out
   uyeligi degerlendirmede kullanilmamisti. Burada probe TRAIN'de egitilir, esik
   DEV'de sabitlenir, HELD-OUT'ta bir kez olculur.
   Uyari: held-out'ta 1. yil pozitifi 6 PID'dir (kilitteki 11, 6 yillik sayidir).

C/D. PILLAR ikincil baseline olarak FP/FN tablosuna geri alinir; Sybil ve Pillar'in
   FN kumeleri vaka duzeyinde karsilastirilir.

E. KUCUK EK BUTCELER. +428 ek alarm kohortun %71,5'ine alarm demekti; +10/+25/+50/+100
   gibi gerceklci butceler eklenir.

F. 2-6 YIL. Ileri yillarda tani alan seriler analiz disi birakilmaz; resmi Mask
   kolonlariyla ayri bir gelecek-risk analizi yapilir.

Cikti: outputs/vlm34/denetim_duzeltmeleri.json, ozet_denetim.txt, sekil_8_*.svg/png
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

KOK = Path(__file__).resolve().parents[1]
BASE = KOK / "data/external/model_benchmarks_v4"
CIKTI = KOK / "outputs/vlm34"
TOHUMLAR = [0, 1, 2, 3, 4]
SYBIL_ESIK = 0.20
BOOTSTRAP = 2000

rapor: dict = {}
satirlar: list[str] = []


def yaz(s: str = "") -> None:
    print(s)
    satirlar.append(s)


def kaydet(fig, ad: str) -> None:
    """SVG + PNG yaz. SVG'den DOCTYPE/DTD temizlenir: SVG 1.1 DTD kullanim disi ve
    DTD tasiyan XML bazi tuketicilerce (artifact yayimlama) reddediliyor."""
    for uz in ("svg", "png"):
        fig.savefig(CIKTI / f"{ad}.{uz}", bbox_inches="tight")
    p = CIKTI / f"{ad}.svg"
    p.write_text(re.sub(r"<!DOCTYPE[^>]*>\s*", "", p.read_text(encoding="utf-8")),
                 encoding="utf-8")


# --------------------------------------------------------------------------
# Veri
# --------------------------------------------------------------------------
df = pd.read_csv(CIKTI / "seri_skorlari.csv", dtype={"patient_id": str, "tarama_yili": str})
kilit = json.loads((KOK / "configs/splits_astra.json").read_text(encoding="utf-8"))
xl = pd.read_excel(KOK / "astra_radiology_reports_with_labels_all.xlsx")
xl = xl.set_index("Seri_Anahtari").loc[df["series_key"]].reset_index()
kanser_yil = xl[[f"Kanser_Yil_{i}" for i in range(1, 7)]].to_numpy(float)
mask_yil = xl[[f"Mask_Yil_{i}" for i in range(1, 7)]].to_numpy(float)

sp_npz = np.load(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_embeddings.npz",
                 allow_pickle=True)
keys_ham = np.array([str(s) for s in sp_npz["series_keys"]])
konum = pd.Series(np.arange(len(keys_ham)), index=keys_ham).loc[df["series_key"]].to_numpy()
EMB = {
    "SPECTRE": sp_npz["cls_embeds"][konum],
    "M3D": np.load(BASE / "m3d/nlst_full_cohort_2965/m3d_nlst_full_2965_embeddings.npz",
                   allow_pickle=True)["embeddings"][konum],
    "MG-3D": np.load(BASE / "mg3d/nlst_full_cohort_2965/mg3d_nlst_full_2965_embeddings.npz",
                     allow_pickle=True)["embeddings"][konum],
}

pid = df["patient_id"].to_numpy()
y1 = df["y1"].to_numpy()
y6 = df["y6"].to_numpy()
censor = df["censor_time"].to_numpy()
yil = df["tarama_yili"].to_numpy()
sybil = df["sybil_y1"].to_numpy()
pillar = df["pillar_y1"].to_numpy()
skor = {"Sybil": sybil, "Pillar": pillar,
        "SPECTRE": df["skor_SPECTRE"].to_numpy(), "M3D": df["skor_M3D"].to_numpy(),
        "MG-3D": df["skor_MG-3D"].to_numpy()}
SIRA = ["Sybil", "Pillar", "SPECTRE", "M3D", "MG-3D"]

yaz("=" * 80)
yaz("SUDE-VLM-34 - BAGIMSIZ DENETIM DUZELTMELERI")
yaz("=" * 80)

# --------------------------------------------------------------------------
# A. Estimand karsilastirmasi
# --------------------------------------------------------------------------
yaz()
yaz("## A. Uc estimand yan yana (1. yil kanseri)")
yaz()
yaz("  Ayni veriden uc FARKLI soru sorulabilir. Onceki rapor birincil olarak hasta-max")
yaz("  kuralini kullaniyordu; bu, tek bir BT'den risk tahmini DEGILDIR.")
yaz()

# indeks BT: hastanin en erken taramasi (T0 tabani), hasta basina tek gozlem
sirali = df.assign(_i=np.arange(len(df))).sort_values(["patient_id", "tarama_yili"])
indeks_i = sirali.groupby("patient_id")["_i"].first().to_numpy()
indeks_m = np.zeros(len(df), bool)
indeks_m[indeks_i] = True

estimandlar = {
    "tarama başına (seri)": (np.ones(len(df), bool), "max", False),
    "indeks BT (en erken tarama)": (indeks_m, "max", False),
    "hasta-max (herhangi bir yıl)": (np.ones(len(df), bool), "max", True),
}

rapor["a_estimand"] = {}
for ad, (maske, _, hasta_topla) in estimandlar.items():
    if hasta_topla:
        h = pd.DataFrame({"pid": pid, "y": y1, **{m: skor[m] for m in SIRA}}).groupby("pid").max()
        hedef, sk = h["y"].to_numpy(), {m: h[m].to_numpy() for m in SIRA}
        n, npoz = len(h), int(hedef.sum())
    else:
        hedef = y1[maske]
        sk = {m: skor[m][maske] for m in SIRA}
        n, npoz = int(maske.sum()), int(hedef.sum())
    yaz(f"  {ad}  —  n={n}, pozitif={npoz} ({npoz/n:.2%})")
    yaz("    " + "  ".join(f"{m}={roc_auc_score(hedef, sk[m]):.3f}" for m in SIRA))
    rapor["a_estimand"][ad] = {"n": n, "pozitif": npoz,
                               **{m: float(roc_auc_score(hedef, sk[m])) for m in SIRA}}
yaz()
yaz("  Not: indeks BT hasta basina tek gozlemdir; hasta kumelenmesi yoktur, guven")
yaz("  araliklari icin bootstrap'ta ozel islem gerekmez. Tarama basina analiz ise")
yaz("  yayimlanmis tek-BT sonuclariyla AYNI soruyu sorar.")

# --------------------------------------------------------------------------
# B. Split'e saygili degerlendirme
# --------------------------------------------------------------------------
yaz()
yaz("## B. Dondurulmus astra-split-1.0 ile degerlendirme")
yaz()
bol = {a: set(kilit["bolunme"][a]["pid_listesi"]) for a in ("train", "dev", "held_out")}
m_tr = np.isin(pid, list(bol["train"]))
m_dv = np.isin(pid, list(bol["dev"]))
m_ho = np.isin(pid, list(bol["held_out"]))

yaz(f"  {'bolum':10s} {'seri':>6} {'hasta':>6} {'1y poz seri':>12} {'1y poz PID':>11} {'6y poz PID':>11}")
rapor["b_split"] = {"bolumler": {}}
for ad, m in (("train", m_tr), ("dev", m_dv), ("held_out", m_ho)):
    p1 = pd.Series(y1[m], index=pid[m]).groupby(level=0).max()
    p6 = pd.Series(y6[m], index=pid[m]).groupby(level=0).max()
    yaz(f"  {ad:10s} {int(m.sum()):>6} {len(set(pid[m])):>6} {int(y1[m].sum()):>12} "
        f"{int(p1.sum()):>11} {int(p6.sum()):>11}")
    rapor["b_split"]["bolumler"][ad] = {"seri": int(m.sum()), "hasta": len(set(pid[m])),
                                        "y1_poz_seri": int(y1[m].sum()),
                                        "y1_poz_pid": int(p1.sum()), "y6_poz_pid": int(p6.sum())}
yaz()
yaz("  ! Kilitteki 'pozitif_pid: 11' degeri 6 YILLIK kanser sayisidir. Bu calismanin")
yaz("    birincil hedefi olan 1. yil kanserinde held-out'ta 6 PID vardir.")
yaz()

# Probe TRAIN'de egitilir (train icinde kat-disi ile esik secimi icin dev kullanilir)
yaz("  Probe yalniz TRAIN'de egitildi, DEV'de esik sabitlendi, HELD-OUT'ta bir kez olculdu.")
yaz()


def train_probe(X: np.ndarray) -> object:
    """Yalniz train bolumunde egitilmis, tohum ortalamasiz tek model."""
    mdl = make_pipeline(StandardScaler(),
                        LogisticRegression(C=1, max_iter=3000, class_weight="balanced"))
    mdl.fit(X[m_tr], y1[m_tr])
    return mdl


split_skor = {"Sybil": sybil, "Pillar": pillar}
for ad, X in EMB.items():
    mdl = train_probe(X)
    split_skor[ad] = mdl.predict_proba(X)[:, 1]


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.959963985, k / n
    d = 1 + z * z / n
    orta = (p + z * z / (2 * n)) / d
    yari = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, orta - yari), min(1.0, orta + yari))


yaz(f"  {'model':10s} {'dev AUC':>8} {'held-out AUC':>13} {'dev esik':>9} "
    f"{'HO: TP/FN':>10} {'HO duyarlilik [Wilson %95]':>28} {'HO FP':>6}")
rapor["b_split"]["sonuc"] = {}
for ad in SIRA:
    s = split_skor[ad]
    a_dv = roc_auc_score(y1[m_dv], s[m_dv])
    a_ho = roc_auc_score(y1[m_ho], s[m_ho])
    # esik DEV'de sabitlenir: Sybil'in dev'deki alarm yukune esit yuk
    dev_yuk = float((sybil[m_dv] >= SYBIL_ESIK).mean())
    esik = float(np.quantile(s[m_dv], 1 - dev_yuk))
    al = s[m_ho] >= esik
    tp = int((al & (y1[m_ho] == 1)).sum())
    fn = int((~al & (y1[m_ho] == 1)).sum())
    fp = int((al & (y1[m_ho] == 0)).sum())
    lo, hi = wilson(tp, tp + fn)
    yaz(f"  {ad:10s} {a_dv:>8.3f} {a_ho:>13.3f} {esik:>9.3f} {tp:>5}/{fn:<4} "
        f"{tp/(tp+fn):>10.3f} [{lo:.3f}; {hi:.3f}] {fp:>6}")
    rapor["b_split"]["sonuc"][ad] = {"dev_auc": a_dv, "ho_auc": a_ho, "esik": esik,
                                     "TP": tp, "FN": fn, "FP": fp,
                                     "duyarlilik": tp / (tp + fn), "wilson": [lo, hi]}
yaz()
yaz("  ! Held-out'ta 6 pozitif seri vardir. Kusursuz 6/6 sonucta bile Wilson %95 alt")
yaz(f"    siniri %{wilson(6,6)[0]*100:.1f}'dir; bu kume hicbir esigi SINAYAMAZ, yalniz")
yaz("    nokta tahmin ve cok genis bir aralik raporlar (kilit karari D100).")
yaz("  ! Havuzlanmis 5 katli OOF olcumu (raporun geri kalani) bir GELISTIRME olcumudur,")
yaz("    dondurulmus held-out'un yerini tutmaz.")

# --------------------------------------------------------------------------
# C. Pillar ikincil baseline olarak FP/FN
# --------------------------------------------------------------------------
yaz()
yaz("## C. FP/FN tablosu - Pillar ikincil baseline olarak geri alindi")
yaz("   (tarama basina estimand; birincil hedef 1. yil)")
yaz()
yaz(f"  {'model':10s} {'esik/butce':>11} {'TP':>4} {'FN':>4} {'FP':>5} {'TN':>5} "
    f"{'duyarlilik':>11} {'ozgulluk':>9} {'PPV':>7}")
butce_seri = int((sybil >= SYBIL_ESIK).sum())
rapor["c_fpfn"] = {"butce_seri": butce_seri}
for ad in SIRA:
    s = skor[ad]
    esik = SYBIL_ESIK if ad == "Sybil" else float(np.quantile(s, 1 - butce_seri / len(s)))
    al = s >= esik
    tp, fn = int((al & (y1 == 1)).sum()), int((~al & (y1 == 1)).sum())
    fp, tn = int((al & (y1 == 0)).sum()), int((~al & (y1 == 0)).sum())
    yaz(f"  {ad:10s} {esik:>11.3f} {tp:>4} {fn:>4} {fp:>5} {tn:>5} "
        f"{tp/(tp+fn):>11.3f} {tn/(tn+fp):>9.3f} {tp/(tp+fp):>7.3f}")
    rapor["c_fpfn"][ad] = {"esik": esik, "TP": tp, "FN": fn, "FP": fp, "TN": tn}

# --------------------------------------------------------------------------
# D. Sybil ve Pillar FN kumelerinin ortusmesi
# --------------------------------------------------------------------------
yaz()
yaz("## D. FN kumelerinin vaka duzeyinde ortusmesi (tarama basina, 41 pozitif seri)")
poz_i = np.where(y1 == 1)[0]
fn_kume = {}
for ad in SIRA:
    s = skor[ad]
    esik = SYBIL_ESIK if ad == "Sybil" else float(np.quantile(s, 1 - butce_seri / len(s)))
    fn_kume[ad] = {int(i) for i in poz_i if s[i] < esik}
yaz(f"  {'model':10s} {'FN':>4}  kacirdigi seri anahtarlari (kisaltilmis)")
for ad in SIRA:
    ks = sorted(fn_kume[ad])
    yaz(f"  {ad:10s} {len(ks):>4}  " + ", ".join(df['series_key'].iloc[i].split('/')[0] for i in ks[:12])
        + (" ..." if len(ks) > 12 else ""))
yaz()
yaz(f"  Sybil ∩ Pillar   = {len(fn_kume['Sybil'] & fn_kume['Pillar'])} ortak FN")
yaz(f"  Sybil ∩ SPECTRE  = {len(fn_kume['Sybil'] & fn_kume['SPECTRE'])} ortak FN")
yaz(f"  Yalniz Sybil FN  = {len(fn_kume['Sybil'] - fn_kume['Pillar'] - fn_kume['SPECTRE'])}")
yaz(f"  Uc modelin ortak FN'i = {len(fn_kume['Sybil'] & fn_kume['Pillar'] & fn_kume['SPECTRE'])}")
yaz(f"  En az bir model yakaliyor = {len(poz_i) - len(fn_kume['Sybil'] & fn_kume['Pillar'] & fn_kume['SPECTRE'])}"
    f"/{len(poz_i)}")
rapor["d_fn_ortusme"] = {
    "fn_sayisi": {a: len(fn_kume[a]) for a in SIRA},
    "sybil_pillar_ortak": len(fn_kume["Sybil"] & fn_kume["Pillar"]),
    "sybil_spectre_ortak": len(fn_kume["Sybil"] & fn_kume["SPECTRE"]),
    "uclu_ortak": len(fn_kume["Sybil"] & fn_kume["Pillar"] & fn_kume["SPECTRE"]),
}

# --------------------------------------------------------------------------
# E. Kucuk, gerceklci ek alarm butceleri
# --------------------------------------------------------------------------
yaz()
yaz("## E. Sybil-negatif havuzda KUCUK ek alarm butceleri (hasta duzeyi)")
h = pd.DataFrame({"pid": pid, "y1": y1, "y6": y6,
                  **{m: skor[m] for m in SIRA}}).groupby("pid").max()
h_hedef = h["y1"].to_numpy()
h_y6a = h["y6"].to_numpy()
h_neg = h["Sybil"].to_numpy() < SYBIL_ESIK
butce_hasta = int((~h_neg).sum())
havuz_n, kacan = int(h_neg.sum()), int(h_hedef[h_neg].sum())
yaz(f"  Havuz: {havuz_n} hasta, {kacan} kacan kanser (taban oran %{kacan/havuz_n*100:.2f})")
yaz(f"  Onceki rapordaki +{int((~h_neg).sum())} butcesi kohortun "
    f"%{((~h_neg).sum()*2)/len(h)*100:.1f}'ine alarm demekti; asagida gerceklci butceler.")
yaz()
BUTCELER = [10, 25, 50, 100, 200, int((~h_neg).sum())]
yaz("  Her hucre: kurtarilan kanser (parantezde ayni butcedeki ek YANLIS alarm).")
yaz("  Ek yanlis alarm = butce - kurtarilan; FN-FP odunlesmesini dogrudan gosterir.")
yaz()
yaz(f"  {'ek butce':>9} {'rastgele bekl.':>15} "
    + " ".join(f"{m:>12}" for m in SIRA if m != "Sybil"))
rapor["e_kucuk_butce"] = {"havuz": havuz_n, "kacan": kacan}
for b in BUTCELER:
    bekl = b * kacan / havuz_n
    sat, kayit = [], {"beklenen": bekl}
    for m in SIRA:
        if m == "Sybil":
            continue
        s = h[m].to_numpy()[h_neg]
        kurt = int(h_hedef[h_neg][np.argsort(-s)[:b]].sum())
        sat.append(f"{kurt:>5} ({b - kurt:>4})")
        kayit[m] = kurt
        kayit[f"{m}_ek_fp"] = b - kurt
    yaz(f"  {b:>9} {bekl:>15.2f} " + " ".join(sat))
    rapor["e_kucuk_butce"][b] = kayit
yaz()
yaz(f"  ! Havuzda yalniz {kacan} FN var. Tek bir vakanin yer degistirmesi kurtarma")
yaz(f"    oranini {100/kacan:.0f} puan oynatir. Bu sayilarla ne 'tamamlayicilik var'")
yaz("    ne 'yok' denebilir; hüküm KARAR VERILEMEZ'dir.")

# --------------------------------------------------------------------------
# F. 2-6 yil gelecek risk (resmi Mask ile)
# --------------------------------------------------------------------------
yaz()
yaz("## F. Gelecek risk: 2-6. yil ufuklari (resmi Kanser_Yil/Mask, tarama basina)")
yaz("   Ileri yillarda tani alan 99 seri analiz disi BIRAKILMAZ; Sybil'in asli gorevi")
yaz("   olan gelecek riski burada olculur.")
yaz()
yaz("   Her ufukta o ufkun kendi risk skoru kullanilir (Sybil/Pillar y1..y6); onceki")
yaz("   surum her ufukta y1 skorunu kullaniyordu (ikinci denetim bulgusu 1b).")
yaz()
SYB6 = sp_npz["sybil_y1_to_y6"][konum]
PIL6 = sp_npz["pillar_y1_to_y6"][konum]


def ufuk_skor(m: str, k: int) -> np.ndarray:
    """k = 0-tabanli ufuk indeksi."""
    if m == "Sybil":
        return SYB6[:, k]
    if m == "Pillar":
        return PIL6[:, k]
    return skor[m]  # temel modellerin probu yalniz 1. yil hedefiyle egitildi


yaz(f"  {'ufuk':>5} {'pozitif':>8} {'gecerli':>8} " + " ".join(f"{m:>9}" for m in SIRA))
rapor["f_gelecek"] = {}
for k in range(6):
    gec = mask_yil[:, k] == 1
    poz = kanser_yil[gec, k].astype(int)
    if poz.sum() < 5:
        continue
    yaz(f"  {k+1:>5} {int(poz.sum()):>8} {int(gec.sum()):>8} "
        + " ".join(f"{roc_auc_score(poz, ufuk_skor(m, k)[gec]):>9.3f}" for m in SIRA))
    rapor["f_gelecek"][k + 1] = {"pozitif": int(poz.sum()), "gecerli": int(gec.sum()),
                                 **{m: float(roc_auc_score(poz, ufuk_skor(m, k)[gec]))
                                    for m in SIRA}}

# --- Birlesik 2-6 yil (DUZELTILDI, ikinci denetim bulgusu 1) ---
yaz()
yaz("  Birlesik 2.-6. yil penceresi:")
yaz("    ONCEKI SURUM HATALIYDI. `mask_y6 == 1` sarti, 2.-5. yilda kanser cikanlari")
yaz("    disliyordu (olay sonrasi maske sifirlaniyor); geriye yalniz 6. yil olaylari")
yaz("    kaliyordu: 11 pozitif / 1.799 seri, 11'inin 11'i 6. yil.")
yaz("    DOGRU KURGU: pozitif = 2.-6. yilda olay; negatif = 6. yila kadar olaysiz takip;")
yaz("    1. yil kanserleri her iki taraftan da cikarilir.")
poz_m = kanser_yil[:, 1:].sum(1) > 0
neg_m = (kanser_yil.sum(1) == 0) & (mask_yil[:, 5] == 1)
gec26 = (poz_m | neg_m) & (kanser_yil[:, 0] == 0)
h26 = (poz_m & gec26)[gec26].astype(int)
yaz(f"    -> {int(h26.sum())} pozitif / {int(gec26.sum())} seri")
yaz("    " + "  ".join(f"{m}={roc_auc_score(h26, ufuk_skor(m, 5)[gec26]):.3f}" for m in SIRA))
rapor["f_birlesik_2_6"] = {"pozitif": int(h26.sum()), "gecerli": int(gec26.sum()),
                           "skor": "Sybil/Pillar y6; temel modeller 1-yil probu",
                           **{m: float(roc_auc_score(h26, ufuk_skor(m, 5)[gec26])) for m in SIRA}}

# --------------------------------------------------------------------------
# G. FP zenginlesmesi - her model KENDI TN grubuyla
# --------------------------------------------------------------------------
yaz()
yaz("## G. Yanlis pozitiflerin ileride kanserle iliskisi (payda duzeltildi)")
yaz("   Onceki surum her modelin FP oranini SYBIL'in TN oranina boluyordu. Her model")
yaz("   kendi TN grubuyla karsilastirilir (ikinci denetim bulgusu 4).")
yaz("   Not: ileride kanser tanisi almak, ilk alarmin dogru oldugunu lezyon kaniti")
yaz("   olmadan GOSTERMEZ; olculen sey 'ileride kanserle iliskili alarm' oranidir.")
yaz()
yaz(f"  {'model':10s} {'FP':>5} {'FP icinde 2-6y':>15} {'FP orani':>9} {'kendi TN orani':>15} "
    f"{'zenginlesme':>12}")
rapor["g_zenginlesme"] = {}
for m in SIRA:
    s = h[m].to_numpy()
    ust = np.argsort(-s)[:butce_hasta]
    al = np.zeros(len(s), bool)
    al[ust] = True
    fp = al & (h_hedef == 0)
    tn = (~al) & (h_hedef == 0)
    f_oran = h_y6a[fp].sum() / fp.sum()
    t_oran = h_y6a[tn].sum() / tn.sum()
    yaz(f"  {m:10s} {int(fp.sum()):>5} {int(h_y6a[fp].sum()):>15} {f_oran:>9.1%} "
        f"{t_oran:>15.1%} {f_oran/t_oran:>11.2f}x")
    rapor["g_zenginlesme"][m] = {"fp": int(fp.sum()), "fp_gec_kanser": int(h_y6a[fp].sum()),
                                 "fp_oran": float(f_oran), "tn_oran": float(t_oran),
                                 "zenginlesme": float(f_oran / t_oran)}

# --------------------------------------------------------------------------
# I. Pillar icin eslestirilmis farklar (tarama basina, 1. yil)
# --------------------------------------------------------------------------
yaz()
yaz("## I. Pillar'in farki eslestirilmis testle (tarama basina, 1. yil)")
yaz("   Pillar'in ustunlugu once yalniz nokta tahminle soylenmisti; burada ayni")
yaz("   hasta-kumeli bootstrap ornekleminde eslestirilmis fark hesaplanir.")
yaz()
hastalar_u = np.unique(pid)
idx_pid = {p: np.where(pid == p)[0] for p in hastalar_u}
rng_b = np.random.default_rng(20260916)
BOOT = [np.concatenate([idx_pid[p] for p in rng_b.choice(hastalar_u, len(hastalar_u), replace=True)])
        for _ in range(BOOTSTRAP)]
yaz(f"  {'karsilastirma':26s} {'DeltaAUC':>9} {'%95 GA':>20} {'p':>9}")
rapor["i_pillar_fark"] = {}
for a, b in [("Pillar", "SPECTRE"), ("Pillar", "Sybil"), ("Pillar", "M3D"), ("Pillar", "MG-3D")]:
    d0 = roc_auc_score(y1, skor[a]) - roc_auc_score(y1, skor[b])
    orn = np.array([roc_auc_score(y1[ii], skor[a][ii]) - roc_auc_score(y1[ii], skor[b][ii])
                    for ii in BOOT if 0 < y1[ii].sum() < len(ii)])
    lo, hi = np.percentile(orn, [2.5, 97.5])
    pv = float(min(1.0, 2 * min((orn <= 0).mean(), (orn >= 0).mean())))
    yaz(f"  {a+' - '+b:26s} {d0:>+9.3f} [{lo:>+7.3f}; {hi:>+7.3f}] {pv:>9.4f}")
    rapor["i_pillar_fark"][f"{a}-{b}"] = {"fark": d0, "ga": [lo, hi], "p": pv}
ps = sorted((v["p"], k) for k, v in rapor["i_pillar_fark"].items())
onceki_p, m_p = 0.0, len(ps)
yaz("  Holm duzeltmesi (4 karsilastirma):")
for i, (pv, k) in enumerate(ps):
    duz = min(1.0, max(onceki_p, (m_p - i) * pv))
    onceki_p = duz
    rapor["i_pillar_fark"][k]["holm_p"] = duz
    yaz(f"    {k:26s} ham p={pv:.4f}  Holm p={duz:.4f}  "
        f"{'anlamli' if duz < 0.05 else 'anlamli DEGIL'}")

# --------------------------------------------------------------------------
# H. Hasta ici kontrolde protokol gercekten sabit mi?
# --------------------------------------------------------------------------
yaz()
yaz("## H. Hasta ici kontrolun 'ayni cihaz/protokol' varsayimi")
man = pd.read_csv(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_manifest.csv")
man = man.set_index("series_key").loc[df["series_key"]].reset_index()
prot = man["series_id"].str.extract(r"-(\d)OPA([A-Z]+)")[1].fillna("NA").to_numpy()
kans = df[df.y6 == 1].copy()
kans["prot"] = prot[df.y6.to_numpy() == 1]
uyg = kans.groupby("patient_id").filter(lambda g: len(g) > 1 and g.y1.nunique() > 1)
ayni = uyg.groupby("patient_id")["prot"].nunique()
yaz(f"  Sekil 5'teki {uyg.patient_id.nunique()} hastadan protokolu sabit kalan: "
    f"{int((ayni == 1).sum())}; protokolu degisen: {int((ayni > 1).sum())}")
yaz("  -> 'ayni cihaz ve protokol, fark yalniz zaman' ifadesi bu hastalarin cogunlugu")
yaz("     icin DOGRU DEGIL; hasta ici kontrol sanildigi kadar siki degil.")
rapor["h_protokol"] = {"hasta": int(uyg.patient_id.nunique()),
                       "protokol_sabit": int((ayni == 1).sum()),
                       "protokol_degisen": int((ayni > 1).sum())}

# --------------------------------------------------------------------------
# Sekil 8: estimand + kucuk butce
# --------------------------------------------------------------------------
plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 140, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
                     "figure.facecolor": "white", "axes.facecolor": "white"})
RENK = {"Sybil": "#1f6feb", "Pillar": "#7c3aed", "SPECTRE": "#c2410c",
        "M3D": "#6b7280", "MG-3D": "#9ca3af"}

fig, axlar = plt.subplots(1, 2, figsize=(11, 4.3))

ax = axlar[0]
etiketler = list(rapor["a_estimand"])
x = np.arange(len(etiketler))
gen = 0.16
for i, m in enumerate(SIRA):
    ax.bar(x + (i - 2) * gen, [rapor["a_estimand"][e][m] for e in etiketler], gen,
           color=RENK[m], alpha=0.85, label=m)
ax.axhline(0.5, color="#111827", ls=":", lw=0.9)
ax.set_xticks(x)
ax.set_xticklabels([f"{e}\nn={rapor['a_estimand'][e]['n']}, poz={rapor['a_estimand'][e]['pozitif']}"
                    for e in etiketler], fontsize=7.6)
ax.set_ylabel("1. yıl AUC"); ax.set_ylim(0, 1.18)
ax.set_title("Estimand seçimi sonucu değiştiriyor", fontsize=9.5, pad=18)
ax.legend(fontsize=7.4, frameon=False, ncols=5, loc="upper center",
          bbox_to_anchor=(0.5, 1.10), columnspacing=1.1, handlelength=1.2)

ax = axlar[1]
bs = [b for b in BUTCELER if b <= 200]
for m in SIRA:
    if m == "Sybil":
        continue
    s = h[m].to_numpy()[h_neg]
    sr = np.argsort(-s)
    ax.plot(bs, [h_hedef[h_neg][sr[:b]].sum() for b in bs], marker="o", ms=4,
            color=RENK[m], lw=1.6, label=m)
ax.plot(bs, [b * kacan / havuz_n for b in bs], ls=":", color="#9ca3af", lw=1.3,
        label="rastgele beklenti")
ax.axhline(kacan, color="#111827", ls=":", lw=0.8)
ax.text(200, kacan + 0.06, f"havuzdaki tüm FN = {kacan}", ha="right", fontsize=7.4)
ax.set_xlabel("Sybil'e eklenen ek alarm sayısı (hasta)")
ax.set_ylabel("kurtarılan 1. yıl kanseri")
ax.set_title(f"Küçük ek bütçelerde kurtarma (havuz {havuz_n} hasta, {kacan} FN)", fontsize=9.5)
ax.legend(fontsize=7.6, frameon=False, loc="upper left")
fig.suptitle("Denetim düzeltmeleri: estimand ve gerçekçi alarm bütçesi", fontsize=11, y=1.0)
fig.tight_layout()
kaydet(fig, "sekil_8_denetim")
plt.close(fig)

(CIKTI / "denetim_duzeltmeleri.json").write_text(
    json.dumps(rapor, indent=2, ensure_ascii=False), encoding="utf-8")
(CIKTI / "ozet_denetim.txt").write_text("\n".join(satirlar), encoding="utf-8")
yaz()
yaz(f"Cikti: {CIKTI}/denetim_duzeltmeleri.json, sekil_8_denetim.svg")
