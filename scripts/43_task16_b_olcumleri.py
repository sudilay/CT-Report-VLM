"""TASK-16 Adim 3 - B TIPI OLCUMLER.

Plan: docs/29 §8.5 adim 3 · Kural: docs/29 §2.2/B

B tipi = korpustan sayilabilir NESNEL olgu. Yalniz KAPSAM belirler, klinik
agirlik VERMEZ. Sinif prevalansi OLCULMEZ (kurallar henuz yazilmadi - docs/32
bulgu #2).

Neyi olctugumuz adim 2'nin cikardigi A kurallarina baglidir: her A kuralinin bu
korpusta karsiligi var mi, ne kadar? Karsiligi olmayan kural semaya girmez
(docs/29 §9-B.4).

KAPSAM: yalniz gelistirme havuzu. Degerlendirme kilidi okunmaz.

Kullanim:
    python scripts/43_task16_b_olcumleri.py
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
CIKTI = KOK / "reports/task16_b_olcumleri.json"

# --- A26: Lung-RADS'in BENIGN kalsifikasyon listesi (Kategori 1) ---
A26_BENIGN = {
    "complete calcification": r"complete(?:ly)? calcifi",
    "central calcification": r"central(?:ly)? calcifi|calcifi\w*.{0,12}\bcentral",
    "popcorn calcification": r"popcorn",
    "concentric/laminated": r"concentric|laminat",
    "fat-containing": r"fat.contain|contains? fat|fat density|fatty",
}
A26_GENEL = {"herhangi kalsifikasyon": r"calcifi"}

# --- A34: perifissural / jukstaplevral (Fleischner) ---
A34 = {
    "perifissural": r"perifissural|peri.fissural",
    "juxtapleural/subpleural": r"juxtapleural|subpleural|adjacent to the (?:pleura|fissure)",
    "intrapulmonary lymph node": r"intrapulmonary lymph node",
}

# --- A32: kilavuzsuz bolge gostergeleri ---
A32 = {
    "bilinen primer kanser": r"known (?:primary )?(?:cancer|malignan)|primary (?:of the )?patient|history of (?:cancer|malignan)|previously (?:diagnosed|operated)|post.?(?:operative|treatment) (?:control|follow)",
    "bagisiklik baskilanmasi": r"immunocompromis|immunosuppress|immune deficien",
}

# --- #4: derece kelimeleri (suphe siddeti) ---
DERECE = {
    "high suspicion": r"high(?:ly)? suspic|strongly suspic|highly suggestive",
    "suspicious (yalin)": r"suspicio",
    "may / probable / possible": r"\bmay be\b|\bprobabl|\bpossibl|\bmay represent",
    "cannot be excluded": r"cannot be excluded|can not be excluded|could not be excluded",
    "compatible/consistent with": r"compatible with|consistent with",
    "in favor of (CIKARIM, A8)": r"in favor of",
}

# --- A22 / olcu konvansiyonu ---
OLCU = {"short axis": r"short axis|short.axis", "long axis": r"long axis"}

# --- A28/A29: buyume (dar desen, docs/31 §2/1) ---
BUYUME = {
    "1 genis desen (ARTEFAKTLI)": r"increas|enlarg|growth|\bgrew\b|\bnew\b|progress",
    "2   artefakt: dansite/kalinlik artisi": r"(?:density|densit|thickness|thickening|attenuation|opacity)\s+increas",
    "3 dar desen": r"\benlarg|growth|\bgrew\b|progress|size increas|increased in size",
    "4   artefakt: 'enlarged lymph node' (STATIK boyut)": r"enlarged lymph|lymph node.{0,20}enlarg",
    "5 zamansal atif (onceki tetkik)": r"previous|prior|compared to|comparison|follow.up",
    "6 GERCEK BUYUME = dar desen VE zamansal atif": None,
    "7 yeni gelisen": r"newly (?:developed|appeared)|de novo|not (?:seen|observed) (?:in|on) the previous",
}

GRUPLAR = [
    ("A26 · Lung-RADS benign kalsifikasyon paternleri", A26_BENIGN),
    ("A26 · karsilastirma: genel kalsifikasyon", A26_GENEL),
    ("A34 · Fleischner perifissural / jukstaplevral", A34),
    ("A32 · kilavuzsuz bolge gostergeleri", A32),
    ("#4 · suphe derece kelimeleri", DERECE),
    ("A22 · olcu konvansiyonu", OLCU),
    ("A28/A29 · buyume", BUYUME),
]


def main() -> int:
    for y in (CUMLELER, KORPUS, KILIT):
        if not y.exists():
            print(f"HATA: yok: {y}")
            return 1

    kilit = json.loads(KILIT.read_text(encoding="utf-8"))
    dk = kilit["degerlendirme_kilidi"]
    kilitli = set(dk["a_ctrate_valid"]["hasta_listesi"]) | set(dk["b_train_kilit"]["hasta_listesi"])

    k = pd.read_parquet(KORPUS, columns=["study_id", "patient_id", "PatientAge"])
    gel = k[~k["patient_id"].isin(kilitli)]
    gel_calisma = set(gel["study_id"])

    s = pd.read_parquet(CUMLELER, columns=["study_id", "text"])
    s = s[s["study_id"].isin(gel_calisma)]
    metin = s["text"].fillna("")
    n_cumle, n_calisma = len(s), s["study_id"].nunique()
    print(f"kapsam: gelistirme havuzu · {n_cumle:,} cumle / {n_calisma:,} calisma\n")

    sonuc: dict[str, dict] = {}
    for baslik, grup in GRUPLAR:
        print(f"### {baslik}")
        sonuc[baslik] = {}
        for ad, dsn in grup.items():
            if dsn is None:  # ozel: dar desen VE zamansal atif kesisimi
                m = (metin.str.contains(BUYUME["3 dar desen"], case=False, regex=True, na=False)
                     & metin.str.contains(BUYUME["5 zamansal atif (onceki tetkik)"],
                                          case=False, regex=True, na=False))
            else:
                m = metin.str.contains(dsn, case=False, regex=True, na=False)
            c, ca = int(m.sum()), int(s.loc[m, "study_id"].nunique())
            sonuc[baslik][ad] = {"cumle": c, "calisma": ca,
                                 "calisma_orani_yuzde": round(ca / n_calisma * 100, 3)}
            print(f"  {ad:44} {c:>7,} cumle / {ca:>6,} calisma  (%{ca/n_calisma*100:5.2f})")
        print()

    # --- A32: yas dagilimi (hasta duzeyi, metinden degil metadata'dan) ---
    yas = pd.to_numeric(gel["PatientAge"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    genc = int((yas < 35).sum())
    print("### A32 · yas (Fleischner < 35 yasi disliyor)")
    print(f"  yas bilinen calisma                          {int(yas.notna().sum()):>7,}")
    print(f"  < 35 yas                                     {genc:>7,} "
          f"(%{genc/max(1,yas.notna().sum())*100:5.2f})")
    sonuc["A32 · yas"] = {
        "yas_bilinen_calisma": int(yas.notna().sum()),
        "yas_35_alti_calisma": genc,
        "medyan": float(yas.median()) if yas.notna().any() else None,
    }

    ozet = {
        "uretim_utc": datetime.now(timezone.utc).isoformat(),
        "kapsam": "yalniz gelistirme havuzu; degerlendirme kilidi okunmadi",
        "kilit_surumu": kilit["surum"],
        "taranan_cumle": n_cumle,
        "taranan_calisma": n_calisma,
        "not": "B tipi olcum: yalniz kapsam belirler, klinik agirlik vermez (docs/29 §2.2/B). "
               "Sinif prevalansi OLCULMEDI - kurallar henuz yazilmadi.",
        "olcumler": sonuc,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nYAZILDI: {CIKTI.relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
