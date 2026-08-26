# -*- coding: utf-8 -*-
"""A2 / TASK-08: Sablon cumle istatistigi ve esik adaylari.

Kararlar:
  D11 - Istatistik YALNIZCA train hastalarindan hesaplanir (valid'den sizinti olmasin).
  D11 - Sayim HASTA bazindadir; bir hastanin birden cok calismasi cumleyi sisirmesin.
  D3  - Yalnizca sayilar maskelenir. Anatomi ve taraf (right/left, lob, segment)
        klinik olarak anlamli oldugu icin KORUNUR. Tarih ayrimi yapilmaz
        (raporlarin %99,6'sinda tarih yok).

Cikti:
  reports/sablon_dagilimi.csv     esik adaylari ve kapsama oranlari
  reports/figures/sablon_dagilimi.png
  reports/en_sik_sablonlar.csv    elle etiketleme icin ilk N sablon

Kullanim:  .venv/Scripts/python.exe scripts/05_template_stats.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import re  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SENT = ROOT / "data" / "processed" / "sentences.parquet"
REPS = ROOT / "data" / "processed" / "reports_study_level.parquet"
OUTD = ROOT / "reports"
FIGD = OUTD / "figures"

SAYI = re.compile(r"\d+(?:\.\d+)?")
BOSLUK = re.compile(r"\s+")
ESIKLER = [2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
ELLE_ETIKET_N = 250


def normalize(metin: str) -> str:
    """D3: sayilari maskele, bosluklari sadelestir, kucuk harfe indir.
    Anatomi ve taraf bilgisi KORUNUR."""
    return BOSLUK.sub(" ", SAYI.sub("<NUM>", metin.lower())).strip()


def main() -> None:
    OUTD.mkdir(exist_ok=True)
    FIGD.mkdir(parents=True, exist_ok=True)

    sent = pd.read_parquet(SENT)
    reps = pd.read_parquet(REPS, columns=["study_id", "patient_id", "split"])
    sent = sent.merge(reps, on="study_id", how="left")

    # --- D11: yalnizca train ---
    train = sent[sent.split == "train"].copy()
    print(f"toplam cumle          : {len(sent):,}")
    print(f"train cumle (kullanilan): {len(train):,}  "
          f"({train.patient_id.nunique():,} hasta)")
    print(f"valid cumle (haric)   : {len(sent) - len(train):,}")

    train["norm"] = train.text.map(normalize)

    # --- D11: HASTA bazinda sayim ---
    hasta = train.groupby("norm")["patient_id"].nunique().rename("n_hasta")
    cumle = train.groupby("norm").size().rename("n_cumle")
    tab = pd.concat([hasta, cumle], axis=1).sort_values("n_hasta", ascending=False)
    tab["rank"] = range(1, len(tab) + 1)

    print(f"\nbenzersiz normalize cumle: {len(tab):,}")
    print(f"tek hastada gecen        : {(tab.n_hasta == 1).sum():,} "
          f"(%{100*(tab.n_hasta == 1).mean():.1f})")

    # --- Esik adaylari ---
    toplam = len(train)
    satirlar = []
    for k in ESIKLER:
        sec = tab[tab.n_hasta >= k]
        satirlar.append({
            "esik_K": k,
            "sablon_ailesi": len(sec),
            "kapsanan_cumle": int(sec.n_cumle.sum()),
            "kapsama_yuzde": round(100 * sec.n_cumle.sum() / toplam, 1),
        })
    dag = pd.DataFrame(satirlar)
    dag.to_csv(OUTD / "sablon_dagilimi.csv", index=False)

    print("\nESIK ADAYLARI (train, hasta bazinda)")
    print("-" * 62)
    print(f"{'K':>6} {'sablon ailesi':>15} {'kapsanan cumle':>16} {'kapsama':>9}")
    for r in satirlar:
        print(f"{r['esik_K']:>6} {r['sablon_ailesi']:>15,} "
              f"{r['kapsanan_cumle']:>16,} {r['kapsama_yuzde']:>8.1f}%")

    # --- Grafik ---
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    ax[0].loglog(tab["rank"], tab["n_hasta"], lw=1.1, color="#0284c7")
    ax[0].set_xlabel("Sablon sirasi (rank)")
    ax[0].set_ylabel("Gectigi hasta sayisi")
    ax[0].set_title("Sablon frekans dagilimi (log-log)")
    ax[0].grid(alpha=.3, which="both")
    for k in (10, 100, 1000):
        ax[0].axhline(k, ls="--", lw=.8, color="#94a3b8")

    ax[1].plot(dag.esik_K, dag.kapsama_yuzde, "o-", color="#dc2626")
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Esik K (en az kac hastada)")
    ax[1].set_ylabel("Kapsanan cumle yuzdesi")
    ax[1].set_title("Esige gore kapsama")
    ax[1].grid(alpha=.3)
    for _, r in dag.iterrows():
        ax[1].annotate(f"{r.kapsama_yuzde:.0f}%", (r.esik_K, r.kapsama_yuzde),
                       textcoords="offset points", xytext=(0, 7), fontsize=8, ha="center")
    fig.tight_layout()
    fig.savefig(FIGD / "sablon_dagilimi.png", dpi=140)
    print(f"\ngrafik: reports/figures/sablon_dagilimi.png")

    # --- Elle etiketleme listesi ---
    ust = tab.head(ELLE_ETIKET_N).reset_index()
    # her normalize sablon icin bir ornek ham cumle
    ornek = train.drop_duplicates("norm").set_index("norm")["text"]
    ust["ornek_ham_cumle"] = ust["norm"].map(ornek)
    ust["template_type"] = ""      # elle doldurulacak
    ust["malignite_ilgili"] = ""   # Faz 3 icin not; Faz 1'de KULLANILMAZ
    ust.to_csv(OUTD / "en_sik_sablonlar.csv", index=False, encoding="utf-8-sig")
    kaps = 100 * tab.head(ELLE_ETIKET_N).n_cumle.sum() / toplam
    print(f"elle etiketleme listesi: reports/en_sik_sablonlar.csv "
          f"(ilk {ELLE_ETIKET_N}, cumlelerin %{kaps:.1f}'ini kapsiyor)")


if __name__ == "__main__":
    main()
