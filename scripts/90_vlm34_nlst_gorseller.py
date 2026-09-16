"""SUDE-VLM-34 gorselleri. Hasta goruntusu icermez, depoya girebilir.

Her sekil hem .svg hem .png olarak yazilir. Raporda .svg kullanilir: matplotlib
renkleri ogenin ustunde tasir (ayri bir <style> blogunda degil), bu yuzden
GitHub markdown icinde guvenle gomulur.

Cikti: outputs/vlm34/sekil_*.{svg,png}
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
from matplotlib.lines import Line2D
from sklearn.metrics import roc_auc_score, roc_curve

KOK = Path(__file__).resolve().parents[1]
CIKTI = KOK / "outputs/vlm34"

plt.rcParams.update({
    "figure.dpi": 140, "savefig.dpi": 140, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
RENK = {"Sybil": "#1f6feb", "SPECTRE": "#c2410c", "M3D": "#6b7280", "MG-3D": "#9ca3af",
        "Pillar": "#7c3aed"}


def kaydet(fig, ad: str) -> None:
    """SVG + PNG yaz. SVG'den DOCTYPE/DTD temizlenir: SVG 1.1 DTD kullanim disi ve
    DTD tasiyan XML bazi tuketicilerce (artifact yayimlama) reddediliyor."""
    for uz in ("svg", "png"):
        fig.savefig(CIKTI / f"{ad}.{uz}", bbox_inches="tight")
    p = CIKTI / f"{ad}.svg"
    p.write_text(re.sub(r"<!DOCTYPE[^>]*>\s*", "", p.read_text(encoding="utf-8")),
                 encoding="utf-8")

df = pd.read_csv(CIKTI / "seri_skorlari.csv", dtype={"patient_id": str, "tarama_yili": str})
sonuc = json.loads((CIKTI / "sonuclar.json").read_text(encoding="utf-8"))
pid, y1, y6, censor = (df["patient_id"].to_numpy(), df["y1"].to_numpy(),
                       df["y6"].to_numpy(), df["censor_time"].to_numpy())
skor = {"Sybil": df["sybil_y1"].to_numpy(), "SPECTRE": df["skor_SPECTRE"].to_numpy(),
        "M3D": df["skor_M3D"].to_numpy(), "MG-3D": df["skor_MG-3D"].to_numpy()}
pillar = df["pillar_y1"].to_numpy()
SIRA = ["Sybil", "SPECTRE", "M3D", "MG-3D"]


def hasta(s):
    return pd.Series(s, index=pid).groupby(level=0).max()


h_y1 = hasta(y1)
h_sira = h_y1.index.to_numpy()
hedef_h = h_y1.loc[h_sira].to_numpy()

# --------------------------------------------------------------------------
# Sekil 1 - ROC (hasta duzeyi, 1. yil)
# --------------------------------------------------------------------------
fig, axlar = plt.subplots(1, 2, figsize=(10, 4.4))
for ax, (duzey, s_al, hedef) in zip(
        axlar,
        [("Tarama başına · birincil (2.940 tarama, 41 pozitif)", lambda s: s, y1),
         ("Hasta-max · ikincil (1.198 hasta, 40 pozitif)",
          lambda s: hasta(s).loc[h_sira].to_numpy(), hedef_h)]):
    sp_ = s_al(pillar)
    fpr, tpr, _ = roc_curve(hedef, sp_)
    ax.plot(fpr, tpr, color=RENK["Pillar"], lw=2,
            label=f"Pillar  {roc_auc_score(hedef, sp_):.3f}")
    for ad in SIRA:
        s = s_al(skor[ad])
        fpr, tpr, _ = roc_curve(hedef, s)
        ax.plot(fpr, tpr, color=RENK[ad], lw=2 if ad in ("Sybil", "SPECTRE") else 1.2,
                label=f"{ad}  {roc_auc_score(hedef, s):.3f}")
    ax.plot([0, 1], [0, 1], color="#d1d5db", lw=0.8, ls=":")
    ax.set_xlabel("1 − özgüllük"); ax.set_ylabel("duyarlılık")
    ax.set_title(duzey, fontsize=9.5)  # baslik metni asagida tanimli
    ax.legend(loc="lower right", fontsize=7.6, frameon=False, title="AUC", title_fontsize=7.6)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
fig.suptitle("NLST · 1. yıl akciğer kanseri ayrımı", fontsize=11, y=0.99)
fig.tight_layout()
kaydet(fig, "sekil_1_roc")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 2 - Fonksiyonel ayrim: censor_time'a gore skor
# --------------------------------------------------------------------------
fig, axlar = plt.subplots(1, 2, figsize=(10, 4.2), sharey=False)
gruplar = [(f"kanser yok\nn={int((y6==0).sum())}", y6 == 0)] + [
    (f"{c}\nn={int(((y6==1)&(censor==c)).sum())}", (y6 == 1) & (censor == c)) for c in range(6)]
for ax, ad in zip(axlar, ["Sybil", "SPECTRE"]):
    veri = [skor[ad][m] for _, m in gruplar]
    bp = ax.boxplot(veri, widths=0.6, patch_artist=True, showfliers=False,
                    medianprops=dict(color="black", lw=1.4))
    for i, kutu in enumerate(bp["boxes"]):
        kutu.set(facecolor="#e5e7eb" if i == 0 else RENK[ad], alpha=0.35 if i else 0.6,
                 edgecolor="#4b5563", lw=0.8)
    for i, (_, m) in enumerate(gruplar, start=1):
        x = np.random.default_rng(i).normal(i, 0.055, m.sum())
        # rasterized: 2.800 nokta SVG'yi sisiriyor; metin ve eksenler vektor kaliyor
        ax.scatter(x, skor[ad][m], s=3.5, color="#374151", alpha=0.18 if i == 1 else 0.55,
                   lw=0, rasterized=True)
    ax.set_xticks(range(1, len(gruplar) + 1))
    ax.set_xticklabels([g[0] for g in gruplar], fontsize=8)
    ax.set_xlabel("tanıya kalan yıl (censor_time) · kanserli seriler")
    ax.set_ylabel(f"{ad} 1. yıl skoru")
    ax.set_title(ad, fontsize=10, color=RENK[ad])
fig.suptitle("Skorların tanıya kalan yıla göre dağılımı", fontsize=11, y=1.0)
fig.text(0.5, -0.05, "SPECTRE skoru yalnız tanı yılındaki taramada yükseliyor; Sybil tanıdan "
                     "yıllar önce de taban üstünde kalıyor.\ncensor_time bir tanı zamanı "
                     "etiketidir, görüntüde lezyon olup olmadığını söylemez.",
         ha="center", fontsize=7.8, color="#4b5563")
fig.tight_layout()
kaydet(fig, "sekil_2_fonksiyonel_ayrim")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 3 - Alarm butcesi vs yakalanan kanser
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.4, 4.4))
n_h = len(h_sira)
butceler = np.arange(10, 701, 10)
for ad in SIRA:
    s = hasta(skor[ad]).loc[h_sira].to_numpy()
    sirali = np.argsort(-s)
    yak = [hedef_h[sirali[:b]].sum() for b in butceler]
    ax.plot(butceler, yak, color=RENK[ad], lw=2 if ad in ("Sybil", "SPECTRE") else 1.2, label=ad)
ax.plot(butceler, butceler * hedef_h.sum() / n_h, color="#9ca3af", ls=":", lw=1.2,
        label="rastgele beklenti")
b_sybil = sonuc["d_butce"]["butce"]
ax.axvline(b_sybil, color="#1f6feb", ls="--", lw=0.9, alpha=0.7)
ax.annotate(f"Sybil 0,20 eşiği\n({b_sybil} hasta = %{b_sybil/n_h*100:.0f} alarm yükü)",
            xy=(b_sybil, 8), xytext=(b_sybil + 25, 6), fontsize=7.4, color="#1f6feb")
ax.axhline(hedef_h.sum(), color="#111827", ls=":", lw=0.8)
ax.text(690, hedef_h.sum() + 0.6, f"toplam {int(hedef_h.sum())} kanser", ha="right", fontsize=7.4)
ax.set_xlabel("alarm verilen hasta sayısı (bütçe)")
ax.set_ylabel("yakalanan 1. yıl kanseri")
ax.set_title("Sabit alarm bütçesinde yakalama (hasta düzeyi)", fontsize=10)
ax.legend(fontsize=8, frameon=False, loc="lower right")
fig.tight_layout()
kaydet(fig, "sekil_3_alarm_butcesi")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 4 - Yanlis pozitifler erken uyari mi?
# --------------------------------------------------------------------------
f = sonuc["f_erken_uyari"]
fm = sonuc["f_model"]
fig, ax = plt.subplots(figsize=(6.6, 4.1))
# Her model KENDI TN grubuyla karsilastirilir; ortak Sybil-TN paydasi yaniltiyordu.
gz = json.loads((CIKTI / "denetim_duzeltmeleri.json").read_text(encoding="utf-8"))["g_zenginlesme"]
adlar = ["Pillar", "Sybil", "SPECTRE", "M3D", "MG-3D"]
x = np.arange(len(adlar))
fp_o = [gz[a]["fp_oran"] * 100 for a in adlar]
tn_o = [gz[a]["tn_oran"] * 100 for a in adlar]
ax.bar(x - 0.19, fp_o, 0.38, color=[RENK[a] for a in adlar], alpha=0.9, label="alarm verilen (FP)")
ax.bar(x + 0.19, tn_o, 0.38, color="#9ca3af", alpha=0.65, label="alarm verilmeyen (TN)")
for i, a in enumerate(adlar):
    ax.text(i, max(fp_o[i], tn_o[i]) + 0.18, f"{gz[a]['zenginlesme']:.2f}×",
            ha="center", fontsize=8.5, fontweight="bold",
            color=RENK[a] if gz[a]["zenginlesme"] > 1.3 else "#6b7280")
ax.axhline(0, color=RENK["Sybil"], lw=0)
ax.set_xticks(x); ax.set_xticklabels(adlar, fontsize=8.5)
ax.set_ylabel("2.–6. yılda kanser çıkan hasta oranı (%)")
ax.set_ylim(0, max(fp_o + tn_o) * 1.32)
ax.set_title("Alarm verilen hastalar ileride daha sık kanser oluyor mu?", fontsize=10)
ax.legend(fontsize=7.8, frameon=False, loc="upper right")
fig.text(0.5, -0.07, "Her model kendi alarm verdiği ve vermediği hasta gruplarıyla "
                     "karşılaştırılır; eşit alarm yükünde.\nİleride kanser tanısı almak, "
                     "ilk alarmın doğru olduğunu lezyon kanıtı olmadan göstermez.",
         ha="center", fontsize=7.8, color="#4b5563")
fig.tight_layout()
kaydet(fig, "sekil_4_erken_uyari")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 5 - Hasta ici trajektori
# --------------------------------------------------------------------------
kans = df[df.y6 == 1]
uygun = kans.groupby("patient_id").filter(lambda g: len(g) > 1 and g.y1.nunique() > 1)
fig, axlar = plt.subplots(1, 2, figsize=(9.6, 4.2))
for ax, ad in zip(axlar, ["Sybil", "SPECTRE"]):
    kol = "sybil_y1" if ad == "Sybil" else "skor_SPECTRE"
    # x ekseni gercek zaman: taniya kalan yil, saga dogru azalir
    for p, g in uygun.groupby("patient_id"):
        g = g.sort_values("censor_time", ascending=False)
        ax.plot(-g["censor_time"].to_numpy(), g[kol].to_numpy(), color=RENK[ad],
                alpha=0.35, lw=1, marker="o", ms=3.5, mfc="white", mew=0.8)
        poz = g[g.y1 == 1]
        ax.scatter(-poz["censor_time"].to_numpy(), poz[kol].to_numpy(), s=28,
                   color=RENK[ad], zorder=3, edgecolor="white", lw=0.8)
    ust = int(uygun["censor_time"].max())
    ax.set_xticks(list(range(-ust, 1)))
    ax.set_xticklabels([str(-t) for t in range(-ust, 1)], fontsize=8)
    ax.set_xlabel("tanıya kalan yıl (censor_time)")
    ax.set_ylabel(f"{ad} 1. yıl skoru")
    ax.set_title(ad, fontsize=10, color=RENK[ad])
    ax.set_ylim(-0.03, 1.03)
fig.suptitle(f"Aynı hastanın ardışık taramalarında skor "
             f"({uygun.patient_id.nunique()} kanserli hasta)", fontsize=10.5, y=1.0)
fig.text(0.5, -0.06, "Dolu nokta = tanının konduğu yıldaki tarama (görüntüde lezyon "
                     "doğrulanmış değildir).\n12 hastanın yalnız 5'inde tarama protokolü "
                     "sabit kalmıştır; bu bir eşleştirilmiş kontrol değildir.",
         ha="center", fontsize=7.8, color="#4b5563")
fig.tight_layout()
kaydet(fig, "sekil_5_hasta_ici")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 6 - Permutasyon null
# --------------------------------------------------------------------------
ek = CIKTI / "eslestirilmis.json"
if ek.exists():
    e = json.loads(ek.read_text(encoding="utf-8"))
    if "permutasyon" in e:
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        adlar = ["SPECTRE", "M3D", "MG-3D"]
        for i, ad in enumerate(adlar):
            d = e["permutasyon"][ad]
            ax.plot(d["null_ga"], [i, i], color="#9ca3af", lw=7, alpha=0.5,
                    solid_capstyle="butt")
            ax.scatter(d["null_medyan"], i, marker="|", s=90, color="#4b5563", zorder=3)
            ax.scatter(d["gercek"], i, s=70, color=RENK[ad], zorder=4,
                       edgecolor="white", lw=1.2)
            holm = d.get("holm_p")
            etiket = f"{d['gercek']:.3f}  ({d['tekrar']} tekrar, ham p={d['p']:.3f}"
            etiket += f", Holm {holm:.3f})" if holm is not None else ")"
            ax.text(d["gercek"], i + 0.26, etiket, ha="center", fontsize=7.8, color=RENK[ad])
        ax.axvline(0.5, color="#111827", ls=":", lw=0.9)
        ax.set_yticks(range(len(adlar))); ax.set_yticklabels(adlar)
        ax.set_xlabel("1. yıl AUC (seri düzeyi)")
        ax.set_xlim(0.3, 1.02); ax.set_ylim(-1.05, len(adlar) - 0.15)
        ax.set_title("Ölçülen AUC, etiket permütasyonu null dağılımına karşı", fontsize=10)
        ax.legend(handles=[Line2D([], [], color="#9ca3af", lw=7, alpha=0.5,
                                  label="null %2,5–%97,5 bandı"),
                           Line2D([], [], marker="|", ls="", color="#4b5563", label="null medyanı"),
                           Line2D([], [], marker="o", ls="", color="#374151", label="ölçülen AUC")],
                  fontsize=7.4, frameon=False, loc="lower left", ncols=3)
        fig.text(0.5, -0.07, "Null bandı geniştir: 41 pozitifle eğitilen bir sınıflandırıcı, hiç "
                             "sinyal yokken bile 0,39–0,61 arası AUC üretebilir.\nSPECTRE bandın "
                             "çok dışında (Holm p = 0,030). M3D ve MG-3D bandın içinde: "
                             "ters sinyal değil, ölçülebilir sinyal yok.",
                 ha="center", fontsize=7.8, color="#4b5563")
        fig.tight_layout()
        kaydet(fig, "sekil_6_permutasyon")
        plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 9 - Rapor sekli 1: kucuk ek alarm butcelerinde FN kurtarma (tek panel)
# --------------------------------------------------------------------------
dd = json.loads((CIKTI / "denetim_duzeltmeleri.json").read_text(encoding="utf-8"))
kb = dd["e_kucuk_butce"]
butceler_k = [10, 25, 50, 100, 200]
fig, ax = plt.subplots(figsize=(6.6, 4.2))
for ad in ("Pillar", "SPECTRE", "M3D", "MG-3D"):
    ax.plot(butceler_k, [kb[str(b)][ad] for b in butceler_k], marker="o", ms=5,
            color=RENK[ad], lw=2 if ad in ("Pillar", "SPECTRE") else 1.3, label=ad)
ax.plot(butceler_k, [kb[str(b)]["beklenen"] for b in butceler_k], ls=":", color="#9ca3af",
        lw=1.4, label="rastgele beklenti")
ax.axhline(kb["kacan"], color="#111827", ls=":", lw=0.9)
ax.text(12, kb["kacan"] + 0.12, f"Sybil'in atladığı tüm hastalar = {kb['kacan']}",
        ha="left", va="bottom", fontsize=7.8, color="#374151")
ax.set_xlabel("Sybil'e eklenen ek alarm sayısı (hasta)")
ax.set_ylabel("yakalanan ek vaka")
ax.set_yticks(range(kb["kacan"] + 1))
ax.set_ylim(-0.25, kb["kacan"] + 0.9)
ax.set_xlim(0, 212)
ax.set_title(f"Atlanan kanserleri yakalamanın bedeli\n"
             f"(havuz {kb['havuz']} hasta, {kb['kacan']} atlanan vaka)", fontsize=10)
leg = ax.legend(fontsize=8, loc="lower right", bbox_to_anchor=(1.0, 0.02),
                frameon=True, framealpha=0.92, edgecolor="none")
leg.get_frame().set_facecolor("white")
kaydet(fig, "sekil_9_fn_kurtarma")
plt.close(fig)

# --------------------------------------------------------------------------
# Sekil 10 - Rapor sekli 2: vaka duzeyi FN matrisi (41 pozitif x 5 model)
# --------------------------------------------------------------------------
MOD = ["Pillar", "SPECTRE", "Sybil", "MG-3D", "M3D"]
tum = {**skor, "Pillar": pillar}
butce_seri = int((skor["Sybil"] >= 0.20).sum())
esikler = {m: (0.20 if m == "Sybil"
               else float(np.quantile(tum[m], 1 - butce_seri / len(tum[m])))) for m in MOD}
poz_i = np.where(y1 == 1)[0]
yakala = np.array([[tum[m][i] >= esikler[m] for m in MOD] for i in poz_i])
# satirlari: once kac model yakaliyor, sonra Sybil skoru
sira_i = np.lexsort((skor["Sybil"][poz_i], yakala.sum(1)))
yakala, poz_s = yakala[sira_i], poz_i[sira_i]

fig, ax = plt.subplots(figsize=(7.4, 8.4))
for j, m in enumerate(MOD):
    for i in range(len(poz_s)):
        if yakala[i, j]:
            ax.scatter(j, i, s=64, color=RENK[m], zorder=3, lw=0)
        else:
            ax.scatter(j, i, s=64, facecolor="none", edgecolor="#c8d0d8", lw=1.2, zorder=3)
ax.set_xticks(range(len(MOD)))
ax.set_xticklabels([f"{m}\n{int(yakala[:, j].sum())}/41" for j, m in enumerate(MOD)],
                   fontsize=9)
ax.xaxis.set_ticks_position("top")
etiketler = [f"{df['patient_id'].iloc[i]}" for i in poz_s]
ax.set_yticks(range(len(poz_s)))
ax.set_yticklabels(etiketler, fontsize=7.2, fontfamily="monospace")
# Sybil'in kacirdigi satirlari isaretle
sy_j = MOD.index("Sybil")
for i in range(len(poz_s)):
    if not yakala[i, sy_j]:
        ax.axhspan(i - 0.45, i + 0.45, color="#fbeceb", zorder=0)
ax.set_xlim(-0.6, len(MOD) - 0.4)
ax.set_ylim(-0.7, len(poz_s) - 0.3)
ax.invert_yaxis()
ax.grid(False)
for s in ("top", "right", "bottom", "left"):
    ax.spines[s].set_visible(False)
ax.set_title("Hangi model hangi kanseri yakalıyor?\n"
             "41 pozitif tarama, eşitlenmiş alarm yükünde", fontsize=10.5, pad=34)
fig.text(0.5, 0.055, "Dolu daire = yakalandı, boş daire = kaçırıldı. "
                     "Kırmızı şeritli satırlar Sybil'in kaçırdığı taramalar.\n"
                     "Sybil'in kaçırdığı altı taramanın altısını da Pillar yakalıyor; "
                     "hiçbir kanser üç modelden birden kaçmıyor.",
         ha="center", fontsize=8, color="#4b5563")
fig.tight_layout(rect=[0, 0.085, 1, 1])
kaydet(fig, "sekil_10_vaka_matrisi")
plt.close(fig)

print("Uretilen sekiller:")
for p in sorted(CIKTI.glob("sekil_*.png")):
    print(f"  {p.name}  ({p.stat().st_size//1024} KB)")
