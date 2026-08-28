# -*- coding: utf-8 -*-
"""TASK-13 / C2-pilot: Kucuk pilot isaretleme paketi.

NEDEN PILOT: Tam ayar kumesi 150 cumle + 625 aday = ~4-6 saat. Once 30 cumlelik
bir pilot uc soruyu cevaplar:
  (a) kilavuz uygulanabilir mi
  (b) isaretleyici yapabiliyor mu
  (c) sistemde felaket bir sorun var mi (kesinlik %60 gibi)
Sonucuna gore tam kumeye devam edilir veya once kilavuz duzeltilir.

Katmanli secim: her zor vaka grubundan esit sayida - rastgele ornek pilotu
kolay vakalarla doldurur ve zor kismi hic sinamaz.

Kullanim: .venv/Scripts/python.exe scripts/15_build_pilot.py [--n 30]
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
TOHUM = 20260827


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="pilot cumle sayisi")
    a = ap.parse_args()

    A = pd.read_csv(PROC / "task13_A_kor_listeleme_ayar.csv", encoding="utf-8-sig")
    B = pd.read_csv(PROC / "task13_B_yargilama_ayar.csv", encoding="utf-8-sig")

    # katmanli secim - her gruptan esit pay
    gruplar = sorted(A.grup.unique())
    pay = max(1, a.n // len(gruplar))
    parcalar = [g.sample(min(pay, len(g)), random_state=TOHUM)
                for _, g in A.groupby("grup")]
    pilot = pd.concat(parcalar)
    if len(pilot) < a.n:                      # kalani rastgele tamamla
        kalan = A[~A.index.isin(pilot.index)]
        pilot = pd.concat([pilot, kalan.sample(min(a.n - len(pilot), len(kalan)),
                                               random_state=TOHUM)])
    pilot = pilot.sample(frac=1, random_state=TOHUM).reset_index(drop=True)

    anahtar = ["study_id", "section", "sent_idx"]
    secilen = set(map(tuple, pilot[anahtar].values))
    b_pilot = B[[tuple(x) in secilen for x in B[anahtar].values]] \
        .sample(frac=1, random_state=TOHUM).reset_index(drop=True)

    yol_a = PROC / "PILOT_A_kor_listeleme.csv"
    yol_b = PROC / "PILOT_B_yargilama.csv"
    pilot.to_csv(yol_a, index=False, encoding="utf-8-sig")
    b_pilot.to_csv(yol_b, index=False, encoding="utf-8-sig")

    print(f"PILOT paketi hazir\n")
    print(f"  A · kor listeleme : {yol_a.name}   {len(pilot):>3} cumle")
    print(f"  B · yargilama     : {yol_b.name}   {len(b_pilot):>3} aday")
    print(f"\n  grup dagilimi: {pilot.grup.value_counts().to_dict()}")
    print(f"  tahmini sure : A ~{len(pilot)*0.75:.0f} dk · B ~{len(b_pilot)*0.3:.0f} dk")

    # pilotta gecen kavramlar - rehberdeki sozluk bunlardan yazilir
    kav = sorted(b_pilot.aday_kavram.unique())
    print(f"\n  pilotta gecen {len(kav)} kavram:")
    for i in range(0, len(kav), 6):
        print("    " + " · ".join(kav[i:i + 6]))


if __name__ == "__main__":
    main()
