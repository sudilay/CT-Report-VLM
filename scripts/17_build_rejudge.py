# -*- coding: utf-8 -*-
"""TASK-13: Kilavuz bosluguyla etkilenen satirlari yeniden yargilamaya acar.

NEDEN:
  Iki bagimsiz isaretleyici kesinlikte 113 satirda ayristi, 99'u anatomi.
  Yon tek tarafli: biri 'mevcut', digeri 'yok'. Sebep, kilavuzda anatominin
  negasyondan korundugunu soyleyen kuralin (D28) HIC YAZILMAMIS olmasi.
  D28 bu isaretlemeden ONCE alinmisti; eksik olan yalnizca kilavuza gecirilmesi.

  Kural yazildi (docs/11, docs/12). Yalnizca ETKILENEN satirlar yeniden
  yargilanir - tum is tekrarlanmaz.

DURUSTLUK NOTU:
  Bu duzeltmenin yonu SISTEMI IYI GOSTERIR. O yuzden:
    - karar isaretleyiciye birakilir, kural yazari uygulamaz
    - eski cevap dosyada TUTULUR (_onceki_cevap), degisim izlenebilir
    - skor iki turlu raporlanir: duzeltmeli ve duzeltmesiz

Kullanim: .venv/Scripts/python.exe scripts/17_build_rejudge.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
K = ["study_id", "section", "sent_idx", "aday_metin", "aday_kavram"]

# Kapsam kurucu ifadeler: bu cumlelerdeki anatomi adaylari etkilenmis olabilir.
KAPSAM = re.compile(
    r"\bno\b|\bnot\b|absence|without|could not|cannot be|free of|negative for",
    re.I)

ISARETLEYICILER = ("codex", "gemini")


def main() -> None:
    anahtar = pd.read_csv(P / "task13_B_anahtar_ayar.csv",
                          encoding="utf-8-sig").drop_duplicates(K)

    for m in ISARETLEYICILER:
        yol = P / f"KALAN_B_{m}.csv"
        if not yol.exists():
            sys.exit(f"bulunamadi: {yol}")
        d = pd.read_csv(yol, encoding="utf-8-sig").merge(
            anahtar[K + ["_gizli_sahte"]], on=K, how="left")
        d["_sahte"] = d._gizli_sahte.fillna(0).astype(int)

        etkilenen = d[(d._sahte == 0)
                      & (d.aday_tip == "anatomy")
                      & d.cumle.astype(str).str.contains(KAPSAM)].copy()

        etkilenen["_onceki_cevap"] = etkilenen.kesinlik_ne_olmali
        etkilenen["kesinlik_ne_olmali"] = ""          # yeniden doldurulacak
        etkilenen = etkilenen.drop(columns=["_gizli_sahte", "_sahte"])

        cikti = P / f"YENIDEN_{m}.csv"
        etkilenen.to_csv(cikti, index=False, encoding="utf-8-sig")

        onc = etkilenen._onceki_cevap.astype(str).str.strip().str.lower()
        print(f"{m:<8} {len(etkilenen):>4} satir -> {cikti.name}")
        print(f"         onceki cevaplari: "
              + " · ".join(f"{k} {v}" for k, v in onc.value_counts().items()))

    print("\nDoldurulacak TEK kolon: kesinlik_ne_olmali  (mevcut/yok/belirsiz)")
    print("Kural: docs/12_pilot_rehberi.md -> 'anatomi olumsuzlanmaz'")
    print("_onceki_cevap kolonu BILGI icindir; degistirmek serbesttir,")
    print("ayni birakmak da serbesttir - kural neyi soyluyorsa o yazilir.")


if __name__ == "__main__":
    main()
