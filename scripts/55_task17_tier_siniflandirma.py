"""TASK-17 Madde 5b/6/7 - TIER SINIFLANDIRMASI: SIFIR-DESTEK IDDIASI SINANIR.

Plan: docs/34_task17_calisma_plani.md v2 §4.1 (Tier B) + §4.4 (benign Tier B)
Karar kaydi: D83

NEDEN VAR
---------
D74 Tier B'yi *"bu korpusta SIFIR gecen otoriter kanser terimleri"* diye
tanimladi ve ornek olarak `adenocarcinoma`, `squamous cell carcinoma`,
`lymphoma`, `sarcoma`, `mesothelioma` saydi. Tier B'nin butun ucuzlugu bu
iddiaya dayanir: *"hic eslesmeyen bir desen hicbir sayiyi degistiremez."*

⚠ AMA O ORNEKLER OLCULMEMISTI, VARSAYILMISTI.

Bagimsiz denetim is emrinde S5 tam olarak bunu sormustu: *"'bugun sifir
eslesiyor' iddiasi hangi olcumle dogrulanacak?"* Bu betik o olcumdur.

Ayni sinama benign eksene de uygulanir (docs/34 §4.4): kilavuzun benign
kalsifikasyon paternleri gercekten sifir mi?

YONTEM
------
Her aday desen gelistirme havuzunda ham cumle metnine karsi taranir.
  n = 0   -> Tier B  : olcum-notr, `ent` surumunu kirmaz
  n > 0   -> Tier A  : OLCUM DEGISTIRIR, kilit + yeniden uretim + etki
                       olcumu yolundan gecmek ZORUNDA
Ayrica n > 0 cikan her desen icin ORNEK CUMLE basilir - desenin DOGRU seyi
yakalayip yakalamadigi elle gorulsun diye. Sifirdan farkli olmak bir terimi
otomatik olarak gecerli yapmaz; desen YANLIS seyi yakaliyor olabilir.

KAPSAM: yalniz GELISTIRME HAVUZU. Degerlendirme kilidi okunmaz.
⚠ SINIR: sifir-destek iddiasi YALNIZ gelistirme havuzu icin dogrulanir.
Kilit uzerinde ateslenip ateslenmedigi madde 8/9'daki yeniden uretim ve
fark olcumunde ortaya cikacaktir; orada ateslerse YENI BULGU olarak
raporlanir, sessizce gecistirilmez.

Kullanim:
    .venv/Scripts/python.exe scripts/55_task17_tier_siniflandirma.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

KOK = Path(__file__).resolve().parent.parent
CUMLELER = KOK / "data/processed/sentences.parquet"
KORPUS = KOK / "data/processed/reports_study_level.parquet"
KILIT = KOK / "configs/splits_holdout.json"
CIKTI = KOK / "reports/task17_tier_siniflandirma.json"

ORNEK = 3
TOHUM = 20260907

# Aday desenler. `eksen` yalniz raporlama icin.
ADAYLAR: dict[str, dict] = {
    # ---- benign eksen (docs/34 §4.4, kilavuz kaynakli) ----
    "popcorn_calcification": {
        "desen": r"popcorn", "eksen": "benign",
        "kaynak": "ACR Lung-RADS v2022 · Fleischner 2017"},
    "laminated_calcification": {
        "desen": r"laminated", "eksen": "benign",
        "kaynak": "ACR Lung-RADS v2022",
        "not": "⚠ `concentric` BILEREK DISARIDA - olculdu, 16 eslesmenin tamami "
               "damar/duvar ('concentric wall thickness'), kalsifikasyon paterni DEGIL."},
    "central_calcification": {
        "desen": r"central calcification|centrally calcified", "eksen": "benign",
        "kaynak": "ACR Lung-RADS v2022"},
    "complete_calcification": {
        "desen": r"complete(?:ly)? calcifi", "eksen": "benign",
        "kaynak": "ACR Lung-RADS v2022",
        "not": "⚠ `diffuse calcifi` BILEREK DISARIDA - olculdu, 491 eslesmenin "
               "tamami damar ateromu ('diffuse calcific atheroma plaques'). "
               "Lung-RADS'in 'complete calcification'i ile AYNI KAVRAM DEGIL; "
               "docs/34 §4.4'un acik birakilan sorusu boylece cevaplandi."},
    # ---- malignite ekseni (D74, WHO 2021 / alan sozlugu §15) ----
    "adenocarcinoma": {"desen": r"adenocarcinom", "eksen": "malignite",
                       "kaynak": "WHO 2021 toraks tumorleri"},
    "squamous_cell_carcinoma": {"desen": r"squamous cell|epidermoid carcinom",
                                "eksen": "malignite", "kaynak": "WHO 2021"},
    "small_cell_carcinoma": {"desen": r"small cell (?:lung )?(?:carcinom|cancer)",
                             "eksen": "malignite", "kaynak": "WHO 2021"},
    "large_cell_carcinoma": {"desen": r"large cell carcinom",
                             "eksen": "malignite", "kaynak": "WHO 2021"},
    "lymphoma": {"desen": r"lymphoma", "eksen": "malignite", "kaynak": "WHO 2021"},
    "sarcoma": {"desen": r"sarcom", "eksen": "malignite", "kaynak": "WHO 2021"},
    "mesothelioma": {"desen": r"mesotheliom", "eksen": "malignite", "kaynak": "WHO 2021"},
    "thymoma": {"desen": r"thymom", "eksen": "malignite", "kaynak": "WHO 2021"},
    "carcinoid": {"desen": r"carcinoid", "eksen": "malignite", "kaynak": "WHO 2021"},
    # ---- Tier A cekirdegi (D74'te zaten olculmustu, burada dogrulanir) ----
    "carcinomatosis": {"desen": r"carcinomatos", "eksen": "malignite",
                       "kaynak": "alan sozlugu §15", "not": "D74'un ilk maddesi"},
}

# ⛔ OLCULUP REDDEDILEN desen parcalari - kayit icin (neden alinmadigi sorulmasin)
REDDEDILEN = {
    "concentric": {"cumle": 16, "sebep": "damar/duvar kalinlasmasi, kalsifikasyon paterni degil"},
    "diffuse calcifi": {"cumle": 491, "sebep": "damar ateromu; Lung-RADS 'complete'i ile ayni kavram degil"},
}


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])
    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id"])
    gelistirme = set(k.loc[~k["patient_id"].isin(kilitli), "study_id"])

    c = pd.read_parquet(CUMLELER, columns=["study_id", "text"])
    c = c[c["study_id"].isin(gelistirme)]
    metin = c["text"].fillna("")

    print(f"kapsam: gelistirme havuzu · {len(gelistirme):,} calisma "
          f"· {len(c):,} cumle  (kilit OKUNMADI)\n")
    print("=" * 76)
    print("TIER SINIFLANDIRMASI - 'sifir destek' iddiasi SINANIR")
    print("=" * 76)
    print(f"  {'aday':26} {'eksen':10} {'cumle':>6} {'calisma':>8}  tier")

    kayit: dict[str, dict] = {}
    for ad, t in ADAYLAR.items():
        e = metin.str.contains(t["desen"], case=False, regex=True, na=False)
        n, s = int(e.sum()), int(c.loc[e, "study_id"].nunique())
        tier = "B" if n == 0 else "A"
        print(f"  {ad:26} {t['eksen']:10} {n:>6,} {s:>8,}  Tier {tier}"
              + ("" if n == 0 else "  <- OLCUM DEGISTIRIR"))
        kayit[ad] = {
            "desen": t["desen"], "eksen": t["eksen"], "kaynak": t["kaynak"],
            "cumle": n, "calisma": s, "tier": tier,
            "korpus_destegi": n,
            "amac": "transfer" if n == 0 else "olculmus",
            **({"not": t["not"]} if "not" in t else {}),
            "ornek": [x[:200] for x in metin[e].sample(
                min(ORNEK, n), random_state=TOHUM)] if n else [],
        }

    b = [a for a, r in kayit.items() if r["tier"] == "B"]
    a_ = [a for a, r in kayit.items() if r["tier"] == "A"]
    print(f"\n  Tier B (sifir destekli, olcum-notr) : {len(b)}  -> {b}")
    print(f"  Tier A (olcum degistirir)           : {len(a_)}  -> {a_}")

    print("\n" + "=" * 76)
    print("Tier A CIKANLARIN ORNEK CUMLELERI - desen DOGRU seyi yakaliyor mu?")
    print("=" * 76)
    for ad in a_:
        print(f"\n  {ad}  ({kayit[ad]['cumle']} cumle)")
        for x in kayit[ad]["ornek"]:
            print(f"    · {x[:150]}")

    print("\n" + "=" * 76)
    print("⛔ OLCULUP REDDEDILEN DESEN PARCALARI")
    print("=" * 76)
    for d, r in REDDEDILEN.items():
        print(f"  `{d}` : {r['cumle']} cumle - {r['sebep']}")

    rapor = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "taranan_cumle": int(len(c)),
        "taranan_calisma": len(gelistirme),
        "sinir": ("Sifir-destek iddiasi YALNIZ gelistirme havuzu icin dogrulanmistir. "
                  "Kilit uzerinde atesleme madde 8/9'daki yeniden uretim ve fark "
                  "olcumunde ortaya cikacak; orada ateslerse YENI BULGU olarak "
                  "raporlanir."),
        "adaylar": kayit,
        "tier_b": b,
        "tier_a": a_,
        "reddedilen_desen_parcalari": REDDEDILEN,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
