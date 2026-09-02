"""EN simetrik gecis · adim 1: Ingilizce sozlugun `train` cevirisindeki bosluklari olcer.

⚠ Bu betik kavramlari BAGIMSIZ tariyor; uretim birlesik matcher kullanir.
  Ciktilari uretimle bire bir DEGILDIR (D60/D61).

NEDEN (D56): Turkce sozluk RadTr'de gelistirildi, Ingilizce sozluk CT-RATE'te.
`dev`de olculdu: TR'de bulunup EN'de bulunamayan kavramlarin buyuk kismi CEVIRI
KAYBI DEGIL, Ingilizce sozlugun o ifadeyi tanimamasi. Ornek: Turkce
*"Kalp boyutlari artmistir"* -> Google *"Heart DIMENSIONS were increased"*, ama
Ingilizce sozluk `heart SIZE increase` ariyor.

Bu betik `train` uzerinde bosluklari ve HANGI INGILIZCE IFADENIN eklenmesi
gerektigini cikarir. Aday yuzeyler korpustan turetilir, ithal edilmez (D16).

⚠ YALNIZ `train`. `dev` ayar kumesi, `test` kilitli. Sozluk `train`de gelistirilip
dondurulacak; boylece Turkce sozlugun sahip oldugu firsatin ayni Ingilizce'ye
verilmis olur.

Kullanim:
  .venv/Scripts/python.exe scripts/32_task15_en_sozluk_bosluklari.py
  .venv/Scripts/python.exe scripts/32_task15_en_sozluk_bosluklari.py --kavram cardiomegaly
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "configs"
PAKET = ROOT / "outputs" / "task15" / "train_packages"

CUMLE = re.compile(r"(?<=[.!?])\s+")


def desenleri_yukle() -> tuple[dict, dict]:
    tr = {
        k: re.compile(v["desen"], re.IGNORECASE)
        for k, v in yaml.safe_load(
            (CONF / "turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8")
        )["yuzeyler"].items()
    }
    en = {}
    for dosya in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
        d = yaml.safe_load((CONF / dosya).read_text(encoding="utf-8"))
        for ad, t in d["kavramlar"].items():
            en[ad] = re.compile(
                "|".join(f"(?:{x})" for x in t["desenler"]), re.IGNORECASE
            )
    return tr, en


def satirlar(yol: Path, alan: str) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)[alan] for s in f}


def hizalanan_cumle(tr_metin: str, en_metin: str, tr_konum: int) -> str:
    """Turkce eslesmenin bulundugu cumlenin Ingilizce karsiligini TAHMIN et.

    Google belge duzeyinde ceviriyor ve cumle sirasini genelde koruyor; bu yuzden
    cumle INDEKSI makul bir hizalama capasidir. Kesin degildir - yalniz aday
    yuzey onermek icin kullanilir, olcume girmez.
    """
    tr_cumleler = CUMLE.split(tr_metin)
    en_cumleler = CUMLE.split(en_metin)
    sayac = 0
    for i, c in enumerate(tr_cumleler):
        sayac += len(c) + 1
        if sayac > tr_konum:
            return en_cumleler[i] if i < len(en_cumleler) else ""
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kavram", help="tek kavram icin ornek cumleleri goster")
    ap.add_argument("--ornek", type=int, default=4)
    args = ap.parse_args()

    tr_desen, en_desen = desenleri_yukle()
    tr = satirlar(PAKET / "translation_train.jsonl", "text_tr")
    en = satirlar(PAKET / "en_genel_train.jsonl", "text")
    assert set(tr) == set(en), "belge kumeleri farkli"
    print(f"train: {len(tr)} belge · {len(tr_desen)} kavram\n")

    bosluk = Counter()
    var_ikisinde = Counter()
    ornekler = defaultdict(list)
    for k in tr:
        for kav in tr_desen:
            m = tr_desen[kav].search(tr[k])
            if not m:
                continue
            if en_desen[kav].search(en[k]):
                var_ikisinde[kav] += 1
            else:
                bosluk[kav] += 1
                if len(ornekler[kav]) < 12:
                    ornekler[kav].append(
                        (m.group(0), hizalanan_cumle(tr[k], en[k], m.start()))
                    )

    if args.kavram:
        kav = args.kavram
        print(f"=== {kav} · bosluk {bosluk[kav]} belge · ikisinde de var {var_ikisinde[kav]}")
        print(f"    EN deseni: {en_desen[kav].pattern[:100]}\n")
        for tr_es, en_c in ornekler[kav][: args.ornek]:
            print(f"  TR eslesme: {tr_es}")
            print(f"  EN cumle  : {en_c[:150]}\n")
        return

    toplam_bosluk = sum(bosluk.values())
    toplam_var = sum(var_ikisinde.values())
    print(f"TR bulup EN bulamadigi  : {toplam_bosluk:,} belge-kavram")
    print(f"ikisinin de buldugu     : {toplam_var:,}")
    print(f"BOSLUK ORANI            : %{100 * toplam_bosluk / (toplam_bosluk + toplam_var):.1f}")
    print(f"bosluklu kavram sayisi  : {len(bosluk)} / {len(tr_desen)}\n")

    print("EN COK BOSLUK VEREN 25 KAVRAM")
    print(f"{'kavram':<26}{'bosluk':>8}{'ikisinde':>10}  ornek EN cumle")
    for kav, n in bosluk.most_common(25):
        ornek = ornekler[kav][0][1][:58] if ornekler[kav] else ""
        print(f"{kav:<26}{n:>8}{var_ikisinde[kav]:>10}  {ornek}")

    print("\nAyrinti icin: --kavram <ad>")


if __name__ == "__main__":
    main()
