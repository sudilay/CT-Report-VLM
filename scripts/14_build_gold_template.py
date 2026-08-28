# -*- coding: utf-8 -*-
"""TASK-13 / C2: Altin aciklama icin KOR isaretleme dosyalari uretir.

IKI AYRI DOSYA - cunku duyarlilik ve kesinligin yanliliklari farkli:

  A · KOR LISTELEME  (duyarlilik / K5)
     Yalnizca cumle gosterilir. Isaretleyici icinde ne varsa yazar.
     Sistem ciktisi GOSTERILMEZ - gosterilirse sistemin KACIRDIGI sey hic akla
     gelmez ve duyarlilik olculemez.

  B · YARGILAMA  (kesinlik / K4 + K6/K7)
     Aday span gosterilir, "bu dogru mu" diye sorulur. Sunulan bir ogeyi
     yargilamak mesrudur ve hizlidir.
     YANLILIK ONLEMI: listeye sistemin URETMEDIGI sahte adaylar (celdirici)
     karistirilir. Isaretleyici her seye "dogru" diyorsa celdiricileri de kabul
     eder ve bunu goruruz. Celdirici ret orani rapora yazilir.

Kullanim:
    .venv/Scripts/python.exe scripts/14_build_gold_template.py            # ayar
    .venv/Scripts/python.exe scripts/14_build_gold_template.py --kume test-v1
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction import entities as E   # noqa: E402

PROC = ROOT / "data" / "processed"
ANAHTAR = ["study_id", "section", "sent_idx"]
TOHUM = 20260827
CELDIRICI_ORAN = 0.15      # aday listesinin ~%15'i sahte


def celdirici_uret(metin: str, gercek: list[tuple], kavramlar, rng) -> list[dict]:
    """Sistemin URETMEDIGI ama makul gorunen sahte adaylar.

    Amac isaretleyiciyi sinamak: her seye 'dogru' diyen bir isaretleyici
    bunlari da kabul eder ve olcum guvenilmez oldugu anlasilir.
    """
    kelimeler = [(m.start(), m.end()) for m in
                 __import__("re").finditer(r"\b[A-Za-z][A-Za-z\-]{4,}\b", metin)]
    dolu = {(b, s) for b, s, _ in gercek}
    bos = [x for x in kelimeler if x not in dolu]
    if not bos:
        return []
    n = max(1, int(len(gercek) * CELDIRICI_ORAN))
    sec = rng.sample(bos, min(n, len(bos)))
    adlar = [k.ad for k in kavramlar if k.tip == "observation"]
    return [{"bas": b, "son": s, "kavram": rng.choice(adlar), "sahte": True}
            for b, s in sec]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", default="ayar", help="ayar | test-v1 | test-v2")
    a = ap.parse_args()

    yol = PROC / f"task12_{a.kume}.csv"
    if not yol.exists():
        raise SystemExit(f"orneklem yok: {yol} - once scripts/10_build_eval_split.py")

    import random
    rng = random.Random(TOHUM)

    orn = pd.read_csv(yol, encoding="utf-8-sig")
    ent = pd.read_parquet(PROC / "entities.parquet")
    kavramlar, _ = E.sozlukleri_yukle()

    ent_g = {k: v for k, v in ent.groupby(ANAHTAR)}
    print(f"kume: {a.kume} · {len(orn)} cumle")

    # ---------------- A · KOR LISTELEME ----------------
    orn = orn.rename(columns={"text": "cumle"})
    kor = orn[["kume", "grup", "tur", "study_id", "section", "sent_idx", "cumle"]].copy()
    kor["bulgular"] = ""       # gozlemler, virgulle
    kor["anatomiler"] = ""     # anatomik yapilar, virgulle
    kor["notlar"] = ""
    kor = kor.sample(frac=1, random_state=TOHUM).reset_index(drop=True)  # sira karistir
    yol_a = PROC / f"task13_A_kor_listeleme_{a.kume}.csv"
    kor.to_csv(yol_a, index=False, encoding="utf-8-sig")

    # ---------------- B · YARGILAMA ----------------
    satir = []
    for r in orn.itertuples(index=False):
        k = (r.study_id, r.section, r.sent_idx)
        v = ent_g.get(k)
        if v is None:
            continue
        gercek = [(e.char_start, e.char_end, e) for e in v.itertuples(index=False)]
        for b, s, e in gercek:
            satir.append({
                "study_id": r.study_id, "section": r.section, "sent_idx": r.sent_idx,
                "grup": r.grup, "tur": r.tur, "cumle": r.cumle,
                "aday_metin": e.raw_text,
                "aday_tip": e.entity_type,
                "aday_kavram": e.normalized_concept,
                "_gizli_sahte": 0,
                "_gizli_assertion": e.assertion,
                "_gizli_temporality": e.temporality,
                "dogru_varlik_mi": "",       # E / H
                "dogru_kavram_mi": "",       # E / H  (varlik dogruysa)
                "kesinlik_ne_olmali": "",    # mevcut / yok / belirsiz
                "zaman_ne_olmali": "",       # guncel / onceki / bilinmiyor
                "not": "",
            })
        # celdiriciler
        metin = r.cumle if isinstance(r.cumle, str) else ""
        for c in celdirici_uret(metin, [(0, 0, None)] * len(gercek), kavramlar, rng):
            satir.append({
                "study_id": r.study_id, "section": r.section, "sent_idx": r.sent_idx,
                "grup": r.grup, "tur": r.tur, "cumle": r.cumle,
                "aday_metin": metin[c["bas"]:c["son"]],
                "aday_tip": "observation", "aday_kavram": c["kavram"],
                "_gizli_sahte": 1, "_gizli_assertion": "", "_gizli_temporality": "",
                "dogru_varlik_mi": "", "dogru_kavram_mi": "",
                "kesinlik_ne_olmali": "", "zaman_ne_olmali": "", "not": "",
            })

    b_df = pd.DataFrame(satir).sample(frac=1, random_state=TOHUM + 3).reset_index(drop=True)
    # gizli kolonlari AYRI dosyaya al - isaretleyici gormesin
    gizli = b_df[["study_id", "section", "sent_idx", "aday_metin", "aday_kavram",
                  "_gizli_sahte", "_gizli_assertion", "_gizli_temporality"]]
    gorunen = b_df.drop(columns=["_gizli_sahte", "_gizli_assertion",
                                 "_gizli_temporality"])
    yol_b = PROC / f"task13_B_yargilama_{a.kume}.csv"
    yol_g = PROC / f"task13_B_anahtar_{a.kume}.csv"
    gorunen.to_csv(yol_b, index=False, encoding="utf-8-sig")
    gizli.to_csv(yol_g, index=False, encoding="utf-8-sig")

    n_sahte = int(gizli._gizli_sahte.sum())
    print(f"\nA · kor listeleme : {yol_a.name}  ({len(kor)} cumle)")
    print(f"     kolonlar: bulgular · anatomiler · notlar   (sistem ciktisi YOK)")
    print(f"\nB · yargilama     : {yol_b.name}  ({len(gorunen)} aday)")
    print(f"     bunlarin {n_sahte} tanesi CELDIRICI (%{100*n_sahte/len(gorunen):.0f})")
    print(f"     anahtar AYRI dosyada: {yol_g.name}  <-- isaretleyiciye VERILMEZ")
    print(f"\nKilavuz: docs/11_isaretleme_kilavuzu.md")


if __name__ == "__main__":
    main()
