"""TASK-16 adim 7 - CODEX icin KOR yargilama paketi.

Plan: docs/29 §8.5 adim 7 · Kilit: configs/sema_takim_kilidi.json (takim-1.1)

NEYI SINAR: kilitli HEDEFLERI - motoru degil. Adim 6 gosterdi ki hedefleri
atayan taraf ile kurallari yazan taraf ayni (D75'in ortaya cikardigi sorun);
bu paket o hedeflere gercek bir DIS kontrol getirir.

KORLUK: pakete YALNIZ vaka kimligi ve cumle girer. Hedef sinif, dayanak
etiketi (A#/C#), motor ciktisi ve gerekce GIRMEZ. Sizinti olursa sinav
degersizdir - bu yuzden betik cikti kolonlarini acikca beyaz listeler.

Kullanim:
    python scripts/50_task16_adim7_kor_paket.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
SINIR = KOK / "data/processed/sema_sinir_vakalari.csv"
KILIT = KOK / "configs/sema_takim_kilidi.json"
CIKTI_DIZIN = KOK / "outputs/task16/adim7_codex"

# Kor pakete girebilecek TEK kolonlar. Beyaz liste - kara liste degil.
IZINLI_KOLONLAR = ["vaka_id", "cumle"]


def main() -> int:
    for y in (SINIR, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    d = pd.read_csv(SINIR, keep_default_na=False)
    sizinti = [k for k in d.columns if k not in IZINLI_KOLONLAR]
    kor = d[IZINLI_KOLONLAR].copy()

    CIKTI_DIZIN.mkdir(parents=True, exist_ok=True)
    kor_csv = CIKTI_DIZIN / "KOR_sinir_vakalari.csv"
    kor.to_csv(kor_csv, index=False, encoding="utf-8")

    ham = kor_csv.read_bytes()
    sha = hashlib.sha256(ham).hexdigest()

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    manifest = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kaynak_kilit_surumu": kilit.get("surum", "?"),
        "vaka_sayisi": int(len(kor)),
        "izinli_kolonlar": IZINLI_KOLONLAR,
        "paketten_CIKARILAN_kolonlar": sizinti,
        "kor_paket_sha256": sha,
        "kural": "Yargilama tamamlanip kilitlenmeden `sema_sinir_vakalari.csv` "
                 "ve `outputs/task16/INCELEME_v1.1.md` ACILMAZ.",
    }
    (CIKTI_DIZIN / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"vaka          : {len(kor)}")
    print(f"paketten cikan: {sizinti}")
    print(f"sha256        : {sha}")
    print(f"YAZILDI       : {kor_csv.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
