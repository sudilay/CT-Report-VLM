"""Sozluk onarimi · BOSLUK CUMLELERINI okumak icin arac (D58 · 1. kural).

NEDEN BU BETIK VAR: `scripts/33`/`34` n-gram siralamasiyla aday uretiyor ve
231 adaydan yalnizca ~5'i gercek cikti. Raporlar sablonlu oldugu icin "birlikte
gecen" ile "ayni anlama gelen" ayrilamiyor (`lobulated` <- `interlobular`:
%97 kapsama, %0 gurultu, CT-RATE 2.423 anma - ve tamamen yanlis).

Dogru cevaplar hep CUMLE OKUYARAK bulundu. Bu betik siralamaz, sayilari
one cikarmaz; sadece bosluk belgelerindeki cumleleri KARSILIKLI gosterir:
kaynak dilde eslesen tam cumle + hedef dilde ayni indeksteki cumle ve
KOMSULARI (i-1, i, i+1).

Komsular bilerek gosteriliyor: Google cumle sirasini genelde korur ama her
zaman degil (EK 2'nin durustluk notu). Yanlis hizalama komsulara bakinca
gorulur; gizlenmis olmaz.

⚠ Bu betik HUKUM VERMEZ. Cikti insanin okumasi icindir. Bilgi hedef metinde
varsa alet arizasidir (duzeltilir); cevirmen dusurmusse gercek kayiptir
(dokunulmaz).

⚠ Desenler uretim sinirlariyla derlenir ama kavramlar BILINCLI olarak bagimsiz
  taranir: amac nihai cikti degil, insanin inceleyecegi bosluk adaylarini gormektir.

⚠ YALNIZ `train`. `dev` ayar kumesi, `test` kilitli.

Kullanim:
  python scripts/35_task15_bosluk_cumleleri.py --kavram cardiomegaly
  python scripts/35_task15_bosluk_cumleleri.py --kavram rib --yon tr
  python scripts/35_task15_bosluk_cumleleri.py --liste --yon en
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

CUMLE = re.compile(r"(?<=[.!?])\s+")


def desenleri_yukle() -> tuple[dict, dict]:
    """Desenleri URETIMDEKI GIBI derler - iki taraf ayni kurali kullanmaz.

    ⛔ Bu betigin ilk surumu iki tarafi da CIPLAK derliyordu (`re.compile(desen)`)
    ve bu, olcumu bozan bir ALET ARIZASIYDI:
      * TR ciplak derlenince `ektazi` deseni at-ektazi/brons-ektazi ICINE dustu
        (74 belge) ve `lob[uü]le` deseni inter-lobuler ICINE dustu (30 belge).
        Uretim (`scripts/23.derle`) soldan `\b` ekledigi icin bu ASLA olmuyordu.
      * EN ciplak derlenince desen kelime ICINDE eslesiyordu; uretim
        (`entities.py`) iki yandan `\b` ekler, yani daha katidir.
    Sonuc: sozlukte olmayan hatalar "sozluk hatasi" gibi gorunuyordu.
    `scripts/31`-`34` hala eski derlemeyi kullaniyor; ciktilari bu yuzden
    uretimle bire bir DEGILDIR.
    """
    tr = {
        # scripts/23_turkce_dev_olcum.derle: Turkce sondan eklemelidir ->
        # desen BASTA sinirli, SONDA serbest.
        k: re.compile(r"\b(?:" + v["desen"] + ")", re.IGNORECASE)
        for k, v in yaml.safe_load(
            (CONF / "turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8")
        )["yuzeyler"].items()
    }
    en = {}
    for dosya in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
        d = yaml.safe_load((CONF / dosya).read_text(encoding="utf-8"))
        for ad, t in d["kavramlar"].items():
            # entities.py: iki yandan kelime siniri
            en[ad] = re.compile(
                r"\b(?:" + "|".join(t["desenler"]) + r")\b", re.IGNORECASE
            )
    return tr, en


def satirlar(yol: Path, alan: str) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)[alan] for s in f}


def cumle_indeksi(metin: str, konum: int) -> tuple[list[str], int]:
    """Metni cumlelere ayirir ve `konum` karakterinin dustugu cumlenin indeksini verir."""
    cumleler = CUMLE.split(metin)
    sayac = 0
    for i, c in enumerate(cumleler):
        sayac += len(c) + 1
        if sayac > konum:
            return cumleler, i
    return cumleler, len(cumleler) - 1


def kirp(s: str, n: int = 210) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + " …"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kavram")
    ap.add_argument("--yon", choices=["en", "tr"], default="en",
                    help="en: EN sozlugun boslugu (TR buldu, EN bulamadi) · tr: tersi")
    ap.add_argument("--ornek", type=int, default=8)
    ap.add_argument("--liste", action="store_true", help="bosluk siralamasini yaz, cumle gosterme")
    args = ap.parse_args()

    tr_desen, en_desen = desenleri_yukle()
    tr = satirlar(PAKET / "translation_train.jsonl", "text_tr")
    en = satirlar(PAKET / "en_genel_train.jsonl", "text")
    assert set(tr) == set(en), "belge kumeleri farkli"

    if args.yon == "en":
        kaynak, hedef, k_desen, h_desen = tr, en, tr_desen, en_desen
        k_ad, h_ad = "TR", "EN"
    else:
        kaynak, hedef, k_desen, h_desen = en, tr, en_desen, tr_desen
        k_ad, h_ad = "EN", "TR"

    if args.liste:
        bosluk, ikisi = Counter(), Counter()
        for d in kaynak:
            for kav in k_desen:
                if kav not in h_desen or not k_desen[kav].search(kaynak[d]):
                    continue
                (ikisi if h_desen[kav].search(hedef[d]) else bosluk)[kav] += 1
        print(f"{h_ad} sozlugunun boslugu · {len(kaynak)} belge\n")
        print(f"{'kavram':<28}{'bosluk':>8}{'ikisinde':>10}")
        for kav, n in bosluk.most_common(40):
            print(f"{kav:<28}{n:>8}{ikisi[kav]:>10}")
        print(f"\nTOPLAM {sum(bosluk.values())} belge-kavram · {len(bosluk)} kavram")
        return

    kav = args.kavram
    if not kav:
        ap.error("--kavram ya da --liste gerekli")
    if kav not in k_desen or kav not in h_desen:
        ap.error(f"{kav} iki sozlukten birinde yok")

    n_bosluk = n_var = 0
    gosterilen = 0
    print(f"=== {kav} · {h_ad} sozluk boslugu ===")
    print(f"{k_ad} deseni: {k_desen[kav].pattern[:160]}")
    print(f"{h_ad} deseni: {h_desen[kav].pattern[:160]}\n")

    for d in sorted(kaynak):
        m = k_desen[kav].search(kaynak[d])
        if not m:
            continue
        if h_desen[kav].search(hedef[d]):
            n_var += 1
            continue
        n_bosluk += 1
        if gosterilen >= args.ornek:
            continue
        gosterilen += 1
        k_cumleler, i = cumle_indeksi(kaynak[d], m.start())
        h_cumleler = CUMLE.split(hedef[d])
        kayma = f"  [cumle {i+1}/{len(k_cumleler)} -> hedefte {len(h_cumleler)} cumle]"
        print(f"--- {d}{kayma}")
        print(f"  {k_ad}  : {kirp(k_cumleler[i])}")
        print(f"  eslesme: '{m.group(0)}'")
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(h_cumleler):
                isaret = ">>" if j == i else "  "
                print(f"  {isaret}{h_ad}{j-i:+d}: {kirp(h_cumleler[j])}")
        print()

    print(f"bosluk {n_bosluk} belge · ikisinde de var {n_var}")


if __name__ == "__main__":
    main()
