"""EN simetrik gecis · adim 2: eksik Ingilizce yuzeyleri KORPUSTAN turet.

⚠ Bu betik kavramlari BAGIMSIZ tariyor; uretim birlesik matcher kullanir.
  Ciktilari uretimle bire bir DEGILDIR (D60/D61).

YONTEM (D16 - ithal etme, madenle):
  Bir kavram icin BOSLUK belgeleri = TR deseni yakaliyor ama EN deseni yakalamiyor.
  KONTROL belgeleri  = TR deseni de yakalamiyor (kavram muhtemelen yok).
  Bosluk belgelerinde SIK, kontrol belgelerinde SEYREK gecen Ingilizce n-gramlar
  aday yuzeydir. Hizalamaya ihtiyac yok; olcum belge duzeyinde.

NEDEN ELLE YAZMIYORUZ: Turkce sozluk bu disiplinle kuruldu (D42: "kardiyomegali"
0 anma, "kalp boyutlari" 313). Ingilizce tarafa elle yuzey yazmak, EN kolunu
kazandirmak icin desen uydurmakla ayni sey olurdu. Aday listesi olculur, sonra
anlamca dogrulanir.

⚠ Bu betik ADAY uretir, sozluk YAZMAZ. Her aday su uc kapidan gecmelidir:
  1. kavrami gercekten ifade ediyor mu (anlam kontrolu - insan)
  2. olculmus destegi var mi (bu betik)
  3. baska kavramin yuzeyiyle carpisiyor mu (bu betik uyarir)

⚠ YALNIZ `train`. `dev` ve `test` bu turetmeye girmez.

Kullanim:
  .venv/Scripts/python.exe scripts/33_task15_en_yuzey_adaylari.py
  .venv/Scripts/python.exe scripts/33_task15_en_yuzey_adaylari.py --kavram cardiomegaly
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "configs"
PAKET = ROOT / "outputs" / "task15" / "train_packages"

KELIME = re.compile(r"[a-z]+")
# Tek baslarina yuzey olamayacak kelimeler; n-gram icinde gecebilirler ama
# n-gram BUNLARDAN IBARET olamaz.
DOLGU = frozenset(
    ["the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "is", "are", "was", "were", "be", "been", "being", "with", "without", "for", "from", "by", "as", "that", "this", "these", "those", "it", "its", "no", "not", "non", "have", "has", "had", "which", "were", "seen", "observed", "noted", "present", "detected", "identified", "appearance", "appearances", "left", "right", "both", "bilateral", "level", "levels", "area", "areas", "region", "regions"]
)


def desenleri_yukle() -> tuple[dict, dict]:
    tr = {
        k: re.compile(v["desen"], re.IGNORECASE)
        for k, v in yaml.safe_load(
            (CONF / "turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8")
        )["yuzeyler"].items()
    }
    en = {}
    for dosya in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
        for ad, t in yaml.safe_load(
            (CONF / dosya).read_text(encoding="utf-8")
        )["kavramlar"].items():
            en[ad] = re.compile("|".join(f"(?:{x})" for x in t["desenler"]), re.IGNORECASE)
    return tr, en


def satirlar(yol: Path, alan: str) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)[alan] for s in f}


def ngramlar(metin: str, azami: int = 3) -> set[str]:
    """Belgede gecen 1-3 kelimelik n-gramlar. Tamami dolgu olanlar atilir."""
    kelimeler = KELIME.findall(metin.lower())
    cikti = set()
    for n in range(1, azami + 1):
        for i in range(len(kelimeler) - n + 1):
            gram = kelimeler[i : i + n]
            if all(k in DOLGU for k in gram) or len(gram[0]) < 3:
                continue
            cikti.add(" ".join(gram))
    return cikti


def adaylari_bul(
    kavram: str, tr, en, tr_desen, en_desen, min_destek: int, azami_gurultu: float
) -> list[tuple[str, int, float]]:
    bosluk = [k for k in tr if tr_desen[kavram].search(tr[k]) and not en_desen[kavram].search(en[k])]
    kontrol = [k for k in tr if not tr_desen[kavram].search(tr[k])]
    if len(bosluk) < min_destek or not kontrol:
        return []
    b_say, k_say = Counter(), Counter()
    for k in bosluk:
        b_say.update(ngramlar(en[k]))
    for k in kontrol:
        k_say.update(ngramlar(en[k]))
    adaylar = []
    for gram, n in b_say.items():
        if n < min_destek:
            continue
        gurultu = k_say[gram] / len(kontrol)
        if gurultu > azami_gurultu:
            continue
        adaylar.append((gram, n, n / len(bosluk), gurultu))
    # once bosluk kapsamasi, sonra dusuk gurultu
    adaylar.sort(key=lambda x: (-x[2], x[3], -len(x[0])))
    return adaylar


def carpisma(gram: str, kavram: str, en_desen: dict) -> list[str]:
    return [k for k, r in en_desen.items() if k != kavram and r.search(gram)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kavram")
    ap.add_argument("--min-destek", type=int, default=3)
    ap.add_argument("--azami-gurultu", type=float, default=0.10)
    ap.add_argument("--aday", type=int, default=6)
    args = ap.parse_args()

    tr_desen, en_desen = desenleri_yukle()
    tr = satirlar(PAKET / "translation_train.jsonl", "text_tr")
    en = satirlar(PAKET / "en_genel_train.jsonl", "text")

    bosluklu = [
        k
        for k in tr_desen
        if sum(
            1 for d in tr if tr_desen[k].search(tr[d]) and not en_desen[k].search(en[d])
        )
        >= args.min_destek
    ]
    hedefler = [args.kavram] if args.kavram else bosluklu
    print(
        f"train {len(tr)} belge · bosluklu kavram {len(bosluklu)} "
        f"(min destek {args.min_destek}, azami gurultu %{100 * args.azami_gurultu:.0f})\n"
    )

    for kav in hedefler:
        adaylar = adaylari_bul(
            kav, tr, en, tr_desen, en_desen, args.min_destek, args.azami_gurultu
        )
        n_bosluk = sum(
            1 for d in tr if tr_desen[kav].search(tr[d]) and not en_desen[kav].search(en[d])
        )
        print(f"=== {kav}  ({n_bosluk} belgede bosluk)")
        print(f"    mevcut EN deseni: {en_desen[kav].pattern[:80]}")
        if not adaylar:
            print("    aday yok - esikleri gevsetmek gerekebilir\n")
            continue
        for gram, n, kapsama, gurultu in adaylar[: args.aday]:
            c = carpisma(gram, kav, en_desen)
            uyari = f"  ⚠ carpisma: {c[:3]}" if c else ""
            print(
                f"    {gram:<34} bosluk {n:>3}/{n_bosluk} (%{100 * kapsama:.0f})"
                f" · gurultu %{100 * gurultu:.1f}{uyari}"
            )
        print()

    if not args.kavram:
        print("Ayrinti icin: --kavram <ad>")
        print("\n⚠ Bunlar ADAYDIR. Sozluge girmeden once anlam kontrolunden gecer.")


if __name__ == "__main__":
    main()
