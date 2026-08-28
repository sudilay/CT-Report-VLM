# -*- coding: utf-8 -*-
"""TASK-12: Kesinlik, belirsizlik ve zamansallik atamasini korpusa uygular.

Gunceller:
  data/processed/entities.parquet      assertion/temporality/change_type + ipucu ve kural
  data/processed/measurements.parquet  olcu duzeyi temporality (meas-1.2)

Cikti SEMAYA KARSI DOGRULANIR (sema-1.3); ihlal varsa YAZILMAZ.

OLCU DUZEYI ZAMANSALLIK NEDEN AYRI:
  661 cumlede ayni cumlede iki farkli zamana ait iki olcu var:
    "...51x42 mm in the current examination and 46x36 mm in the previous PET-CT"
  Varlik duzeyi tek bir deger bunu tasiyamaz. Varlik 'current' (kitle simdi var),
  olculer ayri ayri 'current' ve 'prior'.

Sira: 08_extract_entities.py -> 11_apply_context.py
Kullanim: .venv/Scripts/python.exe scripts/11_apply_context.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import context as C     # noqa: E402
from radyovlm.extraction import schema as S      # noqa: E402

PROC = ROOT / "data" / "processed"
ANAHTAR = ["study_id", "section", "sent_idx"]


def main() -> None:
    ipuclari, sonlandirici = C.ipuclarini_kur()
    print(f"ipucu sozlugu: {len(ipuclari)} girdi")

    sent = pd.read_parquet(PROC / "sentences.parquet")
    ent = pd.read_parquet(PROC / "entities.parquet")
    meas = pd.read_parquet(PROC / "measurements.parquet")
    reps = pd.read_parquet(PROC / "reports_study_level.parquet",
                           columns=["study_id", "report_text"])
    print(f"girdi: {len(ent):,} varlik · {len(meas):,} olcu · {len(sent):,} cumle")

    cumle_bas = {tuple(k): v for k, v in
                 zip(sent[ANAHTAR].values, sent.char_start)}
    metinler = {tuple(k): v for k, v in zip(sent[ANAHTAR].values, sent.text)}

    ent_g = {k: v for k, v in ent.groupby(ANAHTAR)}
    meas_g = {k: v for k, v in meas.groupby(ANAHTAR)}

    e_sonuc, m_sonuc = {}, {}
    for k, metin in metinler.items():
        varlik_df = ent_g.get(k)
        olcu_df = meas_g.get(k)
        if varlik_df is None and olcu_df is None:
            continue
        cb = cumle_bas[k]

        if varlik_df is not None:
            vs = [{"id": r.entity_id, "bas": r.char_start - cb,
                   "son": r.char_end - cb, "tip": r.entity_type}
                  for r in varlik_df.itertuples(index=False)]
            for x in C.zaman_ata(metin, C.kesinlik_ata(metin, vs, ipuclari,
                                                       sonlandirici),
                                 ipuclari, sonlandirici):
                e_sonuc[x["id"]] = x

        if olcu_df is not None:
            os_ = [{"id": r.measurement_id, "bas": r.char_start - cb,
                    "son": r.char_end - cb}
                   for r in olcu_df.itertuples(index=False)]
            for x in C.zaman_ata(metin, os_, ipuclari, sonlandirici):
                m_sonuc[x["id"]] = x

    # ---------------- varliklara yaz ----------------
    def al(kimlik, alan, varsayilan=None):
        r = e_sonuc.get(kimlik)
        return r[alan] if r else varsayilan

    ent["assertion"] = [al(i, "assertion", "present") for i in ent.entity_id]
    ent["assertion_cue"] = [al(i, "assertion_cue") for i in ent.entity_id]
    ent["assertion_rule"] = [al(i, "assertion_rule", "varsayilan_present")
                             for i in ent.entity_id]
    ent["temporality"] = [al(i, "temporality", "current") for i in ent.entity_id]
    ent["temporality_cue"] = [al(i, "temporality_cue") for i in ent.entity_id]
    ent["temporality_rule"] = [al(i, "temporality_rule", "varsayilan_current")
                               for i in ent.entity_id]
    ent["change_type"] = [al(i, "change_type", "none") for i in ent.entity_id]
    ent["change_cue"] = [al(i, "change_cue") for i in ent.entity_id]
    ent["change_rule"] = [al(i, "change_rule", "karsilastirma_yok")
                          for i in ent.entity_id]
    ent["context_version"] = C.CONTEXT_VERSION

    # ---------------- olculere yaz ----------------
    def alm(kimlik, alan, varsayilan=None):
        r = m_sonuc.get(kimlik)
        return r[alan] if r else varsayilan

    meas["temporality"] = [alm(i, "temporality", "current")
                           for i in meas.measurement_id]
    meas["temporality_cue"] = [alm(i, "temporality_cue") for i in meas.measurement_id]
    meas["temporality_rule"] = [alm(i, "temporality_rule", "varsayilan_current")
                                for i in meas.measurement_id]
    meas["measurement_version"] = "meas-1.2"

    # ---------------- sema kapisi ----------------
    print("\nsema dogrulamasi (sema-1.3)...")
    ihl = S.dogrula_entities(ent, sentences=sent, reports=reps)
    S.dogrula_veya_dur(ihl, "TASK-12 ciktisi")
    print("  gecti - K1, K1b, K1c, K3, K3b, K3c, K3d, K3e, K3f, K3g")

    ent.to_parquet(PROC / "entities.parquet", index=False)
    meas.to_parquet(PROC / "measurements.parquet", index=False)
    ozet(ent, meas)


def ozet(ent: pd.DataFrame, meas: pd.DataFrame) -> None:
    print(f"\nyazildi: entities.parquet ({len(ent):,}) · "
          f"measurements.parquet (meas-1.2)")

    print("\nKESINLIK (assertion)")
    for k, n in ent.assertion.value_counts().items():
        print(f"  {k:<14} {n:>9,}  (%{100*n/len(ent):.1f})")

    print("\n  en sik kural:")
    for k, n in ent.assertion_rule.value_counts().head(8).items():
        print(f"    {k:<42} {n:>9,}")

    print("\nZAMANSALLIK (varlik)")
    for k, n in ent.temporality.value_counts().items():
        print(f"  {k:<14} {n:>9,}  (%{100*n/len(ent):.1f})")

    print("\nDEGISIM (change_type)")
    for k, n in ent.change_type.value_counts().items():
        print(f"  {k:<14} {n:>9,}  (%{100*n/len(ent):.1f})")

    print("\nOLCU DUZEYI ZAMANSALLIK (meas-1.2)")
    for k, n in meas.temporality.value_counts().items():
        print(f"  {k:<14} {n:>9,}  (%{100*n/len(meas):.1f})")
    onceki = int((meas.temporality == "prior").sum())
    print(f"  -> onceki tetkike ait olcu: {onceki:,}")

    # Gozlem tipine gore - klinik olarak asil ilgilendigimiz
    goz = ent[ent.entity_type == "observation"]
    print(f"\nYALNIZCA GOZLEMLER ({len(goz):,})")
    for k, n in goz.assertion.value_counts().items():
        print(f"  {k:<14} {n:>9,}  (%{100*n/len(goz):.1f})")


if __name__ == "__main__":
    main()
