"""SUDE-VLM-14 · Adim 5-6 · Dondurulmus motorla kosum.

Dondurulmus artefaktlar:
    `astra-sozlesme-1.1` · `astra-adaptor-1.2` · `sema-1.0` · `astra-split-1.0`

⛔ KAPSAM BAYRAGI ZORUNLU. Varsayilan `train`'dir; `dev` ve `tam` ACIKCA
   istenmeden kosulmaz. Kurallar Adim 4'te kilitlendigi icin `dev` YALNIZ BIR
   KEZ acilir; `dev`de gorulen sonuca gore adaptor degistirilirse bu ACIKCA
   kaydedilir ve `dev` artik dogrulama kumesi sayilmaz.

⛔ HELD-OUT KOR URETILIR: ozellikler dondurulmus motorla uretilir, etiketle
   BIRLESTIRILMEZ, metrik HESAPLANMAZ. Etiketli degerlendirme VLM-23'undur.
   Hat kaynak dosyadan yalniz PID · Seri_Anahtari · Radyoloji_Raporu okur
   (docs/39 §6); etiket kolonlari bu betikte HIC acilmaz.

Kullanim:
    python scripts/63_vlm14_tam_kosum.py --kapsam train
    python scripts/63_vlm14_tam_kosum.py --kapsam dev
    python scripts/63_vlm14_tam_kosum.py --kapsam tam
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.evaluation import sema  # noqa: E402
from radyovlm.evaluation import vlm14 as V  # noqa: E402
from radyovlm.extraction import astra as A  # noqa: E402
from radyovlm.extraction import context as C  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

CUMLELER = KOK / "data/processed/astra_sentences.parquet"
KILIT_ADAPTOR = KOK / "configs/astra_adaptor_kilidi.json"
KILIT_BOLUNME = KOK / "configs/splits_astra.json"
CIKTI_DIZIN = KOK / "outputs/vlm14"

KAPSAMLAR = {
    "train": ["train"],
    "dev": ["train", "dev"],
    "tam": ["train", "dev", "held_out", "kohort_disi"],
}


def _olcu_modulu():
    yol = KOK / "scripts/07_extract_measurements.py"
    spec = importlib.util.spec_from_file_location("_olcu07", yol)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_olcu07"] = mod
    spec.loader.exec_module(mod)
    return mod


def cikar(cumleler: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Varlik ve iliski katmanlarini uretir (etiket OKUNMAZ)."""
    olcu07 = _olcu_modulu()
    kavramlar, _ = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)
    ipuclari, sonlandirici = C.ipuclarini_kur()

    satirlar: list[dict] = []
    iliskiler: list[dict] = []

    for r in cumleler.itertuples(index=False):
        metin = r.cumle_metni
        varliklar = E.cumleden_varliklar(metin, matcher, indeks)
        if not varliklar:
            continue
        # ⚠ Bu iki fonksiyon YERINDE DEGISTIRMEZ, YENI LISTE DONDURUR.
        varliklar = C.kesinlik_ata(metin, varliklar, ipuclari, sonlandirici)
        varliklar = C.zaman_ata(metin, varliklar, ipuclari, sonlandirici)

        for i, v in enumerate(varliklar):
            v["_eid"] = f"astra-{len(satirlar) + i:08d}"

        olculer = []
        for m in olcu07.OLCU.finditer(metin):
            if A.olcu_teknik_mi(metin, m.start(), m.end()):   # TEK KAYNAK (K5.1)
                continue                      # teknik olcu ASLA baglanmaz
            olculer.append({"bas": m.start(), "son": m.end(),
                            "metin": m.group(0), "kavram": None})

        rel, _ = E.iliskileri_kur(varliklar, olculer, metin)
        for x in rel:
            bas, kuy = x["head"], x["tail"]
            iliskiler.append({
                "seri_anahtari": r.seri_anahtari,
                "bolum_ham": r.bolum_ham, "cumle_idx": r.cumle_idx,
                "relation_type": x["tip"],
                "head_id": bas.get("_eid") if isinstance(bas, dict) else None,
                "tail_id": kuy.get("_eid") if isinstance(kuy, dict) else None,
                "tail_olcu": bool(x.get("tail_olcu")),
                "tail_metin": kuy.get("metin") if isinstance(kuy, dict) else None,
                "kural": x.get("kural"),
            })

        for v in varliklar:
            kav = v["kavram"]
            satirlar.append({
                "entity_id": v["_eid"],
                "seri_anahtari": r.seri_anahtari, "pid": r.pid,
                "bolum_ham": r.bolum_ham, "bolum_eslenmis": r.bolum_eslenmis,
                "kapsam_ici": r.kapsam_ici, "cumle_idx": r.cumle_idx,
                "normalized_concept": kav.ad, "entity_type": kav.tip,
                "raw_text": v["metin"],
                # ⚠ Ofsetler ZORUNLU: anatomi filtresi span oncesi pencereyi
                # tarar (`TORAKS_ONEK_PENCERESI`). Kolon dusurulurse filtre
                # KeyError verir - sessizce yanlis sonuc uretmez.
                "char_start": v["bas"],
                "char_end": v["son"],
                "assertion": v.get("assertion"),
                "assertion_rule": v.get("assertion_rule"),
                "assertion_cue": v.get("assertion_cue"),
                "temporality": v.get("temporality"),
                "sablon_cumle": r.sablon_cumle,
                "cumle_metni": metin,
            })

    return pd.DataFrame(satirlar), pd.DataFrame(iliskiler)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kapsam", choices=sorted(KAPSAMLAR), default="train",
                    help="`dev` ve `tam` ACIKCA istenmelidir")
    args = ap.parse_args()
    splitler = KAPSAMLAR[args.kapsam]

    if args.kapsam != "train":
        print(f"[KAPSAM UYARISI] KAPSAM = {args.kapsam}. Bu kosum {splitler} kumelerini acar.")
        print("   Kurallar `astra-adaptor-1.2` ile KILITLIDIR; sonuca gore "
              "adaptor degistirilirse bu ACIKCA kaydedilmelidir.\n")

    # ⚠ Sablon istatistigi TANIM GEREGI yalniz train'den hesaplanir (D4), bu
    # nedenle train satirlari her kapsamda okunur. Kapsam disi split'ler
    # OKUMA ANINDA elenir - bellege alinmaz (R5.4).
    okunacak = sorted(set(splitler) | {"train"})
    c = pd.read_parquet(CUMLELER, filters=[("split", "in", okunacak)])
    c = V.sablon_kolonu_ekle(c)
    c = c[c["split"].isin(splitler)]

    print(f"kapsam: {args.kapsam} · {c['seri_anahtari'].nunique():,} seri "
          f"· {len(c):,} cumle")

    varlik, iliski = cikar(c)
    varlik = V.supheli_niteleyici_ekle(varlik, iliski)

    kanit = V.boyut_ekle(V.kanit_tablosu(varlik), iliski)
    boyutlu = set(kanit.loc[kanit["boyut_mm"].notna(), "seri_anahtari"])
    seri = V.seri_ozeti(varlik, c, boyutlu, iliski)

    CIKTI_DIZIN.mkdir(parents=True, exist_ok=True)
    ek = "" if args.kapsam == "tam" else f"_{args.kapsam}"
    seri.to_parquet(CIKTI_DIZIN / f"astra_seri_duzeyi{ek}.parquet", index=False)
    kanit.to_parquet(CIKTI_DIZIN / f"astra_kanit_duzeyi{ek}.parquet", index=False)

    kilit = json.loads(KILIT_ADAPTOR.read_text(encoding="utf-8"))
    bolunme = json.loads(KILIT_BOLUNME.read_text(encoding="utf-8"))
    gunluk = {
        "gorev": "SUDE-VLM-14 · Adim 5-6",
        "kosum_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": args.kapsam,
        "acilan_splitler": splitler,
        "surumler": {
            "sozlesme": A.SOZLESME_SURUMU,
            "adaptor": kilit["surum"],
            "sema": sema.SEMA_SURUMU,
            "bolunme": bolunme["surum"],
            "segmentasyon": "astra-seg-1.0",
            "sablon_esigi_K": V.SABLON_ESIGI,
        },
        "okunan_kaynak_kolonlar": ["PID", "Seri_Anahtari", "Radyoloji_Raporu"],
        "etiket_kolonu_okundu_mu": False,
        "held_out_beyani": (
            "Held-out serileri icin ozellikler dondurulmus motorla KOR bicimde "
            "uretilmistir; etiketle birlestirilmemis, hicbir metrik "
            "hesaplanmamis ve sonuclara gore hicbir kural degistirilmemistir. "
            "Etiketli degerlendirme SUDE-VLM-23'e birakilmistir."),
        "evren": {
            "aciklama": ("Uretim TUM serileri isler; dislanan seriler "
                         "`included_in_evaluation=false` ile isaretlenir. "
                         "Kilitteki `train_dogrulamasi` sayilari YALNIZ "
                         "degerlendirmeye dahil evreni kullanir."),
            "islenen_seri": int(seri["seri_anahtari"].nunique()),
            "degerlendirmeye_dahil_seri": int(
                seri.loc[seri["included_in_evaluation"], "seri_anahtari"].nunique()),
        },
        "sayilar": {
            "seri": int(seri["seri_anahtari"].nunique()),
            "cumle": int(len(c)),
            "varlik": int(len(varlik)),
            "iliski": int(len(iliski)),
            "kanit_satiri": int(len(kanit)),
            "degerlendirmeye_dahil_seri": int(seri["included_in_evaluation"].sum()),
            "dislanan_seri": int((~seri["included_in_evaluation"]).sum()),
        },
        "dagilimlar": {
            "malignite_sinifi": seri["report_derived_malignancy_label"]
                                .value_counts().to_dict(),
            "nodul_var_mi": seri["nodul_var_mi"].value_counts().to_dict(),
            "split": seri.groupby("split")["seri_anahtari"].nunique().to_dict(),
        },
        "kalite_bayraklari": {
            "measurement_available": int(seri["measurement_available"].sum()),
            "nodule_type_available": int(seri["nodule_type_available"].sum()),
            "qf_placeholder": int(seri["qf_placeholder"].sum()),
            "qf_bolum_eksik": int(seri["qf_bolum_eksik"].sum()),
            "qf_ekstratorasik_malignite_elendi":
                int(seri["qf_ekstratorasik_malignite_elendi"].sum()),
        },
    }
    yol = KOK / f"reports/vlm14_kosum_gunlugu{ek or '_tam'}.json"
    yol.write_text(json.dumps(gunluk, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    print(f"\nseri {gunluk['sayilar']['seri']:,} · varlik "
          f"{gunluk['sayilar']['varlik']:,} · iliski "
          f"{gunluk['sayilar']['iliski']:,}")
    print(f"malignite sinifi: {gunluk['dagilimlar']['malignite_sinifi']}")
    print(f"\nyazildi: outputs/vlm14/ · {yol.relative_to(KOK)}")


if __name__ == "__main__":
    main()
