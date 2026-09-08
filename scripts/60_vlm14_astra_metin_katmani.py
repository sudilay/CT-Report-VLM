"""SUDE-VLM-14 · Adim 1 · Astra metin katmani.

Astra raporlarini bolumlere ayirir, cumlelere boluter ve
`data/processed/astra_sentences.parquet` uretir.

⛔ GIRDI KOLONU KISITI (docs/39 §6): kaynak dosyadan YALNIZ
   PID · Seri_Anahtari · Radyoloji_Raporu okunur.
   `Kanser_Etiketi_y`, `Censor_Time`, `Pillar_Ensemble_Skoru` OKUNMAZ.
   `split` ve `included_in_evaluation` bolunme KILIDINDEN turetilir
   (kilit dislanan seri anahtarlarini kaydetmistir), etiketten degil.
   Boylece held-out ozellikleri yapisal olarak KOR uretilir.

Kullanim:
    python scripts/60_vlm14_astra_metin_katmani.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import medspacy  # noqa: F401  - spaCy fabrikalarini kaydeder
import pandas as pd
import spacy

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import astra as A  # noqa: E402

KAYNAK = KOK / "astra_radiology_reports_with_labels_all.xlsx"
KILIT = KOK / "configs/splits_astra.json"
CIKTI = KOK / "data/processed/astra_sentences.parquet"
OZET = KOK / "reports/vlm14_metin_katmani_ozeti.json"

# ⛔ Bu liste degistirilmeden once docs/39 §6 okunmalidir.
IZINLI_KOLONLAR = ["PID", "Seri_Anahtari", "Radyoloji_Raporu"]

SEGMENTASYON_SURUMU = "astra-seg-1.0"


def bolunme_haritasi() -> tuple[dict[str, str], set[str], str]:
    """seri/pid -> split esleme ve dislanan seri anahtarlari (kilitten)."""
    k = json.loads(KILIT.read_text(encoding="utf-8"))
    pid_split: dict[str, str] = {}
    for ad in ("train", "dev", "held_out"):
        for pid in k["bolunme"][ad]["pid_listesi"]:
            pid_split[str(pid)] = ad
    dislanan = set(k["filtre"]["dislanan_seri_anahtarlari"])
    return pid_split, dislanan, k["surum"]


def main() -> None:
    pid_split, dislanan, kilit_surumu = bolunme_haritasi()

    df = pd.read_excel(KAYNAK, usecols=IZINLI_KOLONLAR)
    print(f"kaynak: {len(df):,} seri · okunan kolon: {IZINLI_KOLONLAR}")

    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")

    def isler():
        for r in df.itertuples(index=False):
            sk = str(r.Seri_Anahtari)
            pid = str(r.PID)
            for bolum_ham, icerik in A.bolumlere_ayir(str(r.Radyoloji_Raporu or "")):
                yield icerik, (sk, pid, bolum_ham)

    satirlar: list[dict] = []
    sayac: Counter = Counter()
    cumle_idx: dict[tuple[str, str], int] = {}

    for doc, (sk, pid, bolum_ham) in nlp.pipe(isler(), as_tuples=True,
                                              batch_size=64):
        kova, kapsam_ici, bilinmeyen = A.bolum_esle(bolum_ham)
        sayac[kova] += 1
        for sent in doc.sents:
            metin = sent.text.strip()
            if not metin or not any(c.isalpha() for c in metin):
                continue
            anahtar = (sk, bolum_ham)
            i = cumle_idx.get(anahtar, 0)
            cumle_idx[anahtar] = i + 1
            satirlar.append({
                "seri_anahtari": sk,
                "pid": pid,
                "split": pid_split.get(pid, "kohort_disi"),
                "included_in_evaluation": sk not in dislanan,
                "bolum_ham": bolum_ham,
                "bolum_eslenmis": kova,
                "kapsam_ici": kapsam_ici,
                "bilinmeyen_baslik": bilinmeyen,
                "cumle_idx": i,
                "cumle_metni": metin,
                "is_technical_param": A.teknik_satir_mi(metin),
                "has_placeholder": A.yer_tutucu_var_mi(metin),
            })

    out = pd.DataFrame(satirlar)
    out["sozlesme_surumu"] = A.SOZLESME_SURUMU
    out["segmentation_version"] = SEGMENTASYON_SURUMU
    out["bolunme_kilidi"] = kilit_surumu

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CIKTI, index=False)

    ozet = {
        "gorev": "SUDE-VLM-14 · Adim 1",
        "kaynak_seri": int(len(df)),
        "islenen_seri": int(out["seri_anahtari"].nunique()),
        "cumle": int(len(out)),
        "okunan_kolonlar": IZINLI_KOLONLAR,
        "bolunme_kilidi": kilit_surumu,
        "sozlesme_surumu": A.SOZLESME_SURUMU,
        "bolum_kova_dagilimi": dict(sayac),
        "kapsam_ici_cumle": int(out["kapsam_ici"].sum()),
        "kapsam_disi_cumle": int((~out["kapsam_ici"]).sum()),
        "bilinmeyen_baslikli_cumle": int(out["bilinmeyen_baslik"].sum()),
        "teknik_satir_cumle": int(out["is_technical_param"].sum()),
        "yer_tutuculu_cumle": int(out["has_placeholder"].sum()),
        "split_dagilimi": out.groupby("split")["seri_anahtari"].nunique().to_dict(),
        "dislanan_seri": int((~out["included_in_evaluation"]).sum() and
                             out.loc[~out["included_in_evaluation"],
                                     "seri_anahtari"].nunique()),
    }
    OZET.parent.mkdir(parents=True, exist_ok=True)
    OZET.write_text(json.dumps(ozet, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"\nislenen seri : {ozet['islenen_seri']:,} / {ozet['kaynak_seri']:,}")
    print(f"cumle        : {ozet['cumle']:,}")
    print(f"kapsam ici   : {ozet['kapsam_ici_cumle']:,}")
    print(f"kapsam disi  : {ozet['kapsam_disi_cumle']:,}")
    print(f"split        : {ozet['split_dagilimi']}")
    print(f"\nyazildi: {CIKTI.relative_to(KOK)} · {OZET.relative_to(KOK)}")


if __name__ == "__main__":
    main()
