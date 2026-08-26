# -*- coding: utf-8 -*-
"""TASK-11 ciktisi icin elle inceleme ornegi uretir.

TASK-13'un altin aciklama seti DEGILDIR - o ayri ve daha resmi bir istir.
Bu, cikarimin gozle taranabilmesi icin bir ornektir: cumle, cikan varliklar,
kurulan iliskiler ve hangi kuralin kurdugu yan yana.

Ornekleme HEDEFLI: kolay vakalar zaten cogunluk oldugu icin rastgele ornek
neredeyse hep kolay cikar ve zor alt kume hakkinda hicbir sey soylemez.
(Ayni hata Faz 1'de olcu-bag dogrulugunda da yapilabilirdi.)

Kullanim: .venv/Scripts/python.exe scripts/09_sample_entities.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PROC = ROOT / "data" / "processed"
OUTD = ROOT / "reports"
TOHUM = 20260826
N_GRUP = 25


def main() -> None:
    OUTD.mkdir(exist_ok=True)
    sent = pd.read_parquet(PROC / "sentences.parquet")
    ent = pd.read_parquet(PROC / "entities.parquet")
    rel = pd.read_parquet(PROC / "relations.parquet")
    meas = pd.read_parquet(PROC / "measurements.parquet")

    anahtar = ["study_id", "section", "sent_idx"]
    ent_g = {k: v for k, v in ent.groupby(anahtar)}
    rel_kaynak = {}
    for r in rel.itertuples(index=False):
        rel_kaynak.setdefault(r.head_id, []).append(r)

    ad = dict(zip(ent.entity_id, ent.raw_text))
    tip = dict(zip(ent.entity_id, ent.entity_type))
    olcu_ad = dict(zip(meas.measurement_id, meas.raw_text))

    olculu = set(map(tuple, meas[anahtar].drop_duplicates().values))
    coklu = {k for k, v in ent.groupby(anahtar).size().items() if v >= 5}
    ent_anahtar = dict(zip(ent.entity_id, map(tuple, ent[anahtar].values)))
    esitlik = {ent_anahtar[h] for h in
               rel.loc[rel.attachment_rule == "esitlikte_sag", "head_id"]
               if h in ent_anahtar}

    gruplar = {
        "rastgele": list(map(tuple, sent[anahtar].sample(
            N_GRUP, random_state=TOHUM).values)),
        "olculu": _sec(olculu, N_GRUP, TOHUM),
        "coklu_varlik": _sec(coklu, N_GRUP, TOHUM + 1),
        "esitlikte_bag": _sec(esitlik, N_GRUP, TOHUM + 2),
    }

    sm = sent.set_index(anahtar)
    satir = []
    for grup, anahtarlar in gruplar.items():
        for k in anahtarlar:
            if k not in ent_g:
                continue
            try:
                metin = sm.loc[k, "text"]
            except KeyError:
                continue
            metin = metin if isinstance(metin, str) else metin.iloc[0]
            e = ent_g[k]
            varliklar = " · ".join(
                f"{r.raw_text}[{r.entity_type[:4]}:{r.normalized_concept}"
                + (f"/{r.laterality}" if r.laterality else "") + "]"
                for r in e.itertuples(index=False))
            baglar = []
            for r in e.itertuples(index=False):
                for il in rel_kaynak.get(r.entity_id, []):
                    hedef = (olcu_ad.get(il.tail_id) if il.tail_kind == "measurement"
                             else ad.get(il.tail_id))
                    baglar.append(f"{r.raw_text} -{il.relation_type}-> {hedef} "
                                  f"({il.attachment_rule})")
            satir.append({
                "grup": grup, "study_id": k[0], "section": k[1], "sent_idx": k[2],
                "cumle": metin,
                "varliklar": varliklar,
                "iliskiler": " | ".join(baglar),
                "dogru_mu": "", "not": "",
            })

    df = pd.DataFrame(satir)
    yol = OUTD / "varlik_cikarim_ornegi.csv"
    df.to_csv(yol, index=False, encoding="utf-8-sig")
    print(f"yazildi: reports/{yol.name}  ({len(df)} cumle)")
    print(df.grup.value_counts().to_dict())
    print("\nKolonlar: cumle · varliklar · iliskiler · dogru_mu · not")
    print("Doldurulacak: dogru_mu (E/H/K=kismen) ve gerekirse not")


def _sec(kume, n, tohum):
    s = pd.Series(sorted(kume))
    return list(s.sample(min(n, len(s)), random_state=tohum))


if __name__ == "__main__":
    main()
