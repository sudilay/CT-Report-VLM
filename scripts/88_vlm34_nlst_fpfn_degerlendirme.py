"""SUDE-VLM-34 - NLST'de uc 3B BT temel modelinin ve Sybil'in FP/FN degerlendirmesi.

Birincil hedef : 1. yil icinde akciger kanseri (NLST resmi Kanser_Yil_1 / Mask_Yil_1)
Birincil duzey : hasta (PID, max kurali - astra-split-1.0 D98/D100)
Ana taban      : Sybil (Pillar ayri bulgu olarak, bolum I)
Kohort         : astra-split-1.0 filtresi -> 2.940 seri / 1.198 hasta

CPU, yaklasik 10 dk. Cikti: outputs/vlm34/
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

KOK = Path(__file__).resolve().parents[1]
BASE = KOK / "data/external/model_benchmarks_v4"
CIKTI = KOK / "outputs/vlm34"
CIKTI.mkdir(parents=True, exist_ok=True)

TOHUMLAR = [0, 1, 2, 3, 4]
BOOTSTRAP = 2000
SYBIL_ESIK = 0.20  # BIMCV analizinde onceden sabitlenmis esik (vlm33 bolum 6)

rapor: dict = {}
satirlar: list[str] = []


def yaz(s: str = "") -> None:
    print(s)
    satirlar.append(s)


# --------------------------------------------------------------------------
# A. Veri
# --------------------------------------------------------------------------
sp = np.load(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_embeddings.npz", allow_pickle=True)
m3 = np.load(BASE / "m3d/nlst_full_cohort_2965/m3d_nlst_full_2965_embeddings.npz", allow_pickle=True)
mg = np.load(BASE / "mg3d/nlst_full_cohort_2965/mg3d_nlst_full_2965_embeddings.npz", allow_pickle=True)

keys_ham = np.array([str(s) for s in sp["series_keys"]])
for ad, d in (("m3d", m3), ("mg3d", mg)):
    assert np.array_equal(np.array([str(s) for s in d["series_keys"]]), keys_ham), f"{ad} seri sirasi farkli"
    assert np.array_equal(d["y"], sp["y"]), f"{ad} etiket farkli"
    assert np.array_equal(d["censor_times"], sp["censor_times"]), f"{ad} censor_time farkli"
    assert np.allclose(d["sybil_y1_to_y6"], sp["sybil_y1_to_y6"]), f"{ad} Sybil skorlari farkli"
    assert np.allclose(d["pillar_y1_to_y6"], sp["pillar_y1_to_y6"]), f"{ad} Pillar skorlari farkli"

# NLST resmi survival etiketleri (Excel), seri anahtarina gore hizalanir
xl = pd.read_excel(KOK / "astra_radiology_reports_with_labels_all.xlsx")
xl = xl.set_index("Seri_Anahtari").loc[keys_ham].reset_index()
assert np.array_equal(xl["Kanser_Etiketi_y"].values, sp["y"])
assert np.array_equal(xl["Censor_Time"].values, sp["censor_times"])
kanser_yil_ham = xl[[f"Kanser_Yil_{i}" for i in range(1, 7)]].to_numpy(float)
mask_yil_ham = xl[[f"Mask_Yil_{i}" for i in range(1, 7)]].to_numpy(float)

# astra-split-1.0 filtresi
kilit = json.loads((KOK / "configs/splits_astra.json").read_text(encoding="utf-8"))
tut = ~np.isin(keys_ham, list(kilit["filtre"]["dislanan_seri_anahtarlari"]))

keys = keys_ham[tut]
pid = sp["patient_ids"][tut].astype(str)
y6 = sp["y"][tut]
censor = sp["censor_times"][tut]
sybil = sp["sybil_y1_to_y6"][tut]
pillar = sp["pillar_y1_to_y6"][tut]
kanser_yil = kanser_yil_ham[tut]
mask_yil = mask_yil_ham[tut]
tarama_yili = np.array([k.split("/")[1].split("-")[2] for k in keys])

EMB = {
    "SPECTRE": sp["cls_embeds"][tut],
    "M3D": m3["embeddings"][tut],
    "MG-3D": mg["embeddings"][tut],
}
y1 = kanser_yil[:, 0].astype(int)  # birincil hedef

yaz("=" * 78)
yaz("SUDE-VLM-34 - NLST FP/FN DEGERLENDIRMESI")
yaz("=" * 78)
yaz()
yaz("## A. Kohort")
yaz(f"  ham paket            : {len(keys_ham)} seri")
yaz(f"  astra-split-1.0 sonra: {len(keys)} seri / {len(set(pid))} hasta")
yaz(f"  1. yil pozitif       : {y1.sum()} seri / {len(set(pid[y1 == 1]))} hasta")
yaz(f"  6. yil pozitif       : {int((y6 == 1).sum())} seri / {len(set(pid[y6 == 1]))} hasta")
yaz(f"  hasta basina seri    : medyan {int(np.median(pd.Series(pid).value_counts()))}, "
    f"tek serili hasta {int((pd.Series(pid).value_counts() == 1).sum())}")
yaz(f"  tarama yili dagilimi : "
    + ", ".join(f"{t}: {int((tarama_yili == t).sum())}" for t in sorted(set(tarama_yili))))
rapor["kohort"] = {"seri": int(len(keys)), "hasta": len(set(pid)),
                   "y1_pozitif_seri": int(y1.sum()), "y1_pozitif_hasta": len(set(pid[y1 == 1])),
                   "y6_pozitif_seri": int((y6 == 1).sum()), "y6_pozitif_hasta": len(set(pid[y6 == 1]))}

# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------
hastalar = np.unique(pid)
idx_pid = {p: np.where(pid == p)[0] for p in hastalar}
rng = np.random.default_rng(20260916)
BOOT_SEC = [rng.choice(hastalar, len(hastalar), replace=True) for _ in range(BOOTSTRAP)]


def oof_skor(X: np.ndarray, hedef: np.ndarray, gruplar: np.ndarray) -> np.ndarray:
    """Tohum ortalamali, hasta gruplu 5 kat kat-disi olasilik."""
    toplam = np.zeros(len(hedef))
    for t in TOHUMLAR:
        cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=t)
        p = np.zeros(len(hedef))
        for tr, te in cv.split(X, hedef, gruplar):
            mdl = make_pipeline(StandardScaler(),
                                LogisticRegression(C=1, max_iter=3000, class_weight="balanced"))
            mdl.fit(X[tr], hedef[tr])
            p[te] = mdl.predict_proba(X[te])[:, 1]
        toplam += p
    return toplam / len(TOHUMLAR)


def auc_ga(skor: np.ndarray, hedef: np.ndarray) -> tuple[float, float, float]:
    """Hasta kumeli bootstrap ile AUC ve %95 GA (seri duzeyi girdiler icin)."""
    a = roc_auc_score(hedef, skor)
    orn = []
    for sec in BOOT_SEC:
        ii = np.concatenate([idx_pid[p] for p in sec])
        h = hedef[ii]
        if h.sum() == 0 or h.sum() == len(h):
            continue
        orn.append(roc_auc_score(h, skor[ii]))
    lo, hi = np.percentile(orn, [2.5, 97.5])
    return a, lo, hi


def hasta_duzeyi(skor: np.ndarray) -> pd.Series:
    return pd.Series(skor, index=pid).groupby(level=0).max()


h_y1 = pd.Series(y1, index=pid).groupby(level=0).max()
h_y6 = pd.Series(y6, index=pid).groupby(level=0).max()
h_censor = pd.Series(censor, index=pid).groupby(level=0).min()
h_sira = h_y1.index.to_numpy()
h_idx = {p: i for i, p in enumerate(h_sira)}
BOOT_H = [np.array([h_idx[p] for p in sec]) for sec in BOOT_SEC]


def auc_ga_hasta(skor_h: pd.Series, hedef_h: pd.Series) -> tuple[float, float, float]:
    s, h = skor_h.loc[h_sira].to_numpy(), hedef_h.loc[h_sira].to_numpy()
    a = roc_auc_score(h, s)
    orn = []
    for ii in BOOT_H:
        hh = h[ii]
        if hh.sum() == 0 or hh.sum() == len(hh):
            continue
        orn.append(roc_auc_score(hh, s[ii]))
    lo, hi = np.percentile(orn, [2.5, 97.5])
    return a, lo, hi


# --------------------------------------------------------------------------
# B. Ayirma gucu
# --------------------------------------------------------------------------
yaz()
yaz("## B. Ayirma gucu - birincil hedef (1. yil kanseri)")
yaz()
yaz("  ! Esitsizlik beyani: uc temel modelin skoru bu kohortun etiketleriyle egitilmis")
yaz("    lineer probun kat-disi ciktisidir (hasta gruplu, 5 tohum ortalamasi). Sybil ve")
yaz("    Pillar ham on-egitimli model ciktisidir, burada egitilmedi.")
yaz()

skorlar: dict[str, np.ndarray] = {ad: oof_skor(X, y1, pid) for ad, X in EMB.items()}
skorlar["Sybil"] = sybil[:, 0]
SIRA = ["Sybil", "SPECTRE", "M3D", "MG-3D"]

yaz(f"  {'model':10s} {'seri AUC [%95 GA]':>26}   {'hasta AUC [%95 GA]':>26}")
rapor["b_ayirma"] = {}
for ad in SIRA:
    a, lo, hi = auc_ga(skorlar[ad], y1)
    ah, loh, hih = auc_ga_hasta(hasta_duzeyi(skorlar[ad]), h_y1)
    yaz(f"  {ad:10s} {a:>9.3f} [{lo:.3f}; {hi:.3f}]   {ah:>9.3f} [{loh:.3f}; {hih:.3f}]")
    rapor["b_ayirma"][ad] = {"seri_auc": [a, lo, hi], "hasta_auc": [ah, loh, hih]}

# Cok ufuklu (ikincil, betimsel) - resmi Mask ile
yaz()
yaz("  Ikincil: zaman ufkuna gore (NLST resmi Kanser_Yil/Mask), seri duzeyi AUC")
yaz(f"  {'ufuk':>5} {'pozitif':>8} {'gecerli':>8} " + " ".join(f"{a:>9}" for a in SIRA))
rapor["b_ufuk"] = {}
for k in range(6):
    gec = mask_yil[:, k] == 1
    poz = kanser_yil[gec, k].astype(int)
    if poz.sum() == 0 or poz.sum() == len(poz):
        continue
    sat = [f"{roc_auc_score(poz, skorlar[a][gec]):>9.3f}" for a in SIRA]
    yaz(f"  {k+1:>5} {int(poz.sum()):>8} {int(gec.sum()):>8} " + " ".join(sat))
    rapor["b_ufuk"][k + 1] = {"pozitif": int(poz.sum()), "gecerli": int(gec.sum()),
                              **{a: float(roc_auc_score(poz, skorlar[a][gec])) for a in SIRA}}

# --------------------------------------------------------------------------
# C. Sybil FP/FN - esik taramasi
# --------------------------------------------------------------------------
yaz()
yaz("## C. Sybil FP/FN (birincil: hasta duzeyi, 1. yil)")
yaz()


def kafes(skor, hedef, esik):
    al = skor >= esik
    return (int((al & (hedef == 1)).sum()), int((~al & (hedef == 1)).sum()),
            int((al & (hedef == 0)).sum()), int((~al & (hedef == 0)).sum()))


h_sybil = hasta_duzeyi(sybil[:, 0])
yaz(f"  {'esik':>6} {'TP':>4} {'FN':>4} {'FP':>5} {'TN':>5} {'duyarlilik':>11} {'ozgulluk':>9} "
    f"{'PPV':>7} {'alarm yuku':>11}")
rapor["c_sybil_esik"] = {}
for esik in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
    tp, fn, fp, tn = kafes(h_sybil.loc[h_sira].to_numpy(), h_y1.loc[h_sira].to_numpy(), esik)
    duy, ozg = tp / (tp + fn), tn / (tn + fp)
    ppv = tp / (tp + fp) if tp + fp else float("nan")
    isaret = " <-" if abs(esik - SYBIL_ESIK) < 1e-9 else ""
    yaz(f"  {esik:>6.2f} {tp:>4} {fn:>4} {fp:>5} {tn:>5} {duy:>11.3f} {ozg:>9.3f} {ppv:>7.3f} "
        f"{(tp+fp)/len(h_sira):>10.1%}{isaret}")
    rapor["c_sybil_esik"][esik] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn,
                                   "duyarlilik": duy, "ozgulluk": ozg, "ppv": ppv}

tp, fn, fp, tn = kafes(sybil[:, 0], y1, SYBIL_ESIK)
yaz(f"\n  Seri duzeyi (ikincil), esik {SYBIL_ESIK}: TP={tp} FN={fn} FP={fp} TN={tn}")
rapor["c_seri_duzeyi"] = {"TP": tp, "FN": fn, "FP": fp, "TN": tn}

# --------------------------------------------------------------------------
# D. Sabit alarm butcesinde uc model
# --------------------------------------------------------------------------
yaz()
yaz("## D. Ayni alarm yukunde uc model vs Sybil (hasta duzeyi, 1. yil)")
butce = int((h_sybil.loc[h_sira].to_numpy() >= SYBIL_ESIK).sum())
h_hedef = h_y1.loc[h_sira].to_numpy()
yaz(f"  Sybil {SYBIL_ESIK} esiginde {butce} hastaya alarm veriyor; her modele ayni butce verildi.")
yaz(f"  {'model':10s} {'TP':>4} {'FN':>4} {'FP':>5} {'duyarlilik':>11} {'PPV':>7} {'Sybil ile ortak':>16}")
sybil_alarm = set(np.where(h_sybil.loc[h_sira].to_numpy() >= SYBIL_ESIK)[0])
rapor["d_butce"] = {"butce": butce}
for ad in SIRA:
    s = hasta_duzeyi(skorlar[ad]).loc[h_sira].to_numpy()
    ust = set(np.argsort(-s)[:butce])
    ii = np.array(sorted(ust))
    tp = int(h_hedef[ii].sum())
    fn = int(h_hedef.sum() - tp)
    ortak = len(ust & sybil_alarm)
    yaz(f"  {ad:10s} {tp:>4} {fn:>4} {butce-tp:>5} {tp/h_hedef.sum():>11.3f} {tp/butce:>7.3f} "
        f"{ortak:>10} ({ortak/butce:>4.0%})")
    rapor["d_butce"][ad] = {"TP": tp, "FN": fn, "FP": butce - tp, "sybil_ortak": ortak}

# --------------------------------------------------------------------------
# E. Tamamlayicilik - Sybil'in kacirdiklarini kim kurtariyor
# --------------------------------------------------------------------------
yaz()
yaz("## E. Tamamlayicilik: Sybil-negatif havuzda FN kurtarma (hasta duzeyi)")
neg_m = h_sybil.loc[h_sira].to_numpy() < SYBIL_ESIK
havuz_n = int(neg_m.sum())
kacan = int(h_hedef[neg_m].sum())
ek_butce = butce
bekl = ek_butce * kacan / havuz_n
yaz(f"  Sybil-negatif havuz: {havuz_n} hasta, {kacan} kacan kanser")
yaz(f"  Ek alarm butcesi {ek_butce} (Sybil kadar), rastgele beklenen kurtarma {bekl:.2f}")
yaz(f"  {'model':10s} {'havuz AUC':>10} {'kurtarilan':>11} {'ek FP':>7} {'kesifsel p':>11}")
rapor["e_kurtarma"] = {"havuz": havuz_n, "kacan": kacan, "ek_butce": ek_butce, "beklenen": bekl}
for ad in SIRA:
    if ad == "Sybil":
        continue
    s = hasta_duzeyi(skorlar[ad]).loc[h_sira].to_numpy()[neg_m]
    h = h_hedef[neg_m]
    auc = roc_auc_score(h, s)
    ust = np.argsort(-s)[:ek_butce]
    k = int(h[ust].sum())
    p = float(hypergeom.sf(k - 1, len(h), int(h.sum()), ek_butce))
    yaz(f"  {ad:10s} {auc:>10.3f} {k:>11} {ek_butce-k:>7} {p:>11.4f}")
    rapor["e_kurtarma"][ad] = {"havuz_auc": auc, "kurtarilan": k, "p": p}

# --------------------------------------------------------------------------
# F. Sybil'in yanlis pozitifleri gercekten yanlis mi? (erken uyari)
# --------------------------------------------------------------------------
yaz()
yaz("## F. Sybil'in 1. yil FP'leri erken uyari mi?")
yaz("  Soru: 1. yilda kanser cikmadigi icin FP sayilan hastalarin kaci 2-6. yilda kanser oldu?")
h_alarm = h_sybil.loc[h_sira].to_numpy() >= SYBIL_ESIK
fp_m = h_alarm & (h_hedef == 0)
tn_m = (~h_alarm) & (h_hedef == 0)
h_y6a = h_y6.loc[h_sira].to_numpy()
fp_gec = int(h_y6a[fp_m].sum())
tn_gec = int(h_y6a[tn_m].sum())
yaz(f"  FP grubu: {int(fp_m.sum())} hasta, {fp_gec} tanesi 2-6. yilda kanser ({fp_gec/fp_m.sum():.1%})")
yaz(f"  TN grubu: {int(tn_m.sum())} hasta, {tn_gec} tanesi 2-6. yilda kanser ({tn_gec/tn_m.sum():.1%})")
orani = (fp_gec / fp_m.sum()) / (tn_gec / tn_m.sum()) if tn_gec else float("nan")
p_f = float(hypergeom.sf(fp_gec - 1, int(fp_m.sum() + tn_m.sum()), fp_gec + tn_gec, int(fp_m.sum())))
yaz(f"  Zenginlesme orani {orani:.2f}x, kesifsel p = {p_f:.2e}")
rapor["f_erken_uyari"] = {"fp_n": int(fp_m.sum()), "fp_gec_kanser": fp_gec,
                          "tn_n": int(tn_m.sum()), "tn_gec_kanser": tn_gec,
                          "zenginlesme": orani, "p": p_f}

yaz()
yaz("  ! Modeller arasi zenginlesme karsilastirmasi BU BETIKTEN KALDIRILDI.")
yaz("    Onceki surum her modelin FP oranini SYBIL'in TN oranina boluyordu; her model")
yaz("    kendi TN grubuyla karsilastirilmalidir (ikinci bagimsiz denetim bulgusu 4).")
yaz("    Duzeltilmis tablo: scripts/92_vlm34_nlst_denetim_duzeltmeleri.py bolum G.")

# --------------------------------------------------------------------------
# G. Fonksiyonel ayrim: mevcut lezyon mu, gelecek risk mi?
# --------------------------------------------------------------------------
yaz()
yaz("## G. Fonksiyonel ayrim: censor_time'a gore skor (kanserli seriler)")
yaz("  censor=0 -> tarama sirasinda tumor muhtemelen goruntude")
yaz("  censor>=1 -> tanidan yillar once; tumor henuz yok/cok kucuk")
yaz(f"  {'censor':>7} {'n':>5} " + " ".join(f"{a:>10}" for a in SIRA))
rapor["g_lead"] = {}
for c in range(6):
    m = (y6 == 1) & (censor == c)
    if m.sum() == 0:
        continue
    yaz(f"  {c:>7} {int(m.sum()):>5} " + " ".join(f"{np.median(skorlar[a][m]):>10.3f}" for a in SIRA))
    rapor["g_lead"][c] = {"n": int(m.sum()), **{a: float(np.median(skorlar[a][m])) for a in SIRA}}
m0 = y6 == 0
yaz(f"  {'kanser yok':>7} {int(m0.sum()):>5} " + " ".join(f"{np.median(skorlar[a][m0]):>10.3f}" for a in SIRA))
rapor["g_lead"]["negatif"] = {"n": int(m0.sum()), **{a: float(np.median(skorlar[a][m0])) for a in SIRA}}

yaz()
yaz("  Ayirma gucu: 'censor>=1 kanserli seri' vs 'hic kanser olmayan seri'")
yaz("  (gelecek riski gorme yetenegi; mevcut lezyon sinyali burada yok)")
gel = (y6 == 1) & (censor >= 1)
alt = gel | (y6 == 0)
hedef_gel = gel[alt].astype(int)
rapor["g_gelecek"] = {}
for ad in SIRA:
    a = roc_auc_score(hedef_gel, skorlar[ad][alt])
    yaz(f"    {ad:10s} AUC={a:.3f}")
    rapor["g_gelecek"][ad] = a

# --------------------------------------------------------------------------
# H. Hasta ici longitudinal kontrol
# --------------------------------------------------------------------------
yaz()
yaz("## H. Hasta ici kontrol: ayni hastanin taramalari")
yaz("  Ayni hasta, ayni cihaz/protokol; fark yalniz tarama zamani.")
cok = pd.DataFrame({"pid": pid, "y6": y6, "censor": censor, "y1": y1,
                    **{a: skorlar[a] for a in SIRA}})
kans = cok[cok.y6 == 1]
uygun = kans.groupby("pid").filter(lambda g: len(g) > 1 and g.y1.nunique() > 1)
yaz(f"  {uygun.pid.nunique()} kanserli hastada hem 1-yil-pozitif hem 1-yil-negatif tarama var")
yaz(f"  {'model':10s} {'1y-poz medyan':>14} {'1y-neg medyan':>14} {'hasta ici artis':>16} "
    f"{'artan hasta':>12}")
rapor["h_hastaici"] = {"hasta": int(uygun.pid.nunique())}
for ad in SIRA:
    poz_m = uygun.loc[uygun.y1 == 1, ad].median()
    neg_m = uygun.loc[uygun.y1 == 0, ad].median()
    artan = sum(g.loc[g.y1 == 1, ad].max() > g.loc[g.y1 == 0, ad].max()
                for _, g in uygun.groupby("pid"))
    n = uygun.pid.nunique()
    yaz(f"  {ad:10s} {poz_m:>14.3f} {neg_m:>14.3f} {poz_m-neg_m:>16.3f} {artan:>8}/{n}")
    rapor["h_hastaici"][ad] = {"poz_medyan": float(poz_m), "neg_medyan": float(neg_m),
                               "artan": int(artan), "n": int(n)}

# --------------------------------------------------------------------------
# I. Pillar - ayri bulgu
# --------------------------------------------------------------------------
yaz()
yaz("## I. Pillar (ayri bulgu, ana karsilastirmanin disinda)")
eski_pillar = np.array([ast.literal_eval(x) for x in xl["Pillar_Ensemble_Skoru"]])[tut]
yaz(f"  Yeni paketteki pillar_y1_to_y6, projedeki Pillar_Ensemble_Skoru ile birebir ayni: "
    f"{np.allclose(eski_pillar, pillar)}")
sabit_p = int(np.isclose(pillar[:, 0], pillar[:, 5]).sum())
sabit_s = int(np.isclose(sybil[:, 0], sybil[:, 5]).sum())
yaz(f"  y1..y6 birebir sabit olan seri: Pillar {sabit_p}/{len(pillar)} ({sabit_p/len(pillar):.1%}), "
    f"Sybil {sabit_s}/{len(sybil)} ({sabit_s/len(sybil):.1%})")
a, lo, hi = auc_ga(pillar[:, 0], y1)
ah, loh, hih = auc_ga_hasta(hasta_duzeyi(pillar[:, 0]), h_y1)
yaz(f"  1. yil AUC seri  : {a:.3f} [{lo:.3f}; {hi:.3f}]   yayimlanmis held-out test: 0,945 [0,920; 0,969]")
yaz(f"  1. yil AUC hasta : {ah:.3f} [{loh:.3f}; {hih:.3f}]")
a_s, lo_s, hi_s = auc_ga(sybil[:, 0], y1)
yaz(f"  Karsilastirma - Sybil seri: {a_s:.3f} [{lo_s:.3f}; {hi_s:.3f}]  "
    f"yayimlanmis held-out test: 0,915 [0,878; 0,952]")
yaz("  -> Sybil yayimlanan degerle ortusuyor; Pillar yayimlanan araligin ustune kayiyor.")
rapor["i_pillar"] = {"eski_ile_ayni": bool(np.allclose(eski_pillar, pillar)),
                     "sabit_seri": sabit_p, "sybil_sabit_seri": sabit_s,
                     "seri_auc": [a, lo, hi], "hasta_auc": [ah, loh, hih],
                     "sybil_seri_auc": [a_s, lo_s, hi_s]}

# --------------------------------------------------------------------------
# J. Kestirme ve sizinti kontrolleri
# --------------------------------------------------------------------------
yaz()
yaz("## J. Kestirme (shortcut) ve sizinti kontrolleri")
man = pd.read_csv(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_manifest.csv")
man = man[tut].reset_index(drop=True)
shape = man["shape"].str.strip("()").str.split(", ", expand=True).astype(int)
zooms = man["zooms_mm"].str.strip("()").str.split(", ", expand=True).astype(float)
meta = np.column_stack([shape.values, zooms.values])
a_meta = roc_auc_score(y1, oof_skor(meta, y1, pid))
yaz(f"  Yalniz kayit metadatasindan (shape+zooms) 1. yil AUC = {a_meta:.3f}  (0,50 beklenir)")
prot = man["series_id"].str.extract(r"-(\d)OPA([A-Z]+)")[1].fillna("NA")
a_prot = roc_auc_score(y1, oof_skor(pd.get_dummies(prot).to_numpy(float), y1, pid))
yaz(f"  Yalniz cihaz/protokol dizgesinden 1. yil AUC   = {a_prot:.3f}")
rapor["j_kestirme"] = {"metadata_auc": a_meta, "protokol_auc": a_prot}

# --------------------------------------------------------------------------
# Kayit
# --------------------------------------------------------------------------
df_skor = pd.DataFrame({"series_key": keys, "patient_id": pid, "y1": y1, "y6": y6,
                        "censor_time": censor, "tarama_yili": tarama_yili,
                        "sybil_y1": sybil[:, 0], "pillar_y1": pillar[:, 0],
                        **{f"skor_{a}": skorlar[a] for a in EMB}})
df_skor.to_csv(CIKTI / "seri_skorlari.csv", index=False)
(CIKTI / "sonuclar.json").write_text(json.dumps(rapor, indent=2, ensure_ascii=False), encoding="utf-8")
(CIKTI / "ozet.txt").write_text("\n".join(satirlar), encoding="utf-8")
yaz()
yaz(f"Cikti: {CIKTI}")
