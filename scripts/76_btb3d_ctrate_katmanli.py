"""BTB3D degerlendirmesi · CT-RATE 500 · katmanli cozumleme.

Betik 75 tek bir makro-F1 uretir. Bu betik o sayinin NEREDEN geldigini ayirir:

  (b) KESIKLIK    512 token kapaginda cumle ortasinda kesilen raporlar,
                  modelin goremedigi icin degil URETEMEDIGI icin bulgu
                  kaybediyor olabilir. Kesik / tam ayri olculur.
  (c) SABLON      Ayni metin birden fazla vakaya yazilmissa o vaka icin
                  rapor vaka-ozgu bilgi tasiyamaz. Benzersiz / tekrar ayrilir.
  (d) ZORLUK      Hekimin tarif ettigi bulgu sayisina gore katman. Hipotez:
                  normal vakalarda sablon dogru cikiyor, patolojik vakalarda
                  cokuyor. Dogrulanirsa "yuksek dogruluk" iddiasinin kaynagi
                  normal vakalardir.
  (e) OLCU        Iki taraf da olcu verdiginde sayilar birbirini tutuyor mu.

⛔ DUVAR: girdi CT-RATE valid muhurlu havuzudur; ciktilar karantinaya yazilir.

Kullanim:
    python scripts/76_btb3d_ctrate_katmanli.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
KARANTINA = KOK / "outputs/btb3d_ctrate_muhurlu"
ETIKET = KARANTINA / "ctrate500_18sinif.parquet"
HAM = KOK / "data/raw/btb3d-ctrate-500-reports/generated_reports_500.csv"

OLCU = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mm|cm)\b", re.I)


def prf(y: np.ndarray, p: np.ndarray) -> tuple[float, float, float]:
    tp = int(((y == 1) & (p == 1)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return pr, rc, (2 * pr * rc / (pr + rc) if pr + rc else 0.0)


def sans_f1(y: np.ndarray, p: np.ndarray) -> float:
    n = len(y)
    a, c = int(y.sum()), int(p.sum())
    return 2 * a * c / (n * (a + c)) if (a + c) else 0.0


def makro(d: pd.DataFrame, S: list[str]) -> tuple[float, float, int]:
    """(makro-F1, sans makro-F1, n). Hicbir tarafta gecmeyen sinif ATLANIR."""
    f, s = [], []
    for x in S:
        y = d[f"A::{x}"].values
        p = d[f"C::{x}"].values
        if y.sum() == 0 and p.sum() == 0:
            continue
        f.append(prf(y, p)[2])
        s.append(sans_f1(y, p))
    return float(np.mean(f)), float(np.mean(s)), len(d)


def katman_tablosu(d: pd.DataFrame, S: list[str], kolon: str,
                   baslik: str) -> pd.DataFrame:
    satir = []
    for ad, alt in d.groupby(kolon, sort=True):
        f, s, n = makro(alt, S)
        satir.append({"Katman": f"{baslik}: {ad}", "n": n,
                      "makro-F1": f, "sans": s, "fark": f - s})
    f, s, n = makro(d, S)
    satir.append({"Katman": "TUMU", "n": n, "makro-F1": f, "sans": s,
                  "fark": f - s})
    return pd.DataFrame(satir)


def main() -> None:
    d = pd.read_parquet(ETIKET)
    ham = pd.read_csv(HAM)[["VolumeName", "Generated_Report",
                            "Ground_Truth_Findings",
                            "Ground_Truth_Impressions"]]
    d = d.merge(ham, on="VolumeName")
    S = [c[3:] for c in d.columns if c.startswith("A::")]

    g = d.Generated_Report.fillna("").str.strip()
    d["kesik"] = np.where(~g.str.endswith((".", "!", "?")), "kesik", "tam")
    vc = g.value_counts()
    d["sablon"] = np.where(g.map(vc) > 1, "tekrar eden", "benzersiz")
    n_poz = d[[f"A::{x}" for x in S]].sum(axis=1)
    d["zorluk"] = pd.cut(n_poz, [-1, 0, 2, 100],
                         labels=["0 bulgu", "1-2 bulgu", "3+ bulgu"])

    tablolar = {
        "b_kesiklik": katman_tablosu(d, S, "kesik", "(b) 512-token"),
        "c_sablon": katman_tablosu(d, S, "sablon", "(c) sablon"),
        "d_zorluk": katman_tablosu(d, S, "zorluk", "(d) hekimin bulgu sayisi"),
    }
    for ad, t in tablolar.items():
        print(f"\n### {ad}")
        print(t.to_string(index=False,
                          formatters={"makro-F1": "{:.3f}".format,
                                      "sans": "{:.3f}".format,
                                      "fark": "{:+.3f}".format}))

    # (e) olcu uyumu -------------------------------------------------------
    def mm(t: str) -> list[float]:
        out = []
        for s, b in OLCU.findall(str(t)):
            v = float(s.replace(",", "."))
            out.append(v * 10 if b.lower() == "cm" else v)
        return out

    gt_o = (d.Ground_Truth_Findings.fillna("") + " "
            + d.Ground_Truth_Impressions.fillna("")).map(mm)
    gen_o = d.Generated_Report.fillna("").map(mm)
    ikisi = [(a, b) for a, b in zip(gt_o, gen_o) if a and b]

    esik = 2.0   # mm - ayni bulgunun makul olcum toleransi
    eslesen = sum(1 for a, b in ikisi
                  if any(min(abs(x - y) for x in a) <= esik for y in b))
    print(f"\n### e_olcu  (iki taraf da olcu veren {len(ikisi)} vaka)")
    print(f"  BTB3D'nin verdigi en az bir olcu, hekimin bir olcusune "
          f"{esik:.0f} mm icinde: {eslesen} vaka (%{100*eslesen/len(ikisi):.1f})")
    ort_gt = np.mean([np.mean(a) for a, _ in ikisi])
    ort_ge = np.mean([np.mean(b) for _, b in ikisi])
    print(f"  ortalama olcu  hekim {ort_gt:.1f} mm | BTB3D {ort_ge:.1f} mm")
    r = np.corrcoef([np.max(a) for a, _ in ikisi],
                    [np.max(b) for _, b in ikisi])[0, 1]
    print(f"  en buyuk olcu korelasyonu (Pearson r): {r:+.3f}")

    with pd.ExcelWriter(KARANTINA / "btb3d_ctrate500_katmanli.xlsx",
                        engine="openpyxl") as w:
        for ad, t in tablolar.items():
            t.to_excel(w, sheet_name=ad, index=False)

    (KARANTINA / "ctrate500_katmanli.json").write_text(json.dumps({
        "katmanlar": {k: v.to_dict("records") for k, v in tablolar.items()},
        "olcu": {"iki_tarafli_vaka": len(ikisi), "eslesen": eslesen,
                 "esik_mm": esik, "pearson_en_buyuk": float(r),
                 "ort_hekim_mm": float(ort_gt), "ort_btb3d_mm": float(ort_ge)},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nyazildi: {KARANTINA / 'btb3d_ctrate500_katmanli.xlsx'}")


if __name__ == "__main__":
    main()
