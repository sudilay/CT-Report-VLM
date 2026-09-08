"""SUDE-VLM-14 · Adim 2 · Astra `train` aktarim denetimi.

SORU: Sozlukler (`bulgu-1.2`, `anat-1.1`) CT-RATE metninde gelistirildi ve
Astra'nin dagilimini HIC gormedi. Motor Astra metnine aktarilabiliyor mu?

D56 DERSI: TASK-15'te kavram farkinin %78'i ceviri kaybi degil SOZLUK BOSLUGU
cikti; olculmeseydi yanlis sebebe baglanacakti. Ayni hatayi tekrarlamamak
icin once OLCULUR, sonra uretilir.

⛔ KAPSAM: yalniz `train` (838 PID / 2.050 seri). `dev` ve `held_out`
   satirlarina DOKUNULMAZ.
⛔ KAPI YOKTUR (docs/39 revizyonu): TASK-17'de genel bir %5 kabul esigi
   tanimlanmadi; oradaki %4,0 -> %0,4 olcumu SABIT MALIGNITE BAGLAMLI evrene
   ozguydu. Burada kapsam BETIMLEYICI metrik olarak raporlanir.

METRIK — TASK-17 ile AYNI TANIM:
   sozluk boslugu = (malignite metin deseni eslesen cumlelerin,
                     yapilandirilmis malignite kavrami URETMEYEN orani)

Kullanim:
    python scripts/61_vlm14_train_aktarim_denetimi.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

import importlib.util  # noqa: E402

from radyovlm.evaluation import envanter as env  # noqa: E402
from radyovlm.evaluation import sema  # noqa: E402
from radyovlm.extraction import astra as A  # noqa: E402
from radyovlm.extraction import context as C  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

CUMLELER = KOK / "data/processed/astra_sentences.parquet"
CIKTI_VARLIK = KOK / "data/processed/astra_entities_train.parquet"
CIKTI_OLCUM = KOK / "reports/vlm14_aktarim_denetimi.json"
CIKTI_ILISKI = KOK / "data/processed/astra_relations_train.parquet"


def _olcu_modulu():
    """scripts/07'nin olcu ve TEKNIK desenlerini BIREBIR kullan."""
    yol = KOK / "scripts/07_extract_measurements.py"
    spec = importlib.util.spec_from_file_location("_olcu07", yol)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_olcu07"] = mod
    spec.loader.exec_module(mod)
    return mod

MAL_METIN = re.compile(env.MALIGNITE_METIN_DESENI, re.I)


def main() -> None:
    # Split filtresi OKUMA aninda - dev/held_out bellege alinmaz (R5.4).
    d = pd.read_parquet(CUMLELER, filters=[("split", "==", "train")])
    train = d[d["included_in_evaluation"]].copy()
    print(f"kapsam: train · {train['seri_anahtari'].nunique():,} seri "
          f"· {len(train):,} cumle  (dev/held_out OKUNMADI)")

    kavramlar, taraf_sozluk = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)
    ipuclari, sonlandirici = C.ipuclarini_kur()

    olcu07 = _olcu_modulu()

    satirlar: list[dict] = []
    iliskiler: list[dict] = []
    for r in train.itertuples(index=False):
        metin = r.cumle_metni
        varliklar = E.cumleden_varliklar(metin, matcher, indeks)
        if not varliklar:
            continue
        # ⚠ Bu iki fonksiyon YERINDE DEGISTIRMEZ, YENI LISTE DONDURUR.
        # Donus degeri yok sayilirsa assertion/temporality SESSIZCE null kalir
        # ve negasyon hic uygulanmamis olur. Bu hata bir kez yapildi.
        varliklar = C.kesinlik_ata(metin, varliklar, ipuclari, sonlandirici)
        varliklar = C.zaman_ata(metin, varliklar, ipuclari, sonlandirici)

        # Varlik kimligi ILISKI kurulmadan ONCE atanir - iliski satirlari
        # kimlige referans verir.
        # ⚠ enumerate ile - list.index() esit sozlukleri karistirabilir.
        for i, v in enumerate(varliklar):
            v["_eid"] = f"astra-{len(satirlar) + i:08d}"

        # --- Olculer: TEKNIK olanlar DISLANIR (docs/39 §7) ---
        olculer = []
        for m in olcu07.OLCU.finditer(metin):
            if A.olcu_teknik_mi(metin, m.start(), m.end()):   # TEK KAYNAK (K5.1)
                continue
            olculer.append({"bas": m.start(), "son": m.end(),
                            "metin": m.group(0), "kavram": None})

        rel, _ = E.iliskileri_kur(varliklar, olculer, metin)
        for x in rel:
            bas = x["head"]
            kuy = x["tail"]
            iliskiler.append({
                "seri_anahtari": r.seri_anahtari,
                "bolum_ham": r.bolum_ham,
                "cumle_idx": r.cumle_idx,
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
                "seri_anahtari": r.seri_anahtari,
                "pid": r.pid,
                "bolum_ham": r.bolum_ham,
                "bolum_eslenmis": r.bolum_eslenmis,
                "kapsam_ici": r.kapsam_ici,
                "cumle_idx": r.cumle_idx,
                "normalized_concept": kav.ad,
                "entity_type": kav.tip,
                "raw_text": v["metin"],
                "char_start": v["bas"],
                "char_end": v["son"],
                "assertion": v.get("assertion"),
                "assertion_rule": v.get("assertion_rule"),
                "assertion_cue": v.get("assertion_cue"),
                "temporality": v.get("temporality"),
                "cumle_metni": metin,
            })

    varlik = pd.DataFrame(satirlar)
    CIKTI_VARLIK.parent.mkdir(parents=True, exist_ok=True)
    varlik.to_parquet(CIKTI_VARLIK, index=False)

    iliski = pd.DataFrame(iliskiler)
    iliski.to_parquet(CIKTI_ILISKI, index=False)

    # --- Sozluk boslugu · TASK-17 ile AYNI TANIM --------------------------
    train["mal_metin"] = train["cumle_metni"].map(lambda x: bool(MAL_METIN.search(x)))
    evren = train[train["mal_metin"]]

    anahtar = ["seri_anahtari", "bolum_ham", "cumle_idx"]
    mal_kavram = varlik[varlik["normalized_concept"].isin(sema.MALIGNITE_KAVRAMLARI)]
    uretenler = set(map(tuple, mal_kavram[anahtar].drop_duplicates().values))
    evren_anahtar = list(map(tuple, evren[anahtar].values))
    bosta = [a for a in evren_anahtar if a not in uretenler]

    bosluk_yuzde = round(100 * len(bosta) / max(len(evren_anahtar), 1), 2)

    # Kapsanmayan cumlelerden en sik yuzeyler
    bosta_kume = set(bosta)
    ornekler = evren[[tuple(x) in bosta_kume for x in evren[anahtar].values]]
    yuzey = Counter()
    for t in ornekler["cumle_metni"]:
        for m in MAL_METIN.finditer(t):
            yuzey[m.group(0).lower()] += 1

    olcum = {
        "gorev": "SUDE-VLM-14 · Adim 2",
        "kapsam": "yalniz train; dev ve held_out okunmadi",
        "kapi": "YOK - betimleyici olcum (docs/39 revizyonu)",
        "metrik_tanimi": ("malignite metin deseni eslesen cumlelerin, "
                          "yapilandirilmis malignite kavrami uretmeyen orani "
                          "(TASK-17 ile ayni tanim)"),
        "metin_deseni": env.MALIGNITE_METIN_DESENI,
        "train_seri": int(train["seri_anahtari"].nunique()),
        "train_cumle": int(len(train)),
        "uretilen_varlik": int(len(varlik)),
        "varlik_ureten_cumle": int(varlik[anahtar].drop_duplicates().shape[0]),
        "malignite_baglamli_cumle": int(len(evren_anahtar)),
        "kavram_uretmeyen_cumle": int(len(bosta)),
        "sozluk_boslugu_yuzde": bosluk_yuzde,
        "task17_ct_rate_boslugu_yuzde": 0.4,
        "kapsanmayan_yuzeyler": dict(yuzey.most_common(20)),
        "kova_bazinda_varlik": varlik["bolum_eslenmis"].value_counts().to_dict(),
        "en_sik_kavram": varlik["normalized_concept"].value_counts().head(20).to_dict(),
        "assertion_dagilimi": varlik["assertion"].value_counts(dropna=False).to_dict(),
        "iliski_satiri": int(len(iliski)),
        "iliski_tipleri": (iliski["relation_type"].value_counts().to_dict()
                           if len(iliski) else {}),
        "measured_by_L1": int((iliski["relation_type"].eq("measured_by")).sum())
                          if len(iliski) else 0,
    }
    CIKTI_OLCUM.parent.mkdir(parents=True, exist_ok=True)
    CIKTI_OLCUM.write_text(json.dumps(olcum, ensure_ascii=False, indent=1),
                           encoding="utf-8")

    print(f"\nuretilen varlik          : {olcum['uretilen_varlik']:,}")
    print(f"malignite baglamli cumle : {olcum['malignite_baglamli_cumle']:,}")
    print(f"kavram uretmeyen         : {olcum['kavram_uretmeyen_cumle']:,}")
    print(f"SOZLUK BOSLUGU           : %{bosluk_yuzde}"
          f"   (CT-RATE'te %0,4)")
    if yuzey:
        print("\nkapsanmayan yuzeyler (ilk 10):")
        for y, n in yuzey.most_common(10):
            print(f"   {n:6,}  {y}")
    print(f"\nyazildi: {CIKTI_VARLIK.relative_to(KOK)} · "
          f"{CIKTI_OLCUM.relative_to(KOK)}")


if __name__ == "__main__":
    main()
