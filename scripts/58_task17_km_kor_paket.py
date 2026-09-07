"""TASK-17 - `known_malignancy` KOR DOGRULAMA PAKETI uretir.

Protokol: docs/37_task17_known_malignancy_kor_dogrulama.md (SONUC GORULMEDEN
yazildi) · Denetim maddesi: D94/4 · Karar kaydi: D95

Paket YALNIZ `vaka_id` + `cumle` icerir. Kavram, duzey, kural adi, `study_id`
CIKARILIR - yargic semayi, kurali ve kavram listesini GORMEZ.

⚠ OLCULEN: cumle gercekten YAZILI/BELGELENMIS kanser oykusu bildiriyor mu?
⚠ OLCULMEYEN: hastanin gercekten kanseri olup olmadigi (D71 - ground truth yok).

Kullanim:
    .venv/Scripts/python.exe scripts/58_task17_km_kor_paket.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
from radyovlm.evaluation import sema  # noqa: E402

P = KOK / "data/processed"
KILIT = KOK / "configs/splits_holdout.json"
SURUM = "v2"      # D97: `due to` dali daraltildi -> YENI kural surumu
CIKTI_DIZIN = KOK / f"outputs/task17/km_kor_{SURUM}"
ANAHTAR = KOK / f"configs/task17_km_kor_anahtar_{SURUM}.json"

ORNEKLEM = 40          # protokolde ONCEDEN ilan edildi
TOHUM = 20260908       # ⚠ v2 icin YENI tohum - eski orneklem TEKRAR
                       # KULLANILMAZ. Protokol: yeni kural surumu YENI
                       # kor orneklem ister; eskisini yeniden puanlayip
                       # gecerli saymak YASAK (D97, denetim onerisi 6).


def main() -> int:
    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(P / "reports_study_level.parquet", columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    v = pd.read_parquet(P / "entities.parquet", columns=[
        "entity_id", "study_id", "section", "sent_idx", "normalized_concept",
        "assertion", "raw_text"])
    v = v[v["study_id"].isin(gelistirme)]
    c = pd.read_parquet(P / "sentences.parquet",
                        columns=["study_id", "section", "sent_idx", "text"])
    v = v.merge(c, on=["study_id", "section", "sent_idx"], how="left")
    v["cumle_metni"] = v["text"].fillna("")

    # Kuralin TETIKLENDIGI varliklar
    mal = v[v["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)].copy()
    mal["tetikledi"] = mal.apply(sema._bilinen_kanser, axis=1)
    tetik = mal[mal["tetikledi"]]
    print(f"kapsam: gelistirme havuzu · kural {tetik['study_id'].nunique():,} "
          f"calismada tetikledi ({len(tetik):,} varlik)")

    # Calisma basina TEK cumle (ilk tetikleyen) - ayni raporu iki kez sormayalim
    tek = tetik.drop_duplicates(subset=["study_id"])[["study_id", "cumle_metni"]]
    n = min(ORNEKLEM, len(tek))
    ornek = tek.sample(n, random_state=TOHUM).reset_index(drop=True)
    print(f"orneklem: {n} vaka (tohum {TOHUM}, protokolde ONCEDEN ilan edildi)\n")

    ornek["vaka_id"] = [f"KM-{i+1:02d}" for i in range(len(ornek))]

    CIKTI_DIZIN.mkdir(parents=True, exist_ok=True)
    kor = ornek[["vaka_id", "cumle_metni"]].rename(columns={"cumle_metni": "cumle"})
    kor["yargi_E_H_SORU"] = ""
    kor["gerekce"] = ""
    kor_yol = CIKTI_DIZIN / f"KOR_known_malignancy_{SURUM}.csv"
    kor.to_csv(kor_yol, index=False, encoding="utf-8")
    sha = hashlib.sha256(kor_yol.read_bytes()).hexdigest()

    # ANAHTAR - yargicin GORMEYECEGI esleme
    ANAHTAR.write_text(json.dumps({
        "surum": f"km-kor-2.0-{SURUM}",
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "protokol": "docs/37_task17_known_malignancy_kor_dogrulama.md",
        "orneklem": n, "tohum": TOHUM,
        "populasyon_calisma": int(tetik["study_id"].nunique()),
        "kor_paket_sha256": sha,
        "kabul_olcutu": {"kesinlik_esigi_yuzde": 85,
                         "tanim": "E / (E + H); `?` paydadan cikarilir ve ayrica raporlanir"},
        "esleme": {r["vaka_id"]: r["study_id"] for _, r in ornek.iterrows()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"KOR PAKET : {kor_yol.relative_to(KOK)}")
    print(f"  SHA-256 : {sha}")
    print(f"ANAHTAR   : {ANAHTAR.relative_to(KOK)}  (yargica VERILMEZ)")
    print(f"\nPakette YALNIZ: {list(kor.columns)}")
    print("  -> kavram, duzey, kural adi, study_id CIKARILDI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
