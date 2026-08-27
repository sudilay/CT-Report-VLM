# -*- coding: utf-8 -*-
"""TASK-12 / B0: Ayar ve degerlendirme ornekleminin cikarilmasi (D26).

NEDEN AYRI IKI KUME:
  Kurallar bir orneklege bakilarak duzeltilip AYNI orneklem uzerinde basarim
  bildirilirse, bildirilen sayi o orneklere uydurulmus olur. Faz 1'de sablon
  esigini (K=10) train orneklerine bakarak sectik; oradaki "100/100" bir
  GELISTIRME GOZLEMIDIR, bagimsiz basarim olcumu degil.

NEDEN TEST VALID'DEN:
  Sozluk madenciligi (terim_madeni.py) ve her 'korpus' sayisi TUM train
  cumleleri uzerinde yapildi. Dolayisiyla ayirip kenara koydugumuz bir train
  hastasi bile sozluge katkida bulunmustur; onun uzerinde olculen basarim
  IYIMSERDIR. Valid sozluge hic katki vermedi.

KORUMALAR - ihlal varsa DOSYA YAZILMAZ:
  1. Ayrim HASTA duzeyinde (calisma duzeyinde degil)
  2. dev ∩ test hasta kesisimi bos olmali
  3. Bugune kadar incelenen orneklem dosyalarindaki hastalar ("yanmis liste")
     teste giremez
  4. dev yalnizca train'den, test yalnizca valid'den

Kullanim:
    .venv/Scripts/python.exe scripts/10_build_eval_split.py
    .venv/Scripts/python.exe scripts/10_build_eval_split.py --surum test-v2
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

TOHUM = 20260827
N_DEV = 150
N_TEST = 200

# Hedefli zor kume bilesimi - rastgele ile AYRI raporlanir (D26/6)
HEDEFLI = {
    "negasyon": 20, "belirsizlik": 20, "coklu_bulgu": 20,
    "onceki_tetkik": 20, "coklu_olcu": 20,
}


def yanmis_hastalar(reps: pd.DataFrame) -> tuple[set, pd.DataFrame]:
    """Bugune kadar incelenen tum orneklem dosyalarindaki hastalar.

    Bu calismalara BAKILDI; uzerlerinde kural gelistirildi. Degerlendirme
    kumesine giremezler.
    """
    calisma_hasta = dict(zip(reps.study_id, reps.patient_id))
    kayitlar = []
    for f in sorted(REPORTS.glob("*.csv")):
        try:
            d = pd.read_csv(f, encoding="utf-8-sig")
        except Exception:
            continue
        if "study_id" not in d.columns:
            continue
        for s in d.study_id.dropna().astype(str).unique():
            if s in calisma_hasta:
                kayitlar.append({"kaynak": f.name, "study_id": s,
                                 "patient_id": calisma_hasta[s]})
    df = pd.DataFrame(kayitlar)
    return (set(df.patient_id) if len(df) else set()), df


def hedefli_maske(sent: pd.DataFrame, ent: pd.DataFrame,
                  meas: pd.DataFrame) -> dict:
    """Zor vaka gruplarinin cumle anahtarlari."""
    a = ["study_id", "section", "sent_idx"]
    anahtar = set(map(tuple, sent[a].values))

    neg = set(map(tuple, sent.loc[sent.text.str.contains(
        r"\bno\b|\bnot\b|\bwithout\b", case=False, regex=True), a].values))
    bel = set(map(tuple, sent.loc[sent.text.str.contains(
        r"\?|in favor of|suspicious|compatible with|consistent with|"
        r"cannot be excluded|thought to be", case=False, regex=True), a].values))
    onc = set(map(tuple, sent.loc[sent.text.str.contains(
        r"previous|control|follow-?up|stable|newly|current examination",
        case=False, regex=True), a].values))

    goz = ent[ent.entity_type == "observation"].groupby(a).size()
    cok_b = {k for k, v in goz.items() if v >= 2}
    cok_o = {k for k, v in meas.groupby(a).size().items() if v >= 2}

    return {"negasyon": neg & anahtar, "belirsizlik": bel & anahtar,
            "onceki_tetkik": onc & anahtar, "coklu_bulgu": cok_b & anahtar,
            "coklu_olcu": cok_o & anahtar}


def sec(havuz: set, n: int, tohum: int) -> list:
    s = pd.Series(sorted(havuz))
    return list(s.sample(min(n, len(s)), random_state=tohum))


def kume_kur(sent: pd.DataFrame, ent: pd.DataFrame, meas: pd.DataFrame,
             hastalar: set, n_rastgele: int, tohum: int, etiket: str) -> pd.DataFrame:
    a = ["study_id", "section", "sent_idx"]
    alt = sent[sent.patient_id.isin(hastalar)]
    gruplar = hedefli_maske(alt, ent, meas)
    havuz = set(map(tuple, alt[a].values))

    secilen, satir = set(), []
    for grup, n in HEDEFLI.items():
        aday = gruplar[grup] - secilen
        for k in sec(aday, n, tohum + hash(grup) % 1000):
            secilen.add(k)
            satir.append({"kume": etiket, "grup": grup, "tur": "hedefli", **dict(zip(a, k))})
    for k in sec(havuz - secilen, n_rastgele, tohum):
        secilen.add(k)
        satir.append({"kume": etiket, "grup": "rastgele", "tur": "rastgele", **dict(zip(a, k))})
    return pd.DataFrame(satir)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surum", default="test-v1",
                    help="degerlendirme kumesi surumu; teste bakip kural "
                         "degistirildiyse test-v2 cekilir (D26/5)")
    args = ap.parse_args()

    sent = pd.read_parquet(PROC / "sentences.parquet")
    ent = pd.read_parquet(PROC / "entities.parquet")
    meas = pd.read_parquet(PROC / "measurements.parquet")
    reps = pd.read_parquet(PROC / "reports_study_level.parquet",
                           columns=["study_id", "patient_id", "split"])
    sent = sent.merge(reps, on="study_id", how="left")

    yanmis, yanmis_df = yanmis_hastalar(reps)
    print(f"yanmis (incelenmis) hasta : {len(yanmis):,}  "
          f"[{yanmis_df.kaynak.nunique() if len(yanmis_df) else 0} dosyadan]")

    train_h = set(reps.loc[reps.split == "train", "patient_id"])
    valid_h = set(reps.loc[reps.split == "valid", "patient_id"])
    dev_h = train_h - yanmis
    test_h = valid_h - yanmis
    print(f"dev havuzu  (train - yanmis) : {len(dev_h):,} hasta")
    print(f"test havuzu (valid - yanmis) : {len(test_h):,} hasta "
          f"(yanmis olan {len(valid_h & yanmis)} valid hastasi cikarildi)")

    dev = kume_kur(sent, ent, meas, dev_h, N_DEV - sum(HEDEFLI.values()),
                   TOHUM, "ayar")
    test = kume_kur(sent, ent, meas, test_h, N_TEST - sum(HEDEFLI.values()),
                    TOHUM + 7, args.surum)

    # ---------------- KORUMALAR ----------------
    h = dict(zip(reps.study_id, reps.patient_id))
    s_ = dict(zip(reps.study_id, reps.split))
    dev_p = {h[x] for x in dev.study_id}
    test_p = {h[x] for x in test.study_id}
    ihlal = []
    if dev_p & test_p:
        ihlal.append(f"dev ∩ test hasta kesisimi: {len(dev_p & test_p)}")
    if test_p & yanmis:
        ihlal.append(f"yanmis hasta teste sizmis: {len(test_p & yanmis)}")
    kotu_dev = {x for x in dev.study_id if s_[x] != "train"}
    if kotu_dev:
        ihlal.append(f"dev'de train disi calisma: {len(kotu_dev)}")
    kotu_test = {x for x in test.study_id if s_[x] != "valid"}
    if kotu_test:
        ihlal.append(f"test'te valid disi calisma: {len(kotu_test)}")
    if ihlal:
        raise SystemExit("ORNEKLEM KORUMASI BASARISIZ - dosya yazilmadi:\n  "
                         + "\n  ".join(ihlal))
    print("\nkorumalar gecti: hasta kesisimi yok · yanmis sizinti yok · "
          "dev=train · test=valid")

    # ---------------- YAZ ----------------
    for df, ad in ((dev, "task12_ayar"), (test, f"task12_{args.surum}")):
        df = df.merge(sent[["study_id", "section", "sent_idx", "text"]],
                      on=["study_id", "section", "sent_idx"], how="left")
        for k in ("assertion_dogru", "temporality_dogru", "change_type_dogru", "not"):
            df[k] = ""
        df.to_csv(PROC / f"{ad}.csv", index=False, encoding="utf-8-sig")
        print(f"  yazildi: data/processed/{ad}.csv  ({len(df)} cumle, "
              f"{df.study_id.map(h).nunique()} hasta)")
        print(f"           {df.grup.value_counts().to_dict()}")

    yanmis_df.to_csv(PROC / "incelenmis_hastalar.csv", index=False,
                     encoding="utf-8-sig")
    # Faz 3'e borc: test valid hastasi tuketiyor, TASK-18 bilsin
    pd.DataFrame({"patient_id": sorted(test_p), "tuketen": args.surum}).to_csv(
        PROC / "tuketilen_valid_hastalar.csv", index=False, encoding="utf-8-sig")
    print(f"  yazildi: incelenmis_hastalar.csv ({len(yanmis_df)} kayit)")
    print(f"  yazildi: tuketilen_valid_hastalar.csv ({len(test_p)} hasta) "
          "-> TASK-18 bunlari hesaba katmali")

    print("\nUYARI: test kumesi kurallar DONDUKTAN SONRA bir kez acilir (D26).")
    print("       Teste bakip kural degistirilirse bu surum IPTAL edilir ve")
    print("       --surum test-v2 ile yenisi cekilir; eski skor raporda gecersiz yazar.")


if __name__ == "__main__":
    main()
