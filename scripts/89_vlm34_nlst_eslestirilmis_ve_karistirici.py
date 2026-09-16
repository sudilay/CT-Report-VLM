"""SUDE-VLM-34 eki - eslestirilmis model farklari ve sans-alti AUC'nin kok nedeni.

1) SPECTRE vs Sybil farki: ayni hasta-kumeli bootstrap ornekleminde eslestirilmis GA.
2) M3D/MG-3D neden sans altinda? Kohortta kayit teknigi ile sonlanim arasinda
   karistirici (confounder) var mi; modeller patolojiyi mi kayit teknigini mi tasiyor?

Cikti: outputs/vlm34/eslestirilmis.json, outputs/vlm34/ozet_ek.txt
"""
from __future__ import annotations

import json
from pathlib import Path

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
BOOTSTRAP = 2000
TOHUMLAR = [0, 1, 2, 3, 4]

rapor: dict = {}
satirlar: list[str] = []


def yaz(s: str = "") -> None:
    print(s)
    satirlar.append(s)


df = pd.read_csv(CIKTI / "seri_skorlari.csv", dtype={"patient_id": str, "tarama_yili": str})
pid = df["patient_id"].to_numpy()
y1 = df["y1"].to_numpy()
y6 = df["y6"].to_numpy()
censor = df["censor_time"].to_numpy()

SIRA = ["Sybil", "SPECTRE", "M3D", "MG-3D"]
skor = {"Sybil": df["sybil_y1"].to_numpy(), "SPECTRE": df["skor_SPECTRE"].to_numpy(),
        "M3D": df["skor_M3D"].to_numpy(), "MG-3D": df["skor_MG-3D"].to_numpy()}

hastalar = np.unique(pid)
idx_pid = {p: np.where(pid == p)[0] for p in hastalar}
rng = np.random.default_rng(20260916)
BOOT = [np.concatenate([idx_pid[p] for p in rng.choice(hastalar, len(hastalar), replace=True)])
        for _ in range(BOOTSTRAP)]

yaz("=" * 78)
yaz("SUDE-VLM-34 EKI - ESLESTIRILMIS FARKLAR VE KARISTIRICI KONTROLU")
yaz("=" * 78)

# --------------------------------------------------------------------------
# 1. Eslestirilmis farklar
# --------------------------------------------------------------------------
yaz()
yaz("## 1. Eslestirilmis model farklari (1. yil, seri duzeyi, ayni bootstrap ornegi)")
yaz("   Ayni hasta-kumeli bootstrap ornekleminde iki modelin AUC farki hesaplanir.")
yaz()


def eslestirilmis(a: str, b: str) -> dict:
    fark = roc_auc_score(y1, skor[a]) - roc_auc_score(y1, skor[b])
    orn = []
    for ii in BOOT:
        h = y1[ii]
        if h.sum() == 0 or h.sum() == len(h):
            continue
        orn.append(roc_auc_score(h, skor[a][ii]) - roc_auc_score(h, skor[b][ii]))
    orn = np.array(orn)
    lo, hi = np.percentile(orn, [2.5, 97.5])
    # iki yanli bootstrap p: farkin 0'i icermesi
    p = 2 * min((orn <= 0).mean(), (orn >= 0).mean())
    return {"fark": fark, "ga": [lo, hi], "p": float(min(p, 1.0))}


yaz(f"  {'karsilastirma':24s} {'DeltaAUC':>9} {'%95 GA':>20} {'p':>9}")
rapor["eslestirilmis"] = {}
ciftler = [("SPECTRE", "Sybil"), ("SPECTRE", "M3D"), ("SPECTRE", "MG-3D"),
           ("Sybil", "M3D"), ("Sybil", "MG-3D"), ("MG-3D", "M3D")]
for a, b in ciftler:
    r = eslestirilmis(a, b)
    yaz(f"  {a+' - '+b:24s} {r['fark']:>+9.3f} [{r['ga'][0]:>+7.3f}; {r['ga'][1]:>+7.3f}] {r['p']:>9.4f}")
    rapor["eslestirilmis"][f"{a}-{b}"] = r

yaz()
yaz("  Holm duzeltmesi (6 karsilastirma):")
ps = sorted(((v["p"], k) for k, v in rapor["eslestirilmis"].items()))
m = len(ps)
onceki = 0.0
for i, (p, k) in enumerate(ps):
    duz = min(1.0, max(onceki, (m - i) * p))
    onceki = duz
    rapor["eslestirilmis"][k]["holm_p"] = duz
    yaz(f"    {k:24s} ham p={p:.4f}  Holm p={duz:.4f}  {'anlamli' if duz < 0.05 else '-'}")

# --------------------------------------------------------------------------
# 2. Sans-alti AUC'nin kok nedeni
# --------------------------------------------------------------------------
yaz()
yaz("## 2. M3D ve MG-3D neden sansin ALTINDA? (AUC 0,41 ve 0,49)")
yaz("   Sans-alti AUC rastgele gurultu degildir: sistematik ters siralama demektir.")
yaz("   Hipotez: kohortta kayit teknigi ile sonlanim arasinda karistirici var; bu iki")
yaz("   model patoloji yerine kayit teknigini tasiyor.")
yaz()

man = pd.read_csv(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_manifest.csv")
man = man.set_index("series_key").loc[df["series_key"]].reset_index()
shape = man["shape"].str.strip("()").str.split(", ", expand=True).astype(int)
zooms = man["zooms_mm"].str.strip("()").str.split(", ", expand=True).astype(float)
meta = pd.DataFrame({"kesit_sayisi": shape[2].values, "kesit_kalinligi": zooms[2].values,
                     "piksel_mm": zooms[0].values})
meta["uretici"] = man["series_id"].str.extract(r"-(\d)OPA([A-Z]+)")[1].fillna("NA")

yaz("  2a. Kayit parametrelerinin tek basina yonu (1. yil hedefi, ham AUC)")
for kol in ["kesit_sayisi", "kesit_kalinligi", "piksel_mm"]:
    a = roc_auc_score(y1, meta[kol])
    yaz(f"    {kol:18s} AUC={a:.3f}  (poz medyan={meta.loc[y1==1,kol].median():.3f}, "
        f"neg medyan={meta.loc[y1==0,kol].median():.3f})")
rapor["karistirici_tekil"] = {k: float(roc_auc_score(y1, meta[k]))
                              for k in ["kesit_sayisi", "kesit_kalinligi", "piksel_mm"]}

yaz()
yaz("  2b. Uretici/protokol basina 1. yil kanser orani")
g = pd.DataFrame({"uretici": meta["uretici"], "y1": y1}).groupby("uretici").agg(
    n=("y1", "size"), poz=("y1", "sum"))
g["oran"] = g["poz"] / g["n"]
g = g.sort_values("oran", ascending=False)
for u, r in g[g["n"] >= 50].iterrows():
    yaz(f"    {u:18s} n={int(r['n']):>5} poz={int(r['poz']):>3} oran={r['oran']:.2%}")
rapor["uretici_oran"] = {str(u): {"n": int(r["n"]), "poz": int(r["poz"]), "oran": float(r["oran"])}
                         for u, r in g.iterrows()}

yaz()
yaz("  2c. Modeller kayit teknigini ne kadar tasiyor? (embeddingden kesit kalinligi tahmini)")
yaz("      Hedef: kesit kalinligi medyanin ustunde mi (ikili). Yuksek AUC = model teknigi kodluyor.")
EMB = {
    "SPECTRE": np.load(BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_embeddings.npz",
                       allow_pickle=True)["cls_embeds"],
    "M3D": np.load(BASE / "m3d/nlst_full_cohort_2965/m3d_nlst_full_2965_embeddings.npz",
                   allow_pickle=True)["embeddings"],
    "MG-3D": np.load(BASE / "mg3d/nlst_full_cohort_2965/mg3d_nlst_full_2965_embeddings.npz",
                     allow_pickle=True)["embeddings"],
}
keys_ham = np.array([str(s) for s in np.load(
    BASE / "spectre/nlst_full_cohort_2965/spectre_nlst_full_2965_embeddings.npz",
    allow_pickle=True)["series_keys"]])
konum = pd.Series(np.arange(len(keys_ham)), index=keys_ham).loc[df["series_key"]].to_numpy()
EMB = {k: v[konum] for k, v in EMB.items()}

kalin = (meta["kesit_kalinligi"] > meta["kesit_kalinligi"].median()).astype(int).to_numpy()
uretici_hedef = (meta["uretici"] == meta["uretici"].mode()[0]).astype(int).to_numpy()


def oof(X, hedef, gruplar):
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


yaz(f"    {'model':10s} {'kesit kalinligi':>16} {'uretici':>10}")
rapor["teknik_kodlama"] = {}
for ad, X in EMB.items():
    a_k = roc_auc_score(kalin, oof(X, kalin, pid))
    a_u = roc_auc_score(uretici_hedef, oof(X, uretici_hedef, pid))
    yaz(f"    {ad:10s} {a_k:>16.3f} {a_u:>10.3f}")
    rapor["teknik_kodlama"][ad] = {"kesit_kalinligi_auc": a_k, "uretici_auc": a_u}

yaz()
yaz("  2d. Karistirici katman icinde (uretici sabit tutularak) 1. yil AUC")
yaz("      Her uretici grubunda ayri AUC, grup buyuklugune gore agirlikli ortalama.")
rapor["katman_ici"] = {}
for ad in SIRA:
    paylar, agirliklar = [], []
    for u, r in g.iterrows():
        m_u = (meta["uretici"] == u).to_numpy()
        if m_u.sum() < 50 or y1[m_u].sum() < 3:
            continue
        paylar.append(roc_auc_score(y1[m_u], skor[ad][m_u]))
        agirliklar.append(m_u.sum())
    a = float(np.average(paylar, weights=agirliklar))
    yaz(f"    {ad:10s} katman-ici AUC={a:.3f}  (ham AUC={roc_auc_score(y1, skor[ad]):.3f}, "
        f"{len(paylar)} uretici grubu)")
    rapor["katman_ici"][ad] = {"katman_ici_auc": a, "ham_auc": float(roc_auc_score(y1, skor[ad])),
                               "grup": len(paylar)}

# --------------------------------------------------------------------------
# 3. Permutasyon null - bootstrap GA yeterli mi?
# --------------------------------------------------------------------------
yaz()
yaz("## 3. Permutasyon null: lineer probun BOS hipotez altindaki AUC dagilimi")
yaz("   Etiketler HASTA duzeyinde permute edilip kat-disi AUC null dagilimi olculur.")
yaz()
yaz("   HAT ESLESMESI (denetim duzeltmesi): null ile karsilastirilan 'gercek' deger de")
yaz("   permutasyonla BIREBIR AYNI hattan uretilir - tek kat bolunmesi (tohum 0),")
yaz("   max_iter=3000. Raporun baska yerlerindeki 5 tohum ortalamasi DEGILDIR;")
yaz("   ortalama varyansi dusurur, bu yuzden iki deger karistirilmamalidir.")
yaz()
yaz("   Tekrar sayisi modele gore: M3D'nin p degeri 0,05 civarinda oldugu icin")
yaz("   orada cok daha fazla tekrar gerekir.")
yaz()
PERM = {"SPECTRE": 200, "M3D": 1000, "MG-3D": 200}
rng_p = np.random.default_rng(20260916)
h_y1 = pd.Series(y1, index=pid).groupby(level=0).max()


def tek_tohum_oof(X: np.ndarray, hedef: np.ndarray) -> np.ndarray:
    """Permutasyon ve gercek deger icin ORTAK hat. Tek kat bolunmesi, tohum 0."""
    cv_t = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
    p = np.zeros(len(hedef))
    for tr, te in cv_t.split(X, hedef, pid):
        mdl = make_pipeline(StandardScaler(),
                            LogisticRegression(C=1, max_iter=3000, class_weight="balanced"))
        mdl.fit(X[tr], hedef[tr])
        p[te] = mdl.predict_proba(X[te])[:, 1]
    return p


yaz(f"  {'model':10s} {'tekrar':>7} {'gercek(1 tohum)':>16} {'5 tohum':>9} {'null medyan':>12} "
    f"{'null %2,5-%97,5':>22} {'p':>8}")
rapor["permutasyon"] = {"hat": "tek tohum (0), max_iter=3000; gercek ve null ayni hat"}
for ad, X in EMB.items():
    n_tekrar = PERM[ad]
    gercek = roc_auc_score(y1, tek_tohum_oof(X, y1))   # null ile AYNI hat
    bes_tohum = roc_auc_score(y1, skor[ad])            # raporun geri kalaninda kullanilan
    null = []
    for _ in range(n_tekrar):
        ph = h_y1.copy()
        ph[:] = rng_p.permutation(ph.values)
        yp = ph.loc[pid].to_numpy()
        null.append(roc_auc_score(yp, tek_tohum_oof(X, yp)))
    null = np.array(null)
    lo, hi = np.percentile(null, [2.5, 97.5])
    # (1+k)/(1+n) tarzi, sifir gozlemde bile sonlu p verir
    alt = (1 + int((null <= gercek).sum())) / (1 + n_tekrar)
    ust = (1 + int((null >= gercek).sum())) / (1 + n_tekrar)
    pv = float(min(1.0, 2 * min(alt, ust)))
    yaz(f"  {ad:10s} {n_tekrar:>7} {gercek:>16.3f} {bes_tohum:>9.3f} {np.median(null):>12.3f} "
        f"[{lo:>8.3f}; {hi:>8.3f}] {pv:>8.4f}")
    rapor["permutasyon"][ad] = {"tekrar": n_tekrar, "gercek": gercek, "bes_tohum": bes_tohum,
                                "null_medyan": float(np.median(null)),
                                "null_ga": [float(lo), float(hi)], "p": pv}
ps = sorted((rapor["permutasyon"][a]["p"], a) for a in EMB)
m_p = len(ps)
onceki = 0.0
yaz()
yaz("  Holm duzeltmesi (3 model birlikte sinandi):")
for i, (p, k) in enumerate(ps):
    duz = min(1.0, max(onceki, (m_p - i) * p))
    onceki = duz
    rapor["permutasyon"][k]["holm_p"] = duz
    yaz(f"    {k:10s} ham p={p:.3f}  Holm p={duz:.3f}  "
        f"{'anlamli' if duz < 0.05 else 'anlamli DEGIL'}")

yaz()
yaz("  Yorum notu (denetim duzeltmesi): bootstrap GA ile permutasyon null'i AYNI SEYI")
yaz("  olcmez, biri digerinden 'dogru' degildir.")
yaz("    - Bootstrap: sabit, egitilmis bir OOF skorun orneklem belirsizligi.")
yaz("      Soru: 'bu skoru baska hastalarda olcsek AUC ne olurdu?'")
yaz("    - Permutasyon: etiket-sonuc baginin olmadigi durumda, YENIDEN EGITIMLI hattin")
yaz("      davranisi. Soru: 'bu hat hic sinyal yokken hangi AUC'leri uretir?'")
yaz("  Ikisi farkli sorulara cevap verdigi icin aralik genislikleri de farklidir; sans")
yaz("  duzeyine yakin degerleri yorumlarken permutasyon daha uygun referanstir, ama")
yaz("  bootstrap 'yanlis' degildir.")

(CIKTI / "eslestirilmis.json").write_text(json.dumps(rapor, indent=2, ensure_ascii=False), encoding="utf-8")
(CIKTI / "ozet_ek.txt").write_text("\n".join(satirlar), encoding="utf-8")
yaz()
yaz(f"Cikti: {CIKTI}/eslestirilmis.json")
