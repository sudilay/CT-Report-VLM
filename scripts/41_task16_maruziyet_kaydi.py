"""TASK-16 Adim 0 - MARUZIYET KAYDI.

Plan: docs/29_task16_calisma_plani.md §4.4

Neden: docs/29 §6'daki ornek cumleler, bolunme kilidi URETILMEDEN ONCE tum
korpustan cekildi. Bagimsiz denetim bunu kirlenme olarak isaretledi (docs/32
bulgu #5). Maruziyet kucuktur ama GIZLENMEZ: hangi calismalarin gorulduğu ve
kacinin degerlendirme kilidine dustugu olculur ve kayda gecirilir.

Emsal: TASK-14'te ayni yontem uygulandi ("maruziyet olculdu ve sifir cikti",
reports/turkce_bolunme_dondurma.md).

Kullanim:
    python scripts/41_task16_maruziyet_kaydi.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task16_maruziyet_kaydi.json"

# docs/29 §6'da plan metnine ALINAN cumleler.
# Anahtar = plandaki konum, deger = eslesme icin ayirt edici alt dize.
GORULEN = {
    "§6.1/1": "No active infiltration or mass lesion was observed in both lungs",
    "§6.1/2": "sequela calcific pulmonary nodule in the posterobasal segment",
    "§6.1/3": "Destruction area compatible with metastasis was observed in the sternum",
    "§6.2/1": "Stable, calcific parenchymal metastases in both lungs",
    "§6.2/2": "no lytic-destructive lesion in favor of metastasis was dete",
    "§6.2/3": "Suspicious findings in terms of Covid-19 viral pneumonia",
    "§6.2/4": "liver segment 8 is stable",
    "§6.2/5": "in favor of minimal sequelae",
}


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])

    s = pd.read_parquet(CUMLELER, columns=["study_id", "text", "is_stock_phrasing"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id", "split"])
    esleme = dict(zip(k["study_id"], k["patient_id"]))

    kayitlar = []
    for konum, parca in GORULEN.items():
        vurus = s[s["text"].str.contains(parca, case=False, regex=False, na=False)]
        calismalar = sorted(vurus["study_id"].unique().tolist())
        hastalar = sorted({esleme.get(c) for c in calismalar} - {None})
        kilitte = sorted(h for h in hastalar if h in kilitli)
        sablon = int(vurus["is_stock_phrasing"].sum())
        kayitlar.append({
            "plan_konumu": konum,
            "arama_parcasi": parca,
            "eslesen_cumle": int(len(vurus)),
            "sablon_cumle": sablon,
            "sablon_mu": sablon > len(vurus) / 2,
            "eslesen_calisma": len(calismalar),
            "eslesen_hasta": len(hastalar),
            "kilitteki_hasta": len(kilitte),
            "kilitteki_hasta_listesi": kilitte[:20],
            "ornek_calisma": calismalar[:3],
        })
        et = "SABLON" if sablon > len(vurus) / 2 else "ozgun"
        print(f"  {konum:8} cumle {len(vurus):>5} ({et:6})  calisma {len(calismalar):>5}  "
              f"hasta {len(hastalar):>5}  KILITTE {len(kilitte):>4}")

    tum_kilitte = sorted({h for r in kayitlar for h in r["kilitteki_hasta_listesi"]})
    toplam_hasta = sum(r["eslesen_hasta"] for r in kayitlar)
    toplam_kilitte = sum(r["kilitteki_hasta"] for r in kayitlar)

    ozet = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "amac": "docs/29 §6'daki ornek cumlelerin bolunme kilidinden ONCE gorulmus "
                "olmasinin olculmus kaydi (docs/32 bulgu #5).",
        "kilit_surumu": kilit["surum"],
        "gorulen_cumle_yeri": len(GORULEN),
        "toplam_eslesen_hasta": toplam_hasta,
        "toplam_kilitteki_hasta": toplam_kilitte,
        "benzersiz_kilitteki_hasta": len(tum_kilitte),
        "yorum": None,   # asagida doldurulur
        "kayitlar": kayitlar,
    }

    sablon_kayit = [r for r in kayitlar if r["sablon_mu"]]
    ozgun_kilitte = sorted({h for r in kayitlar if not r["sablon_mu"]
                            for h in r["kilitteki_hasta_listesi"]})
    ozet["sablon_olan_ornek"] = len(sablon_kayit)
    ozet["ozgun_ornekten_kilitteki_hasta"] = len(ozgun_kilitte)

    if toplam_kilitte == 0:
        ozet["yorum"] = ("Gorulen ornekler degerlendirme kilidine HIC dusmedi; "
                         "maruziyet sifirdir.")
    else:
        ozet["yorum"] = (
            f"Gorulen ornek cumlelerin gectigi {len(tum_kilitte)} benzersiz hasta "
            "degerlendirme kilidinde. MARUZIYET SIFIR DEGILDIR ve gizlenmiyor. "
            f"Ancak {len(sablon_kayit)} ornek SABLON cumledir (korpusun %71'i sablondur, "
            "AGENTS.md): bu metinler onlarca calismada BIREBIR ayni gecer ve hastaya "
            "ozgu hicbir bilgi tasimaz; gorulmeleri o hastalarin verisini gormek "
            "degildir. Ozgun (sablon olmayan) orneklerden kilide dusen benzersiz hasta "
            f"sayisi {len(ozgun_kilitte)}'dir. Her hâlukârda gorulen sey cumlelerin "
            "METNIDIR; hicbir etiket, sinif karari veya olcum bunlardan turetilmedi ve "
            "bu calismalar sinir/kontrol takimlarina ALINMAYACAKTIR (docs/29 §4.4 "
            "baglayici kurali)."
        )

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  toplam eslesen hasta      : {toplam_hasta}")
    print(f"  bunlardan KILITTE olan    : {toplam_kilitte}")
    print(f"  benzersiz kilitteki hasta : {len(tum_kilitte)}")
    print(f"\n  {ozet['yorum']}")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
