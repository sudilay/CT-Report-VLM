"""NLST · malignite olcutunun duzeltilmis yeniden analizi.

DUZELTILEN KUSUR
    Onceki olcutte anatomi kosulu KARA LISTE idi (`anatomi_disla`): karaciger,
    tiroid, bobrek gibi bilinen toraks disi yapilar eleniyordu. Ancak anatomi
    sozlugunde HIC BULUNMAYAN yapilar (vokal kord, prostat, larinks) bos
    anatomi baglami uretiyor ve elenmiyordu. Boylece "sag vokal kord uzerinde
    4 cm kitle" gibi ifadeler pulmoner malignite sayilabiliyordu.

    Bu betik olcutu BEYAZ LISTEYE cevirir: malignite ifadesinin, cumlesinde
    veya iliski hedefinde PULMONER (ya da genis tanimda TORASIK) bir anatomi
    bulunmasi ZORUNLUDUR. Anatomi belirtilmemis ifadeler artik ELENIR.

EK OLARAK
    - Sistemler arasi fark icin ESLESTIRILMIS bootstrap (ayni hastalar)
    - Firsat yanliligi kontrolu: seri sayisi ile kanser durumu iliskisi
    - Tek indeks tarama duyarlilik analizi
    - Paydalarin acikca raporlanmasi

Kullanim:
    python scripts/83_nlst_malignite_yeniden.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import medspacy  # noqa: F401
import numpy as np
import pandas as pd
import spacy
from loguru import logger
from scipy.stats import fisher_exact

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from radyovlm.extraction import context as C  # noqa: E402
from radyovlm.extraction import entities as E  # noqa: E402

DIZIN = KOK / "outputs/btb3d_nlst"
BULGU = DIZIN / "nlst_uclu_bulgular.parquet"
BTB3D = KOK / "data/raw/btb3d-nlst-2965-reports/generated_reports_nlst_2965.csv"
ASTRA = KOK / "astra_radiology_reports_with_labels_all.xlsx"
MEDMO = KOK / "medmo_radiology_reports_with_labels.xlsx"

SISTEMLER = ["BTB3D", "ASTRA", "MEDMO"]
TEKRAR = 5000
TOHUM = 20260910

MALIGNITE_KAVRAM = {
    "mass", "tumor", "malignancy", "neoplasm", "carcinoma", "metastasis",
    "carcinomatosis", "lymphoma", "sarcoma", "mesothelioma",
    "small_cell_carcinoma", "adenocarcinoma", "squamous_cell_carcinoma",
    "large_cell_carcinoma", "carcinoid", "cancer", "malignant_character",
    "space_occupying_lesion",
}

# BEYAZ LISTE - dar tanim: akciger parankimi ve plevra
PULMONER = {
    "lung", "lung_parenchyma", "parenchyma", "upper_lobe", "middle_lobe",
    "lower_lobe", "lingula", "anatomic_segment", "lung_apex", "hemithorax",
    "pleura", "fissure", "bronchus", "airway", "pleuroparenchymal",
}
# BEYAZ LISTE - genis tanim: toraks bosluğu
TORASIK = PULMONER | {
    "mediastinum", "hilum", "lymph_node", "station_prevascular",
    "station_paratracheal", "station_subcarinal", "station_hilar_axillary",
    "station_aortopulmonary", "trachea", "thymus", "pericardium", "heart",
    "aorta", "coronary_artery", "pulmonary_artery", "vena_cava",
    "vascular_structure", "esophagus", "chest_wall", "rib", "sternum",
    "diaphragm", "lumen",
}


def _s74():
    yol = KOK / "scripts/74_btb3d_ctrate_18sinif.py"
    spec = importlib.util.spec_from_file_location("_s74", yol)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_s74"] = mod
    spec.loader.exec_module(mod)
    return mod


def J(y: np.ndarray, p: np.ndarray) -> float:
    tp = ((y == 1) & (p == 1)).sum(); fn = ((y == 1) & (p == 0)).sum()
    tn = ((y == 0) & (p == 0)).sum(); fp = ((y == 0) & (p == 1)).sum()
    return ((tp / (tp + fn) if tp + fn else 0.0)
            + (tn / (tn + fp) if tn + fp else 0.0) - 1)


def sayim(y: np.ndarray, p: np.ndarray) -> dict:
    tp = int(((y == 1) & (p == 1)).sum()); fp = int(((y == 0) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum()); tn = int(((y == 0) & (p == 0)).sum())
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "duyarlilik": tp / (tp + fn) if tp + fn else 0.0,
            "ozgulluk": tn / (tn + fp) if tn + fp else 0.0,
            "J": J(y, p)}


def main() -> None:
    logger.remove()
    M = _s74()
    d = pd.read_parquet(BULGU)

    b = pd.read_csv(BTB3D).set_index("key")
    a = pd.read_excel(ASTRA, usecols=["Seri_Anahtari", "Radyoloji_Raporu"])
    m = pd.read_excel(MEDMO, usecols=["series_key", "full_report"])
    A = dict(zip(a.Seri_Anahtari.astype(str), a.Radyoloji_Raporu.fillna("")))
    MM = dict(zip(m.series_key.astype(str), m.full_report.fillna("")))

    nlp = spacy.blank("en")
    nlp.add_pipe("medspacy_pyrush")
    kav, _ = E.sozlukleri_yukle()
    matcher, indeks = E.matcher_kur(kav)
    ip, son = C.ipuclarini_kur()

    siniflar = {
        "Pulmoner malignite": {"kavram": MALIGNITE_KAVRAM, "anatomi": PULMONER},
        "Torasik malignite": {"kavram": MALIGNITE_KAVRAM, "anatomi": TORASIK},
    }

    print(f"{len(d)} seri x 3 sistem yeniden etiketleniyor...")
    for i, r in enumerate(d.itertuples(index=False), 1):
        metinler = {"BTB3D": str(b.loc[r.key, "Generated_Report"]),
                    "ASTRA": str(A[r.key]), "MEDMO": str(MM[r.key])}
        for sis, metin in metinler.items():
            v, _ = M.rapor_etiketle(metin, nlp, matcher, indeks, ip, son,
                                    siniflar=siniflar, yerel_desen={})
            for ad, x in v.items():
                d.loc[d.index[i - 1], f"{sis}::{ad}"] = x
        if i % 500 == 0:
            print(f"  {i}/{len(d)}")

    d.to_parquet(DIZIN / "nlst_malignite_duzeltilmis.parquet", index=False)

    print("\n" + "=" * 74)
    print("1. OLCUT DEGISIKLIGININ ETKISI (seri duzeyi bildirim orani)")
    print("=" * 74)
    print(f"  {'Sistem':7s} {'eski (kara liste)':>18s} {'torasik':>10s} {'pulmoner':>10s}")
    for s in SISTEMLER:
        print(f"  {s:7s} {100*d[f'{s}::Malignite'].mean():17.1f}% "
              f"{100*d[f'{s}::Torasik malignite'].mean():9.1f}% "
              f"{100*d[f'{s}::Pulmoner malignite'].mean():9.1f}%")

    # -------------------------------------------------- firsat yanliligi
    print("\n" + "=" * 74)
    print("2. FIRSAT YANLILIGI KONTROLU")
    print("=" * 74)
    ser = d.groupby("pid").size()
    lab = d.groupby("pid").label.max()
    print(f"  seri sayisi: kanserli {ser[lab == 1].mean():.2f} · "
          f"kanser olmayan {ser[lab == 0].mean():.2f}")
    print(f"  dagilim kanserli: {dict(ser[lab==1].value_counts().sort_index())}")
    print(f"  dagilim negatif : {dict(ser[lab==0].value_counts().sort_index())}")

    # -------------------------------------------------- ana olcum
    print("\n" + "=" * 74)
    print("3. DUZELTILMIS OLCUT ILE KANSER SONUCU")
    print("=" * 74)
    rng = np.random.default_rng(TOHUM)
    sonuc = []
    for gos in ["Pulmoner malignite", "Torasik malignite"]:
        for kur, ad in [("max", "hasta duzeyi (herhangi bir seri)"),
                        ("ilk", "tek indeks tarama (ilk seri)")]:
            if kur == "max":
                pid = d.groupby("pid").agg(
                    {**{f"{s}::{gos}": "max" for s in SISTEMLER},
                     "label": "max", "followup_yil": "min"})
            else:
                ilk = d.sort_values(["pid", "key"]).groupby("pid").head(1)
                pid = ilk.set_index("pid")[
                    [f"{s}::{gos}" for s in SISTEMLER] + ["label", "followup_yil"]]
            alt = pid[(pid.label == 0) | (pid.followup_yil <= 1)]
            y = alt.label.values
            print(f"\n  --- {gos} · {ad}")
            print(f"      payda: {len(alt)} hasta = {int((y==0).sum())} kanser "
                  f"olmayan + {int(y.sum())} tanisi <=1 yil "
                  f"({len(pid)-len(alt)} gec tanili hasta cikarildi)")
            P = {s: alt[f"{s}::{gos}"].values for s in SISTEMLER}
            for s in SISTEMLER:
                k = sayim(y, P[s])
                bs = np.array([J(y[i], P[s][i]) for i in
                               (rng.integers(0, len(y), len(y))
                                for _ in range(TEKRAR))])
                lo, hi = np.percentile(bs, [2.5, 97.5])
                print(f"      {s:7s} TP{k['TP']:3d} FP{k['FP']:4d} FN{k['FN']:3d} "
                      f"TN{k['TN']:4d} | duy {k['duyarlilik']:.3f} "
                      f"ozg {k['ozgulluk']:.3f} | J {k['J']:+.3f} [{lo:+.3f},{hi:+.3f}]")
                sonuc.append({"gosterge": gos, "kural": ad, "sistem": s,
                              **k, "J_alt": lo, "J_ust": hi})
            # ESLESTIRILMIS fark
            print("      eslestirilmis fark (ayni hastalar):")
            for s1, s2 in [("ASTRA", "BTB3D"), ("ASTRA", "MEDMO"), ("BTB3D", "MEDMO")]:
                dj = J(y, P[s1]) - J(y, P[s2])
                bs = np.array([J(y[i], P[s1][i]) - J(y[i], P[s2][i]) for i in
                               (rng.integers(0, len(y), len(y))
                                for _ in range(TEKRAR))])
                lo, hi = np.percentile(bs, [2.5, 97.5])
                im = "aralik sifiri icermiyor" if (lo > 0 or hi < 0) else "aralik sifiri iceriyor"
                print(f"        DJ({s1}-{s2}) {dj:+.3f} [{lo:+.3f},{hi:+.3f}]  {im}")

    # -------------------------------------------------- yon testi
    print("\n" + "=" * 74)
    print("4. YON TESTI (duzeltilmis olcut, tum hastalar)")
    print("=" * 74)
    for gos in ["Pulmoner malignite", "Torasik malignite"]:
        pid = d.groupby("pid").agg(
            {**{f"{s}::{gos}": "max" for s in SISTEMLER}, "label": "max"})
        y = pid.label.values
        print(f"\n  {gos}")
        for s in SISTEMLER:
            p = pid[f"{s}::{gos}"].values
            t = [[int(((y == 1) & (p == 1)).sum()), int(((y == 1) & (p == 0)).sum())],
                 [int(((y == 0) & (p == 1)).sum()), int(((y == 0) & (p == 0)).sum())]]
            orn, pv = fisher_exact(t)
            k1 = 100 * t[0][0] / max(1, t[0][0] + t[0][1])
            k0 = 100 * t[1][0] / max(1, t[1][0] + t[1][1])
            print(f"    {s:7s} kanserli %{k1:5.1f} · kanser olmayan %{k0:5.1f} "
                  f"| odds {orn:6.2f}  p={pv:.4f}")

    (DIZIN / "nlst_malignite_duzeltilmis.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8")
    print(f"\nyazildi: {DIZIN / 'nlst_malignite_duzeltilmis.parquet'}")


if __name__ == "__main__":
    main()
