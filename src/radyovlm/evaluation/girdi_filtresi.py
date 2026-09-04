"""TASK-16 Adim 5 - GIRDI KALITE FILTRESI.

Plan: docs/29_task16_calisma_plani.md §7

NEDEN VAR: semanin girdisi Faz 2'nin cikarim katmanidir ve o katmanin kusurlari
OLCULMUSTUR:

    K7 (zaman ekseni) F1 = %36,4  -> esigi GECEMEDI (test-v2, D39)
    `uncertain` duyarliligi %71 / %46
    sebep: D29 belirsizlik ipuclarini `cikarim_ifadesi` -> `present` yapmisti

RISK: sema "en yuksek supheli bulgu kazanir" (A25/A33) diye toplama yapar.
Cikarim katmani GECMIS bir bulguyu `present` verirse, toplama kurali raporu
haksiz yere maligniteye yukseltir - projenin ANA HEDEFININ TAM TERSI.

--------------------------------------------------------------------------
ADIM 5'TE OLCULEN - filtre tahminle degil bu sayilarla tasarlandi
(gelistirme havuzu, 957.503 varlik):

  temporality = "prior"                    4.746  (%0,50)
    -> bunlarin 4.557'si assertion=present
    -> o 4.557'nin 3.711'i (%81,4) IPUCUSUZ, yani `varsayilan_present`

  temporality_rule = "varsayilan_current"  %99,24
    -> zamansallik ekseni pratikte BILGI TASIMIYOR: "current" bir kanit degil,
       kanit YOKLUGUDUR

  assertion_rule = "varsayilan_present"    %80,33
    -> `present`in cogunlugu da ipucuyla degil VARSAYILANLA atanmis

  malignite-ilgili kavramlar (70.258 varlik):
    %65,8 ipucuyla atanmis (negasyon ipuclari bu kavramlarda cok caliskan)
    %34,2 = 24.017 varlik `varsayilan_present` - ipucu YOK
--------------------------------------------------------------------------

FILTRENIN YAPTIGI SEY: varliklari elemez, ETIKETLER. Dusuk guvenli varliklar
`dusuk_guven` kanalina dusulur ve rapor sinifini YUKSELTEMEZ; ama kayitta
kalirlar ve raporlanirlar. Bilgi atilmaz, agirligi sinirlanir.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

FILTRE_SURUMU = "girdi-filtresi-1.0"

# Malignite eksenine giren kavramlar. TASK-17'de sozluk daraltilinca yeniden
# turetilecek; simdilik 144'luk envanterin malignite-ilgili alt kumesi.
MALIGNITE_KAVRAMLARI: frozenset[str] = frozenset({
    "metastasis", "malignancy", "carcinoma", "tumor", "neoplasm", "mass",
    "nodule", "lytic_destructive_lesion", "space_occupying_lesion", "spiculated",
})

# Bir degerin IPUCUYLA mi VARSAYILANLA mi atandigini ayirt eden kurallar.
VARSAYILAN_KURALLAR: frozenset[str] = frozenset({
    "varsayilan_present", "varsayilan_current", "varsayilan_absent",
})


@dataclass(frozen=True)
class FiltreKurali:
    """Tek bir dusuk-guven kurali; her biri olculmus bir kusura dayanir."""

    kod: str
    aciklama: str
    dayanak: str


KURALLAR: tuple[FiltreKurali, ...] = (
    FiltreKurali(
        kod="F1_gecmis_bulgu",
        aciklama="temporality = 'prior' olan her varlik dusuk guvenlidir.",
        dayanak=(
            "K7 (zaman ekseni) F1 %36,4 ile esigi GECEMEDI (D39). Ayrica "
            "temporality_rule'un %99,24'u 'varsayilan_current' - eksen pratikte "
            "bilgi tasimiyor. Gecmis bir bulgunun rapor sinifini yukseltmesi, "
            "olculmus bir hatanin sonuca tasinmasi olurdu."
        ),
    ),
    FiltreKurali(
        kod="F2_kanitsiz_present",
        aciklama=(
            "Malignite eksenindeki bir kavram `present` ama assertion_rule "
            "'varsayilan_present' ise (yani hicbir ipucu bulunmamissa) dusuk "
            "guvenlidir."
        ),
        dayanak=(
            "`present`in %80,33'u varsayilanla atanmis. `uncertain` duyarliligi "
            "%71/%46 - yani gercekte belirsiz olan bulgularin onemli bir kismi "
            "`present` etiketlenmis (D29). Ipucu bulunmamis bir `present`, "
            "kanit degil kanit YOKLUGUDUR ve tek basina yuksek suphe uretemez."
        ),
    ),
)


def uygula(varliklar: pd.DataFrame) -> pd.DataFrame:
    """Varlik tablosuna dusuk-guven etiketlerini ekler.

    Girdi `entities.parquet` semasini bekler; en az su kolonlar gerekir:
    `normalized_concept`, `assertion`, `temporality`, `assertion_rule`.

    Doner: ayni tablo + uc yeni kolon
      `dusuk_guven`        bool
      `dusuk_guven_kodu`   str  ("" ya da tetiklenen kural kodlari, "|" ile)
      `suphe_yukseltebilir` bool  - toplama kuralinin kullandigi bayrak
    """
    gerekli = {"normalized_concept", "assertion", "temporality", "assertion_rule"}
    eksik = gerekli - set(varliklar.columns)
    if eksik:
        raise ValueError(f"girdi filtresi icin eksik kolon: {sorted(eksik)}")

    d = varliklar.copy()

    f1 = d["temporality"].eq("prior")
    f2 = (
        d["normalized_concept"].isin(MALIGNITE_KAVRAMLARI)
        & d["assertion"].eq("present")
        & d["assertion_rule"].isin(VARSAYILAN_KURALLAR)
    )

    kodlar = pd.Series([[] for _ in range(len(d))], index=d.index)
    for bayrak, kod in ((f1, "F1_gecmis_bulgu"), (f2, "F2_kanitsiz_present")):
        kodlar[bayrak] = kodlar[bayrak].apply(lambda lst, k=kod: lst + [k])

    d["dusuk_guven"] = f1 | f2
    d["dusuk_guven_kodu"] = kodlar.apply("|".join)
    # Dusuk guvenli varlik rapor sinifini YUKSELTEMEZ. Silinmez, kayitta kalir.
    d["suphe_yukseltebilir"] = ~d["dusuk_guven"]
    d["girdi_filtresi_surumu"] = FILTRE_SURUMU
    return d


def ozet(filtrelenmis: pd.DataFrame) -> dict:
    """Filtrenin etkisini raporlanabilir bicimde ozetler."""
    n = len(filtrelenmis)
    dg = filtrelenmis["dusuk_guven"]
    kod_sayim: dict[str, int] = {}
    for k in filtrelenmis.loc[dg, "dusuk_guven_kodu"]:
        for parca in k.split("|"):
            kod_sayim[parca] = kod_sayim.get(parca, 0) + 1
    return {
        "filtre_surumu": FILTRE_SURUMU,
        "toplam_varlik": n,
        "dusuk_guven": int(dg.sum()),
        "dusuk_guven_orani_yuzde": round(float(dg.mean()) * 100, 3) if n else 0.0,
        "kural_basina": kod_sayim,
        "suphe_yukseltebilir": int((~dg).sum()),
    }


def hata_butcesi() -> dict:
    """Zaman ekseninin sema ciktisina katkisinin UST SINIRI.

    docs/29 §7/2: "prior F1 %36,4 verilmisken, zaman ekseninin sema ciktisina
    katkisi UST SINIRLA sinirlandirilir ve bu sinir yazilir."

    Hesap: zaman ekseni varliklarin yalniz %0,50'sine dokunuyor (prior). Bu
    eksen TAMAMEN yanlis olsa bile etkileyebilecegi varlik orani bu tavanla
    sinirlidir. Filtre bu varliklari zaten suphe yukseltemez yaptigi icin,
    kalan risk YONU TERSTIR: KACIRILAN prior'lar (yani `current` sanilan gecmis
    bulgular). O yon olculemez cunku K7 zaten esigi gecemedi.

    Bu yuzden BAGLAYICI KARAR: zaman ekseni semada KARAR AGIRLIGI TASIMAZ.
    Yalniz dusuk-guven isaretlemesi icin kullanilir.
    """
    return {
        "zaman_ekseni_kapsami_yuzde": 0.50,
        "prior_present_varlik": 4557,
        "bunlarin_ipucusuz_orani_yuzde": 81.4,
        "K7_prior_F1_yuzde": 36.4,
        "temporality_varsayilan_orani_yuzde": 99.24,
        "baglayici_karar": (
            "Zaman ekseni semada KARAR AGIRLIGI TASIMAZ. Olculmus F1 %36,4 ile "
            "esigi gecememis, ustelik degerlerin %99,24'u varsayilandir - "
            "'current' bir kanit degil kanit yoklugudur. Eksen yalniz "
            "dusuk-guven isaretlemesinde kullanilir."
        ),
        "kalan_olculemez_risk": (
            "KACIRILAN prior'lar (gecmis bulgunun `current` sanilmasi). K7 esigi "
            "gecemedigi icin bu yonun buyuklugu OLCULEMEZ ve acikca ilan edilir."
        ),
    }
