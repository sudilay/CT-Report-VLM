"""TASK-15 on olcum: ayni belge TR ve EN okununca AYNI kavramlari mi veriyor?

⚠ BU BIR SONUC DEGILDIR. Kanonik kavram altini (radyolog onayli) henuz
uretilmedi, dolayisiyla A1/A2/A3 F1 HESAPLANAMAZ. Burada olculen sey kollarin
BIRBIRIYLE uyumu: EN kolu, TR kolunun buldugu kavramlari buluyor mu?

Bu bir GELISTIRME GOZLEMIDIR (D31). `dev` uzerinde kosar, `test` acilmaz.
Ablasyonun cevabi degildir ve sonuc hanesine yazilmaz.

NE ISE YARAR: cevirinin kavram duzeyinde ne kaybettirdigini altin beklemeden
gosterir. TR'de bulunup EN'de bulunamayan kavramlar, cevirinin sildikleridir.

Kullanim:
  .venv/Scripts/python.exe scripts/31_task15_kol_karsilastirma.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.extraction.entities import matcher_kur, sozlukleri_yukle  # noqa: E402
from radyovlm.extraction.turkce_varliklar import (  # noqa: E402
    kavramlari_bul,
    tr_matcher_kur,
    turkce_sozlugu_yukle,
)

CEVIRI = ROOT / "outputs" / "task15" / "ceviri_dev"
PAKET = ROOT / "outputs" / "task15" / "dev_packages_v2" / "translation_dev.jsonl"


def satirlar(yol: Path, alan: str) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)[alan] for s in f}


def main() -> None:
    tr_yuzey = turkce_sozlugu_yukle()
    tr_matcher, tr_indeks = tr_matcher_kur(tr_yuzey)
    en_kavramlar, _ = sozlukleri_yukle()
    en_matcher, en_nesne_indeks = matcher_kur(en_kavramlar)
    en_indeks = {grup: kavram.ad for grup, kavram in en_nesne_indeks.items()}
    ortak = set(tr_yuzey) & {kavram.ad for kavram in en_kavramlar}
    print(
        f"kapali envanter: {len(ortak)} kavram "
        f"(TR {len(tr_yuzey)} · EN {len(en_kavramlar)})\n"
    )

    kollar = {"TR": (satirlar(PAKET, "text_tr"), tr_matcher, tr_indeks)}
    for ad, dosya in (("EN-genel", "en_genel_dev.jsonl"), ("EN-ucuz", "en_ucuz_dev.jsonl")):
        yol = CEVIRI / dosya
        if yol.exists():
            kollar[ad] = (satirlar(yol, "text"), en_matcher, en_indeks)
    tibbi = CEVIRI / "en_tibbi_dev.jsonl"
    if tibbi.exists():
        kollar["EN-tibbi"] = (satirlar(tibbi, "text"), en_matcher, en_indeks)
    else:
        print("(EN-tibbi yok - istem v2 ile yeniden kosulmayi bekliyor)\n")

    bulunan = {
        ad: {
            k: kavramlari_bul(metin, matcher, indeks) & ortak
            for k, metin in metinler.items()
        }
        for ad, (metinler, matcher, indeks) in kollar.items()
    }
    belgeler = sorted(bulunan["TR"])

    print("BELGE BASINA BULUNAN KAVRAM")
    print(f"{'kol':<10}{'toplam':>9}{'belge basina':>14}")
    for ad in kollar:
        t = sum(len(bulunan[ad][k]) for k in belgeler)
        print(f"{ad:<10}{t:>9}{t / len(belgeler):>14.1f}")

    print("\nTR'YE GORE KOL UYUMU  (TR bulduklarini EN de buluyor mu)")
    print(f"{'kol':<10}{'ortak':>8}{'yalniz TR':>11}{'yalniz EN':>11}{'Jaccard':>10}")
    for ad in kollar:
        if ad == "TR":
            continue
        o = y_tr = y_en = 0
        kayip = Counter()
        for k in belgeler:
            a, b = bulunan["TR"][k], bulunan[ad][k]
            o += len(a & b)
            y_tr += len(a - b)
            y_en += len(b - a)
            kayip.update(a - b)
        j = o / (o + y_tr + y_en) if (o + y_tr + y_en) else 0.0
        print(f"{ad:<10}{o:>8}{y_tr:>11}{y_en:>11}{j:>10.3f}")
        print("     TR'de bulunup bu kolda kaybolan ilk 8 kavram:")
        for kav, n in kayip.most_common(8):
            print(f"       {n:>3}  {kav}")

    print("\nUYARI: Bu sayilar F1 DEGILDIR ve ablasyonun cevabi degildir.")
    print("  Kanonik altin uretilmeden dogruluk olculemez; bu yalniz kollarin")
    print("  birbiriyle uyumudur ve bir GELISTIRME GOZLEMIDIR (D31).")


if __name__ == "__main__":
    main()
