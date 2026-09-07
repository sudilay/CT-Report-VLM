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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from radyovlm.evaluation import envanter as env  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task16_celisen_gosterge_taramasi.json"

# ═══════════════════════════════════════════════════════════════════════
# ⚠ SURUM tarama-1.1 (2026-09-04, TASK-17 madde 1) - UC DESEN ONARILDI
# ═══════════════════════════════════════════════════════════════════════
# Plan: docs/34_task17_calisma_plani.md v2 §3.1 · Olcum:
# scripts/52_task17_desen_onarim_olcumu.py -> reports/task17_desen_onarim_olcumu.json
#
# D72 uc "olcum artefakti" kaydetmis ama DUZELTMEMISTI ("sozluk duzeltmesi
# TASK-17'nin isidir"). docs/34 §3.1 olctu ki kusur URETIM SOZLUGUNDE degil,
# TAM OLARAK BURADA: `configs/ipucu_sozlugu.yaml` dogrudur, bu tarayici ondan
# sapmistir. Onarim uretim sozlugune HIZALAMA ile yapildi (D60: olcum once
# alete uygulanir). Hicbir dondurulmus surum kirilmadi.
#
# 1) `belirsizlik` - ESKI 9.481 cumlenin %97,2'si (9.212) HATALIYDI.
#    ⚠ D72 yalniz `in favor of`u (6.720) isaretlemisti; olcum gosterdi ki
#      `suspicious` (1.745), `possibl` (430), `probabl` (407) DA hatali -
#      dordu de uretimde `cikarim_ifadesi` altindadir ve `present` uretir.
#      Gercek belirsizlik yalniz 305 cumleydi.
#    YENI = uretimin gercek belirsizlik siniflari:
#      belirsizlik_oncelikli.cannot_be_excluded + belirsizlik.{ayirici_tani,
#      parantez_soru}
#
# 2) `buyume` - ESKI 34.262 cumlenin 9.881'i "density/thickness increase"
#    (bulgu betimlemesi), 12.208'i "enlarged lymph node" (STATIK boyut).
#    YENI = lezyon buyumesi: acik boyut artisi + yeni ortaya cikma +
#    progresyon. ⚠ HARIC["buyume"] ile ORGAN boyutu ayiklanir - "Heart size
#    increased." korpusta 709, "Heart dimensions..." 825 kez gecen SABLON
#    cumlelerdir, lezyon buyumesi degil. Ayiklamanin maliyeti olculdu:
#    3.543 organ cumlesinin yalniz 1'inde baska buyume tetikleyicisi var.
#
# 3) `stabilite` ∩ `negasyon` - ESKI kesisim 1.020, bunun 934'u (%91,6)
#    SAHTEYDI: "no significant difference" iki desene birden uyuyordu.
#    Uretim sozlugu bunlari ZATEN `sahte_negasyon.degisim_yok` diye
#    isaretlemis; tarayici bunu bilmiyordu. YENI negasyon deseni bu kaliplari
#    olumsuz ileri-bakisla disliyor. Kesisim 1.020 -> 106.
# ═══════════════════════════════════════════════════════════════════════

TARAMA_SURUMU = "tarama-1.1"

# `sahte_negasyon.degisim_yok` (configs/ipucu_sozlugu.yaml): bir bulguyu
# OLUMSUZLAMAZ, STABILITE bildirir. `\bno\b` bunlari yakalamamali.
_SAHTE_NEGASYON = r"(?!\s+(?:significant\s+(?:change|difference)|interval\s+change|change\b))"

# Gosterge siniflari. Desenler AGENTS.md'deki olculmus korpus terimlerinden
# ve `configs/ipucu_sozlugu.yaml`den turetildi (ornegin bu korpusun benign
# sozlugu `sequela`, `popcorn` degil).
SINIFLAR: dict[str, str] = {
    # TASK-17 madde 3 (D79): tek kaynak. Eski DAR desen (`tumoral`)
    # 68 cumle / 56 calisma kaciriyordu - olculdu, bkz. envanter.py.
    "malignite":     env.MALIGNITE_METIN_DESENI,
    "benign":        r"sequela|granulom|benign|hamartom",
    "kalsifikasyon": r"calcific",
    # ONARILDI (3) - uretimdeki `degisim.stabil` ile hizalandi
    "stabilite":     r"\bstable\b|\bunchanged\b|no significant change|no interval change"
                     r"|no change\b|no significant difference|similar to (?:the )?previous",
    # ONARILDI (3) - sahte negasyon disland
    "negasyon":      rf"\bno\b{_SAHTE_NEGASYON}"
                     r"|\bnot\b|without|\babsent\b|absence of|negative for",
    # ONARILDI (1) - uretimin GERCEK belirsizlik siniflari
    "belirsizlik":   r"can ?not be excluded|can ?not be ruled out"
                     r"|cannot be definitively excluded"
                     r"|differential diagnos[ei]s|\bdifferential\b"
                     r"|\([^)]{1,60}\?\)",
    "enfeksiyon":    r"pneumon|infect|covid|inflammat|tuberculo",
    # ONARILDI (2) - LEZYON buyumesi; bulgu betimlemesi degil
    "buyume":        r"increase[d]? in size|increase in (?:the )?(?:size|dimension)"
                     r"|size (?:has |had )?increased|enlarg\w* in size"
                     r"|\bgrew\b|\bgrowth\b|growing"
                     r"|newly (?:developed|appeared|emerged|detected)|\bnewly\b"
                     r"|not (?:present|observed) in the previous"
                     r"|progression|progressed",
    "ekstratorasik": r"\bliver\b|hepatic|adrenal|\bkidney\b|\brenal\b|\bspleen\b",
}

# Sinifi daraltan DISLAMA desenleri. Bir cumle sinifin desenine uysa bile
# buradaki desene uyuyorsa sinifa ALINMAZ. Yalniz gerekcesi OLCULMUS
# dislamalar buraya girer.
HARIC: dict[str, str] = {
    # ORGAN boyutu artisi lezyon buyumesi DEGILDIR (kardiyomegali,
    # splenomegali). Sablon cumleler: "Heart size increased." 709 kez.
    # Maliyet olculdu: 3.543 organ cumlesinin 1'i baska buyume tetikleyicisi
    # de tasiyor - yani dislamanin bedeli 1 cumle.
    "buyume": r"(?:heart|cardiac|spleen|liver|hepatic|thyroid|kidney|renal"
              r"|adrenal|prostate|uter\w+|aort\w*)\s+(?:size|dimension)"
              r"|(?:size|dimension)s?\s+of\s+the\s+(?:heart|spleen|liver|thyroid|kidney)",
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

    # Dislama desenleri (tarama-1.1) - gerekcesi olculmus daraltmalar
    for ad, haric_dsn in HARIC.items():
        haric = metin.str.contains(haric_dsn, case=False, regex=True, na=False)
        n_once = int(bayrak[ad].sum())
        bayrak[ad] = bayrak[ad] & ~haric
        print(f"  [HARIC] {ad}: {n_once:,} -> {int(bayrak[ad].sum()):,} cumle "
              f"({n_once - int(bayrak[ad].sum()):,} dislandi)")

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
        "tarama_surumu": TARAMA_SURUMU,
        "desenler": dict(SINIFLAR),
        "dislama_desenleri": dict(HARIC),
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
