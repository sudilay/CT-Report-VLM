"""NLST kohortu · uc sistemin karsilastirmali degerlendirmesi.

Uc eksen:

  A. SISTEMLER ARASI TUTARLILIK
     Insan yazimi referans olmadigi icin bu "dogruluk" degildir. Ayni
     goruntuye bakan uc sistem ayni bulguyu bildiriyor mu sorusudur.
     Sans duzeyinde ayrisiyorlarsa en az ikisi guvenilmezdir.

  B. KANSER SONUCUNA KARSI
     Tek dis gercek. Tahmin edilen buyukluk: "tumoru gordu mu" DEGIL,
     "sonradan kanser tanisi alan hastanin raporunda supheli bir bulgu
     bildirilmis mi". NLST bir TARAMA kohortudur; pozitiflerin cogunda o
     taramada gorunur hastalik yoktur. Bu yuzden tani ile tarama arasindaki
     sureye gore katmanlama ZORUNLUDUR.

  C. VAKA OZGULLUGU
     Referans gerektirmez, CT-RATE olcumleriyle DOGRUDAN karsilastirilabilir.

Kullanim:
    python scripts/80_nlst_uclu_metrik.py
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
DIZIN = KOK / "outputs/btb3d_nlst"
GIRDI = DIZIN / "nlst_uclu_bulgular.parquet"

SISTEMLER = ["BTB3D", "ASTRA", "MEDMO"]
PANEL = ["Malignite", "Supheli morfoloji", "Nodul", "Kitle"]
TEKRAR = 10_000
TOHUM = 20260910


def kappa(x: np.ndarray, y: np.ndarray) -> float:
    tp = int(((x == 1) & (y == 1)).sum()); fp = int(((x == 0) & (y == 1)).sum())
    fn = int(((x == 1) & (y == 0)).sum()); tn = int(((x == 0) & (y == 0)).sum())
    n = tp + fp + fn + tn
    if n == 0:
        return 0.0
    po = (tp + tn) / n
    pe = ((tp + fn) * (tp + fp) + (fn + tn) * (fp + tn)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 0.0


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    orta = (p + z * z / (2 * n)) / d
    yari = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, orta - yari), min(1.0, orta + yari))


def main() -> None:
    d = pd.read_parquet(GIRDI)
    siniflar = sorted({c.split("::", 1)[1] for c in d.columns if "::" in c})
    on_18 = [s for s in siniflar if s not in PANEL]

    ozet: dict = {"kapsam": {"seri": len(d), "pid": int(d.pid.nunique()),
                             "pozitif_seri": int(d.label.sum()),
                             "pozitif_pid": int(d.groupby("pid").label.max().sum())}}
    print("KAPSAM:", ozet["kapsam"])

    # ------------------------------------------------ A. sistemler arasi
    print("\n" + "=" * 72)
    print("A. SISTEMLER ARASI TUTARLILIK  (referans yok, 'dogruluk' degil)")
    print("=" * 72)
    satir = []
    for a, b in combinations(SISTEMLER, 2):
        x = d[[f"{a}::{s}" for s in on_18]].values.ravel()
        y = d[[f"{b}::{s}" for s in on_18]].values.ravel()
        k18 = kappa(x, y)
        xm = d[[f"{a}::{s}" for s in PANEL]].values.ravel()
        ym = d[[f"{b}::{s}" for s in PANEL]].values.ravel()
        satir.append({"cift": f"{a} - {b}", "18 sinif kappa": k18,
                      "malignite paneli kappa": kappa(xm, ym)})
        print(f"  {a:6s} - {b:6s}   18 sinif kappa {k18:+.3f}   "
              f"malignite paneli kappa {kappa(xm, ym):+.3f}")
    ozet["sistemler_arasi"] = satir

    print("\n  Malignite panelinde sinif bazinda ikili kappa:")
    print(f"  {'':20s} " + "  ".join(f"{a[:3]}-{b[:3]}"
                                     for a, b in combinations(SISTEMLER, 2)))
    for s in PANEL:
        hucre = "  ".join(f"{kappa(d[f'{a}::{s}'].values, d[f'{b}::{s}'].values):+7.3f}"
                          for a, b in combinations(SISTEMLER, 2))
        print(f"  {s:20s} {hucre}")

    print("\n  Bildirim oranlari (seri duzeyi):")
    for s in PANEL:
        print(f"  {s:20s} " + "  ".join(
            f"{x} %{100*d[f'{x}::{s}'].mean():5.1f}" for x in SISTEMLER))

    # ------------------------------------------------ B. kanser sonucu
    print("\n" + "=" * 72)
    print("B. KANSER SONUCUNA KARSI  (PID duzeyi, tek dis gercek)")
    print("=" * 72)
    pid = d.groupby("pid").agg(
        {**{f"{x}::{s}": "max" for x in SISTEMLER for s in PANEL},
         "label": "max", "followup_yil": "min"})
    print(f"  {len(pid)} PID · {int(pid.label.sum())} kanser pozitif")

    katmanlar = {
        "tani <= 1 yil": pid[(pid.label == 0) | (pid.followup_yil <= 1)],
        "tum pozitifler": pid,
    }
    bkayit = []
    for kad, alt in katmanlar.items():
        y = alt.label.values
        print(f"\n  --- {kad}  (n={len(alt)} PID, {int(y.sum())} pozitif) ---")
        print(f"  {'Sistem':7s} {'Gosterge':20s} {'Duyarlilik':>22s} {'Ozgulluk':>10s}")
        for s in ("Malignite", "Nodul", "Supheli morfoloji"):
            for x in SISTEMLER:
                p = alt[f"{x}::{s}"].values
                tp = int(((y == 1) & (p == 1)).sum()); fn = int(((y == 1) & (p == 0)).sum())
                tn = int(((y == 0) & (p == 0)).sum()); fp = int(((y == 0) & (p == 1)).sum())
                duy = tp / (tp + fn) if tp + fn else 0.0
                ozg = tn / (tn + fp) if tn + fp else 0.0
                lo, hi = wilson(tp, tp + fn)
                print(f"  {x:7s} {s:20s} {duy:6.3f} [{lo:.3f}-{hi:.3f}] "
                      f"({tp}/{tp+fn}) {ozg:10.3f}")
                bkayit.append({"katman": kad, "sistem": x, "gosterge": s,
                               "duyarlilik": duy, "ga_alt": lo, "ga_ust": hi,
                               "ozgulluk": ozg, "tp": tp, "poz": tp + fn})
    ozet["kanser_sonucu"] = bkayit

    # ------------------------------------------------ C. vaka ozgullugu
    print("\n" + "=" * 72)
    print("C. VAKA OZGULLUGU  (referanssiz; CT-RATE ile karsilastirilabilir)")
    print("=" * 72)
    ckayit = []
    for x in SISTEMLER:
        poz = d[d.label == 1]
        neg = d[d.label == 0]
        b_poz = poz[[f"{x}::{s}" for s in on_18]].sum(axis=1).mean()
        b_neg = neg[[f"{x}::{s}" for s in on_18]].sum(axis=1).mean()
        mal_poz = poz[f"{x}::Malignite"].mean()
        mal_neg = neg[f"{x}::Malignite"].mean()
        ckayit.append({"sistem": x, "bulgu_kanserli": b_poz,
                       "bulgu_kansersiz": b_neg, "fark": b_poz - b_neg,
                       "malignite_kanserli": mal_poz,
                       "malignite_kansersiz": mal_neg})
        print(f"  {x:6s}  vaka basina bulgu: kanserli {b_poz:.2f} · "
              f"kansersiz {b_neg:.2f} · fark {b_poz-b_neg:+.2f}")
        print(f"          malignite bildirimi: kanserli %{100*mal_poz:.1f} · "
              f"kansersiz %{100*mal_neg:.1f}")
    ozet["vaka_ozgullugu"] = ckayit

    DIZIN.mkdir(parents=True, exist_ok=True)
    (DIZIN / "nlst_uclu_metrik.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8")
    print(f"\nyazildi: {DIZIN / 'nlst_uclu_metrik.json'}")


if __name__ == "__main__":
    main()
