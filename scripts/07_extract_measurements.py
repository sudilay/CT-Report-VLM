# -*- coding: utf-8 -*-
"""A4 / TASK-09: Olcu ifadelerini cikarir -> measurements.parquet

Kararlar:
  D5  - "millimetric" gibi SAYISIZ boyut ifadeleri ayri niteliksel kategori olarak
        saklanir. Sayi atanmaz (uydurma veri olurdu), yok da sayilmaz (raporlarin
        buyuk kismi boyutu boyle veriyor).
  D6  - Araliklar (2-3 mm) icin ALT ve UST sinir birlikte tutulur. "Ust siniri al"
        bir KARAR KURALIDIR ve karar kurallari Faz 6'ya aittir; veri hazirligi
        korur, karar vermez.
        Bilinen belirsizlik: tire her zaman aralik demek degil. 166 kaydin 1'i
        "29-29 mm" seklinde sag-sol iki esit degeri listeliyor. Ayirt etmek
        karar kurali gerektirirdi; kaydedilip geciliyor.
  D7  - cm degerleri mm'ye cevrilir; ham birim unit_raw'da korunur.
  D3-b- Teknik olculer (kesit kalinligi) is_technical ile ayrilir, SILINMEZ.
  D10 - Ofsetler report_text'e goredir.

Yaziım varyantlari veriden olculdu (tahmin degil):
  millimetric 16.269 cumle · milimetric 292 · subcentimetric 96 · mm-sized 71
  x (carpi) 4.471 cumle · unicode × 0 · aralik "-" 151 · ondalik virgul 0

is_technical DAR desenle belirlenir. Genis desen ("thick" veya "thickness"
kelimesi) 54.031 cumle yakaliyor ve neredeyse tamami KLINIK:
  "The pleural effusion measured 50 mm at its thickest point"
  "an effusion reaching 7 mm in thickness"
Gercek teknik olcu Findings/Impression icinde yalnizca ~10 cumlede var; teknik
bilgi ayri Technique_EN alaninda duruyor ve o bolutlenmiyor.

BILINEN OZELLIK - cift kayit degil, iki ayri ANMA:
  712 cumlede hem niteliksel hem sayisal olcu var:
    "A subpleural non-specific millimetric nodule with a diameter of ~4 mm"
  Ikisi de metinde gecen ayri ANMALARDIR ve ikisi de kaydedilir. Ayni lezyona
  ait olduklarini belirlemek bulgu (entity) duzeyi bir istir -> Faz 2.
  UYARI: "kac olcu var" diye sayarken bu 712 cumle iki kez sayilir.

DEGERLENDIRILIP ALINMAYAN: micro* terimleri (217 cumle - micronodular,
  microcalcification, microlobulation, microcystic). Bunlar boyut beyani degil,
  patern/morfoloji niteleyicisi. "millimetric" acikca olcek soyluyor, "micro"
  soylemiyor; kategoriyi bulandirmamak icin alinmadi.

Sira: 04_segment_sentences.py -> 07_extract_measurements.py
Kullanim: .venv/Scripts/python.exe scripts/07_extract_measurements.py
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SENT = ROOT / "data" / "processed" / "sentences.parquet"
OUT = ROOT / "data" / "processed" / "measurements.parquet"

MEASUREMENT_VERSION = "meas-1.0"
CM_MM = 10.0
TEKNIK_PENCERE = 60      # karakter, olcunun iki yaninda
AYKIRI_MM = 200.0        # bu degerin ustu tek tek incelenir

_N = r"\d+(?:\.\d+)?"

# Sirasi onemli: once cok eksenli, sonra aralik, sonra tek deger.
# Lookbehind: bir sayinin ORTASINDAN eslesmeyi engeller ("12.5 mm" -> "5 mm" olmasin)
# ama bozuk noktalamadan sonra gelen mesru olcuyu engellemez:
#   "12.5 mm"        -> "5"in oncesi "." ve ondan onceki "2" rakam  -> reddedilir
#   "limits.5 mm"    -> "5"in oncesi "." ve ondan onceki "s"        -> kabul edilir
# Ilk hali (?<![\d.]) ikinci durumu da bloke ediyordu; 23 olcu kaciyordu.
OLCU = re.compile(
    rf"(?<!\d)(?<!\d\.)(?P<num>"
    rf"{_N}(?:\s*[xX×]\s*{_N})+"      # 5x3  /  26x18x40
    rf"|{_N}\s*-\s*{_N}"                    # 2-3
    rf"|{_N}"                               # 12
    rf")\s*(?P<unit>mm|cm)\b", re.I)

# Niteliksel boyut (D5). Yazim varyantlari veriden alindi.
NITELIKSEL = re.compile(r"\b(?P<q>sub)?(?P<s>milli|mili|centi)metri[ck]\w*", re.I)

# Teknik olcu baglami - DAR. Genis desen klinik olculeri yanlis isaretler.
TEKNIK = re.compile(
    r"thick\s+sections?|section\s+thickness|slice\s+thickness|"
    r"sections?\s+(?:were|was)\s+(?:taken|obtained)|collimat\w*|"
    r"reconstruction\s+interval", re.I)


def eksenleri_coz(ham: str, birim: str) -> tuple[list[float], bool]:
    """Ham sayi grubunu mm cinsinden eksen listesine cevirir (D7)."""
    aralik = bool(re.search(r"\d\s*-\s*\d", ham))
    parcalar = re.split(r"\s*[xX×-]\s*", ham)
    carpan = CM_MM if birim.lower() == "cm" else 1.0
    return [round(float(p) * carpan, 2) for p in parcalar if p], aralik


def teknik_mi(metin: str, bas: int, son: int) -> bool:
    """D3-b: olcunun cevresinde DAR teknik desen var mi."""
    p = metin[max(0, bas - TEKNIK_PENCERE): son + TEKNIK_PENCERE]
    return bool(TEKNIK.search(p))


def main() -> None:
    sent = pd.read_parquet(SENT)
    print(f"kaynak: {len(sent):,} cumle")

    kayitlar = []
    for r in sent.itertuples(index=False):
        metin = r.text
        # Cumle icindeki tum olculer once toplanir, sonra METIN SIRASINA gore
        # numaralandirilir. Sayisal ve niteliksel ayri donguler oldugu icin
        # dogrudan sayac kullanmak sirayi bozuyordu: "millimetric nodule ...
        # 4 mm" cumlesinde onde gelen 'millimetric' arkadaki '4 mm'den sonra
        # numara aliyordu (562 cumle etkileniyordu).
        bulunanlar = []

        # --- Sayisal olculer ---
        for m in OLCU.finditer(metin):
            eksenler, aralik = eksenleri_coz(m.group("num"), m.group("unit"))
            if not eksenler:
                continue
            bulunanlar.append({
                "study_id": r.study_id, "section": r.section, "sent_idx": r.sent_idx,
                "kind": "numeric",
                "raw_text": m.group(0),
                "unit_raw": m.group("unit").lower(),
                "axes_mm": eksenler,
                "n_axes": len(eksenler),
                "min_mm": min(eksenler), "max_mm": max(eksenler),
                "is_range": aralik,
                "size_qualitative": None,
                "is_technical": teknik_mi(metin, m.start(), m.end()),
                "char_start": r.char_start + m.start(),
                "char_end": r.char_start + m.end(),
            })

        # --- Niteliksel boyutlar (D5) ---
        for m in NITELIKSEL.finditer(metin):
            olcek = m.group("s").lower()
            olcek = "milli" if olcek in ("milli", "mili") else olcek
            etiket = ("sub" if m.group("q") else "") + olcek + "metric"
            bulunanlar.append({
                "study_id": r.study_id, "section": r.section, "sent_idx": r.sent_idx,
                "kind": "qualitative",
                "raw_text": m.group(0),
                "unit_raw": None, "axes_mm": None, "n_axes": 0,
                "min_mm": None, "max_mm": None, "is_range": False,
                "size_qualitative": etiket,
                "is_technical": False,
                "char_start": r.char_start + m.start(),
                "char_end": r.char_start + m.end(),
            })

        # --- Metin sirasina gore numaralandir ---
        for idx, kayit in enumerate(sorted(bulunanlar, key=lambda x: x["char_start"])):
            kayit["meas_idx"] = idx
            kayitlar.append(kayit)

    df = pd.DataFrame(kayitlar)
    # Surum zinciri: olcunun hangi bolutleme ve sablon surumunden geldigi
    # kaybolmasin diye ust katmanlarin surumleri de tasinir.
    for kol in ("segmentation_version", "template_version"):
        if kol in sent.columns:
            df[kol] = sent[kol].iloc[0]
    df["measurement_version"] = MEASUREMENT_VERSION
    df.to_parquet(OUT, index=False)

    say = df.kind.value_counts()
    print(f"\nyazildi: {OUT.name}  ({len(df):,} olcu)")
    print(f"  sayisal    : {say.get('numeric', 0):,}")
    print(f"  niteliksel : {say.get('qualitative', 0):,}")

    num = df[df.kind == "numeric"]
    print(f"\nSAYISAL OLCULER")
    print(f"  birim  : {num.unit_raw.value_counts().to_dict()}")
    print(f"  eksen  : {num.n_axes.value_counts().sort_index().to_dict()}")
    print(f"  aralik : {num.is_range.sum():,}")
    print(f"  teknik : {num.is_technical.sum():,}")
    print(f"  max_mm : medyan={num.max_mm.median():.1f}  "
          f"p99={num.max_mm.quantile(.99):.1f}  max={num.max_mm.max():.1f}")
    aykiri = num[num.max_mm > AYKIRI_MM]
    print(f"  {AYKIRI_MM:.0f} mm ustu: {len(aykiri):,} (elle incelenecek)")

    nit = df[df.kind == "qualitative"]
    print(f"\nNITELIKSEL BOYUTLAR")
    print(f"  {nit.size_qualitative.value_counts().to_dict()}")

    kapsanan = df.groupby(["study_id", "section", "sent_idx"]).size()
    print(f"\n  olcu iceren cumle: {len(kapsanan):,} "
          f"(%{100*len(kapsanan)/len(sent):.1f})")


if __name__ == "__main__":
    main()
