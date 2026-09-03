"""TASK-16 Adim 0 - HASTA DUZEYINDE BOLUNME KILIDI.

Plan: docs/29_task16_calisma_plani.md §4.3

Neden simdi: sema ve sozlukler korpusa BAKARAK yazilacak. Bolunme sonra
dondurulursa sema butun korpusu gormus olur ve Faz 5'te olculen dogruluk
sisik cikar. TASK-14'un kendi kurali: "Bolunme sozluk kurulmadan ONCE
yapilmali; sonra yapmak ise yaramaz." (reports/turkce_bolunme_dondurma.md)

Kilit iki parcadir:
  (a) CT-RATE'in KENDI resmi `valid` bolunmesi - dokunulmaz, karsilastirilabilirlik
      icin (AGENTS.md kurali)
  (b) `train`den hasta duzeyinde %15, sabit tohum, TEK SEFER

Gelistirme havuzu = train eksi (b).

BU BETIK GERI DONUSSUZDUR: mevcut kilit dosyasinin uzerine YAZMAZ. Yeniden
uretmek gerekirse dosya elle silinmeli ve bu bilincli bir karar olarak
kaydedilmelidir.

Kullanim:
    python scripts/40_task16_bolunme_kilidi.py
    python scripts/40_task16_bolunme_kilidi.py --dogrula   # kilidi yeniden uret ve karsilastir
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"

TOHUM = 20260903          # docs/29 §4.3'te ilan edildi
TRAIN_KILIT_ORANI = 0.15  # docs/29 §4.3'te ilan edildi
SURUM = "holdout-1.0"


def sha(metinler: list[str]) -> str:
    """Sirali kimlik listesinin kararli saglama toplami."""
    h = hashlib.sha256()
    for m in sorted(metinler):
        h.update(m.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def kilidi_uret(d: pd.DataFrame) -> dict:
    """Deterministik: ayni korpus + ayni tohum -> ayni kilit."""
    valid_hastalar = sorted(d.loc[d["split"] == "valid", "patient_id"].unique())
    train_hastalar = sorted(d.loc[d["split"] == "train", "patient_id"].unique())

    k = round(len(train_hastalar) * TRAIN_KILIT_ORANI)
    # random.Random(tohum).sample CPython'da kararlidir; girdi SIRALI verilir
    train_kilit = sorted(random.Random(TOHUM).sample(train_hastalar, k))
    train_kilit_kumesi = set(train_kilit)
    gelistirme = [p for p in train_hastalar if p not in train_kilit_kumesi]

    def sayim(hastalar: list[str]) -> int:
        return int(d["patient_id"].isin(set(hastalar)).sum())

    return {
        "surum": SURUM,
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "tohum": TOHUM,
        "train_kilit_orani": TRAIN_KILIT_ORANI,
        "kaynak": {
            "dosya": "data/processed/reports_study_level.parquet",
            "calisma": int(len(d)),
            "hasta": int(d["patient_id"].nunique()),
        },
        "degerlendirme_kilidi": {
            "aciklama": "TASK-16/17/18 bu havuza DOKUNMAZ. Test kumesi nihai boyutu "
                        "TASK-18'in prevalans olcumunden sonra BU havuzun ICINDEN secilir; "
                        "havuz sonradan GENISLETILMEZ.",
            "a_ctrate_valid": {
                "hasta": len(valid_hastalar),
                "calisma": sayim(valid_hastalar),
                "sha256": sha(valid_hastalar),
                "hasta_listesi": valid_hastalar,
            },
            "b_train_kilit": {
                "hasta": len(train_kilit),
                "calisma": sayim(train_kilit),
                "sha256": sha(train_kilit),
                "hasta_listesi": train_kilit,
            },
        },
        "gelistirme_havuzu": {
            "aciklama": "Sema, sozluk, sinir vakasi ve kontrol takimi YALNIZ buradan cikarilir.",
            "hasta": len(gelistirme),
            "calisma": sayim(gelistirme),
            "sha256": sha(gelistirme),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dogrula", action="store_true",
                    help="Kilidi yeniden uretip mevcut dosyayla karsilastirir, yazmaz.")
    a = ap.parse_args()

    if not KORPUS.exists():
        print(f"HATA: korpus yok: {KORPUS}")
        return 1

    d = pd.read_parquet(KORPUS, columns=["patient_id", "study_id", "split"])
    yeni = kilidi_uret(d)

    if a.dogrula:
        if not KILIT.exists():
            print(f"HATA: dogrulanacak kilit yok: {KILIT}")
            return 1
        eski = json.loads(KILIT.read_text(encoding="utf-8"))
        alanlar = [
            ("degerlendirme_kilidi", "a_ctrate_valid", "sha256"),
            ("degerlendirme_kilidi", "b_train_kilit", "sha256"),
            ("gelistirme_havuzu", "sha256"),
        ]
        tamam = True
        for yol in alanlar:
            e, y = eski, yeni
            for k in yol:
                e, y = e[k], y[k]
            isaret = "OK " if e == y else "FARK"
            if e != y:
                tamam = False
            print(f"  [{isaret}] {'.'.join(yol)}: {e[:16]}")
        print("\nKILIT YENIDEN URETILEBILIR" if tamam else "\n!!! KILIT YENIDEN URETILEMIYOR !!!")
        return 0 if tamam else 1

    if KILIT.exists():
        print(f"HATA: kilit ZATEN VAR ve uzerine yazilmaz: {KILIT}")
        print("      Bu bilincli bir tasarimdir (docs/29 §4.3 - geri donussuz).")
        print("      Yeniden uretmek icin dosyayi ELLE silin ve kararinizi kaydedin.")
        print("      Dogrulama icin: --dogrula")
        return 1

    KILIT.parent.mkdir(parents=True, exist_ok=True)
    KILIT.write_text(json.dumps(yeni, ensure_ascii=False, indent=2), encoding="utf-8")

    dk = yeni["degerlendirme_kilidi"]
    gh = yeni["gelistirme_havuzu"]
    print(f"YAZILDI: {KILIT.relative_to(KOK)}  (surum {SURUM}, tohum {TOHUM})\n")
    print(f"  DEGERLENDIRME KILIDI (dokunulmaz)")
    print(f"    (a) CT-RATE valid : {dk['a_ctrate_valid']['hasta']:>6} hasta "
          f"/ {dk['a_ctrate_valid']['calisma']:>6} calisma  {dk['a_ctrate_valid']['sha256'][:16]}")
    print(f"    (b) train %15     : {dk['b_train_kilit']['hasta']:>6} hasta "
          f"/ {dk['b_train_kilit']['calisma']:>6} calisma  {dk['b_train_kilit']['sha256'][:16]}")
    print(f"  GELISTIRME HAVUZU   : {gh['hasta']:>6} hasta "
          f"/ {gh['calisma']:>6} calisma  {gh['sha256'][:16]}")
    print(f"\n  dosya sha256: {hashlib.sha256(KILIT.read_bytes()).hexdigest()[:32]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
