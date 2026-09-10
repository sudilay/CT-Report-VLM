"""BTB3D degerlendirmesi · CT-RATE 500 · metrik hesabi.

Girdi : outputs/btb3d_ctrate_muhurlu/ctrate500_18sinif.parquet  (betik 74)
Cikti : ayni dizine metrik tablolari + Excel

Uc olcum yapilir:

  KALIBRASYON  B ↔ A · kendi cikaricimiz GT hekim raporunda, resmi etikete
               karsi. Bu, C ↔ A icin ULASILABILIR TAVANDIR; altkume secimi
               bu tavana gore yapilir.
  OLCUM        C ↔ A · BTB3D uretilmis raporu, resmi etikete karsi.
  TABAN        Ayni pozitif oranini rastgele dagitan tahmin edicinin
               beklenen F1'i. F1'in mutlak degeri prevalansa bagli oldugu
               icin TEK BASINA yorumlanamaz; fark ve MCC raporlanir.

Guven araligi: 10.000 tekrarli, RAPOR duzeyinde (kumeleme yok - her
seri bagimsiz bir volum) bootstrap, yuzde 2,5 / 97,5.

⛔ DUVAR: girdi CT-RATE valid muhurlu havuzudur; ciktilar karantina
   dizinine yazilir ve depoya girmez.

Kullanim:
    python scripts/75_btb3d_ctrate_metrik.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
KARANTINA = KOK / "outputs/btb3d_ctrate_muhurlu"
GIRDI = KARANTINA / "ctrate500_18sinif.parquet"

TEKRAR = 10_000
TOHUM = 20260910
KALIBRASYON_ESIGI = 0.85


# ------------------------------------------------------------------ metrik

def _sayimlar(y: np.ndarray, p: np.ndarray) -> tuple[int, int, int, int]:
    return (int(((y == 1) & (p == 1)).sum()), int(((y == 0) & (p == 1)).sum()),
            int(((y == 1) & (p == 0)).sum()), int(((y == 0) & (p == 0)).sum()))


def prf(y: np.ndarray, p: np.ndarray) -> tuple[float, float, float]:
    tp, fp, fn, _ = _sayimlar(y, p)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return pr, rc, f1


def mcc(y: np.ndarray, p: np.ndarray) -> float:
    tp, fp, fn, tn = _sayimlar(y, p)
    payda = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / payda if payda else 0.0


def sans_f1(y: np.ndarray, p: np.ndarray) -> float:
    """Ayni pozitif ORANINI rastgele dagitan tahmin edicinin beklenen F1'i.

    precision -> prevalans, recall -> tahmin orani; ikisinin harmonik ortalamasi.
    """
    n = len(y)
    a, c = int(y.sum()), int(p.sum())
    return 2 * a * c / (n * (a + c)) if (a + c) else 0.0


def makro_f1(d: pd.DataFrame, siniflar: list[str], kaynak: str,
             idx: np.ndarray | None = None) -> float:
    f = []
    for s in siniflar:
        y = d[f"A::{s}"].values
        p = d[f"{kaynak}::{s}"].values
        if idx is not None:
            y, p = y[idx], p[idx]
        f.append(prf(y, p)[2])
    return float(np.mean(f))


def bootstrap_makro(d: pd.DataFrame, siniflar: list[str],
                    kaynak: str) -> tuple[float, float]:
    rng = np.random.default_rng(TOHUM)
    n = len(d)
    ornekler = np.empty(TEKRAR)
    for i in range(TEKRAR):
        idx = rng.integers(0, n, n)
        ornekler[i] = makro_f1(d, siniflar, kaynak, idx)
    return float(np.percentile(ornekler, 2.5)), float(np.percentile(ornekler, 97.5))


def main() -> None:
    d = pd.read_parquet(GIRDI)
    S = [c[3:] for c in d.columns if c.startswith("A::")]

    satirlar = []
    for s in S:
        a = d[f"A::{s}"].values
        b = d[f"B::{s}"].values
        c = d[f"C::{s}"].values
        pb, rb, fb = prf(a, b)
        pc, rc, fc = prf(a, c)
        tp, fp, fn, tn = _sayimlar(a, c)
        satirlar.append({
            "Sinif": s,
            "A resmi +": int(a.sum()),
            "B kalibrasyon +": int(b.sum()),
            "B P": pb, "B R": rb, "B F1": fb,
            "C BTB3D +": int(c.sum()),
            "C P": pc, "C R": rc, "C F1": fc,
            "C TP": tp, "C FP": fp, "C FN": fn, "C TN": tn,
            "sans F1": sans_f1(a, c),
            "C F1 - sans": fc - sans_f1(a, c),
            "C MCC": mcc(a, c),
            "kalibre": bool(fb >= KALIBRASYON_ESIGI),
        })
    t = pd.DataFrame(satirlar)

    kal = [r["Sinif"] for r in satirlar if r["kalibre"]]
    ozet_satirlari = []
    for ad, siniflar in (("18 sinif (tumu)", S),
                         (f"kalibre altkume (B F1>={KALIBRASYON_ESIGI})", kal)):
        alt = t[t.Sinif.isin(siniflar)]
        alt_b, ust_b = bootstrap_makro(d, siniflar, "B")
        alt_c, ust_c = bootstrap_makro(d, siniflar, "C")
        ozet_satirlari.append({
            "Kume": ad, "Sinif sayisi": len(siniflar),
            "B makro-F1 (tavan)": alt["B F1"].mean(),
            "B %95 GA": f"[{alt_b:.3f}-{ust_b:.3f}]",
            "C makro-F1 (BTB3D)": alt["C F1"].mean(),
            "C %95 GA": f"[{alt_c:.3f}-{ust_c:.3f}]",
            "sans makro-F1": alt["sans F1"].mean(),
            "C - sans": alt["C F1"].mean() - alt["sans F1"].mean(),
            "ortalama MCC": alt["C MCC"].mean(),
        })
    ozet = pd.DataFrame(ozet_satirlari)

    with pd.ExcelWriter(KARANTINA / "btb3d_ctrate500_metrik.xlsx",
                        engine="openpyxl") as w:
        ozet.to_excel(w, sheet_name="Ozet", index=False)
        t.to_excel(w, sheet_name="Sinif bazinda", index=False)

    (KARANTINA / "ctrate500_metrik.json").write_text(
        json.dumps({"ozet": ozet_satirlari, "sinif": satirlar,
                    "bootstrap_tekrar": TEKRAR, "tohum": TOHUM},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    pd.set_option("display.width", 200)
    print(ozet.to_string(index=False))
    print()
    print(t[["Sinif", "A resmi +", "B F1", "C BTB3D +", "C P", "C R", "C F1",
             "sans F1", "C MCC"]].to_string(index=False))
    print(f"\nyazildi: {KARANTINA / 'btb3d_ctrate500_metrik.xlsx'}")


if __name__ == "__main__":
    main()
