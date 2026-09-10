"""NLST kohortu · uc sistemin rapor ciktilarindan bulgu cikarimi.

BTB3D · Astra · MedMo ayni 2.965 seride hizalidir ve kanser etiketleri
birebir aynidir. Bu betik ucunu de AYNI dondurulmus cikarim hattindan
gecirir, boylece sistemler arasi fark yontemden degil ciktidan gelir.

⛔ KAPSAM: yalniz train + dev. Held-out kilitte DOKUNULMAZ ilan edilmistir
   (`configs/splits_astra.json`), bu betik onu okumaz.

⚠ NLST'de INSAN YAZIMI REFERANS RAPOR YOKTUR. Uc kaynak da model ciktisidir.
  Dis gercek yalnizca dogrulanmis kanser etiketidir. Sistemler arasi uyum
  "dogruluk" degil "tutarlilik" olarak yorumlanmalidir.

Cikti:
    outputs/btb3d_nlst/nlst_uclu_bulgular.parquet

Kullanim:
    python scripts/79_nlst_uclu_cikarim.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import medspacy  # noqa: F401  - spaCy fabrikalarini kaydeder
import pandas as pd
import spacy
from loguru import logger

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import context as C  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

BTB3D = KOK / "data/raw/btb3d-nlst-2965-reports/generated_reports_nlst_2965.csv"
ASTRA = KOK / "astra_radiology_reports_with_labels_all.xlsx"
MEDMO = KOK / "medmo_radiology_reports_with_labels.xlsx"
KILIT = KOK / "configs/splits_astra.json"
CIKTI = KOK / "outputs/btb3d_nlst/nlst_uclu_bulgular.parquet"

SURUM = "nlst-uclu-cikarim-1.0"
KAPSAM = ("train", "dev")

TORAKS_DISI = {"liver", "adrenal_gland", "kidney", "spleen", "gallbladder",
               "pancreas", "thyroid", "breast", "abdomen"}

# ---------------------------------------------------- malignite paneli (ON PLAN)
MALIGNITE_PANELI: dict[str, dict] = {
    "Malignite": {
        "kavram": {"mass", "tumor", "malignancy", "neoplasm", "carcinoma",
                   "metastasis", "carcinomatosis", "lymphoma", "sarcoma",
                   "mesothelioma", "small_cell_carcinoma", "adenocarcinoma",
                   "squamous_cell_carcinoma", "large_cell_carcinoma",
                   "carcinoid", "cancer", "malignant_character",
                   "space_occupying_lesion"},
        "anatomi_disla": TORAKS_DISI,
    },
    "Supheli morfoloji": {
        "kavram": {"spiculated", "irregular", "lobulated", "cavitation"},
        "anatomi_disla": TORAKS_DISI,
    },
    "Nodul": {
        "kavram": {"nodule", "nodular_lesion"},
        "anatomi_disla": TORAKS_DISI | {"lymph_node"},
    },
    "Kitle": {
        "kavram": {"mass", "space_occupying_lesion"},
        "anatomi_disla": TORAKS_DISI,
    },
}


def _s74():
    yol = KOK / "scripts/74_btb3d_ctrate_18sinif.py"
    spec = importlib.util.spec_from_file_location("_s74", yol)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_s74"] = mod
    spec.loader.exec_module(mod)
    return mod


def kapsam_serileri() -> pd.DataFrame:
    """train + dev serileri; kilitte dislanan 25 seri cikarilir."""
    k = json.loads(KILIT.read_text(encoding="utf-8"))
    pid_split = {}
    for ad in ("train", "dev", "held_out"):
        for p in k["bolunme"][ad]["pid_listesi"]:
            pid_split[str(p)] = ad
    dislanan = set(k["filtre"]["dislanan_seri_anahtarlari"])

    b = pd.read_csv(BTB3D)
    b["pid"] = b.key.str.split("/").str[0].astype(str)
    b["split"] = b.pid.map(pid_split).fillna("kohort_disi")
    b = b[b.split.isin(KAPSAM) & ~b.key.isin(dislanan)].copy()
    if b.empty:
        raise ValueError("kapsam bos - kilit okunamadi mi?")
    return b, k["surum"]


def main() -> None:
    logger.remove()          # medspacy hata ayiklama gurultusunu kapat
    M = _s74()
    siniflar = {**M.SINIFLAR, **MALIGNITE_PANELI}
    yerel = M.YEREL_DESEN

    b, kilit_surumu = kapsam_serileri()
    print(f"kapsam: {len(b)} seri · {b.pid.nunique()} PID · "
          f"{int(b.label.sum())} pozitif seri · kilit {kilit_surumu}")

    a = pd.read_excel(ASTRA, usecols=["Seri_Anahtari", "Radyoloji_Raporu"])
    m = pd.read_excel(MEDMO, usecols=["series_key", "full_report"])
    a = dict(zip(a.Seri_Anahtari.astype(str), a.Radyoloji_Raporu.fillna("")))
    m = dict(zip(m.series_key.astype(str), m.full_report.fillna("")))

    eksik = [k for k in b.key if k not in a or k not in m]
    if eksik:
        raise ValueError(f"{len(eksik)} seri ucunde birden yok, ilk: {eksik[0]}")

    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")
    kavramlar, _ = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kavramlar)
    ipuclari, sonlandirici = C.ipuclarini_kur()

    satirlar = []
    for i, r in enumerate(b.itertuples(index=False), 1):
        metinler = {"BTB3D": str(r.Generated_Report),
                    "ASTRA": str(a[r.key]),
                    "MEDMO": str(m[r.key])}
        satir = {"key": r.key, "pid": r.pid, "split": r.split,
                 "label": int(r.label), "censor_yil": int(r.censor_time),
                 "followup_yil": int(r.followup_year)}
        for sistem, metin in metinler.items():
            varsa, _ = M.rapor_etiketle(metin, nlp, matcher, indeks, ipuclari,
                                        sonlandirici, siniflar=siniflar,
                                        yerel_desen=yerel)
            satir[f"{sistem}__kelime"] = len(metin.split())
            for ad, v in varsa.items():
                satir[f"{sistem}::{ad}"] = v
        satirlar.append(satir)
        if i % 250 == 0:
            print(f"  {i}/{len(b)} seri")

    out = pd.DataFrame(satirlar)
    out["surum"] = SURUM
    out["bolunme_kilidi"] = kilit_surumu
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(CIKTI, index=False)

    print(f"\nyazildi: {CIKTI}  ({len(out)} seri)")
    print("\npozitif oranlari (seri duzeyi):")
    for ad in list(MALIGNITE_PANELI):
        s = "  ".join(f"{x} %{100*out[f'{x}::{ad}'].mean():4.1f}"
                      for x in ("BTB3D", "ASTRA", "MEDMO"))
        print(f"  {ad:20s} {s}")


if __name__ == "__main__":
    main()
