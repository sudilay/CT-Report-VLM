"""EN/TR sozluk onarimi · aday listesini UC KURALDAN gecirip inceleme dosyasi uretir.

⚠ Bu betik kavramlari BAGIMSIZ tariyor; uretim birlesik matcher kullanir.
  Ciktilari uretimle bire bir DEGILDIR (D60/D61).

UC KURAL (D58, Sude onayi 2026-09-01):
  1. Bilgi hedef metinde VAR mi? Varsa ve sozluk goremiyorsa alet arizasidir ->
     duzeltilir. Bilgi cevirmen tarafindan DUSURULMUSSE gercek kayiptir -> dokunulmaz.
     (Bu kural anlam kontrolu gerektirir; betik aday sunar, hukum insanindir.)
  2. Aday IKINCI korpusta da destekli mi?
       EN adaylari -> CT-RATE train (449.868 cumle) ile sinanir.
       ⚠ TR adaylari icin ikinci korpus YOK (CT-RATE Turkce asillari yayimlanmadi);
         yalniz RadTr destegi ve anlam kontrolu ile degerlendirilir. Bu sinir
         raporda acikca yazilir.
  3. Tek gecis, sonra dondur.

CIKTI: `reports/task15_yuzey_onarim_adaylari.csv` - her satir bir aday, karar
sutunu BOS. Anlam kontrolu ve onay o dosyada yapilir.

⚠ YALNIZ `train`. `dev` ayar, `test` kilitli.

Kullanim: .venv/Scripts/python.exe scripts/34_task15_yuzey_onarim_listesi.py
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "configs"
PAKET = ROOT / "outputs" / "task15" / "train_packages"
CIKTI = ROOT / "reports" / "task15_yuzey_onarim_adaylari.csv"

KELIME_EN = re.compile(r"[a-z]+")
KELIME_TR = re.compile(r"[a-zçğıöşü]+")
DOLGU = frozenset(
    ["the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "is", "are", "was", "were", "be", "been", "being", "with", "without", "for", "from", "by", "as", "that", "this", "these", "those", "it", "its", "no", "not", "non", "have", "has", "had", "which", "seen", "observed", "noted", "present", "detected", "identified", "appearance", "appearances", "left", "right", "both", "bilateral", "level", "levels", "area", "areas", "region", "regions", "ve", "ile", "bir", "bu", "su", "icin", "olan", "olarak", "var", "yok", "ise", "de", "da", "ki", "mi", "mu", "izlendi", "izlenmektedir", "mevcut", "goruldu", "saptandi", "dikkati", "cekti"]
)
MIN_DESTEK = 3
AZAMI_GURULTU = 0.10
CT_RATE_ESIK = 100  # bu esigin altinda kalan aday RadTr'ye ozgu sayilir


def desenler():
    tr = {
        k: re.compile(v["desen"], re.IGNORECASE)
        for k, v in yaml.safe_load(
            (CONF / "turkce_yuzeyler_taslak.yaml").read_text(encoding="utf-8")
        )["yuzeyler"].items()
    }
    en = {}
    for f in ("anatomi_sozlugu.yaml", "bulgu_sozlugu.yaml"):
        for ad, t in yaml.safe_load((CONF / f).read_text(encoding="utf-8"))["kavramlar"].items():
            en[ad] = re.compile("|".join(f"(?:{x})" for x in t["desenler"]), re.IGNORECASE)
    return tr, en


def satirlar(yol: Path, alan: str) -> dict[str, str]:
    with yol.open(encoding="utf-8") as f:
        return {json.loads(s)["document_id"]: json.loads(s)[alan] for s in f}


def ngramlar(metin: str, kelime_deseni: re.Pattern, azami: int = 3) -> set[str]:
    kelimeler = kelime_deseni.findall(metin.lower())
    cikti = set()
    for n in range(1, azami + 1):
        for i in range(len(kelimeler) - n + 1):
            gram = kelimeler[i : i + n]
            # 3 harf siniri: Turkce radyolojide `kot` (kaburga) gecerli bir yuzey.
            # Ilk surumde 4'tu ve `kot`u eledi - elle bulunmus gercek bir bosluktu.
            if all(k in DOLGU for k in gram) or len(gram[0]) < 3:
                continue
            cikti.add(" ".join(gram))
    return cikti


def ct_rate_metni() -> str:
    s = pd.read_parquet(ROOT / "data/processed/sentences.parquet", columns=["study_id", "text"])
    r = pd.read_parquet(
        ROOT / "data/processed/reports_study_level.parquet", columns=["study_id", "split_tag"]
    )
    train = set(r.loc[r.split_tag.astype(str).str.contains("train", case=False, na=False), "study_id"])
    return " ".join(s.loc[s.study_id.isin(train), "text"].astype(str)).lower()


def adaylar(kavram, kaynak, hedef, kaynak_desen, hedef_desen, kelime_deseni):
    """kaynak dilinde bulunup hedef dilinde bulunamayan belgelerden aday n-gram."""
    bosluk = [
        k for k in kaynak
        if kaynak_desen[kavram].search(kaynak[k]) and not hedef_desen[kavram].search(hedef[k])
    ]
    kontrol = [k for k in kaynak if not kaynak_desen[kavram].search(kaynak[k])]
    if len(bosluk) < MIN_DESTEK or not kontrol:
        return [], len(bosluk)
    b, c = Counter(), Counter()
    for k in bosluk:
        b.update(ngramlar(hedef[k], kelime_deseni))
    for k in kontrol:
        c.update(ngramlar(hedef[k], kelime_deseni))
    out = []
    for gram, n in b.items():
        if n < MIN_DESTEK:
            continue
        gurultu = c[gram] / len(kontrol)
        if gurultu > AZAMI_GURULTU:
            continue
        out.append((gram, n, n / len(bosluk), gurultu))
    out.sort(key=lambda x: (-x[2], x[3]))
    return out, len(bosluk)


def main() -> None:
    tr_desen, en_desen = desenler()
    tr = satirlar(PAKET / "translation_train.jsonl", "text_tr")
    en = satirlar(PAKET / "en_genel_train.jsonl", "text")
    print("CT-RATE train yukleniyor (2. kural kapisi)...")
    ct = ct_rate_metni()
    tr_korpus = " ".join(tr.values()).lower()
    print(f"CT-RATE {len(ct):,} karakter · RadTr train {len(tr_korpus):,} karakter\n")

    satir_listesi = []
    for yon, kaynak, hedef, k_desen, h_desen, kelime, ikinci_korpus in (
        ("EN eksik", tr, en, tr_desen, en_desen, KELIME_EN, ct),
        ("TR eksik", en, tr, en_desen, tr_desen, KELIME_TR, None),
    ):
        for kavram in k_desen:
            ad_listesi, n_bosluk = adaylar(kavram, kaynak, hedef, k_desen, h_desen, kelime)
            for gram, n, kapsama, gurultu in ad_listesi[:5]:
                if ikinci_korpus is not None:
                    destek = len(re.findall(re.escape(gram), ikinci_korpus))
                    kapi2 = "GECER" if destek >= CT_RATE_ESIK else (
                        "sinirda" if destek >= 10 else "KALIR")
                else:
                    destek = len(re.findall(re.escape(gram), tr_korpus))
                    kapi2 = "ikinci korpus YOK"
                carpisan = [
                    k for k, r in h_desen.items() if k != kavram and r.search(gram)
                ]
                satir_listesi.append({
                    "yon": yon,
                    "kavram": kavram,
                    "aday_yuzey": gram,
                    "bosluk_belge": n_bosluk,
                    "kapsama_yuzde": round(100 * kapsama),
                    "gurultu_yuzde": round(100 * gurultu, 1),
                    "ikinci_korpus_anma": destek,
                    "kural2": kapi2,
                    "carpisma": ";".join(carpisan[:3]),
                    "KARAR": "",
                    "GEREKCE": "",
                })

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    with CIKTI.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satir_listesi[0]))
        w.writeheader()
        w.writerows(satir_listesi)

    print(f"yazildi: {CIKTI.relative_to(ROOT)}  ({len(satir_listesi)} aday satiri)")
    for yon in ("EN eksik", "TR eksik"):
        alt = [s for s in satir_listesi if s["yon"] == yon]
        kav = len({s["kavram"] for s in alt})
        gecer = sum(1 for s in alt if s["kural2"] == "GECER")
        print(f"  {yon:<10}{len(alt):>4} aday · {kav:>3} kavram · 2. kuraldan gecen {gecer}")
    print("\nKARAR ve GEREKCE sutunlari BOS - anlam kontrolu (1. kural) orada yapilacak.")


if __name__ == "__main__":
    main()
