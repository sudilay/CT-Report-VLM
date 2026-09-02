"""MedGemma post-editini denetler: sayi/birim ihlalleri GERCEK mi, artefakt mi?

NEDEN AYRI BETIK: `--gevsek-sayi` ile kosuldugunda ihlal SAYISI raporlanir ama
turu raporlanmaz. 23/46 gibi bir oran tek basina okunamaz - "MedGemma olcumleri
bozuyor" da olabilir, "denetim yanlis alarm veriyor" da. Ayni hatayi bir kez
yaptik: Turkce eki birime yapisinca (`1 cm'yi`) TR->EN kiyasi 6 yanlis alarm
uretmisti. Bu betik ihlalleri TURUNE gore ayirir.

Kullanim:
  .venv/Scripts/python.exe scripts/30_task15_postedit_denetimi.py ^
    --once outputs/task15/ceviri_dev/en_genel_dev.jsonl ^
    --sonra outputs/task15/ceviri_dev/en_tibbi_dev.jsonl
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from radyovlm.evaluation.translation import (
    birim_imzasi,
    sayi_imzasi,
)

# Zararsiz olabilecek donusumler - ihlali ACIKLAR, mesrulastirmaz.
DENK_BIRIM = {("cm", "mm"), ("mm", "cm")}  # birim cevrimi: sayi da degismeli


def satirlar(yol: Path) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)["text"] for s in f}


def sinifla(once: str, sonra: str) -> tuple[str, str]:
    """Ihlali turune ayir: (sinif, aciklama)."""
    s_once, s_sonra = sayi_imzasi(once), sayi_imzasi(sonra)
    b_once, b_sonra = birim_imzasi(once), birim_imzasi(sonra)
    dusen_s = sorted((s_once - s_sonra).elements())
    eklenen_s = sorted((s_sonra - s_once).elements())
    dusen_b = sorted((b_once - b_sonra).elements())
    eklenen_b = sorted((b_sonra - b_once).elements())

    if not (dusen_s or eklenen_s or dusen_b or eklenen_b):
        return "temiz", ""
    if not dusen_s and not eklenen_s:
        return "yalniz_birim", f"birim {dusen_b} -> {eklenen_b}"
    if dusen_s and not eklenen_s and not eklenen_b:
        return "OLCUM_DUSTU", f"kaybolan sayi: {dusen_s}"
    if eklenen_s and not dusen_s:
        return "OLCUM_EKLENDI", f"uydurulan sayi: {eklenen_s}"
    if dusen_b and eklenen_b and {(*dusen_b, *eklenen_b)} & {frozenset(x) for x in DENK_BIRIM}:
        return "birim_cevrimi", f"{dusen_s}{dusen_b} -> {eklenen_s}{eklenen_b}"
    return "OLCUM_DEGISTI", f"{dusen_s} -> {eklenen_s}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", type=Path, required=True, help="post-edit ONCESI (EN)")
    ap.add_argument("--sonra", type=Path, required=True, help="post-edit SONRASI (EN)")
    ap.add_argument("--ornek", type=int, default=6, help="gosterilecek ornek sayisi")
    args = ap.parse_args()

    a, b = satirlar(args.once), satirlar(args.sonra)
    if set(a) != set(b):
        sys.exit(f"DURDU: belge kumeleri farkli ({len(a)} vs {len(b)})")

    siniflar, ornekler = Counter(), []
    uzunluk_orani = []
    for k in sorted(a):
        sinif, aciklama = sinifla(a[k], b[k])
        siniflar[sinif] += 1
        if sinif != "temiz":
            ornekler.append((sinif, k, aciklama))
        uzunluk_orani.append(len(b[k]) / max(len(a[k]), 1))

    n = len(a)
    print(f"belge: {n}\n")
    print("IHLAL SINIFLARI")
    for sinif, sayi in siniflar.most_common():
        agir = "  ⚠ CIDDI" if sinif.isupper() or sinif.startswith("OLCUM") else ""
        print(f"  {sinif:<16}{sayi:>4}  (%{100 * sayi / n:.0f}){agir}")

    ort = sum(uzunluk_orani) / n
    print(f"\nUZUNLUK ORANI (sonra/once): ort {ort:.2f} · "
          f"min {min(uzunluk_orani):.2f} · max {max(uzunluk_orani):.2f}")
    if ort < 0.8:
        print("  ⚠ post-edit metni belirgin KISALTMIS - ozetleme yasagi ihlal olabilir")
    if ort > 1.3:
        print("  ⚠ post-edit metni belirgin UZATMIS - aciklama eklemis olabilir")

    print(f"\nORNEKLER (ilk {args.ornek})")
    for sinif, k, aciklama in ornekler[: args.ornek]:
        print(f"\n  [{sinif}] {k}")
        print(f"    {aciklama}")
        for ad, metin in (("ONCE ", a[k]), ("SONRA", b[k])):
            olcum = re.findall(r"[^.]*?\d+[^.]*\.", metin)[:2]
            for c in olcum:
                print(f"    {ad}: {c.strip()[:110]}")

    ciddi = sum(v for s, v in siniflar.items() if s.startswith("OLCUM"))
    print(f"\nHUKUM: {ciddi}/{n} belgede GERCEK olcum degisikligi "
          f"(%{100 * ciddi / n:.0f})")
    if ciddi:
        print("  Test kosusunda `--gevsek-sayi` KULLANILMAZ; bu ihlaller kosuyu durdurur.")
        print("  Once istem sikilastirilip `dev`de tekrar olculmelidir.")


if __name__ == "__main__":
    main()
