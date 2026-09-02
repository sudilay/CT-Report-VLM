"""RadTr bolunme dosyalarini ICERIK HASH'i ile denetler.

NEDEN VAR:
  RadTr'nin yayimlanmis `train.json` dosyasi `dev.json` ve `test.json`
  belgelerinin TAMAMINI birebir icerir. Bolunme kimligi DOSYA ADINDAN
  turetildigi surece (16_extract_radtr_thorax.py'deki eski `kaynak_bolum`
  alani gibi) test kilidi bos doner: train.json icinden okunan bir test
  belgesi `kaynak_bolum="train"` etiketi alir ve gelistirme havuzuna girer.

  Bu betik kimligi icerikten uretir ve cakismayi gorunur kilar. Kirlenme
  bulursa cikis kodu 1'dir; regresyon kapisi olarak kullanilabilir.

MARUZIYET:
  Belge metni, span metni veya etiket ICERIGI hicbir kosulda basilmaz ve
  dosyaya yazilmaz. Her belge tek bir SHA-256 degerine indirgenir; yalnizca
  sayimlar raporlanir. Bu yuzden `test.json` uzerinde de calistirilabilir.

Kullanim: .venv/Scripts/python.exe scripts/26_bolunme_denetimi.py
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KAYNAK = ROOT / "data" / "external" / "radtr"
HARITA = ROOT / "data" / "processed" / "radtr_bolunme_haritasi.json"
BOLUMLER = ("train", "dev", "test")
# Bir belge birden fazla dosyada goruluyorsa GERCEK bolumu en kisitlayici
# olandir: test > dev > train. `train.json` icindeki bir test belgesi test'tir.
ONCELIK = {"test": 0, "dev": 1, "train": 2}

# 16_extract_radtr_thorax.py ile ayni tetkik-basligi suzgeci.
TORAKS = re.compile(r"TORAKS|AKC[İI]Ğ|AKCIG|TORAX|PULMONER|H[İI]LER", re.IGNORECASE)
KORONER = re.compile(r"KORONER", re.IGNORECASE)


def belge_kimligi(kayit: dict) -> tuple[str, str, bool]:
    """(icerik_hash, tam_hash, toraks_mi) — hicbiri metin tasimaz."""
    metin = " ".join(w for c in kayit["sentences"] for w in c)
    icerik = hashlib.sha256(metin.encode("utf-8")).hexdigest()
    tam = hashlib.sha256(
        (metin + json.dumps(kayit["ner"], sort_keys=True)).encode("utf-8")
    ).hexdigest()
    bas = metin[:70]
    return icerik, tam, bool(TORAKS.search(bas)) and not KORONER.search(bas)


def oku(bolum: str) -> list[tuple[str, str, bool]]:
    yol = KAYNAK / f"{bolum}.json"
    if not yol.exists():
        sys.exit(f"RadTr bulunamadi: {yol}")
    return [belge_kimligi(json.loads(s)) for s in yol.open(encoding="utf-8")]


def harita_yaz(veri: dict[str, list[tuple[str, str, bool]]]) -> None:
    """icerik SHA-256 -> gercek bolum. Yalniz hash ve etiket icerir, METIN ICERMEZ."""
    harita: dict[str, str] = {}
    for bolum in BOLUMLER:
        for icerik, _, _ in veri[bolum]:
            mevcut = harita.get(icerik)
            if mevcut is None or ONCELIK[bolum] < ONCELIK[mevcut]:
                harita[icerik] = bolum
    HARITA.parent.mkdir(parents=True, exist_ok=True)
    HARITA.write_text(
        json.dumps(
            {
                "aciklama": (
                    "icerik SHA-256 -> GERCEK RadTr bolumu. train.json dev ve test "
                    "belgelerini de icerdigi icin bolum kimligi dosya adindan "
                    "alinamaz (D49/D50). Bu dosya yalniz hash tasir, metin tasimaz."
                ),
                "oncelik": "test > dev > train",
                "belge_sayisi": len(harita),
                "harita": harita,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    dagitim = {b: sum(1 for v in harita.values() if v == b) for b in BOLUMLER}
    print(f"\nharita yazildi: {HARITA.relative_to(ROOT)}")
    print(f"  {len(harita)} benzersiz belge  ->  " + " · ".join(f"{b} {n}" for b, n in dagitim.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--yaz-harita",
        action="store_true",
        help="icerik hash -> gercek bolum haritasini yaz (metin icermez)",
    )
    args = ap.parse_args()
    veri = {b: oku(b) for b in BOLUMLER}
    icerik = {b: {x[0] for x in v} for b, v in veri.items()}
    toraks = {b: {x[0] for x in v if x[2]} for b, v in veri.items()}

    print("KAYIT SAYILARI")
    for b in BOLUMLER:
        print(f"  {b:<6}{len(veri[b]):>6} kayit   {len(icerik[b]):>6} benzersiz")
    tum = set().union(*icerik.values())
    print(f"  {'TOPLAM':<6}{sum(len(v) for v in veri.values()):>6} kayit   {len(tum):>6} benzersiz")

    print("\nBOLUMLER ARASI ICERIK CAKISMASI")
    kirli = 0
    for i, a in enumerate(BOLUMLER):
        for b in BOLUMLER[i + 1 :]:
            ortak = icerik[a] & icerik[b]
            kirli += len(ortak)
            durum = "TEMIZ" if not ortak else "KIRLI"
            print(f"  {a:<6}<-> {b:<6}{len(ortak):>6} ortak belge   [{durum}]")

    print("\nTORAKS ALT KUMESI")
    for b in BOLUMLER:
        print(f"  {b:<6}{len(toraks[b]):>6} belge")
    tum_toraks = set().union(*toraks.values())
    temiz = toraks["train"] - toraks["dev"] - toraks["test"]
    print(f"  benzersiz toraks belgesi        {len(tum_toraks):>6}")
    print(f"  temiz train havuzu (test/dev haric) {len(temiz):>6}")

    if args.yaz_harita:
        harita_yaz(veri)

    if kirli:
        print(
            "\nDURDU: bolumler ortak belge tasiyor. Bolunme kimligi DOSYA ADINDAN\n"
            "alinamaz; icerik hash'inden uretilmelidir (D49/D50).\n"
            "Ayrinti: docs/25_task15_bolunme_kirlenme_denetimi.md\n"
            "Cozum: --yaz-harita ile uretilen harita kullanilir; cikarim betigi\n"
            "bolumu bu haritadan okur, dosya adindan degil."
        )
        sys.exit(0 if args.yaz_harita else 1)
    print("\nBolumler ayrik.")


if __name__ == "__main__":
    main()
