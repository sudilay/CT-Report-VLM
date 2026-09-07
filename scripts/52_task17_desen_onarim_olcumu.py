"""TASK-17 Madde 1 - `scripts/42` TARAMA DESENLERININ ONARIM OLCUMU.

Plan: docs/34_task17_calisma_plani.md v2 §3.1 · madde 1

NEDEN: docs/34 §3.1 olctu ki devir notunun "sozluk duzeltilecek" dedigi uc
kalem aslinda URETIM SOZLUGUNDE degil, `scripts/42`nin TARAMA DESENINDE.
Uretim sozlugu (`configs/ipucu_sozlugu.yaml`) dogrudur; tarayici ondan
sapmistir. Bu D60'in ("olcum once alete uygulanir") uygulamasidir.

BU BETIK KARAR VERMEZ, OLCER. Her iddia icin:
  - eski desenin kac cumle yakaladigi
  - bunlarin kaci HATALI (ve neden)
  - onerilen yeni desenin kac cumle yakaladigi
  - farkin icinden ORNEK CUMLELER (elle bakilsin diye)

KAPSAM: yalniz GELISTIRME HAVUZU. Degerlendirme kilidi okunmaz.

Kullanim:
    .venv/Scripts/python.exe scripts/52_task17_desen_onarim_olcumu.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task17_desen_onarim_olcumu.json"

ORNEK_SAYISI = 8
TOHUM = 20260904

# ═══════════════════════════════════════════════════════════════════
# ESKI DESENLER - scripts/42 satir 42-46, bugunku hali
# ═══════════════════════════════════════════════════════════════════
ESKI = {
    "belirsizlik": r"cannot be excluded|can not be excluded|suspicious|probabl|possibl|may represent|in favor of",
    "buyume": r"increas|enlarg|growth|\bgrew\b|\bnew\b|progress",
    "stabilite": r"\bstable\b|unchanged|no change|no significant (?:difference|change)",
    "negasyon": r"\bno\b|\bnot\b|without|absent|negative for",
}

# ═══════════════════════════════════════════════════════════════════
# ONERILEN YENI DESENLER - hepsi `configs/ipucu_sozlugu.yaml`e HIZALI
# ═══════════════════════════════════════════════════════════════════
#
# belirsizlik: uretim sozlugunun GERCEK belirsizlik siniflari
#   belirsizlik_oncelikli.cannot_be_excluded + belirsizlik.{parantez_soru,
#   ayirici_tani}. `suspicious`, `possibl`, `probabl`, `may represent`,
#   `in favor of` uretimde `cikarim_ifadesi` ALTINDADIR -> `present`.
YENI_BELIRSIZLIK = (
    r"can ?not be excluded|can ?not be ruled out|cannot be definitively excluded"
    r"|differential diagnos[ei]s|\bdifferential\b"
    r"|\([^)]{1,60}\?\)"
)

# buyume: LEZYON BUYUMESI - bulgu betimlemesi degil.
#   Uretimdeki `degisim.artmis` (increas|enlarg|progress, 39.520) COK GENIS;
#   o bir CUE kaydidir, karar sinifi degil. Burada gereken: bir lezyonun
#   BUYUDUGUNU soyleyen cumle. Uc yol kabul edilir:
#     (a) acik boyut artisi ifadesi
#     (b) yeni ortaya cikma (uretim `degisim.yeni`)
#     (c) ilerleme (progresyon)
YENI_BUYUME = (
    r"increase[d]? in size|increase in (?:the )?(?:size|dimension)"
    r"|size (?:has |had )?increased|enlarg\w* in size"
    r"|\bgrew\b|\bgrowth\b|growing"
    r"|newly (?:developed|appeared|emerged|detected)|\bnewly\b"
    r"|not (?:present|observed) in the previous"
    r"|progression|progressed"
)

# negasyon: SAHTE NEGASYONU disla.
#   `configs/ipucu_sozlugu.yaml` -> sahte_negasyon.degisim_yok:
#     ["no significant change","no interval change","no change","no significant difference"]
#   Bunlar bir bulguyu OLUMSUZLAMAZ, STABILITE bildirir. Eski desende
#   `\bno\b` bunlari da yakaliyordu -> stabilite ∩ negasyon SAHTE kesisim.
_SAHTE = r"(?!\s+(?:significant\s+(?:change|difference)|interval\s+change|change\b))"
YENI_NEGASYON = (
    rf"\bno\b{_SAHTE}"
    r"|\bnot\b|without|\babsent\b|absence of|negative for"
)

# stabilite: DEGISMIYOR - uretimdeki `degisim.stabil` ile hizalandi.
YENI_STABILITE = (
    r"\bstable\b|\bunchanged\b|no significant change|no interval change"
    r"|no change\b|no significant difference|similar to (?:the )?previous"
)

YENI = {
    "belirsizlik": YENI_BELIRSIZLIK,
    "buyume": YENI_BUYUME,
    "stabilite": YENI_STABILITE,
    "negasyon": YENI_NEGASYON,
}

# ═══════════════════════════════════════════════════════════════════
# IDDIA TESTLERI - eski desendeki her hatali parcayi AYRI olc
# ═══════════════════════════════════════════════════════════════════
# Her satir: (sinif, parca_adi, desen, uretimdeki_yeri, hatali_mi)
PARCA_TESTLERI = [
    ("belirsizlik", "cannot_be_excluded", r"can ?not be excluded",
     "belirsizlik_oncelikli.cannot_be_excluded", False),
    ("belirsizlik", "suspicious", r"suspicious",
     "cikarim_ifadesi.supheli -> present", True),
    ("belirsizlik", "probabl", r"probabl",
     "cikarim_ifadesi.olasilik -> present", True),
    ("belirsizlik", "possibl", r"possibl",
     "cikarim_ifadesi.olasilik -> present", True),
    ("belirsizlik", "may_represent", r"may represent",
     "cikarim_ifadesi.dusunuldu -> present", True),
    ("belirsizlik", "in_favor_of", r"in favor of",
     "cikarim_ifadesi.lehine -> present (D29)", True),
]

# `buyume`nin bilinen yanlis basliklari (docs/31 §2, D72)
BUYUME_YANLIS_BASLIK = (
    r"(?:density|densit\w+|thickness|attenuation|opacity|calibration|"
    r"diameter of the|caliber)\s+(?:increase|increment)"
    r"|increase in (?:density|thickness|attenuation|opacity|calibration)"
)
# `enlarged lymph node` - statik boyut bildirimi, buyume DEGIL (AGENTS.md)
BUYUME_STATIK_LAP = r"enlarged lymph node"

# ORGAN boyutu artisi lezyon buyumesi DEGILDIR (kardiyomegali/splenomegali).
# scripts/42 HARIC["buyume"] ile birebir ayni desen - ikisi ayrisirsa olcum
# gonderilen desenle uyusmaz.
BUYUME_HARIC_ORGAN = (
    r"(?:heart|cardiac|spleen|liver|hepatic|thyroid|kidney|renal"
    r"|adrenal|prostate|uter\w+|aort\w*)\s+(?:size|dimension)"
    r"|(?:size|dimension)s?\s+of\s+the\s+(?:heart|spleen|liver|thyroid|kidney)"
)


def _ornekler(seri: pd.Series, maske: pd.Series, n: int = ORNEK_SAYISI) -> list[str]:
    """Maskeye uyan cumlelerden sabit tohumlu ornek."""
    havuz = seri[maske]
    if havuz.empty:
        return []
    k = min(n, len(havuz))
    return [t[:220] for t in havuz.sample(k, random_state=TOHUM).tolist()]


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    # --- kapsam: yalniz gelistirme havuzu (scripts/42 ile AYNI yordam) ---
    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])

    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    s = pd.read_parquet(CUMLELER, columns=["study_id", "text"])
    s = s[s["study_id"].isin(gelistirme)]
    metin = s["text"].fillna("")
    n_top = len(s)

    print(f"kapsam: gelistirme havuzu · {n_top:,} cumle / "
          f"{s['study_id'].nunique():,} calisma  (kilit OKUNMADI)")
    print(f"kilit surumu: {kilit['surum']}\n")

    rapor: dict = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "taranan_cumle": int(n_top),
        "taranan_calisma": int(s["study_id"].nunique()),
        "ornek_tohumu": TOHUM,
    }

    def es(desen: str) -> pd.Series:
        return metin.str.contains(desen, case=False, regex=True, na=False)

    # ═══ 1 · BELIRSIZLIK - parca parca ═══
    print("=" * 72)
    print("1 · BELIRSIZLIK DESENI - hangi parca hatali?")
    print("=" * 72)
    eski_b = es(ESKI["belirsizlik"])
    print(f"  ESKI desen toplam: {int(eski_b.sum()):>7,} cumle\n")
    parcalar = []
    for sinif, ad, dsn, yer, hatali in PARCA_TESTLERI:
        if sinif != "belirsizlik":
            continue
        m = es(dsn) & eski_b
        n = int(m.sum())
        isaret = "HATALI" if hatali else "dogru "
        print(f"  [{isaret}] {ad:20} {n:>7,} cumle   ({yer})")
        parcalar.append({"parca": ad, "desen": dsn, "cumle": n,
                         "uretimdeki_yeri": yer, "hatali": hatali,
                         "ornekler": _ornekler(metin, m, 3)})
    hatali_m = es("|".join(d for si, _, d, _, h in PARCA_TESTLERI
                           if si == "belirsizlik" and h)) & eski_b
    dogru_m = es(r"can ?not be excluded") & eski_b
    print(f"\n  -> HATALI parcalarin yakaladigi : {int(hatali_m.sum()):>7,} "
          f"(%{int(hatali_m.sum())/max(int(eski_b.sum()),1)*100:.1f})")
    print(f"  -> gercek belirsizlik (cannot be excluded): {int(dogru_m.sum()):>7,}")

    yeni_b = es(YENI["belirsizlik"])
    print(f"\n  YENI desen toplam: {int(yeni_b.sum()):>7,} cumle")
    print(f"  (uretim sozlugune hizali: cannot_be_excluded + ayirici_tani + parantez_soru)")
    print("\n  YENI'nin yakalayip ESKI'nin kacirdigi ornekler:")
    for t in _ornekler(metin, yeni_b & ~eski_b, 4):
        print(f"    · {t}")
    print("\n  ESKI'nin yakalayip YENI'nin ATTIGI ornekler (hatali olmali):")
    for t in _ornekler(metin, eski_b & ~yeni_b, 4):
        print(f"    · {t}")

    rapor["belirsizlik"] = {
        "eski_desen": ESKI["belirsizlik"], "yeni_desen": YENI["belirsizlik"],
        "eski_cumle": int(eski_b.sum()), "yeni_cumle": int(yeni_b.sum()),
        "hatali_parcalarin_yakaladigi": int(hatali_m.sum()),
        "gercek_belirsizlik": int(dogru_m.sum()),
        "parcalar": parcalar,
        "yeni_ekledigi_ornek": _ornekler(metin, yeni_b & ~eski_b, ORNEK_SAYISI),
        "yeni_attigi_ornek": _ornekler(metin, eski_b & ~yeni_b, ORNEK_SAYISI),
    }

    # ═══ 2 · BUYUME ═══
    print("\n" + "=" * 72)
    print("2 · BUYUME DESENI - lezyon buyumesi mi, bulgu betimlemesi mi?")
    print("=" * 72)
    eski_g = es(ESKI["buyume"])
    yanlis_baslik = es(BUYUME_YANLIS_BASLIK) & eski_g
    statik_lap = es(BUYUME_STATIK_LAP) & eski_g
    print(f"  ESKI desen toplam            : {int(eski_g.sum()):>7,} cumle")
    print(f"    bunlarin 'density/thickness increase' olani : {int(yanlis_baslik.sum()):>7,}")
    print(f"    bunlarin 'enlarged lymph node' olani        : {int(statik_lap.sum()):>7,}")
    print("\n  'density/thickness increase' ornekleri (buyume DEGIL):")
    for t in _ornekler(metin, yanlis_baslik, 4):
        print(f"    · {t}")

    # Dislamanin MALIYETI: kac organ cumlesi baska bir buyume tetikleyicisi
    # de tasiyor? Buyukse dislama gercek buyume kaybettiriyor demektir.
    DIGER_TETIK = (r"\bgrew\b|\bgrowth\b|growing"
                   r"|newly (?:developed|appeared|emerged|detected)|\bnewly\b"
                   r"|not (?:present|observed) in the previous|progression|progressed")
    yeni_g_ham = es(YENI["buyume"])
    organ = es(BUYUME_HARIC_ORGAN)
    yeni_g = yeni_g_ham & ~organ
    dislama_maliyeti = int((organ & es(DIGER_TETIK)).sum())
    print(f"\n  YENI desen (dislama ONCESI)  : {int(yeni_g_ham.sum()):>7,} cumle")
    print(f"    bunlarin ORGAN boyutu olani : {int((yeni_g_ham & organ).sum()):>7,}  <- HARIC")
    print(f"    dislama maliyeti            : {dislama_maliyeti:>7,} cumle "
          f"(organ cumlesi olup BASKA buyume tetikleyicisi de tasiyan)")
    print(f"  YENI desen toplam            : {int(yeni_g.sum()):>7,} cumle")
    print(f"    hala 'density/thickness' iceren : {int((yeni_g & es(BUYUME_YANLIS_BASLIK)).sum()):>7,}")
    print(f"    hala 'enlarged lymph node'      : {int((yeni_g & es(BUYUME_STATIK_LAP)).sum()):>7,}")
    print("\n  YENI'nin tuttugu ornekler (gercek buyume olmali):")
    for t in _ornekler(metin, yeni_g, 6):
        print(f"    · {t}")
    print("\n  ESKI'nin tutup YENI'nin ATTIGI ornekler:")
    for t in _ornekler(metin, eski_g & ~yeni_g, 5):
        print(f"    · {t}")

    rapor["buyume"] = {
        "eski_desen": ESKI["buyume"], "yeni_desen": YENI["buyume"],
        "yeni_dislama_desen": BUYUME_HARIC_ORGAN,
        "eski_cumle": int(eski_g.sum()),
        "yeni_cumle_dislama_oncesi": int(yeni_g_ham.sum()),
        "yeni_cumle": int(yeni_g.sum()),
        "dislanan_organ_cumlesi": int((yeni_g_ham & organ).sum()),
        "dislama_maliyeti_cumle": dislama_maliyeti,
        "eski_icinde_density_thickness": int(yanlis_baslik.sum()),
        "eski_icinde_enlarged_lymph_node": int(statik_lap.sum()),
        "yeni_icinde_density_thickness": int((yeni_g & es(BUYUME_YANLIS_BASLIK)).sum()),
        "yeni_icinde_enlarged_lymph_node": int((yeni_g & es(BUYUME_STATIK_LAP)).sum()),
        "yeni_tuttugu_ornek": _ornekler(metin, yeni_g, ORNEK_SAYISI),
        "yeni_attigi_ornek": _ornekler(metin, eski_g & ~yeni_g, ORNEK_SAYISI),
    }

    # ═══ 3 · STABILITE ∩ NEGASYON SAHTE KESISIMI ═══
    print("\n" + "=" * 72)
    print("3 · STABILITE ∩ NEGASYON - sahte kesisim")
    print("=" * 72)
    eski_st, eski_ng = es(ESKI["stabilite"]), es(ESKI["negasyon"])
    eski_kesisim = eski_st & eski_ng
    sahte = es(r"no (?:significant )?(?:change|difference)|no interval change") & eski_kesisim
    print(f"  ESKI kesisim (stabilite & negasyon): {int(eski_kesisim.sum()):>7,} cumle")
    print(f"    bunlarin 'no change/difference' olani: {int(sahte.sum()):>7,}  <- SAHTE")
    print("\n  sahte kesisim ornekleri:")
    for t in _ornekler(metin, sahte, 4):
        print(f"    · {t}")

    yeni_st, yeni_ng = es(YENI["stabilite"]), es(YENI["negasyon"])
    yeni_kesisim = yeni_st & yeni_ng
    print(f"\n  YENI stabilite : {int(yeni_st.sum()):>7,} cumle")
    print(f"  YENI negasyon  : {int(yeni_ng.sum()):>7,} cumle")
    print(f"  YENI kesisim   : {int(yeni_kesisim.sum()):>7,} cumle "
          f"(eski {int(eski_kesisim.sum()):,} -> fark {int(eski_kesisim.sum())-int(yeni_kesisim.sum()):+,})")
    print("\n  YENI kesisimde KALAN ornekler (gercek kesisim olmali):")
    for t in _ornekler(metin, yeni_kesisim, 5):
        print(f"    · {t}")

    rapor["stabilite_negasyon"] = {
        "eski_stabilite_desen": ESKI["stabilite"], "yeni_stabilite_desen": YENI["stabilite"],
        "eski_negasyon_desen": ESKI["negasyon"], "yeni_negasyon_desen": YENI["negasyon"],
        "eski_stabilite_cumle": int(eski_st.sum()), "yeni_stabilite_cumle": int(yeni_st.sum()),
        "eski_negasyon_cumle": int(eski_ng.sum()), "yeni_negasyon_cumle": int(yeni_ng.sum()),
        "eski_kesisim": int(eski_kesisim.sum()), "yeni_kesisim": int(yeni_kesisim.sum()),
        "sahte_kesisim": int(sahte.sum()),
        "sahte_ornek": _ornekler(metin, sahte, ORNEK_SAYISI),
        "yeni_kesisimde_kalan_ornek": _ornekler(metin, yeni_kesisim, ORNEK_SAYISI),
    }

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    print("\n⚠ BU BETIK KARAR VERMEZ. Ornekler elle incelenip desenler "
          "onaylandiktan SONRA scripts/42 guncellenir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
