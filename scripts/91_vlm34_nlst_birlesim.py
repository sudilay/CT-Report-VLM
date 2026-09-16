"""SUDE-VLM-34 - Sybil + SPECTRE birlesimi.

Gerekce: iki model ayni alarm yukunde hastalarin yalniz %56'sinda anlasiyor ve
fonksiyonel olarak farkli is yapiyorlar (SPECTRE mevcut lezyon, Sybil gelecek risk).
Birlesim tamamlayicilik icin alan var mi diye olculur.

Birlesim kurallari PARAMETRESIZ secildi; agirlik bu kohortta fit edilmedi:
  - sira ortalamasi (rank average): iki skorun yuzdelik sirasinin ortalamasi
  - VEYA kurali: butcenin yarisi her modelden, birlesim (ortusme kadar ust siradan tamamlanir)
Agirlik ogrenen bir birlesim (lojistik) 40 pozitifle ic ice CV ister; yapilmadi.

Cikti: outputs/vlm34/birlesim.json, ozet_birlesim.txt, sekil_7_birlesim.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score, roc_curve

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "outputs/vlm34"
BOOTSTRAP = 2000

rapor: dict = {}
satirlar: list[str] = []


def yaz(s: str = "") -> None:
    print(s)
    satirlar.append(s)


df = pd.read_csv(CIKTI / "seri_skorlari.csv", dtype={"patient_id": str})
sonuc = json.loads((CIKTI / "sonuclar.json").read_text(encoding="utf-8"))
pid = df["patient_id"].to_numpy()


def hasta(s):
    return pd.Series(s, index=pid).groupby(level=0).max()


h_y1 = hasta(df["y1"].to_numpy())
h_sira = h_y1.index.to_numpy()
hedef = h_y1.loc[h_sira].to_numpy()
h_y6 = hasta(df["y6"].to_numpy()).loc[h_sira].to_numpy()

s_sybil = hasta(df["sybil_y1"].to_numpy()).loc[h_sira].to_numpy()
s_spectre = hasta(df["skor_SPECTRE"].to_numpy()).loc[h_sira].to_numpy()
N = len(hedef)

# Parametresiz birlesim: yuzdelik sira ortalamasi
r_sybil = rankdata(s_sybil) / N
r_spectre = rankdata(s_spectre) / N
s_birlesim = (r_sybil + r_spectre) / 2

SKOR = {"Sybil": s_sybil, "SPECTRE": s_spectre, "Sybil+SPECTRE": s_birlesim}
RENK = {"Sybil": "#1f6feb", "SPECTRE": "#c2410c", "Sybil+SPECTRE": "#047857"}


def kaydet(fig, ad: str) -> None:
    for uzanti in ("svg", "png"):
        fig.savefig(CIKTI / f"{ad}.{uzanti}", bbox_inches="tight")

rng = np.random.default_rng(20260916)
BOOT = [rng.integers(0, N, N) for _ in range(BOOTSTRAP)]

yaz("=" * 74)
yaz("SUDE-VLM-34 - SYBIL + SPECTRE BIRLESIMI (hasta duzeyi, 1. yil kanseri)")
yaz("=" * 74)
yaz()
yaz(f"  {N} hasta, {int(hedef.sum())} pozitif")
yaz("  Birlesim kurali: yuzdelik sira ortalamasi (parametresiz; agirlik fit edilmedi)")
yaz()

# --- 1. AUC ---
yaz("## 1. Ayirma gucu")
yaz(f"  {'model':16s} {'AUC':>7} {'%95 GA':>18}")
rapor["auc"] = {}
for ad, s in SKOR.items():
    a = roc_auc_score(hedef, s)
    orn = [roc_auc_score(hedef[ii], s[ii]) for ii in BOOT
           if 0 < hedef[ii].sum() < len(ii)]
    lo, hi = np.percentile(orn, [2.5, 97.5])
    yaz(f"  {ad:16s} {a:>7.3f} [{lo:.3f}; {hi:.3f}]")
    rapor["auc"][ad] = {"auc": a, "ga": [lo, hi]}

yaz()
yaz("## 2. Eslestirilmis farklar (ayni bootstrap ornegi)")
yaz(f"  {'karsilastirma':30s} {'DeltaAUC':>9} {'%95 GA':>20} {'p':>8}")
rapor["fark"] = {}
for a, b in [("Sybil+SPECTRE", "Sybil"), ("Sybil+SPECTRE", "SPECTRE"), ("SPECTRE", "Sybil")]:
    d = roc_auc_score(hedef, SKOR[a]) - roc_auc_score(hedef, SKOR[b])
    orn = np.array([roc_auc_score(hedef[ii], SKOR[a][ii]) - roc_auc_score(hedef[ii], SKOR[b][ii])
                    for ii in BOOT if 0 < hedef[ii].sum() < len(ii)])
    lo, hi = np.percentile(orn, [2.5, 97.5])
    p = float(min(1.0, 2 * min((orn <= 0).mean(), (orn >= 0).mean())))
    yaz(f"  {a+' - '+b:30s} {d:>+9.3f} [{lo:>+7.3f}; {hi:>+7.3f}] {p:>8.4f}")
    rapor["fark"][f"{a}-{b}"] = {"fark": d, "ga": [lo, hi], "p": p}

# --- 3. Sabit alarm butcesinde ---
butce = sonuc["d_butce"]["butce"]
yaz()
yaz(f"## 3. Sabit alarm butcesi ({butce} hasta = Sybil'in 0,20 esigindeki yuku)")
yaz(f"  {'kural':26s} {'TP':>4} {'FN':>4} {'FP':>5} {'duyarlilik':>11} {'PPV':>7}")
rapor["butce"] = {"butce": butce}


def butce_sonuc(ad: str, secim: np.ndarray) -> None:
    tp = int(hedef[secim].sum())
    fn = int(hedef.sum() - tp)
    yaz(f"  {ad:26s} {tp:>4} {fn:>4} {len(secim)-tp:>5} {tp/hedef.sum():>11.3f} {tp/len(secim):>7.3f}")
    rapor["butce"][ad] = {"TP": tp, "FN": fn, "FP": len(secim) - tp, "n": len(secim)}


for ad, s in SKOR.items():
    butce_sonuc(ad, np.argsort(-s)[:butce])

# VEYA kurali: her modelden butcenin yarisi, birlesim
yari = butce // 2
u_s = set(np.argsort(-s_sybil)[:yari])
u_p = set(np.argsort(-s_spectre)[:yari])
birlik = u_s | u_p
# ortusme yuzunden butcenin altinda kalirsa sira ortalamasindan tamamla
if len(birlik) < butce:
    for i in np.argsort(-s_birlesim):
        if len(birlik) >= butce:
            break
        birlik.add(int(i))
butce_sonuc(f"VEYA (her modelden {yari})", np.array(sorted(birlik)))
rapor["veya_ortusme"] = len(u_s & u_p)
yaz(f"  (VEYA kuralinda iki modelin ust {yari} listesi {len(u_s & u_p)} hastada ortusuyor)")

# --- 4. Butce egrisi ---
yaz()
yaz("## 4. Farkli butcelerde yakalanan kanser")
yaz(f"  {'butce':>6} {'Sybil':>7} {'SPECTRE':>9} {'birlesim':>10}")
rapor["egri"] = {}
for b in (100, 200, 300, 428, 600):
    sat = {ad: int(hedef[np.argsort(-s)[:b]].sum()) for ad, s in SKOR.items()}
    yaz(f"  {b:>6} {sat['Sybil']:>7} {sat['SPECTRE']:>9} {sat['Sybil+SPECTRE']:>10}")
    rapor["egri"][b] = sat

# --- 5. Birlesimin FP'leri erken uyari mi ---
yaz()
yaz("## 5. Birlesimin yanlis pozitifleri")
taban = sonuc["f_erken_uyari"]["tn_gec_kanser"] / sonuc["f_erken_uyari"]["tn_n"]
yaz(f"  {'model':16s} {'FP':>5} {'2-6y kanser':>12} {'oran':>7} {'zenginlesme':>12}")
rapor["fp_erken"] = {}
for ad, s in SKOR.items():
    ust = np.argsort(-s)[:butce]
    fp_i = ust[hedef[ust] == 0]
    g = int(h_y6[fp_i].sum())
    yaz(f"  {ad:16s} {len(fp_i):>5} {g:>12} {g/len(fp_i):>7.1%} {(g/len(fp_i))/taban:>11.2f}x")
    rapor["fp_erken"][ad] = {"fp": len(fp_i), "gec_kanser": g, "oran": g / len(fp_i)}

# --- Sekil ---
plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 140, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
                     "figure.facecolor": "white", "axes.facecolor": "white"})
fig, axlar = plt.subplots(1, 2, figsize=(10, 4.3))

ax = axlar[0]
for ad, s in SKOR.items():
    fpr, tpr, _ = roc_curve(hedef, s)
    ax.plot(fpr, tpr, color=RENK[ad], lw=2.2 if "+" in ad else 1.5,
            label=f"{ad}  {roc_auc_score(hedef, s):.3f}")
ax.plot([0, 1], [0, 1], color="#d1d5db", lw=0.8, ls=":")
ax.set_xlabel("1 − özgüllük"); ax.set_ylabel("duyarlılık")
ax.set_title("ROC · hasta düzeyi, 1. yıl kanseri", fontsize=9.5)
ax.legend(loc="lower right", fontsize=8, frameon=False, title="AUC", title_fontsize=8)
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)

ax = axlar[1]
butceler = np.arange(10, 701, 10)
for ad, s in SKOR.items():
    sirali = np.argsort(-s)
    ax.plot(butceler, [hedef[sirali[:b]].sum() for b in butceler], color=RENK[ad],
            lw=2.2 if "+" in ad else 1.5, label=ad)
ax.plot(butceler, butceler * hedef.sum() / N, color="#9ca3af", ls=":", lw=1.2,
        label="rastgele beklenti")
ax.axvline(butce, color="#6b7280", ls="--", lw=0.9)
ax.annotate(f"Sybil 0,20 eşiği\n({butce} hasta)", xy=(butce, 6), xytext=(butce + 22, 4),
            fontsize=7.4, color="#6b7280")
ax.axhline(hedef.sum(), color="#111827", ls=":", lw=0.8)
ax.text(690, hedef.sum() + 0.6, f"toplam {int(hedef.sum())} kanser", ha="right", fontsize=7.4)
ax.set_xlabel("alarm verilen hasta sayısı (bütçe)")
ax.set_ylabel("yakalanan 1. yıl kanseri")
ax.set_title("Sabit alarm bütçesinde yakalama", fontsize=9.5)
ax.legend(fontsize=8, frameon=False, loc="lower right")

fig.suptitle("Sybil + SPECTRE birleşimi (sıra ortalaması, parametresiz)", fontsize=11, y=1.0)
fig.tight_layout()
kaydet(fig, "sekil_7_birlesim")
plt.close(fig)

(CIKTI / "birlesim.json").write_text(json.dumps(rapor, indent=2, ensure_ascii=False), encoding="utf-8")
(CIKTI / "ozet_birlesim.txt").write_text("\n".join(satirlar), encoding="utf-8")
yaz()
yaz(f"Cikti: {CIKTI}/birlesim.json, sekil_7_birlesim.png")
