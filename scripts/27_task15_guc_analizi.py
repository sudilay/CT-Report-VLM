"""TASK-15 guc analizi - hangi eksen 0,05 F1'lik marji ayirt edebilir?

YONTEM: belge basina eksen destegi GERCEK RadTr `dev` (46 toraks belgesi)
verisinden alinir; TR ve EN kollari bilinen bir hata modeliyle (duyarlilik
0,80 · kesinlik 0,85 · gercek fark delta = 0) uretilir ve projenin KENDI
`paired_bootstrap_difference` fonksiyonu kosulur. Olculen sey sistem
basarimi DEGIL, olcegin verdigi guven araligi GENISLIGIDIR.

SINIRLARI:
  - Span sayimi kullanilir; gercek A2/A3 (belge, kavram, kesinlik) uclusunu
    tekillestirecegi icin oge sayisi daha az olacak -> gercek GA biraz DAHA
    GENIS cikar.
  - `dev`de absent 1,9/belge, `test`te 86/56 = 1,5/belge -> gercek absent GA'si
    buradaki sayidan DAHA KOTU olacak. Bu tablo iyimser taraftadir.
  - `test.json` okunmaz.

Kullanim: .venv/Scripts/python.exe scripts/27_task15_guc_analizi.py
"""

import json
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.task15 import paired_bootstrap_difference

TORAKS = re.compile(r"TORAKS|AKC[İI]Ğ|AKCIG|TORAX|PULMONER|H[İI]LER", re.IGNORECASE)
KORONER = re.compile(r"KORONER", re.IGNORECASE)
EKSEN = {
    "Obs_Present": "present",
    "Symptom_P": "present",
    "Obs_Absent": "absent",
    "Symptom_A": "absent",
    "Obs_Uncertain": "uncertain",
    "Differential Diagnosis": "uncertain",
}
DUYARLILIK, KESINLIK, MARJ = 0.80, 0.85, 0.05


def belge_basina_destek() -> dict[str, list[int]]:
    """GERCEK dev toraks belgelerinde eksen basina span sayisi."""
    per: dict[str, list[int]] = {"present": [], "absent": [], "uncertain": []}
    with (ROOT / "data" / "external" / "radtr" / "dev.json").open(encoding="utf-8") as f:
        for satir in f:
            d = json.loads(satir)
            metin = " ".join(w for c in d["sentences"] for w in c)
            bas = metin[:70]
            if not TORAKS.search(bas) or KORONER.search(bas):
                continue
            sayac = Counter(
                EKSEN[e] for _, _, e in [x for c in d["ner"] for x in c] if e in EKSEN
            )
            for eksen, liste in per.items():
                liste.append(sayac.get(eksen, 0))
    return per


def kol(destek, rng) -> list[tuple[int, int, int]]:
    """Belge basina (tp, fp, fn) uret."""
    sonuc = []
    for n in destek:
        tp = sum(1 for _ in range(n) if rng.random() < DUYARLILIK)
        fp = sum(1 for _ in range(n) if rng.random() < 1 - KESINLIK)
        sonuc.append((tp, fp, n - tp))
    return sonuc


def mikro_f1(sayaclar, indeksler) -> float:
    tp = fp = fn = 0
    for i in indeksler:
        a, b, c = sayaclar[i]
        tp, fp, fn = tp + a, fp + b, fn + c
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def yari_genislik(destek: list[int], n: int, tekrar: int = 12) -> float:
    genislikler = []
    for t in range(tekrar):
        rng = random.Random(500 + t)
        ornek = [rng.choice(destek) for _ in range(n)]
        tr, en = kol(ornek, rng), kol(ornek, rng)
        kimlikler = [str(i) for i in range(n)]
        indeks = {k: i for i, k in enumerate(kimlikler)}

        def metrik(sayaclar, s, ix=indeks):
            return mikro_f1(sayaclar, [ix[x] for x in s])

        sonuc = paired_bootstrap_difference(
            kimlikler,
            lambda s, c=tr: metrik(c, s),
            lambda s, c=en: metrik(c, s),
            iterations=2000,
            seed=11 + t,
        )
        genislikler.append((sonuc["ci95"][1] - sonuc["ci95"][0]) / 2)
    return statistics.median(genislikler)


def main() -> None:
    per = belge_basina_destek()
    print(f"gercek dev toraks belgesi: {len(per['present'])}\n")
    for eksen, liste in per.items():
        bos = sum(1 for x in liste if x == 0)
        print(
            f"  {eksen:<10} belge basina ort {statistics.mean(liste):.1f} · "
            f"toplam {sum(liste)} · destegi sifir olan belge {bos}/{len(liste)}"
        )

    boyutlar = (56, 100, 150)
    print(f"\nGA YARI GENISLIGI (delta=0, marj {MARJ})")
    print("eksen      " + "".join(f"{f'n={n}':>10}" for n in boyutlar))
    for eksen, liste in per.items():
        satir = [yari_genislik(liste, n) for n in boyutlar]
        bayrak = "   <- MARJI ASIYOR" if satir[0] > MARJ else ""
        print(f"{eksen:<11}" + "".join(f"{x:>10.3f}" for x in satir) + bayrak)

    print(
        "\nOkuma: yari genislik marjdan buyukse o eksen 0,05'lik farki "
        "AYIRT EDEMEZ;\nsonucu ne olursa olsun 'kanit yetersiz' cikar."
    )


if __name__ == "__main__":
    main()
