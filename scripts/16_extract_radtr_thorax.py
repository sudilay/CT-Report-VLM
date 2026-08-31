# -*- coding: utf-8 -*-
"""RadTr'nin TORAKS alt kumesini ayirir ve bizim sema eksenlerine esler.

KAYNAK: github.com/BIGDaTA-Lab-AI/dygiepp-multilingual-radiology (data/radtr)
MAKALE: Diagnostic and Interventional Radiology 2025, dir.2025.243100

NEDEN AYIRIYORUZ:
  RadTr 1.364 belge ama yalnizca %21'i toraks. Makale "toraks" diyor; olculen
  dagilim abdomen %33, beyin %17. Bizim gorevimiz toraks BT oldugu icin
  alt kume ayrilmadan kullanilirsa alan disi metinle calisilmis olur.

SENTETIK UYARISI (docs/14):
  Raporlar radyologlar tarafindan ELLE yazildi (gercek hasta verisi degil) ve
  UC radyolog paralel etiketledi. Turkce kural gelistirme icin kullanilabilir;
  GERCEK DUNYA BASARIM iddiasi icin yeterli degildir.

LISANS UYARISI:
  Depo LICENSE'i MIT ama telif "David Wadden 2021" -> catallanan DyGIE++ KODU.
  VERININ lisansi ayrica dogrulanmali; yayinda kullanmadan once yazarlara sorulmali.

Kullanim: .venv/Scripts/python.exe scripts/16_extract_radtr_thorax.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAYNAK = ROOT / "data" / "external" / "radtr"
HEDEF = ROOT / "data" / "processed"

# Tetkik basligindan bolge tayini. Baslik ilk ~70 karakterde.
TORAKS = re.compile(r"TORAKS|AKC[İI]Ğ|AKCIG|TORAX|PULMONER|H[İI]LER", re.I)
# Koroner BT anjiyo toraks sayilmaz: PARROT'ta oldugu gibi akciger icerigi yok.
KORONER = re.compile(r"KORONER", re.I)

# RadTr etiketi -> bizim eksen. Esleme TAM DEGIL, bilerek:
#   Obs_Technical bizde AYRI eksen (D30), assertion'a karismaz.
#   Obs_Advice bizde kesinligi degistirmez.
ESLEME = {
    "Obs_Present":            ("observation", "present"),
    "Obs_Absent":             ("observation", "absent"),
    "Obs_Uncertain":          ("observation", "uncertain"),
    "Obs_Anatomy":            ("anatomy",     None),
    "Obs_Technical":          (None,          None),      # D30: ayri eksen
    "Obs_Advice":             (None,          None),      # kesinligi degistirmez
    "Differential Diagnosis": ("observation", "uncertain"),
    "Symptom_P":              ("symptom",     "present"),
    "Symptom_A":              ("symptom",     "absent"),
}


def belge_metni(d: dict) -> tuple[list, str]:
    kel = [w for s in d["sentences"] for w in s]
    return kel, " ".join(kel)


def toraks_mi(metin: str) -> bool:
    bas = metin[:70]
    return bool(TORAKS.search(bas)) and not KORONER.search(bas)


def main() -> None:
    if not (KAYNAK / "train.json").exists():
        sys.exit(f"RadTr bulunamadi: {KAYNAK}")

    hepsi, secilen = [], []
    for f in ("train", "dev", "test"):
        for satir in (KAYNAK / f"{f}.json").open(encoding="utf-8"):
            d = json.loads(satir)
            d["_bolum"] = f
            hepsi.append(d)
            if toraks_mi(belge_metni(d)[1]):
                secilen.append(d)

    print(f"RadTr toplam : {len(hepsi):,} belge")
    print(f"TORAKS alt kumesi: {len(secilen):,} belge "
          f"(%{100*len(secilen)/len(hepsi):.0f})")

    # ---- cikti: belge basina duz kayit ----
    kayitlar, etiket_say = [], Counter()
    for d in secilen:
        kel, metin = belge_metni(d)
        varliklar = []
        for b, e, t in [(b, e, t) for s in d["ner"] for b, e, t in s]:
            tip, kesinlik = ESLEME.get(t, (None, None))
            # OFSET DUZELTMESI (2026-08-31): RadTr token indeksleri 1-TABANLI.
            # Ilk surum kel[b:e+1] aliyordu ve span'lar BIR TOKEN saga kaymisti:
            # Obs_Anatomy etiketi "artmistir." fiiline denk geliyor, span'lar
            # cumle sinirini asiyordu.
            #
            # Nesnel olcut: iyi hizalanmis bir span, SON tokeni disinda nokta ile
            # biten token ICERMEZ. Kaymalar -4..+4 denendi:
            #     -1 -> %9,6   0 -> %16,3   +1 -> %22,7   (31.847 span)
            # -1 net minimum. Ikinci dogrulama: Obs_Anatomy span'larinin yuklemle
            # bitme orani %8,3 -> %2,4'e dustu.
            #
            # ⚠ Bu hata daha once bir kez "ofset 0 dogru" diye YANLIS
            # dogrulanmisti. Simdiki dogrulama nesnel olcute dayaniyor.
            varliklar.append({
                "metin": " ".join(kel[max(0, b - 1):e]),
                "radtr_etiket": t,
                "bizim_tip": tip,
                "bizim_kesinlik": kesinlik,
                "tok_bas": b - 1, "tok_son": e - 1,   # 0-tabanli, kapsayici
            })
            etiket_say[t] += 1
        kayitlar.append({
            "belge_id": d.get("doc_key", ""),
            "kaynak_bolum": d["_bolum"],
            "metin": metin,
            "varlik_sayisi": len(varliklar),
            "varliklar": varliklar,
        })

    yol = HEDEF / "radtr_toraks.jsonl"
    with yol.open("w", encoding="utf-8") as f:
        for k in kayitlar:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")

    tv = sum(k["varlik_sayisi"] for k in kayitlar)
    print(f"\nyazildi: {yol.name}")
    print(f"  {len(kayitlar):,} belge · {tv:,} etiketli varlik")

    print("\nETIKET DAGILIMI (toraks alt kumesi)")
    for t, n in etiket_say.most_common():
        tip, kes = ESLEME.get(t, (None, None))
        hedef = f"{tip}/{kes}" if tip else "AYRI EKSEN"
        print(f"  {t:<24}{n:>7,}   -> {hedef}")

    print("\nICERIK DENETIMI")
    metinler = [k["metin"] for k in kayitlar]
    for terim in ("nodül", "kitle", "malign", "metastaz", "plevra",
                  "lenf", "buzlu cam", "amfizem", "efüzyon"):
        n = sum(1 for m in metinler if re.search(terim, m, re.I))
        print(f"  {terim:<12}{n:>5} belge  (%{100*n/len(metinler):.0f})")


if __name__ == "__main__":
    main()
