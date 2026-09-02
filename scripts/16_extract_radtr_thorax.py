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

BOLUNME KIRLENMESI (D49/D50, 2026-09-01):
  RadTr'nin `train.json` dosyasi `dev.json` VE `test.json` belgelerinin tamamini
  birebir icerir. Bu betigin ilk surumu bolum kimligini DOSYA ADINDAN uretiyordu;
  bu yuzden 56 test toraks belgesi `kaynak_bolum="train"` etiketiyle gelistirme
  havuzuna sizdi. Artik bolum, `scripts/26_bolunme_denetimi.py --yaz-harita` ile
  uretilen ICERIK HASH haritasindan okunuyor ve test belgeleri hicbir cikti
  dosyasina giremiyor. `--bolum test` ve `--bolum all` secenekleri kaldirildi.
  Ayrinti: docs/25_task15_bolunme_kirlenme_denetimi.md

Kullanim: .venv/Scripts/python.exe scripts/16_extract_radtr_thorax.py --bolum dev
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAYNAK = ROOT / "data" / "external" / "radtr"
HEDEF = ROOT / "data" / "processed"
HARITA = HEDEF / "radtr_bolunme_haritasi.json"

# Bolum -> okunacak kaynak dosyalar. `test.json` HICBIR secenekte acilmaz.
# train.json dev/test belgeleri de icerdigi icin cikti haritayla suzulur.
BOLUM_KAYNAGI = {
    "train": ("train",),
    "dev": ("dev",),
    "gelistirme": ("train", "dev"),
}

# Tetkik basligindan bolge tayini. Baslik ilk ~70 karakterde.
TORAKS = re.compile(r"TORAKS|AKC[İI]Ğ|AKCIG|TORAX|PULMONER|H[İI]LER", re.IGNORECASE)
# Koroner BT anjiyo toraks sayilmaz: PARROT'ta oldugu gibi akciger icerigi yok.
KORONER = re.compile(r"KORONER", re.IGNORECASE)

# RadTr etiketi -> bizim eksen. Esleme TAM DEGIL, bilerek:
#   Obs_Technical bizde AYRI eksen (D30), assertion'a karismaz.
#   Obs_Advice bizde kesinligi degistirmez.
ESLEME = {
    "Obs_Present": ("observation", "present"),
    "Obs_Absent": ("observation", "absent"),
    "Obs_Uncertain": ("observation", "uncertain"),
    "Obs_Anatomy": ("anatomy", None),
    "Obs_Technical": (None, None),  # D30: ayri eksen
    "Obs_Advice": (None, None),  # kesinligi degistirmez
    "Differential Diagnosis": ("observation", "uncertain"),
    "Symptom_P": ("symptom", "present"),
    "Symptom_A": ("symptom", "absent"),
}


def belge_metni(d: dict) -> tuple[list, str]:
    kel = [w for s in d["sentences"] for w in s]
    return kel, " ".join(kel)


def icerik_hash(metin: str) -> str:
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def bolunme_haritasi() -> dict[str, str]:
    """icerik SHA-256 -> GERCEK bolum. Dosya adina GUVENILMEZ (D49/D50)."""
    if not HARITA.exists():
        sys.exit(
            f"DURDU: bolunme haritasi yok: {HARITA}\n"
            "  Once uret: .venv/Scripts/python.exe scripts/26_bolunme_denetimi.py "
            "--yaz-harita\n"
            "  Gerekce: RadTr train.json dev ve test belgelerini de icerir; bolum "
            "dosya adindan alinamaz (docs/25)."
        )
    return json.loads(HARITA.read_text(encoding="utf-8"))["harita"]


def toraks_mi(metin: str) -> bool:
    bas = metin[:70]
    return bool(TORAKS.search(bas)) and not KORONER.search(bas)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bolum",
        choices=tuple(BOLUM_KAYNAGI),
        required=True,
        help="Islenecek GERCEK bolum; `test` bilerek yoktur (D49/D50)",
    )
    ap.add_argument(
        "--task15-paket-dir",
        type=Path,
        help="Yalniz train/dev icin ayni geciste iki TASK-15 kor paketi yaz",
    )
    args = ap.parse_args()
    if args.task15_paket_dir and args.bolum not in ("train", "dev"):
        sys.exit("DURDU: TASK-15 gelistirme paketleri yalniz train/dev icindir")

    harita = bolunme_haritasi()
    istenen = {"gelistirme": {"train", "dev"}}.get(args.bolum, {args.bolum})
    dosyalar = BOLUM_KAYNAGI[args.bolum]
    if any(not (KAYNAK / f"{f}.json").exists() for f in dosyalar):
        sys.exit(f"RadTr bulunamadi: {KAYNAK}")

    hepsi, secilen, gorulen = 0, [], set()
    atlanan = Counter()
    for f in dosyalar:
        for satir in (KAYNAK / f"{f}.json").open(encoding="utf-8"):
            d = json.loads(satir)
            hepsi += 1
            h = icerik_hash(belge_metni(d)[1])
            gercek = harita.get(h)
            if gercek is None:
                sys.exit(f"DURDU: haritada olmayan belge, harita bayat: {h[:12]}")
            # KRITIK KAPI: train.json icindeki test/dev belgeleri buradan gecemez.
            if gercek not in istenen:
                atlanan[gercek] += 1
                continue
            if h in gorulen:  # ayni belge birden fazla dosyada olabilir
                atlanan["tekrar"] += 1
                continue
            gorulen.add(h)
            d["_bolum"] = gercek
            d["_hash"] = h
            if toraks_mi(belge_metni(d)[1]):
                secilen.append(d)

    print(f"RadTr kaynak ({'+'.join(dosyalar)}.json): {hepsi:,} kayit okundu")
    if atlanan:
        ayrinti = " · ".join(f"{k} {n:,}" for k, n in sorted(atlanan.items()))
        print(f"  bolum/tekrar suzgeci disladi: {ayrinti}")
    print(f"  gecerli benzersiz belge: {len(gorulen):,}")
    print(
        f"TORAKS alt kumesi: {len(secilen):,} belge "
        f"(%{100 * len(secilen) / len(gorulen):.0f})"
    )

    # ---- cikti: belge basina duz kayit ----
    kayitlar, etiket_say = [], Counter()
    for d in secilen:
        kel, metin = belge_metni(d)
        varliklar = []
        for b, e, t in [(b, e, t) for s in d["ner"] for b, e, t in s]:
            tip, kesinlik = ESLEME.get(t, (None, None))
            # OFSET: RadTr/DyGIE++ indeksleri 0-TABANLI ve son indeks KAPSAYICI.
            # span = kel[b:e+1]. Resmi okuyucu (dygiepp document.py Span.text)
            # `sentence.text[start_sent:end_sent + 1]` yapar; veri formati
            # dokumani da `[start_tok, end_tok, label]` ornegini 0'dan baslatir.
            #
            # ⚠ Bu satir iki kez YANLIS "duzeltildi". 2026-08-31'de `-1` kaymasi
            # kondu; gerekcesi "iyi hizalanmis span son tokeni disinda nokta
            # ICERMEZ" olcutuydu (-1 %9,6 · 0 %16,3). O olcut kendini kanitlayan
            # bir olcuttur: spani SOLA kaydirmak cumle-sonu noktasini mekanik
            # olarak disari atar, anlami duzeltmez.
            #
            # 2026-09-01 dogrulamasi YON-TARAFSIZ bir semantik capa kullanir:
            # bir `Obs_Absent` spani negasyon ipucu ICERMELIDIR. train+dev'de
            # kaymalar -4..+4 tarandi:
            #     -1 -> %32,3    0 -> %76,1    +1 -> %56,2
            # Tepe tam 0'da. Regresyon testi: tests/test_task15.py
            # `test_radtr_ofseti_semantik_capayi_gecer`.
            varliklar.append(
                {
                    "metin": " ".join(kel[b : e + 1]),
                    "radtr_etiket": t,
                    "bizim_tip": tip,
                    "bizim_kesinlik": kesinlik,
                    "tok_bas": b,
                    "tok_son": e,  # 0-tabanli, kapsayici
                }
            )
            etiket_say[t] += 1
        kayitlar.append(
            {
                # `doc_key` BENZERSIZ DEGIL: `_66_263.txt` ve `_71_42.txt` iki
                # ayri belgeyi adlandiriyor (D50). Kimlik icerik hash'iyle
                # tekillestirilir; RadTr adi izlenebilirlik icin korunur.
                "belge_id": f"{d.get('doc_key', '')}#{d['_hash'][:8]}",
                "radtr_doc_key": d.get("doc_key", ""),
                "icerik_sha256": d["_hash"],
                "kaynak_bolum": d["_bolum"],  # haritadan, dosya adindan DEGIL
                "metin": metin,
                "varlik_sayisi": len(varliklar),
                "varliklar": varliklar,
            }
        )

    yol = HEDEF / (
        "radtr_toraks.jsonl"
        if args.bolum == "gelistirme"
        else f"radtr_toraks_{args.bolum}.jsonl"
    )
    # Uzerine yazma kapisi ARTIK KOSULSUZ: `-1` ofsetiyle uretilmis eski
    # ciktilar denetim izi olarak korunacak (docs/24, docs/25).
    if yol.exists():
        sys.exit(
            f"DURDU: var olan ciktinin uzerine yazilmaz: {yol}\n"
            "  Eski dosya gecersizse once karantinaya al, ornegin:\n"
            f"  {yol.stem}.INVALID_OFFSET_MINUS1{yol.suffix}"
        )
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
    for terim in (
        "nodül",
        "kitle",
        "malign",
        "metastaz",
        "plevra",
        "lenf",
        "buzlu cam",
        "amfizem",
        "efüzyon",
    ):
        n = sum(1 for m in metinler if re.search(terim, m, re.IGNORECASE))
        print(f"  {terim:<12}{n:>5} belge  (%{100 * n / len(metinler):.0f})")

    if args.task15_paket_dir:
        sys.path.insert(0, str(ROOT / "src"))
        from radyovlm.evaluation.task15 import (
            build_package_records,
            write_package_pair,
        )

        ceviri, normalizasyon = build_package_records(kayitlar, args.bolum)
        manifest = write_package_pair(
            ceviri, normalizasyon, args.bolum, args.task15_paket_dir
        )
        print("\nTASK-15 KOR PAKETLER")
        print(
            f"  ceviri       {len(ceviri):,} belge  {manifest['translation']['sha256']}"
        )
        print(
            f"  normalizasyon {len(normalizasyon):,} span   "
            f"{manifest['normalization']['sha256']}"
        )
        print(f"  manifest                 {manifest['manifest_sha256']}")


if __name__ == "__main__":
    main()
