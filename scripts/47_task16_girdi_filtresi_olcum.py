"""TASK-16 Adim 5 - girdi kalite filtresinin gelistirme havuzunda olculmesi.

Plan: docs/29 §7 · Modul: src/radyovlm/evaluation/girdi_filtresi.py

Filtre varlik ELEMEZ, ETIKETLER: dusuk guvenli varliklar rapor sinifini
yukseltemez ama kayitta kalir. Bu betik etkinin buyuklugunu olcer ve yazar.

KAPSAM: yalniz gelistirme havuzu. Degerlendirme kilidi okunmaz.

Kullanim:
    python scripts/47_task16_girdi_filtresi_olcum.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import girdi_filtresi as gf  # noqa: E402

VARLIKLAR = KOK / "data/processed/entities.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task16_girdi_filtresi_olcum.json"


def main() -> int:
    for y in (VARLIKLAR, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gel = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    e = pd.read_parquet(
        VARLIKLAR,
        columns=["study_id", "entity_type", "normalized_concept", "assertion",
                 "temporality", "change_type", "assertion_rule", "temporality_rule"],
    )
    e = e[e["study_id"].isin(gel)]
    print(f"kapsam: gelistirme havuzu · {len(e):,} varlik / {e['study_id'].nunique():,} calisma\n")

    f = gf.uygula(e)
    o = gf.ozet(f)

    print("FILTRENIN ETKISI")
    print(f"  toplam varlik            {o['toplam_varlik']:>9,}")
    print(f"  dusuk guven isaretlenen  {o['dusuk_guven']:>9,}  (%{o['dusuk_guven_orani_yuzde']})")
    print(f"  suphe yukseltebilir      {o['suphe_yukseltebilir']:>9,}")
    print("\n  kural basina:")
    for kod, n in sorted(o["kural_basina"].items()):
        print(f"    {kod:24} {n:>9,}")

    # --- malignite ekseni ozel: filtre orada ne kadar isriyor ---
    mal = f[f["normalized_concept"].isin(gf.MALIGNITE_KAVRAMLARI)]
    mal_dg = int(mal["dusuk_guven"].sum())
    print(f"\n  MALIGNITE EKSENI ({len(mal):,} varlik)")
    print(f"    dusuk guven          {mal_dg:>9,}  (%{mal_dg/max(1,len(mal))*100:.1f})")
    print(f"    suphe yukseltebilir  {len(mal)-mal_dg:>9,}")

    # --- calisma duzeyi: kac raporda en az bir dusuk guvenli varlik var ---
    cal = f.groupby("study_id")["dusuk_guven"].any()
    print(f"\n  en az bir dusuk guvenli varlik iceren calisma: "
          f"{int(cal.sum()):,} / {len(cal):,}  (%{cal.mean()*100:.1f})")

    ozet = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "filtre": o,
        "malignite_ekseni": {
            "varlik": int(len(mal)),
            "dusuk_guven": mal_dg,
            "suphe_yukseltebilir": int(len(mal) - mal_dg),
        },
        "calisma_duzeyi": {
            "toplam": int(len(cal)),
            "en_az_bir_dusuk_guvenli": int(cal.sum()),
        },
        "hata_butcesi": gf.hata_butcesi(),
        "kurallar": [
            {"kod": r.kod, "aciklama": r.aciklama, "dayanak": r.dayanak}
            for r in gf.KURALLAR
        ],
        "not": (
            "Duyarlilik analizi (docs/29 §7/3) SEMA YAZILDIKTAN SONRA kosulacak - "
            "cikarim katmaninin bilinen hata oranlari enjekte edilip rapor sinifi "
            "dagiliminin ne kadar kaydigi olculecek. Adim 6'nin ciktisina baglidir."
        ),
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
