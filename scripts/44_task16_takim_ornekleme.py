"""TASK-16 Adim 4 - SINIR VAKASI ve NEGATIF KONTROL TAKIMLARININ ORNEKLENMESI.

Plan: docs/29 §8.1 ve §8.3

NEDEN BU SIRA: takimlar KURALLAR YAZILMADAN ONCE secilir ve kilitlenir. Vakalari
da kurallari da ayni anda yazarsak kabul olcutu kendiliginden saglanir ve hicbir
sey olcmez (docs/32 bulgu #3).

ORNEKLEME ILAN EDILMIS YORDAMLA yapilir: sabit tohum + populasyon basina kota.
"Zor gorunen cumleyi elle sec" YASAKTIR - o, sinavi kendi kurallarimiza gore
sekillendirmek olurdu.

KAPSAM:
  - yalniz GELISTIRME havuzu (configs/splits_holdout.json)
  - adim 0'da maruziyet kaydi olan 17 hasta HARIC (docs/29 §4.4 baglayici kurali)
  - sablon cumleler HARIC (hasta bilgisi tasimayan kopyala-yapistir metinler,
    sistemin zorlandigi yeri gostermez)

CIKTI: hedef sinif sutunlari BOS birakilir. Hedefler ayri ve gorunur bir adimda
atanir, sonra hash'lenip kilitlenir.

Kullanim:
    python scripts/44_task16_takim_ornekleme.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
MARUZIYET = KOK / "reports/task16_maruziyet_kaydi.json"
CIKTI_SINIR = KOK / "data/processed/sema_sinir_vakalari.csv"
CIKTI_KONTROL = KOK / "data/processed/sema_negatif_kontrol.csv"

TOHUM = 20260904   # adim 4 icin ilan edilir; adim 0'in tohumundan farkli

# ⚠⚠ TASK-17 madde 3 (D79) - BU DESEN BILEREK GUNCELLENMEDI.
# Bu betik `configs/sema_takim_kilidi.json` (takim-1.1) ornegini uretti ve
# o kilit DONDURULMUSTUR. Desen genisletilirse betik kilidi YENIDEN
# URETEMEZ hale gelir - dondurulmus bir artefaktin izlenebilirligi kirilir.
# Olculdu (2026-09-07): dogru/genis desen (`tumor`) bunun UST KUMESI ve
# fark 68 cumle / 56 calisma. Yani o 56 calisma ORNEKLEMEYE HIC GORUNMEDI.
# Kilit kurali geregi (docs/33 §7) kilit ACILMAZ; fark ILAN EDILIR (D75
# emsali). Duzeltilmis desen: env.MALIGNITE_METIN_DESENI.
M = env.MALIGNITE_METIN_DESENI_KILIT_ONCESI
BENIGN = r"sequela|granulom|benign|hamartom"
NEG = r"\bno\b|\bnot\b|without|absent|negative for"
BELIRSIZ = r"cannot be excluded|can not be excluded|suspicio|probabl|possibl|may represent"
ENF = r"pneumon|infect|covid|inflammat|tuberculo"
STABIL = r"\bstable\b|unchanged|no significant (?:difference|change)"
EKSTRA = r"\bliver\b|hepatic|adrenal|\bkidney\b|\brenal\b|\bspleen\b"
DERECE_YUKSEK = r"high(?:ly)? suspic|strongly suspic|highly suggestive"
CIKARIM = r"in favor of|compatible with|consistent with"

# --- SINIR VAKALARI: her populasyon bir C kararina ya da A kuralina bagli ---
# (kod, dayanak, kota, "iceren" desenler, "icermeyen" desenler)
SINIR = [
    ("C1-negasyon-kapsami", "C #1 · negasyonun kapsami", 3, [M, NEG], []),
    ("C4-derece-yuksek", "C #4 · derece kelimesi (yuksek)", 2, [M, DERECE_YUKSEK], []),
    ("C4-derece-orta", "C #4 · derece kelimesi (orta)", 2,
     [M, r"\bmay be\b|probabl|possibl"], [DERECE_YUKSEK]),
    ("C4-derece-dislanamaz", "C #4 · derece kelimesi (dislanamaz)", 2,
     [M, r"cannot be excluded|can not be excluded"], []),
    ("C5-stabil-malignite", "C #5 · stabil malignite", 3, [M, STABIL], []),
    ("C6-malignite-benign", "C #6 · malignite + benign", 3, [M, BENIGN], []),
    ("C11-olumsuz-belirsiz", "C #11 · olumsuzlanmis belirsizlik", 2, [NEG, BELIRSIZ], []),
    ("C12-benign-belirsiz", "C #12 · benign + belirsizlik", 3, [BENIGN, BELIRSIZ], [M]),
    ("C13-ekstratorasik", "C #13 · ekstratorasik malignite", 3, [M, EKSTRA], []),
    ("C16-malignite-enf", "C #16 · malignite + enfeksiyon", 3, [M, ENF], []),
    ("A8-cikarim-ifadesi", "A8 · cikarim ifadesi -> present", 2, [CIKARIM], [M, NEG]),
    ("A26-kalsifikasyon", "A26 · kalsifikasyon benign yapmaz", 2, [M, r"calcific"], []),
]

# --- NEGATIF/BENIGN KORUMA TAKIMI: sema bunlarda malignite URETMEYECEK ---
KONTROL = [
    ("K-olumsuz-kitle", "acikca olumsuzlanmis kitle/malignite", 4,
     [r"\bno\b|\bnot\b", r"mass|tumoral|malignan"], [r"metasta|carcinom", DERECE_YUKSEK]),
    ("K-sekel-benign", "sade sekel/benign bulgu, malignite terimi YOK", 4,
     [BENIGN], [M, BELIRSIZ]),
    ("K-enfeksiyon", "enfeksiyon/pnomoni, malignite terimi YOK", 3, [ENF], [M]),
    ("K-stabil-benign", "stabil benign bulgu, malignite terimi YOK", 2,
     [STABIL, BENIGN], [M]),
    ("K-teknik", "teknik kisitlilik ifadesi", 2,
     [r"could not be (?:evaluated|assessed)|not (?:be )?evaluated|technical|artifact"], [M]),
]


def sec(havuz, kod, dayanak, kota, iceren, haric, rnd):
    m = pd.Series(True, index=havuz.index)
    for d in iceren:
        m &= havuz["text"].str.contains(d, case=False, regex=True, na=False)
    for d in haric:
        m &= ~havuz["text"].str.contains(d, case=False, regex=True, na=False)
    alt = havuz[m]
    if alt.empty:
        print(f"  ! {kod:24} POPULASYON BOS")
        return []
    alt = alt.sort_values(["study_id", "text"]).reset_index(drop=True)
    k = min(kota, len(alt))
    idx = sorted(rnd.sample(range(len(alt)), k))
    print(f"  {kod:24} populasyon {len(alt):>6,} -> {k} vaka")
    return [{
        "vaka_id": f"{kod}-{i+1:02d}",
        "populasyon_kodu": kod,
        "dayanak": dayanak,
        "populasyon_buyuklugu": len(alt),
        "study_id": alt.at[j, "study_id"],
        "cumle": " ".join(str(alt.at[j, "text"]).split()),
        "hedef_sinif": "",
        "hedef_kaynagi": "",
        "hedef_gerekcesi": "",
    } for i, j in enumerate(idx)]


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT, MARUZIYET):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1
    for c in (CIKTI_SINIR, CIKTI_KONTROL):
        if c.exists():
            print(f"HATA: takim ZATEN VAR ve uzerine yazilmaz: {c.name}")
            print("      Kilitli takim degistirilemez (docs/29 §8.1/4).")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])

    mar = json.loads(MARUZIYET.read_text(encoding="utf-8"))
    maruz = {h for r in mar["kayitlar"] for h in r["kilitteki_hasta_listesi"]}

    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    disarida = kilitli | maruz
    gel_calisma = set(k.loc[~k["patient_id"].isin(disarida), "study_id"])

    s = pd.read_parquet(CUMLELER, columns=["study_id", "text", "is_stock_phrasing"])
    havuz = s[s["study_id"].isin(gel_calisma) & (~s["is_stock_phrasing"].fillna(False))]
    havuz = havuz.drop_duplicates(subset="text")
    print(f"ornekleme havuzu: {len(havuz):,} benzersiz ozgun cumle")
    print(f"  (gelistirme havuzu · sablon HARIC · maruz {len(maruz)} hasta HARIC)\n")

    rnd = random.Random(TOHUM)
    print("SINIR VAKALARI")
    sinir = [v for a in SINIR for v in sec(havuz, *a, rnd)]
    print("\nNEGATIF/BENIGN KORUMA TAKIMI")
    kontrol = [v for a in KONTROL for v in sec(havuz, *a, rnd)]

    pd.DataFrame(sinir).to_csv(CIKTI_SINIR, index=False, encoding="utf-8")
    pd.DataFrame(kontrol).to_csv(CIKTI_KONTROL, index=False, encoding="utf-8")
    print(f"\nSINIR   : {len(sinir)} vaka -> {CIKTI_SINIR.relative_to(KOK)}")
    print(f"KONTROL : {len(kontrol)} vaka -> {CIKTI_KONTROL.relative_to(KOK)}")
    print(f"tohum {TOHUM}\n\nHEDEF SINIFLAR BOS - ayri adimda atanip kilitlenecek.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
