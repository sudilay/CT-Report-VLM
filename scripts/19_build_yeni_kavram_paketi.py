# -*- coding: utf-8 -*-
"""TASK-13: Sozluge YENI eklenen kavramlar icin yargilama paketi.

NEDEN AYRI BIR PAKET:
  bulgu-1.1 / anat-1.1 ile 13 yeni kavram eklendi ve korpusta 20.435 varlik
  urettiler. Isaretleyiciler ESKI aday listesini yargilamisti; bu varliklarin
  hicbirini gormediler. Duyarliligin yukseldigini gosterip kesinligi bedava
  saymak olmaz - yeni adaylar da yargilanmali.

  Ayar kumesinin 150 cumlesinde yalnizca 19 yeni varlik var; kavram basina
  kesinlik olcmeye yetmez. Bu yuzden YENI ornek cekilir.

D26 KORUMALARI (kod otomatik reddeder):
  - yalnizca TRAIN hastalari; valid dokunulmaz (test-v1 rezervi)
  - daha once incelenmis/tuketilen hastalar DISLANIR
  - ayar kumesindeki cumleler DISLANIR (ayni cumle iki kez yargilanmasin)

CELDIRICI: 14_build_gold_template.py ile ayni disiplin - sistemin URETMEDIGI
sahte adaylar karistirilir, anahtar AYRI dosyada tutulur.

Kullanim: .venv/Scripts/python.exe scripts/19_build_yeni_kavram_paketi.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
K = ["study_id", "section", "sent_idx"]
TOHUM = 20260828
KAVRAM_BASINA = 8
CELDIRICI_ORAN = 0.20

YENI = ["covid", "pleuroparenchymal", "small_airway_disease",
        "small_vessel_disease", "soft_tissue_density", "adiposity", "edema",
        "infective_pathology", "aortic_valve", "pulmonary_conus",
        "lymphadenomegaly", "lymphoma", "goiter"]


def main() -> None:
    rng = np.random.default_rng(TOHUM)
    e = pd.read_parquet(P / "entities.parquet")
    s = pd.read_parquet(P / "sentences.parquet")

    # --- D26 kapilari ---
    yasak = set()
    for ad in ("tuketilen_valid_hastalar.csv", "incelenmis_hastalar.csv"):
        yol = P / ad
        if yol.exists():
            d = pd.read_csv(yol, encoding="utf-8-sig")
            kol = "patient_id" if "patient_id" in d.columns else d.columns[0]
            yasak |= set(d[kol].astype(str))
    ayar = pd.read_csv(P / "task12_ayar.csv", encoding="utf-8-sig")
    ayar_c = set(map(tuple, ayar[K].values))

    aday = e[e.normalized_concept.isin(YENI)].copy()
    aday["_hasta"] = aday.study_id.str.rsplit("_", n=1).str[0]
    once = len(aday)
    aday = aday[~aday.study_id.str.startswith(("valid", "test"))]
    aday = aday[~aday._hasta.astype(str).isin(yasak)]
    aday = aday[[tuple(x) not in ayar_c for x in aday[K].values]]
    print(f"yeni kavram varligi {once:,} -> D26 kapilarindan sonra {len(aday):,}")
    if aday.study_id.str.startswith(("valid", "test")).any():
        sys.exit("DURDU: valid/test sizintisi")

    # --- kavram basina esit ornek ---
    sec = []
    for k in YENI:
        g = aday[aday.normalized_concept == k]
        if g.empty:
            print(f"  UYARI: {k} icin aday yok")
            continue
        n = min(KAVRAM_BASINA, len(g))
        sec.append(g.sample(n=n, random_state=TOHUM))
    sec = pd.concat(sec, ignore_index=True)

    metin = s.set_index(K).text
    bas = s.set_index(K).char_start
    satir = []
    for r in sec.itertuples(index=False):
        k = (r.study_id, r.section, r.sent_idx)
        cb = bas.loc[k]
        satir.append({
            "study_id": r.study_id, "section": r.section, "sent_idx": r.sent_idx,
            "cumle": metin.loc[k],
            "aday_metin": r.raw_text, "aday_tip": r.entity_type,
            "aday_kavram": r.normalized_concept,
            "_gizli_sahte": 0, "_gizli_assertion": r.assertion,
            "dogru_varlik_mi": "", "dogru_kavram_mi": "",
            "kesinlik_ne_olmali": "", "not": "",
        })

    # --- celdirici: sistemin URETMEDIGI sahte adaylar ---
    n_sahte = int(len(satir) * CELDIRICI_ORAN / (1 - CELDIRICI_ORAN))
    kelimeler = {}
    for r in sec.itertuples(index=False):
        k = (r.study_id, r.section, r.sent_idx)
        t = metin.loc[k]
        gercek = {x.lower() for x in e[(e.study_id == r.study_id)
                                       & (e.section == r.section)
                                       & (e.sent_idx == r.sent_idx)].raw_text}
        aday_k = [w for w in str(t).split()
                  if len(w) > 4 and w.strip(".,;:()").lower() not in gercek]
        if aday_k:
            kelimeler[k] = aday_k
    anahtarlar = list(kelimeler)
    for _ in range(n_sahte):
        k = anahtarlar[rng.integers(len(anahtarlar))]
        w = kelimeler[k][rng.integers(len(kelimeler[k]))].strip(".,;:()")
        satir.append({
            "study_id": k[0], "section": k[1], "sent_idx": k[2],
            "cumle": metin.loc[k], "aday_metin": w,
            "aday_tip": YENI[rng.integers(len(YENI))] and "observation",
            "aday_kavram": YENI[rng.integers(len(YENI))],
            "_gizli_sahte": 1, "_gizli_assertion": None,
            "dogru_varlik_mi": "", "dogru_kavram_mi": "",
            "kesinlik_ne_olmali": "", "not": "",
        })

    df = pd.DataFrame(satir).sample(frac=1, random_state=TOHUM + 1).reset_index(drop=True)
    df.insert(0, "aday_no", range(len(df)))
    gizli = df[["aday_no", "study_id", "section", "sent_idx", "aday_metin",
                "aday_kavram", "_gizli_sahte", "_gizli_assertion"]]
    gorunen = df.drop(columns=["_gizli_sahte", "_gizli_assertion"])

    for m in ("codex", "gemini"):
        yol = P / f"YENIKAVRAM_{m}.csv"
        if yol.exists():
            v = pd.read_csv(yol, encoding="utf-8-sig")
            if "dogru_varlik_mi" in v and v.dogru_varlik_mi.notna().any():
                sys.exit(f"DURDU: {yol.name} DOLU, uzerine yazilmadi.")
        gorunen.to_csv(yol, index=False, encoding="utf-8-sig")
    gizli.to_csv(P / "YENIKAVRAM_anahtar.csv", index=False, encoding="utf-8-sig")

    print(f"\nyazildi: YENIKAVRAM_codex.csv · YENIKAVRAM_gemini.csv  ({len(gorunen)} aday)")
    print(f"  bunlarin {int(gizli._gizli_sahte.sum())} tanesi CELDIRICI "
          f"(%{100*gizli._gizli_sahte.mean():.0f})")
    print(f"  anahtar AYRI: YENIKAVRAM_anahtar.csv  <-- isaretleyiciye VERILMEZ")
    print(f"  hasta sayisi: {gorunen.study_id.str.rsplit('_', n=1).str[0].nunique()}")


if __name__ == "__main__":
    main()
