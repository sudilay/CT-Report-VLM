"""TASK-17 madde 12 - DAGILIM CAPASININ YENIDEN TURETILMESI (D76 -> Poisson).

Plan: docs/34_task17_calisma_plani.md v2 §6 (kullanici onayli) · Karar: D93

NEDEN
-----
D76: eski capa GECERSIZDI. Kabul araligi (%0,5-3,0) *"yuksek dereceli suphe
ifadesi"* sikligindan turetilmisti (392 cumle / 230 calisma), ama olculdu ki
o 392 cumlenin **yalniz 15'i** kanser terimi iceriyor - kalan 377'si
enfeksiyon/COVID suphesi. Capa *"suphe derecesi dili"* ile *"MALIGNITE
suphe derecesi dili"*ni ESITLEMISTI.

Yeni capa: **derece ifadesi ∩ kanser terimi** kesisimi (D76'nin kendi
yazdigi duzeltme).

⚠⚠ SIRA SORUNU - ACIKCA ILAN EDILIYOR
--------------------------------------
Bu betik kosarken sema ZATEN bir kez kosuldu (madde 11, `known_malignancy`
tetikleyicisinin etkisini olcmek icin) ve **sonucu BILINIYOR** (%0,870).
Normalde bu, "sonucu gorup olcut secmek" olurdu ve docs/29 §8.4 bunu
YASAKLAR.

Bu itiraza verilebilecek TEK dururst cevap sudur: **hicbir serbestlik
derecesi kalmamistir.** Capanin iki bileseni de ONCEDEN dondurulmustur:

  DERECE_DESENI          -> `sema.py` satir 327, TASK-16'da donduruldu
  MALIGNITE_METIN_DESENI -> `envanter.py`, `tier-1.2` kilidiyle hash'li

Aralik formulu de onceden yazildi: docs/34 v2 §6, *"aralik, dondurulmus
capa sayiminin %95 Poisson guven araligi olarak hesaplanir"* - plan
kullanici tarafindan onaylandiginda madde 8-11 HENUZ KOSULMAMISTI.

Yani burada SECILEN hicbir sey yok; onceden yazilmis bir formul, onceden
dondurulmus iki desene uygulaniyor. Yine de sonucu bildigim ILAN EDILIYOR
ki okuyan kendi hukmunu verebilsin.

⚠ Aralik BU BETIKTE hesaplanip DOSYAYA YAZILIR; madde 13'un resmi kosumu
ona KARSI degerlendirilir. Bu betikten sonra aralik DEGISTIRILMEZ.

Kullanim:
    .venv/Scripts/python.exe scripts/57_task17_dagilim_capasi.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from scipy import stats

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "src"))
from radyovlm.evaluation import envanter as env  # noqa: E402
from radyovlm.evaluation import sema  # noqa: E402

CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "configs/task17_dagilim_capasi.json"

GUVEN = 0.95


def poisson_ga(k: int, guven: float = GUVEN) -> tuple[float, float]:
    """Gozlenen k sayim icin TAM (exact) Poisson guven araligi.

    Alt sinir: chi2.ppf(alfa/2, 2k)/2      (k=0 icin 0)
    Ust sinir: chi2.ppf(1-alfa/2, 2k+2)/2
    """
    alfa = 1 - guven
    alt = 0.0 if k == 0 else stats.chi2.ppf(alfa / 2, 2 * k) / 2
    ust = stats.chi2.ppf(1 - alfa / 2, 2 * k + 2) / 2
    return float(alt), float(ust)


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])
    n_calisma = len(gelistirme)

    c = pd.read_parquet(CUMLELER, columns=["study_id", "text"])
    c = c[c["study_id"].isin(gelistirme)]
    m = c["text"].fillna("")

    print(f"kapsam: gelistirme havuzu · {n_calisma:,} calisma / {len(c):,} cumle")
    print("        (degerlendirme kilidi OKUNMADI)\n")

    print("=" * 74)
    print("CAPANIN IKI BILESENI - ikisi de ONCEDEN DONDURULMUS")
    print("=" * 74)
    print(f"  DERECE_DESENI          : {sema.DERECE_DESENI.pattern}")
    print(f"  MALIGNITE_METIN_DESENI : {env.MALIGNITE_METIN_DESENI}")

    derece = m.str.contains(sema.DERECE_DESENI, na=False)
    kanser = m.str.contains(env.MALIGNITE_METIN_DESENI, case=False, regex=True, na=False)
    kesisim = derece & kanser

    n_derece_c = int(derece.sum())
    n_kesisim_c = int(kesisim.sum())
    n_derece_s = int(c.loc[derece, "study_id"].nunique())
    n_kesisim_s = int(c.loc[kesisim, "study_id"].nunique())

    print("\n" + "=" * 74)
    print("OLCUM")
    print("=" * 74)
    print(f"  derece ifadesi olan cumle          : {n_derece_c:>6,} / {n_derece_s:>5,} calisma")
    print(f"  ⭐ derece ∩ KANSER TERIMI (yeni capa): {n_kesisim_c:>6,} / {n_kesisim_s:>5,} calisma")
    print(f"     -> capa orani: %{n_kesisim_s / n_calisma * 100:.3f}")
    print(f"\n  (D76'da bu kesisim 15 CUMLE idi - sozluk genisletmesi sonrasi degisti)")

    alt, ust = poisson_ga(n_kesisim_s)
    alt_o, ust_o = alt / n_calisma * 100, ust / n_calisma * 100

    print("\n" + "=" * 74)
    print(f"ARALIK - %{GUVEN*100:.0f} TAM POISSON GUVEN ARALIGI")
    print("=" * 74)
    print(f"  gozlenen  : {n_kesisim_s} calisma")
    print(f"  GA (sayim): [{alt:.1f}, {ust:.1f}]")
    print(f"  ⭐ KABUL ARALIGI: [%{alt_o:.3f}, %{ust_o:.3f}]")
    print(f"  (eski, GECERSIZ ilan edilen aralik: [%0,5, %3,0] - D76)")

    print("\n" + "=" * 74)
    print("⚠ KAPININ GUCU - RAPORA AYNEN GIRECEK")
    print("=" * 74)
    guc_notu = (
        f"Dagilim kapisi bu korpusta DUSUK GUCLUDUR. Capa tabani {n_kesisim_s} "
        f"calismadir; Poisson orneklem hatasi ±{n_kesisim_s**0.5:.1f} "
        f"(%{n_kesisim_s**0.5/max(n_kesisim_s,1)*100:.0f} bagil). Kapi yalniz KABA "
        "DEJENERASYONU (semanin populasyonun cok buyuk ya da cok kucuk bir "
        "bolumunu malignite-pozitif ilan etmesi) yakalayabilir; ince kalibrasyon "
        "hatasini yakalayamaz. KAPININ GECILMESI, SEMANIN DAGILIMININ DOGRU "
        "OLDUGUNUN KANITI DEGILDIR."
    )
    print("  " + guc_notu.replace(". ", ".\n  "))

    kayit = {
        "surum": "capa-1.0",
        "olusturma_utc": datetime.now(timezone.utc).isoformat(),
        "gorev": "TASK-17 madde 12 - dagilim capasinin yeniden turetilmesi",
        "yetki": "docs/34 v2 §6 (kullanici onayli: 'sert kapi kalsin, Poisson + guc ilan edilsin')",
        "eski_capa": {
            "aralik": [0.5, 3.0],
            "durum": "GECERSIZ (D76)",
            "sebep": ("'suphe derecesi dili' ile 'MALIGNITE suphe derecesi dili' "
                      "esitlenmisti; 392 derece cumlesinin yalniz 15'i kanser terimi "
                      "iceriyordu, 377'si enfeksiyon/COVID."),
        },
        "yeni_capa": {
            "tanim": "derece ifadesi ∩ kanser terimi (D76'nin kendi yazdigi duzeltme)",
            "derece_deseni": sema.DERECE_DESENI.pattern,
            "kanser_deseni": env.MALIGNITE_METIN_DESENI,
            "ikisi_de_onceden_dondurulmus": True,
            "derece_cumle": n_derece_c, "derece_calisma": n_derece_s,
            "kesisim_cumle": n_kesisim_c, "kesisim_calisma": n_kesisim_s,
            "capa_orani_yuzde": round(n_kesisim_s / n_calisma * 100, 4),
        },
        "kabul_araligi": {
            "yontem": f"tam (exact) Poisson %{GUVEN*100:.0f} guven araligi",
            "gozlenen_calisma": n_kesisim_s,
            "ga_sayim": [round(alt, 2), round(ust, 2)],
            "alt_yuzde": round(alt_o, 4),
            "ust_yuzde": round(ust_o, 4),
            "payda_calisma": n_calisma,
        },
        "guc_ilani": guc_notu,
        "sira_sorunu_ilani": (
            "⚠ Bu capa hesaplanirken sema ZATEN bir kez kosulmustu (madde 11) ve "
            "sonucu biliniyordu (%0,870). Normalde bu 'sonucu gorup olcut secmek' "
            "olurdu. Itiraza cevap: HICBIR SERBESTLIK DERECESI KALMAMISTIR - "
            "capanin iki deseni de onceden dondurulmustur (DERECE_DESENI TASK-16, "
            "MALIGNITE_METIN_DESENI tier-1.2 kilidi) ve aralik formulu plan v2 §6'da "
            "madde 8-11 kosulmadan ONCE yazilip onaylanmistir. Secilen hicbir sey "
            "yoktur; onceden yazilmis bir formul onceden dondurulmus desenlere "
            "uygulanmistir. Yine de sonucun bilindigi ILAN EDILIYOR."
        ),
        "baglayici": "Bu dosya yazildiktan SONRA aralik DEGISTIRILMEZ. Madde 13'un resmi kosumu buna karsi degerlendirilir.",
    }
    CIKTI.write_text(json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI (ve DONDURULDU): {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
