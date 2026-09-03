"""TASK-16 Adim 1 - CELISEN GOSTERGE TARAMASI.

Plan: docs/29_task16_calisma_plani.md §8.5 adim 1

Amac: C kaydinin (klinik yargi gerektiren kararlar) gercek buyuklugunu OLCMEK.
Bagimsiz denetim, "15-25 madde" tahmininin ampirik olmadigini isaretledi
(docs/32 bulgu #6). Bu betik tahmin yerine SAYIM koyar.

Yontem: ayni cumlede birbiriyle celisen gosterge siniflari birlikte geciyorsa,
o cumle bir KARAR NOKTASI uretir - semanin hangisinin kazanacagini soylemesi
gerekir. Celisen sinif ciftlerini ve her birinin korpustaki agirligini sayar.

KAPSAM: yalniz GELISTIRME HAVUZU (configs/splits_holdout.json).
Degerlendirme kilidindeki hicbir cumle okunmaz.

Kullanim:
    python scripts/42_task16_celisen_gosterge_taramasi.py
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task16_celisen_gosterge_taramasi.json"

# Gosterge siniflari. Desenler AGENTS.md'deki olculmus korpus terimlerinden
# turetildi (ornegin bu korpusun benign sozlugu `sequela`, `popcorn` degil).
SINIFLAR: dict[str, str] = {
    "malignite":     r"malignan|metasta|carcinom|tumoral|neoplas|spicul",
    "benign":        r"sequela|granulom|benign|hamartom",
    "kalsifikasyon": r"calcific",
    "stabilite":     r"\bstable\b|unchanged|no change|no significant (?:difference|change)",
    "negasyon":      r"\bno\b|\bnot\b|without|absent|negative for",
    "belirsizlik":   r"cannot be excluded|can not be excluded|suspicious|probabl|possibl|may represent|in favor of",
    "enfeksiyon":    r"pneumon|infect|covid|inflammat|tuberculo",
    "buyume":        r"increas|enlarg|growth|\bgrew\b|\bnew\b|progress",
    "ekstratorasik": r"\bliver\b|hepatic|adrenal|\bkidney\b|\brenal\b|\bspleen\b",
}

# Semanin karar vermek ZORUNDA oldugu celiskiler.
# (a, b, neden karar gerektirdigi)
KARAR_GEREKTIREN: list[tuple[str, str, str]] = [
    ("malignite", "benign",        "Ayni cumlede hem malignite hem benign gosterge var; hangisi kazanir?"),
    ("malignite", "kalsifikasyon", "Kalsifikasyon tek basina benign gostergesi mi? Kanitlanmis maligniteyi ezer mi?"),
    ("malignite", "stabilite",     "Stabil bir malignite bulgusu hangi supheye duser?"),
    ("malignite", "negasyon",      "Negasyonun KAPSAMI malignite terimini iceriyor mu?"),
    ("malignite", "belirsizlik",   "Belirsiz malignite hangi duzeye duser?"),
    ("malignite", "enfeksiyon",    "Enfeksiyoz sureclе birlikte gecen malignite terimi nasil tartilir?"),
    ("malignite", "buyume",        "Buyume malignite suphesini yukseltir mi, ne kadar?"),
    ("malignite", "ekstratorasik", "Ekstratorasik organdaki malignite bulgusu kapsama girer mi?"),
    ("benign", "buyume",           "Benign nitelenen bir bulgu buyuyorsa benign kalir mi?"),
    ("benign", "belirsizlik",      "Belirsizlikle nitelenen benign bulgu hangi duzeye duser?"),
    ("kalsifikasyon", "buyume",    "Kalsifiye ve buyuyen lezyon nasil siniflanir?"),
    ("stabilite", "buyume",        "Ayni cumlede hem stabilite hem buyume ifadesi - hangisi gecerli?"),
    ("enfeksiyon", "belirsizlik",  "Enfeksiyon suphesi malignite suphesi degildir; ayrim nasil kurulur?"),
    ("negasyon", "belirsizlik",    "Olumsuzlanmis belirsizlik (ornegin 'dislanamaz degil') nasil cozulur?"),
]


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    # --- kapsam: yalniz gelistirme havuzu ---
    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])

    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme_calismalari = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    s = pd.read_parquet(CUMLELER, columns=["study_id", "text"])
    s = s[s["study_id"].isin(gelistirme_calismalari)]
    print(f"kapsam: gelistirme havuzu · {len(s):,} cumle "
          f"/ {s['study_id'].nunique():,} calisma  (kilit okunmadi)\n")

    # --- sinif bayraklari ---
    metin = s["text"].fillna("")
    bayrak = pd.DataFrame(
        {ad: metin.str.contains(dsn, case=False, regex=True, na=False)
         for ad, dsn in SINIFLAR.items()}
    )

    print("GOSTERGE SINIFI YOGUNLUGU")
    for ad in SINIFLAR:
        n = int(bayrak[ad].sum())
        print(f"  {ad:15} {n:>7,} cumle  (%{n / len(s) * 100:5.2f})")

    # --- celiskiler ---
    print("\nKARAR GEREKTIREN CELISKILER  (ayni cumlede birlikte gecen)")
    kayitlar = []
    for a, b, neden in KARAR_GEREKTIREN:
        birlikte = bayrak[a] & bayrak[b]
        n_cumle = int(birlikte.sum())
        n_calisma = int(s.loc[birlikte, "study_id"].nunique())
        kayitlar.append({
            "cift": f"{a}+{b}",
            "sinif_a": a, "sinif_b": b,
            "neden": neden,
            "cumle": n_cumle,
            "calisma": n_calisma,
            "cumle_orani_yuzde": round(n_cumle / len(s) * 100, 4),
        })
    kayitlar.sort(key=lambda r: -r["cumle"])
    for r in kayitlar:
        print(f"  {r['cift']:32} {r['cumle']:>7,} cumle / {r['calisma']:>6,} calisma")

    # --- olculmemis ciftler (kapsam denetimi) ---
    print("\nKAPSAM DENETIMI - listede OLMAYAN ama korpusta gecen ciftler")
    listede = {(r["sinif_a"], r["sinif_b"]) for r in kayitlar}
    listede |= {(b, a) for a, b in listede}
    atlanan = []
    for a, b in itertools.combinations(SINIFLAR, 2):
        if (a, b) in listede:
            continue
        n = int((bayrak[a] & bayrak[b]).sum())
        if n >= 500:  # anlamli hacim
            atlanan.append({"cift": f"{a}+{b}", "cumle": n})
    for r in sorted(atlanan, key=lambda x: -x["cumle"]):
        print(f"  {r['cift']:32} {r['cumle']:>7,} cumle   <- karar listesinde YOK")
    if not atlanan:
        print("  (yok)")

    esik = 100
    c_sayisi = sum(1 for r in kayitlar if r["cumle"] >= esik)

    ozet = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "taranan_cumle": int(len(s)),
        "taranan_calisma": int(s["study_id"].nunique()),
        "sinif_yogunlugu": {ad: int(bayrak[ad].sum()) for ad in SINIFLAR},
        "karar_esigi_cumle": esik,
        "esigi_gecen_celiski": c_sayisi,
        "celiskiler": kayitlar,
        "listede_olmayan_hacimli_ciftler": atlanan,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nOLCUM: {len(kayitlar)} celiski tarandi, "
          f"{c_sayisi} tanesi >={esik} cumlede geciyor.")
    print(f"YAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
