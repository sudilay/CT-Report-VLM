"""BTB3D degerlendirmesi · kor ikinci degerlendirici uyumu.

Korlugu ACAR ve uc degerlendiriciyi karsilastirir:

    BEN      elle okuma          (`el_yargisi.csv`, 30 vaka)
    CODEX    kor ikinci gorus    (`KOR_paket_codex.csv`, 40 vaka)
    CIKARICI otomatik hat        (`ctrate500_18sinif.parquet`, B/C kolonlari)

Uc olcum:
  1. Degerlendiriciler arasi uyum (kappa) - cikarici insan yargisiyla ortusuyor mu
  2. CODEX'in etiketleriyle BTB3D performansi - bagimsiz ucuncu tahmin
  3. Korluk denetimi - Codex hekim/model metinlerini ayirt edebilmis mi

⛔ DUVAR: girdi CT-RATE valid muhurlu havuzudur; ciktilar karantinaya yazilir.

Kullanim:
    python scripts/78_btb3d_kor_uyum.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
KARANTINA = KOK / "outputs/btb3d_ctrate_muhurlu"

KIS = ["MM", "AWC", "CM", "PCE", "CAWC", "HH", "LAP", "EMP", "ATL",
       "LN", "LO", "PFS", "PLE", "MAP", "PBT", "CONS", "BRE", "IST"]
TAM = ["Medical material", "Arterial wall calcification", "Cardiomegaly",
       "Pericardial effusion", "Coronary artery wall calcification",
       "Hiatal hernia", "Lymphadenopathy", "Emphysema", "Atelectasis",
       "Lung nodule", "Lung opacity", "Pulmonary fibrotic sequela",
       "Pleural effusion", "Mosaic attenuation pattern",
       "Peribronchial thickening", "Consolidation", "Bronchiectasis",
       "Interlobular septal thickening"]


def kappa(x: np.ndarray, y: np.ndarray) -> tuple[float, float, int, int, int]:
    """Cohen kappa + gozlenen uyum + TP/FP/FN (x referans kabul edilir)."""
    tp = int(((x == 1) & (y == 1)).sum())
    fp = int(((x == 0) & (y == 1)).sum())
    fn = int(((x == 1) & (y == 0)).sum())
    tn = int(((x == 0) & (y == 0)).sum())
    n = tp + fp + fn + tn
    po = (tp + tn) / n
    pe = ((tp + fn) * (tp + fp) + (fn + tn) * (fp + tn)) / n ** 2
    return ((po - pe) / (1 - pe) if pe < 1 else 0.0), po, tp, fp, fn


def f1(x: np.ndarray, y: np.ndarray) -> float:
    tp = int(((x == 1) & (y == 1)).sum())
    fp = int(((x == 0) & (y == 1)).sum())
    fn = int(((x == 1) & (y == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def sans_f1(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    a, c = int(x.sum()), int(y.sum())
    return 2 * a * c / (n * (a + c)) if (a + c) else 0.0


def main() -> None:
    cod = pd.read_csv(KARANTINA / "KOR_paket_codex.csv")
    anh = pd.read_csv(KARANTINA / ".KOR_anahtar.csv")
    el = pd.read_csv(KARANTINA / "el_yargisi.csv")
    cik = pd.read_parquet(KARANTINA / "ctrate500_18sinif.parquet").set_index(
        "VolumeName")

    # --- korlugu ac -------------------------------------------------------
    d = cod[["vaka_id", "metin_no"] + KIS + ["malignite"]].merge(
        anh[["vaka_id", "metin_no", "gercek_kaynak", "VolumeName"]],
        on=["vaka_id", "metin_no"], how="left", validate="one_to_one")
    if d.gercek_kaynak.isna().any():
        raise ValueError("anahtar eslesmesi eksik")

    # cikaricinin ayni satir icin etiketi: HEKIM -> B, BTB3D -> C
    for k, t in zip(KIS, TAM):
        d[f"cik_{k}"] = [
            int(cik.loc[v, f"{'B' if s == 'HEKIM' else 'C'}::{t}"])
            for v, s in zip(d.VolumeName, d.gercek_kaynak)]

    # benim etiketim (yalniz 30 rastgele vaka)
    elm = el.copy()
    elm["gercek_kaynak"] = np.where(elm.kaynak == "GT", "HEKIM", "BTB3D")
    d = d.merge(elm[["rapor", "gercek_kaynak"] + KIS].rename(
        columns={"rapor": "vaka_id", **{k: f"ben_{k}" for k in KIS}}),
        on=["vaka_id", "gercek_kaynak"], how="left")

    d.to_csv(KARANTINA / "kor_acilmis_birlesik.csv", index=False)

    def yigin(df: pd.DataFrame, on1: str, on2: str) -> tuple[np.ndarray, np.ndarray]:
        a = df[[f"{on1}{k}" if on1 else k for k in KIS]].values.ravel()
        b = df[[f"{on2}{k}" if on2 else k for k in KIS]].values.ravel()
        return a.astype(int), b.astype(int)

    print("=" * 74)
    print("1. DEGERLENDIRICILER ARASI UYUM")
    print("=" * 74)
    var = d[d[[f"ben_{k}" for k in KIS]].notna().all(axis=1)]
    ciftler = [
        ("BEN", "", "CODEX", "", var, "ben_"),
        ("BEN", "ben_", "CIKARICI", "cik_", var, None),
        ("CODEX", "", "CIKARICI", "cik_", d, None),
    ]
    sonuc = {}
    for ad1, p1, ad2, p2, df, ozel in ciftler:
        if ozel is not None:          # BEN vs CODEX: ben_ referans, ham Codex
            x = df[[f"ben_{k}" for k in KIS]].values.ravel().astype(int)
            y = df[KIS].values.ravel().astype(int)
        else:
            x, y = yigin(df, p1, p2)
        k, po, tp, fp, fn = kappa(x, y)
        sonuc[f"{ad1} vs {ad2}"] = {"kappa": k, "uyum": po, "n": len(x),
                                    "TP": tp, "FP": fp, "FN": fn}
        print(f"  {ad1:9s} ↔ {ad2:9s}  n={len(x):5d}  uyum %{100*po:5.1f}  "
              f"kappa {k:+.3f}   (TP{tp} FP{fp} FN{fn})")

    print("\n  Kaynaga gore ayristirilmis (CODEX ↔ CIKARICI):")
    for kay in ("HEKIM", "BTB3D"):
        alt = d[d.gercek_kaynak == kay]
        x, y = yigin(alt, "", "cik_")
        k, po, *_ = kappa(y, x)
        print(f"    {kay:6s} metinlerinde  n={len(x):4d}  uyum %{100*po:5.1f}  "
              f"kappa {k:+.3f}")

    print("\n" + "=" * 74)
    print("2. CODEX'IN ETIKETLERIYLE BTB3D PERFORMANSI (40 vaka, bagimsiz)")
    print("=" * 74)
    hek = d[d.gercek_kaynak == "HEKIM"].set_index("vaka_id")
    btb = d[d.gercek_kaynak == "BTB3D"].set_index("vaka_id")
    ort = sorted(set(hek.index) & set(btb.index))
    H = hek.loc[ort, KIS].values.astype(int)
    B = btb.loc[ort, KIS].values.astype(int)

    tp = int(((H == 1) & (B == 1)).sum()); fp = int(((H == 0) & (B == 1)).sum())
    fn = int(((H == 1) & (B == 0)).sum()); tn = int(((H == 0) & (B == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    mikro = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    makro = float(np.mean([f1(H[:, j], B[:, j]) for j in range(len(KIS))]))
    sans = float(np.mean([sans_f1(H[:, j], B[:, j]) for j in range(len(KIS))]))
    print(f"  TP {tp}  FP {fp}  FN {fn}  TN {tn}")
    print(f"  duyarlilik {rc:.3f} | kesinlik {pr:.3f} | mikro-F1 {mikro:.3f} | "
          f"makro-F1 {makro:.3f} (sans {sans:.3f}, fark {makro-sans:+.3f})")
    hic = sum(1 for i in range(len(ort))
              if H[i].sum() > 0 and (H[i] & B[i]).sum() == 0)
    tam = sum(1 for i in range(len(ort)) if (H[i] == B[i]).all())
    print(f"  hekimin hicbir bulgusunu yakalamamis: {hic}/{len(ort)} vaka")
    print(f"  18/18 tam isabet: {tam}/{len(ort)} vaka")

    print("\n" + "=" * 74)
    print("3. KORLUK DENETIMI")
    print("=" * 74)
    m1 = d[d.metin_no == "Metin-1"]
    dogru = int((m1.gercek_kaynak == "HEKIM").sum())
    print(f"  Metin-1 gercekte hekim olan vaka: {dogru}/{len(m1)} "
          f"(%{100*dogru/len(m1):.0f}) - paket dengeli")
    print("  Codex'in bildirdigi bulgu sayisi (kaynagi bilmeden):")
    for kay in ("HEKIM", "BTB3D"):
        alt = d[d.gercek_kaynak == kay]
        print(f"    {kay:6s}: vaka basina ort. {alt[KIS].sum(axis=1).mean():.2f} "
              f"bulgu | malignite dagilimi {dict(alt.malignite.value_counts())}")

    (KARANTINA / "kor_uyum.json").write_text(json.dumps({
        "degerlendirici_uyumu": sonuc,
        "codex_ile_btb3d": {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
                            "duyarlilik": rc, "kesinlik": pr,
                            "mikro_f1": mikro, "makro_f1": makro,
                            "sans_makro_f1": sans, "vaka": len(ort),
                            "hicbirini_yakalamamis": hic, "tam_isabet": tam},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nyazildi: {KARANTINA / 'kor_uyum.json'}")


if __name__ == "__main__":
    main()
