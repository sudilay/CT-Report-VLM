# -*- coding: utf-8 -*-
"""TASK-11: Varlik, iliski ve olcu baglarini uretir.

Uretir:
  data/processed/entities.parquet              1 satir = 1 varlik anmasi
  data/processed/relations.parquet             1 satir = 1 iliski
  data/processed/unresolved_attachments.parquet 1 satir = kurulamayan 1 bag (D22)
  data/processed/measurements.parquet          meas-1.0 -> meas-1.1 (measurement_id)

Cikti SEMAYA KARSI DOGRULANIR; ihlal varsa YAZILMAZ (TASK-10 kapisi).

D21: assertion/temporality/change_type bu betikte KESIN DEGER ALMAZ. TASK-12
kosana kadar sirasiyla not_processed / unknown / unknown yazilir - onceki surumde
'present'/'current' yaziliyordu ve negasyon ipuclu cumlelerdeki 426.099 anma da
"mevcut" gorunuyordu.

D22: kurulamayan hicbir bag dusurulmez. Varlik CIKMAYAN cumlelerdeki olculer de
kaydedilir - onceki surumde o cumleler bastan atlaniyordu ve 805 olcu sessizce
yok oluyordu.

Sira: 04_segment_sentences.py -> 06_apply_templates.py -> 07_extract_measurements.py
      -> 08_extract_entities.py
Kullanim: .venv/Scripts/python.exe scripts/08_extract_entities.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import entities as E          # noqa: E402
from radyovlm.extraction import schema as S            # noqa: E402

PROC = ROOT / "data" / "processed"
SENT = PROC / "sentences.parquet"
MEAS = PROC / "measurements.parquet"
REPS = PROC / "reports_study_level.parquet"
OUT_E = PROC / "entities.parquet"
OUT_R = PROC / "relations.parquet"
OUT_C = PROC / "unresolved_attachments.parquet"
OUTD = ROOT / "reports"


def main() -> None:
    kavramlar, taraf_sozluk = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)
    t_desen, t_indeks = E.taraf_matcher(taraf_sozluk)
    print(f"sozluk: {len(kavramlar)} kavram "
          f"({sum(1 for k in kavramlar if k.tip=='observation')} gozlem, "
          f"{sum(1 for k in kavramlar if k.tip=='anatomy')} anatomi, "
          f"{sum(1 for k in kavramlar if k.tip=='qualifier')} niteleyici, "
          f"{sum(1 for k in kavramlar if k.tip=='device')} cihaz)")

    sent = pd.read_parquet(SENT)
    meas = pd.read_parquet(MEAS)
    reps = pd.read_parquet(REPS, columns=["study_id", "report_text",
                                          "impression_is_null"])
    print(f"girdi : {len(sent):,} cumle · {len(meas):,} olcu")

    # --- olculere kalici kimlik (meas-1.1) ---
    if "measurement_id" not in meas.columns:
        meas["measurement_id"] = [
            E._kimlik(r.study_id, r.section, r.sent_idx, r.meas_idx, r.char_start)
            for r in meas.itertuples(index=False)]
    if "temporality" not in meas.columns:
        meas["temporality"] = "unknown"      # TASK-12 dolduracak
    meas["measurement_version"] = E.MEASUREMENT_VERSION_YENI

    olcu_indeks: dict[tuple, list] = {}
    for r in meas.itertuples(index=False):
        olcu_indeks.setdefault((r.study_id, r.section, r.sent_idx), []).append(
            {"id": r.measurement_id, "bas": r.char_start, "son": r.char_end})

    surumler = {k: sent[k].iloc[0] for k in ("segmentation_version",
                                             "template_version")}

    ent_satir, rel_satir, coz_satir = [], [], []

    for r in sent.itertuples(index=False):
        metin = r.text
        varliklar = E.cumleden_varliklar(metin, matcher, indeks)
        cumle_olculeri = olcu_indeks.get((r.study_id, r.section, r.sent_idx), [])
        if not varliklar:
            # Varlik yok ama OLCU olabilir. Ilk surumde bu cumleler tamamen
            # atlaniyordu ve icindeki 805 olcu SESSIZCE dusuyordu - tam olarak
            # unresolved_attachments'in engellemek icin var oldugu sey.
            for o in cumle_olculeri:
                coz_satir.append({
                    "source_id": o["id"], "source_kind": "measurement",
                    "study_id": r.study_id, "section": r.section,
                    "sent_idx": r.sent_idx, "relation_type": "measured_by",
                    "reason": "aday_yok", "n_candidates": 0,
                    "entity_version": E.ENTITY_VERSION,
                })
            continue
        taraflar = E.taraf_bul(metin, t_desen, t_indeks)

        for v in varliklar:
            k = v["kavram"]
            mutlak_bas = r.char_start + v["bas"]
            mutlak_son = r.char_start + v["son"]
            v["entity_id"] = E._kimlik(r.study_id, r.section, r.sent_idx,
                                       mutlak_bas, mutlak_son, k.ad)
            v["mutlak_bas"], v["mutlak_son"] = mutlak_bas, mutlak_son
            ent_satir.append({
                "entity_id": v["entity_id"], "study_id": r.study_id,
                "section": r.section, "sent_idx": r.sent_idx,
                "char_start": mutlak_bas, "char_end": mutlak_son,
                "raw_text": v["metin"], "entity_type": k.tip,
                "qualifier_group": k.grup,
                "normalized_concept": k.ad, "concept_source": "yerel_sozluk",
                "laterality": (E.taraf_ata(taraflar, v["bas"], v["son"])
                               if k.taraf_alir else None),
                # sema-1.1: TASK-12 kosmadan kesinlik/zaman IDDIA EDILMEZ.
                # Onceki surumde 'present'/'current' yaziliyordu ve negasyon
                # ipuclu cumlelerdeki 426.099 anma da "mevcut" gorunuyordu.
                "assertion": "not_processed", "temporality": "unknown",
                "change_type": "unknown",
                # sema-1.2 IZLENEBILIRLIK ALANLARI (2026-08-28'de eklendi):
                # Bu betik sema-1.1 doneminde yazilmisti; sema-1.2 kesinlik ve
                # zaman atamalarinin DAYANAGINI zorunlu kildiginda guncellenmedi.
                # Sonuc: sozluk genisletilip 08 yeniden kosuldugunda sema kapisi
                # ciktiyi reddetti (K0: kolon eksik). Kapi dogru davrandi.
                # Degerler burada None'dir - TASK-12 dolduracak (D21).
                "assertion_cue": None, "assertion_rule": "islenmedi",
                "temporality_cue": None, "temporality_rule": "islenmedi",
                "change_cue": None, "change_rule": "islenmedi",
                # Surum zincirinin son halkasi. Burada "islenmedi" yazar;
                # TASK-12 kosunca gercek ctx surumuyle DEGISTIRILIR. Boylece
                # baglam atanmamis bir ciktinin ctx surumu tasimasi engellenir.
                "context_version": "islenmedi",
                "mentioned_in_findings": False,
                "mentioned_in_impression": False,
                "promoted_to_impression": False,
                "extraction_rule": "sozluk_eslesme",
                **surumler, "entity_version": E.ENTITY_VERSION,
            })

        olculer = [{"id": o["id"], "bas": o["bas"] - r.char_start,
                    "son": o["son"] - r.char_start} for o in cumle_olculeri]

        iliskiler, cozulemeyenler = E.iliskileri_kur(varliklar, olculer, metin)
        for c in cozulemeyenler:
            k = c["kaynak"]
            coz_satir.append({
                "source_id": k["id"] if c["olcu_mu"] else k["entity_id"],
                "source_kind": "measurement" if c["olcu_mu"] else "entity",
                "study_id": r.study_id, "section": r.section,
                "sent_idx": r.sent_idx, "relation_type": c["tip"],
                "reason": c["sebep"], "n_candidates": c["n_aday"],
                "entity_version": E.ENTITY_VERSION,
            })
        for il in iliskiler:
            olcu_ucu = il.get("tail_olcu", False)
            head_id = il["head"]["entity_id"]
            tail_id = il["tail"]["id"] if olcu_ucu else il["tail"]["entity_id"]
            rel_satir.append({
                "relation_id": E._kimlik(head_id, tail_id, il["tip"]),
                "study_id": r.study_id,
                "head_id": head_id, "head_kind": "entity",
                "tail_id": tail_id,
                "tail_kind": "measurement" if olcu_ucu else "entity",
                "relation_type": il["tip"], "attachment_rule": il["kural"],
                "is_cross_sentence": False,
                "entity_version": E.ENTITY_VERSION,
                "relation_version": E.RELATION_VERSION,
            })

    ent = pd.DataFrame(ent_satir)
    rel = pd.DataFrame(rel_satir).drop_duplicates("relation_id")
    coz = pd.DataFrame(coz_satir)
    print(f"\ncikarildi: {len(ent):,} varlik · {len(rel):,} iliski · "
          f"{len(coz):,} cozulemeyen bag")

    # --- D8/D19: Findings -> Impression onem sinyali ---
    ent = onem_sinyali(ent, reps)

    # --- TASK-10 kapisi: sema dogrulamasi ---
    print("\nsema dogrulamasi...")
    sema = S.yukle()
    ihl = S.dogrula_entities(ent, sema, sentences=sent, reports=reps)
    ihl += S.dogrula_relations(rel, sema, entities=ent, measurements=meas)
    S.dogrula_veya_dur(ihl, "TASK-11 ciktisi")
    print("  gecti - K1, K1b, K1c, K2, K2b, K2c, K3, K3b, K3c, K3d")

    ent.to_parquet(OUT_E, index=False)
    rel.to_parquet(OUT_R, index=False)
    if not coz.empty:
        coz.to_parquet(OUT_C, index=False)
    meas.to_parquet(MEAS, index=False)
    ozet(ent, rel, coz, sent, meas)


def onem_sinyali(ent: pd.DataFrame, reps: pd.DataFrame) -> pd.DataFrame:
    """D19: kavram Findings'te ve Impression'da geciyor mu.

    TUZAK (D14): 825 calismada Impression yok - 811'i "Not given.", 14'u bos.
    "Not given." bolutlemede NORMAL BIR CUMLE gibi gorunur ve o calismalar
    impression bolumune sahipmis gibi durur. Dislanmazsa 825 calismada
    "hicbir bulgu Impression'a tasinmadi" gibi SAHTE bir sinyal uretilir.
    """
    bos = set(reps.loc[reps.impression_is_null, "study_id"])
    anahtar = ["study_id", "normalized_concept"]

    f = set(map(tuple, ent.loc[ent.section == "findings", anahtar].values))
    i = set(map(tuple, ent.loc[ent.section == "impression", anahtar].values))

    ikili = list(zip(ent.study_id, ent.normalized_concept))
    ent["mentioned_in_findings"] = [x in f for x in ikili]
    ent["mentioned_in_impression"] = [x in i for x in ikili]

    # DARALTMA (inceleme): once bu bayrak kavramin TUM satirlarina - Impression
    # satirlarina da - konuyordu ve anatomiyi de kapsiyordu; 242.533 anatomi
    # anmasi "tasinmis" gorunuyordu, 'lung' tek basina 87.671 kez. Anatominin
    # iki bolumde de gecmesi bir ONEM sinyali degil, iskelet tekrari.
    # Artik: yalnizca FINDINGS satirinda (tasinan anma odur) ve anatomi haric.
    ent["promoted_to_impression"] = [
        (x in f) and (x in i) and (x[0] not in bos)
        and sec == "findings" and tip != "anatomy"
        for x, sec, tip in zip(ikili, ent.section, ent.entity_type)]
    return ent


def ozet(ent, rel, coz, sent, meas) -> None:
    OUTD.mkdir(exist_ok=True)
    print(f"\nyazildi: entities.parquet ({len(ent):,}) · "
          f"relations.parquet ({len(rel):,}) · measurements.parquet (meas-1.1)")

    print("\nVARLIK TIPLERI")
    for tip, n in ent.entity_type.value_counts().items():
        print(f"  {tip:<14} {n:>9,}")

    kaps = ent.groupby(["study_id", "section", "sent_idx"]).ngroups
    print(f"\nKAPSAMA")
    print(f"  varlik iceren cumle : {kaps:,} / {len(sent):,} "
          f"(%{100*kaps/len(sent):.1f})")
    print(f"  varlik iceren calisma: {ent.study_id.nunique():,}")

    print("\nILISKI TIPLERI")
    for tip, n in rel.relation_type.value_counts().items():
        print(f"  {tip:<14} {n:>9,}")

    print("\nBAGLAMA KURALLARI (D18 - hangi kural kac bag kurdu)")
    for kural, n in rel.attachment_rule.value_counts().items():
        print(f"  {kural:<20} {n:>9,} (%{100*n/len(rel):.1f})")

    print("\nOLCU-BULGU BAGI")
    ob = rel[rel.relation_type == "measured_by"]
    print(f"  bag KURULAN olcu : {ob.tail_id.nunique():,} / {len(meas):,} "
          f"(%{100*ob.tail_id.nunique()/len(meas):.1f})")
    print("  !! Bu BAGLANMA orani; DOGRULUK orani DEGILDIR.")
    print("     Baglarin dogrulugu TASK-13'te altin aciklama setiyle olculecek.")

    print("\nCOZULEMEYEN BAGLAR (sema-1.1 - artik izlenebilir)")
    if coz.empty:
        print("  yok")
    else:
        for (tip, sebep), n in coz.groupby(["relation_type", "reason"]).size().items():
            print(f"  {tip:<14} {sebep:<12} {n:>7,}")

    print("\nTARAF")
    t = ent.laterality.value_counts(dropna=False)
    print(f"  {t.to_dict()}")

    print("\nONEM SINYALI (D19)")
    print(f"  Impression'a tasinan varlik anmasi: "
          f"{int(ent.promoted_to_impression.sum()):,} (%{100*ent.promoted_to_impression.mean():.1f})")


if __name__ == "__main__":
    main()
